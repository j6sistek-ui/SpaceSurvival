#include "SSShipVisualRig.h"
#include "SSShip.h"
#include "SSContentTypes.h"
#include "SSPhoenixGearBounds.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Camera/CameraComponent.h"
#include "Components/ArrowComponent.h"
#include "Components/AudioComponent.h"
#include "Components/BoxComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/MovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "PhysicsEngine/PhysicsThrusterComponent.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/BodyInstance.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
#if WITH_EDITOR
#include "StaticMeshCompiler.h"
#endif

namespace
{
// The source Blueprint's demo graph references missing projectile/occupant classes. This private
// derivative preserves its complete SCS rig, with that unrelated demo logic removed by the author script.
const TCHAR *PhoenixBlueprint =
    TEXT("/Game/SpaceSurvival/Licensed/PhoenixPresentation/BP_PhoenixPresentation.BP_PhoenixPresentation_C");

UAnimSequence *LoadClip(const FString &Path, const USkeletalMeshComponent *Mesh)
{
    if (Path.IsEmpty() || !Mesh || !Mesh->GetSkeletalMeshAsset())
        return nullptr;
    UAnimSequence *Clip = LoadObject<UAnimSequence>(nullptr, *Path);
    return Clip && Clip->GetSkeleton() == Mesh->GetSkeletalMeshAsset()->GetSkeleton() ? Clip : nullptr;
}
} // namespace

USSShipVisualRig::USSShipVisualRig()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;
    PrimaryComponentTick.TickGroup = TG_PostPhysics;
}

