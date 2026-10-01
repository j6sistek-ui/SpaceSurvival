"""Native Genesis panels attached to the existing moving door anchors.

AuthorOutpostSandbox.door uses yaw-only actors, a native frame scaled Z1.25,
and LeftClosed/RightClosed=(0,+/-75,150). SSOutpostSandbox.cpp moves each leaf
and its separately root-attached blocker; it does not reset leaf meshes.
This helper changes only visual mesh/scale and attaches noncolliding children.
The native floor pivot is retained, matching the frame's vertical openings.

Installed UE5.8 source checked: SceneComponent GetWorldLocation/SetRelativeScale3D,
BoxComponent GetScaledBoxExtent, and Actor AttachToComponent are reflected APIs.
No C++ or source-asset changes; call apply(globals()) after all door() calls.
"""
import json
import math
from pathlib import Path


ASSET = "/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_Door200X250_V1_Part2.SM_Door200X250_V1_Part2"
VISUAL_SCALE = 1.25
BACKING_THICKNESS = 2.0
MARKER = "OutpostNativeDoorVisual"
# Catalog measurements are used by pure checks. apply verifies current loaded
# geometry before touching actors and uses its live values for placement.
NATIVE_ORIGIN = (-.000001192, -.000068665, 130.872300148)
NATIVE_EXTENT = (6.025609732, 59.813747406, 111.6429739)


def rotate(v, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return [v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2]]


def transform(position, yaw, local):
    return [a + b for a, b in zip(position, rotate(local, yaw))]


def visual_transform(position, yaw, closed, travel=(0, 0, 0), fraction=0,
                     origin=NATIVE_ORIGIN, extent=NATIVE_EXTENT):
    """Bounds-centred native panel and its native-pivot actor location."""
    # The frame and panel share floor Z0. Do not centre this native panel at
    # the physical blocker's Z150: that would move its top below the header.
    local_center = [closed[0], closed[1], origin[2] * VISUAL_SCALE]
    local_center = [a + b * fraction for a, b in zip(local_center, travel)]
    center = transform(position, yaw, local_center)
    offset = rotate([v * VISUAL_SCALE for v in origin], yaw)
    return {"center": center, "pivot": [a - b for a, b in zip(center, offset)],
            "size": [v * 2 * VISUAL_SCALE for v in extent], "yaw": yaw}


def self_check(origin=NATIVE_ORIGIN, extent=NATIVE_EXTENT):
    checks = []
    for yaw in (0, 90, 180, -90):
        for sign in (-1, 1):
            closed, travel = (0, sign * 75, 150), (0, sign * 160, 0)
            position = (4200, -2300, 0)
            start = visual_transform(position, yaw, closed, origin=origin, extent=extent)
            end = visual_transform(position, yaw, closed, travel, 1, origin, extent)
            recovered = transform(start["pivot"], yaw, [v * VISUAL_SCALE for v in origin])
            assert max(abs(a - b) for a, b in zip(recovered, start["center"])) < .001
            delta = [b - a for a, b in zip(start["center"], end["center"])]
            assert max(abs(a - b) for a, b in zip(delta, rotate(travel, yaw))) < .001
            assert abs(start["pivot"][2] - position[2]) < .001
            checks.append({"yaw": yaw, "side": sign, "pivot_and_travel_preserved": True})
    width = extent[1] * 2 * VISUAL_SCALE
    seam, passage = 150 - width, 470 - width
    assert 0 <= seam < 1, "Native leaves must meet with a sub-centimetre seam"
    assert passage >= 300, "Visual panels must preserve at least 300cm open clearance"
    bottom = (origin[2] - extent[2]) * VISUAL_SCALE
    top = (origin[2] + extent[2]) * VISUAL_SCALE
    assert 20 < bottom < 30 and 300 < top < 305
    assert BACKING_THICKNESS < extent[0] * 2 * VISUAL_SCALE
    return {"geometry_only": True, "transforms": checks, "closed_seam_cm": seam,
            "open_visual_clearance_cm": passage, "panel_bottom_cm": bottom,
            "panel_top_cm": top, "native_uniform_scale": VISUAL_SCALE,
            "inset_backing_thickness_cm": BACKING_THICKNESS}


