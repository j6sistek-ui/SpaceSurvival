"""Inspect all four actual player bodies and the existing wardrobe in a guarded private Play session."""
import hashlib
import json
import math
import sys
import time
import traceback
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / '.agent/local/HeroIntegration_20261020/GameReviewFinal'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'Scripts'))
from StationReviewProfile import verify_before_play

lvl = u.get_editor_subsystem(u.LevelEditorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
MAP = '/Game/SpaceSurvival/Maps/Survival'
assert lvl.load_level(MAP)
map_file = ROOT / 'Content/SpaceSurvival/Maps/Survival.umap'
map_sha = hashlib.sha256(map_file.read_bytes()).hexdigest()
camera = u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(u.CameraActor, u.Vector())
camera.set_actor_label('PlayableHeroInspectionCamera')
REPORT = {'profile_guard': verify_before_play(), 'shots': [], 'bodies': {}, 'cloth_samples': [], 'errors': [],
          'view': 'Actual player and selector, with a temporary body inspection camera', 'map_saved': False}
HEROES = [('EX7', 'EX7Hero'), ('Green', 'GreenHero'), ('Blue', 'BlueHero'), ('Cloth', 'ClothHero')]
state = {'phase': 'wait', 'start': time.monotonic(), 'hero': 0, 'frames': 0, 'view': 'body', 'busy': False, 'handle': None}


def persist():
    (OUT / 'Runtime.json').write_text(json.dumps(REPORT, indent=2))


def ready(path):
    return path.exists() and path.stat().st_size > 200 and path.read_bytes()[-8:-4] == b'IEND'


def begin_view(world):
    key, identifier = HEROES[state['hero']]
    menu = state['view'] == 'selector'
    pc = u.GameplayStatics.get_player_controller(world, 0)
    if menu:
        pc.set_view_target_with_blend(u.GameplayStatics.get_player_pawn(world, 0), 0, u.ViewTargetBlendFunction.VT_BLEND_LINEAR, 0, False)
    assert u.SSPlayableHeroTools.begin_game_review(world, identifier, menu), (key, state['view'])
    pawn = u.GameplayStatics.get_player_pawn(world, 0)
    component = pawn.get_component_by_class(u.SkeletalMeshComponent)
    mesh = component.get_editor_property('skeletal_mesh_asset')
    assert mesh.get_path_name().endswith('/SK_' + key + '.SK_' + key), mesh.get_path_name()
    component.set_editor_property('wait_for_parallel_cloth_task', True)
    component.set_editor_property('visibility_based_anim_tick_option', u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    REPORT['bodies'][key] = {'mesh': mesh.get_path_name(), 'materials': [str(component.get_material(i).get_path_name()) for i in range(component.get_num_materials())]}
    u.GameplayStatics.set_game_paused(world, False)
    REPORT.setdefault('clock', []).append({'hero': key, 'view': state['view'], 'game_time': u.GameplayStatics.get_time_seconds(world), 'paused': u.GameplayStatics.is_game_paused(world)})
    if not menu:
        if 'body_spot' not in state:
            state['body_spot'] = pawn.get_actor_location()
        pawn.set_actor_location_and_rotation(state['body_spot'], u.Rotator(), False, False)
        cam = next(a for a in u.GameplayStatics.get_all_actors_of_class(world, u.CameraActor)
                   if a.get_actor_label() == 'PlayableHeroInspectionCamera')
        target = pawn.get_actor_location()
        position = target + pawn.get_actor_forward_vector() * 560 + u.Vector(0, 0, 15)
        cam.set_actor_location_and_rotation(position, u.MathLibrary.find_look_at_rotation(position, target), False, False)
        cam.get_component_by_class(u.CameraComponent).set_field_of_view(40)
        pc.set_view_target_with_blend(cam, 0, u.ViewTargetBlendFunction.VT_BLEND_LINEAR, 0, False)
    state.update(phase='warm', frames=0, component=component, path=OUT / (key + '_' + state['view'] + '.png'))
    if menu and not state.get('selector_settled', False):
        pc.set_view_target_with_blend(pawn, 0, u.ViewTargetBlendFunction.VT_BLEND_LINEAR, 0, False)
        state.update(phase='settle_selector', frames=0, selector_settled=True)
    persist()


def stop():
    state['phase'] = 'stop'
    lvl.editor_request_end_play()


def finish():
    REPORT['map_unchanged'] = hashlib.sha256(map_file.read_bytes()).hexdigest() == map_sha
    REPORT['core_integration_pass'] = len(REPORT['shots']) == 8 and not REPORT['errors'] and REPORT['map_unchanged']
    valid = [row for row in REPORT['cloth_samples'] if row.get('success')]
    REPORT['cloth_simulation_pass'] = len(valid) >= 3
    REPORT['success'] = REPORT['core_integration_pass'] and REPORT['cloth_simulation_pass']
    persist()
    u.unregister_slate_post_tick_callback(state['handle'])
    u.EditorPythonScripting.set_keep_python_script_alive(False)
    print('HERO_GAME_REVIEW', REPORT['core_integration_pass'], REPORT['cloth_simulation_pass'], REPORT['errors'], flush=True)
    u.SystemLibrary.quit_editor()


def tick(dt):
    if state['busy']:
        return
    state['busy'] = True
    try:
        world = editor.get_game_world()
        if state['phase'] == 'stop':
            if not world:
                finish()
            return
        if time.monotonic() - state['start'] > 420:
            raise RuntimeError('Private game review timed out')
        if not world:
            return
        if state['phase'] == 'wait':
            if not u.GameplayStatics.get_player_controller(world, 0):
                return
            if u.GameplayStatics.get_time_seconds(world) < 1.:
                return
            for cmd in ['r.ScreenPercentage 100', 'r.MotionBlurQuality 0', 'r.DepthOfFieldQuality 0']:
                u.SystemLibrary.execute_console_command(world, cmd)
            begin_view(world)
            return
        state['frames'] += 1
        if state['phase'] == 'settle_selector':
            if state['frames'] >= 30:
                begin_view(world)
            return
        if HEROES[state['hero']][0] == 'Cloth' and state['frames'] >= 30 and state['frames'] % 15 == 0:
            REPORT['cloth_samples'].append(json.loads(u.SSPlayableHeroTools.read_cloth_simulation(state['component'])))
        if state['phase'] == 'warm' and state['frames'] >= 90:
            snapshot = json.loads(u.SSPlayableHeroTools.read_cloth_simulation(state['component']))
            assert snapshot.get('animation_asset') and snapshot['animation_asset'] != 'None', snapshot
            REPORT['clock'].append({'hero': HEROES[state['hero']][0], 'view': state['view'], 'game_time': u.GameplayStatics.get_time_seconds(world), 'paused': u.GameplayStatics.is_game_paused(world), 'animation_position': state['component'].get_position()})
            state['phase'] = 'capture'
            u.SystemLibrary.execute_console_command(world, 'HighResShot 1600x900 filename="' + str(state['path']).replace('\\', '/') + '"')
        elif state['phase'] == 'capture' and ready(state['path']):
            REPORT['shots'].append({'hero': HEROES[state['hero']][0], 'view': state['view'], 'image': str(state['path']),
                                    'sha256': hashlib.sha256(state['path'].read_bytes()).hexdigest()})
            if state['view'] == 'body':
                state['view'] = 'selector'
            else:
                state['hero'] += 1
                state['view'] = 'body'
                state['selector_settled'] = False
            persist()
            if state['hero'] == len(HEROES):
                stop()
            else:
                begin_view(world)
    except Exception:
        REPORT['errors'].append(traceback.format_exc())
        u.log_error(REPORT['errors'][-1])
        persist()
        stop()
    finally:
        state['busy'] = False


u.EditorPythonScripting.set_keep_python_script_alive(True)
state['handle'] = u.register_slate_post_tick_callback(tick)
lvl.editor_request_begin_play()
