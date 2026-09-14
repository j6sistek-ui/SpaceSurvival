#include "SSDistantAsteroids.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "HAL/IConsoleManager.h"
#include "Misc/PackageName.h"

namespace
{
TAutoConsoleVariable<int32>
    DistantAsteroidCount(TEXT("ss.DistantAsteroidCount"), 384,
                         TEXT("Visual-only distant asteroid count, clamped 0..768. Does not alter hazards."),
                         ECVF_Scalability);
constexpr double MaximumParallax = 4500.0;
constexpr double MinimumAnchorDistance = 32000.0;
constexpr double MaximumRockRadius = 2200.0;
} // namespace

ASSDistantAsteroids::ASSDistantAsteroids()
{
    PrimaryActorTick.bCanEverTick = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("DistantFieldRoot"));
    SetActorEnableCollision(false);
    SetActorHiddenInGame(true);
}

void ASSDistantAsteroids::BeginPlay()
{
    Super::BeginPlay();
    const TCHAR *Names[] = {TEXT("SM_Asteroid_Barren_1"), TEXT("SM_Asteroid_Barren_2"), TEXT("SM_Asteroid_Barren_3"),
                            TEXT("SM_AsteroidBarren_4")};
    for (int32 Index = 0; Index < 4; ++Index)
    {
        const FString Package = FString::Printf(TEXT("/Game/Asteroid_Library/Static_Meshes/%s"), Names[Index]);
        UStaticMesh *Mesh =
            FPackageName::DoesPackageExist(Package) ? LoadObject<UStaticMesh>(nullptr, *Package) : nullptr;
        if (!Mesh)
            Mesh = LoadObject<UStaticMesh>(nullptr,
                                           TEXT("/Game/SpaceSurvival/Meshes/SM_AsteroidMedium.SM_AsteroidMedium"));
        if (!Mesh)
            continue;
        auto *Batch =
            NewObject<UInstancedStaticMeshComponent>(this, FName(*FString::Printf(TEXT("DistantRock_%d"), Index)));
        Batch->SetupAttachment(RootComponent);
        Batch->SetStaticMesh(Mesh);
        Batch->SetCollisionProfileName(TEXT("NoCollision"));
        Batch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Batch->SetGenerateOverlapEvents(false);
        Batch->SetCanEverAffectNavigation(false);
        Batch->SetCastShadow(false);
        Batch->SetMobility(EComponentMobility::Movable);
        Batch->RegisterComponent();
        Batches.Add(Batch);
    }
    BuildField(FMath::Clamp(DistantAsteroidCount.GetValueOnGameThread(), 0, 768));
}

void ASSDistantAsteroids::Follow(AActor *InViewer)
{
    if (Viewer.Get() == InViewer)
        return;
    if (Viewer.IsValid())
        RemoveTickPrerequisiteActor(Viewer.Get());
    Viewer = InViewer;
    ParallaxOffset = FVector::ZeroVector;
    if (IsValid(InViewer))
    {
        PreviousViewerPosition = InViewer->GetActorLocation();
        FieldBasis = InViewer->GetActorQuat();
        SetActorLocation(PreviousViewerPosition);
        AddTickPrerequisiteActor(InViewer);
        SetActorHiddenInGame(!bFlightVisible);
    }
    BuildField(FMath::Clamp(DistantAsteroidCount.GetValueOnGameThread(), 0, 768));
}

void ASSDistantAsteroids::SetFlightVisible(bool bVisible)
{
    if (bFlightVisible == bVisible)
        return;
    bFlightVisible = bVisible;
    SetActorHiddenInGame(!bVisible);
    if (Viewer.IsValid())
    {
        PreviousViewerPosition = Viewer->GetActorLocation();
        SetActorLocation(PreviousViewerPosition);
    }
}

