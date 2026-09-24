"""Eight mounted native advertising/data displays for the private outpost.

Four market fixtures preserve the complete four-part BP_ISM_Screen_V1 source
composition (frame, animated pane, cable and support), with original P5 adverts.
Two Genesis adverts face arrivals on the entrance facade; two cyan instrument
panes sit on room hatch headers. No invented text, replacement flat material,
lights, planet/character changes or new collision. Caller owns map save/render.
"""
import itertools
import json
import math
import os
from pathlib import Path

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
PREFIX = 'BlueSignage/'
TAG = 'OutpostBlueSignage'
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/'
P5 = '/Game/P1toP5_Bundle/P5_FruitSeller/'
SOURCE_MAP = '/Game/P1toP5_Bundle/P5_FruitSeller/Maps/DemoLevel_FruitSeller'
# Native actor BP_ISM_Screen_V1 in vendor-market.json. Child relative transform
# plus instance transform; all source rotations are zero, all scales are one.
MARKET_PARTS = (
    ('Frame','SM_Props_ConstructionPart124',(-50,0,-50)),
    ('Animated advertisement','SM_Props_ConstructionPart125_Screen',(-50,0,-50)),
    ('Connected cables','SM_Props_ConstructionPart126_Cables',(20,0,50)),
    ('Native support','SM_Props_ConstructionPart127_Support',(-40,0,50)),
)


def _asset(pack, folder, name):
    return pack+folder+'/'+name+'.'+name


def _rotate(point,yaw):
    a=math.radians(yaw)
    return [math.cos(a)*point[0]-math.sin(a)*point[1],
            math.sin(a)*point[0]+math.cos(a)*point[1],point[2]]


def _touch(a,b):
    return all(a[i] <= b[i+3]+.1 and b[i] <= a[i+3]+.1 for i in range(3))


