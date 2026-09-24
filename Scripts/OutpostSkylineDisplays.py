"""Mounted native Genesis display bands for the non-playable rear district.

Twenty-six complete frame/pane pairs sit on measured tower and gallery
surfaces. Six authored digital-glass materials supply graphics. No new lights,
shadows, collision, windows cut in vendor meshes or playable-area changes.
Call build(api) after OutpostSkyline. layout/audit need no Unreal process.
"""
import json
import math
import os
from pathlib import Path

PREFIX = 'SkylineDisplays/'
OWNER_TAG = 'OutpostSkylineDisplay'
TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
PACK = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/'
VARIANTS = ('DigitalPanel', 'Graph1', 'Graph2', 'CosmoAdvertisment',
            'RobotAdvertisment', 'KeosAdvertisment')


def rotate(v, yaw):
    a = math.radians(yaw)
    return [v[0] * math.cos(a) - v[1] * math.sin(a),
            v[0] * math.sin(a) + v[1] * math.cos(a), v[2]]


def bounds(row):
    x, y, z = row['size']
    c, s = abs(math.cos(math.radians(row['yaw']))), abs(math.sin(math.radians(row['yaw'])))
    e = [(c*x+s*y)/2, (s*x+c*y)/2, z/2]
    return [row['center'][i]-e[i] for i in range(3)] + [row['center'][i]+e[i] for i in range(3)]


def _overlap(a, b, tolerance=.01):
    return all(a[i] < b[i+3]-tolerance and a[i+3] > b[i]+tolerance for i in range(3))


