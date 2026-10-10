"""Read-only support probe for floor-mounted TVs beside the fitted cabinets.

Probe1 rejected an uneven cabinet top; Probe2 failed on its hit-dict schema. This new attempt retains that
failure and changes the physical support instead of weakening a flat-top guard.
Native source geometry, roof attachments and all four capsule routes remain
required. No spawning, material authoring, import or save belongs here.
"""
import math

import RefineStationOperationsDensity as D

MAP, BASE, PREFIX = D.MAP, D.BASE, D.PREFIX
POST_FOOT = (44., 10.)
POST_Y = 1259.


def _floor(world, xy, ignored, u):
    """Use the inspected Workroom hit schema, not Arcade's different encoding."""
    from RefineStationWorkroomComposition import _hit
    D._require(not ignored, 'Never bypass physical floor eligibility')
    hit = _hit(u.SystemLibrary.line_trace_single_by_profile(world,
        u.Vector(xy[0], xy[1], 18.), u.Vector(xy[0], xy[1], -35.),
        'Pawn', False, [], u.DrawDebugTrace.NONE, True))
    D._require(hit and set(hit) == {'label', 'component', 'point', 'normal', 'initial_overlap'} and
               hit['label'] == 'Ground/Operations' and hit['component'] and
               abs(hit['point'][2]) < .08 and hit['normal'][2] >= .7,
               'No actual Operations floor support: '+repr({'xy': xy, 'hit': hit}))
    return hit


def mount_plan(sign):
    right, up = D.SCREEN_RIGHT, D.SCREEN_UP
    front = (up[1]*right[2]-up[2]*right[1], up[2]*right[0]-up[0]*right[2],
             up[0]*right[1]-up[1]*right[0])
    yaw = (90. if sign < 0 else 270.)-math.degrees(math.atan2(front[1], front[0]))
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    foot = (7050., sign*POST_Y)
    points = [(foot[0]+c*x-s*y, foot[1]+s*x+c*y)
              for x, y in ((0., 0.), (-22., -5.), (-22., 0.), (-22., 5.),
                           (0., -5.), (0., 5.), (22., -5.), (22., 0.), (22., 5.))]
    D._require(all(6400. < x < 9200. and -1300. < y < 1300. for x, y in points),
               'Physical TV post escapes actual Operations floor footprint')
    pivot_z = 225.-D.SCREEN_CENTER[2]*D.TV_SCALE
    return {'sign': sign, 'yaw_degrees': yaw, 'face_normal_source': list(front),
            'foot_xy_cm': list(foot), 'foot_size_native_axes_cm': list(POST_FOOT),
            'foot_sample_xy_cm': [list(p) for p in points], 'base_z_cm': 0.,
            'top_z_cm': pivot_z+19.318534851*D.TV_SCALE, 'pivot_z_cm': pivot_z}


def probe(ctx):
    import unreal as u
    from RefineStationOperationsComposition import _clearance
    from RefineStationOperationsDisplays import _state
    from RefineStationSocialSeatedCrew import _geometry
    proposal, source, native = D._inputs(ctx, u)
    actors = list(ctx.eas.get_all_level_actors())
    D._require(not any(a.get_actor_label().startswith(PREFIX) for a in actors),
               'Preserve an existing density pass')
    before = {a.get_path_name(): _state(a, u) for a in actors}
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    _, geometry = _geometry(ctx.asset(D.CABINET), False, u)
    storage, posts = [], []
    for part in proposal['parts'][-2:]:
        sign = 1 if part['location'][1] > 0 else -1
        lo, hi = part['bounds']['minimum'], part['bounds']['maximum']
        points = [(7050., sign*1204.)]+[(x, y) for x in (lo[0]+5., hi[0]-5.)
                                      for y in (lo[1]+5., hi[1]-5.)]
        cabinet_floor = [_floor(world, xy, [], u) for xy in points]
        raw_top = []
        for dx, dy in ((0., 0.), (-21., -9.), (-21., 9.), (21., -9.), (21., 9.)):
            xy = (7050.+dx, sign*1220.+dy)
            raw_top.append({'xy_cm': list(xy), 'native_surface_z_cm': D._cabinet_top(geometry, part, xy)})
        storage.append({'part': part['name'], 'sign': sign, 'floor_samples': cabinet_floor,
                        'unused_cabinet_top_samples': raw_top,
                        'cabinet_top_is_tv_support': False})
        mount = mount_plan(sign)
        foot = [_floor(world, xy, [], u) for xy in mount['foot_sample_xy_cm']]
        D._require(all(hit['label'] == 'Ground/Operations' and abs(hit['point'][2]) < .08 for hit in foot),
                   'TV support feet must contact the actual Operations floor')
        # The rotated foot clears the cabinet rear, rather than penetrating it.
        D._require(all(abs(point[1]) > max(abs(lo[1]), abs(hi[1]))+.5
                       for point in mount['foot_sample_xy_cm']), 'TV floor support intersects fitted cabinet')
        posts.append({**mount, 'floor_samples': foot})
    roof = D._roof_contacts(ctx, actors, native, u)
    bounds = ctx.asset(D.POST).get_bounds()
    D._require(math.dist(bounds.origin.to_tuple(), (0., 0., 100.)) < .01 and
               math.dist(bounds.box_extent.to_tuple(), (5., 5., 100.)) < .01,
               'Native support profile differs from measured10x10x200')
    D._require(all(_state(a, u) == before[a.get_path_name()] for a in actors),
               'Read-only support probe changed actor state')
    return {'source_sha256': source, 'plan_sha256': D.PLAN_SHA, 'art_manifest_sha256': D.ART_SHA,
            'roof_supports': roof, 'storage_supports': storage, 'tv_floor_supports': posts,
            'routes': _clearance(world, u), 'existing_actors_preserved': len(actors),
            'actor_count_proposal': 21, 'native_tv_aperture_probe_sha256': D.TV_PROBE_SHA,
            'scope': '12 canopies +3 measured roof rails +2 cabinets +2 floor TV posts +2 original TVs',
            'floor_hit_schema': 'Workroom _hit: label/component/point/normal/initial_overlap',
            'superseded_support': 'Probe1 top rejected; Probe2 schema failed; no physical guard relaxed',
            'limits': 'No authoring/saving; native placement, pixels and walking remain unverified.'}
