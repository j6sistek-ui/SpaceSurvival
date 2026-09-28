#include "SSDirectorVillain.h"
#include "SSContentTypes.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "Animation/AnimSequence.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"

namespace
{
const FSSVillainDefinition &VillainData(const UObject *Context)
{
    const auto *Mode = Cast<ASSGameMode>(UGameplayStatics::GetGameMode(Context));
    const USSPhase1Data *Data = Mode && Mode->Tuning ? Mode->Tuning.Get() : GetDefault<USSPhase1Data>();
    return Data->Villain;
}
} // namespace

ASSDirectorVillain::ASSDirectorVillain()
{
    PrimaryActorTick.bCanEverTick = true;
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);
    Craft = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Craft"));
    Craft->SetupAttachment(Root);
    Craft->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Craft->SetGenerateOverlapEvents(false);
    Rider = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Rider"));
    Rider->SetupAttachment(Craft);
    Rider->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Rider->SetGenerateOverlapEvents(false);
    Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
    Glow->SetupAttachment(Root);
    Glow->SetIntensityUnits(ELightUnits::Lumens);
    Glow->SetCastShadows(false);
    SetActorEnableCollision(false);
    SetActorHiddenInGame(true);
}

void ASSDirectorVillain::BeginPlay()
{
    Super::BeginPlay();
    ApplyDefinition();
}

void ASSDirectorVillain::ApplyDefinition()
{
    const FSSVillainDefinition &Data = VillainData(this);
    const bool bOwnCraft = FSSHeroDefinition::AssetInstalled(Data.CraftMeshPath);
    UStaticMesh *Mesh = bOwnCraft ? LoadObject<UStaticMesh>(nullptr, *Data.CraftMeshPath) : nullptr;
    if (!Mesh && FSSHeroDefinition::AssetInstalled(Data.FallbackCraftMeshPath))
        Mesh = LoadObject<UStaticMesh>(nullptr, *Data.FallbackCraftMeshPath);
    if (!Mesh)
        Mesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cone.Cone"));
    Craft->SetStaticMesh(Mesh);
    Craft->SetRelativeRotation(Data.CraftRotation);
    Craft->SetRelativeScale3D(FVector(bOwnCraft && Mesh ? Data.CraftScale : Data.FallbackCraftScale));

    USkeletalMesh *Body = FSSHeroDefinition::AssetInstalled(Data.RiderMeshPath)
                              ? LoadObject<USkeletalMesh>(nullptr, *Data.RiderMeshPath)
                              : nullptr;
    Rider->SetSkeletalMesh(Body);
    Rider->SetVisibility(Body != nullptr);
    if (Body)
    {
        // The rider is placed against the craft's unscaled geometry, so the craft's scale carries him with it.
        Rider->SetRelativeLocation(Data.RiderOffset);
        Rider->SetRelativeRotation(Data.RiderRotation);
        Rider->SetRelativeScale3D(FVector(Data.RiderScale));
        if (FSSHeroDefinition::AssetInstalled(Data.RiderClipPath))
            if (auto *Clip = LoadObject<UAnimSequence>(nullptr, *Data.RiderClipPath))
            {
                Rider->SetAnimationMode(EAnimationMode::AnimationSingleNode);
                Rider->PlayAnimation(Clip, true);
            }
    }
    Glow->SetLightColor(Data.GlowColor);
    Glow->SetAttenuationRadius(Data.GlowRadius);
    Glow->SetIntensity(Data.GlowLumens);
}

ASSShip *ASSDirectorVillain::FindShip() const
{
    return Cast<ASSShip>(UGameplayStatics::GetPlayerPawn(this, 0));
}

FVector ASSDirectorVillain::DesiredLocation(const ASSShip *Ship) const
{
    const FSSVillainDefinition &Data = VillainData(this);
    const float Phase = 2.f * PI * Age / FMath::Max(1.f, Data.SwayPeriod);
    return Ship->GetActorLocation() + Ship->GetActorForwardVector() * Data.LeadDistance +
           Ship->GetActorUpVector() * (Data.HeightOffset + FMath::Cos(Phase * .7f) * Data.SwayAmplitude * .35f) +
           Ship->GetActorRightVector() * FMath::Sin(Phase) * Data.SwayAmplitude;
}

void ASSDirectorVillain::SetPresent(bool bValue)
{
    if (bPresent == bValue)
        return;
    bPresent = bValue;
    SetActorHiddenInGame(!bValue);
    if (!bValue)
    {
        bPlaced = false;
        FlareSeconds = 0.f;
    }
}

void ASSDirectorVillain::Launch(const FVector &Target)
{
    if (!bPresent)
        return;
    FlareSeconds = VillainData(this).LaunchFlareSeconds;
    // He turns toward what he threw only for the flare, then resumes facing along the chase.
    const FVector ToTarget = Target - GetActorLocation();
    if (!ToTarget.IsNearlyZero())
        SetActorRotation(FMath::RInterpTo(GetActorRotation(), ToTarget.Rotation(), 1.f, .35f));
}

void ASSDirectorVillain::NotifyLaunch(UWorld *World, const FVector &Target)
{
    if (!World)
        return;
    for (TActorIterator<ASSDirectorVillain> It(World); It; ++It)
        if (!It->IsActorBeingDestroyed())
        {
            It->Launch(Target);
            return;
        }
}

void ASSDirectorVillain::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    ASSShip *Ship = FindShip();
    if (!bPresent || !Ship)
        return;
    const FSSVillainDefinition &Data = VillainData(this);
    Age += DeltaSeconds;
    const FVector Desired = DesiredLocation(Ship);
    if (!bPlaced)
    {
        SetActorLocation(Desired);
        bPlaced = true;
    }
    else
        SetActorLocation(FMath::VInterpTo(GetActorLocation(), Desired, DeltaSeconds, Data.FollowResponse));
    FRotator Facing = Ship->GetActorForwardVector().Rotation();
    Facing.Roll = FMath::Sin(2.f * PI * Age / FMath::Max(1.f, Data.SwayPeriod)) * 18.f;
    SetActorRotation(FMath::RInterpTo(GetActorRotation(), Facing, DeltaSeconds, 2.f));
    FlareSeconds = FMath::Max(0.f, FlareSeconds - DeltaSeconds);
    const float Flare = FlareSeconds / FMath::Max(.05f, Data.LaunchFlareSeconds);
    Glow->SetIntensity(Data.GlowLumens * (1.f + (Data.LaunchFlare - 1.f) * Flare));
}
