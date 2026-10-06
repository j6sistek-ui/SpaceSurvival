"""Versioned, CPU-only authored metal terminal and modular salvage crane revision.

Frozen1 is read-only input. V2 exports remain unfrozen until actual render review.
"""
import json
import math
import random
import shutil
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from finish_cabinets import cube, cylinder, panel, tube, front_panel, side_skin

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.agent/local/ArcadeGeneration/final'
TEX=OUT/'textures_v2'
GROUPS={}


def require_unfrozen(name):
    if (OUT.parent/'FROZEN_V2_MANIFEST.json').exists():
        raise RuntimeError('V2 is preserved; author a new version instead')
    manifest=OUT/name/'asset.json'
    if manifest.exists() and json.loads(manifest.read_text()).get('frozen'):
        raise RuntimeError('Refusing to overwrite frozen V2 output')


def mat(name,texture=None,color=(.05,.07,.09,1),metal=.75,rough=.28,emission=0,alpha=1):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    for key,value in [('Base Color',color),('Metallic',metal),('Roughness',rough),('Alpha',alpha),('Emission Strength',emission)]:
        p.inputs[key].default_value=value
    if texture:
        n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(TEX/(texture+'.png')),check_existing=True)
        m.node_tree.links.new(n.outputs['Color'],p.inputs['Base Color'])
        if emission:m.node_tree.links.new(n.outputs['Color'],p.inputs['Emission Color'])
    elif emission:p.inputs['Emission Color'].default_value=color
    return m


def group(before,name,pivot):
    items=[o for o in bpy.context.scene.objects if o not in before and o.type in {'MESH','CURVE'}]
    bpy.ops.object.select_all(action='DESELECT')
    for o in items:o.select_set(True)
    bpy.context.view_layer.objects.active=items[0]
    bpy.ops.object.convert(target='MESH');bpy.ops.object.join()
    o=bpy.context.object;o.name=name
    bpy.context.scene.cursor.location=pivot;bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    GROUPS[name]=o
    return o


def bolt(name,loc,metal,r=.006):
    o=cylinder(name,loc,r,.006,metal,6);o.rotation_euler.x=math.pi/2
    return o


def join_all(name):
    meshes=[o for o in bpy.context.scene.objects if o.type in {'MESH','CURVE'}]
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    bpy.ops.object.convert(target='MESH');bpy.ops.object.join()
    o=bpy.context.object;o.name=name
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return o


def frame(name,cx,y,z,w,h,thick,material,bevel=.003):
    for x in (cx-w/2,cx+w/2):cube(name+'_Vertical',(x,y,z),(thick,.024,h+thick),material,bevel)
    for zz in (z-h/2,z+h/2):cube(name+'_Horizontal',(cx,y,zz),(w-thick,.024,thick),material,bevel)


def metal_palette(prefix):
    return {
        'body':mat(prefix+'_CoatedMetal','V2_Graphite',metal=.73,rough=.29),
        'steel':mat(prefix+'_BrushedSteel','V2_Titanium',metal=.95,rough=.23),
        'bronze':mat(prefix+'_Bronze','V2_Bronze',metal=.91,rough=.27),
        'black':mat(prefix+'_Ceramic','V2_Ceramic',metal=.05,rough=.39),
        'rubber':mat(prefix+'_Gaskets',color=(.013,.018,.022,1),metal=0,rough=.66),
        'light':mat(prefix+'_CyanLight',color=(.065,.41,.53,1),metal=0,rough=.22,emission=1.4),
    }


