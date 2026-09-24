"""Turn the StationLarge composition into a CreateStationVisualLayout recipe.

The big station already exists as a .umap built by Scripts/AuthorStationLarge.py. The GAME, though,
does not load a map - ASSStation spawns BP_StationVisualLayout, which
USSStationLayoutAuthoringLibrary::CreateStationVisualLayout(RecipeJson, bReset) rebuilds from JSON.
So wiring the big station in is a recipe swap, not a code change.

This reproduces the authoring script's composition offline - same WINGS, same APERTURES, same LINKS -
and emits that recipe. No editor needed, which matters because a running PIE session blocks every
level operation.

Rotation conventions, which differ at every hop and are the easy thing to get wrong:
  kit_rooms.json stores euler as [roll, pitch, yaw]
  unreal.Rotator(a, b, c)      is (roll, pitch, yaw)   <- what AuthorStationLarge.py feeds
  recipe "rotation": [x, y, z] becomes FRotator(x, y, z) = (Pitch, Yaw, Roll)
so the recipe needs [pitch, yaw, roll] = [dump[1], dump[2] + wing_yaw, dump[0]].
"""
import json
import math
from pathlib import Path

ROOT = Path(r"C:\Users\j6sis\SpaceSurvival")
DUMP = ROOT / "Artifacts" / "StationLarge" / "kit_rooms.json"
OUT = Path(__file__).resolve().parents[1] / "Artifacts" / "StationRecipe" / "station_recipe.json"

# --- copied verbatim from Scripts/AuthorStationLarge.py so the two cannot drift silently ---
WINGS = [
    ("corridor", (-812.0, 486.0), (0.0, 0.0), 0.0),
    ("comm", (83.5, 0.0), (3400.0, 0.0), 0.0),
    ("props", (1075.0, -820.0), (0.0, 3200.0), 0.0),
    ("props", (1075.0, -820.0), (0.0, -3200.0), 180.0),
]
APERTURES = [
    (2280.0, 2720.0, -320.0, 320.0),
    (1440.0, 1820.0, -320.0, 320.0),
    (-320.0, 320.0, 2330.0, 2760.0),
    (-320.0, 320.0, 620.0, 980.0),
    (-320.0, 320.0, -2760.0, -2330.0),
    (-320.0, 320.0, -980.0, -620.0),
]
BLOCKERS = ("wall", "pilar", "portal", "doorframe", "div")
FLOOR = "/Game/SciFiCorridor/Meshes/SM_Floor_02"
WALL = "/Game/SciFiCorridor/Meshes/SM_Wall_03"
CEIL = "/Game/SciFiCorridor/Meshes/SM_Celling_01"
PILAR = "/Game/SciFiCorridor/Meshes/SM_Pilar"
FLOOR_PITCH_X, FLOOR_PITCH_Y = 535.0, 566.8
WALL_PITCH = 539.8
CEIL_PITCH = 300.0
CEIL_Z = 307.0
LINKS = [
    ("X", 1618.0, 2454.0, 0.0),
    ("Y", 797.0, 2490.0, 0.0),
    ("Y", -797.0, -2490.0, 0.0),
]


def blocks_a_doorway(mesh_path, x, y):
    name = mesh_path.rsplit("/", 1)[-1].lower()
    if not any(k in name for k in BLOCKERS):
        return False
    if "floor" in name or "celling" in name or "ceiling" in name:
        return False
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, x1, y0, y1 in APERTURES)


def rotate_xy(x, y, yaw_deg):
    r = math.radians(yaw_deg)
    c, s = math.cos(r), math.sin(r)
    return x * c - y * s, x * s + y * c


rooms = json.loads(DUMP.read_text(encoding="utf-8"))
meshes, lights = [], []
skipped = {"opened": 0, "spot": 0, "rect": 0}
used = set()


def name_for(stem):
    """CreateStationVisualLayout rejects duplicate component names outright, so uniquify here."""
    stem = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in stem)[:48]
    n, i = stem, 1
    while n in used:
        i += 1
        n = f"{stem}_{i}"
    used.add(n)
    return n


# CreateStationVisualLayout pre-fills each component's materials from the mesh's own slots and then
# REFUSES any mesh with an unassigned slot. SciFiCorridor's SM_Top_Wall02 ships with slot 0 empty, so
# nine pieces would abort the whole build. Give them the same kit's wall material.
SLOT_FIXES = {
    "/Game/SciFiCorridor/Meshes/SM_Top_Wall02":
        ["/Game/SciFiCorridor/Materials/MI_CorridorWall_03.MI_CorridorWall_03"],
}


FLOOR_MAT = "/Game/SciFiCorridor/Materials/MI_CorridorFloor_02.MI_CorridorFloor_02"


def add_mesh(asset, loc, rot_pyr, scale, stem, mats=None):
    entry = {"name": name_for(stem),
             "asset": asset,
             "location": [round(v, 2) for v in loc],
             "rotation": [round(v, 3) for v in rot_pyr],
             "scale": [round(v, 4) for v in scale],
             "cast_shadows": False}
    if mats:
        entry["materials"] = list(mats)
    elif asset in SLOT_FIXES:
        entry["materials"] = SLOT_FIXES[asset]
    meshes.append(entry)


# ------------------------------------------------------------------ wings
for wing_index, (key, local_centre, world_centre, yaw) in enumerate(WINGS):
    room = rooms.get(key)
    if room is None:
        continue
    for m in room["meshes"]:
        lx = m["loc"][0] - local_centre[0]
        ly = m["loc"][1] - local_centre[1]
        rx, ry = rotate_xy(lx, ly, yaw)
        wx, wy = world_centre[0] + rx, world_centre[1] + ry
        if blocks_a_doorway(m["mesh"], wx, wy):
            skipped["opened"] += 1
            continue
        roll, pitch, y_aw = m["rot"][0], m["rot"][1], m["rot"][2]
        add_mesh(m["mesh"], (wx, wy, m["loc"][2]),
                 (pitch, y_aw + yaw, roll), tuple(m["scale"]),
                 f"{key}{wing_index}_{m['mesh'].rsplit('/', 1)[-1]}")
    for li, l in enumerate(room["lights"]):
        cls = l["class"]
        if "Spot" in cls:
            skipped["spot"] += 1
            continue
        if "Rect" in cls:
            skipped["rect"] += 1
            continue
        lx = l["loc"][0] - local_centre[0]
        ly = l["loc"][1] - local_centre[1]
        rx, ry = rotate_xy(lx, ly, yaw)
        roll, pitch, y_aw = l["rot"][0], l["rot"][1], l["rot"][2]
        lights.append({"name": name_for(f"{key}{wing_index}_light{li}"),
                       "location": [round(world_centre[0] + rx, 2),
                                    round(world_centre[1] + ry, 2),
                                    round(l["loc"][2], 2)],
                       "rotation": [round(pitch, 3), round(y_aw + yaw, 3), round(roll, 3)],
                       "scale": [1.0, 1.0, 1.0],
                       # the dump captured FColor 0-255; LinearColor wants 0-1. Passing these raw
                       # once made every light 255x its colour.
                       "color": [round(l["color"][0] / 255.0, 4),
                                 round(l["color"][1] / 255.0, 4),
                                 round(l["color"][2] / 255.0, 4)],
                       "intensity": l["intensity"],
                       "attenuation_radius": l.get("radius") or 1000.0,
                       "cast_shadows": False})

