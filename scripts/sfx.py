#!/usr/bin/env python3
"""
sfx.py — Futuristic *particle* SFX pack, 48kHz stereo WAVs.

Video Toolkit v6 aesthetic: airy, granular, crystalline — think sci-fi light
particles and soft energy, NOT arcade lasers or 8-bit blips. Everything is
gentle and high-air; compose.py mixes them low (~0.12) under the voice.

The 12 names are kept identical to the previous pack (whoosh/pop/tick/riser/
ding/blip/zap/charge/scan/glitch/impact/shimmer) so existing plans and
validate_plan.py's SFX_KNOWN keep working — only the *sound design* changed.

Usage: python sfx.py --out sfx
Only dependency: numpy (std-lib wave for writing).
"""
import os, wave, argparse, numpy as np
SR=48000
np.random.seed(42)   # reproducible builds: same sounds on every regeneration

def _wav(path,sig):
    sig=np.clip(sig,-1,1)
    if sig.ndim==1: sig=np.stack([sig,sig],axis=1)
    data=(sig*32767).astype("<i2").tobytes()
    w=wave.open(path,"wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data); w.close()

def env(n,att=0.01,rel=0.2):
    a=int(SR*att); r=int(SR*rel); e=np.ones(n)
    if a>0: e[:a]=np.linspace(0,1,a)
    if r>0: e[-r:]=np.linspace(1,0,r)
    return e

def _norm(sig,peak=0.9):
    return sig/(np.max(np.abs(sig))+1e-9)*peak

def _smooth(sig,win):
    k=np.hanning(win)/max(1e-9,np.hanning(win).sum())
    return np.convolve(sig,k,mode="same")

def _air(sig,tail=0.28,wet=0.32,seed=0):
    """Soft diffuse tail — sprinkles a decaying-noise reverb so hits bloom
    into 'air' instead of stopping dead. Keeps the particle feel."""
    rng=np.random.RandomState(seed)
    n=len(sig); L=int(SR*tail)
    ir=rng.randn(L)*np.exp(-np.linspace(0,7,L))
    w=np.convolve(sig,ir,mode="full")[:n]
    return sig*(1-wet)+_norm(w,1.0)*wet

def _grains(n,count,fmin=1900,fmax=6500,decay=42,spread=1.0,seed=0,glen=0.11):
    """Cloud of tiny detuned sine 'particles' — the core of the palette.
    Each grain is a short high sine with fast exp decay, scattered in time."""
    rng=np.random.RandomState(seed)
    out=np.zeros(n)
    maxlen=int(SR*glen)
    for _ in range(count):
        start=int(rng.rand()*max(1,n*spread))
        if start>=n: continue
        f=rng.uniform(fmin,fmax)
        L=min(n-start,maxlen)
        if L<=1: continue
        tt=np.linspace(0,L/SR,L)
        g=np.sin(2*np.pi*f*tt)*np.exp(-tt*decay*rng.uniform(0.7,1.4))
        out[start:start+L]+=g*rng.uniform(0.25,1.0)
    return out

def _stereo_spread(mono_l,mono_r):
    return np.stack([mono_l,mono_r],axis=1)

# ---------------- futuristic particle palette ----------------

def whoosh(dur=0.6):
    """Airy particle sweep — soft filtered-noise pass, no tonal laser."""
    n=int(SR*dur); t=np.linspace(0,dur,n)
    noise=_smooth(np.random.randn(n),520)
    swell=np.sin(np.pi*t/dur)**1.6
    grains=_grains(n,26,2200,7000,decay=30,seed=1)*0.35
    sig=(noise*swell*0.8+grains*swell)
    sig=_air(sig,0.30,0.30,seed=1)
    return _norm(sig,0.82)*env(n,0.02,0.18)

def pop(dur=0.18):
    """Soft sparkle pop — rounded low click + a little grain shimmer."""
    n=int(SR*dur); t=np.linspace(0,dur,n)
    body=np.sin(2*np.pi*np.cumsum(np.linspace(520,240,n))/SR)*np.exp(-t*24)
    grains=_grains(n,8,2600,6000,decay=55,spread=0.5,seed=2)*0.5
    sig=body*0.7+grains
    sig=_air(sig,0.16,0.25,seed=2)
    return _norm(sig,0.85)*env(n,0.001,0.05)

def tick(dur=0.06):
    """Tiny high sparkle tick — soft, glassy, for table rows / counters."""
    n=int(SR*dur); t=np.linspace(0,dur,n)
    sig=(np.sin(2*np.pi*3200*t)+0.4*np.sin(2*np.pi*4800*t))*np.exp(-t*90)
    return _norm(sig,0.75)*env(n,0.0005,0.02)

def riser(dur=1.1):
    """Airy sparkle riser — noise swell + more and faster particles as it climbs."""
    n=int(SR*dur); t=np.linspace(0,dur,n)
    noise=_smooth(np.random.randn(n),420)*((t/dur)**2)*0.5
    grains=_grains(n,40,1400,7000,decay=26,seed=3)
    # weight grains toward the end so density rises
    grains*=np.interp(np.arange(n),[0,n],[0.2,1.0])
    sig=noise+grains*0.5
    sig=_air(sig,0.35,0.3,seed=3)
    return _norm(sig,0.8)*env(n,0.03,0.15)

def ding(dur=0.7):
    """Soft glassy chime — rounded partials, gentle, for confirmations."""
    n=int(SR*dur); t=np.linspace(0,dur,n)
    sig=np.zeros(n)
    for f,a in [(1320,1.0),(1980,0.45),(2640,0.22)]:
        sig+=np.sin(2*np.pi*f*t)*a
    sig*=np.exp(-t*6)
    sig+=_grains(n,10,3000,6500,decay=30,spread=0.3,seed=4)*0.25
    sig=_air(sig,0.30,0.28,seed=4)
    return _norm(sig,0.8)*env(n,0.003,0.22)

def blip(dur=0.12):
    """Soft rounded UI pulse — sine confirm + micro sparkle, no harsh harmonics."""
    n=int(SR*dur); t=np.linspace(0,dur,n)
    f=np.where(t<dur*0.4,1500.0,1900.0)
    body=np.sin(2*np.pi*np.cumsum(f)/SR)*(np.exp(-t*22)+0.2)
    grains=_grains(n,5,3200,6000,decay=60,spread=0.4,seed=5)*0.35
    sig=body*0.8+grains
    sig=_air(sig,0.14,0.22,seed=5)
    return _norm(sig,0.82)*env(n,0.001,0.03)

def zap(dur=0.34):
    """Gentle downward sparkle cascade — replaces the old laser 'zap'.
    Particles falling in pitch; used for negatives/warnings, but still soft."""
    n=int(SR*dur); t=np.linspace(0,dur,n)
    rng=np.random.RandomState(6)
    out=np.zeros(n)
    steps=9
    for i in range(steps):
        start=int(i/steps*n*0.7)
        f=3200*(0.72**i)+140
        L=min(n-start,int(SR*0.13))
        if L<=1: continue
        tt=np.linspace(0,L/SR,L)
        g=np.sin(2*np.pi*f*tt)*np.exp(-tt*30)
        out[start:start+L]+=g*(0.9-i*0.06)
    out+=_grains(n,14,1600,5000,decay=28,seed=6)*0.3
    sig=_air(out,0.24,0.3,seed=6)
    return _norm(sig,0.82)*env(n,0.002,0.08)

def charge(dur=0.62):
    """Particle-gathering riser — soft airy swell with grains converging.
    The signature 'entrance' sound for titles/schemas."""
    n=int(SR*dur); t=np.linspace(0,dur,n)
    # airy body sweeping gently up
    f=520+900*(t/dur)**1.4
    body=(np.sin(2*np.pi*np.cumsum(f)/SR)+0.4*np.sin(2*np.pi*np.cumsum(f*1.5)/SR))
    body*=0.28*(t/dur)**1.2
    noise=_smooth(np.random.randn(n),360)*((t/dur)**1.5)*0.35
    grains=_grains(n,34,1800,7000,decay=24,seed=7)
    grains*=np.interp(np.arange(n),[0,n],[0.15,1.0])
    sig=body+noise+grains*0.5
    sig=_air(sig,0.32,0.32,seed=7)
    return _norm(sig,0.8)*env(n,0.02,0.14)

def scan(dur=0.42):
    """Light ascending sparkle arpeggio — soft, for cascades/counters."""
    n=int(SR*dur); t=np.linspace(0,dur,n)
    out=np.zeros(n)
    steps=7
    for i in range(steps):
        start=int(i/steps*n)
        f=1400*(2**(i*2.0/12.0))
        L=min(n-start,int(SR*0.12))
        if L<=1: continue
        tt=np.linspace(0,L/SR,L)
        out[start:start+L]+=np.sin(2*np.pi*f*tt)*np.exp(-tt*34)*0.9
    sig=_air(out,0.22,0.28,seed=8)
    return _norm(sig,0.78)*env(n,0.002,0.08)

def glitch(dur=0.26):
    """Airy granular dust — soft particle texture for broll/transitions.
    (No digital bit-crush; this is 'sparkle dust', not a stutter.)"""
    n=int(SR*dur)
    grains=_grains(n,44,2200,8000,decay=40,seed=9)
    grains+=_smooth(np.random.randn(n),40)*np.exp(-np.linspace(0,dur,n)*10)*0.25
    sig=_air(grains,0.20,0.3,seed=9)
    return _norm(sig,0.78)*env(n,0.003,0.06)

def impact(dur=0.5):
    """Soft bloom — gentle sub swell + a scattering particle burst tail.
    For big landings (numbers), but rounded, never a hard thud."""
    n=int(SR*dur); t=np.linspace(0,dur,n)
    f=90*np.exp(-t*7)+40
    sub=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*6)*0.9
    burst=_grains(n,40,1500,7000,decay=20,spread=0.35,seed=10)
    burst*=np.interp(np.arange(n),[0,int(n*0.1),n],[0.2,1.0,0.0])
    sig=sub+burst*0.55
    sig=_air(sig,0.34,0.3,seed=10)
    return _norm(sig,0.88)*env(n,0.001,0.16)

