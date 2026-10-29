#include "SSGameInstance.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSSpaceLookData.h"
#include "SSSpaceScenery.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/IConsoleManager.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSceneryReservedRoute, "SpaceSurvival.Flight.SceneryReservedRoute",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSSceneryReservedRoute::RunTest(const FString &)
{
    auto *Preview = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.SpaceAreaPreview"));
    auto *Variation = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.SpaceAreaVariation"));
    if (!TestNotNull(TEXT("Area preview"), Preview) || !TestNotNull(TEXT("Area variation"), Variation))
        return false;
    const int32 OldPreview = Preview->GetInt(), OldVariation = Variation->GetInt();
    const auto PreviewPriority = EConsoleVariableFlags(Preview->GetFlags() & ECVF_SetByMask);
    const auto VariationPriority = EConsoleVariableFlags(Variation->GetFlags() & ECVF_SetByMask);
    ON_SCOPE_EXIT
    {
        Preview->Set(OldPreview, PreviewPriority);
        Variation->Set(OldVariation, VariationPriority);
    };
    Preview->Set(0, PreviewPriority);
    Variation->Set(0, VariationPriority);
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Create isolated admission world"), World))
        return false;
    auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    auto *Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
    Instance->AddToRoot();
    Instance->AccountStorageBlocked = true;
    Instance->Session.settings.masterVolume = 0;
    Context.OwningGameInstance = Instance;
    World->SetGameInstance(Instance);
    ON_SCOPE_EXIT
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        Instance->RemoveFromRoot();
    };
    World->GetWorldSettings()->DefaultGameMode = AGameModeBase::StaticClass();
    if (!TestTrue(TEXT("Stock mode without production actors or saves"), World->SetGameMode(FURL())))
        return false;
    auto *Ship = World->SpawnActor<ASSShip>(FVector::ZeroVector, FRotator(0, 45, 0));
    auto *Viewer = World->SpawnActor<AActor>();
    auto *Baseline = World->SpawnActor<ASSSpaceScenery>();
    auto *Filtered = World->SpawnActor<ASSSpaceScenery>();
    if (!TestNotNull(TEXT("Real route owner"), Ship) || !TestNotNull(TEXT("Unrestricted reference viewer"), Viewer) ||
        !TestNotNull(TEXT("Reference scenery"), Baseline) || !TestNotNull(TEXT("Reserved scenery"), Filtered))
        return false;
    Ship->Tuning = NewObject<USSPhase1Data>(Ship);
    if (!TestTrue(TEXT("In-memory run"), Instance->Session.StartRun("scenery-route")))
        return false;
    Ship->Tick(0);
    const FQuat Route = Ship->GetReservedWaveRouteFrame();
    const FVector Origin = Ship->GetReservedWaveRouteOrigin();
    auto *Mesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (!TestNotNull(TEXT("Engine geometry needs no licensed assets"), Mesh))
        return false;
    auto *Look = NewObject<USSSpaceLookData>();
    Look->AreaClutterBudget = 768;
    Look->AreaRecipes.SetNum(1);
    auto &Recipe = Look->AreaRecipes[0];
    Recipe.ClutterDensity = 2;
    Recipe.ClusterAxes = FVector::ZeroVector;
    FSSSceneryCandidate Candidate;
    Candidate.Mesh = Mesh;
    Candidate.MinRadius = 1200;
    Candidate.MaxRadius = 3200;
    Recipe.Clutter.Add(Candidate);
    for (int32 Index = 0; Index < 2; ++Index)
    {
        FSSSceneryPlacement Placement;
        Placement.Mesh = Mesh;
        Placement.Center = Route.RotateVector(FVector(100000, Index * 50000, 0));
        Placement.Radius = 2500;
        Recipe.Landmarks.Add(Placement);
    }
    Baseline->ConfigureLook(Look);
    Baseline->Follow(Viewer);
    Filtered->ConfigureLook(Look);
    Filtered->Follow(Ship);
    TestEqual(TEXT("Reference retains the two-part authored group"), Baseline->GetResidentLandmarkCount(), 2);
    TestEqual(TEXT("One blocking member rejects its complete group"), Filtered->GetResidentLandmarkCount(), 0);
    TestTrue(TEXT("Route admission removes blocking clutter but retains the side field"),
             Filtered->GetResidentClutterCount() > 0 &&
                 Filtered->GetResidentClutterCount() < Baseline->GetResidentClutterCount());
    auto Snapshot = [&](ASSSpaceScenery *Scenery, FVector RemoveOffset = FVector::ZeroVector)
    {
        TArray<FString> Result;
        TInlineComponentArray<UStaticMeshComponent *> Parts;
        Scenery->GetComponents(Parts);
        for (auto *Part : Parts)
        {
            if (auto *Batch = Cast<UInstancedStaticMeshComponent>(Part))
            {
                for (int32 Index = 0; Index < Batch->GetInstanceCount(); ++Index)
                {
                    FTransform Pose;
                    Batch->GetInstanceTransform(Index, Pose, true);
                    Pose.AddToTranslation(-RemoveOffset);
                    Result.Add(Pose.ToString());
                    if (Scenery == Filtered)
                    {
                        const FBox Hull = Ship->FlightHullBounds(
                            FTransform(FQuat::Identity, FVector::ZeroVector, Ship->GetActorScale3D()));
                        const double Radius = Mesh->GetBounds().SphereRadius * Pose.GetScale3D().GetAbsMax() +
                                              Hull.GetCenter().Size() + Hull.GetExtent().Size() + 1000;
                        const FVector Local =
                            Route.UnrotateVector(Pose.TransformPosition(Mesh->GetBounds().Origin) - Origin);
                        const FVector2D Limits = Ship->GetWaveCorridorHalfExtents();
                        const FVector Closest(Local.X, FMath::Clamp(Local.Y, -Limits.X, Limits.X),
                                              FMath::Clamp(Local.Z, -Limits.Y, Limits.Y));
                        TestTrue(TEXT("Every retained sphere clears all drift positions and rolled hulls"),
                                 FVector::Dist(Local, Closest) >= Radius - .1);
                    }
                }
            }
        }
        Result.Sort();
        return Result;
    };
    const auto Original = Snapshot(Baseline);
    const auto Initial = Snapshot(Filtered);
    for (const auto &Pose : Initial)
        TestTrue(TEXT("Accepted clutter preserves original deterministic pose"), Original.Contains(Pose));
    Ship->SetActorRotation(FRotator(55, 170, 120));
    Ship->SetActorLocation(FVector(1200, -2500, 3000));
    Instance->Session.run.active = false;
    Ship->Tick(0);
    Filtered->Tick(0);
    TestTrue(TEXT("Leaving waves and changing hull attitude does not alter visible scenery"),
             Initial == Snapshot(Filtered));
    Ship->SetActorLocation(FVector(2000000, 2000000, 2000000));
    Filtered->Tick(0);
    Ship->SetActorLocation(FVector::ZeroVector);
    Filtered->Tick(0);
    TestTrue(TEXT("Cell eviction and return retain the original reserved route and poses"),
             Initial == Snapshot(Filtered));
    const FVector Shift(-1000000, 1500000, -200000);
    Ship->ApplyWorldOffset(Shift, true);
    Filtered->ApplyWorldOffset(Shift, true);
    Filtered->Tick(0);
    TestTrue(TEXT("World-origin rebasing preserves scenery relative to the reserved route"),
             Initial == Snapshot(Filtered, Shift));
    return true;
}
#endif
