"""Mounted atrium services: native ribs, cable trays and framed information screens.

All additions stay at the wall or above4.8m; the globe, seven terminals, walking
routes and sensor doors retain their clearances. No source assets are modified.
"""
import json
import math

PREFIX = 'AtriumDetail/'
TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/'
P5 = '/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/'
SCREEN = P5+'SM_Props_ConstructionPart133_Screen'
SCREEN_NATIVE_SIZE = (170.01417589187622,5.1195549964904785,70.00015187263489)
INFORMATION = (
    ('OPERATIONS','TRADE / CONTRACT PREVIEWS'),
    ('CREW ARCHIVE','LOUNGE / WARDROBE PREVIEW'),
    ('SURVIVAL DEPARTURES','START / CONTINUE AT HUB'),
    ('MARKET','LOCAL VENDORS / SERVICES'),
    ('BERTHS','SHIP FINISH / FREE FLIGHT'),
    ('OBSERVATION','UPPER GLASS GALLERY'),
    ('ENGINEERING','FLIGHT UPGRADE PREVIEW'),
    ('WAYFARER EXCHANGE','WELCOME / INFORMATION'),
)


def layout():
    rows = []
    def add(name, asset, radius, angle, z, size, yaw_offset=0):
        a = math.radians(angle)
        rows.append(dict(name=PREFIX+name, asset=asset+'.'+asset.rsplit('/',1)[-1],
            center=[4200+radius*math.cos(a),radius*math.sin(a),z],
            size=list(size),yaw=angle+yaw_offset))
    for i in range(24):
        angle=7.5+i*15
        add(f'Overhead service bay {i+1:02}/Cable tray',
            P4+'SM_CornerWallCeiling400X70_V2_ElectricalCableRouting',
            1270,angle,642,(320,70,60),90)
        for side in (-1,1):
            add(f'Overhead service bay {i+1:02}/Roof tie {side}',
                P5+'SM_Props_ConstructionPart119',1270,angle+side*6.4,682,(10,10,76))
    for i in range(8):
        angle=22.5+i*45
        # Native wall_main spans radial1532.8..1590 at Z430..630.
        # This crown overlaps it by12.2cm, rather than floating38cm in front.
        add(f'Wall service {i+1:02}/Equipment crown',
            P4+'SM_CornerWallCeiling200X70_V4_ElectricalEquipment',
            1510,angle,632,(200,70,60),90)
        for side in (-1,1):
            # Six110cm sections overlap2cm. Native120cm cable detail remains
            # near its intended proportions instead of stretching one pole650cm.
            for segment in range(6):
                add(f'Wall service {i+1:02}/Vertical feed {side}/Section {segment+1}',
                    P5+'SM_Props_ConstructionPart119',1530,angle+side*3.3,
                    55+segment*108,(14,14,110))
            # Hangers touch the screen back and crown underside; local tangent
            # ±84cm lies inside both the200cm crown and238cm screen frame.
            add(f'Wall service {i+1:02}/Screen hanger {side}',
                P5+'SM_Props_ConstructionPart119',1500,angle+side*3.2,590,(14,14,50))
        add(f'Wall service {i+1:02}/Information screen', SCREEN,
            1490,angle,534,[v*1.4 for v in SCREEN_NATIVE_SIZE],90)
        rows[-1]['screen_index']=i
    return rows


def bounds(row):
    a=math.radians(row['yaw']);sx,sy,sz=row['size'];x,y,z=row['center']
    ex=(abs(math.cos(a))*sx+abs(math.sin(a))*sy)/2
    ey=(abs(math.sin(a))*sx+abs(math.cos(a))*sy)/2
    return [x-ex,y-ey,z-sz/2,x+ex,y+ey,z+sz/2]


def _touch(a,b):
    return all(a[i]<=b[i+3]+.1 and b[i]<=a[i+3]+.1 for i in range(3))


