"""Five physical service markers; root owns map loading, asset saves and capture.

Only new NoCollision StaticMeshActors and nine private assets are staged. Native
services, supplied furniture, lights, floor geometry and source materials stay.
"""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from StationOperationsAccessMarkerGeometry import geometry, validate

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.agent/local/StationRefinement'
MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/OperationsAccessMarkers20261007'
PREFIX = 'Refine/OperationsAccess/'
PLAN = LOCAL / 'StationOperationsAccessMarkersPlan1.json'
PLAN_SHA = 'd0f30fea95f455c5701238ed8aaef42c3aa32031bea937182b74140723e790a3'
GEOMETRY_SHA = '0c100892810f5ed1a0335fc70cca0f8c288fb0158d3a37328abc8dcd85d08ad0'
SERVICES_SHA = 'b84699a20232f73c3af6de762cb62a94fc0ea76a82ccf40051aac6e6711dce59'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def path(obj):
    return obj.get_path_name() if obj else None


def resolve(library, identity):
    names = [name for name in dir(library) if name.replace('_', '').lower() == identity.lower()
             and callable(getattr(library, name, None))]
    require(len(names) == 1, 'Exact registered native API differs: ' + identity + '; ' + str(names))
    function = getattr(library, names[0])
    return function, {'python_name': names[0], 'cpp_identity': identity, 'doc': str(function.__doc__)}


def plan():
    require(sha(PLAN) == PLAN_SHA and sha(ROOT/'Scripts/StationOperationsAccessMarkerGeometry.py') == GEOMETRY_SHA,
            'Frozen marker design changed')
    value = json.loads(PLAN.read_text())
    data = geometry(); validate(data)
    require(value['geometry_source_sha256'] == GEOMETRY_SHA and value['services5_sha256'] == SERVICES_SHA and
            value['services5_completed_standing_evidence_used'] and not value['services5_aggregate_success'] and
            len(value['placements']) == 5 and value['vertex_count'] == len(data['positions']) == 5768 and
            value['triangle_count'] == len(data['triangles']) == 2980 and
            {int(k): v for k, v in value['material_triangle_counts'].items()} == dict(Counter(data['material_ids'])) and
            value['mesh']['bounds_cm'] == data['bounds_cm'] and
            value['native_asset_plan']['total_private_assets'] == 9, 'Reviewed physical marker population differs')
    return value


def _buffers(u, positions, normals, uvs, triangles):
    return u.GeometryScriptSimpleMeshBuffers(vertices=[u.Vector(*p) for p in positions],
        normals=[u.Vector(*p) for p in normals], uv0=[u.Vector2D(*p) for p in uvs],
        triangles=[u.IntVector(*p) for p in triangles])


def _bulk_ids(dynamic, u):
    function, _ = resolve(u.GeometryScript_Materials, 'GetAllTriangleMaterialIDs')
    result = function(dynamic)
    require(isinstance(result, tuple) and len(result) == 3 and result[0] == dynamic and result[2],
            'Exact bulk material-ID tuple differs')
    return list(u.GeometryScript_List.convert_index_list_to_array(result[1]))


def _attributes(dynamic, triangle, u):
    uv_function, _ = resolve(u.GeometryScript_MeshQueries, 'GetTriangleUVs')
    normal_function, _ = resolve(u.GeometryScript_MeshQueries, 'GetTriangleNormals')
    uv_result, normal_result = uv_function(dynamic, 0, triangle), normal_function(dynamic, triangle)
    require(isinstance(uv_result, tuple) and len(uv_result) == 4 and uv_result[3] and
            isinstance(normal_result, tuple) and len(normal_result) == 5 and normal_result[0] == dynamic and normal_result[4],
            'Exact native UV/split-normal return tuple differs')
    return {'uvs': [list(p.to_tuple()) for p in uv_result[:3]],
            'normals': [list(p.to_tuple()) for p in normal_result[1:4]]}


