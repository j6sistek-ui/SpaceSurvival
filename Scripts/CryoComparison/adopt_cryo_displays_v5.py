"""Guarded content-only v5 installation; default dry run, no Unreal launch."""
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import runpy
import shutil

WORK = Path(__file__).resolve().parent
API = runpy.run_path(str(WORK / 'snapshot_cryo_v5.py'))
OUT, OWNER, STAGE, REL, sha, snapshot = (API[k] for k in ('OUT', 'OWNER', 'STAGE', 'NAMESPACE', 'sha', 'snapshot'))
MAP = (REL / 'Maps/L_CryoComparison.umap').as_posix()


def main(apply=False):
    baseline = json.loads((WORK / 'CryoDisplayV5Baseline.json').read_text())
    author = json.loads((WORK / 'CryoDisplayV5Apply.json').read_text())
    visual_path = WORK / 'CryoDisplayV5VisualReview.json'
    visual = json.loads(visual_path.read_text()) if visual_path.exists() else {}
    expected = {k.replace('\\', '/'): h for k, h in author['native_after_hashes'].items()
                if k.replace('\\', '/').startswith(REL.as_posix() + '/')}
    previous = baseline['native']
    assert author['status'] == 'DISPLAY_V5_SAVED_PENDING_VISUAL_REVIEW'
    assert snapshot(OWNER, REL) == previous, 'Owner cryo namespace changed since baseline'
    assert snapshot(STAGE, REL) == expected, 'Stage changed after native author receipt'
    assert all(sha(OWNER / p) == h for p, h in baseline['owner_protected'].items()), 'Owner protected file changed'
    assert all(sha(p) == h for p, h in baseline['source_glbs'].items()), 'Original GLB changed'
    assert set(previous) <= set(expected), 'Existing native file removed'
    changed = [p for p in previous if previous[p] != expected[p]]
    assert changed == [MAP], 'Only the owned comparison map may replace an existing package'
    new = sorted(set(expected) - set(previous))
    assert new and all('/Meshes/DisplayV5/' in p or '/Materials/DisplayV5/' in p for p in new), 'Unexpected v5 package path'
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'apply': apply,
              'status': 'DRY_RUN_READY_V5_CONTENT_ONLY', 'destination': str(OWNER / REL),
              'changed_existing': changed, 'new_packages': new, 'owner_source_config_plugin_unchanged': True,
              'author_receipt_sha256': sha(WORK / 'CryoDisplayV5Apply.json'),
              'visual_review': str(visual_path), 'files': []}
    if apply:
        assert visual.get('accepted') is True, 'Lead visual review must pass before adoption'
        assert visual['manifest_sha256'] == author['manifest_sha256'], 'Visual review describes another revision'
        for key in ('angles', 'interaction'):
            proof = json.loads(Path(visual[key]['path']).read_text())
            assert sha(visual[key]['path']) == visual[key]['sha256'] and not proof['errors']
            assert proof['protected_native_hashes'] == author['native_after_hashes'], 'Capture package hashes differ'
        backup = WORK / ('owner-display-v5-backup-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
        backup.mkdir(exist_ok=False)
        source = OWNER / MAP
        shutil.copy2(source, backup / source.name)
        assert sha(backup / source.name) == previous[MAP]
        report['backup_map'] = str(backup / source.name)
        for name in new + changed:
            destination = OWNER / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(STAGE / name, destination)
            assert sha(destination) == expected[name]
        assert snapshot(OWNER, REL) == expected
        assert all(sha(OWNER / p) == h for p, h in baseline['owner_protected'].items())
        report['status'] = 'ADOPTED_V5_CONTENT_ONLY_HASH_VERIFIED'
    for name, digest in sorted(expected.items()):
        report['files'].append({'relative_path': Path(name).relative_to(REL).as_posix(),
                                'sha256': digest, 'bytes': (STAGE / name).stat().st_size})
    revision = author.get('revision', 'v5')
    assert revision in ('v5', 'v5_3', 'v5_4'), 'Unexpected authored revision'
    destination = OUT / ('native-adoption-v5.json' if apply else f'native-adoption-v5-dry-run-{revision}.json')
    assert not destination.exists(), 'Do not overwrite an adoption receipt'
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'new': len(new), 'replaced': changed, 'receipt': str(destination)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    main(parser.parse_args().apply)
