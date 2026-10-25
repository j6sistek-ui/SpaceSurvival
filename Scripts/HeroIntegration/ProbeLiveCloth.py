"""Live numerical cloth check with no screenshots or asset/map/profile writes."""
import hashlib
import json
import sys
import time
import traceback
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / '.agent/local/HeroIntegration_20261020'
sys.path.insert(0, str(ROOT / 'Scripts'))
from StationReviewProfile import verify_before_play

MAP = '/Game/SpaceSurvival/Licensed/CharacterStudio/L_CharacterStudio'
lvl = u.get_editor_subsystem(u.LevelEditorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
assert lvl.load_level(MAP)
map_file = ROOT / 'Content/SpaceSurvival/Licensed/CharacterStudio/L_CharacterStudio.umap'
before = hashlib.sha256(map_file.read_bytes()).hexdigest()
actor = actors.spawn_actor_from_class(u.SkeletalMeshActor, u.Vector())
actor.set_actor_label('HeroClothNumericalProbe')
c = actor.skeletal_mesh_component
mesh = u.load_asset('/Game/SpaceSurvival/Licensed/PlayableHeroes_20261020/Cloth/SK_Cloth')
clip = u.load_asset('/Game/SpaceSurvival/Licensed/PlayableHeroes_20261020/Cloth/A_Jog')
c.set_skeletal_mesh_asset(mesh)
c.set_editor_property('visibility_based_anim_tick_option', u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
c.set_editor_property('wait_for_parallel_cloth_task', True)
c.set_component_tick_enabled(True)
c.set_forced_lod(1)
c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
c.set_editor_property('animation_data', u.SingleAnimationPlayData(anim_to_play=clip, saved_looping=True, saved_playing=True, saved_position=0., saved_play_rate=1.))
REPORT = {'profile_guard': verify_before_play(), 'samples': [], 'errors': [], 'screenshots': False}
state = {'start': time.monotonic(), 'frames': 0, 'handle': None, 'stopping': False, 'physics_enabled': False}


def finish():
    REPORT['map_unchanged'] = hashlib.sha256(map_file.read_bytes()).hexdigest() == before
    REPORT['success'] = len(REPORT['samples']) >= 8 and not REPORT['errors'] and REPORT['map_unchanged']
    (OUT / 'LiveCloth.json').write_text(json.dumps(REPORT, indent=2))
    u.unregister_slate_post_tick_callback(state['handle'])
    u.EditorPythonScripting.set_keep_python_script_alive(False)
    print('HERO_LIVE_CLOTH', REPORT['success'], len(REPORT['samples']), REPORT['errors'], flush=True)
    u.SystemLibrary.quit_editor()


def tick(dt):
    try:
        world = editor.get_game_world()
        if state['stopping']:
            if not world:
                finish()
            return
        if time.monotonic() - state['start'] > 45:
            raise RuntimeError('Live cloth numerical timeout')
        if not world:
            return
        if not state['physics_enabled']:
            REPORT['cloth_physics_before'] = u.SystemLibrary.get_console_variable_int_value('p.ClothPhysics')
            u.SystemLibrary.execute_console_command(world, 'p.ClothPhysics 1')
            state['physics_enabled'] = True
        state['frames'] += 1
        if state['frames'] % 15:
            return
        found = next((a for a in u.GameplayStatics.get_all_actors_of_class(world, u.SkeletalMeshActor)
                      if a.get_actor_label() == 'HeroClothNumericalProbe'), None)
        assert found
        sample = json.loads(u.SSPlayableHeroTools.read_cloth_simulation(found.skeletal_mesh_component))
        if not sample['success']:
            if state['frames'] > 360:
                raise RuntimeError(str(sample))
            return
        REPORT['samples'].append(sample)
        if len(REPORT['samples']) >= 12:
            state['stopping'] = True
            lvl.editor_request_end_play()
    except Exception:
        REPORT['errors'].append(traceback.format_exc())
        state['stopping'] = True
        lvl.editor_request_end_play()


u.EditorPythonScripting.set_keep_python_script_alive(True)
state['handle'] = u.register_slate_post_tick_callback(tick)
lvl.editor_request_begin_play()
