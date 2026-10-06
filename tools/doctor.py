#!/usr/bin/env python3
"""Read-only dependency check for local video work. No provider or account calls."""
import importlib.util
import json
import platform
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def report():
    binaries = {name: bool(shutil.which(name)) for name in ['ffmpeg','ffprobe','node','npm']}
    libraries = {name: importlib.util.find_spec(name) is not None for name in ['PIL','numpy','faster_whisper']}
    subtitles = False
    if binaries['ffmpeg']:
        result = subprocess.run(['ffmpeg','-hide_banner','-filters'],capture_output=True,text=True)
        subtitles = any(' subtitles ' in line for line in result.stdout.splitlines())
    return {'python': platform.python_version(), 'system': platform.system(),
            'binaries': binaries, 'libraries': libraries,
            'pil_render_ready': binaries['ffmpeg'] and binaries['ffprobe'] and libraries['PIL'] and libraries['numpy'],
            'captions_filter_available': subtitles,
            'remotion_dependencies_installed': (ROOT/'remotion/node_modules/remotion/package.json').is_file(),
            'cloud_access': 'not supplied by this repository',
            'note': 'Presence checks do not certify a render or a working GPU.'}


if __name__ == '__main__':
    print(json.dumps(report(),indent=2))
