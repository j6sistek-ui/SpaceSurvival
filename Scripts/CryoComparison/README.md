# Four-way cryogenic chamber comparison

**Current revision: v6 is reviewed in native Unreal and installed locally.**
All four use matching readable displays behind glass, frost/fog and native
four-second freeze. V6 moves each lower blue core and its supported collar clear
of the chamber rim, and adds two small steady downward nozzle streams per bay.
Four derived Body meshes change locally; original files, topology/UVs, accepted
displays/enclosures and the other 80 component exports remain preserved.

Lead review covers 48 current views and 19 effect frames. Eight steady jets stay
active through 1,224 samples; four stronger freeze cycles reset in 4.018–4.044 s.
Guarded adoption adds five packages/map-only replacement. Fresh owner smoke passes
277 identities/261 cryo packages, the idle jets and a complete freeze/reset.

D leads hero detail, A has the smallest static budget and C offers four-sided
viewing. Source faceting, frost grain, C posts/outlet occlusion, dark contacts and
limited central reflections remain. Exact side views can hide a front-facing
core behind another part. Owner preference, physical input and packaged performance
stay separate; PR86 remains unmerged. [Current evidence](../../docs/validation/2026-10-24-cryo-core-idle-v6.md),
[v5 history](../../docs/validation/2026-10-23-cryo-displays-v5.md),
[active review](../../docs/KNOWN_ISSUES.md#rpt-20261021-cryo--four-way-chamber-comparison).

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

All four current variants are installed in the owner project at the private native
destination
`/Game/SpaceSurvival/CryoComparison/Maps/L_CryoComparison`. Its content directory
is ignored by Git; a clone does not recreate these native assets. The exact
`DirectoriesToNeverCook` entry excludes this review namespace from the project's
broad `/Game/SpaceSurvival` cook root. Removing that exclusion is a separate
integration decision, with dependency and performance checks. Do not force-add
the native directory or the owned `NiagaraExamples` pack to Git.
[Historical v4 adoption receipt](../../docs/validation/2026-10-22-cryo-adoption.json)
verifies 201 files/182,257,046 bytes: 76 additions, one map replacement and 124
preserved packages. Seven narrow source edits and 11 owned plugin files were
installed with exact D: backups; 16 donor and 106 source/import hashes remain
unchanged. Those v4 files matched their accepted stage; current v5 adoption adds the
display packages and replaces only the map. The prior
[v3 receipt](../../docs/validation/2026-10-21-cryo-adoption.json) is historical.
The latest owner-source build and uncooked compatibility smoke pass; physical
input and packaged performance remain untested.

## Preserved v4 fit and interaction baseline

The v4 baseline has the same 19 component roles, shared art, material/effect recipe
and original bodies. Glass follows measured posts and caps; C has four connected
window sectors. Closed seats support the panes, while the chamber HUD follows
the glass at 2.5 mm. Console glass and transparent HUD sit 8 mm and 10 mm above
their inset backing, replacing the rejected 4 cm raised slab. Shape-specific
supports make the added triangle counts differ; equal treatment does not mean
identical geometry around different source frames.

The native plugin starts two local-space downward Niagara jets, delays frost
until 0.65 seconds, reaches full frost at 1.25 seconds and restores normal by
four seconds. A Pawn-only capsule supplies walking collision. Native saved
references bind every frost surface and the two inner top outlets; Python is
used to author and observe, while C++ owns gameplay timing and material state.
[V4 runtime baseline](../../docs/validation/2026-10-22-cryo-runtime.json)
records 408 interaction samples and four cycles ending in 4.002–4.031 seconds,
plus 1,029 ambient samples across the all-angle review. Every pane restores its
normal state and each bay's other three chambers remain unchanged.

[V4 static metrics](../../docs/validation/2026-10-22-cryo-v4-resources.json)
record 42,699 / 67,046 / 117,389 / 121,150 triangles and 19 sections per model.
C's four-sided glass and supporting rails explain its increased geometry.
The numerical fit audit retains 23 local seating-span flags at source recesses.
Closed supports bridge them; illuminated native side/oblique views show no
floating added panes or consoles. Dark top/rear views do not resolve every
fine contact. Frost retains a granular edge and ramp, and C's original front
ribs still obscure parts of the character.

## V3 treatment baseline — fit rejected

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
The v3 chamber parts had no collision; the current plugin adds a simple walking
boundary without changing the original mesh collision settings.

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

Historical raster status, chamber hologram and console-hologram textures used
sharpened mips and `NeverStream` for text. Current v5 uses mesh glyphs and retains
those image packages only as recovery. The three source body maps retain
ordinary streaming settings.
Original opaque-console packages remain as recovery and are excluded from active
mesh/texture accounting. [Resource receipt](../../docs/validation/2026-10-21-cryo-resources.json)
labels native disk size and GPU-memory estimates separately.

## Archived recipes and execution layout

The Python files include current v5 recipes and retained v4/v3 prerequisites/history.
Their exact roles and hashes are recorded in [recipe-snapshots.json](recipe-snapshots.json).
Snapshot `sha256` and `bytes` describe LF-normalized Git content so they remain
portable across Windows checkouts. A `private_source` record preserves the raw
byte count and hash when the tested private recipe used CRLF. Only line endings
are normalized; tested private files and native evidence remain unchanged.
They are not a one-click installer. They expect this private layout after being copied into a
new D: review workspace, alongside the required original inputs and artwork:

```text
<review workspace>/
  work/
    *.py                         # recipe snapshots copied here
    glb-baseline.json             # inventory receipt
    CryoStage/CryoStage.uproject  # isolated native project and dependency copy
    cryo-repo/                  # isolated source checkout and private build guards
    cryo-owner-runtime-source-plan.json # fresh owner-byte patch plan, kept private
    console-bezel-projection-v5_4.json # private measured source-display planes
    *.json                       # per-step authoring/verification receipts
  outputs/Cryo_Comparison/
    shared/                      # original generated artwork
    assembly.json                # base finish manifest
    assembly_holo_consoles.json   # raised transparent-console manifest
    assembly_fit_v4_2.json        # fitted contact-audit baseline
    assembly_fit_v4_3.json        # C rear tail-clearance revision
    assembly_fit_v4_4.json        # historical fit including D rear console
    assembly_displays_v5_4.json   # current vector-display source assembly
    <model>/                     # model source maps, components and revisions
```

Copy [stage-template](stage-template/CryoStage.uproject) into `work/CryoStage`
when preparing a new isolated project. It enables the installed Python,
editor-scripting, Niagara and Sequencer services used by the recipes. The
template intentionally omits the task stage's temporary global near-fog preview
override; the native sequence track is responsible for restoring that value
after playback, as verified in the native game run. It does not enable plugins or
change renderer configuration in the owner project.

The interactive revision also needs the owned `Plugins/SSCryoRuntime` source
built with the installed Unreal toolchain and copied into the stage's Plugins
directory. Its native classes supply the chamber and walking preview; binaries
are local build output. `CascadeToNiagaraConverter` is an installed editor-only
authoring dependency for the jet recipe, not a runtime Python dependency.

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

The retained v4 revision uses these source snapshots. Its separate native
receipts describe that earlier fit and behavior; they do not certify v5 visuals.

| Retained v4 recipe | Role and execution boundary |
| --- | --- |
| `fit_cryo_geometry_v4.py`, `validate_cryo_fit_v4.py`, `render_fit_v4.py` | Separate Blender v4_2 geometry, preservation/contact audit and nine-angle previews; never substitute Blender views for Unreal acceptance |
| `upgrade_cryo_fit_unreal.py` | Dry-run by default; imports 72 new fitted meshes and updates only the isolated comparison map |
| `fit_cryo_C_tail_v4_3.py`, `apply_cryo_tail_fit.py` | Derive C rear glass/frost tail clearance without changing topology, then hash-guarded replacement of those two owned stage mesh packages |
| `diagnose_cryo_C_rear.py` | Read-only reload of C's saved source to verify rear-tail clearance independently of the authoring process |
| `finish_cryo_D_rear_console_v4_4.py`, `render_cryo_D_rear_console_v4_4.py`, `apply_cryo_rear_console.py` | Same display treatment on D's third service console, source previews and exact four-mesh stage update; no new components or packages |
| `author_cryo_freeze_fx.py` | Dry-run by default; creates owned frost material and local-space downward Niagara jet using installed editor converter services |
| `refine_cryo_frost_masked.py` | Guarded stage-only frost depth correction; saves the owned frost master while preserving the remaining packages |
| `refine_cryo_jet_containment.py` | New shared inward/downward jet and map-only binding update; preserves the prior jet, nozzle origins, materials and four-second timing |
| `balance_cryo_360_lighting.py`, `bind_cryo_interaction.py` | Guarded map-only rear fill and four native chamber bindings; explicit apply in the isolated stage |
| `verify_cryo_interaction.py` | Actual-game observer calls the same native controller action as E/X, then observes timers, materials, jets, access and collision; no material setters or manual actor ticks |
| `verify_cryo_fit_angles.py` | Actual-game nine-angle capture per bay with natural effects/light playback and package/source preservation |
| `verify_cryo_owner_smoke.py` | Read-only owner-project compatibility observer after adoption/build; verifies installed hashes and one native cycle without physical key input |
| `measure_cryo_costs.py` | Updated read-only active/recovery accounting against exact fitted manifest and authoring receipts |
| `build_cryo_evaluation_v4.py` | Creates private HTML/JSON comparison only from explicit matching capture, visual review, metrics and adoption receipts; omitted evidence stays pending |
| `adopt_cryo_v4.py` | Dry-run default; requires accepted exact native evidence, all 125 old owner hashes, 76 new packages including the exact contained jet, map-only replacement, seven fresh source hashes and 11 verified plugin files; D: backups precede any write |

The adopter needs private source proposals and the verified plugin build/copy
manifest under `work/cryo-repo/.agent/local/CryoInteraction`. These are not
portable patches for a different owner checkout. It refuses an existing owner
plugin folder, changed source, unknown native files or running Unreal/UBT.
After apply, build the owner's latest source separately; never copy the isolated
SpaceSurvival DLL into that differently edited checkout. Native binaries, guard
inputs, owner patch contents and screenshots are intentionally absent from Git.

## Current v6 recipes

V6 is the current installed correction to the accepted v5.4 baseline. Four
Body derivatives move only the local core/collar; topology/UVs and original
source files stay preserved. The steady effect adds one shared native
system and eight nozzle actors without changing the larger freeze interaction.
[Current evidence](../../docs/validation/2026-10-24-cryo-core-idle-v6.md).

| Recipe | Boundary |
| --- | --- |
| `snapshot_cryo_v6.py` | New-only baseline of matching owner/stage v5.4 packages and protected inputs |
| `plan_cryo_cores_v6.py`, `raise_cryo_cores_v6.py`, `audit_cryo_cores_v6.py` | Source clearance plan, separate body derivatives and independent audit; retain private `work/cryo-core-v6-plan.json` and do not regenerate it over accepted evidence |
| `apply_cryo_core_v6.py`, `add_cryo_idle_jets_v6.py` | Dry-run-first, serialized stage-only core and steady-jet authoring; only owned map changes among existing packages |
| `compose_cryo_polish_v6.py` | Binds exact core→jet receipts and combined active-mesh identities; no native edits |
| `verify_cryo_polish_v6.py`, `run_polish_v6_angles.py` |48 current native views; wrapper reviews new core/jet close-ups before established angles |
| `verify_cryo_interaction_v6.py`, `verify_cryo_owner_smoke_v6.py` | Native action/reset and fresh owner compatibility observers, no effect setters |
| `adopt_cryo_polish_v6.py` | Default dry run; exact accepted capture/package hashes, process guard, unique D: backups/receipts; only new PolishV6 meshes/FX and map replacement allowed |
| `build_cryo_evaluation_v6.py` | Separate pending report by default; exact source/native/visual/adoption/smoke gates before explicit canonical publication with prior-report archive |

The source manifest is `assembly_polish_v6.json`; audit/plan hashes are recorded
in the concise evidence. Native receipts are `CryoPolishV6Baseline.json`,
`CryoPolishV6Apply.json`, `CryoPolishV6Angles_*` and `CryoInteractionV6_*`.
Never inherit current visual acceptance from the earlier v5 captures.
Observers separate bounded natural Niagara startup from continuity sampling and
the first native action. They do not activate effects or excuse later inactivity;
that startup interval is not a packaged load-time measurement.

<a id="current-v5-recipes"></a>

## Retained v5 recipes

These retained snapshots require the same D: work/output layout above. No native
binary, screenshot, font file or private artwork is published with the scripts.
`build_cryo_displays_v5.py` uses the existing local Bahnschrift font; the recipe
records its identity without copying the font into Git.

| Recipe | Boundary |
| --- | --- |
| `build_cryo_displays_v5.py`, `clean_cryo_vector_caps_v5_3.py` | Ordered Blender derivatives v4.4 → v5.2 → v5.3; older geometry stays preserved |
| `render_console_bezel_probe_v5_4.py`, `fit_cryo_displays_v5_4.py` | New-only source-display previews/projection measurements, then fitted B/C console stacks and D status support; requires the private projection JSON in `work` |
| `validate_cryo_displays_v5.py` | Independent read-only geometry/provenance audit; no native acceptance |
| `apply_cryo_displays_v5.py`, `refine_cryo_displays_v5.py` | Explicit isolated-stage import/refinement, protected native hashes and archived prior receipts |
| `patch_cryo_displays_v5_4.py` | Dry-run-first bounded stage patch: 18 existing v5 meshes, one new D housing mesh and its map binding; archives and hash-binds the prior apply receipt |
| `verify_cryo_displays_v5.py`, `verify_cryo_interaction_v5.py` | Native observers: trial/final 53 views and four freeze cycles/19 frames; no gameplay setters |
| `run_display_v5_owner_smoke.py` | Exact-session wrapper binds the retained read-only owner-smoke observer to the final v5 interaction receipt; invokes the native action without effect setters |
| `snapshot_cryo_v5.py` | Protected input snapshot for the bounded revision |
| `adopt_cryo_displays_v5.py` | Dry-run-first content-only owner copy after exact native/visual evidence; refuses unexpected changes |
| `build_cryo_evaluation_v5.py` | Static cost/report builder with actual native-image dropdowns; separate pending output by default, explicit publish requires exact accepted/adopted/smoke evidence and archives the prior report |

The accepted v5 source manifest was `assembly_displays_v5_4.json`; its independent
audit and private bezel-projection hashes are bound in the concise evidence.
That v5 checkpoint added 55 packages plus the comparison-map update
(256 cryo packages; 272 including donors). Its guarded adoption and fresh
uncooked compatibility smoke passed for those historical identities. Native receipts
are `CryoDisplayV5Apply.json`, final `CryoDisplayV5Angles_*` and
`CryoInteractionV5_*`; none of these earlier captures certifies the v6 core/jet change.

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
