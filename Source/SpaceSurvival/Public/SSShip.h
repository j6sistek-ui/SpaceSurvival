#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "Domain/SurvivalCore.h"
#include "SSContentTypes.h"
#include "SSShip.generated.h"
class USphereComponent;
class UPrimitiveComponent;
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
    /** The radius of the body that actually has to fit through the station's corridor, read off the ship
     *  rather than repeated. It was repeated: five call sites carried a literal 105 while SSWorldActors
     *  carried 120, so hazard contact was already being judged against a ship 15 cm wider than the one
     *  the docking sweeps used. That is survivable at 105 and is not survivable at all once a hull of a
     *  different size is installed, which is why this exists now rather than after the fact. */
    /** Which hull this build flies. THE selection, in one place, because a test that re-derives it is a
     *  second copy of a rule - and this project has paid for a duplicated constant three times already. A
     *  fixture asking "whose tolerances apply" and BeginPlay asking "whose mesh do I load" must never be
     *  able to disagree. */
    static ESSHullIdentity SelectedHullIdentity();
    static float FlightCollisionRadius();
    /** The stick as ShipCore's gyro sees it: (yaw, pitch) stick to the plugin's (roll, pitch, yaw) body torque,
     *  axes and signs. Pure and static so the translation is pinned by a test that needs no physics world;
     *  the plugin's own convention is pinned separately by ShipCoreGyroAxes, and between them the whole chain
     *  from stick to rotator sign is measured rather than read. */
    static FVector GyroInputFor(FVector2D Steer, float Turn);
    /** How close this hull has to be to a dock point to be offered docking, in centimetres. */
    float DockApproachRadius() const;
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void ApplyWorldOffset(const FVector &InOffset, bool bWorldShift) override;
    virtual FVector GetVelocity() const override;
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
    /** Reapplies the account's paint bay choices to the hull: after the hull loads, and when paint changes. */
    void RefreshPaint();
    /** The hero in the seat. Not always the one walking the deck: a stand-in that has never been
     *  seated wins the walker slot without taking this one. */
    const FSSHeroDefinition &GetPilotHero() const
    {
        return PilotHero;
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
    /** The hull when it is a skeletal mesh. The three hulls the game has always flown are static meshes,
     *  and the Stellar Phoenix is not, so rather than converting HullMesh and changing what every existing
     *  hull does, the pawn carries both and shows one. Hidden and empty unless a skeletal hull is
     *  installed, which keeps the shipped ship exactly as it was. */
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USkeletalMeshComponent> SkeletalHull;
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
    FSSHeroDefinition PilotHero = FSSHeroDefinition::Fallback();
    /** How much further back the chase boom sits, because the hull is that many times longer than the one
     *  the 900 cm arm was framed for. One while the classic hull flies, which is every build today. */
    float HullChaseScale = 1.f;
    /** The hull's own engine exhausts, attached to its engine bones. Empty for a static hull, whose
     *  exhausts USSShipPresentation already fits to the mesh it knows. */
    UPROPERTY()
    TArray<TObjectPtr<class UNiagaraComponent>> HullExhausts;
    /** True once the root is simulating and ShipCore's components have accepted it. While false the hand
     *  written integrator below runs exactly as it always has, which is every build that does not pass
     *  -SSPhoenix. */
    bool ShipCoreDriven = false;
    UPROPERTY()
    TObjectPtr<class UThrusterManagerComp> Thrusters;
    UPROPERTY()
    TObjectPtr<class UGyroManagerComp> Gyros;
    /** Hands this frame's input and this run's upgraded stats to ShipCore, which then moves the body.
     *  Replaces the substepped integrator entirely while it is driving; the two never both run. */
    void DriveShipCore(float Dt, double Acceleration, double Maneuver, double Response, float Speed, float Authority,
                       float Interference);
    /** Stop or restart the physics body around a scripted move. Only does anything while ShipCore drives. */
    void HoldBody(bool Hold);
    /** Hull impact while ShipCore drives. The old integrator took its hits off the swept move's
     *  FHitResult, and a simulating body never runs that path - so without this, ramming an asteroid in
     *  the Phoenix is free. Physics handles the bounce; this only carries the damage across. */
    UFUNCTION()
    void OnHullImpact(UPrimitiveComponent *HitComp, AActor *OtherActor, UPrimitiveComponent *OtherComp,
                      FVector NormalImpulse, const FHitResult &Hit);
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
