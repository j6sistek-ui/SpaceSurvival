#include "SSDistantAsteroids.h"
#include "SSSpaceLookData.h"
#include "SSSpaceScenery.h"
#include "SSShip.h"
#include "Camera/CameraComponent.h"
#include "SSAsteroidBurst.h"
#include "SSAudio.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformTime.h"
#include "Misc/PackageName.h"
#include "Materials/MaterialInstanceDynamic.h"
#if WITH_EDITOR
#include "StaticMeshCompiler.h"
#endif

namespace
{
// The traversable field has its own budget: distant regional silhouettes cannot starve it.
TAutoConsoleVariable<int32> DistantAsteroidCount(
    TEXT("ss.DistantAsteroidCount"), 6144,
    TEXT("Resident world-space field instances, clamped 0..8192. Independent of Director pressure."), ECVF_Scalability);
constexpr double MinimumAnchorDistance = 8000.0;
constexpr double MaximumRockRadius = 8000.0;
// Every entire mesh sphere fits inside its 500 m cell. At a boundary crossing the nearest
// incoming/outgoing surface is therefore >= 1 km away, beyond the 950 m material fade.
constexpr double CellSize = 50000.0;
constexpr int32 AsteroidCellRadius = 2;
constexpr int32 AsteroidCellCount = 125;
constexpr int32 LayoutGroupSize = 24;
constexpr double FadeStartDistance = 70000.0;
constexpr double FadeEndDistance = 95000.0;
// Component/instance culling must not remove a sphere whose nearer pixels are still visible.
constexpr double DrawDistance = FadeEndDistance + MaximumRockRadius + 5000.0;
FVector LaneCenter(double X)
{
    // Fixed world passages bend gently through the owned formations; they never follow aim.
    return FVector(X, 7000.0 * FMath::Sin(X / 100000.0), 4500.0 * FMath::Sin(X / 150000.0));
}
bool HasFlightClearance(const FVector &Center, double Radius)
{
    if (Center.SizeSquared() < FMath::Square(MinimumAnchorDistance + Radius))
        return false;
    // Periodic parallel routes leave connected, navigable openings without restricting free flight.
    FVector Lane = LaneCenter(Center.X);
    Lane.Y += FMath::RoundToDouble((Center.Y - Lane.Y) / (CellSize * 2.0)) * CellSize * 2.0;
    Lane.Z += FMath::RoundToDouble((Center.Z - Lane.Z) / (CellSize * 2.0)) * CellSize * 2.0;
    return FVector::DistSquared(Center, Lane) >= FMath::Square(6000.0 + Radius);
}
FIntVector CellAt(const FVector &Position)
{
    return FIntVector(FMath::FloorToInt(Position.X / CellSize + .5), FMath::FloorToInt(Position.Y / CellSize + .5),
                      FMath::FloorToInt(Position.Z / CellSize + .5));
}
int32 CellResidue(int32 Coordinate)
{
    return (Coordinate % 5 + 5) % 5;
}

} // namespace

