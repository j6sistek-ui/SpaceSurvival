#include "SSAmbientPresentation.h"
#include "SSShip.h"
#include "SSShipPresentation.h"
#include "SSSpaceLookData.h"
#include "SSSpaceScenery.h"
#include "Engine/StaticMeshActor.h"
#include "Components/SkyLightComponent.h"
#include "Engine/TextureCube.h"
#include "Engine/DirectionalLight.h"
#include "Components/DirectionalLightComponent.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/StaticMesh.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "Misc/PackageName.h"

namespace
{
constexpr int32 DustCount = 320;
constexpr double DustHalfWidth = 2400.0; // Fine passing grains, distinct from gameplay debris.
TAutoConsoleVariable<int32> DustEnabled(TEXT("ss.LocalDust"), 1,
                                        TEXT("Enable cosmetic local dust grains (0 disables)."));
TAutoConsoleVariable<int32> CloudEnabled(TEXT("ss.AtmosphereClouds"), 1,
                                         TEXT("Enable optional distant atmosphere cloud banks (0 disables)."));
TAutoConsoleVariable<int32> TrailEnabled(TEXT("ss.EngineTrails"), 1,
                                         TEXT("Enable optional Niagara engine ribbon trails (0 disables)."));
} // namespace

ASSAmbientPresentation::ASSAmbientPresentation()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickGroup = TG_PostPhysics;
    SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("PresentationRoot")));
    AmbientLight = CreateDefaultSubobject<USkyLightComponent>(TEXT("SpaceAmbientLight"));
    AmbientLight->SetupAttachment(RootComponent);
    AmbientLight->SetMobility(EComponentMobility::Movable);
    AmbientLight->SourceType = SLS_SpecifiedCubemap;
    AmbientLight->SetVisibility(false);
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
    VolumeFog->SetStartDistance(30000.f);
    VolumeFog->SetVolumetricFogStartDistance(25000.f);
    VolumeFog->SetVolumetricFogNearFadeInDistance(10000.f);
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
        auto *Core = CreateDefaultSubobject<UStaticMeshComponent>(*FString::Printf(TEXT("EngineCore%d"), Index));
        Core->SetupAttachment(RootComponent);
        Core->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Core->SetGenerateOverlapEvents(false);
        Core->SetCastShadow(false);
        Core->SetCanEverAffectNavigation(false);
        Core->SetVisibility(false);
        EngineCores.Add(Core);
        auto *Light = CreateDefaultSubobject<UPointLightComponent>(*FString::Printf(TEXT("EngineGlow%d"), Index));
        Light->SetupAttachment(Core);
        Light->SetIntensityUnits(ELightUnits::Lumens);
        Light->SetAttenuationRadius(700.f);
        Light->SetCastShadows(false);
        Light->SetVisibility(false);
        EngineLights.Add(Light);
    }
}

