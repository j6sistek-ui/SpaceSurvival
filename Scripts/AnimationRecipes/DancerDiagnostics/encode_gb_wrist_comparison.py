import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Encode completed native captures and retain exact pose-seek evidence."""
import json,subprocess
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
source=json.loads((R/'NativeGBWristComparison.json').read_text());assert source['ok']
ffmpeg=Path('C:/Program Files/Lian-Li/L-Connect 3/x64/ffmpeg.exe');assert ffmpeg.is_file()
report={'scope':'Native private Vexa, unconstrained clips; matched wrist events and full G1. No pole contact, anatomical or artistic acceptance.','videos':[]}
for seg in source['segments']:
 folder=R/'NativeGBWristComparison'/seg['name'];assert all((folder/f'{i:04d}.png').is_file() for i in range(seg['frames']))
 dest=D/('Vexa_Wrist_'+seg['name']+'.mp4')
 subprocess.run([str(ffmpeg),'-hide_banner','-loglevel','error','-y','-framerate',str(seg['fps']),'-i',str(folder/'%04d.png'),'-frames:v',str(seg['frames']),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],check=True)
 check=subprocess.run([str(ffmpeg),'-v','error','-i',str(dest),'-f','null','-','-progress','pipe:1','-nostats'],check=True,capture_output=True,text=True)
 decoded=[int(line.split('=',1)[1]) for line in check.stdout.splitlines() if line.startswith('frame=')]
 assert decoded and decoded[-1]==seg['frames'],(seg['name'],decoded)
 assert not check.stderr.strip(),check.stderr
 report['videos'].append({**seg,'file':str(dest),'bytes':dest.stat().st_size,'decoded_frames':decoded[-1]})
report['max_seek_error_seconds']=max(abs(x['seconds']-x['actual_position']) for x in source['captured'])
assert report['max_seek_error_seconds']<1e-5
(R/'VexaDistalRepair/NativeGBWristVideos.json').write_text(json.dumps(report,indent=2));print('GB_WRIST_VIDEOS',len(report['videos']),report['max_seek_error_seconds'])
