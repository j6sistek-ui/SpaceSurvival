# Operations display integration — 2026-10-06 owner session

Recorded at 2026-10-07T02:03Z; actual saved Art3 visual failures updated at 2026-10-07T08:36Z.
**PARTIAL: saved displays, supported density and graphite podium pass their
implementation/preservation checks; actual Art3 room remains about7/10 with mirrored/obstructed side art and T remains owner-unapproved.** This is a T Operations presentation
pass on the separate owner preview. The accepted L lounge, canonical runtime map,
published build and gameplay service behavior are not changed.

## Saved scope and identity

- Map: `/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006`.
- Input SHA256: `ab263462e6b4fe4150dcd4e30a42fbe5ab0f1e04204d73d1aa3eca2e33694d64`.
- Saved author2 SHA256: `d2ce5b1a100fd0ca684e5d81619a07551e0e9f3f07fc801015ec0a00d7904563`.
- Saved author3 SHA256: `d545cbeafcc346704bdeb9ff0c19fc6cd7f6fe0ce1a3e333151a2ee504ada8da`, superseding author2 as the current display-pass preview.
- Canonical Wayfarer remains `9c83968d9765467a05b104eaadc65dd44ff06dbfdbe797c8a38a58645756ca9c`.
- Lead-run author2 fixture and preservation checks pass; the lead independently
  observes native exit0. Capture2 also passes with an observed native exit0.

Three existing rear P4 Genesis panes receive Navigation, System Diagnostics and
Contract Status artwork. Their frames, transforms and collision remain intact.
The central P1 Goliath circuit panel retains both original material slots. A
64×24 cm Flight Upgrades insert mounts to that component with four small clips;
all five new decorative actors have collision disabled. No lights or unrelated
actors move. Four textures and four materials are saved exclusively under
`/Game/OutpostSandbox/StationRefinement/OperationsDisplays20261007`.

The baseline reads the current preview's service actors as `Information` actions.
These graphics introduce no purchases, contracts, navigation route, tier ownership
or live telemetry. The existing Flight Upgrades action/description and the other
service identities remain unchanged. A production gameplay transaction was not
tested by this presentation pass.

## Geometry and retained failures

| Evidence | Result and limit |
| --- | --- |
| OperationsBaseline1 | Native exit0, fixture fails before images because optional detailed screen geometry exceeded its export budget. No map/save change. |
| OperationsBaseline2 | Four actual SIE room images and native actor/material inventory pass; lead observes native exit0. Optional heavy screen detail is explicitly skipped rather than blocking the images. |
| OperationsDisplays1 | Native exit0; fixture fails before import/save. The central slot's projected surface occupies about69.5% of its138.367×40.269 cm bounding rectangle, below the rectangular-fit guard. No assets save; preservation passes. |
| OperationsScreenApertureProbe1 | Read-only fixture/source preservation pass. Lead observes exit `-1073741819` (`0xc0000005`) after normal LogExit. This is a mixed outcome, not a clean native pass. |
| OperationsDisplays2 | Author fixture/preservation pass;8 new assets and owner preview save; lead observes native exit0. |
| OperationsDisplaysCapture2 | Six actual saved-room SIE images pass;1,094 files,3 saves and ships unchanged; PIE stops. Lead observes native exit0. Actual rear images fail visual quality review because of blur and obstructing old hardware. |
| OperationsDisplays3 | Four resident texture/material copies and three complete rear frame/pane shifts save; author/preservation pass, lead observes native exit0. No new actors/lights. |
| OperationsDisplaysCapture3 | Six matched actual saved-room SIE images pass; files/saves/ships unchanged, PIE stops; lead observes native exit0. Independent review of all six confirms sharper rear art and unobstructed headings. Room composition remains unfinished. |
| OperationsPromptVisibility1 | Preflight fails on the already-hidden editor ArrowComponent, before mutations or save; preservation passes. Lead observes exit `-1073741819` after normal LogExit. Retained unchanged as failed/mixed history. |
| OperationsPromptVisibility2 | Exact TextRenderComponent guard repairs the ArrowComponent mistake; six labels retire and owner preview saves with preservation pass. Lead observes exit `-1073741819` after normal LogExit; no fatal error is reported. This is a mixed author/process result, pending fresh persisted-state capture. |

The focused probe establishes that the central surface is a detailed cutout
circuit panel, not an uninterrupted LCD. Its7,514 slot1 triangles have dominant
normals approximately±Y; tilt is not the cause of the missing coverage. The
selected front plane has2,132 triangles and large physical openings. The repair
does not relax the rectangular-fit threshold or map words across those holes.

The inserted display uses a separate2.667:1 layout without stretching. Each clip
has nine support samples on the actual retained native face. Their3.6 cm depth
bridges native localY−1.738 through insertY+1.1. Original collision and all existing
component transforms/materials/services are compared using stable numeric
snapshots; the attempt1 helper is retained unchanged in ignored history.

## Artwork and source preservation

The four compositions use the actual owned Phoenix reference and Havolk enemy
thumbnails, real-font typography and vector briefing diagrams. Navigation also
uses the retained NASA/Goddard Milky Way source with ESA/Gaia/DPAC attribution and
the CC0 Poly Haven Rock Face textures. These are CPU-authored compositions; this
pass makes no hosted/local image-generation call, purchase, download or install.
The lead approves the source designs for native evaluation, not final room quality.

The exact approved source images and recipes remain in ignored
`.agent/local/StationRefinement/OperationsGraphics1`. The original2:1 Flight
Upgrades draft is preserved alongside the compact insert revision. The manifests
retain dated source-code references for the copy; concurrently authorized C++
edits are not misrepresented as immutable art pixels or overwritten.

Author2 verifies1,082 protected asset entries representing1,071 unique packages,
six other map files and three save files unchanged. No existing source package
is overwritten. All four new material graphs report empty native compile-error
lists. The source helper, versioned wrapper and capture script parse successfully;
offline artwork-hash and clip-footprint checks pass. These checks do not establish
screen readability, collision traversal, controller behavior, frame rate or a
packaged gameplay pass.

## Immutable local receipts

All paths below are relative to `.agent/local/StationRefinement`; raw logs and
screenshots remain ignored/private rather than being committed as large evidence.

| Receipt/input | SHA256 |
| --- | --- |
| `StationOperationsBaseline2/manifest.json` | `02c279c096587a8c684f3d55e6285699cb60834198470dfc3b609ab97323d884` |
| `StationOperationsDisplays1.json` | `0eafc5dcccd9f499dfb18e02415525d5a9e72992d2a095540e89b8573968de85` |
| `StationOperationsScreenApertureProbe1.json` | `e742b71dfb2f0bba622a94ce1e2c38659598a16c518fde4bb1999b5cfd96f3f0` |
| `StationOperationsDisplays2.json` | `b87dcc8c063abad20bf90db3332feeae02a5810a22d2775af19f16e78a2769c2` |
| `StationOperationsDisplaysCapture2/manifest.json` | `fe779349936b6df9b990434e160d8e06fb303886b0d026b7897a329fd12a430d` |
| `OperationsGraphics1/preview_v2/manifest.json` | `314f57730a2e2c469aa831aa3ff2b276a91b86b9e0f60a301905a0bc152934cc` |
| `OperationsGraphics1/preview_services_v1/manifest.json` | `6529d0be0bcc22c738bf016c0b241e3cd4d5e757b749c983b1091018d6a89fae` |
| `OperationsGraphics1/preview_central_insert_v1/manifest.json` | `78548e050c51ec89213871cf78bee11b4339671a8b2bf254df31a7124b51e4d4` |
| `apply_operations_displays2.py` | `c9b6c443946b404ef4b29305cf36cbd781e2c90315f8c982c40d08069a08e3c3` |
| `capture_operations_displays2.py` | `10ad29eddce6cbe6b86d6533fe4fae98764f676810dd78f143a3563250abd8dc` |