void ASSAmbientPresentation::BeginPlay()
{
    Super::BeginPlay();
    const TCHAR *LookPath = TEXT("/Game/SpaceSurvival/Licensed/Atmosphere/DA_DeepSpaceLook");
    SpaceLook = FPackageName::DoesPackageExist(LookPath) ? LoadObject<USSSpaceLookData>(nullptr, LookPath) : nullptr;
    UMaterialInterface *Material = SpaceLook ? SpaceLook->CloudMaterial.Get() : nullptr;
    if (SpaceLook)
    {
        VolumeFog->SetFogDensity(SpaceLook->FogDensity);
        VolumeFog->SetFogHeightFalloff(0.f);
        // The flight backdrop is opaque geometry, not sky: AuthorContent spawns a 50 km sphere and
        // GenerateGeometry places the starfield at 40 km, and the sky material is authored is_sky=False
        // because is_sky=True rendered black. That is not a mystery worth solving here. A sky material
        // is routed out of the base pass into EMeshPass::SkyPass, which BasePassRendering.cpp:1512 runs
        // only when EngineShowFlags.Atmosphere is set, so the sky becomes conditional on a view flag the
        // offscreen capture path need not share. Bounding the fog instead removes the need for the flag:
        // the engine documents FogCutoffDistance as "Scene elements past this distance will not have fog
        // applied. This is useful for excluding skyboxes". At 20 km nothing exists between the playable
        // field and the cutoff, so the seam is invisible, while the starfield and backdrop keep true black.
        VolumeFog->SetFogCutoffDistance(2000000.f);
        // Second guard, so the furthest landmark inside the cutoff still keeps a fifth of its own value.
        VolumeFog->SetFogMaxOpacity(.8f);
        VolumeFog->SetVolumetricFogExtinctionScale(1.f);
        VolumeFog->SetVolumetricFogAlbedo(FColor::White);
        VolumeFog->SetVolumetricFogDistance(SpaceLook->FogDistance);
        AmbientLight->SetCubemap(SpaceLook->AmbientCubemap);
        AmbientLight->SetIntensity(SpaceLook->AmbientIntensity);
    }
    auto *Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto *HullMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/SpaceSurvival/Materials/M_Hull.M_Hull"),
                                                        nullptr, LOAD_NoWarn | LOAD_Quiet);
    auto *CoreMaterial = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/SpaceSurvival/Materials/M_Emissive.M_Emissive"), nullptr, LOAD_NoWarn | LOAD_Quiet);
    if (Cube && HullMaterial)
    {
        Dust->SetStaticMesh(Cube);
        DustMaterial = UMaterialInstanceDynamic::Create(HullMaterial, this);
        DustMaterial->SetVectorParameterValue(TEXT("Color"), FLinearColor(.30f, .36f, .42f));
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
            DustSizes.Add(Random.FRandRange(.25f, .85f));
            DustTransforms.Add(FTransform(FRotator(Random.FRandRange(0.f, 180.f), Random.FRandRange(0.f, 180.f), 0.f),
                                          FVector::ZeroVector, FVector::ZeroVector));
        }
        Dust->AddInstances(DustTransforms, false, false, false);
    }
    if (Cube && CoreMaterial)
        for (const auto &Core : EngineCores)
        {
            Core->SetStaticMesh(Cube);
            auto *Dynamic = UMaterialInstanceDynamic::Create(CoreMaterial, this);
            Dynamic->SetVectorParameterValue(TEXT("Color"), FLinearColor::White);
            Dynamic->SetScalarParameterValue(TEXT("Emission"), 3.f);
            Core->SetMaterial(0, Dynamic);
            EngineCoreMaterials.Add(Dynamic);
        }
    CloudAvailable = Material && Cube;
    if (CloudAvailable)
    {
        for (int32 Index = 0; Index < CloudBanks.Num(); ++Index)
        {
            auto *Cloud = CloudBanks[Index].Get();
            Cloud->SetStaticMesh(Cube);
            // Engine cube is 100cm across; banks remain inside the 1.6km fog grid.
            Cloud->SetWorldScale3D(SpaceLook->CloudScale);
            auto *Dynamic = UMaterialInstanceDynamic::Create(Material, this);
            // Keep the authored volume parameters, including its soft boundary and lighting.
            Cloud->SetMaterial(0, Dynamic);
            CloudMaterials.Add(Dynamic);
        }
    }
    const TCHAR *TrailPath = TEXT("/Game/SpaceSurvival/Licensed/Atmosphere/NS_DeepSpaceExhaust");
    auto *System = FPackageName::DoesPackageExist(TrailPath) ? LoadObject<UNiagaraSystem>(nullptr, TrailPath) : nullptr;
    if (!System)
        System = LoadObject<UNiagaraSystem>(
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
    CloudPositionInitialized = false;
    CloudTravel = FVector::ZeroVector;
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
        FVector ExhaustPosition(Rear, Index == 0 ? -Side : Side, 10.f);
        if (Ship && Ship->Presentation)
            Ship->Presentation->TryGetExhaustLocalPosition(Index, ExhaustPosition);
        Trail->SetRelativeLocation(ExhaustPosition);
        Trail->SetRelativeRotation(FRotator::ZeroRotator);
        if (EngineCores.IsValidIndex(Index))
        {
            EngineCores[Index]->AttachToComponent(Ship && Ship->HullMesh ? Ship->HullMesh.Get() : GetRootComponent(),
                                                  FAttachmentTransformRules::KeepRelativeTransform);
            EngineCores[Index]->SetRelativeLocation(ExhaustPosition + FVector(-18.f, 0.f, 0.f));
            EngineCores[Index]->SetRelativeRotation(FRotator::ZeroRotator);
        }
    }
    RestartTrails = true;
}

