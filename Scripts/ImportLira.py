"""Import Lira (Mo Ling body + Lira outfit, Rigify deform skeleton) and her clips into the crew folder.

  set SS_LIRA_DIR=<folder with SK_Lira.fbx, tex/, manifest.json, Lira_<Clip>.fbx ...>
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/ImportLira.py"

Lands in /Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/Lira/: Mat/ (one PNG set + material instance per
slot: opaque slots on M_Tripo_PBR_Master, slots with an alpha map on a masked, two-sided M_Lira_Masked built
here), Rig/SK_Lira (legacy FBX path, no materials or morphs imported; slots assigned by name) and
Role/A_Lira_<Clip> (legacy FBX path onto SK_Lira's skeleton). The manifest comes from the Blender export
(scratch export_lira.py). Re-running replaces everything.
"""
import glob
import json
import os
import re

import unreal as u

L = u.EditorAssetLibrary; MEL = u.MaterialEditingLibrary; TOOLS = u.AssetToolsHelpers.get_asset_tools()
SRC = os.environ["SS_LIRA_DIR"]
WHO = "Lira"
BASE = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/%s" % WHO
MAT, RIG, ROLE = BASE + "/Mat", BASE + "/Rig", BASE + "/Role"
MASTER = "/Game/TripoModels/Materials/M_Tripo_PBR_Master"
manifest = json.load(open(os.path.join(SRC, "manifest.json")))


def line(s):
    u.log_warning("LIRA| " + str(s))


def key(n):
    return "".join(ch for ch in str(n).lower() if ch.isalnum())


for d in (BASE, MAT, RIG, ROLE):
    if not L.does_directory_exist(d):
        L.make_directory(d)


def imp_tex(fname, name, srgb, comp, flip_green=False):
    t = u.AssetImportTask(); t.filename = os.path.join(SRC, "tex", fname); t.destination_path = MAT
    t.destination_name = name; t.automated = True; t.replace_existing = True; t.save = False
    TOOLS.import_asset_tasks([t])
    tex = L.load_asset(MAT + "/" + name)
    assert isinstance(tex, u.Texture2D), "texture import failed: " + name
    tex.set_editor_property("virtual_texture_streaming", False)
    tex.set_editor_property("srgb", srgb); tex.set_editor_property("compression_settings", comp)
    if flip_green:
        tex.set_editor_property("flip_green_channel", True)
    L.save_loaded_asset(tex, False)
    return tex


