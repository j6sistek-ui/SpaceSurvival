#include "SSNPCHeadFillComponent.h"
#include "SSOutpostSandbox.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Pawn.h"
#include "Materials/MaterialInterface.h"

USSNPCHeadFillComponent::USSNPCHeadFillComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

bool USSNPCHeadFillComponent::ReceiverEligible() const
{
    const AActor *Owner = GetOwner();
    if (!IsValid(Owner) || Owner->IsA<APawn>() || !IsValid(ReceiverMesh) || ReceiverMesh->GetOwner() != Owner ||
        Owner->ActorHasTag(TEXT("OutpostRole:Hologram")) ||
        ReceiverMesh->ComponentHasTag(TEXT("OutpostRole:Hologram")) ||
        ReceiverMesh->ComponentHasTag(TEXT("StationCompanionDrone")) ||
        ReceiverMesh->GetFName() == TEXT("StationCompanionDrone"))
        return false;
    // Enrollment must not bypass the existing Ambient exclusions, including wardrobe-owned playback.
    if (const auto *Ambient = Cast<ASSOutpostAmbientActor>(Owner);
        Ambient && (Ambient->bDrone || Ambient->bAnimationManagedExternally || !Ambient->bEnableHeadFill))
        return false;
    if (!ReceiverMesh->GetSkeletalMeshAsset() || HeadFillSocket.IsNone() ||
        !ReceiverMesh->DoesSocketExist(HeadFillSocket))
        return false;
    for (int32 Slot = 0; Slot < ReceiverMesh->GetNumMaterials(); ++Slot)
        if (const UMaterialInterface *Material = ReceiverMesh->GetMaterial(Slot))
            if (Material->GetBlendMode() == BLEND_Opaque || Material->GetBlendMode() == BLEND_Masked)
                return true;
    return false;
}

void USSNPCHeadFillComponent::DisableAndRestoreReceiver()
{
    if (IsValid(HeadFillLight) && HeadFillLight->GetOwner() == GetOwner())
        HeadFillLight->SetVisibility(false);
    if (bOwnsReceiverChannel && IsValid(OwnedReceiver) && OwnedReceiver->GetOwner() == GetOwner())
        OwnedReceiver->SetLightingChannels(OwnedReceiver->LightingChannels.bChannel0,
                                           OwnedReceiver->LightingChannels.bChannel1, bPreviousChannel2);
    bOwnsReceiverChannel = false;
    OwnedReceiver = nullptr;
}

bool USSNPCHeadFillComponent::EnsureLight()
{
    if (IsValid(HeadFillLight))
        return HeadFillLight->GetOwner() == GetOwner();
    auto *Light = NewObject<UPointLightComponent>(GetOwner(), NAME_None, RF_Transactional);
    if (!Light)
        return false;
    Light->CreationMethod = EComponentCreationMethod::Instance;
    Light->SetVisibility(false);
    Light->SetMobility(EComponentMobility::Movable);
    Light->SetupAttachment(ReceiverMesh);
    GetOwner()->AddInstanceComponent(Light);
    HeadFillLight = Light;
    bCreatedLight = true;
    Light->RegisterComponent();
    return Light->IsRegistered();
}

void USSNPCHeadFillComponent::RefreshReadabilityLighting()
{
    DisableAndRestoreReceiver();
    if (!bEnableHeadFill || !ReceiverEligible() || HeadFillOffset.ContainsNaN() || !FMath::IsFinite(HeadFillLumens) ||
        HeadFillLumens <= 0.f || !FMath::IsFinite(HeadFillRadius) || !FMath::IsFinite(HeadFillSourceRadius) ||
        (OffsetFrame && (!IsValid(OffsetFrame) || OffsetFrame->GetOwner() != GetOwner())))
        return;
    if (!EnsureLight() ||
        !HeadFillLight->AttachToComponent(ReceiverMesh, FAttachmentTransformRules::KeepWorldTransform, HeadFillSocket))
        return;
    const FTransform HeadTransform = ReceiverMesh->GetSocketTransform(HeadFillSocket);
    const FTransform Frame = OffsetFrame ? OffsetFrame->GetComponentTransform() : GetOwner()->GetActorTransform();
    const FVector WorldOffset = Frame.TransformVectorNoScale(HeadFillOffset);
    HeadFillLight->SetRelativeLocation(
        HeadTransform.InverseTransformPosition(HeadTransform.GetLocation() + WorldOffset));
    HeadFillLight->SetWorldScale3D(FVector::OneVector);
    HeadFillLight->SetIntensityUnits(ELightUnits::Lumens);
    HeadFillLight->SetIntensity(FMath::Clamp(HeadFillLumens, 0.f, 100.f));
    HeadFillLight->SetUseInverseSquaredFalloff(true);
    HeadFillLight->SetAttenuationRadius(FMath::Clamp(HeadFillRadius, 60.f, 140.f));
    HeadFillLight->SetSourceRadius(FMath::Clamp(HeadFillSourceRadius, 0.f, 20.f));
    HeadFillLight->SetLightColor(FLinearColor(1.f, .95f, .9f));
    HeadFillLight->SetLightingChannels(false, false, true);
    HeadFillLight->SetSpecularScale(0.f);
    HeadFillLight->SetIndirectLightingIntensity(0.f);
    HeadFillLight->SetVolumetricScatteringIntensity(0.f);
    HeadFillLight->SetAffectReflection(false);
    HeadFillLight->SetAffectGlobalIllumination(false);
    HeadFillLight->SetCastShadows(false);
    OwnedReceiver = ReceiverMesh;
    bPreviousChannel2 = OwnedReceiver->LightingChannels.bChannel2;
    OwnedReceiver->SetLightingChannels(OwnedReceiver->LightingChannels.bChannel0,
                                       OwnedReceiver->LightingChannels.bChannel1, true);
    bOwnsReceiverChannel = true;
    HeadFillLight->SetVisibility(true);
}

