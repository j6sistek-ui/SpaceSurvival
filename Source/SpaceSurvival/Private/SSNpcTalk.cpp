#include "SSNpcTalk.h"
#include "AudioCaptureCore.h"
#include "Dom/JsonObject.h"
#include "Engine/GameInstance.h"
#include "HAL/PlatformProcess.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "Misc/App.h"
#include "Misc/Crc.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
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

TArray<uint8> WhisperBody(const TArray<uint8> &Wav, FString &OutBoundary, const FString &Prompt)
{
    OutBoundary = TEXT("----SSNpcTalk7f3a9c2e");
    // whisper-server's "prompt" field biases it toward the game's own words; without it "Nyxar" is heard as English.
    const FString PromptPart =
        Prompt.IsEmpty()
            ? FString()
            : FString::Printf(TEXT("--%s\r\nContent-Disposition: form-data; name=\"prompt\"\r\n\r\n%s\r\n"),
                              *OutBoundary, *Prompt);
    const FString Head =
        PromptPart +
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
    // Stage directions in asterisks (*offers a sample*) come off whole, however often the rules say not to. Only an
    // asterisk at a word edge delimits one: with a letter on both sides it is a censored word (measured 2026-10-10,
    // NSFW-3B writes "f*cking" and a naive pair match deleted the text between two of them), and it stays.
    auto InWord = [&Text](int32 I)
    { return I > 0 && I + 1 < Text.Len() && FChar::IsAlpha(Text[I - 1]) && FChar::IsAlpha(Text[I + 1]); };
    for (int32 Open = 0; Open < Text.Len(); ++Open)
    {
        if (Text[Open] != TEXT('*') || InWord(Open) || (Open > 0 && FChar::IsAlnum(Text[Open - 1])))
            continue;
        int32 Close = Open + 1;
        while (Close < Text.Len() && (Text[Close] != TEXT('*') || InWord(Close)))
            ++Close;
        if (Close >= Text.Len())
            break;
        Text.RemoveAt(Open, Close - Open + 1);
        --Open;
    }
    // Whatever is left at a word edge is stray formatting ("credits* each").
    for (int32 I = Text.Len() - 1; I >= 0; --I)
        if (Text[I] == TEXT('*') && !InWord(I))
            Text.RemoveAt(I);
    while (Text.Contains(TEXT("  ")))
        Text.ReplaceInline(TEXT("  "), TEXT(" "));
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

FString GivenName(const FString &Type, const FString &Seed)
{
    // Names apart from the seven deck crew TagTalkers already names, so a placed alien never shares one of theirs.
    static const TCHAR *Nyxar[] = {TEXT("Ilo"),   TEXT("Saro"), TEXT("Tev"),  TEXT("Maru"), TEXT("Quill"),
                                   TEXT("Nessa"), TEXT("Brin"), TEXT("Yara"), TEXT("Zeth"), TEXT("Lumi"),
                                   TEXT("Corr"),  TEXT("Avi"),  TEXT("Thal"), TEXT("Rook"), TEXT("Esk")};
    if (Type != TEXT("Nyxar") || Seed.IsEmpty())
        return Type;
    return Nyxar[FCrc::StrCrc32(*Seed) % UE_ARRAY_COUNT(Nyxar)];
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

FVoiceClip VoiceClip(const TArray<uint8> &Body, const FString &RateHeader)
{
    FVoiceClip Clip;
    const FString Header = RateHeader.TrimStartAndEnd();
    const int32 Rate = Header.IsEmpty() ? 48000 : FCString::Atoi(*Header);
    const int32 Bytes = Body.Num() & ~1;
    if (Rate < 8000 || Rate > 48000 || Bytes < 2)
        return Clip;
    Clip.SampleRate = Rate;
    Clip.Pcm.Reserve(Bytes + Rate / 2);
    Clip.Pcm.Append(Body.GetData(), Bytes);
    Clip.Pcm.AddZeroed(Rate / 4 * 2);
    return Clip;
}

FString VoiceArgs(const FString &Script, const FString &Repo, const FString &VoicesDir, const FString &DefaultVoice,
                  int32 Threads, int32 Port, uint32 ParentPid)
{
    for (const FString *Value : {&Script, &Repo, &VoicesDir, &DefaultVoice})
        if (Value->Contains(TEXT("\"")))
            return FString();
    // A trailing slash before the closing quote would escape it on a Windows command line.
    const auto Q = [](FString Value)
    {
        while (Value.EndsWith(TEXT("/")) || Value.EndsWith(TEXT("\\")))
            Value.LeftChopInline(1);
        return FString::Printf(TEXT("\"%s\""), *Value);
    };
    return FString::Printf(TEXT("%s --lux-repo %s --voices %s --default %s --threads %d --port %d --parent-pid %u"),
                           *Q(Script), *Q(Repo), *Q(VoicesDir), *Q(DefaultVoice), FMath::Max(1, Threads), Port,
                           ParentPid);
}

void ParseVoiceProfile(const FString &Text, FVoiceProfile &Out)
{
    TArray<FString> Lines;
    Text.ParseIntoArrayLines(Lines);
    for (const FString &Line : Lines)
    {
        FString Key, Value;
        if (!Line.Split(TEXT("="), &Key, &Value))
            continue;
        Key = Key.TrimStartAndEnd().ToLower();
        Value = Value.TrimStartAndEnd();
        if (Key == TEXT("speed") && Value.IsNumeric())
            Out.Speed = FCString::Atof(*Value);
        else if (Key == TEXT("treatment"))
            Out.Treatment = Value.IsEmpty() ? TEXT("none") : Value.ToLower();
    }
}

FString VoiceCacheName(const FString &Reference, float Speed, const FString &Treatment, const FString &Text)
{
    const FString Material =
        FString::Printf(TEXT("%s|%.2f|%s|%s"), *FPaths::GetCleanFilename(Reference), Speed, *Treatment, *Text);
    const FTCHARToUTF8 Utf8(*Material);
    FMD5 Md5;
    Md5.Update(reinterpret_cast<const uint8 *>(Utf8.Get()), Utf8.Length());
    uint8 Digest[16];
    Md5.Final(Digest);
    return BytesToHex(Digest, 16).ToLower() + TEXT(".pcm");
}

float VoiceDeadline(const FString &Text, bool bReply)
{
    // He speaks ~3.3 words a second and LuxTTS with the entity treatment makes speech about as fast as he says it on
    // four threads beside the game (2026-10-11), so a line takes about its own length to make.
    TArray<FString> Words;
    Text.ParseIntoArrayWS(Words);
    const float Render = Words.Num() / 3.3f;
    return bReply ? FMath::Min(20.f, 4.f + 3.f * Render) : FMath::Min(10.f, 2.f + 2.f * Render);
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
    TArray<FString> Files;
    IFileManager::Get().FindFiles(Files, *FPaths::Combine(FPaths::ProjectContentDir(), PersonaDirectory, TEXT("*.txt")),
                                  true, false);
    for (const FString &File : Files)
        PersonaNames.Add(FPaths::GetBaseFilename(File));
    UE_LOG(LogSSNpcTalk, Display, TEXT("talk pack %s"),
           bInstalled ? TEXT("installed") : TEXT("not installed: conversations stay off"));
    // Voices are their own optional piece: they need none of the above, and the above does not need them. Each
    // <Name>.wav is a character's voice; the .txt beside it is read the way the server reads it.
    TArray<FString> Wavs;
    IFileManager::Get().FindFiles(Wavs, *FPaths::Combine(VoicesPath(), TEXT("*.wav")), true, false);
    for (const FString &Wav : Wavs)
    {
        SSNpcTalk::FVoiceProfile Profile;
        Profile.Reference = FPaths::Combine(VoicesPath(), Wav);
        FString Settings;
        if (FFileHelper::LoadFileToString(Settings, *FPaths::ChangeExtension(Profile.Reference, TEXT("txt"))))
            SSNpcTalk::ParseVoiceProfile(Settings, Profile);
        Voices.Add(FPaths::GetBaseFilename(Wav), Profile);
    }
    bVoiceInstalled = FPaths::FileExists(VoicePython) && FPaths::FileExists(VoiceScriptPath()) &&
                      FPaths::DirectoryExists(VoiceRepo) && !Voices.IsEmpty();
    TArray<FString> Names;
    Voices.GetKeys(Names);
    UE_LOG(LogSSNpcTalk, Display, TEXT("npc voices %s: %s"),
           bVoiceInstalled ? TEXT("installed") : TEXT("not installed, everyone stays text-only"),
           *FString::Join(Names, TEXT(", ")));
    // Up for the whole session (owner 2026-10-12: it touches no video memory, and the station crew will use it
    // too): it takes ~30 s to load beside the editor, and the first test lost two replies waiting for it.
    EnsureVoice();
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
    StopVoice();
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
    // The voice runs in every context; this is where it comes back if it died. Before the talk-pack check: an
    // install with only the voice still gets it.
    EnsureVoice();
    if (!IsEnabled())
        return;
    if (Context == ESSTalkContext::Station)
        EnsureServers();
    else
        StopLlama();
}

bool USSNpcTalkSubsystem::IsVoiceEnabled() const
{
    return bVoiceEnabled && bVoiceInstalled && VoiceCrashes <= 2 && !FApp::IsUnattended() && !GIsAutomationTesting;
}

FString USSNpcTalkSubsystem::VoicesPath() const
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectContentDir(), VoiceDirectory));
}

