#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSWorldActors.h"
#include "Camera/CameraComponent.h"
#include "Components/SphereComponent.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerInput.h"
#include "GameFramework/WorldSettings.h"
#include "InputKeyEventArgs.h"
#include "Physics/Experimental/PhysScene_Chaos.h"

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

    ~FSSControllerFlightWorld()
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
            F.Axis(Gamepad ? EKeys::Gamepad_RightY : EKeys::MouseY, Gamepad ? .6f : -4.f);
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
            F.Axis(Gamepad ? EKeys::Gamepad_RightY : EKeys::MouseY, Gamepad ? .6f : -4.f);
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
#endif
