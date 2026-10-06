#!/usr/bin/env python3
"""
davinci_timeline.py — Build a DaVinci-Resolve-importable FCPXML timeline from a
plan.json + the rendered overlay assets + the SFX, so you get an EDITABLE timeline
(separate tracks) instead of a flat MP4.

Layout produced:
  - Lane 0 (primary)  : the source video (its own audio = the voice).
  - Lanes 1..N (video): every overlay asset (ProRes 4444 .mov, alpha) at its plan
                        timecode. Overlays are interval-packed onto as few lanes as
                        possible (they never overlap in time -> usually 1 lane).
  - Lanes -1.. (audio): every SFX event (single "sfx" or timed "sfx_events"),
                        interval-packed onto as few audio lanes as possible.

Import in Resolve:  Media Pool > right-click > Timelines > Import > AAF/EDL/XML…
                    (or File > Import > Timeline) then pick the .fcpxml.
If any clip is "Media Offline", right-click > Relink to the assets/ + sfx/ folders.

Usage:
    python davinci_timeline.py --plan plan.json --source "video.mp4" \
        --assets assets --sfx-dir sfx --out output/project.fcpxml [--res 3840x2160] [--fps 30]
"""
import os, sys, json, argparse, subprocess
from urllib.parse import quote
from xml.sax.saxutils import escape

def xml_attr(value):
    return escape(str(value), {'"':'&quot;', "'":'&apos;'})

def ffprobe_duration(path):
    try:
        out=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
            "-of","default=nw=1:nk=1",path],stderr=subprocess.STDOUT).decode().strip()
        return float(out)
    except Exception: return None

def file_url(path):
    p=os.path.abspath(path).replace("\\","/")
    if not p.startswith("/"): p="/"+p          # X:/... -> /X:/...
    return "file://"+quote(p, safe="/:")

def fdur(frames,fps): return f"{int(frames)}/{int(fps)}s"

def pack_lanes(items):
    """items: list of (start_f, end_f, payload). Returns list with lane index added,
    greedily packing non-overlapping items onto the fewest lanes."""
    lanes=[]  # each lane = last end_f
    out=[]
    for s,e,p in sorted(items,key=lambda x:x[0]):
        placed=None
        for li,last in enumerate(lanes):
            if s>=last: lanes[li]=e; placed=li; break
        if placed is None: lanes.append(e); placed=len(lanes)-1
        out.append((placed,s,e,p))
    return out,len(lanes)

