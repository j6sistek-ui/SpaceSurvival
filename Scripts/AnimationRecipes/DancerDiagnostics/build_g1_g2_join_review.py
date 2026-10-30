"""Encode/decode the saved join review; keep native acceptance separate."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

project=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()
source=project/'SourceAssets/DanceRefinement_20261025'
review=project/'.agent/local/AnimationReview_20261025/G1G2JoinMotion'
record=json.loads((review/'Motion.json').read_text())
ffmpeg=Path('C:/Program Files/Lian-Li/L-Connect 3/x64/ffmpeg.exe')
assert ffmpeg.is_file()
videos=[]
for view in record['views']:
    files=sorted((review/view).glob('*.png'))
    assert len(files)==record['frames_per_view']==193
    movie=source/f'G1G2_Join_{view}.mp4'
    assert not movie.exists(),'Preserve previous encoded evidence'
    command=[str(ffmpeg),'-nostdin','-v','warning','-framerate','24','-i',str(review/view/'%04d.png'),
             '-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p','-movflags','+faststart',str(movie)]
    run=subprocess.run(command,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    (review/f'Encode_{view}.log').write_bytes(run.stderr);assert run.returncode==0
    decode=subprocess.run([str(ffmpeg),'-nostdin','-v','error','-i',str(movie),'-map','0:v:0','-f','framemd5','-'],
                          capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    decoded=[line for line in decode.stdout.splitlines() if line and not line.startswith(b'#')]
    assert decode.returncode==0 and len(decoded)==193
    (review/f'Decode_{view}.framemd5').write_bytes(decode.stdout)
    videos.append({'view':view,'file':movie.name,'sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'decoded_frames':len(decoded)})
frames=[0,47,48,72,96,120,143,144,192]
for view in record['views']:
    sheet=Image.new('RGB',(1200,1260),(28,35,41));draw=ImageDraw.Draw(sheet)
    for i,frame in enumerate(frames):
        with Image.open(review/view/f'{frame:04d}.png') as picture:sheet.paste(picture.resize((400,400)),((i%3)*400,(i//3)*420))
        draw.text(((i%3)*400+8,(i//3)*420+401),f'{view}: {frame/24:.3f}s',fill='white')
    sheet.save(review/f'{view}_overview.jpg',quality=93)
html='''<!doctype html><meta charset="utf-8"><title>Vexa — G1 to G2 transition</title>
<style>body{background:#111a21;color:#eaf1f6;font:18px system-ui;margin:32px auto;max-width:1200px}p{max-width:850px;line-height:1.5}section{display:flex;gap:20px;flex-wrap:wrap}article{flex:1;min-width:300px}video{width:100%;border-radius:12px}a{color:#81d8f0}small{color:#b1c1cc}</style>
<h1>Vexa · G1 → G2</h1><p>Two seconds of G1, a four-second floating transition, then two seconds of G2. The orange pole makes clearance visible. Each view uses the same saved animation and a fixed camera.</p>
<p><small>Private Blender Workbench preview. The selected Unreal shoulder-normal treatment is not shown here. This transition has not yet been imported or accepted in game. The original G1 and G2 clips remain unchanged.</small></p><section>'''
for row in videos:
    html+=f'<article><h2>{row["view"].title()}</h2><video controls loop muted playsinline preload="metadata" src="{row["file"]}"></video></article>'
html+='</section><p><a href="G1ShoulderReview.html">Shoulder repair and Unreal comparison</a></p>'
page=source/'G1G2JoinReview.html';assert not page.exists();page.write_text(html,encoding='utf-8')
receipt={'source':record,'videos':videos,'page':str(page),'scope':'Fully decoded source review; native transfer and full routine acceptance remain open.'}
(review/'Delivery.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({'page':str(page),'videos':videos},indent=2))
