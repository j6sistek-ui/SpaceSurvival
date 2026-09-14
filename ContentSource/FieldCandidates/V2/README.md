# Field V2: thinner additive candidate

V1 remains preserved in the parent folder. Lead review of its actual native interior view rejected the thick opaque strands and cage silhouette. V2 is a separate candidate prepared in response. It has now been imported into four new assets, fresh-validated and rendered in eight unsaved native views. It is not adopted or owner-approved.

| Candidate | V1 -> V2 half-width (cm at source radius 100) | Triangles | Material slots |
| --- | --- | ---: | ---: |
| Electrical primary / branches | 0.65 / 0.38 -> 0.195 / 0.114 | 3,168 | 1 |
| Gravity curves | 0.5 -> 0.15 | 4,740 | 1 |
| Both outer filaments | 0.4 -> 0.12 | included above | shared slot |

Every width is exactly 30% of V1. The boundary centre moves from radius99.6 to99.88 so maximum envelope and all axis extents remain exactly100cm. Gravity centreline samples increase29 ->45 per strand; normals are smooth radial rather than per-triangle. Geometry is still static, and the existing gameplay radius/forces/collision/timers are untouched.

The separate material graph is additive/unlit, one-sided and depth-tested, with no opacity mask, WPO, refraction, texture assets, core sphere or global bloom changes. One Custom float4 supplies RGB and opacity through two component masks. Exact existing parameters remain Tint, Color and Emission; UV0, Time, PixelNormalWS and CameraVectorWS are additional graph inputs. View-angle opacity softens strand edges. The much fainter outer boundary retains a positive, Time-independent floor. Thin-line visibility at distance is not established by a positive mathematical floor.

Electrical grain remains within0.90..1.00; gravity flow within0.80..1.00. Their decorative motion cannot create a new warning or discharge schedule. Electrical amplitude and white-core contribution follow supplied Emission, including the existing2.8 discharge. Gravity amplitude follows supplied Emission; decorative longitudinal movement remains outer-to-inner. The native preview will hold existing scalar samples as V1 did; live clock/HUD integration is a later check.

`SourceReport.json` binds actual OBJ/blend/MTL/HLSL bytes and16 immutable original/V1 inputs, including the supplied original GLB. Runtime C++ snapshots from V1 are checked against immutable Git base ccfc91400ca10168dba7471fa5a2f3c888a32d6e, rather than requiring current runtime files to remain at their historical hashes. The author/validator check current Source/Config/unrelated Content only across their own call, so deliberate lead integration changes remain possible.

`SourceValidation.json` records the successful actual OBJ parsing, finite unit normals, UV roles, nondegenerate triangles, exact spherical envelope,30% width ratios, protected hashes and five Python AST checks. That receipt is the earlier CPU-only checkpoint. The actual Unreal results are recorded below; it is retained as historical source evidence.

The prepared scripts are `Scripts/AuthorFieldCandidatesV2.py`, `Scripts/ValidateFieldCandidatesV2.py` and `Scripts/PreviewFieldCandidatesV2.py`. They target only four NEW paths: Meshes/SM_ElectricalFieldCandidateV2, Meshes/SM_GravityFieldCandidateV2, Materials/M_ElectricalFieldCandidateV2 and Materials/M_GravityFieldCandidateV2 under /Game/SpaceSurvival. They do not adopt runtime refs or alter V1. The lead released the shared window after the 21-test suite passed. All three candidate-only Unreal processes completed and the native process is gone.


## Native V2 evidence

`CandidateReceipt.json` binds source, saved assets, shader statistics, raw logs and all eight PNGs. `UnrealImport.json`, `UnrealPersisted.json` and `UnrealPreview.json` retain the fresh reports. Images are under `Native/20daf98c0a824b0dacb42708075db0ff`; V1 images remain in the parent folder for comparison.

| Built field | Triangles | Render vertices | Pixel instructions | Vertex instructions | Samplers | Pixel / vertex texture samples |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Electrical V2 | 3,168 | 2,466 | 208 | 278 | 1 | 0 / 3 |
| Gravity V2 | 4,740 | 3,600 | 206 | 278 | 1 | 0 / 3 |

The additive materials are one-sided, depth-tested and unlit, with the intended opacity connection and no mask/WPO/refraction connection. Both have one section/UV channel, zero collision, +/-100cm bounds and maximum built radius100.0000025cm. No texture assets are referenced; the engine-reported sampler/vertex sample counts are preserved rather than hidden. These shader estimates do not establish frame cost.

Import and fresh validation each preserved141 other Source/Config/Content files. Preview preserved all145 files including the four V2 assets. Reports have empty errors; import retained two missing smoothing-group warnings while fresh built normals were finite/unit. Owned preview PID84268 exited normally0 and was confirmed gone. DX12 SM6, editor quality3 in eleven logged groups,1600x1000 screenshots, exposure1, bloom0.35 and34m radius match the V1 inspection setup. These are editor images, not packaged gameplay.

The directly inspected interior view has much less opaque visual coverage than V1 and leaves the ship/rock visible. Electrical branching and gravity curves remain distinct. Outside strands have visible dashed aliasing at subpixel widths, the boundary is extremely faint, and close gravity curves still show polygon corners. An always-positive shader value does not prove an adequate warning boundary. Those findings keep adoption/readability acceptance open. Temporal behavior, live HUD, electrical damage alignment, forces, audio and frame time were not exercised by the static sample scene.
