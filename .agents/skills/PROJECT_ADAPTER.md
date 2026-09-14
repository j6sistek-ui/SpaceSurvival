# SpaceSurvival skill adapter

Use this mapping when a repository skill is selected. This file adapts generic guidance; the owner's current instructions, AGENTS.md, docs/GAME_SCOPE.md and IMPLEMENT.md remain authoritative.

## Scope and implementation map

- Phase 1 is single-player Windows. Generic networking/RPC, Steamworks, GameplayTags, GAS or new-system suggestions are optional techniques, not requirements to add them.
- Domain rules: Source/SpaceSurvival/Domain/SurvivalCore.*. Session ownership and persistence: SSGameInstance.* and SSLocalSave.*.
- Runtime input/orchestration: SSGameMode.cpp (including ASSPlayerController). Flight: SSShip.*. Hazards, enemies, encounters and director: SSWorldActors.*. Station/walker: SSStation.*. HUD: SSHUD.*. Tuning: SSPhase1Data.h, SSContentTypes.h and the authored DA_Phase1 asset.
- Read current asset paths and save slots from source when needed; do not infer loaded content from filesystem existence. The default and optional trial ship differ. Appropriately licensed local content is required to reproduce the licensed presentation.
- Existing native rules and Data Assets are the starting point. A header-only change does not require a token .cpp edit. Retain stable string paths until a measured loading, cook or authoring problem justifies migration. Keep natural simulation Tick where it is needed.

## Tools and validation

- Detect the current engine installation; the reviewed version was UE 5.8.2. Do not copy an author's absolute paths or assume nearby minor-version APIs are identical.
- Use Scripts/TestCore.ps1 and Scripts/Format.ps1 -Check for the existing container workflows, and existing Python for the source/content checks specified in AGENTS.md.
- Use Scripts/Build.ps1 for native Unreal compilation, authoring, automation and packaging with the existing owner-installed Windows toolchain. Read its current parameters rather than inventing commands. Do not replace it with a plugin's build/restart helper.
- A report is tied to its source, build configuration, content mode, actual resolution, assistance flags and executable identity. Separate portable tests, engine automation, packaged runtime, physical input, natural play and performance evidence.
- Existing owner checklists do not get marked by code presence, actor counts or fixture success. Do not discard a transition spike just because a median/percentile is good; attribute material outliers to gameplay moments.
- Scale checks to the change and the required acceptance criteria. Do not repeatedly run expensive builds or recook unchanged content without a new reason. A generic recommendation to check Shipping is not permission to change the release configuration or publish.

## Editor access

The editor belongs to one integration lead. Serialize Unreal calls and schedule builds/restarts at a stable checkpoint. Inspect the actual MCP tool inventory/schema before using a tool name from a skill. A project skill is not evidence that Unreal MCP is connected.

Existing Python authoring remains useful. For a future connection, evaluate UE 5.8 native MCP first and VibeUE only for a demonstrated gap. Neither is enabled by these skills. Keep automation local and verify packaging exclusions if an editor bridge is later added. Preserve AGENTS.md when adapting generated agent guides.

## Known upstream limits

The imported UnrealXu debug helper scripts were omitted. In an isolated fixture, its scan_output_log.py returned zero errors and warnings for standard category-before-verbosity Unreal log lines containing one of each. Its filesystem-only asset helper would not prove cooked or loaded state. Use the repository's current validation flow and relevant editor inspection.

Buckley's Enhanced Input skill at 023eaa68 claims wrong-type FInputActionValue getters return zero. Installed UE 5.8.2 InputActionValue.h getters instead expose components / IsNonZero; consult current engine source and Epic's API reference. Buckley materials remain linked references because redistribution licensing was unconfirmed at review time.
