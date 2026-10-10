// Push-to-talk conversations with station characters: the microphone is transcribed by a local whisper.cpp
// server, the character answers through a local llama.cpp server, both started by the game as hidden child
// processes. Text in, text out; nothing leaves the machine. Owner decision 2026-10-10 (docs/NPC_TALK.md).
#pragma once

#include "CoreMinimal.h"
#include "AudioCaptureCore.h"
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
/** "SK_Dread" -> "Dread". The crew meshes carry the character's name; nothing else on the actor does. */
SPACESURVIVAL_API FString CharacterNameFromMesh(const FString &MeshName);
} // namespace SSNpcTalk

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
    virtual void Deinitialize() override;

    bool IsEnabled() const
    {
        return bEnabled && !WhisperServerExe.IsEmpty() && !LlamaServerExe.IsEmpty();
    }
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

private:
    void StopServers();
    void Fail(const FString &Character, const FString &Why);
    void SendToWhisper(const FString &Character, const TArray<uint8> &Wav);
    void SendToLlama(const FString &Character, const FString &Question);
    FString BuiltInPersona(const FString &Character) const;

    ESSTalkPhase CurrentPhase = ESSTalkPhase::Idle;
    FString Error;
    FProcHandle WhisperProc, LlamaProc;
    TUniquePtr<Audio::FAudioCapture> Capture;
    bool bStreamOpen = false;
    FCriticalSection SamplesLock;
    TArray<float> Samples;
    int32 CaptureRate = 0, CaptureChannels = 0;
    TMap<FString, TArray<SSNpcTalk::FTurn>> History;
    TSharedPtr<IHttpRequest, ESPMode::ThreadSafe> Pending;
};
