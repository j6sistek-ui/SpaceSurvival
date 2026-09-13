"""Independent source-format checks; does not claim Unreal/gameplay validation."""
from array import array
import hashlib
import json
import math
from pathlib import Path
import sys
import wave

ROOT = Path(__file__).resolve().parent


def validate():
    results = {"status": "SOURCE_FORMATS_VALIDATED_ONLY", "meshes": [], "audio": [],
               "unverified": ["Unreal import", "hero orientation/animation", "collision", "visual quality in gameplay", "audio mix", "performance"]}
    mesh_manifest = json.loads((ROOT / "Meshes" / "manifest.json").read_text())
    for item in mesh_manifest["assets"]:
        path = ROOT / "Meshes" / (item["name"] + ".obj")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], path
        vertices, normals, uv, faces, materials = [], [], [], [], set()
        for line in path.read_text().splitlines():
            words = line.split()
            if not words:
                continue
            if words[0] == "v":
                vertices.append(tuple(map(float, words[1:])))
            elif words[0] == "vn":
                normals.append(tuple(map(float, words[1:])))
            elif words[0] == "vt":
                uv.append(tuple(map(float, words[1:])))
            elif words[0] == "f":
                faces.append([tuple(map(int, word.split("/"))) for word in words[1:]])
            elif words[0] == "usemtl":
                materials.add(words[1])
        assert len(vertices) == item["vertices"] and len(faces) == item["triangles"], path
        assert materials == set(item["materials"]), path
        assert all(all(math.isfinite(n) for n in v) for v in vertices + normals + uv), path
        assert all(abs(sum(x*x for x in n) - 1) < 1e-4 for n in normals), path
        for face in faces:
            assert len(face) == 3, path
            for v, t, n in face:
                assert 1 <= v <= len(vertices) and 1 <= t <= len(uv) and 1 <= n <= len(normals), path
            a, b, c = (vertices[corner[0] - 1] for corner in face)
            x = tuple(b[i] - a[i] for i in range(3))
            y = tuple(c[i] - a[i] for i in range(3))
            area_squared = sum(v*v for v in (x[1]*y[2]-x[2]*y[1], x[2]*y[0]-x[0]*y[2], x[0]*y[1]-x[1]*y[0]))
            assert area_squared > 1e-10, f"{path}: degenerate triangle"
        results["meshes"].append({"name": item["name"], "triangles": len(faces), "valid_indices_normals_nonzero_area": True})
    audio_manifest = json.loads((ROOT / "Audio" / "manifest.json").read_text())
    for item in audio_manifest["assets"]:
        path = ROOT / "Audio" / (item["name"] + ".wav")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], path
        with wave.open(str(path), "rb") as wav:
            assert wav.getnchannels() == item["channels"] and wav.getsampwidth() == 2, path
            assert wav.getframerate() == item["sample_rate"], path
            assert wav.getnframes() == round(item["seconds"] * item["sample_rate"]), path
            samples = array("h", wav.readframes(wav.getnframes()))
        if sys.byteorder != "little":
            samples.byteswap()
        peak = max(abs(s) for s in samples)
        assert 0 < peak < 29490, f"{path}: silence or insufficient headroom"
        channels = item["channels"]
        jump = max(abs(samples[c] - samples[-channels+c]) for c in range(channels)) / 32767
        # Large boundary discontinuities are a source defect; listening is still required.
        if item["loop"]:
            assert jump < 0.01, f"{path}: excessive loop boundary discontinuity {jump}"
        results["audio"].append({"name": item["name"], "peak_sample": peak, "boundary_jump": round(jump, 6), "valid_pcm": True})
    results["preserved_hero_sha256"] = hashlib.sha256((ROOT.parent / "model-rigged.glb").read_bytes()).hexdigest()
    assert results["preserved_hero_sha256"] == "c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91"
    (ROOT / "source_validation.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Validated source formats: {len(results['meshes'])} meshes, {len(results['audio'])} WAVs, unchanged GLB. Unreal validation remains open.")
    return results


if __name__ == "__main__":
    validate()