# ------------------------------------------------------- link corridors
for axis, a0, a1, cross in LINKS:
    lo, hi = (a0, a1) if a0 < a1 else (a1, a0)
    span = hi - lo
    steps = max(1, int(round(span / FLOOR_PITCH_X)))
    tag = f"link{axis}{int(lo)}"
    if axis == "X":
        for i in range(steps):
            x = lo + i * FLOOR_PITCH_X
            add_mesh(FLOOR, (x, cross + FLOOR_PITCH_Y * .5, 0.0), (0, 0, 0), (1, 1, 1), f"{tag}_floor{i}")
            add_mesh(WALL, (x, cross - 280.0, 0.0), (0, 0, 0), (1, 1, 1), f"{tag}_wallA{i}")
            add_mesh(WALL, (x + WALL_PITCH, cross + 280.0, 0.0), (0, 180, 0), (1, 1, 1), f"{tag}_wallB{i}")
        for i in range(max(1, int(round(span / CEIL_PITCH)))):
            add_mesh(CEIL, (lo + CEIL_PITCH * (i + .5), cross, CEIL_Z), (0, 0, 0), (1, 1, 1), f"{tag}_ceil{i}")
        for i in range(steps + 1):
            x = lo + i * FLOOR_PITCH_X
            add_mesh(PILAR, (x, cross - 300.0, 0.0), (0, 0, 0), (1, 1, 1), f"{tag}_pilA{i}")
            add_mesh(PILAR, (x, cross + 300.0, 0.0), (0, 180, 0), (1, 1, 1), f"{tag}_pilB{i}")
    else:
        for i in range(steps):
            y = lo + i * FLOOR_PITCH_X
            add_mesh(FLOOR, (cross - FLOOR_PITCH_Y * .5, y, 0.0), (0, 90, 0), (1, 1, 1), f"{tag}_floor{i}")
            add_mesh(WALL, (cross + 280.0, y, 0.0), (0, 90, 0), (1, 1, 1), f"{tag}_wallA{i}")
            add_mesh(WALL, (cross - 280.0, y + WALL_PITCH, 0.0), (0, 270, 0), (1, 1, 1), f"{tag}_wallB{i}")
        for i in range(max(1, int(round(span / CEIL_PITCH)))):
            add_mesh(CEIL, (cross, lo + CEIL_PITCH * (i + .5), CEIL_Z), (0, 90, 0), (1, 1, 1), f"{tag}_ceil{i}")
        for i in range(steps + 1):
            y = lo + i * FLOOR_PITCH_X
            add_mesh(PILAR, (cross + 300.0, y, 0.0), (0, 90, 0), (1, 1, 1), f"{tag}_pilA{i}")
            add_mesh(PILAR, (cross - 300.0, y, 0.0), (0, 270, 0), (1, 1, 1), f"{tag}_pilB{i}")

# ------------------------------------------- continuous deck, hull, columns
# Without these the wings read as disconnected boxes floating apart, with no ground between them.
DECK_X0, DECK_X1 = -2200.0, 4500.0
DECK_Y0, DECK_Y1 = -4200.0, 4200.0
DECK_Z, HULL_Z = -8.0, 0.0      # deck sits just under the rooms' own floors so nothing z-fights

deck = 0
y = DECK_Y0
while y < DECK_Y1:
    x = DECK_X0
    while x < DECK_X1:
        add_mesh(FLOOR, (x, y + FLOOR_PITCH_Y, DECK_Z), (0, 0, 0), (1, 1, 1), f"deck_{deck}",
                 mats=[FLOOR_MAT, FLOOR_MAT])
        deck += 1
        x += FLOOR_PITCH_X
    y += FLOOR_PITCH_Y

hull = 0
x = DECK_X0
while x < DECK_X1:
    add_mesh(WALL, (x, DECK_Y0, HULL_Z), (0, 0, 0), (1, 1, 1), f"hull_{hull}"); hull += 1
    add_mesh(WALL, (x + WALL_PITCH, DECK_Y1, HULL_Z), (0, 180, 0), (1, 1, 1), f"hull_{hull}"); hull += 1
    x += WALL_PITCH
y = DECK_Y0
while y < DECK_Y1:
    if abs(y + WALL_PITCH) >= 700:          # leave the pad doorway open (walkway spans y -300..300)
        add_mesh(WALL, (DECK_X0, y + WALL_PITCH, HULL_Z), (0, 270, 0), (1, 1, 1), f"hull_{hull}"); hull += 1
    add_mesh(WALL, (DECK_X1, y, HULL_Z), (0, 90, 0), (1, 1, 1), f"hull_{hull}"); hull += 1
    y += WALL_PITCH

col = 0
for gx in range(int(DECK_X0) + 600, int(DECK_X1) - 400, 1100):
    for gy in range(int(DECK_Y0) + 700, int(DECK_Y1) - 500, 1300):
        if abs(gx) < 1750 and abs(gy) < 900:
            continue                                  # leave the junction complex clear
        if 2300 < gx < 4400 and abs(gy) < 1500:
            continue                                  # and the command centre
        add_mesh(PILAR, (float(gx), float(gy), HULL_Z), (0, 0, 0), (1, 1, 1), f"deckcol_{col}")
        col += 1

# ------------------------------------------------------------ landing pad
# ASSLandingPad draws only a grey engine-cube deck (HalfExtent 1600 -> 32x32 m) with two cyan
# strips and a cylinder marker, at world (-4500, 0), top surface z = -10. Everything here is
# DRESSING placed around that functional pad; the pad actor is untouched so docking still works.
PAD_CX, PAD_TOP, PAD_HALF = -4500.0, -10.0, 1600.0
PAD_X0, PAD_X1 = PAD_CX - PAD_HALF, PAD_CX + PAD_HALF      # -6100 .. -2900
PAD_Y0, PAD_Y1 = -PAD_HALF, PAD_HALF                       # -1600 .. 1600

BOLLARD = ("/Game/Sci_Fi_Light/Static_Meshes/SM_Sci_Fi_Bollard_Light"
           "/Mesh/SM_Sci_Fi_Bollard_Light")          # 8x8x41 cm, emissive
SPOT = "/Game/NERVES/SM/SM_Spotlight_01"                       # 17x17x1.1 disc, centred pivot
LAMP = "/Game/Megastructure_Scifi_World/Meshes/Lamp/SM_lamp_big"   # 60x60x15.6 dome, base at z0
CRATE = "/Game/SciFiCorridor/Meshes/SM_Crate"                  # 150x146x120, pivot at its CENTRE
DOORFRAME = "/Game/SciFiCorridor/Meshes/SM_DoorFrame"          # 181 wide, 284 tall, pivot on y=0

def padlight(name, x, y, z, rgb, intensity, radius):
    lights.append({"name": name_for(name), "location": [x, y, z], "rotation": [0.0, 0.0, 0.0],
                   "scale": [1.0, 1.0, 1.0], "color": list(rgb), "intensity": intensity,
                   "attenuation_radius": radius, "cast_shadows": False})

# Runway edge lighting: two rows of inset discs down the long axis. The disc is 17 cm, so
# scale 7 makes a ~1.2 m deck light.
n = 0
for side in (-1.0, 1.0):
    x = PAD_X0 + 260.0
    while x <= PAD_X1 - 260.0:
        add_mesh(SPOT, (x, side * 1340.0, PAD_TOP), (0, 0, 0), (7, 7, 7), f"pad_edgelight_{n}")
        n += 1
        x += 320.0
# every third one gets an actual light so the count stays sane
for i in range(0, 9):
    x = PAD_X0 + 260.0 + i * 320.0 * 1.15
    if x > PAD_X1 - 260.0:
        break
    padlight(f"pad_edge_L{i}", x, -1340.0, 60.0, (0.30, 0.72, 1.00), 5200.0, 900.0)
    padlight(f"pad_edge_R{i}", x, 1340.0, 60.0, (0.30, 0.72, 1.00), 5200.0, 900.0)

