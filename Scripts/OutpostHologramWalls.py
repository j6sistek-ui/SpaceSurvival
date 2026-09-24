"""Large native Genesis graphic walls and two mounted arrival billboards.

Six existing architectural panes gain the matched native digital-pane mesh,
with identical bounds/pivot and untouched structural collision. Two complete
4x2m frame/glass assemblies sit on native gantry brackets, leaving the centre
sightline open. Native image/animation layers are inherited by private material
instances; no generic flat graphic, global lighting, planet or character edit.
Interior walls use a separate cyan-blue color derivative; arrival billboards
retain native advertisement colors. Black animation states remain black.
"""
import hashlib
import itertools
import json
import math
import os
from pathlib import Path

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
PREFIX = 'HologramWalls/'
TAG = 'OutpostHologramWalls'
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/'
P5 = '/Game/P1toP5_Bundle/P5_FruitSeller/'
PRIVATE = '/Game/OutpostSandbox/Materials/'
WINDOWS = (
    ('Engineering/Bay N1', [3457.142857142857,-2300.,0.], -90., .9285714285714286, 'RobotAdvertisment'),
    ('Engineering/Bay W4', [2900.,-2850.,0.], 0., .9166666666666667, 'RobotAdvertisment'),
    ('Lounge/Bay S1', [3457.142857142857,2300.,0.], 90., .9285714285714286, 'KeosAdvertisment'),
    ('Lounge/Bay W1', [2900.,2850.,0.], 0., .9166666666666667, 'RobotAdvertisment'),
    ('Operations/Bay W1', [6400.,-742.8571428571429,0.], 0., .9285714285714286, 'RobotAdvertisment'),
    ('Operations/Bay N4', [8200.,1300.,0.], -90., 1., 'RobotAdvertisment'),
)
# Capture20260924T194040: DigitalPanel was practically empty in both32/34;
# 33 shows full Robot/Keos imagery on the SAME400x250 pane geometry, so the
# correction is restricted to native graphic selection, not replacement UVs,
# geometry, backface flags or another global exposure adjustment.
STYLES = ('RobotAdvertisment', 'KeosAdvertisment')
# Common gain, not per-channel compression. The original graph supplies all
# texture UVs, scrolling, layered animation, masks and native blue colours.
COMMON_GAIN = 8.
MASTER = P4+'Materials/Masters/MM_MasterMaterial02_Translucent.MM_MasterMaterial02_Translucent'


def asset(pack, folder, name):
    return pack + folder + '/' + name + '.' + name


def rotate(v, yaw):
    a = math.radians(yaw)
    return [math.cos(a)*v[0]-math.sin(a)*v[1], math.sin(a)*v[0]+math.cos(a)*v[1], v[2]]


def transformed(mesh, position, yaw, scale):
    corners = [rotate([(mesh['origin'][i]+mesh['extent'][i]*s[i])*scale[i]
                       for i in range(3)], yaw) for s in itertools.product((-1,1), repeat=3)]
    return [position[i]+min(c[i] for c in corners) for i in range(3)] + \
           [position[i]+max(c[i] for c in corners) for i in range(3)]


