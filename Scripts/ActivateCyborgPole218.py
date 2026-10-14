"""Fit the existing rigged Cyborg and pole clip to the owner-created R stage.

One guarded application. Preserve the raw imported Cyborg, room design and all
other residents. Joy stands beside the pole while the first dancer is reviewed.
"""
import hashlib, json
from pathlib import Path
MAP='/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
EXPECTED='08d2231afc24a7ce8ac97dae6f08cec23584a16e3d76514e07303d4de03e0ea2'
CYB='/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/Cyborg'
JOY='/Game/SpaceSurvival/Licensed/StationAssets/JoyLightBlue117'
def fingerprint(u,a):
    row={'label':a.get_actor_label(),'class':a.get_class().get_name(),'transform':a.get_actor_transform().export_text(),'hidden':bool(a.hidden),'collision':a.get_actor_enable_collision(),'tags':list(map(str,a.tags)),'components':[]}
    for c in a.get_components_by_class(u.MeshComponent):
        part={'name':c.get_name(),'transform':c.get_world_transform().export_text(),'materials':[m.get_path_name() if m else None for m in c.get_materials()],'visible':c.is_visible(),'hidden':c.get_editor_property('hidden_in_game'),'collision':str(c.get_collision_enabled())}
        if isinstance(c,u.SkeletalMeshComponent):
            mesh=c.get_editor_property('skeletal_mesh_asset')
            data=c.get_editor_property('animation_data')
            part.update(mesh=mesh.get_path_name() if mesh else None,animation=data.export_text(),mode=str(c.get_editor_property('animation_mode')))
        elif isinstance(c,u.StaticMeshComponent):part['mesh']=c.static_mesh.get_path_name() if c.static_mesh else None
        row['components'].append(part)
    return row
def animation(u,c,path):
    anim=u.load_asset(path);assert anim and anim.get_editor_property('skeleton')==c.get_editor_property('skeletal_mesh_asset').skeleton
    c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
    data=c.get_editor_property('animation_data')
    for key,value in {'anim_to_play':anim,'saved_looping':True,'saved_playing':True,'saved_position':0.,'saved_play_rate':1.}.items():data.set_editor_property(key,value)
    c.set_editor_property('animation_data',data)
def apply(u):
    root=Path(u.Paths.project_dir()).resolve();file=root/'Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap'
    out=root/'.agent/local/StationRefinement/CyborgPole218'
    assert not out.exists(),'Never replay the adopted placement.'
    assert hashlib.sha256(file.read_bytes()).hexdigest()==EXPECTED
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages() and not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    assert u.SystemLibrary.get_console_variable_int_value('r.RayTracing')==0
    sub=u.get_editor_subsystem(u.EditorActorSubsystem);actors=list(sub.get_all_level_actors());assert len(actors)==9103
    by_label={a.get_actor_label():a for a in actors}
    labels=['HomeHub/Residents/Joy']+['HomeHub/Residents/Pole/'+n for n in ('Shaft','Floor mount','Floor collar','Ceiling mount','Ceiling collar')]
    assert all(n in by_label for n in labels)
    assert not any(c.get_editor_property('skeletal_mesh_asset') and c.get_editor_property('skeletal_mesh_asset').get_path_name().startswith(CYB+'/Rig/SK_Cyborg.') for a in actors for c in a.get_components_by_class(u.SkeletalMeshComponent)),'Inspect an existing rigged Cyborg rather than duplicating it.'
    pole=by_label[labels[1]];p=pole.get_actor_location();assert abs(p.x-3239.000947689117)<.01 and abs(p.y-2594.967386597775)<.01
    mesh=u.load_asset(CYB+'/Rig/SK_Cyborg');clip=u.load_asset(CYB+'/Role/A_Cyborg_PoleHipCircle');idle=u.load_asset(JOY+'/Animations/A_Joy_Idle')
    assert mesh and clip and idle and clip.get_editor_property('skeleton')==mesh.skeleton
    out.mkdir(parents=True)
    (out/'MapBefore.umap').write_bytes(file.read_bytes())
    before={a.get_path_name():fingerprint(u,a) for a in actors};(out/'Before.json').write_text(json.dumps(before,indent=2)+'\n')
    report={'status':'PREPARED','map_before_sha256':EXPECTED,'allowed_existing':[by_label[n].get_path_name() for n in labels],'clip':clip.get_path_name(),'placement_reason':'Owner R stage retained; no rigged Cyborg exists in saved map. Reuse the canonical rigged asset rather than the raw imported duplicate.','source_assets':{}}
    for asset in (mesh,clip,idle):
        f=root/'Content'/(asset.get_path_name().split('.')[0].removeprefix('/Game/')+'.uasset');report['source_assets'][str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
    (out/'Receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    with u.ScopedEditorTransaction('Activate existing Cyborg pole practice in R'):
        joy=by_label[labels[0]];joy.modify();joy.set_actor_location(u.Vector(3350.,2710.,20.5),False,True)
        body=joy.get_component_by_class(u.SkeletalMeshComponent);body.modify();animation(u,body,idle.get_path_name())
        mount_z={'Floor mount':21.5,'Floor collar':25.,'Ceiling mount':390.,'Ceiling collar':386.5}
        for name,z in mount_z.items():
            a=by_label['HomeHub/Residents/Pole/'+name];a.modify();a.set_actor_location(u.Vector(p.x,p.y,z),False,True)
        pole.modify();pole.set_actor_location(u.Vector(p.x,p.y,206.),False,True);pole.set_actor_scale3d(u.Vector(.045,.045,3.68))
        cy=sub.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(p.x,p.y,20.5));assert cy
        cy.set_actor_label('R/Performance/Cyborg girl');cy.set_folder_path('R/Performance');cy.tags=[u.Name('CyborgPole218')]
        cy.set_actor_rotation(u.Rotator(yaw=-50.),False)
        c=cy.skeletal_mesh_component;c.set_skeletal_mesh_asset(mesh);animation(u,c,clip.get_path_name())
        c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    after={a.get_path_name():fingerprint(u,a) for a in sub.get_all_level_actors()}
    changed=[k for k,v in before.items() if k not in report['allowed_existing'] and after.get(k)!=v]
    assert not changed,changed[:10]
    assert len(after)==9104
    for f,h in report['source_assets'].items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h
    report.update(status='PLACED_UNSAVED_NATIVE_REVIEW_PENDING',new_actor=cy.get_path_name(),protected_actors=len(before)-len(labels),outside_changes=changed,actor_count=len(after))
    (out/'After.json').write_text(json.dumps(after,indent=2)+'\n');(out/'Receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
def save(u):
    root=Path(u.Paths.project_dir()).resolve();out=root/'.agent/local/StationRefinement/CyborgPole218';report=json.loads((out/'Receipt.json').read_text())
    assert report['status']=='PLACED_UNSAVED_NATIVE_REVIEW_PENDING'
    assert u.EditorLevelLibrary.save_current_level()
    file=root/'Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap'
    report.update(status='SAVED_NATIVE_REVIEW_PENDING',map_sha256=hashlib.sha256(file.read_bytes()).hexdigest())
    (out/'MapAfter.umap').write_bytes(file.read_bytes());(out/'Receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
