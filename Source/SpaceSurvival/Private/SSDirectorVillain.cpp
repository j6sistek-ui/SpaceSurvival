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
    // On the root, not the craft: a rider carried by the craft's scale would change size with every craft.
    Rider->SetupAttachment(Root);
    Rider->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Rider->SetGenerateOverlapEvents(false);
    Rider->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
    Rider->bEnableUpdateRateOptimizations = true;
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

    // The knight once his files are named; until then an existing character rides in his place. Either is
    // fitted to a height in the world and stood on the top of the craft's bounds, so swapping the craft moves
    // his feet but never resizes him.
    const bool bKnight = FSSHeroDefinition::AssetInstalled(Data.RiderMeshPath);
    const FString &BodyPath = bKnight ? Data.RiderMeshPath : Data.StandInRiderMeshPath;
    const FString &ClipPath = bKnight ? Data.RiderClipPath : Data.StandInRiderClipPath;
    USkeletalMesh *Body =
        FSSHeroDefinition::AssetInstalled(BodyPath) ? LoadObject<USkeletalMesh>(nullptr, *BodyPath) : nullptr;
    const FBoxSphereBounds BodyBounds = Body ? Body->GetBounds() : FBoxSphereBounds(ForceInit);
    const float NativeHeight = BodyBounds.BoxExtent.Z * 2.f;
    if (!FMath::IsFinite(NativeHeight) || NativeHeight <= 1.f)
        Body = nullptr;
    Rider->SetSkeletalMeshAsset(Body);
    Rider->SetVisibility(Body != nullptr);
    if (Body)
    {
        const float Scale =
            Data.RiderHeight > 0.f ? Data.RiderHeight / NativeHeight : FMath::Max(.01f, Data.RiderScale);
        const FBoxSphereBounds Deck =
            Mesh ? Mesh->GetBounds().TransformBy(Craft->GetRelativeTransform()) : FBoxSphereBounds(ForceInit);
        const FVector Top(Deck.Origin.X, Deck.Origin.Y, Deck.Origin.Z + Deck.BoxExtent.Z);
        const FVector Soles(BodyBounds.Origin.X, BodyBounds.Origin.Y, BodyBounds.Origin.Z - BodyBounds.BoxExtent.Z);
        Rider->SetRelativeTransform(FTransform(Data.RiderRotation,
                                               Top - Data.RiderRotation.RotateVector(Soles * Scale) + Data.RiderOffset,
                                               FVector(Scale)));
        UAnimSequence *Clip =
            FSSHeroDefinition::AssetInstalled(ClipPath) ? LoadObject<UAnimSequence>(nullptr, *ClipPath) : nullptr;
        // A clip from another skeleton would only warn and leave him frozen in his bind pose.
        if (Clip && Clip->GetSkeleton() == Body->GetSkeleton())
            Rider->PlayAnimation(Clip, true);
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

void ASSDirectorVillain::Launch()
{
    // Turning the craft toward each throw swung his rider away from the pilot, once a second.
    if (bPresent)
        FlareSeconds = VillainData(this).LaunchFlareSeconds;
}

void ASSDirectorVillain::NotifyLaunch(UWorld *World)
{
    if (!World)
        return;
    for (TActorIterator<ASSDirectorVillain> It(World); It; ++It)
        if (!It->IsActorBeingDestroyed())
        {
            It->Launch();
            return;
        }
}

bool ASSDirectorVillain::FindLaunchPoint(UWorld *World, FVector &Out)
{
    if (!World)
        return false;
    for (TActorIterator<ASSDirectorVillain> It(World); It; ++It)
        if (!It->IsActorBeingDestroyed() && It->bPresent && It->bPlaced)
        {
            Out = It->GetActorLocation();
            return true;
        }
    return false;
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
