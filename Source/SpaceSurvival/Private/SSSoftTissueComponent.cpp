#include "SSSoftTissueComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/Actor.h"

USSSoftTissueComponent::USSSoftTissueComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickGroup = TG_PostPhysics;
    SetIsReplicatedByDefault(false);
}

void USSSoftTissueComponent::BeginPlay()
{
    Super::BeginPlay();
    TInlineComponentArray<USkeletalMeshComponent *> Meshes(GetOwner());
    for (auto *Candidate : Meshes)
        if (MeshComponentName.IsNone() || Candidate->GetFName() == MeshComponentName)
        {
            Mesh = Candidate;
            break;
        }
    if (!Mesh || !Mesh->GetSkeletalMeshAsset() || Regions.IsEmpty())
    {
        SetComponentTickEnabled(false);
        return;
    }
    const auto &Ref = Mesh->GetSkeletalMeshAsset()->GetRefSkeleton();
    TArray<FTransform> Reference = Ref.GetRefBonePose();
    for (int32 I = 0; I < Reference.Num(); ++I)
        if (Ref.GetParentIndex(I) != INDEX_NONE)
            Reference[I] *= Reference[Ref.GetParentIndex(I)];
    bBindingValid = true;
    States.SetNum(Regions.Num());
    CurrentOffsetsCm.Init(FVector::ZeroVector, Regions.Num());
    for (int32 I = 0; I < Regions.Num(); ++I)
    {
        const auto &Region = Regions[I];
        auto &State = States[I];
        double Total = 0;
        for (const auto &Anchor : Region.Anchors)
        {
            const int32 Bone = Ref.FindBoneIndex(Anchor.Bone);
            if (Bone == INDEX_NONE || Anchor.Weight <= 0 || !FMath::IsFinite(Anchor.Weight) ||
                Anchor.RestPosition.ContainsNaN())
            {
                bBindingValid = false;
                break;
            }
            State.Bindings.Add({Bone, Reference[Bone].Inverse(), Anchor.RestPosition, Anchor.Weight});
            Total += Anchor.Weight;
        }
        bBindingValid &= FMath::Abs(Total - 1.) < .001;
        for (int32 Axis = 0; Axis < 3; ++Axis)
        {
            State.Morphs[Axis] = FName(Region.MorphPrefix.ToString() + TEXT("_") + FString::Chr(TEXT('X') + Axis));
            bBindingValid &= Mesh->GetSkeletalMeshAsset()->FindMorphTarget(State.Morphs[Axis]) != nullptr;
            bBindingValid &= FMath::Abs(FMath::Abs(Region.MorphAxisSigns[Axis]) - 1.) < .001;
        }
    }
    if (!bBindingValid)
    {
        UE_LOG(LogTemp, Warning, TEXT("Soft tissue binding invalid on %s; existing animation remains active"),
               *GetOwner()->GetName());
        SetComponentTickEnabled(false);
        return;
    }
    AddTickPrerequisiteComponent(Mesh);
    ResetDynamics();
}

void USSSoftTissueComponent::ResetDynamics()
{
    for (int32 I = 0; I < States.Num(); ++I)
    {
        auto &State = States[I];
        State.Samples = 0;
        State.Offset = State.Velocity = State.Acceleration = FVector::ZeroVector;
        if (CurrentOffsetsCm.IsValidIndex(I))
            CurrentOffsetsCm[I] = FVector::ZeroVector;
        if (Mesh && bBindingValid)
            for (FName Morph : State.Morphs)
                Mesh->SetMorphTarget(Morph, 0.f, false);
    }
}

void USSSoftTissueComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    if (Mesh && bBindingValid)
    {
        RemoveTickPrerequisiteComponent(Mesh);
        for (const auto &State : States)
            for (FName Morph : State.Morphs)
                Mesh->SetMorphTarget(Morph, 0.f, true);
    }
    Super::EndPlay(Reason);
}

