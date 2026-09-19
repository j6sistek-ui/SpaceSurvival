"""Author a large station interior from the owner's installed kits.

  UnrealEditor-Cmd.exe <project> -unattended -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser -ExecutePythonScript="<abs>/Scripts/AuthorStationLarge.py"

Writes /Game/SpaceSurvival/Maps/StationLarge. Nothing existing is modified: the live station that
SSStation.cpp builds is untouched, so this can be looked at and thrown away.

Why it is composed rather than tiled. The measurement pass showed the two StarterBundle demo maps are
opposite things. SciFi_COMM_EX1 is 127 placements of 72 distinct meshes, nearly all at yaw 0, with
pivots baked to room-world positions - one room authored in place, which tiles into garbage. Its
ExampleMap sibling is 448 placements of 52 meshes with pieces repeated up to 40 times - that one does
tile. So the vendor rooms are placed whole, as wings, and only the links between them are tiled, from
SciFiCorridor, whose pivots sit on piece corners.

Footprint is about 60 x 78 m against the current station's 34 x 26 m.
"""
import json
import math
import os
import unreal

# Overridable, because an editor with the level open locks the .umap and the save silently fails.
# Writing to a second name sidesteps that without anyone having to close anything.
LEVEL = os.environ.get("SS_STATION_LEVEL", "/Game/SpaceSurvival/Maps/StationLarge")
DUMP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "Artifacts", "StationLarge", "kit_rooms.json")
FALLBACK_DUMP = (r"C:\Users\j6sis\AppData\Local\Temp\claude"
                 r"\C--Users-j6sis-SpaceSurvival\43aeb267-a48d-426d-8ee3-bf3c92861d49"
                 r"\scratchpad\kit_rooms.json")

# Each wing is placed by its own measured centre, so the numbers below are where the room lands, not
# an opaque offset. Local centres come from the dump's extents.
WINGS = [
    # key, local centre (cm), world centre (cm), yaw
    ("corridor", (-812.0, 486.0), (0.0, 0.0), 0.0),
    ("comm", (83.5, 0.0), (3400.0, 0.0), 0.0),
    ("props", (1075.0, -820.0), (0.0, 3200.0), 0.0),
    ("props", (1075.0, -820.0), (0.0, -3200.0), 180.0),
]

# Where a link corridor meets a wing there has to be a doorway, and nothing in these kits cuts one.
# So the wall pieces that would stand across the opening are simply not placed. Each box is in world
# centimetres and only suppresses wall-like meshes - floors and ceilings still run through, which is
# what an opening should look like.
APERTURES = [
    (2280.0, 2720.0, -320.0, 320.0),    # east link into the command centre
    (1440.0, 1820.0, -320.0, 320.0),    # east link out of the junction complex
    (-320.0, 320.0, 2330.0, 2760.0),    # north link into the props hall
    (-320.0, 320.0, 620.0, 980.0),      # north link out of the junction complex
    (-320.0, 320.0, -2760.0, -2330.0),  # south link into the props hall
    (-320.0, 320.0, -980.0, -620.0),    # south link out of the junction complex
]
BLOCKERS = ("wall", "pilar", "portal", "doorframe", "div")


def blocks_a_doorway(mesh_path, x, y):
    name = mesh_path.rsplit("/", 1)[-1].lower()
    if not any(k in name for k in BLOCKERS):
        return False
    if "floor" in name or "celling" in name or "ceiling" in name:
        return False
    for x0, x1, y0, y1 in APERTURES:
        if x0 <= x <= x1 and y0 <= y <= y1:
            return True
    return False


# SciFiCorridor pieces, measured: origin sits on the piece's min-X edge, floor at Z=0.
FLOOR = "/Game/SciFiCorridor/Meshes/SM_Floor_02"
WALL = "/Game/SciFiCorridor/Meshes/SM_Wall_03"
CEIL = "/Game/SciFiCorridor/Meshes/SM_Celling_01"
PILAR = "/Game/SciFiCorridor/Meshes/SM_Pilar"
FLOOR_PITCH_X, FLOOR_PITCH_Y = 535.0, 566.8
WALL_PITCH = 539.8
CEIL_PITCH = 300.0
CEIL_Z = 307.0

