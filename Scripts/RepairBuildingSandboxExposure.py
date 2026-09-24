"""Inspect or repair only the open authoring sandbox's inherited exposure.

Call run() for a dry run, then run(apply=True) in the same idle editor.
Preserves all vendor maps; records the old settings and backs up the saved sandbox.
The transaction is undoable. Save the current sandbox after visual review.
"""
import datetime
import json
import shutil
from pathlib import Path
import unreal as u

TARGET = '/Game/Blender/Sandbox/BuildingSandbox_20260922'


def run(apply=False):
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    assert world.get_path_name().split('.')[0] == TARGET, 'Wrong map: sandbox only'
    assert not editor.get_game_world(), 'Stop Play before repairing editor settings'
    volumes = u.GameplayStatics.get_all_actors_of_class(world, u.PostProcessVolume)
    assert len(volumes) == 1, 'Inspect unexpected post-process volumes before editing'
    volume = volumes[0]
    assert volume.unbound and volume.enabled and volume.blend_weight == 1
    extended = u.SystemLibrary.get_console_variable_int_value(
        'r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange')
    changes = {
        'override_auto_exposure_method': True,
        'auto_exposure_method': u.AutoExposureMethod.AEM_HISTOGRAM,
        'override_auto_exposure_bias': True,
        'auto_exposure_bias': 0.0,
        'override_auto_exposure_apply_physical_camera_exposure': True,
        'auto_exposure_apply_physical_camera_exposure': False,
        'override_auto_exposure_min_brightness': True,
        'auto_exposure_min_brightness': -5.0 if extended else 0.03,
        'override_auto_exposure_max_brightness': True,
        'auto_exposure_max_brightness': 15.0 if extended else 32.0,
        'override_bloom_method': True,
        'bloom_method': u.BloomMethod.BM_SOG,
        'override_bloom_intensity': True,
        'bloom_intensity': 0.35,
        'override_bloom_size_scale': True,
        'bloom_size_scale': 1.0,
        'override_bloom_threshold': True,
        'bloom_threshold': 1.0,
        'override_color_grading_intensity': True,
        'color_grading_intensity': 0.0,
        'override_white_temp': True,
        'white_temp': 6500.0,
        'override_white_tint': True,
        'white_tint': 0.0,
        'override_scene_color_tint': True,
        'scene_color_tint': u.LinearColor(1, 1, 1, 1),
    }
    settings = volume.settings
    sun = u.GameplayStatics.get_all_actors_of_class(world, u.DirectionalLight)
    sky = u.GameplayStatics.get_all_actors_of_class(world, u.SkyAtmosphere)
    assert len(sun) == 1 and len(sky) == 1, 'Inspect unexpected environment actors'
    light = sun[0].get_component_by_class(u.DirectionalLightComponent)
    atmosphere = sky[0].get_component_by_class(u.SkyAtmosphereComponent)
    default_rayleigh = u.get_default_object(u.SkyAtmosphereComponent).rayleigh_scattering_scale
    report = {'map': TARGET, 'apply': apply, 'extended_ev_range': bool(extended),
              'before': {k: str(settings.get_editor_property(k)) for k in changes},
              'proposed': {k: str(v) for k, v in changes.items()},
              'saved': False}
    report['environment_before'] = {'use_temperature': light.use_temperature,
        'temperature': light.temperature, 'rayleigh_scale': atmosphere.rayleigh_scattering_scale}
    report['environment_proposed'] = {'use_temperature': False, 'rayleigh_scale': default_rayleigh}
    blendables = settings.weighted_blendables
    kept = [b for b in blendables.array
            if not b.object or 'MI_DepthFog_PostProcessVolume' not in b.object.get_path_name()]
    report['removed_depth_fog_blendables'] = len(blendables.array) - len(kept)
    if apply:
        root = Path(u.Paths.project_dir())
        out = root / '.agent/local/SandboxExposure' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        out.mkdir(parents=True, exist_ok=False)
        shutil.copy2(root / ('Content/' + TARGET[6:] + '.umap'), out / 'Before.umap')
        with u.ScopedEditorTransaction('Repair building sandbox exposure'):
            volume.modify()
            for key, value in changes.items():
                settings.set_editor_property(key, value)
            blendables.array = kept
            settings.weighted_blendables = blendables
            volume.set_editor_property('settings', settings)
            light.modify()
            light.set_editor_property('use_temperature', False)
            atmosphere.modify()
            atmosphere.set_editor_property('rayleigh_scattering_scale', default_rayleigh)
        report['after'] = {k: str(volume.settings.get_editor_property(k)) for k in changes}
        report['backup'] = str(out)
        (out / 'repair.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))
    return report
