# SpaceSurvival Agent Instructions

## Source of truth

Read these before substantive project work:

1. `docs/GAME_SCOPE.md` — authoritative game/product specification.
2. `IMPLEMENT.md` — authoritative Phase 1 execution order and Definition of Done.
3. Existing source, assets, tests, and build configuration — authoritative implementation state.

If project documents conflict, use this precedence unless a later explicit owner decision says otherwise:

`docs/GAME_SCOPE.md` > `IMPLEMENT.md` > implementation assumptions.

Do not reinterpret locked design decisions without an explicit owner instruction.

## Mission

Build the Phase 1 near-alpha vertical slice defined in `IMPLEMENT.md` and satisfy its complete Definition of Done.

This is intended to become the actual foundation of SpaceSurvival, not a disposable prototype.

Success is not code presence or compilation alone. The integrated game loop must be validated end to end.

## Architecture

- Unreal Engine 5.
- Windows PC first; Steam is the intended commercial destination, but do not add Steamworks in Phase 1.
- Single-player only in Phase 1. Do not implement networking.
- Durable gameplay/system architecture belongs in C++.
- Tunable content belongs in Blueprints and/or Data Assets where appropriate.
- Keep core systems extensible for the Phase 2 systems described in `docs/GAME_SCOPE.md` without implementing those deferred systems now.
- Preserve supplied hero assets rather than recreating them unnecessarily.

## Scope discipline

Implement only the Phase 1 systems explicitly authorized by `docs/GAME_SCOPE.md` and `IMPLEMENT.md`.

You may:

- fill small implementation gaps;
- add polish required for coherence;
- improve transitions, VFX, audio, animation, and presentation;
- make technically necessary architectural decisions.

You may not silently:

- introduce major new mechanics;
- redesign the core loop;
- change progression philosophy;
- alter the every-five-wave station cadence;
- replace locked mechanics with preferred alternatives;
- implement deferred Phase 2 systems;
- expand content counts beyond Phase 1 limits merely because implementation time remains.

If a material deviation is technically required, document it explicitly.

## Working behavior

- Inspect the repository, available Unreal environment, dependencies, assets, build capability, and Git state before modifying implementation.
- Prefer production-quality implementations over temporary hacks in core systems.
- Keep systems modular and data-driven where practical.
- Do not hide incomplete behavior behind placeholder success states.
- Use subagents or parallel workstreams where useful, but one lead implementation context must own architectural coherence, integration, and final Definition-of-Done verification.
- Specialists should receive bounded tasks and should not independently reinterpret the entire game design.
- When implementation reveals a design ambiguity, choose the smallest interpretation consistent with `docs/GAME_SCOPE.md`; document consequential assumptions rather than inventing new game systems.

## Validation requirements

Before reporting Phase 1 complete, validate every applicable requirement in `IMPLEMENT.md`, including at minimum:

- project builds successfully;
- packaged Windows build is produced;
- complete Waves 1–10 loop is exercised;
- Wave 5 authored climax is validated;
- Station 1 is validated;
- Wave 10 compound climax is validated;
- Station 2 is validated;
- keyboard/mouse controls are tested;
- controller controls are tested;
- both weapon classes are tested;
- both enemy archetypes are tested;
- all four Phase 1 hazard families are tested;
- mobile depot is tested;
- both optional events are tested;
- both contract types are tested;
- all five core upgrade trees function as scoped;
- both Phase 1 utilities function;
- save/resume is tested;
- death correctly ends the active run;
- death → XP → unlock → hangar → next run is tested;
- second weapon unlock is tested;
- second ship unlock is tested;
- performance is reviewed against the 60 FPS minimum target;
- known issues and limitations are documented;
- Phase 2 integration notes are produced;
- `PROJECT_STATE.md` is current at handoff.

Never report `COMPLETE` when an applicable acceptance criterion is unverified.

If environmental/tooling limitations prevent verification, report the work as `PARTIAL`, complete everything else that can be completed, and identify the exact missing verification with evidence.

## Delivery state

Leave the repository with the delivery package required by `IMPLEMENT.md`, including:

- complete Unreal source project;
- packaged Windows build or documented artifact location;
- build/run instructions;
- architecture documentation;
- `PROJECT_STATE.md`;
- known issues/limitations;
- Phase 2 integration notes;
- validation/test record;
- clean, understandable Git state suitable for continued development.