# Threshold chevron pointing at the station door, so the approach reads directionally.
for i in range(5):
    off = (i - 2) * 300.0
    add_mesh(SPOT, (PAD_X1 - 420.0 - abs(off) * 0.55, off, PAD_TOP), (0, 0, 0), (6, 6, 6),
             f"pad_chevron_{i}")
padlight("pad_threshold", PAD_X1 - 500.0, 0.0, 70.0, (1.00, 0.86, 0.45), 14000.0, 1500.0)

# Touchdown marker ring at the dock point.
for i in range(12):
    import math as _m
    a = _m.radians(i * 30.0)
    add_mesh(SPOT, (PAD_CX + _m.cos(a) * 760.0, _m.sin(a) * 760.0, PAD_TOP), (0, 0, 0), (5, 5, 5),
             f"pad_ring_{i}")
# 22000 visibly blew out the whole centre of the pad in PIE. Measured by eye, corrected.
padlight("pad_touchdown", PAD_CX, 0.0, 120.0, (0.55, 0.95, 1.00), 6000.0, 1500.0)

# Corner beacon masts - 3 m columns with a dome on top. Port red / starboard green, which is
# the convention a pilot reads without being told.
CORNERS = [(PAD_X0 + 190.0, PAD_Y0 + 190.0, (1.00, 0.16, 0.12)),
           (PAD_X0 + 190.0, PAD_Y1 - 190.0, (0.16, 1.00, 0.30)),
           (PAD_X1 - 190.0, PAD_Y0 + 190.0, (1.00, 0.16, 0.12)),
           (PAD_X1 - 190.0, PAD_Y1 - 190.0, (0.16, 1.00, 0.30))]
for i, (cx, cy, rgb) in enumerate(CORNERS):
    add_mesh(PILAR, (cx, cy, PAD_TOP), (0, i * 90.0, 0), (1, 1, 1), f"pad_mast_{i}")
    add_mesh(LAMP, (cx, cy, PAD_TOP + 300.0), (0, 0, 0), (1.6, 1.6, 1.6), f"pad_beacon_{i}")
    padlight(f"pad_beacon_light_{i}", cx, cy, PAD_TOP + 340.0, rgb, 9000.0, 1400.0)

# Pad edge markers. These were 3 m SM_Pilar columns every 4.2 m, which from outside read as a
# palisade of dark blocks fencing in the landing pad - visible and wrong on the approach. A pad
# edge wants low emissive markers, not a colonnade, so they are bollard lights at ~1 m, spaced
# wider, and the corner masts carry the height instead.
BOLLARD_PAD = 2.5
p = 0
for sx in (PAD_X0 + 40.0, PAD_X1 - 40.0):
    yy = PAD_Y0 + 420.0
    while yy <= PAD_Y1 - 420.0:
        if not (sx > PAD_CX and abs(yy) < 460.0):        # keep the walkway mouth clear
            add_mesh(BOLLARD, (sx, yy, PAD_TOP), (0, 90.0 if sx < PAD_CX else 270.0, 0),
                     (BOLLARD_PAD,) * 3, f"pad_post_{p}")
            p += 1
        yy += 640.0
for sy in (PAD_Y0 + 40.0, PAD_Y1 - 40.0):
    xx = PAD_X0 + 420.0
    while xx <= PAD_X1 - 420.0:
        add_mesh(BOLLARD, (xx, sy, PAD_TOP), (0, 0.0 if sy < 0 else 180.0, 0),
                 (BOLLARD_PAD,) * 3, f"pad_post_{p}")
        p += 1
        xx += 640.0

# Ground crew clutter, kept off the touchdown circle. Crate pivot is centred, so +60 to stand it
# on the deck rather than half-sunk.
CRATES = [(-5850, -1180), (-5850, -980), (-5700, -1180), (-5880, 1120), (-5680, 1180),
          (-3250, -1250), (-3250, 1250), (-3420, 1180)]
for i, (cx, cy) in enumerate(CRATES):
    add_mesh(CRATE, (float(cx), float(cy), PAD_TOP + 60.0), (0, (i % 4) * 90.0, 0), (1, 1, 1),
             f"pad_crate_{i}")
padlight("pad_service_W", -5750.0, 0.0, 200.0, (1.00, 0.78, 0.42), 7000.0, 1800.0)

# Covered walkway from the pad edge to the station hull: 7 m, same construction as the existing
# link corridors so it reads as part of the same station.
WALK_X0, WALK_X1 = PAD_X1, DECK_X0                  # -2900 .. -2200, a 700 cm span
WALK_SPAN = WALK_X1 - WALK_X0
# SM_Wall_03 is 540 long and SM_Celling_01 is 300. Tiling either one past the span pushed a 5.4 m
# wall 3.75 m INTO the station - a free-standing wall in the middle of the hallway. Fit the span
# instead of tiling into it: one stretched panel per side, ceiling tiles sized to divide evenly.
w = 0
x = WALK_X0
while x < WALK_X1 - 1.0:
    add_mesh(FLOOR, (x, FLOOR_PITCH_Y * .5, 0.0), (0, 0, 0), (1, 1, 1), f"walk_floor_{w}")
    w += 1
    x += FLOOR_PITCH_X
