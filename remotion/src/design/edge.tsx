import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {DESIGN_W, DESIGN_H, INK, MUT, lighten, withAlpha} from './theme';
import {POPPINS, LATO, MONO, RevealLine, FadeSlide, Particles, SPRINGS, useExit} from './primitives';

type Props = {ov: Record<string, any>; color: string; side: 'right' | 'left'};

// ---------------------------------------------------------------------------
// v6 "Particle" system â€” FULLSCREEN, face-safe.
// The speaker is centred, so all heavy content lives in the top & bottom
// thirds; only soft, semi-transparent particle dust ever drifts over the
// centre. No more right-anchored pills / lower-thirds.
// ---------------------------------------------------------------------------

/** Drifting glow-dust across the WHOLE frame â€” the ambient "futuristic
 *  particles" layer. Deterministic (no Math.random) so renders are stable. */
export const AmbientField: React.FC<{color: string; n?: number; seed?: number}> = ({color, n = 48, seed = 1}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const appear = spring({frame, fps, config: SPRINGS.smooth, durationInFrames: Math.round(fps * 0.7)});
  const exit = useExit(10);
  const life = frame / fps;
  return (
    <div style={{position: 'absolute', inset: 0, opacity: appear * exit, pointerEvents: 'none'}}>
      {Array.from({length: n}, (_, k) => {
        const x = (k * 97.13 + seed * 23.7) % 100;                 // vw%
        const baseY = (k * 57.31 + seed * 41.3) % 100;             // vh%
        const rise = (frame / durationInFrames) * (14 + (k % 6) * 5); // slow upward drift
        const sway = 1.1 * Math.sin(life * (0.5 + (k % 7) * 0.2) + k);
        const y = (((baseY - rise) % 100) + 100) % 100;
        const size = 1.5 + (k % 4);
        const tw = 0.5 + 0.5 * Math.sin(life * (1.1 + (k % 5) * 0.35) + k * 1.7);
        return (
          <div key={k} style={{
            position: 'absolute', left: `calc(${x}% + ${sway}px)`, top: `${y}%`,
            width: size, height: size, borderRadius: size,
            background: k % 5 === 0 ? color : INK,
            opacity: 0.08 + 0.22 * tw,
            boxShadow: `0 0 ${4 + size * 2}px ${withAlpha(color, 0.55)}`,
          }} />
        );
      })}
    </div>
  );
};

/** Centred energy rule that draws out from the middle â€” relative (in-flow). */
const Rule: React.FC<{color: string; delay?: number; maxW?: number}> = ({color, delay = 0, maxW = 520}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - delay, fps, config: SPRINGS.smooth, durationInFrames: Math.round(fps * 0.5)});
  return (
    <div style={{width: maxW * p, height: 4, borderRadius: 3, margin: '0 auto',
      background: `linear-gradient(90deg, transparent, ${color} 18%, ${lighten(color, 0.5)} 50%, ${color} 82%, transparent)`,
      boxShadow: `0 0 16px ${withAlpha(color, 0.9)}`}} />
  );
};

/** Soft gradient rising from the bottom â€” guarantees text readability in the
 *  face-safe lower band without a hard box. */
const BottomScrim: React.FC<{h?: number}> = ({h = 460}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame, fps, config: SPRINGS.smooth, durationInFrames: Math.round(fps * 0.5)});
  const exit = useExit(8);
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: h, opacity: p * exit,
      background: 'linear-gradient(180deg, rgba(4,6,8,0) 0%, rgba(4,6,8,0.15) 34%, rgba(4,6,8,0.55) 70%, rgba(4,6,8,0.85) 100%)'}} />
  );
};

/** Big kinetic title, CENTRED in the lower third, full-frame ambient. */
export const TitleBand: React.FC<Props> = ({ov, color}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const exit = useExit();
  const kick = spring({frame: frame - 2, fps, config: SPRINGS.smooth, durationInFrames: Math.round(fps * 0.5)});
  return (
    <div style={{position: 'absolute', inset: 0, opacity: exit}}>
      <AmbientField color={color} seed={3} />
      <BottomScrim />
      {/* top-centre kicker tag frames the shot without covering the face */}
      {ov.small ? (
        <div style={{position: 'absolute', top: 88, left: 0, right: 0, display: 'flex', justifyContent: 'center',
          alignItems: 'center', gap: 14, opacity: kick, transform: `translateY(${(1 - kick) * -14}px)`}}>
          <div style={{width: 12, height: 12, borderRadius: 3, background: color, boxShadow: `0 0 12px ${color}`}} />
          <div style={{fontFamily: MONO, fontWeight: 700, fontSize: 26, letterSpacing: '0.18em', color: INK,
            textShadow: '0 2px 14px rgba(0,0,0,0.85)'}}>{String(ov.small).toUpperCase()}</div>
        </div>
      ) : null}
      {/* main title â€” anchored in the face-safe BOTTOM band, grows upward */}
      <div style={{position: 'absolute', left: 120, right: 120, bottom: 108, textAlign: 'center',
        textShadow: '0 4px 26px rgba(0,0,0,0.9)'}}>
        <div style={{marginBottom: 22}}><Rule color={color} delay={2} maxW={520} /></div>
        <RevealLine delay={4} style={{overflow: 'visible'}}>
          <div style={{fontFamily: POPPINS, fontWeight: 700, fontSize: 88, lineHeight: 1.08, color: INK}}>
            {String(ov.big)}
          </div>
        </RevealLine>
      </div>
      <Particles cx={DESIGN_W / 2} cy={DESIGN_H - 250} color={color} start={Math.round(fps * 0.25)} n={18} radius={300} seed={5} />
    </div>
  );
};

