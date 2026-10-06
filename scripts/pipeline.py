#!/usr/bin/env python3
"""
pipeline.py â€” One-command orchestrator for the whole auto-edit pipeline.

Stages (each skippable, timings logged):
  transcribe -> [PLAN: written by the operator/Claude] -> validate -> sfx ->
  motion -> compose -> fcpxml -> qc

Typical use once the plan exists:
    python pipeline.py --source "VIDEO.mp4" --plan out/plan.json \
        --res 3840x2160 --encoder nvenc --sfx-volume 0.30

First run on a new video (no plan yet): transcribe only, then stop so the plan
can be written from the transcript:
    python pipeline.py --source "VIDEO.mp4" --transcribe-only

Outputs: output/<project>_FINAL.mp4, output/<project>.fcpxml, output/qc/.
"""
import os, sys, json, time, argparse, subprocess

HERE=os.path.dirname(os.path.abspath(__file__))
PY=sys.executable

def stage(name,cmd,timings):
    print(f"\n=== {name} ===")
    t0=time.time()
    r=subprocess.run(cmd)
    dt=time.time()-t0
    timings.append((name,dt,r.returncode))
    if r.returncode!=0:
        print(f"!! Ã©chec Ã  l'Ã©tape '{name}' (code {r.returncode}) â€” pipeline arrÃªtÃ©")
        summary(timings); sys.exit(r.returncode)
    print(f"=== {name} OK ({dt:.1f}s) ===")

