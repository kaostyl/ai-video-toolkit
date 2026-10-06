# English quick start

Give your agent the repository URL and ask it to read AGENTS.md. Actual rendering
requires code execution and access to your media. A read-only chat can plan but
cannot produce a rendered file from the link alone.

Install Python 3.10+, FFmpeg/FFprobe and `pip install -r requirements.txt`.
Run `python tools/doctor.py` and `python tools/demo.py` for a synthetic 24-second
local example. Outputs are in `.work/demo/` and contain no real person.

Use a separate working folder per project. Reference toolkit scripts by absolute
path from that folder. For cuts, use `scripts/edit.py` with examples/edit.json.
For transcripts, install requirements-transcription.txt and run transcribe.py
with `--device cpu --lang en`; first use downloads model weights.
Inspect the storyboard and transcript, then write an overlay plan (docs/PLANS.md).
Run pipeline.py with `--skip-transcribe --renderer pil --encoder cpu --loudnorm`.
Inspect the resulting contact sheet, listen to the mix and deliver the MP4.
Optional captions.py burns an aligned SRT using FFmpeg/libass.

PIL/CPU is the default. Optional Remotion requires Node/npm/browser dependencies;
HyperFrames is an advanced alternative. Their licenses and downloads are separate.
Cloud generation requires the user's own supported provider connection and an
accepted budget. No provider runtime, account, API key or subscription is included.

The exported FCPXML describes the master, overlay assets and SFX; it does not
reconstruct the master's internal cuts, caption burn-in, ducking or normalization.
Verify actual import in your editor. See docs/QUICKSTART.md for complete commands.
