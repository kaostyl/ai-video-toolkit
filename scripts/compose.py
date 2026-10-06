#!/usr/bin/env python3
"""
compose.py — Composite rendered overlays onto the source video + mix SFX,
in a SINGLE ffmpeg pass. On a machine with an NVIDIA GPU it uses NVENC and
can output true 4K. (No 45s limits here — this is meant to run on your PC.)

Usage:
    python compose.py --plan plan.json --source "video.mp4" --assets assets \
        --out output/final.mp4 [--res 3840x2160] [--encoder auto] [--sfx-volume 0.16]

Overlay placement comes straight from the plan timecodes (t, dur). Edge overlays
(.mov, alpha) sit on top; schemas (.mp4, opaque) cover the frame for their window.
A subtle SFX (whoosh/pop/...) is mixed in at each overlay whose "sfx" is set.
"""
import os, sys, json, argparse, subprocess, shutil

def has_encoder(name):
    try:
        out=subprocess.check_output(["ffmpeg","-hide_banner","-encoders"],stderr=subprocess.STDOUT).decode()
        return name in out
    except Exception: return False

NVENC_Q=["-rc","vbr","-b:v","0","-spatial-aq","1","-temporal-aq","1","-rc-lookahead","20","-bf","3"]
COLOR_TAGS=["-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709"]

def pick_encoder(choice):
    if choice=="cpu": return ("libx264",["-preset","slow","-crf","18"])
    if choice in ("nvenc","h264_nvenc") and has_encoder("h264_nvenc"):
        return ("h264_nvenc",["-preset","p5","-cq","19","-profile:v","high"]+NVENC_Q)
    if choice=="hevc_nvenc" and has_encoder("hevc_nvenc"):
        return ("hevc_nvenc",["-preset","p5","-cq","21","-tag:v","hvc1"]+NVENC_Q)
    if choice=="auto":
        if has_encoder("h264_nvenc"): return ("h264_nvenc",["-preset","p5","-cq","19","-profile:v","high"]+NVENC_Q)
        return ("libx264",["-preset","medium","-crf","18"])
    # fallback
    return ("libx264",["-preset","medium","-crf","18"])

def asset_path(assets,oid):
    for ext in (".mov",".mp4"):
        p=os.path.join(assets,oid+ext)
        if os.path.exists(p): return p,ext
    return None,None

def probe_wh(path):
    try:
        out=subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0",
            "-show_entries","stream=width,height","-of","csv=p=0",path],stderr=subprocess.STDOUT).decode().strip()
        w,h=out.split(",")[:2]; return int(w),int(h)
    except Exception: return None,None

