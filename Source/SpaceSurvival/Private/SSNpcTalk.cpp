#include "SSNpcTalk.h"
#include "AudioCaptureCore.h"
#include "Dom/JsonObject.h"
#include "HAL/PlatformProcess.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

DEFINE_LOG_CATEGORY_STATIC(LogSSNpcTalk, Log, All);

namespace SSNpcTalk
{
TArray<float> ToMono16k(const TArray<float> &Interleaved, int32 Channels, int32 SampleRate)
{
    TArray<float> Out;
    if (Channels <= 0 || SampleRate <= 0 || Interleaved.Num() < Channels)
        return Out;
    const int32 Frames = Interleaved.Num() / Channels;
    TArray<float> Mono;
    Mono.SetNumUninitialized(Frames);
    for (int32 F = 0; F < Frames; ++F)
    {
        float Sum = 0.f;
        for (int32 C = 0; C < Channels; ++C)
            Sum += Interleaved[F * Channels + C];
        Mono[F] = Sum / Channels;
    }
    if (SampleRate == 16000)
        return Mono;
    // Linear interpolation is enough for speech; whisper resamples internally anyway if it has to.
    const double Step = double(SampleRate) / 16000.0;
    const int32 OutFrames = FMath::Max(1, int32(Frames / Step));
    Out.SetNumUninitialized(OutFrames);
    for (int32 O = 0; O < OutFrames; ++O)
    {
        const double Pos = O * Step;
        const int32 I = FMath::Min(int32(Pos), Frames - 1), J = FMath::Min(I + 1, Frames - 1);
        const float T = float(Pos - I);
        Out[O] = Mono[I] * (1.f - T) + Mono[J] * T;
    }
    return Out;
}

TArray<uint8> EncodeWav16k(const TArray<float> &Mono)
{
    const uint32 DataBytes = Mono.Num() * 2, SampleRate = 16000, ByteRate = SampleRate * 2;
    TArray<uint8> Wav;
    Wav.Reserve(44 + DataBytes);
    auto Put = [&Wav](const void *Bytes, int32 Count) { Wav.Append(static_cast<const uint8 *>(Bytes), Count); };
    auto U32 = [&Put](uint32 V) { Put(&V, 4); };
    auto U16 = [&Put](uint16 V) { Put(&V, 2); };
    Put("RIFF", 4);
    U32(36 + DataBytes);
    Put("WAVE", 4);
    Put("fmt ", 4);
    U32(16);
    U16(1);
    U16(1);
    U32(SampleRate);
    U32(ByteRate);
    U16(2);
    U16(16);
    Put("data", 4);
    U32(DataBytes);
    for (float S : Mono)
    {
        const int16 V = int16(FMath::Clamp(S, -1.f, 1.f) * 32767.f);
        Put(&V, 2);
    }
    return Wav;
}

TArray<uint8> WhisperBody(const TArray<uint8> &Wav, FString &OutBoundary)
{
    OutBoundary = TEXT("----SSNpcTalk7f3a9c2e");
    const FString Head =
        FString::Printf(TEXT("--%s\r\nContent-Disposition: form-data; name=\"response_format\"\r\n\r\njson\r\n"
                             "--%s\r\nContent-Disposition: form-data; name=\"temperature\"\r\n\r\n0.0\r\n"
                             "--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"ask.wav\"\r\n"
                             "Content-Type: audio/wav\r\n\r\n"),
                        *OutBoundary, *OutBoundary, *OutBoundary);
    const FString Tail = FString::Printf(TEXT("\r\n--%s--\r\n"), *OutBoundary);
    TArray<uint8> Body;
    const FTCHARToUTF8 H(*Head), T(*Tail);
    Body.Append(reinterpret_cast<const uint8 *>(H.Get()), H.Length());
    Body.Append(Wav);
    Body.Append(reinterpret_cast<const uint8 *>(T.Get()), T.Length());
    return Body;
}

static TSharedPtr<FJsonObject> Parse(const FString &Json)
{
    TSharedPtr<FJsonObject> Object;
    const auto Reader = TJsonReaderFactory<>::Create(Json);
    return FJsonSerializer::Deserialize(Reader, Object) ? Object : nullptr;
}

FString ParseTranscript(const FString &Json)
{
    const auto Object = Parse(Json);
    FString Text;
    if (Object && Object->TryGetStringField(TEXT("text"), Text))
        return Text.TrimStartAndEnd();
    return FString();
}

FString ChatBody(const FString &System, const TArray<FTurn> &Turns, int32 MaxTokens, float Temperature)
{
    const auto Root = MakeShared<FJsonObject>();
    TArray<TSharedPtr<FJsonValue>> Messages;
    auto Add = [&Messages](const FString &Role, const FString &Content)
    {
        const auto M = MakeShared<FJsonObject>();
        M->SetStringField(TEXT("role"), Role);
        M->SetStringField(TEXT("content"), Content);
        Messages.Add(MakeShared<FJsonValueObject>(M));
    };
    Add(TEXT("system"), System);
    for (const FTurn &Turn : Turns)
        Add(Turn.Role, Turn.Content);
    Root->SetArrayField(TEXT("messages"), Messages);
    Root->SetNumberField(TEXT("max_tokens"), MaxTokens);
    Root->SetNumberField(TEXT("temperature"), Temperature);
    Root->SetBoolField(TEXT("stream"), false);
    FString Out;
    const auto Writer = TJsonWriterFactory<>::Create(&Out);
    FJsonSerializer::Serialize(Root, Writer);
    return Out;
}

FString ParseReply(const FString &Json)
{
    const auto Object = Parse(Json);
    if (!Object)
        return FString();
    const TArray<TSharedPtr<FJsonValue>> *Choices = nullptr;
    if (!Object->TryGetArrayField(TEXT("choices"), Choices) || !Choices || Choices->IsEmpty())
        return FString();
    const auto Choice = (*Choices)[0]->AsObject();
    const TSharedPtr<FJsonObject> *Message = nullptr;
    FString Content;
    if (Choice && Choice->TryGetObjectField(TEXT("message"), Message) && Message &&
        (*Message)->TryGetStringField(TEXT("content"), Content))
        return Content.TrimStartAndEnd();
    return FString();
}

FString CharacterNameFromMesh(const FString &MeshName)
{
    FString Name = MeshName;
    if (Name.StartsWith(TEXT("SK_")))
        Name.RightChopInline(3);
    return Name;
}
} // namespace SSNpcTalk

