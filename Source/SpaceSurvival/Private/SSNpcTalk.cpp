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
#include "HAL/FileManager.h"
#include "Containers/Ticker.h"
#if WITH_EDITOR
#include "Editor.h"
#endif
#if PLATFORM_WINDOWS
#include "Windows/AllowWindowsPlatformTypes.h"
#include "Windows/WindowsHWrapper.h"
#include <dxgi1_4.h>
namespace SSNpcTalkWindows
{
// Video memory this process may still take on the largest adapter: the DXGI budget minus current use; -1 if unknown.
static int64 FreeVideoMemory()
{
    HMODULE Dxgi = ::GetModuleHandleW(L"dxgi.dll");
    if (!Dxgi)
        Dxgi = ::LoadLibraryW(L"dxgi.dll");
    using FCreateFactory = HRESULT(WINAPI *)(REFIID, void **);
    const auto Create =
        Dxgi ? reinterpret_cast<FCreateFactory>(reinterpret_cast<void *>(::GetProcAddress(Dxgi, "CreateDXGIFactory1")))
             : nullptr;
    IDXGIFactory1 *Factory = nullptr;
    if (!Create || FAILED(Create(__uuidof(IDXGIFactory1), reinterpret_cast<void **>(&Factory))) || !Factory)
        return -1;
    int64 Free = -1;
    SIZE_T Largest = 0;
    IDXGIAdapter1 *Adapter = nullptr;
    for (UINT Index = 0; Factory->EnumAdapters1(Index, &Adapter) != DXGI_ERROR_NOT_FOUND; ++Index)
    {
        DXGI_ADAPTER_DESC1 Desc;
        IDXGIAdapter3 *Adapter3 = nullptr;
        if (SUCCEEDED(Adapter->GetDesc1(&Desc)) && !(Desc.Flags & DXGI_ADAPTER_FLAG_SOFTWARE) &&
            Desc.DedicatedVideoMemory > Largest &&
            SUCCEEDED(Adapter->QueryInterface(__uuidof(IDXGIAdapter3), reinterpret_cast<void **>(&Adapter3))))
        {
            DXGI_QUERY_VIDEO_MEMORY_INFO Info;
            if (SUCCEEDED(Adapter3->QueryVideoMemoryInfo(0, DXGI_MEMORY_SEGMENT_GROUP_LOCAL, &Info)))
            {
                Largest = Desc.DedicatedVideoMemory;
                Free = Info.Budget > Info.CurrentUsage ? int64(Info.Budget - Info.CurrentUsage) : 0;
            }
            Adapter3->Release();
        }
        Adapter->Release();
    }
    Factory->Release();
    return Free;
}
// Puts a process in a job that Windows closes, killing what is in it, when this process ends - crash or not.
static bool KillWithThisProcess(void *Process)
{
    static HANDLE Job = []() -> HANDLE
    {
        HANDLE New = ::CreateJobObjectW(nullptr, nullptr);
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION Info = {};
        Info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        if (New && !::SetInformationJobObject(New, JobObjectExtendedLimitInformation, &Info, sizeof(Info)))
        {
            ::CloseHandle(New);
            New = nullptr;
        }
        return New;
    }();
    return Job && Process && ::AssignProcessToJobObject(Job, static_cast<HANDLE>(Process));
}
} // namespace SSNpcTalkWindows
#include "Windows/HideWindowsPlatformTypes.h"
#endif

// How long after launch a refused or 503 answer still means "reading the model off the disk", and how often the
// question is re-posted meanwhile. The station model is several gigabytes; a cold start is the normal path here.
static constexpr double ColdStartSeconds = 120.0;
static constexpr float ColdStartRetrySeconds = 2.f;

