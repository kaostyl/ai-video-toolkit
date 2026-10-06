#!/usr/bin/env python3
"""Audit distributable files for obvious personal data, secrets and scope errors."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {'.git','.work','projects','node_modules','.venv','__pycache__'}
TEXT_SUFFIXES = {'.py','.md','.json','.tsx','.ts','.mjs','.html','.txt','.yml','.yaml'}
PATTERNS = [
    ('user directory', re.compile(r'(?i)(?:[A-Z]:[/\\]Users[/\\][^/\\\s]+|/' + r'Users/[^/\s]+|/' + r'home/[^/\s]+)')),
    ('private key', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
    ('provider token', re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{30,}|AKIA[A-Z0-9]{16})')),
    ('email address', re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')),
]


def files():
    for p in sorted(ROOT.rglob('*')):
        rel = p.relative_to(ROOT)
        if p.is_file() and not any(part in IGNORED_DIRS for part in rel.parts):
            yield p, rel.as_posix()


def audit(write_manifest=False):
    errors, manifest = [], []
    for p, name in files():
        if p.is_symlink():
            errors.append((name, 'symlink')); continue
        if p.suffix not in TEXT_SUFFIXES and p.name not in {'LICENSE','.gitignore','.gitattributes','.env.example'}:
            errors.append((name, 'unexpected/non-text file')); continue
        try:
            content = p.read_text(encoding='utf-8-sig')
        except UnicodeError:
            errors.append((name, 'non-UTF8 file')); continue
        for label, pattern in PATTERNS:
            if pattern.search(content): errors.append((name, label))
        if name != 'catalog/manifest.json':
            manifest.append({'path':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
    catalog = json.loads((ROOT/'catalog/capabilities.json').read_text(encoding='utf-8'))
    for row in catalog['skills']:
        if not (ROOT/row['entrypoint']).is_file(): errors.append((row['entrypoint'],'missing skill'))
        if row['name'] not in {'video-planning','video-editing','video-overlays','video-captions','video-audio','video-generation','video-quality','youtube-packaging'}:
            errors.append((row['name'],'outside video scope'))
    manifest_path=ROOT/'catalog/manifest.json'
    if not write_manifest and manifest_path.exists():
        expected=json.loads(manifest_path.read_text(encoding='utf-8'))['files']
        if expected != manifest: errors.append(('catalog/manifest.json','content changed; refresh audit manifest'))
    if not errors and write_manifest:
        manifest_path.write_text(json.dumps({'scope':'video-only','files':manifest},indent=2)+'\n',encoding='utf-8',newline='\n')
    return {'ok':not errors,'files':len(manifest),'skills':len(catalog['skills']),'errors':errors}


if __name__ == '__main__':
    result=audit('--write-manifest' in sys.argv)
    print(json.dumps(result,indent=2))
    sys.exit(0 if result['ok'] else 1)
