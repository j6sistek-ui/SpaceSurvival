"""Add the home annex to the saved outpost without regenerating existing areas.

Run in a dedicated offscreen editor, after AuthorHomeApartment. Refuses a second
application; backups and a complete original-actor fingerprint precede changes.
"""
import hashlib
import json
import math
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Artifacts/ApartmentHome'
TARGET='/Game/OutpostSandbox/L_AsteroidOutpost'
MAP=ROOT/'Content/OutpostSandbox/L_AsteroidOutpost.umap'
BP='/Game/BuildingLibrary/Assembled/Home/BP_CrewApartment_Complete'
sys.path.insert(0,str(ROOT/'Scripts'))
import HomeAnnexConnector
EAS=u.get_editor_subsystem(u.EditorActorSubsystem)
LEVEL=u.get_editor_subsystem(u.LevelEditorSubsystem)
EDITOR=u.get_editor_subsystem(u.UnrealEditorSubsystem)
ASSETS=json.loads((ROOT/'Scripts/OutpostAssets.json').read_text(encoding='utf-8'))['assets']
CACHE={}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def v(p):return [round(p.x,5),round(p.y,5),round(p.z,5)]
def load(p):
    if p not in CACHE:CACHE[p]=u.load_asset(p)
    assert CACHE[p],p
    return CACHE[p]
def label(a,name):
    assert name.startswith('HomeHub/'),name
    a.set_actor_label(name);a.set_folder_path('HomeHub')
    a.tags=list(a.tags)+[u.Name('HomeHubAddition')]
    return a
def raw(name,path,location,yaw=0,scale=(1,1,1),solid=False,materials=None,rotation=None):
    a=label(EAS.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*location)),name)
    c=a.static_mesh_component;c.set_static_mesh(load(path))
    a.set_actor_rotation(u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]) if rotation else u.Rotator(yaw=yaw),False)
    a.set_actor_scale3d(u.Vector(*scale))
    c.set_collision_profile_name('BlockAll' if solid else 'NoCollision')
    if materials:
        for i,m in enumerate(materials):c.set_material(i,m)
    elif path==ASSETS['floor_main']['asset'] and FLOOR_MATERIALS:
        for i,m in enumerate(FLOOR_MATERIALS):c.set_material(i,m)
    return a
def place(name,path,center,size=None,height=None,yaw=0,solid=False,material=None,support=None):
    b=load(path).get_bounds();dims=v(b.box_extent*2)
    scale=[size[i]/max(dims[i],.001) for i in range(3)] if size else [height/dims[2]]*3 if height else [1,1,1]
    origin=b.origin*u.Vector(*scale)
    offset=u.Rotator(yaw=yaw).quaternion().rotate_vector(origin)
    return raw(name,path,v(u.Vector(*center)-offset),yaw,scale,solid,[material] if material else None)
def box(name,center,size,mat,solid=False,yaw=0):
    return place(name,'/Engine/BasicShapes/Cube.Cube',center,size=size,yaw=yaw,solid=solid,material=mat)
def text(name,words,pos,yaw,size=25,color=(150,224,255)):
    a=label(EAS.spawn_actor_from_class(u.TextRenderActor,u.Vector(*pos)),name)
    a.set_actor_rotation(u.Rotator(yaw=yaw),False)
    c=a.get_component_by_class(u.TextRenderComponent)
    c.set_text(words);c.set_world_size(size);c.set_text_material(load('/Engine/EngineMaterials/UnlitText'))
    c.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER);c.set_text_render_color(u.Color(*color,255))
    c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    return a
def light(name,pos,color=(.55,.8,1),power=2500,radius=1100,shadow=False):
    a=label(EAS.spawn_actor_from_class(u.PointLight,u.Vector(*pos)),name)
    c=a.light_component;c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_editor_property('intensity_units',u.LightUnits.LUMENS)
    c.set_intensity(power);c.set_light_color(u.LinearColor(*color,1));c.set_attenuation_radius(radius);c.set_cast_shadows(shadow)
    return a