void ASSAmbientPresentation::SetFlightVisible(bool Visible)
{
    if (FlightVisible == Visible)
        return;
    FlightVisible = Visible;
    if (SpaceLook && SpaceLook->bOverrideFlightKeyDirection && !SpaceLook->FlightKeyRotation.ContainsNaN())
    {
        if (Visible)
        {
            for (TActorIterator<ADirectionalLight> It(GetWorld()); It; ++It)
                if (auto *Light = Cast<UDirectionalLightComponent>(It->GetLightComponent());
                    Light && Light->ForwardShadingPriority == 2)
                {
                    FlightKey = *It;
                    PreviousKeyRotation = It->GetActorRotation();
                    PreviousKeyColor = Light->GetLightColor();
                    PreviousKeyIntensity = Light->Intensity;
                    It->SetActorRotation(SpaceLook->FlightKeyRotation);
                    break;
                }
        }
        else if (FlightKey.IsValid())
        {
            FlightKey->SetActorRotation(PreviousKeyRotation);
            if (auto *Light = Cast<UDirectionalLightComponent>(FlightKey->GetLightComponent()))
            {
                Light->SetLightColor(PreviousKeyColor);
                Light->SetIntensity(PreviousKeyIntensity);
            }
            FlightKey.Reset();
        }
    }
    if (!Visible)
    {
        Dust->SetVisibility(false);
        VolumeFog->SetVisibility(false);
        AmbientLight->SetVisibility(false);
        for (const auto &Cloud : CloudBanks)
            Cloud->SetVisibility(false);
        for (const auto &Trail : EngineTrails)
            Trail->DeactivateImmediate();
        for (const auto &Core : EngineCores)
            Core->SetVisibility(false);
        for (const auto &Light : EngineLights)
            Light->SetVisibility(false);
    }
    else
        RestartTrails = true;
}

