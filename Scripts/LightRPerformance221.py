"""Local canopy stage lights: readable key, cyan and violet accents, RT off."""
import hashlib,json,math
from pathlib import Path
EXPECTED='658311702b68a6d757bafadccaffde7194403c1514119079ab42e53be779a4aa'
SPECS=(('Front key',(3410.,2770.,375.),(3310.,2660.,150.),2300.,(.80,.91,1.)),
       ('Cyan rim',(3110.,2500.,374.),(3270.,2600.,150.),1400.,(.10,.80,1.)),
       ('Violet rim',(3360.,2420.,375.),(3280.,2610.,150.),700.,(.55,.20,1.)))
def apply(u,fingerprint):
    root=Path(u.Paths.project_dir()).resolve();file=root/'Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap'
    out=root/'.agent/local/StationRefinement/RPerformance221'
    assert not out.exists() and hashlib.sha256(file.read_bytes()).hexdigest()==EXPECTED
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages() and not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    assert u.SystemLibrary.get_console_variable_int_value('r.RayTracing')==0
    sub=u.get_editor_subsystem(u.EditorActorSubsystem);actors=list(sub.get_all_level_actors());assert len(actors)==9104
    before={a.get_path_name():fingerprint(u,a) for a in actors}
    out.mkdir(parents=True);(out/'MapBefore.umap').write_bytes(file.read_bytes());(out/'Before.json').write_text(json.dumps(before,indent=2)+'\n')
    added=[]
    with u.ScopedEditorTransaction('Light the R performance canopy'):
        for label,pos,target,lumens,color in SPECS:
            a=sub.spawn_actor_from_class(u.RectLight,u.Vector(*pos));assert a
            a.set_actor_label('R/Performance/Lighting/'+label);a.set_folder_path('R/Performance/Lighting');a.tags=[u.Name('RPerformance221')]
            dx,dy,dz=[target[i]-pos[i] for i in range(3)]
            a.set_actor_rotation(u.Rotator(pitch=math.degrees(math.atan2(dz,math.hypot(dx,dy))),yaw=math.degrees(math.atan2(dy,dx))),False)
            c=a.get_component_by_class(u.RectLightComponent);c.set_mobility(u.ComponentMobility.MOVABLE)
            for name,value in {'intensity_units':u.LightUnits.LUMENS,'intensity':lumens,'source_width':120.,'source_height':35.,'attenuation_radius':460.,'cast_shadows':True}.items():c.set_editor_property(name,value)
            c.set_light_color(u.LinearColor(*color,1.),False)
            added.append({'path':a.get_path_name(),'label':a.get_actor_label(),'position':list(pos),'target':list(target),'lumens':lumens,'color':list(color),'radius':460.})
    after={a.get_path_name():fingerprint(u,a) for a in sub.get_all_level_actors()}
    assert all(after.get(k)==v for k,v in before.items()) and len(after)==9107
    assert u.EditorLevelLibrary.save_current_level()
    report={'map_before_sha256':EXPECTED,'map_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'actor_count':len(after),'protected_actors':len(before),'added':added,'status':'SAVED_NATIVE_REVIEW_PENDING','ray_tracing':0}
    (out/'MapAfter.umap').write_bytes(file.read_bytes());(out/'Receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
