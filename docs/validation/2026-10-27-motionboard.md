# MotionBoard local planner — October 27, 2026

Status: PARTIAL. RPT-20261016-03 owns remaining lead work and owner acceptance.
Snapshot: 2026-10-27T02:15Z. Local authoring/browser preview, not a game build or rig repair.

## Tool and storage

Docker publishes `127.0.0.1:8769`; tracked code is in `Tools/MotionBoard`.
GLBs, vendor modules, manifest/discovery inventory and state stay ignored in
`SourceAssets/MotionBoard`. Assets/frontend are mounted read-only, state separately
writable. Python uses the standard library; no host packages are installed.
Allowlisted routes and Host/Origin checks restrict access; JSON saves are bounded,
revision-checked and atomically replaced. A stale tab returns HTTP409, and corrupt
state is preserved rather than silently overwritten.

Animated cards feed eight rough-order slots with trim, duration, reverse and notes.
Export is a JSON proposal with clip/source identity, not a merged GLB/FBX or
Unreal animation. Browser-selected GLBs stay local and need reselecting after
reopening. Direct FBX loading now has CPU fixture checks; browser validation is open. Global
card-only ¼×/½×/1×/2× speed changes preserve phase and browser preference; main
preview, slot timing and exported proposal timing are unchanged.

## Verified snapshot

- Private manifest: **12 registered libraries / 330 clips**. All 72 priority clips from
  VarietyDanceAnims, RitualDanceAnims, SensualMoves and SensualMoves2 are now
  packed/registered, superseding the earlier 59-clip/export-only snapshot.
  Native export receipts record unchanged inputs; preview exports do not establish
  target-dancer compatibility or visual quality. Snapshot SHA-256:
  `5e525c71d941acc216855d2874ce633e77cba2696d675294fce51d06b87c0399`.
- Python backend: 18 tests passed in an isolated existing Docker image using only
  temporary fixtures; no owner board was mounted. Coverage includes path/Origin
  guards, eight-slot types/ranges, stale HTTP409, corrupt-save preservation, atomic
  replacement/failure cleanup, mount roots and optional bounded clip metadata.
- JavaScript: lead reports 11 passing tests for the model/library/framing behavior.
  This is source/fixture evidence, not a physical drag gesture or every-clip review.
- Lead browser QA repaired overlay, root-follow, framing and narrow-layout defects.
  Separate port 8770 test state passed clip trim, duration, reverse, save and JSON export.
  The owner's port 8769 board was not used as the QA write fixture. Global card speed is
  implemented with phase continuity and browser persistence; owner feel is open.

These browser findings are the integrating lead's observed results, not a claim
that this document's author reran the UI. Private review material remains under
`.agent/local/MotionBoardReview`; native conversion receipts are in
`.agent/local/MotionBoardExports`.

## Repeat playback and direct FBX follow-up — 2026-10-27T02:35Z

- Optional item playbackMode/playbackSpeed/repeatCount fields keep old items in
  one-pass stretch mode. Source trims, source speed and total slot duration are
  distinct. A0.5-second trim ×10 at1× occupies5seconds; repeat-for10seconds yields
  20cycles. Reverse starts each cycle at trim end. Interior boundaries reset; the
  final boundary samples the completed or fractional cycle. Export adds an
  explicit playbackPlan; no source curves or seams are repaired.
- `npm run check`: **22 tests passed, no skips**, including shared timing, library,
  private Meshy/Flips framing and direct FBX fixtures. Tests cover exact boundaries,
  fractional/reverse cycles, reload/pause, card-rate independence, mixed slot
  timing and exported loop boundaries. The stale temporary Tavern FBX fixture
  was replaced by the existing private A_F3_ZeroG_01_Drift.fbx fixture.
- `server_test.py -v`: **20 tests passed** in the existing Docker image with a
  read-only tool mount, temporary state and no published ports. Repeat modes
  roundtrip without altering legacy items; invalid totals/types fail without
  replacing saved state. Owner assets/state were not mounted.
