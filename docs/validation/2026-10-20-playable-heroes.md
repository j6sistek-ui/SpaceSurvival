# Supplied playable heroes — October20

Owner request: import white EX7 plus green, blue and cloth heroes into Unreal,
validate materials/animation/weights, establish white as the default and expose the
others through the existing character selector. This supersedes their earlier
asset-only hold. It does not authorize changes to unrelated crew, maps or flight behavior.

Source branch: `codex/hero-select-20261020`, based on wardrobe PR76 head`3174bec`.
Native work is isolated first; adoption into the owner checkout and final runtime
evidence are recorded below when verified. No automatic merge or packaged release.

| Hero | Render triangles | Skeleton bones | Material slots |
| --- | ---: | ---: | ---: |
| White EX7 | 135,476 | 82 | 21 |
| Green | 74,858 | 61 | 2 |
| Blue | 72,953 | 61 | 2 |
| Cloth | 52,324 | 106 | 5 |

Every mesh retains185cm exterior height and at most4 skin influences. The actual
render buffers report zero invalid bone indices, unnormalized weight sums, missing
material slots or shader compile errors. The32 derived gameplay clips each use their
own mesh's skeleton;25 CPU-skinned surface samples per clip check finite deformation.
That is bounded deformation evidence, not proof of every possible gameplay contact.

The source PBR textures, UVs and authored emission masks are preserved. Five previously
UV-less EX7 procedural seals receive separate4K normal bakes in a derived FBX. The
remaining color/PBR inputs retain8K/4K source resolution. The cloth armor and four cloth
pieces receive separate sections;585 proxy vertices/921 triangles and36 pinned vertices
drive cape/front/rear/side cloth with body collision.

## Corrections and retained failures

- A deprecated FBX import created a mesh without a skeleton. The failed private package
  is archived; Interchange imports create independent skeletons and physics assets.
- Initial meter/centimeter skeleton transforms broke retargeted proportions and landing.
  Unit-root centimeter FBXs replace only the failed new imports; originals are unchanged.
- Unreal hides the coating pins from Python. A scoped native authoring helper transfers
  the supplied coating values rather than dropping the material input.
- Template landing clips are additive. Full evaluated poses are baked to standalone
  clips before single-node use. Forced root locking is removed from the corrected jump
  and landing copies so measured contact curves are actually evaluated.
- Dense render cloth contains a degenerate triangle, so simulation uses the supplied
  clean low resolution cages. Section user data must retain the binding across mesh rebuilds.
- The first two studio runs stop at empty cloth inspection buffers. They are retained
  as failed checks, not complete four-character reviews. Parallel-task readback and
  inspection rendering are corrected for the next bounded review.

All originals and rejected assets remain recoverable on D. No blanket remesh, texture
atlas replacement, recolor, paid regeneration or original Blender save is performed.

## Checks and current limits

- Editor builds pass, including the version built on the existing wardrobe branch.
  Installed engine/plugin deprecation warnings remain.
- Six native Menu tests pass with zero test errors; eight existing
  `SS_STATION_WARP_PLACEMENT_REFUSED reason=welcome footprint/support` warnings occur
  in the isolated fixtures. This is not a zero-warning test result.
- Source structure checks and source-content format checks pass. Final documentation,
  scoped format and current-source checks are recorded at publication.
- The new menu test browses every installed body, explicitly selects each supplied
  hero, verifies actual pawn/material/clip assignment and capsule height, resets to
  white, and checks that the active run is unchanged. Account persistence is blocked.
- Full-pose, ground-contact and cloth receipts, native import hashes and raw images are
  under `.agent/local/HeroIntegration_20261020` in the managed worktree.

## Canonical adoption and actual game review

The canonical checkout now has172 new private files/483,605,169 bytes. Its activated
DA_Phase1 is `c3098913ccfc86354db7acf3fd5a0a179c9e198291f5da1478ed2ccf8269d503`;
the four new rows precede the unchanged eight prior rows. Non-hero tuning is unchanged.
Original source Blenders, all three production saves, the station map and unrelated
source hashes are preserved. Original packages/source and rejected attempts remain on D.

Actual canonical Play review `94fe02a9edc8450fb3cd9b56e9686a8e` resolves all four
player meshes/material slots and all four wardrobe holograms. Eight1600x900 captures
and advancing animation clocks are in `GameReviewFinal`. Body shots use a temporary
inspection camera; selector shots use the actual existing panel/projection. The offline
HTML/JPEG review is `Downloads/Hero_EX7_Rigged/Unreal_Review_20261020`.

The first review exposed an empty transient EX7 single-node animation asset after body
initialization, despite a valid idle clip. Runtime recovery restores a missing clip only
on these four new heroes. Fresh Play shows white's relaxed idle and advancing clock;
the new native menu regression also clears the transient clip and verifies recovery.
The first two UI captures used a stale pre-teleport camera; settling the normal pawn
camera before opening the panel restores visible projections. No gameplay camera patch
or station-map edit is used for that harness correction.

Final isolated Editor build passes12.33s and combined canonical Editor build26.75s.
Six final Menu cases all return Success, with0 errors/skips and8 existing station-placement
warnings. They include all four seat-clip fallbacks and first-idle recovery. Fifty source
structure checks,156 string-loaded cook-path checks, source-content formats, Python
compilation, scoped format, documentation and whitespace checks pass. The earlier
parallel build hit a shared ShipCore DLL lock; the serialized retry passes. Engine/plugin
deprecation warnings remain. No package, upload or merge is performed.

## Remaining failed check: live cloth

Cloth physics is **not accepted**. Fresh native inspection finds4 binding records and
585 solver particles (38 fixed/547 dynamic), but0 source/render cloth mappings,
0 solver time and0 published particle positions. Waiting for parallel tasks, forced LOD,
always-tick pose, direct instance readback and two explicit rebind trials do not repair it.
The rebind trials are not saved; the experimental repair helper is removed from the
delivered source. The current skeletal cloth fallback is selectable and renders, but
dynamic cape/tabard movement is not validated. Historical ChaosBinding success proves
binding records, not working cloth deformation. Three studio attempts and failed game
checks are retained. Do not close RPT-20261020-01 or mark this PR ready from core passes.

Epic's [5.8 simulation interface](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/ClothingSystemRuntimeInterface/IClothingSimulationInterface?lang=en-US)
and installed Chaos header show that LOD eligibility gates simulation; the installed
implementation header tracks render mapping availability. This supports the next lead
check: rebuild/retain actual deformer mappings, then verify live motion/collision and a
fresh load. The exact cause of their loss is still UNCONFIRMED. Documentation checked
October20; no publication date is supplied.

Physical keyboard/controller feel, fine furniture/contact review, representative FPS/VRAM,
packaged testing and owner appearance acceptance remain separate work. The existing hidden
flight-pilot behavior is preserved; these imports do not reintroduce a seated boarding figure.
