"""Four real-player PIE lighting views; dedicated -RenderOffscreen editor only.

Uses the possessed walker's normal camera/boom and scene postprocess. Only pawn
pose/control direction/FOV change for capture; no light/material/PP edits, map
travel, service interactions, cargo tests or saves. Lead owns engine invocation.
"""
import hashlib
import json
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
import unreal as u

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
SELECTED = ('07_Market_', '14_Engineering_', '17_Lounge_', '19_Operations_')
EXPOSURE_RANGE = 'r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange'
SHOW_FLAGS = ('Lighting', 'DirectLighting', 'DeferredLighting', 'GlobalIllumination', 'SkyLighting', 'DynamicShadows', 'PostProcessing')
PP = ('auto_exposure_method', 'auto_exposure_min_brightness', 'auto_exposure_max_brightness',
      'auto_exposure_bias', 'bloom_intensity', 'vignette_intensity', 'color_saturation', 'scene_color_tint')


def vec(v):
    return [float(v.x), float(v.y), float(v.z)]


def properties(obj, names):
    result = {}
    for name in names:
        try:
            value = obj.get_editor_property(name)
            result[name] = value if isinstance(value, (str, int, float, bool)) else str(value)
        except Exception as error:
            result[name] = 'UNAVAILABLE: ' + str(error)
    return result


