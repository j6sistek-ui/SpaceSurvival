"""Author four owned-content region recipes; keep originals and backup the private look.

Run after the Editor build. This is tunable art content, never a visual acceptance claim.
"""
import hashlib
import json
from pathlib import Path
import shutil
import uuid
import unreal as u

ROOT=Path(__file__).resolve().parents[1]
BASE='/Game/SpaceSurvival/Licensed/Atmosphere'
KIT='/Game/Megastructure_Scifi_World/Meshes/'
ROCK='/Game/Asteroid_Library/Static_Meshes/'
WRECK='/Game/SpaceSurvival/Licensed/OrbitalWreck/'
LIB=u.EditorAssetLibrary
EDIT=u.MaterialEditingLibrary

def mesh(path):
    obj=u.load_asset(path)
    assert isinstance(obj,u.StaticMesh),path
    return obj

def placement(path,center,radius,rotation=(0,0,0)):
    p=u.SSSceneryPlacement()
    p.set_editor_property('mesh',mesh(path))
    p.set_editor_property('center',u.Vector(*center))
    p.set_editor_property('radius',radius)
    p.set_editor_property('rotation',u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]))
    return p

def sky():
    path=BASE+'/M_SpatialAreaSky'
    material=LIB.load_asset(path) if LIB.does_asset_exist(path) else LIB.duplicate_asset(BASE+'/M_RegionSky',path)
    if LIB.get_metadata_tag(material,'SSSpatialGrade')!='1':
        original=EDIT.get_material_property_input_node(material,u.MaterialProperty.MP_EMISSIVE_COLOR)
        grade=EDIT.create_material_expression(material,u.MaterialExpressionCustom,1800,0)
        grade.set_editor_property('description','Desaturated deep-space background with regional haze palette')
        grade.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3)
        pins=[]
        for name in ('Sky','AreaTint'):
            pin=u.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
        grade.set_editor_property('inputs',pins)
        grade.set_editor_property('code','float l=dot(Sky,float3(.2126,.7152,.0722)); return (lerp(Sky,l.xxx,.95)*.16+.012)*max(AreaTint,float3(.15,.15,.15));')
        tint=EDIT.create_material_expression(material,u.MaterialExpressionVectorParameter,1600,200)
        tint.set_editor_property('parameter_name','AreaTint')
        tint.set_editor_property('default_value',u.LinearColor(.72,.9,1.,1))
        assert EDIT.connect_material_expressions(original,'',grade,'Sky')
        assert EDIT.connect_material_expressions(tint,'',grade,'AreaTint')
        assert EDIT.connect_material_property(grade,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
        LIB.set_metadata_tag(material,'SSSpatialGrade','1')
        EDIT.recompile_material(material)
        assert LIB.save_loaded_asset(material)
    # This private output has a single grade node at emissive; update its tuning
    # in place instead of stacking successive contrast operators on reruns.
    grade=EDIT.get_material_property_input_node(material,u.MaterialProperty.MP_EMISSIVE_COLOR)
    assert isinstance(grade,u.MaterialExpressionCustom)
    grade.set_editor_property('code','float l=dot(Sky,float3(.2126,.7152,.0722)); return (lerp(Sky,l.xxx,.95)*.16+.012)*max(AreaTint,float3(.15,.15,.15));')
    EDIT.recompile_material(material)
    assert LIB.save_loaded_asset(material)
    return material

def charcoal_assemblies():
    # Preserve the supplied detail/POM graphs in private material instances.
    source='/Game/Megastructure_Scifi_World/Materials/'
    palette={}
    for name in ('MI_metal_01','MI_metal_01_O'):
        path=BASE+'/'+name+'_Wreck'
        material=LIB.load_asset(path) if LIB.does_asset_exist(path) else LIB.duplicate_asset(source+name,path)
        EDIT.set_material_instance_vector_parameter_value(material,'Base Color',u.LinearColor(.32,.29,.25,1))
        assert LIB.save_loaded_asset(material)
        palette[name]=material
    for name in ('BrokenHullSpine','ButtressedChunk','FragmentedArch'):
        obj=mesh('/Game/SpaceSurvival/Licensed/SpatialAssemblies/SM_'+name)
        for index,slot in enumerate(obj.get_editor_property('static_materials')):
            original=slot.material_interface.get_name()
            for name,material in palette.items():
                if original in (name,name+'_Wreck'):obj.set_material(index,material)
        assert LIB.save_loaded_asset(obj)

def main():
    out=ROOT/'Artifacts/SpaceAreas'/uuid.uuid4().hex;out.mkdir(parents=True)
    lookfile=ROOT/'Content/SpaceSurvival/Licensed/Atmosphere/DA_DeepSpaceLook.uasset'
    shutil.copy2(lookfile,out/lookfile.name)
    look=LIB.load_asset(BASE+'/DA_DeepSpaceLook');assert look
    charcoal_assemblies()
    pillar=lambda n:KIT+f'Pillar/SM_architecture_module_{n:02}'
    panel=lambda n:KIT+f'Pannels/SM_Pannel_part_{n:02}'
    # Torn floor plating reads as hull skin rather than architecture, so it carries the
    # broken-structure story at a larger silhouette than the wall panels do.
    floor=lambda n:KIT+f'Floor/SM_floor_module_{n:02}'
    barren=[ROCK+n for n in ['SM_Asteroid_Barren_1','SM_Asteroid_Barren_2','SM_Asteroid_Barren_3','SM_AsteroidBarren_4']]
    mineral=[ROCK+f'SM_AsteroidMineral_{i}' for i in range(1,5)]
    fragments=[ROCK+f'SM_AsteroidFragment_{i}' for i in range(1,5)]
    arc=WRECK+'BrokenArc/SM_BrokenArc';ring=WRECK+'RingFragment/SM_RingFragment';beam=WRECK+'KitBeam/SM_KitBeam'
    station='/Game/SpaceSurvival/Licensed/StationVisualPass/Meshes/SM_Station3Exterior'
    assembly='/Game/SpaceSurvival/Licensed/SpatialAssemblies/'
    definitions=[
      ('ObsidianWreck',(.25,.28,.32),(1.,.96,.90),1.6,(1.55,.7,.45),[
        (assembly+'SM_BrokenHullSpine',(165000,-150000,-30000),105000,(35,25,65)),
        (assembly+'SM_ButtressedChunk',(190000,170000,15000),110000,(-25,50,-30)),
        (assembly+'SM_FragmentedArch',(335000,-70000,110000),65000,(30,-10,15)),
        (barren[2],(255000,65000,-95000),52000,(35,60,10)),
        (assembly+'SM_BrokenHullSpine',(410000,130000,85000),46000,(10,45,35)),
        (fragments[0],(110000,-110000,68000),31000,(65,20,15)),
        (beam,(295000,215000,-100000),38000,(25,30,55)),
        (station,(480000,-170000,20000),33000,(15,-25,0))],
        [(p,1.,1800.,11000.) for p in fragments+barren]+
        [(panel(n),2.,1200.,7500.) for n in (1,3,6,8,12)]+
        [(floor(n),1.5,2200.,9000.) for n in (2,4)]+[(pillar(4),1.,1800.,6500.)]),
      ('MineralReach',(.18,.32,.34),(.55,.83,1.),.65,(1.8,.5,.4),[
        (mineral[0],(170000,-145000,-55000),74000,(15,30,50)),
        (mineral[2],(215000,175000,50000),71000,(50,10,70)),
        (barren[1],(325000,-90000,100000),45000,(30,60,5)),
        (mineral[3],(345000,45000,-110000),55000,(20,-45,35)),
        (barren[2],(465000,-100000,-45000),65000,(70,0,15)),
        (fragments[2],(235000,85000,140000),21000,(20,40,80)),
        (mineral[1],(125000,-195000,115000),48000,(45,45,40)),
        (station,(470000,185000,55000),17000,(0,55,10))],
        [(p,3.,1400.,9500.) for p in mineral]+[(p,1.,900.,6500.) for p in fragments]+
        [(panel(n),.6,1000.,5000.) for n in (11,15)]),
      ('AlienCauseway',(.18,.29,.33),(.72,.9,.83),.85,(1.7,.4,.25),[
        (KIT+'Arch/SM_triangle_arch',(215000,135000,50000),100000,(20,35,70)),
        (pillar(12),(175000,-145000,-15000),98000,(0,25,80)),
        (KIT+'Arch/SM_arch_03',(315000,-105000,85000),62000,(30,55,10)),
        (assembly+'SM_FragmentedArch',(355000,60000,-125000),85000,(-10,-30,5)),
        (pillar(7),(390000,155000,40000),59000,(45,5,20)),
        (KIT+'Arch/SM_arch_01',(470000,65000,110000),39000,(70,-20,10)),
        (barren[0],(270000,-155000,-110000),55000,(20,45,50)),
        (pillar(3),(130000,-185000,115000),31000,(25,35,60))],
        [(p,1.,1300.,7500.) for p in fragments]+
        [(panel(n),2.,1400.,7000.) for n in (2,5,9,13)]+
        [(floor(n),1.,2000.,8000.) for n in (1,3)]+[(pillar(2),1.,1500.,5000.)]),
      ('AmberDerelict',(.36,.24,.16),(1.,.7,.42),1.15,(1.4,.75,.3),[
        (arc,(245000,210000,6000),150000,(75,5,105)),
        (ring,(165000,-155000,-80000),110000,(25,45,-30)),
        (barren[0],(270000,-125000,65000),66000,(20,35,70)),
        (barren[2],(385000,85000,100000),70000,(50,-10,35)),
        (beam,(220000,-190000,65000),50000,(10,70,45)),
        (station,(460000,-20000,65000),34000,(15,-30,0)),
        (barren[3],(340000,125000,-95000),49000,(75,40,25)),
        (fragments[3],(165000,175000,125000),34000,(10,40,70))],
        [(p,2.,1500.,11000.) for p in barren+fragments]+[(beam,1.,700.,4500.)]+
        [(panel(n),1.5,1100.,6500.) for n in (4,7,14)]+[(floor(4),1.,2400.,8500.)]),
    ]
    lighting={
        'ObsidianWreck':(.000018,3.8,6.),
        'MineralReach':(.000035,4.,8.),
        'AlienCauseway':(.000011,4.5,9.),
        'AmberDerelict':(.000027,4.5,7.),
    }
    # Per-zone height fog. Owner direction: some zones should be eerie and some fogless, and it is
    # easier to take fog away than to add it, so the field carries it and one region sets it to zero.
    zone_fog={
        'ObsidianWreck':.0042,   # the charcoal wreckfield, deliberately the eerie one
        'MineralReach':.0006,    # thinned: the rock field sits near the dark end, closer to art/asteroids.jpg
        'AlienCauseway':.0020,   # thinned: structures read harder against less haze
        'AmberDerelict':0.,      # genuinely fogless: hard edges, deep blacks, full contrast
    }
    recipes=[];record=[]
    for name,haze,key,density,axes,landmarks,candidates in definitions:
        haze_density,key_intensity,ambient_intensity=lighting[name]
        recipe=u.SSSpaceAreaRecipe()
        recipe.set_editor_property('name',name)
        recipe.set_editor_property('landmarks',[placement(*p) for p in landmarks])
        clutter=[]
        for path,weight,low,high in candidates:
            c=u.SSSceneryCandidate()
            for k,v in {'mesh':mesh(path),'weight':weight,'min_radius':low,'max_radius':high}.items():c.set_editor_property(k,v)
            clutter.append(c)
        for k,v in {'clutter':clutter,'clutter_density':density,'cluster_radius':135000.,'clear_radius':40000.,
                    'cluster_axes':u.Vector(*axes),'haze_color':u.LinearColor(*haze,1),
                    'haze_density':haze_density,'fog_density':zone_fog[name],'key_color':u.LinearColor(*key,1),'key_intensity':key_intensity,
                    'ambient_intensity':ambient_intensity}.items():recipe.set_editor_property(k,v)
        recipes.append(recipe);record.append({'name':name,'landmarks':landmarks,'clutter':candidates,'haze':haze,'density':density,'lighting':lighting[name]})
    for k,v in {'area_recipes':recipes,'area_cell_size':650000.,'area_clutter_budget':384,'area_landmark_budget':64,
                'sky_material':sky(),'fog_density':.0038,'fog_distance':600000.,'cloud_scale':u.Vector(1800,650,850),
                'cloud_offset_a':u.Vector(120000,100000,-25000),'cloud_offset_b':u.Vector(260000,-140000,65000),
                'override_flight_key_direction':True,'flight_key_rotation':u.Rotator(pitch=-28,yaw=-135,roll=0)}.items():
        look.set_editor_property(k,v)
    assert LIB.save_loaded_asset(look)
    report={'status':'AUTHORED_NOT_ACCEPTED','recipes':record,'look_sha256':hashlib.sha256(lookfile.read_bytes()).hexdigest(),
            'backup':str(out/lookfile.name),'limits':'Private recipes only. Actual game renders and independent review required.'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (out.parent/'latest.json').write_text(json.dumps({'root':str(out)}),encoding='utf-8')
    u.log('SPACE_AREAS_AUTHORED')

if __name__=='__main__':main()
