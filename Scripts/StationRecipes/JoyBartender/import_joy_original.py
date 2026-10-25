"""Import the original Joy as SK_Joy on the skeleton the light-blue Joy already uses, with her bartender look.

  set SS_JOY_EXPORT=<dir written by export_joy_original.py + paint_outfit.py>
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/import_joy_original.py"

Mirrors .agent/local/StationRefinement/Lineup92/import_joy.py (the route that imported the first Joy) with three
differences: the FBX is bound to /JoyPurple/Mesh/SK_JoyPurple_Skeleton so every A_Joy_* clip, IK_Joy and RTG_CyborgToJoy
apply to her at once; textures that already exist under JoyPurple/Textures are reused rather than imported twice
(only the painted body diffuse, the strap mask, the vest, bottoms and hair maps are new); and the materials carry the
owner's look of 2026-10-14 - original skin tone, the vest closed and restyled gold-metallic, the bottoms styled dark like
pants, hot pink stylised hair, a glossy strap. Fresh-create only: DEST must not exist.
"""
import json
import os
from pathlib import Path

import unreal as u

EXP = Path(os.environ["SS_JOY_EXPORT"])
DATA = json.loads((EXP / "Export.json").read_text())
PAINT = json.loads((EXP / "Paint.json").read_text()) if (EXP / "Paint.json").exists() else {"painted": {}, "masks": {}}
DEST = "/Game/SpaceSurvival/Licensed/StationAssets/JoyBartender"
JOYP = "/Game/SpaceSurvival/Licensed/StationAssets/JoyPurple"
SKEL = JOYP + "/Mesh/SK_JoyPurple_Skeleton"
MESH_NAME = "SK_Joy"  # not SK_JoyLightBlue / SK_JoyPurple: those alias to the talk name "Cyan"
TOOLS = u.AssetToolsHelpers.get_asset_tools()
EDIT = u.MaterialEditingLibrary
L = u.EditorAssetLibrary
REPORT = {"created": []}

# the look (owner 2026-10-14): gold vest, pants-dark bottoms, hot pink hair, original skin, glossy strap
STYLE = {
    "FS_waistcoat": {"kind": "Opaque", "LuminanceTint": 1.0, "Tint": (0.95, 0.70, 0.20), "Metallic": 0.85, "Roughness": 0.30},
    "Underwear_Bottoms": {"kind": "Masked", "LuminanceTint": 1.0, "Tint": (0.06, 0.06, 0.07), "Metallic": 0.25, "Roughness": 0.35},
    "ShortStraight_Transparency": {"kind": "Masked", "LuminanceTint": 1.0, "Tint": (1.8, 0.12, 0.85), "Metallic": 0.0, "Roughness": 0.45},  # hot pink, over 1 to lift the dark cards
}
SUIT = {"SuitRoughness": 0.30, "SuitMetallic": 0.20}


def log(s):
    u.log_warning("JOYIMPORT| " + str(s))


def save(asset):
    assert L.save_loaded_asset(asset, False), asset.get_path_name()
    REPORT["created"].append(asset.get_path_name())


def task(file, folder, name, options=None, factory=None):
    t = u.AssetImportTask()
    for k, v in dict(filename=str(file), destination_path=folder, destination_name=name, automated=True, replace_existing=False, save=False).items():
        t.set_editor_property(k, v)
    if options:
        t.set_editor_property("options", options)
    if factory:
        t.set_editor_property("factory", factory)
    return t


def import_body():
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    assert not L.does_directory_exist(DEST), "Fresh-create only: " + DEST
    skeleton = u.load_asset(SKEL)
    assert isinstance(skeleton, u.Skeleton), SKEL
    options = u.FbxImportUI()
    for k, v in dict(automated_import_should_detect_type=False, mesh_type_to_import=u.FBXImportType.FBXIT_SKELETAL_MESH, import_as_skeletal=True,
                     import_mesh=True, import_animations=False, import_materials=False, import_textures=False, create_physics_asset=False,
                     skeleton=skeleton).items():
        options.set_editor_property(k, v)
    for k, v in dict(import_uniform_scale=1.0, convert_scene=True, convert_scene_unit=True, force_front_x_axis=False, use_t0_as_ref_pose=False,
                     preserve_smoothing_groups=True, import_morph_targets=True, normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS).items():
        options.skeletal_mesh_import_data.set_editor_property(k, v)
    t = task(DATA["fbx"]["path"], DEST + "/Mesh", MESH_NAME, options, u.FbxFactory())
    TOOLS.import_asset_tasks([t])
    paths = list(t.imported_object_paths)
    meshes = [u.load_asset(p) for p in paths if isinstance(u.load_asset(p), u.SkeletalMesh)]
    assert len(meshes) == 1, paths
    mesh = meshes[0]
    assert mesh.skeleton.get_path_name() == skeleton.get_path_name(), mesh.skeleton.get_path_name()
    comp = u.SkeletalMeshComponent()
    comp.set_skeletal_mesh_asset(mesh)
    b = mesh.get_bounds()
    REPORT["body"] = {"mesh": mesh.get_path_name(), "skeleton": mesh.skeleton.get_path_name(), "bones": comp.get_num_bones(),
                      "height_cm": b.box_extent.z * 2, "morphs": len(mesh.get_all_morph_target_names()) if hasattr(mesh, "get_all_morph_target_names") else -1,
                      "slots": [str(s.material_slot_name) for s in mesh.materials]}
    log(REPORT["body"])
    assert REPORT["body"]["bones"] == 101, REPORT["body"]["bones"]
    return mesh


