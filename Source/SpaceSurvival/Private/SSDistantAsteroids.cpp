#include "SSDistantAsteroids.h"
#include "SSSpaceLookData.h"
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
constexpr double MinimumAnchorDistance = 32000.0;
constexpr double MaximumRockRadius = 4800.0;
struct FDepthBand
{
    float MinimumDistance;
    float MaximumDistance;
    float MinimumRadius;
    float MaximumRadius;
    double Parallax;
    double Tumble;
};
// The pack's examples build scale from sparse large bodies through many small fragments.
// Keep that hierarchy in four bounded visual layers; none enters the playable hazard volume.
const FDepthBand DepthBands[] = {{42000.f, 62000.f, 2300.f, float(MaximumRockRadius), .7, .25},
                                 {float(MinimumAnchorDistance), 51000.f, 450.f, 1000.f, 1.0, 1.0},
                                 {68000.f, 95000.f, 450.f, 1400.f, .35, .5},
                                 {115000.f, 175000.f, 180.f, 650.f, .12, .1}};

float ShellFade(const FVector &Center, const FDepthBand &Band)
{
    const double Distance = Center.Size();
    const double Edge = FMath::Min(Distance - Band.MinimumDistance, Band.MaximumDistance - Distance);
    const float Alpha = FMath::Clamp(float(Edge / 3500.0), 0.f, 1.f);
    return Alpha * Alpha * (3.f - 2.f * Alpha);
}
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
    const TCHAR *LookPath = TEXT("/Game/SpaceSurvival/Licensed/Atmosphere/DA_DeepSpaceLook");
    SpaceLook = FPackageName::DoesPackageExist(LookPath) ? LoadObject<USSSpaceLookData>(nullptr, LookPath) : nullptr;
    // Large bodies use barren/mineral families; fragments/debris keep their smaller role.
    const TCHAR *Names[] = {TEXT("SM_Asteroid_Barren_1"),  TEXT("SM_Asteroid_Barren_2"),  TEXT("SM_Asteroid_Barren_3"),
                            TEXT("SM_AsteroidBarren_4"),   TEXT("SM_AsteroidMineral_1"),  TEXT("SM_AsteroidMineral_2"),
                            TEXT("SM_AsteroidMineral_3"),  TEXT("SM_AsteroidMineral_4"),  TEXT("SM_AsteroidFragment_1"),
                            TEXT("SM_AsteroidFragment_2"), TEXT("SM_AsteroidFragment_3"), TEXT("SM_AsteroidFragment_4"),
                            TEXT("SM_Debris_1"),           TEXT("SM_Debris_2"),           TEXT("SM_Debris_3")};
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Names); ++Index)
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
        Batch->SetRelativeLocation(FVector::ZeroVector);
    }
    InstanceBands.SetNum(Batches.Num());
    RestTransforms.SetNum(Batches.Num());
    AnimatedTransforms.SetNum(Batches.Num());
    for (auto &Bands : InstanceBands)
        Bands.Reset();
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
        const int32 BandIndex = Index % 16 == 0 ? 0 : (Index % 4 == 0 ? 1 : (Index % 4 == 1 ? 2 : 3));
        const FDepthBand &Band = DepthBands[BandIndex];
        const int32 BatchIndex = (BandIndex == 0   ? Index / 16 % 8
                                  : BandIndex == 1 ? 4 + Index / 4 % 8
                                                   : 8 + (Index + Index / 4) % 7) %
                                 Batches.Num();
        auto *Batch = Batches[BatchIndex].Get();
        const FBoxSphereBounds Bounds = Batch->GetStaticMesh()->GetBounds();
        const int32 ClusterIndex = Random.RandRange(0, UE_ARRAY_COUNT(Clusters) - 1);
        FVector Detail = Random.VRand();
        if (SpaceLook)
        {
            const auto &Samples = ClusterIndex % 3 == 0   ? SpaceLook->AsteroidArchSamples
                                  : ClusterIndex % 3 == 1 ? SpaceLook->AsteroidGlobularSamples
                                                          : SpaceLook->AsteroidLinearSamples;
            if (!Samples.IsEmpty())
                Detail = Samples[Random.RandRange(0, Samples.Num() - 1)].GetClampedToMaxSize(1.0);
        }
        FVector Direction = (Clusters[ClusterIndex] + Detail * .65).GetSafeNormal();
        // Move the largest silhouettes to the sides of the entry view, rather than
        // letting a backdrop rock conceal targets directly ahead of the launch heading.
        if (BandIndex == 0 && Direction.X > .9)
        {
            Direction.Y += Direction.Y < 0 ? -.45 : .45;
            Direction.Normalize();
        }
        const double Distance = Random.FRandRange(Band.MinimumDistance + 3500.f, Band.MaximumDistance - 3500.f);
        double Radius = Random.FRandRange(Band.MinimumRadius, Band.MaximumRadius);
        if (Direction.X > .97)
            Radius = FMath::Min(Radius, 220.0);
        const double Scale = Radius / FMath::Max(1.0, double(Bounds.SphereRadius));
        const FQuat Rotation = FRotator(Random.FRandRange(-180.f, 180.f), Random.FRandRange(-180.f, 180.f),
                                        Random.FRandRange(-180.f, 180.f))
                                   .Quaternion();
        const FVector Center = FieldBasis.RotateVector(Direction * Distance);
        const FVector Pivot = Center - Rotation.RotateVector(Bounds.Origin * Scale);
        const FTransform Pose(Rotation, Pivot, FVector(Scale));
        FTransform Animated = Pose;
        Batch->AddInstance(Animated);
        RestTransforms[BatchIndex].Add(Pose);
        AnimatedTransforms[BatchIndex].Add(Animated);
        InstanceBands[BatchIndex].Add(uint8(BandIndex));
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
    // Keep parallax moving during sustained travel. Each shell recycles only at its
    // faded radial edge, never into reachable collision/weapon space. Teleports and
    // world rebases must not look like movement through the field.
    const FVector FieldTravel =
        !Travel.ContainsNaN() && Travel.SizeSquared() < FMath::Square(8000.0) ? Travel : FVector::ZeroVector;
    // Slow individual tumble around each mesh bound center, not its imported pivot.
    // Bounded batched submissions, no per-rock actors, collision, or gameplay Tick.
    SpinSeconds = FMath::Fmod(SpinSeconds + FMath::Max(0.f, DeltaSeconds), 36000.0);
    for (int32 BatchIndex = 0; BatchIndex < Batches.Num(); ++BatchIndex)
    {
        auto *Batch = Batches[BatchIndex].Get();
        Batch->SetRelativeLocation(FVector::ZeroVector);
        const FVector Origin = Batch->GetStaticMesh()->GetBounds().Origin;
        for (int32 Index = 0; Index < RestTransforms[BatchIndex].Num(); ++Index)
        {
            const FDepthBand &Band = DepthBands[InstanceBands[BatchIndex][Index]];
            FTransform &Rest = RestTransforms[BatchIndex][Index];
            FVector Center = Rest.TransformPosition(Origin) - FieldTravel * Band.Parallax;
            const double Distance = Center.Size();
            if (Distance < Band.MinimumDistance)
                Center = -Center.GetSafeNormal() * Band.MaximumDistance;
            else if (Distance > Band.MaximumDistance)
                Center = -Center.GetSafeNormal() * Band.MinimumDistance;
            Rest.SetLocation(Center - Rest.GetRotation().RotateVector(Origin * Rest.GetScale3D()));
            const FVector Axis = FVector(1.0, .3 + BatchIndex, .2 + Index % 3).GetSafeNormal();
            const double Rate = (.2 + .1 * ((Index + BatchIndex) % 7)) * Band.Tumble;
            const FQuat Rotation = FQuat(Axis, FMath::DegreesToRadians(SpinSeconds * Rate)) * Rest.GetRotation();
            FTransform &Pose = AnimatedTransforms[BatchIndex][Index];
            Pose.SetRotation(Rotation);
            Pose.SetScale3D(Rest.GetScale3D() * ShellFade(Center, Band));
            Pose.SetLocation(Center - Rotation.RotateVector(Origin * Pose.GetScale3D()));
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
