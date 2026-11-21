#include "SSClubCrowd.h"
#include "SSOutpostSandbox.h"
#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/ArrowComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"

namespace
{
static_assert(static_cast<int>(ESSClubCategory::Special) + 1 == SS::Club::CategoryCount,
              "ESSClubCategory must mirror SS::Club::Category");

std::string SkeletonId(const USkeleton *Skeleton)
{
    return Skeleton ? std::string(TCHAR_TO_UTF8(*Skeleton->GetPathName())) : std::string();
}

SS::Club::Vec3 ToRules(const FVector &Location)
{
    return {Location.X, Location.Y, Location.Z};
}

FVector FromRules(const SS::Club::Vec3 &Position)
{
    return FVector(Position.x, Position.y, Position.z);
}

/** Capsule-centre location standing on the deck at a floor-level point; keeps Z when no deck is found. */
FVector StandOnDeck(const ASSOutpostAmbientActor &Actor, const FVector &FloorPoint)
{
    const float HalfHeight = Actor.Body ? Actor.Body->GetScaledCapsuleHalfHeight() : 90.f;
    FVector Result = FloorPoint + FVector(0, 0, HalfHeight);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(ClubCrowdFloor), false, &Actor);
    FHitResult Ground;
    // Same rule as the ambient walker: only upward-facing static deck supports crew.
    if (Actor.GetWorld()->LineTraceSingleByObjectType(Ground, FloorPoint + FVector(0, 0, 70),
                                                      FloorPoint - FVector(0, 0, 260),
                                                      FCollisionObjectQueryParams(ECC_WorldStatic), Query) &&
        Ground.ImpactNormal.Z > .7f)
        Result.Z = Ground.ImpactPoint.Z + HalfHeight + 2.f;
    return Result;
}
} // namespace

ASSClubActivitySpot::ASSClubActivitySpot()
{
    PrimaryActorTick.bCanEverTick = false;
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    RootComponent = Root;
    Facing = CreateDefaultSubobject<UArrowComponent>(TEXT("Facing"));
    Facing->SetupAttachment(Root);
    Facing->SetHiddenInGame(true);
}

ASSClubCrowdDirector::ASSClubCrowdDirector()
{
    PrimaryActorTick.bCanEverTick = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void ASSClubCrowdDirector::BeginPlay()
{
    Super::BeginPlay();
    SS::Club::Settings Settings;
    Settings.syncRadius = SyncRadius;
    Settings.heroCount = HeroCount;
    Settings.nearRadius = NearRadius;
    Settings.midRadius = FMath::Max(MidRadius, NearRadius);
    ActiveSeedValue = Seed != 0 ? Seed : FMath::RandRange(1, MAX_int32);
    Rules = MakeUnique<SS::Club::Director>(static_cast<std::uint32_t>(ActiveSeedValue), Settings);

    ClipAssets.Reset();
    if (ClipTable && ClipTable->GetRowStruct() && ClipTable->GetRowStruct()->IsChildOf(FSSClubClipRow::StaticStruct()))
    {
        for (const FName &Name : ClipTable->GetRowNames())
        {
            const auto *Row = ClipTable->FindRow<FSSClubClipRow>(Name, TEXT("ClubCrowd"), false);
            if (!Row || !Row->Clip || !Row->Clip->GetSkeleton() || Row->Clip->GetPlayLength() <= .01f)
                continue;
            SS::Club::Clip Clip;
            Clip.id = TCHAR_TO_UTF8(*Name.ToString());
            Clip.category = static_cast<SS::Club::Category>(Row->Activity);
            Clip.posture = static_cast<SS::Club::Posture>(Row->Posture);
            Clip.prop = static_cast<SS::Club::Prop>(Row->Prop);
            Clip.skeleton = SkeletonId(Row->Clip->GetSkeleton());
            Clip.style = Row->Style;
            Clip.seconds = Row->Clip->GetPlayLength();
            Clip.weight = Row->Weight;
            Clip.loop = Row->bLoop;
            Clip.mirrorSafe = false; // single-node playback cannot mirror yet
            Rules->AddClip(Clip);
            ClipAssets.Add(Row->Clip);
        }
    }

    SpotActors.Reset();
    if (Spots.IsEmpty())
        for (TActorIterator<ASSClubActivitySpot> It(GetWorld()); It; ++It)
            SpotActors.Add(*It);
    else
        for (ASSClubActivitySpot *Spot : Spots)
            if (IsValid(Spot))
                SpotActors.Add(Spot);
    for (ASSClubActivitySpot *Spot : SpotActors)
    {
        SS::Club::Spot Rule;
        Rule.category = static_cast<SS::Club::Category>(Spot->Activity);
        Rule.posture = static_cast<SS::Club::Posture>(Spot->Posture);
        Rule.position = ToRules(Spot->GetActorLocation());
        Rule.capacity = Spot->Capacity;
        Rules->AddSpot(Rule);
    }

    PatronActors.Reset();
    for (const FSSClubPatron &Entry : Patrons)
    {
        ASSOutpostAmbientActor *Actor = Entry.Actor;
        if (!IsValid(Actor) || Actor->bDrone || !Actor->CharacterMesh || !Actor->CharacterMesh->GetSkeletalMeshAsset())
            continue;
        // The director owns this NPC's animation and position from now on; its own route/gesture loop stops.
        Actor->bAnimationManagedExternally = true;
        Actor->RoutePoints.Reset();
        const float HalfHeight = Actor->Body ? Actor->Body->GetScaledCapsuleHalfHeight() : 90.f;
        Rules->AddPatron(SkeletonId(Actor->CharacterMesh->GetSkeletalMeshAsset()->GetSkeleton()), Entry.DanceStyle,
                         ToRules(Actor->GetActorLocation() - FVector(0, 0, HalfHeight)));
        PatronActors.Add(Actor);
    }

    UE_LOG(LogTemp, Display, TEXT("club crowd %s: seed %d, %d patrons, %d spots, %d clips"), *GetName(),
           ActiveSeedValue, PatronActors.Num(), SpotActors.Num(), ClipAssets.Num());
    if (ClipAssets.IsEmpty() || SpotActors.IsEmpty())
        UE_LOG(LogTemp, Warning, TEXT("club crowd %s has no usable clips or spots; patrons keep their last pose"),
               *GetName());
}

void ASSClubCrowdDirector::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!Rules || PatronActors.IsEmpty())
        return;
    FVector Viewer = GetActorLocation();
    if (const APlayerCameraManager *Camera = UGameplayStatics::GetPlayerCameraManager(this, 0))
        Viewer = Camera->GetCameraLocation();
    for (const SS::Club::Play &Play : Rules->Update(GetWorld()->GetTimeSeconds(), ToRules(Viewer)))
        Apply(Play);
    FollowWalkers(DeltaSeconds);
    if (bApplyDetailTiers)
        ApplyTiers();
}

