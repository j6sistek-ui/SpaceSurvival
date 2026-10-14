"""Rebuild SK_Joy from an author_soft_tissue.py FBX: the same body and skeleton, the materials put back by slot name, the
twelve ST_<Region>_<Axis> morph targets Silver's BodyDynamics spring component drives, and whatever garments the export
carries (the fitted jacket since 2026-10-14). The .uasset is copied aside first.

  set SS_JOY_ST_DIR=<soft_tissue export folder>   (SK_Joy.fbx + SoftTissue.json)
  set SS_JOY_ST_BACKUP=<folder for the pre-reimport SK_Joy.uasset>
  set SS_JOY_DROP_SLOTS=FS_waistcoat                                  (optional: slots the new FBX no longer has)
  set SS_JOY_SLOT_MATERIALS=M_jacket=/Game/Jacket_1/Materials/MI_Jacket (optional: materials for new slots, ';'-separated)
  set SS_JOY_SKIN_ORIGINAL=1                                          (optional: body diffuse back to the original, no painted strap)
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI ... -ExecutePythonScript="<abs>/reimport_joy_soft_tissue.py"
"""
import json
import os
import shutil

import unreal as u

B = "/Game/SpaceSurvival/Licensed/StationAssets/JoyBartender"
MESH = B + "/Mesh/SK_Joy"
SKEL = "/Game/SpaceSurvival/Licensed/StationAssets/JoyPurple/Mesh/SK_JoyPurple_Skeleton"
SRC = os.environ["SS_JOY_ST_DIR"]
BACKUP = os.environ["SS_JOY_ST_BACKUP"]
DATA = json.load(open(os.path.join(SRC, "SoftTissue.json")))
EXPECTED = sorted(DATA["new_keys"]["CC_Base_Body"])
DROP = [n for n in os.environ.get("SS_JOY_DROP_SLOTS", "").split(",") if n]
ADD = dict(kv.split("=", 1) for kv in os.environ.get("SS_JOY_SLOT_MATERIALS", "").split(";") if kv)
L = u.EditorAssetLibrary
TOOLS = u.AssetToolsHelpers.get_asset_tools()


def log(s):
    u.log_warning("JOYST| " + str(s))


assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
mesh = u.load_asset(MESH)
assert isinstance(mesh, u.SkeletalMesh), MESH
skeleton = u.load_asset(SKEL)
before_materials = [(str(s.material_slot_name), s.material_interface.get_path_name() if s.material_interface else None) for s in mesh.materials]
before_morphs = sorted(str(n) for n in mesh.get_all_morph_target_names())
file = u.SystemLibrary.get_system_path(mesh)
assert file.endswith(".uasset") and os.path.exists(file), file
os.makedirs(BACKUP, exist_ok=False)
shutil.copy2(file, os.path.join(BACKUP, "SK_Joy.uasset"))
log("backup %s -> %s ; %d materials, %d morphs before" % (file, BACKUP, len(before_materials), len(before_morphs)))

options = u.FbxImportUI()
for k, v in dict(automated_import_should_detect_type=False, mesh_type_to_import=u.FBXImportType.FBXIT_SKELETAL_MESH, import_as_skeletal=True,
                 import_mesh=True, import_animations=False, import_materials=False, import_textures=False, create_physics_asset=False,
                 skeleton=skeleton).items():
    options.set_editor_property(k, v)
for k, v in dict(import_uniform_scale=1.0, convert_scene=True, convert_scene_unit=True, force_front_x_axis=False, use_t0_as_ref_pose=False,
                 preserve_smoothing_groups=True, import_morph_targets=True, normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS).items():
    options.skeletal_mesh_import_data.set_editor_property(k, v)
# A replace-in-place reimport is not deterministic here: the first one went through Interchange (morphs kept, 90 spaced
# names rewritten), the next took the legacy FbxFactory reimport path and came back with NO morph targets. A fresh legacy
# import into the same path keeps every morph (verified on a probe import), so the old asset is force-deleted first (the
# map references SK_Joy by path and resolves again on load) and the materials are put back from the record taken above.
assert L.delete_asset(MESH), "could not delete the old SK_Joy"
t = u.AssetImportTask()
for k, v in dict(filename=os.path.join(SRC, "SK_Joy.fbx"), destination_path=B + "/Mesh", destination_name="SK_Joy", automated=True, replace_existing=False, save=False,
                 options=options, factory=u.FbxFactory()).items():
    t.set_editor_property(k, v)
