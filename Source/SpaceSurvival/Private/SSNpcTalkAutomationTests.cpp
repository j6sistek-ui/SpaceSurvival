#include "Misc/AutomationTest.h"
#include "SSNpcTalk.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#if WITH_DEV_AUTOMATION_TESTS

// The parts of push-to-talk that can be pinned down without a microphone or a server: the audio that leaves
// the game, the two request bodies, the two answers coming back, and the name taken from a crew mesh.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSNpcTalkEncodingTest, "SpaceSurvival.NpcTalk.Encoding",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FSSNpcTalkEncodingTest::RunTest(const FString &)
{
    // 48 kHz stereo, half a second, a 1 kHz tone on the left and silence on the right -> 16 kHz mono at half level.
    TArray<float> Stereo;
    for (int32 F = 0; F < 24000; ++F)
    {
        Stereo.Add(FMath::Sin(2.f * PI * 1000.f * F / 48000.f));
        Stereo.Add(0.f);
    }
    const TArray<float> Mono = SSNpcTalk::ToMono16k(Stereo, 2, 48000);
    TestEqual(TEXT("half a second at 16 kHz"), Mono.Num(), 8000);
    float Peak = 0.f;
    for (float S : Mono)
        Peak = FMath::Max(Peak, FMath::Abs(S));
    TestTrue(TEXT("stereo averaged: the tone peaks near 0.5"), Peak > .45f && Peak <= .5f);
    TestEqual(TEXT("already 16 kHz mono passes through unchanged"), SSNpcTalk::ToMono16k(Mono, 1, 16000).Num(),
              Mono.Num());
    TestEqual(TEXT("empty or bad input is empty"), SSNpcTalk::ToMono16k({}, 0, 0).Num(), 0);

    const TArray<uint8> Wav = SSNpcTalk::EncodeWav16k(Mono);
    TestEqual(TEXT("44-byte header plus 16-bit samples"), Wav.Num(), 44 + 8000 * 2);
    TestTrue(TEXT("RIFF/WAVE tags"), Wav.Num() > 12 && FMemory::Memcmp(Wav.GetData(), "RIFF", 4) == 0 &&
                                         FMemory::Memcmp(Wav.GetData() + 8, "WAVE", 4) == 0);
    uint32 DataBytes = 0, Rate = 0;
    uint16 Channels = 0, Bits = 0;
    FMemory::Memcpy(&Channels, Wav.GetData() + 22, 2);
    FMemory::Memcpy(&Rate, Wav.GetData() + 24, 4);
    FMemory::Memcpy(&Bits, Wav.GetData() + 34, 2);
    FMemory::Memcpy(&DataBytes, Wav.GetData() + 40, 4);
    TestEqual(TEXT("mono"), int32(Channels), 1);
    TestEqual(TEXT("16 kHz"), int32(Rate), 16000);
    TestEqual(TEXT("16-bit"), int32(Bits), 16);
    TestEqual(TEXT("data chunk size"), int32(DataBytes), 16000);

    FString Boundary;
    const TArray<uint8> Body = SSNpcTalk::WhisperBody(Wav, Boundary);
    TestTrue(TEXT("a boundary came back"), !Boundary.IsEmpty());
    const FString BodyText(Body.Num(), reinterpret_cast<const ANSICHAR *>(Body.GetData()));
    TestTrue(TEXT("multipart names the file field"), BodyText.Contains(TEXT("name=\"file\"; filename=\"ask.wav\"")));
    TestTrue(TEXT("multipart asks for json"),
             BodyText.Contains(TEXT("name=\"response_format\"")) && BodyText.Contains(TEXT("\r\n\r\njson\r\n")));
    TestTrue(TEXT("multipart closes with the boundary"), BodyText.EndsWith(TEXT("--") + Boundary + TEXT("--\r\n")));
    TestTrue(TEXT("the wav is inside"), Body.Num() > Wav.Num() + 100);

    TestEqual(TEXT("whisper answer"), SSNpcTalk::ParseTranscript(TEXT("{\"text\":\"  Hey Dread, what's on tap?\\n\"}")),
              FString(TEXT("Hey Dread, what's on tap?")));
    TestEqual(TEXT("whisper garbage"), SSNpcTalk::ParseTranscript(TEXT("not json")), FString());

    TArray<SSNpcTalk::FTurn> Turns = {{TEXT("user"), TEXT("What's on tap?")},
                                      {TEXT("assistant"), TEXT("Synth-ale.")},
                                      {TEXT("user"), TEXT("And gin?")}};
    const FString Chat = SSNpcTalk::ChatBody(TEXT("You are Dread."), Turns, 90, .7f);
    // Read the body back the way the server will: the writer's whitespace is its own business.
    TSharedPtr<FJsonObject> ChatJson;
    TestTrue(TEXT("chat body is JSON"),
             FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Chat), ChatJson) && ChatJson.IsValid());
    if (ChatJson.IsValid())
    {
        const TArray<TSharedPtr<FJsonValue>> *Messages = nullptr;
        TestTrue(TEXT("chat body has four messages"),
                 ChatJson->TryGetArrayField(TEXT("messages"), Messages) && Messages && Messages->Num() == 4);
        if (Messages && Messages->Num() == 4)
        {
            TestEqual(TEXT("system prompt first"), (*Messages)[0]->AsObject()->GetStringField(TEXT("role")),
                      FString(TEXT("system")));
            TestEqual(TEXT("last turn is the question"), (*Messages)[3]->AsObject()->GetStringField(TEXT("content")),
                      FString(TEXT("And gin?")));
            TestEqual(TEXT("the answer in between survives"),
                      (*Messages)[2]->AsObject()->GetStringField(TEXT("content")), FString(TEXT("Synth-ale.")));
        }
        TestEqual(TEXT("bounded"), int32(ChatJson->GetNumberField(TEXT("max_tokens"))), 90);
        TestFalse(TEXT("not streamed"), ChatJson->GetBoolField(TEXT("stream")));
    }
    TestEqual(TEXT("llama answer"),
              SSNpcTalk::ParseReply(
                  TEXT("{\"choices\":[{\"message\":{\"role\":\"assistant\",\"content\":\" Europa gin, cold. \"}}]}")),
              FString(TEXT("Europa gin, cold.")));
    TestEqual(TEXT("llama empty"), SSNpcTalk::ParseReply(TEXT("{\"choices\":[]}")), FString());

    TestEqual(TEXT("crew mesh name"), SSNpcTalk::CharacterNameFromMesh(TEXT("SK_Dread")), FString(TEXT("Dread")));
    TestEqual(TEXT("other mesh name"), SSNpcTalk::CharacterNameFromMesh(TEXT("SquirrelHero")),
              FString(TEXT("SquirrelHero")));
    return true;
}

#endif
