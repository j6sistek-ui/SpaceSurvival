"""Reviewed R/Market/L source sets; native staging is an explicit caller action.

Importing this module or using its CLI only reads source files. Staging creates
five unsaved private textures, never materials/actors/assignments/map saves.
IDs/families are declared metadata, not semantic uniqueness proof; bind the
manually reviewed manifest hash. Caller verifies pending texture compilation,
native dimensions, appearance and cycling separately after staging.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOMS = {
    "R": ("R customization / crew archive", "CustomizationCampaigns"),
    "Market": ("Market", "MarketCampaigns"),
    "L": ("L social / lounge / bar", "LoungeCampaigns"),
}
BASE = "/Game/OutpostSandbox/StationRefinement/"
SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9_]{0,63}\Z")
SHA = re.compile(r"[0-9a-fA-F]{64}\Z")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_sources(manifest_path, expected_manifest_sha256, room_id):
    """Read only the five selected local files; variants never become rows."""
    _require(room_id in ROOMS, "Only R, Market and L are allowed; T/central are excluded")
    _require(isinstance(expected_manifest_sha256, str) and SHA.fullmatch(expected_manifest_sha256),
             "Supply the exact reviewed manifest SHA256")
    manifest_path = Path(manifest_path).resolve(strict=True)
    raw = manifest_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    _require(digest == expected_manifest_sha256.lower(), "Reviewed manifest bytes changed")
    data = json.loads(raw.decode("utf-8-sig"))
    rows = data.get("campaigns")
    _require(data.get("room") == ROOMS[room_id][0], "Manifest room differs from room_id")
    _require(data.get("campaign_count") == 5 and isinstance(rows, list) and len(rows) == 5,
             "Exactly five selected campaigns required")
    selected, ids, families, paths, hashes = [], set(), set(), set(), set()
    for row in rows:
        name, filename, digest = row.get("campaign_id"), row.get("file"), row.get("sha256")
        family = row.get("family_id", name)
        _require(isinstance(name, str) and SLUG.fullmatch(name), "Invalid campaign_id slug")
        _require(isinstance(family, str) and family.strip() and family == family.strip(),
                 "Invalid declared family_id")
        _require(isinstance(filename, str) and filename and not Path(filename).is_absolute(),
                 "Selected file must be relative to the manifest folder")
        path = (manifest_path.parent / filename).resolve(strict=True)
        _require(path.is_relative_to(manifest_path.parent) and path.is_file(),
                 "Selected source escapes the manifest folder")
        _require(path.suffix.lower() in (".png", ".jpg", ".jpeg"), "Only selected PNG/JPEG art allowed")
        _require(isinstance(digest, str) and SHA.fullmatch(digest) and _sha(path) == digest.lower(),
                 "Selected source hash differs: " + filename)
        _require(name.casefold() not in ids and family.casefold() not in families and
                 path not in paths and digest.lower() not in hashes,
                 "Repeated declared ID/family, selected file or identical bitmap")
        ids.add(name.casefold()); families.add(family.casefold())
        paths.add(path); hashes.add(digest.lower())
        selected.append({"campaign_id": name, "family_id": family,
                         "file": str(path), "sha256": digest.lower()})
    return {"status": "SOURCE_HASHES_VERIFIED", "room_id": room_id,
            "manifest": str(manifest_path), "manifest_sha256": expected_manifest_sha256.lower(),
            "campaigns": selected, "family_identity": "declared; manual review required"}


class StageError(RuntimeError):
    """The report retains partial identities; never retry or delete blindly."""
    def __init__(self, report):
        self.report = report
        super().__init__("Texture staging failed; inspect StageError.report: " + report["error"])


def stage_textures(u, manifest_path, expected_manifest_sha256, room_id, stage_id):
    """Root-only, when native work is authorized; refuse any prior staging."""
    source = inspect_sources(manifest_path, expected_manifest_sha256, room_id)
    _require(isinstance(stage_id, str) and SLUG.fullmatch(stage_id), "Invalid stage_id slug")
    destination = BASE + ROOMS[room_id][1] + stage_id + "/Textures"
    targets = [destination + "/T_" + row["campaign_id"] for row in source["campaigns"]]
    present = [bool(u.EditorAssetLibrary.does_asset_exist(path)) for path in targets]
    folder_exists = bool(u.EditorAssetLibrary.does_directory_exist(destination))
    _require(not any(present) and not folder_exists,
             "Destination already exists; no overwrite, resume or partial retry: " + destination)
    settings = {"srgb": True, "compression_settings": u.TextureCompressionSettings.TC_BC7,
                "lod_group": u.TextureGroup.TEXTUREGROUP_WORLD,
                "mip_gen_settings": u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,
                "address_x": u.TextureAddress.TA_CLAMP, "address_y": u.TextureAddress.TA_CLAMP}
    report = {"status": "STAGING", "source": source, "destination": destination,
              "targets": targets, "attempted_paths": [], "created_paths": [],
              "import_results": [], "saved": False, "compilation_verified": False,
              "dimensions_verified": False, "screen_fit_verified": False, "cycling_verified": False}
    task = None
    try:
        for row, target in zip(source["campaigns"], targets):
            _require(_sha(Path(row["file"])) == row["sha256"], "Source changed before import")
            task = u.AssetImportTask()
            for key, value in {"filename": row["file"], "destination_path": destination,
                               "destination_name": target.rsplit("/", 1)[1], "automated": True,
                               "replace_existing": False, "replace_existing_settings": False,
                               "save": False}.items():
                task.set_editor_property(key, value)
            report["attempted_paths"].append(target)
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            result = {"target": target, "imported_object_paths":
                      [str(p) for p in task.get_editor_property("imported_object_paths")]}
            report["import_results"].append(result)
            texture = u.load_asset(target)
            _require(isinstance(texture, u.Texture2D), "Expected Texture2D not created: " + target)
            identity = texture.get_path_name()
            report["created_paths"].append(identity)
            name = target.rsplit("/", 1)[1]
            _require(identity == target + "." + name, "Imported texture identity differs")
            for key, value in settings.items():
                texture.set_editor_property(key, value)
        inspect_sources(manifest_path, expected_manifest_sha256, room_id)
        report["status"] = "STAGED_UNVERIFIED"
        return report
    except Exception as error:
        report.update(status="STAGING_FAILED", error=repr(error), inspection_errors=[])
        if task is not None:
            try:
                report["last_task_imported_paths"] = [str(p) for p in
                                                      task.get_editor_property("imported_object_paths")]
            except Exception as inspection_error:
                report["inspection_errors"].append(repr(inspection_error))
        report["observed_existing_paths"] = []
        for path in targets:
            try:
                if u.EditorAssetLibrary.does_asset_exist(path):
                    report["observed_existing_paths"].append(path)
            except Exception as inspection_error:
                report["inspection_errors"].append(path + ": " + repr(inspection_error))
        raise StageError(report) from error


def main():
    parser = argparse.ArgumentParser(description="Read-only reviewed ad source inspection; no Unreal import")
    parser.add_argument("manifest")
    parser.add_argument("expected_sha256")
    parser.add_argument("--room", choices=tuple(ROOMS), required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_sources(args.manifest, args.expected_sha256, args.room), indent=2))


if __name__ == "__main__":
    main()
