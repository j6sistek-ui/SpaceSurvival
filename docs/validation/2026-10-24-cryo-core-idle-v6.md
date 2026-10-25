# Cryo forward-core and steady-nozzle polish — October 24, 2026

**V6 is reviewed in native Unreal, adopted locally and passes fresh owner smoke.**

All four lower-front blue cores now sit ahead of their chamber rim, with the
existing collars remaining supported. Two small white-cyan streams run downward
and inward from each roof, separate from the stronger four-second freeze burst.
The accepted displays, glass, frost, ambient fog and breathing lights remain.
Four active Body meshes change locally; original downloads/body exports/native
packages, topology, UVs and the other 80 component exports remain preserved.

Independent source audit passes 329 protected files/zero errors. Offsets are
A 7 / B 5.5 / C 4 / D 9.9 cm, fitted to each frame. Native OBJ normals outside the
collar are exact. Blender re-encoding affects four pre-existing zero-area C
corners (unit to zero normal); other differences are at most about 0.076°.
Twelve CPU fit previews were reviewed separately from native acceptance.

The lead reviewed 48 ordinary 960×1200 views and 19 freeze frames. The eight steady
jets remain active across 1,224 samples/260.166 world seconds, with 43 natural light
loops. Four native cycles across 381 samples frost fully and reset in 4.018–4.044 s;
repeat/range/visibility/other-bay guards and package/source preservation pass.
[Exact receipt](2026-10-24-cryo-core-idle-v6.json).

| Candidate | Triangles | Components | Body texture estimate MiB | Active model native MiB |
| --- | ---: | ---: | ---: | ---: |
| A | 68,407 | 21 | 42.67 | 19.13 |
| B | 95,143 | 21 | 74.67 | 31.54 |
| C | 145,724 | 21 | 42.67 | 22.89 |
| D | 154,211 | 21 | 74.67 | 89.30 |

D leads hero detail, A has the smallest static budget and C offers four-sided
viewing. Body/shared texture estimates are unchanged: shared frost/mist 4.000061 MiB
once, all body sets plus those maps 238.666931 MiB. Eight CPU emitters at 10 particles/s
with 0.95 s lifetime imply about 76 steady-state particles, not a measured cap.
The extra particles add simulation/overdraw work; unchanged triangles do not prove
unchanged runtime cost. Model disk sizes include meshes/body textures/material,
while shared effects are separate. None is a load-time, FPS or VRAM benchmark.

Guarded content adoption adds five packages and replaces only the comparison map;
261 cryo packages total 197,146,816 bytes including recovery (277 with donors).
Fresh owner smoke verifies all identities, eight steady jets and a complete native
cycle resetting in 4.032643 s across 91 samples. Protected config/saves/source/assets
remain unchanged; fog restores. All three native verification processes exit 0.
Known EditorToolset startup errors remain separate from zero observer errors.
V6 changes no runtime C++; earlier source builds remain historical proof.

The first 48-view run stays failed history because three initial samples preceded
uncooked Niagara readiness. Final observers record a separate bounded natural
startup before continuity/action, without activation calls or later-inactivity
exemptions. This readiness wait is not a packaged load measurement.

Limits remain: source faceting and fine frost grain, C rails/outlet frost partly
obscuring the right stream or subject, dark rear/top contacts and limited central
glass reflections. Exact side views can hide a front-facing core behind neighboring
consoles; the rim correction does not make solid geometry transparent. Owner
preference, physical input, production placement and packaged performance remain
unverified. The local report contains 67 current views, starting with full front
views; prior reports and failed evidence are preserved. Native/vendor/art remains
private and excluded from cook; non-Unreal work stays on D:. PR86 is unmerged.

[Recipes and guards](../../Scripts/CryoComparison/README.md#current-v6-recipes),
[accepted v5 history](2026-10-23-cryo-displays-v5.md),
[active review](../KNOWN_ISSUES.md#rpt-20261021-cryo--four-way-chamber-comparison).