namespace
{
FString Quote(const FString &Path)
{
    return FString::Printf(TEXT("\"%s\""), *Path);
}
FProcHandle Launch(const FString &Exe, const FString &Args)
{
    if (!FPaths::FileExists(Exe))
        return FProcHandle();
    // Hidden: no console window may appear on the owner's screen (CLAUDE.md), and a game that ships this must not
    // flash terminals either.
    return FPlatformProcess::CreateProc(*Exe, *Args, false, true, true, nullptr, 0, *FPaths::GetPath(Exe), nullptr);
}
} // namespace

void USSNpcTalkSubsystem::Deinitialize()
{
    Cancel();
    if (Capture && bStreamOpen)
        Capture->AbortStream();
    Capture.Reset();
    StopServers();
    Super::Deinitialize();
}

void USSNpcTalkSubsystem::StopServers()
{
    for (FProcHandle *Proc : {&WhisperProc, &LlamaProc})
        if (Proc->IsValid())
        {
            FPlatformProcess::TerminateProc(*Proc, true);
            FPlatformProcess::CloseProc(*Proc);
            *Proc = FProcHandle();
        }
}

void USSNpcTalkSubsystem::EnsureServers()
{
    if (!IsEnabled())
        return;
    if (!WhisperProc.IsValid() || !FPlatformProcess::IsProcRunning(WhisperProc))
    {
        WhisperProc = Launch(WhisperServerExe, FString::Printf(TEXT("-m %s --host 127.0.0.1 --port %d -t %d"),
                                                               *Quote(WhisperModel), WhisperPort, Threads));
        UE_LOG(LogSSNpcTalk, Display, TEXT("whisper-server %s on %d"),
               WhisperProc.IsValid() ? TEXT("started") : TEXT("NOT FOUND"), WhisperPort);
    }
    if (!LlamaProc.IsValid() || !FPlatformProcess::IsProcRunning(LlamaProc))
    {
        LlamaProc =
            Launch(LlamaServerExe, FString::Printf(TEXT("-m %s -ngl %d --host 127.0.0.1 --port %d -c 4096 -t %d"),
                                                   *Quote(LlamaModel), LlamaGpuLayers, LlamaPort, Threads));
        UE_LOG(LogSSNpcTalk, Display, TEXT("llama-server %s on %d"),
               LlamaProc.IsValid() ? TEXT("started") : TEXT("NOT FOUND"), LlamaPort);
    }
}

