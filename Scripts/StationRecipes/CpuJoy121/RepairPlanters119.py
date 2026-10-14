"""Replace only three private planter meshes with the verified cap-winding fix."""
import unreal as u
import hashlib
import json
import shutil
import traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT / '.agent/local/StationRefinement/CpuJoy121'
OUT=WORK/'CentralPlanter119'
DEST='/Game/OutpostSandbox/StationRefinement/CentralFeatures99'
NAMES={
 'SM_CentralPlanter':'7fd566e2c020d652f97aa618e784d66ead7ffbbac576f992ad2534f3fc4c2d70',
 'SM_CentralPlanterSoil':'432fe29430534e482a3dfbc7de67001bc44e3364b25ada2592a714db2d580596',
 'SM_CentralPlanterLip':'8b25d9607a70782a57c4e3155bd2107e60df3e1a9ee598f2055cb656cc42e446'}
REPORT={'state':'IN_PROGRESS','meshes':[],'errors':[]}
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def checkpoint():(OUT/'Receipt.json').write_text(json.dumps(REPORT,indent=2)+'\n')
def file_for(name):return ROOT/'Content/OutpostSandbox/StationRefinement/CentralFeatures99'/(name+'.uasset')
def main():
    assert not OUT.exists(),'Keep any previous partial result for inspection.'
    OUT.mkdir()
    baseline=json.loads((WORK/'CpuVerification108.json').read_text())
    for row in baseline['private_packages']:assert sha(ROOT/row['file'])==row['sha256'],row['file']
    mapfile=ROOT/'Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap'
    assert sha(mapfile)==baseline['map_sha256']
    for name,expected in NAMES.items():
        source=WORK/'CentralFeatures109Geometry'/(name+'.obj')
        assert sha(source)==expected
        before=file_for(name);backup=OUT/(name+'.before.uasset')
        shutil.copy2(before,backup);assert sha(backup)==sha(before)
        mesh=u.load_asset(DEST+'/'+name);assert isinstance(mesh,u.StaticMesh)
        materials=list(mesh.get_editor_property('static_materials'))
        bounds=mesh.get_bounds();old_bounds=list(bounds.origin.to_tuple())+list(bounds.box_extent.to_tuple())
        row={'asset':mesh.get_path_name(),'source_sha256':expected,'before_sha256':sha(before),'backup':str(backup),'before_bounds':old_bounds,
             'materials_before':[m.material_interface.get_path_name() if m.material_interface else None for m in materials]}
        REPORT['meshes'].append(row);checkpoint()
        task=u.AssetImportTask()
        for k,v in dict(filename=str(source),destination_path=DEST,destination_name=name,automated=True,replace_existing=True,replace_existing_settings=True,save=False).items():task.set_editor_property(k,v)
        opts=u.FbxImportUI()
        for k,v in dict(import_mesh=True,import_as_skeletal=False,import_materials=False,import_textures=False,mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH).items():opts.set_editor_property(k,v)
        for k,v in dict(combine_meshes=True,auto_generate_collision=False,generate_lightmap_u_vs=True,import_uniform_scale=1.,convert_scene=False,force_front_x_axis=False,normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS).items():opts.static_mesh_import_data.set_editor_property(k,v)
        task.options=opts;task.factory=u.FbxFactory()
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        assets=[u.load_asset(p) for p in task.imported_object_paths]
        assert len(assets)==1 and assets[0].get_path_name()==row['asset']
        mesh=assets[0];mesh.set_editor_property('static_materials',materials)
        bounds=mesh.get_bounds();new_bounds=list(bounds.origin.to_tuple())+list(bounds.box_extent.to_tuple())
        assert all(abs(a-b)<1e-4 for a,b in zip(old_bounds,new_bounds)),(old_bounds,new_bounds)
        assert u.EditorAssetLibrary.save_loaded_asset(mesh,False)
        row['after_bounds']=new_bounds;row['after_sha256']=sha(before);row['saved']=True
        row['materials_after']=[m.material_interface.get_path_name() if m.material_interface else None for m in mesh.static_materials]
        assert row['materials_after']==row['materials_before']
        checkpoint()
    changed=set(str(file_for(n).relative_to(ROOT)).replace('\\','/') for n in NAMES)
    for row in baseline['private_packages']:
        if row['file'].replace('\\','/') not in changed:assert sha(ROOT/row['file'])==row['sha256'],row['file']
    REPORT['map_sha256']=sha(mapfile);assert REPORT['map_sha256']==baseline['map_sha256']
    REPORT['other37_packages_preserved']=True
    REPORT['state']='THREE_MESHES_SAVED_MAP_UNCHANGED_VISUAL_REVIEW_PENDING'
    checkpoint()
try:main()
except Exception:
    REPORT['errors'].append(traceback.format_exc());REPORT['state']='FAILED_RETAIN_BACKUPS_AND_PARTIAL_RESULT';checkpoint();raise
print('CENTRAL119_RESULT',REPORT['state'])
