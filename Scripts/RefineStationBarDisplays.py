"""Image-led bar graphics and supported glass menus; lead owns native saves.

Original local Qwen illustrations and independently reviewed typography are
hash-bound. Only five obsolete TextRender labels retire. Existing layout,
character animation, materials and lighting are protected. Decorative only.
"""
import hashlib
import json
import math
import re
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from RefineStationBarPresentation import _one, _path, _require
from RefineStationLoungeCeiling import _snapshot
from StationRefinementSupport import transform_record

MAP='/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
BASE='/Game/OutpostSandbox/StationRefinement/BarDisplays20261006'
PREFIX='Refine/BarDisplays/'
SOURCE=Path(__file__).resolve().parents[1]/'.agent/local/StationRefinement/BarDisplays1'
ART_SHA='db4c74c112670f0da65532d0f8c35727b7212e7de76e28a61779d7ad8f4f1446'
TV='/Game/CyberpunkRestaurant/Meshes/SM_TV_Screen_02'
TABLET='/Game/Cyberpunk_Room/Mesh/SM_Tablet'
GRAPHITE='/Game/OutpostSandbox/Materials/M_OutpostGraphite'
GLASS_LENS='/Game/OutpostSandbox/StationRefinement/BarPresentation20261006/M_BarCoolDiffuser'
PLANE='/Engine/BasicShapes/Plane'
TOP=107.55418
RECESSED_DOCK_TOP=92.24733
# Exact native four-vertex screen basis, fitted to the owner-provided source.
SCREEN_CENTER=(15.4304671288,56.0843825340,-10.7984161377)
SCREEN_RIGHT=(.67750667714,-.73551149966,.00274523214)
SCREEN_UP=(-.00412942915,-.00007138854,.99999147132)
SCREEN_SIZE=(86.2190632285,48.3440479405)

def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def inspect_sources():
    manifest=SOURCE/'final/manifest.json'
    _require(_sha(manifest)==ART_SHA,'Reviewed final bar art manifest changed')
    data=json.loads(manifest.read_text())
    assets={row['name']:row for row in data['assets']}
    for row in assets.values():
        p=Path(row['file']).resolve()
        _require(p.is_relative_to((SOURCE/'final').resolve()) and _sha(p)==row['sha256'],
                 'Final illustration/layout file changed: '+str(p))
    for p,digest in data['sources'].items():
        _require(_sha(p)==digest,'Original local illustration changed')
    return data,assets

def _texture(name,art,u,dirty):
    path=BASE+'/Textures/T_'+name
    _require(not u.EditorAssetLibrary.does_asset_exist(path),'Preserve prior display texture '+path)
    task=u.AssetImportTask()
    for key,value in {'filename':art[name]['file'],'destination_path':BASE+'/Textures',
            'destination_name':'T_'+name,'automated':True,'replace_existing':False,'save':False}.items():
        task.set_editor_property(key,value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex=u.load_asset(path)
    _require(isinstance(tex,u.Texture2D),'Display texture import failed '+name)
    tex.set_editor_property('srgb',True)
    tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_BC7)
    tex.set_editor_property('lod_group',u.TextureGroup.TEXTUREGROUP_WORLD)
    tex.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    tex.set_editor_property('address_x',u.TextureAddress.TA_CLAMP)
    tex.set_editor_property('address_y',u.TextureAddress.TA_CLAMP)
    dirty.append(tex.get_path_name())
    return tex

