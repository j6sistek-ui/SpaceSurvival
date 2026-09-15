"""Stage selected owned content without modifying Fab downloads.

Native Unreal packs are copied byte-for-byte into the working project so the
Station Workshop can browse them. A small role-based audio set and the raw drone
GLB are copied into the private authoring area for Unreal import.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil
import struct
import wave

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "User downloaded assets/SpaceSurvival/Content"
VAULT = ROOT / "User downloaded assets/VaultCache/FabLibrary"
PRIVATE = ROOT / ".agent/local/OwnedAssetIntegration"

NATIVE_PACKS = (
    "SciFITrooper_Man_03",
    "Heavy_space_trooper",
    "CosmicMaterial",
)

AUDIO = {
    "Engine": ("enginesounds/WAV/engine16_loop.uasset", True),
    "Laser": ("weapons/WAV/aliengun001singleshot.uasset", False),
    "Cannon": ("weapons/WAV/aliengun004singleshot.uasset", False),
    "Impact": ("shipsounds/WAV/mechanic05.uasset", False),
    "Pickup": ("interface/WAV/bleep31.uasset", False),
    "Alarm": ("alarm/WAV/alarm03.uasset", False),
    "Station": ("atmos/WAV/electric_power01_loop.uasset", True),
    "EnemyFire": ("weapons/WAV/Alien_gun_set_08_sound10.uasset", False),
    "EnemyBreak": ("explosions/WAV/explosion24.uasset", False),
    "DebrisBreak": ("explosions/WAV/explosion24.uasset", False),
}

DRONE = VAULT / (
    "Customizable_Drone_Companion_1-d88ec08e/glb/converted/"
    "drone_pack_1_sci_fi_ue4_project_included.glb"
)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def copy_tree(source: Path, destination: Path) -> dict:
    if not source.is_dir():
        raise FileNotFoundError(source)
    copied = reused = 0
    total = 0
    for original in sorted(path for path in source.rglob("*") if path.is_file()):
        relative = original.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.stat().st_size != original.stat().st_size or sha(target) != sha(original):
                raise RuntimeError(f"Existing owned asset differs; reconcile manually: {target}")
            reused += 1
        else:
            shutil.copy2(original, target)
            if sha(target) != sha(original):
                raise RuntimeError(f"Copy verification failed: {target}")
            copied += 1
        total += original.stat().st_size
    return {"source": str(source.relative_to(ROOT)), "destination": str(destination.relative_to(ROOT)),
            "files": copied + reused, "copied": copied, "reused": reused, "bytes": total}


def extract_wave(source: Path, target: Path, looping: bool) -> dict:
    payload = source.read_bytes()
    offset = payload.find(b"RIFF")
    if offset < 0:
        raise RuntimeError(f"No embedded RIFF payload: {source}")
    size = struct.unpack_from("<I", payload, offset + 4)[0] + 8
    riff = payload[offset:offset + size]
    if len(riff) != size or riff[8:12] != b"WAVE":
        raise RuntimeError(f"Invalid embedded WAVE payload: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(riff)
    with wave.open(str(target), "rb") as audio:
        seconds = audio.getnframes() / audio.getframerate()
        fmt = {"rate": audio.getframerate(), "channels": audio.getnchannels(),
               "bits": audio.getsampwidth() * 8, "seconds": round(seconds, 4)}
    return {"source": str(source.relative_to(ROOT)), "source_sha256": sha(source),
            "wav": str(target.relative_to(ROOT)), "wav_sha256": sha(target),
            "loop": looping, **fmt}


def main() -> None:
    PRIVATE.mkdir(parents=True, exist_ok=True)
    packs = [copy_tree(STAGING / name, ROOT / "Content" / name) for name in NATIVE_PACKS]

    audio_root = STAGING / "cplomedia_spaceship"
    sounds = {}
    for role, (relative, looping) in AUDIO.items():
        sounds[role] = extract_wave(audio_root / relative, PRIVATE / "Audio" / f"{role}.wav", looping)

    if not DRONE.is_file():
        raise FileNotFoundError(DRONE)
    drone_copy = PRIVATE / "Source/StationDrone.glb"
    drone_copy.parent.mkdir(parents=True, exist_ok=True)
    if not drone_copy.exists():
        shutil.copy2(DRONE, drone_copy)
    if sha(drone_copy) != sha(DRONE):
        raise RuntimeError("Drone source copy differs from the preserved Fab download")

    receipt = {
        "status": "OWNED_SOURCES_STAGED_FOR_PRIVATE_UNREAL_IMPORT",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "native_packs": packs,
        "audio": sounds,
        "drone": {"source": str(DRONE.relative_to(ROOT)), "source_sha256": sha(DRONE),
                  "copy": str(drone_copy.relative_to(ROOT)), "copy_sha256": sha(drone_copy)},
        "limits": [
            "No Fab source file was modified or deleted.",
            "Audio selection is a first integration pass; listening acceptance remains open.",
            "Private Content and authoring output are excluded from Git and need separate backup.",
        ],
    }
    (PRIVATE / "Preparation.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"native_packs": len(packs), "audio_roles": len(sounds),
                      "receipt": str(PRIVATE / "Preparation.json")}))


if __name__ == "__main__":
    main()
