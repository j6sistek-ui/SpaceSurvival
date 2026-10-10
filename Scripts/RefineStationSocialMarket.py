"""Compose the owner's L social room and four readable market frontages.

Invoked only by the lead's guarded owner-preview transaction. This module does
not load/save maps, edit assets, or regenerate architecture. Existing source
groups stay at their saved anchors; retired furnishings remain reversibly hidden.
Distances are centimetres. Native furniture proportions and materials are kept.
"""

from OutpostGeometryUtils import mesh_union


BAR = '/Game/CyberPunkBarAssetSet01/StaticMeshes/'
FOOD = '/Game/CyberpunkRestaurant/Meshes/'
P5 = '/Game/P1toP5_Bundle/P5_FruitSeller/Blueprints/'
GRAPHITE = '/Game/OutpostSandbox/Materials/M_OutpostGraphite.M_OutpostGraphite'
WARM = (1.0, .72, .40)
CREAM = (1.0, .90, .70)
GREEN = (.65, .95, .72)
BLUE = (.65, .84, 1.0)

# Operations owns the complete primary workstation, its light assembly, service
# terminals and Engineer. Never include those prefixes in the retired furniture.
SOCIAL_RETIRE_PREFIXES = (
    'Engineering/Work bay Port/', 'Engineering/Work bay Starboard/',
    'Engineering/Diagnostic backing/', 'Engineering_Diagnostics_',
    'Engineering_DiagnosticChair_', 'Engineering_RepairBench_',
    'Engineering_PowerDock_', 'Engineering_IonCore_', 'Engineering_SparesRack_',
    'Engineering_ServiceCargo_', 'Engineering_WaitingBench_',
)
SOCIAL_RETIRE_EXACT = {'Engineering/Identity', 'Engineering/Task light',
                       'FrontLighting/Engineering workstation key'}
HIGH_SCREEN_LABELS = {'BP_ISM_Screen_V12', 'BP_ISM_Screen_V13', 'BP_ISM_Screen_V14'}
MACHINERY_KEEP_ANTS = {'BP_Meca5_Ant1', 'BP_Meca5_Ant8'}


def object_path(root, name):
    return root + name + '.' + name


def _one(actors, label):
    found = [a for a in actors if a.get_actor_label() == label]
    if len(found) != 1:
        raise RuntimeError('Expected one owner anchor %s, found %d' % (label, len(found)))
    return found[0]


def _group(actors, prefix):
    result = [a for a in actors if a.get_actor_label().startswith(prefix)]
    if not result:
        raise RuntimeError('Missing preserved source assembly: ' + prefix)
    return result


def _bounds(actors):
    # Only used for already registered saved-map actors, not newly spawned meshes.
    low, high = [float('inf')] * 3, [float('-inf')] * 3
    for actor in actors:
        center, extent = actor.get_actor_bounds(False)
        for i, axis in enumerate(('x', 'y', 'z')):
            low[i] = min(low[i], getattr(center, axis) - getattr(extent, axis))
            high[i] = max(high[i], getattr(center, axis) + getattr(extent, axis))
    return low, high


def _top(actor):
    center, extent = mesh_union(actor)
    return center.z + extent.z


def _move_grounded(ctx, actor, xy, yaw, floor=0):
    """Reuse the exact owner actor/scale; align its geometry after rotation."""
    loc = actor.get_actor_location()
    ctx.move(actor, (xy[0], xy[1], loc.z), (0, yaw, 0))
    center, extent = mesh_union(actor)
    loc = actor.get_actor_location()
    ctx.move(actor, (loc.x + xy[0] - center.x, loc.y + xy[1] - center.y,
                     loc.z + floor - center.z + extent.z))


def _standing_crew(ctx, actors, label, xy, yaw):
    # These existing clips are standing idles. Preserve their established sole
    # offset; never bury the legs in a sofa to pretend that they are seated.
    actor = _one(actors, label)
    ctx.move(actor, (xy[0], xy[1], actor.get_actor_location().z), (0, yaw, 0))


def _sign(ctx, label, text, xy, width, yaw, color, height=285):
    """A supported, opaque storefront sign, facing the actual public aisle."""
    x, y = xy
    facing = 1 if yaw == 90 else -1
    ctx.box(label + '/Backing', (x, y, height), (width, 8, 72), GRAPHITE, False)
    for side in (-1, 1):
        ctx.box(label + '/Post ' + str(side), (x + side * (width / 2 - 12), y, height / 2),
                (6, 8, height), GRAPHITE, True)
    ctx.text(label + '/Name', text, (x, y + facing * 5, height), yaw,
             size=22, color=color)


