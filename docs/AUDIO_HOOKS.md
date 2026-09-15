# Phase 1 audio hooks

Historical September 13 hook implementation: **Unreal build, content import, fresh content validation and both audio automation tests passed.** The final combined suite passed 21/21 tests with no warnings or failures at 2026-09-13 09:29:16 UTC. Native playback and listening acceptance remain unverified. Phase 1 remains **PARTIAL**.

The scope requires spatial threats, distinct warnings, atmospheric environments and an adaptive score. This change wires those existing behaviors to editable cues. It does not establish cinematic quality, mix balance, perceived direction, warning readability or owner acceptance.

The September 15 [local audio and glyph evaluation](production/SOLUTION_CATALOG.md#new-local-audio-and-glyphs-evaluation-and-proposed-integration) records the two newly downloaded sound packs and the proposed selective integration. Those assets have not replaced these generated sources; listening and integration remain pending.

## Startup and settings

Music, ship engine and station ambience disable automatic component activation, assign their persisted master/category gain, then call Play. The initial Hangar phase is read from the session before the hub exists. This closes a source ordering defect; no previously audible leak was reproduced.

The persistent base score uses 0.35 gain in the home hangar/station and 0.65 during the run. Pressure layers follow the existing Director pressure, capped at 0.65 gain, and are silent during breathing and non-flight phases. The climax layer uses 0.75 gain only during Climax. All values are multiplied by master and music settings. Engine and station use effects gains 0.35 and 0.25. Settings gains are finite and bounded to 0–1; invalid values fail silent.

All looping source assets are authored with PlayWhenSilent virtualization so a muted score layer can retain its timeline. The fresh-content validator checks that flag. This is separate from verifying the actual audio renderer and phase alignment by listening.

## Reflected threat cues

Existing hazard and enemy Data Asset rows expose cue definitions:

| Existing behavior | Editable field | Default source cue |
| --- | --- | --- |
| Electrical field charging | FieldLoopAudio | ElectricalCharge |
| Electrical pulse discharge | DischargeAudio | ElectricalDischarge |
| Gravity field ambience | FieldLoopAudio | GravityAmbience |
| Destructible asteroid/wreckage defeat | DestructionAudio | DebrisBreak |
| Enemy projectile creation | ShotAudio | EnemyFire |
| Enemy defeat, including environmental collision | DestructionAudio | EnemyBreak |

Each cue has UseDefaultSound, a soft Sound reference and Gain. UseDefaultSound=true selects the fixed role preset, including for old serialized rows whose new fields were absent. Setting it false honors the Sound reference exactly: a blank reference means deliberate silence. Authoring does not replace custom references or overwrite explicit blank intent. Existing actor kinds, save identities, damage, drop rates and progression remain unchanged.

An electrical loop's envelope/pitch follows the same countdown that controls its visual discharge and damage. The discharge cue is emitted only when that clock fires. Gravity volume rises with its existing telegraph. Enemy fire plays after an actual projectile spawns; destruction plays once on actual defeat, with no kill reward added to environmental defeats.

Loop cues must actually loop, and one-shot cues must be non-looping. A mismatched override is silent rather than falling back. Finite authored gain clamps to 0–1; nonfinite gain is silent.

## Voice and lifetime bounds

USSWorldAudioSubsystem owns the spatial mix for a Game/PIE world, separately from gameplay and save state. It preloads the fixed cue hooks during GameMode initialization and retains resolved assets for that world.

- Shared distance attenuation: 650 cm inner radius and 7,500 cm falloff, with spatialization enabled.
- Shared renderer concurrency: 12 one-shots and 4 field loops, farthest then oldest eviction, with short 0.04/0.08-second voice-steal fades.
- Component allocation: at most 12 retained one-shot components; at most 24 field components, matching the Director threat cap.
- Inaudible one-shots beyond 8,150 cm or at zero effects gain allocate nothing.
- One-shots are released on the next subsystem tick after their bounded duration (at most ten seconds) plus a 0.25-second cleanup margin. Loop overrides cannot enter the one-shot path.
- Fields attach to their actual actor and end when the actor is destroyed. A field evicted by concurrency retries at most once per second.
- Existing voices apply live master/effects settings each subsystem tick. World teardown stops and destroys retained components.

Native renderer concurrency, starvation, pause/focus behavior, mixing under maximum pressure and positional perception require rendered playback and listening. No such pass is claimed here.

## Sources and validation

Scripts/GenerateAudio.py adds six deterministic original synthetic sources. All ten earlier WAV files retain their exact bytes; the local generation receipt is .agent/local/AudioSourceGeneration.json. The complete audio manifest records 16 source hashes, formats, durations and peak/RMS levels. No samples or external audio were used.

Source validation passed for 26 meshes, 16 WAVs and the unchanged supplied GLB; 22 source structural checks passed. Separately, the combined Editor build succeeded in 21.30 seconds, content imported at 09:23:45 UTC, and fresh validation passed at 09:26:42 UTC with 16 SoundWave assets and all seven loops checked for PlayWhenSilent. The initial generic asteroid material expectation failed after the approved photographic material adoption; the lead corrected that exact expectation while retaining the geometry preservation guard.

SSAudioAutomationTests.cpp adds:

1. AudioFirstPlayMix: transient GameMode BeginPlay, initially muted and unmuted Hangar, real ship/station components, Director pressure, breathing/climax/station changes and live mute.
2. SpatialThreatAudio: actual electrical timing/damage cue, gravity loop, enemy projectile/destruction, asteroid destruction, custom Data Asset routing, explicit silence, loop-role rejection, malformed gain, distance filtering, burst allocation and owner/lifetime cleanup.

The fixtures use in-memory sessions, never call GameInstance Init or save APIs, and block account writes. They inspect real components and actor routes under Unreal automation; NullRHI does not prove audible buffers, renderer voice counts or listening quality. Both audio tests passed in the first 20/21 suite and the final 21/21 suite. The one initial failure was an economy test fixture that omitted the Director's offer-seen flags when manually accepting events. A fixture-only correction and 4.71-second incremental build produced the final 2.318785-second suite with no warnings, failures or unrun tests.

The [focused receipt](validation/2026-09-13-audio-hooks.json) binds exact final C++/Python source, Editor DLL, imported audio assets, 16 source hashes, logs and test results. It independently compares all ten original WAVs with immutable commit a9da95e18be56fe55b230b0ad48b4fad2317360b. The first failing suite's log is retained; its report, original failing test source and DLL were not copied or hashed before the rerun, and the receipt states that limit.

Package 9 remains a historical source4178 artifact and does not contain this change. Human listening and game-feel checks remain open under [ISS-08 in the canonical issue log](KNOWN_ISSUES.md#iss-08).
