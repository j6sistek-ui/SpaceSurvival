"""Mounted native Genesis architectural fixtures for the rear outpost.

Call build_lighting(globals()) after OutpostSkyline has been placed. This does
not change exposure, fog, ambient light or playable geometry. Hardware stays
at native scale and its three parts preserve their shared source pivot.
"""
import json
import math
import os
from pathlib import Path


PARTS = (
    "SM_CornerWallCeiling400X70_V6_Lights_Part1",
    "SM_CornerWallCeiling400X70_V6V7V8_Lights_Part2",
    "SM_CornerWallCeiling400X70_V6V7V8_Lights_Part3",
)
MARKER = "OutpostSkylineFixture"
COLORS = {"Cyan": (.30, .72, 1.0), "Amber": (1.0, .55, .25)}


def rotate(v, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return [v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2]]


def bounds(row):
    sx, sy, sz = row['size']
    c, s = abs(math.cos(math.radians(row['yaw']))), abs(math.sin(math.radians(row['yaw'])))
    ext = ((sx*c+sy*s)/2, (sx*s+sy*c)/2, sz/2)
    return [row['center'][i]-ext[i] for i in range(3)] + [row['center'][i]+ext[i] for i in range(3)]


def layout(catalog):
    import OutpostSkyline
    architecture = OutpostSkyline.build(catalog)
    meshes = catalog['meshes']
    parts = []
    for name in PARTS:
        found = [m for m in meshes if m['name']==name and '/P4_Genesis_Vol1/' in m['asset']]
        if len(found)!=1:raise ValueError('Missing or ambiguous skyline fixture mesh: '+name)
        parts.append(found[0])
    fixtures = []

    def mounts(prefix):
        group = [r for r in architecture if r['name'].startswith(prefix)]
        if not group:raise ValueError('Skyline fixture mounting geometry missing: '+prefix)
        bb = [bounds(r) for r in group]
        return group, [min(b[i] for b in bb) for i in range(3)] + [max(b[i+3] for b in bb) for i in range(3)]

    def add(name, surface, normal, top, color, lumens, radius, mount_rows):
        # Native +Y faces out, local X spans the wall. Its housing back plane
        # is Y=-40; putting its pivot40cm off the facade makes it touch exactly.
        yaw = math.degrees(math.atan2(normal[1],normal[0]))-90
        pivot = [surface[0]+normal[0]*40, surface[1]+normal[1]*40, top]
        components = []
        for part in parts:
            offset = rotate(part['origin'],yaw)
            components.append({'name':part['name'],'asset':part['asset'],
                'center':[pivot[i]+offset[i] for i in range(3)],
                'size':[v*2 for v in part['extent']], 'yaw':yaw})
        # Point light sits just outside the native lenses, casting a local wash
        # onto the mounting surface. No shadow maps and no atmospheric effects.
        offset=rotate((0,60,-6),yaw)
        fixtures.append({'name':'SkylineLighting/'+name,'pivot':pivot,'yaw':yaw,
            'normal':list(normal),'surface':list(surface),'color':color,'lumens':lumens,
            'radius':radius,'light_position':[pivot[i]+offset[i] for i in range(3)],
            'parts':components,'mount_rows':[r['name'] for r in mount_rows]})

    for index,(y,height) in enumerate(((-4800,2200),(-2800,3200),(3000,3800),(5100,2600)),1):
        levels=math.ceil((height-200-515)/400)
        for tier,level in enumerate((0,(levels-1)//2,levels-1)):
            group,b=mounts(f'Skyline/Tower {index}/Storey cornice_{level}_')
            add(f'Tower {index}/Storey {level}',(b[0],y),( -1,0),b[5]-5,
                'Amber' if tier==2 else 'Cyan',1000 if tier==2 else 1300,950,group)

    for face in (5,6,7):
        group,b=mounts(f'Skyline/Command drum Upper/{face}/Header')
        row=group[0]; angle=math.radians(face*30); normal=(math.cos(angle),math.sin(angle))
        surface=[row['center'][i]+normal[i]*row['size'][0]/2 for i in range(2)]
        add('Command drum/Header '+str(face),surface,normal,min(b[5]-5,1760),
            'Amber',1100,850,group)

    group,b=mounts('Skyline/Upper gallery front cornice_')
    for y in (-3800,-1600,1600,4100):
        add('Upper gallery/'+str(y),(b[0],y),(-1,0),b[5]-5,'Cyan',800,800,group)

    for name,side in (('Engineering',-1),('Lounge',1)):
        group,b=mounts('Skyline/'+name+' bridge edge '+str(side)+'_')
        surface_y=b[1] if side<0 else b[4]
        for x in (6500,8600):
            add(name+' service bridge/'+str(x),(x,surface_y),(0,side),b[5]-5,
                'Amber',650,650,group)
    return fixtures


def audit(fixtures):
    errors=[]
    gallery=[2900,-4400,520,4300,-2400,1100]
    for f in fixtures:
        housing=f['parts'][0]
        # The rear mounting plane of the native housing touches the real
        # cornice/header. Other parts retain their shared-pivot offsets.
        back=rotate((0,-40,0),f['yaw'])
        back_world=[f['pivot'][i]+back[i] for i in range(2)]
        if max(abs(back_world[i]-f['surface'][i]) for i in range(2))>.001:
            errors.append(f['name']+': housing not on mounting plane')
        for row in f['parts']:
            b=bounds(row)
            if all(b[i]<gallery[i+3] and b[i+3]>gallery[i] for i in range(3)):
                errors.append(f['name']+': intersects playable observation gallery')
        if not 0<f['lumens']<=1300 or not 0<f['radius']<=950:
            errors.append(f['name']+': local light budget exceeded')
    return {'geometry_only':True,'fixtures':len(fixtures),'native_mesh_parts':sum(len(f['parts']) for f in fixtures),
            'lights':len(fixtures),'shadow_casting_lights':0,'uniform_native_scale':1,
            'total_lumens':sum(f['lumens'] for f in fixtures),'violations':errors}


def build_lighting(api):
    u,eas=api['u'],api['EAS']
    root=Path(api['ROOT'])
    catalog=json.loads(Path(os.environ.get('SS_PREFAB_CATALOG',str(root/'Artifacts/PrefabLibrary/catalog.json'))).read_text(encoding='utf-8'))
    fixtures=layout(catalog); evidence=audit(fixtures)
    if evidence['violations']:raise ValueError('; '.join(evidence['violations']))
    # Only this helper's explicitly tagged fixtures are replaced on a repeat.
    for actor in eas.get_all_level_actors():
        if MARKER in [str(t) for t in actor.tags]:
            if not eas.destroy_actor(actor):raise RuntimeError('Cannot replace old skyline fixture')
    lenses={name:api['material']('M_OutpostSkylineLens'+name,color,emission=2.0)
            for name,color in COLORS.items()}
    for f in fixtures:
        housing=None
        for index,row in enumerate(f['parts']):
            actor=api['place'](f['name']+'/Part '+str(index+1),row['asset'],row['center'],
                               size=row['size'],yaw=row['yaw'],solid=False,
                               material=lenses[f['color']] if index==2 else None)
            api['tag'](actor,MARKER);api['tag'](actor,'OutpostRole:SkylineMountedFixture')
            if index==0:housing=actor
        light=api['light'](f['name']+'/Local wash',f['light_position'],COLORS[f['color']],
                           power=f['lumens'],radius=f['radius'],shadow=False)
        api['tag'](light,MARKER)
        if not light.attach_to_component(housing.static_mesh_component,u.Name(''),
                u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False):
            raise RuntimeError('Cannot attach architectural light to native housing')
    result={'audit':evidence,'fixtures':fixtures,
            'scope':'Mounted local architectural fixtures only. No exposure, fog, ambient or collision changes.'}
    (Path(api['OUT'])/'skyline-lighting.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
