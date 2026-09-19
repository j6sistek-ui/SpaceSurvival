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

## Cost

Usage is a real constraint here. The expensive mistake is not a slow command — it is deciding on your own
that something is worth fixing, and then investigating it fully before anyone said they cared.

- **Ask before investigating anything the owner did not ask for.** One line — *"found X, worth fixing?"* —
  costs a sentence; measuring it costs a session. **Noticing a defect is not authorisation to chase it.**
- Run **one automation suite**, not all 67, while iterating. The single-suite command is above.
- Fan out subagents only when the owner asks for it, or once at a milestone — and say what it will cost
  before starting. One sweep in this repository spent 927k tokens in thirteen minutes. It was worth it
  that time; it is not a routine move.
- Verify what the change touched, not everything around it.
- Prefer the narrow fix over the sweep that would also find its cousins. Offer the sweep; do not take it.

### Before anything expensive, ask

Unless the owner asked for that specific thing, confirm before starting. Say which rung you think it needs
and why — **take the lowest rung that would actually answer the question.**

1. **Look at it.** One offscreen capture or screenshot. Minutes, and it answers anything visible.
2. **One automation suite.** Seconds. The single-suite command is above.
3. **The whole suite.** Minutes — for the commit, not for the iteration.
4. **A full debug: instrument, rebuild, measure, re-measure.** Expensive. **Confirm it is needed first.**
5. **A subagent sweep.** Rare. State the cost before starting.

Most questions about the game are answered on rung 1. Reaching for rung 4 first is the habit to break.

### Is it worth validating at all

Before building verification around something, three questions:

1. **Can the owner see or feel it?** If not, does it change something they can?
2. **Does it exist?**
3. **What is the cheapest check that catches a real regression?** Usually one assertion — not a new field.

Fails 1 or 2, it is a one-line mention to the owner, not an investigation.

### The hard facts, so this does not repeat

Both of these happened in a single session, and both looked reasonable while they were happening:

- **`ContactStandoffCm` exists because a ship stops 1.38 cm further from a wall.** A substep artefact, on a
  24.84 m hull. It was given a documented per-hull field, a `Validate()` rule and a measured comment. No
  player can perceive 1.38 cm.
- **An assertion counting the hull's Niagara plumes was written, then withdrawn.** Under `-NullRHI` that
  count is *always zero* however correct the ship is — validating something that cannot exist inside the
  harness doing the validating.

In that same session, on the ship a player actually looks at: exhaust ribbons and engine cores were sitting
**11 m in front of the real engines**, the drive visual was **frozen at one value**, and a packaged build
would have shipped the **wrong hull entirely**. All three visible. None needed a tolerance field. The first
would have shown up in one offscreen capture.

**"67 tests green" was never the thing worth buying.**

## Bought content

The owner has bought 100+ content packs. **A pack's Blueprint is the deliverable, not a reference for its
meshes.** When they supply an asset or pack:

- **Use the Blueprint it ships, and its tools.** Reparent it to our class, or child-actor it. Do not
  re-derive its contents by hand.
- **Use its tools, not merely its ideas.** Buying a Blueprint that generates asteroids procedurally and
  then hand-placing our own asteroids "in that style" throws away the thing that was paid for.
- **A conflict with the game's architecture is a conversation.** Flag it, explain the specific risk, and
  let the owner choose. It is not licence to rebuild.
- In practice only a pack's *logic* conflicts — its own movement or input graph. Its *component wiring*
  almost never does. **Keep the wiring, replace the logic.**

**The evidence, so this is not an abstraction.** `BP_Spaceship` in the Stellar Phoenix pack already had the
skeletal mesh, both engine nacelle meshes, a separate airbrake mesh, twelve Niagara components, a point
light, two spring arms, a camera and the anim clips wired and working in its own demo level. Rebuilding
that by reading its component list and retyping the transforms into C++ produced **four separate placement
errors in one evening**: nacelle offsets composed against the wrong pivot so the engines hung under the
belly; 90 degrees transcribed into yaw instead of roll so the plumes sprayed sideways; eight effects
placed flat when they are children of some other parent; and a lamp mounted where it cannot light the
door it was added for. Every one of those was already correct in the Blueprint.

## Hard rules

- **Background runs go offscreen; an editor window is not forbidden.** Anything started on Claude's own
  initiative - automation, captures, content authoring - passes `-NullRHI` (no renderer) or
  `-RenderOffscreen` (a real renderer, no window), because it should never interrupt whatever the owner is
  doing. Automation uses `-NullRHI`; content authoring and captures need a real RHI, so `-RenderOffscreen`.
  That is courtesy, not a prohibition: opening the editor is fine when the owner is working alongside and
  expects it. An earlier version of this file called it a hard rule, which was wrong - it came from a
  single occasion when the owner happened to be busy, and it quietly ruled out interactive work that would
  sometimes be the faster answer.
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
