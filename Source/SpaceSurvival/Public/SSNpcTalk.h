// Push-to-talk conversations with station characters: the microphone is transcribed by a local whisper.cpp
// server, the character answers through a local llama.cpp server, both started by the game as hidden child
// processes. Text in, text out; nothing leaves the machine. Owner decision 2026-10-10 (docs/NPC_TALK.md).
#pragma once

#include "CoreMinimal.h"
#include "AudioCaptureCore.h"
#include "Engine/TimerHandle.h"
#include "Interfaces/IHttpRequest.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "SSNpcTalk.generated.h"

/** Who is being spoken to. Name keys the conversation and the caption; Type picks the persona file when no file
 *  carries the name (seven Nyxar crew share Nyxar.txt); Activity is what they are doing right now ("playing pool at
 *  the lounge table, just scratched"), told to the model so they can talk about it. Owner 2026-10-10: a profile for
 *  every NPC type and character, and a special role makes that NPC aware of it. */
struct FSSTalkIdentity
{
    /** Role picks the scenario file (Pool, Bartender, Guard), the layer the game adds on top of the profile. */
    FString Name, Type, Role, Activity;
    bool IsValid() const
    {
        return !Name.IsEmpty();
    }
};

/** Pure helpers behind the subsystem, kept free of the engine so the automation suite can pin them down. */
namespace SSNpcTalk
{
struct FTurn
{
    FString Role, Content;
};
/** Component tags "TalkName:Vel", "TalkType:Nyxar", "TalkRole:Watch", "TalkActivity:watching the dock". Type falls
 *  back to the mesh name, Name to the Type. */
SPACESURVIVAL_API FSSTalkIdentity IdentityFromTags(const TArray<FName> &Tags, const FString &MeshName);
/** Any Talk* tag at all: the station's deck crew are tagged, its display ship and holograms are not. */
SPACESURVIVAL_API bool HasTalkTag(const TArray<FName> &Tags);
/** Interleaved float PCM at any rate and channel count -> mono 16 kHz, which is what whisper wants. */
SPACESURVIVAL_API TArray<float> ToMono16k(const TArray<float> &Interleaved, int32 Channels, int32 SampleRate);
/** Mono 16 kHz float -> a complete 16-bit PCM WAV file. */
SPACESURVIVAL_API TArray<uint8> EncodeWav16k(const TArray<float> &Mono);
/** The multipart body whisper-server's /inference reads; the boundary comes back for the Content-Type header. */
SPACESURVIVAL_API TArray<uint8> WhisperBody(const TArray<uint8> &Wav, FString &OutBoundary,
                                            const FString &Prompt = FString());
SPACESURVIVAL_API FString ParseTranscript(const FString &Json);
/** OpenAI-style chat request for llama-server's /v1/chat/completions. */
SPACESURVIVAL_API FString ChatBody(const FString &System, const TArray<FTurn> &Turns, int32 MaxTokens,
                                   float Temperature, float RepeatPenalty = 1.f);
SPACESURVIVAL_API FString ParseReply(const FString &Json);
/** Bold markers and wrapping quotes off; when the token cap cut the reply short, whole sentences only. */
SPACESURVIVAL_API FString TidyReply(const FString &Raw, bool bCutShort);
/** Did the pilot swear? Decides whether the villain is told to give it back. */
SPACESURVIVAL_API bool HasProfanity(const FString &Text);
/** A placed crew member of a shared species with no name of its own gets a stable given name from its actor name
 *  (owner: "who's Nyxar?"). Any other type is returned unchanged. */
SPACESURVIVAL_API FString GivenName(const FString &Type, const FString &Seed);
/** "SK_Dread" -> "Dread", "SKM_Nyxar" -> "Nyxar". The crew meshes carry the character's name. */
SPACESURVIVAL_API FString CharacterNameFromMesh(const FString &MeshName);

/** One line in the villain's voice: mono 16-bit little-endian PCM at SampleRate. */
struct FVoiceClip
{
    TArray<uint8> Pcm;
    int32 SampleRate = 0;
    bool IsValid() const
    {
        return SampleRate > 0 && Pcm.Num() >= 2;
    }
    float Seconds() const
    {
        return IsValid() ? float(Pcm.Num() / 2) / float(SampleRate) : 0.f;
    }
};
/** The voice server's reply body and X-Sample-Rate header as a clip ready to play: an odd trailing byte dropped and
 *  a quarter second of silence after the last word, so the tail is never clipped. An empty body or a rate outside
 *  8-48 kHz is no clip; no header means LuxTTS's own 48 kHz. */
SPACESURVIVAL_API FVoiceClip VoiceClip(const TArray<uint8> &Body, const FString &RateHeader);
/** Arguments for Tools/NpcTalk/director_voice_server.py. Empty when a path holds a double quote, which the command
 *  line cannot carry. */
SPACESURVIVAL_API FString VoiceArgs(const FString &Script, const FString &Repo, const FString &VoicesDir,
                                    const FString &DefaultVoice, int32 Threads, int32 Port, uint32 ParentPid);
/** The file a line is kept in: an MD5 of "<reference file>|<speed>|<treatment>|<line>", exactly as the server's
 *  --prerender names it, so lines made ahead of time are found. A new voice, speed or treatment is a new name. */
SPACESURVIVAL_API FString VoiceCacheName(const FString &Reference, double Speed, const FString &Treatment,
                                         const FString &Text);
/** A character's voice: the recording the server clones, and the settings from the <Name>.txt beside it. Speed is
 *  a double so "%.2f" rounds exactly as the server's Python does (0.985 is 0.98 to both). */
struct FVoiceProfile
{
    FString Reference;
    double Speed = 0.92;
    FString Treatment = TEXT("none");
};
/** "speed=0.92" and "treatment=entity" lines, as the server reads them; anything else is ignored. */
SPACESURVIVAL_API void ParseVoiceProfile(const FString &Text, FVoiceProfile &Out);
/** How long a line may wait for its voice before the caption carries it alone. A scripted line heard seconds after
 *  its caption is worse than none; a reply is what the pilot asked for, so it waits longer. */
SPACESURVIVAL_API float VoiceDeadline(const FString &Text, bool bReply);
} // namespace SSNpcTalk

