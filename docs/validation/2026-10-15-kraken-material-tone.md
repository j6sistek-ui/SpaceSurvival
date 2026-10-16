# Kraken head tone and green-fabric transparency

Owner review on October15 rejected the pale face against the darker body and
requested approximately50% transparency for the green gown fabric.
Issue: `RPT-20261015-03`; this supersedes the V4 appearance checkpoint only.

## Change

The old head material brightened its texture by RGB(1.262577,1.266450,1.321779),
based on neck samples. The derived head material adds `HeadSkinBrightness=0.32`
before the existing neck-color blend. Face and antennae now read charcoal gray
with their texture details retained; body materials and the neck target remain
unchanged. Lighting and exposure were not changed.

The gown retains12,657 triangles:3,234 solid/cutout,6,198 original sheer, and
3,225 green-fabric/bodice triangles. `FabricOpacity=0.5` applies to teal pixels;
gold and neutral pixels retain their original alpha. The original4K texture
maps are unchanged. The shader uses:

```text
GreenMask = saturate((min(G,B)-R) / max(max(R,G,B),0.001) * 25)
Opacity = BaseColor.A * lerp(1, FabricOpacity, GreenMask)
```

The first V5 candidate selected only whole triangles without gold samples.
It produced patchy edges on the coarse bodice and was rejected before adoption.
V6 assigns the whole bodice section and uses the texture mask above. The original
white sheer panels and separate solid gold sections remain unchanged. Independent
front/quarter review found no new blocking sorting or patch-boundary defect.

## Saved result and verification

- Current mesh: `/Game/SpaceSurvival/Licensed/StationAssets/KrakenOutfit_20261015/SK_Kraken_Gown_V6`.
- Saved map SHA256: `61408f7c89a8a5a9c55aec77b43d1826416f9d136c7cfa3677b41b3e0b9e6279`.
- New material instances are in the same root's `MaterialTune` folder:
  `MI_Kraken_HeadTone` and `MI_Gown_GreenBlend`; both controls remain editable.
- Fresh Editor32 reload verifies six material slots, both parameter values,
  original skeleton/walk, head attachment and clean packages. The first immediate
  load showed four socket-attached world-pose differences (hair and three existing
  props), all under0.24cm; retained `ReloadActorDiff.json` records them. Repeating
  the settled map load matches all9,473 numeric actor fingerprints exactly.
- Final normal Survival run uses saved V6 directly, crew trim1, without temporary
  material overrides, lighting changes or forced texture residency. 108 samples
  span 37.984s and 2537.23cm, with advancing walk and head attachment throughout.
  Four ordinary1600x900 front/quarter/head/back views were visually inspected.
- All34 pre-existing protected packages, including original Kraken, vendor and
  V4 assets, retain hashes. The editable V6 preserves body/gown geometry, weights,
  UVs, vertex colors,243bones and34actions. Native import explicitly preserves
  the neck vertex colors. Desktop master and previous V4 remain unchanged.
- This amendment changes private assets and documentation only. The existing
  canonical runtime module `b07543eb` is unchanged; no C++ rebuild was required.
  Documentation consistency and whitespace checks accompany the PR update.

Existing sheer-edge stipple, BP_Blinds material warnings and a VSM local-light
overflow warning remain recorded. No global rendering change was made for them.
This is not independent cloth simulation, other-animation, performance, packaged
or owner-appearance acceptance. Astra's seated shorts remain separately open.

## Local review and provenance

Private root: `.agent/local/KrakenOutfit_20261015/MaterialTune_20261015`.
Use `Review.html` there or the updated parent `Review.html` for current views.
Editable source: `Kraken_Outfit_Fit_V6.blend`, SHA256
`5d953e8c0dd010b9db544b115d8d8436d3a54e4bc1a03647e83a6f02819236c4`.
FBX SHA256: `69c2fab1621bfc5480ee0959240ec1e938581c033f7915068f8447bf1e6baa85`.
Key receipts: `SplitV6Verified.json`, `NativeV6Imported.json`, `Adopted.json`,
`FreshReload.json`, `FinalWalking.json`, and `Verified.json`. Exact pre-change
map backup: `StationBeforeMaterialTune.umap`; do not restore over later work.
Source PR75 records the change; paid/local assets are not uploaded. No merge,
package or publication occurred.