def layout(catalog):
    import OutpostPromenadeDetails
    meshes = {m['asset']:m for m in catalog['meshes']}
    old = asset(P4,'Meshes','SM_Window400X250_V1_Part2')
    digital = asset(P4,'Meshes','SM_Window400X250_V2_Part2_DigitalWindow')
    frame = asset(P4,'Meshes','SM_Window400X250_V1_Part1')
    plan = {'windows':[], 'billboards':[], 'parts':[]}
    for name, position, yaw, width, style in WINDOWS:
        scale = [1.,width,1.6]
        original = digital if name.startswith('Operations/') else old
        mesh = meshes[digital]
        if max(abs(a-b) for field in ('origin','extent')
               for a,b in zip(meshes[original][field],mesh[field])) > .01:
            raise ValueError('Native architectural pane alternatives are not identical in bounds')
        plan['windows'].append({'name':name+'/Glass', 'frame':name+'/Frame',
            'original_mesh':original, 'mesh':digital, 'frame_mesh':frame,
            'position':position, 'yaw':yaw, 'scale':scale, 'style':style,
            'bounds':transformed(mesh,position,yaw,scale),
            'frame_bounds':transformed(meshes[frame],position,yaw,scale),
            'native_origin':mesh['origin'], 'native_extent':mesh['extent']})
    promenade = {r['name']:r for r in OutpostPromenadeDetails.layout(catalog)}
    frame = meshes[asset(P4,'Meshes','SM_Window400X200_V2_Part1')]
    pane = meshes[asset(P4,'Meshes','SM_Window400X200_V2_Part2_DigitalWindow')]
    arm = meshes[asset(P5,'Meshes','SM_Building_StructureLink90x10_V1')]

    def part(group, suffix, mesh, position, yaw, style=None):
        row = {'name':PREFIX+group+'/'+suffix, 'asset':mesh['asset'], 'position':list(position),
            'yaw':yaw, 'scale':[1.,1.,1.], 'style':style,
            'bounds':transformed(mesh,position,yaw,[1.,1.,1.]),
            'native_origin':mesh['origin'], 'native_extent':mesh['extent']}
        plan['parts'].append(row)
        return row

    for side, style, index in ((-1,'RobotAdvertisment',0),(1,'KeosAdvertisment',3)):
        name = 'Arrival '+('South' if side<0 else 'North')
        mount = promenade['PromenadeKit/Arrivals gantry/Connected cable cornice '+str(index)]
        mount_bounds = mount['bounds']
        bottom = mount_bounds[5]+2*arm['extent'][2]-.4
        # Native frame rear plane contacts the cornice front. Its lower frame
        # rests on two horizontal owned metal brackets seated on that cornice.
        center = [mount_bounds[0]-frame['extent'][0]+.3,side*540.,bottom+frame['extent'][2]]
        offset = rotate(frame['origin'],180.)
        pivot = [center[i]-offset[i] for i in range(3)]
        front = part(name,'Frame',frame,pivot,180.)
        glass = part(name,'Native animated graphics',pane,pivot,180.,style)
        supports = []
        for number, y in enumerate((side*540.-110,side*540.+110),1):
            c = [1610.,y,mount_bounds[5]+arm['extent'][2]]
            pos = [c[i]-arm['origin'][i] for i in range(3)]
            supports.append(part(name,'Native support '+str(number),arm,pos,0.))
        plan['billboards'].append({'name':name,'style':style,'front_normal':[-1,0,0],
            'mount_name':mount['name'],'mount_asset':mount['asset'],'mount_bounds':mount_bounds,
            'frame':front['name'],'glass':glass['name'],'support_names':[s['name'] for s in supports],
            'source_assembly':'P4 Genesis native400X200 V2 frame/glass shared pivot; P5 native bracket'})
    return plan


def audit(plan):
    failures=[]
    parts={p['name']:p for p in plan['parts']}
    for row in plan['windows']:
        b,f=row['bounds'],row['frame_bounds']
        if any(b[i]<f[i]-.05 or b[i+3]>f[i+3]+.05 for i in range(3)):
            failures.append(row['name']+': pane escapes its existing frame')
        if (b[5]-b[2])<350 or max(b[3]-b[0],b[4]-b[1])<340:
            failures.append(row['name']+': architectural display unexpectedly small')
    for group in plan['billboards']:
        frame=parts[group['frame']]['bounds'];glass=parts[group['glass']]['bounds']
        if frame[2]<490 or frame[5]>710 or frame[1]<320<frame[4] or frame[1]<-320<frame[4]:
            failures.append(group['name']+': entry/planet sightline or height changed')
        for name in group['support_names']:
            b=parts[name]['bounds'];m=group['mount_bounds']
            if abs(b[2]-m[5])>.01 or not (b[0]<m[3] and b[3]>m[0] and b[1]<m[4] and b[4]>m[1]):
                failures.append(name+': bracket detached from real cornice')
            if abs(frame[2]-b[5]+.4)>.01 or not (b[0]<frame[3] and b[3]>frame[0]):
                failures.append(name+': billboard frame not supported')
        if any(glass[i]<frame[i]-.05 or glass[i+3]>frame[i+3]+.05 for i in range(3)):
            failures.append(group['name']+': native pane outside shared frame')
    return {'full_height_graphic_walls':len(plan['windows']), 'large_billboards':len(plan['billboards']),
        'new_native_parts':len(plan['parts']), 'new_lights':0, 'new_collision':0,
        'existing_structural_collision_unchanged':True,'failures':failures}


def _xyz(v):
    return [float(v.x),float(v.y),float(v.z)]