FString USSNpcTalkSubsystem::VoiceScriptPath() const
{
    // Absolute: ProjectDir() is relative to the engine's Binaries folder, and python runs from the venv's folder.
    return FPaths::IsRelative(VoiceScript)
               ? FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), VoiceScript))
               : VoiceScript;
}

void USSNpcTalkSubsystem::EnsureVoice()
{
    if (!IsVoiceEnabled() || (VoiceProc.IsValid() && FPlatformProcess::IsProcRunning(VoiceProc)))
        return;
    if (VoiceProc.IsValid())
    {
        // It died on its own. A broken install is not restarted for ever: twice, then he stays text-only.
        FPlatformProcess::CloseProc(VoiceProc);
        VoiceProc = FProcHandle();
        bVoiceReady = false;
        UE_LOG(LogSSNpcTalk, Display, TEXT("npc voices: the server stopped by itself"));
        ++VoiceCrashes;
    }
    if (VoiceCrashes > 2)
        return;
    const FString Args =
        SSNpcTalk::VoiceArgs(VoiceScriptPath(), FPaths::ConvertRelativePathToFull(VoiceRepo), VoicesPath(),
                             DefaultVoice, VoiceThreads, VoicePort, FPlatformProcess::GetCurrentProcessId());
    if (Args.IsEmpty())
    {
        UE_LOG(LogSSNpcTalk, Display, TEXT("npc voices: a path holds a double quote"));
        return;
    }
    // The server leaves by itself when this process does (--parent-pid), so a crash never strands its memory.
    VoiceProc = Launch(VoicePython, Args);
    VoiceStartedAt = FPlatformTime::Seconds();
    bVoiceReady = false;
    UE_LOG(LogSSNpcTalk, Display, TEXT("npc voices %s on %d"),
           VoiceProc.IsValid() ? TEXT("starting") : TEXT("NOT FOUND"), VoicePort);
}