def native_api_preflight(u):
    """Exercise one triangle before content load; no package or actor mutation."""
    append, append_api = resolve(u.GeometryScript_MeshEdits, 'AppendBuffersToMesh')
    enable, enable_api = resolve(u.GeometryScript_Materials, 'EnableMaterialIDs')
    dynamic = u.DynamicMesh(); enable(dynamic)
    result = append(dynamic, _buffers(u, [[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]],
        [[0.,0.,1.]]*3, [[0.,0.],[1.,0.],[0.,1.]], [[0,1,2]]), material_id=2)
    require(isinstance(result, tuple) and len(result) == 2 and result[0] == dynamic and
            list(u.GeometryScript_List.convert_index_list_to_array(result[1])) == [0] and
            dynamic.get_triangle_count() == 1 and _bulk_ids(dynamic,u) == [2],
            'Entry native buffer/material-ID preflight failed')
    attributes = _attributes(dynamic,0,u)
    require(attributes == {'uvs':[[0.,0.],[1.,0.],[0.,1.]],'normals':[[0.,0.,1.]]*3},
            'Entry UV/split-normal buffer preflight failed')
    options = u.GeometryScriptCreateNewStaticMeshAssetOptions(enable_collision=False, enable_nanite=False,
        enable_recompute_normals=False, enable_recompute_tangents=False, use_original_vertex_order=True)
    require(not options.get_editor_property('enable_collision') and
            not options.get_editor_property('enable_recompute_normals'), 'Static options reflection differs')
    slot = u.StaticMaterial(material_slot_name='CheckedRole')
    require(str(slot.get_editor_property('material_slot_name')) == 'CheckedRole', 'Static slot reflection differs')
    require(callable(getattr(u.GeometryScript_AssetUtils,'copy_mesh_from_static_mesh_v2',None)),
            'Exact native static source-model copy export missing')
    classes = {}
    for name in ('MaterialExpressionConstant','MaterialExpressionConstant3Vector','MaterialExpressionVectorParameter',
                 'MaterialExpressionScalarParameter','MaterialExpressionTime','MaterialExpressionAdd',
                 'MaterialExpressionMultiply','MaterialExpressionSine'):
        cdo = u.get_default_object(getattr(u,name))
        require(cdo and cdo.get_class().get_name() == name, 'Native material node class missing: '+name)
        classes[name] = {'inputs':list(u.MaterialEditingLibrary.get_material_expression_input_names(cdo)),
                         'outputs':list(u.MaterialEditingLibrary.get_material_expression_output_names(cdo))}
    _, ids_api = resolve(u.GeometryScript_Materials, 'GetAllTriangleMaterialIDs')
    _, uv_api = resolve(u.GeometryScript_MeshQueries,'GetTriangleUVs')
    _, normal_api = resolve(u.GeometryScript_MeshQueries,'GetTriangleNormals')
    return {'append':append_api,'enable_ids':enable_api,'bulk_ids':ids_api,'uvs':uv_api,'normals':normal_api,
            'sample_triangle_count':1,'sample_attributes':attributes,'material_classes':classes,
            'static_mesh_options_have_materials_map':False}


def service_records(actors, u, value):
    from InspectStationOperationsCrewContacts import transform
    result = {}
    for row in value['placements']:
        original = row['original_terminal']
        found = [a for a in actors if a.get_path_name().split(':PersistentLevel.')[-1] ==
                 original['actor'].split(':PersistentLevel.')[-1]]
        require(len(found) == 1 and isinstance(found[0],u.SSOutpostTerminal), 'Original terminal identity missing')
        actor = found[0]
        interaction = {k: path(actor.get_editor_property(k)) if k == 'presentation_target' else
            float(actor.get_editor_property(k)) if k == 'use_distance' else str(actor.get_editor_property(k))
            for k in ('display_name','description','action','use_distance','presentation_target')}
        require(transform(actor.get_actor_transform()) == original['pose'] and
                interaction == original['preserved_interaction'] and
                actor.get_actor_label() == 'Services/'+row['service'], 'Original service pose/action/access changed')
        result[row['service']] = {'actor':path(actor),'pose':original['pose'],'interaction':interaction}
    return result


