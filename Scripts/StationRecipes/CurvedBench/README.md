# Curved bench source repair

Owner request: repair the supplied curved sofa and stay out of Unreal. This is
a Blender-only repair, separate from the observatory's existing native sofas.

## Open

Local delivery: `C:/Users/j6sis/SpaceSurvival/SourceAssets/CurvedBench_20261024/`.

- `CurvedBench_Repaired.blend`: editable repaired assembly, seven PBR materials,
  preview studio and a hidden, packed reference of the original download.
- `CurvedBench_Repaired.glb`: repaired parts only; no studio or original mesh.
- `Review.html`: original/repair views and the fresh GLB import render.
- `RepairReport.json` and `Verification.json`: source/output hashes and checks.

In Blender, edit the **REPAIRED - editable parts** collection. The seat, three
back cushions, shell, rails, arm pads and feet have separate names/materials.
The original is in **REFERENCE - original source - hidden**. Materials use
portable PBR values, with UVs available for later painting. The source's smeared
texture atlas is retained with the hidden reference rather than stretched onto
the reconstructed parts. The seven material slots are intentionally shared.

The measured 107-degree crescent is retained. Scale is corrected from the
normalized download to a seat approximately 45 cm high; the repaired footprint
is approximately 3.66 by 3.61 m and the top rail is 0.933 m high. The repair
reconstructs warped surfaces and irregular supports; it is not a topology- or
texture-preserving conversion. The evaluated export has 41,978 triangles across
43 closed parts. This is a source asset, not a measured runtime optimization.

## Reproduce without Unreal

Use the existing Blender 5.2 installation. Do not install packages. On Windows,
launch with `Start-Process -WindowStyle Hidden`, redirected logs, and these
arguments (quote the paths as needed):

```text
--background --factory-startup --disable-autoexec --threads 6
--python RepairBench.py --
--source "C:/Users/j6sis/Downloads/futuristic+curved+sofa+3d+model (1).glb"
--output "C:/Users/j6sis/SpaceSurvival/SourceAssets/CurvedBench_20261024"
```

The recipe refuses a different source hash. Rerunning replaces its own named
outputs; it never saves to the input file. Cycles is explicitly CPU-only, six
threads. It does not connect to Unreal, create UAssets or modify a level.

After the authoring job exits, launch another hidden Blender process with:

```text
--background --factory-startup --disable-autoexec --threads 6
--python VerifyBench.py --
--output "C:/Users/j6sis/SpaceSurvival/SourceAssets/CurvedBench_20261024"
```

Require the `BENCH_ROUNDTRIP_PASS` marker, not just Blender's process exit code;
Blender can exit zero after a Python assertion. Verification reopens the blend,
audits evaluated geometry, replaces the disposable repaired assembly with the
GLB import and renders using the same CPU studio. It does not resave the blend.

## Boundary

Private source and deliverables remain ignored under `SourceAssets`; only the
recipe, guide and evidence are published. No new C++ binary or package exists.
Unreal import, collision, LODs, seat interaction, placement and performance are
unverified and are held by the owner's explicit instruction. Existing follow-up:
[RPT-20261023-02](../../../docs/KNOWN_ISSUES.md).
