"""New-only station shell/material import; runtime evaluation remains separate."""
from pathlib import Path
import hashlib
import json
import re
from contextlib import contextmanager
import sys
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'ContentSource/StationShellCandidate'
OUTPUT = ROOT/'Saved/Validation'
BASE = '/Game/SpaceSurvival'
MESH = BASE+'/Meshes/SM_StationShellCandidateV1'
VERSION = 'StationShell1'
UV_VERSION = 'ObjectLocalBox1m1'
MESH_PACKAGE = ROOT/'Content/SpaceSurvival/Meshes/SM_StationShellCandidateV1.uasset'
BUILD_SETTINGS = {
    'recompute_normals': False,
    'recompute_tangents': True,
    'use_mikk_t_space': True,
    'use_full_precision_u_vs': True,
}
LIB = u.EditorAssetLibrary
EDIT = u.MaterialEditingLibrary


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    report = json.loads((SOURCE/'Report.json').read_text(encoding='utf-8'))
    validation = json.loads((SOURCE/'Validation.json').read_text(encoding='utf-8'))
    assert validation['source_report_sha256'] == sha(SOURCE/'Report.json')
    assert validation['triangles'] == report['evaluated_triangles'] == 85180
    assert validation['maximum_normal_unit_error'] < 1e-5
    assert validation['triangle_area_below_one_millionth_square_cm'] == 0
    assert validation['corridor_triangle_aabb_conflicts'] == validation['mica_corner_triangle_aabb_conflicts'] == 0
    assert not report['service_envelope_conflicting_parts']
    assert validation['uv_corner_records'] == 255540
    assert validation['uv_float32_degenerate_triangles'] == 0
    assert validation['uv_float32_minimum_absolute_determinant'] > 1e-6
    assert validation['uv_revision_sha256'] == sha(SOURCE/'UVRevision.json')
    for row in report['outputs']:
        assert sha(SOURCE/row['file']) == row['sha256'], row['file']
    return report


def material_path(row):
    return BASE+'/Materials/M_StationShell_'+row['name'].removeprefix('SSS_')


def validate_material(material, row):
    assert isinstance(material, u.Material)
    assert LIB.get_metadata_tag(material,'SSStationShellVersion') == VERSION
    assert material.get_editor_property('blend_mode') == u.BlendMode.BLEND_OPAQUE
    assert material.get_editor_property('shading_model') == u.MaterialShadingModel.MSM_DEFAULT_LIT
    for name, expected in [('Metallic',row['metallic']),('Roughness',row['roughness']),('Emission',row['emission_strength'])]:
        assert abs(EDIT.get_material_default_scalar_parameter_value(material,name)-expected) < 1e-5
    color = EDIT.get_material_default_vector_parameter_value(material,'Color')
    assert all(abs(getattr(color,axis)-expected)<1e-5 for axis,expected in zip(('r','g','b'),row['base_color']))
    expressions = EDIT.get_material_expressions(material)
    vectors = [e for e in expressions if isinstance(e, u.MaterialExpressionVectorParameter)]
    scalars = {str(e.get_editor_property('parameter_name')): e for e in expressions if isinstance(e, u.MaterialExpressionScalarParameter)}
    products = [e for e in expressions if isinstance(e, u.MaterialExpressionMultiply)]
    assert len(expressions) == 5 and len(vectors) == len(products) == 1
    assert set(scalars) == {'Metallic', 'Roughness', 'Emission'}
    assert str(vectors[0].get_editor_property('parameter_name')) == 'Color'
    for prop, expected in ((u.MaterialProperty.MP_BASE_COLOR, vectors[0]),
                           (u.MaterialProperty.MP_METALLIC, scalars['Metallic']),
                           (u.MaterialProperty.MP_ROUGHNESS, scalars['Roughness']),
                           (u.MaterialProperty.MP_EMISSIVE_COLOR, products[0])):
        assert EDIT.get_material_property_input_node(material, prop) == expected
    assert EDIT.get_inputs_for_material_expression(material, products[0]) == [vectors[0], scalars['Emission']]
    for prop in (u.MaterialProperty.MP_OPACITY, u.MaterialProperty.MP_OPACITY_MASK,
                 u.MaterialProperty.MP_WORLD_POSITION_OFFSET, u.MaterialProperty.MP_REFRACTION):
        assert EDIT.get_material_property_input_node(material, prop) is None
    assert not EDIT.get_material_used_textures(material)
    assert not material.get_editor_property('two_sided')


