# Open work and owner review

**Start here. This is the single active issues, follow-up, action and priority log.** Updated September 16, 2026. Phase 1 remains PARTIAL.

## Current instruction: hold ACT-03 and return to other open issues

**Owner direction, September 16:** hold further environment/area iteration for now. The owner considers the current scenes improved enough to pause, but did not accept the visual target or close ACT-03. The earlier instruction was to continue until target agreement; stopping at a documented NOT MET checkpoint did not fulfill it. Preserve the current scene and remaining acceptance gaps. Other issues remain in the existing queue; ACT-01 flight/input/propulsion is the next listed production action. No new repair, merge or publication is claimed by this status update.

**September 16 implementation checkpoint: PARTIAL; flight target remains NOT MET after independent review, with the lead agreeing.** Four real area recipes now exist: Obsidian Wreck, Mineral Reach, Alien Causeway and Amber Derelict. World-fixed cells choose coherent authored groups and weighted clutter from the persistent run identity; preview recipes/variations remain reproducible. Three private broken assemblies use the owned alien kit's solid pieces. Richer distant asteroid bands continue through quieter local space. Lighting/haze palettes vary by area. This supersedes the prior proposal-only/fixed-twelve-placement state; it does not change wave durations, progression or Director hazards.

**Art target and closure rule:** the supplied dark metallic wreckfield plus accepted orbital-wreck concept govern scale, irregular structure silhouettes, receding debris, thin depth haze and readable ship/aim space. Dense distant fields should usually remain visible even when foreground space opens up. Lead and independent agent must agree against actual game captures. Counts, build passes and concepts cannot close ACT-03. First area renders were rejected for flat panels, sparse backgrounds and weak depth; their evidence is retained. Current receipt: [area/gallery review](validation/2026-09-16-space-areas-gallery.json).

**Lead-owned acceptance work when ACT-03 resumes:** replace isolated distant scatter with overlapping receding clusters and depth-dependent contrast; assemble alien slabs/arcs into thick architectural groups; remove large masses from the turned ship/aim backdrop. The spherical far distribution improved angular coverage but did not meet the target. Four area previews and a second wreck arrangement exist; compare their final candidate against its target; then demonstrate sustained approach, sparse/dense transition, actual cell crossings and revisit. New cells currently appear/disappear immediately. World-fixed decorative structures have no collision and can be approached through arbitrary routes; the cell-center clearance test is not safe near-surface traversal evidence. Resolve visible boundary changes and the visual/physical mismatch before calling the long-zone experience complete. Continuous motion, natural combat readability and representative performance remain unverified. Do not add collision hazards or alter balance merely to hide a scenery problem.

**Station alien evaluation doorway:** implemented and independently accepted for the bounded rendered entry → full vendor showcase → full asset-layout map → return path. In the rebuilt development game, use E/A at **ALIEN WORLD**; Tab/Y switches maps, Esc/B returns. Run/account and station position are preserved in the scripted round trip. Both vendor maps remain unchanged on disk. First asset-view capture showed only floor; corrected framing visibly includes the modular inventory. Physical input, close inspection/reset and a packaged launch remain open. [Controls and authoring](STATION_EDITING.md). This is an evaluation space, not a new gameplay planet or station rebuild.

PR17 remains draft and unmerged. **The existing packaged EXE and itch 0.1.16-alpha.1/build1979965 do not contain these changes.** The earlier flight/combat slice, cubic-thruster report, natural audio/input checks and wormhole-plugin pilot remain open under their existing ACT/ISS/RPT entries. No purchase, package or publication is required to continue this editor review. The Station Workshop remains available for owner composition work.


### Newly reported bugs — open, capture only

These are paraphrases of the owner's reports, not reproduced findings. Report context follows the 0.1.16 release, but the exact launched build and device/settings are UNCONFIRMED. No fix, retest or acceptance closure is claimed.

| Report ID | Owner observation | Tracking / later verification |
| --- | --- | --- |
| RPT-20260914-01 | Inverting flight controls also inverts character controls. | ISS-05; PT-05,10,15–17. Later verify independent flight/on-foot pitch preferences and persistence. |
| RPT-20260914-02 | Can walk through nearly every station object, but movement is blocked at the words/labels. | ISS-03; PT-10,17. Later map visible geometry to actual collision and service reachability; the report does not prove text geometry itself is the blocker. |
| RPT-20260914-03 | An NPC is stuck in a table. | ISS-03; PT-10,18. Later identify the NPC/location and check body/furniture overlap in natural play. |

Additional owner reports (capture only; same unconfirmed build/device boundary):

| Report ID | Owner observation | Tracking / later verification |
| --- | --- | --- |
| RPT-20260914-04 | The base weapon barely shows anything coming out of the front. | ISS-01/06; PT-06,18. Later review muzzle/projectile visibility from the normal chase camera. |
| RPT-20260914-05 | Combat feels like Space Invaders: enemies line up ahead to shoot rather than create a dynamic space fight. | ISS-06; PT-06,12. Later review approaches, lateral/vertical motion, maneuvering and pressure in natural combat before choosing changes. |
| RPT-20260914-06 | Backgrounds still look graphically weak and fuzzy, like low-resolution artwork. | ISS-01; PT-03,18. Later compare actual runtime resolution, filtering and source imagery; cause unconfirmed. |
| RPT-20260915-07 | The ship died while pulling into the station after catching an entrance edge, bouncing off several times and taking repeated collision damage. | ISS-03/06; PT-09,12,13. Capture only. Later reproduce with the exact build, approach speed/angle and hull state; review entrance snag points, repeated-impact cadence and docking-assist recovery before changing collision. |
| RPT-20260915-08 | Thrusters look like cubes. | ISS-01/02; ACT-01; PT-03,18. Owner report plus confirmed Cube-based emissive cores in SSAmbientPresentation.cpp. Unfinished, not fixed: audition tapered exhaust/soft glow from owned effects and verify idle, acceleration, boost, brake and damage in motion. |

