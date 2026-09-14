# NASA Milky Way 2020 candidate

Native 8192x4096 Milky Way background for isolated gameplay evaluation. Lead approved the source preview; owner art acceptance remains open. The bright Hipparcos/Tycho layer is omitted, while faint Gaia points and detailed dust structure remain. It is not a starless image.

MilkyWay2020_8k.png is the exact approved Standard-display conversion: 52,500,034 bytes, SHA256 e5d17bc576e8a7278ab314958efb36e68a9ce0e6616169e035ef683a9f7c039d. It was reproduced byte-for-byte by Convert.py using the original NASA EXR; ConversionReceipt.json binds the executed converter, original and output. No sharpening, resampling, compositing or artistic changes were applied. RGB8 quantization is lossy relative to the half-float original.

The original is 137,307,727 bytes, SHA256 361d1961647af073b3b3e4aea4fca85f15b3c9d915e0c8c4befb02520dadd10a. It stays under ignored .agent/local/SkyCandidate; download URL and server file date are in manifest.json. No 8K PNG/TIFF of this same 2020 map is supplied by the official release. The separately inspected 2012 TIFF is an older rendition and is not this candidate.

## Portable source check and conversion

Run CheckSource.py with the existing Python runtime. It needs only the standard library, reads only, verifies the PNG size/hash/IHDR, exact original identity, and executed conversion receipt, and checks every source file stays below 100 MB.

To reproduce into a new output path, download the exact official EXR manually and verify the manifest hash, then run existing Blender 5.1.2:

    blender --background --factory-startup --threads 2 --python Convert.py -- --input <original.exr> --output <new.png> --receipt <new.json>

The script is CPU image load/save only. It rejects changed original bytes, another Blender version, existing outputs, resampling and a different output hash. Reproduction was executed successfully before source handoff. No render or host install is needed.

## Isolated Unreal APIs

- Scripts/AuthorMilkyWay.py main() creates only /Game/SpaceSurvival/Textures/T_MilkyWay2020 and /Game/SpaceSurvival/Materials/MI_SpaceMilkyWay.
- Scripts/ValidateMilkyWay.py main() performs fresh-process readback; it writes a routine report under Saved/Validation/MilkyWay2020 and never saves an asset.
- The material instance inherits M_Space and overrides only its SpacePanorama texture parameter. Existing direction mapping, seam/pole treatment, Tint and SkyIntensity remain inherited. The old material and texture packages are preserved.
- Texture settings are sRGB, BC7, Skybox, no power-of-two resampling, SimpleAverage mips, Wrap X / Clamp Y, zero LOD bias, 8192 maximum dimension, ordinary streaming enabled, and virtual streaming disabled. No NeverStream or global scalability changes.
- Existing candidates must pass exact metadata and setting checks; reruns do not silently repair or resave mismatches. Source/Config/Content preservation is checked per invocation, and unexpected new packages fail the guard.

## Unreal authoring and remaining native checks

The two assets were imported on UE 5.8.2, then loaded in a fresh process and validated at compiled 8192x4096 dimensions. A separate author rerun created nothing and left all 162 Source/Config/Content files byte-identical. All 160 files present before this task, including M_Space and the old panorama, were preserved. NativeValidation.json binds the source, packages, guarded snapshots and process evidence.

Two failed author attempts are retained: the factory InitialParent property is not exposed to this Python interface, and the installed texture-override setter always returns false even after applying the value. The importer now sets the parent through MaterialEditingLibrary and verifies the actual texture override; the fresh validator independently checks the sole global override and inherited values. The validator and rerun also logged the engine r.MotionVectorSimulation render-thread warning during shutdown; these were not warning-free runs.

Compiled size is distinct from actual runtime mip residency. The lead has prepared separate runtime selection on the real backdrop before its dynamic instance is created, retaining the original fallback when absent; that C++ change was not compiled or rendered by these asset processes. Native checks must confirm actual 8K residency, sky orientation/seam/pole appearance, field/enemy/ship readability and frame cost. Owner art acceptance remains open.

The background-only map best complements the existing 1,200 geometry stars; using the full NASA star map simultaneously would combine two unrelated bright-star distributions. The band is brighter in this background file than in the full star-map file at the same display conversion, so do not assume equal source intensity. Current shader defaults stay unchanged for the first comparison.

See LICENSE.md for required NASA and Gaia credit and primary reuse links. All current source files are below 100 MB; the raw EXR is deliberately excluded.