def _social(ctx, actors):
    anchor = _one(actors, 'Engineering/Roof structure')
    loc = anchor.get_actor_location()
    # The saved owner room remains 26 x 22 m, centered here. Follow its actual
    # translation instead of restoring old architectural or floor transforms.
    dx, dy = loc.x - 4200, loc.y + 3400
    if abs(anchor.get_actor_rotation().yaw) > .01:
        raise RuntimeError('L room was rotated; review furniture axes before authoring')

    def xy(x, y):
        return (x + dx, y + dy)

    def place(label, root, name, x, y, floor=0, yaw=0, collision=True):
        return ctx.grounded('Social/' + label, object_path(root, name), xy(x, y),
                            floor=floor, yaw=yaw, collision=collision)

    retired = []
    for actor in actors:
        label = actor.get_actor_label()
        if label.startswith(SOCIAL_RETIRE_PREFIXES) or label in SOCIAL_RETIRE_EXACT:
            ctx.hide(actor)
            retired.append(label)

    # One equipped 8.2 m bar, with a 2.4 m working aisle behind it. This is two
    # native matching counter sections, not a row of unrelated service desks.
    bar_left = place('Bar/Counter left', BAR, 'SM_Bardesk01', 3992.5, -4070, yaw=90)
    bar_right = place('Bar/Counter right', BAR, 'SM_Bardesk01', 4407.5, -4070, yaw=90)
    left_top, right_top = _top(bar_left), _top(bar_right)
    place('Bar/Coffee machine', BAR, 'SM_CoffeeMachine01', 3910, -4070,
          floor=left_top, yaw=90, collision=False)
    place('Bar/Coffee glasses', BAR, 'SM_CoffeeGlasses01', 4000, -4060,
          floor=left_top, collision=False)
    place('Bar/Wine glass', BAR, 'SM_Glasses02', 4430, -4060,
          floor=right_top, collision=False)
    place('Bar/Serving glasses', BAR, 'SM_Glasses01', 4310, -4060,
          floor=right_top, collision=False)
    for i, x in enumerate((3900, 4100, 4300, 4500)):
        place('Bar/Stool %d' % (i + 1), FOOD, 'SM_Stool_01', x, -3910, yaw=180)

    work = place('Bar/Preparation counter', FOOD, 'SM_Work_Table_01', 4200, -4390)
    place('Bar/Oven', BAR, 'SM_Oven01', 4250, -4390, floor=_top(work), collision=False)
    place('Bar/Drinks refrigerator', FOOD, 'SM_Refrigerator_01', 4590, -4380)
    # Solid shelf supports and native bottle props make the bar readable in the
    # room wide shot. Small serving props never obstruct character movement.
    for level, z in enumerate((190, 250)):
        ctx.box('Social/Bar/Bottle shelf %d' % level, (*xy(4190, -4435), z),
                (350, 30, 6), GRAPHITE, False)
        for i, (x, name) in enumerate(((4060, 'SM_BWineBottle01'),
                                     (4120, 'SM_BVodkaBottle01'),
                                     (4190, 'SM_BMalibuBottle01'),
                                     (4260, 'SM_BoChampagneBottle01'),
                                     (4320, 'SM_BWineBottle01'))):
            place('Bar/Bottle %d-%d' % (level, i), BAR, name, x, -4435,
                  floor=z + 3, collision=False)
    for x in (4020, 4360):
        ctx.box('Social/Bar/Shelf upright %d' % x, (*xy(x, -4443), 225),
                (5, 8, 125), GRAPHITE, False)
    _sign(ctx, 'Social/Bar/Identity', 'THE LONGER ROUTE\nCOFFEE / FOOD / FRIENDS',
          xy(4200, -4460), 600, 90, CREAM, height=348)

    # Three distinct conversation pockets leave the north doorway -> bar aisle
    # clear at X4000..4400. Native 44.5 cm tables are actual couch-table height.
    for i, (x, y) in enumerate(((3370, -3000), (5050, -3000), (3370, -3800)), 1):
        place('Conversation %d/Sofa south' % i, FOOD, 'SM_Sofa_01', x, y - 165)
        place('Conversation %d/Sofa north' % i, FOOD, 'SM_Sofa_01', x, y + 165, yaw=180)
        table = place('Conversation %d/Low table' % i, FOOD, 'SM_Table_01', x, y)
        top = _top(table)
        place('Conversation %d/Coffee' % i, BAR, 'SM_CoffeeGlasses01', x - 35, y,
              floor=top, collision=False)
        ctx.grounded('Social/Conversation %d/Shared food' % i,
                     '/Game/CyberPunkMegapack/Meshes/SM_RestaurantFood.SM_RestaurantFood',
                     xy(x + 25, y), floor=top, collision=False)

    # A separate eating/standing conversation edge, rather than more consoles.
    dining = ctx.grounded('Social/Food/Shared table',
                          '/Game/CyberPunkMegapack/Meshes/SM_CafeTable01.SM_CafeTable01',
                          xy(5050, -3570))
    for i, (x, y, yaw) in enumerate(((5050, -3430, 180), (5050, -3710, 0))):
        place('Food/Chair %d' % i, FOOD, 'SM_Stool_01', x, y, yaw=yaw)
    for i, x in enumerate((5000, 5100)):
        place('Food/Meal %d' % i, FOOD, 'SM_Food_Package_02', x, -3570,
              floor=_top(dining), collision=False)
    place('Food/Drinks', BAR, 'SM_VendingMachine01', 5320, -3810, yaw=90)
    for i, (x, y) in enumerate(((3030, -2450), (5350, -2450), (3030, -4380))):
        ctx.grounded('Social/Planter %d' % i, object_path(P5, 'BP_ISM_PlantBox_V1'),
                     xy(x, y), scale=(2.765208, 2.765208, 2.765208))

    # Relocate the owner's existing cabinets; preserve scale and native assets.
    for label, x in (('Lounge_Arcade_SpaceHunt', 4870), ('Lounge_Arcade_RetroConsole', 5140)):
        _move_grounded(ctx, _one(actors, label), xy(x, -4300), 0)
    for label in ('Lounge/Arcade name', 'Lounge/Arcade key'):
        ctx.hide(_one(actors, label))
    _sign(ctx, 'Social/Arcade/Identity', 'AFTERBURN / ARCADE', xy(5005, -4440),
          450, 90, BLUE, height=300)
    _standing_crew(ctx, actors, 'Crew/Arcade visitor', xy(4870, -4140), -90)
    _standing_crew(ctx, actors, 'Crew/Lounge guest', xy(4150, -4260), 90)
    _standing_crew(ctx, actors, 'Crew/Lounge conversation A', xy(4860, -3540), 115)
    _standing_crew(ctx, actors, 'Crew/Lounge conversation B', xy(4810, -3440), -55)

    # Local pools supplement the already installed usable room ceiling lights.
    for name, x, y, power, radius in (
            ('Bar', 4200, -4050, 1800, 650), ('West conversations', 3370, -3400, 950, 850),
            ('Food', 5000, -3500, 900, 650), ('Arcade', 5000, -4150, 500, 450)):
        ctx.light('Social/Lighting/' + name, (*xy(x, y), 300), power, radius, WARM)
    return {'retired_furnishings': retired, 'room_center': [loc.x, loc.y],
            'clear_entry_route': {'x': [4000 + dx, 4400 + dx],
                                  'y': [-3750 + dy, -2300 + dy]},
            'sofa_groups': 3, 'bar_frontage_cm': 820,
            'crew_pose': 'preserved standing clips; native seated actors are separate work'}


