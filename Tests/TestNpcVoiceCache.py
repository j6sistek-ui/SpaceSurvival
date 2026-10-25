"""CPU-only voice cache compatibility and real prerender read/write regression checks."""
import contextlib
import importlib.util
import io
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("director_voice_server", ROOT / "Tools/NpcTalk/director_voice_server.py")
VOICE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VOICE)


class VoiceCacheTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / "Artifacts/VoiceCacheTests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def profile(self, name, settings=None):
        # The parser only discovers filenames; no model or reference audio is loaded by these tests.
        (self.folder / (name + ".wav")).write_bytes(b"reference fixture")
        if settings is not None:
            (self.folder / (name + ".txt")).write_text(settings, encoding="utf-8-sig")

    def test_legacy_goldens_omitted_and_empty_revision(self):
        vectors = [
            ("predator_ref_cut.wav", .92, "entity", "Fetch.", "abb6b07d574d96cb727ac1df10ad746e"),
            ("Joy.wav", .90, "none", "Only if we make one very important decision.", "9098a8788d3990c0fdfa04178c4bde80"),
        ]
        for reference, speed, treatment, text, expected in vectors:
            with self.subTest(reference=reference):
                args = (reference, speed, treatment, text)
                self.assertEqual(VOICE.cache_key(*args), expected)
                self.assertEqual(VOICE.cache_key(*args, ""), expected)

    def test_revision_goldens_shared_with_native_automation(self):
        self.assertEqual(
            VOICE.cache_key("Joy.wav", .90, "none", "Only if we make one very important decision.", "reference-v2"),
            "238e7861397bccd3156c587ef4c16f9a",
        )
        self.assertEqual(VOICE.cache_key("Astra.wav", .88, "none", "Café.", "révision-2"),
                         "99f23596df069069a86f71559a2ec524")

    def test_profile_revision_is_optional_and_voice_local(self):
        self.profile("Joy", "speed=0.9\nTreatment=None\nCache_Revision = reference-v2  \n")
        self.profile("Astra", "speed=0.88\n")
        self.profile("Director")
        voices = VOICE.read_voices(self.folder)
        self.assertEqual(voices["joy"]["cache_revision"], "reference-v2")
        self.assertEqual(voices["joy"]["speed"], .9)
        self.assertEqual(voices["joy"]["treatment"], "none")
        self.assertEqual(voices["astra"]["cache_revision"], "")
        self.assertEqual(voices["director"]["cache_revision"], "")

    def test_explicit_empty_revision_clears_prior_setting(self):
        self.profile("Joy", "cache_revision=old\ncache_revision= \n")
        self.assertEqual(VOICE.read_voices(self.folder)["joy"]["cache_revision"], "")

    def test_prerender_replaces_only_revised_voice_and_reuses_it_next_time(self):
        text = "Only if we make one very important decision."
        self.profile("Joy", "speed=0.9\ncache_revision=reference-v2\n")
        self.profile("Astra", "speed=0.88\n")
        voices = VOICE.read_voices(self.folder)
        lines = self.folder / "lines.txt"
        lines.write_text(text + "\n", encoding="utf-8")
        cache = self.folder / "cache"
        cache.mkdir()
        args = SimpleNamespace(prerender=str(lines), cache=str(cache), check=None)
        joy, astra = voices["joy"], voices["astra"]
        old = cache / (VOICE.cache_key(joy["reference"], joy["speed"], joy["treatment"], text) + ".pcm")
        astra_path = cache / (VOICE.cache_key(astra["reference"], astra["speed"], astra["treatment"], text) + ".pcm")
        old.write_bytes(b"old Joy cache retained")
        astra_path.write_bytes(b"Astra cache retained")
        calls = []
        pcm = struct.pack("<hh", 123, -123)

        def fake_speak(voice, line, pace):
            calls.append((voice["name"], line, pace))
            return pcm, 48000

        with contextlib.redirect_stdout(io.StringIO()):
            VOICE.prerender(args, joy, fake_speak)
            VOICE.prerender(args, joy, fake_speak)
            VOICE.prerender(args, astra, fake_speak)
        self.assertEqual(calls, [("Joy", text, 1.0)])
        revised = cache / "238e7861397bccd3156c587ef4c16f9a.pcm"
        self.assertEqual(revised.read_bytes(), struct.pack("<i", 48000) + pcm + bytes(24000))
        self.assertEqual(old.read_bytes(), b"old Joy cache retained")
        self.assertEqual(astra_path.read_bytes(), b"Astra cache retained")
        self.assertEqual(len(list(cache.glob("*.pcm"))), 3)

    def test_prerender_accepts_legacy_profile_without_revision_field(self):
        text = "Fetch."
        lines = self.folder / "lines.txt"
        lines.write_text(text + "\n", encoding="utf-8")
        profile = {"name": "Director", "reference": "predator_ref_cut.wav", "speed": .92, "treatment": "entity"}
        args = SimpleNamespace(prerender=str(lines), cache=str(self.folder), check=None)
        original = self.folder / "abb6b07d574d96cb727ac1df10ad746e.pcm"
        original.write_bytes(b"legacy cache retained")
        with contextlib.redirect_stdout(io.StringIO()):
            VOICE.prerender(args, profile, lambda *_: self.fail("Legacy cached line must not be generated again"))
        self.assertEqual(original.read_bytes(), b"legacy cache retained")


if __name__ == "__main__":
    unittest.main()
