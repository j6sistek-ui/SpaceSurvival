"""Release safety regression checks; synthetic payloads, no network or real game writes."""
import tempfile
import unittest
from pathlib import Path
import ItchRelease as release


class ReleaseSafety(unittest.TestCase):
    def test_reject_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            for name in ('../outside', '/absolute', 'C:/outside', 'x\\y', 'x/../../outside'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    release.safe_path(Path(temp), name)

    def test_detect_content_addition_removal_and_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / 'game.exe'
            game.write_bytes(b'original')
            receipt = {'files': release.entries(root), 'target': release.TARGET}
            release.check(root, receipt)
            game.write_bytes(b'modified')
            with self.assertRaises(ValueError):
                release.check(root, receipt)
            game.write_bytes(b'original')
            extra = root / 'private-save.sav'
            extra.write_bytes(b'private')
            with self.assertRaises(ValueError):
                release.check(root, receipt)
            extra.unlink()
            game.unlink()
            with self.assertRaises(ValueError):
                release.check(root, receipt)

    def test_reject_other_target(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                release.check(Path(temp), {'files': [], 'target': 'wrong/game:windows'})

    def test_existing_version_is_immutable(self):
        import json
        original_root = release.ROOT
        with tempfile.TemporaryDirectory() as temp:
            try:
                release.ROOT = Path(temp)
                (release.ROOT / 'Artifacts/Releases/0.1/payload').mkdir(parents=True)
                receipt = release.ROOT / 'audit.json'
                receipt.write_text(json.dumps({}))
                with self.assertRaisesRegex(ValueError, 'already exists'):
                    release.prepare('0.1', receipt)
            finally:
                release.ROOT = original_root


if __name__ == '__main__':
    unittest.main()
