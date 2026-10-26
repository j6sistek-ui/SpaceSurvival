"""Encode opposing source leg-phrase views and retain complete-decode receipts."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

project = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home() / 'SpaceSurvival'))).resolve()
source_legs = '--source-legs' in sys.argv
diagnostic = '--diagnostic' in sys.argv
assert not diagnostic or source_legs
root = project / '.agent/local/AnimationReview_20261025/G2FloatingLife' / ('SourceLegControl' if source_legs else 'PhraseControl')
audit_root = root
framed = '--framed' in sys.argv
if framed:
    root = root / ('DiagnosticFramed' if diagnostic else 'Framed')
source = project / 'SourceAssets/DanceRefinement_20261025'
ffmpeg = Path('C:/Program Files/Lian-Li/L-Connect 3/x64/ffmpeg.exe')
if '--native' in sys.argv:
    assert not source_legs and not diagnostic, 'No native proof for this source-only experiment'
    native = project / '.agent/local/AnimationReview_20261025/G2FloatingPhraseNative240'
    capture = json.loads((native / 'NativeCapture.json').read_text())
    parity = json.loads((native / 'NativeParity.json').read_text())
    assert capture['ok'] and parity['ok'] and capture['action_sha256'] == parity['action_sha256']
    frames = sorted((native / 'NativeViews').glob('loop_*.png'))
    assert len(frames) == capture['frames']
    movie = source / 'G2_LegPhrase_Unreal.mp4'
    assert not movie.exists(), 'Preserve prior native media'
    with (native / 'Encode.log').open('w') as log:
        subprocess.run([str(ffmpeg), '-nostdin', '-v', 'warning', '-framerate', '24',
            '-i', str(native / 'NativeViews/loop_%04d.png'), '-c:v', 'libx264', '-crf', '18',
            '-preset', 'medium', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(movie)],
            stdout=log, stderr=log, check=True)
    decoded = native / 'Decode.framemd5'
    subprocess.run([str(ffmpeg), '-nostdin', '-v', 'error', '-i', str(movie), '-f', 'framemd5', str(decoded)], check=True)
    count = sum(bool(line.strip()) and not line.startswith('#') for line in decoded.read_text().splitlines())
    assert count == len(frames)
    for view in ('front', 'back', 'side'):
        shots = [r for r in capture['captures'] if r['kind'] == 'still' and r['view'] == view]
        assert len(shots) == 8
        sheet = Image.new('RGB', (1600, 840), (25, 30, 35)); draw = ImageDraw.Draw(sheet)
        for i, row in enumerate(shots):
            with Image.open(row['path']) as picture:
                sheet.paste(picture.resize((400, 400)), ((i % 4) * 400, (i // 4) * 420))
            draw.text(((i % 4) * 400 + 8, (i // 4) * 420 + 402), f'{view} {row["seconds"]:.2f}s', fill='white')
        sheet.save(source / f'G2_LegPhrase_Unreal_{view}.jpg', quality=94)
    page = source / 'G2LegPhraseReview.html'
    html = page.read_text(encoding='utf-8')
    assert '<h2>Full Unreal leg pass</h2>' not in html
    html += '<h2>Full Unreal leg pass</h2><p>Full51.167-second G2 candidate after a fresh private native reload. Framing follows the whole body. This is not production or owner acceptance.</p><video style="max-width:800px" controls preload="metadata" src="G2_LegPhrase_Unreal.mp4"></video>'
    page.write_text(html, encoding='utf-8')
    report = {'action_sha256': capture['action_sha256'], 'movie': str(movie), 'decoded_frames': count,
              'sha256': hashlib.sha256(movie.read_bytes()).hexdigest(), 'fps': 24,
              'scope': 'Fully decoded private native motion; selected opposing views require inspection, owner review remains pending.'}
    (native / 'Media.json').write_text(json.dumps(report, indent=2))
    print('FLOATING_NATIVE_MEDIA', report)
    raise SystemExit(0)
motion = json.loads((root / 'Motion.json').read_text())
audit = json.loads((audit_root / 'Audit.json').read_text())
assert (audit['passed'] or diagnostic) and audit['control_sha256'] == motion['control_sha256']
assert not diagnostic or motion['diagnostic_only'], 'Do not relabel a failed render as a normal review'
prefix = 'G2_SourceLegs_Diagnostic' if source_legs else 'G2_LegPhrase'
rows = []
for view in motion['views']:
    for label, start, end in motion['clips']:
        folder = root / f'{view}_{label}'
        frames = sorted(folder.glob('*.png'))
        assert len(frames) == round((end - start) * motion['fps']) + 1
        destination = source / f'{prefix}_{view}_{label}{"_Framed" if framed else ""}.mp4'
        assert not destination.exists(), 'Preserve earlier review'
        with (root / f'{view}_{label}_Encode.log').open('w') as log:
            subprocess.run([str(ffmpeg), '-nostdin', '-v', 'warning', '-framerate', str(motion['fps']),
                '-i', str(folder / '%04d.png'), '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(destination)], stdout=log, stderr=log, check=True)
        decode = root / f'{view}_{label}_Decode.framemd5'
        subprocess.run([str(ffmpeg), '-nostdin', '-v', 'error', '-i', str(destination), '-f', 'framemd5', str(decode)], check=True)
        decoded = sum(bool(line.strip()) and not line.startswith('#') for line in decode.read_text().splitlines())
        assert decoded == len(frames)
        rows.append({'view': view, 'clip': label, 'file': destination.name, 'frames': decoded,
                     'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()})
        sheet = Image.new('RGB', (1500, 320), (25, 30, 35))
        draw = ImageDraw.Draw(sheet)
        for col, fraction in enumerate((0., .25, .5, .75, 1.)):
            index = round((len(frames) - 1) * fraction)
            image = Image.open(frames[index]); image.thumbnail((300, 300))
            sheet.paste(image, (col * 300, 20))
            draw.text((col * 300 + 8, 4), f'{view} {label} {start + index / motion["fps"]:.2f}s', fill='white')
        sheet.save(destination.with_suffix('.jpg'))
body = ''.join(f'<section><h2>{r["view"]} — {r["clip"]}</h2><video controls preload="metadata" src="{r["file"]}"></video></section>' for r in rows)
html = '<!doctype html><meta charset="utf-8"><title>G2 leg phrasing</title><style>body{background:#17202a;color:#eee;font:18px system-ui;margin:32px}main{display:grid;grid-template-columns:repeat(2,minmax(300px,1fr));gap:24px}video{width:100%}a{color:#79d5ef}</style><h1>G2 leg phrasing — private source review</h1><p>Normal-speed opposing views. Alternating knee draw and extension on previously held passages. Original grip, shoulders and clip endpoints retained. This is Blender source rendering, not game acceptance.</p><p><a href="CurrentGRoutineReview.html">Earlier full native G1 / bridge / G2 review</a> (does not contain this leg pass).</p><main>' + body + '</main>'
if source_legs:
    html = html.replace('Alternating knee draw and extension on previously held passages.',
        f'Original G1 leg phrases transferred into the held passages. DIAGNOSTIC ONLY: contact checks fail in {len(audit["flags"])} sampled frames. These moves are retained for repair, not accepted for production.')
    html = html.replace('<title>G2 leg phrasing</title>', '<title>G1 source legs on G2 — contact repair pending</title>')
(source / ('G2SourceLegReview.html' if source_legs else 'G2LegPhraseReview.html')).write_text(html, encoding='utf-8')
(root / 'Delivery.json').write_text(json.dumps({'control_sha256': motion['control_sha256'], 'fps': motion['fps'], 'videos': rows,
    'audit_passed':audit['passed'],'diagnostic_only':diagnostic,
    'scope': 'Every encoded frame decoded; selected opposing samples inspected separately. No owner acceptance.'}, indent=2))
print('FLOATING_VIDEOS', [(r['file'], r['frames']) for r in rows])
