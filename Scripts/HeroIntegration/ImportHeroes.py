"""Import only the supplied heroes into a new private family. Default is read-only planning.

Run ExportSourceManifest.py in Blender first, then invoke Unreal with -SSApplyPlayableHeroes.
This script never runs AuthorContent or saves an existing station/map/vendor asset.
"""
import hashlib,json,re
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.agent/local/HeroIntegration_20261020'
PLAN=json.loads((OUT/'SourceManifest.json').read_text());BASE='/Game/SpaceSurvival/Licensed/PlayableHeroes_20261020'
L=u.EditorAssetLibrary;E=u.MaterialEditingLibrary;T=u.AssetToolsHelpers.get_asset_tools()
APPLY='SSApplyPlayableHeroes' in u.SystemLibrary.get_command_line()
report={'apply':APPLY,'heroes':{},'warnings':[],'source_sha256_verified':True}
def log(*x):print('HEROIMPORT|',*x,flush=True)
def persist():(OUT/'ImportReceipt.json').write_text(json.dumps(report,indent=2))
def safe(s):return re.sub('[^A-Za-z0-9_]','_',s)
for h in PLAN['heroes']:
    assert hashlib.sha256(Path(h['fbx']).read_bytes()).hexdigest()==h['fbx_sha256']
    assert hashlib.sha256(Path(h['source_blend']).read_bytes()).hexdigest()==h['blend_sha256']
    for record in h['images'].values():assert hashlib.sha256(Path(record['file']).read_bytes()).hexdigest()==record['sha256']
if not APPLY:
    report['plan']=[{'hero':h['key'],'fbx':h['fbx'],'materials':len(h['materials']),'textures':len(h['images'])} for h in PLAN['heroes']];persist();log('DRY_RUN',report['plan'])
