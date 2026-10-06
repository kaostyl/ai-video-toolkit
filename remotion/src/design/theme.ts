// Design tokens for the Video Toolkit "Premium Broadcast HUD" system.
// All layout is designed in a 1920x1080 reference space and scaled at render.

export const DESIGN_W = 1920;
export const DESIGN_H = 1080;

// Video Toolkit brand charter: neon green on green-tinted blacks, JetBrains Mono accents
export const INK = '#EAF4EC';
export const MUT = '#9FBCA8';
export const DARK = '#070A08';
export const BRAND = '#3BFF6E';

export const DEFAULT_STYLE: Record<string, string> = {
  problem: '#FF4545',
  solution: '#3BFF6E',   // brand neon green
  neutral: '#7FA98B',    // charter sage
  gold: '#FBBF24',
};

export type Style = Record<string, string>;

export const resolveColor = (style: Style, name?: string): string => {
  if (!name) return DEFAULT_STYLE.neutral;
  if (name.startsWith('#')) return name;
  return style[name] ?? DEFAULT_STYLE[name] ?? DEFAULT_STYLE.neutral;
};

export const lighten = (hex: string, f: number): string => {
  const c = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(c.slice(i, i + 2), 16));
  const l = (x: number) => Math.min(255, Math.round(x + (255 - x) * f));
  return `rgb(${l(r)},${l(g)},${l(b)})`;
};

export const darken = (hex: string, f: number): string => {
  const c = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(c.slice(i, i + 2), 16));
  return `rgb(${Math.round(r * f)},${Math.round(g * f)},${Math.round(b * f)})`;
};

export const withAlpha = (hex: string, a: number): string => {
  const c = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(c.slice(i, i + 2), 16));
  return `rgba(${r},${g},${b},${a})`;
};

// Right-side layout (mirrors the python pipeline geometry)
export const MARGIN = 70;
export const COLW = Math.round(DESIGN_W * 0.44);            // text column width
export const AX = DESIGN_W - MARGIN;                         // right anchor x
export const COLCX = AX - Math.round(COLW / 2);              // keyword pop center
export const CARD_W = Math.round(DESIGN_W * 0.42);           // 806
export const CARD_H = Math.round((CARD_W * 9) / 16);         // 453
export const CARD_X = DESIGN_W - MARGIN - CARD_W;            // 1044
export const CARD_Y = Math.round((DESIGN_H - CARD_H) / 2);   // 313
export const CARD_INSET = 8;                                 // card frame inset (design px)
export const CARD_RADIUS = 15;                               // card corner radius (design px)

export type OverlayData = {
  id: string;
  type: string;
  t: number;
  dur: number;
  color?: string;
  [key: string]: unknown;
};
