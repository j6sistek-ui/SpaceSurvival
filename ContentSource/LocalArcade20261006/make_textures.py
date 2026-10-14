"""Local reference rectification and deterministic metal/playfield texture authoring."""

import json
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / ".agent/local/ArcadeGeneration"
OUT = WORK / "final" / "textures"


def rectified(source, label, points, size):
    if (WORK / "FROZEN_MANIFEST.json").exists():
        raise RuntimeError("Frozen1 is preserved; author a new version instead")
    image = Image.open(WORK / "source" / source).convert("RGB")
    tl, tr, br, bl = points
    image.transform(size, Image.Transform.QUAD, tuple(tl + bl + br + tr), Image.Resampling.BICUBIC).save(OUT / f"{label}.png")


def main():
    if (WORK / "FROZEN_MANIFEST.json").exists():
        raise RuntimeError("Frozen1 is preserved; author a new version instead")
    OUT.mkdir(parents=True, exist_ok=True)
    rectified("1-Photo-1.jpg", "AsteroidArena_Title", [(412, 89), (864, 111), (861, 230), (411, 211)], (1024, 256))
    rectified("1-Photo-1.jpg", "AsteroidArena_Screen", [(497, 318), (850, 357), (804, 589), (449, 552)], (1024, 768))
    rectified("1-Photo-1.jpg", "AsteroidArena_Badge", [(438, 884), (614, 925), (608, 1070), (440, 1023)], (512, 512))
    rectified("3-Photo-3.jpg", "GalaxyPinball_Title", [(432, 91), (864, 116), (858, 237), (429, 210)], (1024, 256))
    rectified("3-Photo-3.jpg", "GalaxyPinball_Screen", [(511, 302), (854, 346), (825, 480), (480, 438)], (1024, 512))
    rectified("7-Photo-8.jpg", "TokensKiosk_Title", [(497, 77), (823, 75), (815, 160), (494, 160)], (1024, 256))
    rectified("7-Photo-8.jpg", "TokensKiosk_Screen", [(518, 225), (769, 213), (790, 399), (535, 412)], (1024, 768))
    rng = np.random.default_rng(6102026)
    grain = rng.normal(0, 2.6, (1024, 1024, 1))
    for name, color in {"Graphite": (37, 43, 47), "GreenMetal": (42, 75, 46), "VioletMetal": (61, 38, 83), "Titanium": (87, 97, 105), "Brass": (117, 97, 59)}.items():
        image = Image.fromarray(np.uint8(np.clip(np.array(color)[None,None,:] + grain, 0, 255)))
        draw = ImageDraw.Draw(image)
        rand = random.Random(101)
        for _ in range(170):
            x, y = rand.randrange(1024), rand.randrange(1024)
            shade = tuple(min(255, v + rand.randrange(8, 19)) for v in color)
            draw.line((x, y, x + rand.randrange(2, 28), y + rand.randrange(-1, 2)), fill=shade, width=1)
        image.save(OUT / f"{name}.png")
    rand = random.Random(10062026)
    image = Image.new("RGB", (1024, 1024), (7, 8, 24))
    draw = ImageDraw.Draw(image)
    for _ in range(750):
        x, y = rand.randrange(1024), rand.randrange(1024)
        r = rand.choice([1, 1, 1, 2, 3])
        draw.ellipse((x-r, y-r, x+r, y+r), fill=rand.choice([(59, 95, 176), (132, 81, 177), (202, 193, 220)]))
    for index in range(7):
        x, y = rand.randrange(80, 940), rand.randrange(80, 940)
        draw.line((x-28, y, x+28, y), fill=(153, 120, 255), width=1)
        draw.line((x, y-28, x, y+28), fill=(153, 120, 255), width=1)
    for inset in (36, 50):
        draw.rounded_rectangle((inset, inset, 1024-inset, 1024-inset), radius=250, outline=(148, 100, 37), width=6)
    for y in (260, 435, 620):
        for x in (300, 725):
            draw.ellipse((x-35, y-35, x+35, y+35), outline=(220, 147, 49), width=8)
            draw.ellipse((x-12, y-12, x+12, y+12), fill=(236, 205, 125))
    image.save(OUT / "GalaxyPinball_Playfield.png")
    image = Image.new("RGB", (512, 256), (5, 19, 25))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 25)
    draw.text((24, 20), "STATION SERVICES", fill=(105, 206, 232), font=font)
    for i, label in enumerate(("ACCOUNT ACCESS", "STATION LEDGER", "CREDIT EXCHANGE")):
        draw.text((24, 76 + i * 48), label, fill=(75, 148, 178), font=font)
    image.save(OUT / "TokensKiosk_Status.png")
    # Owner superseded the token-game theme with a service terminal.
    from make_crane_textures import label
    label("TokensKiosk_Title", ["CREDIT", "EXCHANGE"], (1024, 256), (198, 216, 230))
    label("TokensKiosk_Screen", ["STATION LEDGER", "ACCOUNT SERVICES", "CREDIT EXCHANGE"], (1024, 768), (91, 177, 218))
    label("TokensKiosk_Status", ["STATION SERVICES", "ACCOUNT ACCESS"], (512, 256), (80, 179, 211))
    print(f"Wrote {len(list(OUT.glob('*.png')))} local textures to {OUT}")


if __name__ == "__main__":
    main()