def material_statistics(material):
    u.AutomationLibrary.finish_loading_before_screenshot()
    statistics = EDIT.get_statistics(material)
    names = ('num_vertex_shader_instructions', 'num_pixel_shader_instructions',
             'num_samplers', 'num_vertex_texture_samples', 'num_pixel_texture_samples',
             'num_virtual_texture_samples', 'num_uv_scalars', 'num_interpolator_scalars')
    stats = {name: int(statistics.get_editor_property(name)) for name in names}
    assert stats['num_pixel_shader_instructions'] > 0, 'Compiled material statistics unavailable'
    return stats


def author_material(row):
    path = material_path(row)
    material = LIB.load_asset(path)
    if material:
        validate_material(material,row)
        return material
    folder,name = path.rsplit('/',1)
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,u.Material,u.MaterialFactoryNew())
    assert material
    material.set_editor_property('blend_mode',u.BlendMode.BLEND_OPAQUE)
    material.set_editor_property('shading_model',u.MaterialShadingModel.MSM_DEFAULT_LIT)
    color = EDIT.create_material_expression(material,u.MaterialExpressionVectorParameter,-500,0)
    color.set_editor_property('parameter_name','Color')
    color.set_editor_property('default_value',u.LinearColor(*row['base_color'],1))
    assert EDIT.connect_material_property(color,'',u.MaterialProperty.MP_BASE_COLOR)
    scalars={}
    for index,(name,value) in enumerate([('Metallic',row['metallic']),('Roughness',row['roughness']),('Emission',row['emission_strength'])]):
        node=EDIT.create_material_expression(material,u.MaterialExpressionScalarParameter,-500,200+index*150)
        node.set_editor_property('parameter_name',name);node.set_editor_property('default_value',value)
        scalars[name]=node
    assert EDIT.connect_material_property(scalars['Metallic'],'',u.MaterialProperty.MP_METALLIC)
    assert EDIT.connect_material_property(scalars['Roughness'],'',u.MaterialProperty.MP_ROUGHNESS)
    emission=EDIT.create_material_expression(material,u.MaterialExpressionMultiply,-150,500)
    assert EDIT.connect_material_expressions(color,'',emission,'A')
    assert EDIT.connect_material_expressions(scalars['Emission'],'',emission,'B')
    assert EDIT.connect_material_property(emission,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    EDIT.recompile_material(material)
    LIB.set_metadata_tag(material,'SSStationShellVersion',VERSION)
    assert LIB.save_loaded_asset(material,only_if_is_dirty=False)
    validate_material(material,row)
    return material



def approved_uv_migration(mesh):
    """Only the exact separately authored UV-less candidate may be replaced."""
    if mesh is None:
        return False
    if LIB.get_metadata_tag(mesh, 'SSStationShellSourceSHA256') == sha(SOURCE/'StationShellCandidate.obj'):
        if mesh.get_num_sections(0) == 7:
            return False
        failure = json.loads((SOURCE/'HistoricalEvidence/UVInterchangeSections/Failure.json').read_text(encoding='utf-8'))
        assert sha(MESH_PACKAGE) == failure['mesh_package_sha256'], 'Unreviewed section layout'
        assert mesh.get_num_sections(0) == failure['inspection']['sections'] == 232
        return True
    revision = json.loads((SOURCE/'UVRevision.json').read_text(encoding='utf-8'))
    prior = next(row for row in revision['prior_import'] if row['path'] == MESH)
    assert LIB.get_metadata_tag(mesh, 'SSStationShellVersion') == VERSION
    assert LIB.get_metadata_tag(mesh, 'SSStationShellSourceSHA256') == revision['prior_obj_sha256']
    assert sha(MESH_PACKAGE) == prior['sha256'], 'Unreviewed station mesh package; refusing replacement'
    return True


def surface_signature(mesh, phase):
    """Read built LOD0 triangles/normals independently of vertex splits or UVs."""
    directory = ROOT/'.agent/local/StationShellSession'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory/('Surface_'+phase+'.fbx')
    options = u.FbxExportOption()
    for name, value in {'ascii': True, 'level_of_detail': False, 'collision': False,
                        'export_source_mesh': False}.items():
        options.set_editor_property(name, value)
    task = u.AssetExportTask()
    for name, value in {'object': mesh, 'filename': str(path), 'automated': True,
                        'prompt': False, 'replace_identical': True,
                        'exporter': u.StaticMeshExporterFBX(), 'options': options}.items():
        task.set_editor_property(name, value)
    assert u.Exporter.run_asset_export_task(task) and path.is_file()
    text = path.read_text(encoding='utf-8-sig')
    arrays = {}
    for name, count, values in re.findall(
        r'\b(Vertices|PolygonVertexIndex|Normals)\s*:\s*\*(\d+)\s*\{\s*a:\s*([^}]*)\}', text, re.S
    ):
        numbers = values.replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').strip(',').split(',')
        assert name not in arrays and len(numbers) == int(count)
        arrays[name] = numbers
    positions = [float(value) for value in arrays['Vertices']]
    normals = [float(value) for value in arrays['Normals']]
    indices = [int(value) for value in arrays['PolygonVertexIndex']]
    assert len(indices) == 85180*3 and len(normals) == len(indices)*3
    assert all(value < 0 if i % 3 == 2 else value >= 0 for i, value in enumerate(indices))
    corners = []
    for i, value in enumerate(indices):
        index = -value-1 if value < 0 else value
        corners.append(tuple(round(v, 6) for v in positions[index*3:index*3+3]+normals[i*3:i*3+3]))
    triangles = []
    for i in range(0, len(corners), 3):
        tri = tuple(corners[i:i+3])
        triangles.append(min(tri, tri[1:]+tri[:1], tri[2:]+tri[:2]))
    raw = json.dumps(sorted(triangles), separators=(',', ':')).encode('utf-8')
    return {'triangle_position_normal_sha256': hashlib.sha256(raw).hexdigest(),
            'triangles': len(triangles), 'rounding_digits': 6,
            'method': 'Built LOD0 FBX expanded triangle positions and normals, winding retained; UV and vertex storage splits excluded.'}


def validate_mesh(mesh,report):
    editor=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    assert isinstance(mesh,u.StaticMesh) and mesh.get_path_name().split('.')[0] == MESH
    assert LIB.get_metadata_tag(mesh,'SSStationShellVersion') == VERSION
    assert LIB.get_metadata_tag(mesh,'SSStationShellSourceSHA256') == sha(SOURCE/'StationShellCandidate.obj')
    assert LIB.get_metadata_tag(mesh, 'SSStationShellUVVersion') == UV_VERSION
    assert editor.get_num_uv_channels(mesh, 0) == 1
    build = editor.get_lod_build_settings(mesh, 0)
    for name, expected in BUILD_SETTINGS.items():
        assert build.get_editor_property(name) == expected, name
    assert editor.get_lod_count(mesh) == 1 and mesh.get_num_sections(0) == 7
    assert mesh.get_num_triangles(0) == report['evaluated_triangles']
    assert editor.get_simple_collision_count(mesh) == 0
    assert all(not editor.is_section_collision_enabled(mesh,0,i) for i in range(7))
    assert mesh.get_editor_property('body_setup').get_editor_property('default_instance').get_editor_property('collision_enabled') == u.CollisionEnabled.NO_COLLISION
    bounds=mesh.get_bounds()
    actual=[[getattr(bounds.origin,a)+sign*getattr(bounds.box_extent,a) for a in ('x','y','z')] for sign in (-1,1)]
    assert all(abs(actual[e][a]-report['bounds_cm'][e][a])<.04 for e in range(2) for a in range(3))
    expected={r['name']:r for r in report['materials']}
    slots = mesh.get_editor_property('static_materials')
    names = [str(slot.get_editor_property('imported_material_slot_name')) for slot in slots]
    assert len(slots) == len(set(names)) == 7 and set(names) == set(expected)
    for slot in slots:
        name=str(slot.get_editor_property('imported_material_slot_name'))
        material=slot.get_editor_property('material_interface')
        assert material.get_path_name().split('.')[0] == material_path(expected[name])
        validate_material(material,expected[name])
    return {'path':mesh.get_path_name(),'triangles':mesh.get_num_triangles(0),'vertices':editor.get_number_verts(mesh,0),'sections':7,'bounds_cm':actual,'collision':'NoCollision', 'uv_channels':1, 'build_settings':BUILD_SETTINGS}



@contextmanager
def legacy_obj_import():
    """Scope factory routing to this import; restore both editor CVars afterward."""
    names = ('Interchange.FeatureFlags.Import.OBJ', 'Interchange.FeatureFlags.Import.FBX')
    previous = {name: u.SystemLibrary.get_console_variable_int_value(name) for name in names}
    try:
        for name in names:
            u.SystemLibrary.execute_console_command(None, name+' 0')
            assert u.SystemLibrary.get_console_variable_int_value(name) == 0
        yield
    finally:
        for name, value in previous.items():
            u.SystemLibrary.execute_console_command(None, name+' '+str(value))
            assert u.SystemLibrary.get_console_variable_int_value(name) == value


def author_mesh(report,materials):
    mesh=LIB.load_asset(MESH)
    migration = approved_uv_migration(mesh)
    if mesh and not migration:
        validate_mesh(mesh,report)
        return mesh, None
    before_surface = surface_signature(mesh, 'before_legacy_repair') if migration else None
    options=u.FbxImportUI()
    for key,value in {'import_mesh':True,'import_as_skeletal':False,'import_materials':False,'import_textures':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH}.items():
        options.set_editor_property(key,value)
    data=options.get_editor_property('static_mesh_import_data')
    for key,value in {'combine_meshes':True,'auto_generate_collision':False,'generate_lightmap_u_vs':False,'import_uniform_scale':1.0,'convert_scene':False,'convert_scene_unit':False,'force_front_x_axis':False,'normal_import_method':u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS,'normal_generation_method':u.FBXNormalGenerationMethod.MIKK_T_SPACE,'import_translation':u.Vector(0,0,0),'import_rotation':u.Rotator(0,0,0)}.items():
        data.set_editor_property(key,value)
    task=u.AssetImportTask()
    for key,value in {'filename':str(SOURCE/'StationShellCandidate.obj'),'destination_path':BASE+'/Meshes','destination_name':'SM_StationShellCandidateV1','automated':True,'replace_existing':migration,'replace_existing_settings':True,'save':False,'factory':u.FbxFactory(),'options':options}.items():
        task.set_editor_property(key,value)
    with legacy_obj_import():
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes=[LIB.load_asset(p) for p in task.get_editor_property('imported_object_paths')]
    meshes=[m for m in meshes if isinstance(m,u.StaticMesh)]
    assert len(meshes)==1 and meshes[0].get_path_name().split('.')[0]==MESH
    mesh=meshes[0]
    for i,slot in enumerate(mesh.get_editor_property('static_materials')):
        mesh.set_material(i,materials[str(slot.get_editor_property('imported_material_slot_name'))])
    editor=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    build = editor.get_lod_build_settings(mesh, 0)
    for name, value in BUILD_SETTINGS.items():
        build.set_editor_property(name, value)
    editor.set_lod_build_settings(mesh, 0, build)
    u.AutomationLibrary.finish_loading_before_screenshot()
    after_surface = surface_signature(mesh, 'after_legacy_repair')
    if before_surface is not None:
        assert before_surface == after_surface, 'UV revision changed built geometry or normals'
    editor.remove_collisions(mesh)
    for i in range(mesh.get_num_sections(0)):
        editor.enable_section_collision(mesh,False,0,i)
    body=mesh.get_editor_property('body_setup');instance=body.get_editor_property('default_instance')
    instance.set_editor_property('collision_profile_name','NoCollision')
    instance.set_editor_property('collision_enabled',u.CollisionEnabled.NO_COLLISION)
    body.set_editor_property('default_instance',instance)
    LIB.set_metadata_tag(mesh,'SSStationShellVersion',VERSION)
    LIB.set_metadata_tag(mesh,'SSStationShellUVVersion',UV_VERSION)
    LIB.set_metadata_tag(mesh,'SSStationShellSourceSHA256',sha(SOURCE/'StationShellCandidate.obj'))
    validate_mesh(mesh, report)
    assert LIB.save_loaded_asset(mesh,only_if_is_dirty=False)
    return mesh, {'before':before_surface, 'after':after_surface, 'same_built_surface':before_surface == after_surface if before_surface else None}


def main(validate_only=False):
    protected={p:sha(p) for folder in ('Source','Config','Content') for p in (ROOT/folder).rglob('*') if p.is_file()}
    report=sources()
    migration_record = None
    migration = not validate_only and approved_uv_migration(LIB.load_asset(MESH))
    if migration:
        protected.pop(MESH_PACKAGE)
    if validate_only:
        mesh=LIB.load_asset(MESH)
    else:
        materials={row['name']:author_material(row) for row in report['materials']}
        mesh, migration_record=author_mesh(report,materials)
    record=validate_mesh(mesh,report)
    record['materials'] = []
    for row in report['materials']:
        material = LIB.load_asset(material_path(row))
        validate_material(material, row)
        record['materials'].append({'path':material.get_path_name(), 'parameters':row, 'graph_connections_verified':True, 'textures':[], 'compiled_statistics':material_statistics(material)})
    record['statistics_limit'] = 'Editor compiled shader estimates; not measured frame time or native art acceptance.'
    record['uv_contract'] = 'One full-precision object-local box-projected UV channel at one-metre repeat; intentional seams. Imported normals preserved, tangents computed with MikkTSpace.'
    record['uv_revision'] = migration_record
    record['author_sha256'] = sha(Path(__file__))
    record['source_validation_sha256'] = sha(SOURCE/'Validation.json')
    assert all(sha(p)==digest for p,digest in protected.items()),'Existing game files changed'
    record.update(status='SEPARATE_STATION_SHELL_PERSISTED_NOT_RUNTIME_ADOPTED',existing_files_unchanged=len(protected),source_report_sha256=sha(SOURCE/'Report.json'),engine=u.SystemLibrary.get_engine_version(),limits=['Source candidate only. No runtime selection, collision integration, performance or owner acceptance.'])
    assets=[MESH]+[material_path(row) for row in report['materials']]
    record['packages']=[]
    for asset in assets:
        path=ROOT/'Content'/(asset.removeprefix('/Game/')+'.uasset')
        record['packages'].append({'path':asset,'bytes':path.stat().st_size,'sha256':sha(path)})
    OUTPUT.mkdir(parents=True,exist_ok=True)
    (OUTPUT/('StationShellPersisted.json' if validate_only else 'StationShellImport.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    return record


if __name__=='__main__':
    main('--validate-only' in sys.argv)