bool USSShipVisualRig::Initialize(ASSShip *Ship, const FSSHullDefinition &Definition)
{
    ReleaseRig();
    if (!Ship || Ship != GetOwner() || !GetWorld() || Definition.Identity != ESSHullIdentity::StellarPhoenix)
        return false;
    UClass *RigClass = LoadClass<APawn>(nullptr, PhoenixBlueprint);
    if (!RigClass)
        return false;

    const FTransform SpawnTransform = Ship->GetActorTransform();
    RigPawn = GetWorld()->SpawnActorDeferred<APawn>(RigClass, SpawnTransform, Ship, nullptr,
                                                    ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if (!RigPawn)
        return false;
    // These must precede FinishSpawning: APawn's component initialization otherwise lets the vendor
    // AutoPossessPlayer default take the controller away from the native flight pawn.
    RigPawn->AutoPossessPlayer = EAutoReceiveInput::Disabled;
    RigPawn->AutoPossessAI = EAutoPossessAI::Disabled;
    RigPawn->AutoReceiveInput = EAutoReceiveInput::Disabled;
    RigPawn->PrimaryActorTick.bCanEverTick = false;
    RigPawn->PrimaryActorTick.bStartWithTickEnabled = false;
    RigPawn->SetActorEnableCollision(false);
    RigPawn->SetReplicates(false);
    RigPawn->FinishSpawning(SpawnTransform);
    RigPawn->DisableInput(nullptr);
    RigPawn->SetActorTickEnabled(false);
    RigPawn->SetActorEnableCollision(false);

    // Keep the Blueprint's actual scene tree, including its offset engine pivots, bone attachments,
    // separate airbrake rig and muzzle arrows. Only its demo gameplay/camera components are disabled.
    TInlineComponentArray<UActorComponent *> Components(RigPawn);
    for (UActorComponent *Component : Components)
    {
        Component->SetCanEverAffectNavigation(false);
        Component->SetComponentTickEnabled(false);
        if (auto *Primitive = Cast<UPrimitiveComponent>(Component))
        {
            Primitive->SetSimulatePhysics(false);
            Primitive->SetEnableGravity(false);
            Primitive->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Primitive->SetGenerateOverlapEvents(false);
        }
        if (auto *Mesh = Cast<USkeletalMeshComponent>(Component))
        {
            Mesh->SetAllBodiesSimulatePhysics(false);
            Mesh->bPauseAnims = false;
            Mesh->bNoSkeletonUpdate = false;
            Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
            Mesh->SetComponentTickEnabled(true);
            if (Mesh->GetSkeletalMeshAsset() && Mesh->GetSkeletalMeshAsset()->GetPathName() == Definition.MeshPath)
                Hull = Mesh;
            else if (Mesh->GetName().StartsWith(TEXT("Stellar_Phoenix_AirBrake")))
                AirBrakes.Add(Mesh);
        }
        if (auto *Arrow = Cast<UArrowComponent>(Component))
        {
            const FString Name = Arrow->GetName();
            if (Name == TEXT("EngineLeft") || Name == TEXT("EngineRight"))
            {
                EnginePivots.Add(Arrow);
                EngineRestRotations.Add(Arrow->GetRelativeRotation().Quaternion());
            }
            else if (Name.StartsWith(TEXT("ProjectileSpawn")))
                Muzzles.Add(Arrow);
        }
        if (auto *Effect = Cast<UNiagaraComponent>(Component))
        {
            Exhausts.Add(Effect);
            ExhaustRestScales.Add(Effect->GetRelativeScale3D());
            Effect->SetComponentTickEnabled(true);
        }
        if (auto *Thruster = Cast<UPhysicsThrusterComponent>(Component))
        {
            Thruster->ThrustStrength = 0.f;
            Thruster->Deactivate();
        }
        if (auto *Movement = Cast<UMovementComponent>(Component))
            Movement->Deactivate();
        if (auto *Camera = Cast<UCameraComponent>(Component))
            Camera->Deactivate();
        if (auto *Boom = Cast<USpringArmComponent>(Component))
            Boom->Deactivate();
        if (auto *Text = Cast<UTextRenderComponent>(Component))
        {
            Text->SetVisibility(false);
            Text->SetHiddenInGame(true);
        }
        if (auto *Audio = Cast<UAudioComponent>(Component))
            Audio->Stop();
        if (auto *Light = Cast<UPointLightComponent>(Component))
        {
            // Retain the reviewed deep-space fill while using the supplied Blueprint's lamp.
            Light->SetIntensity(Definition.HullLightIntensity);
            Light->SetAttenuationRadius(Definition.HullLightRadius);
            Light->SetLightColor(FLinearColor(Definition.HullLightColor));
            Light->SetCastShadows(false);
        }
    }
    if (!Hull)
    {
        ReleaseRig();
        return false;
    }
    UPhysicsAsset *ParkedPhysics = LoadObject<UPhysicsAsset>(
        nullptr, TEXT("/Game/SpaceSurvival/Licensed/PhoenixPresentation/PA_PhoenixParked.PA_PhoenixParked"));
    if (!ParkedPhysics)
    {
        UE_LOG(LogTemp, Error, TEXT("Phoenix parked physics is missing; run AuthorPhoenixParkedPhysics.py"));
        ReleaseRig();
        return false;
    }
    // The source PA's three foot boxes span empty floor as far as 4.85 metres from the centreline.
    // Its private derivative retains the hull and ramp; the animated part bounds below own the gear.
    Hull->SetPhysicsAsset(ParkedPhysics, true);
    RigPawn->AttachToComponent(Ship->GetRootComponent(), FAttachmentTransformRules::KeepRelativeTransform);
    RigPawn->SetActorRelativeTransform(
        FTransform(FRotator(0.f, Definition.MeshYaw, 0.f), FVector::ZeroVector, FVector(Definition.HullScale)));
    Hull->SetVisibility(true);
    for (const FSSPhoenixGearBounds &Gear : SSPhoenixGearBounds)
    {
        const FName Bone(Gear.Bone);
        if (Hull->GetBoneIndex(Bone) == INDEX_NONE)
            continue;
        UBoxComponent *Box = NewObject<UBoxComponent>(RigPawn, FName(*FString::Printf(TEXT("Parked_%s"), Gear.Bone)));
        Box->SetupAttachment(Hull, Bone);
        Box->SetRelativeLocation((Gear.Min + Gear.Max) * .5);
        // The stored measurements round to 0.001 bone-local units. Half one unit of that precision
        // keeps the measured vertices inside the narrow part bounds (0.05 cm at authored bone scale).
        Box->SetBoxExtent((Gear.Max - Gear.Min) * .5 + FVector(.0005));
        Box->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Box->SetGenerateOverlapEvents(false);
        Box->SetCanEverAffectNavigation(false);
        Box->CanCharacterStepUpOn = ECB_No;
        RigPawn->AddInstanceComponent(Box);
        Box->RegisterComponent();
        GearColliders.Add(Box);
    }

    // Rigid-vertex measurements in PhoenixGearGeometry identify the walking faces, not the raised
    // edge trim. Bone-local units are metres at the supplied bone scale of 100. The toe's face runs
    // Y=-.225..2.533, Z=-.022..-.010; the main central face runs (-2.371,.034)..(-.174,.266).
    // Their overlapping upper faces make a continuous ~27-degree slope. Narrow supports stay within
    // both rendered panels, extend to the visible toe, and follow their separate animated bones.
    const auto AddRamp = [this](const TCHAR *Name, const TCHAR *Bone, FVector Start, FVector End, float HalfWidth)
    {
        if (Hull->GetBoneIndex(FName(Bone)) == INDEX_NONE)
            return;
        UBoxComponent *Box = NewObject<UBoxComponent>(RigPawn, FName(Name));
        const FVector Along = (End - Start).GetSafeNormal();
        const FQuat Rotation = FRotationMatrix::MakeFromYZ(Along, FVector::UpVector).ToQuat();
        const FVector Normal = Rotation.GetAxisZ();
        constexpr float HalfThickness = .025f;
        Box->SetupAttachment(Hull, FName(Bone));
        Box->SetRelativeRotation(Rotation);
        Box->SetRelativeLocation((Start + End) * .5 - Normal * HalfThickness);
        Box->SetBoxExtent(FVector(HalfWidth, FVector::Distance(Start, End) * .5, HalfThickness));
        Box->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Box->SetGenerateOverlapEvents(false);
        Box->SetCanEverAffectNavigation(false);
        Box->CanCharacterStepUpOn = ECB_Yes;
        RigPawn->AddInstanceComponent(Box);
        Box->RegisterComponent();
        RampColliders.Add(Box);
    };
    AddRamp(TEXT("BoardingRampToe"), TEXT("Cargo_Door_A_Mesh"), FVector(0, -.225, -.022), FVector(0, 2.533, -.010),
            1.14f);
    AddRamp(TEXT("BoardingRampMain"), TEXT("Cargo_Door_Mesh"), FVector(0, -2.884, -.020), FVector(0, .020, .2865),
            1.14f);

    LandingOn = LoadClip(Definition.LandingDeployClipPath, Hull);
    LandingOff = LoadClip(Definition.LandingStowClipPath, Hull);
    BattleEnter = LoadClip(Definition.FlightPoseClipPath, Hull);
    // This private mesh contains the supplied landed interior/chair/door triangles, not a
    // hull-sized primitive. It is never rendered or used for the simulated flight body.
    if (auto *Interior = LoadObject<UStaticMesh>(nullptr,
                                                 TEXT("/Game/SpaceSurvival/Licensed/PhoenixPresentation/"
                                                      "SM_PhoenixParkedInterior.SM_PhoenixParkedInterior"),
                                                 nullptr, LOAD_NoWarn | LOAD_Quiet))
    {
#if WITH_EDITOR
        // Editor cold loads can return before this mesh's physics data is ready. Unreal skips
        // creating physics for compiling static meshes; do not open the measured interior and
        // disable its old coarse envelopes before its real floor can support the walking pilot.
        // Cooked builds already have this data and never enter the editor compilation path.
        if (Interior->IsCompiling())
        {
            UE_LOG(LogTemp, Display, TEXT("SS_PHOENIX_INTERIOR_WAIT mesh=%s compiling=%d"), *Interior->GetPathName(),
                   Interior->IsCompiling());
            UStaticMesh *RequiredMeshes[] = {Interior};
            FStaticMeshCompilingManager::Get().FinishCompilation(RequiredMeshes);
            UE_LOG(LogTemp, Display, TEXT("SS_PHOENIX_INTERIOR_COMPILED mesh=%s compiling=%d"),
                   *Interior->GetPathName(), Interior->IsCompiling());
        }
#endif
        InteriorCollider = NewObject<UStaticMeshComponent>(RigPawn, TEXT("ParkedInterior"));
        InteriorCollider->SetupAttachment(Ship->GetRootComponent());
        InteriorCollider->SetStaticMesh(Interior);
        InteriorCollider->SetVisibility(false);
        InteriorCollider->SetHiddenInGame(true);
        InteriorCollider->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        InteriorCollider->SetGenerateOverlapEvents(false);
        InteriorCollider->SetCanEverAffectNavigation(false);
        InteriorCollider->CanCharacterStepUpOn = ECB_Yes;
        RigPawn->AddInstanceComponent(InteriorCollider);
        InteriorCollider->RegisterComponent();
    }

    // Native landed triangles put the rear floor/ceiling at Z230/494 and cockpit at
    // Z389/569 cm. Lower diffuse pools make the boarding route readable without the
    // old ceiling highlights. Shadow containment and parked-only visibility remain.
    const auto AddCabinLight =
        [this, Ship](const TCHAR *Name, FVector Location, float Lumens, float Radius, FLinearColor Color)
    {
        UPointLightComponent *Light = NewObject<UPointLightComponent>(RigPawn, FName(Name));
        Light->SetupAttachment(Ship->GetRootComponent());
        Light->SetMobility(EComponentMobility::Movable);
        Light->SetRelativeLocation(Location);
        Light->SetUseInverseSquaredFalloff(true);
        Light->SetIntensityUnits(ELightUnits::Lumens);
        Light->SetIntensity(Lumens);
        Light->SetAttenuationRadius(Radius);
        Light->SetLightColor(Color);
        Light->SetSourceRadius(9.f);
        Light->SetSpecularScale(.025f);
        Light->SetCastShadows(true);
        Light->SetVolumetricScatteringIntensity(0.f);
        Light->SetVisibility(false);
        RigPawn->AddInstanceComponent(Light);
        Light->RegisterComponent();
        CabinLights.Add(Light);
        return Light;
    };
    AddCabinLight(TEXT("BoardingThresholdLight"), FVector(-900, 0, 415), 450.f, 325.f, FLinearColor(.78f, .88f, 1.f));
    AddCabinLight(TEXT("BoardingRearCabinLight"), FVector(-600, 0, 420), 850.f, 460.f, FLinearColor(1.f, .90f, .78f));
    AddCabinLight(TEXT("BoardingStairApproachLight"), FVector(180, 0, 425), 550.f, 320.f,
                  FLinearColor(.78f, .88f, 1.f));
    AddCabinLight(TEXT("BoardingCockpitLight"), FVector(650, 0, 520), 700.f, 350.f, FLinearColor(1.f, .90f, .78f));

    UStaticMesh *DisplayPlane = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Plane.Plane"));
    UStaticMesh *DisplayCase = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    UMaterialInterface *CaseFinish = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/OutpostSandbox/Materials/M_OutpostGraphite.M_OutpostGraphite"));
    UMaterialInterface *NavigationDisplay = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/SpaceSurvival/Licensed/PhoenixCabin/M_CabinNavigation.M_CabinNavigation"));
    UMaterialInterface *SystemsDisplay = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/SpaceSurvival/Licensed/PhoenixCabin/M_CabinSystems.M_CabinSystems"));
    if (DisplayPlane && DisplayCase && CaseFinish && NavigationDisplay && SystemsDisplay)
    {
        const auto AddCabinDetail = [this, Ship](const TCHAR *Name, UStaticMesh *Mesh, UMaterialInterface *Material,
                                                 FVector Location, FVector Scale, FRotator Rotation)
        {
            UStaticMeshComponent *Detail = NewObject<UStaticMeshComponent>(RigPawn, FName(Name));
            Detail->SetupAttachment(Ship->GetRootComponent());
            Detail->SetMobility(EComponentMobility::Movable);
            Detail->SetStaticMesh(Mesh);
            Detail->SetMaterial(0, Material);
            Detail->SetRelativeLocation(Location);
            Detail->SetRelativeScale3D(Scale);
            Detail->SetRelativeRotation(Rotation);
            Detail->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Detail->SetGenerateOverlapEvents(false);
            Detail->SetCanEverAffectNavigation(false);
            Detail->SetCastShadow(false);
            Detail->SetVisibility(false);
            RigPawn->AddInstanceComponent(Detail);
            Detail->RegisterComponent();
            CabinDetails.Add(Detail);
        };
        // Rear ribs project to Y +/-168.845 cm. Move cases and panes 14 cm
        // inward so both complete displays sit in front of the ribs.
        for (int32 Index = 0; Index < 2; ++Index)
        {
            const float Side = Index == 0 ? -1.f : 1.f;
            const float X = Index == 0 ? -650.f : -400.f;
            AddCabinDetail(Index == 0 ? TEXT("CabinNavigationCase") : TEXT("CabinSystemsCase"), DisplayCase, CaseFinish,
                           FVector(X, Side * 166.5f, 380.f), FVector(.86f, .04f, .54f), FRotator::ZeroRotator);
            AddCabinDetail(Index == 0 ? TEXT("CabinNavigationDisplay") : TEXT("CabinSystemsDisplay"), DisplayPlane,
                           Index == 0 ? NavigationDisplay : SystemsDisplay, FVector(X, Side * 164.1f, 380.f),
                           FVector(.8f, .48f, 1.f), FRotator(0.f, Index == 0 ? 0.f : 180.f, 90.f));
        }
    }

    BattleExit = LoadClip(TEXT("/Game/Stellar_Phoenix/Spaceship/Animation/BattleMode_Exit.BattleMode_Exit"), Hull);
    if (!AirBrakes.IsEmpty())
        AirBrakeClip =
            LoadClip(TEXT("/Game/SpaceSurvival/Licensed/PhoenixPresentation/AirBrake.AirBrake"), AirBrakes[0]);
    for (USkeletalMeshComponent *BrakeMesh : AirBrakes)
    {
        BrakeMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
        BrakeMesh->SetAnimation(AirBrakeClip);
        BrakeMesh->SetPosition(0.f, false);
    }

    Muzzles.Sort([](const USceneComponent &A, const USceneComponent &B) { return A.GetName() < B.GetName(); });
    // There is no firing skeletal clip in this pack. Its authored firing animation is VFX_Shoot,
    // placed at the gun arrows; it never spawns a projectile or invokes a damage event here.
    if (UNiagaraSystem *Shot =
            LoadObject<UNiagaraSystem>(nullptr, TEXT("/Game/Stellar_Phoenix/Spaceship/VFX/VFX_Shoot.VFX_Shoot")))
        for (USceneComponent *Muzzle : Muzzles)
            if (UNiagaraComponent *Flash = UNiagaraFunctionLibrary::SpawnSystemAttached(
                    Shot, Muzzle, NAME_None, FVector::ZeroVector, FRotator::ZeroRotator,
                    EAttachLocation::KeepRelativeOffset, false, false))
                MuzzleFlashes.Add(Flash);
    Landing = true;
    PlayTakeoff();
    SetComponentTickEnabled(true);
    return true;
}

bool USSShipVisualRig::HasBlueprintRig() const
{
    return IsValid(RigPawn) && IsValid(Hull);
}

USkeletalMeshComponent *USSShipVisualRig::GetHull() const
{
    return Hull;
}

FBox USSShipVisualRig::GetHullBoundsInSpace(const FTransform &Space) const
{
    FBox Bounds(ForceInit);
    if (!HasBlueprintRig())
        return Bounds;
    TInlineComponentArray<UPrimitiveComponent *> Components(RigPawn);
    for (UPrimitiveComponent *Component : Components)
        if (Component->IsVisible() &&
            (Cast<USkeletalMeshComponent>(Component) || Cast<UStaticMeshComponent>(Component)))
            Bounds += Component->CalcBounds(Component->GetComponentTransform().GetRelativeTransform(Space)).GetBox();
    return Bounds;
}

bool USSShipVisualRig::GetParkedRampLanding(FTransform &LandingFrame, float &HalfWidth) const
{
    if (!Parked || !HasBlueprintRig() || RampColliders.Num() != 2)
        return false;
    const UBoxComponent *Toe = RampColliders[0];
    const UBoxComponent *Main = RampColliders[1];
    if (!IsValid(Toe) || !IsValid(Main) || !Toe->IsRegistered() || !Main->IsRegistered() ||
        !Toe->IsQueryCollisionEnabled() || !Main->IsQueryCollisionEnabled() || Toe->GetAttachParent() != Hull ||
        Main->GetAttachParent() != Hull || Toe->GetAttachSocketName() != FName(TEXT("Cargo_Door_A_Mesh")) ||
        Main->GetAttachSocketName() != FName(TEXT("Cargo_Door_Mesh")))
        return false;
    const FTransform ToePose = Toe->GetComponentTransform();
    const FVector Extent = Toe->GetUnscaledBoxExtent();
    const FVector Foot = ToePose.TransformPosition(FVector(0, Extent.Y, Extent.Z));
    FVector Outward = ToePose.GetUnitAxis(EAxis::Y);
    if (Foot.ContainsNaN() || FVector::DotProduct(ToePose.GetUnitAxis(EAxis::Z), FVector::UpVector) < .7f)
        return false;
    Outward.Z = 0.f;
    if (!Outward.Normalize())
        return false;
    HalfWidth = float(Toe->GetScaledBoxExtent().X);
    if (!FMath::IsFinite(HalfWidth) || HalfWidth <= 0.f)
        return false;
    LandingFrame = FTransform(FRotationMatrix::MakeFromXZ(Outward, FVector::UpVector).ToQuat(), Foot);
    return true;
}

void USSShipVisualRig::SetStationCollision(bool Enabled)
{
    Parked = Enabled;
    if (!HasBlueprintRig())
        return;
    for (UPointLightComponent *Light : CabinLights)
        Light->SetVisibility(Enabled);
    for (UStaticMeshComponent *Detail : CabinDetails)
        Detail->SetVisibility(Enabled);
    if (Enabled && LandingOn)
    {
        // Also handles initial hangar display, which has no incoming flight/descent to animate.
        // Normal landings have already played the whole sequence over their supplied duration.
        Landing = true;
        PlayHullSequence(LandingOn, nullptr);
        Hull->SetPosition(LandingOn->GetPlayLength(), false);
        Hull->Stop();
        Hull->RefreshBoneTransforms();
    }
    RigPawn->SetActorEnableCollision(Enabled);
    TInlineComponentArray<UPrimitiveComponent *> Components(RigPawn);
    for (UPrimitiveComponent *Component : Components)
        if (Cast<USkeletalMeshComponent>(Component) || Cast<UStaticMeshComponent>(Component) ||
            GearColliders.Contains(Component) || RampColliders.Contains(Component))
        {
            // Cabin display cases and panes remain decorative during the parked collision transition.
            if (auto *Detail = Cast<UStaticMeshComponent>(Component); Detail && CabinDetails.Contains(Detail))
                continue;
            Component->SetSimulatePhysics(false);
            Component->SetCollisionObjectType(ECC_WorldDynamic);
            Component->SetCollisionResponseToAllChannels(ECR_Ignore);
            Component->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
            Component->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
            Component->SetCollisionResponseToChannel(ECC_Camera, ECR_Block);
            Component->SetCollisionEnabled(Enabled ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
        }
    if (Enabled)
    {
        // Disable the coarse ramp and measured interior envelopes on this body instance. The asset's box geometry
        // remains untouched; UE intersects this per-shape filter with the component filter.
        // Classify the measured shape in ship space rather than assuming an array index forever.
        UPhysicsAsset *Physics = Hull->GetPhysicsAsset();
        int32 Replaced = 0;
        for (USkeletalBodySetup *Setup : Physics->SkeletalBodySetups)
            if (FBodyInstance *Body = Hull->GetBodyInstance(Setup->BoneName))
            {
                const FTransform BoneToShip =
                    Hull->GetSocketTransform(Setup->BoneName).GetRelativeTransform(GetOwner()->GetActorTransform());
                for (int32 Index = 0; Index < Setup->AggGeom.GetElementCount(); ++Index)
                    if (const FKShapeElem *Shape = Setup->AggGeom.GetElement(Index);
                        Shape && Shape->GetShapeType() == EAggCollisionShape::Box)
                    {
                        // Match the parked-asset author's measurement, which preserves the original
                        // boxes. The separate flight profile converts its shapes to convexes.
                        FKConvexElem Measurement;
                        Measurement.ConvexFromBoxElem(*static_cast<const FKBoxElem *>(Shape));
                        Measurement.BakeTransformToVerts();
                        FBox Bounds(ForceInit);
                        for (const FVector &Vertex : Measurement.VertexData)
                            Bounds += BoneToShip.TransformPosition(Vertex);
                        const bool RampEnvelope = Bounds.Min.X < -1250.f && Bounds.Max.X < -900.f &&
                                                  Bounds.Min.Z < 10.f && Bounds.Max.Z < 250.f;
                        // Original source shapes 5/6/7 enclose the passage, cockpit and dividing
                        // bulkhead. Exact landed triangles replace them only when available.
                        const bool InteriorEnvelope =
                            InteriorCollider &&
                            ((Bounds.Min.X > -90.f && Bounds.Min.X < -80.f && Bounds.Max.X > 720.f &&
                              Bounds.Max.X < 730.f && Bounds.Min.Z > 320.f && Bounds.Max.Z > 650.f) ||
                             (Bounds.Min.X > 250.f && Bounds.Min.X < 255.f && Bounds.Max.X > 1070.f &&
                              Bounds.Max.X < 1085.f && Bounds.Max.Z > 665.f) ||
                             (Bounds.Min.X > -50.f && Bounds.Min.X < -45.f && Bounds.Max.X > 110.f &&
                              Bounds.Max.X < 120.f && Bounds.Min.Y < -520.f && Bounds.Max.Y > 520.f));
                        if (RampEnvelope || InteriorEnvelope)
                        {
                            Body->SetShapeCollisionEnabled(Index, ECollisionEnabled::NoCollision);
                            ++Replaced;
                        }
                    }
            }
        ensureMsgf(Replaced == (InteriorCollider ? 4 : 1) && RampColliders.Num() == 2,
                   TEXT("Phoenix boarding expects measured ramp/interior replacements and two authored panels; "
                        "replaced=%d panels=%d"),
                   Replaced, RampColliders.Num());
    }
}

FTransform USSShipVisualRig::GetPilotSeatPelvisWorld() const
{
    // The cushion at ship X850..875 is Z423.276..429.375; the measured replacement
    // pilot's hip is ~20cm above its seated lower thigh. This is not the cockpit bone pivot.
    return FTransform(FQuat::Identity, FVector(860.f, 0.f, 446.f)) * GetOwner()->GetActorTransform();
}

bool USSShipVisualRig::CanUsePilotSeatAt(FVector Position, float Radius, float HalfHeight) const
{
    if (!Parked || !InteriorCollider || !InteriorCollider->IsCollisionEnabled() || Position.ContainsNaN() ||
        !FMath::IsFinite(Radius) || !FMath::IsFinite(HalfHeight) || Radius <= 0.f || HalfHeight <= Radius ||
        !GetWorld())
        return false;
    const FVector Local = GetOwner()->GetActorTransform().InverseTransformPosition(Position);
    const float Feet = Local.Z - HalfHeight;
    if (Local.X < 720.f || Local.X > 940.f || FMath::Abs(Local.Y) > 100.f || Feet < 365.f || Feet > 402.f)
        return false;
    FHitResult Floor;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(PhoenixPilotChair), false, GetOwner());
    const FVector Up = GetOwner()->GetActorUpVector();
    const FVector Foot = Position - Up * HalfHeight;
    // The chair approach has two narrow descending treads. A supported capsule can straddle an edge
    // while a centre-only ray sees the lower tread more than 5cm away. Query its actual rounded base,
    // keeping the same 5cm support tolerance. Visibility ignores the querying walker's Pawn capsule;
    // ECC_Pawn would hit that capsule from inside before reaching this ship's floor.
    const FVector BaseCenter = Foot + Up * Radius;
    return GetWorld()->SweepSingleByChannel(Floor, BaseCenter + Up * 5.f, BaseCenter - Up * 5.f, FQuat::Identity,
                                            ECC_Visibility, FCollisionShape::MakeSphere(Radius), Query) &&
           !Floor.bStartPenetrating && Floor.GetComponent() == InteriorCollider &&
           FVector::DotProduct(Floor.ImpactNormal, Up) > .7f;
}

bool USSShipVisualRig::CanBoardAt(FVector Position, float Radius, float HalfHeight) const
{
    if (!Parked || !HasBlueprintRig() || Position.ContainsNaN() || !FMath::IsFinite(Radius) ||
        !FMath::IsFinite(HalfHeight) || Radius <= 0.f || HalfHeight < Radius)
        return false;
    const FVector Local = GetOwner()->GetActorTransform().InverseTransformPosition(Position);
    // The visible rear doorway is at X=-958. Require the whole capsule beyond it and inside the
    // measured cabin walls (Y=-193..194), with feet at its ~230cm floor, not underneath the hull.
    if (Local.X - Radius < -940.f || Local.X > -650.f || FMath::Abs(Local.Y) + Radius > 180.f ||
        Local.Z - HalfHeight < 210.f || Local.Z - HalfHeight > 260.f)
        return false;
    FHitResult Floor;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(PhoenixCabinBoarding), false, GetOwner());
    const FVector Feet = Position - FVector(0, 0, HalfHeight);
    return GetWorld()->LineTraceSingleByChannel(Floor, Feet + FVector(0, 0, 5), Feet - FVector(0, 0, 12),
                                                ECC_Visibility, Query) &&
           (Floor.GetComponent() == Hull || Floor.GetComponent() == InteriorCollider) && Floor.ImpactNormal.Z > .7f &&
           FMath::Abs(Feet.Z - Floor.ImpactPoint.Z) <= 5.f;
}

