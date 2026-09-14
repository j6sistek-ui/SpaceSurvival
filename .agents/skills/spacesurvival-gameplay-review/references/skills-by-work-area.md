# Skills by work area

This is original SpaceSurvival guidance, not a copy of the linked skill bodies. Select only the area relevant to the current task. Read the selected upstream entry before using its details, consult the errata in [the catalog audit](../../CATALOG_AUDIT.md), and verify APIs against the installed engine. Links are pinned to the reviewed Buckley revision. Current owner decisions and project scope outrank generic advice.

## Flight, camera and physical controls

Trace the real PlayerController input to ship or walker, including menu state, possession, focus and close-frame consumption. Compare keyboard/mouse and gamepad capabilities in live reward/depot panels. Match camera clearance to the visible hull and collision envelope; keep mouse deltas distinct from stick rotation rates. Enhanced Input configuration alone does not prove action/context bindings. A migration needs an input-state acceptance table first.

Read [Enhanced Input][enhanced-input], [character/movement][character-and-movement] or [core types][core-types-and-containers] as needed.

## Combat, enemies and hazard fairness

Use committed attack paths, the existing director admission budget and normal movement speeds to inspect telegraph visibility and avoidability. Test both enemies and compound hazards with ordinary durability and upgrades. Preserve the single electrical clock for warning, appearance and damage. Navigation frameworks and physics simulation are optional; neither proves better arcade combat.

Read [AI/navigation][ai-and-navigation], [physics/collision][physics-and-chaos] and [debugging][debugging-techniques].

## Interactions, station services and economy

Follow explicit acceptance through current eligibility/range checks into the domain transaction and visible result. Verify once-only grants, unaffordable/invalid choices, depot interruption and station return. Review normal player spending before changing prices. Keep existing roster identities and five-wave cadence.

Use the local ue5-world-interaction workflow and [data-driven design][data-driven-design].

## Animation, pilot visibility and contact

Inspect continuous pilot, exit, idle, forward/back/strafe and run motion. Measure visible contacts and capsule/mesh offsets rather than approving a still image. The existing native pose proxy is a valid starting point; check its game-thread snapshot and evaluation ownership before editing. An optional ship that hides the pilot needs an explicit visual acceptance decision. Preserve original hero sources and adopt retargeting/IK only for a demonstrated motion problem.

Read [animation][animation-system], [Control Rig/IK][control-rig-and-ik] and [meshes][meshes-static-and-skeletal].

## Audio and music

Listen to full combat overlaps, field warnings, rewards, docking and station transitions. Check that important cues remain distinguishable at actual settings and that voices clean up after the state ends. The existing audio subsystem already preloads content, limits voices and controls music layers. Choose MetaSounds or additional mixing tools only for a concrete benefit.

Read [audio][audio-and-metasounds] and [subsystems][subsystems].

## VFX and spatial ambience

Improve a current effect through explicit native state and editable content references. Verify user-parameter names/types, bounds/culling, lifetime, world-origin shifts, camera-local versus world-local placement, cooking and combined-scene cost. Keep cosmetic dust outside damage/director counts. Particle collision must not silently become damage authority.

Read [Niagara][niagara-vfx]. The transferable ideas in [weather particles][udw-particles] and [spatial blends][udw-spatial] do not require purchasing or adding UDW.

## Materials, lighting and rendered readability

Check the actual material domain, blend mode, texture conventions, mesh slots, exposure and shadow cost. Normal maps supplied as DirectX should not receive an automatic green-channel flip. Validate silhouettes and hazard warnings in motion at intended display settings. Evaluate Nanite/LODs or light changes against an observed rendering bottleneck.

Read [materials][materials-and-shaders], [lighting][lighting-and-lumen] and [rendering][nanite-and-rendering].

## UI, accessibility and feedback

Review the current Canvas HUD at supported resolution/UI scale with mouse and controller. Cover focus, navigation, selection/confirm/back, panel occlusion, failure explanations and returning control to gameplay. Widgets should read state and request actions through the owner. UMG/CommonUI is a candidate for a justified panel improvement, not a mandatory rewrite.

Use the local ue5-ui-umg-slate adapter and [UMG/Slate concepts][umg-and-slate].

## Data, Blueprint and authoring

Expose the next useful tuning or presentation parameter through the existing Data Asset and validation path. Preserve stable IDs and serialized names. A Blueprint variant needs its native parent, editable defaults and actual runtime class reference wired. Make authoring commands idempotent where possible; fail explicitly on import, compile or save errors and read back the result.

Read [data design][data-driven-design], [Blueprint/C++ integration][blueprint-cpp-integration], [editor Python][editor-scripting-and-python] and [importing][importing-content].

## Architecture, component ownership and lifetime

Trace ownership from domain Session through GameInstance, GameMode, actors, subsystems and presentation. Review constructor/CDO setup, runtime registration, reflected retention, weak observation and teardown. Inspect BeginPlay followed by Configure for duplicated presentation work before introducing deferred spawning. Add an event boundary or extracted class only where current coupling obstructs an authorized change.