def _display_material(name,texture,u,dirty,*,tv=False,phase=0.,glass=False):
    """Object-local projection preserves readable art when the owner moves a prop.

    TV source UVs use a shared atlas; projection on its verified actual screen
    quad avoids modifying those UVs or remapping the other seven native slots.
    Twelve-second ad changes use ordinary material Time, no new actor Tick.
    """
    path=BASE+'/Materials/M_'+name
    _require(not u.EditorAssetLibrary.does_asset_exist(path),'Preserve prior display material '+path)
    edit=u.MaterialEditingLibrary
    mat=u.AssetToolsHelpers.get_asset_tools().create_asset('M_'+name,BASE+'/Materials',u.Material,u.MaterialFactoryNew())
    _require(mat,'Cannot create bounded display material')
    mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('two_sided',True)
    mat.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT if glass else u.BlendMode.BLEND_OPAQUE)
    def node(kind,**props):
        out=edit.create_material_expression(mat,getattr(u,kind))
        _require(out is not None,'Missing native expression '+kind)
        for k,v in props.items():out.set_editor_property(k,v)
        return out
    pos=node('MaterialExpressionWorldPosition')
    local=node('MaterialExpressionTransformPosition',
        transform_source_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,
        transform_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    _require(edit.connect_material_expressions(pos,'',local,''),'Cannot derive local display coordinates')
    tex=node('MaterialExpressionTextureObjectParameter',parameter_name='Artwork',texture=texture,
             sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR)
    time=node('MaterialExpressionTime')
    center=SCREEN_CENTER if tv else (0.,0.,0.)
    right=SCREEN_RIGHT if tv else (1.,0.,0.)
    # UE positive Roll takes local +Y downward: negative Y is the pane's up.
    up=SCREEN_UP if tv else (0.,-1.,0.)
    size=SCREEN_SIZE if tv else (100.,100.)
    vec=lambda v:'float3('+','.join('%.11f'%x for x in v)+')'
    code='float3 p=P-'+vec(center)+';\n'
    code+='float2 uv=float2(dot(p,'+vec(right)+')/%.11f+0.5,0.5-dot(p,'%size[0]+vec(up)+')/%.11f);\n'%size[1]
    code+='uv=clamp(uv,0.0015,0.9985);\n'
    if tv:
        code+='float frame=fmod(floor((T+%.3f)/12.0),4.0);\n'%phase
        code+='uv=(uv+float2(fmod(frame,2.0),floor(frame/2.0)))*0.5;\n'
    code+='float3 c=Texture2DSample(Artwork,ArtworkSampler,uv).rgb;\n'
    if glass:
        code+='float a=0.16+0.78*smoothstep(0.01,0.16,max(c.r,max(c.g,c.b)));\n'
        code+='float scan=0.982+0.018*sin((uv.y*180.0-T*0.14)*6.2831853);\n'
        code+='return float4((c+float3(0.002,0.009,0.013))*scan*0.9,a);'
    else:code+='return float4(c*0.82,1.0);'
    custom=node('MaterialExpressionCustom',code=code,description='Original local ad art / object-local fit / decorative only',
                output_type=u.CustomMaterialOutputType.CMOT_FLOAT4)
    inputs=[]
    for name in ('P','Artwork','T'):
        pin=u.CustomInput();pin.set_editor_property('input_name',name);inputs.append(pin)
    custom.set_editor_property('inputs',inputs)
    for source,key in ((local,'P'),(tex,'Artwork'),(time,'T')):
        _require(edit.connect_material_expressions(source,'',custom,key),'Display input failed '+key)
    rgb=node('MaterialExpressionComponentMask',r=True,g=True,b=True,a=False)
    _require(edit.connect_material_expressions(custom,'',rgb,'') and
             edit.connect_material_property(rgb,'',u.MaterialProperty.MP_EMISSIVE_COLOR),'Display color output failed')
    if glass:
        alpha=node('MaterialExpressionComponentMask',r=False,g=False,b=False,a=True)
        _require(edit.connect_material_expressions(custom,'',alpha,'') and
                 edit.connect_material_property(alpha,'',u.MaterialProperty.MP_OPACITY),'Glass opacity output failed')
    edit.layout_material_expressions(mat)
    errors=edit.recompile_material(mat)
    _require(not errors,'Native display material compile failed: '+str(errors))
    dirty.append(mat.get_path_name())
    return mat,{'asset':mat.get_path_name(),'local_projection':True,'native_compile_errors':list(errors),
                'loop_seconds':48 if tv else None,
                'seconds_per_ad':12 if tv else None,'phase_seconds':phase,'glass':glass,'shader':code}

def apply(ctx,expected_map_sha256,native_probe_sha256):
    """Stage the approved local art; return only new dirty assets. No save/run."""
    import unreal as u
    from PlaceStationLocalArcade import _floor
    from RefineStationSocialSeatedCrew import _geometry
    from RefineStationSocialFinish import _surface,_aisle
    root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    map_file=root/('Content/'+MAP[6:]+'.umap')
    _require(re.fullmatch('[0-9a-f]{64}',expected_map_sha256) and _sha(map_file)==expected_map_sha256 and
             world.get_path_name().split('.')[0]==MAP,'Require exact latest owner-preview map')
    probe_path=SOURCE/'NativeDisplayProbe1.json'
    _require(re.fullmatch('[0-9a-f]{64}',native_probe_sha256) and _sha(probe_path)==native_probe_sha256,
             'Native display geometry receipt changed')
    probe=json.loads(probe_path.read_text())
    _require(probe['success'],'Native display probe did not pass')
    manifest,art=inspect_sources()
    source_hashes=dict(probe['source_sha256'])
    source_hashes[GRAPHITE]=_sha(root/('Content/'+GRAPHITE[6:]+'.uasset'))
    # Use the reviewed existing graphite and diffuser; do not create a new finish
    # or touch the current local lighting agent's materials.
    source_hashes[GLASS_LENS]=_sha(root/('Content/'+GLASS_LENS[6:]+'.uasset'))
    for path,digest in source_hashes.items():
        _require(_sha(root/('Content/'+path[6:]+'.uasset'))==digest,'Owned display source changed '+path)
    for row in probe['meshes']:
        mesh=ctx.asset(row['asset']);b=mesh.get_bounds()
        _require(math.dist(b.origin.to_tuple(),row['origin_cm'])<.001 and
                 math.dist(b.box_extent.to_tuple(),row['extent_cm'])<.001,'Native display bounds changed')
    actors=list(ctx.eas.get_all_level_actors())
    _require(not any(a.get_actor_label().startswith(PREFIX) for a in actors),'Preserve previous bar-display pass')
    before={a.get_path_name():_snapshot(a,u) for a in actors}
    dirty=[];materials={};material_rows=[]
    names=('05_Drinks_Menu','06_Kitchen_Menu','07_DrinksTablet','08_FoodTablet','09_VenueBanner','10_AdLoopAtlas')
    textures={n:_texture(n,art,u,dirty) for n in names}
    for name in names[:-1]:
        materials[name],r=_display_material(name,textures[name],u,dirty,glass=name in names[2:4]);material_rows.append(r)
    for index in range(2):
        materials['TV'+str(index)],r=_display_material('TV'+str(index),textures['10_AdLoopAtlas'],u,dirty,tv=True,phase=index*24.)
        material_rows.append(r)
    retired=set();changes=[]
    def attach(actor,parent):
        component=parent.get_component_by_class(u.StaticMeshComponent)
        _require(component and actor.attach_to_component(component,u.Name(''),u.AttachmentRule.KEEP_WORLD,
            u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False),'Display must attach to actual support')
    def pane(name,center,width,height,material,parent,roll=90.):
        actor=ctx.raw(PREFIX+name,PLANE,center,rot=(0.,0.,roll),scale=(width/100.,height/100.,1.),collision=False)
        actor.static_mesh_component.set_material(0,material)
        actor.static_mesh_component.set_cast_shadow(False)
        attach(actor,parent);return actor
    def box(name,center,size,parent=None,material=GRAPHITE):
        actor=ctx.box(PREFIX+name,center,size,ctx.asset(material),False)
        if parent:attach(actor,parent)
        return actor
    def retire(label):
        actor=_one(actors,label);retired.add(actor.get_path_name());ctx.hide(actor)
    # Preserve existing plaque geometry and location; lay art just in front.
    for label,graphic in (('Drinks','05_Drinks_Menu'),('Kitchen','06_Kitchen_Menu')):
        frame=_one(actors,'Refine/SocialDetail/Menu/'+label+'/Frame');c,e=mesh_union(frame)
        for part in ('Heading','Body'):retire('Refine/SocialDetail/Menu/'+label+'/'+part)
        ratio=2./3.;height=min(e.z*2.-12.,(e.x*2.-14.)/ratio);width=height*ratio
        actor=pane('Board '+label,(c.x,c.y+e.y+2.5,c.z),width,height,materials[graphic],frame)
        changes.append({'kind':'existing_board_graphics','label':label,'graphic':graphic,
                        'native_frame_pose':transform_record(frame),'image_size_cm':[width,height],
                        'letterbox_preserves_aspect':True,'surface':transform_record(actor)})
    frame=_one(actors,'Refine/Social/Bar/Identity/Backing');c,e=mesh_union(frame)
    retire('Refine/Social/Bar/Identity/Name')
    pane('Venue banner',(c.x,c.y+e.y+2.5,c.z),544.,68.,materials['09_VenueBanner'],frame)
    # Two native detailed monitor arms, each fixed to a slender grounded service
    # post behind the counter. Screens use their own true planar material slot.
    yaw=47.35;rotation=u.Rotator(pitch=0.,yaw=yaw,roll=0.);scale=1.8
    for index,x in enumerate((3470.,4830.)):
        screen=u.Vector(x,-4350.,255.)
        pivot=screen-rotation.quaternion().rotate_vector(u.Vector(*SCREEN_CENTER))*scale
        floor_hit=_floor(world,(pivot.x,pivot.y),[],u)
        floor=floor_hit['point'][2]
        base=box('TV %d/Foot'%index,(pivot.x,pivot.y,floor+2.),(30.,28.,4.))
        post=box('TV %d/Support'%index,(pivot.x,pivot.y,(floor+pivot.z+25.)*.5),
                 (12.,10.,pivot.z+25.-floor),base)
        actor=ctx.raw(PREFIX+'TV %d/Owned articulated frame'%index,TV,pivot,rotation,(scale,)*3,False)
        attach(actor,post);component=actor.static_mesh_component
        _require(component.get_num_materials()==8,'Native monitor slot count changed')
        original=[_path(component.get_material(i)) for i in range(8)]
        component.set_material(5,materials['TV'+str(index)])
        _require(all(_path(component.get_material(i))==original[i] for i in range(8) if i!=5),
                 'Native frame materials changed beyond screen slot')
        actual=component.get_world_transform().transform_location(u.Vector(*SCREEN_CENTER))
        _require(math.dist(actual.to_tuple(),screen.to_tuple())<.02,'TV native screen center differs')
        changes.append({'kind':'owned_tv','actor':transform_record(actor),'native_slot':5,
             'screen_center_cm':list(actual.to_tuple()),'screen_size_cm':[v*scale for v in SCREEN_SIZE],
             'source_frame_material_slots_preserved':7,'support_floor_cm':floor,'support_floor_hit':floor_hit})
    # Tablet foundations are actual rounded native tablet hardware, scaled down
    # as docking feet. Transparent upper glass has a real central clamp/stem.
    counters=[_one(actors,'Refine/Social/Bar/Counter '+s) for s in ('left','right')]
    _,geometry=_geometry(counters[0].static_mesh_component.static_mesh,False,u)
    obstacles=[_one(actors,'Refine/Social/Bar/'+n) for n in
        ('Coffee machine','Coffee glasses','Wine glass','Serving glasses')]
    supports=[]
    # Native author2 measured all five left-footprint samples at92.24733.
    # Both counters share mesh/rotation/scale and differ by exactly415cm X.
    _require(math.dist((counters[1].get_actor_location()-counters[0].get_actor_location()).to_tuple(),
                       (415.,0.,0.))<.01,'Counter pair no longer has the measured matching placement')
    for index,(counter,candidates) in enumerate(zip(counters,((4045.,),(4460.,)))):
        found=None;trials=[]
        for x in candidates:
            xy=(x,-4059.7);points=[xy]+[(x+sx*10.,xy[1]+sy*7.) for sx in (-1.,1.) for sy in (-1.,1.)]
            row={'xy':list(xy)}
            try:
                heights=[_surface(counter,geometry,*p,u) for p in points]
                clear=True
                for item in obstacles:
                    cc,ee=mesh_union(item)
                    clear=clear and not(abs(cc.x-x)<ee.x+24. and abs(cc.y-xy[1])<ee.y+15.)
                good=clear and max(heights)-min(heights)<.08 and abs(max(heights)-RECESSED_DOCK_TOP)<.08
                row.update(surface_z=heights,prop_clearance=clear,accepted=good)
                if good:found=(xy,max(heights));trials.append(row);break
            except RuntimeError as error:row.update(accepted=False,error=str(error))
            trials.append(row)
        _require(found is not None,'No supported clear tablet spot: '+json.dumps(trials))
        xy,top=found
        base=ctx.grounded(PREFIX+'Tablet %d/Native dock'%index,TABLET,xy,floor=top,yaw=90.,scale=(.42,)*3,collision=False)
        attach(base,counter)
        base.static_mesh_component.set_material(0,ctx.asset(GRAPHITE))
        center=(xy[0],xy[1]-4.7,126.)
        stem_bottom=top+.5
        stem_top=116.3
        stem=box('Tablet %d/Stem'%index,(xy[0],xy[1],(stem_bottom+stem_top)*.5),
                 (4.,4.,stem_top-stem_bottom),base)
        box('Tablet %d/Clamp'%index,(xy[0],xy[1],114.7),(18.,3.6,3.2),stem)
        name=('07_DrinksTablet','08_FoodTablet')[index]
        pane('Tablet %d/Glass menu'%index,center,39.5,24.6875,materials[name],stem,roll=68.)
        # Thin native practical inset inside the clamp, not another PointLight.
        box('Tablet %d/Status lens'%index,(xy[0],xy[1]+1.85,114.7),(13.,.3,.65),stem,GLASS_LENS)
        supports.append({'tablet':index,'trials':trials,'native_top_cm':top,'base':transform_record(base),
                         'support_design':'Native recessed dock with continuous physical pedestal to shared glass height',
                         'pedestal_z_cm':[stem_bottom,stem_top],
                         'glass_center_cm':center,'size_cm':[39.5,24.6875],
                         'bartender_mark_separation_cm':math.dist(xy,(4150.,-4160.))})
    _aisle(world,u)
    for actor in actors:
        key=actor.get_path_name();old=before[key];now=_snapshot(actor,u)
        if key in retired:
            for field in ('location','rotation','scale','materials','lights'):
                _require(now[field]==old[field],'Retired text changed beyond visibility')
        else:_require(now==old,'Protected room actor changed '+actor.get_actor_label())
    _require(len(retired)==5,'Unexpected old-text retirement scope')
    _require(_sha(map_file)==expected_map_sha256 and all(_sha(root/('Content/'+p[6:]+'.uasset'))==h
        for p,h in source_hashes.items()),'Display helper must not save or change source packages')
    return {'dirty_assets':dirty,'source_sha256':source_hashes,'art_manifest_sha256':ART_SHA,
        'native_probe_sha256':native_probe_sha256,'materials':material_rows,'panels':changes,'tablet_support':supports,
        'retired_text_actors':sorted(retired),'created':[transform_record(a) for a in ctx.created],
        'new_light_count':0,'protected_existing_layout_animation_lighting_preserved':True,
        'limits':'Decorative fiction only. Native compilation, orientation, glass contrast, timed change and player-distance readability require actual capture.'}
