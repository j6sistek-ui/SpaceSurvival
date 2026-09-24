"""Import exact read-only Figma exports. Dry-run by default; -SSApplyUIRefresh creates only owned UI assets."""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ContentSource/FigmaUIRefresh"
BASE = "/Game/SpaceSurvival/UI/Refresh"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate():
    manifest = json.loads((SOURCE / "provenance.json").read_text(encoding="utf-8"))
    assert manifest["fileKey"] == "6M3VvUB7jsPDd3E41YpKM0"
    assert manifest["pageId"] == "203:1058"
    names = set()
    for row in manifest["assets"]:
        assert row["name"].isalnum() and row["name"] not in names
        names.add(row["name"])
        assert row["file"] == row["name"] + ".png"
        data = (SOURCE / row["file"]).read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        assert struct.unpack_from(">II", data, 16) == (row["width"], row["height"])
        assert hashlib.sha256(data).hexdigest() == row["sha256"]
        if row["name"] != "Background":
            assert row["alphaMin"] == 0 and row["alphaMax"] > 0
    for row in manifest['font'].values():
        assert digest(SOURCE / row['file']) == row['sha256']
        assert digest(ROOT / 'Content/SpaceSurvival/UI/Fonts' / row['file']) == row['sha256']
    return manifest


def author():
    import unreal as u
    assert Path(u.Paths.project_dir()).resolve() == ROOT
    manifest = validate()
    apply = "-SSApplyUIRefresh" in u.SystemLibrary.get_command_line()
    lib = u.EditorAssetLibrary
    receipt = {"apply": apply, "status": "dry-run", "textures": [], "outputs": {}}
    for row in manifest["assets"]:
        path = BASE + "/T_" + row["name"]
        if lib.does_asset_exist(path):
            texture = lib.load_asset(path)
            assert isinstance(texture, u.Texture2D)
            assert lib.get_metadata_tag(texture, "SSFigmaSourceSHA256") == row["sha256"], path
    if apply:
        settings = {"compression_settings": u.TextureCompressionSettings.TC_EDITOR_ICON,
                    "lod_group": u.TextureGroup.TEXTUREGROUP_UI,
                    "mip_gen_settings": u.TextureMipGenSettings.TMGS_NO_MIPMAPS,
                    "srgb": True, "never_stream": True, "filter": u.TextureFilter.TF_BILINEAR,
                    "address_x": u.TextureAddress.TA_CLAMP, "address_y": u.TextureAddress.TA_CLAMP}
        for row in manifest["assets"]:
            name = "T_" + row["name"]
            path = BASE + "/" + name
            if not lib.does_asset_exist(path):
                task = u.AssetImportTask()
                for key, value in {"filename": str(SOURCE / row["file"]), "destination_path": BASE,
                                   "destination_name": name, "automated": True,
                                   "replace_existing": False, "save": False}.items():
                    task.set_editor_property(key, value)
                u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
                texture = lib.load_asset(path)
                assert isinstance(texture, u.Texture2D)
                for key, value in settings.items():
                    texture.set_editor_property(key, value)
                lib.set_metadata_tag(texture, "SSFigmaSourceSHA256", row["sha256"])
                lib.set_metadata_tag(texture, "SSFigmaNodeId", row["nodeId"])
                assert lib.save_loaded_asset(texture, only_if_is_dirty=False)
            texture = lib.load_asset(path)
            assert (texture.blueprint_get_size_x(), texture.blueprint_get_size_y()) == (row["width"], row["height"])
            receipt["textures"].append(path)
            receipt["outputs"][path] = digest(ROOT / "Content/SpaceSurvival/UI/Refresh" / (name + ".uasset"))
        receipt["status"] = "complete"
    validate()
    out = ROOT / "Artifacts/UIRefresh" / ("author.json" if apply else "author-dry-run.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    u.log("SS_UI_REFRESH " + receipt["status"])


if __name__ == "__main__":
    if "--validate-only" in sys.argv:
        print("Validated exact UI asset hashes/dimensions:", len(validate()["assets"]))
    else:
        author()
