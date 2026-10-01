"""Create a private furnished apartment Level Instance with a working entry.

Original downloaded scene is never saved. Global showcase effects are omitted;
local furnishings, spline assemblies and lights remain together. Entry is (0,0,0).
"""
import hashlib
import json
from pathlib import Path
import sys
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Artifacts/ApartmentHome'
OUT.mkdir(parents=True,exist_ok=True)
SOURCE='/Game/Cyberpunk_Room/Maps/Cyberpunk_Room'
TARGET='/Game/BuildingLibrary/Home/L_CrewApartment'
BP='/Game/BuildingLibrary/Assembled/Home/BP_CrewApartment_Complete'
ANCHOR=u.Vector(-2384,-45,-445.859375)
EAS=u.get_editor_subsystem(u.EditorActorSubsystem)
LIB=u.EditorAssetLibrary
LEVEL=u.get_editor_subsystem(u.LevelEditorSubsystem)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def path(package):return ROOT/('Content/'+package.removeprefix('/Game/')+'.umap')
def v(x):return [x.x,x.y,x.z]
def label(a,name):
    a.set_actor_label('HomeApartment/'+name)
    a.set_folder_path('HomeApartment')
    return a

def cube(name,center,size,visible=False):
    a=label(EAS.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*center)),name)
    a.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
    a.set_actor_scale3d(u.Vector(*(n/100 for n in size)))
    a.static_mesh_component.set_collision_profile_name('BlockAll')
    a.set_actor_hidden_in_game(not visible)
    if not visible:a.static_mesh_component.set_visibility(False)
    return a

