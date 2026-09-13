# Shadow-factor diagnosis â€” 2026-09-13

The bounded studio matrix completed at 09:32:53 UTC, and owned UnrealEditor-Cmd PID 52076 exited normally with code 0. All 128 files under Source, Config and Content retained their bytes; none were added. Console values were restored before exit. No targeted correction was established, so no render-policy or art change is proposed for the current package.

The fixture matches the previous material diagnostic: a unit-scale stock ship actor, camera `(-720,470,310)` looking at `(-15,0,20)`, FOV 42, three unchanged directional-light transforms/colors/intensities, exposure 1, bloom 0, screen percentage 100, no motion blur and AA disabled. All nine views have shadows enabled. The process used VSM, with hardware ray tracing disabled.

## Results

| Image | Single changed factor | Observed result |
| --- | --- | --- |
| Baseline | Default VSM normal bias 0.5; screen ray 0.015; SMRT directional ray count 8; light source angle 0.5357 degrees | Broad white-panel patch pattern reproduced |
| LightBias1 | All fixture lights' regular shadow bias 0.5 â†’ 1 | Pattern remains |
| LightSlope1 | All fixture lights' regular slope bias 0.5 â†’ 1 | Pattern remains |
| VSMTraceOff | VSM smart screen-ray length 0.015 â†’ 0 | Pattern remains |
| VSMNormal1 | VSM normal bias 0.5 â†’ 1 | Pattern remains |
| VSMNormal2 | VSM normal bias 0.5 â†’ 2 | Pattern remains |
| HardVSM | SMRT directional ray count 8 â†’ 0, retaining ordinary hard VSM shadow sampling | Pattern remains |
| SourceAngle2 | Light source angle 0.5357 â†’ 2 degrees | Pattern remains |
| BaselineRestored | All original values restored | Pattern remains; temporal shadow noise changes some pixels |

All three light contact-shadow lengths were already zero. A redundant contact-off case was skipped. The VSM smart screen trace is a separate mechanism from per-light contact shadows and was tested independently.

The restored-baseline full-image mean absolute channel difference is about 0.183 on a 0â€“255 scale. This provides a temporal-noise control; a small image difference in another case is not proof of improvement. Review.json contains the raw comparisons, including a fixed hull region. There is no automatic score claiming better shadow quality.

## Engine-source basis and next investigation

Installed UE 5.8.2 `VirtualShadowMapArray.cpp` defines VSM NormalBias as a receiver offset along the surface normal, scaled by camera distance. `VirtualShadowMapProjectionCommon.ush` applies a minimum offset and camera-distance scaling. `VirtualShadowMapProjection.usf` performs its separate smart screen trace before VSM/SMRT lookup and confirms that ray count zero uses hard VSM sampling. Regular per-light slope/depth bias does not establish control over this separate VSM receiver-normal offset. Source and runtime property values were inspected rather than inferred from names.

Next useful isolation is one light's shadow contribution at a time while retaining all illumination, followed by affected-pixel to built-triangle mapping and a comparison of geometric/shading normals. Only if that evidence supports it should an isolated transient material shadow-pass offset or a specific source surface correction be tested. Broad normal rebuilding, blind tessellation, global shadow disabling and an unreviewed global normal-bias increase are not supported by these results.

`Capture.py` reproduces the unsaved matrix using the installed editor Python interface. It requires a quiet project-file window because its guard rejects concurrent Source/Config/Content writes. `NativeMatrix.json` records actual values, images and preservation assertions; `Review.json` adds process result, evidence hashes and difference metrics. These are studio diagnostics, with no gameplay, performance or owner art acceptance claim.

A separate read-only cockpit measurement is preserved in `PilotControlProxies.json`. The current 13-cm grip segments end roughly 5.5–6.8 cm from wrist-to-middle-knuckle midpoint proxies. Extending/angling only their upper sections is the smallest proposed later fit change; actual hand-surface contact and release clearance must be checked before adopting endpoints. The pilot pose and transform remain unchanged.
