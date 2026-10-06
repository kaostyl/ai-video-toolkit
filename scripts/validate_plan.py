#!/usr/bin/env python3
"""
validate_plan.py — Sanity-check a plan.json BEFORE spending minutes rendering.
Catches: duplicate/missing ids, unknown types, missing required fields, time
overlaps, pacing problems, durations out of recommended range, overlays past the
end of the video, unknown SFX names, sfx_events outside the overlay window, and
texts that are too long for the right-side layout.

Exit code: 0 = OK (warnings allowed), 1 = at least one ERROR.

Usage:
    python validate_plan.py --plan out/plan.json [--source "video.mp4"] [--sfx-dir sfx] [--strict]
"""
import os, json, argparse, subprocess, sys, math, re

EDGE={"title_band","lower_third","keyword_pop","broll"}
SCHEMA={"schema_requirements","schema_bignumber","schema_barcompare","schema_table","schema_checklist","schema_ranking"}
REQUIRED={
 "title_band":["big"], "lower_third":["title"], "keyword_pop":["text"], "broll":["query"],
 "schema_requirements":["reqs"], "schema_bignumber":["number"],
 "schema_barcompare":["bars"], "schema_table":["title","colA","colB"], "schema_checklist":["rows"],
 "schema_ranking":["items"],
}
DUR_RANGE={  # recommended (soft) duration ranges, seconds
 "title_band":(4,9),"lower_third":(4,8),"keyword_pop":(3,7),"broll":(3,9),
 "schema_requirements":(6,10),"schema_bignumber":(6,10),"schema_barcompare":(6,10),
 "schema_table":(10,15),"schema_checklist":(10,15),"schema_ranking":(7,14),
}
# max text lengths for the right-side layout (approx, chars)
TEXT_LIMITS={
 "title_band":[("big",34),("small",64)],
 "lower_third":[("title",52),("sub",70)],
 "keyword_pop":[("text",64)],
}
SFX_KNOWN={"whoosh","pop","tick","riser","ding","blip","zap","charge","scan","glitch","impact","shimmer"}
COLORS={"problem","solution","neutral","gold"}

