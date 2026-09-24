#include "Misc/AutomationTest.h"
#include "SSLandingPad.h"
#include "SSStation.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"

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

    // Measured Phoenix hull at the docked transform: the previous centreline and -350 side exit both
    // fall inside this 2484 x 1244 footprint. Capsule clearance and floor support must be independent of
    // the small flight collision sphere, and must still hold on a rotated standalone pad.
    const FBox Phoenix(FVector(-1383.16, -623.92, 230.25), FVector(1100.84, 619.96, 935.05));
    TestTrue(TEXT("Measured Phoenix admits a supported exterior exit"),
             Pad->ConfigureWalkExit(Phoenix, 42.f, 96.f, nullptr));
    TestTrue(TEXT("Both standing and animated exits clear the complete rendered footprint"),
             Pad->IsOutsideParkedHull(Pad->WalkSpawn(), 42.f) && Pad->IsOutsideParkedHull(Pad->ExitPoint(), 42.f));
    TestTrue(TEXT("The selected exterior exit has the pad directly beneath it"),
             World->LineTraceSingleByObjectType(Hit, Pad->ExitPoint(), Pad->ExitPoint() - FVector(0, 0, 500),
                                                StaticObjects, Query) &&
                 Hit.GetActor() == Pad && FMath::IsNearlyEqual((Pad->ExitPoint() - Hit.ImpactPoint).Z, 98.5, .1));
    TestTrue(TEXT("Measured safe exit remains on the pad"), Pad->Covers(Pad->ExitPoint(), -42.f));
    TestFalse(TEXT("A hull covering the entire pad cannot claim a safe exit"),
              Pad->ConfigureWalkExit(FBox(FVector(-2000, -2000, 0), FVector(2000, 2000, 1000)), 42.f, 96.f, nullptr));

    TestTrue(TEXT("The landing indicator starts lit, waiting for a ship"), Pad->IsIndicatorVisible());
    Pad->ShowIndicator(false);
    TestFalse(TEXT("And goes out when told the ship is down"), Pad->IsIndicatorVisible());

    // The reset uses a real circular support surface and solid guardrails, with a deliberate open
    // bridge sector. Test physics independently of Covers so a square collider cannot pass as a disc.
    auto *Circle = World->SpawnActor<ASSLandingPad>(Where + FVector(0, 10000, 0), Facing);
    if (TestNotNull(TEXT("Spawn circular reset pad"), Circle))
    {
        Circle->bCircularDeck = true;
        Circle->Build();
        const FTransform CircleSpace = Circle->GetActorTransform();
        const auto At = [&CircleSpace](float X, float Y, float Z)
        { return CircleSpace.TransformPosition(FVector(X, Y, Z)); };
        TestTrue(TEXT("Circular pad supports its centre"),
                 World->LineTraceSingleByObjectType(Hit, At(0, 0, 100), At(0, 0, -500), StaticObjects, Query) &&
                     Hit.GetActor() == Circle);
        TestFalse(TEXT("Circular coverage excludes old square corners"), Circle->Covers(At(1500, 1500, 50)));
        TestFalse(
            TEXT("Circular physics excludes old square corners"),
            World->LineTraceSingleByObjectType(Hit, At(1500, 1500, 100), At(1500, 1500, -500), StaticObjects, Query));
        TestTrue(TEXT("A standing walking capsule is blocked by the visible side guardrail"),
                 World->SweepSingleByObjectType(Hit, At(0, 1450, 100), At(0, 1650, 100), CircleSpace.GetRotation(),
                                                StaticObjects, FCollisionShape::MakeCapsule(42.f, 96.f), Query) &&
                     Hit.GetComponent()->ComponentHasTag(TEXT("StationLandingKerb")));
        const float StepHeight = GetDefault<ASSWalker>()->GetCharacterMovement()->MaxStepHeight;
        TInlineComponentArray<UStaticMeshComponent *> CircleMeshes(Circle);
        for (const auto *Rail : CircleMeshes)
            if (Rail->ComponentHasTag(TEXT("StationLandingKerb")))
            {
                const FBox Bounds =
                    Rail->CalcBounds(Rail->GetComponentTransform().GetRelativeTransform(CircleSpace)).GetBox();
                TestTrue(TEXT("Every perimeter guard reaches 110cm and exceeds actual walker step height"),
                         FMath::IsNearlyEqual(Bounds.Min.Z, 0., .01) && FMath::IsNearlyEqual(Bounds.Max.Z, 110., .01) &&
                             Bounds.Max.Z > StepHeight);
                TestTrue(TEXT("Perimeter guards explicitly reject CharacterMovement step-up"),
                         Rail->CanCharacterStepUpOn == ECB_No);
            }
        TestFalse(TEXT("A standing capsule crosses the bridge opening without an invisible barrier"),
                  World->SweepSingleByObjectType(Hit, At(1200, 0, 100), At(1700, 0, 100), CircleSpace.GetRotation(),
                                                 StaticObjects, FCollisionShape::MakeCapsule(42.f, 96.f), Query));
        for (float Side : {-1.f, 1.f})
            for (float Degrees : {15.f, 18.f, 22.f, 26.f, 30.f})
            {
                const float Angle = FMath::DegreesToRadians(Degrees) * Side;
                const FVector Direction(FMath::Cos(Angle), FMath::Sin(Angle), 0);
                const FVector Start = CircleSpace.TransformPosition(Direction * 1200.f + FVector(0, 0, 100));
                const FVector End = CircleSpace.TransformPosition(Direction * 1900.f + FVector(0, 0, 100));
                TestTrue(FString::Printf(TEXT("Standing capsule cannot escape the bridge return at %.0f degrees"),
                                         Degrees * Side),
                         World->SweepSingleByObjectType(Hit, Start, End, CircleSpace.GetRotation(), StaticObjects,
                                                        FCollisionShape::MakeCapsule(42.f, 96.f), Query) &&
                             !Hit.bStartPenetrating && Hit.GetComponent()->ComponentHasTag(TEXT("StationLandingKerb")));
            }
        TestTrue(TEXT("Circular pad still provides a clear supported Phoenix exit"),
                 Circle->ConfigureWalkExit(Phoenix, 42.f, 96.f, nullptr));
        Circle->Destroy();
    }

    Pad->Destroy();
    GEngine->DestroyWorldContext(World);
    World->DestroyWorld(false);
    return true;
}
#endif
