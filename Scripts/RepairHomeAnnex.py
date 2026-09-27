"""One-time focused correction from the first saved-home walkthrough.

Touches only the private apartment and new HomeHub light pools. Original
station actor fingerprints and the downloaded apartment are protected.
"""
import hashlib
import json
import shutil
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Artifacts/ApartmentHome'
LIB=u.EditorAssetLibrary
LEVEL=u.get_editor_subsystem(u.LevelEditorSubsystem)
EAS=u.get_editor_subsystem(u.EditorActorSubsystem)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
home=ROOT/'Content/BuildingLibrary/Home/L_CrewApartment.umap'
station=ROOT/'Content/OutpostSandbox/L_AsteroidOutpost.umap'
source=ROOT/'Content/Cyberpunk_Room/Maps/Cyberpunk_Room.umap'
assert sha(home)=='511e82cde95778dd3742c7e0dda2019abd403aa5e2df26d9888258600d7470c2','Home changed; preserve owner edits'
assert sha(station)=='c1bea499ee752a8d6b9398f3ff8e749b2a39c10b8d5fe16fd7aa33e1dfa68fb6','Station changed; preserve owner edits'
report={'status':'running','before':{str(p):sha(p) for p in (home,station,source)},'collision':[],'lights':[]}
for p in (home,station):shutil.copy2(p,OUT/(p.stem+'-before-home-repair.umap'))
try:
 import ss_catalog_refresh
 h=ss_catalog_refresh._state.get('handle')
 if h:u.unregister_slate_post_tick_callback(h);ss_catalog_refresh._state['handle']=None
except ImportError:pass

def v(p):return [round(p.x,5),round(p.y,5),round(p.z,5)]
def fingerprint(a):
 t=a.get_actor_transform();r=a.get_actor_rotation()
 return {'label':a.get_actor_label(),'transform':[v(t.translation),[r.pitch,r.yaw,r.roll],v(t.scale3d)],
  'parts':[(c.get_name(),c.static_mesh.get_path_name() if c.static_mesh else None,
    [m.get_path_name() if m else None for m in c.get_materials()],str(c.get_collision_enabled()))
    for c in a.get_components_by_class(u.StaticMeshComponent)]}

try:
 assert LEVEL.load_level('/Game/BuildingLibrary/Home/L_CrewApartment')
 u.AutomationLibrary.finish_loading_before_screenshot()
 actors=list(EAS.get_all_level_actors())
 for a in actors:
  for c in a.get_components_by_class(u.StaticMeshComponent):
   mesh=c.static_mesh
   mats=[m.get_name().lower() for m in c.get_materials() if m]
   # Source floating decal planes are nearly ten metres across and solid.
   # They are decoration; the intact walls/floors carry physical collision.
   decorative=any('floater_decal' in m for m in mats) or (mesh and 'carpet' in mesh.get_name().lower())
   leaf=a.get_name() in ('SM_Door_3','SM_Door_01_25')
   if decorative or leaf:
    report['collision'].append({'actor':a.get_name(),'mesh':str(mesh),'old_profile':str(c.get_collision_profile_name()),'reason':'moving visual leaf' if leaf else 'surface decoration'})
    c.set_collision_profile_name('NoCollision')
  for c in a.get_components_by_class(u.LightComponent):
   old=float(c.intensity)
   c.set_intensity(old*8.)
   report['lights'].append({'actor':a.get_name(),'old_candela':old,'new_candela':float(c.intensity)})
 for i,pos in enumerate(((500,450,260),(1450,450,260),(500,1080,260),(1450,1080,260))):
  a=EAS.spawn_actor_from_class(u.RectLight,u.Vector(*pos));a.set_actor_label('HomeApartment/Soft ceiling fill '+str(i));a.set_folder_path('HomeApartment/Lighting')
  a.set_actor_rotation(u.Rotator(pitch=-90),False)
  c=a.light_component;c.set_mobility(u.ComponentMobility.MOVABLE)
  c.set_editor_property('intensity_units',u.LightUnits.CANDELAS)
  c.set_intensity(500.);c.set_attenuation_radius(1100.);c.set_cast_shadows(False)
  c.set_light_color(u.LinearColor(.79,.88,1.,1.))
  c.set_editor_property('source_width',200.);c.set_editor_property('source_height',160.)
 assert LEVEL.save_current_level()
 assert LEVEL.load_level('/Game/OutpostSandbox/L_AsteroidOutpost')
 u.AutomationLibrary.finish_loading_before_screenshot()
 original=[a for a in EAS.get_all_level_actors() if 'HomeHubAddition' not in map(str,a.tags)]
 before={a.get_name():fingerprint(a) for a in original}
 recorded=json.loads((OUT/'station-before-home-actors.json').read_text(encoding='utf-8'))
 assert json.loads(json.dumps(before))==recorded,'Original station actor drift before repair'
 pools=[a for a in EAS.get_all_level_actors() if a.get_actor_label().startswith('HomeHub/Connector/Lighting/') and isinstance(a,u.PointLight)]
 assert len(pools)==6,len(pools)
 for a in pools:
  c=a.light_component
  assert c.intensity==450.,'New corridor was externally changed'
  c.set_intensity(2400.);c.set_attenuation_radius(720.)
 assert before=={a.get_name():fingerprint(a) for a in original},'Original actors changed'
 assert LEVEL.save_current_level()
 report['preserved_station_actors']=len(original)
 report['status']='SAVED_REQUIRES_REVIEW'
finally:
 report['source_preserved']=sha(source)==report['before'][str(source)]
 report['after']={str(p):sha(p) for p in (home,station,source)}
 if not report['source_preserved']:report['status']='FAILED_SOURCE_DRIFT'
 (OUT/'home-repair.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
u.log('HOME_REPAIR '+report['status'])