void USSNPCHeadFillComponent::OnRegister()
{
    Super::OnRegister();
    // Use Ambient's authoritative profile/legacy handoff on initial registration and reregistration.
    if (auto *Ambient = Cast<ASSOutpostAmbientActor>(GetOwner()))
        Ambient->RefreshReadabilityLighting();
    else
        RefreshReadabilityLighting();
}
void USSNPCHeadFillComponent::OnUnregister()
{
    DisableAndRestoreReceiver();
    Super::OnUnregister();
}
void USSNPCHeadFillComponent::BeginPlay()
{
    Super::BeginPlay();
    if (!Cast<ASSOutpostAmbientActor>(GetOwner()))
        RefreshReadabilityLighting();
}
void USSNPCHeadFillComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    DisableAndRestoreReceiver();
    Super::EndPlay(EndPlayReason);
}
void USSNPCHeadFillComponent::OnComponentDestroyed(bool bDestroyingHierarchy)
{
    DisableAndRestoreReceiver();
    if (bCreatedLight && IsValid(HeadFillLight) && HeadFillLight->GetOwner() == GetOwner())
        HeadFillLight->DestroyComponent();
    HeadFillLight = nullptr;
    bCreatedLight = false;
    Super::OnComponentDestroyed(bDestroyingHierarchy);
}

USSNPCHeadFillComponent *USSNPCHeadFillComponent::EnrollNPCMesh(USkeletalMeshComponent *Mesh)
{
    return EnrollNPCMeshInFrame(Mesh, nullptr, FVector(45.f, 0.f, 15.f));
}
USSNPCHeadFillComponent *USSNPCHeadFillComponent::EnrollNPCMeshInFrame(USkeletalMeshComponent *Mesh,
                                                                       USceneComponent *Frame, const FVector &Offset)
{
    if (!IsValid(Mesh) || !IsValid(Mesh->GetOwner()) || Mesh->GetOwner()->IsA<APawn>() ||
        (Frame && (!IsValid(Frame) || Frame->GetOwner() != Mesh->GetOwner())) || Offset.ContainsNaN())
        return nullptr;
    AActor *Owner = Mesh->GetOwner();
    if (auto *Ambient = Cast<ASSOutpostAmbientActor>(Owner))
    {
        // Ambient's serialized properties remain the authoritative profile and playback exclusions.
        if (Mesh != Ambient->CharacterMesh)
            return nullptr;
        Ambient->RefreshReadabilityLighting();
        return Ambient->HeadFillConfiguration;
    }
    TInlineComponentArray<USSNPCHeadFillComponent *> Configurations(Owner);
    for (auto *Configuration : Configurations)
        if (Configuration->ReceiverMesh == Mesh)
        {
            Configuration->RefreshReadabilityLighting();
            return Configuration;
        }
    auto *Configuration = NewObject<USSNPCHeadFillComponent>(Owner, NAME_None, RF_Transactional);
    Configuration->CreationMethod = EComponentCreationMethod::Instance;
    Configuration->ReceiverMesh = Mesh;
    Configuration->OffsetFrame = Frame;
    Configuration->HeadFillOffset = Offset;
    // Reject before allocating a light or enrolling a non-NPC mesh. No world-wide discovery is performed.
    if (!Configuration->ReceiverEligible())
        return nullptr;
#if WITH_EDITOR
    Owner->Modify();
    Mesh->Modify();
#endif
    Owner->AddInstanceComponent(Configuration);
    Configuration->RegisterComponent();
    return Configuration;
}
