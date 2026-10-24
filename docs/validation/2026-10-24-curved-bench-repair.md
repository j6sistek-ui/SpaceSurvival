# Curved bench source repair — October 24, 2026 UTC

**Result: repaired source delivered; Unreal integration not performed.** Owner
requested “fix the bench, stay out unreal,” after inspection of the supplied
curved-sofa GLB. The light-VRAM boundary remains in force. This work used hidden
Blender 5.2.2 processes with Cycles CPU rendering and six threads. No Unreal
invocation, native asset edit, game build or package was made.

## Source and delivery

Input: `C:/Users/j6sis/Downloads/futuristic+curved+sofa+3d+model (1).glb`.
Its unchanged SHA256 is
`5bc9af8b78567772dfcd7bf99e708f4ad2315e4345823ac5f9f6feddfbdd28d4`.
Initial inspection found warped rails/supports, smeared rear materials and
normalized rather than seating scale. The original has 6,199 triangles and three
embedded 4K maps; welding its disconnected seams leaves 517 boundary edges.

Private delivery on C:
`SourceAssets/CurvedBench_20261024/`.

| File | SHA256 | Bytes |
| --- | --- | ---: |
| `CurvedBench_Repaired.blend` | `4ff1fc7d0c0e7bc75c27d30536405e6162b19206d53ee90bcf84cb29b3b5f106` | 11,785,002 |
| `CurvedBench_Repaired.glb` | `da94e1b338aeb20cf0460a71b3662432d63fd5eb61257b3b586d4647feedd686` | 1,215,732 |

The repair reconstructs the measured 107-degree crescent into 43 named, editable
parts: seat, cushions, structural shell, rails, arms and six feet. It preserves
black/violet/titanium styling with seven portable PBR materials; the old smeared
atlas is not reused on the rebuilt surfaces. The original mesh/material and all
three packed images remain in a hidden Blender reference collection. Only the
repair exports to GLB. This is not a topology-preserving cleanup.

Seat height is approximately 45 cm. Evaluated dimensions are
3.661764 × 3.607207 × 0.933120 m; the soles reach Z=0. The export has 41,978
triangles, more than the flawed source. Its smaller file and texture-free PBR
materials do not establish a runtime performance win. Future placement,
collision/LODs and seating must be verified separately.

## Verification

- Four CPU views reviewed: front quarter, rear quarter, side and overhead.
  Circular rails, level supports and smooth rear panels are visible from opposing
  directions; editable material boundaries remain distinct.
- Fresh Blender reopen and GLB import pass: 43 parts, seven exported materials,
  identical evaluated triangle counts and dimensions. All parts have UV layers,
  finite vertices, positive signed volume and no zero-area faces. A disposable
  seam weld finds zero boundary/nonmanifold edges; delivery geometry is not welded.
- Freshly imported GLB rendered again in the same CPU studio and inspected.
  Source, blend and GLB hashes remain unchanged after verification. Original
  reference stays hidden with three packed image payloads.
- First round-trip audit incorrectly compared the editable cage bounds to the
  beveled export and failed at a 1.7 mm difference. Corrected audit compares
  evaluated geometry on both sides, which agrees exactly. Failed receipt retained
  privately; no tolerance increase or asset deformation was used to pass.
- Python syntax compilation passes for both recipes. Final authoring and
  verification logs contain `BENCH_REPAIR_AUTHORED` and `BENCH_ROUNDTRIP_PASS`.
  Authoring reports Blender's future-6.0 `use_nodes` deprecation notices; no current
  API failure. C++/Unreal build and C++ formatting are not applicable to this
  standalone Python/asset change and were not invoked.

Open `SourceAssets/CurvedBench_20261024/Review.html` for the before/after gallery.
Private reports are `RepairReport.json` and `Verification.json` beside the files;
process logs and the failed first audit are in `.agent/local/BenchRepair_20261024`.
[Recipe and editing guide](../../Scripts/StationRecipes/CurvedBench/README.md).

## Handoff

**Open:** the repaired Blender file or GLB and local gallery above.
**Check:** crescent silhouette, black/violet material balance and intended size.
**Still open:** owner appearance acceptance; AI-held Unreal import, collision,
seat/exit interaction and measured rendering cost only after a later authorization.
The existing observatory sofas remain in place. This is a source-only follow-up
under [RPT-20261023-02](../KNOWN_ISSUES.md), not a new gameplay completion claim.
Only recipes/documentation are published; all model and reference payloads stay
private on C. No automatic merge.