def credit():
    require_unfrozen('CreditExchangeV2')
    name='CreditExchangeV2'
    bpy.ops.wm.read_factory_settings(use_empty=True);GROUPS.clear()
    p=metal_palette('CEV2')
    title=mat('CEV2_Title','CreditExchangeV2_Title',metal=.02,rough=.23,emission=.45)
    display=mat('CEV2_Display','CreditExchangeV2_Display',metal=0,rough=.19,emission=.7)
    scan=mat('CEV2_ScanDisplay','CreditExchangeV2_Scanner',metal=.05,rough=.2,emission=.45)
    plate=mat('CEV2_ServicePlate','CreditExchangeV2_ServicePlate',metal=.68,rough=.33)
    legends=mat('CEV2_ControlLegend','CreditExchangeV2_Controls',metal=.35,rough=.36)
    before=set(bpy.context.scene.objects)
    cube('GroundPlinth',(0,0,.06),(.92,.69,.12),p['body'],.012)
    for x in (-.35,.35):
        for y in (-.25,.24):cube('RecessedRubberFoot',(x,y,.025),(.15,.14,.05),p['rubber'],.005)
    cube('StructuralCore',(0,.015,.895),(.77,.53,1.54),p['body'],.006)
    # Deliberately planar extruded sheet-metal sides and a narrow bright edge.
    profile=[(-.31,.105),(.305,.105),(.305,1.765),(-.215,1.765),(-.31,1.654),(-.31,1.092),(-.43,1.01),(-.43,.925),(-.31,.843)]
    for sign in (-1,1):
        side_skin('FoldedSideShell',sign*.427,profile,p['steel'])
        side_skin('InsetCoatedSide',sign*.447,[(y+.010 if y<0 else y-.024,z+.025 if z<.2 else z-.021) for y,z in profile],p['body'])
        # Side-access plate, one seam and precise fixings.
        cube('SideAccessDoor',(sign*.470,.025,.47),(.014,.41,.59),p['body'],.004)
        for z in (.24,.28,.32,.36):cube('SideCoolingLouvre',(sign*.480,.058,z),(.009,.22,.007),p['black'],.001)
        for y in (-.15,.195):
            for z in (.2,.73):
                o=cylinder('SideFastener',(sign*.486,y,z),.005,.005,p['steel'],6);o.rotation_euler.y=math.pi/2
    cube('CanopyFold',(0,.039,1.748),(.865,.532,.037),p['body'],.004)
    cube('DisplayRecess',(0,-.290,1.346),(.812,.075,.536),p['rubber'],.004)
    frame('DisplayBezel',0,-.335,1.335,.750,.456,.027,p['steel'])
    front_panel('AccountInformation',.361,1.122,1.549,0,-.349,display)
    # Shallow top identity strip is separate from the actual information display.
    cube('MarqueeBacking',(0,-.298,1.660),(.801,.045,.113),p['black'],.004)
    front_panel('TerminalIdentity',.374,1.612,1.702,0,-.323,title)
    for x in (-.393,.393):
        for z in (1.098,1.566,1.65):bolt('TorxBezelFastener',(x,-.342,z),p['steel'])
    cube('ControlDeck',(0,-.296,.987),(.818,.258,.068),p['steel'],.005)
    cube('ControlInset',(0,-.313,1.024),(.753,.213,.013),p['body'],.003)
    cube('ScannerBezel',(-.223,-.313,1.038),(.225,.175,.022),p['black'],.005)
    panel('ScannerGlass',[(-.320,-.387,1.052),(-.126,-.387,1.052),(-.126,-.242,1.052),(-.320,-.242,1.052)],scan)
    cube('ScanIndicator',(-.223,-.227,1.043),(.123,.008,.009),p['light'],.001)
    # Separate recessed metal keys, consistent widths and tactile travel.
    cube('KeypadRecess',(.164,-.310,1.035),(.252,.187,.021),p['black'],.003)
    for row in range(3):
        for col in range(3):
            x=.084+col*.079;y=-.371+row*.060
            cube('NavigationKey',(x,y,1.050),(.062,.045,.010),p['steel'],.003)
            cube('KeyIndex',(x,y,1.056),(.022,.0025,.001),p['black'],.0001)
    cube('ConfirmButton',(.327,-.309,1.047),(.040,.167,.022),p['black'],.003)
    cube('ConfirmIndicator',(.327,-.309,1.059),(.010,.071,.004),p['light'],.001)
    panel('ControlLegends',[(-.373,-.440,.940),(.373,-.440,.940),(.373,-.440,.975),(-.373,-.440,.975)],legends)
    # Recessed service door surrounds a real depth dispenser opening.
    cube('ServiceDoor',(0,-.277,.480),(.753,.029,.672),p['body'],.003)
    frame('ServiceSeam',0,-.298,.487,.702,.590,.006,p['black'],.001)
    cube('DispenserRecess',(0,-.304,.695),(.474,.032,.103),p['black'],.003)
    frame('DispenserSteelLip',0,-.329,.698,.490,.107,.012,p['steel'],.002)
    cube('DispenserInnerFloor',(0,-.347,.657),(.455,.076,.008),p['steel'],.001)
    cube('DispenserHood',(0,-.341,.748),(.515,.091,.014),p['body'],.002)
    cube('DispenserStatus',(.221,-.342,.780),(.029,.005,.004),p['light'],.001)
    panel('ServiceID',[(-.266,-.300,.325),(.266,-.300,.325),(.266,-.300,.572),(-.266,-.300,.572)],plate)
    for x in (-.338,.338):
        for z in (.215,.776):bolt('ServiceDoorFastener',(x,-.302,z),p['steel'])
    for z in (.169,.192):cube('ToeVent',(0,-.318,z),(.551,.011,.007),p['black'],.001)
    cube('ToeGuard',(0,-.338,.112),(.862,.037,.034),p['steel'],.004)
    # Rear cover remains editable; no inaccessible paper-thin silhouette.
    cube('RearServiceCover',(0,.319,.873),(.753,.025,1.435),p['body'],.004)
    for z in (1.22,1.25,1.28,1.31,1.34):cube('RearVent',(0,.334,z),(.480,.012,.008),p['black'],.001)
    for o in bpy.context.scene.objects:
        if o not in before and o.type=='MESH':
            o.name='CEV2_'+o.name
            GROUPS[o.name]=o
    export(name,False,'Fully locally authored replacement housing, clean panels, scanner, keypad and dispenser; no AI mesh in V2',1.78)


