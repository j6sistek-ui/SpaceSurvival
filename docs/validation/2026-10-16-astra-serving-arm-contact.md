# Astra serving arm and prop contact

Owner feedback on October16 identified a backwards tray arm, fingers through the
tray, the tumbler crossing the right wrist/forearm, and the corset clipping the
counter. Earlier native transfer checks did not establish acceptable anatomy.

## Initial V14 correction and identity

The local station is `dfdd292df4748161e72c6ae5bcb1e5d09d3195ea35a01672010297285b073b3e`.
Editor module `d248d14e0884deee2a394534caa07f6c687336f59f46136f4346dbce6a4624e4`
is unchanged. No C++ behavior, package, release or remote merge changed.

Only Astra's four optional tray-animation assignments changed:

- `CounterHandoff/A_astra_CounterCandidateV14`: move the tray forward, seed the
  arm from the natural carry orientation, reduce the lean and turn the pickup
  grip so the forearm approaches the near side of the glass.
- `ContactFit/A_tray_carry_animation_FlatPalmV14` and
  `A_tray_serve_animation_FlatPalmV14`: flatten the left fingers under the tray.
- `ContactFit/A_tray_set_down_animation_FlatPalmV14`: retain the table-delivery
  motion and add the same palm support.

Paths are beneath `/Game/SpaceSurvival/Licensed/StationAssets/BarHologram_20261016`.
Original clips, body, outfit, rig, physics, grips, service timing and all9,483 actor
transforms remain. The three palm-only derivatives change fifteen left-finger
rotation tracks, preserving source lengths and the other authored tracks.

## Evidence

The old pickup held the tray hand31.72cm behind the shoulder at1.2s. Its largest
left forearm/hand rotation changes between30fps keys were133.80/143.10degrees.
V14 places the hand19.59cm forward and reduces those steps to6.46/14.05degrees.
This is authored-key evidence, not a performance measurement.

Hand and planted-foot reach errors remain below0.00004cm with unchanged bone
lengths. A conservative2.5cm-radius forearm proxy changes from penetrating the
glass envelope to at least1.40cm clearance throughout the held counter-pickup
interval. Finger joints lie beneath the tray plane; side/rear/front native views
were inspected for the actual skin, tray and garment.

Normal and shared candidate orders pass4,443 per-frame samples. They include the
counter pickup, return, table delivery, shared drinking and cleanup. Counter
transfers are at most4.04cm; table transfers are at most2.14cm. Minimum sampled
head/tray clearance is12.05cm. Reviewed table frames retain the original delivery
and show the flatter supporting hand. A fresh editor reload verifies the four
saved assignments, all9,483 transforms, original clips/grips and Kraken V12 with
all nine materials. The subsequent saved ordinary order passes1,990 samples.
Play stops and the owned editor exits with clean packages.

All225 pre-existing non-map guard files and the four replaced animation files
retain their hashes. The original map and both intermediate saved maps are backed
up. V11/V13 reach failures remain unadopted; V12 corrected the arm but was
superseded after the owner's additional contact feedback. The earlier V9/V10
pose trials are retained as history.

## Storage and limits

Private inputs, candidate keys, full native logs, unedited captures, backups and
preservation manifests:
`C:/Users/j6sis/SpaceSurvival/.agent/local/Waitress_20261015/Handoff_20261016/PourReview/ArmRepair_20261016`.
`SavedReload/Adopted.json` pins the four final native assignments. The final
review is `Review.html` in the private directory. Native assets remain local;
the source PR carries this evidence and updated operating documentation.

Owner natural-play acceptance remains pending. Seated garments, detailed thumb
contact in other gestures, natural laughter, broader room composition, physical
input and performance remain open in KNOWN_ISSUES. These checks do not pause
independent work. No claim of complete bar or Phase1 acceptance is made.

The owner's subsequent onto-tray close-up identifies remaining right-finger and
thumb overlap with the tumbler. This supersedes any inference of complete grip
acceptance from the wider V14 views. A separate finger-fit trial is under review;
the current saved map remains V14 until native review passes.

## Final grip correction after the owner close-up

The saved station is now `7431ed23ef99770ebe369746c8f6ab164c658558126d96a9a3c415ce625b23dc`. The editor module is unchanged. The two new optional clips are `CounterHandoff/A_astra_CounterCandidateV17` and `ContactFit/A_TraySetDown_GripFitV18`; V14 flat-palm carry/serve remain. Each new clip changes 21 rotation tracks: fifteen right-finger tracks plus both upper arms, forearms and hands. Authored translation/scale tracks and service timing are preserved.

The raw pose and runtime arm proportions differed by about 2.71 cm in upper-arm/forearm local translations. Solving only against the raw pose had left about 4 cm between the hand-held glass and its tray attachment. The bounded solve now uses the observed runtime proportions without changing the rig or physics. The close-up endpoint difference is 0.00514 cm. Five fingers wrap around the glass envelope; all other original tracks and assets are preserved. V15/V16 finger-only trials remain unadopted because they did not correct this runtime displacement.

Normal/shared service passes 4,218 samples. Counter transfers are at most 0.117 cm, hand-to-tray at most 0.0052 cm, and table transfers at most 0.201 cm in those cases. Fresh reload matches all saved fields and the subsequent saved order passes 1,762 samples. All 9,483 transforms, 225 prior non-map files, six replaced animation files and Kraken V12/nine materials are preserved. The initial adoption attempt stopped before mutation on an unavailable Python property; using the supported editor property access completed it.

Private receipts and unedited close-ups are in `ArmRepair_20261016/GripFit`; `Adopted.json`, `ServiceV18/ServiceChecks.json`, `FinalReload/Reload.json` and `FinalReload/SavedService/ServiceChecks.json` pin the result. `GripFit/Review.html` is the current review. Owner retest, broader anatomy/contact polish and the other bar acceptance rows remain open.
