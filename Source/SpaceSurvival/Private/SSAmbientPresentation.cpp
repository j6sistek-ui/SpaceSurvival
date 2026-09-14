#include "SSAmbientPresentation.h"
#include "SSShip.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Engine/StaticMesh.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "Misc/PackageName.h"

namespace
{
constexpr int32 DustCount = 128;
constexpr double DustHalfWidth = 3400.0; // Cube corners remain within 6000cm.
TAutoConsoleVariable<int32> DustEnabled(TEXT("ss.LocalDust"), 1,
                                        TEXT("Enable cosmetic local dust grains (0 disables)."));
TAutoConsoleVariable<int32> CloudEnabled(TEXT("ss.AtmosphereClouds"), 0,
                                         TEXT("Enable optional distant atmosphere cloud banks (0 disables)."));
TAutoConsoleVariable<int32> TrailEnabled(TEXT("ss.EngineTrails"), 1,
                                         TEXT("Enable optional Niagara engine ribbon trails (0 disables)."));
} // namespace

ASSAmbientPresentation::ASSAmbientPresentation()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickGroup = TG_PostPhysics;
    SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("PresentationRoot")));
    VolumeFog = CreateDefaultSubobject<UExponentialHeightFogComponent>(TEXT("CloudVolumeGrid"));
    VolumeFog->SetupAttachment(RootComponent);
    // Engine scene registration rejects densities below DELTA / 1000.
    VolumeFog->SetFogDensity(.000001f);
    VolumeFog->SetFogInscatteringColor(FLinearColor::Black);
    VolumeFog->SetDirectionalInscatteringColor(FLinearColor::Black);
    VolumeFog->SetVolumetricFog(true);
    VolumeFog->SetVolumetricFogExtinctionScale(0.f);
    VolumeFog->SetVolumetricFogAlbedo(FColor::Black);
    VolumeFog->SetVolumetricFogEmissive(FLinearColor::Black);
    VolumeFog->SetVolumetricFogDistance(160000.f);
    VolumeFog->SetVisibility(false);
    Dust = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("LocalDust"));
    Dust->SetupAttachment(RootComponent);
    Dust->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Dust->SetGenerateOverlapEvents(false);
    Dust->SetCastShadow(false);
    Dust->SetCanEverAffectNavigation(false);
    Dust->SetVisibility(false);
    for (int32 Index = 0; Index < 2; ++Index)
    {
        auto *Cloud = CreateDefaultSubobject<UStaticMeshComponent>(*FString::Printf(TEXT("CloudBank%d"), Index));
        Cloud->SetupAttachment(RootComponent);
        Cloud->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Cloud->SetGenerateOverlapEvents(false);
        Cloud->SetCastShadow(false);
        // This mesh bounds a participating medium; its faces must not occlude the sky.
        Cloud->SetRenderInDepthPass(false);
        // Main-pass relevance must remain enabled for static volume voxelization.
        Cloud->SetCanEverAffectNavigation(false);
        Cloud->SetVisibility(false);
        CloudBanks.Add(Cloud);
        auto *Trail = CreateDefaultSubobject<UNiagaraComponent>(*FString::Printf(TEXT("EngineTrail%d"), Index));
        Trail->SetupAttachment(RootComponent);
        Trail->SetAutoActivate(false);
        Trail->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Trail->SetCastShadow(false);
        EngineTrails.Add(Trail);
    }
}

