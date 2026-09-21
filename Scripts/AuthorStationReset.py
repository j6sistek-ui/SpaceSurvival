"""Author the separate industrial asteroid station Blueprint in the owner's editor.

Run only through the integration lead's serialized Unreal authoring session. The default
measures licensed meshes and emits a reviewable recipe. -SSApplyStationReset compiles/saves
only BP_StationReset after checking its ownership receipt. The prior Blueprint is untouched.
All geometry is in station-local centimetres. Recipe rotation is [pitch, yaw, roll].
"""
import json
import math
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

PACKAGE = "/Game/SpaceSurvival/Licensed/StationReset/BP_StationReset"
ROOT = Path(__file__).resolve().parents[1]
PROPS = "/Game/StarterBundle/ModularScifiProps/Meshes/"
COMM = "/Game/StarterBundle/ModularSci_Comm/Meshes/"
INDUSTRIAL = "/Game/SciFiCorridor/Meshes/"
TERMINAL = COMM + "SM_Terminal_A"
TERMINAL_UI = COMM + "SM_Terminal_A_UI"
COLONY_HABITAT = "/Game/SpaceSurvival/Licensed/StationReset/ColonyHabitat/SM_ColonyHabitat"
ASTEROID = "/Game/SpaceSurvival/Licensed/StationReset/SM_StationAsteroid"
FLOOR_Z = -10.0


def rotated_vector(vector, rotation):
    """UE FRotator local-to-world basis (pitch, yaw, roll), also used by geometric guards."""
    pitch, yaw, roll = [math.radians(v) for v in rotation]
    sp, cp, sy, cy, sr, cr = math.sin(pitch), math.cos(pitch), math.sin(yaw), math.cos(yaw), math.sin(roll), math.cos(roll)
    x, y, z = vector
    return [x * cp * cy + y * (sr * sp * cy - cr * sy) - z * (cr * sp * cy + sr * sy),
            x * cp * sy + y * (sr * sp * sy + cr * cy) + z * (sr * cy - cr * sp * sy),
            x * sp - y * sr * cp + z * cr * cp]


