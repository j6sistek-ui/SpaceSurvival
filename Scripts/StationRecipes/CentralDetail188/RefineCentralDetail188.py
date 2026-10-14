"""Bounded Central wall/portal and planting pass. Import inert; explicit apply/save."""
import unreal as u,hashlib,json,math
from pathlib import Path
ROOT=Path('C:/Users/j6sis/SpaceSurvival')
OUT=ROOT/'.agent/local/StationRefinement/CentralDetail187'
MAP=ROOT/'Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap'
SHA='7e30f69f57b4c2ecb2600334c39ed18038fda28a90fbffee632660651a80f937'
PREFIX='Refine/CentralDetail188/'
EAS=u.get_editor_subsystem(u.EditorActorSubsystem)

def snap(a):
 c=a.get_component_by_class(u.StaticMeshComponent)
 return {'label':a.get_actor_label(),'transform':a.get_actor_transform().export_text(),'hidden':a.get_editor_property('hidden'),'collision':a.get_actor_enable_collision(),'mesh':c.static_mesh.get_path_name() if c and c.static_mesh else None,'materials':[m.get_path_name() if m else None for m in c.get_materials()] if c else []}

def inspect():
 global actors,bylabel,plants,frames,original
 assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
 assert hashlib.sha256(MAP.read_bytes()).hexdigest()==SHA
 assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
 assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
 actors=list(EAS.get_all_level_actors());assert len(actors)==9058
 bylabel={a.get_actor_label():a for a in actors}
 assert not any(k.startswith(PREFIX) for k in bylabel)
 plants=[a for a in actors if a.get_actor_label().startswith('Refine/CentralFeatures99/Waiting ') and any(s in a.get_actor_label() for s in ('/Broadleaf ','/Low planting '))]
 frames=[a for a in actors if a.get_actor_label().startswith('Refine/CentralFeatures99/Portal ') and '/Frame ' in a.get_actor_label()]
 assert len(plants)==44 and len(frames)==20,(len(plants),len(frames))
 assert 'Refine/CentralArchitecture97/Bay 01/Pilaster -1' in bylabel
 original={a.get_name():snap(a) for a in actors}
 return {'plants':len(plants),'portal_frames':len(frames),'added_wall_members':24,'other_actors_preserved':len(actors)-len(plants),'new_materials':0}

def apply():
 global changed,new,report
 inspect();assert not (OUT/'Detail188-receipt.json').exists()
 (OUT/'Detail188-before.json').write_text(json.dumps(original,indent=2))
 changed=[];new=[];report={'status':'APPLYING','before_sha':SHA}
 def record(): (OUT/'Detail188-receipt.json').write_text(json.dumps(report,indent=2))
 record()
 def named(a,label):
  a.set_actor_label(PREFIX+label);a.set_folder_path('StationRefinement/CentralDetail188');a.set_editor_property('tags',[u.Name('OutpostAuthored'),u.Name('OutpostLabel:'+PREFIX+label)]);a.set_actor_enable_collision(False);a.static_mesh_component.set_collision_profile_name('NoCollision');new.append(a);return a
 def position(angle,radius,offset,z):
  r=math.radians(angle);return u.Vector(4200+radius*math.cos(r)-offset*math.sin(r),radius*math.sin(r)+offset*math.cos(r),z)
 source=bylabel['Refine/CentralArchitecture97/Bay 01/Pilaster -1']
 def member(label,center,size,rotation):
  a=named(EAS.duplicate_actor(source,u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()),label)
  ext=a.static_mesh_component.static_mesh.get_bounds().box_extent.to_tuple()
  a.set_actor_rotation(rotation,False);a.set_actor_scale3d(u.Vector(*(size[i]/(2*ext[i]) for i in range(3))))
  p,_=a.get_actor_bounds(False);a.set_actor_location(a.get_actor_location()+center-p,False,True);return a
 try:
  for a in plants:
   label=a.get_actor_label();i=int(label.rsplit(' ',1)[-1]);old=a.get_actor_transform();changed.append((a,old));p,e=a.get_actor_bounds(False);base=p.z-e.z
   if '/Low planting ' in label:height=48.;width=.8
   else:height={0:105.,1:185.,2:75.,3:70.,4:75.,5:185.,6:105.}[i];width=.65 if i in (1,5) else .78
   a.modify();s=a.get_actor_scale3d();a.set_actor_scale3d(u.Vector(s.x*width,s.y*width,s.z*height/(2*e.z)))
   p2,e2=a.get_actor_bounds(False);target=u.Vector(p.x,p.y,base+height/2);a.set_actor_location(a.get_actor_location()+target-p2,False,True)
  for a in frames:
   idx=int(a.get_actor_label().split('/Portal ')[1].split('/')[0]);angle=idx*90.;r=math.radians(angle)
   duplicate=named(EAS.duplicate_actor(a,u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()),'Portal %d/Inner %s'%(idx,a.get_actor_label().rsplit(' ',1)[-1]))
   duplicate.set_actor_location(duplicate.get_actor_location()+u.Vector(math.cos(r)*58,math.sin(r)*58,0),False,True)
  for i,angle in enumerate((45.,135.,225.,315.)):
   for side in (-1,1):
    member('Wall %d/Side %d'%(i,side),position(angle,1512,side*285,310),(590,45,46),u.Rotator(pitch=90,yaw=angle+90))
    member('Wall %d/Diagonal %d'%(i,side),position(angle,1510,side*143,535),(297,32,32),u.Rotator(pitch=side*22,yaw=angle+90))
   member('Wall %d/Lower header'%i,position(angle,1512,0,458),(555,38,38),u.Rotator(yaw=angle+90))
   member('Wall %d/Upper header'%i,position(angle,1512,0,605),(555,38,38),u.Rotator(yaw=angle+90))
  assert len(new)==44
  allowed={a.get_name() for a,_ in changed}
  assert all(snap(a)==original[a.get_name()] for a in actors if a.get_name() not in allowed)
  report.update(status='APPLIED_UNSAVED',new=[snap(a) for a in new],changed=[{'name':a.get_name(),**snap(a)} for a,_ in changed],untouched=len(actors)-len(changed));record()
  return {'status':report['status'],'added':len(new),'plant_transforms':len(changed),'untouched':report['untouched']}
 except Exception as error:
  report.update(status='FAILED_INSPECT',error=repr(error));record();raise

def save():
 assert report['status']=='APPLIED_UNSAVED'
 assert hashlib.sha256(MAP.read_bytes()).hexdigest()==SHA
 assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
 assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
 report.update(status='SAVED_REQUIRES_VISUAL_REVIEW',after_sha=hashlib.sha256(MAP.read_bytes()).hexdigest(),actor_count=len(EAS.get_all_level_actors()))
 (OUT/'Detail188-receipt.json').write_text(json.dumps(report,indent=2));return {'status':report['status'],'sha':report['after_sha'],'count':report['actor_count']}

def restore():
 for a,t in changed:a.set_actor_transform(t,False,True)
 for a in reversed(new):EAS.destroy_actor(a)
