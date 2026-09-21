#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSShipVisualRig.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
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
        Controller->SetAsLocalPlayerController();
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
        for (int32 Frame = 0; Frame < 240 && !F.Mode->IsMenuOpen(); ++Frame)
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
        if (!TestTrue(TEXT("Walking into the supported rear cabin opens the actual launch-choice panel"),
                      F.Mode->Panel == ESSPanel::Launch && F.Mode->IsWalkerInsideShip(F.Walker)))
            continue;
        TestTrue(TEXT("Boarding retains the walker until a launch choice is confirmed"),
                 F.Controller->GetPawn() == F.Walker);
        F.Mode->ClosePanel();
        F.Frames(30);
        TestFalse(TEXT("Closing launch choices while still in the cabin does not reopen them"), F.Mode->IsMenuOpen());
        for (int32 Frame = 0; Frame < 180 && F.Local().X > -1500; ++Frame)
            F.Frame(FVector2D(0, -1));
        TestTrue(TEXT("Walker can turn and walk back down the real ramp"),
                 F.Local().X < -1450 && F.Walker->GetCharacterMovement()->IsMovingOnGround());
        for (int32 Frame = 0; Frame < 240 && !F.Mode->IsMenuOpen(); ++Frame)
            F.Frame(FVector2D(0, 1));
        TestTrue(TEXT("Leaving and re-entering the cabin offers boarding again"), F.Mode->Panel == ESSPanel::Launch);
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
