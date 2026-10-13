"""Re-import a crew character's textures in place, keeping its material instance exactly as it is.

  set SS_TEX_WHO=Cyborg  SS_TEX_DIR=<folder of T_Cyborg_*.png>
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/ReimportCrewTextures.py"

For a mesh whose UVs changed (the 2026-10-12 optimisation bakes the character's maps into a fresh layout): every
T_<Who>_*.png in the folder replaces the texture of the same name in TripoCrew/<Who>/Mat, with the settings
ImportCrewMaterial.py uses (BaseColor sRGB; Normal as a normal map with the green channel flipped, the PNG being
a Blender/OpenGL +Y bake; everything else a linear mask). The material instance is not touched, so whichever
texture it already pointed at, tuned ones included, keeps its name and gets the new pixels.
"""
import os

import unreal as u

L = u.EditorAssetLibrary
TOOLS = u.AssetToolsHelpers.get_asset_tools()
WHO, SRC = os.environ["SS_TEX_WHO"], os.environ["SS_TEX_DIR"]
FOLDER = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/%s/Mat" % WHO


def line(s):
    u.log_warning("CREWTEX| " + str(s))


done = []
for name in sorted(os.listdir(SRC)):
    if not (name.startswith("T_%s_" % WHO) and name.lower().endswith(".png")):
        continue
    stem = name[:-4]
    path = FOLDER + "/" + stem
    existed = L.does_asset_exist(path)
    t = u.AssetImportTask()
    t.filename = os.path.join(SRC, name)
    t.destination_path = FOLDER
    t.destination_name = stem
    t.automated = True
    t.replace_existing = True
    t.save = False
    TOOLS.import_asset_tasks([t])
    tex = L.load_asset(path)
    assert isinstance(tex, u.Texture2D), "texture import failed: " + name
    kind = stem[len("T_%s_" % WHO):]
    tex.set_editor_property("virtual_texture_streaming", False)
    if kind == "BaseColor":
        tex.set_editor_property("srgb", True)
        tex.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_DEFAULT)
    elif kind == "Normal":
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property("flip_green_channel", True)
    else:
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_MASKS)
    L.save_loaded_asset(tex, False)
    done.append("%s %dx%d %s" % (stem, tex.blueprint_get_size_x(), tex.blueprint_get_size_y(),
                                 "replaced" if existed else "NEW"))
line("%s: %s" % (WHO, "; ".join(done)))
assert done, "no T_%s_*.png in %s" % (WHO, SRC)
