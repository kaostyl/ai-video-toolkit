import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {INK, MUT, DARK, Style, resolveColor, lighten, darken, withAlpha} from './theme';
import {POPPINS, LATO, MONO, RevealLine, FadeSlide, Kicker, Particles, SPRINGS, useExit} from './primitives';

type SProps = {ov: Record<string, any>; style: Style; color: string};

/** Subtle full-frame scrim: keeps white text readable over any footage while
 *  the video (and the face) stays clearly visible. */
export const Scrim: React.FC<{strength?: number}> = ({strength = 1}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame, fps, config: SPRINGS.smooth, durationInFrames: Math.round(fps * 0.5)});
  const exit = useExit(8);
  return (
    <div style={{
      position: 'absolute', inset: 0, opacity: p * exit * strength,
      background: 'linear-gradient(180deg, rgba(4,6,10,0.62) 0%, rgba(4,6,10,0.28) 38%, rgba(4,6,10,0.18) 62%, rgba(4,6,10,0.55) 100%)',
    }} />
  );
};

const Wrap: React.FC<{children: React.ReactNode; scrim?: number}> = ({children, scrim = 1}) => {
  const exit = useExit(8);
  return (
    <>
      <Scrim strength={scrim} />
      <div style={{position: 'absolute', inset: 0, opacity: exit}}>{children}</div>
    </>
  );
};

const KickerRow: React.FC<{label: string; color: string; top?: number}> = ({label, color, top = 74}) => (
  <div style={{position: 'absolute', top, left: 0, right: 0, display: 'flex', justifyContent: 'center',
    transform: 'scale(1.6)', transformOrigin: 'top center', filter: 'drop-shadow(0 3px 10px rgba(0,0,0,0.8))'}}>
    <Kicker label={label} color={color} delay={4} />
  </div>
);

const Note: React.FC<{text?: unknown; delayFrac?: number}> = ({text, delayFrac = 0.62}) => {
  const {durationInFrames} = useVideoConfig();
  if (!text) return null;
  return (
    <FadeSlide delay={Math.round(durationInFrames * delayFrac)} dy={18}
      style={{position: 'absolute', bottom: 54, left: 0, right: 0, textAlign: 'center'}}>
      <div style={{fontFamily: LATO, fontWeight: 400, fontSize: 34, color: INK, opacity: 0.85,
        textShadow: '0 2px 14px rgba(0,0,0,0.9)'}}>{String(text)}</div>
    </FadeSlide>
  );
};

const cardBg = 'linear-gradient(180deg, rgba(18,27,20,0.93), rgba(7,10,8,0.93))';  // charter green-blacks
const floatShadow = '0 18px 44px rgba(0,0,0,0.55)';

