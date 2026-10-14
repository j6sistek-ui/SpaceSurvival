"""Configure the existing native staff actor after measured idle/room review.

The lead supplies exact successful grounding and current-scene identities and
saves the map. This helper never loads/saves a level or modifies an asset.
"""
import hashlib
import json
import math
import struct
from pathlib import Path

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
LABEL = 'Crew/Lounge guest'
FEMALE = '/Game/SpaceSurvival/Licensed/AlienFemalePresentation/SK_AlienFemalePresentation'
CLIP = '/Game/OutpostSandbox/StationRefinement/BartenderGrounded20261006_V1/A_FemaleBartender_Type02_Grounded'
GROUND_RECEIPT = 'StationBartenderGrounding1.json'
ROOM_MANIFEST = 'StationBartenderGroundedRoomCapture1/manifest.json'


def _require(value, message):
    if not value:
        raise RuntimeError(message)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _pose(actor):
    t = actor.get_actor_transform()
    return {'location': list(t.translation.to_tuple()), 'rotation': list(t.rotation.to_tuple()),
            'scale': list(t.scale3d.to_tuple())}


def configure_visibility(actor, bounds_scale=4.):
    """Adopt/replay the measured Type02 visibility fix on this female only.

    The low-camera trial accepted scale4 for this rig/clip. Future variants
    need their own motion envelope; this does not prove skin contact or cost.
    """
    import unreal as u
    _require(isinstance(actor, u.SSOutpostAmbientActor) and actor.get_actor_label() == LABEL and
             actor.get_path_name().startswith(MAP+'.'), 'Target only the owner preview female bartender')
    _require(not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world(),
             'Configure editor presentation only after PIE stops')
    mesh = actor.get_component_by_class(u.SkeletalMeshComponent)
    _require(mesh and mesh.get_skeletal_mesh_asset() and
             mesh.get_skeletal_mesh_asset().get_path_name().split('.')[0] == FEMALE,
             'Keep the owner-chosen female mesh; never apply this profile to another rig')
    _require(math.isfinite(bounds_scale) and bounds_scale >= 1., 'Use a finite per-actor bounds scale of at least1')
    native_scale = struct.unpack('<f', struct.pack('<f', bounds_scale))[0]
    before = {'fixed_skel_bounds': bool(mesh.get_editor_property('component_use_fixed_skel_bounds')),
              'bounds_scale': float(mesh.get_editor_property('bounds_scale'))}
    if not before['fixed_skel_bounds']:
        mesh.set_editor_property('component_use_fixed_skel_bounds', True)
    if before['bounds_scale'] != native_scale:
        mesh.set_bounds_scale(native_scale)
    after = {'fixed_skel_bounds': bool(mesh.get_editor_property('component_use_fixed_skel_bounds')),
             'bounds_scale': float(mesh.get_editor_property('bounds_scale'))}
    _require(after == {'fixed_skel_bounds': True, 'bounds_scale': native_scale},
             'Native female component visibility fields differ from the requested profile')
    return {'actor': actor.get_path_name(), 'before': before, 'after': after,
            'changed': before != after, 'source_asset_edits': 0}


