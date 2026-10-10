#include "SSNpcTalk.h"
#include "AudioCaptureCore.h"
#include "Dom/JsonObject.h"
#include "Engine/GameInstance.h"
#include "HAL/PlatformProcess.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "Misc/App.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "TimerManager.h"

// How long after launch a refused or 503 answer still means "reading the model off the disk", and how often the
// question is re-posted meanwhile. The station model is several gigabytes; a cold start is the normal path here.
static constexpr double ColdStartSeconds = 120.0;
static constexpr float ColdStartRetrySeconds = 2.f;

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

FString ChatBody(const FString &System, const TArray<FTurn> &Turns, int32 MaxTokens, float Temperature,
                 float RepeatPenalty)
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
    if (RepeatPenalty != 1.f)
        Root->SetNumberField(TEXT("repeat_penalty"), RepeatPenalty);
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
    {
        // A thinking model that was not told to stop thinking leaks its scratchpad in <think> tags; a caption
        // never wants that, whatever the server was launched with.
        int32 Open = Content.Find(TEXT("<think>"));
        while (Open != INDEX_NONE)
        {
            const int32 Close = Content.Find(TEXT("</think>"), ESearchCase::IgnoreCase, ESearchDir::FromStart, Open);
            Content = Close == INDEX_NONE ? Content.Left(Open) : Content.Left(Open) + Content.Mid(Close + 8);
            Open = Content.Find(TEXT("<think>"));
        }
        FString Finish;
        Choice->TryGetStringField(TEXT("finish_reason"), Finish);
        return TidyReply(Content, Finish == TEXT("length"));
    }
    return FString();
}

FString TidyReply(const FString &Raw, bool bCutShort)
{
    FString Text = Raw.TrimStartAndEnd();
    // Models dress a line up as prose: **bold** markers and quotation marks around the whole thing.
    Text.ReplaceInline(TEXT("**"), TEXT(""));
    Text.TrimStartAndEndInline();
    for (const TCHAR *Pair : {TEXT("\"\""), TEXT("“”")})
        if (Text.Len() > 1 && Text[0] == Pair[0] && Text[Text.Len() - 1] == Pair[1])
            Text = Text.Mid(1, Text.Len() - 2).TrimStartAndEnd();
    if (bCutShort)
    {
        // The token cap fell mid-sentence: keep whole sentences only, unless that would leave nothing.
        int32 End = INDEX_NONE;
        for (int32 I = Text.Len() - 1; I >= 0; --I)
            if (Text[I] == TEXT('.') || Text[I] == TEXT('!') || Text[I] == TEXT('?'))
            {
                End = I;
                break;
            }
        if (End > 0)
            Text = Text.Left(End + 1);
    }
    return Text;
}

bool HasProfanity(const FString &Text)
{
    static const TCHAR *Words[] = {TEXT("fuck"),  TEXT("shit"), TEXT("bitch"), TEXT("bastard"), TEXT("asshole"),
                                   TEXT("prick"), TEXT("dick"), TEXT("damn"),  TEXT("crap"),    TEXT("piss")};
    const FString Lower = Text.ToLower();
    for (const TCHAR *Word : Words)
        if (Lower.Contains(Word))
            return true;
    return false;
}

FString CharacterNameFromMesh(const FString &MeshName)
{
    FString Name = MeshName;
    for (const TCHAR *Prefix : {TEXT("SKM_"), TEXT("SK_")})
        if (Name.StartsWith(Prefix))
        {
            Name.RightChopInline(FCString::Strlen(Prefix));
            break;
        }
    return Name;
}

FSSTalkIdentity IdentityFromTags(const TArray<FName> &Tags, const FString &MeshName)
{
    FSSTalkIdentity Who;
    for (const FName &Tag : Tags)
    {
        FString Key, Value;
        if (!Tag.ToString().Split(TEXT(":"), &Key, &Value))
            continue;
        if (Key == TEXT("TalkName"))
            Who.Name = Value;
        else if (Key == TEXT("TalkType"))
            Who.Type = Value;
        else if (Key == TEXT("TalkRole"))
            Who.Role = Value;
        else if (Key == TEXT("TalkActivity"))
            Who.Activity = Value;
    }
    if (Who.Type.IsEmpty())
        Who.Type = CharacterNameFromMesh(MeshName);
    if (Who.Name.IsEmpty())
        Who.Name = Who.Type;
    return Who;
}

