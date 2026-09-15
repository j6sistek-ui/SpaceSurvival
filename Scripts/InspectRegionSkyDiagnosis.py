"""Read-only comparison of the black custom sky and working NebulaFantasy sky.

Integration lead runs in the full Unreal editor. No graph changes, texture setting
changes, recompile, asset save, render or GPU export are performed. The only write
is Artifacts/VisualPass/RegionSkyDiagnosis.json. Source min/max reads CPU pixels.
"""
import json
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
EDIT = u.MaterialEditingLibrary
LIB = u.EditorAssetLibrary
BASE = "/Game/SpaceSurvival/Licensed/Atmosphere"
VENDOR = "/Game/SpaceNebulaFantasy"


def value(v):
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, u.Object):
        return v.get_path_name()
    if isinstance(v, (list, tuple)):
        return [value(x) for x in v]
    for fields in (("r", "g", "b", "a"), ("x", "y", "z")):
        if all(hasattr(v, f) for f in fields):
            return {f: value(getattr(v, f)) for f in fields}
    return str(v)


def call(obj, names, *args):
    """Keep API naming differences or unavailable editor data in the receipt."""
    errors = {}
    for name in names:
        method = getattr(obj, name, None)
        if not callable(method):
            continue
        try:
            return {"api": name, "result": value(method(*args))}
        except Exception as exc:
            errors[name] = str(exc)
    return {"unavailable": list(names), "errors": errors}


def properties(obj, names):
    result = {}
    for name in names:
        try:
            result[name] = value(obj.get_editor_property(name))
        except Exception:
            pass  # Different expression classes expose different subsets.
    return result


def texture(path):
    tex = LIB.load_asset(path)
    if not tex:
        return {"path": path, "loaded": False}
    return {
        "path": tex.get_path_name(), "class": tex.get_class().get_name(),
        "settings": properties(tex, (
            "srgb", "compression_settings", "compression_no_alpha",
            "compression_none", "defer_compression", "max_texture_size",
            "lod_bias", "lod_group", "mip_gen_settings", "filter",
            "never_stream", "virtual_texture_streaming", "power_of_two_mode",
            "adjust_brightness", "adjust_brightness_curve", "adjust_saturation",
            "adjust_vibrance", "adjust_min_alpha", "adjust_max_alpha",
            "source_color_settings", "downscale", "downscale_options")),
        "built_size": call(tex, ("blueprint_get_built_texture_size", "get_built_texture_size")),
        "gpu_memory_bytes": call(tex, ("blueprint_get_memory_size", "get_memory_size")),
        "source_sizes_bytes": call(tex, ("blueprint_get_texture_source_disk_and_memory_size",
                                         "get_texture_source_disk_and_memory_size")),
        "source_id": call(tex, ("blueprint_get_texture_source_id_string", "get_texture_source_id_string")),
        "source_channel_min_max": call(tex, ("compute_texture_source_channel_min_max",)),
        "streaming_method": call(tex, ("get_texture_streaming_method",)),
    }


def graph(material):
    nodes = []
    for node in EDIT.get_material_expressions(material):
        names = list(EDIT.get_material_expression_input_names(node))
        inputs = list(EDIT.get_inputs_for_material_expression(material, node))
        nodes.append({
            "name": node.get_name(), "class": node.get_class().get_name(),
            "settings": properties(node, (
                "parameter_name", "default_value", "texture", "sampler_type",
                "sampler_source", "mip_value_mode", "const_mip_value",
                "automatic_view_mip_bias", "const_coordinate", "const_a",
                "const_b", "const_alpha", "r", "constant", "luminance_factors",
                "transform_source_type", "transform_type", "material_function",
                "code", "output_type", "a", "b", "alpha", "input", "fraction",
                "coordinates", "texture_object", "outputs")),
            "inputs": [{"pin": str(names[i]) if i < len(names) else str(i),
                        "node": source.get_name() if source else None,
                        "output": call(EDIT, ("get_input_node_output_name_for_material_expression",),
                                       node, source) if source else None}
                       for i, source in enumerate(inputs)],
            "output_names": value(list(EDIT.get_material_expression_output_names(node))),
        })
    return nodes


def material(path):
    mat = LIB.load_asset(path)
    if not mat:
        return {"path": path, "loaded": False}
    result = {"path": mat.get_path_name(), "class": mat.get_class().get_name(),
              "settings": properties(mat, ("parent", "shading_model", "shading_models",
                  "blend_mode", "material_domain", "two_sided", "is_sky",
                  "use_material_attributes", "opacity_mask_clip_value",
                  "disable_depth_test", "base_property_overrides")), "parameters": {}}
    instance = isinstance(mat, u.MaterialInstanceConstant)
    for kind in ("scalar", "vector", "texture", "static_switch"):
        getter = "get_material_instance_" + kind + "_parameter_value" if instance else (
            "get_material_default_" + kind + "_parameter_value")
        names = getattr(EDIT, "get_" + kind + "_parameter_names")(mat)
        result["parameters"][kind] = {str(n): call(EDIT, (getter,), mat, n) for n in names}
    if isinstance(mat, u.Material):
        result["graph"] = graph(mat)
        result["emissive"] = {
            "node": call(EDIT, ("get_material_property_input_node",), mat,
                         u.MaterialProperty.MP_EMISSIVE_COLOR),
            "output": call(EDIT, ("get_material_property_input_node_output_name",), mat,
                           u.MaterialProperty.MP_EMISSIVE_COLOR)}
    return result


def main():
    pairs = [
        (VENDOR + "/Textures/Skybox_8/T_Nebula_Turquoise_Dark_8", BASE + "/T_Region_Skybox_8"),
        (VENDOR + "/Textures/Skybox_6/T_Nebula_Orange_6", BASE + "/T_Region_Skybox_6"),
        (VENDOR + "/Textures/Skybox_1/T_Nebula_Blue_1", BASE + "/T_Region_Skybox_1"),
        (VENDOR + "/Textures/Starfields/T_Stars_Far_White", BASE + "/T_RegionStars"),
    ]
    receipt = {
        "status": "READ_ONLY_DIAGNOSIS_NOT_RENDERED_VALIDATION",
        "engine": u.SystemLibrary.get_engine_version(),
        "materials": [material(p) for p in (
            VENDOR + "/Materials/M_Skybox_Nebula",
            VENDOR + "/Material_instances/MI_Skybox_Nebula_8", BASE + "/M_RegionSky")],
        "texture_pairs": [{"vendor": texture(a), "duplicate": texture(b)} for a, b in pairs],
        "asset_writes": False,
    }
    look = LIB.load_asset(BASE + "/DA_DeepSpaceLook")
    receipt["look"] = properties(look, ("sky_material", "region_skies", "region_stars",
                                        "region_seconds")) if look else None
    out = ROOT / "Artifacts/VisualPass/RegionSkyDiagnosis.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    u.log("REGION_SKY_READ_ONLY_DIAGNOSIS " + str(out))


if __name__ == "__main__":
    main()