void ASSDistantAsteroids::BuildField(int32 Count)
{
    for (const auto &Batch : Batches)
    {
        Batch->ClearInstances();
        Batch->SetRelativeLocation(ParallaxOffset);
    }
    RestTransforms.SetNum(Batches.Num());
    AnimatedTransforms.SetNum(Batches.Num());
    for (auto &Transforms : RestTransforms)
        Transforms.Reset();
    for (auto &Transforms : AnimatedTransforms)
        Transforms.Reset();
    BuiltCount = 0;
    MinimumAnchorSurface = MinimumAnchorDistance - MaximumRockRadius;
    if (Batches.IsEmpty())
        return;
    // Five forward/lateral clusters and three rear clusters surround the viewer.
    // Persistent clusters and varied angular sizes; never reseed as the camera turns.
    const FVector Clusters[] = {FVector(1, -.65, .24), FVector(1, .7, .4),   FVector(1, -.15, -.65),
                                FVector(1, .18, .65),  FVector(1, .05, .06), FVector(-.5, -1, .2),
                                FVector(-.5, 1, -.3),  FVector(-1, 0, .45)};
    FRandomStream Random(740127);
    for (int32 Index = 0; Index < Count; ++Index)
    {
        auto *Batch = Batches[Index % Batches.Num()].Get();
        const FBoxSphereBounds Bounds = Batch->GetStaticMesh()->GetBounds();
        const FVector Direction = (Clusters[Index % UE_ARRAY_COUNT(Clusters)] + Random.VRand() * .42).GetSafeNormal();
        const double Distance = MinimumAnchorDistance + (Index % 3) * 18000.0 + Random.FRandRange(0.f, 12000.f);
        // Most rocks are small distant silhouettes; sparse larger anchors supply scale.
        // Leave the central sight corridor open without turning decoration into hazards.
        double Radius =
            Index % 12 == 0 ? Random.FRandRange(1400.f, float(MaximumRockRadius)) : Random.FRandRange(100.f, 700.f);
        if (Direction.X > .97)
            Radius = FMath::Min(Radius, 220.0);
        const double Scale = Radius / FMath::Max(1.0, double(Bounds.SphereRadius));
        const FQuat Rotation = FRotator(Random.FRandRange(-180.f, 180.f), Random.FRandRange(-180.f, 180.f),
                                        Random.FRandRange(-180.f, 180.f))
                                   .Quaternion();
        const FVector Center = FieldBasis.RotateVector(Direction * Distance);
        const FVector Pivot = Center - Rotation.RotateVector(Bounds.Origin * Scale);
        const FTransform Pose(Rotation, Pivot, FVector(Scale));
        Batch->AddInstance(Pose);
        RestTransforms[Index % Batches.Num()].Add(Pose);
        AnimatedTransforms[Index % Batches.Num()].Add(Pose);
        ++BuiltCount;
    }
}

void ASSDistantAsteroids::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!Viewer.IsValid())
    {
        SetActorHiddenInGame(true);
        return;
    }
    const FVector Position = Viewer->GetActorLocation();
    const FVector Travel = Position - PreviousViewerPosition;
    PreviousViewerPosition = Position;
    SetActorLocation(Position, false, nullptr, ETeleportType::TeleportPhysics);
    if (!bFlightVisible)
        return;
    const int32 Wanted = FMath::Clamp(DistantAsteroidCount.GetValueOnGameThread(), 0, 768);
    if (Wanted != BuiltCount && !Batches.IsEmpty())
        BuildField(Wanted);
    // A finite sky-shell translation gives gentle depth without eventually reaching
    // a non-colliding rock. Even at the clamp, all mesh bounds remain >=25300cm away.
    // Large jumps are teleports, not parallax motion; rebasing is handled separately.
    if (!Travel.ContainsNaN() && Travel.SizeSquared() < FMath::Square(8000.0))
        ParallaxOffset = (ParallaxOffset - Travel * .08).GetClampedToMaxSize(MaximumParallax);
    // Slow individual tumble around each mesh bound center, not its imported pivot.
    // Four batched submissions, no per-rock actors, collision, or gameplay Tick.
    SpinSeconds = FMath::Fmod(SpinSeconds + FMath::Max(0.f, DeltaSeconds), 36000.0);
    for (int32 BatchIndex = 0; BatchIndex < Batches.Num(); ++BatchIndex)
    {
        auto *Batch = Batches[BatchIndex].Get();
        Batch->SetRelativeLocation(ParallaxOffset);
        const FVector Origin = Batch->GetStaticMesh()->GetBounds().Origin;
        for (int32 Index = 0; Index < RestTransforms[BatchIndex].Num(); ++Index)
        {
            const FTransform &Rest = RestTransforms[BatchIndex][Index];
            const FVector Axis = FVector(1.0, .3 + BatchIndex, .2 + Index % 3).GetSafeNormal();
            const double Rate = .2 + .1 * ((Index + BatchIndex) % 7);
            const FQuat Rotation = FQuat(Axis, FMath::DegreesToRadians(SpinSeconds * Rate)) * Rest.GetRotation();
            FTransform &Pose = AnimatedTransforms[BatchIndex][Index];
            Pose.SetRotation(Rotation);
            Pose.SetLocation(Rest.TransformPosition(Origin) - Rotation.RotateVector(Origin * Rest.GetScale3D()));
        }
        if (!AnimatedTransforms[BatchIndex].IsEmpty())
            Batch->BatchUpdateInstancesTransforms(0, AnimatedTransforms[BatchIndex], false, true, false);
    }
}

void ASSDistantAsteroids::ApplyWorldOffset(const FVector &InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    PreviousViewerPosition += InOffset;
}