Read [planning][gameplay-architecture-planning], [actors/components][actors-and-components], [C++ fundamentals][cpp-fundamentals], [memory/GC][memory-and-gc] and [delegates][delegates-and-events].

## Persistence and asynchronous work

Keep account/settings/suspension distinct and preserve durable consume-before-resume and once-only death awards. Profile account writes triggered during input. A worker-thread design requires immutable snapshots, ordered acknowledgements and defined shutdown/stale-callback/failure behavior. The current backend is explicitly game-thread-bound; using AsyncSaveGameToSlot is not an equivalent protocol by itself.

Use the local save adapter and read [save/load][save-and-load] or [timers/async][timers-and-async] for the actual change.

## Debugging and acceptance evidence

Define a player-visible result, capture the first divergence and select the smallest discriminating check. Preserve useful deterministic tests while labeling accelerated waves, inflated health, scripted actions, direct actor manipulation and offscreen captures. Physical comfort, sound quality, normal balance and retry appeal require different evidence. A source observation is not a reproduced runtime defect.

Read [automation/testing][automation-and-testing], [debugging][debugging-techniques], [logging][logging-and-assertions] and [engine source navigation][navigating-engine-source].

## Performance, packaging and release quality

Bind each result to source, assets, package identity, actual resolution/settings and assistance. Separate cold loading, CPU/GPU time and memory growth. Include material transition spikes and representative busy scenes; do not infer the minimum-spec gate from a capped high-end fixture. Verify cooked dependencies, editor-only plugin boundaries and a clean-PC installation/update/save path when release work reaches that stage.

Read [game-thread costs][game-thread-performance], [profiling][profiling-and-optimization], [build system][module-and-build-system], [asset management][asset-management] and [packaging][packaging-and-deployment].

## Efficient use

Give one lead ownership of editor/build integration. Start a task with one player-visible goal, the relevant code path and evidence needed to close it. Load one or two relevant entries, check only the APIs used, and batch related source checks. Run expensive Unreal work after a coherent bounded change. Record the resulting source/package and acceptance gaps once; the next chat should start there. More installed skills or longer prompts do not establish better output or usage savings.

[enhanced-input]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-enhanced-input/SKILL.md
[character-and-movement]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-character-and-movement/SKILL.md
[core-types-and-containers]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-core-types-and-containers/SKILL.md
[ai-and-navigation]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-ai-and-navigation/SKILL.md
[physics-and-chaos]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-physics-and-chaos/SKILL.md
[debugging-techniques]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-debugging-techniques/SKILL.md
[data-driven-design]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-data-driven-design/SKILL.md
[animation-system]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-animation-system/SKILL.md
[control-rig-and-ik]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-control-rig-and-ik/SKILL.md
[meshes-static-and-skeletal]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-meshes-static-and-skeletal/SKILL.md
[audio-and-metasounds]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-audio-and-metasounds/SKILL.md
[subsystems]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-subsystems/SKILL.md
[niagara-vfx]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-niagara-vfx/SKILL.md
[udw-particles]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/ultra-dynamic-weather/ue-udw-particles-lightning-wind-sounds/SKILL.md
[udw-spatial]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/ultra-dynamic-weather/ue-udw-spatial-weather/SKILL.md
[materials-and-shaders]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-materials-and-shaders/SKILL.md
[lighting-and-lumen]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-lighting-and-lumen/SKILL.md
[nanite-and-rendering]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-nanite-and-rendering/SKILL.md
[umg-and-slate]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-umg-and-slate/SKILL.md
[blueprint-cpp-integration]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-blueprint-cpp-integration/SKILL.md
[editor-scripting-and-python]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-editor-scripting-and-python/SKILL.md
[importing-content]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-importing-content/SKILL.md
[gameplay-architecture-planning]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-gameplay-architecture-planning/SKILL.md
[actors-and-components]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-actors-and-components/SKILL.md
[cpp-fundamentals]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-cpp-fundamentals/SKILL.md
[memory-and-gc]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-memory-and-gc/SKILL.md
[delegates-and-events]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-delegates-and-events/SKILL.md
[save-and-load]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-save-and-load/SKILL.md
[timers-and-async]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-timers-and-async/SKILL.md
[automation-and-testing]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-automation-and-testing/SKILL.md
[logging-and-assertions]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-logging-and-assertions/SKILL.md
[navigating-engine-source]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-navigating-engine-source/SKILL.md
[game-thread-performance]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-game-thread-performance/SKILL.md
[profiling-and-optimization]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-profiling-and-optimization/SKILL.md
[module-and-build-system]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-module-and-build-system/SKILL.md
[asset-management]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-asset-management/SKILL.md
[packaging-and-deployment]: https://github.com/kevinpbuckley/unreal-engine-skills/blob/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core/ue-packaging-and-deployment/SKILL.md
