"""Read-only Alien Female asset inspection; run by the serialized Unreal lead.

No asset, actor, level, save or configuration is changed. The JSON receipt is the
only output. Render/posed-vertex evidence remains a separate native fixture.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / "Artifacts/AlienFemaleReview"
SOURCE = "/Game/TripoModels/AlienFemale"
PRIVATE = "/Game/SpaceSurvival/Licensed/AlienFemalePresentation"
CLIPS = "/Game/Robot_scout_R_21/Demo/Animations/"


def path(obj):
    return obj.get_path_name() if obj else None


def hashes():
    files = list((ROOT / "Content/TripoModels/AlienFemale").glob("*.uasset"))
    files += list((ROOT / "Content/TripoModels/Materials").glob("*.uasset"))
    return {str(item.relative_to(ROOT)): hashlib.sha256(item.read_bytes()).hexdigest()
            for item in files}


def material(interface):
    if not interface:
        return None
    edit = u.MaterialEditingLibrary
    base = interface.get_base_material()
    result = {"path": path(interface), "base": path(base), "textures": {}, "scalars": {}}
    if base:
        for prop in ("blend_mode", "material_domain", "two_sided"):
            result[prop] = str(base.get_editor_property(prop))
        result["skeletal_usage"] = bool(edit.has_material_usage(interface, u.MaterialUsage.MATUSAGE_SKELETAL_MESH))
    instance = isinstance(interface, u.MaterialInstance)
    for name in edit.get_texture_parameter_names(interface):
        texture = (edit.get_material_instance_texture_parameter_value(interface, name) if instance
                   else edit.get_material_default_texture_parameter_value(interface, name))
        result["textures"][str(name)] = path(texture)
    for name in edit.get_scalar_parameter_names(interface):
        result["scalars"][str(name)] = (edit.get_material_instance_scalar_parameter_value(interface, name)
                                         if instance else edit.get_material_default_scalar_parameter_value(interface, name))
    return result


def mesh_record(package):
    mesh = u.load_asset(package)
    assert isinstance(mesh, u.SkeletalMesh), "Expected actual female skeletal mesh: " + package
    edit = u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
    result = {"path": path(mesh), "skeleton": path(mesh.get_editor_property("skeleton")),
              "physics_asset": path(mesh.get_editor_property("physics_asset")),
              "materials": [material(slot.material_interface) for slot in mesh.get_editor_property("materials")],
              "bounds": str(mesh.get_bounds()), "lods": []}
    for lod in range(edit.get_lod_count(mesh)):
        sections = edit.get_num_sections(mesh, lod)
        result["lods"].append({"lod": lod, "vertices": edit.get_num_verts(mesh, lod), "sections": sections,
                               "material_slots": [edit.get_lod_material_slot(mesh, lod, section)
                                                  for section in range(sections)]})
    return result


def main():
    before = hashes()
    result = {"utc": datetime.now(timezone.utc).isoformat(), "mode": "read-only",
              "source_hashes": before, "meshes": [mesh_record(SOURCE + "/SK_AlienFemale")],
              "standalone_material": material(u.load_asset(SOURCE + "/MI_AlienFemale")), "clips": []}
    if u.EditorAssetLibrary.does_asset_exist(PRIVATE + "/SK_AlienFemalePresentation"):
        result["meshes"].append(mesh_record(PRIVATE + "/SK_AlienFemalePresentation"))
    for name in ("ThirdPersonIdle", "ThirdPersonWalk", "ThirdPersonRun"):
        clip = u.load_asset(CLIPS + name)
        assert isinstance(clip, u.AnimSequence), "Expected installed locomotion clip"
        result["clips"].append({"path": path(clip), "skeleton": path(clip.get_editor_property("skeleton")),
                                "length": clip.get_play_length()})
    result["source_preserved"] = before == hashes()
    assert result["source_preserved"], "Source content changed during read-only inspection"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "asset-inspection.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


main()