/** A + B -> result — full-width formula. */
export const Requirements: React.FC<SProps> = ({ov, style, color}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const neu = resolveColor(style, 'neutral');
  const gold = resolveColor(style, 'gold');
  const reqs: [string, string][] = ov.reqs ?? [];
  const resStart = Math.round(durationInFrames * 0.5);
  const resP = spring({frame: frame - resStart, fps, config: SPRINGS.snappy, durationInFrames: Math.round(fps * 0.5)});
  return (
    <Wrap>
      <KickerRow label={String(ov.kicker ?? 'LE SEUIL')} color={color} />
      <div style={{position: 'absolute', top: 250, left: 0, right: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 56}}>
        {reqs.map(([big, small], i) => {
          const p = spring({frame: frame - Math.round(fps * (0.2 + i * 0.3)), fps, config: SPRINGS.bouncy, durationInFrames: Math.round(fps * 0.6)});
          return (
            <React.Fragment key={i}>
              {i > 0 && (
                <div style={{fontFamily: POPPINS, fontWeight: 700, fontSize: 110, color: INK,
                  opacity: Math.min(1, p * 1.4), transform: `scale(${0.4 + 0.6 * p})`,
                  textShadow: '0 4px 18px rgba(0,0,0,0.8)'}}>+</div>
              )}
              <div style={{
                width: 430, padding: '34px 0', textAlign: 'center', borderRadius: 24,
                background: cardBg, border: `3px solid ${neu}`, boxShadow: `${floatShadow}, 0 0 30px ${withAlpha(neu, 0.25)}`,
                opacity: Math.min(1, p * 1.4), transform: `translateY(${(1 - p) * 70}px) scale(${0.85 + 0.15 * Math.min(1, p)})`,
              }}>
                <div style={{fontFamily: MONO, fontWeight: 700, fontSize: 70, color: INK, lineHeight: 1}}>{big}</div>
                <div style={{fontFamily: LATO, fontWeight: 400, fontSize: 30, color: MUT, marginTop: 10}}>{small}</div>
              </div>
            </React.Fragment>
          );
        })}
      </div>
      <div style={{position: 'absolute', top: 570, left: 0, right: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18,
        opacity: Math.min(1, resP * 1.4), transform: `translateY(${(1 - resP) * 46}px)`}}>
        <div style={{width: 0, height: 0, borderLeft: '26px solid transparent', borderRight: '26px solid transparent', borderTop: `36px solid ${gold}`,
          filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.7))'}} />
        <div style={{
          padding: '24px 84px', borderRadius: 22, background: cardBg,
          border: `3px solid ${gold}`, boxShadow: `${floatShadow}, 0 0 34px ${withAlpha(gold, 0.35)}`,
        }}>
          <div style={{fontFamily: POPPINS, fontWeight: 700, fontSize: 52, color: gold}}>{String(ov.result ?? '')}</div>
        </div>
      </div>
      <Particles cx={960} cy={660} color={gold} start={resStart + Math.round(fps * 0.3)} n={14} radius={240} seed={7} />
      <Note text={ov.note} delayFrac={0.72} />
    </Wrap>
  );
};