def layout(catalog):
    import OutpostSkyline
    architecture = OutpostSkyline.build(catalog)
    by_name = {r['name']: r for r in architecture}
    meshes = catalog['meshes']

    def mesh(name):
        found = [m for m in meshes if m['name'] == name and PACK in m['asset']]
        if len(found) != 1:
            raise ValueError('Missing or ambiguous skyline display mesh: ' + name)
        return found[0]

    # These exact frame/glass parts and six native materials appear together
    # in the original Genesis example exported in BuildingSandbox/scene.json.
    frame = mesh('SM_Window400X200_V2_Part1')
    glass = mesh('SM_Window400X200_V2_Part2_DigitalWindow')
    panels = []

    def add(name, mounts, center, normal, variant, scale=1., text=None):
        if variant not in VARIANTS:
            raise ValueError('Unaudited digital-glass material variant')
        yaw = math.degrees(math.atan2(normal[1], normal[0]))
        # Native frame X-negative is its back when local+X faces out. Put that
        # rear plane exactly on the actual facade/cornice front surface.
        outward = frame['extent'][0] * scale
        frame_center = [center[i] + (normal[i] * outward if i < 2 else 0) for i in range(3)]
        offset = rotate([v * scale for v in frame['origin']], yaw)
        pivot = [frame_center[i] - offset[i] for i in range(3)]
        parts = []
        matname = 'MI_DigitalGlass_Window400X200_' + variant
        material = PACK + 'Materials/Instances/Translucent/' + matname + '.' + matname
        for i, item in enumerate((frame, glass)):
            delta = rotate([v * scale for v in item['origin']], yaw)
            row = {'name': PREFIX + name + ('/Frame' if i == 0 else '/Digital pane'),
                   'asset': item['asset'], 'center': [pivot[j] + delta[j] for j in range(3)],
                   'location': list(pivot), 'size': [2*v*scale for v in item['extent']],
                   'yaw': yaw, 'scale': [scale]*3, 'solid': False, 'casts_shadow': False,
                   'native_origin_cm': list(item['origin'])}
            if i == 1:
                row['material'] = material
            row['bounds'] = bounds(row)
            parts.append(row)
        panel = {'name': name, 'surface': list(center), 'normal': list(normal),
                 'yaw': yaw, 'shared_pivot': pivot, 'scale': scale, 'variant': variant,
                 'mounts': [{'name': r['name'], 'bounds': bounds(r)} for r in mounts], 'parts': parts}
        if text:
            # TextRender's installed-engine local face normal is+X. Place it
            # on the outward side of the frame, facing the same district view.
            panel['text'] = {'words': text, 'size': 42 if scale > 1 else 27,
                'position': [frame_center[0] + normal[0] * (outward + 3),
                             frame_center[1] + normal[1] * (outward + 3), center[2] - 16],
                'yaw': yaw}
        panels.append(panel)

    def face(name, row, variant, scale=1., text=None, center_z=None, mounts=None):
        normal = rotate((1, 0, 0), row['yaw'])[:2]
        surface = [row['center'][i] + normal[i] * row['size'][0] / 2 for i in range(2)]
        surface.append(row['center'][2] if center_z is None else center_z)
        add(name, mounts or [row], surface, normal, variant, scale, text)

    # Paired lower bands and one upper focal display per tower; two adjacent
    # south-facing bays continue the band around the visible corner. Heights
    # follow real storeys and deliberately differ with the tower silhouette.
    specifications = [
        (1, 0, 3, ('DigitalPanel', 'Graph1', 'Graph2', 'DigitalPanel', 'RobotAdvertisment')),
        (2, 3, 5, ('Graph1', 'Graph2', 'DigitalPanel', 'Graph1', 'DigitalPanel')),
        (3, 3, 5, ('CosmoAdvertisment', 'KeosAdvertisment', 'DigitalPanel', 'CosmoAdvertisment', 'Graph2')),
        (4, 0, 3, ('DigitalPanel', 'Graph2', 'Graph1', 'RobotAdvertisment', 'KeosAdvertisment')),
    ]
    for tower, lower, upper, styles in specifications:
        for index, bay in enumerate((0, 2)):
            row = by_name[f'Skyline/Tower {tower}/Front_{lower}_{bay}']
            # Move the pair70cm inward from the outer bay centres so their
            # frames clear the actual stepped corner buttresses by5cm.
            placement = dict(row)
            placement['center'] = list(row['center'])
            placement['center'][1] += 70 if bay == 0 else -70
            center_row = by_name[f'Skyline/Tower {tower}/Front_{lower}_1']
            face(f'Tower {tower}/Lower band {index}', placement, styles[index],
                 mounts=[row, center_row])
        row = by_name[f'Skyline/Tower {tower}/Front_{upper}_1']
        face(f'Tower {tower}/Upper signal', row, styles[2])
        for index, bay in enumerate((0, 1)):
            row = by_name[f'Skyline/Tower {tower}/Side_{upper}_-1/Cladding_0_{bay}']
            face(f'Tower {tower}/Corner return {index}', row, styles[3+index], .9)

    # Four hanging displays are bolted through the top80cm of their frames to
    # the continuous gallery cornice. Their centres avoid the23 light housings.
    cornices = [r for r in architecture if r['name'].startswith('Skyline/Upper gallery front cornice_')]
    for index, y in enumerate((-4800, -2650, 2450, 5000)):
        chosen = [r for r in cornices if bounds(r)[1] < y + 200 and bounds(r)[4] > y - 200]
        surface_x = min(bounds(r)[0] for r in chosen)
        add('Upper gallery/Band ' + str(index), chosen, (surface_x, y, 1410), (-1, 0),
            ('Graph2', 'DigitalPanel', 'DigitalPanel', 'Graph1')[index],
            text={1: 'SERVICE DECK', 2: 'TRANSIT LINK'}.get(index))

    # Two larger district panels preserve the same2:1 native aspect ratio.
    # Their260cm height fits between the actual lower/upper storey cornices.
    for tower, words in ((2, 'FLIGHT OPERATIONS'), (3, 'CREW HABITATS')):
        mounts = [by_name[f'Skyline/Tower {tower}/Front_6_{bay}'] for bay in range(3)]
        row = mounts[1]
        face(f'Tower {tower}/District identity', row, 'DigitalPanel', 1.3, words,
             center_z=row['center'][2]-20, mounts=mounts)
    return panels


