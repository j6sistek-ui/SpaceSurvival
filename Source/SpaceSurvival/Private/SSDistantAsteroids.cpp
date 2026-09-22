#include "SSDistantAsteroids.h"
#include "SSSpaceLookData.h"
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
// Five cells per axis keep the nearest eviction beyond the 1.4 km draw distance.
constexpr double CellSize = 80000.0;
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
#if WITH_EDITOR
        // As with the landing pad, an asynchronously compiling mesh cannot create collision yet.
        // Wait only for the meshes being registered; packaged meshes are already compiled.
        if (Mesh->IsCompiling())
        {
            UStaticMesh *RequiredMeshes[] = {Mesh};
            FStaticMeshCompilingManager::Get().FinishCompilation(RequiredMeshes);
        }
#endif
        auto *Batch =
            NewObject<UInstancedStaticMeshComponent>(this, FName(*FString::Printf(TEXT("DistantRock_%d"), Index)));
        Batch->SetupAttachment(RootComponent);
        Batch->SetStaticMesh(Mesh);
        // Use the owned library's private simple-collision derivatives. These are world objects,
        // independent of the Director; ship sweeps and weapons must both hit them.
        Batch->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Batch->SetCollisionObjectType(ECC_WorldStatic);
        Batch->SetCollisionResponseToAllChannels(ECR_Ignore);
        Batch->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
        Batch->SetCollisionResponseToChannel(ECC_PhysicsBody, ECR_Block);
        Batch->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
        Batch->SetGenerateOverlapEvents(false);
        Batch->SetCanEverAffectNavigation(false);
        Batch->SetCastShadow(false);
        Batch->SetCullDistances(120000, 140000);
        Batch->SetMobility(EComponentMobility::Movable);
        Batch->RegisterComponent();
        Batches.Add(Batch);
    }
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
        const int32 BatchIndex = Random.RandRange(0, Batches.Num() - 1);
        auto *Batch = Batches[BatchIndex].Get();
        const FBoxSphereBounds Bounds = Batch->GetStaticMesh()->GetBounds();
        const double Radius =
            Index % 11 == 0 ? Random.FRandRange(2300.f, float(MaximumRockRadius)) : Random.FRandRange(450.f, 1800.f);
        FVector Center;
        do
        {
            Center = FVector(Cell) * CellSize + FVector(Random.FRandRange(-.49f, .49f), Random.FRandRange(-.49f, .49f),
                                                        Random.FRandRange(-.49f, .49f)) *
                                                    CellSize;
        } while (Center.SizeSquared() < FMath::Square(MinimumAnchorDistance));
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
