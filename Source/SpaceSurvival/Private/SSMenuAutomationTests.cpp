#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSMenuWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;

    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated menu world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // Init/InitializeStandalone and PersistSettings never run. Account writes
        // are blocked too; settings refresh is exercised through OpenPanel itself.
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = 0;
        Instance->Session.account.tutorialFlags = 255;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        GWorld = World;
        World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
        if (!Test.TestTrue(TEXT("Install actual menu GameMode"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        if (!Test.TestNotNull(TEXT("Resolve actual menu GameMode"), Mode))
            return false;
        Mode->Tuning = NewObject<USSPhase1Data>(Mode);
        World->InitializeActorsForPlay(FURL());
        auto *Controller = World->SpawnActor<APlayerController>();
        if (!Test.TestNotNull(TEXT("Create isolated local menu controller"), Controller))
            return false;
        Controller->SetAsLocalPlayerController();
        World->AddController(Controller);
        Controller->SetActorTickEnabled(false);
        World->BeginPlay();
        return true;
    }
    int32 Entry(int32 Action) const
    {
        return Mode->Entries.IndexOfByPredicate([Action](const FSSMenuEntry &Entry) { return Entry.Action == Action; });
    }
    bool Station(FAutomationTestBase &Test)
    {
        auto &S = Instance->Session;
        if (!Test.TestTrue(TEXT("Start assisted in-memory menu run"), S.StartRun("menu-fixture")))
            return false;
        S.run.wave = S.run.wavesCompleted = 5;
        S.run.phase = SS::Phase::Station;
        return true;
    }
    ~FSSMenuWorld()
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSettingsRefreshFocus, "SpaceSurvival.Menu.SettingsRefreshFocus",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSSettingsRefreshFocus::RunTest(const FString &)
{
    FSSMenuWorld F;
    if (!F.Initialize(*this))
        return false;
    const ESSPanel Panels[] = {ESSPanel::Settings, ESSPanel::Graphics, ESSPanel::Audio, ESSPanel::Controls};
    const int32 Actions[] = {14, 18, 21, 23};
    for (int32 Case = 0; Case < 4; ++Case)
    {
        F.Mode->OpenPanel(Panels[Case]);
        const int32 Index = F.Entry(Actions[Case]);
        if (!TestTrue(TEXT("Non-first setting row exists"), Index > 0))
            return false;
        F.Mode->SelectedEntry = Index;
        // Update a value in memory, then use the exact rebuild path used after a
        // setting action. Calling ActivateEntry for settings would persist to disk.
        auto &Settings = F.Instance->Session.settings;
        Settings.uiScale = 1.2;
        Settings.motionBlur = true;
        Settings.effectsVolume = .4;
        Settings.controllerSensitivity = 1.8;
        const std::string Before = SS::EncodeSettings(Settings);
        for (int32 Refresh = 0; Refresh < 2; ++Refresh)
        {
            F.Mode->OpenPanel(Panels[Case]);
            if (!TestTrue(TEXT("Panel refresh retains a valid selection"),
                          F.Mode->Entries.IsValidIndex(F.Mode->SelectedEntry)))
                return false;
            TestEqual(TEXT("Repeated refresh keeps the same action instead of jumping to row zero"),
                      F.Mode->Entries[F.Mode->SelectedEntry].Action, Actions[Case]);
            TestTrue(TEXT("Rebuilding settings keeps their exact values"), SS::EncodeSettings(Settings) == Before);
        }
    }
    F.Mode->OpenPanel(ESSPanel::Main);
    F.Mode->OpenPanel(ESSPanel::Controls);
    TestEqual(TEXT("Entering a different panel still starts at its first row"), F.Mode->SelectedEntry, 0);
    AddInfo(TEXT("No settings action, persistence API, disk-backed GI initialization or physical input was used; "
                 "this regression exercises the real focus-losing panel rebuild."));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSRewardChoiceEligibility, "SpaceSurvival.Menu.RewardChoiceEligibility",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSRewardChoiceEligibility::RunTest(const FString &)
{
    for (int32 Action : {46, 47, 48})
    {
        FSSMenuWorld F;
        if (!F.Initialize(*this) || !F.Station(*this))
            return false;
        auto &S = F.Instance->Session;
        F.Mode->NotifyEventCompleted(true); // Real reward production; objective survival is assisted.
        auto Fit = [&]()
        {
            return Action == 48
                       ? S.ReplaceWeapon(SS::Weapon::HeavyCannon)
                       : S.EquipUtility(Action == 46 ? SS::Utility::VectorThrusters : SS::Utility::OverdriveCooling);
        };
        TestTrue(TEXT("Prepare already-equipped reward state using existing free equip API"), Fit());
        F.Mode->OpenPanel(ESSPanel::Reward);
        int32 Index = F.Entry(Action);
        if (!TestTrue(TEXT("Already-fitted reward row remains explicit and disabled"),
                      Index != INDEX_NONE && !F.Mode->Entries[Index].Enabled &&
                          F.Mode->Entries[Index].Label.Contains(TEXT("already fitted"))))
            return false;
        std::string Before = SS::EncodeRun(S.run);
        F.Mode->ActivateEntry(Index);
        TestTrue(TEXT("Disabled duplicate cannot consume reward or mutate earned credits/equipment"),
                 SS::EncodeRun(S.run) == Before && S.run.pendingReward);

        S.run.utility = SS::Utility::None;
        S.run.weapon = SS::Weapon::RapidLaser;
        F.Mode->OpenPanel(ESSPanel::Reward);
        Index = F.Entry(Action);
        if (!TestTrue(TEXT("Different equipment is an enabled reward choice"),
                      Index != INDEX_NONE && F.Mode->Entries[Index].Enabled))
            return false;
        TestTrue(TEXT("Equipment can change after row creation"), Fit());
        Before = SS::EncodeRun(S.run);
        F.Mode->ActivateEntry(Index);
        TestTrue(TEXT("Stale enabled duplicate is rechecked at action without consuming reward"),
                 SS::EncodeRun(S.run) == Before && S.run.pendingReward && F.Mode->IsMenuOpen());
        const int32 Alternative = Action == 46 ? 47 : 46;
        Index = F.Entry(Alternative);
        if (!TestTrue(TEXT("A genuine alternative remains available"),
                      Index != INDEX_NONE && F.Mode->Entries[Index].Enabled))
            return false;
        const int32 Credits = S.run.credits, Earned = S.run.totalCreditsEarned;
        F.Mode->ActivateEntry(Index);
        TestTrue(TEXT("Actual alternative is fitted for free and consumes the reward once"),
                 !S.run.pendingReward && !F.Mode->IsMenuOpen() && S.run.credits == Credits &&
                     S.run.totalCreditsEarned == Earned &&
                     S.run.utility ==
                         (Alternative == 46 ? SS::Utility::VectorThrusters : SS::Utility::OverdriveCooling));
        TestTrue(TEXT("Reward choices do not award death XP or create completed runs"),
                 S.account.xp == 0 && S.account.runs == 0 && S.account.history.empty());
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSUpgradeMenuPreview, "SpaceSurvival.Menu.UpgradePreview",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSUpgradeMenuPreview::RunTest(const FString &)
{
    FSSMenuWorld F;
    if (!F.Initialize(*this) || !F.Station(*this))
        return false;
    auto &S = F.Instance->Session;
    S.tuning.baseHull = 120;
    S.tuning.baseShield = 80;
    S.tuning.baseSpeed = 3000;
    S.tuning.baseManeuver = 1500;
    S.tuning.baseWeaponDamage = 20;
    S.run.credits = 2000;
    S.run.hull = 40;
    S.run.shield = 30;
    const std::string Before = SS::EncodeRun(S.run);
    F.Mode->OpenPanel(ESSPanel::Upgrades);
    const TCHAR *Expected[] = {TEXT("120 -> 174 max"), TEXT("80 -> 120 max"), TEXT("30.0 -> 33.9 m/s"),
                               TEXT("15.0 -> 18.0 m/s"), TEXT("20.0 -> 27.0 damage")};
    for (int32 Upgrade = 0; Upgrade < 5; ++Upgrade)
    {
        const int32 Index = F.Entry(100 + Upgrade);
        if (!TestTrue(TEXT("Every core tier has an enabled, priced effective-stat preview"),
                      Index != INDEX_NONE && F.Mode->Entries[Index].Enabled &&
                          F.Mode->Entries[Index].Label.Contains(TEXT("I -> II")) &&
                          F.Mode->Entries[Index].Label.Contains(Expected[Upgrade]) &&
                          !F.Mode->Entries[Index].Label.Contains(TEXT("-1"))))
            return false;
    }
    TestTrue(TEXT("Hull/shield capacity versus repair is disclosed"),
             F.Mode->PanelDetail.Contains(TEXT("capacity only; repair separately")));
    TestTrue(TEXT("Preview copies never charge money, upgrade tiers or refill damaged resources"),
             SS::EncodeRun(S.run) == Before);
    for (int32 Upgrade = 0; Upgrade < 5; ++Upgrade)
        S.run.tiers[Upgrade] = 5;
    const std::string Capped = SS::EncodeRun(S.run);
    F.Mode->OpenPanel(ESSPanel::Upgrades);
    for (int32 Upgrade = 0; Upgrade < 5; ++Upgrade)
    {
        const int32 Index = F.Entry(100 + Upgrade);
        if (!TestTrue(TEXT("Maximum tier is clearly disabled without a negative price"),
                      Index != INDEX_NONE && !F.Mode->Entries[Index].Enabled &&
                          F.Mode->Entries[Index].Label.Contains(TEXT("V | MAX TIER")) &&
                          !F.Mode->Entries[Index].Label.Contains(TEXT("-1"))))
            return false;
        F.Mode->ActivateEntry(Index);
    }
    TestTrue(TEXT("Maximum-tier clicks conserve the full run state"), SS::EncodeRun(S.run) == Capped);
    return true;
}
#endif
