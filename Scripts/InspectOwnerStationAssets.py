"""Read-only bounds and material inventory of owner-staged station parts."""
from pathlib import Path
import json
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
LIB=u.EditorAssetLibrary
rows=[]
for folder in ['/Game/StarterBundle/ModularScifiProps/Meshes','/Game/StarterBundle/ModularSci_Comm/Meshes']:
 for path in LIB.list_assets(folder, recursive=True, include_folder=False):
  mesh=LIB.load_asset(path)
  if not isinstance(mesh,u.StaticMesh): continue
  b=mesh.get_bounds()
  rows.append({'asset':path,'origin':[b.origin.x,b.origin.y,b.origin.z], 'extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z], 'materials':[str(x.material_interface.get_path_name()) if x.material_interface else None for x in mesh.static_materials]})
out=ROOT/'.agent/local/StationVisualPass/OwnerStationAssets.json'
out.write_text(json.dumps({'status':'BOUNDS_AND_MATERIAL_INVENTORY_ONLY','meshes':rows},indent=2),encoding='utf-8')
u.log(f'OWNER_STATION_ASSETS_INSPECTED {len(rows)}')
