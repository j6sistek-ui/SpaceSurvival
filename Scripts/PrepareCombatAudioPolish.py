"""Compose short role-specific combat cues from owned PCM; never modify source downloads.

Uses the already installed NumPy runtime. Outputs private WAVs and a reproducible
measurement/audition receipt under .agent/local. Measurements are not listening acceptance.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import struct
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OWNED = ROOT / "User downloaded assets/SpaceSurvival/Content/cplomedia_spaceship"
OUT = ROOT / ".agent/local/CombatAudioPolish"
RATE = 48000
SOURCES = {
    "laser": "weapons/WAV/aliengun001singleshot.uasset",
    "cannon": "weapons/WAV/aliengun004singleshot.uasset",
    "click": "shipsounds/WAV/mechanic05.uasset",
    "crunch": "shipsounds/WAV/mechanic01.uasset",
    "body": "shipsounds/WAV/mechanic06.uasset",
    "boom": "explosions/WAV/explosion05.uasset",
    "debris": "explosions/WAV/explosion24.uasset",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pcm(path: Path) -> np.ndarray:
    payload = path.read_bytes()
    offset = payload.find(b"RIFF")
    if offset < 0:
        raise RuntimeError(f"No embedded source PCM: {path}")
    size = struct.unpack_from("<I", payload, offset + 4)[0] + 8
    riff = payload[offset:offset + size]
    if len(riff) != size or riff[8:12] != b"WAVE":
        raise RuntimeError(f"Invalid embedded source PCM: {path}")
    with wave.open(io.BytesIO(riff), "rb") as sound:
        if sound.getsampwidth() != 2:
            raise RuntimeError("This inspected palette expects 16-bit source PCM")
        signal = np.frombuffer(sound.readframes(sound.getnframes()), "<i2").astype(np.float64)
        signal = signal.reshape(-1, sound.getnchannels()).mean(axis=1) / 32768.0
        source_rate = sound.getframerate()
    if source_rate != RATE:
        signal = np.interp(np.arange(round(len(signal) * RATE / source_rate)) * source_rate / RATE,
                           np.arange(len(signal)), signal)
    return signal


def band(signal: np.ndarray, low: float, high: float) -> np.ndarray:
    # Smooth fourth-order spectral slopes avoid hard brick-wall ringing. Pad beyond the
    # complete cue, then discard the padded tail; no circular tail wraps into the attack.
    count = 1 << (max(1, 2 * len(signal)) - 1).bit_length()
    hz = np.fft.rfftfreq(count, 1 / RATE)
    highpass = (hz / max(1, low)) ** 4
    response = highpass / (1 + highpass) / (1 + (hz / high) ** 4)
    return np.fft.irfft(np.fft.rfft(signal, count) * response, count)[:len(signal)]


def layer(source: np.ndarray, seconds: float, pitch: float, low: float, high: float,
          decay: float, start: float = 0.0) -> np.ndarray:
    times = np.arange(round(seconds * RATE)) / RATE
    signal = np.interp((start + times * pitch) * RATE, np.arange(len(source)), source, left=0, right=0)
    signal = band(signal, low, high)
    peak = float(np.max(np.abs(signal)))
    if peak < 1e-8:
        raise RuntimeError("Selected source layer is silent")
    signal /= peak
    # Two-millisecond attack and finite release prevent clicks at either end.
    envelope = np.minimum(times / .002, 1) * np.exp(-times / decay)
    envelope *= np.clip((seconds - times) / min(.035, seconds * .25), 0, 1) ** 2
    shaped = signal * envelope
    return shaped / max(float(np.max(np.abs(shaped))), 1e-8)


def put(target: np.ndarray, signal: np.ndarray, at: float = 0.0, gain: float = 1.0) -> None:
    first = round(at * RATE)
    count = min(len(signal), len(target) - first)
    target[first:first + count] += signal[:count] * gain


def master(signal: np.ndarray, peak_db: float) -> np.ndarray:
    signal -= np.mean(signal)
    signal = band(signal, 28, 11000)
    # Reshape only incidental summed peaks; leave the transient/body envelope intact.
    signal = np.tanh(signal * 1.15)
    signal *= 10 ** (peak_db / 20) / max(float(np.max(np.abs(signal))), 1e-8)
    edge = min(96, len(signal) // 4)
    signal[:edge] *= np.linspace(0, 1, edge)
    signal[-edge:] *= np.linspace(1, 0, edge)
    return signal


def metrics(signal: np.ndarray) -> dict:
    peak = max(float(np.max(np.abs(signal))), 1e-12)
    rms = max(float(np.sqrt(np.mean(signal * signal))), 1e-12)
    power = np.abs(np.fft.rfft(signal)) ** 2
    hz = np.fft.rfftfreq(len(signal), 1 / RATE)
    total = max(float(power.sum()), 1e-12)
    # Sample-peak and band-energy measurements; no ITU true-peak certification is claimed.
    return {
        "seconds": round(len(signal) / RATE, 4), "sample_rate": RATE, "channels": 1,
        "peak_dbfs": round(20 * np.log10(peak), 3), "rms_dbfs": round(20 * np.log10(rms), 3),
        "crest_db": round(20 * np.log10(peak / rms), 3),
        "energy_below_250hz": round(float(power[hz < 250].sum()) / total, 5),
        "energy_above_1200hz": round(float(power[hz > 1200].sum()) / total, 5),
        "energy_centroid_hz": round(float((power * hz).sum()) / total, 2),
        "dc_offset": round(float(np.mean(signal)), 7), "clipped_samples": int((np.abs(signal) >= 1).sum()),
        "edge_sample_max": round(float(max(abs(signal[0]), abs(signal[-1]))), 8),
    }


def write_wav(path: Path, signal: np.ndarray) -> None:
    if np.max(np.abs(signal)) >= 1:
        raise RuntimeError(f"Refusing clipped mix: {path}")
    with wave.open(str(path), "wb") as sound:
        sound.setnchannels(1)
        sound.setsampwidth(2)
        sound.setframerate(RATE)
        sound.writeframes(np.round(signal * 32767).astype("<i2").tobytes())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source_hashes = {name: sha(OWNED / path) for name, path in SOURCES.items()}
    samples = {name: read_pcm(OWNED / path) for name, path in SOURCES.items()}
    cues = {}
    laser = np.zeros(round(.115 * RATE))
    put(laser, layer(samples["laser"], .115, 1.05, 300, 8500, .055), gain=.82)
    put(laser, layer(samples["crunch"], .04, 1.25, 1800, 9500, .012), gain=.22)
    put(laser, layer(samples["cannon"], .085, 1.1, 95, 360, .025), gain=.30)
    cues["Laser"] = master(laser, -10)

    cannon = np.zeros(round(.46 * RATE))
    put(cannon, layer(samples["cannon"], .34, .83, 100, 3800, .12), gain=.50)
    put(cannon, layer(samples["boom"], .46, 1.0, 35, 160, .19, start=.50), gain=.85)
    put(cannon, layer(samples["crunch"], .09, .72, 700, 5500, .025), gain=.28)
    cues["Cannon"] = master(cannon, -8)

    impact = np.zeros(round(.44 * RATE))
    put(impact, layer(samples["body"], .40, .86, 55, 650, .12, start=.12), gain=.65)
    put(impact, layer(samples["crunch"], .20, .65, 350, 4200, .05, start=.25), gain=.60)
    put(impact, layer(samples["boom"], .33, 1.15, 40, 160, .09, start=.50), gain=.35)
    cues["Impact"] = master(impact, -9)

    debris = np.zeros(round(.60 * RATE))
    put(debris, layer(samples["debris"], .50, 1.18, 160, 2100, .14), gain=.50)
    put(debris, layer(samples["body"], .30, 1.1, 80, 500, .07), gain=.26)
    for index, at in enumerate((0, .043, .103, .184, .285)):
        put(debris, layer(samples["crunch"], .13, .75 + index * .09, 600, 5600, .035,
                         start=index * .071), at, .48 * .78 ** index)
    cues["DebrisBreak"] = master(debris, -10)

    records = {}
    for role, signal in cues.items():
        path = OUT / f"{role}.wav"
        write_wav(path, signal)
        records[role] = {**metrics(signal), "wav": str(path.relative_to(ROOT)), "sha256": sha(path), "loop": False}
    # Mix repeated fire at the real baseline weapon intervals, without a safety limiter,
    # so the receipt proves source headroom instead of hiding clipping after summation.
    laser_train = np.zeros(2 * RATE)
    for index in range(12):
        put(laser_train, cues["Laser"], index * .12)
    stress = np.zeros(4 * RATE)
    for index in range(24):
        put(stress, cues["Laser"], index * .12)
    for at in (.18, 1.03, 1.88):
        put(stress, cues["Cannon"], at)
    for at in (.35, 1.1, 2.1):
        put(stress, cues["DebrisBreak"], at, .8)
    put(stress, cues["Impact"], .35, .9)
    if np.max(np.abs(stress)) >= .95:
        raise RuntimeError("Dense combat stress mix lacks headroom; revise cue layering")
    audition = np.zeros(14 * RATE)
    timeline = [
        ("Original laser x6", .25, "laser"), ("New laser x6", 2.0, "Laser"),
        ("New heavy cannon x2", 3.65, "Cannon"), ("Original hull click", 6.0, "click"),
        ("New hull crunch", 7.8, "Impact"), ("New rock breakup", 9.1, "DebrisBreak"),
        ("Mixed sustained combat", 10.0, "stress"),
    ]
    for label, at, role in timeline:
        if role == "stress":
            put(audition, stress, at)
        elif "x6" in label:
            signal = cues[role] if role in cues else samples[role] * .45
            for index in range(6):
                put(audition, signal, at + index * .12)
        elif "x2" in label:
            for index in range(2):
                put(audition, cues[role], at + index * .85)
        else:
            put(audition, cues[role] if role in cues else samples[role], at)
    write_wav(OUT / "CombatAudio-Audition.wav", audition)
    report = {
        "status": "MEASURED_PRIVATE_WAV_AUDITION_NOT_LISTENING_OR_RUNTIME_ACCEPTANCE",
        "recipe": "CombatPolish1", "sources": {name: {"path": str((OWNED / relative).relative_to(ROOT)),
            "sha256": source_hashes[name], "metrics": metrics(samples[name])} for name, relative in SOURCES.items()},
        "outputs": records, "laser_train": metrics(laser_train), "combat_stress": metrics(stress),
        "audition": {"wav": str((OUT / "CombatAudio-Audition.wav").relative_to(ROOT)),
                     "sha256": sha(OUT / "CombatAudio-Audition.wav"), "timeline": timeline},
        "vendor_unchanged": all(sha(OWNED / SOURCES[name]) == value for name, value in source_hashes.items()),
        "limits": ["No device audio playback or listening acceptance performed.",
                   "Headroom test is a bounded fixture, not every possible live mix or ITU true-peak certification.",
                   "Private WAV and Unreal assets require local backup; vendor PCM must not be committed."]}
    assert report["vendor_unchanged"]
    assert records["Cannon"]["energy_below_250hz"] > records["Laser"]["energy_below_250hz"]
    assert records["DebrisBreak"]["energy_above_1200hz"] > .03
    (OUT / "Preparation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"outputs": records, "stress": report["combat_stress"], "vendor_unchanged": True}, indent=2))


if __name__ == "__main__":
    main()
