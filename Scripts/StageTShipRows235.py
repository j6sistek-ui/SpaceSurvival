"""One-time copy/paste mock-up: six Phoenix displays; park existing desks aside."""
import hashlib, importlib.util, json
from pathlib import Path
MAP='/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
EXPECTED='205078467def6a7a1ad1aa3d090cfb145976b3da8311effe7c15469641bd835a'
PREFIX='Refine/OperationsComposition/'
CENTRES=((7240.,-400.),(7990.,-400.),(8740.,-400.),(7240.,400.),(7990.,400.),(8740.,400.))

def apply(u, resume_before_duplication=False):
    root=Path(u.Paths.project_dir()).resolve()
    file=root/'Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap'
    out=root/'.agent/local/StationRefinement/TShipRows241'
    assert not out.exists() or resume_before_duplication, 'Never replay the saved mock-up.'
    assert hashlib.sha256(file.read_bytes()).hexdigest()==EXPECTED, 'Preserve newer owner edits.'
    editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
    assert not editor.get_game_world() and editor.get_editor_world().get_path_name().split('.')[0]==MAP
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages() and not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    assert u.SystemLibrary.get_console_variable_int_value('r.RayTracing')==0
    spec=importlib.util.spec_from_file_location('t235fingerprint',root/'Scripts/ActivateCyborgPole218.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    sub=u.get_editor_subsystem(u.EditorActorSubsystem);actors=list(sub.get_all_level_actors())
    assert len(actors)==9107
    assembly=[a for a in actors if a.get_actor_label().startswith(PREFIX)]
    assert len(assembly)==60
    sequence_actor=[a for a in assembly if isinstance(a,u.LevelSequenceActor)];assert len(sequence_actor)==1
    sequence_actor=sequence_actor[0];sequence=sequence_actor.get_sequence()
    bindings=sequence.get_bindings();assert len(bindings)==1
    binding_id=u.MovieSceneSequenceExtensions.get_binding_id(sequence,bindings[0])
    pivot=[a for a in assembly if a.get_actor_label()==PREFIX+'Phoenix rotation pivot'];assert len(pivot)==1
    pivot=pivot[0]
    instance=sequence_actor.get_editor_property('default_instance_data');assert instance
    original_overrides=sequence_actor.get_editor_property('binding_overrides')
    original_binding_data=list(original_overrides.get_editor_property('binding_data'))
    # Populate serialized overrides directly. SetBinding crashes in this editor
    # before its sequence player initializes; do not call that runtime method.
    probe=u.MovieSceneBindingOverrideData()
    probe.set_editor_property('object_binding_id',binding_id)
    probe.set_editor_property('object',pivot)
    probe.set_editor_property('overrides_default',True)
    old_origin=instance.get_editor_property('transform_origin')
    old_override=sequence_actor.get_editor_property('override_instance_data')
    assert not old_override
    moves={}
    for a in actors:
        label=a.get_actor_label()
        if label.startswith(('Engineering/Primary workstation/','Engineering/Workstation light/Primary/','Refine/OperationsDisplays/Flight upgrades/')):
            moves[a]=u.Vector(-960.,900.,0.)
        for side,dy in (('Port North',420.),('Port South',-420.),('Starboard North',120.),('Starboard South',-120.)):
            if label.startswith('OperationsNative/Command island '+side+'/') or label=='Refine/OperationsMountedDisplays/'+side or label=='Refine/Operations/'+side+'/Footrest':
                moves[a]=u.Vector(0.,dy,0.)
    assert len(moves)>100
    assert not any(isinstance(a,u.SkeletalMeshActor) or a.get_class().get_name()=='SSOutpostAmbientActor' for a in moves), 'Keep all NPC placements.'
    before={a.get_path_name():helper.fingerprint(u,a) for a in actors}
    changed=set(assembly)|set(moves)
    transforms={a:a.get_actor_transform() for a in changed}
    if resume_before_duplication:
        assert out.exists() and not (out/'Applied.json').exists() and not (out/'Failed.json').exists()
        assert json.loads((out/'Before.json').read_text())==before, 'Resume only an unchanged pre-mutation state.'
        assert (out/'BeforeMap.umap').read_bytes()==file.read_bytes()
    else:
        out.mkdir(parents=True)
        (out/'BeforeMap.umap').write_bytes(file.read_bytes())
        (out/'Before.json').write_text(json.dumps(before,indent=2)+'\n')
    assets={}
    for a in assembly:
        for c in a.get_components_by_class(u.MeshComponent):
            mesh=c.static_mesh if isinstance(c,u.StaticMeshComponent) else c.get_editor_property('skeletal_mesh_asset') if isinstance(c,u.SkeletalMeshComponent) else None
            for asset in ([mesh] if mesh else [])+list(c.get_materials()):
                if asset:assets[asset.get_path_name().split('.')[0]]=asset
    assets[sequence.get_path_name().split('.')[0]]=sequence
    def assetfile(name):
        if name.startswith('/Game/'):return root/('Content/'+name[6:]+'.uasset')
        assert name.startswith('/Engine/'), name
        return Path(u.Paths.convert_relative_path_to_full(u.Paths.engine_content_dir()))/(name[8:]+'.uasset')
    source_hashes={name:hashlib.sha256(assetfile(name).read_bytes()).hexdigest() for name in assets}
    created=[];slots=[]
    try:
        for slot,(x,y) in enumerate(CENTRES[1:],2):
            delta=u.Vector(x-8170.,y,0.);mapping={}
            # Singleton duplication avoids relying on batch result ordering.
            for source in assembly:
                copies=sub.duplicate_actors([source],editor.get_editor_world(),u.Vector(0.,0.,0.))
                assert len(copies)==1, source.get_actor_label()
                copy=copies[0];created.append(copy);mapping[source]=copy
                if copy.get_attach_parent_actor():
                    copy.detach_from_actor(u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD)
                copy.set_actor_transform(transforms[source],False,True)
                copy.set_actor_location(source.get_actor_location()+delta,False,True)
                copy.set_actor_label('TShipPreview235/Slot '+str(slot)+'/'+source.get_actor_label()[len(PREFIX):])
                copy.set_folder_path('TShipPreview235/Slot '+str(slot))
                copy.tags=list(copy.tags)+[u.Name('TShipRows235'),u.Name('TShipSlot:'+str(slot))]
            for source,copy in mapping.items():
                parent=source.get_attach_parent_actor()
                if parent:
                    assert parent in mapping
                    copy.attach_to_actor(mapping[parent],u.Name(''),u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
            seq_copy=mapping[sequence_actor]
            copied_data=seq_copy.get_editor_property('default_instance_data')
            assert copied_data and copied_data!=instance, 'Instance data must be private to each actor.'
            copied_data.set_editor_property('transform_origin',u.Transform(location=delta))
            seq_copy.set_editor_property('override_instance_data',True)
            override=u.MovieSceneBindingOverrideData()
            override.set_editor_property('object_binding_id',binding_id)
            override.set_editor_property('object',mapping[pivot])
            override.set_editor_property('overrides_default',True)
            seq_copy.get_editor_property('binding_overrides').set_editor_property('binding_data',[override])
            slots.append({'slot':slot,'centre':[x,y],'parts':len(mapping),'pivot':mapping[pivot].get_path_name(),'sequence_actor':seq_copy.get_path_name()})
        # Move roots only; attached ship/display parts follow their own parent.
        delta=u.Vector(CENTRES[0][0]-8170.,CENTRES[0][1],0.)
        for a in assembly:
            if a.get_attach_parent_actor() not in assembly:a.set_actor_location(a.get_actor_location()+delta,False,True)
        instance.set_editor_property('transform_origin',u.Transform(location=delta))
        sequence_actor.set_editor_property('override_instance_data',True)
        original_overrides.set_editor_property('binding_data',[probe])
        slots.insert(0,{'slot':1,'centre':list(CENTRES[0]),'parts':len(assembly),'pivot':pivot.get_path_name(),'sequence_actor':sequence_actor.get_path_name()})
        for a,delta in moves.items():
            if a.get_attach_parent_actor() not in moves:a.set_actor_location(a.get_actor_location()+delta,False,True)
        untouched=[a for a in actors if a not in changed]
        assert all(helper.fingerprint(u,a)==before[a.get_path_name()] for a in untouched), 'Unexpected change outside displays/desks.'
        assert len(sub.get_all_level_actors())==9407 and len(created)==300
        assert source_hashes=={name:hashlib.sha256(assetfile(name).read_bytes()).hexdigest() for name in assets}
        result={'status':'APPLIED_UNSAVED','original_count':9107,'actor_count':9407,'copied_actors':300,'parts_per_display':60,'rows':2,'columns':3,'slots':slots,'moved_desk_actors':len(moves),'moved_desks':[{'label':a.get_actor_label(),'delta':list(d.to_tuple()),'path':a.get_path_name()} for a,d in moves.items()],'protected_existing_actors':len(untouched),'source_asset_hashes':source_hashes,'all_other_fingerprints_unchanged':True,'new_mechanics':False,'ray_tracing':0}
        (out/'Applied.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    except Exception as error:
        for a in reversed(created):sub.destroy_actor(a)
        for a in changed:
            if a.get_attach_parent_actor() not in changed:a.set_actor_transform(transforms[a],False,True)
        for a in changed:
            if a.get_attach_parent_actor() in changed:a.set_actor_transform(transforms[a],False,True)
        instance.set_editor_property('transform_origin',old_origin)
        sequence_actor.set_editor_property('override_instance_data',old_override)
        original_overrides.set_editor_property('binding_data',original_binding_data)
        (out/'Failed.json').write_text(json.dumps({'error':repr(error),'rollback_existing':all(helper.fingerprint(u,a)==before[a.get_path_name()] for a in actors),'new_actors_after_rollback':len(sub.get_all_level_actors())-9107},indent=2)+'\n')
        raise