def textures():
    """Reuse JoyPurple's identical maps; import what is new (painted body diffuse, strap mask, vest, bottoms, hair)."""
    painted = {v["diffuse"] for v in PAINT["painted"].values()}
    tex = {}
    tasks, rows = [], []
    for row in DATA["images"]:
        existing = JOYP + "/Textures/" + row["name"]
        if row["path"] not in painted and L.does_asset_exist(existing):
            tex[row["name"]] = u.load_asset(existing)
            continue
        tasks.append(task(row["path"], DEST + "/Textures", row["name"]))
        rows.append(row)
    for m in PAINT["masks"].values():
        tasks.append(task(m["path"], DEST + "/Textures", m["name"]))
        rows.append({"name": m["name"], "srgb": False, "mask": True})
    TOOLS.import_asset_tasks(tasks)
    for row, t in zip(rows, tasks):
        values = [u.load_asset(p) for p in t.imported_object_paths]
        assert len(values) == 1 and isinstance(values[0], u.Texture2D), row["name"]
        tx = values[0]
        tx.set_editor_property("srgb", row["srgb"])
        if row["name"].endswith("_Normal"):
            tx.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_NORMALMAP)
            tx.set_editor_property("flip_green_channel", True)
        if row.get("mask"):
            tx.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_MASKS)
        save(tx)
        tex[row["name"]] = tx
    REPORT["textures"] = {"reused": [k for k in tex if tex[k].get_path_name().startswith(JOYP)], "imported": [r["name"] for r in rows]}
    return tex


