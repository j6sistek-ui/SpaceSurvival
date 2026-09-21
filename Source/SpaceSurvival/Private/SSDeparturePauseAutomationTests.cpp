#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSShipVisualRig.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "Physics/Experimental/PhysScene_Chaos.h"
#include "UObject/UnrealType.h"
#include "UObject/GarbageCollection.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSDeparturePauseWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    ASSShip *Ship = nullptr;
    ULocalPlayer *LocalPlayer = nullptr;

    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated departure pause world"), World))
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
        if (!Test.TestTrue(TEXT("Install production menu and departure mode"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        auto *Content = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
        if (!Test.TestNotNull(TEXT("Resolve mode"), Mode) || !Test.TestNotNull(TEXT("Resolve actual tuning"), Content))
            return false;
        Mode->Tuning = DuplicateObject<USSPhase1Data>(Content, Mode);
        Mode->SetActorTickEnabled(false);
        Mode->Director->SetComponentTickEnabled(false);
        if (!Test.TestTrue(TEXT("Create in-memory station run"), Instance->Session.StartRun("departure-pause-fixture")))
            return false;
        Instance->Session.run.phase = SS::Phase::Station;
        Instance->Session.run.wave = Instance->Session.run.wavesCompleted = 5;
        Instance->Session.run.phaseSeconds = Instance->Session.run.phaseDuration = 0;
        World->InitializeActorsForPlay(FURL());
        // Do not run production BeginPlay/account initialization; exercise the actual departure
        // transaction and pause APIs with only the actors required by that handoff.
        World->SetBegunPlay(true);
        if (World->GetPhysicsScene())
            World->GetPhysicsScene()->OnWorldBeginPlay();
        auto *Controller = World->SpawnActor<APlayerController>();
        auto *Hub = World->SpawnActor<ASSStation>(FVector(0, 0, 7000), FRotator::ZeroRotator);
        if (!Test.TestNotNull(TEXT("Create departure controller"), Controller) ||
            !Test.TestNotNull(TEXT("Create station anchor"), Hub))
            return false;
        LocalPlayer = NewObject<ULocalPlayer>(GEngine, NAME_None, RF_Transient);
        Instance->AddLocalPlayer(LocalPlayer, FPlatformUserId::CreateFromInternalId(0));
        Controller->SetPlayer(LocalPlayer);
        // GameplayStatics routes pause through the game instance's local-player registry, not the
        // world's controller list. A bare SetPlayer fixture never reaches the real SetPause call.
        if (!Test.TestTrue(TEXT("Pause resolves the registered local departure controller"),
                           Instance->GetFirstLocalPlayerController() == Controller) ||
            !Test.TestNotNull(TEXT("The engine has a player state that can own pause"), Controller->PlayerState.Get()))
            return false;
        Controller->SetActorTickEnabled(false);
        World->AddController(Controller);
        Ship = World->SpawnActor<ASSShip>(Hub->PadDockPosition(), Hub->PadDockRotation());
        if (!Test.TestNotNull(TEXT("Create actual parked ship"), Ship))
            return false;
        Ship->SetDockingTarget(Hub->PadDockPosition(), Hub->PadDockRotation());
        Ship->FinishDocking();
        auto *HubProperty = FindFProperty<FObjectPropertyBase>(ASSGameMode::StaticClass(), TEXT("Hub"));
        auto *ShipProperty = FindFProperty<FObjectPropertyBase>(ASSGameMode::StaticClass(), TEXT("Ship"));
        if (!Test.TestNotNull(TEXT("Resolve native hub ownership"), HubProperty) ||
            !Test.TestNotNull(TEXT("Resolve native ship ownership"), ShipProperty))
            return false;
        HubProperty->SetObjectPropertyValue_InContainer(Mode, Hub);
        ShipProperty->SetObjectPropertyValue_InContainer(Mode, Ship);
        Mode->LaunchFromHub();
        return Test.TestTrue(TEXT("Real departure keeps Station phase and the same pawn during lift"),
                             Mode->IsDepartingStation() && Ship->IsTakingOff() && Controller->GetPawn() == Ship &&
                                 Instance->Session.run.phase == SS::Phase::Station);
    }

    void Frames(int32 Count)
    {
        for (int32 Index = 0; Index < Count; ++Index)
        {
            ++GFrameCounter;
            World->Tick(LEVELTICK_All, 1.f / 60.f);
        }
    }

    bool Shutdown()
    {
        bool PlayersReleased = true;
        if (World)
        {
            if (Mode)
                Mode->ClosePanel();
            // AddLocalPlayer initializes local-player subsystems. Release them while their owner,
            // controller and world are alive; waiting for the UObject destructor is too late in GC.
            if (Instance && LocalPlayer)
            {
                Instance->RemoveLocalPlayer(LocalPlayer);
                PlayersReleased = Instance->GetNumLocalPlayers() == 0;
                LocalPlayer = nullptr;
            }
            World->EndPlay(EEndPlayReason::Quit);
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
            GWorld = PreviousWorld;
            World = nullptr;
            Mode = nullptr;
            Ship = nullptr;
        }
        if (Instance)
        {
            Instance->RemoveFromRoot();
            Instance = nullptr;
        }
        return PlayersReleased;
    }

    ~FSSDeparturePauseWorld()
    {
        Shutdown();
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSStationDeparturePause, "SpaceSurvival.Flight.StationDeparturePause",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSStationDeparturePause::RunTest(const FString &)
{
    FSSDeparturePauseWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    Fixture.Frames(15);
    const FVector DuringLift = Fixture.Ship->GetActorLocation();
    const auto *Rig = Fixture.Ship->GetVisualRig();
    const auto *Hull = Rig ? Rig->GetHull() : nullptr;
    UAnimSingleNodeInstance *Animation = Hull ? Hull->GetSingleNodeInstance() : nullptr;
    if (!TestNotNull(TEXT("Actual Phoenix animation is available during lift"), Animation))
        return false;
    const float LiftAnimationTime = Animation->GetCurrentTime();
    Fixture.Mode->OpenPanel(ESSPanel::Main);
    TestTrue(TEXT("Main menu pauses a lift while domain phase is Station"), Fixture.World->IsPaused());
    Fixture.Frames(60);
    TestTrue(TEXT("Paused lift does not advance actor position or finish taking off"),
             Fixture.Ship->GetActorLocation().Equals(DuringLift, .01) && Fixture.Ship->IsTakingOff());
    TestEqual(TEXT("Paused lift also holds its visible authored animation"), Animation->GetCurrentTime(),
              LiftAnimationTime);
    Fixture.Mode->ClosePanel();
    TestFalse(TEXT("Closing menu releases the engine pause"), Fixture.World->IsPaused());
    TestFalse(TEXT("Closing menu clears menu ownership"), Fixture.Mode->IsMenuOpen());
    Fixture.Frames(30);
    TestTrue(TEXT("The same lift resumes after closing its menu"),
             FVector::Dist(Fixture.Ship->GetActorLocation(), DuringLift) > 25.f && Fixture.Ship->IsTakingOff());
    Fixture.Frames(145);
    TestFalse(TEXT("Three seconds of unpaused simulation completes the lift"), Fixture.Ship->IsTakingOff());
    Fixture.Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 1.f, false, false);
    Fixture.Frames(60);
    TestTrue(TEXT("Physical flight is moving within the station departure zone"),
             Fixture.Ship->GetVelocity().Size() > 100.f && Fixture.Mode->IsInStationZone() &&
                 Fixture.Instance->Session.run.phase == SS::Phase::Station);
    const FTransform DuringFlight = Fixture.Ship->GetActorTransform();
    Fixture.Mode->OpenPanel(ESSPanel::Settings);
    TestTrue(TEXT("Settings pauses physical departure flight while domain phase remains Station"),
             Fixture.World->IsPaused());
    Fixture.Frames(60);
    TestTrue(TEXT("Paused departure cannot coast out of control behind a menu"),
             Fixture.Ship->GetActorTransform().Equals(DuringFlight, .01));
    Fixture.Mode->ClosePanel();
    TestFalse(TEXT("Closing settings restores simulation"), Fixture.World->IsPaused());
    Fixture.Frames(30);
    TestTrue(TEXT("Departure flight resumes on the same pawn after settings"),
             FVector::Dist(Fixture.Ship->GetActorLocation(), DuringFlight.GetLocation()) > 25.f &&
                 Fixture.Mode->GetPlayerShip() == Fixture.Ship);
    const TWeakObjectPtr<ULocalPlayer> RegisteredPlayer(Fixture.LocalPlayer);
    TestTrue(TEXT("Fixture removes its initialized local player before destroying the world"), Fixture.Shutdown());
    // The failure previously surfaced during a later gallery test's collection. Exercise that
    // boundary here so a passing pause test cannot leave a deferred subsystem-destruction crash.
    CollectGarbage(RF_NoFlags, true);
    TestFalse(TEXT("Registered pause player is released cleanly through garbage collection"),
              RegisteredPlayer.IsValid());
    return true;
}
#endif
