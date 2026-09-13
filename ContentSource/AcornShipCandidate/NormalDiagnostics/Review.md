# Ship material and shadow diagnostic — 2026-09-13

The six solid-surface material graphs now correctly feed object-local position into their subtle roughness noise. Fresh Unreal 5.8.2 reload verified both graph edges in all six materials, along with the original nine material slots, PBR values, bounds and disabled display-mesh collision. Both the rendered repair process and fresh validation exited with code 0. This repairs an actual graph defect; the visible white-panel shadow faceting remains unresolved.

## Evidence and scope

`NormalSettings.json` records the persisted read-only inspection: imported normals, `recompute_normals=false`, MikkTSpace tangent recomputation, weighted-normal setting enabled, low-precision tangent basis, one UV channel and no generated lightmap UVs. No build setting was changed. Source OBJ inspection found 9,656 WarmCeramic triangles and none with all three corners sharing one normal index; this alone is not a proof of ideal normal continuity.

The old author script used `Input` on TransformPosition and `Position` on Noise. Actual UE input names are an unnamed first TransformPosition pin and `World Position` on Noise. Both connection calls had returned false without an assertion. Installed engine source confirms disconnected Noise defaults to world position. The repair uses checked first-pin connections and verifies the resulting WorldPosition → World-to-Local TransformPosition → Noise chain. It saves only six material graphs/metadata. Glass, cockpit padding and emissive material remain unchanged. The source importer now repairs this known owned graph on rerun and refuses unexpected custom input wiring.

`MicrodetailRepair.json` contains the original disconnected graph evidence in its `graphs` field, the six before/after package hashes and matching geometry fingerprints. `AcornShipPersisted.json` records the independently reloaded corrected chains at 09:16:35 UTC. `Review.json` binds receipts, image dimensions and script hashes. These are asset diagnostics, not runtime gameplay or owner art acceptance.

The mesh package remained SHA256 `23c9c18be50728e5d17fa4a545bb334319e010ae25b9845ef942d0fdddae5107` throughout this repair. The built render geometry fingerprint remained `5cc66bbfec97a393789843b40a6fba03bd4b257900b72f72647f723240acb15f`: 134,262 triangles, 79,268 vertices, nine sections, one LOD, one UV channel, exact bounds and no collision. All other content packages also retained their bytes during the repair. This is the current repair baseline; historical initial import receipts have their own package hashes.

## Visual comparison

- `BeforeShadowEnabled.png` and `AfterShadowEnabled.png`: identical camera, mesh transform and three-light fixture. Both retain triangular white-hull patches. Correcting micro-noise does not remove those patches.
- `BeforeShadowFree.png` and `AfterShadowFree.png`: same fixture with cast shadows disabled. The broad white-panel patches are absent.
- `NeutralShadowFree.png`: unsaved uniform neutral material under the same lights, with shadows disabled; broad hull shading is smooth.
- `VertexNormalColor.png`: unsaved unlit vertex-normal visualization; broad hull gradients are smooth.
- `AuthoredNoMicro.png` and `AuthoredShadowFree.png`: initial isolation compares zero roughness modulation with the old authored noise under shadow-free lighting. Their similarity did not support roughness noise as the cause of the broad patches.

These observations support investigating shadow/render interaction next; they do not establish whether shadow bias, smooth-normal geometry interaction or another rendering setting is the precise cause. No normal rebuild or broad shadow disabling has been adopted. The images retain aliasing because temporal AA was deliberately disabled; that is a diagnostic condition.

The fixture uses a stock StaticMeshActor at zero rotation and unit scale, camera `(-720,470,310)` looking at `(-15,0,20)`, FOV 42. Directional lights are pitch/yaw `(-35,-30)`, `(-25,145)`, `(-65,70)` with RGB colors `(0.9,0.95,1)`, `(1,0.89,0.75)`, `(0.5,0.7,1)` and intensities 4, 2, 1. Exposure min/max is 1, bloom is 0, motion blur is 0, screen percentage is 100 and AA method is 0. The saved 1600×900 canvas reflects the camera's 16:9 aspect. No map or diagnostic material was saved.

## Remaining work

The broader shadow defect, pilot hand contact, thin residual tail fragments, glass ordering and motion/rebasing appearance need actual runtime review. Nine material sections and a single 134k-triangle LOD still warrant cost measurement. These checks do not constitute acceptance of the requested Hybrid visual quality.
