#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSShipVisualRig.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "Camera/CameraComponent.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/WorldSettings.h"
#include "Physics/Experimental/PhysScene_Chaos.h"
#include "UObject/UnrealType.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSBoardingWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    ASSStation *Hub = nullptr;
    ASSShip *Ship = nullptr;
    ASSWalker *Walker = nullptr;
    APlayerController *Controller = nullptr;
    ULocalPlayer *LocalPlayer = nullptr;

    bool Initialize(FAutomationTestBase &Test, bool Home)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated actual-movement boarding world"), World))
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
        if (!Test.TestTrue(TEXT("Install production boarding mode"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        auto *Data = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
        if (!Test.TestNotNull(TEXT("Load production tuning"), Data))
            return false;
        Mode->Tuning = DuplicateObject<USSPhase1Data>(Data, Mode);
        Mode->SetActorTickEnabled(false);
        Mode->Director->SetComponentTickEnabled(false);
        if (!Home)
        {
            if (!Test.TestTrue(TEXT("Create in-memory station run"), Instance->Session.StartRun("boarding-fixture")))
                return false;
            Instance->Session.run.phase = SS::Phase::Station;
            Instance->Session.run.wave = Instance->Session.run.wavesCompleted = 5;
        }
        World->InitializeActorsForPlay(FURL());
        // Skip account/startup BeginPlay, retaining real actor, physics and CharacterMovement ticks.
        World->SetBegunPlay(true);
        World->GetPhysicsScene()->OnWorldBeginPlay();
        Controller = World->SpawnActor<APlayerController>();
        // Production pause routes through the game instance's local-player registry.
        LocalPlayer = NewObject<ULocalPlayer>(GEngine, NAME_None, RF_Transient);
        Instance->AddLocalPlayer(LocalPlayer, FPlatformUserId::CreateFromInternalId(0));
        Controller->SetPlayer(LocalPlayer);
        if (!Test.TestNotNull(TEXT("Real boarding pause has a registered owning player state"),
                              Controller->PlayerState.Get()))
            return false;
        World->AddController(Controller);
        Controller->SetActorTickEnabled(false);
        Hub = World->SpawnActor<ASSStation>(FVector(1000, -2000, 7000), FRotator(0, Home ? 0 : 73, 0));
        Hub->BuildHub(Home);
        if (!Test.TestTrue(TEXT("Actual functional home/station layout is loaded"), Hub->IsUsingFunctionalLayout()))
            return false;
        Ship = World->SpawnActor<ASSShip>(Hub->PadDockPosition(), Hub->PadDockRotation());
        Ship->SetDockingTarget(Hub->PadDockPosition(), Hub->PadDockRotation());
        Ship->FinishDocking();
        Ship->SetActorTickEnabled(false);
        if (!Test.TestTrue(TEXT("Actual Phoenix rig is parked for boarding"), Ship->GetVisualRig()->HasBlueprintRig()))
            return false;
        const float HalfHeight = GetDefault<ASSWalker>()->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight();
        Walker = World->SpawnActor<ASSWalker>(
            Ship->GetActorTransform().TransformPosition(FVector(-1510, 0, HalfHeight + 1)), Ship->GetActorRotation());
        if (!Test.TestNotNull(TEXT("Create actual walker outside the ramp toe"), Walker))
            return false;
        Controller->Possess(Walker);
        Controller->SetControlRotation(Ship->GetActorRotation());
        for (const auto &Pair : {TPair<FName, UObject *>(TEXT("Hub"), Hub), TPair<FName, UObject *>(TEXT("Ship"), Ship),
                                 TPair<FName, UObject *>(TEXT("Walker"), Walker)})
        {
            auto *Property = FindFProperty<FObjectPropertyBase>(ASSGameMode::StaticClass(), Pair.Key);
            if (!Test.TestNotNull(TEXT("Bind production ownership for boarding"), Property))
                return false;
            Property->SetObjectPropertyValue_InContainer(Mode, Pair.Value);
        }
        Frames(20);
        return Test.TestTrue(TEXT("Walker begins supported by the actual pad"),
                             Walker->GetCharacterMovement()->IsMovingOnGround());
    }

    FVector Local() const
    {
        return Ship->GetActorTransform().InverseTransformPosition(Walker->GetActorLocation());
    }
    void Frame(FVector2D Direction = FVector2D::ZeroVector)
    {
        Walker->Move(Direction, FVector2D::ZeroVector, false, 1.f / 60.f);
        ++GFrameCounter;
        World->Tick(LEVELTICK_All, 1.f / 60.f);
    }
    void Frames(int32 Count, FVector2D Direction = FVector2D::ZeroVector)
    {
        for (int32 Index = 0; Index < Count; ++Index)
            Frame(Direction);
    }
    ~FSSBoardingWorld()
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPhoenixWalkBoarding, "SpaceSurvival.Integration.PhoenixWalkBoarding",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSPhoenixWalkBoarding::RunTest(const FString &)
{
    for (bool Home : {true, false})
    {
        FSSBoardingWorld F;
        if (!F.Initialize(*this, Home))
            return false;
        const float Radius = F.Walker->GetCapsuleComponent()->GetScaledCapsuleRadius();
        const float HalfHeight = F.Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
        auto CanBoard = [&](FVector Local)
        {
            return F.Ship->GetVisualRig()->CanBoardAt(F.Ship->GetActorTransform().TransformPosition(Local), Radius,
                                                      HalfHeight);
        };
        TestFalse(TEXT("Standing at the ramp toe does not open launch choices"), F.Mode->IsMenuOpen());
        TestFalse(TEXT("Side proximity outside the cabin cannot board"),
                  CanBoard(FVector(-850, 260, HalfHeight + 238)));
        TestFalse(TEXT("Standing underneath the cabin cannot board"), CanBoard(FVector(-850, 0, HalfHeight)));
        TestFalse(TEXT("Airborne above the cabin floor cannot board"), CanBoard(FVector(-850, 0, HalfHeight + 300)));
        bool ToeContact = false, MainContact = false;
        double LargestHeightStep = 0;
        FVector Previous = F.Local();
        for (int32 Frame = 0; Frame < 240 && !F.Mode->IsWalkerInsideShip(F.Walker); ++Frame)
        {
            F.Frame(FVector2D(0, 1));
            const FVector Now = F.Local();
            LargestHeightStep = FMath::Max(LargestHeightStep, FMath::Abs(Now.Z - Previous.Z));
            Previous = Now;
            const auto *Floor = F.Walker->GetCharacterMovement()->CurrentFloor.HitResult.GetComponent();
            ToeContact |= Floor && Floor->GetName() == TEXT("BoardingRampToe");
            MainContact |= Floor && Floor->GetName() == TEXT("BoardingRampMain");
        }
        AddInfo(FString::Printf(
            TEXT("BOARDING home=%d shipYaw=%.2f local=%s toe=%d main=%d maxStep=%.3f grounded=%d floor=%s menu=%d"),
            Home, F.Ship->GetActorRotation().Yaw, *F.Local().ToString(), ToeContact, MainContact, LargestHeightStep,
            F.Walker->GetCharacterMovement()->IsMovingOnGround(),
            *GetNameSafe(F.Walker->GetCharacterMovement()->CurrentFloor.HitResult.GetComponent()),
            F.Mode->IsMenuOpen()));
        TestTrue(TEXT("Real CharacterMovement climbs both supplied ramp panels from the actual deck"),
                 ToeContact && MainContact);
        TestTrue(TEXT("Ramp and cabin seams stay below the ordinary step height without teleporting"),
                 LargestHeightStep < 25.);
        TestEqual(TEXT("Boarding route needs no off-deck rescue"), F.Walker->OffDeckRecoveries(), 0);
        TestFalse(TEXT("Walking up the ramp never opens a popup"), F.Mode->IsMenuOpen());
        F.Mode->Interact();
        if (!TestTrue(TEXT("Rear cabin stays on foot; only the cockpit chair can begin departure"),
                      !F.Mode->IsMenuOpen() && F.Mode->IsWalkerInsideShip(F.Walker) && !F.Walker->IsBoarding()))
            continue;
        TestTrue(TEXT("Rear cabin retains the walking pawn"), F.Controller->GetPawn() == F.Walker);
        F.Mode->ClosePanel();
        F.Frames(30);
        TestFalse(TEXT("Waiting inside the rear cabin never opens a launch menu"), F.Mode->IsMenuOpen());
        for (int32 Frame = 0; Frame < 180 && F.Local().X > -1500; ++Frame)
            F.Frame(FVector2D(0, -1));
        TestTrue(TEXT("Walker can turn and walk back down the real ramp"),
                 F.Local().X < -1450 && F.Walker->GetCharacterMovement()->IsMovingOnGround());
        for (int32 Frame = 0; Frame < 240 && !F.Mode->IsWalkerInsideShip(F.Walker); ++Frame)
            F.Frame(FVector2D(0, 1));
        TestFalse(TEXT("Re-entering still leaves movement uninterrupted"), F.Mode->IsMenuOpen());
        F.Mode->Interact();
        TestTrue(TEXT("Rear-cabin re-entry cannot bypass the cockpit chair"),
                 !F.Mode->IsMenuOpen() && !F.Walker->IsBoarding());
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPhoenixCockpitDeparture, "SpaceSurvival.Integration.PhoenixCockpitDeparture",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSPhoenixCockpitDeparture::RunTest(const FString &)
{
    for (const bool Home : {true, false})
    {
        FSSBoardingWorld F;
        if (!F.Initialize(*this, Home))
            return false;
        // Initialize constructs the already-entered station without running startup/session ticks.
        // Match that history once: a first Tick at chair commit must not treat the existing Station
        // phase as a new arrival and replace the pilot immediately after beginning departure.
        F.Mode->PreviousPhase = int32(F.Instance->Session.run.phase);
        F.Mode->PreviousWave = F.Instance->Session.run.wave;
        TestTrue(TEXT("The isolated boarding world begins with its existing station phase observed"),
                 F.Mode->PreviousPhase == int32(F.Instance->Session.run.phase) &&
                     F.Mode->PreviousWave == F.Instance->Session.run.wave);
        const std::string RunId = F.Instance->Session.run.id;
        const int32 Wave = F.Instance->Session.run.wave;
        TestEqual(TEXT("Current measured squirrel retains radius and receives its body-height collision fit"),
                  F.Walker->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight(), 75.f);
        TestEqual(TEXT("The measured height correction never reduces the horizontal body clearance"),
                  F.Walker->GetCapsuleComponent()->GetUnscaledCapsuleRadius(), 34.f);
        const FTransform MeshBeforeRefit = F.Walker->GetMesh()->GetComponentTransform();
        const FVector FootBeforeRefit =
            F.Walker->GetActorLocation() -
            FVector::UpVector * F.Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
        F.Walker->ApplyHero(F.Walker->GetHero().Id);
        TestTrue(TEXT("Reapplying the measured hero preserves the world soles and rendered size"),
                 F.Walker->GetMesh()->GetComponentTransform().Equals(MeshBeforeRefit, .001f) &&
                     (F.Walker->GetActorLocation() -
                      FVector::UpVector * F.Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight())
                         .Equals(FootBeforeRefit, .001f));
        if (Home)
        {
            F.Mode->OpenPanel(ESSPanel::Launch);
            const int32 FreeFlight =
                F.Mode->Entries.IndexOfByPredicate([](const FSSMenuEntry &Entry) { return Entry.Action == 156; });
            if (!TestTrue(TEXT("Station computer exposes an explicit Free Flight preference"),
                          FreeFlight != INDEX_NONE))
                return false;
            TestFalse(TEXT("The computer has no immediate start/depart command"),
                      F.Mode->Entries.ContainsByPredicate(
                          [](const FSSMenuEntry &Entry)
                          { return Entry.Action == 3 || Entry.Action == 50 || Entry.Action == 52; }));
            F.Mode->ActivateEntry(FreeFlight);
            TestTrue(TEXT("Terminal changes only the departure preference"),
                     F.Mode->GetSelectedDepartureMode() == ESSDepartureMode::FreeFlight &&
                         !F.Instance->IsFreeFlight() && F.Instance->Session.run.id == RunId &&
                         F.Instance->Session.run.wave == Wave && !F.Mode->IsMenuOpen());
            F.Mode->CycleDepartureMode();
        }
        else
        {
            F.Mode->CycleDepartureMode();
            TestTrue(TEXT("Station 1 retains its active Waves mode and progress"),
                     F.Mode->GetSelectedDepartureMode() == ESSDepartureMode::Waves &&
                         F.Instance->Session.run.id == RunId && F.Instance->Session.run.wave == 5);
        }
        const auto SeatAt = [&](FVector Local)
        {
            return F.Ship->GetVisualRig()->CanUsePilotSeatAt(F.Ship->GetActorTransform().TransformPosition(Local), 34.f,
                                                             75.f);
        };
        UStaticMeshComponent *Interior = nullptr;
        TInlineComponentArray<UStaticMeshComponent *> RigMeshes(F.Ship->GetVisualRig()->GetHull()->GetOwner());
        for (UStaticMeshComponent *Component : RigMeshes)
            if (Component->GetFName() == TEXT("ParkedInterior"))
                Interior = Component;
        if (!TestNotNull(TEXT("The actual parked interior exists for cold and warm boarding"), Interior))
            return false;
        TestTrue(TEXT("The parked interior has a real Pawn-blocking physics query before any walking"),
                 Interior->IsPhysicsStateCreated() && Interior->IsCollisionEnabled() &&
                     Interior->GetCollisionResponseToChannel(ECC_Pawn) == ECR_Block);
        const auto LogSeatProbe = [&](const TCHAR *Stage, FVector Local)
        {
            bool Compiling = false;
#if WITH_EDITOR
            Compiling = Interior->GetStaticMesh() && Interior->GetStaticMesh()->IsCompiling();
#endif
            AddInfo(
                FString::Printf(TEXT("COCKPIT_QUERY_STATE home=%d stage=%s interiorPhysics=%d compiling=%d "
                                     "capsuleCollision=%d capsuleVisibility=%d meshCollision=%d meshVisibility=%d"),
                                Home, Stage, Interior->IsPhysicsStateCreated(), Compiling,
                                int32(F.Walker->GetCapsuleComponent()->GetCollisionEnabled()),
                                int32(F.Walker->GetCapsuleComponent()->GetCollisionResponseToChannel(ECC_Visibility)),
                                int32(F.Walker->GetMesh()->GetCollisionEnabled()),
                                int32(F.Walker->GetMesh()->GetCollisionResponseToChannel(ECC_Visibility))));
            const FVector Up = F.Ship->GetActorUpVector();
            const FVector Base = F.Ship->GetActorTransform().TransformPosition(Local) - Up * (75.f - 34.f);
            for (const bool IgnoreWalker : {false, true})
            {
                FCollisionQueryParams Query(SCENE_QUERY_STAT(PhoenixChairDiagnostic), false, F.Ship);
                if (IgnoreWalker)
                    Query.AddIgnoredActor(F.Walker);
                FHitResult Hit;
                const bool Blocking =
                    F.World->SweepSingleByChannel(Hit, Base + Up * 5.f, Base - Up * 5.f, FQuat::Identity,
                                                  ECC_Visibility, FCollisionShape::MakeSphere(34.f), Query);
                AddInfo(FString::Printf(
                    TEXT("COCKPIT_QUERY home=%d stage=%s ignoreWalker=%d local=%s hit=%d actor=%s component=%s "
                         "interior=%d penetrating=%d point=%s normal=%s time=%.6f"),
                    Home, Stage, IgnoreWalker, *Local.ToString(), Blocking, *GetNameSafe(Hit.GetActor()),
                    *GetNameSafe(Hit.GetComponent()), Hit.GetComponent() == Interior, Hit.bStartPenetrating,
                    *F.Ship->GetActorTransform().InverseTransformPosition(Hit.ImpactPoint).ToString(),
                    *Hit.ImpactNormal.ToString(), Hit.Time));
            }
        };
        // The first native route reached this real supported pose against the chair. Its rounded
        // base rests on the tread at X756.4/Z379.1; the centre ray sees Z372.2 below the next riser.
        LogSeatProbe(TEXT("MeasuredSupport"), FVector(766.912, 0, 454.273));
        TestTrue(TEXT("The measured supported capsule can use the chair while straddling its approach tread"),
                 SeatAt(FVector(766.912, 0, 454.273)));
        TestFalse(TEXT("A capsule hovering above the chair approach cannot use the seat"),
                  SeatAt(FVector(766.912, 0, 474.273)));
        TestFalse(TEXT("Standing beside the cockpit outside the chair reach cannot use the seat"),
                  SeatAt(FVector(766.912, 150, 454.273)));
        TestFalse(TEXT("The rear cabin cannot become a remote chair interaction"), SeatAt(FVector(-850, 0, 313)));
        for (int32 Frame = 0; Frame < 900 && !F.Mode->IsWalkerAtPilotSeat(F.Walker); ++Frame)
        {
            // Actual paired capsule queries show a one-sided console trim at X110..150.
            // Ten centimetres left clears the unchanged radius, then the stair crest
            // requires the centreline. CharacterMovement still owns the entire route.
            const FVector Local = F.Local();
            const float TargetY = -10.f * (1.f - FMath::Clamp((float(Local.X) - 180.f) / 70.f, 0.f, 1.f));
            F.Frame(FVector2D(FMath::Clamp((TargetY - float(Local.Y)) * .15f, -.35f, .35f), 1.f));
        }
        AddInfo(FString::Printf(
            TEXT("COCKPIT home=%d local=%s floor=%s grounded=%d floorGap=%.3f rescues=%d"), Home, *F.Local().ToString(),
            *GetNameSafe(F.Walker->GetCharacterMovement()->CurrentFloor.HitResult.GetComponent()),
            F.Walker->GetCharacterMovement()->IsMovingOnGround(),
            F.Walker->GetCharacterMovement()->CurrentFloor.FloorDist, F.Walker->OffDeckRecoveries()));
        LogSeatProbe(TEXT("WalkedApproach"), F.Local());
        if (!TestTrue(TEXT("Ordinary CharacterMovement reaches the chair through the actual interior triangles"),
                      F.Mode->IsWalkerAtPilotSeat(F.Walker)))
            continue;
        TestEqual(TEXT("The complete ramp, passage and stairs need no rescue"), F.Walker->OffDeckRecoveries(), 0);
        TestFalse(TEXT("Walking to the cockpit never opens a launch menu"), F.Mode->IsMenuOpen());
        const FTransform Standing = F.Walker->GetActorTransform();
        const FVector StandingCamera = F.Walker->Camera->GetComponentLocation();
        const FVector StandingBoom = F.Walker->Boom->GetComponentLocation();
        const FVector StandingBoomRelative = F.Walker->Boom->GetRelativeLocation();
        F.Mode->Interact();
        TestTrue(TEXT("Chair interaction begins a visible sit without destroying or unpossessing the walker"),
                 F.Walker->IsBoarding() && !F.Walker->IsSeated() && F.Walker->GetMesh()->IsVisible() &&
                     F.Controller->GetPawn() == F.Walker && !F.Mode->IsDepartingStation() && !F.Mode->IsMenuOpen());
        TestFalse(TEXT("Repeated chair use cannot restart the transition"), F.Mode->TryBoardShip(F.Walker));
        F.Frames(30);
        TestTrue(TEXT("Half-second sample retains a visible intermediate seated blend"),
                 F.Walker->IsBoarding() && !F.Walker->IsSeated() && F.Walker->GetMesh()->IsVisible() &&
                     !F.Walker->GetActorTransform().Equals(Standing, .01f));
        TestTrue(TEXT("The intermediate sit retains the colliding camera behind the moving hero"),
                 F.Walker->Boom->bDoCollisionTest &&
                     F.Walker->Boom->GetComponentLocation().Equals(StandingBoom, .01f) &&
                     F.Walker->Camera->GetComponentLocation().Equals(StandingCamera, 2.f));
        const FTransform BeforePause = F.Walker->GetActorTransform();
        F.Mode->OpenPanel(ESSPanel::Main);
        F.Frames(30);
        TestTrue(TEXT("Pause freezes the visible sit and closing it resumes the same transition"),
                 F.World->IsPaused() && F.Walker->IsBoarding() && !F.Walker->IsSeated() &&
                     F.Walker->GetActorTransform().Equals(BeforePause, .01f));
        F.Mode->ClosePanel();
        F.Frames(60);
        if (!TestTrue(TEXT("The complete sit reaches a valid same-rig pilot handoff"),
                      F.Ship->CanAdoptBoardedPilot(F.Walker)))
            continue;
        const FVector SeatedCamera = F.Walker->Camera->GetComponentLocation();
        const FVector SeatedPelvis = F.Walker->GetMesh()->GetSocketLocation(F.Walker->GetHero().PelvisBone);
        TestTrue(TEXT("Seated camera stays behind the chair approach instead of collapsing into the hero"),
                 F.Walker->Boom->bDoCollisionTest && SeatedCamera.Equals(StandingCamera, 2.f) &&
                     FVector::Distance(SeatedCamera, SeatedPelvis) > 100.f);
        const FTransform Seated = F.Walker->GetMesh()->GetComponentTransform();
        const auto *SeatedMesh = F.Walker->GetMesh()->GetSkeletalMeshAsset();
        FString CommitReason;
        const bool CanCommit = F.Mode->CanCommitDeparture(CommitReason);
        AddInfo(FString::Printf(TEXT("COCKPIT_COMMIT home=%d eligible=%d seated=%d phase=%d previousPhase=%d "
                                     "wave=%d previousWave=%d reason=%s"),
                                Home, CanCommit, F.Walker->IsSeated(), int32(F.Instance->Session.run.phase),
                                F.Mode->PreviousPhase, F.Instance->Session.run.wave, F.Mode->PreviousWave,
                                *CommitReason));
        F.Mode->Tick(0.f);
        AddInfo(FString::Printf(TEXT("COCKPIT_RESULT home=%d departing=%d takingOff=%d possessedShip=%d message=%s"),
                                Home, F.Mode->IsDepartingStation(), F.Ship->IsTakingOff(),
                                F.Controller->GetPawn() == F.Ship, *F.Mode->Announcement));
        if (Home)
        {
            // This fixture intentionally blocks account storage. Starting Waves must fail safely.
            TestTrue(TEXT("Failed account save restores walking at the original chair approach"),
                     !F.Mode->IsDepartingStation() && !F.Walker->IsBoarding() && F.Controller->GetPawn() == F.Walker &&
                         F.Walker->GetActorTransform().Equals(Standing, .01f) &&
                         F.Walker->GetCapsuleComponent()->IsCollisionEnabled() && !F.Instance->Session.run.active);
            TestTrue(TEXT("Failed departure restores the normal walking camera attachment"),
                     F.Walker->Boom->GetRelativeLocation().Equals(StandingBoomRelative, .01f));
            F.Frames(1);
            TestTrue(TEXT("The restored walking view matches the original supported chair approach"),
                     F.Walker->Camera->GetComponentLocation().Equals(StandingCamera, 2.f));
        }
        else
        {
            TestTrue(TEXT("Station 1 chair starts the existing takeoff on the same ship"),
                     F.Mode->IsDepartingStation() && F.Controller->GetPawn() == F.Ship && F.Ship->IsTakingOff());
            TestTrue(TEXT("Same visible hero and exact component pose survive walking-pawn release"),
                     F.Ship->Pilot->IsVisible() && F.Ship->Pilot->GetSkeletalMeshAsset() == SeatedMesh &&
                         F.Ship->Pilot->GetComponentTransform().Equals(Seated, .01f));
            TestTrue(TEXT("Sitting does not restart the run or spend Wave 6 on the pad"),
                     F.Instance->Session.run.id == RunId && F.Instance->Session.run.wave == 5 &&
                         F.Instance->Session.run.phase == SS::Phase::Station);
        }
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSWalkerDirectionalMovement, "SpaceSurvival.Integration.WalkerDirectionalMovement",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSWalkerDirectionalMovement::RunTest(const FString &)
{
    FSSBoardingWorld F;
    if (!F.Initialize(*this, true))
        return false;
    // Move along the clear rear pad edge, perpendicular to the ship, then reverse. No teleport or
    // direct velocity assignment supplies the assertion: CharacterMovement owns acceleration/turns.
    const FVector Start = F.Walker->GetActorLocation();
    const FRotator View = F.Controller->GetControlRotation();
    F.Frames(35, FVector2D(1, 0));
    const FVector Right = FRotationMatrix(FRotator(0, View.Yaw, 0)).GetUnitAxis(EAxis::Y);
    TestTrue(TEXT("Right movement travels to camera right and turns the character toward that travel"),
             FVector::DotProduct(F.Walker->GetActorLocation() - Start, Right) > 100.f &&
                 FVector::DotProduct(F.Walker->GetActorForwardVector(), Right) > .99f);
    TestTrue(TEXT("Directional walking leaves the camera heading independent"),
             F.Controller->GetControlRotation().Equals(View, .01f));
    const FVector Reversal = F.Walker->GetActorLocation();
    F.Frames(50, FVector2D(-1, 0));
    TestTrue(TEXT("Reversing turns the character around instead of gliding sideways"),
             FVector::DotProduct(F.Walker->GetActorLocation() - Reversal, Right) < -100.f &&
                 FVector::DotProduct(F.Walker->GetActorForwardVector(), -Right) > .99f);
    F.Frames(15);
    const double GroundZ = F.Walker->GetActorLocation().Z;
    F.Walker->Jump();
    F.Frames(8);
    TestTrue(TEXT("The grounded walker can jump under actual CharacterMovement"),
             F.Walker->GetCharacterMovement()->IsFalling() && F.Walker->GetActorLocation().Z > GroundZ + 20.f);
    F.Walker->StopJumping();
    F.Frames(90);
    TestTrue(TEXT("Jump returns to the same supported pad without rescue"),
             F.Walker->GetCharacterMovement()->IsMovingOnGround() && F.Walker->OffDeckRecoveries() == 0);
    return true;
}
#endif
