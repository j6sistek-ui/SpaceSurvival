"""Import/apply private machined perimeter meshes on exactly three berth pads.

Run BuildOutpostPadTrim.py in Blender first. Native textured metal stays inherited;
the two source halo actors per pad remain hidden for provenance. Existing deck
panels, underside, edge fixtures, ground collision, ship and access routes remain.
Caller owns map saving and native visual review; never touches atrium/globe rings.
"""
import hashlib
import json
import math
from pathlib import Path

TARGET='/Game/OutpostSandbox/L_AsteroidOutpost'
TAG='OutpostMachinedPadTrim'
REPLACED='OutpostMachinedPadTrim:ReplacedHalo'
DEST='/Game/OutpostSandbox/Geometry/PadTrim'
PADS=(('Player berth',(-4200.,0.),3000.,'SM_OutpostPadTrim_Player'),
      ('Visitor berth 02',(-600.,-3900.),1400.,'SM_OutpostPadTrim_Visitor'),
      ('Visitor berth 03',(-600.,3900.),1400.,'SM_OutpostPadTrim_Visitor'))
SLOTS=('PadMetal','PadBezel','PadCyanLens','PadWarmGuide')
NATIVE_METAL='/Game/P1toP5_Bundle/P4_Genesis_Vol1/Materials/Instances/Opaque/MI_Metal12_PaintAnodizedAluminium_Dark'
DECK_MESH='/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_UniversalPanel400X200_V2'
MATCH_METAL='/Game/OutpostSandbox/Materials/MI_PadTrim_DeckMatch'


def source_audit(catalog):
    """Confirm the new inner circular edge overlaps retained tiled deck at720 angles."""
    from OutpostBerthDetails import PADS as BERTHS,layout,bounds
    rows=layout(catalog)
    report=[]
    for pad in BERTHS:
        tiles=[bounds(row) for row in rows if row['pad']==pad['name'] and row['role']=='Deck']
        misses=[]
        for index in range(720):
            angle=index*math.tau/720
            x=pad['center'][0]+(pad['radius']-500)*math.cos(angle)
            y=pad['center'][1]+(pad['radius']-500)*math.sin(angle)
            if not any(b[0]-.05<=x<=b[3]+.05 and b[1]-.05<=y<=b[4]+.05 for b in tiles):
                misses.append(index)
        report.append({'pad':pad['name'],'inner_edge_samples':720,'uncovered_samples':misses,
                       'new_collision':False,'trim_deck_z':.65,'retained_tile_max_z':.5})
    return report