The reusable [display helper](../../Scripts/RefineStationOperationsDisplays.py)
is frozen at SHA256 `4b637848710b0a16b075d2910e6a69c74674a62ea78bf834541692b7bd9abc0c`.
Capture2 contains six actual saved-room SIE views: entrance, central insert, all
three rear panels and reverse room. It checks saved materials, attachments,
files, saves and ships. Independent review of all six confirms correct graphic
orientation and a physically mounted, readable central insert. The three rear
images are visibly blurry despite crisp source pixels; the cause remains
UNCONFIRMED. Old suspended bars obscure the Diagnostics and Contracts artwork
and headings, while cables cross portions of the panels. These defects prevent
display acceptance. Lead assessment is approximately7/10 for the graphic content
and4–5/10 for the unfinished whole room, not an owner acceptance score.

The saved author3 correction uses four private resident texture/material copies
and shifts each complete rear frame/pane pair15 cm toward the room, followed by
matching images. Baseline bounds locate the obstructing hardware inside the
native SmartStorage wall modules, rather than separate disposable actors: wall
frontX9142.85 intersects prior paneX9150.86. The proposed paneX9135.86–9138.77
clears that hardware, while frame rearX9154.09 remains supported against the wall.
No wall, global texture-pool, light, source artwork or accepted L change occurs.
The four textures retain original pixels, compression, filters and mip settings;
only private copies set NeverStream. Their unchanged custom projection shaders
receive the resident copies. This addresses the suspected mip residency cause;
matched actual pixels establish the repair, rather than proving a general
streaming diagnosis. Resident budget is approximately10MiB including mip chains.
Capture3 confirms readable Navigation, Diagnostics and Contracts panels without
the former bars crossing their artwork. The central Flight Upgrades insert
retains its physical clips, original circuit-panel material and readable content.

Exact author3 evidence, all under `.agent/local/StationRefinement`:

| Local evidence | SHA256 |
| --- | --- |
| `StationOperationsDisplays3.json` | `a15161dc715b5f6d8fe7d6d37aac7a68df5aa15deb5ffa64152beb2191bd0641` |
| `StationOperationsDisplaysCapture3/manifest.json` | `408998767e5b403602abd1876663fe1819e5b42ea9a105f21ba03c6fa32e0ae5` |
| `apply_operations_displays3.py` | `5d497fb19efa4b43c0e245c1de0db0b09eefd5985a153418e7c2298cbef149cf` |
| `capture_operations_displays3.py` | `d31c72a59f32b03f795d4916ac920c986243f031ae978ba046623e7a7e89bf3a` |

[Readability helper](../../Scripts/RefineStationOperationsDisplayReadability.py)
SHA256 is `bd57a36e23b69afdf873006c35488f58315adb41a6056228fbd6132e1b335926`.
The earlier rejected Capture2 and author/probe failures remain intact.

## Owner-requested text cleanup — saved, fresh capture pending

The owner rejects boring floating text and unfriendly prompts. The new
[visibility helper2](../../Scripts/RefineStationOperationsPromptVisibility2.py)
applies exactly six reversible visibility edits: `Refine/Operations/Identity`
and the `Face` text actor belonging to Flight Upgrades, Ship & Parts, Pilot
Leaderboard, Contract Exchange and Trade Network. Actor IDs, source text,
transforms, font/material, collision and all five terminal identities/actions/
access/anchors remain. Fitted graphics and a single nearby contextual HUD action
replace redundant text in the presentation; preview Information actions continue
to say Read overview/information rather than implying a working purchase.

Attempt1 incorrectly required every PrimitiveComponent to be visible, including
the TextRenderActor's editor-only ArrowComponent. Its frozen helper/wrapper and
receipt remain unchanged. Attempt2 guards and hides only the exact measured
TextRenderComponent, preserves arrow visibility and accepts already-retired labels
as explicit no-ops. Actor visibility and text visibility are recorded separately;
no-op-only runs do not save. Exact actor/source/transform/service guards remain.

| Visibility evidence | SHA256 |
| --- | --- |
| Failed `StationOperationsPromptVisibility1.json` | `3cb3139e713f97868a386b76214e1d0287156096877312ce9ab20210f4ec2f4d` |
| Attempt1 helper, retained | `273c62922d522a175d97dab534eba30bb53a8db4b088c22b880c3e1a48c24f56` |
| Attempt1 wrapper, retained | `ed1df6ee9ad7ba56e56ff54c041099f7943edceb63bc336a3d03a3f942af0bcb` |
| `StationOperationsPromptVisibility2.json` | `2bffe3e5e670b545b006141d4c70eb1c8fe0755eb65855b161a66574174e4cb7` |
| Attempt2 helper | `b0fa94264e22a01cf61ce3a1e934a7352fa92245a0251bc3f96cb6e26a7bd241` |
| `apply_operations_prompt_visibility2.py` | `a877a29fdacd2c50657976facbc312881a441fba64cacdc5dfbe8d91e1d105af` |

The saved visibility2 preview is
`3e3f187c81de87f2fc14b2fc8f57d624ef82c6a2bbf1321eb0c764b9dad2c49f`,
superseding author3 for this narrow follow-up. The author fixture succeeds and
preservation passes, but the lead observes a post-shutdown native access violation.
A fresh capture must reload and verify the persisted flags and unchanged terminals;
saved-state visual acceptance is not inferred from the receipt. Python compilation
and scoped source checks pass. Contextual C++ HUD changes still await the lead's
Build32 and native regression/capture at this checkpoint. The substantial glass
Phoenix podium and finish/lighting are separate concurrent passes; this receipt
does not establish their saved state or full-room quality.

## Original Operations ads — local artwork ready, not imported

On October7 the owner asks for room-specific illustrated TVs. Two original
local Qwen-Image-2.1 Q4_K_M images now depict an orange maintenance robot holding
a cracked coolant manifold and an alien recovery pilot with a damaged courier.
Rimfix Field Service and Voidspan Recovery use distinct illustrated subjects,
authored layouts and actual installed-font typography. Copy is fictional scenery;
no repair/recovery transaction, economy or terminal mapping is added.

The root explicitly releases the GPU for exactly two prepared jobs. The installed
CLI incorrectly rejects an empty autogrow image input, although the live local
schema records minimum0. Its failed validation/tool attempt remains in the receipt.
An empty real queue is verified before direct loopback submission of the exact
frozen graphs/seeds; both jobs succeed. The owned Comfy PID42892 is stopped,
server_info reports running=false and the process is absent before Unreal resumes.
No model download/upgrade, host installation, cloud generation or extra job occurs.

