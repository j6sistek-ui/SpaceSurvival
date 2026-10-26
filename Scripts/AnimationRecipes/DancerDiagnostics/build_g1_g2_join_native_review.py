"""Add decoded native bridge evidence to the existing source review page."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

project=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()
source=project/'SourceAssets/DanceRefinement_20261025'
out=project/'.agent/local/AnimationReview_20261025/G1G2JoinNative240'
capture=json.loads((out/'NativeCapture.json').read_text(encoding='utf-8'))
parity=json.loads((out/'NativeParity.json').read_text(encoding='utf-8'))
assert capture['ok'] and parity['ok'] and capture['action_sha256']==parity['action_sha256']
ffmpeg=Path('C:/Program Files/Lian-Li/L-Connect 3/x64/ffmpeg.exe')
movie=source/'G1G2_Join_Unreal.mp4'
assert not movie.exists(),'Preserve existing native video'
files=sorted((out/'NativeViews').glob('loop_*.png'))
assert len(files)==capture['frames']==97
run=subprocess.run([str(ffmpeg),'-nostdin','-v','warning','-framerate','24','-i',str(out/'NativeViews/loop_%04d.png'),
    '-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p','-movflags','+faststart',str(movie)],
    capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
(out/'NativeEncode.log').write_bytes(run.stderr);assert run.returncode==0
decode=subprocess.run([str(ffmpeg),'-nostdin','-v','error','-i',str(movie),'-map','0:v:0','-f','framemd5','-'],
    capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
rows=[line for line in decode.stdout.splitlines() if line and not line.startswith(b'#')]
assert decode.returncode==0 and len(rows)==97
(out/'NativeDecode.framemd5').write_bytes(decode.stdout)
images=[]
for view in ('front','back','side'):
    shots=[r for r in capture['captures'] if r['kind']=='shoulder' and r['view']==view]
    assert len(shots)==8
    sheet=Image.new('RGB',(1600,840),(28,35,41));draw=ImageDraw.Draw(sheet)
    for i,row in enumerate(shots):
        with Image.open(row['path']) as picture:sheet.paste(picture.resize((400,400)),((i%4)*400,(i//4)*420))
        draw.text(((i%4)*400+8,(i//4)*420+402),f'{view} / {row["seconds"]:.2f}s',fill='white')
    path=source/f'G1G2_Join_Unreal_{view}.jpg';assert not path.exists()
    sheet.save(path,quality=94);images.append(path.name)
page=source/'G1G2JoinReview.html'
html=page.read_text(encoding='utf-8')
old='This transition has not yet been imported or accepted in game.'
assert old in html and '<h2>Unreal bridge proof</h2>' not in html
html=html.replace(old,'A separate native bridge proof is below; production adoption and complete routine acceptance remain open.')
html+='<h2>Unreal bridge proof</h2><p>The four-second bridge after a fresh private-map reload, with the local shoulder normal mask. The eight close-ups per view sample the beginning, middle and end. This does not establish acceptance of the full routine.</p>'
html+=f'<video style="max-width:800px" controls loop muted playsinline preload="metadata" src="{movie.name}"></video>'
for name in images:html+=f'<p><a href="{name}"><img style="width:100%" src="{name}" alt="Native shoulder views"></a></p>'
page.write_text(html,encoding='utf-8')
receipt={'movie':str(movie),'sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'decoded_frames':len(rows),
    'images':images,'page':str(page),'action_sha256':capture['action_sha256'],
    'scope':'Private saved native bridge; original clips, complete routine, other joints and owner acceptance remain separate.'}
(out/'Media.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