void USSNpcTalkSubsystem::StopVoice()
{
    if (VoicePending.IsValid())
    {
        VoicePending->OnProcessRequestComplete().Unbind();
        VoicePending->CancelRequest();
        VoicePending.Reset();
    }
    // Callers waiting on a line drop it by their own deadline; nothing is called back from here.
    VoiceJobs.Reset();
    if (UGameInstance *GI = GetGameInstance())
        GI->GetTimerManager().ClearTimer(VoiceRetryTimer);
    if (VoiceProc.IsValid())
    {
        if (!FPlatformProcess::IsProcRunning(VoiceProc))
        {
            UE_LOG(LogSSNpcTalk, Display, TEXT("npc voices: the server stopped by itself"));
            ++VoiceCrashes;
        }
        // KillTree: the venv's python.exe is a launcher with the real interpreter as its child.
        FPlatformProcess::TerminateProc(VoiceProc, true);
        FPlatformProcess::CloseProc(VoiceProc);
        VoiceProc = FProcHandle();
        UE_LOG(LogSSNpcTalk, Display, TEXT("npc voices stopped"));
    }
    bVoiceReady = false;
}

FString USSNpcTalkSubsystem::VoiceCacheFile(const FString &Voice, const FString &Text) const
{
    // Named by the voice as well as the words: a new recording, speed or treatment makes every line again.
    const FString Dir = VoiceCacheDirectory.IsEmpty()
                            ? FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("NpcTalk"), TEXT("Voices"))
                            : VoiceCacheDirectory;
    const SSNpcTalk::FVoiceProfile *Profile = Voices.Find(Voice);
    if (!Profile)
        return FString();
    return FPaths::Combine(Dir,
                           SSNpcTalk::VoiceCacheName(Profile->Reference, Profile->Speed, Profile->Treatment, Text));
}

