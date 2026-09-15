#include "SSSpaceScenery.h"
#include "SSSpaceLookData.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
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
    TInlineComponentArray<UStaticMeshComponent *> Structures;
    Fixture.Scenery->GetComponents(Structures);
    if (!TestTrue(TEXT("Authored scenery actually builds visible geometry"), !Structures.IsEmpty()))
        return false;
    TestFalse(TEXT("The scenery actor itself has no gameplay collision"), Fixture.Scenery->GetActorEnableCollision());
    for (auto *Part : Structures)
    {
        TestTrue(TEXT("Every decorative part belongs to its registered scenery actor"),
                 Part->IsRegistered() && Part->GetOwner() == Fixture.Scenery &&
                     Part->GetAttachParent() == Fixture.Scenery->GetRootComponent());
        TestEqual(TEXT("Decorative structures have no collision"), Part->GetCollisionEnabled(),
                  ECollisionEnabled::NoCollision);
        TestFalse(TEXT("Decorative structures generate no overlaps"), Part->GetGenerateOverlapEvents());
        TestFalse(TEXT("Decorative structures are excluded from navigation"), Part->CanEverAffectNavigation());
        TestFalse(TEXT("Distant structures add no shadow rendering work"), Part->CastShadow);
        if (!TestNotNull(TEXT("Decorative structures resolve their imported meshes"), Part->GetStaticMesh().Get()))
            return false;
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
#endif
