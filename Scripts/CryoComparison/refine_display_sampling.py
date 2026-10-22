"""Keep three shared display textures resident and frame the physical screen detail."""
from pathlib import Path
import json,traceback
import unreal as u
WORK=Path(__file__).resolve().parent
BASE='/Game/SpaceSurvival/CryoComparison'
r={'status':'FAILED','textures':[]}
try:
    assert Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==(WORK/'CryoStage').resolve()
    world=u.EditorLoadingAndSavingUtils.load_map(BASE+'/Maps/L_CryoComparison')
    assert world
    for name in ('Status','Holo','ConsoleHolo'):
        tex=u.EditorAssetLibrary.load_asset(BASE+'/Textures/T_Cryo_'+name)
        assert tex
        tex.set_editor_property('lod_group',u.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property('never_stream',True)
        tex.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_SHARPEN4)
        assert u.EditorAssetLibrary.save_loaded_asset(tex,False)
        r['textures'].append({'name':name,'resolution':[tex.blueprint_get_size_x(),tex.blueprint_get_size_y()],'never_stream':True})
    camera=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='DETAIL_D_Consoles')
    position=u.Vector(440,230,110)
    target=u.Vector(441,74,28)
    camera.set_actor_location_and_rotation(position,u.MathLibrary.find_look_at_rotation(position,target),False,False)
    camera.get_component_by_class(u.CameraComponent).set_field_of_view(34)
    assert u.EditorLoadingAndSavingUtils.save_map(world,BASE+'/Maps/L_CryoComparison')
    r['status']='DISPLAY_SAMPLING_SAVED_PENDING_CAPTURE'
except Exception:
    r['error']=traceback.format_exc()
    u.log_error(r['error'])
finally:
    (WORK/'CryoDisplaySampling.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
    u.SystemLibrary.quit_editor()
