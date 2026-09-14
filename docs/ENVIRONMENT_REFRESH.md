# Camera and environment refresh

**Historical release record.** The [combined space look](production/COMBINED_SPACE_LOOK.md) supersedes the cloud, sky, lighting, density, exhaust and tuning settings below. The 0.1.15-alpha release itself remains unchanged.

Owner request: retain approachable early-wave hazards while adding background volume, space dust and depth from supplied assets; fix the clipped flight camera; evaluate Space Station 4 as exterior mass. This is a scoped presentation follow-up, not Phase 1 completion.

## Implementation

- Flight camera: 900 cm minimum chase distance, 125 cm vertical socket offset, 4-degree downward sight; positional lag capped at 35 cm with substeps. Weapons continue using the actual rendered camera sight. Bounds tests exercise normal flight, boost, braking and turns at 30/60/144 Hz.
- Distant asteroids: four ISM batches, 128 deterministic clustered instances, bounded parallax. No collision, overlap, navigation or gameplay-target registration. Minimum conservative surface separation 25,300 cm. Early-wave Director admission and hazard counts unchanged.
- Ambient presentation remains unfinished: two local volume banks use the purchased Asteroid Library 3D texture. The latest editor capture removes the earlier opaque rectangular artifacts, but the intended luminous clouds remain visually absent. Do not treat this as delivered atmospheric quality. Low graphics settings may also omit volumetric fog.
- Fine dust: 128 world-space grains with edge recycling and smooth size fading, no collision; 1-4 cm sizes and a ship clearance bubble. One batched transform update per active tick.
- Engine wake: paired Epic Niagara ribbon trails, cleared when moored, hidden, retargeted or rebased. Current stock warm-colored ribbon is an initial wake treatment, not final tuned blue exhaust or an approved nozzle/socket fit.
- Station exterior: owner-supplied Space Station 4, 96,623 body triangles, two material primitives, 2K PBR maps. Detached light-point mesh omitted from derivative; original GLB unchanged. Exterior sits behind the bay at local (7000,0,3500), yaw90. Conservative solid envelope blocks the exterior and its visual gaps; they are not traversable passages. Existing dock corridor and on-foot bay are retained.

## Cost and controls

`ss.DistantAsteroidCount` 0-160 (default128), `ss.LocalDust` 0/1, `ss.AtmosphereClouds` 0/1, `ss.EngineTrails` 0/1 provide bounded presentation controls. These do not change progression or Director tuning. The volume grid is the largest new rendering risk and requires representative gameplay profiling. Offscreen captures are not 60 FPS acceptance evidence.

## Provenance and reproduction

The owner's cache remains unchanged. Stage the Content roots of NiagaraExamplesPack, Asteroid Library and the corridor under the matching project Content directories. All vendor roots, RPGEnvironmentVFX and Vefects are ignored. RPG effects and galaxy shaders were inspected; wholesale fantasy effects are not integrated.

Run `Scripts/AuthorStationExterior.py` with the existing Blender background workflow, then `Scripts/ImportStationExterior.py` through hidden Unreal Python. Run `Scripts/AuthorSpaceDustVolume.py` once to create the private atmospheric derivative. Import/author scripts refuse to replace existing completed derivatives. Inspect before rebuilding. Private derivatives live under `/Game/SpaceSurvival/Licensed`; no raw Fab content belongs in the public PR.

Run `Scripts/Build.ps1 -Target Editor`, then `-Target Test`, then `-Target Package` using PowerShell 7 and the installed Unreal/Windows toolchain. No new host dependencies are needed. Docker domain checks remain unavailable while the Docker daemon is absent.

## Owner checks tomorrow

Check whole-ship framing during controller turns/boost/braking, sight alignment, dust speed cues, volume readability, and whether background rocks are distinguishable from actual nearby threats. Check station arrival scale and camera comfort. These are not claimed passed by scripted tests. Compare the optional Try New Ship launcher separately; default ship remains the visible-pilot starter.

## Validation

Final evidence and package identity are recorded in `docs/validation/2026-09-14-environment-refresh.json`. Rendered fixtures use isolated fresh profiles and scripted input. Full natural ten-wave enjoyment, physical-controller feel, sound, clean-PC startup and near-alpha art acceptance remain open. The owner authorized a manual itch update on September 14; release verification is separate from visual acceptance.

User-supplied reference consulted: https://github.com/kevinpbuckley/unreal-engine-skills/blob/master/skills/ultra-dynamic-sky/ue-uds-fog-and-atmosphere/SKILL.md (blob ae92f0e5e5f3c8deff14d8764032bb953fa59ca9). Applies general shadow-scalability and fog-color diagnostics; UDS-specific runtime controls are not used and no UDS purchase/install is required by this pass.

Release correction: the final packaged check reproduced an opaque rectangle from the experimental cloud bounds. Atmospheric cloud banks are therefore disabled by default (`ss.AtmosphereClouds=0`) for 0.1.15-alpha. Local dust, background asteroids and engine wakes remain enabled. Earlier statements that the rectangle was fully fixed are superseded.
