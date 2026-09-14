"""Read-only Havolk mesh bounds/materials and built-LOD FBX export for the visual pass.

Run under the integration lead's existing Unreal workflow after privately staging
Spacecraft_Pack at its original /Game path. Never saves or edits vendor assets.
"""
import hashlib
import json
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Artifacts/ShipVisualPass/Source"
BASE = "/Game/Spacecraft_Pack/Static_Meshes"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    rows = []
    for path in sorted(u.EditorAssetLibrary.list_assets(BASE, recursive=True, include_folder=False)):
        mesh = u.load_asset(path)
        if not isinstance(mesh, u.StaticMesh):
            continue
        target = OUT / (mesh.get_name() + ".fbx")
        options = u.FbxExportOption()
        for key, value in {"ascii": False, "level_of_detail": False, "collision": False,
                           "export_source_mesh": False, "vertex_color": True}.items():
            options.set_editor_property(key, value)
        task = u.AssetExportTask()
        for key, value in {"object": mesh, "filename": str(target), "automated": True,
                           "prompt": False, "replace_identical": True,
                           "exporter": u.StaticMeshExporterFBX(), "options": options}.items():
            task.set_editor_property(key, value)
        assert u.Exporter.run_asset_export_task(task) and target.is_file(), path
        bounds = mesh.get_bounds()
        rows.append({"path": mesh.get_path_name(), "name": mesh.get_name(),
                     "origin_cm": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
                     "extent_cm": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z],
                     "lod_count": editor.get_lod_count(mesh),
                     "materials": [slot.material_interface.get_path_name() if slot.material_interface else None
                                   for slot in mesh.static_materials],
                     "fbx": target.name, "fbx_sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    assert len(rows) >= 30, "Full Havolk pack was not staged"
    report = {"engine": u.SystemLibrary.get_engine_version(), "assets": rows,
              "status": "READ_ONLY_SOURCE_EXPORT_NOT_APPEARANCE_ACCEPTANCE"}
    (OUT / "Inventory.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    u.log("SHIP_VISUAL_SOURCE_EXPORT_OK " + str(len(rows)))


if __name__ == "__main__":
    main()