def axis_cylinder(name,a,b,r,material,vertices=20):
    a,b=Vector(a),Vector(b)
    o=cylinder(name,(a+b)/2,r,(b-a).length,material,vertices)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o


def claw_finger(angle,p):
    # Curved jaw silhouette, tapered toward its inward-facing gripping tip.
    shape=[(.055,1.319),(.088,1.303),(.130,1.273),(.162,1.228),(.176,1.175),(.168,1.128),(.141,1.093),(.099,1.066),(.069,1.075),(.112,1.109),(.138,1.144),(.142,1.180),(.130,1.218),(.105,1.253),(.069,1.281)]
    vertices=[]
    for side in (-.008,.008):
        for r,z in shape:vertices.append((.07+r*math.cos(angle)-side*math.sin(angle),.045+r*math.sin(angle)+side*math.cos(angle),z))
    n=len(shape);faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    m=bpy.data.meshes.new('ClawJawProfile');m.from_pydata(vertices,[],faces);m.update()
    o=bpy.data.objects.new('MachinedClawJaw',m);bpy.context.collection.objects.link(o);o.data.materials.append(p['steel'])
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    bevel=o.modifiers.new('Machined jaw bevel','BEVEL');bevel.width=.002;bevel.segments=2;bpy.ops.object.modifier_apply(modifier=bevel.name);o.select_set(False)
    tangent=Vector((-math.sin(angle),math.cos(angle),0))
    pivot=Vector((.07+.068*math.cos(angle),.045+.068*math.sin(angle),1.306))
    axis_cylinder('JawHingePin',pivot-tangent*.022,pivot+tangent*.022,.020,p['bronze'],16)
    for sign in (-1,1):axis_cylinder('HingeCap',pivot+tangent*(sign*.022),pivot+tangent*(sign*.027),.011,p['steel'],12)
    a=(.07+.045*math.cos(angle),.045+.045*math.sin(angle),1.412)
    b=(.07+.116*math.cos(angle),.045+.116*math.sin(angle),1.266)
    axis_cylinder('JawActuatorRod',a,b,.005,p['steel'],12)
    v1=Vector(a).lerp(Vector(b),.17);v2=Vector(a).lerp(Vector(b),.60)
    axis_cylinder('JawActuatorSleeve',v1,v2,.010,p['bronze'],16)
    return pivot


