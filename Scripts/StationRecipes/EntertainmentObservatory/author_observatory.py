"""Build the isolated three-deck observatory. Never saves the main station."""
import json
import math
import traceback
from pathlib import Path
import unreal as u

ROOT=Path(__file__).resolve().parents[3]
R=ROOT/'.agent/local/Observatory_20261023'
BASE='/Game/SpaceSurvival/Licensed/EntertainmentObservatory'
MAP=BASE+'/L_EntertainmentObservatory'
es=u.get_editor_subsystem(u.EditorActorSubsystem)
ls=u.get_editor_subsystem(u.LevelEditorSubsystem)
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
lib=u.EditorAssetLibrary
edit=u.MaterialEditingLibrary
report={'errors':[],'assets':[],'features':[]}
assert '-RenderOffscreen' in u.SystemLibrary.get_command_line(), 'Use a hidden authoring editor'
assert '-SaveToUserDir' in u.SystemLibrary.get_command_line(), 'Use an isolated user profile'

def polar(r,angle,z):
    a=math.radians(angle);return (r*math.cos(a),r*math.sin(a),z)

def mat(name,color,metal=0,rough=.4,glow=0,glass=False,opacity=.28):
    path=BASE+'/Materials/'+name
    m=lib.load_asset(path) if lib.does_asset_exist(path) else u.AssetToolsHelpers.get_asset_tools().create_asset(name,BASE+'/Materials',u.Material,u.MaterialFactoryNew())
    edit.delete_all_material_expressions(m)
    m.set_editor_property('two_sided',glass)
    if glass:
        m.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT)
        m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    c=edit.create_material_expression(m,u.MaterialExpressionConstant3Vector)
    c.constant=u.LinearColor(*color,1)
    edit.connect_material_property(c,'',u.MaterialProperty.MP_EMISSIVE_COLOR if glass else u.MaterialProperty.MP_BASE_COLOR)
    if glow and not glass:
        e=edit.create_material_expression(m,u.MaterialExpressionConstant3Vector);e.constant=u.LinearColor(*(v*glow for v in color),1)
        edit.connect_material_property(e,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    for prop,val in ((u.MaterialProperty.MP_METALLIC,metal),(u.MaterialProperty.MP_ROUGHNESS,rough)):
        n=edit.create_material_expression(m,u.MaterialExpressionConstant);n.r=val;edit.connect_material_property(n,'',prop)
    if glass:
        f=edit.create_material_expression(m,u.MaterialExpressionFresnel)
        f.set_editor_property('base_reflect_fraction',.035);f.set_editor_property('exponent',4)
        mul=edit.create_material_expression(m,u.MaterialExpressionMultiply);mul.set_editor_property('const_b',opacity)
        edit.connect_material_expressions(f,'',mul,'A');edit.connect_material_property(mul,'',u.MaterialProperty.MP_OPACITY)
    edit.recompile_material(m);assert lib.save_loaded_asset(m)
    return m

def place(label,mesh,loc=(0,0,0),scale=(1,1,1),yaw=0,material=None,folder='Structure',collision=True):
    if isinstance(mesh,str):mesh=lib.load_asset(mesh)
    assert mesh,label
    a=es.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*loc),u.Rotator(yaw=yaw))
    a.set_actor_label('OBS/'+label);a.set_folder_path('Observatory/'+folder);a.set_actor_scale3d(u.Vector(*scale))
    c=a.static_mesh_component;c.set_static_mesh(mesh)
    c.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
    if material:c.set_material(0,material)
    return a

def sign(label,text,loc,yaw,size=24,color=(160,215,255)):
    a=es.spawn_actor_from_class(u.TextRenderActor,u.Vector(*loc),u.Rotator(yaw=yaw))
    a.set_actor_label('OBS/'+label);a.set_folder_path('Observatory/Wayfinding')
    c=a.text_render;c.set_text(text);c.set_world_size(size);c.set_text_render_color(u.Color(*color,255))
    c.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER)
    return a