# Links: from, to, along which axis, at what cross-axis position.
LINKS = [
    ("X", 1618.0, 2454.0, 0.0),
    ("Y", 797.0, 2490.0, 0.0),
    ("Y", -797.0, -2490.0, 0.0),
]


def line(s=""):
    unreal.log_warning("BIG| " + str(s))


def section(t):
    line()
    line("=" * 74)
    line(t)
    line("=" * 74)


def load_dump():
    for path in (DUMP, FALLBACK_DUMP):
        if os.path.exists(path):
            line("  reading %s" % path)
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    line("  NO DUMP FOUND - run the dump pass first")
    return None


rooms = load_dump()
if rooms is None:
    raise SystemExit

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

section("NEW LEVEL")
# NOT LevelEditorSubsystem.new_level: it saves whatever map is currently open, and the editor opens
# the game's own Survival map by default. That silently wrote the station into
# Content/SpaceSurvival/Maps/Survival.umap twice, taking it from 30 KB to megabytes. new_blank_map
# takes an explicit "do not save the existing map" flag.
new_world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
line("  blank map created without touching the open one")

# The default template ships daylight: a sun, a sky atmosphere and clouds. This is an interior in
# orbit, and once doorways are opened that daylight floods straight through them and washes every
# room to flat white. Strip it and let the kits' own fixtures light the place.
# Match on class name, not isinstance: the template's actors are engine classes whose Python
# bindings do not all resolve, and an isinstance sweep silently missed the sun.
DAYLIGHT = ("DirectionalLight", "SkyAtmosphere", "VolumetricCloud", "ExponentialHeightFog",
            "SkyLight", "AtmosphericFog", "SunSky")
_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
removed = 0
for a in list(_sub.get_all_level_actors()):
    cls = a.get_class().get_name()
    if any(k in cls for k in DAYLIGHT):
        _sub.destroy_actor(a)
        removed += 1
line("  removed %d daylight actors from the template" % removed)

_cache = {}


def asset(path):
    if path not in _cache:
        _cache[path] = unreal.EditorAssetLibrary.load_asset(path)
    return _cache[path]


placed = {"mesh": 0, "light": 0, "link": 0, "missing": 0, "opened": 0}


def place_mesh(path, loc, rot=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0), tag=None):
    mesh = asset(path)
    if mesh is None:
        placed["missing"] += 1
        return None
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor,
                                      unreal.Vector(loc[0], loc[1], loc[2]),
                                      unreal.Rotator(rot[0], rot[1], rot[2]))
    if a is None:
        placed["missing"] += 1
        return None
    comp = a.static_mesh_component
    # Movable, not static. Nothing builds lighting here, and a static mesh with no lightmap renders
    # black - which is why the comm and props wings disappeared entirely while the corridor, whose
    # kit is full of emissive strips and screens, still showed up.
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_static_mesh(mesh)
    a.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
    if tag:
        a.tags = [unreal.Name(tag)]
    placed["mesh"] += 1
    return a


def rotate_xy(x, y, yaw_deg):
    r = math.radians(yaw_deg)
    c, s = math.cos(r), math.sin(r)
    return x * c - y * s, x * s + y * c


wing_lights = []   # one list of world XY per wing instance, used to derive camera anchors
wing_cams = []     # the vendor's own CineCameraActors, transformed into this level

