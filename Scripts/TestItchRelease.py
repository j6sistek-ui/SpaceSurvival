"""Release safety regression checks; synthetic payloads, no network or real game writes."""
import json
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

    def test_reject_matching_receipt_with_runtime_user_state(self):
        for relative in ('SpaceSurvival/SaVeD/Config/Windows/Game.ini',
                         'SpaceSurvival/Saved/SaveGames/Account.sav',
                         'outside/Profile.SAV', 'outside/Session.LOG'):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                private = root / relative
                private.parent.mkdir(parents=True, exist_ok=True)
                private.write_bytes(b'private user state')
                receipt = {'files': release.entries(root), 'target': release.TARGET}
                with self.assertRaisesRegex(ValueError, 'Runtime user state'):
                    release.check(root, receipt)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'sAvEd').mkdir()
            with self.assertRaisesRegex(ValueError, 'Runtime user state'):
                release.check(root, {'files': [], 'target': release.TARGET})

    def test_prepare_excludes_runtime_state_and_preserves_package(self):
        required = {'SpaceSurvival.exe', 'SpaceSurvival/Binaries/Win64/SpaceSurvival.exe',
                    'Engine/Extras/Redist/en-us/vc_redist.x64.exe', 'NOTICES.txt', 'THIRD_PARTY.md'}
        private = {'SpaceSurvival/SaVeD/Config/Windows/Game.ini',
                   'SpaceSurvival/Saved/Logs/Game.log',
                   'SpaceSurvival/Saved/SaveGames/Account.sav',
                   'outside/Profile.SAV', 'outside/Session.LOG'}
        original_root = release.ROOT
        with tempfile.TemporaryDirectory() as temp:
            try:
                release.ROOT = Path(temp)
                package = release.ROOT / 'Artifacts/Windows'
                for relative in required | private | {'SpaceSurvival/Binaries/Win64/Game.pdb'}:
                    path = package / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(relative.encode('utf-8'))
                before = release.entries(package)
                audit = release.ROOT / 'audit.json'
                audit.write_text(json.dumps({'source_commit': 'synthetic-source',
                    'archive_files': [dict(row, path=release.PREFIX + row['path']) for row in before]}))
                release.prepare('0.1-test', audit)
                stage = release.ROOT / 'Artifacts/Releases/0.1-test/payload'
                receipt = json.loads((stage.parent / 'release.json').read_text())
                release.check(stage, receipt)
                self.assertEqual({row['path'] for row in receipt['files']},
                                 required | {'.itch.toml', 'VERSION.txt', 'PLAYTEST.txt'})
                for relative in required:
                    self.assertEqual((stage / relative).read_bytes(), (package / relative).read_bytes())
                self.assertEqual(release.entries(package), before)
                with self.assertRaisesRegex(ValueError, 'already exists'):
                    release.prepare('0.1-test', audit)
            finally:
                release.ROOT = original_root

    def test_reject_other_target(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                release.check(Path(temp), {'files': [], 'target': 'wrong/game:windows'})

    def test_existing_version_is_immutable(self):
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
