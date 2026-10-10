"""Original factual reception display, deterministic PNG and editable SVG."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent

def main():
    width,height=1024,768
    bg,ink,accent='#101820','#f2eee3','#dfb778'
    image=Image.new('RGB',(width,height),bg);draw=ImageDraw.Draw(image)
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         f'<rect width="{width}" height="{height}" fill="{bg}"/>']
    rows=((88,'WAYFARER EXCHANGE',38,accent),(226,'WELCOME',92,ink),
          (337,'ABOARD',92,ink),(482,'RECEPTION / INFORMATION',40,ink),
          (590,'Speak with our reception staff',36,ink),(685,'FIND YOUR NEXT STOP',34,accent))
    for y,text,size,color in rows:
        font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',size)
        length=draw.textlength(text,font=font);assert length<width-128
        x=(width-length)/2
        draw.text((x,y),text,font=font,fill=color,anchor='ls')
        svg.append(f'<text x="{x}" y="{y}" font-family="Segoe UI" font-size="{size}" font-weight="700" fill="{color}">{text}</text>')
    for y in (135,397,727):
        draw.line((80,y,944,y),fill=accent,width=3)
        svg.append(f'<path d="M80 {y}H944" stroke="{accent}" stroke-width="3"/>')
    svg.append('</svg>')
    (ROOT/'CheckIn.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8',newline='\n')
    image.save(ROOT/'CheckIn.png')
    (ROOT/'manifest.json').write_text(json.dumps({'size':[width,height],'purpose':'Reception information; no new check-in mechanic',
        'sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('CheckIn.svg','CheckIn.png')}},indent=2)+'\n',encoding='utf-8',newline='\n')

if __name__=='__main__':main()
