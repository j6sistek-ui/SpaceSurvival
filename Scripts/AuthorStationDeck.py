"""Import the attributed CC0 deck maps and author a floor-only PBR material.

Source bitmaps remain byte-identical. No displacement, geometry or collision edits.
The 50 cm repeat is fitted to the existing 535 x 435 cm decorative floor panels.
"""
import hashlib
import json
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ContentSource/ThirdParty/PolyHaven/MetalPlate"
BASE = "/Game/SpaceSurvival"
MATERIAL = BASE + "/Materials/M_StationDeck"
VERSION = "MetalPlate1"
NAMES = {"diff": "T_StationDeck_Color", "arm": "T_StationDeck_ARM", "nor_dx": "T_StationDeck_Normal"}


def source_manifest():
    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["license"] == "CC0-1.0"
    assert {row["kind"] for row in manifest["maps"]} == set(NAMES)
    for row in manifest["maps"]:
        path = SOURCE / row["file"]
        data = path.read_bytes()
        assert len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == row["sha256"], str(path)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        assert int.from_bytes(data[16:20], "big") == row["width"] == 2048
        assert int.from_bytes(data[20:24], "big") == row["height"] == 2048
    return manifest


def author():
    manifest = source_manifest()
    library = u.EditorAssetLibrary
    edit = u.MaterialEditingLibrary
    tools = u.AssetToolsHelpers.get_asset_tools()
    textures = {}
    library.make_directory(BASE + "/Textures")
    compression = {"diff": u.TextureCompressionSettings.TC_BC7,
                   "arm": u.TextureCompressionSettings.TC_MASKS,
                   "nor_dx": u.TextureCompressionSettings.TC_NORMALMAP}
    for row in manifest["maps"]:
        kind = row["kind"]
        path = BASE + "/Textures/" + NAMES[kind]
        texture = library.load_asset(path) if library.does_asset_exist(path) else None
        if not texture:
            task = u.AssetImportTask()
            for key, value in {"filename": str(SOURCE / row["file"]), "destination_path": BASE + "/Textures",
                               "destination_name": NAMES[kind], "automated": True, "replace_existing": False,
                               "save": False}.items():
                task.set_editor_property(key, value)
            tools.import_asset_tasks([task])
            texture = library.load_asset(path)
            if not isinstance(texture, u.Texture2D):
                raise RuntimeError("Missing deck texture: " + path)
            texture.set_editor_property("srgb", kind == "diff")
            texture.set_editor_property("compression_settings", compression[kind])
            texture.set_editor_property("lod_group", u.TextureGroup.TEXTUREGROUP_WORLD_NORMAL_MAP if kind == "nor_dx" else u.TextureGroup.TEXTUREGROUP_WORLD)
            texture.set_editor_property("mip_gen_settings", u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
            texture.set_editor_property("address_x", u.TextureAddress.TA_WRAP)
            texture.set_editor_property("address_y", u.TextureAddress.TA_WRAP)
            library.set_metadata_tag(texture, "SSDeckSourceSHA256", row["sha256"])
            library.set_metadata_tag(texture, "SSAuthoringVersion", "1")
            if not library.save_loaded_asset(texture, only_if_is_dirty=False):
                raise RuntimeError("Deck texture save failed")
        if library.get_metadata_tag(texture, "SSDeckSourceSHA256") != row["sha256"]:
            raise RuntimeError("Deck map requires deliberate reviewed reimport: " + path)
        textures[kind] = texture

    source_key = hashlib.sha256("".join(row["sha256"] for row in manifest["maps"]).encode()).hexdigest()
    material = library.load_asset(MATERIAL) if library.does_asset_exist(MATERIAL) else None
    if material:
        if library.get_metadata_tag(material, "SSDeckVersion") == VERSION and library.get_metadata_tag(material, "SSDeckSourceKey") == source_key:
            return
        if library.get_metadata_tag(material, "SSAuthoringVersion") != "1":
            raise RuntimeError("Existing deck material is not owned by this authoring pipeline")
    else:
        material = tools.create_asset("M_StationDeck", BASE + "/Materials", u.Material, u.MaterialFactoryNew())
    if not material:
        raise RuntimeError("Deck material creation failed")
    edit.delete_all_material_expressions(material)
    material.set_editor_property("blend_mode", u.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("shading_model", u.MaterialShadingModel.MSM_DEFAULT_LIT)
    material.set_editor_property("used_with_instanced_static_meshes", True)

    def node(cls, x, y):
        return edit.create_material_expression(material, cls, x, y)

    def connect(source, output, target, pin):
        if not edit.connect_material_expressions(source, output, target, pin):
            raise RuntimeError("Deck graph connection failed: " + pin)

    def scalar(name, value, x, y):
        result = node(u.MaterialExpressionScalarParameter, x, y)
        result.set_editor_property("parameter_name", name)
        result.set_editor_property("default_value", value)
        return result

    uv = node(u.MaterialExpressionTextureCoordinate, -1100, 0)
    uv.set_editor_property("u_tiling", 10.7)
    uv.set_editor_property("v_tiling", 8.7)
    samples = {}
    for index, kind in enumerate(NAMES):
        sample = node(u.MaterialExpressionTextureSampleParameter2D, -850, index * 300)
        sample.set_editor_property("parameter_name", NAMES[kind])
        sample.set_editor_property("texture", textures[kind])
        sample.set_editor_property("sampler_type", {"diff": u.MaterialSamplerType.SAMPLERTYPE_COLOR,
                                                     "arm": u.MaterialSamplerType.SAMPLERTYPE_MASKS,
                                                     "nor_dx": u.MaterialSamplerType.SAMPLERTYPE_NORMAL}[kind])
        connect(uv, "", sample, "UVs")
        samples[kind] = sample

    desaturate = node(u.MaterialExpressionDesaturation, -520, 0)
    connect(samples["diff"], "RGB", desaturate, "")
    connect(scalar("Desaturation", .85, -800, -180), "", desaturate, "Fraction")
    tint = node(u.MaterialExpressionVectorParameter, -520, -180)
    tint.set_editor_property("parameter_name", "DeckTint")
    tint.set_editor_property("default_value", u.LinearColor(.45, .52, .60, 1))
    color = node(u.MaterialExpressionMultiply, -240, 0)
    connect(desaturate, "", color, "A")
    connect(tint, "", color, "B")
    normal_scale = node(u.MaterialExpressionConstant3Vector, -520, 780)
    normal_scale.set_editor_property("constant", u.LinearColor(.55, .55, 1, 1))
    normal_mult = node(u.MaterialExpressionMultiply, -240, 600)
    connect(samples["nor_dx"], "RGB", normal_mult, "A")
    connect(normal_scale, "", normal_mult, "B")
    normal = node(u.MaterialExpressionNormalize, 0, 600)
    connect(normal_mult, "", normal, "")
    for expression, output, prop in (
        (color, "", u.MaterialProperty.MP_BASE_COLOR),
        (samples["arm"], "R", u.MaterialProperty.MP_AMBIENT_OCCLUSION),
        (samples["arm"], "G", u.MaterialProperty.MP_ROUGHNESS),
        (samples["arm"], "B", u.MaterialProperty.MP_METALLIC),
        (normal, "", u.MaterialProperty.MP_NORMAL),
    ):
        if not edit.connect_material_property(expression, output, prop):
            raise RuntimeError("Deck material property connection failed")
    edit.recompile_material(material)
    for key, value in {"SSAuthoringVersion": "1", "SSDeckVersion": VERSION, "SSDeckSourceKey": source_key,
                       "SSAssetLicense": "CC0-1.0", "SSAssetSource": manifest["asset_url"],
                       "SSDeckRepeatCm": "50", "SSDeckPanelsCm": "535x435"}.items():
        library.set_metadata_tag(material, key, value)
    if not library.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError("Deck material save failed")
    u.log("SS_STATION_DECK_AUTHORED: source bitmaps preserved; visual review pending")


if __name__ == "__main__":
    author()
