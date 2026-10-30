"""Encode the source-library review with explicit playback speed and hashes."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
ffmpeg = 'C:/Program Files/Lian-Li/L-Connect 3/x64/ffmpeg.exe'
rows = []
for receipt in sorted(args.root.glob('*/Review.json')):
    data = json.loads(receipt.read_text())
    for view in data['views']:
        name = receipt.parent.name+'_'+view
        frames = sorted((receipt.parent/view).glob('*.png'))
        assert len(frames) == data['frames_per_view']
        movie = args.output/(name+'.mp4')
        assert not movie.exists(), 'Preserve existing review'
        subprocess.run([ffmpeg,'-nostdin','-v','error','-framerate',str(data['fps']),
                        '-i',str(receipt.parent/view/'%04d.png'),'-c:v','libx264',
                        '-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(movie)],check=True)
        decoded = receipt.parent/(view+'_Decode.framemd5')
        subprocess.run([ffmpeg,'-nostdin','-v','error','-i',str(movie),'-f','framemd5',str(decoded)],check=True)
        count = sum(bool(s.strip()) and not s.startswith('#') for s in decoded.read_text().splitlines())
        assert count == len(frames)
        sheet = Image.new('RGB',(1600,420),(25,30,35)); draw = ImageDraw.Draw(sheet)
        for i in range(8):
            index = round((len(frames)-1)*i/7)
            with Image.open(frames[index]) as picture:
                sheet.paste(picture.resize((200,200)),(i*200,20))
            draw.text((i*200+5,4),f'{index/(data["fps"]*data["slow_factor"]):.2f}s source',fill='white')
        draw.text((10,235),f'{receipt.parent.name}: original source mesh/motion; {data["slow_factor"]:.1f}x duration. No adaptation or adoption.',fill='white')
        sheet = sheet.crop((0,0,1600,265))
        sheet.save(args.output/(name+'.jpg'),quality=94)
        rows.append({'clip':receipt.parent.name,'view':view,'movie':movie.name,
                     'sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),
                     'decoded_frames':count,'source_seconds':data['source_seconds'],
                     'slow_factor':data['slow_factor'],'sources':data['sources']})
assert rows, 'No complete reviews'
sections = ''.join(f'<section><h2>{r["clip"]} — {r["view"]}</h2><p>{r["source_seconds"]:.3f}s source, {r["slow_factor"]:.1f}x duration.</p><video controls preload="metadata" src="{r["movie"]}"></video></section>' for r in rows)
(args.output/'Review.html').write_text('<!doctype html><meta charset="utf-8"><title>Original library motion</title><style>body{background:#17202a;color:#eee;font:18px system-ui;margin:24px}main{display:grid;grid-template-columns:repeat(2,minmax(280px,1fr));gap:20px}video{width:100%}</style><h1>Original library motion — selection study</h1><p>These retain original whole-body choreography on the source mesh. Slower playback helps inspect rotation and leg phrasing; floating adaptation and character fit remain pending.</p><main>'+sections+'</main>',encoding='utf-8')
(args.root/'Media.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('LIBRARY_MEDIA',[(r['movie'],r['decoded_frames']) for r in rows])
