"""Prepare reproducible graphs for the owner's installed local ComfyUI only.

This helper does not start a server, download weights, or submit work.
"""

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / ".agent/local/ArcadeGeneration"
LIBRARY = Path("M:/Local AI/Game Asset Studio/API")
REFERENCES = Path(
    "C:/Users/j6sis/.codex/codex-remote-attachments/"
    "01a0c239-12ad-7c60-83ce-bd20c0072f9a/B8859199-1EC7-4F23-9B92-024829746543"
)
ASSETS = (
    ("AsteroidArena", "1-Photo-1.jpg", 1.90, 1006202601),
    ("GalaxyPinball", "3-Photo-3.jpg", 1.90, 1006202603),
    ("TokensKiosk", "7-Photo-8.jpg", 1.75, 1006202607),
)


def main():
    if (WORK / "FROZEN_MANIFEST.json").exists():
        raise RuntimeError("Frozen1 is preserved; author a new version instead")
    for folder in ("source", "workflows", "raw", "receipts", "preview"):
        (WORK / folder).mkdir(parents=True, exist_ok=True)
    remove = json.loads((LIBRARY / "06_Remove_Background.json").read_text())
    geometry = json.loads((LIBRARY / "08_Image_to_3D_Prop.json").read_text())
    manifest = []
    for name, filename, height_m, seed in ASSETS:
        original = REFERENCES / filename
        target = WORK / "source" / filename
        if not target.exists():
            target.write_bytes(original.read_bytes())
        graph = copy.deepcopy(remove)
        graph["1"]["inputs"]["image"] = filename
        graph["6"]["inputs"]["filename_prefix"] = f"LocalArcade20261006/{name}/cutout"
        (WORK / "workflows" / f"{name}_cutout.json").write_text(json.dumps(graph, indent=2))
        graph = copy.deepcopy(geometry)
        graph["1"]["inputs"]["image"] = f"{name}_clean.png"
        graph["7"]["inputs"]["seed"] = seed
        graph["10"]["inputs"]["filename_prefix"] = f"LocalArcade20261006/{name}/raw"
        (WORK / "workflows" / f"{name}_geometry.json").write_text(json.dumps(graph, indent=2))
        manifest.append({
            "name": name, "reference": filename,
            "reference_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
            "target_height_m": height_m, "seed": seed,
            "geometry_model": "hunyuan3d-dit-v2_fp16.safetensors",
            "background_model": "birefnet.safetensors",
            "generation_endpoint": "http://127.0.0.1:8188",
            "status": "prepared; not executed",
        })
    (WORK / "receipts" / "prepared.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
