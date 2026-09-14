#include "SSAsteroidBurst.h"
#include "SSWorldActors.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSAsteroidBreakup, "SpaceSurvival.Presentation.AsteroidBreakup",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSAsteroidBreakup::RunTest(const FString &)
{
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Isolated breakup world"), World))
        return false;
    GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    auto Count = [&]()
    {
        int32 Result = 0;
        for (TActorIterator<ASSAsteroidBurst> It(World); It; ++It)
            Result += !It->IsActorBeingDestroyed();
        return Result;
    };
    for (ESSWorldKind Kind : {ESSWorldKind::SmallAsteroid, ESSWorldKind::MediumAsteroid})
    {
        auto *Rock = World->SpawnActor<ASSWorldBody>(FVector(1000, 0, 0), FRotator::ZeroRotator);
        Rock->Configure(Kind, 150.f, 0.f);
        Rock->SetLinearVelocity(FVector(100, 20, 0));
        const int32 Before = Count();
        Rock->ReceiveWeaponHit(100000.f);
        TestEqual(TEXT("Defeating a destructible rock emits one burst"), Count(), Before + 1);
        Rock->ReceiveWeaponHit(100000.f);
        TestEqual(TEXT("Repeated defeat callback cannot duplicate the burst"), Count(), Before + 1);
    }
    ASSAsteroidBurst *Sample = nullptr;
    for (TActorIterator<ASSAsteroidBurst> It(World); It; ++It)
        if (!It->IsActorBeingDestroyed())
        {
            Sample = *It;
            break;
        }
    if (TestNotNull(TEXT("Actual burst exists"), Sample))
    {
        TestFalse(TEXT("Cosmetic burst cannot be a world-body weapon target"),
                  Sample->IsA(ASSWorldBody::StaticClass()));
        TestFalse(TEXT("Burst actor collision disabled"), Sample->GetActorEnableCollision());
        TestTrue(TEXT("Chips collision disabled"),
                 Sample->Chips->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
        TestFalse(TEXT("Chips generate no overlaps"), Sample->Chips->GetGenerateOverlapEvents());
        TestEqual(TEXT("One burst has twelve actual instances"), Sample->Chips->GetInstanceCount(), 12);
        FTransform Before, After;
        Sample->Chips->GetInstanceTransform(0, Before);
        const FVector Origin = Sample->GetActorLocation();
        Sample->Tick(.5f);
        Sample->Chips->GetInstanceTransform(0, After);
        TestTrue(TEXT("Burst inherits actual asteroid drift"),
                 Sample->GetActorLocation().Equals(Origin + FVector(50, 10, 0), .01));
        const FVector MeshOrigin = Sample->Chips->GetStaticMesh()->GetBounds().Origin;
        TestTrue(TEXT("Chips spread outward from the breakup"),
                 After.TransformPosition(MeshOrigin).Size() > Before.TransformPosition(MeshOrigin).Size());
        TestTrue(TEXT("Opaque chips shrink during their fade interval"), After.GetScale3D().X < Before.GetScale3D().X);
    }
    for (int32 Index = 0; Index < 20; ++Index)
        ASSAsteroidBurst::SpawnBurst(World, FVector(Index * 100, 0, 0), FVector::ZeroVector, 150.f);
    TestEqual(TEXT("Burst admission caps simultaneous actors at eight"), Count(), 8);
    TestNull(TEXT("Cap rejects additional burst without replacing active ones"),
             ASSAsteroidBurst::SpawnBurst(World, FVector::ZeroVector, FVector::ZeroVector, 100.f));
    TArray<ASSAsteroidBurst *> Bursts;
    for (TActorIterator<ASSAsteroidBurst> It(World); It; ++It)
        Bursts.Add(*It);
    for (auto *Burst : Bursts)
        Burst->Tick(1.f);
    TestEqual(TEXT("Every burst retires within one second"), Count(), 0);
    TestNotNull(TEXT("Expired bursts release capacity"),
                ASSAsteroidBurst::SpawnBurst(World, FVector::ZeroVector, FVector::ZeroVector, 100.f));
    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}
#endif
