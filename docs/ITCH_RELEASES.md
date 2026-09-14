# Restricted Windows playtest releases

The owner builds locally and deliberately publishes selected milestones. No build, commit,
PR, CI run, or prepare command uploads automatically. Source PRs remain unmerged until approved.

- Page: https://j6sistek-ui.itch.io/space-survival (game ID 5006010).
- Stable channel: `j6sistek-ui/space-survival:windows-alpha`.
- First prepared version: `0.1.14-alpha`, Package14, gameplay source `f4bfec8`.
- First upload verified: upload 19226459, build 1975861, version 0.1.14-alpha; page displays 471 MB.
- Phase 1 remains PARTIAL. Distribution readiness does not establish gameplay acceptance.

## Owner workflow

Run from the repository root with existing Python 3.11+ and portable official butler.
The current tool is `.agent/local/Tools/butler/butler.exe` (ignored, no system PATH changes).
Install from https://itch.io/docs/butler/installing.html; use the Windows amd64 archive.
Run `butler.exe login` once and approve its browser prompt. Never paste credentials into
chat or commit them. Butler stores the login in the current user's `.config/itch/butler_creds`.

```powershell
# Local preparation only; audited archive must still match every receipt hash.
python Scripts/ItchRelease.py prepare --version 0.1.14-alpha --receipt docs/validation/2026-09-13-station-camera.json
# Inspect/validate without uploading.
python Scripts/ItchRelease.py preview --version 0.1.14-alpha
# Deliberate publication, only when this milestone is ready for testers.
python Scripts/ItchRelease.py publish --version 0.1.14-alpha
python Scripts/ItchRelease.py status --version 0.1.14-alpha
```

The existing first version is already prepared; do not prepare it again. Each later release
uses a new version and a new reviewed package receipt with `source_commit` and `archive_files`
(path, bytes, SHA256). Build/package and validate gameplay first. The default receipt is only
for Package14: a newer archive will fail its hash check. Do not relabel an untested archive.

Prepared payloads live under `Artifacts/Releases/<version>/payload`, with a hash receipt
alongside, outside the upload. Preparation refuses to overwrite a version. Verification
rejects changed/missing/extra files and links, and publishing always runs a dry run first.
Keep payloads closed to other writers during publish. Release receipts are local integrity
records, not signed attestations. The channel is fixed to prevent accidental cross-project uploads.
No automatic rollback: republishing an older audited payload is another deliberate upload.

## What testers receive

A cooked Windows game, not the Unreal project. Unreal Editor and Visual Studio are unnecessary.
The payload preserves all audited runtime dependencies and notices, removes PDB symbols,
UAT file manifests and the developer-path prerequisite receipt, and adds `.itch.toml`,
`VERSION.txt` and `PLAYTEST.txt`. Original symbols remain in the local package for debugging.

Install through the itch desktop app using an account granted access to the restricted page.
Keep that installation and channel; the app can apply subsequent updates. Browser ZIP downloads
do not provide that managed update workflow. Close the game before updating. The owner grants
access/download keys through itch; this setup neither invites testers nor changes visibility.

If first launch reports a missing runtime, choose the bundled **Install Microsoft Visual C++
runtime** launch action, complete Microsoft's prompts, and then choose Play Now. The bundled
x64 installer is 14.51.36247.0, verified in Package14. On 2026-09-13 itch's newest v14 registry
entry was only 14.50.35719.0, so the manifest intentionally does not declare that older version
as sufficient. This is a manual prerequisite step; installation on a clean PC is not yet verified.

## Saves and update pilot

The itch Play action passes `-SaveToUserDir`, selecting a stable user profile outside the install,
normally `%LOCALAPPDATA%/SpaceSurvival/Saved/SaveGames` (sandbox/low-integrity may use LocalLow).
Direct launch must also use `SpaceSurvival.exe -SaveToUserDir`; plain double-clicking this
Development build can use install-local saves. Existing development saves are not automatically
migrated. Do not ship a Saved directory, rename the project/slots, or add version-specific UserDir.

Before wider invitations, test with one tester: install A, change settings, earn account
progress and suspend a run, close it, publish a genuinely changed B when ready, update through
itch, relaunch, and verify all three save domains plus version identity. Record patch size,
Windows/GPU/controller, install location and any prerequisite prompts. Back up that tester's
save files before the first migration test. This A-to-B test and clean-PC install remain open.

Ask feedback to include VERSION.txt, wave/station, expected/actual behavior and reproduction
steps or a clip. Camera comfort, mouse inversion, physical controller parity and natural run
balance remain owner/tester checks in PLAYTEST_TOMORROW.md. No new in-game version badge was
added by this release task; version is available in itch and the installed VERSION.txt.

## Verification and limits

Run `python Scripts/TestItchRelease.py` and compile both release scripts with `python -m py_compile`. The script uses only Python's standard library. Prefer the existing
container workflow when its daemon is available. No UE rebuild is necessary for this packaging-only
change; Package14's existing 38-test receipt binds the unchanged gameplay binaries.

Official references checked 2026-09-13:
- https://itch.io/docs/butler/pushing.html — channels, manual versions, dry runs, 30 GB uncompressed limit.
- https://itch.io/docs/itch/integrating/updates.html — app-managed updates.
- https://itch.io/docs/itch/integrating/manifest-actions.html — launch paths/arguments.
- https://itch.io/docs/itch/integrating/prereqs/ — prerequisite registry.

Actual patch size varies with changed assets and cooked container layout. This setup does not
promise tiny updates or prove save compatibility across future game/schema changes.

## September 14 update

0.1.15-alpha is verified ready on windows-alpha, upload19226459/build1978147, based on1975861. Butler reports539.30MiB patch (52.88% savings); actual client update/save preservation is unverified. Devlog remains drafted, not published: browser authentication required.

Source `602be07`; package receipt `validation/2026-09-14-environment-refresh.json`. Public-copy draft: `ITCH_DEVLOG_0.1.15.md`. Experimental clouds disabled by default after packaged artifact reproduction. Phase1 PARTIAL.
