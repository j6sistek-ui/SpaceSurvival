#pragma once
#include "CoreMinimal.h"
#include "SSOutpostSandbox.h"
#include "SSBarCrew.generated.h"

/** Authored contacts on an existing table/chair; does not create furniture. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSBarTable : public AActor
{
    GENERATED_BODY()
public:
    ASSBarTable();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bar")
    TObjectPtr<USceneComponent> Approach;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bar")
    TObjectPtr<USceneComponent> Seat;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bar")
    TObjectPtr<USceneComponent> DrinkContact;
    TWeakObjectPtr<AActor> Occupant;
};

UENUM(BlueprintType)
enum class ESSBarServiceState : uint8
{
    Available,
    GoingToBar,
    WaitingForBar,
    ReturningToGuest,
    Serving,
    JoiningTable,
    Seated,
    Drinking,
    ReturningHome
};

/** Existing NPC interaction route, with explicit service ownership and hand-attached props. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSBarCrew : public ASSOutpostAmbientActor
{
    GENERATED_BODY()
public:
    ASSBarCrew();
    virtual void OnConstruction(const FTransform &Transform) override;
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void Tick(float DeltaSeconds) override;
    virtual bool TriggerAction(int32 Index) override;
    virtual bool IsActionPlaying() const override;
    virtual void ApplyWorldOffset(const FVector &Offset, bool bWorldShift) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    bool bIsBartender = false;
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Bar")
    TObjectPtr<ASSBarCrew> Bartender;
    /** Pickup is a capsule-centre location on the guest side of the counter. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    FVector PickupOffset = FVector(0, 120, 0);
    /** Safe corridor points relative to the placed waitress. Direct visible links are searched at request time. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    TArray<FVector> ServiceWaypoints;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    TObjectPtr<UAnimSequence> CarryAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    TObjectPtr<UAnimSequence> ServeAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    TObjectPtr<UAnimSequence> SeatedAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    TObjectPtr<UAnimSequence> DrinkAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar", meta = (ClampMin = "100"))
    float GuestDepartureDistance = 650.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    FName GlassHand = TEXT("hand_l");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    FName BottleHand = TEXT("hand_r");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    FName DrinkHand = TEXT("hand_r");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    FTransform GlassGrip;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    FTransform BottleGrip;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    FTransform DrinkGrip;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    FVector2D PourPropWindow = FVector2D(0, 100);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bar")
    FVector2D CheersPropWindow = FVector2D(0, 100);
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bar")
    TObjectPtr<USkeletalMeshComponent> Corset;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bar")
    TObjectPtr<USkeletalMeshComponent> Shorts;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bar")
    TObjectPtr<UStaticMeshComponent> Glass;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bar")
    TObjectPtr<UStaticMeshComponent> Bottle;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bar")
    TObjectPtr<UStaticMeshComponent> ServedGlass;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bar")
    ESSBarServiceState ServiceState = ESSBarServiceState::Available;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bar")
    FString ServiceNotice;
    /** Explicit guest entry point for native interaction and review fixtures. */
    UFUNCTION(BlueprintCallable, Category = "Bar")
    bool RequestService(int32 ActionIndex, APawn *Guest);

private:
    TWeakObjectPtr<APawn> ServiceGuest;
    TWeakObjectPtr<ASSBarTable> Table;
    TWeakObjectPtr<ASSBarTable> DeliveryTable;
    TWeakObjectPtr<ASSBarCrew> ReservedBy;
    TWeakObjectPtr<UAnimSequence> ServiceClip;
    FTransform Home;
    FVector GuestOrigin = FVector::ZeroVector;
    TArray<FVector> Path;
    int32 PathIndex = 0, BarAction = INDEX_NONE;
    float StateTime = 0, BlockedTime = 0, ChatterTime = 8.f;
    bool bDrinkTogether = false;
    void ConfigureParts();
    void PlayService(UAnimSequence *Clip, bool bLoop, bool bRestart = false);
    void SetState(ESSBarServiceState State, const FString &Activity);
    bool PlanPath(const FVector &Destination);
    bool MoveAlongPath(float DeltaSeconds);
    void ReturnHome(const FString &Reason);
    void ReleaseTable();
    ASSBarTable *FindTable(APawn *Guest) const;
    bool BeginPour(ASSBarCrew *Waitress);
};
