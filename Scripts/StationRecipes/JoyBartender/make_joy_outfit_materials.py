"""Joy's own instances of the sci-fi pants and sneaker materials (the pack's red, colour variant c3), tinted with the
pack's own 'Color' multiplier. Owner 2026-10-14: "make the red slightly more closer in color to her hair but not exact,
just a minor shift to make it more girly"; "not super hot pink, let me find a color sample". The pack's assets are
never edited: these are children in JoyBartender/Materials, created or updated in place.

  set SS_PANTS_TINT=r,g,b      (linear multiplier on the base colour; the pack's own value is 0.79,0.79,0.79)
  set SS_PANTS_ROUGHNESS=0.45  set SS_PANTS_SPECULAR=0.6   (optional; the pack ships 1.0 and 0.5)
  set SS_EYE_TEXTURES=<author_soft_tissue.py --eyes output folder>   (optional: MI_Joy_EyeOption from its two maps)
  set SS_FABRIC_SLOT=M_SciFi_P_Pack_02   (optional: her pants' own satin instance on that SK_Joy slot; the sneakers keep
      MI_Joy_Pants / MI_Joy_Sneakers_L)   SS_FABRIC_ROUGHNESS=1.25  SS_FABRIC_METALLIC=0.15  SS_FABRIC_SPECULAR=0.5
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI ... -ExecutePythonScript="<abs>/make_joy_outfit_materials.py"
"""
import json
import os

import unreal as u