void ASSAmbientPresentation::BeginPlay()
{
    Super::BeginPlay();
    const TCHAR *CloudPath = TEXT("/Game/SpaceSurvival/Licensed/Atmosphere/M_SpaceDustVolume");
    auto *Material =
        FPackageName::DoesPackageExist(CloudPath) ? LoadObject<UMaterialInterface>(nullptr, CloudPath) : nullptr;
    auto *Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto *HullMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/SpaceSurvival/Materials/M_Hull.M_Hull"),
                                                        nullptr, LOAD_NoWarn | LOAD_Quiet);
    if (Cube && HullMaterial)
    {
        Dust->SetStaticMesh(Cube);
        DustMaterial = UMaterialInstanceDynamic::Create(HullMaterial, this);
        DustMaterial->SetVectorParameterValue(TEXT("Color"), FLinearColor(.18f, .21f, .24f));
        DustMaterial->SetVectorParameterValue(TEXT("Tint"), FLinearColor::White);
        DustMaterial->SetScalarParameterValue(TEXT("Metallic"), 0.f);
        DustMaterial->SetScalarParameterValue(TEXT("Roughness"), .9f);
        DustMaterial->SetScalarParameterValue(TEXT("Emission"), .15f);
        Dust->SetMaterial(0, DustMaterial);
        DustPositions.Reserve(DustCount);
        DustTransforms.Reserve(DustCount);
        DustSizes.Reserve(DustCount);
        FRandomStream Random(419731);
        for (int32 Index = 0; Index < DustCount; ++Index)
        {
            DustPositions.Add(FVector(Random.FRandRange(-DustHalfWidth, DustHalfWidth),
                                      Random.FRandRange(-DustHalfWidth, DustHalfWidth),
                                      Random.FRandRange(-DustHalfWidth, DustHalfWidth)));
            DustSizes.Add(Random.FRandRange(1.f, 4.f));
            DustTransforms.Add(FTransform(FRotator(Random.FRandRange(0.f, 180.f), Random.FRandRange(0.f, 180.f), 0.f),
                                          FVector::ZeroVector, FVector::ZeroVector));
        }
        Dust->AddInstances(DustTransforms, false, false, false);
    }
    CloudAvailable = Material && Cube;
    if (CloudAvailable)
    {
        for (int32 Index = 0; Index < CloudBanks.Num(); ++Index)
        {
            auto *Cloud = CloudBanks[Index].Get();
            Cloud->SetStaticMesh(Cube);
            // Engine cube is 100cm across; banks remain inside the 1.6km fog grid.
            Cloud->SetWorldScale3D(Index == 0 ? FVector(600, 500, 250) : FVector(700, 500, 350));
            auto *Dynamic = UMaterialInstanceDynamic::Create(Material, this);
            Dynamic->SetScalarParameterValue(TEXT("Density"), .00001f);
            Cloud->SetMaterial(0, Dynamic);
            CloudMaterials.Add(Dynamic);
        }
    }
    auto *System = LoadObject<UNiagaraSystem>(
        nullptr, TEXT("/Game/NiagaraExamples/FX_Weapons/Trails/NS_SimpleRibbonTrail.NS_SimpleRibbonTrail"), nullptr,
        LOAD_NoWarn | LOAD_Quiet);
    TrailsAvailable = System != nullptr;
    for (const auto &Trail : EngineTrails)
    {
        Trail->SetAsset(System);
        // Instance-only bounds: never mutate the shared vendor system.
        Trail->SetSystemFixedBounds(FBox(FVector(-6000, -400, -400), FVector(400, 400, 400)));
    }
}

void ASSAmbientPresentation::Follow(AActor *Actor)
{
    if (Followed.Get() == Actor)
        return;
    if (Followed.IsValid())
        RemoveTickPrerequisiteActor(Followed.Get());
    Followed = Actor;
    DustInitialized = false;
    if (Actor)
        AddTickPrerequisiteActor(Actor);
    auto *Ship = Cast<ASSShip>(Actor);
    for (int32 Index = 0; Index < EngineTrails.Num(); ++Index)
    {
        auto *Trail = EngineTrails[Index].Get();
        Trail->DeactivateImmediate();
        Trail->AttachToComponent(Ship && Ship->HullMesh ? Ship->HullMesh.Get() : GetRootComponent(),
                                 FAttachmentTransformRules::KeepRelativeTransform);
        float Rear = -235.f;
        float Side = 80.f;
        if (Ship && Ship->HullMesh && Ship->HullMesh->GetStaticMesh())
        {
            const FBox Bounds = Ship->HullMesh->GetStaticMesh()->GetBoundingBox();
            Rear = Bounds.Min.X + 10.f;
            Side = Bounds.GetExtent().Y * .55f;
        }
        Trail->SetRelativeLocation(FVector(Rear, Index == 0 ? -Side : Side, 10.f));
        Trail->SetRelativeRotation(FRotator::ZeroRotator);
    }
    RestartTrails = true;
}