FSSTalkDiagnostics USSNpcTalkSubsystem::Diagnostics() const
{
    FSSTalkDiagnostics Result;
    Result.Phase = CurrentPhase;
    Result.Installed = bInstalled;
    Result.Enabled = IsEnabled();
    auto Running = [](FProcHandle Handle) { return Handle.IsValid() && FPlatformProcess::IsProcRunning(Handle); };
    Result.LlamaRunning = Running(LlamaProc);
    Result.WhisperRunning = Running(WhisperProc);
    Result.VoiceInstalled = bVoiceInstalled;
    Result.VoiceEnabled = bVoiceEnabled;
    Result.VoiceRunning = Running(VoiceProc);
    Result.VoiceReady = Result.VoiceRunning && bVoiceReady;
    Result.VoiceQueue = VoiceJobs.Num(); // Includes the in-flight job until FinishVoiceJob removes it.
    Result.VoiceRestarts = VoiceCrashes;
    Result.VoiceFailures = VoiceFailures;
    Result.TalkError = !Error.IsEmpty();
    if (CurrentPhase == ESSTalkPhase::Thinking && AskedAt > 0)
        Result.RequestSeconds = FMath::Max(0.0, FPlatformTime::Seconds() - AskedAt);
    return Result;
}

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

FSSTalkIdentity PlacedIdentity(const TArray<FName> &ActorTags, const TArray<FName> &ComponentTags,
                               const FString &MeshName, TFunctionRef<FString(const FString &)> Alias)
{
    FSSTalkIdentity Who;
    if (HasTalkTag(ActorTags) || HasTalkTag(ComponentTags))
    {
        TArray<FName> Tags = ActorTags;
        Tags.Append(ComponentTags); // read in order, so a component tag overrides the actor's
        Who = IdentityFromTags(Tags, MeshName);
    }
    else
        Who.Name = Who.Type = CharacterNameFromMesh(MeshName);
    Who.Name = Alias(Who.Name);
    Who.Type = Alias(Who.Type);
    return Who;
}

int32 ChooseGpuLayers(int64 FreeBytes, int64 ModelBytes, int32 Blocks, int64 MarginBytes, int64 FixedBytes)
{
    if (FreeBytes < 0 || ModelBytes <= 0 || Blocks <= 0)
        return 0;
    const int64 Room = FreeBytes - FMath::Max<int64>(MarginBytes, 0) - FMath::Max<int64>(FixedBytes, 0);
    if (Room <= 0)
        return 0;
    if (Room >= ModelBytes)
        return 999;
    const int64 PerLayer = FMath::Max<int64>(ModelBytes / (int64(Blocks) + 1), 1);
    return int32(FMath::Min<int64>(Room / PerLayer, Blocks));
}

