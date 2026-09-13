"""Fresh-editor, read-only persisted asset checks. Does not validate gameplay."""
import hashlib
import json
import math
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
BASE = "/Game/SpaceSurvival"


def main():
    library = u.EditorAssetLibrary
    record = {"status": "PERSISTED_ASSETS_VALIDATED_NOT_GAMEPLAY", "engine": u.SystemLibrary.get_engine_version(),
              "meshes": [], "audio": [], "materials": [], "errors": [],
              "limits": ["No gameplay classes or map validation", "No rendered visual approval", "No audio listening", "No player input or performance verification"]}

    def required(path, cls):
        obj = library.load_asset(path)
        assert obj and isinstance(obj, cls), f"Missing or incorrect class: {path}"
        assert library.get_metadata_tag(obj, "SSAuthoringVersion") == "1", f"Incomplete authoring: {path}"
        return obj

    def checked(label, fn):
        try:
            fn()
        except Exception as error:
            record["errors"].append(f"{label}: {error}")

    meshes = json.loads((ROOT / "ContentSource/Meshes/manifest.json").read_text())
    sounds = json.loads((ROOT / "ContentSource/Audio/manifest.json").read_text())
    mesh_tools = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)

    def validate_material(name):
        material = required(f"{BASE}/Materials/{name}", u.Material)
        record["materials"].append(material.get_path_name())

    def validate_mesh(item):
        mesh = required(f"{BASE}/Meshes/{item['name']}", u.StaticMesh)
        bounds = mesh.get_bounds()
        extent = bounds.box_extent
        dimensions = [extent.x * 2, extent.y * 2, extent.z * 2]
        expected = [item["bounds_cm"][1][i] - item["bounds_cm"][0][i] for i in range(3)]
        assert all(math.isfinite(v) and v > 0 for v in dimensions), f"Invalid bounds: {dimensions}"
        assert all(abs(a-b) <= max(0.02, b*0.00001) for a,b in zip(dimensions, expected)), f"Import changed axes/scale: {dimensions} expected {expected}"
        materials = [slot.get_editor_property("material_interface") for slot in mesh.get_editor_property("static_materials")]
        assert all(materials), "Null material slot"
        assert {m.get_name() for m in materials} == set(item["materials"]), "Lost material groups"
        vertices = mesh_tools.get_number_verts(mesh, 0)
        assert vertices > 0 and mesh_tools.get_lod_count(mesh) >= 1, "No built geometry"
        record["meshes"].append({"name": item["name"], "dimensions_cm": dimensions, "lod0_render_vertices": vertices,
                                 "material_slots": [m.get_name() for m in materials]})

    def validate_hero():
        hero = required(BASE + "/Character/SK_Acornaut", u.SkeletalMesh)
        walk = required(BASE + "/Character/A_Walk", u.AnimSequence)
        skeleton = hero.get_editor_property("skeleton")
        assert skeleton and skeleton == walk.get_editor_property("skeleton"), "Mismatched skeleton"
        duration = walk.get_editor_property("sequence_length")
        assert duration > 0, "Empty animation"
        bounds = hero.get_imported_bounds()
        extent = bounds.box_extent
        materials = [slot.get_editor_property("material_interface") for slot in hero.get_editor_property("materials")]
        assert materials and all(materials), "Null hero materials"
        assert hero.get_editor_property("physics_asset"), "Missing physics asset"
        pilot = required(BASE + "/Character/A_Pilot", u.AnimSequence)
        assert pilot.get_editor_property("skeleton") == skeleton, "Pilot skeleton mismatch"
        assert abs(pilot.get_editor_property("sequence_length")-4.0) < .01, "Pilot duration mismatch"
        source_hash = hashlib.sha256((ROOT / "model-rigged.glb").read_bytes()).hexdigest()
        assert source_hash == "c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91", "Changed supplied GLB"
        record["hero"] = {"mesh": hero.get_path_name(), "animation": walk.get_path_name(), "skeleton": skeleton.get_path_name(),
                          "animation_seconds": duration, "dimensions_cm": [extent.x*2, extent.y*2, extent.z*2],
                          "pilot_animation":pilot.get_path_name(),"pilot_seconds":pilot.get_editor_property("sequence_length"),
                          "materials": [m.get_path_name() for m in materials], "source_sha256": source_hash}

    def validate_sound(item):
        sound = required(f"{BASE}/Audio/{item['name']}", u.SoundWave)
        duration = sound.get_editor_property("duration")
        channels = sound.get_editor_property("num_channels")
        rate = sound.get_editor_property("imported_sample_rate")
        loop = sound.get_editor_property("looping")
        assert abs(duration-item["seconds"]) < .001, f"Duration {duration}"
        assert channels == item["channels"] and rate == item["sample_rate"], f"Wrong format {channels}/{rate}"
        assert loop == item["loop"], "Wrong looping flag"
        record["audio"].append({"name": item["name"], "seconds": duration, "channels": channels, "sample_rate": rate, "loop": loop})

    for name in meshes["palette"]:
        checked(name, lambda name=name: validate_material(name))
    for item in meshes["assets"]:
        checked(item["name"], lambda item=item: validate_mesh(item))
    checked("Preserved hero", validate_hero)
    for item in sounds["assets"]:
        checked(item["name"], lambda item=item: validate_sound(item))
    if record["errors"]:
        record["status"] = "FAILED"
    output = ROOT / "Saved/Validation/PersistedContent.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if record["errors"]:
        raise RuntimeError(f"Persisted asset validation failed: {record['errors']}")
    u.log(f"Persisted content validation passed: {len(record['meshes'])} meshes, {len(record['materials'])} materials, preserved hero/walk, {len(record['audio'])} sounds. No gameplay verification.")


if __name__ == "__main__":
    main()
