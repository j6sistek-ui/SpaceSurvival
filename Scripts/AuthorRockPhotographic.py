"""CC0 photographic rock material with opt-in approved material-only adoption.

Local triplanar sampling needs no mesh UVs. Existing asteroids use uniform actor
scale: RepeatLocalCm is expressed before that scale so the pattern rotates and
translates with each rock. It is not a fixed world-space texel density promise.
"""
import hashlib,json,sys,re
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'ContentSource/ThirdParty/PolyHaven/RockFace'
BASE='/Game/SpaceSurvival'
MATERIAL=BASE+'/Materials/M_RockPhotographic'
VERSION='RockFaceLocalTriplanar1'
ROCK_MESHES=('SM_AsteroidSmall','SM_AsteroidMedium','SM_AsteroidMassive')
NAMES={'diff':'T_RockFace_Color','arm':'T_RockFace_ARM','nor_dx':'T_RockFace_Normal'}
LIB=u.EditorAssetLibrary
EDIT=u.MaterialEditingLibrary


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def owned(path):return path.stem=='M_RockPhotographic' or path.stem in NAMES.values()


def source_manifest():
    manifest=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['license']=='CC0-1.0' and manifest['asset']=='rock_face'
    assert {r['kind'] for r in manifest['maps']}==set(NAMES)
    for row in manifest['maps']:
        path=SOURCE/row['file'];data=path.read_bytes()
        assert len(data)==row['bytes'] and digest(path)==row['sha256'],str(path)
        assert hashlib.md5(data).hexdigest()==row['official_md5'],'Provider checksum mismatch'
        assert data[:8]==b'\x89PNG\r\n\x1a\n' and int.from_bytes(data[16:20],'big')==2048 and int.from_bytes(data[20:24],'big')==2048
    return manifest


def connect(source,output,target,pin):
    assert EDIT.connect_material_expressions(source,output,target,pin),'Rock graph connection failed: '+pin