B = "/Game/SpaceSurvival/Licensed/StationAssets/JoyBartender/Materials"
PACK = "/Game/SciFi_PS_P02_UE5/Materials"
TINT = [float(v) for v in os.environ.get("SS_PANTS_TINT", "0.79,0.72,1.10").split(",")]
assert len(TINT) == 3 and all(0.0 < v < 3.0 for v in TINT), TINT
MAKE = {"MI_Joy_Pants": PACK + "/ML_Pants_Sneakers_p02_c3_Inst", "MI_Joy_Sneakers_L": PACK + "/ML_Sneakers_L_p02_c3_Inst"}
E = u.MaterialEditingLibrary
L = u.EditorAssetLibrary
TOOLS = u.AssetToolsHelpers.get_asset_tools()
report = {}
for name, parent_path in MAKE.items():
    parent = u.load_asset(parent_path)
    assert isinstance(parent, u.MaterialInstanceConstant), parent_path
    path = B + "/" + name
    mi = u.load_asset(path) if L.does_asset_exist(path) else TOOLS.create_asset(name, B, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
    assert mi, path
    E.set_material_instance_parent(mi, parent)
    E.set_material_instance_vector_parameter_value(mi, "Color", u.LinearColor(TINT[0], TINT[1], TINT[2], 0.0))
    # owner 2026-10-14: "making it a more material match to the jacket might be good" - a leather sheen
    for k, env in (("Roughness", "SS_PANTS_ROUGHNESS"), ("Specular", "SS_PANTS_SPECULAR")):
        if os.environ.get(env):
            E.set_material_instance_scalar_parameter_value(mi, k, float(os.environ[env]))
    E.update_material_instance(mi)
    assert L.save_loaded_asset(mi, False), path
    report[name] = {"parent": parent_path, "Color": list(E.get_material_instance_vector_parameter_value(mi, "Color").to_tuple()),
                    "Roughness": E.get_material_instance_scalar_parameter_value(mi, "Roughness"), "Specular": E.get_material_instance_scalar_parameter_value(mi, "Specular")}
# the brow ring (owner 2026-10-14: "eyebrow piercing, metal"): her own opaque master, white base, polished steel
ring_path = B + "/MI_Joy_Piercing"
ring = u.load_asset(ring_path) if L.does_asset_exist(ring_path) else TOOLS.create_asset("MI_Joy_Piercing", B, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
E.set_material_instance_parent(ring, u.load_asset(B + "/M_JoyBOpaque"))
E.set_material_instance_texture_parameter_value(ring, "BaseColor", u.load_asset("/Engine/EngineResources/WhiteSquareTexture"))
E.set_material_instance_vector_parameter_value(ring, "Tint", u.LinearColor(0.62, 0.62, 0.66, 1.0))
for k, v in (("Metallic", 1.0), ("Roughness", 0.22), ("Specular", 0.5), ("LuminanceTint", 0.0), ("SuitMix", 0.0)):
    E.set_material_instance_scalar_parameter_value(ring, k, v)
E.update_material_instance(ring)
assert L.save_loaded_asset(ring, False), ring_path
report["MI_Joy_Piercing"] = {"parent": B + "/M_JoyBOpaque", "scalars": {str(p): E.get_material_instance_scalar_parameter_value(ring, p) for p in E.get_scalar_parameter_names(ring)}}
# the G-string (owner 2026-10-14): black, a soft satin sheen
gs_path = B + "/MI_Joy_GString"
gsm = u.load_asset(gs_path) if L.does_asset_exist(gs_path) else TOOLS.create_asset("MI_Joy_GString", B, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
E.set_material_instance_parent(gsm, u.load_asset(B + "/M_JoyBOpaque"))
E.set_material_instance_texture_parameter_value(gsm, "BaseColor", u.load_asset("/Engine/EngineResources/WhiteSquareTexture"))
E.set_material_instance_vector_parameter_value(gsm, "Tint", u.LinearColor(0.015, 0.015, 0.018, 1.0))
for k, v in (("Metallic", 0.0), ("Roughness", 0.45), ("Specular", 0.5), ("LuminanceTint", 0.0), ("SuitMix", 0.0)):
    E.set_material_instance_scalar_parameter_value(gsm, k, v)
E.update_material_instance(gsm)
assert L.save_loaded_asset(gsm, False), gs_path
report["MI_Joy_GString"] = {"parent": B + "/M_JoyBOpaque"}
# the owner's eyeball pick (2026-10-14, "1.7k large iris"): its colour map (sRGB) and normal map (glTF is OpenGL, +Y:
# the green channel is flipped for Unreal) beside her other textures, on her opaque master, wet-glossy
if os.environ.get("SS_EYE_TEXTURES"):
    TEX = B.rsplit("/", 1)[0] + "/Textures"
    tex = {}
    for kind in ("BaseColor", "Normal"):
        src = os.path.join(os.environ["SS_EYE_TEXTURES"], "T_Joy_EyeOption_%s.png" % kind)
        assert os.path.exists(src), src
        t = u.AssetImportTask()
        for k, v in dict(filename=src, destination_path=TEX, destination_name="T_Joy_EyeOption_" + kind, automated=True, replace_existing=True, save=False).items():
            t.set_editor_property(k, v)
        TOOLS.import_asset_tasks([t])
        tx = u.load_asset(TEX + "/T_Joy_EyeOption_" + kind)
        assert isinstance(tx, u.Texture2D), (kind, list(t.imported_object_paths))
        if kind == "Normal":
            tx.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_NORMALMAP)
            tx.set_editor_property("srgb", False)
            tx.set_editor_property("flip_green_channel", True)
        else:
            tx.set_editor_property("srgb", True)
        assert L.save_loaded_asset(tx, False), kind
        tex[kind] = tx
    eye_path = B + "/MI_Joy_EyeOption"
    eye = u.load_asset(eye_path) if L.does_asset_exist(eye_path) else TOOLS.create_asset("MI_Joy_EyeOption", B, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
    master = u.load_asset(B + "/M_JoyBOpaque")
    E.set_material_instance_parent(eye, master)
    E.set_material_instance_texture_parameter_value(eye, "BaseColor", tex["BaseColor"])
    tex_params = [str(n) for n in E.get_texture_parameter_names(eye)]
    normal_param = next((n for n in tex_params if "normal" in n.lower()), None)
    if normal_param:
        E.set_material_instance_texture_parameter_value(eye, normal_param, tex["Normal"])
    E.set_material_instance_vector_parameter_value(eye, "Tint", u.LinearColor(1.0, 1.0, 1.0, 1.0))
    for k, v in (("Metallic", 0.0), ("Roughness", 0.18), ("Specular", 0.6), ("LuminanceTint", 0.0), ("SuitMix", 0.0)):
        E.set_material_instance_scalar_parameter_value(eye, k, v)
    E.update_material_instance(eye)
    assert L.save_loaded_asset(eye, False), eye_path
    report["MI_Joy_EyeOption"] = {"parent": master.get_path_name(), "texture_params": tex_params, "normal_param": normal_param,
                                  "textures": {k: v.get_path_name() for k, v in tex.items()}}
# Her pants' own fabric (owner 2026-10-14 night: "can her pants be a bit less reflective? no need for hyper shiny").
# The pack's master reads metallic straight from the ORM map's blue channel, 0.5 over all of the red fabric, with no
# parameter: a half-metal red with roughness 0.48 x the instance's multiplier is the foil look. A copy of the master in
# Joy's folder gets a MetallicScale on that channel (the pack's assets stay untouched), and her pants slot gets its own
# instance of it; the sneakers keep theirs.
if os.environ.get("SS_FABRIC_SLOT"):
    MASTER_SRC = "/Game/SciFi_PS_P02_UE5/Materials/SciFi_Base/M_Pants_Sneakers_p02_c3"
    MASTER = B + "/M_Joy_SciFiPants"
    if not L.does_asset_exist(MASTER):
        assert L.duplicate_asset(MASTER_SRC, MASTER), MASTER
    mat = u.load_asset(MASTER)
    assert isinstance(mat, u.Material), MASTER
    if "MetallicScale" not in [str(n) for n in E.get_scalar_parameter_names(mat)]:
        orm = E.get_material_property_input_node(mat, u.MaterialProperty.MP_METALLIC)
        assert isinstance(orm, u.MaterialExpressionTextureSample), orm
        assert str(E.get_material_property_input_node_output_name(mat, u.MaterialProperty.MP_METALLIC)) == "B"
        mul = E.create_material_expression(mat, u.MaterialExpressionMultiply, -260, 420)
        par = E.create_material_expression(mat, u.MaterialExpressionScalarParameter, -520, 520)
        par.set_editor_property("parameter_name", "MetallicScale")
        par.set_editor_property("default_value", 1.0)
        assert E.connect_material_expressions(orm, "B", mul, "A")
        assert E.connect_material_expressions(par, "", mul, "B")
        assert E.connect_material_property(mul, "", u.MaterialProperty.MP_METALLIC)
        E.recompile_material(mat)
    assert L.save_loaded_asset(mat, False), MASTER
    assert "MetallicScale" in [str(n) for n in E.get_scalar_parameter_names(mat)]
    pack_inst = u.load_asset(PACK + "/ML_Pants_Sneakers_p02_c3_Inst")
    fab_path = B + "/MI_Joy_PantsFabric"
    fab = u.load_asset(fab_path) if L.does_asset_exist(fab_path) else TOOLS.create_asset("MI_Joy_PantsFabric", B, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
    E.set_material_instance_parent(fab, mat)
    E.set_material_instance_texture_parameter_value(fab, "Skin_Texture", E.get_material_instance_texture_parameter_value(pack_inst, "Skin_Texture"))
    E.set_material_instance_vector_parameter_value(fab, "Color", u.LinearColor(TINT[0], TINT[1], TINT[2], 0.0))
    E.set_material_instance_scalar_parameter_value(fab, "Emissive", E.get_material_instance_scalar_parameter_value(pack_inst, "Emissive"))
    for k, env, dflt in (("Roughness", "SS_FABRIC_ROUGHNESS", 1.25), ("MetallicScale", "SS_FABRIC_METALLIC", 0.15), ("Specular", "SS_FABRIC_SPECULAR", 0.5)):
        E.set_material_instance_scalar_parameter_value(fab, k, float(os.environ.get(env, dflt)))
    E.update_material_instance(fab)
    assert L.save_loaded_asset(fab, False), fab_path
    mesh = u.load_asset(B.rsplit("/", 1)[0] + "/Mesh/SK_Joy")
    slots = list(mesh.materials)
    before = {str(x.material_slot_name): (x.material_interface.get_name() if x.material_interface else None) for x in slots}
    hit = 0
    for i, x in enumerate(slots):
        if str(x.material_slot_name) == os.environ["SS_FABRIC_SLOT"]:
            x.set_editor_property("material_interface", fab)
            slots[i] = x
            hit += 1
    assert hit == 1, ("slot", os.environ["SS_FABRIC_SLOT"], list(before))
    mesh.set_editor_property("materials", slots)
    assert L.save_loaded_asset(mesh, False)
    report["MI_Joy_PantsFabric"] = {"parent": MASTER, "slot": os.environ["SS_FABRIC_SLOT"], "slots_before": before,
                                    "scalars": {str(p): E.get_material_instance_scalar_parameter_value(fab, p) for p in E.get_scalar_parameter_names(fab)}}
jk = u.load_asset("/Game/Jacket_1/Materials/MI_Jacket")
report["MI_Jacket"] = {"scalars": {str(p): E.get_material_instance_scalar_parameter_value(jk, p) for p in E.get_scalar_parameter_names(jk)},
                       "textures": {str(p): (E.get_material_instance_texture_parameter_value(jk, p).get_name() if E.get_material_instance_texture_parameter_value(jk, p) else None) for p in E.get_texture_parameter_names(jk)}}
u.log_warning("OUTFITMAT| DONE " + json.dumps(report))
