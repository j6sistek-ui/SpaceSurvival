"""Hash/atomicity tests in temporary directories; never modify the live vendor."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import prepare_vendor as vendor


class VendorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='motionboard-vendor-test-')
        self.root = Path(self.temporary.name)
        self.recipe = json.loads(vendor.PATCH.read_bytes())

    def tearDown(self):
        self.temporary.cleanup()

    def private_sources(self):
        missing = [name for name in vendor.FILES if not (vendor.ROOT / name).is_file()]
        if missing:
            self.skipTest('Pinned MIT vendor not prepared; no licensed media are required')
        return {name: (vendor.ROOT / name).read_bytes() for name in vendor.FILES}

    def test_unknown_loader_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unknown FBXLoader'):
            vendor.patch_loader(b'locally changed or different release', self.recipe)

    def test_wrong_upstream_recipe_is_rejected(self):
        wrong = dict(self.recipe, upstreamSha256='0'*64)
        with self.assertRaisesRegex(ValueError, 'does not target'):
            vendor.patch_loader(b'anything', wrong)

    def test_preflight_rejects_before_any_file_or_provenance_write(self):
        original = {name: b'unknown' for name in vendor.FILES}
        for name, data in original.items():
            target = self.root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        provenance = self.root/'provenance.json'
        provenance.write_bytes(b'owner provenance sentinel')
        with self.assertRaisesRegex(ValueError, 'Unknown r180 dependency'):
            vendor.prepare(self.root, fetch=lambda _: self.fail('Must not download'))
        self.assertEqual(provenance.read_bytes(), b'owner provenance sentinel')
        for name, data in original.items():
            self.assertEqual((self.root/name).read_bytes(), data)

    def test_exact_upstream_patch_and_idempotent_bootstrap(self):
        sources = self.private_sources()
        source_hashes = {name: vendor.digest(data) for name, data in sources.items()}
        # Exercise a fresh upstream install even when the local dependency has
        # already been patched. Reverse only this known test copy, never a file.
        if source_hashes[vendor.FBX] == self.recipe['patchedSha256']:
            text = sources[vendor.FBX].decode('utf-8')
            for edit in reversed(self.recipe['patches']):
                self.assertEqual(text.count(edit['new']), 1)
                text = text.replace(edit['new'], edit['old'], 1)
            sources[vendor.FBX] = text.encode('utf-8')
        self.assertEqual(vendor.digest(sources[vendor.FBX]), self.recipe['upstreamSha256'])
        records = vendor.prepare(self.root, fetch=sources.__getitem__)
        self.assertEqual(len(records), len(vendor.FILES))
        loader = self.root/vendor.FBX
        self.assertEqual(vendor.digest(loader.read_bytes()), self.recipe['patchedSha256'])
        first = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with patch.object(vendor, 'atomic_write', wraps=vendor.atomic_write) as write:
            vendor.prepare(self.root, fetch=lambda _: self.fail('Already prepared'))
            self.assertEqual([call.args[0].name for call in write.call_args_list], ['provenance.json'])
        second = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(first, second)
        self.assertEqual(source_hashes, {name: vendor.digest((vendor.ROOT/name).read_bytes()) for name in sources})
        provenance = json.loads((self.root/'provenance.json').read_bytes())
        record = next(r for r in provenance['files'] if r['file'] == vendor.FBX)
        self.assertEqual(record['upstreamSha256'], self.recipe['upstreamSha256'])
        self.assertEqual(record['patchSha256'], vendor.digest(vendor.PATCH.read_bytes()))
        self.assertEqual((self.root/'LICENSE').read_bytes(), sources['LICENSE'])

    def test_unknown_loader_preserves_existing_provenance(self):
        sources = self.private_sources()
        vendor.prepare(self.root, fetch=sources.__getitem__)
        loader = self.root/vendor.FBX
        loader.write_bytes(loader.read_bytes()+b'\n// unknown edit')
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError, 'Unknown FBXLoader'):
            vendor.prepare(self.root)
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_check_mode_does_not_create_files(self):
        sources = self.private_sources()
        records = vendor.prepare(self.root, fetch=sources.__getitem__, check=True)
        self.assertEqual(len(records), len(vendor.FILES))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_failed_atomic_replace_keeps_previous_file_and_cleans_temp(self):
        target = self.root/'test.js'
        target.write_bytes(b'previous')
        with patch.object(vendor.os, 'replace', side_effect=OSError('simulated failed replace')):
            with self.assertRaisesRegex(OSError, 'simulated'):
                vendor.atomic_write(target, b'replacement')
        self.assertEqual(target.read_bytes(), b'previous')
        self.assertEqual(list(self.root.iterdir()), [target])


if __name__ == '__main__':
    unittest.main()