def author_material(textures,key):
    material=LIB.load_asset(MATERIAL) if LIB.does_asset_exist(MATERIAL) else None
    if material:
        assert LIB.get_metadata_tag(material,'SSRockVersion')==VERSION,'Candidate requires deliberate reviewed reauthor'
        previous_key=LIB.get_metadata_tag(material,'SSRockSourceKey')
        if previous_key==key:return material
        # Bounded repair of the first unadopted import's loop-variable metadata.
        assert previous_key=='a' and LIB.get_metadata_tag(material,'SSAuthoringVersion')=='1','Unexpected source checksum'
        LIB.set_metadata_tag(material,'SSRockSourceKey',key);assert LIB.save_loaded_asset(material,only_if_is_dirty=False)
        return material
    material=u.AssetToolsHelpers.get_asset_tools().create_asset('M_RockPhotographic',BASE+'/Materials',u.Material,u.MaterialFactoryNew())
    assert material
    material.set_editor_property('blend_mode',u.BlendMode.BLEND_OPAQUE)
    material.set_editor_property('shading_model',u.MaterialShadingModel.MSM_DEFAULT_LIT)
    material.set_editor_property('tangent_space_normal',False)
    material.set_editor_property('used_with_instanced_static_meshes',True)
    def node(cls,x,y):return EDIT.create_material_expression(material,cls,x,y)
    def scalar(name,value,x,y):
        result=node(u.MaterialExpressionScalarParameter,x,y);result.set_editor_property('parameter_name',name);result.set_editor_property('default_value',value);return result
    def custom(description,code,inputs,x,y,size=3):
        result=node(u.MaterialExpressionCustom,x,y);result.set_editor_property('description',description);result.set_editor_property('code',code);result.set_editor_property('output_type',{2:u.CustomMaterialOutputType.CMOT_FLOAT2,3:u.CustomMaterialOutputType.CMOT_FLOAT3}[size])
        entries=[]
        for name in inputs:
            item=u.CustomInput();item.set_editor_property('input_name',name);entries.append(item)
        result.set_editor_property('inputs',entries)
        for name,(expression,output) in inputs.items():connect(expression,output,result,name)
        return result
    # Absolute world position is converted back using the rendered object's
    # current transform. No actor translation or world-origin value enters UVs.
    world=node(u.MaterialExpressionWorldPosition,-1800,0)
    local=node(u.MaterialExpressionTransformPosition,-1600,0)
    local.set_editor_property('transform_source_type',u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD)
    local.set_editor_property('transform_type',u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    connect(world,'',local,'')
    vertex_normal=node(u.MaterialExpressionVertexNormalWS,-1800,250)
    local_normal=node(u.MaterialExpressionTransform,-1600,250)
    local_normal.set_editor_property('transform_source_type',u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD)
    local_normal.set_editor_property('transform_type',u.MaterialVectorCoordTransform.TRANSFORM_LOCAL)
    connect(vertex_normal,'',local_normal,'')
    repeat=scalar('RepeatLocalCm',240,-1800,-220)
    uv=[]
    for axis,swizzle,sign_component in [(0,'yz','x'),(1,'zx','y'),(2,'xy','z')]:
        code=f'float2 q=P.{swizzle}/max(RepeatCm,1.0); q.x*=N.{sign_component}<0?-1.0:1.0; return q;'
        uv.append(custom('Signed local projection '+str(axis),code,{'P':(local,''),'N':(local_normal,''),'RepeatCm':(repeat,'')},-1320,axis*220,2))
    samples={kind:[] for kind in NAMES}
    sampler={'diff':u.MaterialSamplerType.SAMPLERTYPE_COLOR,'arm':u.MaterialSamplerType.SAMPLERTYPE_MASKS,'nor_dx':u.MaterialSamplerType.SAMPLERTYPE_NORMAL}
    for map_index,kind in enumerate(NAMES):
        for axis in range(3):
            sample=node(u.MaterialExpressionTextureSampleParameter2D,-1030+map_index*350,axis*260)
            sample.set_editor_property('parameter_name',NAMES[kind]);sample.set_editor_property('texture',textures[kind]);sample.set_editor_property('sampler_type',sampler[kind]);connect(uv[axis],'',sample,'UVs');samples[kind].append(sample)
    weight_code='float3 w=pow(abs(normalize(N)),4.0); w/=max(w.x+w.y+w.z,0.0001); return X*w.x+Y*w.y+Z*w.z;'
    blends={}
    for index,kind in enumerate(('diff','arm')):
        inputs={'N':(local_normal,''),**{axis:(sample,'RGB') for axis,sample in zip(('X','Y','Z'),samples[kind])}}
        blends[kind]=custom('Blend '+kind,weight_code,inputs,200,index*280)
    # Perturb the original local surface normal by each projected map's slopes.
    # A flat normal map resolves to N exactly, including diagonal blend regions.
    # Signed U axes avoid inverted detail on negative-facing projections.
    normal_code='''float3 n=normalize(N);
float3 w=pow(abs(n),4.0);w/=max(w.x+w.y+w.z,0.0001);
float3 s=float3(n.x<0?-1:1,n.y<0?-1:1,n.z<0?-1:1);
float2 dx=X.xy/max(X.z,0.25)*Strength;
float2 dy=Y.xy/max(Y.z,0.25)*Strength;
float2 dz=Z.xy/max(Z.z,0.25)*Strength;
float3 nx=normalize(n+float3(0,dx.x*s.x,dx.y));
float3 ny=normalize(n+float3(dy.y,0,dy.x*s.y));
float3 nz=normalize(n+float3(dz.x*s.z,dz.y,0));
return normalize(nx*w.x+ny*w.y+nz*w.z);'''
    inputs={'N':(local_normal,''),'Strength':(scalar('NormalStrength',.75,-200,1050),'')}
    inputs.update({axis:(sample,'RGB') for axis,sample in zip(('X','Y','Z'),samples['nor_dx'])})
    normal=custom('Object local triplanar surface normal',normal_code,inputs,200,650)
    world_normal=node(u.MaterialExpressionTransform,530,650)
    world_normal.set_editor_property('transform_source_type',u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL)
    world_normal.set_editor_property('transform_type',u.MaterialVectorCoordTransform.TRANSFORM_WORLD)
    connect(normal,'',world_normal,'')
    tint=node(u.MaterialExpressionVectorParameter,200,-280);tint.set_editor_property('parameter_name','RockTint');tint.set_editor_property('default_value',u.LinearColor(.72,.79,.85,1))
    desaturation=node(u.MaterialExpressionDesaturation,500,0);connect(blends['diff'],'',desaturation,'');connect(scalar('Desaturation',.5,200,-120),'',desaturation,'Fraction')
    color=node(u.MaterialExpressionMultiply,780,0);connect(desaturation,'',color,'A');connect(tint,'',color,'B')
    arm_channels=[]
    for index in range(3):
        channel=node(u.MaterialExpressionComponentMask,500,240+index*140)
        for mask_key,value in [('r',index==0),('g',index==1),('b',index==2),('a',False)]:channel.set_editor_property(mask_key,value)
        connect(blends['arm'],'',channel,'');arm_channels.append(channel)
    rough=node(u.MaterialExpressionMax,780,300);connect(arm_channels[1],'',rough,'A');connect(scalar('RoughnessFloor',.68,500,100),'',rough,'B')
    # ARM metallic is preserved in source; rock is explicitly dielectric.
    metallic=node(u.MaterialExpressionConstant,780,460);metallic.set_editor_property('r',0.0)
    for expression,prop in [(color,u.MaterialProperty.MP_BASE_COLOR),(arm_channels[0],u.MaterialProperty.MP_AMBIENT_OCCLUSION),(rough,u.MaterialProperty.MP_ROUGHNESS),(metallic,u.MaterialProperty.MP_METALLIC),(world_normal,u.MaterialProperty.MP_NORMAL)]:
        assert EDIT.connect_material_property(expression,'',prop),'Rock property connection failed'
    EDIT.recompile_material(material)
    for name,value in {'SSAuthoringVersion':'1','SSRockVersion':VERSION,'SSRockSourceKey':key,'SSAssetLicense':'CC0-1.0','SSAssetSource':'https://polyhaven.com/a/rock_face','SSRockMapping':'SignedObjectLocalTriplanarNoUVs','SSRockTextureReads':'9','SSRockGeometryChanges':'None'}.items():LIB.set_metadata_tag(material,name,value)
    assert LIB.save_loaded_asset(material,only_if_is_dirty=False)
    return material



def mesh_signature(mesh,phase):
    """Export built LOD0 arrays read-only, independent of material assignment."""
    editor=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    assert editor.get_lod_count(mesh)==1 and editor.get_num_uv_channels(mesh,0)>0,'Unsupported LOD/UV layout for preservation audit'
    directory=ROOT/'.agent/local/RockAdoption';directory.mkdir(parents=True,exist_ok=True)
    path=directory/(mesh.get_name()+'_'+phase+'.fbx');task=u.AssetExportTask();options=u.FbxExportOption()
    for name,value in {'ascii':True,'level_of_detail':False,'collision':False,'export_source_mesh':False,'vertex_color':True}.items():options.set_editor_property(name,value)
    for name,value in {'object':mesh,'filename':str(path),'automated':True,'prompt':False,'replace_identical':True,'exporter':u.StaticMeshExporterFBX(),'options':options}.items():task.set_editor_property(name,value)
    assert u.Exporter.run_asset_export_task(task) and path.is_file(),'Built geometry FBX export failed'
    text=path.read_text(encoding='utf-8-sig');arrays={}
    for name,count,values in re.findall(r'\b(Vertices|PolygonVertexIndex|Normals|NormalsIndex|Tangents|TangentsIndex|Binormals|BinormalsIndex|UV|UVIndex|Colors|ColorIndex)\s*:\s*\*(\d+)\s*\{\s*a:\s*([^}]*)\}',text,re.S):
        numbers=values.replace('\n','').replace('\r','').replace('\t','').replace(' ','').strip(',').split(',')
        assert len(numbers)==int(count),'Malformed exported array '+name
        arrays.setdefault(name,[]).append(numbers)
    assert all(name in arrays for name in ('Vertices','PolygonVertexIndex','Normals','UV')),'FBX missing built geometry attributes'
    geometry=json.dumps(arrays,sort_keys=True,separators=(',',':'))
    body=mesh.get_editor_property('body_setup');instance=body.get_editor_property('default_instance');bounds=mesh.get_bounds()
    return {'render_lod0_geometry_sha256':hashlib.sha256(geometry.encode()).hexdigest(),'triangles':mesh.get_num_triangles(0),'vertices':editor.get_number_verts(mesh,0),'lods':editor.get_lod_count(mesh),'uv_channels':editor.get_num_uv_channels(mesh,0),'sections':mesh.get_num_sections(0),'bounds_origin_cm':[bounds.origin.x,bounds.origin.y,bounds.origin.z],'bounds_extent_cm':[bounds.box_extent.x,bounds.box_extent.y,bounds.box_extent.z],'simple_collision_count':editor.get_simple_collision_count(mesh),'section_collision':[editor.is_section_collision_enabled(mesh,0,i) for i in range(mesh.get_num_sections(0))],'collision_trace':str(body.get_editor_property('collision_trace_flag')),'collision_enabled':str(instance.get_editor_property('collision_enabled')),'collision_profile':str(instance.get_editor_property('collision_profile_name'))}


def adopt(material):
    source=json.loads((ROOT/'ContentSource/RockPhotographicPreview/AdoptionSource.json').read_text())
    assert set(source['meshes'])==set(ROCK_MESHES)
    baseline_path=ROOT/'ContentSource/RockPhotographicPreview/AdoptionBaseline.json';before={};meshes={}
    for name in ROCK_MESHES:
        assert digest(ROOT/'ContentSource/Meshes'/(name+'.obj'))==source['meshes'][name]['obj_sha256'],'Authored asteroid source changed; deliberate review required'
        mesh=LIB.load_asset(BASE+'/Meshes/'+name);assert isinstance(mesh,u.StaticMesh)
        slots=list(mesh.get_editor_property('static_materials'));assert len(slots)==1,'Unexpected material section layout'
        assert slots[0].get_editor_property('material_interface').get_path_name().split('.')[0] in (BASE+'/Materials/M_Rock',MATERIAL),'Unexpected original material'
        before[name]=mesh_signature(mesh,'before');meshes[name]=mesh
    if baseline_path.exists():
        baseline=json.loads(baseline_path.read_text());assert baseline['geometry']==before,'Built asteroid geometry/collision differs from approved baseline'
    else:
        baseline={'status':'PRE_ADOPTION_BUILT_GEOMETRY_BASELINE','geometry':before,'source':source}
        baseline_path.write_text(json.dumps(baseline,indent=2)+'\n',encoding='utf-8')
    rows=[]
    for name,mesh in meshes.items():
        if mesh.get_editor_property('static_materials')[0].get_editor_property('material_interface')!=material or LIB.get_metadata_tag(mesh,'SSRockSurfaceVersion')!=VERSION:
            mesh.set_material(0,material);LIB.set_metadata_tag(mesh,'SSRockSurfaceVersion',VERSION);LIB.set_metadata_tag(mesh,'SSRockGeometryPreservedSHA256',before[name]['render_lod0_geometry_sha256']);assert LIB.save_loaded_asset(mesh,only_if_is_dirty=False)
        after=mesh_signature(mesh,'after');assert before[name]==after,'Material adoption changed geometry/collision'
        rows.append({'mesh':mesh.get_path_name(),'geometry_before_equals_after':True,'geometry':after,'package_sha256':digest(ROOT/'Content/SpaceSurvival/Meshes'/(name+'.uasset'))})
    receipt={'status':'THREE_ASTEROID_MATERIALS_ADOPTED_GEOMETRY_COLLISION_PRESERVED','errors':[],'material':MATERIAL,'rows':rows,'runtime_residency':'Lead-owned scoped residency; no NeverStream asset change','telegraphs_or_gameplay_changed':False}
    (ROOT/'Saved/Validation/RockPhotographicAdoption.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return receipt

def main(adopt_existing_meshes=False):
    record={'status':'FAILED','errors':[],'engine':u.SystemLibrary.get_engine_version()}
    protected={p:digest(p) for p in (ROOT/'Content').rglob('*.uasset') if not owned(p) and not (adopt_existing_meshes and p.stem in ROCK_MESHES)}
    try:
        manifest=source_manifest();tools=u.AssetToolsHelpers.get_asset_tools();textures={};LIB.make_directory(BASE+'/Textures')
        for row in manifest['maps']:
            kind=row['kind'];path=BASE+'/Textures/'+NAMES[kind];texture=LIB.load_asset(path) if LIB.does_asset_exist(path) else None
            if not texture:
                task=u.AssetImportTask()
                for k,v in {'filename':str(SOURCE/row['file']),'destination_path':BASE+'/Textures','destination_name':NAMES[kind],'automated':True,'replace_existing':False,'save':False}.items():task.set_editor_property(k,v)
                tools.import_asset_tasks([task]);texture=LIB.load_asset(path);assert isinstance(texture,u.Texture2D)
                texture.set_editor_property('srgb',kind=='diff');texture.set_editor_property('compression_settings',{'diff':u.TextureCompressionSettings.TC_BC7,'arm':u.TextureCompressionSettings.TC_MASKS,'nor_dx':u.TextureCompressionSettings.TC_NORMALMAP}[kind]);texture.set_editor_property('lod_group',u.TextureGroup.TEXTUREGROUP_WORLD_NORMAL_MAP if kind=='nor_dx' else u.TextureGroup.TEXTUREGROUP_WORLD)
                texture.set_editor_property('address_x',u.TextureAddress.TA_WRAP);texture.set_editor_property('address_y',u.TextureAddress.TA_WRAP);texture.set_editor_property('flip_green_channel',False)
                LIB.set_metadata_tag(texture,'SSAuthoringVersion','1');LIB.set_metadata_tag(texture,'SSRockSourceSHA256',row['sha256']);assert LIB.save_loaded_asset(texture,only_if_is_dirty=False)
            assert LIB.get_metadata_tag(texture,'SSRockSourceSHA256')==row['sha256'];textures[kind]=texture
        key=hashlib.sha256(''.join(row['sha256'] for row in manifest['maps']).encode()).hexdigest();material=author_material(textures,key)
        adoption=adopt(material) if adopt_existing_meshes else None
        assert all(digest(p)==h for p,h in protected.items()),'Existing content package changed'
        record.update(status='ISOLATED_ROCK_MATERIAL_IMPORTED_FRESH_VALIDATION_PENDING',material=material.get_path_name(),source_key=key,protected_content_packages_unchanged=len(protected),new_content_assets=4,geometry_or_assignment_changes=bool(adoption),adoption=adoption,limits=['Object-local repeat scales with the rock actor','Nine texture samples; actual gameplay cost not profiled','No displacement, geometry or collision change','Source alpha/ARM metallic unused; rock is dielectric'])
    except Exception as error:record['errors'].append(str(error));u.log_error('ROCK_AUTHOR_FAILED: '+str(error))
    out=ROOT/'Saved/Validation/RockPhotographicImport.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    if record['errors']:raise RuntimeError('Rock candidate authoring failed')
    u.log('ROCK_PHOTOGRAPHIC_AUTHORED')
    return record


if __name__=='__main__':main('--adopt' in sys.argv)