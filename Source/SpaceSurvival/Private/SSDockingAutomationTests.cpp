#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SphereComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "UObject/UnrealType.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSDockingWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    ASSShip *Ship = nullptr;
    ASSStation *Hub = nullptr;
    APlayerController *Controller = nullptr;

    bool Initialize(FAutomationTestBase &Test, int32 Wave = 5)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated docking world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // No Init/InitializeStandalone or save APIs. Block accidental persistence as well.
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = 0;
        Instance->Session.account.tutorialFlags = 255;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        GWorld = World;
        World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
        if (!Test.TestTrue(TEXT("Install actual docking GameMode"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        World->InitializeActorsForPlay(FURL());
        Controller = World->SpawnActor<APlayerController>();
        if (!Test.TestNotNull(TEXT("Resolve actual GameMode"), Mode) ||
            !Test.TestNotNull(TEXT("Create input-free local controller"), Controller))
            return false;
        Controller->SetAsLocalPlayerController();
        World->AddController(Controller);
        Controller->SetActorTickEnabled(false);
        World->BeginPlay();
        if (!Test.TestTrue(TEXT("Start in-memory arrival fixture"), Instance->Session.StartRun("docking-fixture")))
            return false;
        // Seed arrival instead of waiting through five waves. All admission, collision,
        // docking and disembark code below is the production actor path.
        for (const TCHAR *Name : {TEXT("Ship"), TEXT("Walker"), TEXT("Hub")})
        {
            auto *Property = FindFProperty<FObjectPropertyBase>(ASSGameMode::StaticClass(), Name);
            if (!Test.TestNotNull(TEXT("Resolve existing orchestration reference"), Property))
                return false;
            if (auto *Actor = Cast<AActor>(Property->GetObjectPropertyValue_InContainer(Mode)))
                Actor->Destroy();
            Property->SetObjectPropertyValue_InContainer(Mode, nullptr);
        }
        auto &Run = Instance->Session.run;
        Run.wave = Wave;
        Run.wavesCompleted = Wave;
        Run.phase = SS::Phase::Approach;
        Run.phaseSeconds = Run.phaseDuration = 0;
        Ship = World->SpawnActor<ASSShip>(FVector(13000, -5000, 7200), FRotator(0, 73, 0));
        if (!Test.TestNotNull(TEXT("Create real flight pawn"), Ship))
            return false;
        FindFProperty<FObjectPropertyBase>(ASSGameMode::StaticClass(), TEXT("Ship"))
            ->SetObjectPropertyValue_InContainer(Mode, Ship);
        Controller->Possess(Ship);
        Mode->ClosePanel();
        Mode->Tick(0.f); // Actual phase transition creates the translated, rotated station.
        Hub = Cast<ASSStation>(FindFProperty<FObjectPropertyBase>(ASSGameMode::StaticClass(), TEXT("Hub"))
                                   ->GetObjectPropertyValue_InContainer(Mode));
        return Test.TestNotNull(TEXT("Real approach creates its physical hub"), Hub) &&
               Test.TestTrue(TEXT("Arrival remains manually controlled outside 12 metres"),
                             Run.phase == SS::Phase::Approach && Controller->GetPawn() == Ship);
    }

    void Place(FVector LocalPosition, FVector LocalDirection)
    {
        const auto Transform = Hub->GetActorTransform();
        Ship->SetActorLocationAndRotation(Transform.TransformPosition(LocalPosition),
                                          Transform.TransformVectorNoScale(LocalDirection).Rotation());
    }

    void Reject(FAutomationTestBase &Test, const TCHAR *Name, FVector LocalPosition, FVector LocalDirection)
    {
        Place(LocalPosition, LocalDirection);
        const FVector Before = Ship->GetActorLocation();
        Mode->Tick(0.f);
        Test.TestTrue(FString::Printf(TEXT("%s: no assistance or teleport"), Name),
                      Instance->Session.run.phase == SS::Phase::Approach &&
                          Ship->GetActorLocation().Equals(Before, .001) && Controller->GetPawn() == Ship);
    }

    ~FSSDockingWorld()
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSDockingAdmission, "SpaceSurvival.Integration.DockingAdmission",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSDockingAdmission::RunTest(const FString &)
{
    FSSDockingWorld F;
    if (!F.Initialize(*this))
        return false;
    // This suite used to pin a corridor: eight ways of arriving, each refused for not being "level, centred
    // and through the hangar mouth". Docking now happens at an exterior pad, and the rule for it is that
    // you are not forced to approach a certain way - so most of those refusals describe a game that no
    // longer exists. Worse, every one of them would still have passed, on distance alone, while its name
    // went on claiming to test heading and lane discipline. That is the failure mode where a suite stays
    // green and stops meaning anything, so the cases are re-derived rather than re-pointed.
    //
    // Two things are actually still true of admission, and they are what is tested now: you have to be near
    // the pad, and your hull has to be able to reach it without hitting something. Heading is not a rule any
    // more, which is why the four headings below are ADMITTED rather than refused.
    const FVector Pad(ASSStation::PadCenterX, 0, 220);
    for (const auto &Case : {TPair<FVector, FVector>(Pad + FVector(-900, 0, 0), FVector(1, 0, 0)),
                             TPair<FVector, FVector>(Pad + FVector(0, 0, 900), FVector(0, 0, -1)),
                             TPair<FVector, FVector>(Pad + FVector(0, 900, 0), FVector(0, -1, 0)),
                             TPair<FVector, FVector>(Pad + FVector(700, 0, 0), FVector(-1, 0, 0))})
    {
        F.Instance->Session.run.phase = SS::Phase::Approach;
        F.Instance->Session.run.phaseDuration = 0.0;
        F.Place(Case.Key, Case.Value);
        F.Mode->Tick(0.f);
        TestTrue(TEXT("Any heading is admitted near the pad, including straight down and from behind"),
                 F.Instance->Session.run.phase == SS::Phase::Docking);
    }
    F.Instance->Session.run.phase = SS::Phase::Approach;
    F.Instance->Session.run.phaseDuration = 0.0;
    // Out of range stays out of range, whichever way it points.
    F.Reject(*this, TEXT("Beyond the approach range of the pad"), Pad + FVector(-1900, 0, 0), FVector(1, 0, 0));
    F.Reject(*this, TEXT("Far side of the station"), FVector(1850, 0, 220), FVector(-1, 0, 0));

    auto *Obstacle = F.World->SpawnActor<AActor>();
    if (!TestNotNull(TEXT("Create temporary swept-clearance obstacle"), Obstacle))
        return false;
    auto *Box = NewObject<UBoxComponent>(Obstacle);
    Obstacle->SetRootComponent(Box);
    Obstacle->AddInstanceComponent(Box);
    Box->SetBoxExtent(FVector(30, 80, 150));
    Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Box->SetCollisionObjectType(ECC_WorldStatic);
    Box->SetCollisionResponseToAllChannels(ECR_Block);
    Box->RegisterComponent();
    Obstacle->SetActorLocationAndRotation(F.Hub->GetActorTransform().TransformPosition(Pad + FVector(-450, 160, 0)),
                                          F.Hub->GetActorRotation());
    F.Place(FVector(ASSStation::PadCenterX - 900.f, 0, 220), FVector(1, 0, 0));
    FHitResult Hit;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSDockingRegression), false, F.Ship);
    TestFalse(
        TEXT("Obstacle misses the flight center line"),
        F.World->LineTraceSingleByChannel(Hit, F.Ship->GetActorLocation(), F.Hub->PadDockPosition(), ECC_Pawn, Query));
    TestTrue(TEXT("Actual flight sphere catches the offset obstacle"),
             F.World->SweepSingleByChannel(Hit, F.Ship->GetActorLocation(), F.Hub->PadDockPosition(), FQuat::Identity,
                                           ECC_Pawn, F.Ship->Collision->GetCollisionShape(), Query) &&
                 Hit.GetActor() == Obstacle);
    F.Reject(*this, TEXT("Swept body blocked despite clear center line"), Pad + FVector(-900, 0, 0), FVector(1, 0, 0));
    Obstacle->SetActorEnableCollision(false);
    Obstacle->Destroy();

    F.Place(FVector(ASSStation::PadCenterX - 900.f, 0, 220), FVector(1, 0, 0));
    const FVector AdmissionPosition = F.Ship->GetActorLocation();
    F.Mode->Tick(0.f);
    TestTrue(TEXT("Centered inbound lane admits the actual rotated station"),
             F.Instance->Session.run.phase == SS::Phase::Docking);
    TestEqual(TEXT("Admission preserves the three second docking duration"), F.Instance->Session.run.phaseDuration,
              3.0);
    TestTrue(TEXT("Admission itself does not teleport the player"),
             F.Ship->GetActorLocation().Equals(AdmissionPosition));
    // Admission is still judged against the bay, but the assist now flies the ship to the exterior pad, so
    // the distance that has to be closing is the distance to where it is actually going. Stated as a share
    // of the gap rather than as a band in centimetres: the old 800..1000 window only meant "a tenth of the
    // way, smoothly" for one particular dock distance, and silently stopped meaning it when the dock moved.
    const double BeforeDistance = FVector::Dist(F.Ship->GetActorLocation(), F.Hub->PadDockPosition());
    F.Ship->Tick(.05f);
    const double RemainingDistance = FVector::Dist(F.Ship->GetActorLocation(), F.Hub->PadDockPosition());
    const double Closed = (BeforeDistance - RemainingDistance) / FMath::Max(BeforeDistance, 1.0);
    TestTrue(TEXT("Existing assistance advances smoothly along the cleared path, without teleporting"),
             Closed > .02 && Closed < .25);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSContractArrivalFeedback, "SpaceSurvival.Integration.ContractArrivalFeedback",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSContractArrivalFeedback::RunTest(const FString &)
{
    for (int32 Case = 0; Case < 3; ++Case)
    {
        FSSDockingWorld F;
        if (!F.Initialize(*this, 10))
            return false;
        auto &Session = F.Instance->Session;
        auto &Run = Session.run;
        Session.settings.subtitles = false;
        Session.tuning.objectiveContractReward = 137;
        Session.tuning.pressureContractReward = 193;
        Run.contract = Case == 2 ? SS::Contract::Pressure : SS::Contract::Objective;
        Run.contractAcceptedWave = 5;
        Run.contractTarget = Case == 2 ? 5 : 6;
        Run.contractProgress = Case == 0 ? 5 : Run.contractTarget;
        Run.contractResolved = false;
        Run.credits = Run.totalCreditsEarned = 300;
        F.Place(FVector(ASSStation::PadCenterX - 900.f, 0, 220), FVector(1, 0, 0));
        F.Mode->Tick(0.f);
        if (!TestTrue(TEXT("Contract arrival uses actual docking admission"), Run.phase == SS::Phase::Docking))
            return false;
        F.Mode->Tick(3.01f);
        const int32 Reward = Case == 0 ? 0 : Case == 1 ? 137 : 193;
        TestTrue(TEXT("Actual station transition settles the contract once"),
                 Run.phase == SS::Phase::Station && Run.contract == SS::Contract::None && Run.contractResolved &&
                     Run.credits == 300 + Reward && Run.contractsCompleted == (Case == 0 ? 0 : 1));
        const FString Expected = Case == 0 ? TEXT("Hunter contract failed / no reward")
                                           : FString::Printf(TEXT("%s contract complete / +%d credits"),
                                                             Case == 1 ? TEXT("Hunter") : TEXT("Pressure"), Reward);
        TestTrue(TEXT("Arrival names the real success, payout or failure"), F.Mode->Announcement.Contains(Expected));
        TestTrue(TEXT("Actual arrival result remains visible through the HUD gate with subtitles off"),
                 F.Mode->IsAnnouncementVisible());
        TestEqual(TEXT("Transactional notice retains its full 18-second duration"), F.Mode->AnnouncementSeconds, 18.f);
        const FString Receipt = F.Mode->Announcement;
        auto *Walker = Cast<ASSWalker>(F.Controller->GetPawn());
        if (!TestNotNull(TEXT("Arrival possesses the actual disembarking walker"), Walker))
            return false;
        for (int32 Frame = 0; Frame < 25; ++Frame)
        {
            Walker->Tick(.1f);
            F.Mode->Tick(.1f);
        }
        TestTrue(TEXT("Outcome remains readable after disembark without paying again"),
                 !Walker->IsDisembarking() && F.Mode->Announcement == Receipt && F.Mode->AnnouncementSeconds > 15.f &&
                     F.Mode->IsAnnouncementVisible() && Run.credits == 300 + Reward);
        F.Mode->Tick(.1f);
        TestTrue(TEXT("Repeated station ticks do not synthesize another receipt"),
                 F.Mode->Announcement == Receipt && F.Mode->AnnouncementSeconds < 15.6f);
        F.Mode->Tick(15.5f);
        TestFalse(TEXT("Expired transaction notice disappears normally"), F.Mode->IsAnnouncementVisible());
        TestEqual(TEXT("Notice expiry never pays the settled contract again"), Run.credits, 300 + Reward);
        F.Mode->Announce(TEXT("Dockmaster: Your ship is in the service bay."));
        TestFalse(TEXT("Actual Dockmaster dialogue remains suppressed with subtitles off"),
                  F.Mode->IsAnnouncementVisible());
        Session.settings.subtitles = true;
        TestTrue(TEXT("Enabling subtitles reveals active Dockmaster dialogue"), F.Mode->IsAnnouncementVisible());
        Session.settings.subtitles = false;
        F.Mode->Announce(TEXT("Acornaut: Good to be back."));
        TestFalse(TEXT("Actual pilot dialogue remains suppressed with subtitles off"), F.Mode->IsAnnouncementVisible());
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSStationChaseCamera, "SpaceSurvival.Integration.StationChaseCamera",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSStationChaseCamera::RunTest(const FString &)
{
    FSSDockingWorld F;
    if (!F.Initialize(*this))
        return false;
    F.Place(FVector(ASSStation::PadCenterX - 900.f, 0, 220), FVector(1, 0, 0));
    F.Mode->Tick(0.f);
    F.Mode->Tick(3.01f);
    auto *Walker = Cast<ASSWalker>(F.Controller->GetPawn());
    if (!TestNotNull(TEXT("Actual station arrival supplies the third-person walker"), Walker))
        return false;
    // What arrival hands the player depends on the hero, and both answers are correct. A hero with an
    // exit clip is still climbing out, and the exit owns the camera and the body until it finishes. A
    // hero without one - the ship has no door, so the exit animation was cancelled and logged as
    // RPT-20260917-01 - is standing outside the ship already, and the player has the camera and the body
    // from the first frame. The test asserts whichever applies rather than assuming the climb-out, but it
    // does not let either turn into the other: an exit that ignored input and never ended, or an arrival
    // that left the player unable to look, would both still be caught here.
    const FRotator Arrival = F.Controller->GetControlRotation();
    const bool ClimbsOut = !Walker->GetHero().DisembarkClipPath.IsEmpty();
    AddInfo(FString::Printf(TEXT("STATION_ARRIVAL hero=%s climbsOut=%d"), *Walker->GetHero().Id.ToString(),
                            ClimbsOut ? 1 : 0));
    // Read before Move, which sets the body's rotation itself. This fixture flies in on a heading of 73
    // degrees and the station is built at it, so the hub's yaw here is nothing like world north - which
    // is the whole point. A hero with no exit clip is placed by the spawn and by nothing else: it does
    // not orient to movement and does not follow the controller, and the authored exit that used to
    // reconcile body and camera by slerping to the hub's rotation on its last tick never runs. So the
    // spawn has to have turned it, or the player meets the hero 73 degrees side-on for the whole arrival
    // and the body snaps through that angle on the first input. A climbing hero is mid-clip here and
    // wears the seated pose instead; its facing is checked below, where the exit has finished.
    const double HubYaw = F.Hub->GetActorRotation().Yaw;
    if (!ClimbsOut)
        TestEqual(TEXT("A hero with no exit clip arrives turned the way the station faces"),
                  double(FMath::Abs(FMath::FindDeltaAngleDegrees(Walker->GetActorRotation().Yaw, HubYaw))), 0., 1e-3);
    TestEqual(TEXT("The arrival camera is pointed the same way the station faces"),
              double(FMath::Abs(FMath::FindDeltaAngleDegrees(Arrival.Yaw, HubYaw))), 0., 1e-3);
    Walker->Move(FVector2D(0, 1), FVector2D(1, 1), true, .1f);
    if (ClimbsOut)
        TestTrue(TEXT("An authored disembark ignores look and walking"),
                 Walker->IsDisembarking() && F.Controller->GetControlRotation().Equals(Arrival) &&
                     Walker->GetPendingMovementInputVector().IsNearlyZero());
    else
        TestTrue(TEXT("A hero with no exit clip already has look and walking when docking finishes"),
                 !Walker->IsDisembarking() && !F.Controller->GetControlRotation().Equals(Arrival) &&
                     !Walker->GetPendingMovementInputVector().IsNearlyZero() &&
                     Walker->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics);
    Walker->ConsumeMovementInputVector();
    for (int32 Frame = 0; Frame < 25; ++Frame)
        Walker->Tick(.1f);
    // Either route ends in the same place: the player driving the walker, however it got onto the deck.
    TestTrue(TEXT("The chase camera checks below run on a walker the player controls"),
             !Walker->IsDisembarking() && F.Controller->GetPawn() == Walker &&
                 Walker->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics);
    // The climb-out's own last tick slerps the body to the station's facing, which is the behaviour the
    // spawn above now has to reproduce for a hero that never runs it. Asserted here rather than with the
    // other one because it is only true once the clip has finished. The walking hero has been driven by
    // Move since, so its facing is its view's and is no longer the arrival's to check.
    if (ClimbsOut)
        TestEqual(TEXT("A climb-out ends turned the way the station faces"),
                  double(FMath::Abs(FMath::FindDeltaAngleDegrees(Walker->GetActorRotation().Yaw, HubYaw))), 0., 1e-3);
    for (int32 Rate : {30, 60, 144})
    {
        const float Dt = 1.f / Rate;
        for (float Sign : {-1.f, 1.f})
        {
            F.Controller->SetControlRotation(FRotator::ZeroRotator);
            for (int32 Frame = 0; Frame < Rate; ++Frame)
                Walker->Move(FVector2D::ZeroVector, FVector2D(1, Sign * .5f), false, Dt);
            const FRotator View = F.Controller->GetControlRotation().GetNormalized();
            TestTrue(TEXT("Station yaw applies now rather than waiting in discarded RotationInput"),
                     FMath::IsNearlyEqual(View.Yaw, 90.f, .01f));
            TestTrue(TEXT("Both vertical directions turn equally across frame rates"),
                     FMath::IsNearlyEqual(View.Pitch, -Sign * 35.f, .01f));
            TestTrue(TEXT("The upright body faces camera yaw without camera pitch or roll"),
                     Walker->GetActorRotation().Equals(FRotator(0, 90, 0), .01f));
        }
    }
    F.Controller->SetControlRotation(FRotator(-12, 73, 0));
    Walker->Move(FVector2D(0, -1), FVector2D::ZeroVector, false, 1.f / 60.f);
    TestTrue(TEXT("Backward walking stays behind-facing rather than rotating toward the viewer"),
             Walker->GetActorRotation().Equals(FRotator(0, 73, 0), .01f) &&
                 FVector::DotProduct(Walker->GetPendingMovementInputVector(), Walker->GetActorForwardVector()) <
                     -.99f &&
                 !Walker->GetCharacterMovement()->bOrientRotationToMovement);
    Walker->ConsumeMovementInputVector();
    Walker->Move(FVector2D(1, 0), FVector2D::ZeroVector, true, 1.f / 60.f);
    TestTrue(TEXT("Strafe uses the same view direction and retains run speed"),
             FVector::DotProduct(Walker->GetPendingMovementInputVector(), Walker->GetActorRightVector()) > .99f &&
                 Walker->GetCharacterMovement()->MaxWalkSpeed == 560.f);
    Walker->ConsumeMovementInputVector();
    Walker->Boom->TickComponent(1.f / 60.f, LEVELTICK_All, nullptr);
    TestTrue(TEXT("Actual camera remains behind the facing body with collision protection enabled"),
             FVector::DotProduct(Walker->Camera->GetComponentLocation() - Walker->GetActorLocation(),
                                 Walker->GetActorForwardVector()) < -100.f &&
                 Walker->Boom->bDoCollisionTest);
    Walker->Move(FVector2D::ZeroVector, FVector2D(0, 100), false, 1.f);
    TestEqual(TEXT("Downward view stops before flipping the camera"),
              FRotator::NormalizeAxis(F.Controller->GetControlRotation().Pitch), -55.0);
    Walker->Move(FVector2D::ZeroVector, FVector2D(0, -100), false, 1.f);
    TestEqual(TEXT("Upward view remains bounded"), FRotator::NormalizeAxis(F.Controller->GetControlRotation().Pitch),
              35.0);
    return true;
}
#endif
