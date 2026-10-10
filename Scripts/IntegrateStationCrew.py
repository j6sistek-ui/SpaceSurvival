"""Bounded, reversible assignment of imported crew to existing station jobs.

Run preflight first in the already-open live Wayfarer map with PIE stopped.
apply changes placed actors only; the lead backs up, reviews and saves the map.
Source meshes/materials/animations and protected hologram actors are never edited.
The imported crew has a 178 cm reference height; animation compatibility is checked
by exact Skeleton identity. A new model needs one assignment row and compatible clips.
"""
import hashlib
from pathlib import Path

MAP = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
ROOT = '/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew'
TAG = 'StationCrew20261009'
# Existing labels are stable authoring keys, even when their old name is generic.
ASSIGNMENTS = (
    ('Crew/Atrium A', 'Seer', 'Check-in and visitor support', 'Idle',
     ('Role/TalkLoop', 'Role/Emote_Greeting')),
    ('Crew/Atrium B', 'Tendril', 'Welcome and directions', 'Listen',
     ('Role/Gesture_InstructionalPoint', 'Role/TalkLoop')),
    ('Crew/Atrium patrol', 'Olive', 'Unarmed station security', 'Role/Crew_Worker_Idle_Alert',
     ('Role/Emote_Greeting',)),
    ('Crew/Trader A', 'Robe', 'Outside merchant A', 'Role/IdleBartering',
     ('Role/PitchBarter_Lt', 'Role/TalkLoop')),
    ('Crew/Trader B', 'Glyph', 'Outside merchant B', 'Role/IdleBartering',
     ('Role/PitchBarter_Rt', 'Role/Gesture_Yes')),
    ('Crew/Botanist', 'Tribal', 'Outside produce merchant', 'Role/IdleBartering',
     ('Role/TalkLoop', 'Role/Emote_Greeting')),
    ('Crew/Machinery attendant', 'Warden', 'Equipment inspection', 'Role/Crew_Worker_Idle',
     ('LookL', 'LookR')),
    ('Crew/Market courier', 'Crest', 'Market service circuit', 'Role/Crew_Worker_Idle_Alert',
     ('LookL',)),
    ('Crew/Lounge guest', 'Dread', 'Bartender', 'Role/BarBartender_Type02', ()),
    ('Refine/Archive/Conversation guest B', 'Amethyst', 'Wardrobe visitor', 'Listen',
     ('Talk', 'Role/Gesture_Yes')),
)
FIELDS = ('idle_animation', 'walk_animation', 'gesture_animations', 'phase_offset')
# Put the produce seller behind the existing south stall, facing arriving customers.
JOB_PLACEMENTS = {'Crew/Botanist': ((-520., -1665., 85.), 90.)}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def path(obj):
    return obj.get_path_name() if obj else None


def context(u):
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    require(not editor.get_game_world() and world and path(world).split('.')[0] == MAP,
            'Open the live Wayfarer map and stop PIE first')
    return world, list(u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())


def clip_path(name, tag):
    folder, _, clip = tag.rpartition('/')
    return ROOT + '/' + name + '/' + (folder + '/' if folder else '') + 'A_' + name + '_' + clip


def preflight(u):
    _, actors = context(u)
    loaded, report = [], []
    for label, name, job, idle, gestures in ASSIGNMENTS:
        matches = [a for a in actors if a.get_actor_label() == label]
        require(len(matches) == 1, 'Expected one original job: ' + label)
        actor = matches[0]
        require(isinstance(actor, u.SSOutpostAmbientActor) and not actor.drone and
                not actor.animation_managed_externally and not actor.hidden,
                'Preserve hidden, projected or externally managed actors: ' + label)
        folder = 'Rig' if name in ('Olive', 'Crest') else 'Mesh'
        mesh = u.load_asset(ROOT + '/' + name + '/' + folder + '/SK_' + name)
        require(isinstance(mesh, u.SkeletalMesh), 'Missing mesh: ' + name)
        b = mesh.get_bounds()
        require(abs(2. * b.box_extent.z - 178.) < .1 and
                abs(b.origin.z - b.box_extent.z) < .1, 'Unnormalized height/sole: ' + name)
        clips = [u.load_asset(clip_path(name, tag)) for tag in (idle, 'Walk', *gestures)]
        require(all(isinstance(c, u.AnimSequence) and c.get_editor_property('skeleton') == mesh.skeleton and
                    c.get_editor_property('sequence_length') > .01 for c in clips), 'Animation mismatch: ' + name)
        require(all(m.material_interface for m in mesh.materials), 'Missing source materials: ' + name)
        loaded.append((actor, name, job, mesh, clips))
        report.append({'actor':path(actor), 'label':label, 'character':name, 'job':job,
                       'mesh':path(mesh), 'skeleton':path(mesh.skeleton),
                       'animations':[path(c) for c in clips], 'material_slots':len(mesh.materials),
                       'reference_height_cm':2. * b.box_extent.z,
                       'route_points':len(actor.route_points)})
    return loaded, report


