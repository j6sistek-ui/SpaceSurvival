"""Bake owned Blueprint layouts into private presentation data, preserving vendor assets.

Run after the Editor build. Backs up the four private packages before changing them.
The native fields are construction-script inputs; their collision and actors do not
enter gameplay. Resolution is an explicit audition setting, not new source detail.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import uuid

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
BASE = "/Game/SpaceSurvival/Licensed/Atmosphere"


def main():
    out = ROOT / "Artifacts/AsteroidDepth" / uuid.uuid4().hex
    out.mkdir(parents=True)
    packages = ["DA_DeepSpaceLook", "T_Region_Skybox_8", "T_Region_Skybox_6", "T_Region_Skybox_1"]
    for name in packages:
        source = ROOT / "Content/SpaceSurvival/Licensed/Atmosphere" / (name + ".uasset")
        shutil.copy2(source, out / source.name)
    def protected():
        return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for folder in ("Asteroid_Library", "SpaceNebulaFantasy")
                for p in (ROOT / "Content" / folder).rglob("*") if p.is_file()}
    before = protected()
    u.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    look = u.load_asset(BASE + "/DA_DeepSpaceLook")
    report = {"layouts": [], "textures": [], "backup": str(out), "status": "REQUIRES_RENDER"}
    names = ("Number of Asteroids", "Number of Clusters", "Asteroid Scale", "Asteroid Scale Variation Fraction",
             "Asteroid Distance", "Asteroids Distance", "Clusters Dispersion", "Arch Degrees", "Arch Radius")
    for kind in ("Arch", "Globular", "Linear"):
        path = "/Game/Asteroid_Library/Blueprints/BP_AsteroidField_" + kind
        actor = actors.spawn_actor_from_class(u.EditorAssetLibrary.load_blueprint_class(path), u.Vector())
        assert actor, path
        controls = {}
        for name in names:
            try:
                controls[name] = str(actor.get_editor_property(name))
            except Exception:
                pass
        centers = []
        for batch in actor.get_components_by_class(u.InstancedStaticMeshComponent):
            origin = batch.get_editor_property("static_mesh").get_bounds().origin
            for index in range(batch.get_instance_count()):
                pose = batch.get_instance_transform(index, world_space=True)
                centers.append(u.MathLibrary.transform_location(pose, origin))
        assert centers
        middle = sum(centers, u.Vector()) / len(centers)
        radius = max((center - middle).length() for center in centers)
        samples = [(center - middle) / radius for center in centers]
        property_name = "asteroid_" + kind.lower() + "_samples"
        existing = look.get_editor_property(property_name)
        if existing:
            samples = existing  # Preserve the authored private composition on ordinary reruns.
        else:
            look.set_editor_property(property_name, samples)
        report["layouts"].append({"blueprint": path, "samples": len(samples), "controls": controls,
                                   "preserved_existing": bool(existing),
                                   "normalization_radius_cm": radius})
        actors.destroy_actor(actor)
    assert u.EditorAssetLibrary.save_loaded_asset(look)
    match = re.search(r"-SSSkyResolution=(2048|4096)\b", u.SystemLibrary.get_command_line())
    resolution = int(match.group(1)) if match else 2048
    for name in packages[1:]:
        texture = u.load_asset(BASE + "/" + name)
        u.AutomationLibrary.finish_loading_before_screenshot()
        row = {"path": texture.get_path_name(), "before_size": str(texture.blueprint_get_built_texture_size()),
               "source_dimensions": str(u.EditorAssetLibrary.find_asset_data(texture.get_path_name()).get_tag_value("Dimensions")),
               "before_bytes": str(texture.blueprint_get_memory_size())}
        texture.set_editor_property("max_texture_size", resolution)
        texture.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_HDR_COMPRESSED)
        assert u.EditorAssetLibrary.save_loaded_asset(texture)
        u.AutomationLibrary.finish_loading_before_screenshot()
        row.update(after_size=str(texture.blueprint_get_built_texture_size()),
                   after_bytes=str(texture.blueprint_get_memory_size()), max_size=resolution,
                   compression="BC6H")
        report["textures"].append(row)
    report["vendor_unchanged"] = before == protected()
    assert report["vendor_unchanged"]
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out.parent / "latest.json").write_text(json.dumps({"root": str(out)}), encoding="utf-8")
    u.log("ASTEROID_DEPTH_AUTHORED_REQUIRES_RENDER")


if __name__ == "__main__":
    main()
