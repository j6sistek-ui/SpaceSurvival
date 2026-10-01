"""Build the private Wayfarer Exchange review map from owned kit assets.

Run in the isolated outpost checkout using UnrealEditor-Cmd -RenderOffscreen.
All writes stay under /Game/OutpostSandbox. Existing map is backed up before rebuilding.
Bounds are transformed deliberately; assembled vendor parts retain shared pivots.
"""
import json
import math
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT = ROOT / 'Artifacts/Outpost'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'Scripts'))
PLAN = json.loads(Path(__file__).with_name('OutpostAssets.json').read_text(encoding='utf-8'))
ASSETS = PLAN['assets']
TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
EAS = u.get_editor_subsystem(u.EditorActorSubsystem)
LIB = u.EditorAssetLibrary
EDIT = u.MaterialEditingLibrary
TOOLS = u.AssetToolsHelpers.get_asset_tools()
RECORDS = []
CACHE = {}
MATERIALS = {}
BALANCED = {}

def load(path):
    if path not in CACHE:
        CACHE[path] = u.load_asset(path)
        assert CACHE[path], 'Required asset missing: ' + path
    return CACHE[path]

def tag(actor, value):
    actor.tags = list(actor.tags) + [u.Name(value)]

def label(actor, name):
    actor.set_actor_label(name)
    actor.set_folder_path(name.split('/')[0])
    tag(actor, 'OutpostAuthored')
    return actor

def balanced(mat):
    if not isinstance(mat, u.MaterialInstanceConstant): return mat
    # Resolve our previous balanced child before computing source-relative gain.
    # Repeated authoring must not balance already compressed channels again.
    visited = set()
    while mat.get_path_name().startswith('/Game/OutpostSandbox/Materials/MI_Balanced_'):
        if mat.get_path_name() in visited:
            raise RuntimeError('Cyclic private balanced-material parent chain')
        visited.add(mat.get_path_name())
        mat = mat.get_editor_property('parent')
        if not isinstance(mat, u.MaterialInstanceConstant):
            raise RuntimeError('Balanced material lost its native instance parent')
    path = mat.get_path_name()
    if path in BALANCED: return BALANCED[path]
    params = {str(n): EDIT.get_material_instance_scalar_parameter_value(mat, n)
              for n in EDIT.get_scalar_parameter_names(mat)
              if (('emiss' in str(n).lower() or str(n).lower().startswith('intensity em')) and any(t in str(n).lower() for t in ('intens','strength','power')))}
    high = {k:v for k,v in params.items() if abs(v) > 30}
    em_channels = {k:v for k,v in params.items() if k.lower().startswith('intensity em')}
    peak = max((abs(v) for v in em_channels.values()), default=0.)
    if any(not math.isfinite(v) for v in params.values()):
        raise RuntimeError('Nonfinite emission parameter in '+path)
    channel_gain = min(1.,40./peak) if peak else 1.
    rough = {str(n): EDIT.get_material_instance_scalar_parameter_value(mat,n)
             for n in EDIT.get_scalar_parameter_names(mat) if str(n).lower() in ('roughness','roughness_a','roughness_b','roughness_c')}
    rough = {k:v for k,v in rough.items() if 0 <= v < .42}
    # Native inspection found negative roughness in kit damage/dirt layers.
    # Balance only private opaque derivatives, retaining the original textures.
    surface = {}
    if '/P1toP5_Bundle/' in path and '/Opaque/' in path:
        for key in EDIT.get_scalar_parameter_names(mat):
            key = str(key)
            value = EDIT.get_material_instance_scalar_parameter_value(mat,key)
            if key.startswith('Min Roughness') and value < .48: surface[key] = .48
            elif key.startswith('Max Roughness') and value > 1: surface[key] = 1.0
            elif key.startswith('Normal Intensity') and abs(value) > .65:
                surface[key] = math.copysign(.65,value)
    if high or rough or surface:
        import hashlib
        name = 'MI_Balanced_' + hashlib.sha1(path.encode()).hexdigest()[:12]
        dest = '/Game/OutpostSandbox/Materials/' + name
        child = load(dest) if LIB.does_asset_exist(dest) else TOOLS.create_asset(name, '/Game/OutpostSandbox/Materials', u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        changed = child.get_editor_property('parent') != mat
        if changed: EDIT.set_material_instance_parent(child, mat)
        overrides = dict(surface)
        overrides.update({key:.42 for key in rough})
        # These channels combine image, scan-line and animated effects. Preserve
        # every source ratio, including tiny channels, with one common gain.
        overrides.update({key:5.0 for key in high if key not in em_channels})
        if peak > 30:
            overrides.update({key:value*channel_gain for key,value in em_channels.items()})
        for key,value in overrides.items():
            current = EDIT.get_material_instance_scalar_parameter_value(child,key)
            if abs(current-value) > .000001:
                EDIT.set_material_instance_scalar_parameter_value(child,key,value)
                changed = True
        if changed: LIB.save_loaded_asset(child)
        BALANCED[path] = child
    else: BALANCED[path] = mat
    return BALANCED[path]

def finish(actor, name, solid=False, materials=None):
    label(actor,name)
    for c in actor.get_components_by_class(u.StaticMeshComponent):
        c.set_collision_profile_name('BlockAll' if solid else 'NoCollision')
        c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS if solid else u.CollisionEnabled.NO_COLLISION)
        for i,mat in enumerate(c.get_materials()):
            if mat: c.set_material(i, balanced(mat))
        if materials:
            for i,mat in enumerate(materials): c.set_material(i,mat)
    return actor

