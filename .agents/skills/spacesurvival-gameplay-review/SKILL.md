---
name: spacesurvival-gameplay-review
description: Review or improve SpaceSurvival flight, combat, station interactions, or Phase 1 acceptance by tracing actual player paths and matching claims to evidence. Use for gameplay defects and readiness reviews; do not trigger for unrelated repository administration.
---

Read [the project adapter](../PROJECT_ADAPTER.md) before applying this workflow. Use the current source, not an earlier chat's completion estimate.

**Start with the player's action.** Identify the input/device, game state, expected response, observed failure and source/package revision. Follow that action through PlayerController, pawn, GameMode, the domain Session, and the relevant asset or presentation callback. Investigate the first divergence. File size, C++ usage, Canvas UI, or a class name alone does not prove a defect.

**Review the path that matters to this task.**

- For controls, distinguish flight, walking, paused menus and live reward/depot panels. Check action availability on mouse/keyboard and controller, input consumption on the close-menu frame, hold/toggle state, possession changes and focus loss. Configured Enhanced Input classes do not prove action/context routing exists. Keep mouse deltas and stick rates distinct.
- For flight and threats, compare speed/turn authority, collision shape, visible silhouette, telegraph timing and a plausible escape route. Check combined hazards, offscreen cues, damage attribution and aim obstruction. Review normal settings as well as isolated cases.
- For rewards and stations, trace explicit acceptance, objective reachability, range revalidation, transaction results, once-only rewards, service discovery and return to flight. Apply the current authorized depot behavior, not historical instructions.
- For saves, distinguish account/tutorial progress, settings, suspension consumption and death award persistence. A blocking I/O path inside input Tick merits measurement. Preserve durable transaction guarantees; verify thread restrictions before suggesting asynchronous work.
- For presentation, inspect the running asset and motion: pilot visibility, feet/contact, camera clearance, animation transitions, material slots, HUD obstruction and sound hierarchy. A material assignment or still screenshot does not accept the moving experience.
- For performance, identify whether work is loading, construction, ticking, rendering or memory pressure. Measure cold and warm behavior when relevant. Existing hangar/audio preloads can change whether a synchronous load actually touches disk.

**Use discriminating evidence.** State each finding as a confirmed code condition, reproduced runtime failure, unmeasured risk, maintainability concern or missing acceptance evidence. Attach a file/function and a scenario. Verify third-party API claims against the installed engine. Do not assume a skill's example is correct.

The accelerated journey intentionally shortens waves, increases durability and manipulates objectives; scripted soak input can bypass PlayerController. Retain these useful regression checks, but do not use them to establish physical controls, normal balance, readability or retry appeal. A green portable CI run does not compile/cook Unreal.

**Deliver one bounded improvement.** Define the expected player-visible result before editing. Reproduce through the real runtime path where it matters, fix the smallest cause, and run the relevant project checks. Use a targeted regression only when it protects behavior or exposes a meaningful gap. Do not replace the full game with a new framework to satisfy generic skill advice.

Report what was inspected, what changed, what evidence supports it and what remains unverified. Use the authoritative Definition of Done without completion percentages derived from code or test counts. End with one concrete next owner playtest step; keep the full acceptance matrix in the repository.

Relevant public references, loaded only for the active problem:

- [Skills by work area](references/skills-by-work-area.md): project-specific tasks and pinned references across gameplay, presentation, architecture and delivery; select only the active area.

- [Epic Enhanced Input](https://dev.epicgames.com/documentation/unreal-engine/enhanced-input-in-unreal-engine): context and action routing.
- [Epic Visual Logger](https://dev.epicgames.com/documentation/en-us/unreal-engine/visual-logger-in-unreal-engine): state around gameplay failures.
- [Epic Unreal Insights](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-insights-in-unreal-engine): frame time, loading and memory.
- [Buckley core skills, pinned review reference](https://github.com/kevinpbuckley/unreal-engine-skills/tree/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core): consult the relevant subsystem; not vendored and not an API authority.
