# Repository skills

This small set lives in Codex's repository discovery directory, .agents/skills. Each skill has its own SKILL.md and optional on-demand references. It does not enable an Unreal MCP server.

The full code findings, public-resource evaluation and implementation proposal are in [issue #7](https://github.com/j6sistek-ui/SpaceSurvival/issues/7).

| Skill | Select it for |
|---|---|
| spacesurvival-gameplay-review | Actual player-path review, gameplay defects and Phase 1 acceptance evidence |
| ue5-cpp-gameplay | A bounded native class/component or Data Asset change |
| ue5-debug-validation | Reproduction, first-failure diagnosis and focused regression work |
| ue5-performance-packaging | Measured runtime performance or a packaging-readiness task |

Load only the skill relevant to the current task. Explicit invocation examples are $spacesurvival-gameplay-review or $ue5-debug-validation. Read PROJECT_ADAPTER.md when selecting an imported skill; it maps the generic workflow to this project.

The skills are available to Codex tasks using a checkout containing these files. A task on another branch will not gain them until that branch incorporates the skills commit. Discovery refreshes on a subsequent turn; explicit SKILL.md paths can be used if the current client has not refreshed its catalog.

## Provenance and local changes

The three ue5-* folders derive from [UnrealXu/UnrealEngine5-Skills](https://github.com/UnrealXu/UnrealEngine5-Skills) at c21bb876a128a7c06e2782769bda524a3301aa99 (August 26, 2026). The retained MIT grant is in licenses/UnrealXu-MIT.txt. Each SKILL.md adds a project-adapter entry, each placeholder adapter points to PROJECT_ADAPTER.md, and Codex UI metadata is normalized to the current interface schema. Other retained reference text is upstream material.

The debug skill's two optional scripts are deliberately omitted; the log parser fails the category-before-verbosity fixture described in PROJECT_ADAPTER.md, and file presence alone is insufficient asset validation. No upstream script is executed automatically. No auto-router, PCG, save/replication or UI skill was imported.

spacesurvival-gameplay-review and PROJECT_ADAPTER.md are project-authored guidance from the gameplay/code evaluation. They do not copy the Buckley skill bodies. [Buckley's core library](https://github.com/kevinpbuckley/unreal-engine-skills/tree/023eaa68d80897e6df64a22fcf471940a7b6848b/skills/core) remains a linked reference; an explicit redistribution grant was not identified at that revision.

Update imported content deliberately against a pinned revision, review changed instructions/API claims and preserve attribution. Installation and format validation do not establish that a skill improves gameplay or reduces usage; evaluate those outcomes on real bounded tasks.
