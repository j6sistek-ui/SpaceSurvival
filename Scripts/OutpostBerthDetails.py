"""Owned-kit surface and service detail for the three outpost berths.

Pure layout/audit functions do not import Unreal. Existing discs remain the
collision authority; all new deck tiles and below-deck trim are noncolliding.
Raised maintenance assemblies stay outside the conservative ship/route bounds.
"""
import json
import math
import os
from pathlib import Path


PADS = (
    {"name": "Player", "center": (-4200, 0), "radius": 3000},
    {"name": "Visitor02", "center": (-600, -3900), "radius": 1400},
    {"name": "Visitor03", "center": (-600, 3900), "radius": 1400},
)
# Conservative plan-view exclusions for any new above-deck furniture. They
# exceed the visible hull/ramp bounds rather than depending on animation pose.
CLEARWAYS = (
    ("Phoenix wings / launch", (-5900, -1600, -2300, 1600)),
    ("Ramp / cockpit approach", (-5200, -260, -1450, 260)),
    ("Ship finish access", (-3250, -1520, -2550, -850)),
    ("Courier / launch", (-1450, -4750, 250, -3050)),
    ("Flanker / launch", (-1450, 3050, 250, 4750)),
    ("South berth bridge", (-1050, -3900, -150, -1750)),
    ("North berth bridge", (-1050, 1750, -150, 3900)),
)


def bounds(row):
    """Conservative world AABB from bounds-centred local dimensions + yaw."""
    x, y, z = row["center"]
    sx, sy, sz = row["size"]
    c, s = abs(math.cos(math.radians(row["yaw"]))), abs(math.sin(math.radians(row["yaw"])))
    hx, hy = (sx * c + sy * s) / 2, (sx * s + sy * c) / 2
    return [x - hx, y - hy, z - sz / 2, x + hx, y + hy, z + sz / 2]