else:
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 1')
    for h in PLAN['heroes']:
        key=h['key'];folder=BASE+'/'+key;assetpath=folder+'/SK_'+key
        existing=L.load_asset(assetpath) if L.does_asset_exist(assetpath) else None
        if existing and not existing.skeleton:
            # The deprecated FBX factory produced a mesh without any skeleton in 5.8.
            # Preserve that failed, newly created asset before replacing only our private copy.
            import shutil
            rejected=Path('D:/SpaceSurvival_AssetArchive/HeroUnreal_20261020/RejectedLegacy');rejected.mkdir(parents=True,exist_ok=True)
            disk=ROOT/'Content'/Path(assetpath.removeprefix('/Game/')).with_suffix('.uasset')
            shutil.copy2(disk,rejected/(key+'_'+hashlib.sha256(disk.read_bytes()).hexdigest()[:16]+'.uasset'))
            assert L.delete_asset(assetpath);existing=None;u.SystemLibrary.collect_garbage()
        if not existing:
            p=u.new_object(u.InterchangeGenericAssetsPipeline,name='Playable'+key+'Pipeline')
            for prop,v in {'asset_name':'SK_'+key,'use_source_name_for_asset':False,'asset_type_sub_folders':False,'scene_name_sub_folder':False}.items():p.set_editor_property(prop,v)
            c=p.get_editor_property('common_skeletal_meshes_and_animations_properties');c.set_editor_property('import_only_animations',False);c.set_editor_property('try_auto_select_skeleton',False)
            m=p.get_editor_property('mesh_pipeline')
            for prop,v in {'import_static_meshes':False,'import_skeletal_meshes':True,'create_physics_asset':True,'update_skeleton_reference_pose':False}.items():m.set_editor_property(prop,v)
            m.set_editor_property('combine_skeletal_meshes_behavior',u.InterchangeCombineSkeletalMeshesBehavior.BY_SKELETON)
            p.get_editor_property('animation_pipeline').set_editor_property('import_animations',False)
            p.get_editor_property('material_pipeline').set_editor_property('import_materials',False);p.get_editor_property('material_pipeline').get_editor_property('texture_pipeline').set_editor_property('import_textures',False)
            params=u.ImportAssetParameters();params.set_editor_property('is_automated',True);params.set_editor_property('replace_existing',True);params.set_editor_property('override_pipelines',[u.SoftObjectPath(p.get_path_name())])
            manager=u.InterchangeManager.get_interchange_manager_scripted();objects=manager.import_asset(folder,manager.create_source_data(h['fbx']),params)
            meshes=[o for o in objects if isinstance(o,u.SkeletalMesh)];assert len(meshes)==1,[(o.get_name(),o.get_class().get_name()) for o in objects]
            imported=meshes[0]
            if imported.get_path_name().split('.')[0]!=assetpath:assert L.rename_asset(imported.get_path_name(),assetpath)
            for obj in objects:assert L.save_loaded_asset(obj,False)
        mesh=L.load_asset(assetpath);assert isinstance(mesh,u.SkeletalMesh),assetpath
        bounds=mesh.get_imported_bounds();height=2*bounds.box_extent.z;assert abs(height-185)<.5,(key,height)
        textures={}
        for digest,im in h['images'].items():
            name='T_'+digest[:18];path=folder+'/Textures/'+name
            if not L.does_asset_exist(path):
                task=u.AssetImportTask()
                for prop,v in {'filename':im['file'],'destination_path':folder+'/Textures','destination_name':name,'automated':True,'replace_existing':False,'save':True}.items():task.set_editor_property(prop,v)
                T.import_asset_tasks([task])
            tex=L.load_asset(path);assert tex,path
            normal='normal' in im['name'].lower();color=im['color_space']=='sRGB' and not normal
            tex.set_editor_property('srgb',color)
            tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP if normal else u.TextureCompressionSettings.TC_DEFAULT if color else u.TextureCompressionSettings.TC_MASKS)
            if normal:tex.set_editor_property('flip_green_channel',True)
            tex.set_editor_property('max_texture_size',max(im['size']));L.save_loaded_asset(tex,False)
            textures[digest]=(tex,normal,color)
        mats={}
        for desc in h['materials']:
            name='M_'+safe(desc['name']);path=folder+'/Materials/'+name
            mat=L.load_asset(path) or T.create_asset(name,folder+'/Materials',u.Material,u.MaterialFactoryNew());assert mat,path
            E.delete_all_material_expressions(mat)
            nodes={n['name']:n for n in desc['nodes']};links={(l['to'],l['input']):l for l in desc['links']};cache={}
            def make(cls,**props):
                node=E.create_material_expression(mat,getattr(u,cls))
                for p,v in props.items():node.set_editor_property(p,v)
                return node
            def connect(a,b,p):assert E.connect_material_expressions(a[0],a[1],b,p),(desc['name'],p)
            def constant(v):
                if isinstance(v,list):return make('MaterialExpressionConstant3Vector',constant=u.LinearColor(*v[:3],1)),''
                return make('MaterialExpressionConstant',r=float(v or 0)),''
            def input_of(node,identifier):
                link=links.get((node['name'],identifier))
                if link:return output_of(link['from'],link['output'])
                value=next(p['value'] for p in node['inputs'] if p['id']==identifier);return constant(value)
            def binary(cls,a,b):
                n=make(cls);connect(a,n,'A');connect(b,n,'B');return n,''
            def texture(digest):
                tex,normal,color=textures[digest];n=make('MaterialExpressionTextureSample',texture=tex)
                n.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL if normal else u.MaterialSamplerType.SAMPLERTYPE_COLOR if color else u.MaterialSamplerType.SAMPLERTYPE_MASKS)
                return n
            def output_of(name,output):
                ck=(name,output)
                if ck in cache:return cache[ck]
                n=nodes[name];kind=n['type']
                if kind=='ShaderNodeTexImage':result=(texture(n['image']),'A' if output=='Alpha' else 'RGB')
                elif kind=='ShaderNodeSeparateColor':
                    mask=make('MaterialExpressionComponentMask',r=output=='Red',g=output=='Green',b=output=='Blue',a=False);connect(input_of(n,'Color'),mask,'');result=(mask,'')
                elif kind=='ShaderNodeNormalMap':
                    raw=input_of(n,'Color');strength=next(p['value'] for p in n['inputs'] if p['id']=='Strength')
                    if abs(strength-1)<.001:result=raw
                    else:
                        mix=make('MaterialExpressionLinearInterpolate');connect(constant([0,0,1]),mix,'A');connect(raw,mix,'B');connect(constant(strength),mix,'Alpha');norm=make('MaterialExpressionNormalize');connect((mix,''),norm,'');result=(norm,'')
                elif kind=='ShaderNodeMix':
                    assert n['blend_type']=='MULTIPLY' and n['data_type']=='RGBA',n
                    a=input_of(n,'A_Color');multiply=binary('MaterialExpressionMultiply',a,input_of(n,'B_Color'))
                    mix=make('MaterialExpressionLinearInterpolate');connect(a,mix,'A');connect(multiply,mix,'B');connect(input_of(n,'Factor_Float'),mix,'Alpha');result=(mix,'')
                else:raise AssertionError((desc['name'],name,kind,output))
                cache[ck]=result;return result
            shader=next(n for n in desc['nodes'] if n['type']=='ShaderNodeBsdfPrincipled');values={p['id']:p['value'] for p in shader['inputs']}
            for socket,prop in [('Base Color',u.MaterialProperty.MP_BASE_COLOR),('Metallic',u.MaterialProperty.MP_METALLIC),('Roughness',u.MaterialProperty.MP_ROUGHNESS),('Specular IOR Level',u.MaterialProperty.MP_SPECULAR)]:
                expr=input_of(shader,socket);assert E.connect_material_property(expr[0],expr[1],prop)
            if 'portable_normal' in desc:normal=(texture(desc['portable_normal']),'RGB');assert E.connect_material_property(normal[0],normal[1],u.MaterialProperty.MP_NORMAL)
            elif (shader['name'],'Normal') in links:
                normal=input_of(shader,'Normal');assert E.connect_material_property(normal[0],normal[1],u.MaterialProperty.MP_NORMAL)
            emission=binary('MaterialExpressionMultiply',input_of(shader,'Emission Color'),input_of(shader,'Emission Strength'));E.connect_material_property(emission[0],emission[1],u.MaterialProperty.MP_EMISSIVE_COLOR)
            if values.get('Coat Weight',0)>.001:
                mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_CLEAR_COAT)
                assert u.SSPlayableHeroTools.configure_coating(mat,values['Coat Weight'],values['Coat Roughness'])
            if desc['name'].startswith('Cloth_') and desc['name']!='Cloth_Armor':mat.set_editor_property('two_sided',True)
            E.set_base_material_usage(mat,u.MaterialUsage.MATUSAGE_SKELETAL_MESH,True);E.recompile_material(mat);assert L.save_loaded_asset(mat,False)
            mats[''.join(c for c in desc['name'].lower() if c.isalnum())]=mat
        slots=list(mesh.materials);unmatched=[]
        for i,slot in enumerate(slots):
            label=str(slot.material_slot_name);lookup=''.join(c for c in label.lower() if c.isalnum());material=mats.get(lookup)
            if not material:unmatched.append(label)
            else:slot.material_interface=material;slots[i]=slot
        assert not unmatched,(key,unmatched,list(mats))
        mesh.set_editor_property('materials',slots);assert L.save_loaded_asset(mesh,False)
        ref=u.AnimPoseExtensions.get_reference_pose(mesh.skeleton);bones=list(map(str,u.AnimPoseExtensions.get_bone_names(ref)))
        expected={'EX7':82,'Green':61,'Blue':61,'Cloth':106}[key];assert len(bones)==expected,(key,len(bones));assert all(n in bones for n in ['root','pelvis','head','hand_l','foot_l'])
        report['heroes'][key]={'mesh':mesh.get_path_name(),'height_cm':height,'bones':len(bones),'slots':[{'name':str(s.material_slot_name),'material':s.material_interface.get_path_name()} for s in slots],'textures':len(textures),'source_fbx_sha256':h['fbx_sha256']};persist();log('IMPORTED',key,height,len(bones),len(slots),len(textures))
    u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 1');persist();log('ALL_HEROES_IMPORTED')