int32 GgufBlockCount(const FString &Path)
{
    TUniquePtr<FArchive> Ar(IFileManager::Get().CreateFileReader(*Path));
    if (!Ar)
        return -1;
    // Every read and skip is checked against the file's size first: the file reader asserts on a seek past the end,
    // and a truncated or foreign file must read as "unknown", never stop the game.
    const uint64 Total = uint64(FMath::Max<int64>(Ar->TotalSize(), 0));
    auto Fits = [&Ar, Total](uint64 Bytes) { return Bytes <= Total && uint64(Ar->Tell()) + Bytes <= Total; };
    auto Skip = [&Ar, &Fits](uint64 Bytes)
    {
        if (!Fits(Bytes))
            return false;
        Ar->Seek(Ar->Tell() + int64(Bytes));
        return true;
    };
    uint32 Magic = 0, Version = 0;
    uint64 Tensors = 0, Pairs = 0;
    if (!Fits(24))
        return -1;
    *Ar << Magic << Version;
    if (Magic != 0x46554747u || Version < 2) // "GGUF"; version 1 counted in 32 bits
        return -1;
    *Ar << Tensors << Pairs;
    // Bytes per value by GGUF type: uint8 int8 uint16 int16 uint32 int32 float32 bool string array uint64 int64 float64
    static const uint64 Sizes[] = {1, 1, 2, 2, 4, 4, 4, 1, 0, 0, 8, 8, 8};
    auto String = [&Ar, &Fits, &Skip](FString *Out) -> bool
    {
        uint64 Len = 0;
        if (!Fits(8))
            return false;
        *Ar << Len;
        if (!Out)
            return Skip(Len);
        if (Len > (1u << 16) || !Fits(Len))
            return false; // a key is a short name
        TArray<ANSICHAR> Bytes;
        Bytes.SetNumUninitialized(int32(Len));
        Ar->Serialize(Bytes.GetData(), int64(Len));
        const FUTF8ToTCHAR Text(Bytes.GetData(), int32(Len));
        *Out = FString(Text.Length(), Text.Get());
        return true;
    };
    for (uint64 I = 0; I < Pairs && I < 100000; ++I)
    {
        FString Key;
        uint32 Type = 0;
        if (!String(&Key) || !Fits(4))
            return -1;
        *Ar << Type;
        if (Type > 12)
            return -1;
        if (Key.EndsWith(TEXT(".block_count")))
        {
            if ((Type == 4 || Type == 5) && Fits(4))
            {
                uint32 Value = 0;
                *Ar << Value;
                return int32(FMath::Min<uint32>(Value, MAX_int32));
            }
            if ((Type == 10 || Type == 11) && Fits(8))
            {
                uint64 Value = 0;
                *Ar << Value;
                return int32(FMath::Min<uint64>(Value, MAX_int32));
            }
            return -1;
        }
        if (Type == 8)
        {
            if (!String(nullptr))
                return -1;
        }
        else if (Type == 9)
        {
            uint32 Element = 0;
            uint64 Count = 0;
            if (!Fits(12))
                return -1;
            *Ar << Element << Count;
            if (Element > 12 || Element == 9)
                return -1; // nested arrays: in no header this reads
            if (Element == 8)
            {
                for (uint64 K = 0; K < Count; ++K)
                    if (!String(nullptr))
                        return -1;
            }
            else if (Count > Total / Sizes[Element] || !Skip(Sizes[Element] * Count))
                return -1;
        }
        else if (!Skip(Sizes[Type]))
            return -1;
    }
    return -1;
}

int64 FreeVideoMemoryBytes()
{
#if PLATFORM_WINDOWS
    return SSNpcTalkWindows::FreeVideoMemory();
#else
    return -1;
#endif
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
            Out.Speed = FCString::Atod(*Value);
        else if (Key == TEXT("treatment"))
            Out.Treatment = Value.IsEmpty() ? TEXT("none") : Value.ToLower();
        else if (Key == TEXT("cache_revision"))
            Out.CacheRevision = Value;
    }
}

