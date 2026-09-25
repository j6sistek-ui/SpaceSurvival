"""Pure recipes for complete, source-backed building-library assemblies.

No Unreal import, map operation or asset write occurs here. ``recipes`` consumes
the native survey (its ``assets`` list, or the list itself) and reads the two
existing outpost source manifests. Locations are in centimetres, rotations are
Unreal's (pitch, yaw, roll), and each source scale/material override is retained.
The caller may normalize the entire assembly pivot after creating its parts.
"""

import json
from pathlib import Path


_BUNDLE = "/Game/P1toP5_Bundle/"
_GENESIS = _BUNDLE + "P4_Genesis_Vol1/Meshes/"
_COMPUTER = _BUNDLE + "P3_ComputerStation/Meshes/"
_SCREEN_MATERIALS = (
    "P1toP5_Bundle/P4_Genesis_Vol1/Materials/Instances/Translucent"
)
_ADVERTS = (
    "Graph1", "Graph2", "RobotAdvertisment", "KeosAdvertisment",
    "CosmoAdvertisment", "DigitalPanel",
)


def _object(package):
    """Return a native object path without altering the vendor package root."""
    return package if "." in package.rsplit("/", 1)[-1] else (
        package + "." + package.rsplit("/", 1)[-1]
    )


def _part(name, asset, location=(0, 0, 0), rotation=(0, 0, 0),
          scale=(1, 1, 1), materials=None, solid=None):
    result = {
        "name": name, "asset": _object(asset), "location": list(location),
        "rotation": list(rotation), "scale": list(scale),
    }
    if materials is not None:
        result["materials"] = list(materials)
    if solid is not None:
        result["solid"] = solid
    return result


def _native_part(record, anchor):
    """Remove one source anchor; preserve all relative geometry and overrides."""
    asset = record["asset"]
    solid = (
        "IndustryStation_V1_Part1" in asset
        or "IndustrySeat_V1_Part1" in asset
        or "IndustrySeat_V1_Part2" in asset
        or ("Storage3000Series" in asset and "_Part1." in asset)
    )
    return _part(
        record["name"], asset,
        [record["location"][axis] - anchor[axis] for axis in range(3)],
        record["rotation"], record["scale"], record["materials"], solid,
    )


