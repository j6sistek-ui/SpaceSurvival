"""Import only the private closed player hull and its fitted Havolk modules.

Run by the integration lead after AssemblePlayerShipVisualPass.py. Shares the
proven static-mesh importer, but writes a separate ignored private root only.
"""
import importlib.util
import json
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Artifacts/PlayerShipVisualPass"
spec = importlib.util.spec_from_file_location("ship_import", ROOT / "Scripts/AuthorShipVisualPass.py")
ship_import = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ship_import)
ship_import.SOURCE = OUT / "Assembly"
ship_import.BASE = "/Game/SpaceSurvival/Licensed/PlayerShipVisualPass/Meshes"
ship_import.VERSION = "HavolkPlayerHull1"


def main():
    source = OUT / "Assembly/Assembly.json"
    report = json.loads(source.read_text(encoding="utf-8"))
    assert report["generator_sha256"] == ship_import.sha(ROOT / "Scripts/AssemblePlayerShipVisualPass.py")
    assert report["helper_sha256"] == ship_import.sha(ROOT / "Scripts/AssembleShipVisualPass.py")
    assert report["coordinate_encoder_sha256"] == ship_import.sha(ROOT / "Scripts/EncodeUnrealObj.py")
    assert report["obj_space"] == "UNREAL_FBX_REFLECT_Y_REVERSE_WINDING_V1"
    expected = {"SM_UpgradeHavolk" + track + str(tier)
                for track in ("Hull", "Shield", "Engine", "Thrusters", "Laser", "Cannon") for tier in range(2, 6)}
    expected |= {"SM_PlayerHavolkStarter", "SM_UtilityHavolkVector", "SM_UtilityHavolkCooling"}
    assert {row["name"] for row in report["assets"]} == expected
    for row in report["assets"]:
        assert row["obj_encoding"]["space"] == report["obj_space"]
        assert row["obj_encoding"]["encoded_sha256"] == row["obj_sha256"]
    originals = {p: ship_import.sha(p) for folder in ("Content/Spacecraft_Pack", "Content/SpaceSurvival/Character",
                 "Content/SpaceSurvival/Meshes", "Content/SpaceSurvival/Licensed/ShipVisualPass")
                 for p in (ROOT / folder).rglob("*.uasset")}
    rows = [ship_import.validate(ship_import.import_mesh(row), row) for row in report["assets"]]
    assert all(ship_import.sha(p) == digest for p, digest in originals.items()), "Protected asset changed"
    result = {"status": "IMPORTED_BOUNDS_MATERIAL_COLLISION_VERIFIED_REQUIRES_NATIVE_REVIEW",
              "engine": u.SystemLibrary.get_engine_version(), "assembly_sha256": ship_import.sha(source),
              "assets": rows, "protected_assets_unchanged": len(originals),
              "scope": "Provisional Starter presentation; stats, collision, artist originals and rigs unchanged."}
    (OUT / "Import.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    u.log("PLAYER_SHIP_VISUAL_IMPORT_OK " + str(len(rows)))


if __name__ == "__main__":
    main()