/** Full-width broadcast chyron at the BOTTOM â€” avatar + title + sub. */
export const LowerThird: React.FC<Props> = ({ov, color}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const exit = useExit();
  const enter = spring({frame, fps, config: SPRINGS.snappy, durationInFrames: Math.round(fps * 0.55)});
  const dy = (1 - enter) * 120;
  const pulse = 1 + 0.28 * Math.sin(Math.min(1, frame / (fps * 0.55)) * Math.PI);
  const BAR_H = 168;
  return (
    <div style={{position: 'absolute', inset: 0, opacity: exit}}>
      <AmbientField color={color} n={40} seed={7} />
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 70, height: BAR_H,
        transform: `translateY(${dy}px)`, opacity: Math.min(1, enter * 1.5)}}>
        {/* full-width glass bar */}
        <div style={{position: 'absolute', inset: 0,
          background: 'linear-gradient(180deg, rgba(10,16,12,0.0) 0%, rgba(9,14,11,0.82) 22%, rgba(7,11,9,0.9) 100%)'}} />
        {/* animated top accent line spanning the whole width */}
        <div style={{position: 'absolute', top: 0, left: DESIGN_W / 2 - (DESIGN_W / 2) * enter, width: DESIGN_W * enter, height: 4,
          background: `linear-gradient(90deg, transparent, ${color} 20%, ${lighten(color, 0.5)} 50%, ${color} 80%, transparent)`,
          boxShadow: `0 0 18px ${withAlpha(color, 0.9)}`}} />
        {/* content, left-aligned in a safe inset */}
        <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', gap: 30, padding: '0 130px'}}>
          <div style={{position: 'relative', flexShrink: 0}}>
            <div style={{width: 96, height: 96, borderRadius: 999,
              border: `3px solid ${color}`, boxShadow: `0 0 18px ${withAlpha(color, 0.75)}`, background: `linear-gradient(135deg, ${color}, #172026)`}} />
            <div style={{position: 'absolute', right: 0, bottom: 0, width: 18 * pulse, height: 18 * pulse,
              borderRadius: 99, background: color, border: '3px solid rgba(7,10,8,0.95)'}} />
          </div>
          <div>
            <RevealLine delay={3}>
              <div style={{fontFamily: POPPINS, fontWeight: 700, fontSize: 52, color: INK, lineHeight: 1.12,
                textShadow: '0 2px 14px rgba(0,0,0,0.7)'}}>{String(ov.title)}</div>
            </RevealLine>
            {ov.sub ? (
              <FadeSlide delay={Math.round(fps * 0.32)} dy={18}>
                <div style={{fontFamily: LATO, fontWeight: 400, fontSize: 30, color: MUT, marginTop: 6}}>
                  {String(ov.sub)}
                </div>
              </FadeSlide>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
};

/** Big keyword STAMP, centred in the lower third â€” scales in with a burst. */
export const KeywordPop: React.FC<Props> = ({ov, color}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const exit = useExit();
  const enter = spring({frame, fps, config: SPRINGS.bouncy, durationInFrames: Math.round(fps * 0.55)});
  const scale = 0.62 + 0.38 * enter;
  const rot = (1 - enter) * -3;
  const glow = interpolate(enter, [0, 1], [0.3, 0.85]);
  return (
    <div style={{position: 'absolute', inset: 0, opacity: exit}}>
      <AmbientField color={color} seed={9} />
      <BottomScrim />
      {/* keyword stamp â€” face-safe BOTTOM band, grows upward */}
      <div style={{position: 'absolute', left: 140, right: 140, bottom: 120, textAlign: 'center',
        transform: `scale(${scale}) rotate(${rot}deg)`, transformOrigin: 'center bottom',
        opacity: Math.min(1, enter * 1.6)}}>
        <div style={{marginBottom: 18}}><Rule color={color} delay={1} maxW={640} /></div>
        <div style={{
          fontFamily: POPPINS, fontWeight: 700, fontSize: 74, lineHeight: 1.14, color: INK,
          textShadow: `0 0 34px ${withAlpha(color, glow)}, 0 4px 24px rgba(0,0,0,0.9)`,
          whiteSpace: 'pre-wrap',
        }}>
          {String(ov.text)}
        </div>
        <div style={{margin: '18px auto 0', width: 180, height: 5, borderRadius: 3,
          background: `linear-gradient(90deg, transparent, ${color}, transparent)`,
          boxShadow: `0 0 14px ${color}`}} />
      </div>
      <Particles cx={DESIGN_W / 2} cy={DESIGN_H - 230} color={color} start={Math.round(fps * 0.15)} n={20} radius={320} seed={13} />
    </div>
  );
};
