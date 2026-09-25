"""Relocate only the exact Solar/Portal staging receipt's Rocket packages.

Refuses missing, modified, extra or dirty source content. A receipt lacking
hashes for every staged file cannot authorize relocation. Never use this to
move an arbitrary existing Rocket library.
"""
import hashlib
import json
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / 'Artifacts/BuildingLibrary'
family = 'Solar' if '-SSSolar' in u.SystemLibrary.get_command_line() else 'Portal'
source, destination = '/Game/Rocket', '/Game/ImportedLibrary/' + family


def verify_staged_source(project, output, selected_family):
    """Bind the whole on-disk source tree to its known staging operation."""
    receipt_names = {
        'Solar': ('staging-cargo-nova-solar-apply.json', {'cargo', 'nova', 'solar'}),
        'Portal': ('staging-portal-apply.json', {'portal'}),
    }
    filename, expected_groups = receipt_names[selected_family]
    receipt_path = output / filename
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    if receipt.get('mode') != 'apply' or set(receipt.get('groups', [])) != expected_groups:
        raise RuntimeError('Staging receipt does not match the requested family: ' + str(receipt_path))
    written = receipt.get('written', [])
    if (receipt.get('already_identical') != 0
            or not written or len(written) != receipt.get('unique_packages')):
        raise RuntimeError('Staging receipt lacks complete per-file hashes; relocation refused')
    content = (project / 'Content').resolve()
    source_root = (content / 'Rocket').resolve()
    expected = {}
    expected_packages = set()
    all_targets = set()
    for record in written:
        path = Path(record['path']).resolve()
        if not path.is_relative_to(content):
            raise RuntimeError('Staging receipt targets a different project: ' + str(path))
        key = str(path).casefold()
        if key in all_targets:
            raise RuntimeError('Duplicate file in staging receipt: ' + str(path))
        all_targets.add(key)
        if not path.is_relative_to(source_root):
            continue  # The Solar receipt also staged Cargo and Nova roots.
        sha = str(record['sha256']).lower()
        if len(sha) != 64 or any(char not in '0123456789abcdef' for char in sha):
            raise RuntimeError('Invalid staging checksum for ' + str(path))
        relative = path.relative_to(source_root).as_posix()
        expected[relative.casefold()] = sha
        if path.suffix.lower() in ('.uasset', '.umap'):
            expected_packages.add(('/Game/Rocket/' + str(Path(relative).with_suffix('')).replace('\\', '/')).casefold())
    if not expected or not expected_packages:
        raise RuntimeError('Receipt contains no Rocket packages for the requested family')
    actual = {}
    for path in source_root.rglob('*'):
        if not path.is_file():
            continue
        if not path.resolve().is_relative_to(source_root):
            raise RuntimeError('Source file resolves outside the staged Rocket root: ' + str(path))
        relative = path.relative_to(source_root).as_posix().casefold()
        if relative in actual:
            raise RuntimeError('Case-insensitive duplicate source filename: ' + relative)
        actual[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    changed = sorted(path for path in set(actual) & set(expected) if actual[path] != expected[path])
    if missing or extra or changed:
        raise RuntimeError('Rocket source differs from exact ' + selected_family + ' staging receipt: '
                           + json.dumps({'missing': missing, 'extra': extra, 'changed': changed}))
    return {
        'receipt': str(receipt_path),
        'receipt_sha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        'verified_source_files': len(expected),
    }, expected_packages


lib = u.EditorAssetLibrary
reg = u.AssetRegistryHelpers.get_asset_registry()
reg.search_all_assets(True)
assets = reg.get_assets_by_path(source, recursive=True)
assert assets and not reg.get_assets_by_path(destination, recursive=True), 'Expected untouched staged family and empty target'
paths = [str(a.package_name) for a in assets]
staging_guard, expected_packages = verify_staged_source(ROOT, OUT, family)
assert {path.casefold() for path in paths} == expected_packages, 'Registry assets differ from exact staged package set'
destination_disk = ROOT / 'Content/ImportedLibrary' / family
assert not any(path.is_file() for path in destination_disk.rglob('*')), 'Destination contains existing files'
dirty = [package.get_path_name() for package in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
assert not any(path.startswith(source + '/') or path.startswith(destination + '/') for path in dirty), 'Source or destination has unsaved edits'
assert lib.rename_directory(source, destination), 'Native asset relocation failed'
assert lib.save_directory(destination, only_if_is_dirty=False, recursive=True)
reg.scan_paths_synchronous([destination, source], force_rescan=True)
deps = u.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
targets = reg.get_assets_by_path(destination, recursive=True)
remaining = {str(a.package_name): [str(d) for d in reg.get_dependencies(a.package_name, deps) if str(d).startswith(source + '/')]
             for a in targets}
remaining = {k: v for k, v in remaining.items() if v}
assert not remaining, 'Relocated packages still depend on temporary Rocket path: ' + str(remaining)
redirectors = reg.get_assets_by_path(source, recursive=True)
assert all(str(a.asset_class_path.asset_name) == 'ObjectRedirector' for a in redirectors), 'Real source assets remain'
root = ROOT / 'Content/Rocket'
files = [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in root.rglob('*') if p.is_file()]
report = {'status': 'PASS', 'family': family, 'source_count': len(paths), 'target_count': len(targets),
          'target': destination, 'staging_guard': staging_guard,
          'remaining_source_dependencies': remaining, 'redirectors': len(redirectors), 'source_files': files}
(OUT / ('relocate-' + family.lower() + '.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
u.log('BUILDING_MATERIAL_RELOCATE_OK ' + family)
