#include "Misc/AutomationTest.h"
#include "SSOutpostSandbox.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Physics/Experimental/PhysScene_Chaos.h"

#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR
namespace
{
struct FSSOutpostTestWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;

    bool Initialize(FAutomationTestBase &Test)
    {
        UWorld::InitializationValues Values;
        Values.CreatePhysicsScene(true)
            .ShouldSimulatePhysics(false)
            .AllowAudioPlayback(false)
            .RequiresHitProxies(false)
            .CreateNavigation(false)
            .CreateAISystem(false);
        World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
        if (!Test.TestNotNull(TEXT("Create isolated outpost collision world"), World))
            return false;
        GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
        GWorld = World;
        World->InitializeActorsForPlay(FURL());
        World->SetBegunPlay(true);
        if (!Test.TestNotNull(TEXT("Collision scene exists"), World->GetPhysicsScene()))
            return false;
        World->GetPhysicsScene()->OnWorldBeginPlay();
        return true;
    }
    ~FSSOutpostTestWorld()
    {
        if (World)
        {
            World->EndPlay(EEndPlayReason::Quit);
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
            GWorld = PreviousWorld;
        }
    }
    AActor *Box(const FVector &Where, const FVector &Extent, ECollisionChannel ObjectType)
    {
        auto *Actor = World->SpawnActor<AActor>();
        auto *Shape = NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Shape);
        Actor->AddInstanceComponent(Shape);
        Shape->SetBoxExtent(Extent);
        Shape->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        Shape->SetCollisionObjectType(ObjectType);
        Shape->SetCollisionResponseToAllChannels(ECR_Block);
        Shape->RegisterComponent();
        Actor->SetActorLocation(Where);
        return Actor;
    }
    APawn *Pawn(const FVector &Where)
    {
        auto *Actor = World->SpawnActor<APawn>();
        auto *Body = NewObject<UCapsuleComponent>(Actor);
        Actor->SetRootComponent(Body);
        Actor->AddInstanceComponent(Body);
        Body->InitCapsuleSize(42, 96);
        Body->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        Body->SetCollisionObjectType(ECC_Pawn);
        Body->SetCollisionResponseToAllChannels(ECR_Block);
        Body->RegisterComponent();
        Actor->SetActorLocation(Where);
        return Actor;
    }
};

void TickDoor(ASSOutpostDoor *Door, float Seconds)
{
    for (int32 Step = 0; Step < FMath::CeilToInt(Seconds * 60); ++Step)
        Door->Tick(1.f / 60);
}