def master(name, blend, mask_default):
    mat = TOOLS.create_asset(name, DEST + "/Materials", u.Material, u.MaterialFactoryNew())
    assert mat
    mat.set_editor_property("blend_mode", blend)
    mat.set_editor_property("two_sided", True)
    mat.set_editor_property("used_with_skeletal_mesh", True)
    # SK_Joy carries morph targets (ST_* soft-tissue springs every tick, CC face keys): without this flag a morphed
    # section draws the default checker material in Play (2026-10-15; fix_joy_material_usage.py repairs saved masters)
    mat.set_editor_property("used_with_morph_targets", True)

    def node(cls, param=None):
        n = EDIT.create_material_expression(mat, cls)
        if param:
            n.set_editor_property("parameter_name", param)
            n.set_editor_property("group", "Joy source material")
        return n

    def conn(a, out, b, p):
        assert EDIT.connect_material_expressions(a, out, b, p), (a, b, p)

    def prop(a, out, p):
        assert EDIT.connect_material_property(a, out, p)

    white = u.load_asset("/Engine/EngineResources/WhiteSquareTexture")
    tex = node(u.MaterialExpressionTextureSampleParameter2D, "BaseColor")
    tex.set_editor_property("texture", white)
    color = node(u.MaterialExpressionVectorParameter, "Tint")
    color.set_editor_property("default_value", u.LinearColor(1, 1, 1, 1))
    lum = node(u.MaterialExpressionDotProduct)
    coeff = node(u.MaterialExpressionConstant3Vector)
    coeff.set_editor_property("constant", u.LinearColor(.2126, .7152, .0722, 1))
    conn(tex, "RGB", lum, "A")
    conn(coeff, "", lum, "B")
    choice = node(u.MaterialExpressionLinearInterpolate)
    use = node(u.MaterialExpressionScalarParameter, "LuminanceTint")
    use.set_editor_property("default_value", 0.)
    conn(tex, "RGB", choice, "A")
    conn(lum, "", choice, "B")
    conn(use, "", choice, "Alpha")
    mul = node(u.MaterialExpressionMultiply)
    conn(choice, "", mul, "A")
    conn(color, "", mul, "B")
    prop(mul, "", u.MaterialProperty.MP_BASE_COLOR)
    normal = node(u.MaterialExpressionTextureSampleParameter2D, "Normal")
    normal.set_editor_property("texture", u.load_asset("/Engine/EngineMaterials/DefaultNormal"))
    normal.set_editor_property("sampler_type", u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    prop(normal, "RGB", u.MaterialProperty.MP_NORMAL)
    # the painted strap: a mask lerps roughness and metallic toward the suit values (SuitMix 0 = no effect)
    # A Masks sampler must default to a TC_MASKS texture: the engine's white square is sRGB and the mismatch is a
    # material COMPILE ERROR that drops every instance to the fallback (she rendered pure white, 2026-10-14).
    mask = node(u.MaterialExpressionTextureSampleParameter2D, "SuitMask")
    mask.set_editor_property("texture", mask_default)
    mask.set_editor_property("sampler_type", u.MaterialSamplerType.SAMPLERTYPE_MASKS)
    mix = node(u.MaterialExpressionScalarParameter, "SuitMix")
    mix.set_editor_property("default_value", 0.)
    amount = node(u.MaterialExpressionMultiply)
    conn(mask, "R", amount, "A")
    conn(mix, "", amount, "B")
    for pname, default, sname, sdefault, p in [("Roughness", .55, "SuitRoughness", SUIT["SuitRoughness"], u.MaterialProperty.MP_ROUGHNESS),
                                               ("Metallic", 0., "SuitMetallic", SUIT["SuitMetallic"], u.MaterialProperty.MP_METALLIC)]:
        base = node(u.MaterialExpressionScalarParameter, pname)
        base.set_editor_property("default_value", default)
        suit = node(u.MaterialExpressionScalarParameter, sname)
        suit.set_editor_property("default_value", sdefault)
        lerp = node(u.MaterialExpressionLinearInterpolate)
        conn(base, "", lerp, "A")
        conn(suit, "", lerp, "B")
        conn(amount, "", lerp, "Alpha")
        prop(lerp, "", p)
    spec = node(u.MaterialExpressionScalarParameter, "Specular")
    spec.set_editor_property("default_value", .5)
    prop(spec, "", u.MaterialProperty.MP_SPECULAR)
    if blend != u.BlendMode.BLEND_OPAQUE:
        opacity = node(u.MaterialExpressionTextureSampleParameter2D, "Opacity")
        opacity.set_editor_property("texture", white)
        alpha = node(u.MaterialExpressionScalarParameter, "Alpha")
        alpha.set_editor_property("default_value", 1.)
        m = node(u.MaterialExpressionMultiply)
        conn(opacity, "R", m, "A")
        conn(alpha, "", m, "B")
        prop(m, "", u.MaterialProperty.MP_OPACITY_MASK if blend == u.BlendMode.BLEND_MASKED else u.MaterialProperty.MP_OPACITY)
    EDIT.recompile_material(mat)
    save(mat)
    return mat


def materials(mesh, tex):
    masks = [tex[m["name"]] for m in PAINT["masks"].values() if m["name"] in tex]
    assert masks, "a painted mask texture is needed as the Masks sampler default"
    parents = {k: master("M_JoyB" + k, v, masks[0]) for k, v in [("Opaque", u.BlendMode.BLEND_OPAQUE), ("Masked", u.BlendMode.BLEND_MASKED), ("Translucent", u.BlendMode.BLEND_TRANSLUCENT)]}
    assigned = {}
    for row in DATA["materials"]:
        name = row["name"]
        style = STYLE.get(name, {})
        if "kind" in style:
            kind = style["kind"]
        elif name == "Std_Eyelash":
            kind = "Masked"
        elif row["alpha"] < .999 or row["alpha_linked"]:
            kind = "Translucent"
        else:
            kind = "Opaque"
        mi = TOOLS.create_asset(row["unreal_name"], DEST + "/Materials", u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        assert mi, row["unreal_name"]
        EDIT.set_material_instance_parent(mi, parents[kind])
        for key, tname in row["textures"].items():
            if key == "Opacity" and kind == "Opaque":
                continue
            assert tname in tex, tname
            EDIT.set_material_instance_texture_parameter_value(mi, key, tex[tname])
        tint = style.get("Tint") or (row["base_color"][:3] if not row["base_color_linked"] else [1, 1, 1])
        EDIT.set_material_instance_vector_parameter_value(mi, "Tint", u.LinearColor(*tint, 1))
        spec = min(1., ((row["ior"] - 1) / (row["ior"] + 1)) ** 2 * 2 * row["specular_ior_level"] / .08)
        scalars = {"LuminanceTint": style.get("LuminanceTint", 0.), "Metallic": style.get("Metallic", row["metallic"]),
                   "Roughness": style.get("Roughness", row["roughness"]), "Specular": spec, "Alpha": row["alpha"]}
        if name in PAINT["masks"]:
            EDIT.set_material_instance_texture_parameter_value(mi, "SuitMask", tex[PAINT["masks"][name]["name"]])
            scalars["SuitMix"] = 1.
            scalars.update(SUIT)
        for k, v in scalars.items():
            EDIT.set_material_instance_scalar_parameter_value(mi, k, float(v))
        save(mi)
        assigned[name] = mi
    slots = list(mesh.materials)
    for i, s in enumerate(slots):
        sname = str(s.material_slot_name)
        assert sname in assigned, sname
        s.set_editor_property("material_interface", assigned[sname])
        slots[i] = s
    mesh.set_editor_property("materials", slots)
    save(mesh)
    REPORT["materials"] = {k: v.get_path_name() for k, v in assigned.items()}


mesh = import_body()
tex = textures()
materials(mesh, tex)
(EXP / "Import.json").write_text(json.dumps(REPORT, indent=2))
log("DONE " + json.dumps({"mesh": REPORT["body"]["mesh"], "bones": REPORT["body"]["bones"], "height": REPORT["body"]["height_cm"], "slots": len(REPORT["body"]["slots"]), "imported_textures": len(REPORT["textures"]["imported"]), "reused": len(REPORT["textures"]["reused"])}))