UENUM()
enum class ESSTalkContext : uint8
{
    Flight,
    Station
};

UENUM()
enum class ESSTalkPhase : uint8
{
    Idle,
    Listening,
    Transcribing,
    Thinking
};

/** Owns the microphone, the two sidecar servers and one conversation per character. Config/DefaultNpcTalk.ini. */
UCLASS(Config = NpcTalk)
class SPACESURVIVAL_API USSNpcTalkSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase &Collection) override;
    virtual void Deinitialize() override;

    /** The optional talk pack was on disk at start-up: both servers, the transcriber model and the flight model. */
    bool IsInstalled() const
    {
        return bInstalled;
    }
    bool IsEnabled() const;
    /** The station loads the better talker on arrival; launching into a wave kills the server. */
    void SetContext(ESSTalkContext Context);
    ESSTalkPhase Phase() const
    {
        return CurrentPhase;
    }
    const FString &LastError() const
    {
        return Error;
    }
    /** Start whichever sidecar is not running yet. Idempotent; the first call after launch takes a few seconds. */
    void EnsureServers();
    /** Open the microphone. False, with LastError set, when there is no device or the feature is off. */
    bool BeginListening();
    /** Close the microphone, transcribe what was said and ask the character; answers arrive on the delegates
     *  keyed by Who.Name. The identity is remembered so the persona can fall back to the type's file. */
    void EndListeningAndAsk(const FSSTalkIdentity &Who);
    void Cancel();
    void ForgetConversations()
    {
        History.Empty();
    }
    /** The character's system prompt: Content/<PersonaDirectory>/<Name>.txt, else <Type>.txt, else _Default.txt,
     *  else built in; "{Name}" in the file becomes the character's name. */
    FString Persona(const FString &Character) const;
    /** A profile file exists for this name (read once at start-up): a placed character with one can be talked to. */
    /** "Mesh=Character": a body that plays someone else (owner: the Joy body at the pole is Cyan). */
    UPROPERTY(Config)
    TArray<FString> CharacterAliases = {TEXT("JoyLightBlue=Cyan"), TEXT("JoyPurple=Cyan")};
    FString ResolveAlias(const FString &Name) const
    {
        for (const FString &Pair : CharacterAliases)
        {
            FString From, To;
            if (Pair.Split(TEXT("="), &From, &To) && From.TrimStartAndEnd() == Name)
                return To.TrimStartAndEnd();
        }
        return Name;
    }
    bool HasPersona(const FString &Name) const
    {
        return PersonaNames.Contains(Name);
    }

    DECLARE_MULTICAST_DELEGATE_TwoParams(FOnTalkText, const FString & /*Character*/, const FString & /*Text*/);
    FOnTalkText OnTranscript, OnReply, OnFailure;
    /** A phrase for the status line ("is still waking up...") while a freshly started server reads its model. */
    FOnTalkText OnStatus;

    /** Plain second-person sentences about the game right now; the game mode refreshes it before each question. */
    FString Digest;

    UPROPERTY(Config)
    bool bEnabled = true;
    UPROPERTY(Config)
    FString WhisperServerExe;
    UPROPERTY(Config)
    FString WhisperModel;
    UPROPERTY(Config)
    FString LlamaServerExe;
    UPROPERTY(Config)
    FString LlamaModel;
    /** Relative to the project's Content folder. Personas are the owner's profiles, one per character or type. */
    UPROPERTY(Config)
    FString PersonaDirectory = TEXT("SpaceSurvival/NpcTalk/Personas");
    /** Scenario files, one per role (Pool, Bartender, Guard), appended to the profile of whoever holds that role. */
    UPROPERTY(Config)
    FString ScenarioDirectory = TEXT("SpaceSurvival/NpcTalk/Scenarios");
    /** Words whisper should expect: the game's invented names are otherwise heard as English ("Nyxar" came back as
     *  "Nick's car"; with this list it comes back right). The character being spoken to is appended. */
    UPROPERTY(Config)
    FString WhisperVocabulary =
        TEXT("Nyxar, the Director, Wayfarer Exchange, Stellar Phoenix, Dread, Vel, Orrin, Sable, "
             "Kett, Rue, Pim, Dax, Brakk, Mica, Unit Seven, Cyan, Cyborg, Violet, Tribal, Seer, "
             "Tendril, Glyph, Robe, Ember, Crest, Olive, Warden, Abyss, Silver, Elf, Crystal, "
             "Finhead, Amethyst, Joy, synth-ale, Europa gin, Nebula, cheers, pour, toast.");
    UPROPERTY(Config)
    int32 WhisperPort = 8701;
    UPROPERTY(Config)
    int32 LlamaPort = 8702;
    UPROPERTY(Config)
    int32 LlamaGpuLayers = 99;
    UPROPERTY(Config)
    int32 MaxReplyTokens = 90;
    /** Turns of back-and-forth remembered per character. */
    UPROPERTY(Config)
    int32 HistoryTurns = 8;
    UPROPERTY(Config)
    float Temperature = 0.7f;
    /** llama-server defaults to 1.0; every Llama roleplay card read on 2026-10-10 wants 1.05 or the reply ends in a
     *  repeated paragraph. 1.0 sends nothing. */
    UPROPERTY(Config)
    float RepeatPenalty = 1.05f;
    UPROPERTY(Config)
    int32 Threads = 8;
    /** Appended to the llama-server command line. "--reasoning off" keeps a thinking model from thinking out loud. */
    UPROPERTY(Config)
    FString LlamaExtraArgs = TEXT("--reasoning off");
    /** The station's model, loaded on arrival and killed on launch (owner: the station is talk, a wave is combat).
     *  Empty or missing: the flight model serves the station too. */
    UPROPERTY(Config)
    FString StationLlamaModel;
    UPROPERTY(Config)
    FString StationLlamaExtraArgs;

    /** Spoken lines (owner 2026-10-10: text is hard to read while flying; 2026-10-12: a voice profile for every
     *  character). LuxTTS on the processor, no video memory. Optional like the rest: its python, the server
     *  script, the LuxTTS checkout and at least one voice on disk at start-up, else everyone stays text-only.
     *  A voice is Content/<VoiceDirectory>/<Name>.wav with an optional <Name>.txt (speed=, treatment=), read like
     *  the text profiles. The server runs for the whole session. */
    bool IsVoiceEnabled() const;
    /** This character can be heard: a recording of their own, else the shared _Default.wav when there is one. The
     *  villain's is "Director". */
    bool HasVoice(const FString &Character) const
    {
        return !VoiceFor(Character).IsEmpty();
    }
    /** The voice name a character speaks with: their own, else "_Default", else empty. */
    FString VoiceFor(const FString &Character) const
    {
        // The file's own spelling goes to the server, whatever case the character name came in.
        for (const auto &Voice : Voices)
            if (Voice.Key.Equals(Character, ESearchCase::IgnoreCase))
                return Voice.Key;
        return Voices.Contains(TEXT("_Default")) ? FString(TEXT("_Default")) : FString();
    }
    /** Start the voice server unless it runs. Idempotent; it answers ~15-35 s after a cold start. */
    void EnsureVoice();
    void StopVoice();
    /** Say Text in Voice. Done runs on the game thread with the clip - at once when it was made before (bKeep
     *  lines are kept, on disk too), else when the server answers, empty when it could not. False when there is
     *  no such voice: the caption carries the line alone. Only the newest unanswered line is kept waiting. */
    bool Speak(const FString &Voice, const FString &Text, bool bKeep,
               TFunction<void(const SSNpcTalk::FVoiceClip &)> Done);
    /** Make scripted lines ahead, behind any live line, so they play the moment they fire. Lines already made in
     *  an earlier session come off the disk instead. */
    void Prerender(const FString &Voice, const TArray<FString> &Lines);
    UPROPERTY(Config)
    bool bVoiceEnabled = true;
    /** The LuxTTS venv's python.exe (not pythonw.exe). */
    UPROPERTY(Config)
    FString VoicePython;
    /** Relative to the project folder unless absolute. */
    UPROPERTY(Config)
    FString VoiceScript = TEXT("Tools/NpcTalk/director_voice_server.py");
    /** The LuxTTS checkout (its zipvoice package is not pip-installed). */
    UPROPERTY(Config)
    FString VoiceRepo;
    /** Relative to the project's Content folder: one <Name>.wav per character, a 4-7 s recording cut at a pause,
     *  plus an optional <Name>.txt with speed= and treatment= (entity, chrome, none). A new voice is a file. */
    UPROPERTY(Config)
    FString VoiceDirectory = TEXT("SpaceSurvival/NpcTalk/Voices");
    /** The voice a request without a character gets, and the one warmed at start-up. */
    UPROPERTY(Config)
    FString DefaultVoice = TEXT("Director");
    /** Processor threads for a line made live; the game is running beside it. */
    UPROPERTY(Config)
    int32 VoiceThreads = 4;
    /** Where kept lines live, made ahead by the server's --prerender or kept as they are made. Empty: Saved/. */
    UPROPERTY(Config)
    FString VoiceCacheDirectory;
    UPROPERTY(Config)
    int32 VoicePort = 8703;
    /** A refused connection this soon after launch means "still loading", and is retried every second. Measured:
     *  ~14 s alone, ~33 s beside the editor and a running game. */
    UPROPERTY(Config)
    float VoiceStartupSeconds = 120.f;
    /** His replies are heard mid-flight, so they are capped harder than the crew's. */
    UPROPERTY(Config)
    int32 DirectorReplyTokens = 48;