UMaterial *PaintFixture()
{
    auto *Material = NewObject<UMaterial>(GetTransientPackage());
    auto *Parameter = NewObject<UMaterialExpressionVectorParameter>(Material);
    Parameter->ParameterName = TEXT("HullTint");
    Parameter->DefaultValue = FLinearColor::White;
    Material->GetExpressionCollection().AddExpression(Parameter);
    Material->GetEditorOnlyData()->BaseColor.Expression = Parameter;
    Material->UpdateCachedExpressionData();
    return Material;
}
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSOutpostDoorSafety, "SpaceSurvival.Outpost.DoorSafety",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSOutpostDoorSafety::RunTest(const FString &)
{
    FSSOutpostTestWorld Rig;
    if (!Rig.Initialize(*this))
        return false;
    auto *Door = Rig.World->SpawnActor<ASSOutpostDoor>();
    auto *Visitor = Rig.Pawn(FVector(-300, 0, 98));
    FCollisionQueryParams Query(SCENE_QUERY_STAT(OutpostDoorTest), false, Visitor);
    const auto PassageBlocked = [&]()
    {
        FHitResult Hit;
        return Rig.World->SweepSingleByChannel(Hit, FVector(-170, 0, 98), FVector(170, 0, 98), FQuat::Identity,
                                               ECC_Pawn, FCollisionShape::MakeCapsule(42, 96), Query);
    };
    TestTrue(TEXT("Closed leaves physically block the walking capsule"), PassageBlocked());
    TickDoor(Door, 1.2f);
    TestTrue(TEXT("Approaching pawn opens the sensor door"), Door->OpenFraction > .99f);
    TestFalse(TEXT("Fully open leaves clear the actual walking capsule"), PassageBlocked());

    Visitor->SetActorLocation(FVector(0, 0, 98));
    TickDoor(Door, 3.f);
    TestTrue(TEXT("A visitor in the doorway keeps it open past the hold timer"), Door->OpenFraction > .99f);
    Visitor->SetActorLocation(FVector(-2000, 0, 98));
    auto *Crate = Rig.Box(FVector(0, 275, 150), FVector(20, 20, 30), ECC_PhysicsBody);
    TestTrue(TEXT("A crate in the leaf travel pocket counts as occupied"), Door->IsDoorwayOccupied());
    TickDoor(Door, 3.5f);
    TestTrue(TEXT("Door does not close through the occupied leaf pocket"), Door->OpenFraction > .99f);
    Crate->SetActorLocation(FVector(2000, 2000, 150));
    TickDoor(Door, 3.5f);
    TestTrue(TEXT("Door closes after the opening and leaf pockets are empty"), Door->OpenFraction < .01f);
    TestTrue(TEXT("Closed door restores its blocking collision"), PassageBlocked());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSOutpostTerminalPaint, "SpaceSurvival.Outpost.TerminalPaint",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSOutpostTerminalPaint::RunTest(const FString &)
{
    FSSOutpostTestWorld Rig;
    if (!Rig.Initialize(*this))
        return false;
    auto *Console = Rig.World->SpawnActor<ASSOutpostTerminal>(FVector(0, 0, 100), FRotator::ZeroRotator);
    auto *User = Rig.Pawn(FVector(-200, 0, 100));
    auto *Controller = Rig.World->SpawnActor<APlayerController>();
    Controller->Possess(User);
    Console->Action = ESSOutpostAction::CycleShipPaint;
    auto *Ship = Rig.World->SpawnActor<AActor>();
    Console->PresentationTarget = Ship;
    auto *Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (!TestNotNull(TEXT("Engine fixture cube exists"), Cube))
        return false;
    auto *FactoryMaterial = PaintFixture();
    const auto Panel = [&](const TCHAR *Name, bool Paintable)
    {
        auto *Component = NewObject<UStaticMeshComponent>(Ship, Name);
        Ship->AddInstanceComponent(Component);
        if (!Ship->GetRootComponent())
            Ship->SetRootComponent(Component);
        else
            Component->SetupAttachment(Ship->GetRootComponent());
        Component->SetStaticMesh(Cube);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetMaterial(0, FactoryMaterial);
        if (Paintable)
            Component->ComponentTags.Add(Console->PaintComponentTag);
        Component->RegisterComponent();
        return Component;
    };
    auto *Hull = Panel(TEXT("Hull"), true);
    auto *Glass = Panel(TEXT("UntouchedGlass"), false);
    TestTrue(TEXT("Nearby unobstructed user can reach console"), Console->CanUse(User));
    User->SetActorLocation(FVector(-1000, 0, 100));
    Console->Use(Controller);
    TestFalse(TEXT("Range is rechecked by use"), Console->CanUse(User));
    TestTrue(TEXT("Out-of-range use leaves the original hull material untouched"),
             Hull->GetMaterial(0) == FactoryMaterial);

    User->SetActorLocation(FVector(-200, 0, 100));
    auto *Wall = Rig.Box(FVector(-100, 0, 125), FVector(10, 120, 125), ECC_WorldStatic);
    TestFalse(TEXT("An opaque wall blocks a nearby console"), Console->CanUse(User));
    Console->Use(Controller);
    TestTrue(TEXT("Occluded use cannot repaint through a wall"), Hull->GetMaterial(0) == FactoryMaterial);
    Wall->SetActorLocation(FVector(0, 2000, 125));
    Console->Use(Controller);
    auto *Tint = Cast<UMaterialInstanceDynamic>(Hull->GetMaterial(0));
    if (!TestNotNull(TEXT("Authorized paint creates a private dynamic instance"), Tint))
        return false;
    TestTrue(TEXT("Only the tagged hull receives the selected paint color"),
             Tint->K2_GetVectorParameterValue(Console->PaintParameter).Equals(Console->PaintPalette[0]));
    TestTrue(TEXT("Untagged glazing keeps the exact factory material"), Glass->GetMaterial(0) == FactoryMaterial);
    Console->Use(Controller);
    TestTrue(TEXT("Second use advances the palette on that same hull instance"),
             Hull->GetMaterial(0) == Tint &&
                 Tint->K2_GetVectorParameterValue(Console->PaintParameter).Equals(Console->PaintPalette[1]));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSOutpostCrewSupport, "SpaceSurvival.Outpost.CrewSupport",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSOutpostCrewSupport::RunTest(const FString &)
{
    FSSOutpostTestWorld Rig;
    if (!Rig.Initialize(*this))
        return false;
    Rig.Box(FVector(0, 0, -10), FVector(200, 150, 10), ECC_WorldStatic);
    auto *Crew = Rig.World->SpawnActor<ASSOutpostAmbientActor>(FVector(0, 0, 87), FRotator::ZeroRotator);
    Crew->RoutePoints = {FVector::ZeroVector, FVector(500, 0, 0)};
    Crew->PauseAtWaypoint = 0.f;
    Crew->TravelSpeed = 120.f;
    float MaxX = 0.f, MaxGroundError = 0.f;
    for (int32 Step = 0; Step < 300; ++Step)
    {
        Crew->Tick(1.f / 60);
        MaxX = FMath::Max(MaxX, float(Crew->GetActorLocation().X));
        MaxGroundError = FMath::Max(MaxGroundError, FMath::Abs(float(Crew->GetActorLocation().Z) - 87.f));
    }
    TestTrue(TEXT("Crew actually walks along the supported part of its route"), MaxX > 100.f);
    TestTrue(TEXT("Crew refuses an authored waypoint beyond the supporting deck"), MaxX <= 200.1f);
    TestTrue(TEXT("Grounded crew remains at capsule height instead of floating or falling"), MaxGroundError < 1.f);

    // Another crew capsule below an unsupported route must not become a substitute floor.
    // Its top is at deck height, outside the real deck's Y extent, and clear of the walking capsule.
    auto *LowerCrew = Rig.World->SpawnActor<ASSOutpostAmbientActor>(FVector(0, 600, -85), FRotator::ZeroRotator);
    auto *Unsupported = Rig.World->SpawnActor<ASSOutpostAmbientActor>(FVector(0, 600, 87), FRotator::ZeroRotator);
    Unsupported->RoutePoints = {FVector::ZeroVector, FVector(100, 0, 0)};
    Unsupported->PauseAtWaypoint = 0.f;
    Unsupported->TravelSpeed = 120.f;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(OutpostCrewSupportTest), false, Unsupported);
    FHitResult ResponseHit;
    TestTrue(TEXT("Negative fixture exposes the other crew to the old response-channel floor trace"),
             Rig.World->LineTraceSingleByChannel(ResponseHit, FVector(2, 600, 157), FVector(2, 600, -173),
                                                 ECC_WorldStatic, Query) &&
                 ResponseHit.GetActor() == LowerCrew);
    float MaxUnsupportedTravel = 0.f;
    for (int32 Step = 0; Step < 90; ++Step)
    {
        Unsupported->Tick(1.f / 60);
        MaxUnsupportedTravel = FMath::Max(MaxUnsupportedTravel,
                                          float(FVector::Dist(Unsupported->GetActorLocation(), FVector(0, 600, 87))));
    }
    TestTrue(TEXT("Another crew capsule cannot support movement into a route with no static deck"),
             MaxUnsupportedTravel < .1f);
    return true;
}
#endif
