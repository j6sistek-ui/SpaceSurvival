"""Guarded v6 content adoption; default dry run, no engine launch.

Only new PolishV6 meshes/FX and the existing comparison map are writable.
Receipts and map recovery are unique D: files. Repeated apply refuses a changed baseline.
"""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import uuid

WORK = Path(__file__).resolve().parent
API = runpy.run_path(str(WORK / 'snapshot_cryo_v5.py'))
OUT, OWNER, STAGE, REL, sha, snapshot = (API[k] for k in ('OUT', 'OWNER', 'STAGE', 'NAMESPACE', 'sha', 'snapshot'))
PREFIX = REL.as_posix() + '/'
MAP = PREFIX + 'Maps/L_CryoComparison.umap'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def normal(mapping):
    result = {name.replace('\\', '/'): digest for name, digest in mapping.items()}
    assert len(result) == len(mapping), 'Ambiguous path spelling'
    for name in result:
        assert not Path(name).is_absolute() and '..' not in Path(name).parts, 'Unsafe relative path'
    return result


def checked(root, name):
    destination = (root / name).resolve()
    assert destination.is_relative_to(root.resolve()), 'Path leaves approved root'
    return destination


def no_native_processes():
    command = "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(UnrealEditor.*|UnrealBuildTool|ShaderCompileWorker|SpaceSurvival.*)\\.exe$' } | Select-Object Name,ProcessId | ConvertTo-Json -Compress"
    result = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', command],
                            check=True, capture_output=True, text=True)
    assert not result.stdout.strip(), 'Close Unreal/build processes before adopting content'


def main(apply=False):
    baseline_path = WORK / 'CryoPolishV6Baseline.json'
    author_path = WORK / 'CryoPolishV6Apply.json'
    visual_path = WORK / 'CryoPolishV6VisualReview.json'
    baseline, author = read(baseline_path), read(author_path)
    before, after = normal(author['native_before_hashes']), normal(author['native_after_hashes'])
    previous = normal(baseline['native'])
    assert author['status'] == 'POLISH_V6_SAVED_PENDING_VISUAL_REVIEW' and not author['errors']
    assert author['baseline_sha256'] == sha(baseline_path), 'Wrong baseline'
    assert before == normal(baseline['native_all']), 'Author did not start from v5 baseline'
    assert set(before) <= set(after), 'Existing native package removed'
    expected = {p: h for p, h in after.items() if p.startswith(PREFIX)}
    changed = sorted(p for p in before if before[p] != after[p])
    assert changed == [MAP], 'Only the comparison map may replace an existing package'
    new = sorted(set(after) - set(before))
    assert new and all(p.startswith(PREFIX + 'Meshes/PolishV6/') or
                       (p.startswith(PREFIX + 'FX/') and p.endswith('V6.uasset')) for p in new), 'Unexpected new package'
    assert snapshot(OWNER, REL) == previous, 'Owner namespace changed since baseline'
    assert snapshot(STAGE, REL) == expected, 'Stage namespace changed after authoring'
    assert all(sha(checked(STAGE, p)) == h for p, h in after.items()), 'Stage dependency changed'
    assert all(sha(checked(OWNER, p)) == h for p, h in before.items()), 'Owner dependency changed'
    assert all(sha(checked(OWNER, p)) == h for p, h in baseline['owner_protected'].items()), 'Owner protected file changed'
    assert all(sha(p) == h for p, h in baseline['source_glbs'].items()), 'Original GLB changed'
    visual = read(visual_path) if visual_path.exists() else {}
    if apply:
        assert visual.get('accepted') is True, 'Exact lead visual review is required'
        assert visual['manifest_sha256'] == author['manifest_sha256'], 'Visual revision mismatch'
        for kind in ('angles', 'interaction'):
            item = visual[kind]
            assert sha(item['path']) == item['sha256'], 'Visual evidence changed'
            proof = read(item['path'])
            assert not proof['errors'] and proof['fit_manifest_sha256'] == author['manifest_sha256']
            wanted = 'NATIVE_POLISH_V6_CAPTURED_PENDING_VISUAL_REVIEW' if kind == 'angles' else 'FOUR_NATIVE_FREEZE_CYCLES_VERIFIED_PENDING_VISUAL_REVIEW'
            assert proof['status'] == wanted and len(proof['screenshots']) == (48 if kind == 'angles' else 19)
            assert all(sha(shot['png']) == shot['sha256'] for shot in proof['screenshots']), 'Accepted capture changed'
            if kind == 'angles':
                assert proof['analysis']['eight_idle_jets_active_throughout']
            else:
                assert proof['idle_jet_component_count'] == 8
            assert normal(proof['protected_native_hashes']) == after
            assert proof['native_hashes_unchanged'] and proof['original_source_hashes_unchanged']
        no_native_processes()
    token = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '_' + uuid.uuid4().hex[:8]
    receipt = OUT / ('native-adoption-v6-' + ('apply-' if apply else 'dry-run-') + token + '.json')
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'apply': apply,
              'status': 'DRY_RUN_READY_V6_CONTENT_ONLY', 'destination': str(OWNER / REL),
              'baseline_sha256': sha(baseline_path), 'author_receipt_sha256': sha(author_path),
              'manifest_sha256': author['manifest_sha256'], 'changed_existing': changed, 'new_packages': new,
              'owner_source_config_plugin_unchanged': True, 'visual_review': str(visual_path),
              'files': [{'relative_path': p[len(PREFIX):], 'sha256': h, 'bytes': (STAGE / p).stat().st_size}
                        for p, h in sorted(expected.items())], 'copied': []}
    # Reserve the exact receipt before any owner mutation; never overwrite another run.
    with receipt.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2)
    if apply:
        backup = WORK / ('owner-polish-v6-backup-' + token)
        backup.mkdir(exist_ok=False)
        recovery = backup / 'L_CryoComparison.umap'
        shutil.copy2(OWNER / MAP, recovery)
        assert sha(recovery) == previous[MAP]
        report['backup_map'] = str(recovery)
        report['status'] = 'APPLY_IN_PROGRESS'
        try:
            for name in new:
                destination = checked(OWNER, name)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open('xb') as output, (STAGE / name).open('rb') as source:
                    shutil.copyfileobj(source, output)
                assert sha(destination) == after[name]
                report['copied'].append(name)
            assert sha(OWNER / MAP) == previous[MAP], 'Map changed during adoption'
            destination = checked(OWNER, MAP)
            temporary = destination.with_name(destination.name + '.' + token + '.pending')
            with temporary.open('xb') as output, (STAGE / MAP).open('rb') as source:
                shutil.copyfileobj(source, output)
            assert sha(temporary) == after[MAP]
            os.replace(temporary, destination)
            report['copied'].append(MAP)
            assert snapshot(OWNER, REL) == expected
            assert all(sha(checked(OWNER, p)) == h for p, h in baseline['owner_protected'].items())
            assert all(sha(checked(OWNER, p)) == h for p, h in after.items())
            report['status'] = 'ADOPTED_V6_CONTENT_ONLY_HASH_VERIFIED'
        except Exception as error:
            report['status'] = 'FAILED_PARTIAL_APPLY_REQUIRES_INSPECTION'
            report['error'] = str(error)
            raise
        finally:
            receipt.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'new': len(new), 'replaced': changed, 'receipt': str(receipt)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    main(parser.parse_args().apply)