FString VoiceCacheName(const FString &Reference, double Speed, const FString &Treatment, const FString &Text,
                       const FString &CacheRevision)
{
    FString Material =
        FString::Printf(TEXT("%s|%.2f|%s|%s"), *FPaths::GetCleanFilename(Reference), Speed, *Treatment, *Text);
    if (!CacheRevision.IsEmpty())
        Material += TEXT("|cache_revision=") + CacheRevision;
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

// A helper in this job dies with this process, crash or not, so a kept-alive model never outlives the editor.
bool TieToThisProcess(const FProcHandle &Proc)
{
#if PLATFORM_WINDOWS
    return Proc.IsValid() && SSNpcTalkWindows::KillWithThisProcess(Proc.Get());
#else
    return false;
#endif
}

// Helpers handed from one Play session's subsystem to the next (editor only).
struct FParkedServers
{
    FProcHandle Whisper, Llama, Voice;
    bool bWhisperTied = false, bLlamaTied = false, bVoiceReady = false;
    FString LlamaModel, LlamaKey, VoiceKey;
    double LlamaStartedAt = 0.0, VoiceStartedAt = 0.0, ParkedAt = 0.0, KeepSeconds = 600.0;
    FTSTicker::FDelegateHandle Expiry;
};
FParkedServers &Parked()
{
    static FParkedServers Servers;
    return Servers;
}
void StopParked(FParkedServers &Keep)
{
    for (FProcHandle *Proc : {&Keep.Whisper, &Keep.Llama, &Keep.Voice})
        if (Proc->IsValid())
        {
            FPlatformProcess::TerminateProc(*Proc, true);
            FPlatformProcess::CloseProc(*Proc);
            *Proc = FProcHandle();
        }
}
// Kept helpers that no new Play picked up in time are stopped: they hold ports and video memory.
bool ExpireParked(float)
{
    FParkedServers &Keep = Parked();
    if (FPlatformTime::Seconds() - Keep.ParkedAt < Keep.KeepSeconds)
        return true;
    StopParked(Keep);
    Keep.Expiry.Reset();
    UE_LOG(LogSSNpcTalk, Display, TEXT("npc talk: no Play for %.0f min, the kept helpers are stopped"),
           Keep.KeepSeconds / 60.0);
    return false;
}
bool KeepAcrossPlay()
{
    return GIsEditor && !IsEngineExitRequested();
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
    // The server reads the voices once, when it starts: a kept one serves only the same set, unchanged on disk.
    TArray<FString> VoiceParts;
    for (const auto &Pair : Voices)
        VoiceParts.Add(FString::Printf(
            TEXT("%s@%s@%s"), *Pair.Key, *IFileManager::Get().GetTimeStamp(*Pair.Value.Reference).ToString(),
            *IFileManager::Get().GetTimeStamp(*FPaths::ChangeExtension(Pair.Value.Reference, TEXT("txt"))).ToString()));
    VoiceParts.Sort();
    VoiceKey = FString::Printf(TEXT("%s|%d|%d|%s"), *FString::Join(VoiceParts, TEXT(",")), VoiceThreads, VoicePort,
                               *DefaultVoice);
    TArray<FString> Names;
    Voices.GetKeys(Names);
    UE_LOG(LogSSNpcTalk, Display, TEXT("npc voices %s: %s"),
           bVoiceInstalled ? TEXT("installed") : TEXT("not installed, everyone stays text-only"),
           *FString::Join(Names, TEXT(", ")));
    // Up for the whole session (owner 2026-10-12: it touches no video memory, and the station crew will use it
    // too): it takes ~30 s to load beside the editor, and the first test lost two replies waiting for it.
    AdoptParkedServers();
    EnsureVoice();
}

void USSNpcTalkSubsystem::Deinitialize()
{
    Cancel();
    if (Capture && bStreamOpen)
        Capture->AbortStream();
    Capture.Reset();
    if (KeepAcrossPlay())
        ParkServers();
    else
        StopServers();
    Super::Deinitialize();
}

void USSNpcTalkSubsystem::ParkServers()
{
    FParkedServers &Keep = Parked();
    // Only a helper that dies with the editor is kept; any other is stopped as before.
    auto Park = [](FProcHandle &From, FProcHandle &To, bool bTied) -> bool
    {
        if (!From.IsValid())
            return false;
        if (bTied && !To.IsValid() && FPlatformProcess::IsProcRunning(From))
        {
            To = From;
            From = FProcHandle();
            return true;
        }
        FPlatformProcess::TerminateProc(From, true);
        FPlatformProcess::CloseProc(From);
        From = FProcHandle();
        return false;
    };
    const bool bWhisper = Park(WhisperProc, Keep.Whisper, bWhisperTied);
    if (bWhisper)
        Keep.bWhisperTied = true;
    const FString Model = RunningModel, Key = RunningLlamaKey;
    const bool bLlama = Park(LlamaProc, Keep.Llama, bLlamaTied);
    if (bLlama)
    {
        Keep.bLlamaTied = true;
        Keep.LlamaModel = Model;
        Keep.LlamaKey = Key;
        Keep.LlamaStartedAt = LlamaStartedAt;
    }
    RunningModel.Empty();
    RunningLlamaKey.Empty();
    // The voice leaves with the editor by itself (--parent-pid); its queue belongs to this session and goes.
    bool bVoice = false;
    if (VoiceProc.IsValid() && FPlatformProcess::IsProcRunning(VoiceProc) && !Keep.Voice.IsValid())
    {
        Keep.Voice = VoiceProc;
        Keep.bVoiceReady = bVoiceReady;
        Keep.VoiceStartedAt = VoiceStartedAt;
        Keep.VoiceKey = VoiceKey;
        VoiceProc = FProcHandle();
        bVoice = true;
    }
    StopVoice();
#if WITH_EDITOR
    // A Standalone Game launched from this editor starts its own helpers on the same ports: the kept ones stop first.
    static const bool bWatchStandalone = []
    {
        FEditorDelegates::BeginStandaloneLocalPlay.AddLambda(
            [](const uint32)
            {
                FParkedServers &Parked_ = Parked();
                if (Parked_.Expiry.IsValid())
                {
                    FTSTicker::GetCoreTicker().RemoveTicker(Parked_.Expiry);
                    Parked_.Expiry.Reset();
                }
                StopParked(Parked_);
            });
        return true;
    }();
#endif
    Keep.ParkedAt = FPlatformTime::Seconds();
    Keep.KeepSeconds = FMath::Max(1, KeptHelpersMinutes) * 60.0;
    if ((bWhisper || bLlama || bVoice) && !Keep.Expiry.IsValid())
        Keep.Expiry = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateStatic(&ExpireParked), 15.f);
    UE_LOG(LogSSNpcTalk, Display, TEXT("npc talk: kept running for the next Play: whisper %s, llama %s, voice %s"),
           bWhisper ? TEXT("yes") : TEXT("no"), bLlama ? TEXT("yes") : TEXT("no"), bVoice ? TEXT("yes") : TEXT("no"));
}

