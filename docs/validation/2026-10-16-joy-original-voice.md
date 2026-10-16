# Joy original voice and cache revision — 2026-10-16 UTC

Owner request: replace Joy's robotic/standard delivery and reserve distinct voices for Astra and Joy within the cast. This does not establish global uniqueness of a synthetic voice. RPT-20261015-01 remains open for listening and expressive laughter.

## Result and provenance

- Joy now uses an original adult synthetic reference designed locally with Qwen3-TTS VoiceDesign 1.7B, revision `5ecdb67327fd37bb2e042aab12ff7391903235d3`, seed `20261016`. The description requests a warm medium-low, relaxed bartender delivery; it supplies no real-person recording or Cyborg reference. Generation ran offline on CPU, leaving the owner's Blender/GPU work alone.
- The new reference is 3.76 seconds, mono PCM16 at 24 kHz; SHA-256 `4ea4ddf6b41e0b1268adfdc8148a1b83115d41a101e0ade63214fd692c90ee69`. Settings remain `speed=0.9`, `treatment=none`; `cache_revision=4ea4ddf6b41e0b12` selects new clips.
- The old Joy reference, an unused velvet Cyborg audition rather than Cyborg's selected bright voice, is retained privately: SHA-256 `6e8b3abbb150b4d7041255dac164b5e89e9eb113f26b05a3d80cea7a963c2de2`. All other voice WAV/settings hashes remain unchanged. Astra retains her separately designed reference; exact-name routing and no aliases targeting Astra/Joy prevent a shared role fallback from selecting these voices.
- Existing CPU LuxTTS rendered nine new Joy clips: one greeting and eight bar replies. All retained clips contain the requested words under local whisper.cpp transcription; failed first takes and slower retries are preserved. The prior 26 Astra clips are unchanged. Nine revision-key cache entries were added; old cache files were not removed or overwritten.

## Cache repair and checks

Replacing a WAV at the same filename previously left its cache identity unchanged. Optional `cache_revision` now participates in both native lookup and Python prerender naming. Omitted/empty revisions preserve every legacy key, including Astra and the Director.

- `Tests/TestNpcVoiceCache.py`: six CPU checks pass, including actual stale/revised cache read/write, reuse on the next run, unaffected Astra entries and shared UTF-8 golden hashes. The source workflow runs this regression suite without TTS model dependencies.
- `SpaceSurvival.NpcTalk.Encoding`: one native test passes, zero warnings/failures/skips, using a separate NullRHI/NoSound process and isolated user directory.
- Isolated WorktreeBuild8 passes (65.09 s); canonical integrated Build15 passes (75.10 s), module SHA-256 `35b7379d28476dcf5a0e75a64171231b6122253fec19fb2369800c4ee81e38c6`. Existing engine API deprecation warnings remain; no build errors.
- The 49 structural checks, Python compilation, source-format validation (26 meshes/17 WAVs), scoped clang-format22, documentation navigation/counts and whitespace checks pass. This is source/local Editor work; no map, mesh, animation, packaged build or release was changed by this follow-up.

## Listen and remaining verification

Private review folder: `C:/Users/j6sis/SpaceSurvival/.agent/local/Waitress_20261015/Voice/JoyOriginal_20261016`.

Open `index.html`; play **new Joy greeting**, then the **same-line old/new comparison**, then **Astra**. `Joy_New_00.wav` is a direct standalone sample. Two exchange clips use one-second editorial gaps and omit simultaneous drink animations: they are listening aids, not runtime synchronization evidence. Nothing autoplays.

`Design.json`, `RuntimePreview.json`, `Adopted.json`, `AuditionVerification.json`, `NativeEncoding/index.json` and build logs retain the bounded evidence. Prior files in `PreviousJoy` permit recovery. HTML links, PCM/WAV hashes, exact exchange joins and absence of rail clipping pass file checks. Automatic browser preview rejected local file URLs; no alternate proxy/surface was used. The page was not rendered or heard by the agent.

Next owner check: is Joy natural and clearly different from Astra? Lead retains tuning, laughter and native audible mix verification. Word coverage and NoSound automation do not prove naturalness, emotional quality or final in-game sound. Restart the game/talk sidecar to load the new voice settings. Both PR74 and the broader bar work remain draft/unmerged and incomplete.
