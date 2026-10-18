"""Import one Fab GLB (any path) as a single static mesh with its materials, the way ImportVaultGlb.py does for the
vault folder - for listings that landed in another vault (the Fab plugin's M: library).

  set SS_GLB=<path to .glb>  SS_NAME=<asset-safe listing name>
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/ImportFabGlbFile.py"

Lands at /Game/Fab/<Name>/SM_<Name> (GLB metres -> Interchange centimetres, no extra scale), box collision added
when the mesh has none. Re-running replaces it.
"""
import os

import unreal as u

LIB = u.EditorAssetLibrary
GLB, NAME = os.environ["SS_GLB"], os.environ["SS_NAME"]
BASE = "/Game/Fab"
target_dir = "%s/%s" % (BASE, NAME); name = "SM_%s" % NAME; target = "%s/%s" % (target_dir, name)


def line(s):
    u.log_warning("FABGLB| " + str(s))


if LIB.does_directory_exist(target_dir):
    for stale in LIB.list_assets(target_dir, recursive=True, include_folder=False):
        LIB.delete_asset(stale)
pipeline = u.new_object(u.InterchangeGenericAssetsPipeline, name="SSFabGlb_%s" % NAME)
for k, v in {"asset_name": name, "use_source_name_for_asset": False, "asset_type_sub_folders": False, "scene_name_sub_folder": False}.items():
    pipeline.set_editor_property(k, v)
common = pipeline.get_editor_property("common_meshes_properties")
common.set_editor_property("force_all_mesh_as_type", u.InterchangeForceMeshType.IFMT_STATIC_MESH)
mp = pipeline.get_editor_property("mesh_pipeline")
mp.set_editor_property("import_static_meshes", True)
mp.set_editor_property("combine_static_meshes_behavior", u.InterchangeCombineStaticMeshesBehavior.ALL)
mp.set_editor_property("import_skeletal_meshes", False)
pipeline.get_editor_property("animation_pipeline").set_editor_property("import_animations", False)
materials = pipeline.get_editor_property("material_pipeline")
materials.set_editor_property("import_materials", True)
materials.get_editor_property("texture_pipeline").set_editor_property("import_textures", True)
params = u.ImportAssetParameters()
params.set_editor_property("is_automated", True); params.set_editor_property("replace_existing", True)
params.set_editor_property("override_pipelines", [u.SoftObjectPath(pipeline.get_path_name())])
manager = u.InterchangeManager.get_interchange_manager_scripted()
assets = manager.import_asset(target_dir, manager.create_source_data(GLB), params)
meshes = [a for a in assets if isinstance(a, u.StaticMesh)]
line("imported %d assets, %d static meshes" % (len(assets), len(meshes)))
assert len(meshes) == 1, "expected one static mesh"
mesh = meshes[0]
if mesh.get_path_name().split(".")[0] != target:
    assert LIB.rename_asset(mesh.get_path_name(), target), "rename failed"
    mesh = u.load_asset(target)
empty = [str(s.material_slot_name) for s in mesh.static_materials if not s.material_interface]
b = mesh.get_bounds(); size = [round(b.box_extent.x * 2), round(b.box_extent.y * 2), round(b.box_extent.z * 2)]
editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
if editor.get_simple_collision_count(mesh) == 0:
    try:
        editor.add_simple_collisions(mesh, u.ScriptCollisionShapeType.BOX)
    except Exception as e:
        line("box collision not added (%s)" % e)
LIB.save_directory(target_dir, False, True)
line("DONE %s size cm %s slots %d empty %s" % (target, size, len(mesh.static_materials), empty))