def support_records(world, u, value, ignored=None):
    from RefineStationWorkroomComposition import _hit
    result = []
    for row in value['placements']:
        contacts=[]
        for prior in row['prior_floor_contacts']:
            point=prior['point_cm']
            hit=_hit(u.SystemLibrary.line_trace_single_by_profile(world,
                u.Vector(point[0],point[1],18.),u.Vector(point[0],point[1],-35.),
                'Pawn',False,ignored or [],u.DrawDebugTrace.NONE,True))
            contacts.append({'point_cm':point,'hit':hit})
            require(hit and hit['label']=='Ground/Operations' and hit['component']=='StaticMeshComponent0' and
                    not hit['initial_overlap'] and math.dist(hit['point'],point)<.08 and hit['normal'][2]>=.7,
                    'Marker footprint lacks actual retained floor support: '+row['service'])
        capsules={}
        for half in (75.,88.):
            point=row['centre_cm']; center=u.Vector(point[0],point[1],point[2]+half+3.)
            hit=_hit(u.SystemLibrary.capsule_trace_single_by_profile(world,center,center,34.,half,
                'Pawn',False,ignored or [],u.DrawDebugTrace.NONE,True))
            capsules[str(half)]=hit
            require(hit is None,'Marker standing capsule blocked: '+row['service'])
        result.append({'service':row['service'],'floor_contacts':contacts,'capsule_hits':capsules})
    require(sum(len(r['floor_contacts']) for r in result)==65,'Exact footprint sample population differs')
    return result


