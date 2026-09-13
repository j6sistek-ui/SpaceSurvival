"""Fresh-process readback of the isolated NASA texture/material instance.
No asset saves, runtime selection, viewport rendering or quality changes.
"""
import hashlib
import importlib.util
from pathlib import Path
import traceback
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ss_milkyway_author", ROOT / "Scripts/AuthorMilkyWay.py")
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)


def main():
    before = author.snapshot()
    record = {"status": "FAILED", "errors": []}
    try:
        manifest = author.source_manifest()
        texture = u.EditorAssetLibrary.load_asset(author.TEXTURE)
        instance = u.EditorAssetLibrary.load_asset(author.INSTANCE)
        record.update(author.validate_loaded(texture, instance, manifest))
        assert author.OWNED.issubset(before), "Both persisted candidate packages must exist"
        record["packages"] = [{"path": path, "bytes": (ROOT / path).stat().st_size,
                               "sha256": author.sha(ROOT / path)} for path in sorted(author.OWNED)]
        record["parent_package"] = {
            "path": "Content/SpaceSurvival/Materials/M_Space.uasset",
            "sha256": author.sha(ROOT / "Content/SpaceSurvival/Materials/M_Space.uasset"),
        }
        record["scripts"] = {
            name: hashlib.sha256((ROOT / "Scripts" / name).read_bytes()).hexdigest()
            for name in ("AuthorMilkyWay.py", "ValidateMilkyWay.py")
        }
        author.check_unchanged(before)
        author.source_manifest()
        record.update(status="NASA_SKY_FRESH_SELECTION_AND_8K_VALIDATED_NOT_NATIVE_VISUAL_ACCEPTANCE",
                      errors=[], engine=u.SystemLibrary.get_engine_version(), preserved_files=len(before),
                      limits=["Compiled 8192x4096 dimensions do not prove actual runtime mip residency.",
                              "Inherited sky graph and one texture override only; no native view or frame-cost measurement.",
                              "Display-converted RGB8 source is not a byte-lossless copy of the original half-float EXR.",
                              "Existing runtime bindings and geometry stars remain unchanged by these scripts."])
        author.write("Persisted.json", record)
        return record
    except Exception as exc:
        record["errors"].append(str(exc))
        try:
            author.check_unchanged(before)
        except Exception as guard:
            record["errors"].append(str(guard))
        author.write("Persisted.json", record)
        u.log_error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
