# Silver: fitted pink ponytail and magenta irises

2026-10-14, final native checkpoint 15:57 UTC. RPT-20261013-01. Local saved
character update; owner appearance approval, representative performance, voice
and packaged inclusion remain open. This supersedes the earlier long-hair contact
trial and the initial unsaved color preview.

## Result and scope

The existing apartment `BP_Silver_Apartment` now uses the owner's exact DropBear
PonytailGroom, fitted to Silver, with paired temple patches touching the measured
head surface. Group 0 fixes the crown, fringe and temple strands to the head;
group 1 alone simulates the loose ponytail. Hair and the existing lace outfit are
pink. Both irises are magenta; pupils, eye whites and silver skin retain their
original material inputs. Mesh, skeleton, clips and BodyDynamics region settings
were not edited. The old native groom, binding and materials remain available.

The owner required Cyborg verification first. A fresh offscreen check after the
other contributor's upload exercised six Cyborg clips / 82 frames / 724 finite
dynamics samples with runtime module `7d76ae93`; breast maxima were 1.542/1.363 cm.
Ordinary 1600x900 views passed the prior material-streaming check. This opened the
Silver gate; it does not close broader non-pole Cyborg appearance acceptance.

## Saved assets and private sources

All native paths below are private/local, not redistributed by this source PR.

| Asset | SHA-256 |
| --- | --- |
| `SilverPonytail_20261014/Separated/G_SilverSeparated_v3` | `cfa6491fbd8073cfbfcdf46d4936f295a036fd7c7dfd271ea188f6f8ca4cdf33` |
| `SilverPonytail_20261014/M_SilverMagentaEyes` | `3442b3a5d57ad15c3e626edafbbe8d84879e9a9011b30b522e1941bd563e614a` |
| `SilverPonytail_20261014/M_PinkPonytail` | `d6611b7e13f234d93536b1a9113e229f05a3514a626656de74570b0b4cba614f` |
| `SilverPonytail_20261014/M_PinkLace` | `9f2b66cc3a01de066742b14c1cfa973af9423f673699f0c26f8f3c00f59b5ae6` |
| `SilverPonytail_20261014/PA_Ponytail` | `a646963d7cbf72d9d1ea909128a703bf6672e5314bbe5b0b66580bbf3db3963f` |
| `ViableEldReview_20261013/MotionFinish_v1/BP_Silver_Apartment` | `43bba71cdd8fe7292be63ca525aabebd38802a432f1bda275faa6e9ee9c61fe4` |

Paths are relative to `/Game/SpaceSurvival/Licensed`; physical assets are under
`C:/Users/j6sis/SpaceSurvival/Content/SpaceSurvival/Licensed` with `.uasset` suffix.
The production BP backup is `.agent/local/SilverPonytail_20261014/OriginalSilverBeforePonytail.uasset`
(`a76aaa58` before change). Do not blindly restore it over later owner work.

Owned source:
`M:/SpaceSurvival/UserDownloadedAssets_SpaceSurvival/Content/VaultCache/FabLibrary/PonytailGroom-d8c790ae/metahuman/UE_5.6/gb_ponytail.mhpkg`.
Its imported private source `SilverPonytail_20261014/Source/ponytail` remains
byte-identical (`b0e3c23b`). The earlier Blender master remains a recovery source;
this native ponytail/color pass is not baked back into that Blender file.

## Authoring and reproduction

`SSGroomAuthoring` is editor-only. It reads strand descriptions and validates a
new, unsaved two-group candidate inside the private Silver namespace. Dry run is
the default; malformed descriptions, invalid names and existing targets are
rejected. It rebuilds interpolation/simulation data before use. There is no
runtime content-authoring API or vendor overwrite.

`Scripts/PrepareSilverPonytail.py` consumes retained `SourceStrands.json` and
`HeadPoints.json` in the ignored task folder. The output reproduces every reviewed
point, UV and guide assignment exactly. It uses existing Python/numpy and creates
only a new output file. Example from the canonical repository:

```powershell
python Scripts/PrepareSilverPonytail.py --strands .agent/local/SilverPonytail_20261014/SourceStrands.json --head-points .agent/local/SilverPonytail_20261014/HeadPoints.json --output .agent/local/SilverPonytail_20261014/NewDescription.json
```

