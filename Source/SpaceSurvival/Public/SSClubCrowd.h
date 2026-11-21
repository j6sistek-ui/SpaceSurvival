#pragma once
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "GameFramework/Actor.h"
#include "Domain/ClubCrowd.h"
#include "SSClubCrowd.generated.h"

class ASSOutpostAmbientActor;
class UAnimSequence;
class UArrowComponent;
class USceneComponent;

/** Mirrors SS::Club::Category; the order must match. */
UENUM(BlueprintType)
enum class ESSClubCategory : uint8
{
    Dancing,
    Bar,
    Lounge,
    Social,
    Moving,
    Special
};

UENUM(BlueprintType)
enum class ESSClubPosture : uint8
{
    Standing,
    Seated
};

UENUM(BlueprintType)
enum class ESSClubProp : uint8
{
    None,
    Glass,
    Shot,
    Bottle,
    Tray
};

/** One usable clip in the club library (docs/production/CLUB_AMBIENCE_PLAN.md, Props and contact). */
USTRUCT(BlueprintType)
struct FSSClubClipRow : public FTableRowBase
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club")
    TObjectPtr<UAnimSequence> Clip;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club")
    ESSClubCategory Activity = ESSClubCategory::Dancing;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club")
    ESSClubPosture Posture = ESSClubPosture::Standing;
    /** What the hands hold. Recorded now; attaching the prop is Phase 4. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club")
    ESSClubProp Prop = ESSClubProp::None;
    /** Dance style, 0 = any. A patron keeps one style. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club", meta = (ClampMin = "0"))
    int32 Style = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club", meta = (ClampMin = "0"))
    float Weight = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club")
    bool bLoop = true;
    /** Recorded for later: single-node playback cannot mirror yet, so the director never mirrors. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club")
    bool bMirrorSafe = false;
};

/** A place a patron can do one activity: a dance-floor spot, stool, lounge seat or group table. Facing = actor yaw. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSClubActivitySpot : public AActor
{
    GENERATED_BODY()
public:
    ASSClubActivitySpot();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Club")
    TObjectPtr<USceneComponent> Root;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Club")
    TObjectPtr<UArrowComponent> Facing;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club")
    ESSClubCategory Activity = ESSClubCategory::Dancing;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club")
    ESSClubPosture Posture = ESSClubPosture::Standing;
    /** Group tables hold several patrons; stools and seats hold one. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club", meta = (ClampMin = "1", ClampMax = "8"))
    int32 Capacity = 1;
    /** Seat top above the spot origin, in cm. Recorded now; hip fitting is Phase 4. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club", meta = (ClampMin = "0", ClampMax = "120"))
    float SeatHeight = 0.f;
};

USTRUCT(BlueprintType)
struct FSSClubPatron
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club")
    TObjectPtr<ASSOutpostAmbientActor> Actor;
    /** Dance style this patron keeps, 0 = any. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club", meta = (ClampMin = "0"))
    int32 DanceStyle = 0;
};

/**
 * One per venue. Keeps the crowd mix, gives patrons free spots, picks clips by the plan's variation rules and sets a
 * detail tier per patron. The rules live in SS::Club::Director (engine-independent, unit tested); this actor applies
 * them to existing ambient NPCs, which hand their animation over (bAnimationManagedExternally).
 */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSClubCrowdDirector : public AActor
{
    GENERATED_BODY()
public:
    ASSClubCrowdDirector();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club")
    TObjectPtr<UDataTable> ClipTable;
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Club")
    TArray<FSSClubPatron> Patrons;
    /** Empty: every activity spot in the level. */
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Club")
    TArray<TObjectPtr<ASSClubActivitySpot>> Spots;
    /** 0 picks a new seed each session; the seed is logged so a night can be replayed exactly. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club")
    int32 Seed = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club", meta = (ClampMin = "100"))
    float SyncRadius = 800.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club", meta = (ClampMin = "0"))
    int32 HeroCount = 8;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club", meta = (ClampMin = "100"))
    float NearRadius = 1500.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club", meta = (ClampMin = "100"))
    float MidRadius = 3000.f;
    /** Animation update interval per tier (seconds; 0 = every frame): Hero, Near, Mid, Far. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club|Detail")
    FVector4 TierAnimationInterval = FVector4(0.f, 1.f / 30.f, 1.f / 15.f, 1.f / 8.f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Club|Detail")
    bool bApplyDetailTiers = true;

    UFUNCTION(BlueprintPure, Category = "Club")
    int32 ActiveSeed() const
    {
        return ActiveSeedValue;
    }

private:
    TUniquePtr<SS::Club::Director> Rules;
    /** Domain clip index -> asset, domain patron index -> actor, domain spot index -> actor. */
    UPROPERTY(Transient)
    TArray<TObjectPtr<UAnimSequence>> ClipAssets;
    UPROPERTY(Transient)
    TArray<TObjectPtr<ASSOutpostAmbientActor>> PatronActors;
    UPROPERTY(Transient)
    TArray<TObjectPtr<ASSClubActivitySpot>> SpotActors;
    int32 ActiveSeedValue = 0;
    double StartSeconds = 0.0;

    void Apply(const SS::Club::Play &Play);
    void FollowWalkers(float DeltaSeconds);
    void ApplyTiers();
};