def apply(api):
    u, eas = api["u"], api["EAS"]
    mesh = api["load"](ASSET)
    b = mesh.get_bounds()
    values = lambda v: [v.x, v.y, v.z]
    origin, extent = values(b.origin), values(b.box_extent)
    geometry = self_check(origin, extent)
    doors = [a for a in eas.get_all_level_actors()
             if isinstance(a, u.SSOutpostDoor) and a.get_actor_label().startswith("Doors/")]
    if not doors:
        raise ValueError("Author the sandbox doors before adding native visual panels")
    properties = ("left_closed", "right_closed", "left_travel", "right_travel",
                  "leaf_half_extent", "safety_half_extent", "sensor_radius",
                  "slide_seconds", "hold_open_seconds")

    def physics_state(door):
        state = {}
        for key in properties:
            value = door.get_editor_property(key)
            state[key] = values(value) if isinstance(value, u.Vector) else value
        state["blockers"] = [
            {"location": values(c.get_world_location()), "extent": values(c.get_scaled_box_extent()),
             "collision": str(c.get_collision_enabled())}
            for c in (door.left_blocker, door.right_blocker)]
        return state

    prepared = []
    for door in doors:
        rotation, scale = door.get_actor_rotation(), values(door.get_actor_scale3d())
        if abs(rotation.pitch) > .001 or abs(rotation.roll) > .001 or max(abs(v - 1) for v in scale) > .001:
            raise ValueError("Door visual helper requires the author's unscaled yaw-only doors")
        if abs(door.open_fraction) > .001:
            raise ValueError("Stop Play and close the saved sandbox doors before authoring visuals")
        prepared.append((door, physics_state(door), rotation.yaw))
    wanted_labels = {a.get_actor_label() + "/Native " + side + " " + piece
                     for a in doors for side in ("left", "right") for piece in ("panel", "seal")}
    # Idempotency is scoped to this helper's explicit actor tag AND exact labels.
    removed = 0
    for actor in eas.get_all_level_actors():
        if actor.get_actor_label() in wanted_labels and MARKER in [str(t) for t in actor.tags]:
            if not eas.destroy_actor(actor):
                raise RuntimeError("Unable to replace native door visual: " + actor.get_actor_label())
            removed += 1
    receipt = {"geometry": geometry, "replaced_visual_actors": removed, "panels": [], "backing_plates": []}
    for door, before, yaw in prepared:
        position = values(door.get_actor_location())
        for side in ("left", "right"):
            anchor = getattr(door, side + "_leaf")
            anchor.set_static_mesh(None)
            anchor.set_relative_scale3d(u.Vector(1, 1, 1))
            closed = values(door.get_editor_property(side + "_closed"))
            tx = visual_transform(position, yaw, closed, origin=origin, extent=extent)
            name = door.get_actor_label() + "/Native " + side + " panel"
            child = api["place"](name, ASSET, tx["center"], size=tx["size"], yaw=yaw, solid=False)
            child.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
            api["tag"](child, MARKER)
            api["tag"](child, "OutpostRole:DoorLeafVisual")
            attached = child.attach_to_component(anchor, u.Name(""), u.AttachmentRule.KEEP_WORLD,
                                                u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False)
            if not attached:
                raise RuntimeError("Unable to attach native door visual to " + side + " leaf")
            receipt["panels"].append({"name": name, "asset": ASSET, "center": tx["center"],
                                      "size": tx["size"], "yaw": yaw, "anchor": anchor.get_name()})
            # The vendor leaf has a shaped perimeter. A thin dark inset core
            # closes the triangular top/bottom cutouts seen in Capture6 while
            # leaving the native raised faces exposed on BOTH sides. It lies
            # inside the native 15cm thickness, not over either detailed face.
            seal_name = door.get_actor_label() + "/Native " + side + " seal"
            seal_size = [BACKING_THICKNESS, tx["size"][1], tx["size"][2]]
            seal = api["place"](seal_name, "/Engine/BasicShapes/Cube.Cube", tx["center"],
                                size=seal_size, yaw=yaw, solid=False, material=api["DARK"])
            seal.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
            api["tag"](seal, MARKER)
            api["tag"](seal, "OutpostRole:DoorLeafVisual")
            if not seal.attach_to_component(anchor, u.Name(""), u.AttachmentRule.KEEP_WORLD,
                                            u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False):
                raise RuntimeError("Unable to attach native door inset core")
            receipt["backing_plates"].append({"name": seal_name, "center": tx["center"], "size": seal_size})
        if physics_state(door) != before:
            raise RuntimeError("Native door visuals unexpectedly changed physical door settings")
    receipt["physical_blockers_and_settings_preserved"] = True
    (Path(api["OUT"]) / "door-visuals.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt
