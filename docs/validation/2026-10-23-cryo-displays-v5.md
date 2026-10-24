# Cryo display/glass correction — October 23, 2026

**V5.4 is reviewed in native Unreal, installed locally and passes owner compatibility.**

All four share real font-mesh lettering/vector instruments behind separate glass
lenses, a compact curved chamber hologram and revised cold-glass shading. Original
bodies/textures, fitted enclosures, C tail clearance, generated frost/mist, native
Niagara, four-second freeze and breathing-light sequence remain protected.
Display copy is authored presentation, not live telemetry.

The independent source audit passes with zero errors and 301 protected files
unchanged. B/C displays cover the original console art; D status clears its rail
on a supported pad. All nine bottom consoles were reviewed in closeup. The lead
accepted 53 ordinary 960×1200 views and 19 freeze frames. Native observation
records 1,510 ambient samples/52 light loops and 370 interaction samples; all four
cycles frost fully and reset in 4.003–4.039 seconds, with repeat/range/visibility
guards and package/source preservation. [Exact receipt](2026-10-23-cryo-displays-v5.json).

| Candidate | Triangles | Components | Body texture estimate MiB | Active model native MiB |
| --- | ---: | ---: | ---: | ---: |
| A | 68,407 | 21 | 42.67 | 19.13 |
| B | 95,143 | 21 | 74.67 | 31.54 |
| C | 145,724 | 21 | 42.67 | 22.89 |
| D | 154,211 | 21 | 74.67 | 89.29 |

D leads for hero detail, A has the smallest static budget, and C provides the
clearest view around all sides. B's softer body detail retains the higher 8K
texture tier. Active model disk bytes include meshes, body textures/material;
shared effects/materials are separate. Shared frost/mist BC3 full-mip estimate is
4.000061 MiB once; all body sets plus those maps total 238.666931 MiB. These are
static estimates, not measured residency, load time or frame time.

Guarded content-only adoption adds 55 packages (49 meshes/six materials), replaces
only the comparison map and preserves prior packages. The 256 cryo packages total
187,100,078 bytes including recovery content. Fresh owner smoke verifies the
272-package closure and four configured chambers; one native cycle reaches full
frost/jets and resets in 4.032 seconds across 94 samples. Protected config, saves,
source and package hashes remain unchanged and fog restores. The process exits0;
observer errors are empty. Known EditorToolset/ToolsetRegistry startup errors for
unavailable AgentSkill/PythonTestRunner under `-game` match the earlier baseline
and are recorded separately. V5 changes no runtime C++; prior build proof is history.

Acceptance has limits: A/D show some faceted dark seating rims at extreme close
range, frost retains fine grain, C's original posts obscure the hero, and the
black environment limits central glass reflections. Dark top/rear images do not
resolve every fine contact. Physical input, owner preference, production placement
and packaged performance remain unverified. The canonical local report provides
all 72 actual-image dropdown views; the previous report is archived with matching
hashes. Private native/art/font/vendor files stay local and non-Unreal work stays
on D:. The review namespace remains excluded from cook; PR86 is unmerged.

[Recipes and guards](../../Scripts/CryoComparison/README.md#current-v5-recipes),
[v4 history](2026-10-22-cryo-fit-interaction.md),
[active owner review](../KNOWN_ISSUES.md#rpt-20261021-cryo--four-way-chamber-comparison).
