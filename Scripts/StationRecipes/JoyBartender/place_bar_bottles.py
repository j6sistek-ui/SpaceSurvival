"""Check the Fab prop packs the owner unpacked into Content (CS1 benches and street light, MLR bar props, CPM solar frame)
all load, then stand the MLR alcohol bottles on the bar top beside the bartender in L_WayfarerRuntime.

  set SS_BOTTLES_REPORT=<json>      set SS_BOTTLES_BACKUP=<copy of the map before the edit>
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI ... -ExecutePythonScript="<abs>/place_bar_bottles.py"

Owner 2026-10-14: "there are some alcohol bottles to add to the bar top (if these aren't already in the game)". The bar
set's own bottles sit on the shelves behind her; these go on the counter. The counter is found by its mesh name and its
top height near the bartender; without one nothing is placed and the report says so.
"""
import json
import os
import shutil

import unreal as u

MAP = "/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime"
LABEL = "Crew/Lounge guest"
PACKS = ["/Game/CS1_Bench_01", "/Game/CS1_Bench_03", "/Game/CS1_Bench_08", "/Game/CS1_Bench_10", "/Game/CS1_StreetLight_01", "/Game/CPM_SolarFrame",
         "/Game/MLR_AlcoholBottles_Bottle07", "/Game/MLR_BarCounter_WallDecor01", "/Game/MLR_IlluminatedWall", "/Game/MLR_Minibar", "/Game/MLR_StageLight"]
BOTTLES = "/Game/MLR_AlcoholBottles_Bottle07"
REPORT = os.environ.get("SS_BOTTLES_REPORT", "")
BACKUP = os.environ.get("SS_BOTTLES_BACKUP", "")
COUNT = 6
SPACING = 16.0  # cm between bottles along the counter
L = u.EditorAssetLibrary
AR = u.AssetRegistryHelpers.get_asset_registry()


def log(s):
    u.log_warning("BOTTLES| " + str(s))


# --- every asset of every pack loads; static meshes reported with their size
packs = {}
for pack in PACKS:
    AR.scan_paths_synchronous([pack], True)
    rows = AR.get_assets_by_path(pack, True)
    loaded, failed, meshes = 0, [], []
    for ad in rows:
        a = ad.get_asset()
        if a is None:
            failed.append(str(ad.package_name))
            continue
        loaded += 1
        if isinstance(a, u.StaticMesh):
            b = a.get_bounds()
            meshes.append({"path": a.get_path_name(), "size_cm": [round(v * 2, 1) for v in b.box_extent.to_tuple()], "materials": len(a.static_materials)})
        elif isinstance(a, u.SkeletalMesh):
            meshes.append({"path": a.get_path_name(), "skeletal": True})
    packs[pack] = {"assets": len(rows), "loaded": loaded, "failed": failed, "meshes": meshes}
    log("%s: %d assets, %d failed, meshes %s" % (pack, len(rows), len(failed), [m["path"].rsplit("/", 1)[1] for m in meshes]))
bottle_meshes = [u.load_asset(m["path"].split(".")[0]) for m in packs[BOTTLES]["meshes"] if not m.get("skeletal")]
assert bottle_meshes, "no bottle static mesh in the pack"

# --- the counter beside the bartender
assert u.EditorLevelLibrary.load_level(MAP)
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
bar = next((a for a in actors if a.get_actor_label() == LABEL), None)
assert bar, LABEL
b = bar.get_actor_location()
fwd = bar.get_actor_forward_vector()
right = bar.get_actor_right_vector()
feet_z = b.z - bar.body.get_scaled_capsule_half_height()
candidates = []
for a in actors:
    if not isinstance(a, u.StaticMeshActor):
        continue
    sm = a.static_mesh_component.static_mesh if a.static_mesh_component else None
    if not sm:
        continue
    name = sm.get_name().lower()
    if not any(k in name for k in ("bar", "counter")):
        continue
    o, e = a.get_actor_bounds(False)
    d = o - b
    dist = (d.x ** 2 + d.y ** 2) ** 0.5
    top = o.z + e.z
    if dist > 450 or not (feet_z + 70 <= top <= feet_z + 135):
        continue
    ahead = d.x * fwd.x + d.y * fwd.y
    candidates.append({"actor": a, "label": a.get_actor_label(), "mesh": sm.get_name(), "dist": dist, "top": top, "ahead": ahead, "origin": o, "extent": e})
candidates.sort(key=lambda c: (c["ahead"] < 20, c["dist"]))
log("counter candidates: %s" % [(c["label"], c["mesh"], round(c["dist"]), round(c["top"] - feet_z), round(c["ahead"])) for c in candidates])
placed = []
if candidates:
    c = candidates[0]
    if BACKUP:
        shutil.copy2(u.SystemLibrary.get_system_path(u.load_asset(MAP)), BACKUP)
    # a row along the counter's long axis, on the back half of the top (her side), starting a little to her right
    long_axis = right if c["extent"].x * abs(right.x) + c["extent"].y * abs(right.y) >= c["extent"].x * abs(fwd.x) + c["extent"].y * abs(fwd.y) else fwd
    o = c["origin"]
    depth = c["extent"].x * abs(fwd.x) + c["extent"].y * abs(fwd.y)
    back = u.Vector(o.x - fwd.x * depth * 0.45, o.y - fwd.y * depth * 0.45, c["top"])
    start = u.Vector(back.x + right.x * 35.0, back.y + right.y * 35.0, back.z)
    for i in range(COUNT):
        mesh = bottle_meshes[i % len(bottle_meshes)]
        loc = u.Vector(start.x + long_axis.x * SPACING * i, start.y + long_axis.y * SPACING * i, c["top"] + 0.2)
        actor = u.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, u.Rotator(0.0, 0.0, (i * 37) % 360))
        actor.set_actor_label("Bar/Bottle_%02d" % (i + 1))
        actor.set_folder_path("Bar")
        actor.static_mesh_component.set_mobility(u.ComponentMobility.STATIC)
        placed.append({"label": actor.get_actor_label(), "mesh": mesh.get_name(), "location": list(loc.to_tuple())})
    assert u.EditorLevelLibrary.save_current_level(), "map save failed"
    assert u.EditorLevelLibrary.load_level(MAP)
    labels = {a.get_actor_label() for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    assert all(p["label"] in labels for p in placed), [p["label"] for p in placed if p["label"] not in labels]
# the candidate's actor handle is dead after the level reload: only plain values go into the report
report = {"packs": packs, "counter": {k: v for k, v in (candidates[0].items() if candidates else []) if k in ("label", "mesh", "dist", "top", "ahead")},
          "placed": placed, "bartender_feet_z": feet_z}
if REPORT:
    json.dump(report, open(REPORT, "w"), indent=1, default=str)
log("DONE placed %d bottles; counter %s" % (len(placed), candidates[0]["label"] if candidates else None))