def ffprobe_duration(path):
    try:
        out=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
            "-of","default=nw=1:nk=1",path],stderr=subprocess.STDOUT).decode().strip()
        return float(out)
    except Exception: return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--plan",required=True); ap.add_argument("--source",default=None)
    ap.add_argument("--sfx-dir",default="sfx")
    ap.add_argument("--strict",action="store_true",help="warnings become errors")
    a=ap.parse_args()
    plan=json.load(open(a.plan,encoding="utf-8"))
    ovs=plan.get("overlays",[])
    errors=[]; warns=[]
    def err(m): errors.append(m)
    def warn(m): warns.append(m)
    safe_id=re.compile(r"^[A-Za-z0-9_-]+$")
    if not safe_id.fullmatch(str(plan.get("project","autoedit"))): err("project: use only letters, digits, _ and -")
    resolution=plan.get("resolution",[1920,1080])
    if not isinstance(resolution,list) or len(resolution)!=2 or any(type(v) is not int or v<2 or v>8192 or v%2 for v in resolution):
        err("resolution: require two even integers between 2 and 8192")
    fps=plan.get("fps",30)
    if type(fps) is not int or not 1<=fps<=120: err("fps: require integer between 1 and 120")
    if plan.get("side","right") not in ("left","right"): err("side: require left or right")
    timeline=[]

    if not ovs: err("plan sans overlays")
    ids=[o.get("id") for o in ovs]
    for i,o in enumerate(ovs):
        tag=o.get("id",f"overlay#{i}")
        if not o.get("id"): err(f"{tag}: 'id' manquant")
        elif not safe_id.fullmatch(str(o["id"])): err(f"{tag}: unsafe id; use letters, digits, _ and -")
        if ids.count(o.get("id"))>1: err(f"{tag}: id dupliqué")
        typ=o.get("type")
        if typ not in EDGE|SCHEMA: err(f"{tag}: type inconnu '{typ}'"); continue
        for f in REQUIRED[typ]:
            if f not in o: err(f"{tag}: champ requis '{f}' manquant pour {typ}")
        try: t=float(o["t"]); dur=float(o["dur"])
        except Exception: err(f"{tag}: t/dur manquant ou non numérique"); continue
        if not math.isfinite(t) or not math.isfinite(dur): err(f"{tag}: nonfinite t/dur"); continue
        if t<0: err(f"{tag}: t < 0")
        timeline.append((t,t+dur,tag))
        if dur<=0: err(f"{tag}: dur <= 0")
        lo,hi=DUR_RANGE[typ]
        if not (lo<=dur<=hi): warn(f"{tag}: dur {dur:g}s hors plage conseillée [{lo}-{hi}]s pour {typ}")
        col=o.get("color")
        if col and col not in COLORS and not str(col).startswith("#"): err(f"{tag}: couleur inconnue '{col}'")
        # text lengths
        for field,lim in TEXT_LIMITS.get(typ,[]):
            v=o.get(field)
            if v and len(v)>lim: warn(f"{tag}: '{field}' fait {len(v)} car. (> {lim}) — risque de pavé/3 lignes")
        if typ=="schema_table":
            for side in ("colA","colB"):
                for r in o.get(side,{}).get("rows",[]):
                    if len(r)>34: warn(f"{tag}: ligne '{r[:30]}…' > 34 car. — sera serrée dans la carte")
        if typ=="schema_checklist":
            for r in o.get("rows",[]):
                if len(r.get("text",""))>46: warn(f"{tag}: item '{r.get('text','')[:30]}…' > 46 car.")
        # sfx
        evs=o.get("sfx_events")
        if evs:
            for e in evs:
                if e.get("name") not in SFX_KNOWN: err(f"{tag}: sfx inconnu '{e.get('name')}'")
                elif not os.path.exists(os.path.join(a.sfx_dir,e["name"]+".wav")):
                    warn(f"{tag}: {e['name']}.wav absent de {a.sfx_dir}/ (lance sfx.py)")
                try: at=float(e.get("at",0)); vol=float(e.get("vol",1))
                except (ValueError,TypeError): err(f"{tag}: invalid SFX timing/gain"); continue
                if not math.isfinite(at) or not math.isfinite(vol) or not 0<=vol<=1: err(f"{tag}: SFX timing/gain must be finite and gain within 0..1")
                if at<0 or at>dur: err(f"{tag}: sfx_event at={at:g}s hors de la fenêtre [0-{dur:g}]s")
        elif o.get("sfx") and o["sfx"] not in SFX_KNOWN:
            err(f"{tag}: sfx inconnu '{o['sfx']}'")

    # timeline coherence
    tl=sorted(timeline)
    for (s1,e1,i1),(s2,e2,i2) in zip(tl,tl[1:]):
        if s2<e1: err(f"chevauchement: {i1} (fin {e1:g}s) et {i2} (début {s2:g}s)")
        elif s2-e1<3: warn(f"enchaînement serré: {i1} -> {i2} ({s2-e1:.1f}s d'écart, vise >= 3s)")
    for (s1,_,i1),(s2,_,i2) in zip(tl,tl[1:]):
        if s2-s1>45: warn(f"trou de {s2-s1:.0f}s sans overlay entre {i1} et {i2} (vise 15-25s)")

    if a.source:
        vd=ffprobe_duration(a.source)
        if vd:
            for s,e,i in tl:
                if e>vd+0.5: err(f"{i}: se termine à {e:g}s mais la vidéo fait {vd:.1f}s")
        else: warn("durée source illisible (ffprobe)")

    for w in warns: print(f"  WARN  {w}")
    for e in errors: print(f"  ERREUR {e}")
    n_err=len(errors)+(len(warns) if a.strict else 0)
    print(f"validate_plan: {len(ovs)} overlays — {len(errors)} erreur(s), {len(warns)} warning(s)"+
          (" [strict]" if a.strict else ""))
    sys.exit(1 if n_err else 0)

if __name__=="__main__": main()
