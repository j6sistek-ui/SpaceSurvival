"""Deterministic SVG typography and matching CPU previews; no game asset writes."""
import hashlib
import html
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1960, 1000
FONTS = {'regular': Path('C:/Windows/Fonts/segoeui.ttf'),
         'bold': Path('C:/Windows/Fonts/segoeuib.ttf')}
BG, PANEL, LINE = '#08131f', '#132435', '#344b60'
WHITE, BODY, CYAN, GOLD = '#f2f7fc', '#d8e5f0', '#70dae8', '#f2c884'


class Board:
    def __init__(self, title, subtitle, number):
        self.image = Image.new('RGB', (WIDTH, HEIGHT), BG)
        self.draw = ImageDraw.Draw(self.image)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
                    f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{html.escape(title)}">',
                    f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>']
        self.rect((80, 64, 112, 72), CYAN)
        self.text((80, 97), 'WAYFARER / VISITOR GUIDE', 27, CYAN, 'bold')
        self.text((80, 175), title, 66, WHITE, 'bold')
        self.text((80, 227), subtitle, 31, BODY)
        self.text((1765, 97), number, 27, CYAN, 'bold', 115)

    def rect(self, box, fill, radius=0, stroke=None, thickness=2):
        x0, y0, x1, y1 = box
        self.draw.rounded_rectangle(box, radius, fill=fill, outline=stroke, width=thickness)
        self.svg.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" '
                        f'rx="{radius}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="{thickness}"/>')

    def line(self, points, color=CYAN, thickness=4):
        self.draw.line(points, fill=color, width=thickness, joint='curve')
        value = ' '.join(f'{x},{y}' for x, y in points)
        self.svg.append(f'<polyline points="{value}" fill="none" stroke="{color}" '
                        f'stroke-width="{thickness}" stroke-linejoin="round" stroke-linecap="round"/>')

    def circle(self, center, radius, color=CYAN, thickness=4):
        x, y = center
        self.draw.ellipse((x-radius, y-radius, x+radius, y+radius), outline=color, width=thickness)
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="none" '
                        f'stroke="{color}" stroke-width="{thickness}"/>')

    def text(self, position, value, size, color=BODY, weight='regular', max_width=1740):
        font = ImageFont.truetype(str(FONTS[weight]), size)
        width = self.draw.textlength(value, font=font)
        if width > max_width:
            raise ValueError('Text exceeds its layout: ' + value)
        self.draw.text(position, value, font=font, fill=color, anchor='ls')
        self.svg.append(f'<text x="{position[0]}" y="{position[1]}" font-family="Segoe UI" '
                        f'font-size="{size}" font-weight="{700 if weight == "bold" else 400}" '
                        f'fill="{color}">{html.escape(value)}</text>')

    def card(self, x, y, heading, lines, icon):
        self.rect((x, y, x+870, y+268), PANEL, 18, LINE)
        self.rect((x+26, y+27, x+104, y+105), BG, 14)
        if isinstance(icon, int):
            self.text((x+47, y+83), str(icon), 43, CYAN, 'bold', 60)
        else:
            icon(self, x+36, y+39)
        self.text((x+127, y+86), heading, 44, WHITE, 'bold', 715)
        for i, value in enumerate(lines):
            self.text((x+32, y+151+i*42), value, 32, BODY, max_width=806)

    def save(self, name, footer):
        self.rect((80, 883, 1880, 925), BG)
        self.line([(80, 876), (1880, 876)], LINE, 2)
        self.text((80, 930), footer, 30, GOLD, max_width=1800)
        self.svg.append('</svg>')
        svg = HERE / (name+'.svg')
        png = HERE / (name+'.png')
        svg.write_text('\n'.join(self.svg)+'\n', encoding='utf-8')
        self.image.save(png)
        return {'id': name, 'svg': svg.name, 'png': png.name, 'size': [WIDTH, HEIGHT],
                'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (svg, png)}}


def operations(b, x, y):
    b.rect((x+4, y+7, x+56, y+43), BG, 4, CYAN, 4)
    b.line([(x+19,y+53),(x+41,y+53),(x+36,y+44)], CYAN, 4)
    b.line([(x+15,y+21),(x+25,y+21),(x+25,y+14),(x+34,y+14),(x+34,y+32),(x+46,y+32)], CYAN, 4)


def character(b, x, y):
    b.circle((x+30,y+15), 12)
    b.line([(x+9,y+55),(x+9,y+48),(x+18,y+35),(x+42,y+35),(x+51,y+48),(x+51,y+55)])


def social(b, x, y):
    b.line([(x+8,y+17),(x+43,y+17),(x+43,y+48),(x+8,y+48),(x+8,y+17)])
    b.line([(x+43,y+22),(x+56,y+22),(x+56,y+37),(x+43,y+37)])
    b.line([(x+4,y+55),(x+48,y+55)])


def berths(b, x, y):
    b.line([(x+30,y+4),(x+53,y+37),(x+37,y+33),(x+37,y+52),
            (x+23,y+52),(x+23,y+33),(x+7,y+37),(x+30,y+4)])
    b.circle((x+30,y+23), 5, CYAN, 3)
    b.line([(x+26,y+55),(x+26,y+60)], CYAN, 3)
    b.line([(x+34,y+55),(x+34,y+60)], CYAN, 3)


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    directory = Board('FIND YOUR NEXT STOP', 'Choose a destination. Follow the existing room signs.', '01 / 02')
    directory.card(80, 290, 'OPERATIONS', ['Choose ships & weapons at home.',
        'Upgrades & contracts at Survival stops.', 'Check your pilot record.'], operations)
    directory.card(1010, 290, 'CREW ARCHIVE', ['Choose your character', 'at Crew Wardrobe.'], character)
    directory.card(80, 580, 'SOCIAL LOUNGE', ['Visit the bar, booths & arcade.'], social)
    directory.card(1010, 580, 'MARKET & BERTHS', ['Back along the arrival concourse.'], berths)
    rows = [directory.save('01_StationDirectory', 'HOME / THROUGH THE LOWER PASSAGE')]
    flight = Board('YOUR NEXT FLIGHT', 'The cockpit chair is your departure point.', '02 / 02')
    flight.card(80, 290, 'AT HOME', ['Choose Waves or Free Flight', 'at the Phoenix cockpit chair.', 'Sit to depart.'], 1)
    flight.card(1010, 290, 'AT A SURVIVAL STOP', ['Sit in the cockpit chair', 'to continue your current run.'], 2)
    flight.card(80, 580, 'RETURNING', ['Follow LANDING PAD. Brake.', 'Interact when docking is ready.'], 3)
    flight.card(1010, 580, 'SAVED RUN', ['Choose Continue saved Survival', 'in Flight Briefing.'], 4)
    rows.append(flight.save('02_FlightGuide', 'FREE FLIGHT / AVAILABLE AT HOME / SURVIVAL PROGRESS PROTECTED'))
    manifest = {'status': 'DETERMINISTIC SOURCE ART; NATIVE ACCEPTANCE RECORDED SEPARATELY',
                'source_aspect': WIDTH/HEIGHT,
                'fonts': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in FONTS.values()},
                'provenance': 'PROVENANCE.md', 'boards': rows,
                'native_assets': {
                    'housing': '/Game/SciFiCorridor/Meshes/SM_Monitor',
                    'screen': '/Game/SciFiCorridor/Meshes/SM_MonitorScreen',
                    'housing_material': '/Game/SciFiCorridor/Materials/MI_Assets',
                    'private_root': '/Game/OutpostSandbox/StationRefinement/CentralInformationBoards20261007'},
                'limits': ['No directional arrows are universal to both mounted walls.',
                           'Source format and copy do not establish mounted brightness or owner acceptance.',
                           'No Unreal/native calls or private .uasset files are included.']}
    (HERE/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print('Composed two SVG sources and matching typography previews.')


if __name__ == '__main__':
    main()
