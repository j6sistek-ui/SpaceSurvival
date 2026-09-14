"""Read-only UE bounds/material inventory for locally staged licensed assets.

Run through the installed Unreal Python execution workflow after staging assets.
This does not import, modify, or save vendor assets and does not contain their data.
"""
import json
from pathlib import Path
import unreal as u

rows = []
for root in ('/Game/Asteroid_Library', '/Game/SciFiCorridor'):
    for path in u.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
        if '/Static_Mesh' not in path and '/Meshes/' not in path:
            continue
        mesh = u.load_asset(path)
        if not isinstance(mesh, u.StaticMesh):
            continue
        bounds = mesh.get_bounds()
        rows.append(dict(path=path,
                         origin=[bounds.origin.x, bounds.origin.y, bounds.origin.z],
                         extent=[bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z],
                         radius=bounds.sphere_radius,
                         materials=[slot.material_interface.get_path_name() if slot.material_interface else None
                                    for slot in mesh.static_materials]))
output = Path(u.Paths.project_dir()) / 'Artifacts/Refresh/vendor-meshes.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(rows, indent=2), encoding='utf-8')
print('VENDOR_INSPECTION_OK', len(rows))
