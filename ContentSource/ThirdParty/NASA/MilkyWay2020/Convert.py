"""Reproduce only the approved native-size NASA display conversion in Blender.
Run: blender --background --factory-startup --threads 2 --python Convert.py --
     --input <verified original EXR> --output <new PNG> --receipt <new JSON>
Original download is deliberately not bundled or fetched by this script.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy

SOURCE_SHA256 = "361d1961647af073b3b3e4aea4fca85f15b3c9d915e0c8c4befb02520dadd10a"
OUTPUT_SHA256 = "e5d17bc576e8a7278ab314958efb36e68a9ce0e6616169e035ef683a9f7c039d"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    source, output, receipt = [Path(value).resolve() for value in (args.input, args.output, args.receipt)]
    assert source.is_file() and source.stat().st_size == 137307727
    assert digest(source) == SOURCE_SHA256, "Official source bytes differ"
    assert not output.exists() and not receipt.exists(), "Never overwrite existing outputs"
    assert output != receipt and output.suffix.lower() == ".png"
    assert bpy.app.version[:3] == (5, 1, 2), "Re-review conversion identity with a different Blender version"
    image = bpy.data.images.load(str(source), check_existing=False)
    assert tuple(image.size) == (8192, 4096) and image.is_float
    assert image.colorspace_settings.name == "Linear Rec.709"
    scene = bpy.context.scene
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15
    image.save_render(str(output), scene=scene)
    assert digest(source) == SOURCE_SHA256, "Original modified during conversion"
    assert digest(output) == OUTPUT_SHA256, "Conversion bytes differ; do not adopt this result"
    record = {
        "status": "EXACT_APPROVED_NATIVE_SIZE_CONVERSION_REPRODUCED",
        "blender": bpy.app.version_string,
        "blender_build_hash": bpy.app.build_hash.decode(),
        "script_sha256": digest(__file__),
        "source_sha256": SOURCE_SHA256,
        "output_sha256": OUTPUT_SHA256,
        "dimensions": [8192, 4096],
        "output_bytes": output.stat().st_size,
        "operations": "Standard display conversion, exposure 0/gamma 1, RGB8 PNG compression 15. No resampling or artistic edit.",
        "limits": "Display quantization is not a byte-lossless copy of the half-float EXR. No Unreal render or acceptance.",
    }
    receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    bpy.data.images.remove(image)
    print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