def asset_path(assets,oid):
    for ext in (".mov",".mp4"):
        p=os.path.join(assets,oid+ext)
        if os.path.exists(p): return p
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--plan",required=True); ap.add_argument("--source",required=True)
    ap.add_argument("--assets",default="assets"); ap.add_argument("--sfx-dir",default="sfx")
    ap.add_argument("--out",default="output/project.fcpxml")
    ap.add_argument("--res",default=None); ap.add_argument("--fps",default=None)
    a=ap.parse_args()
    plan=json.load(open(a.plan,encoding="utf-8"))
    res=a.res or plan.get("resolution") or [1920,1080]
    if isinstance(res,str): res=[int(x) for x in res.lower().split("x")]
    W,H=int(res[0]),int(res[1]); fps=int(a.fps or plan.get("fps",30))
    os.makedirs(os.path.dirname(a.out) or ".",exist_ok=True)

    src_dur=ffprobe_duration(a.source) or 0.0
    total_f=max(1,round(src_dur*fps))

    resources=[f'<format id="r1" name="FFVideoFormat{W}x{H}p{fps}" frameDuration="1/{fps}s" width="{W}" height="{H}" colorSpace="1-1-1 (Rec. 709)"/>']
    # source asset
    resources.append(
        f'<asset id="a0" name="{xml_attr(os.path.basename(a.source))}" start="0s" duration="{fdur(total_f,fps)}" '
        f'hasVideo="1" hasAudio="1" videoSources="1" audioSources="1" audioChannels="2" audioRate="48000" format="r1">'
        f'<media-rep kind="original-media" src="{file_url(a.source)}"/></asset>')

    overlays=plan["overlays"]
    # ---- overlay video clips ----
    vid_items=[]; aid=1; missing=[]
    for ov in overlays:
        p=asset_path(a.assets,ov["id"])
        if not p: missing.append(ov["id"]); continue
        n=int(float(ov["dur"])*fps); s=round(float(ov["t"])*fps)
        rid=f"a{aid}"; aid+=1
        resources.append(
            f'<asset id="{rid}" name="{ov["id"]}" start="0s" duration="{fdur(n,fps)}" '
            f'hasVideo="1" videoSources="1" format="r1"><media-rep kind="original-media" src="{file_url(p)}"/></asset>')
        vid_items.append((s,s+n,{"ref":rid,"name":ov["id"],"off":s,"n":n}))
    vid_packed,nvlanes=pack_lanes(vid_items)

    # ---- sfx audio clips ----
    sfx_dur_cache={}
    def sfx_frames(name):
        if name not in sfx_dur_cache:
            d=ffprobe_duration(os.path.join(a.sfx_dir,name+".wav")) or 0.2
            sfx_dur_cache[name]=max(1,round(d*fps))
        return sfx_dur_cache[name]
    def sfx_events(ov):
        ev=ov.get("sfx_events")
        if ev: return [(float(e["at"]),e["name"]) for e in ev]
        if ov.get("sfx"): return [(0.0,ov["sfx"])]
        return []
    sfx_assets={}  # name -> resource id
    sfx_items=[]
    for ov in overlays:
        for at,name in sfx_events(ov):
            wp=os.path.join(a.sfx_dir,name+".wav")
            if not os.path.exists(wp): continue
            if name not in sfx_assets:
                rid=f"a{aid}"; aid+=1; sfx_assets[name]=rid
                resources.append(
                    f'<asset id="{rid}" name="{name}" start="0s" duration="{fdur(sfx_frames(name),fps)}" '
                    f'hasAudio="1" audioSources="1" audioChannels="2" audioRate="48000">'
                    f'<media-rep kind="original-media" src="{file_url(wp)}"/></asset>')
            s=round((float(ov["t"])+at)*fps); n=sfx_frames(name)
            sfx_items.append((s,s+n,{"ref":sfx_assets[name],"name":name,"off":s,"n":n}))
    sfx_packed,nalanes=pack_lanes(sfx_items)

    # ---- build spine (connected clips hang off the base source clip) ----
    conn=[]
    for lane,s,e,p in vid_packed:
        conn.append(f'<asset-clip ref="{p["ref"]}" lane="{lane+1}" offset="{fdur(p["off"],fps)}" '
                    f'name="{p["name"]}" duration="{fdur(p["n"],fps)}" start="0s" format="r1"/>')
    for lane,s,e,p in sfx_packed:
        conn.append(f'<asset-clip ref="{p["ref"]}" lane="{-(lane+1)}" offset="{fdur(p["off"],fps)}" '
                    f'name="{p["name"]}" duration="{fdur(p["n"],fps)}" start="0s"/>')
    base=(f'<asset-clip ref="a0" offset="0s" name="{xml_attr(os.path.basename(a.source))}" '
          f'duration="{fdur(total_f,fps)}" start="0s" format="r1">'+"".join(conn)+'</asset-clip>')

    proj=plan.get("project","autoedit")
    xml=('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n<fcpxml version="1.9">\n'
         '  <resources>\n    '+"\n    ".join(resources)+'\n  </resources>\n'
         '  <library>\n    <event name="Video Toolkit AutoEdit">\n'
         f'      <project name="{xml_attr(proj)}">\n'
         f'        <sequence format="r1" duration="{fdur(total_f,fps)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">\n'
         '          <spine>\n            '+base+'\n          </spine>\n'
         '        </sequence>\n      </project>\n    </event>\n  </library>\n</fcpxml>\n')
    open(a.out,"w",encoding="utf-8").write(xml)
    print(f"FCPXML -> {a.out}")
    print(f"  source: {src_dur:.2f}s @ {fps}fps  ({W}x{H})")
    print(f"  overlays: {len(vid_items)} clips on {nvlanes} video lane(s)")
    print(f"  sfx: {len(sfx_items)} clips on {nalanes} audio lane(s)")
    if missing: print("  ! assets manquants (ignorés):",", ".join(missing))

if __name__=="__main__": main()
