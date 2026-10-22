"""Bind four persistent native interaction actors in the isolated review map."""
import json, runpy, shutil, traceback
from pathlib import Path
from datetime import datetime, timezone
WORK=Path(__file__).resolve().parent
API=runpy.run_path(str(WORK/'upgrade_cryo_fit_unreal.py'))
STAGE,MAP,BASE=(API[k] for k in ('STAGE','MAP','BASE'))
require=API['require'];hashes=API['package_hashes']
MANIFEST=WORK.parent/'outputs/Cryo_Comparison/assembly_fit_v4_2.json'

def main(apply=False):
    report={'status':'DRY_RUN_READY','utc':datetime.now(timezone.utc).isoformat(),'apply':apply,'errors':[],'manifest':str(MANIFEST),'actors':[]}
    u=None
    try:
        manifest=json.loads(MANIFEST.read_text())
        for model,x in zip(manifest['models'],(-540,-180,180,540)):
            outlets=[[p[0]*100,-p[1]*100,p[2]*100] for p in model['fit_v4']['nozzle_outlets_blender_m']]
            require(len(outlets)==2,'Expected two physical nozzle outlets')
            report['actors'].append({'label':model['id']+'_CryoInteraction','model':model['id'],'location_cm':[x,0,0],'nozzle_local_cm':outlets,'use_point_cm':[0,130,100],'frost_actor':model['id']+'_Frost'})
        if not apply:return report
        import unreal as u
        require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==STAGE.resolve(),'Isolated stage only')
        require(hasattr(u,'SSCryoChamber') and hasattr(u,'SSCryoPreviewGameMode'),'Compiled native runtime plugin required')
        before=hashes();report['native_before_hashes']=before
        original_map=STAGE/'Content/SpaceSurvival/CryoComparison/Maps/L_CryoComparison.umap'
        recovery=WORK/('pre_interaction_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));recovery.mkdir()
        shutil.copy2(original_map,recovery/original_map.name);report['map_recovery']=str(recovery/original_map.name)
        world=u.EditorLoadingAndSavingUtils.load_map(MAP)
        require(world is not None,'Review map load failed')
        subsystem=u.get_editor_subsystem(u.EditorActorSubsystem)
        actors={a.get_actor_label():a for a in subsystem.get_all_level_actors()}
        require(all(row['label'] not in actors for row in report['actors']),'Interaction actors already exist')
        jet=u.EditorAssetLibrary.load_asset(BASE+'/FX/NS_CryoFreezeJet')
        require(jet is not None,'Compiled cryo jet required')
        for row in report['actors']:
            actor=subsystem.spawn_actor_from_class(u.SSCryoChamber,u.Vector(*row['location_cm']))
            actor.set_actor_label(row['label'])
            actor.set_editor_property('display_name',row['model']+' / Acornaut cryogenic chamber')
            actor.set_editor_property('frost_surfaces',[actors[row['frost_actor']]])
            actor.set_editor_property('jet_system',jet)
            actor.set_editor_property('use_point',u.Vector(*row['use_point_cm']))
            actor.set_editor_property('use_distance',250.)
            for key,point in zip(('left_nozzle','right_nozzle'),row['nozzle_local_cm']):
                comp=actor.get_editor_property(key)
                comp.set_editor_property('relative_location',u.Vector(*point))
                comp.set_editor_property('relative_rotation',u.Rotator(0,0,0))
                comp.set_editor_property('auto_activate',False)
                comp.set_asset(jet)
            capsules=actor.get_components_by_class(u.CapsuleComponent)
            require(len(capsules)==1,'Walk-up chamber needs one collision core')
            row['collision_radius_cm']=capsules[0].get_unscaled_capsule_radius()
            row['collision_half_height_cm']=capsules[0].get_unscaled_capsule_half_height()
        settings=world.get_world_settings()
        report['previous_game_mode']=str(settings.get_editor_property('default_game_mode'))
        settings.set_editor_property('default_game_mode',u.SSCryoPreviewGameMode.static_class())
        starts=[a for a in actors.values() if isinstance(a,u.PlayerStart)]
        require(len(starts)==1,'Expected one review PlayerStart')
        starts[0].set_actor_location(u.Vector(180,480,100),False,True)
        starts[0].set_actor_rotation(u.Rotator(0,-90,0),True)
        require(u.EditorLoadingAndSavingUtils.save_map(world,MAP),'Save failed')
        after=hashes();changed=sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p))
        require(changed==['Content\\SpaceSurvival\\CryoComparison\\Maps\\L_CryoComparison.umap'],'Only owned map may change')
        report.update(status='INTERACTION_MAP_SAVED_PENDING_RUNTIME',native_after_hashes=after,changed_packages=changed,preview_game_mode='/Script/SSCryoRuntime.SSCryoPreviewGameMode',input='WASD/mouse or gamepad; E/controller X interacts')
        return report
    except Exception:
        report['status']='FAILED';report['errors'].append(traceback.format_exc())
        if u:u.log_error(report['errors'][-1])
        return report
    finally:
        (WORK/('CryoInteractionApply.json' if apply else 'CryoInteractionPlan.json')).write_text(json.dumps(report,indent=2)+'\n')
        print('CRYO_INTERACTION_BIND',report['status'],flush=True)
        if u:u.SystemLibrary.quit_editor()

if __name__=='__main__':main(False)
