# Dependencies and media rights

The MIT license covers the toolkit's code and original workflow instructions. It
does not replace the licenses of dependencies, fonts, providers, or user media.
No third-party plugin skill packs, host binaries, stock media, fonts, or model
weights are bundled.

- FFmpeg/FFprobe: install separately; the build's LGPL/GPL and codec terms apply.
  https://ffmpeg.org/legal.html
- Pillow and NumPy: their upstream licenses apply.
- Optional faster-whisper/CTranslate2 and downloaded model weights: see
  https://github.com/SYSTRAN/faster-whisper and the selected model's license.
- Optional Remotion/React packages: the lockfile records dependency metadata.
  Remotion has its own license and usage conditions; check eligibility before use:
  https://www.remotion.dev/docs/license
- Optional HyperFrames/GSAP: install or download from their upstream sources;
  https://github.com/heygen-com/hyperframes and https://gsap.com/community/standard-license/
- Browser renderers request Space Grotesk and JetBrains Mono from Google Fonts.
  PIL uses locally installed fonts. No font file is distributed here.
- Optional Pexels footage: inspect and respect current media/API terms:
  https://www.pexels.com/license/ and https://www.pexels.com/api/

Demo media is generated locally from color and sine sources; it contains no
recorded person or copyrighted music. Users supply their own footage and music.
Cloud providers, accounts, subscriptions, credentials, and permissions are not
included. No cloud generation is called by the demo.
