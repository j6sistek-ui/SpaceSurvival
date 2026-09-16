"""Build three private, genuinely three-dimensional wreck assemblies from owned meshes.

Run in the lead's unattended editor with -ExecutePythonScript. Uses a disposable
unsaved map; never run over an owner's unsaved editing session. Native mesh aspect
ratios and material slots are preserved. No flattening/material bake or vendor save.
UE 5.8 bindings checked against StaticMeshEditorSubsystemHelpers.h,
MeshMergingSettings.h and MeshMergeUtilities.cpp (which adds the SM_ prefix).
"""
import hashlib
import json
import math
from pathlib import Path
import shutil
import uuid

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
BASE = "/Game/SpaceSurvival/Licensed/SpatialAssemblies"
KIT = "/Game/Megastructure_Scifi_World/Meshes"
LIB = u.EditorAssetLibrary
VERSION = "1"


def pillar(number):
    return f"{KIT}/Pillar/SM_architecture_module_{number:02}"


def panel(number):
    return f"{KIT}/Pannels/SM_Pannel_part_{number:02}"


def arch(number):
    return f"{KIT}/Arch/SM_arch_{number:02}"


def recipes():
    """Each tuple is source, bounds-center cm, pitch/yaw/roll degrees, UNIFORM scale.

    Pillars 09/10/13 are volumetric core masses. Zero-thickness vendor panels are
    small attached fins only, never the assembly's wall or principal silhouette.
    Meshes overlap at structural junctions; asymmetric breaks leave exposed ribs.
    """
    spine = [
        (pillar(9), (-2400, -120, -100), (84, -5, 8), 1.45),
        (pillar(13), (-200, 0, 40), (88, 7, -12), 1.55),
        (pillar(10), (2100, 120, -180), (79, -10, 15), 1.3),
        (pillar(12), (-900, 0, 620), (8, 0, 0), 1.45),
        (pillar(12), (1600, 0, -740), (-12, -8, 25), 1.05),
        (pillar(3), (-2600, -1050, 650), (-22, 14, -42), 1.55),
        (pillar(5), (-700, -1200, 700), (-15, 9, -37), 1.35),
        (pillar(4), (1250, -950, 500), (28, 20, -42), 1.45),
        (pillar(3), (-2000, 950, 600), (24, -10, 40), 1.55),
        (pillar(5), (200, 1150, 720), (-18, 15, 48), 1.4),
        (pillar(7), (2400, 800, 850), (24, -7, 26), .8),
        (arch(3), (-1650, 0, 1050), (0, 90, -12), 1.5),
        (arch(4), (650, 100, 1100), (0, 87, 10), 1.65),
        (panel(6), (-1300, -900, 420), (15, 12, -30), 3.2),
        (panel(8), (750, 940, 380), (-20, 5, 38), 3.0),
        (panel(1), (2600, -620, 80), (34, 18, -25), 2.7),
        (pillar(1), (3520, 370, -30), (61, -30, 25), 1.25),
        (pillar(6), (3800, -460, 360), (42, 18, -20), 1.5),
        (pillar(6), (-3700, 580, -430), (-45, 25, 18), 1.55),
        (panel(3), (3380, -820, 250), (17, -22, 15), 2.1),
    ]
    chunk = [
        (pillar(10), (0, 0, -350), (10, 12, 5), 1.7),
        (pillar(9), (-1300, -350, -650), (-18, -14, -8), 1.3),
        (pillar(13), (1000, 470, -260), (27, 35, 13), 1.35),
        (pillar(11), (-480, -1130, 240), (-5, -20, 22), 1.4),
        (pillar(12), (0, 720, 730), (5, -5, 8), 1.2),
        (pillar(7), (-1100, -550, 1420), (-22, 5, -24), 1.05),
        (pillar(5), (720, -550, 1440), (32, 45, 12), 1.5),
        (pillar(3), (1050, 880, 890), (25, -15, 33), 1.75),
        (pillar(4), (-1650, 700, 630), (-34, 14, -29), 1.6),
        (pillar(1), (-900, 1300, -700), (62, 15, 35), 1.85),
        (pillar(2), (900, 1350, -1100), (56, -10, -35), 1.7),
        (pillar(6), (1600, -670, 1270), (12, 32, 45), 2.2),
        (arch(3), (-800, -1220, 650), (6, 12, -10), 1.9),
        (arch(1), (720, 1130, 30), (27, -15, 18), 1.8),
        (panel(6), (-1050, -1000, 1370), (-22, -5, -25), 3.6),
        (panel(9), (600, -1300, 520), (20, -12, 20), 3.3),
        (panel(14), (1200, 950, 400), (22, 20, 28), 2.7),
        (panel(2), (-1650, 450, -350), (35, 45, -20), 2.8),
        (pillar(6), (1950, 400, -1550), (45, -40, 20), 1.7),
        (pillar(1), (-1600, -950, -1680), (62, 10, -20), 1.1),
    ]
    broken_arch = []
    # Partial arch in YZ; deliberately no full ring, square frame or mirrored end caps.
    angles = (-105, -65, -25, 15, 55, 95)
    for index, angle in enumerate(angles):
        theta = math.radians(angle)
        center = ((index % 3 - 1) * 180, 2550 * math.cos(theta), 2550 * math.sin(theta))
        tangent_y, tangent_z = -math.sin(theta), math.cos(theta)
        rotation = (math.degrees(math.asin(tangent_z)), 90 if tangent_y >= 0 else -90, 0)
        broken_arch.append((pillar(12), center, rotation, .82 + .035 * index))
        # Real volumetric buttresses bridge the inside face and create cross-sectional depth.
        inside = (center[0] - 240, center[1] * .83, center[2] * .83)
        broken_arch.append((pillar(8), inside, (angle * .35, 25 * index, angle), 2.0))
    broken_arch += [
        (pillar(10), (-200, -300, -2450), (10, -20, 10), .95),
        (pillar(13), (180, 250, 2500), (-25, 18, 26), .85),
        (arch(3), (-520, 2380, -320), (0, 90, -15), 1.4),
        (arch(4), (540, 1850, 1320), (10, 90, 45), 1.3),
        (panel(6), (-620, 1570, -1580), (-20, 35, -35), 2.6),
        (panel(8), (620, 2100, 830), (35, 45, 25), 2.5),
        (pillar(4), (230, -1070, 2570), (-30, -15, 25), 1.2),
        (pillar(6), (-120, -900, -2910), (35, -25, 15), 1.6),
        (panel(2), (300, -1480, 2590), (-20, 10, 40), 2.4),
    ]
    return {"BrokenHullSpine": spine, "ButtressedChunk": chunk, "FragmentedArch": broken_arch}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_file(path):
    assert path.startswith("/Game/")
    return ROOT / "Content" / (path.removeprefix("/Game/") + ".uasset")


