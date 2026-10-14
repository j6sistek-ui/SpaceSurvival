"""Original deterministic wardrobe screen; factual text, no character artwork."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1024, 768
BG, INK, ACCENT = '#08131f', '#e6f3fa', '#70dae8'

def main():
    image = Image.new('RGB', (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
           f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>']
    for y, text, size, color in ((88,'WAYFARER / CREW SERVICES',30,ACCENT),
                                (212,'CREW',88,INK),(319,'WARDROBE',88,INK),
                                (495,'CHOOSE YOUR CHARACTER',44,INK),
                                (630,'INTERACT TO OPEN',48,ACCENT)):
        font = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', size)
        width = draw.textlength(text,font=font)
        assert width < WIDTH-128, text
        x = (WIDTH-width)/2
        draw.text((x,y),text,font=font,fill=color,anchor='ls')
        svg.append(f'<text x="{x}" y="{y}" font-family="Segoe UI" font-size="{size}" font-weight="700" fill="{color}">{text}</text>')
    for y in (380,690):
        draw.line((90,y,934,y),fill=ACCENT,width=3)
        svg.append(f'<path d="M90 {y}H934" stroke="{ACCENT}" stroke-width="3"/>')
    svg.append('</svg>')
    (ROOT/'Wardrobe.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8',newline='\n')
    image.save(ROOT/'Wardrobe.png')
    (ROOT/'manifest.json').write_text(json.dumps({'size':[WIDTH,HEIGHT],
        'sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                  for name in ('Wardrobe.svg','Wardrobe.png')}},indent=2)+'\n',encoding='utf-8',newline='\n')

if __name__ == '__main__':
    main()