def audit(panels, catalog):
    import OutpostSkyline
    import OutpostSkylineLighting
    architecture = OutpostSkyline.build(catalog)
    fixtures = OutpostSkylineLighting.layout(catalog)
    hardware = [bounds(r) for fixture in fixtures for r in fixture['parts']]
    failures, labels = [], set()
    protected = [2850, -4450, 0, 9350, 4550, 1120]
    for panel in panels:
        frame = panel['parts'][0]
        b = frame['bounds']
        normal = panel['normal']
        # Source frame back plane must touch the declared real mounting plane.
        rear = [frame['center'][i] - normal[i] * frame['size'][0]/2 for i in range(2)]
        if max(abs(rear[i]-panel['surface'][i]) for i in range(2)) > .01:
            failures.append(panel['name'] + ': rear mounting plane disconnected')
        if not any(_overlap(b, mount['bounds'], -.02) for mount in panel['mounts']):
            failures.append(panel['name'] + ': no native support contact')
        mounts = {m['name'] for m in panel['mounts']}
        for row in architecture:
            if row['name'] not in mounts and _overlap(b, bounds(row), .05):
                failures.append(panel['name'] + ': intersects other architecture ' + row['name'])
        for part in panel['parts']:
            if part['name'] in labels:
                failures.append(part['name'] + ': duplicate name')
            labels.add(part['name'])
            if part['solid'] or part['casts_shadow'] or min(part['scale']) <= 0 or len(set(part['scale'])) != 1:
                failures.append(part['name'] + ': must be uniform decorative geometry without shadows')
            if _overlap(part['bounds'], protected) or part['bounds'][0] < 9400:
                failures.append(part['name'] + ': enters playable district')
            if any(_overlap(part['bounds'], h) for h in hardware):
                failures.append(part['name'] + ': overlaps existing architectural light housing')
            if part['location'] != panel['shared_pivot']:
                failures.append(part['name'] + ': frame/pane source pivot separated')
    for i, panel in enumerate(panels):
        for other in panels[:i]:
            if _overlap(panel['parts'][0]['bounds'], other['parts'][0]['bounds']):
                failures.append(panel['name'] + ': overlaps ' + other['name'])
    return {'scope': 'Source/native-bounds audit; render and actual saved-map review still required.',
            'assemblies': len(panels), 'native_parts': len(labels),
            'district_labels': sum('text' in p for p in panels),
            'material_variants': sorted({p['variant'] for p in panels}),
            'new_lights': 0, 'new_shadow_casters': 0,
            'minimum_x': min(r['bounds'][0] for p in panels for r in p['parts']),
            'violations': failures}


def build(api):
    import unreal as u
    from OutpostGeometryUtils import mesh_union
    root, out = Path(api['ROOT']), Path(api['OUT'])
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    if package != TARGET and not (package.startswith('/Temp/Untitled') and api.get('TARGET') == TARGET):
        raise RuntimeError('Skyline displays are restricted to ' + TARGET)
    catalog = json.loads(Path(os.environ.get('SS_PREFAB_CATALOG',
        str(root/'Artifacts/PrefabLibrary/catalog.json'))).read_text(encoding='utf-8'))
    panels = layout(catalog); evidence = audit(panels, catalog)
    if evidence['violations']:
        raise ValueError('; '.join(evidence['violations']))
    actors = {a.get_actor_label(): a for a in api['EAS'].get_all_level_actors()}
    measured_mounts = {}
    for panel in panels:
        for mount in panel['mounts']:
            name = mount['name']
            if name not in measured_mounts:
                actor = actors.get(name)
                if not actor:
                    raise ValueError('Native display mounting actor missing: ' + name)
                c, e = mesh_union(actor)
                actual = [c.x-e.x,c.y-e.y,c.z-e.z,c.x+e.x,c.y+e.y,c.z+e.z]
                error = max(abs(actual[i]-mount['bounds'][i]) for i in range(6))
                measured_mounts[name] = {'bounds': actual, 'maximum_bound_error_cm': error}
                if error > 1.:
                    raise ValueError('Saved facade differs from source display mount: ' + name)
        for row in panel['parts']:
            api['load'](row['asset'])
            if row.get('material'):
                api['load'](row['material'])
    removed = 0
    for actor in list(actors.values()):
        if actor.get_actor_label().startswith(PREFIX) and OWNER_TAG in [str(t) for t in actor.tags]:
            api['EAS'].destroy_actor(actor); removed += 1
    for panel in panels:
        for row in panel['parts']:
            actor = api['raw'](row['name'], row['asset'], row['location'],
                               yaw=row['yaw'], scale=row['scale'], solid=False)
            for component in actor.get_components_by_class(u.StaticMeshComponent):
                component.set_cast_shadow(False)
                if row.get('material'):
                    mat = api['balanced'](api['load'](row['material']))
                    for slot in range(component.get_num_materials()):
                        component.set_material(slot, mat)
            api['tag'](actor, OWNER_TAG); api['tag'](actor, 'OutpostRole:SkylineDisplay')
        if panel.get('text'):
            t = panel['text']
            actor = api['text'](PREFIX+panel['name']+'/District label', t['words'],
                               t['position'], t['yaw'], size=t['size'])
            actor.get_component_by_class(u.TextRenderComponent).set_cast_shadow(False)
            api['tag'](actor, OWNER_TAG)
    receipt = {'audit': evidence, 'panels': panels, 'actual_mounts': measured_mounts,
               'removed_owned_actors': removed, 'vendor_assets_modified': False,
               'provenance': 'P4 native mesh catalog plus six material overrides from original BuildingSandbox Genesis export.',
               'validation': 'Rendered appearance not yet accepted.'}
    (out/'skyline-displays.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt
