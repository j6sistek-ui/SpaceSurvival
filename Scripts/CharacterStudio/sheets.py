"""One review sheet per character from CaptureStudio.py's PNGs. System Python + PIL.

  python -I sheets.py <capture_dir> <out_dir>
"""
import glob
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
small = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 20)
ORDER = ["idle_front", "idle_34", "idle_side", "idle_back", "idle_legs", "idle_head",
         "walk_front", "walk_34", "walk_back", "role_front", "role_34"]
by = {}
if os.path.isfile(os.path.join(src, "capture.json")):
    rep = json.load(open(os.path.join(src, "capture.json")))
    for s in rep["shots"]:
        by.setdefault(s["character"], {})[s["shot"]] = s
else:                                   # a run still in progress: sheets from the files on disk, clips unknown
    rep = {"shots": [], "exposure_bias": float("nan")}
    for f in glob.glob(os.path.join(src, "*_*.png")):
        base = os.path.basename(f)[:-4]
        for k in ORDER:
            if base.endswith("_" + k):
                by.setdefault(base[:-len(k) - 1], {})[k] = {"png": f, "clip": ""}
only = set(sys.argv[3:])
if only:
    by = {k: v for k, v in by.items() if k in only}
CW, CH, PER = 640, 360, 4
for name, shots in by.items():
    keys = [k for k in ORDER if k in shots]
    rows = (len(keys) + PER - 1) // PER
    sheet = Image.new("RGB", (PER * CW, rows * (CH + 30) + 44), (12, 12, 14))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), "%s  -  in-game studio capture (UE 5.8, animated, play mode), exposure bias %.2f" % (name, rep.get("exposure_bias", 0)), fill=(255, 220, 80), font=font)
    for i, k in enumerate(keys):
        im = Image.open(shots[k]["png"]).convert("RGB").resize((CW, CH))
        x, y = (i % PER) * CW, 44 + (i // PER) * (CH + 30)
        sheet.paste(im, (x, y + 30))
        clip = (shots[k]["clip"] or "").rsplit("/", 1)[-1].split(".")[0]
        d.text((x + 6, y + 4), "%s   %s" % (k, clip), fill=(230, 230, 230), font=small)
    sheet.save(os.path.join(out, "%s.png" % name))
    print("sheet", name, len(keys))
