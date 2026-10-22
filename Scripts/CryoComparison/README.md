# Four-way cryogenic chamber comparison

Owner-requested asset finishing and comparison, dated October 21, 2026. All four
source chambers receive the same screen artwork, material recipe, glass, frost,
hologram and native Unreal effects before any quality ranking. This is a separate
authoring scene; it does not replace a gameplay map or the playable Acornaut.

Current verification and remaining work belong to
[RPT-20261021-CRYO](../../docs/KNOWN_ISSUES.md#rpt-20261021-cryo--four-way-chamber-comparison).
The [dated receipt](../../docs/validation/2026-10-21-cryo-comparison.md) separates
source preparation, saved native content, rendered verification and performance.

## Inputs and private storage

The four untouched originals are in the owner's `Downloads/CRYO` folder.
[source-provenance.json](source-provenance.json) records filenames, full SHA-256
hashes and source GLB resource counts. A source filename is a comparison label,
not proof of character identity or output quality.

| ID | Source filename | Source triangles | Source body textures |
| --- | --- | ---: | --- |
| A | `cybernetic cat 3d model.glb` | 25,491 | Three 4K maps |
| B | `futuristic cat 3d model.glb` | 49,838 | 8K base color; two 4K maps |
| C | `futuristic fox 3d model_Clone1.glb` | 51,101 | Three 4K maps |
| D | `Meshy_AI_Cybernetic_Raccoon_Ch_1021225808_texture.glb` | 103,888 | 8K base color; two 4K maps |

Each source is one opaque body mesh/material with three embedded PBR maps, no
separate glass or screen surface, and no skin or animation. The finish adds
separate components rather than changing source topology or painting over the
original texture bytes. Source texture resolutions are retained for comparison.

Non-Unreal revisions, editable Blender files, finished GLBs, source textures,
generated artwork, manifests and captures live physically on
`D:/Codex/CryoComparison_20261021`. The task's `work` and `outputs/Cryo_Comparison`
paths on C: are junctions into that D: tree. They are not second copies. Do not
recursively delete or move through the junctions. Original downloads stay intact.

All four variants are now copied into the owner project at the private native
destination
`/Game/SpaceSurvival/CryoComparison/Maps/L_CryoComparison`. Its content directory
is ignored by Git; a clone does not recreate these native assets. The exact
`DirectoriesToNeverCook` entry excludes this review namespace from the project's
broad `/Game/SpaceSurvival` cook root. Removing that exclusion is a separate
integration decision, with dependency and performance checks. Do not force-add
the native directory or the owned `NiagaraExamples` pack to Git.
[Adoption receipt](../../docs/validation/2026-10-21-cryo-adoption.json) verifies
125 copied files/178,288,150 bytes after the two-material Niagara usage repair,
16 unchanged donor hashes and 106 preserved source/import hashes. All 125 files
match the accepted native game run. The owner project itself was not launched.

## Equal treatment

All chambers are normalized to 320 cm height and grounded. A is rotated to align
its opening; the other sources already face forward. Fitted glass dimensions and
screen positions vary only to meet each source's existing shape. All four have
the same finish roles and counts:

| Component role | Count per chamber | Shared treatment |
| --- | ---: | --- |
| Original body | 1 | Original PBR maps/factors, metallic multiplier 0.7, roughness floor 0.25 |
| Console hologram | 2 | Shared generated transparent HUD art with a 5.5-second native scan |
| Console glass | 2 | Raised 4 cm above the original screen, with HUD at 4.25 cm |
| Console backing | 2 | Dark backing covers the original garbled display |
| Console support frame | 2 | Narrow raised frame supports each glass display |
| Glass enclosure | 1 | Curved transparent front with the same Fresnel material |
| Edge frost | 1 | The same generated transparent crystal-rim texture/material |
| Holographic display | 1 | The same generated text art with Unreal scan/pulse animation |
| Status screen | 1 | The same portrait status image |
| Status housing | 1 | Supported graphite housing |
| Supplemental mist card | 4 | Shared low-opacity moving material |
| Cyan trim | 1 | Shared emissive material |

This is 19 components across 12 roles per chamber. Each adds exactly 6,610
triangles to its original body. The comparison uses the same camera framing,
lighting, exposure and native effect
settings for each bay. Unreal adds one local fog volume and one Niagara system
actor per chamber, plus shared exponential volumetric fog. The mist cards
supplement these effects; they are not the only freeze/fog treatment. Native
effects cannot be carried inside a GLB or established by a Blender render.

Two shadowless cyan lights per chamber share a six-second native Level Sequence:
interior intensity 5–12 lumens and rim intensity 4–10 lumens. The accepted native
game run recorded 66 samples over 14.124 world seconds, two natural loop wraps,
matching light phase across all four and four active bounded Niagara systems.
The fog distance restored from 1000 to 10 to 1000 cm across BeginPlay/EndPlay.
[Runtime receipt](../../docs/validation/2026-10-21-cryo-runtime.json) separates
these checks from the lead's visual review. This is presentation animation,
with no gameplay dependency or packaged performance claim.

The hologram is **authored display art animated by an Unreal material**. Its
temperature, pressure and status copy are presentation values, not live game
telemetry, an interactive control panel or a new cryogenic gameplay mechanic.
The chamber parts currently have no collision; the review floor alone blocks.

## Pipeline and safeguards

The local workflow inventories and hashes the four GLBs, creates shared
images through image generation, derives fitted components in Blender, imports
explicit centimeter OBJ geometry into an isolated native Unreal project, then
checks a fresh native load and real renderer output. Generated artwork prompts
and exact native dependency-copy hashes are retained with the private receipt.
[art-provenance.json](art-provenance.json) records the six source image hashes,
dimensions and generation instructions; the console-hologram edit record is
explicitly a summary of its instruction rather than a verbatim prompt.

Unreal authoring uses installed UE 5.8.4 and editor scripting. A full offscreen
Editor is required for `StaticMeshEditorSubsystem`; a commandlet-only run does
not provide that subsystem. Agent launches must use `-RenderOffscreen` or
`-NullRHI`, and captures must be serialized. A NullRHI asset-load pass does not
prove visible fog, Niagara motion or hologram animation.

The smoke source is the owner's existing
`/Game/NiagaraExamples/FX_Smoke/NS_Smoke_Plume`. A private duplicate supplies the
chamber effect; a new bounded material uses the generated mist image, replacing
the donor renderer's atlas/cutout. Original vendor assets remain unchanged. Only
the initial dependency closure is copied into the isolated stage. Live reflected parameters are
`SpawnRate`, `Sprite Size` and `Smoke Color` with their native types; guessed
`User.` names or a claimed parameter that is not exposed are not interchangeable.

The Unreal authoring entry point defaults to dry-run, requires all four models
and matching role counts, hashes source files, refuses an existing output
namespace, and only applies inside the dedicated `CryoStage` project. Scripts
are task-specific recipes, not a command to regenerate adopted owner content.
Keep their recorded work/output layout and inspect guards before any later use.
Existing source inputs and saved owner work must never be overwritten to make a
rerun pass. Saved content must be reloaded and viewed before a finish claim.

Unreal texture build sizing/mips can resample the generated PNGs for streaming;
the original image-generation pixels remain preserved as source. Source body
resolution, collision policy, LOD/Nanite choices and translucency costs must be
reported separately from any perceived quality ranking.

Status, chamber hologram and console-hologram textures use sharpened mips and
`NeverStream` in the final review for readable text. That is an explicit shared
residency choice; the three source body maps retain ordinary streaming settings.
Original opaque-console packages remain as recovery and are excluded from active
mesh/texture accounting. [Resource receipt](../../docs/validation/2026-10-21-cryo-resources.json)
labels native disk size and GPU-memory estimates separately.

## Archived recipes and execution layout

The Python files here are snapshots of the actual task recipes. Their hashes are
recorded in [recipe-snapshots.json](recipe-snapshots.json). They are not a
one-click installer. They expect this private layout after being copied into a
new D: review workspace, alongside the required original inputs and artwork:

```text
<review workspace>/
  work/
    *.py                         # recipe snapshots copied here
    glb-baseline.json             # inventory receipt
    CryoStage/CryoStage.uproject  # isolated native project and dependency copy
    *.json                       # per-step authoring/verification receipts
  outputs/Cryo_Comparison/
    shared/                      # original generated artwork
    assembly.json                # base finish manifest
    assembly_holo_consoles.json   # raised transparent-console manifest
    <model>/                     # model source maps, components and revisions
```

Copy [stage-template](stage-template/CryoStage.uproject) into `work/CryoStage`
when preparing a new isolated project. It enables the installed Python,
editor-scripting, Niagara and Sequencer services used by the recipes. The
template intentionally omits the task stage's temporary global near-fog preview
override; the native sequence track is responsible for restoring that value
after playback, as verified in the native game run. It does not enable plugins or
change renderer configuration in the owner project.

Do not execute them from `Scripts/CryoComparison`: `__file__` determines the work
directory and native stage guard. Original-download and owner Niagara-source
paths are intentionally machine-specific. A Git clone alone lacks the private
inputs, native stage and generated image files. Never repoint these recipes at
the owner's adopted content to work around a failed guard.

| Recipe | Role and execution boundary |
| --- | --- |
| `inventory_glbs.py` | Stdlib source reader; writes only its adjacent inventory JSON |
| `finish_cryo_blender.py` | Blender base-finish recipe; writes/replaces derived outputs and previews, so use only a new review destination |
| `probe_niagara.py`, `copy_niagara_dependencies.py` | Native capability probe and new-only hash-verified local dependency copy |
| `author_cryo_unreal.py` | Base native authoring; dry-run by default, explicit apply in a new isolated stage |
| `refine_cryo_native.py`, `tune_cryo_unreal.py`, `polish_cryo_unreal.py` | Ordered historical corrections to the owned base stage; execute immediately when loaded inside Unreal and then quit that editor |
| `upgrade_console_geometry.py`, `upgrade_console_unreal.py` | New-only raised glass/HUD geometry, followed by native import and replacement of eight superseded console actors |
| `add_cryo_breathing_lights.py` | Dry-run by default; explicit apply creates the shared eight-track native light loop |
| `refine_display_sampling.py` | Owned-stage display residency/detail-camera correction; executes immediately inside Unreal |
| `add_cryo_fog_preview_track.py` | Adds the restoring sequence CVar track in the isolated stage; native game playback/restoration verified |
| `compose_final_receipt.py` | Aggregates native/source identities; it does not compile materials or establish renderer success |
| `verify_cryo_final.py`, `verify_cryo_runtime.py` | Fresh real-renderer/editor and attempted Simulate/Play checks; Simulate lacked a usable viewport on this host, so use the separate actual-game evidence |
| `verify_cryo_game.py` | Observes actual native BeginPlay, loops, active Niagara and EndPlay restoration without calling sequence play/seek or saving assets; captures three review views |
| `fix_cryo_niagara_usage.py` | Isolated-stage correction for the rejected checkerboard render: enables NiagaraSprites usage on the owned master and saves its instance |
| `measure_cryo_costs.py` | Read-only static geometry/disk/texture analysis using existing Pillow; no engine launch or benchmark |
| `adopt_cryo_native.py` | Explicit new-namespace copy to the owner project after dry-run, with content/donor/source hashes and backups before exact ignore/never-cook text edits; refuses an existing destination, so do not rerun after adoption |
| `adopt_cryo_usage_fix.py` | One-time two-material follow-up; verifies every adopted hash and creates exclusive backups before copying; executes immediately and must not be rerun after adoption |
| `finalize_cryo_runtime_receipt.py` | Verifies accepted game captures/package hashes against delivered owner files, then writes a concise private receipt; it does not run the engine |

The correction recipes record the completed session's intermediate states. Some
are deliberately non-repeatable after later revisions. Review the receipt and
current stage before reuse; do not run the table blindly in the owner project.
The accepted native-game receipt supersedes the inactive-Niagara editor capture
and rejected checkerboard runtime trial. Do not treat either earlier pass as
proof of the final particles.

## Portable checks

The existing root containers cover C++ tests and formatting. The small
[Dockerfile](Dockerfile) adds Python syntax and documentation checks for this
bundle without installing host packages. From the repository root:

```powershell
docker build -f Scripts/CryoComparison/Dockerfile -t spacesurvival-cryo-check .
docker run --rm spacesurvival-cryo-check
```

The Docker daemon was unavailable during preparation. Equivalent source checks
use the already installed Python runtime:

```powershell
python -m compileall -q Scripts/CryoComparison
python Scripts/CheckPrDocumentation.py --repo .
```

Neither path imports assets or validates Unreal, GPU performance, a cooked
package, appearance or owner preference. Runtime load risk must distinguish
source download size, native package size, texture residency, mesh/material
counts and translucent overdraw. Editor capture timing is not a 60 FPS benchmark.
