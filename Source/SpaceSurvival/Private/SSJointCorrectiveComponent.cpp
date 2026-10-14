#include "SSJointCorrectiveComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/Actor.h"

USSJointCorrectiveComponent::USSJointCorrectiveComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickGroup = TG_PostPhysics;
    SetIsReplicatedByDefault(false);
}

void USSJointCorrectiveComponent::BeginPlay()
{
    Super::BeginPlay();
    Mesh = GetOwner()->FindComponentByClass<USkeletalMeshComponent>();
    if (!Mesh || !Mesh->GetSkeletalMeshAsset() || Correctives.IsEmpty())
    {
        SetComponentTickEnabled(false);
        return;
    }
    const auto &Ref = Mesh->GetSkeletalMeshAsset()->GetRefSkeleton();
    TArray<FTransform> Reference = Ref.GetRefBonePose();
    for (int32 I = 0; I < Reference.Num(); ++I)
        if (Ref.GetParentIndex(I) != INDEX_NONE)
            Reference[I] *= Reference[Ref.GetParentIndex(I)];
    TSet<FName> Morphs;
    bBindingValid = true;
    for (const auto &C : Correctives)
    {
        FBinding B;
        B.Bone = Ref.FindBoneIndex(C.Bone);
        B.End = Ref.FindBoneIndex(C.EndBone);
        B.Reference = Ref.FindBoneIndex(C.ReferenceBone);
        B.Morph = C.Morph;
        B.FullWeight = C.FullWeightProjection;
        if (B.Bone == INDEX_NONE || B.End == INDEX_NONE || B.Reference == INDEX_NONE ||
            !Mesh->GetSkeletalMeshAsset()->FindMorphTarget(B.Morph) || Morphs.Contains(B.Morph) ||
            !FMath::IsFinite(B.FullWeight) || B.FullWeight < .1f || B.FullWeight > 1.f)
        {
            bBindingValid = false;
            break;
        }
        B.DownAxis = Reference[B.Reference].GetRotation().UnrotateVector(FVector::DownVector);
        Morphs.Add(B.Morph);
        Bindings.Add(B);
    }
    if (!bBindingValid)
    {
        Bindings.Reset();
        SetComponentTickEnabled(false);
        UE_LOG(LogTemp, Warning, TEXT("Joint corrective binding invalid on %s"), *GetOwner()->GetName());
        return;
    }
    CurrentWeights.Init(0.f, Bindings.Num());
    AddTickPrerequisiteComponent(Mesh);
}

void USSJointCorrectiveComponent::TickComponent(float DeltaTime, ELevelTick TickType,
                                                FActorComponentTickFunction *ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!Mesh || !bBindingValid)
        return;
    for (int32 I = 0; I < Bindings.Num(); ++I)
    {
        const auto &B = Bindings[I];
        const FVector Direction =
            (Mesh->GetBoneTransform(B.End).GetLocation() - Mesh->GetBoneTransform(B.Bone).GetLocation())
                .GetSafeNormal();
        const FVector Local = Mesh->GetBoneTransform(B.Reference).GetRotation().UnrotateVector(Direction);
        const double Projection = FVector::DotProduct(Local, B.DownAxis);
        const float T = FMath::IsFinite(Projection) ? FMath::Clamp(Projection / B.FullWeight, 0., 1.) : 0.;
        CurrentWeights[I] = T * T * (3.f - 2.f * T);
        Mesh->SetMorphTarget(B.Morph, CurrentWeights[I], false);
    }
}

void USSJointCorrectiveComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    if (Mesh && bBindingValid)
    {
        RemoveTickPrerequisiteComponent(Mesh);
        for (const auto &B : Bindings)
            Mesh->SetMorphTarget(B.Morph, 0.f, true);
    }
    Super::EndPlay(Reason);
}
