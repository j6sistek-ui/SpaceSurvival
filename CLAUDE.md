# CLAUDE.md — how to actually run this project

Operational notes: the toolchain, the commands, and the traps that have cost real time.

**This file does not repeat [AGENTS.md](AGENTS.md)**, which owns scope discipline, PR and documentation
policy, and the Phase 1 Definition of Done. Read that one for *what you are allowed to do*; read this one
for *how the machine works*. Every fact below was verified by running it. Where the two disagree about a
command, this file is describing this machine and AGENTS.md is describing the intended workflow — both
statements are noted together rather than one quietly overwriting the other.

## This machine

| Tool | State |
|---|---|
| Unreal Engine 5.8 | `C:\Program Files\EpicGames2\UE_5.8` — `Engine\Binaries\Win64\UnrealEditor-Cmd.exe` |
| Python | 3.11.9, on PATH as `python` |
| clang-format | 22.1.3 at `C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\Llvm\x64\bin\clang-format.exe` |
| Docker | Desktop is usually **not running**, and `docker version` then *hangs* rather than failing fast. Start Docker Desktop if you need the container tooling; do not block a session waiting on it. |
| `gh` CLI | **Not installed.** Use the GitHub MCP tools instead. |

Two consequences worth stating plainly:

- `Scripts/Format.ps1` and `Scripts/TestCore.ps1` are container-based, so **they only run when Docker
  Desktop is up** — and when it is down they hang rather than erroring, which is easy to mistake for a slow
  build. Format with the clang-format path above instead (`-i` to apply, `--dry-run --Werror` to check); it
  needs no container. CI runs the containerised versions on `ubuntu-latest`, so that remains the confirming
  gate regardless of local Docker state.
- Issues and pull requests share **one number sequence** in this repo. A "missing" PR number is usually an
  issue.

## Build and test

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File Scripts/Build.ps1 -Target Editor
```

`-Target` accepts `Editor`, `Content`, `Validate`, `Test`, `Package`.

**`-Target Test` does not rebuild.** Run `-Target Editor` first or you are testing the previous binary.

The test gate demands *all* of: `succeeded >= 1`, `failed == 0`, `notRun == 0`, `succeededWithWarnings == 0`.
**Engine warnings fail it**, and they are easy to produce without failing a single assertion.

Running one suite instead of all 67 takes seconds instead of minutes — prefer it while iterating:

```bash
"C:/Program Files/EpicGames2/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" SpaceSurvival.uproject -unattended -NullRHI -stdout -FullStdOutLogOutput "-ExecCmds=Automation RunTests SpaceSurvival.Flight.DirectionalDodgeCollision" "-TestExit=Automation Test Queue Empty" -DisablePlugins=UAssetBrowser
```

Source-level checks, all fast and all runnable without Unreal:

```bash
python Scripts/CheckProject.py          # 34 structural checks
python Tests/TestSourceDigests.py       # 13 tests
python Scripts/CheckPrDocumentation.py --repo .
python Tests/TestPrDocumentation.py     # only when changing the documentation gate
```

## Hard rules

- **Never put a window on the owner's screen.** Every Unreal invocation passes `-NullRHI` (no renderer) or
  `-RenderOffscreen` (renderer, no window). Automation uses `-NullRHI`; content authoring and captures need
  a real RHI, so they use `-RenderOffscreen`.
- **Never commit `docs/production/UI_ART_REQUESTS.md`.** The owner keeps an uncommitted local edit there.
- **A change that affects how the game plays or feels is a conversation, not a task.** Propose it and wait.
  Fixing something that is provably broken is work; changing a dial is a decision.
- **Never run two captures concurrently.**

## The ship

The **Stellar Phoenix is the default hull.** `-SSClassic` flies the old kinematic hull; `-SSPhoenix` still
parses and is now a no-op. `ASSShip::SelectedHullIdentity()` is the single place that decides, and tests ask
*it* rather than re-deriving the answer from the command line.

Per-hull values live in `FSSHullDefinition` (`Source/SpaceSurvival/Public/SSContentTypes.h`), and
`Validate(FString &Why)` names the first one a hull left unset. **When a gate fails on a new hull, give that
hull its own number — never widen a shared tolerance to fit it.** Splitting an assertion into a universal
claim plus a per-hull figure is the established pattern; there are several worked examples in
`SSFlightAutomationTests.cpp`.

Two flight drives exist and never both run: the hand-written substepped integrator (classic) and the
ShipCore force solver on a simulating Chaos body (Phoenix).

## Traps that have already cost real time

- **Member versus body.** Under ShipCore the hand-kept `Velocity` member is never read by the solver, so any
  code that writes it must also write the physics body. This has been found **four separate times** —
  collision damage, hazard shoves, `RequestDodge` (the dodge key did nothing at all), and `HoldBody` leaving
  ShipCore's manager components pushing into a switched-off body. Assume a fifth exists.
- **`-NullRHI` creates no Niagara components.** An assertion that counts them reads 0 no matter how correct
  the ship is. Never write one — it cannot pass, so it gets "fixed" by being loosened until it asserts
  nothing.
- **A test aborts on its first breach.** So raising a bound to "measure" the true value yields a larger
  number every time, and never the real one. Measure with a dedicated survey flag, not by loosening.
- **A fresh checkout does not compile.** `Plugins/ShipCore/` is git-ignored with zero tracked files, while
  `SpaceSurvival.Build.cs` lists `ShipCore` as an unconditional dependency. The content fallback for
  `Content/Stellar_Phoenix/` is real; the *plugin* has none. CI never catches it — `.github/workflows/core.yml`
  has no Unreal step.
- **A packaged build does not contain what the tests ran against.** The hull is loaded by string path and
  `/Game/Stellar_Phoenix` has no `DirectoriesToAlwaysCook` entry, so a package silently ships the *old* hull
  with no error and a green suite. Check `grep -rn "Stellar_Phoenix" Config/` before any release. Note that
  `Config/DefaultGame.ini` treats a cook as redistribution and names `THIRD_PARTY.md` as the authority.
- **Treat "67 tests pass" as saying nothing about what a player receives.** The suite runs headless, against
  source, on a machine that has the licensed content. None of those three things is true of a shipped build.

## Pull requests

`Scripts/CheckPrDocumentation.py` validates structure, not truth. A body needs exactly one **checked**
declaration for each of `State`, `Solutions`, `Start/run`, `System/evidence`, `Storage/release` and
`Owner handoff`, each reading `Updated — <specific reason>` or `Reviewed unchanged — <specific reason>`;
then a `## Owner review` section with one `Open:`, one `Check:` and one `Still open:`; then a substantive
`## Validation` section.

The gate cannot tell whether the body describes the commits it actually contains. **Re-read the body against
the diff before asking for a merge** — a stale body that still passes the gate is the normal failure here.
