# Fitted cryo comparison and native interaction — October 22, 2026

**Current disposition: v4_4 visually verified, installed, owner-built and
compatibility smoke passed.** This supersedes the v3 fit claim, which the owner
rejected after seeing glass/status/HUD surfaces float away from the frame.
[V3 evidence](2026-10-21-cryo-comparison.md) remains historical. PR86 stays open
and unmerged; the active task is [RPT-20261021-CRYO](../KNOWN_ISSUES.md#rpt-20261021-cryo--four-way-chamber-comparison).

The all-angle pass found a third original service console on D's rear. Its
matching backing/glass/HUD/frame treatment is now included within four existing
meshes. The v4_4 metrics below include its additional 54 triangles, with no texture
budget increase; the namespace and 19 components per model stay unchanged.

## Fitted source and shared treatment

All four retain their original body topology, UVs, texture resolution and source
GLB hashes. The same generated artwork, materials, fog, lights and native cycle
apply to each. Each has 19 static components across the same 12 finish roles.
Different frame shapes need different fitted geometry: C has four connected
window sectors, while A/B/D cover their existing front opening.

The v4_2 glass follows measured cap/post regions, with closed metal seats and
upper nozzles. The chamber HUD follows its actual glass surface at 2.5 mm.
Bottom console backing is inset into the existing bezel; glass sits 8 mm above
it, with the transparent generated HUD at 10 mm. This replaces the rejected
4 cm raised console arrangement. Original body geometry remains untouched.

C's rear glass and frost now have a local bulge of up to 30 mm for tail clearance.
The separate v4_3 tail audit records 7.376 mm minimum clearance over 28,596 samples;
only 164 vertices per surface move, with topology and all other components unchanged.
The full-frost material also has a native depth correction. Final native captures
are accepted; the resource figures below match the eight-receipt v4_4 authoring chain.

The fresh v4_4 read-only numerical contact audit retains **23 local seat-clearance flags**
at irregular generated recesses. They have not been relabeled as a numerical pass.
Closed supports bridge them; reviewed illuminated side/oblique views show no
floating added panes or consoles. Dark rear/top views do not resolve every fine
contact. [Static values and audit identity](2026-10-22-cryo-v4-resources.json)
record the exact fitted manifest and private analysis hashes.

## Native action and build evidence

The owned [SSCryoRuntime plugin](../../Plugins/SSCryoRuntime/README.md) supplies
the chamber actor, dynamic frost material ownership, two downward Niagara
nozzles and a four-second world-time cycle. The same final jet recipe also aims
inward to clear the curved glass; the previous jet asset is preserved. Jets remain visible through clear
glass for 0.65 seconds; frost rises to full at 1.25 seconds, holds through 3.4
seconds and resets by four seconds. Repeated use cannot extend a cycle.
Range/visibility checks reject inaccessible uses, and a Pawn-only capsule
provides a simple walking boundary. EndPlay clears the timer and restores
original material assignments. Python does not implement gameplay behavior.

The production bridge adds `CryoChill` to the existing terminal action and uses
the existing keyboard/controller interaction. No production terminal placement
or game map is changed. The separate comparison map has four saved native
chamber bindings and the plugin's walking preview mode. Its observer invokes
the same native controller action as E/X; that is not physical-input testing.

[Native build receipt](2026-10-22-cryo-interaction-build.json): initial plugin
build passes, the full isolated Editor build passes 50 actions in 91.30 seconds,
the collision update passes nine actions in 144.71 seconds, and the jet lead-in
update passes four actions in 7.36 seconds. Current Stage plugin source/DLL
hashes match. Installed MSVC/engine deprecations and the existing HairStrands
dependency warning remain recorded. A stalled parallel editor/build attempt
was retained; subsequent operations are serialized. The
[latest owner-source build](2026-10-22-cryo-owner-build.json) also passes:
134 actions in 89.75 seconds. Its fresh game/plugin DLLs and exact source hashes
are recorded separately. The owner project then passes an uncooked compatibility
smoke: four configured chambers, 217 matching packages, 99 samples, full frost
and bounded jets followed by reset at 4.006 seconds. Config, saves, source and
package hashes remain unchanged, and fog restores. Existing editor-toolset
startup Python errors and other startup warnings are recorded in that receipt;
the native observer itself reports no errors.

[Final native evidence](2026-10-22-cryo-runtime.json) records 408 interaction
samples: four cycles ending in 4.002–4.031 seconds, full frost followed by zero,
stopped jets, repeat/range/occlusion refusal and collision sweeps. The 19 effect
frames include C's frozen side windows. The 36 angle views cover nine directions
per model, with 1,029 ambient samples over 213.16 world seconds and 35 natural
light loops. All four Niagara systems stay active/bounded, eight lights share
phase, and fog restores 1000→10→1000 cm. All 55 frames passed the lead's review.
Frost retains fine granular edges/ramp; C's original front ribs remain visible.

Current capture observers use ordinary `Shot` captures from the actual
960×1200 viewport, with owner-matching TSR in their disposable game process.
This preserves temporal history for dithered frost and does not change the
owner's renderer configuration.

## Latest measured static resources (v4_4)

| Variant | Fitted triangles | Static sections | Model native MiB | Body texture estimate MiB |
| --- | ---: | ---: | ---: | ---: |
| A — Cybernetic Cat | 42,699 | 19 | 18.27 | 42.67 |
| B — Futuristic Cat | 67,046 | 19 | 30.67 | 74.67 |
| C — Futuristic Fox | 117,389 | 19 | 22.00 | 42.67 |
| D — Meshy Raccoon | 121,150 | 19 | 88.26 | 74.67 |

Shared full-mip texture estimate is 10.67 MiB once. All four bodies plus shared
art estimate 245.33 MiB. These standard BC estimates exclude buffers, shaders,
fog grids, render targets, overdraw and actual streaming residency. Native file
size is uncooked storage, not load time or VRAM; sections are not measured draw
calls. The stage now stores 200 uassets, of which 82 are known retained recovery,
plus the comparison map. No recovery content is deleted.

A remains the lowest static budget; D retains the highest-detail body candidate.
C's four-sided enclosure brings its geometry close to D while retaining A's
lower texture tier. The accepted review favors D for hero detail and A for
efficiency; owner preference remains open. Packaged load time, FPS, GPU time and resident VRAM
remain unmeasured.

## Preservation, adoption and source checks

The original four GLBs and six generated source-image hashes were rechecked.
Native assets, private vendor dependencies, pictures and editable source stay
local; non-Unreal work remains on D:. Source-only recipes and plugin code are
reviewable in Git. The namespace stays ignored and excluded from cooking.

[Guarded adoption](2026-10-22-cryo-adoption.json) installed and hash-verified
201 packages / 182,257,046 bytes: 76 new
packages, a map-only replacement and 124 unchanged prior packages. It also
installed seven narrow owner-source changes and 11 owned plugin files after
matching accepted evidence and idle native processes. Exact overwritten bytes
are backed up on D:. All 16 donor and 106 source/import hashes remain unchanged.
The owner's latest source was built separately; no isolated game DLL was copied.

There are 42 Python recipe snapshots, including 21 current v4 tools and 21
retained prerequisites/history. Their hashes are in the [snapshot manifest](../../Scripts/CryoComparison/recipe-snapshots.json).
The [bundle README](../../Scripts/CryoComparison/README.md) gives their execution
layout and guards. Current static checks cover syntax, source structure,
formatting, documentation and links, independently of the native evidence.
The comparison report passes 72 link checks; its latest browser layout was not
visually rechecked because local file navigation was blocked. Owner compatibility
smoke passes; physical keys and production game-mode use remain untested. No package, merge or production-map placement is claimed.
