# Station shell candidate

Separate station candidate, reviewed by the lead as suitable for native evaluation. The eight isolated assets have been imported, with a UV-only repair preserving the reviewed surface. Runtime integration, native station appearance and owner acceptance remain separate lead-owned checks. Sources are under `ContentSource/StationShellCandidate`; dedicated Unreal scripts are under `Scripts`. The original ignored source execution remains available locally.

`Generate.py` authors 401 editable parts, retaining bevel/weighted-normal modifiers in `StationShellCandidate.blend`. The single `StationShellCandidate.obj` uses centimetres, the station's original XYZ axes and origin, 85,180 triangles, 43,392 source vertices and seven shared PBR material groups. The small MTL records base color, metallic, roughness and emission. It contains no character, deck, console, collision or service assets.

The industrial direction uses bent perimeter ribs, recessed panel layers, machined fasteners, external radiator housings and restrained cyan guides against graphite/blue-grey metal with warm safety accents. This improves structural definition over the existing plain cubes, but the first three views still have a regular, utilitarian silhouette and broad uncluttered front panels. There is no surface wear texture or native material/lighting acceptance.

## Source views and evidence

- `Approach.png`: incoming view of the exact open entrance and existing ship bay.
- `Interior.png`: eye-level view of perimeter detailing and the original service floor.
- `Wide.png`: full frame/roof/radiator layout; decorative housings extend beyond the playable deck.
- `Report.json`: authoring hashes, materials, bounds, service-envelope tests, context and rendering limits.
- `Validation.json`: independent OBJ, normal, triangle-area, image and preservation checks.

All images are 1600 by 1000, Blender Cycles CPU, eight threads and 36 samples. The final render run finished at approximately 2026-09-13T12:26:53Z, logged elapsed 78.079 seconds. They use source studio lighting and approximate deck shading. They are not native gameplay images, performance evidence or a substitute for the next actual-station capture.

The first geometry check caught bevels reaching the thickness clamp on thin panels, producing invalid corner normals. The final author limits box bevel width to 35% of its smallest dimension. Final independent checks find all 255,540 normals valid (maximum unit error 1.804e-7) and no triangle area below 1e-6 square centimetres. The geometry count remains 85,180 triangles.

## Preserved spatial contract

- Original playable/collision deck: 3400 by 2800 by 100 cm, centered at (0,0,-60), collision top Z=-10 cm. It is transient render context, not exported.
- Inbound wall plane: X=-1700 cm. The entire approach region X<-1675, Y between -700 and +700, Z>-10 contains no candidate triangle AABB. No entrance lintel was added.
- Existing overhead beam underside remains Z=967.5 cm, with the previous seven X positions and 18 by 2800 by 25 cm sizes.
- Seven original service anchors and 180 by 180 by 280 cm envelopes are clear after triangle/AABB separating-axis checks. The independent Mica corner envelope (1020,1040,-10) to (1200,1220,270) is also clear.
- Original ship display remains at (850,0,220). Its existing source mesh is transient render context and excluded from source exports.
- Candidate decorative bounds: X[-1749.600029,1715.999985], Y[-1546.000004,1546.000004], Z[-115.499997,1000] cm. External housings add no walkable space and must remain NoCollision.
- Original character GLB, ship source, station C++/header and referenced deck bitmap were hash-preserved during authoring. The source script does not write any of them.

The renders use exact-sized source console boxes at original anchors, without service labels or animation. Mica, hero and moving service machinery are not reconstructed for the source render. Their native assets and all interaction logic remain runtime-owned.

## Intended visual replacement mapping

The lead will implement a conditional presentation path only after import verification. Resolve the candidate successfully before suppressing anything. If it is missing, retain the complete existing presentation.

| Existing BuildHub geometry | Candidate-present handling | Preserved behavior |
| --- | --- | --- |
| Solid deck Cube at (0,0,-60), scale (34,28,1) | Keep visible and colliding | Exact deck collision and floor height |
| `TexturedDeckPanels` | Keep every instance | Existing deck material, mip policy and tile transforms |
| Two solid side-wall Cubes, ten solid columns, two inbound wings and one aft low barrier | Keep components and collision; hide their visual mesh and shadow casting | All 15 collision transforms, responses and world-static type remain exact |
| `DeckPanels`: twelve side-panel and twelve canopy instances | Suppress these 24 cosmetic instances | Batch is NoCollision; no service logic attached |
| `ServiceStructure`: twelve side rails at Y=±1365/Z365 and seven overhead strips at Z980 | Omit only these 19 matching cosmetic instances | Preserve ship cradle, service-arm base, crate pallets, Mica bench and story plaque structure |
| `DeckGuides`: twelve canopy strips at Y=±1150/Z949 and two perimeter strips at Y=±1340/Z8 | Omit only these 14 duplicated cosmetic guides | Preserve the fourteen runway strips at Y=±650/Z=-5 |
| `BayPaint`, bay ship, service arm, seven consoles, Mica, crates, beacon, plaque and station lights/audio | Keep unchanged | No service movement, interaction, collision, animation, texture or lighting changes |
| New shell display | One static-mesh component at relative identity, scale one, NoCollision; no overlaps/navigation contribution | Presentation only; all physical geometry above remains authoritative |

