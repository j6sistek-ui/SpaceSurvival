# Kraken rear-hem coverage — 2026-10-16

## Result

The pale lower-rear patches were bright flooring visible through the sheer panel in gaps between Kraken's tentacles. CPU topology/texture inspection and frozen native section isolation found a complete panel; the opaque diagnostic covers it continuously. Constant0.65 alpha still showed the floor. The adopted correction gradually reinforces only the lower blue fabric instead of changing the entire back to opaque.

`MI_Gown_BackHem_V12` retains base back opacity0.65 and the original atlas hue mask. A smooth UV0-V ramp from0.84 to0.94 raises blue-fabric coverage toward0.98 at the bottom. Gold/neutral atlas pixels, original cutouts, base color, normals and roughness stay on their prior graph branches. This is a material revision: the saved character mesh remains `SK_Kraken_Gown_Mandala_V11`, with only its placed component's slot8 overridden. Its other eight material assignments, selected Purple Mandala eyes, body, rig, walk, hair and route are unchanged.

## Exact local state

- Canonical station map SHA256 `b5141cb691f41cbb197a867aa508da2be8beec407fc3e579beddd4776ffd81cb`; supersedes `fbb69f362ed086b16b1f0e79da6cb4010e0024d3efad363f7bf8b29e48905402` from the separate sofa-exit repair. Backup: `HemRepair_20261016/StationBeforeHem.umap`.
- Editor module SHA256 `a841a562d86967fb3d5d934c6cb9464328f5875f6d59fd90169052c146618ddf` is unchanged. No C++ source change, additional build, cook, package or release belongs to this material amendment.
- Native candidate master/instance: `/Game/SpaceSurvival/Licensed/StationAssets/KrakenOutfit_20261015/HemRepair/M_Gown_BackHem_V12` and `MI_Gown_BackHem_V12`. The preceding constant-alpha trial remains unadopted.
- Private evidence root: `C:/Users/j6sis/SpaceSurvival/.agent/local/KrakenOutfit_20261015/HemRepair_20261016/`. `Adopted.json`, `Reload.json`, `GuardAfter.json` and `FinalPreservation.json` record save, reload and preservation. Paid/native assets and recovery files remain local, not in this PR.
- Original Blender V11 SHA256 `7bd7344b08a51443480c52cd0e083302066141c8129090f3e7f1aedecdc24905` remains unchanged. No new FBX, mesh deformation, weight or UV edit.

## Verification and limits

- Component2 has1,380 triangles, one closed boundary and no nonmanifold edges; the lower-gown scan found no zero-area faces or opposed neighboring normals under its stated threshold. This does not claim a global mesh audit.
- `BackPanelOriginalAtlas.png`/`BackPanelUniform.png` are isolated CPU source renders. `Isolation.json` and four native views separate all layers, back only, no back and an opaque back diagnostic. `CoveragePreview.json` retains the unsuccessful constant-alpha trial.
- `HemBefore.png`/`HemAfter.png` compare the same frozen pose/camera. The ramp reduces the sharp floor-colored gaps while preserving upper-back sheerness. Candidate motion covers223 samples/five views.
- Sequential guarded adoption and unload/reload preserve all9,480 actor transforms, identities, labels and tags. Nine effective material slots, original walk and head-groom link verify after reload. All170 prior non-map files, including three owner saves, remain unchanged; final175-file preservation passes with clean packages.
- Saved-scene ordinary Play uses the saved component override directly: 93 samples over19.641s and1348.044cm cumulative travel, with valid hair attachment throughout. `SavedHem_Front.png` and `SavedHem_Back.png` are1600x900 views. No runtime material substitution or global lighting/exposure change in this saved review.
- First authoring attempt stopped on the unnamed UE5.8 ComponentMask input and was corrected using reflected input names. A subsequent multi-phase save helper re-entered MAP LOAD through its Slate callback and the owned offscreen editor exited with `EXCEPTION_STACK_OVERFLOW` before adoption. All171 guarded files remained byte-identical. A fresh editor used sequential guarded commands and completed save/reload; failed receipts and original logs are retained. This was a helper failure, not a repaired gameplay defect.
- Existing BP_Blinds null-material and licensed-room/Nanite warnings remain. These NoSound sessions provide no audio evidence. Shallow cuff contact, independent cloth/all-animation clearance, physical-input play, owner appearance, representative performance and cooked-game acceptance remain open.

## Review and references

Open `HemRepair_20261016/Review.html`; check the softer hem and upper-back transparency on her normal route. This is pending owner feedback, not a stop gate for independent work. The selected eyes remain settled. Lead continues cuff contact and the separate Astra/bar repairs; hero/squirrel changes and PR73 remain held, and PR75 is draft/unmerged.

Research consulted October16: [Epic transparency guidance](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-transparency?application_version=4.27) helped frame the rejected sorting hypothesis; actual UE5.8 `MaterialExpressionSmoothStep.h` and `MaterialExpressionTextureCoordinate.h` plus native input reflection define the adopted ramp. Older single-sided/dither trials are not adopted. [Earlier V11 provenance](2026-10-16-kraken-blue-fit-eyes.md) remains historical evidence.