section("WINGS")
for wing_index, (key, local_centre, world_centre, yaw) in enumerate(WINGS):
    room = rooms.get(key)
    if room is None:
        line("  %-9s MISSING from dump" % key)
        continue
    n0 = placed["mesh"]
    here = []
    for m in room["meshes"]:
        lx = m["loc"][0] - local_centre[0]
        ly = m["loc"][1] - local_centre[1]
        rx, ry = rotate_xy(lx, ly, yaw)
        wx, wy = world_centre[0] + rx, world_centre[1] + ry
        if blocks_a_doorway(m["mesh"], wx, wy):
            placed["opened"] += 1
            continue
        place_mesh(m["mesh"],
                   (wx, wy, m["loc"][2]),
                   (m["rot"][0], m["rot"][1], m["rot"][2] + yaw),
                   tuple(m["scale"]),
                   tag="StationLarge_" + key)
    for l in room["lights"]:
        lx = l["loc"][0] - local_centre[0]
        ly = l["loc"][1] - local_centre[1]
        rx, ry = rotate_xy(lx, ly, yaw)
        loc = unreal.Vector(world_centre[0] + rx, world_centre[1] + ry, l["loc"][2])
        rot = unreal.Rotator(l["rot"][0], l["rot"][1], l["rot"][2] + yaw)
        cls = unreal.SpotLight if "Spot" in l["class"] else (
            unreal.RectLight if "Rect" in l["class"] else unreal.PointLight)
        a = actors.spawn_actor_from_class(cls, loc, rot)
        if a is None:
            continue
        try:
            comp = a.light_component
            # Movable, not static: nothing runs Lightmass here, and a static light with no built
            # lighting contributes nothing at all - the level would render black.
            comp.set_mobility(unreal.ComponentMobility.MOVABLE)
            comp.set_intensity(l["intensity"])
            # The dump captured FColor (0-255 ints). LinearColor wants 0-1, so passing them raw
            # made every light 255x its colour - survivable at the corridor's 10-250 intensities,
            # ruinous at comm's 1500-5000.
            comp.set_light_color(unreal.LinearColor(l["color"][0] / 255.0,
                                                    l["color"][1] / 255.0,
                                                    l["color"][2] / 255.0, 1.0))
            if l.get("radius"):
                comp.set_attenuation_radius(l["radius"])
            # No shadows from imported room fixtures. In the vendor's map the lighting is baked and
            # the source sits inside its housing mesh; made movable and shadow-casting it is occluded
            # by its own fixture and lights nothing, which is why comm and props rendered pure black
            # while the corridor - whose spots hang clear of geometry - looked fine.
            try:
                comp.set_editor_property("cast_shadows", False)
            except Exception:
                pass
        except Exception:
            pass
        placed["light"] += 1
        here.append((loc.x, loc.y, loc.z))
    wing_lights.append({"key": key, "index": wing_index, "points": here,
                        "centre": list(world_centre)})
    for st in room.get("stands", []):
        if "Camera" not in st["class"]:
            continue
        sx = st["loc"][0] - local_centre[0]
        sy = st["loc"][1] - local_centre[1]
        cx, cy = rotate_xy(sx, sy, yaw)
        wing_cams.append({"key": key, "index": wing_index,
                          "loc": [world_centre[0] + cx, world_centre[1] + cy, st["loc"][2]],
                          "rot": [st["rot"][0], st["rot"][1], st["rot"][2] + yaw]})
    line("  %-9s at (%6.0f, %6.0f) yaw %3.0f  -> %d meshes"
         % (key, world_centre[0], world_centre[1], yaw, placed["mesh"] - n0))