def fingerprint(a):
    t=a.get_actor_transform();r=a.get_actor_rotation()
    return {'label':a.get_actor_label(),'transform':[v(t.translation),[r.pitch,r.yaw,r.roll],v(t.scale3d)],
      'parts':[(c.get_name(),c.static_mesh.get_path_name() if c.static_mesh else None,
                [m.get_path_name() if m else None for m in c.get_materials()],str(c.get_collision_enabled()))
               for c in a.get_components_by_class(u.StaticMeshComponent)]}

try:
    import ss_catalog_refresh
    h=ss_catalog_refresh._state.get('handle')
    if h:u.unregister_slate_post_tick_callback(h);ss_catalog_refresh._state['handle']=None
except ImportError:pass
assert LEVEL.load_level(TARGET)
u.AutomationLibrary.finish_loading_before_screenshot()
existing=list(EAS.get_all_level_actors())
assert not any('HomeHubAddition' in map(str,a.tags) for a in existing),'Home annex already exists; preserve owner edits'
before={a.get_name():fingerprint(a) for a in existing}
run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup=OUT/('L_AsteroidOutpost-before-home-'+run+'.umap')
shutil.copy2(MAP,backup)
assert sha(MAP)==sha(backup)
report={'status':'running','before_sha256':sha(MAP),'backup':str(backup),'existing_actor_count':len(existing),'errors':[]}
(OUT/'station-before-home-actors.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
FLOOR_MATERIALS=next((a.static_mesh_component.get_materials() for a in existing if isinstance(a,u.StaticMeshActor)
                   and a.get_actor_label().startswith('Lounge/Deck')),[])
DARK=load('/Game/OutpostSandbox/Materials/M_OutpostGraphite')
PEARL=load('/Game/OutpostSandbox/Materials/M_OutpostPearl')
CYAN=load('/Game/OutpostSandbox/Materials/M_OutpostCyan')
instance=label(EAS.spawn_actor_from_class(load(BP).generated_class(),u.Vector(6120,4100,-120)),'HomeHub/Complete crew apartment')
assert instance
report['connector']=HomeAnnexConnector.build(globals())
report['instance_location']=v(instance.get_actor_location())
state={'start':time.monotonic(),'busy':False,'done':False,'handle':None}

def finish():
    if state['done']:return
    state['done']=True
    (OUT/'home-integration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.log('HOME_INTEGRATION '+report['status'])
    u.unregister_slate_post_tick_callback(state['handle'])
    u.EditorPythonScripting.set_keep_python_script_alive(False)
    u.SystemLibrary.quit_editor()

def tick(delta):
    if state['busy'] or state['done']:return
    state['busy']=True
    try:
        world=EDITOR.get_editor_world()
        homes=[a for a in u.GameplayStatics.get_all_actors_of_class(world,u.SSOutpostDoor)
               if a.get_actor_label()=='HomeApartment/Automatic entry']
        if homes and time.monotonic()-state['start']>5:
            u.AutomationLibrary.finish_loading_before_screenshot()
            after={a.get_name():fingerprint(a) for a in existing}
            report['existing_actor_deltas']={name:{'before':value,'after':after.get(name)} for name,value in before.items() if after.get(name)!=value}
            assert before==after,'Existing actor transforms/assets changed'
            assert sha(MAP)==report['before_sha256'],'Source changed externally; do not save'
            report['preserved_existing_actors']=len(existing)
            report['new_station_actors']=len(EAS.get_all_level_actors())-len(existing)
            report['entry_door_world']=v(homes[0].get_actor_location())
            assert (homes[0].get_actor_location()-u.Vector(6120,4100,-120)).length()<.1
            assert LEVEL.save_current_level()
            report['after_sha256']=sha(MAP)
            report['status']='SAVED_REQUIRES_WALK_VALIDATION'
            finish()
        elif time.monotonic()-state['start']>100:raise RuntimeError('Apartment LevelInstance did not finish loading')
    except Exception:
        report['errors'].append(traceback.format_exc());report['status']='FAILED'
        u.log_error(report['errors'][-1]);finish()
    finally:state['busy']=False
u.EditorPythonScripting.set_keep_python_script_alive(True)
state['handle']=u.register_slate_post_tick_callback(tick)
