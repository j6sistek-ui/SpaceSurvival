"""Preserve the downloaded complete cargo ship in a single-place Level Instance.

The source showcase contains a complete ship with its interior, lights, ropes
and gate Blueprints. A private level copy removes only the vendor camera rig,
global environment and giant sky sphere. No station or vendor map is saved.
"""
import hashlib
import json
import re
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Artifacts/BuildingLibrary'
SOURCE='/Game/CargoShip/Maps/L_Showcase'
TARGET='/Game/BuildingLibrary/Ships/L_CargoShip_Complete'
BP_PATH='/Game/BuildingLibrary/Assembled/Ships/BP_CargoShip_Complete'
source_file=ROOT/'Content/CargoShip/Maps/L_Showcase.umap'
station_file=ROOT/'Content/OutpostSandbox/L_AsteroidOutpost.umap'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=OUT/'cargo-prefab.json'
prior=json.loads(receipt.read_text()) if receipt.exists() else {}
target_file=ROOT/'Content/BuildingLibrary/Ships/L_CargoShip_Complete.umap'
bp_file=ROOT/'Content/BuildingLibrary/Assembled/Ships/BP_CargoShip_Complete.uasset'
if receipt.exists():
    history=OUT/('cargo-prefab-'+sha(receipt)[:12]+'.json')
    if not history.exists():
        history.write_bytes(receipt.read_bytes())
report={'source':SOURCE,'target':TARGET,'blueprint':BP_PATH,'removed':[],'errors':[],
        'source_before':sha(source_file),'station_before':sha(station_file),'status':'running'}
try:
    level=u.get_editor_subsystem(u.LevelEditorSubsystem)
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    resume=u.EditorAssetLibrary.does_asset_exist(TARGET)
    if resume:
        explicit=re.search(r'-SSResumeCargoMapSha=([a-fA-F0-9]{64})',u.SystemLibrary.get_command_line())
        expected=prior.get('target_sha256') or (explicit.group(1).lower() if explicit else None)
        assert expected and sha(target_file)==expected, 'Preserve unrecognized or edited cargo map'
        assert prior.get('source_before')==sha(source_file), 'Source changed since private copy'
        report['removed']=prior.get('removed',[])
    assert level.load_level(TARGET if resume else SOURCE)
    all_actors=actors.get_all_level_actors()
    removed_this_run=0
    excluded={'PostProcessVolume','ExponentialHeightFog','DirectionalLight','SkyLight','SkyAtmosphere',
              'VolumetricCloud','CineCameraActor','CameraActor','LevelSequenceActor','GroupActor','PCGWorldActor'}
    for actor in all_actors:
        remove=not resume and actor.get_class().get_name() in excluded
        if actor.get_class().get_name()=='StaticMeshActor':
            mesh=actor.static_mesh_component.static_mesh
            origin,extent=actor.get_actor_bounds(False)
            remove=remove or (not resume and mesh and mesh.get_path_name()=='/Engine/BasicShapes/Sphere.Sphere' and max(extent.x,extent.y,extent.z)>100000)
            remove=remove or (mesh and mesh.get_path_name()=='/Game/CargoShip/Meshes/SM_Planet.SM_Planet' and max(extent.x,extent.y,extent.z)>100000)
        if remove:
            report['removed'].append({'label':actor.get_actor_label(),'class':actor.get_class().get_name()})
            assert actors.destroy_actor(actor)
            removed_this_run+=1
    kept=actors.get_all_level_actors()
    # UE5.8 cannot render translucent materials through Nanite. Preserve the
    # vendor meshes; opt only private placed glass components out of Nanite.
    glass_fixed=[]
    for actor in kept:
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            mesh=component.static_mesh
            if not mesh or not mesh.get_editor_property('nanite_settings').enabled:
                continue
            translucent=any(m and m.get_base_material().get_editor_property('blend_mode') not in
                            (u.BlendMode.BLEND_OPAQUE,u.BlendMode.BLEND_MASKED)
                            for m in component.get_materials())
            if translucent and not component.get_editor_property('disallow_nanite'):
                component.set_editor_property('disallow_nanite',True)
                glass_fixed.append(actor.get_actor_label()+':'+component.get_name())
    report['private_translucent_components_fixed']=glass_fixed
    hull=next(a for a in kept if isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh and
              a.static_mesh_component.static_mesh.get_name()=='SM_SpaceShip_Outer_Body2')
    center,extent=hull.get_actor_bounds(False)
    anchor=u.Vector(center.x,center.y,center.z-extent.z)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if not resume:
        for actor in kept:
            if not actor.get_attach_parent_actor():
                assert actor.set_actor_location(actor.get_actor_location()-anchor,False,False)
        assert u.EditorLoadingAndSavingUtils.save_map(world,TARGET)
    else:
        assert anchor.length()<1., 'Existing private cargo map has an unexpected pivot'
        if glass_fixed or removed_this_run:
            assert u.EditorLoadingAndSavingUtils.save_map(world,TARGET)
    report.update(retained_actors=len(kept),anchor=[anchor.x,anchor.y,anchor.z],
                  dimensions_cm=[2*extent.x,2*extent.y,2*extent.z],target_sha256=sha(target_file))
    receipt.write_text(json.dumps(report,indent=2),encoding='utf-8')
    if u.EditorAssetLibrary.does_asset_exist(BP_PATH):
        assert prior.get('blueprint_sha256')==sha(bp_file), 'Preserve unrecognized or edited ship Blueprint'
        bp=u.load_asset(BP_PATH)
    else:
        bp=u.BlueprintEditorLibrary.create_blueprint_asset_with_parent(BP_PATH,u.LevelInstance)
    assert bp,'LevelInstance Blueprint could not be created'
    u.BlueprintEditorLibrary.compile_blueprint(bp)
    cdo=u.get_default_object(bp.generated_class())
    cdo.set_editor_property('world_asset',u.load_asset(TARGET))
    assert u.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False)
    ref=u.Collection(container='Game',name='SS_01_Assembled___Drag_These',share_type=u.CollectionShareType.LOCAL)
    manager=u.get_editor_subsystem(u.CollectionManagerSubsystem)
    manager.add_asset_to_collection(ref,u.SoftObjectPath(BP_PATH+'.BP_CargoShip_Complete'))
    assert BP_PATH in {str(a.package_name) for a in manager.get_assets_in_collection(ref)}
    report.update(status='PASS',blueprint_sha256=sha(bp_file),
                  instance_world=str(cdo.get_editor_property('world_asset')),
                  target_sha256=sha(ROOT/'Content/BuildingLibrary/Ships/L_CargoShip_Complete.umap'))
except Exception as error:
    report['status']='FAILED'
    report['errors'].append(str(error))
    raise
finally:
    report['source_unchanged']=sha(source_file)==report['source_before']
    report['station_unchanged']=sha(station_file)==report['station_before']
    if not report['source_unchanged'] or not report['station_unchanged']:
        report['status']='FAILED'
        report['errors'].append('Protected map bytes changed during cargo authoring')
    (OUT/'cargo-prefab.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.log('CARGO_PREFAB '+report['status'])