Raw images are1024 square. CPU layouts preserve illustration aspect at2048×1152,
16:9, with text inside a5% safe border and headline fonts at least90px. Raw art and
final layouts receive visual review: the damaged part, robot expression, recovery
hook and courier are recognizable; materials and large typography are coherent.
Lead specialist rates artwork approximately8/10 against the supplied illustrative
ad standard, with simpler landscape copy. This is an artwork assessment only.
Native placement/readability and owner approval remain UNCONFIRMED.

Private evidence under `.agent/local/StationRefinement/OperationsAds1`:

| Artwork evidence | SHA256 |
| --- | --- |
| Frozen prepared `manifest.json` | `74caa16ec4f9f7e57c6f69497097ad1d5500b245d76e23100afc96a1ac4b86d0` |
| `generation_execution1.json` | `0df39cc720d0220fc7bb75d1dad54fb526f27f43f87f8d296584510dc874386f` |
| `final_manifest.json` | `8a5f4ecf04d7b83209125109447d3eabf6ab4309237aab14cc7137479a65dda3` |
| `final/01_Engineering_Landscape.png` | `b2990d94dbf77c004bd6fc01b73e06b15d7168cca3b87d27f5654a77e7aaf0ac` |
| `final/02_Recovery_Landscape.png` | `eb92b1024e34e1ece33079e89c94ae0d4fcdd80d463a4a6a5a19ef7d95f7fcce` |

Exact workflow graphs, model roles, seeds2026100711/2026100712, completed histories,
raw pixels, installed font hashes and text bounds are retained. Intended placement
is one/two supported entry-front side alcoves, clear of the four staffed desks,
rear functional briefings and Phoenix podium. Measured hardware fit and a fresh
actual saved-room view are required before rating the in-room ads.

## Supported canopy and original-ad follow-up — prepared October7

The entry-side density addition is limited to12 native canopy panels,3 shared
profiled roof rails,2 native storage cabinets and2 owned detailed TVs on native
profiled floor posts:21 new actors and4 private display assets. Existing lighting,
accepted L, four staffed pods,97 command/staff parts, service mappings and the
four ordinary capsule routes are protected. The two original ads above have no
gameplay action or transaction. Native import and full-room quality remain
UNCONFIRMED; source preparation is not a saved-room result.

The first read-only native support attempt fails because the cabinet top is not
flat enough for the proposed mount. Its receipt is
`StationOperationsDensityProbe1.json`, SHA256
`50a2c40d833280d37b4bb411c6f4da670e51632668a4a46b080e6395631ac1bf`.
Preservation passes and the lead observes native exit0; no mutation or save
occurs. The failed helper/wrapper remain unchanged. The second attempt changes
the physical mount to the real station floor behind the cabinets rather than
loosening the top-contact criterion. It records the unused uneven top heights,
checks nine rotated feet points for each post, and preserves roof-triangle,
source and route checks. Probe2 native outcome is pending at preparation.

The new author helper derives TV yaw47.3502/227.3502 from its actual oblique screen
face, matches its native mounting plate to the rotated post, and retains all
seven body material slots. Only the measured screen slot5 receives the new art.
The resident BC7 artwork uses true screen-plane projection,16:9 letterboxing and
display gain6, preserving illustration aspect and the established readable
display treatment. Actual native TV triangles check existing fixture clearance
before imports; roof rails contact the measured roof and attach to its component.
Neither helper saves any map or source asset; only the guarded lead transaction
may save the exact four new assets and owner preview.

Prepared source identities:

| Prepared helper or wrapper | SHA256 |
| --- | --- |
| `RefineStationOperationsDensity2.py` | `9313cd114aa27c59c3d9f7e2ca7be141b97c5ee9d4f2b8653599cc72b5be9dfb` |
| `probe_operations_density2.py` | `dc693c8f19cc496674aa575d06a7915c261b12f69554b8d571887c80f7a020f3` |
| `AuthorStationOperationsDensity.py` | `73b0c06e7558878c6601f0a9ca071dfc78d8a7f62fbabf93268192ad10065c58` |
| `apply_operations_density1.py` | `f2d67e621d40d44418bd7a8cb172ff0fb7ed5600a870ca5a0a5b9812a5b66644` |

Python parse/compile, CheckProject40, documentation navigation and diff hygiene
pass. The wrapper requires a successful preserved Probe2 and the exact latest
saved-scene receipt; podium4 may be saved between probe and author only when
the same source/roof/floor supports and routes still pass. Native saving, fresh
in-room visual comparison and ordinary walking remain required. Owner acceptance
and published build state remain unchanged.

## Subsequent diagnostic failures — no density author or save

Probe2 fails on a floor-hit dictionary key before roof validation. Arcade._floor
returns actor/point/normal, whereas the specialist incorrectly assumed the
Workroom decoder's label/component fields. Receipt SHA256
`339116166a91b76ded48064ff619f5caf9b6e594c4ce5c355be08d181b558b92`
records preservation PASS; the lead observes native exit0. This is a schema
failure, not a demonstrated physical-support failure. The original attempt is
retained unchanged. Probe3 uses the directly inspected Workroom decoder with the
same physical Ground/Operations and native Z checks, reaches roof validation and
rejects the actual raw roof contact outside the proposed band. Receipt SHA256
`27952dd22fdb53178a84f9f34dff6b0d495035c4996efce5e3e0444dbfd83aea`
records preservation PASS/native0. Neither probe imports, spawns or saves.

The canopy author is blocked pending a diagnostic-only native roof survey. New
RoofProbe4 records every clipped candidate, actual contact minimum/maximum and
source triangle, comparing raw source geometry with geometry using mesh build
settings and rendered native bounds. It preserves28 roof identities/poses/source
hashes and contains no canopy height decision or authoring. Its helper SHA256 is
`3cec67160f9f7357de0bf33fe84839bf4090c2c5c3b76bc0bc971788f6c7e6fb`;
wrapper SHA256 is
`93c7af0b2d5fa1226ea7d39b82fa5a5388677392cc5419680ce1272617d39992`.
Native outcome is pending. The source is StarterBundle SM_Ceiling_B; its unusual
native origin does not justify guessing the actual lower surface or lowering
the physical support guard. A clean fit must be established, or a separately
authorized reduced pass may deliver storage/ads first.

Corrected author2 and a six-shot fresh saved-room capture are prepared but
unexecuted; previous prepared author1 is retained. Source review is favorable,
but that does not establish native support, saved assets or visual quality.
All source/native failure history remains part of this validation record.

## Measured roof repair — 2026-10-07T03:56Z

RoofProbe4 now succeeds with preservation PASS and lead-observed native exit0.
Receipt SHA256 is
`231e8861c75d955a6f7ec250decbf050d0bc7981fdc629bca9d8c90f3e094454`.
Its28 native StarterBundle roof parts and their actual source triangles show a
stepped ceiling. Raw geometry and build-settings-applied geometry agree. At the
original Y−500 rail the actual lower trim is Z397.567688cm; at Y0 and+500 the
inner recess is Z430.520939cm. The prior upper425cm guard correctly rejects
those recesses. Native bounds alone cannot identify the contact surface.

