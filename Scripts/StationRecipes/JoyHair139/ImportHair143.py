"""Guarded NullRHI adoption of Joy's reviewed hair cleanup; no map/animation edits."""
import unreal as u,json,hashlib,shutil,traceback
from pathlib import Path
REPO=Path(__file__).resolve().parents[3];WORK=Path(__file__).resolve().parents[3]/'.agent/local/StationRefinement/JoyHair139';OUT=WORK/'JoyHair143'
DEST='/Game/SpaceSurvival/Licensed/StationAssets/JoyLightBlue117';JOY='/Game/SpaceSurvival/Licensed/StationAssets/JoyPurple'
GROOM=DEST+'/Hair/G_JoyHair_base_Clean139';BINDING=DEST+'/Hair/GB_Joy_base_Clean139';BP=DEST+'/BP_JoyLightBlue_Review'
REPORT={'state':'IN_PROGRESS','errors':[],'written':[]}
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def file_for(p):return REPO/'Content'/(p.removeprefix('/Game/').split('.')[0]+'.uasset')
def checkpoint():(OUT/'Adopt143.json').write_text(json.dumps(REPORT,indent=2)+'\n')
def save(a):
 assert u.EditorAssetLibrary.save_loaded_asset(a,False),a.get_path_name()
 REPORT['written'].append({'asset':a.get_path_name(),'sha256':sha(file_for(a.get_path_name()))});checkpoint()
