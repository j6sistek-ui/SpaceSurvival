"""Build one crew material instance from a character's own PBR PNG set (export_glb_textures.py) on the Tripo master.

  set SS_MAT_WHO=Cyborg  SS_MAT_SLOT=CyborgBody  SS_MAT_TEX_DIR=<folder with T_Cyborg_BaseColor.png ...>
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/ImportCrewMaterial.py"

Textures land in TripoCrew/<Who>/Mat as T_<Who>_BaseColor (sRGB), _Normal (normal map, green flipped: the PNG is
glTF/OpenGL +Y), _Roughness and _Metallic (linear masks); MI_<Slot> parents M_Tripo_PBR_Master, whose four
texture parameters are the only inputs it takes (no emissive). ImportTripoCrew.py assigns it by slot name
through MATERIAL_SLOTS. Re-running replaces the textures and the instance.
"""
import os

import unreal as u

L = u.EditorAssetLibrary; MEL = u.MaterialEditingLibrary; TOOLS = u.AssetToolsHelpers.get_asset_tools()
WHO, SLOT, SRC = os.environ["SS_MAT_WHO"], os.environ["SS_MAT_SLOT"], os.environ["SS_MAT_TEX_DIR"]
FOLDER = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/%s/Mat" % WHO
MASTER = "/Game/TripoModels/Materials/M_Tripo_PBR_Master"


def imp(name, srgb, comp, flip_green=False):
    t = u.AssetImportTask(); t.filename = os.path.join(SRC, name + ".png"); t.destination_path = FOLDER
    t.destination_name = name; t.automated = True; t.replace_existing = True; t.save = False
    TOOLS.import_asset_tasks([t])
    tex = L.load_asset(FOLDER + "/" + name)
    assert isinstance(tex, u.Texture2D), "texture import failed: " + name
    # a 4K PNG auto-imports as a virtual texture, and the master samples plain Texture2D: assigning a VT to it fails
    tex.set_editor_property("virtual_texture_streaming", False)
    tex.set_editor_property("srgb", srgb); tex.set_editor_property("compression_settings", comp)
    if flip_green:
        tex.set_editor_property("flip_green_channel", True)
    L.save_loaded_asset(tex, False)
    return tex


if not L.does_directory_exist(FOLDER):
    L.make_directory(FOLDER)
base = imp("T_%s_BaseColor" % WHO, True, u.TextureCompressionSettings.TC_DEFAULT)
normal = imp("T_%s_Normal" % WHO, False, u.TextureCompressionSettings.TC_NORMALMAP, flip_green=True)
rough = imp("T_%s_Roughness" % WHO, False, u.TextureCompressionSettings.TC_MASKS)
metal = imp("T_%s_Metallic" % WHO, False, u.TextureCompressionSettings.TC_MASKS)
path = "%s/MI_%s" % (FOLDER, SLOT)
if L.does_asset_exist(path):
    L.delete_asset(path)
mi = TOOLS.create_asset("MI_" + SLOT, FOLDER, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
MEL.set_material_instance_parent(mi, L.load_asset(MASTER))
WANT = (("BaseColorTex", base), ("NormalTex", normal), ("RoughnessTex", rough), ("MetallicTex", metal))
for pname, tex in WANT:
    # the return value is not the test (it read False here while the value was stored); the read-back below is
    MEL.set_material_instance_texture_parameter_value(mi, pname, tex)
MEL.update_material_instance(mi); L.save_loaded_asset(mi, False)
got = {str(n): MEL.get_material_instance_texture_parameter_value(mi, n) for n in MEL.get_texture_parameter_names(mi)}
bad = [p for p, t in WANT if got.get(p) != t]
assert not bad, "parameters not taken on %s: %s (have %s)" % (path, bad, {k: v.get_name() if v else None for k, v in got.items()})
u.log_warning("CREWMAT| %s -> %s (%dx%d base colour)" % (SLOT, path, base.blueprint_get_size_x(), base.blueprint_get_size_y()))