Owner subsequently authorized the editor workshop and this bounded presentation slice. The unrelated bug-fix pause remains in force.

Lead maintains these reports here while the owner continues listing observations. Existing acceptance cases remain open. Reproduction and repair are paused until the owner resumes them.

## Review route when playtesting resumes

**For the new area/gallery work:** open `C:/Users/j6sis/SpaceSurvival/Play Development Build.cmd`. Its separate development profile keeps the installed game's saves apart. First visit **ALIEN WORLD** in the hangar, inspect the showcase, Tab/Y to the asset layout and Esc/B back. Current scene quality and lead-owned remaining checks are at the top of this log. The older packaged route below remains for release-specific PT checks.

The new local visual build is ready for owner review: **Package 4, source `cf6296f`**, at `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows/SpaceSurvival.exe`. Keep the entire folder. It includes the provisional Havolk starter hull, refreshed space/combat presentation and furnished, editable station. The [project state](PROJECT_STATE.md#source-build-and-release) identifies this build and the now-published itch 0.1.16-alpha.1 / build 1979965. Close the game and update through the itch app on windows-alpha to review that version.

1. **Check the flight view first.** Open the executable, set controller sensitivity and preferred pitch direction, then launch and try ordinary turns, boost and brake. Judge the new starter silhouette, exhaust attachment, camera framing and hazard visibility against the space lighting. Relevant cases: PT-01,03–05,15,18.
2. **Check combat cues.** Fire at a target and look for a clear distinction between a shot, a hit and a confirmed death while hazards are present. Report the single most confusing moment, with a clip or screenshot if useful. Relevant cases: PT-06,12,18.
3. **Try one lasting station edit.** Open `C:/Users/j6sis/SpaceSurvival/SpaceSurvival.uproject`, then use **Tools > Station Workshop** and the [first-edit guide](STATION_EDITING.md#first-edit). Move or add one prop, Save + Apply, then open the normal Survival map and restart Play to see it in the station. Keep the marked corridor and fixed service anchors clear; check furnishings, robot staff and service-label readability from both sides. This editing check does not close the natural station cases PT-09,10,17,18.

When the owner resumes structured review, start with item 1; the lead records your build, device/settings and observations against the corresponding IDs, then brings you back to the next unresolved step. You do not need to edit Markdown or remember the full checklist. Partial observations leave the corresponding acceptance case open.

Technical validation: 49 Unreal tests passed cleanly at 23:57:10 UTC on September 14, covering the unchanged C++ implementation. The subsequent star-material change was authored, cooked and rendered separately. Package 4 passed its actual IoStore export/import audit and both packaged visual captures: 4 Wave 1 images and 16 Station 5 images. [Current validation](validation/2026-09-14-visual-enhancement-stars.json) binds the source, private inputs and actual package. Scripted captures and automated checks do not close natural play, visual quality or representative performance acceptance.

The new slice is **source/editor evidence only** and is absent from Package 4 and itch. Its final editor build, 49/49 headless suite, 1/1 rendering-enabled VFX lifecycle test and current fixed captures are recorded in the [September 15 validation section](VALIDATION.md#september-15-flight-combat-and-space-slice). Use those captures for review; keep Package 4 as the last published executable until this source is packaged separately.

## Current action queue and ownership

The sequence below is the active execution order. It covers the whole Phase 1 experience and keeps station work from hiding flight, combat, space, UI, audio, persistence and release gaps. An action starts only after owner direction; later actions remain visible while the active action is being reviewed. The lead owns integration and evidence. The owner supplies feel/art decisions after a concrete review build, and the regular 3D contributor owns the long-term hero and iconic starter.

| Order | Action | Scope and linked issues | Lead next action | Observable closure |
| --- | --- | --- | --- | --- |
| 0 | **ACT-00 — Asset Lab and evidence gate** | ISS-01/02/03/06/08/09/16 | After the owner starts implementation, establish one lightweight audition level, inventory the exact candidate dependencies and record each selection as **owned → imported → referenced → visible → accepted**. Use UAsset Browser if acquired; it is a selection aid, not acceptance. | At least one rejected and one selected candidate are shown for each role in the first slice; selected dependencies and license/source boundaries are recorded; no full pack is copied merely to browse it. |
| 1 | **ACT-01 — Flight, camera and propulsion** | ISS-02/05/08/10/12; PT-01–05,15,16,18 | Compare the current chase view and Havolk assembly against the target in ordinary turns, boost, brake and dodge. Audition owned trail/exhaust candidates and separate ship, camera and on-foot input settings. | Ship remains framed and readable; thrust states are visually/audibly distinct; KBM and controller settings behave independently; natural-play and packaged evidence pass. |
| 2 | **ACT-02 — Weapons and dynamic combat** | ISS-01/06/08/10/12; RPT-20260914-04/05; PT-06,12,18 | Build one complete Rapid Laser and Heavy Cannon cue chain: muzzle, travel, impact, shield/hull response, kill and synchronized sound. Exercise lateral/vertical pursuit, approach, evasion and cover instead of front-line formations. | Both weapons and enemy roles remain distinct in a busy fight; shots, hits and deaths are unmistakable; enemies maneuver in three dimensions; readability and frame-time checks pass. |
| 3 | **ACT-03 — Asteroid field, debris and regional depth** | ISS-01/06/10/12/16; RPT-20260914-06; PT-03,06,09,12,18 | Compare the current custom field with Asteroid Library's Linear, Globular and Arch Blueprints; evaluate unused mineral/fragment families, close/mid/far materials, dust and ambient landmarks. Diagnose actual background resolution/filtering before replacement. | Different area scenes have deliberate near/mid/far silhouettes, distinct structures/materials, lighting and thin local haze. Open foregrounds reveal rich distant fields; approach, sparse/dense transitions and revisits remain coherent across run variations. Independent multi-area visual review and separate performance evidence pass; hazards stay readable. |
| 4 | **ACT-04 — Wormhole and distinct destination** | ISS-01/06/10/16; PT-09,12,13,18 | Run a controlled Wormhole Portal plugin pilot against the custom system, then combine the selected transition with owned nebula/galaxy/cosmic resources and a clearly different destination composition. | Approach, transit and exit read as one continuous event; the destination is immediately unfamiliar through structure, light, particles and landmarks; plugin cost/dependencies and fallback are documented. |
| 5 | **ACT-05 — Station arrival, exterior, interior and services** | ISS-03/04/09/10/13; RPT-20260914-02/03 and RPT-20260915-07; PT-09–13,17,18 | Reproduce entrance damage and collision reports, define a compact floor plan, connect the exterior to a believable entrance, and compose modular architecture before decorative props. Preserve service/save rules. | Arrival, docking, entrance, walking, services and departure form one coherent route; visible solids have suitable collision; labels do not block movement; service anchors remain reachable; Station 1 and 2 natural-play cases pass. |
| 6 | **ACT-06 — Character, NPC and station-life pass** | ISS-02/03/08/10/16; PT-01,10,18 | Validate temporary hero locomotion and exit animation; give robots/troopers/drone safe anchors and a small number of purposeful idle, patrol or work loops using owned animations. | Hero motion has no major deformation or foot/turn errors; NPCs do not intersect furniture; station activity has clear roles and stays within navigation, collision and performance limits. |
| 7 | **ACT-07 — Workshop semantics and reusable composition** | ISS-03/09/14/16 | Extend the existing decorative bridge only where needed for collision role, grouping/prefabs, snapping and repeatable Level Instance/Blueprint composition. Keep gameplay anchors guarded. | Owner can place and revise a representative room or exterior module, apply/export it, reopen it without drift, and identify which objects are decorative, blocking or interactive. |
| 8 | **ACT-08 — Audio, UI and input glyph integration** | ISS-05/08/13/16; PT-05–08,10,15–18 | Audition the selected audio by role, tune loops/mix/concurrency, and implement one shared action-to-input prompt path with device switching and text fallback. | Flight, combat, warnings, rewards, wormhole and station cues remain distinct; prompts match actual bindings/controller family and remain legible in busy scenes. |
| 9 | **ACT-09 — Progression, objectives, save and release safety** | ISS-04/07/11/13/14/15; PT-07–17,19 | Exercise the two-block loop, objective acceptance/outcome, depot, contracts, upgrades, death/unlock/retry and suspend/resume; finish private-asset backup and clean install/update checks. | Phase 1 progression and persistence cases pass without state loss; clean-machine/itch update identity is verified; paid/private assets remain out of Git; repository documentation enforcement is active. |
| 10 | **ACT-10 — Representative performance and final acceptance** | ISS-01–16; PT-01–19 | Profile the selected content in a natural busy run, complete Waves 1–10 and both stations with physical devices, and package the exact reviewed source. | All applicable PT cases have build/device/evidence records; representative 60 FPS target is assessed with frame-time distributions; remaining limitations are explicit; only then may Phase 1 move from PARTIAL. |

For each action, component count, successful import, Blueprint compilation, automated tests and a still image are intermediate evidence. Player-visible motion, sound, collision, interaction, representative performance and the exact packaged build determine acceptance. Fixed comparison cameras and short natural-play captures should use the visual target before/after whenever presentation changes.

### September 15 ACT-00–ACT-04 checkpoint

| Action | Implementation/evaluation checkpoint (`b6c58b8`, ACT-03 updated at `16007ab`) | State that remains open |
| --- | --- | --- |
| ACT-00 | Audited Asteroid Library's three construction-script field Blueprints, five sky candidates, Cosmic Material instances, Nerves, Niagara Examples, Sci-Fi Weapons VFX and the installed Wormhole Portal plugin. Fixed capture rejected the two Free Galaxy cubemaps from the region rotation after they produced a weaker sparse black/red scene; the three NebulaFantasy regions remain selected. | The audit is not a reusable audition level and no candidate is accepted from inventory alone. Private/vendor content remains outside Git. |
| ACT-01 | Drive state now reaches presentation; two nozzle cores, localized lights, trail scaling and speed-oriented dust distinguish idle/acceleration/boost/braking/damage in code. A first capture exposed hull washout; reduced emission and light radius restore readable ship surfaces. | RPT-20260915-08 records unfinished cubic thrusters. Fixed Boost/Brake stills do not show enough state distinction for acceptance. Natural motion, listening, package cooking, physical controls and owner judgment remain open. |
| ACT-02 | Rapid Laser, Heavy Cannon and enemy bolts have distinct native cores and bounded projectile lights even when optional Niagara is absent. Muzzle/impact/explosion light pulses are bounded. Pursuer/Flanker motion gains vertical/lateral/longitudinal variation and banking. The Nerves-derived electrical field and Sci-Fi Weapons discharge are authored private effects. | The scripted real-kill frame shows a visible spark/fire impact but cannot establish complete muzzle/travel/hit/death chains, audio sync, allegiance readability, dynamic combat feel or representative cost. RPT-20260914-04/05 and PT-06/12/18 remain open. |
| ACT-03 | Constructed and rendered all three native fields (336 instances each); baked their positions into private presentation data. Runtime uses 15 barren/mineral/fragment/debris meshes, four bands and the unchanged 384-instance budget. Sustained-travel parallax no longer saturates; dust is 320 smaller grains with less stretch. Fixed 2K/4K sky comparison selects 2K BC6H from the existing 8192x4096 source panoramas. [Evidence](validation/2026-09-15-asteroid-depth.json). | PARTIAL. Continuous-motion review of scale fading/recycling, natural near/mid/far depth, focal contrast, early hazard pressure, background fidelity and representative performance remain open. Native auditions are composition references, not matched-density gameplay benchmarks. No new package or owner acceptance. |
| ACT-04 | Wormhole Portal 1.0 is installed for UE5.8/Win64; 309 plugin assets and its runtime/sample/renderer/editor modules plus EnhancedInput/StateTree dependencies were inventoried. | Plugin is not enabled, spawned, cooked or timed. Current captures still show the custom ring transition, so approach/transit/destination acceptance remains open. |

### Owned-first purchase gate

Do not recommend or purchase another flight, combat, VFX, environment, audio, UI or workflow pack until the active action records all four points below:

1. The exact missing player-facing capability, with a target frame, clip or reproducible scenario.
2. The owned candidates already examined and their **owned/imported/referenced/visible/accepted** states.
3. Why each plausible owned candidate failed the role after a bounded audition, including quality, control, compatibility, dependency or performance evidence.
4. What the proposed purchase uniquely supplies, where it enters the action, and how it will be accepted in natural play.

A listing's screenshots, feature list or similarity to the target is discovery evidence only. Overlap belongs in the solution catalog. A purchase is justified by a demonstrated capability gap, not by incomplete use of an existing pack.

### Transfer packet for another model or contributor

Work on only one ACT item at a time unless its row explicitly requires a paired slice. Before handing it off, leave this compact packet in `.agent/CONTINUITY.md` and the PR's **Open / Check / Still open** section:

- **Action and objective:** ACT ID, linked ISS/RPT/PT IDs, and the exact player-facing result.
- **Authority and limits:** relevant GAME_SCOPE/IMPLEMENT requirements, explicit owner decisions, protected behavior and excluded work.
- **Current state:** branch, exact head, open PR, source/package/itch distinction, and whether private licensed content is required.
- **Inputs:** owned asset IDs/paths, target references, relevant skills to read, and the last accepted fallback.
- **Evidence:** baseline captures or reproduction, commands already run, receipts, observed failures and acceptance still missing.
- **Next operation:** one concrete bounded step, expected outputs and the condition for stopping or asking the owner to review.

The receiving model should begin from this packet and current files, then verify drift cheaply. It should not repeat the whole library audit, reinterpret scope or start a later action because the active action is difficult. Partial work updates the same ACT/ISS rows and remains open.

No other document maintains a separate active priority order. The [solution catalog](production/SOLUTION_CATALOG.md) records candidate value and utilization, not purchase authorization or scheduling. Work-package and Phase 2 documents provide context only; the action IDs above own current order.

## Art ownership

Owner decision, September 14: the regular 3D contributor owns the hero and iconic starter ship long term. The lead owns Unreal integration, collision/scale/socket/material checks, gameplay testing and packaging. Supplied AI models and kitbash alternatives are provisional, not replacements for that contributor's design ownership.

The owner purchased catalog C23, Space Ship 02 Modular Pack (Havolk). Its prepared assembly now supplies the default closed-cockpit starter, with the seated pilot hidden during flight, plus matching tier/utility hardware and the existing enemy-role derivatives. This is a provisional kit interpretation awaiting owner art review; Phase 1 still contains only the starter and scoped second ship. Future ship content stays deferred. ISS-02 owns art follow-up and ISS-14 the collaboration/storage setup; the owner confirmed the collaborator delivers model/texture/animation files only, not Unreal project edits. A private versioned Drive handoff is the proposed starting workflow; destination/access setup remains open.

## Implementation and verification issues

These are grouped problems, not extra game features or a completion percentage. Related PT cases below describe how to validate them. **All rows remain open.** A status of *Needs owner retest* means a bounded repair exists, not that the issue is accepted.

| ID | Issue and evidence boundary | Status / owner | Next action and closure evidence |
| --- | --- | --- | --- |
| <a id="iss-01"></a>ISS-01 | Space depth, lighting, VFX and wormhole arrival remain unaccepted against the visual target. The packaged pass includes three blended owned nebula cubemaps, warm key light, eight ambient rock shapes, smaller dust grains, distant structures and bounded combat effects. Package 4 reduces the previously overpowering stars, but RPT-20260914-06 still describes fuzzy, low-quality backgrounds. The native Asteroid Library field Blueprints, broader Niagara library, Free Galaxy Shader, Cosmic Materials and installed Wormhole Portal plugin have not been accepted as an integrated moving experience. Nozzle/exhaust response, parallax, directional variety and unfamiliar arrival feel remain open. [Combined record](production/COMBINED_SPACE_LOOK.md). | Needs integrated visual review / lead | Execute ACT-01/03/04 from fixed target cameras and natural combat. Close only with accepted motion, focal contrast, depth, destination differentiation and packaged performance, not asset presence or a screenshot alone. PT-03,09,12,13,18. |
| <a id="iss-02"></a>ISS-02 | Hero/ships and continuous animation remain provisional. The default starter is the purchased Havolk closed-cockpit assembly; only a small subset of the modular ship pack is visible in normal progression despite its value for tier silhouettes, enemy roles, ambient traffic, wreckage and hangar previews. When the owned Sci-Fi Space Character packages are present, the station walker uses that temporary hero with matching walk and exit animation; missing/incompatible content falls back to Acornaut. Automation covers both routes, but rendered/package review and natural motion remain open. The regular contributor still owns the long-term hero and iconic starter. [Current validation](VALIDATION.md), [earlier refresh](ASSET_REFRESH.md). | Needs owner retest + art work / regular 3D contributor; lead integrates | Use ACT-01/06 to judge the hull, fitted modules and temporary hero in motion; validate scale, sockets, collision, materials, animation and package cooking. Preserve contributor ownership and original sources. PT-01,03,10,18. |
| <a id="iss-03"></a>ISS-03 | Station arrival, composition, physical coherence and ambience remain unaccepted. Capture-only reports RPT-20260914-02/03 and RPT-20260915-07 describe walk-through props, blockage near labels, an NPC intersecting a table and repeated collision damage after catching an entrance edge; causes remain unconfirmed. The saved 380-component Blueprint demonstrates dressing breadth, but much of that dressing is nonblocking and the main exterior mass does not yet establish a continuous exterior-to-interior route. Owned modular architecture, screens, electronic-prop Blueprints, station GLBs, robots and character animation remain lightly used. Native services/save rules stay authoritative. [Station editing](STATION_EDITING.md). | Needs reconstruction and natural review / lead; owner composes/reviews | Execute ACT-05/06/07: reproduce defects, establish floor plan/entrance/collision roles, then add purposeful architecture, activity, lighting and sound. Close with natural approach, traversal, services, exit and package evidence. PT-09,10,12,13,17,18. |
| <a id="iss-04"></a>ISS-04 | Station 2 services/save/discard boundary needs usability and replay-appeal acceptance. Actual failure/retry persistence tests exist; no Wave 11 or completion XP is authorized. [Boundary evidence](STATION2_DISCARD.md). | Needs owner/QA verification / lead | Natural arrival, service/save/discard and next-run review. Preserve disclosed zero-death-XP discard. PT-13,14,17,19. |
| <a id="iss-05"></a>ISS-05 | Input comfort, camera framing and full physical-device parity remain unaccepted. B23 glyphs have local artwork/dependency inspection and a [selective integration record](production/SOLUTION_CATALOG.md#new-local-audio-and-glyphs-evaluation-and-selective-integration); glyphs, device switching and mapping changes remain unimplemented. New capture-only report RPT-20260914-01 says flight inversion also changes character controls; independent preferences need later verification. Station rear-camera, inversion and flight framing fixes exist. Owner feedback F01/F09/F10 says starter handling is decent but inverse mouse was a barrier; controller is preferred. [Camera](STATION_CAMERA.md), [environment](ENVIRONMENT_REFRESH.md). | Needs owner retest / lead | Calibrate preferred inversion/sensitivity before retuning; verify KBM and controller, reconnect and menu focus. PT-02–05,15–17. |
| <a id="iss-06"></a>ISS-06 | Natural combat, hit/death certainty, target identification, reward cadence and Director fairness need integrated play. RPT-20260914-04 says the base shot is barely visible; RPT-20260914-05 says combat feels front-lined rather than like a dynamic space fight. Existing bolt/muzzle/impact/explosion effects and deterministic projectile/fragment/admission repairs do not settle feel or balance. The real-kill fixture verifies explosion activation, but a visible fire/smoke plume remains unverified. Hundreds of owned weapon/Niagara candidates have not been compared as complete role-based cue chains. [Gameplay repairs](GAMEPLAY_QUALITY.md), [combat cues](COMBAT_CUES.md). | Needs integrated combat slice / lead | Execute ACT-02: compare owned effects for muzzle/travel/impact/kill, synchronize audio/light, and test both enemy roles with lateral/vertical maneuvering amid hazards. Preserve manual aim and scoped rosters. PT-06,07,09,12–14,18,19. |
| <a id="iss-07"></a>ISS-07 | Save safety is verified only within bounded fault cases. Disk-full/short-write, arbitrary binary corruption and hardware-loss remain untested; generic Windows backend only, no multi-slot transaction/automatic backup. [Fault](validation/2026-09-13-storage-faults.json) and [corruption](validation/2026-09-13-corrupt-account.json) evidence. | Needs qualification / lead | Isolated profiles and guarded reproducible failure tests; preserve owner saves. Record unsupported cases honestly. PT-11,14,17 for natural UI path. |
| <a id="iss-08"></a>ISS-08 | UI/audio/music need actual listening and busy-scene review. The A21/A22 inventory covers 1,410 recordings plus cue wrappers. This owned-asset pass selects ten A22 roles for engine, weapons, impact, pickup, alarm, station ambience and enemy/debris events; runtime references prefer the private licensed assets and fall back to generated sources when absent. Editor build and all 49 automation tests pass, but listening, loop-seam/mix judgment and package cooking remain open. Glyph integration is still pending. [Audio hooks](AUDIO_HOOKS.md). | Needs acceptance / lead | Listen through flight, combat, arrival and station; tune distinction, levels, looping and concurrency from evidence. Then evaluate the limited glyph sample without coupling it to inversion repair. PT-05,06,10,16,18. |
| <a id="iss-09"></a>ISS-09 | The owner-authorized editor workshop adds asset-browser placement/rotation/scaling/deletion, ten materials and saved-map application/export in PR14; Editor build, nine save/apply/export checks and the visible asset-browser capture pass; [receipt](validation/2026-09-15-station-workshop.json). The owned-asset follow-up validates **708** filtered placeables: 702 under `/Game` plus six engine basic shapes, including 26 Sci-Fi Space Character, two Heavy Space Trooper, two Cosmic Material and one private drone entries. Material assets remain available through the Details panel; the curated preset list stays at ten. [Station editing](STATION_EDITING.md) describes the controls and supported-content boundary. Gameplay collision/service anchors and native menus/behavior remain separate. | Needs review / lead | Place, transform, material-swap, delete, export and apply a representative new asset; verify the saved scene in play. Keep unsupported behavior actors and gameplay anchors outside the decorative bridge. |
| <a id="iss-10"></a>ISS-10 | Representative 60 FPS/full-run CPU/GPU/RAM/VRAM acceptance is open. Older RTX 5080 scripted samples are bounded; current Wave1 capture includes readback/startup stalls, and standard analyzer rejects that scenario. [Performance](PERFORMANCE.md), [combined diagnostic](production/COMBINED_SPACE_LOOK.md). | Needs qualification / lead | Fix/extend scenario analysis where justified, profile a natural busy run and scaling; report frame-time distributions and hardware. No claim of “120 FPS accepted” from capped screenshot fixtures. |
| <a id="iss-11"></a>ISS-11 | Distribution: clean-PC startup and real itch A-to-B update/save preservation remain unverified. The new local Package 4 passed its actual archive/dependency audit and both packaged visual captures. The owner authorized PR11/12 merges and the itch update on September 14. Release preparation found runtime saves/config/logs in the archive; the publisher now filters them and rejects unsafe prepared payloads. The clean 0.1.16-alpha.1 payload is verified ready as itch build1979965; the release record owns its full identity. The new devlog remains a draft pending browser security/sign-in. [Release workflow](ITCH_RELEASES.md). | Needs release/QA follow-up / lead | Finish the devlog after browser sign-in, then test clean install/update with preserved saves and version identity. Merge is not publication. |
| <a id="iss-12"></a>ISS-12 | Continuous contact uses linear per-frame player/shot motion; enemy/world-cover queries use current transforms. Nonlinear paths inside a hitch are not reconstructed. [Gameplay follow-up](validation/2026-09-13-gameplay-fairness-followup.json). | Known approximation / lead | Reproduce an unfair contact before broad redesign; retain first-contact/cover-order regressions and document practical hitch limits. PT-04,06,12. |
| <a id="iss-13"></a>ISS-13 | Event/depot/contract/beacon clarity and live input need retest. F02/F03/F04/F07/D01 map here: following distraction, unclear objective/beacon/allegiance, and optional magnetic parking. Mooring/feedback repairs exist. Issue #7 additionally flags live reward device differences and synchronous tutorial saves; runtime impact is not established. [Feedback provenance](production/OWNER_FEEDBACK.md), [review issue](https://github.com/j6sistek-ui/SpaceSurvival/issues/7). | Needs owner retest/investigation / lead | Verify explicit acceptance, objective/progress/outcome, 20-second aboard-ship lock/release and no lingering follower; reproduce input/write risks before claiming a fix. PT-07,08,10,16,17. |
| <a id="iss-14"></a>ISS-14 | GitHub is not a complete backup of local licensed derivatives, raw downloads, manual tuning, art experiments or saves. Source-export checks do not reproduce the current licensed look from Git alone. [Storage map](PROJECT_STATE.md#where-files-live), [source integrity](SOURCE_INTEGRITY.md). | Needs collaborator handoff/backup plan / lead + owner for storage choice | Choose the shared handoff destination, then inventory unique inputs and document private backup/reacquisition, versioned upload, import and restore paths. See the proposed asset collaboration workflow in Project State. Verify a fresh development setup without publishing paid source assets. No cleanup/deletion is implied. |
| <a id="iss-15"></a>ISS-15 | PR documentation enforcement: template/CI check merged through PR11; last ruleset audit requires PRs but no successful status checks. A running check is not yet a server merge requirement. | Needs repository setting / lead | After explicit repository-setting approval, add the verified documentation job to required checks while preserving existing rules. Confirm a failed check blocks merging. No branch-rule change is claimed by this PR. |
| <a id="iss-16"></a>ISS-16 | Owned-asset utilization and selection discipline are unaccepted. A September 15 offline inventory found 3,603 third-party files (about 9.87 GiB) already inside project Content, while the largest packs are represented by only a small number of runtime selections. External owner-project and VaultCache copies add substantial duplicated storage, but deletion is unauthorized. Asset presence, a generated derivative or a component count has too often stood in for player-visible acceptance. [Solution catalog utilization](production/SOLUTION_CATALOG.md#owned-library-utilization-audit) records roles without becoming a second queue. | Needs controlled pipeline / lead | Execute ACT-00, then require owned/imported/referenced/visible/accepted status and role-based candidate comparisons for later actions. After accepted migration, audit dependencies and package size before proposing any deletion. |

## Hands-on acceptance cases

**19 open / 0 passed** at this update. All 19 previously unchecked cases remain here; none was accepted by this planning edit. They are acceptance scenarios related to the issues and actions above, not 19 additional features or a required single sitting.

Structured review and defect fixes are currently paused under the capture-only instruction above. When resumed, use the short review route and the relevant unresolved case. Controller cases can be done first. For each case record the actual build, date, device/settings, observation and result: not tried, partial, failed, needs retest or passed. Check the box only after the full case passes with owner/tester evidence. A defect report or automated fixture is useful evidence but not a pass.

Session date/time: __________
Build/receipt: __________
Resolution / quality / cap: __________
Device / connection / sensitivity / pitch direction: __________

<a id="pt-01"></a>
1. [ ] **Launch the recorded executable and open the home hangar.**\
   Expected: usable game window, visible Acornaut/ship and readable shell; no black view, missing assets or unwanted fullscreen switch.\
   Observation / screenshot / issue: ______________________________________

<a id="pt-02"></a>
2. [ ] **Set a comfortable mouse steering dial before judging flight.**\
   Open **Settings → Controls → Mouse sensitivity**. The dial is adjustable from 0.3–2.9 in 0.2 steps, with an upper clamp and wrap to 0.3. The lead verified a change from 1.0 to 1.2 and a later packaged relaunch displaying mouse 1.2/controller 1.0. Your preferred values and their feel still need checking. Record the actual displayed value above. Launch a run, make small horizontal/vertical corrections, and adjust again if too slow or too sharp.\
   Expected: a visible change in response and usable fine corrections. Sensitivity is a preference to tune, not a fixed value the tester must accept.\
   Observation / preferred value: _________________________________________

<a id="pt-03"></a>
3. [ ] **Check keyboard/mouse flight and chase camera.**\
   Mouse steers; W/S changes throttle; A/D and R/F move sideways/up/down. Try gentle weaving and a stronger turn.\
   Expected: responsive control with momentum/banking, ongoing forward movement, a fully framed ship and readable hazards without excessive camera swing.\
   Observation — loose, stiff, sluggish, twitchy or comfortable: ____________

<a id="pt-04"></a>
4. [ ] **Try boost, sustained brake and all dodge directions.**\
   Shift exhausts boost; release to recharge. Hold Space until overheating, then cool. Use Q with lateral/vertical direction, including one deliberate obstacle clip during a dodge.\
   Expected: useful boost, meaningful partial braking without permanent parking, obvious resource states, sharp directional dodge and damage on collision.\
   Observation: _________________________________________________________

<a id="pt-05"></a>
5. [ ] **Tune comfort/accessibility and return to flight.**\
   Test sensitivity, invert pitch, boost/brake hold versus toggle, camera shake, motion blur, subtitles, UI scale, Graphics and Audio.\
   Expected: ordinary menus pause, settings visibly apply, text stays inside panels, warnings remain understandable without color, and return does not leave stuck inputs.\
   Observation / preferred settings: ______________________________________

<a id="pt-06"></a>
6. [ ] **Feel damage, recovery, pickups and Rapid Laser combat.**\
   Observe shield/hull damage and recovery in danger versus clear space. Collect each reward shape; use manual aim/soft brackets against debris/enemies and try an obstructed shot.\
   Expected: shield does not refill automatically; hull can recover; damage/critical state is clear. Pickups justify route risk; laser/destruction/fragments are readable; assistance never fires automatically.\
   Observation — hit feel, aim, recovery, reward clarity: ___________________

<a id="pt-07"></a>
7. [ ] **Follow the first block and deliberately accept Salvage Cache.**\
   Approach before pressing E; complete a diversion when comfortable. On another attempt let an event fail.\
   Expected: approach alone does not commit; objectives/reward/failure are clear; event UI leaves the live ship controllable.\
   Observation: _________________________________________________________

<a id="pt-08"></a>
8. [ ] **Choose a depot stop and use its magnetic mooring.**\
   Approach voluntarily and interact; remain aboard while the service panel shows the lock. Inspect the upgrade subset/deal; with missing shield try the paid shield-only recharge (21 credits at defaults). Close the panel to release, and observe the 20-second service boundary.\
   Expected: no physical pad/on-foot scene, clear stop/release, no wave progress while moored, limited offers and no distracting follower after departure. Check that failed/stale purchases do not spend credits.\
   Observation: _________________________________________________________

<a id="pt-09"></a>
9. [ ] **Play Wave 5 and approach Station 1.**\
   Watch the wormhole emerge, counter the pull, survive hostile arrival, approach manually and enter landing assistance. If the run ends earlier, record death/retry notes in Step 14 and resume this route on another run.\
   Expected: continuous journey, noticeable climax, useful warnings, consistent controls and understandable/satisfying docking.\
   Observation — tension, fairness, visibility, docking: ____________________

<a id="pt-10"></a>
10. [ ] **Walk Station 1 and choose meaningful purchases.**\
    WASD/Shift/E walk/run/interact. Visit all five upgrade paths, repair, Mica, contracts, the story beacon and launch. Buy what you want; try the beacon reward twice.\
    Expected: coherent feet/camera/exit, easy service discovery, roughly 2–3 useful purchases, compact visit and once-only side reward. Pressure discloses reduced shield/added pressure; Hunter explains target/reward.\
    Observation / purchases / visit length: ________________________________

<a id="pt-11"></a>
11. [ ] **Save & Quit, relaunch, Continue and leave for Wave 6.**\
    First record ship/weapon, wave, credits, tiers, hull/shield, utility and contract. Compare after relaunch.\
    Expected: same station run/build, retained contract, Wave 6 departure and a consumed suspension that cannot act as a reusable checkpoint.\
    Before / after / discrepancy: _________________________________________

<a id="pt-12"></a>
12. [ ] **Play Waves 6–10, Distress and both utility choices across attempts.**\
    Compare Vector Thrusters with Overdrive Cooling and try Heavy Cannon when rewarded/unlocked. Observe electrical/gravity pressure with debris and both enemies.\
    Expected: stronger compositions without unreadable hits, deliberate rewards, distinct weapons/utilities and time to respond to warning direction/sound.\
    Observation — weapon/utility feel, enemy distinction, unfair moment: _____

<a id="pt-13"></a>
13. [ ] **Reach Wave 10's compound climax and Station 2.**\
    Look for simultaneous gravity, asteroids and enemies; inspect second-station services and contract resolution.\
    Expected: difficult but readable pressure and clean landing. Current slice behavior has no Wave 11; services/suspension remain and labelled abandonment gives no death XP. That boundary remains under review.\
    Observation — climax, reward and boundary friction: _____________________

<a id="pt-14"></a>
14. [ ] **Inspect ordinary death, resumed death, progression and another run.**\
    Review XP/score, unlock messages, history and loadout. Use Heavy Cannon and Swift after their early unlocks; compare Swift agility/durability.\
    Expected: one award, permanently ended run, no reloadable dead checkpoint, clear next milestone, retained account options and fresh run-specific power.\
    Observation — clarity and immediate desire to relaunch: _________________

<a id="pt-15"></a>
15. [ ] **Switch to a physical controller and calibrate its own dial.**\
    **Settings → Controls → Controller sensitivity** is separately adjustable from 0.3–2.9. Right stick steers, left stick moves laterally/vertically, D-pad up/down changes throttle.\
    Expected: comfortable fine control and a stable resting stick; mouse preference does not force the controller value.\
    Observation / preferred value / drift: _________________________________

<a id="pt-16"></a>
16. [ ] **Repeat controller actions and live menus.**\
    RT boost, LT brake, LB directional dodge, RB fire, A interact, Menu shell and B back. Test hold/toggle, live depot/reward choices and disconnect/reconnect.\
    Expected: keyboard/mouse capability parity, no lost steering, accidental selection/fire or stuck inputs.\
    Observation: _________________________________________________________

<a id="pt-17"></a>
17. [ ] **Complete the two-block station/save/death route on controller.**\
    Left stick walks, X runs, A interacts. Repeat services, events, contracts, utility/reward choices, both climaxes, Save & Quit/Continue and next-run selection across natural attempts.\
    Expected: no keyboard rescue; comfortable combat/walking and usable menus/terminals.\
    Observation / keyboard rescue needed: _________________________________

<a id="pt-18"></a>
18. [ ] **Listen and judge readability in the busiest scenes.**\
    Compare engine/weapon/impact/pickup cues, alarm frequency/direction, pressure music and station decompression. Check the hero/tail/feet while on foot, the closed Starter hull in flight, bloom, hazards, telegraphs and maximum UI scale.\
    Expected: essential sounds/cues remain distinct without constant alarms/chatter or a hidden route. Rejected provisional art still requires replacement regardless of functional readability.\
    Observation / wave or timestamp: ______________________________________

<a id="pt-19"></a>
19. [ ] **Record the decisive player verdict and next adjustment.**\
    After ordinary death and the available boundary, record whether another run is immediately appealing. Identify one biggest source of friction. Perceived smoothness is useful; measured FPS belongs in the separate performance record.\
    Immediate retry: __________  Why / why not: ____________________________\
    Biggest next adjustment: ______________________________________________\
    First unchecked step / next place to resume: ___________________________

## Updating and closing work

The lead maintains this file after material changes and owner feedback, and links the relevant IDs in every PR. Keep a stable ID until closure; update the existing item instead of creating a duplicate. Each new active task needs scope/WBS basis, an owner, next action and an observable closure condition. Do not add speculative purchases or Phase 2 features as current tasks.

On closure retain the item with **Closed**, date, revision/build and evidence; owner-experience items additionally require the owner's reported outcome. Failed or incomplete retests remain open with the next action. Superseded duplicates point to the surviving ID. Do not silently remove unfinished work or mark it done because a PR merged.

Closed/superseded work at this consolidation: no open acceptance case was closed. Earlier technical repairs and their exact test limits remain in [validation records](VALIDATION.md) and immutable `docs/validation/` receipts. Removed stale running commentary remains recoverable in Git history.

Other documents have distinct roles: [Project State](PROJECT_STATE.md) for build/storage status; [solution catalog](production/SOLUTION_CATALOG.md) for candidate resources; [work packages](production/WORK_PACKAGES.md) for needs/dependencies; [game scope](GAME_SCOPE.md) and [IMPLEMENT](../IMPLEMENT.md) for authority. None is a second active task list.
