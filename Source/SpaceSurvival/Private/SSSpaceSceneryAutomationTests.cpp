#include "SSSpaceScenery.h"
#include "SSShip.h"
#include "SSSpaceLookData.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/IConsoleManager.h"
#include "Misc/AutomationTest.h"
#include "Misc/PackageName.h"
#include "Misc/ScopeExit.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
// Stock world: exercise actual BeginPlay without Session, Director, input or saves.
struct FSSSceneryWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    UGameInstance *Instance = nullptr;
    AActor *Viewer = nullptr;
    ASSSpaceScenery *Scenery = nullptr;

    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated scenery world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<UGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        GWorld = World;
        World->GetWorldSettings()->DefaultGameMode = AGameModeBase::StaticClass();
        if (!Test.TestTrue(TEXT("Install stock scenery fixture GameMode"), World->SetGameMode(FURL())))
            return false;
        World->InitializeActorsForPlay(FURL());
        Viewer = World->SpawnActor<AActor>();
        Scenery = World->SpawnActor<ASSSpaceScenery>();
        if (!Test.TestNotNull(TEXT("Spawn inert scenery viewer"), Viewer) ||
            !Test.TestNotNull(TEXT("Spawn actual scenery actor"), Scenery))
            return false;
        auto *Root = NewObject<USceneComponent>(Viewer);
        Viewer->SetRootComponent(Root);
        Root->RegisterComponent();
        Viewer->SetActorLocation(FVector(13000, -5000, 8000));
        World->BeginPlay();
        return Test.TestTrue(TEXT("Actual scenery BeginPlay completed"), Scenery->HasActorBegunPlay());
    }

    ~FSSSceneryWorld()
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSScenerySafety, "SpaceSurvival.Presentation.DistantStructureSafety",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSScenerySafety::RunTest(const FString &)
{
    const TCHAR *LookPath = TEXT("/Game/SpaceSurvival/Licensed/Atmosphere/DA_DeepSpaceLook");
    if (!FPackageName::DoesPackageExist(LookPath))
    {
        AddInfo(TEXT("SKIPPED distant-structure asset coverage: private look is not installed."));
        return true;
    }
    auto *Look = LoadObject<USSSpaceLookData>(nullptr, LookPath);
    if (!TestNotNull(TEXT("Installed look resolves its expected data class"), Look))
        return false;
    if (Look->StructureMeshes.IsEmpty())
    {
        AddInfo(TEXT("SKIPPED distant-structure geometry checks: this look has no authored structure meshes."));
        return true;
    }
    IConsoleVariable *Switch = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.SpaceStructures"));
    if (!TestNotNull(TEXT("Distant structure scalability control exists"), Switch))
        return false;
    const int32 Previous = Switch->GetInt();
    const EConsoleVariableFlags Priority = EConsoleVariableFlags(Switch->GetFlags() & ECVF_SetByMask);
    ON_SCOPE_EXIT
    {
        Switch->Set(Previous, Priority);
    };
    Switch->Set(1, Priority);
    FSSSceneryWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    // This test deliberately exercises backward compatibility, even when the installed look has regions.
    auto *LegacyLook = DuplicateObject<USSSpaceLookData>(Look, GetTransientPackage());
    LegacyLook->AreaRecipes.Reset();
    Fixture.Scenery->ConfigureLook(LegacyLook);
    TInlineComponentArray<UStaticMeshComponent *> Structures;
    Fixture.Scenery->GetComponents(Structures);
    if (!TestTrue(TEXT("Authored scenery actually builds visible geometry"), !Structures.IsEmpty()))
        return false;
    // Scenery used to be strictly decorative. It is now solid, because a rock large enough to fly into should
    // stop the ship rather than swallow it; actor-level collision gates the components, so it has to be on too.
    TestTrue(TEXT("The scenery actor allows its parts to be swept against"),
             Fixture.Scenery->GetActorEnableCollision());
    for (auto *Part : Structures)
    {
        TestTrue(TEXT("Every decorative part belongs to its registered scenery actor"),
                 Part->IsRegistered() && Part->GetOwner() == Fixture.Scenery &&
                     Part->GetAttachParent() == Fixture.Scenery->GetRootComponent());
        TestEqual(TEXT("Scenery participates in sweeps and Phoenix physics"), Part->GetCollisionEnabled(),
                  ECollisionEnabled::QueryAndPhysics);
        TestEqual(TEXT("Scenery answers as world static"), Part->GetCollisionObjectType(), ECC_WorldStatic);
        TestEqual(TEXT("Scenery blocks the Phoenix body"), Part->GetCollisionResponseToChannel(ECC_PhysicsBody),
                  ECR_Block);
        TestEqual(TEXT("Scenery blocks the ship"), Part->GetCollisionResponseToChannel(ECC_Pawn), ECR_Block);
        TestEqual(TEXT("Scenery blocks weapon and sight traces"), Part->GetCollisionResponseToChannel(ECC_Visibility),
                  ECR_Block);
        TestFalse(TEXT("Decorative structures generate no overlaps"), Part->GetGenerateOverlapEvents());
        TestFalse(TEXT("Decorative structures are excluded from navigation"), Part->CanEverAffectNavigation());
        TestFalse(TEXT("Distant structures add no shadow rendering work"), Part->CastShadow);
        if (!TestNotNull(TEXT("Decorative structures resolve their imported meshes"), Part->GetStaticMesh().Get()))
            return false;
    }
    // Settings alone prove nothing: a mesh with no simple collision is query-only and still unhittable. Sweep
    // the ship's own sphere radius through a real structure's bounds and require an actual blocking hit.
    {
        UStaticMeshComponent *Solid = nullptr;
        for (auto *Part : Structures)
            if (Part->GetStaticMesh() && Part->GetCollisionEnabled() != ECollisionEnabled::NoCollision &&
                Part->Bounds.SphereRadius > 1000.f)
            {
                Solid = Part;
                break;
            }
        if (TestNotNull(TEXT("A solid structure exists to sweep against"), Solid))
        {
            const FVector Centre = Solid->Bounds.Origin;
            const double Reach = Solid->Bounds.SphereRadius * 3.0;
            FHitResult Hit;
            FCollisionQueryParams Params;
            Params.AddIgnoredActor(Fixture.Viewer);
            const bool Blocked = Fixture.Scenery->GetWorld()->SweepSingleByChannel(
                Hit, Centre + FVector(Reach, 0, 0), Centre - FVector(Reach, 0, 0), FQuat::Identity, ECC_Visibility,
                FCollisionShape::MakeSphere(ASSShip::FlightCollisionRadius()), Params);
            TestTrue(TEXT("A sweep through a structure actually reports a blocking hit"), Blocked);
        }
    }
    TestTrue(TEXT("Scenery starts hidden without a viewer"), Fixture.Scenery->IsHidden());
    Fixture.Scenery->SetFlightVisible(true);
    Fixture.Scenery->Tick(0);
    TestTrue(TEXT("Flight state alone cannot expose unbound scenery"), Fixture.Scenery->IsHidden());
    Fixture.Scenery->Follow(Fixture.Viewer);
    Fixture.Scenery->Tick(0);
    TestFalse(TEXT("A valid flight viewer activates scenery"), Fixture.Scenery->IsHidden());

    auto RelativeCenters = [&]()
    {
        TArray<FVector> Result;
        for (auto *Part : Structures)
            Result.Add(Part->GetComponentTransform().TransformPosition(Part->GetStaticMesh()->GetBounds().Origin) -
                       Fixture.Viewer->GetActorLocation());
        return Result;
    };
    const TArray<FVector> Initial = RelativeCenters();
    Fixture.Viewer->AddActorWorldOffset(FVector(700, -400, 100));
    Fixture.Scenery->Tick(.05f);
    const TArray<FVector> BeforeShift = RelativeCenters();
    TestFalse(TEXT("Ordinary flight produces parallax rather than rigid camera attachment"),
              Initial[0].Equals(BeforeShift[0], .1));
    // A shift smaller than the teleport guard is deliberate: a stale LastCenter
    // would otherwise be hidden by that guard and escape this regression check.
    const FVector Shift(4500, -2200, 700);
    Fixture.Viewer->ApplyWorldOffset(Shift, true);
    Fixture.Scenery->ApplyWorldOffset(Shift, true);
    Fixture.Scenery->Tick(0);
    const TArray<FVector> AfterShift = RelativeCenters();
    for (int32 Index = 0; Index < Structures.Num(); ++Index)
        TestTrue(TEXT("World-origin rebasing preserves each structure's view-relative position"),
                 BeforeShift[Index].Equals(AfterShift[Index], .1));

    auto IsOutsidePlay = [&]()
    {
        for (auto *Part : Structures)
        {
            const FBoxSphereBounds Bounds = Part->GetStaticMesh()->GetBounds();
            const FTransform Transform = Part->GetComponentTransform();
            const double SurfaceDistance =
                FVector::Distance(Transform.TransformPosition(Bounds.Origin), Fixture.Viewer->GetActorLocation()) -
                Bounds.SphereRadius * Transform.GetScale3D().GetAbsMax();
            if (!FMath::IsFinite(SurfaceDistance) || SurfaceDistance <= 80000.0)
                return false;
        }
        return true;
    };
    TestTrue(TEXT("Actual mesh surfaces start well beyond the playable field"), IsOutsidePlay());
    bool RemainedOutside = true;
    for (int32 Step = 0; Step < 120; ++Step)
    {
        Fixture.Viewer->AddActorWorldOffset(FVector(5000, 500, -200));
        Fixture.Scenery->Tick(.05f);
        RemainedOutside = RemainedOutside && IsOutsidePlay();
    }
    TestTrue(TEXT("Sustained flight cannot pull distant structures into gameplay"), RemainedOutside);
    Switch->Set(0, Priority);
    Fixture.Scenery->Tick(0);
    TestTrue(TEXT("Scalability disables scenery independently of flight"), Fixture.Scenery->IsHidden());
    Switch->Set(1, Priority);
    Fixture.Scenery->Tick(0);
    TestFalse(TEXT("Scalability can restore the same flight scenery"), Fixture.Scenery->IsHidden());
    Fixture.Scenery->SetFlightVisible(false);
    TestTrue(TEXT("Leaving flight hides scenery immediately"), Fixture.Scenery->IsHidden());
    Fixture.Scenery->SetFlightVisible(true);
    Fixture.Scenery->Follow(nullptr);
    Fixture.Scenery->Tick(0);
    TestTrue(TEXT("Losing the followed viewer hides scenery safely"), Fixture.Scenery->IsHidden());
    AddInfo(TEXT("Component and geometry safety only; no rendered readability or performance claim."));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSceneryRegions, "SpaceSurvival.Presentation.WorldStableAreaRecipes",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSSceneryRegions::RunTest(const FString &)
{
    auto *Preview = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.SpaceAreaPreview"));
    auto *Variation = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.SpaceAreaVariation"));
    auto *FarCount = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.DistantAsteroidCount"));
    if (!TestNotNull(TEXT("Area preview exists"), Preview) || !TestNotNull(TEXT("Area variation exists"), Variation) ||
        !TestNotNull(TEXT("Shared far-field budget exists"), FarCount))
        return false;
    const int32 OldPreview = Preview->GetInt(), OldVariation = Variation->GetInt(), OldFar = FarCount->GetInt();
    const auto PreviewPriority = EConsoleVariableFlags(Preview->GetFlags() & ECVF_SetByMask);
    const auto VariationPriority = EConsoleVariableFlags(Variation->GetFlags() & ECVF_SetByMask);
    const auto FarPriority = EConsoleVariableFlags(FarCount->GetFlags() & ECVF_SetByMask);
    ON_SCOPE_EXIT
    {
        Preview->Set(OldPreview, PreviewPriority);
        Variation->Set(OldVariation, VariationPriority);
        FarCount->Set(OldFar, FarPriority);
    };
    Preview->Set(0, PreviewPriority);
    Variation->Set(0, VariationPriority);
    FarCount->Set(2688, FarPriority);
    FSSSceneryWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    auto *Mesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (!TestNotNull(TEXT("Engine geometry makes coverage independent of licensed content"), Mesh))
        return false;
    auto *Look = NewObject<USSSpaceLookData>();
    Look->AreaClutterBudget = 768;
    Look->AreaRecipes.SetNum(3);
    for (int32 RecipeIndex = 0; RecipeIndex < 3; ++RecipeIndex)
    {
        auto &Recipe = Look->AreaRecipes[RecipeIndex];
        Recipe.Name = FName(*FString::Printf(TEXT("Fixture%d"), RecipeIndex));
        Recipe.ClutterDensity = 2.f;
        FSSSceneryCandidate Candidate;
        Candidate.Mesh = Mesh;
        Candidate.MinRadius = 1200;
        Candidate.MaxRadius = 3200;
        Recipe.Clutter.Add(Candidate);
        for (int32 Index = 0; Index < 8; ++Index)
        {
            FSSSceneryPlacement Placement;
            Placement.Mesh = Mesh;
            Placement.Center = FVector(90000 + 11000 * Index, Index % 2 ? 100000 : -100000, 10000 * RecipeIndex);
            Placement.Radius = 2500;
            Recipe.Landmarks.Add(Placement);
        }
    }
    Fixture.Viewer->SetActorLocation(FVector::ZeroVector);
    Fixture.Scenery->ConfigureLook(Look);
    Fixture.Scenery->Follow(Fixture.Viewer);
    Fixture.Scenery->SetFlightVisible(true);
    Fixture.Scenery->Tick(0);
    TestEqual(TEXT("All neighboring world cells resident"), Fixture.Scenery->GetResidentCellCount(), 27);
    TestTrue(TEXT("Local clutter exists and shares the 3072 total limit with 2688 far instances"),
             Fixture.Scenery->GetResidentClutterCount() > 0 && Fixture.Scenery->GetResidentClutterCount() <= 384);
    TestEqual(TEXT("Starting authored cell retains its entire eight-part group"),
              Fixture.Scenery->GetResidentLandmarkCount(), 8);
    auto Snapshot = [&](FVector RemoveOffset = FVector::ZeroVector)
    {
        TArray<FString> Result;
        TInlineComponentArray<UStaticMeshComponent *> Parts;
        Fixture.Scenery->GetComponents(Parts);
        for (auto *Part : Parts)
        {
            // Solid, but query-only: the field is swept against and never simulates.
            TestEqual(TEXT("World-stable scenery supports queries and physics"), Part->GetCollisionEnabled(),
                      ECollisionEnabled::QueryAndPhysics);
            TestEqual(TEXT("World-stable scenery blocks the ship"), Part->GetCollisionResponseToChannel(ECC_Pawn),
                      ECR_Block);
            TestFalse(TEXT("Scenery never modifies navigation"), Part->CanEverAffectNavigation());
            if (auto *Batch = Cast<UInstancedStaticMeshComponent>(Part))
            {
                TestFalse(TEXT("Clutter batches retain their bounded shadow-free cost"), Part->CastShadow);
                for (int32 Index = 0; Index < Batch->GetInstanceCount(); ++Index)
                {
                    FTransform Transform;
                    Batch->GetInstanceTransform(Index, Transform, true);
                    Transform.AddToTranslation(-RemoveOffset);
                    Result.Add(Transform.ToString());
                }
            }
            else
            {
                TestTrue(TEXT("Authored major forms cast shadows for depth"), Part->CastShadow);
                FTransform Transform = Part->GetComponentTransform();
                Transform.AddToTranslation(-RemoveOffset);
                Result.Add(Transform.ToString());
            }
        }
        Result.Sort();
        return Result;
    };
    const auto Initial = Snapshot();
    Fixture.Viewer->SetActorRotation(FRotator(65, 145, 30));
    Fixture.Viewer->AddActorWorldOffset(FVector(12000, -3000, 1700));
    Fixture.Scenery->Tick(.05f);
    TestTrue(TEXT("Turning and ordinary movement never drag, clear or reroll scenery"), Initial == Snapshot());
    Fixture.Viewer->SetActorLocation(FVector(500000, 500000, 500000));
    Fixture.Scenery->Tick(.05f);
    TestEqual(TEXT("Maximum eight complete authored groups remain within 64 landmarks"),
              Fixture.Scenery->GetResidentLandmarkCount(), 64);
    TestTrue(TEXT("Movement preserves the shared small/middle resident budget"),
             Fixture.Scenery->GetResidentClutterCount() <= 384);
    Fixture.Viewer->SetActorLocation(FVector::ZeroVector);
    Fixture.Scenery->Tick(.05f);
    TestTrue(TEXT("Revisiting regenerates exactly the same transforms, including unloaded neighbors"),
             Initial == Snapshot());
    const FVector Shift(12000, -3200, 700);
    Fixture.Viewer->ApplyWorldOffset(Shift, true);
    Fixture.Scenery->ApplyWorldOffset(Shift, true);
    Fixture.Scenery->Tick(0);
    TestTrue(TEXT("Rebase changes no logical cell or relative scene placement"), Initial == Snapshot(Shift));
    Preview->Set(2, PreviewPriority);
    Fixture.Scenery->Tick(0);
    TestEqual(TEXT("Explicit preview selects the requested recipe"), Fixture.Scenery->GetCurrentAreaIndex(), 2);
    TestFalse(TEXT("Different authored area actually changes geometry"), Initial == Snapshot(Shift));
    Preview->Set(0, PreviewPriority);
    Variation->Set(1, VariationPriority);
    Fixture.Scenery->Tick(0);
    TestFalse(TEXT("A second explicit variation produces a different region arrangement"), Initial == Snapshot(Shift));
    Variation->Set(0, VariationPriority);
    Fixture.Scenery->Tick(0);
    TestTrue(TEXT("Restoring variation reproduces the original recipe exactly"), Initial == Snapshot(Shift));
    Fixture.Scenery->SetRunSeed(101);
    Fixture.Scenery->Tick(0);
    TestTrue(TEXT("A fixed recipe preview ignores real run identity"), Initial == Snapshot(Shift));
    Preview->Set(-1, PreviewPriority);
    Fixture.Scenery->Tick(0);
    const auto FirstRun = Snapshot(Shift);
    Fixture.Scenery->SetRunSeed(202);
    Fixture.Scenery->Tick(0);
    TestFalse(TEXT("A different persistent run identity varies normal play"), FirstRun == Snapshot(Shift));
    Fixture.Scenery->SetRunSeed(101);
    Fixture.Scenery->Tick(0);
    TestTrue(TEXT("Restoring a run identity restores its complete arrangement"), FirstRun == Snapshot(Shift));
    // Taking the whole shared cap for the far field is exactly the condition the runtime now warns about,
    // because it silently starved the local clutter once. The warning is the expected observation here, not
    // an incident, so it is declared rather than left to fail the run.
    AddExpectedMessage(TEXT("Scenery clutter starved"), ELogVerbosity::Warning,
                       EAutomationExpectedMessageFlags::Contains, 0);
    FarCount->Set(3072, FarPriority);
    Fixture.Scenery->Tick(0);
    TestEqual(TEXT("Full far-field budget leaves no local clutter overspend"),
              Fixture.Scenery->GetResidentClutterCount(), 0);
    const auto Before = ASSSpaceScenery::SampleAreaStyle(Look, FVector(999999, 55000, -33000));
    const auto After = ASSSpaceScenery::SampleAreaStyle(Look, FVector(1000001, 55000, -33000));
    TestTrue(TEXT("Style blending is continuous across noise-cell seams"),
             FMath::Abs((Before.First + Before.Alpha) - (After.First + After.Alpha)) < .001f);
    Preview->Set(0, PreviewPriority);
    Look->AreaRecipes[0].Landmarks[0].Center = FVector::ZeroVector;
    Fixture.Scenery->ConfigureLook(Look);
    Fixture.Scenery->Tick(0);
    TestEqual(TEXT("A landmark violating the authored clearance rejects the entire group"),
              Fixture.Scenery->GetResidentLandmarkCount(), 0);
    Fixture.Scenery->ConfigureLook(nullptr);
    Fixture.Scenery->Tick(0);
    TestEqual(TEXT("Missing optional data leaves no stale resident cells"), Fixture.Scenery->GetResidentCellCount(), 0);
    TInlineComponentArray<UStaticMeshComponent *> EmptyParts;
    Fixture.Scenery->GetComponents(EmptyParts);
    TestEqual(TEXT("Source-only missing look cleanly omits licensed scenery"), EmptyParts.Num(), 0);
    AddInfo(TEXT("Deterministic state/budget coverage only; art quality, distant streaming visibility and performance "
                 "require gameplay review."));
    return true;
}
#endif