void ASSAmbientPresentation::SetFlightVisible(bool Visible)
{
    if (FlightVisible == Visible)
        return;
    FlightVisible = Visible;
    if (!Visible)
    {
        Dust->SetVisibility(false);
        VolumeFog->SetVisibility(false);
        for (const auto &Cloud : CloudBanks)
            Cloud->SetVisibility(false);
        for (const auto &Trail : EngineTrails)
            Trail->DeactivateImmediate();
    }
    else
        RestartTrails = true;
}

void ASSAmbientPresentation::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const bool Active = FlightVisible && Followed.IsValid();
    const bool CloudsVisible = Active && CloudAvailable && CloudEnabled.GetValueOnGameThread() != 0;
    const FVector Center = Followed.IsValid() ? Followed->GetActorLocation() : FVector::ZeroVector;
    VolumeFog->SetVisibility(CloudsVisible);
    if (CloudsVisible)
        VolumeFog->SetWorldLocation(Center);
    UpdateDust(Center, Active && DustEnabled.GetValueOnGameThread() != 0);
    for (int32 Index = 0; Index < CloudBanks.Num(); ++Index)
    {
        CloudBanks[Index]->SetVisibility(CloudsVisible);
        if (CloudsVisible)
            CloudBanks[Index]->SetWorldLocation(
                Center + (Index == 0 ? FVector(65000, 30000, 17000) : FVector(100000, -45000, -18000)));
    }
    const auto *Ship = Cast<ASSShip>(Followed.Get());
    const bool TrailsVisible =
        Active && Ship && !Ship->IsMoored() && TrailsAvailable && TrailEnabled.GetValueOnGameThread() != 0;
    for (const auto &Trail : EngineTrails)
    {
        if (TrailsVisible)
        {
            if (RestartTrails || !Trail->IsActive())
                Trail->Activate(true);
        }
        else if (Trail->IsActive())
            Trail->DeactivateImmediate();
    }
    RestartTrails = false;
}

void ASSAmbientPresentation::ApplyWorldOffset(const FVector &InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    if (DustInitialized)
    {
        LastDustCenter += InOffset;
        for (auto &Position : DustPositions)
            Position += InOffset;
    }
    // Clear world-space ribbon history across rebasing to avoid a screen-wide streak.
    for (const auto &Trail : EngineTrails)
        Trail->DeactivateImmediate();
    RestartTrails = true;
}

void ASSAmbientPresentation::UpdateDust(const FVector &Center, bool Visible)
{
    Dust->SetVisibility(Visible && DustMaterial != nullptr);
    if (!Visible || !DustMaterial || DustPositions.IsEmpty())
        return;
    // Positions remain world-stationary while the ship flies past. Only recycle
    // across the faded outer shell; never rotate the field with the camera.
    const FVector Travel = Center - LastDustCenter;
    const bool Teleported = DustInitialized && Travel.SizeSquared() > FMath::Square(6000.0);
    if (!DustInitialized || Teleported)
    {
        for (auto &Position : DustPositions)
            Position += DustInitialized ? Travel : Center - LastDustCenter;
        DustInitialized = true;
    }
    LastDustCenter = Center;
    for (int32 Index = 0; Index < DustPositions.Num(); ++Index)
    {
        FVector Offset = DustPositions[Index] - Center;
        for (int32 Axis = 0; Axis < 3; ++Axis)
        {
            if (Offset[Axis] < -DustHalfWidth || Offset[Axis] > DustHalfWidth)
                Offset[Axis] -= FMath::FloorToDouble((Offset[Axis] + DustHalfWidth) / (2.0 * DustHalfWidth)) *
                                (2.0 * DustHalfWidth);
        }
        DustPositions[Index] = Center + Offset;
        const double EdgeDistance = DustHalfWidth - Offset.GetAbsMax();
        const float Edge = FMath::Clamp(float(EdgeDistance / 700.0), 0.f, 1.f);
        const float Bubble = FMath::Clamp(float((Offset.Size() - 200.0) / 300.0), 0.f, 1.f);
        const float Fade = Edge * Edge * (3.f - 2.f * Edge) * Bubble * Bubble * (3.f - 2.f * Bubble);
        DustTransforms[Index].SetLocation(DustPositions[Index]);
        DustTransforms[Index].SetScale3D(FVector(DustSizes[Index] * Fade / 100.f));
    }
    // One component submission/render-state update for all 128 grains.
    Dust->BatchUpdateInstancesTransforms(0, DustTransforms, true, true, Teleported);
}
