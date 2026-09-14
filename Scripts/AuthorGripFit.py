"""Import only the separate grip-fit mesh; optional unsaved native comparison."""
from pathlib import Path
import hashlib
import json
import math
import runpy
import sys
import time
import traceback
import unreal as u


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'ContentSource/AcornShipGripFit'
# Permit only the shared helper's exact uniform LF/CRLF text representations.
matches = runpy.run_path(str(ROOT / 'Scripts/SourceDigests.py'))['matches']
PATH = '/Game/SpaceSurvival/Meshes/SM_AcornShipGripFit'
VERSION = 'UpperGripsMeasured1'
LIB = u.EditorAssetLibrary


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_source():
    report = json.loads((SOURCE / 'Report.json').read_text(encoding='utf-8'))
    for row in report['outputs']:
        assert matches(SOURCE / row['file'], row['sha256']), row['file']
    for path, digest in report['protected_sha256'].items():
        assert matches(ROOT / path, digest), path
    assert report['unchanged_authored_parts'] == 181
    return (report, sha(SOURCE / 'AcornShipGripFit.obj'))

def validate(mesh, report, digest):
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    assert isinstance(mesh, u.StaticMesh)
    assert LIB.get_metadata_tag(mesh, 'SSGripFitVersion') == VERSION
    assert matches(SOURCE / 'AcornShipGripFit.obj', LIB.get_metadata_tag(mesh, 'SSGripFitSourceSHA256'))
    assert mesh.get_num_sections(0) == 9 and editor.get_lod_count(mesh) == 1
    assert editor.get_simple_collision_count(mesh) == 0 and all((not editor.is_section_collision_enabled(mesh, 0, i) for i in range(9)))
    instance = mesh.get_editor_property('body_setup').get_editor_property('default_instance')
    assert instance.get_editor_property('collision_enabled') == u.CollisionEnabled.NO_COLLISION
    bounds = mesh.get_bounds()
    actual = [
        [getattr(bounds.origin, a) - getattr(bounds.box_extent, a) for a in ('x', 'y', 'z')],
        [getattr(bounds.origin, a) + getattr(bounds.box_extent, a) for a in ('x', 'y', 'z')],
    ]
    assert all((abs(actual[e][a] - report['bounds_cm'][e][a]) < 0.03 for e in range(2) for a in range(3)))
    expected = {item['name']: '/Game/SpaceSurvival/Materials/M_AcornV2_' + item['name'].removeprefix('AC01_') for item in report['materials']}
    slots = []
    for slot in mesh.get_editor_property('static_materials'):
        name = str(slot.get_editor_property('imported_material_slot_name'))
        material = slot.get_editor_property('material_interface')
        assert material.get_path_name().split('.')[0] == expected[name]
        slots.append({'slot': name, 'material': material.get_path_name()})
    return {
        'mesh': mesh.get_path_name(),
        'bounds_cm': actual,
        'triangles': mesh.get_num_triangles(0),
        'vertices': editor.get_number_verts(mesh, 0),
        'material_sections': 9,
        'collision_enabled': 'NoCollision',
        'slots': slots,
    }