def crystal(name,loc,r,height,material,rng):
    verts=[]
    for z,scale,angle in [(0,.74,0),(height*.62,1,.07),(height,.15,.20)]:
        for j in range(6):
            a=j*math.tau/6+angle;verts.append((loc[0]+math.cos(a)*r*scale,loc[1]+math.sin(a)*r*scale,loc[2]+z))
    faces=[tuple(range(5,-1,-1)),tuple(range(12,18))]
    faces += [(k*6+j,k*6+(j+1)%6,(k+1)*6+(j+1)%6,(k+1)*6+j) for k in range(2) for j in range(6)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.data.materials.append(material)
    return o


def crane():
    require_unfrozen('RiftSalvageV2')
    name='RiftSalvageV2'
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'RiftSalvage/RiftSalvage.blend'));GROUPS.clear()
    for o in list(bpy.context.scene.objects):
        if any(k in o.name for k in ('Prize','Claw','HoistCable')):bpy.data.objects.remove(o,do_unlink=True)
    p=metal_palette('RSV2')
    mapping={'Rift_Graphite':p['body'],'Rift_Titanium':p['steel'],'Rift_WornBrass':p['bronze'],'Rift_Rubber':p['rubber']}
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        for i,m in enumerate(o.data.materials):
            if m.name in mapping:o.data.materials[i]=mapping[m.name]
        o.name=o.name.replace('RiftSalvage','RiftSalvageV2');GROUPS[o.name]=o
        if 'Joystick' in o.name:
            for face in o.data.polygons:face.use_smooth=True
    for m in list(bpy.data.materials):
        if not m.users:continue
        if m.name.startswith('Rift_'):
            m.name=m.name.replace('Rift_','RSV2_')
            node=m.node_tree.nodes.get('Principled BSDF')
            if 'Light' in m.name:node.inputs['Emission Strength'].default_value=1.0
            if 'Glass' in m.name:node.inputs['Alpha'].default_value=.035
    # New native texture identities: never collide with the already imported V1 set.
    copied={}
    for m in {m for o in GROUPS.values() for m in o.data.materials}:
        for node in m.node_tree.nodes:
            if node.type!='TEX_IMAGE' or not node.image:continue
            source=Path(bpy.path.abspath(node.image.filepath)).resolve()
            if source.parent==TEX.resolve():continue
            destination=TEX/('RSV2_'+source.name)
            if source not in copied:
                shutil.copyfile(source,destination)
                fresh=node.image.copy();fresh.name='RSV2_'+node.image.name;fresh.filepath=str(destination)
                copied[source]=fresh
            node.image=copied[source]
    # Metal carriage and cable, with visible mounting and three articulated jaws.
    before=set(bpy.context.scene.objects)
    cylinder('HoistUpperCollar',(.07,.045,1.524),.042,.046,p['steel'],24)
    axis_cylinder('BraidedLiftCable',(.07,.045,1.50),(.07,.045,1.435),.007,p['steel'],12)
    coil=[]
    for i in range(121):
        a=i/120*math.tau*10;coil.append((.092+.019*math.cos(a),.045+.019*math.sin(a),1.447+i/120*.110))
    tube('FlexibleControlCable',coil,.0028,p['rubber'])
    group(before,'SM_RiftSalvageV2_HoistCable',(.07,.045,1.548))
    before=set(bpy.context.scene.objects)
    cylinder('ClawMachinedBarrel',(.07,.045,1.381),.055,.146,p['steel'],32)
    for z,r in [(1.451,.060),(1.428,.061),(1.329,.064),(1.310,.070)]:cylinder('ActuatorCollar',(.07,.045,z),r,.010,p['bronze'],24)
    cylinder('ActuatorBase',(.07,.045,1.305),.047,.031,p['black'],24)
    for i in range(6):
        a=i*math.tau/6
        cube('MotorFin',(.07+.058*math.cos(a),.045+.058*math.sin(a),1.376),(.012,.012,.064),p['body'],.001)
    group(before,'SM_RiftSalvageV2_ClawBodyZ',(.07,.045,1.457))
    for i in range(3):
        before=set(bpy.context.scene.objects);pivot=claw_finger(i*math.tau/3+.25,p)
        group(before,f'SM_RiftSalvageV2_ClawFinger{i+1}',pivot)
    # Separate prizes on a witnessed common bed; varied salvage instead of giant gems.
    ore=mat('RSV2_MeteorOre',color=(.065,.088,.100,1),metal=.80,rough=.34)
    ore_light=mat('RSV2_OreExposedMetal',color=(.28,.22,.15,1),metal=.88,rough=.28)
    gem=mat('RSV2_Amethyst',color=(.145,.025,.31,1),metal=.28,rough=.14)
    gem2=mat('RSV2_ColdMineral',color=(.025,.17,.16,1),metal=.37,rough=.19)
    capsule_band=mat('RSV2_CapsuleIdentification',color=(.11,.22,.29,1),metal=.58,rough=.25)
    rng=random.Random(100620262)
    positions=[(-.335+c*.162+rng.uniform(-.013,.013),-.245+r*.160+rng.uniform(-.012,.012)) for r in range(4) for c in range(5)]
    for i,(x,y) in enumerate(positions):
        before=set(bpy.context.scene.objects)
        if i%4 in (0,1):
            cylinder('ContainmentCapsule', (0,0,0),.032,.108,p['body'],16)
            for z in (-.059,.059):
                cylinder('CapsuleEndcap',(0,0,z),.035,.016,p['steel'],16)
                cylinder('CapsulePort',(0,0,z*1.19),.016,.010,p['black'],12)
            for z in (-.036,.037):cylinder('CapsuleRetentionRing',(0,0,z),.036,.008,p['bronze'],16)
            cylinder('CapsuleIDBand',(0,0,0),.033,.019,capsule_band,16)
            for sign in (-1,1):cube('CapsuleGripRail',(sign*.034,0,0),(.009,.022,.058),p['steel'],.0015)
        else:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(0,0,0))
            o=bpy.context.object;o.name='RecoveredOreFragment';o.scale=(.055,.040,.025)
            o.data.materials.append(ore);o.data.materials.append(ore_light)
            for v in o.data.vertices:v.co*=rng.uniform(.88,1.12)
            for f in o.data.polygons:f.material_index=int(rng.random()<.17)
            bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
            if i%4==2:
                for j in range(3):crystal('EmbeddedMineral',((j-1)*.022,rng.uniform(-.012,.012),.013),rng.uniform(.014,.020),rng.uniform(.041,.074),gem if i%3 else gem2,rng)
        o=group(before,f'SM_RiftSalvageV2_Prize{i+1:02}',(0,0,0))
        o.rotation_euler=(math.pi/2 if i%4 in (0,1) else rng.uniform(-.14,.14),0 if i%4 in (0,1) else rng.uniform(-.2,.2),rng.uniform(0,math.tau))
        o.location=(x,y,0)
        bpy.context.view_layer.update()
        minimum=min((o.matrix_world@v.co).z for v in o.data.vertices)
        o.location.z=.865-minimum
    export(name,True,'Locally authored modular salvage crane; V2 replaces claw, cable and all prizes, retaining the authored V1 frame',2.11)


