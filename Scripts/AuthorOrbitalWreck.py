"""Import private wreck derivatives and author the reference composition.

Run in a rendering-enabled editor after PrepareOrbitalWreck and the Editor build.
Backs up the private look/cloud before changes; never saves vendor packages.
"""
import hashlib
import json
from pathlib import Path
import shutil
import uuid
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
BASE = '/Game/SpaceSurvival/Licensed/OrbitalWreck'
ATM = '/Game/SpaceSurvival/Licensed/Atmosphere'
LIB = u.EditorAssetLibrary


def main():
    out = ROOT/'Artifacts/OrbitalWreck'/uuid.uuid4().hex
    out.mkdir(parents=True)
    for name in ('DA_DeepSpaceLook', 'MI_DeepSpaceCloud'):
        p = ROOT/'Content/SpaceSurvival/Licensed/Atmosphere'/(name+'.uasset')
        shutil.copy2(p, out/p.name)
    LIB.make_directory(BASE)
    report = {'status': 'AUTHORED_REQUIRES_RENDER', 'imports': [], 'placements': [], 'backup': str(out)}
    meshes = {}
    for name in ('BrokenArc', 'RingFragment', 'KitBeam'):
        target = BASE+'/'+name+'/SM_'+name
        mesh = LIB.load_asset(target) if LIB.does_asset_exist(target) else None
        if not mesh:
            pipeline = u.new_object(u.InterchangeGenericAssetsPipeline, name='Wreck'+name)
            for key, value in {'asset_name':'SM_'+name, 'use_source_name_for_asset':False,
                               'asset_type_sub_folders':False, 'scene_name_sub_folder':False}.items():
                pipeline.set_editor_property(key, value)
            pipeline.get_editor_property('mesh_pipeline').set_editor_property('import_skeletal_meshes', False)
            pipeline.get_editor_property('animation_pipeline').set_editor_property('import_animations', False)
            params = u.ImportAssetParameters()
            params.set_editor_property('is_automated', True)
            params.set_editor_property('replace_existing', False)
            params.set_editor_property('override_pipelines', [u.SoftObjectPath(pipeline.get_path_name())])
            manager = u.InterchangeManager.get_interchange_manager_scripted()
            source = ROOT/'.agent/local/OrbitalWreck'/(name+'.glb')
            assets = manager.import_asset(BASE+'/'+name, manager.create_source_data(str(source)), params)
            candidates = [a for a in assets if isinstance(a, u.StaticMesh)]
            assert len(candidates) == 1
            mesh = candidates[0]
            if mesh.get_path_name().split('.')[0] != target:
                assert LIB.rename_asset(mesh.get_path_name(), target)
                mesh = LIB.load_asset(target)
            u.get_editor_subsystem(u.StaticMeshEditorSubsystem).remove_collisions(mesh)
            for asset in assets:
                if isinstance(asset, u.Texture):
                    asset.set_editor_property('max_texture_size', 2048)
                assert LIB.save_loaded_asset(asset)
            assert LIB.save_loaded_asset(mesh)
            report['imports'].append({'path':target,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
        meshes[name] = mesh
    look = LIB.load_asset(ATM+'/DA_DeepSpaceLook'); assert look
    station = LIB.load_asset('/Game/SpaceSurvival/Licensed/StationVisualPass/Meshes/SM_Station3Exterior')
    # Near frame, dominant arc, detached section and small distant landmark.
    composition = [
        (meshes['BrokenArc'], (225000,115000,12000), (80,0,20), 115000),
        (meshes['RingFragment'], (170000,-145000,-90000), (45,20,-35), 110000),
        (meshes['RingFragment'], (280000,125000,98000), (60,-25,45), 38000),
        (station, (490000,-210000,155000), (15,-30,0), 38000),
        (meshes['RingFragment'], (345000,155000,-42000), (-30,15,90), 15000),
        (meshes['KitBeam'], (190000,110000,75000), (20,25,55), 22000),
        (meshes['KitBeam'], (215000,85000,-65000), (-35,10,20), 18000),
        (meshes['KitBeam'], (260000,145000,115000), (15,-40,-60), 12000),
    ]
    placements = []
    for mesh, center, rotation, radius in composition:
        assert mesh
        item = u.SSSceneryPlacement()
        for key, value in {'mesh':mesh, 'center':u.Vector(*center),
                           'rotation':u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]),
                           'radius':radius}.items():
            item.set_editor_property(key, value)
        placements.append(item)
        report['placements'].append({'mesh':mesh.get_path_name(),'center_cm':center,'rotation':rotation,'radius_cm':radius})
    look.set_editor_property('structure_composition', placements)
    look.set_editor_property('ambient_intensity', 5.)
    look.set_editor_property('key_color', u.LinearColor(1.,.66,.36,1))
    look.set_editor_property('key_intensity', 4.)
    look.set_editor_property('cloud_scale', u.Vector(650,220,350))
    look.set_editor_property('cloud_offset_a', u.Vector(65000,36000,-9000))
    look.set_editor_property('cloud_offset_b', u.Vector(115000,-42000,26000))
    cloud = look.get_editor_property('cloud_material')
    u.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(cloud, 'Density', .000032)
    u.MaterialEditingLibrary.set_material_instance_vector_parameter_value(cloud, 'Color', u.LinearColor(.23,.17,.11,1))
    for asset in (look, cloud):
        assert LIB.save_loaded_asset(asset)
    (out/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (out.parent/'latest.json').write_text(json.dumps({'root':str(out)}), encoding='utf-8')
    u.log('ORBITAL_WRECK_AUTHORED_REQUIRES_RENDER')


if __name__ == '__main__':
    main()
