"""Composite local BiRefNet alpha onto white, preserving model input receipts."""

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / ".agent/local/ArcadeGeneration"


def main():
    if (WORK / "FROZEN_MANIFEST.json").exists():
        raise RuntimeError("Frozen1 is preserved; author a new version instead")
    records = []
    for name in ("AsteroidArena", "GalaxyPinball", "TokensKiosk"):
        inputs = sorted((WORK / "raw" / name).glob("*.png"))
        assert len(inputs) == 1, f"Expected one local cutout for {name}"
        image = Image.open(inputs[0]).convert("RGBA")
        bbox = image.getchannel("A").point(lambda value: 255 if value > 127 else 0).getbbox()
        assert bbox
        image = image.crop(bbox)
        size = int(max(image.size) * 1.12)
        clean = Image.new("RGBA", (size, size), "white")
        clean.alpha_composite(image, ((size - image.width) // 2, (size - image.height) // 2))
        target = WORK / "source" / f"{name}_clean.png"
        clean.convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS).save(target)
        records.append({"name": name, "alpha_bounds": bbox, "source": str(inputs[0]), "output": str(target)})
    (WORK / "receipts" / "cutout_preparation.json").write_text(json.dumps(records, indent=2))
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
