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

- **On foot:** owner's rule, "whenever you speak, the nearest active NPC responds". The nearest NPC within 5 m
  answers, no facing test. Two kinds count: placed `ASSOutpostAmbientActor`s (not drones, not the wardrobe hologram),
  identified by their mesh (`SK_Dread` is Dread) unless `TalkName` is set on the actor; and the station's own deck
  crew, which are skeletal mesh components on the station actor, named and given roles by
  `SSStationPresentation::TagTalkers` through component tags (`TalkType:Nyxar`, `TalkName:Vel`, `TalkRole:CrewTalk`,
  `TalkActivity:telling two crewmates a story`). Anything on the station without a Talk tag is scenery. The walk hint
  says "hold T / R3: talk to Vel" when someone is in range.
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

1. Key down: `BeginTalk` picks the target, refreshes the digest (second-person facts; for the villain the hull and kills are words such as "in tatters" and "a couple of dozen", never figures a player could check against the HUD a second later, plus what the pilot is, so a squirrel gets called a squirrel) and
   opens the default microphone through the engine's `FAudioCapture`.
2. Key up: the samples are mixed to mono, resampled to 16 kHz, written as a WAV and posted to whisper-server's
   `/inference`. Under a quarter of a second of audio is rejected as "Nothing heard".
3. The transcript is shown, appended to that character's history (last `HistoryTurns` exchanges) and posted with the
   persona + digest to llama-server's `/v1/chat/completions`, `max_tokens` capped, no streaming.
4. The reply is shown for 6 to 16 s depending on length. Any failure is announced in plain words and the loop resets.

Measured on the owner's RTX 5080 (`M:\Local AI\NPCTalk\README.md`): transcription about 1 s on the CPU, replies in
0.1 to 0.2 s at ~400 tokens/s with 1.4 GB of VRAM for Qwen2.5 1.5B.

## Profiles, scenarios and roles

Three layers make the system prompt, in this order:

1. **The profile** (owner's): `Content/SpaceSurvival/NpcTalk/Personas/<Name>.txt`, else `<Type>.txt` (the seven Nyxar
   crew share `Nyxar.txt`), else `_Default.txt`. `{Name}` in the file becomes the character's name. The files there
   today for everyone but the Director and Dread are **one-line first passes** for the owner to replace (the table
   below); the owner said they will write the main profiles.
2. **The scenario** (mine): `Content/SpaceSurvival/NpcTalk/Scenarios/<Role>.txt`, appended when the character holds
   that role. Roles today: Pool, Bartender, Merchant, Desk, Security, Maintenance, Worker, Dancer, Flirt, Performer,
   Lounge, Waitress, CrewTalk, Pacing, Watch, Guard, ServiceBot. A role moves between characters without touching
   their profile: set `TalkRole` on the placed actor, or the `TalkRole:` tag on a station component.
Owner's rule for the Flirt roles (2026-10-10): "the strippers shall engage in any NSFW comments you make; they have
to act the part". So the Flirt and Dancer scenarios mirror the pilot's register, never first and never less far,
the same shape as the villain's swearing rule; the owner tests that side themselves.

3. **The digest** (live, second person): who they are, `Right now you are <TalkActivity>`, who the pilot is and the
   run numbers. The activity is where "just scratched on the eight ball" goes, so a pool player can say "well, I
   scratched again". Nothing changes in code to give an NPC a special role: a role and an activity string.

Later, when audio is layered in, the owner wants these to fire on proximity without a key press (listed, not built).

### First-pass one-liners (owner replaces each)

