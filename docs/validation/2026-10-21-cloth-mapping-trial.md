# October21 Cloth mapping trial — visually rejected

RPT-20261020-01 remains **PARTIAL / lead**. The missing mappings are understood,
but working particle simulation did not produce acceptable fabric. The original
production mesh is restored; Kraken motion, roster and texture changes remain.

## Finding and bounded implementation

Installed UE5.8 `SkeletalMeshRenderData.cpp` restores cached section data during
rebuild, replacing mappings seeded immediately before `PostEditChange`.
`SkeletalMesh.cpp` documents invalidating the derived-data GUID before rebuilding
cloth mappings. Doing that restores four source and render cloth sections.

`SSPlayableHeroTools::RepairClothMappings` validates every section before updating
any mapping, reports projection distance/extrapolation and forces a fresh build.
It requires `-SSApplyHeroCloth`, accepts only explicit `Cloth/PhysicsReview/`
copies, and never saves. Original-mesh refusal passes on a fresh native load.
The companion read-only streaming-budget helper records the earlier quality pass's
engine counters without altering pool size or quality settings.

Final Editor build succeeds in12.16seconds; DLL SHA256
`78c26277e29d4011c9818978a051c04169924ac80a4e90e9563f8c0c89f2d224`.
Existing engine/plugin deprecation warnings remain. No packaged build is produced.
The earlier roster suites used DLL5e546820 and are historical evidence for their
unchanged gameplay paths, not a rerun on this diagnostic helper build.

## What was actually exercised

- Saved review-copy reload retains52,324triangles,31,426vertices,106bones, four
  mappings, valid weights/materials and the original skeleton/physics/materials.
- Actual RHI playback publishes585particles across four cloths,38fixed and547
  dynamic;15initial and46idle/jog samples have finite moving buffers.
- A brief production-path trial was then reviewed in a fresh private profile:
  the actual default player selected Cloth without replacing its mesh or forcing
  animation. Its normal `wait_for_parallel_cloth_task=False` stayed unchanged.
- Twenty-eight samples cover idle, walk, a90-degree turn, jump/landing and settle;
  every sample has585finite particles. Controller ticking was temporarily disabled
  in this private probe to prevent release polling cancelling the scripted jump.
  This is not physical keyboard/controller acceptance or a performance benchmark.
- Full-body captures expose pointed stretching and folded/shredded cape/panels.
  Those images override the successful counts: **visual quality failed**.

Projection offsets reach13.21cm for the cape and14.18cm for the side panel;
maximum barycentric magnitudes range4.00–8.79. These large extrapolations are
consistent with the visible amplification and identify simulation-cage coverage
and mapping as the next investigation. They do not prove the complete cause.
Do not attempt to hide this with stronger damping or claim collision acceptance.

## Rollback and retained evidence

Original `Cloth/SK_Cloth.uasset` SHA256
`90bfa7cc31c0c84332f5c4813137afd13c5bf4039e468ed7a6be361dbeac8de8`
is restored byte-for-byte. A fresh editor confirms its previous zero-mapping
state and refuses to run the copy-only repair on it. The rejected trial hash
`eb5acdaef1c57caa033e3b96089864ba3ecbb860ad7679370208de144327d5e2`
and exact original are preserved under
`D:/SpaceSurvival_AssetArchive/QualityPass_20261021/Cloth`; D is not used at runtime.

Private receipts and actual frames:
`.agent/local/QualityPass_20261021/ClothCacheTrial/`
(`Result.json`, `Visual.json`, `Locomotion.json`, `Reverted.json`,
`MappingAudit.json`, corresponding exit/save guards and PNGs).
An interim `Adopted.json` is explicitly superseded by `Reverted.json`.
The first visual probe's Python pawn-access error is retained separately and
was corrected before the successful captures; exit0 alone was not accepted.

Production saves and final original mesh are preserved. Lead next: fit the
simulation surface to the render garment, recheck attachments/gravity/body
collision in actual motion, and only then adopt a visually sound result.
Owner need not retest the rejected candidate.
