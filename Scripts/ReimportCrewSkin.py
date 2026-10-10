"""Re-import a crew character's skinned mesh onto its EXISTING skeleton, keeping every clip that references it.

  set SS_SKIN_WHO=Cyborg  SS_SKIN_FBX=<abs path to Cyborg.fbx from Scripts/TripoCrewBlender/export_for_unreal.py>
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/ReimportCrewSkin.py"

For skin-weight repairs (2026-10-10: the Cyborg's flank tore when her arm was raised; Cyborg_Claude/rig/
reweight_flank.py). ImportTripoCrew.py deletes the Rig folder and makes a new skeleton, which would orphan the ~140
retargeted and authored clips; this goes through the legacy FBX path with the existing skeleton set, so the mesh is
replaced in place and the skeleton is untouched. The material slots are restored from what the mesh had before.
"""
import os

import unreal as u

L = u.EditorAssetLibrary
WHO, FBX = os.environ["SS_SKIN_WHO"], os.environ["SS_SKIN_FBX"]
CREW = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew"
RIG_FOLDER = {"Abyss", "Ember", "Crest", "Olive", "Elf", "Cyborg"}  # see ImportTripoCrew.py
FOLDER = "%s/%s/%s" % (CREW, WHO, "Rig" if WHO in RIG_FOLDER else "Mesh")


def line(s):
    u.log_warning("CREWSKIN| " + str(s))


mesh = L.load_asset("%s/SK_%s" % (FOLDER, WHO))
assert isinstance(mesh, u.SkeletalMesh), "no skeletal mesh for " + WHO
skeleton = mesh.get_editor_property("skeleton")
before = {str(s.get_editor_property("material_slot_name")): s.get_editor_property("material_interface")
          for s in mesh.get_editor_property("materials")}
bones_before = mesh.get_editor_property("skeleton").get_path_name()
line("%s before: skeleton %s, slots %s" % (WHO, bones_before, {k: (v.get_name() if v else None) for k, v in before.items()}))

u.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
ui = u.FbxImportUI()
for prop, value in (("import_mesh", True), ("import_as_skeletal", True), ("import_animations", False),
                    ("import_materials", False), ("import_textures", False), ("create_physics_asset", False),
                    ("mesh_type_to_import", u.FBXImportType.FBXIT_SKELETAL_MESH), ("skeleton", skeleton)):
    ui.set_editor_property(prop, value)
ui.get_editor_property("skeletal_mesh_import_data").set_editor_property("import_morph_targets", False)
ui.get_editor_property("skeletal_mesh_import_data").set_editor_property("convert_scene", True)
task = u.AssetImportTask()
for prop, value in (("filename", FBX), ("destination_path", FOLDER), ("destination_name", "SK_" + WHO),
                    ("automated", True), ("replace_existing", True), ("save", True), ("options", ui)):
    task.set_editor_property(prop, value)
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
u.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 1")

mesh = L.load_asset("%s/SK_%s" % (FOLDER, WHO))
assert isinstance(mesh, u.SkeletalMesh), "re-import failed for " + WHO
slots = list(mesh.get_editor_property("materials"))
for slot in slots:
    name = str(slot.get_editor_property("material_slot_name"))
    if before.get(name):
        slot.set_editor_property("material_interface", before[name])
mesh.set_editor_property("materials", slots)
L.save_loaded_asset(mesh, only_if_is_dirty=False)

after = mesh.get_editor_property("skeleton").get_path_name()
mats = {str(s.get_editor_property("material_slot_name")): (s.get_editor_property("material_interface").get_name()
        if s.get_editor_property("material_interface") else None) for s in mesh.get_editor_property("materials")}
clips = [a for a in L.list_assets("%s/%s" % (CREW, WHO), recursive=True) if "/A_" in a]
mismatched = [c for c in clips if L.find_asset_data(c).get_asset() and isinstance(L.find_asset_data(c).get_asset(), u.AnimSequence)
              and L.find_asset_data(c).get_asset().get_editor_property("skeleton").get_path_name() != after]
line("%s after: skeleton %s (%s), slots %s, %d clips, %d on another skeleton, %.1f cm tall"
     % (WHO, after, "UNCHANGED" if after == bones_before else "CHANGED", mats, len(clips), len(mismatched),
        2 * mesh.get_imported_bounds().box_extent.z))
