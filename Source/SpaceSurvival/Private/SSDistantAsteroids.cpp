#include "SSDistantAsteroids.h"
#include "SSSpaceLookData.h"
#include "SSSpaceScenery.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "HAL/IConsoleManager.h"
#include "Misc/PackageName.h"
#if WITH_EDITOR
#include "StaticMeshCompiler.h"
#endif

namespace
{
// Share a bounded population with the separately streamed, world-stable scenery cells.
TAutoConsoleVariable<int32>
    DistantAsteroidCount(TEXT("ss.DistantAsteroidCount"), 2048,
                         TEXT("World-space asteroid count, clamped 0..3072. Does not alter hazards."),
                         ECVF_Scalability);
constexpr double MinimumAnchorDistance = 32000.0;
constexpr double MaximumRockRadius = 4800.0;
// Five cells per axis keep the nearest eviction beyond the 900 m draw distance.
constexpr double CellSize = 50000.0;
constexpr int32 CellRadius = 2;
constexpr int32 CellCount = 125;
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
    PrimaryActorTick.TickInterval = .25f;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("DistantFieldRoot"));
    SetActorEnableCollision(true);
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
                    // Large silhouettes retire farther from their nearest visible surface.
                    Batches[Batch]->SetCullDistances(60000, 75000);
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
    Batch->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Batch->SetCollisionObjectType(ECC_WorldStatic);
    Batch->SetCollisionResponseToAllChannels(ECR_Ignore);
    Batch->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
    Batch->SetCollisionResponseToChannel(ECC_PhysicsBody, ECR_Block);
    Batch->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Batch->SetGenerateOverlapEvents(false);
    Batch->SetCanEverAffectNavigation(false);
    Batch->SetCastShadow(false);
    Batch->SetCullDistances(75000, 90000);
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
    if (IsValid(InViewer))
    {
        if (ConfiguredCount < 0)
            SetActorLocation(InViewer->GetActorLocation());
        AddTickPrerequisiteActor(InViewer);
        SetActorHiddenInGame(!bFlightVisible);
    }
    if (BuiltCount < 0)
        BuildField(FMath::Clamp(DistantAsteroidCount.GetValueOnGameThread(), 0, 3072));
}

void ASSDistantAsteroids::SetFlightVisible(bool bVisible)
{
    if (bFlightVisible == bVisible)
        return;
    bFlightVisible = bVisible;
    SetActorHiddenInGame(!bVisible);
}

void ASSDistantAsteroids::BuildField(int32 Count)
{
    for (const auto &Batch : Batches)
        Batch->ClearInstances();
    Cells.Reset();
    ResidentCenter = FIntVector(MAX_int32);
    ConfiguredCount = Count;
    BuiltCount = 0;
    MinimumAnchorSurface = MinimumAnchorDistance - MaximumRockRadius;
    StreamCells();
}

