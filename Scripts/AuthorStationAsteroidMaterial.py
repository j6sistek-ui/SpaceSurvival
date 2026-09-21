"""Author a private cool rock finish without modifying the supplied mesh or material.

The default is a dry-run. Add -SSApplyStationAsteroidMaterial to save the owned derivative.
World lighting is deliberately unchanged; this is the asteroid's local surface finish.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
SOURCE = "/Game/NeonGrid/Debris14A/Materials/Instances/MI_Debris14A_nanite"
TARGET = "/Game/SpaceSurvival/Licensed/StationReset/Materials/MI_StationAsteroid"
OUT = ROOT / "Artifacts/StationAsteroid/material-author.json"
SCALARS = {"base_color_brightness": .18, "base_color_saturation": .1, "Tiling": 2.5,
           "roughness_low": .65, "roughness_high": .95, "specular_intensity": .25,
           "metallic_low": 0., "metallic_high": 0.}
TINT = (.55, .7, 1., 1.)


def digest(package):
    path = ROOT / "Content" / (package.removeprefix("/Game/") + ".uasset")
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main():
    apply = "-SSApplyStationAsteroidMaterial" in u.SystemLibrary.get_command_line()
    before = digest(SOURCE)
    assert before, "Supplied asteroid material is missing"
    original = u.load_asset(SOURCE)
    edit, assets = u.MaterialEditingLibrary, u.EditorAssetLibrary
    assert set(SCALARS).issubset({str(n) for n in edit.get_scalar_parameter_names(original)})
    assert "base_color_tint" in {str(n) for n in edit.get_vector_parameter_names(original)}
    existing = digest(TARGET)
    previous = json.loads(OUT.read_text(encoding="utf-8")) if OUT.is_file() else None
    if existing:
        assert previous and previous.get("output_sha256") == existing, "Preserving unowned or edited material"
        assert previous.get("source_sha256") == before, "Supplied material changed since authoring"
    record = {"utc": datetime.now(timezone.utc).isoformat(), "mode": "apply" if apply else "dry-run",
              "source": SOURCE, "source_sha256": before, "target": TARGET,
              "scalars": SCALARS, "base_color_tint": TINT}
    if apply:
        if not existing:
            assets.make_directory(TARGET.rsplit("/", 1)[0])
        material = assets.load_asset(TARGET) if existing else assets.duplicate_asset(SOURCE, TARGET)
        assert material, "Private material duplication failed"
        # UE5.8 MaterialEditingLibrary setters mutate the instance but return an unchanged false
        # local (verified in installed engine source). Validate values through readback instead.
        for name, value in SCALARS.items():
            edit.set_material_instance_scalar_parameter_value(material, name, value)
        edit.set_material_instance_vector_parameter_value(material, "base_color_tint", u.LinearColor(*TINT))
        edit.update_material_instance(material)
        for name, value in SCALARS.items():
            assert abs(edit.get_material_instance_scalar_parameter_value(material, name) - value) < .0001, name
        color = edit.get_material_instance_vector_parameter_value(material, "base_color_tint")
        assert all(abs(a - b) < .0001 for a, b in zip((color.r, color.g, color.b, color.a), TINT))
        assert assets.save_loaded_asset(material, only_if_is_dirty=False), "Private material save failed"
        record["output_sha256"] = digest(TARGET)
    record["source_preserved"] = digest(SOURCE) == before
    assert record["source_preserved"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    destination = OUT if apply else OUT.with_name("material-dry-run.json")
    destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("STATION_ASTEROID_MATERIAL_COMPLETE " + record["mode"])


main()
