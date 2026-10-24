"""Capture the installed v5.4 baseline before bounded core/idle-jet polish."""
from datetime import datetime, timezone
import json
from pathlib import Path
import runpy

WORK = Path(__file__).resolve().parent
API = runpy.run_path(str(WORK / 'snapshot_cryo_v5.py'))
OUT, OWNER, STAGE, REL, sha, snapshot = (API[k] for k in ('OUT', 'OWNER', 'STAGE', 'NAMESPACE', 'sha', 'snapshot'))


def main():
    receipt = WORK / 'CryoPolishV6Baseline.json'
    if receipt.exists():
        raise RuntimeError('Never overwrite the pre-v6 baseline')
    previous_path = OUT / 'native-adoption-v5.json'
    previous = json.loads(previous_path.read_text())
    author_path = WORK / 'CryoDisplayV5Apply.json'
    author = json.loads(author_path.read_text())
    expected = {(REL / row['relative_path']).as_posix(): row['sha256'] for row in previous['files']}
    owner, stage = snapshot(OWNER, REL), snapshot(STAGE, REL)
    if owner != expected or stage != expected or len(owner) != 256:
        raise RuntimeError('Installed v5.4 owner and stage must match')
    all_native = author['native_after_hashes']
    if not all(sha(STAGE / p) == h and sha(OWNER / p) == h for p, h in all_native.items()):
        raise RuntimeError('Prior native dependency closure changed')
    protection = {}
    for folder in ('Config', 'Plugins/SSCryoRuntime/Source', 'Plugins/SSCryoRuntime/Binaries/Win64', 'Saved/SaveGames'):
        protection.update(snapshot(OWNER, folder))
    for name in ('SpaceSurvival.uproject', 'Plugins/SSCryoRuntime/SSCryoRuntime.uplugin'):
        protection[name] = sha(OWNER / name)
    original = json.loads((WORK / 'glb-baseline.json').read_text())
    sources = {row['file']: row['sha256'].lower() for row in original['assets']}
    if not all(sha(p) == h for p, h in sources.items()):
        raise RuntimeError('Original GLB changed')
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'status': 'V5_4_OWNER_AND_STAGE_MATCH',
              'owner': str(OWNER), 'stage': str(STAGE), 'native': owner, 'native_all': all_native,
              'owner_protected': protection, 'source_glbs': sources,
              'previous_author': str(author_path), 'previous_author_sha256': sha(author_path),
              'previous_adoption': str(previous_path), 'previous_adoption_sha256': sha(previous_path),
              'manifest': author['manifest'], 'manifest_sha256': author['manifest_sha256'],
              'namespace_bytes': sum((OWNER / p).stat().st_size for p in owner)}
    receipt.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'receipt': str(receipt), 'native_files': len(owner), 'native_all': len(all_native),
                      'owner_protected_files': len(protection), 'source_glbs': len(sources)}))


if __name__ == '__main__':
    main()
