"""Preserve the supplied Phoenix hull/ramp and replace only coarse parked foot envelopes.

UnrealEditor-Cmd -ExecutePythonScript=<this file> performs a dry-run.
Add -SSApplyPhoenixParkedPhysics to save the unique private physics derivative.
"""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
TARGET = "/Game/SpaceSurvival/Licensed/PhoenixPresentation/PA_PhoenixParked"
RECEIPT = ROOT / "Artifacts/PhoenixPresentation/parked-physics-author.json"
SOURCES = (
    "/Game/Stellar_Phoenix/Spaceship/Meshes/Stellar_Phoenix_PhysicsAsset",
    "/Game/Stellar_Phoenix/Spaceship/Meshes/Stellar_Phoenix",
)


def digest(package):
    path = ROOT / "Content" / (package.removeprefix("/Game/") + ".uasset")
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main():
    apply = "-SSApplyPhoenixParkedPhysics" in u.SystemLibrary.get_command_line()
    original = {name: digest(name) for name in SOURCES}
    assert all(original.values()), "Required licensed Phoenix assets are missing"
    prior = json.loads(RECEIPT.read_text(encoding="utf-8")) if RECEIPT.is_file() else None
    existing = digest(TARGET)
    if existing:
        assert prior and prior.get("output_sha256") == existing, "Unowned or edited target; refusing overwrite"
        assert prior.get("source_sha256") == original, "Source changed since the recorded authoring"
    result = json.loads(u.SSFlightHullAuthoringLibrary.author_phoenix_parked_physics(apply, bool(existing)))
    result.update(utc=datetime.now(timezone.utc).isoformat(), source_sha256=original, mode="apply" if apply else "dry-run")
    assert result["success"], json.dumps(result)
    if apply:
        asset = u.load_asset(TARGET)
        assert asset and u.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False), "Parked physics save failed"
        result["output_sha256"] = digest(TARGET)
    result["source_preserved"] = {name: digest(name) == sha for name, sha in original.items()}
    assert all(result["source_preserved"].values()), "An original licensed asset changed during authoring"
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    destination = RECEIPT if apply else RECEIPT.with_name("parked-physics-dry-run.json")
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("PHOENIX_PARKED_PHYSICS_COMPLETE " + str(result["parked_shapes"]))


main()
