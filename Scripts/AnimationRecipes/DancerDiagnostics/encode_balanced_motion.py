import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Encode only completed native frame sequences, without touching source assets."""
from pathlib import Path
import json,subprocess,numpy as np
from PIL import Image
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
report=json.loads((R/'NativeVexaBalancedMotion.json').read_text());assert report['ok']
ffmpeg=Path('C:/Program Files/Lian-Li/L-Connect 3/x64/ffmpeg.exe');assert ffmpeg.is_file()
out={'source':'native offscreen scene capture','fps':24,'frames_per_view':384,'views':{},'owner_accepted':False}
for view in report['views']:
 folder=R/'NativeVexaBalancedMotion'/view;files=[folder/f'{i:04d}.png' for i in range(384)];assert all(p.is_file() for p in files)
 dest=D/f'Vexa_ShoulderBalanced_Native_{view}.mp4'
 subprocess.run([str(ffmpeg),'-hide_banner','-loglevel','error','-y','-framerate','24','-i',str(folder/'%04d.png'),'-frames:v','384','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],check=True)
 frames=[np.asarray(Image.open(p).convert('RGB').resize((80,80)),dtype=float)/255 for p in files]
 difference=[float(np.abs(frames[i]-frames[i-1]).mean()) for i in range(1,384)];rank=np.argsort(difference)[-6:][::-1]
 out['views'][view]={'video':str(dest),'bytes':dest.stat().st_size,'largest_frame_changes':[{'frame':int(i+1),'seconds':float((i+1)/24),'mean_pixel_change':difference[i]} for i in rank],'loop_pixel_change':float(np.abs(frames[-1]-frames[0]).mean())}
rows=report['captured'];out['max_pose_seek_error_seconds']=max(abs(x['seconds']-x['actual_position']) for x in rows)
assert out['max_pose_seek_error_seconds']<1e-5
(R/'NativeBalancedVideos.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True)