# ---------------------------------------------------------------- a masked master for the alpha slots
def masked_master():
    path = MAT + "/M_Lira_Masked"
    if L.does_asset_exist(path):
        L.delete_asset(path)
    # The linear slots (roughness / metallic / alpha) are TC_MASKS textures, so their samplers must be Masks and the
    # master's default must be a Masks texture too: the Tripo default white is a greyscale texture, and a LinearColor
    # sampler on it failed the whole material ("Default Material will be used") - the hair rendered grey.
    white_masks = imp_tex("T_Lira_Default_White_Masks.png", "T_Lira_Default_White_Masks", False, u.TextureCompressionSettings.TC_MASKS)
    m = TOOLS.create_asset("M_Lira_Masked", MAT, u.Material, u.MaterialFactoryNew())
    m.set_editor_property("blend_mode", u.BlendMode.BLEND_MASKED)
    m.set_editor_property("two_sided", True)
    nodes = {}
    for i, (pname, prop, defkind) in enumerate((("BaseColor", u.MaterialProperty.MP_BASE_COLOR, "color"), ("Normal", u.MaterialProperty.MP_NORMAL, "normal"),
                                                 ("Roughness", u.MaterialProperty.MP_ROUGHNESS, "linear"), ("Metallic", u.MaterialProperty.MP_METALLIC, "linear"),
                                                 ("Alpha", u.MaterialProperty.MP_OPACITY_MASK, "linear"))):
        n = MEL.create_material_expression(m, u.MaterialExpressionTextureSampleParameter2D, -400, i * 220)
        n.set_editor_property("parameter_name", pname)
        default = white_masks if defkind == "linear" else L.load_asset(
            "/Game/TripoModels/Materials/T_Tripo_Default_Normal" if defkind == "normal" else "/Game/TripoModels/Materials/T_Tripo_Default_White")
        if default:
            n.set_editor_property("texture", default)
        if defkind == "normal":
            n.set_editor_property("sampler_type", u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        elif defkind == "linear":
            n.set_editor_property("sampler_type", u.MaterialSamplerType.SAMPLERTYPE_MASKS)
        MEL.connect_material_property(n, "RGB" if defkind != "linear" else "R", prop)
        nodes[pname] = n
    MEL.recompile_material(m)
    L.save_loaded_asset(m, False)
    return m


master = L.load_asset(MASTER)
assert master, "Tripo master missing"
master_params = {str(n): str(n) for n in MEL.get_texture_parameter_names(master)}


def param_for(names, want):
    for n in names:
        if want in n.lower():
            return n
    return None


masked = masked_master()
made_mi = {}
for slot, rec in manifest["slots"].items():
    is_masked = rec.get("masked")
    parent = masked if is_masked else master
    pnames = [str(n) for n in MEL.get_texture_parameter_names(parent)]
    texs = {}
    texs["base"] = imp_tex(rec["base"], "T_%s_%s_BaseColor" % (WHO, slot), True, u.TextureCompressionSettings.TC_DEFAULT)
    if rec.get("normal"):
        texs["normal"] = imp_tex(rec["normal"], "T_%s_%s_Normal" % (WHO, slot), False, u.TextureCompressionSettings.TC_NORMALMAP, flip_green=True)
    texs["rough"] = imp_tex(rec["rough"], "T_%s_%s_Roughness" % (WHO, slot), False, u.TextureCompressionSettings.TC_MASKS)
    texs["metal"] = imp_tex(rec["metal"], "T_%s_%s_Metallic" % (WHO, slot), False, u.TextureCompressionSettings.TC_MASKS)
    if is_masked:
        texs["alpha"] = imp_tex(rec["alpha"], "T_%s_%s_Alpha" % (WHO, slot), False, u.TextureCompressionSettings.TC_MASKS)
    mi_path = MAT + "/MI_%s_%s" % (WHO, slot)
    if L.does_asset_exist(mi_path):
        L.delete_asset(mi_path)
    mi = TOOLS.create_asset("MI_%s_%s" % (WHO, slot), MAT, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    for want, tex in (("base", texs.get("base")), ("normal", texs.get("normal")), ("rough", texs.get("rough")), ("metal", texs.get("metal")), ("alpha", texs.get("alpha"))):
        if tex is None:
            continue
        pname = param_for(pnames, want)
        if pname:
            MEL.set_material_instance_texture_parameter_value(mi, pname, tex)
    got = {str(n): MEL.get_material_instance_texture_parameter_value(mi, n) for n in MEL.get_texture_parameter_names(mi)}
    L.save_loaded_asset(mi, False)
    made_mi[key(rec["material"])] = mi
    line("slot %-28s %s  %s" % (slot, "masked" if is_masked else "opaque", {k: (v.get_name() if v else None) for k, v in got.items()}))

# ---------------------------------------------------------------- the mesh (legacy FBX path, like the crew)
u.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
if L.does_asset_exist(RIG + "/SK_" + WHO):
    L.delete_directory(RIG); L.make_directory(RIG)
options = u.FbxImportUI()
options.set_editor_property("import_mesh", True); options.set_editor_property("import_as_skeletal", True)
options.set_editor_property("import_animations", False); options.set_editor_property("import_materials", False)
options.set_editor_property("import_textures", False); options.set_editor_property("create_physics_asset", True)
options.set_editor_property("mesh_type_to_import", u.FBXImportType.FBXIT_SKELETAL_MESH)
sk = options.get_editor_property("skeletal_mesh_import_data")
sk.set_editor_property("import_morph_targets", False); sk.set_editor_property("convert_scene", True)
task = u.AssetImportTask()
for prop, value in (("filename", os.path.join(SRC, "SK_%s.fbx" % WHO)), ("destination_path", RIG), ("destination_name", "SK_" + WHO),
                    ("automated", True), ("replace_existing", True), ("save", True), ("options", options)):
    task.set_editor_property(prop, value)
TOOLS.import_asset_tasks([task])
mesh = L.load_asset(RIG + "/SK_" + WHO)
assert isinstance(mesh, u.SkeletalMesh), "mesh import failed"
missing = []
# UE 5.8 Python: a SkeletalMaterial struct read from the mesh does not take set_editor_property (the value reads back
# None, so the slots saved empty and the character rendered in the default white material). Build new structs and
# write the whole list back; ImportedMaterialSlotName is read-only and only matters for reimport.
slots = []
for slot in mesh.get_editor_property("materials"):
    name = str(slot.get_editor_property("material_slot_name"))
    mi = made_mi.get(key(name))
    if not mi:
        missing.append(name)
    sm = u.SkeletalMaterial()
    sm.set_editor_property("material_slot_name", name)
    sm.set_editor_property("material_interface", mi)
    slots.append(sm)
mesh.set_editor_property("materials", slots)
L.save_loaded_asset(mesh, False)
empty = [str(s.get_editor_property("material_slot_name")) for s in mesh.get_editor_property("materials") if not s.get_editor_property("material_interface")]
assert not empty, "material slots still empty after assignment: %s" % empty
b = mesh.get_bounds()
ext = b.box_extent
line("SK_%s imported: bounds extent (cm) x %.0f y %.0f z %.0f (height ~%.0f), slots %d, unassigned %s" % (
    WHO, ext.x, ext.y, ext.z, ext.z * 2, len(mesh.get_editor_property("materials")), missing))
skeleton = mesh.get_editor_property("skeleton")

# ---------------------------------------------------------------- clips
made = []
for fbx in sorted(glob.glob(os.path.join(SRC, "%s_*.fbx" % WHO))):
    clip = os.path.basename(fbx)[len(WHO) + 1:-4]
    name = "A_%s_%s" % (WHO, clip)
    if L.does_asset_exist(ROLE + "/" + name):
        L.delete_asset(ROLE + "/" + name)
    ui = u.FbxImportUI()
    for prop, value in (("import_mesh", False), ("import_animations", True), ("import_as_skeletal", True), ("import_materials", False),
                        ("import_textures", False), ("skeleton", skeleton), ("mesh_type_to_import", u.FBXImportType.FBXIT_ANIMATION),
                        ("original_import_type", u.FBXImportType.FBXIT_ANIMATION), ("automated_import_should_detect_type", False)):
        ui.set_editor_property(prop, value)
    task = u.AssetImportTask()
    for prop, value in (("filename", fbx), ("destination_path", ROLE), ("destination_name", name), ("automated", True),
                        ("replace_existing", True), ("save", True), ("options", ui)):
        task.set_editor_property(prop, value)
    TOOLS.import_asset_tasks([task])
    a = L.load_asset(ROLE + "/" + name)
    made.append("%s %s" % (name, ("%.2fs" % a.get_play_length()) if isinstance(a, u.AnimSequence) else "FAILED(%s)" % type(a).__name__))
u.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 1")
line("clips: %s" % made)
L.save_directory(BASE, False, True)
line("DONE")
