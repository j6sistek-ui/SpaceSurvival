#include "SSShipVisualRig.h"
#include "SSShip.h"
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
#include "Components/PrimitiveComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/AutomationTest.h"
#include "NiagaraSystem.h"
#include "PhysicsEngine/PhysicsThrusterComponent.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
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

    bool Initialize(FAutomationTestBase &Test)
    {
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
        if (!Test.TestNotNull(TEXT("Native pawn owns visual adapter"), Rig) ||
            !Test.TestTrue(TEXT("Licensed Phoenix Blueprint actually loaded"), Rig->HasBlueprintRig()))
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
    const UAnimSingleNodeInstance *Animation = Mesh->GetSingleNodeInstance();
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
    if (!TestNotNull(TEXT("Parked hull retains its supplied physics asset"), Physics))
        return false;
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
        const FVector Side = Fixture.Ship->GetActorRightVector();
        const float Travel = Bounds.GetExtent().Y + Radius * 2.f;
        LastStart = Center + Side * Travel;
        LastEnd = Center - Side * Travel;
        FHitResult Hit;
        const bool Blocked =
            Fixture.World->SweepSingleByChannel(Hit, LastStart, LastEnd, FQuat::Identity, ECC_Pawn, Capsule, Query);
        const bool HitAuthoredGear = Blocked && Hit.GetComponent() == Box;
        if (HitAuthoredGear)
            ++GearHits;
        AddInfo(FString::Printf(TEXT("Phoenix walker sweep bone=%s center=%s hit=%s blocking=%d"), Gear.Bone,
                                *Center.ToString(), *GetNameSafe(Hit.GetComponent()), Blocked));
    }
    TestEqual(TEXT("All three separate landing feet are measured and present"), GearBodies, 3);
    TestEqual(TEXT("Walking capsule is blocked at all three actual animated landing feet"), GearHits, 3);
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
#endif
