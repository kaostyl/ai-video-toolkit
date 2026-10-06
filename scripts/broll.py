#!/usr/bin/env python3
"""
broll.py — Fetch Pexels stock B-roll clips for every overlay of type "broll".

Plan syntax:
    {"id":"br_argent","type":"broll","t":58,"dur":6,"query":"counting money desk",
     "sfx_events":[{"at":0,"name":"whoosh"}]}

For each broll overlay: searches Pexels Videos, picks the best landscape file
(resolution >= target if available, duration >= dur), downloads it to
<assets>/<id>.mp4 (skipped if already present) and records author credits in
<assets>/broll_credits.json (paste them in the YouTube description).

API key: PEXELS_API_KEY env var, or .env file at the project root.
compose.py displays brolls full-frame (cover-crop) with a short cross-fade.

Usage:
    python broll.py --plan out/plan.json --assets assets [--res 3840x2160]
"""
import os, sys, json, argparse, urllib.request, urllib.parse

def load_key():
    k=os.environ.get("PEXELS_API_KEY")
    if k: return k.strip()
    here=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    envp=os.path.join(here,".env")
    if os.path.exists(envp):
        for line in open(envp,encoding="utf-8"):
            if line.strip().startswith("PEXELS_API_KEY="):
                return line.strip().split("=",1)[1].strip()
    return None

UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Video Toolkit-AutoEdit/1.0"
def api(url,key):
    req=urllib.request.Request(url,headers={"Authorization":key,"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))
def download(url,out):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=120) as r, open(out,"wb") as f:
        while True:
            chunk=r.read(1<<20)
            if not chunk: break
            f.write(chunk)

def pick_file(video,target_h):
    files=[f for f in video.get("video_files",[]) if f.get("file_type")=="video/mp4" and f.get("height")]
    if not files: return None
    ge=[f for f in files if f["height"]>=target_h]
    if ge: return min(ge,key=lambda f:f["height"])   # smallest file that still covers the target
    return max(files,key=lambda f:f["height"])        # else the biggest available

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--plan",required=True); ap.add_argument("--assets",default="assets")
    ap.add_argument("--res",default=None)
    a=ap.parse_args()
    plan=json.load(open(a.plan,encoding="utf-8"))
    res=a.res or plan.get("resolution") or [1920,1080]
    if isinstance(res,str): res=[int(x) for x in res.lower().split("x")]
    target_h=int(res[1])
    brolls=[o for o in plan.get("overlays",[]) if o.get("type")=="broll"]
    if not brolls:
        print("broll: aucun overlay 'broll' dans le plan — rien à faire"); return
    key=load_key()
    if not key:
        print("!! PEXELS_API_KEY introuvable (env ou .env)"); sys.exit(1)
    os.makedirs(a.assets,exist_ok=True)
    credits_path=os.path.join(a.assets,"broll_credits.json")
    credits=json.load(open(credits_path,encoding="utf-8")) if os.path.exists(credits_path) else {}
    for ov in brolls:
        out=os.path.join(a.assets,ov["id"]+".mp4")
        if os.path.exists(out) and os.path.getsize(out)>0:
            print(f"  {ov['id']}: déjà téléchargé — sauté"); continue
        q=ov.get("query")
        if not q: print(f"  ! {ov['id']}: champ 'query' manquant"); continue
        need=float(ov.get("dur",5))+0.5
        data=api("https://api.pexels.com/videos/search?"+urllib.parse.urlencode(
            {"query":q,"per_page":8,"orientation":"landscape"}),key)
        chosen=None; cf=None
        for v in data.get("videos",[]):
            if float(v.get("duration",0))<need: continue
            f=pick_file(v,target_h)
            if f: chosen,cf=v,f; break
        if not chosen:
            print(f"  ! {ov['id']}: aucun résultat Pexels adapté pour '{q}'"); continue
        print(f"  {ov['id']}: '{q}' -> pexels#{chosen['id']} {cf['width']}x{cf['height']} {chosen['duration']}s")
        download(cf["link"],out)
        credits[ov["id"]]={"pexels_url":chosen.get("url"),"author":chosen.get("user",{}).get("name"),
                           "author_url":chosen.get("user",{}).get("url"),"query":q}
    json.dump(credits,open(credits_path,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print(f"broll: OK ({len(brolls)} clip(s)) — crédits dans {credits_path}")

if __name__=="__main__": main()
