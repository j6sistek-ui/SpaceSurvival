"""Replace the preview lounge's levitating reset with a grounded ambient match.

The integration lead owns the guarded map transaction and native asset saves.
Only agent-owned pool actors change. Original animation/mesh assets, the room
layout and the canonical live station remain outside this authoring operation.
"""
from RefineStationOrbitPool import MAP, POOL, _one, _position
from RefineStationSocialFinish import _aisle


PLAYER_LABELS = {'nyxar': 'Refine/OrbitPool/Alien shooter',
                 'trooper': 'Refine/OrbitPool/Trooper captain'}
OLD_SEQUENCE = 'Refine/OrbitPool/Ambient match sequence'
NEW_SEQUENCE = 'Refine/OrbitPool/Alternating match sequence'


def prepare(ctx):
    """Validate the existing owned corner, then retire only its superseded reset."""
    import unreal as u
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != MAP:
        raise RuntimeError('Pool revision belongs only to the separate owner preview')
    if any(a.get_actor_label() == NEW_SEQUENCE for a in ctx.actors):
        raise RuntimeError('Grounded match already exists; review before replay')
    before = _aisle(world, u)
    players = {key: _one(ctx.actors, label) for key, label in PLAYER_LABELS.items()}
    cue = _one(ctx.actors, 'Refine/OrbitPool/Cue')
    balls = [_one(ctx.actors, 'Refine/OrbitPool/Ball ' + name)
             for name in ('Ivory', 'IonBlue', 'SolarAmber')]
    score = _one(ctx.actors, 'Refine/OrbitPool/Score console Rule')
    old = _one(ctx.actors, OLD_SEQUENCE)
    if old.get_sequence().get_path_name().split('.')[0] != (
            '/Game/OutpostSandbox/StationRefinement/Sequences/LS_OrbitPool_20261006'):
        raise RuntimeError('Unexpected sequence on the old ambient actor')
    retired = [old]
    for prefix in ('Refine/OrbitPool/Return spill ', 'Refine/OrbitPool/Field return emitter '):
        group = [a for a in ctx.actors if a.get_actor_label().startswith(prefix)]
        if len(group) != 4:
            raise RuntimeError('Expected four obsolete reset actors: ' + prefix)
        retired.extend(group)
    allowed = {a.get_path_name() for a in (*players.values(), cue, *balls, score, *retired)}
    protected = {a.get_path_name(): _position(a) for a in ctx.actors if a.get_path_name() not in allowed}
    retired_rows = [{'actor': a.get_path_name(), 'label': a.get_actor_label()} for a in retired]
    for actor in retired:
        if not ctx.eas.destroy_actor(actor):
            raise RuntimeError('Could not retire an owned reset actor')
    score.get_component_by_class(u.TextRenderComponent).set_text('SCRATCH / BALL IN HAND')
    other_cue = ctx.raw('OrbitPool/Cue trooper', POOL + '_CueStick_c1_Nanite',
                        (4800, -2960, 100), collision=False)
    other_cue.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
    return {'players': players, 'cues': {'nyxar': cue, 'trooper': other_cue},
            'balls': balls, 'protected': protected,
            'report': {'retired': retired_rows, 'aisle_before': before,
                       'rule': 'SCRATCH / BALL IN HAND', 'scope': 'Ambient dressing; no playable pool feature'}}


def place_players(ctx, staged, clips, animation_report):
    """Use the measured actor/mesh transforms from each native skeleton's fit."""
    import unreal as u
    rows = []
    for key in ('nyxar', 'trooper'):
        actor, clip = staged['players'][key], clips[key]
        fit = animation_report['players'][key]
        component = actor.get_component_by_class(u.SkeletalMeshComponent)
        if component.get_skeletal_mesh_asset().get_path_name().split('.')[0] != fit['mesh']:
            raise RuntimeError('Fitted pool player mesh differs from saved actor: ' + key)
        if component.get_skeletal_mesh_asset().skeleton != clip.get_editor_property('skeleton'):
            raise RuntimeError('Pool pose does not match native skeleton: ' + key)
        ctx.move(actor, fit['actor_location'], fit['actor_rotation'])
        actor.set_actor_scale3d(u.Vector(1, 1, 1))
        component.set_relative_scale3d(u.Vector(*fit['mesh_scale']))
        component.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
        data = component.get_editor_property('animation_data')
        data.anim_to_play, data.saved_looping, data.saved_playing = clip, False, False
        data.saved_position = 0.
        component.set_editor_property('animation_data', data)
        component.set_update_animation_in_editor(True)
        component.play_animation(clip, False)
        component.set_position(0., False)
        component.set_play_rate(0.)
        actor.set_actor_enable_collision(False)
        rows.append({'actor': actor, 'clip': clip, 'cue': staged['cues'][key],
                     'cue_samples': fit['cue_samples']})
    return rows


def finish(ctx, staged):
    import unreal as u
    current = {a.get_path_name(): a for a in ctx.eas.get_all_level_actors()}
    changed = [path for path, pose in staged['protected'].items()
               if path not in current or _position(current[path]) != pose]
    if changed:
        raise RuntimeError('Pool revision changed protected owner actors: ' + str(changed))
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    staged['report'].update(protected_actors_unchanged=len(staged['protected']),
                            aisle_after=_aisle(world, u))
    return staged['report']