def main():
    try:
        import ss_catalog_refresh
        h=ss_catalog_refresh._state.get('handle')
        if h:u.unregister_slate_post_tick_callback(h);ss_catalog_refresh._state['handle']=None
    except ImportError:pass
    assert not LIB.does_asset_exist(TARGET),'Private apartment already exists; preserve edits'
    assert not LIB.does_asset_exist(BP),'Private apartment Blueprint already exists'
    protected=[path(SOURCE),path('/Game/OutpostSandbox/L_AsteroidOutpost')]
    before={str(p):sha(p) for p in protected}
    report={'source':SOURCE,'target':TARGET,'blueprint':BP,'source_anchor':v(ANCHOR),
            'protected_before':before,'removed':[],'collision_derivatives':[],'status':'running'}
    try:
        assert LEVEL.load_level(SOURCE)
        actors=list(EAS.get_all_level_actors())
        excluded={'CineCameraActor','CameraActor','LevelSequenceActor','GroupActor','PlayerStart',
                  'DirectionalLight','SkyLight','SkyAtmosphere','AtmosphericFog','ExponentialHeightFog',
                  'PostProcessVolume','LightmassImportanceVolume','BP_Sky_Sphere_C','BP_GodRay_C',
                  'BoxReflectionCapture','SphereReflectionCapture'}
        # Plane_4 is the large opaque city-image backdrop outside the window.
        for a in actors:
            if a.get_class().get_name() in excluded or a.get_name()=='Plane_4':
                report['removed'].append({'name':a.get_name(),'class':a.get_class().get_name()})
                assert EAS.destroy_actor(a)
        kept=list(EAS.get_all_level_actors())
        for a in kept:
            if not a.get_attach_parent_actor():
                assert a.set_actor_location(a.get_actor_location()-ANCHOR,False,False)
        # Precise structural collision preserves door/window openings. Copies
        # share native materials/textures; no vendor mesh is modified.
        mesher=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
        copies={}
        for a in kept:
            for c in a.get_components_by_class(u.StaticMeshComponent):
                m=c.static_mesh
                if not m:continue
                name=m.get_name().lower()
                structural=any(t in name for t in ('wall','floor','roof','doorway','door_03','window','fence'))
                if structural and m.get_path_name().startswith('/Game/Cyberpunk_Room/'):
                    source=m.get_path_name()
                    if source not in copies:
                        dest='/Game/BuildingLibrary/Home/Collision/'+m.get_name()
                        assert not LIB.does_asset_exist(dest),'Unrecognized private collision asset '+dest
                        copy=LIB.duplicate_asset(source,dest)
                        assert copy
                        mesher.remove_collisions(copy)
                        body=copy.get_editor_property('body_setup')
                        body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
                        body.set_editor_property('double_sided_geometry',True)
                        for section in range(copy.get_num_sections(0)):
                            mesher.enable_section_collision(copy,True,0,section)
                        assert LIB.save_loaded_asset(copy,only_if_is_dirty=False)
                        copies[source]=copy
                        report['collision_derivatives'].append({'source':source,'asset':dest})
                    c.set_static_mesh(copies[source])
                    c.set_collision_profile_name('BlockAll')
                if 'carpet' in name or any('floater_decal' in material.get_name().lower()
                                         for material in c.get_materials() if material):
                    c.set_collision_profile_name('NoCollision')
            for c in a.get_components_by_class(u.LightComponent):
                c.set_mobility(u.ComponentMobility.MOVABLE)
                # Adapt the native local lights to the outpost exposure, which
                # differs from the vendor showcase's removed postprocessing.
                c.set_intensity(c.intensity*8.)
                c.set_cast_shadows(False)
        for i,pos in enumerate(((500,450,260),(1450,450,260),(500,1080,260),(1450,1080,260))):
            a=label(EAS.spawn_actor_from_class(u.RectLight,u.Vector(*pos)),'Soft ceiling fill '+str(i))
            a.set_folder_path('HomeApartment/Lighting')
            a.set_actor_rotation(u.Rotator(pitch=-90),False)
            c=a.light_component;c.set_mobility(u.ComponentMobility.MOVABLE)
            c.set_editor_property('intensity_units',u.LightUnits.CANDELAS)
            c.set_intensity(500.);c.set_attenuation_radius(1100.);c.set_cast_shadows(False)
            c.set_light_color(u.LinearColor(.79,.88,1.,1.))
            c.set_editor_property('source_width',200.);c.set_editor_property('source_height',160.)
        # Native planes have no thickness. Hidden support is directly below the
        # intact visible floors, including the raised entrance strip.
        cube('Lower floor support',(984,585,-65),(2000,1600,30))
        cube('Entry floor support',(984,5,-15),(2000,400,30))
        by_name={a.get_name():a for a in kept}
        leaves=[by_name['SM_Door_3'],by_name['SM_Door_01_25']]
        door=label(EAS.spawn_actor_from_class(u.SSOutpostDoor,u.Vector()),'Automatic entry')
        closed=[]
        for leaf in leaves:
            center,extent=leaf.get_actor_bounds(False)
            closed.append(center)
        for key,val in [('left_closed',closed[0]),('right_closed',closed[1]),
                        ('left_travel',u.Vector(0,-100,0)),('right_travel',u.Vector(0,100,0)),
                        ('leaf_half_extent',u.Vector(12,40,111)),('safety_half_extent',u.Vector(100,155,125)),
                        ('sensor_radius',280.),('slide_seconds',.7)]:
            door.set_editor_property(key,val)
        for leaf,anchor,blocker,position in zip(leaves,[door.left_leaf,door.right_leaf],
                [door.left_blocker,door.right_blocker],closed):
            anchor.set_relative_location(position,False,False)
            blocker.set_relative_location(position,False,False)
            blocker.set_box_extent(u.Vector(12,40,111),False)
            leaf.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
            # Set the profile so mesh-default collision cannot return on load.
            leaf.static_mesh_component.set_collision_profile_name('NoCollision')
            leaf.attach_to_component(anchor,'None',u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
        report['door']={'class':door.get_class().get_path_name(),'closed':[v(p) for p in closed],
                        'leaf_actors':[a.get_name() for a in leaves],'sensor_cm':280}
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
        world.get_world_settings().set_editor_property('default_game_mode',None)
        assert u.EditorLoadingAndSavingUtils.save_map(world,TARGET)
        report['retained_actors']=len(EAS.get_all_level_actors())
        report['target_sha256']=sha(path(TARGET))
        bp=u.BlueprintEditorLibrary.create_blueprint_asset_with_parent(BP,u.LevelInstance)
        assert bp
        u.BlueprintEditorLibrary.compile_blueprint(bp)
        u.get_default_object(bp.generated_class()).set_editor_property('world_asset',u.load_asset(TARGET))
        assert LIB.save_loaded_asset(bp,only_if_is_dirty=False)
        manager=u.get_editor_subsystem(u.CollectionManagerSubsystem)
        for name in ('SS_01_Assembled___Drag_These','SS_New_CP_Apartment'):
            ref=u.Collection(container='Game',name=name,share_type=u.CollectionShareType.LOCAL)
            manager.add_asset_to_collection(ref,u.SoftObjectPath(BP+'.BP_CrewApartment_Complete'))
        report['status']='PASS'
    finally:
        report['protected_unchanged']=all(sha(p)==before[str(p)] for p in protected)
        if not report['protected_unchanged']:
            report['status']='FAILED_PROTECTED_MAP_DRIFT'
        (OUT/'apartment-author.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        assert report['protected_unchanged'],'Protected source/station map bytes changed'
    u.log('APARTMENT_AUTHOR '+report['status'])

if __name__=='__main__':main()
