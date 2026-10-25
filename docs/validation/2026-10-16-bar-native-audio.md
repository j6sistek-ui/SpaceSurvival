# Native staff-shot audio — 2026-10-16

Ordinary Play now has a captured native master mix for two complete Astra/Joy staff-shot cycles. This checks actual `CrewRadio` procedural playback, rather than inspecting the TTS source files. The unchanged combined module is `cd9ed5339257ba3419d5fd42642dfb9d1c7d3641312279df9421864823db0cf0`; station map is `ddc040c15d724938e5a15ba2e9553cb62938e74b527388edeef28c48d55e8670`. No source, voice selection, native asset or owner configuration changed for this review.

## Evidence

- Separate hidden editor, private user directory and copied voice cache; voice port18703, LLM/STT disabled and no microphone request. Installed CPU voice playback uses the existing approved references. Two nearby idle breaks were accelerated only in memory; original intervals and ambient flag were restored.
- 1,418 samples over89.301 seconds capture two complete routines and six alternating spoken lines. The 48kHz stereo mix peaks at-12.09dBFS with zero clipped samples. No sample has speech playing while both staff shot glasses are visible. This is a sampled timing check, not a lip-sync or whole-game mix test.
- CPU Whisper transcription of all six segments from the **native recording** recovers every expected word. The second exchange includes Astra's spoken “Ha!”; this does not establish natural nonverbal laughter or listener preference.
- `StaffNativeMix.png` was inspected. It shows the existing bar and both staff; no presentation or lighting changes were adopted in this audio pass.
- Final preservation passes193 protected files and72 original production cache files, with clean map/content packages. The owned editor exits cleanly. Native assets, saves, original voice references/settings and shared cache remain unchanged.

Private evidence: `.agent/local/BarAudio_20261016/BackgroundAudio/{Capture.json,AudioAnalysis.json,Transcripts.json,StaffNativeMix.wav,StaffNativeMix.png,FinalPreservation.json}`. WAV SHA256:`89f2b886392316ffa5128fbf3554c20bc443ef3eb81f658e649c8db805262513`.

## Retained failures and limits

The first native master recording was completely silent, despite valid source-clock samples. Installed engine defaults mute unfocused audio. A separate repeat enables background audio and disables foreground-only throttling through that review process's command-line configuration; no owner/global INI is edited. The silent run is retained under the parent `BarAudio_20261016` directory and is **not** audible-playback evidence. Earlier Python property/name lookup failures are also retained; native `GetIni` verifies the final private configuration before playback.

Owner listening, perceived uniqueness/naturalness, expressive laughter, physical input, busy-room mix, performance and packaged playback remain open. No claim of human listening is made from signal analysis or transcription. The pending owner table in KNOWN_ISSUES remains a feedback log, not a gate on continued work.