section("LINK CORRIDORS")
for axis, a0, a1, cross in LINKS:
    lo, hi = (a0, a1) if a0 < a1 else (a1, a0)
    span = hi - lo
    n0 = placed["mesh"]
    if axis == "X":
        steps = max(1, int(round(span / FLOOR_PITCH_X)))
        for i in range(steps):
            x = lo + i * FLOOR_PITCH_X
            place_mesh(FLOOR, (x, cross + FLOOR_PITCH_Y * .5, 0.0), tag="StationLarge_link")
            place_mesh(WALL, (x, cross - 280.0, 0.0), (0, 0, 0), tag="StationLarge_link")
            place_mesh(WALL, (x + WALL_PITCH, cross + 280.0, 0.0), (0, 0, 180), tag="StationLarge_link")
        for i in range(max(1, int(round(span / CEIL_PITCH)))):
            place_mesh(CEIL, (lo + CEIL_PITCH * (i + .5), cross, CEIL_Z), tag="StationLarge_link")
        for i in range(steps + 1):
            x = lo + i * FLOOR_PITCH_X
            place_mesh(PILAR, (x, cross - 300.0, 0.0), tag="StationLarge_link")
            place_mesh(PILAR, (x, cross + 300.0, 0.0), (0, 0, 180), tag="StationLarge_link")
    else:
        steps = max(1, int(round(span / FLOOR_PITCH_X)))
        for i in range(steps):
            y = lo + i * FLOOR_PITCH_X
            place_mesh(FLOOR, (cross - FLOOR_PITCH_Y * .5, y, 0.0), (0, 0, 90), tag="StationLarge_link")
            place_mesh(WALL, (cross + 280.0, y, 0.0), (0, 0, 90), tag="StationLarge_link")
            place_mesh(WALL, (cross - 280.0, y + WALL_PITCH, 0.0), (0, 0, 270), tag="StationLarge_link")
        for i in range(max(1, int(round(span / CEIL_PITCH)))):
            place_mesh(CEIL, (cross, lo + CEIL_PITCH * (i + .5), CEIL_Z), (0, 0, 90), tag="StationLarge_link")
        for i in range(steps + 1):
            y = lo + i * FLOOR_PITCH_X
            place_mesh(PILAR, (cross + 300.0, y, 0.0), (0, 0, 90), tag="StationLarge_link")
            place_mesh(PILAR, (cross - 300.0, y, 0.0), (0, 0, 270), tag="StationLarge_link")
    placed["link"] += placed["mesh"] - n0
    line("  %s link %7.0f..%-7.0f at %5.0f -> %d pieces" % (axis, lo, hi, cross, placed["mesh"] - n0))

section("CONTINUOUS DECK AND HULL")
# The wings were three separate vendor rooms bridged by narrow spurs, which reads as disconnected
# boxes floating apart - no ground between them and no outer skin. A single deck under the whole
# footprint and a perimeter wall turn them into one structure.
DECK_X0, DECK_X1 = -2200.0, 4500.0
DECK_Y0, DECK_Y1 = -4200.0, 4200.0
DECK_Z = -8.0          # just under the rooms' own floors, so nothing z-fights
HULL_Z = 0.0

deck = 0
y = DECK_Y0
while y < DECK_Y1:
    x = DECK_X0
    while x < DECK_X1:
        if place_mesh(FLOOR, (x, y + FLOOR_PITCH_Y, DECK_Z), tag="StationLarge_deck"):
            deck += 1
        x += FLOOR_PITCH_X
    y += FLOOR_PITCH_Y
line("  deck %d tiles over %.0f x %.0f m" % (deck, (DECK_X1-DECK_X0)/100.0, (DECK_Y1-DECK_Y0)/100.0))

hull = 0
x = DECK_X0
while x < DECK_X1:
    if place_mesh(WALL, (x, DECK_Y0, HULL_Z), (0, 0, 0), tag="StationLarge_hull"): hull += 1
    if place_mesh(WALL, (x + WALL_PITCH, DECK_Y1, HULL_Z), (0, 0, 180), tag="StationLarge_hull"): hull += 1
    x += WALL_PITCH
y = DECK_Y0
while y < DECK_Y1:
    if place_mesh(WALL, (DECK_X0, y + WALL_PITCH, HULL_Z), (0, 0, 270), tag="StationLarge_hull"): hull += 1
    if place_mesh(WALL, (DECK_X1, y, HULL_Z), (0, 0, 90), tag="StationLarge_hull"): hull += 1
    y += WALL_PITCH
line("  hull %d perimeter wall sections" % hull)

# Columns on the open deck so the space between wings is not a bare plain.
col = 0
for gx in range(int(DECK_X0) + 600, int(DECK_X1) - 400, 1100):
    for gy in range(int(DECK_Y0) + 700, int(DECK_Y1) - 500, 1300):
        if abs(gx) < 1750 and abs(gy) < 900:
            continue          # leave the junction complex clear
        if 2300 < gx < 4400 and abs(gy) < 1500:
            continue          # and the command centre
        if place_mesh(PILAR, (float(gx), float(gy), HULL_Z), tag="StationLarge_deck"):
            col += 1
