"""Import the generated distant panorama and author a camera-direction sky material.

The source bitmap stays unchanged. Unreal resamples to 2048x1024 for streamed mips;
this changes presentation only, with no scene geometry/collision or lighting actors.
"""
import hashlib
import json
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
BASE = "/Game/SpaceSurvival"
VERSION = "EquirectangularPanorama1"


def author():
    library = u.EditorAssetLibrary
    source = ROOT / "ContentSource/Textures/SpacePanorama-v1.png"
    manifest = json.loads(source.with_suffix(".json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != manifest["sha256"]:
        raise RuntimeError("Panorama source differs from its provenance manifest")
    texture_path = BASE + "/Textures/T_SpacePanorama_v1"
    library.make_directory(BASE + "/Textures")
    texture = library.load_asset(texture_path)
    if not texture:
        task = u.AssetImportTask()
        for key, value in {"filename": str(source), "destination_path": BASE + "/Textures",
                           "destination_name": "T_SpacePanorama_v1", "automated": True,
                           "replace_existing": False, "save": True}.items():
            task.set_editor_property(key, value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture = library.load_asset(texture_path)
        if not texture or not isinstance(texture, u.Texture2D):
            raise RuntimeError("Panorama import did not produce the expected Texture2D")
        texture.set_editor_property("srgb", True)
        texture.set_editor_property("lod_group", u.TextureGroup.TEXTUREGROUP_SKYBOX)
        texture.set_editor_property("power_of_two_mode", u.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO)
        texture.set_editor_property("mip_gen_settings", u.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE)
        texture.set_editor_property("address_x", u.TextureAddress.TA_WRAP)
        texture.set_editor_property("address_y", u.TextureAddress.TA_CLAMP)
        library.set_metadata_tag(texture, "SSAuthoringVersion", "1")
        library.set_metadata_tag(texture, "SSPanoramaSourceSHA256", digest)
        if not library.save_loaded_asset(texture, only_if_is_dirty=False):
            raise RuntimeError("Panorama texture save failed")
    if library.get_metadata_tag(texture, "SSPanoramaSourceSHA256") != digest:
        raise RuntimeError("Panorama requires a deliberate reviewed reimport")
    material = library.load_asset(BASE + "/Materials/M_Space")
    if not material:
        raise RuntimeError("Base palette must be authored before the panorama material")
    if library.get_metadata_tag(material, "SSPanoramaVersion") == VERSION and library.get_metadata_tag(material, "SSPanoramaSourceSHA256") == digest:
        return
    edit = u.MaterialEditingLibrary
    edit.delete_all_material_expressions(material)
    material.set_editor_property("shading_model", u.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)
    direction = edit.create_material_expression(material, u.MaterialExpressionCameraVectorWS, -900, 0)
    uv = edit.create_material_expression(material, u.MaterialExpressionCustom, -650, 0)
    uv.set_editor_property("description", "World direction to equirectangular UV, stable across travel")
    uv.set_editor_property("code", "float3 d = normalize(-Direction); return float2(atan2(d.y,d.x)*0.15915494309+0.5, acos(clamp(d.z,-1.0,1.0))*0.31830988618);")
    uv.set_editor_property("output_type", u.CustomMaterialOutputType.CMOT_FLOAT2)
    item = u.CustomInput()
    item.set_editor_property("input_name", "Direction")
    uv.set_editor_property("inputs", [item])
    sample = edit.create_material_expression(material, u.MaterialExpressionTextureSampleParameter2D, -400, 0)
    sample.set_editor_property("parameter_name", "SpacePanorama")
    sample.set_editor_property("texture", texture)
    tint = edit.create_material_expression(material, u.MaterialExpressionVectorParameter, -400, 240)
    tint.set_editor_property("parameter_name", "Tint")
    tint.set_editor_property("default_value", u.LinearColor(.6, .7, 1, 1))
    multiply = edit.create_material_expression(material, u.MaterialExpressionMultiply, -140, 0)
    intensity = edit.create_material_expression(material, u.MaterialExpressionScalarParameter, -140, 240)
    intensity.set_editor_property("parameter_name", "SkyIntensity")
    intensity.set_editor_property("default_value", 2.0)
    output = edit.create_material_expression(material, u.MaterialExpressionMultiply, 100, 0)
    for src, pin, dst, input_pin in ((direction, "", uv, "Direction"), (uv, "", sample, "UVs"),
                                    (sample, "RGB", multiply, "A"), (tint, "", multiply, "B"),
                                    (multiply, "", output, "A"), (intensity, "", output, "B")):
        if not edit.connect_material_expressions(src, pin, dst, input_pin):
            raise RuntimeError(f"Panorama graph connection failed: {input_pin}")
    if not edit.connect_material_property(output, "", u.MaterialProperty.MP_EMISSIVE_COLOR):
        raise RuntimeError("Panorama emissive connection failed")
    edit.recompile_material(material)
    library.set_metadata_tag(material, "SSPanoramaVersion", VERSION)
    library.set_metadata_tag(material, "SSPanoramaSourceSHA256", digest)
    library.set_metadata_tag(material, "SSAuthoringVersion", "1")
    if not library.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError("Panorama material save failed")
    u.log("SS_PANORAMA imported and authored; runtime seam/readability approval remains open: " + digest)


if __name__ == "__main__":
    author()
