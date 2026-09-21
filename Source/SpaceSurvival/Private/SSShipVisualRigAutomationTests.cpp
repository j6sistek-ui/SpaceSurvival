#include "SSShipVisualRig.h"
#include "SSShip.h"
#include "SSFlightHull.h"
#include "SSGameInstance.h"
#include "SSPhase1Data.h"
#include "SSStation.h"
#include "SSPhoenixGearBounds.h"
#include "Animation/AnimationAsset.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Camera/CameraComponent.h"
#include "Components/ArrowComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/BoxComponent.h"
#include "Components/SphereComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "NiagaraSystem.h"
#include "PhysicsEngine/PhysicsThrusterComponent.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
#include "PhysicsEngine/BodySetup.h"
#include "ThrusterManagerComp.h"
#include "GyroManagerComp.h"
#if WITH_EDITOR
#include "Rendering/SkeletalMeshModel.h"
#include "Animation/AnimSequence.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#endif

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSVisualRigWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    USSGameInstance *Instance = nullptr;
    ASSShip *Ship = nullptr;
    APlayerController *Controller = nullptr;
    USSShipVisualRig *Rig = nullptr;
    FString SavedCommandLine;
    bool RestoreCommandLine = false;

    bool Initialize(FAutomationTestBase &Test, bool Classic = false)
    {
        if (Classic)
        {
            SavedCommandLine = FCommandLine::Get();
            RestoreCommandLine = true;
            FCommandLine::Append(TEXT(" -SSClassic"));
        }
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated presentation world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // Never initialize account storage or touch the owner's saves.
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = 0;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        GWorld = World;
        World->GetWorldSettings()->DefaultGameMode = AGameModeBase::StaticClass();
        if (!Test.TestTrue(TEXT("Install stock fixture GameMode"), World->SetGameMode(FURL())))
            return false;
        World->InitializeActorsForPlay(FURL());
        Controller = World->SpawnActor<APlayerController>();
        Ship = World->SpawnActor<ASSShip>(FVector(0, 0, 7000), FRotator::ZeroRotator);
        if (!Test.TestNotNull(TEXT("Create native flight pawn"), Ship) ||
            !Test.TestNotNull(TEXT("Create fixture controller"), Controller))
            return false;
        Ship->Tuning = NewObject<USSPhase1Data>(Ship);
        if (!Test.TestTrue(TEXT("Begin in-memory run"), Instance->Session.StartRun("phoenix-visual-fixture")))
            return false;
        Controller->SetAsLocalPlayerController();
        World->AddController(Controller);
        Controller->Possess(Ship);
        Controller->SetActorTickEnabled(false);
        World->BeginPlay();
        Controller->SetActorTickEnabled(false);
        Rig = Ship->GetVisualRig();
        if (!Test.TestNotNull(TEXT("Native pawn owns visual adapter"), Rig))
            return false;
        if (Classic ? !Test.TestFalse(TEXT("Explicit Classic fixture does not load the Phoenix rig"),
                                      Rig->HasBlueprintRig())
                    : !Test.TestTrue(TEXT("Licensed Phoenix Blueprint actually loaded"), Rig->HasBlueprintRig()))
            return false;
        // Hold only the native flight body. Real world/component/animation ticks still execute, even
        // when ASSShip itself is stopped, exactly as they must after landing at a station.
        Ship->BeginMooring();
        Ship->SetActorTickEnabled(false);
        return true;
    }

    void Seconds(float Duration)
    {
        const int32 Count = FMath::CeilToInt(Duration * 60.f);
        for (int32 Frame = 0; Frame < Count; ++Frame)
        {
            ++GFrameCounter;
            World->Tick(LEVELTICK_All, 1.f / 60.f);
        }
    }

    ~FSSVisualRigWorld()
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
        if (RestoreCommandLine)
            FCommandLine::Set(*SavedCommandLine);
    }
};

template <class T> T *NamedComponent(AActor *Actor, const TCHAR *Name)
{
    TInlineComponentArray<T *> Components(Actor);
    for (T *Component : Components)
        if (Component->GetName() == Name)
            return Component;
    return nullptr;
}

bool PoseChanged(const TArray<FTransform> &Before, const TArray<FTransform> &After)
{
    if (Before.Num() != After.Num() || Before.IsEmpty())
        return false;
    for (int32 Index = 0; Index < Before.Num(); ++Index)
        if (!Before[Index].Equals(After[Index], .01f))
            return true;
    return false;
}

bool AnimationNamed(FAutomationTestBase &Test, USkeletalMeshComponent *Mesh, const TCHAR *Expected)
{
    UAnimSingleNodeInstance *Animation = Mesh->GetSingleNodeInstance();
    if (!Test.TestNotNull(TEXT("Skeletal rig has a live single-node animation instance"), Animation) ||
        !Test.TestNotNull(TEXT("Animation instance has an actual clip"), Animation->GetAnimationAsset()))
        return false;
    return Test.TestEqual(TEXT("Native state selects the authored clip"), Animation->GetAnimationAsset()->GetName(),
                          FString(Expected));
}

float ClipSeconds(USkeletalMeshComponent *Mesh)
{
    UAnimSingleNodeInstance *Animation = Mesh->GetSingleNodeInstance();
    return Animation->GetLength() / Animation->GetPlayRate();
}