The new, unexecuted author3 keeps that385..425cm guard and moves only proposed
canopy rows to Y−400/0/+400. Three10cm-deep shared rails span X7000..8600 at
Y−498/−98/+302, contacting the actual lower trim with12.567688cm of support.
One proposed panel at X7600/Y0 is omitted to preserve the existing pendant
stem at X7750/Y0/Z335..435. Its deliberate400×200cm opening prevents a fixture
intersection. Scope is therefore11 canopy panels,3 rails,2 fitted cabinets,
2 floor-mounted supports and2 original illustrated native TVs:20 new actors,
4 private assets and no new lights. The earlier12-panel/21-actor proposal remains
history, not a required count.

CPU checks reproduce the native roof triangles and verify the revised boxes
against all available baseline fixtures and the saved60-part Composition5 podium.
Source, artwork, plan and dependency hashes pass; CheckProject40, documentation
navigation, Python parsing and scoped diff hygiene pass. The cabin specialist's
independent bounded author/wrapper review passes; native execution remains pending.
Author3 requires successful RoofProbe4 and
the exact latest saved scene; it rechecks all actual roof geometry/transforms,
five floor points per cabinet, nine points per TV post, actual TV triangles and
four capsule routes before importing or spawning. Prepared author2, which requires
failed Probe3, must not run.

| New prepared identity | SHA256 |
| --- | --- |
| `OperationsDensityPlan2.json` | `154eaba007a83cfae2b409d10c4ef5f445794d8005c9de32136ba669715a4f97` |
| `AuthorStationOperationsDensity3.py` | `a54c00147be2f012ad079d5eb789f62f9bc7c08c0ee43805e5d04e3f32216f21` |
| `apply_operations_density3.py` | `df476b58ab5d5be22f21e104900c77bc872b0bb25f812a951bdde860efb25144` |
| `capture_operations_density2.py` | `9f582dde44da1ba56265d77b99698d4988840c04e6078c34a69ab6d96cfed00d` |

Capture2 is prepared for the saved density proof and latest successful scene:
matched entrance/reverse, two individual illustrated ads, supported ceiling and
podium-side room. It reloads all20 parts, both resident textures, seven original
TV body slots, physical attachments, all five service mappings and six retired
TextRender flags. No imported ad, saved density or in-room quality is claimed yet.
The separate saved Composition5 preview is
`bcadec049db0bf58c5a5a1c511ac3e7fce34f7e7ac1876a03b526e7146b83639`;
its Capture6 manifest is
`0af2c3670848fa499f5a256b027ac177147a0c49985d5fbc0d53b5bb17edb174`.
Those podium results do not establish density/ad acceptance. The owner-approved
L lounge, canonical map and published build remain unchanged.

## Density3 retained failure and native-surface revision4

Density3 exits0 but fails before any import, spawning or save. Its conservative
box check reports a canopy intersection with `Environment/Starfield`. Receipt
`StationOperationsDensity3.json` SHA256 is
`ea8c479f983172fa12998b9b30e7fad9f33ff2e4c7ab47a449d261b10da8b64e`;
saved-assets is empty, preservation passes and preview `bcadec049...` is unchanged.
The frozen author3, wrapper3 and receipt remain intact.

Source inspection establishes that AuthorOutpostSandbox creates this backdrop
from Engine BasicShapes Sphere, fitted to180000cm diameter, tagged OutpostRole:Sky,
with MI_OutpostStars parented to M_RegionSky. Its creation uses component
NoCollision and disables shadow casting. The operations baseline filters actors
by room proximity and therefore excludes this enclosing backdrop; the CPU
baseline-box check could not reproduce the false positive. Source intent is
distinct from actual native state: revision4 must read back its mesh, material,
parent, collision, shadows and bounds before any imports.

New author4 keeps all physical fixtures eligible. Every overlapping broadphase
box now receives an actual native fixture-triangle/box narrowphase, including all
ISM world instances. No actor label or collision flag exempts a surface. The TV
guard also checks actual fixture surfaces before applying its retained conservative
TV-triangle/fixture-box test, preventing the same sky AABB false positive there.
The engine sphere package and two owned sky materials receive explicit source
hash/preservation guards. All20 actors, four private assets, actual roof/floor
supports, protected services and capsule routes retain their previous scope.

Prepared, unexecuted helper4 SHA256 is
`9d54a9eb3070be0c3ba206141d50f645c8237999a0def2863aeaccf3e99c2496`;
wrapper4 SHA256 is
`6ad380b6e49d6f1c0d82aa3ceee0881a948d1f6598e84dea65479730f6f26753`.
Python parsing/compilation and all12 dependency hash checks pass. Independent
review and native author4 outcome remain pending. The wrapper accepts the exact
latest successful saved scene, including a later finish pass, while retaining
successful RoofProbe4 as the geometry proof. Density/ad pixels and owner approval
remain unverified.

## Saved density4 and combined review preparation — 2026-10-07T04:15Z

This supersedes the unexecuted author4 status above. Independent cabin-specialist
review passes, and the root observes native exit0 with author/preservation PASS.
`StationOperationsDensity4.json` SHA256 is
`22dfb8e6565a8c0cd4272ed94087c5083642883151ec072bad8158e02a3628e9`.
The saved preview is
`c1f62aed453362a1eacc20faeb6f9d589bae5e9f42f03053a28dd3e2c5f1371c`.
Exactly20 actors and four private texture/material assets save. Native sky readback
confirms the source sphere, material/parent, NoCollision, disabled shadow casting
and90000cm extents; its actual triangles remain eligible in fixture clearance.
All floor/roof contacts, service identities,97 command/staff parts, four capsule
routes, original sources/maps and save files pass preservation checks. No light
changes occur. Failed Density3 remains retained as history.

The latest author is bound to the successful separate MaterialFinish2 receipt,
SHA256 `eb61d1045b7bc91eaa37d09a2da171b7391eac46435d498573753f46afee7691`.
That pass saves ten private materials on52 slots across37 original podium/central
workstation actors; the original60-part podium geometry, glass, hologram, sequence
and lighting remain intact. These saves do not establish visual quality.

NEW combined Capture3 is prepared for eight actual saved-room views: entrance,
two natural command phases, podium side, reverse room, each original illustrated
ad and supported ceiling. It binds the latest successful scene plus saved density
proof, protects all ten finish assets and four density assets, reloads actual
native poses/material slots/attachments and verifies the five services and six
retired text labels. The earlier69.681-second original Capture6 loop proof remains
authenticated; this short capture observes native autoplay without repeating the
full loop or changing playback. Previous unexecuted Capture2 remains frozen.
Capture3 wrapper SHA256 is
`0e7dda620ec3cf62c0bbf9c5058e2e15e43fe1f84af33b28cf4e1faf921f3f63`.
Python parse/compile, dependency hashes and offline52-slot/37-component proof
reconstruction pass. Independent cabin-specialist source review also passes;
the root alone executes native capture. Fresh combined pixels and owner acceptance
remain pending; the original-art8/10
assessment is not an in-room rating.

## Combined saved Capture3 outcome — 2026-10-07T04:26Z

This supersedes the prepared Capture3 status above. The root observes native
exit0; receipt success,1151 protected files,three saves, ship poses and stopped
PIE checks pass. The map remains `c1f62aed...`. Manifest SHA256 is
`9a819592026749b1f1b8c3aaaf6687caf34ec3c7b6190bcb7a6fa49e9529d49e`.
All eight1600×900 actual saved-room images are inspected: entrance, two natural
command phases, podium side, reverse, both illustrated ads and supported ceiling.
Actual native readbacks retain20 density parts,60 original podium parts,37 finish
components, both eight-slot TV material lists, their physical attachments, two
resident2048×1152 textures, five services and six retired text labels. Short
natural autoplay passes; the unchanged original full-loop Capture6 proof remains
authenticated rather than being repeated.