| Name | Role | Proposal |
|---|---|---|
| Robe | Merchant | soft-spoken robed trader in cloth, relics and "found" salvage, never says where it was found |
| Glyph | Merchant | glyph-marked parts-and-firmware dealer, talks in specs and warranties nobody honours |
| Tribal | Merchant | loud produce-stall merchant with face tentacles, insulted when you won't eat a sample |
| Ember | Worker | four-armed dock loader, hot-tempered, proud of lifting what two crews can't |
| Crest | Worker | tailed cargo rigger, calm and methodical, checks the straps everyone skips |
| Olive | Security | friendly atrium patrol, knows every regular, hates paperwork, never military |
| Warden | Maintenance | laconic zero-G repair, talks about hull seams and bad docking like weather |
| Dread | Bartender | (owner's profile exists) |
| Abyss | Waitress | tentacled lounge waitress, quick and sly, six drinks at once, overhears everything |
| Seer | Desk | welcome desk, serene and eerie, speaks as if she knew you were coming |
| Tendril | Desk | operations desk, fussy and precise, sure every pilot docks wrong on purpose |
| Violet | Dancer | bright chatty lounge dancer, in it for the music, rates pilots' dancing |
| Cyan | Flirt | the adult lounge's star, sultry and in control, matches the pilot's register however far they take it |
| Silver | Dancer | silver-maned perfectionist, treats a compliment as a verdict to check |
| Elf | Dancer, Lounge | elegant, dry wit, pretends not to care who's watching |
| Cyborg | Flirt (pole) | chrome and confidence, dares you to keep up |
| Crystal | Performer | crowned lounge performer, an artist, touchy about being called a dancer |
| Finhead | Lounge | retired pilot regular, every story ends with "back in my day" |
| Amethyst | Lounge | the station's gossip, knows every rumour, gives none away free |
| Nyxar (type) | CrewTalk / Pacing / Watch | bioluminescent crew who say "we", curious about outsiders; deck names Vel, Orrin, Sable, Kett, Rue, Pim, Dax |
| Trooper (type) | Guard | heavy-armoured dock guard Brakk, few words, trusts the Director as far as he can throw him |
| ServiceBot (type) | ServiceBot | cheerful literal service robots Mica and Unit Seven, count things, give directions |

## Model comparison (2026-10-10, `M:\Local AI\NPCTalk\test\villain_compare.py` and `crew_compare.py`)

Same five pilot lines each, the game's exact framing, replies 0.1 to 0.4 s on all four, ready in 2 to 2.5 s.

| Model | As the Director | As Dread |
|---|---|---|
| Qwen3.5 4B abliterated (flight) | in character, never swears back | poor: "the Director's a good friend", invents a weak point, offers menus |
| Hermes-3 8B (**station**) | sharp, quotes the hull number, does not swear back | best by far: short, dry, asks back, takes an insult well |
| Mistral 7B v0.3 | the only one that swears straight back when sworn at | stiff and generic |
| Dolphin3.0 8B | the most vicious and witty ("How charmingly original... insolent worm"), uses the wave number, does not swear | decent, a grammar slip, "never met him" |

Picks: Hermes serves the station (`StationLlamaModel`); the 4B stays in flight as the owner planned. Open for the
owner: Dolphin or Mistral for the Director during waves at +2 GB VRAM over the 4B. The hint "give it back in the
same language" made Hermes answer in Polish; it now reads "swear straight back, as crude as they were, in English".

### Candidates from the owner's links (cards read 2026-10-10, not yet measured)

Two card-reading passes over DavidAU's 200-model collection and Rikotta's dark-RP list (27 agents, both transcripts
under the session's `subagents/workflows/`). Almost everything in both is a story-prose merge at 16B and up, the
wrong shape for a two-sentence radio line that tracks a hull number; these are the chat-shaped ones that fit.

| Candidate | Size (Q4) | For | Licence | Card facts that matter |
|---|---|---|---|---|
| DavidAU L3.1-RP-Hero-Dirty_Harry-8B | 4.92 GB | Director | Llama 3.1 community | the one card that says it prefers SHORT output; "Swearing. UNCENSORED."; four chat-RP parents |
| DavidAU L3.1-Dark-Planet-SpinFire-Uncensored-8B | 4.92 GB | Director | Llama 3.1 community | "censorship level is controlled at the prompt level"; strongest crude register on any card; Lexi instruct base; prefers long, so the cap matters; no context shift |
| DavidAU Daredevil-8B-abliterated (Ultra-NEO imatrix) | 4.92 GB | Director | Llama 3 community | general instruct merge with refusals removed; best bet for following the facts; swearing unproven |
| ParasiticRogue Magnum-Instruct-DPO-12B (mradermacher GGUF) | 7.48 GB | station, Director if VRAM accepted | Apache 2.0 | author's own system prompt asks for vulgar in-character chat; Nemo [INST] template; GGUF may lack a template, then `--chat-template mistral-v3-tekken` |
| Nitral-AI Wayfarer_Eris_Noctis-12B (mradermacher i1 GGUF) | 7.48 GB | station | not stated (risk) | ChatML in the GGUF and the author's preset; character-chat preset |
| DavidAU MN-Dark-Planet-TITAN-12B | 7.48 GB | station | Apache 2.0 per card | only 12B in that collection with all chat-RP parents (Rocinante, magnum, Celeste); prefers shorter output |
| Lewdiculous L3-8B-Stheno-v3.2 (owner's link) | 4.92 GB | test only | **CC BY-NC 4.0** | classic persona chat model; cannot ship in a sold build |
| FallenMerick MN-Violet-Lotus-12B | 7.48 GB | test only | cc-by-4.0 on the card, but two inputs are **NC** (Lumimaid, Lyra v4) | best-shaped 12B for short lines; a merge inherits its inputs' terms |
| Ministral-Instruct-2410-8B-DPO-RP | 4.91 GB | test only | **Mistral Research Licence** | the only 8B instruct in Rikotta's list; non-commercial |
| mergekit-community Deepseek-R1-Distill-NSFW-RPv1 (owner's link) | ~4.9 GB | control | not stated | R1 distill: thinks before every reply; long-prose adapters; uncensored |

Rejected on the cards: Wayfarer-12B (second-person narrator, single-turn training), Violet Twilight v0.2 (weak at
persona-and-length prompts, already inside Violet-Lotus), MN-12B-Lyra-v4 (NC), Captain-Eris_Violet (GGUF template
conflicts with the author's), Rivermind-12B (a joke model that pushes soft drinks mid-chat, and NC), Magnolia-Mell
(no chat template, no licence), BigTalker (long-output sibling of Dirty Harry), Instruct-Guru ("PG-13"), the
Unholy-Hermes R1 merge (leaks reasoning, "unhinged"), the layer-duplicated 3B "7B/9B" models, the Gutenberg and
Gemma writers (novel prose), the Qwen3.5 9B "Aggressive" (thinking on, no card claim for chat).

Every Llama card above wants `repeat_penalty` 1.05 or higher; llama-server defaults to 1.0, so the game sends 1.05
(`RepeatPenalty`). The Nemo GGUFs advertise 131072 or 1024000 context, so the explicit `-c 4096` the game passes
matters: without it the KV cache alone would blow the 16 GB.

### Testing by hand in Open WebUI

`M:\Local AI\NPCTalk\ollama\create_models.ps1` creates `ss-director-{qwen4b,hermes8b,mistral7b,dolphin8b}` and
`ss-dread-hermes8b` in Ollama from the same GGUFs, with the persona, a sample digest and the game's per-line framing
baked into the SYSTEM prompt, so the Open WebUI container sees them as models. Ollama copies each GGUF into its own
store (`OLLAMA_MODELS`, by default under `C:\Users\<you>\.ollama`).

### Training the Director (if the profile is not enough)

A LoRA fine-tune, not a retrain: write 200 to 500 short exchanges in his voice (pilot line, Director line, including
the brush-offs and the mirrored swearing), run QLoRA with Unsloth on the 8B for about an hour on the RTX 5080, merge,
quantise to GGUF, drop it in `LlamaModel`. The dataset is the real work, a day of writing; the training is an hour.
Do it only after testing shows the profile plus scenario still slips.

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