def raw(name,path,location,yaw=0,scale=(1,1,1),solid=False,materials=None,rotation=None):
    a = EAS.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*location))
    a.static_mesh_component.set_static_mesh(load(path))
    a.set_actor_rotation(u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]) if rotation else u.Rotator(yaw=yaw),False)
    a.set_actor_scale3d(u.Vector(*scale))
    finish(a,name,solid,materials)
    RECORDS.append({'name':name,'asset':path,'location':location,'rotation':rotation or [0,yaw,0],'scale':scale,'solid':solid})
    return a

def place(name,path,center,size=None,height=None,yaw=0,solid=False,material=None,support=None):
    mesh = load(path); b = mesh.get_bounds()
    dims = [b.box_extent.x*2,b.box_extent.y*2,b.box_extent.z*2]
    scale = [size[i]/max(dims[i],.001) for i in range(3)] if size else [height/dims[2]]*3 if height else [1,1,1]
    o = [b.origin.x*scale[0],b.origin.y*scale[1],b.origin.z*scale[2]]
    rad=math.radians(yaw); offset=[o[0]*math.cos(rad)-o[1]*math.sin(rad),o[0]*math.sin(rad)+o[1]*math.cos(rad),o[2]]
    a=raw(name,path,[center[i]-offset[i] for i in range(3)],yaw,scale,solid,[material] if material else None)
    if support is not None:
        tag(a,'OutpostRole:FloorProp');tag(a,'OutpostSupport:'+str(support))
    return a

def box(name,center,size,mat,solid=False,yaw=0):
    return place(name,'/Engine/BasicShapes/Cube.Cube',center,size=size,yaw=yaw,solid=solid,material=mat)

def disk(name,center,radius,height,mat,solid=False):
    return place(name,'/Engine/BasicShapes/Cylinder.Cylinder',center,size=[radius*2,radius*2,height],solid=solid,material=mat)

def ring(name,center,radius,mat,kind='Halo',height=None):
    path='/Game/OutpostSandbox/Geometry/SM_Outpost'+kind
    return place(name,path,center,size=[radius*2,radius*2,height or radius*.04],material=mat)

def material(name,color,metal=.6,rough=.35,emission=0,opacity=None):
    path='/Game/OutpostSandbox/Materials/'+name
    mat=load(path) if LIB.does_asset_exist(path) else TOOLS.create_asset(name,'/Game/OutpostSandbox/Materials',u.Material,u.MaterialFactoryNew())
    EDIT.delete_all_material_expressions(mat)
    color_node=EDIT.create_material_expression(mat,u.MaterialExpressionVectorParameter)
    color_node.set_editor_property('parameter_name','HullTint');color_node.set_editor_property('default_value',u.LinearColor(*color,1))
    if emission:
        mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
        mul=EDIT.create_material_expression(mat,u.MaterialExpressionMultiply);mul.set_editor_property('const_b',emission)
        EDIT.connect_material_expressions(color_node,'',mul,'A')
        EDIT.connect_material_property(mul,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    else:
        EDIT.connect_material_property(color_node,'',u.MaterialProperty.MP_BASE_COLOR)
        for value,prop in [(metal,u.MaterialProperty.MP_METALLIC),(rough,u.MaterialProperty.MP_ROUGHNESS)]:
            node=EDIT.create_material_expression(mat,u.MaterialExpressionConstant);node.set_editor_property('r',value)
            EDIT.connect_material_property(node,'',prop)
    if opacity is not None:
        mat.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT)
        mat.set_editor_property('two_sided',True)
        mat.set_editor_property('used_with_skeletal_mesh',True)
        fres=EDIT.create_material_expression(mat,u.MaterialExpressionFresnel);fres.set_editor_property('base_reflect_fraction',float(opacity));fres.set_editor_property('exponent',2.5)
        EDIT.connect_material_property(fres,'',u.MaterialProperty.MP_OPACITY)
    EDIT.recompile_material(mat);LIB.save_loaded_asset(mat)
    MATERIALS[name]=mat
    return mat

def light(name,pos,color=(.55,.8,1),power=2500,radius=1100,shadow=False):
    a=label(EAS.spawn_actor_from_class(u.PointLight,u.Vector(*pos)),name)
    c=a.get_component_by_class(u.PointLightComponent);c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_editor_property('intensity_units',u.LightUnits.LUMENS)
    c.set_intensity(power);c.set_light_color(u.LinearColor(*color,1));c.set_attenuation_radius(radius);c.set_cast_shadows(shadow)
    return a

