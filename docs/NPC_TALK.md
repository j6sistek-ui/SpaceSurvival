# Push-to-talk conversations (NPC talk)

Owner decision, 2026-10-10: the station crew and the villain can be spoken to. Hold **T** (keyboard) or **R3** (pad),
speak into the microphone, release. Your words appear as a caption ("You: ..."), and the character answers in a
caption of their own. Text only for now; voice out is "maybe later, if I like the dynamic". No cloud: both halves
run on the player's machine as hidden sidecar processes the game starts and stops.

| Piece | What | Where |
|---|---|---|
| `USSNpcTalkSubsystem` | microphone, the two servers, one conversation per character, the HTTP calls | `Source/SpaceSurvival/Public/SSNpcTalk.h`, `Private/SSNpcTalk.cpp` |
| `ASSGameMode::BeginTalk / EndTalk / TalkTarget` | who is listening, the game-state digest, the captions | `SSGameMode.cpp`, end of file |
| `ASSPlayerController::PlayerTick` | the key: held = listening, released = send | `SSGameMode.cpp` |
| `ASSHUD` | the "You:" box, the crew answer box (deck teal), the status line, the walk hint | `SSHUD.cpp` |
| `Config/DefaultNpcTalk.ini` | executables, the flight and station models, ports, reply length, memory | |
| `Content/SpaceSurvival/NpcTalk/Personas/<Name>.txt` | one system prompt per character; `_Default.txt` for the rest; `{Name}` is substituted | |
| `SpaceSurvival.NpcTalk.Encoding` | automation suite: the WAV, both request bodies, both answers, the mesh-name rule | `SSNpcTalkAutomationTests.cpp` |

## Who you can talk to

- **On foot:** the crew member within 3.5 m that the walker is facing. Characters are identified by their mesh
  (`SK_Dread` is Dread), so a placed crew actor needs no extra property. The walk hint says "hold T / R3: talk to
  Dread" when someone is in range. Drones are skipped.
- **In the ship:** the villain, but only after he has transmitted at least once in the current run (owner: "after the
  first time the director speaks, you can talk back"). Before that the key answers "Nobody is on the line. He talks
  first." His replies use his own ember caption, not the crew box; his persona mirrors the pilot's tone, so profanity
  is answered in kind. Measured 2026-10-10 on stock Qwen 1.5B (`M:\Local AI\NPCTalk\test\villain_probe*.py`): handed
  the pilot's bare sentence it refused the first swear with assistant-speak; with the sentence framed as quoted radio
  traffic plus "answer them now, as the Director" it stayed in character and swore back. That framing is what the
  subsystem sends. The owner first ruled out abliterated models for release, then, later the same day, chose one for
  the test period ("I'll decide later if it's a risk for release"): `Huihui-Qwen3.5-4B-abliterated` Q4_K_M, 2.7 GB,
  Apache 2.0 base, launched with `--reasoning off` because Qwen3.5 thinks out loud otherwise (and `ParseReply` strips
  `<think>` blocks regardless). The stock 1.5B was removed from the drive at the owner's request. Before any release:
  decide this. A stock 4B or Mistral 7B Instruct (Apache 2.0) is the shippable fallback if the answer is no.

## Two models, one at a time

Owner's split, 2026-10-10: "the space station is less game, more chat. Load the better model at space stations;
initiating a wave kills the server until you land at a space station again. The Director can live on the small
model, active during waves." So:

| Where | llama-server | Set by |
|---|---|---|
| Walker on the deck (hangar shown, or landed on the pad) | `StationLlamaModel`, started on arrival so the first question is quick | `SetContext(Station)` after the walker spawns |
| Departure (any launch: next wave, new run, free flight) | stopped; the GPU is the game's again | `SetContext(Flight)` in `BeginDeparture` |
| The villain's first line of the run | `LlamaModel` (the 4B), started then so he can be answered | `EnsureServers` in `ShowVillainLine` |

whisper-server stays up throughout (CPU, 0.5 GB). A freshly started llama-server refuses or answers 503 while it reads
its model off the disk; `PostToLlama` re-posts the same question every 2 s for up to two minutes with the status line
"<Name> is still waking up, hold on...", so a question asked on arrival is answered, late, not lost.

## Optional pack

None of this is gameplay (owner: "it's all extra"), so the sidecars and models are an optional download, not part of
the core package. `IsInstalled()` checks once at start-up that both executables and both models exist; without them
`IsEnabled()` is false, `TalkTarget()` is empty, the HUD never mentions the key, no server starts and nothing is logged
beyond one line. The core package carries `DefaultNpcTalk.ini` pointing at where the pack would go.

## The loop

1. Key down: `BeginTalk` picks the target, refreshes the digest (second-person facts: wave, hull, credits, kills) and
   opens the default microphone through the engine's `FAudioCapture`.
2. Key up: the samples are mixed to mono, resampled to 16 kHz, written as a WAV and posted to whisper-server's
   `/inference`. Under a quarter of a second of audio is rejected as "Nothing heard".
3. The transcript is shown, appended to that character's history (last `HistoryTurns` exchanges) and posted with the
   persona + digest to llama-server's `/v1/chat/completions`, `max_tokens` capped, no streaming.
4. The reply is shown for 6 to 16 s depending on length. Any failure is announced in plain words and the loop resets.

Measured on the owner's RTX 5080 (`M:\Local AI\NPCTalk\README.md`): transcription about 1 s on the CPU, replies in
0.1 to 0.2 s at ~400 tokens/s with 1.4 GB of VRAM for Qwen2.5 1.5B.

## Adding a character

Write `Content/SpaceSurvival/NpcTalk/Personas/<Name>.txt` where `<Name>` is the mesh name without `SK_`. Say who
they are, what they know, what they do not know, and how they talk; forbid assistant phrasing explicitly, because
a small model drifts into it otherwise. Facts that change go in the digest (`NpcDigest`), not the persona. The owner
writes these one at a time after testing each.

## Limits and later

- No lip sync is possible: no crew member has jaw bones or mouth shapes. Talk gestures only.
- The sidecar paths in `DefaultNpcTalk.ini` are this machine's. A package must carry `bin/` and `models/` beside the
  executable and point the ini at them; non-asset persona files need `DirectoriesToAlwaysStageAsNonUFS`.
- Typed fallback, characters who speak first (bartender, merchants) and voice out are owner-listed follow-ups.
- Owner ideas, not scheduled: a boast from the villain when a run ends (the `VillainEpitaph` slot exists for his last
  word on a death); a small local player profile, how often the pilot swears across runs, so how vulgar he may get
  tracks the player's own habit, or simply a setting. The language-mirroring today is per line only.
- Licences: whisper.cpp and llama.cpp MIT, whisper small.en MIT, Qwen2.5-1.5B-Instruct Apache 2.0. Verify the exact
  model file before any release (docs/production/SOLUTION_CATALOG.md rule).
