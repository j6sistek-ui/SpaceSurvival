"""Author only the private cook label for the two untouched owned gallery maps.

Run with the existing Unreal Python authoring runner. This does not modify vendor
content or the player's station layout. Both maps and recursive dependencies are
selected so an explicitly packaged licensed build can use the runtime doorway.
"""
from pathlib import Path
import json
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
MAPS = (
    "/Game/Megastructure_Scifi_World/Level/L_Showcase_level",
    "/Game/Megastructure_Scifi_World/Level/L_assets",
)


def main():
    library = u.EditorAssetLibrary
    maps = [library.load_asset(path) for path in MAPS]
    if not all(maps):
        raise RuntimeError("Both owned alien maps must be installed before authoring the gallery cook label")
    base = "/Game/SpaceSurvival/Licensed/AlienGallery"
    path = base + "/DA_AlienGalleryCook"
    library.make_directory(base)
    cls = u.load_class(None, "/Script/Engine.PrimaryAssetLabel")
    label = library.load_asset(path) if library.does_asset_exist(path) else None
    if not label:
        factory = u.DataAssetFactory()
        factory.set_editor_property("data_asset_class", cls)
        label = u.AssetToolsHelpers.get_asset_tools().create_asset("DA_AlienGalleryCook", base, cls, factory)
    if not label or label.get_class() != cls:
        raise RuntimeError("Private gallery cook label could not be created")
    rules = label.get_editor_property("Rules")
    for key, value in {"Priority": 1, "ChunkId": -1, "bApplyRecursively": True,
                       "CookRule": u.PrimaryAssetCookRule.ALWAYS_COOK}.items():
        rules.set_editor_property(key, value)
    label.set_editor_property("Rules", rules)
    label.set_editor_property("bIsRuntimeLabel", True)
    label.set_editor_property("bLabelAssetsInMyDirectory", False)
    label.set_editor_property("bIncludeRedirectors", False)
    label.set_editor_property("ExplicitAssets", maps)
    label.set_editor_property("ExplicitBlueprints", [])
    if not library.save_loaded_asset(label, only_if_is_dirty=False):
        raise RuntimeError("Could not save private gallery cook label")
    receipt = ROOT / "Artifacts/AlienGallery/authoring.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({"status": "COOK_LABEL_AUTHORED_RUNTIME_REVIEW_PENDING",
                                  "engine": u.SystemLibrary.get_engine_version(),
                                  "maps": MAPS, "label": label.get_path_name(),
                                  "vendor_modified": False}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