WALL_FIT = WALK_SPAN / 540.0                       # stretch one panel to cover exactly
add_mesh(WALL, (WALK_X0, -280.0, 0.0), (0, 0, 0), (WALL_FIT, 1, 1), "walk_wallA")
add_mesh(WALL, (WALK_X1, 280.0, 0.0), (0, 180, 0), (WALL_FIT, 1, 1), "walk_wallB")
CEIL_N = max(1, int(WALK_SPAN // 300))
CEIL_FIT = WALK_SPAN / (CEIL_N * 300.0)
for i in range(CEIL_N):
    add_mesh(CEIL, (WALK_X0 + WALK_SPAN * (i + .5) / CEIL_N, 0.0, CEIL_Z), (0, 0, 0),
             (CEIL_FIT, 1, 1), f"walk_ceil_{i}")
    padlight(f"walk_light_{i}", WALK_X0 + WALK_SPAN * (i + .5) / CEIL_N, 0.0, CEIL_Z - 40.0,
             (0.86, 0.94, 1.00), 4200.0, 700.0)
for i, px in enumerate((WALK_X0, WALK_X1)):
    add_mesh(PILAR, (px, -300.0, 0.0), (0, 0, 0), (1, 1, 1), f"walk_pilA_{i}")
    add_mesh(PILAR, (px, 300.0, 0.0), (0, 180, 0), (1, 1, 1), f"walk_pilB_{i}")

add_mesh(DOORFRAME, (DECK_X0, 90.0, 0.0), (0, 0, 0), (1, 1, 1), "walk_door_station")
add_mesh(DOORFRAME, (PAD_X1, 90.0, 0.0), (0, 0, 0), (1, 1, 1), "walk_door_pad")
padlight("walk_door_glow", DECK_X0 - 60.0, 0.0, 190.0, (0.45, 0.85, 1.00), 5000.0, 800.0)

# ---------------------------------------------------------- pickup review row
# The 13 Tripo power-ups, floated at chest height INSIDE the walkable box
# (|X| <= 1750, |Y| <= 1450 per ASSStation::Walkable) so they can actually be walked up to.
# Pivots sit on the mesh base, so a Z of 110 floats them rather than half-sinking them.
PICKUPS = [
    "electric_bolt_3d_model_Clone1", "futuristic_energy_sphere_3d_model",
    "medical_cross_3d_model_Clone1", "futuristic_energy_core_3d_model",
    "metallic_info_gear_3d_model", "sci-fi_emblem_3d_model",
    "steampunk_shield_3d_model", "green_sci-fi_emblem_3d_model_Clone1",
    "steampunk_capsule_3d_model_Clone1_Clone1", "golden_gear_emblem_3d_model_Clone1",
    "futuristic_weapon_3d_model", "blue_gear_emblem_3d_model",
    "green_sci-fi_emblem_3d_model",
]
# The flat review row is gone - the trophy run below shows the same thirteen properly,
# on lit plinths where the player walks, which is both the review and the design.

# ------------------------------------------------------- service kiosks + polish
# Measured min.z for every prop used below, so things REST on the deck instead of floating or
# half-sinking. Offset = -min.z. Checked with get_bounds, not guessed - several were wrong.
KIOSK   = "/Game/Fab/Sci_fi_Console_Game/SM_Sci_fi_Console_Game"            # min.z  +0.07
LOADER  = "/Game/Fab/Industrial_Loader_Robot/SM_Industrial_Loader_Robot"    # min.z  -8.89
TERMINAL= "/Game/StarterBundle/ModularSci_Comm/Meshes/SM_Terminal_A"        # min.z +18.91
GLASS   = "/Game/StarterBundle/ModularScifiProps/Meshes/SM_Wall_B_Glass"    # min.z   0, corner pivot
LAMPF   = "/Game/SciFiCorridor/Meshes/SM_LampFloor"                         # min.z  -2.19, only 4.4cm tall
ARMORY  = "/Game/SciFiCorridor/Meshes/SM_ArmoryBox"                         # min.z -19.98
MONITOR = "/Game/SciFiCorridor/Meshes/SM_Monitor"                           # centred, wall-mounted
CABLE   = "/Game/SciFiCorridor/Meshes/SM_CorridorCable01"
TUBE    = "/Game/SciFiCorridor/Meshes/SM_Tube"                              # min.z   0

GROUND = {KIOSK: 0.0, LOADER: 8.89, TERMINAL: -18.91, GLASS: 0.0,
          ARMORY: 19.98, TUBE: 0.0, CRATE: 60.31, PILAR: 0.0}
LAMP_SCALE = 4.0                      # 4.4cm is invisible; x4 makes it a 17.5cm deck fixture
FLOOR_Z = 0.0                         # the interior walking surface


def stand(asset, x, y, z, yaw, stem, scale=1.0, mats=None):
    """Place so the mesh BASE meets z, using its measured min.z."""
    off = GROUND.get(asset, 0.0) * scale
    add_mesh(asset, (x, y, z + off), (0, yaw % 360.0, 0), (scale, scale, scale), stem, mats=mats)


# --- seven service kiosks on the layout's own Guide_ anchors -------------------
SERVICES = [
    ("upgrades", 200.0, -1000.0, (0.32, 0.72, 1.00)),
    ("repair", -800.0, -1000.0, (1.00, 0.62, 0.22)),
    ("contracts", -1100.0, 850.0, (0.40, 0.80, 1.00)),
    ("save", 0.0, 1000.0, (0.40, 1.00, 0.55)),
    ("launch", 950.0, -450.0, (0.45, 1.00, 0.60)),
    ("mica", 1000.0, 1000.0, (0.85, 0.55, 1.00)),
    ("beacon", -1400.0, 0.0, (1.00, 0.80, 0.35)),
]
for key, kx, ky, rgb in SERVICES:
    # snapped to 45 deg: still facing the deck centre, but on a grid. An arbitrary bearing
    # makes every prop around it off-square, which is what reads as wreckage.
    yaw = round(math.degrees(math.atan2(-ky, -kx)) / 45.0) * 45.0
    ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    stand(KIOSK, kx, ky, FLOOR_Z, yaw, f"kiosk_{key}", 1.25)
    # a terminal bank set BEHIND the kiosk, its 1.42m depth pushed back off the pivot
    stand(TERMINAL, kx - ca * 210.0, ky - sa * 210.0, FLOOR_Z, yaw, f"kioskterm_{key}")
    stand(ARMORY, kx - sa * 175.0, ky + ca * 175.0, FLOOR_Z, yaw, f"kioskbox_{key}")
    stand(TUBE, kx + sa * 205.0, ky - ca * 205.0, FLOOR_Z, yaw, f"kiosktube_{key}")
    for j, sgn in enumerate((-1.0, 1.0)):
        stand(LAMPF, kx + sa * sgn * 110.0, ky - ca * sgn * 110.0, FLOOR_Z, yaw,
              f"kiosklamp_{key}_{j}", LAMP_SCALE)
    padlight(f"kiosk_light_{key}", kx, ky, 235.0, rgb, 4200.0, 620.0)
    padlight(f"kiosk_wash_{key}", kx, ky, 60.0, rgb, 1700.0, 430.0)

# --- observation gallery: a glazed bay on the east wall of the WALKABLE box ----
# Windows only earn their keep if you can stand at them. The walkable interior stops at
# X 1750, so the glass runs just inside it rather than out on the unreachable hull.
GLASS_X, g = 1690.0, 0
gy = -1230.0
while gy < 1230.0:
    stand(GLASS, GLASS_X, gy, FLOOR_Z, 90.0, f"window_{g}")
    if g % 4 == 0:
        stand(LAMPF, GLASS_X - 150.0, gy + 60.0, FLOOR_Z, 0.0, f"windowlamp_{g}", LAMP_SCALE)
        padlight(f"window_light_{g}", GLASS_X - 190.0, gy + 60.0, 250.0,
                 (0.55, 0.78, 1.00), 2400.0, 640.0)
    g += 1
    gy += 122.6
# a rail of monitors facing the glass, so the gallery reads as an observation deck
for i in range(5):
    my = -960.0 + i * 480.0
    add_mesh(MONITOR, (GLASS_X - 120.0, my, 165.0), (0, 270, 0), (1, 1, 1), f"windowmon_{i}")
padlight("window_gallery", GLASS_X - 330.0, 0.0, 300.0, (0.42, 0.68, 1.00), 7000.0, 2100.0)

# --- deck crew: loader robots parked where cargo would move -------------------
for i, (lx, ly, lyaw) in enumerate([(-1500.0, -1150.0, 0.0), (1350.0, -1250.0, 180.0),
                                    (-1650.0, 1150.0, 270.0)]):
    stand(LOADER, lx, ly, FLOOR_Z, lyaw, f"loader_{i}")
    stand(CRATE, lx + 190.0, ly + 120.0, FLOOR_Z, round(lyaw / 90.0) * 90.0, f"loadercrate_{i}")
    padlight(f"loader_light_{i}", lx, ly, 210.0, (1.00, 0.72, 0.30), 2200.0, 520.0)

# --- clutter on the open deck, never in the docking lane ----------------------
CLUTTER = [
    (-1900.0, -2600.0), (-1600.0, -2750.0), (-1780.0, 2500.0), (-1450.0, 2680.0),
    (2600.0, -2300.0), (2900.0, -2480.0), (2700.0, 2350.0), (3050.0, 2520.0),
    (3900.0, -1200.0), (4050.0, 1150.0), (-2000.0, -1500.0), (-2050.0, 1450.0),
    (2300.0, -2900.0), (3400.0, 2000.0), (-1900.0, -3100.0), (3700.0, -2600.0),
]
for i, (cx, cy) in enumerate(CLUTTER):
    if abs(cy) < 760.0 and -1900.0 < cx < 1715.0:
        continue
    pick = (ARMORY, CRATE, TUBE)[i % 3]
    stand(pick, cx, cy, DECK_Z, (i % 4) * 90.0, f"clutter_{i}")

# --- hull dressing so the perimeter is not blank wall -------------------------
d = 0
for sy in (DECK_Y0 + 60.0, DECK_Y1 - 60.0):
    xx = DECK_X0 + 900.0
    while xx <= DECK_X1 - 900.0:
        add_mesh(CABLE, (xx, sy, 150.0), (0, 0.0 if sy < 0 else 180.0, 0), (1, 1, 1),
                 f"hullcable_{d}")
        if d % 3 == 0:
            add_mesh(MONITOR, (xx + 220.0, sy, 170.0), (0, 0.0 if sy < 0 else 180.0, 0),
                     (1, 1, 1), f"hullmon_{d}")
            padlight(f"hullmon_light_{d}", xx + 220.0, sy * 0.96, 190.0,
                     (0.40, 0.78, 1.00), 1500.0, 430.0)
        d += 1
        xx += 1200.0

# --- deck lights lining the main walking axes ---------------------------------
n = 0
for ax in range(-1500, 1600, 380):
    for sy in (-1380.0, 1380.0):
        stand(LAMPF, float(ax), sy, FLOOR_Z, 0.0, f"axislamp_{n}", LAMP_SCALE); n += 1
for ay in range(-1200, 1300, 380):
    stand(LAMPF, -1680.0, float(ay), FLOOR_Z, 0.0, f"axislampw_{n}", LAMP_SCALE); n += 1

# ============================================================ CORRIDOR DRESSING
# Every circulation route gets the same treatment rather than a handful of props dropped in the
# middle. Sci_Fi_Light is authored small - its bollard is 41 cm - so it scales x2.5 to human size.
SFL = "/Game/Sci_Fi_Light/Static_Meshes/%s/Mesh/%s"
BOLLARD  = SFL % ("SM_Sci_Fi_Bollard_Light", "SM_Sci_Fi_Bollard_Light")        # 8x8x41  -> x2.5
MONOLITH = SFL % ("SM_Sci_Fi_Monolith_Light", "SM_Sci_Fi_Monolith_Light")      # 9x9x40  -> x2.5
NEON     = SFL % ("SM_Sci_Fi_X_Frame_Neon_Sign", "SM_Sci_Fi_X_Frame_Neon_Sign")# 61x4x61 -> x2
CRATEPT  = "/Game/SciFiCorridor/Meshes/SM_Crate_Part"
HOOK     = "/Game/SciFiCorridor/Meshes/SM_Hook_01"
FLAG     = "/Game/SciFiCorridor/Meshes/SM_Flag_02"
CABLE2   = "/Game/SciFiCorridor/Meshes/SM_CorridorCable02"
SFL_S, NEON_S = 2.5, 2.0

def dress_run(axis, lo, hi, cross, tag, z=0.0, half=250.0, dense=1.0):
    """Lay a full kit along a corridor run: lights, cables, crates, pipes, hooks - both sides."""
    span = hi - lo
    if span <= 0:
        return 0
    n = 0

    def place(asset, along, side, height, yaw, scale=1.0, stem=""):
        nonlocal n
        if axis == "X":
            x, y = along, cross + side
        else:
            x, y = cross + side, along
        add_mesh(asset, (x, y, z + height), (0, yaw % 360.0, 0), (scale, scale, scale),
                 f"{tag}_{stem}{n}")
        n += 1

    # wall lights and floor bollards, alternating sides down the length
    a, i = lo + 120.0, 0
    while a < hi - 80.0:
        side = half - 40.0 if i % 2 else -(half - 40.0)
        yaw = (90.0 if axis == "X" else 0.0) + (180.0 if side > 0 else 0.0)
        place(BOLLARD, a, side, 0.0, yaw, SFL_S, "boll")
        if i % 2 == 0:
            place(MONOLITH, a + 90.0, -side, 0.0, yaw + 180.0, SFL_S, "mono")
        i += 1
        a += 240.0 / dense
    # cable runs at shoulder height on both walls
    a = lo + 60.0
    while a < hi - 60.0:
        for side in (-half, half):
            yaw = (0.0 if axis == "X" else 90.0) + (180.0 if side > 0 else 0.0)
            place(CABLE2 if int(a) % 2 else CABLE, a, side, 165.0, yaw, 1.0, "cab")
        a += 420.0 / dense
    # crates, boxes and part-crates pushed against the walls, never in the walking line
    a, i = lo + 260.0, 0
    while a < hi - 200.0:
        side = (half - 95.0) * (1 if i % 2 else -1)
        pick = (CRATE, ARMORY, CRATEPT, TUBE)[i % 4]
        off = {CRATE: 60.31, ARMORY: 19.98}.get(pick, 0.0)
        place(pick, a, side, off, (0.0 if axis == "X" else 90.0) + (180.0 if side > 0 else 0.0), 1.0, "box")
        i += 1
        a += 560.0 / dense
    # hooks and a flag high on the wall, plus a monitor every other bay
    a, i = lo + 380.0, 0
    while a < hi - 300.0:
        side = -half + 20.0 if i % 2 else half - 20.0
        yaw = (0.0 if axis == "X" else 90.0) + (180.0 if side > 0 else 0.0)
        place(HOOK, a, side, 210.0, yaw, 1.0, "hook")
        if i % 2 == 0:
            place(MONITOR, a + 140.0, side, 175.0, yaw, 1.0, "mon")
        if i % 3 == 0:
            place(FLAG, a + 60.0, side, 240.0, yaw, 1.0, "flag")
        i += 1
        a += 700.0 / dense
    # a light every other bay so the run is actually lit, not just decorated
    a = lo + 200.0
    while a < hi - 150.0:
        if axis == "X":
            padlight(f"{tag}_lt{int(a)}", a, cross, z + 250.0, (0.70, 0.86, 1.00), 2600.0, 560.0)
        else:
            padlight(f"{tag}_lt{int(a)}", cross, a, z + 250.0, (0.70, 0.86, 1.00), 2600.0, 560.0)
        a += 600.0
    return n


dressed = 0
dressed += dress_run("X", WALK_X0 + 40.0, WALK_X1 - 40.0, 0.0, "walkdress", 0.0, 250.0, 1.6)
for axis, a0, a1, cross in LINKS:
    lo, hi = (a0, a1) if a0 < a1 else (a1, a0)
    dressed += dress_run(axis, lo, hi, cross, f"link{axis}{int(lo)}dress", 0.0, 250.0, 1.0)

# the walkable interior perimeter - the ring the player actually circulates on
for i, (ax, ay, yaw) in enumerate([(1620.0, 0.0, 180.0), (-1620.0, 0.0, 0.0),
                                   (0.0, 1380.0, 270.0), (0.0, -1380.0, 90.0)]):
    if ax:
        dressed += dress_run("Y", -1300.0, 1300.0, ax, f"ring{i}", 0.0, 120.0, 0.7)
    else:
        dressed += dress_run("X", -1550.0, 1550.0, ay, f"ring{i}", 0.0, 120.0, 0.7)

# neon signage over every kiosk, so the seven service points read at a glance
for key, kx, ky, rgb in SERVICES:
    yaw = round(math.degrees(math.atan2(-ky, -kx)) / 45.0) * 45.0
    add_mesh(NEON, (kx, ky, 250.0), (0, yaw, 0), (NEON_S, NEON_S, NEON_S), f"kiosksign_{key}")
    padlight(f"kiosksign_lt_{key}", kx, ky, 300.0, rgb, 2600.0, 400.0)

# ====================================================== PLACES, NOT PROPS
# Five distinct areas with their own purpose, palette and silhouette, instead of one uniform
# scatter. A pit stop should read as somewhere people work, sell, wait and look out.
SHELF = "/Game/StarterBundle/ModularScifiProps/Meshes/SM_Shelf_A_v1"   # 183x64x141, corner pivot
UPG = "/Game/SpaceSurvival/Licensed/PlayerShipVisualPass/Meshes/%s"
PHX_L = "/Game/Stellar_Phoenix/Spaceship/Meshes/SM_Stellar_Phoenix_Engine_Left"
PHX_R = "/Game/Stellar_Phoenix/Spaceship/Meshes/SM_Stellar_Phoenix_Engine_Right"
# the upgrade meshes are authored at their position ON the ship, so their pivot sits ~162 cm
# outboard of the part itself. Re-centre before placing or every one hangs off its plinth.
UPG_CENTRE = 162.0


def display(asset, x, y, z, yaw, scale, stem):
    r = math.radians(yaw)
    add_mesh(asset, (x + math.cos(r) * UPG_CENTRE * scale, y + math.sin(r) * UPG_CENTRE * scale, z),
             (0, yaw % 360.0, 0), (scale, scale, scale), stem)


# --- 1. THE SHOWROOM, at the upgrades kiosk ----------------------------------
# Racked by tier so a player sees what they are working toward: tiers 2-3 shelved small,
# tier 5 standing full size on a lit plinth as the thing you cannot afford yet.
SX, SY = 200.0, -1000.0
FAMILIES = ["Cannon", "Engine", "Hull", "Laser", "Shield", "Thrusters"]
for i, fam in enumerate(FAMILIES):
    sx = SX - 520.0 + i * 210.0
    stand(SHELF, sx, SY - 430.0, FLOOR_Z, 0.0, f"show_shelf_{fam}")
    for t in (2, 3):
        display(UPG % f"SM_UpgradeHavolk{fam}{t}", sx + 90.0, SY - 400.0,
                FLOOR_Z + 60.0 + (t - 2) * 62.0, 0.0, 0.30, f"show_{fam}{t}")
    padlight(f"show_lt_{fam}", sx + 90.0, SY - 400.0, FLOOR_Z + 190.0,
             (0.45, 0.80, 1.00), 1500.0, 300.0)
# the hero tier, full size on the floor, warm-lit
for i, fam in enumerate(("Engine", "Cannon", "Shield")):
    hx = SX - 300.0 + i * 340.0
    stand(ARMORY, hx, SY + 380.0, FLOOR_Z, 0.0, f"show_plinth_{fam}")
    display(UPG % f"SM_UpgradeHavolk{fam}5", hx, SY + 380.0, FLOOR_Z + 50.0, 180.0, 0.55,
            f"show_hero_{fam}")
    padlight(f"show_hero_lt_{fam}", hx, SY + 380.0, FLOOR_Z + 210.0,
             (1.00, 0.78, 0.38), 3200.0, 380.0)

# --- 2. THE TROPHY RUN -------------------------------------------------------
# The thirteen power-ups as an exhibition down the concourse: each on its own plinth,
# floated and lit like a museum piece rather than dropped in a row on the floor.
TROPHY_TINT = [(0.35, 0.75, 1.00), (1.00, 0.72, 0.30), (0.50, 1.00, 0.62),
               (0.85, 0.55, 1.00), (1.00, 0.45, 0.42)]
_trophy_taken = []
for i, nm in enumerate(PICKUPS):
    side = -1.0 if i % 2 else 1.0
    tx = -1350.0 + (i // 2) * 350.0
    ty = side * 1300.0
    # a plinth landing on a kiosk's terminal bank is the only way two solids collided; slide
    # it along the run until it clears every service point rather than fixing it by hand.
    for _ in range(8):
        clear_kiosk = all(math.hypot(tx - kx, ty - ky) > 360.0 for _k, kx, ky, _c in SERVICES)
        clear_peer = all(math.hypot(tx - px, ty - py) > 250.0 for px, py in _trophy_taken)
        if clear_kiosk and clear_peer:
            break
        tx += 180.0
    _trophy_taken.append((tx, ty))
    stand(ARMORY, tx, ty, FLOOR_Z, 90.0 if side < 0 else 270.0, f"trophy_plinth_{i}")
    add_mesh(f"/Game/TripoModels/{nm}/{nm}", (tx, ty, FLOOR_Z + 118.0),
             (0, 90.0 if side < 0 else 270.0, 0), (0.62, 0.62, 0.62), f"trophy_{nm[:28]}")
    padlight(f"trophy_lt_{i}", tx, ty, FLOOR_Z + 235.0, TROPHY_TINT[i % 5], 1800.0, 300.0)

# --- 3. THE REPAIR BAY, at its kiosk ----------------------------------------
# The Phoenix's own nacelles up on stands, mid-service. Same mesh as the ship parked outside.
RX, RY = -800.0, -1000.0
for i, (mesh, off) in enumerate(((PHX_L, -260.0), (PHX_R, 260.0))):
    stand(ARMORY, RX + off, RY - 430.0, FLOOR_Z, 0.0, f"repair_stand_{i}")
    add_mesh(mesh, (RX + off, RY - 430.0, FLOOR_Z + 46.0), (0, 90.0 + i * 180.0, 0),
             (0.85, 0.85, 0.85), f"repair_nacelle_{i}")
    padlight(f"repair_lt_{i}", RX + off, RY - 430.0, FLOOR_Z + 250.0,
             (1.00, 0.60, 0.22), 2600.0, 420.0)
stand(LOADER, RX + 470.0, RY + 240.0, FLOOR_Z, 180.0, "repair_loader")
for i in range(5):
    stand((CRATEPT, TUBE, ARMORY)[i % 3], RX - 430.0 + i * 190.0, RY + 330.0, FLOOR_Z,
          (i % 2) * 90.0, f"repair_part_{i}")

# --- 4. CARGO, at the walkway mouth where freight would actually land --------
CGX, CGY = -1980.0, -980.0
for i in range(7):
    col, row = i % 3, i // 3
    stand(CRATE, CGX + col * 165.0, CGY + row * 158.0, FLOOR_Z, 0.0, f"cargo_{i}")
stand(LOADER, CGX + 520.0, CGY + 120.0, FLOOR_Z, 90.0, "cargo_loader")
padlight("cargo_lt", CGX + 160.0, CGY + 80.0, FLOOR_Z + 280.0, (1.00, 0.80, 0.40), 3000.0, 700.0)

# --- 5. THE GALLERY gets seating and standing lights, not just glass ---------
for i in range(4):
    gy = -900.0 + i * 600.0
    stand(MONOLITH, GLASS_X - 280.0, gy, FLOOR_Z, 270.0, f"gallery_mono_{i}", SFL_S)
    stand(ARMORY, GLASS_X - 430.0, gy + 150.0, FLOOR_Z, 270.0, f"gallery_seat_{i}")

# ============================================================== ROOF
# The deck had a perimeter wall and no roof, so everything between the wings was open to space and
# the kit rooms were being seen from outside - which is why the whole thing read as an unlit plate.
# The station is INTERIOR. The pad and its approach stay exterior; everything from the airlock in
# is enclosed. Wing rooms carry their own ceilings at their own heights, so the roof skips them.
ROOF_Z = CEIL_Z                       # 307, matching the wall course and the link corridors
WINGS_FOOTPRINT = [
    (-1700.0, 1700.0, -850.0, 850.0),        # corridor junction complex
    (2400.0, 4400.0, -1460.0, 1460.0),       # command centre
    (-1750.0, 1750.0, 2450.0, 3950.0),       # props hall north
    (-1750.0, 1750.0, -3950.0, -2450.0),     # props hall south
]


def _under_wing(x, y):
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, x1, y0, y1 in WINGS_FOOTPRINT)


roof = 0
ry = DECK_Y0
while ry < DECK_Y1:
    rx = DECK_X0
    while rx < DECK_X1:
        if not _under_wing(rx + CEIL_PITCH * .5, ry + 256.0):
            add_mesh(CEIL, (rx, ry, ROOF_Z), (0, 0, 0), (1, 1, 1), f"roof_{roof}")
            roof += 1
        rx += CEIL_PITCH
    ry += 512.0

# a light under every sixth roof tile, so the enclosed deck is lit from above like a room
lit = 0
ry = DECK_Y0 + 256.0
while ry < DECK_Y1:
    rx = DECK_X0 + 600.0
    while rx < DECK_X1:
        if not _under_wing(rx, ry):
            padlight(f"rooflight_{lit}", rx, ry, ROOF_Z - 60.0, (0.74, 0.85, 1.00), 3000.0, 1100.0)
            lit += 1
        rx += 1800.0
    ry += 1550.0

# ====================================================== FOUNDATION PLATFORM
# The base sits on an asteroid whose surface undulates ~40 m under the footprint. Rather than
# pretend the rock has a machined bowl, the outpost gets a built foundation - which is what an
# actual outpost on uneven ground would have. Megastructure floor modules are 25x25 m with their
# pivot at the TOP corner (z spans -200..0), so the placement Z is the walking surface.
PLATE = "/Game/Megastructure_Scifi_World/Meshes/Floor/SM_floor_module_01"   # 2500x2500x200
PLATE_SPAN = 2500.0
PLATE_Z = DECK_Z - 12.0            # 12 cm under the deck so it reads as a foundation lip
plate = 0
py_ = DECK_Y0 - 100.0
while py_ < DECK_Y1 + 100.0:
    px = DECK_X0 - 100.0
    while px < DECK_X1 + 100.0:
        add_mesh(PLATE, (px, py_, PLATE_Z), (0, 0, 0), (1, 1, 1), f"plat_{plate}")
        plate += 1
        px += PLATE_SPAN
    py_ += PLATE_SPAN
# a skirt of the same plates one step down and out, so the platform has thickness from below
skirt = 0
for sx, sy in ((DECK_X0 - 2600.0, 0.0), (DECK_X1 + 100.0, 0.0)):
    yy = DECK_Y0 - 100.0
    while yy < DECK_Y1:
        add_mesh(PLATE, (sx, yy, PLATE_Z - 900.0), (0, 0, 0), (1, 1, 1), f"platskirt_{skirt}")
        skirt += 1
        yy += PLATE_SPAN

# ====================================================== COLONY DISTRICT (lower terrace)
# The Ultimate Space Colony Outpost pack is 30 glTF-converted modules, each ~1 m and each capped
# at 1.5M triangles (Nanite was off on arrival and has been enabled on all 30 - without it these
# are unshippable). At their authored scale they are props; scaled x8-x16 they become the
# background town the outpost has been missing. They carry no interiors and sit OUTSIDE
# ASSStation::Walkable(), so they are silhouette and depth only - nothing the player can enter.
COL = "/Game/Ultimate_Space_Colony_Outpost_Pack/Mesh/SM_N_0_node_0_%s"

# measured min.z per module, so a base meets the terrace instead of floating or sinking
COL_MINZ = {
    "02cbb809": -42.8, "0e91b437": -26.0, "1b070bc8": -27.0, "2c8f5471": -46.0,
    "2d53a3ce": -34.7, "31ae4aa4": -21.1, "33f78fbd": -40.3, "3f257365": -40.6,
    "42621487": -47.7, "43170fc0": -30.1, "488478fc": -30.7, "51702727": -39.0,
    "685404fa": -30.8, "9d2c502a": -22.2, "a0585acf": -50.3, "a1d1c3ad": -25.4,
    "b3e50c39": -40.8, "b5620d09": -38.3, "bcca6cd0": -33.4, "cd3e7dc4": -55.9,
    "d0b31940": -29.6, "d1c9ae4d": -33.0, "d32a908b": -22.8, "d450ca1a": -28.7,
    "eefb4b0b": -37.6, "f70883da": -26.6, "fb29e835": -44.4,
}
# b8d2dede, c30d22d1 and de44f686 are deliberately absent: all three have magenta faces baked
# into their BaseColor (an artefact of the pack's AI generation, not a missing material), which
# reads as an error the moment they are scaled up.

TERRACE_Z = PLATE_Z - 900.0        # the same step down the platform skirt already uses
TERR_HALF = 12500.0
CHAMFER = 8750.0                   # corners cut, so the pad reads as built rather than as a box

def colony(stem, key, x, y, scale, yaw):
    """Place a colony module with its BASE on the terrace, on a grid-snapped heading."""
    add_mesh(COL % key, (x, y, TERRACE_Z - COL_MINZ[key] * scale),
             (0, yaw % 360.0, 0), (scale, scale, scale), stem)

def district_light(stem, x, y, z, rgb, intensity, radius):
    lights.append({"name": name_for(stem), "location": [x, y, z],
                   "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0],
                   "color": list(rgb), "intensity": intensity,
                   "attenuation_radius": radius, "cast_shadows": False})

# --- the terrace: a chamfered apron one tier below the outpost's own foundation
terr = 0
ty = -TERR_HALF
while ty < TERR_HALF:
    tx = -TERR_HALF
    while tx < TERR_HALF:
        cx, cy = tx + PLATE_SPAN / 2.0, ty + PLATE_SPAN / 2.0
        over_platform = (tx < DECK_X1 + 100.0 and tx + PLATE_SPAN > DECK_X0 - 100.0 and
                         ty < DECK_Y1 + 100.0 and ty + PLATE_SPAN > DECK_Y0 - 100.0)
        over_pad = (tx < PAD_X1 and tx + PLATE_SPAN > PAD_X0 and
                    ty < PAD_Y1 and ty + PLATE_SPAN > PAD_Y0)
        cut_corner = abs(cx) > CHAMFER and abs(cy) > CHAMFER
        if not (over_platform or over_pad or cut_corner):
            add_mesh(PLATE, (tx, ty, TERRACE_Z), (0, 0, 0), (1, 1, 1), f"terr_{terr}")
            terr += 1
        tx += PLATE_SPAN
    ty += PLATE_SPAN

# --- the town. Two streets per side rather than one, because a single file of buildings around
# a rim reads as a fence, not a settlement. Every heading is a multiple of 90; the previous pass
# of pseudo-random yaws read as debris.
HAB   = ["3f257365", "2d53a3ce", "51702727", "eefb4b0b", "fb29e835", "d0b31940"]
INDUS = ["43170fc0", "488478fc", "685404fa", "bcca6cd0", "d1c9ae4d", "1b070bc8"]
TANK  = ["42621487", "b3e50c39", "b5620d09"]
CONT  = ["0e91b437", "a1d1c3ad", "9d2c502a", "d32a908b"]
MAST  = ["2c8f5471", "cd3e7dc4", "f70883da", "a0585acf"]

# Street lighting is sized by measurement, not by eye. A point light's contribution falls off as
# 1/r^2, so a lamp 9.5 m over an open deck is nothing like a corridor fixture 2.5 m over a floor.
# Reference: the station's own BayLight is 120000 at 650 cm -> 120000/650^2 = 0.284. The first
# pass put street lamps at 15640 (post-grade) and 950 cm -> 0.017, SIXTEEN TIMES dimmer than the
# light the station already reads by, which is why the terrace rendered as a void with 38 light
# sprites floating over it. These values drop the lamps to 5 m and match BayLight illuminance.
# (label, axis, fixed, start, step, count, palette, scale, yaw-facing-the-station)
ROWS = [
    ("nA", "y",   7400.0, -3500.0, 1700.0, 7, HAB,   10.0, 270),
    ("nB", "y",  10200.0, -4500.0, 2000.0, 7, INDUS, 11.0, 270),
    ("sA", "y",  -6200.0, -3500.0, 1700.0, 7, HAB,   10.0,  90),
    ("sB", "y",  -9000.0, -4500.0, 2000.0, 7, INDUS, 11.0,  90),
    ("eA", "x",   7000.0, -5500.0, 1700.0, 8, CONT,   8.0, 180),
    ("eB", "x",   9800.0, -6500.0, 2000.0, 8, HAB,   10.0, 180),
    ("wA", "x",  -8000.0, -5500.0, 1700.0, 8, INDUS, 11.0,   0),
    ("wB", "x", -10800.0, -6500.0, 2000.0, 8, CONT,   8.0,   0),
]
town = 0
lamp = 0
for label, axis, fixed, start, step, count, palette, sc, yaw in ROWS:
    for i in range(count):
        along = start + i * step
        x, y = (along, fixed) if axis == "y" else (fixed, along)
        colony(f"col_{label}_{i}", palette[i % len(palette)], x, y, sc, yaw)
        town += 1
        # a lamp every other lot, set between the lots so the street lights and the gaps stay dark
        if i % 2 == 1:
            lx, ly = (along - step / 2.0, fixed) if axis == "y" else (fixed, along - step / 2.0)
            district_light(f"col_lamp_{label}_{i}", lx, ly, TERRACE_Z + 500.0,
                           (1.00, 0.66, 0.34), 220000.0, 5200.0)
            lamp += 1

# corner clusters, so the chamfers are occupied instead of being bare cut edges
CORNER_MIX = [TANK[0], INDUS[2], CONT[1], HAB[4]]
for ci, (cx_, cy_) in enumerate([(8200.0, 8200.0), (8200.0, -7600.0),
                                 (-9400.0, -7600.0), (-9400.0, 8200.0)]):
    for j, dx, dy in ((0, 0.0, 0.0), (1, 1600.0, 0.0), (2, 0.0, 1600.0), (3, 1600.0, 1600.0)):
        colony(f"col_corner_{ci}_{j}", CORNER_MIX[j], cx_ + dx, cy_ + dy, 9.0, 90 * j)
        town += 1
    district_light(f"col_corner_lamp_{ci}", cx_ + 800.0, cy_ + 800.0, TERRACE_Z + 600.0,
                   (0.44, 0.70, 1.00), 160000.0, 4600.0)
    lamp += 1

# tank farm: a block rather than a line, so not every silhouette is a straight run
for ti, (tx_, ty_, tk) in enumerate([(4200.0, -7400.0, TANK[0]), (5700.0, -7400.0, TANK[1]),
                                     (4200.0, -8900.0, TANK[2]), (5700.0, -8900.0, TANK[0])]):
    colony(f"col_tank_{ti}", tk, tx_, ty_, 9.0, 90 * (ti % 4))
    town += 1
district_light("col_tankfarm", 4950.0, -8150.0, TERRACE_Z + 550.0, (0.30, 0.62, 1.00), 170000.0, 4600.0)
lamp += 1

# the gate: the archway on the landing-pad approach, flanked by two hab blocks, facing the pad
colony("col_gate", "02cbb809", -8600.0, 0.0, 14.0, 0)
colony("col_gate_l", HAB[0], -8600.0, -2300.0, 10.0, 0)
colony("col_gate_r", HAB[3], -8600.0,  2300.0, 10.0, 0)
town += 3
district_light("col_gate_lamp", -8100.0, 0.0, TERRACE_Z + 700.0, (1.00, 0.58, 0.24), 300000.0, 6000.0)
lamp += 1

# skyline: the only pieces tall enough to break the roofline, on the four chamfers
for mi, (mx, my, mk) in enumerate([(-6200.0, 10400.0, MAST[0]), (10400.0,  6200.0, MAST[1]),
                                   (6200.0, -10000.0, MAST[2]), (-10400.0, -5200.0, MAST[3])]):
    colony(f"col_mast_{mi}", mk, mx, my, 16.0, 90 * mi)
    town += 1
    district_light(f"col_mast_lamp_{mi}", mx, my, TERRACE_Z + 1900.0,
                   (0.38, 0.72, 1.00), 180000.0, 3600.0)
    lamp += 1

print(f"colony district    {town} structures, {terr} terrace plates, {lamp} district lights")

# The ModularSci_Comm kit is a white/grey set lit by white panels, so a faithful copy of its own
# lighting reads monochrome. These are the art direction the marketing shots have and the demo
# map does not: a warm floor wash and a cool rim, per wing.
ACCENTS = [
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
for ai, (ax, ay, az, r, g, b, intensity, radius) in enumerate(ACCENTS):
    lights.append({"name": name_for(f"accent_{ai}"),
                   "location": [ax, ay, az], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0],
                   "color": [r, g, b], "intensity": intensity,
                   "attenuation_radius": radius, "cast_shadows": False})

# Group every placement by the mesh it uses, so the Blueprint gets ONE instanced component per
# distinct asset instead of one component per placement. 1,793 individual StaticMeshComponents
# compiled fine and then hung PIE while the actor constructed; 164 instanced ones is the shape
# ASSStation::BuildHub already uses for its own dressing.
batches = {}
for m in meshes:
    key = (m["asset"], tuple(m.get("materials", ())), m["cast_shadows"])
    batches.setdefault(key, []).append(m)

instanced = []
for (a, mats, shadows), group in sorted(batches.items(), key=lambda kv: -len(kv[1])):
    entry = {"name": name_for("ism_" + a.rsplit("/", 1)[-1]),
             "asset": a,
             "cast_shadows": shadows,
             "instances": [{"location": g["location"], "rotation": g["rotation"], "scale": g["scale"]}
                           for g in group]}
    if mats:
        entry["materials"] = list(mats)
    instanced.append(entry)

# --flat emits one StaticMeshComponent per placement, which is all the SHIPPED binary can parse.
# The instanced path needs the SSStationVisualLayout.cpp change compiled in first.
import sys
FLAT = "--flat" in sys.argv
# --------------------------------------------------------------- light grade
# Darker and more realistic: the first pass lit everything evenly, which reads as a showroom, not
# a working station. Cutting intensity hard and pulling the radii in turns fill into POOLS - lit
# where something is happening, dark between. The emissive fixtures still read as sources, so the
# place stays legible without being flooded. Applies only to lights this recipe creates; the
# station's own BayLights are harvested by the C++ and untouched.
DIM_INTENSITY, DIM_RADIUS = 0.34, 0.80
_before = sum(l["intensity"] for l in lights)
for l in lights:
    l["intensity"] = round(l["intensity"] * DIM_INTENSITY, 1)
    l["attenuation_radius"] = round(l["attenuation_radius"] * DIM_RADIUS, 1)
_after = sum(l["intensity"] for l in lights)

recipe = ({"static_meshes": meshes, "point_lights": lights} if FLAT
          else {"instanced_meshes": instanced, "point_lights": lights})
OUT.write_text(json.dumps(recipe), encoding="utf-8")

extent_x = (min(m["location"][0] for m in meshes), max(m["location"][0] for m in meshes))
extent_y = (min(m["location"][1] for m in meshes), max(m["location"][1] for m in meshes))
print(f"meshes            {len(meshes)}   (deck {deck}, hull {hull}, columns {col})")
print(f"point lights      {len(lights)}   energy {_before:.0f} -> {_after:.0f} ({100*_after/_before:.0f}% of before)")
print(f"doorways opened   {skipped['opened']}")
print(f"DROPPED spot      {skipped['spot']}   (recipe has no spot_lights)")
print(f"DROPPED rect      {skipped['rect']}   (recipe has no rect_lights)")
print(f"footprint         {(extent_x[1] - extent_x[0]) / 100:.1f} x {(extent_y[1] - extent_y[0]) / 100:.1f} m")
print(f"distinct assets   {len({m['asset'] for m in meshes})}")
print(f"instanced comps   {len(instanced)}  "
      f"(largest {max(len(i['instances']) for i in instanced)} instances)")
print(f"component total   {len(instanced) + len(lights)}  was {len(meshes) + len(lights)}")
print(f"recipe            {OUT}  ({OUT.stat().st_size / 1024:.0f} KB)")