def layout(catalog):
    """Pure plan derived from native bounds and existing mounted structures."""
    import OutpostPromenadeDetails,OutpostEntranceDetails
    meshes={m['asset']:m for m in catalog['meshes']}
    promenade={r['name']:r for r in OutpostPromenadeDetails.layout(catalog)}
    entrance={r['name']:r for r in OutpostEntranceDetails.layout(catalog)}
    groups=[]

    def part(group,label,mesh_path,location,yaw,scale,overrides=None):
        mesh=meshes[mesh_path]
        corners=[_rotate([(mesh['origin'][i]+mesh['extent'][i]*sign[i])*scale
                         for i in range(3)],yaw)
                 for sign in itertools.product((-1,1),repeat=3)]
        low=[location[i]+min(p[i] for p in corners) for i in range(3)]
        high=[location[i]+max(p[i] for p in corners) for i in range(3)]
        materials=list(mesh['materials'])
        for slot,value in (overrides or {}).items():materials[slot]=value
        row={'name':PREFIX+group['name']+'/'+label,'asset':mesh_path,
             'location':list(location),'yaw':yaw,'scale':[scale]*3,
             'bounds':low+high,'materials':materials,
             'native_origin':mesh['origin'],'native_extent':mesh['extent']}
        group['parts'].append(row)
        return row

    # Mount each complete source display on a real upper gantry upright.
    # Width/height stay at1.4x native; all visible parts begin above Z230.
    styles=[('Exchange gantry',-1,'FruitMarket'),('Exchange gantry',1,'FoodRobots'),
            ('Arrivals gantry',-1,'YourHealth'),('Arrivals gantry',1,'CultivatedByRobots')]
    support=meshes[_asset(P5,'Meshes','SM_Props_ConstructionPart127_Support')]
    for gantry,side,style in styles:
        name='Market/'+gantry+('/South' if side<0 else '/North')
        mount=promenade['PromenadeKit/'+gantry+'/Upright '+str(side)+'-1']
        scale,yaw=1.4,90.
        # At yaw90 native+Y faces west. Set native support back surface into
        # the actual pole by0.5cm; its authored offset also contacts the frame.
        local_back=-(support['origin'][1]-support['extent'][1])*scale
        pivot=[mount['bounds'][0]-local_back+.5,side*780.,300.]
        group={'name':name,'mount_name':mount['name'],'mount_bounds':mount['bounds'],
               'front_normal':[-1,0,0],'parts':[],'source_graphic':style,
               'provenance':'Complete BP_ISM_Screen_V1 four-part native composition; shader animation retained'}
        for label,mesh_name,offset in MARKET_PARTS:
            delta=_rotate([v*scale for v in offset],yaw)
            overrides=None
            if label=='Animated advertisement':
                material=_asset(P5,'Materials/Instances/Translucent','MI_Glass06_DropOfWater_'+style)
                overrides={0:material,1:material}
            part(group,label,_asset(P5,'Meshes',mesh_name),
                 [pivot[i]+delta[i] for i in range(3)],yaw,scale,overrides)
        group['mount_part']=group['parts'][-1]['name']
        groups.append(group)

    def framed(name,dimensions,pivot,yaw,scale,variant,mount_name,mount_bounds):
        group={'name':name,'mount_name':mount_name,'mount_bounds':mount_bounds,
               'front_normal':_rotate((1,0,0),yaw),'parts':[],
               'source_graphic':variant,
               'provenance':'Matched P4 Genesis frame/glass with native original-demo material variant'}
        for label,suffix in (('Frame','_V1_Part1'),('Animated advertisement','_V2_Part2_DigitalWindow')):
            material=_asset(P4,'Materials/Instances/Translucent','MI_DigitalGlass_Window400X200_'+variant)
            row=part(group,label,_asset(P4,'Meshes','SM_Window'+dimensions+suffix),
                     pivot,yaw,scale,{0:material,1:material} if label!='Frame' else None)
            if label=='Frame':group['mount_part']=row['name']
        groups.append(group)

    # Two full-aspect native picture/text adverts on the real entrance upper
    # facade. Their image palettes are retained; no forced blue tint is applied.
    frame=meshes[_asset(P4,'Meshes','SM_Window400X200_V1_Part1')]
    for side,style in ((-1,'RobotAdvertisment'),(1,'KeosAdvertisment')):
        mount=entrance['EntranceKit/Upper facade/Storage infill '+str(side)]
        scale=.7
        pivot=[mount['bounds_min'][0]-frame['extent'][0]*scale+.5,side*200.,430.]
        framed('Entrance/'+('South' if side<0 else 'North'),'400X200',pivot,180,scale,
               style,mount['name'],mount['bounds_min']+mount['bounds_max'])

    # Native cyan graph/instrument images enrich each approach without covering
    # the existing readable room-name boards or reducing the302cm door opening.
    frame=meshes[_asset(P4,'Meshes','SM_Window300X100_V1_Part1')]
    for name,y,normal,style in (('Engineering',-2300,1,'Graph1'),('Lounge',2300,-1,'DigitalPanel')):
        scale=.8
        mount=[4000.,y-37.5,302.,4400.,y+37.5,402.]
        surface=y+normal*37.5
        pivot=[4200.,surface+normal*(frame['extent'][0]*scale-.5),310.]
        framed('Room/'+name,'300X100',pivot,normal*90,scale,style,
               'Doors/'+name+' hatch/Header',mount)
    return groups


def audit(groups):
    failures=[]
    if len(groups)!=8:failures.append('Expected eight complete display groups')
    for group in groups:
        contact=next(p for p in group['parts'] if p['name']==group['mount_part'])
        if not _touch(contact['bounds'],group['mount_bounds']):
            failures.append(group['name']+': mounting geometry is detached')
        for row in group['parts']:
            if row['bounds'][2]<229.9:
                failures.append(row['name']+': enters walking/head clearance')
            if not all(math.isfinite(v) for v in row['bounds']):
                failures.append(row['name']+': nonfinite bounds')
        if group['name'].startswith('Market/'):
            # The owner-approved main lane remains |Y|<500, and nearby public
            # fixtures are centredY+/-600 with13cm half-depth.
            for row in group['parts']:
                if row['bounds'][1]<630 and row['bounds'][4]>-630:
                    failures.append(row['name']+': gantry light/central lane conflict')
    return {'groups':len(groups),'parts':sum(len(g['parts']) for g in groups),
            'failures':failures,'new_lights':0,'new_collision':0,
            'lowest_new_geometry_cm':min(p['bounds'][2] for g in groups for p in g['parts'])}