TOOLS.import_asset_tasks([t])
paths = list(t.imported_object_paths)
log("imported: %s" % paths)
mesh = u.load_asset(MESH)
assert isinstance(mesh, u.SkeletalMesh) and any(p.startswith(MESH) for p in paths), paths
assert mesh.skeleton.get_path_name() == skeleton.get_path_name(), mesh.skeleton.get_path_name()
comp = u.SkeletalMeshComponent()
comp.set_skeletal_mesh_asset(mesh)
assert comp.get_num_bones() == 101, comp.get_num_bones()
after_morphs = sorted(str(n) for n in mesh.get_all_morph_target_names())
st = [n for n in after_morphs if n.startswith("ST_")]
assert st == EXPECTED, (st, EXPECTED)
# the reimport path writes the CC tearline / eye-occlusion morph names with underscores where the first import kept
# spaces ("EO Bulge L" -> "EO_Bulge_L"); nothing drives those morphs, so the spelling change is recorded, not refused
norm = lambda n: n.replace(" ", "_")  # noqa: E731
missing = sorted(n for n in before_morphs if norm(n) not in {norm(a) for a in after_morphs})
# a dropped garment takes its own keys with it (the waistcoat's EV_gilet_open_*); the face and body must lose nothing
lost = [n for n in missing if not n.startswith("EV_")]
assert not lost, lost
assert L.save_loaded_asset(mesh, False)  # the old asset is gone: the new one is on disk before any further check can fail
log("saved after import: slots %s" % [(str(s.material_slot_name), s.material_interface.get_name() if s.material_interface else None) for s in mesh.materials])
renamed = sorted(n for n in before_morphs if n not in set(after_morphs))
# the reimport keeps the materials by slot name; put any slot back that came through empty or changed
slots = list(mesh.materials)
restored = 0
for i, s in enumerate(slots):
    name = str(s.material_slot_name)
    want = next((m for n, m in before_materials if n == name), None) or (ADD[name] + "." + ADD[name].rsplit("/", 1)[1] if name in ADD else None)
    have = s.material_interface.get_path_name() if s.material_interface else None
    if want and have != want:
        s.set_editor_property("material_interface", u.load_asset(want.split(".")[0]))
        slots[i] = s
        restored += 1
if restored:
    mesh.set_editor_property("materials", slots)
expected = sorted([n for n, _ in before_materials if n not in DROP] + [n for n in ADD if n not in [m for m, _ in before_materials]])
assert sorted(str(s.material_slot_name) for s in mesh.materials) == expected, (sorted(str(s.material_slot_name) for s in mesh.materials), expected)
empty = [str(s.material_slot_name) for s in mesh.materials if not s.material_interface]
assert not empty, ("slots without a material", empty, {k: v for k, v in ADD.items()})
assert L.save_loaded_asset(mesh, False)
skin = None
if os.environ.get("SS_JOY_SKIN_ORIGINAL"):
    # owner 2026-10-14: the jacket is the cover; the painted strap goes, the body diffuse is the pack's original again
    E = u.MaterialEditingLibrary
    mi = u.load_asset(B + "/Materials/MI_Joy_Std_Skin_Body")
    orig = u.load_asset("/Game/SpaceSurvival/Licensed/StationAssets/JoyPurple/Textures/T_Joy_Std_Skin_Body_Diffuse")
    assert isinstance(mi, u.MaterialInstanceConstant) and isinstance(orig, u.Texture2D)
    E.set_material_instance_texture_parameter_value(mi, "BaseColor", orig)
    E.set_material_instance_scalar_parameter_value(mi, "SuitMix", 0.0)
    E.update_material_instance(mi)
    assert L.save_loaded_asset(mi, False)
    skin = {"base_color": orig.get_path_name(), "suit_mix": 0.0}
b = mesh.get_bounds()
# her size, not just her bone count: an exploded garment shows here first (the 100x jacket of 2026-10-14 imported fine)
assert 170 <= b.box_extent.z * 2 <= 195 and b.box_extent.x * 2 <= 200 and b.box_extent.y * 2 <= 200, ("SK_Joy bounds", list(b.box_extent.to_tuple()))
report = {"mesh": mesh.get_path_name(), "bones": comp.get_num_bones(), "height_cm": b.box_extent.z * 2, "morphs_before": len(before_morphs), "morphs_after": len(after_morphs),
          "soft_tissue_morphs": st, "materials_restored": restored, "renamed_morphs": len(renamed), "dropped_morphs": missing, "backup": BACKUP, "fbx": DATA["fbx"], "slots": [str(s.material_slot_name) for s in mesh.materials], "dropped": DROP, "added": ADD, "skin": skin}
json.dump(report, open(os.path.join(SRC, "Reimport.json"), "w"), indent=1)
log("DONE " + json.dumps(report))
