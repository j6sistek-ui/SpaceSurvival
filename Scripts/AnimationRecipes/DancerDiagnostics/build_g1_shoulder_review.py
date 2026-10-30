"""Encode verified private captures and build a local, plainly labelled review."""
import hashlib
import html
import json
import os
import re
import subprocess
from pathlib import Path

project = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home()/'SpaceSurvival'))).resolve()
review = project/'.agent/local/AnimationReview_20261025/G1ShoulderCapNative240'
source = project/'SourceAssets/DanceRefinement_20261025'
ffmpeg = Path(os.environ.get('SS_FFMPEG', 'C:/Program Files/Lian-Li/L-Connect 3/x64/ffmpeg.exe'))
assert ffmpeg.is_file()
parity = json.loads((review/'NativeParity.json').read_text())
assert parity['ok']
videos = []
for receipt_name, folder, name in (
    ('NativeCapture.json', 'NativeViews', 'G1_Shoulder_Native_Body.mp4'),
    ('NativeShoulderMotion.json', 'NativeShoulderMotion', 'G1_Shoulder_Native_Close.mp4'),
):
    receipt = json.loads((review/receipt_name).read_text())
    assert receipt['ok'] and receipt['local_normal_mask'] and receipt['native_inputs_unchanged']
    output = review/name
    assert not output.exists(), 'Preserve earlier encoded evidence'
    frames = sorted((review/folder).glob('loop_*.png'))
    assert len(frames) == receipt['frames'] == 660
    assert [p.name for p in frames] == [f'loop_{i:04d}.png' for i in range(660)]
    command = [str(ffmpeg), '-hide_banner', '-loglevel', 'warning', '-framerate', '24', '-i',
        str(review/folder/'loop_%04d.png'), '-an', '-c:v', 'libx264', '-crf', '19',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output)]
    result = subprocess.run(command, capture_output=True, text=True)
    (review/(name+'.encode.log')).write_text(result.stderr)
    assert result.returncode == 0, result.stderr[-1500:]
    encode_warnings = result.stderr
    result = subprocess.run([str(ffmpeg), '-hide_banner', '-loglevel', 'warning', '-i', str(output),
        '-progress', 'pipe:1', '-nostats', '-f', 'null', '-'], capture_output=True, text=True)
    (review/(name+'.decode.log')).write_text(result.stdout+'\n'+result.stderr)
    decoded = [int(n) for n in re.findall(r'^frame=(\d+)', result.stdout, re.M)]
    assert result.returncode == 0 and decoded[-1] == len(frames), result.stderr
    videos.append({'path': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                   'decoded_frames': decoded[-1], 'encode_warnings': encode_warnings,
                   'decode_warnings': result.stderr})

def uri(path):
    return html.escape(Path(path).as_uri(), quote=True)

normal = review/'NativeLocalNormalControl'
options = {label: {view: {mode: uri(normal/f'{stamp}_{view}_{mode}.png') for mode in ('skinned','recomputed')}
                  for view in ('front','side','back')}
           for label, stamp in (('Forward reach','t03000'), ('Shoulder cap','t07255'), ('Later reach','t08417'))}
body_video, close_video = [uri(v['path']) for v in videos]
document = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vexa · shoulder motion review</title><style>
body{margin:0;background:#11151c;color:#e6edf6;font:16px/1.5 system-ui}main{max-width:1100px;margin:auto;padding:28px}
h1{font-size:30px;margin-bottom:8px}p{max-width:850px;color:#b7c4d6}section{margin:30px 0;border-top:1px solid #334052;padding-top:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px}video,img{width:100%;border-radius:8px;background:#000}
button,select{background:#24334a;color:#eef4ff;border:1px solid #536780;border-radius:6px;padding:9px;margin:0 7px 10px 0}button.active{background:#285d76}
small{color:#a6bacf}details{padding:14px;background:#18202c}code{overflow-wrap:anywhere}a{color:#84cff0}
</style><main><h1>Vexa · shoulder motion review</h1>
<p>The forward-reaching shoulder has a local shape correction and a local lighting correction. These captures use the saved private Unreal proof. Earlier raised-arm approvals remain limited to those poses.</p>
<section><h2>Full passage and shoulder close-up</h2><div class="grid">
<div><video controls preload="metadata" src="BODYVIDEO"></video><small>Whole-body view · 27.45-second G1 passage</small></div>
<div><video controls preload="metadata" src="CLOSEVIDEO"></video><small>Continuous front shoulder view · same saved action</small></div>
</div><p>This G1 passage has different start/end poses; it is not a finished loop. Complete hand, garment, other-joint and routine quality remain under review.</p></section>
<section><h2>Isolate the lighting correction</h2><p>Both sides below already contain the same shoulder shape correction. Toggle only the local normal treatment; geometry and animation stay the same.</p>
<select id="pose"><option>Forward reach</option><option>Shoulder cap</option><option>Later reach</option></select>
<select id="view"><option>front</option><option>side</option><option>back</option></select>
<button id="old">Original skinned normals</button><button id="new" class="active">Local recalculation</button>
<img id="comparison" alt="Same-pose native shoulder comparison"></section>
<details><summary>Evidence and limits</summary><p>Source: <code>51c25e24</code>; G1 action: <code>cc652d79</code>; local-normal mesh: <code>e434f671</code>. Eight native pose comparisons passed: BONEMM mm maximum bone difference and SURFACEMM mm visible-surface difference. Both videos decode all 660 frames.</p>
<p>Private CharacterWorkbench map: <code>/Game/SpaceSurvival/Licensed/VexaG1ShoulderCap240Proof_20261026/L_G1ShoulderCap240_Review</code>. No production character, game binary, save or package changed. No full-rig or owner acceptance is implied.</p></details>
<script>const data=OPTIONS;let mode='recomputed';const pose=document.querySelector('#pose'),view=document.querySelector('#view');function update(){document.querySelector('#comparison').src=data[pose.value][view.value][mode];document.querySelector('#old').className=mode==='skinned'?'active':'';document.querySelector('#new').className=mode==='recomputed'?'active':'';}pose.onchange=view.onchange=update;document.querySelector('#old').onclick=()=>{mode='skinned';update()};document.querySelector('#new').onclick=()=>{mode='recomputed';update()};update();</script></main></html>'''
document = document.replace('BODYVIDEO', body_video).replace('CLOSEVIDEO', close_video).replace('OPTIONS', json.dumps(options))
document = document.replace('BONEMM', f"{parity['max_bone_error_mm']:.3f}").replace('SURFACEMM', f"{parity['max_surface_error_mm']:.3f}")
page = source/'G1ShoulderReview.html'
assert not page.exists(), 'Preserve prior owner review'
page.write_text(document, encoding='utf-8')
(review/'Media.json').write_text(json.dumps({'ok': True, 'videos': videos, 'page': str(page),
    'page_sha256': hashlib.sha256(page.read_bytes()).hexdigest()}, indent=2))
print('G1_SHOULDER_MEDIA_DONE', page, flush=True)
