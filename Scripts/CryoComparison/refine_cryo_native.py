"""Bounded revision of this task's own stage packages; never owner project."""
from pathlib import Path
import json
import traceback
import unreal as u

WORK = Path(__file__).resolve().parent
BASE = '/Game/SpaceSurvival/CryoComparison'
report = {'status': 'FAILED', 'textures': [], 'mesh_actor_count': 0}
try:
    assert Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == (WORK / 'CryoStage').resolve()
    assert u.EditorLoadingAndSavingUtils.load_map(BASE + '/Maps/L_CryoComparison')
    for name, size in {'Status':(1024,2048),'Console':(2048,1024),'Holo':(1024,2048),'Frost':(1024,2048),'Mist':(1024,1024)}.items():
        tex = u.EditorAssetLibrary.load_asset(BASE + '/Textures/T_Cryo_' + name)
        assert u.EditorAssetLibrary.get_metadata_tag(tex, 'CryoModelID') == 'Shared'
        tex.set_editor_property('power_of_two_mode', u.TexturePowerOfTwoSetting.RESIZE_TO_SPECIFIC_RESOLUTION)
        tex.set_editor_property('resize_during_build_x',size[0])
        tex.set_editor_property('resize_during_build_y',size[1])
        tex.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
        tex.set_editor_property('never_stream',False)
        assert u.EditorAssetLibrary.save_loaded_asset(tex,False)
        report['textures'].append({'asset':tex.get_path_name(),'build_size':size,'source_pixels_unchanged':True})
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if isinstance(actor,u.StaticMeshActor):
            mesh=actor.get_component_by_class(u.StaticMeshComponent).get_editor_property('static_mesh')
            if mesh and mesh.get_path_name().startswith(BASE+'/Meshes/'):
                assert u.EditorAssetLibrary.get_metadata_tag(mesh,'CryoAuthoringVersion') == 'CryoComparison_20261021_v1'
                actor.set_actor_scale3d(u.Vector(1,-1,1))
                report['mesh_actor_count']+=1
    assert report['mesh_actor_count']==52
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert u.EditorLoadingAndSavingUtils.save_map(world,BASE+'/Maps/L_CryoComparison')
    report['status']='NATIVE_REFINEMENT_SAVED_PENDING_RENDER'
except Exception:
    report['error']=traceback.format_exc()
    u.log_error(report['error'])
finally:
    (WORK/'CryoNativeRefinement.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.SystemLibrary.quit_editor()