void ASSAmbientPresentation::UpdateAreaStyle(float DeltaSeconds)
{
    if (!SpaceLook || SpaceLook->AreaRecipes.IsEmpty())
        return;
    if (!RegionScenery.IsValid())
        for (TActorIterator<ASSSpaceScenery> It(GetWorld()); It; ++It)
        {
            RegionScenery = *It;
            break;
        }
    if (!RegionScenery.IsValid())
        return;
    const auto Blend = RegionScenery->GetCurrentAreaBlend();
    if (!SpaceLook->AreaRecipes.IsValidIndex(Blend.First) || !SpaceLook->AreaRecipes.IsValidIndex(Blend.Second))
        return;
    const auto &A = SpaceLook->AreaRecipes[Blend.First];
    const auto &B = SpaceLook->AreaRecipes[Blend.Second];
    const float Smooth = AreaStyleInitialized ? 1.f - FMath::Exp(-FMath::Max(0.f, DeltaSeconds) * .3f) : 1.f;
    CurrentHazeColor = FMath::Lerp(CurrentHazeColor, FMath::Lerp(A.HazeColor, B.HazeColor, Blend.Alpha), Smooth);
    CurrentKeyColor = FMath::Lerp(CurrentKeyColor, FMath::Lerp(A.KeyColor, B.KeyColor, Blend.Alpha), Smooth);
    CurrentHazeDensity =
        FMath::Lerp(CurrentHazeDensity, FMath::Lerp(A.HazeDensity, B.HazeDensity, Blend.Alpha), Smooth);
    CurrentKeyIntensity =
        FMath::Lerp(CurrentKeyIntensity, FMath::Lerp(A.KeyIntensity, B.KeyIntensity, Blend.Alpha), Smooth);
    CurrentAmbientIntensity =
        FMath::Lerp(CurrentAmbientIntensity, FMath::Lerp(A.AmbientIntensity, B.AmbientIntensity, Blend.Alpha), Smooth);
    AreaStyleInitialized = true;
    // A restrained distance tint connects separated silhouettes without washing
    // the nearby ship. The bounded volume banks provide the denser local patches.
    VolumeFog->SetFogInscatteringColor(CurrentHazeColor * .12f);
    for (const auto &Material : CloudMaterials)
    {
        Material->SetVectorParameterValue(TEXT("Color"), CurrentHazeColor);
        Material->SetScalarParameterValue(TEXT("Density"), CurrentHazeDensity);
    }
    AmbientLight->SetIntensity(CurrentAmbientIntensity);
    if (FlightKey.IsValid())
        if (auto *Light = Cast<UDirectionalLightComponent>(FlightKey->GetLightComponent()))
        {
            Light->SetLightColor(CurrentKeyColor);
            Light->SetIntensity(CurrentKeyIntensity);
        }
    if (!RegionSkyMaterial)
        for (TActorIterator<AStaticMeshActor> It(GetWorld()); It; ++It)
            if (It->ActorHasTag(TEXT("SpaceBackdrop")))
                RegionSkyMaterial = Cast<UMaterialInstanceDynamic>(It->GetStaticMeshComponent()->GetMaterial(0));
    if (RegionSkyMaterial)
        RegionSkyMaterial->SetVectorParameterValue(TEXT("AreaTint"), CurrentHazeColor * 3.f);
}