def shimmer(dur=0.85):
    """Crystalline sparkle cloud — dense detuned particles twinkling.
    Positive confirmations (checks, #1, reveals)."""
    n=int(SR*dur); t=np.linspace(0,dur,n)
    base=np.zeros(n)
    for det in [1.0,1.005,0.995,1.5,2.01,2.5]:
        base+=np.sin(2*np.pi*1800*det*t)*(0.5)
    trem=1+0.25*np.sin(2*np.pi*7*t)
    base*=trem*np.exp(-t*4.6)*0.4
    grains=_grains(n,50,2400,8500,decay=18,seed=11)
    sig=base+grains*0.5
    sig=_air(sig,0.38,0.34,seed=11)
    return _norm(sig,0.82)*env(n,0.004,0.26)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default="sfx"); a=ap.parse_args()
    os.makedirs(a.out,exist_ok=True)
    for name,fn in [("whoosh",whoosh),("pop",pop),("tick",tick),("riser",riser),("ding",ding),
                    ("blip",blip),("zap",zap),("charge",charge),("scan",scan),
                    ("glitch",glitch),("impact",impact),("shimmer",shimmer)]:
        _wav(os.path.join(a.out,name+".wav"),fn()); print("  ",name+".wav")
    print("SFX (particules futuristes) -> ",a.out)
if __name__=="__main__": main()