bool USSNpcTalkSubsystem::BeginListening()
{
    if (!IsEnabled())
    {
        Error = TEXT("NPC talk is off (Config/DefaultNpcTalk.ini).");
        return false;
    }
    if (CurrentPhase != ESSTalkPhase::Idle)
        return false;
    EnsureServers();
    if (!Capture)
        Capture = MakeUnique<Audio::FAudioCapture>();
    Audio::FCaptureDeviceInfo Info;
    if (!Capture->GetCaptureDeviceInfo(Info))
    {
        Error = TEXT("No microphone found.");
        return false;
    }
    {
        FScopeLock Lock(&SamplesLock);
        Samples.Reset();
        CaptureRate = Info.PreferredSampleRate;
        CaptureChannels = Info.InputChannels;
    }
    Audio::FAudioCaptureDeviceParams Params;
    const bool Opened = Capture->OpenAudioCaptureStream(
        Params,
        [this](const void *InAudio, int32 NumFrames, int32 NumChannels, int32 SampleRate, double, bool)
        {
            FScopeLock Lock(&SamplesLock);
            CaptureRate = SampleRate;
            CaptureChannels = NumChannels;
            Samples.Append(static_cast<const float *>(InAudio), NumFrames * NumChannels);
        },
        1024);
    if (!Opened || !Capture->StartStream())
    {
        Error = FString::Printf(TEXT("Could not open the microphone (%s)."), *Info.DeviceName);
        if (Opened)
            Capture->CloseStream();
        return false;
    }
    bStreamOpen = true;
    CurrentPhase = ESSTalkPhase::Listening;
    Error.Empty();
    return true;
}

void USSNpcTalkSubsystem::EndListeningAndAsk(const FString &Character)
{
    if (CurrentPhase != ESSTalkPhase::Listening)
        return;
    TArray<float> Taken;
    int32 Rate = 0, Channels = 0;
    if (Capture && bStreamOpen)
    {
        Capture->StopStream();
        Capture->CloseStream();
        bStreamOpen = false;
    }
    {
        FScopeLock Lock(&SamplesLock);
        Taken = MoveTemp(Samples);
        Rate = CaptureRate;
        Channels = CaptureChannels;
    }
    const TArray<float> Mono = SSNpcTalk::ToMono16k(Taken, Channels, Rate);
    if (Mono.Num() < 16000 / 4)
    {
        CurrentPhase = ESSTalkPhase::Idle;
        Fail(Character, TEXT("Nothing heard. Hold the key while you speak."));
        return;
    }
    CurrentPhase = ESSTalkPhase::Transcribing;
    SendToWhisper(Character, SSNpcTalk::EncodeWav16k(Mono));
}

void USSNpcTalkSubsystem::Cancel()
{
    if (Capture && bStreamOpen)
    {
        Capture->StopStream();
        Capture->CloseStream();
        bStreamOpen = false;
    }
    if (Pending.IsValid())
    {
        Pending->CancelRequest();
        Pending.Reset();
    }
    CurrentPhase = ESSTalkPhase::Idle;
}

void USSNpcTalkSubsystem::Fail(const FString &Character, const FString &Why)
{
    Error = Why;
    CurrentPhase = ESSTalkPhase::Idle;
    Pending.Reset();
    UE_LOG(LogSSNpcTalk, Warning, TEXT("%s: %s"), *Character, *Why);
    OnFailure.Broadcast(Character, Why);
}