ASSDistantAsteroids::ASSDistantAsteroids()
{
    PrimaryActorTick.bCanEverTick = true;
    // Streaming work is spread over rendered frames; the settled path only compares one cell coordinate.
    PrimaryActorTick.TickInterval = 0.f;
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
    const TCHAR *Names[] = {
        TEXT("SM_Asteroid_Barren_1"),  TEXT("SM_Asteroid_Barren_2"),  TEXT("SM_Asteroid_Barren_3"),
        TEXT("SM_AsteroidBarren_4"),   TEXT("SM_AsteroidMineral_1"),  TEXT("SM_AsteroidMineral_2"),
        TEXT("SM_AsteroidMineral_3"),  TEXT("SM_AsteroidMineral_4"),  TEXT("SM_AsteroidFragment_1"),
        TEXT("SM_AsteroidFragment_2"), TEXT("SM_AsteroidFragment_3"), TEXT("SM_AsteroidFragment_4"),
        TEXT("SM_AsteroidFragment_1"), TEXT("SM_AsteroidFragment_2"), TEXT("SM_AsteroidFragment_3")};
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Names); ++Index)
    {
        const FString Package = FString::Printf(TEXT("/Game/SpaceSurvival/Licensed/SolidScenery/%s"), Names[Index]);
        UStaticMesh *Mesh =
            FPackageName::DoesPackageExist(Package) ? LoadObject<UStaticMesh>(nullptr, *Package) : nullptr;
        if (!Mesh)
            Mesh = LoadObject<UStaticMesh>(nullptr,
                                           TEXT("/Game/SpaceSurvival/Meshes/SM_AsteroidMedium.SM_AsteroidMedium"));
        if (!Mesh)
            continue;
        AddMeshBatch(Mesh);
    }
    RockBatchCount = Batches.Num();
    // Restore the owned wreck/panel/beam mix in the traversable field, not only kilometre-scale regions.
    if (SpaceLook)
        for (const auto &Recipe : SpaceLook->AreaRecipes)
        {
            for (const auto &Candidate : Recipe.Clutter)
                if (Candidate.Mesh && !Candidate.Mesh->GetName().Contains(TEXT("Asteroid")))
                    AddMeshBatch(Candidate.Mesh);
            for (const auto &Placement : Recipe.Landmarks)
                if (Placement.Mesh && !Placement.Mesh->GetName().Contains(TEXT("Asteroid")))
                {
                    const int32 Batch = AddMeshBatch(Placement.Mesh);
                    Batches[Batch]->SetCullDistances(int32(FadeEndDistance), int32(DrawDistance));
                }
        }
}

int32 ASSDistantAsteroids::AddMeshBatch(UStaticMesh *Mesh)
{
    if (const int32 *Existing = MeshBatches.Find(Mesh))
        return *Existing;
#if WITH_EDITOR
    if (Mesh->IsCompiling())
    {
        UStaticMesh *RequiredMeshes[] = {Mesh};
        FStaticMeshCompilingManager::Get().FinishCompilation(RequiredMeshes);
    }
#endif
    auto *Batch = NewObject<UInstancedStaticMeshComponent>(this);
    Batch->SetupAttachment(RootComponent);
    Batch->SetStaticMesh(Mesh);
    if (SpaceLook)
        for (int32 Slot = 0; Slot < Batch->GetNumMaterials(); ++Slot)
            if (const auto *Override = SpaceLook->FieldMaterialOverrides.Find(Batch->GetMaterial(Slot)))
                if (Override->Get())
                    if (auto *Material = Batch->CreateDynamicMaterialInstance(Slot, Override->Get()))
                    {
                        Material->SetScalarParameterValue(TEXT("SSFadeStart"), float(FadeStartDistance));
                        Material->SetScalarParameterValue(TEXT("SSFadeEnd"), float(FadeEndDistance));
                    }
    Batch->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Batch->SetCollisionObjectType(ECC_WorldStatic);
    Batch->SetCollisionResponseToAllChannels(ECR_Ignore);
    Batch->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
    Batch->SetCollisionResponseToChannel(ECC_PhysicsBody, ECR_Block);
    Batch->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Batch->SetGenerateOverlapEvents(false);
    Batch->SetCanEverAffectNavigation(false);
    Batch->SetCastShadow(false);
    Batch->SetCullDistances(int32(FadeEndDistance), int32(DrawDistance));
    Batch->SetMobility(EComponentMobility::Movable);
    Batch->RegisterComponent();
    const int32 Index = Batches.Add(Batch);
    MeshBatches.Add(Mesh, Index);
    return Index;
}

void ASSDistantAsteroids::Follow(AActor *InViewer)
{
    if (Viewer.Get() == InViewer)
        return;
    if (Viewer.IsValid())
        RemoveTickPrerequisiteActor(Viewer.Get());
    Viewer = InViewer;
    SetActorEnableCollision(bFlightVisible && IsValid(InViewer));
    if (IsValid(InViewer))
    {
        if (ConfiguredCount < 0)
            SetActorLocation(InViewer->GetActorLocation());
        AddTickPrerequisiteActor(InViewer);
        SetActorHiddenInGame(!bFlightVisible);
    }
    if (BuiltCount < 0)
        BuildField(FMath::Clamp(DistantAsteroidCount.GetValueOnGameThread(), 0, 8192));
}

