"""Timing-only video comparison; never changes the underlying rig or action.

Smoothly compress four identified held passages. Preserve every input pose
frame by presenting at 60 Hz; repeated frames are not newly evaluated poses.
This is an editorial preview, not continuous-motion or contact validation.
"""
import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np


project = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home() / 'SpaceSurvival'))).resolve()
source = project / 'SourceAssets/DanceRefinement_20261025'
review = project / '.agent/local/AnimationReview_20261025'
original = source / 'G1G2_Current_LegPass_Unreal.mp4'
expected = 'aad072adbe63fa501139e17dbf27db1e3e0490128e6c29bf48ea45cc41a92d9b'
assert hashlib.sha256(original.read_bytes()).hexdigest() == expected
delivery = json.loads((review / 'CurrentGFullLegReview/Delivery.json').read_text())
assert delivery['frames'] == 1986 and delivery['fps'] == 24 and delivery['sha256'] == expected
out = review / 'CurrentGTimingComparison'
out.mkdir(exist_ok=True)
receipt = out / 'Timing.json'
movie = source / 'G1G2_Timing_Comparison.mp4'
assert not receipt.exists() and not movie.exists(), 'Preserve prior timing review'

# Source-time intervals, minimum destination-time scale and smooth ramp width.
# G1, bridge, supported excerpt and return blend are retained at their speed.
windows = [
    ('G2 approach', 31.5416666667, 38.2336909597, .45, .8),
    ('G2 release', 64.6191730868, 70.8654424687, .62, .8),
    ('Move away', 70.8654424687, 74.7197018523, .65, .65),
    ('Return approach', 78.8926115055, 82.75, .60, .7),
]
duration = delivery['frames'] / delivery['fps']
grid = np.linspace(0., duration, round(duration * 2400) + 1)
density = np.ones_like(grid)
for _, start, end, scale, ramp in windows:
    u = np.clip((grid - start) / ramp, 0., 1.)
    v = np.clip((end - grid) / ramp, 0., 1.)
    smooth_u = u * u * (3 - 2 * u)
    smooth_v = v * v * (3 - 2 * v)
    density -= (1. - scale) * smooth_u * smooth_v
assert density.min() >= .449999 and density.max() <= 1.
dest = np.r_[0., np.cumsum((density[:-1] + density[1:]) * .5 * np.diff(grid))]
fps = 60
output_times = np.arange(round(float(dest[-1]) * fps)) / fps
source_times = np.interp(output_times, dest, grid)
indices = np.clip(np.floor(source_times * 24 + .5).astype(int), 0, 1985)
assert np.all(np.diff(indices) >= 0)
assert np.array_equal(np.unique(indices), np.arange(1986)), 'Every original pose frame must be represented'

ffmpeg = os.environ.get('SS_FFMPEG', 'C:/Program Files/Lian-Li/L-Connect 3/x64/ffmpeg.exe')
frame_bytes = 800 * 800 * 3
decoded_count = 0
written = 0
with (out / 'DecodeSource.log').open('wb') as decoder_log, (out / 'Encode.log').open('wb') as encoder_log:
    decoder = subprocess.Popen([ffmpeg, '-hide_banner', '-nostdin', '-i', str(original),
                                '-an', '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'],
                               stdout=subprocess.PIPE, stderr=decoder_log)
    encoder = subprocess.Popen([ffmpeg, '-hide_banner', '-nostdin', '-n', '-f', 'rawvideo',
                                '-pix_fmt', 'rgb24', '-s', '800x800', '-r', str(fps), '-i', 'pipe:0',
                                '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                                '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(movie)],
                               stdin=subprocess.PIPE, stderr=encoder_log)
    try:
        for index in range(1986):
            chunks = bytearray()
            while len(chunks) < frame_bytes:
                chunk = decoder.stdout.read(frame_bytes - len(chunks))
                if not chunk:
                    break
                chunks.extend(chunk)
            assert len(chunks) == frame_bytes, ('Short input', index, len(chunks))
            decoded_count += 1
            while written < len(indices) and indices[written] == index:
                encoder.stdin.write(chunks)
                written += 1
        assert not decoder.stdout.read(1), 'Unexpected additional input frame'
        encoder.stdin.close()
        assert decoder.wait() == 0 and encoder.wait() == 0
    finally:
        for process in (decoder, encoder):
            if process.poll() is None:
                process.terminate()
                process.wait()
assert written == len(indices) and decoded_count == 1986
md5 = out / 'FullDecode.framemd5'
subprocess.run([ffmpeg, '-nostdin', '-v', 'error', '-i', str(movie), '-an', '-f', 'framemd5', str(md5)], check=True)
decoded_output = sum(bool(line) and not line.startswith('#') for line in md5.read_text().splitlines())
assert decoded_output == written
assert hashlib.sha256(original.read_bytes()).hexdigest() == expected
record = {
    'original_sha256': expected, 'original_frames': 1986, 'original_seconds': duration,
    'video': str(movie), 'sha256': hashlib.sha256(movie.read_bytes()).hexdigest(),
    'fps': fps, 'decoded_frames': decoded_output, 'seconds': decoded_output / fps,
    'all_original_pose_frames_retained': True, 'source_frame_for_output': indices.tolist(),
    'sections': [{'name': name, 'source_start': a, 'source_end': b,
                  'preview_start': float(np.interp(a, grid, dest)),
                  'preview_end': float(np.interp(b, grid, dest)),
                  'minimum_time_scale': scale, 'ramp_seconds': ramp}
                 for name, a, b, scale, ramp in windows],
    'scope': 'Timing-only video retime. All source pose frames retained, with repeats at 60 Hz; no new poses or action changes. Camera cuts retained. Not live playback, contact verification or new choreography.',
}
receipt.write_text(json.dumps(record, indent=2), encoding='utf-8')
(source / 'CurrentGTimingReview.html').write_text('''<!doctype html><meta charset="utf-8">
<title>Current routine: timing comparison</title><style>body{max-width:950px;margin:24px auto;background:#17202a;color:#eef3fa;font:18px system-ui;line-height:1.5;padding:0 16px}video{width:100%;max-height:75vh}a{color:#79dcee}button{padding:12px;margin:5px;font:inherit}</style>
<h1>Current routine — shorter waits</h1><p>The same moves and grip-release order. Only four held passages have faster timing; this does not restore the missing choreography yet.</p>
<video id="v" controls playsinline preload="metadata" src="G1G2_Timing_Comparison.mp4"></video>
<button onclick="v.src='G1G2_Timing_Comparison.mp4';v.play()">Timing comparison</button>
<button onclick="v.src='G1G2_Current_LegPass_Unreal.mp4';v.play()">Original timing</button>
<p>Video edit only. All original pose frames are retained and repeated as needed at 60 Hz. No rig/action changes; two camera cuts remain. This is not a completed loop or motion-quality approval.</p>
<p><a href="CurrentGLegReview.html">Original chapters and source coverage</a></p>''', encoding='utf-8')
print('TIMING_REVIEW', record['seconds'], decoded_output, record['sha256'], flush=True)
