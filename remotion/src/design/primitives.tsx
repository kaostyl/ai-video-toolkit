import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont as loadGrotesk} from '@remotion/google-fonts/SpaceGrotesk';
import {loadFont as loadMono} from '@remotion/google-fonts/JetBrainsMono';
import {INK, withAlpha, lighten, darken} from './theme';

// Video Toolkit charter: Space Grotesk for display/body, JetBrains Mono for HUD labels/values
const grotesk = loadGrotesk('normal', {weights: ['500', '700'], subsets: ['latin']});
const mono = loadMono('normal', {weights: ['500', '700'], subsets: ['latin']});
export const POPPINS = grotesk.fontFamily;   // display (kept name to avoid churn)
export const LATO = grotesk.fontFamily;      // body
export const MONO = mono.fontFamily;         // kickers, numbers, values

export const SPRINGS = {
  snappy: {damping: 20, stiffness: 200},
  bouncy: {damping: 11, stiffness: 140},
  smooth: {damping: 200},
} as const;

/** Kinetic-typography primitive: text slides up from behind an invisible edge. */
export const RevealLine: React.FC<{
  children: React.ReactNode;
  delay?: number;               // frames
  style?: React.CSSProperties;
  bounce?: boolean;
}> = ({children, delay = 0, style, bounce = true}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({
    frame: frame - delay,
    fps,
    config: bounce ? SPRINGS.snappy : SPRINGS.smooth,
    durationInFrames: Math.round(fps * 0.55),
  });
  return (
    <div style={{overflow: 'hidden', ...style}}>
      <div style={{transform: `translateY(${(1 - p) * 110}%)`}}>{children}</div>
    </div>
  );
};

/** Fade + slide, for secondary text. */
export const FadeSlide: React.FC<{
  children: React.ReactNode;
  delay?: number;
  dy?: number;
  style?: React.CSSProperties;
}> = ({children, delay = 0, dy = 26, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - delay, fps, config: SPRINGS.smooth, durationInFrames: Math.round(fps * 0.6)});
  return (
    <div style={{opacity: p, transform: `translateY(${(1 - p) * dy}px)`, ...style}}>
      {children}
    </div>
  );
};

/** Whole-overlay exit fade during the last `frames`. */
export const useExit = (frames = 9): number => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return interpolate(frame, [durationInFrames - frames, durationInFrames - 1], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
};

/** Small-caps, letter-spaced editorial label with accent square + rule. */
export const Kicker: React.FC<{label: string; color: string; delay?: number}> = ({label, color, delay = 0}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - delay, fps, config: SPRINGS.smooth, durationInFrames: Math.round(fps * 0.45)});
  const rule = interpolate(p, [0, 1], [0, 120]);
  return (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 7, opacity: p}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 12, transform: `translateX(${(1 - p) * 18}px)`}}>
        <div style={{width: 10, height: 10, borderRadius: 3, background: color}} />
        <div style={{fontFamily: MONO, fontWeight: 700, fontSize: 16, letterSpacing: '0.14em', color: INK}}>
          {label.toUpperCase()}
        </div>
      </div>
      <div style={{width: rule, height: 1.6, background: 'rgba(255,255,255,0.16)'}} />
    </div>
  );
};

/** Deterministic particle burst (no Math.random — stable across renders). */
export const Particles: React.FC<{
  cx: number; cy: number; color: string;
  start: number;                 // frame at which the burst begins
  n?: number; radius?: number; seed?: number;
}> = ({cx, cy, color, start, n = 12, radius = 90, seed = 1}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const life = Math.round(fps * 0.55);
  const t = (frame - start) / life;
  if (t <= 0 || t >= 1) return null;
  const e = 1 - (1 - t) ** 3;
  return (
    <>
      {Array.from({length: n}, (_, k) => {
        const jitter = Math.sin(seed * 7.31 + k * 12.9);
        const a = (2 * Math.PI * k) / n + jitter * 0.55;
        const r = radius * e * (0.65 + 0.35 * ((k * 37 % 10) / 10));
        const s = Math.max(1.5, 4.5 * (1 - t));
        return (
          <div key={k} style={{
            position: 'absolute',
            left: cx + Math.cos(a) * r - s,
            top: cy + Math.sin(a) * r * 0.8 - s,
            width: s * 2, height: s * 2, borderRadius: s,
            background: color, opacity: 1 - t,
          }} />
        );
      })}
    </>
  );
};

/** Gradient pill with white keyline + hard offset shadow ("sticker"). */
export const Sticker: React.FC<{
  color: string;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({color, children, style}) => (
  <div style={{
    background: `linear-gradient(180deg, ${lighten(color, 0.3)} 0%, ${color} 45%, ${darken(color, 0.78)} 100%)`,
    border: '2.6px solid rgba(255,255,255,0.95)',
    boxShadow: '7px 8px 0 rgba(0,0,0,0.65)',
    borderRadius: 999,
    padding: '14px 30px',
    ...style,
  }}>
    {children}
  </div>
);

/** Animated HUD corner brackets. */
export const Brackets: React.FC<{color: string; inset?: number; delay?: number}> = ({color, inset = 8, delay = 0}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - delay, fps, config: SPRINGS.smooth, durationInFrames: Math.round(fps * 0.4)});
  const len = 30 * p;
  const th = 3;
  const glow = `drop-shadow(0 0 6px ${withAlpha(color, 0.8)})`;
  const corner = (pos: React.CSSProperties, dirX: 1 | -1, dirY: 1 | -1) => (
    <div style={{position: 'absolute', filter: glow, ...pos}}>
      {/* horizontal arm hugs the frame edge: top edge for top corners, bottom for bottom */}
      <div style={{position: 'absolute', width: len, height: th, background: color, ...(dirX === -1 ? {right: 0} : {left: 0}), ...(dirY === -1 ? {bottom: 0} : {top: 0})}} />
      <div style={{position: 'absolute', width: th, height: len, background: color, ...(dirX === -1 ? {right: 0} : {left: 0}), ...(dirY === -1 ? {bottom: 0} : {top: 0})}} />
    </div>
  );
  return (
    <>
      {corner({left: inset, top: inset, width: len, height: len}, 1, 1)}
      {corner({right: inset, top: inset, width: len, height: len}, -1, 1)}
      {corner({left: inset, bottom: inset, width: len, height: len}, 1, -1)}
      {corner({right: inset, bottom: inset, width: len, height: len}, -1, -1)}
    </>
  );
};

/** Diagonal shine sweeping across a container during the entrance. */
export const Shine: React.FC<{delay?: number}> = ({delay = 0}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = interpolate(frame - delay, [0, fps * 0.9], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  if (p >= 1) return null;
  const x = interpolate(1 - (1 - p) ** 3, [0, 1], [-45, 145]);
  return (
    <div style={{
      position: 'absolute', inset: 0, overflow: 'hidden', borderRadius: 'inherit', pointerEvents: 'none',
    }}>
      <div style={{
        position: 'absolute', top: '-30%', bottom: '-30%',
        left: `${x}%`, width: '22%',
        transform: 'rotate(14deg)',
        background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.16), transparent)',
      }} />
    </div>
  );
};