void ASSClubCrowdDirector::Apply(const SS::Club::Play &Play)
{
    if (!PatronActors.IsValidIndex(Play.patron) || !ClipAssets.IsValidIndex(Play.clip))
        return;
    ASSOutpostAmbientActor *Actor = PatronActors[Play.patron];
    UAnimSequence *Clip = ClipAssets[Play.clip];
    if (!IsValid(Actor) || !Clip)
        return;
    USkeletalMeshComponent *Mesh = Actor->CharacterMesh;
    if (!Mesh || !Mesh->GetSkeletalMeshAsset() || Mesh->GetSkeletalMeshAsset()->GetSkeleton() != Clip->GetSkeleton())
        return;
    const SS::Club::Clip &Rule = Rules->Clips()[Play.clip];
    Mesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    Mesh->PlayAnimation(Clip, Rule.loop);
    Mesh->SetPlayRate(static_cast<float>(Play.playRate));
    Mesh->SetPosition(static_cast<float>(Play.startFraction) * Clip->GetPlayLength(), false);

    // Arrived (or placed at the start of the night): stand on the spot and face its arrow.
    if (!Play.travelling && SpotActors.IsValidIndex(Play.spot) && IsValid(SpotActors[Play.spot]))
    {
        const ASSClubActivitySpot *Spot = SpotActors[Play.spot];
        Actor->SetActorLocationAndRotation(StandOnDeck(*Actor, Spot->GetActorLocation()),
                                           FRotator(0, Spot->GetActorRotation().Yaw, 0));
    }
}

void ASSClubCrowdDirector::FollowWalkers(float DeltaSeconds)
{
    const auto &Rulebook = Rules->Patrons();
    for (int32 Index = 0; Index < PatronActors.Num() && Index < static_cast<int32>(Rulebook.size()); ++Index)
    {
        const SS::Club::Patron &Patron = Rulebook[Index];
        ASSOutpostAmbientActor *Actor = PatronActors[Index];
        if (!Patron.travelling || !IsValid(Actor))
            continue;
        const FVector Before = Actor->GetActorLocation();
        const FVector Next = StandOnDeck(*Actor, FromRules(Patron.position));
        const FVector Delta = Next - Before;
        // No sweep: a blocked walker would pop on arrival, which reads worse than briefly brushing past someone.
        Actor->SetActorLocation(Next, false);
        if (Delta.SizeSquared2D() > 1.f)
            Actor->SetActorRotation(
                FMath::RInterpTo(Actor->GetActorRotation(), FRotator(0, Delta.Rotation().Yaw, 0), DeltaSeconds, 6.f));
    }
}

void ASSClubCrowdDirector::ApplyTiers()
{
    const auto &Rulebook = Rules->Patrons();
    const float Intervals[] = {static_cast<float>(TierAnimationInterval.X), static_cast<float>(TierAnimationInterval.Y),
                               static_cast<float>(TierAnimationInterval.Z),
                               static_cast<float>(TierAnimationInterval.W)};
    for (int32 Index = 0; Index < PatronActors.Num() && Index < static_cast<int32>(Rulebook.size()); ++Index)
    {
        ASSOutpostAmbientActor *Actor = PatronActors[Index];
        if (!IsValid(Actor) || !Actor->CharacterMesh)
            continue;
        const float Interval = FMath::Max(0.f, Intervals[static_cast<int32>(Rulebook[Index].tier)]);
        if (!FMath::IsNearlyEqual(Actor->CharacterMesh->GetComponentTickInterval(), Interval))
            Actor->CharacterMesh->SetComponentTickInterval(Interval);
    }
}
