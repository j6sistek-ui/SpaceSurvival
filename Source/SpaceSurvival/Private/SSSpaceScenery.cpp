#include "SSSpaceScenery.h"
#include "SSSpaceLookData.h"
#include "Algo/AllOf.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Misc/PackageName.h"
#include "HAL/IConsoleManager.h"
namespace
{
TAutoConsoleVariable<int32> StructuresEnabled(TEXT("ss.SpaceStructures"), 1,
                                              TEXT("Distant decorative structures (0 disables). No gameplay impact."),
                                              ECVF_Scalability);
TAutoConsoleVariable<int32> AreaPreview(TEXT("ss.SpaceAreaPreview"), -1,
                                        TEXT("-1: spatial regions; 0..N-1: reproducible recipe preview."));
TAutoConsoleVariable<int32> AreaVariation(TEXT("ss.SpaceAreaVariation"), 0,
                                          TEXT("Internal visual variation for repeatable area comparison."));
uint32 CellSeed(const FIntVector &Cell, int32 Seed)
{
    return HashCombineFast(HashCombineFast(GetTypeHash(Cell.X), GetTypeHash(Cell.Y)),
                           HashCombineFast(GetTypeHash(Cell.Z), GetTypeHash(Seed)));
}
double ValidCellSize(const USSSpaceLookData *Data)
{
    return Data && FMath::IsFinite(Data->AreaCellSize) ? FMath::Max(300000.0, double(Data->AreaCellSize)) : 500000.0;
}
bool ValidPlacement(const FSSSceneryPlacement &Placement)
{
    return Placement.Mesh && !Placement.Center.ContainsNaN() && !Placement.Rotation.ContainsNaN() &&
           FMath::IsFinite(Placement.Radius) && Placement.Radius > 0.f;
}
} // namespace
ASSSpaceScenery::ASSSpaceScenery()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = .05f;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("SceneryRoot"));
    SetActorEnableCollision(false);
    SetActorHiddenInGame(true);
}
void ASSSpaceScenery::BeginPlay()
{
    Super::BeginPlay();
    const TCHAR *Path = TEXT("/Game/SpaceSurvival/Licensed/Atmosphere/DA_DeepSpaceLook");
    auto *Data = FPackageName::DoesPackageExist(Path) ? LoadObject<USSSpaceLookData>(nullptr, Path) : nullptr;
    ConfigureLook(Data);
}
void ASSSpaceScenery::ClearGeometry()
{
    for (const auto &Part : Structures)
        if (Part)
            Part->DestroyComponent();
    Structures.Reset();
    Anchors.Reset();
    Cells.Reset();
    ResidentClutter = 0;
    ResidentLandmarks = 0;
    LastCell = FIntVector(MAX_int32);
}
void ASSSpaceScenery::ConfigureLook(USSSpaceLookData *Data)
{
    ClearGeometry();
    Look = Data;
    if (!Data)
        return;
    if (!Data->AreaRecipes.IsEmpty())
    {
        SetActorLocation(OriginOffset);
        LastPreview = MIN_int32;
        RefreshCells();
        return;
    }
    const FVector Positions[] = {FVector(145000, -85000, 24000), FVector(320000, 130000, -45000),
                                 FVector(-240000, -165000, 60000), FVector(420000, -90000, 100000)};
    const bool Authored = !Data->StructureComposition.IsEmpty();
    const int32 Count =
        Authored ? FMath::Min(12, Data->StructureComposition.Num()) : FMath::Min(4, Data->StructureMeshes.Num());
    for (int32 Index = 0; Index < Count; ++Index)
    {
        auto *Mesh = Authored ? Data->StructureComposition[Index].Mesh.Get() : Data->StructureMeshes[Index].Get();
        if (!Mesh)
            continue;
        const FVector Center = Authored ? Data->StructureComposition[Index].Center : Positions[Index];
        const double Radius = Authored ? Data->StructureComposition[Index].Radius : (Index == 0 ? 13500.0 : 19000.0);
        if (Authored && Data->StructureComposition[Index].Rotation.ContainsNaN())
            continue;
        // Preserve the unreachable scenery boundary even for hand-authored layouts.
        if (Center.ContainsNaN() || !FMath::IsFinite(Radius) || Radius <= 0 || Center.Size() - Radius < 105000.0)
            continue;
        auto *Part = NewObject<UStaticMeshComponent>(this);
        Part->SetupAttachment(RootComponent);
        Part->SetStaticMesh(Mesh);
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetGenerateOverlapEvents(false);
        Part->SetCanEverAffectNavigation(false);
        Part->SetCastShadow(false);
        Part->SetMobility(EComponentMobility::Movable);
        const double Scale = Radius / FMath::Max(1.0, double(Mesh->GetBounds().SphereRadius));
        const FQuat Rotation = (Authored ? Data->StructureComposition[Index].Rotation
                                         : FRotator(25 + Index * 17, -45 + Index * 60, Index * 11))
                                   .Quaternion();
        const FVector Anchor = Center - Rotation.RotateVector(Mesh->GetBounds().Origin * Scale);
        Part->SetRelativeTransform(FTransform(Rotation, Anchor, FVector(Scale)));
        Part->RegisterComponent();
        Structures.Add(Part);
        Anchors.Add(Anchor);
    }
}
void ASSSpaceScenery::SetRunSeed(uint32 Seed)
{
    RunSeed = Seed;
}
int32 ASSSpaceScenery::EffectiveVariation() const
{
    const uint32 Variation = uint32(AreaVariation.GetValueOnGameThread());
    return int32(AreaPreview.GetValueOnGameThread() >= 0 ? Variation : Variation ^ RunSeed);
}
void ASSSpaceScenery::Follow(AActor *Viewer)
{
    if (Followed.Get() == Viewer)
        return;
    if (Followed.IsValid())
        RemoveTickPrerequisiteActor(Followed.Get());
    Followed = Viewer;
    Parallax = FVector::ZeroVector;
    if (Viewer)
    {
        LastCenter = Viewer->GetActorLocation();
        SetActorLocation(Look && !Look->AreaRecipes.IsEmpty() ? OriginOffset : LastCenter);
        AddTickPrerequisiteActor(Viewer);
        if (Look && !Look->AreaRecipes.IsEmpty())
            RefreshCells();
    }
}
void ASSSpaceScenery::SetFlightVisible(bool Visible)
{
    FlightVisible = Visible;
    SetActorHiddenInGame(!Visible || !Followed.IsValid() || StructuresEnabled.GetValueOnGameThread() == 0);
}
void ASSSpaceScenery::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    SetFlightVisible(FlightVisible);
    if (!Followed.IsValid())
        return;
    if (Look && !Look->AreaRecipes.IsEmpty())
    {
        RefreshCells();
        LastCenter = Followed->GetActorLocation();
        return;
    }
    const FVector Center = Followed->GetActorLocation();
    const FVector Step = Center - LastCenter;
    LastCenter = Center;
    SetActorLocation(Center);
    // A bounded shell cannot drift into the gameplay corridor during a long run.
    if (FlightVisible && Step.SizeSquared() < FMath::Square(12000.0))
        Parallax = (Parallax - Step * .4).GetClampedToMaxSize(20000.0);
    for (int32 Index = 0; Index < Structures.Num(); ++Index)
        Structures[Index]->SetRelativeLocation(Anchors[Index] + Parallax / (Index + 1));
}
void ASSSpaceScenery::ApplyWorldOffset(const FVector &InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    LastCenter += InOffset;
    OriginOffset += InOffset;
}

