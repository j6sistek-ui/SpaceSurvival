"""Read back deck assets in a fresh Editor; does not mutate content."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ss_deck_author", ROOT / "Scripts/AuthorStationDeck.py")
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)


def main():
    result = {"status": "FAILED", "errors": [], "textures": [],
              "limits": ["Persisted import/material checks only; native visual and resource review pending."]}
    try:
        manifest = author.source_manifest()
        library = u.EditorAssetLibrary
        edit = u.MaterialEditingLibrary
        expected = {"diff": u.TextureCompressionSettings.TC_BC7,
                    "arm": u.TextureCompressionSettings.TC_MASKS, "nor_dx": u.TextureCompressionSettings.TC_NORMALMAP}
        for row in manifest["maps"]:
            path = author.BASE + "/Textures/" + author.NAMES[row["kind"]]
            texture = library.load_asset(path)
            assert isinstance(texture, u.Texture2D), path
            assert library.get_metadata_tag(texture, "SSDeckSourceSHA256") == row["sha256"]
            assert texture.get_editor_property("srgb") == (row["kind"] == "diff")
            assert texture.get_editor_property("compression_settings") == expected[row["kind"]]
            assert texture.get_editor_property("address_x") == u.TextureAddress.TA_WRAP
            assert texture.get_editor_property("address_y") == u.TextureAddress.TA_WRAP
            result["textures"].append({"path": path, "source_sha256": row["sha256"],
                                       "compression": str(texture.get_editor_property("compression_settings")),
                                       "srgb": texture.get_editor_property("srgb")})
        material = library.load_asset(author.MATERIAL)
        assert isinstance(material, u.Material)
        assert library.get_metadata_tag(material, "SSDeckVersion") == author.VERSION
        source_key = hashlib.sha256("".join(row["sha256"] for row in manifest["maps"]).encode()).hexdigest()
        assert library.get_metadata_tag(material, "SSDeckSourceKey") == source_key
        assert library.get_metadata_tag(material, "SSAssetLicense") == "CC0-1.0"
        assert material.get_editor_property("blend_mode") == u.BlendMode.BLEND_OPAQUE
        assert material.get_editor_property("used_with_instanced_static_meshes")
        assert abs(edit.get_material_default_scalar_parameter_value(material, "Desaturation") - .85) < 1e-5
        tint = edit.get_material_default_vector_parameter_value(material, "DeckTint")
        assert all(abs(a-b) < 1e-5 for a, b in zip((tint.r, tint.g, tint.b), (.45, .52, .60)))
        for kind, name in author.NAMES.items():
            texture = edit.get_material_default_texture_parameter_value(material, name)
            assert texture and texture.get_path_name().split(".")[0] == author.BASE + "/Textures/" + name
        result.update(status="PERSISTED_DECK_ASSETS_VERIFIED_NOT_VISUAL_ACCEPTANCE",
                      material=author.MATERIAL, source_key=source_key, repeat_cm=50, panel_cm=[535,435],
                      author=manifest["author"], asset_url=manifest["asset_url"], license="CC0-1.0")
    except Exception as error:
        result["errors"].append(str(error))
        u.log_error("SS_STATION_DECK_VALIDATION_FAILED: " + str(error))
    folder = ROOT / "Saved/Validation"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "StationDeckPersisted.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if result["errors"]:
        raise RuntimeError("Deck validation failed; see Saved/Validation/StationDeckPersisted.json")
    u.log("SS_STATION_DECK_PERSISTED_OK")


if __name__ == "__main__":
    main()
