"""Compose two static cabinet cards from existing owner art; no game wiring.

Uses the existing Pillow runtime. Originals and Frozen1 exports are read-only;
new cards, distance previews and a hashed provenance receipt go to a fresh folder.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
ART_ROOT = Path('C:/Users/j6sis/acornaut/tmp/zone-art-review')
OUTPUT = ROOT / '.agent/local/ArcadeGeneration/AttractCardsV2/approved_v2'
FONT = Path('C:/Windows/Fonts/bahnschrift.ttf')
SIZE = (1024, 768)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compose(source_root, output):
    output = output.resolve()
    allowed = (ROOT / '.agent/local/ArcadeGeneration').resolve()
    if not output.is_relative_to(allowed) or output == allowed:
        raise ValueError('Write only a new folder under the ignored ArcadeGeneration area')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Preserve existing cards/receipts: choose a fresh output folder')
    source_root = source_root.resolve()
    sources = {}

    def read(relative):
        path = source_root / relative
        sources[str(path)] = digest(path)
        return Image.open(path).convert('RGBA')

    def font(size):
        return ImageFont.truetype(str(FONT), size)

    def shade(image, left_max=135, bottom_max=140):
        # Protect typography without boxing the artwork into a portrait inset.
        mask = Image.new('RGBA', SIZE)
        pixels = mask.load()
        for y in range(SIZE[1]):
            bottom = bottom_max * max(0., (y-610)/158.)
            for x in range(SIZE[0]):
                left = left_max * max(0., 1.-x/650.)
                pixels[x, y] = (2, 7, 17, int(min(200., max(left, bottom))))
        return Image.alpha_composite(image, mask)

    def type_on(image, xy, text, size, color):
        draw = ImageDraw.Draw(image)
        draw.text(xy, text, font=font(size), fill=color, stroke_width=1,
                  stroke_fill=(1, 6, 14, 190))

    def frame(image, accent, number):
        draw = ImageDraw.Draw(image)
        draw.line((48, 52, 110, 52), fill=accent, width=5)
        draw.line((48, 52, 48, 85), fill=accent, width=5)
        draw.line((976, 716, 914, 716), fill=accent, width=4)
        draw.text((54, 685), 'WAYFARER ARCADE', font=font(19), fill=(203, 216, 224))
        draw.text((866, 684), number, font=font(20), fill=accent)

    # Full-height, right-anchored cover preserves the astronaut and planet arc.
    arcade_source = read('site-src/assets/bg-wide.jpg')
    arcade = ImageOps.fit(arcade_source, SIZE, Image.Resampling.LANCZOS, centering=(1., .5))
    arcade = shade(arcade, left_max=45)
    type_on(arcade, (54, 164), 'ACORNAUT', 37, (244, 232, 202))
    type_on(arcade, (46, 222), 'ARCADE', 142, (255, 205, 113))
    draw = ImageDraw.Draw(arcade)
    draw.line((55, 390, 352, 390), fill=(235, 161, 74), width=3)
    type_on(arcade, (55, 412), 'ONE MORE RUN.', 29, (232, 224, 207))
    frame(arcade, (239, 175, 86), '03 / ARCADE')

    hyper = ImageOps.fit(read('site-src/assets/hero-wide.jpg'), SIZE, Image.Resampling.LANCZOS)
    # Native 512px portal layers remain registered; uniform enlargement only.
    for name in ('entry-mouth', 'entry-rim-back', 'entry-glyphs', 'entry-rim-front'):
        layer = read('docs/art/hyper-run/' + name + '.png')
        layer = layer.resize((730, 730), Image.Resampling.LANCZOS)
        hyper.alpha_composite(layer, (305, 5))
    hyper = shade(hyper, left_max=140)
    # Use the existing scout silhouette with alpha, never stretch its aspect.
    ship = read('docs/art/hyper-run/scout-ship.png')
    ship = ship.crop(ship.getbbox())
    ship = ship.resize((410, round(ship.height*410/ship.width)), Image.Resampling.LANCZOS)
    hyper.alpha_composite(ship, (236, 430))
    type_on(hyper, (54, 93), 'ACORNAUT', 36, (216, 242, 254))
    type_on(hyper, (48, 150), 'HYPER', 105, (126, 225, 255))
    type_on(hyper, (48, 251), 'RUN', 133, (221, 252, 255))
    frame(hyper, (112, 229, 255), '04 / HYPER')

    output.mkdir(parents=True, exist_ok=False)
    outputs = {}
    for name, image in (('AcornautArcade', arcade), ('AcornautHyperRun', hyper)):
        path = output / (name + '_AttractV2.png')
        image.convert('RGB').save(path, optimize=True)
        outputs[name] = {'path': str(path), 'sha256': digest(path), 'dimensions': list(SIZE),
                         'material_slot': 'M_' + name + '_Screen',
                         'actor_label': 'Refine/LocalArcade/' + name + '/Body'}
    preview = Image.new('RGB', (1064, 446), (12, 19, 29))
    draw = ImageDraw.Draw(preview)
    for index, (name, image) in enumerate((('ARCADE', arcade), ('HYPER RUN', hyper))):
        x = 12 + index*528
        draw.text((x+6, 10), name + ' / 50% texture', font=font(22), fill=(230, 240, 248))
        preview.paste(image.convert('RGB').resize((512, 384), Image.Resampling.LANCZOS), (x, 48))
    preview.save(output/'review.png')
    receipt = {'kind': 'Static decorative attract compositions, not gameplay screenshots',
               'source_repository': 'https://github.com/j6sistek-ui/AcornautSandbox.git',
               'source_checkout': str(source_root),
               'source_head_reference': 'a0c9a0d3467160553fb726325c0689d0e7c501f0',
               'source_sha256': sources, 'font': str(FONT), 'font_sha256': digest(FONT),
               'recipe_sha256': digest(Path(__file__)), 'outputs': outputs,
               'composition': {'Arcade': 'Full-bleed right-anchored cover, aspect preserved',
                               'HyperRun': 'Owned registered portal layers and scout on owned sky'},
               'unreal_state': 'Not imported or assigned; root must review first'}
    for path, expected in sources.items():
        if digest(Path(path)) != expected:
            raise RuntimeError('Source artwork changed: ' + path)
    (output/'manifest.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=ART_ROOT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = compose(args.source_root, args.output)
    print(json.dumps({'outputs': result['outputs'], 'sources_preserved': True}, indent=2))