def apply(u, expected_sha256, allow_dirty_map=False):
    world, _ = context(u)
    file = Path(u.Paths.project_content_dir()) / (MAP.removeprefix('/Game/') + '.umap')
    require(hashlib.sha256(file.read_bytes()).hexdigest() == expected_sha256, 'Saved map changed')
    dirty_maps = [p.get_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    require((not dirty_maps or (allow_dirty_map and dirty_maps == [MAP])) and
            not u.EditorLoadingAndSavingUtils.get_dirty_content_packages(), 'Preserve pre-existing dirty work')
    loaded, report = preflight(u)
    require(all(TAG not in map(str, a.tags) for a, *_ in loaded), 'Already assigned; verify instead of reapplying')
    state = []
    try:
        for actor, name, job, mesh, clips in loaded:
            c = actor.character_mesh
            before = {'actor':actor, 'mesh':c.get_skeletal_mesh_asset(),
                      'actor_transform':actor.get_actor_transform(),
                      'transform':c.get_relative_transform(), 'materials':list(c.get_editor_property('override_materials')),
                      'animation_mode':c.animation_mode, 'animation_data':c.animation_data,
                      'tags':list(actor.tags), 'fields':{f:actor.get_editor_property(f) for f in FIELDS}}
            state.append(before)
            actor.modify()
            c.modify()
            if actor.get_actor_label() in JOB_PLACEMENTS:
                position, yaw = JOB_PLACEMENTS[actor.get_actor_label()]
                actor.set_actor_location(u.Vector(*position), False, True)
                actor.set_actor_rotation(u.Rotator(yaw=yaw), False)
            c.set_skeletal_mesh_asset(mesh)
            c.set_editor_property('override_materials', [])
            c.set_relative_transform(u.Transform(location=u.Vector(0.,0.,-85.),
                rotation=u.Rotator(yaw=-90.), scale=u.Vector(1.,1.,1.)), False, True)
            c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
            data = u.SingleAnimationPlayData(anim_to_play=clips[0], saved_looping=True,
                saved_playing=True, saved_position=0., saved_play_rate=1.)
            c.set_editor_property('animation_data', data)
            actor.set_editor_property('idle_animation', clips[0])
            actor.set_editor_property('walk_animation', clips[1])
            actor.set_editor_property('gesture_animations', clips[2:])
            actor.set_editor_property('tags', before['tags'] + [u.Name(TAG),
                u.Name('StationCrew:' + name), u.Name('StationJob:' + job)])
            actor.refresh_readability_lighting()
        result = verify(u)
        require(result['valid'], 'Placed crew verification failed')
        return state, {'assignments':report, 'verification':result}
    except Exception:
        restore(u, state)
        raise


def restore(u, state):
    context(u)
    for row in reversed(state):
        actor = row['actor']
        actor.set_actor_transform(row['actor_transform'], False, True)
        c = actor.character_mesh
        c.set_skeletal_mesh_asset(row['mesh'])
        c.set_relative_transform(row['transform'], False, True)
        c.set_editor_property('override_materials', row['materials'])
        c.set_animation_mode(row['animation_mode'])
        c.set_editor_property('animation_data', row['animation_data'])
        actor.set_editor_property('tags', row['tags'])
        for field, value in row['fields'].items():
            actor.set_editor_property(field, value)
        actor.refresh_readability_lighting()


def verify(u):
    loaded, _ = preflight(u)
    rows = []
    for a, name, job, mesh, clips in loaded:
        c, light = a.character_mesh, a.head_fill_light
        flags = {'mesh':c.get_skeletal_mesh_asset() == mesh,
                 'materials':not c.get_editor_property('override_materials') and all(c.get_material(i) == m.material_interface
                             for i, m in enumerate(mesh.materials)),
                 'scale':(c.relative_scale3d-u.Vector(1.,1.,1.)).length() < .0001,
                 'idle':a.idle_animation == clips[0], 'walk':a.walk_animation == clips[1],
                 'gestures':list(a.gesture_animations) == clips[2:],
                 'tag':u.Name('StationCrew:' + name) in a.tags,
                 'fill':light.is_visible() and not light.get_editor_property('cast_shadows') and
                        light.get_editor_property('specular_scale') == 0. and
                        light.get_editor_property('indirect_lighting_intensity') == 0. and
                        not light.get_editor_property('affect_reflection') and
                        not light.get_editor_property('affect_global_illumination')}
        rows.append({'name':name,'job':job,'checks':flags,'position':list(a.get_actor_location().to_tuple())})
    return {'valid':all(all(r['checks'].values()) for r in rows), 'actors':rows}
