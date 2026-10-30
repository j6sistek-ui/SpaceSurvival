import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""G2 fixed-basis bone parity, decoded media and labelled full-body views."""
from pathlib import Path
import subprocess, json
code = (_recipe_dir/'compare_supported_release_native.py').read_text(encoding='utf-8')
exec(compile(code.replace('GBSupportedRelease', 'G2SupportedPassage').replace('NativeSupportedRelease', 'NativeG2Support'), __file__, 'exec'))
code = (_recipe_dir/'review_release_media.py').read_text(encoding='utf-8')
code = code.replace('NativeSupportedRelease', 'NativeG2Support').replace('300,320,360,440', '300,320,360,400')
exec(compile(code, __file__, 'exec'))
ffmpeg = 'C:/Program Files/Lian-Li/L-Connect 3/x64/ffmpeg.exe'
rows=[]
for view in ['front','back']:
    destination=D/f'G2_SupportedPassage_{view}.mp4'
    command=[ffmpeg,'-y','-v','error','-framerate','24','-i',str(O/view/'%04d.png'),'-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(destination)]
    subprocess.run(command,check=True)
    p=subprocess.run([ffmpeg,'-v','error','-i',str(destination),'-f','null','-','-progress','pipe:1'],capture_output=True,text=True,check=True)
    assert 'frame=401' in p.stdout and 'progress=end' in p.stdout,p.stdout
    rows.append({'view':view,'file':str(destination),'bytes':destination.stat().st_size,'decoded_frames':401,'fps':24})
(O/'Videos.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows))
