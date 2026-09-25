"""Owned rotating planet art and seven welcome displays; no global sky Blueprint.

BP_Planet also owns a skybox, volumetric clouds and global atmosphere commands.
This presentation reuses its mesh and day/cloud textures through a private self-lit display material.
The 13m globe remains above walking headroom and passes through the 14.6m oculus.
"""
import json
import math
import unreal as u


def build(api):
    load, place, ring, text = (api[n] for n in ('load','place','ring','text'))
    eas, lib, tools, edit = (api[n] for n in ('EAS','LIB','TOOLS','EDIT'))
    center=(4200,0,1170)
    mesh='/Game/Planet_Project/Assets/Static_Meshes/SM_Earth_Planet'
    import OutpostPlanetDisplay
    display_material=OutpostPlanetDisplay.build(api)
    actor=place('Atrium/Planetary archive/World',mesh,center,size=[1300]*3,material=display_material)
    actor.static_mesh_component.set_cast_shadow(False)
    api['tag'](actor,'OutpostRole:DecorativeHologram')
    ring('Atrium/Projection emitter',(4200,0,2),420,api['CYAN'],height=3)
    ring('Atrium/Orbital halo',(4200,0,560),740,api['CYAN'],height=5)
    api['light']('Atrium/Globe key',(3300,-1000,1400),(.72,.83,1),18000,2000)
    # Owned framed screen assemblies retain their screen materials and motion.
    topics=[('WELCOME / WAYFARER','Welcome to Wayfarer Exchange. Market and landing berths outside; Engineering, Crew Lounge and Operations branch from this hall.'),
            ('FLIGHT ENGINEERING','Flight refits and the ship merchant are in Engineering. This sandbox previews the service layout.'),
            ('CREW ARCHIVE','Visit the Crew Lounge to preview installed characters as holograms.'),
            ('OPERATIONS','Operations hosts contract, trade and leaderboard display previews.'),
            ('SURVIVAL DEPARTURES','Use the departure terminal here or by the player berth to open Start or Continue Survival.'),
            ('OBSERVATION GALLERY','The upper glass gallery overlooks space and the visiting ships. Stairs are beside Engineering.'),
            ('MARKET / BERTHS','Explore the market and parked ships. Berth 01 remains reserved for the player; ship-finish preview is beside it.')]
    records=[]
    for i,(title,description) in enumerate(topics):
        angle=22.5+i*45;rad=math.radians(angle);nx,ny=math.cos(rad),math.sin(rad)
        x,y=4200+1040*nx,1040*ny
        bp=load('/Game/P1toP5_Bundle/P5_FruitSeller/Blueprints/BP_ISM_Screen_V3')
        actor=eas.spawn_actor_from_class(bp.generated_class(),u.Vector())
        actor.set_actor_rotation(u.Rotator(yaw=angle+90),False)
        from OutpostGeometryUtils import fit_blueprint_from_geometry
        fitted=fit_blueprint_from_geometry(actor,(x,y,190),120)
        api['finish'](actor,'Welcome/'+str(i+1)+'/Display',False)
        api['box']('Welcome/'+str(i+1)+'/Pedestal',(x,y,58),(48,48,116),api['DARK'],True)
        text('Welcome/'+str(i+1)+'/Heading',title,(x+nx*20,y+ny*20,257),angle,8,(165,231,255))
        service=eas.spawn_actor_from_class(u.SSOutpostTerminal,u.Vector(x+nx*50,y+ny*50,110))
        api['label'](service,'Welcome/'+str(i+1)+' / '+title)
        service.set_editor_property('display_name',title)
        service.set_editor_property('description',description)
        service.set_editor_property('action',u.SSOutpostAction.INFORMATION)
        records.append({'title':title,'center':[x,y,190],'angle':angle,'geometry_fit':fitted})
    (api['OUT']/'globe.json').write_text(json.dumps({'center':center,'diameter_cm':1300,'minimum_surface_z':520,'global_blueprint_used':False,'display_layers':1,'owned_textures':['T_8k_earth_daymap','T_8k_earth_clouds'],'information_displays':records},indent=2),encoding='utf-8')