def _materials(value,u):
    tools,edit=u.AssetToolsHelpers.get_asset_tools(),u.MaterialEditingLibrary
    assets=[]; receipts=[]; role_materials={}
    for role,name in (('GRAPHITE_SATIN_FRAME','M_Frame'),('SLOW_ACCENT_LENS','M_AccentLens'),
                      ('TITANIUM_FASTENERS','M_Fasteners')):
        require(not u.EditorAssetLibrary.does_asset_exist(PRIVATE+'/'+name),'Preserve previous marker material')
        material=tools.create_asset(name,PRIVATE,u.Material,u.MaterialFactoryNew())
        require(isinstance(material,u.Material),'Private marker material creation failed')
        assets.append(material);role_materials[role]=material;nodes=[]
        material.set_editor_property('blend_mode',u.BlendMode.BLEND_OPAQUE)
        material.set_editor_property('shading_model',u.MaterialShadingModel.MSM_DEFAULT_LIT)
        material.set_editor_property('two_sided',False)
        def node(cls,**props):
            obj=edit.create_material_expression(material,getattr(u,cls)); require(obj,'Cannot create '+cls)
            actual={}
            for key,val in props.items():
                obj.set_editor_property(key,val)
                native=obj.get_editor_property(key)
                if isinstance(val,u.LinearColor):
                    actual[key]=[float(getattr(native,c)) for c in ('r','g','b','a')]
                    require(actual[key]==[float(getattr(val,c)) for c in ('r','g','b','a')],
                            'Marker color graph readback differs')
                elif isinstance(val,(float,int)):
                    actual[key]=float(native)
                    require(abs(actual[key]-val)<1.e-6,'Marker numeric graph readback differs')
                else:
                    actual[key]=str(native)
                    require(actual[key]==str(val),'Marker named graph readback differs')
            nodes.append({'class':cls,'properties':actual})
            return obj
        def link(a,b,pin='',output=''):
            require(edit.connect_material_expressions(a,output,b,pin),'Marker shader connection failed')
        def prop(a,key,output=''):
            require(edit.connect_material_property(a,output,getattr(u.MaterialProperty,key)),
                    'Marker shader output failed '+key)
        settings=value['material_plan'][role]
        if role!='SLOW_ACCENT_LENS':
            prop(node('MaterialExpressionConstant3Vector',constant=u.LinearColor(*settings['base_color_linear'],1.)),
                 'MP_BASE_COLOR')
            for key,field in (('MP_METALLIC','metallic'),('MP_ROUGHNESS','roughness'),('MP_SPECULAR','specular')):
                prop(node('MaterialExpressionConstant',r=settings[field]),key)
        else:
            accent=node('MaterialExpressionVectorParameter',parameter_name='Accent',default_value=u.LinearColor(.03,.62,1.,1.))
            prop(accent,'MP_BASE_COLOR','RGB')
            prop(node('MaterialExpressionConstant',r=.32),'MP_ROUGHNESS')
            prop(node('MaterialExpressionConstant',r=.1),'MP_METALLIC')
            prop(node('MaterialExpressionConstant',r=.28),'MP_SPECULAR')
            phase=node('MaterialExpressionScalarParameter',parameter_name='PhaseSeconds',default_value=0.)
            clock=node('MaterialExpressionTime')
            summed=node('MaterialExpressionAdd');link(clock,summed,'A');link(phase,summed,'B')
            cycles=node('MaterialExpressionMultiply',const_b=.2);link(summed,cycles,'A')
            sine=node('MaterialExpressionSine',period=1.);link(cycles,sine)
            half=node('MaterialExpressionMultiply',const_b=.5);link(sine,half,'A')
            positive=node('MaterialExpressionAdd',const_b=.5);link(half,positive,'A')
            amplitude=node('MaterialExpressionMultiply',const_b=.4);link(positive,amplitude,'A')
            gain=node('MaterialExpressionAdd',const_b=.75);link(amplitude,gain,'A')
            emission=node('MaterialExpressionMultiply');link(accent,emission,'A','RGB');link(gain,emission,'B')
            prop(emission,'MP_EMISSIVE_COLOR')
        edit.layout_material_expressions(material)
        errors=edit.recompile_material(material)
        require(not errors,'Private marker shader compile errors: '+str(errors))
        require(material.get_editor_property('blend_mode')==u.BlendMode.BLEND_OPAQUE and
                material.get_editor_property('shading_model')==u.MaterialShadingModel.MSM_DEFAULT_LIT and
                not material.get_editor_property('two_sided') and
                edit.get_material_property_input_node(material,u.MaterialProperty.MP_WORLD_POSITION_OFFSET) is None,
                'Marker material classification or displacement differs')
        receipts.append({'role':role,'asset':path(material),'declared_nodes':nodes,'compile_errors':list(errors or [])})
    children=[]
    for index,row in enumerate(value['placements']):
        name='MI_Accent_%02d'%index
        child=tools.create_asset(name,PRIVATE,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        require(child,'Private marker accent creation failed');assets.append(child)
        edit.set_material_instance_parent(child,role_materials['SLOW_ACCENT_LENS'])
        edit.set_material_instance_vector_parameter_value(child,'Accent',u.LinearColor(*row['accent']['linear'],1.))
        edit.set_material_instance_scalar_parameter_value(child,'PhaseSeconds',float(row['phase_seconds']))
        edit.update_material_instance(child)
        color=edit.get_material_instance_vector_parameter_value(child,'Accent')
        actual=[float(getattr(color,k)) for k in ('r','g','b','a')]
        # Native MIC vectors store float32; compare against the exact same native conversion.
        expected=u.LinearColor(*row['accent']['linear'],1.)
        require(actual==[float(getattr(expected,k)) for k in ('r','g','b','a')] and
                float(edit.get_material_instance_scalar_parameter_value(child,'PhaseSeconds'))==row['phase_seconds'] and
                child.get_editor_property('parent')==role_materials['SLOW_ACCENT_LENS'], 'Accent parameter readback differs')
        children.append(child);receipts.append({'service':row['service'],'asset':path(child),'accent_rgba':actual,
            'phase_seconds':row['phase_seconds'],'pulse_period_seconds':5.,'gain_range':[.75,1.15]})
    return role_materials,children,assets,receipts


def _mesh(u,materials):
    data=geometry();dynamic=u.DynamicMesh()
    enable,_=resolve(u.GeometryScript_Materials,'EnableMaterialIDs');enable(dynamic)
    append,_=resolve(u.GeometryScript_MeshEdits,'AppendBuffersToMesh')
    ordered=[];sample_triangles=[]
    for role in (0,1,2):
        source=[(triangle,mid) for triangle,mid in zip(data['triangles'],data['material_ids']) if mid==role]
        indices=sorted({i for triangle,_ in source for i in triangle});remap={index:n for n,index in enumerate(indices)}
        buffers=_buffers(u,[data['positions'][i] for i in indices],[data['normals'][i] for i in indices],
            [data['uvs'][i] for i in indices],[[remap[i] for i in triangle] for triangle,_ in source])
        appended=append(dynamic,buffers,material_id=role)
        require(isinstance(appended,tuple) and len(appended)==2 and appended[0]==dynamic,
                'Native three-role buffer append tuple differs')
        triangle_ids=list(u.GeometryScript_List.convert_index_list_to_array(appended[1]))
        require(len(triangle_ids)==len(source),'Native role triangle population differs')
        ordered.extend(source)
        for index in (0,len(source)//2,len(source)-1):
            sample_triangles.append((triangle_ids[index],source[index][0]))
    ids=_bulk_ids(dynamic,u)
    require(dynamic.get_triangle_count()==2980 and dict(Counter(ids))=={0:1248,1:1252,2:480},
            'Native marker geometry/material role counts differ')
    sample_reads=[]
    for triangle,source_triangle in sample_triangles:
        actual=_attributes(dynamic,triangle,u)
        expected={'uvs':[data['uvs'][i] for i in source_triangle],
                  'normals':[data['normals'][i] for i in source_triangle]}
        require(all(math.dist(actual[key][i],expected[key][i])<3.e-6 for key in expected for i in range(3)),
                'Native generated marker UV/split normal differs')
        sample_reads.append({'triangle':triangle,'actual':actual})
    mesh,outcome=u.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic,PRIVATE+'/SM_ServiceMarker',
        u.GeometryScriptCreateNewStaticMeshAssetOptions(enable_nanite=False,enable_collision=False,
            enable_recompute_normals=False,enable_recompute_tangents=False,use_original_vertex_order=True))
    require(mesh and outcome==u.GeometryScriptOutcomePins.SUCCESS,'Private physical marker mesh creation failed')
    require(len(mesh.get_editor_property('static_materials'))==3 and mesh.get_num_sections(0)==3,
            'Native static marker must have exactly three material-ID sections')
    slots=[]
    for role,material in zip(data['material_roles'],materials):
        slots.append(u.StaticMaterial(material_interface=material,material_slot_name=role))
    mesh.set_editor_property('static_materials',slots)
    require([path(s.get_editor_property('material_interface')) for s in mesh.get_editor_property('static_materials')]==
            [path(m) for m in materials], 'Explicit static marker material-slot readback failed')
    native=u.DynamicMesh()
    copied_mesh=u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(mesh,native,
        u.GeometryScriptCopyMeshFromAssetOptions(apply_build_settings=False),
        u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.SOURCE_MODEL,lod_index=0),
        use_section_materials=False)
    require(isinstance(copied_mesh,tuple) and len(copied_mesh)==2 and copied_mesh[0]==native and
            copied_mesh[1]==u.GeometryScriptOutcomePins.SUCCESS,'Exact static marker source-model copy differs')
    _,vertices,gaps=u.GeometryScript_MeshQueries.get_all_vertex_positions(native,False)
    _,triangles,triangle_gaps=u.GeometryScript_MeshQueries.get_all_triangle_indices(native,False)
    require(not gaps and not triangle_gaps,'Unexpected sparse created marker mesh IDs')
    copied={'vertices':[list(v.to_tuple()) for v in u.GeometryScript_List.convert_vector_list_to_array(vertices)],
            'triangles':[[int(t.x),int(t.y),int(t.z)] for t in u.GeometryScript_List.convert_triangle_list_to_array(triangles)]}
    copied_ids=_bulk_ids(native,u)
    require(len(copied['triangles'])==2980 and dict(Counter(copied_ids))==dict(Counter(ids)),
            'Actual static mesh topology/material IDs differ')
    def physical_faces(vertices,triangles,material_ids):
        return Counter((mid,tuple(sorted(tuple(round(v,4) for v in vertices[i]) for i in triangle)))
                       for triangle,mid in zip(triangles,material_ids))
    require(physical_faces(copied['vertices'],copied['triangles'],copied_ids)==
            physical_faces(data['positions'],data['triangles'],data['material_ids']),
            'Actual static marker face geometry differs at0.0001cm quantization')
    bounds=mesh.get_bounds();minimum=[bounds.origin.to_tuple()[i]-bounds.box_extent.to_tuple()[i] for i in range(3)]
    maximum=[bounds.origin.to_tuple()[i]+bounds.box_extent.to_tuple()[i] for i in range(3)]
    require(math.dist(minimum,data['bounds_cm'][0])<.0001 and math.dist(maximum,data['bounds_cm'][1])<.0001,
            'Actual marker bounds differ from approved radii/height')
    return mesh,{'asset':path(mesh),'triangles':2980,'native_material_counts':dict(Counter(copied_ids)),
        'bounds_cm':[minimum,maximum],'native_attribute_samples':sample_reads,
        'all_face_geometry_verified_quantization_cm':.0001,'no_collision_requested':True,
        'materials':[path(m) for m in materials]}


