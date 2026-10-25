# Kraken waist fit and selective transparency

Owner clarification on October15 (recorded October16 UTC): fit the floating
underwear and gold waist band/medallion to the body. New transparency was intended
for the front rectangle and breast covers, with skin showing only slightly
through the breasts. Issue: RPT-20261015-03. This supersedes V6 appearance only.

## Change and preserved work

- V7 moves860 of7,285 garment vertices using horizontal outside-in rays against
  the central torso surface, with smooth falloffs into connected panel roots.
  Underwear target clearance is7mm, belt8mm; the medallion moves5.5mm inward
  rigidly. The largest displaced low underwear vertex moved12.82cm. Four ray
  misses retain original positions; measurements are diagnostic, not proof of
  all-pose clearance. CPU close front/quarter/back and native walking views
  were reviewed; the broad floating hip loops are removed.
- Component2 is the back drape/high hip rim and is opaque again. Component6 is
  the long front rectangle at opacity0.5. Component3 is the bodice with the new
  independent `MI_Gown_BreastSubtle`, opacity0.75. The existing per-pixel green
  mask preserves gold/neutral alpha. Underwear14–17 uses the original masked
  material. Original sheer sleeves/side panels remain sheer; those were not
  newly made transparent. Upper breast geometry remains unchanged.
- Body/armor geometry, garment topology/UVs/weights/colors,243bones,34actions,
  original textures and V6 head gain0.32 before neck blending are preserved.
  Gown remains12,657 triangles. V4/V6 and Desktop master remain recoverable.

## Saved native evidence

- Mesh: `/Game/SpaceSurvival/Licensed/StationAssets/KrakenOutfit_20261015/SK_Kraken_Gown_V7`.
- Station SHA256: `7187b5bb1ce600f14fbe5ef7c5d8ce94202ef42d7d8fdc1830588877b4bf1d51`.
- Fresh Editor35 reload verifies seven materials, head0.32/front0.5/breast0.75,
  original skeleton/walk, head-attached groom and clean packages. All9,473
  settled actor identities/labels/transforms/tags match. The initial pre-adoption
  fingerprint guard stopped on four existing socket-pose differences (hair and
  three props, under0.24cm/0.04degrees); exact diffs were retained and validated
  before a settled baseline. No arbitrary actor changes were allowed.
- Final normal Survival run uses saved V7 directly, trim1 and no material/mesh
  overrides or forced residency: 173 samples, 37.672s, 2603.12cm,
  advancing walk and head attachment throughout. Four ordinary1600x900 views
  show front/quarter/waist/back; root and an independent reviewer inspected
  candidate views, and root inspected the fresh saved views.
- All42 pre-existing native packages retain hashes. Only the intended map mesh
  assignment and new V7 mesh/material instance are adopted. The existing runtime
  module b07543eb is unchanged; no C++ change/rebuild required for this amendment.
- Editor33 stalled waiting for its local cache during startup, before asset
  loading; only that owned process was stopped. Offscreen unattended Editor34
  completed authoring and35 verified a fresh load. Existing BP_Blinds and room
  rendering warnings are retained; no global lighting or renderer change.

This is not independent cloth simulation, all-animation, physical-input,
performance, packaged or owner appearance acceptance. No merge. Minor gathered
panel folds and existing sheer-edge stipple remain visible. Astra seated clothing
is separate and remains open; the owner backlog records future requests only.

## Local artifacts

Private root: `.agent/local/KrakenOutfit_20261015/WaistFit_20261016`.
Editable `Kraken_Outfit_Fit_V7.blend` SHA256 `1385e32530b7c2e5b66afc1a0411aa209372f0a3ee3d54bb4859e5aebbd3e7cd`.
FBX SHA256 `4a249c242db1ea50e4b2cba195d8955b15df47eeaecc52aa4a9365df426c0f1d`.
Receipts: FitV7Verified, NativeV7Imported, AdoptionActorDiff, Adopted,
FreshReload, FinalWalking and Verified JSON. `Review.html` contains the native
images; the parent review and former MaterialTune review link to the current
result, with V6 review retained. StationBeforeWaistFit.umap is a recovery copy,
not permission to overwrite later owner work. Paid assets are local, not in PR75.
Documentation consistency and whitespace checks accompany the PR amendment.
