# Operations human and robot seated candidates — 2026-10-07

Status: **PARTIAL**. Two compatible seated animation candidates and their complete source skins are available. Existing Operations crew and female-alien lounge bartender are unchanged. Actual chair contact, desk clearance, full-loop fitting, natural playback and rendered appearance remain unverified.

## Scope and actual saved evidence

The owner requested a less alien-heavy Operations room. The proposed mix is two armoured humans, one scout robot and at most one retained alien on the existing four chairs. No new gameplay, population increase or bartender replacement is authorized by this candidate pass.

Root collected native exit **0** for `StationOperationsCrewCandidates1.json` (finished `2026-10-07T06:48:02Z`). Receipt SHA256: `09424ec294afc9defe0d32e83678c78c537ac85a1234bbdc2028ac84d09cd922`. Its success, source/map/save preservation, unchanged editor scene and stopped PIE checks pass. Exactly seven new private assets were saved under `/Game/OutpostSandbox/StationRefinement/OperationsCrewNonAlien20261007`:

- One owned seated-source IK rig.
- Human and robot IK rigs and retargeters.
- `A_Human_SeatedOperations` and `A_Robot_SeatedOperations`.

The source is the owned `Body_Pilot` seated motion. Nine explicit biped retarget chains, pelvis root and a separate seated alignment pose produce target-skeleton-compatible four-second clips. These are seated motions, not standing idle animations placed beside a chair.

| Candidate | Exact owned mesh | Native height | Five native seated samples |
| --- | --- | --- | --- |
| Armoured human | `/Game/SciFITrooper_Man_03/SkeletalMesh/SK_SciFITrooper_Man_03` | 184.113 cm | Knee angles 112.179–112.642 degrees |
| Scout robot | `/Game/Robot_scout_R_21/Mesh/SK_Robot_scout_R21` | 178.577 cm | Knee angles 112.967–113.229 degrees |

Samples at 0, 1, 2, 3 and 4 seconds verify target skeletons, seated leg configuration and preserved cadence. They measure bone positions, which do not establish visible skin contact. The receipt explicitly retains `contact_fit_pass: false` and `actual_contacts_and_visuals_pass: false`.

The read-only NPC section of Services5 supplies source identity and existing chair poses. Services5's aggregate failure and native `0xC0000005` shutdown remain retained history; its successful independent NPC section is not presented as an aggregate clean pass.

## Contact export attempts

`Scripts/InspectStationOperationsCrewContacts.py` and the ignored root launcher `probe_operations_crew_contact1.py` prepare one read-only current-map export. No actors, bones, clips, materials, settings or map files are authored by this probe.

- Count both exact source meshes before exporting arrays; retain strict 60,000 vertices and 200,000 triangles per candidate.
- Read every source vertex's skin weights in chunks of 128 per Slate tick. No filtered contact subset is presented as full skin.
- Retain actual twelve chair-part and four footrest transforms and native source triangles. Record the four desk bodies separately, with triangle/contact status explicitly unmeasured.
- Export five raw compatible native poses and compare native component-space bones with deterministic hierarchy reconstruction before using offline skin calculations.
- Guard all seven saved candidate assets, original sources and exact Main1 preview. Separately bind failed Remainder4 receipt `822d176b0b80723df3548470de04d89b6914613605e3f2acd8975a0c09a03c73` and its 36 retained packages: 34 materials, saved private Home map and unchanged initial Cargo copy. Exact package population and hashes must survive the probe. Remainder4 is not treated as a successful station floor save.
- Write progress before native copy stages. The Python bound is 300 seconds; root owns a 330-second external process watchdog because synchronous native calls cannot be interrupted by Python.

Python AST/compile checks pass for the prepared files. Native source counts, skin weights, chair surfaces, fitting and appearance are still pending. A successful export supplies fitting data; it cannot approve an installed operator or claim room quality.

2026-10-07T07:13Z [TOOL] The final read-only wrapper `1c87c27d95d7073a181abc7f780ebc3771b98116428e492e88bace98c0c1934c` and helper `a5136920140fd33dd93de331baa0bdccf72bcfafd40f3b54dde081bc3b7cf283` have independent source review. The earlier wrapper `60b30cd0...` is preserved unrun. Root owns the serialized native launch and actual exit; contact fitting remains pending.

2026-10-07T07:27Z [TOOL] Supersedes attempt1's pending execution: root collected native exit0 and aggregate **FAIL**, receipt `ce3d2154882b821ec05d899dfd78943f5490b88c4cf1b40fcf018e8c12686caa`. Protected files, three production saves, all 36 partial floor packages and the exact editor scene remain unchanged. The real footrest Cube exports 26 vertices/48 triangles. The first chair source, `SM_TitaniumIndustrySeat_V1_Part1`, contains 308,395 vertices/616,454 triangles and fails the strict full-array export budget before either model is exported. No geometry, skin weights or contact result is fabricated for the chair or models.