def _market(ctx, actors):
    groups = {name: _group(actors, 'MarketNative/' + name + '/') for name in
              ('NorthCommerce', 'SouthBotany', 'SouthMachinery', 'ArrivalProduce')}
    bounds = {name: _bounds(rows) for name, rows in groups.items()}
    arrival_low, arrival_high = bounds['ArrivalProduce']
    # Same arrival-frontage anchor; the deeper northwest bay is unoccupied in the
    # saved inventory. Keep the main public route |Y| <= 500 completely clear.
    food_x = (arrival_low[0] + arrival_high[0]) * .5
    food_y = arrival_high[1] + 80
    retired = []
    for name, group in groups.items():
        for actor in group:
            label = actor.get_actor_label()
            leaf = label.rsplit('/', 1)[-1]
            cls = actor.get_class().get_name()
            remove = name == 'ArrivalProduce'  # duplicate low produce island -> food service
            if name == 'NorthCommerce' and cls.startswith('BP_Mech'):
                remove = True  # produce identity; real mechanisms remain at machinery
            if name == 'SouthMachinery':
                if cls == 'BP_Mech5_Ant_C' and leaf not in MACHINERY_KEEP_ANTS:
                    remove = True
                if cls == 'BP_Mech3_FlyingInsect_C' and leaf != 'BP_Meca4':
                    remove = True
                # Only loose fruit actors; never strip source structure or
                # individual components out of a complete tray/arm Blueprint.
                if cls == 'StaticMeshActor' and leaf.startswith('SM_Props_Fruit'):
                    remove = True
            if name in ('NorthCommerce', 'SouthMachinery') and leaf in HIGH_SCREEN_LABELS:
                remove = True
            if remove:
                ctx.hide(actor)
                retired.append(label)

    def food(label, name, dx, dy, floor=0, yaw=0, collision=True):
        return ctx.grounded('Market/Nova/' + label, object_path(FOOD, name),
                            (food_x + dx, food_y + dy), floor=floor,
                            yaw=yaw, collision=collision)

    counter = food('Serving counter', 'SM_Bar_01', 0, 0)
    food('Preparation', 'SM_Work_Table_01', 0, 350)
    food('Cooking line', 'SM_Stove_01', 10, 560)
    food('Refrigerator', 'SM_Refrigerator_01', -305, 625)
    for i, (x, y, name) in enumerate(((-190, -50, 'SM_Food_Package_01'),
                                     (-100, -45, 'SM_Food_Package_02'),
                                     (35, -50, 'SM_Food_Package_02'),
                                     (115, -45, 'SM_Food_Package_01'))):
        food('Order %d' % i, name, x, y, floor=_top(counter), collision=False)
    food('Native Nova brand', 'SM_Nova_Sign_01', 0, 680, floor=255, collision=False)
    for side in (-1, 1):
        ctx.box('Market/Nova/Brand support ' + str(side),
                (food_x + side * 155, food_y + 680, 190), (7, 12, 380), GRAPHITE)

    nlow, nhigh = bounds['NorthCommerce']
    blow, bhigh = bounds['SouthBotany']
    mlow, mhigh = bounds['SouthMachinery']
    frontages = (
        ('Produce', 'SOL & SON\nFRESH FROM MANY WORLDS',
         ((nlow[0] + nhigh[0]) / 2, nlow[1] - 70), 720, -90, CREAM),
        ('Botany', 'VERDANT ISLES\nLIVING PLANTS / GROWING SUPPLIES',
         ((blow[0] + bhigh[0]) / 2, bhigh[1] + 65), 620, 90, GREEN),
        ('Machinery', 'KEL-TEC\nPACKING / ROBOTICS / SERVICE',
         ((mlow[0] + mhigh[0]) / 2, mhigh[1] + 65), 670, 90, BLUE),
        ('Nova', 'NOVA BITES\nHOT FOOD / LONG JOURNEYS',
         (food_x, food_y - 160), 620, -90, WARM),
    )
    for name, title, xy, width, yaw, color in frontages:
        if abs(xy[1]) < 600:
            raise RuntimeError('Vendor frontage would intrude into the arrival walk: ' + name)
        _sign(ctx, 'Market/' + name + '/Identity', title, xy, width, yaw, color)
        # Actual pack fixture housing, with a bounded pool rather than lighting
        # every duplicate decorative robot or adding unbounded point lights.
        ctx.grounded('Market/' + name + '/Task housing',
                     object_path(FOOD, 'SM_Lamp_02'), xy, floor=321,
                     collision=False)
        ctx.light('Market/' + name + '/Working light', (xy[0], xy[1], 280),
                  1200, 620, color)

    # Existing character roles now face what they do. Keep the customer's main
    # walkway open and retain their established standing-animation floor offset.
    _standing_crew(ctx, actors, 'Crew/Produce shopper', (food_x - 100, food_y - 330), 90)
    _standing_crew(ctx, actors, 'Crew/Trader B', (food_x, food_y + 220), -90)
    _standing_crew(ctx, actors, 'Crew/Botanist',
                   ((blow[0] + bhigh[0]) / 2, bhigh[1] + 160), -90)
    _standing_crew(ctx, actors, 'Crew/Machinery attendant',
                   (mhigh[0] + 110, (mlow[1] + mhigh[1]) / 2), 180)
    return {'retired_duplicates_and_repurposed_island': retired,
            'preserved_major_groups': ['NorthCommerce', 'SouthBotany', 'SouthMachinery'],
            'food_anchor': [food_x, food_y],
            'public_route': {'min_y': -500, 'max_y': 500},
            'identities': [entry[0] for entry in frontages],
            'remaining_native_checks': ['actual furniture facing', 'countertop food contacts',
                                        'pedestrian sweeps', 'sign visibility', 'rendered lighting']}


def apply(ctx):
    """Apply once to the lead's loaded owner preview; return factual changes."""
    actors = list(ctx.actors)
    if any(a.get_actor_label().startswith(('Refine/Social/', 'Refine/Market/')) for a in actors):
        raise RuntimeError('Social/market already refined; restore guarded baseline before replay')
    # Fail before any changes if this is not the saved composition we inspected.
    for label in ('Engineering/Roof structure', 'Lounge_Arcade_SpaceHunt',
                  'Lounge_Arcade_RetroConsole', 'Crew/Trader B'):
        _one(actors, label)
    for name in ('NorthCommerce', 'SouthBotany', 'SouthMachinery', 'ArrivalProduce'):
        _group(actors, 'MarketNative/' + name + '/')
    social = _social(ctx, actors)
    market = _market(ctx, actors)
    return {'module': 'social_market', 'social': social, 'market': market,
            'evidence': 'authored placement only; lead owns native visual and passage validation'}