def text(name,words,pos,yaw,size=35,color=(150,224,255)):
    a=label(EAS.spawn_actor_from_class(u.TextRenderActor,u.Vector(*pos)),name)
    a.set_actor_rotation(u.Rotator(yaw=yaw),False)
    c=a.get_component_by_class(u.TextRenderComponent);c.set_text(words);c.set_world_size(size)
    c.set_text_material(load('/Engine/EngineMaterials/UnlitText.UnlitText'))
    c.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER);c.set_text_render_color(u.Color(*color,255))
    c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    return a

def floor_rect(name,x,y,sx,sy):
    box('Ground/'+name,[x,y,-24],[sx,sy,48],DARK,True).set_actor_hidden_in_game(True)
    # Exactly fit panel bounds to the tiled footprint. Mesh details retain intended human scale.
    nx=round(sx/200);ny=round(sy/400)
    for ix in range(nx):
        for iy in range(ny):
            place(name+f'/Deck {ix:02}-{iy:02}',ASSETS['floor_main']['asset'],[x-sx/2+(ix+.5)*sx/nx,y-sy/2+(iy+.5)*sy/ny,-9],size=[sx/nx,sy/ny,18])

def edge_wall(name,pos,yaw,width=400,glass=False,holo=False):
    # All P4 wall parts share Xnormal/Ywidth/Zup and a floor pivot.
    x,y=pos
    if glass:
        frame=ASSETS['window_frame_4m']['asset'];pane=ASSETS['window_holo_4m' if holo else 'window_glass_4m']['asset']
        for suffix,path in [('Frame',frame),('Glass',pane)]: raw(name+'/'+suffix,path,[x,y,0],yaw,[1,width/400,1.6])
    else:
        for z in (0,200): raw(name+f'/Panel {z}',ASSETS['wall_main']['asset'],[x,y,z],yaw,[1,width/400,1])
    # Explicit wall collision: glass also blocks, none of the thin vendor shells are trusted.
    box(name+'/Solid wall',[x,y,200],[30,width,400],DARK,True,yaw).set_actor_hidden_in_game(True)
    box(name+'/Top beam',[x,y,425],[75,width+6,50],DARK,yaw=yaw)
    box(name+'/Light seam',[x,y,403],[12,width-20,4],CYAN,yaw=yaw)

def room(name,cx,cy,sx,sy,portal,accent):
    floor_rect(name,cx,cy,sx,sy)
    # West/east, south/north. Door spans middle600cm on requested side.
    for side,length in [('W',sy),('E',sy),('S',sx),('N',sx)]:
        n=math.ceil(length/400);step=length/n
        for i in range(n):
            t=-length/2+(i+.5)*step
            if side==portal and abs(t)<400: continue
            x=cx+(-sx/2 if side=='W' else sx/2 if side=='E' else t)
            y=cy+(-sy/2 if side=='S' else sy/2 if side=='N' else t)
            yaw={'W':0,'E':180,'S':90,'N':-90}[side]
            edge_wall(name+f'/Bay {side}{i}',(x,y),yaw,step,glass=(i%3==1),holo=(name=='Operations'))
    # Roof has kit texture beneath a sealed dark structural slab.
    # Observation decking is at Z520: its supporting Engineering slab must
    # stay below it while keeping the native ceiling top Z438 exposed.
    roof_z, roof_height = (477, 76) if name == 'Engineering' else (486, 80)
    box(name+'/Roof structure',[cx,cy,roof_z],[sx+100,sy+100,roof_height],DARK,True)
    for x in range(int(cx-sx/2+100),int(cx+sx/2),200):
        for y in range(int(cy-sy/2+200),int(cy+sy/2),400):
            raw(name+'/Ceiling panel',ASSETS['ceiling_main']['asset'],[x,y,438])
    for x in (cx-sx*.30,cx+sx*.30):
        box(name+'/Ceiling luminaire',[x,cy,430],[18,sy*.7,8],accent)
        light(name+'/Ceiling pool',[x,cy,340],power=1100,radius=1500,shadow=True)

def terminal(name,pos,action,description,target=None,yaw=180):
    a=label(EAS.spawn_actor_from_class(u.SSOutpostTerminal,u.Vector(*pos)),name)
    a.set_editor_property('display_name',name.split('/')[-1]);a.set_editor_property('description',description)
    a.set_editor_property('action',action)
    if target:a.set_editor_property('presentation_target',target)
    import textwrap
    words=name.split('/')[-1].replace('PAD / ','').replace('HUB / ','')
    words='\n'.join(textwrap.wrap(words,18))
    rad=math.radians(yaw);nx,ny=math.cos(rad),math.sin(rad)
    integrated = any(token in name for token in ('FLIGHT UPGRADES','COCKPIT','CONTRACT EXCHANGE','TRADE NETWORK','PILOT LEADERBOARD','SHIP & PARTS'))
    if integrated:
        text(name+'/Face',words,(pos[0],pos[1],pos[2]+40),yaw,9,(180,235,255))
    else:
        place(name+'/Console support',ASSETS['holo_projector']['asset'],[pos[0],pos[1],45],height=90)
        disk(name+'/Foot',[pos[0],pos[1],8],43,16,DARK)
        box(name+'/Stem',[pos[0],pos[1],55],[18,32,95],DARK)
        box(name+'/Display',[pos[0],pos[1],pos[2]+10],[8,105,54],DARK,yaw=yaw)
        box(name+'/Status line',[pos[0]+nx*5,pos[1]+ny*5,pos[2]+30],[3,95,2],CYAN,yaw=yaw)
        text(name+'/Face',words,(pos[0]+nx*6,pos[1]+ny*6,pos[2]+15),yaw,7,(210,239,255))
    return a