void USSNpcTalkSubsystem::AdoptParkedServers()
{
    FParkedServers &Keep = Parked();
    if (Keep.Expiry.IsValid())
    {
        FTSTicker::GetCoreTicker().RemoveTicker(Keep.Expiry);
        Keep.Expiry.Reset();
    }
    if (Keep.Voice.IsValid() && Keep.VoiceKey != VoiceKey)
    {
        UE_LOG(LogSSNpcTalk, Display,
               TEXT("npc talk: the voices changed since the last Play, the voice server restarts"));
        FPlatformProcess::TerminateProc(Keep.Voice, true);
        FPlatformProcess::CloseProc(Keep.Voice);
        Keep.Voice = FProcHandle();
    }
    auto Take = [](FProcHandle &From, FProcHandle &To) -> bool
    {
        if (!From.IsValid())
            return false;
        const bool bAlive = FPlatformProcess::IsProcRunning(From);
        if (bAlive)
            To = From;
        else
            FPlatformProcess::CloseProc(From);
        From = FProcHandle();
        return bAlive;
    };
    const bool bWhisper = Take(Keep.Whisper, WhisperProc);
    if (bWhisper)
        bWhisperTied = Keep.bWhisperTied;
    const bool bLlama = Take(Keep.Llama, LlamaProc);
    if (bLlama)
    {
        bLlamaTied = Keep.bLlamaTied;
        RunningModel = Keep.LlamaModel;
        RunningLlamaKey = Keep.LlamaKey;
        LlamaStartedAt = Keep.LlamaStartedAt;
    }
    const bool bVoice = Take(Keep.Voice, VoiceProc);
    if (bVoice)
    {
        bVoiceReady = Keep.bVoiceReady;
        VoiceStartedAt = Keep.VoiceStartedAt;
    }
    if (bWhisper || bLlama || bVoice)
        UE_LOG(LogSSNpcTalk, Display, TEXT("npc talk: picked up from the last Play: whisper %s, llama %s, voice %s"),
               bWhisper ? TEXT("yes") : TEXT("no"), bLlama ? TEXT("yes") : TEXT("no"),
               bVoice ? TEXT("yes") : TEXT("no"));
}

