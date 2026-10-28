# SS Link portable geometry library — October 28, 2026

Owner request: verify the current building-parts library and provide an offline
Blender package on D. Owner confirmed geometry/layout is sufficient. This is
a private layout library, not a packaged game or an Unreal content migration.

## Delivered package

- ZIP: `D:/Codex/SpaceSurvivalLink_20261028/SpaceSurvival-Link-0.5.0-LayoutLibrary-20261028.zip`
- Size: 4,672,970,466 bytes; payload before compression: 7,089,790,032 bytes.
- Guide beside it: `READ_ME_FIRST.txt`.
- SS Link source version0.5.0; native asset files built for Blender5.2.2.
- No original models, levels or user Blender preferences were overwritten.
  The other chat's offscreen editor was not stopped or modified.

## Coverage and limitations

A separate UE5.8.4 NullRHI commandlet queries the current native asset registry.
All3,857 /Game static-mesh paths exactly match the catalog: zero missing or
unexpected paths. Prepared Blender files exist for all3,857 entries. Every
row/proxy/thumbnail fingerprint agrees with its prepared-file manifest.

The Building group has1,056 pieces and no missing geometry or thumbnails.
Some building-useful pieces can be classified Misc; all static-mesh groups
are included. Twenty-three non-Building parts lack thumbnails, while their
proxy and native geometry files are present. This does not test the appearance
or usability of every mesh.

The package includes referenced GLB proxies, available thumbnails, native
Blender asset files/catalogs, prefab recipes and the add-on/install scripts.
It does not include full Unreal shader graphs/textures, the registry's1,659
Material and4,073 MaterialInstanceConstant assets,312 skeletal meshes,
functional Blueprint logic, lights, VFX, gameplay or a complete placed station.
Source-only models not imported into Unreal are outside this registry scope.
The owner explicitly accepted geometry/layout rather than textured previews.

The installed Blender5.2 add-on matches project modules except the fallback
engine-path preference order in core.py; its configured project/engine roots
are already correct. This export uses the project add-on. Older Blender5.1
modules differ; Blender5.2 is the verified target, and other versions remain
unverified.

## Verification and preservation

- Native inventory: zero set differences across3,857 static meshes, no registry
  loading remaining. No GPU rendering or asset exports were requested.
- All11,581 archive payload files pass SHA-256 against the embedded manifest;
  archive membership and paths are checked.
- Isolated Blender5.2.2 with fresh D-drive user/config folders loads four
  representative Galaxy wall/floor/door/furniture parts via GLB and native
  Blender assets. Geometry is nonempty and Unreal identities/asset markers
  survive. Proxy/native polygon counts are12/12,12/12,320/320 and428/428.
  No SpaceSurvival.uproject exists in the test root.
- Initial live export correctly rejected a source changing during packaging.
  A subsequent catalog timestamp refresh invalidated the global digest while
  all individual fingerprints and asset membership remained identical.
  The final private archive rebinds only its own prepared manifest after
  verifying every row fingerprint; the live manifest is not patched.
- Final capture freezes each file in one buffer and checks expected source
  size/mtime before and after reading. This avoids copying a full expanded
  staging library to the external drive. Temporary snapshot/test files are
  removed after verification; concise receipts remain beside the ZIP.
- Private receipts: NativeRegistryAudit.json, PackageReceipt.json,
  ArchiveVerification.json and OfflineBlenderSmoke.json. Earlier failed-export
  logs remain diagnostic history, not successful verification.
- No C++ source changed; build/format/game tests do not apply. Documentation
  gate applies to this evidence-only update. No system packages were installed.

## On the other computer

1. Install/use Blender5.2, then extract the full SpaceSurvivalLibrary folder.
2. With Blender closed, run its Tools/SSLiveLink/Install Blender Add-on.cmd.
   For another OS/custom install, install the ss_live_link folder as an add-on
   ZIP and set Project root to the folder containing SSPortableLibrary.json.
3. Open Blender: N sidebar > SS Link > Parts library > Pop Out Library.
4. Place parts and save a trial .blend. Keep Live off while offline.
5. Bring that .blend back to the original project for an explicit reviewed
   Push/Apply. External custom models/textures require separate transfer.

Open: the ZIP and guide above. Check: install on the actual other computer,
browse/place a building part, then save/reopen the layout. Still open:
second-machine installation, interactive drag/drop and owner layout acceptance
under RPT-20261028-01; no game-performance or textured-material acceptance.
