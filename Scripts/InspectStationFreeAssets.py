"""Read-only mounted robot/electronics audit. Integration lead schedules Unreal.

No vendor assets, examples, Blueprint defaults, maps or animations are saved.
"""
import json
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
ROBOT = "/Game/Robot_scout_R_21/Mesh/SK_Robot_scout_R21"
ANIMATIONS = "/Game/Robot_scout_R_21/Demo/Animations"
PROPS = "/Game/Defect/StaticMeshes/Props"


def vector(value):
    return [value.x, value.y, value.z]


def bound_row(mesh):
    bounds = mesh.get_bounds()
    return dict(origin_cm=vector(bounds.origin), extent_cm=vector(bounds.box_extent),
                radius_cm=bounds.sphere_radius)


def material_paths(slots):
    return [slot.material_interface.get_path_name() if slot.material_interface else None for slot in slots]


def optional(read):
    try:
        return read()
    except Exception as exc:
        return dict(status="UNKNOWN", reason=str(exc))


def main():
    lib = u.EditorAssetLibrary
    report = dict(engine=u.SystemLibrary.get_engine_version(),
                  status="READ_ONLY_ASSET_INSPECTION_NOT_RENDER_OR_ANIMATION_ACCEPTANCE")
    robot = lib.load_asset(ROBOT)
    assert isinstance(robot, u.SkeletalMesh), "Completed Robot scout R21 pack is not mounted"
    skeleton = robot.get_editor_property("skeleton")
    report["robot"] = dict(path=robot.get_path_name(), **bound_row(robot),
                           skeleton=skeleton.get_path_name() if skeleton else None,
                           materials=material_paths(robot.get_editor_property("materials")),
                           lod_count=optional(lambda: u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem).get_lod_count(robot)))
    report["animations"] = []
    for path in sorted(lib.list_assets(ANIMATIONS, recursive=True, include_folder=False)):
        clip = lib.load_asset(path)
        if not isinstance(clip, u.AnimSequence):
            continue
        clip_skeleton = clip.get_editor_property("skeleton")
        report["animations"].append(dict(path=clip.get_path_name(),
            seconds=optional(lambda: clip.get_editor_property("sequence_length")),
            skeleton=clip_skeleton.get_path_name() if clip_skeleton else None,
            matches_robot_skeleton=clip_skeleton == skeleton,
            enable_root_motion=optional(lambda: clip.get_editor_property("enable_root_motion"))))
    report["props"] = []
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    for path in sorted(lib.list_assets(PROPS, recursive=True, include_folder=False)):
        mesh = lib.load_asset(path)
        if not isinstance(mesh, u.StaticMesh):
            continue
        report["props"].append(dict(path=mesh.get_path_name(), **bound_row(mesh),
            lod_count=optional(lambda: editor.get_lod_count(mesh)), materials=material_paths(mesh.static_materials)))
    assert report["props"], "Completed Defect electronics pack is not mounted"
    out = ROOT / ".agent/local/StationVisualPass"
    out.mkdir(parents=True, exist_ok=True)
    (out / "FreeAssetInspection.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    u.log("STATION_FREE_ASSETS_INSPECTED "+json.dumps(report))


if __name__ == "__main__":
    main()