void USSNpcTalkSubsystem::SendToWhisper(const FString &Character, const TArray<uint8> &Wav)
{
    FString Boundary;
    const TArray<uint8> Body = SSNpcTalk::WhisperBody(Wav, Boundary);
    const auto Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(FString::Printf(TEXT("http://127.0.0.1:%d/inference"), WhisperPort));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("multipart/form-data; boundary=") + Boundary);
    Request->SetContent(Body);
    Request->SetTimeout(30.f);
    Request->OnProcessRequestComplete().BindWeakLambda(
        this,
        [this, Character](FHttpRequestPtr, FHttpResponsePtr Response, bool bOk)
        {
            if (!bOk || !Response.IsValid() || Response->GetResponseCode() != 200)
            {
                Fail(Character, TEXT("The transcriber did not answer. Is whisper-server running?"));
                return;
            }
            const FString Text = SSNpcTalk::ParseTranscript(Response->GetContentAsString());
            if (Text.IsEmpty() || Text.StartsWith(TEXT("[")) || Text.StartsWith(TEXT("(")))
            {
                Fail(Character, TEXT("Could not make out any words."));
                return;
            }
            OnTranscript.Broadcast(Character, Text);
            SendToLlama(Character, Text);
        });
    Pending = Request;
    Request->ProcessRequest();
}

void USSNpcTalkSubsystem::SendToLlama(const FString &Character, const FString &Question)
{
    CurrentPhase = ESSTalkPhase::Thinking;
    TArray<SSNpcTalk::FTurn> &Turns = History.FindOrAdd(Character);
    Turns.Add({TEXT("user"), Question});
    while (Turns.Num() > HistoryTurns * 2)
        Turns.RemoveAt(0);
    const FString System = Persona(Character) + (Digest.IsEmpty() ? FString() : TEXT("\n\nRight now: ") + Digest);
    const auto Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(FString::Printf(TEXT("http://127.0.0.1:%d/v1/chat/completions"), LlamaPort));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetContentAsString(SSNpcTalk::ChatBody(System, Turns, MaxReplyTokens, Temperature));
    Request->SetTimeout(60.f);
    Request->OnProcessRequestComplete().BindWeakLambda(
        this,
        [this, Character](FHttpRequestPtr, FHttpResponsePtr Response, bool bOk)
        {
            if (!bOk || !Response.IsValid() || Response->GetResponseCode() != 200)
            {
                Fail(Character, TEXT("No answer came back. Is llama-server running?"));
                return;
            }
            const FString Reply = SSNpcTalk::ParseReply(Response->GetContentAsString());
            if (Reply.IsEmpty())
            {
                Fail(Character, TEXT("The answer was empty."));
                return;
            }
            History.FindOrAdd(Character).Add({TEXT("assistant"), Reply});
            CurrentPhase = ESSTalkPhase::Idle;
            Pending.Reset();
            OnReply.Broadcast(Character, Reply);
        });
    Pending = Request;
    Request->ProcessRequest();
}

FString USSNpcTalkSubsystem::Persona(const FString &Character) const
{
    const FString Dir = FPaths::Combine(FPaths::ProjectContentDir(), PersonaDirectory);
    FString Text;
    for (const FString &Stem : {Character, FString(TEXT("_Default"))})
        if (FFileHelper::LoadFileToString(Text, *FPaths::Combine(Dir, Stem + TEXT(".txt"))) &&
            !Text.TrimStartAndEnd().IsEmpty())
            return Text.Replace(TEXT("{Name}"), *Character);
    return BuiltInPersona(Character);
}

FString USSNpcTalkSubsystem::BuiltInPersona(const FString &Character) const
{
    return FString::Printf(
        TEXT("You are %s, a crew member of the Wayfarer Exchange, a space station far from any planet. "
             "Stay in character. Speak like a person, not an assistant: never offer help menus, never "
             "apologise for limits, never use asterisks or stage directions. Answer in at most two short "
             "sentences. You know only the station and the pilot in front of you; you know nothing of "
             "Earth."),
        *Character);
}
