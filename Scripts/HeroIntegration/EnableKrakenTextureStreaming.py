"""Permit the existing Kraken texture mip chains to stream without reducing resolution.

Read-only plan by default. Apply requires -SSEnableKrakenStreaming and unchanged
inputs. Only NeverStream changes; all original packages are hash-backed up first.
"""
import hashlib
import json
import shutil
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / '.agent/local/QualityPass_20261021'
OUT.mkdir(parents=True, exist_ok=True)
APPLY = '-SSEnableKrakenStreaming' in u.SystemLibrary.get_command_line().split()
BASE = '/Game/SpaceSurvival/Licensed/StationAssets/KrakenRefresh_20261015/Textures/'
properties = ['mip_gen_settings', 'compression_settings', 'compression_no_alpha',
              'lod_group', 'lod_bias', 'max_texture_size', 'srgb', 'power_of_two_mode',
              'virtual_texture_streaming', 'lossy_compression_amount', 'num_cinematic_mip_levels']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def settings(asset):
    return {name: str(asset.get_editor_property(name)) for name in properties}


assets = []
rows = []
for index in range(4):
    for suffix in ['BaseColor', 'MetalRough', 'Normal']:
        path = BASE + 'M' + str(index) + '_' + suffix
        asset = u.load_asset(path)
        assert isinstance(asset, u.Texture2D), path
        assert asset.mip_gen_settings == u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP
        width, height = asset.blueprint_get_size_x(), asset.blueprint_get_size_y()
        assert width > 0 and height > 0 and width & (width - 1) == 0 and height & (height - 1) == 0
        file = ROOT / ('Content/' + path[len('/Game/'):] + '.uasset')
        rows.append({'path': path, 'file': str(file.relative_to(ROOT)), 'before_sha256': sha(file),
                     'never_stream': bool(asset.never_stream), 'width': width, 'height': height,
                     'preserved_settings': settings(asset)})
        assets.append(asset)
plan = OUT / 'KrakenStreamingPlan.json'
if APPLY:
    assert json.loads(plan.read_text()) == rows, 'Texture inputs changed since plan'
    assert all(row['never_stream'] for row in rows), 'Already changed or mixed starting state'
    archive = Path('D:/SpaceSurvival_AssetArchive/QualityPass_20261021/KrakenTextures')
    archive.mkdir(parents=True, exist_ok=True)
    # Preserve every source before saving any package.
    for row in rows:
        source = ROOT / row['file']
        backup = archive / (source.stem + '_' + row['before_sha256'] + '.uasset')
        if not backup.exists():
            shutil.copy2(source, backup)
        assert sha(backup) == row['before_sha256']
        row['backup'] = str(backup)
    for row, asset in zip(rows, assets):
        asset.set_editor_property('never_stream', False)
        assert settings(asset) == row['preserved_settings']
        assert u.EditorAssetLibrary.save_loaded_asset(asset, False)
        row['after_sha256'] = sha(ROOT / row['file'])
    (OUT / 'KrakenStreamingApplied.json').write_text(json.dumps(rows, indent=2))
else:
    plan.write_text(json.dumps(rows, indent=2))
print('KRAKEN_STREAMING_' + ('APPLIED' if APPLY else 'PLAN'), len(rows))