def apply(ctx, expected_map_sha256, grounding_sha256, room_manifest_sha256):
    import unreal as u
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    base = root/'.agent/local/StationRefinement'
    _require(_sha(root/('Content/'+MAP[6:]+'.umap')) == expected_map_sha256, 'Current owner preview changed')
    _require(_sha(base/GROUND_RECEIPT) == grounding_sha256 and _sha(base/ROOM_MANIFEST) == room_manifest_sha256,
             'Grounding/actual room evidence changed')
    grounded = json.loads((base/GROUND_RECEIPT).read_text(encoding='utf-8'))
    room = json.loads((base/ROOM_MANIFEST).read_text(encoding='utf-8'))
    _require(grounded['success'] and grounded['preservation_pass'] and room['success'] and
             room['files_unchanged'] and room['saves_unchanged'] and len(room['images']) == 2,
             'Require successful grounded clip and actual room fixture')
    _require(room['author_sha256'] == grounding_sha256, 'Room fixture used another grounded clip')
    for image in room['images']:
        for sample in ('before', 'after'):
            contacts = image[sample]['contacts']
            _require(all(-.1 <= foot['sole_gap_cm'] < 1. for foot in contacts['sole'].values()),
                     'Actual room soles remain ungrounded')
            _require(not contacts['potential_hand_counter_intersections'] and contacts['torso_rear_counter_clearance_cm'] > 20.,
                     'Actual room hand/body clearance remains unresolved')
    candidates = [a for a in ctx.actors if a.get_actor_label() == LABEL]
    _require(len(candidates) == 1 and isinstance(candidates[0], u.SSOutpostAmbientActor), 'Expected original native staff actor')
    actor = candidates[0]
    mesh = actor.get_component_by_class(u.SkeletalMeshComponent)
    _require(mesh and mesh.get_skeletal_mesh_asset().get_path_name().split('.')[0] == '/Game/Nyxar/Meshes/SKM_Nyxar',
             'Staff source differs; do not overwrite another character edit')
    _require(math.dist(actor.get_actor_location().to_tuple(), (4150., -4260., 85.)) < .01,
             'Original staff placement changed')
    rotation = actor.get_actor_rotation()
    _require(abs(rotation.yaw-90.) < .001 and abs(rotation.pitch) < .001 and abs(rotation.roll) < .001,
             'Original staff facing changed')
    before = {a.get_path_name(): _pose(a) for a in ctx.actors}
    source_state = {'actor': actor.get_path_name(), 'label': LABEL, 'pose': _pose(actor),
                    'mesh': mesh.get_skeletal_mesh_asset().get_path_name(),
                    'materials': [m.get_path_name() if m else None for m in mesh.get_materials()],
                    'idle': str(actor.get_editor_property('idle_animation')),
                    'gestures': list(map(str, actor.get_editor_property('gesture_animations')))}
    idle, female = ctx.asset(CLIP), ctx.asset(FEMALE)
    _require(idle.get_editor_property('skeleton') == female.skeleton, 'Grounded idle/female skeleton mismatch')
    for package, digest in grounded['saved_asset_sha256'].items():
        _require(_sha(root/('Content/'+package[6:].split('.')[0]+'.uasset')) == digest, 'Grounded private asset changed')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    hit = u.SystemLibrary.line_trace_single_by_profile(world, u.Vector(4150., -4160., 25.),
        u.Vector(4150., -4160., -35.), 'Pawn', False, [actor], u.DrawDebugTrace.NONE, True)
    fields = hit.to_tuple() if hit is not None else None
    _require(fields and fields[0] and fields[7].z > .85 and abs(fields[5].z) < 1.,
             'Reviewed bartender position has no native horizontal floor')
    presentation = grounded['candidate']['target_presentation']
    actor.set_actor_location(u.Vector(4150., -4160., 85.), False, False)
    mesh.set_skeletal_mesh_asset(female)
    mesh.set_editor_property('override_materials', [])
    mesh.set_relative_location(u.Vector(0., 0., -85.+fields[5].z+presentation['sole_offset_cm']), False, False)
    mesh.set_relative_rotation(u.Rotator(pitch=0., yaw=-90., roll=0.), False, False)
    mesh.set_relative_scale3d(u.Vector(*([presentation['uniform_scale']]*3)))
    mesh.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    mesh.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
    mesh.override_animation_data(idle, True, True, 0., 1.)
    mesh.set_editor_property('visibility_based_anim_tick_option', u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    actor.set_editor_property('idle_animation', idle)
    actor.set_editor_property('walk_animation', None)
    actor.set_editor_property('gesture_animations', [])
    actor.set_editor_property('route_points', [])
    actor.set_editor_property('animation_managed_externally', False)
    actor.set_editor_property('drone', False)
    actor.set_actor_hidden_in_game(False)
    actor.set_is_temporarily_hidden_in_editor(False)
    mesh.set_visibility(True, True)
    visibility = configure_visibility(actor)
    actual = mesh.get_world_transform()
    _require(math.dist(actual.translation.to_tuple(), (4150., -4160., fields[5].z+presentation['sole_offset_cm'])) < .001,
             'Native staff mesh does not match the reviewed grounded world origin')
    _require(abs(actual.rotation.w) > .99999 and abs(actual.scale3d.z-presentation['uniform_scale']) < .00001,
             'Native staff mesh does not match the reviewed orientation/scale')
    _require(mesh.get_material(0) == female.get_editor_property('materials')[0].material_interface,
             'Old male material override survived the mesh replacement')
    after = {a.get_path_name(): _pose(a) for a in ctx.actors}
    _require(before.keys() == after.keys(), 'Staff integration changed actor inventory')
    _require(all(before[path] == after[path] for path in before if path != actor.get_path_name()),
             'Staff integration moved another actor')
    return {'success': True, 'dirty_assets': [], 'actor': actor.get_path_name(), 'label': LABEL,
            'source_staff': source_state, 'female_mesh': female.get_path_name(), 'grounded_idle': idle.get_path_name(),
            'after_pose': _pose(actor), 'mesh_world_origin': list(actual.translation.to_tuple()),
            'mesh_world_scale': list(actual.scale3d.to_tuple()), 'floor_normal': list(fields[7].to_tuple()),
            'actor_inventory_preserved': True, 'all_other_actor_transforms_preserved': True,
            'native_ambient_idle_configuration': True, 'counter_lights_layout_assets_unchanged': True,
            'visibility_configuration': visibility,
            'limits': 'One grounded conversational idle; varied prop service and owner quality acceptance remain open.'}
