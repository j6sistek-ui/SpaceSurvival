"""Paint the bartender outfit (black glossy bodysuit, thigh boots, fingerless gloves) into Joy's skin diffuse maps.

  python -I paint_outfit.py <export_dir>

Reads <export_dir>/Export.json and uv_regions.json (from export_joy_original.py), rasterises each region's UV polygons
into a per-material mask, feathers it (owner lesson from the green alien: hard texel masks look torn), composites the
suit colour over the original diffuse, and writes T_Joy_<Mat>_SuitMask.png for the material's gloss/metal lerp.
The original diffuse is kept beside it as *_Orig.png. Writes Paint.json for the Unreal import.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

EXP = Path(sys.argv[1])
data = json.loads((EXP / "Export.json").read_text())
reg = json.loads((EXP / "uv_regions.json").read_text())["regions"]
SUIT = (14, 12, 17)
images = {row["name"]: row for row in data["images"]}
paint = {"painted": {}, "masks": {}}
for mat in data["materials"]:
    name = mat["name"]
    if name not in reg or "BaseColor" not in mat["textures"]:
        continue
    tex = images[mat["textures"]["BaseColor"]]
    src = Path(tex["path"])
    im = Image.open(src).convert("RGB")
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    n = 0
    for label, polys in reg[name].items():
        for poly in polys:
            # Character Creator bodies are UDIM: the torso sits in tile 1002 (u 1..2), each material has its own map
            tu = int(sum(u for u, _ in poly) / len(poly) // 1)
            tv = int(sum(v for _, v in poly) / len(poly) // 1)
            pts = [((u - tu) * w, (1.0 - (v - tv)) * h) for u, v in poly]
            d.polygon(pts, fill=255)
            n += 1
    # close hairline gaps between neighbouring faces, then feather
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(radius=max(1.5, w / 4096 * 4)))
    suit = Image.new("RGB", (w, h), SUIT)
    out = Image.composite(suit, im, mask)
    orig = src.with_name(src.stem + "_Orig" + src.suffix)
    if not orig.exists():
        src.rename(orig)
    out.save(src)
    mpath = EXP / ("T_Joy_%s_SuitMask.png" % name.replace(" ", "_"))
    mask.save(mpath)
    paint["painted"][name] = {"diffuse": str(src), "original": str(orig), "faces": n}
    paint["masks"][name] = {"name": mpath.stem, "path": str(mpath), "size": [w, h]}
    print("PAINT| %-16s %d faces painted into %s (%dx%d), mask %s" % (name, n, src.name, w, h, mpath.name), flush=True)
(EXP / "Paint.json").write_text(json.dumps(paint, indent=2))
print("PAINT| done", flush=True)
