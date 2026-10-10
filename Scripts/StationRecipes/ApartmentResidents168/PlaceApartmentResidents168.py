"""Guarded apartment addition; import inert. Does not alter existing actors/assets."""
import hashlib,json,shutil
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'.agent/local/StationRefinement/ApartmentResidents169'
MAP=ROOT/'Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap'
SHA='52a5ee747fe7a586029c9f2ad85d782972b22c61b60bfbfcc9f7c88387dafdc7'
DEST='/Game/OutpostSandbox/StationRefinement/ApartmentResidents168'
PREFIX='HomeHub/Residents/'
JOY='/Game/SpaceSurvival/Licensed/StationAssets/JoyLightBlue117'
CYB='/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/Cyborg'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EAS=u.get_editor_subsystem(u.EditorActorSubsystem)
LEVEL=u.get_editor_subsystem(u.LevelEditorSubsystem)
def snapshot(a):
 return {'label':a.get_actor_label(),'transform':a.get_actor_transform().export_text(),'hidden':bool(a.get_editor_property('hidden')),
 'parts':[{'name':c.get_name(),'transform':c.get_world_transform().export_text(),'mesh':c.static_mesh.get_path_name() if c.static_mesh else None,'materials':[m.get_path_name() if m else None for m in c.get_materials()],'collision':str(c.get_collision_enabled())} for c in a.get_components_by_class(u.StaticMeshComponent)]}
def name(a,n):
 a.set_actor_label(PREFIX+n);a.set_folder_path('HomeHub/Residents');a.tags=list(a.tags)+[u.Name('ApartmentResidents168')];return a
def animation(c,path):
 anim=u.load_asset(path);assert anim,path
 c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
 data=c.get_editor_property('animation_data');data.set_editor_property('anim_to_play',anim);data.set_editor_property('saved_looping',True);data.set_editor_property('saved_playing',True)
 c.set_editor_property('animation_data',data);c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
def cylinder(n,center,diameter,height,material,solid=False):
 a=name(EAS.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*center)),n);c=a.static_mesh_component
 mesh=u.load_asset('/Engine/BasicShapes/Cylinder');c.set_static_mesh(mesh);b=mesh.get_bounds();size=b.box_extent*2
 a.set_actor_scale3d(u.Vector(diameter/size.x,diameter/size.y,height/size.z));c.set_material(0,material);c.set_collision_profile_name('BlockAll' if solid else 'NoCollision');return a
def apply():
 global report,original,new
 assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
 assert u.SystemLibrary.get_console_variable_int_value('r.RayTracing')==0
 assert sha(MAP)==SHA and not OUT.exists(),'State changed or already attempted; inspect before continuing'
 assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages() and not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
 original=list(EAS.get_all_level_actors());assert len(original)==9051
 assert not any(a.get_actor_label().startswith(PREFIX) for a in original)
 OUT.mkdir(parents=True);shutil.copy2(MAP,OUT/'Wayfarer-before.umap');assert sha(OUT/'Wayfarer-before.umap')==SHA
 before={a.get_name():snapshot(a) for a in original};(OUT/'original-actors.json').write_text(json.dumps(before,indent=2))
 report={'status':'PREFLIGHT','before_sha':SHA,'new_actors':[],'original_count':len(original),'errors':[]};new=[]
 def record(): (OUT/'receipt.json').write_text(json.dumps(report,indent=2))
 record()
 try:
  parent=u.load_asset('/Game/P1toP5_Bundle/P4_Genesis_Vol1/Materials/Instances/Opaque/MI_Metal10_Nickel');assert parent
  path=DEST+'/MI_PolishedPole';assert not u.EditorAssetLibrary.does_asset_exist(path)
  mat=u.AssetToolsHelpers.get_asset_tools().create_asset('MI_PolishedPole',DEST,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew());assert mat
  u.MaterialEditingLibrary.set_material_instance_parent(mat,parent)
  for key,value in {'Min Roughness':.12,'Max Roughness':.24,'Normal Intensity':.3,'Opacity Value (Dirt)':0.,'Opacity (Damage)':0.}.items():assert u.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mat,key,value)
  u.MaterialEditingLibrary.update_material_instance(mat);assert u.EditorAssetLibrary.save_loaded_asset(mat)
  bp=u.load_asset(JOY+'/BP_JoyLightBlue_Review');assert bp and bp.generated_class()
  joy=name(EAS.spawn_actor_from_class(bp.generated_class(),u.Vector(7018,5020,-169.5)),'Joy');new.append(joy)
  animation(joy.get_component_by_class(u.SkeletalMeshComponent),JOY+'/Animations/A_Joy_PoleIdle')
  cy=name(EAS.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(7220,5130,-169.5)),'Cyborg girl');new.append(cy)
  cy.set_actor_rotation(u.Rotator(yaw=-30),False);body=cy.skeletal_mesh_component;body.set_skeletal_mesh_asset(u.load_asset(CYB+'/Rig/SK_Cyborg'));animation(body,CYB+'/A_Cyborg_Idle')
  for spec in [('Pole/Shaft',(7000,5000,30),4.5,396,True),('Pole/Floor mount',(7000,5000,-168.5),24,3,False),('Pole/Floor collar',(7000,5000,-165),8,5,False),('Pole/Ceiling mount',(7000,5000,229),24,3,False),('Pole/Ceiling collar',(7000,5000,225.5),8,5,False)]:
   n,p,d,h,solid=spec;new.append(cylinder(n,p,d,h,mat,solid))
  assert all(snapshot(a)==before[a.get_name()] for a in original),'Existing actor changed'
  assert sha(MAP)==SHA,'Concurrent map change'
  report.update(status='PLACED_UNSAVED',new_actors=[{'name':a.get_name(),**snapshot(a)} for a in new],material=path,existing_preserved=True);record()
  return {'status':report['status'],'added':len(new)}
 except Exception as error:
  report['status']='FAILED_INSPECT_BEFORE_RETRY';report['errors'].append(repr(error));record();raise
def save():
 assert report['status']=='PLACED_UNSAVED'
 before=json.loads((OUT/'original-actors.json').read_text())
 assert all(snapshot(a)==before[a.get_name()] for a in original)
 assert sha(MAP)==SHA and len(EAS.get_all_level_actors())==9058
 assert LEVEL.save_current_level()
 report.update(status='SAVED_REQUIRES_NATIVE_REVIEW',after_sha=sha(MAP),actor_count=len(EAS.get_all_level_actors()))
 (OUT/'receipt.json').write_text(json.dumps(report,indent=2));return {'status':report['status'],'map_sha':report['after_sha']}
