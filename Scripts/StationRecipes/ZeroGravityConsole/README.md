# Zero-gravity console source cleanup

Owner supplied `zero+gravity+console+3d+model.glb` as the second cleanup in PR92,
after approving the bench preview. This is source work in Blender, with Unreal
still held. It does not add console behavior or a zero-gravity volume.

## Open and edit

Private delivery: `C:/Users/j6sis/SpaceSurvival/SourceAssets/ZeroGravityConsole_20261024/`.

- `Review.html`: before/after views, side, overhead and fresh GLB render.
- `ZeroGravityConsole_Repaired.blend`: 60 named editable parts and CPU studio.
- `ZeroGravityConsole_Repaired.glb`: repaired assembly with four embedded artwork
  projections; excludes the original and studio.
- `RepairReport.json` and `Verification.json`: identity and reload checks.

Edit **REPAIRED - editable parts**. The root moves the whole assembly; cabinet,
rails, sign, monitor, service panels, seals and feet are separate. The untouched
input remains packed in **REFERENCE - original source - hidden**. Turn off the
repaired collection before displaying that reference. Original source geometry
is normalized to about one meter; the reconstruction is approximately
1.964 m wide, 1.241 m deep and 2.127 m tall, with controls around 0.92 m high.
This is an explicit human-scale assumption, not confirmed station placement.

The original has 9,606 triangles and retains 1,055 nonmanifold edges after a
disposable seam weld. Reconstruction replaces warped rails and uneven/open
surfaces with closed beveled parts. It retains the original sign/display/button
artwork using orthographic color projections, including its original wording.
The metal cabinet uses portable PBR materials. It is a reconstruction, not a
topology-preserving repair or a retexture of every original surface.

## Reproduce

Use the existing Blender 5.2 installation; do not install packages. Launch with
`Start-Process -WindowStyle Hidden` and redirected logs on Windows:

```text
--background --factory-startup --disable-autoexec --threads 6
--python RepairConsole.py --
--source "C:/Users/j6sis/Downloads/zero+gravity+console+3d+model.glb"
--output "C:/Users/j6sis/SpaceSurvival/SourceAssets/ZeroGravityConsole_20261024"
```

The recipe requires the inspected source SHA256. It never writes to the input,
uses Cycles CPU with six threads, and replaces only its named deliverables.
`--bake-only` provides a fast artwork-framing check without building the model.
The optional original-angle gallery links use the private inspection folder.

After authoring exits, run a second hidden Blender process:

```text
--background --factory-startup --disable-autoexec --threads 6
--python VerifyConsole.py --
--output "C:/Users/j6sis/SpaceSurvival/SourceAssets/ZeroGravityConsole_20261024"
```

Require `CONSOLE_REPAIR_AUTHORED` and `CONSOLE_ROUNDTRIP_PASS`; process exit alone
does not prove Blender Python succeeded. The verifier reopens the saved blend,
audits evaluated solid meshes, replaces only its disposable assembly with the
GLB, checks embedded images and renders again. It does not resave the delivery.

## Remaining boundaries

Published files are recipes, this guide, gallery template and concise evidence.
All model/texture payloads remain private on C. No Unreal import, collision,
LOD, console interaction, station placement or performance validation occurred.
The bench preview is owner-approved; console appearance needs its own review.
Both remain under [RPT-20261023-02](../../../docs/KNOWN_ISSUES.md).
