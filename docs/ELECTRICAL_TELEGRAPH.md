# Electrical pulse warning

Status: Editor compilation and actual-actor tests passed. Rendered readability and updated packaged verification remain pending.

The storm's charge and discharge flash now use the same countdown as its electrical damage. The independent sinusoidal warning clock was removed from electrical storms. Gravity's existing presentation and force behavior are preserved.

The first tick observes the final reaction delay after the Director's override. Each later cycle uses the configured hazard Data Asset pulse interval (default 1.8 seconds, minimum 0.2). Fractional frame overshoot is carried forward to avoid accumulating cadence drift. A long hitch applies at most one hit; it cannot deliver a burst of missed pulses. Damage, radius, electrical interference, roster and warning/audio cooldowns are unchanged. The clock continues when no player pawn is present, but damage still requires a ship inside the field.

The existing material brightens during charge and flashes on the discharge update. Flash decay is derived from the same cycle phase, without a second pulse timer. A newly configured actor restarts its full initial warning. Nonfinite timing values fall back to the existing defaults.

Two new Unreal integration tests drive the actual storm actor, possessed ship, domain damage path and dynamic material. They cover 30/60/144 FPS across 0.2, 0.73, 1.8 and 2.6 second intervals for 40 pulses each; Director-style reaction overrides; reconfiguration; range changes; temporary absence of a pawn; a long hitch; and malformed timing values. These fixtures create a transient GameInstance without Init or BeginPlay, block account persistence, mute audio, increase durability and disable only fixture actor expiry. They do not access production save slots or simulate a natural flight run.

The combined Editor build succeeded in 32.22 seconds. The fresh Unreal report at 2026.09.13-08.50.18 records 17 successful tests, zero warnings/failures/not-run tests, and 2.194975 seconds total duration. Both electrical tests passed, including all 12 cadence cases and 480 sampled discharges. The build retains the known nonpreferred MSVC and Engine Character.h deprecation warnings.

The [focused validation receipt](validation/2026-09-13-electrical-telegraph.json) binds the exact source, output DLL, report, logs, material/mesh files and test entries. These changes were uncommitted on base 4178ff443d34a7611a7353bac784091ec25ba0fa at build time; the receipt records their actual source hashes.

Scoped container formatting, diff checks and 21 structural checks also passed. The tests ran with NullRHI and synthetic actor steps. They establish timing/material-state/damage correctness, not rendered readability, audio quality, natural balance or the full Phase 1 acceptance gate. Package 9 predates this fix.
