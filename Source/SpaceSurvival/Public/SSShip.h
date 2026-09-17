#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "Domain/SurvivalCore.h"
#include "SSShip.generated.h"
class USphereComponent;
class UStaticMeshComponent;
class USkeletalMeshComponent;
class USpringArmComponent;
class UCameraComponent;
class UAudioComponent;
class USSPhase1Data;
class USSShipPresentation;

UCLASS()
class SPACESURVIVAL_API ASSShip : public APawn
{
    GENERATED_BODY()
public:
    ASSShip();
    // Flight and every station bay share the same reviewed hull selection.
    static const TCHAR *HullAssetPath(SS::Ship Kind);
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void ApplyWorldOffset(const FVector &InOffset, bool bWorldShift) override;
    virtual FVector GetVelocity() const override
    {
        return Velocity;
    }
    void SetFlightInput(FVector2D Steering, FVector2D Strafe, float Throttle, bool Boost, bool Brake);
    void RequestDodge();
    void Fire();
    void ReceiveDamage(float Amount, SS::DamageType Type = SS::DamageType::Kinetic);
    void ReceiveImpact(float Amount, FVector AwayFromContact);
    void AddExternalForce(FVector Force);
    void SetDockingTarget(FVector Target, FRotator Rotation);
    void FinishDocking();
    bool BeginMooring();
    void EndMooring();
    bool IsMoored() const
    {
        return Moored;
    }
    /** Brief window after each shot. The HUD reticle needs one firing state that reads the same on
     *  both weapons, and the cannon's own cooldown is far too long to stand in for that. */
    bool IsFiring() const
    {
        return FireVisualSeconds > 0.f;
    }
    /** Read-only presentation state. Gameplay remains owned by the domain session. */
    void GetDrivePresentation(float &OutPower, bool &OutBoosting, bool &OutBraking, float &OutDamage) const
    {
        OutPower = DrivePresentationPower;
        OutBoosting = DrivePresentationBoosting;
        OutBraking = DrivePresentationBraking;
        OutDamage = DrivePresentationDamage;
    }
    static float SoftAssistWeight(float Alignment, float ConeDegrees, float MaximumStrength);
    FVector AimDirection() const;
    AActor *SoftTarget = nullptr;
    UPROPERTY(EditAnywhere, Category = "Flight|Aim", meta = (ClampMin = "0.0", ClampMax = "0.4"))
    float MaximumSoftAssist = .20f;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USphereComponent> Collision;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> HullMesh;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USkeletalMeshComponent> Pilot;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USpringArmComponent> CameraBoom;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UCameraComponent> Camera;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UAudioComponent> EngineAudio;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USSShipPresentation> Presentation;
    UPROPERTY(EditAnywhere)
    TObjectPtr<USSPhase1Data> Tuning;

private:
    void UpdateEngineMix();
    FVector Velocity = FVector::ZeroVector, Forces = FVector::ZeroVector;
    FVector2D Steer = FVector2D::ZeroVector, StrafeInput = FVector2D::ZeroVector;
    float ThrottleInput = 0.f, FireCooldown = 0.f, ImpactCooldown = 0.f, FireVisualSeconds = 0.f;
    /** Impact shake phase and severity. Presentation only; neither reaches thrust or shot origin. */
    float ShakeSeconds = 0.f, ShakeSeverity = 0.f;
    /** Decays from one when boost engages, so acceleration has a transient the sustained levels do not give it. */
    float BoostPunch = 0.f;
    bool WasBoosting = false;
    float DrivePresentationPower = .45f, DrivePresentationDamage = 0.f;
    bool DrivePresentationBoosting = false, DrivePresentationBraking = false;
    bool BoostInput = false, BrakeInput = false, Docking = false, Moored = false;
    FVector DockTarget = FVector::ZeroVector;
    FRotator DockRotation = FRotator::ZeroRotator;
};
