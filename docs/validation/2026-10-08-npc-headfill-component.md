# Shared NPC head-fill component — build and runtime validation

**2026-10-08 update: Build49 linked/reopened; lifecycle and seven-enrollment save/reload PASS.**
Build49 supersedes Build48's object-only/unloaded boundary. This record covers the
eight-file component/adoption/lifecycle-case change. The common preset is retained
after a bounded matched comparison; fresh saved-scene Play appearance, full variant
acceptance and performance remain open.

## Change and adoption

`USSNPCHeadFillComponent` targets one explicit same-owner skeletal mesh, with no
world scan or extra Tick. It shares the accepted40lm/100cm reach/12cm source profile,
default `head` anchor and actor-frame(45,0,15)cm offset. Ambient's existing
`NPCHeadFill` point-light name/type, editable profile and refresh API remain intact;
the configuration borrows that original light. Known runtime staff hooks enroll
their selected components. `EnrollNPCMesh` supports an existing plain NPC actor
without replacing its actor, sequence, mesh or animation; repeated enrollment
reuses its configuration, and the caller owns saving.

The receiver keeps channels0/1 and temporarily adds channel2. Disable, unregister
and teardown restore its previous channel2. Destroying the configuration removes
only its own added light; Ambient's borrowed light survives. Exclusions are all
`APawn` owners (including player/ship), receivers named/tagged
`StationCompanionDrone`, owner/receiver tags `OutpostRole:Hologram`, missing anchors
and receivers without opaque/masked materials. Ambient's drone and external-animation
flags remain authoritative; other drone/projection models need explicit tags.
The female bartender's model, clip, grounding and bounds are
unchanged. Socket/offset overrides support future variants without bespoke rigs;
every variant still needs actual visual/performance review.

## Exact reviewed source

Paths are relative to `Source/SpaceSurvival/`.

| File | SHA256 |
| --- | --- |
| `Public/SSNPCHeadFillComponent.h` | `a33f76b7eb69dd77519d407bd8028ea2d97fe9fc16e2362ecb66af73bc6b5e88` |
| `Private/SSNPCHeadFillComponent.cpp` | `865f27a9494b3a10e3c60e2cd66360273e23142e25d20d6521e253f170154910` |
| `Public/SSOutpostSandbox.h` | `7a6e20a0c9f23911c23ae832d3c0148594a5fb71215c54b74e42dc60108f4b80` |
| `Private/SSOutpostSandbox.cpp` | `6e5ef7cc5f3145251c223fcf376449081b2c09e1da44b030d22a29e1ce60af53` |
| `Private/SSStationPresentation.cpp` | `652e34fe5eff14a18c9c3a530aa8578b686dc42e636f829465a0019a043985f2` |
| `Public/SSStationVisualLayout.h` | `6902e3afb1218bde2ef28cdf5bfddb9ff496c8d226262dd64ca3a9c1b8268fde` |
| `Private/SSStationVisualLayout.cpp` | `abfaffbb0b576fbc1dd7616c75f9871457080c09dd14bc2f7f278a7cee3affa9` |
| `Private/SSNPCHeadFillAutomationTests.cpp` | `076757e64ca57d865b7ca9ce628019415a0eb3b3cbb59e541e845d56acf8093a` |

## Checks and boundaries

- Independent source peer: **PASS**, including the unregister/reregister repair
  that refreshes Ambient through its authoritative profile.
- Installed clang-format dry-run on all eight files and `git diff --check`: **PASS**.
- `Scripts/CheckProject.py`: **42 checks PASS**. These are structural checks.
- Root's eight-file C++ format and Python compilation checks: **PASS**.
- Build48 `SpaceSurvivalEditor Win64 Development -NoLink -NoHotReloadFromIDE`:
  root session76866, terminal exit0,12 compile actions,99.53s: **PASS, objects only**.
  Both component and lifecycle-case objects compiled; the log has no error records. Log
  `.agent/local/StationRefinement/Build48.log` SHA256
  `25b3d3e52c21b466ec092f7cea157914eae4414a5a55e213448b895a9823b3d2`.
- Native case `SpaceSurvival.Presentation.NPCHeadFillLifecycle` requires
  the actual Nyxar mesh, opaque/masked material and head anchor; absence fails
  rather than skips. It checks idempotent enrollment, reregister visibility,
  channel restoration and owned-light versus borrowed-light teardown. Build49's
  focused NullRHI run reports **one Success**, zero failed/notRun, test warnings or
  errors, duration0.413684s and root-confirmed exit0.

Build48 retains the existing newer-toolchain and Tripo/Interchange dependency
warnings, engine C4996 notices and project-use FSlateFontInfo/InstanceBodies
deprecations; they are not new component compile failures.

## Build49 and explicit enrollment — October8 supersession

The full Editor build completed with root-confirmed exit0, five actions in2.96s
(four library/DLL links and WriteMetadata; no fresh compilation). DLL SHA256
`e2e7b5c7ba25ce9e77f50545a6dbeea3f7f29531d332b9b9f33dcd57508560ff`
was reopened in one offscreen editor, PID40232, and the reflected component class
was verified. Build49 emits newer-MSVC and Tripo/Interchange dependency warnings;
Build48's compile deprecations above remain historical. The native test's zero
warnings/errors count is test-scoped, not a claim about the whole startup log.
Root retained an initial unquoted-comma PowerShell parser failure before test
execution; the corrected command produced the successful report and native exit0.

