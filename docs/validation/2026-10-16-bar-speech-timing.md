# Bar speech countdown repair — 2026-10-16 UTC

RPT-20261015-01. The owner authorized continued bar synchronization work while
keeping GPU memory available. This is a bounded C++ timer repair, not new voice,
animation or character content.

## Defect and change

`ASSGameMode::UpdateCrewRadio` started a ready PCM clip, assigned its full
duration, then immediately subtracted the current frame's `Dt`. That elapsed
time preceded `Play()`, so it shortened the new clip's playback budget. For
example, Joy's cached 2.234-second staff-meeting reply began with only 1.934
seconds remaining after a 0.3-second frame. A clip shorter than its start frame
could be stopped in that same call.

The function now returns after starting the clip and consuming `CrewRadioReady`.
Later updates retain the existing countdown and expiry behavior. The shared
speech gate therefore retains the full new clip duration. This does not change
the two-second banter minimum, same-frame drink-animation start, grips, animation
speeds, voice selection or cache identity. Normal-frame errors may be masked by
the cached trailing silence; no audible truncation was reproduced by this audit.

## Regression and validation

The existing `FSSAudioFirstState` test in `SSAudioAutomationTests.cpp` injects
ready PCM into the actual `UpdateCrewRadio` path with the fixture muted. It checks
a one-second clip through start, later countdown and expiry, plus a ten-millisecond
clip that is shorter than its start frame. Both cases require the ready PCM to
be consumed. The test uses no TTS service and makes no listening assertion.

- Isolated `Scripts/Build.ps1 -Target Editor`: WorktreeBuild9 **PASS**, 182.90s.
  Existing engine/plugin deprecation warnings are outside the changed lines.
- Scoped clang-format check, `git diff --check`, and
  `python Scripts/CheckProject.py`: **PASS**, including 49 structural checks.
- First native `SpaceSurvival.Integration.AudioFirstPlayMix` run: assertions
  succeeded, but the strict gate **FAILED** on two
  `SS_STATION_WARP_PLACEMENT_REFUSED reason=welcome footprint/support` warnings
  from the empty audio fixture's station placement. Report: succeeded0,
  succeededWithWarnings1, failed0, errors0; duration47.38s. Retain this result.
- Isolated native retry: **PASS**, one test, zero warnings/errors/failures/skips,
  8.23s; process exit0 at03:52:45Z. The same test/module used the existing
  `-SSLegacyStation` flag, a fresh user directory and a separate report. This
  selects the small native station rather than the licensed outpost; no runtime
  placement code or warning handling is changed. Both runs use CPU-only NullRHI,
  open no rendered editor and do not establish heard audio.
- Canonical integrated Build16: **PASS**, 179.58s. Module SHA-256:
  `29b1a46ff25e006a5b69ec37bb74752b6f67e15974406912e7b02e1c3577bcc9`.
  Existing engine/plugin deprecation warnings remain. Canonical formatter findings
  at previously untouched GameMode lines are not repaired by this one-line change;
  the scoped worktree formatter pass above is the bounded formatting evidence.

Private evidence root:
`C:/Users/j6sis/SpaceSurvival/.agent/local/Waitress_20261015/Voice/Laughter_20261016`.
`TimingAudit.json` records the earlier source/cache and animation-clock review;
this later start-frame finding supersedes its no-definite-timing-defect conclusion
only for the countdown. Build logs are `WorktreeBuild9.log` and
`CanonicalBuild16.log`; the first native report is
`NativeAudioTiming/Report/index.json`. The clean retry is recorded in
`NativeAudioTimingIsolated/Report/index.json` (03:52:41Z) and sibling `Process.json`.

## Scope and remaining acceptance

Only `SSGameMode.cpp`, its existing audio regression and documentation change.
Maps, native assets, animation clips, cached PCM, accepted voice references and
personality profiles are untouched. No cook, package, publication or merge.

Unattended/automation speech normally bypasses voice playback before cache lookup;
the injected-PCM regression validates the countdown without claiming live speech.
Native audible mix, expressive laughter, hand/glass contact during shared shots,
Astra's seated shorts and physical-input/performance acceptance remain open.
The lead owns those checks and repairs; GPU-dependent work remains held while the
owner needs VRAM. Prior aligned animation-clock samples do not close these gates.