private:
    void StopServers();
    void Fail(const FString &Character, const FString &Why);
    void SendToWhisper(const FString &Character, const TArray<uint8> &Wav);
    void SendToLlama(const FString &Character, const FString &Question);
    /** Posts the character's history as it stands; retried on a timer while a cold llama-server is still loading. */
    void PostToLlama(const FString &Character);
    FString BuiltInPersona(const FString &Character) const;
    void StopLlama();

    bool bInstalled = false;
    TSet<FString> PersonaNames;
    ESSTalkPhase CurrentPhase = ESSTalkPhase::Idle;
    ESSTalkContext CurrentContext = ESSTalkContext::Flight;
    FString Error, RunningModel;
    double LlamaStartedAt = 0.0, AskedAt = 0.0;
    int32 LlamaRetries = 0;
    FTimerHandle RetryTimer;
    FProcHandle WhisperProc, LlamaProc;
    TUniquePtr<Audio::FAudioCapture> Capture;
    bool bStreamOpen = false;
    FCriticalSection SamplesLock;
    TArray<float> Samples;
    int32 CaptureRate = 0, CaptureChannels = 0;
    TMap<FString, TArray<SSNpcTalk::FTurn>> History;
    TMap<FString, FSSTalkIdentity> Known;
    TSharedPtr<IHttpRequest, ESPMode::ThreadSafe> Pending;

    struct FVoiceJob
    {
        int32 Id = 0;
        FString Voice, Text;
        TFunction<void(const SSNpcTalk::FVoiceClip &)> Done;
        bool bLive = false, bKeep = false;
    };
    FString VoiceScriptPath() const;
    FString VoicesPath() const;
    FString VoiceCacheFile(const FString &Voice, const FString &Text) const;
    bool FindVoiceClip(const FString &Voice, const FString &Text, SSNpcTalk::FVoiceClip &Out);
    /** Send the next job; one at a time, as the server works one line at a time. */
    void PumpVoice();
    void FinishVoiceJob(int32 Id, const FString &Voice, const FString &Text, bool bKeep,
                        const SSNpcTalk::FVoiceClip &Clip);
    TMap<FString, SSNpcTalk::FVoiceProfile> Voices;
    bool bVoiceInstalled = false, bVoiceReady = false;
    FProcHandle VoiceProc;
    double VoiceStartedAt = 0.0, PrerenderStartedAt = 0.0;
    int32 VoiceCrashes = 0, NextVoiceJob = 0, InFlightVoiceJob = 0, Prerendered = 0;
    TArray<FVoiceJob> VoiceJobs;
    TMap<FString, SSNpcTalk::FVoiceClip> VoiceCache;
    TSharedPtr<IHttpRequest, ESPMode::ThreadSafe> VoicePending;
    FTimerHandle VoiceRetryTimer;
};