void ASSDistantAsteroids::SetFlightVisible(bool bVisible)
{
    if (bFlightVisible == bVisible)
        return;
    bFlightVisible = bVisible;
    SetActorHiddenInGame(!bVisible);
    SetActorEnableCollision(bVisible);
    if (bVisible)
        for (const auto &Batch : Batches)
            if (!Batch->IsPhysicsStateCreated())
                // UE's actor collision toggle updates existing filters only. A field built while
                // hidden has no instance bodies yet, so explicitly create them on first activation.
                Batch->RecreatePhysicsState();
}

void ASSDistantAsteroids::BuildField(int32 Count)
{
    for (const auto &Batch : Batches)
        Batch->ClearInstances();
    Cells.Reset();
    PendingCells.Reset();
    ResidentCenter = FIntVector(MAX_int32);
    ConfiguredCount = Count;
    BuiltCount = 0;
    MinimumAnchorSurface = MinimumAnchorDistance;
    StreamCells();
}

void ASSDistantAsteroids::AddCell(const FIntVector &Cell)
{
    auto &Instances = Cells.Add(Cell);
    // Placement history includes destroyed ordinals: returning to a cell must not rearrange
    // its survivors because a previous neighbour was shot away.
    struct FCompositionRock
    {
        FVector Center;
        double Radius;
        int32 Batch;
        bool bAsteroid;
    };
    TArray<FCompositionRock, TInlineAllocator<66>> Composition;
    // A modulo-5 allocation gives every resident 5x5x5 region the same bounded population.
    const int32 Residue = CellResidue(Cell.X) + 5 * CellResidue(Cell.Y) + 25 * CellResidue(Cell.Z);
    const int32 Count = ConfiguredCount / AsteroidCellCount + (Residue < ConfiguredCount % AsteroidCellCount ? 1 : 0);
    FRandomStream Random(int32(HashCombineFast(GetTypeHash(Cell), 740127u ^ RunSeed)));
    for (int32 Index = 0; Index < Count; ++Index)
    {
        int32 BatchIndex = Random.RandRange(0, RockBatchCount - 1);
        double DebrisRadius = 0;
        if (Index == 0 && Cell != FIntVector::ZeroValue && SpaceLook && !SpaceLook->AreaRecipes.IsEmpty())
        {
            const auto Blend = ASSSpaceScenery::SampleAreaStyle(SpaceLook, FVector(Cell) * CellSize);
            const auto &Recipe = SpaceLook->AreaRecipes[Random.FRand() < Blend.Alpha ? Blend.Second : Blend.First];
            TArray<const FSSSceneryPlacement *> Pieces;
            for (const auto &Placement : Recipe.Landmarks)
                if (Placement.Mesh && !Placement.Mesh->GetName().Contains(TEXT("Asteroid")))
                    Pieces.Add(&Placement);
            if (!Pieces.IsEmpty())
            {
                const auto *Selected = Pieces[Random.RandRange(0, Pieces.Num() - 1)];
                BatchIndex = MeshBatches.FindChecked(Selected->Mesh);
                DebrisRadius = FMath::Clamp(Selected->Radius * .1f, 3500.f, float(MaximumRockRadius));
            }
        }
        if (Index % 7 == 1 && SpaceLook && !SpaceLook->AreaRecipes.IsEmpty())
        {
            const auto Blend = ASSSpaceScenery::SampleAreaStyle(SpaceLook, FVector(Cell) * CellSize);
            const auto &Recipe = SpaceLook->AreaRecipes[Random.FRand() < Blend.Alpha ? Blend.Second : Blend.First];
            TArray<const FSSSceneryCandidate *> Debris;
            for (const auto &Candidate : Recipe.Clutter)
                if (Candidate.Mesh && !Candidate.Mesh->GetName().Contains(TEXT("Asteroid")))
                    Debris.Add(&Candidate);
            if (!Debris.IsEmpty())
            {
                const auto *Selected = Debris[Random.RandRange(0, Debris.Num() - 1)];
                BatchIndex = MeshBatches.FindChecked(Selected->Mesh);
                DebrisRadius = Random.FRandRange(600.f, 3500.f);
            }
        }
        if (DebrisRadius == 0 && RockBatchCount > 2)
        {
            // Break exact silhouette repeats among neighbouring formation samples while
            // retaining the full owned mesh palette and deterministic cell seed.
            const int32 GroupStart = Index / LayoutGroupSize * LayoutGroupSize;
            for (int32 Choice = 0; Choice < RockBatchCount; ++Choice)
            {
                bool Repeated = false;
                for (int32 Prior = FMath::Max(GroupStart, Composition.Num() - 2); Prior < Composition.Num(); ++Prior)
                    Repeated |= Composition[Prior].bAsteroid && Composition[Prior].Batch == BatchIndex;
                if (!Repeated)
                    break;
                BatchIndex = (BatchIndex + 1) % RockBatchCount;
            }
        }
        auto *Batch = Batches[BatchIndex].Get();
        const bool bAsteroid = Batch->GetStaticMesh()->GetName().Contains(TEXT("Asteroid"));
        const FBoxSphereBounds Bounds = Batch->GetStaticMesh()->GetBounds();
        const double Radius = DebrisRadius > 0 ? DebrisRadius
                                               : (Index % 17 == 0 ? Random.FRandRange(4500.f, float(MaximumRockRadius))
                                                                  : Random.FRandRange(800.f, 3400.f));
        FRandomStream GroupRandom(
            int32(HashCombineFast(GetTypeHash(Cell), uint32(Index / LayoutGroupSize + 317) ^ RunSeed)));
        const FVector GroupCenter = FVector(GroupRandom.FRandRange(-.16f, .16f), GroupRandom.FRandRange(-.16f, .16f),
                                            GroupRandom.FRandRange(-.16f, .16f)) *
                                    CellSize;
        const FQuat GroupRotation = GroupRandom.VRand().ToOrientationQuat();
        const uint32 Layout = (GetTypeHash(Cell) + uint32(Index / LayoutGroupSize)) % 3u;
        const TArray<FVector> *Samples = !SpaceLook ? nullptr
                                                    : (Layout == 0   ? &SpaceLook->AsteroidArchSamples
                                                       : Layout == 1 ? &SpaceLook->AsteroidGlobularSamples
                                                                     : &SpaceLook->AsteroidLinearSamples);
        FVector Center;
        auto OverlapsSimilarRock = [&]()
        {
            if (!bAsteroid)
                return false;
            for (const auto &Prior : Composition)
            {
                // A few small fragments beside a hero rock read naturally. Comparable boulders
                // need a visible gap instead of intersecting into a repeated bead-chain wall.
                if (!Prior.bAsteroid || FMath::Min(Radius, Prior.Radius) < FMath::Max(Radius, Prior.Radius) * .6)
                    continue;
                if (FVector::DistSquared(Center, Prior.Center) < FMath::Square((Radius + Prior.Radius) * .95))
                    return true;
            }
            return false;
        };
        int32 Attempt = 0;
        do
        {
            if (Samples && !Samples->IsEmpty() && Attempt < 24)
            {
                // Sample across the entire owned Blueprint construction, not its first eight points.
                const FVector Detail =
                    (*Samples)[(Index % LayoutGroupSize * Samples->Num() / LayoutGroupSize + Attempt) % Samples->Num()];
                Center = FVector(Cell) * CellSize + GroupCenter +
                         GroupRotation.RotateVector(Detail.GetClampedToMaxSize(1.) * CellSize * .27) +
                         Random.VRand() * CellSize * .012;
            }
            else
                Center =
                    FVector(Cell) * CellSize + Random.VRand() * Random.FRandRange(.1f, .95f) * (CellSize * .5 - Radius);
            ++Attempt;
        } while (Attempt < 128 && ((Center - FVector(Cell) * CellSize).GetAbsMax() + Radius > CellSize * .5 ||
                                   !HasFlightClearance(Center, Radius) || OverlapsSimilarRock()));
        if ((Center - FVector(Cell) * CellSize).GetAbsMax() + Radius > CellSize * .5 ||
            !HasFlightClearance(Center, Radius) || OverlapsSimilarRock())
            continue;
        Composition.Add({Center, Radius, BatchIndex, bAsteroid});
        const double Scale = Radius / FMath::Max(1.0, double(Bounds.SphereRadius));
        const FQuat Rotation = FRotator(Random.FRandRange(-180.f, 180.f), Random.FRandRange(-180.f, 180.f),
                                        Random.FRandRange(-180.f, 180.f))
                                   .Quaternion();
        const FVector Pivot = Center - Rotation.RotateVector(Bounds.Origin * Scale);
        const float Health = FMath::Clamp(12.f + float(Radius) * .02f, 24.f, 600.f);
        const auto *PriorDamage = DamageByCell.Find(Cell);
        const float Applied = PriorDamage ? PriorDamage->FindRef(Index) : 0.f;
        if (bAsteroid && Applied >= Health)
            continue;
        Instances.Add({BatchIndex, Batch->AddInstanceById(FTransform(Rotation, Pivot, FVector(Scale))), Index, Center,
                       float(Radius), Health - Applied, bAsteroid});
        ++BuiltCount;
    }
}