/** Giant number — full screen, orbit rings + particles. */
export const BigNumber: React.FC<SProps> = ({ov, style, color}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const num = String(ov.number ?? '0');
  const isInt = /^[+-]?\d+$/.test(num);
  const cnt = interpolate(frame, [Math.round(fps * 0.2), Math.round(fps * 1.15)], [0, isInt ? parseInt(num, 10) : 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });
  const disp = isInt ? `${num.startsWith('+') ? '+' : ''}${Math.round(cnt)}` : num;
  const pop = spring({frame: frame - Math.round(fps * 0.15), fps, config: SPRINGS.bouncy, durationInFrames: Math.round(fps * 0.7)});
  const landing = Math.round(fps * 1.05);
  // number cluster sits RIGHT of the centered face
  const NX = 1360;
  const ring = (delayS: number, size: number, op: number) => {
    const rp = interpolate(frame - Math.round(fps * delayS), [0, fps * 1.1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    if (rp <= 0 || rp >= 1) return null;
    const e = 1 - (1 - rp) ** 2;
    return (
      <div style={{
        position: 'absolute', left: NX - (size * e) / 2, top: 430 - (size * e) / 2,
        width: size * e, height: size * e, borderRadius: '50%',
        border: `3px solid ${withAlpha(color, op * (1 - rp))}`,
      }} />
    );
  };
  return (
    <Wrap>
      <KickerRow label={String(ov.kicker ?? 'AUCUN SEUIL')} color={color} />
      {ring(0.95, 800, 0.8)}
      {ring(1.15, 1150, 0.5)}
      <div style={{position: 'absolute', top: 200, left: NX - 500, width: 1000, textAlign: 'center'}}>
        <div style={{
          fontFamily: MONO, fontWeight: 700, fontSize: 330, lineHeight: 1, color,
          transform: `scale(${0.5 + 0.5 * pop})`,
          textShadow: `0 0 80px ${withAlpha(color, 0.75)}, 0 0 26px ${withAlpha(color, 0.55)}, 0 8px 30px rgba(0,0,0,0.8)`,
          opacity: Math.min(1, pop * 1.5),
        }}>
          {disp}
        </div>
        <RevealLine delay={Math.round(fps * 0.5)}>
          <div style={{fontFamily: POPPINS, fontWeight: 500, fontSize: 52, color: INK, marginTop: 2,
            textShadow: '0 3px 16px rgba(0,0,0,0.85)'}}>
            {String(ov.label ?? '')}
          </div>
        </RevealLine>
      </div>
      <Particles cx={NX} cy={430} color={color} start={landing} n={16} radius={340} seed={3} />
      {ov.line ? (
        <RevealLine delay={Math.round(durationInFrames * 0.5)} style={{position: 'absolute', bottom: 150, left: 0, right: 0}}>
          <div style={{fontFamily: POPPINS, fontWeight: 700, fontSize: 58, color: INK, textAlign: 'center',
            textShadow: '0 3px 18px rgba(0,0,0,0.9)'}}>
            {String(ov.line)}
          </div>
        </RevealLine>
      ) : null}
      <Note text={ov.note} delayFrac={0.66} />
    </Wrap>
  );
};

/** Animated CHART: axis, gridlines, spring bars, counting % labels. */
export const BarCompare: React.FC<SProps> = ({ov, style}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const neu = resolveColor(style, 'neutral');
  const gold = resolveColor(style, 'gold');
  const bars: any[] = ov.bars ?? [];
  const base = 830; const maxh = 470; const chartW = 1240;
  const axis = spring({frame: frame - 4, fps, config: SPRINGS.smooth, durationInFrames: Math.round(fps * 0.5)});
  return (
    <Wrap>
      <KickerRow label={String(ov.kicker ?? 'COMPARAISON')} color={neu} />
      {/* gridlines */}
      {[0.25, 0.5, 0.75, 1].map((g, i) => (
        <div key={i} style={{
          position: 'absolute', left: 960 - (chartW / 2) * axis, width: chartW * axis, top: base - maxh * g, height: 1.6,
          background: 'rgba(255,255,255,0.14)',
          opacity: interpolate(frame, [fps * (0.2 + i * 0.06), fps * (0.4 + i * 0.06)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
        }} />
      ))}
      {/* axis */}
      <div style={{position: 'absolute', left: 960 - (chartW / 2) * axis, width: chartW * axis, top: base, height: 4,
        background: 'rgba(255,255,255,0.4)', boxShadow: '0 2px 10px rgba(0,0,0,0.7)'}} />
      {bars.map((b, i) => {
        const col = resolveColor(style, b.color);
        const p = spring({frame: frame - Math.round(durationInFrames * (0.1 + i * 0.12)), fps, config: SPRINGS.bouncy, durationInFrames: Math.round(fps * 0.85)});
        const h = Math.max(0, maxh * (b.ratio ?? 1) * p);
        const cx = 960 + (i - (bars.length - 1) / 2) * 560;
        const pct = Math.round((b.ratio ?? 1) * 100 * Math.min(1, p));
        return (
          <React.Fragment key={i}>
            <div style={{
              position: 'absolute', left: cx - 130, top: base - h, width: 260, height: h,
              borderRadius: '16px 16px 4px 4px',
              background: `linear-gradient(180deg, ${lighten(col, 0.35)}, ${col} 32%, ${darken(col, 0.7)})`,
              boxShadow: `0 0 34px ${withAlpha(col, 0.45)}, ${floatShadow}`,
            }}>
              <div style={{position: 'absolute', top: 0, left: 5, right: 5, height: 10, borderRadius: 6,
                background: lighten(col, 0.7), opacity: 0.95}} />
            </div>
            {/* counting value chip above the bar */}
            <div style={{
              position: 'absolute', left: cx - 120, width: 240, top: base - h - 92, textAlign: 'center',
              opacity: Math.min(1, p * 1.3),
            }}>
              <div style={{
                display: 'inline-block', padding: '6px 24px', borderRadius: 999,
                background: cardBg, border: `2.4px solid ${col}`,
                fontFamily: MONO, fontWeight: 700, fontSize: 40, color: col,
                boxShadow: `0 0 20px ${withAlpha(col, 0.4)}`,
              }}>
                {b.value && !/^\d+%?$/.test(String(b.value)) ? String(b.value) : `${pct}%`}
              </div>
            </div>
            <div style={{position: 'absolute', left: cx - 250, width: 500, top: base + 30, textAlign: 'center',
              fontFamily: POPPINS, fontWeight: 700, fontSize: 46, color: INK, textShadow: '0 3px 14px rgba(0,0,0,0.9)'}}>
              {String(b.label ?? '')}
            </div>
          </React.Fragment>
        );
      })}
      {ov.note ? (
        <FadeSlide delay={Math.round(durationInFrames * 0.66)} dy={18}
          style={{position: 'absolute', bottom: 46, left: 0, right: 0, textAlign: 'center'}}>
          <div style={{fontFamily: POPPINS, fontWeight: 700, fontSize: 42, color: gold, textShadow: '0 3px 14px rgba(0,0,0,0.9)'}}>
            {String(ov.note)}
          </div>
        </FadeSlide>
      ) : null}
    </Wrap>
  );
};

/** VS split: columns left & right of the speaker, sticker headers. */
export const Table: React.FC<SProps> = ({ov, style}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames: dif} = useVideoConfig();
  const colw = 640; const top = 300; const rowh = 118;
  const col = (side: 'left' | 'right', head: string, colr: string, rows: string[], startFrac: number) => {
    const isL = side === 'left';
    const x = isL ? 70 : 1920 - 70 - colw;
    const headP = spring({frame: frame - Math.round(dif * startFrac), fps, config: SPRINGS.bouncy, durationInFrames: Math.round(fps * 0.5)});
    return (
      <>
        <div style={{position: 'absolute', left: x, width: colw, top: top - 84, display: 'flex', justifyContent: 'center',
          opacity: Math.min(1, headP * 1.5), transform: `scale(${0.6 + 0.4 * headP})`}}>
          <div style={{
            background: `linear-gradient(180deg, ${lighten(colr, 0.28)}, ${darken(colr, 0.8)})`,
            border: '3.4px solid rgba(255,255,255,0.92)', borderRadius: 999, padding: '10px 44px',
            boxShadow: '6px 8px 0 rgba(0,0,0,0.55)',
            fontFamily: POPPINS, fontWeight: 700, fontSize: 44, color: DARK,
          }}>
            {head}
          </div>
        </div>
        {rows.map((r, i) => {
          const p = spring({frame: frame - Math.round(dif * (startFrac + 0.14 + i * 0.075)), fps, config: SPRINGS.snappy, durationInFrames: Math.round(fps * 0.45)});
          const xoff = (1 - p) * 170 * (isL ? -1 : 1);
          return (
            <div key={i} style={{
              position: 'absolute', left: x + xoff, width: colw, top: top + i * rowh, minHeight: rowh - 18,
              borderRadius: 16, background: cardBg, boxShadow: floatShadow,
              border: `1.6px solid ${withAlpha(colr, 0.45)}`,
              display: 'flex', alignItems: 'center', gap: 20, padding: '12px 24px',
              opacity: Math.min(1, p * 1.5),
            }}>
              <div style={{width: 18, height: 18, borderRadius: 99, background: colr, flexShrink: 0,
                boxShadow: `0 0 10px ${withAlpha(colr, 0.9)}`}} />
              <div style={{fontFamily: POPPINS, fontWeight: 500, fontSize: 33, color: INK, lineHeight: 1.22}}>{r}</div>
            </div>
          );
        })}
      </>
    );
  };
  const a = ov.colA ?? {}; const b = ov.colB ?? {};
  const vsP = spring({frame: frame - Math.round(dif * 0.36), fps, config: SPRINGS.bouncy, durationInFrames: Math.round(fps * 0.55)});
  return (
    <Wrap scrim={0.85}>
      <RevealLine delay={3} style={{position: 'absolute', top: 60, left: 0, right: 0}}>
        <div style={{fontFamily: POPPINS, fontWeight: 700, fontSize: 72, color: INK, textAlign: 'center',
          textShadow: '0 4px 20px rgba(0,0,0,0.9)'}}>
          {String(ov.title ?? '')}
        </div>
      </RevealLine>
      {/* VS badge between the header chips, above the face */}
      <div style={{position: 'absolute', left: 960 - 62, top: 172, width: 124, height: 124, borderRadius: '50%',
        background: cardBg, border: '3px solid rgba(255,255,255,0.5)', boxShadow: floatShadow,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        opacity: Math.min(1, vsP * 1.4), transform: `scale(${0.4 + 0.6 * vsP})`}}>
        <div style={{fontFamily: POPPINS, fontWeight: 700, fontSize: 48, color: INK}}>VS</div>
      </div>
      {col('left', String(a.head ?? ''), resolveColor(style, a.color ?? 'problem'), a.rows ?? [], 0.1)}
      {col('right', String(b.head ?? ''), resolveColor(style, b.color ?? 'solution'), b.rows ?? [], 0.42)}
    </Wrap>
  );
};

/** Full-width checklist rows with drawn marks + particles. */
export const Checklist: React.FC<SProps> = ({ov, style}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const gold = resolveColor(style, 'gold');
  const rows: any[] = ov.rows ?? [];
  return (
    <Wrap>
      <KickerRow label={String(ov.kicker ?? 'À RETENIR')} color={gold} />
      {rows.map((row, i) => {
        const isCross = row.mark === 'cross' || (row.mark === undefined && row.ok === false);
        const col = resolveColor(style, isCross ? 'problem' : 'solution');
        const startF = Math.round(durationInFrames * (0.12 + i * 0.3));
        const p = spring({frame: frame - startF, fps, config: SPRINGS.snappy, durationInFrames: Math.round(fps * 0.5)});
        const markP = interpolate(frame, [startF + Math.round(fps * 0.25), startF + Math.round(fps * 0.9)], [0, 1], {
          extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
        });
        const xoff = (1 - p) * 190 * (i % 2 === 0 ? -1 : 1);
        const y = 310 + i * 200;
        const markDone = startF + Math.round(fps * 0.9);
        return (
          <React.Fragment key={i}>
            <div style={{
              position: 'absolute', left: 960 - 620 + xoff, width: 1240, top: y, height: 150,
              borderRadius: 22, background: cardBg, boxShadow: `${floatShadow}, 0 0 26px ${withAlpha(col, 0.2)}`,
              border: `2.4px solid ${withAlpha(col, 0.55)}`,
              display: 'flex', alignItems: 'center', gap: 38, paddingLeft: 42,
              opacity: Math.min(1, p * 1.5),
            }}>
              <svg width={78} height={78} viewBox="0 0 72 72" style={{flexShrink: 0, filter: `drop-shadow(0 0 10px ${withAlpha(col, 0.9)})`}}>
                {isCross ? (
                  <>
                    <line x1={12} y1={12} x2={12 + 48 * Math.min(1, markP * 2)} y2={12 + 48 * Math.min(1, markP * 2)}
                      stroke={col} strokeWidth={12} strokeLinecap="round" />
                    {markP > 0.5 && (
                      <line x1={60} y1={12} x2={60 - 48 * Math.min(1, (markP - 0.5) * 2)} y2={12 + 48 * Math.min(1, (markP - 0.5) * 2)}
                        stroke={col} strokeWidth={12} strokeLinecap="round" />
                    )}
                  </>
                ) : (
                  <>
                    <line x1={10} y1={40} x2={10 + 18 * Math.min(1, markP * 2.5)} y2={40 + 18 * Math.min(1, markP * 2.5)}
                      stroke={col} strokeWidth={12} strokeLinecap="round" />
                    {markP > 0.4 && (
                      <line x1={28} y1={58} x2={28 + 34 * Math.min(1, (markP - 0.4) / 0.6)} y2={58 - 46 * Math.min(1, (markP - 0.4) / 0.6)}
                        stroke={col} strokeWidth={12} strokeLinecap="round" />
                    )}
                  </>
                )}
              </svg>
              <div style={{fontFamily: POPPINS, fontWeight: 700, fontSize: 50, color: INK,
                textShadow: '0 2px 12px rgba(0,0,0,0.7)'}}>{String(row.text ?? '')}</div>
            </div>
            <Particles cx={960 - 620 + 82} cy={y + 75} color={col} start={markDone} n={11} radius={130} seed={11 + i} />
          </React.Fragment>
        );
      })}
      <Note text={ov.note} delayFrac={0.7} />
    </Wrap>
  );
};

/** RANKING — gorgeous animated leaderboard (new type "schema_ranking").
 *  {"type":"schema_ranking","kicker":"LE CLASSEMENT","items":[
 *    {"label":"Affiliation","value":"élevé","ratio":1.0,"color":"solution"},
 *    {"label":"AdSense","value":"faible","ratio":0.3,"color":"problem"}]}   */
export const Ranking: React.FC<SProps> = ({ov, style, color}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const items: any[] = (ov.items ?? []).slice(0, 5);
  const rowh = items.length > 3 ? 150 : 180; // value col widened for mono
  const top = items.length > 3 ? 260 : 300;
  const medals = ['#FFD75E', '#C9D4E4', '#E4A15E', '#7B8798', '#7B8798'];
  return (
    <Wrap>
      <KickerRow label={String(ov.kicker ?? 'CLASSEMENT')} color={color} />
      {items.map((it, i) => {
        const col = resolveColor(style, it.color ?? (i === 0 ? 'solution' : 'neutral'));
        const startF = Math.round(durationInFrames * (0.1 + i * 0.16));
        const p = spring({frame: frame - startF, fps, config: SPRINGS.snappy, durationInFrames: Math.round(fps * 0.5)});
        const barP = spring({frame: frame - startF - Math.round(fps * 0.2), fps, config: SPRINGS.smooth, durationInFrames: Math.round(fps * 0.8)});
        const y = top + i * rowh;
        const barW = 900 * (it.ratio ?? 0.5) * barP;
        const medal = medals[i] ?? medals[4];
        return (
          <div key={i} style={{
            position: 'absolute', left: 240 + (1 - p) * 220, top: y, width: 1440, height: rowh - 26,
            borderRadius: 20, background: cardBg, boxShadow: floatShadow,
            border: `1.8px solid ${i === 0 ? withAlpha(medal, 0.8) : 'rgba(255,255,255,0.14)'}`,
            display: 'flex', alignItems: 'center', gap: 30, padding: '0 38px',
            opacity: Math.min(1, p * 1.5),
          }}>
            {/* medal / rank badge */}
            <div style={{
              width: 74, height: 74, borderRadius: '50%', flexShrink: 0,
              background: `linear-gradient(180deg, ${lighten(medal, 0.3)}, ${darken(medal, 0.75)})`,
              border: '3px solid rgba(255,255,255,0.85)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: i === 0 ? `0 0 26px ${withAlpha(medal, 0.7)}` : '0 4px 12px rgba(0,0,0,0.5)',
              fontFamily: MONO, fontWeight: 700, fontSize: 36, color: DARK,
            }}>
              {i + 1}
            </div>
            <div style={{width: 380, fontFamily: POPPINS, fontWeight: 700, fontSize: 44, color: INK}}>
              {String(it.label ?? '')}
            </div>
            {/* animated bar */}
            <div style={{flex: 1, height: 34, borderRadius: 999, background: 'rgba(255,255,255,0.08)', overflow: 'hidden'}}>
              <div style={{
                width: barW, maxWidth: '100%', height: '100%', borderRadius: 999,
                background: `linear-gradient(90deg, ${darken(col, 0.75)}, ${col}, ${lighten(col, 0.4)})`,
                boxShadow: `0 0 18px ${withAlpha(col, 0.6)}`,
              }} />
            </div>
            {it.value ? (
              <div style={{width: 250, textAlign: 'right', whiteSpace: 'nowrap', fontFamily: MONO, fontWeight: 700, fontSize: 30, color: col,
                opacity: Math.min(1, barP * 1.4)}}>
                {String(it.value)}
              </div>
            ) : null}
          </div>
        );
      })}
      <Note text={ov.note} delayFrac={0.7} />
    </Wrap>
  );
};