def build(name, parts, actors, merger, output, source_hashes):
    assert 12 <= len(parts) <= 25
    asset_path = BASE + "/SM_" + name
    fingerprint = hashlib.sha256(json.dumps({"version": VERSION, "parts": parts,
                                             "sources": source_hashes}, sort_keys=True).encode()).hexdigest()
    existing = LIB.load_asset(asset_path) if LIB.does_asset_exist(asset_path) else None
    if existing and LIB.get_metadata_tag(existing, "SSAssemblyFingerprint") == fingerprint:
        return {"path": asset_path, "status": "PRESERVED_IDENTICAL", "parts": len(parts), "fingerprint": fingerprint}
    target = package_file(asset_path)
    for suffix in (".uasset", ".uexp", ".ubulk"):
        file = target.with_suffix(suffix)
        if file.exists():
            backup = output / "backups" / file.name
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, backup)
    spawned = []
    inputs = []
    merged_actor = None
    try:
        for index, (source_path, center, rotation, scale) in enumerate(parts):
            mesh = LIB.load_asset(source_path)
            assert isinstance(mesh, u.StaticMesh), source_path
            actor = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(), u.Rotator(*rotation))
            assert actor
            spawned.append(actor)
            actor.set_actor_label(f"SSAssembly_{name}_{index:02}")
            component = actor.static_mesh_component
            component.set_static_mesh(mesh)
            actor.set_actor_scale3d(u.Vector(scale, scale, scale))
            # Recenter transformed import pivots without deforming the source proportions.
            bounds_center, _ = actor.get_actor_bounds(False)
            actor.set_actor_location(u.Vector(*center) - bounds_center, False, False)
            inputs.append({"mesh": source_path, "center_cm": center, "rotation_pitch_yaw_roll": rotation,
                           "uniform_scale": scale,
                           "materials": [str(s.material_interface.get_path_name()) if s.material_interface else None
                                         for s in mesh.get_editor_property("static_materials")]})
        settings = u.MeshMergingSettings()
        for key, value in {"merge_materials": False, "merge_equivalent_materials": False,
                           "merge_physics_data": False, "generate_light_map_uv": False,
                           "lod_selection_type": u.MeshLODSelectionType.SPECIFIC_LOD,
                           "specific_lod": 0, "pivot_type": u.MeshMergePivotType.WORLD_ORIGIN}.items():
            settings.set_editor_property(key, value)
        options = u.MergeStaticMeshActorsOptions()
        options.set_editor_property("base_package_name", BASE + "/" + name)
        options.set_editor_property("destroy_source_actors", False)
        options.set_editor_property("spawn_merged_actor", True)
        options.set_editor_property("new_actor_label", "SSMerged_" + name)
        options.set_editor_property("mesh_merging_settings", settings)
        result = merger.merge_static_mesh_actors(spawned, options)
        if isinstance(result, u.StaticMeshActor):
            merged_actor = result
        elif isinstance(result, tuple):
            merged_actor = next((item for item in result if isinstance(item, u.StaticMeshActor)), None)
        mesh = LIB.load_asset(asset_path)
        assert isinstance(mesh, u.StaticMesh), f"Merge did not create expected mesh: {asset_path}; result={result}"
        materials = [str(s.material_interface.get_path_name()) if s.material_interface else None
                     for s in mesh.get_editor_property("static_materials")]
        source_materials = {path for part in inputs for path in part["materials"] if path}
        assert materials and all(path in source_materials for path in materials), "Merge baked or replaced source materials"
        bounds = mesh.get_bounds()
        dimensions = [bounds.box_extent.x * 2, bounds.box_extent.y * 2, bounds.box_extent.z * 2]
        assert min(dimensions) > 500, f"Assembly unexpectedly flat: {dimensions}"
        LIB.set_metadata_tag(mesh, "SSAssemblyFingerprint", fingerprint)
        LIB.set_metadata_tag(mesh, "SSAssemblyProvenance", "Owned Megastructure_Scifi_World; uniform scale; original materials; no bake")
        assert LIB.save_loaded_asset(mesh, only_if_is_dirty=False)
        return {"path": asset_path, "status": "AUTHORED_NOT_VISUALLY_ACCEPTED", "fingerprint": fingerprint,
                "parts": inputs, "bounds_cm": dimensions, "lod0_vertices": merger.get_number_verts(mesh, 0),
                "materials": materials, "sha256": digest(target)}
    finally:
        for actor in spawned:
            actors.destroy_actor(actor)
        if merged_actor:
            actors.destroy_actor(merged_actor)


