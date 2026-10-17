# NPC helper reuse — October 17, 2026

Issue RPT-20261016-17; source follow-up in draft PR74, atop unchanged foundation PR78. No merge or packaged release.

## Trigger and change

Stopping and restarting Play can keep local speech, dialogue and voice helpers alive. The foundation compared incomplete startup identities: speech had no configuration key, dialogue omitted its executable, port and automatic GPU allowances, and voice omitted its engine/script/Python and reference-directory paths. Changing those settings could leave requests going to an old port or voices served from an old directory. This is a source-confirmed configuration defect; it is not claimed as the cause of the owner's earlier robotic-voice feedback.

The kept helpers now include these startup settings in their reuse identities. Speech preserves its identity across parking and is discarded when the next session's settings differ; the active speech path also checks it. Dialogue retains its existing restart path with the complete key. Voice includes its complete launch arguments, each reference path, loaded speed/treatment/cache revision and existing modification timestamps. Sorting keeps unchanged profiles reusable regardless of enumeration order. No voice, dialogue model, port or GPU setting was changed. No new Blueprint interface, plugin or dependency.

## Verification

- Isolated PR74 build succeeds in69.90s; canonical combined build succeeds in89.65s. Existing engine/plugin deprecations and non-preferred compiler warning remain.
- Both modules pass the focused `SpaceSurvival.NpcTalk.HelperIdentity` test:1 pass,0 failed,0 not-run,0 test warnings. It covers changed ports, executables, speech model/threads, GPU allowances, voice paths and loaded profile revisions/settings, plus unchanged/restored settings and stable profile order.
- Tests run in separate owned NullRHI processes with isolated user storage, no sound, AI services disabled and no microphone or actual helper request. Two ShipCore startup messages appear at Warning severity outside each zero-warning test result. Owned processes7868 and44584 exit0. Live process restarts, voice listening, physical input and gameplay are not established by this test.
- Each checkout passes49 source structural checks and13 source-digest tests; scoped installed clang-format22 and whitespace checks pass. Exact-head container CI is checked after publication.

Canonical editor module`d248d14e0884deee2a394534caa07f6c687336f59f46136f4346dbce6a4624e4` supersedes`b9a9d71e`; station remains`c3dd6ea9dad3cf85e7d8451546cb95e33acc39013c3f8774c00ecb318bbc21ca`. All226 other guarded native files are unchanged. The three canonical source files were backed up and patched by exact reviewed hunks, preserving diagnostics and other owner work. Four existing ShipCore DLL/PDB build outputs were rebuilt; the other269 guarded plugin files, including plugin sources, remain unchanged. A hash read during linking encountered a temporarily absent PDB; the completed-build audit above is authoritative.

Private receipts: `.agent/local/HelperReuse_20261017/Verification.json`, `Adoption.json`, `Source.patch`, `Before/`, worktree/canonical build logs, test reports and launch/exit records. No scene recipe or old native artifact was replayed.

## Still open

Joy/Astra listening and natural laughter remain separate owner/lead checks. Seated clothing and the exterior composition remain open. Foundation boarding/pilot scope still needs reconciliation before readiness; PR73 and new hero/squirrel work remain held. No merge, package or Phase1 completion claim.

## Process lifetime follow-up — October 16 local time

A separate development-only `SpaceSurvival.NpcTalk.HelperLifetime` test exercises the actual ParkServers, AdoptParkedServers, expiry and shutdown paths with five inert, short-lived Python processes. It requires an unattended NullRHI editor and refuses to touch an existing parked helper set. Each process is tied to the test editor's Windows job, also exits by itself after30seconds, and has an independently opened observation handle. Cleanup stops only fixture-owned processes. The generic game instance is never initialized; no production persistence, microphone, network listener, AI model or TTS engine is started.

The same three live handles survive an unchanged-session handoff. Changing speech threads and voice threads terminates the incompatible speech/voice processes; dialogue remains available for its existing EnsureServers identity check. Expiry terminates the parked dialogue process, an untied helper is refused, and explicit shutdown terminates the active voice process. This establishes OS process lifetime behavior for the fixture, not model startup, network health or audible quality.

The first isolated build failed because Windows IsProcRunning takes a non-const handle reference; the fixture loop was corrected without runtime changes. The next build succeeds in5.41s. The focused Helper suite passes2 tests,0 failures,0 not-run and0 test warnings. The lifetime case takes0.098s; both cases run in owned process36264, which exits0. Two pre-existing ShipCore startup warnings remain outside the passing test result. Installed scoped formatting,49 structure checks,13 digest checks and whitespace validation pass.

Tested isolated module: `3a48ef3a973e78243c75d995062587eb0b66a65b193f4172b7381f2bcd390322`. The new source delta is test-only; the canonical module stays `d248d14e` and station stays `c3dd6ea9`. All227 guarded canonical native files remain unchanged. Two exact backed-up source patches preserve the canonical diagnostics additions. There is no new gameplay build, content import or package in this follow-up. Private evidence remains `HelperReuse_20261017/Lifetime*` (build1 failure, build2 success, report, exit, source patch and guard).

Actual model/server startup and request health, human listening, bar input and appearance remain open. The owner explicitly reports the tray/face check Not tested yet; that is not a pause on independent work.
