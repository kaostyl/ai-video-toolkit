import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {CARD_W, CARD_H, CARD_X, CARD_Y, CARD_INSET, CARD_RADIUS, withAlpha} from './theme';
import {Brackets, Shine, SPRINGS, useExit} from './primitives';

/**
 * The HUD side card that hosts every schema. Children are rendered inside a
 * nested 1920x1080 design space scaled to fit the card, so schema layouts can
 * use full-frame coordinates.
 * The frosted-glass blur of the video behind the card is applied by compose.py.
 */
export const HudCard: React.FC<{
  color: string;
  side: 'right' | 'left';
  children: React.ReactNode;
}> = ({color, side, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: SPRINGS.snappy, durationInFrames: Math.round(fps * 0.5)});
  const exit = useExit(8);
  const dx = (1 - enter) * 46 * (side === 'left' ? -1 : 1);
  const gridShift = (frame * 0.55) % 32;
  const scale = CARD_W / 1920;
  return (
    <div style={{
      position: 'absolute',
      left: CARD_X, top: CARD_Y, width: CARD_W, height: CARD_H,
      transform: `translateX(${dx}px)`,
      opacity: Math.min(enter * 1.4, 1) * exit,
    }}>
      {/* card body */}
      <div style={{
        position: 'absolute',
        inset: CARD_INSET,
        borderRadius: CARD_RADIUS,
        background: 'rgba(7,10,17,0.78)',
        border: '1px solid rgba(255,255,255,0.13)',
        boxShadow: '0 14px 34px rgba(0,0,0,0.6)',
        overflow: 'hidden',
      }}>
        {/* drifting dot grid */}
        <div style={{
          position: 'absolute', inset: -32,
          backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.055) 1.1px, transparent 1.1px)',
          backgroundSize: '32px 32px',
          transform: `translateX(${gridShift}px)`,
        }} />
        {/* gradient hairline, top */}
        <div style={{
          position: 'absolute', top: 0, left: CARD_RADIUS, height: 2.4,
          width: '58%',
          background: `linear-gradient(90deg, ${withAlpha(color, 0.85)}, transparent)`,
        }} />
        <Shine />
      </div>
      <Brackets color={color} inset={CARD_INSET - 2} delay={2} />
      {/* nested full-frame design space for schema layouts */}
      <div style={{
        position: 'absolute', left: 0, top: 0, width: 1920, height: 1080,
        transform: `scale(${scale})`, transformOrigin: 'top left',
      }}>
        {children}
      </div>
    </div>
  );
};

/** Map a fraction of the overlay duration to frames (for staggering). */
export const useT = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return frame / Math.max(1, durationInFrames - 1);
};
