# Four-way cryo comparison — October 21, 2026

Scope: finish all four owner-supplied GLBs consistently, retain all four native
Unreal variants, then compare appearance and runtime load risk. The owner's
reference images establish glass, icy edges, readable blue screens and cold
atmosphere; they are visual references, not instructions embedded in a document.
Native volumetric fog and Niagara are explicitly required.

## Prepared and saved evidence

The local `glb-baseline.json` inventories the four untouched downloads. Full
source hashes and resource counts are preserved in
[source-provenance.json](../../Scripts/CryoComparison/source-provenance.json).
The [pipeline README](../../Scripts/CryoComparison/README.md) records equal
treatment and the private storage boundary.

The final raised-console assemblies supersede the earlier 13-component finish:
all four have 19 components across 12 roles. Each console has dark backing,
glass raised 4 cm, a transparent generated HUD at 4.25 cm and a narrow frame;
the native HUD material scans every 5.5 seconds. Original body topology and
source texture resolutions remain unchanged. Editable `.blend` and finished
GLB copies remain on D:. Blender preview images are not Unreal evidence.

The isolated UE 5.8.4 scene contains 76 active mesh components, four Niagara
actors, four local fog volumes and shared exponential volumetric fog. The
namespace stores 124 `.uasset` files plus one map; ten assets are retained
recovery from the opaque-console version. The bounded Niagara material uses the
generated mist image instead of the donor atlas/cutout. Two shadowless cyan
lights per chamber share a six-second eight-track Level Sequence.

The latest fresh capture, `Unreal_20261022T025919Z_52468`, contains eleven
real-renderer screenshots with zero receipt errors/warnings; 124 assets load and
all 125 protected package hashes remain unchanged. The source hashes are also
unchanged. [Sanitized native preview receipt](2026-10-21-cryo-native-preview.json).
The initial overexposed scene and escaping smoke plume were rejected
before the bounded material/shared lighting correction. Sixty-nine later samples
measure matching interior intensity 5–11.989 lumens and rim intensity 4–9.990
lumens across all four. This establishes editor sequence playback. Native game
autoplay/restoration was subsequently verified below; packaged behavior remains
unmeasured. Owner-project copying is hash-verified below.

The fixed-camera temporal pair is separated by 3.203 seconds. Its static control
region has zero RGB change while the hologram/interior regions change; this
supports temporal activity but cannot isolate Niagara motion from changing
lighting or volumetric history. The capture used a stage-only
`r.LocalFogVolume.GlobalStartDistance=0` preview setting, not evidence that a
1000-to-10-to-1000 runtime restoration sequence succeeds. The tracked stage
template excludes that persistent preview override.

All four Niagara components report `is_active=False` at every screenshot
request in this editor capture. Four saved actors and changing interior pixels
therefore do not establish live Niagara playback. The separate actual-game
activation, bounds and visible-mist check below closes that specific gap.

## Native game playback and visual review

The accepted run `CryoGameRuntime_20261022T031733Z_31568` uses the real renderer
in an uncooked native game world. [Runtime receipt](2026-10-21-cryo-runtime.json)
records 66 samples over 14.124 world seconds, two natural six-second loop wraps,
eight lights playing in matching phase and all four Niagara systems active with
nontrivial bounds. BeginPlay starts the native sequence; the observer does not
play or seek it. The fog start distance is 1000 cm before BeginPlay, 10 cm during
playback and 1000 cm after EndPlay. Source and native package hashes are unchanged.

The lead reviewed the D runtime pair and all-four overview: bounded cold mist,
cyan illumination and no checkerboard particles. The disposable DefaultPawn was
hidden only for these review captures; no asset save was needed. The process
exited successfully with zero errors. Its only log warning concerns a slow
Python startup command, about 2.47 seconds; no material-usage warning remains.
This establishes native presentation playback, not production-map integration,
owner-project launch, packaged load time or GPU performance.

Lead visual review favors **D for the hero presentation** and **A for lower
resource cost**. D preserves the strongest chamber/occupant detail in the native
views but also has the highest geometry and uncooked storage cost. A offers the
lowest geometry count and the lower body-texture tier. B/C remain available for
owner comparison; no unsupported numeric quality score is assigned. Final owner
preference remains open.

## Static resource comparison

[Sanitized metrics](2026-10-21-cryo-resources.json) come from
`cryo-costs-final.json` at 2026-10-22T03:15:23Z. All four source hashes still
match the baseline, and all 104 analysis input hashes remain unchanged.