void ASSAmbientPresentation::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const bool Active = FlightVisible && Followed.IsValid();
    if (Active)
        UpdateAreaStyle(DeltaSeconds);
    const bool CloudsVisible = Active && CloudAvailable && CloudEnabled.GetValueOnGameThread() != 0;
    const FVector Center = Followed.IsValid() ? Followed->GetActorLocation() : FVector::ZeroVector;
    if (!CloudPositionInitialized)
    {
        LastCloudCenter = Center;
        CloudPositionInitialized = true;
    }
    const FVector CloudStep = Center - LastCloudCenter;
    // Banks remain world-stationary over ordinary travel. Bound the accumulated
    // offset so long runs cannot leave the local fog grid; never rotate with aim.
    if (CloudStep.SizeSquared() < FMath::Square(6000.0))
        CloudTravel = (CloudTravel - CloudStep).GetClampedToMaxSize(35000.0);
    else
        CloudTravel = FVector::ZeroVector;
    LastCloudCenter = Center;
    VolumeFog->SetVisibility(CloudsVisible);
    AmbientLight->SetVisibility(Active && SpaceLook && SpaceLook->AmbientCubemap);
    if (CloudsVisible)
        VolumeFog->SetWorldLocation(Center + FVector(0, 0, -10000000));
    const auto *Ship = Cast<ASSShip>(Followed.Get());
    UpdateDust(Center, Ship ? Ship->GetVelocity() : FVector::ZeroVector,
               Active && DustEnabled.GetValueOnGameThread() != 0);
    for (int32 Index = 0; Index < CloudBanks.Num(); ++Index)
    {
        CloudBanks[Index]->SetVisibility(CloudsVisible);
        if (CloudsVisible)
            CloudBanks[Index]->SetWorldLocation(Center + CloudTravel +
                                                (Index == 0 ? SpaceLook->CloudOffsetA : SpaceLook->CloudOffsetB));
    }
    const bool TrailsVisible =
        Active && Ship && !Ship->IsMoored() && TrailsAvailable && TrailEnabled.GetValueOnGameThread() != 0;
    float DrivePower = 0.f, Damage = 0.f;
    bool Boosting = false, Braking = false;
    if (Ship)
        Ship->GetDrivePresentation(DrivePower, Boosting, Braking, Damage);
    const float Pulse = .85f + .15f * FMath::Sin(GetWorld()->GetTimeSeconds() * (Damage > .1f ? 28.f : 9.f));
    const FLinearColor DriveColor = Damage > .1f && Pulse < .92f ? FLinearColor(1.f, .02f, .01f)
                                    : Braking                    ? FLinearColor(1.f, .18f, .02f)
                                    : Boosting                   ? FLinearColor(.18f, .62f, 1.2f)
                                                                 : FLinearColor(.03f, .22f, .82f);
    const float VisualPower = (Boosting ? 1.75f : Braking ? .55f : DrivePower) * Pulse;
    for (int32 Index = 0; Index < EngineTrails.Num(); ++Index)
    {
        const auto &Trail = EngineTrails[Index];
        FVector ExhaustPosition;
        if (Ship && Ship->Presentation && Ship->Presentation->TryGetExhaustLocalPosition(Index, ExhaustPosition))
        {
            Trail->SetRelativeLocation(ExhaustPosition);
            if (EngineCores.IsValidIndex(Index))
                EngineCores[Index]->SetRelativeLocation(ExhaustPosition + FVector(-18.f, 0.f, 0.f));
        }
        if (TrailsVisible)
        {
            if (RestartTrails || !Trail->IsActive())
                Trail->Activate(true);
            Trail->SetRelativeScale3D(FVector(FMath::Clamp(.65f + VisualPower * .55f, .55f, 1.8f)));
        }
        else if (Trail->IsActive())
            Trail->DeactivateImmediate();
    }
    const bool CoreVisible = Active && Ship && !Ship->IsMoored() && !EngineCoreMaterials.IsEmpty();
    for (int32 Index = 0; Index < EngineCores.Num(); ++Index)
    {
        auto *Core = EngineCores[Index].Get();
        Core->SetVisibility(CoreVisible);
        if (CoreVisible)
        {
            const float Length = FMath::Clamp(18.f + VisualPower * 42.f, 14.f, 95.f);
            const float Width = FMath::Clamp(7.f + VisualPower * 4.f, 6.f, 18.f);
            // Engine cube is 100cm; extend rearward along the ship's +X/-X axis.
            Core->SetRelativeScale3D(FVector(Length, Width, Width) / 100.f);
            if (EngineCoreMaterials.IsValidIndex(Index))
            {
                EngineCoreMaterials[Index]->SetVectorParameterValue(TEXT("Tint"), DriveColor);
                EngineCoreMaterials[Index]->SetScalarParameterValue(TEXT("Emission"), .45f + VisualPower * 1.15f);
            }
            if (EngineLights.IsValidIndex(Index))
            {
                EngineLights[Index]->SetLightColor(DriveColor.GetClamped());
                EngineLights[Index]->SetIntensity(35.f + VisualPower * 180.f);
                EngineLights[Index]->SetAttenuationRadius(170.f + VisualPower * 90.f);
            }
        }
        if (EngineLights.IsValidIndex(Index))
            EngineLights[Index]->SetVisibility(CoreVisible);
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
    if (CloudPositionInitialized)
        LastCloudCenter += InOffset;
    // Clear world-space ribbon history across rebasing to avoid a screen-wide streak.
    for (const auto &Trail : EngineTrails)
        Trail->DeactivateImmediate();
    RestartTrails = true;
}

void ASSAmbientPresentation::UpdateDust(const FVector &Center, const FVector &Velocity, bool Visible)
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
    const float SpeedFraction = FMath::Clamp(float(Velocity.Size() / 4200.0), 0.f, 1.5f);
    const FQuat TravelRotation = Velocity.IsNearlyZero() ? FQuat::Identity : Velocity.ToOrientationQuat();
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
        DustTransforms[Index].SetRotation(TravelRotation);
        const float Width = DustSizes[Index] * Fade / 100.f;
        DustTransforms[Index].SetScale3D(FVector(Width * (1.f + SpeedFraction * 3.f), Width, Width));
    }
    // One component submission/render-state update for all grains.
    Dust->BatchUpdateInstancesTransforms(0, DustTransforms, true, true, Teleported);
}
