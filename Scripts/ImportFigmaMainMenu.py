"""Import the approved main-menu PNGs without modifying their source bytes.

Portable validation: python Scripts/ImportFigmaMainMenu.py --validate-only
The lead runs the default dry-run in a separate offscreen editor, then repeats
with -SSApplyFigmaMainMenu. Only the 19 named UI textures can be created. Existing
outputs require the prior local ownership receipt and are reused unchanged;
unknown or modified outputs fail before any import. No Figma API calls occur.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ContentSource/FigmaMainMenu"
OUT = ROOT / "Artifacts/FigmaMainMenu"
BASE = "/Game/SpaceSurvival/UI/MainMenu"
NAMES = {
    "main-background.png": "T_MainBackground", "main-title.png": "T_MainTitle",
    "main-hero-left.png": "T_MainHeroLeft", "main-hero-right.png": "T_MainHeroRight",
    "continue-normal.png": "T_ContinueNormal", "continue-hover.png": "T_ContinueHover",
    "new-game-normal.png": "T_NewGameNormal", "new-game-hover.png": "T_NewGameHover",
    "settings-normal.png": "T_SettingsNormal", "settings-hover.png": "T_SettingsHover",
    "exit-normal.png": "T_ExitNormal", "exit-hover.png": "T_ExitHover",
    "footer-panel-inner.png": "T_FooterPanel", "hint-enter.png": "T_HintEnter",
    "hint-select.png": "T_HintSelect", "hint-move-keys.png": "T_HintMoveKeys",
    "hint-move.png": "T_HintMove", "hint-escape.png": "T_HintEscape", "hint-quit.png": "T_HintQuit",
}


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def validate_sources(source=SOURCE):
    manifest = json.loads((source / "provenance.json").read_text(encoding="utf-8"))
    assert manifest["fileKey"] == "6M3VvUB7jsPDd3E41YpKM0" and manifest["pageId"] == "142:1059"
    assert {row["file"] for row in manifest["assets"] if row["runtime"]} == set(NAMES)
    assert len({row["file"] for row in manifest["assets"]}) == len(manifest["assets"])
    for row in manifest["assets"]:
        assert Path(row["file"]).name == row["file"], "Source path escaped the approved export folder"
        file = source / row["file"]
        data = file.read_bytes()
        assert hashlib.sha256(data).hexdigest() == row["sha256"], "Source hash differs: " + row["file"]
        assert data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR"
        assert struct.unpack_from(">II", data, 16) == (row["width"], row["height"])
        assert len(data) == row["sizeBytes"]
        if row["runtime"] and row["file"] != "main-background.png":
            assert row["alphaMin"] == 0 and row["alphaMax"] == 255, "Opaque/empty UI overlay rejected"
    assert sha(source / "main-hero-left-source.png") == manifest["sourcePortraitSHA256"]
    return manifest


def source_hashes():
    return {file.name: sha(file) for file in sorted(SOURCE.iterdir()) if file.is_file()}


def package_file(name):
    assert name in NAMES.values(), "Output escaped the approved UI texture set"
    return ROOT / "Content/SpaceSurvival/UI/MainMenu" / (name + ".uasset")


def output_hashes():
    return {BASE + "/" + name: sha(package_file(name)) for name in NAMES.values() if package_file(name).exists()}


def write_receipt(path, receipt):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")


def author():
    import unreal as u

    assert Path(u.Paths.project_dir()).resolve() == ROOT, "Wrong project: use the repair checkout"
    manifest = validate_sources()
    before = source_hashes()
    existing = output_hashes()
    apply = "-SSApplyFigmaMainMenu" in u.SystemLibrary.get_command_line()
    receipt_path = OUT / ("author.json" if apply else "author-dry-run.json")
    previous_path = OUT / "author.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else {}
    for path, digest in existing.items():
        assert previous.get("outputs", {}).get(path) == digest, "Unknown or modified private output: " + path
    if existing:
        assert previous.get("source_hashes") == before, "Source changed; deliberate reviewed reimport required"
    receipt = {"utc": datetime.now(timezone.utc).isoformat(), "status": "dry-run", "apply": apply,
               "source_hashes": before, "source_preserved": True, "outputs_before": existing,
               "outputs": existing.copy(), "created": [], "reused": [], "textures": [],
               "source_url": manifest["sourceURL"], "runtime_visual_acceptance": False}
    write_receipt(receipt_path, receipt)
    if not apply:
        receipt["planned_packages"] = [BASE + "/" + name for name in NAMES.values()]
        write_receipt(receipt_path, receipt)
        u.log("SS_FIGMA_MAIN_MENU_DRY_RUN 19 exact textures; no content changes")
        return

    lib = u.EditorAssetLibrary
    settings = {"compression_settings": u.TextureCompressionSettings.TC_EDITOR_ICON,
                "lod_group": u.TextureGroup.TEXTUREGROUP_UI,
                "mip_gen_settings": u.TextureMipGenSettings.TMGS_NO_MIPMAPS,
                "srgb": True, "never_stream": True, "filter": u.TextureFilter.TF_BILINEAR,
                "address_x": u.TextureAddress.TA_CLAMP, "address_y": u.TextureAddress.TA_CLAMP,
                "lod_bias": 0, "max_texture_size": 0}
    try:
        # Preflight ALL loaded identities/settings before creating the first missing texture.
        for row in manifest["assets"]:
            if not row["runtime"]:
                continue
            name = NAMES[row["file"]]
            path = BASE + "/" + name
            if path not in existing:
                assert not lib.does_asset_exist(path), "Unsaved or unreceipted output exists: " + path
                continue
            texture = lib.load_asset(path)
            assert isinstance(texture, u.Texture2D)
            assert lib.get_metadata_tag(texture, "SSFigmaSourceSHA256") == row["sha256"]
            for key, value in settings.items():
                assert texture.get_editor_property(key) == value, "Owned texture settings differ: " + path + "/" + key
        for row in manifest["assets"]:
            if not row["runtime"]:
                continue
            name = NAMES[row["file"]]
            path = BASE + "/" + name
            if path in existing:
                texture = lib.load_asset(path)
                receipt["reused"].append(path)
            else:
                task = u.AssetImportTask()
                for key, value in {"filename": str(SOURCE / row["file"]), "destination_path": BASE,
                                   "destination_name": name, "automated": True,
                                   "replace_existing": False, "save": False}.items():
                    task.set_editor_property(key, value)
                u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
                texture = lib.load_asset(path)
                assert isinstance(texture, u.Texture2D), "Import did not produce expected texture: " + path
                for key, value in settings.items():
                    texture.set_editor_property(key, value)
                lib.set_metadata_tag(texture, "SSFigmaSourceSHA256", row["sha256"])
                lib.set_metadata_tag(texture, "SSFigmaNodeId", row["nodeId"])
                lib.set_metadata_tag(texture, "SSFigmaFileKey", manifest["fileKey"])
                assert lib.save_loaded_asset(texture, only_if_is_dirty=False), "Texture save failed: " + path
                receipt["created"].append(path)
            assert (texture.blueprint_get_size_x(), texture.blueprint_get_size_y()) == (row["width"], row["height"])
            receipt["textures"].append({"package": path, "source_sha256": row["sha256"],
                                         "width": row["width"], "height": row["height"], "drawRect4K": row["drawRect4K"]})
            receipt["outputs"] = output_hashes()
            receipt["status"] = "in-progress"
            write_receipt(receipt_path, receipt)
        receipt["status"] = "complete"
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error"] = str(error)
        raise
    finally:
        receipt["source_preserved"] = source_hashes() == before
        receipt["outputs"] = output_hashes()
        write_receipt(receipt_path, receipt)
        assert receipt["source_preserved"], "Figma source bytes changed during import"
    u.log("SS_FIGMA_MAIN_MENU_COMPLETE 19 exact textures; rendered/input acceptance remains open")


if __name__ == "__main__":
    if "--validate-only" in sys.argv:
        document = validate_sources()
        print(f"Figma sources verified: {len(document['assets'])} PNG hashes/dimensions; {len(NAMES)} runtime textures.")
    else:
        author()