def counts(a):return [{'group':str(g.get_editor_property('group_name')),'curves':g.get_editor_property('num_curves'),'guides':g.get_editor_property('num_guides'),'vertices':g.get_editor_property('num_curve_vertices')} for g in a.get_editor_property('hair_groups_info')]
def main():
 OUT.mkdir(exist_ok=False)
 failed=json.loads((WORK/'JoyHair141/Adopt141.json').read_text());assert failed['state']=='FAILED_RETAIN_PARTIAL_FOR_INSPECTION' and not failed['written'] and 'group_name' in failed['errors'][0]
 author=json.loads((WORK/'JoyHair139/Author139.json').read_text());reload=json.loads((WORK/'JoyHair140/Reload140.json').read_text());assert reload['state']=='SAVED_BLENDER_RELOAD_AND_CPU_PREVIEW_PASS'
 abc=WORK/'JoyHair139/G_JoyHair_base_Clean.abc';assert sha(abc)==author['abc_sha256']
 original_export=json.loads((REPO/'.agent/local/StationRefinement/Lineup92/JoyExportRest/Export.json').read_text());assert author['hair_pose_to_rest']==original_export['hair_pose_to_rest']
 baseline=json.loads((WORK/'CpuVerification108.json').read_text());complete=json.loads((WORK/'JoyBlue114/Complete121.json').read_text());pilot=json.loads((WORK/'JoyBlue114/Author117.json').read_text());planters=json.loads((WORK/'CentralPlanter119/Receipt.json').read_text())
 protected={r['file']:r['sha256'] for r in baseline['protected_files']}
 for r in baseline['private_packages']:protected[str(REPO/r['file'])]=r['sha256']
 for r in planters['meshes']:protected[str(file_for(r['asset']))]=r['after_sha256']
 protected.update(pilot['protected'])
 for r in complete['native_packages']:protected[str(file_for(r['asset']))]=r['sha256']
 protected[str(REPO/'Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap')]=planters['map_sha256']
 protected.update({'M:/Local AI/Projects/Cyborg_Claude/rig/Cyborg_new.blend':'5cbc50ebf7281503f917755a3e140901e7af52c876637e3eef4fa4d4ffc0155d','M:/Local AI/Projects/JoySkinPreview_20261008/selected_deep_purple/Joy_Purple_HairFitted.blend':'ea6f4be979d1381b15899b16cded8059578d8529c9d2deed962fc6f09b5576a6'})
 for p,digest in protected.items():assert sha(Path(p))==digest,p
 REPORT['protected_before']=protected;checkpoint()
 edit=u.EditorAssetLibrary
 assert not edit.does_asset_exist(GROOM) and not edit.does_asset_exist(BINDING)
 shutil.copy2(file_for(BP),OUT/'BP_JoyLightBlue_Review.before.uasset')
 crashed=json.loads((WORK/'JoyHair142/Adopt142.json').read_text());assert crashed['state']=='IN_PROGRESS' and not crashed['written']
 assert not file_for(GROOM).exists() and not file_for(BINDING).exists()
 old=u.load_asset(JOY+'/Hair/G_JoyHair_base_Rest');mesh=u.load_asset(DEST+'/Mesh/SK_JoyLightBlue');assert old and mesh
 REPORT['old_groom_counts']=counts(old)
 options=u.GroomImportOptions();options.conversion_settings=u.GroomConversionSettings(rotation=u.Vector(90,0,0),scale=u.Vector(100,-100,100))
 task=u.AssetImportTask();task.filename=str(abc);task.destination_path=DEST+'/Hair';task.destination_name=GROOM.split('/')[-1];task.automated=True;task.replace_existing=False;task.save=False;task.options=options;task.factory=u.HairStrandsFactory()
 u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert len(task.imported_object_paths)==1
 groom=u.load_asset(task.imported_object_paths[0]);assert isinstance(groom,u.GroomAsset) and groom.get_path_name().split('.')[0]==GROOM
 REPORT['new_groom_counts']=counts(groom)
 assert len(REPORT['old_groom_counts'])==len(REPORT['new_groom_counts'])
 assert sum(r['curves'] for r in REPORT['old_groom_counts'])-sum(r['curves'] for r in REPORT['new_groom_counts'])==153
 for prop in ('hair_groups_rendering','hair_groups_physics','hair_groups_interpolation','hair_groups_lod','hair_groups_materials'):
  groom.set_editor_property(prop,old.get_editor_property(prop))
 save(groom)
 binding=u.GroomLibrary.create_new_groom_binding_asset_with_path(BINDING,groom,mesh,100,None,0);assert isinstance(binding,u.GroomBindingAsset)
 assert binding.get_editor_property('groom')==groom and binding.get_editor_property('target_skeletal_mesh')==mesh and len(binding.get_editor_property('group_infos'))>0;save(binding)
 bp=u.load_asset(BP);sub=u.get_engine_subsystem(u.SubobjectDataSubsystem);api=u.SubobjectDataBlueprintFunctionLibrary;components={}
 for h in sub.k2_gather_subobject_data_for_blueprint(bp):
  o=api.get_object_for_blueprint(api.get_data(h),bp)
  if o:components[o.get_path_name()]=o
 hairs=[o for o in components.values() if isinstance(o,u.GroomComponent)];assert len(hairs)==2
 base=next(o for o in hairs if o.get_name()=='FittedHair_base_GEN_VARIABLE');streak=next(o for o in hairs if o.get_name()=='FittedHair_streak_GEN_VARIABLE')
 assert base.get_editor_property('groom_asset')==old
 REPORT['streak_binding']=streak.get_editor_property('binding_asset').get_path_name();material=base.get_material(0)
 base.set_groom_asset(groom);base.set_binding_asset(binding);assert base.get_material(0)==material
 REPORT['base_material']=material.get_path_name()
 u.BlueprintEditorLibrary.compile_blueprint(bp);assert bp.generated_class();save(bp)
 assert streak.get_editor_property('binding_asset').get_path_name()==REPORT['streak_binding']
 for p,digest in protected.items():
  if Path(p)!=file_for(BP):assert sha(Path(p))==digest,p
 REPORT['unchanged_file_count']=len(protected)-1;REPORT['map_sha256']=planters['map_sha256'];REPORT['clips_preserved']=135
 REPORT['state']='NATIVE_HAIR_SAVED_NULLRHI_RELOAD_PENDING';checkpoint()
try:main()
except Exception:
 REPORT['state']='FAILED_RETAIN_PARTIAL_FOR_INSPECTION';REPORT['errors'].append(traceback.format_exc());checkpoint();raise
print('HAIR143_SAVED',REPORT['written'],flush=True)