bool USSNpcTalkSubsystem::FindVoiceClip(const FString &Voice, const FString &Text, SSNpcTalk::FVoiceClip &Out)
{
    if (const SSNpcTalk::FVoiceClip *Kept = VoiceCache.Find(Voice + TEXT("\n") + Text))
    {
        Out = *Kept;
        return true;
    }
    // On disk: four bytes of sample rate, then the clip as played.
    const FString Path = VoiceCacheFile(Voice, Text);
    TArray<uint8> File;
    if (Path.IsEmpty() || !FFileHelper::LoadFileToArray(File, *Path, FILEREAD_Silent) || File.Num() < 6)
        return false;
    int32 Rate = 0;
    FMemory::Memcpy(&Rate, File.GetData(), sizeof(Rate));
    SSNpcTalk::FVoiceClip Clip;
    Clip.SampleRate = Rate;
    Clip.Pcm.Append(File.GetData() + sizeof(Rate), (File.Num() - int32(sizeof(Rate))) & ~1);
    if (!Clip.IsValid() || Rate < 8000 || Rate > 48000)
        return false;
    Out = VoiceCache.Add(Voice + TEXT("\n") + Text, MoveTemp(Clip));
    return true;
}

bool USSNpcTalkSubsystem::Speak(const FString &Character, const FString &Text, bool bKeep,
                                TFunction<void(const SSNpcTalk::FVoiceClip &)> Done)
{
    const FString Line = Text.TrimStartAndEnd();
    const FString Voice = VoiceFor(Character);
    if (Line.IsEmpty() || !IsVoiceEnabled() || Voice.IsEmpty())
        return false;
    SSNpcTalk::FVoiceClip Clip;
    if (FindVoiceClip(Voice, Line, Clip))
    {
        if (Done)
            Done(Clip);
        return true;
    }
    EnsureVoice();
    if (!VoiceProc.IsValid())
        return false;
    // The same line already being made (his first line of a flight, queued ahead at departure) answers this caller.
    const int32 Same = VoiceJobs.IndexOfByPredicate([&Voice, &Line](const FVoiceJob &Job)
                                                    { return Job.Voice == Voice && Job.Text == Line; });
    if (Same != INDEX_NONE && VoiceJobs[Same].Id == InFlightVoiceJob)
    {
        VoiceJobs[Same].Done = MoveTemp(Done);
        VoiceJobs[Same].bLive = true;
        VoiceJobs[Same].bKeep |= bKeep;
        return true;
    }
    const bool bWasKept = Same != INDEX_NONE && VoiceJobs[Same].bKeep;
    // A newer line overtakes any older one still waiting; scripted lines being made ahead keep their place behind.
    VoiceJobs.RemoveAll(
        [this, &Voice, &Line](const FVoiceJob &Job)
        { return Job.Id != InFlightVoiceJob && (Job.bLive || (Job.Voice == Voice && Job.Text == Line)); });
    VoiceJobs.Insert({++NextVoiceJob, Voice, Line, MoveTemp(Done), true, bKeep || bWasKept}, 0);
    PumpVoice();
    return true;
}

void USSNpcTalkSubsystem::Prerender(const FString &Character, const TArray<FString> &Lines)
{
    const FString Voice = VoiceFor(Character);
    if (!IsVoiceEnabled() || Voice.IsEmpty())
        return;
    int32 Added = 0;
    SSNpcTalk::FVoiceClip Clip;
    for (const FString &Text : Lines)
    {
        const FString Line = Text.TrimStartAndEnd();
        if (Line.IsEmpty() || FindVoiceClip(Voice, Line, Clip) ||
            VoiceJobs.ContainsByPredicate([&Voice, &Line](const FVoiceJob &Job)
                                          { return Job.Voice == Voice && Job.Text == Line; }))
            continue;
        VoiceJobs.Add({++NextVoiceJob, Voice, Line, nullptr, false, true});
        ++Added;
    }
    UE_LOG(LogSSNpcTalk, Display, TEXT("npc voices: %d of %d scripted %s lines to make, the rest are on disk"), Added,
           Lines.Num(), *Voice);
    if (!Added)
        return;
    Prerendered = 0;
    PrerenderStartedAt = FPlatformTime::Seconds();
    EnsureVoice();
    PumpVoice();
}

