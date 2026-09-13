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
VERSION = "EquirectangularStarless3"


def author():
    library = u.EditorAssetLibrary
    source = ROOT / "ContentSource/Textures/SpacePanorama-starless-v2.png"
    manifest = json.loads(source.with_suffix(".json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != manifest["sha256"]:
        raise RuntimeError("Panorama source differs from its provenance manifest")
    texture_path = BASE + "/Textures/T_SpacePanorama_starless_v2"
    library.make_directory(BASE + "/Textures")
    texture = library.load_asset(texture_path)
    if not texture:
        task = u.AssetImportTask()
        for key, value in {"filename": str(source), "destination_path": BASE + "/Textures",
                           "destination_name": "T_SpacePanorama_starless_v2", "automated": True,
                           "replace_existing": False, "save": True}.items():
            task.set_editor_property(key, value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture = library.load_asset(texture_path)
        if not texture or not isinstance(texture, u.Texture2D):
            raise RuntimeError("Panorama import did not produce the expected Texture2D")
        texture.set_editor_property("srgb", True)
        texture.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_BC7)
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
    texture_object = edit.create_material_expression(material, u.MaterialExpressionTextureObjectParameter, -900, 240)
    texture_object.set_editor_property("parameter_name", "SpacePanorama")
    texture_object.set_editor_property("texture", texture)
    sample = edit.create_material_expression(material, u.MaterialExpressionCustom, -600, 0)
    sample.set_editor_property("description", "Starless nebula with continuous wrap and quiet poles; stars are separate geometry")
    # Tilt distant nebula into the upper chase view. Blend opposite border samples
    # only within nine degrees of the wrap; equal edge values remove a bitmap seam.
    sample.set_editor_property("code", """
float3 d = normalize(-Direction);
const float tilt = 0.471238898;
d = float3(d.x*cos(tilt)-d.z*sin(tilt), d.y, d.x*sin(tilt)+d.z*cos(tilt));
float2 uv = float2(frac(atan2(d.y,d.x)*0.15915494309+0.2), acos(clamp(d.z,-1.0,1.0))*0.31830988618);
float seamBlend = 0.5*(1.0-smoothstep(0.0,0.025,min(uv.x,1.0-uv.x)));
float3 nebula = lerp(Texture2DSample(Panorama,PanoramaSampler,uv).rgb,
                     Texture2DSample(Panorama,PanoramaSampler,float2(1.0-uv.x,uv.y)).rgb,seamBlend);
float poleBlend = smoothstep(0.0,0.035,min(uv.y,1.0-uv.y));
return lerp(float3(0.0001,0.00015,0.0003),nebula,poleBlend);
""")
    sample.set_editor_property("output_type", u.CustomMaterialOutputType.CMOT_FLOAT3)
    inputs = []
    for name in ("Direction", "Panorama"):
        item = u.CustomInput()
        item.set_editor_property("input_name", name)
        inputs.append(item)
    sample.set_editor_property("inputs", inputs)
    tint = edit.create_material_expression(material, u.MaterialExpressionVectorParameter, -400, 240)
    tint.set_editor_property("parameter_name", "Tint")
    tint.set_editor_property("default_value", u.LinearColor(.6, .7, 1, 1))
    # Keep slow region tint changes subtle so the distant sky stays subordinate
    # to ship silhouettes and hazard warnings rather than becoming saturated magenta.
    neutral = edit.create_material_expression(material, u.MaterialExpressionConstant3Vector, -400, 420)
    neutral.set_editor_property("constant", u.LinearColor(1, 1, 1, 1))
    region_tint = edit.create_material_expression(material, u.MaterialExpressionLinearInterpolate, -220, 240)
    region_tint.set_editor_property("const_alpha", 0.25)
    multiply = edit.create_material_expression(material, u.MaterialExpressionMultiply, -140, 0)
    intensity = edit.create_material_expression(material, u.MaterialExpressionScalarParameter, -140, 240)
    intensity.set_editor_property("parameter_name", "SkyIntensity")
    intensity.set_editor_property("default_value", 0.8)
    output = edit.create_material_expression(material, u.MaterialExpressionMultiply, 100, 0)
    for src, pin, dst, input_pin in ((direction, "", sample, "Direction"), (texture_object, "", sample, "Panorama"),
                                    (sample, "", multiply, "A"), (region_tint, "", multiply, "B"),
                                    (neutral, "", region_tint, "A"), (tint, "", region_tint, "B"),
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