NEW `Scripts/InspectStationOperationsCrewContacts2.py` (`75fa04448041d13497070dda14754a5ec479b16efe8266810b99f6ed8e6ac62f`) collects both full model skins independently before fixtures. A failed model or unrelated fixture diagnostic retains any other completed model artifact. Dense chairs remain in native BVHs: exactly three source meshes receive 357 downward rays each in 24-ray chunks; only actual hit triangles and normals are exported, capped at 2,000 hit triangles per part. The native BVH source budget of one million triangles is separate from the unchanged 200,000-triangle full Python-array budget. Sampled support coverage is explicitly incomplete; continuous body/chair clearance and per-frame native skin contacts remain separate gates.

The new wrapper `bb9c21db7923aaa38d44565ef88627c6f672bdded3dffaea502e120cc8615293` has bounded independent review and AST checks. It preserves failed attempt1 and its Cube artifact, Main1 sources, seven saved candidate assets, and all 36 current floor derivatives. It accepts exact Main1 or successful Final6 evidence; failed Floor5's saved Home/Cargo outputs are protected without treating that failed author as complete. The root-owned external watchdog remains 330 seconds. Source structural checks pass40; no new C++ build is required for these read-only Python helpers.

2026-10-07T07:44Z [TOOL] Supersedes attempt2's pending execution: root collected native exit0, exact editor/source/save preservation PASS, and aggregate **FAIL**. Receipt `bfe82d76f2cc417a8ac42d8f94aa4456d97773008f33a38f5dbb6e81836639ca` retains both independently completed models in `ContactAuthoringInput.json`, SHA256 `f4aec0a034c17cc563da70a838a79cac78e7a2f516209fa03f5dceffc8522773`:

| Model | Full vertices and weights | Source triangles | Bones | Raw native poses |
| --- | --- | --- | --- | --- |
| Human | 11,693 | 21,920 | 76 | 0/1/2/3/4 seconds |
| Robot | 18,850 | 21,503 | 68 | 0/1/2/3/4 seconds |

Native/offline hierarchy reconstruction passes for both models. The actual Part1 chair base provides 357 rays/236 hit triangles; its centre is Z12.091 cm, which is not the seat. Part3 provides 357 rays/10 hit triangles for upper fittings. Part2, which supplies the cushion/armrests/back, has 691,725 vertices/1,382,533 triangles and fails the unchanged one-million-triangle BVH budget. The completed skins are retained; no fit to the base or fabricated Part2 contact is accepted.

NEW `Scripts/InspectStationOperationsSeatSupport3.py` (`2ad4c027ab3790d3a67eae8573fda998c5d143a1b47850978460080bbf87ae10`) and ignored `probe_operations_seat_support3.py` (`63cb84efc5a31a9edfe321b9662425ae5c021b494d070de824769d72b29e5f8a`) prepare a Part2-only read-only query. Native box selection and transient copy isolate two overlapping seat/arm/back contact regions. Each must remain within the existing one-million-triangle BVH limit; only actual ray-hit triangles are exported, capped at 2,000. The 126 rays retain misses as unknown. Original source counts/bytes and all existing chair/operator/footrest poses are guarded. It accepts exact saved Final6 or Opaque2 evidence, without repeating either model export. Native execution and peer review are pending; the Python/external bounds are 120/150 seconds.

2026-10-07T07:44Z [CODE] A pure ignored fitting draft follows actual skeleton ancestry to classify skin. Trooper muscle/twist bones must count as their measured thigh segment; the dominant bone is never literally `thigh_l` for its thigh vertices. Five-phase offline preparation fits both unit-scale models' visible boots inside the measured Cube footrests and gives actual hand-skin/thigh gaps around0.6 cm, preserving limb translations/scales. This uses the older Z60.267 seat coordinate explicitly labelled **native Part2 support pending**. It is not chair-contact closure, a full121-key pass, an authored animation or a rendered review.

## Remaining acceptance

Fit the human and robot to actual cushion surfaces and footrests or floor without changing limb lengths. Check visible feet, pelvis, hands and desk/body clearance across the animation loop. Then install only the bounded three operator replacements and review actual game images and playback before treating the room mix as accepted. Preserve the fourth alien and the female-alien bartender.

Root alone owns native execution, saves, integration and visual acceptance. This work is not packaged or published and does not satisfy the Operations 9/10 gate.
