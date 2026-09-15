"""Validate the owned audio, character, drone and builder-visible asset pass."""
from pathlib import Path
import json
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".agent/local/OwnedAssetIntegration"
AUDIO = ("Engine", "Laser", "Cannon", "Impact", "Pickup", "Alarm", "Station",
         "EnemyFire", "EnemyBreak", "DebrisBreak")
CHARACTERS = (
    "/Game/SciFITrooper_Man_03/SkeletalMesh/SK_SciFITrooper_Man_03",
    "/Game/SciFITrooper_Man_03/DemoContent/Anims/ThirdPersonWalk",
    "/Game/SciFITrooper_Man_03/DemoContent/Anims/ThirdPersonJump_End",
    "/Game/Heavy_space_trooper/character/mesh/Heavy_space_trooper_A_Pose",
    "/Game/Heavy_space_trooper/Demo/animations/ThirdPersonIdle",
)


def required(path, kind=None):
    asset = u.EditorAssetLibrary.load_asset(path)
    if not asset or (kind and not isinstance(asset, kind)):
        raise RuntimeError("Missing or incorrect asset: " + path)
    return asset


def main():
    audio = []
    for name in AUDIO:
        sound = required(f"/Game/SpaceSurvival/Licensed/Audio/{name}", u.SoundWave)
        audio.append({"name": name, "looping": bool(sound.get_editor_property("looping")),
                      "duration": sound.get_editor_property("duration")})
    if not next(row for row in audio if row["name"] == "Engine")["looping"]:
        raise RuntimeError("Engine sound must loop")
    if not next(row for row in audio if row["name"] == "Station")["looping"]:
        raise RuntimeError("Station ambience must loop")

    hero = required(CHARACTERS[0], u.SkeletalMesh)
    walk = required(CHARACTERS[1], u.AnimSequence)
    jump = required(CHARACTERS[2], u.AnimSequence)
    heavy = required(CHARACTERS[3], u.SkeletalMesh)
    heavy_idle = required(CHARACTERS[4], u.AnimSequence)
    if hero.get_editor_property("skeleton") != walk.get_editor_property("skeleton") or \
            hero.get_editor_property("skeleton") != jump.get_editor_property("skeleton"):
        raise RuntimeError("Temporary hero animation skeleton mismatch")
    if heavy.get_editor_property("skeleton") != heavy_idle.get_editor_property("skeleton"):
        raise RuntimeError("Heavy station trooper animation skeleton mismatch")
    drone = required("/Game/SpaceSurvival/Licensed/StationAssets/Drone/SK_StationDrone", u.SkeletalMesh)
    drone_idle = required("/Game/SpaceSurvival/Licensed/StationAssets/Drone/A_DroneIdle", u.AnimSequence)
    if drone.get_editor_property("skeleton") != drone_idle.get_editor_property("skeleton"):
        raise RuntimeError("Station drone animation skeleton mismatch")

    label = required("/Game/SpaceSurvival/Licensed/OwnedCharacters/DA_OwnedCharacterCook")
    explicit = [asset.get_path_name().split(".")[0] for asset in label.get_editor_property("ExplicitAssets")]
    if explicit != list(CHARACTERS):
        raise RuntimeError("Owned-character cook label differs from runtime asset set")

    registry = u.AssetRegistryHelpers.get_asset_registry()
    classes = {"StaticMesh", "SkeletalMesh", "NiagaraSystem"}
    placeables = []
    added = {"SciFITrooper_Man_03": 0, "Heavy_space_trooper": 0, "CosmicMaterial": 0,
             "StationDrone": 0}
    game_assets = registry.get_assets_by_path("/Game", recursive=True, include_only_on_disk_assets=True)
    engine_shapes = registry.get_assets_by_path(
        "/Engine/BasicShapes", recursive=True, include_only_on_disk_assets=True)
    for data in game_assets:
        if str(data.asset_class_path.asset_name) not in classes:
            continue
        path = str(data.package_name)
        placeables.append(path)
        if path.startswith("/Game/SciFITrooper_Man_03/"):
            added["SciFITrooper_Man_03"] += 1
        elif path.startswith("/Game/Heavy_space_trooper/"):
            added["Heavy_space_trooper"] += 1
        elif path.startswith("/Game/CosmicMaterial/"):
            added["CosmicMaterial"] += 1
        elif path.startswith("/Game/SpaceSurvival/Licensed/StationAssets/Drone/"):
            added["StationDrone"] += 1
    for name in ("SciFITrooper_Man_03", "Heavy_space_trooper", "StationDrone"):
        if added[name] < 1:
            raise RuntimeError(name + " added no builder-placeable asset")

    result = {"status": "OWNED_ASSET_PASS_STATIC_VALIDATION_PASS",
              "engine": u.SystemLibrary.get_engine_version(), "audio": audio,
              "character_assets": list(CHARACTERS), "cook_label": label.get_path_name(),
              "builder_placeables_game": len(placeables),
              "builder_placeables_engine_basic_shapes": sum(
                  str(data.asset_class_path.asset_name) in classes for data in engine_shapes),
              "builder_placeables_total": len(placeables) + sum(
                  str(data.asset_class_path.asset_name) in classes for data in engine_shapes),
              "new_root_placeables": added,
              "cosmic_material_note": "Materials remain selectable in Content Browser/Details; presets stay bounded."}
    (PRIVATE / "Validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    u.log("OWNED_ASSET_VALIDATION " + json.dumps(result))


if __name__ == "__main__":
    main()
