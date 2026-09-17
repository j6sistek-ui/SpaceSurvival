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
rejects changed/missing/extra files and links. It also refuses runtime Saved directories
and .sav/.log files even when an older prepared receipt lists matching hashes. Publishing
always runs a dry run first.
Keep payloads closed to other writers during publish. Release receipts are local integrity
records, not signed attestations. The channel is fixed to prevent accidental cross-project uploads.
No automatic rollback: republishing an older audited payload is another deliberate upload.

## What testers receive

A cooked Windows game, not the Unreal project. Unreal Editor and Visual Studio are unnecessary.
The payload preserves all audited runtime dependencies and notices, removes PDB symbols,
UAT file manifests, all runtime Saved directories and .sav/.log files, and the developer-path prerequisite receipt, and adds `.itch.toml`,
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
balance remain owner/tester checks in [KNOWN_ISSUES.md](KNOWN_ISSUES.md). No new in-game version badge was
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

## September 17 0.1.18-alpha published, from a repaired candidate

**Published on the owner's instruction to merge PR #19 and update itch.** `0.1.18-alpha` is on `windows-alpha` as upload 19226459; itch reports build **1988042** ready (from 1984728). Packaged source `de5d56c`: main `c46e571` (PR #19 merged) plus the one commit of PR #20, which the lead was not permitted to merge and left open for the owner. Butler reports a **188.32 MiB patch (92.97% savings)**, 85.80% of old data re-used and 380.29 MiB fresh; these are publisher figures, not measured client results. The payload is **51 files / 2,808,973,625 bytes**. [Release receipt](validation/2026-09-17-itch-0.1.18-release.json); [package receipt](validation/2026-09-17-admitted-bodies-package.json).

**Why it was not the first candidate.** The package built from the merged source `87c445b` passed the packaged Station 5 fixture and then failed Wave 10 honestly: zero seconds of compound presence, peak 15 threats. Publication was held. The cause was a real gameplay regression from the September 16 Director dials, not a fixture fault: spawn leads had grown past the fixed 22,000 retirement radius, so bodies were placed, charged for and deleted a tick later, more of them the faster the player flew. It was fixed, adversarially reviewed (twelve findings, all addressed), proven by a test that fails 37 expectations without the fix, and re-verified on a new package: Wave 10 `99e9072f8ca140d8a3c04d4896dd168e` with 39.26 of 40.00 seconds of compound presence and peak 24, Station 5 `92dacd93a1d847b9a9e2b3569aaa6a79` with all 16 images, and IoStore audit `2cde7e3cb7e74c15965564c11fa462dc` with 1,897 described exports and zero unresolved imports. 54 of 54 Unreal tests pass with no warnings.

**Tell the tester.** The field is denser and more dangerous than in 0.1.17, most of all while boosting; the dials were tuned against the thinned version and have not been re-judged. The account save moves to payload version 3 for ship paint; versions 1 and 2 still load, but a real A-to-B update with save preservation remains unverified, as does clean-PC installation. The ALIEN WORLD doorway defect (RPT-20260916-10) is not claimed fixed; this build logs which rejection fires. [Devlog copy](ITCH_DEVLOG_0.1.18.md) is drafted and **not published**: posting needs the owner's itch browser sign-in.

The receipt lists 53 archive files. It does not bind the 17 files under `Saved` inside `Artifacts/Windows`, which are the owner's own runs of the packaged build: they are never shipped, and they change whenever the owner plays, which would make an honest receipt fail its own hash check.

## September 16 0.1.17-alpha PUBLISHED on owner direction, with an open defect

**September 16 09:20 UTC: published on owner direction.** `0.1.17-alpha` is live on `windows-alpha` as upload 19226459, build **1984728** (from 1979965), packaged source `a77010e`. Butler reports a 398.75 MiB patch (84.60% savings) with 77.19% of old data re-used; these are publisher figures, not measured client results. The lead recommended holding twice because the gallery entry defect (RPT-20260916-10) is open and undiagnosed; the owner reaffirmed publication, noting the page is restricted to the owner and one tester. **The shipped build therefore contains a known intermittent defect: the station ALIEN WORLD doorway can ignore the interact key until the game is relaunched.** Tell the tester. [Release receipt](validation/2026-09-16-itch-0.1.17-release.json).

**Superseded hold, September 16 09:05 UTC.** Owner hands-on play of this candidate found the station ALIEN WORLD doorway silently unresponsive, then working after a reload. `USSAlienGallery::Enter` rejects before `StartLoad` with no log or message, and the scripted fixture cannot see it because it teleports the walker and calls `ASSGameMode::Interact` directly instead of walking and pressing a key. This is a second, undiagnosed intermittent defect on the gallery entry path. That hold was lifted by owner direction at 09:20 UTC. See ISS-11 and RPT-20260916-10 in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

`Artifacts/Releases/0.1.17-alpha/payload` is prepared and locally verified from packaged source `a77010e`: 51 files, 2,715,833,034 bytes, against the passing IoStore dependency audit and packaged fixtures recorded in the [gallery input-isolation receipt](validation/2026-09-16-gallery-input-isolation.json). Preparation and local verification upload nothing. `preview` and `publish` contact itch and need portable butler plus an explicit owner decision; neither was run. The published tester build is still `0.1.16-alpha.1`. Clean-PC installation and a real A-to-B update with save preservation remain unverified.

## September 14 update

0.1.15-alpha is verified ready on windows-alpha, upload19226459/build1978147, based on1975861. Butler reports539.30MiB patch (52.88% savings); actual client update/save preservation is unverified. Devlog remains drafted, not published: browser authentication required.

Source `602be07`; package receipt `validation/2026-09-14-environment-refresh.json`. Public-copy draft: `ITCH_DEVLOG_0.1.15.md`. Experimental clouds disabled by default after packaged artifact reproduction. Phase1 PARTIAL.

## September 15 visual release

The owner authorized merging PR11/12 and updating itch. Both PRs are merged; main was verified at `c0479cf`. Packaged game source remains `cf6296f`; subsequent documentation/merge/release-script commits do not relabel its runtime source.

**0.1.16-alpha.1 is verified ready** on windows-alpha, upload **19226459**, build **1979965**, based on **1978147**. The clean payload contains **51 files / 2,664,557,549 bytes**. Butler reports a **1.49 GiB patch (39.76% savings)**, with 32.19% of old data reused. These are publisher reports, not measured client-download or update/save-preservation results. The [immutable release receipt](validation/2026-09-15-itch-visual-release.json) records every uploaded file hash, the reviewed Package4 lineage, merge commits and ready status.

The preview caught ten runtime files under Saved (settings/logs/saves). They were also present in the earlier 0.1.15 payload. The corrected publisher excludes case-insensitive Saved directories and .sav/.log files and refuses an older unsafe payload even if its receipt matches. The abandoned local 0.1.16-alpha preparation was never uploaded; a new immutable 0.1.16-alpha.1 preparation was used. All 63 original audited files remain byte-identical, including local saves. Existing published history was not deleted.

Six synthetic release-safety tests and Python compilation pass; CI now runs the release tests.31 source structural checks pass. No Unreal rebuild or new gameplay acceptance is claimed: the release carries the same verified game executable and cooked containers. All 19 owner cases remain open.

[Current devlog copy](ITCH_DEVLOG_0.1.16.md) is prepared but **not published**: itch browser security/sign-in needs owner completion. It supersedes the unpublished 0.1.15 draft. The game update itself is available through the existing itch app channel. Use that app's Play action with -SaveToUserDir; do not copy developer Saved folders into a tester installation.
