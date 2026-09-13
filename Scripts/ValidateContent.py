"""Fresh-editor, read-only persisted asset checks. Does not validate gameplay."""
import hashlib
import json
import math
import runpy
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
BASE = "/Game/SpaceSurvival"


def main():
    library = u.EditorAssetLibrary
    record = {"status": "PERSISTED_ASSETS_VALIDATED_NOT_GAMEPLAY", "engine": u.SystemLibrary.get_engine_version(),
              "meshes": [], "audio": [], "materials": [], "errors": [],
              "limits": ["No gameplay simulation or input validation", "No rendered visual approval", "No audio listening", "No player input or performance verification"]}

    def required(path, cls):
        obj = library.load_asset(path)
        assert obj and isinstance(obj, cls), f"Missing or incorrect class: {path}"
        assert library.get_metadata_tag(obj, "SSAuthoringVersion") == "1", f"Incomplete authoring: {path}"
        return obj

    def checked(label, fn):
        try:
            fn()
        except Exception as error:
            record["errors"].append(f"{label}: {error}")

    meshes = json.loads((ROOT / "ContentSource/Meshes/manifest.json").read_text())
    sounds = json.loads((ROOT / "ContentSource/Audio/manifest.json").read_text())
    mesh_tools = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)

    def validate_material(name):
        material = required(f"{BASE}/Materials/{name}", u.Material)
        if name in ("M_Hull", "M_Gold", "M_Cyan"):
            assert material.get_editor_property("used_with_instanced_static_meshes"), f"{name}: missing station batch usage"
        record["materials"].append(material.get_path_name())

    def validate_panorama():
        source = ROOT / "ContentSource/Textures/SpacePanorama-starless-v2.png"
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        texture = required(BASE + "/Textures/T_SpacePanorama_starless_v2", u.Texture2D)
        material = required(BASE + "/Materials/M_Space", u.Material)
        assert library.get_metadata_tag(texture, "SSPanoramaSourceSHA256") == digest
        assert library.get_metadata_tag(material, "SSPanoramaSourceSHA256") == digest
        assert library.get_metadata_tag(material, "SSPanoramaVersion") == "EquirectangularStarless3"
        assert texture.get_editor_property("srgb")
        assert texture.get_editor_property("compression_settings") == u.TextureCompressionSettings.TC_BC7
        assert texture.get_editor_property("lod_group") == u.TextureGroup.TEXTUREGROUP_SKYBOX
        assert texture.get_editor_property("power_of_two_mode") == u.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO
        assert texture.get_editor_property("mip_gen_settings") == u.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE
        assert texture.get_editor_property("address_x") == u.TextureAddress.TA_WRAP
        assert texture.get_editor_property("address_y") == u.TextureAddress.TA_CLAMP
        assert material.get_editor_property("shading_model") == u.MaterialShadingModel.MSM_UNLIT
        assert material.get_editor_property("two_sided")
        record["space_panorama"] = {"texture": texture.get_path_name(), "source_sha256": digest,
                                    "power_of_two_resampling": "StretchToPowerOfTwo", "mips": "SimpleAverage", "compression": "BC7",
                                    "runtime_seam_and_readability_approval": False}

    def validate_mesh(item):
        mesh = required(f"{BASE}/Meshes/{item['name']}", u.StaticMesh)
        bounds = mesh.get_bounds()
        extent = bounds.box_extent
        dimensions = [extent.x * 2, extent.y * 2, extent.z * 2]
        expected = [item["bounds_cm"][1][i] - item["bounds_cm"][0][i] for i in range(3)]
        assert all(math.isfinite(v) and v > 0 for v in dimensions), f"Invalid bounds: {dimensions}"
        assert all(abs(a-b) <= max(0.02, b*0.00001) for a,b in zip(dimensions, expected)), f"Import changed axes/scale: {dimensions} expected {expected}"
        materials = [slot.get_editor_property("material_interface") for slot in mesh.get_editor_property("static_materials")]
        assert all(materials), "Null material slot"
        assert {m.get_name() for m in materials} == set(item["materials"]), "Lost material groups"
        vertices = mesh_tools.get_number_verts(mesh, 0)
        assert vertices > 0 and mesh_tools.get_lod_count(mesh) >= 1, "No built geometry"
        record["meshes"].append({"name": item["name"], "dimensions_cm": dimensions, "lod0_render_vertices": vertices,
                                 "material_slots": [m.get_name() for m in materials]})

    def validate_hero():
        hero = required(BASE + "/Character/SK_Acornaut", u.SkeletalMesh)
        walk = required(BASE + "/Character/A_Walk", u.AnimSequence)
        skeleton = hero.get_editor_property("skeleton")
        assert skeleton and skeleton == walk.get_editor_property("skeleton"), "Mismatched skeleton"
        duration = walk.get_editor_property("sequence_length")
        assert duration > 0, "Empty animation"
        bounds = hero.get_imported_bounds()
        extent = bounds.box_extent
        materials = [slot.get_editor_property("material_interface") for slot in hero.get_editor_property("materials")]
        assert materials and all(materials), "Null hero materials"
        assert hero.get_editor_property("physics_asset"), "Missing physics asset"
        pilot = required(BASE + "/Character/A_Pilot", u.AnimSequence)
        assert pilot.get_editor_property("skeleton") == skeleton, "Pilot skeleton mismatch"
        assert abs(pilot.get_editor_property("sequence_length")-4.0) < .01, "Pilot duration mismatch"
        exit_clip = required(BASE + "/Character/A_Disembark", u.AnimSequence)
        exit_source = ROOT / "ContentSource/Animation/Disembark.glb"
        exit_manifest = json.loads(exit_source.with_suffix(".json").read_text(encoding="utf-8"))
        exit_hash = hashlib.sha256(exit_source.read_bytes()).hexdigest()
        assert exit_hash == exit_manifest["animation_sha256"], "Disembark source mismatch"
        assert library.get_metadata_tag(exit_clip, "SSDisembarkSourceSHA256") == exit_hash, "Stale disembark import"
        assert library.get_metadata_tag(exit_clip, "SSDisembarkSourceFormat") == "OriginalGLTFBasis1", "Disembark basis mismatch"
        assert exit_clip.get_editor_property("skeleton") == skeleton, "Disembark skeleton mismatch"
        assert abs(exit_clip.get_editor_property("sequence_length") - 2.4) < .01, "Disembark duration mismatch"
        assert not exit_clip.get_editor_property("enable_root_motion"), "Actor owns exit travel"
        assert not exit_clip.get_editor_property("force_root_lock"), "Exit local pelvis track must remain intact"
        record["disembark"] = {"animation": exit_clip.get_path_name(), "seconds": 2.4,
                                "source_sha256": exit_hash, "root_motion": False, "force_root_lock": False}
        pilot_mesh = required(BASE + "/Character/SK_AcornautPilot", u.SkeletalMesh)
        assert pilot_mesh.get_editor_property("skeleton") == skeleton, "Pilot mesh skeleton mismatch"
        pilot_manifest = json.loads((ROOT / "ContentSource/Animation/PilotMesh.json").read_text(encoding="utf-8"))
        assert library.get_metadata_tag(pilot_mesh, "SSPilotMeshSourceSHA256") == pilot_manifest["derivative_sha256"], "Pilot derivative source mismatch"
        source_hash = hashlib.sha256((ROOT / "model-rigged.glb").read_bytes()).hexdigest()
        assert source_hash == "c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91", "Changed supplied GLB"
        record["hero"] = {"mesh": hero.get_path_name(), "animation": walk.get_path_name(), "skeleton": skeleton.get_path_name(),
                          "animation_seconds": duration, "dimensions_cm": [extent.x*2, extent.y*2, extent.z*2],
                          "pilot_animation":pilot.get_path_name(),"pilot_seconds":pilot.get_editor_property("sequence_length"),
                          "materials": [m.get_path_name() for m in materials], "source_sha256": source_hash}

    def validate_sound(item):
        sound = required(f"{BASE}/Audio/{item['name']}", u.SoundWave)
        duration = sound.get_editor_property("duration")
        channels = sound.get_editor_property("num_channels")
        rate = sound.get_editor_property("imported_sample_rate")
        loop = sound.get_editor_property("looping")
        assert abs(duration-item["seconds"]) < .001, f"Duration {duration}"
        assert channels == item["channels"] and rate == item["sample_rate"], f"Wrong format {channels}/{rate}"
        assert loop == item["loop"], "Wrong looping flag"
        record["audio"].append({"name": item["name"], "seconds": duration, "channels": channels, "sample_rate": rate, "loop": loop})

    for name in meshes["palette"]:
        checked(name, lambda name=name: validate_material(name))
    for item in meshes["assets"]:
        checked(item["name"], lambda item=item: validate_mesh(item))
    checked("Station deck material", lambda: runpy.run_path(str(ROOT / "Scripts/ValidateStationDeck.py"), run_name="__main__"))
    checked("Space panorama", validate_panorama)
    checked("Authored Acorn ship", lambda: runpy.run_path(str(ROOT / "Scripts/ValidateAcornShip.py"), run_name="__main__"))
    checked("Preserved hero", validate_hero)
    checked("Reviewed tail repair", lambda: runpy.run_path(str(ROOT / "Scripts/ValidateTailRepair.py"), run_name="__main__"))
    def validate_scene():
        runpy.run_path(str(ROOT / "Scripts/ValidateScene.py"), run_name="__main__")
        data = required(BASE + "/Data/DA_Phase1", u.SSPhase1Data)
        world = required(BASE + "/Maps/Survival", u.World)
        assert world.get_world_settings().get_editor_property("default_game_mode") == u.SSGameMode.static_class(), "Gameplay map class mismatch"
        assert len(data.get_editor_property("hazards")) == 6, "Phase 1 hazard variants mismatch"
        assert len(data.get_editor_property("enemies")) == 2, "Phase 1 enemy roster mismatch"
        assert len(data.get_editor_property("encounters")) == 3, "Phase 1 encounter roster mismatch"
        assert data.has_valid_utility_tuning(), "Malformed Phase 1 utility identity, price or effect tuning"
        record["utilities"] = [{name: (str(entry.get_editor_property(name)) if name == "kind" else entry.get_editor_property(name))
                                for name in ("kind", "price", "maneuver_multiplier", "response_multiplier",
                                             "boost_efficiency", "cooling_efficiency")}
                               for entry in data.get_editor_property("utilities")]
        record["scene"] = {"map": world.get_path_name(), "data": data.get_path_name(), "collision_and_skeletal_material_flags": "validated"}
    checked("Persistent gameplay scene", validate_scene)
    for item in sounds["assets"]:
        checked(item["name"], lambda item=item: validate_sound(item))
    if record["errors"]:
        record["status"] = "FAILED"
    output = ROOT / "Saved/Validation/PersistedContent.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if record["errors"]:
        raise RuntimeError(f"Persisted asset validation failed: {record['errors']}")
    u.log(f"Persisted content validation passed: {len(record['meshes'])} meshes, {len(record['materials'])} materials, preserved hero/walk, {len(record['audio'])} sounds. No gameplay verification.")


if __name__ == "__main__":
    main()