def bounds(objects):
    vv=[o.matrix_world@v.co for o in objects for v in o.data.vertices]
    return [[min(v[i] for v in vv) for i in range(3)],[max(v[i] for v in vv) for i in range(3)]]


def validate_uv(objects):
    repairs=0
    for o in objects:
        bm=bmesh.new();bm.from_mesh(o.data)
        bmesh.ops.dissolve_degenerate(bm,dist=1e-8,edges=list(bm.edges))
        dead=[f for f in bm.faces if f.calc_area()<1e-12]
        if dead:bmesh.ops.delete(bm,geom=dead,context='FACES')
        bm.to_mesh(o.data);bm.free();o.data.update();o.data.calc_loop_triangles()
        uv=o.data.uv_layers.active.data
        bad=set()
        for tri in o.data.loop_triangles:
            if tri.area<1e-12:raise RuntimeError('Collapsed triangle: '+o.name)
            a,b,c=[uv[i].uv for i in tri.loops]
            if abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))<1e-12:bad.add(tri.polygon_index)
        for index in bad:
            face=o.data.polygons[index];n=face.normal
            axis=min((Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))),key=lambda v:abs(v.dot(n)))
            u=n.cross(axis).normalized();v=n.cross(u).normalized()
            coords=[o.data.vertices[o.data.loops[i].vertex_index].co for i in face.loop_indices]
            scale=max(max(c.dot(u) for c in coords)-min(c.dot(u) for c in coords),max(c.dot(v) for c in coords)-min(c.dot(v) for c in coords),1e-8)
            for loop,c in zip(face.loop_indices,coords):uv[loop].uv=(c.dot(u)/scale,c.dot(v)/scale)
        repairs+=len(bad)
        for tri in o.data.loop_triangles:
            a,b,c=[uv[i].uv for i in tri.loops]
            if abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))<1e-12:raise RuntimeError('Degenerate UV triangle: '+o.name)
    return {'zero_area_triangles':0,'degenerate_uv_triangles':0,'reprojected_faces':repairs}


