import React from 'react';
import {AbsoluteFill, useVideoConfig} from 'remotion';
import {DESIGN_W, DESIGN_H, Style, OverlayData, resolveColor, CARD_INSET, CARD_RADIUS} from './design/theme';
import {TitleBand, LowerThird, KeywordPop} from './design/edge';
import {Requirements, BigNumber, BarCompare, Table, Checklist, Ranking} from './design/schemas';

export type OverlayProps = {
  overlay: OverlayData;
  style: Style;
  side: 'right' | 'left';
  width: number;
  height: number;
  fps: number;
};

const EDGE: Record<string, React.FC<any>> = {
  title_band: TitleBand,
  lower_third: LowerThird,
  keyword_pop: KeywordPop,
};

const SCHEMA: Record<string, React.FC<any>> = {
  schema_requirements: Requirements,
  schema_bignumber: BigNumber,
  schema_barcompare: BarCompare,
  schema_table: Table,
  schema_checklist: Checklist,
  schema_ranking: Ranking,
};

/** Renders ONE overlay on a transparent canvas, in 1920x1080 design space
 *  scaled to the output resolution. */
export const OverlayComp: React.FC<OverlayProps> = ({overlay, style, side}) => {
  const {width} = useVideoConfig();
  const scale = width / DESIGN_W;
  const color = resolveColor(style, overlay.color);
  const Edge = EDGE[overlay.type];
  const Schema = SCHEMA[overlay.type];
  return (
    <AbsoluteFill style={{backgroundColor: 'transparent'}}>
      <div style={{width: DESIGN_W, height: DESIGN_H, transform: `scale(${scale})`, transformOrigin: 'top left', position: 'absolute'}}>
        {Edge ? <Edge ov={overlay} color={color} side={side} /> : null}
        {/* schemas are now FULL-SCREEN transparent motion graphics (no card) */}
        {Schema ? <Schema ov={overlay} style={style} color={color} /> : null}
      </div>
    </AbsoluteFill>
  );
};

/** White rounded-rect on black: the frosted-glass mask used by compose.py. */
export const CardMask: React.FC = () => {
  const {width} = useVideoConfig();
  const scale = width / 806; // mask comp is rendered at the card's pixel size
  return (
    <AbsoluteFill style={{backgroundColor: 'black'}}>
      <div style={{
        position: 'absolute',
        left: CARD_INSET * scale, top: CARD_INSET * scale,
        right: CARD_INSET * scale, bottom: CARD_INSET * scale,
        borderRadius: CARD_RADIUS * scale,
        background: 'white',
      }} />
    </AbsoluteFill>
  );
};
