"""Read-only, standard-library check for the promoted native NASA sky source."""
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == 1
    assert manifest["license"] == "NASA-SVS-Public-Domain-With-Gaia-Credit"
    assert manifest["file"] == "MilkyWay2020_8k.png"
    assert manifest["credit"] == "NASA/Goddard Space Flight Center Scientific Visualization Studio. Gaia DR2: ESA/Gaia/DPAC."
    png = ROOT / manifest["file"]
    data = png.read_bytes()
    assert len(data) == manifest["bytes"] == 52500034
    assert hashlib.sha256(data).hexdigest() == manifest["sha256"] == "e5d17bc576e8a7278ab314958efb36e68a9ce0e6616169e035ef683a9f7c039d"
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR"
    assert struct.unpack(">II", data[16:24]) == (manifest["width"], manifest["height"]) == (8192, 4096)
    assert data[24:26] == bytes([8, 2]), "Expected RGB8 PNG"
    original = manifest["source"]
    assert original["url"] == "https://svs.gsfc.nasa.gov/vis/a000000/a004800/a004851/milkyway_2020_8k.exr"
    assert original["bytes"] == 137307727
    assert original["sha256"] == "361d1961647af073b3b3e4aea4fca85f15b3c9d915e0c8c4befb02520dadd10a"
    conversion = json.loads((ROOT / "ConversionReceipt.json").read_text(encoding="utf-8"))
    assert conversion["status"] == "EXACT_APPROVED_NATIVE_SIZE_CONVERSION_REPRODUCED"
    assert conversion["script_sha256"] == sha(ROOT / "Convert.py")
    assert conversion["source_sha256"] == original["sha256"]
    assert conversion["output_sha256"] == manifest["sha256"]
    assert conversion["dimensions"] == [8192, 4096] and conversion["output_bytes"] == len(data)
    proof = json.loads((ROOT / "SourceOrigin.json").read_text(encoding="utf-8"))
    assert original in proof["downloads"]
    assert proof["source_header"]["dataWindow"] == [0, 0, 8191, 4095]
    assert (ROOT / "LICENSE.md").is_file()
    assert all(p.stat().st_size < 100000000 for p in ROOT.rglob("*") if p.is_file())
    return manifest


if __name__ == "__main__":
    result = check()
    print(json.dumps({"status": "NASA_SKY_SOURCE_CHECK_PASS", "file": result["file"],
                      "dimensions": [result["width"], result["height"]], "sha256": result["sha256"]}))