In Unreal, `Scripts/ConfigureSilverPonytail.py` takes `DESCRIPTION_PATH`, a fresh
`CANDIDATE_NAME` and optional `APPLY=True` globals. Run the default dry run first.
It configures/saves only the new groom, never a production BP or map. Stop PIE
before authoring. The published recipe's syntax and preparation were checked;
its equivalent local recipe produced the reviewed native asset. No redundant
candidate was created solely to test the packaged recipe.

The vendor tie split is at source Y=-9.5 cm for the long rear strands; fit is baked
as scale (1.18,1.10,1) plus (0,-4,3) cm. Do not apply that transform twice.
The two groups have 21,113/4,610 render strands and 2,112/461 independent guides.
There are 550 new mirrored surface-following temple strands per side. Attach the
groom to `head` with rigid binding and no skin binding asset. Deferred attachment
sets the inverse reference-head transform; immediate component transforms were
overwritten in earlier failed fitting trials.

Tail: Cosserat rods, 5 substeps, 8 iterations, gravity -981 cm/s², air drag .35,
bend stiffness .2/damping .1, stretch stiffness 1/damping .1, projected collision
radius .15 cm and 32 guide points. Crown simulation is explicitly disabled in
both physics and LOD settings. Render width .02 cm, root scale 1.15, tip .4.
The physics asset derives from Silver's existing head collision asset.

Eye shader: `saturate((G-max(R,B)-.005)*70)` selects iris green, multiplied by five
rectangles on the original 2048 texture: (809,1344)-(838,1374), (56,1483)-(74,1509),
(1132,1477)-(1156,1505), (316,99)-(330,121), (1279,46)-(1293,62). Lerp the original
color toward `G * IrisMagenta`, linear (.8,.035,.46). The UV restriction prevents
compression noise from tinting silver skin. Original roughness/metal/normal inputs
are retained. Hair linear tint is (.12,.035,.065), roughness .42, specular .5.
Lace tint is (1.65,.28,.65) over the original desaturated base; opacity is preserved.

## Verification and failures retained

- Canonical Editor build PASS: 8.76 seconds. Editor module `bd343b56`; runtime
  module remains `7d76ae93`. Existing engine-header deprecation warnings remain.
- Native dry run, malformed-input/path rejection and overwrite refusal PASS;
  no assets created by the guard check. Scoped C++ clang-format check PASS.
- Source handoff: 42 structural checks, Python compileall, content validation
  (26 meshes / 17 WAVs), documentation consistency and whitespace checks PASS.
  No domain gameplay changes; the unrelated full automation suite was not run.
- Deterministic preparation exactly matches the reviewed strand/guide/UV JSON.
- Studio: 94 frames, 2,510 finite samples, 28.5-second dance. All five static views,
  a 16-frame motion sheet and selected detailed poses were visually reviewed.
- Final fresh-process apartment: actual `HomeHub/Residents/Silver` at
  (6900,4620,-169.5), yaw90; saved BP/materials/groom and unchanged BodyDynamics
  settings read back. Group Niagara activity `[false,true]`.
- Five unique full-size apartment views show fitted hair, paired temples and
  magenta irises without skin tint. Normal player viewport 1600x900; no texture
  residency force, map lighting edits or quality override.
- Actual apartment dance: 91 frames / 801 finite samples over 28.5 seconds;
  body offset maximum 1.5624 cm, hair bounds radius maximum 40.222 cm. The sampled
  poses show fixed crown coverage, moving tail and no explosive deformation.
  This is a bounded visual/motion check, not an all-animation collision guarantee.
- Initial color edits during PIE did not persist despite the preview looking
  correct. Fresh reload caught green eyes; final edits were saved with PIE stopped,
  then confirmed by another fresh process and the final apartment views.
- Early single-group crown simulation, overwritten fitting transforms, unrestricted
  eye color mask and pre-final apartment captures are rejected diagnostic evidence.
- Temporary capture/player cameras and review GameMode were discarded. Viewport
  restored, task editor exited. Station map `78417193`/9,408 actors, project file,
  protected layout and original imported groom hashes are unchanged.

Local evidence: `.agent/local/SilverPonytail_20261014/{Verified.json,Review.html,
ApartmentViewsFinal,ApartmentMotion,EyeSavedReadback.json,MaterialsSaved.json,
AuthoringGuard.json,SplitBuild2.log}`. `Review.html` links unedited stills and a
sampled full-dance playback. No cook, package, upload, physical-input, live-voice
or representative-performance acceptance is claimed.
