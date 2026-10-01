#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "GameFramework/PlayerController.h"
#include "SSOutpostSandbox.generated.h"

class UAnimSequence;
class UBoxComponent;
class UCapsuleComponent;
class UMaterialInterface;
class USkeletalMeshComponent;
class UStaticMeshComponent;

/** Isolated presentation-map rules. No economy or progression is simulated here. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSOutpostSandboxGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    ASSOutpostSandboxGameMode();
    virtual void HandleStartingNewPlayer_Implementation(APlayerController *NewPlayer) override;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outpost")
    FName PreferredHeroId = TEXT("Squirrel");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outpost")
    FName GameplayMap = TEXT("/Game/SpaceSurvival/Maps/Survival");
};

UENUM(BlueprintType)
enum class ESSOutpostAction : uint8
{
    Information,
    CycleShipPaint,
    CycleWardrobe,
    SurvivalBoarding,
    FreeFlight
};

/** Place at a console's use point. All transactions recheck range and sight. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSOutpostTerminal : public AActor
{
    GENERATED_BODY()
public:
    ASSOutpostTerminal();
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outpost")
    FString DisplayName = TEXT("OUTPOST SERVICES");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outpost", meta = (MultiLine = true))
    FString Description = TEXT("Display preview. Service integration is not enabled in this design sandbox.");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outpost")
    ESSOutpostAction Action = ESSOutpostAction::Information;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outpost", meta = (ClampMin = "100", ClampMax = "600"))
    float UseDistance = 300.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outpost")
    TObjectPtr<AActor> PresentationTarget;
    /** Explicit opt-in prevents accidental repainting of glazing or interior materials. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Paint")
    FName PaintComponentTag = TEXT("OutpostPaintable");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Paint")
    FName PaintParameter = TEXT("HullTint");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Paint")
    TArray<int32> PaintMaterialSlots = {0};
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Paint")
    TArray<FLinearColor> PaintPalette;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Wardrobe")
    TObjectPtr<UMaterialInterface> HologramMaterial;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Wardrobe")
    float HologramHeight = 185.f;
    UFUNCTION(BlueprintCallable, Category = "Outpost")
    FString Use(APlayerController *User);
    bool CanUse(const APawn *User) const;

private:
    int32 PreviewIndex = -1;
    FString CyclePaint();
    FString CycleWardrobe();
};

UCLASS()
class SPACESURVIVAL_API ASSOutpostSandboxController : public APlayerController
{
    GENERATED_BODY()
public:
    ASSOutpostSandboxController();
    virtual void BeginPlay() override;
    virtual void PlayerTick(float DeltaSeconds) override;
    UFUNCTION(BlueprintCallable, Category = "Outpost")
    void Interact();
    UFUNCTION(BlueprintPure, Category = "Outpost")
    ASSOutpostTerminal *FocusedTerminal() const;
    FString Notice;
    float NoticeSeconds = 0.f;
    bool IsReviewPaused() const
    {
        return bReviewPaused;
    }

private:
    bool bReviewPaused = false;
    FVector SafeSpawn = FVector::ZeroVector;
};

UCLASS()
class SPACESURVIVAL_API ASSOutpostSandboxHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
};

/** Two sliding leaves. Local X is passage direction and leaves slide on Y. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSOutpostDoor : public AActor
{
    GENERATED_BODY()
public:
    ASSOutpostDoor();
    virtual void OnConstruction(const FTransform &Transform) override;
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Door")
    TObjectPtr<UStaticMeshComponent> LeftLeaf;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Door")
    TObjectPtr<UStaticMeshComponent> RightLeaf;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Door")
    TObjectPtr<UBoxComponent> LeftBlocker;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Door")
    TObjectPtr<UBoxComponent> RightBlocker;
    /** Default 300 cm passage; authored leaf mesh should be centred on its origin. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
    FVector LeftClosed = FVector(0, -75, 150);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
    FVector RightClosed = FVector(0, 75, 150);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
    FVector LeftTravel = FVector(0, -160, 0);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
    FVector RightTravel = FVector(0, 160, 0);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
    FVector LeafHalfExtent = FVector(12, 75, 150);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
    FVector SafetyHalfExtent = FVector(120, 185, 170);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door", meta = (ClampMin = "200"))
    float SensorRadius = 430.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door", meta = (ClampMin = "0.2"))
    float SlideSeconds = .85f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door", meta = (ClampMin = "0.5"))
    float HoldOpenSeconds = 2.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Door")
    float OpenFraction = 0.f;
    UFUNCTION(BlueprintCallable, Category = "Door")
    void RequestOpen();
    UFUNCTION(BlueprintPure, Category = "Door")
    bool IsDoorwayOccupied() const;

private:
    float HoldRemaining = 0.f;
    void PositionLeaves();
};

/** Local authored route for crew or drone; capsule sweeps keep walkers from crossing walls. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSOutpostAmbientActor : public AActor
{
    GENERATED_BODY()
public:
    ASSOutpostAmbientActor();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ambient")
    TObjectPtr<UCapsuleComponent> Body;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ambient")
    TObjectPtr<USkeletalMeshComponent> CharacterMesh;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ambient")
    TObjectPtr<UStaticMeshComponent> DroneMesh;
    /** Positions relative to placed actor transform; origin is capsule centre, not feet. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    TArray<FVector> RoutePoints;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    TObjectPtr<UAnimSequence> IdleAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    TObjectPtr<UAnimSequence> WalkAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    TArray<TObjectPtr<UAnimSequence>> GestureAnimations;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    bool bDrone = false;
    /** A wardrobe projector owns its newly selected mesh/clip; ambient idle must not overwrite it. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    bool bAnimationManagedExternally = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    float TravelSpeed = 120.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    float PauseAtWaypoint = 2.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    float BobAmplitude = 12.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    float PhaseOffset = 0.f;

private:
    FTransform RouteOrigin;
    int32 RouteIndex = 0, GestureIndex = 0;
    float WaitRemaining = 0.f, Elapsed = 0.f, GestureRemaining = 0.f, NextGesture = 6.f, BlockedSeconds = 0.f;
    UPROPERTY()
    TObjectPtr<UAnimSequence> ActiveAnimation;
    void PlayClip(UAnimSequence *Clip, bool bLoop);
};
