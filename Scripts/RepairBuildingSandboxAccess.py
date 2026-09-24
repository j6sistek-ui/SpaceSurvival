"""Flatten only the private building sandbox and remove its canyon/display barriers.

run() is a dry run. run(apply=True) backs up the map before an undoable edit.
Does not save the level: inspect it, then save explicitly. Vendor assets stay intact.
"""
import datetime
import json
import shutil
from pathlib import Path
import unreal as u

TARGET = '/Game/Blender/Sandbox/BuildingSandbox_20260922'
# Main walk-floor tops from the source scene survey, in centimeters.
FLOOR_TOP = {'Genesis': 50.0, 'WorkStation': 2.28, 'StarterPack': 52.28,
             'ComputerStation': 10.61, 'FruitSeller': 198.82}
FLAT_TAG = 'SSSandboxFlatV1'


def run(apply=False):
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    assert world and world.get_path_name().split('.')[0] == TARGET, 'Wrong map'
    assert not editor.get_game_world(), 'Stop Play before editing'
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
    eas = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = list(eas.get_all_level_actors())
    removals, fog, moves = [], [], []
    for actor in actors:
        area = str(actor.get_folder_path())
        tags = [str(t) for t in actor.tags]
        label = actor.get_actor_label()
        mesh = actor.static_mesh_component.static_mesh if isinstance(actor, u.StaticMeshActor) else None
        if mesh:
            _, extent = actor.get_actor_bounds(False)
            enclosure = (mesh.get_path_name() == '/Engine/BasicShapes/Plane.Plane'
                         and area in ('WorkStation', 'StarterPack')
                         and extent.z > 200 and min(extent.x, extent.y) < .1)
            if 'RedCanyon' in mesh.get_name() or enclosure or (area == 'Sandbox foundation' and 'ramp' in label):
                removals.append(actor)
                continue
            if any('/Fog/' in m.get_path_name() for m in actor.static_mesh_component.get_materials() if m):
                fog.append(actor)
        if area in FLOOR_TOP and FLAT_TAG not in tags:
            moves.append((actor, -FLOOR_TOP[area]))
    floor = next(a for a in actors if a.get_actor_label() == 'Sandbox connecting floor')
    parent = u.load_asset('/Game/SpaceSurvival/Licensed/Atmosphere/M_RegionSky')
    assert parent, 'Owned working space material missing'
    report = {'map': TARGET, 'apply': apply, 'removed': [a.get_name() for a in removals],
              'canyon_count': sum('RedCanyon' in a.static_mesh_component.static_mesh.get_name() for a in removals),
              'moved': len(moves), 'area_z_delta': {k:-v for k,v in FLOOR_TOP.items()},
              'platform_top': 0, 'saved': False}
    if not apply:
        print(json.dumps({k:v for k,v in report.items() if k != 'removed'}))
        return report
    out = root / '.agent/local/SandboxFlat' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    out.mkdir(parents=True)
    shutil.copy2(root / ('Content/' + TARGET[6:] + '.umap'), out / 'Before.umap')
    report['old_locations'] = {a.get_name(): [a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z] for a,dz in moves}
    # Persist intent before editing so partial execution is diagnosable.
    (out/'repair.json').write_text(json.dumps(report, indent=2))
    with u.ScopedEditorTransaction('Flat space building sandbox'):
        for actor in removals:
            assert eas.destroy_actor(actor), actor.get_name()
        for actor, dz in moves:
            actor.modify()
            actor.set_actor_location(actor.get_actor_location()+u.Vector(0,0,dz),False,False)
            actor.tags = list(actor.tags) + [u.Name(FLAT_TAG)]
        for actor in fog:
            actor.static_mesh_component.modify()
            actor.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        floor.modify()
        p = floor.get_actor_location()
        floor.set_actor_location(u.Vector(p.x,p.y,-25),False,False)
        # Full-width walkable apron and space behind the examples; existing scene XY layout stays.
        floor.set_actor_scale3d(u.Vector(260,110,.5))
        for actor in actors:
            kind = actor.get_class().get_name() if u.SystemLibrary.is_valid(actor) else ''
            if kind in ('SkyAtmosphere','VolumetricCloud','ExponentialHeightFog'):
                actor.modify()
                actor.set_actor_hidden_in_game(True)
                for c in actor.get_components_by_class(u.SceneComponent):
                    c.modify(); c.set_visibility(False,True)
            elif kind == 'DirectionalLight':
                c = actor.get_component_by_class(u.DirectionalLightComponent)
                c.modify(); c.set_editor_property('atmosphere_sun_light',False)
            elif kind == 'PlayerStart':
                actor.modify()
                actor.set_actor_location(u.Vector(180,-70,100),False,False)
                actor.set_actor_rotation(u.Rotator(yaw=0),False)
        path = '/Game/Blender/Sandbox/MI_SandboxStars'
        sky_material = u.load_asset(path)
        if not sky_material:
            sky_material = u.AssetToolsHelpers.get_asset_tools().create_asset('MI_SandboxStars','/Game/Blender/Sandbox',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        u.MaterialEditingLibrary.set_material_instance_parent(sky_material,parent)
        u.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(sky_material,'SkyBrightness',0)
        u.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(sky_material,'StarBrightness',.6)
        u.EditorAssetLibrary.save_loaded_asset(sky_material)
        sky = next((a for a in eas.get_all_level_actors() if a.get_actor_label() == 'Sandbox stars'),None)
        if not sky:
            sky = eas.spawn_actor_from_class(u.StaticMeshActor,u.Vector(7415,2012,0))
        sky.set_actor_label('Sandbox stars'); sky.set_folder_path('Sandbox environment')
        sky.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Sphere.Sphere'))
        sky.static_mesh_component.set_material(0,sky_material)
        sky.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        sky.static_mesh_component.set_cast_shadow(False)
        sky.set_actor_scale3d(u.Vector(2000,2000,2000))
    report['receipt'] = str(out/'repair.json')
    (out/'repair.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('removed','old_locations')}))
    return report


def balance_computer(apply=False):
    """Normalize this one demo's extreme lights/emission for the shared exposure."""
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    assert world and world.get_path_name().split('.')[0] == TARGET
    assert not editor.get_game_world(), 'Stop Play before editing'
    actors = [a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
              if str(a.get_folder_path()) == 'ComputerStation']
    lib = u.MaterialEditingLibrary
    materials = {}
    for actor in actors:
        if not isinstance(actor,u.StaticMeshActor):
            continue
        for mat in actor.static_mesh_component.get_materials():
            if not isinstance(mat,u.MaterialInstanceConstant) or not mat.get_path_name().startswith('/Game/P1toP5_Bundle/'):
                continue
            params = {str(n):lib.get_material_instance_scalar_parameter_value(mat,n)
                      for n in lib.get_scalar_parameter_names(mat)
                      if 'intens' in str(n).lower() and 'em' in str(n).lower()}
            if any(v > 100 for v in params.values()):
                materials[mat.get_path_name()] = (mat,params)
    lights = [(a,c) for a in actors if 'SSSandboxLightBalanced' not in [str(t) for t in a.tags]
              for c in a.get_components_by_class(u.LightComponent)]
    report = {'apply':apply,'lights':len(lights),'emissive_materials':len(materials),
              'light_factor':.0001,'emission_factor':.00001}
    if apply:
        with u.ScopedEditorTransaction('Balance sandbox ComputerStation lights and emission'):
            for actor,component in lights:
                actor.modify();component.modify()
                component.set_intensity(component.intensity*.0001)
                actor.tags = list(actor.tags)+[u.Name('SSSandboxLightBalanced')]
            for actor in actors:
                for capture in actor.get_components_by_class(u.ReflectionCaptureComponent):
                    capture.modify();capture.set_editor_property('brightness',1.0)
            replacements = {}
            for path,(mat,params) in materials.items():
                name = 'MI_Sandbox_' + mat.get_name()
                dest = '/Game/Blender/Sandbox/ComputerMaterials/' + name
                child = u.load_asset(dest)
                if not child:
                    child = u.AssetToolsHelpers.get_asset_tools().create_asset(name,
                        '/Game/Blender/Sandbox/ComputerMaterials',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
                lib.set_material_instance_parent(child,mat)
                for param,value in params.items():
                    lib.set_material_instance_scalar_parameter_value(child,param,value*.00001)
                assert u.EditorAssetLibrary.save_loaded_asset(child)
                replacements[path] = child
            for actor in actors:
                if not isinstance(actor,u.StaticMeshActor):continue
                comp = actor.static_mesh_component
                for i,mat in enumerate(comp.get_materials()):
                    if mat and mat.get_path_name() in replacements:
                        comp.modify();comp.set_material(i,replacements[mat.get_path_name()])
    print(json.dumps(report))
    return report