void USSShipVisualRig::UpdateFlight(FVector2D Steering, FVector2D Strafe, float Power, bool Boost, bool Brake)
{
    SteeringInput = Steering.GetClampedToMaxSize(1.f);
    StrafeInput = Strafe.GetClampedToMaxSize(1.f);
    DrivePower = FMath::Clamp(Power, 0.f, 1.f);
    Boosting = Boost;
    if (Braking != Brake && !Landing)
        SetAirBrake(Brake);
    Braking = Brake;
}

void USSShipVisualRig::PlayHullSequence(UAnimSequence *First, UAnimSequence *Then)
{
    if (!Hull)
        return;
    PendingClip = First ? Then : nullptr;
    UAnimSequence *Clip = First ? First : Then;
    SequenceSeconds = Clip ? Clip->GetPlayLength() / SequencePlayRate : 0.f;
    if (Clip)
    {
        Hull->bPauseAnims = false;
        Hull->SetComponentTickEnabled(true);
        Hull->PlayAnimation(Clip, false);
        Hull->SetPlayRate(SequencePlayRate);
    }
}

void USSShipVisualRig::PlayLanding(float Duration)
{
    if (Landing)
        return;
    Landing = true;
    DrivePower = 0.f;
    Boosting = Braking = false;
    SteeringInput = StrafeInput = FVector2D::ZeroVector;
    SetAirBrake(false);
    const float AuthoredDuration =
        (BattleExit ? BattleExit->GetPlayLength() : 0.f) + (LandingOn ? LandingOn->GetPlayLength() : 0.f);
    SequencePlayRate = Duration > 0.f && AuthoredDuration > 0.f ? AuthoredDuration / Duration : 1.f;
    PlayHullSequence(BattleExit, LandingOn);
}

