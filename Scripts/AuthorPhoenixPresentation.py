"""Create a private presentation-only derivative of the supplied Phoenix Blueprint.

Run in the owner's installed Unreal editor commandlet with -NullRHI or -RenderOffscreen.
Default is inspection only. Pass -SSApplyPhoenixPresentation to create the derivative.
The source Blueprint and animation are never saved. Existing outputs are accepted only
when their bytes match this script's previous ownership receipt; unknown edits stop the run.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Artifacts" / "PhoenixPresentation"
RECEIPT = OUT / "author.json"
SOURCE = "/Game/Stellar_Phoenix/Spaceship/BP/BP_Spaceship"
SOURCE_CLIP = "/Game/Stellar_Phoenix/Spaceship/Animation/AirBrake"
BASE = "/Game/SpaceSurvival/Licensed/PhoenixPresentation"
TARGET = BASE + "/BP_PhoenixPresentation"
TARGET_CLIP = BASE + "/AirBrake"
APPLY = "-SSApplyPhoenixPresentation" in u.SystemLibrary.get_command_line() or "--apply" in sys.argv
LIB = u.EditorAssetLibrary
BP = u.BlueprintEditorLibrary
REVISION = 2


def disk_path(package):
    assert package.startswith("/Game/")
    return ROOT / "Content" / (package[6:] + ".uasset")


def digest(package):
    path = disk_path(package)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def save_receipt(receipt):
    OUT.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def name(obj):
    return obj.get_name().removesuffix("_GEN_VARIABLE") if obj else None


def components(blueprint):
    subsystem = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    lib = u.SubobjectDataBlueprintFunctionLibrary
    result = []
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
        data = lib.get_data(handle)
        obj = lib.get_associated_object(data)
        if not isinstance(obj, u.ActorComponent):
            continue
        parent_handle = lib.get_parent_handle(data)
        parent = lib.get_associated_object(lib.get_data(parent_handle)) if lib.is_handle_valid(parent_handle) else None
        result.append((obj, parent))
    # The subsystem may expose the same SCS template through more than one handle.
    return list({name(obj): (obj, parent) for obj, parent in result}.values())


def signature(blueprint):
    records = []
    for obj, parent in components(blueprint):
        record = {"name": name(obj), "class": obj.get_class().get_name(),
                  "parent": name(parent) if isinstance(parent, u.ActorComponent) else "@root"}
        if isinstance(obj, u.SceneComponent):
            for field, axes in (("relative_location", "xyz"), ("relative_scale3d", "xyz"),
                                ("relative_rotation", ("pitch", "yaw", "roll"))):
                value = obj.get_editor_property(field)
                record[field] = [round(float(getattr(value, axis)), 6) for axis in axes]
            record["socket"] = str(obj.get_attach_socket_name())
        if isinstance(obj, u.StaticMeshComponent):
            mesh = obj.get_editor_property("static_mesh")
            record["mesh"] = mesh.get_path_name() if mesh else None
        elif isinstance(obj, u.SkeletalMeshComponent):
            mesh = obj.get_skeletal_mesh_asset()
            record["mesh"] = mesh.get_path_name() if mesh else None
        records.append(record)
    return sorted(records, key=lambda record: record["name"])


def clip_data(clip):
    model = clip.get_editor_property("data_model_interface")
    assert model, "Animation data model unavailable"
    tracks = model.get_bone_track_names()
    assert model.get_num_bone_tracks() and tracks, "AirBrake has no authored bone tracks"
    # Engine load repairs the old 21-key metadata into a 49-frame/50-key sequencer model. Public
    # interface methods expose that corrected state; the old raw-track API intentionally returns [].
    samples = []
    for bone in tracks:
        for fraction in (0., .5, 1.):
            pose = u.AnimationLibrary.get_bone_pose_for_time(clip, bone, model.get_play_length() * fraction, False)
            samples.append([str(bone), fraction] + [round(float(value), 6) for value in (
                pose.translation.x, pose.translation.y, pose.translation.z, pose.rotation.x,
                pose.rotation.y, pose.rotation.z, pose.rotation.w, pose.scale3d.x, pose.scale3d.y, pose.scale3d.z)])
    rate = model.get_frame_rate()
    return model, {"frames": model.get_number_of_frames(), "keys": model.get_number_of_keys(),
                   "duration": model.get_play_length(),
                   "frame_rate": [rate.numerator, rate.denominator], "tracks": model.get_num_bone_tracks(),
                   "bone_names": [str(bone) for bone in tracks], "model_class": model.get_class().get_name(),
                   "sampled_pose_sha256": hashlib.sha256(json.dumps(samples).encode("utf-8")).hexdigest()}


def derivative_clip(source_clip):
    _, source_data = clip_data(source_clip)
    clip = u.load_asset(TARGET_CLIP) if LIB.does_asset_exist(TARGET_CLIP) else LIB.duplicate_asset(SOURCE_CLIP, TARGET_CLIP)
    assert clip, "Could not create private AirBrake derivative"
    _, after = clip_data(clip)
    assert after == source_data, "Private AirBrake clone changed the repaired source data or sampled poses"
    assert after["keys"] == after["frames"] + 1, "AirBrake frame/key count remains inconsistent"
    assert LIB.save_loaded_asset(clip, only_if_is_dirty=False), "AirBrake derivative save failed"
    return clip, {"source_after_engine_load": source_data, "saved_derivative": after}


def main():
    original = {package: digest(package) for package in (SOURCE, SOURCE_CLIP)}
    assert all(original.values()), "Required licensed source assets are not installed"
    prior = json.loads(RECEIPT.read_text(encoding="utf-8")) if RECEIPT.is_file() else None
    for package in (TARGET, TARGET_CLIP):
        current = digest(package)
        if current:
            assert prior and prior.get("outputs", {}).get(package) == current, "Refusing unrecognized or edited derivative: " + package
            assert prior.get("source_sha256") == original, "Source assets changed; review before replacing the existing derivative"
    receipt = {"utc": datetime.now(timezone.utc).isoformat(), "mode": "apply" if APPLY else "dry-run", "revision": REVISION,
               "status": "inspecting", "source_sha256": original, "outputs": {}, "source_preserved": False}
    try:
        source = u.load_asset(SOURCE)
        assert source, "Could not inspect supplied Blueprint"
        source_signature = signature(source)
        assert source_signature, "Supplied Blueprint has no component hierarchy"
        receipt["source_components"] = source_signature
        receipt["source_graphs"] = [graph.get_name() for graph in BP.list_graphs(source)]
        source_clip = u.load_asset(SOURCE_CLIP)
        _, receipt["source_airbrake"] = clip_data(source_clip)
        if not APPLY:
            receipt["status"] = "dry-run"
            print("PHOENIX_PRESENTATION_DRY_RUN " + json.dumps({"components": len(source_signature),
                  "graphs_to_remove": receipt["source_graphs"], "airbrake": receipt["source_airbrake"]}))
            return
        if prior and prior.get("status") == "complete" and prior.get("revision") == REVISION:
            existing = u.load_asset(TARGET)
            assert signature(existing) == source_signature, "Existing derivative hierarchy changed"
            assert not BP.list_graphs(existing), "Existing derivative contains a gameplay graph"
            receipt.update({key: value for key, value in prior.items() if key not in
                            ("utc", "mode", "outputs", "source_preserved")})
            receipt["status"] = "complete"
            receipt["idempotent_existing"] = True
            return
        clip, receipt["airbrake_repair"] = derivative_clip(source_clip)
        target = u.load_asset(TARGET) if LIB.does_asset_exist(TARGET) else LIB.duplicate_asset(SOURCE, TARGET)
        assert target, "Could not duplicate supplied Blueprint"
        # RemoveUnusedVariables intentionally excludes multicast delegates. The supplied OnExited
        # dispatcher belongs to its demo occupant graph, so remove dispatchers explicitly as well.
        receipt["removed_demo_dispatchers"] = [str(value) for value in BP.list_event_dispatchers(target)]
        for dispatcher in list(BP.list_event_dispatchers(target)):
            assert BP.remove_event_dispatcher(target, dispatcher), "Could not remove demo dispatcher " + str(dispatcher)
        for graph in list(BP.list_graphs(target)):
            BP.remove_graph(target, graph)
        # Graph-independent demo fields include invalid Occupant types. They are not presentation
        # data: deleting NewVariables retains the independently owned SCS component variables.
        receipt["removed_demo_variables"] = BP.remove_unused_variables(target)
        receipt["runtime_safety_overrides"] = []
        # These explicit gameplay defaults are intentionally outside the visual hierarchy signature.
        # Apply them to SCS templates before actor construction so a deferred spawn never briefly
        # initializes vendor physics, auto-playing audio, or its force-producing thruster.
        for obj, _ in components(target):
            obj.set_editor_property("auto_activate", False)
            if isinstance(obj, u.PrimitiveComponent):
                body = obj.get_editor_property("body_instance")
                body.set_editor_property("simulate_physics", False)
                body.set_editor_property("enable_gravity", False)
                obj.set_editor_property("body_instance", body)
                obj.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
                obj.set_editor_property("generate_overlap_events", False)
            receipt["runtime_safety_overrides"].append(name(obj))
            if isinstance(obj, u.SkeletalMeshComponent):
                animation = obj.get_editor_property("animation_data")
                old = animation.get_editor_property("anim_to_play")
                if old and old.get_path_name().split(".")[0] == SOURCE_CLIP:
                    animation.set_editor_property("anim_to_play", clip)
                    obj.set_editor_property("animation_data", animation)
        assert BP.compile_blueprint(target), "Presentation Blueprint compilation failed"
        assert not BP.list_graphs(target), "Demo graphs remain in presentation Blueprint"
        receipt["remaining_member_names"] = [str(value) for value in BP.list_member_variable_names(target, False)]
        component_names = {record["name"].casefold() for record in source_signature}
        receipt["remaining_noncomponent_members"] = [value for value in receipt["remaining_member_names"]
                                                      if value.casefold() not in component_names]
        assert not receipt["remaining_noncomponent_members"], "Demo variables remain: " + str(receipt["remaining_noncomponent_members"])
        actual_signature = signature(target)
        assert actual_signature == source_signature, "Supplied component hierarchy changed while removing demo logic"
        assert LIB.save_loaded_asset(target, only_if_is_dirty=False), "Presentation Blueprint save failed"
        receipt["components"] = actual_signature
        receipt["blueprint_compiled"] = True
        receipt["status"] = "complete"
        print("PHOENIX_PRESENTATION_COMPLETE " + json.dumps({"target": TARGET, "components": len(actual_signature)}))
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error"] = str(error)
        raise
    finally:
        receipt["source_preserved"] = original == {package: digest(package) for package in original}
        receipt["outputs"] = {package: digest(package) for package in (TARGET, TARGET_CLIP)}
        # Dry runs never replace the ownership receipt required to identify existing generated outputs.
        if APPLY:
            save_receipt(receipt)
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / "dry-run.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        assert receipt["source_preserved"], "Original licensed source bytes changed"


main()
