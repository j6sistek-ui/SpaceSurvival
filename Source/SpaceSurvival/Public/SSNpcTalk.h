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

/** Pure helpers behind the subsystem, kept free of the engine so the automation suite can pin them down. */
namespace SSNpcTalk
{
struct FTurn
{
    FString Role, Content;
};
/** Interleaved float PCM at any rate and channel count -> mono 16 kHz, which is what whisper wants. */
SPACESURVIVAL_API TArray<float> ToMono16k(const TArray<float> &Interleaved, int32 Channels, int32 SampleRate);
/** Mono 16 kHz float -> a complete 16-bit PCM WAV file. */
SPACESURVIVAL_API TArray<uint8> EncodeWav16k(const TArray<float> &Mono);
/** The multipart body whisper-server's /inference reads; the boundary comes back for the Content-Type header. */
SPACESURVIVAL_API TArray<uint8> WhisperBody(const TArray<uint8> &Wav, FString &OutBoundary);
SPACESURVIVAL_API FString ParseTranscript(const FString &Json);
/** OpenAI-style chat request for llama-server's /v1/chat/completions. */
SPACESURVIVAL_API FString ChatBody(const FString &System, const TArray<FTurn> &Turns, int32 MaxTokens,
                                   float Temperature);
SPACESURVIVAL_API FString ParseReply(const FString &Json);
/** Bold markers and wrapping quotes off; when the token cap cut the reply short, whole sentences only. */
SPACESURVIVAL_API FString TidyReply(const FString &Raw, bool bCutShort);
/** Did the pilot swear? Decides whether the villain is told to give it back. */
SPACESURVIVAL_API bool HasProfanity(const FString &Text);
/** "SK_Dread" -> "Dread". The crew meshes carry the character's name; nothing else on the actor does. */
SPACESURVIVAL_API FString CharacterNameFromMesh(const FString &MeshName);
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
    /** Close the microphone, transcribe what was said and ask the character; answers arrive on the delegates. */
    void EndListeningAndAsk(const FString &Character);
    void Cancel();
    void ForgetConversations()
    {
        History.Empty();
    }
    /** The character's system prompt: Content/<PersonaDirectory>/<Character>.txt, else _Default.txt, else built in. */
    FString Persona(const FString &Character) const;

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
    /** Relative to the project's Content folder. */
    UPROPERTY(Config)
    FString PersonaDirectory = TEXT("SpaceSurvival/NpcTalk/Personas");
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
    ESSTalkPhase CurrentPhase = ESSTalkPhase::Idle;
    ESSTalkContext CurrentContext = ESSTalkContext::Flight;
    FString Error, RunningModel;
    double LlamaStartedAt = 0.0;
    int32 LlamaRetries = 0;
    FTimerHandle RetryTimer;
    FProcHandle WhisperProc, LlamaProc;
    TUniquePtr<Audio::FAudioCapture> Capture;
    bool bStreamOpen = false;
    FCriticalSection SamplesLock;
    TArray<float> Samples;
    int32 CaptureRate = 0, CaptureChannels = 0;
    TMap<FString, TArray<SSNpcTalk::FTurn>> History;
    TSharedPtr<IHttpRequest, ESPMode::ThreadSafe> Pending;
};
