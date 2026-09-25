"""Author single-placement building assemblies and additive browser collections.

Run offscreen against the sandbox. Never loads or saves L_AsteroidOutpost.
Existing generated assets are reused only if both receipt and bytes match.
"""
import hashlib
import json
import re
import sys
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT/'Scripts'))
import BuildingPrefabRecipes
import ConfigureUlatLibrary

OUT = ROOT/'Artifacts/BuildingLibrary'
BASE = '/Game/BuildingLibrary/Assembled'
MAP = ROOT/'Content/OutpostSandbox/L_AsteroidOutpost.umap'
LIB = u.EditorAssetLibrary
EAS = u.get_editor_subsystem(u.EditorActorSubsystem)
SUB = u.get_engine_subsystem(u.SubobjectDataSubsystem)
ABOUT = u.SubobjectDataBlueprintFunctionLibrary


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def disk(package):
    return ROOT/'Content'/(package.removeprefix('/Game/')+'.uasset')


def vec(value):
    return u.Vector(*value)


def rot(value):
    return u.Rotator(pitch=value[0], yaw=value[1], roll=value[2])


def make_part(bp, parent, name, cls):
    params = u.AddNewSubobjectParams(parent_handle=parent, new_class=cls,
                                     blueprint_context=bp, skip_mark_blueprint_modified=False)
    handle, reason = SUB.add_new_subobject(params)
    assert ABOUT.is_handle_valid(handle), str(reason)
    assert SUB.rename_subobject(handle, u.Text(re.sub(r'[^A-Za-z0-9_]', '_', name)))
    obj = ABOUT.get_object_for_blueprint(ABOUT.get_data(handle), bp)
    assert obj, 'No editable Blueprint component template: '+name
    return handle, obj


def inspect_instance(bp, expected):
    cls = bp.generated_class()
    actor = EAS.spawn_actor_from_class(cls, u.Vector(0, 0, 0))
    try:
        components = actor.get_components_by_class(u.StaticMeshComponent)
        assert len(components) == expected, (bp.get_name(), len(components), expected)
        assert all(c.static_mesh for c in components), 'Missing mesh after Blueprint compile'
        # Changing the one actor must carry every layer together.
        before = [c.get_world_location() for c in components]
        actor.set_actor_location(u.Vector(137, 251, 389), False, False)
        after = [c.get_world_location() for c in components]
        assert all((b-a-u.Vector(137, 251, 389)).length() < .05 for a,b in zip(before,after)), 'Assembly contains a detached layer'
        origin, extent = actor.get_actor_bounds(False)
        return {'components': len(components), 'bounds_extent': [extent.x,extent.y,extent.z],
                'bottom_at_placement_z': abs(origin.z-extent.z-389)<1., 'moves_as_one': True}
    finally:
        EAS.destroy_actor(actor)


def create_prefab(recipe, prior):
    category = re.sub(r'[^A-Za-z0-9_]', '_', recipe['category'])
    name = recipe['name']
    package = BASE+'/'+category+'/'+name
    signature = hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest()
    if LIB.does_asset_exist(package):
        record = prior.get(package)
        assert record and record['file_sha256'] == digest(disk(package)), 'Preserve owner-edited or unrecognized prefab: '+package
        assert record['recipe_sha256'] == signature, 'Recipe changed; deliberate regeneration required: '+package
        return dict(record, reused=True)
    bp = u.BlueprintEditorLibrary.create_blueprint_asset_with_parent(package, u.Actor)
    assert bp, 'Blueprint creation failed: '+package
    handles = SUB.k2_gather_subobject_data_for_blueprint(bp)
    scene = [(h, ABOUT.get_object_for_blueprint(ABOUT.get_data(h), bp)) for h in handles]
    roots = [(h,o) for h,o in scene if isinstance(o,u.SceneComponent)]
    if roots:
        parent, root = roots[0]
    else:
        parent, root = make_part(bp, handles[0], 'AssemblyRoot', u.SceneComponent)
    root.set_editor_property('mobility', u.ComponentMobility.STATIC)
    templates = []
    bounds = []
    for index, part in enumerate(recipe['parts']):
        mesh = u.load_asset(part['asset'])
        assert isinstance(mesh,u.StaticMesh), part['asset']
        _, component = make_part(bp, parent, str(index)+'_'+part['name'], u.StaticMeshComponent)
        component.set_static_mesh(mesh)
        component.set_editor_property('mobility',u.ComponentMobility.STATIC)
        component.set_editor_property('relative_location',vec(part['location']))
        component.set_editor_property('relative_rotation',rot(part['rotation']))
        component.set_editor_property('relative_scale3d',vec(part['scale']))
        for slot,path in enumerate(part.get('materials',[])):
            if path:
                material=u.load_asset(path)
                assert material,path
                component.set_material(slot,material)
        if part.get('solid') is False:
            component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        templates.append(component)
        # Transform all eight native bounds corners, including nonzero source pivots.
        b=mesh.get_bounds()
        q=rot(part['rotation']).quaternion()
        for x in (-1,1):
            for y in (-1,1):
                for z in (-1,1):
                    point=u.Vector((b.origin.x+x*b.box_extent.x)*part['scale'][0],
                                   (b.origin.y+y*b.box_extent.y)*part['scale'][1],
                                   (b.origin.z+z*b.box_extent.z)*part['scale'][2])
                    bounds.append(q.rotate_vector(point)+vec(part['location']))
    anchor=u.Vector((min(v.x for v in bounds)+max(v.x for v in bounds))/2,
                    (min(v.y for v in bounds)+max(v.y for v in bounds))/2,
                    min(v.z for v in bounds))
    for component in templates:
        component.set_editor_property('relative_location',component.get_editor_property('relative_location')-anchor)
    u.BlueprintEditorLibrary.compile_blueprint(bp)
    validation=inspect_instance(bp,len(templates))
    assert validation['bottom_at_placement_z'], 'Unexpected placement pivot: '+package
    assert LIB.save_loaded_asset(bp,only_if_is_dirty=False)
    return {'asset':package+'.'+name,'recipe_sha256':signature,'file_sha256':digest(disk(package)),
            'source':recipe.get('source'), 'parts':len(templates),'validation':validation}


