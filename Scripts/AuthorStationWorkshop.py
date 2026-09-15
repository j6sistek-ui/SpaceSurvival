"""Create ten original workshop materials once; preserve later owner edits.
Run inside the installed Unreal editor Python commandlet. No vendor asset is edited.
"""
from pathlib import Path
import hashlib
import json
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
BASE = "/Game/SpaceSurvival/Licensed/StationWorkshop/Materials"
PRESETS = (
    ("Steel", (0.40, 0.45, 0.48), 0.95, 0.30, 0.0),
    ("Dark steel", (0.045, 0.060, 0.080), 0.85, 0.42, 0.0),
    ("Painted white", (0.72, 0.75, 0.77), 0.15, 0.48, 0.0),
    ("Copper", (0.55, 0.23, 0.075), 0.95, 0.30, 0.0),
    ("Caution yellow", (0.85, 0.51, 0.025), 0.05, 0.48, 0.0),
    ("Rubber", (0.016, 0.020, 0.024), 0.0, 0.88, 0.0),
    ("Glass", (0.15, 0.32, 0.40), 0.0, 0.12, 0.0),
    ("Cyan light", (0.035, 0.50, 0.80), 0.10, 0.30, 3.0),
    ("Amber light", (0.85, 0.32, 0.025), 0.10, 0.30, 3.0),
    ("Red light", (0.80, 0.035, 0.015), 0.10, 0.30, 3.0),
)


def create_master(name, glass=False):
    lib, edit = u.EditorAssetLibrary, u.MaterialEditingLibrary
    path = BASE + "/" + name
    if lib.does_asset_exist(path):
        return lib.load_asset(path)
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(name, BASE, u.Material, u.MaterialFactoryNew())
    assert material, path
    if glass:
        material.set_editor_property("blend_mode", u.BlendMode.BLEND_TRANSLUCENT)
        material.set_editor_property("two_sided", True)
    color = edit.create_material_expression(material, u.MaterialExpressionVectorParameter, -600, -200)
    color.set_editor_property("parameter_name", "Tint")
    color.set_editor_property("default_value", u.LinearColor(.4, .4, .4, 1))
    edit.connect_material_property(color, "", u.MaterialProperty.MP_BASE_COLOR)
    for name, value, prop, y in (("Metallic", .8, u.MaterialProperty.MP_METALLIC, 0),
                                  ("Roughness", .35, u.MaterialProperty.MP_ROUGHNESS, 160)):
        node = edit.create_material_expression(material, u.MaterialExpressionScalarParameter, -600, y)
        node.set_editor_property("parameter_name", name)
        node.set_editor_property("default_value", value)
        edit.connect_material_property(node, "", prop)
    glow = edit.create_material_expression(material, u.MaterialExpressionScalarParameter, -600, 320)
    glow.set_editor_property("parameter_name", "Glow")
    glow.set_editor_property("default_value", 0.0)
    multiply = edit.create_material_expression(material, u.MaterialExpressionMultiply, -300, 240)
    edit.connect_material_expressions(color, "", multiply, "A")
    edit.connect_material_expressions(glow, "", multiply, "B")
    edit.connect_material_property(multiply, "", u.MaterialProperty.MP_EMISSIVE_COLOR)
    if glass:
        opacity = edit.create_material_expression(material, u.MaterialExpressionScalarParameter, -600, 480)
        opacity.set_editor_property("parameter_name", "Opacity")
        opacity.set_editor_property("default_value", .22)
        edit.connect_material_property(opacity, "", u.MaterialProperty.MP_OPACITY)
    edit.recompile_material(material)
    assert lib.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def main():
    lib, edit = u.EditorAssetLibrary, u.MaterialEditingLibrary
    lib.make_directory(BASE)
    surface = create_master("M_WorkshopSurface")
    glass = create_master("M_WorkshopGlass", True)
    rows = []
    for i, (label, tint, metallic, roughness, glow) in enumerate(PRESETS, 1):
        name = f"MI_Workshop_{i:02d}"
        path = BASE + "/" + name
        exists = lib.does_asset_exist(path)
        if not exists:
            instance = u.AssetToolsHelpers.get_asset_tools().create_asset(name, BASE, u.MaterialInstanceConstant,
                                                                         u.MaterialInstanceConstantFactoryNew())
            assert instance, path
            edit.set_material_instance_parent(instance, glass if label == "Glass" else surface)
            edit.set_material_instance_vector_parameter_value(instance, "Tint", u.LinearColor(*tint, 1))
            for key, value in (("Metallic", metallic), ("Roughness", roughness), ("Glow", glow)):
                edit.set_material_instance_scalar_parameter_value(instance, key, value)
            lib.set_metadata_tag(instance, "WorkshopLabel", label)
            assert lib.save_loaded_asset(instance, only_if_is_dirty=False)
        disk = ROOT / "Content" / (path[len("/Game/"):] + ".uasset")
        rows.append(dict(label=label, asset=path, preserved=exists,
                         sha256=hashlib.sha256(disk.read_bytes()).hexdigest()))
    result = u.SSStationLayoutAuthoringLibrary.open_station_workshop()
    success, message = result if isinstance(result, tuple) else (bool(result), str(result))
    assert success, message
    receipt = ROOT / ".agent/local/StationWorkshop/Preparation.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(dict(engine=u.SystemLibrary.get_engine_version(), materials=rows,
                                       workshop=message), indent=2) + "\n", encoding="utf-8")
    u.log("STATION_WORKSHOP_PREPARED " + str(receipt))


if __name__ == "__main__":
    main()
