# Room ad source sets — October 7

This records prepared artwork for R customization, the market and L lounge, not an Unreal
installation or a new gameplay service. T display selection remains held. Central
retains its separate one-or-two-ad exception and useful information priority.

## Customization: five distinct campaigns

Private folder: `.agent/local/StationRefinement/CustomizationCampaigns20261007`.
Its `README.md` links every image and the two exact generation prompts.

| Campaign | Source | Image SHA256 |
| --- | --- | --- |
| Morph Clinic | Owner original, unchanged | `52047c0f59154dbf6f472abb4becb05cc18822933d5eb72948f1d8922335893a` |
| Hologram Doctor | Owner original, unchanged | `4d14844a826017e6540c24db419a456add0fdcb32a3841fdd42b862196dd0195` |
| Zero-G Massage | Owner original, unchanged | `53bfbc7d0547cae56aa572246b8d38cf0c78f7cd156990a275ece6da6f1808fe` |
| Vacuum Valet | New builtin `image_gen` illustration | `37a1ac79e8cc7fb645cee8e13c432ecd07d5d9ce6dfa670cb5c6a9354b55cf56` |
| First Contact Photo Co. | New builtin `image_gen` illustration | `414ee8a9cc530c83b4ff5fd6a85ff36a6ab0831346509f6f7c7bbd00d81ce80c` |

`manifest5.json` SHA256
`0e1c3914f878d70b710ae06c0f3ef8ac08aab01ddf6ebd070f061a81cec5a4b7`
records source paths, image dimensions, exact prompt hashes and separate review
flags. All five local images and original/generated source files match their
hashes and dimensions. Supplied originals are853×1280; the two new images
are1024×1536. Neither new image modifies or replaces an original.

Root and independent visual review pass both new images for complete correct
text, distinct illustrated stories and the owner's cream/purple/teal cosmic
style. Vacuum Valet's grip is not clearly the prompt's laundry tongs, but the
suit-cleaning story is clear. First Contact Photo shows an actual portrait
session. These are source-art findings only, not owner approval or screen fit.

## Market: five distinct campaigns

Private folder: `.agent/local/StationRefinement/MarketCampaigns20261007`.
Its README links selected images and all four generation/two repair prompts.

| Campaign | Selected source | Image SHA256 |
| --- | --- | --- |
| Cosmic Tacos | Owner original, unchanged | `ab3d501532a723ee9e7736d02fda719820f2eb5af332ba92c2b383fce2e5636d` |
| Moonjar Pantry | New illustration v1 | `950e8fa46c6ecf72fde5e9e718a69ad7bd34edc7cb4fb097de1c0e4e4863b273` |
| Anchor & Saucer | New illustration v2 | `e1de7fc58e093cca60cfe5a1b78ad8e79d37be591fe8a6460e9ab8fa2b2919e6` |
| Relatively Good Clocks | New illustration v2 | `176e0cfd5359578187c18b893f55cd955cf1f1b98a69879c349022045c60829d` |
| Rock Solid Companions | New illustration v1 | `bd89eb5cdc8ef36a1de306a4faf7fe7c7e43fcefd2d88f20115ff9161cc8c253` |

`manifest5.json` SHA256
`4d30c1c3a3c565d1a7679d3abd7614077ceea35534ddf24367261699b946cced`
records the five final sources and excluded variants. All source/copy hashes
and dimensions match; Cosmic Tacos is853×1280 and the new art is1024×1536.
All generation and image editing used builtin `image_gen`; no host tool install.

Root and independent visual review pass the four selected illustrations for
correct complete text, distinct product stories and consistent art direction.
M03v1 omitted the brand ampersand; its targeted v2 restores it. M04v1 gave the
human customer a third hand; v2 removes it while retaining both watch-holding
hands. These failures remain recorded rather than being counted as passes.
M02's four-eyed grocer differs from the suggested three eyes but does not impair
the product story. Independent `Review.md` SHA256
`0a3bd0aab670ee5435c3b80fc099757e217aaa7af3dd3850f7111d9c3a41499b`
records findings. Owner review, aperture fit and native display checks remain open.

## Lounge: five families, eight unchanged source files

Private folder: `.agent/local/StationRefinement/LoungeCampaigns20261007`.
Its README links the two supplied originals, three existing portrait graphics and
their three landscape alternatives. No artwork was generated or edited for this set.

| Campaign | Selected portrait SHA256 |
| --- | --- |
| Spousal Abduction, owner original | `875ad89b977029de6cfb63e84692cd86c90c88f37dbd72030b1525f460dc83fa` |
| Dock Drink Dock, owner original | `7455c0f962d6ac91c7616f8f4b901a52a4c7f9e3c17fe9950fb2388adf4d8eba` |
| BENT ORBIT, existing illustration/layout | `17f458868d57527961a78929e3ee1946022aac8fca6218424b849d9cc7e8c657` |
| VEL & VOID, existing illustration/layout | `18ada2c716ac256f846f21e612b9630e4a01326d38bbeb5025f02f541ebe58dd` |
| PORT AUTHORITY, existing illustration/layout | `23083c21d0f94f7dffbef467164e1b6e1346989f8e673867c8f16c930026407d` |