def collection(name,paths):
    manager=u.get_editor_subsystem(u.CollectionManagerSubsystem)
    name=re.sub(r'[^A-Za-z0-9_]', '_', name)
    ref=u.Collection(container='Game',name=name,share_type=u.CollectionShareType.LOCAL)
    paths=sorted(set(paths))
    if paths:
        # A false return can also mean every asset is already a member.
        manager.add_assets_to_collection(ref,[u.SoftObjectPath(p) for p in paths])
        members=manager.get_assets_in_collection(ref)
        if isinstance(members,tuple):
            members=members[-1]
        actual={str(p.package_name)+'.'+str(p.asset_name) for p in members}
        assert set(paths).issubset(actual),name
    return {'name':name,'requested_assets':len(paths)}


def main():
    before=digest(MAP)
    OUT.mkdir(parents=True,exist_ok=True)
    receipt=OUT/'prefab-author.json'
    prior=json.loads(receipt.read_text()) if receipt.exists() else {'prefabs':{}}
    report={'status':'running','station_before':before,'prefabs':prior['prefabs'],'collections':[],'errors':[]}
    try:
        assert u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_path_name().startswith('/Engine/Maps/Entry'), 'Run in empty Entry map only'
        registry=u.AssetRegistryHelpers.get_asset_registry()
        registry.search_all_assets(True)
        roots=['/Game/P1toP5_Bundle','/Game/CargoShip','/Game/CyberpunkRestaurant','/Game/Rocket','/Game/ImportedLibrary',
               '/Game/StarterBundle','/Game/SciFiCorridor','/Game/Ultimate_Space_Colony_Outpost_Pack']
        inventory=[]
        for path in roots:
            for a in registry.get_assets_by_path(path,recursive=True):
                inventory.append({'asset':str(a.package_name)+'.'+str(a.asset_name),'name':str(a.asset_name),'class':str(a.asset_class_path.asset_name)})
        recipes=BuildingPrefabRecipes.recipes(ROOT,inventory)
        for recipe in recipes:
            record=create_prefab(recipe,report['prefabs'])
            package=record['asset'].split('.')[0]
            report['prefabs'][package]=record
            receipt.write_text(json.dumps(report,indent=2),encoding='utf-8')
        report['collections'].append(collection('SS 01 Assembled - Drag These', [r['asset'] for r in report['prefabs'].values()]))
        groups={}
        for a in inventory:
            if a['class'] not in ('StaticMesh','Blueprint','MaterialInstanceConstant'):
                continue
            if a['class']=='StaticMesh':
                _,label=ConfigureUlatLibrary._classify(a['asset'])
                groups.setdefault('SS Parts - '+label,[]).append(a['asset'])
            if a['asset'].startswith('/Game/CargoShip/'):
                groups.setdefault('SS New - Cargo Ship',[]).append(a['asset'])
            elif a['asset'].startswith('/Game/CyberpunkRestaurant/'):
                groups.setdefault('SS New - Nova Space Burgers',[]).append(a['asset'])
            elif a['asset'].startswith('/Game/Rocket/'):
                groups.setdefault('SS New - Furniture Lights and Props',[]).append(a['asset'])
            elif a['asset'].startswith('/Game/ImportedLibrary/'):
                groups.setdefault('SS New - Solar and Portal Materials',[]).append(a['asset'])
        for name,paths in groups.items():
            report['collections'].append(collection(name,paths))
        ulat=ConfigureUlatLibrary.apply(roots=roots,apply=False)
        report['ulat_dry_run']={k:ulat.get(k) for k in ('status','planned_rows','existing_rows','errors','report_path')}
        assert ulat['status']=='dry_run_ready', 'ULAT dry-run failed: '+str(ulat['errors'])
        if ulat['status']=='dry_run_ready' and '-SSApplyUlat' in u.SystemLibrary.get_command_line():
            result=ConfigureUlatLibrary.apply(roots=roots,apply=True)
            report['ulat_apply']={k:result.get(k) for k in ('status','verified_rows','errors','report_path')}
            assert result['status'] in ('applied','unchanged'), 'ULAT apply failed: '+str(result['errors'])
            assert result.get('verified_rows',result.get('existing_rows',0))>4, 'No building meshes registered in ULAT'
        report['status']='PASS'
    except Exception as error:
        report['errors'].append(str(error))
        report['status']='FAILED'
        raise
    finally:
        report['station_after']=digest(MAP)
        report['station_unchanged']=before==report['station_after']
        if not report['station_unchanged']:
            report['status']='FAILED'
            report['errors'].append('Station bytes changed during library authoring')
        receipt.write_text(json.dumps(report,indent=2),encoding='utf-8')
        u.log('BUILDING_LIBRARY_AUTHOR '+report['status'])


if __name__=='__main__':
    main()
