#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "Kismet/GameplayStatics.h"
#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSaveRoundTrip,"SpaceSurvival.Save.PayloadRoundTrip",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSSSaveRoundTrip::RunTest(const FString& Parameters)
{
    SS::Session S; S.StartRun("automation-save"); S.run.wave=5; S.run.wavesCompleted=5; S.run.phase=SS::Phase::Station;
    S.run.depotSeen=true; S.run.pendingReward=true; S.run.credits=100; S.run.totalCreditsEarned=100;
    auto* Save=Cast<USSStoredData>(UGameplayStatics::CreateSaveGameObject(USSStoredData::StaticClass()));
    Save->Valid=true; Save->Payload=UTF8_TO_TCHAR(SS::EncodeRun(S.run).c_str());
    TArray<uint8> Bytes;
    TestTrue(TEXT("UE serializes SaveGame"),UGameplayStatics::SaveGameToMemory(Save,Bytes));
    auto* Loaded=Cast<USSStoredData>(UGameplayStatics::LoadGameFromMemory(Bytes));
    TestNotNull(TEXT("UE deserializes SaveGame"),Loaded);
    if(!Loaded)return false;
    SS::Run Restored; std::string Error;
    TestTrue(TEXT("Strict run decode"),SS::DecodeRun(TCHAR_TO_UTF8(*Loaded->Payload),Restored,Error));
    TestEqual(TEXT("Wave"),Restored.wave,5); TestTrue(TEXT("Deferred reward retained"),Restored.pendingReward);
    TestEqual(TEXT("Credits"),Restored.credits,100);
    return true;
}
#endif