def beam(label,start,end,material,folder):
    delta=u.Vector(*(b-a for a,b in zip(start,end)))
    length=math.sqrt(sum((b-a)**2 for a,b in zip(start,end)))
    a=place(label,'/Engine/BasicShapes/Cylinder',tuple((a+b)/2 for a,b in zip(start,end)),
            (.05,.05,length/100),material=material,folder=folder)
    a.set_actor_rotation(u.MathLibrary.make_rot_from_z(delta),False)
    return a

try:
    try:
        import ss_catalog_refresh
        ss_catalog_refresh.unregister()
    except ImportError:pass
    assert ls.load_level(MAP)
    world=ed.get_editor_world()
    if any(a.get_actor_label().startswith('OBS/') for a in es.get_all_level_actors()):
        assert globals().get('OBSERVATORY_ALLOW_REBUILD',False), 'Existing observatory preserved; rebuild needs an explicit reviewed override'
    chars={}
    for a in es.get_all_level_actors():
        name=a.get_actor_label()
        if name in ('Jinx','Roxie','Vesper','Vexa'):chars[name]=a
        elif name.startswith('Legacy/'):continue
        elif a.get_class().get_name() not in ('WorldSettings','Brush','LevelScriptActor'):es.destroy_actor(a)
    assert len(chars)==4,chars.keys()
    u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')
    meshes={}
    for src in sorted((ROOT/'SourceAssets/EntertainmentObservatory/Modules').glob('*.fbx')):
        path=BASE+'/Architecture/'+src.stem
        if not lib.does_asset_exist(path):
            t=u.AssetImportTask();t.filename=str(src);t.destination_path=BASE+'/Architecture';t.automated=True;t.save=True;t.factory=u.FbxFactory()
            o=u.FbxImportUI();o.import_mesh=True;o.import_materials=False;o.import_textures=False;o.import_as_skeletal=False
            o.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
            o.static_mesh_import_data.convert_scene_unit=True;o.static_mesh_import_data.auto_generate_collision=False;o.static_mesh_import_data.one_convex_hull_per_ucx=True
            t.options=o;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        meshes[src.stem]=lib.load_asset(path);assert meshes[src.stem],path
        report['assets'].append(path)
    assert len(meshes)==12,len(meshes)
    pearl=mat('M_Pearl',(.56,.63,.69),.2,.4,.035)
    deck=mat('M_Graphite',(.022,.031,.05),.2,.42)
    violet=mat('M_Violet',(.24,.025,.5),.2,.25,3)
    cyan=mat('M_Ice',(.06,.55,.8),.15,.25,3)
    metal=mat('M_Titanium',(.15,.20,.27),.85,.28)
    warm=mat('M_Champagne',(.55,.32,.14),.75,.25)
    glass=mat('M_ChamberGlass',(.08,.42,.52),glass=True)
    window_glass=mat('M_WindowClear',(.015,.025,.04),glass=True,opacity=.06)
    cube='/Engine/BasicShapes/Cube';cyl='/Engine/BasicShapes/Cylinder'
    place('GroundDeck',cyl,(0,0,-22),(46,46,.44),material=deck,folder='01/Shell')
    for floor,z in ((2,600),(3,1200)):
        gap={16,17,18,19} if floor==2 else {21,22,23,24}
        for i in range(32):
            yaw=i*11.25
            place(f'Deck{floor}/Inner/{i}',meshes['SM_Obs_InnerDeck'],(0,0,z),yaw=yaw,material=deck,folder=f'0{floor}/Deck')
            if i not in gap:place(f'Deck{floor}/Outer/{i}',meshes['SM_Obs_OuterDeck'],(0,0,z),yaw=yaw,material=deck,folder=f'0{floor}/Deck')
            place(f'Deck{floor}/Inlay/{i}',meshes['SM_Obs_FloorTrim'],(0,0,z+1),yaw=yaw,material=cyan,folder=f'0{floor}/Trim',collision=False)
            place(f'Deck{floor}/OuterInlay/{i}',meshes['SM_Obs_OuterTrim'],(0,0,z+1),yaw=yaw,material=violet,folder=f'0{floor}/Trim',collision=False)
            place(f'Deck{floor}/InnerRail/{i}',meshes['SM_Obs_Rail'],(0,0,z+108),yaw=yaw,material=metal,folder=f'0{floor}/Rail')
            place(f'Deck{floor}/MidRail/{i}',meshes['SM_Obs_Rail'],(0,0,z+55),yaw=yaw,material=metal,folder=f'0{floor}/Rail')
            place(f'Deck{floor}/RailPost/{i}',cyl,polar(425,yaw,z+54),(.035,.035,1.08),material=metal,folder=f'0{floor}/Rail')
        # Clear exterior stair shafts while the inner circulation ring stays continuous.
        for i in range(32):
            if floor==2:
                place(f'EnclosedMiddleWall/{i}',meshes['SM_Obs_Wall'],(0,0,600),yaw=i*11.25,material=pearl,folder='02/Shell')
            else:
                theta=i*11.25
                # Vendor pivot is at the roof rail; local +Y spans one 4m bay.
                rad=math.radians(theta)
                pos=(1820*math.cos(rad)+220*math.sin(rad),1820*math.sin(rad)-220*math.cos(rad),1738)
                p='/Game/Galaxy/Meshes/Architecture/Large_Glass/SM_Glass_A_45_Long_A'
                window=place(f'PanoramaWindow/{i}',p,pos,(1,1.1,.78),yaw=theta,folder='03/SpectrumWindows')
                window.static_mesh_component.set_material(1,window_glass)
                place(f'PanoramaTrim/{i}',p+'_Trim_A',pos,(1,1.1,.78),yaw=theta,folder='03/SpectrumWindows',collision=False)
    for i in range(32):
        yaw=i*11.25
        if i not in (23,24,25):place(f'GroundWall/{i}',meshes['SM_Obs_Wall'],yaw=yaw,material=metal,folder='01/Shell')
        place(f'Roof/{i}',meshes['SM_Obs_Roof'],(0,0,1800),yaw=yaw,material=pearl,folder='03/Ceiling')
        place(f'CeilingCrown/{i}',meshes['SM_Obs_Crown'],(0,0,1760),yaw=yaw,material=pearl,folder='Chamber')
        for z in (605,1185,1750):
            place(f'ChamberCollar/{z}/{i}',meshes['SM_Obs_Collar'],(0,0,z),yaw=yaw,material=metal,folder='Chamber')
            place(f'ChamberLight/{z}/{i}',meshes['SM_Obs_FloorTrim'],(0,0,z+12),(.85,.85,1),yaw=yaw,material=cyan,folder='Chamber',collision=False)
        place(f'ChamberGlass/{i}',meshes['SM_Obs_Glass'],(0,0,615),yaw=yaw,material=glass,folder='Chamber',collision=False)
    # Chamber has one continuous interior through decks 2 and 3.
    place('ChamberBase',cyl,(0,0,595),(7,7,.18),material=metal,folder='Chamber')
    place('ChamberCeiling',cyl,(0,0,1790),(7,7,.2),material=pearl,folder='Chamber')
    place('Pole',cyl,(0,0,1195),(.05,.05,11.6),material=warm,folder='Chamber')
    for floor,start in ((1,181),(2,237.25)):
        base=(floor-1)*600
        for j in range(40):
            angle=start+j*.90;z=base+j*15
            place(f'Stairs{floor}/{j}',meshes['SM_Obs_Stair'],(0,0,z),yaw=angle,material=pearl,folder=f'Stairs/{floor}')
            for side,radius,limit in (('Inner',1828,36),('Outer',2052,39)):
                if j<limit:
                    for height in (60,110):
                        beam(f'StairRail{floor}/{side}/{height}/{j}',polar(radius,angle,z+height),
                             polar(radius,angle+.90,z+15+height),warm,f'Stairs/{floor}')
                if j<=limit and (j%4==0 or j==limit):
                    place(f'StairPost{floor}/{side}/{j}',cyl,polar(radius,angle,z+62.5),(.04,.04,.95),material=metal,folder=f'Stairs/{floor}')
        # Extend the landing inward onto the continuous circulation ring.
        # 0.75cm lip prevents coplanar flicker where the landing meets the deck.
        place(f'Landing{floor}',cube,polar(1900,start+37.15,base+588.75),(4.5,1.1,.24),yaw=start+37.15,material=pearl,folder=f'Stairs/{floor}')
        # Protect the open side of the upper circulation ring beside the stairwell.
        for j in range(45):
            angle=start-6+j*.90
            place(f'ShaftRail{floor}/{j}',meshes['SM_Obs_StairRail'],(0,0,base+708),(1764/1828,1764/1828,1),yaw=angle,material=metal,folder=f'Stairs/{floor}')
            if j%5==0:place(f'ShaftPost{floor}/{j}',cyl,polar(1764,angle,base+654),(.035,.035,1.08),material=metal,folder=f'Stairs/{floor}')
    lounge='/Game/Galaxy/Meshes/Props/Lounge/'
    for floor,z in ((2,600),(3,1200)):
        # Distinct social pockets, with a broad path between seats and chamber.
        for pocket,angle in enumerate((15,75,135,300,345)):
            center=polar(1250,angle,z)
            place(f'Sofa{floor}/{pocket}',lounge+'SM_Sofa_A',center,yaw=angle-90,folder=f'0{floor}/Seating')
            for side in (-1,1):
                p=polar(1110,angle+side*9,z)
                place(f'Chair{floor}/{pocket}/{side}',lounge+'SM_Recliner_A',p,yaw=angle+90+side*25,folder=f'0{floor}/Seating')
            table=polar(1030,angle,z+35)
            place(f'Table{floor}/{pocket}',cyl,table,(1.1,1.1,.08),material=metal,folder=f'0{floor}/Seating')
            place(f'TableStem{floor}/{pocket}',cyl,(table[0],table[1],z+17),(.15,.15,.34),material=warm,folder=f'0{floor}/Seating')
            for k in (-1,1):place(f'Drink{floor}/{pocket}/{k}',lounge+'SM_Cup_B',(table[0]+k*18,table[1],z+40),folder=f'0{floor}/Details',collision=False)
    # Preserve original character instances and customization; move their demonstration positions.
    for idx,name in enumerate(('Jinx','Roxie','Vesper','Vexa')):
        a=chars[name];pos=polar(650,45+idx*90,1296)
        a.set_actor_location(u.Vector(*pos),False,True);a.set_actor_rotation(u.Rotator(yaw=225+idx*90),True)
        a.set_folder_path('Observatory/03/Performers')
        a.set_editor_property('auto_possess_player',u.AutoReceiveInput.DISABLED)
    # Existing aerial routine demonstrates the shared chamber; original source clips are unchanged.
    performer=chars['Vexa'];performer.set_actor_location(u.Vector(0,0,930),False,True)
    performer.set_actor_rotation(u.Rotator(yaw=0),True);performer.set_folder_path('Observatory/Chamber')
    performer.character_movement.set_editor_property('default_land_movement_mode',u.MovementMode.MOVE_NONE)
    performer.character_movement.set_editor_property('gravity_scale',0)
    performer.character_movement.disable_movement()
    performer.set_actor_enable_collision(False)
    clip=lib.load_asset('/Game/SpaceSurvival/Licensed/CharacterWorkshop/Animations/A_F3_G1_G2_Routine')
    for c in performer.get_components_by_class(u.SkeletalMeshComponent):
        if c.get_editor_property('skeletal_mesh_asset'):
            c.set_leader_pose_component(None,True,True);c.override_animation_data(clip,True,True,8,1)
            c.set_update_animation_in_editor(True);c.set_collision_profile_name('NoCollision')
    for floor,z in ((2,600),(3,1200)):
        for i,ang in enumerate((40,140,220,320)):
            a=es.spawn_actor_from_class(u.RectLight,u.Vector(*polar(920,ang,z+475)),u.Rotator(pitch=-70,yaw=ang+180))
            a.set_actor_label(f'OBS/SoftLight{floor}/{i}');a.set_folder_path('Observatory/Lighting')
            c=a.rect_light_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_intensity(850);c.set_attenuation_radius(1550)
            c.set_source_width(450);c.set_source_height(300);c.set_cast_shadows(i<2)
            c.set_light_color(u.LinearColor(.72,.83,1,1))
        for i,ang in enumerate(range(0,360,45)):
            a=es.spawn_actor_from_class(u.RectLight,u.Vector(*polar(1700,ang,z+280)),u.Rotator(yaw=ang))
            a.set_actor_label(f'OBS/WallWash{floor}/{i}');a.set_folder_path('Observatory/Lighting')
            c=a.rect_light_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_intensity(240);c.set_attenuation_radius(1000)
            c.set_source_width(420);c.set_source_height(250);c.set_cast_shadows(False)
            c.set_light_color(u.LinearColor(.60,.48,1,1) if i%2 else u.LinearColor(.7,.82,1,1))
    sky=es.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,1800));sky.set_actor_label('OBS/Ambient');sky.set_folder_path('Observatory/Lighting')
    c=sky.get_component_by_class(u.SkyLightComponent);c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    c.set_cubemap(lib.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'));c.set_intensity(3);c.set_editor_property('lower_hemisphere_is_black',False)
    pp=es.spawn_actor_from_class(u.PostProcessVolume,u.Vector());pp.set_actor_label('OBS/Exposure');pp.set_folder_path('Observatory/Lighting');pp.set_editor_property('unbound',True)
    s=pp.get_editor_property('settings')
    for k,v in [('override_auto_exposure_min_brightness',True),('auto_exposure_min_brightness',3.0),('override_auto_exposure_max_brightness',True),('auto_exposure_max_brightness',3.0),('override_bloom_intensity',True),('bloom_intensity',.15)]:s.set_editor_property(k,v)
    pp.set_editor_property('settings',s)
    sky_path=BASE+'/Materials/MI_ObservatorySpace'
    sky_mat=lib.load_asset(sky_path) if lib.does_asset_exist(sky_path) else u.AssetToolsHelpers.get_asset_tools().create_asset('MI_ObservatorySpace',BASE+'/Materials',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
    edit.set_material_instance_parent(sky_mat,lib.load_asset('/Game/SpaceSurvival/Licensed/Atmosphere/M_RegionSky'))
    edit.set_material_instance_texture_parameter_value(sky_mat,'RegionA',lib.load_asset('/Game/SpaceSurvival/Licensed/Atmosphere/T_Region_Skybox_8'))
    edit.set_material_instance_scalar_parameter_value(sky_mat,'SkyBrightness',1.2)
    edit.set_material_instance_scalar_parameter_value(sky_mat,'StarBrightness',1.0)
    assert lib.save_loaded_asset(sky_mat)
    place('DeepSpacePanorama','/Engine/BasicShapes/Sphere',(0,0,900),(5000,5000,5000),material=sky_mat,folder='SpaceView',collision=False)
    sign('EntryTitle','01 / CREW SELECT + PERFORMANCE',(0,-2200,290),90,25)
    start=es.spawn_actor_from_class(u.PlayerStart,u.Vector(0,-1800,100));start.set_actor_label('OBS/PlayerStart');start.set_folder_path('Observatory/01')
    walk_mode=lib.load_blueprint_class('/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode')
    assert walk_mode
    world.get_world_settings().set_editor_property('default_game_mode',walk_mode)
    ed.set_level_viewport_camera_info(u.Vector(1300,-1200,1380),u.MathLibrary.find_look_at_rotation(u.Vector(1300,-1200,1380),u.Vector(0,100,1400)))
    assert ls.save_current_level()
    report.update(ok=True,map=MAP,actors=len(es.get_all_level_actors()),floors_cm=[0,600,1200],roof_cm=1800,diameter_m=46,original_station_saved=False)
except Exception:report['errors'].append(traceback.format_exc())
finally:
    (R/'Build.json').write_text(json.dumps(report,indent=2));print('OBSERVATORY_BUILD',report.get('ok'),report['errors'],flush=True)
    u.SystemLibrary.quit_editor()
