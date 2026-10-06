#!/usr/bin/env python3
"""
qc.py — Automated quality control of the FINAL render.
1) Extracts a frame at each overlay's mid-window from the final MP4 and builds a
   single contact sheet (grid, labelled) -> one image to eyeball everything.
2) Audio: measures integrated loudness (LUFS), loudness range and true peak with
   ffmpeg ebur128, flags clipping risk and distance to the YouTube -14 LUFS target.
3) Container: verifies resolution/fps/duration against the plan/source.

Usage:
    python qc.py --plan out/plan.json --video output/FINAL.mp4 --out output/qc
Exit code: 0 = OK (warnings allowed), 1 = hard failure (frame extraction failed, wrong res...).
"""
import os, re, json, math, argparse, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

def run(cmd): return subprocess.run(cmd,capture_output=True,text=True)

def probe(video):
    r=run(["ffprobe","-v","error","-select_streams","v:0",
           "-show_entries","stream=width,height,avg_frame_rate","-show_entries","format=duration",
           "-of","json",video])
    j=json.loads(r.stdout or "{}")
    st=(j.get("streams") or [{}])[0]; fr=st.get("avg_frame_rate","0/1")
    num,den=(fr.split("/")+["1"])[:2]; fps=(float(num)/float(den)) if float(den) else 0
    return int(st.get("width",0)),int(st.get("height",0)),fps,float(j.get("format",{}).get("duration",0))

def measure_audio(video):
    r=run(["ffmpeg","-nostats","-i",video,"-map","0:a:0","-filter:a","ebur128=peak=true","-f","null","-"])
    txt=r.stderr
    tail=txt[txt.rfind("Summary:"):] if "Summary:" in txt else txt
    def grab(pat):
        m=re.search(pat,tail)
        return float(m.group(1)) if m else None
    return {"I":grab(r"I:\s*(-?[\d.]+)\s*LUFS"),"LRA":grab(r"LRA:\s*([\d.]+)\s*LU"),
            "TP":grab(r"Peak:\s*(-?[\d.]+)\s*dBFS")}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--plan",required=True); ap.add_argument("--video",required=True)
    ap.add_argument("--out",default="output/qc"); ap.add_argument("--cols",type=int,default=4)
    a=ap.parse_args()
    plan=json.load(open(a.plan,encoding="utf-8"))
    os.makedirs(a.out,exist_ok=True)
    errors=[]; warns=[]

    # --- container checks ---
    W,H,fps,dur=probe(a.video)
    pres=plan.get("resolution") or [1920,1080]
    if [W,H]!=[int(pres[0]),int(pres[1])]: errors.append(f"résolution {W}x{H} != plan {pres[0]}x{pres[1]}")
    pfps=int(plan.get("fps",30))
    if abs(fps-pfps)>0.6: warns.append(f"fps {fps:.2f} != plan {pfps}")
    last=max((float(o['t'])+float(o['dur'])) for o in plan["overlays"])
    if dur+0.5<last: errors.append(f"vidéo {dur:.1f}s plus courte que le dernier overlay ({last:.1f}s)")
    print(f"container: {W}x{H}@{fps:.2f} {dur:.1f}s")

    # --- frames + contact sheet ---
    thumbs=[]; tw=640
    for ov in plan["overlays"]:
        t=float(ov["t"])+float(ov["dur"])*0.6
        fp=os.path.join(a.out,f"{ov['id']}.png")
        r=run(["ffmpeg","-y","-ss",f"{t:.2f}","-i",a.video,"-frames:v","1","-vf",f"scale={tw}:-1",fp])
        if not os.path.exists(fp) or os.path.getsize(fp)==0:
            errors.append(f"frame introuvable pour {ov['id']} @ {t:.1f}s"); continue
        thumbs.append((ov["id"],t,fp))
    if thumbs:
        im0=Image.open(thumbs[0][2]); th=im0.height; cols=a.cols; rows=math.ceil(len(thumbs)/cols)
        pad=8; label=26
        sheet=Image.new("RGB",(cols*(tw+pad)+pad,rows*(th+label+pad)+pad),(12,14,18))
        d=ImageDraw.Draw(sheet)
        try: f=ImageFont.truetype(os.path.join(os.path.dirname(__file__),"fonts","Poppins-Medium.ttf"),18)
        except Exception: f=ImageFont.load_default()
        for k,(oid,t,fp) in enumerate(thumbs):
            x=pad+(k%cols)*(tw+pad); y=pad+(k//cols)*(th+label+pad)
            sheet.paste(Image.open(fp),(x,y))
            d.text((x+4,y+th+3),f"{oid}  @{t:.1f}s",font=f,fill=(220,225,235))
        cs=os.path.join(a.out,"contact_sheet.png"); sheet.save(cs)
        print(f"contact sheet: {cs} ({len(thumbs)} overlays)")

    # --- audio ---
    au=measure_audio(a.video)
    if au["I"] is not None:
        print(f"audio: {au['I']:.1f} LUFS (cible YouTube -14) | LRA {au['LRA']} LU | true peak {au['TP']} dBFS")
        if au["TP"] is not None and au["TP"]>-0.8: warns.append(f"true peak {au['TP']} dBFS trop chaud (vise <= -1.0)")
        if au["I"]<-19: warns.append(f"loudness {au['I']} LUFS faible — YouTube n'amplifie pas (envisage --loudnorm)")
        if au["I"]>-12.5: warns.append(f"loudness {au['I']} LUFS fort — YouTube va réduire le volume")
    else: warns.append("mesure loudness impossible")

    for w in warns: print(f"  WARN  {w}")
    for e in errors: print(f"  ERREUR {e}")
    print(f"qc: {len(errors)} erreur(s), {len(warns)} warning(s)")
    sys.exit(1 if errors else 0)

if __name__=="__main__": main()
