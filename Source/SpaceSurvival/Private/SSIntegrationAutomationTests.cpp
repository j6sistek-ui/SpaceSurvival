#include "Misc/AutomationTest.h"
#include "Misc/PackageName.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "SSPhase1Data.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/PoseSnapshot.h"
#include "SSStationPoseTransition.h"
#include "Components/CapsuleComponent.h"
#include "Components/SphereComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSIsolatedTestWorld
{
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    FSSIsolatedTestWorld()
    {
        if (World)
            GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    }
    ~FSSIsolatedTestWorld()
    {
        if (World)
        {
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
        }
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSStationPresentationCollision,
                                 "SpaceSurvival.Integration.StationPresentationCollision",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSStationPresentationCollision::RunTest(const FString &)
{
    const TCHAR *ShellPath = TEXT("/Game/SpaceSurvival/Meshes/SM_StationShellCandidateV1.SM_StationShellCandidateV1");
    struct FLicensedBatch
    {
        const TCHAR *Mesh;
        int32 Instances;
    };
    const FLicensedBatch LicensedExpected[] = {{TEXT("SM_Celling_01"), 66}, {TEXT("SM_Crate"), 3},
                                               {TEXT("SM_Floor_01"), 102},  {TEXT("SM_LampCelling"), 10},
                                               {TEXT("SM_Monitor"), 5},     {TEXT("SM_MonitorScreen"), 5},
                                               {TEXT("SM_Top_Wall02"), 31}, {TEXT("SM_Wall_03"), 57}};
    bool LicensedAvailable = true;
    for (const auto &Expected : LicensedExpected)
        LicensedAvailable &=
            FPackageName::DoesPackageExist(FString(TEXT("/Game/SciFiCorridor/Meshes/")) + Expected.Mesh);
    if (!LicensedAvailable)
        AddInfo(TEXT("Licensed assets unavailable: default selection must use the actual legacy shell fallback."));
    struct FBoundary
    {
        FVector Position, Scale;
    };
    TArray<FBoundary> Boundaries = {{FVector(0, -1400, 170), FVector(34, .3f, 4.5f)},
                                    {FVector(0, 1400, 170), FVector(34, .3f, 4.5f)},
                                    {FVector(-1700, -1050, 350), FVector(.5f, 7, 8)},
                                    {FVector(-1700, 1050, 350), FVector(.5f, 7, 8)},
                                    {FVector(1700, 0, 100), FVector(.3f, 28, 2)}};
    for (float X : {-1200.f, -600.f, 0.f, 600.f, 1200.f})
        for (float Y : {-1400.f, 1400.f})
            Boundaries.Add({FVector(X, Y, 500), FVector(.5f, .5f, 10)});

    for (bool Home : {true, false})
        for (int32 Presentation : {0, 1, 2})
        {
            // Fresh actor/world per branch: BuildHub appends components. No GI Init or save APIs.
            FSSIsolatedTestWorld Fixture;
            if (!TestNotNull(TEXT("Create isolated station collision world"), Fixture.World))
                return false;
            auto *Hub = Fixture.World->SpawnActor<ASSStation>(FVector(16000, -8000, 5000), FRotator(0, 75, 0));
            if (!TestNotNull(TEXT("Create transformed station"), Hub))
                return false;
            // Default selection exercises installed licensed content or its real absence fallback.
            // Actor-local opt-out separately proves both legacy and bare presentation branches.
            Hub->bUseLicensedPresentation = Presentation == 0;
            const bool UseLicensed = Presentation == 0 && LicensedAvailable;
            const bool UseShell = Presentation != 2 && !UseLicensed;
            const bool HasPresentation = UseLicensed || UseShell;
            const FString Label = FString::Printf(TEXT("%s / %s"), Home ? TEXT("Home") : TEXT("Station"),
                                                  UseLicensed ? TEXT("licensed")
                                                  : UseShell  ? TEXT("shell")
                                                              : TEXT("fallback"));
            UStaticMesh *ExpectedShell = nullptr;
            if (UseShell)
            {
                TestEqual(Label + TEXT(" uses the reviewed default shell path"), Hub->ShellAsset.ToString(),
                          FString(ShellPath));
                ExpectedShell = Hub->ShellAsset.LoadSynchronous();
                if (!TestNotNull(Label + TEXT(" loads the actual candidate; no silent fallback pass"), ExpectedShell))
                    return false;
            }
            else
                Hub->ShellAsset.Reset(); // Actor-local seam; do not rename/delete any project asset.
            Hub->BuildHub(Home);
            TestEqual(Label + TEXT(" preserves hub context"), Hub->IsHome(), Home);

            TInlineComponentArray<UStaticMeshComponent *> Components;
            Hub->GetComponents(Components);
            TArray<UStaticMeshComponent *> SolidCubes;
            UStaticMeshComponent *Shell = nullptr, *Floor = nullptr;
            int32 ShellCount = 0;
            for (auto *Component : Components)
            {
                if (Component->GetFName() == TEXT("StationShell"))
                {
                    Shell = Component;
                    ++ShellCount;
                }
                if (Cast<UInstancedStaticMeshComponent>(Component) || !Component->GetStaticMesh() ||
                    Component->GetStaticMesh()->GetPathName() != TEXT("/Engine/BasicShapes/Cube.Cube") ||
                    Component->GetCollisionEnabled() != ECollisionEnabled::QueryAndPhysics)
                    continue;
                SolidCubes.Add(Component);
                if (Component->GetRelativeLocation().Equals(FVector(0, 0, -60), .001))
                    Floor = Component;
            }
            TestEqual(Label + TEXT(" creates a shell only when resolved"), ShellCount, UseShell ? 1 : 0);
            if (UseShell)
            {
                if (!TestNotNull(Label + TEXT(" exposes the shell component"), Shell))
                    return false;
                TestTrue(Label + TEXT(" keeps shell presentation out of collision, overlaps and navigation"),
                         Shell->GetStaticMesh() == ExpectedShell &&
                             Shell->GetAttachParent() == Hub->GetRootComponent() &&
                             Shell->GetRelativeTransform().Equals(FTransform::Identity, .001) &&
                             Shell->GetCollisionEnabled() == ECollisionEnabled::NoCollision &&
                             !Shell->GetGenerateOverlapEvents() && !Shell->CanEverAffectNavigation());
            }
            TestEqual(Label + TEXT(" keeps the deck plus all 15 physical boundary cubes"), SolidCubes.Num(), 16);
            if (!TestNotNull(Label + TEXT(" retains the solid deck"), Floor))
                return false;
            TestTrue(Label + TEXT(" keeps the deck visible at its original scale"),
                     Floor->IsVisible() && Floor->GetRelativeScale3D().Equals(FVector(34, 28, 1), .001));
            for (const FBoundary &Expected : Boundaries)
            {
                UStaticMeshComponent *Found = nullptr;
                int32 Matches = 0;
                for (auto *Cube : SolidCubes)
                    if (Cube->GetRelativeLocation().Equals(Expected.Position, .001))
                    {
                        Found = Cube;
                        ++Matches;
                    }
                TestEqual(Label + TEXT(" has one physical proxy at each original boundary"), Matches, 1);
                if (!TestNotNull(Label + TEXT(" retains each boundary proxy"), Found))
                    return false;
                // Compare every stored channel; ECC_MAX also includes a nonserialized sentinel.
                const bool BlocksAllChannels =
                    Found->GetCollisionResponseToChannels() == FCollisionResponseContainer(ECR_Block);
                TestTrue(Label + TEXT(" preserves boundary geometry and collision while changing only presentation"),
                         Found->GetRelativeScale3D().Equals(Expected.Scale, .001) &&
                             Found->GetRelativeRotation().IsNearlyZero(.001) &&
                             Found->GetCollisionObjectType() == ECC_WorldStatic && BlocksAllChannels &&
                             Found->IsVisible() == !HasPresentation && bool(Found->CastShadow) == !HasPresentation);
            }

            TInlineComponentArray<UInstancedStaticMeshComponent *> Batches;
            Hub->GetComponents(Batches);
            int32 LicensedBatchCount = 0;
            for (auto *Batch : Batches)
            {
                if (Batch->GetFName() == TEXT("TexturedDeckPanels"))
                    TestEqual(Label + TEXT(" hides duplicate floor only for licensed tiles"), Batch->IsVisible(),
                              !UseLicensed);
                if (!Batch->GetName().StartsWith(TEXT("LicensedStation_")))
                    continue;
                ++LicensedBatchCount;
                TestTrue(Label + TEXT(" licensed dressing has no collision, overlap or navigation"),
                         Batch->GetCollisionEnabled() == ECollisionEnabled::NoCollision &&
                             !Batch->GetGenerateOverlapEvents() && !Batch->CanEverAffectNavigation() &&
                             Batch->GetAttachParent() == Hub->GetRootComponent() &&
                             Batch->GetRelativeTransform().Equals(FTransform::Identity, .001));
                UStaticMesh *Mesh = Batch->GetStaticMesh();
                if (!TestNotNull(Label + TEXT(" licensed batch resolves its source mesh"), Mesh))
                    return false;
                bool Recognized = false;
                for (const auto &Expected : LicensedExpected)
                    if (Mesh->GetName() == Expected.Mesh)
                    {
                        Recognized = true;
                        TestEqual(Label + TEXT(" has measured instance count for ") + Expected.Mesh,
                                  Batch->GetInstanceCount(), Expected.Instances);
                    }
                TestTrue(Label + TEXT(" uses only reviewed licensed meshes"), Recognized);
                const auto &Materials = Mesh->GetStaticMaterials();
                TestTrue(Label + TEXT(" keeps source material slots"), Materials.Num() > 0);
                for (int32 Slot = 0; Slot < Materials.Num(); ++Slot)
                {
                    auto *Material = Batch->GetMaterial(Slot);
                    UMaterialInterface *ExpectedMaterial = Materials[Slot].MaterialInterface;
                    if (!ExpectedMaterial && Mesh->GetFName() == TEXT("SM_MonitorScreen"))
                        ExpectedMaterial = LoadObject<UMaterialInterface>(
                            nullptr, TEXT("/Game/SciFiCorridor/Materials/MI_MonitorError_Inst2.MI_MonitorError_Inst2"));
                    if (!ExpectedMaterial && Mesh->GetFName() == TEXT("SM_Top_Wall02"))
                        ExpectedMaterial = LoadObject<UMaterialInterface>(
                            nullptr, TEXT("/Game/SciFiCorridor/Materials/MI_CorridorWall_02.MI_CorridorWall_02"));
                    TestTrue(Label + TEXT(" preserves vendor slots or assigns the two explicit missing-slot repairs"),
                             Material && Material == ExpectedMaterial &&
                                 Material->GetPathName().StartsWith(TEXT("/Game/SciFiCorridor/")));
                }
            }
            TestEqual(Label + TEXT(" creates all eight licensed batches only when selected and available"),
                      LicensedBatchCount, UseLicensed ? 8 : 0);
            auto BatchCount = [&Batches](const TCHAR *Name)
            {
                int32 Count = 0;
                for (auto *Batch : Batches)
                    if (Batch->GetFName() == Name)
                        Count += Batch->GetInstanceCount();
                return Count;
            };
            TestEqual(Label + TEXT(" retains all textured walking floor tiles"), BatchCount(TEXT("TexturedDeckPanels")),
                      36);
            TestEqual(Label + TEXT(" removes only the 24 duplicate wall/canopy panels"), BatchCount(TEXT("DeckPanels")),
                      HasPresentation ? 0 : 24);
            TestEqual(Label + TEXT(" preserves runway guides when canopy/perimeter copies are removed"),
                      BatchCount(TEXT("DeckGuides")), HasPresentation ? 14 : 28);
            TestEqual(Label + TEXT(" preserves cradle, pallets and station-only service dressing"),
                      BatchCount(TEXT("ServiceStructure")), (Home ? 9 : 13) + (HasPresentation ? 0 : 19));

            const FTransform Transform = Hub->GetActorTransform();
            auto WorldPoint = [&Transform](FVector Local) { return Transform.TransformPosition(Local); };
            FCollisionObjectQueryParams StaticObjects(ECC_WorldStatic);
            FCollisionQueryParams Query(SCENE_QUERY_STAT(SSStationPresentationCollision), false);
            FHitResult Hit;
            // Positive floor/boundary queries prevent a missing physics scene from passing the clear corridor.
            for (FVector Point : {FVector(-300, 0, 180), FVector(650, -350, 180)})
            {
                const bool Blocked = Fixture.World->LineTraceSingleByObjectType(
                    Hit, WorldPoint(Point), WorldPoint(FVector(Point.X, Point.Y, -200)), StaticObjects, Query);
                TestTrue(Label + TEXT(" resolves the original deck, not a cosmetic replacement"),
                         Blocked && Hit.GetComponent() == Floor &&
                             FMath::IsNearlyEqual(Transform.InverseTransformPosition(Hit.ImpactPoint).Z, -10.0, .1));
            }
            for (float Side : {-1.f, 1.f})
            {
                TestTrue(Label + TEXT(" side walls still block"),
                         Fixture.World->LineTraceSingleByObjectType(Hit, WorldPoint(FVector(-300, Side * 1300, 220)),
                                                                    WorldPoint(FVector(-300, Side * 1500, 220)),
                                                                    StaticObjects, Query) &&
                             Hit.GetActor() == Hub &&
                             SolidCubes.Contains(Cast<UStaticMeshComponent>(Hit.GetComponent())));
                TestTrue(Label + TEXT(" inbound wings still block beside the open corridor"),
                         Fixture.World->LineTraceSingleByObjectType(Hit, WorldPoint(FVector(-1900, Side * 1050, 350)),
                                                                    WorldPoint(FVector(-1500, Side * 1050, 350)),
                                                                    StaticObjects, Query) &&
                             Hit.GetActor() == Hub &&
                             SolidCubes.Contains(Cast<UStaticMeshComponent>(Hit.GetComponent())));
            }
            TestFalse(Label + TEXT(" admits the existing 105 cm ship envelope through the real approach corridor"),
                      Fixture.World->SweepSingleByObjectType(
                          Hit, Hub->DockPosition() - Hub->GetActorForwardVector() * 3000.f,
                          Hub->DockPosition() - Hub->GetActorForwardVector() * 1250.f, FQuat::Identity, StaticObjects,
                          FCollisionShape::MakeSphere(105.f), Query));

            struct FServiceExpectation
            {
                FVector Position;
                ESSPanel HomePanel, StationPanel;
            };
            const FServiceExpectation Services[] = {
                {FVector(200, -1000, 0), ESSPanel::Weapon, ESSPanel::Upgrades},
                {FVector(-800, -1000, 0), ESSPanel::Ship, ESSPanel::Repair},
                {FVector(-1100, 850, 0), ESSPanel::Progression, ESSPanel::Contracts},
                {FVector(0, 1000, 0), ESSPanel::Settings, ESSPanel::Save},
                {FVector(950, -450, 0), ESSPanel::Launch, ESSPanel::Launch},
                {FVector(1000, 1000, 0), ESSPanel::None, ESSPanel::Vendor},
                {FVector(-1400, 0, 0), ESSPanel::None, ESSPanel::Reward}};
            for (const FServiceExpectation &Expected : Services)
            {
                FString ServiceLabel;
                const ESSPanel Panel = Hub->NearestService(WorldPoint(Expected.Position), ServiceLabel);
                TestTrue(Label + TEXT(" retains the actual home/station service at its original world anchor"),
                         Panel == (Home ? Expected.HomePanel : Expected.StationPanel));
                if (Panel != ESSPanel::None)
                    TestFalse(Label + TEXT(" retains its service label"), ServiceLabel.IsEmpty());
            }
            FString NoServiceLabel;
            TestTrue(Label + TEXT(" does not add a service outside the walking hub"),
                     Hub->NearestService(WorldPoint(FVector(0, -2000, 0)), NoServiceLabel) == ESSPanel::None);
        }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSStationWalkerRecovery, "SpaceSurvival.Integration.StationWalkerRecovery",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSStationWalkerRecovery::RunTest(const FString &Parameters)
{
    // No game instance, BeginPlay, account initialization or platform saves.
    FSSIsolatedTestWorld Fixture;
    if (!TestNotNull(TEXT("Create isolated world"), Fixture.World))
        return false;
    auto *Hub = Fixture.World->SpawnActor<ASSStation>(FVector(16000, -8000, 5000), FRotator(0, 75, 0));
    auto *Walker = Fixture.World->SpawnActor<ASSWalker>();
    if (!TestNotNull(TEXT("Create rotated hub"), Hub) || !TestNotNull(TEXT("Create walker"), Walker))
        return false;
    const FTransform HubTransform = Hub->GetActorTransform();
    const FVector DeckPosition = HubTransform.TransformPosition(FVector(-1200, 0, 180));
    Walker->SetActorLocation(DeckPosition);
    Walker->Tick(1.f / 60.f);
    TestTrue(TEXT("Ordinary deck position is unchanged"), Walker->GetActorLocation().Equals(DeckPosition, .01));

    const FVector Escapes[] = {FVector(-1800, 0, 180), FVector(1800, 0, 180), FVector(0, 1500, 180),
                               FVector(0, -1500, 180), FVector(0, 0, -300)};
    for (const FVector &Local : Escapes)
    {
        Walker->SetActorLocation(HubTransform.TransformPosition(Local));
        Walker->GetCharacterMovement()->Velocity = FVector(500, 0, -900);
        Walker->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
        Walker->Tick(1.f / 60.f);
        TestTrue(TEXT("Escaped walker returns to the rotated hub spawn"),
                 Walker->GetActorLocation().Equals(Hub->WalkSpawn(), .01));
        TestTrue(TEXT("Recovery clears falling momentum"), Walker->GetVelocity().IsNearlyZero());
        TestTrue(TEXT("Recovery restores walking"), Walker->GetCharacterMovement()->MovementMode == MOVE_Walking);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSAuthoredDisembark, "SpaceSurvival.Integration.AuthoredDisembark",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSAuthoredDisembark::RunTest(const FString &Parameters)
{
    // Real world, assets, physics queries and pawns; no GameInstance Init or save APIs.
    FSSIsolatedTestWorld Fixture;
    if (!TestNotNull(TEXT("Create isolated exit world"), Fixture.World))
        return false;
    auto *Hub = Fixture.World->SpawnActor<ASSStation>(FVector(16000, -8000, 5000), FRotator(0, 75, 0));
    auto *Walker = Fixture.World->SpawnActor<ASSWalker>();
    auto *Ship = Fixture.World->SpawnActor<ASSShip>();
    auto *Controller = Fixture.World->SpawnActor<APlayerController>();
    auto *ExitAnimation = LoadObject<UAnimSequence>(
        nullptr, TEXT("/Game/SpaceSurvival/Character/A_DisembarkLegRepair.A_DisembarkLegRepair"));
    auto *PilotAnimation =
        LoadObject<UAnimSequence>(nullptr, TEXT("/Game/SpaceSurvival/Character/A_PilotGripFit.A_PilotGripFit"));
    if (!TestNotNull(TEXT("Create station"), Hub) || !TestNotNull(TEXT("Create walker"), Walker) ||
        !TestNotNull(TEXT("Create ship"), Ship) || !TestNotNull(TEXT("Create local controller"), Controller) ||
        !TestNotNull(TEXT("Load authored exit"), ExitAnimation) ||
        !TestNotNull(TEXT("Load pilot animation"), PilotAnimation))
        return false;
    Hub->BuildHub(false);
    Walker->DispatchBeginPlay();
    Ship->DispatchBeginPlay();
    auto *PilotMesh = Ship->Pilot->GetSkeletalMeshAsset();
    auto *WalkerMesh = Walker->GetMesh()->GetSkeletalMeshAsset();
    auto *SeatedAnimation = Ship->Pilot->GetSingleNodeInstance();
    if (!TestNotNull(TEXT("Real ship BeginPlay resolves the runtime pilot mesh"), PilotMesh) ||
        !TestNotNull(TEXT("Real walker BeginPlay resolves the runtime character mesh"), WalkerMesh) ||
        !TestTrue(TEXT("Ship and walker use the same actual runtime mesh before geometry evaluation"),
                  PilotMesh == WalkerMesh) ||
        !TestTrue(TEXT("Real ship BeginPlay selects the authored pilot animation"),
                  SeatedAnimation && SeatedAnimation->GetCurrentAsset() == PilotAnimation))
        return false;
    AddInfo(TEXT("EXIT_RUNTIME_MESH: ") + PilotMesh->GetPathName());
    Controller->SetAsLocalPlayerController();
    Fixture.World->AddController(Controller);
    Controller->Possess(Walker);
    Ship->SetActorLocationAndRotation(Hub->DockPosition(), Hub->GetActorRotation());
    SeatedAnimation->SetPlaying(false);
    SeatedAnimation->SetPosition(1.137f, false);
    Ship->Pilot->TickAnimation(0.f, false);
    Ship->Pilot->RefreshBoneTransforms();
    FPoseSnapshot SeatedPose;
    Ship->Pilot->SnapshotPose(SeatedPose);
    TestTrue(TEXT("Capture the actual nonzero-phase pilot pose"), SeatedPose.bIsValid);
    const FTransform Seated = Ship->Pilot->GetComponentTransform();
    const FVector Pelvis = Ship->Pilot->GetSocketLocation(TEXT("Pelvis"));
    const FVector End = Hub->GetActorTransform().TransformPosition(FVector(650, -350, 100));
    TestTrue(TEXT("Exit is the authored 2.4 second clip without extracted root motion"),
             FMath::IsNearlyEqual(ExitAnimation->GetPlayLength(), 2.4f, .001f) && !ExitAnimation->HasRootMotion());
    if (!TestTrue(TEXT("Begin actual authored exit"),
                  Walker->BeginDisembark(Seated, End, Hub->GetActorRotation(), &SeatedPose)))
        return false;
    auto *Animation = Walker->GetMesh()->GetSingleNodeInstance();
    TestTrue(TEXT("Walker retains the shared runtime mesh and constant scale"),
             Walker->GetMesh()->GetSkeletalMeshAsset() == PilotMesh &&
                 Walker->GetMesh()->GetRelativeScale3D().Equals(FVector(1.5f), .001));
    TestTrue(TEXT("Exit starts at the exact seated component transform and pelvis"),
             Walker->GetMesh()->GetComponentTransform().Equals(Seated, .001) &&
                 Walker->GetMesh()->GetSocketLocation(TEXT("Pelvis")).Equals(Pelvis, .1));
    TestTrue(TEXT("Exit starts at zero, nonlooping, under the actor clock"),
             Animation && Animation->GetCurrentAsset() == ExitAnimation && !Animation->IsLooping() &&
                 !Animation->IsPlaying() && FMath::IsNearlyZero(Animation->GetCurrentTime()));
    FPoseSnapshot ExitInitial;
    Walker->GetMesh()->SnapshotPose(ExitInitial);
    bool ExactInitialPose = ExitInitial.bIsValid && ExitInitial.BoneNames == SeatedPose.BoneNames &&
                            ExitInitial.LocalTransforms.Num() == SeatedPose.LocalTransforms.Num();
    if (ExactInitialPose)
        for (int32 I = 0; I < ExitInitial.LocalTransforms.Num(); ++I)
            ExactInitialPose &= ExitInitial.LocalTransforms[I].Equals(SeatedPose.LocalTransforms[I], .001);
    TestTrue(TEXT("Every initial exit bone preserves the outgoing live pilot phase"), ExactInitialPose);
    TestNotNull(TEXT("Live-pose handoff uses the transition instance"),
                Cast<USSStationPoseTransition>(Walker->GetMesh()->GetAnimInstance()));
    const FVector Start = Walker->GetActorLocation();
    const FRotator Control = Controller->GetControlRotation();
    Walker->Move(FVector2D(1, 1), FVector2D(1, 1), true, .1f);
    TestTrue(TEXT("Exit blocks queued movement and camera input"),
             Walker->GetPendingMovementInputVector().IsNearlyZero() &&
                 Controller->GetControlRotation().Equals(Control, .001) &&
                 Walker->GetCharacterMovement()->MovementMode == MOVE_None);
    Walker->Tick(.4f);
    TestTrue(TEXT("Actor stays seated through the brace"), Walker->GetActorLocation().Equals(Start, .01));
    // A separate, unblended real walker establishes the expected clip pose after
    // the short handoff. No copied blend formula or mock animation evaluation.
    auto *ReferenceWalker = Fixture.World->SpawnActor<ASSWalker>();
    if (!TestNotNull(TEXT("Create exit pose reference"), ReferenceWalker))
        return false;
    ReferenceWalker->DispatchBeginPlay();
    if (!TestTrue(TEXT("Start ordinary authored reference exit"),
                  ReferenceWalker->BeginDisembark(Seated, End, Hub->GetActorRotation())))
        return false;
    ReferenceWalker->Tick(.4f);
    FPoseSnapshot BlendedBrace, ReferenceBrace;
    Walker->GetMesh()->SnapshotPose(BlendedBrace);
    ReferenceWalker->GetMesh()->SnapshotPose(ReferenceBrace);
    bool PureAuthoredBrace = BlendedBrace.LocalTransforms.Num() == ReferenceBrace.LocalTransforms.Num();
    if (PureAuthoredBrace)
        for (int32 I = 0; I < BlendedBrace.LocalTransforms.Num(); ++I)
            PureAuthoredBrace &= BlendedBrace.LocalTransforms[I].Equals(ReferenceBrace.LocalTransforms[I], .001);
    TestTrue(TEXT("Blend completely releases to the actual authored brace before rise"), PureAuthoredBrace);
    auto *Transition = Cast<USSStationPoseTransition>(Walker->GetMesh()->GetAnimInstance());
    if (!TestNotNull(TEXT("Retain transition instance through exit"), Transition))
        return false;
    TestTrue(TEXT("Completed blend releases its copied pose"), !Transition->GetSourcePose().bIsValid);
    FPoseSnapshot WrongMeshPose = SeatedPose;
    WrongMeshPose.SkeletalMeshName = TEXT("UnrelatedMesh");
    TestFalse(TEXT("Different mesh snapshot is rejected"), Transition->SetSourcePose(WrongMeshPose));
    FPoseSnapshot WrongBonePose = SeatedPose;
    WrongBonePose.BoneNames[0] = TEXT("UnrelatedBone");
    TestFalse(TEXT("Mismatched reference bone order is rejected"), Transition->SetSourcePose(WrongBonePose));
    ReferenceWalker->Destroy();
    const FVector Offset(12000, -3000, 500);
    if (!TestTrue(TEXT("Rebase the actual world and its physics scene during exit"),
                  Fixture.World->SetNewWorldOrigin(FIntVector(-12000, 3000, -500))))
        return false;
    Walker->Tick(.4f);
    TestTrue(TEXT("World-origin shift preserves the stationary rise"),
             Walker->GetActorLocation().Equals(Start + Offset, .01));
    Walker->Tick(.8f);
    const FVector Contact = Walker->GetActorLocation();
    FHitResult Floor;
    const double WalkingFloorGap =
        (UCharacterMovementComponent::MIN_FLOOR_DIST + UCharacterMovementComponent::MAX_FLOOR_DIST) * .5;
    TestTrue(TEXT("Landing capsule already has the normal walking gap above the real station floor"),
             Fixture.World->LineTraceSingleByObjectType(Floor, Contact, Contact - FVector(0, 0, 300),
                                                        FCollisionObjectQueryParams(ECC_WorldStatic)) &&
                 Floor.GetActor() == Hub &&
                 FMath::IsNearlyEqual(
                     Contact.Z - Floor.ImpactPoint.Z,
                     double(Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()) + WalkingFloorGap, .1));
    AddInfo(FString::Printf(
        TEXT("EXIT_CONTACT actor=%s floorZ=%.6f capsuleGap=%.6f meshZ=%.6f"), *Contact.ToString(), Floor.ImpactPoint.Z,
        Contact.Z - Floor.ImpactPoint.Z - Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight(),
        Walker->GetMesh()->GetRelativeLocation().Z));
    auto CheckVisibleSole = [this, Walker, Hub, PilotMesh](const TCHAR *Stage)
    {
        const auto *RenderData = PilotMesh->GetResourceForRendering();
        const auto *Weights = Walker->GetMesh()->GetSkinWeightBuffer(0);
        if (!TestTrue(TEXT("Imported LOD 0 retains CPU data for the sole geometry check"),
                      RenderData && !RenderData->LODRenderData.IsEmpty() && Weights &&
                          RenderData->LODRenderData[0].StaticVertexBuffers.PositionVertexBuffer.GetAllowCPUAccess() &&
                          Weights->GetNeedsCPUAccess()))
            return;
        TArray<FMatrix44f> RefToLocal;
        TArray<FVector3f> Vertices;
        Walker->GetMesh()->GetCurrentRefToLocalMatrices(RefToLocal, 0);
        USkinnedMeshComponent::ComputeSkinnedPositions(Walker->GetMesh(), Vertices, RefToLocal,
                                                       RenderData->LODRenderData[0], *Weights);
        if (!TestTrue(TEXT("Imported mesh supplies skinned vertices"), !Vertices.IsEmpty()))
            return;
        FVector Lowest(0, 0, UE_DOUBLE_BIG_NUMBER);
        for (const FVector3f &Vertex : Vertices)
        {
            const FVector WorldVertex = Walker->GetMesh()->GetComponentTransform().TransformPosition(FVector(Vertex));
            if (WorldVertex.Z < Lowest.Z)
                Lowest = WorldVertex;
        }
        double PlateZ = -UE_DOUBLE_BIG_NUMBER;
        TInlineComponentArray<UInstancedStaticMeshComponent *> Batches;
        Hub->GetComponents(Batches);
        for (auto *Batch : Batches)
            if (Batch->GetFName() == TEXT("TexturedDeckPanels") && Batch->GetStaticMesh())
            {
                for (int32 Index = 0; Index < Batch->GetInstanceCount(); ++Index)
                {
                    FTransform Instance;
                    Batch->GetInstanceTransform(Index, Instance, true);
                    const FVector Local = Instance.InverseTransformPosition(Lowest);
                    const FBox Bounds = Batch->GetStaticMesh()->GetBoundingBox();
                    if (Local.X >= Bounds.Min.X && Local.X <= Bounds.Max.X && Local.Y >= Bounds.Min.Y &&
                        Local.Y <= Bounds.Max.Y)
                        PlateZ =
                            FMath::Max(PlateZ, Instance.TransformPosition(FVector(Local.X, Local.Y, Bounds.Max.Z)).Z);
                }
            }
        if (!TestTrue(TEXT("Visible sole resolves to an actual textured floor panel"), PlateZ > -UE_DOUBLE_BIG_NUMBER))
            return;
        AddInfo(FString::Printf(TEXT("EXIT_SOLE %s vertices=%d soleZ=%.6f plateZ=%.6f clearance=%.6f"), Stage,
                                Vertices.Num(), Lowest.Z, PlateZ, Lowest.Z - PlateZ));
        TestTrue(FString::Printf(TEXT("%s visible sole meets the actual deck panel within 1 mm"), Stage),
                 FMath::Abs(Lowest.Z - PlateZ) <= .1);
    };
    CheckVisibleSole(TEXT("contact"));
    const FVector LeftFoot = Walker->GetMesh()->GetSocketLocation(TEXT("L_Foot"));
    const FVector RightFoot = Walker->GetMesh()->GetSocketLocation(TEXT("R_Foot"));
    Walker->Tick(.4f);
    TestTrue(TEXT("Actor and both feet stay planted during compression"),
             Walker->IsDisembarking() && Walker->GetActorLocation().Equals(Contact, .01) &&
                 Walker->GetMesh()->GetSocketLocation(TEXT("L_Foot")).Equals(LeftFoot, .1) &&
                 Walker->GetMesh()->GetSocketLocation(TEXT("R_Foot")).Equals(RightFoot, .1));
    TestTrue(TEXT("Collision and movement stay disabled before clip completion"),
             Walker->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::NoCollision &&
                 Walker->GetCharacterMovement()->MovementMode == MOVE_None);
    Walker->Tick(.401f);
    Animation = Walker->GetMesh()->GetSingleNodeInstance();
    AddInfo(FString::Printf(TEXT("EXIT_HANDOFF actorDelta=%s leftFootDelta=%s rightFootDelta=%s floorDist=%.6f"),
                            *(Walker->GetActorLocation() - Contact).ToString(),
                            *(Walker->GetMesh()->GetSocketLocation(TEXT("L_Foot")) - LeftFoot).ToString(),
                            *(Walker->GetMesh()->GetSocketLocation(TEXT("R_Foot")) - RightFoot).ToString(),
                            Walker->GetCharacterMovement()->CurrentFloor.FloorDist));
    CheckVisibleSole(TEXT("walk handoff"));
    TestTrue(TEXT("Exit completes without losing possession or moving the planted actor"),
             !Walker->IsDisembarking() && Controller->GetPawn() == Walker &&
                 Walker->GetActorLocation().Equals(Contact, .01));
    TestTrue(TEXT("Completion restores collision, walking and the matching walk phase"),
             Walker->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics &&
                 Walker->GetCharacterMovement()->MovementMode == MOVE_Walking && Animation &&
                 Animation->GetCurrentAsset() && Animation->GetCurrentAsset()->GetName() == TEXT("A_WalkLegRepair") &&
                 Animation->IsLooping() && FMath::IsNearlyEqual(Animation->GetCurrentTime(), .308333333f, .001f));
    TestTrue(TEXT("Walk handoff preserves both foot positions"),
             Walker->GetMesh()->GetSocketLocation(TEXT("L_Foot")).Equals(LeftFoot, .1) &&
                 Walker->GetMesh()->GetSocketLocation(TEXT("R_Foot")).Equals(RightFoot, .1));
    Walker->Move(FVector2D(0, 1), FVector2D::ZeroVector, false, .1f);
    TestFalse(TEXT("Walking input is restored after the authored exit"),
              Walker->GetPendingMovementInputVector().IsNearlyZero());
    for (int32 Rate : {30, 60, 144})
    {
        FTransform ShiftedSeat = Seated;
        ShiftedSeat.AddToTranslation(Offset);
        TestTrue(TEXT("Restart isolated exit for frame-rate comparison"),
                 Walker->BeginDisembark(ShiftedSeat, End + Offset, Hub->GetActorRotation(), &SeatedPose));
        for (int32 Frame = 0; Frame < Rate * 3; ++Frame)
        {
            Walker->Tick(1.f / Rate);
            if (!TestTrue(TEXT("All exit samples preserve the full pilot mesh scale"),
                          Walker->GetMesh()->GetComponentScale().Equals(FVector(1.5f), .001)))
                return false;
        }
        AddInfo(FString::Printf(TEXT("EXIT_RATE rate=%d actorDelta=%s floorDist=%.6f"), Rate,
                                *(Walker->GetActorLocation() - Contact).ToString(),
                                Walker->GetCharacterMovement()->CurrentFloor.FloorDist));
        TestTrue(TEXT("30/60/144 Hz finish at the same landing point with walking restored"),
                 !Walker->IsDisembarking() && Walker->GetActorLocation().Equals(Contact, .1) &&
                     Walker->GetCharacterMovement()->MovementMode == MOVE_Walking);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSFieldPresentationSelection, "SpaceSurvival.Integration.FieldPresentationSelection",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSFieldPresentationSelection::RunTest(const FString &)
{
    FSSIsolatedTestWorld Fixture;
    if (!TestNotNull(TEXT("Create isolated field world"), Fixture.World))
        return false;
    auto *Field = Fixture.World->SpawnActor<ASSWorldBody>();
    if (!TestNotNull(TEXT("Create actual field actor"), Field))
        return false;
    const ESSWorldKind Kinds[] = {ESSWorldKind::ElectricalStorm, ESSWorldKind::GravityAnomaly,
                                  ESSWorldKind::ElectricalStorm};
    const TCHAR *Names[] = {TEXT("Electrical"), TEXT("Gravity"), TEXT("Electrical")};
    for (int32 Index = 0; Index < 3; ++Index)
    {
        // Reuse the actor deliberately: stale component overrides must not retain
        // the preceding family's shader when Configure installs another mesh.
        Field->Configure(Kinds[Index], 3400.f, 7.f, 5);
        auto *Mesh = Field->Visual->GetStaticMesh().Get();
        auto *Material = Cast<UMaterialInstanceDynamic>(Field->Visual->GetMaterial(0));
        if (!TestNotNull(TEXT("Load actual field mesh"), Mesh) ||
            !TestNotNull(TEXT("Create actual field dynamic material"), Material))
            return false;
        TestEqual(TEXT("Configure selects the intended field geometry"), Mesh->GetName(),
                  FString::Printf(TEXT("SM_%sFieldCandidateV3"), Names[Index]));
        TestEqual(TEXT("Each field uses its own authored shader"), Material->Parent->GetName(),
                  FString::Printf(TEXT("M_%sFieldCandidateV3"), Names[Index]));
        TestTrue(TEXT("Dynamic material parent comes from the newly selected mesh"),
                 Material->Parent == Mesh->GetMaterial(0));
        TestTrue(TEXT("Visual adoption preserves the exact danger radius and query collision"),
                 FMath::IsNearlyEqual(Field->GetBodyRadius(), 3400.f) &&
                     FMath::IsNearlyEqual(Field->Collision->GetScaledSphereRadius(), 3400.f) &&
                     Field->Visual->GetCollisionEnabled() == ECollisionEnabled::NoCollision &&
                     Field->Collision->GetCollisionResponseToChannel(ECC_Visibility) == ECR_Ignore);
        TestTrue(TEXT("Visual boundary fits the existing spherical radius"),
                 FMath::IsNearlyEqual(Mesh->GetBounds().BoxExtent.GetMax() * Field->Visual->GetRelativeScale3D().X,
                                      3400.0, .01));
        TestTrue(TEXT("Configure resets the existing warning brightness"),
                 FMath::IsNearlyEqual(Material->K2_GetScalarParameterValue(TEXT("Emission")), .25f));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSLateEventAcceptance, "SpaceSurvival.Integration.LateEventAcceptance",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSLateEventAcceptance::RunTest(const FString &Parameters)
{
    for (ESSEncounterKind Kind : {ESSEncounterKind::SalvageCache, ESSEncounterKind::DistressCombat})
    {
        // Exercise real objective actors and weak-owner completion callbacks in a
        // transient world; no production save or account adapter is instantiated.
        FSSIsolatedTestWorld Fixture;
        if (!TestNotNull(TEXT("Create isolated event world"), Fixture.World))
            return false;
        auto *Controller = Fixture.World->SpawnActor<APlayerController>();
        auto *Ship = Fixture.World->SpawnActor<ASSShip>();
        auto *Beacon = Fixture.World->SpawnActor<ASSEncounterBeacon>();
        if (!TestNotNull(TEXT("Create event controller"), Controller) ||
            !TestNotNull(TEXT("Create event ship"), Ship) || !TestNotNull(TEXT("Create event beacon"), Beacon))
            return false;
        Fixture.World->AddController(Controller);
        Controller->Possess(Ship);
        if (!TestTrue(TEXT("Event resolves the possessed player ship"),
                      UGameplayStatics::GetPlayerPawn(Beacon, 0) == Ship))
            return false;
        Beacon->ConfigureEncounter(Kind, Kind == ESSEncounterKind::SalvageCache ? 2 : 7);
        Beacon->LifetimeSeconds = 1.f;
        Beacon->Tick(.9f);
        if (!TestTrue(TEXT("Accept just before the offer expires"), Beacon->TryAccept()))
            return false;
        const float ObjectiveDuration = GetDefault<USSPhase1Data>()->Encounter(Kind).ObjectiveDuration;
        Beacon->Tick(ObjectiveDuration - 1.f);
        if (!TestFalse(TEXT("Accepted signal survives its original offer expiry"), Beacon->IsActorBeingDestroyed()))
            return false;
        TestFalse(TEXT("Objective remains live until its own deadline"), Beacon->IsResolved());
        if (Kind == ESSEncounterKind::SalvageCache)
        {
            TArray<ASSPickup *> Caches;
            for (TActorIterator<ASSPickup> It(Fixture.World); It; ++It)
                Caches.Add(*It);
            TestEqual(TEXT("Acceptance spawned every salvage objective"), Caches.Num(),
                      Beacon->GetObjectiveRemaining());
            for (ASSPickup *Cache : Caches)
            {
                Ship->SetActorLocation(Cache->GetActorLocation());
                Cache->Tick(0.f);
            }
        }
        else
        {
            TArray<ASSEnemy *> Attackers;
            for (TActorIterator<ASSEnemy> It(Fixture.World); It; ++It)
                Attackers.Add(*It);
            TestEqual(TEXT("Acceptance spawned every combat objective"), Attackers.Num(),
                      Beacon->GetObjectiveRemaining());
            for (ASSEnemy *Enemy : Attackers)
                Enemy->ReceiveWeaponHit(100000.f);
        }
        TestTrue(TEXT("Actual objective completion resolves a late-accepted event"), Beacon->IsResolved());
        TestEqual(TEXT("All objective callbacks reached their surviving owner"), Beacon->GetObjectiveRemaining(), 0);
    }
    return true;
}
#endif
