"""Import owned FBX clip packs onto the UE4 mannequin skeleton the Tripo crew retargets from.

  set SS_CLIPLIB_SOURCE=<folder of anim-only FBX files>   set SS_CLIPLIB_NAME=<library name, e.g. Merchant>
  optional: SS_CLIPLIB_SKELETON=<skeleton asset path>   (default: UE4 mannequin)
            SS_CLIPLIB_FILES=<name,name,...>            (search SOURCE recursively, first file per name wins)
            SS_CLIPLIB_WITH_MESH=1                      (SOURCE is ONE fbx carrying its own skinned mesh and many
                                                         takes, e.g. Bar Counter People: mesh, new skeleton and
                                                         every take are imported together; unset or 0 = off)
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/ImportStationClipLibrary.py"

Clips land in OUT/<name>/ and nothing in any pack folder is written. The skeleton is MCO_Mocap_Basics'
UE4_Mannequin_Skeleton, the source side of every RTG_<Name> made by AuthorTripoCrew.py, so a clip imported here
retargets onto any crew member without a new IK rig.

The legacy FBX path is forced on: Interchange ignores FbxImportUI, and with automated type detection on, an
animation-only FBX is imported as a skeletal mesh.
"""
import glob
import os

import unreal as u

OUT = "/Game/SpaceSurvival/Licensed/StationAssets/ClipLibrary"
SKELETON = "/Game/MCO_Mocap_Basics/Character/Mesh/UE4_Mannequin_Skeleton"
LIB = u.EditorAssetLibrary


def line(s):
    u.log_warning("CLIPLIB| " + str(s))


def import_with_mesh(fbx, dest):
    # Before anything is deleted: a folder SOURCE (or a stale =1 left in the shell) must not empty the library.
    assert os.path.isfile(fbx), "SS_CLIPLIB_WITH_MESH needs SOURCE to be one FBX file, got: " + fbx
    # Over an existing mesh Unreal runs a re-import, which keeps the mesh and silently drops every take.
    for path in LIB.list_assets(dest, recursive=False, include_folder=False):
        LIB.delete_asset(path.split(".")[0])
    ui = u.FbxImportUI()
    for prop, value in (("import_mesh", True), ("import_animations", True), ("import_as_skeletal", True),
                        ("import_materials", False), ("import_textures", False), ("create_physics_asset", False),
                        ("mesh_type_to_import", u.FBXImportType.FBXIT_SKELETAL_MESH),
                        ("automated_import_should_detect_type", False)):
        ui.set_editor_property(prop, value)
    ui.get_editor_property("anim_sequence_import_data").set_editor_property(
        "animation_length", u.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    task = u.AssetImportTask()
    for prop, value in (("filename", fbx), ("destination_path", dest), ("automated", True),
                        ("replace_existing", True), ("save", True), ("options", ui)):
        task.set_editor_property(prop, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    # task "save" writes only the primary asset; the new skeleton and every take stay in memory unless saved here
    LIB.save_directory(dest, only_if_is_dirty=False, recursive=True)
    reg = u.AssetRegistryHelpers.get_asset_registry()
    found = [(str(d.asset_class_path.asset_name), str(d.asset_name)) for d in reg.get_assets_by_path(dest, recursive=False)]
    anims = sorted(n for c, n in found if c == "AnimSequence")
    meshes = sorted(n for c, n in found if c == "SkeletalMesh")
    line("  meshes %s" % meshes)
    line("  %d takes, e.g. %s" % (len(anims), anims[:3]))
    return anims


def main():
    source = os.environ["SS_CLIPLIB_SOURCE"]
    name = os.environ["SS_CLIPLIB_NAME"]
    skel_path = os.environ.get("SS_CLIPLIB_SKELETON", SKELETON)
    if "/Game/" in skel_path and not skel_path.startswith("/Game/"):
        skel_path = skel_path[skel_path.index("/Game/"):]  # Git Bash rewrites /Game/... into a Windows path
    skeleton = LIB.load_asset(skel_path)
    assert isinstance(skeleton, u.Skeleton), "skeleton missing: " + skel_path
    dest = "%s/%s" % (OUT, name)
    if not LIB.does_directory_exist(dest):
        LIB.make_directory(dest)
    u.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
    if os.environ.get("SS_CLIPLIB_WITH_MESH", "0").strip() not in ("", "0"):   # by value, like SS_POST
        anims = import_with_mesh(source, dest)
        u.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 1")
        line("DONE %s: %d takes with mesh" % (name, len(anims)))
        return
    made, failed = [], []
    # Windows globbing is case-insensitive, so *.fbx and *.FBX return the same files: de-duplicate by path.
    wanted = [w.strip() for w in os.environ.get("SS_CLIPLIB_FILES", "").split(",") if w.strip()]
    if wanted:
        found = {}
        for dirpath, _, names in sorted(os.walk(source)):
            for n in names:
                base, ext = os.path.splitext(n)
                if ext.lower() == ".fbx" and base in wanted and base not in found:
                    found[base] = os.path.join(dirpath, n)
        for w in wanted:
            if w not in found:
                failed.append("%s -> not found under source" % w)
        files = {os.path.normcase(v): v for v in found.values()}
    else:
        files = {os.path.normcase(p): p for p in glob.glob(os.path.join(source, "*.fbx")) + glob.glob(os.path.join(source, "*.FBX"))}
    for fbx in sorted(files.values()):
        clip = os.path.splitext(os.path.basename(fbx))[0]
        ui = u.FbxImportUI()
        for prop, value in (("import_mesh", False), ("import_animations", True), ("import_as_skeletal", True),
                            ("import_materials", False), ("import_textures", False), ("skeleton", skeleton),
                            ("mesh_type_to_import", u.FBXImportType.FBXIT_ANIMATION),
                            ("original_import_type", u.FBXImportType.FBXIT_ANIMATION),
                            ("automated_import_should_detect_type", False)):
            ui.set_editor_property(prop, value)
        task = u.AssetImportTask()
        for prop, value in (("filename", fbx), ("destination_path", dest), ("destination_name", clip),
                            ("automated", True), ("replace_existing", True), ("save", True), ("options", ui)):
            task.set_editor_property(prop, value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        asset = LIB.load_asset(dest + "/" + clip)
        if isinstance(asset, u.AnimSequence):
            made.append("%s %.2fs" % (clip, asset.get_play_length()))
        else:
            failed.append("%s -> %s" % (clip, type(asset).__name__))
    u.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 1")
    for m in made:
        line("  " + m)
    for f in failed:
        line("  FAILED " + f)
    line("DONE %s: %d clips, %d failed" % (name, len(made), len(failed)))


main()