void USSSoftTissueComponent::TickComponent(float DeltaTime, ELevelTick TickType,
                                           FActorComponentTickFunction *ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!Mesh || !bBindingValid || Regions.Num() != States.Num())
        return;
    if (!bDynamicsEnabled || !FMath::IsFinite(DeltaTime) || DeltaTime > .2f)
    {
        ResetDynamics();
        return;
    }
    if (DeltaTime <= SMALL_NUMBER)
        return;
    for (int32 I = 0; I < States.Num(); ++I)
    {
        auto &State = States[I];
        const auto &Region = Regions[I];
        FVector Anchor = FVector::ZeroVector;
        FVector Axes[3] = {FVector::ZeroVector, FVector::ZeroVector, FVector::ZeroVector};
        for (const auto &Binding : State.Bindings)
        {
            const FTransform Skin = Binding.InverseReference * Mesh->GetBoneTransform(Binding.BoneIndex);
            Anchor += Skin.TransformPosition(Binding.Position) * Binding.Weight;
            for (int32 Axis = 0; Axis < 3; ++Axis)
            {
                FVector Direction = FVector::ZeroVector;
                Direction[Axis] = Region.MorphAxisSigns[Axis];
                Axes[Axis] += Skin.TransformVector(Direction) * Binding.Weight;
            }
        }
        const FMatrix Basis(Axes[0], Axes[1], Axes[2], FVector::ZeroVector);
        if (Anchor.ContainsNaN() || FMath::Abs(Basis.Determinant()) < .01 ||
            (State.Samples && FVector::Dist(Anchor, State.PreviousAnchor) > 50.))
        {
            ResetDynamics();
            return;
        }
        const FMatrix Inverse = Basis.Inverse();
        const FVector AnchorVelocity =
            State.Samples ? (Anchor - State.PreviousAnchor) / DeltaTime : FVector::ZeroVector;
        const FVector RawAcceleration =
            State.Samples > 1 ? (AnchorVelocity - State.PreviousVelocity) / (.5 * (DeltaTime + State.PreviousDelta))
                              : FVector::ZeroVector;
        State.Acceleration +=
            (RawAcceleration.GetClampedToMaxSize(12000.) - State.Acceleration) * (1. - FMath::Exp(-DeltaTime / .035));
        State.PreviousAnchor = Anchor;
        State.PreviousVelocity = AnchorVelocity;
        State.PreviousDelta = DeltaTime;
        State.Samples = FMath::Min(State.Samples + 1, 3);
        const double Stiffness = FMath::Clamp(Region.Stiffness, 10.f, 2000.f) / FMath::Clamp(Region.MassKg, .05f, 5.f);
        const double Damping = 2. * FMath::Clamp(Region.DampingRatio, .1f, 2.f) * FMath::Sqrt(Stiffness);
        FVector LocalForce = FVector(Inverse.TransformVector(-State.Acceleration));
        for (int32 Axis = 0; Axis < 3; ++Axis)
            LocalForce[Axis] *= FMath::Clamp(Region.AxisResponse[Axis], 0., 3.);
        const FVector Force = FVector(Basis.TransformVector(LocalForce)) * FMath::Clamp(Region.Strength, 0.f, 2.f);
        // Small, bounded substeps avoid frame-rate-dependent explicit spring instability.
        const int32 Steps = FMath::CeilToInt(DeltaTime / .002);
        const double Step = DeltaTime / Steps;
        for (int32 S = 0; S < Steps; ++S)
        {
            State.Velocity += (Force - Stiffness * State.Offset - Damping * State.Velocity) * Step;
            State.Offset += State.Velocity * Step;
        }
        FVector Local = FVector(Inverse.TransformVector(State.Offset));
        const double Length = Local.Length();
        const double Limit = FMath::Clamp(Region.MaxOffsetCm, .1f, 3.f);
        if (Length > SMALL_NUMBER)
            Local *= Limit * FMath::Tanh(Length / Limit) / Length;
        if (Local.ContainsNaN())
        {
            ResetDynamics();
            return;
        }
        CurrentOffsetsCm[I] = Local;
        for (int32 Axis = 0; Axis < 3; ++Axis)
            // Explicit zero retains the override, suppressing the old baked XYZ curve.
            Mesh->SetMorphTarget(State.Morphs[Axis], Local[Axis] / FMath::Max(Region.CentimetresPerMorphUnit, .01f),
                                 false);
    }
}