| Variant | Finished triangles | Model-owned native files, MiB | Estimated body textures, MiB |
| --- | ---: | ---: | ---: |
| A — Cybernetic Cat | 32,101 | 18.02 | 42.67 |
| B — Futuristic Cat | 56,448 | 30.46 | 74.67 |
| C — Futuristic Fox | 57,711 | 20.99 | 42.67 |
| D — Meshy Raccoon | 110,498 | 88.04 | 74.67 |

Each has 19 static material sections and adds exactly 6,610 triangles. Section
counts are not measured draw calls. Native size is uncooked disk storage, not
runtime residency or load time. Texture estimates assume standard BC1/BC3/BC5
formats with complete mip chains, exclude geometry/shaders/particle and fog
buffers/overdraw/driver allocation, and do not measure actual residency. Shared
finish textures add an estimated 10.67 MiB once, not once per chamber. The
retained donor dependency closure is not a measured final live dependency set.

These resource facts support A as the lower-cost candidate and D as the heaviest;
they are not an FPS or load-time ranking. C shares A's body-texture tier but has
more geometry; B shares D's texture tier with fewer triangles. Source body
resolutions have not been reduced for any model.

## Retained failures and limits

- The first commandlet-only authoring run lacked `StaticMeshEditorSubsystem`.
  The full offscreen Editor supplied the required subsystem. This is an editor
  service distinction, not a source mesh defect.
- Generated shared PNG dimensions require deliberate Unreal texture build
  sizing/mips. The saved correction preserves original source images. The three
  shared display textures now use sharpened mips and explicit nonstreaming
  residency for text; body textures retain ordinary streaming.
- Source import reports near-zero tangent/binormal warnings. Their visible
  impact must be assessed in the final native views; the receipt does not call
  them repaired or harmless.
- The hologram animates authored text art; it does not display real game state.
  No chamber interaction, opening door, occupant rig or collision is added.
- Editor frame/capture timing, static resource counts and a successful load do
  not establish packaged startup, representative frame times or 60 FPS.
- The first actual-game logic pass rendered checkerboard particles because the
  owned mist master lacked NiagaraSprites usage. The master and its instance
  were corrected, saved and hash-guardedly adopted with backups; the final
  actual-game renders were reviewed again. Editor actor counts did not catch it.
- Simulate verification lacked an active editor viewport on this offscreen
  host. Actual native game BeginPlay/EndPlay observation supplied the accepted
  playback/restoration evidence; no successful Simulate run is claimed.

## Storage and release

Non-Unreal work and revisions are on `D:/Codex/CryoComparison_20261021`. The
original task paths on C: are junctions, with a hash-verified move receipt.
Native review assets remain private local content; the new `.gitignore` entry
prevents accidental raw-asset publication. The exact never-cook exclusion also
keeps this comparison namespace out of the broad SpaceSurvival cook selection.

At 2026-10-22T03:06:21Z, the new namespace was copied into the owner's
`Content/SpaceSurvival/CryoComparison`. A guarded two-material follow-up at
03:15:23Z fixes Niagara sprite usage; the final 125 files/178,288,150 bytes match
the stage and accepted game-run hashes. All 16 donor hashes and 106 original/
import hashes remain intact.
The owner's existing config/ignore text was backed up, then only the exact
never-cook and ignore entries were added. [Adoption evidence](2026-10-21-cryo-adoption.json).
No owner-project editor launch is claimed; this validates copying, not a full
project reload. Native game playback was verified in the isolated stage.

No current gameplay map, playable hero, service, save, C++ module or packaged
release is changed. The isolated source worktree is
`codex/cryo-four-way-review`; owner checkout edits remain outside this PR.
Owner selection and any later production integration remain tracked under
[RPT-20261021-CRYO](../KNOWN_ISSUES.md#rpt-20261021-cryo--four-way-chamber-comparison).

## Source checks

The recipe snapshots compile with the existing Python interpreter;
`Scripts/CheckProject.py` passes all 45 structural checks,
`Scripts/CheckPrDocumentation.py --repo .` passes and `git diff --check` is clean.
Docker execution remains unavailable because the local daemon is not running;
the added container recipe has not been run. No C++ source changes or full game
rebuild/cook are part of this asset-review check. Native fresh-load rendering is
separate evidence above. Native game playback and owner-copy identity are also
verified above; owner selection and production performance remain unconfirmed.