void USSNpcTalkSubsystem::PumpVoice()
{
    if (VoicePending.IsValid() || !VoiceProc.IsValid())
        return;
    // A line made since it was queued is answered from what was kept.
    SSNpcTalk::FVoiceClip Kept;
    while (!VoiceJobs.IsEmpty() && FindVoiceClip(VoiceJobs[0].Voice, VoiceJobs[0].Text, Kept))
    {
        FVoiceJob Job = MoveTemp(VoiceJobs[0]);
        VoiceJobs.RemoveAt(0);
        if (Job.Done)
            Job.Done(Kept);
    }
    if (VoicePending.IsValid() || VoiceJobs.IsEmpty())
        return; // a callback above may have asked for something new and sent it
    const FVoiceJob &Job = VoiceJobs[0];
    const auto Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(FString::Printf(TEXT("http://127.0.0.1:%d/speak"), VoicePort));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("text/plain; charset=utf-8"));
    Request->SetHeader(TEXT("X-Voice"), Job.Voice);
    Request->SetContentAsString(Job.Text);
    Request->SetTimeout(30.f);
    Request->OnProcessRequestComplete().BindWeakLambda(
        this,
        [this, Id = Job.Id, Voice = Job.Voice, Text = Job.Text, bKeep = Job.bKeep](FHttpRequestPtr,
                                                                                   FHttpResponsePtr Response, bool bOk)
        {
            VoicePending.Reset();
            InFlightVoiceJob = 0;
            if (!bOk || !Response.IsValid())
            {
                // Refused by a server launched moments ago: it opens its port only once it is loaded and warm.
                const bool bLoading = !bVoiceReady && VoiceProc.IsValid() &&
                                      FPlatformProcess::IsProcRunning(VoiceProc) &&
                                      FPlatformTime::Seconds() - VoiceStartedAt < VoiceStartupSeconds;
                UGameInstance *GI = GetGameInstance();
                if (bLoading && GI)
                {
                    GI->GetTimerManager().SetTimer(
                        VoiceRetryTimer, FTimerDelegate::CreateWeakLambda(this, [this] { PumpVoice(); }), 1.f, false);
                    return;
                }
                // Display, never Fail(): a missing voice is not the pilot's problem and must not reach the screen.
                UE_LOG(LogSSNpcTalk, Display, TEXT("npc voices: no answer, the line stays text"));
                FinishVoiceJob(Id, Voice, Text, false, SSNpcTalk::FVoiceClip());
                return;
            }
            if (!bVoiceReady && Response->GetResponseCode() == 200)
            {
                bVoiceReady = true;
                UE_LOG(LogSSNpcTalk, Display, TEXT("npc voices ready after %.1f s"),
                       FPlatformTime::Seconds() - VoiceStartedAt);
            }
            if (Response->GetResponseCode() != 200)
                UE_LOG(LogSSNpcTalk, Display, TEXT("npc voices: %d for %s \"%s\""), Response->GetResponseCode(), *Voice,
                       *Text);
            FinishVoiceJob(
                Id, Voice, Text, bKeep,
                Response->GetResponseCode() == 200
                    ? SSNpcTalk::VoiceClip(Response->GetContent(), Response->GetHeader(TEXT("X-Sample-Rate")))
                    : SSNpcTalk::FVoiceClip());
        });
    VoicePending = Request;
    InFlightVoiceJob = Job.Id;
    Request->ProcessRequest();
}

