#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Character.h"
#include "SSGameMode.h"
#include "SSStation.generated.h"
class UStaticMeshComponent;
class UCameraComponent;
class USpringArmComponent;
class UAudioComponent;
class UAnimSequence;
struct FPoseSnapshot;

UCLASS()
class SPACESURVIVAL_API ASSStation : public AActor
{
    GENERATED_BODY()
public:
    ASSStation();
    void BuildHub(bool bHome);
    void SetBayShip(int32 ShipKind);
    void ShowBayShip(bool Visible);
    virtual void Tick(float DeltaSeconds) override;
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
    struct FService
    {
        FVector Location;
        FString Label;
        ESSPanel Panel;
    };
    TArray<FService> Services;
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
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USpringArmComponent> Boom;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UCameraComponent> Camera;

private:
    TWeakObjectPtr<ASSStation> RecoveryHub;
    FVector ExitStart = FVector::ZeroVector, ExitEnd = FVector::ZeroVector;
    FQuat ExitStartRotation = FQuat::Identity, ExitEndRotation = FQuat::Identity;
    double ExitElapsed = 0.0;
    bool Disembarking = false;
    UPROPERTY()
    TObjectPtr<UAnimSequence> WalkAnimation;
    void SampleExitPose(float Seconds);
    void StartWalkingAnimation();
};
