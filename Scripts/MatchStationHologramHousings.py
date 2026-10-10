"""Match Crew/Explorer static housings to the owner-edited Traders housing.

One guarded application on the inspected saved map. Hologram characters, labels,
lighting, other room edits and source assets stay intact. Do not replay after save.
"""
import hashlib
import json
from pathlib import Path

MAP='/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
EXPECTED='12761d2f4bc2e8c64ff0c5d5ee48fbd3b8326950f080085b411b3b82e0e745fd'

def fingerprint(u,a):
    row={'path':a.get_path_name(),'label':a.get_actor_label(),
         'class':a.get_class().get_name(),'position':list(a.get_actor_location().to_tuple()),
         'rotation':list(a.get_actor_rotation().to_tuple()),'scale':list(a.get_actor_scale3d().to_tuple()),
         'tags':list(map(str,a.tags)),'hidden':bool(a.hidden),
         'actor_collision':a.get_actor_enable_collision()}
    if isinstance(a,u.StaticMeshActor):
        c=a.static_mesh_component
        row.update(mesh=c.static_mesh.get_path_name() if c.static_mesh else None,
            materials=[m.get_path_name() if m else None for m in c.get_materials()],
            visible=c.is_visible(),component_hidden=c.get_editor_property('hidden_in_game'),
            collision=str(c.get_collision_enabled()),profile=str(c.get_collision_profile_name()))
    return row

def part(a,bay):
    label=a.get_actor_label()
    for prefix,kind in ((f'LoungeNative/Hologram bay {bay}/','Housing'),
                        (f'Refine/ArchiveConcept77/Bay {bay}/Warm edge','Trim')):
        if label.startswith(prefix):return kind+':'+label[len(prefix):]
    return None

def inspect(u):
    editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
    assert not editor.get_game_world(), 'Stop owned Play before authoring'
    world=editor.get_editor_world()
    assert world.get_path_name().split('.')[0]==MAP
    root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
    file=root/'Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap'
    assert hashlib.sha256(file.read_bytes()).hexdigest()==EXPECTED, 'Preserve newer owner changes'
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    actors=list(u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())
    groups={}
    for bay in (1,2,3):
        group={}
        for a in actors:
            key=part(a,bay)
            if key and isinstance(a,u.StaticMeshActor):
                assert key not in group and not a.get_attach_parent_actor(), a.get_actor_label()
                group[key]=a
        groups[bay]=group
    assert len(groups[2])==21 and all(len(groups[b])==16 for b in (1,3)), 'Inspect the exact owner structure'
    for bay in (1,3):
        assert set(groups[bay])-set(groups[2])=={'Housing:North/Frame','Housing:South/Frame'}
        assert len(set(groups[2])-set(groups[bay]))==7
    return root,file,world,actors,groups

def apply(u):
    root,file,world,actors,groups=inspect(u)
    out=root/'.agent/local/StationRefinement/HologramMatch210'
    out.mkdir(exist_ok=False)
    before={a.get_path_name():fingerprint(u,a) for a in actors}
    (out/'Before.json').write_text(json.dumps(before,indent=2)+'\n')
    (out/'OwnerSavedMapBefore.umap').write_bytes(file.read_bytes())
    assert hashlib.sha256((out/'OwnerSavedMapBefore.umap').read_bytes()).hexdigest()==EXPECTED
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    target_paths={a.get_path_name() for bay in (1,3) for a in groups[bay].values()}
    added=[];removed=[];matches=[]
    with u.ScopedEditorTransaction('Match Crew and Explorer housings to Traders'):
        for bay,dx in ((1,-580.),(3,580.)):
            for key,source in groups[2].items():
                target=groups[bay].get(key)
                if not target:
                    target=sub.duplicate_actor(source,world,u.Vector(dx,0.,0.))
                    assert target
                    label=source.get_actor_label().replace('bay 2/','bay '+str(bay)+'/').replace('Bay 2/','Bay '+str(bay)+'/')
                    target.set_actor_label(label)
                    target.set_editor_property('tags',[u.Name(str(t).replace(source.get_actor_label(),label)) for t in source.tags])
                    added.append(target.get_path_name())
                else:
                    target.modify();c=target.static_mesh_component;sc=source.static_mesh_component
                    c.modify();c.set_static_mesh(sc.static_mesh)
                    for slot in range(sc.get_num_materials()):c.set_material(slot,sc.get_material(slot))
                    c.set_collision_profile_name(sc.get_collision_profile_name())
                    c.set_collision_enabled(sc.get_collision_enabled())
                    c.set_visibility(sc.is_visible())
                    c.set_editor_property('hidden_in_game',sc.get_editor_property('hidden_in_game'))
                    target.set_actor_hidden_in_game(source.hidden)
                    target.set_actor_enable_collision(source.get_actor_enable_collision())
                    target.set_actor_transform(source.get_actor_transform(),False,True)
                    target.set_actor_location(source.get_actor_location()+u.Vector(dx,0.,0.),False,True)
                matches.append({'source':source.get_path_name(),'target':target.get_path_name(),'bay':bay,'offset':[dx,0.,0.]})
            for key in set(groups[bay])-set(groups[2]):
                old=groups[bay][key]
                removed.append(old.get_path_name());assert sub.destroy_actor(old)
    after={a.get_path_name():fingerprint(u,a) for a in sub.get_all_level_actors()}
    untouched={k:v for k,v in before.items() if k not in target_paths}
    changed_outside=[k for k,v in untouched.items() if after.get(k)!=v]
    assert not changed_outside, changed_outside[:10]
    assert len(added)==14 and len(removed)==4 and len(after)==len(before)+10
    receipt={'before_sha256':EXPECTED,'before_actor_count':len(before),'after_actor_count':len(after),
             'protected_existing_actors':len(untouched),'changed_outside_scope':changed_outside,
             'added':added,'removed':removed,'matches':matches,'saved':False}
    (out/'After.json').write_text(json.dumps(after,indent=2)+'\n')
    (out/'Receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt

def verify(u):
    actors=list(u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())
    groups={bay:{part(a,bay):a for a in actors if part(a,bay) and isinstance(a,u.StaticMeshActor)} for bay in (1,2,3)}
    assert all(set(groups[b])==set(groups[2]) for b in (1,3))
    for bay,dx in ((1,-580.),(3,580.)):
        for key,source in groups[2].items():
            target=groups[bay][key]
            assert (target.get_actor_location()-source.get_actor_location()-u.Vector(dx,0,0)).length()<.001
            assert all(abs(a-b)<.001 for a,b in zip(target.get_actor_rotation().to_tuple(),source.get_actor_rotation().to_tuple()))
            assert all(abs(a-b)<.001 for a,b in zip(target.get_actor_scale3d().to_tuple(),source.get_actor_scale3d().to_tuple()))
            a,b=fingerprint(u,source),fingerprint(u,target)
            for field in ('mesh','materials','visible','component_hidden','collision','profile','actor_collision','hidden'):
                assert a[field]==b[field], (bay,key,field)
    return {'matched_parts_per_housing':len(groups[2]),'matched_housings':2}

def save(u):
    check=verify(u)
    root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
    out=root/'.agent/local/StationRefinement/HologramMatch210'
    assert u.EditorLevelLibrary.save_current_level(), 'Retain current state and inspect a failed save'
    file=root/'Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap'
    receipt=json.loads((out/'Receipt.json').read_text())
    receipt.update(saved=True,map_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),verification=check)
    (out/'MapAfter.umap').write_bytes(file.read_bytes())
    (out/'Receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return {k:v for k,v in receipt.items() if k not in ('matches','added','removed')}
