# Wardrobe hologram selector — October 16, 2026

Owner request: RPT-20261016-15. Replace the wardrobe's full-screen list with a
character showcase at the existing pad. Preserve the current roster, hero and
squirrel work. This branch is stacked on PR74 (`codex/waitress-service`).

## Implementation

The existing Canvas interface owns a compact selection panel. Left/right browses
installed bodies; Select alone uses the existing account/equip transaction.
Previous/Next and Select/Back also have pointer targets. Character names come
from roster IDs. No invented strength/rating values or biographies are supplied;
authored descriptions remain a content follow-up.

The approached wardrobe terminal supplies its existing projection actor and
hologram material. A temporary skeletal component previews a compatible idle,
fits the requested world height and preserves the original sole plane. Original
mesh, materials and animation remain intact. Closing, switching panels or world
teardown removes the preview and restores the original visibility. A temporary
camera frames the pad, preserves live exposure and restores the prior view.
Camera placement sweeps from the current view to avoid crossing walls.

Missing projection connections report that the world preview is unavailable;
they do not silently substitute another character. Empty rosters are safe.
Browsing never writes an account. Selection rechecks the previewed stable ID.

## Verification

- Worktree Build1 failed on an inferred pawn-pointer declaration and an incorrect
  skeletal-mesh-actor include. Both causes were repaired; the failed log is
  retained. Worktree Build2 **passed in 10.51 seconds**.
- Final worktree Build3, including reflected `BrowseWardrobe`, **passed in
  23.99 seconds**. Existing engine/plugin deprecation warnings remain; no new
  project warning was found. Docker Desktop was unavailable, so local formatting
  used the installed clang-format; container CI remains the publication gate.
- `SpaceSurvival.Menu.WardrobePreviewNavigation` **passed: 1 test, 0 warnings,
  errors or skips** under NullRHI with an isolated user directory. Test duration
  was **0.482 seconds**; the process exited 0 after **45.40 seconds**. The single
  test covers browse/Select/Cancel/account behavior and terminal preview cleanup,
  original restoration and 185 cm world height with a scaled parent. It does not
  establish camera framing or physical input acceptance.
- 49 structural checks, Python compileall, content-format validation (26 meshes,
  17 WAV files), scoped C++ formatting and documentation checks passed.
- The canonical source patch was applied after backing up the affected originals.
  CanonicalBuild1 **passed in 30.94 seconds**. The canonical editor DLL SHA-256 is
  `0a679b4305cd961dc72cfdb67b93613b6aa2a0b0fc22a63c8b0dd9af58a690ad`.
- The owner released the GPU hold at **05:09 UTC** ("good to go"); the lead recorded
  1,471 MiB VRAM in use. Offscreen native preview PID 20452 launched at 05:15 UTC
  with that module.
- The first capture harness opened wardrobe in the teleport tick, using the old
  cached camera position, and resized afterward. Its restoration receipt also
  hit an unsupported `Transform.equals` argument. Failed captures/error remain
  retained. The corrected harness establishes 1600×900 first, settles for three
  seconds, then opens the wardrobe; this did not require a gameplay camera change.
- `NativePreview2.json` verifies scripted forward/back browsing, prior camera and
  pawn-transform restoration, unchanged player mesh and zero remaining temporary
  skeletal components. `Wardrobe_Current2.png` and `Wardrobe_Next2.png` show the
  large Squirrel/Nyxar holograms on the pad beside the panel at actual 1600×900.
  These are scripted captures, not pointer-click or physical-controller evidence.
- `NyxarFacingDiagnostic.png`, using original materials temporarily on the preview,
  confirms the character faces forward. The existing hologram transparency reduces
  face detail; readability remains open. No native asset, map or save edit was
  performed. `NativePreservation.json` verifies the station map and three owner
  save files retain their original SHA-256 hashes, with no dirty editor packages.
  The owned editor exited after the review without saving.

Private receipts: worktree `.agent/local/WardrobeBuild/Build1.log`, `Build2.log`, `Build3.log`
and `NativeTest1/{Report/index.json,Process.json}`. Canonical receipts and original
source backups are under `.agent/local/WardrobeHologram_20261016/`, including
`SourceBefore.json`, `CanonicalBuild1.log`, `Launch1.json`, `NativePreview2.json`
and the named captures. These local receipts are not included in the source PR.

## Still open

Lead still owns actual pointer-click and physical-controller checks, hologram
readability and owner appearance/feel acceptance. Authored short biographies need
real character content. Packaged review remains open; scripted browsing and
screenshots do not close these gates.