def import_candidate(report, digest):
    mesh = LIB.load_asset(PATH)
    if mesh:
        validate(mesh, report, digest)
        return mesh
    options = u.FbxImportUI()
    for key, value in {
        'import_mesh': True,
        'import_as_skeletal': False,
        'import_materials': False,
        'import_textures': False,
        'mesh_type_to_import': u.FBXImportType.FBXIT_STATIC_MESH,
    }.items():
        options.set_editor_property(key, value)
    data = options.get_editor_property('static_mesh_import_data')
    for key, value in {
        'combine_meshes': True,
        'auto_generate_collision': False,
        'generate_lightmap_u_vs': False,
        'import_uniform_scale': 1.0,
        'convert_scene': False,
        'force_front_x_axis': False,
        'normal_import_method': u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS,
    }.items():
        data.set_editor_property(key, value)
    task = u.AssetImportTask()
    for key, value in {
        'filename': str(SOURCE / 'AcornShipGripFit.obj'),
        'destination_path': '/Game/SpaceSurvival/Meshes',
        'destination_name': 'SM_AcornShipGripFit',
        'automated': True,
        'replace_existing': False,
        'save': False,
        'options': options,
        'factory': u.FbxFactory(),
    }.items():
        task.set_editor_property(key, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    objects = [LIB.load_asset(p) for p in task.get_editor_property('imported_object_paths')]
    meshes = [o for o in objects if isinstance(o, u.StaticMesh)]
    assert len(meshes) == 1
    mesh = meshes[0]
    assert mesh.get_path_name().split('.')[0] == PATH, 'Unexpected import destination; refuse renaming existing content'
    expected = {item['name']: u.load_asset('/Game/SpaceSurvival/Materials/M_AcornV2_' + item['name'].removeprefix('AC01_')) for item in report['materials']}
    for i, slot in enumerate(mesh.get_editor_property('static_materials')):
        name = str(slot.get_editor_property('imported_material_slot_name'))
        assert name in expected and expected[name]
        mesh.set_material(i, expected[name])
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    editor.remove_collisions(mesh)
    for section in range(mesh.get_num_sections(0)):
        editor.enable_section_collision(mesh, False, 0, section)
    body = mesh.get_editor_property('body_setup')
    instance = body.get_editor_property('default_instance')
    instance.set_editor_property('collision_profile_name', 'NoCollision')
    instance.set_editor_property('collision_enabled', u.CollisionEnabled.NO_COLLISION)
    body.set_editor_property('default_instance', instance)
    LIB.set_metadata_tag(mesh, 'SSGripFitVersion', VERSION)
    LIB.set_metadata_tag(mesh, 'SSGripFitSourceSHA256', digest)
    assert LIB.save_loaded_asset(mesh, only_if_is_dirty=False)
    return mesh

def preview(mesh, record, protected, matched=False, cases_override=None, receipt_name=None):
    u.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    for command in ('r.MotionBlurQuality 0', 'r.ScreenPercentage 100', 'r.AntiAliasingMethod 2'):
        u.SystemLibrary.execute_console_command(world, command)
    ship = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, 0, 0))
    visual = ship.get_component_by_class(u.StaticMeshComponent)
    visual.set_mobility(u.ComponentMobility.MOVABLE)
    visual.set_static_mesh(mesh)
    visual.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    character = actors.spawn_actor_from_class(u.SkeletalMeshActor, u.Vector(-15, 0, 72), u.Rotator(pitch=0, yaw=-90, roll=0))
    character.set_actor_scale3d(u.Vector(1.5, 1.5, 1.5))
    hero = character.get_component_by_class(u.SkeletalMeshComponent)
    hero.set_skeletal_mesh_asset(u.load_asset('/Game/SpaceSurvival/Character/SK_AcornautTailV2'))
    hero.set_update_animation_in_editor(True)
    hero.set_editor_property('visibility_based_anim_tick_option', u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    hero.set_animation_mode(u.AnimationMode.ANIMATION_BLUEPRINT)
    hero.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    if matched:
        u.AutomationLibrary.finish_loading_before_screenshot()
        used = u.MaterialEditingLibrary.get_material_used_textures(hero.get_material(0))
        record['hero_material_used_texture_paths'] = [t.get_path_name() for t in used]
        u.log('GRIP_HERO_MATERIAL_TEXTURES ' + str(record['hero_material_used_texture_paths']))
        textures = list({t.get_path_name(): t for t in used if t.get_path_name().startswith('/Game/SpaceSurvival/Character/')}.values())
        assert len(textures) == 1 and isinstance(textures[0], u.Texture2D) and (textures[0].get_path_name().split('.')[0] == '/Game/SpaceSurvival/Character/model-rigged_texture_0')
        for texture in textures:
            texture.set_force_mip_levels_to_be_resident(120.0)
        record['temporary_hero_residency'] = {
            'texture_paths': [t.get_path_name() for t in textures],
            'seconds': 120,
            'wait_before_each_capture_seconds': 10,
            'asset_streaming_flags_saved': False,
            'proof': 'Hero ListTextures lines before each screenshot are bound in MatchedResidency.json',
        }
    for pitch, yaw, color, intensity in [
        (-35, -30, (0.9, 0.95, 1, 1), 4),
        (-25, 145, (1, 0.89, 0.75, 1), 2),
        (-65, 70, (0.5, 0.7, 1, 1), 1),
    ]:
        actor = actors.spawn_actor_from_class(u.DirectionalLight, u.Vector(0, 0, 500), u.Rotator(pitch=pitch, yaw=yaw, roll=0))
        lamp = actor.get_component_by_class(u.DirectionalLightComponent)
        lamp.set_mobility(u.ComponentMobility.MOVABLE)
        lamp.set_light_color(u.LinearColor(*color))
        lamp.set_intensity(intensity)
    post = actors.spawn_actor_from_class(u.PostProcessVolume, u.Vector(0, 0, 0))
    post.set_editor_property('unbound', True)
    settings = post.get_editor_property('settings')
    for key, value in {
        'override_auto_exposure_min_brightness': True,
        'override_auto_exposure_max_brightness': True,
        'auto_exposure_min_brightness': 1.0,
        'auto_exposure_max_brightness': 1.0,
        'override_bloom_intensity': True,
        'bloom_intensity': 0.1,
    }.items():
        settings.set_editor_property(key, value)
    post.set_editor_property('settings', settings)
    camera = actors.spawn_actor_from_class(u.CameraActor, u.Vector(0, 0, 0))
    camera.get_component_by_class(u.CameraComponent).set_field_of_view(35)
    camera.get_component_by_class(u.CameraComponent).set_editor_property('aspect_ratio', 4 / 3)
    u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)
    old = u.load_asset('/Game/SpaceSurvival/Meshes/SM_AcornShipV2')
    cases = [
        ('UnrealBefore', old, 'Pilot', 0, (165, -165, 185), (12, 0, 94)),
        ('UnrealAfter', mesh, 'Pilot', 0, (165, -165, 185), (12, 0, 94)),
        ('UnrealLeftContact', mesh, 'Pilot', 0, (105, 100, 135), (20, 22, 94)),
        ('UnrealRightContact', mesh, 'Pilot', 0, (102, -105, 135), (16, -20, 95)),
        ('UnrealPilotPeak', mesh, 'Pilot', 1, (165, -165, 185), (12, 0, 94)),
        ('UnrealExitRelease', mesh, 'Disembark', 0.2, (165, -165, 185), (12, 0, 94)),
    ]
    if matched:
        cases = [
            ('UnrealMatchedBefore', old, 'Pilot', 0, (165, -165, 185), (12, 0, 94)),
            ('UnrealMatchedAfter', mesh, 'Pilot', 0, (165, -165, 185), (12, 0, 94)),
        ]
    if cases_override is not None:
        cases = cases_override
    state = {
        'index': 0,
        'task': None,
        'frames': 0,
        'busy': False,
        'handle': None,
        'done': False,
        'start': time.monotonic(),
    }
    record['images'] = []

    def setup():
        name, asset, clip, seconds, position, target = cases[state['index']]
        visual.set_static_mesh(asset)
        animation = u.load_asset('/Game/SpaceSurvival/Character/A_' + clip)
        assert isinstance(animation, u.AnimSequence)
        hero.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
        hero.set_animation(animation)
        hero.stop()
        hero.set_position(seconds, False)
        hero.set_play_rate(0.0)
        hero.override_animation_data(animation, False, False, seconds, 0.0)
        state['animation'] = animation
        state['seconds'] = seconds
        camera.set_actor_location(u.Vector(*position), False, False)
        camera.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*position), u.Vector(*target)), False)
        state.update(task=None, frames=0, case_start=time.monotonic())

    def verify_pose():
        expected_clip = state['animation']
        seconds = state['seconds']
        assert hero.get_animation_mode() == u.AnimationMode.ANIMATION_SINGLE_NODE
        assert hero.get_anim_instance().get_animation_asset() == expected_clip
        assert abs(hero.get_position() - seconds) < 0.0001
        options = u.AnimPoseEvaluationOptions()
        options.set_editor_property('evaluation_type', u.AnimDataEvalType.COMPRESSED)
        options.set_editor_property('extract_root_motion', False)
        options.set_editor_property('optional_skeletal_mesh', u.load_asset('/Game/SpaceSurvival/Character/SK_AcornautTailV2'))
        expected = u.AnimPoseExtensions.get_anim_pose_at_time(expected_clip, seconds, options)
        assert u.AnimPoseExtensions.is_valid(expected)
        names = ('Pelvis', 'Spine3', 'L_Elbow', 'L_Wrist', 'L_Middle1', 'R_Elbow', 'R_Wrist', 'L_Ankle', 'R_Ankle')
        available = [str(n) for n in u.AnimPoseExtensions.get_bone_names(expected)]
        assert all((n in available for n in names))
        vector = lambda v: [float(getattr(v, a)) for a in ('x', 'y', 'z')]
        quaternion = lambda q: [float(getattr(q, a)) for a in ('x', 'y', 'z', 'w')]

        def angle(a, b):
            dot = abs(sum((x * y for x, y in zip(a, b)))) / math.sqrt(sum((x * x for x in a)) * sum((x * x for x in b)))
            return math.degrees(2 * math.acos(min(1, max(0, dot))))
        checks = {}
        for name in names:
            target = u.AnimPoseExtensions.get_bone_pose(expected, name, u.AnimPoseSpaces.WORLD)
            actual = hero.get_socket_transform(name, u.RelativeTransformSpace.RTS_COMPONENT)
            position_error = (actual.translation - target.translation).length()
            rotation_error = angle(quaternion(actual.rotation), quaternion(target.rotation))
            assert position_error < 0.05 and rotation_error < 0.1, (name, position_error, rotation_error)
            checks[name] = {
                'component_cm': vector(actual.translation),
                'quaternion_xyzw': quaternion(actual.rotation),
                'expected_position_error_cm': position_error,
                'expected_rotation_error_degrees': rotation_error,
            }
        if 'baseline_bones' not in state:
            state['baseline_bones'] = checks
        if expected_clip.get_name() == 'A_PilotGripFit':
            assert angle(checks['L_Wrist']['quaternion_xyzw'], state['baseline_bones']['L_Wrist']['quaternion_xyzw']) > 90, 'New Pilot did not rotate L wrist'
        if expected_clip.get_name() == 'A_DisembarkGripFit' and seconds > 0.05:
            assert math.dist(checks['L_Wrist']['component_cm'], state['baseline_bones']['L_Wrist']['component_cm']) > 2, 'Exit did not move L wrist'
        record.setdefault('pose_checks', []).append({
            'case': cases[state['index']][0],
            'active_asset': expected_clip.get_path_name(),
            'seconds': seconds,
            'independent_evaluation': 'Compressed, same mesh, component space',
            'bones': checks,
        })

    def finish():
        if state['done']:
            return
        state['done'] = True
        try:
            assert all((sha(p) == digest for p, digest in protected.items())), 'Existing content/source/config changed'
            record['existing_protected_files_unchanged'] = len(protected)
            record['status'] = 'SEPARATE_GRIP_FIT_NATIVE_PREVIEWED_NOT_ADOPTED' if not record['errors'] else 'FAILED_NATIVE_PREVIEW'
        except Exception as error:
            record['errors'].append(str(error))
            u.log_error(str(error))
        (ROOT / 'Saved/Validation').mkdir(parents=True, exist_ok=True)
        (SOURCE / (receipt_name or ('UnrealMatchedPreview.json' if matched else 'UnrealPreview.json'))).write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
        u.unregister_slate_post_tick_callback(state['handle'])
        u.EditorPythonScripting.set_keep_python_script_alive(False)
        u.log('GRIP_FIT_PREVIEW_FINISHED')

    def tick(delta):
        if state['busy'] or state['done']:
            return
        state['busy'] = True
        try:
            state['frames'] += 1
            name = cases[state['index']][0]
            path = SOURCE / (name + '.png')
            if state['task'] is None and state['frames'] >= 90 and (time.monotonic() - state['case_start'] > (10 if matched else 3)):
                if matched:
                    u.log('GRIP_MATCHED_RESIDENCY_' + name)
                    u.SystemLibrary.execute_console_command(world, 'ListTextures')
                u.AutomationLibrary.finish_loading_before_screenshot()
                verify_pose()
                state['task'] = u.AutomationLibrary.take_high_res_screenshot(1600, 1200, str(path), camera, delay=0.3)
                assert state['task'].is_valid_task()
            if state['task'] and state['task'].is_task_done() and path.exists():
                record['images'].append({
                    'file': path.name,
                    'sha256': sha(path),
                    'clip': cases[state['index']][2],
                    'seconds': cases[state['index']][3],
                })
                state['index'] += 1
                if state['index'] == len(cases):
                    finish()
                else:
                    setup()
            elif time.monotonic() - state['start'] > 150:
                raise RuntimeError('Native grip preview timeout')
        except Exception as error:
            record['errors'].append(str(error))
            u.log_error(traceback.format_exc())
            finish()
        finally:
            state['busy'] = False
    setup()
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    state['handle'] = u.register_slate_post_tick_callback(tick)

