"""Joy's own instances of the sci-fi pants and sneaker materials (the pack's red, colour variant c3), tinted with the
pack's own 'Color' multiplier. Owner 2026-10-14: "make the red slightly more closer in color to her hair but not exact,
just a minor shift to make it more girly"; "not super hot pink, let me find a color sample". The pack's assets are
never edited: these are children in JoyBartender/Materials, created or updated in place.

  set SS_PANTS_TINT=r,g,b      (linear multiplier on the base colour; the pack's own value is 0.79,0.79,0.79)
  set SS_PANTS_ROUGHNESS=0.45  set SS_PANTS_SPECULAR=0.6   (optional; the pack ships 1.0 and 0.5)
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
jk = u.load_asset("/Game/Jacket_1/Materials/MI_Jacket")
report["MI_Jacket"] = {"scalars": {str(p): E.get_material_instance_scalar_parameter_value(jk, p) for p in E.get_scalar_parameter_names(jk)},
                       "textures": {str(p): (E.get_material_instance_texture_parameter_value(jk, p).get_name() if E.get_material_instance_texture_parameter_value(jk, p) else None) for p in E.get_texture_parameter_names(jk)}}
u.log_warning("OUTFITMAT| DONE " + json.dumps(report))
