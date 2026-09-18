#include "Misc/AutomationTest.h"
#include "SSShip.h"
#include "Misc/PackageName.h"
#include "SSStation.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSExteriorTestWorld
{
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    FSSExteriorTestWorld()
    {
        if (World)
            GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    }
    ~FSSExteriorTestWorld()
    {
        if (World)
        {
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
        }
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSStationExteriorCollision, "SpaceSurvival.Integration.StationExteriorCollision",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSStationExteriorCollision::RunTest(const FString &)
{
    const TCHAR *PitStop = TEXT("/Game/SpaceSurvival/Licensed/StationPitStop/SM_StationPitStop");
    if (FPackageName::DoesPackageExist(PitStop))
    {
        // The pit stop body sits at the station origin with no collision of its own; its solids are the generated
        // boxes, invisible and blocking, and none of them reaches into the hangar or the approach lane.
        for (bool Home : {false, true})
        {
            FSSExteriorTestWorld Fixture;
            if (!TestNotNull(TEXT("Create isolated pit stop collision world"), Fixture.World))
                return false;
            auto *Hub = Fixture.World->SpawnActor<ASSStation>(FVector(16000, -8000, 5000), FRotator(0, 75, 0));
            if (!TestNotNull(TEXT("Spawn transformed actual station"), Hub))
                return false;
            Hub->bUseEditableLayout = false;
            Hub->BuildHub(Home);
            TInlineComponentArray<UStaticMeshComponent *> Components;
            Hub->GetComponents(Components);
            int32 Bodies = 0, Solids = 0, Intrusions = 0;
            for (auto *Component : Components)
            {
                if (!Component->GetStaticMesh() || Cast<UInstancedStaticMeshComponent>(Component))
                    continue;
                if (Component->GetStaticMesh()->GetPathName().StartsWith(PitStop))
                {
                    ++Bodies;
                    TestTrue(TEXT("Pit stop body sits at the origin, unrotated, without collision or shadow"),
                             Component->GetRelativeTransform().Equals(FTransform::Identity, .001) &&
                                 Component->GetCollisionEnabled() == ECollisionEnabled::NoCollision &&
                                 !Component->CastShadow);
                }
                if (!Component->ComponentHasTag(TEXT("StationPitStopSolid")))
                    continue;
                ++Solids;
                TestTrue(TEXT("Pit stop solid is an invisible WorldStatic blocker"),
                         !Component->IsVisible() && !Component->CastShadow &&
                             Component->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics &&
                             Component->GetCollisionObjectType() == ECC_WorldStatic &&
                             Component->GetCollisionResponseToChannel(ECC_Pawn) == ECR_Block);
                const FVector Centre = Component->GetRelativeLocation();
                const FVector Half = Component->GetRelativeScale3D() * 50.f; // the engine cube is 100 cm
                const FBox Box(Centre - Half, Centre + Half);
                // Strictly inside: the bow plate and lintel touch these volumes on their faces by design.
                const FBox Interior(FVector(-1700, -1400, -60), FVector(1715, 1400, 1000));
                const FBox Lane(FVector(-20000, -700, -10), FVector(-1700, 700, 967.5));
                auto Overlaps = [&Box](const FBox &Volume)
                {
                    return Box.Min.X < Volume.Max.X && Box.Max.X > Volume.Min.X && Box.Min.Y < Volume.Max.Y &&
                           Box.Max.Y > Volume.Min.Y && Box.Min.Z < Volume.Max.Z && Box.Max.Z > Volume.Min.Z;
                };
                Intrusions += Overlaps(Interior) || Overlaps(Lane) ? 1 : 0;
            }
#include "SSStationPitStopBoxes.inl"
            TestEqual(TEXT("One pit stop body"), Bodies, 1);
            TestEqual(TEXT("Every generated box is placed"), Solids,
                      static_cast<int32>(UE_ARRAY_COUNT(SSStationPitStopBoxes)));
            TestEqual(TEXT("No pit stop solid reaches into the hangar or the approach lane"), Intrusions, 0);
        }
        return true;
    }
    const TCHAR *Package = TEXT("/Game/SpaceSurvival/Licensed/StationExterior/SM_StationExterior");
    if (!FPackageName::DoesPackageExist(Package))
    {
        AddInfo(
            TEXT("SKIPPED licensed exterior checks: optional private asset is not installed. "
                 "This run does not verify exterior collision; fallback coverage is in StationPresentationCollision."));
        return true;
    }
    for (bool Home : {false, true})
    {
        FSSExteriorTestWorld Fixture;
        if (!TestNotNull(TEXT("Create isolated exterior collision world"), Fixture.World))
            return false;
        auto *Hub = Fixture.World->SpawnActor<ASSStation>(FVector(16000, -8000, 5000), FRotator(0, 75, 0));
        if (!TestNotNull(TEXT("Spawn transformed actual station"), Hub))
            return false;
        Hub->bUseEditableLayout = false; // Native exterior fallback; editable layout has separate coverage.
        Hub->BuildHub(Home);
        TInlineComponentArray<UStaticMeshComponent *> Components;
        Hub->GetComponents(Components);
        UStaticMeshComponent *Exterior = nullptr;
        UStaticMeshComponent *Proxy = nullptr;
        int32 ExteriorCount = 0, ProxyCount = 0;
        for (auto *Component : Components)
        {
            if (!Component->GetStaticMesh() || Cast<UInstancedStaticMeshComponent>(Component))
                continue;
            if (Component->GetStaticMesh()->GetPathName().StartsWith(Package))
            {
                Exterior = Component;
                ++ExteriorCount;
            }
            if (Component->GetRelativeLocation().Equals(FVector(7000, 0, 3500), .01) &&
                Component->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics)
            {
                Proxy = Component;
                ++ProxyCount;
            }
        }
        TestEqual(TEXT("One real exterior presentation mesh"), ExteriorCount, 1);
        TestEqual(TEXT("One dedicated exterior collision proxy"), ProxyCount, 1);
        if (!TestNotNull(TEXT("Exterior asset resolved without fallback"), Exterior) ||
            !TestNotNull(TEXT("Exterior collision exists"), Proxy))
            return false;
        const FBox VisualBounds = Exterior->GetStaticMesh()->GetBoundingBox().TransformBy(
            Exterior->GetRelativeTransform().ToMatrixWithScale());
        const FBox ProxyBounds =
            Proxy->GetStaticMesh()->GetBoundingBox().TransformBy(Proxy->GetRelativeTransform().ToMatrixWithScale());
        TestTrue(TEXT("Actual exterior and collision both stay beyond the bay rear boundary"),
                 VisualBounds.Min.X > 1715 && ProxyBounds.Min.X > 1715);
        TestTrue(TEXT("Proxy encloses actual imported mesh bounds including its rotated axes"),
                 ProxyBounds.ExpandBy(.1).IsInsideOrOn(VisualBounds.Min) &&
                     ProxyBounds.ExpandBy(.1).IsInsideOrOn(VisualBounds.Max));
        TestTrue(TEXT("Invisible proxy blocks every channel as WorldStatic"),
                 !Proxy->IsVisible() && !Proxy->CastShadow && Proxy->GetCollisionObjectType() == ECC_WorldStatic &&
                     Proxy->GetCollisionResponseToChannels() == FCollisionResponseContainer(ECR_Block));
        const auto Transform = Hub->GetActorTransform();
        auto WorldPoint = [&Transform](FVector Point) { return Transform.TransformPosition(Point); };
        FCollisionObjectQueryParams Objects(ECC_WorldStatic);
        FCollisionQueryParams Query(SCENE_QUERY_STAT(SSStationExteriorCollision), false);
        for (FVector Start : {FVector(3000, 0, 3500), FVector(7000, -6000, 3500), FVector(7000, 6000, 3500),
                              FVector(7000, 0, 8000), FVector(7000, 0, -1000)})
        {
            FHitResult Hit;
            TestTrue(TEXT("Exterior is physically solid from front, sides, above and below"),
                     Fixture.World->LineTraceSingleByObjectType(Hit, WorldPoint(Start),
                                                                WorldPoint(FVector(7000, 0, 3500)), Objects, Query) &&
                         Hit.GetComponent() == Proxy);
        }
        FHitResult Hit;
        TestFalse(TEXT("Added exterior leaves the existing inbound ship envelope clear"),
                  Fixture.World->SweepSingleByObjectType(
                      Hit, Hub->DockPosition() - Hub->GetActorForwardVector() * 3000.f,
                      Hub->DockPosition() - Hub->GetActorForwardVector() * 1250.f, FQuat::Identity, Objects,
                      FCollisionShape::MakeSphere(ASSShip::FlightCollisionRadius()), Query));
    }
    return true;
}
#endif