void USSShipVisualRig::PlayTakeoff(float Duration)
{
    SetStationCollision(false);
    Landing = false;
    SetAirBrake(false);
    const float AuthoredDuration =
        (LandingOff ? LandingOff->GetPlayLength() : 0.f) + (BattleEnter ? BattleEnter->GetPlayLength() : 0.f);
    SequencePlayRate = Duration > 0.f && AuthoredDuration > 0.f ? AuthoredDuration / Duration : 1.f;
    PlayHullSequence(LandingOff, BattleEnter);
}

void USSShipVisualRig::SetAirBrake(bool Deployed)
{
    if (!AirBrakeClip)
        return;
    for (USkeletalMeshComponent *Mesh : AirBrakes)
        if (UAnimSingleNodeInstance *Animation = Mesh->GetSingleNodeInstance())
            Animation->PlayAnim(false, Deployed ? 1.f : -1.f, Animation->GetCurrentTime());
}

void USSShipVisualRig::PlayFiring()
{
    if (!Landing)
        for (UNiagaraComponent *Flash : MuzzleFlashes)
            if (IsValid(Flash))
                Flash->Activate(true);
}

bool USSShipVisualRig::GetMuzzleWorldPosition(FVector &Position) const
{
    if (Muzzles.IsEmpty())
        return false;
    Position = FVector::ZeroVector;
    for (const USceneComponent *Muzzle : Muzzles)
        Position += Muzzle->GetComponentLocation();
    Position /= Muzzles.Num();
    return true;
}