line("  %d deck columns between the wings" % col)

section("BACKDROP AND ACCENTS")
# A station in orbit needs something behind it, and with the template daylight gone the background
# renders white. The project already owns a deep-space sky; put it on a big inverted sphere rather
# than reintroducing a sun that floods every doorway.
# No sky dome. A 250 m inverted sphere with an unlit material encloses the whole station, and every
# exterior shot came back black because the camera was inside it looking at its interior surface.
# The SkyAtmosphere provides the backdrop instead, which is also what actually lights the hull.

# The ModularSci_Comm kit is a white/grey set lit by white panels, so a faithful copy of its own
# lighting reads monochrome. These accents are the art direction the marketing shots have and the
# demo map does not: a warm floor wash and a cool rim, placed per wing.
ACCENTS = [
    # x, y, z, r, g, b, intensity, radius
    (3400.0, 0.0, 120.0, 1.00, 0.52, 0.18, 22000.0, 1900.0),
    (3400.0, 0.0, 520.0, 0.24, 0.58, 1.00, 16000.0, 2100.0),
    (2600.0, -900.0, 240.0, 1.00, 0.42, 0.14, 12000.0, 1500.0),
    (2600.0, 900.0, 240.0, 0.20, 0.62, 1.00, 12000.0, 1500.0),
    (0.0, 3200.0, 150.0, 1.00, 0.55, 0.20, 18000.0, 2200.0),
    (0.0, 3900.0, 300.0, 0.22, 0.60, 1.00, 12000.0, 1800.0),
    (0.0, -3200.0, 150.0, 1.00, 0.55, 0.20, 18000.0, 2200.0),
    (0.0, -3900.0, 300.0, 0.22, 0.60, 1.00, 12000.0, 1800.0),
    (0.0, 0.0, 180.0, 1.00, 0.48, 0.16, 16000.0, 1800.0),
    (-900.0, 0.0, 300.0, 0.26, 0.64, 1.00, 12000.0, 1700.0),
    (0.0, 1600.0, 180.0, 1.00, 0.50, 0.18, 9000.0, 1200.0),
    (0.0, -1600.0, 180.0, 0.24, 0.60, 1.00, 9000.0, 1200.0),
    (2050.0, 0.0, 180.0, 1.00, 0.50, 0.18, 9000.0, 1200.0),
]
for x, y, z, r, g, b, intensity, radius in ACCENTS:
    a = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, z),
                                      unreal.Rotator(0, 0, 0))
    if a is None:
        continue
    comp = a.light_component
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_intensity(intensity)
    comp.set_light_color(unreal.LinearColor(r, g, b, 1.0))
    comp.set_attenuation_radius(radius)
    try:
        comp.set_editor_property("cast_shadows", False)
    except Exception:
        pass
    placed["light"] += 1
line("  %d accent lights (warm floor wash, cool rim)" % len(ACCENTS))

# A blank map has no SkyAtmosphere, and that turns out to be what was lighting the station at all:
# with only local fixtures the StarterBundle wings render black from every angle, inside and out,
# while the SciFiCorridor wing survives on its emissive strips. Put an atmosphere back, with a sun
# dim enough not to flood the interiors.
atmos = actors.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0),
                                      unreal.Rotator(0, 0, 0))
if atmos:
    line("  sky atmosphere restored")

# Directional intensity is LUX. 3.2 lux is moonlight, which is why the hull rendered black from
# outside; a key and an opposing fill at sane levels give it form without touching the interiors.
for tag, rot, lux, colour in (
        ("StationLarge_key",  unreal.Rotator(0, -38.0, 25.0),  18.0, (0.66, 0.76, 1.00)),
        ("StationLarge_fill", unreal.Rotator(0, -22.0, 205.0),  6.0, (1.00, 0.74, 0.48))):
    d = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 4000), rot)
    if not d:
        continue
    dc = d.light_component
    dc.set_mobility(unreal.ComponentMobility.MOVABLE)
    dc.set_intensity(lux)
    dc.set_light_color(unreal.LinearColor(colour[0], colour[1], colour[2], 1.0))
    d.tags = [unreal.Name(tag)]
    placed["light"] += 1
