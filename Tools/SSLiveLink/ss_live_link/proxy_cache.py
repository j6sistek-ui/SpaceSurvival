"""Content identities for snapshot proxies, independent of Blender and file timestamps."""
import hashlib
from pathlib import Path


def snapshot_mesh_key(asset, proxy):
    digest = hashlib.sha256(asset.encode('utf-8') + b'\0')
    with Path(proxy).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    # Below Blender's 63-byte ID-name limit even for long Unreal package names.
    return 'SSSnapshot:' + digest.hexdigest()[:48]