void CheckAdvancingPose(FAutomationTestBase &Test, FSSVisualRigWorld &Fixture, USkeletalMeshComponent *Mesh)
{
    UAnimSingleNodeInstance *Animation = Mesh->GetSingleNodeInstance();
    const float Duration = ClipSeconds(Mesh);
    Fixture.Seconds(Duration * .12f);
    const float BeforeTime = Animation->GetCurrentTime();
    const TArray<FTransform> Before = Mesh->GetBoneSpaceTransforms();
    Fixture.Seconds(Duration * .6f);
    Test.TestTrue(TEXT("World ticks advance the clip without manual seeking"),
                  Animation->GetCurrentTime() > BeforeTime);
    Test.TestTrue(TEXT("Real bone transforms change while the authored clip plays"),
                  PoseChanged(Before, Mesh->GetBoneSpaceTransforms()));
}
#if WITH_EDITOR
// Clip the actual posed triangles against a vertical column. A bone's whole-part bounds can
// reach below standing height far away from the walking path and cannot prove local headroom.
double LowestPosedSurfaceInColumn(USkeletalMeshComponent *Hull, const FBox2D &Column)
{
    USkeletalMesh *Mesh = Hull->GetSkeletalMeshAsset();
    const FSkeletalMeshModel *Model = Mesh->GetImportedModel();
    if (!Model || Model->LODModels.IsEmpty())
        return -DBL_MAX;
    const auto &Skeleton = Mesh->GetRefSkeleton();
    TArray<FTransform> Bind = Skeleton.GetRefBonePose();
    TArray<FTransform> Skin;
    Skin.SetNum(Bind.Num());
    for (int32 Bone = 0; Bone < Bind.Num(); ++Bone)
    {
        const int32 Parent = Skeleton.GetParentIndex(Bone);
        if (Parent != INDEX_NONE)
            Bind[Bone] *= Bind[Parent];
        Skin[Bone] = Bind[Bone].Inverse() * Hull->GetBoneTransform(Bone);
    }
    const FSkeletalMeshLODModel &LOD = Model->LODModels[0];
    if (LOD.IndexBuffer.IsEmpty() || LOD.NumVertices == 0)
        return -DBL_MAX;
    TArray<FVector> Posed;
    Posed.Init(FVector::ZeroVector, LOD.NumVertices);
    int32 PosedVertices = 0;
    for (const FSkelMeshSection &Section : LOD.Sections)
        for (int32 Index = 0; Index < Section.SoftVertices.Num(); ++Index)
        {
            const FSoftSkinVertex &Vertex = Section.SoftVertices[Index];
            FVector Position = FVector::ZeroVector;
            for (int32 Influence = 0; Influence < MAX_TOTAL_INFLUENCES; ++Influence)
                if (Vertex.InfluenceWeights[Influence])
                {
                    const int32 Bone = Section.BoneMap[Vertex.InfluenceBones[Influence]];
                    Position += Skin[Bone].TransformPosition(FVector(Vertex.Position)) *
                                (double(Vertex.InfluenceWeights[Influence]) / MAX_uint16);
                }
            Posed[Section.BaseVertexIndex + Index] = Position;
            ++PosedVertices;
        }
    if (PosedVertices != int32(LOD.NumVertices))
        return -DBL_MAX;
    double Lowest = DBL_MAX;
    for (int32 Index = 0; Index + 2 < LOD.IndexBuffer.Num(); Index += 3)
    {
        TArray<FVector> Polygon = {Posed[LOD.IndexBuffer[Index]], Posed[LOD.IndexBuffer[Index + 1]],
                                   Posed[LOD.IndexBuffer[Index + 2]]};
        for (int32 Side = 0; Side < 4 && !Polygon.IsEmpty(); ++Side)
        {
            const int32 Axis = Side / 2;
            const bool Minimum = (Side % 2) == 0;
            const double Plane = Minimum ? Column.Min[Axis] : Column.Max[Axis];
            auto Distance = [Axis, Minimum, Plane](const FVector &Point)
            { return Minimum ? Point[Axis] - Plane : Plane - Point[Axis]; };
            TArray<FVector> Clipped;
            FVector Previous = Polygon.Last();
            double PreviousDistance = Distance(Previous);
            for (const FVector &Current : Polygon)
            {
                const double CurrentDistance = Distance(Current);
                if ((CurrentDistance >= 0.) != (PreviousDistance >= 0.))
                    Clipped.Add(
                        FMath::Lerp(Previous, Current, PreviousDistance / (PreviousDistance - CurrentDistance)));
                if (CurrentDistance >= 0.)
                    Clipped.Add(Current);
                Previous = Current;
                PreviousDistance = CurrentDistance;
            }
            Polygon = MoveTemp(Clipped);
        }
        for (const FVector &Vertex : Polygon)
            Lowest = FMath::Min(Lowest, Vertex.Z);
    }
    return Lowest;
}
#endif

} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPhoenixBlueprintRig, "SpaceSurvival.Presentation.PhoenixBlueprintRig",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSPhoenixBlueprintRig::RunTest(const FString &)
{
    FSSVisualRigWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    USkeletalMeshComponent *Hull = Fixture.Rig->GetHull();
    APawn *Presentation = Cast<APawn>(Hull->GetOwner());
    if (!TestNotNull(TEXT("Authored hull belongs to its supplied Blueprint pawn"), Presentation))
        return false;
    TestEqual(TEXT("Presentation-only derivative of the supplied Blueprint is used"),
              Presentation->GetClass()->GetPathName(),
              FString(TEXT(
                  "/Game/SpaceSurvival/Licensed/PhoenixPresentation/BP_PhoenixPresentation.BP_PhoenixPresentation_C")));
    TestEqual(TEXT("Main hull is not the separate airbrake mesh"), Hull->GetSkeletalMeshAsset()->GetPathName(),
              FString(TEXT("/Game/Stellar_Phoenix/Spaceship/Meshes/Stellar_Phoenix.Stellar_Phoenix")));
    TestTrue(TEXT("Presentation remains owned and attached to native ship"),
             Presentation->GetOwner() == Fixture.Ship && Presentation->GetAttachParentActor() == Fixture.Ship);
    TestTrue(TEXT("Native pawn keeps the controller; vendor cannot receive input or autopossess"),
             Fixture.Controller->GetPawn() == Fixture.Ship && Presentation->GetController() == nullptr &&
                 Presentation->AutoPossessPlayer == EAutoReceiveInput::Disabled &&
                 Presentation->AutoPossessAI == EAutoPossessAI::Disabled &&
                 Presentation->AutoReceiveInput == EAutoReceiveInput::Disabled && !Presentation->InputEnabled());
    TestFalse(TEXT("Vendor flight Event Tick is disabled"), Presentation->IsActorTickEnabled());
    TestFalse(TEXT("Vendor actor cannot collide"), Presentation->GetActorEnableCollision());
    TInlineComponentArray<UPrimitiveComponent *> Primitives(Presentation);
    for (UPrimitiveComponent *Primitive : Primitives)
        TestTrue(FString::Printf(TEXT("%s cannot add physics, blocking or overlap events"), *Primitive->GetName()),
                 !Primitive->IsSimulatingPhysics() &&
                     Primitive->GetCollisionEnabled() == ECollisionEnabled::NoCollision &&
                     !Primitive->GetGenerateOverlapEvents());
    auto *Thruster = NamedComponent<UPhysicsThrusterComponent>(Presentation, TEXT("PhysicsThruster"));
    if (TestNotNull(TEXT("Supplied physics thruster is present but inert"), Thruster))
        TestTrue(TEXT("Vendor thruster cannot tick or apply force"),
                 !Thruster->IsComponentTickEnabled() && !Thruster->IsActive() && Thruster->ThrustStrength == 0.f);
    auto *Camera = NamedComponent<UCameraComponent>(Presentation, TEXT("Camera"));
    if (TestNotNull(TEXT("Supplied demo camera remains in hierarchy"), Camera))
        TestFalse(TEXT("Supplied camera cannot take the view"), Camera->IsActive());
    auto *Crosshair = NamedComponent<UTextRenderComponent>(Presentation, TEXT("Crosshair"));
    if (TestNotNull(TEXT("Supplied crosshair is identified"), Crosshair))
        TestFalse(TEXT("Demo crosshair cannot overlay native targeting"), Crosshair->IsVisible());
    TestNotNull(TEXT("Separate airbrake mesh retained"),
                NamedComponent<USkeletalMeshComponent>(Presentation, TEXT("Stellar_Phoenix_AirBrake")));
    for (const TCHAR *Side : {TEXT("Left"), TEXT("Right")})
    {
        auto *Pivot = NamedComponent<UArrowComponent>(Presentation, *FString::Printf(TEXT("Engine%s"), Side));
        auto *Engine = NamedComponent<UStaticMeshComponent>(Presentation,
                                                            *FString::Printf(TEXT("Stellar_Phoenix_Engine_%s"), Side));
        if (TestNotNull(TEXT("Engine has its authored pivot"), Pivot) &&
            TestNotNull(TEXT("Engine mesh retained"), Engine))
            TestTrue(TEXT("Engine remains attached to its authored pivot"), Engine->GetAttachParent() == Pivot);
    }
    FVector AuthoredMean = FVector::ZeroVector;
    for (const TCHAR *Name :
         {TEXT("ProjectileSpawn"), TEXT("ProjectileSpawn1"), TEXT("ProjectileSpawn2"), TEXT("ProjectileSpawn3")})
    {
        USceneComponent *Muzzle = NamedComponent<UArrowComponent>(Presentation, Name);
        if (!TestNotNull(TEXT("Every authored gun anchor survives the adapter"), Muzzle))
            return false;
        AuthoredMean += Muzzle->GetComponentLocation() * .25;
    }
    FVector Muzzle;
    TestTrue(TEXT("Native weapons receive the authored gun origin"),
             Fixture.Rig->GetMuzzleWorldPosition(Muzzle) && Muzzle.Equals(AuthoredMean, .01));
    const FSSHullDefinition Definition(ESSHullIdentity::StellarPhoenix);
    TestTrue(TEXT("Shot origin is forward of the gameplay collision sphere"),
             FVector::DotProduct(Muzzle - Fixture.Ship->GetActorLocation(), Fixture.Ship->GetActorForwardVector()) >
                 Definition.ScaledCollisionRadius());
    TestNotNull(TEXT("Authored firing effect asset resolves"),
                LoadObject<UNiagaraSystem>(nullptr, TEXT("/Game/Stellar_Phoenix/Spaceship/VFX/VFX_Shoot.VFX_Shoot")));
    Fixture.Rig->PlayFiring();
    // NullRHI intentionally creates no Niagara render components. Emission and appearance belong to
    // the rendered capture gate, not a component-count assertion in this suite.
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPhoenixAnimationTransitions,
                                 "SpaceSurvival.Presentation.PhoenixAnimationTransitions",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSPhoenixAnimationTransitions::RunTest(const FString &)
{
    FSSVisualRigWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    USkeletalMeshComponent *Hull = Fixture.Rig->GetHull();
    if (!AnimationNamed(*this, Hull, TEXT("Landing_Off")))
        return false;
    const float StowDuration = ClipSeconds(Hull);
    CheckAdvancingPose(*this, Fixture, Hull);
    Fixture.Seconds(StowDuration * .4f);
    if (!AnimationNamed(*this, Hull, TEXT("BattleMode_Enter")))
        return false;
    Fixture.Seconds(Hull->GetSingleNodeInstance()->GetLength() + .1f);
    const TArray<FTransform> FlightPose = Hull->GetBoneSpaceTransforms();

    auto *AirBrake = NamedComponent<USkeletalMeshComponent>(Hull->GetOwner(), TEXT("Stellar_Phoenix_AirBrake"));
    if (!TestNotNull(TEXT("Independent airbrake component is available"), AirBrake) ||
        !AnimationNamed(*this, AirBrake, TEXT("AirBrake")))
        return false;
    const TArray<FTransform> BrakeRest = AirBrake->GetBoneSpaceTransforms();
    auto *Pivot = NamedComponent<UArrowComponent>(Hull->GetOwner(), TEXT("EngineLeft"));
    if (!TestNotNull(TEXT("Authored engine pivot available"), Pivot))
        return false;
    const FQuat EngineRest = Pivot->GetRelativeRotation().Quaternion();
    Fixture.Rig->UpdateFlight(FVector2D(.8, .6), FVector2D(.3, .5), 1.f, true, true);
    Fixture.Seconds(AirBrake->GetSingleNodeInstance()->GetLength() * .6f);
    TestTrue(TEXT("Brake input advances the separate airbrake pose"),
             PoseChanged(BrakeRest, AirBrake->GetBoneSpaceTransforms()));
    TestFalse(TEXT("Airbrake animation does not replace the settled main hull pose"),
              PoseChanged(FlightPose, Hull->GetBoneSpaceTransforms()));
    TestTrue(TEXT("Steering animates the engine about its original pivot"),
             EngineRest.AngularDistance(Pivot->GetRelativeRotation().Quaternion()) > FMath::DegreesToRadians(1.f));
    const float BrakeTime = AirBrake->GetSingleNodeInstance()->GetCurrentTime();
    Fixture.Rig->UpdateFlight(FVector2D::ZeroVector, FVector2D::ZeroVector, .4f, false, false);
    Fixture.Seconds(.1f);
    TestTrue(TEXT("Releasing brake reverses the authored airbrake animation"),
             AirBrake->GetSingleNodeInstance()->GetCurrentTime() < BrakeTime);

    Fixture.Rig->PlayLanding();
    if (!AnimationNamed(*this, Hull, TEXT("BattleMode_Exit")))
        return false;
    const float ExitDuration = ClipSeconds(Hull);
    Fixture.Seconds(ExitDuration * .2f);
    const float LandingTime = Hull->GetSingleNodeInstance()->GetCurrentTime();
    Fixture.Rig->PlayLanding();
    TestEqual(TEXT("Repeated landing notification cannot restart the animation"),
              Hull->GetSingleNodeInstance()->GetCurrentTime(), LandingTime);
    Fixture.Seconds(ExitDuration * .9f);
    if (!AnimationNamed(*this, Hull, TEXT("Landing_On")))
        return false;
    CheckAdvancingPose(*this, Fixture, Hull);
    Fixture.Seconds(Hull->GetSingleNodeInstance()->GetLength());
    TestTrue(TEXT("Settled landing pose visibly differs from flight"),
             PoseChanged(FlightPose, Hull->GetBoneSpaceTransforms()));

    Fixture.Rig->PlayTakeoff();
    if (!AnimationNamed(*this, Hull, TEXT("Landing_Off")))
        return false;
    CheckAdvancingPose(*this, Fixture, Hull);
    Fixture.Seconds(StowDuration * .4f);
    if (!AnimationNamed(*this, Hull, TEXT("BattleMode_Enter")))
        return false;
    Fixture.Seconds(Hull->GetSingleNodeInstance()->GetLength() + .1f);
    TestFalse(TEXT("Takeoff restores the same authored flight configuration"),
              PoseChanged(FlightPose, Hull->GetBoneSpaceTransforms()));
    TestTrue(TEXT("Hull animation remains tickable with native pawn tick stopped"),
             Hull->IsComponentTickEnabled() && !Hull->bPauseAnims && !Fixture.Ship->IsActorTickEnabled());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPhoenixMooringPose, "SpaceSurvival.Presentation.PhoenixMooringPose",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSPhoenixMooringPose::RunTest(const FString &)
{
    FSSVisualRigWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    USkeletalMeshComponent *Hull = Fixture.Rig->GetHull();
    Fixture.Seconds(ClipSeconds(Hull) + .1f);
    if (!AnimationNamed(*this, Hull, TEXT("BattleMode_Enter")))
        return false;
    Fixture.Seconds(ClipSeconds(Hull) + .1f);
    const TArray<FTransform> FlightPose = Hull->GetBoneSpaceTransforms();
    const float SettledTime = Hull->GetSingleNodeInstance()->GetCurrentTime();
    TestTrue(TEXT("Actual flight pawn begins this release in a magnetic hold"), Fixture.Ship->IsMoored());

    Fixture.Ship->EndMooring();
    TestFalse(TEXT("Native release clears the magnetic hold"), Fixture.Ship->IsMoored());
    TestTrue(TEXT("Native release resumes forward flight"), Fixture.Ship->GetVelocity().X > 1000.f);
    AnimationNamed(*this, Hull, TEXT("BattleMode_Enter"));
    TestEqual(TEXT("Depot release does not rewind the authored flight animation"),
              Hull->GetSingleNodeInstance()->GetCurrentTime(), SettledTime);
    Fixture.Seconds(.2f);
    TestFalse(TEXT("Evaluated gear and ramp stay stowed after depot release"),
              PoseChanged(FlightPose, Hull->GetBoneSpaceTransforms()));

    Fixture.Ship->EndMooring();
    Fixture.Seconds(.2f);
    AnimationNamed(*this, Hull, TEXT("BattleMode_Enter"));
    TestFalse(TEXT("Repeated release cannot redeploy the evaluated gear and ramp"),
              PoseChanged(FlightPose, Hull->GetBoneSpaceTransforms()));

    // A real pad departure still owns the authored takeoff sequence after depot release loses it.
    Fixture.Ship->SetDockingTarget(Fixture.Ship->GetActorLocation(), FRotator::ZeroRotator);
    Fixture.Ship->FinishDocking();
    const TArray<FTransform> LandedPose = Hull->GetBoneSpaceTransforms();
    TestTrue(TEXT("Positive control: the settled pad pose differs from flight"), PoseChanged(FlightPose, LandedPose));
    Fixture.Ship->BeginTakeoff(Fixture.Ship->GetActorLocation() + FVector(0, 0, 700), FRotator::ZeroRotator);
    if (!AnimationNamed(*this, Hull, TEXT("Landing_Off")))
        return false;
    Fixture.Seconds(.5f);
    TestTrue(TEXT("Native station takeoff still advances the actual gear and ramp pose"),
             PoseChanged(LandedPose, Hull->GetBoneSpaceTransforms()));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSClassicLaunchPresentation, "SpaceSurvival.Presentation.ClassicLaunchPresentation",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSClassicLaunchPresentation::RunTest(const FString &)
{
    FSSVisualRigWorld Fixture;
    if (!Fixture.Initialize(*this, true))
        return false;
    ASSShip *Ship = Fixture.Ship;
    auto *Fill = Ship->FindComponentByClass<UPointLightComponent>();
    if (!TestNotNull(TEXT("Classic flight fill exists"), Fill) ||
        !TestNotNull(TEXT("Classic parked ship has its initial static hull"), Ship->HullMesh->GetStaticMesh().Get()))
        return false;
    TestEqual(TEXT("Parked pawn initially displays the previous Starter selection"),
              Ship->HullMesh->GetStaticMesh()->GetPathName(), FString(ASSShip::HullAssetPath(SS::Ship::Starter)));
    Ship->SetDockingTarget(Ship->GetActorLocation(), FRotator::ZeroRotator);
    Ship->FinishDocking();
    TestFalse(TEXT("Parked pilot leaves the cockpit"), Ship->Pilot->IsVisible());
    TestFalse(TEXT("Parked flight fill is off"), Fill->IsVisible());

    // Seed the committed loadout without invoking persistence. This is the same native launch entry
    // GameMode calls after StartNewRun has accepted and saved the new selection.
    auto &Run = Fixture.Instance->Session.run;
    Run.ship = SS::Ship::Agile;
    Run.tiers[0] = 3;
    const std::string RunId = Run.id;
    Ship->BeginTakeoff(Ship->GetActorLocation() + FVector(0, 0, 700), FRotator::ZeroRotator);
    TestEqual(TEXT("The existing pawn refreshes to the selected Agile hull"),
              Ship->HullMesh->GetStaticMesh()->GetPathName(), FString(ASSShip::HullAssetPath(SS::Ship::Agile)));
    TestTrue(TEXT("Agile open-cockpit pilot is visible again"), Ship->Pilot->IsVisible());
    TestTrue(TEXT("Classic takeoff restores its flight fill"), Fill->IsVisible());
    TestTrue(TEXT("Loadout presentation leaves run identity and upgrades intact"),
             Run.id == RunId && Run.tiers[0] == 3);
    TestTrue(TEXT("The selected hull remains on the same possessed flight pawn"),
             Ship == Fixture.Controller->GetPawn() && Ship->HullMesh->IsVisible() && !Ship->HasFlightHull());
    const FVector Before = Ship->GetActorLocation();
    Fixture.Seconds(.5f);
    TestTrue(TEXT("The reused Classic pawn actually lifts while its pilot remains visible"),
             Ship->GetActorLocation().Z > Before.Z && Ship->Pilot->IsVisible());
    return true;
}

#if WITH_EDITOR
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPhoenixGearGeometry, "SpaceSurvival.Presentation.PhoenixGearGeometry",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSPhoenixGearGeometry::RunTest(const FString &)
{
    USkeletalMesh *Mesh = LoadObject<USkeletalMesh>(
        nullptr, TEXT("/Game/Stellar_Phoenix/Spaceship/Meshes/Stellar_Phoenix.Stellar_Phoenix"));
    if (!TestNotNull(TEXT("Supplied Phoenix geometry resolves"), Mesh))
        return false;
    FSkeletalMeshModel *Model = Mesh->GetImportedModel();
    if (!TestTrue(TEXT("Imported source vertices available for collision measurement"),
                  Model && !Model->LODModels.IsEmpty()))
        return false;
    const FReferenceSkeleton &Skeleton = Mesh->GetRefSkeleton();
    TArray<FTransform> Bind = Skeleton.GetRefBonePose();
    TArray<FBox> Bounds;
    TArray<int32> Counts, BlendedCounts;
    Bounds.Init(FBox(ForceInit), Bind.Num());
    Counts.Init(0, Bind.Num());
    BlendedCounts.Init(0, Bind.Num());
    for (int32 Bone = 0; Bone < Bind.Num(); ++Bone)
    {
        const int32 Parent = Skeleton.GetParentIndex(Bone);
        if (Parent != INDEX_NONE)
            Bind[Bone] *= Bind[Parent];
    }
    for (const FSkelMeshSection &Section : Model->LODModels[0].Sections)
        for (const FSoftSkinVertex &Vertex : Section.SoftVertices)
        {
            int32 Strongest = 0;
            for (int32 Index = 1; Index < MAX_TOTAL_INFLUENCES; ++Index)
                if (Vertex.InfluenceWeights[Index] > Vertex.InfluenceWeights[Strongest])
                    Strongest = Index;
            if (Vertex.InfluenceWeights[Strongest] == 0)
                continue;
            const int32 Bone = Section.BoneMap[Vertex.InfluenceBones[Strongest]];
            Bounds[Bone] += Bind[Bone].InverseTransformPosition(FVector(Vertex.Position));
            ++Counts[Bone];
            if (Vertex.InfluenceWeights[Strongest] != MAX_uint16)
                ++BlendedCounts[Bone];
        }
    for (const FSSPhoenixGearBounds &Gear : SSPhoenixGearBounds)
    {
        const int32 Bone = Skeleton.FindBoneIndex(Gear.Bone);
        if (!TestTrue(TEXT("Every parked collider names a real source mesh bone"), Bone != INDEX_NONE))
            continue;
        TestEqual(TEXT("Measured gear part retains its actual rigid vertices"), Counts[Bone], Gear.Vertices);
        TestEqual(TEXT("Rigid bone attachment accurately follows every measured gear vertex"), BlendedCounts[Bone], 0);
        TestTrue(TEXT("Collision bounds come from the supplied vertices within their recorded precision"),
                 Bounds[Bone].Min.Equals(Gear.Min, .00051) && Bounds[Bone].Max.Equals(Gear.Max, .00051));
    }
    auto Receipt = MakeShared<FJsonObject>();
    Receipt->SetStringField(TEXT("mesh"), Mesh->GetPathName());
    TArray<TSharedPtr<FJsonValue>> Bones;
    for (int32 Bone = 0; Bone < Bind.Num(); ++Bone)
    {
        auto Record = MakeShared<FJsonObject>();
        Record->SetStringField(TEXT("bone"), Skeleton.GetBoneName(Bone).ToString());
        Record->SetNumberField(TEXT("vertices"), Counts[Bone]);
        Record->SetNumberField(TEXT("blended_vertices"), BlendedCounts[Bone]);
        Record->SetStringField(TEXT("bind_component_transform"), Bind[Bone].ToString());
        if (Bounds[Bone].IsValid)
        {
            Record->SetStringField(TEXT("bone_local_min"), Bounds[Bone].Min.ToString());
            Record->SetStringField(TEXT("bone_local_max"), Bounds[Bone].Max.ToString());
            AddInfo(FString::Printf(TEXT("Phoenix geometry %s vertices=%d min=%s max=%s"),
                                    *Skeleton.GetBoneName(Bone).ToString(), Counts[Bone], *Bounds[Bone].Min.ToString(),
                                    *Bounds[Bone].Max.ToString()));
        }
        Bones.Add(MakeShared<FJsonValueObject>(Record));
    }
    Receipt->SetArrayField(TEXT("bones"), Bones);
    auto Durations = MakeShared<FJsonObject>();
    for (const TCHAR *Name :
         {TEXT("BattleMode_Exit"), TEXT("Landing_On"), TEXT("Landing_Off"), TEXT("BattleMode_Enter")})
    {
        UAnimSequence *Clip = LoadObject<UAnimSequence>(
            nullptr, *FString::Printf(TEXT("/Game/Stellar_Phoenix/Spaceship/Animation/%s.%s"), Name, Name));
        if (TestNotNull(TEXT("Authored transition clip resolves"), Clip))
        {
            Durations->SetNumberField(Name, Clip->GetPlayLength());
            AddInfo(FString::Printf(TEXT("Phoenix clip %s length=%.6f seconds"), Name, Clip->GetPlayLength()));
        }
    }
    Receipt->SetObjectField(TEXT("durations"), Durations);
    FSSVisualRigWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    USkeletalMeshComponent *Hull = Fixture.Rig->GetHull();
    Fixture.Rig->PlayLanding();
    Fixture.Seconds(Hull->GetSingleNodeInstance()->GetLength() + .1f);
    Fixture.Seconds(Hull->GetSingleNodeInstance()->GetLength() + .1f);
    for (int32 Bone = 0; Bone < Bounds.Num(); ++Bone)
        if (Bounds[Bone].IsValid)
        {
            const FTransform BoneToShip =
                Hull->GetBoneTransform(Bone).GetRelativeTransform(Fixture.Ship->GetActorTransform());
            const FBox Landed = Bounds[Bone].TransformBy(BoneToShip);
            auto Record = Bones[Bone]->AsObject();
            Record->SetStringField(TEXT("landed_ship_min"), Landed.Min.ToString());
            Record->SetStringField(TEXT("landed_ship_max"), Landed.Max.ToString());
            Record->SetStringField(TEXT("landed_bone_to_ship"), BoneToShip.ToString());
        }
    FString Json;
    FJsonSerializer::Serialize(Receipt, TJsonWriterFactory<>::Create(&Json));
    const FString Folder = FPaths::ProjectDir() / TEXT("Artifacts/PhoenixPresentation");
    IFileManager::Get().MakeDirectory(*Folder, true);
    TestTrue(TEXT("Save bounded measured-geometry receipt"),
             FFileHelper::SaveStringToFile(Json, *(Folder / TEXT("gear-geometry.json")),
                                           FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM));
    return true;
}
#endif

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPhoenixParkedCollision, "SpaceSurvival.Presentation.PhoenixParkedCollision",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSPhoenixParkedCollision::RunTest(const FString &)
{
    FSSVisualRigWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    USkeletalMeshComponent *Hull = Fixture.Rig->GetHull();
    const FSSHullDefinition Definition(ESSHullIdentity::StellarPhoenix);
    Fixture.Ship->SetActorLocation(FVector(0, 0, Definition.DockClearanceAboveDeck));
    Fixture.Rig->PlayLanding(3.f);
    Fixture.Seconds(3.f);
    if (!AnimationNamed(*this, Hull, TEXT("Landing_On")))
        return false;
    TestTrue(TEXT("Whole authored landing sequence completes during the production three-second descent"),
             Hull->GetSingleNodeInstance()->GetCurrentTime() >= Hull->GetSingleNodeInstance()->GetLength() - .025f);
    UPhysicsAsset *Physics = Hull->GetPhysicsAsset();
    if (!TestNotNull(TEXT("Parked hull resolves its private supplied-geometry derivative"), Physics))
        return false;
    TestTrue(TEXT("Rig uses the private parked physics asset instead of the coarse vendor feet"),
             Physics->GetPathName() ==
                 TEXT("/Game/SpaceSurvival/Licensed/PhoenixPresentation/PA_PhoenixParked.PA_PhoenixParked"));
    UPhysicsAsset *Original = Hull->GetSkeletalMeshAsset()->GetPhysicsAsset();
    TestTrue(TEXT("Licensed skeletal mesh keeps its original thirteen-shape physics asset"),
             Original && Original != Physics && Original->SkeletalBodySetups.Num() == 1 &&
                 Original->SkeletalBodySetups[0]->AggGeom.GetElementCount() == 13);
    TestTrue(TEXT("Private parked hull retains ten source shapes, including its cargo ramp"),
             Physics->SkeletalBodySetups.Num() == 1 && Physics->SkeletalBodySetups[0]->AggGeom.GetElementCount() == 10);
    AddInfo(FString::Printf(TEXT("Phoenix parked physics asset %s has %d authored bodies"), *Physics->GetPathName(),
                            Physics->SkeletalBodySetups.Num()));
    Fixture.Rig->SetStationCollision(true);
    Fixture.Seconds(.05f);
    TestTrue(TEXT("Parked hull queries block walkers without another simulated body"),
             Hull->GetCollisionEnabled() == ECollisionEnabled::QueryOnly && !Hull->IsSimulatingPhysics() &&
                 Hull->GetCollisionResponseToChannel(ECC_Pawn) == ECR_Block);

    const UCapsuleComponent *WalkerCapsule = GetDefault<ASSWalker>()->GetCapsuleComponent();
    const float Radius = WalkerCapsule->GetUnscaledCapsuleRadius();
    const FCollisionShape Capsule = FCollisionShape::MakeCapsule(Radius, WalkerCapsule->GetUnscaledCapsuleHalfHeight());
    FCollisionQueryParams Query(SCENE_QUERY_STAT(PhoenixParkedLegs), false, Fixture.Ship);
    const float HalfHeight = WalkerCapsule->GetUnscaledCapsuleHalfHeight();
    int32 GearBodies = 0, GearHits = 0;
    FVector LastStart = FVector::ZeroVector, LastEnd = FVector::ZeroVector;
    for (const FSSPhoenixGearBounds &Gear : SSPhoenixGearBounds)
    {
        UBoxComponent *Box =
            NamedComponent<UBoxComponent>(Hull->GetOwner(), *FString::Printf(TEXT("Parked_%s"), Gear.Bone));
        if (!TestNotNull(TEXT("Measured individual gear part has its own collision shape"), Box))
            continue;
        TestTrue(TEXT("Each shape follows the exact animated bone carrying its visible mesh vertices"),
                 Box->GetAttachParent() == Hull && Box->GetAttachSocketName() == FName(Gear.Bone));
        TestTrue(TEXT("Gear can only query-block the walker while parked"),
                 Box->GetCollisionEnabled() == ECollisionEnabled::QueryOnly && !Box->IsSimulatingPhysics() &&
                     Box->GetCollisionResponseToChannel(ECC_Pawn) == ECR_Block);
        if (!FString(Gear.Bone).Contains(TEXT("_Leg_")))
            continue;
        ++GearBodies;
        const FBox Bounds = Box->Bounds.GetBox();
        TestTrue(TEXT("Authored parked feet stand on the pad instead of floating two metres above it"),
                 Bounds.Min.Z >= -.1f && Bounds.Min.Z < 5.f);
        FVector Center = Bounds.GetCenter();
        Center.Z = HalfHeight;
        // Approach each rear foot from the centre aisle. The right nacelle overhangs its outer
        // approach; starting inside that real obstacle would test the engine, not walking into gear.
        const FVector Side = Fixture.Ship->GetActorRightVector() * (Center.Y > 100.f ? -1.f : 1.f);
        const float Travel = Bounds.GetExtent().Y + Radius * 2.f;
        LastStart = Center + Side * Travel;
        LastEnd = Center - Side * Travel;
        TestFalse(TEXT("The walking approach starts in reachable space outside all ship geometry"),
                  Fixture.World->OverlapBlockingTestByChannel(LastStart, FQuat::Identity, ECC_Pawn, Capsule, Query));
        FHitResult Hit;
        const bool Blocked =
            Fixture.World->SweepSingleByChannel(Hit, LastStart, LastEnd, FQuat::Identity, ECC_Pawn, Capsule, Query);
        const bool HitAuthoredGear = Blocked && Hit.GetComponent() == Box;
        if (HitAuthoredGear)
            ++GearHits;
        AddInfo(FString::Printf(TEXT("Phoenix walker sweep bone=%s center=%s hit=%s blocking=%d penetrating=%d"),
                                Gear.Bone, *Center.ToString(), *GetNameSafe(Hit.GetComponent()), Blocked,
                                Hit.bStartPenetrating));
    }
    TestEqual(TEXT("All three separate landing feet are measured and present"), GearBodies, 3);
    TestEqual(TEXT("Walking capsule is blocked at all three actual animated landing feet"), GearHits, 3);
#if WITH_EDITOR
    const double FrontFootFloor = LowestPosedSurfaceInColumn(Hull, FBox2D(FVector2D(610, -48), FVector2D(825, 48)));
    TestTrue(TEXT("Posed triangle measurement finds the actual front foot at deck height"),
             FrontFootFloor >= -.1f && FrontFootFloor < 5.f);
    const double FrontHeadroom = LowestPosedSurfaceInColumn(
        Hull, FBox2D(FVector2D(650 - Radius, 300 - Radius), FVector2D(780 + Radius, 300 + Radius)));
    AddInfo(FrontHeadroom == DBL_MAX
                ? TEXT("Front-side walking path has no posed hull triangles anywhere above its capsule envelope")
                : FString::Printf(TEXT("Front-side path lowest posed surface: %.3f cm; standing height: %.3f cm"),
                                  FrontHeadroom, HalfHeight * 2.f));
    TestTrue(TEXT("Actual posed hull triangles leave standing headroom beside the front foot"),
             FrontHeadroom > HalfHeight * 2.f);
#endif
    FHitResult FrontGap;
    TestFalse(
        TEXT("Real standing capsule passes beside the front foot where its old nine-metre box blocked empty floor"),
        Fixture.World->SweepSingleByChannel(FrontGap, FVector(650, 300, HalfHeight), FVector(780, 300, HalfHeight),
                                            FQuat::Identity, ECC_Pawn, Capsule, Query));
    FHitResult BodyHit, RampHit;
    TestTrue(
        TEXT("Parked nose remains solid above the actual gear"),
        Fixture.World->LineTraceSingleByChannel(BodyHit, FVector(700, 0, 800), FVector(700, 0, 300), ECC_Pawn, Query) &&
            BodyHit.GetComponent() == Hull);
    TestTrue(TEXT("Supplied deployed cargo ramp remains solid"),
             Fixture.World->LineTraceSingleByChannel(RampHit, FVector(-1150, 0, 400), FVector(-1150, 0, 100), ECC_Pawn,
                                                     Query) &&
                 RampHit.GetComponent() == Hull);
    // The real fuselage has less than standing headroom along parts of its centreline. Only the new
    // gear proxies promise an open gap; the actual low hull must retain its own blocking collision.
    FCollisionQueryParams GearOnly = Query;
    TInlineComponentArray<UPrimitiveComponent *> PresentationPrimitives(Hull->GetOwner());
    for (UPrimitiveComponent *Primitive : PresentationPrimitives)
        if (!Primitive->GetName().StartsWith(TEXT("Parked_")))
            GearOnly.AddIgnoredComponent(Primitive);
    FHitResult UnderHull;
    TestFalse(TEXT("New gear proxies leave their middle gap open instead of enclosing the hull footprint"),
              Fixture.World->SweepSingleByChannel(UnderHull, FVector(-400, 0, HalfHeight), FVector(400, 0, HalfHeight),
                                                  FQuat::Identity, ECC_Pawn, Capsule, GearOnly));

    Fixture.Rig->PlayTakeoff();
    Fixture.Seconds(.05f);
    TestTrue(TEXT("Takeoff removes parked collision before native flight resumes"),
             !Hull->GetOwner()->GetActorEnableCollision() &&
                 Hull->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
    if (GearBodies > 0)
    {
        FHitResult Hit;
        TestFalse(
            TEXT("Previously blocked leg path no longer leaves an invisible flight obstacle"),
            Fixture.World->SweepSingleByChannel(Hit, LastStart, LastEnd, FQuat::Identity, ECC_Pawn, Capsule, Query));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPhoenixFlightHull, "SpaceSurvival.Flight.PhoenixHullCollision",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSPhoenixFlightHull::RunTest(const FString &)
{
    FSSVisualRigWorld Fixture;
    if (!Fixture.Initialize(*this) ||
        !TestTrue(TEXT("Default Phoenix has its authored flight compound"), Fixture.Ship->HasFlightHull()))
        return false;
    ASSShip *Ship = Fixture.Ship;
    auto *Compound = Ship->FindComponentByClass<USSFlightHullComponent>();
    if (!TestNotNull(TEXT("Fixed native collision component exists"), Compound))
        return false;
    TestTrue(TEXT("Authored hull is welded into the original native root"),
             Compound->IsWelded() && Compound->GetAttachParent() == Ship->Collision);
    TestEqual(TEXT("Deployment envelopes are excluded while rigid hull and both nacelles remain"),
              Compound->GetBodySetup()->AggGeom.ConvexElems.Num(), 11);
    for (const auto &Shape : Compound->GetBodySetup()->AggGeom.ConvexElems)
        TestFalse(TEXT("Contact geometry does not silently change the flight body's mass or inertia"),
                  Shape.GetContributeToMass());
    Ship->EndMooring();
    const FVector Origin = Ship->GetActorLocation();
    TestTrue(TEXT("Compound preserves the calibrated native body mass"),
             FMath::IsNearlyEqual(Ship->Collision->GetMass(), 4687.5f, .1f));
    TestTrue(TEXT("Compound leaves the original centre of mass at the native pivot"),
             Ship->Collision->GetCenterOfMass().Equals(Origin, .1f));
    const double SphereInertia = .4 * 4687.5 * 105. * 105.;
    TestTrue(TEXT("Added shapes preserve the calibrated inertia tensor"),
             Ship->Collision->GetInertiaTensor().Equals(FVector(SphereInertia), SphereInertia * .01));
    Ship->BeginMooring();
    auto Contact = [&](const FVector &From, const FVector &To, float Radius = 15.f)
    {
        FHitResult Hit;
        return Ship->SweepFlightContact(Hit, Origin + From, Origin + To, Radius);
    };
    TestTrue(TEXT("A nose strike reaches the visible ship long before the old origin sphere"),
             Contact(FVector(1450, 0, 480), FVector(800, 0, 480)));
    TestTrue(TEXT("The left authored nacelle is solid in flight"),
             Contact(FVector(-650, -1500, 350), FVector(-650, -600, 350)));
    TestTrue(TEXT("The right authored nacelle is solid in flight"),
             Contact(FVector(-650, 1500, 350), FVector(-650, 600, 350)));
    TestFalse(TEXT("Empty space beside the forward hull remains clear inside its overall bounding box"),
              Contact(FVector(400, 750, 900), FVector(400, 750, -100)));
    TestFalse(TEXT("Retracted front gear does not leave the supplied deployed-foot envelope in flight"),
              Contact(FVector(700, 0, -50), FVector(700, 0, 70), 10.f));

    // Exercise a real off-centre Chaos collision, not just our query wrapper. This obstacle misses
    // the old origin sphere; a wing contact must produce damage and remain recoverable by the gyro.
    Ship->EndMooring();
    Ship->SetActorTickEnabled(false);
    Ship->FindComponentByClass<UThrusterManagerComp>()->SetComponentTickEnabled(false);
    Ship->FindComponentByClass<UGyroManagerComp>()->SetComponentTickEnabled(false);
    auto *Obstacle = Fixture.World->SpawnActor<AActor>();
    auto *Box = NewObject<UBoxComponent>(Obstacle);
    Obstacle->SetRootComponent(Box);
    Box->SetBoxExtent(FVector(140, 30, 140));
    Box->SetCollisionObjectType(ECC_WorldStatic);
    Box->SetCollisionResponseToAllChannels(ECR_Block);
    Box->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Box->RegisterComponent();
    Obstacle->SetActorLocation(Origin + FVector(-650, -1200, 350));
    Ship->Collision->SetPhysicsLinearVelocity(FVector(0, -1600, 0));
    Ship->Collision->SetPhysicsAngularVelocityInRadians(FVector::ZeroVector);
    const double Vitality = Fixture.Instance->Session.run.hull + Fixture.Instance->Session.run.shield;
    Fixture.Seconds(.4f);
    TestTrue(TEXT("A physical wing collision reaches the native damage authority"),
             Fixture.Instance->Session.run.hull + Fixture.Instance->Session.run.shield < Vitality);
    const FVector ImpactSpin = Ship->Collision->GetPhysicsAngularVelocityInRadians();
    TestTrue(TEXT("Off-centre impact produces finite angular response"),
             !ImpactSpin.ContainsNaN() && ImpactSpin.Size() > .01f);
    AddInfo(FString::Printf(TEXT("Measured wing impact angular speed %.2f degrees/sec"),
                            FMath::RadiansToDegrees(ImpactSpin.Size())));
    Obstacle->Destroy();
    Ship->FindComponentByClass<UThrusterManagerComp>()->SetComponentTickEnabled(true);
    Ship->FindComponentByClass<UGyroManagerComp>()->SetComponentTickEnabled(true);
    Ship->SetActorTickEnabled(true);
    Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 0, false, false);
    Fixture.Seconds(3.f);
    TestTrue(TEXT("Existing gyro recovers control after a glancing full-hull impact"),
             Ship->Collision->GetPhysicsAngularVelocityInRadians().Size() < FMath::DegreesToRadians(10.f));

    Ship->SetDockingTarget(Origin, FRotator::ZeroRotator);
    TestEqual(TEXT("Scripted descent disables the fixed flight compound"), Compound->GetCollisionEnabled(),
              ECollisionEnabled::NoCollision);
    Fixture.Seconds(3.f);
    Ship->FinishDocking();
    Ship->BeginTakeoff(Origin + FVector(0, 0, 700), FRotator::ZeroRotator);
    TestEqual(TEXT("Flight geometry remains disabled through controlled lift"), Compound->GetCollisionEnabled(),
              ECollisionEnabled::NoCollision);
    Fixture.Seconds(3.1f);
    TestTrue(TEXT("Lift completion restores the same welded collision body without changing mass"),
             Compound->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics && Compound->IsWelded() &&
                 FMath::IsNearlyEqual(Ship->Collision->GetMass(), 4687.5f, .1f));
    return true;
}

#endif