Suppressing a whole `ServiceStructure` or `DeckGuides` component would also remove unrelated cradle/guidance content; do not do that. Avoid leaving the old visible walls/roof/panels beneath the new shell, which would cause overlapping surfaces and shadows. Do not hide the root actor or disable the preserved collision components.

## Import history and validation

`Scripts/AuthorStationShell.py` exposes `main()` for authoring and `main(validate_only=True)` for read-only validation. `Scripts/ValidateStationShell.py` exposes `main()` and invokes the latter. They target exactly `/Game/SpaceSurvival/Meshes/SM_StationShellCandidateV1` and seven `/Game/SpaceSurvival/Materials/M_StationShell_*` materials. An already-valid asset is loaded and checked without resaving it. Unrecognized package/source changes fail; the only migration exceptions are exact hashes of this task's retained failed candidate states.

The first isolated import ended at 12:45:57Z on 2026-09-13. It saved seven materials and the UV-less mesh while preserving all 152 preexisting Source/Config/Content files, including 110 game packages. Unreal reported degenerate tangent bases. That version was not accepted for integration. Its source OBJ, Blend, source receipts and import receipt remain under `HistoricalEvidence/InitialNoUV`.

The UV-only revision adds dominant geometric-face box projection at a one-metre repeat. It preserves all 384,513 geometry, normal and material records exactly (digest `c3f45f946eea6ede6c06983638cd7ba408bb586644ad62f04d4c989521d0a8f7`) and all three reviewed render PNGs. There are 255,540 explicit UV corners; independent float32 checks find no degenerate UV triangles, with minimum absolute determinant 2.09508e-6. The editable Blend has a `StationBox1m` UV layer; the generator derives evaluated-face UVs again after bevels. Box-axis seams and repeated coordinates are intentional. This is a tiling UV layout, not a nonoverlapping lightmap atlas or a texture-art approval. `UVRevision.json` records this source revision and its historical pending-native status; later receipts supersede that status without rewriting it.

The first UV reimport unexpectedly routed through Interchange despite the requested FbxFactory. It retained seven material slots but generated 232 sections, failing the strict seven-section assertion after saving only the owned candidate mesh. `HistoricalEvidence/UVInterchangeSections/Failure.json` preserves the exact executed-script hash, package identity and section inspection. The importer now scopes the installed OBJ/FBX legacy-import CVars to the individual import and restores their prior values in `finally`; it does not write project or global settings. Final mesh validation runs before saving.

The corrected import finished at 13:05:25Z. It has 85,180 triangles, 80,001 render vertices, seven unique material slots/sections and one full-precision UV channel. The render-vertex increase from the UV-less 54,240 is due to UV corner splits; the expanded built LOD0 triangle positions and normals are identical to the initial surface at six decimal places, with winding retained. The fingerprint is `3f1968e5cbffba7cd3b09a8c484349b18b9543d6b98878dfe6413c69654bd123`. Imported normals remain enabled, normal recomputation is off, tangent recomputation and MikkTSpace are on. All 255,540 exported normal, tangent and binormal vectors are finite and nonzero. No degenerate-tangent warning remains in this repair log. A generic FBX missing-smoothing-group warning remains; the measured unchanged authored normals are the evidence boundary, not a claim that the warning never occurred.

The mesh remains at centimetre scale with exact zero import translation/rotation, no scene/unit conversion, no generated simple collision, every section collision disabled and BodySetup NoCollision. Only the candidate mesh package changed during repair; all seven candidate materials and the 110 original packages remained byte-identical. The corrected mesh is 1,958,805 bytes, SHA-256 `dcfcf42e8d44c5be3f6e6e1988de8e0eef3d35f771ed5526e0dd386e36462738`.

Each material is opaque DefaultLit with exact Color/Metallic/Roughness/Emission defaults and a checked five-node graph. The materials have no referenced textures. The editor's compiled estimate is 339 pixel instructions and three reported samplers per material; these are engine shader statistics, not a zero-sampler claim or frame-time measurement. Seven sections may submit separate draws in each applicable pass. The mesh currently has one LOD; no runtime distance/LOD or GPU performance result is implied.

`UnrealImport.json` retains the successful UV repair receipt, including the before/after native surface comparison. Routine outputs are `Saved/Validation/StationShellImport.json`, `StationShellPersisted.json` and this task's `StationShellIdempotence.json`. Fresh-process results and the concise `UnrealValidation.json` handoff bind the final package/source identities and preservation checks. They do not establish native station presentation or gameplay collision integration.

`SourceRevision.json` preserves the earlier promotion history. `Report.json` now binds the UV-aware generator and records the original render-generator identity separately; `Validation.json` is the refreshed independent source check. Protected original character/ship/deck sources remain exact. Historical station C++ hashes are context because the lead separately owns its presentation integration.

Native evaluation must use the actual map, station lights, character, deck and service scale in a fresh isolated fixture. The lead owns visibility gates, regression tests, build and capture; there is no owner-editor or live-PIE dependency. No runtime C++ change, gameplay collision change or commit was performed by this content subtask.