def apply(api):
    """Idempotent additions only; exact real mounts and native graphics checked."""
    import unreal as u
    from OutpostGeometryUtils import mesh_union
    package=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_path_name().split('.')[0]
    if package!=TARGET and not (package.startswith('/Temp/Untitled') and api.get('TARGET')==TARGET):
        raise RuntimeError('Blue native signage requires the private outpost')
    root=Path(api['ROOT'])
    catalog=json.loads(Path(os.environ.get('SS_PREFAB_CATALOG',str(root/'Artifacts/PrefabLibrary/catalog.json'))).read_text(encoding='utf-8'))
    groups=layout(catalog);evidence=audit(groups)
    if evidence['failures']:raise RuntimeError('; '.join(evidence['failures']))
    actors={}
    for actor in api['EAS'].get_all_level_actors():
        actors.setdefault(actor.get_actor_label(),[]).append(actor)

    def bounds(actor):
        c,e=mesh_union(actor)
        return [c.x-e.x,c.y-e.y,c.z-e.z,c.x+e.x,c.y+e.y,c.z+e.z]

    prepared={};mounts=[];material_receipts={}
    planned={row['name']:row for group in groups for row in group['parts']}
    for name,found in actors.items():
        if name.startswith(PREFIX) and (name not in planned or len(found)!=1 or TAG not in map(str,found[0].tags)):
            raise RuntimeError('Unknown or duplicate actor in owned signage namespace: '+name)
    for group in groups:
        found=actors.get(group['mount_name'],[])
        if len(found)!=1 or 'OutpostAuthored' not in map(str,found[0].tags):
            raise RuntimeError('Missing or unowned real signage mount: '+group['mount_name'])
        observed=bounds(found[0]);error=max(abs(a-b) for a,b in zip(observed,group['mount_bounds']))
        if error>.1:raise RuntimeError('Saved signage mount changed: '+group['mount_name'])
        mounts.append({'name':group['mount_name'],'actual_bounds':observed,'error_cm':error})
        for row in group['parts']:
            mesh=api['load'](row['asset']);b=mesh.get_bounds()
            native=[b.origin.x,b.origin.y,b.origin.z,b.box_extent.x,b.box_extent.y,b.box_extent.z]
            if max(abs(a-b) for a,b in zip(native,row['native_origin']+row['native_extent']))>.1:
                raise RuntimeError('Native signage bounds changed: '+row['asset'])
            materials=[]
            for path in row['materials']:
                source=api['load'](path);material=api['balanced'](source)
                if '/Translucent/' in path and path not in material_receipts:
                    edit=api['EDIT'];textures={};colors={};preserved_scalars=0
                    for key in edit.get_texture_parameter_names(source):
                        original=edit.get_material_instance_texture_parameter_value(source,key)
                        inherited=edit.get_material_instance_texture_parameter_value(material,key)
                        if original!=inherited:raise RuntimeError('Signage graphic lost native texture: '+path)
                        if original:textures[str(key)]=original.get_path_name()
                    for key in edit.get_vector_parameter_names(source):
                        original=edit.get_material_instance_vector_parameter_value(source,key)
                        inherited=edit.get_material_instance_vector_parameter_value(material,key)
                        values=[getattr(original,c) for c in ('r','g','b','a')]
                        if max(abs(values[i]-getattr(inherited,c)) for i,c in enumerate(('r','g','b','a')))>.0001:
                            raise RuntimeError('Signage native colors changed: '+path)
                        colors[str(key)]=values
                    for key in edit.get_scalar_parameter_names(source):
                        lower=str(key).lower()
                        emission=(('emiss' in lower or lower.startswith('intensity em')) and
                                  any(s in lower for s in ('intens','strength','power')))
                        if emission or lower in ('roughness','roughness_a','roughness_b','roughness_c'):continue
                        original=float(edit.get_material_instance_scalar_parameter_value(source,key))
                        inherited=float(edit.get_material_instance_scalar_parameter_value(material,key))
                        if abs(original-inherited)>.0001:
                            raise RuntimeError('Signage animation/graphic parameter changed: '+path+'/'+str(key))
                        preserved_scalars+=1
                    channels={str(k):float(edit.get_material_instance_scalar_parameter_value(source,k))
                              for k in edit.get_scalar_parameter_names(source) if str(k).lower().startswith('intensity em')}
                    gain=min(1.,40./max(abs(v) for v in channels.values())) if channels and max(abs(v) for v in channels.values())>30 else 1.
                    for key,value in channels.items():
                        actual=float(edit.get_material_instance_scalar_parameter_value(material,key))
                        if abs(actual-value*gain)>max(.0001,abs(value*gain)*.0001):
                            raise RuntimeError('Signage channel ratios were not preserved: '+path)
                    material_receipts[path]={'assigned':material.get_path_name(),'native_textures':textures,
                                             'native_colors':colors,'verified_other_scalars':preserved_scalars,
                                             'source_channels':channels,'common_gain':gain}
                materials.append(material)
            found=actors.get(row['name'],[])
            if found:
                actor=found[0];components=actor.get_components_by_class(u.StaticMeshComponent)
                p,r,s=actor.get_actor_location(),actor.get_actor_rotation(),actor.get_actor_scale3d()
                pose_error=max([abs(v-w) for v,w in zip((p.x,p.y,p.z),row['location'])]+
                               [abs(v-w) for v,w in zip((s.x,s.y,s.z),row['scale'])]+
                               [abs(r.pitch),abs(r.roll),abs((r.yaw-row['yaw']+180)%360-180)])
                if (len(components)!=1 or not components[0].static_mesh or
                    components[0].static_mesh.get_path_name()!=row['asset'] or
                    components[0].get_collision_enabled()!=u.CollisionEnabled.NO_COLLISION or
                    pose_error>.05 or max(abs(a-b) for a,b in zip(bounds(actor),row['bounds']))>.1):
                    raise RuntimeError('Existing owned sign changed; refusing overwrite: '+row['name'])
            prepared[row['name']]=(mesh,materials,found[0] if found else None)
    placements=[]
    for row in planned.values():
        mesh,materials,actor=prepared[row['name']];created=actor is None
        if created:
            actor=api['raw'](row['name'],row['asset'],row['location'],yaw=row['yaw'],
                             scale=row['scale'],solid=False,materials=materials)
            actor.tags=list(actor.tags)+[u.Name(TAG),u.Name('OutpostMount:ExistingStructure')]
        component=actor.static_mesh_component
        component.set_cast_shadow(False)
        for i,material in enumerate(materials):component.set_material(i,material)
        measured=bounds(actor)
        if max(abs(a-b) for a,b in zip(measured,row['bounds']))>.1:
            raise RuntimeError('Native signage placement did not match plan: '+row['name'])
        placements.append({'name':row['name'],'created':created,'actual_bounds':measured})
    return {'audit':evidence,'groups':groups,'actual_mounts':mounts,'placements':placements,
            'materials':material_receipts,'source_market_map':SOURCE_MAP,
            'provenance':'P5 screen125 thumbnail inspected: cyan Fruit Market words, photographs, QR/data and glass effects; P4 native Graph1/DigitalPanel cyan, Robot/Keos advert colors retained.',
            'untouched':'Planet, character holograms, existing signs, vendor banks, gameplay, lights, collision and all native assets',
            'map_saved':False,'validation':'Source bounds and material inheritance checks; native readability capture pending'}
