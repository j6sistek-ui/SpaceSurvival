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
class UPointLightComponent;
class USSNPCHeadFillComponent;
class USkeletalMeshComponent;
class UStaticMeshComponent;

/** Presentation-map rules; the current station authoring map enters the full game on Play. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSOutpostSandboxGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    ASSOutpostSandboxGameMode();
    virtual void BeginPlay() override;
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

/** One thing a crew member can be asked to do, by a spoken word or a key: a clip, and a line said as it starts
 *  (owner 2026-10-14: "add ways to interact... to initiate various animations, so they don't just sit idle"). */
USTRUCT(BlueprintType)
struct FSSNpcAction
{
    GENERATED_BODY()
    /** Prompt label ("Pour a drink"). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Talk")
    FString Name;
    /** Lower-case words that trigger it from what the pilot said ("pour", "gin", "nebula"). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Talk")
    TArray<FString> Keywords;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Talk")
    TObjectPtr<UAnimSequence> Clip;
    /** A looping clip holds for LoopSeconds; a one-shot plays once. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Talk")
    bool bLoop = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Talk")
    float LoopSeconds = 15.f;
    /** Said in their own voice as the clip starts ("One Nebula, coming up."). Empty: silent. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Talk")
    FString Line;
};

/** Local authored route for crew or drone; capsule sweeps keep walkers from crossing walls. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSOutpostAmbientActor : public AActor
{
    GENERATED_BODY()
public:
    ASSOutpostAmbientActor();
    virtual void OnConstruction(const FTransform &Transform) override;
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void ApplyWorldOffset(const FVector &InOffset, bool bWorldShift) override;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ambient")
    TObjectPtr<UCapsuleComponent> Body;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ambient")
    TObjectPtr<USkeletalMeshComponent> CharacterMesh;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ambient")
    TObjectPtr<UStaticMeshComponent> DroneMesh;
    /** Shared NPC-only fill; channel 1 remains reserved for the player. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ambient|Readability")
    TObjectPtr<UPointLightComponent> HeadFillLight;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ambient|Readability")
    TObjectPtr<USSNPCHeadFillComponent> HeadFillConfiguration;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient|Readability")
    bool bEnableHeadFill = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient|Readability")
    FName HeadFillSocket = TEXT("head");
    /** Actor-frame centimetres from the animated head, independent of the model's mesh yaw/scale. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient|Readability")
    FVector HeadFillOffset = FVector(45.f, 0.f, 15.f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient|Readability",
              meta = (ClampMin = "0", ClampMax = "100"))
    float HeadFillLumens = 40.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient|Readability",
              meta = (ClampMin = "60", ClampMax = "140"))
    float HeadFillRadius = 100.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient|Readability",
              meta = (ClampMin = "0", ClampMax = "20"))
    float HeadFillSourceRadius = 12.f;
    /** Call after changing mesh, materials, socket or profile at runtime; no separate light Tick. */
    UFUNCTION(BlueprintCallable, Category = "Ambient|Readability")
    void RefreshReadabilityLighting();
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
    /** Push-to-talk identity (docs/NPC_TALK.md). Empty TalkName: the mesh name ("SK_Dread" is Dread). TalkRole names
     *  a scenario file (Pool, Bartender, Guard); TalkActivity is the live detail told to the model ("just scratched
     *  on the eight ball"). */
    /** False for unavailable crew, such as the permanently sleeping bar patron. Keeps the idle animation. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Talk")
    bool bConversationEnabled = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Talk")
    FString TalkName;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Talk")
    FString TalkRole;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Talk")
    FString TalkActivity;
    /** What the pilot can ask of them: keys 1-4 (D-pad on a pad) while the talk hint shows, or a keyword in what the
     *  pilot said. Empty for crew who only idle. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Talk")
    TArray<FSSNpcAction> Actions;
    /** Seconds of idle between gestures; the bartender keeps a short one so she is never standing still
     *  (owner 2026-10-14: "needs to be the life of the room"). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    float GestureInterval = 9.f;
    /** Said out loud, unprompted, while the pilot is within earshot and nobody is talking to her (owner 2026-10-14:
     *  "constantly chatty, audibly"). "line|Action name" also plays that action as the line starts. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Talk")
    TArray<FString> Chatter;
    /** Seconds between unprompted lines (the next one lands between this and half again as long). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Talk")
    float ChatterInterval = 30.f;
    /** The next unprompted line in order, with "|Action name" still attached. */
    FString TakeChatterLine();
    /** Plays that action's clip now and returns whether it could. */
    UFUNCTION(BlueprintCallable, Category = "Talk")
    virtual bool TriggerAction(int32 Index);
    /** The first action one of whose keywords occurs in the text, or -1. */
    UFUNCTION(BlueprintPure, Category = "Talk")
    int32 MatchAction(const FString &SpokenText) const;
    virtual bool IsActionPlaying() const
    {
        return ActionRemaining > 0.f;
    }
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    float TravelSpeed = 120.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    float PauseAtWaypoint = 2.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    float BobAmplitude = 12.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambient")
    float PhaseOffset = 0.f;

protected:
    /** Use a fitted variant for one action without changing the authored action list. */
    bool TriggerActionClip(int32 Index, UAnimSequence *ClipOverride);

private:
    // Legacy ownership is restored once before handing the mask to HeadFillConfiguration.
    UPROPERTY()
    bool bHeadFillOwnsChannel = false;
    UPROPERTY()
    bool bHeadFillPreviousChannel2 = false;
    FTransform RouteOrigin;
    int32 RouteIndex = 0, GestureIndex = 0;
    float WaitRemaining = 0.f, Elapsed = 0.f, GestureRemaining = 0.f, NextGesture = 6.f, BlockedSeconds = 0.f;
    float ActionRemaining = 0.f, NextChatter = 12.f;
    int32 ChatterIndex = 0;
    UPROPERTY()
    TObjectPtr<UAnimSequence> ActiveAnimation;
    void PlayClip(UAnimSequence *Clip, bool bLoop);
};
