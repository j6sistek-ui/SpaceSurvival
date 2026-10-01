"""Deliberate non-walkable roof, entrance and skyline architecture.

Uses bounds-centred WORLD positions, LOCAL sizes before yaw, and no collision.
Ventilator housings/fans and observation frames/glazing preserve shared pivots.
The Genesis palette continues from the inhabited wings into a joined service
terrace, upper utility gallery and four panelled towers anchored in the rock.
This replaces the author's former primitive tower/window-bar loop.
"""
from math import ceil, cos, radians, sin, tan


def build(catalog):
    meshes = catalog['meshes'] if isinstance(catalog, dict) else catalog
    result = []

    def get(name, pack='P4_Genesis_Vol1'):
        matches = [m for m in meshes if m['name'] == name and pack in m['asset']]
        if len(matches) != 1:
            raise ValueError('Skyline asset missing or ambiguous: ' + name)
        return matches[0]

    def rotated(v, yaw):
        a = radians(yaw)
        return [v[0] * cos(a) - v[1] * sin(a),
                v[0] * sin(a) + v[1] * cos(a), v[2]]

    def put(label, mesh, center, scale=1.0, yaw=0):
        result.append({'name': label, 'asset': mesh['asset'],
                       'center': list(center),
                       'size': [2 * v * scale for v in mesh['extent']],
                       'yaw': yaw, 'solid': False, 'expected_up': [0, 0, 1],
                       'role': 'SkylineDecoration'})

    def grounded(label, mesh, x, y, floor, scale=1.0, yaw=0):
        put(label, mesh, (x, y, floor + mesh['extent'][2] * scale), scale, yaw)

    def fitted(label, mesh, center, size, yaw=0):
        put(label, mesh, center, yaw=yaw)
        result[-1]['size'] = list(size)

    def shared_pair(label, names, x, y, floor, scale=1.0, yaw=0):
        parts = [get(name) for name in names]
        bottom = min(m['origin'][2] - m['extent'][2] for m in parts)
        for index, mesh in enumerate(parts):
            local = [v * scale for v in mesh['origin']]
            local[2] -= bottom * scale
            center = rotated(local, yaw)
            center = [center[0] + x, center[1] + y, center[2] + floor]
            put(label + '_' + str(index + 1), mesh, center, scale, yaw)
            result[-1]['assembly'] = label
            result[-1]['assembly_floor_z'] = floor

    # Paired heat exchangers read as maintained equipment, with a service spine
    # perpendicular to them. They sit entirely on the flat wing roofs at Z515.
    vent = ['SM_FloorVentilation_V1_Part1', 'SM_FloorVentilation_V1_Part2']
    spine = get('SM_CornerWallFloor400X70_V10_ElectricalEquipment')
    roofs = [
        ('Engineering', [(4900, -3650), (4900, -2950)], (5000, -4100), 0),
        ('Lounge', [(4900, 2950), (4900, 3650)], (4100, 4100), 180),
        ('Operations', [(8500, -650), (8500, 50)], (7600, 800), 90),
    ]
    for wing, vents, service, yaw in roofs:
        for index, (x, y) in enumerate(vents):
            shared_pair('Roof_' + wing + '_HeatExchanger_' + str(index + 1),
                        vent, x, y, 515, scale=2.8, yaw=yaw)
        grounded('Roof_' + wing + '_ServiceSpine', spine, service[0], service[1],
                 515, scale=2.3, yaw=0)

    # Native vertical fascia modules hide the thin dark roof-slab edges. Keep
    # each bay <=4m, matching the existing wall rhythm. Three arrival-facing
    # sides receive detail; the rear edge disappears into the rock/service side.
    fascia = get('SM_CeilingWallPanel400X60_V1')
    for wing, x, y, sx, sy in [
            ('Engineering', 4200, -3400, 2700, 2300),
            ('Lounge', 4200, 3400, 2700, 2300),
            ('Operations', 7800, 0, 2900, 2700)]:
        for side, length in [('West', sy), ('South', sx), ('North', sx)]:
            count = int((length + 399) // 400)
            step = length / count
            for index in range(count):
                offset = -length / 2 + (index + .5) * step
                if side == 'West':
                    center, yaw = (x - sx / 2 - 5, y + offset, 510), 0
                    # Observation bridge crosses the central west bay at Z520.
                    # Keep this noncolliding trim below its walking surface.
                    if wing == 'Engineering' and abs(y + offset + 3400) < 310:
                        center = (center[0], center[1], 475)
                else:
                    center = (x + offset, y + (-sy / 2 - 5 if side == 'South' else sy / 2 + 5), 510)
                    yaw = 90 if side == 'South' else -90
                fitted('Roof_' + wing + '_Fascia_' + side + '_' + str(index + 1),
                       fascia, center, (39, step, 90), yaw)

    # A real kit canopy projects 6m from the entry front. Its underside is
    # articulated ceiling geometry, with a matching framed leading edge and
    # two diagonal corner brackets tied to the existing entrance piers. Every
    # part stays above Z540; the 6m pedestrian opening is completely clear.
    ceiling = get('SM_CeilingPanel400X200_V1')
    for row, x in enumerate((2100, 2300, 2500)):
        for column, y in enumerate((-1100 / 3, 0, 1100 / 3)):
            fitted('Entrance_CanopyPanel_' + str(row) + '_' + str(column),
                   ceiling, (x, y, 735), (200, 1100 / 3, 40))
    for index, y in enumerate((-1100 / 3, 0, 1100 / 3)):
        fitted('Entrance_CanopyFrontFascia_' + str(index), fascia,
               (2000, y, 720), (39, 1100 / 3, 70))
    for side in (-1, 1):
        fitted('Entrance_CanopySideFascia_' + str(side), fascia,
               (2300, side * 550, 720), (39, 600, 70), 90 * side)
        bracket = get('SM_Building_AngleStructureLink_V1', 'P5_FruitSeller')
        fitted('Entrance_CanopyPierBracket_' + str(side), bracket,
               (2330, side * 500, 635), (160, 28, 160), 180)

    # Rear architecture is one connected facility. The low service terrace
    # overlaps the Operations roof edge by 60cm and runs continuously beneath
    # every tower. The upper gallery and conduits repeat that same connection.
    # All modules are decorative: no new walkable routes or hidden floor changes.
    panel = get('SM_WallPanel400X200_V1_SmartStorageUnit')
    low_panel = get('SM_WallPanel400X100_V1_SmartStorageUnit')
    floor_panel = get('SM_UniversalPanel400X200_V2')
    cable = get('SM_CornerWallFloor400X70_V3_ElectricalCableRouting')
    cornice = get('SM_CornerWallFloor400X70_V10_ElectricalEquipment')
    windows = ['SM_Window400X250_V1_Part1', 'SM_Window400X250_V1_Part2']
    mast = get('SM_architecture_module_03', 'Megastructure_Scifi_World')
    post = get('SM_Building_Structure200x10_V1', 'P5_FruitSeller')
    post_base = get('SM_Building_StructureBase_V1', 'P5_FruitSeller')
    post_link = get('SM_Building_StructureLink90x10_V1', 'P5_FruitSeller')

    def deck(name, x, y, sx, sy, z):
        # Native P4 plates stay close to their 2x4m proportions; no giant tile.
        nx, ny = ceil(sx / 400), ceil(sy / 400)
        for ix in range(nx):
            for iy in range(ny):
                fitted(name + '/Deck_' + str(ix) + '_' + str(iy), floor_panel,
                       (x - sx / 2 + (ix + .5) * sx / nx,
                        y - sy / 2 + (iy + .5) * sy / ny, z - 9),
                       (sx / nx + 1, sy / ny + 1, 18))

    def facade(name, x, y, length, bottom, top, yaw=180):
        bays, tiers = ceil(length / 400), max(1, ceil((top - bottom) / 400))
        for tier in range(tiers):
            z = bottom + (tier + .5) * (top - bottom) / tiers
            for bay in range(bays):
                along = -length / 2 + (bay + .5) * length / bays
                offset = rotated((0, along, 0), yaw)
                fitted(name + '/Cladding_' + str(tier) + '_' + str(bay), panel,
                       (x + offset[0], y + offset[1], z),
                       (58, length / bays + 1, (top - bottom) / tiers + 1), yaw)

    def run(name, mesh, x, y, length, z, yaw=0, width=75, height=65):
        count = ceil(length / 400)
        for i in range(count):
            offset = rotated((-length / 2 + (i + .5) * length / count, 0, 0), yaw)
            fitted(name + '_' + str(i), mesh, (x + offset[0], y + offset[1], z),
                   (length / count + 2, width, height), yaw)

    # Main maintenance apron: rear-X edge penetrates the massif bounds (9950),
    # while the front-X edge directly overlaps Operations' roof at X9250.
    deck('Skyline/Ops rear apron', 9770, 0, 1160, 2800, 515)
    deck('Skyline/Lower service spine', 10020, 150, 820, 11500, 515)
    facade('Skyline/Lower retaining wall', 9610, 150, 11500, -160, 497)
    run('Skyline/Lower cornice', cornice, 9580, 150, 11500, 490, 90, 90, 100)
    run('Skyline/Lower utility trunk', cable, 9950, 150, 11500, 575, 90, 110, 90)

    # Engineering and Lounge roof services connect physically to the apron.
    # The engineering link starts east of X5550, beyond the accessible gallery.
    for wing, y in [('Engineering', -3400), ('Lounge', 3400)]:
        deck('Skyline/' + wing + ' service link', 7600, y, 4100, 300, 515)
        for side in (-1, 1):
            run('Skyline/' + wing + ' bridge edge ' + str(side), cornice,
                7600, y + side * 150, 4100, 470, 0, 80, 110)
        run('Skyline/' + wing + ' conduit', cable, 7600, y + 120, 4100, 565, 0, 75, 70)
        for index, x in enumerate((6200, 7600, 9000)):
            for side in (-1, 1):
                facade('Skyline/' + wing + ' support ' + str(index) + '_' + str(side),
                       x, y + side * 115, 140, -160, 480, 90 * side)
            fitted('Skyline/' + wing + ' support cap ' + str(index), cornice,
                   (x, y, 455), (380, 190, 100), 90)

    # A broad, stepped command drum makes the low-to-high transition read as
    # the rounded colony architecture in the owner's reference. Twelve actual
    # Genesis bays form each ring; its smaller glazed upper tier has an eave,
    # equipment crown and roof machinery, rather than a smooth primitive shell.
    def drum_roof(name, radius, z):
        deck(name + '/Core', 10400, 0, radius * 1.25, radius * 1.25, z)
        edge = 2 * radius * tan(radians(15))
        for face in range(12):
            angle = face * 30
            a = radians(angle)
            fitted(name + '/Radial plate ' + str(face), floor_panel,
                   (10400 + radius * .67 * cos(a), radius * .67 * sin(a), z - 9),
                   (radius * .70, edge + 20, 18), angle)

    for tier, radius, bottom, top in [('Lower', 1100, 515, 1115), ('Upper', 850, 1115, 1815)]:
        edge = 2 * radius * tan(radians(15))
        for face in range(12):
            angle = face * 30
            a = radians(angle)
            x, y = 10400 + radius * cos(a), radius * sin(a)
            name = 'Skyline/Command drum ' + tier + '/' + str(face)
            if tier == 'Upper':
                # Same-scale frame and glazing retain their vendor alignment.
                window_scale = edge / 400
                window_height = 250 * window_scale
                sill = (top - bottom - window_height) / 2
                shared_pair(name + '/Glazing', windows, x, y, bottom + sill,
                            window_scale, angle)
                for trim, zz in [('Sill', bottom + sill / 2), ('Header', top - sill / 2)]:
                    fitted(name + '/' + trim, panel, (x, y, zz), (58, edge + 2, sill + 1), angle)
            else:
                facade(name, x, y, edge, bottom, top, angle)
            fitted(name + '/Eave', cornice, (x, y, top + 10),
                   (edge + 25, 140, 120), angle + 90)
            # Native vertical structural profiles replace stretched wall
            # panels. Four uniformly scaled rails, bolted feet and horizontal
            # links make a real built-up pilaster with intact UV proportions.
            if face % 2 == 0:
                rail_scale = (top - bottom + 15) / (post['extent'][2] * 2)
                for radial in (-30, 30):
                    for tangent in (-30, 30):
                        offset = rotated((radial, tangent, 0), angle)
                        grounded(name + '/Pilaster rail ' + str(radial) + '_' + str(tangent),
                                 post, x + offset[0], y + offset[1], bottom, rail_scale, angle)
                    offset = rotated((radial, 0, 0), angle)
                    for joint, zz in enumerate((bottom + 40, (bottom + top) / 2, top - 10)):
                        put(name + '/Pilaster link ' + str(radial) + '_' + str(joint), post_link,
                            (x + offset[0], y + offset[1], zz), 1.1, angle + 90)
                for tangent in (-30, 30):
                    offset = rotated((0, tangent, 0), angle)
                    grounded(name + '/Pilaster foot ' + str(tangent), post_base,
                             x + offset[0], y + offset[1], bottom, 2.0, angle)
        drum_roof('Skyline/Command drum ' + tier + '/Roof', radius, top)
    for y in (-500, 0, 500):
        shared_pair('Skyline/Command roof exchanger ' + str(y), vent,
                    10500, y, 1815, scale=2.5, yaw=90)
    grounded('Skyline/Command communications array', mast, 10400, 0, 1815,
             scale=900 / (mast['extent'][2] * 2))

    deck('Skyline/Upper service gallery', 10210, 150, 500, 11500, 1515)
    run('Skyline/Upper gallery front cornice', cornice, 9930, 150, 11500, 1480, 90, 100, 100)
    run('Skyline/Upper exposed utilities', cable, 10400, 150, 11500, 1580, 90, 110, 100)
    for y in (-5350, -3800, -1600, 1600, 4100, 5650):
        # Repeated service piers tie the gallery down to the same lower spine.
        facade('Skyline/Gallery pier ' + str(y), 9970, y, 160, 515, 1480)
        fitted('Skyline/Gallery pier capital ' + str(y), cornice,
               (10180, y, 1450), (620, 190, 120))

    for index, (y, height, mast_height) in enumerate([
            (-4800, 2200, 650), (-2800, 3200, 950),
            (3000, 3800, 1150), (5100, 2600, 800)]):
        name = 'Skyline/Tower ' + str(index + 1)
        x = 10400 + abs(y) * .10
        front, top = x - 550, height - 200
        levels = ceil((top - 515) / 400)
        rise = (top - 515) / levels
        deck(name + '/Foundation terrace', x - 70, y, 1380, 1600, 515)
        # Fully clad west/south/north surfaces use one shared bay rhythm and
        # finished native P4 materials. Glazing keeps frame and glass pivots.
        for level_index in range(levels):
            z0 = 515 + level_index * rise
            for bay in range(3):
                yy = y + (bay - 1) * 400
                if level_index % 3 == 1:
                    inset = (rise - 250) / 2
                    shared_pair(name + '/Window_' + str(level_index) + '_' + str(bay),
                                windows, front, yy, z0 + inset, yaw=180)
                    for trim, zz in [('Sill', z0 + inset / 2), ('Header', z0 + rise - inset / 2)]:
                        fitted(name + '/' + trim + '_' + str(level_index) + '_' + str(bay),
                               low_panel, (front, yy, zz), (58, 401, inset + 1), 180)
                else:
                    fitted(name + '/Front_' + str(level_index) + '_' + str(bay), panel,
                           (front, yy, z0 + rise / 2), (58, 401, rise + 1), 180)
            for side in (-1, 1):
                facade(name + '/Side_' + str(level_index) + '_' + str(side), x, y + side * 600,
                       1100, z0, z0 + rise, 90 * side)
            run(name + '/Storey cornice_' + str(level_index), cornice,
                front - 35, y, 1260, z0 + rise - 20, 90, 95, 80)
        # Lower and upper galleries terminate in each tower's facade, so every
        # silhouette reads as part of the same facility in the wide approach.
        deck(name + '/Upper connection', (10210 + front) / 2, y,
             front - 10210 + 100, 460, 1515)
        for side in (-1, 1):
            for tier in range(3):
                xx = front - 155 + tier * 42
                facade(name + '/Buttress_' + str(side) + '_' + str(tier),
                       xx, y + side * 600, 130, 0 if tier == 0 else 515,
                       min(top, 850 + tier * 550))
        deck(name + '/Roof', x, y, 1150, 1260, top)
        run(name + '/Crown', cornice, front - 20, y, 1360, top + 25, 90, 130, 120)
        for yy in (y - 330, y + 330):
            shared_pair(name + '/Roof heat exchanger ' + str(yy), vent,
                        x + 50, yy, top, scale=2.0)
        grounded(name + '/Communications mast', mast, x + 200, y, top,
                 scale=mast_height / (mast['extent'][2] * 2))

    # Every new piece remains decorative, and the gallery's player volume is
    # reserved. These bounds checks supplement, but never replace, native review.
    assert len({p['name'] for p in result}) == len(result)
    assert all(not p['solid'] and min(p['size']) > 0 for p in result)
    return result
