#!/usr/bin/env python3
"""Cut and assemble local clips with hard cuts. No cloud calls or source writes."""
import argparse
import json
import math
import os
import subprocess
import tempfile
from pathlib import Path


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration:stream=codec_type', '-of', 'json', str(path)
    ], text=True, encoding='utf-8'))


def finite(value, name):
    if isinstance(value, bool):
        raise ValueError(name + ' must be a finite number')
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(name + ' must be finite')
    return number


def load_plan(plan_path, output):
    plan_path = Path(plan_path).resolve()
    plan = json.loads(plan_path.read_text(encoding='utf-8-sig'))
    res = plan.get('resolution', [1920, 1080])
    if not isinstance(res, list) or len(res) != 2 or any(
        type(v) is not int or v < 2 or v > 8192 or v % 2 for v in res
    ):
        raise ValueError('resolution must be two even integers between 2 and 8192')
    fps = plan.get('fps', 30)
    if type(fps) is not int or not 1 <= fps <= 120:
        raise ValueError('fps must be an integer between 1 and 120')
    clips = plan.get('clips')
    if not isinstance(clips, list) or not 1 <= len(clips) <= 100:
        raise ValueError('clips must be a list of 1 to 100 entries')
    validated = []
    for index, clip in enumerate(clips):
        source = (plan_path.parent / clip['source']).resolve()
        if not source.is_file():
            raise ValueError(f'clip {index}: source not found')
        if source == Path(output).resolve():
            raise ValueError('output must not overwrite an input source')
        info = probe(source)
        duration = finite(info['format']['duration'], 'source duration')
        if not any(s['codec_type'] == 'video' for s in info['streams']):
            raise ValueError(f'clip {index}: source has no video')
        start = finite(clip.get('start', 0), 'start')
        end = finite(clip.get('end', duration), 'end')
        if not 0 <= start < end <= duration + 0.001:
            raise ValueError(f'clip {index}: require 0 <= start < end <= source duration')
        if round((end-start) * fps) < 1:
            raise ValueError(f'clip {index}: range shorter than one output frame')
        audio = any(s['codec_type'] == 'audio' for s in info['streams'])
        validated.append((source, start, end, audio))
    return res, fps, validated


def render(plan_path, output):
    output = Path(output).resolve()
    if output.suffix.lower() != '.mp4':
        raise ValueError('output must end in .mp4')
    res, fps, clips = load_plan(plan_path, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    width, height = res
    with tempfile.TemporaryDirectory(prefix='video-edit-') as scratch:
        scratch = Path(scratch)
        for index, (source, start, end, audio) in enumerate(clips):
            duration = round((end-start)*fps)/fps
            cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                   '-ss', str(start), '-i', str(source)]
            if not audio:
                cmd += ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo']
            cmd += ['-map', '0:v:0', '-map', '0:a:0' if audio else '1:a:0',
                    '-t', str(duration), '-vf',
                    f'scale={width}:{height}:force_original_aspect_ratio=decrease,'
                    f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}',
                    '-af', 'aresample=48000,apad', '-ac', '2', '-ar', '48000',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                    '-video_track_timescale', str(fps*1000),
                    str(scratch/f'clip{index:04d}.mp4')]
            subprocess.run(cmd, check=True)
        (scratch/'concat.txt').write_text(''.join(
            f"file 'clip{index:04d}.mp4'\n" for index in range(len(clips))
        ), encoding='utf-8')
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                        '-f', 'concat', '-safe', '1', '-i', 'concat.txt',
                        '-c', 'copy', '-movflags', '+faststart', str(output)],
                       cwd=scratch, check=True)
    return {'output': str(output), 'clip_count': len(clips), 'resolution': res,
            'fps': fps, 'expected_duration': sum(round((e-s)*fps)/fps for _,s,e,_ in clips)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(render(args.plan, args.out), indent=2))
    except (ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + '\n')
