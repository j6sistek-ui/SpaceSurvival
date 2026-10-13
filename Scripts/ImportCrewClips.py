"""Import Blender-authored clips (one FBX each) onto a crew character's existing skeleton, into its Role/ folder.

  set SS_CLIPS_WHO=Cyborg  SS_CLIPS_DIR=<folder with Cyborg_PoleIdle.fbx ...>   [SS_CLIPS_MATCH=Pole]
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/ImportCrewClips.py"

<Who>_<Clip>.fbx becomes TripoCrew/<Who>/Role/A_<Who>_<Clip>. The clips come out of
Scripts/TripoCrewBlender/pole/pole_dance.py (centimetre export, bones unscaled) and go through the legacy FBX
path onto SK_<Who>'s skeleton - the same route ImportTripoCrew.py uses for the octopus clips, because Interchange
rebinds the skin to a take's first frame. A retarget run (AuthorTripoCrew.py) deletes nothing under Role/, so
these survive a crew rebuild; a rerun here replaces them.
"""
import glob
import os

import unreal as u

L = u.EditorAssetLibrary
WHO, SRC = os.environ["SS_CLIPS_WHO"], os.environ["SS_CLIPS_DIR"]
MATCH = os.environ.get("SS_CLIPS_MATCH", "")
CREW = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew"
RIG_FOLDER = {"Abyss", "Ember", "Crest", "Olive", "Elf", "Cyborg"}  # see ImportTripoCrew.py


def line(s):
    u.log_warning("CREWCLIPS| " + str(s))


mesh = L.load_asset("%s/%s/%s/SK_%s" % (CREW, WHO, "Rig" if WHO in RIG_FOLDER else "Mesh", WHO))
assert isinstance(mesh, u.SkeletalMesh), "no skeletal mesh for " + WHO
skeleton = mesh.get_editor_property("skeleton")
dest = "%s/%s/Role" % (CREW, WHO)
if not L.does_directory_exist(dest):
    L.make_directory(dest)
u.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
made, failed = [], []
for fbx in sorted(glob.glob(os.path.join(SRC, "%s_*.fbx" % WHO))):
    clip = os.path.basename(fbx)[len(WHO) + 1:-4]
    if MATCH and MATCH not in clip:
        continue
    name = "A_%s_%s" % (WHO, clip)
    if L.does_asset_exist(dest + "/" + name):
        L.delete_asset(dest + "/" + name)
    ui = u.FbxImportUI()
    for prop, value in (("import_mesh", False), ("import_animations", True), ("import_as_skeletal", True),
                        ("import_materials", False), ("import_textures", False), ("skeleton", skeleton),
                        ("mesh_type_to_import", u.FBXImportType.FBXIT_ANIMATION),
                        ("original_import_type", u.FBXImportType.FBXIT_ANIMATION),
                        ("automated_import_should_detect_type", False)):
        ui.set_editor_property(prop, value)
    task = u.AssetImportTask()
    for prop, value in (("filename", fbx), ("destination_path", dest), ("destination_name", name), ("automated", True),
                        ("replace_existing", True), ("save", True), ("options", ui)):
        task.set_editor_property(prop, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    a = L.load_asset(dest + "/" + name)
    if isinstance(a, u.AnimSequence):
        made.append("%s %.2fs" % (name, a.get_play_length()))
    else:
        failed.append(name)
line("%s: %d clips imported %s; failed %s" % (WHO, len(made), made, failed))