def _bounds(actor):
    from OutpostGeometryUtils import mesh_union
    c,e=mesh_union(actor)
    return [c.x-e.x,c.y-e.y,c.z-e.z,c.x+e.x,c.y+e.y,c.z+e.z]


def _close(actual,expected,label,tolerance=.2):
    if len(actual)!=len(expected) or max(abs(a-b) for a,b in zip(actual,expected))>tolerance:
        raise RuntimeError(label+' observed='+repr(actual)+' expected='+repr(expected))


def _pose(actor,component):
    t=actor.get_actor_transform();q=t.rotation
    return [_xyz(t.translation),[float(q.x),float(q.y),float(q.z),float(q.w)],_xyz(t.scale3d),
            str(component.get_collision_enabled()),str(component.get_collision_profile_name())]


def _materials(api):
    """Private source-relative copies; native UV, image and animation inherited."""
    u,edit,lib=api['u'],api['EDIT'],api['LIB']
    result,receipt={},{}
    for style in STYLES:
        path=asset(P4,'Materials/Instances/Translucent','MI_DigitalGlass_Window400X200_'+style)
        source=api['load'](path)
        if not isinstance(source,u.MaterialInstanceConstant):raise RuntimeError('Missing native graphic instance')
        parent=source.get_editor_property('parent')
        if not parent or parent.get_path_name()!=MASTER:raise RuntimeError('Native translucent graphic master changed')
        filename=Path(api['ROOT'])/('Content/'+path.split('.')[0][len('/Game/'):]+'.uasset')
        digest=hashlib.sha256(filename.read_bytes()).hexdigest()
        scalar_names=[str(k) for k in edit.get_scalar_parameter_names(source)]
        channel_names=['Intensity EM'+str(i) for i in (1,2,3)]
        if not set(channel_names)<=set(scalar_names):raise RuntimeError('Native graphic emissive interface changed')
        scalars={k:float(edit.get_material_instance_scalar_parameter_value(source,k)) for k in scalar_names}
        textures={str(k):edit.get_material_instance_texture_parameter_value(source,k) for k in edit.get_texture_parameter_names(source)}
        colors={str(k):edit.get_material_instance_vector_parameter_value(source,k) for k in edit.get_vector_parameter_names(source)}
        switches={str(k):bool(edit.get_material_instance_static_switch_parameter_value(source,k))
                  for k in edit.get_static_switch_parameter_names(source)}
        if any('Cov1' in k for k in switches):raise RuntimeError('Unexpected coverage layer on native translucent graphic')
        if abs(scalars.get('Opacity',0)-.6)>.0001 or abs(scalars.get('Opacity_Lerp',0)-.6)>.0001:
            raise RuntimeError('Native translucent opacity interface differs from inspected source')
        if any(not math.isfinite(v) for v in scalars.values()):raise RuntimeError('Nonfinite native pane parameter')
        name='MI_HologramWall_'+style;dest=PRIVATE+name
        child=api['load'](dest) if lib.does_asset_exist(dest) else api['TOOLS'].create_asset(
            name,PRIVATE.rstrip('/'),u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        if not isinstance(child,u.MaterialInstanceConstant):raise RuntimeError('Private graphic path has wrong class')
        edit.set_material_instance_parent(child,source)
        for k in channel_names:edit.set_material_instance_scalar_parameter_value(child,k,scalars[k]*COMMON_GAIN)
        for k,v in scalars.items():
            expected=v*COMMON_GAIN if k in channel_names else v
            actual=float(edit.get_material_instance_scalar_parameter_value(child,k))
            if abs(actual-expected)>max(.0001,abs(expected)*.0001):raise RuntimeError('Graphic scalar readback: '+k)
        for k,v in textures.items():
            if edit.get_material_instance_texture_parameter_value(child,k)!=v:raise RuntimeError('Graphic native UV/image texture override: '+k)
        for k,v in colors.items():
            actual=edit.get_material_instance_vector_parameter_value(child,k)
            _close([getattr(actual,c) for c in 'rgba'],[getattr(v,c) for c in 'rgba'],k,.0001)
        for k,v in switches.items():
            if bool(edit.get_material_instance_static_switch_parameter_value(child,k))!=v:
                raise RuntimeError('Native graphic animation/wrap switch changed: '+k)
        edit.update_material_instance(child)
        if not lib.save_loaded_asset(child):raise RuntimeError('Failed to save private large graphic instance')
        if hashlib.sha256(filename.read_bytes()).hexdigest()!=digest:raise RuntimeError('Native graphic source changed')
        result[style]=child
        receipt[style]={'source':path,'private':child.get_path_name(),'source_sha256':digest,
            'common_emission_gain':COMMON_GAIN,'native_scalars':scalars,
            'native_textures':{k:v.get_path_name() if v else None for k,v in textures.items()},
            'native_colors':{k:[float(getattr(v,c)) for c in 'rgba'] for k,v in colors.items()},
            'native_switches':switches,
            'opacity_route':'Native .6 opacity/Fresnel interpolation followed by roughness-mask interpolation toward opaque; unchanged. No Cov1 interface.',
            'native_image_uv_animation_and_colors_preserved':True}
    return result,receipt


def blue_color(values):
    """Retain channel peak/alpha and animated black while selecting blue hue."""
    if len(values)!=4 or any(not math.isfinite(v) for v in values):
        raise ValueError('Invalid native graphic color')
    peak=max(values[:3])
    return [peak*.06,peak*.5,peak,values[3]] if peak>0 else list(values)


def _blue_wall_materials(api,parents):
    u,edit,lib=api['u'],api['EDIT'],api['LIB']
    required={'Color '+str(c)+' EM'+str(e) for c in (1,2) for e in (1,2,3)}
    result,receipt={},{}
    for style,parent in parents.items():
        source={str(k):edit.get_material_instance_vector_parameter_value(parent,k)
                for k in edit.get_vector_parameter_names(parent)}
        if not required<=source.keys():raise RuntimeError('Missing six native graphic color controls')
        name='MI_HologramWallBlue_'+style;dest=PRIVATE+name
        child=api['load'](dest) if lib.does_asset_exist(dest) else api['TOOLS'].create_asset(
            name,PRIVATE.rstrip('/'),u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        if not isinstance(child,u.MaterialInstanceConstant):raise RuntimeError('Private blue wall path has wrong class')
        edit.set_material_instance_parent(child,parent)
        expected={k:blue_color([float(getattr(v,c)) for c in 'rgba']) for k,v in source.items() if k in required}
        for k,v in expected.items():edit.set_material_instance_vector_parameter_value(child,k,u.LinearColor(*v))
        for k,v in source.items():
            before=[float(getattr(v,c)) for c in 'rgba']
            after=edit.get_material_instance_vector_parameter_value(child,k)
            _close([float(getattr(after,c)) for c in 'rgba'],expected.get(k,before),k,.0001)
            unchanged=edit.get_material_instance_vector_parameter_value(parent,k)
            _close([float(getattr(unchanged,c)) for c in 'rgba'],before,'Parent color '+k,.0001)
        for names,getter in ((edit.get_scalar_parameter_names,edit.get_material_instance_scalar_parameter_value),
                             (edit.get_texture_parameter_names,edit.get_material_instance_texture_parameter_value),
                             (edit.get_static_switch_parameter_names,edit.get_material_instance_static_switch_parameter_value)):
            for k in names(parent):
                if getter(child,k)!=getter(parent,k):raise RuntimeError('Blue wall changed inherited native image/animation parameter: '+str(k))
        edit.update_material_instance(child)
        if not lib.save_loaded_asset(child):raise RuntimeError('Failed to save private blue wall material')
        result[style]=child
        receipt[style]={'parent':parent.get_path_name(),'private':child.get_path_name(),
            'native_colors':{k:[float(getattr(v,c)) for c in 'rgba'] for k,v in source.items()},
            'blue_colors':expected,'black_states_preserved':True,
            'image_uv_animation_scalar_and_switches_inherited_unchanged':True,
            'billboard_material_unchanged':True}
    return result,receipt


def apply(api):
    """After room, promenade and finish passes. Caller owns save and render."""
    u,eas=api['u'],api['EAS']
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package=world.get_path_name().split('.')[0]
    if package!=TARGET and not (package.startswith('/Temp/Untitled') and api.get('TARGET')==TARGET):
        raise RuntimeError('Large hologram walls require the private outpost')
    catalog=json.loads(Path(os.environ.get('SS_PREFAB_CATALOG',str(Path(api['ROOT'])/'Artifacts/PrefabLibrary/catalog.json'))).read_text(encoding='utf-8'))
    plan=layout(catalog);checks=audit(plan)
    if checks['failures']:raise RuntimeError('; '.join(checks['failures']))
    actors={}
    for actor in eas.get_all_level_actors():actors.setdefault(actor.get_actor_label(),[]).append(actor)
    def one(name):
        found=actors.get(name,[])
        if len(found)!=1 or 'OutpostAuthored' not in map(str,found[0].tags):raise RuntimeError('Missing/duplicate/unowned large display anchor: '+name)
        return found[0]
    prepared=[]
    for row in plan['windows']:
        actor,frame=one(row['name']),one(row['frame'])
        c=actor.get_component_by_class(u.StaticMeshComponent)
        f=frame.get_component_by_class(u.StaticMeshComponent)
        if not c or c.static_mesh.get_path_name() not in (row['original_mesh'],row['mesh']) or not f or f.static_mesh.get_path_name()!=row['frame_mesh']:
            raise RuntimeError('Architectural pane/frame differs from exact native pair')
        _close(_bounds(actor),row['bounds'],row['name'])
        _close(_bounds(frame),row['frame_bounds'],row['frame'])
        mesh=api['load'](row['mesh']);b=mesh.get_bounds()
        _close(_xyz(b.origin)+_xyz(b.box_extent),row['native_origin']+row['native_extent'],row['mesh'])
        prepared.append((row,actor,c,mesh,_pose(actor,c),[m.get_path_name() if m else None for m in c.get_materials()]))
    for group in plan['billboards']:
        actor=one(group['mount_name']);c=actor.get_component_by_class(u.StaticMeshComponent)
        if not c or c.static_mesh.get_path_name()!=group['mount_asset']:raise RuntimeError('Billboard cornice mesh changed')
        _close(_bounds(actor),group['mount_bounds'],group['mount_name'])
    expected={r['name'] for r in plan['parts']}
    for name,found in actors.items():
        if name.startswith(PREFIX) and (name not in expected or len(found)!=1 or TAG not in map(str,found[0].tags)):
            raise RuntimeError('Foreign or duplicate large billboard actor: '+name)
    for row in plan['parts']:
        mesh=api['load'](row['asset']);b=mesh.get_bounds()
        _close(_xyz(b.origin)+_xyz(b.box_extent),row['native_origin']+row['native_extent'],row['asset'])
    materials,material_receipt=_materials(api)
    wall_materials,wall_color_receipt=_blue_wall_materials(api,materials)
    windows=[]
    for row,actor,c,mesh,pose,before in prepared:
        prior=c.static_mesh.get_path_name()
        c.set_static_mesh(mesh)
        for slot in range(c.get_num_materials()):c.set_material(slot,wall_materials[row['style']])
        if _pose(actor,c)!=pose:raise RuntimeError('Pane transform/collision changed')
        _close(_bounds(actor),row['bounds'],row['name'])
        windows.append(dict(row,previous_mesh=prior,previous_materials=before,
            assigned_slots=c.get_num_materials(),assigned_material=wall_materials[row['style']].get_path_name(),
            collision_and_pose_unchanged=True))
    placements=[]
    for row in plan['parts']:
        found=actors.get(row['name'],[])
        if found:eas.destroy_actor(found[0])
        actor=api['raw'](row['name'],row['asset'],row['position'],yaw=row['yaw'],scale=row['scale'],solid=False)
        actor.tags=list(actor.tags)+[u.Name(TAG)]
        c=actor.get_component_by_class(u.StaticMeshComponent);c.set_cast_shadow(False)
        if row['style']:
            for slot in range(c.get_num_materials()):c.set_material(slot,materials[row['style']])
        _close(_bounds(actor),row['bounds'],row['name'])
        placements.append(dict(row,actual_bounds=_bounds(actor)))
    receipt={'map':TARGET,'audit':checks,'large_wall_panes':windows,'billboards':plan['billboards'],
        'placements':placements,'materials':material_receipt,'wall_blue_derivatives':wall_color_receipt,'map_saved':False,
        'planet_character_holograms_and_global_lighting_unchanged':True,
        'native_vendor_assets_unchanged':True,
        'validation':'Native bounds, source/parameter and collision guards only; visible large blue graphics require matched native captures.'}
    (Path(api['OUT'])/'hologram-walls.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    return receipt
