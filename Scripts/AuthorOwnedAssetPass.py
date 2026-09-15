"""Import the curated audio palette and animated station drone in UE5.8.

Run after PrepareOwnedAssetPass.py. Existing private assets are verified and
preserved; source downloads and vendor packages are never edited.
"""
from pathlib import Path
import hashlib
import json
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".agent/local/OwnedAssetIntegration"
AUDIO_DEST = "/Game/SpaceSurvival/Licensed/Audio"
DRONE_DEST = "/Game/SpaceSurvival/Licensed/StationAssets/Drone"
COOK_ASSETS = (
    "/Game/SciFITrooper_Man_03/SkeletalMesh/SK_SciFITrooper_Man_03",
    "/Game/SciFITrooper_Man_03/DemoContent/Anims/ThirdPersonWalk",
    "/Game/SciFITrooper_Man_03/DemoContent/Anims/ThirdPersonJump_End",
    "/Game/Heavy_space_trooper/character/mesh/Heavy_space_trooper_A_Pose",
    "/Game/Heavy_space_trooper/Demo/animations/ThirdPersonIdle",
)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(asset) -> None:
    if not u.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError("Could not save " + asset.get_path_name())


def import_audio(preparation: dict) -> list[dict]:
    library = u.EditorAssetLibrary
    tools = u.AssetToolsHelpers.get_asset_tools()
    library.make_directory(AUDIO_DEST)
    rows = []
    for name, record in preparation["audio"].items():
        source = ROOT / record["wav"]
        if sha(source) != record["wav_sha256"]:
            raise RuntimeError(f"Prepared audio changed: {source}")
        path = f"{AUDIO_DEST}/{name}"
        sound = library.load_asset(path) if library.does_asset_exist(path) else None
        if not sound:
            task = u.AssetImportTask()
            for key, value in {"filename": str(source), "destination_path": AUDIO_DEST,
                               "destination_name": name, "automated": True,
                               "replace_existing": False, "save": False}.items():
                task.set_editor_property(key, value)
            tools.import_asset_tasks([task])
            sound = library.load_asset(path)
        if not isinstance(sound, u.SoundWave):
            raise RuntimeError(f"Expected SoundWave at {path}")
        existing = library.get_metadata_tag(sound, "SSOwnedSourceSHA256")
        if existing and existing != record["wav_sha256"]:
            raise RuntimeError(f"Existing licensed audio differs: {path}")
        sound.set_editor_property("looping", bool(record["loop"]))
        if record["loop"]:
            sound.set_editor_property("virtualization_mode", u.VirtualizationMode.PLAY_WHEN_SILENT)
        library.set_metadata_tag(sound, "SSOwnedSourceSHA256", record["wav_sha256"])
        save(sound)
        rows.append({"role": name, "asset": sound.get_path_name(), "loop": bool(record["loop"]),
                     "duration": sound.get_editor_property("duration")})
    return rows


