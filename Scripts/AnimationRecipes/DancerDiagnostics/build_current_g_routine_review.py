"""Assemble current native G1/bridge/G2 captures at their recorded speed.

This is a review edit with camera cuts, not a live LevelSequence integration.
Never substitute a new movement experiment for one of these guarded inputs.
"""
import hashlib
import html
import json
import os
import subprocess
import sys
from pathlib import Path

project = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home()/'SpaceSurvival'))).resolve()
source = project/'SourceAssets/DanceRefinement_20261025'
review = project/'.agent/local/AnimationReview_20261025'
legs = '--legs' in sys.argv
output = review/('CurrentGFullLegReview' if legs else 'CurrentGFullReview')
output.mkdir(exist_ok=True)
video = source/('G1G2_Current_LegPass_Unreal.mp4' if legs else 'G1G2_Current_Full_Unreal.mp4')
assert not video.exists(), 'Preserve the prior full review'
inputs = [review/'G1ShoulderCapNative240/G1_Shoulder_Native_Body.mp4',
          source/'G1G2_Join_Unreal.mp4', review/'G2PalmarNative240/G2_PalmarGrip_Unreal.mp4']
if legs:
    leg_media = json.loads((review/'G2FloatingPhraseNative240/Media.json').read_text())
    inputs[2] = Path(leg_media['movie'])
    assert hashlib.sha256(inputs[2].read_bytes()).hexdigest() == leg_media['sha256']
    assert leg_media['decoded_frames'] == 1229
hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
ffmpeg = os.environ.get('SS_FFMPEG', 'C:/Program Files/Lian-Li/L-Connect 3/x64/ffmpeg.exe')
arguments = [ffmpeg, '-hide_banner', '-nostdin', '-n']
for path in inputs: arguments += ['-i', str(path)]
filters = ';'.join(f'[{i}:v]fps=24,scale=800:800,setsar=1,setpts=PTS-STARTPTS[v{i}]' for i in range(3))
filters += ';[v0][v1][v2]concat=n=3:v=1:a=0[out]'
arguments += ['-filter_complex', filters, '-map', '[out]', '-r', '24', '-fps_mode', 'cfr', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
              '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(video)]
with (output/'Encode.log').open('w', encoding='utf-8') as log:
    subprocess.run(arguments, stdout=log, stderr=subprocess.STDOUT, check=True)
with (output/'Decode.log').open('w', encoding='utf-8') as log:
    subprocess.run([ffmpeg,'-hide_banner','-nostdin','-i',str(video),'-an','-f','framemd5',str(output/'FullDecode.framemd5')], stdout=log, stderr=subprocess.STDOUT, check=True)
frames = sum(1 for line in (output/'FullDecode.framemd5').read_text().splitlines() if line and not line.startswith('#'))
assert frames == 660+97+1229, frames
assert hashes == {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
manifest = {'sources':hashes,'file':video.name,'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
            'fps':24,'frames':frames,'seconds':frames/24,'clip_start_seconds':[0,660/24,(660+97)/24],
            'order':['G1 cc652d79','4s bridge 6172cbde','G2 409a79ad'],
            'scope':'Three current native private proof captures concatenated without retiming. Two camera cuts; not live sequence playback, not a closed routine loop. New floating-leg overlap experiment excluded.'}
if legs:
    manifest['order'][2] = 'G2 leg phrase 173a6223'
    manifest['scope'] = 'Three private native captures including the verified leg candidate. Two camera cuts; not live sequence playback, not a closed routine or full original G1/G2 coverage.'
(output/'Delivery.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
page = source/('CurrentGLegReview.html' if legs else 'CurrentGRoutineReview.html')
page.write_text('''<!doctype html><html><meta charset="utf-8"><title>Current G1 + G2 routine</title>
<style>body{margin:24px auto;max-width:1000px;background:#151b21;color:#edf3f6;font:18px system-ui}video{width:100%;max-height:82vh;background:#000}button{padding:12px;margin:8px;cursor:pointer}p{line-height:1.5}small{color:#bac7d2}</style>
<h1>Current G1 → transition → G2</h1><p>Full motion at normal speed · 82.75 seconds · Unreal captures.</p>
<video id="routine" controls playsinline preload="metadata" src="G1G2_Current_Full_Unreal.mp4"></video>
<div><button onclick="routine.currentTime=0;routine.play()">G1 · 0:00</button><button onclick="routine.currentTime=27.5;routine.play()">Transition · 0:27.5</button><button onclick="routine.currentTime=31.541667;routine.play()">G2 · 0:31.5</button><button onclick="routine.playbackRate=1">Normal speed</button><button onclick="routine.playbackRate=.5">Half speed</button></div>
<p><small>These are the current private Unreal proof captures assembled in order; the camera resets at each section boundary. This is not a live integrated sequence or a completed loop. The new subtle leg-follow-through test is not included yet. Original timing is preserved.</small></p>
<p><a style="color:#7de0ef" href="G1G2JoinReview.html">Transition details</a> · <a style="color:#7de0ef" href="G1ShoulderReview.html">Shoulder review</a></p></html>''',encoding='utf-8')
if legs:
    page.write_text(page.read_text(encoding='utf-8').replace('G1G2_Current_Full_Unreal.mp4', video.name).replace(
        'The new subtle leg-follow-through test is not included yet. Original timing is preserved.',
        'Includes the G2 alternating leg phrase. Timing remains the long diagnostic timing; choreography is still open. Only selected original passages are present.'), encoding='utf-8')
print(json.dumps(manifest,indent=2))
