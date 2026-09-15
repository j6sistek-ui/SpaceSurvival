"""Exercise saved placement -> runtime Blueprint, then remove the test prop.
Run only on the freshly prepared workshop before owner editing. Uses native editor
APIs; writes private receipts/backups and never launches the packaged game.
"""
from pathlib import Path
import json
import hashlib
import importlib.util
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
MAP = "/Game/SpaceSurvival/Licensed/StationWorkshop/L_StationWorkshop"
BP = "/Game/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout"
OUT = ROOT / ".agent/local/StationWorkshop/Validation"
TAG = "StationWorkshopValidationFixture"


def call(name, *args):
    result = getattr(u.SSStationLayoutAuthoringLibrary, name)(*args)
    ok, message = result if isinstance(result, tuple) else (bool(result), str(result))
    assert ok, message
    return message


def export(name):
    path = OUT / (name + ".json")
    call("export_station_workshop", str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    call("open_station_workshop")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    assert not any(TAG in [str(t) for t in a.tags] for a in actors.get_all_level_actors()), "Old validation fixture found."
    palette = [u.load_asset(f"/Game/SpaceSurvival/Licensed/StationWorkshop/Materials/MI_Workshop_{i:02d}")
               for i in range(1, 11)]
    assert all(isinstance(m, u.MaterialInstanceConstant) for m in palette)
    before = export("Before")
    bp_file = ROOT / "Content/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout.uasset"
    original_bp_hash = hashlib.sha256(bp_file.read_bytes()).hexdigest()
    unsupported = actors.spawn_actor_from_class(u.CameraActor, u.Vector())
    try:
        assert u.SSStationLayoutAuthoringLibrary.apply_station_workshop() is None
        assert hashlib.sha256(bp_file.read_bytes()).hexdigest() == original_bp_hash
    finally:
        actors.destroy_actor(unsupported)
    cube = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(500, -450, 175),
                                         u.Rotator(pitch=10, yaw=25, roll=5))
    assert cube
    cube.set_actor_label("WORKSHOP_VALIDATION_TEMPORARY_CUBE")
    cube.tags = [TAG]
    cube.set_actor_scale3d(u.Vector(1.25, .5, 2.0))
    mesh = cube.static_mesh_component
    mesh.set_static_mesh(u.load_asset("/Engine/BasicShapes/Cube"))
    mesh.set_material(0, palette[3])
    mesh.component_tags = [TAG]
    cube.set_actor_scale3d(u.Vector(0, 1, 1))
    assert u.SSStationLayoutAuthoringLibrary.apply_station_workshop() is None
    assert hashlib.sha256(bp_file.read_bytes()).hexdigest() == original_bp_hash
    cube.set_actor_scale3d(u.Vector(1.25, .5, 2.0))
    expected_transform = mesh.get_world_transform()
    try:
        assert levels.save_current_level()
        assert levels.load_level(MAP)
        persisted = [a for a in actors.get_all_level_actors() if TAG in [str(t) for t in a.tags]]
        assert len(persisted) == 1
        cube = persisted[0]
        assert abs(cube.get_actor_scale3d().z - 2.0) < .001
        changed = export("Changed")
        assert len(changed["placements"]) == len(before["placements"]) + 1
        apply_message = call("apply_station_workshop")
        runtime = actors.spawn_actor_from_class(u.EditorAssetLibrary.load_blueprint_class(BP), u.Vector())
        try:
            components = runtime.get_components_by_class(u.StaticMeshComponent)
            found = [c for c in components if TAG in [str(t) for t in c.component_tags]]
            assert len(found) == 1, "Applied prop missing from instantiated station Blueprint."
            target = found[0]
            assert target.get_material(0).get_path_name() == palette[3].get_path_name()
            actual = target.get_world_transform()
            for key, axes in (("translation", "xyz"), ("scale3d", "xyz"), ("rotation", "xyzw")):
                assert all(abs(getattr(getattr(actual, key), axis) -
                               getattr(getattr(expected_transform, key), axis)) < .001 for axis in axes), key
        finally:
            actors.destroy_actor(runtime)
    finally:
        for actor in actors.get_all_level_actors():
            if TAG in [str(t) for t in actor.tags]:
                actors.destroy_actor(actor)
        assert levels.save_current_level()
        restored_message = call("apply_station_workshop")
    after = export("After")
    assert before["placements"] == after["placements"], "Scene changed after removing the test prop."
    private = ROOT / "Content/SpaceSurvival/Licensed/StationWorkshop"
    protected = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in private.rglob("*") if p.is_file()}
    spec = importlib.util.spec_from_file_location("workshop_author", ROOT / "Scripts/AuthorStationWorkshop.py")
    author = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(author)
    author.main()
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest for p, digest in protected.items())
    result = dict(status="PASS", engine=u.SystemLibrary.get_engine_version(), material_presets=len(palette),
                  before_placements=len(before["placements"]), after_placements=len(after["placements"]),
                  checks=["ten materials exist", "unsupported actor rejects apply without changing Blueprint",
                          "zero scale rejects apply without changing Blueprint", "preparation rerun preserves saved map/material bytes", "added rotated/scaled prop survives map save/reopen",
                          "export includes addition", "runtime Blueprint has correct transform and material",
                          "deletion applies", "final exported scene equals initial scene"],
                  apply=apply_message, restored=restored_message,
                  limits="Programmatic editor test; not physical mouse interaction or gameplay acceptance.")
    (OUT / "Result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    u.log("STATION_WORKSHOP_VALIDATION_PASS " + str(OUT / "Result.json"))


if __name__ == "__main__":
    main()