After the R collision-profile repair and map reload, native readback finds34
existing Ambient actors, each with one configuration:25 lights visible and9
excluded. Both dirty package lists were empty at that checkpoint. This is loaded
configuration evidence, not visual approval of all34 actors.

The initial `NPC49_Enrollment.json` records `SEVEN_ENROLLED_UNSAVED`, `saved:false`
for explicit
`SkeletalMeshActor_0..6`: OrbitPool's alien shooter, trooper captain, trooper wingman
and alien partner, plus SocialAtmosphereFollowup's three conversation guests.
Each has one configuration/owned light, successful idempotence and exact preserved
pose, animation and bounds. The common40lm/100cm/12cm profile uses the mesh as
offset frame and(0,45,15)cm for those existing mesh orientations. No actor, mesh,
clip or bartender bounds were replaced.

## Captured profile and durable enrollment — October8 supersession

`NPCShared49` completes seven1014×344 ordinary Play images and technical
finalization/preservation. Independent review finds six visible faces;01 cuts off
the foreground pool shooter's face, and the two ON-only white Troopers appear
bright. That set alone does not attribute brightness to the fill.

The five-image `NPCCompare49` then passes finalization and restores both temporary
comparison-light states. Root and independent peer retain40lm/100cm/12cm: one
Trooper's white armor is already bright OFF, with no obvious worsening ON; one
seated alien gains modest face/neck readability without obvious broad room spill.
PoolWide shows the shooter's profile, near the frame's upper edge. Natural poses
and background ad phases differ; this is one matched Trooper and one matched alien,
not seven independent comparisons or a ten-variant/performance pass. Both capture
manifests preserve targeted camera/viewport/quality/map/player-save/editor-world/
dirty state and explicitly claim no full-world equality. Those photos were
`UNSAVED_EDITOR_TEST`, before the following save.

`NPC49_Save.json` records `SEVEN_ENROLLMENTS_SAVED`: seven configurations and seven
owned lights, unchanged pose/animation/bounds, map SHA256
`e7958758a861d17fe189601b17b486db9ea75086080a8e1b5f17e56cbb7b18db`.
The prior242418 map is preserved byte-exact in
`.agent/local/Outpost/RDisplay48_SaveBackup/OwnerPreview.242418-before-seven-npc.umap`.
`NPC49_ReloadVerified.json` supersedes the save record's `reload_verified:false`:
all seven reload with one configuration and visible light attached to their mesh's
`head`, common40lm/100cm/12cm profile, mesh offset frame and(0,45,15)cm offset.
Receiver/light channels, zero specular/indirect contribution and original
pose/animation/bounds are verified; both dirty lists are empty. R's existing display
adoption also passes against this final map. `owner_approved:false` remains.

Local paths below are relative to `.agent/local/`.

| Evidence | SHA256 |
| --- | --- |
| `StationRefinement/Build49/Build49.log` | `b7fa6518405f694e51a43ac2aca13dbe765daf6faed5aeeb5f4ad6c63fc14bf4` |
| `StationRefinement/Build49/NPCHeadFillLifecycle/index.json` | `75f6b41729996e1a787b94b4d9c1b80f3266373d9b21abe4d717f6b1b17231ee` |
| `StationRefinement/Build49/NPCHeadFillLifecycle.log` | `aedb6995c919d220a333f7adbd576b200f2ab1635b27c9b851a77df4ed5f8da1` |
| `Outpost/RootNPC49_Reopen.json` — reflected class, Ambient census and R adoption | `193b82c6e353c8631886d04e37e623e568f5288d27e1318458a7c42c64532853` |
| `Outpost/NPC49_Enrollment.json` — initial seven unsaved instances | `2bc28d8a12bce50d0a180d6627a8e9927c333a09f902ff50ac7e5d8846e24308` |
| `Outpost/RootNPC49_EnrollmentRequest.json` — explicit targets/profile and preservation checks | `487e093bcca9ed7d5ea36ed711bf286b571912bb3655b4bbb4aa9e91a03a800f` |
| `Outpost/LiveOperationsPIEReview1_NPCShared49/manifest.json` — seven finalized images | `d1341957b60bf7daac9a31c9a629d60460a7435a2452df127bf0210d662d2cbd` |
| `Outpost/LiveOperationsPIEReview1_NPCCompare49/manifest.json` — five finalized comparison images | `f416b6f15ef21f050a5bea7407b400b1ec96dd04d7c1b69babae96d581cbb106` |
| `StationRefinement/NPC49VisualPeer.md` — partial first views/matched preset retention | `2334f49eddb69779e9e31a8c9d3154c2a793219881ecf94deb47267f8a3bbd5f` |
| `Outpost/NPC49_Save.json` — seven enrollments/map save | `125ada9a27316f966286f1d5b536667b485b46aac3e6624310fd92bd5bcc3acf` |
| `Outpost/NPC49_ReloadVerified.json` — seven native reloads/R adoption | `72f2c060f5c1e45e7618cd8f3210daf2ea1713a6e40e4439128bae8bb2f1b41b` |

Fresh saved-scene Play appearance, continuous attachment/contact, measured room
spill/reflections, performance and full variant coverage remain unverified. The
isolated native case is not rendered scene acceptance. The documenting agent performed no
native editor calls, build or commit. Adoption steps are in
[Station editing](../STATION_EDITING.md#reusing-the-npc-lighting-preset).
