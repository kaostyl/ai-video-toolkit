---
name: video-quality
description: Inspect rendered video, timing, audio and editable delivery assets before handing over a final file.
---

# Video Quality

Run scripts/qc.py on the rendered master with its render_plan.json. View the contact
sheet, check text clipping/contrast/face coverage and listen to representative
playback, joins and SFX. Probe duration, resolution, FPS and audio tracks. Compare
with the brief; a contact sheet cannot prove animation pacing or sync alone.

If captions were added later, inspect the captioned MP4 too. Correct material issues
and rerun relevant checks. Deliver MP4, SRT and requested assets. For overlay-only
FCPXML deliver source master, assets and SFX paths; verify import in the actual
editor before claiming success. The XML does not reproduce full cut history,
ducking/normalization or captions. Explain limitations observed, not speculative
ones. Synthetic demo success verifies that path only, not provider/transcription.
