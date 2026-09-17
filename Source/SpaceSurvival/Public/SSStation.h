#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Character.h"
#include "SSGameMode.h"
#include "SSContentTypes.h"
#include "SSStation.generated.h"
class ASSShip;
class USSPhase1Data;
class UStaticMesh;
class UStaticMeshComponent;
class UCameraComponent;
class USpringArmComponent;
class UAudioComponent;
class UAnimSequence;
class UTextRenderComponent;
class UMaterialInterface;
class ASSStationVisualLayout;
struct FPoseSnapshot;

UCLASS()
class SPACESURVIVAL_API ASSStation : public AActor
{
    GENERATED_BODY()
public:
    ASSStation();
    void BuildHub(bool bHome);
    UPROPERTY(EditAnywhere, Category = "Presentation")
    bool bUseLicensedPresentation = true;
    UPROPERTY(EditAnywhere, Category = "Presentation")
    bool bUseEditableLayout = true;
    UPROPERTY(EditAnywhere, Category = "Presentation")
    TSoftClassPtr<ASSStationVisualLayout> VisualLayoutAsset;
    ASSStationVisualLayout *GetVisualLayout() const
    {
        return VisualLayout;
    }
    // Optional presentation asset; the physical hub remains authoritative when it is absent.
    UPROPERTY(EditAnywhere, Category = "Presentation")
    TSoftObjectPtr<UStaticMesh> ShellAsset;
    void SetBayShip(int32 ShipKind);
    void ShowBayShip(bool Visible);
    void RefreshPaint();
    bool CanAssistDocking(const ASSShip *Ship) const;
    virtual void Tick(float DeltaSeconds) override;
    virtual void Destroyed() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    ESSPanel NearestService(FVector Position, FString &Label) const;
    FVector WalkSpawn() const
    {
        return GetActorTransform().TransformPosition(FVector(-300, 0, 180));
    }
    FVector DockPosition() const
    {
        return GetActorTransform().TransformPosition(FVector(850, 0, 220));
    }
    bool IsHome() const
    {
        return Home;
    }

private:
    bool BuildEditableLayout();
    void DestroyVisualLayout();
    bool BuildLicensedShell();
    UPROPERTY()
    TObjectPtr<ASSStationVisualLayout> VisualLayout;
    struct FService
    {
        FVector Location;
        FString Label;
        ESSPanel Panel;
    };
    TArray<FService> Services;
    UPROPERTY()
    TObjectPtr<UMaterialInterface> ServiceLabelMaterial;
    UPROPERTY()
    TArray<TObjectPtr<UTextRenderComponent>> ServiceLabels;
    UPROPERTY()
    TArray<TObjectPtr<UStaticMeshComponent>> Geometry;
    UPROPERTY()
    TObjectPtr<UStaticMeshComponent> ServiceArm;
    UPROPERTY()
    TObjectPtr<UStaticMeshComponent> BayShip;
    UPROPERTY()
    TObjectPtr<UStaticMeshComponent> VendorHead;
    UPROPERTY()
    TObjectPtr<UStaticMeshComponent> VendorArm;
    UPROPERTY()
    TObjectPtr<UStaticMeshComponent> BeaconRotor;
    UPROPERTY()
    TObjectPtr<UAudioComponent> Ambience;
    bool Home = false;
    UStaticMeshComponent *AddMesh(FVector Position, FVector Scale, const TCHAR *Mesh, const TCHAR *Material,
                                  bool Solid = false);
    void AddService(FVector Position, const FString &Label, ESSPanel Panel);
};

UCLASS()
class SPACESURVIVAL_API ASSWalker : public ACharacter
{
    GENERATED_BODY()
public:
    ASSWalker();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void ApplyWorldOffset(const FVector &InOffset, bool bWorldShift) override;
    static constexpr float DisembarkDuration = 2.4f;
    bool BeginDisembark(const FTransform &PilotWorldTransform, FVector End, FRotator Facing,
                        const FPoseSnapshot *SourcePose = nullptr);
    bool IsDisembarking() const
    {
        return Disembarking;
    }
    void Move(FVector2D Direction, FVector2D Look, bool Run, float DeltaSeconds);
    /** Whichever hero this build installed. Telemetry and tests ask it for the names and numbers
     *  they used to spell out, so they follow the hero the player is actually wearing. */
    const FSSHeroDefinition &GetHero() const
    {
        return Hero;
    }
    /** Deck plates sit this far above the collision floor; the sole is fitted to them, not to it. */
    static constexpr float DeckClearance = 2.75f;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USpringArmComponent> Boom;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UCameraComponent> Camera;
    UPROPERTY(EditAnywhere)
    TObjectPtr<USSPhase1Data> Tuning;

private:
    TWeakObjectPtr<ASSStation> RecoveryHub;
    FVector ExitStart = FVector::ZeroVector, ExitEnd = FVector::ZeroVector;
    FQuat ExitStartRotation = FQuat::Identity, ExitEndRotation = FQuat::Identity;
    double ExitElapsed = 0.0;
    bool Disembarking = false;
    /** True when the seated pilot is this same hero, so its component transform and its live pose
     *  carry over to the exit. A stand-in that only walks starts the exit from the ship position. */
    bool SharesPilotRig = true;
    FSSHeroDefinition Hero = FSSHeroDefinition::Fallback();
    UPROPERTY()
    TObjectPtr<UAnimSequence> WalkAnimation;
    double MeshLift(double ScaledSoleOffset) const;
    void SampleExitPose(float Seconds);
    void StartWalkingAnimation();
};