void ASSDistantAsteroids::RemoveCell(const FIntVector &Cell)
{
    if (const auto *Instances = Cells.Find(Cell))
        for (const auto &Rock : *Instances)
        {
            Batches[Rock.Batch]->RemoveInstanceById(Rock.Id);
            --BuiltCount;
        }
    Cells.Remove(Cell);
}

void ASSDistantAsteroids::StreamCells()
{
    if (!Viewer.IsValid() || Batches.IsEmpty())
        return;
    const FVector ViewerLocal = Viewer->GetActorLocation() - GetActorLocation();
    const FIntVector Center = CellAt(ViewerLocal);
    if (Center == ResidentCenter && PendingCells.IsEmpty())
        return;
    const bool Initial = ResidentCenter.X == MAX_int32;
    const bool Synchronous = Initial || (Center - ResidentCenter).GetAbsMax() > 1;
    if (Center != ResidentCenter)
    {
        ResidentCenter = Center;
        PendingCells.Reset();
        for (int32 X = -AsteroidCellRadius; X <= AsteroidCellRadius; ++X)
            for (int32 Y = -AsteroidCellRadius; Y <= AsteroidCellRadius; ++Y)
                for (int32 Z = -AsteroidCellRadius; Z <= AsteroidCellRadius; ++Z)
                {
                    const FIntVector Cell = Center + FIntVector(X, Y, Z);
                    if (!Cells.Contains(Cell))
                        PendingCells.Add(Cell);
                }
    }
    // Initial construction and teleports have no useful previous flight view to preserve.
    if (Synchronous)
    {
        TArray<FIntVector> Retired;
        for (const auto &Cell : Cells)
            if ((Cell.Key - Center).GetAbsMax() > AsteroidCellRadius)
                Retired.Add(Cell.Key);
        for (const auto &Cell : Retired)
            RemoveCell(Cell);
        for (const auto &Cell : PendingCells)
            AddCell(Cell);
        PendingCells.Reset();
        return;
    }

    FVector Eye = ViewerLocal;
    if (const auto *Ship = Cast<ASSShip>(Viewer.Get()); Ship && Ship->Camera)
        Eye = Ship->Camera->GetComponentLocation() - GetActorLocation();
    auto CellDistanceSquared = [&](const FIntVector &Cell)
    {
        // Every mesh sphere is contained by this box, so its nearest pixel cannot be closer.
        const FVector Offset = (Eye - FVector(Cell) * CellSize).GetAbs() - FVector(CellSize * .5);
        return FVector(FMath::Max(0., Offset.X), FMath::Max(0., Offset.Y), FMath::Max(0., Offset.Z)).SizeSquared();
    };
    PendingCells.Sort([&](const FIntVector &A, const FIntVector &B)
                      { return CellDistanceSquared(A) < CellDistanceSquared(B); });
    const double Started = FPlatformTime::Seconds();
    constexpr double WorkBudgetSeconds = .004;
    constexpr double AdmissionDeadline = FadeEndDistance + 5000.;
    constexpr double RetireGuard = FadeEndDistance + 2500.;
    for (int32 Index = 0; Index < PendingCells.Num();)
    {
        const FIntVector Incoming = PendingCells[Index];
        const bool Urgent = CellDistanceSquared(Incoming) <= FMath::Square(AdmissionDeadline);
        // Approaching visibility always takes precedence over the soft work budget.
        if (!Urgent && FPlatformTime::Seconds() - Started >= WorkBudgetSeconds)
            break;
        FIntVector Outgoing(MAX_int32);
        for (const auto &Cell : Cells)
            if (CellResidue(Cell.Key.X) == CellResidue(Incoming.X) &&
                CellResidue(Cell.Key.Y) == CellResidue(Incoming.Y) &&
                CellResidue(Cell.Key.Z) == CellResidue(Incoming.Z))
            {
                Outgoing = Cell.Key;
                break;
            }
        if (Outgoing.X != MAX_int32 && CellDistanceSquared(Outgoing) <= FMath::Square(RetireGuard))
        {
            // Same-slot boxes are >=2km apart. If this one is still near the fade,
            // its replacement remains outside the admission horizon and can wait safely.
            ++Index;
            continue;
        }
        if (Outgoing.X != MAX_int32)
            RemoveCell(Outgoing);
        AddCell(Incoming);
        PendingCells.RemoveAt(Index);
    }
}