def main():
    assert "-unattended" in u.SystemLibrary.get_command_line().lower(), "Use the lead's unattended disposable editor"
    output = ROOT / "Artifacts/WreckAssemblies" / uuid.uuid4().hex
    output.mkdir(parents=True)
    vendor_root = ROOT / "Content/Megastructure_Scifi_World"
    protected = {str(path.relative_to(ROOT)): digest(path) for path in vendor_root.rglob("*") if path.is_file()}
    definitions = recipes()
    sources = {source: digest(package_file(source)) for parts in definitions.values() for source, *_ in parts}
    u.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    merger = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    report = {"engine": u.SystemLibrary.get_engine_version(), "script_sha256": digest(Path(__file__)),
              "status": "AUTHORING_IN_PROGRESS", "source_packages": sources, "assemblies": [],
              "limits": "No visual acceptance, collision gameplay, scene adoption or performance claim. Original materials retained."}
    try:
        for name, parts in definitions.items():
            report["assemblies"].append(build(name, parts, actors, merger, output, sources))
        after = {str(path.relative_to(ROOT)): digest(path) for path in vendor_root.rglob("*") if path.is_file()}
        assert protected == after, "Vendor content changed"
        report["vendor_files_unchanged"] = len(protected)
        report["status"] = "READY_FOR_SCENE_INTEGRATION_AND_RENDERED_REVIEW"
    except Exception as error:
        report["status"] = "FAILED"
        report["error"] = str(error)
        raise
    finally:
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    u.log("WRECK_ASSEMBLIES_AUTHORED " + str(output / "report.json"))


if __name__ == "__main__":
    main()
