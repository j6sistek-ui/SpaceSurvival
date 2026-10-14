"""Author parked-only collision from measured Phoenix interior triangles.

Default dry-run. The integration lead supplies a successful ProbePhoenixCockpit
receipt in .agent/local/SurvivalQuality/PhoenixCockpit. -SSApplyPhoenixCockpitCollision
writes only a private static mesh after backup; original assets/maps stay unchanged.
This script does not launch Unreal or assert that a character can traverse the result.
"""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
INPUT = ROOT / ".agent/local/SurvivalQuality/PhoenixCockpit"
OUT = ROOT / "Artifacts/PhoenixPresentation/CockpitCollision"
TARGET = "/Game/SpaceSurvival/Licensed/PhoenixPresentation/SM_PhoenixParkedInterior"
PARTS = {"Interior_Mesh", "Interior_Mesh_001", "Cockpit_Mesh",
         "Interiro_Doors_L_Mesh", "Interiro_Doors_R_Mesh"}


def path(package):
    return ROOT / "Content" / (package.removeprefix("/Game/").split(".")[0] + ".uasset")


def digest(file):
    return hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else None


def main():
    apply = "-SSApplyPhoenixCockpitCollision" in u.SystemLibrary.get_command_line()
    proof = json.loads((INPUT / "Probe.json").read_text(encoding="utf-8"))
    data = json.loads((INPUT / "PhoenixLanded.json").read_text(encoding="utf-8"))
    assert proof["success"] and all(proof["originals_preserved"].values()), "Probe did not pass"
    original = proof["source_sha256"]
    assert all(digest(path(name)) == value for name, value in original.items()), "Probe assets changed"
    assert data["pose_bone_mapping"] and data["yaw"] == -90 and data["scale"] == 1
    assert data["seconds"] > 1 and data["mesh"] == "/Game/Stellar_Phoenix/Spaceship/Meshes/Stellar_Phoenix"
    vertices, triangles, bones = data["vertices"], data["triangles"], data["vertex_bones"]
    retained = [i for i, row in enumerate(triangles) if all(bones[j] in PARTS for j in row)]
    assert 5000 < len(retained) < 16000, "Interior triangle population changed; inspect before authoring"
    used = {index for i in retained for index in triangles[i]}
    lo = [min(vertices[index][axis] for index in used) for axis in range(3)]
    hi = [max(vertices[index][axis] for index in used) for axis in range(3)]
    assert -1150 < lo[0] < -1100 and 1030 < hi[0] < 1060 and 135 < lo[2] < 150 and 650 < hi[2] < 670
    current = digest(path(TARGET))
    prior_file = OUT / "apply.json"
    prior = json.loads(prior_file.read_text()) if prior_file.is_file() else None
    if current:
        assert prior and prior["output_sha256"] == current, "Private mesh edited or unowned; refusing overwrite"
    report = {"utc": datetime.now(timezone.utc).isoformat(), "apply": apply, "target": TARGET,
              "source_sha256": original, "geometry_sha256": digest(INPUT / "PhoenixLanded.json"),
              "retained_triangles": len(retained), "source_triangles": len(triangles),
              "parts": sorted(PARTS), "bounds_min": lo, "bounds_max": hi,
              "collision": "parked query-only complex-as-simple; no rendered component or flight hull change",
              "success": False}
    OUT.mkdir(parents=True, exist_ok=True)
    if apply:
        if current:
            backup = OUT / ("SM_PhoenixParkedInterior-" + current + ".uasset")
            if not backup.exists():
                shutil.copy2(path(TARGET), backup)
        mesh = u.load_asset(data["mesh"])
        dynamic = u.DynamicMesh()
        options = u.GeometryScriptCopyMeshFromAssetOptions(apply_build_settings=False)
        lod = u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.SOURCE_MODEL, lod_index=0)
        _, outcome = u.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(mesh, dynamic, options, lod)
        assert outcome == u.GeometryScriptOutcomePins.SUCCESS
        _, copied_triangles, gaps = u.GeometryScript_MeshQueries.get_all_triangle_indices(dynamic, False)
        copied = u.GeometryScript_List.convert_triangle_list_to_array(copied_triangles)
        assert not gaps and [[int(t.x), int(t.y), int(t.z)] for t in copied] == triangles, "Source topology changed"
        positions = u.GeometryScript_List.convert_array_to_vector_list([u.Vector(*value) for value in vertices])
        u.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(dynamic, positions)
        selected = set(retained)
        deleted = [i for i in range(len(triangles)) if i not in selected]
        index_list = u.GeometryScript_List.convert_array_to_index_list(deleted)
        _, count = u.GeometryScript_MeshEdits.delete_triangles_from_mesh(dynamic, index_list)
        assert count == len(deleted) and dynamic.get_triangle_count() == len(retained)
        if current:
            target = u.load_asset(TARGET)
            _, outcome = u.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(
                dynamic, target, u.GeometryScriptCopyMeshToAssetOptions(), u.GeometryScriptMeshWriteLOD())
        else:
            target, outcome = u.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
                dynamic, TARGET, u.GeometryScriptCreateNewStaticMeshAssetOptions(enable_nanite=False))
        assert target and outcome == u.GeometryScriptOutcomePins.SUCCESS, "Private collision mesh creation failed"
        subsystem = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
        subsystem.remove_collisions(target)
        target.set_editor_property("lod_for_collision", 0)
        target.set_editor_property("complex_collision_mesh", None)
        body = target.get_editor_property("body_setup")
        body.set_editor_property("collision_trace_flag", u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        body.set_editor_property("double_sided_geometry", True)
        for section in range(target.get_num_sections(0)):
            subsystem.enable_section_collision(target, True, 0, section)
        assert u.EditorAssetLibrary.save_loaded_asset(target, only_if_is_dirty=False)
        assert subsystem.get_collision_complexity(target) == u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
        report["output_sha256"] = digest(path(TARGET))
    report["originals_preserved"] = {name: digest(path(name)) == value for name, value in original.items()}
    assert all(report["originals_preserved"].values()), "Original asset changed"
    report["success"] = True
    (OUT / ("apply.json" if apply else "dry-run.json")).write_text(json.dumps(report, indent=2), encoding="utf-8")
    u.log("PHOENIX_COCKPIT_COLLISION_COMPLETE " + str(apply) + " " + str(len(retained)))


main()