def layout(catalog):
    meshes = catalog["meshes"] if isinstance(catalog, dict) else catalog
    rows = []

    def get(name, pack="P4_Genesis_Vol1"):
        found = [m for m in meshes if m["name"] == name and pack in m["asset"]]
        if len(found) != 1:
            raise ValueError("Missing or ambiguous berth mesh: " + name)
        return found[0]

    def put(name, mesh, center, yaw=0, scale=1, solid=False, pad=None, role="Trim", support=None):
        row = {"name": "BerthDetail/" + name, "asset": mesh["asset"],
               "center": list(center), "size": [v * 2 * scale for v in mesh["extent"]],
               "yaw": yaw, "solid": solid, "role": role, "pad": pad,
               "triangles": mesh["triangles"]}
        if support is not None:
            row["support"] = support
        rows.append(row)
        return row

    floor = get("SM_UniversalPanel400X200_V2")
    service_floor = get("SM_UniversalPanel400X200_V4_BeeCell")
    fascia = get("SM_CeilingWallPanel400X60_V1")
    cable = get("SM_CornerWallFloor400X70_V3_ElectricalCableRouting")
    for pad in PADS:
        name, (cx, cy), radius = pad["name"], pad["center"], pad["radius"]
        # Use the native 2x4m tile spacing and depth. Every tile corner is inside
        # the disc; the continuous existing ring remains exposed at its edge.
        for ix in range(-math.ceil(radius / 200), math.ceil(radius / 200) + 1):
            for iy in range(-math.ceil(radius / 400), math.ceil(radius / 400) + 1):
                x, y = ix * 200, iy * 400
                if math.hypot(abs(x) + 100.05, abs(y) + 200.05) > radius - 85:
                    continue
                mesh = service_floor if abs(y) > radius * .55 and ix % 3 == 0 else floor
                put(f"{name}/Deck {ix:+03}_{iy:+03}", mesh,
                    (cx + x, cy + y, .5 - mesh["extent"][2]), pad=name, role="Deck")
        # Native 4m-long fascia segments are tangent to the circular platform.
        # They overlap slightly at their ends and sit wholly below sole height.
        count = math.ceil(2 * math.pi * (radius - 75) / 380)
        for i in range(count):
            angle = i * 360 / count
            r = math.radians(angle)
            put(f"{name}/Perimeter fascia {i:02}", fascia,
                (cx + (radius - 75) * math.cos(r), cy + (radius - 75) * math.sin(r), -35),
                yaw=angle, pad=name)
            if i % 3 == 1:
                put(f"{name}/Perimeter cable {i:02}", cable,
                    (cx + (radius - 120) * math.cos(r), cy + (radius - 120) * math.sin(r), -112),
                    yaw=angle + 90, pad=name)

    cabinet = get("SM_Cabinet_A", "ModularScifiProps")
    case = get("SM_Props_Box03", "P5_FruitSeller")
    small_case = get("SM_Props_Box04", "P5_FruitSeller")
    ion = get("SM_Props_ConstructionPart35_S3000Serie_IonEnergyStabiliser", "P5_FruitSeller")
    round_ion = get("SM_Props_ConstructionPart36_S3000Serie_IonEnergyStabiliser", "P5_FruitSeller")
    hand_tool = get("SM_Props_ConstructionPart37_S3000Serie_IonEnergyStabiliser", "P5_FruitSeller")
    for name, pad, cx, cy in (
            ("Finish service", "Player", -2350, -1880),
            ("Outer maintenance", "Player", -6000, 1700),
            ("Courier service", "Visitor02", -1580, -4570),
            ("Flanker service", "Visitor03", -1580, 4570)):
        yaw = 90

        def component(suffix, mesh, dx, dy, floor_z=0, scale=1, solid=False):
            # All equipment in this cluster shares its cabinet's orientation.
            put(name + "/" + suffix, mesh,
                (cx - dy, cy + dx, floor_z + mesh["extent"][2] * scale),
                yaw=yaw, scale=scale, solid=solid, pad=pad, role="Service",
                support=0 if floor_z == 0 and solid else None)

        component("Service cabinet", cabinet, 0, 0, solid=True)
        component("Ion unit", ion, -48, 0, 80, .9)
        component("Replacement power core", round_ion, 38, 0, 80, .7)
        component("Calibration tool", hand_tool, 18, -25, 80)
        component("Ground equipment case", case, -135, 0, solid=True)
        component("Case stack", small_case, -135, 0, case["extent"][2] * 2)
        component("Spare case", small_case, 135, 0, solid=True)
        component("Spare hand tool", hand_tool, 138, 0, small_case["extent"][2] * 2)

    post = get("SM_Building_Structure200x10_V1", "P5_FruitSeller")
    foot = get("SM_Building_StructureBase_V1", "P5_FruitSeller")
    brace = get("SM_Building_StructureLink90x10_V1", "P5_FruitSeller")
    for side, cy in (("South", -2150), ("North", 2150)):
        for x in (-1000, -200):
            for i, y in enumerate((cy - 290, cy, cy + 290)):
                put(f"{side} bridge/Post {x}_{i}", post, (x, y, -168), scale=1.3)
                put(f"{side} bridge/Foot {x}_{i}", foot,
                    (x, y, -310), scale=1.3, yaw=90)
            for j, y in enumerate((cy - 200, cy + 200)):
                put(f"{side} bridge/Edge {x}_{j}", fascia, (x, y, -35))
        # Two native structural links span the underside. Surface width and
        # existing 800cm bridge collision are unchanged; no new rail blocks it.
        for x in (-805, -395):
            for y in (cy - 290, cy + 290):
                put(f"{side} bridge/Crossbeam {x}_{y}", brace, (x, y, -80), scale=4.4)
    return rows


def audit(rows):
    """Plan bounds only; does not substitute for Unreal collision/render QA."""
    violations = []
    pad_lookup = {p["name"]: p for p in PADS}
    for row in rows:
        b = bounds(row)
        if row["role"] == "Deck" and (row["solid"] or b[5] > .51):
            violations.append(row["name"] + ": deck must not alter collision/sole height")
        if row["role"] == "Service":
            pad = pad_lookup[row["pad"]]
            cx, cy = pad["center"]
            if any(math.hypot(x - cx, y - cy) > pad["radius"] - 85
                   for x in (b[0], b[3]) for y in (b[1], b[4])):
                violations.append(row["name"] + ": service equipment outside usable disc")
            for name, (x0, y0, x1, y1) in CLEARWAYS:
                if b[3] > x0 and b[0] < x1 and b[4] > y0 and b[1] < y1:
                    violations.append(row["name"] + ": intersects " + name)
        if row["role"] == "Trim" and (row["solid"] or b[5] >= 0):
            violations.append(row["name"] + ": trim must remain below deck/noncolliding")
    return {"geometry_only": True, "rows": len(rows),
            "catalog_render_lod0_triangle_instances": sum(r["triangles"] for r in rows),
            "unique_meshes": len({r["asset"] for r in rows}),
            "solid_props": sum(r["solid"] for r in rows),
            "deck_tiles": {p["name"]: sum(r["role"] == "Deck" and r["pad"] == p["name"] for r in rows) for p in PADS},
            "violations": violations}