def export(name,split,provenance,height):
    require_unfrozen(name)
    target=OUT/name;target.mkdir(parents=True,exist_ok=True)
    objects=list(GROUPS.values())
    # Single-angle normals retain planar faces; bevels catch light without rounded bodies.
    for o in objects:
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        if not o.data.uv_layers:
            bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.cube_project(cube_size=.20);bpy.ops.object.mode_set(mode='OBJECT')
    uv_validation=validate_uv(objects)
    used={m.name:m for o in objects for m in o.data.materials}
    mats=[]
    for key,m in sorted(used.items()):
        p=m.node_tree.nodes.get('Principled BSDF')
        row={'slot':key,'base_color_texture':None,'base_color_linear':list(p.inputs['Base Color'].default_value),'metallic':p.inputs['Metallic'].default_value,'roughness':p.inputs['Roughness'].default_value,'emission_strength':p.inputs['Emission Strength'].default_value,'emission_color_linear':list(p.inputs['Emission Color'].default_value),'emission_uses_base_texture':p.inputs['Emission Color'].is_linked,'alpha':p.inputs['Alpha'].default_value,'transmission':0}
        for socket,field in [('Base Color','base_color_texture')]:
            if p.inputs[socket].is_linked:
                n=p.inputs[socket].links[0].from_node
                if n.type=='TEX_IMAGE':row[field]=str(Path(bpy.path.abspath(n.image.filepath)).resolve())
        mats.append(row)
    bb=bounds(objects)
    report={'name':name,'geometry_provenance':provenance,'texture_provenance':'Local procedural PBR maps and authored static service labels; no cloud generation','front_axis':'-Y in Blender','origin':'ground center for combined exports; named editable mechanisms preserve pivots','dimensions_m':[bb[1][i]-bb[0][i] for i in range(3)],'bounds_m':bb,'materials':mats,'triangles':sum(len(f.vertices)-2 for o in objects for f in o.data.polygons),'parts':[{'name':o.name,'pivot_m':list(o.location),'triangles':sum(len(f.vertices)-2 for f in o.data.polygons)} for o in objects],'frozen':False,'status':'V2 render review pending; no gameplay, transactions or rewards'}
    report['uv_validation']=uv_validation
    if split:
        prizes=[o for o in objects if 'Prize' in o.name]
        report['prize_grounding']=[{'name':o.name,'min_z_m':bounds([o])[0][2],'bed_z_m':.865} for o in prizes]
    bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
    for im in bpy.data.images:
        if im.source=='FILE':im.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(target/(name+'.blend')))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(target/(name+'.glb')),export_format='GLB',use_selection=True)
    bpy.ops.export_scene.fbx(filepath=str(target/(name+'_parts.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
    batches=[('Static',[o for o in objects if 'Glass' not in o.name]),('Glass',[o for o in objects if 'Glass' in o.name])] if split else [('Body',objects)]
    report['fbx_parts']=[]
    for label,batch in batches:
        bpy.ops.object.select_all(action='DESELECT')
        for o in batch:o.select_set(True)
        bpy.context.view_layer.objects.active=batch[0];bpy.ops.object.join();o=bpy.context.object;o.name='SM_'+name+'_'+label
        bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        path=target/(name+('_'+label.lower() if split else '')+'.fbx')
        bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
        bb2=bounds([o]);report['fbx_parts'].append({'name':label,'fbx_path':str(path),'bounds_m':bb2,'dimensions_m':[bb2[1][i]-bb2[0][i] for i in range(3)],'collision':'none' if label=='Glass' else 'box'})
    if not split:report['fbx_path']=report['fbx_parts'][0]['fbx_path']
    (target/'asset.json').write_text(json.dumps(report,indent=2))
    render(name,height)
    print(json.dumps({'name':name,'triangles':report['triangles'],'dimensions_m':report['dimensions_m'],'parts':len(objects),'status':'review pending'}))


def render(name,height):
    require_unfrozen(name)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED';scene.render.threads=8
    scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Neutral local studio');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.105,.12,.145,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.42
    floor=mat('V2_PreviewFloor',color=(.08,.085,.095,1),metal=0,rough=.67)
    cube('PreviewGround',(0,0,-.045),(200,200,.08),floor,0)
    for label,pos,power,shape,sizex,sizey,color in [('Key',(-2.6,-3.0,3.6),590,'RECTANGLE',2.5,3.5,(1,.94,.84)),('Fill',(3,-2,2.7),460,'RECTANGLE',1.3,2.7,(.76,.85,1)),('Rim',(1,2.2,3.3),650,'RECTANGLE',1.2,2.4,(.83,.88,1))]:
        bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=label;o.data.energy=power;o.data.shape=shape;o.data.size=sizex;o.data.size_y=sizey;o.data.color=color
        o.rotation_euler=(Vector((0,0,height*.55))-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO'
    views=[('front',(0,-5,height*.85),(0,0,height*.49),height*1.18),('quarter',(3,-5,height*1.18),(0,0,height*.49),height*1.19)]
    if name=='CreditExchangeV2':views.append(('detail',(1.8,-4,2.4),(0,-.10,1.265),1.17))
    else:views.append(('detail',(1.0,-4,1.96),(0,0,1.185),1.20))
    for label,pos,target,scale in views:
        cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
        scene.render.filepath=str(OUT/name/(name+'_'+label+'.png'));bpy.ops.render.render(write_still=True)


if __name__=='__main__':
    requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if not requested or 'CreditExchangeV2' in requested:credit()
    if not requested or 'RiftSalvageV2' in requested:crane()
