# Video agent entry point

This repository contains video production workflows and runnable local tools.
It does not contain connected accounts, provider tools, or inherited permission.
Read README.md. Run `python tools/doctor.py` if execution is available. Choose only
the skill relevant to the request from `catalog/capabilities.json` and read it.

## Match the requested outcome

- Existing footage with cuts/reordering: `skills/video-editing/SKILL.md`.
- Existing edit to enhance without changing cuts: `skills/video-overlays/SKILL.md`.
- Dialogue and captions: `skills/video-captions/SKILL.md`.
- Script, shot list, research and screen recordings: `skills/video-planning/SKILL.md`.
- Original generated shots or AI presenters: `skills/video-generation/SKILL.md`.
- Music, dialogue clarity and SFX: `skills/video-audio/SKILL.md`.
- Delivery and inspection: `skills/video-quality/SKILL.md`.
- YouTube title, description and thumbnail: `skills/youtube-packaging/SKILL.md`.

Only claim execution when the host can run the required tools and access the media.
If the environment only reads GitHub, deliver a usable plan and commands and state
that rendering still needs an execution environment. Never treat a link as a tool
installation. Use currently exposed provider tool schemas, not guessed calls.

## Local execution

Use an isolated working directory under `projects/<project>/`. All toolkit scripts
are referenced by absolute path from that working directory; all project outputs
stay there. Do not reuse another project's `out/transcript.txt`, assets or plan.
Keep source media unchanged; choose new output filenames. Inspect `--help` and
`docs/PLANS.md` before writing a plan. Use PIL + CPU for the smallest setup;
Remotion requires Node/npm and browser dependencies. Never assume NVENC works just
because the FFmpeg binary lists it. Use `--encoder cpu` when uncertain.

For overlays, inspect the transcript and storyboard before designing the plan.
No two overlays should overlap; leave reading time and clear the visible faces.
Validate before rendering. The PIL layout supports a side column; browser layouts
use wide top/bottom bands and larger cards. Preview the chosen renderer instead
of assuming identical placement. Render and compose at the same resolution/FPS.
Keep `_layout.json` and `_cardmask.png` with the PIL assets.

After cuts, transcribe the assembled master so captions and overlays match its
new timecodes. The transcript's word-gap file is a heuristic, not a reliable edit
decision list. Do not cut speech solely from gaps between word start times.

## Generation and publication

Read docs/CLOUD.md before provider calls. Get a current quote for model, duration,
resolution, audio and quantity. Stay within an accepted budget; count trials and
retakes. The local demo does not call a provider. No provider prices or free-quota
promises are bundled. A web subscription may not include API or automated access.

Use supplied or licensed footage/music. Treat real-account screenshots as private
project inputs; crop or mask sensitive information before public use. Never put
keys, cookies, sessions, `.env`, personal media or account histories into Git.
Present fictional presenters and illustrative demos truthfully; do not invent
product testing, testimonials or measured results. Publishing needs user authority.

## Delivery

Run applicable checks; inspect the contact sheet and representative playback.
Report actual resolution, duration, audio findings and any unresolved limitation.
Deliver the final MP4 and any requested editable assets. FCPXML is an overlay/SFX
timeline, not a complete reconstruction of cuts, captions or the rendered audio mix.
Verify editor import separately before claiming it works. Never claim a synthetic
smoke render proves transcription, cloud access, desktop integration or voice quality.
