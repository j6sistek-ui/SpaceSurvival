"""Read-only pre-v5 inventory; preserves the owned v4 baseline for guarded adoption."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parent
OUT = WORK.parent / 'outputs/Cryo_Comparison'
OWNER = Path('C:/Users/j6sis/SpaceSurvival')
STAGE = WORK / 'CryoStage'
NAMESPACE = Path('Content/SpaceSurvival/CryoComparison')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4194304), b''):
            h.update(block)
    return h.hexdigest()


def snapshot(root, folder):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted((root / folder).rglob('*')) if p.is_file()}


def main():
    receipt = WORK / 'CryoDisplayV5Baseline.json'
    assert not receipt.exists(), 'Never overwrite the pre-v5 baseline'
    previous = json.loads((OUT / 'native-adoption-v4.json').read_text())
    expected = {(NAMESPACE / r['relative_path']).as_posix(): r['sha256'] for r in previous['files']}
    owner = snapshot(OWNER, NAMESPACE)
    stage = snapshot(STAGE, NAMESPACE)
    assert expected == owner == stage, 'Current native content differs from adopted v4; inspect before editing'
    protection = {}
    for folder in ('Config', 'Plugins/SSCryoRuntime/Source', 'Plugins/SSCryoRuntime/Binaries/Win64', 'Saved/SaveGames'):
        protection.update(snapshot(OWNER, folder))
    for name in ('SpaceSurvival.uproject', 'Plugins/SSCryoRuntime/SSCryoRuntime.uplugin'):
        protection[name] = sha(OWNER / name)
    original = json.loads((WORK / 'glb-baseline.json').read_text())
    sources = {r['file']: r['sha256'].lower() for r in original['assets']}
    assert all(sha(p) == h for p, h in sources.items())
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'status': 'V4_OWNER_AND_STAGE_MATCH',
              'owner': str(OWNER), 'stage': str(STAGE), 'native': owner,
              'owner_protected': protection, 'source_glbs': sources,
              'namespace_bytes': sum((OWNER / p).stat().st_size for p in owner)}
    receipt.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'receipt': str(receipt), 'native_files': len(owner), 'owner_protected_files': len(protection), 'source_glbs': len(sources)}))


if __name__ == '__main__':
    main()
