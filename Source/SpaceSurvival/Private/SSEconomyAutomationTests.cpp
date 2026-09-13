#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSWorldActors.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSEconomyWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = nullptr;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    APlayerController *Controller = nullptr;

    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated economy world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // No Init/InitializeStandalone, save APIs or production account. Normal GameMode BeginPlay only.
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = 0;
        Instance->Session.account.tutorialFlags = 255;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        PreviousWorld = GWorld;
        GWorld = World;
        World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
        if (!Test.TestTrue(TEXT("Install real economy GameMode"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        if (!Test.TestNotNull(TEXT("Resolve actual GameMode"), Mode))
            return false;
        auto *Data = NewObject<USSPhase1Data>(Mode);
        Mode->Tuning = Data;
        Data->WaveCredits = 83;
        Data->UpgradeBasePrice = 137;
        Data->Economy.KillCredits = 19;
        Data->Economy.RepairPrice = 47;
        Data->Economy.UpgradePriceStep = 63;
        Data->Economy.StationRewardCredits = 31;
        Data->Encounters[0].CompletionCredits = 89;
        Data->Encounters[1].CompletionCredits = 113;
        Data->Encounters.Swap(0, 1); // Existing identities, independent of designer row order.
        World->InitializeActorsForPlay(FURL());
        Controller = World->SpawnActor<APlayerController>();
        if (!Test.TestNotNull(TEXT("Create isolated local player"), Controller))
            return false;
        Controller->SetAsLocalPlayerController();
        World->AddController(Controller);
        Controller->SetActorTickEnabled(false);
        World->BeginPlay();
        return true;
    }
    int32 Entry(int32 Action) const
    {
        return Mode->Entries.IndexOfByPredicate([Action](const FSSMenuEntry &Item) { return Item.Action == Action; });
    }
    bool Activate(FAutomationTestBase &Test, int32 Action)
    {
        const int32 Index = Entry(Action);
        if (!Test.TestTrue(TEXT("Actual enabled economy action exists"),
                           Index != INDEX_NONE && Mode->Entries[Index].Enabled))
            return false;
        Mode->ActivateEntry(Index);
        return true;
    }
    void ClearObjectives()
    {
        for (TActorIterator<ASSWorldBody> It(World); It; ++It)
            It->Destroy();
    }
    ~FSSEconomyWorld()
    {
        if (World)
        {
            World->EndPlay(EEndPlayReason::Quit);
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
            GWorld = PreviousWorld;
        }
        if (Instance)
            Instance->RemoveFromRoot();
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSEconomyDataAssetBounds, "SpaceSurvival.Content.EconomyDataAssetBounds",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSEconomyDataAssetBounds::RunTest(const FString &Parameters)
{
    auto *Saved = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
    if (!TestNotNull(TEXT("Persisted economy asset resolves"), Saved))
        return false;
    TestTrue(TEXT("Persisted economy and encounter amounts are valid"), Saved->HasValidEconomyTuning());
    auto *Data = NewObject<USSPhase1Data>();
    SS::Session S;
    TestTrue(TEXT("Unchanged default economy maps"), Data->ApplyEconomyTuning(S.tuning));
    TestTrue(TEXT("All existing domain prices/rewards retain their defaults"),
             S.tuning.waveCredits == 75 && S.tuning.killCredits == 12 && S.tuning.upgradeBasePrice == 130 &&
                 S.tuning.upgradePriceStep == 90 && S.tuning.repairPrice == 35);
    TestTrue(TEXT("Existing completion and station rewards retain their defaults"),
             Data->EventCompletionCredits(false) == 70 && Data->EventCompletionCredits(true) == 100 &&
                 Data->StationRewardCredits() == 25);
    // Reproduce construction of an old serialized encounter row before its stored Kind is restored.
    FSSEncounterDefinition Legacy;
    Legacy.Kind = ESSEncounterKind::DistressCombat;
    Data->Encounters[1] = Legacy;
    Data->Encounters[0].CompletionCredits = 91;
    TestFalse(TEXT("Legacy absent amount requires authoring migration"), Data->HasValidEconomyTuning());
    TestEqual(TEXT("Unmigrated combat still uses its own 100-credit default"), Data->EventCompletionCredits(true), 100);
    TestTrue(TEXT("Explicit content migration fills only absent fields"), Data->InitializeLegacyEconomyDefaults());
    TestEqual(TEXT("Designer-authored salvage value survives migration"), Data->EventCompletionCredits(false), 91);
    TestTrue(TEXT("Migrated rows validate"), Data->HasValidEconomyTuning());
    TestFalse(TEXT("Content migration is idempotent"), Data->InitializeLegacyEconomyDefaults());
    Data->WaveCredits = Data->UpgradeBasePrice = std::numeric_limits<int32>::max();
    Data->Economy.UpgradePriceStep = std::numeric_limits<int32>::max();
    Data->Economy.KillCredits = -2;
    Data->Economy.RepairPrice = 0;
    Data->Economy.StationRewardCredits = -2;
    Data->Encounters[1].CompletionCredits = -2;
    TestFalse(TEXT("Malformed amounts are reported and bounded before domain use"), Data->ApplyEconomyTuning(S.tuning));
    TestTrue(TEXT("Price clamps preserve positive service and safe maximum tier arithmetic"),
             S.tuning.repairPrice == 1 && S.tuning.upgradeBasePrice == 25000000 &&
                 S.tuning.upgradePriceStep == 25000000);
    TestTrue(TEXT("Negative awards become zero; fixed wave bonus retains counter headroom"),
             S.tuning.killCredits == 0 && S.tuning.waveCredits == 99999955 && Data->EventCompletionCredits(true) == 0 &&
                 Data->StationRewardCredits() == 0);
    TestTrue(TEXT("Bounded economy creates a valid in-memory run"), S.StartRun("economy-bounds"));
    S.run.tiers[0] = 4;
    TestEqual(TEXT("Highest purchasable tier price remains within counter range"), S.UpgradePrice(SS::Upgrade::Hull),
              100000000);
    S.run.wave = 10;
    S.run.wavesCompleted = 9;
    S.run.phase = SS::Phase::Climax;
    S.FinishWave();
    TestEqual(TEXT("Maximum valid wave amount plus existing bonus is awarded, not dropped"), S.run.credits, 100000000);
    SS::Run Decoded;
    std::string Error;
    TestTrue(TEXT("Boundary amounts remain accepted by the unchanged run codec"),
             SS::DecodeRun(SS::EncodeRun(S.run), Decoded, Error));
    Data = NewObject<USSPhase1Data>();
    Data->Encounters[2].Kind = ESSEncounterKind::SalvageCache;
    TestFalse(TEXT("Duplicate encounter identity is rejected"), Data->HasValidEconomyTuning());
    Data->Encounters[2].Kind = static_cast<ESSEncounterKind>(99);
    TestFalse(TEXT("Unknown encounter identity is rejected"), Data->HasValidEconomyTuning());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSEconomyRuntimeBridge, "SpaceSurvival.Integration.EconomyRewardBridge",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSEconomyRuntimeBridge::RunTest(const FString &Parameters)
{
    FSSEconomyWorld F;
    if (!F.Initialize(*this))
        return false;
    auto &S = F.Instance->Session;
    TestTrue(TEXT("Actual BeginPlay transfers all domain economy magnitudes"),
             S.tuning.waveCredits == 83 && S.tuning.killCredits == 19 && S.tuning.upgradeBasePrice == 137 &&
                 S.tuning.upgradePriceStep == 63 && S.tuning.repairPrice == 47);
    if (!TestTrue(TEXT("Start in-memory economy fixture"), S.StartRun("economy-runtime")))
        return false;
    F.Mode->NotifyEnemyKilled();
    TestTrue(TEXT("Actual kill notification pays custom credits and tracks earnings"),
             S.run.kills == 1 && S.run.credits == 19 && S.run.totalCreditsEarned == 19);
    S.AwardCredits(2000);
    // Station placement and objective progress are assisted; this is not natural travel or balance evidence.
    S.run.wave = S.run.wavesCompleted = 5;
    S.run.phase = SS::Phase::Station;
    S.run.hull = 20;
    S.run.shield = 0;
    F.Mode->OpenPanel(ESSPanel::Repair);
    const int32 RepairIndex = F.Entry(40);
    if (!TestTrue(TEXT("Repair menu displays custom price"),
                  RepairIndex != INDEX_NONE && F.Mode->Entries[RepairIndex].Label.Contains(TEXT("47 credits"))))
        return false;
    S.run.credits = 46;
    F.Mode->ActivateEntry(RepairIndex);
    TestTrue(TEXT("Stale enabled repair row rechecks funds without mutation"), S.run.credits == 46 && S.run.hull == 20);
    S.run.credits = 2019;
    F.Mode->OpenPanel(ESSPanel::Repair);
    if (!F.Activate(*this, 40))
        return false;
    TestTrue(TEXT("Actual repair action charges exactly the custom price and repairs"),
             S.run.credits == 1972 && S.run.hull == S.Stats().maxHull && S.run.shield == S.Stats().maxShield);
    F.Mode->OpenPanel(ESSPanel::Upgrades);
    if (!F.Activate(*this, 100))
        return false;
    TestTrue(TEXT("First actual upgrade charges custom base price"), S.run.credits == 1835 && S.run.tiers[0] == 2);
    const int32 UpgradeIndex = F.Entry(100);
    TestTrue(TEXT("Next actual upgrade row uses custom tier step"),
             UpgradeIndex != INDEX_NONE && F.Mode->Entries[UpgradeIndex].Label.Contains(TEXT("200 credits")));
    if (!F.Activate(*this, 100))
        return false;
    TestTrue(TEXT("Second upgrade conserves money at custom stepped price"),
             S.run.credits == 1635 && S.run.tiers[0] == 3);
    F.Mode->OpenPanel(ESSPanel::Reward);
    const int32 StationIndex = F.Entry(49);
    TestTrue(TEXT("Station reward label matches custom amount"),
             StationIndex != INDEX_NONE && F.Mode->Entries[StationIndex].Label.Contains(TEXT("31 credits")));
    if (!F.Activate(*this, 49))
        return false;
    TestTrue(TEXT("Station reward pays once"), S.run.credits == 1666 && S.run.stationRewardClaimed);
    F.Mode->ActivateEntry(StationIndex);
    TestEqual(TEXT("Duplicate station click does not pay again"), S.run.credits, 1666);
    if (!TestTrue(TEXT("Existing station departure remains available"), S.LaunchFromStation()))
        return false;
    auto *Ship = F.World->SpawnActor<ASSShip>(FVector(0, 0, 7000), FRotator::ZeroRotator);
    if (!TestNotNull(TEXT("Spawn real ship for event acceptance"), Ship))
        return false;
    F.Controller->Possess(Ship);
    for (bool Combat : {false, true})
    {
        F.ClearObjectives();
        auto *Beacon = F.World->SpawnActor<ASSEncounterBeacon>(Ship->GetActorLocation() + FVector(600, 0, 0),
                                                               FRotator::ZeroRotator);
        if (!TestNotNull(TEXT("Spawn actual optional event"), Beacon))
            return false;
        Beacon->ConfigureEncounter(Combat ? ESSEncounterKind::DistressCombat : ESSEncounterKind::SalvageCache, 6);
        // This fixture spawns the offer directly; normal Director admission sets this flag.
        if (Combat)
            S.run.distressEventSeen = true;
        else
            S.run.salvageEventSeen = true;
        const int32 Before = S.run.credits;
        Beacon->RegisterObjectiveProgress();
        TestEqual(TEXT("Unaccepted signal pays nothing"), S.run.credits, Before);
        if (!TestTrue(TEXT("Actual beacon accepts explicit objective"), Beacon->TryAccept()))
            return false;
        const int32 Count = Beacon->GetObjectiveRemaining();
        for (int32 I = 0; I < Count; ++I)
            Beacon->RegisterObjectiveProgress();
        TestTrue(TEXT("Actual event resolution pays its independent custom completion amount"),
                 Beacon->IsResolved() && S.run.credits == Before + (Combat ? 113 : 89) && S.run.pendingReward &&
                     S.run.rewardCombat == Combat);
        const int32 After = S.run.credits;
        Beacon->RegisterObjectiveProgress();
        TestEqual(TEXT("Resolved objective cannot pay twice"), S.run.credits, After);
        SS::Run Decoded;
        std::string Error;
        const bool DecodedSuccessfully = SS::DecodeRun(SS::EncodeRun(S.run), Decoded, Error);
        if (!TestTrue(FString::Printf(TEXT("Existing codec accepts offered/accepted event state: %s"),
                                      UTF8_TO_TCHAR(Error.c_str())),
                      DecodedSuccessfully))
            return false;
        TestTrue(TEXT("Existing codec preserves pending reward choice and earned credits"),
                 Decoded.pendingReward && Decoded.rewardCombat == Combat && Decoded.credits == After &&
                     Decoded.stationRewardClaimed);
        F.Mode->OpenPanel(ESSPanel::Reward);
        TestTrue(TEXT("Pending event choice keeps station tip inaccessible"), F.Entry(49) == INDEX_NONE);
        if (!F.Activate(*this, Combat ? 48 : 46))
            return false;
        TestTrue(
            TEXT("Existing deliberate module/weapon choice remains free"),
            !S.run.pendingReward && S.run.credits == After &&
                (Combat ? S.run.weapon == SS::Weapon::HeavyCannon : S.run.utility == SS::Utility::VectorThrusters));
    }
    F.ClearObjectives();
    auto *Failed =
        F.World->SpawnActor<ASSEncounterBeacon>(Ship->GetActorLocation() + FVector(600, 0, 0), FRotator::ZeroRotator);
    if (!TestNotNull(TEXT("Spawn failure case beacon"), Failed))
        return false;
    Failed->ConfigureEncounter(ESSEncounterKind::SalvageCache, 6);
    if (!TestTrue(TEXT("Accept failure-case objective"), Failed->TryAccept()))
        return false;
    const int32 BeforeFailure = S.run.credits;
    Failed->FailObjective();
    Failed->RegisterObjectiveProgress();
    TestTrue(TEXT("Failed objective pays nothing and produces no pending choice"),
             S.run.credits == BeforeFailure && !S.run.pendingReward && S.run.eventsCompleted == 2);
    S.run.wave = S.run.wavesCompleted = 10;
    S.run.phase = SS::Phase::Docking;
    TestTrue(TEXT("Existing next docking re-arms the one station interaction"),
             S.CompleteDocking() && !S.run.stationRewardClaimed);
    F.Mode->OpenPanel(ESSPanel::Reward);
    if (!F.Activate(*this, 49))
        return false;
    TestEqual(TEXT("Station 2 pays the same configured tip exactly once"), S.run.credits, BeforeFailure + 31);
    TestTrue(TEXT("Economy bridge does not award death XP or fabricate run history"),
             S.account.xp == 0 && S.account.runs == 0 && S.account.history.empty());
    AddInfo(TEXT("ECONOMY_FIXTURE: actual BeginPlay/menu/actor completion paths; assisted station and objective "
                 "progress, no natural balance or disk I/O."));
    return true;
}
#endif
