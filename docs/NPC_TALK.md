# Push-to-talk conversations (NPC talk)

**October20 local storage:** `Config/DefaultNpcTalk.ini` now uses `C:/Users/j6sis/SpaceSurvival/LocalRuntime/NpcTalk` for speech/dialogue, `LocalRuntime/LuxTTS` for voice Python/source, and `LocalRuntime/DirectorVoice/cache` for prerendered lines. The voice server uses the sibling `LocalRuntime/HuggingFace/hub` when present, with offline mode enabled before model imports; standalone installs without this directory retain the usual cache. Model identities, voices, GPU settings and ports are unchanged. Earlier M paths below are historical provenance, not the current launch configuration. [Migration verification](validation/2026-10-20-storage-consolidation.md).

**October17 model check:** The current local speech, voice and station-dialogue models pass isolated CPU health/inference checks. Astra/Joy generated test lines transcribe exactly; the voice engine takes about37s to become ready from cold in this probe. Game startup/reuse, microphone use and listening quality remain separate checks. Fresh test recordings are under `.agent/local/HelperHealth_20261017/Run/`; existing voices and production cache are unchanged. [Evidence](validation/2026-10-17-npc-helper-reuse.md#real-model-health-and-inference).

## Kept helper settings — October 17

A Play restart can reuse unchanged local helpers. Changing speech/dialogue ports, executables, speech models or GPU allowances now invalidates the affected helper. Voice reuse also checks the Python/script/engine/reference-folder paths and loaded profile speed, treatment and cache revision. Keep using a new `cache_revision` when replacing a reference; it now invalidates the parked voice helper even when file timestamps match. This is startup/restart configuration handling, not a live file watcher. [Validation and limits](validation/2026-10-17-npc-helper-reuse.md).

Placed ambient crew expose **Conversation Enabled** (default true). Disable it for unavailable characters such as the passed-out bar patron; fresh/cached prompts, actions and speech are suppressed and an existing conversation disengages. Idle animation and identity remain unchanged. Other crew keep conversation enabled. [Saved verification](validation/2026-10-16-resting-patron-interaction.md).

## Optional diagnostics — October 16

Settings > Graphics > Diagnostics adds a sanitized, read-only view of talk phase, local LLM/STT process presence, voice readiness/queue, voice request failures/restarts and whether a talk error is present. Reading it neither starts helpers nor sends requests. Running is not model readiness; counters are session-local and do not represent all engine errors. Paths, endpoints, prompts, transcripts and response bodies are excluded. [Validation and remaining checks](validation/2026-10-16-runtime-diagnostics.md).

## Astra profile, voice and staff banter — October 15

Astra has her own `Personas/Astra.txt` and synthetic `Voices/Astra.wav`/settings; Waitress type/role files stay reusable. Joy now has a fresh original synthetic reference reserved for her; her rejected velvet audition remains only as a recovery/listening baseline. Their optional nearby bar break alternates the existing voice channel and8 shuffled authored exchanges. The side conversation panel records transcripts and replies when shown, below the radar; it does not change microphone controls or train a LoRA. [Controls, files and limits](production/WAITRESS_BAR_SERVICE.md).

## Waitress actions — October 15

The authored bar waitress uses the existing talk/action selection: Order a drink, Have a drink with me, Sit with me, and Dismiss. Component tags select her Waitress profile; source service states set truthful current activities and use the existing spatial voice/caption channel. Keep the normal talk pack enabled and leave the title menu before using actions. [Service behavior and current validation limits](production/WAITRESS_BAR_SERVICE.md).

Owner decision, 2026-10-10: the station crew and the villain can be spoken to. Tap **T** (keyboard) or **R3** (pad),
speak into the microphone, tap again to send (owner: R3 was hard to keep holding; a hold/tap menu option and
remapping are later). Your words appear as a caption ("You: ..."), and the character answers in a
caption of their own. The crew answer in text; the villain also speaks (see "The villain's voice"). No cloud: every
piece runs on the player's machine as hidden sidecar processes the game starts and stops.

| Piece | What | Where |
|---|---|---|
| `USSNpcTalkSubsystem` | microphone, the two servers, one conversation per character, the HTTP calls | `Source/SpaceSurvival/Public/SSNpcTalk.h`, `Private/SSNpcTalk.cpp` |
| `ASSGameMode::BeginTalk / EndTalk / TalkTarget` | who is listening, the game-state digest, the captions | `SSGameMode.cpp`, end of file |
| `ASSPlayerController::PlayerTick` | the key: first tap listens, second tap sends | `SSGameMode.cpp` |
| `ASSHUD` | the "You:" box, the crew answer box (deck teal), the status line, the walk hint | `SSHUD.cpp` |
| `Config/DefaultNpcTalk.ini` | executables, the flight and station models, ports, reply length, memory | |
| `Content/SpaceSurvival/NpcTalk/Personas/<Name>.txt` | one system prompt per character; `_Default.txt` for the rest; `{Name}` is substituted | |
| `SpaceSurvival.NpcTalk.Encoding` | automation suite: the WAV, both request bodies, both answers, the mesh-name rule | `SSNpcTalkAutomationTests.cpp` |

## Who you can talk to

- **On foot, a formal conversation** (owner, after testing: "I don't know who I'm talking to, so the engagement should
  be more formal: face to face, camera pans, walking a few steps away disengages and goes back; only activate by
  clicking talk"). Nothing starts until the talk key is tapped. The first tap picks the nearest crew member the pilot
  can see: within 5 m, on the same floor, roughly in front of the camera and not behind a wall (a flat range had picked
  people on other floors). The camera moves in over the pilot's shoulder and turns to them, the pilot turns to face
  them, and the microphone opens. Every later tap speaks to that partner, whoever else walks up. Walking about 2.5 m
  away ends it: the camera returns and any open question is dropped. Placed aliens without a name of their own get a
  stable given name from their actor name (`SSNpcTalk::GivenName`; owner: "who's Nyxar?" - Nyxar is the species). The
  station's deck crew are named by `SSStationPresentation::TagTalkers` through component tags. Every question and
  answer is written to the log (`LogSSNpcTalk`, "heard" and "answered after N s") so an odd reply can be read back.
- **The transcriber hears the game's words:** whisper's `prompt` field carries `WhisperVocabulary` plus the partner's
  name. Measured with a synthesized "Who is Nyxar?": "Nazar" without it, "Nyxar" with it (the owner's own test came
  back as "Nick's car").
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

1. First tap: `BeginTalk` picks the target, refreshes the digest (second-person facts; for the villain the hull and kills are words such as "in tatters" and "a couple of dozen", never figures a player could check against the HUD a second later, plus what the pilot is, so a squirrel gets called a squirrel) and
   opens the default microphone through the engine's `FAudioCapture`.
2. Second tap: the samples are mixed to mono, resampled to 16 kHz, written as a WAV and posted to whisper-server's
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
   are mostly **one-line first passes** for the owner to replace (the table below). Director, Dread and Cyborg have
   expanded profiles; Silver received a separate first-pass dancer history on 2026-10-13 at the owner's request.
2. **The scenario** (mine): `Content/SpaceSurvival/NpcTalk/Scenarios/<Role>.txt`, appended when the character holds
   that role. Roles today: Pool, Bartender, Merchant, Desk, Security, Maintenance, Worker, Dancer, Flirt, Performer,
   Lounge, Waitress, CrewTalk, Pacing, Watch, Guard, ServiceBot. A role moves between characters without touching
   their profile: set `TalkRole` on the placed actor, or the `TalkRole:` tag on a station component.
Owner's rule for the Flirt roles (2026-10-10): "the strippers shall engage in any NSFW comments you make; they have
to act the part". So the Flirt and Dancer scenarios mirror the pilot's register, never first and never less far,
the same shape as the villain's swearing rule; the owner tests that side themselves.
After the owner's first hand test on Daredevil ("it really only wanted to repeat its backstory... needs to be a bit
more rogue"), Flirt.txt was rewritten: she runs her own game, leads and may go first, never thanks a compliment,
throws personal questions back instead of reciting her history, and talks like a bar, not a poem. Chosen from three
rewrites by two judges, measured with `M:\Local AI\NPCTalk\test\dancer_probe.py` (same nine-line conversation, same
seeds; `--crude` for a pilot who goes explicit): backstory in Cyborg's replies 5/18 -> 2/18, questions back 4 -> 12.
Watch for: she still makes a crude pilot "prove himself" before matching him, and answers "where are you from?"
with her origin.

3. **The digest** (live, second person): who they are, `Right now you are <TalkActivity>`, who the pilot is and the
   run numbers. The activity is where "just scratched on the eight ball" goes, so a pool player can say "well, I
   scratched again". Nothing changes in code to give an NPC a special role: a role and an activity string.

Later, when audio is layered in, the owner wants these to fire on proximity without a key press (listed, not built).

### Character profiles (first passes unless noted)

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
| Silver | Dancer | expanded 2026-10-13 first pass: adult organic silver-skinned alien, natural legs, platinum hair, green eyes; warm, playful perfectionist with her own station-performance and private-apartment rehearsal history |
| Elf | Dancer, Lounge | elegant, dry wit, pretends not to care who's watching |
| Cyborg | Flirt (pole) | chrome and confidence, dares you to keep up |
| Crystal | Performer | crowned lounge performer, an artist, touchy about being called a dancer |
| Finhead | Lounge | retired pilot regular, every story ends with "back in my day" |
| Amethyst | Lounge | the station's gossip, knows every rumour, gives none away free |
| Nyxar (type) | CrewTalk / Pacing / Watch | bioluminescent crew who say "we", curious about outsiders; deck names Vel, Orrin, Sable, Kett, Rue, Pim, Dax |
| Trooper (type) | Guard | heavy-armoured dock guard Brakk, few words, has seen a lot of pilots not come back |
| ServiceBot (type) | ServiceBot | cheerful literal service robots Mica and Unit Seven, count things, give directions |

Silver's new Sentinel/ViableEld model is the authorized Silver replacement for the private apartment; the older
parked Tripo Silver asset is unchanged. Map the new character with `TalkName:Silver`, `TalkType:Silver` and
`TalkRole:Dancer`, plus an accurate current `TalkActivity`. This gives her a separate persona and voice identity
from Cyborg. Keep the older Silver inactive under that name: dialogue history is keyed by character name, not
mesh. The profile uses the shared station model, currently Daredevil-8B in `DefaultNpcTalk.ini`; no separate
character LoRA is configured. [Profile and voice evidence](validation/2026-10-13-silver-persona-voice.md).

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
| mergekit-community Deepseek-R1-Distill-NSFW-RPv1 (owner's link) | 4.92 GB | control | not stated | R1 distill: thinks before every reply; long-prose adapters; uncensored |
| DavidAU Gemma-3-it-4B-Uncensored (DBL-X) | 2.71 GB | Director, sub-6B tier | Gemma Terms of Use (card says Apache, base is Google's) | the only card with a crude rant delivered on request ("f-bombs galore"); instruct kept; author says refusals still happen without his jailbreak line, "hit regen" |
| mlabonne gemma-3-4b-it-abliterated (mradermacher GGUF) | 2.49 GB | Director or station, sub-6B tier | Gemma Terms of Use | cleanest small instruct chat model, refusals removed; nothing on the card about swearing; "fairly experimental", stray tokens |
| DavidAU Gemma-3 4B MAX-HORROR (owner's split: dancers) | 3.50 GB | test | Gemma Terms of Use | horror-prose story tune with a horror imatrix; wants rep pen 1.1; the owner wants it tried for the dancers anyway |
| QuantFactory NSFW-3B (owner's split: Director) | 1.71 GB | test | **none stated anywhere** (release blocker) | a 2024 StableLM-3B jailbreak tune, 4k context, ChatML, no example output; now redirects to HelpingAI/HELVETE-3B |

Every Gemma 3 template has no system role (the system text is folded into the first user turn) and, like the Mistral
templates, raises if two user turns arrive in a row, so an unanswered question is dropped from the history before
the next one is sent. All of them advertise 128k context; the explicit `-c 4096` matters for VRAM.

Rejected on the cards: Wayfarer-12B (second-person narrator, single-turn training), Violet Twilight v0.2 (weak at
persona-and-length prompts, already inside Violet-Lotus), MN-12B-Lyra-v4 (NC), Captain-Eris_Violet (GGUF template
conflicts with the author's), Rivermind-12B (a joke model that pushes soft drinks mid-chat, and NC), Magnolia-Mell
(no chat template, no licence), BigTalker (long-output sibling of Dirty Harry), Instruct-Guru ("PG-13"), the
Unholy-Hermes R1 merge (leaks reasoning, "unhinged"), the layer-duplicated 3B "7B/9B" models, the Gutenberg and
Gemma writers (novel prose), the Qwen3.5 9B "Aggressive" (thinking on, no card claim for chat).

Every Llama card above wants `repeat_penalty` 1.05 or higher; llama-server defaults to 1.0, so the game sends 1.05
(`RepeatPenalty`). The Nemo GGUFs advertise 131072 or 1024000 context, so the explicit `-c 4096` the game passes
matters: without it the KV cache alone would blow the 16 GB.

### The owner's Director criterion (2026-10-10, after reading the probes)

"Swearing is not as essential as that deep articulate hatred. I'll take a poetic villain too. Just leave the prompt
for when it slips." So the Director is judged on contempt, menace and staying in character first; swearing back is
a bonus, and the mirror instruction stays in the framing. On that reading Gemma-3-4b-it-MAX-HORROR (3.5 GB) is the
owner's leading Director candidate ("might be the Director's fit").

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

## Voices

Astra and Joy each have a separately designed original adult reference and exclusive exact-name routing in the current cast. [Current Joy revision and listening review](validation/2026-10-16-joy-original-voice.md) supersedes her earlier velvet audition. When replacing any reference at the same path, set `cache_revision` in its adjacent `.txt` to a new version or reference hash and prerender that character's lines again. Native lookup and Python prerender include this revision; an absent/empty value keeps legacy filenames exactly. Restart the talk subsystem and sidecar to load the change. Other voices and caches remain unaffected.

Owner, 2026-10-10: text is hard to read while flying, so the villain speaks. After five rounds of voices by ear the
owner chose "predator entity. done. exactly", and on the engine: "it didn't cost us 4 GB of VRAM or a week of
iterations. That's a win."

| Piece | What |
|---|---|
| Engine | LuxTTS (Apache-2.0, code and model), on the **processor**: no video memory. Measured on the i7-14700F with 4 threads: ready ~14 s after a cold start, a 10-word line in 2.7 s, 19 words in 3.6 s, ~1.6 GB of RAM |
| Voice | one `Content/SpaceSurvival/NpcTalk/Voices/<Name>.wav` per character, 4-7 s cut at a pause between sentences, cloned live; an optional `<Name>.txt` beside it sets `speed=` (pace, ~speed squared) and `treatment=` (entity, chrome, none), plus optional `cache_revision=` for a replacement reference. The audio profile, next to the text profiles. `_Default.wav` is everyone else's: Windows' own Microsoft David, recorded with System.Speech (owner: "a neutral default so there is something") |
| Treatment | "entity" (the Director): pitched down 3 semitones, an octave-down double, a faint ghost an octave up, a dark 1.2 s tail. "chrome": a faint metallic comb and shimmer. Applied by the server per voice |
| Server | `Tools/NpcTalk/director_voice_server.py` (POST `/speak` with `X-Voice: <Name>` -> PCM16 48 kHz; GET `/voices`), hidden, 127.0.0.1 only, exits with the game |
| Recipe | `M:\Local AI\DirectorTTS\director_voice_final\README.md`: the description, the settings, the approved sample |

How it plays:

- **Scripted lines** (all 29 except the death line) are made ahead of time with
  `director_voice_server.py --prerender scripted_lines.txt --cache ... --check <whisper-server>`: each take is
  transcribed and said again slower until every word is heard (short lines come out rushed otherwise). They play
  the moment they fire, from the first flight, with no server running. A line missing from the cache (new text in
  `DA_Phase1`) is made at departure.
- **His replies** when the pilot talks back take about their own length to make; the caption waits for the
  sound (owner 2026-10-12: words that lead the voice read as a delay). "The Director is answering..." stays up
  while the line is made, the caption appears as the clip starts, and it appears alone the moment it is known
  that no voice is coming (none asked for, the voice failed, or the deadline passed). The server starts with the game
  and stays up for the session (owner: no video memory, and the station crew will use it too); it takes ~15 s to
  load alone, ~33 s beside the editor, and about 1.6 GB of RAM. Its own log is `Saved/Logs/DirectorVoice.log`.
- **One voice:** a story beat waits while he is still speaking; chatter is dropped; a reply cuts a scripted line
  short; tapping T silences him so the microphone never hears him.
- His replies are capped at one short sentence, two at most (owner: "his lines absolutely can't be long").
- With subtitles off he still speaks (owner); without the voice installed nothing changes from the text-only game.
- Volume follows the Effects slider; `ss.VillainRadioFilter 1|2` adds a radio band for comparison (off by default:
  the treatment is his sound). A separate mute for him is an owner-listed follow-up.
- A new voice is a new `<Name>.wav` (and `.txt`) in the Voices folder; the Director's needs a fresh prerender.
  Today: `Director.wav` ("predator entity"), `Cyborg.wav` ("bright", picked by ear 2026-10-12, dry), `Silver.wav`
  (2026-10-13 exact copy of Cyborg's reference, with her own profile/name), `_Default.wav`. Silver keeps Cyborg's
  `speed=0.82`, `treatment=none`; Cyborg is unchanged. Restart the talk subsystem and voice sidecar to load a new
  voice. Silver's file/settings lookup is verified; live dialogue and listening approval remain unverified.
- **Crew replies** are spoken at the character's body (3D, full within 3 m, gone by 15 m); their caption waits for
  the voice the same way, and shows at once for a character with no voice of their own. Pressing T to talk silences
  them so the microphone never hears them. Captions stay up while they speak.

### Until the crew meshes are optimised (2026-10-12)

The station lagged (owner: "too many NPCs... until I go through and re-optimise the triangle count"), so
`ss.StationCrewTrim` (default 1) hides every character in the authored map except the pool match, the bartender,
the two desks and the stage (by label prefix in `SSStationPresentation::TrimCrew`; labels are editor-only, so a
packaged build keeps everyone). Hidden characters stop animating and cannot be talked to. `ss.StationCrewTrim 0`
shows them again. Separately, `ss.TalkTestCyborg` (default 1) stands a second Cyborg four metres in front of the
station walk-in point, alone and off the pole, to test voice, talk and interaction without other variables.
The real lag found the same day: Voicemod held 5.9 GB of the 16 GB card in the background.

## Limits and later

- No lip sync is possible: no crew member has jaw bones or mouth shapes. Talk gestures only.
- The sidecar paths in `DefaultNpcTalk.ini` are this machine's. A package must carry `bin/` and `models/` beside the
  executable and point the ini at them; non-asset persona files need `DirectoriesToAlwaysStageAsNonUFS`.
- Typed fallback, characters who speak first (bartender, merchants), voices for the crew, a separate mute for the
  villain, and the gameplay UI around talking are owner-listed follow-ups ("over next week, not urgent").
- Owner ideas, not scheduled: a boast from the villain when a run ends (the `VillainEpitaph` slot exists for his last
  word on a death); a small local player profile, how often the pilot swears across runs, so how vulgar he may get
  tracks the player's own habit, or simply a setting. The language-mirroring today is per line only.
- Licences: whisper.cpp and llama.cpp MIT, whisper small.en MIT, Qwen2.5-1.5B-Instruct Apache 2.0. Verify the exact
  model file before any release (docs/production/SOLUTION_CATALOG.md rule).