def import_drone(preparation: dict) -> dict:
    library = u.EditorAssetLibrary
    mesh_path = DRONE_DEST + "/SK_StationDrone"
    idle_path = DRONE_DEST + "/A_DroneIdle"
    source = ROOT / preparation["drone"]["copy"]
    source_sha = preparation["drone"]["copy_sha256"]
    if sha(source) != source_sha:
        raise RuntimeError("Prepared drone source changed")
    if library.does_asset_exist(mesh_path) and library.does_asset_exist(idle_path):
        mesh, idle = library.load_asset(mesh_path), library.load_asset(idle_path)
        if library.get_metadata_tag(mesh, "SSOwnedSourceSHA256") != source_sha:
            raise RuntimeError("Existing station drone differs from prepared source")
        return {"mesh": mesh.get_path_name(), "idle": idle.get_path_name(), "reused": True}
    if library.does_asset_exist(mesh_path) or library.does_asset_exist(idle_path):
        raise RuntimeError("Partial station drone import exists; reconcile it before rerun")

    library.make_directory(DRONE_DEST)
    pipeline_path = DRONE_DEST + "/P_StationDroneImport"
    if not library.does_asset_exist(pipeline_path):
        if not library.duplicate_asset("/Interchange/Pipelines/DefaultAssetsPipeline", pipeline_path):
            raise RuntimeError("Could not create private drone import pipeline")
    pipeline = library.load_asset(pipeline_path)
    pipeline.set_editor_property("asset_type_sub_folders", False)
    pipeline.set_editor_property("scene_name_sub_folder", False)
    pipeline.set_editor_property("use_source_name_for_asset", False)
    mesh_settings = pipeline.get_editor_property("mesh_pipeline")
    mesh_settings.set_editor_property("import_skeletal_meshes", True)
    mesh_settings.set_editor_property("import_static_meshes", False)
    mesh_settings.set_editor_property("combine_skeletal_meshes_behavior",
                                      u.InterchangeCombineSkeletalMeshesBehavior.BY_SKELETON)
    mesh_settings.set_editor_property("create_physics_asset", False)
    pipeline.get_editor_property("animation_pipeline").set_editor_property("import_animations", True)
    save(pipeline)
    manager = u.InterchangeManager.get_interchange_manager_scripted()
    params = u.ImportAssetParameters()
    params.set_editor_property("is_automated", True)
    params.set_editor_property("replace_existing", False)
    params.set_editor_property("override_pipelines", [u.SoftObjectPath(pipeline.get_path_name())])
    imported = manager.import_asset(DRONE_DEST, manager.create_source_data(str(source)), params)
    meshes = [asset for asset in imported if isinstance(asset, u.SkeletalMesh)]
    animations = [asset for asset in imported if isinstance(asset, u.AnimSequence)]
    idle_candidates = [asset for asset in animations if "idle" in asset.get_name().lower()]
    if len(meshes) != 1 or len(idle_candidates) != 1:
        raise RuntimeError(f"Drone import expected one mesh and one idle; got {len(meshes)} and {len(idle_candidates)}")
    if not library.rename_asset(meshes[0].get_path_name(), mesh_path):
        raise RuntimeError("Could not name station drone mesh")
    if not library.rename_asset(idle_candidates[0].get_path_name(), idle_path):
        raise RuntimeError("Could not name station drone idle")
    mesh, idle = library.load_asset(mesh_path), library.load_asset(idle_path)
    if mesh.get_editor_property("skeleton") != idle.get_editor_property("skeleton"):
        raise RuntimeError("Station drone mesh and idle animation use different skeletons")
    library.set_metadata_tag(mesh, "SSOwnedSourceSHA256", source_sha)
    library.set_metadata_tag(idle, "SSOwnedSourceSHA256", source_sha)
    for asset in imported:
        save(asset)
    save(mesh)
    save(idle)
    return {"mesh": mesh.get_path_name(), "idle": idle.get_path_name(),
            "animations": len(animations), "reused": False}


def author_character_cook_label() -> dict:
    """Keep the two runtime-selected vendor characters and clips in packaged builds."""
    library = u.EditorAssetLibrary
    tools = u.AssetToolsHelpers.get_asset_tools()
    selected = [library.load_asset(path) for path in COOK_ASSETS]
    if not all(selected):
        missing = [path for path, asset in zip(COOK_ASSETS, selected) if not asset]
        raise RuntimeError("Missing owned runtime character assets: " + ", ".join(missing))
    base = "/Game/SpaceSurvival/Licensed/OwnedCharacters"
    path = base + "/DA_OwnedCharacterCook"
    library.make_directory(base)
    label_class = u.load_class(None, "/Script/Engine.PrimaryAssetLabel")
    if not label_class:
        raise RuntimeError("PrimaryAssetLabel class is unavailable")
    label = library.load_asset(path) if library.does_asset_exist(path) else None
    if not label:
        factory = u.DataAssetFactory()
        factory.set_editor_property("data_asset_class", label_class)
        label = tools.create_asset("DA_OwnedCharacterCook", base, label_class, factory)
    if not label or label.get_class() != label_class:
        raise RuntimeError("Could not author owned-character cook label")
    rules = label.get_editor_property("Rules")
    for key, value in {"Priority": 1, "ChunkId": -1, "bApplyRecursively": True,
                       "CookRule": u.PrimaryAssetCookRule.ALWAYS_COOK}.items():
        rules.set_editor_property(key, value)
    label.set_editor_property("Rules", rules)
    label.set_editor_property("bIsRuntimeLabel", True)
    label.set_editor_property("bLabelAssetsInMyDirectory", False)
    label.set_editor_property("bIncludeRedirectors", False)
    label.set_editor_property("ExplicitAssets", selected)
    label.set_editor_property("ExplicitBlueprints", [])
    save(label)
    return {"asset": label.get_path_name(), "explicit_assets": list(COOK_ASSETS),
            "cook_rule": "AlwaysCook", "recursive_dependencies": True}


def main() -> None:
    preparation = json.loads((PRIVATE / "Preparation.json").read_text(encoding="utf-8"))
    result = {
        "status": "OWNED_ASSET_PASS_AUTHORED_RUNTIME_REVIEW_PENDING",
        "engine": u.SystemLibrary.get_engine_version(),
        "audio": import_audio(preparation),
        "drone": import_drone(preparation),
        "character_cook": author_character_cook_label(),
    }
    (PRIVATE / "UnrealAuthoring.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    u.log("OWNED_ASSET_PASS " + json.dumps(result))


if __name__ == "__main__":
    main()