bool HasTalkTag(const TArray<FName> &Tags)
{
    for (const FName &Tag : Tags)
        if (Tag.ToString().StartsWith(TEXT("Talk")))
            return true;
    return false;
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

void USSNpcTalkSubsystem::Initialize(FSubsystemCollectionBase &Collection)
{
    Super::Initialize(Collection);
    // The talk pack is an optional download, not part of the game (owner: "none of this is gameplay, it's all
    // extra"). Without it every entry point stays quiet: no hint, no servers, no error. Checked once; the HUD asks
    // every frame.
    bInstalled = FPaths::FileExists(WhisperServerExe) && FPaths::FileExists(WhisperModel) &&
                 FPaths::FileExists(LlamaServerExe) && FPaths::FileExists(LlamaModel);
    UE_LOG(LogSSNpcTalk, Display, TEXT("talk pack %s"),
           bInstalled ? TEXT("installed") : TEXT("not installed: conversations stay off"));
}

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

bool USSNpcTalkSubsystem::IsEnabled() const
{
    // Never in a headless or automation run: the game mode's arrival, departure and villain-line paths would start
    // the sidecars under every one of the 67 suites otherwise, with nobody to talk.
    return bEnabled && bInstalled && !FApp::IsUnattended() && !GIsAutomationTesting;
}

void USSNpcTalkSubsystem::StopLlama()
{
    if (LlamaProc.IsValid())
    {
        FPlatformProcess::TerminateProc(LlamaProc, true);
        FPlatformProcess::CloseProc(LlamaProc);
        LlamaProc = FProcHandle();
        UE_LOG(LogSSNpcTalk, Display, TEXT("llama-server stopped (%s)"), *FPaths::GetCleanFilename(RunningModel));
    }
    RunningModel.Empty();
}

void USSNpcTalkSubsystem::SetContext(ESSTalkContext Context)
{
    // Owner's split: the station is talk, so the better model loads on arrival; a wave is combat, so launching kills
    // the server and the GPU is the game's again. The flight model comes back when the villain first speaks.
    CurrentContext = Context;
    if (!IsEnabled())
        return;
    if (Context == ESSTalkContext::Station)
        EnsureServers();
    else
        StopLlama();
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
    const bool Station = CurrentContext == ESSTalkContext::Station && FPaths::FileExists(StationLlamaModel);
    const FString &Model = Station ? StationLlamaModel : LlamaModel;
    const FString &Extra = Station ? StationLlamaExtraArgs : LlamaExtraArgs;
    if (LlamaProc.IsValid() && FPlatformProcess::IsProcRunning(LlamaProc) && RunningModel != Model)
        StopLlama();
    if (!LlamaProc.IsValid() || !FPlatformProcess::IsProcRunning(LlamaProc))
    {
        LlamaProc =
            Launch(LlamaServerExe, FString::Printf(TEXT("-m %s -ngl %d --host 127.0.0.1 --port %d -c 4096 -t %d %s"),
                                                   *Quote(Model), LlamaGpuLayers, LlamaPort, Threads, *Extra));
        RunningModel = LlamaProc.IsValid() ? Model : FString();
        LlamaStartedAt = FPlatformTime::Seconds();
        UE_LOG(LogSSNpcTalk, Display, TEXT("llama-server %s on %d with %s"),
               LlamaProc.IsValid() ? TEXT("started") : TEXT("NOT FOUND"), LlamaPort, *FPaths::GetCleanFilename(Model));
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

void USSNpcTalkSubsystem::EndListeningAndAsk(const FSSTalkIdentity &Who)
{
    if (CurrentPhase != ESSTalkPhase::Listening)
        return;
    Known.Add(Who.Name, Who);
    const FString &Character = Who.Name;
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
    if (UGameInstance *GI = GetGameInstance())
        GI->GetTimerManager().ClearTimer(RetryTimer);
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
    // The pilot's words go in as quoted radio traffic with an explicit "answer as X". Measured 2026-10-10 on the
    // stock 1.5B model: handed the bare sentence it refused the first swear ("I can't assist with that"); framed
    // this way it stayed in character on every line and answered profanity in kind. The caption shows the raw text.
    FString Framed =
        Character == TEXT("Director")
            ? FString::Printf(TEXT("Radio from the pilot: \"%s\"\nAnswer them now, as the Director, over the radio."),
                              *Question)
            : FString::Printf(TEXT("The pilot says to you: \"%s\"\nAnswer them now, as %s."), *Question, *Character);
    // The villain mirrors the pilot (owner: "if you swear at him he will swear back"); the crew do not rise to it.
    // Not "in the same language": measured 2026-10-10, Hermes 8B read that literally and answered in Polish.
    if (Character == TEXT("Director") && SSNpcTalk::HasProfanity(Question))
        Framed += TEXT(" The pilot just swore at you: swear straight back, as crude as they were, in English.");
    Framed += TEXT(" Two sentences at most, no quotation marks around your words.");
    Turns.Add({TEXT("user"), Framed});
    while (Turns.Num() > HistoryTurns * 2)
        Turns.RemoveAt(0);
    LlamaRetries = 0;
    PostToLlama(Character);
}

void USSNpcTalkSubsystem::PostToLlama(const FString &Character)
{
    const FString System = Persona(Character) + (Digest.IsEmpty() ? FString() : TEXT("\n\nRight now: ") + Digest);
    const auto Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(FString::Printf(TEXT("http://127.0.0.1:%d/v1/chat/completions"), LlamaPort));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetContentAsString(
        SSNpcTalk::ChatBody(System, History.FindOrAdd(Character), MaxReplyTokens, Temperature, RepeatPenalty));
    Request->SetTimeout(60.f);
    Request->OnProcessRequestComplete().BindWeakLambda(
        this,
        [this, Character](FHttpRequestPtr, FHttpResponsePtr Response, bool bOk)
        {
            if (!bOk || !Response.IsValid() || Response->GetResponseCode() != 200)
            {
                // Refused, or 503, from a server started moments ago: it is still reading its model off the disk.
                // The station/flight split restarts llama on every arrival, so this is the normal path, not a fault.
                const bool Loading = LlamaProc.IsValid() && FPlatformProcess::IsProcRunning(LlamaProc) &&
                                     FPlatformTime::Seconds() - LlamaStartedAt < ColdStartSeconds;
                UGameInstance *GI = GetGameInstance();
                if (Loading && GI)
                {
                    if (LlamaRetries++ == 0)
                        OnStatus.Broadcast(Character, TEXT("is still waking up, hold on..."));
                    GI->GetTimerManager().SetTimer(
                        RetryTimer,
                        FTimerDelegate::CreateWeakLambda(this, [this, Character] { PostToLlama(Character); }),
                        ColdStartRetrySeconds, false);
                    return;
                }
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
    const FSSTalkIdentity *Who = Known.Find(Character);
    // The owner's profile: this character's own file, else the file for their type (seven Nyxar share one), else
    // the default. Then the scenario layer for the role they hold right now, kept in its own file so a role can
    // move between characters (owner: "when they get a special role, make that NPC aware of it").
    TArray<FString> Stems = {Character};
    if (Who && !Who->Type.IsEmpty() && Who->Type != Character)
        Stems.Add(Who->Type);
    Stems.Add(TEXT("_Default"));
    FString Text, Out;
    for (const FString &Stem : Stems)
        if (FFileHelper::LoadFileToString(Text, *FPaths::Combine(Dir, Stem + TEXT(".txt"))) &&
            !Text.TrimStartAndEnd().IsEmpty())
        {
            Out = Text.TrimStartAndEnd();
            break;
        }
    if (Out.IsEmpty())
        Out = BuiltInPersona(Character);
    if (Who && !Who->Role.IsEmpty() &&
        FFileHelper::LoadFileToString(
            Text, *FPaths::Combine(FPaths::ProjectContentDir(), ScenarioDirectory, Who->Role + TEXT(".txt"))) &&
        !Text.TrimStartAndEnd().IsEmpty())
        Out += TEXT("\n\n") + Text.TrimStartAndEnd();
    return Out.Replace(TEXT("{Name}"), *Character);
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
