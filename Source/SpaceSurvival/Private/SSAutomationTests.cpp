#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/Guid.h"
#if WITH_DEV_AUTOMATION_TESTS
namespace
{
// Only constructed after both unpredictable QA slots are confirmed absent.
// No production account/settings/suspension slot is ever passed to this guard.
struct FSSQASlotCleanup
{
    FAutomationTestBase &Test;
    const FString AccountSlot;
    const FString RunSlot;
    bool Attempted = false;
    bool Cleaned = false;

    FSSQASlotCleanup(FAutomationTestBase &InTest, const FString &InAccountSlot, const FString &InRunSlot)
        : Test(InTest), AccountSlot(InAccountSlot), RunSlot(InRunSlot)
    {
    }

    bool Clean()
    {
        if (Attempted)
            return Cleaned;
        Attempted = true;
        Cleaned = true;
        for (const FString *Slot : {&AccountSlot, &RunSlot})
        {
            if (UGameplayStatics::DoesSaveGameExist(*Slot, 0) && !UGameplayStatics::DeleteGameInSlot(*Slot, 0))
            {
                Test.AddError(FString::Printf(TEXT("Could not delete exact QA save slot: %s"), **Slot));
                Cleaned = false;
            }
            if (UGameplayStatics::DoesSaveGameExist(*Slot, 0))
            {
                Test.AddError(FString::Printf(TEXT("QA save slot remained after cleanup: %s"), **Slot));
                Cleaned = false;
            }
        }
        return Cleaned;
    }
    ~FSSQASlotCleanup()
    {
        Clean();
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSaveRoundTrip, "SpaceSurvival.Save.PayloadRoundTrip",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSSaveRoundTrip::RunTest(const FString &Parameters)
{
    SS::Session S;
    S.StartRun("automation-save");
    S.run.wave = 5;
    S.run.wavesCompleted = 5;
    S.run.phase = SS::Phase::Station;
    S.run.depotSeen = true;
    S.run.pendingReward = true;
    S.run.credits = 100;
    S.run.totalCreditsEarned = 100;
    auto *Save = Cast<USSStoredData>(UGameplayStatics::CreateSaveGameObject(USSStoredData::StaticClass()));
    if (!TestNotNull(TEXT("Create in-memory QA save"), Save))
        return false;
    Save->Valid = true;
    Save->Payload = UTF8_TO_TCHAR(SS::EncodeRun(S.run).c_str());
    TArray<uint8> Bytes;
    TestTrue(TEXT("UE serializes SaveGame"), UGameplayStatics::SaveGameToMemory(Save, Bytes));
    auto *Loaded = Cast<USSStoredData>(UGameplayStatics::LoadGameFromMemory(Bytes));
    TestNotNull(TEXT("UE deserializes SaveGame"), Loaded);
    if (!Loaded)
        return false;
    SS::Run Restored;
    std::string Error;
    TestTrue(TEXT("Strict run decode"), SS::DecodeRun(TCHAR_TO_UTF8(*Loaded->Payload), Restored, Error));
    TestEqual(TEXT("Wave"), Restored.wave, 5);
    TestTrue(TEXT("Deferred reward retained"), Restored.pendingReward);
    TestEqual(TEXT("Credits"), Restored.credits, 100);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPlatformSaveRoundTrip, "SpaceSurvival.Save.PlatformDiskRoundTrip",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSPlatformSaveRoundTrip::RunTest(const FString &Parameters)
{
    // Exercises UE's platform serializer and disk APIs in this process. This is
    // not a process-restart test or execution of USSGameInstance's transaction.
    const FString Guid = FGuid::NewGuid().ToString(EGuidFormats::Digits);
    const FString AccountSlot = TEXT("SS_QA_") + Guid + TEXT("_Account");
    const FString RunSlot = TEXT("SS_QA_") + Guid + TEXT("_Run");
    if (UGameplayStatics::DoesSaveGameExist(AccountSlot, 0) || UGameplayStatics::DoesSaveGameExist(RunSlot, 0))
    {
        AddError(TEXT("Unexpected GUID QA slot collision; existing slots were left untouched."));
        return false;
    }
    FSSQASlotCleanup Cleanup(*this, AccountSlot, RunSlot);

    SS::Session Session;
    const std::string Suffix = TCHAR_TO_UTF8(*Guid);
    if (!TestTrue(TEXT("Create completed QA run"), Session.StartRun("qa-completed-" + Suffix)))
        return false;
    Session.run.wave = 5;
    Session.run.wavesCompleted = 4;
    Session.RecordKill();
    Session.RecordKill();
    Session.AwardCredits(80);
    Session.EndRun();
    if (!TestEqual(TEXT("Completed run creates one history record"), int32(Session.account.history.size()), 1))
        return false;
    const std::string AccountPayload = SS::EncodeAccount(Session.account);
    if (!TestTrue(TEXT("Account payload uses version 4"), AccountPayload.rfind("SS ACCOUNT 4 ", 0) == 0))
        return false;
    if (!TestTrue(TEXT("Create independent suspended QA run"), Session.StartRun("qa-suspended-" + Suffix)))
        return false;
    Session.run.wave = 5;
    Session.run.wavesCompleted = 5;
    Session.run.phase = SS::Phase::Station;
    Session.run.depotSeen = true;
    Session.run.pendingReward = true;
    Session.run.weaponBuffSeconds = 8.5;
    Session.AwardCredits(200);
    if (!TestTrue(TEXT("QA station purchase"), Session.Purchase(SS::Upgrade::Hull)))
        return false;
    if (!TestTrue(TEXT("QA deliberate utility"), Session.EquipUtility(SS::Utility::VectorThrusters)))
        return false;
    if (!TestTrue(TEXT("QA station contract"), Session.AcceptContract(SS::Contract::Objective)))
        return false;
    const std::string RunPayload = SS::EncodeRun(Session.run);

    auto *AccountRecord = Cast<USSStoredData>(UGameplayStatics::CreateSaveGameObject(USSStoredData::StaticClass()));
    auto *RunRecord = Cast<USSStoredData>(UGameplayStatics::CreateSaveGameObject(USSStoredData::StaticClass()));
    if (!TestNotNull(TEXT("Create QA account record"), AccountRecord) ||
        !TestNotNull(TEXT("Create QA run record"), RunRecord))
        return false;
    AccountRecord->Valid = true;
    AccountRecord->Payload = UTF8_TO_TCHAR(AccountPayload.c_str());
    RunRecord->Valid = true;
    RunRecord->Payload = UTF8_TO_TCHAR(RunPayload.c_str());
    if (!TestTrue(TEXT("Write GUID QA account slot"), UGameplayStatics::SaveGameToSlot(AccountRecord, AccountSlot, 0)))
        return false;
    if (!TestTrue(TEXT("Write GUID QA station slot"), UGameplayStatics::SaveGameToSlot(RunRecord, RunSlot, 0)))
        return false;
    if (!TestTrue(TEXT("QA account file exists"), UGameplayStatics::DoesSaveGameExist(AccountSlot, 0)) ||
        !TestTrue(TEXT("QA station file exists"), UGameplayStatics::DoesSaveGameExist(RunSlot, 0)))
        return false;

    auto *LoadedAccount = Cast<USSStoredData>(UGameplayStatics::LoadGameFromSlot(AccountSlot, 0));
    auto *LoadedRun = Cast<USSStoredData>(UGameplayStatics::LoadGameFromSlot(RunSlot, 0));
    if (!TestNotNull(TEXT("Read QA account from disk"), LoadedAccount) ||
        !TestNotNull(TEXT("Read QA station from disk"), LoadedRun))
        return false;
    if (!TestTrue(TEXT("Both loaded records remain valid"), LoadedAccount->Valid && LoadedRun->Valid))
        return false;
    TestEqual(TEXT("Account wrapper version"), LoadedAccount->Version, 1);
    TestEqual(TEXT("Run wrapper version"), LoadedRun->Version, 1);
    TestEqual(TEXT("Account payload preserved by disk serializer"), LoadedAccount->Payload, AccountRecord->Payload);
    TestEqual(TEXT("Station payload preserved by disk serializer"), LoadedRun->Payload, RunRecord->Payload);
    SS::Account DecodedAccount;
    SS::Run DecodedRun;
    std::string Error;
    if (!TestTrue(TEXT("Decode disk account"),
                  SS::DecodeAccount(TCHAR_TO_UTF8(*LoadedAccount->Payload), DecodedAccount, Error)))
        return false;
    if (!TestTrue(TEXT("Decode disk station run"),
                  SS::DecodeRun(TCHAR_TO_UTF8(*LoadedRun->Payload), DecodedRun, Error)))
        return false;
    if (!TestEqual(TEXT("History survives platform disk serialization"), int32(DecodedAccount.history.size()), 1))
        return false;
    TestTrue(TEXT("History payload fields unchanged"), SS::EncodeAccount(DecodedAccount) == AccountPayload);
    TestTrue(TEXT("Entire station payload unchanged"), SS::EncodeRun(DecodedRun) == RunPayload);
    TestTrue(TEXT("Station remains active"), DecodedRun.active && DecodedRun.phase == SS::Phase::Station);
    TestTrue(TEXT("Deferred choice and utility preserved"),
             DecodedRun.pendingReward && DecodedRun.utility == SS::Utility::VectorThrusters);
    TestTrue(TEXT("Contract and remaining buff preserved"),
             DecodedRun.contract == SS::Contract::Objective && DecodedRun.weaponBuffSeconds == 8.5);

    auto *Consumed = Cast<USSStoredData>(UGameplayStatics::CreateSaveGameObject(USSStoredData::StaticClass()));
    if (!TestNotNull(TEXT("Create consumed QA record"), Consumed))
        return false;
    Consumed->Valid = false;
    Consumed->Payload.Empty();
    if (!TestTrue(TEXT("Overwrite only QA run with consumed marker"),
                  UGameplayStatics::SaveGameToSlot(Consumed, RunSlot, 0)))
        return false;
    auto *LoadedConsumed = Cast<USSStoredData>(UGameplayStatics::LoadGameFromSlot(RunSlot, 0));
    if (!TestNotNull(TEXT("Reload consumed QA record"), LoadedConsumed))
        return false;
    TestFalse(TEXT("Consumed record is invalid for resume"), LoadedConsumed->Valid);
    TestTrue(TEXT("Consumed record removes previous run payload"), LoadedConsumed->Payload.IsEmpty());
    auto *PreservedAccount = Cast<USSStoredData>(UGameplayStatics::LoadGameFromSlot(AccountSlot, 0));
    if (!TestNotNull(TEXT("Account slot remains after run consumption"), PreservedAccount))
        return false;
    TestTrue(TEXT("Account remains valid"), PreservedAccount->Valid);
    TestEqual(TEXT("Consuming run does not rewrite account"), PreservedAccount->Payload, AccountRecord->Payload);
    return Cleanup.Clean();
}
#endif
