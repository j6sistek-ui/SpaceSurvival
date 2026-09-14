# Repository skills

This small set lives in Codex's repository discovery directory, .agents/skills. Each skill has its own SKILL.md and optional on-demand references. It does not enable an Unreal MCP server.

The full code findings, public-resource evaluation and implementation proposal are in [issue #7](https://github.com/j6sistek-ui/SpaceSurvival/issues/7). The [complete 73-entry catalog audit](CATALOG_AUDIT.md) records a decision for every skill in both pinned repositories. [Skills by work area](spacesurvival-gameplay-review/references/skills-by-work-area.md) maps relevant knowledge to actual tasks without loading the entire catalog.

| Skill | Select it for |
|---|---|
| spacesurvival-gameplay-review | Actual player-path review, gameplay defects and Phase 1 acceptance evidence |
| ue5-cpp-gameplay | A bounded native class/component or Data Asset change |
| ue5-debug-validation | Reproduction, first-failure diagnosis and focused regression work |
| ue5-performance-packaging | Measured runtime performance or a packaging-readiness task |
| ue5-architecture | Existing ownership, module dependencies and a justified bounded refactor |
| ue5-blueprint-workflow | Real Blueprint graph/pin edits and content authoring |
| ue5-save-load-replication | Local persistence/schema/failure review; networking portions excluded in Phase 1 |
| ue5-ui-umg-slate | Focus, feedback, layout and a justified panel migration |
| ue5-world-interaction | Pickups, events, service eligibility and once-only transactions |

Load only the skill relevant to the current task. Explicit invocation examples are $spacesurvival-gameplay-review or $ue5-debug-validation. Read PROJECT_ADAPTER.md when selecting an imported skill; it maps the generic workflow to this project.

The skills are available to Codex tasks using a checkout containing these files. A task on another branch will not gain them until that branch incorporates the skills commit. Discovery refreshes on a subsequent turn; explicit SKILL.md paths can be used if the current client has not refreshed its catalog.

## Provenance and local changes

The eight ue5-* folders derive from [UnrealXu/UnrealEngine5-Skills](https://github.com/UnrealXu/UnrealEngine5-Skills) at c21bb876a128a7c06e2782769bda524a3301aa99 (August 26, 2026). The retained MIT grant is in licenses/UnrealXu-MIT.txt. Each SKILL.md adds a project-adapter entry, each placeholder adapter points to PROJECT_ADAPTER.md, and Codex UI metadata is normalized to the current interface schema. Retained reference text is upstream material except the project adapters.

The debug skill's two optional scripts are omitted; the log parser fails the category-before-verbosity fixture described in PROJECT_ADAPTER.md, and file presence alone is insufficient asset validation. Architecture's bulk engine indexes/generator, Blueprint's tool-specific hotkey reference and the replication checklist are also omitted. No executable helper is included. The Blueprint entry removes the arbitrary node minimum and mandatory unconnected-tool instructions. The save entry adds ephemeral local state, excludes networking for Phase 1 and preserves the existing durable backend. The auto-assistant, module-router and PCG-building skills were not imported because their workflows do not fit this phase.

spacesurvival-gameplay-review, its work-area guide, PROJECT_ADAPTER.md and CATALOG_AUDIT.md are project-authored guidance from the gameplay/code evaluation. They do not copy the Buckley skill bodies. [Buckley's core library](https://github.com/kevinpbuckley/unreal-engine-skills/tree/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core) remains a linked reference; an explicit redistribution grant was not identified at that revision.

Nine discoverable workflows are a packaging choice, not a claim that the game needs only nine areas of expertise. Relevant Buckley domains such as animation, audio, VFX, collision, asset loading and lifetime are reachable through the work-area guide. These external references must be read when selected and their API claims checked against the installed engine. They are not installed or certified by appearing in the index.

The UI entry also recognizes the existing Canvas HUD and makes a UMG migration conditional on a concrete benefit. Update imported content deliberately against a pinned revision, review changed instructions/API claims and preserve attribution. Installation and format validation do not establish that a skill improves gameplay or reduces usage; evaluate those outcomes on real bounded tasks.
