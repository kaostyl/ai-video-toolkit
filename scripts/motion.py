#!/usr/bin/env python3
"""
motion.py — "Premium Broadcast HUD" design system (V4).
Reads a plan.json and renders each overlay to assets/<id>.mov (ProRes 4444, alpha).

Design language:
  - Kinetic typography: masked line reveals (text slides up behind an invisible
    edge), staggered, with spring/overshoot easing.
  - HUD cards: animated corner brackets, gradient hairline, drifting dot grid,
    shine sweep, deep shadow. Frosted-glass blur behind is done by compose.py.
  - Sticker pills: gradient fill + white keyline + hard offset shadow, entering
    with a rotation-spring.
  - Particle bursts when a check/cross completes or a big number lands.
  - Gradient bars with glowing caps; zig-zag table rows.

Everything anchored to ONE side (default: right); talking-head stays visible.
2x supersampling everywhere shapes are drawn; frames piped straight to ffmpeg.

Usage:
    python motion.py --plan plan.json --out assets/ [--res 3840x2160] [--side right|left] [--only id1,id2]
"""
import os, sys, json, math, argparse, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------- fonts ----------------
def _find_font(names, fallback):
    roots = [
        "/usr/share/fonts/truetype/google-fonts", "/usr/share/fonts/truetype/lato",
        "/usr/share/fonts/truetype/dejavu", "C:/Windows/Fonts",
        os.path.expanduser("~/.fonts"), os.path.join(os.path.dirname(__file__), "fonts"),
    ]
    for n in names:
        for r in roots:
            p = os.path.join(r, n)
            if os.path.exists(p): return p
    if os.path.exists(fallback): return fallback
    is_bold = "Bold" in fallback
    for candidate in (
        "C:/Windows/Fonts/arialbd.ttf" if is_bold else "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if is_bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        if os.path.exists(candidate): return candidate
    return fallback
POPB = _find_font(["Poppins-Bold.ttf"],  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
POPM = _find_font(["Poppins-Medium.ttf"], POPB)
LATO = _find_font(["Lato-Semibold.ttf","Lato-Regular.ttf"], "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

INK=(238,242,250); MUT=(158,168,188); DARK=(10,12,16)
DEFAULT_STYLE={"problem":"#FF4545","solution":"#2DD48D","neutral":"#38BDF8","gold":"#FBBF24"}
def hex2rgb(h):
    h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))

# ---------------- globals set per render ----------------
W=H=FPS=0; S=1.0
SIDE="right"; MARGIN=0; AX=0; COLW=0; COLCX=0
CARD_W=CARD_H=CARD_X0=CARD_Y0=0

def F(path,size): return ImageFont.truetype(path, max(1,int(round(size*S))))
def P(x): return int(round(x*S))
def eoc(t): return 1-(1-t)**3
def eib(t):
    c1=1.70158; c3=c1+1
    return 1+c3*(t-1)**3+c1*(t-1)**2
def seg(t,a,b):
    if t<=a: return 0.0
    if t>=b: return 1.0
    return (t-a)/(b-a)
def lerp(p,q,a): return (p[0]+(q[0]-p[0])*a, p[1]+(q[1]-p[1])*a)
def meas(d,s,f): b=d.textbbox((0,0),s,font=f); return b[2]-b[0],b[3]-b[1]
def wrap(d,s,f,maxw):
    words=s.split(); lines=[]; cur=""
    for w in words:
        test=(cur+" "+w).strip()
        if not cur or meas(d,test,f)[0]<=maxw: cur=test
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines or [s]
def rr(d,box,r,**kw): d.rounded_rectangle(box,radius=r,**kw)
def lighten(c,f): return tuple(min(255,int(x+(255-x)*f)) for x in c)
def darken(c,f): return tuple(int(x*f) for x in c)

def rr_gradient(img,box,r,c_top,c_bot):
    x0,y0,x1,y1=[int(v) for v in box]; w,h=x1-x0,y1-y0
    if w<=0 or h<=0: return
    tt=np.linspace(0,1,h,dtype=np.float32)[:,None]
    top=np.array(c_top,np.float32); bot=np.array(c_bot,np.float32)
    arr=(top[None,None,:]*(1-tt[...,None])+bot[None,None,:]*tt[...,None]).astype(np.uint8)
    arr=np.repeat(arr,w,axis=1)
    g=Image.fromarray(arr,"RGB")
    m=Image.new("L",(w,h),0); ImageDraw.Draw(m).rounded_rectangle([0,0,w-1,h-1],r,fill=255)
    img.paste(g,(x0,y0),m)

def glow_shape(img,draw_fn,blur,alpha):
    gl=Image.new("RGBA",img.size,(0,0,0,0)); draw_fn(ImageDraw.Draw(gl))
    gl=gl.filter(ImageFilter.GaussianBlur(blur))
    if alpha<1.0:
        al=gl.split()[3].point(lambda p:int(p*alpha)); gl.putalpha(al)
    img.alpha_composite(gl)

def masked_line(text,font,prog,fill,overshoot=True):
    """Kinetic-typo primitive: the text slides UP from behind an invisible edge."""
    tmp=ImageDraw.Draw(Image.new("RGBA",(4,4)))
    bb=tmp.textbbox((0,0),text,font=font); w=bb[2]-bb[0]; h=bb[3]-bb[1]
    pad=max(4,int(h*0.5))
    box=Image.new("RGBA",(w+10,h+pad+6),(0,0,0,0))
    if prog<=0: return box
    e=(eib if overshoot else eoc)(min(1,prog))
    off=int((1-e)*(h+pad))
    ImageDraw.Draw(box).text((5-bb[0],3-bb[1]+off),text,font=font,fill=fill)
    return box

def particles(img,cx,cy,col,prog,n=12,rad=150,seed=1):
    if prog<=0.001 or prog>=0.999: return
    d=ImageDraw.Draw(img); e=eoc(prog)
    for k in range(n):
        a=2*math.pi*(k/n)+math.sin(seed*7.31+k*12.9)*0.55
        rk=P(rad)*e*(0.65+0.35*((k*37%10)/10.0))
        px,py=cx+math.cos(a)*rk,cy+math.sin(a)*rk*0.8
        s=max(1,int(P(8)*(1-prog)))
        d.ellipse([px-s,py-s,px+s,py+s],fill=col+(int(235*(1-prog)),))

def tracked(d,x,y,text,font,fill,tr=0.16,right=False):
    """Letter-spaced small-caps editorial label. Returns total width."""
    text=text.upper()
    widths=[meas(d,ch,font)[0] for ch in text]
    trp=int(font.size*tr)
    total=sum(widths)+trp*(len(text)-1) if text else 0
    cx=x-total if right else x
    for ch,wd in zip(text,widths):
        d.text((cx,y),ch,font=font,fill=fill,anchor="lm"); cx+=wd+trp
    return total

_dots={}
def dotgrid(w,h,step,r,alpha):
    key=(w,h,step,r,alpha)
    if key not in _dots:
        im=Image.new("RGBA",(w+step,h+step),(0,0,0,0)); dd=ImageDraw.Draw(im)
        for yy in range(0,h+2*step,step):
            for xx in range(0,w+2*step,step):
                dd.ellipse([xx-r,yy-r,xx+r,yy+r],fill=(255,255,255,alpha))
        _dots[key]=im
    return _dots[key]

def sticker_chip(img,cx,cy,label,col,fs=44):
    """Gradient pill + white keyline + hard offset shadow (premium sticker)."""
    d=ImageDraw.Draw(img); f=F(POPB,fs); tw,th=meas(d,label,f); bw,bh=tw+P(66),th+P(36)
    x0,y0=int(cx-bw/2),int(cy-bh/2)
    d.rounded_rectangle([x0+P(9),y0+P(11),x0+bw+P(9),y0+bh+P(11)],bh//2,fill=(0,0,0,165))
    rr_gradient(img,[x0,y0,x0+bw,y0+bh],bh//2,lighten(col,0.28),darken(col,0.8))
    d=ImageDraw.Draw(img)
    d.rounded_rectangle([x0,y0,x0+bw,y0+bh],bh//2,outline=(255,255,255,235),width=max(2,P(4)))
    d.text((cx,cy),label,font=f,fill=DARK,anchor="mm")

def hud_kicker(img,t,label,col,y=None):
    """Small-caps tracked label with accent square + thin rule (HUD editorial)."""
    d=ImageDraw.Draw(img); y=y if y is not None else P(140)
    f=F(POPB,33); e=eoc(seg(t,0.02,0.3)); a=int(255*e)
    if a<=0: return
    tmp=ImageDraw.Draw(Image.new("RGBA",(4,4)))
    widths=[meas(tmp,ch,f)[0] for ch in label.upper()]
    trp=int(f.size*0.16); total=sum(widths)+trp*(len(label)-1)
    sq=P(20); grp=sq+P(26)+total
    x=W//2-grp//2+int((1-e)*P(36))
    d.rounded_rectangle([x,y-sq//2,x+sq,y+sq//2],P(5),fill=col+(a,))
    tracked(d,x+sq+P(26),y,label,f,(236,240,248,a))
    rw=int(P(120)*e)
    d.rectangle([W//2-rw,y+P(34),W//2+rw,y+P(34)+P(3)],fill=(255,255,255,int(38*e)))

# ---------------- EDGE OVERLAYS (full frame, alpha) ----------------
def draw_title_band(img,t,ov,C):
    layer=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(layer)
    col=C(ov.get("color","problem")); col2=lighten(col,0.45)
    right=SIDE!="left"; ax=AX if right else MARGIN
    fbig=F(POPB,86); fsm=F(LATO,38)
    tmp=ImageDraw.Draw(Image.new("RGBA",(4,4)))
    big_lines=wrap(tmp,ov["big"],fbig,COLW)
    sm_lines=wrap(tmp,ov.get("small",""),fsm,COLW) if ov.get("small") else []
    gap=P(104)
    total_h=len(big_lines)*gap+((P(26)+len(sm_lines)*P(52)) if sm_lines else 0)
    cy=int(H*0.46); ytop=cy-total_h//2
    # dark halo for readability on bright walls
    halo=Image.new("RGBA",(W,H),(0,0,0,0)); hd=ImageDraw.Draw(halo)
    yy=ytop
    for ln in big_lines:
        hd.text((ax,yy+P(44)),ln,font=fbig,fill=(0,0,0,255),anchor=("rm" if right else "lm")); yy+=gap
    halo=halo.filter(ImageFilter.GaussianBlur(int(13*S)))
    al=halo.split()[3].point(lambda p:int(p*0.72)); halo.putalpha(al); layer.alpha_composite(halo)
    # accent rule with glow, growing
    uw=int(P(350)*eoc(seg(t,0.05,0.38))); yline=ytop-P(40)
    ul=[ax-uw,yline-P(6),ax,yline+P(2)] if right else [ax,yline-P(6),ax+uw,yline+P(2)]
    if uw>2:
        glow_shape(layer,lambda g: g.rectangle(ul,fill=col+(255,)),int(11*S),0.9)
        rr_gradient(layer,ul,P(3),col2,col)
    # big lines: masked reveal, staggered
    yy=ytop; d=ImageDraw.Draw(layer)
    for i,ln in enumerate(big_lines):
        box=masked_line(ln,fbig,seg(t,0.06+i*0.08,0.42+i*0.08),INK+(255,))
        bx=(ax-box.width+5) if right else (ax-5)
        layer.alpha_composite(box,(bx,yy)); yy+=gap
    # small lines: fade + slide, delayed
    if sm_lines:
        sp=eoc(seg(t,0.34,0.62)); yy+=P(26)
        if sp>0.01:
            sub=Image.new("RGBA",(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sub)
            soff=int((1-sp)*P(34))
            for ln in sm_lines:
                sd.text((ax,yy+P(24)+soff),ln,font=fsm,fill=MUT+(255,),anchor=("rm" if right else "lm")); yy+=P(52)
            al=sub.split()[3].point(lambda p:int(p*sp)); sub.putalpha(al); layer.alpha_composite(sub)
    op=seg(t,0.9,1.0)
    if op>0:
        al=layer.split()[3].point(lambda p:int(p*(1-op))); layer.putalpha(al)
    img.alpha_composite(layer)

def draw_lower_third(img,t,ov,C):
    global S
    color=C(ov.get("color","neutral")); title=ov["title"]; sub=ov.get("sub","")
    S*=2
    ft=F(POPB,52); fs=F(LATO,33); tmp=ImageDraw.Draw(Image.new("RGBA",(4,4)))
    maxw=(COLW*2)-P(150)
    tlines=wrap(tmp,title,ft,maxw); slines=wrap(tmp,sub,fs,maxw) if sub else []
    tw=max(meas(tmp,l,ft)[0] for l in tlines); sw=(max(meas(tmp,l,fs)[0] for l in slines) if slines else 0)
    contentw=max(tw,sw); bw=contentw+P(150); lht=P(66); lhs=P(48)
    bh=P(34)+len(tlines)*lht+((P(10)+len(slines)*lhs) if slines else 0)+P(34); pad=P(46)
    c=Image.new("RGBA",(bw+pad*2,bh+pad*2),(0,0,0,0)); ox=oy=pad
    # deep soft shadow
    sh=Image.new("RGBA",c.size,(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([ox,oy+P(12),ox+bw,oy+bh+P(12)],P(22),fill=(0,0,0,170))
    sh=sh.filter(ImageFilter.GaussianBlur(int(20*S))); c=Image.alpha_composite(c,sh); cd=ImageDraw.Draw(c)
    rr(cd,[ox,oy,ox+bw,oy+bh],P(22),fill=(13,17,26,228))
    cd.rounded_rectangle([ox,oy,ox+bw,oy+bh],P(22),outline=(255,255,255,34),width=max(1,P(2)))
    # gradient accent sidebar with glow
    glow_shape(c,lambda g: g.rectangle([ox,oy,ox+P(18),oy+bh],fill=color+(255,)),int(13*S),0.85)
    rr_gradient(c,[ox,oy,ox+P(18),oy+bh],P(8),lighten(color,0.35),darken(color,0.8))
    cd=ImageDraw.Draw(c)
    # pulsing accent dot
    pu=1+0.3*math.sin(min(1,seg(t,0.08,0.55))*math.pi)
    dr=int(P(9)*pu); dcx,dcy=ox+P(52),oy+P(34)+lht//2
    cd.ellipse([dcx-dr,dcy-dr,dcx+dr,dcy+dr],fill=color+(255,))
    # title: masked reveal ; sub: fade-slide
    tx=ox+P(86); ty=oy+P(34)
    for i,l in enumerate(tlines):
        box=masked_line(l,ft,seg(t,0.08+i*0.06,0.42+i*0.06),INK+(255,))
        c.alpha_composite(box,(tx-5,ty)); ty+=lht
    if slines:
        sp=eoc(seg(t,0.3,0.58)); ty+=P(10)
        if sp>0.01:
            sub_l=Image.new("RGBA",c.size,(0,0,0,0)); sd=ImageDraw.Draw(sub_l)
            soff=int((1-sp)*P(22))
            for l in slines:
                sd.text((tx,ty+lhs//2+soff),l,font=fs,fill=MUT+(255,),anchor="lm"); ty+=lhs
            al=sub_l.split()[3].point(lambda p:int(p*sp)); sub_l.putalpha(al); c=Image.alpha_composite(c,sub_l)
    S/=2; pad=pad//2; bw=bw//2
    c=c.resize((c.width//2,c.height//2),Image.LANCZOS)
    ip=eib(min(1,seg(t,0,0.3))); op=seg(t,0.9,1.0); a=1-op; xoff=int((1-min(1,ip))*P(80))
    # slight settle rotation
    ang=(1-min(1,ip))*2.0
    if abs(ang)>0.05: c=c.rotate(ang,resample=Image.BICUBIC,expand=True)
    cw,ch=c.size; cyc=int(H*0.60); by=cyc-ch//2
    bx=(AX-(pad+bw)+xoff) if SIDE!="left" else (MARGIN-pad-xoff)
    if a<1.0:
        al=c.split()[3].point(lambda p:int(p*a)); c=c.copy(); c.putalpha(al)
    img.alpha_composite(c,(bx,by))

def draw_keyword_pop(img,t,ov,C):
    global S
    color=C(ov.get("color","neutral")); text=ov["text"]
    S*=2
    f=F(POPB,54); tmp=ImageDraw.Draw(Image.new("RGBA",(4,4)))
    maxw=(COLW*2)-P(90); lines=wrap(tmp,text,f,maxw); lw=max(meas(tmp,l,f)[0] for l in lines); lh=P(66)
    bw=lw+P(92); bh=len(lines)*lh+P(48); pad=P(40); rad=bh//2 if len(lines)==1 else P(34)
    c=Image.new("RGBA",(bw+pad*2,bh+pad*2),(0,0,0,0)); ox=oy=pad
    cd=ImageDraw.Draw(c)
    # sticker: hard offset shadow, gradient fill, white keyline
    cd.rounded_rectangle([ox+P(12),oy+P(14),ox+bw+P(12),oy+bh+P(14)],rad,fill=(0,0,0,175))
    rr_gradient(c,[ox,oy,ox+bw,oy+bh],rad,lighten(color,0.3),darken(color,0.78))
    cd=ImageDraw.Draw(c)
    cd.rounded_rectangle([ox,oy,ox+bw,oy+bh],rad,outline=(255,255,255,240),width=max(2,P(5)))
    ty=oy+(bh-len(lines)*lh)//2+lh//2
    for l in lines: cd.text((ox+bw//2,ty),l,font=f,fill=DARK,anchor="mm"); ty+=lh
    S/=2
    ip=min(1,eib(min(1,seg(t,0,0.26)))); op=seg(t,0.9,1.0); a=1-op
    sc=0.5+0.5*ip
    cw,ch=c.size[0]//2,c.size[1]//2
    nw,nh=max(1,int(cw*sc)),max(1,int(ch*sc))
    cc=c.resize((nw,nh),Image.LANCZOS)
    ang=(1-ip)*(-6.0)
    if abs(ang)>0.05: cc=cc.rotate(ang,resample=Image.BICUBIC,expand=True)
    if a<1.0:
        al=cc.split()[3].point(lambda p:int(p*a)); cc=cc.copy(); cc.putalpha(al)
    cyc=int(H*0.52)
    img.alpha_composite(cc,(COLCX-cc.width//2,cyc-cc.height//2))

# ---------------- HUD CARD (schemas draw inside) ----------------
def schema_card(img,t,ov,C):
    acc=C(ov.get("color","neutral")); ins=P(18); rad=P(36)
    sh=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([ins,ins+P(16),W-ins,H-ins+P(16)],rad,fill=(0,0,0,175))
    sh=sh.filter(ImageFilter.GaussianBlur(int(28*S))); img.alpha_composite(sh)
    d=ImageDraw.Draw(img)
    rr(d,[ins,ins,W-ins,H-ins],rad,fill=(7,10,17,198))
    # drifting dot grid, clipped to card
    step=P(64); grid=dotgrid(W,H,step,max(1,P(2)),13)
    ox=int(t*step*0.8)%step
    gcrop=grid.crop((ox,0,ox+W,H))
    gm=Image.new("L",(W,H),0); ImageDraw.Draw(gm).rounded_rectangle([ins,ins,W-ins,H-ins],rad,fill=255)
    gl=Image.new("RGBA",(W,H),(0,0,0,0)); gl.paste(gcrop,(0,0),gm)
    img.alpha_composite(gl)
    d=ImageDraw.Draw(img)
    # hairline border + gradient top hairline
    rr(d,[ins,ins,W-ins,H-ins],rad,outline=(255,255,255,34),width=max(1,P(2)))
    hw=int((W-2*ins-2*rad)*0.62)
    hx=ins+rad
    tt=np.linspace(1,0,hw,dtype=np.float32)
    hl=np.zeros((max(1,P(4)),hw,4),np.uint8)
    hl[...,0]=acc[0]; hl[...,1]=acc[1]; hl[...,2]=acc[2]
    hl[...,3]=(tt*210).astype(np.uint8)[None,:]
    img.alpha_composite(Image.fromarray(hl,"RGBA"),(hx,ins))
    # animated corner brackets with glow
    bl=int(P(70)*eoc(seg(t,0.03,0.3))); bw_=max(2,P(7)); m=P(2)
    if bl>2:
        def brackets(g):
            for cx,cy,dx,dy in [(ins+m,ins+m,1,1),(W-ins-m,ins+m,-1,1),(ins+m,H-ins-m,1,-1),(W-ins-m,H-ins-m,-1,-1)]:
                g.line([(cx,cy),(cx+dx*bl,cy)],fill=acc+(255,),width=bw_)
                g.line([(cx,cy),(cx,cy+dy*bl)],fill=acc+(255,),width=bw_)
        glow_shape(img,brackets,int(11*S),0.8)
        d=ImageDraw.Draw(img); brackets(d)
    # shine sweep during entrance
    sp=seg(t,0.04,0.5)
    if 0.0<sp<1.0:
        xs=np.arange(W,dtype=np.float32)[None,:]; ys=np.arange(H,dtype=np.float32)[:,None]
        pos=(-0.35+1.75*eoc(sp))*W
        a=np.exp(-((xs+0.35*ys-pos)/(0.085*W))**2)*46.0
        a*=np.asarray(gm,np.float32)/255.0
        shine=np.zeros((H,W,4),np.uint8); shine[...,:3]=255; shine[...,3]=a.astype(np.uint8)
        img.alpha_composite(Image.fromarray(shine,"RGBA"))

# ---------------- SCHEMAS (card space) ----------------
def draw_schema_requirements(img,t,ov,C):
    d=ImageDraw.Draw(img); col=C(ov.get("color","problem")); gold=C("gold"); neu=C("neutral")
    hud_kicker(img,t,ov.get("kicker","LE SEUIL"),col)
    reqs=ov["reqs"]; cy=P(470); cw,ch=P(590),P(214); n=len(reqs); spread=P(360)
    xs=[W//2+int((i-(n-1)/2)*spread*2) for i in range(n)]
    for i,(big,small) in enumerate(reqs):
        prog=eib(min(1,seg(t,0.1+i*0.1,0.5+i*0.1))); pc=min(1,prog); off=int((1-pc)*P(90)); cx=xs[i]
        if pc<=0.01: continue
        rr_gradient(img,[cx-cw//2,cy-ch//2-off,cx+cw//2,cy+ch//2-off],P(26),(24,32,47),(14,19,29))
        d=ImageDraw.Draw(img)
        rr(d,[cx-cw//2,cy-ch//2-off,cx+cw//2,cy+ch//2-off],P(26),outline=neu+(220,),width=P(3))
        d.text((cx,cy-P(32)-off),big,font=F(POPB,84),fill=INK,anchor="mm")
        d.text((cx,cy+P(56)-off),small,font=F(LATO,36),fill=MUT,anchor="mm")
        if i<n-1 and t>0.28:
            ps=min(1.06,eib(min(1,seg(t,0.26,0.44))))
            d.text(((xs[i]+xs[i+1])//2,cy),"+",font=F(POPB,int(96*ps)),fill=INK,anchor="mm")
            particles(img,(xs[i]+xs[i+1])//2,cy,neu,seg(t,0.3,0.5),n=8,rad=90,seed=5)
    p3=eib(min(1,seg(t,0.55,0.82)))
    if p3>0.02:
        ay=cy+P(158); d=ImageDraw.Draw(img)
        d.polygon([(W//2-P(24),ay),(W//2+P(24),ay),(W//2,ay+P(36))],fill=gold)
        ry=ay+P(150)
        glow_shape(img,lambda g: rr(g,[W//2-P(380),ry-P(70),W//2+P(380),ry+P(70)],P(24),outline=gold+(255,),width=P(6)),int(13*S),0.6)
        rr_gradient(img,[W//2-P(380),ry-P(70),W//2+P(380),ry+P(70)],P(24),(34,28,14),(20,16,9))
        d=ImageDraw.Draw(img)
        rr(d,[W//2-P(380),ry-P(70),W//2+P(380),ry+P(70)],P(24),outline=gold+(255,),width=P(3))
        box=masked_line(ov.get("result","AdSense / Pub"),F(POPB,58),seg(t,0.58,0.85),gold+(255,))
        img.alpha_composite(box,(W//2-box.width//2,ry-P(44)))
        particles(img,W//2,ry,gold,seg(t,0.62,0.85),n=12,rad=200,seed=7)
    if ov.get("note"):
        p4=seg(t,0.72,0.95); d=ImageDraw.Draw(img)
        if p4>0.05: d.text((W//2,H-P(86)),ov["note"],font=F(LATO,40),fill=MUT+(int(255*p4),),anchor="mm")

def draw_schema_bignumber(img,t,ov,C):
    d=ImageDraw.Draw(img); col=C(ov.get("color","solution"))
    hud_kicker(img,t,ov.get("kicker","AUCUN SEUIL"),col)
    num=str(ov.get("number","0")); disp=num
    if num.lstrip("+-").isdigit():
        tgt=int(num); cur=int(round(tgt*eoc(min(1,seg(t,0.1,0.5))))); disp=("+" if num.startswith("+") else "")+str(cur)
    scf=0.55+0.45*min(1.06,eib(min(1,seg(t,0.08,0.48))))
    fnum=F(POPB,int(370*scf))
    glow_shape(img,lambda g: g.text((W//2,P(450)),disp,font=fnum,fill=col+(255,),anchor="mm"),int(22*S),0.9)
    d=ImageDraw.Draw(img)
    d.text((W//2,P(450)),disp,font=fnum,fill=col,anchor="mm")
    particles(img,W//2,P(450),col,seg(t,0.45,0.68),n=14,rad=300,seed=3)
    if t>0.3:
        box=masked_line(ov.get("label","seuil requis"),F(POPM,56),seg(t,0.3,0.55),INK+(255,))
        img.alpha_composite(box,(W//2-box.width//2,P(620)))
    if ov.get("line"):
        box=masked_line(ov["line"],F(POPB,64),seg(t,0.5,0.78),INK+(255,))
        img.alpha_composite(box,(W//2-box.width//2,H-P(230)))
    p3=seg(t,0.62,0.9); d=ImageDraw.Draw(img)
    if ov.get("note") and p3>0.05:
        d.text((W//2,H-P(96)),ov["note"],font=F(LATO,38),fill=MUT+(int(255*p3),),anchor="mm")

def draw_schema_barcompare(img,t,ov,C):
    d=ImageDraw.Draw(img)
    hud_kicker(img,t,ov.get("kicker","COMPARAISON"),C("neutral"))
    base=P(840); maxh=P(500); bars=ov["bars"]; n=len(bars); spread=P(330)
    xs=[W//2+int((i-(n-1)/2)*spread*2) for i in range(n)]
    # baseline rule draws itself
    rw=int(P(760)*eoc(seg(t,0.04,0.3)))
    d.rectangle([W//2-rw,base+P(8),W//2+rw,base+P(11)],fill=(255,255,255,44))
    for i,b in enumerate(bars):
        prog=eib(min(1,seg(t,0.15+i*0.15,0.62+i*0.15))); col=C(b.get("color","neutral"))
        bw=P(310); bh=int(maxh*float(b["ratio"])*min(1.06,prog)); x0=xs[i]-bw//2
        if bh>P(8):
            glow_shape(img,lambda g,_x=x0,_b=bh,_c=col: rr(g,[_x,base-_b,_x+bw,base],P(18),fill=_c+(255,)),int(16*S),0.5)
            rr_gradient(img,[x0,base-bh,x0+bw,base],P(18),lighten(col,0.32),darken(col,0.72))
            # bright cap on top of the bar
            capim=Image.new("RGBA",img.size,(0,0,0,0))
            ImageDraw.Draw(capim).rounded_rectangle([x0+P(6),base-bh,x0+bw-P(6),base-bh+P(12)],P(6),fill=lighten(col,0.65)+(230,))
            img.alpha_composite(capim)
        d=ImageDraw.Draw(img)
        d.text((xs[i],base+P(64)),b["label"],font=F(POPB,52),fill=INK,anchor="mm")
        if b.get("value"):
            vb=masked_line(b["value"],F(POPB,56),seg(t,0.55+i*0.15,0.8+i*0.15),col+(255,))
            img.alpha_composite(vb,(xs[i]-vb.width//2,base-bh-P(96)))
    if ov.get("note"):
        p3=seg(t,0.66,0.92); d=ImageDraw.Draw(img)
        if p3>0.05: d.text((W//2,H-P(70)),ov["note"],font=F(POPB,46),fill=C('gold')+(int(255*p3),),anchor="mm")

def draw_schema_table(img,t,ov,C):
    d=ImageDraw.Draw(img)
    box=masked_line(ov["title"],F(POPB,80),seg(t,0.02,0.3),INK+(255,))
    img.alpha_composite(box,(W//2-box.width//2,P(70)))
    colw=P(770); gap=P(64); total=colw*2+gap; x0=(W-total)//2; top=P(252); rowh=P(128)
    # center divider draws down
    dh=int((rowh*4+P(60))*eoc(seg(t,0.12,0.4)))
    d.rectangle([W//2-P(2),top+P(40),W//2+P(2),top+P(40)+dh],fill=(255,255,255,36))
    def column(cx,head,color,items,prog0,from_left):
        hp=seg(t,prog0-0.06,prog0+0.12)
        if hp>0.02:
            sticker_chip(img,cx,top,head,color,fs=46)
        for i,it in enumerate(items):
            rp=eib(min(1,seg(t,prog0+i*0.08,prog0+i*0.08+0.32)))
            if rp<0.02: continue
            pc=min(1,rp); xoff=int((1-pc)*P(150))*(1 if from_left else -1)
            ry=top+P(102)+i*rowh; xl=cx-colw//2-xoff
            rr_gradient(img,[xl,ry-rowh//2+P(10),xl+colw,ry+rowh//2-P(2)],P(18),(23,31,45),(15,20,30))
            dd=ImageDraw.Draw(img)
            dd.ellipse([xl+P(36),ry-P(11),xl+P(58),ry+P(11)],fill=color)
            dd.text((xl+P(86),ry),it,font=F(POPM,44),fill=INK,anchor="lm")
    a=ov["colA"]; b=ov["colB"]
    column(x0+colw//2,a["head"],C(a.get("color","problem")),a["rows"],0.15,True)
    column(x0+colw+gap+colw//2,b["head"],C(b.get("color","solution")),b["rows"],0.40,False)

def draw_schema_checklist(img,t,ov,C):
    hud_kicker(img,t,ov.get("kicker","À RETENIR"),C("gold"))
    rows=ov["rows"]; y0=P(430); step=P(190)
    for i,row in enumerate(rows):
        prog=eib(min(1,seg(t,0.15+i*0.25,0.55+i*0.25)))
        if prog<0.02: continue
        pc=min(1,prog); xoff=int((1-pc)*P(150))*(1 if i%2==0 else -1)
        y=y0+i*step; mark=row.get("mark","cross" if row.get("ok") is False else "check"); col=C("problem") if mark=="cross" else C("solution")
        g_top=(36,20,20) if mark=="cross" else (18,36,28); g_bot=(22,13,13) if mark=="cross" else (11,22,17)
        xl=W//2-P(720)-xoff
        rr_gradient(img,[xl,y-P(76),xl+P(1440),y+P(76)],P(22),g_top,g_bot)
        d=ImageDraw.Draw(img)
        d.rounded_rectangle([xl,y-P(76),xl+P(1440),y+P(76)],P(22),outline=col+(90,),width=max(1,P(2)))
        xx=xl+P(70); xy=y; r=P(28); wln=P(13)
        mp=min(1,seg(t,0.22+i*0.25,0.62+i*0.25))
        def draw_mark(g,colr):
            if mark=="cross":
                a1=(xx-r,xy-r); b1=(xx+r,xy+r); a2=(xx-r,xy+r); b2=(xx+r,xy-r)
                g.line([a1,lerp(a1,b1,max(0.001,mp))],fill=colr,width=wln)
                if mp>0.0: g.line([a2,lerp(a2,b2,mp)],fill=colr,width=wln)
            else:
                p1=(xx-P(30),xy+P(2)); p2=(xx-P(6),xy+P(28)); p3=(xx+P(36),xy-P(28))
                if mp<=0.4: g.line([p1,lerp(p1,p2,max(0.001,mp/0.4))],fill=colr,width=wln)
                else: g.line([p1,p2],fill=colr,width=wln); g.line([p2,lerp(p2,p3,(mp-0.4)/0.6)],fill=colr,width=wln)
        if mp>0:
            glow_shape(img,lambda g: draw_mark(g,col+(255,)),int(12*S),0.85)
            d=ImageDraw.Draw(img); draw_mark(d,col)
            particles(img,xx,xy,col,seg(t,0.58+i*0.25,0.8+i*0.25),n=10,rad=110,seed=11+i)
        d.text((xl+P(150),y),row["text"],font=F(POPB,56),fill=INK,anchor="lm")
    if ov.get("note"):
        p=seg(t,0.66,0.92); d=ImageDraw.Draw(img)
        if p>0.05: d.text((W//2,H-P(104)),ov["note"],font=F(LATO,42),fill=MUT+(int(255*p),),anchor="mm")

EDGE={"title_band":draw_title_band,"lower_third":draw_lower_third,"keyword_pop":draw_keyword_pop}
SCHEMA={"schema_requirements":draw_schema_requirements,"schema_bignumber":draw_schema_bignumber,
        "schema_barcompare":draw_schema_barcompare,"schema_table":draw_schema_table,"schema_checklist":draw_schema_checklist}

def setup_layout(side):
    global SIDE,MARGIN,AX,COLW,COLCX,CARD_W,CARD_H,CARD_X0,CARD_Y0
    SIDE=side; MARGIN=P(70)
    CARD_W=int(W*0.42); CARD_H=int(round(CARD_W*9/16)); CARD_Y0=(H-CARD_H)//2
    COLW=int(W*0.44)
    if side=="left":
        AX=MARGIN; CARD_X0=MARGIN; COLCX=MARGIN+COLW//2
    else:
        AX=W-MARGIN; CARD_X0=W-MARGIN-CARD_W; COLCX=AX-COLW//2

def open_encoder(out):
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgba","-s",f"{W}x{H}","-framerate",str(FPS),"-i","-",
         "-c:v","prores_ks","-profile:v","4444","-pix_fmt","yuva444p10le","-q:v","9",out]
    return subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def render_overlay(ov,outdir,C):
    global W,H,S
    typ=ov["type"]; is_schema = typ in SCHEMA; fn = EDGE.get(typ) or SCHEMA.get(typ)
    if fn is None: print("  ! type inconnu:",typ); return None
    dur=float(ov["dur"]); n=int(dur*FPS)
    out=os.path.join(outdir,ov["id"]+".mov"); enc=open_encoder(out)
    try:
        for i in range(n):
            t=i/(n-1) if n>1 else 1.0
            frame=Image.new("RGBA",(W,H),(0,0,0,0))
            if is_schema:
                fullW,fullH,fullS=W,H,S
                W,H,S=CARD_W*2,CARD_H*2,(CARD_W*2)/1920.0
                stage=Image.new("RGBA",(W,H),(0,0,0,0)); schema_card(stage,t,ov,C); fn(stage,t,ov,C)
                W,H,S=fullW,fullH,fullS
                stage=stage.resize((CARD_W,CARD_H),Image.LANCZOS)
                ip=eib(min(1,seg(t,0,0.20))); op=seg(t,0.93,1.0); a=min(1,max(0,ip))*(1-op); dx=int((1-min(1,ip))*P(90))
                if a<1.0:
                    al=stage.split()[3].point(lambda p:int(p*a)); stage.putalpha(al)
                px=CARD_X0+(dx if SIDE!="left" else -dx)
                frame.alpha_composite(stage,(px,CARD_Y0))
            else:
                fn(frame,t,ov,C)
            enc.stdin.write(frame.tobytes())
    finally:
        enc.stdin.close(); rc=enc.wait()
    if rc!=0: print(f"  ! encode failed for {ov['id']} (ffmpeg rc={rc})"); return None
    print(f"  rendered {ov['id']}.mov ({n}f, {'side-card' if is_schema else 'edge'})")
    return out

def main():
    global W,H,FPS,S
    ap=argparse.ArgumentParser()
    ap.add_argument("--plan",required=True); ap.add_argument("--out",default="assets")
    ap.add_argument("--res",default=None,help="override WxH, e.g. 3840x2160 or 1920x1080")
    ap.add_argument("--side",default=None,help="right|left (default: plan.side or right)")
    ap.add_argument("--only",default=None,help="comma list of overlay ids")
    a=ap.parse_args()
    plan=json.load(open(a.plan,encoding="utf-8"))
    res = a.res or plan.get("resolution") or [1920,1080]
    if isinstance(res,str): res=[int(x) for x in res.lower().split("x")]
    W,H=int(res[0]),int(res[1]); FPS=int(plan.get("fps",30)); S=W/1920.0
    side=(a.side or plan.get("side","right")).lower()
    setup_layout(side)
    style=dict(DEFAULT_STYLE); style.update(plan.get("style",{}))
    def C(name): return hex2rgb(style.get(name,name)) if not name.startswith("#") else hex2rgb(name)
    os.makedirs(a.out,exist_ok=True)
    sc=CARD_W/1920.0; ins=int(round(18*sc)); rad=int(round(36*sc))
    json.dump({"res":[W,H],"fps":FPS,"side":side,
               "card":{"x":CARD_X0,"y":CARD_Y0,"w":CARD_W,"h":CARD_H}},
              open(os.path.join(a.out,"_layout.json"),"w"),indent=1)
    mask=Image.new("L",(CARD_W,CARD_H),0)
    ImageDraw.Draw(mask).rounded_rectangle([ins,ins,CARD_W-ins,CARD_H-ins],rad,fill=255)
    mask.save(os.path.join(a.out,"_cardmask.png"))
    only=set(a.only.split(",")) if a.only else None
    print(f"motion.py V4-HUD  {W}x{H}@{FPS}  side={side}  ->  {a.out}")
    for ov in plan["overlays"]:
        if only and ov["id"] not in only: continue
        render_overlay(ov,a.out,C)
    print("done.")

if __name__=="__main__": main()
