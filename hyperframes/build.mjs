#!/usr/bin/env node
/**
 * build.mjs â€” HyperFrames batch renderer for Video Toolkit v6 overlays.
 * Drop-in replacement for remotion/render-assets.mjs: reads plan.json and
 * renders every non-broll overlay to a ProRes 4444 alpha .mov (same ids), so
 * compose.py / davinci_timeline.py keep working unchanged.
 *
 * Usage:
 *   node build.mjs --plan ../out_faceless/plan.json --out ../assets_faceless --res 3840x2160 [--only id1,id2] [--quality high]
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const arg = (n, d) => { const i = process.argv.indexOf(`--${n}`); return i >= 0 ? process.argv[i + 1] : d; };

const planPath = arg('plan');
const outDir = path.resolve(arg('out', '../assets'));
const res = arg('res', '1920x1080');
const only = arg('only', null)?.split(',');
const quality = arg('quality', 'high');
const workers = arg('workers', '4');
const fps = Number(arg('fps', '30'));
if (!planPath) { console.error('--plan requis'); process.exit(1); }

const [W, H] = res.toLowerCase().split('x').map(Number);
const SCALE = (W / 1920).toFixed(6);
const plan = JSON.parse(fs.readFileSync(path.resolve(planPath), 'utf8'));
const style = plan.style ?? {};
fs.mkdirSync(outDir, { recursive: true });

const template = fs.readFileSync(path.join(__dirname, 'overlay.html'), 'utf8');

const overlays = plan.overlays.filter(o => o.type !== 'broll' && (!only || only.includes(o.id)));
console.log(`hyperframes build  ${W}x${H}@${fps}  ->  ${outDir}   (${overlays.length} overlays)`);

const t0 = Date.now();
let ok = 0, fail = 0;
for (const ov of overlays) {
  const dur = Math.max(0.1, Number(ov.dur) || 5);
  const inject =
    `window.__OV=${JSON.stringify(ov)};` +
    `window.__STYLE=${JSON.stringify(style)};` +
    `window.__FPS=${fps};window.__DUR=${dur};`;
  const html = template
    .replaceAll('__W__', String(W))
    .replaceAll('__H__', String(H))
    .replaceAll('__SCALE__', SCALE)
    .replaceAll('__DUR__', String(dur))
    .replace('__INJECT__', inject);
  // render() requires a project index.html; write each overlay there in turn (sequential = no clash)
  fs.writeFileSync(path.join(__dirname, 'index.html'), html);
  const outPath = path.join(outDir, `${ov.id}.mov`);
  const t1 = Date.now();
  try {
    execFileSync('npx', ['--yes', 'hyperframes@0.7.42', 'render', '.',
      '-o', outPath, '--format', 'mov', '--quality', quality, '--fps', String(fps), '-w', String(workers), '--quiet'],
      { cwd: __dirname, stdio: ['ignore', 'ignore', 'inherit'], shell: true });
    ok++;
    console.log(`  ok  ${ov.id}.mov  (${dur}s, ${((Date.now() - t1) / 1000).toFixed(1)}s)`);
  } catch (e) {
    fail++;
    console.log(`  FAIL ${ov.id}.mov  -> ${e.message.split('\n')[0]}`);
  }
}
console.log(`done. ${ok} ok / ${fail} fail  (total ${((Date.now() - t0) / 1000).toFixed(1)}s)`);

if (fail) process.exitCode = 1;
