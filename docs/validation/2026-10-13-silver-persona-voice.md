# Silver persona and shared voice — 2026-10-13

Scope: give the new Silver/Sentinel dancer her own profile and mapping while temporarily reusing Cyborg's exact
voice, as requested by the owner. This is a profile/audio-file change; no model training, engine code, native
asset, Cyborg profile, shared scenario or server configuration was changed by this patch.

## Changed files

- `Content/SpaceSurvival/NpcTalk/Personas/Silver.txt`: expanded first-pass adult organic dancer identity, natural
  legs, platinum hair, green eyes and emerald outfit; modest station-performance/rehearsal history, warmer
  conversation and grounded fictional self-awareness. Backstory is provisional writing, not an owner-approved
  canon claim. The prompt does not claim actual AI consciousness or access to unseen player information.
- `Content/SpaceSurvival/NpcTalk/Voices/Silver.wav`: byte-identical copy of the existing Cyborg reference.
- `Content/SpaceSurvival/NpcTalk/Voices/Silver.txt`: independent named profile, same `speed=0.82`, `treatment=none`.

The new Sentinel/ViableEld character is the authorized Silver replacement for the private apartment. Its native
review namespace is `/Game/SpaceSurvival/Licensed/ViableEldReview_20261013`; the older Tripo Silver, parked for
thigh-deformation defects, remains a separate unchanged asset. `TalkName:Silver`, `TalkType:Silver` and
`TalkRole:Dancer` select the new profile; `TalkActivity` must describe the actual scene. Do not activate the old
asset under the same talk name alongside it: name-based history/persona lookup does not distinguish their meshes.
Native tag authoring and live target selection are outside this receipt.

## Evidence

Checked against source HEAD `9912a54d1e464257b4b082c2a23d216f11f5a2e8` with this scoped working-tree patch.
Local detailed receipt: `.agent/local/ViableEldFinish_20261013/SilverPersona/Profile_Validation.json`.

| Check | Result |
|---|---|
| Actual `director_voice_server.read_voices` lookup | `silver` resolves to `Silver.wav`, speed 0.82, treatment none |
| Copied reference | SHA-256 `660b09853e80f5042a6bfae5581d1e5f874f02ccb732a038e305b686c7bcc78c`, equal to Cyborg |
| Audio format | 5.0 seconds, mono PCM16, 24,000 Hz, 120,000 frames |
| Separate cached identity | Same text produces different cache keys for `Silver.wav` and `Cyborg.wav` |
| Persona substitution | `{Name}` resolves to Silver; existing Dancer scenario remains available |
| Silver persona | Windows working-file SHA-256 `ff6ccb2505fbd7ff5ba1a3b5cb03300c11b95529c6bdee5be3943b374980e001`; published LF text `7804bb8512122299ce229bd11df6835cee88083fda656d17f127ce19c04f5575` |
| Preservation | Cyborg persona/WAV/settings, Dancer scenario and DefaultNpcTalk.ini hashes unchanged |
| Whitespace | Scoped `git diff --check` passes |
| Documentation gate | `python Scripts/CheckPrDocumentation.py --repo .` passes; checks navigation/count consistency only |

`USSNpcTalkSubsystem::Persona` resolves name, type, then default; `VoiceFor` resolves the named voice before the
default. Current `StationLlamaModel` is the shared Daredevil-8B GGUF and `StationLlamaExtraArgs` is empty. No
per-character LoRA is configured or created. Reusing the reference preserves the voice identity/settings; it
does not promise bit-identical synthesized lines.

No inference, audio audition, microphone conversation, native identity-selection, packaged staging or owner
personality approval was performed for this receipt. Voice registries are loaded at startup: use a fresh talk
subsystem/sidecar for the next live check. No C++ change, rebuild or game-completion claim.
