"""Inspect staged Megastructure_Scifi_World without saving vendor assets.

Run with -ExecutePythonScript in the installed editor (not the Python commandlet,
which lacks StaticMeshEditorSubsystem); metadata is not visual acceptance.
"""
import json
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Artifacts/Megastructure"


def main():
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    mesh_editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    rows = []
    for asset in registry.get_assets_by_path("/Game/Megastructure_Scifi_World", recursive=True):
        path = str(asset.package_name)
        row = {"path": path, "class": str(asset.asset_class_path.asset_name)}
        # Map inspection is a separate rendered audition; do not load vendor worlds here.
        if row["class"] == "World":
            row["status"] = "registered_not_loaded"
            rows.append(row)
            continue
        obj = u.load_asset(path)
        row["loaded"] = obj is not None
        if isinstance(obj, u.StaticMesh):
            bounds = obj.get_bounds()
            row["size_cm"] = [bounds.box_extent.x * 2, bounds.box_extent.y * 2, bounds.box_extent.z * 2]
            row["lod_count"] = mesh_editor.get_lod_count(obj)
            row["lod0_vertices"] = mesh_editor.get_number_verts(obj, 0)
            row["materials"] = [str(slot.material_interface.get_path_name()) if slot.material_interface else None for slot in obj.static_materials]
        elif isinstance(obj, u.Blueprint):
            generated = obj.generated_class()
            row["generated_class"] = generated.get_path_name() if generated else None
            if generated:
                cdo = u.get_default_object(generated)
                row["default_components"] = [component.get_class().get_name() for component in cdo.get_components_by_class(u.ActorComponent)]
        elif isinstance(obj, u.MaterialInstanceConstant):
            parent = obj.get_editor_property("parent")
            row["parent"] = parent.get_path_name() if parent else None
            row["scalar_parameters"] = [str(p) for p in u.MaterialEditingLibrary.get_scalar_parameter_names(obj)]
            row["vector_parameters"] = [str(p) for p in u.MaterialEditingLibrary.get_vector_parameter_names(obj)]
        rows.append(row)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "inspection.json").write_text(json.dumps({
        "engine": u.SystemLibrary.get_engine_version(),
        "status": "METADATA_ONLY_NOT_RENDERED_OR_INTEGRATED",
        "assets": rows,
        "limits": "No vendor saves, gameplay references, rendered audition, collision or performance acceptance.",
    }, indent=2) + "\n", encoding="utf-8")
    u.log("MEGASTRUCTURE_INSPECTION_COMPLETE")


if __name__ == "__main__":
    main()