def apply(api):
    u,eas,lib,tools=api['u'],api['EAS'],api['LIB'],api['TOOLS']
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if api.get('TARGET')!=TARGET or world.get_path_name().split('.')[0]!=TARGET:
        raise RuntimeError('Machined pad trim requires the saved private outpost')
    root,out=Path(api['ROOT']),Path(api['OUT'])
    directory=Path(api.get('PAD_TRIM_GEOMETRY',out/'PadTrimGeometry'))
    recipe=json.loads((directory/'pad-trim-geometry.json').read_text(encoding='utf-8-sig'))
    metadata={row['mesh']:row for row in recipe['meshes']}
    if set(metadata)!={row[3] for row in PADS}:
        raise RuntimeError('Pad trim export does not contain exactly the two intended meshes')
    import os
    catalog=json.loads(Path(os.environ.get('SS_PREFAB_CATALOG',str(root/'Artifacts/PrefabLibrary/catalog.json'))).read_text(encoding='utf-8'))
    evidence=source_audit(catalog)
    if any(row['uncovered_samples'] for row in evidence):
        raise RuntimeError('Trim inner edge does not bridge retained deck outline')
    from OutpostGeometryUtils import mesh_union
    labels={}
    for actor in eas.get_all_level_actors():
        labels.setdefault(actor.get_actor_label(),[]).append(actor)

    def one(name):
        matches=labels.get(name,[])
        if len(matches)!=1 or 'OutpostAuthored' not in map(str,matches[0].tags):
            raise RuntimeError('Missing, ambiguous or unowned berth actor: '+name)
        return matches[0]

    def geometry_bounds(actor):
        center,extent=mesh_union(actor)
        return [getattr(center,a)-getattr(extent,a) for a in 'xyz']+[getattr(center,a)+getattr(extent,a) for a in 'xyz']

    source_halos=[];ground_snapshots=[];existing={}
    for name,center,radius,mesh_name in PADS:
        ground=one('Ground/'+name)
        if len(ground.get_components_by_class(u.StaticMeshComponent))!=1:
            raise RuntimeError('Unexpected berth ground composition')
        gc=ground.static_mesh_component
        b=geometry_bounds(ground)
        expected=[center[0]-radius,center[1]-radius,-90,center[0]+radius,center[1]+radius,0]
        if max(abs(a-c) for a,c in zip(b,expected))>.15 or str(gc.get_collision_profile_name())!='BlockAll':
            raise RuntimeError('Berth ground geometry/collision changed: '+name)
        ground_snapshots.append((ground,b,str(gc.get_collision_profile_name()),gc.get_collision_enabled()))
        for suffix in ('Approach halo','Inset markings'):
            actor=one(name+'/'+suffix)
            component=actor.static_mesh_component
            if component.get_collision_enabled()!=u.CollisionEnabled.NO_COLLISION:
                raise RuntimeError('Refusing to hide a colliding halo')
            if component.get_editor_property('cast_hidden_shadow'):
                raise RuntimeError('Halo has hidden-shadow behavior')
            source_halos.append((actor,component))
        matches=labels.get('PadTrim/'+name,[])
        if matches:
            if len(matches)!=1 or TAG not in map(str,matches[0].tags):
                raise RuntimeError('Unexpected existing pad trim')
            existing[name]=matches[0]

    # Imported geometry is strictly private. No vendor mesh or material import.
    meshes={};imports=[]
    for name,row in metadata.items():
        fbx=directory/row['fbx']
        if (row.get('failures') or tuple(row['material_slots'])!=SLOTS or
                hashlib.sha256(fbx.read_bytes()).hexdigest()!=row['fbx_sha256']):
            raise RuntimeError('Pad trim export proof/hash mismatch')
        task=u.AssetImportTask()
        task.filename=str(fbx);task.destination_path=DEST;task.destination_name=name
        task.automated=True;task.save=True;task.replace_existing=True
        options=u.FbxImportUI()
        options.import_mesh=True;options.import_materials=False;options.import_textures=False
        options.import_as_skeletal=False
        data=options.static_mesh_import_data
        data.combine_meshes=True;data.auto_generate_collision=False
        data.set_editor_property('build_nanite',False)
        data.set_editor_property('normal_import_method',u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
        task.options=options;tools.import_asset_tasks([task])
        mesh=api['load'](DEST+'/'+name)
        if not isinstance(mesh,u.StaticMesh):
            raise RuntimeError('Private FBX static mesh import failed: '+name)
        b=mesh.get_bounds()
        actual=[b.origin.x-b.box_extent.x,b.origin.y-b.box_extent.y,b.origin.z-b.box_extent.z,
                b.origin.x+b.box_extent.x,b.origin.y+b.box_extent.y,b.origin.z+b.box_extent.z]
        expected=[-row['radius_cm'],-row['radius_cm'],row['min_z_cm'],
                   row['radius_cm'],row['radius_cm'],row['max_z_cm']]
        if max(abs(a-c) for a,c in zip(actual,expected))>.3:
            raise RuntimeError('Imported pad trim has incorrect units/bounds: '+name)
        names=[str(m.material_slot_name) for m in mesh.static_materials]
        if len(names)!=4 or set(names)!=set(SLOTS):
            raise RuntimeError('Private FBX material slot names changed: '+str(names))
        meshes[name]=mesh
        imports.append({'asset':mesh.get_path_name(),'fbx_sha256':row['fbx_sha256'],
                        'actual_bounds_cm':actual,'material_slots':names,'triangles':row['exported_triangles']})

    metal,finish_proof=_deck_match_material(api)
    source_file=Path(finish_proof['native_source_file'])
    native_hash=finish_proof['native_source_sha256']
    materials={'PadMetal':metal,
               'PadBezel':api['load']('/Game/OutpostSandbox/Materials/M_OutpostGraphite'),
               'PadCyanLens':api['material']('M_OutpostPadTrimCyan',(.035,.38,.55),emission=2.4),
               'PadWarmGuide':api['material']('M_OutpostPadTrimWarm',(.65,.22,.035),emission=2.)}
    placed=[]
    for name,center,radius,mesh_name in PADS:
        actor=existing.get(name)
        if actor is None:
            actor=eas.spawn_actor_from_class(u.StaticMeshActor,u.Vector(center[0],center[1],0))
            actor.set_actor_label('PadTrim/'+name);actor.set_folder_path('PadTrim')
            actor.tags=[u.Name(TAG),u.Name('OutpostAuthored')]
        c=actor.static_mesh_component
        c.set_static_mesh(meshes[mesh_name])
        c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        c.set_collision_profile_name('NoCollision')
        c.set_simulate_physics(False)
        for slot,material in enumerate(meshes[mesh_name].static_materials):
            c.set_material(slot,materials[str(material.material_slot_name)])
        actor.set_actor_rotation(u.Rotator(),False)
        actor.set_actor_scale3d(u.Vector(1,1,1))
        actor.set_actor_location(u.Vector(center[0],center[1],0),False,False)
        actor.set_actor_hidden_in_game(False);c.set_visibility(True,False)
        placed.append({'actor':actor.get_actor_label(),'mesh':mesh_name,'bounds_cm':geometry_bounds(actor),
                       'collision':str(c.get_collision_enabled())})
    for actor,component in source_halos:
        component.set_visibility(False,False);actor.set_actor_hidden_in_game(True)
        if REPLACED not in map(str,actor.tags):actor.tags=list(actor.tags)+[u.Name(REPLACED)]
    for ground,b,profile,enabled in ground_snapshots:
        c=ground.static_mesh_component
        if (max(abs(a-v) for a,v in zip(geometry_bounds(ground),b))>.001 or
                str(c.get_collision_profile_name())!=profile or c.get_collision_enabled()!=enabled):
            raise RuntimeError('Supporting berth ground changed during trim apply')
    if hashlib.sha256(source_file.read_bytes()).hexdigest()!=native_hash:
        raise RuntimeError('Owned source metal material changed')
    result={'imports':imports,'placements':placed,'inner_edge_coverage':evidence,
            'hidden_retained_halos':[a.get_actor_label() for a,_ in source_halos],
            'native_metal':metal.get_path_name(),'native_source_sha256':native_hash,
            'deck_material_match':finish_proof,
            'ground_collision_unchanged':True,'map_saved':False,
            'scope':'Three private shallow annuli only; no atrium/globe/ship/stair or launch changes',
            'native_appearance':'PENDING_LEAD_CAPTURE'}
    (out/'pad-trim.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def _deck_match_material(api):
    """Private child of the ACTUAL adjacent native deck finish, no color invention.

    Catalog proxy upward surface area is largest for native slot4 dark painted
    aluminium (3.991m2), followed by slot2 paint (3.553m2). The source finish
    pass preserves that material graph/textures and sets its existing tint and
    roughness parameters. Inheriting the placed slot reproduces those values.
    """
    u,edit,lib=api['u'],api['EDIT'],api['LIB']
    matches=[]
    for actor in api['EAS'].get_all_level_actors():
        if not actor.get_actor_label().startswith('BerthDetail/Player/Deck '):continue
        components=list(actor.get_components_by_class(u.StaticMeshComponent))
        if len(components)!=1 or components[0].static_mesh.get_path_name().split('.')[0]!=DECK_MESH:continue
        source_slots=list(components[0].static_mesh.static_materials)
        if len(source_slots)<=4 or source_slots[4].material_interface.get_path_name().split('.')[0]!=NATIVE_METAL:
            raise RuntimeError('Native deck slot4 no longer identifies dark painted metal')
        current=components[0].get_material(4)
        if not isinstance(current,u.MaterialInstanceConstant) or not current.get_path_name().startswith('/Game/OutpostSandbox/Materials/MI_Finish_Deck_'):
            raise RuntimeError('The adjacent berth has no authored dark deck finish')
        matches.append((actor.get_actor_label(),current))
    if not matches or len({m.get_path_name() for _,m in matches})!=1:
        raise RuntimeError('Missing or inconsistent adjacent deck material; refuse pale fallback')
    reference,source=sorted(matches,key=lambda item:item[0])[0]
    parent=source;chain=[]
    while parent.get_path_name().split('.')[0]!=NATIVE_METAL:
        path=parent.get_path_name()
        if path in chain or not isinstance(parent,u.MaterialInstanceConstant) or not path.startswith((
                '/Game/OutpostSandbox/Materials/MI_Finish_Deck_',
                '/Game/OutpostSandbox/Materials/MI_Balanced_')):
            raise RuntimeError('Adjacent deck finish has an unexpected native parent chain')
        chain.append(path);parent=parent.get_editor_property('parent')
        if parent is None:raise RuntimeError('Broken native deck finish chain')
    chain.append(parent.get_path_name())
    file=Path(api['ROOT'])/('Content/'+NATIVE_METAL[len('/Game/'):]+'.uasset')
    before=hashlib.sha256(file.read_bytes()).hexdigest()
    metal=api['load'](MATCH_METAL) if lib.does_asset_exist(MATCH_METAL) else api['TOOLS'].create_asset(
        'MI_PadTrim_DeckMatch','/Game/OutpostSandbox/Materials',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
    edit.set_material_instance_parent(metal,source)
    edit.update_material_instance(metal)
    if not lib.save_loaded_asset(metal):raise RuntimeError('Could not save private pad/deck match')
    if hashlib.sha256(file.read_bytes()).hexdigest()!=before:raise RuntimeError('Native deck material changed')
    tint=edit.get_material_instance_vector_parameter_value(metal,'Albedo Tint')
    return metal,{'reference_actor':reference,'reference_slot':4,'matching_deck_actors':len(matches),
        'inherited_from':source.get_path_name(),'private':metal.get_path_name(),'parent_chain':chain,
        'native_source_file':str(file),'native_source_sha256':before,
        'inherited_albedo_tint':[tint.r,tint.g,tint.b,tint.a],
        'textures_and_parameters':'Inherited unchanged from actual adjacent deck slot4'}


def apply_material_match(api):
    """Narrow follow-up: only PadMetal on three existing trims; no FBX reimport."""
    u,eas=api['u'],api['EAS']
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if api.get('TARGET')!=TARGET or world.get_path_name().split('.')[0]!=TARGET:
        raise RuntimeError('Pad finish match requires the saved private outpost')
    staged=[]
    for name,center,radius,mesh_name in PADS:
        actors=[a for a in eas.get_all_level_actors() if a.get_actor_label()=='PadTrim/'+name]
        if len(actors)!=1 or TAG not in map(str,actors[0].tags):raise RuntimeError('Missing/ambiguous owned trim')
        actor=actors[0];c=actor.static_mesh_component
        if c.static_mesh.get_path_name().split('.')[0]!=DEST+'/'+mesh_name:raise RuntimeError('Unexpected pad trim mesh')
        indices=[i for i,m in enumerate(c.static_mesh.static_materials) if str(m.material_slot_name)=='PadMetal']
        if len(indices)!=1 or c.get_collision_enabled()!=u.CollisionEnabled.NO_COLLISION:raise RuntimeError('Trim material/collision contract changed')
        staged.append((actor,c,indices[0]))
    metal,proof=_deck_match_material(api)
    changed=[]
    for actor,c,slot in staged:
        before=c.get_material(slot).get_path_name()
        c.set_material(slot,metal)
        if c.get_material(slot)!=metal:raise RuntimeError('Pad dark finish readback failed')
        changed.append({'actor':actor.get_actor_label(),'slot':slot,'before':before,'after':metal.get_path_name()})
    result={'finish':proof,'assignments':changed,'geometry_collision_lights_unchanged':True,
            'appearance':'Pending native same-view review'}
    (Path(api['OUT'])/'pad-trim-material-match.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
