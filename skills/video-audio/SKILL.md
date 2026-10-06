---
name: video-audio
description: Mix dialogue, licensed music and locally synthesized sound effects, then measure the final loudness.
---

# Video Audio

Inspect the source audio and keep speech intelligible. scripts/sfx.py synthesizes
deterministic whooshes/pops/ticks and other short sounds without cloud generation.
In the overlay plan, sync sfx_events to actual animation keyframes, keep each
event within its overlay, and use small gains rather than stacking loud effects.

scripts/compose.py supports a supplied music file, music gain, ducking under voice,
SFX gain and --loudnorm. Use authorized music. --loudnorm targets -14 LUFS and
-1.5 dBTP; measure the output with scripts/qc.py and listen. Targets do not ensure
subjective voice quality or exact results for all content. The exported FCPXML
does not reproduce the rendered ducking/master chain or all event gains.
For narration generation, use the user's actually available provider and budget.
