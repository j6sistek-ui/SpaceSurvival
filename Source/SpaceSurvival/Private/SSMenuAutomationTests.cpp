#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSHUD.h"
#include "SSOutpostSandbox.h"
#include "SSPhase1Data.h"
#include "SSStation.h"
#include "SSStationSeat.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/SkeletalMeshActor.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "Materials/MaterialInstanceDynamic.h"

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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSpatialMenuNavigation, "SpaceSurvival.Menu.SpatialNavigation",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSSpatialMenuNavigation::RunTest(const FString &)
{
    FSSMenuWorld F;
    if (!F.Initialize(*this))
        return false;
    auto *HUD = F.World->SpawnActor<ASSHUD>();
    if (!TestNotNull(TEXT("Create actual Canvas HUD navigation owner"), HUD))
        return false;
    const std::string SettingsBefore = SS::EncodeSettings(F.Instance->Session.settings);
    const std::string RunBefore = SS::EncodeRun(F.Instance->Session.run);
    const std::string AccountBefore = SS::EncodeAccount(F.Instance->Session.account);
    const ESSPanel Panels[] = {ESSPanel::Settings, ESSPanel::Graphics, ESSPanel::Audio, ESSPanel::Controls};
    for (int32 Tab = 0; Tab < UE_ARRAY_COUNT(Panels); ++Tab)
    {
        F.Mode->OpenPanel(Panels[Tab]);
        TestEqual(TEXT("Entering settings focuses its first setting"), F.Mode->SelectedEntry, 4);
        HUD->NavigateMenu(0, -1);
        TestEqual(TEXT("Up reaches the visible active category instead of an unrelated last tab"),
                  F.Mode->SelectedEntry, Tab);
        HUD->NavigateMenu(1, 0);
        TestEqual(TEXT("Right follows the horizontal tab row"), F.Mode->SelectedEntry, FMath::Min(Tab + 1, 3));
        HUD->NavigateMenu(0, 1);
        TestEqual(TEXT("Down enters the setting rows directly"), F.Mode->SelectedEntry, 4);
        HUD->NavigateMenu(0, 1);
        TestEqual(TEXT("Down advances within the vertical setting list"), F.Mode->SelectedEntry, 5);
        HUD->NavigateMenu(0, -1);
        TestEqual(TEXT("Up returns within the vertical setting list"), F.Mode->SelectedEntry, 4);
    }
    F.Mode->OpenPanel(ESSPanel::Ship);
    const int32 Locked = F.Entry(31), Back = F.Entry(0);
    TestFalse(TEXT("Unowned agile ship remains locked"), F.Mode->Entries[Locked].Enabled);
    F.Mode->SelectedEntry = F.Entry(30);
    HUD->NavigateMenu(0, 1);
    TestEqual(TEXT("Controller skips the unavailable ship to reach Back"), F.Mode->SelectedEntry, Back);
    HUD->NavigateMenu(0, 1);
    TestEqual(TEXT("Bottom boundary does not wrap into an unintended action"), F.Mode->SelectedEntry, Back);
    HUD->NavigateMenu(0, -1);
    TestEqual(TEXT("Up skips the unavailable ship in the reverse direction"), F.Mode->SelectedEntry, F.Entry(30));
    TestTrue(TEXT("Navigation alone preserves settings, run and account exactly"),
             SS::EncodeSettings(F.Instance->Session.settings) == SettingsBefore &&
                 SS::EncodeRun(F.Instance->Session.run) == RunBefore &&
                 SS::EncodeAccount(F.Instance->Session.account) == AccountBefore);
    return true;
}

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
    TestEqual(TEXT("Entering controls focuses the first setting after four navigation tabs"), F.Mode->SelectedEntry, 4);
    for (int32 Tab = 0; Tab < 4; ++Tab)
        TestEqual(TEXT("Settings tabs preserve native destinations"), F.Mode->Entries[Tab].Action,
                  Tab == 0 ? 5 : 9 + Tab);
    AddInfo(TEXT("No settings action, persistence API, disk-backed GI initialization or physical input was used; "
                 "this regression exercises the real focus-losing panel rebuild."));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSWardrobePreviewNavigation, "SpaceSurvival.Menu.WardrobePreviewNavigation",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSWardrobePreviewNavigation::RunTest(const FString &)
{
    FSSMenuWorld F;
    if (!F.Initialize(*this))
        return false;
    // Distinct choices share the tracked Acornaut assets; no licensed pack is needed.
    // Three entries distinguish forward from backward instead of making both a toggle.
    FSSHeroDefinition First(ESSHeroIdentity::Acornaut), Second = First, Third = First;
    First.Identity = ESSHeroIdentity::Squirrel;
    First.Id = TEXT("WardrobeTestFirst");
    Second.Identity = ESSHeroIdentity::Nyxar;
    Second.Id = TEXT("WardrobeTestSecond");
    Third.Identity = ESSHeroIdentity::Soldier;
    Third.Id = TEXT("WardrobeTestThird");
    F.Mode->Tuning->Heroes = {First, Second, Third};
    const auto Bodies = F.Mode->WardrobeBodies();
    if (!TestEqual(TEXT("Real installed roster exposes all three test-only choices"), Bodies.Num(), 3))
        return false;
    auto &S = F.Instance->Session;
    S.account.hero = static_cast<int>(First.Identity);
    const std::string Before = SS::EncodeAccount(S.account);
    auto Activate = [&](int32 Action)
    {
        const int32 Index = F.Entry(Action);
        if (!TestTrue(TEXT("Expected wardrobe action is available"),
                      Index != INDEX_NONE && F.Mode->Entries[Index].Enabled))
            return false;
        F.Mode->ActivateEntry(Index);
        return true;
    };

    F.Mode->OpenPanel(ESSPanel::Wardrobe);
    TestEqual(TEXT("Opening wardrobe previews the first installed body"), F.Mode->WardrobePreviewIndex, 0);
    TestEqual(TEXT("Opening wardrobe leaves the worn body alone"), F.Mode->WornHeroId(), First.Id);
    TestTrue(TEXT("Opening wardrobe does not alter the account"), SS::EncodeAccount(S.account) == Before);
    TestFalse(TEXT("Zero direction does not browse"), F.Mode->BrowseWardrobe(0));
    TestTrue(TEXT("Backward navigation is consumed by wardrobe"), F.Mode->BrowseWardrobe(-1));
    TestEqual(TEXT("Backward from first wraps to last"), F.Mode->WardrobePreviewIndex, 2);
    if (!Activate(149))
        return false;
    TestEqual(TEXT("Next action wraps last to first"), F.Mode->WardrobePreviewIndex, 0);
    TestTrue(TEXT("Forward navigation is consumed by wardrobe"), F.Mode->BrowseWardrobe(1));
    TestEqual(TEXT("Forward advances to the second choice"), F.Mode->WardrobePreviewIndex, 1);
    if (!Activate(148))
        return false;
    TestEqual(TEXT("Previous action returns second to first"), F.Mode->WardrobePreviewIndex, 0);
    F.Mode->BrowseWardrobe(1);
    TestTrue(TEXT("Browsing both ways never equips a preview"), SS::EncodeAccount(S.account) == Before);
    if (!Activate(0))
        return false;
    TestFalse(TEXT("Cancel closes wardrobe"), F.Mode->IsMenuOpen());
    TestEqual(TEXT("Cancel clears the preview selection"), F.Mode->WardrobePreviewIndex, INDEX_NONE);
    TestTrue(TEXT("Cancel preserves the original account"), SS::EncodeAccount(S.account) == Before);
    TestFalse(TEXT("Browsing outside wardrobe is rejected"), F.Mode->BrowseWardrobe(1));

    F.Mode->OpenPanel(ESSPanel::Wardrobe);
    F.Mode->BrowseWardrobe(1);
    auto Expected = S.account;
    Expected.hero = static_cast<int>(Second.Identity);
    TestTrue(TEXT("Fixture blocks account storage before explicit selection"), F.Instance->AccountStorageBlocked);
    if (!Activate(150))
        return false;
    TestTrue(TEXT("Only explicit Select changes the account to the previewed identity"),
             SS::EncodeAccount(S.account) == SS::EncodeAccount(Expected));
    TestEqual(TEXT("The worn body follows the selected identity rather than roster index"), F.Mode->WornHeroId(),
              Second.Id);
    TestEqual(TEXT("Selection retains the equipped preview"), F.Mode->WardrobePreviewIndex, 1);
    const int32 Select = F.Entry(150);
    if (!TestTrue(TEXT("Selecting an already worn preview is disabled"),
                  Select != INDEX_NONE && !F.Mode->Entries[Select].Enabled))
        return false;
    F.Mode->ActivateEntry(Select);
    F.Mode->BrowseWardrobe(1);
    F.Mode->OpenPanel(ESSPanel::Ship);
    TestEqual(TEXT("Changing panels clears the preview"), F.Mode->WardrobePreviewIndex, INDEX_NONE);
    TestFalse(TEXT("Changing panels leaves no wardrobe projection active"), F.Mode->HasWardrobeProjection());
    TestFalse(TEXT("Another panel cannot browse the wardrobe"), F.Mode->BrowseWardrobe(-1));
    TestTrue(TEXT("Leaving an unconfirmed preview preserves the equipped account"),
             SS::EncodeAccount(S.account) == SS::EncodeAccount(Expected));

    F.Mode->OpenPanel(ESSPanel::Wardrobe);
    if (!Activate(139))
        return false;
    Expected.hero = -1;
    TestTrue(TEXT("Explicit Station default clears only the saved body choice"),
             SS::EncodeAccount(S.account) == SS::EncodeAccount(Expected));
    TestEqual(TEXT("Station default resolves through the existing roster"), F.Mode->WornHeroId(), First.Id);
    F.Mode->ClosePanel();
    F.Mode->Tuning->Heroes.Empty();
    F.Mode->OpenPanel(ESSPanel::Wardrobe);
    TestEqual(TEXT("Empty wardrobe has no preview selection"), F.Mode->WardrobePreviewIndex, INDEX_NONE);
    TestTrue(TEXT("Empty wardrobe safely consumes forward browsing"), F.Mode->BrowseWardrobe(1));
    TestTrue(TEXT("Empty wardrobe safely consumes backward browsing"), F.Mode->BrowseWardrobe(-1));
    for (int32 Action : {148, 149, 150})
    {
        const int32 Index = F.Entry(Action);
        if (!TestTrue(TEXT("Empty wardrobe disables browsing and selection"),
                      Index != INDEX_NONE && !F.Mode->Entries[Index].Enabled))
            return false;
        F.Mode->ActivateEntry(Index);
    }
    TestEqual(TEXT("Empty-roster actions never manufacture a preview index"), F.Mode->WardrobePreviewIndex, INDEX_NONE);
    TestTrue(TEXT("Empty-roster actions preserve the account"),
             SS::EncodeAccount(S.account) == SS::EncodeAccount(Expected));
    TestTrue(TEXT("Account storage remains blocked throughout the fixture"), F.Instance->AccountStorageBlocked);

    auto *Terminal = F.World->SpawnActor<ASSOutpostTerminal>();
    auto *Projection = F.World->SpawnActor<ASkeletalMeshActor>();
    auto *Asset = LoadObject<USkeletalMesh>(nullptr, *First.MeshPath);
    if (!TestNotNull(TEXT("Create the actual wardrobe terminal"), Terminal) ||
        !TestNotNull(TEXT("Create the placed projection actor"), Projection) ||
        !TestNotNull(TEXT("Load the tracked preview mesh"), Asset))
        return false;
    Terminal->SetActorLocation(FVector(320, -180, 40));
    Terminal->SetActorScale3D(FVector(.75));
    Terminal->HologramHeight = 185.f;
    Terminal->PresentationTarget = Projection;
    Projection->AttachToActor(Terminal, FAttachmentTransformRules::KeepRelativeTransform);
    auto *Original = Projection->GetSkeletalMeshComponent();
    Original->SetSkeletalMeshAsset(Asset);
    Original->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Original->SetRelativeTransform(FTransform(FRotator(0, 27, 0), FVector(32, -16, 60), FVector(1.2)));
    Original->SetHiddenInGame(false);
    auto *OriginalMaterial = Original->GetMaterial(0);
    if (!TestNotNull(TEXT("The original projection has an authored material"), OriginalMaterial))
        return false;
    // A distinct transient material exercises isolation without rendering or shader output.
    Terminal->HologramMaterial = UMaterialInstanceDynamic::Create(OriginalMaterial, Terminal);
    if (!TestNotNull(TEXT("Create the test-only hologram override"), Terminal->HologramMaterial.Get()))
        return false;
    const FTransform OriginalRelative = Original->GetRelativeTransform();
    const FTransform OriginalWorld = Original->GetComponentTransform();
    auto CheckOriginal = [&](bool Visible)
    {
        TestEqual(TEXT("Preview preserves the placed skeletal mesh"), Original->GetSkeletalMeshAsset(), Asset);
        TestTrue(TEXT("Preview preserves the authored relative and world transforms"),
                 Original->GetRelativeTransform().Equals(OriginalRelative) &&
                     Original->GetComponentTransform().Equals(OriginalWorld));
        TestEqual(TEXT("Preview preserves the original material"), Original->GetMaterial(0), OriginalMaterial);
        TestEqual(TEXT("Original visibility is hidden or restored as required"), Original->GetVisibleFlag(), Visible);
        TestFalse(TEXT("Preview never changes the original hidden-in-game flag"), Original->bHiddenInGame);
    };
    auto PreviewComponents = [&]()
    {
        TArray<USkeletalMeshComponent *> Components;
        Terminal->GetComponents(Components);
        Components.RemoveAll([](const USkeletalMeshComponent *Component)
                             { return !IsValid(Component) || !Component->IsRegistered(); });
        return Components;
    };
    FSSHeroDefinition Missing = First;
    Missing.MeshPath = TEXT("/Game/SpaceSurvival/Tests/AbsentWardrobePreview.AbsentWardrobePreview");
    if (!TestFalse(TEXT("Missing-mesh fixture path is not installed"),
                   FSSHeroDefinition::AssetInstalled(Missing.MeshPath)))
        return false;
    Original->SetVisibility(true);
    TestFalse(TEXT("A missing mesh cannot begin a preview"), Terminal->PreviewWardrobe(Missing));
    CheckOriginal(true);
    TestEqual(TEXT("Failed initial preview adds no component"), PreviewComponents().Num(), 0);
    for (bool InitiallyVisible : {true, false})
    {
        Original->SetVisibility(InitiallyVisible);
        if (!TestTrue(TEXT("Real terminal creates a temporary wardrobe preview"), Terminal->PreviewWardrobe(First)))
            return false;
        auto Components = PreviewComponents();
        if (!TestEqual(TEXT("Exactly one transient preview component is registered"), Components.Num(), 1))
            return false;
        auto *Preview = Components[0];
        TestTrue(TEXT("Preview component is transient"), Preview->HasAnyFlags(RF_Transient));
        TestTrue(TEXT("Preview world bounds include the parent's 0.75 scale and fit 185 cm"),
                 FMath::IsNearlyEqual(Preview->Bounds.BoxExtent.Z * 2., 185., .1));
        TestTrue(TEXT("Preview center follows the fitted component bounds"),
                 Terminal->WardrobePreviewCenter().Equals(Preview->Bounds.Origin, .01));
        TestEqual(TEXT("Only the temporary component receives the hologram material"), Preview->GetMaterial(0),
                  Terminal->HologramMaterial.Get());
        CheckOriginal(false);
        if (!TestTrue(TEXT("Browsing replaces the temporary preview"), Terminal->PreviewWardrobe(Second)))
            return false;
        Components = PreviewComponents();
        if (!TestEqual(TEXT("Repeated preview creates no duplicate component"), Components.Num(), 1))
            return false;
        TestTrue(TEXT("Replacement uses a new temporary component"), Components[0] != Preview);
        auto *Replacement = Components[0];
        TestFalse(TEXT("Missing replacement fails safely"), Terminal->PreviewWardrobe(Missing));
        Components = PreviewComponents();
        TestTrue(TEXT("A failed replacement retains the existing temporary preview"),
                 Components.Num() == 1 && Components[0] == Replacement);
        CheckOriginal(false);
        Terminal->EndWardrobePreview();
        TestEqual(TEXT("Ending preview destroys the temporary component"), PreviewComponents().Num(), 0);
        CheckOriginal(InitiallyVisible);
        Terminal->EndWardrobePreview();
        TestEqual(TEXT("Repeated preview cleanup is harmless"), PreviewComponents().Num(), 0);
        CheckOriginal(InitiallyVisible);
    }
    TestTrue(TEXT("Terminal preview and cleanup never change the equipped account"),
             SS::EncodeAccount(S.account) == SS::EncodeAccount(Expected));
    AddInfo(TEXT("Real roster/menu actions were exercised with tracked assets and an in-memory account. "
                 "No disk-backed game-instance initialization, settings persistence or owner save access occurred."));
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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPlayableHeroWardrobe, "SpaceSurvival.Menu.PlayableHeroWardrobe",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSPlayableHeroWardrobe::RunTest(const FString &)
{
    FSSMenuWorld F;
    if (!F.Initialize(*this) || !F.Station(*this))
        return false;
    const FSSHeroDefinition White = F.Mode->Tuning->Hero(ESSHeroIdentity::WhiteHero);
    if (!White.Installed(ESSHeroSlot::Walker))
    {
        AddInfo(TEXT("Private hero package absent; roster order is covered by HeroRoster."));
        return true;
    }
    F.Instance->Session.account.hero = -1;
    TestEqual(TEXT("A fresh account wears white EX7"), F.Mode->WornHeroId(), White.Id);
    const auto Bodies = F.Mode->WardrobeBodies();
    F.Mode->OpenPanel(ESSPanel::Wardrobe);
    for (int32 I = 0; I < Bodies.Num(); ++I)
    {
        TestEqual(TEXT("The existing hologram browser reaches every installed body"), F.Mode->WardrobePreviewIndex, I);
        F.Mode->BrowseWardrobe(1);
    }
    auto *Walker = F.World->SpawnActor<ASSWalker>();
    if (!TestNotNull(TEXT("Spawn actual walking pawn"), Walker))
        return false;
    Walker->Tuning = F.Mode->Tuning;
    const auto RunBefore = SS::EncodeRun(F.Instance->Session.run);
    for (ESSHeroIdentity Identity : {ESSHeroIdentity::GreenHero, ESSHeroIdentity::BlueHero, ESSHeroIdentity::ClothHero,
                                     ESSHeroIdentity::WhiteHero})
    {
        const int32 Index =
            Bodies.IndexOfByPredicate([Identity](const auto &Body) { return Body.Identity == Identity; });
        if (!TestTrue(TEXT("All four supplied heroes are installed together"), Index != INDEX_NONE))
            continue;
        // Account persistence is blocked in this fixture; the real entry action still updates its in-memory choice.
        F.Mode->OpenPanel(ESSPanel::Wardrobe);
        for (int32 Step = 0; Step < Bodies.Num() && F.Mode->WardrobePreviewIndex != Index; ++Step)
            F.Mode->BrowseWardrobe(1);
        TestEqual(TEXT("The hologram browser previews the requested body"), F.Mode->WardrobePreviewIndex, Index);
        F.Mode->ActivateEntry(F.Entry(150));
        TestEqual(TEXT("The selection action stores the stable hero identity"), F.Instance->Session.account.hero,
                  static_cast<int>(Identity));
        TestEqual(TEXT("The saved preference resolves to the selected hero"), F.Mode->WornHeroId(), Bodies[Index].Id);
        Walker->ApplyHero(Bodies[Index].Id);
        if (auto *Node = Walker->GetMesh()->GetSingleNodeInstance())
        {
            Node->SetAnimationAsset(nullptr);
            Walker->Tick(1.f / 60.f);
            TestNotNull(TEXT("A cleared first single-node clip recovers without a wardrobe reselect"),
                        Walker->GetMesh()->GetSingleNodeInstance()->GetCurrentAsset());
        }
        auto *Seat = F.World->SpawnActor<ASSStationSeat>();
        TestNotNull(TEXT("Existing station seats resolve each supplied hero's own seated clip"), Seat->ClipFor(Walker));
        Seat->Destroy();
        TestEqual(TEXT("The actual walking pawn accepts that body"), Walker->GetHero().Identity, Identity);
        TestEqual(TEXT("The supplied suit has a capsule above its 185cm exterior"),
                  Walker->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight(), 96.f);
        auto *Mesh = Walker->GetMesh()->GetSkeletalMeshAsset();
        TestNotNull(TEXT("The walker has a mesh"), Mesh);
        if (Mesh)
        {
            TestEqual(TEXT("The pawn wears the selected mesh"), Mesh->GetPathName(), Bodies[Index].MeshPath);
            TestTrue(TEXT("Every assigned material is present"), Walker->GetMesh()->GetNumMaterials() > 0);
            for (int32 Slot = 0; Slot < Walker->GetMesh()->GetNumMaterials(); ++Slot)
                TestNotNull(TEXT("Each material slot is bound"), Walker->GetMesh()->GetMaterial(Slot));
            for (const FString &Path :
                 {Bodies[Index].IdleClipPath, Bodies[Index].WalkClipPath, Bodies[Index].JogClipPath,
                  Bodies[Index].RunClipPath, Bodies[Index].JumpStartClipPath, Bodies[Index].JumpAirClipPath,
                  Bodies[Index].JumpLandClipPath, Bodies[Index].PilotClipPath})
            {
                auto *Clip = LoadObject<UAnimSequence>(nullptr, *Path);
                if (TestNotNull(TEXT("Each gameplay clip loads"), Clip))
                    TestTrue(TEXT("Each gameplay clip uses this body's skeleton"),
                             Clip->GetSkeleton() == Mesh->GetSkeleton());
            }
        }
    }
    F.Mode->ActivateEntry(F.Entry(139));
    TestEqual(TEXT("Station default forgets the explicit preference"), F.Instance->Session.account.hero, -1);
    TestEqual(TEXT("Station default returns to white EX7"), F.Mode->WornHeroId(), White.Id);
    TestTrue(TEXT("Wardrobe changes preserve the active run"), SS::EncodeRun(F.Instance->Session.run) == RunBefore);
    return true;
}
#endif