def apply(ctx,expected_map_sha256,progress=None):
    import unreal as u
    from AuthorStationWhiteFloorsRemainder4 import state as actor_state
    value=plan();world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    map_file=ROOT/('Content/'+MAP[6:]+'.umap')
    require(world.get_path_name().split('.')[0]==MAP and sha(map_file)==expected_map_sha256,
            'Require exact successful saved preview')
    actors=list(ctx.eas.get_all_level_actors())
    require(not any(a.get_actor_label().startswith(PREFIX) for a in actors),'Preserve previous physical service markers')
    before={path(a):actor_state(a,u) for a in actors};services=service_records(actors,u,value)
    support=support_records(world,u,value)
    if progress:progress('FOOTPRINT_AND_SERVICE_PREFLIGHT_COMPLETE',{'contacts':65,'services':5})
    materials,children,dirty,material_receipts=_materials(value,u)
    mesh,mesh_receipt=_mesh(u,[materials[key] for key in geometry()['material_roles']]);dirty.append(mesh)
    placements=[]
    for index,row in enumerate(value['placements']):
        actor=ctx.raw(PREFIX+row['service'],mesh,row['centre_cm'],rot=(0.,row['yaw_degrees'],0.),collision=False)
        component=actor.static_mesh_component
        component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        component.set_editor_property('generate_overlap_events',False)
        component.set_simulate_physics(False)
        component.set_material(0,materials['GRAPHITE_SATIN_FRAME']);component.set_material(1,children[index])
        component.set_material(2,materials['TITANIUM_FASTENERS'])
        require(not actor.get_actor_enable_collision() and component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION and
                not component.get_editor_property('generate_overlap_events') and not component.is_simulating_physics() and
                component.get_material(1)==children[index],'Exact cosmetic marker collision/material readback failed')
        placements.append({'service':row['service'],'actor':path(actor),'label':actor.get_actor_label(),
            'centre_cm':list(actor.get_actor_location().to_tuple()),'yaw_degrees':float(actor.get_actor_rotation().yaw),
            'materials':[path(m) for m in component.get_materials()],'no_collision':True,'overlaps':False})
    after={path(a):actor_state(a,u) for a in ctx.eas.get_all_level_actors()}
    created={row['actor'] for row in placements}
    require(set(after)-set(before)==created and len(created)==5 and
            {k:v for k,v in after.items() if k not in created}==before and
            service_records(list(ctx.eas.get_all_level_actors()),u,value)==services and
            support_records(world,u,value)==support and len(dirty)==9,
            'Only five cosmetic markers may change the complete saved scene')
    return {'success':True,'dirty_assets':dirty,'new_actor_count':5,'new_light_count':0,
            'private_asset_count':9,'material_slot_allowlist':[],'existing_actor_modifications':0,
            'plan_sha256':PLAN_SHA,'geometry_sha256':GEOMETRY_SHA,'services5_sha256':SERVICES_SHA,
            'mesh':mesh_receipt,'materials':material_receipts,'placements':placements,
            'services_before':services,'services_after':services,'footprints_before':support,'footprints_after':support,
            'scene_preservation_pass':True,'visual_acceptance':False,'owner_acceptance':False,
            'limits':['Same-loaded exact scene equality except five new cosmetic actors; no gameplay action called.',
                      'Natural pulse, actual native Focus and full-size appearance still require fresh saved capture.']}