void ASSDistantAsteroids::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!Viewer.IsValid())
    {
        SetActorHiddenInGame(true);
        SetActorEnableCollision(false);
        return;
    }
    const int32 Wanted = FMath::Clamp(DistantAsteroidCount.GetValueOnGameThread(), 0, 8192);
    if (Wanted != ConfiguredCount && !Batches.IsEmpty())
        BuildField(Wanted);
    else
        StreamCells();
}

void ASSDistantAsteroids::ApplyWorldOffset(const FVector &InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    // Local cell coordinates stay unchanged when the engine rebases actor and viewer together.
}

void ASSDistantAsteroids::SetRunSeed(uint32 Seed)
{
    if (RunSeed == Seed)
        return;
    RunSeed = Seed;
    DamageByCell.Reset();
    if (ConfiguredCount >= 0)
        BuildField(ConfiguredCount);
}

bool ASSDistantAsteroids::ApplyWeaponHit(const FHitResult &Hit, float Damage, bool &bDestroyed)
{
    bDestroyed = false;
    auto *Batch = Cast<UInstancedStaticMeshComponent>(Hit.GetComponent());
    if (!Batch || Batch->GetOwner() != this || Hit.Item < 0 || !FMath::IsFinite(Damage) || Damage <= 0.f)
        return false;
    for (auto &Cell : Cells)
        for (int32 Index = 0; Index < Cell.Value.Num(); ++Index)
        {
            auto &Rock = Cell.Value[Index];
            if (!Rock.bAsteroid || Batches[Rock.Batch] != Batch || !Batch->IsValidId(Rock.Id) ||
                Batch->GetInstanceIndexForId(Rock.Id) != Hit.Item)
                continue;
            const FVector Center = GetActorTransform().TransformPosition(Rock.Center);
            // Reject stale/unrelated hits after an instance-index swap. Current trace points are on
            // the mesh's actual collision surface, bounded by the stored visual sphere.
            if (Hit.ImpactPoint.ContainsNaN() ||
                FVector::DistSquared(Hit.ImpactPoint, Center) > FMath::Square(Rock.Radius + 100.f))
                return false;
            Rock.Health -= Damage;
            DamageByCell.FindOrAdd(Cell.Key).FindOrAdd(Rock.Ordinal) += Damage;
            if (Rock.Health <= 0.f)
            {
                ASSAsteroidBurst::SpawnBurst(GetWorld(), Center, FVector::ZeroVector, Rock.Radius, Hit.ImpactPoint);
                if (auto *Audio = GetWorld()->GetSubsystem<USSWorldAudioSubsystem>())
                {
                    FSSAudioCueDefinition Cue;
                    Cue.Gain = .7f;
                    Audio->PlayOneShot(Cue, TEXT("DebrisBreak"), Hit.ImpactPoint);
                }
                Batch->RemoveInstanceById(Rock.Id);
                Cell.Value.RemoveAtSwap(Index);
                --BuiltCount;
                bDestroyed = true;
            }
            return true;
        }
    return false;
}