def recipes(project_root, inventory):
    """Return 41 complete recipes when the requested native sources are present.

    Missing assets fail explicitly instead of returning incomplete assemblies.
    Material variants change only the digital pane's material; they never add
    a second coincident pane. The five heights-200 digital frames use V2_Part1
    where supplied; other digital windows retain their matching V1 frame.
    """
    root = Path(project_root)
    rows = inventory["assets"] if isinstance(inventory, dict) else inventory
    available = {
        _object(row["asset"])
        for row in rows if row.get("class") == "StaticMesh"
    }
    result = []

    def append(name, category, parts, source):
        missing = sorted({part["asset"] for part in parts} - available)
        if missing:
            raise ValueError(name + " requires native StaticMesh assets: "
                             + ", ".join(missing))
        if len({part["name"] for part in parts}) != len(parts):
            raise ValueError(name + " has duplicate source component names")
        result.append({"name": name, "category": category, "parts": parts,
                       "source": source})

    def window_parts(width, height, digital=False, materials=None):
        stem = "SM_Window" + str(width) + "X" + str(height)
        frame = _GENESIS + stem + "_V1_Part1"
        if digital:
            digital_frame = _GENESIS + stem + "_V2_Part1"
            if _object(digital_frame) in available:
                frame = digital_frame
            pane = _GENESIS + stem + "_V2_Part2_DigitalWindow"
        else:
            pane = _GENESIS + stem + "_V1_Part2"
        return [
            _part("Frame", frame, solid=True),
            _part("DigitalPane" if digital else "GlassPane", pane,
                  materials=materials, solid=False),
        ]

    for width in (200, 300, 400, 500, 600):
        for height in (100, 200, 250):
            dimensions = str(width) + "x" + str(height)
            for digital, label in ((False, "Glass"), (True, "Digital")):
                append(
                    "Genesis_Window_" + dimensions + "_" + label,
                    "Windows", window_parts(width, height, digital),
                    "Genesis native matched frame/pane, common source pivot; "
                    + dimensions + " cm; original mesh materials",
                )

    for advert in _ADVERTS:
        name = "MI_DigitalGlass_Window400X200_" + advert
        material_file = root / "Content" / _SCREEN_MATERIALS / (name + ".uasset")
        if not material_file.is_file():
            raise FileNotFoundError("Native screen material missing: "
                                    + str(material_file))
        material = _object("/Game/" + material_file.relative_to(
            root / "Content").with_suffix("").as_posix())
        append(
            "Genesis_Screen_400x200_" + advert, "Screens",
            window_parts(400, 200, True, [material, material]),
            "Native Genesis 400x200 digital frame/pane; " + material,
        )

    assets_path = root / "Scripts" / "OutpostAssets.json"
    asset_data = json.loads(assets_path.read_text(encoding="utf-8"))
    workstation = []
    for row in asset_data["workstation"]["parts"]:
        workstation.append(_part(
            row["name"], row["asset"], row["location_cm"],
            [row.get("pitch_deg", 0), row["yaw_deg"], row.get("roll_deg", 0)],
            row.get("scale_xyz", [1, 1, 1]), row.get("default_materials", []),
            not any(token in row["name"]
                    for token in ("Screen", "Cable", "Light", "WorkPlan")),
        ))
    append("Goliath_CompleteWorkstation", "Workstations", workstation,
           "Scripts/OutpostAssets.json#workstation.parts; exact source transforms "
           "and default_materials, including the supplied material variants")

    interiors_path = root / "Scripts" / "OutpostInteriorAssemblies.json"
    interiors = json.loads(interiors_path.read_text(encoding="utf-8"))
    actors = interiors["actors"]
    by_name = {record["name"]: record for record in actors}
    if len(by_name) != len(actors):
        raise ValueError("Interior source actors have duplicate names")

    def selected(names):
        wanted = set(names)
        missing = wanted - set(by_name)
        if missing:
            raise ValueError("Interior source actors missing: "
                             + ", ".join(sorted(missing)))
        return [row for row in actors if row["name"] in wanted]

    for name, category, source_rows, anchor_key in (
        ("P3_CompleteConsoleAndChair", "Workstations",
         selected(interiors["console_names"]), "console_anchor"),
        ("P3_CompleteChair", "Chairs",
         selected(interiors["chair_names"]), "chair_anchor"),
        ("P3_CompleteComputerBank", "Workstations", actors, "bank_anchor"),
    ):
        append(
            name, category,
            [_native_part(row, interiors[anchor_key]) for row in source_rows],
            "Scripts/OutpostInteriorAssemblies.json; " + interiors["source_map"]
            + "; original actor transforms and material overrides relative to "
            + anchor_key,
        )

    # Exact three screen actors from the first authored console. Actor labels
    # differ from mesh names: Part2 uses mesh Part1 and Part4 uses mesh Part2.
    # Retain the native middle/top tilt instead of guessing common rotations.
    screen_names = (
        "SM_SciFiScreen_V1_Part2", "SM_SciFiScreen_V1_Part4",
        "SM_SciFiScreen_V1_Part3",
    )
    screen_rows = selected(screen_names)
    expected_meshes = {
        _object(_COMPUTER + "SM_SciFiScreen_V1_Part" + str(index))
        for index in (1, 2, 3)
    }
    if {row["asset"] for row in screen_rows} != expected_meshes:
        raise ValueError("Native console screen source membership changed")
    screen_anchor = by_name[screen_names[0]]["location"]
    append(
        "P3_CompleteThreePartScreen", "Screens",
        [_native_part(row, screen_anchor) for row in screen_rows],
        "Scripts/OutpostInteriorAssemblies.json; first console's three screen "
        "actors, base anchor, original middle/top tilt and material overrides",
    )
    return result
