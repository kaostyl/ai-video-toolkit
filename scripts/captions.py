#!/usr/bin/env python3
"""Burn an aligned SRT into a new MP4 with FFmpeg/libass. Never edits the source."""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def burn(source, srt, output, font_size=24):
    source, srt, output = map(lambda p: Path(p).resolve(), (source, srt, output))
    if not source.is_file() or not srt.is_file():
        raise ValueError('source video and SRT must exist')
    if output in (source, srt) or output.suffix.lower() != '.mp4':
        raise ValueError('output must be a new .mp4 path, not an input')
    if not 12 <= font_size <= 96:
        raise ValueError('font size must be between 12 and 96')
    filters = subprocess.check_output(['ffmpeg', '-hide_banner', '-filters'],
                                      text=True, stderr=subprocess.STDOUT)
    if not any(' subtitles ' in line for line in filters.splitlines()):
        raise ValueError('FFmpeg subtitles filter missing; install a build with libass')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Fixed relative basename avoids FFmpeg filter escaping on Windows and spaces.
    with tempfile.TemporaryDirectory(prefix='video-captions-') as scratch:
        shutil.copyfile(srt, Path(scratch)/'captions.srt')
        style = f'FontName=Arial,FontSize={font_size},Outline=2,Shadow=0,MarginV=28,Alignment=2'
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                        '-i', str(source), '-vf', f"subtitles=captions.srt:force_style='{style}'",
                        '-map', '0:v:0', '-map', '0:a?', '-c:v', 'libx264',
                        '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                        '-c:a', 'copy', '-movflags', '+faststart', str(output)],
                       cwd=scratch, check=True)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--srt', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--font-size', type=int, default=24)
    args = parser.parse_args()
    try:
        print(burn(args.source, args.srt, args.out, args.font_size))
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error)+'\n')
