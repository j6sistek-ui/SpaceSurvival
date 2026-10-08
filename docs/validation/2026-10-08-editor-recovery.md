# October8 authorized recovery and native readback

Owner permitted reopening Unreal. All nine files from the closure manifest were
preflighted against their hashes before restoring the private owner-preview map
and eight previously absent display assets. The previous map and Build39 DLL are
retained under `.agent/local/EditorReopen20261008T0004`. An independent review
rehashed both sources and destinations: nine of nine match.

| Evidence | SHA256 |
| --- | --- |
| Restore receipt | `72be2498cee1aead57b259e82c3a10c0980a19cae6c4b46825b79d1ad1c6ff37` |
| Current saved owner-preview map | `16818b1bb54d7ee6794501a2684bdf450760834d5f434af6c1a0c58423ef05a9` |
| Build47 log | `d9d055266a690b28a6bed6190ce79253ff93c2d0cdfc31db75d191a1e28049b8` |
| Current project DLL | `059831f7b2c1987afe90d521bb6c18676f8a40c8d79c2ceb07807b68766f9ebf` |
| Native recovery/adoption readback | `1bf8b2cd3db1adf8831808d5b980c2e9d39495e211c872c3e53c6465f1d7052c` |
| Four-actor NPC lighting probe | `394572cc05c6beb413e032520861680e416dfa9ae02947a530dbf6575b52afd6` |
| Reception Play capture manifest | `58288481eaa9ac0fcc27d4f40e4d372f6dde0467d0a4fff4b9ba897ed1439d5c` |

Build47 runs the existing Editor build target and ends `Result: Succeeded`, eight
actions in18.62seconds, including the project DLL link. It supersedes object-only
Build46. Existing nonpreferred-MSVC, Tripo Interchange dependency and deprecation
warnings remain; the project warning is the InstanceBodies use in the flight
automation source. This is not a warning-free automation or packaged build.

One offscreen editor reopened the exact restored owner-preview map. Its reflected
NPC refresh API and warp class are present. Eight restored paths resolve as five
textures, one material and two material instances. Read-only adoption checks
find six reception props/two staff poses and four information-board actors with
five private assets/brightness8. Their `saved:false` results describe helpers
that do not save; the recovered map itself is the normal saved map above.

The two reception NPCs automatically have visible head-attached40lm fills,
radius100cm/source12cm, channel2-only lights and preserved mesh channel0.
Specular/indirect/reflection/GI contributions are disabled. The sampled drone
and hologram remain excluded. The proposed editor-load activation defect was
not reproduced, so no additional lifecycle override was introduced.

Actual Play captures at1014x344 show the front and side of reception using the
current saved preview. The capture manifest verifies the real camera, map/save
preservation, unchanged rendering settings, stopped PIE and temporary-camera
cleanup. Head silhouettes and the roles/tablet/gesture activity can be seen;
cropped framing and a passing foreground NPC limit the visual evidence. This
does not verify palm/sole contact, all variants, room spill,60FPS or whole-room
quality. Independent review confirms readable check-in/greeting roles and no
obvious floating desk props in these views, but eye areas/suits remain dark and
the greeting staff's frontal face is not shown. Both PNG hashes match the manifest.

Retained limitations: Nwiro's optional capture-annotations omission failed
validation; the ordinary editor screenshot included icons, so Play captures
were used instead. BP_Blinds AccessedNone warnings accompany startup even when
the actual correct Play world is running; startup was checked, not blindly
retried. The GPU-crash root cause remains open (RPT-20261007-02).

T's restored hardware is still held/rejected pending the owner's P1-P5 choice.
No gameplay warp/travel, owner approval, cook or release is established.
Published0.1.22-alpha/build2048604/sourcee6c2a87 is unchanged.
Private receipts/photos remain local; the source PR stays open and unmerged.

## Native room-ad texture checkpoint,00:37UTC

All fifteen selected textures are imported and saved, five each for R, Market and
L, through the reviewed `StationAdCampaignSet` helper and explicit root verification
and saves. Native Texture2D dimensions match each selected manifest entry; import
ancestry and current source hashes match, sRGB/BC7/clamp settings pass, and the
compilation barrier finishes before saving. Each new destination was absent before
import. Only those fifteen new texture packages were saved. Map16818b1b remains
byte-identical and native dirty map/content lists are empty afterward.

| Room | Private destination beneath `/Game/OutpostSandbox/StationRefinement/` | Save receipt SHA256 |
| --- | --- | --- |
| R | `CustomizationCampaigns20261008A/Textures` | `41666a6ebd32f16d289141518ec1377a0416c7d5aed037bd7e1e0367793eb370` |
| Market | `MarketCampaigns20261008A/Textures` | `9e6ebeff48b1f43e3afdd0249606abf811b3961709e5c79abbed40be6845738e` |
| L | `LoungeCampaigns20261008A/Textures` | `17f644d3621e8e652c8a200a46c26053443dab615ab578e24a2811f99060f5bb` |

The three local `RootReopen47_*Save.json` receipts retain each saved asset's
identity, byte length and hash. R's separate `CustomizationVerify.json` records
native source/settings/dimensions; the other two combined receipts retain their
staging and verification rows. Reviewed source-manifest identities remain in the
[October7 source-art receipt](2026-10-07-room-ad-source-sets.md).

Independent read-only review verifies all fifteen saved byte lengths/hashes,
five unique expected targets per room without collisions, and all selected source
hashes/dimensions/ancestry against the native readbacks. The files total24,817,857
bytes. Fresh map16818b1b and DLL059831f7 hashes also match.

This supersedes the earlier source-only native-import limit. No material, actor or
screen assignment occurred. Physical aperture/ratio fit and all-five cycling are
still unverified. L's existing four-ad loop and8/10 room remain unchanged; T and
central were excluded. Existing Market vendor screens carry functional graphics
and have not been repurposed. Upright hardware and solid-wall mounting candidates
require current native inspection before placement. Source images remain intact.
