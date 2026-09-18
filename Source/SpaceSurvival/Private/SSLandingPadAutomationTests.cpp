#include "Misc/AutomationTest.h"
#include "SSLandingPad.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSLandingPadStandsAlone, "SpaceSurvival.Station.LandingPadStandsAlone",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSLandingPadStandsAlone::RunTest(const FString &)
{
    // The whole point of the pad being an actor is that it works with no station behind it, anywhere,
    // at any rotation. So this test has no station. It puts a pad at an awkward transform - far from the
    // origin, yawed, and not level with anything - and asks it the questions the docking sequence asks.
    auto *World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Create isolated landing pad world"), World))
        return false;
    GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    const FVector Where(-38000, 21000, -6500);
    const FRotator Facing(0, 137, 0);
    auto *Pad = World->SpawnActor<ASSLandingPad>(Where, Facing);
    if (!TestNotNull(TEXT("Spawn a pad on its own"), Pad))
        return false;
    TestFalse(TEXT("A pad is not built until somebody builds it"), Pad->IsBuilt());
    Pad->Build();
    TestTrue(TEXT("Build makes it real"), Pad->IsBuilt());
    Pad->Build();
    TInlineComponentArray<UStaticMeshComponent *> Meshes(Pad);
    TestEqual(TEXT("Building twice does not build twice: one deck, two kerbs, one indicator"), Meshes.Num(), 4);

    // The origin is the landing spot, by construction: the deck's top face is exactly there.
    TestTrue(TEXT("The deck point is the actor's own location"), Pad->DeckPoint().Equals(Where, .01));
    FCollisionObjectQueryParams StaticObjects(ECC_WorldStatic);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSLandingPadStandsAlone), false);
    FHitResult Hit;
    TestTrue(TEXT("There is a solid deck directly under the dock point, and it is this pad"),
             World->LineTraceSingleByObjectType(Hit, Pad->DockPoint(), Pad->DockPoint() - FVector(0, 0, 500),
                                                StaticObjects, Query) &&
                 Hit.GetActor() == Pad && Hit.ImpactPoint.Equals(Where, 1.f));
    TestTrue(TEXT("There is a solid deck under where the hero is set down"),
             World->LineTraceSingleByObjectType(Hit, Pad->WalkSpawn(), Pad->WalkSpawn() - FVector(0, 0, 500),
                                                StaticObjects, Query) &&
                 Hit.GetActor() == Pad);
    TestTrue(TEXT("There is a solid deck under the disembark point"),
             World->LineTraceSingleByObjectType(Hit, Pad->ExitPoint(), Pad->ExitPoint() - FVector(0, 0, 500),
                                                StaticObjects, Query) &&
                 Hit.GetActor() == Pad);
    // The dock clearance is the caller's number, applied along the pad's own up.
    TestTrue(TEXT("The default dock point is the classic hull's 230 cm above the deck"),
             FMath::IsNearlyEqual(float((Pad->DockPoint() - Pad->DeckPoint()).Z), 230.f, .01f));
    TestTrue(TEXT("A hull declares its own clearance and gets exactly that"),
             FMath::IsNearlyEqual(float((Pad->DockPoint(40.f) - Pad->DeckPoint()).Z), 40.f, .01f));

    // Coverage follows the pad's rotation, not the world's axes. A point 1500 along the pad's own X is on
    // it; the same 1500 along WORLD X, at a 137 degree yaw, is off the corner.
    const FTransform T = Pad->GetActorTransform();
    TestTrue(TEXT("The dock point, the walk spawn and the exit are all on the pad"),
             Pad->Covers(Pad->DockPoint()) && Pad->Covers(Pad->WalkSpawn()) && Pad->Covers(Pad->ExitPoint()));
    TestTrue(TEXT("The pad's own edge is on the pad"), Pad->Covers(T.TransformPosition(FVector(1500, 1500, 50))));
    TestFalse(TEXT("Past the kerb and the margin is off it"), Pad->Covers(T.TransformPosition(FVector(1800, 0, 50))));
    TestFalse(TEXT("Coverage is in the pad's frame, so world-axis offsets are not a shortcut"),
              Pad->Covers(Where + FVector(1500, 1500, 50)));
    TestFalse(TEXT("Far below the deck is not on it, so a fall is still a fall"),
              Pad->Covers(T.TransformPosition(FVector(0, 0, -300))));

    TestTrue(TEXT("The landing indicator starts lit, waiting for a ship"), Pad->IsIndicatorVisible());
    Pad->ShowIndicator(false);
    TestFalse(TEXT("And goes out when told the ship is down"), Pad->IsIndicatorVisible());

    Pad->Destroy();
    GEngine->DestroyWorldContext(World);
    World->DestroyWorld(false);
    return true;
}
#endif
