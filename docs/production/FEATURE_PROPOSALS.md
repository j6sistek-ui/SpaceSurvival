# Feature proposals — parked

Features the owner has logged for later. **Nothing here is adopted, scheduled, or built.**

Kept out of `docs/GAME_SCOPE.md` and `docs/production/WORK_PACKAGES.md` on purpose — those are the
Phase 1 specification and work-package dictionary, and an idea sitting in either would read as
committed scope.

Flight motion has its own register: [FLIGHT_MOTION_PROPOSALS.md](FLIGHT_MOTION_PROPOSALS.md).

---

## Cinematic capture (photo mode)

Logged 2026-09-20. Owner's instruction: *just log it, don't build it.*

- Entered from the **pause menu**.
- **Game state stays paused** while it is active.
- The camera **free-roams**, released from the ship.
- The player **takes a picture**.

Nothing in the codebase covers this today — no photo mode, free-roam camera or capture path exists
outside the offscreen tooling used for development validation.

---

## Asteroid fields: constant density, variable director

Logged 2026-09-20. Owner's note, flagged as a topic to return to: *"more in that topic later but
that's enough for me to remember it."* **Not adopted, not designed, not built.**

- **The asteroid field does not get harder as levels progress.** It is at **full density and full
  navigational difficulty from the first wave.**
- What escalates instead is the **director**, which drives the density of **thrown** asteroids.
- Thrown asteroids may become a distinct style later. **For now, paint the round-specific ones red or
  green** so they read as a different thing from the field itself.
- The point: *"this way from the beginning space feels real and alive."*

### What it touches

This is a redefinition of existing spec, not an addition. `docs/GAME_SCOPE.md` section 4 (Waves) and
section 5 (Survival Director, with its "Director progression" subsection) currently carry the
escalation model this replaces. Neither has been changed - the spec still says what it said.

The distinction worth preserving when this is picked up: **field density is a constant, throw rate is
the variable.** Difficulty comes from what is aimed at the player, not from the world getting more
crowded around them.