def door(name,pos,yaw):
    # Native frame authored around 300cm wide clear opening; leaves move outward on localY.
    raw(name+'/Frame',ASSETS['door_frame_4m']['asset'],pos,yaw,[1,1,1.25])
    a=label(EAS.spawn_actor_from_class(u.SSOutpostDoor,u.Vector(*pos)),name)
    a.set_actor_rotation(u.Rotator(yaw=yaw),False)
    a.left_leaf.set_static_mesh(load('/Engine/BasicShapes/Cube.Cube'));a.right_leaf.set_static_mesh(load('/Engine/BasicShapes/Cube.Cube'))
    for c in (a.left_leaf,a.right_leaf):
        c.set_relative_scale3d(u.Vector(.20,1.5,3));c.set_material(0,PEARL)
    tag(a,'OutpostRole:DoorLeaf')
    a.set_editor_property('sensor_radius',500)
    rad=math.radians(yaw)
    for side in (-1,1):
        dy=side*260
        box(name+'/Portal infill',[pos[0]-dy*math.sin(rad),pos[1]+dy*math.cos(rad),200],[70,120,400],DARK,True,yaw)
    box(name+'/Header',[pos[0],pos[1],352],[75,400,100],DARK,True,yaw)
    return a

def crew(name,pos,yaw=0,route=None,skin='Teal',phase=None,floor_z=0):
    a=label(EAS.spawn_actor_from_class(u.SSOutpostAmbientActor,u.Vector(pos[0],pos[1],floor_z+85)),name)
    a.set_actor_rotation(u.Rotator(yaw=yaw),False)
    c=a.character_mesh;mesh=load('/Game/Nyxar/Meshes/SKM_Nyxar.SKM_Nyxar');c.set_skeletal_mesh_asset(mesh)
    b=mesh.get_bounds();scale=190/(b.box_extent.z*2)
    c.set_relative_scale3d(u.Vector(scale,scale,scale));c.set_relative_rotation(u.Rotator(yaw=-90),False,False)
    c.set_relative_location(u.Vector(0,0,-85-(b.origin.z-b.box_extent.z)*scale),False,False)
    base='/Game/SpaceSurvival/Licensed/StationAssets/AlienCrew/'
    body=load(base+'MI_NyxarCrew_'+skin);c.set_material(c.get_num_materials()-1,body)
    idle=load(base+'Anims/A_Alien_Convo_11_Listening_Loop')
    walk=load(base+'Anims/A_Alien_MOB1_Walk_F_Loop_IPC')
    a.set_editor_property('idle_animation',idle);a.set_editor_property('walk_animation',walk)
    a.set_editor_property('gesture_animations',[load(base+'Anims/A_Alien_Convo_01_Low_Key_Loop')])
    a.set_editor_property('phase_offset',phase if phase is not None else sum(ord(c) for c in name)%23*.53)
    if route:a.set_editor_property('route_points',[u.Vector(*p) for p in route])
    c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
    data=c.get_editor_property('animation_data');data.anim_to_play=walk if route else idle;data.saved_looping=True;c.set_editor_property('animation_data',data)
    return a

