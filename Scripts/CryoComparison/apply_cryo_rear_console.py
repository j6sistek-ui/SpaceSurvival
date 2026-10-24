"""Reimport ONLY D's four owned FitV4 console components in isolated CryoStage.

Default main(False) is a file-only dry run. Root launches the editor and invokes
main(True). All four packages are backed up before import. No map/material save.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import runpy
import shutil
import traceback

WORK=Path(__file__).resolve().parent
OUT=WORK.parent/'outputs/Cryo_Comparison'
API=runpy.run_path(str(WORK/'upgrade_cryo_fit_unreal.py'))
STAGE=API['STAGE'];BASE=API['BASE'];digest=API['digest'];require=API['require']
package_hashes=API['package_hashes']
MANIFEST=OUT/'assembly_fit_v4_4.json'
CHANGES=OUT/'native-v4_4-mesh-changes.json'


def main(apply=False):
    receipt=WORK/('CryoRearConsoleApply.json' if apply else 'CryoRearConsoleDryRun.json')
    report={'status':'FAILED','apply':apply,'utc':datetime.now(timezone.utc).isoformat(),
            'manifest':str(MANIFEST),'errors':[],'changes':[]}
    u=None;stage_allowed=False
    try:
        manifest=json.loads(MANIFEST.read_text());delta=json.loads(CHANGES.read_text())
        require(manifest['version']=='v4_4_D_rear_console','Expected final rear console revision')
        manifest_hash=digest(MANIFEST)
        require(manifest_hash==delta['manifest_sha256'],'Import list/manifest mismatch')
        model=next(row for row in manifest['models'] if row['id']=='D')
        source_rows={row['name']:row for row in model['components']}
        changes=delta['changes']
        require(len(changes)==4 and {row['name'] for row in changes}=={'Console_1_Backing','Console_1_Glass','Console_1_HUD','Console_1_Frame'},'Expected only D console group 1')
        for row in changes:
            require(row['model_id']=='D' and row['file']==source_rows[row['name']]['file'],'Unexpected import input')
            require(digest(row['file'])==row['source_sha256'],'Changed OBJ source hash')
            row['asset']=BASE+'/Meshes/FitV4/D/SM_D_'+row['name']+'_FitV4'
            row['package']='Content\\'+row['asset'][len('/Game/'):].replace('/','\\')+'.uasset'
        report.update(manifest_sha256=manifest_hash,changes=changes)
        guards={str(MANIFEST):manifest_hash,str(CHANGES):digest(CHANGES)}
        for row in changes:
            guards[row['file']]=row['source_sha256'];guards[row['previous_file']]=row['previous_source_sha256']
        for assembly in manifest['models']:guards[assembly['source']]=assembly['source_sha256']
        require(all(digest(path)==value for path,value in guards.items()),'Protected input mismatch')
        if not apply:
            report['status']='DRY_RUN_READY_ONLY_D_REAR_CONSOLE_COMPONENTS'
            return report
        import unreal as u
        require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==STAGE.resolve(),'Restricted to isolated CryoStage')
        stage_allowed=True
        require(not u.EditorLevelLibrary.get_pie_worlds(False),'Refusing active PIE')
        before=package_hashes();report['native_before_hashes']=before
        expected={row['package'] for row in changes}
        require(expected<=set(before),'Owned pane packages are missing')
        backup=WORK/('pre_rear_console_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
        backup.mkdir(exist_ok=False);report['backup_directory']=str(backup)
        originals={}
        for row in changes:
            source=STAGE/row['package'];dest=backup/source.name
            shutil.copy2(source,dest);require(digest(dest)==before[row['package']],'Backup hash mismatch')
            row.update(backup=str(dest),backup_sha256=digest(dest))
            mesh=u.EditorAssetLibrary.load_asset(row['asset'])
            require(isinstance(mesh,u.StaticMesh) and mesh.get_num_sections(0)==1,'Unexpected existing mesh')
            require(u.EditorAssetLibrary.get_metadata_tag(mesh,'CryoModelID')=='D','Unowned destination')
            require(u.EditorAssetLibrary.get_metadata_tag(mesh,'CryoSourceSHA256')==row['previous_source_sha256'],'Existing native source differs from v4_2')
            originals[row['name']]=mesh.get_material(0)
        for row in changes:
            folder,name=row['asset'].rsplit('/',1)
            options=u.FbxImportUI()
            for key,value in {'automated_import_should_detect_type':False,'import_mesh':True,'import_as_skeletal':False,
                              'import_materials':False,'import_textures':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH}.items():
                options.set_editor_property(key,value)
            data=options.get_editor_property('static_mesh_import_data')
            for key,value in {'combine_meshes':True,'auto_generate_collision':False,'generate_lightmap_u_vs':False,
                              'build_nanite':False,'import_uniform_scale':1.,'convert_scene':False,'convert_scene_unit':False,
                              'force_front_x_axis':False,'normal_import_method':u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():
                data.set_editor_property(key,value)
            task=u.AssetImportTask()
            for key,value in {'filename':row['file'],'destination_path':folder,'destination_name':name,'automated':True,
                              'replace_existing':True,'save':False,'options':options,'factory':u.FbxFactory()}.items():
                task.set_editor_property(key,value)
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            paths=list(task.get_editor_property('imported_object_paths'))
            require(len(paths)==1 and paths[0].split('.')[0]==row['asset'],'Unexpected reimport target')
            mesh=u.EditorAssetLibrary.load_asset(paths[0])
            require(isinstance(mesh,u.StaticMesh) and mesh.get_num_sections(0)==1,'Unexpected reimport result')
            require(len(mesh.get_editor_property('static_materials'))==1,'Material section count changed')
            mesh.set_material(0,originals[row['name']])
            editor=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
            editor.remove_collisions(mesh);editor.enable_section_collision(mesh,False,0,0)
            for key,value in {'CryoAuthoringVersion':'CryoFitV4_4','CryoManifestSHA256':manifest_hash,'CryoRole':row['role'],
                              'CryoModelID':'D','CryoSourceSHA256':row['source_sha256'],'CryoAcceptance':'PENDING_REAR_SERVICE_CONSOLE_REVIEW'}.items():
                u.EditorAssetLibrary.set_metadata_tag(mesh,key,value)
            require(u.EditorAssetLibrary.save_loaded_asset(mesh,False),'Pane save failed')
            bounds=mesh.get_bounds()
            row.update(material=mesh.get_material(0).get_path_name(),sections_lod0=mesh.get_num_sections(0),
                       native_bounds_cm={'origin':list(bounds.origin.to_tuple()),'extent':list(bounds.box_extent.to_tuple())})
        after=package_hashes();report['native_after_hashes']=after
        changed={path for path in set(before)|set(after) if before.get(path)!=after.get(path)}
        require(set(before)==set(after) and changed==expected,'Unexpected native package change')
        require(all(digest(path)==value for path,value in guards.items()),'Protected source changed')
        report.update(status='REAR_CONSOLE_SAVED_PENDING_VISUAL_REVIEW',changed_existing_packages=sorted(changed),
                      unchanged_native_packages=len(before)-len(changed),native_file_count=len(after),
                      map_materials_other_meshes_unchanged=True,protected_inputs_unchanged=True,
                      protected_inputs=guards)
        return report
    except Exception:
        report['errors'].append(traceback.format_exc())
        if u:u.log_error(report['errors'][-1])
        return report
    finally:
        receipt.write_text(json.dumps(report,indent=2)+'\n')
        print('CRYO_REAR_CONSOLE_RESULT',json.dumps({'status':report['status'],'receipt':str(receipt)}),flush=True)
        if u and stage_allowed:u.SystemLibrary.quit_editor()


if __name__=='__main__':main(False)