def main():
    if '-renderoffscreen' not in u.SystemLibrary.get_command_line().lower():
        raise RuntimeError('Lighting play capture requires a dedicated offscreen editor')
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
    out = root/'Artifacts/Outpost/LightingPlay'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True, exist_ok=False)
    source = root/'Content/OutpostSandbox/L_AsteroidOutpost.umap'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    saved = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_saved_dir()))/'SaveGames'
    def saves():
        return {str(p.relative_to(saved)): hashlib.sha256(p.read_bytes()).hexdigest() for p in saved.rglob('*.sav')} if saved.exists() else {}
    original_saves = saves()
    shots = [r for r in json.loads((root/'Scripts/OutpostWalkthroughShots.json').read_text(encoding='utf-8-sig')) if r[0].startswith(SELECTED)]
    if len(shots) != 4: raise RuntimeError('Expected exactly four named gallery viewpoints')
    # The gallery's Engineering eye position put the live third-person pawn in
    # the workstation. Use its clear entrance aisle; keep the other three views.
    shots = [[name, [4200, -2400, 185], [4200, -3700, 170], fov] if name.startswith('14_Engineering_') else [name, position, target, fov]
             for name, position, target, fov in shots]
    level = u.get_editor_subsystem(u.LevelEditorSubsystem)
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    if editor.get_game_world(): raise RuntimeError('Use a fresh process, not existing PIE')
    if not level.load_level(TARGET): raise RuntimeError('Could not open private outpost')
    u.AutomationLibrary.finish_loading_before_screenshot()
    try:
        import ss_catalog_refresh
        h = ss_catalog_refresh._state.get('handle')
        if h: u.unregister_slate_post_tick_callback(h); ss_catalog_refresh._state['handle'] = None
    except ImportError: pass
    report = {'map': TARGET, 'source_map_sha256': digest, 'images': [], 'errors': [], 'material_parameters': {},
              'scope': 'Possessed-walker PIE lighting with unchanged camera PP/boom/HUD. Staged approximate gallery angles; actual coordinates recorded. Not gameplay/input/performance acceptance.',
              'screenshot_pipeline': 'Ordinary Shot at the existing PIE viewport resolution; no HighResShot, forced LOD, motion-blur override, r.SetRes or new camera. PNG dimensions and reported viewport size retained.'}
    state = {'phase': 'wait', 'start': time.monotonic(), 'index': 0, 'busy': False, 'handle': None, 'stopped': None}

    def material_info(material):
        path = material.get_path_name()
        if path not in report['material_parameters']:
            values = {}
            try:
                for name in u.MaterialEditingLibrary.get_scalar_parameter_names(material):
                    if any(k in str(name).lower() for k in ('intensity em', 'emiss', 'emission', 'gain')):
                        value = material.get_scalar_parameter_value(name) if isinstance(material, u.MaterialInstanceDynamic) else u.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(material, name)
                        values[str(name)] = float(value)
            except Exception as error: values['query_error'] = str(error)
            report['material_parameters'][path] = values
        return path

    def observation():
        pc, pawn, camera = state['pc'], state['pawn'], state['camera']
        manager = pc.player_camera_manager
        eye = manager.get_camera_location()
        row = {'camera_cm': vec(eye), 'camera_rotation': str(manager.get_camera_rotation()),
               'exposure_range_cvar': {EXPOSURE_RANGE: u.SystemLibrary.get_console_variable_int_value(EXPOSURE_RANGE)},
               'show_flag_override_cvars': {name: u.SystemLibrary.get_console_variable_int_value('ShowFlag.'+name) for name in SHOW_FLAGS},
               'show_flag_meaning': '0=forced off, 1=forced on, 2=not overridden; these are not resolved viewport flags. Read-only Show enumeration requested in process log.',
               'actual_fov': manager.get_fov_angle(), 'view_target': pc.get_view_target().get_path_name(), 'viewport_size': list(pc.get_viewport_size()),
               'pawn_cm': vec(pawn.get_actor_location()), 'camera_pp': properties(camera, ('post_process_blend_weight',)),
               'camera_settings': properties(camera.post_process_settings, PP + tuple('override_'+p for p in PP)),
               'camera_pp_unchanged': (camera.post_process_settings.export_text(), camera.post_process_blend_weight) == state['camera_pp'],
               'boom': properties(state['boom'], ('target_arm_length', 'socket_offset', 'do_collision_test')),
               'lights': [], 'display_materials': [], 'postprocess_volumes': []}
        for actor in state['actors']:
            label = actor.get_actor_label()
            if isinstance(actor, u.PostProcessVolume):
                row['postprocess_volumes'].append({'actor': label, **properties(actor, ('enabled', 'unbound', 'priority', 'blend_weight', 'blend_radius')),
                    'settings': properties(actor.settings, PP + tuple('override_'+p for p in PP))})
            for component in actor.get_components_by_class(u.LightComponentBase):
                radius = float(component.get_editor_property('attenuation_radius')) if isinstance(component, u.LocalLightComponent) else 1000000.
                if (component.get_world_location()-eye).length() <= max(2000., radius):
                    row['lights'].append({'actor': label, 'component': component.get_name(), 'class': component.get_class().get_name(),
                        'position': vec(component.get_world_location()), 'actor_hidden': bool(actor.get_editor_property('hidden')), 'component_active': component.is_active(),
                        **properties(component, ('visible', 'hidden_in_game', 'affects_world', 'intensity', 'intensity_units', 'light_color', 'cast_shadows', 'indirect_lighting_intensity', 'volumetric_scattering_intensity', 'lighting_channels'))})
            if (actor.get_actor_location()-eye).length() < 1800 and any(k in label.lower() for k in ('screen', 'holo', 'light', 'lamp', 'signage', 'diagnostic', 'workstation')):
                for component in actor.get_components_by_class(u.StaticMeshComponent):
                    if component.static_mesh:
                        row['display_materials'].append({'actor': label, 'component': component.get_name(),
                            **properties(component, ('visible', 'hidden_in_game')),
                            'materials': [material_info(m) if m else None for m in component.get_materials()]})
        return row

    def begin_view():
        name, position, target, fov = shots[state['index']]
        rotation = u.MathLibrary.find_look_at_rotation(u.Vector(*position), u.Vector(*target))
        pawn = state['pawn']; pawn.character_movement.stop_movement_immediately()
        # Approximate gallery framing: floor-supported pawn and normal boom. Eye Z,
        # rotated socket offset and boom collision remain gameplay-driven, recorded.
        forward = u.MathLibrary.get_forward_vector(rotation)
        distance = float(state['boom'].get_editor_property('target_arm_length'))
        half = pawn.get_component_by_class(u.CapsuleComponent).get_scaled_capsule_half_height()
        pawn.set_actor_location(u.Vector(position[0]+forward.x*distance, position[1]+forward.y*distance, half+3.), False, True)
        state['pc'].set_control_rotation(rotation); state['camera'].set_field_of_view(fov)
        state.update(phase='warm', view_start=time.monotonic(), frames=0, path=out/(name+'.png'))
        u.log('OUTPOST_LIGHTING_PLAY_VIEW '+name)

    def stop():
        if state['phase'] not in ('stop', 'done'):
            state.update(phase='stop', stop_start=time.monotonic())
            for key in ('actors', 'pawn', 'camera', 'boom', 'pc', 'world'): state.pop(key, None)
            level.editor_request_end_play()

    def finish():
        state['phase'] = 'done'
        try:
            report['saved_map_unchanged'] = hashlib.sha256(source.read_bytes()).hexdigest() == digest
            report['save_files_unchanged'] = saves() == original_saves
            report['PIE_stopped'] = not editor.get_game_world()
            if not all(report[k] for k in ('saved_map_unchanged', 'save_files_unchanged', 'PIE_stopped')): report['errors'].append('Preservation or end-play guard failed')
            report['status'] = 'CAPTURED_PIE_LIGHTING_NOT_ACCEPTED' if len(report['images']) == 4 and not report['errors'] else 'FAILED'
            report['finished_utc'] = datetime.now(timezone.utc).isoformat()
            report['post_PIE_grace_seconds'] = time.monotonic()-state['stopped'] if state['stopped'] else 0
            (out/'runtime.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
            (out.parent/'latest.json').write_text(json.dumps({'status': report['status'], 'receipt': str(out/'runtime.json')}, indent=2), encoding='utf-8')
            u.log('OUTPOST_LIGHTING_PLAY_FINISHED '+report['status']+' '+str(out))
        except Exception:
            u.log_error('OUTPOST_LIGHTING_PLAY_FINALIZATION_FAILED '+traceback.format_exc())
        finally:
            u.unregister_slate_post_tick_callback(state['handle'])
            u.EditorPythonScripting.set_keep_python_script_alive(False); u.SystemLibrary.quit_editor()

    def tick(delta):
        if state['busy'] or state['phase'] == 'done': return
        state['busy'] = True
        try:
            now = time.monotonic()
            if state['phase'] == 'stop':
                if not editor.get_game_world():
                    if state['stopped'] is None: state['stopped'] = now
                    if now-state['stopped'] >= 2.: finish()
                elif now-state['stop_start'] > 12.: report['errors'].append('PIE did not stop'); finish()
                return
            if now-state['start'] > 240.: raise RuntimeError('Lighting capture timeout')
            world = editor.get_game_world()
            if not world: return
            if state['phase'] == 'wait':
                pc = u.GameplayStatics.get_player_controller(world, 0); pawn = u.GameplayStatics.get_player_pawn(world, 0)
                if not pc or not isinstance(pawn, u.SSWalker): return
                cameras = [c for c in pawn.get_components_by_class(u.CameraComponent) if c.get_name() == 'WalkCamera']
                booms = [c for c in pawn.get_components_by_class(u.SpringArmComponent) if c.get_name() == 'WalkCameraBoom']
                if len(cameras) != 1 or len(booms) != 1 or cameras[0].get_attach_parent() != booms[0]: raise RuntimeError('Expected one native WalkCamera attached to WalkCameraBoom')
                camera, boom = cameras[0], booms[0]
                state.update(world=world, pc=pc, pawn=pawn, camera=camera, boom=boom, actors=u.GameplayStatics.get_all_actors_of_class(world, u.Actor))
                report['resolved_camera_components'] = {'camera': camera.get_path_name(), 'spring_arm': boom.get_path_name()}
                state['camera_pp'] = (camera.post_process_settings.export_text(), camera.post_process_blend_weight)
                u.log('OUTPOST_LIGHTING_PLAY_READ_ONLY_SHOW_FLAGS')
                u.SystemLibrary.execute_console_command(world, 'Show', pc)
                u.GameplayStatics.set_game_paused(world, False); begin_view(); return
            state['frames'] += 1
            if state['phase'] == 'warm' and state['frames'] >= 90 and now-state['view_start'] >= 6.:
                row = observation()
                if not row['camera_pp_unchanged'] or state['pc'].get_view_target() != state['pawn']: raise RuntimeError('Normal player camera/PP changed')
                name, position, target, fov = shots[state['index']]
                row.update(name=name, requested_camera_cm=position, target_cm=target, requested_fov=fov, png=str(state['path']))
                state['pending'] = row; state['phase'] = 'capture'
                u.SystemLibrary.execute_console_command(world, 'Shot filename="'+str(state['path'])+'" -nosuffix', state['pc'])
            elif state['phase'] == 'capture' and state['path'].is_file():
                data = state['path'].read_bytes()
                if len(data) < 24 or data[:8] != b'\x89PNG\r\n\x1a\n' or data[-8:-4] != b'IEND': return
                dimensions = [int.from_bytes(data[16:20], 'big'), int.from_bytes(data[20:24], 'big')]
                if min(dimensions) <= 0: raise RuntimeError('Invalid native viewport screenshot dimensions')
                state['pending'].update(sha256=hashlib.sha256(data).hexdigest(), resolution=dimensions, matches_reported_viewport_size=dimensions == state['pending']['viewport_size'])
                report['images'].append(state.pop('pending')); state['index'] += 1
                if state['index'] == len(shots): stop()
                else: begin_view()
        except Exception:
            report['errors'].append(traceback.format_exc()); u.log_error(report['errors'][-1]); stop()
        finally: state['busy'] = False
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    state['handle'] = u.register_slate_post_tick_callback(tick)
    level.editor_request_begin_play()


if __name__ == '__main__':
    try: main()
    except Exception:
        u.log_error(traceback.format_exc()); u.EditorPythonScripting.set_keep_python_script_alive(False); u.SystemLibrary.quit_editor()