def summary(timings):
    print("\n--- RÃ©cap pipeline ---")
    for n,dt,rc in timings:
        print(f"  {'OK ' if rc==0 else 'ERR'} {n:<12} {dt:7.1f}s")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True)
    ap.add_argument("--plan",default="out/plan.json")
    ap.add_argument("--res",default="1920x1080"); ap.add_argument("--fps",default=None)
    ap.add_argument("--encoder",default="cpu"); ap.add_argument("--sfx-volume",type=float,default=0.30)
    ap.add_argument("--music",default="auto",help="fichier musique, 'auto' (1er de music/) ou 'none'")
    ap.add_argument("--music-volume",type=float,default=0.09)
    ap.add_argument("--loudnorm",action="store_true")
    ap.add_argument("--out-dir",default="output"); ap.add_argument("--assets",default="assets")
    ap.add_argument("--sfx-dir",default="sfx"); ap.add_argument("--model",default="small"); ap.add_argument("--lang",default="fr")
    ap.add_argument("--transcribe-only",action="store_true",help="transcrit puis s'arrÃªte (le plan reste Ã  Ã©crire)")
    ap.add_argument("--renderer",default="pil",help="remotion|pil â€” moteur de rendu des overlays")
    ap.add_argument("--skip-transcribe",action="store_true"); ap.add_argument("--skip-motion",action="store_true")
    ap.add_argument("--skip-compose",action="store_true"); ap.add_argument("--skip-fcpxml",action="store_true")
    ap.add_argument("--skip-qc",action="store_true")
    a=ap.parse_args()
    timings=[]

    tr_txt=os.path.join("out","transcript.txt")
    if a.transcribe_only or (not a.skip_transcribe and not os.path.exists(tr_txt)):
        stage("transcribe",[PY,os.path.join(HERE,"transcribe.py"),"--source",a.source,"--out","out",
                            "--model",a.model,"--lang",a.lang,"--words"],timings)
        if a.transcribe_only or not os.path.exists(a.plan):
            print(f"\nTranscription prÃªte: {tr_txt}")
            print(f"Ã‰cris maintenant le plan ({a.plan}) puis relance pipeline.py (la transcription sera sautÃ©e).")
            summary(timings); return
    elif os.path.exists(tr_txt):
        print(f"transcribe: dÃ©jÃ  fait ({tr_txt}) â€” sautÃ©")

    if not os.path.exists(a.plan):
        print(f"!! plan introuvable: {a.plan}"); sys.exit(1)
    plan=json.load(open(a.plan,encoding="utf-8"))
    plan["source"]=os.path.abspath(a.source)
    plan["resolution"]=[int(v) for v in a.res.lower().split("x")]
    if a.fps: plan["fps"]=int(a.fps)
    a.plan=os.path.join(a.out_dir,"render_plan.json")
    os.makedirs(a.out_dir,exist_ok=True)
    with open(a.plan,"w",encoding="utf-8") as f: json.dump(plan,f,ensure_ascii=False,indent=2)
    proj=plan.get("project","autoedit")
    final=os.path.join(a.out_dir,f"{proj}_FINAL.mp4")
    fcp=os.path.join(a.out_dir,f"{proj}.fcpxml")

    stage("validate",[PY,os.path.join(HERE,"validate_plan.py"),"--plan",a.plan,
                      "--source",a.source,"--sfx-dir",a.sfx_dir],timings)

    if not all(os.path.exists(os.path.join(a.sfx_dir,n+".wav")) for n in ("whoosh","pop","tick","riser","ding")):
        stage("sfx",[PY,os.path.join(HERE,"sfx.py"),"--out",a.sfx_dir],timings)
    else:
        print("sfx: dÃ©jÃ  prÃ©sents â€” sautÃ©")

    if any(o.get("type")=="broll" for o in plan.get("overlays",[])):
        stage("broll",[PY,os.path.join(HERE,"broll.py"),"--plan",a.plan,"--assets",a.assets,"--res",a.res],timings)

    if not a.skip_motion:
        if a.renderer=="remotion":
            rem=os.path.join(os.path.dirname(HERE),"remotion")
            stage("motion",["node",os.path.join(rem,"render-assets.mjs"),"--plan",os.path.abspath(a.plan),
                            "--out",os.path.abspath(a.assets),"--res",a.res],timings)
        else:
            stage("motion",[PY,os.path.join(HERE,"motion.py"),"--plan",a.plan,"--out",a.assets,"--res",a.res],timings)
    if not a.skip_compose:
        music=None
        if a.music=="auto":
            mdir=os.path.join(os.path.dirname(HERE),"music")
            cands=sorted([f for f in os.listdir(mdir) if f.lower().endswith((".mp3",".wav",".m4a",".flac"))]) if os.path.isdir(mdir) else []
            if cands: music=os.path.join(mdir,cands[0]); print(f"musique auto: {cands[0]}")
        elif a.music not in (None,"none"): music=a.music
        cmd=[PY,os.path.join(HERE,"compose.py"),"--plan",a.plan,"--source",a.source,"--assets",a.assets,
             "--sfx-dir",a.sfx_dir,"--out",final,"--res",a.res,"--encoder",a.encoder,
             "--sfx-volume",str(a.sfx_volume)]
        if music: cmd+=["--music",music,"--music-volume",str(a.music_volume)]
        if a.fps: cmd+=["--fps",a.fps]
        if a.loudnorm: cmd.append("--loudnorm")
        stage("compose",cmd,timings)
    if not a.skip_fcpxml:
        cmd=[PY,os.path.join(HERE,"davinci_timeline.py"),"--plan",a.plan,"--source",a.source,
             "--assets",a.assets,"--sfx-dir",a.sfx_dir,"--out",fcp,"--res",a.res]
        if a.fps: cmd+=["--fps",a.fps]
        stage("fcpxml",cmd,timings)
    if not a.skip_qc and not a.skip_compose:
        stage("qc",[PY,os.path.join(HERE,"qc.py"),"--plan",a.plan,"--video",final,
                    "--out",os.path.join(a.out_dir,"qc")],timings)

    summary(timings)
    print(f"\nLivrables:\n  {final}\n  {fcp}\n  {os.path.join(a.out_dir,'qc','contact_sheet.png')}")

if __name__=="__main__": main()
