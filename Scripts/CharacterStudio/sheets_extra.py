"""Review sheets for the extra (per-clip) shots CaptureStudio.py takes with SS_STUDIO_EXTRA: one row per clip.

  python -I sheets_extra.py <capture_dir> <out.png> [rows_per_sheet=12]
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
per = int(sys.argv[3]) if len(sys.argv) > 3 else 12
font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
rep = json.load(open(os.path.join(src, "capture.json")))
rows = {}
for s in rep["shots"]:
    if s["shot"].split("_")[0] in ("idle", "walk", "role"):
        continue
    rows.setdefault((s["character"], s["clip"]), []).append(s)
keys = sorted(rows)
TW, TH = 480, 270
for page in range(0, len(keys), per):
    chunk = keys[page:page + per]
    cols = max(len(rows[k]) for k in chunk)
    sheet = Image.new("RGB", (cols * TW, len(chunk) * (TH + 30)), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    for r, k in enumerate(chunk):
        y = r * (TH + 30)
        d.text((6, y + 4), "%s  %s" % (k[0], k[1].rsplit("/", 1)[1]), fill=(255, 210, 90), font=font)
        for c, s in enumerate(sorted(rows[k], key=lambda s: s["shot"])):
            if os.path.isfile(s["png"]):
                im = Image.open(s["png"]).resize((TW, TH), Image.LANCZOS); sheet.paste(im, (c * TW, y + 30))
                d.text((c * TW + 6, y + 32), s["shot"].rsplit("_", 1)[1], fill=(255, 255, 255), font=font)
    path = out if len(keys) <= per else out[:-4] + "_%d.png" % (page // per + 1)
    sheet.save(path); print("sheet", path, len(chunk), "clips")