def main():
    global DARK,PEARL,CYAN,AMBER,VIOLET,HOLO
    # Pause this process's optional catalog callback; preserve the owner's refresh preference.
    try:
        import ss_catalog_refresh
        handle=ss_catalog_refresh._state.get('handle')
        if handle:u.unregister_slate_post_tick_callback(handle);ss_catalog_refresh._state['handle']=None
    except ImportError:pass
    targetfile=ROOT/'Content/OutpostSandbox/L_AsteroidOutpost.umap'
    if targetfile.exists():
        backup=OUT/('L_AsteroidOutpost-before-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.umap')
        shutil.copy2(targetfile,backup)
    # Fresh map prevents accumulating last iteration's furniture or environment actors.
    assert u.EditorLoadingAndSavingUtils.new_blank_map(False), "Unable to create isolated blank map"
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    world.get_world_settings().set_editor_property('default_game_mode',u.SSOutpostSandboxGameMode)
    for f in (OUT/'Geometry').glob('*.fbx'):
        dest='/Game/OutpostSandbox/Geometry/'+f.stem
        if LIB.does_asset_exist(dest):continue
        task=u.AssetImportTask();task.filename=str(f);task.destination_path='/Game/OutpostSandbox/Geometry';task.destination_name=f.stem;task.automated=True;task.save=True
        opts=u.FbxImportUI();opts.import_mesh=True;opts.import_materials=False;opts.import_textures=False;opts.import_as_skeletal=False
        opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False
        task.options=opts;TOOLS.import_asset_tasks([task]);assert LIB.does_asset_exist(dest),dest
    DARK=material('M_OutpostGraphite',(.045,.065,.08),.65,.52)
    PEARL=material('M_OutpostPearl',(.30,.37,.40),.55,.50)
    CYAN=material('M_OutpostCyan',(.08,.68,1),emission=6)
    AMBER=material('M_OutpostAmber',(1,.37,.06),emission=5)
    VIOLET=material('M_OutpostViolet',(.45,.12,1),emission=4)
    HOLO=material('M_OutpostHologram',(.05,.58,1),emission=6,opacity=.4)

    # Single shared environment, no imported example atmospheres or extreme postprocessing.
    parent=load('/Game/SpaceSurvival/Licensed/Atmosphere/M_RegionSky')
    skyname='MI_OutpostStars';skypath='/Game/OutpostSandbox/Materials/'+skyname
    sky=load(skypath) if LIB.does_asset_exist(skypath) else TOOLS.create_asset(skyname,'/Game/OutpostSandbox/Materials',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
    EDIT.set_material_instance_parent(sky,parent)
    EDIT.set_material_instance_scalar_parameter_value(sky,'SkyBrightness',.015)
    EDIT.set_material_instance_scalar_parameter_value(sky,'StarBrightness',.6);LIB.save_loaded_asset(sky)
    dome=place('Environment/Starfield','/Engine/BasicShapes/Sphere.Sphere',[0,0,0],size=[180000]*3,material=sky)
    dome.static_mesh_component.set_cast_shadow(False)
    tag(dome,'OutpostRole:Sky')
    sun=label(EAS.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,10000)),'Environment/Cold starlight')
    sun.set_actor_rotation(u.Rotator(pitch=-35,yaw=-125),False)
    lc=sun.get_component_by_class(u.DirectionalLightComponent);lc.set_mobility(u.ComponentMobility.MOVABLE);lc.set_intensity(.85);lc.set_light_color(u.LinearColor(.64,.77,1,1));lc.set_editor_property('atmosphere_sun_light',False)
    pp=label(EAS.spawn_actor_from_class(u.PostProcessVolume,u.Vector()),'Environment/Neutral exposure')
    pp.set_editor_property('unbound',True);s=pp.settings
    ev=3 if u.SystemLibrary.get_console_variable_int_value('r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange') else 8
    for name,value in [('auto_exposure_min_brightness',ev),('auto_exposure_max_brightness',ev),('auto_exposure_bias',0),('bloom_intensity',.20),('vignette_intensity',.20),('motion_blur_amount',0)]:
        s.set_editor_property('override_'+name,True);s.set_editor_property(name,value)
    pp.settings=s
    fill=label(EAS.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,9000)),'Environment/Soft orbital bounce')
    fill.set_actor_rotation(u.Rotator(pitch=-25,yaw=45),False)
    fc=fill.get_component_by_class(u.DirectionalLightComponent);fc.set_mobility(u.ComponentMobility.MOVABLE);fc.set_intensity(.6);fc.set_light_color(u.LinearColor(.26,.41,.62,1));fc.set_cast_shadows(False);fc.set_editor_property('atmosphere_sun_light',False)

    import OutpostEnvironment
    OutpostEnvironment.apply(globals())

    asteroid='/Game/SpaceSurvival/Licensed/StationReset/SM_StationAsteroid.SM_StationAsteroid'
    place('Asteroid/Foundation',asteroid,[1400,0,-8800],size=[24000,22000,17000])
    # Rear massif starts behind operations. Facade is built in front, never intersecting walkable rooms.
    place('Asteroid/Rear massif',asteroid,[13200,500,-600],size=[6500,15500,8500],yaw=0)
    # Player deck, two commercial berths, and supported connecting bridges.
    for name,x,y,r in [('Player berth',-4200,0,3000),('Visitor berth 02',-600,-3900,1400),('Visitor berth 03',-600,3900,1400)]:
        disk('Ground/'+name,[x,y,-45],r,90,DARK,True).set_actor_hidden_in_game(True)
        disk(name+'/Deck',[x,y,-4],r-35,8,PEARL)
        ring(name+'/Approach halo',[x,y,3],r-45,CYAN,height=7)
        ring(name+'/Inset markings',[x,y,4],r*.68,AMBER if x==-4200 else CYAN,height=2)
        disk(name+'/Underside',[x,y,-240],r*.92,340,DARK)
        for a in range(30,360,30):
            rad=math.radians(a);px=x+(r-100)*math.cos(rad);py=y+(r-100)*math.sin(rad)
            if x==-4200 and a in (330,30):continue
            box(name+'/Edge marker',[px,py,35],[45,22,70],DARK,yaw=a)
            box(name+'/Edge lamp',[px,py,75],[30,15,8],CYAN,yaw=a)
        light(name+'/Pool',[x,y,950],power=16000,radius=r*1.2)
    for y in (-2150,2150):floor_rect('Access bridge',-600,y,800,800)
    floor_rect('Market',550,0,4100,4800)
    for y in (-2380,2380):
        for x in range(-1400,2500,400):
            if -1050<x<-150:continue
            box('Market/Guardrail',[x,y,105],[360,12,12],PEARL,True)
            box('Market/Rail post',[x,y,50],[16,16,100],DARK,True)
    for y in (-450,450):box('Market/Navigation strip',[700,y,2],[3700,7,3],CYAN)
    for x in (-1000,600,2050):
        for y in (-2250,2250):
            box('Market/Service pylon',[x,y,180],[70,70,360],DARK,True)
            box('Market/Pylon light',[x-40,y,215],[7,35,150],CYAN)
            light('Market/Pedestrian pool',[x,y,300],power=1800,radius=1100)

    # Sixteen-sided concourse with four strong thresholds and an oculus.
    disk('Ground/Atrium',[4200,0,-30],1650,60,DARK,True).set_actor_hidden_in_game(True)
    disk('Atrium/Deck',[4200,0,-24],1610,12,DARK)
    ring('Atrium/Navigation ring',[4200,0,2],1200,CYAN,height=3)
    ring('Atrium/Inner metal inlay',[4200,0,1],900,DARK,height=2)
    for dx in range(-1400,1500,200):
        for y in range(-1200,1300,400):
            if math.hypot(abs(dx)+100,abs(y)+200)<1570:
                place('Atrium/Floor panel',ASSETS['floor_main']['asset'],[4200+dx,y,-9],size=[200,400,18])
    for i in range(16):
        ang=i*22.5;rad=math.radians(ang);x=4200+1590*math.cos(rad);y=1590*math.sin(rad)
        if i%4==0:continue
        edge_wall('Atrium/Bay '+str(i),(x,y),ang+180,630,glass=(i%2==1))
        raw('Atrium/Upper service panel',ASSETS['wall_main']['asset'],[x,y,430],ang+180,[1,1.575,1])
        box('Atrium/Rib',[x,y,335],[90,55,670],DARK,yaw=ang)
    ring('Atrium/Oculus roof',[4200,0,710],1670,DARK,'Roof',height=80)
    ring('Atrium/Oculus light',[4200,0,650],730,CYAN,height=12)
    ring('Atrium/Upper gallery rim',[4200,0,660],1590,PEARL,'Collar',height=80)
    for ang in range(0,360,45):
        rad=math.radians(ang)
        light('Atrium/Light pool',[4200+1050*math.cos(rad),1050*math.sin(rad),520],power=1400,radius=1400,shadow=ang%90==0)
    # Branch connections remain open at their floor/roof seams.
    floor_rect('Engineering corridor',4200,-1975,600,750)
    floor_rect('Lounge corridor',4200,1975,600,750)
    floor_rect('Operations corridor',6100,0,600,600)
    for sign,y in [('ENGINEERING',-1980),('CREW LOUNGE',1980)]:
        box('Wayfinding/'+sign,[4200,y,395],[600,50,85],DARK)
        text('Wayfinding/'+sign,sign,[4200,y+(30 if y<0 else -30),390],90 if y<0 else -90,32)
    room('Engineering',4200,-3400,2600,2200,'N',AMBER)
    room('Lounge',4200,3400,2600,2200,'S',VIOLET)
    room('Operations',7800,0,2800,2600,'W',CYAN)
    for name,pos,yaw in [('Main threshold',(2600,0,0),0),('Engineering hatch',(4200,-2300,0),90),('Lounge hatch',(4200,2300,0),90),('Operations hatch',(6400,0,0),0)]:door('Doors/'+name,pos,yaw)
    import OutpostDoorVisuals
    OutpostDoorVisuals.apply(globals())
    # Entrance portal combines deep structural layers instead of a flat wall label.
    for y in (-430,430):
        box('Entrance/Portal pier',[2460,y,360],[230,130,720],DARK,True)
        box('Entrance/Light blade',[2310,y,340],[12,45,620],CYAN)
    box('Entrance/Crown',[2460,0,740],[280,1050,140],DARK)
    text('Entrance/Name','WAYFARER  EXCHANGE',[1960,0,724],180,32)
    text('Entrance/Subtitle','TRADE  /  REFIT  /  RECONNECT',[1958,0,683],180,15)
    light('Entrance/Warm welcome',[2100,0,420],(1,.62,.33),5000,1300)

    import OutpostEntranceDetails
    OutpostEntranceDetails.build(globals())
    import OutpostWorkstation
    workstation=OutpostWorkstation.build(globals())
    (OUT/'workstation.json').write_text(json.dumps(workstation,indent=2),encoding='utf-8')
    light('Engineering/Task light',OutpostWorkstation.TASK_LIGHT_POSITION,(1,.63,.40),1600,850)
    text('Engineering/Identity','01 / FLIGHT ENGINEERING',[4200,-4460,315],90,36,(255,183,82))
    terminal('Services/FLIGHT UPGRADES',OutpostWorkstation.UPGRADE_ACCESS,u.SSOutpostAction.INFORMATION,'Engineering workstation. Flight upgrade and purchase interface will be connected after this environment review.',yaw=90)
    # Curated prop composition from owned assets; assembly children share original pivots.
    import OutpostDressing
    catalog=json.loads(Path(os.environ.get('SS_PREFAB_CATALOG',str(ROOT/'Artifacts/PrefabLibrary/catalog.json'))).read_text(encoding='utf-8'))
    import OutpostSkyline
    import OutpostInteriorAssemblies
    dressing = [p for p in OutpostDressing.build(catalog)
                if not p["name"].startswith(OutpostInteriorAssemblies.REPLACED_DRESSING_PREFIXES)]
    for p in dressing + OutpostSkyline.build(catalog):
        if p.get('kind')=='blueprint':
            bp=load(p['asset']);a=EAS.spawn_actor_from_class(bp.generated_class(),u.Vector())
            a.set_actor_rotation(u.Rotator(yaw=p.get('yaw',0)),False)
            from OutpostGeometryUtils import fit_blueprint_from_geometry,mesh_union
            _,extent=mesh_union(a)
            fit_blueprint_from_geometry(a,p['center'],p.get('height') or extent.z*2)
            finish(a,p['name'],p.get('solid',False))
        else:
            a=place(p['name'],p['asset'],p['center'],size=p.get('size'),height=p.get('height'),yaw=p.get('yaw',0),solid=p.get('solid',False))
            if p.get('floor_z') is not None and not p.get('assembly'):
                tag(a,'OutpostRole:FloorProp');tag(a,'OutpostSupport:'+str(p['floor_z']))

    import OutpostRoofDetails, OutpostSkylineLighting
    OutpostRoofDetails.build(globals())
    OutpostSkylineLighting.build_lighting(globals())
    interiors=OutpostInteriorAssemblies.build(globals())
    (OUT/'interiors.json').write_text(json.dumps(interiors,indent=2),encoding='utf-8')
    import OutpostTechDisplays
    market=OutpostTechDisplays.build(globals())
    (OUT/'market.json').write_text(json.dumps(market,indent=2),encoding='utf-8')
    import OutpostGlobe
    OutpostGlobe.build(globals())
    import OutpostObservation
    observation=OutpostObservation.build(globals())
    (OUT/'observation.json').write_text(json.dumps(observation,indent=2),encoding='utf-8')
    # Holographic wardrobe stage, with actual owned characters and a usable cycle control.
    disk('Lounge/Hologram dais',[4750,3880,14],235,28,DARK,True)
    ring('Lounge/Projection rim',[4750,3880,30],225,VIOLET,height=8)
    holo=crew('Lounge/Wardrobe projection',(4750,3880),yaw=-90,skin='Violet')
    holo.set_actor_location(u.Vector(4750,3880,115),False,False)
    for i in range(holo.character_mesh.get_num_materials()):holo.character_mesh.set_material(i,HOLO)
    holo.body.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    tag(holo,'OutpostRole:Hologram')
    ward=terminal('Services/CREW WARDROBE',(4750,3570,100),u.SSOutpostAction.CYCLE_WARDROBE,'Cycle the holographic crew display.',holo,yaw=-90)
    ward.set_editor_property('hologram_material',HOLO)
    for x in (4390,5110):
        place('Lounge/Archive column',ASSETS['floor_wall_trim']['asset'],[x,4250,145],size=[100,125,290],yaw=-90)
        box('Lounge/Archive light',[x,4160,195],[14,8,220],VIOLET)
    for i,(x,y,z) in enumerate(interiors['hologram_character_feet']):
        preview=crew('Lounge/Archive projection '+str(i+1),(x,y),yaw=180,skin='Violet',floor_z=z)
        for slot in range(preview.character_mesh.get_num_materials()):preview.character_mesh.set_material(slot,HOLO)
        preview.body.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        tag(preview,'OutpostRole:Hologram')
    text('Lounge/Archive title','CREW ARCHIVE',[4750,4410,330],-90,23,(210,190,255))
    light('Lounge/Wardrobe key',[4550,3650,250],(.42,.52,1),1200,900)
    light('Lounge/Arcade key',[3730,3870,265],(1,.60,.35),1250,900)
    light('Lounge/Conversation pool',[3330,3260,245],(1,.72,.50),850,650)
    light('Lounge/East seating pool',[5020,2950,250],(.45,.70,1),650,650)
    text('Lounge/Arcade name','AFTERBURN / ARCADE',[3820,4420,290],-90,21,(255,197,100))
    text('Lounge/Identity','02 / CREW QUARTERS',[4200,4460,310],-90,36)
    text('Operations/Identity','03 / OPERATIONS',[9140,0,335],180,40)
    for labelname,pos,desc in [
        ('CONTRACT EXCHANGE',(8590,-560,135),'Contract display preview. Assignments will be connected after environment review.'),
        ('TRADE NETWORK',(8590,560,135),'Trade network display preview. No purchases or currency changes are made here.'),
        ('PILOT LEADERBOARD',(7700,565,150),'Pilot leaderboard display preview. Network services are not enabled.'),
        ('SHIP & PARTS',(3450,-4230,130),'Ship merchant display preview. Permanent ship and part purchases are not enabled in this sandbox.')]:
        terminal('Services/'+labelname,pos,u.SSOutpostAction.INFORMATION,desc,yaw=180 if pos[0]>8000 else -90)
    for name,pos in [('PAD / SURVIVAL DEPARTURES',(-1850,-1150,110)),('HUB / SURVIVAL DEPARTURES',(3250,-1030,110))]:
        terminal('Services/'+name,pos,u.SSOutpostAction.SURVIVAL_BOARDING,'Open the current game departure menu to start or continue Survival.',yaw=180)

    # Social islands face one another, with roaming crews kept on clear loop routes.
    for name,x,y,yaw,skin in [('Trader A',290,1535,0,'Amber'),('Trader B',790,1700,180,'Jade'),('Botanist',-530,-870,180,'Rose'),('Buyer',1040,-780,0,'Teal'),('Produce shopper',-1170,590,90,'Pale'),('Weighing shopper',50,-600,-90,'Rose'),('Machinery attendant',1850,-1100,180,'Violet'),('Atrium A',4700,750,-90,'Violet'),('Atrium B',4880,610,150,'Amber'),('Lounge guest',3800,3000,180,'Rose'),('Ops officer',8400,-500,130,'Teal'),('Engineer',4400,-3000,-90,'Jade'),('Pilot berth02',-300,-3200,90,'Pale'),('Pilot berth03',-300,3200,-90,'Amber')]:crew('Crew/'+name,(x,y),yaw,skin=skin)
    crew('Crew/Market courier',(-100,450),route=[(0,0,0),(1300,0,0),(1300,200,0),(0,200,0)],skin='Pale')
    crew('Crew/Atrium patrol',(3850,-350),route=[(0,0,0),(700,0,0),(700,700,0),(0,700,0)],skin='Teal')
    crew('Crew/Arcade visitor',(3860,4020),yaw=90,skin='Amber')
    crew('Crew/Lounge conversation A',(3800,3650),yaw=180,skin='Teal')
    crew('Crew/Lounge conversation B',(3960,3700),yaw=190,skin='Pale')
    crew('Crew/Observation visitor A',(3260,-3960),yaw=180,skin='Pale',floor_z=520)
    crew('Crew/Observation visitor B',(3770,-3930),yaw=195,skin='Violet',floor_z=520)
    import OutpostVehicles
    OutpostVehicles.build(EAS,load,material,terminal,OUT)
    import OutpostBerthDetails
    OutpostBerthDetails.build(globals())
    for i,(path,xy,yaw,shipheight) in enumerate([
        ('/Game/SpaceSurvival/Licensed/PlayerShipVisualPass/Meshes/SM_PlayerHavolkStarter',(-600,-3900),140,220),
        ('/Game/SpaceSurvival/Licensed/ShipVisualPass/Meshes/SM_FlankerHavolk',(-600,3900),210,180)]):
        mesh=load(path);b=mesh.get_bounds();sf=2.6 if i==0 else 3.0
        dims=[b.box_extent.x*2*sf,b.box_extent.y*2*sf,b.box_extent.z*2*sf]
        place('Visitors/Parked courier '+str(i),path,[xy[0],xy[1],shipheight+dims[2]/2],size=dims,yaw=yaw)
        for dx in (-200,200):
            box('Visitors/Service cradle',[xy[0]+dx,xy[1],shipheight/2],[95,370,shipheight],DARK,True,yaw)
        text('Visitors/Berth number','0'+str(i+2)+' / TRANSIT',[xy[0]+950,xy[1],40],180,42)
    # Spawn review walker looking toward market and entrance.
    for existing in EAS.get_all_level_actors():
        if isinstance(existing,u.PlayerStart):EAS.destroy_actor(existing)
    start=label(EAS.spawn_actor_from_class(u.PlayerStart,u.Vector(-1550,0,100)),'Start/Player approach')
    start.set_actor_rotation(u.Rotator(yaw=0),False)
    u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(-1900,-2200,700),u.Rotator(pitch=-12,yaw=25))
    assert u.EditorLoadingAndSavingUtils.save_map(world,TARGET)
    import OutpostDetailIntegration
    OutpostDetailIntegration.apply(globals())
    assert u.EditorLoadingAndSavingUtils.save_map(world,TARGET)
    LIB.save_directory('/Game/OutpostSandbox',only_if_is_dirty=True,recursive=True)
    (OUT/'build.json').write_text(json.dumps({'map':TARGET,'date':datetime.now(timezone.utc).isoformat(),'actor_count':len(EAS.get_all_level_actors()),'placements':RECORDS,'balanced_materials':list(BALANCED),'validation':'Pending visual and traversal audit'},indent=2),encoding='utf-8')
    u.log('OUTPOST_AUTHORED '+str(len(RECORDS)))
    u.EditorLoadingAndSavingUtils.load_map(TARGET)
    import ValidateOutpostSandbox
    ValidateOutpostSandbox.run(OUT/'placement-audit.json')

if __name__ == '__main__':
    main()
