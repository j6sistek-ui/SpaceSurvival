import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Encode all captured angles and verify decoded frame counts; no quality claim."""
from pathlib import Path
import subprocess,json,hashlib
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'ZeroGSharedHip';report=json.loads((O/'FullMotion.json').read_text());assert report['ok']
ffmpeg=Path('C:/Program Files/Lian-Li/L-Connect 3/x64/ffmpeg.exe');assert ffmpeg.is_file();result={'fps':24,'videos':[]}
for name,duration in report['clips'].items():
 for view in ('front','back','stage'):
  folder=O/'FullMotion'/name/view;expected=round(duration*24);assert len(list(folder.glob('*.png')))==expected
  target=D/f'Vexa_ZeroG_{name}_{view}.mp4'
  run=subprocess.run([str(ffmpeg),'-hide_banner','-loglevel','warning','-y','-framerate','24','-i',str(folder/'%05d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],capture_output=True,text=True);assert run.returncode==0,run.stderr[-1000:]
  decode=subprocess.run([str(ffmpeg),'-hide_banner','-loglevel','error','-i',str(target),'-progress','pipe:1','-f','null','-'],capture_output=True,text=True);assert decode.returncode==0,decode.stderr[-1000:]
  count=int([line.split('=',1)[1] for line in decode.stdout.splitlines() if line.startswith('frame=')][-1]);assert count==expected
  result['videos'].append({'clip':name,'view':view,'path':str(target),'frames':expected,'decoded_frames':count,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'encoder_warnings':run.stderr[-1000:]});print('ZERO_G_ENCODED',name,view,count,flush=True)
(O/'Videos.json').write_text(json.dumps(result,indent=2))