Lead and specialist review rate the native illustrated ads about8/10. The robot,
damaged manifold, recovery pilot/hook and courier read clearly with distinctive
large typography. Whole T is6–6.5/10: ceiling depth and graphite base improve the
composition, but broad panels remain plain and the floor and native workstation
show severe speckled reflections and jagged highlights. These are visible defects
in the captured images; their contribution from high-resolution capture versus
ordinary runtime is UNCONFIRMED. A bounded normal-viewport diagnostic is prepared
separately before global quality/material decisions. The owner subsequently asks
for unsaved pure-white, metallic-silver and white-with-silver floor comparisons;
those are not saved or accepted by this Capture3 result. No canonical runtime,
packaged build, owner visual acceptance or performance acceptance is claimed.

## Ordinary active-camera diagnostic — 2026-10-07T04:49Z

NormalShot1 succeeds and the root observes native exit0. Its manifest SHA256 is
`ac2f08e3a82458153518f405d8c4f337bcaa2836a04402fbe119c19d51a859d7`;
wrapper SHA256 is
`42bef9c47364dcd402551ff5d3f5e11faf6989d63e2dee8f095e14836371a04d`.
Both screenshots are ordinary `Shot` captures of actual PIE,1014×344 pixels,
matching the measured game viewport. Each view explicitly selects its unsaved
CameraActor as the controller's view target, verifies the camera-manager
location/rotation/FOV, then waits159/284 ticks and six wall seconds. This differs
from Capture3's camera argument to the editor high-resolution API: nominal
warmup there did not establish that the camera was the active rendered view.

All1153 protected files, three saves and ship poses remain unchanged; PIE stops.
The saved map stays `c1f62aed...`. No resolution, anti-aliasing, Lumen, material,
lighting or scene overrides are applied. Native readbacks are resolution100%,
anti-aliasing method4, High2 GI/reflections/AA, TSR history100% and Lumen reflection
temporal accumulation enabled. These settings do not establish the final resolved
SceneView flags, owner-size texture pressure or performance.

Four retained LogBlueprintUserMessages warnings report that the diagnostic's
`r.DefaultFeature.AntiAliasing` getter is unregistered. Its returned0 is an
unavailable fallback, not disabled AA. Installed RendererSettings.h:863 uses
`r.AntiAliasingMethod`; installed SceneUtils.h:44–51 defines method4 as TSR, and
the current native readback is4. Future captures omit the obsolete getter; this
frozen receipt and its warnings remain intact. This is a successful preserved
diagnostic with warnings, not a clean automated gameplay-test pass.

The root and specialist inspect both images. Fragmented/chrome workstation and
floor highlights persist at this small viewport. High-resolution capture or
missing camera warmup therefore cannot be established as the whole cause.
The images are not an owner-full-resolution benchmark. A read-only native desk
probe is prepared to verify actual output/static-switch/function connectivity
and material-slot surface areas, alongside the five service standing/support
checks. The prior eight scalar/vector child edits are not repeated merely
because their write/readbacks passed. No global AA, texture pool or lighting
change is justified by this diagnostic alone.

## Superseding owner scope — 2026-10-07T04:49Z

The owner selects textured, low-gloss white floors throughout the station;
rust is rejected. This supersedes the pending floor selection above. Same-angle
floor comparison pixels and the subsequent private full-station application are
separate work: neither is a saved result of Density4 or NormalShot1. Existing
panel normal/AO/detail, geometry, collision and lighting must remain intact.

T stays the presentation priority until the lead's actual visual assessment
reaches9/10. The owner requests clearer real upgrade desks/layout with a pulsing
standing ring at each existing service. The next combined read-only probe checks
five standing positions, native floor/capsule support, unchanged terminal
identities and the actual controller's FocusedTerminal selection. Native CanUse
is not exported as a UFUNCTION; invoking Use would trigger an action and is not
part of this probe. Presentation work must preserve IDs, DisplayName mappings,
access/anchors and service actions; the decorative Trade Network is not silently
turned into a new economy. No new purchase, teleport or progression mechanic is
introduced by the requested rings. Later room/cabin refinements remain held
except the explicitly authorized full-station floor pass.

## Retained service-probe failures and reflected API repair — 2026-10-07T05:31Z

The combined read-only survey has not yet established any complete material,
floor-inventory, NPC, aperture or standing-selection section. All three failed
attempts remain immutable, and the root observes native exit0 for each:

| Attempt | Exact failure and preservation | Receipt SHA256 |
| --- | --- | --- |
| ServicesProbe1 | Pre-map preflight rejects unreflected Controller.get_pawn. All1146 protected files/three saves remain unchanged, PIE is stopped; editor-scene/aggregate preservation are unset because no station map was loaded. | `75ca773ae96605ba5284b36a0d3ec2f7ede6b9c73d36e0b736b8bb40667c7d3d` |
| ServicesProbe2 | Graph2 stops at its native source-area count guard before a completed collector section. Empty-versus-over-budget source count was not recorded. All1148 files/three saves and loaded editor scene remain unchanged; preservation passes. | `42c0600aef1ed5897806cb45c9011931c0168650aff09c6556fef14c41ab07cf` |
| ServicesProbe3 | The literal Python bulk material-ID method is unavailable. Installed C++ header identity does not prove generated Python acronym spelling. All1150 files/three saves and editor scene remain unchanged; preservation passes. | `b1b47ab0dcc1072f9470391e8f6e5de5d3aec53951212032737f3bada67f8d90` |

Installed Controller.h scripts K2_GetPawn as GetControlledPawn; the repaired
probe uses the already proven GameplayStatics.get_player_pawn. NEW graph4,
floor collector2 and wrapper4 resolve exactly one registered callable whose
underscore-free name matches GetAllTriangleMaterialIDs, record its actual
exported name/doc, and preflight graph/list/standing APIs in Entry before map
loading. No guessed alternate or per-triangle fallback is called.

Graph4 retains the strict200k slot-area processing limit. Empty or denser native
sources report exact counts with slot areas unmeasured; material connectivity
is separate evidence. Optional screen-lens export likewise retains200k source
and20k glass limits and leaves the aperture UNKNOWN without a bounds-fit
substitute. All five terminal identities/actions, native floor/capsule support
and ordinary FocusedTerminal selection gates remain unchanged. The survey now
collects the full-station floor inventory first so a later diagnostic failure
does not discard that completed section. AST/source/hash and independent
reviews pass; final native collector/support results remain pending.

New prepared graph4 SHA256 is
`ae058616804ad051480284b0d94a91195a8870700d4625f6d0e1bbb1d5dc1fef`;
floor collector2 is
`5f33d4ddd8823e10a9f2bb00158f4250e103f2de9fed0e15f50e621ad22af148`;
final floor-first wrapper4 is
`f5feb090de3a5af92a5817b1c443536ba84a758d4212de58e63f6f720ea55ad4`.
No service graphics, rings, NPC replacement or desk finish saves result from
these preparations. Earlier recipes and partial/failed evidence remain intact.

## Unsaved selected-white floor evidence — 2026-10-07T05:31Z

