# Enemy art candidates

These are separate original models for the two existing Phase 1 enemy archetypes. They are **candidates, not adopted game art**. The owner rejected the earlier graphics; neither studio renders nor successful imports establish the Hybrid quality target.

The Pursuer uses a compact armored wedge and closely grouped aft drives to support its existing direct-pressure role. The Flanker uses a much wider swept silhouette, stepped wing plates and narrow central hull. Both have one central muzzle, recessed sensor apertures, dark titanium structure, ceramic armor accents, cooling fins and restrained amber exhaust. These are visual details; no weapon, maneuver, enemy archetype or gameplay behavior was added.

| Candidate | Triangles | Vertices | Closed assembled parts | Materials | Source bounds, cm |
|---|---:|---:|---:|---:|---|
| Pursuer | 14,180 | 7,248 | 84 | 4 | ±135.5 X, ±95.442 Y, ±31.066 Z |
| Flanker | 14,840 | 7,586 | 88 | 4 | ±118.5 X, ±172.729 Y, ±27.417 Z |

Generate.py is the complete deterministic original authoring source. No external model, texture, image, kitbash or character asset is embedded. It uses the owner's installed Blender 5.1.2. Editable .blend files preserve individual parts and bevel/normal modifiers; OBJ and GLB exports contain one combined mesh per archetype and exactly four PBR material groups. OBJ uses centimetres, +X forward and +Z up. GLB uses metres with standard glTF axis transport. EnemyPalette.mtl records the same material values; SourceReport.json records source hashes and numeric material values.

Generate from the repository root using the existing installed tools:

~~~powershell
& 'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe' --background --factory-startup --threads 8 --python ContentSource/EnemyCandidates/Generate.py
& 'C:/Program Files/EpicGames2/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe' -B ContentSource/EnemyCandidates/Validate.py
& 'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe' --background --factory-startup --threads 8 --python ContentSource/EnemyCandidates/Generate.py -- --render
~~~

The render command uses Cycles on eight CPU threads, 32 samples and denoising. Coordinate any native game profiling or GPU preview with the lead first. The first Blender launch without factory startup crashed before Python ran; factory startup resolved that launch. An early thin-panel bevel produced degenerate triangles; the generator now bounds bevel width by panel thickness and uses two bevel segments. Final exported geometry passed validation.

Validation.json proves every triangle and UV triangle is nondegenerate, normals are finite and unit length with consistent orientation, every edge belongs to two faces, and every connected component has positive signed volume. Assembled parts may overlap deliberately; this is not a boolean-unioned collision mesh. A second fresh Blender build produced byte-identical OBJ, GLB and MTL exports, recorded in Reproduction.json. Editable Blender container bytes are not claimed deterministic.

The six Pursuer-* / Flanker-* PNGs show forward-quarter, rear-quarter and top views. RenderReport.json binds them to the generator. The final source review corrected a clipped Pursuer top view, excessive continuous ceramic wing area and smeared metal edge normals. These are Blender studio images, not Unreal gameplay.

The existing enemy source OBJ files, original Unreal enemy packages, GenerateGeometry.py and supplied Acornaut source are preserved by hash. No authoring hook or current Data Asset selection was changed. The dedicated Scripts/AuthorEnemyCandidates.py can create only these six separate assets:

- /Game/SpaceSurvival/Meshes/SM_PursuerCandidateV1
- /Game/SpaceSurvival/Meshes/SM_FlankerCandidateV1
- /Game/SpaceSurvival/Materials/M_EnemyCandidate_Titanium
- /Game/SpaceSurvival/Materials/M_EnemyCandidate_Ceramic
- /Game/SpaceSurvival/Materials/M_EnemyCandidate_Recess
- /Game/SpaceSurvival/Materials/M_EnemyCandidate_Amber

The author refuses incompatible existing candidate versions or changed source hashes. Scripts/ValidateEnemyCandidates.py performs fresh-editor material, bounds, triangle, UV, imported-normal and collision checks; --preview adds unsaved Unreal actor renders from three angles and head-on for each archetype. Engine execution remains coordinated by the lead.

The existing runtime scales visuals by 150 / max(BoxExtent) and retains the separate 150 cm gameplay sphere. These candidates preserve that policy and add no mesh collider. Resulting extreme corner distances are 165.276 cm for Pursuer and 161.363 cm for Flanker; the sphere does not exactly trace every wing or exhaust corner. This must be judged during native collision/readability review, not concealed by altering the gameplay radius. Head-on preview uses the +X side, matching the existing enemy actor's direction toward the player.

Fresh Unreal 5.8.2 import and validation completed on 2026-09-13. Import exit 0 created exactly six assets while 129 existing Source/Config/Content files remained unchanged. A second process loaded those saved assets, validated exact triangle counts, material values, centered bounds, imported normals, unit finite built normals/UVs and disabled collision, then captured eight 1400 x 1000 Unreal studio images. It exited 0 normally; all 135 existing Source/Config/Content files remained unchanged. UnrealPersisted.json, UnrealPreview.json and CandidateReceipt.json bind the results and file hashes. The import emitted two missing smoothing-group warnings from the OBJ/FBX path; explicit imported normals and the fresh built-geometry checks passed. No warning-free import is claimed.

The eight UnrealPursuer* / UnrealFlanker* PNGs add actual +X head-on views to the three studio angles. All eight were inspected: no clipped geometry or missing material sections was observed. Quarter/top silhouettes differ clearly, while head-on geometry remains dark and shallow against this black studio background, especially the Flanker wings. The lead reviewed three native images and identified the need to position the existing muzzle cue at each mesh's forward bound during later integration. Neither this lighting nor a still image establishes gameplay readability. The preview created an unsaved static actor scene, used no game run or physical input, and did not collect performance data.

Remaining limits: one LOD/four sections per archetype have no runtime performance acceptance yet. Studio paint and fixed PBR values still need game-lighting normalization, high-speed silhouette review, final art approval and integration. None of these files substitutes for the outstanding physical input, natural gameplay or listening checks.
