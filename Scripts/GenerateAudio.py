"""Original, deterministic provisional Phase 1 sound sources (stdlib only).

Run with Python 3 or Unreal's bundled Python. These are source WAVs, not a
claim of a mixed, playtested commercial score. All music stems share the same
20-second / 8-bar / 96 BPM grid and D-minor harmonic center.
"""
from array import array
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ContentSource" / "Audio"
TAU = math.tau
RATE = 32000


def sine(hz, t):
    return math.sin(TAU * hz * t)


def decay(t, attack=0.008, release=0.16):
    return min(1.0, t / attack) * math.exp(-t / release)


def write_sound(name, duration, sample, stereo=False, loop=False):
    """No normalization: retain authored relative loudness and 3dB headroom."""
    rng = random.Random(517 + sum(map(ord, name)))
    count = round(duration * RATE)
    pcm = array("h")
    peak = 0.0
    energy = 0.0
    for index in range(count):
        t = index / RATE
        value = sample(t, rng)
        values = value if isinstance(value, tuple) else (value,)
        if stereo and len(values) == 1:
            values = values * 2
        # Smooth the boundary of one-shots; loops are periodic by construction.
        fade = 1.0 if loop else min(1.0, t / 0.004, (duration - t) / 0.025)
        for v in values:
            v *= max(0.0, fade)
            if abs(v) >= 0.9:
                raise ValueError(f"{name}: authored sample clips at {t:.4f}s")
            peak = max(peak, abs(v))
            energy += v * v
            pcm.append(round(v * 32767))
    if sys.byteorder != "little":
        pcm.byteswap()
    filename = OUT / f"{name}.wav"
    with wave.open(str(filename), "wb") as wav:
        wav.setnchannels(2 if stereo else 1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(pcm.tobytes())
    return {"name": name, "seconds": duration, "sample_rate": RATE,
            "channels": 2 if stereo else 1, "loop": loop,
            "peak_dbfs": round(20 * math.log10(max(peak, 1e-8)), 2),
            "rms_dbfs": round(10 * math.log10(max(energy / len(pcm), 1e-12)), 2),
            "sha256": hashlib.sha256(filename.read_bytes()).hexdigest()}


def engine(t, _rng):
    # Whole-cycle tones on a 4s loop, with no randomly discontinuous noise.
    rumble = (0.13 * sine(42, t) + 0.065 * sine(84, t) + 0.028 * sine(126, t))
    turbine = 0.023 * sine(378 + 0.6 * sine(0.5, t), t)
    return rumble * (0.87 + 0.1 * sine(0.75, t)) + turbine


def laser(t, _rng):
    phase = 920 * t - 680 * t * t
    return decay(t, 0.002, 0.07) * (0.28 * math.sin(TAU * phase) + 0.07 * sine(1740, t))


def cannon(t, rng):
    return decay(t, 0.002, 0.15) * (0.36 * sine(65, t) + 0.11 * rng.uniform(-1, 1)) + 0.12 * decay(t, 0.002, 0.04) * sine(160, t)


def impact(t, rng):
    return decay(t, 0.001, 0.20) * (0.20 * rng.uniform(-1, 1) + 0.18 * sine(53, t) + 0.04 * sine(183, t))


def pickup(t, _rng):
    return sum(0.12 * decay(t - start, 0.006, 0.12) * sine(hz, t - start)
               for start, hz in ((0, 587.33), (0.065, 880), (0.13, 1174.66)) if t >= start)


def alarm(t, _rng):
    pulse = t % 0.32
    return 0.20 * decay(pulse, 0.012, 0.055) * (sine(660, t) + 0.25 * sine(990, t))


def station(t, _rng):
    return 0.045 * sine(60, t) + 0.018 * sine(120, t) + 0.014 * sine(180, t) * (0.65 + 0.3 * sine(0.25, t))


def music(t, layer):
    # Frequencies quantized to loop duration ensure phase-continuous seams.
    fundamental = (73.4, 87.3, 110.0, 130.8)
    left = right = 0.0
    if layer == "base":
        for i, hz in enumerate(fundamental):
            amp = 0.030 * (0.85 + 0.15 * math.cos(TAU * (t / 20 + i / 4)))
            left += amp * sine(hz, t)
            right += amp * sine(hz + 0.05, t)
        return left, right
    beat = 0.625
    if layer == "pressure":
        pulse = t % (beat / 2)
        hz = fundamental[int(t / beat) % 4] * 2
        env = decay(pulse, 0.006, 0.085)
        # Restart note phase at pulse boundaries; envelope begins at zero.
        signal = 0.058 * env * (sine(hz, pulse) + 0.15 * sine(hz * 2, pulse))
        tick = 0.018 * decay(t % beat, 0.002, 0.025) * sine(1200, t % beat)
        return signal + tick, signal - tick * 0.2
    pulse = t % beat
    kick = 0.085 * decay(pulse, 0.004, 0.14) * sine(49, pulse)
    shimmer = 0.015 * (0.5 + 0.5 * sine(0.4, t)) * sine(587.3, t)
    note = (293.65, 349.25, 440.0, 523.25)[int(t / 2.5) % 4]
    motif = 0.038 * decay(t % 2.5, 0.08, 0.8) * sine(note, t % 2.5)
    return kick + shimmer + motif, kick - shimmer + motif


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = []
    for name, seconds, fn, loop in (
        ("Engine", 4, engine, True), ("Laser", 0.25, laser, False),
        ("Cannon", 0.7, cannon, False), ("Impact", 0.8, impact, False),
        ("Pickup", 0.55, pickup, False), ("Alarm", 0.65, alarm, False),
        ("Station", 4, station, True),
    ):
        result.append(write_sound(name, seconds, fn, loop=loop))
    for name, layer in (("MusicBase", "base"), ("MusicPressure", "pressure"), ("MusicClimax", "climax")):
        result.append(write_sound(name, 20, lambda t, rng, l=layer: music(t, l), stereo=True, loop=True))
    manifest = {"status": "Generated provisional audio; Unreal mix/listening validation pending",
                "source": "Original mathematical synthesis; no samples or external assets",
                "music": {"bpm": 96, "bars": 8, "beats_per_bar": 4, "key": "D minor", "seconds": 20},
                "assets": result}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(result)} original WAV sources in {OUT}")
    return manifest


if __name__ == "__main__":
    main()
