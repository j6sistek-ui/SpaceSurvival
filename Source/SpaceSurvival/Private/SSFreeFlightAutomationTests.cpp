#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "Components/SphereComponent.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "Physics/Experimental/PhysScene_Chaos.h"
#include "UObject/UnrealType.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSFreeFlightWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    APlayerController *Controller = nullptr;
    ULocalPlayer *LocalPlayer = nullptr;

    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated Free Flight world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = 0;
        Instance->Session.account.tutorialFlags = 255;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        GWorld = World;
        World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
        if (!Test.TestTrue(TEXT("Install production Free Flight mode"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        auto *Content = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
        if (!Test.TestNotNull(TEXT("Resolve actual mode"), Mode) ||
            !Test.TestNotNull(TEXT("Resolve actual flight tuning"), Content))
            return false;
        Mode->Tuning = DuplicateObject<USSPhase1Data>(Content, Mode);
        World->InitializeActorsForPlay(FURL());
        // No disk-backed GI initialization or GameMode BeginPlay. The real menu,
        // departure, actor ticks and return APIs run after this controlled setup.
        World->SetBegunPlay(true);
        if (World->GetPhysicsScene())
            World->GetPhysicsScene()->OnWorldBeginPlay();
        Controller = World->SpawnActor<APlayerController>();
        if (!Test.TestNotNull(TEXT("Create actual local controller"), Controller))
            return false;
        LocalPlayer = NewObject<ULocalPlayer>(GEngine, NAME_None, RF_Transient);
        Instance->AddLocalPlayer(LocalPlayer, FPlatformUserId::CreateFromInternalId(0));
        Controller->SetPlayer(LocalPlayer);
        Controller->SetActorTickEnabled(false);
        World->AddController(Controller);
        Mode->RegisterAllActorTickFunctions(true, true);
        Mode->SetActorTickEnabled(true);
        Mode->ShowHangar();
        return Test.TestTrue(TEXT("Real home hangar possesses a walking pawn"),
                             Mode->InHangar() && Cast<ASSWalker>(Controller->GetPawn()) != nullptr);
    }

    int32 Entry(int32 Action) const
    {
        return Mode->Entries.IndexOfByPredicate([Action](const FSSMenuEntry &Entry) { return Entry.Action == Action; });
    }

    ASSStation *Hub() const
    {
        const auto *Property = FindFProperty<FObjectPropertyBase>(ASSGameMode::StaticClass(), TEXT("Hub"));
        return Property ? Cast<ASSStation>(Property->GetObjectPropertyValue_InContainer(Mode)) : nullptr;
    }

    void Frames(int32 Count)
    {
        for (int32 Index = 0; Index < Count; ++Index)
        {
            ++GFrameCounter;
            World->Tick(LEVELTICK_All, 1.f / 60.f);
        }
    }

    ~FSSFreeFlightWorld()
    {
        if (World)
        {
            if (Mode)
                Mode->ClosePanel();
            if (Instance && LocalPlayer)
                Instance->RemoveLocalPlayer(LocalPlayer);
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSFreeFlightLifecycle, "SpaceSurvival.Flight.FreeFlightLifecycle",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSFreeFlightLifecycle::RunTest(const FString &)
{
    FSSFreeFlightWorld F;
    if (!F.Initialize(*this))
        return false;
    ASSStation *Home = F.Hub();
    if (!TestNotNull(TEXT("Home has its actual station actor"), Home) ||
        !TestTrue(TEXT("Default private station is present for the real parked ship"), Home->IsUsingFunctionalLayout()))
        return false;
    const FVector HomeDock = Home->PadDockPosition();
    const std::string AccountBefore = SS::EncodeAccount(F.Instance->Session.account);
    const std::string RunBefore = SS::EncodeRun(F.Instance->Session.run);
    F.Mode->OpenPanel(ESSPanel::Launch);
    const int32 Start = F.Entry(3), Continue = F.Entry(2), Practice = F.Entry(52);
    if (!TestTrue(TEXT("Home launch offers distinct Start Survival, Continue Survival and Free Flight choices"),
                  Start != INDEX_NONE && Continue != INDEX_NONE && Practice != INDEX_NONE &&
                      F.Mode->Entries[Start].Enabled && F.Mode->Entries[Practice].Enabled &&
                      F.Mode->Entries[Start].Label == TEXT("Start Survival") &&
                      F.Mode->Entries[Continue].Label == TEXT("Continue Survival") &&
                      F.Mode->Entries[Practice].Label == TEXT("Free Flight")))
        return false;
    TestFalse(TEXT("Unavailable checkpoint is not offered as a successful Continue"),
              F.Mode->Entries[Continue].Enabled);
    // The production Free Flight action has no save calls. Unblock only that
    // in-memory admission; every other menu read/write remains blocked in this fixture.
    F.Instance->AccountStorageBlocked = false;
    F.Mode->ActivateEntry(Practice);
    F.Instance->AccountStorageBlocked = true;
    ASSShip *Ship = F.Mode->GetPlayerShip();
    if (!TestNotNull(TEXT("Free Flight uses the actual departure ship"), Ship) ||
        !TestTrue(TEXT("Actual launch action owns the practice session and the possessed departing pawn"),
                  F.Instance->IsFreeFlight() && F.Mode->IsDepartingStation() && F.Controller->GetPawn() == Ship &&
                      Ship->IsTakingOff() && !F.Mode->IsMenuOpen()))
        return false;
    const int32 Wave = F.Instance->Session.run.wave;
    F.Frames(210);
    TestFalse(TEXT("Real takeoff finishes without starting survival waves"), Ship->IsTakingOff());
    TestTrue(TEXT("Zero throttle after launch is an engine-off command"), FMath::IsNearlyZero(Ship->GetThrottle()));
    Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 1.f, false, false);
    F.Frames(45);
    TestTrue(TEXT("Ordinary throttle accelerates the real Free Flight pawn without boost"),
             Ship->GetVelocity().Size() > 100.f && !F.Instance->Session.run.boosting);
    TestTrue(TEXT("Practice begins inside the real departure zone"),
             F.Mode->IsDepartingStation() && F.Mode->IsInStationZone());
    Ship->RequestDodge();
    TestTrue(TEXT("Practice near the pad admits its first dodge"), F.Instance->Session.run.dodgeCooldown > 0.);
    F.Frames(FMath::CeilToInt((F.Instance->Session.tuning.dodgeCooldownSeconds + .25) * 60.));
    TestTrue(TEXT("Practice recovery continues while remaining inside the departure zone"),
             F.Mode->IsDepartingStation() && F.Mode->IsInStationZone() && F.Instance->Session.run.dodgeCooldown <= 0. &&
                 F.Instance->Session.run.wave == Wave);

    Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 0.f, false, false);
    if (!TestTrue(TEXT("The real depot mooring path can hold practice flight"), Ship->BeginMooring()))
        return false;
    F.Frames(2);
    TestTrue(TEXT("Mooring actually stops the physical ship"), Ship->GetVelocity().Size() < 1.f);
    Ship->EndMooring();
    F.Frames(30);
    TestTrue(TEXT("Leaving mooring with engine off does not inject the former automatic cruise velocity"),
             !Ship->IsMoored() && FMath::IsNearlyZero(Ship->GetThrottle()) && Ship->GetVelocity().Size() < 5.f &&
                 !F.Instance->Session.run.boosting);

    // Fixture placement crosses the existing departure boundary. This exercises
    // the real boundary transaction, not physical-pilot navigation acceptance.
    Ship->SetActorLocation(Home->PadDockPosition() + Home->PadDockRotation().Vector() * 22000.f + FVector(0, 0, 1200),
                           false, nullptr, ETeleportType::TeleportPhysics);
    F.Frames(2);
    TestFalse(TEXT("Free Flight can leave the station departure zone"), F.Mode->IsDepartingStation());
    TestTrue(TEXT("Leaving in practice retains the same home landing destination"), F.Hub() == Home && IsValid(Home));
    Ship->RequestDodge();
    TestTrue(TEXT("Practice admits a real dodge"), F.Instance->Session.run.dodgeCooldown > 0.);
    F.Frames(FMath::CeilToInt((F.Instance->Session.tuning.dodgeCooldownSeconds + .25) * 60.));
    TestTrue(TEXT("Practice ticks recovery without advancing to another wave"),
             F.Instance->Session.run.dodgeCooldown <= 0. && F.Instance->Session.run.wave == Wave &&
                 F.Instance->Session.run.phase == SS::Phase::Approach && F.Instance->Session.run.phaseSeconds == 0.);
    Ship->RequestDodge();
    TestTrue(TEXT("Dodge remains usable after its first activation in Free Flight"),
             F.Instance->Session.run.dodgeCooldown > 0.);
    TestTrue(TEXT("Actual Director remains inactive and admits no threats during practice"),
             !F.Mode->Director->IsActive() && F.Mode->Director->GetActiveThreatCount() == 0);
    TestFalse(TEXT("Practice cannot create a survival checkpoint"), F.Instance->SuspendRun());
    TestTrue(TEXT("Checkpoint denial identifies practice protection"),
             F.Instance->LastSaveError.Contains(TEXT("Free Flight")));

    // A previous survival destination must never replace the retained home
    // when the player lands. Admission/steering have their own tests; here the
    // real domain + ship choreography reaches the GameMode arrival handoff.
    F.Mode->StationTarget = FVector(270000, -180000, 42000);
    if (!TestTrue(TEXT("Practice can begin the normal docking transition"), F.Instance->Session.BeginDocking()))
        return false;
    Ship->SetDockingTarget(Home->PadDockPosition(), Home->PadDockRotation(),
                           float(F.Instance->Session.run.phaseDuration));
    F.Frames(210);
    TestTrue(TEXT("Landing preserves the actual home hub despite an unrelated old survival destination"),
             F.Hub() == Home && IsValid(Home) && Home->IsHome());
    TestTrue(TEXT("Practice arrival finishes on the retained home pad and returns walking possession"),
             F.Instance->Session.run.phase == SS::Phase::Station && F.Mode->InHangar() &&
                 Cast<ASSWalker>(F.Controller->GetPawn()) != nullptr && Ship->GetActorLocation().Equals(HomeDock, .1));
    F.Mode->OpenPanel(ESSPanel::Main);
    const int32 ReturnHome = F.Entry(53);
    if (!TestTrue(TEXT("Practice pause menu exposes safe return home"), ReturnHome != INDEX_NONE))
        return false;
    F.Mode->ActivateEntry(ReturnHome);
    TestFalse(TEXT("Return action ends practice"), F.Instance->IsFreeFlight());
    TestTrue(TEXT("Return action restores the exact prior account and inactive survival snapshot"),
             SS::EncodeAccount(F.Instance->Session.account) == AccountBefore &&
                 SS::EncodeRun(F.Instance->Session.run) == RunBefore);
    TestTrue(TEXT("Return ends at home with the launch choices available"),
             F.Mode->InHangar() && F.Mode->Panel == ESSPanel::Launch && F.Entry(52) != INDEX_NONE &&
                 Cast<ASSWalker>(F.Controller->GetPawn()) != nullptr);
    AddInfo(TEXT("Actual GameMode/session/ship/Director integration with scripted input and arrival. No GI Init, "
                 "StartNewRun, disk save, physical navigation, rendering or natural-play acceptance."));
    return true;
}
#endif