def probe_dur(path):
    try:
        out=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
            "-of","default=nw=1:nk=1",path],stderr=subprocess.STDOUT).decode().strip()
        return float(out)
    except Exception: return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--plan",required=True); ap.add_argument("--source",required=True)
    ap.add_argument("--assets",default="assets"); ap.add_argument("--out",default="output/final.mp4")
    ap.add_argument("--res",default=None); ap.add_argument("--fps",default=None)
    ap.add_argument("--encoder",default="cpu",help="auto|nvenc|hevc_nvenc|cpu")
    ap.add_argument("--sfx-dir",default="sfx"); ap.add_argument("--sfx-volume",type=float,default=0.16)
    ap.add_argument("--music",default=None,help="musique de fond (bouclee), duckee automatiquement sous la voix")
    ap.add_argument("--music-volume",type=float,default=0.10)
    ap.add_argument("--loudnorm",action="store_true",help="normalise le master a -14 LUFS / -1.5 dBTP (cible YouTube)")
    ap.add_argument("--print-only",action="store_true")
    a=ap.parse_args()
    plan=json.load(open(a.plan,encoding="utf-8"))
    res=a.res or plan.get("resolution") or [1920,1080]
    if isinstance(res,str): res=[int(x) for x in res.lower().split("x")]
    W,Hh=int(res[0]),int(res[1]); fps=int(a.fps or plan.get("fps",30))
    os.makedirs(os.path.dirname(a.out) or ".",exist_ok=True)

    overlays=plan["overlays"]
    source_duration=probe_dur(a.source)
    if not source_duration: raise ValueError("Cannot read source duration")
    if os.path.abspath(a.source)==os.path.abspath(a.out):
        raise ValueError("Output must not overwrite source")
    source_streams=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","stream=codec_type","-of","json",a.source]))["streams"]
    inputs=["-i",a.source]; nin=1          # explicit input counter (inputs may carry flags)
    source_audio="[0:a]"
    if not any(s["codec_type"]=="audio" for s in source_streams):
        inputs += ["-f","lavfi","-t",str(source_duration),"-i","anullsrc=r=48000:cl=stereo"]
        source_audio="[1:a]"; nin=2
    vid_in=[]      # (input_index, ov, needs_scale)
    for ov in overlays:
        p,ext=asset_path(a.assets,ov["id"])
        if not p:
            raise ValueError("Missing rendered asset: "+ov["id"])
        aw,ah=probe_wh(p)
        # Single-threaded decode PER overlay input: ffmpeg opens ALL overlay
        # decoders at once, and ProRes 4444 uses frame-threading (~ncpu 4K
        # frames in flight each). With ~90 overlays that's tens of GB → OOM
        # ("Cannot allocate memory"). One thread per input keeps ~1 frame in
        # flight per stream; decoders still run in parallel across streams, so
        # throughput stays high. Output is bit-identical to multi-thread decode.
        inputs+=["-threads","1","-i",p]; vid_in.append((nin,ov,(aw,ah)!=(W,Hh))); nin+=1

    # frosted-glass geometry (written by motion.py alongside the assets)
    layout=None; mask_idx=None
    lay_p=os.path.join(a.assets,"_layout.json"); msk_p=os.path.join(a.assets,"_cardmask.png")
    schemas=[k for k,(idx,ov,_) in enumerate(vid_in) if str(ov.get("type","")).startswith("schema_")]
    if schemas and os.path.exists(lay_p) and os.path.exists(msk_p):
        layout=json.load(open(lay_p))
        if layout.get("res")==[W,Hh]:
            # mask must EOF *before* the video: framesync repeats its last (static)
            # frame, while a longer mask would extend the output past the source.
            mdur=max(1.0,(probe_dur(a.source) or 3600)-0.1)
            inputs+=["-loop","1","-t",f"{mdur:.2f}","-i",msk_p]; mask_idx=nin; nin+=1
        else:
            print("  ! _layout.json rendu à une autre résolution — verre dépoli désactivé"); layout=None

    # ---- video filtergraph ----
    fc=[f"[0:v]scale={W}:{Hh}:force_original_aspect_ratio=decrease,pad={W}:{Hh}:(ow-iw)/2:(oh-ih)/2,fps={fps},setsar=1[base]"]
    if mask_idx is not None:
        fc.append(f"[{mask_idx}:v]format=gray,fps={fps},split={len(schemas)}"+
                  "".join(f"[mk{k}]" for k in schemas))
    prev="base"
    for k,(idx,ov,needs_scale) in enumerate(vid_in):
        t=float(ov["t"]); dur=float(ov["dur"]); t1=round(t+dur,3)
        if mask_idx is not None and k in schemas:
            # blur the video under the card (rounded mask) for a frosted-glass look
            c=layout["card"]; cx,cy,cw,ch=c["x"],c["y"],c["w"],c["h"]
            fc.append(f"[{prev}]split[ga{k}][gb{k}]")
            fc.append(f"[gb{k}]crop={cw}:{ch}:{cx}:{cy},scale={max(1,cw//14)}:{max(1,ch//14)},"
                      f"scale={cw}:{ch}:flags=bicubic[gbl{k}]")
            fc.append(f"[gbl{k}][mk{k}]alphamerge[ggl{k}]")
            fc.append(f"[ga{k}][ggl{k}]overlay={cx}:{cy}:enable='between(t,{t},{t1})'[gv{k}]")
            prev=f"gv{k}"
        lbl=f"v{k}"
        if ov.get("type")=="broll":
            # full-frame stock footage: cover-crop + short alpha cross-fade
            fd=0.35
            fc.append(f"[{idx}:v]scale={W}:{Hh}:force_original_aspect_ratio=increase,"
                      f"crop={W}:{Hh},fps={fps},setsar=1,format=yuva420p,"
                      f"setpts=PTS-STARTPTS+{t}/TB,"
                      f"fade=t=in:st={t}:d={fd}:alpha=1,fade=t=out:st={round(t1-fd,3)}:d={fd}:alpha=1[o{k}]")
        else:
            # design assets are rendered at compose res — only rescale when they differ
            sc=f"scale={W}:{Hh}," if needs_scale else ""
            fc.append(f"[{idx}:v]{sc}fps={fps},setsar=1,setpts=PTS-STARTPTS+{t}/TB[o{k}]")
        fc.append(f"[{prev}][o{k}]overlay=format=auto:enable='between(t,{t},{t1})'[{lbl}]")
        prev=lbl
    fc.append(f"[{prev}]format=yuv420p[vout]")

    # ---- audio: voice + subtle sfx bed (supports timed multi-sfx per overlay) ----
    def sfx_events(ov):
        # New: list of {"at": sec_from_overlay_start, "name": ..., "vol": mult}.
        # Falls back to the single "sfx" at the overlay start (at=0).
        ev=ov.get("sfx_events")
        if ev: return [(float(e["at"]),e["name"],float(e.get("vol",1.0))) for e in ev]
        if ov.get("sfx"): return [(0.0,ov["sfx"],1.0)]
        return []
    # collect events grouped by sfx name: each wav is loaded ONCE then asplit,
    # so 250 events = 7 inputs instead of 250 (Windows cmdline limit safety)
    by_name={}
    for ov in overlays:
        for at,sname,vol in sfx_events(ov):
            sp=os.path.join(a.sfx_dir,sname+".wav")
            if not os.path.exists(sp): continue
            ms=max(0,int((float(ov["t"])+at)*1000))
            by_name.setdefault(sname,(sp,[]))[1].append((ms,vol))
    amix_inputs=[source_audio]
    sfx_count=0
    for sname,(sp,evs) in by_name.items():
        inputs+=["-i",sp]; idx=nin; nin+=1
        if len(evs)>1:
            fc.append(f"[{idx}:a]asplit={len(evs)}"+"".join(f"[u{sname}{j}]" for j in range(len(evs))))
        for j,(ms,vol) in enumerate(evs):
            src=f"[u{sname}{j}]" if len(evs)>1 else f"[{idx}:a]"
            sfx_count+=1
            fc.append(f"{src}adelay={ms}|{ms},volume={a.sfx_volume*vol:.4f}[s{sfx_count}]")
            amix_inputs.append(f"[s{sfx_count}]")
    # master chain: transparent brickwall limiter so voice+sfx can never clip,
    # optional loudness normalisation to the YouTube delivery target.
    master="alimiter=limit=0.89:level=false"   # brickwall ceiling ~= -1.0 dBFS
    if a.loudnorm: master+=",loudnorm=I=-14:TP=-1.5:LRA=11"
    # voice + sfx premix
    if sfx_count:
        fc.append(f"{''.join(amix_inputs)}amix=inputs={len(amix_inputs)}:normalize=0:dropout_transition=0[vs]")
    else:
        fc.append(source_audio+"anull[vs]")
    if a.music and os.path.exists(a.music):
        # looped music bed, auto-ducked under the voice (sidechain compression)
        mdur2=probe_dur(a.source) or 3600
        inputs+=["-stream_loop","-1","-i",a.music]; midx=nin; nin+=1
        fc.append(f"[{midx}:a]atrim=0:{mdur2:.2f},asetpts=N/SR/TB,aformat=sample_rates=48000:channel_layouts=stereo,"
                  f"volume={a.music_volume}[mus]")
        fc.append("[vs]asplit[vs1][vs2]")
        fc.append("[mus][vs2]sidechaincompress=threshold=0.02:ratio=14:attack=8:release=450[duck]")
        fc.append(f"[vs1][duck]amix=inputs=2:normalize=0:dropout_transition=0,{master}[aout]")
        print("musique:",os.path.basename(a.music),f"(vol {a.music_volume}, ducking auto)")
    else:
        if a.music: print("  ! musique introuvable:",a.music)
        fc.append(f"[vs]{master}[aout]")
    amap="[aout]"

    venc,vopts=pick_encoder(a.encoder)
    # filtergraph via script file: avoids the Windows 32k command-line limit
    fcpath=a.out+".filtergraph.txt"
    open(fcpath,"w",encoding="utf-8").write(";\n".join(fc))
    cmd=["ffmpeg","-y"]+inputs+["-filter_complex_script",fcpath,
         "-map","[vout]","-map",amap,
         "-c:v",venc]+vopts+COLOR_TAGS+["-c:a","aac","-b:a","256k","-ar","48000","-t",str(source_duration),"-movflags","+faststart",a.out]
    print("Encodeur vidéo:",venc," | sortie:",f"{W}x{Hh}@{fps}"," | SFX:",sfx_count)
    if a.print_only:
        print(" ".join(f'"{c}"' if " " in c else c for c in cmd)); return
    subprocess.run(cmd,check=True)
    print("OK ->",a.out)

if __name__=="__main__": main()
