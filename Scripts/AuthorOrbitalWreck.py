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
EDIT = u.MaterialEditingLibrary


def prepare_mesh_materials(mesh):
    """Persist importer-parent usage overrides on private instances only."""
    for slot in mesh.get_editor_property('static_materials'):
        interface = slot.material_interface
        assert interface and interface.get_path_name().startswith(BASE+'/')
        material = interface.get_base_material()
        if material.get_path_name().startswith(BASE+'/'):
            material.set_editor_property('used_with_nanite', True)
            EDIT.recompile_material(material)
            assert LIB.save_loaded_asset(material, only_if_is_dirty=False)
        else:
            assert isinstance(interface, u.MaterialInstanceConstant)
            EDIT.set_material_usage_override(interface, u.MaterialUsage.MATUSAGE_NANITE, True, True)
            EDIT.update_material_instance(interface)
            assert LIB.save_loaded_asset(interface, only_if_is_dirty=False)


def author_sky():
    """Grade the existing owned sky directionally; this remains a distant cubemap."""
    path = ATM+'/M_OrbitalWreckSky'
    material = LIB.load_asset(path) if LIB.does_asset_exist(path) else LIB.duplicate_asset(ATM+'/M_RegionSky', path)
    assert material
    # Update one grading node in the private graph, never stack grades across reruns.
    if LIB.get_metadata_tag(material, 'SSWreckGrade') != '3':
        original = EDIT.get_material_property_input_node(material, u.MaterialProperty.MP_EMISSIVE_COLOR)
        assert original
        existing = next((node for node in EDIT.get_material_expressions(material)
                         if isinstance(node, u.MaterialExpressionCustom)
                         and node.get_editor_property('description') == 'World-direction warm flank and dark flight corridor'), None)
        grade = existing or EDIT.create_material_expression(material, u.MaterialExpressionCustom, 1600, 0)
        grade.set_editor_property('description', 'World-direction warm flank and dark flight corridor')
        grade.set_editor_property('output_type', u.CustomMaterialOutputType.CMOT_FLOAT3)
        pins = []
        for name in ('Sky', 'View'):
            item = u.CustomInput(); item.set_editor_property('input_name', name); pins.append(item)
        if not existing:
            grade.set_editor_property('inputs', pins)
        grade.set_editor_property('code', '''
float3 d = normalize(-View);
float warm = smoothstep(-0.05, 0.65, d.y) * smoothstep(-0.5, 0.75, d.x);
float corridor = pow(saturate(dot(d, float3(1,0,0))), 20.0);
float l = dot(Sky, float3(0.2126,0.7152,0.0722));
float3 cool = lerp(Sky, l * float3(0.25,0.48,0.72), 0.75);
float3 amber = l * float3(2.0,0.73,0.22);
float angle = 1.0 - dot(d, normalize(float3(0.78,0.55,0.3)));
float glow = 0.045 * exp(-angle * 18.0);
float disc = 2.0 * (1.0 - smoothstep(0.0001,0.00016,angle));
return lerp(cool, amber, warm) * (0.65 - 0.5*corridor) + float3(1.0,0.42,0.12)*glow + float3(1.0,0.85,0.55)*disc;
''')
        if not existing:
            view = EDIT.create_material_expression(material, u.MaterialExpressionCameraVectorWS, 1400, 200)
            assert EDIT.connect_material_expressions(original, '', grade, 'Sky')
            assert EDIT.connect_material_expressions(view, '', grade, 'View')
        assert EDIT.connect_material_property(grade, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
        LIB.set_metadata_tag(material, 'SSWreckGrade', '3')
        EDIT.layout_material_expressions(material)
        EDIT.recompile_material(material)
        assert LIB.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def main():
    out = ROOT/'Artifacts/OrbitalWreck'/uuid.uuid4().hex
    out.mkdir(parents=True)
    for name in ('DA_DeepSpaceLook', 'MI_DeepSpaceCloud', 'M_OrbitalWreckSky'):
        p = ROOT/'Content/SpaceSurvival/Licensed/Atmosphere'/(name+'.uasset')
        if p.exists():
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
        prepare_mesh_materials(mesh)
    look = LIB.load_asset(ATM+'/DA_DeepSpaceLook'); assert look
    station = LIB.load_asset('/Game/SpaceSurvival/Licensed/StationVisualPass/Meshes/SM_Station3Exterior')
    rock = lambda name: LIB.load_asset('/Game/Asteroid_Library/Static_Meshes/'+name)
    arc_rotation = u.MathLibrary.compose_rotators(u.Rotator(pitch=80,yaw=0,roll=20), u.Rotator(roll=90))
    # Major masses around the forward and turned view; fewer isolated metal strips.
    composition = [
        (meshes['BrokenArc'], (275000,200000,12000), (arc_rotation.pitch,arc_rotation.yaw,arc_rotation.roll), 190000),
        (meshes['BrokenArc'], (220000,-180000,-95000), (55,-10,-35), 175000),
        (station, (490000,-210000,155000), (15,-30,0), 28000),
        (meshes['KitBeam'], (305000,210000,115000), (15,-40,-60), 18000),
        (rock('SM_Asteroid_Barren_1'), (185000,-120000,35000), (20,35,70), 65000),
        (rock('SM_Asteroid_Barren_3'), (310000,245000,120000), (45,10,30), 72000),
        (rock('SM_AsteroidBarren_4'), (235000,195000,65000), (75,40,25), 42000),
        (rock('SM_AsteroidMineral_2'), (190000,195000,-85000), (20,35,70), 68000),
        (rock('SM_Asteroid_Barren_2'), (85000,220000,80000), (45,-20,10), 69000),
        (rock('SM_Asteroid_Barren_3'), (-65000,235000,-70000), (-25,70,30), 78000),
        (rock('SM_AsteroidFragment_2'), (100000,300000,15000), (10,40,70), 42000),
        (rock('SM_AsteroidMineral_1'), (360000,280000,180000), (50,15,20), 41000),
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
    look.set_editor_property('sky_material', author_sky())
    look.set_editor_property('ambient_intensity', 3.)
    look.set_editor_property('key_color', u.LinearColor(1.,.66,.36,1))
    look.set_editor_property('key_intensity', 4.)
    look.set_editor_property('override_flight_key_direction', True)
    look.set_editor_property('flight_key_rotation', u.Rotator(pitch=-18,yaw=-145,roll=0))
    look.set_editor_property('cloud_scale', u.Vector(650,220,350))
    look.set_editor_property('cloud_offset_a', u.Vector(65000,36000,-9000))
    look.set_editor_property('cloud_offset_b', u.Vector(115000,-42000,26000))
    cloud = look.get_editor_property('cloud_material')
    u.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(cloud, 'Density', .000032)
    u.MaterialEditingLibrary.set_material_instance_vector_parameter_value(cloud, 'Color', u.LinearColor(.23,.17,.11,1))
    for asset in (look, cloud):
        assert LIB.save_loaded_asset(asset)
    report['content_identity'] = []
    candidates = list((ROOT/'Content/SpaceSurvival/Licensed/OrbitalWreck').rglob('*.uasset'))
    candidates += [ROOT/'Content/SpaceSurvival/Licensed/Atmosphere'/(name+'.uasset')
                   for name in ('DA_DeepSpaceLook','MI_DeepSpaceCloud','M_OrbitalWreckSky')]
    for path in sorted(candidates):
        report['content_identity'].append({'path':str(path.relative_to(ROOT)),
                                           'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    report['lighting'] = {'key_rotation':[-18,-145,0], 'key_color':[1.,.66,.36],
                          'key_intensity':4., 'ambient_intensity':3., 'station_direction_restored':True}
    report['sky_limit'] = 'Directional grading and sun disc on owned cubemap; not procedural nebula volume.'
    (out/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (out.parent/'latest.json').write_text(json.dumps({'root':str(out)}), encoding='utf-8')
    u.log('ORBITAL_WRECK_AUTHORED_REQUIRES_RENDER')


if __name__ == '__main__':
    main()