void USSShipVisualRig::TickComponent(float DeltaTime, ELevelTick TickType,
                                     FActorComponentTickFunction *ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!HasBlueprintRig())
        return;
    if (PendingClip)
    {
        SequenceSeconds -= DeltaTime;
        if (SequenceSeconds <= 0.f)
        {
            const float Overshoot = -SequenceSeconds;
            PlayHullSequence(PendingClip, nullptr);
            Hull->SetPosition(Overshoot * SequencePlayRate, false);
        }
    }
    // Nacelles rotate around the Blueprint's pivot arrows, preserving the mesh's authored offset.
    // Rotating the baked mesh at zero would swing the entire engine around the centre of the ship.
    const FQuat Tilt = FRotator(0.f, FMath::Clamp(-SteeringInput.X * 8.f - StrafeInput.X * 10.f, -12.f, 12.f),
                                FMath::Clamp(SteeringInput.Y * 10.f + StrafeInput.Y * 12.f, -12.f, 12.f))
                           .Quaternion();
    for (int32 Index = 0; Index < EnginePivots.Num(); ++Index)
        EnginePivots[Index]->SetRelativeRotation(
            FMath::QInterpTo(EnginePivots[Index]->GetRelativeRotation().Quaternion(), EngineRestRotations[Index] * Tilt,
                             DeltaTime, 7.f));
    for (int32 Index = 0; Index < Exhausts.Num(); ++Index)
    {
        UNiagaraComponent *Effect = Exhausts[Index];
        const bool ManeuverJet = Effect->GetName().Contains(TEXT("Small"));
        const float Maneuver = FMath::Max(SteeringInput.Size(), StrafeInput.Size());
        const float Strength = Parked        ? 0.f
                               : ManeuverJet ? FMath::Max(Maneuver, Braking ? .7f : 0.f)
                                             : FMath::Clamp(DrivePower + (Boosting ? .3f : 0.f), 0.f, 1.3f);
        if (Strength > .05f)
        {
            if (!Effect->IsActive())
                Effect->Activate();
            Effect->SetRelativeScale3D(ExhaustRestScales[Index] * Strength);
        }
        else if (Effect->IsActive())
            Effect->Deactivate();
    }
}

void USSShipVisualRig::ReleaseRig()
{
    SetComponentTickEnabled(false);
    for (UNiagaraComponent *Flash : MuzzleFlashes)
        if (IsValid(Flash))
            Flash->DestroyComponent();
    MuzzleFlashes.Reset();
    if (IsValid(RigPawn))
        RigPawn->Destroy();
    RigPawn = nullptr;
    Hull = nullptr;
    GearColliders.Reset();
    RampColliders.Reset();
    InteriorCollider = nullptr;
    CabinLights.Reset();
    CabinDetails.Reset();
    AirBrakes.Reset();
    EnginePivots.Reset();
    EngineRestRotations.Reset();
    Exhausts.Reset();
    ExhaustRestScales.Reset();
    Muzzles.Reset();
    PendingClip = LandingOn = LandingOff = BattleEnter = BattleExit = AirBrakeClip = nullptr;
}

void USSShipVisualRig::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    ReleaseRig();
    Super::EndPlay(EndPlayReason);
}