def build_recipe(measure):
    """Build solely from measured bounds; no pivot assumptions or arbitrary grounding offsets."""
    meshes, boxes, lights, anchors, placements, staff, capsules = [], [], [], [], [], [], []
    cache = {}

    def inventory(asset):
        if asset not in cache:
            cache[asset] = measure(asset)
        return cache[asset]

    def box(name, center, size, floor=False):
        boxes.append(dict(name=name, location=list(center), rotation=[0, 0, 0], scale=[1, 1, 1],
                          extent=[value / 2 for value in size], walk_floor=floor))

    def fitted(name, asset, center, size, yaw=0, solid=False, materials=None):
        row = inventory(asset)
        origin, extent = row["origin"], row["extent"]
        assert all(value > 0 for value in extent), (asset, extent)
        # Desired size is world-aligned. The local X/Y dimensions swap for a quarter turn.
        quarter = int(round(yaw / 90)) % 2
        local_size = [size[1], size[0], size[2]] if quarter else list(size)
        scale = [local_size[i] / (2 * extent[i]) for i in range(3)]
        angle = math.radians(yaw)
        offset = [origin[i] * scale[i] for i in range(3)]
        rotated = [math.cos(angle) * offset[0] - math.sin(angle) * offset[1],
                   math.sin(angle) * offset[0] + math.cos(angle) * offset[1], offset[2]]
        mats = materials or row["materials"]
        assert mats and all(mats), ("Missing material slot", asset, mats)
        meshes.append(dict(name=name, asset=asset, location=[center[i] - rotated[i] for i in range(3)],
                           rotation=[0, yaw, 0], scale=scale, materials=mats, cast_shadows=True))
        placements.append(dict(name=name, asset=asset, center=list(center), size=list(size), solid=solid))
        if solid:
            box(name, center, size)
        return meshes[-1]

    def placed(name, asset, location, scale, rotation, triangle_collision=False, materials=None):
        row = inventory(asset)
        origin = rotated_vector([row["origin"][i] * scale[i] for i in range(3)], rotation)
        axes = [rotated_vector([row["extent"][i] * scale[i] if i == axis else 0 for i in range(3)], rotation)
                for axis in range(3)]
        size = [2 * sum(abs(axes[axis][i]) for axis in range(3)) for i in range(3)]
        meshes.append(dict(name=name, asset=asset, location=list(location), rotation=list(rotation), scale=list(scale),
                           materials=materials or row["materials"], cast_shadows=True,
                           triangle_collision=triangle_collision))
        placements.append(dict(name=name, asset=asset, center=[location[i] + origin[i] for i in range(3)],
                               size=size, solid=triangle_collision))

    def grounded_uniform(name, asset, x, y, floor, height, yaw):
        row = inventory(asset)
        scale = height / (2 * row["extent"][2])
        origin = rotated_vector([value * scale for value in row["origin"]], [0, yaw, 0])
        placed(name, asset, [x - origin[0], y - origin[1], floor + height / 2 - origin[2]],
               [scale] * 3, [0, yaw, 0])

    cube = "/Engine/BasicShapes/Cube"
    hull = ["/Game/SpaceSurvival/Materials/M_Hull.M_Hull"]
    cyan = ["/Game/SpaceSurvival/Materials/M_Cyan.M_Cyan"]
    gold = ["/Game/SpaceSurvival/Materials/M_Gold.M_Gold"]
    graphite = ["/Game/SpaceSurvival/Materials/M_StationShell_GraphiteAlloy.M_StationShell_GraphiteAlloy"]
    blue_grey = ["/Game/SpaceSurvival/Materials/M_StationShell_BlueGreyPanels.M_StationShell_BlueGreyPanels"]
    ochre = ["/Game/SpaceSurvival/Materials/M_StationShell_SafetyOchre.M_StationShell_SafetyOchre"]
    # One coherent floor and exterior foundation; floor top is exactly the existing pad/walkway top.
    fitted("Foundation", cube, (100, 0, -125), (4080, 3080, 180), materials=hull)
    # Three connected tiers and narrow inset bands give the outpost a deliberate engineered silhouette.
    # These are exterior massing below the usable floor, not pretend rooms or walkable ornamental decks.
    fitted("LowerHull", cube, (100, 0, -285), (4340, 3340, 190), materials=hull)
    fitted("InsetKeel", cube, (100, 0, -485), (3620, 2700, 210), materials=hull)
    for side in (-1, 1):
        fitted(f"HullBelt_{side}", cube, (100, side * 1675, -220), (4080, 10, 16), materials=cyan)
        for x in (-1500, -500, 500, 1500):
            fitted(f"HullPlate_{side}_{x}", PROPS + "SM_Wall_A", (x, side * 1645, -305),
                   (900, 60, 130), yaw=180 if side > 0 else 0)
    box("Floor_Main", (100, 0, -60), (4000, 3000, 100), floor=True)
    for ix in range(8):
        for iy in range(6):
            center = (-1650 + ix * 500, -1250 + iy * 500, FLOOR_Z - 11)
            fitted(f"Deck_{ix}_{iy}", INDUSTRIAL + "SM_Floor_01", center, (500, 500, 22))
            fitted(f"Ceiling_{ix}_{iy}", INDUSTRIAL + "SM_Celling_01", (center[0], center[1], 527.5), (500, 500, 35))
    box("Ceiling_Main", (100, 0, 527.5), (4000, 3000, 35))
    # The exterior used to read as the same flat tiled plane as the floor. A low perimeter cap and
    # four attached stiffeners articulate the existing roof, within its footprint, without new rooms.
    # Every part starts at the measured ceiling top Z545; the highest edge is only Z635.
    for side in (-1, 1):
        fitted(f"ExteriorRoofEdge_{side}", cube, (100, side * 1460, 590), (4000, 80, 90), materials=blue_grey, solid=True)
    for x in (-1860, 2060):
        fitted(f"ExteriorRoofEnd_{x}", cube, (x, 0, 590), (80, 2840, 90), materials=blue_grey, solid=True)
    for x in (-1250, -350, 550, 1450):
        fitted(f"ExteriorRoofRib_{x}", cube, (x, 0, 567), (80, 2840, 44), materials=graphite, solid=True)
    # Modular walls have matching deliberate solids. The west wall leaves a ten metre opening aligned
    # to the eight metre pad walkway; no door leaf or invisible old hangar wall obstructs that route.
    for side, label in ((-1, "South"), (1, "North")):
        for ix in range(8):
            fitted(f"WallPanel_{label}_{ix}", INDUSTRIAL + "SM_Wall_03",
                   (-1650 + ix * 500, side * 1530, 250), (500, 60, 520), yaw=180 if side > 0 else 0)
        box(f"Wall_{label}", (100, side * 1530, 250), (4000, 60, 520))
    # This bulkhead faces the asteroid interior. The real view to space is through the west pad portal;
    # placing an observation window here only framed the rock a few metres beyond it in visual cycle1.
    for iy in range(6):
        fitted(f"WallPanel_East_{iy}", INDUSTRIAL + "SM_Wall_03", (2130, -1250 + iy * 500, 250),
               (60, 500, 520), yaw=90)
    box("Wall_East", (2130, 0, 250), (60, 3000, 520))
    for y in (-1250, -750, 750, 1250):
        fitted(f"WallPanel_Entry_{y}", INDUSTRIAL + "SM_Wall_03", (-1930, y, 250),
               (60, 500, 520), yaw=270)
        box(f"Wall_Entry_{y}", (-1930, y, 250), (60, 500, 520))
    fitted("EntryHeader", cube, (-1930, 0, 475), (80, 1000, 70), materials=hull, solid=True)
    fitted("EntryLight", cube, (-1878, 0, 435), (8, 960, 10), materials=cyan)
    # Face-mounted framing makes the existing portal legible from the pad. It remains outside the
    # ten-metre opening, and the lintel starts at Z440, exactly like the existing physical header.
    fitted("ExteriorEntryHeader", cube, (-1975, 0, 475), (50, 1200, 70), materials=blue_grey, solid=True)
    for side in (-1, 1):
        fitted(f"ExteriorEntryPost_{side}", INDUSTRIAL + "SM_Pilar", (-1950, side * 550, 250),
               (100, 100, 520), solid=True)
        fitted(f"ExteriorEntryStripe_{side}", cube, (-2001, side * 580, 250), (2, 12, 450), materials=ochre)
        fitted(f"ExteriorEntryLamp_{side}", cube, (-2002, side * 530, 320), (4, 12, 140), materials=cyan)
        lights.append(dict(name=f"EntryFaceFill_{side}", location=[-2015, side * 540, 310],
                           rotation=[0, 0, 0], scale=[1, 1, 1], color=[.42, .68, 1.0],
                           intensity=16000, attenuation_radius=1600, cast_shadows=False))
    # Four structural columns touch floor and ceiling and have their own narrow physical footprints.
    for x, y, label in ((-1700, -1350, "SW"), (-1700, 1350, "NW"),
                         (1650, -1350, "SE"), (1650, 1350, "NE")):
        fitted(f"Column_{label}", INDUSTRIAL + "SM_Pilar", (x, y, 250), (90, 90, 520), solid=True)
    # Attached ceiling ribs and perimeter conduits give the industrial reference its structural rhythm.
    # Every piece meets a wall/ceiling face; nothing is suspended mid-room without a supporting surface.
    for x in (-1600, -600, 400, 1400):
        fitted(f"CeilingRib_{x}", cube, (x, 0, 490), (55, 3000, 40), materials=hull)
    for side in (-1, 1):
        for height in (385, 430):
            fitted(f"WallConduit_{side}_{height}", COMM + "SM_Wall_Pipe_A", (100, side * 1480, height),
                   (3900, 35, 35))
    # Continuous circulation strips are inlaid at the same floor, keeping the service aisle clear.
    for y in (-400, 400):
        fitted(f"AisleLine_{y}", cube, (100, y, FLOOR_Z + .3), (3850, 5, .6), materials=cyan)
    for x in (-1400, -600, 200, 1000):
        for sign in (-1, 1):
            fitted(f"ServiceLane_{x}_{sign}", cube, (x, sign * 650, FLOOR_Z + .3),
                   (5, 500, .6), materials=cyan)
    # Console centres are deliberately separated. An anchor sits 190 cm toward the central aisle, so
    # interacting never requires standing inside the terminal's collision. Labels are native, factual
    # home/station-specific UI; every console opens its existing panel, including wardrobe at home.
    services = [
        ("Paint", -1400, -1100, 0, (0, 190)), ("Repair", -600, -1100, 0, (0, 190)),
        ("Loadout", 200, -1100, 0, (0, 190)), ("Launch", 1000, -1100, 0, (0, 190)),
        ("Wardrobe", -1400, 1100, 180, (0, -190)), ("Contracts", -600, 1100, 180, (0, -190)),
        ("Systems", 200, 1100, 180, (0, -190)), ("Modules", 1000, 1100, 180, (0, -190)),
        ("Gallery", 1800, -500, 90, (-190, 0)), ("Beacon", 1800, 500, 90, (-190, 0)),
    ]
    for kind, x, y, yaw, offset in services:
        # The first reviewed recipe accidentally chose a luminous display sculpture. This is the
        # supplied curved command console and its matching UI overlay, kept at one uniform scale and
        # the exact shared authored transform. Source +X is the open operator side, facing the aisle.
        measured = inventory(TERMINAL)
        scale = 110.0 / (2 * measured["extent"][2])
        heading = yaw + 90
        size = [2 * e * scale for e in measured["extent"]]
        if int(round(heading / 90)) % 2:
            size[0], size[1] = size[1], size[0]
        console = fitted(f"Console_{kind}", TERMINAL, (x, y, FLOOR_Z + 55), size,
                         yaw=heading, solid=True)
        placed(f"ConsoleDisplay_{kind}", TERMINAL_UI, console["location"], console["scale"], console["rotation"])
        # A thin, grounded base belongs to its terminal and reinforces the intentional service zone.
        fitted(f"ConsoleBase_{kind}", cube, (x, y, FLOOR_Z + 2), (size[0] + 18, size[1] + 18, 4),
               materials=gold if kind == "Launch" else hull)
        anchors.append(dict(name=f"Service_{kind}", service=kind,
                            location=[x + offset[0], y + offset[1], FLOOR_Z],
                            rotation=[0, 0, 0], scale=[1, 1, 1]))
    # Human-scale bays articulate the large service hall. Each lower canopy meets the perimeter wall
    # and has grounded narrow dividers outside every service approach and the central circulation lane.
    for side in (-1, 1):
        for x in (-1800, -1000, -200, 600, 1400):
            fitted(f"BayDivider_{side}_{x}", INDUSTRIAL + "SM_Pilar", (x, side * 1340, 150),
                   (60, 300, 320), solid=True)
        for x in (-1400, -600, 200, 1000):
            fitted(f"BayCanopy_{side}_{x}", INDUSTRIAL + "SM_Celling_01", (x, side * 1310, 322),
                   (740, 420, 35))
            fitted(f"BayFascia_{side}_{x}", PROPS + "SM_Wall_A", (x, side * 1105, 313),
                   (710, 35, 55))
            fitted(f"BayTaskStrip_{side}_{x}", cube, (x, side * 1220, 300), (260, 12, 4), materials=gold)
            lights.append(dict(name=f"BayTaskLight_{side}_{x}", location=[x, side * 1200, 280],
                               rotation=[0, 0, 0], scale=[1, 1, 1], color=[1.0, .77, .48],
                               intensity=14000, attenuation_radius=620, cast_shadows=False))
    # Fixtures serve a named purpose and sit against supported bay walls, with matching body blockers.
    for x in (-1530, -1270):
        fitted(f"WardrobeLocker_{x}", PROPS + "SM_WallCab_2D", (x, 1440, 145),
               (220, 110, 310), solid=True)
    fitted("RepairStorage", PROPS + "SM_Cabinet_A", (-600, -1410, 70), (430, 140, 160), solid=True)
    fitted("PaintSupplyRack", PROPS + "SM_Shelf_A_v2", (-1400, -1410, 100), (430, 120, 220), solid=True)
    fitted("SystemsStorage", PROPS + "SM_Cabinet_B", (200, 1420, 70), (430, 140, 160), solid=True)
    # Background fill supports the warm pools instead of illuminating every metal panel equally.
    for x in (-1300, -300, 700, 1700):
        for y in (-950, 0, 950):
            fitted(f"Luminaire_{x}_{y}", cube, (x, y, 502), (180, 60, 8), materials=cyan if y == 0 else gold)
            lights.append(dict(name=f"Light_{x}_{y}", location=[x, y, 445], rotation=[0, 0, 0], scale=[1, 1, 1],
                               color=[.62, .80, 1.0] if y == 0 else [1.0, .65, .32],
                               intensity=18000 if y == 0 else 9000, attenuation_radius=850, cast_shadows=False))
    # The inside and pad are separated by a roofed, readable doorway, while pad flight clearance stays
    # untouched. Four low rails protect the sides of the connecting walkway but leave its full width.
    for y in (-445, 445):
        fitted(f"BridgeRail_{y}", cube, (-2430, y, 45), (920, 40, 110), materials=hull, solid=True)
        fitted(f"BridgeRailLight_{y}", cube, (-2430, y, 101), (920, 8, 2), materials=cyan)
        fitted(f"BridgeSupport_{y}", cube, (-2430, y, -180), (780, 90, 340), materials=hull)
        lights.append(dict(name=f"BridgeRailFill_{y}", location=[-2500, math.copysign(410, y), 110],
                           rotation=[0, 0, 0], scale=[1, 1, 1], color=[.42, .68, 1.0],
                           intensity=3000, attenuation_radius=1200, cast_shadows=False))
    # Cycle2 exposed black-on-black deck/gear immediately beside the possessed walker. These small
    # pools sit just inside four existing 110cm rail light strips, below the hull, and model local
    # reflected task light. They do not change exposure, the sky/key, collision or the landing path.
    for degrees in (60, 120, 240, 300):
        angle = math.radians(degrees)
        lights.append(dict(name=f"PadRailFill_{degrees}",
                           location=[-4500 + 1515 * math.cos(angle), 1515 * math.sin(angle), 85],
                           rotation=[0, 0, 0], scale=[1, 1, 1], color=[.42, .68, 1.0],
                           intensity=6500, attenuation_radius=1900, cast_shadows=False))
    # The cavity's front is open space: two continuous cantilever beams carry the pad back into the
    # rock-embedded main foundation. The four uprights meet those beams, not an imaginary ground plane.
    for y in (-950, 950):
        fitted(f"DockSpine_{y}", cube, (-1975, y, -665), (8150, 190, 150), materials=hull)
    for x in (-5450, -3550):
        for y in (-950, 950):
            fitted(f"PadSupport_{x}_{y}", cube, (x, y, -445), (150, 150, 330), materials=hull, solid=True)
    for x in (-5000, -3500, -2000, -500, 1000):
        fitted(f"DockCrossmember_{x}", cube, (x, 0, -620), (120, 2090, 100), materials=hull)

    # Measured against all 5,464,576 source triangles before authoring: this pose turns the cavity
    # axis to -X and leaves the complete 40x30m concourse clear. The derived mesh preserves that frame.
    # The private mesh uses its measured Nanite fallback triangles for collision. The original convex
    # shell is removed so the bowl stays open; the station owns a separate non-simulated native proxy.
    placed("AsteroidHabitat", ASTEROID, [7500, 0, 5300], [145, 145, 145],
           [34.319873, -22.187753, -6.929723], triangle_collision=True,
           materials=["/Game/SpaceSurvival/Licensed/StationReset/Materials/MI_StationAsteroid.MI_StationAsteroid"])

    # Two compact side terraces carry the measured owned Figur habitat derivative. Source-triangle corner
    # probes place them forward of the closing back wall: x[-2000,0], |y|[4500,6500]. The highest
    # probed rock floor is554cm, so a750cm terrace clears it. Their outer/front corners have no rock;
    # paired cantilever beams return to measured rock-supported rear anchors instead of floating legs.
    plate = "/Game/Megastructure_Scifi_World/Meshes/Floor/SM_floor_module_01"
    for side, label in ((1, "North"), (-1, "South")):
        fitted(f"ColonyTerrace_{label}", plate, (-1000, side * 5500, 650), (2000, 2000, 200))
        for distance, rock_floor in ((4500, -1017.3 if side > 0 else -1936.7),
                                     (6500, 554.0 if side > 0 else -148.6)):
            fitted(f"ColonyBeam_{label}_{distance}", cube, (-1000, side * distance, 475),
                   (2200, 200, 150), materials=hull)
            bottom, top = rock_floor - 150, 550
            fitted(f"ColonyRockAnchor_{label}_{distance}", cube,
                   (0, side * distance, (bottom + top) / 2), (200, 200, top - bottom), materials=hull)
        # A connected raised maintenance bridge is visible from the pad. It terminates against the
        # station roof structure; the playable concourse remains intentionally bounded by its walls.
        fitted(f"ColonyBridge_{label}", plate, (-1000, side * 2950, 650), (600, 3100, 200))
        for edge in (-1320, -680):
            fitted(f"ColonyBridgeRail_{label}_{edge}", cube, (edge, side * 2950, 800),
                   (35, 3100, 100), materials=hull)
            fitted(f"ColonyBridgeLight_{label}_{edge}", cube, (edge, side * 2950, 851),
                   (8, 3060, 2), materials=cyan)
        fitted(f"ColonyBridgeRoot_{label}", cube, (-1000, side * 1470, 470), (600, 120, 360), materials=hull)
        measured = inventory(COLONY_HABITAT)
        height = min(4500, 1800 * measured["extent"][2] / max(measured["extent"][:2]))
        grounded_uniform(f"ColonyHabitat_{label}", COLONY_HABITAT, -1000, side * 5500,
                         750, height, 270 if side > 0 else 90)
        for index, distance in enumerate((4950, 6050)):
            lights.append(dict(name=f"ColonyLight_{label}_{index}",
                               location=[-1950, side * distance, 1150],
                               rotation=[0, 0, 0], scale=[1, 1, 1], color=[.5, .75, 1], intensity=65000,
                               attenuation_radius=2200, cast_shadows=False))

    # Two purposeful staff replace the previous scattered crowd. Body meshes preserve uniform scale,
    # a matching authored idle, measured sole placement and a native capsule at that exact body position.
    robot = "/Game/Robot_scout_R_21/Mesh/SK_Robot_scout_R21"
    idle = "/Game/Robot_scout_R_21/Demo/Animations/ThirdPersonIdle"
    body = inventory(robot)
    staff_scale = 190.0 / (2 * body["extent"][2])
    for role, x, y, heading in (("Mica", 1150, 1320, -90), ("Dockmaster", -1650, -650, 0)):
        yaw = heading - 90  # The source UE4 mannequin faces +Y.
        angle = math.radians(yaw)
        origin = [v * staff_scale for v in body["origin"]]
        rotated = [math.cos(angle) * origin[0] - math.sin(angle) * origin[1],
                   math.sin(angle) * origin[0] + math.cos(angle) * origin[1], origin[2]]
        center = [x, y, FLOOR_Z + 95]
        staff.append(dict(name="Staff_" + role, asset=robot, animation=idle,
                          location=[center[i] - rotated[i] for i in range(3)], rotation=[0, yaw, 0],
                          scale=[staff_scale] * 3))
        capsules.append(dict(name="StaffBody_" + role, location=center, rotation=[0, 0, 0], scale=[1, 1, 1],
                             radius=38, half_height=95))

    for group in (meshes, placements, lights, anchors):
        for row in group:
            row["name"] = row["name"].replace("-", "n")
    names = [row["name"] for row in meshes] + [row["name"] for row in anchors]
    # Collision specs are prefixed because SCS names are globally unique across component classes.
    for row in boxes:
        row["name"] = "Collision_" + row["name"].replace("-", "n")
    names += [row["name"] for row in boxes + lights + staff + capsules]
    assert len(names) == len(set(names)), "Duplicate Blueprint component name"
    assert len(anchors) == 10
    return dict(functional_layout=True, exclude_harvested=["*"], static_meshes=meshes,
                collision_boxes=boxes, service_anchors=anchors, point_lights=lights,
                skeletal_meshes=staff, collision_capsules=capsules), placements, cache


