"""Import the repaired Tripo crew meshes as new skeletal meshes with their own skeletons.

  set SS_TRIPOCREW_FBX=<folder holding Glyph.fbx, Olive.fbx, ...>
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/ImportTripoCrew.py"

The FBX files come out of a Blender pass that fixes what Tripo's auto-rig shipped:
  - every bone sat under an 'Armature' bone scaled x100 over a ~1-unit skeleton. The retargeter ignores
    that scale, so retargeted limbs collapsed to within a centimetre of the pelvis. The pass rebuilds
    the rest pose from the real joint positions at unit scale and removes the bone;
  - nine skeletons had no 'root' bone; one is added at the floor;
  - four characters (Glyph, Olive, Dread, Violet) had scrambled skin weights in Tripo's own export
    (fingertips weighted to the spine, a hand to a thigh), so they are re-weighted from the skeleton;
  - every character is scaled from Tripo's normalised 98 cm to 178 cm;
  - Kraken and Abyss get their own rig instead of biped clips: one 8-bone chain per tentacle (14 lower, 2 per
    arm), skin-geodesic weights, fused skin between tentacles removed, and procedural crawl/idle/turn clips
    with skin-level floor contact (Scripts/TripoCrewBlender/tentacles/);
  - Ember has four arms; the lower pair gets upperarm_low/lowerarm_low/hand_low bones under spine_02
    (Scripts/TripoCrewBlender/rig_lower_arms.py);
  - Cyan, Warden, Tribal and Amethyst arrived unrigged (static parts). They get a body-matched crew
    skeleton fitted to their bounds and fresh bone-heat weights (never weights copied from a donor).

Materials are not imported. Each slot is named after the Tripo material instance it used, so the
original textured instances under /Game/TripoModels are reassigned by name. Nothing there is written.

Elf and Cyborg (2026-10-08) are repaired base bodies delivered by the character-repair chat, already rigged and
weighted, with hand-restored roughness on their native materials. Their slots take the material instances off
the DELIVERED native meshes (MATERIAL_FROM), matched by slot name, so a re-import here never resets those
settings; nothing under CharacterRepairs_20261008 is written.
"""
import os

import unreal as u

OUT = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew"
LIB = u.EditorAssetLibrary
CREW = {
    "Glyph": "alien_creature_3d_model",
    "Olive": "alien_creature_3d_model_1",
    "Robe": "alien_creature_3d_model_2",
    "Finhead": "alien_creature_3d_model_3",
    "Tendril": "alien_humanoid_3d_model",
    "Dread": "alien_warrior_3d_model",
    "Seer": "alien_warrior_3d_model_1",
    "Ember": "demon_creature_3d_model",
    "Crest": "demonic_humanoid_3d_model",
    "Silver": "fantasy_elf_3d_model",
    "Violet": "purple_alien_cyborg_3d_model_Clone1",
    "Crystal": "sci-fi_alien_3d_model",
    "Cyan": "alien_female_3d_model",
    "Warden": "armored_humanoid_3d_model",
    "Tribal": "fantasy_creature_3d_model",
    "Amethyst": "fantasy_elf_3d_model_Clone1",
    "Kraken": "sci-fi_octopus_humanoid_3d_model",
    "Abyss": "sci-fi_octopus_humanoid_3d_model_Clone1",
    "Elf": "CharacterRepairs_20261008/Elf",
    "Cyborg": "CharacterRepairs_20261008/Cyborg",
}
REPAIRS = "/Game/SpaceSurvival/Licensed/CharacterRepairs_20261008"
MATERIAL_FROM = {"Elf": REPAIRS + "/Elf/SK_Fantasy_Elf", "Cyborg": REPAIRS + "/Cyborg/SK_Purple_Cyborg"}


OCTOPUS = {"Kraken", "Abyss"}
# Characters whose skeleton changed after a first import live in Rig/: a stale skeleton under Mesh/ cannot be
# deleted while older clips reference it, and Interchange silently reuses it, dropping the new bones.
RIG_FOLDER = OCTOPUS | {"Ember", "Crest", "Olive", "Elf"}


def line(s):
    u.log_warning("TRIPOIMPORT| " + str(s))