The earlier multi-option floor capture was terminated before a manifest or
images; it does not establish a floor result. The subsequent White1 fixture
succeeds and the root observes native exit0. Its manifest SHA256 is
`40341b218ea8909387727a0872a63a68a28b91eae26293664de4e656f2d7f5c4`.
It records four1600×900 images, an unsaved replacement on exactly84 T floor
actors/420 slots,25 private inheritance-preserving MIC copies and a private
master clone. Only BaseColor/Metallic/Roughness outputs change; all377 original
nodes and native Normal/AO state are retained. Original references are restored,
candidate package files are absent, and all1170 protected files/three saves,
editor scene and ship poses remain unchanged; PIE stops.

The matched podium-side pair is inspected independently: the selected white
surface retains visible panel/seam detail and removes the rusty color. The root
rejects the entrance control as misframed despite scripted camera checks; that
pair is not accepted as a matched visual comparison. The slowly rotating Phoenix
remains natural, so its orientation differs between shots. These are explicitly
a current saved control and an UNSAVED material test, not a current white-floor
saved build or full-station application. Root acceptance of the white-side
material test does not establish room9/10, owner visual acceptance, performance,
a published build or complete station floor coverage. Current saved preview
remains `c1f62aed...`; station-wide floor authoring awaits the actual inventory.

## Completed floor subsection and isolated service follow-up — 2026-10-07T05:49Z

ServicesProbe4 supersedes the pending survey status above. The root observes
native exit0; aggregate success remains false because the later graph collector
cannot read StaticBoolParameter.dynamic_branch. All1277 protected files, three
saves and the loaded editor scene remain unchanged; preservation passes and PIE
is stopped. Receipt SHA256 is
`38ba0dca69bd5d17709fe6fb923f1843e4c0771cfb789a20e4c931287e41383d`.
The completed station_floor_inventory subsection succeeds read-only with2029
candidate components, actual source geometry/material lineage and unchanged
scene. It is valid partial floor evidence, not a successful combined service
probe. The actual registered bulk method is get_all_triangle_material_i_ds;
its documented three-value result is used by the completed collector.

No completed NPC, lens, remaining-desks or standing-selection sections result
from ServicesProbe4. NEW graph5 preflights every required property against its
actual class default object before map loading. Installed StaticBoolParameter.h
contains DynamicBranch as a bare UPROPERTY without editable flags; header
presence does not prove get_editor_property access. The exact unavailable
optional property is now recorded as UNKNOWN, never invented false. Unexpected
read errors still fail. Required connectivity, source hashes and strict area
budgets remain; graph5 is source-reviewed, not a native graph result.
Graph5 SHA256 is
`34894d608eef55dc0300cccbe88693cb3bd9f9ef8625d3b94382b8ae40a535dd`.
The new service wrapper retains independent collector failures and runs the
optional graph after PIE stops, so it cannot suppress unrelated NPC, lens or
five-position native standing evidence. It reuses Floor4 instead of repeating
the full survey. No service/standing marker or NPC content saves yet.

The separate main-floor author is independently source-reviewed for1022 unique
measured components and5017 explicit material slots,44 source leaves,49 private
inherited MICs and four private master clones. Original hierarchy/local
overrides, Normal/AO/UV and glass-slot exclusions remain. Only private direct
BaseColor/Metallic/Roughness outputs change to the selected low-gloss white.
Actual save and fresh game-view pixels remain pending at this checkpoint.
This bounded main-map pass excludes mixed owner-deck slabs/ring and streamed
child interiors; it must not be called complete full-station coverage.

The owner-ring omission is traced to the private collision-preserving mesh
SM_OwnerRing_AccurateCollision, whose name no longer matches the floor
collector's Arco_Tubo condition. Three private owner-deck slabs also mix floor,
sides and underside in one material slot; upward triangle winding alone does
not identify their true walkable tops. A narrow read-only ring inventory is
prepared rather than applying a whole-slot white override to these structures.
Earlier failures remain immutable. No canonical map, packaged build or T9/10
acceptance follows from these preparations.

## Saved main floors and retained mixed capture — 2026-10-07T05:58Z

This supersedes the pending main-floor save above. Main1 succeeds with
preservation PASS and root-observed native exit0. Receipt SHA256 is
`71bf0fb1f31e2673adb2bdd7b2c2ff28f27f727dbfacf8ccd31081ca5a84f1c2`;
the saved owner preview is
`211c812516fd81a71be64c6ddd3a372b3a2a94187f56790c03bc60719a077f34`.
Exactly53 private materials save, and5017 slots on1022 measured components
receive the selected white finish. Root verifies1281 protected files and three
saves unchanged. Independent CPU review matches all53 saved package hashes,
the current map identity and exact slot/component counts. Zero new actors or
lights are recorded. Mixed owner foundation and streamed child floors remain
excluded; full_station_complete stays false.

MainCapture1 produces14 actual1600×900 room/route images, but is not a clean
capture pass. The root observes native exit-1073741819 after shutdown; the
manifest reports success=false and editor_scene_unchanged=false with no
recorded Python errors. All1337 protected files, three saves and ship poses
remain unchanged, and PIE stops. Manifest SHA256 is
`74e428958579ef2780b7465c845a10fd57e3542f1944e8e51568fd36ca93a7b8`.
The separate on-disk saved-floor author remains valid; this capture's editor
state difference and native crash remain explicit failures requiring diagnosis.

The specialist views both T entrance and podium-side images. White panel
seams/normal detail remain visible and the rusty floor color is removed. The
workstations still show fragmented glossy highlights; image softness/jagged
edges remain. These visual observations neither establish the cause nor
justify global AA/resolution/lighting changes. The root and cabin specialist
continue a bounded actual-render-view diagnostic. No room9/10, complete
full-station coverage, physical-input, performance or published-build acceptance
is inferred from the14 files or material-source checks.

## Partial native services and material connectivity — 2026-10-07T06:36Z

Services5 is an aggregate failure with a root-observed native access violation
after shutdown. Receipt SHA256 is
`b84699a20232f73c3af6de762cb62a94fc0ea76a82ccf40051aac6e6711dce59`.
All1364 guarded files, three saves, editor scene, ships and services remain
unchanged, and PIE stops. Independent NPC, lens inventory, five standing samples
and graph sections finish; only the remaining28-part collector rejects an
immutable Engine texture namespace. These completed sections are partial
evidence, not a clean combined/native gameplay pass.

All five initial standing placements settle normally on Ground/Operations with
feetZ2.150cm and select the expected native terminal. Full3D distances are64.204cm
for Flight Upgrades and47.85cm for the other four, within the280cm integrated
limit. Strict floor/capsule support passes. No Use, transaction, ring authoring,
physical-input traversal or NPC replacement occurs. Compatible human/robot rigs
are measured separately; actual seating, skin/hand contact and pixels remain
required before installation.

Graph5 proves that the central eight parameter changes reach active native
base outputs; an inactive-setter defect is not established. The actual covering
switches are false. Metallic is texture×intensity; roughness is the native
texture interpolated between minimum/maximum. Central90,296 source triangles
are measured, while each5,022,252-triangle side base retains UNMEASURED slot
areas under the strict200k export budget. Native Normal/UV and the original null
AO output remain. No global rendering or new desk material change follows from
this connectivity diagnosis alone.

