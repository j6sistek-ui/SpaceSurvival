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
- When an Unreal-specific issue stalls, consult the owner-provided [Unreal skills catalog](https://github.com/kevinpbuckley/unreal-engine-skills/tree/master/skills/core) and read the relevant skill before further trial-and-error. Validate version-specific advice against installed engine source; plugin-specific guidance does not authorize installing that plugin.
- Assess every proposed asset, kit or tool against the whole Phase 1 scope and the owner's desired experience, not only the active task. Maintain docs/production/SOLUTION_CATALOG.md with stable IDs, WBS uses, dated evidence, separate acquisition/evaluation status, whole-project value, timing and next checks. Retain useful later options; distinguish duplicate functionality from useful new art. Do not infer purchase, installation, integration or acceptance from a wishlist or catalog entry.
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

## Repository tooling workflow

- Run `./Scripts/TestCore.ps1` from the repository root for portable domain checks. `Dockerfile` uses `gcc:14-bookworm` to build strict C++17 and ASan/UBSan test binaries; it does not install host packages.
- Run `./Scripts/Format.ps1 -Check` to check C++ formatting, or omit `-Check` to apply it. `Tools.Dockerfile` supplies clang-format inside a container; `.clang-format` preserves Unreal generated-header include order.
- Run `python Scripts/CheckProject.py`, `python -m compileall -q Scripts ContentSource`, and `python ContentSource/ValidateSources.py` for source/content-source checks using an existing Python runtime.
- Unreal compilation, asset authoring, automation and Windows packaging use the owner's installed Unreal engine and Windows C++/SDK toolchain through `Scripts/Build.ps1`. The Linux container does not supply or validate these tools. Do not install host prerequisites without explicit owner instruction.
- Keep runtime artifacts, intermediate files and raw editor logs in ignored `Artifacts`, `Intermediate` and `Saved` directories. Commit concise sanitized validation records under `docs/validation` and intended content assets under `Content`.
- Never treat portable test passes or the assets-only authoring workbench as evidence of an integrated Unreal gameplay pass.

## Repository skills

- Codex-discoverable skills live under `.agents/skills`; see its README for selection and provenance.
- Use `spacesurvival-gameplay-review` for requested gameplay/code quality reviews and Phase 1 acceptance work; load other skills only for the active task.
- Imported generic skills must read `.agents/skills/PROJECT_ADAPTER.md`. They do not authorize networking, new mechanics, engine changes, tool installation, publication or merge.
- Verify third-party API advice against the installed engine. A skill, MCP connection or passing fixture does not establish accepted gameplay.
