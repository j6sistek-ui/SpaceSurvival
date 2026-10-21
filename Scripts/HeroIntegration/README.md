# Supplied playable heroes

Current owner direction, October21: Cloth is the station default; white EX7 is removed
from the active roster for Blender repair while its files and identity remain preserved.
Green/blue and the eight older choices remain available. This supersedes the original
October20 white-default import direction; do not replay historical activation.

## Inputs and storage

The original import read the four editable deliveries from
`C:/Users/j6sis/Downloads/Hero_EX7_Rigged`; that path is historical after the owner
storage cleanup. Use the preserved manifest and D recovery archive to locate originals.
`SourceManifest.json` in `.agent/local/HeroIntegration_20261020` pins their hashes and
the packed material graphs/images. New native packages belong only to
`/Game/SpaceSurvival/Licensed/PlayableHeroes_20261020/{EX7,Green,Blue,Cloth}`.
Originals, failed trials and adopted private packages are archived under
`D:/SpaceSurvival_AssetArchive/HeroUnreal_20261020`; Git is not the private-art backup.
No paid generation, texture regeneration or Tripo credits are used by these scripts.

## Current corrective recipes

`RetireWhiteHero.py` plans the exact roster change; `-SSRetireWhiteHero` applies only
an unchanged plan after backing up the native data asset. Other tuning and saves
are checked, not regenerated. Already-applied assets must not be replayed blindly.

`EnableKrakenTextureStreaming.py` plans twelve known Kraken textures, then requires
`-SSEnableKrakenStreaming` to change only NeverStream after hash-verified backups.
It requires existing mip chains and preserves resolution/compression/materials.
[Current tests and native receipt](../../docs/validation/2026-10-21-quality-roster.md).

The editor helper `RepairClothMappings` requires `-SSApplyHeroCloth` and refuses
production meshes; it operates only on explicit `Cloth/PhysicsReview/` copies and
never saves implicitly. Cache invalidation restores mappings, but the current
simulation surface produces unacceptable stretching. Keep the restored production
mesh unchanged until the [visual failure](../../docs/validation/2026-10-21-cloth-mapping-trial.md) is repaired.

## Historical authoring order

Do not replay the pipeline on an adopted character. Read the receipts and inspect
the existing packages first. Each writer has an explicit command-line flag; ordinary
import/activation inspection is read-only. Import resumes its own private assets,
whereas cloth authoring refuses to overwrite an existing cloth setup.

1. In background Blender, export the source manifest. Bake only EX7's five procedural
   seals to4K normals, give the cloth render pieces distinct material slots, then derive
   centimeter-native, unit-root FBXs with `NormalizeUnits.py`. Original blends are never saved.
2. Build the editor module. Import through Interchange with independent skeletons.
   Rebuild the supplied PBR graphs, packed channels, explicit emission masks and coating;
   preserve8K color and4K PBR inputs. OpenGL tangent normals need the green-channel conversion.
3. Retarget the installed locomotion, jump and seated references. Bake additive clips
   to full poses for single-node playback, then measure/correct jump and landing boot
   contact. Source clips are read-only; only derived clips in the new family change.
4. Bind the supplied585-vertex cape/tabard simulation cages,36 pinned vertices and body
   collision. The four separate cloth sections keep the armor out of the simulation.
5. Run `ValidateHeroes.py`: actual render skin, valid/normalized weights, material
   compilation, own-skeleton/full-pose clips,25 surface samples per clip, stride and seat
   measurements. Render with `Scripts/CharacterStudio/CaptureStudio.py` in a fresh
   `StationReviewProfile.py` profile, `-RenderOffscreen`, `-SaveToUserDir`, `-UserDir` and
   `-SSStationReviewRoot`. Live particle readback must wait for the parallel cloth task.
6. Plan activation, then apply the unchanged plan with `-SSActivatePlayableHeroes`.
   It prepends the four verified definitions while preserving every prior row, all
   other tuning and all player saves. Never run `AuthorContent.py` to activate these imports.

`PrepareHeroes.py` requires `-SSApplyPlayableHeroes -SSBakeHeroAdditives
-SSCorrectHeroFeet -SSApplyHeroCloth` for a new private import. `ActivateHeroes.py`
defaults to a plan; the apply pass requires that exact plan and successful validation.
Use the installed editor through an owned offscreen process, never the owner's editor.

## Runtime behavior and validation limits

Existing identity values0–7 stay stable; white/green/blue/cloth append8–11. Cloth now comes
first in the eleven-row roster, and white is omitted until repaired. Missing private art still falls back to existing installed content;
explicit saved character preferences remain intact. All four suits retain185cm exterior
height with a192cm collision capsule. Gait rates use measured planted-foot speeds.
Existing seats can use each new body's own seated clip without editing placed furniture.

The existing Previous/Next/Select hologram interface remains in place. Browsing does
not equip a body; Select does, and Station default resolves Cloth. A stale white preference falls back to Cloth without
rewriting the saved account. Automated checks use
blocked account storage. Full natural play, physical inputs, fine contacts and owner
appearance acceptance remain separate from shader/skin/pose evidence. No package,
publication or PR merge is implied by an editor import.

October20 historical result: canonical imports/default/selection and actual idle playback
are verified. `GameReviewFinal` records all four actual player bodies and wardrobe
projections; the offline review is in Downloads/Hero_EX7_Rigged/Unreal_Review_20261020.
The first EX7 single-node instance lost its clip after initialization; a scoped runtime
recovery now restores it without requiring a wardrobe reselect.

**Cloth physics is still open.** Four assets and585 particles exist, but source and render
sections contain zero deformer mappings. The solver reports zero simulation time and
publishes no particle buffer. Two explicit rebinding trials, including waiting for each
mesh compilation, do not repair this and are not saved. The skeletal fallback remains
selectable. Bound-asset counts alone are insufficient: require four render mappings,
live finite particle samples, collision/motion review and fresh reload before accepting
cloth. Historical `ChaosBinding.json` success describes binding records only.
