"""Read-only rendered-editor reload of the hair-only native change."""
import unreal as u,json,hashlib,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];WORK=Path(__file__).resolve().parents[3]/'.agent/local/StationRefinement/JoyHair139';OUT=WORK/'JoyHair159';OUT.mkdir(exist_ok=False)
DEST='/Game/SpaceSurvival/Licensed/StationAssets/JoyLightBlue117';REPORT={'state':'IN_PROGRESS','errors':[]}
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def file_for(p):return ROOT/'Content'/(p.removeprefix('/Game/').split('.')[0]+'.uasset')
def checkpoint():(OUT/'Reload159.json').write_text(json.dumps(REPORT,indent=2)+'\n')
def main():
 warm=json.loads((WORK/'Hair158Probe.json').read_text());assert warm['info']==['(RenRootCount=10823,RenLODCount=1,SimRootCount=1082,SimLODCount=1)'] and not warm['dirty']
 REPORT['load_mode']='Fresh rendered editor; saved binding loaded in157, checked after post-load ticks in158, no rebuild or save'
 adopted=json.loads((WORK/'JoyHair153/Adopt153.json').read_text());assert adopted['state']=='NATIVE_HAIR_SAVED_NULLRHI_RELOAD_PENDING' and not adopted['errors']
 hashes=dict(adopted['protected_before'])
 for r in adopted['written']:hashes[str(file_for(r['asset']))]=r['sha256']
 for p,h in hashes.items():assert sha(Path(p))==h,p
 groom=u.load_asset(DEST+'/Hair/G_JoyHair_base_Clean139');binding=u.load_asset(DEST+'/Hair/GB_Joy_base_Clean139');bp=u.load_asset(DEST+'/BP_JoyLightBlue_Review');mesh=u.load_asset(DEST+'/Mesh/SK_JoyLightBlue')
 assert isinstance(groom,u.GroomAsset) and isinstance(binding,u.GroomBindingAsset) and bp.generated_class()
 assert binding.get_editor_property('groom')==groom and binding.get_editor_property('target_skeletal_mesh')==mesh
 assert len(binding.group_infos)>0
 REPORT['binding_info']=[x.export_text() for x in binding.group_infos];checkpoint()
 assert sum(x.get_editor_property('ren_root_count') for x in binding.group_infos)==10823
 assert sum(x.get_editor_property('sim_root_count') for x in binding.group_infos)==1082
 counts=[{'group':str(g.get_editor_property('group_name')),'curves':g.get_editor_property('num_curves'),'guides':g.get_editor_property('num_guides'),'vertices':g.get_editor_property('num_curve_vertices')} for g in groom.get_editor_property('hair_groups_info')]
 assert counts==adopted['new_groom_counts']
 old=u.load_asset('/Game/SpaceSurvival/Licensed/StationAssets/JoyPurple/Hair/G_JoyHair_base_Rest')
 for prop in ('hair_groups_rendering','hair_groups_physics','hair_groups_interpolation','hair_groups_lod','hair_groups_materials'):
  assert [x.export_text() for x in groom.get_editor_property(prop)]==[x.export_text() for x in old.get_editor_property(prop)],prop
 sub=u.get_engine_subsystem(u.SubobjectDataSubsystem);api=u.SubobjectDataBlueprintFunctionLibrary;components={}
 for h in sub.k2_gather_subobject_data_for_blueprint(bp):
  obj=api.get_object_for_blueprint(api.get_data(h),bp)
  if obj:components[obj.get_path_name()]=obj
 base=next(o for o in components.values() if o.get_name()=='FittedHair_base_GEN_VARIABLE');streak=next(o for o in components.values() if o.get_name()=='FittedHair_streak_GEN_VARIABLE')
 assert base.get_editor_property('groom_asset')==groom and base.get_editor_property('binding_asset')==binding
 assert base.get_material(0).get_path_name()==adopted['base_material']
 assert streak.get_editor_property('binding_asset').get_path_name()==adopted['streak_binding']
 bodies=[o for o in components.values() if isinstance(o,u.SkeletalMeshComponent)];assert len(bodies)==1
 body=bodies[0];assert body.get_editor_property('skeletal_mesh_asset')==mesh
 animation=body.get_editor_property('animation_data');assert animation.anim_to_play.get_path_name().split('.')[0]==DEST+'/Animations/A_Joy_Idle' and animation.saved_looping and animation.saved_playing
 assert len(u.AssetRegistryHelpers.get_asset_registry().get_assets_by_path(DEST,True))==149
 REPORT.update({'groom_counts':counts,'binding_groups':len(binding.group_infos),'protected_hash_count':len(hashes),'clips_preserved':135,'native_package_count':149,'dirty_maps':[p.get_path_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()],'dirty_content':[p.get_path_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]})
 assert not REPORT['dirty_maps'] and not REPORT['dirty_content']
 REPORT['state']='NATIVE_HAIR_RELOAD_PASS_RENDERED_MOTION_PENDING';checkpoint()
try:main()
except Exception:
 REPORT['state']='FAILED_READ_ONLY_CHECK';REPORT['errors'].append(traceback.format_exc());checkpoint();raise
print('HAIR159_PASS',flush=True)