def audit(rows):
    """Conservative source layout checks; native geometry is checked in build."""
    by_name={row['name']:row for row in rows};failures=[]
    for row in rows:
        x,y,z=row['center'];sx,sy,sz=row['size'];radial=math.hypot(x-4200,y)
        if z-sz/2<300 and not ('Vertical feed' in row['name'] and radial>=1529):
            failures.append(row['name']+': circulation intrusion')
        # Radius650 globe,730cm oculus,1040cm information pedestals. Below-head
        # services hug the1530cm wall line; overhead hardware starts above480cm.
        if radial-math.hypot(sx,sy)/2<1060:
            failures.append(row['name']+': central display/globe clearance')
        if max(sx,sy,sz)<=0:
            failures.append(row['name']+': invalid dimensions')
    for i in range(8):
        stem=PREFIX+f'Wall service {i+1:02}/'
        crown=bounds(by_name[stem+'Equipment crown'])
        screen=bounds(by_name[stem+'Information screen'])
        for side in (-1,1):
            hanger=bounds(by_name[stem+f'Screen hanger {side}'])
            if not _touch(crown,hanger) or not _touch(screen,hanger):
                failures.append(stem+': detached screen hanger')
            feeds=[bounds(by_name[stem+f'Vertical feed {side}/Section {j+1}']) for j in range(6)]
            if abs(feeds[0][2])>.1 or not _touch(feeds[-1],crown):
                failures.append(stem+': unsupported wall feed')
            if any(not _touch(a,b) for a,b in zip(feeds,feeds[1:])):
                failures.append(stem+': gapped wall feed')
    for i in range(24):
        stem=PREFIX+f'Overhead service bay {i+1:02}/'
        tray=bounds(by_name[stem+'Cable tray'])
        for side in (-1,1):
            tie=bounds(by_name[stem+f'Roof tie {side}'])
            if not _touch(tray,tie) or tie[5]<670:
                failures.append(stem+': unsupported overhead tray')
    if failures:
        raise RuntimeError('Atrium detail geometry: '+ '; '.join(failures))
    return {'source_geometry_only':True,'parts':len(rows),'connected_screen_groups':8,
            'grounded_segmented_feeds':16,'roof_supported_trays':24,
            'central_radial_clearance_min_cm':min(math.hypot(r['center'][0]-4200,r['center'][1])-math.hypot(*r['size'][:2])/2 for r in rows)}


def build(api):
    u=api['u']
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package=world.get_path_name().split('.')[0]
    if package != TARGET and not (package.startswith('/Temp/Untitled') and api.get('TARGET')==TARGET):
        raise RuntimeError('Atrium detail may only modify the private outpost')
    rows=layout();geometry=audit(rows)
    meshes={asset:api['load'](asset) for asset in {r['asset'] for r in rows}}
    if any(not isinstance(m,u.StaticMesh) for m in meshes.values()):
        raise RuntimeError('A measured atrium detail source mesh is missing')
    screen=meshes[SCREEN+'.'+SCREEN.rsplit('/',1)[-1]]
    dimensions=[2*getattr(screen.get_bounds().box_extent,axis) for axis in ('x','y','z')]
    if max(abs(a-b) for a,b in zip(dimensions,SCREEN_NATIVE_SIZE))>.2:
        raise RuntimeError('Native information screen dimensions changed')
    if len(screen.get_editor_property('static_materials'))!=5:
        raise RuntimeError('Native information screen material slots changed')
    image=screen.get_material(4)
    if image is None or not image.get_name().endswith('_Screen'):
        raise RuntimeError('Native information screen image slot changed')
    face=api['material']('M_AtriumInformationSurface',(.008,.032,.05),emission=1.0)
    for actor in list(api['EAS'].get_all_level_actors()):
        if actor.get_actor_label().startswith(PREFIX):api['EAS'].destroy_actor(actor)
    from OutpostGeometryUtils import mesh_union
    actual=[]
    for row in rows:
        actor=api['place'](row['name'],row['asset'],row['center'],size=row['size'],yaw=row['yaw'],solid=False)
        api['tag'](actor,'OutpostRole:MountedAtriumDetail')
        center,extent=mesh_union(actor)
        if abs(center.z-row['center'][2])>.1 or abs(extent.z*2-row['size'][2])>.2:
            raise RuntimeError('Atrium mounted geometry transform mismatch: '+row['name'])
        if 'screen_index' in row:
            actor.static_mesh_component.set_material(4,face)
            index=row['screen_index'];angle=22.5+index*45;a=math.radians(angle)
            heading,subheading=INFORMATION[index]
            # Source glass normal is local+Y. yaw=angle+90 faces inward;
            # text normal local+X faces inward at angle+180. Both text lines
            # sit several centimetres in front of the opaque image surface.
            for suffix,words,z,size in [('Heading',heading,550,12),('Subheading',subheading,522,6.8)]:
                text_actor=api['text'](row['name']+'/'+suffix,words,
                    [4200+1474*math.cos(a),1474*math.sin(a),z],angle+180,size,(130,220,250))
                api['tag'](text_actor,'OutpostRole:MountedAtriumDetail')
        actual.append(dict(name=row['name'],min_z=center.z-extent.z,max_z=center.z+extent.z))
    receipt=dict(parts=len(rows),native_assets=len(meshes),walk_routes_changed=False,
        lower_feed_wall_radius_cm=1530,overhead_tray_bottom_cm=612,information_screens=8,
        geometry_audit=geometry,actual=actual,visual_acceptance='Pending native render review')
    (api['OUT']/'atrium-details.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    return receipt
