---
name: video-overlays
description: Add animated titles, HUD cards, keywords and synchronized SFX to a completed edit without changing its cuts.
---

# Video Overlays

Read docs/PLANS.md. Read the master transcript, generate a storyboard and view it.
Choose meaningful definitions, numbers, comparisons and conclusions; preserve
faces and leave reading time. Write a sparse overlay plan with unique safe IDs,
no overlap, clear semantic colors and discrete timed sfx_events.

Use scripts/pipeline.py with --skip-transcribe after transcription, --renderer pil
and --encoder cpu for the minimal setup. The pipeline preserves master duration,
validates the plan, synthesizes SFX, renders alpha assets, composes the MP4, exports
FCPXML and creates QC. Render and compose at the same resolution/FPS.

Optional Remotion uses Node/npm and a browser; HyperFrames is a separate advanced
renderer. See docs/QUICKSTART.md and THIRD_PARTY.md. Their layouts differ from PIL;
inspect actual frames rather than assuming face-safe positioning. Keep PIL layout
and mask sidecars. Inspect output/qc/contact_sheet.png and animation playback.
Do not deliver a render with missing assets. Keep assets and SFX for relinking.
