"""Prepare and explicitly publish audited Windows builds. Python standard library only."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
TARGET = 'j6sistek-ui/space-survival:windows-alpha'
PREFIX = 'Artifacts/Windows/'
EXCLUDED = {'Prerequisites.json', 'Manifest_DebugFiles_Win64.txt',
            'Manifest_NonUFSFiles_Win64.txt', 'Manifest_UFSFiles_Win64.txt'}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_path(root, relative):
    p = PurePosixPath(relative)
    if not relative or '\\' in relative or ':' in relative or p.is_absolute() or '..' in p.parts:
        raise ValueError(f'Unsafe relative path: {relative}')
    result = root.joinpath(*p.parts)
    for item in [root, result, *result.parents]:
        if item.is_symlink() or (hasattr(item, 'is_junction') and item.is_junction()):
            raise ValueError('Links/junctions are not permitted')
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError('Path escapes root')
    return result


def entries(folder):
    result = []
    for p in sorted(folder.rglob('*')):
        rel = p.relative_to(folder).as_posix()
        safe_path(folder, rel)
        if p.is_file():
            result.append({'path': rel, 'bytes': p.stat().st_size, 'sha256': sha(p)})
    return result


def runtime_user_state(relative):
    path = PurePosixPath(relative)
    return (any(part.casefold() == 'saved' for part in path.parts)
            or path.suffix.casefold() in {'.sav', '.log'})


def check(folder, receipt):
    actual = entries(folder)
    # A matching old receipt is not permission to publish personal runtime state.
    # Include directories so an empty Saved folder cannot pass verification either.
    if any(runtime_user_state(p.relative_to(folder).as_posix()) for p in folder.rglob('*')):
        raise ValueError('Runtime user state is forbidden in release payloads; prepare a fresh version')
    if actual != receipt['files']:
        raise ValueError('Release files changed or unexpected files were added; prepare a fresh version')
    if receipt['target'] != TARGET:
        raise ValueError('Unexpected publishing target')


def prepare(version, package_receipt):
    audit = json.loads(package_receipt.read_text(encoding='utf-8-sig'))
    stage = safe_path(ROOT, f'Artifacts/Releases/{version}/payload')
    if stage.parent.exists():
        raise ValueError('Version already exists; never overwrite a prepared release')
    source = ROOT / 'Artifacts/Windows'
    audited = audit['archive_files']
    selected = []
    for row in audited:
        if not row['path'].startswith(PREFIX):
            raise ValueError('Receipt contains a file outside the package')
        rel = row['path'][len(PREFIX):]
        path = safe_path(source, rel)
        if not path.is_file() or path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
            raise ValueError(f'Package no longer matches audit: {rel}')
        if rel in EXCLUDED or rel.lower().endswith('.pdb') or runtime_user_state(rel):
            continue
        selected.append((rel, path))
    required = {'SpaceSurvival.exe', 'SpaceSurvival/Binaries/Win64/SpaceSurvival.exe',
                'Engine/Extras/Redist/en-us/vc_redist.x64.exe', 'NOTICES.txt', 'THIRD_PARTY.md'}
    if not required.issubset({rel for rel, _ in selected}):
        raise ValueError('Required runtime or notices absent')
    # Verify everything before creating the version directory. Preserve original symbols locally.
    stage.mkdir(parents=True)
    for rel, path in selected:
        dest = safe_path(stage, rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        if sha(dest) != sha(path):
            raise ValueError(f'Copy verification failed: {rel}')
    manifest = '''[[actions]]
name = "play"
path = "SpaceSurvival.exe"
platform = "windows"
args = ["-SaveToUserDir"]

[[actions]]
name = "Install Microsoft Visual C++ runtime (first launch if needed)"
path = "Engine/Extras/Redist/en-us/vc_redist.x64.exe"
platform = "windows"
'''
    (stage / '.itch.toml').write_text(manifest, encoding='utf-8')
    (stage / 'VERSION.txt').write_text(version + '\n', encoding='utf-8')
    (stage / 'PLAYTEST.txt').write_text(
        f'SpaceSurvival {version}\nSource: {audit["source_commit"]}\n\n'
        'Early development playtest; Phase 1 remains PARTIAL. Visuals, balance, controller feel,\n'
        'full-run performance and replay appeal still need feedback.\n\n'
        'Install through the itch desktop app, then use Play Now. Unreal Editor is not required.\n'
        'If Windows reports missing Visual C++ runtime, select the bundled Microsoft installer\n'
        'launch option, complete its prompts, then Play Now. Restart Windows if requested.\n'
        'This build needs the bundled 14.51 runtime or newer.\n\n'
        'The itch Play action uses -SaveToUserDir so saves are outside the installation.\n'
        'For a direct launch use: SpaceSurvival.exe -SaveToUserDir\n'
        'Do not rename the project or pass a version-specific UserDir. Close the game before updating.\n'
        'Settings > Controls includes sensitivity and pitch inversion.\n\n'
        'Feedback: include VERSION.txt, your Windows/GPU/controller, the wave/station,\n'
        'what happened, what you expected, and steps or a short clip. Avoid sharing personal data.\n'
        'Save migration and clean-PC installation still need a pilot test before wider invitations.\n', encoding='utf-8')
    receipt = {'version': version, 'target': TARGET, 'source_commit': audit['source_commit'],
               'package_receipt': package_receipt.relative_to(ROOT).as_posix(),
               'package_receipt_sha256': sha(package_receipt), 'files': entries(stage)}
    (stage.parent / 'release.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    check(stage, receipt)
    print(f'Prepared {version}: {len(receipt["files"])} files, {sum(r["bytes"] for r in receipt["files"]):,} bytes')
    print(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'verify', 'preview', 'publish', 'status'])
    parser.add_argument('--version', required=True)
    parser.add_argument('--receipt', default='docs/validation/2026-09-13-station-camera.json')
    parser.add_argument('--butler', default='.agent/local/Tools/butler/butler.exe')
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9][A-Za-z0-9._-]{0,63}', args.version):
        parser.error('Version must start with a digit and contain only letters, digits, dot, dash or underscore')
    if args.action == 'prepare':
        prepare(args.version, safe_path(ROOT, args.receipt))
        return
    stage = safe_path(ROOT, f'Artifacts/Releases/{args.version}/payload')
    receipt = json.loads((stage.parent / 'release.json').read_text(encoding='utf-8'))
    if receipt['version'] != args.version:
        raise ValueError('Version identity mismatch')
    check(stage, receipt)
    print(f'Verified {args.version} -> {TARGET}', flush=True)
    if args.action == 'verify':
        return
    butler = safe_path(ROOT, args.butler)
    if not butler.is_file():
        raise ValueError('Install portable official butler locally; see docs/ITCH_RELEASES.md')
    def run(*command):
        subprocess.run([str(butler), *command], check=True, cwd=ROOT)
    if args.action == 'status':
        run('status', TARGET)
        return
    run('validate', str(stage), '--platform', 'windows', '--arch', 'amd64')
    # Every publish performs a dry run first; neither building nor preparing uploads anything.
    run('push', str(stage), TARGET, '--userversion', args.version, '--dry-run')
    if args.action == 'publish':
        check(stage, receipt)
        run('push', str(stage), TARGET, '--userversion', args.version)
        run('status', TARGET)


if __name__ == '__main__':
    main()