line("  exterior key 18 lux + opposing fill 6 lux")

section("AMBIENT")
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 900))
if sky:
    try:
        sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        sky.light_component.set_intensity(.22)
        sky.light_component.set_light_color(unreal.LinearColor(.18, .26, .44, 1.0))
    except Exception:
        pass
    line("  skylight for fill only - the rooms carry their own lighting")

section("INTERIOR ANCHORS")
# Cameras derived from geometry kept landing outside rooms or inside pillars. A light, by contrast,
# always hangs in open space, so a light's XY at eye height is reliably standable. Stand at the light
# furthest from the wing's own lighting centroid and look back across the room.
import json as _json
import math as _math

anchors = []
for wing in wing_lights:
    pts = wing["points"]
    if len(pts) < 2:
        continue
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    # Put the camera ON a light. A fixture hangs in open air by definition, which neither a mesh
    # centroid nor a room centre guarantees - both put cameras inside a dais or a wall and rendered
    # solid black. Stand at the light nearest the middle and look at the one furthest out.
    near = min(pts, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
    far = max(pts, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
    ex, ey = near[0], near[1]
    ez = min(max(near[2] - 40.0, 150.0), 420.0)
    yaw = _math.degrees(_math.atan2(far[1] - ey, far[0] - ex))
    name = "%02d_%s" % (wing["index"], wing["key"])
    anchors.append({"name": name, "loc": [round(ex, 1), round(ey, 1), round(ez, 1)],
                    "rot": [-3.0, round(yaw, 1), 0.0], "bias": 3.5,
                    "note": "stands at the outermost light of the %s wing, looking across it" % wing["key"]})
    line("  %-16s stand (%8.1f %8.1f %6.1f) yaw %6.1f  from %d lights"
         % (name, ex, ey, ez, yaw, len(pts)))

for i, c in enumerate(wing_cams[:4]):
    anchors.append({"name": "cam%d_%s" % (i, c["key"]),
                    "loc": [round(v, 1) for v in c["loc"]],
                    # the dump stores euler as [roll, pitch, yaw]; anchors carry [pitch, yaw, roll]
                    "rot": [round(c["rot"][1], 1), round(c["rot"][2], 1), round(c["rot"][0], 1)],
                    "bias": 3.5, "note": "vendor showcase camera from the %s demo map" % c["key"]})
line("  %d vendor showcase cameras carried over" % min(4, len(wing_cams)))

_anchor_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "Artifacts", "StationLarge", "anchors.json")
os.makedirs(os.path.dirname(_anchor_path), exist_ok=True)
with open(_anchor_path, "w", encoding="utf-8") as f:
    _json.dump(anchors, f, indent=1)
line("  wrote %d anchors to %s" % (len(anchors), _anchor_path))

section("SAVE")
# Check the result. save_map returns False when the package is locked - which happens whenever the
# level is open in another editor - and without this the script cheerfully reported "saved" while
# two builds in a row never reached disk.
saved = unreal.EditorLoadingAndSavingUtils.save_map(new_world, LEVEL)
if not saved:
    line("  *** SAVE FAILED - %s was not written." % LEVEL)
    line("  *** The usual cause is the level being open in another Unreal editor, which locks the")
    line("  *** .umap. Close it there and run this again.")
line("  meshes  %d" % placed["mesh"])
line("  lights  %d" % placed["light"])
line("  link    %d" % placed["link"])
line("  missing %d" % placed["missing"])
line("  doorways opened (wall pieces omitted) %d" % placed["opened"])
line("  saved   %s" % LEVEL if saved else "  NOT SAVED - see above")
line()
line("BIG| DONE")
