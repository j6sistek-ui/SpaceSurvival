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
#include "Engine/World.h"
#include "GameFramework/MovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "PhysicsEngine/PhysicsThrusterComponent.h"

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

    LandingOn = LoadClip(Definition.LandingDeployClipPath, Hull);
    LandingOff = LoadClip(Definition.LandingStowClipPath, Hull);
    BattleEnter = LoadClip(Definition.FlightPoseClipPath, Hull);
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

void USSShipVisualRig::SetStationCollision(bool Enabled)
{
    Parked = Enabled;
    if (!HasBlueprintRig())
        return;
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
            GearColliders.Contains(Component))
        {
            Component->SetSimulatePhysics(false);
            Component->SetCollisionObjectType(ECC_WorldDynamic);
            Component->SetCollisionResponseToAllChannels(ECR_Ignore);
            Component->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
            Component->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
            Component->SetCollisionResponseToChannel(ECC_Camera, ECR_Block);
            Component->SetCollisionEnabled(Enabled ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
        }
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
    const FQuat Tilt =
        FRotator(0.f, -SteeringInput.X * 8.f - StrafeInput.X * 10.f, SteeringInput.Y * 10.f + StrafeInput.Y * 12.f)
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
                                             : FMath::Clamp(.35f + DrivePower + (Boosting ? .3f : 0.f), .35f, 1.7f);
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
