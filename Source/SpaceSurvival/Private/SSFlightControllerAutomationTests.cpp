#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSHUD.h"
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
#include "GameFramework/SpringArmComponent.h"
#include "GyroManagerComp.h"
#include "GameFramework/WorldSettings.h"
#include "InputKeyEventArgs.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformFileManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Guid.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
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
        Tuning.baseSpeed = Content->FlightCruiseSpeed();
        Tuning.baseManeuver = Content->LateralSpeed;
        Tuning.baseResponse = Content->Response;
        Tuning.baseAcceleration = Content->FlightAcceleration();
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
        Controller->ClientSetHUD(ASSHUD::StaticClass());
        Controller->SetActorTickEnabled(false);
        Ship->Tuning = DuplicateObject<USSPhase1Data>(Content, Ship);
        return Test.TestNotNull(TEXT("SetPlayer supplied a real PlayerInput"), Controller->PlayerInput.Get()) &&
               Test.TestNotNull(TEXT("Controller owns the real Canvas focus handler"), Controller->GetHUD()) &&
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
            F.Axis(Gamepad ? EKeys::Gamepad_LeftX : EKeys::MouseX, Gamepad ? 0.f : 5.f);
            F.Axis(Gamepad ? EKeys::Gamepad_LeftY : EKeys::MouseY, Gamepad ? .6f : 4.f);
            F.Step();
        }
        const FRotator Turn = (F.Ship->GetActorRotation() - BeforeTurn).GetNormalized();
        AddInfo(
            FString::Printf(TEXT("%s raw look produced yaw %.2f pitch %.2f degrees"), *Device, Turn.Yaw, Turn.Pitch));
        TestTrue(Device + TEXT(" raw steering rotates the physical ship on the assigned axes"),
                 (Gamepad ? FMath::Abs(Turn.Yaw) < 1.f : Turn.Yaw > 5.f) && Turn.Pitch > 5.f);
        F.Axis(Gamepad ? EKeys::Gamepad_LeftX : EKeys::MouseX, 0.f);
        F.Axis(Gamepad ? EKeys::Gamepad_LeftY : EKeys::MouseY, 0.f);
        F.Frames(30);

        F.Ship->Collision->SetPhysicsLinearVelocity(FVector::ZeroVector);
        const FVector BeforeStrafeVelocity = F.Ship->GetVelocity();
        const FVector BeforeStrafeUp = F.Ship->GetActorUpVector();
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
                F.Axis(EKeys::Gamepad_RightY, 0.f);
            }
            F.Step();
        }
        const FVector StrafeVelocity = F.Ship->GetActorTransform().InverseTransformVectorNoScale(F.Ship->GetVelocity());
        AddInfo(FString::Printf(TEXT("STRAFE %s local=%s deltaUp=%.3f"), *Device, *StrafeVelocity.ToString(),
                                FVector::DotProduct(F.Ship->GetVelocity() - BeforeStrafeVelocity, BeforeStrafeUp)));
        TestTrue(Device + TEXT(" controller steering adds no lateral thrust; keyboard retains maneuvering thrusters"),
                 Gamepad ? StrafeVelocity.Size() < 1.f : (StrafeVelocity.Y > 50.f && StrafeVelocity.Z > 50.f));
        if (Gamepad)
        {
            F.Axis(EKeys::Gamepad_LeftX, 0.f);
            F.Axis(EKeys::Gamepad_RightY, 0.f);
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
                F.Button(EKeys::Gamepad_FaceButton_Right, true);
            F.Step();
        }
        TestTrue(Device + TEXT(" raw boost spends resource and accelerates the actual ship"),
                 F.Instance->Session.run.boosting && F.Instance->Session.run.boost < 95. &&
                     F.Ship->GetVelocity().Size() > Cruise + 100.);
        if (Gamepad)
            F.Button(EKeys::Gamepad_FaceButton_Right, false);
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
        F.Button(Gamepad ? EKeys::Gamepad_FaceButton_Bottom : EKeys::LeftMouseButton, true);
        F.Step();
        TestTrue(Device + TEXT(" raw fire trigger deals native damage and starts feedback"),
                 Target->IsActorBeingDestroyed() && F.Ship->IsFiring() && F.Mode->PlayerHitFlashSeconds > 0.f);
        F.Button(Gamepad ? EKeys::Gamepad_FaceButton_Bottom : EKeys::LeftMouseButton, false);
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
        auto *OtherPawn = F.World->SpawnActor<ASSWalker>();
        if (!TestNotNull(TEXT("Create the actual walker for the possession handoff"), OtherPawn))
            return false;
        F.Controller->Possess(OtherPawn);
        F.Step();
        TestFalse(Device + TEXT(" parked hull no longer integrates physics"), F.Ship->Collision->IsSimulatingPhysics());
        if (Gamepad)
        {
            F.Button(EKeys::Gamepad_FaceButton_Bottom, true);
            F.Step(); // The actual walking adapter receives A before possession changes.
        }
        F.Controller->Possess(F.Ship);
        OtherPawn->Destroy(); // Match departure: the old weak pawn is invalid before the next controller tick.
        const FVector Hover = Pad + FVector(0, 0, 700.f);
        F.Ship->BeginTakeoff(Hover, Facing, 1.f);
        const double DodgeCooldownBeforeLift = F.Instance->Session.run.dodgeCooldown;
        if (!Gamepad)
            F.Button(EKeys::LeftMouseButton, true);
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
        if (!Gamepad)
            F.Button(EKeys::LeftMouseButton, false);
        F.Button(Gamepad ? EKeys::Gamepad_LeftShoulder : EKeys::Q, false);
        F.Frames(31);
        TestTrue(Device + TEXT(" lift hands back the same possessed ship and restores its drive"),
                 !F.Ship->IsTakingOff() && F.Controller->GetPawn() == F.Ship &&
                     F.Ship->Collision->IsSimulatingPhysics() == UsedPhysics &&
                     F.Ship->Collision->GetCollisionEnabled() != ECollisionEnabled::NoCollision);
        if (Gamepad)
        {
            TestFalse(TEXT("A held from walking cannot become fire after the lift finishes"), F.Ship->IsFiring());
            F.Button(EKeys::Gamepad_FaceButton_Bottom, false);
            F.Step();
            TestFalse(TEXT("Releasing the walking A press does not fire"), F.Ship->IsFiring());
            F.Button(EKeys::Gamepad_FaceButton_Bottom, true);
            F.Step();
            TestTrue(TEXT("A fresh A press after release fires the actual ship weapon"), F.Ship->IsFiring());
            F.Button(EKeys::Gamepad_FaceButton_Bottom, false);
            F.Step();
        }

        const FRotator BeforeTurn = F.Ship->GetActorRotation();
        // Takeoff leaves the engine off. The pilot must explicitly request ordinary power.
        if (!Gamepad)
            F.Button(EKeys::W, true);
        for (int32 Frame = 0; Frame < 60; ++Frame)
        {
            if (Gamepad)
                F.Axis(EKeys::Gamepad_RightTriggerAxis, 1.f);
            F.Axis(Gamepad ? EKeys::Gamepad_LeftX : EKeys::MouseX, Gamepad ? 0.f : 5.f);
            F.Axis(Gamepad ? EKeys::Gamepad_LeftY : EKeys::MouseY, Gamepad ? .6f : 4.f);
            F.Step();
        }
        if (!Gamepad)
            F.Button(EKeys::W, false);
        else
            F.Axis(EKeys::Gamepad_RightTriggerAxis, 0.f);
        const FRotator Turn = (F.Ship->GetActorRotation() - BeforeTurn).GetNormalized();
        TestTrue(Device + TEXT(" assigned steering still responds after re-possession and lift"),
                 (Gamepad ? FMath::Abs(Turn.Yaw) < 1.f : Turn.Yaw > 5.f) && Turn.Pitch > 5.f);
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
            FKey Axis = Gamepad ? EKeys::Gamepad_LeftY : EKeys::MouseY;
            const float Value = Gamepad ? .6f : 4.f;
            const double Sign = Inverted ? -1. : 1.;
            const FString Case = FString::Printf(TEXT("%s / %s"), Gamepad ? TEXT("stick up") : TEXT("mouse up"),
                                                 Inverted ? TEXT("inverted") : TEXT("standard"));
            if (Gamepad)
            {
                F.Axis(Axis, .08f);
                F.Step();
                TestEqual(TEXT("Configured steering-stick deadzone removes small resting drift before polling"),
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
            Axis = Gamepad ? EKeys::Gamepad_RightY : EKeys::MouseY;
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
        TestTrue(TEXT("Canvas input keeps permanent capture and the initial mouse event for live offers"),
                 F.ViewportClient->GetMouseCaptureMode() ==
                     EMouseCaptureMode::CapturePermanently_IncludingInitialMouseDown);
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
        const float BeforePitch = F.Ship->GetActorRotation().Pitch;
        const int32 BeforeSteeringChoice = F.Mode->SelectedEntry;
        for (int32 Frame = 0; Frame < 30; ++Frame)
        {
            F.Axis(Gamepad ? EKeys::Gamepad_LeftY : EKeys::MouseY, Gamepad ? .7f : 4.f);
            F.Step();
        }
        TestTrue(TEXT("Controller routing continues to steer while reward navigation is open"),
                 FMath::FindDeltaAngleDegrees(BeforePitch, F.Ship->GetActorRotation().Pitch) > 3.f);
        TestEqual(TEXT("Flight steering cannot also navigate a live reward"), F.Mode->SelectedEntry,
                  BeforeSteeringChoice);
        if (Gamepad)
        {
            for (int32 Frame = 0; Frame < 30; ++Frame)
            {
                F.Axis(EKeys::Gamepad_LeftY, -.7f);
                F.Step();
            }
            TestEqual(TEXT("Pitching down cannot silently change the chosen live reward"), F.Mode->SelectedEntry,
                      BeforeSteeringChoice);
        }
        F.Axis(Gamepad ? EKeys::Gamepad_LeftY : EKeys::MouseY, 0.f);
        const FKey DownKey = Gamepad ? EKeys::Gamepad_DPad_Down : EKeys::Down;
        F.Button(DownKey, true);
        F.Step();
        F.Button(DownKey, false);
        F.Step();
        TestTrue(TEXT("Arrow/D-pad selects Cooling initially, then skips the already-fitted Cooling to Back"),
                 F.Mode->Entries.IsValidIndex(F.Mode->SelectedEntry) &&
                     F.Mode->Entries[F.Mode->SelectedEntry].Action == (Gamepad ? 0 : 47));
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
        F.Frames(15);
        TestFalse(TEXT("Held menu confirm cannot leak into weapon fire"), F.Ship->IsFiring());
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
    TestTrue(TEXT("Moored depot retains its visible cursor and the first Canvas click"),
             F.Controller->bShowMouseCursor && F.ViewportClient->GetMouseCaptureMode() ==
                                                   EMouseCaptureMode::CapturePermanently_IncludingInitialMouseDown);
    F.Mode->ClosePanel();
    F.Mode->OpenPanel(ESSPanel::Main);
    TestTrue(TEXT("Ordinary Canvas menus retain their visible cursor and the first click"),
             F.Controller->bShowMouseCursor && F.ViewportClient->GetMouseCaptureMode() ==
                                                   EMouseCaptureMode::CapturePermanently_IncludingInitialMouseDown);
    F.Mode->ClosePanel();
    // Mode/cursor policy and synthetic routing are covered; no native window, real pointer focus,
    // capture acquisition or physical-device acceptance is claimed by this inert viewport fixture.
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSAnalogThrottleAndCoast, "SpaceSurvival.Flight.AnalogThrottleAndCoast",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSAnalogThrottleAndCoast::RunTest(const FString &)
{
    FSSControllerFlightWorld F;
    if (!F.Initialize(*this))
        return false;
    F.Ship->Collision->SetPhysicsLinearVelocity(FVector::ZeroVector);
    F.Axis(EKeys::Gamepad_RightTriggerAxis, 0.f);
    F.Frames(30);
    TestTrue(TEXT("Released throttle does not start the engine or force a speed floor"),
             F.Ship->GetVelocity().Size() < 1.f && F.Ship->GetThrottle() == 0.f);
    F.Button(EKeys::W, true);
    F.Frames(120);
    F.Button(EKeys::W, false);
    F.Step();
    TestTrue(TEXT("W establishes persistent full keyboard throttle before switching to RT"),
             F.Ship->GetThrottle() > .99f);
    for (int32 Frame = 0; Frame < 90; ++Frame)
    {
        F.Axis(EKeys::Gamepad_RightTriggerAxis, .5f);
        F.Step();
    }
    const float HalfSpeed = F.Ship->GetVelocity().Size();
    TestTrue(TEXT("Half trigger provides ordinary thrust without consuming boost"),
             FMath::IsNearlyEqual(F.Ship->GetThrottle(), .5f, .01f) && HalfSpeed > 300.f &&
                 !F.Instance->Session.run.boosting && F.Instance->Session.run.boost >= 99.9);
    for (int32 Frame = 0; Frame < 90; ++Frame)
    {
        F.Axis(EKeys::Gamepad_RightTriggerAxis, 1.f);
        F.Step();
    }
    TestTrue(TEXT("Full normal trigger is faster than half power without boosting"),
             F.Ship->GetVelocity().Size() > HalfSpeed * 1.3f && !F.Instance->Session.run.boosting);
    TestTrue(TEXT("Normal full throttle reaches the approved 60 m/s baseline"),
             F.Ship->GetVelocity().Size() > 5500.f && F.Ship->GetVelocity().Size() <= 6100.f);
    const FVector Momentum = F.Ship->GetVelocity();
    F.Axis(EKeys::Gamepad_RightTriggerAxis, 0.f);
    for (int32 Frame = 0; Frame < 45; ++Frame)
    {
        F.Axis(EKeys::Gamepad_LeftY, .4f);
        F.Step();
    }
    TestTrue(TEXT("Engine-off turning retains world-space momentum"),
             FVector::Distance(F.Ship->GetVelocity(), Momentum) < 5.f &&
                 FMath::Abs(F.Ship->GetActorRotation().Pitch) > 1.f);
    F.Axis(EKeys::Gamepad_LeftY, 0.f);
    F.Axis(EKeys::MouseX, 5.f);
    F.Step();
    F.Button(EKeys::LeftControl, true);
    F.Step();
    F.Button(EKeys::LeftControl, false);
    F.Step();
    TestTrue(TEXT("Mouse and unrelated keyboard input cannot revive stale W throttle after RT release"),
             !F.Controller->bLastInputWasGamepad && F.Ship->GetThrottle() == 0.f &&
                 FVector::Distance(F.Ship->GetVelocity(), Momentum) < 5.f);
    float Power, Damage;
    bool Boosting, Braking;
    F.Ship->GetDrivePresentation(Power, Boosting, Braking, Damage);
    TestTrue(TEXT("Engine-off presentation has no drive power"), Power == 0.f && !Boosting);
    F.Button(EKeys::Gamepad_FaceButton_Right, true);
    F.Frames(30);
    TestTrue(TEXT("B independently engages boost"),
             F.Instance->Session.run.boosting && F.Instance->Session.run.boost < 99.f);
    F.Button(EKeys::Gamepad_FaceButton_Right, false);
    const double BeforeBrake = F.Ship->GetVelocity().Size();
    for (int32 Frame = 0; Frame < 60; ++Frame)
    {
        F.Axis(EKeys::Gamepad_LeftTriggerAxis, 1.f);
        F.Step();
    }
    TestTrue(TEXT("Left trigger reduces coasting speed"), F.Ship->GetVelocity().Size() < BeforeBrake * .65);
    F.Axis(EKeys::Gamepad_LeftTriggerAxis, 0.f);
    F.Button(EKeys::S, true);
    F.Step();
    F.Button(EKeys::S, false);
    F.Step();
    const float KeyboardPower = F.Ship->GetThrottle();
    TestTrue(TEXT("A fresh S command deliberately resumes the retained keyboard setting"),
             KeyboardPower > .9f && KeyboardPower < 1.f);
    F.Axis(EKeys::Gamepad_LeftY, .4f);
    F.Step();
    TestTrue(TEXT("Controller look changes HUD device without changing keyboard throttle ownership"),
             F.Controller->bLastInputWasGamepad && FMath::IsNearlyEqual(F.Ship->GetThrottle(), KeyboardPower));
    F.Axis(EKeys::Gamepad_LeftY, 0.f);
    F.Axis(EKeys::Gamepad_RightTriggerAxis, .35f);
    F.Step();
    TestTrue(TEXT("A fresh trigger press takes normal throttle ownership"),
             FMath::IsNearlyEqual(F.Ship->GetThrottle(), .35f, .01f));
    F.Button(EKeys::W, true);
    F.Step();
    F.Button(EKeys::W, false);
    F.Step();
    TestTrue(TEXT("Fresh W takes over from a held trigger without being overridden on the next frame"),
             F.Ship->GetThrottle() > .99f);
    for (float Trigger : {.354f, .358f})
    {
        F.Axis(EKeys::Gamepad_RightTriggerAxis, Trigger);
        F.Step();
    }
    TestTrue(TEXT("Sub-one-percent trigger noise cannot immediately override a keyboard command"),
             F.Ship->GetThrottle() > .99f);
    F.Axis(EKeys::Gamepad_RightTriggerAxis, .366f);
    F.Step();
    TestTrue(TEXT("A deliberate gradual trigger adjustment takes ownership once its total change is meaningful"),
             FMath::IsNearlyEqual(F.Ship->GetThrottle(), .366f, .01f));
    F.Axis(EKeys::Gamepad_RightTriggerAxis, 0.f);
    F.Step();
    TestTrue(TEXT("Actually lifting the held trigger takes ownership and cuts thrust again"),
             F.Ship->GetThrottle() == 0.f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSControllerTestingPreset, "SpaceSurvival.Flight.ControllerTestingPreset",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSControllerTestingPreset::RunTest(const FString &)
{
    FSSControllerFlightWorld F;
    if (!F.Initialize(*this))
        return false;
    F.Ship->Collision->SetPhysicsLinearVelocity(FVector::ZeroVector);
    F.Axis(EKeys::Gamepad_RightTriggerAxis, 0.f);
    F.Frames(30);
    const FQuat BodyBefore = F.Ship->GetActorQuat();
    const FVector CrosshairBefore = F.Ship->CrosshairWorldPoint();
    const FRotator ViewBefore = F.Ship->CameraBoom->GetRelativeRotation();
    for (int32 Frame = 0; Frame < 45; ++Frame)
    {
        F.Axis(EKeys::Gamepad_RightX, .8f);
        F.Axis(EKeys::Gamepad_RightY, .4f);
        F.Step();
    }
    const FRotator View = F.Ship->CameraBoom->GetRelativeRotation() - ViewBefore;
    TestTrue(TEXT("Right stick independently looks sideways and upward"), View.Yaw > 20.f && View.Pitch > 8.f);
    TestTrue(TEXT("Free-look cannot steer the ship or create strafe thrust"),
             BodyBefore.AngularDistance(F.Ship->GetActorQuat()) < .005f && F.Ship->GetVelocity().Size() < 1.f);
    TestTrue(TEXT("Free-look leaves the ship's weapon anchor in place"),
             FVector::Distance(CrosshairBefore, F.Ship->CrosshairWorldPoint()) < 1.f);
    F.Axis(EKeys::Gamepad_RightX, 0.f);
    F.Axis(EKeys::Gamepad_RightY, 0.f);
    F.Frames(90);
    TestTrue(TEXT("Releasing free-look gently restores the chase view"),
             FMath::Abs((F.Ship->CameraBoom->GetRelativeRotation() - ViewBefore).Yaw) < 2.f);
    const double YawStart = F.Ship->GetActorRotation().Yaw;
    for (int32 Frame = 0; Frame < 30; ++Frame)
    {
        F.Axis(EKeys::Gamepad_LeftX, 1.f);
        F.Step();
    }
    F.Axis(EKeys::Gamepad_LeftX, 0.f);
    const double YawTurn = FMath::FindDeltaAngleDegrees(YawStart, F.Ship->GetActorRotation().Yaw);
    AddInfo(FString::Printf(TEXT("ARCADE half-second nose yaw=%.2f"), YawTurn));
    TestTrue(TEXT("Left stick turns the actual nose promptly without sideways thrust"),
             YawTurn > 25. && F.Ship->GetVelocity().Size() < 1.f);
    F.Frames(30);
    const FVector DashStart = F.Ship->GetActorLocation();
    const FVector DashRight = F.Ship->GetActorRightVector();
    F.Button(EKeys::Gamepad_RightShoulder, true);
    F.Frames(4);
    F.Button(EKeys::Gamepad_RightShoulder, false);
    F.Frames(12);
    const double TapBank = F.Ship->GetActorRotation().Roll;
    const double DashTravel = FVector::DotProduct(F.Ship->GetActorLocation() - DashStart, DashRight);
    AddInfo(FString::Printf(TEXT("ARCADE tap bank=%.2f lateralTravel=%.2f"), TapBank, DashTravel));
    TestTrue(TEXT("Bumper tap quickly moves sideways and banks the actual hull"), TapBank > 10. && DashTravel > 300.);
    F.Frames(100);
    TestTrue(TEXT("A short evasive tap returns toward level"), FMath::Abs(F.Ship->GetActorRotation().Roll) < 3.);
    F.Ship->Collision->SetPhysicsLinearVelocity(FVector::ZeroVector);
    const double RightStart = F.Ship->GetActorRotation().Roll;
    F.Button(EKeys::Gamepad_RightShoulder, true);
    F.Frames(45);
    F.Button(EKeys::Gamepad_RightShoulder, false);
    const double RightRoll = FMath::FindDeltaAngleDegrees(RightStart, F.Ship->GetActorRotation().Roll);
    AddInfo(FString::Printf(TEXT("ARCADE held RB delta=%.2f"), RightRoll));
    TestTrue(TEXT("Holding RB transitions into fast arcade roll"), RightRoll > 70. && RightRoll < 180.);
    TestFalse(TEXT("RB is not weapon fire"), F.Ship->IsFiring());
    F.Frames(90);
    const double HeldRoll = F.Ship->GetActorRotation().Roll;
    TestTrue(TEXT("Released sustained roll retains the chosen attitude"), FMath::Abs(HeldRoll) > 70.);
    F.Button(EKeys::Gamepad_LeftShoulder, true);
    F.Frames(45);
    F.Button(EKeys::Gamepad_LeftShoulder, false);
    const double LeftRoll = FMath::FindDeltaAngleDegrees(HeldRoll, F.Ship->GetActorRotation().Roll);
    AddInfo(FString::Printf(TEXT("ARCADE held LB delta=%.2f"), LeftRoll));
    TestTrue(TEXT("Holding LB rolls the hull left at the same arcade rate"), LeftRoll < -70.);
    F.Frames(60);
    // All gamepad flight interaction moved to X; A is fire. A newly confirmed menu
    // press remains gated until release in LiveRewardInput; direct flight A must fire.
    F.Button(EKeys::Gamepad_FaceButton_Bottom, true);
    F.Step();
    TestTrue(TEXT("A fires the ship's weapon"), F.Ship->IsFiring());
    TestEqual(TEXT("A fire does not open a flight interaction panel"), F.Mode->Panel, ESSPanel::None);
    F.Button(EKeys::Gamepad_FaceButton_Bottom, false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSMenuBackBoostRelease, "SpaceSurvival.Flight.MenuBackBoostRelease",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSMenuBackBoostRelease::RunTest(const FString &)
{
    for (bool Toggle : {false, true})
        for (ESSPanel Panel : {ESSPanel::Main, ESSPanel::Reward})
        {
            FSSControllerFlightWorld F;
            if (!F.Initialize(*this) || !F.AttachInertViewport(*this))
                return false;
            F.Instance->Session.settings.toggleBoost = Toggle;
            F.Step();
            if (Panel == ESSPanel::Reward)
                F.Mode->NotifyEventCompleted(false);
            F.Mode->OpenPanel(Panel);
            const double BeforeBoost = F.Instance->Session.run.boost;
            F.Button(EKeys::Gamepad_FaceButton_Right, true);
            F.Step();
            TestFalse(TEXT("B closes the actual panel"), F.Mode->IsMenuOpen());
            // A physical button remains down across multiple frames after its pressed edge.
            // Do not synthesize a release immediately after Back, which would hide this defect.
            F.Frames(12);
            TestTrue(TEXT("The held menu Back press cannot boost or consume boost after closure"),
                     !F.Instance->Session.run.boosting && F.Instance->Session.run.boost >= BeforeBoost);
            F.Controller->UnPossess();
            F.Step();
            F.Controller->Possess(F.Ship);
            F.Frames(4);
            TestTrue(TEXT("Possession reset preserves suppression of the same consumed Back press"),
                     !F.Instance->Session.run.boosting && F.Instance->Session.run.boost >= BeforeBoost);
            F.Button(EKeys::Gamepad_FaceButton_Right, false);
            F.Step();
            F.Button(EKeys::Gamepad_FaceButton_Right, true);
            F.Frames(4);
            TestTrue(TEXT("Releasing then freshly pressing B engages the selected boost mode"),
                     F.Instance->Session.run.boosting && F.Instance->Session.run.boost < BeforeBoost);
            F.Button(EKeys::Gamepad_FaceButton_Right, false);
            F.Frames(4);
            TestEqual(TEXT("Hold mode releases and toggle mode stays active after the fresh press"),
                      F.Instance->Session.run.boosting, Toggle);
            if (Toggle)
            {
                F.Button(EKeys::Gamepad_FaceButton_Right, true);
                F.Step();
                TestFalse(TEXT("Another fresh B press switches toggle boost off"), F.Instance->Session.run.boosting);
                F.Button(EKeys::Gamepad_FaceButton_Right, false);
                F.Step();
            }
        }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSControllerMenuStick, "SpaceSurvival.UI.ControllerMenuStick",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSControllerMenuStick::RunTest(const FString &)
{
    FSSControllerFlightWorld F;
    if (!F.Initialize(*this) || !F.AttachInertViewport(*this))
        return false;
    for (ESSPanel Panel : {ESSPanel::Main, ESSPanel::Settings, ESSPanel::Wardrobe})
    {
        F.Mode->OpenPanel(Panel);
        F.Axis(EKeys::Gamepad_LeftY, 0.f);
        F.Step();
        TestTrue(TEXT("Canvas menu retains viewport input"), !F.ViewportClient->IgnoreInput());
        const int32 Initial = F.Mode->SelectedEntry;
        F.Axis(EKeys::Gamepad_LeftY, -.8f);
        F.Step();
        TestEqual(TEXT("Stick down selects the next row"), F.Mode->SelectedEntry, Initial + 1);
        for (int32 Frame = 0; Frame < 8; ++Frame)
        {
            F.Axis(EKeys::Gamepad_LeftY, -.8f);
            F.Step();
        }
        TestEqual(TEXT("Held stick does not race through rows immediately"), F.Mode->SelectedEntry, Initial + 1);
        for (int32 Frame = 0; Frame < 18; ++Frame)
        {
            F.Axis(EKeys::Gamepad_LeftY, -.8f);
            F.Step();
        }
        TestTrue(TEXT("Held stick repeats after the initial delay"), F.Mode->SelectedEntry > Initial + 1);
        const int32 Before = F.Mode->SelectedEntry;
        F.Axis(EKeys::Gamepad_LeftY, .8f);
        F.Step();
        TestEqual(TEXT("Reversing stick responds immediately"), F.Mode->SelectedEntry, Before - 1);
        F.Axis(EKeys::Gamepad_LeftY, .1f);
        F.Frames(30);
        TestEqual(TEXT("Neutral drift does not change focus"), F.Mode->SelectedEntry, Before - 1);
        F.Mode->ClosePanel();
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSRawMenuDirections, "SpaceSurvival.UI.RawMenuDirections",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSRawMenuDirections::RunTest(const FString &)
{
    FSSControllerFlightWorld F;
    if (!F.Initialize(*this) || !F.AttachInertViewport(*this))
        return false;
    const std::string SettingsBefore = SS::EncodeSettings(F.Instance->Session.settings);
    auto Tap = [&](FKey Key)
    {
        F.Button(Key, true);
        F.Step();
        F.Button(Key, false);
        F.Step();
    };
    F.Mode->OpenPanel(ESSPanel::Controls);
    Tap(EKeys::Gamepad_DPad_Up);
    TestEqual(TEXT("Raw D-pad up reaches the active Controls tab"), F.Mode->SelectedEntry, 3);
    F.Axis(EKeys::Gamepad_LeftX, -.8f);
    F.Axis(EKeys::Gamepad_LeftY, .6f);
    F.Step();
    TestEqual(TEXT("A diagonal stick takes only its dominant horizontal step"), F.Mode->SelectedEntry, 2);
    F.Axis(EKeys::Gamepad_LeftX, 0.f);
    F.Axis(EKeys::Gamepad_LeftY, 0.f);
    F.Step();
    Tap(EKeys::Gamepad_DPad_Right);
    TestEqual(TEXT("Raw D-pad right moves across tabs"), F.Mode->SelectedEntry, 3);
    Tap(EKeys::Gamepad_DPad_Left);
    TestEqual(TEXT("Raw D-pad left returns across tabs"), F.Mode->SelectedEntry, 2);
    F.Button(EKeys::Gamepad_FaceButton_Bottom, true);
    F.Step();
    F.Frames(8);
    TestTrue(TEXT("A opens Audio and its held press does not activate the new first setting"),
             F.Mode->Panel == ESSPanel::Audio && F.Mode->SelectedEntry == 4 &&
                 SS::EncodeSettings(F.Instance->Session.settings) == SettingsBefore);
    F.Button(EKeys::Gamepad_FaceButton_Bottom, false);
    F.Step();
    Tap(EKeys::Gamepad_DPad_Down);
    TestEqual(TEXT("Raw D-pad down enters the next actual setting row"), F.Mode->SelectedEntry, 5);
    Tap(EKeys::Gamepad_DPad_Up);
    TestEqual(TEXT("Raw D-pad up returns to the previous actual setting row"), F.Mode->SelectedEntry, 4);
    F.Button(EKeys::Gamepad_FaceButton_Right, true);
    F.Step();
    F.Frames(12);
    TestTrue(TEXT("B closes Audio while a held Back cannot become flight boost"),
             !F.Mode->IsMenuOpen() && !F.Instance->Session.run.boosting);
    F.Button(EKeys::Gamepad_FaceButton_Right, false);
    F.Step();
    F.Mode->OpenPanel(ESSPanel::Main);
    F.Button(EKeys::Gamepad_FaceButton_Bottom, true);
    F.Step();
    F.Frames(12);
    TestTrue(TEXT("A resumes the actual paused menu but cannot fire until released"),
             !F.Mode->IsMenuOpen() && !F.Ship->IsFiring());
    F.Button(EKeys::Gamepad_FaceButton_Bottom, false);
    F.Step();
    F.Button(EKeys::Gamepad_FaceButton_Bottom, true);
    F.Step();
    TestTrue(TEXT("A fresh post-release press fires normally"), F.Ship->IsFiring());
    F.Button(EKeys::Gamepad_FaceButton_Bottom, false);
    TestTrue(TEXT("Navigation and panel activation did not change or persist a setting"),
             SS::EncodeSettings(F.Instance->Session.settings) == SettingsBefore);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSIsolatedControllerSettings, "SpaceSurvival.UI.IsolatedControllerSettings",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSIsolatedControllerSettings::RunTest(const FString &)
{
    auto Normalize = [](FString Path)
    {
        Path = FPaths::ConvertRelativePathToFull(Path);
        FPaths::NormalizeDirectoryName(Path);
        FPaths::CollapseRelativeDirectories(Path);
        return Path;
    };
    FString UserArgument;
    const FString User = Normalize(FPaths::ProjectUserDir());
    const FString Root = FPaths::GetPath(User), Token = FPaths::GetCleanFilename(Root);
    const FString Parent = FPaths::GetPath(Root);
    FGuid Guid;
    if (!TestTrue(TEXT("Value-changing input requires explicit protected, unattended NullRHI opt-in"),
                  FParse::Param(FCommandLine::Get(), TEXT("SSMenuSettingsTest")) &&
                      FParse::Param(FCommandLine::Get(), TEXT("unattended")) &&
                      FParse::Param(FCommandLine::Get(), TEXT("NullRHI")) && FPaths::ShouldSaveToUserDir() &&
                      FParse::Value(FCommandLine::Get(), TEXT("UserDir="), UserArgument) &&
                      Normalize(UserArgument) == User && FPaths::GetCleanFilename(User) == TEXT("User") &&
                      FGuid::ParseExact(Token, EGuidFormats::Digits, Guid) &&
                      FPaths::GetCleanFilename(Parent) == TEXT("MenuSettings") &&
                      FPaths::GetCleanFilename(FPaths::GetPath(Parent)) == TEXT("Artifacts") &&
                      Normalize(FPaths::ProjectSavedDir()) == User / TEXT("Saved")))
        return false;
    auto &Files = FPlatformFileManager::Get().GetPlatformFile();
    for (FString Path = Normalize(FPaths::ProjectSavedDir()) / TEXT("SaveGames"); !Path.IsEmpty();)
    {
        if (!TestTrue(TEXT("Protected settings paths cannot redirect through a junction or symlink"),
                      Files.IsSymlink(*Path) == ESymlinkResult::NonSymlink))
            return false;
        const FString Next = FPaths::GetPath(Path);
        if (Next == Path)
            break;
        Path = Next;
    }
    TArray<FString> Existing;
    IFileManager::Get().FindFiles(Existing, *(FPaths::ProjectSavedDir() / TEXT("SaveGames/*")), true, false);
    if (!TestTrue(TEXT("Protected settings profile starts without any save slot"), Existing.IsEmpty()))
        return false;
    FSSControllerFlightWorld F;
    if (!F.Initialize(*this) || !F.AttachInertViewport(*this))
        return false;
    const std::string AccountBefore = SS::EncodeAccount(F.Instance->Session.account);
    auto Tap = [&](FKey Key)
    {
        F.Button(Key, true);
        F.Step();
        F.Button(Key, false);
        F.Step();
    };
    auto &Settings = F.Instance->Session.settings;
    Settings.masterVolume = .5;
    F.Mode->OpenPanel(ESSPanel::Audio);
    Tap(EKeys::Gamepad_DPad_Left);
    TestTrue(TEXT("Actual D-pad left decreases the selected volume"), FMath::IsNearlyEqual(Settings.masterVolume, .4));
    Tap(EKeys::Gamepad_DPad_Right);
    TestTrue(TEXT("Actual D-pad right increases the selected volume"), FMath::IsNearlyEqual(Settings.masterVolume, .5));
    Settings.masterVolume = 0.;
    Tap(EKeys::Gamepad_DPad_Left);
    TestEqual(TEXT("Left at minimum volume cannot wrap to maximum"), Settings.masterVolume, 0.);
    Settings.masterVolume = 1.;
    Tap(EKeys::Gamepad_DPad_Right);
    TestEqual(TEXT("Right at maximum volume cannot wrap to minimum"), Settings.masterVolume, 1.);
    TestEqual(TEXT("Repeated value rebuild retains the actual selected row"), F.Mode->SelectedEntry, 4);
    F.Mode->OpenPanel(ESSPanel::Graphics);
    Tap(EKeys::Gamepad_DPad_Down);
    Settings.frameLimit = 60;
    Tap(EKeys::Gamepad_DPad_Left);
    TestEqual(TEXT("Frame limit clamps at the lower end"), Settings.frameLimit, 60);
    Tap(EKeys::Gamepad_DPad_Right);
    TestEqual(TEXT("Right reaches the next supported frame limit"), Settings.frameLimit, 120);
    Tap(EKeys::Gamepad_DPad_Right);
    Tap(EKeys::Gamepad_DPad_Right);
    TestEqual(TEXT("Frame limit clamps at the upper end"), Settings.frameLimit, 144);
    F.Mode->OpenPanel(ESSPanel::Controls);
    Tap(EKeys::Gamepad_DPad_Down);
    Settings.controllerSensitivity = .3;
    Tap(EKeys::Gamepad_DPad_Left);
    TestTrue(TEXT("Sensitivity clamps at its minimum"), FMath::IsNearlyEqual(Settings.controllerSensitivity, .3));
    Tap(EKeys::Gamepad_DPad_Right);
    TestTrue(TEXT("Sensitivity increases through the actual input path"),
             FMath::IsNearlyEqual(Settings.controllerSensitivity, .5));
    Settings.controllerSensitivity = 2.9;
    Tap(EKeys::Gamepad_DPad_Right);
    TestTrue(TEXT("Sensitivity clamps at its maximum"), FMath::IsNearlyEqual(Settings.controllerSensitivity, 2.9));
    TestTrue(TEXT("Value adjustment never changes the account"),
             SS::EncodeAccount(F.Instance->Session.account) == AccountBefore);
    TestTrue(TEXT("Only the protected settings slot is written"),
             IFileManager::Get().FileExists(*(FPaths::ProjectSavedDir() / TEXT("SaveGames/SS_Settings_v1.sav"))) &&
                 !IFileManager::Get().FileExists(*(FPaths::ProjectSavedDir() / TEXT("SaveGames/SS_Account_v1.sav"))) &&
                 !IFileManager::Get().FileExists(*(FPaths::ProjectSavedDir() / TEXT("SaveGames/SS_Suspend_v1.sav"))));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSTitleMenuNavigation, "SpaceSurvival.UI.TitleMenuNavigation",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSTitleMenuNavigation::RunTest(const FString &)
{
    for (bool Gamepad : {false, true})
    {
        FSSControllerFlightWorld F;
        if (!F.Initialize(*this) || !F.AttachInertViewport(*this))
            return false;
        F.Instance->Session.run = {};
        F.Mode->Ship = F.Ship;
        F.Mode->OpenPanel(ESSPanel::Main);
        F.Step();
        const FString Device = Gamepad ? TEXT("D-pad/A") : TEXT("W/S/Enter");
        const int32 Actions[] = {2, 4, 5, 7};
        if (!TestEqual(Device + TEXT(" title exposes exactly four approved actions"), F.Mode->Entries.Num(), 4))
            return false;
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(Actions); ++Index)
            TestEqual(FString::Printf(TEXT("Title row %d retains its real action"), Index),
                      F.Mode->Entries[Index].Action, Actions[Index]);
        TestFalse(TEXT("Fresh isolated profile has no Continue checkpoint"), F.Mode->Entries[0].Enabled);
        auto Tap = [&](FKey Key)
        {
            F.Button(Key, true);
            F.Step();
            F.Button(Key, false);
            F.Step();
        };
        const FKey Confirm = Gamepad ? EKeys::Gamepad_FaceButton_Bottom : EKeys::Enter;
        const FKey Up = Gamepad ? EKeys::Gamepad_DPad_Up : EKeys::W;
        const FKey Down = Gamepad ? EKeys::Gamepad_DPad_Down : EKeys::S;
        TestEqual(TEXT("Title initially focuses the first enabled New Game action"), F.Mode->SelectedEntry, 1);
        F.Mode->SelectedEntry = 0; // Verify the disabled action itself remains protected from activation.
        Tap(Confirm);
        TestTrue(Device + TEXT(" disabled Continue cannot start or dismiss the title"),
                 F.Mode->IsTitleMenu() && !F.Instance->Session.run.active);
        for (FKey Back : {EKeys::Gamepad_FaceButton_Right, EKeys::Gamepad_Special_Right})
        {
            Tap(Back);
            TestTrue(TEXT("Controller Back/Menu cannot bypass the startup title"), F.Mode->IsTitleMenu());
        }
        Tap(Down);
        TestEqual(Device + TEXT(" down selects New Game"), F.Mode->SelectedEntry, 1);
        Tap(Up);
        TestEqual(Device + TEXT(" up cannot focus unavailable Continue"), F.Mode->SelectedEntry, 1);
        Tap(Down);
        TestEqual(Device + TEXT(" second down selects Settings"), F.Mode->SelectedEntry, 2);
        Tap(Confirm);
        TestTrue(Device + TEXT(" confirms actual Settings action"), F.Mode->Panel == ESSPanel::Settings);
        F.Mode->ClosePanel();
        TestTrue(TEXT("Closing title-origin Settings returns to the title"), F.Mode->IsTitleMenu());
        F.Mode->ActivateEntry(2); // The verified title Settings action.
        const int32 Acknowledgements =
            F.Mode->Entries.IndexOfByPredicate([](const FSSMenuEntry &Entry) { return Entry.Action == 9; });
        if (!TestTrue(TEXT("Settings exposes its actual acknowledgements action"), Acknowledgements != INDEX_NONE))
            return false;
        F.Mode->ActivateEntry(Acknowledgements);
        TestTrue(TEXT("Settings opens asset acknowledgements"), F.Mode->Panel == ESSPanel::Acknowledgements);
        F.Mode->ClosePanel();
        TestTrue(TEXT("Closing title-origin acknowledgements returns to the title"), F.Mode->IsTitleMenu());
        Tap(Confirm);
        TestTrue(Device + TEXT(" New Game opens the real home walker without starting survival"),
                 F.Mode->InHangar() && IsValid(F.Mode->Walker) && F.Controller->GetPawn() == F.Mode->Walker &&
                     !F.Mode->IsMenuOpen() && !F.Instance->Session.run.active && !F.Instance->IsFreeFlight());
        F.Mode->OpenPanel(ESSPanel::Main);
        TestFalse(TEXT("Pausing the home station cannot reopen title art"), F.Mode->IsTitleMenu());
        TestEqual(TEXT("Home pause is distinctly labeled"), F.Mode->PanelTitle, FString(TEXT("PAUSED")));
        TestTrue(TEXT("Home pause resumes walking"),
                 F.Mode->Entries.ContainsByPredicate([](const FSSMenuEntry &Entry) { return Entry.Action == 1; }));
        F.Mode->ClosePanel();
        const auto Bodies = F.Mode->WardrobeBodies();
        TestFalse(TEXT("Original Acornaut is retired from wardrobe"),
                  Bodies.ContainsByPredicate([](const FSSHeroDefinition &Body)
                                             { return Body.Identity == ESSHeroIdentity::Acornaut; }));
        F.Instance->Session.account.hero = static_cast<int32>(ESSHeroIdentity::Acornaut);
        TestEqual(TEXT("Legacy Acornaut selection safely resolves to current default"), F.Mode->WornHeroId(),
                  F.Mode->Tuning->SelectHero(ESSHeroSlot::Walker).Id);
        // Ordinary in-game Settings still closes back to play. StartRun is the pure
        // domain operation; GameMode.StartNewRun and all persistence APIs are excluded.
        if (!TestTrue(TEXT("Seed only memory for ordinary in-game Settings"),
                      F.Instance->Session.StartRun("title-settings-regression")))
            return false;
        F.Mode->OpenPanel(ESSPanel::Main);
        const int32 Settings =
            F.Mode->Entries.IndexOfByPredicate([](const FSSMenuEntry &Entry) { return Entry.Action == 5; });
        if (!TestTrue(TEXT("Active pause retains Settings"), Settings != INDEX_NONE))
            return false;
        F.Mode->ActivateEntry(Settings);
        F.Mode->ClosePanel();
        TestTrue(TEXT("Closing active-run Settings returns to play, not startup"),
                 !F.Mode->IsMenuOpen() && !F.Mode->IsTitleMenu() && F.Instance->Session.run.active);
        TestTrue(TEXT("Title fixture keeps account storage blocked"), F.Instance->AccountStorageBlocked);
        TestFalse(TEXT("Title fixture never ran production GameMode BeginPlay"), F.Mode->HasActorBegunPlay());
        // Exit Game/Escape are deliberately never activated inside the shared test process.
    }
    return true;
}

#endif
