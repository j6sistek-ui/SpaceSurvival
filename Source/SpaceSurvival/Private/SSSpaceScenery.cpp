#include "SSSpaceScenery.h"
#include "SSSpaceLookData.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Misc/PackageName.h"
#include "HAL/IConsoleManager.h"
namespace
{
TAutoConsoleVariable<int32> StructuresEnabled(TEXT("ss.SpaceStructures"), 1,
                                              TEXT("Distant decorative structures (0 disables). No gameplay impact."),
                                              ECVF_Scalability);
}
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
    if (!Data)
        return;
    const FVector Positions[] = {FVector(145000, -85000, 24000), FVector(320000, 130000, -45000),
                                 FVector(-240000, -165000, 60000), FVector(420000, -90000, 100000)};
    for (int32 Index = 0; Index < FMath::Min(4, Data->StructureMeshes.Num()); ++Index)
    {
        auto *Mesh = Data->StructureMeshes[Index].Get();
        if (!Mesh)
            continue;
        auto *Part = NewObject<UStaticMeshComponent>(this);
        Part->SetupAttachment(RootComponent);
        Part->SetStaticMesh(Mesh);
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetGenerateOverlapEvents(false);
        Part->SetCanEverAffectNavigation(false);
        Part->SetCastShadow(false);
        Part->SetMobility(EComponentMobility::Movable);
        const double Scale = (Index == 0 ? 13500.0 : 19000.0) / FMath::Max(1.0, double(Mesh->GetBounds().SphereRadius));
        const FQuat Rotation = FRotator(25 + Index * 17, -45 + Index * 60, Index * 11).Quaternion();
        const FVector Anchor = Positions[Index] - Rotation.RotateVector(Mesh->GetBounds().Origin * Scale);
        Part->SetRelativeTransform(FTransform(Rotation, Anchor, FVector(Scale)));
        Part->RegisterComponent();
        Structures.Add(Part);
        Anchors.Add(Anchor);
    }
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
        SetActorLocation(LastCenter);
        AddTickPrerequisiteActor(Viewer);
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
}