FIntVector ASSSpaceScenery::CellAt(const FVector &Position, double Size)
{
    Size = FMath::IsFinite(Size) ? FMath::Max(300000.0, Size) : 500000.0;
    if (Position.ContainsNaN())
        return FIntVector::ZeroValue;
    return FIntVector(FMath::FloorToInt(Position.X / Size + .5), FMath::FloorToInt(Position.Y / Size + .5),
                      FMath::FloorToInt(Position.Z / Size + .5));
}
FSSSpaceAreaBlend ASSSpaceScenery::SampleAreaStyle(const USSSpaceLookData *Data, const FVector &Position, int32 Preview,
                                                   int32 Variation)
{
    FSSSpaceAreaBlend Result;
    if (!Data || Data->AreaRecipes.IsEmpty() || Position.ContainsNaN())
        return Result;
    if (Preview >= 0)
    {
        Result.First = Result.Second = FMath::Clamp(Preview, 0, Data->AreaRecipes.Num() - 1);
        return Result;
    }
    // Continuous trilinear value noise, independent of flight direction and Director cadence.
    const FVector P = Position / (ValidCellSize(Data) * 2.0);
    const FIntVector Base(FMath::FloorToInt(P.X), FMath::FloorToInt(P.Y), FMath::FloorToInt(P.Z));
    FVector T = P - FVector(Base);
    T = T * T * (FVector(3) - 2.0 * T);
    double Value = 0;
    for (int32 Z = 0; Z < 2; ++Z)
        for (int32 Y = 0; Y < 2; ++Y)
            for (int32 X = 0; X < 2; ++X)
            {
                FRandomStream Random(int32(
                    CellSeed(Base + FIntVector(X, Y, Z), int32(uint32(Data->AreaVariationSeed) + uint32(Variation)))));
                Value += Random.FRand() * (X ? T.X : 1 - T.X) * (Y ? T.Y : 1 - T.Y) * (Z ? T.Z : 1 - T.Z);
            }
    const double Style = Value * (Data->AreaRecipes.Num() - 1);
    Result.First = FMath::Clamp(FMath::FloorToInt(Style), 0, Data->AreaRecipes.Num() - 1);
    Result.Second = FMath::Min(Result.First + 1, Data->AreaRecipes.Num() - 1);
    Result.Alpha = float(Style - Result.First);
    return Result;
}
FSSSpaceAreaBlend ASSSpaceScenery::GetCurrentAreaBlend() const
{
    const FVector Position = Followed.IsValid() ? Followed->GetActorLocation() - OriginOffset : FVector::ZeroVector;
    return SampleAreaStyle(Look, Position, AreaPreview.GetValueOnGameThread(), EffectiveVariation());
}
int32 ASSSpaceScenery::GetCurrentAreaIndex() const
{
    const auto Blend = GetCurrentAreaBlend();
    return Blend.Alpha < .5f ? Blend.First : Blend.Second;
}
const FSSSpaceAreaRecipe *ASSSpaceScenery::GetActiveRecipe() const
{
    return Look && Look->AreaRecipes.IsValidIndex(GetCurrentAreaIndex()) ? &Look->AreaRecipes[GetCurrentAreaIndex()]
                                                                         : nullptr;
}
void ASSSpaceScenery::RefreshCells()
{
    if (!Look || Look->AreaRecipes.IsEmpty() || !Followed.IsValid())
        return;
    const int32 Preview = AreaPreview.GetValueOnGameThread();
    const int32 Variation = EffectiveVariation();
    const auto *FarCount = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.DistantAsteroidCount"));
    const int32 Budget =
        FMath::Clamp(Look->AreaClutterBudget, 0, 3072 - FMath::Clamp(FarCount ? FarCount->GetInt() : 2048, 0, 3072));
    const FIntVector Center = CellAt(Followed->GetActorLocation() - OriginOffset, ValidCellSize(Look));
    if (Preview != LastPreview || Variation != LastVariation || Budget != LastClutterBudget)
    {
        ClearGeometry(); // Only an explicit preview/quality change rebuilds still-visible resident cells.
        LastPreview = Preview;
        LastVariation = Variation;
        LastClutterBudget = Budget;
    }
    if (Center == LastCell)
        return;
    LastCell = Center;
    for (auto It = Cells.CreateIterator(); It; ++It)
    {
        const FIntVector D = It.Key() - Center;
        if (FMath::Abs(D.X) <= 1 && FMath::Abs(D.Y) <= 1 && FMath::Abs(D.Z) <= 1)
            continue;
        ResidentClutter -= It.Value().Clutter;
        ResidentLandmarks -= It.Value().Landmarks;
        for (auto *Part : It.Value().Parts)
        {
            Structures.Remove(Part);
            Part->DestroyComponent();
        }
        It.RemoveCurrent();
    }
    for (int32 Z = -1; Z <= 1; ++Z)
        for (int32 Y = -1; Y <= 1; ++Y)
            for (int32 X = -1; X <= 1; ++X)
            {
                const FIntVector Id = Center + FIntVector(X, Y, Z);
                if (!Cells.Contains(Id))
                {
                    // Fixed world identities, not viewer distance, own each allowance. Concentrate
                    // middle-scale debris around authored masses without redistributing on movement.
                    const bool LandmarkCell = Id.X % 2 == 0 && Id.Y % 2 == 0 && Id.Z % 2 == 0;
                    const int32 LandmarkClutter = Budget / 12;
                    const int32 SurroundingClutter = (Budget - 8 * LandmarkClutter) / 19;
                    BuildCell(Id, LandmarkCell ? LandmarkClutter : SurroundingClutter,
                              FMath::Clamp(Look->AreaLandmarkBudget, 0, 64) / 8);
                }
            }
}
void ASSSpaceScenery::BuildCell(const FIntVector &Id, int32 ClutterPerCell, int32 LandmarksPerCell)
{
    FCell &Cell = Cells.Add(Id);
    const double Size = ValidCellSize(Look);
    const FVector Center = FVector(Id) * Size;
    const auto Blend = SampleAreaStyle(Look, Center, LastPreview, LastVariation);
    FRandomStream Random(int32(CellSeed(Id, int32(uint32(Look->AreaVariationSeed) + uint32(LastVariation)))));
    const auto &Recipe = Look->AreaRecipes[Random.FRand() < Blend.Alpha ? Blend.Second : Blend.First];
    const bool Origin = Id == FIntVector::ZeroValue;
    // Non-origin compositions rotate as a whole. Their fixed openings never follow the camera.
    const FQuat GroupRotation = Origin ? FQuat::Identity : FRotator(0, Random.FRandRange(-180, 180), 0).Quaternion();
    auto Register = [&](UStaticMeshComponent *Part)
    {
        Part->SetupAttachment(RootComponent);
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetGenerateOverlapEvents(false);
        Part->SetCanEverAffectNavigation(false);
        Part->SetCastShadow(false);
        Part->SetMobility(EComponentMobility::Movable);
        Part->RegisterComponent();
        Structures.Add(Part);
        Cell.Parts.Add(Part);
    };
    // A 3x3x3 resident window contains at most eight even/even/even landmark cells.
    // Whole groups exceeding their allowance are rejected, never chopped into incoherent parts.
    const double LandmarkClearance =
        FMath::IsFinite(Recipe.ClearRadius) ? FMath::Max(40000.0, double(Recipe.ClearRadius)) : 40000.0;
    const bool ValidGroup = Algo::AllOf(
        Recipe.Landmarks, [&](const FSSSceneryPlacement &Placement)
        { return ValidPlacement(Placement) && Placement.Center.Size() - Placement.Radius >= LandmarkClearance; });
    if ((Id.X % 2 == 0) && (Id.Y % 2 == 0) && (Id.Z % 2 == 0) && Recipe.Landmarks.Num() <= LandmarksPerCell &&
        ValidGroup)
    {
        for (const auto &Placement : Recipe.Landmarks)
        {
            if (!ValidPlacement(Placement))
                continue;
            auto *Part = NewObject<UStaticMeshComponent>(this);
            Part->SetStaticMesh(Placement.Mesh);
            const double Scale = Placement.Radius / FMath::Max(1.0, double(Placement.Mesh->GetBounds().SphereRadius));
            const FQuat Rotation = GroupRotation * Placement.Rotation.Quaternion();
            const FVector Location = Center + GroupRotation.RotateVector(Placement.Center) -
                                     Rotation.RotateVector(Placement.Mesh->GetBounds().Origin * Scale);
            Register(Part);
            Part->SetCastShadow(true);
            Part->SetRelativeTransform(FTransform(Rotation, Location, FVector(Scale)));
            ++Cell.Landmarks;
        }
    }
    const auto &A = Look->AreaRecipes[Blend.First];
    const auto &B = Look->AreaRecipes[Blend.Second];
    const float DensityA = FMath::IsFinite(A.ClutterDensity) ? FMath::Clamp(A.ClutterDensity, 0.f, 2.f) : 0.f;
    const float DensityB = FMath::IsFinite(B.ClutterDensity) ? FMath::Clamp(B.ClutterDensity, 0.f, 2.f) : 0.f;
    const float Density = FMath::Lerp(DensityA, DensityB, Blend.Alpha);
    // Stable quiet pockets reduce near/middle density; the independent distant field remains rich.
    const float Gap = Random.FRand() < .18f && !Origin ? .25f : 1.f;
    const int32 Count =
        FMath::Clamp(FMath::RoundToInt(ClutterPerCell * FMath::Clamp(Density, 0.f, 2.f) * Gap), 0, ClutterPerCell);
    TMap<UStaticMesh *, UInstancedStaticMeshComponent *> Batches;
    for (int32 Index = 0; Index < Count; ++Index)
    {
        const auto &Style = Random.FRand() < Blend.Alpha ? B : A;
        float Total = 0;
        for (const auto &Candidate : Style.Clutter)
            if (Candidate.Mesh && FMath::IsFinite(Candidate.Weight) && Candidate.Weight > 0)
                Total += Candidate.Weight;
        if (Total <= 0)
            continue;
        float Choice = Random.FRand() * Total;
        const FSSSceneryCandidate *Selected = nullptr;
        for (const auto &Candidate : Style.Clutter)
            if (Candidate.Mesh && FMath::IsFinite(Candidate.Weight) && Candidate.Weight > 0)
            {
                Choice -= Candidate.Weight;
                if (Choice <= 0)
                {
                    Selected = &Candidate;
                    break;
                }
            }
        if (!Selected || !FMath::IsFinite(Selected->MinRadius) || !FMath::IsFinite(Selected->MaxRadius))
            continue;
        const float MinimumRadius = FMath::Max(1.f, Selected->MinRadius);
        const double Radius = Random.FRandRange(MinimumRadius, FMath::Max(MinimumRadius, Selected->MaxRadius));
        const double ClusterRadius = FMath::IsFinite(Style.ClusterRadius)
                                         ? FMath::Clamp(double(Style.ClusterRadius), 1000.0, Size * .3)
                                         : Size * .18;
        const FVector Axes = Style.ClusterAxes.ContainsNaN() ? FVector(1.6, .55, .3)
                                                             : Style.ClusterAxes.GetAbs().ComponentMin(FVector(2));
        const FVector ClusterCenter =
            FVector(.22 * Size, (Index % 2 ? -.22 : .22) * Size, (Index % 3 - 1) * .12 * Size);
        const FVector Offset = ClusterCenter + Random.VRand() * Random.FRandRange(.15, 1.0) * Axes * ClusterRadius;
        const double Clearance =
            FMath::IsFinite(Style.ClearRadius) ? FMath::Max(1000.0, double(Style.ClearRadius)) : 35000.0;
        if (Offset.Size() < Clearance + Radius)
            continue;
        auto *Mesh = Selected->Mesh.Get();
        auto *&Batch = Batches.FindOrAdd(Mesh);
        if (!Batch)
        {
            Batch = NewObject<UInstancedStaticMeshComponent>(this);
            Batch->SetStaticMesh(Mesh);
            Register(Batch);
        }
        const double Scale = Radius / FMath::Max(1.0, double(Mesh->GetBounds().SphereRadius));
        const FQuat Rotation = Random.VRand().ToOrientationQuat();
        const FVector Location =
            Center + GroupRotation.RotateVector(Offset) - Rotation.RotateVector(Mesh->GetBounds().Origin * Scale);
        Batch->AddInstance(FTransform(Rotation, Location, FVector(Scale)));
        ++Cell.Clutter;
    }
    ResidentClutter += Cell.Clutter;
    ResidentLandmarks += Cell.Landmarks;
}
