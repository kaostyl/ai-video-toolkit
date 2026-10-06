---
name: video-editing
description: Cut and assemble local video clips from an edit decision list using FFmpeg, preserving source files.
---

# Video Editing

Read docs/PLANS.md and inspect script help for scripts/edit.py. Probe all inputs;
view a storyboard or representative clips before choosing cuts. Use a new working
folder per project. Write edit.json with ordered source/start/end entries relative
to its own folder, resolution and FPS. Run edit.py to a new MP4 filename.

The tool makes hard cuts, normalizes video/audio, and inserts silence for mute
clips. It validates ranges before rendering and refuses to overwrite an input.
It does not automatically detect semantic cuts or deliver a native editing project.
Inspect the joins and total duration. Transcribe the assembled master for captions
and overlays so subsequent timestamps refer to the final edit. If a full editable
cut timeline is needed, use an actual supported editor integration or build and
verify one; the overlay FCPXML does not reconstruct internal master cuts.
