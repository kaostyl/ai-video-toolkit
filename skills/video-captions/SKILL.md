---
name: video-captions
description: Transcribe dialogue to timestamped SRT, correct it and optionally burn readable subtitles into a video.
---

# Video Captions

Install requirements-transcription.txt only when transcription is needed. Run
scripts/transcribe.py on the final assembled master with --lang matching speech,
--words and --device cpu unless CUDA is actually configured. First use downloads
weights. Check names, terminology, punctuation and timestamps against the audio.
Word-start gaps are a heuristic; they do not prove silence or safe cut points.

Keep an editable SRT. To burn captions, inspect scripts/captions.py --help and run
it to a new MP4. It requires FFmpeg's subtitles filter (libass). Use a readable
size, bottom safe margins and no conflict with overlays. Review a captioned frame
and playback with long lines. Incrustation is not recreated in the FCPXML. If the
filter is unavailable, deliver SRT and explain installation or editor import.
