#include "Misc/AutomationTest.h"
#include "SSStation.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Physics/Experimental/PhysScene_Chaos.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSWalkerSupportWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    bool Initialize()
    {
        UWorld::InitializationValues Values;
        Values.CreatePhysicsScene(true)
            .ShouldSimulatePhysics(false)
            .AllowAudioPlayback(false)
            .CreateNavigation(false)
            .CreateAISystem(false);
        World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
        if (!World)
            return false;
        GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
        GWorld = World;
        World->InitializeActorsForPlay(FURL());
        World->SetBegunPlay(true);
        World->GetPhysicsScene()->OnWorldBeginPlay();
        return true;
    }
    ~FSSWalkerSupportWorld()
    {
        if (World)
        {
            World->EndPlay(EEndPlayReason::Quit);
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
            GWorld = PreviousWorld;
        }
    }
    UBoxComponent *Box(FVector Location, FVector Extent, ECollisionChannel Type = ECC_WorldStatic)
    {
        auto *Owner = World->SpawnActor<AActor>();
        auto *Shape = NewObject<UBoxComponent>(Owner);
        Owner->SetRootComponent(Shape);
        Owner->AddInstanceComponent(Shape);
        Shape->SetBoxExtent(Extent);
        Shape->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Shape->SetCollisionObjectType(Type);
        Shape->SetCollisionResponseToAllChannels(ECR_Block);
        Shape->RegisterComponent();
        Owner->SetActorLocation(Location);
        return Shape;
    }
    void Frames(int32 Count)
    {
        for (int32 Index = 0; Index < Count; ++Index)
        {
            ++GFrameCounter;
            World->Tick(LEVELTICK_All, 1.f / 60.f);
        }
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSWalkerSupportRecovery, "SpaceSurvival.Integration.WalkerSupportRecovery",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSWalkerSupportRecovery::RunTest(const FString &)
{
    FSSWalkerSupportWorld F;
    if (!TestTrue(TEXT("Create real capsule collision fixture"), F.Initialize()))
        return false;
    auto *Hub = F.World->SpawnActor<ASSStation>();
    Hub->SetActorTickEnabled(false);
    F.Box(FVector(0, 0, -10), FVector(500, 500, 10));
    auto *Decoration = F.Box(FVector(0, 0, 100), FVector(20, 20, 80));
    Decoration->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
    TestTrue(TEXT("Pawn-ignored apartment decoration cannot hide the floor from recovery"),
             Hub->OutpostWalkable(FVector(0, 0, 88), nullptr));
    Decoration->DestroyComponent();
    F.Box(FVector(1200, 0, -10), FVector(100, 100, 10), ECC_WorldDynamic);
    TestTrue(TEXT("Authored movable support counts when it actually blocks the pawn"),
             Hub->OutpostWalkable(FVector(1200, 0, 88), nullptr));
    TestTrue(TEXT("Capsule-edge support remains valid when the centre clears a threshold"),
             Hub->OutpostWalkable(FVector(513, 0, 88), nullptr));
    TestFalse(TEXT("An empty gap is still unsupported"), Hub->OutpostWalkable(FVector(800, 0, 88), nullptr));

    auto *Controller = F.World->SpawnActor<APlayerController>();
    Controller->SetAsLocalPlayerController();
    F.World->AddController(Controller);
    Controller->SetActorTickEnabled(false);
    auto *Walker = F.World->SpawnActor<ASSWalker>(FVector(200, 100, 95), FRotator(0, 53, 0));
    if (!TestNotNull(TEXT("Spawn actual walker"), Walker))
        return false;
    Controller->Possess(Walker);
    F.Frames(20);
    const FVector Safe = Walker->GetActorLocation();
    TestTrue(TEXT("The recorded nearby recovery point is real walking support"),
             Walker->GetCharacterMovement()->IsMovingOnGround());
    const int32 Before = Walker->OffDeckRecoveries();
    const FVector Miss(2400, 0, 95);
    Walker->SetActorLocation(Miss, false, nullptr, ETeleportType::TeleportPhysics);
    Walker->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    Walker->Tick(.1f);
    TestEqual(TEXT("One short support miss never teleports the walker"), Walker->OffDeckRecoveries(), Before);
    TestTrue(TEXT("A short miss preserves the real current position"), Walker->GetActorLocation().Equals(Miss));
    Walker->SetActorLocation(Safe, false, nullptr, ETeleportType::TeleportPhysics);
    Walker->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    F.Frames(5);
    Walker->SetActorLocation(Miss, false, nullptr, ETeleportType::TeleportPhysics);
    Walker->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    Walker->Tick(.31f);
    TestEqual(TEXT("Returning to support resets the miss clock"), Walker->OffDeckRecoveries(), Before);
    Walker->Tick(.1f);
    TestEqual(TEXT("A persistent actual departure is recovered exactly once"), Walker->OffDeckRecoveries(), Before + 1);
    TestTrue(TEXT("A real fall returns to the latest verified nearby floor, not the landing pad"),
             Walker->GetActorLocation().Equals(Safe, 1.f));
    TestEqual(TEXT("Recovery preserves the player's facing"), Walker->GetActorRotation().Yaw, 53., .01);
    return true;
}
#endif
