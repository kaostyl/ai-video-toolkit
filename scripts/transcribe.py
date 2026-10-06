#!/usr/bin/env python3
"""
transcribe.py — Transcribe a video to transcript.json / .srt / .txt with timecodes.
Uses faster-whisper; runs on CUDA (your GPU) if available, else CPU.
Detects silence gaps (>1.5s) so the editor can spot dead air / retakes.

Usage:
    python transcribe.py --source "video.mp4" --out out/ [--model small] [--lang fr]
Deps: faster-whisper, ffmpeg on PATH.
"""
import os, json, argparse, subprocess, tempfile

def extract_audio(src):
    fd,tmp=tempfile.mkstemp(prefix="video-transcript-",suffix=".wav")
    os.close(fd)
    subprocess.run(["ffmpeg","-y","-i",src,"-vn","-ac","1","-ar","16000","-c:a","pcm_s16le",tmp],
                   check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return tmp

def srt_ts(t):
    h=int(t//3600); m=int((t%3600)//60); s=t%60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace('.',',')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True); ap.add_argument("--out",default="out")
    ap.add_argument("--model",default="small"); ap.add_argument("--lang",default="fr")
    ap.add_argument("--words",action="store_true",help="word timestamps + gap report")
    ap.add_argument("--device",default="auto",help="auto|cuda|cpu")
    a=ap.parse_args()
    os.makedirs(a.out,exist_ok=True)
    from faster_whisper import WhisperModel
    device="cpu"; ctype="int8"
    if a.device=="cuda": device,ctype="cuda","float16"
    elif a.device=="auto":
        try:
            import torch
            if torch.cuda.is_available(): device,ctype="cuda","float16"
        except Exception: pass
    print(f"transcribe: model={a.model} device={device}")
    m=WhisperModel(a.model,device=device,compute_type=ctype)
    audio=extract_audio(a.source)
    segs,info=m.transcribe(audio,language=a.lang,vad_filter=True,word_timestamps=a.words)
    out=[]; words=[]
    for s in segs:
        out.append({"start":round(s.start,2),"end":round(s.end,2),"text":s.text.strip()})
        if a.words and s.words:
            for w in s.words: words.append((round(w.start,2),w.word.strip()))
    os.unlink(audio)
    json.dump(out,open(os.path.join(a.out,"transcript.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    with open(os.path.join(a.out,"transcript.srt"),"w",encoding="utf-8") as f:
        for i,s in enumerate(out,1): f.write(f"{i}\n{srt_ts(s['start'])} --> {srt_ts(s['end'])}\n{s['text']}\n\n")
    with open(os.path.join(a.out,"transcript.txt"),"w",encoding="utf-8") as f:
        for s in out: f.write(f"[{s['start']:7.2f}->{s['end']:7.2f}] {s['text']}\n")
    if a.words:
        gaps=[]; prev=None
        for t,w in words:
            if prev is not None and t-prev>1.5: gaps.append({"from":prev,"to":t,"len":round(t-prev,1),"before":w})
            prev=t
        json.dump(gaps,open(os.path.join(a.out,"silence_gaps.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        print(f"  {len(gaps)} silences >1.5s détectés")
    print(f"  {len(out)} segments -> {a.out}/transcript.json")

if __name__=="__main__": main()
