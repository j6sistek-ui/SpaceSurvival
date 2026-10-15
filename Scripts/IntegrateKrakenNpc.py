"""Stage the owner-approved Kraken walk and head-attached MetaHair162.

Run preflight(unreal) first with the live station open and PIE stopped. stage()
does not save the map: inspect native walking, floor contact and hair before
saving. Existing actors and the licensed source assets are never rewritten.
The prepared private assets and exact authoring provenance are documented in
docs/validation/2026-10-15-kraken-npc.md. This is not a general character importer.
"""
import hashlib
import math
from pathlib import Path

MAP = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
ROOT = '/Game/SpaceSurvival/Licensed/StationAssets/KrakenRefresh_20261015'
LABEL = 'Crew/Kraken visitor'
HAIR_LABEL = 'Crew/Kraken fitted hair'
FIT_LOCATION = (-1.213051, .656107, .045738)
FIT_QUATERNION = (-.170199, -.696922, .165277, -.676768)


def route(u):
    # The west reception furniture intersects a complete circle. Retrace only
    # the tested southern/eastern arc; keep the 75 cm sweep clearance.
    return [u.Vector(4200 + 800 * math.cos(math.pi / 2 + i * math.pi / 4),
                     800 * math.sin(math.pi / 2 + i * math.pi / 4), 87)
            for i in (3, 4, 5, 6, 5, 4)]


def preflight(u):
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    assert not u.EditorLevelLibrary.get_pie_worlds(False), 'Stop PIE first'
    assert world.get_path_name().split('.')[0] == MAP, 'Open the current station'
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages(), 'Preserve unsaved map work'
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages(), 'Preserve unsaved assets'
    actors = list(u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())
    assert not any(a.get_actor_label() in (LABEL, HAIR_LABEL) for a in actors), 'Already placed; verify, do not replay'
    assets = {name: u.load_asset(ROOT + '/' + name) for name in
              ('BP_Kraken', 'SK_Kraken', 'A_Kraken_Walking', 'G_Kraken_MetaHair162', 'M_Kraken_Hair')}
    assert all(assets.values()), 'Missing prepared private assets'
    mesh = assets['SK_Kraken']
    assert assets['A_Kraken_Walking'].get_editor_property('skeleton') == mesh.skeleton
    assert len(mesh.materials) == 4 and all(m.material_interface for m in mesh.materials)
    points = route(u)
    for i, start in enumerate(points):
        assert u.SystemLibrary.capsule_trace_single_for_objects(
            world, start, points[(i + 1) % len(points)], 75., 85.,
            [u.ObjectTypeQuery.OBJECT_TYPE_QUERY1], False, [],
            u.DrawDebugTrace.NONE, True) is None, 'Route scenery changed; review clearance'
    map_file = Path(u.Paths.project_content_dir()) / (MAP.removeprefix('/Game/') + '.umap')
    return assets, {'map_sha256': hashlib.sha256(map_file.read_bytes()).hexdigest(),
                    'existing_actors': len(actors), 'route': [list(p.to_tuple()) for p in points],
                    'assets': {k: a.get_path_name() for k, a in assets.items()}}


def stage(u, expected_map_sha256):
    assets, report = preflight(u)
    assert report['map_sha256'] == expected_map_sha256, 'Saved map changed'
    es = u.get_editor_subsystem(u.EditorActorSubsystem)
    created = []
    try:
        points = route(u)
        actor = es.spawn_actor_from_class(assets['BP_Kraken'].generated_class(), points[0],
                                         u.Rotator(yaw=-22.5))
        created.append(actor)
        actor.set_actor_label(LABEL)
        actor.body.set_capsule_size(70., 85., False)
        actor.set_editor_property('travel_speed', 70.)
        actor.set_editor_property('pause_at_waypoint', 0.)
        actor.set_editor_property('gesture_animations', [])
        for field in ('idle_animation', 'walk_animation'):
            actor.set_editor_property(field, assets['A_Kraken_Walking'])
        actor.set_editor_property('route_points', [u.MathLibrary.inverse_transform_location(
            actor.get_actor_transform(), p) for p in points])
        actor.refresh_readability_lighting()
        hair = es.spawn_actor_from_class(u.GroomActor, u.Vector())
        created.append(hair)
        hair.set_actor_label(HAIR_LABEL)
        component = hair.get_component_by_class(u.GroomComponent)
        component.set_groom_asset(assets['G_Kraken_MetaHair162'])
        component.set_material(0, assets['M_Kraken_Hair'])
        settings = component.simulation_settings
        settings.set_editor_property('override_settings', True)
        solver = settings.solver_settings
        solver.set_editor_property('enable_simulation', False)
        settings.set_editor_property('solver_settings', solver)
        component.set_editor_property('simulation_settings', settings)
        assert hair.attach_to_component(actor.character_mesh, 'head', u.AttachmentRule.KEEP_RELATIVE,
                                        u.AttachmentRule.KEEP_RELATIVE, u.AttachmentRule.KEEP_RELATIVE, False)
        component.set_relative_transform(u.Transform(location=u.Vector(*FIT_LOCATION),
            rotation=u.Quat(*FIT_QUATERNION).rotator(), scale=u.Vector(.01, .01, .01)), False, False)
        assert str(component.get_attach_socket_name()) == 'head'
        return created, report
    except Exception:
        for actor in reversed(created):
            es.destroy_actor(actor)
        raise


def verify(u):
    actors = list(u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())
    body = [a for a in actors if a.get_actor_label() == LABEL]
    hair = [a for a in actors if a.get_actor_label() == HAIR_LABEL]
    assert len(body) == len(hair) == 1
    actor, component = body[0], hair[0].get_component_by_class(u.GroomComponent)
    assert component.get_attach_parent() == actor.character_mesh
    assert str(component.get_attach_socket_name()) == 'head'
    assert len(actor.route_points) == 6 and not actor.gesture_animations
    assert actor.walk_animation.get_editor_property('skeleton') == actor.character_mesh.get_skeletal_mesh_asset().skeleton
    assert component.groom_asset.get_path_name() == ROOT + '/G_Kraken_MetaHair162.G_Kraken_MetaHair162'
    return {'actor': actor.get_path_name(), 'hair': hair[0].get_path_name(),
            'route_points': len(actor.route_points), 'attachment': 'head'}