void ASSDistantAsteroids::AddCell(const FIntVector &Cell)
{
    auto &Instances = Cells.Add(Cell);
    // A modulo-5 allocation gives every resident 5x5x5 region the same bounded population.
    const int32 Residue = CellResidue(Cell.X) + 5 * CellResidue(Cell.Y) + 25 * CellResidue(Cell.Z);
    const int32 Count = ConfiguredCount / CellCount + (Residue < ConfiguredCount % CellCount ? 1 : 0);
    FRandomStream Random(int32(HashCombineFast(GetTypeHash(Cell), 740127u)));
    for (int32 Index = 0; Index < Count; ++Index)
    {
        int32 BatchIndex = Random.RandRange(0, RockBatchCount - 1);
        double DebrisRadius = 0;
        bool Landmark = false;
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
                DebrisRadius = FMath::Clamp(Selected->Radius * .12f, 3500.f, 11000.f);
                Landmark = true;
            }
        }
        if (Index % 3 == 1 && SpaceLook && !SpaceLook->AreaRecipes.IsEmpty())
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
        auto *Batch = Batches[BatchIndex].Get();
        const FBoxSphereBounds Bounds = Batch->GetStaticMesh()->GetBounds();
        const double Radius = DebrisRadius > 0 ? DebrisRadius
                                               : (Index % 11 == 0 ? Random.FRandRange(2300.f, float(MaximumRockRadius))
                                                                  : Random.FRandRange(450.f, 1800.f));
        FRandomStream GroupRandom(int32(HashCombineFast(GetTypeHash(Cell), uint32(Index / 8 + 317))));
        const FVector GroupCenter = FVector(GroupRandom.FRandRange(-.2f, .2f), GroupRandom.FRandRange(-.2f, .2f),
                                            GroupRandom.FRandRange(-.2f, .2f)) *
                                    CellSize;
        const FQuat GroupRotation = GroupRandom.VRand().ToOrientationQuat();
        const TArray<FVector> *Samples = !SpaceLook ? nullptr
                                                    : (Index / 8 % 3 == 0   ? &SpaceLook->AsteroidArchSamples
                                                       : Index / 8 % 3 == 1 ? &SpaceLook->AsteroidGlobularSamples
                                                                            : &SpaceLook->AsteroidLinearSamples);
        FVector Center;
        int32 Attempt = 0;
        do
        {
            if (Samples && !Samples->IsEmpty() && Attempt < 8)
            {
                // Preserve the owned construction-script silhouettes in world-fixed small groups.
                const FVector Detail = (*Samples)[(Index % 8 * Samples->Num() / 8 + Attempt) % Samples->Num()];
                Center = FVector(Cell) * CellSize + GroupCenter +
                         GroupRotation.RotateVector(Detail.GetClampedToMaxSize(1.) * CellSize * .24) +
                         Random.VRand() * CellSize * .025;
            }
            else
                Center =
                    FVector(Cell) * CellSize + FVector(Random.FRandRange(-.49f, .49f), Random.FRandRange(-.49f, .49f),
                                                       Random.FRandRange(-.49f, .49f)) *
                                                   CellSize;
            ++Attempt;
        } while (Center.SizeSquared() < FMath::Square(MinimumAnchorDistance + (Landmark ? Radius : 0.)));
        const double Scale = Radius / FMath::Max(1.0, double(Bounds.SphereRadius));
        const FQuat Rotation = FRotator(Random.FRandRange(-180.f, 180.f), Random.FRandRange(-180.f, 180.f),
                                        Random.FRandRange(-180.f, 180.f))
                                   .Quaternion();
        const FVector Pivot = Center - Rotation.RotateVector(Bounds.Origin * Scale);
        Instances.Add({BatchIndex, Batch->AddInstanceById(FTransform(Rotation, Pivot, FVector(Scale)))});
        ++BuiltCount;
    }
}

void ASSDistantAsteroids::StreamCells()
{
    if (!Viewer.IsValid() || Batches.IsEmpty())
        return;
    const FIntVector Center = CellAt(Viewer->GetActorLocation() - GetActorLocation());
    if (Center == ResidentCenter)
        return;
    ResidentCenter = Center;
    // Remove only remote cells. Stable engine instance IDs preserve every retained body's pose.
    for (auto It = Cells.CreateIterator(); It; ++It)
    {
        const FIntVector Delta = It.Key() - Center;
        if (FMath::Abs(Delta.X) <= CellRadius && FMath::Abs(Delta.Y) <= CellRadius && FMath::Abs(Delta.Z) <= CellRadius)
            continue;
        for (const auto &Rock : It.Value())
        {
            Batches[Rock.Batch]->RemoveInstanceById(Rock.Id);
            --BuiltCount;
        }
        It.RemoveCurrent();
    }
    for (int32 X = -CellRadius; X <= CellRadius; ++X)
        for (int32 Y = -CellRadius; Y <= CellRadius; ++Y)
            for (int32 Z = -CellRadius; Z <= CellRadius; ++Z)
            {
                const FIntVector Cell = Center + FIntVector(X, Y, Z);
                if (!Cells.Contains(Cell))
                    AddCell(Cell);
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
    const int32 Wanted = FMath::Clamp(DistantAsteroidCount.GetValueOnGameThread(), 0, 3072);
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