The four side lenses use a318,328-triangle/159,110-vertex source. Services5
explicitly reports OUTSIDE_STRICT_GEOMETRY_BUDGET and physical_mount_fitted=false.
A new slot-only extraction preflight fails before map loading on its empty
native return identity contract. Focused1 receipt SHA256 is
`8c9a4b66a68c919e9dc8af0da50d9d0f318ee45682de935144e535de9def6a57`;
the root observes native exit0. Disk files/saves remain equal and PIE is stopped,
but editor_scene_unchanged is unset and aggregate preservation is false. The
frozen failure remains. A separate Entry-only return survey and independent
remaining-parts wrapper are peer-reviewed, unrun preparations; optional lens
reflection must not block the useful material inventory. No aperture is fitted.

## Five illustrated service identities — offline, 2026-10-07T06:36Z

Exactly five authorized local Qwen jobs produce Phoenix systems, paired engines,
an original pilot insignia, Havolk mission art and cargo-route imagery. All five
downloaded PNGs embed the exact frozen workflow inputs, seeds2026100751–55 and28
steps. Four original/prepared references and raw outputs remain byte-identical.
Fresh visual comparison retains recognizable owned silhouettes and lists the
illustrative additions; these images are not native mesh renders. No fabricated
price, score or transaction is included. Initial model-path/schema/loopback and
pilot-validator failures are retained, with no model installation or upgrade.

Actual installed fonts compose the unchanged service titles and short subtitles,
with6% horizontal safe borders. Central illustration pixels remain identical;
there is no crop or silhouette warp. The root approves the offline direction at
about8/10. Artwork quality, physical screen fit, saved-room readability and owner
acceptance remain separate; all five plates are unimported and retain their
generated aspect ratios until measured native fitting.

Private evidence under OperationsServiceIdentity1:

| Evidence | SHA256 |
| --- | --- |
| Frozen prepared manifest | `106090a709f0d252ae1245e6d9935761094620485af0e6f7d04d302c1db1d38c` |
| Generation/reference review results2 | `85aba88a93254c0aba986c96238a33b20c049cb471ced40cf735b575569261b9` |
| Font plates1 manifest | `deda7b225d2e812d18846b5329af13bb9e7552980b3674a21e83de52bc65dcf4` |

The owned Comfy PID24164 is stopped and absent. A fresh06:30Z server_info confirms
running=false/background=null before further native work. Old CLI job files
without watchers retain stale queued statuses and are not current queue or
completion evidence. No further GPU jobs, scene writes or native imports occur.

## Actual hardware measurement and opaque save — 2026-10-07T07:43Z

RemainingLens3 succeeds with root-collected native exit0 and strict read-only
preservation. Receipt SHA256 is
`613efbd036ed579ab72158a7e5d8f7f7377c62d636e994ad0dec4da5810152e8`.
It measures the28 remaining primary hardware actors/34 current material slots.
Native slot4 extraction succeeds within the unchanged20k selected-slot budget,
but its1112 triangles form only a108.95×2.24×6.55cm light strip. This is not a
useful LCD aperture. ScreenFace4 also succeeds as a read-only measurement/native0
(`f022cf0aebf83521f816233a29767c11b57f0dafe9a66e0ee122b4d2607ef1d7`),
while actual slot3 has135426 triangles and remains
OUTSIDE_STRICT_SELECTED_SLOT_BUDGET. No dense arrays or fitted-image claim follow.
The original whole-mesh/focused preflight failures remain above.

The root saves Opaque2 with native exit0:57 existing hardware actors receive145
opaque-slot replacements through58 private ancestry/master packages. Native
texture variation, UV, Normal, AO and emissive outputs remain; glass/LCD/control
slots, geometry, collision, services and lighting are unchanged. The private
graphite-paint/satin-titanium treatment modifies active BaseColor/Metallic/
Roughness outputs rather than repeating the earlier eight parameter edits.
Receipt SHA256 is
`7368247a5ebfbe77842a2cd0777eeb6ac236c5230729c8521327032f1ef70123`;
current saved preview SHA256 is
`f8b49d938fa53f93e5fb5ca666108185bcd41419682257003cdec8c851afbd89`.
Original sources, successful Floor6 private materials/maps and all three saves
are preserved. This is a saved implementation pass; new finish pixels are
unreviewed and there is no T9/10 or owner-acceptance claim.

A peer-reviewed five-display artwork helper is prepared, unrun: count-first
measurement of the actual separate Part3 LCD/glass mesh must establish a useful
planar surface under20k triangles/40k vertices before any import. No housing
bounds substitute is allowed. The four square plates retain their aspect;
the Flight illustration has a deterministic2048×768 layout for the existing
supported64×24cm insert, preserving the original Phoenix pixels. Ten private
assets/five existing material slots are the proposed scope; no new actor, lamp,
service or hardware. Native shader compilation, fit, orientation and readability
remain distinct pending gates. The earlier fullsize ordinary image at actual
1600×900 was rated6.5–7/10 before this opaque save; it does not rate the new finish.

## Preserved display-fit and capture failures — 2026-10-07T08:05Z

Art1 is now a native exit0 failure before imports/saves, superseding its prepared
status above. Receipt `4d996c293e710a6980925de04f7a5a3067579511933d982a67eaeb767ab7e15e`
preserves the current Opaque2 map/private assets and saves. The actual Part3
source has7668 triangles/3836 vertices, within the unchanged20k/40k bounds.
The assumed coordinate-axis projection selected a narrow bevel; it did not
establish a useful LCD. All original Art1 inputs remain immutable.

Art2 also fails before imports/saves with root-collected native exit0 and
preservation PASS, receipt
`00a6044c4a6898332301e2a5eddc0c4f84ea75e6a9b28a247921269863a2d81f`.
It records complete bounded native geometry before fitting, then measures the
dominant actual triangle plane and per-display upright viewer basis. The
proposed image-square edge samples cross real surface cutouts, so the strict
121-point support guard rejects them. No image is imported and the private
artwork namespace remains empty. Art3 preparation uses those retained triangles
offline to find a supported inner rectangle; no wider budget or repeated
inventory is authorized by this repair. Actual shader/orientation/readability
remain pending.

FinishCapture1 fails before map load/images/editor snapshot on an unclassified
exact EngineResources/Black.uasset dependency. The root collects an access-
violation shutdown exit; there is no clean native capture or aggregate editor
preservation pass. Its launch-error SHA256 is
`0902c233438f62d2bee82029353c018ed8f076da5c0a37d55b4e10d9dbee16d1`.
NEW Capture2 source audit
`a7bd73be6a6aceaef3405eab1cb9ef5e1240070ae0189c26df18ce028878b640`
independently classifies and verifies all1602 current/prospective protected
paths: six exact Engine dependencies, four exact owner art references, two
fonts and seven verified content junctions. It grants no blanket Engine or
external-folder exception. Wrapper
`e613060a0682f3a36d7a203952699f133f2f7a118eeeb761df0b49bc4ab8a593`
retains the six actual-PC views and exact same-loaded typed scene guards.
Only the successful Opaque2 branch is currently eligible; native images remain
pending. This source/audit pass does not rate the new room finish.

## Saved opaque finish pixels and supported inner rectangles — 2026-10-07T08:19Z

