#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "Camera/CameraComponent.h"
#include "Components/SphereComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerInput.h"
#include "GameFramework/WorldSettings.h"
#include "InputKeyEventArgs.h"
#include "Physics/Experimental/PhysScene_Chaos.h"
#include "Slate/SceneViewport.h"
#include "Widgets/SViewport.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
/** Synthetic raw device events through the actual player controller, with an isolated physics world.
 * This validates the adapter chain; it is not evidence of physical keyboard/controller owner acceptance. */
struct FSSControllerFlightWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    ASSPlayerController *Controller = nullptr;
    ASSShip *Ship = nullptr;
    UGameViewportClient *ViewportClient = nullptr;
    TSharedPtr<SViewport> ViewportWidget;
    TSharedPtr<FSceneViewport> SceneViewport;
    static constexpr float StepSeconds = 1.f / 60.f;

    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated controller/physics world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // No GameInstance Init/InitializeStandalone and no disk-backed account/settings.
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = 0;
        Instance->Session.settings.cameraShake = false;
        Instance->Session.settings.toggleBoost = false;
        Instance->Session.settings.toggleBrake = false;
        Instance->Session.account.tutorialFlags = 255;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        GWorld = World;
        World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
        if (!Test.TestTrue(TEXT("Install actual mode required by the controller"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        auto *Content = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
        if (!Test.TestNotNull(TEXT("Resolve actual mode"), Mode) ||
            !Test.TestNotNull(TEXT("Load production flight tuning"), Content))
            return false;
        Mode->Tuning = DuplicateObject<USSPhase1Data>(Content, Mode);
        Mode->SetActorTickEnabled(false);
        Mode->Director->SetComponentTickEnabled(false);
        auto &Tuning = Instance->Session.tuning;
        Tuning.baseHull = Content->BaseHull;
        Tuning.baseShield = Content->BaseShield;
        Tuning.baseSpeed = Content->CruiseSpeed;
        Tuning.baseManeuver = Content->LateralSpeed;
        Tuning.baseResponse = Content->Response;
        Tuning.baseAcceleration = Content->Acceleration;
        Tuning.baseWeaponDamage = Content->BaseWeaponDamage;
        if (!Test.TestTrue(TEXT("Start an isolated in-memory run"), Instance->Session.StartRun("raw-input-fixture")))
            return false;
        World->InitializeActorsForPlay(FURL());
        // Start only the actors under test. Calling the production mode's BeginPlay would create
        // a hangar, possess a walker and run unrelated account/menu orchestration.
        World->SetBegunPlay(true);
        if (World->GetPhysicsScene())
            World->GetPhysicsScene()->OnWorldBeginPlay();
        Controller = World->SpawnActor<ASSPlayerController>();
        Ship = World->SpawnActor<ASSShip>(FVector(0, 0, 7000), FRotator::ZeroRotator);
        if (!Test.TestNotNull(TEXT("Spawn actual player controller"), Controller) ||
            !Test.TestNotNull(TEXT("Spawn actual flying ship"), Ship))
            return false;
        // SetPlayer is the engine entry point that creates PlayerInput and the input stack.
        // A bare SetAsLocalPlayerController leaves PlayerInput null and crashes Super::PlayerTick.
        auto *LocalPlayer = NewObject<ULocalPlayer>(GEngine, NAME_None, RF_Transient);
        Controller->SetPlayer(LocalPlayer);
        Controller->bEnableMouseOverEvents = false;
        Controller->bEnableTouchOverEvents = false;
        Controller->bForceFeedbackEnabled = false;
        Controller->SetDisableHaptics(true);
        World->AddController(Controller);
        Controller->Possess(Ship);
        Controller->SetActorTickEnabled(false);
        Ship->Tuning = DuplicateObject<USSPhase1Data>(Content, Ship);
        return Test.TestNotNull(TEXT("SetPlayer supplied a real PlayerInput"), Controller->PlayerInput.Get()) &&
               Test.TestTrue(TEXT("Actual ship began play, is possessed and moving"),
                             Ship->HasActorBegunPlay() && Controller->GetPawn() == Ship &&
                                 Ship->GetVelocity().Size() > 1000.f);
    }

    void Button(FKey Key, bool Pressed)
    {
        Controller->InputKey(
            FInputKeyEventArgs::CreateSimulated(Key, Pressed ? IE_Pressed : IE_Released, Pressed ? 1.f : 0.f));
    }

    void Axis(FKey Key, float Value)
    {
        auto Event = FInputKeyEventArgs::CreateSimulated(Key, IE_Axis, Value, 1);
        Event.DeltaTime = StepSeconds;
        Controller->InputKey(Event);
    }

    void Step()
    {
        ++GFrameCounter;
        // Super::PlayerTick processes PlayerInput first; the real adapter then polls it and
        // commands the ship. The normal world tick advances the actual movement/Chaos body.
        Controller->PlayerTick(StepSeconds);
        World->Tick(LEVELTICK_All, StepSeconds);
    }

    void Frames(int32 Count)
    {
        for (int32 Index = 0; Index < Count; ++Index)
            Step();
    }

    bool AttachInertViewport(FAutomationTestBase &Test)
    {
        // An unattached Slate viewport exercises ApplyInputMode's actual engine branch. No SWindow,
        // RHI frame, native focus operation or OS cursor event is created/applied by this fixture.
        ViewportClient = NewObject<UGameViewportClient>(GEngine, NAME_None, RF_Transient);
        ViewportClient->AddToRoot();
        auto &Context = *GEngine->GetWorldContextFromWorld(World);
        Context.GameViewport = ViewportClient;
        CastChecked<ULocalPlayer>(Controller->Player)->ViewportClient = ViewportClient;
        ViewportWidget = SNew(SViewport);
        SceneViewport = ViewportClient->CreateViewport(ViewportWidget);
        return Test.TestTrue(TEXT("Input mode resolves the isolated inert viewport widget"),
                             World->GetGameViewport() == ViewportClient &&
                                 ViewportClient->GetGameViewportWidget() == ViewportWidget);
    }

    ~FSSControllerFlightWorld()
    {
        if (World)
        {
            if (ViewportClient)
            {
                auto *Player = Cast<ULocalPlayer>(Controller->Player);
                Player->ViewportClient = nullptr;
                Player->GetSlateOperations() = FReply::Unhandled();
                SceneViewport.Reset();
                ViewportWidget.Reset();
                GEngine->GetWorldContextFromWorld(World)->GameViewport = nullptr;
                ViewportClient->RemoveFromRoot();
            }
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSControllerToFlight, "SpaceSurvival.Flight.ControllerToPhysics",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSControllerToFlight::RunTest(const FString &)
{
    for (bool Gamepad : {false, true})
    {
        FSSControllerFlightWorld F;
        if (!F.Initialize(*this))
            return false;
        const FString Device = Gamepad ? TEXT("Gamepad") : TEXT("Keyboard/mouse");
        F.Frames(30);
        const FRotator BeforeTurn = F.Ship->GetActorRotation();
        for (int32 Frame = 0; Frame < 60; ++Frame)
        {
            F.Axis(Gamepad ? EKeys::Gamepad_RightX : EKeys::MouseX, Gamepad ? .8f : 5.f);
            F.Axis(Gamepad ? EKeys::Gamepad_RightY : EKeys::MouseY, Gamepad ? .6f : 4.f);
            F.Step();
        }
        const FRotator Turn = (F.Ship->GetActorRotation() - BeforeTurn).GetNormalized();
        AddInfo(
            FString::Printf(TEXT("%s raw look produced yaw %.2f pitch %.2f degrees"), *Device, Turn.Yaw, Turn.Pitch));
        TestTrue(Device + TEXT(" raw look rotates the physical ship in both commanded directions"),
                 Turn.Yaw > 5.f && Turn.Pitch > 5.f);
        F.Axis(Gamepad ? EKeys::Gamepad_RightX : EKeys::MouseX, 0.f);
        F.Axis(Gamepad ? EKeys::Gamepad_RightY : EKeys::MouseY, 0.f);
        F.Frames(30);

        if (!Gamepad)
        {
            F.Button(EKeys::D, true);
            F.Button(EKeys::R, true);
        }
        for (int32 Frame = 0; Frame < 60; ++Frame)
        {
            if (Gamepad)
            {
                F.Axis(EKeys::Gamepad_LeftX, .8f);
                F.Axis(EKeys::Gamepad_LeftY, .8f);
            }
            F.Step();
        }
        const FVector StrafeVelocity = F.Ship->GetActorTransform().InverseTransformVectorNoScale(F.Ship->GetVelocity());
        TestTrue(Device + TEXT(" raw strafe changes actual lateral and vertical velocity"),
                 StrafeVelocity.Y > 50.f && StrafeVelocity.Z > 50.f);
        if (Gamepad)
        {
            F.Axis(EKeys::Gamepad_LeftX, 0.f);
            F.Axis(EKeys::Gamepad_LeftY, 0.f);
        }
        else
        {
            F.Button(EKeys::D, false);
            F.Button(EKeys::R, false);
        }
        F.Frames(90);
        const double Cruise = F.Ship->GetVelocity().Size();
        if (!Gamepad)
            F.Button(EKeys::LeftShift, true);
        for (int32 Frame = 0; Frame < 60; ++Frame)
        {
            if (Gamepad)
                F.Axis(EKeys::Gamepad_RightTriggerAxis, 1.f);
            F.Step();
        }
        TestTrue(Device + TEXT(" raw boost spends resource and accelerates the actual ship"),
                 F.Instance->Session.run.boosting && F.Instance->Session.run.boost < 95. &&
                     F.Ship->GetVelocity().Size() > Cruise + 100.);
        if (Gamepad)
            F.Axis(EKeys::Gamepad_RightTriggerAxis, 0.f);
        else
            F.Button(EKeys::LeftShift, false);
        F.Frames(120);
        const double BeforeBrake = F.Ship->GetVelocity().Size();
        if (!Gamepad)
            F.Button(EKeys::SpaceBar, true);
        for (int32 Frame = 0; Frame < 90; ++Frame)
        {
            if (Gamepad)
                F.Axis(EKeys::Gamepad_LeftTriggerAxis, 1.f);
            F.Step();
        }
        TestTrue(Device + TEXT(" raw brake heats the brake and slows the actual ship"),
                 F.Instance->Session.run.braking && F.Instance->Session.run.brakeHeat > 0. &&
                     F.Ship->GetVelocity().Size() < BeforeBrake * .8);
        if (Gamepad)
            F.Axis(EKeys::Gamepad_LeftTriggerAxis, 0.f);
        else
            F.Button(EKeys::SpaceBar, false);
        F.Frames(30);

        const FVector Eye = F.Ship->Camera->GetComponentLocation();
        const FVector Ray = (F.Ship->CrosshairWorldPoint() - Eye).GetSafeNormal();
        const float MuzzleAlong = FVector::DotProduct(F.Ship->MuzzleWorldPosition() - Eye, Ray);
        const FVector TargetPosition = Eye + Ray * (MuzzleAlong + 6000.f);
        auto *Target = F.World->SpawnActor<ASSWorldBody>(TargetPosition, FRotator::ZeroRotator);
        if (!TestNotNull(Device + TEXT(" creates a native target visibly under the reticle"), Target))
            return false;
        Target->Configure(ESSWorldKind::SmallAsteroid, 120.f, 0.f);
        F.Ship->Tuning->SoftAimDegrees = 0.f;
        F.Ship->SoftTarget = nullptr;
        F.Instance->Session.tuning.baseWeaponDamage = 30;
        F.Button(Gamepad ? EKeys::Gamepad_RightShoulder : EKeys::LeftMouseButton, true);
        F.Step();
        TestTrue(Device + TEXT(" raw fire trigger deals native damage and starts feedback"),
                 Target->IsActorBeingDestroyed() && F.Ship->IsFiring() && F.Mode->PlayerHitFlashSeconds > 0.f);
        F.Button(Gamepad ? EKeys::Gamepad_RightShoulder : EKeys::LeftMouseButton, false);
        TestFalse(TEXT("Fixture never entered production GameMode BeginPlay"), F.Mode->HasActorBegunPlay());
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSControllerAfterTakeoff, "SpaceSurvival.Flight.ControllerAfterTakeoff",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSControllerAfterTakeoff::RunTest(const FString &)
{
    for (bool Gamepad : {false, true})
    {
        FSSControllerFlightWorld F;
        if (!F.Initialize(*this))
            return false;
        const FString Device = Gamepad ? TEXT("Gamepad") : TEXT("Keyboard/mouse");
        F.Frames(30);
        const bool UsedPhysics = F.Ship->Collision->IsSimulatingPhysics();
        const FVector Pad = F.Ship->GetActorLocation();
        const FRotator Facing = F.Ship->GetActorRotation();
        F.Ship->SetDockingTarget(Pad, Facing);
        F.Ship->FinishDocking();
        auto *OtherPawn = F.World->SpawnActor<APawn>();
        if (!TestNotNull(TEXT("Create another pawn for the possession handoff"), OtherPawn))
            return false;
        F.Controller->Possess(OtherPawn);
        F.Step();
        TestFalse(Device + TEXT(" parked hull no longer integrates physics"), F.Ship->Collision->IsSimulatingPhysics());
        F.Controller->Possess(F.Ship);
        const FVector Hover = Pad + FVector(0, 0, 700.f);
        F.Ship->BeginTakeoff(Hover, Facing, 1.f);
        const double DodgeCooldownBeforeLift = F.Instance->Session.run.dodgeCooldown;
        F.Button(Gamepad ? EKeys::Gamepad_RightShoulder : EKeys::LeftMouseButton, true);
        F.Button(Gamepad ? EKeys::Gamepad_LeftShoulder : EKeys::Q, true);
        F.Frames(30);
        int32 ShotsDuringLift = 0;
        for (TActorIterator<ASSProjectile> It(F.World); It; ++It)
            if (!It->IsActorBeingDestroyed())
                ++ShotsDuringLift;
        TestTrue(Device + TEXT(" raw fire is rejected during the scripted lift"),
                 F.Ship->IsTakingOff() && !F.Ship->IsFiring() && ShotsDuringLift == 0);
        TestEqual(Device + TEXT(" raw dodge cannot consume cooldown during the scripted lift"),
                  F.Instance->Session.run.dodgeCooldown, DodgeCooldownBeforeLift);
        F.Button(Gamepad ? EKeys::Gamepad_RightShoulder : EKeys::LeftMouseButton, false);
        F.Button(Gamepad ? EKeys::Gamepad_LeftShoulder : EKeys::Q, false);
        F.Frames(31);
        TestTrue(Device + TEXT(" lift hands back the same possessed ship and restores its drive"),
                 !F.Ship->IsTakingOff() && F.Controller->GetPawn() == F.Ship &&
                     F.Ship->Collision->IsSimulatingPhysics() == UsedPhysics &&
                     F.Ship->Collision->GetCollisionEnabled() != ECollisionEnabled::NoCollision);

        const FRotator BeforeTurn = F.Ship->GetActorRotation();
        for (int32 Frame = 0; Frame < 60; ++Frame)
        {
            F.Axis(Gamepad ? EKeys::Gamepad_RightX : EKeys::MouseX, Gamepad ? .8f : 5.f);
            F.Axis(Gamepad ? EKeys::Gamepad_RightY : EKeys::MouseY, Gamepad ? .6f : 4.f);
            F.Step();
        }
        const FRotator Turn = (F.Ship->GetActorRotation() - BeforeTurn).GetNormalized();
        TestTrue(Device + TEXT(" raw look still rotates both axes after re-possession and lift"),
                 Turn.Yaw > 5.f && Turn.Pitch > 5.f);
        TestTrue(Device + TEXT(" restored drive moves the ship away from the lift endpoint"),
                 FVector::Dist(F.Ship->GetActorLocation(), Hover) > 100.f);
        TestFalse(TEXT("Re-possession fixture never entered production GameMode BeginPlay"),
                  F.Mode->HasActorBegunPlay());
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSControllerPitchParity, "SpaceSurvival.Flight.ControllerPitchParity",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSControllerPitchParity::RunTest(const FString &)
{
    for (bool Gamepad : {false, true})
        for (bool Inverted : {false, true})
        {
            FSSControllerFlightWorld F;
            if (!F.Initialize(*this))
                return false;
            F.Instance->Session.settings.invertPitch = Inverted;
            const FKey Axis = Gamepad ? EKeys::Gamepad_RightY : EKeys::MouseY;
            const float Value = Gamepad ? .6f : 4.f;
            const double Sign = Inverted ? -1. : 1.;
            const FString Case = FString::Printf(TEXT("%s / %s"), Gamepad ? TEXT("stick up") : TEXT("mouse up"),
                                                 Inverted ? TEXT("inverted") : TEXT("standard"));
            if (Gamepad)
            {
                F.Axis(Axis, .08f);
                F.Step();
                TestEqual(TEXT("Configured right-stick deadzone removes small resting drift before polling"),
                          F.Controller->GetInputAnalogKeyState(Axis), 0.f);
            }
            // SceneViewport::OnMouseMove subtracts screen CursorDelta.Y, so physical mouse-up
            // already arrives as positive MouseY. Positive stick Y has the same up convention.
            const float BeforeFlight = F.Ship->GetActorRotation().Pitch;
            for (int32 Frame = 0; Frame < 30; ++Frame)
            {
                F.Axis(Axis, Value);
                F.Step();
            }
            const double FlightPitch = FMath::FindDeltaAngleDegrees(BeforeFlight, F.Ship->GetActorRotation().Pitch);
            TestTrue(Case + TEXT(" pitches the actual flight body in the requested direction"),
                     FlightPitch * Sign > 3.);
            F.Axis(Axis, 0.f);
            F.Ship->BeginMooring();
            F.Ship->SetActorTickEnabled(false);
            auto *Walker = F.World->SpawnActor<ASSWalker>(FVector(10000, 0, 7000), FRotator::ZeroRotator);
            if (!TestNotNull(TEXT("Create actual station walking pawn"), Walker))
                return false;
            F.Controller->Possess(Walker);
            F.Controller->SetControlRotation(FRotator::ZeroRotator);
            for (int32 Frame = 0; Frame < 30; ++Frame)
            {
                F.Axis(Axis, Value);
                F.Step();
            }
            const double WalkPitch = FRotator::NormalizeAxis(F.Controller->GetControlRotation().Pitch);
            TestTrue(Case + TEXT(" points the station view in the same requested direction"), WalkPitch * Sign > 3.);
        }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSLiveRewardInput, "SpaceSurvival.Flight.LiveRewardInput",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSLiveRewardInput::RunTest(const FString &)
{
    FSSControllerFlightWorld F;
    if (!F.Initialize(*this) || !F.AttachInertViewport(*this))
        return false;
    for (bool Gamepad : {false, true})
    {
        F.Mode->NotifyEventCompleted(false);
        F.Mode->OpenPanel(ESSPanel::Reward);
        TestFalse(TEXT("Live flight reward hides the pointer to retain mouse steering"),
                  F.Controller->bShowMouseCursor);
        TestTrue(TEXT("Actual engine input mode requests permanent capture for live flight rewards"),
                 F.ViewportClient->GetMouseCaptureMode() == EMouseCaptureMode::CapturePermanently);
        TestFalse(TEXT("Reward selection keeps the world live"), F.World->IsPaused());
        TestTrue(TEXT("Captured reward explains the keyboard and controller selection controls"),
                 F.Mode->PanelDetail.Contains(TEXT("Up/Down or D-pad")) &&
                     F.Mode->PanelDetail.Contains(TEXT("Enter/A")));
        const SS::Utility BeforeUtility = F.Instance->Session.run.utility;
        const int32 Choice = Gamepad ? 0 : 1;
        // A previously rendered cursor rectangle can still resolve to a valid action index.
        // Exercise that exact pointer action route, independently of an OS cursor or HUD renderer.
        F.Mode->ActivateEntry(Choice, true);
        TestTrue(TEXT("Hidden captured pointer cannot accept a stale reward row"),
                 F.Mode->Panel == ESSPanel::Reward && F.Instance->Session.run.pendingReward &&
                     F.Instance->Session.run.utility == BeforeUtility);
        F.Button(EKeys::LeftMouseButton, true);
        F.Step();
        F.Button(EKeys::LeftMouseButton, false);
        F.Step();
        TestTrue(TEXT("Hidden reward mouse clicks neither choose nor fire"),
                 F.Mode->Panel == ESSPanel::Reward && F.Instance->Session.run.pendingReward && !F.Ship->IsFiring());
        const float BeforeYaw = F.Ship->GetActorRotation().Yaw;
        for (int32 Frame = 0; Frame < 30; ++Frame)
        {
            F.Axis(Gamepad ? EKeys::Gamepad_RightX : EKeys::MouseX, Gamepad ? .7f : 4.f);
            F.Step();
        }
        TestTrue(TEXT("Controller routing continues to steer while reward navigation is open"),
                 FMath::FindDeltaAngleDegrees(BeforeYaw, F.Ship->GetActorRotation().Yaw) > 3.f);
        F.Axis(Gamepad ? EKeys::Gamepad_RightX : EKeys::MouseX, 0.f);
        const FKey DownKey = Gamepad ? EKeys::Gamepad_DPad_Down : EKeys::Down;
        F.Button(DownKey, true);
        F.Step();
        F.Button(DownKey, false);
        F.Step();
        TestEqual(TEXT("Arrow/D-pad navigation still chooses the next live reward row"), F.Mode->SelectedEntry, 1);
        if (Choice == 0)
        {
            F.Button(EKeys::Gamepad_DPad_Up, true);
            F.Step();
            F.Button(EKeys::Gamepad_DPad_Up, false);
            F.Step();
        }
        const FKey Confirm = Gamepad ? EKeys::Gamepad_FaceButton_Bottom : EKeys::Enter;
        F.Button(Confirm, true);
        F.Step();
        F.Button(Confirm, false);
        F.Step();
        TestTrue(TEXT("Enter/A accepts one reward and returns to flight without firing"),
                 F.Mode->Panel == ESSPanel::None && !F.Instance->Session.run.pendingReward &&
                     F.Instance->Session.run.utility != BeforeUtility && !F.Ship->IsFiring());
        TestTrue(TEXT("Closing reward retains the flight capture mode"),
                 !F.Controller->bShowMouseCursor &&
                     F.ViewportClient->GetMouseCaptureMode() == EMouseCaptureMode::CapturePermanently);
    }
    F.Ship->BeginMooring();
    F.Mode->OpenPanel(ESSPanel::Depot);
    TestTrue(TEXT("Moored depot retains its visible cursor and pointer capture policy"),
             F.Controller->bShowMouseCursor &&
                 F.ViewportClient->GetMouseCaptureMode() == EMouseCaptureMode::CaptureDuringMouseDown);
    F.Mode->ClosePanel();
    F.Mode->OpenPanel(ESSPanel::Main);
    TestTrue(TEXT("Ordinary menus retain cursor UI mode"),
             F.Controller->bShowMouseCursor &&
                 F.ViewportClient->GetMouseCaptureMode() == EMouseCaptureMode::CaptureDuringMouseDown);
    F.Mode->ClosePanel();
    // Mode/cursor policy and synthetic routing are covered; no native window, real pointer focus,
    // capture acquisition or physical-device acceptance is claimed by this inert viewport fixture.
    return true;
}
#endif
