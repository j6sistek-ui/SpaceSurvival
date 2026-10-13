"""Turn render_strip.py frames into per-clip strips and one contact sheet per character. System Python + PIL.

  python -I sheets.py <frames_dir> <out_dir> [Who ...]

Frames are <frames_dir>/A_<Who>_<Clip>_<i>f.png. Writes <out_dir>/strips/A_<Who>_<Clip>.png (all frames side by side)
and <out_dir>/<Who>_clips.png (every clip as frames 1/3/5/7, cropped to the figure) - the sheet the owner reviews.
"""
import glob
import os
import re
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
only = set(sys.argv[3:])
os.makedirs(os.path.join(out, "strips"), exist_ok=True)
try:
    font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 15)
except OSError:
    font = ImageFont.load_default()
clips = {}
for f in glob.glob(os.path.join(src, "A_*_*f.png")):
    m = re.match(r"(A_([A-Za-z0-9]+)_.+)_(\d+)f\.png$", os.path.basename(f))
    if m and (not only or m.group(2) in only):
        clips.setdefault((m.group(2), m.group(1)), {})[int(m.group(3))] = f
by_who = {}
for (who, clip), frames in sorted(clips.items()):
    ims = [Image.open(frames[i]).convert("RGB") for i in sorted(frames)]
    w, h = ims[0].size
    strip = Image.new("RGB", (w * len(ims), h + 20), (20, 20, 20))
    ImageDraw.Draw(strip).text((4, 2), clip, fill=(255, 220, 80), font=font)
    for i, im in enumerate(ims):
        strip.paste(im, (i * w, 20))
    strip.save(os.path.join(out, "strips", clip + ".png"))
    by_who.setdefault(who, []).append((clip, ims))
CW, CH, PER = 128, 190, 3
for who, items in by_who.items():
    cells = []
    for clip, ims in items:
        pick = [ims[i] for i in (0, 2, 4, 6) if i < len(ims)]
        bg = Image.new("RGB", pick[0].size, pick[0].getpixel((2, 2))); box = None
        for fr in pick:
            b = ImageChops.difference(fr, bg).convert("L").point(lambda v: 255 if v > 18 else 0).getbbox()
            if b:
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        box = box or (0, 0) + pick[0].size
        bw, bh = box[2] - box[0], box[3] - box[1]; k = min(CW / bw, (CH - 22) / bh)
        cell = Image.new("RGB", (CW * 4, CH), (22, 22, 24))
        ImageDraw.Draw(cell).text((4, 2), clip[len("A_%s_" % who):][:52], fill=(255, 220, 80), font=font)
        for j, fr in enumerate(pick):
            im = fr.crop(box).resize((max(1, int(bw * k)), max(1, int(bh * k))))
            cell.paste(im, (j * CW + (CW - im.width) // 2, 22))
        cells.append(cell)
    rows = (len(cells) + PER - 1) // PER
    sheet = Image.new("RGB", (PER * (CW * 4 + 10), rows * (CH + 6) + 30), (8, 8, 10))
    ImageDraw.Draw(sheet).text((6, 4), "%s - %d clips (frames 1/3/5/7)" % (who, len(cells)), fill=(255, 255, 255), font=font)
    for n, c in enumerate(cells):
        sheet.paste(c, ((n % PER) * (CW * 4 + 10), 30 + (n // PER) * (CH + 6)))
    sheet.save(os.path.join(out, "%s_clips.png" % who))
    print("sheet", who, len(cells))