def import_clips(short, mesh, source):
    """The octopus pair's own procedural clips: one FBX per clip, imported onto the mesh's skeleton.

    Shipped in the mesh FBX instead, Interchange rebinds the skin to frame 0 of the first take and ignores
    FbxImportUI, so clips go through the legacy FBX path, one file each."""
    u.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
    base = "%s/%s/Clips" % (OUT, short)
    if not LIB.does_directory_exist(base):
        LIB.make_directory(base)
    # an earlier run left skeletal meshes under these names one folder up; they are not clips
    for clip in ("Crawl", "Idle", "TurnL", "TurnR"):
        stale = "%s/%s/A_%s_Tent%s" % (OUT, short, short, clip)
        if LIB.does_asset_exist(stale) and not isinstance(LIB.load_asset(stale), u.AnimSequence):
            line("%-8s removed stale mesh %s: %s" % (short, stale.rsplit("/", 1)[1], LIB.delete_asset(stale)))
    made = []
    for clip in ("Crawl", "Idle", "TurnL", "TurnR"):
        fbx = os.path.join(source, "%s_%s.fbx" % (short, clip))
        if not os.path.exists(fbx):
            line("%-8s clip file missing: %s" % (short, fbx)); continue
        name = "A_%s_Tent%s" % (short, clip)
        if LIB.does_asset_exist(base + "/" + name):
            LIB.delete_asset(base + "/" + name)
        ui = u.FbxImportUI()
        ui.set_editor_property("import_mesh", False)
        ui.set_editor_property("import_animations", True)
        ui.set_editor_property("import_as_skeletal", True)
        ui.set_editor_property("import_materials", False)
        ui.set_editor_property("import_textures", False)
        ui.set_editor_property("skeleton", mesh.get_editor_property("skeleton"))
        ui.set_editor_property("mesh_type_to_import", u.FBXImportType.FBXIT_ANIMATION)
        ui.set_editor_property("original_import_type", u.FBXImportType.FBXIT_ANIMATION)
        # left on, automated import "detects" these as skeletal meshes and writes a mesh instead of a clip
        ui.set_editor_property("automated_import_should_detect_type", False)
        task = u.AssetImportTask()
        for prop, value in (("filename", fbx), ("destination_path", base), ("destination_name", name),
                            ("automated", True), ("replace_existing", True), ("save", True), ("options", ui)):
            task.set_editor_property(prop, value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        clip_asset = LIB.load_asset(base + "/" + name)
        if isinstance(clip_asset, u.AnimSequence):
            made.append("%s %.2fs" % (name, clip_asset.get_play_length()))
        else:
            line("%-8s %s did not import as an animation (%s)" % (short, name, type(clip_asset).__name__))
    u.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 1")
    line("%-8s clips %s" % (short, made))


def import_one(short, folder, fbx):
    # The octopus pair lives in Rig/: an older 78-bone skeleton under Mesh/ could not be deleted and Interchange
    # silently reuses a skeleton found at the destination path, which drops all 144 tentacle bones.
    dest = "%s/%s/%s" % (OUT, short, "Rig" if short in RIG_FOLDER else "Mesh")
    if LIB.does_directory_exist(dest):
        LIB.delete_directory(dest)
    LIB.make_directory(dest)
    options = u.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_animations", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("create_physics_asset", False)
    options.set_editor_property("mesh_type_to_import", u.FBXImportType.FBXIT_SKELETAL_MESH)
    sk = options.get_editor_property("skeletal_mesh_import_data")
    sk.set_editor_property("import_morph_targets", False)
    sk.set_editor_property("convert_scene", True)
    task = u.AssetImportTask()
    for prop, value in (("filename", fbx), ("destination_path", dest), ("destination_name", "SK_" + short),
                        ("automated", True), ("replace_existing", True), ("save", True), ("options", options)):
        task.set_editor_property(prop, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = LIB.load_asset(dest + "/SK_" + short)
    if not isinstance(mesh, u.SkeletalMesh):
        line("%-8s IMPORT FAILED" % short)
        return None
    slots = list(mesh.get_editor_property("materials"))
    missing = []
    donor = {}
    if short in MATERIAL_FROM:
        key = lambda n: "".join(ch for ch in n.lower() if ch.isalnum())  # Blender ".002" arrives as "_002"
        for ds in LIB.load_asset(MATERIAL_FROM[short]).get_editor_property("materials"):
            donor[key(str(ds.get_editor_property("material_slot_name")))] = ds.get_editor_property("material_interface")
    for slot in slots:
        name = str(slot.get_editor_property("material_slot_name"))
        if short in MATERIAL_FROM:
            mi = donor.get(key(name))
        else:
            mi = LIB.load_asset("/Game/TripoModels/%s/%s" % (folder, name))
        if mi:
            slot.set_editor_property("material_interface", mi)
        else:
            missing.append(name)
    mesh.set_editor_property("materials", slots)
    LIB.save_loaded_asset(mesh, only_if_is_dirty=False)
    skeleton = mesh.get_editor_property("skeleton")
    bounds = mesh.get_imported_bounds().box_extent
    if short in OCTOPUS:
        import_clips(short, mesh, os.path.dirname(fbx))
    line("%-8s %5.1f cm tall  %2d slots  %d unmatched %s  skeleton=%s" % (
        short, 2 * bounds.z, len(slots), len(missing), missing[:3], skeleton.get_name() if skeleton else None))
    return mesh


def main():
    source = os.environ["SS_TRIPOCREW_FBX"]
    only = os.environ.get("SS_TRIPOCREW_ONLY")
    made = 0
    for short, folder in CREW.items():
        if only and short not in only.split(","):
            continue
        fbx = os.path.join(source, short + ".fbx")
        if not os.path.exists(fbx):
            line("%-8s no FBX at %s" % (short, fbx))
            continue
        if import_one(short, folder, fbx):
            made += 1
    line("DONE %d imported" % made)


main()