def verify_final_trim_clearance(u, placements, out):
    """Check the added trim against the actual private rock fallback before saving a Blueprint."""
    mesh_path = ROOT / "Content" / (ASTEROID.removeprefix("/Game/") + ".uasset")
    before = hashlib.sha256(mesh_path.read_bytes()).hexdigest()
    mesh = u.load_asset(ASTEROID)
    dynamic = u.DynamicMesh()
    lod = u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.RENDER_DATA, lod_index=0)
    _, outcome = u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic, u.GeometryScriptCopyMeshFromAssetOptions(apply_build_settings=False), lod)
    if outcome != u.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError("Could not read station asteroid fallback for final-trim clearance")
    spatial = u.GeometryScript_MeshSpatial
    _, bvh = spatial.build_bvh_for_mesh(dynamic)
    options = u.GeometryScriptSpatialQueryOptions(max_distance=500.)
    inverse = u.Quat(0, .30010876326423286, .16601761372063947, .9393470509596106)
    translation = u.Vector(7500, 0, 5300)
    samples = []
    for part in placements:
        if not part["name"].startswith(("ExteriorRoof", "ExteriorEntry")):
            continue
        center, size = part["center"], part["size"]
        # Each axis-aligned authored box contributes its eight corners and centre. This supplements
        # the existing room/terrace clearance receipt; it is not a claim of continuous mesh clearance.
        points = [[center[0] + sx * size[0] / 2, center[1] + sy * size[1] / 2,
                   center[2] + sz * size[2] / 2] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
        for coords in points + [center]:
            point = inverse.rotate_vector((u.Vector(*coords) - translation) / 145.)
            _, inside, _ = spatial.is_point_inside_mesh(dynamic, bvh, point, options)
            samples.append(dict(part=part["name"], hub_cm=coords, inside_rock=bool(inside)))
    inside = [s for s in samples if s["inside_rock"]]
    preserved = hashlib.sha256(mesh_path.read_bytes()).hexdigest() == before
    record = dict(asset=ASTEROID, asset_sha256=before, asset_preserved=preserved,
                  geometry="built_lod0_collision_fallback", triangles=dynamic.get_triangle_count(),
                  status="sampled-clearance-pass" if not inside and preserved else "failed",
                  samples=samples, inside_samples=inside,
                  limit="Added trim corners and centres only; runtime collision and rendered review remain separate.")
    (out / "final-trim-clearance.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    if inside or not preserved:
        raise RuntimeError("Final station trim failed the private asteroid clearance/preservation guard")
    return dict(samples=len(samples), inside=0, asset_preserved=True)


def main():
    import unreal as u

    def measure(asset):
        mesh = u.load_asset(asset)
        if not isinstance(mesh, (u.StaticMesh, u.SkeletalMesh)):
            raise RuntimeError("Required station mesh is unavailable: " + asset)
        skeletal = isinstance(mesh, u.SkeletalMesh)
        bounds = mesh.get_imported_bounds() if skeletal else mesh.get_bounds()
        materials = [slot.material_interface.get_path_name() if slot.material_interface else
                     "/Game/SpaceSurvival/Materials/M_Hull.M_Hull" for slot in
                     (mesh.get_editor_property("materials") if skeletal else mesh.static_materials)]
        return dict(origin=[bounds.origin.x, bounds.origin.y, bounds.origin.z],
                    extent=[bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z], materials=materials)

    recipe, placements, inventory = build_recipe(measure)
    out = ROOT / "Artifacts" / "StationReset"
    out.mkdir(parents=True, exist_ok=True)
    (out / "recipe.json").write_text(json.dumps(recipe, indent=2), encoding="utf-8")
    (out / "placements.json").write_text(json.dumps(placements, indent=2), encoding="utf-8")
    (out / "measured-assets.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    trim_clearance = verify_final_trim_clearance(u, placements, out)
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

    original = ROOT / "Content/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout.uasset"
    target = ROOT / "Content/SpaceSurvival/Licensed/StationReset/BP_StationReset.uasset"
    ownership = out / "ownership.json"
    original_before, target_before = sha(original), sha(target)
    apply = "-SSApplyStationReset" in u.SystemLibrary.get_command_line()
    dry_run = dict(mode="apply" if apply else "dry_run", package=PACKAGE,
                   original_sha256=original_before, previous_target_sha256=target_before,
                   meshes=len(recipe["static_meshes"]), solids=len(recipe["collision_boxes"]),
                   services=len(recipe["service_anchors"]), final_trim_clearance=trim_clearance)
    (out / "plan.json").write_text(json.dumps(dry_run, indent=2), encoding="utf-8")
    if not apply:
        u.log("STATION_RESET_DRY_RUN " + json.dumps(dry_run))
        return None
    if target_before:
        previous = json.loads(ownership.read_text(encoding="utf-8")) if ownership.exists() else {}
        if previous.get("output_sha256") != target_before:
            raise RuntimeError("BP_StationReset has no matching ownership receipt; preserving unknown owner edits")
        backup = out / "Backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup / target.name)
    blueprint = u.SSStationLayoutAuthoringLibrary.create_station_layout_at_path(json.dumps(recipe), PACKAGE, True)
    if not blueprint:
        raise RuntimeError("Station reset Blueprint failed to compile")
    # This apply path is for headless authoring with the newly rebuilt native API, not a live modal
    # editor paste. The author API returns only after successful compile and an initialized CDO.
    if not u.EditorAssetLibrary.save_loaded_asset(blueprint, only_if_is_dirty=False):
        raise RuntimeError("Station reset Blueprint did not save")
    if sha(original) != original_before:
        raise RuntimeError("Original station changed during authoring; receipt refused")
    output_sha = sha(target)
    if not output_sha:
        raise RuntimeError("Saved station reset package was not found at the expected project path")
    receipt = dict(dry_run, output_sha256=output_sha, original_after_sha256=sha(original),
                   authored_at=datetime.now(timezone.utc).isoformat(),
                   author_script_sha256=sha(Path(__file__)))
    ownership.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    u.log(f"STATION_RESET_AUTHORED package={PACKAGE} meshes={len(recipe['static_meshes'])} "
          f"solids={len(recipe['collision_boxes'])} services={len(recipe['service_anchors'])}; "
          f"saved_sha256={output_sha}; validate rendered runtime before acceptance")
    return blueprint


if __name__ == "__main__":
    main()