Manifest SHA256 `503bb4b1e2f556dfa4f2c29614b32774d053c8cc620687b90eea69d4daca6eec`
binds all eight exact copies and their dimensions/ancestry. Independent source review
covers all eight; root also reviewed the three existing portrait and landscape
graphics. Principal text and heroes are complete. The existing graphics have a
cleaner style than the vintage originals. PORT AUTHORITY's landscape has different
case-file copy from its portrait and older manifest; the new manifest records its
actual text. The layouts remain one campaign each. This is source review only.

The saved lounge still cycles four campaigns every12seconds, including HULL ASSURED,
which is a reserve outside the new selection. L's accepted8/10 layout is unchanged.
Two originals are853×1280; retained portraits1024×1536 and landscapes1536×864.
The selected portraits are not fitted to the existing landscape televisions.

## Guarded import preparation

`Scripts/StationAdCampaignSet.py` is import-inert; its CLI only reads the selected
five files. It binds the manually reviewed manifest hash, room, declared identities,
contained file paths and byte hashes. It does not prove semantic uniqueness from
hashes. Variants do not increase the count. Explicit `stage_textures` preflights every
target and the fresh private R/Market/L destination before importing five unsaved
textures. Existing destinations refuse overwrite/resume; partial failures retain
attempted, imported and observed identities. No actor/material assignment or saving
is included. T and central are excluded.

Root ran all nine targeted `Tests/TestStationAdCampaignSet.py` cases successfully,
covering changed files/manifests, escaping paths, duplicate declared families/bytes,
held rooms, destination collisions and partial/unexpected native import identities
through a test double. Test fixtures now use a temporary workspace-root directory,
so a clean checkout needs no private folder. Strict `Path.resolve` encounters
WinError5 under the restricted Windows sandbox; normal host file access passes,
without weakening containment checks. Real R/Market/L manifest inspection also
passes. Fake-engine tests do not establish native import behavior or rendering.
Native staging, compilation readback, dimensions, fit, cycling and saving are UNRUN.
Reviewed helper SHA256 `627a235f9403bf098877d0a04f3dd6ff51a4663944f63aa77b90f91a97e0d7fe`;
test SHA256 `439781806d6db41a231c7bd4d1e45b47aef4016bdbd7b61b296f7c4c23d1c753`.
Independent source review found no concrete blocker. Root syntax compilation,
41structural checks and repository documentation checks pass. No C++ source changed;
no Unreal rebuild, launch, import or gameplay test was performed for this helper.
See [usage and remaining checks](../STATION_EDITING.md#preparing-a-rooms-five-ad-sources).

## Source audit and limits

`RoomAdAssignmentAudit1.md` SHA256
`5bdc46396412fc4843607ed2c1ae777843e75f3347ef6f4a8a65871d473ad4b9`
records the bounded filename/manifest/recipe audit. The sixteen reuploaded
originals provide thirteen campaign families; alternate ratios and reuploads
count once. Original provenance16 has SHA256
`d11ffea0e76dde7b5c0e3b7c6891b271a2362e1ff6b4204375b9c27bc5552600`.

T already has five selected original source campaigns and needs no new art
while its hardware choice is held. L has five packaged source campaigns, but its saved
recipe still cycles four every twelve seconds. The market initially has only
Cosmic Tacos; the four generated sources above now fill that source gap.
The initial showroom source gap was conditional. A later retained-receipt and
layout-source check establishes that Ship & Parts is inside T, without a
separate confirmed showroom room or ad host; no additional five-image job is
justified from that historical plan name. Home apartment monitors and the Cargo
dashboard are genuine screens, but advertising purpose remains unconfirmed.
Protect those functional/residential screens until their actual use is established.

The later mapping is `RemainingRoomAdHosts1.md`, SHA256
`784e81fe0d8daabf0e32d018ace5b583d65e9da7c4aa33cd22caa53427dbbffc`.
It binds the current T service source and retained native service receipt,
existing R archive, L TV frames and Market seller meshes. T/R/L/Market each
have five available source families; the minimum confirmed new-art gap is zero.
R/Market host eligibility and physical fit remain open. This does not establish
that every station screen should become an ad display, or complete installation.

No new images in this record have been imported, assigned, fitted to physical
screens, observed cycling, or accepted by the owner. Artwork and prompts remain
in ignored local storage, not in GitHub or a packaged build. No Unreal call,
normal map save, DLL link, cook or publication is part of this source-art work.
Ad audio remains future work. The lead still owns native integration and review.
