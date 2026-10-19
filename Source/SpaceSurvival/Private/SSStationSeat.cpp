#include "SSStationSeat.h"
#include "SSStation.h"
#include "SSBarCrew.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"

ASSStationSeat::ASSStationSeat()
{
    PrimaryActorTick.bCanEverTick = false;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Cushion"));
}

UAnimSequence *ASSStationSeat::ClipFor(const ASSWalker *Walker) const
{
    const auto *Mesh = Walker ? Walker->GetMesh()->GetSkeletalMeshAsset() : nullptr;
    if (Mesh)
        for (const auto &Clip : SeatedAnimations)
            if (Clip && Clip->GetSkeleton() == Mesh->GetSkeleton())
                return Clip;
    return nullptr;
}

bool ASSStationSeat::IsAvailable(const ASSWalker *Walker) const
{
    if (!bEnabled || !Walker || (Occupant.IsValid() && Occupant != Walker) || !ClipFor(Walker))
        return false;
    // Native crew are actors, not pawns. Reserve both their occupied place and an approaching waitress's place.
    auto Near = [this](const FVector &Position)
    {
        return FVector::DistSquared2D(Position, GetActorLocation()) < FMath::Square(55.f) &&
               FMath::Abs(Position.Z - GetActorLocation().Z) < 180.f;
    };
    for (TActorIterator<APawn> It(GetWorld()); It; ++It)
        if (*It != Walker && !It->IsHidden() && Near(It->GetActorLocation()))
            return false;
    for (TActorIterator<ASSOutpostAmbientActor> It(GetWorld()); It; ++It)
        if (!It->IsHidden() && Near(It->GetActorLocation()))
            return false;
    for (TActorIterator<ASSBarTable> It(GetWorld()); It; ++It)
        if (It->Occupant.IsValid() && Near(It->Seat->GetComponentLocation()))
            return false;
    return true;
}

bool ASSStationSeat::CanReach(const ASSWalker *Walker) const
{
    if (!Walker || FVector::DistSquared2D(GetActorLocation(), Walker->GetActorLocation()) > FMath::Square(Reach) ||
        FMath::Abs(GetActorLocation().Z - Walker->GetActorLocation().Z) > 150.f)
        return false;
    // Approach from an authored exit side. Bar stools face a counter but are entered from behind.
    const FVector Local = GetActorTransform().InverseTransformPosition(Walker->GetActorLocation());
    bool OpenSide = false;
    for (const FVector &Offset : StandOffsets)
        OpenSide |= FVector::DotProduct(FVector(Local.X, Local.Y, 0), Offset.GetSafeNormal2D()) >= 10.f;
    if (!OpenSide)
        return false;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSSeatReach), false, Walker);
    Query.AddIgnoredActor(this);
    Query.AddIgnoredActor(Furniture);
    return !GetWorld()->LineTraceTestByChannel(Walker->GetActorLocation(), GetActorLocation() + FVector(0, 0, 55),
                                               ECC_Visibility, Query);
}

bool ASSStationSeat::FindExit(const ASSWalker *Walker, FTransform &Out) const
{
    if (!Walker)
        return false;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSSeatExit), false, Walker);
    Query.AddIgnoredActor(this);
    const float Half = Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
    for (const FVector &Offset : StandOffsets)
    {
        FVector Point = GetActorTransform().TransformPosition(Offset);
        FHitResult Floor;
        if (!GetWorld()->LineTraceSingleByChannel(Floor, Point + FVector(0, 0, 40), Point - FVector(0, 0, 230),
                                                  ECC_Pawn, Query) ||
            Floor.ImpactNormal.Z < Walker->GetCharacterMovement()->GetWalkableFloorZ() || Floor.GetActor() == Furniture)
            continue;
        Point.Z = Floor.ImpactPoint.Z + Half + 2.15f;
        bool CrewInExit = false;
        for (TActorIterator<ASSOutpostAmbientActor> It(GetWorld()); It; ++It)
            if (!It->IsHidden() && FVector::DistSquared2D(It->GetActorLocation(), Point) < FMath::Square(55.f) &&
                FMath::Abs(It->GetActorLocation().Z - Point.Z) < 150.f)
                CrewInExit = true;
        if (CrewInExit)
            continue;
        if (GetWorld()->OverlapBlockingTestByChannel(Point, FQuat::Identity, ECC_Pawn,
                                                     Walker->GetCapsuleComponent()->GetCollisionShape(), Query))
            continue;
        FCollisionQueryParams PathQuery = Query;
        PathQuery.AddIgnoredActor(Furniture);
        if (GetWorld()->LineTraceTestByChannel(GetActorLocation() + FVector(0, 0, 55), Point, ECC_Pawn, PathQuery))
            continue;
        Out = FTransform(GetActorRotation(), Point, Walker->GetActorScale3D());
        return true;
    }
    return false;
}

ASSStationSeat *ASSStationSeat::Find(const ASSWalker *Walker)
{
    if (!Walker || Walker->IsResting() || Walker->IsBoarding() || Walker->IsDisembarking() ||
        !Walker->GetCharacterMovement()->IsMovingOnGround())
        return nullptr;
    ASSStationSeat *Best = nullptr;
    float Distance = MAX_flt;
    for (TActorIterator<ASSStationSeat> It(Walker->GetWorld()); It; ++It)
    {
        const float D = FVector::DistSquared2D(It->GetActorLocation(), Walker->GetActorLocation());
        FTransform Exit;
        if (D < Distance && It->CanReach(Walker) && It->IsAvailable(Walker) && It->FindExit(Walker, Exit))
        {
            Best = *It;
            Distance = D;
        }
    }
    return Best;
}