int32 USSNpcTalkSubsystem::GpuLayersFor(const FString &Model) const
{
    if (LlamaGpuLayers >= 0)
        return LlamaGpuLayers;
    const int64 Free = SSNpcTalk::FreeVideoMemoryBytes();
    const int64 Size = IFileManager::Get().FileSize(*Model);
    const int32 Blocks = SSNpcTalk::GgufBlockCount(Model);
    const int32 Layers =
        SSNpcTalk::ChooseGpuLayers(Free, Size, Blocks, int64(LlamaVramMarginMB) << 20, int64(LlamaVramFixedMB) << 20);
    UE_LOG(LogSSNpcTalk, Display,
           TEXT("llama: %d of %d layers on the GPU (%.1f GB free to the game's budget, %.1f GB kept for it, model %.1f "
                "GB)"),
           Layers >= 999 ? Blocks : Layers, Blocks, Free / 1073741824.0, LlamaVramMarginMB / 1024.0,
           Size / 1073741824.0);
    return Layers;
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
        // Auto layers measure free video memory at the next launch: give its memory a moment to come back, never more
        // than two seconds on the game thread.
        for (const double Until = FPlatformTime::Seconds() + 2.0;
             LlamaGpuLayers < 0 && FPlatformProcess::IsProcRunning(LlamaProc) && FPlatformTime::Seconds() < Until;)
            FPlatformProcess::Sleep(0.01f);
        FPlatformProcess::CloseProc(LlamaProc);
        LlamaProc = FProcHandle();
        UE_LOG(LogSSNpcTalk, Display, TEXT("llama-server stopped (%s)"), *FPaths::GetCleanFilename(RunningModel));
    }
    RunningModel.Empty();
    RunningLlamaKey.Empty();
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
    TieToThisProcess(VoiceProc);
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
    // A replacement recording can opt into a new revision without invalidating other voices' cached lines.
    const FString Dir = VoiceCacheDirectory.IsEmpty()
                            ? FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("NpcTalk"), TEXT("Voices"))
                            : VoiceCacheDirectory;
    const SSNpcTalk::FVoiceProfile *Profile = Voices.Find(Voice);
    if (!Profile)
        return FString();
    return FPaths::Combine(Dir, SSNpcTalk::VoiceCacheName(Profile->Reference, Profile->Speed, Profile->Treatment, Text,
                                                          Profile->CacheRevision));
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
                ++VoiceFailures;
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
            {
                ++VoiceFailures;
                UE_LOG(LogSSNpcTalk, Display, TEXT("npc voices: %d for %s \"%s\""), Response->GetResponseCode(), *Voice,
                       *Text);
            }
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
        if (WhisperProc.IsValid())
            FPlatformProcess::CloseProc(WhisperProc); // it exited by itself
        WhisperProc = Launch(WhisperServerExe, FString::Printf(TEXT("-m %s --host 127.0.0.1 --port %d -t %d"),
                                                               *Quote(WhisperModel), WhisperPort, Threads));
        bWhisperTied = TieToThisProcess(WhisperProc);
        UE_LOG(LogSSNpcTalk, Display, TEXT("whisper-server %s on %d"),
               WhisperProc.IsValid() ? TEXT("started") : TEXT("NOT FOUND"), WhisperPort);
    }
    const bool Station = CurrentContext == ESSTalkContext::Station && FPaths::FileExists(StationLlamaModel);
    const FString &Model = Station ? StationLlamaModel : LlamaModel;
    const FString &Extra = Station ? StationLlamaExtraArgs : LlamaExtraArgs;
    // What the running server was started with: a kept-alive one is reused only for the same model and settings.
    const FString Key = FString::Printf(TEXT("%s|%d|%d|%s"), *Model, LlamaGpuLayers, Threads, *Extra);
    if (LlamaProc.IsValid() && FPlatformProcess::IsProcRunning(LlamaProc) && RunningLlamaKey != Key)
        StopLlama();
    if (!LlamaProc.IsValid() || !FPlatformProcess::IsProcRunning(LlamaProc))
    {
        if (LlamaProc.IsValid())
            FPlatformProcess::CloseProc(LlamaProc); // it exited by itself
        LlamaProc =
            Launch(LlamaServerExe, FString::Printf(TEXT("-m %s -ngl %d --host 127.0.0.1 --port %d -c 4096 -t %d %s"),
                                                   *Quote(Model), GpuLayersFor(Model), LlamaPort, Threads, *Extra));
        bLlamaTied = TieToThisProcess(LlamaProc);
        RunningModel = LlamaProc.IsValid() ? Model : FString();
        RunningLlamaKey = LlamaProc.IsValid() ? Key : FString();
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
