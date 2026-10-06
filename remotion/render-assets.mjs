#!/usr/bin/env node
/**
 * render-assets.mjs — Batch-render every overlay of a plan.json to
 * ProRes 4444 .mov files with alpha, drop-in compatible with compose.py.
 *
 * Bundles the Remotion project ONCE, then renders each overlay with its own
 * input props. Also writes _layout.json + _cardmask.png for the frosted-glass
 * pass in compose.py.
 *
 * Usage:
 *   node render-assets.mjs --plan ../out/plan.json --out ../assets --res 3840x2160 [--only id1,id2]
 */
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const arg = (name, dflt) => {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : dflt;
};

const planPath = arg('plan');
const outDir = path.resolve(arg('out', '../assets'));
const res = arg('res', null);
const only = arg('only', null)?.split(',');
if (!planPath) { console.error('--plan requis'); process.exit(1); }

const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
let [W, H] = res ? res.toLowerCase().split('x').map(Number) : (plan.resolution ?? [1920, 1080]);
const fps = plan.fps ?? 30;
const side = plan.side ?? 'right';
const style = plan.style ?? {};
fs.mkdirSync(outDir, {recursive: true});

// mirrors theme.ts geometry
const CARD_W = Math.round(W * 0.42);
const CARD_H = Math.round((CARD_W * 9) / 16);
const CARD_X = W - Math.round((70 * W) / 1920) - CARD_W;
const CARD_Y = Math.round((H - CARD_H) / 2);

const t0 = Date.now();
console.log(`remotion render-assets  ${W}x${H}@${fps}  side=${side}  ->  ${outDir}`);
const serveUrl = await bundle({
  entryPoint: path.join(__dirname, 'src', 'index.ts'),
  onProgress: () => {},
});
console.log(`  bundle ok (${((Date.now() - t0) / 1000).toFixed(1)}s)`);

for (const ov of plan.overlays) {
  if (only && !only.includes(ov.id)) continue;
  if (ov.type === 'broll') continue; // stock footage: fetched by scripts/broll.py
  const inputProps = {overlay: ov, style, side, width: W, height: H, fps};
  const composition = await selectComposition({serveUrl, id: 'Overlay', inputProps});
  const t1 = Date.now();
  await renderMedia({
    serveUrl,
    composition,
    codec: 'prores',
    proResProfile: '4444',
    pixelFormat: 'yuva444p10le',
    imageFormat: 'png',
    inputProps,
    outputLocation: path.join(outDir, `${ov.id}.mov`),
    logLevel: 'error',
  });
  console.log(`  rendered ${ov.id}.mov (${composition.durationInFrames}f, ${((Date.now() - t1) / 1000).toFixed(1)}s)`);
}

// V5 full-screen design: no side card -> no frosted-glass sidecars.
// Remove stale ones so compose.py doesn't blur a card region that no longer exists.
for (const f of ['_layout.json', '_cardmask.png']) {
  const p = path.join(outDir, f);
  if (fs.existsSync(p)) fs.unlinkSync(p);
}
console.log(`done. (total ${((Date.now() - t0) / 1000).toFixed(1)}s)`);