def main(render=False, validate_only=False, matched=False):
    (ROOT / 'Saved/Validation').mkdir(parents=True, exist_ok=True)
    record = {
        'status': 'FAILED',
        'errors': [],
        'engine': u.SystemLibrary.get_engine_version(),
        'limits': [
            'Separate asset only; gameplay still selectsSM_AcornShipV2',
            'Open/upturned sourceLhand remains; no grasp pose repair',
            'No performance or owner art acceptance',
        ],
    }
    protected = {p: sha(p) for directory in ('Source', 'Config', 'Content') for p in (ROOT / directory).rglob('*') if p.is_file()}
    try:
        report, digest = checked_source()
        mesh = LIB.load_asset(PATH) if validate_only else import_candidate(report, digest)
        record.update(validate(mesh, report, digest))
        assert all((sha(p) == h for p, h in protected.items())), 'Existing protected files changed'
        package = ROOT / 'Content/SpaceSurvival/Meshes/SM_AcornShipGripFit.uasset'
        record['package'] = {
            'file': str(package.relative_to(ROOT)),
            'bytes': package.stat().st_size,
            'sha256': sha(package),
        }
        record['source_obj_sha256'] = digest
        record['existing_protected_files_unchanged'] = len(protected)
        record['status'] = 'SEPARATE_GRIP_FIT_SAVED_VALIDATED_NOT_ADOPTED'
        (ROOT / 'Saved/Validation' / ('GripFitPersisted.json' if validate_only else 'GripFitImport.json')).write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
        if render:
            preview(mesh, record, protected, matched)
    except Exception as error:
        record['errors'].append(str(error))
        (ROOT / 'Saved/Validation' / ('GripFitPersisted.json' if validate_only else 'GripFitImport.json')).write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
        u.log_error(traceback.format_exc())
        raise


if __name__ == '__main__':
    main('--preview' in sys.argv, '--validate-only' in sys.argv, '--matched' in sys.argv)
