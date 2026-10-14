#include "SSAsteroidBurst.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"

ASSAsteroidBurst::ASSAsteroidBurst()
{
    PrimaryActorTick.bCanEverTick = true;
    Chips = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("CosmeticChips"));
    RootComponent = Chips;
    Chips->SetCollisionProfileName(TEXT("NoCollision"));
    Chips->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Chips->SetGenerateOverlapEvents(false);
    Chips->SetCanEverAffectNavigation(false);
    Chips->SetCastShadow(false);
    SetActorEnableCollision(false);
}
ASSAsteroidBurst *ASSAsteroidBurst::SpawnBurst(UWorld *World, FVector Position, FVector Drift, float Radius,
                                               TOptional<FVector> ImpactPoint)
{
    if (!World || Position.ContainsNaN() || Drift.ContainsNaN() || !FMath::IsFinite(Radius) || Radius <= 0.f ||
        (ImpactPoint.IsSet() && ImpactPoint->ContainsNaN()))
        return nullptr;
    int32 Active = 0;
    for (TActorIterator<ASSAsteroidBurst> It(World); It; ++It)
        if (!It->IsActorBeingDestroyed() && ++Active >= 8)
            return nullptr;
    auto *Burst = World->SpawnActor<ASSAsteroidBurst>(Position, FRotator::ZeroRotator);
    if (Burst)
        Burst->Initialize(Drift, Radius, ImpactPoint);
    return Burst;
}
void ASSAsteroidBurst::Initialize(FVector Drift, float Radius, TOptional<FVector> ImpactPoint)
{
    auto *Mesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/SpaceSurvival/Meshes/SM_AsteroidSmall.SM_AsteroidSmall"));
    if (!Mesh)
    {
        Destroy();
        return;
    }
    Chips->SetStaticMesh(Mesh); // Retain the existing project rock material.
    MeshOrigin = Mesh->GetBounds().Origin;
    InheritedVelocity = Drift;
    StartRadius = FMath::Max(Radius * .5f, 8.f);
    Duration = FMath::Clamp(.65f + Radius * .0003f, .85f, 2.4f);
    SpreadSpeed = FMath::Clamp(Radius * .65f, 650.f, 22000.f);
    // Cosmetic stream is independent of hazard drop/fragment RNG and run RNG.
    FRandomStream CosmeticRandom(int32(GetTypeHash(GetActorLocation())) ^ 0x4B17);
    const float MeshRadius = FMath::Max(1.f, Mesh->GetBounds().SphereRadius);
    for (int32 Index = 0; Index < 12; ++Index)
    {
        FVector Direction = CosmeticRandom.VRand();
        const FQuat Rotation = CosmeticRandom.VRand().Rotation().Quaternion();
        // Keep shards proportional to the destroyed silhouette, including the large regional bodies.
        // The fixed twelve-instance/eight-burst budget bounds cost independently of their size.
        float ChipRadius = FMath::Max(Radius * CosmeticRandom.FRandRange(.12f, .26f), 6.f);
        FVector Offset = Direction * StartRadius;
        if (ImpactPoint.IsSet() && Index < 2)
        {
            // Surface chips keep a close hit readable when the centre is hundreds of metres away.
            const FVector Surface = (*ImpactPoint - GetActorLocation()).GetClampedToMaxSize(Radius);
            Direction = (Surface.GetSafeNormal() + Direction * .25f).GetSafeNormal();
            ChipRadius = FMath::Clamp(Radius * .025f, 6.f, 450.f);
            Offset = Surface + CosmeticRandom.VRand() * ChipRadius;
        }
        const float Scale = ChipRadius / MeshRadius;
        Directions.Add(Direction);
        Offsets.Add(Offset);
        Rotations.Add(Rotation);
        Scales.Add(Scale);
        Chips->AddInstance(FTransform(Rotation, Offset - Rotation.RotateVector(MeshOrigin * Scale), FVector(Scale)));
    }
}
void ASSAsteroidBurst::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds < 0.f)
        return;
    const float LiveSeconds = FMath::Min(DeltaSeconds, FMath::Max(0.f, Duration - Age));
    Age += LiveSeconds;
    if (Age >= Duration)
    {
        Destroy();
        return;
    }
    AddActorWorldOffset(InheritedVelocity * LiveSeconds);
    // Shrink to zero over the final half-second, avoiding a transparent material pass.
    const float Fade = FMath::Clamp((Duration - Age) / .5f, 0.f, 1.f);
    for (int32 Index = 0; Index < Directions.Num(); ++Index)
    {
        const float Scale = Scales[Index] * Fade;
        const FVector Centre = Offsets[Index] + Directions[Index] * (Age * SpreadSpeed);
        const FQuat Rotation = FQuat(Directions[(Index + 3) % Directions.Num()], Age * 1.8f) * Rotations[Index];
        Chips->UpdateInstanceTransform(
            Index, FTransform(Rotation, Centre - Rotation.RotateVector(MeshOrigin * Scale), FVector(Scale)), false,
            false, true);
    }
    Chips->MarkRenderStateDirty();
}
