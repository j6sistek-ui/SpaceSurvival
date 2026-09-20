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
