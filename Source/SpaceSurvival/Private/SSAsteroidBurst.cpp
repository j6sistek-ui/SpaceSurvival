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
ASSAsteroidBurst *ASSAsteroidBurst::SpawnBurst(UWorld *World, FVector Position, FVector Drift, float Radius)
{
    if (!World || Position.ContainsNaN() || Drift.ContainsNaN() || !FMath::IsFinite(Radius))
        return nullptr;
    int32 Active = 0;
    for (TActorIterator<ASSAsteroidBurst> It(World); It; ++It)
        if (!It->IsActorBeingDestroyed() && ++Active >= 8)
            return nullptr;
    auto *Burst = World->SpawnActor<ASSAsteroidBurst>(Position, FRotator::ZeroRotator);
    if (Burst)
        Burst->Initialize(Drift, Radius);
    return Burst;
}
void ASSAsteroidBurst::Initialize(FVector Drift, float Radius)
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
    StartRadius = FMath::Clamp(Radius * .25f, 8.f, 100.f);
    // Cosmetic stream is independent of hazard drop/fragment RNG and run RNG.
    FRandomStream CosmeticRandom(int32(GetTypeHash(GetActorLocation())) ^ 0x4B17);
    const float MeshRadius = FMath::Max(1.f, Mesh->GetBounds().SphereRadius);
    for (int32 Index = 0; Index < 12; ++Index)
    {
        const FVector Direction = CosmeticRandom.VRand();
        const FQuat Rotation = CosmeticRandom.VRand().Rotation().Quaternion();
        const float Scale = FMath::Clamp(Radius * CosmeticRandom.FRandRange(.04f, .09f), 6.f, 25.f) / MeshRadius;
        Directions.Add(Direction);
        Rotations.Add(Rotation);
        Scales.Add(Scale);
        Chips->AddInstance(
            FTransform(Rotation, Direction * StartRadius - Rotation.RotateVector(MeshOrigin * Scale), FVector(Scale)));
    }
}
void ASSAsteroidBurst::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds < 0.f)
        return;
    const float LiveSeconds = FMath::Min(DeltaSeconds, FMath::Max(0.f, .85f - Age));
    Age += LiveSeconds;
    if (Age >= .85f)
    {
        Destroy();
        return;
    }
    AddActorWorldOffset(InheritedVelocity * LiveSeconds);
    // Shrink to zero over the final half-second, avoiding a transparent material pass.
    const float Fade = FMath::Clamp((.85f - Age) / .5f, 0.f, 1.f);
    for (int32 Index = 0; Index < Directions.Num(); ++Index)
    {
        const float Scale = Scales[Index] * Fade;
        const FVector Centre = Directions[Index] * (StartRadius + Age * 650.f);
        Chips->UpdateInstanceTransform(
            Index,
            FTransform(Rotations[Index], Centre - Rotations[Index].RotateVector(MeshOrigin * Scale), FVector(Scale)),
            false, false, true);
    }
    Chips->MarkRenderStateDirty();
}
