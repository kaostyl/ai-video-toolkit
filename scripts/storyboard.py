#!/usr/bin/env python3
"""
storyboard.py — Sample frames from the source video into ONE labelled contact
sheet, to be LOOKED AT before writing the overlay plan (framing, face position,
lighting, existing cuts…). Complements the transcript: text tells you WHAT is
said, the storyboard shows you WHAT IS ON SCREEN while it's said.

Usage:
    python storyboard.py --source "VIDEO.mp4" --out out/storyboard.png [--every 8] [--cols 6]
"""
import os, json, math, argparse, subprocess
from PIL import Image, ImageDraw, ImageFont

def duration(path):
    out=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nw=1:nk=1",path]).decode().strip()
    return float(out)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True); ap.add_argument("--out",default="out/storyboard.png")
    ap.add_argument("--every",type=float,default=8.0); ap.add_argument("--cols",type=int,default=6)
    ap.add_argument("--tw",type=int,default=420)
    a=ap.parse_args()
    os.makedirs(os.path.dirname(a.out) or ".",exist_ok=True)
    dur=duration(a.source)
    times=[t for t in [i*a.every for i in range(1+int(dur/a.every))] if t<dur-0.5]
    tmp=os.path.join(os.path.dirname(a.out) or ".","_sb")
    os.makedirs(tmp,exist_ok=True)
    thumbs=[]
    for i,t in enumerate(times):
        fp=os.path.join(tmp,f"f{i:04d}.png")
        subprocess.run(["ffmpeg","-y","-ss",f"{t:.2f}","-i",a.source,"-frames:v","1",
                        "-vf",f"scale={a.tw}:-1",fp],check=True,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        thumbs.append((t,fp))
    with Image.open(thumbs[0][1]) as im0: th=im0.height
    pad=6; label=22; cols=a.cols; rows=math.ceil(len(thumbs)/cols)
    sheet=Image.new("RGB",(cols*(a.tw+pad)+pad,rows*(th+label+pad)+pad),(12,14,18))
    d=ImageDraw.Draw(sheet)
    try: f=ImageFont.truetype(os.path.join(os.path.dirname(__file__),"fonts","Poppins-Medium.ttf"),15)
    except Exception: f=ImageFont.load_default()
    for k,(t,fp) in enumerate(thumbs):
        x=pad+(k%cols)*(a.tw+pad); y=pad+(k//cols)*(th+label+pad)
        with Image.open(fp) as im: sheet.paste(im,(x,y))
        mm,ss=divmod(int(t),60)
        d.text((x+4,y+th+2),f"{mm:02d}:{ss:02d}",font=f,fill=(220,225,235))
    sheet.save(a.out)
    for _,fp in thumbs: os.remove(fp)
    os.rmdir(tmp)
    print(f"storyboard: {len(thumbs)} frames ({a.every}s) -> {a.out}")

if __name__=="__main__": main()