void USSNpcTalkSubsystem::FinishVoiceJob(int32 Id, const FString &Voice, const FString &Text, bool bKeep,
                                         const SSNpcTalk::FVoiceClip &Clip)
{
    if (Clip.IsValid() && bKeep)
    {
        VoiceCache.Add(Voice + TEXT("\n") + Text, Clip);
        TArray<uint8> File;
        File.Append(reinterpret_cast<const uint8 *>(&Clip.SampleRate), sizeof(Clip.SampleRate));
        File.Append(Clip.Pcm);
        FFileHelper::SaveArrayToFile(File, *VoiceCacheFile(Voice, Text));
    }
    TFunction<void(const SSNpcTalk::FVoiceClip &)> Done;
    bool bWasAhead = false;
    const int32 Index = VoiceJobs.IndexOfByPredicate([Id](const FVoiceJob &Job) { return Job.Id == Id; });
    if (Index != INDEX_NONE)
    {
        Done = MoveTemp(VoiceJobs[Index].Done);
        bWasAhead = !VoiceJobs[Index].bLive;
        VoiceJobs.RemoveAt(Index);
    }
    // Anyone else waiting on the same words is answered by this take.
    TArray<TFunction<void(const SSNpcTalk::FVoiceClip &)>> Others;
    if (Clip.IsValid())
        for (int32 Other = VoiceJobs.Num() - 1; Other >= 0; --Other)
            if (VoiceJobs[Other].Voice == Voice && VoiceJobs[Other].Text == Text)
            {
                if (VoiceJobs[Other].Done)
                    Others.Add(MoveTemp(VoiceJobs[Other].Done));
                VoiceJobs.RemoveAt(Other);
            }
    if (bWasAhead && ++Prerendered && !VoiceJobs.ContainsByPredicate([](const FVoiceJob &Job) { return !Job.bLive; }))
        UE_LOG(LogSSNpcTalk, Display, TEXT("npc voices: made %d scripted lines in %.1f s"), Prerendered,
               FPlatformTime::Seconds() - PrerenderStartedAt);
    if (Done)
        Done(Clip);
    for (auto &Other : Others)
        Other(Clip);
    PumpVoice();
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
    AskedAt = FPlatformTime::Seconds();
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
    const TArray<uint8> Body = SSNpcTalk::WhisperBody(
        Wav, Boundary, WhisperVocabulary + (Character.IsEmpty() ? TEXT("") : TEXT(" ") + Character));
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
            // Logged so a strange answer can be read back after play (owner: "responded something weird").
            UE_LOG(LogSSNpcTalk, Display, TEXT("%s heard: \"%s\" (%.1f s)"), *Character, *Text,
                   FPlatformTime::Seconds() - AskedAt);
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
    // The pilot hears him while flying (owner: "his lines absolutely can't be long"); the crew are read on foot.
    Framed += Character == TEXT("Director")
                  ? TEXT(" One short sentence, two at most, under twenty words, no quotation marks around your words.")
                  : TEXT(" Two sentences at most, no quotation marks around your words.");
    // A question that never got its answer (server down, cancelled) must not stay in the history: the Gemma 3 and
    // Mistral chat templates raise on two user turns in a row, and the whole request fails with a 500.
    if (Turns.Num() && Turns.Last().Role == TEXT("user"))
        Turns.Pop();
    Turns.Add({TEXT("user"), Framed});
    while (Turns.Num() > HistoryTurns * 2)
        Turns.RemoveAt(0);
    LlamaRetries = 0;
    PostToLlama(Character);
}

void USSNpcTalkSubsystem::PostToLlama(const FString &Character)
{
    // No "Right now:" label on the digest: measured 2026-10-10, two models copied the label back and narrated
    // "Right now: I'm stretching..." after every line, and one recited the whole digest as its answer.
    const FString System = Persona(Character) + (Digest.IsEmpty() ? FString() : TEXT("\n\n") + Digest);
    const auto Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(FString::Printf(TEXT("http://127.0.0.1:%d/v1/chat/completions"), LlamaPort));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetContentAsString(SSNpcTalk::ChatBody(
        System, History.FindOrAdd(Character),
        Character == TEXT("Director") ? FMath::Min(MaxReplyTokens, DirectorReplyTokens) : MaxReplyTokens, Temperature,
        RepeatPenalty));
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
            UE_LOG(LogSSNpcTalk, Display, TEXT("%s answered after %.1f s: %s"), *Character,
                   FPlatformTime::Seconds() - AskedAt, *Reply);
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