def plan_svg(rows):
    """A labelled plan map for independent placement review, not a render."""
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-7450 -5650 9250 11300">',
                '<rect x="-7450" y="-5650" width="9250" height="11300" fill="#0c1720"/>']
    for pad in PADS:
        cx, cy = pad["center"]
        elements.append(f'<circle cx="{cx}" cy="{cy}" r="{pad["radius"]}" fill="#1e3444" stroke="#67d7eb" stroke-width="18"/>')
        elements.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" fill="white" font-size="130">{pad["name"]}</text>')
    for name, (x0, y0, x1, y1) in CLEARWAYS:
        elements.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="#98434d" opacity=".32"><title>{name}</title></rect>')
    for row in rows:
        if row["role"] != "Service":
            continue
        b = bounds(row)
        elements.append(f'<rect x="{b[0]}" y="{b[1]}" width="{b[3]-b[0]}" height="{b[4]-b[1]}" fill="#ffc36a" stroke="#ffe8b1" stroke-width="5"><title>{row["name"]}</title></rect>')
    elements.append('</svg>')
    return "\n".join(elements)


def substrate_tops(rows):
    """Plain discs must sit below the lowest native relief, not obscure it."""
    return {pad["name"]: min(bounds(r)[2] for r in rows
                             if r["role"] == "Deck" and r["pad"] == pad["name"]) - 2
            for pad in PADS}


def lower_visual_substrates(api, rows):
    # Capture6 exposed the former plain disc at Z0 swallowing every recessed
    # panel face. Only lower that exact noncolliding display disc. The hidden
    # Ground/ disc is the unchanged Z0 collision authority; halos/rims stay put.
    labels = {"Player": "Player berth", "Visitor02": "Visitor berth 02",
              "Visitor03": "Visitor berth 03"}
    actors = {a.get_actor_label(): a for a in api["EAS"].get_all_level_actors()}
    receipt = []
    for pad, top in substrate_tops(rows).items():
        name = labels[pad]
        visual, ground = actors[name + "/Deck"], actors["Ground/" + name]
        if visual.static_mesh_component.get_collision_enabled() != api["u"].CollisionEnabled.NO_COLLISION:
            raise ValueError("Refusing to lower a colliding berth substrate: " + name)
        before_ground, ground_extent = ground.get_actor_bounds(False)
        center, extent = visual.get_actor_bounds(False)
        location = visual.get_actor_location()
        previous_top = center.z + extent.z
        location.z += top - previous_top
        visual.set_actor_location(location, False, False)
        for record in api.get("RECORDS", []):
            if record.get("name") == name + "/Deck":
                record["location"] = [location.x, location.y, location.z]
        after, after_extent = visual.get_actor_bounds(False)
        ground_after, extent_after = ground.get_actor_bounds(False)
        assert abs(after.z + after_extent.z - top) < .01
        assert abs(ground_after.z - before_ground.z) < .001
        assert abs(extent_after.z - ground_extent.z) < .001
        assert abs(ground_after.z + extent_after.z) < .01
        receipt.append({"name": name + "/Deck", "previous_top_z": previous_top,
                        "new_top_z": top, "physical_floor_top_z": ground_after.z + extent_after.z})
    return receipt


def build(api):
    root, out = Path(api["ROOT"]), Path(api["OUT"])
    catalog = json.loads(Path(os.environ.get("SS_PREFAB_CATALOG", str(root / "Artifacts/PrefabLibrary/catalog.json"))).read_text(encoding="utf-8"))
    rows = layout(catalog)
    evidence = audit(rows)
    if evidence["violations"]:
        raise ValueError("Berth detail clearance failed: " + "; ".join(evidence["violations"]))
    substrates = lower_visual_substrates(api, rows)
    for row in rows:
        api["place"](row["name"], row["asset"], row["center"], size=row["size"],
                     yaw=row["yaw"], solid=row["solid"], support=row.get("support"))
    receipt = {"audit": evidence, "pads": PADS, "clearways": CLEARWAYS, "placements": rows,
               "visual_substrates": substrates}
    (out / "berth-details.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    (out / "berth-details-plan.svg").write_text(plan_svg(rows), encoding="utf-8")
    return receipt
