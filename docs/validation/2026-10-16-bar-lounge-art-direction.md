# Bar colors and observation windows — 2026-10-16 UTC

RPT-20261015-01. The owner supplied four bar mood references and explicitly
authorized darker room colors, Astra indigo/violet/gold, Joy plum hair/indigo
pants, pink owned Illuminated Wall panels and large exterior-view windows.
This is a saved local appearance candidate, not final bar acceptance.

## Saved changes

The existing map remains
`/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime`.
Saved SHA-256:
`5fd8e2570964542ea2c563dd699646f0befb790e9980142d4b640353fae2681e`.

- All 9,473 original actor transforms are preserved. Six new actors add two
  window frames, two glass panes and two pink wall panels: 9,479 actors total.
- Thirteen private material instances and the new `M_Joy_IndigoFabric` parent
  provide 431 material-slot assignments. Six existing local bar lights have
  reduced intensity; this is not a global exposure replacement.
- Astra retains V16 garment geometry and rigging with indigo fabric, violet
  laces and gold details. Joy retains her mesh/animations with plum hair and
  indigo pants. The new pants parent desaturates the original diffuse before
  color multiplication, retaining normal, roughness, metallic and emissive
  inputs. Accepted voices and personality profiles are unchanged.
- The two south-facing observation bays reuse
  `/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_Window600X250_V1_Part1`
  and `Part2`. Each is nominally 7.43 m wide by 4 m high, centered at
  `(3271.429,-4500,0)` and `(5128.571,-4500,0)`, with yaw90 and scale
  `(1,1.238095,1.6)`. Existing collision walls are retained; broad physical
  input/navigation acceptance is not established by that property check.
- The panel mesh is
  `/Game/MLR_IlluminatedWall/Unreal/Rocket/MLR_IlluminatedWall/SM_MLR_BPR_Illuminated_Wall_Deco01_a_c1_Nanite`.
  Its actual assigned source material is
  `/Game/Rocket/MLR_IlluminatedWall/MI_MLR_BPR_Illuminated_Wall_Deco01_a_4096`.
  The private `MI_Leartes_PinkAccent` derivative retains that source.

New private materials live under
`/Game/SpaceSurvival/Licensed/StationAssets/BarArt_20261016/Materials`.
No new purchase, plugin or character/venue rename is introduced.

## Verification and evidence

Private evidence root:
`C:/Users/j6sis/SpaceSurvival/.agent/local/Waitress_20261015/ArtDirection_20261016`.

| Receipt | Verified result / limit |
| --- | --- |
| `PanelInspect.json` | Exact assigned panel material and its parent/texture inputs; the source material is in `/Game/Rocket`, not alongside the mesh. |
| `PantsMaster.json` | Private pants parent and bounded diffuse desaturation; retained surface inputs. |
| `Adopted.json` | Saved map hash, 9,473 preserved original transforms, six additions, 13 material instances, 431 assignments and six local-light changes. |
| `FreshReload.json` | Same map hash, 9,479 actors, recorded transforms/assignments/additions/lights, retained window collision and character meshes/idle/walk, zero dirty packages. |
| `SavedCapture.json` | Five fresh saved-scene camera samples with current Astra/Joy clip positions. This is not full animation/contact or audio validation. |
| `FinalPreservation.json` | 62 guarded files checked; all 61 non-map originals, including three project saves, unchanged. Fourteen new material hashes recorded, same map hash, zero dirty packages and play world ended. This is the enumerated guard set, not an all-disk preservation audit. |

Saved native stills are `Saved_Lounge.png`, `Saved_Astra.png`, `Saved_Joy.png`,
`Saved_JoyPants.png` and `Saved_WindowLeft.png`, all verified as 1600 by 900 PNGs;
`Review.html` is the local review destination. Earlier candidate images, including
`PantsIndigoFixed.png`, remain historical previews rather than saved-state
evidence. The lead reports the owned editor process exited after the guard.

Source is unchanged by this material/scene pass. It uses the existing canonical
combined Editor module, which also includes PR76 wardrobe work, SHA-256:
`0a679b4305cd961dc72cfdb67b93613b6aa2a0b0fc22a63c8b0dd9af58a690ad`.
The existing DLL hash was rechecked against that identity. No new compile,
cook, packaged build or release upload is required or claimed for this checkpoint.
`python Scripts/CheckPrDocumentation.py --repo .` and `git diff --check` pass
for the documentation changes; they do not establish visual quality.

## Open / Check / Still open

- **Open:** the private `ArtDirection_20261016/Review.html` and saved native
  stills for map `5fd8e257`, using the existing module above.
- **Check:** darker-room readability, Astra/Joy colors and observation-window
  shape with the owner. Names, voices and existing service behavior are retained.
- **Still open:** nearby asteroid terrain blocks the requested open starfield;
  the current windows do not deliver that composition. Costume fit through
  movement, Astra's seated shorts,
  service and shared-shot contacts, native audible mix/laughter, physical input,
  representative performance and owner acceptance retain their existing open
  checks. No still-image, save or reload result closes those gates.
