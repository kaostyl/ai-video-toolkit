"""Local integration checks on synthetic media. No cloud service needed."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


edit, captions = load('edit'), load('captions')


class VideoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='video-test-')
        cls.work=Path(cls.temp.name)
        for name,color,audio in [('red.mp4','red',True),('blue.mp4','blue',False)]:
            cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i',f'color={color}:s=160x90:r=12:d=3']
            if audio: cmd+=['-f','lavfi','-i','sine=frequency=440:duration=3']
            cmd+=['-t','3','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(cls.work/name)]
            subprocess.run(cmd,check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def plan(self,clips):
        path=self.work/'edit.json'
        path.write_text(json.dumps({'resolution':[160,90],'fps':12,'clips':clips}),encoding='utf-8')
        return path

    def test_assemble_order_duration_and_mute_audio(self):
        plan=self.plan([{'source':'red.mp4','start':1,'end':2},{'source':'blue.mp4','start':0,'end':2}])
        output=self.work/'assembled.mp4'
        edit.render(plan,output)
        info=edit.probe(output)
        self.assertLess(abs(float(info['format']['duration'])-3),0.2)
        self.assertTrue(any(s['codec_type']=='audio' for s in info['streams']))
        for t,channel in [(0.5,0),(2,2)]:
            pixel=subprocess.check_output(['ffmpeg','-hide_banner','-loglevel','error','-ss',str(t),'-i',str(output),'-frames:v','1','-vf','scale=1:1','-f','rawvideo','-pix_fmt','rgb24','-'])
            self.assertGreater(pixel[channel],pixel[2-channel]+100)
        # The clip without audio must receive silence, not repeat the first clip.
        pcm=subprocess.check_output(['ffmpeg','-hide_banner','-loglevel','error','-ss','1.5','-i',str(output),'-t','0.5','-f','s16le','-ac','1','-'])
        import array
        samples=array.array('h',pcm)
        self.assertLess(max(abs(v) for v in samples),100)

    def test_invalid_ranges_and_nonfinite(self):
        for start,end in [(-1,2),(2,1),(0,20),(0,float('inf'))]:
            with self.assertRaises(ValueError):
                edit.load_plan(self.plan([{'source':'red.mp4','start':start,'end':end}]),self.work/'invalid.mp4')

    def test_refuses_source_overwrite(self):
        with self.assertRaises(ValueError):
            edit.load_plan(self.plan([{'source':'red.mp4'}]),self.work/'red.mp4')

    def test_captions_preserve_duration_and_change_frame(self):
        filters=subprocess.check_output(['ffmpeg','-hide_banner','-filters'],text=True,stderr=subprocess.STDOUT)
        if not any(' subtitles ' in line for line in filters.splitlines()): self.skipTest('libass not installed')
        srt=self.work/'caption file.srt'
        srt.write_text('1\n00:00:00,100 --> 00:00:02,900\nReadable caption\n',encoding='utf-8')
        output=self.work/'captioned.mp4'
        captions.burn(self.work/'red.mp4',srt,output,24)
        self.assertLess(abs(float(edit.probe(output)['format']['duration'])-3),0.2)
        def frame(path):
            return subprocess.check_output(['ffmpeg','-hide_banner','-loglevel','error','-ss','1','-i',str(path),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
        before,after=frame(self.work/'red.mp4'),frame(output)
        self.assertGreater(sum(abs(a-b)>30 for a,b in zip(before,after)),100)

    def test_overlay_composition_on_mute_source(self):
        # Exercise the audio fallback without a heavyweight overlay render.
        plan=self.work/'overlay-plan.json'
        plan.write_text(json.dumps({'project':'mute','source':str(self.work/'blue.mp4'),
            'resolution':[160,90],'fps':12,'overlays':[]}),encoding='utf-8')
        output=self.work/'mute-composed.mp4'
        subprocess.run(['python',str(ROOT/'scripts/compose.py'),'--source',str(self.work/'blue.mp4'),
            '--plan',str(plan),'--out',str(output),'--encoder','cpu'],check=True,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        info=edit.probe(output)
        self.assertLess(abs(float(info['format']['duration'])-3),0.2)
        self.assertTrue(any(s['codec_type']=='audio' for s in info['streams']))

    def test_validation_rejects_unsafe_id_and_nonfinite_time(self):
        for overlay_id,t in [('../escape',1),('safe',float('inf')),('safe',-1)]:
            plan=self.work/'invalid-overlay.json'
            plan.write_text(json.dumps({'overlays':[{'id':overlay_id,'type':'title_band','big':'Test','t':t,'dur':4}]}),encoding='utf-8')
            result=subprocess.run(['python',str(ROOT/'scripts/validate_plan.py'),'--plan',str(plan)],capture_output=True)
            self.assertNotEqual(result.returncode,0)

    def test_fcpxml_escapes_source_name(self):
        import shutil
        import xml.etree.ElementTree as ET
        source=self.work/'clip & demo.mp4'
        shutil.copyfile(self.work/'red.mp4',source)
        plan=self.work/'xml-plan.json'
        plan.write_text(json.dumps({'project':'demo','resolution':[160,90],'fps':12,'overlays':[]}),encoding='utf-8')
        timeline=self.work/'timeline.fcpxml'
        subprocess.run(['python',str(ROOT/'scripts/davinci_timeline.py'),'--plan',str(plan),
            '--source',str(source),'--out',str(timeline)],check=True,stdout=subprocess.PIPE)
        parsed=ET.parse(timeline)
        self.assertEqual(parsed.find('./resources/asset').attrib['name'],source.name)


if __name__=='__main__':
    unittest.main()
