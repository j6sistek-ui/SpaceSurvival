"""Create the owner-editable station Blueprint once, then preserve manual edits.

Run through the installed editor Python commandlet after AuthorStationVisualPass.
Optional --layout-recipe PATH supplements/replaces initial meshes and lights.
Only --reset-layout explicitly rebuilds an existing Blueprint; it first preserves
the prior saved .uasset byte-for-byte in the private authoring receipt directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import uuid
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "/Game/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layout-recipe", type=Path,
                        default=ROOT / ".agent/local/StationVisualPass/EditableLayout.json")
    parser.add_argument("--reset-layout", action="store_true")
    args = parser.parse_args()
    lib = u.EditorAssetLibrary
    existed = lib.does_asset_exist(PACKAGE)
    output = ROOT / ".agent/local/StationVisualPass" / ("EditableLayout-" + uuid.uuid4().hex)
    output.mkdir(parents=True, exist_ok=False)
    disk = ROOT / "Content" / (PACKAGE[len("/Game/"):] + ".uasset")
    before = hashlib.sha256(disk.read_bytes()).hexdigest() if disk.is_file() else None
    backup = None
    if existed and args.reset_layout:
        assert disk.is_file(), "Save the existing owner layout before an explicit reset."
        backup = output / disk.name
        shutil.copy2(disk, backup)
        assert hashlib.sha256(backup.read_bytes()).hexdigest() == before
    recipe_text = args.layout_recipe.read_text(encoding="utf-8-sig") if args.layout_recipe.is_file() else "{}"
    json.loads(recipe_text)
    bridge = u.SSStationLayoutAuthoringLibrary
    if existed and not args.reset_layout:
        blueprint = lib.load_asset(PACKAGE)
        status = "OWNER_LAYOUT_PRESERVED_UNCHANGED"
    else:
        blueprint = bridge.create_station_visual_layout(recipe_text, args.reset_layout)
        assert blueprint, "Native station layout authoring failed; inspect the editor log."
        audit = json.loads(bridge.describe_station_visual_layout(blueprint))
        assert audit.get("compiled") and len(audit.get("components", [])) > 0, audit
        lib.set_metadata_tag(blueprint, "SSStationLayoutInitialRecipeSHA256", hashlib.sha256(recipe_text.encode()).hexdigest())
        assert lib.save_loaded_asset(blueprint, only_if_is_dirty=False)
        status = "EDITABLE_LAYOUT_AUTHORED_RUNTIME_REVIEW_PENDING"
    assert blueprint and disk.is_file()
    after = hashlib.sha256(disk.read_bytes()).hexdigest()
    if existed and not args.reset_layout:
        assert after == before, "Existing owner layout bytes changed unexpectedly."
    audit = json.loads(bridge.describe_station_visual_layout(blueprint))
    result = dict(status=status, blueprint=PACKAGE, file=str(disk), sha256=after,
                  previous_sha256=before, backup=str(backup) if backup else None,
                  recipe=str(args.layout_recipe) if args.layout_recipe.is_file() else None,
                  recipe_sha256=hashlib.sha256(recipe_text.encode()).hexdigest(),
                  native_audit=audit, engine=u.SystemLibrary.get_engine_version(),
                  scope="Editable visual components; ASSStation retains collision, services and docking.")
    receipt = output / "Authoring.json"
    receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    u.log("STATION_EDITABLE_LAYOUT " + json.dumps(dict(status=status, receipt=str(receipt), components=len(audit.get("components", [])))))


if __name__ == "__main__":
    main()