FinishCapture2 supersedes the pending capture status above. The root collects
native exit0 and success: six actual-PC1600×900 views, all1573 protected files,
three saves, ship poses and the exact same-loaded editor scene remain unchanged.
The persisted delta artifact has count0 and PIE stops. Manifest SHA256 is
`c709af07f2b33adc0e830c423858b57bcb52d71ba1c54a1634383bf997150587`;
the saved map remains Opaque2 `f8b49d938...`. These are current saved-preview
images with temporary cameras; all four original alien operators remain, the
new mixed crew is uninstalled, physical rings are unfinished and the new five
service illustrations remain unimported.

The root inspects all six images and rates the room about7/10. Graphite/satin
side hardware and the clean podium improve the presentation. The under-ceiling
area remains dark relative to the selected white floor. The specialist checks
the actual Flight and Pilot close-ups: competing native diagrams are visible
through the translucent central insert, while the side screen shows a busy
generic native visualization. T has not reached the lead9/10 gate; the floor
choice, room lighting and published build are not changed by this assessment.

NEW Art3 is prepared against that exact saved Opaque2 producer, not a future
floor save. Immutable Art2's complete7668-triangle/3836-vertex source is reused
without another native inventory/export. Exact source bytes, plane/face IDs,
four native placements and original material slots are revalidated before
imports. Three supported square image regions measure50.55cm and the fourth
51.40cm. Full illustration aspect is preserved with letterboxing. In addition
to121 actual triangle samples, a continuous projected-triangle union check
covers every vertex/edge-intersection/rectangle-crossing interval. An offline
0.001cm slit test passes the sparse samples but is correctly rejected by this
continuous guard. Strict20k/40k limits remain unchanged.

The retained inner-fit plan is
`dc3ed7a1103219d483d225df1460462241f8633563dbb46d0ce0c5de3812bfcd`.
The author source/receipt gate verifies1617 protected files using the actual
producer schemas. This is a CPU check, not native import or save evidence.
Area-summation diagnostics differ at machine precision between Python runtimes;
both records remain, while exact physical plane/face identities and independent
strict support predicates remain mandatory. No generic scene tolerance is added.

The central existing64×24cm mount receives only a private artwork material copy:
opaque instead of translucent, gain1.5 instead of6, unchanged UV/custom code and
all other native graph connections/defaults. The original source stays intact.
Art3 remains exactly ten proposed private assets/five existing slots, zero new
actors/lights/services. Native shader compilation, actual rendered orientation,
readability, save preservation and whole-room quality remain separate pending
gates. Failed Art1/2 and FinishCapture1 inputs/receipts are preserved.

## Art3 saved author and failed shutdown — 2026-10-07T08:27Z

This supersedes the prepared Art3 status above. Root and independent source
reviews pass, followed by a saved author receipt with success/preservation true,
exactly ten private assets/five existing slots and no Python errors. Receipt
SHA256 is
`5eac150f83215f6ac3a97f741b77537bd5623f5b11282874f70e0358331c7121`;
the saved preview is
`eeffd79b164aa1d868f9f4935b6b9e8be272734a9a2bdca98f5964d1bf7ae54b`.
All1617 protected files, original sources, Floor6 child maps/materials, private
Opaque2 finish assets and three saves remain unchanged. Independent CPU
readback verifies every saved asset hash and the exact five-slot count.

Actual UE support readbacks pass121 samples and continuous coverage for all
four inner rectangles. Four side shader compile-error arrays are empty; the
central private graph and compilation pass their exact output/default checks.
Only that private Flight material becomes opaque/gain1.5, with the original
translucent/gain6 source and UV/custom code retained. No mesh, actor, collision,
light, service/action, floor or NPC change occurs.

The root collects native exit-1073741819 after normal subsystem/log shutdown.
This is a saved author verification with a failed native-process outcome, not
a clean aggregate PASS. NEW Capture3 reloads the actual Art3 producer and its
assets for six same-angle actual-PC images. Wrapper
`be341a3085e94ccf8475a90e6b7bc5b30d09eb94dd48162d78987c0a46a75f21`
and classifier audit
`91636e8c86087bec13a24835368f50f0c2966dbd897e89681826b079ed27b441`
pass independent source review/full1620-path classification and digest checks.
Fresh orientation, readable whole illustrations, competing-underlay removal
and whole-room quality remain pending; the previous about7/10 rating applies
to Opaque2 before this artwork save. No T9/10, owner approval or publication
is inferred from the save or source review.

## Saved Art3 actual visual review — 2026-10-07T08:36Z

Capture3 reloads Art3 and delivers all six actual1600×900 images. Manifest
SHA256 is `f54f5fabbbda731198b6db50a87090c5555b5fd40abcd77600a2e85b63cc707e`;
files/saves/ships and exact same-loaded editor state are unchanged, with zero
scene deltas. Root again collects nativeA5 after shutdown. The preserved
rendered/readback evidence is distinct from the failed native-process exit.

Root and independent reviewers inspect all six images. Flight's opaque insert
removes the competing underlay and its title reads, but the Phoenix illustration
is dim. Pilot close view06 clearly mirrors the title horizontally; top/bottom
hardware rails obscure the square composition. A vertical inversion is not
proved. The source plate is upright. The measured projection used
`cross(up,normalTowardViewer)`, which is opposite UE camera-right: the actual
north-facing close camera has world-right−X while that shader's basis points+X.
Continuous LCD triangle support did not establish visibility through the frame.
Whole T remains about7/10, not the lead9/10 gate or owner acceptance.

NEW Art4 is preparing correct viewer handedness and a complete illustration-led
4:1 strip inside the clear upper window, reusing the retained native LCD data.
Each complete source hero is uniformly scaled, with the existing service name
and subtitle beside it; no crop, silhouette warp, fake stats or new service.
Native whole-frame BVH footprint checks are bounded author preflight, not a new
inventory or raised export budget. Original Art3 packages and the white floors
remain protected. Private display gain may increase from1.5 to3.5; actual
brightness/readability and frame clearance still require new saved pixels.

Current saved producer is the unrelated one-threshold floor repair2, receipt
`67bf51f6ce0629c6d719c7b9b0bb42039ed07be8ea91919ff50c8c7fd2a8b0a2`,
preview `fb3d5ed7ee58afc3e90044cec21a4428022a7224f9d7b1fa71e0d65bab3ff3b2`.
It retains every Art3 package. Future Art4 must bind that actual producer rather
than mutate the stale Art3 map hash. Four original alien operators remain in the
saved scene; mixed-crew previews and physical standing rings are unfinished.

## Open / Check / Still open

- **Open:** the separate owner preview at the saved Threshold2 hash above; this is not a
  canonical-game or itch update.
- **Check:** repair mirrored/rail-obscured illustration mapping, then review
  actually fitted service graphics, saved private desk finish and standing-ring pixels
  alongside the saved white-floor coverage before judging the revised T room.
- **Still open:** T room visual acceptance, noisy workstation/rendered highlights,
  broad-panel detail, clear service desks/rings, fitted illustration capture and
  the remaining full-station white-floor coverage.
  Pre-finish T was6.5–7/10; current saved opaque finish is about7/10 against the lead9/10 goal. The owner accepted L8/10 for now;
  this display pass does not extend that acceptance to T. RPT-20261006-04 in
  [KNOWN_ISSUES](../KNOWN_ISSUES.md) remains the authoritative owner-acceptance log.
