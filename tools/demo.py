#!/usr/bin/env python3
"""Offline end-to-end smoke render on synthetic media. No account/API calls."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT
WORK = ROOT / '.work' / 'demo'

def run(command):
    result = subprocess.run(command,cwd=VIDEO,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONUTF8':'1'})
    WORK.mkdir(parents=True,exist_ok=True)
    with (WORK/'run.log').open('a',encoding='utf-8') as log:
        log.write('COMMAND: '+repr(command)+'\n'+result.stdout+'\n')
    if result.returncode:
        print(result.stdout[-5000:].encode('ascii','backslashreplace').decode('ascii'))
        raise RuntimeError('Local smoke stage failed: '+command[0])

def smoke():
    WORK.mkdir(parents=True,exist_ok=True)
    source = WORK/'source.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=0x172026:s=640x360:r=12:d=24','-f','lavfi','-i','sine=frequency=220:sample_rate=48000:duration=24','-af','volume=0.1','-t','24','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(source)])
    plan = {'project':'offline_smoke','source':str(source),'resolution':[640,360],'fps':12,'side':'right','overlays':[
        {'id':'title','type':'title_band','t':1,'dur':4,'color':'neutral','big':'Local demo','small':'An original overlay','sfx_events':[{'at':0,'name':'whoosh','vol':0.4}]},
        {'id':'check','type':'schema_checklist','t':12,'dur':10,'color':'solution','kicker':'LOCAL CHECK','rows':[{'text':'Image','ok':True},{'text':'Audio','ok':True},{'text':'Export','ok':True}],'sfx_events':[{'at':0,'name':'whoosh','vol':0.4},{'at':4,'name':'ding','vol':0.4}]}
    ]}
    plan_path=WORK/'plan.json'
    plan_path.write_text(json.dumps(plan,indent=2),encoding='utf-8')
    run([sys.executable,str(VIDEO/'scripts/pipeline.py'),'--source',str(source),'--plan',str(plan_path),'--skip-transcribe','--renderer','pil','--res','640x360','--encoder','cpu','--music','none','--loudnorm','--assets',str(WORK/'assets'),'--sfx-dir',str(WORK/'sfx'),'--out-dir',str(WORK/'output')])
    final=WORK/'output/offline_smoke_FINAL.mp4'
    timeline=WORK/'output/offline_smoke.fcpxml'
    if not final.is_file() or not timeline.is_file():
        raise RuntimeError('Expected MP4 and FCPXML were not produced.')
    probe=subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,width,height','-of','json',str(final)],text=True)
    result=json.loads(probe)
    video=next(row for row in result['streams'] if row['codec_type']=='video')
    if [video['width'],video['height']]!=[640,360] or abs(float(result['format']['duration'])-24)>0.2:
        raise RuntimeError('Output resolution or duration mismatch.')
    summary={'ok':True,'cloud_calls':0,'width':640,'height':360,'duration_seconds':float(result['format']['duration']),'mp4':final.relative_to(ROOT).as_posix(),'fcpxml':timeline.relative_to(ROOT).as_posix(),'contact_sheet':'.work/demo/output/qc/contact_sheet.png'}
    (WORK/'result.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    smoke()