- The FBX loader warns that vertex influences above four are reduced in preview.
  Source file/curve hashes remain unchanged; skin-deformation fidelity is not
  established by parsing. Direct FBX browser interaction remains pending.
- Dance6's existing start4.87/end10.9333 is retained even though current export
  metadata ends10.9. A timing-only edit preserves it; a changed end10.92 is
  rejected. The UI explains last-frame holding rather than silently retiming
  owner data. Full source-origin offset reconciliation remains open.
- No browser/GPU, Unreal/Blender, server restart, owner save or native animation
  operation occurred in this pass. Lead browser repeat-mode/layout checks and
  deployment coordination are pending. Seams are not blended and owner
  acceptance is still open.

## Deployment, coverage and CPU study — 2026-10-27T02:55Z

- Integrating-lead read-only receipt `RepeatDeployment.json` confirms both
  loopback backends8769/8770 are deployed. Served/disk revisions are22/23 and
  owner items match. The8770 whole response differs because validation normalizes
  library metadata; that is not an owner-item change. The owner is actively
  editing8770, so old snapshot hashes are not claimed unchanged. This check wrote
  no owner state. Repeat layout/interaction remains browser-unverified under the
  current CPU-only constraint; direct FBX and gesture drag/drop checks stay open.
- Lead's completed import snapshot: **1304 clips / 22 logical packs**, with1285
  clips in43 preview GLBs plus19 Meshy clips, about490.5MB. Source receipts cover
  1307 unchanged original files and6345 pose probes with error at most0.235mm.
  The43 files are preview chunks, not distinct purchases. Flight, AFS glider/zombie,
  large Paragon weapon, ambiguous FBX and seven unlocated titles remain outside
  accepted coverage. This supersedes the earlier dated330-clip preparation.
- `SourceAssets/PerformancePlan_20261027/Review.html` exposes the complete80-second
  CPU study,160 decoded frames at2Hz, with source/time indices. Recorded
  `Receipt.json`/`Verification.json` show unchanged source hashes, both camera
  views fitting the figure, continuous section-boundary positions and zero
  positional error for preserved S04 departure samples at displayed times.
  This is articulated proxy planning: no native character, skin weights or
  production animation changed. Contact, acceleration, full-speed native quality
  and loop acceptance remain unverified. The lead owns the final renderer/receipt
  refresh after the S08 supporting-hand correction.
- The isolated MotionBoard Docker image build passed; it did not restart either
  portal. The performance-study script compiled in read-only Docker; the lead's
  CPU render/verification is separate evidence. Existing22 JavaScript and20
  backend fixture passes remain applicable; they are not owner visual acceptance.

## Coverage and unresolved checks

The broader conversion queue is partial. At this snapshot, retained retry receipts
show TavernAnims and DrunkAnimations packing failures and an MCO_Mocap_Basics
validation failure; other conversions continue. Failed/unregistered outputs are
not counted as Ready. `PackQueueStatus.json` and `SubsetRetryStatus.json` retain
the exact evidence. LibraryDiscovery.json reconstructs 38 owned-library candidates;
exact Fab-category membership/complete coverage is unconfirmed. Archive copies,
root-motion variants and demo poses are not automatically unique animations.

Actual pointer drag-and-drop, direct FBX browser interaction and owner usability remain open.
The lead owns missing-library conversion and failed-check retries. Neither valid
keys nor a browser preview prove correct deformation, contacts, transitions,
retargeting, all-clip quality or native-game acceptance. Sequencer compatibility
and its earlier Undo defect remain separate; broad dancer repair stays paused.
No C++ module, production rig/map, packaged game or release changed. C++ build,
gameplay/performance and packaging checks do not apply to this browser-only delta.
Final documentation gates must use the exact assembled publication files.
