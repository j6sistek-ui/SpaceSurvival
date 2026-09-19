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
class UPointLightComponent;
class UAudioComponent;
class UAnimSequence;
class UTextRenderComponent;
class UMaterialInterface;
class ASSStationVisualLayout;
class ASSLandingPad;
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
    /** The landing marker on the pad. Lit while the pad is waiting for a ship, dark once one is sitting on
     *  it - an indicator that stays up after you have landed is just a decal. */
    void ShowPadIndicator(bool Visible);
    /** The pad this station owns. A real, separately placeable ASSLandingPad, attached to the station so it
     *  moves with it; the station is one client of a pad, not the definition of one. */
    ASSLandingPad *GetLandingPad() const
    {
        return LandingPad;
    }
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
    /** Where THIS station places ITS pad, in station-local centimetres. These are measured, not chosen. The
     *  deck is at Z -10 because that is already the top of everything the hero walks on: DeckCollision spans
     *  Z -110..-10 and Bow_Sill's top face is -10 too. One plane end to end means walking in from the pad
     *  needs no step, which matters because ASSWalker has two movement inputs and no jump. The pad itself -
     *  its deck, kerbs, indicator, and every question about parking or standing on it - is ASSLandingPad,
     *  which knows nothing about stations; these numbers are only this station's placement of one. */
    static constexpr float PadDeckTop = -10.f;
    static constexpr float PadCenterX = -4500.f;
    static constexpr float PadHalfExtent = 1600.f;
    /** Where the walkway meets the hangar mouth. The mouth itself spans X -1900..-1700. */
    static constexpr float PadWalkwayInnerX = -1900.f;
    /** Where the ship parks, the hero appears, and a disembark ends - all answered by the pad. The station
     *  keeps these names so that every caller written against "the station's pad" keeps working, but the
     *  numbers now live on the one place they mean anything. */
    FVector PadDockPosition() const;
    FVector PadWalkSpawn() const;
    FVector PadExit() const;
    /** Whether a world position is somewhere the hero is allowed to be: the interior deck, the walkway out
     *  to the pad, or the pad itself. The three overlap across each threshold on purpose - a gap between
     *  any two would be a spot where crossing it teleports the hero home. Not static any more, because the
     *  pad is an actor with its own transform and the only honest answer comes from asking it. */
    bool Walkable(const FVector &World) const;
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
    TObjectPtr<ASSLandingPad> LandingPad;
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
    /** Spawns this station's pad and builds the walkway that joins it to the hangar mouth. */
    void BuildLandingPad(bool bHome, const TCHAR *Cube, const TCHAR *Hull);
    void DestroyLandingPad();
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
    /** Put a hero on this pawn: mesh, lift, yaw, scale, the gait ladder, the readability rig and the
     *  foot rest height. Called once from BeginPlay, and again whenever the station wardrobe changes
     *  the choice. An empty preference is exactly the old behaviour - the first installed hero in
     *  roster order - so a pawn that is never asked for anything wears what it always wore. */
    void ApplyHero(FName PreferredId = NAME_None);
    /** Whichever hero this build installed. Telemetry and tests ask it for the names and numbers
     *  they used to spell out, so they follow the hero the player is actually wearing. */
    const FSSHeroDefinition &GetHero() const
    {
        return Hero;
    }
    /** Deck plates sit this far above the collision floor; the sole is fitted to them, not to it. */
    static constexpr float DeckClearance = 2.75f;
    /** The two speeds the idle/locomotion switch turns on, as fractions of this hero's own authored
     *  walk speed so they mean the same thing for a hero whose stride is not 180 cm/s. Standing
     *  becomes moving above the first; moving becomes standing below the second. They are different
     *  numbers on purpose: one threshold would let a pawn creeping across it - a nudged stick, the
     *  last centimetres of braking, a shove from geometry - flip clip every frame, and each flip is a
     *  hard cut on a single-node pawn, so the flicker would be the loudest thing on screen. At the
     *  squirrel's 180 these are 18 and 7.2 cm/s: 18 is reached within a frame of real input and is
     *  slow enough that the step it starts is a step, and below 7.2 the hero covers less ground in a
     *  second than its own planted foot wanders inside the idle, so a planted idle foot there cannot
     *  be seen to slide. */
    static constexpr float MoveEnterFraction = .10f;
    static constexpr float MoveExitFraction = .04f;
    /** How far past a gait boundary the pawn has to get before the clip changes, as a fraction of
     *  that boundary. The boundaries themselves are the geometric means of the neighbouring clips'
     *  authored speeds, so this band is symmetric in the thing that actually matters - the ratio the
     *  rate ends up at. Without it a pawn cruising on a boundary changes clip every frame. */
    static constexpr float GaitHysteresis = .08f;
    /** How many times Tick has had to haul this pawn back onto the deck. In play that is a mercy: a
     *  walker who wanders off the finite deck is returned to its spawn rather than losing the run. To
     *  anything checking an arrival it is the opposite - the clamp restores exactly the state an
     *  arrival is asked to prove (walking, on the deck, at WalkSpawn), so a fixture that only looks
     *  at the pawn cannot tell a good arrival from a bad one the clamp healed. Counting the rescues
     *  is what tells them apart, so a rescue during arrival can be refused rather than certified. */
    int32 OffDeckRecoveries() const
    {
        return OffDeckRescues;
    }
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USpringArmComponent> Boom;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UCameraComponent> Camera;
    /** The readability rig: a yaw-only frame that holds the two lights aimed relative to the view. */
    UPROPERTY(VisibleAnywhere, Category = "Readability")
    TObjectPtr<USceneComponent> LightRig;
    /** Camera-side key. Models the body and gives the suit a specular the camera can see. */
    UPROPERTY(VisibleAnywhere, Category = "Readability")
    TObjectPtr<UPointLightComponent> KeyLight;
    /** Far-side rim. Draws the outline against a deck that is brighter than any hero suit. */
    UPROPERTY(VisibleAnywhere, Category = "Readability")
    TObjectPtr<UPointLightComponent> RimLight;
    UPROPERTY(EditAnywhere)
    TObjectPtr<USSPhase1Data> Tuning;

private:
    TWeakObjectPtr<ASSStation> RecoveryHub;
    int32 OffDeckRescues = 0;
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
    /** Null for a hero that declares no idle, and null for one whose idle failed to load or belongs
     *  to another skeleton. Every branch that reads it treats null as "this hero stands the way the
     *  game has always stood a hero", so a missing file degrades rather than breaks. */
    UPROPERTY()
    TObjectPtr<UAnimSequence> IdleAnimation;
    UPROPERTY()
    TArray<TObjectPtr<UAnimSequence>> FidgetAnimations;
    /** The gaits this hero owns, ascending by the speed each was authored to travel at. Element 0 is
     *  always the walk, so this is never empty and a hero with no fast clips has exactly one entry -
     *  which is the whole of the old behaviour, reached without a branch. */
    UPROPERTY()
    TArray<TObjectPtr<UAnimSequence>> GaitAnimations;
    TArray<float> GaitSpeeds;
    /** Which side of the hysteresis band the pawn is currently on, not what its velocity is. */
    bool Moving = false;
    /** Which entry of GaitAnimations is playing; kept across frames because the band it was chosen
     *  in is wider than the band it would be re-chosen in. */
    int32 Gait = 0;
    float StandingSeconds = 0.f;
    float FidgetSecondsLeft = 0.f;
    int32 NextFidget = 0;
    /** Seconds into a cross-blend out of the pose the previous clip was holding, or negative when no
     *  blend is running. Only a hero with an idle ever sets it: see PlayClip. */
    float CutSeconds = -1.f;
    double MeshLift(double ScaledSoleOffset) const;
    void SampleExitPose(float Seconds);
    void PlayClip(UAnimSequence *Clip, float Seconds, bool Loop, float RateScale, bool CarryPose);
    int32 ChooseGait(float Speed) const;
    /** CarryPose false is the spawn case: there is no outgoing animation to blend off, only the
     *  reference pose the component happens to be holding, and blending off that would make the
     *  hero's first tenth of a second a fade out of a T-pose. */
    void StartStandingAnimation(bool CarryPose = true);
    void UpdateHeroAnimation(float DeltaSeconds);
    void UpdateFootsteps(float DeltaSeconds);
    void UpdateReadabilityLighting();
    /** Whether each boot was down last frame, so a step sounds on the way down and not every frame
     *  it stays there, and a short bar on how soon the next one may sound. */
    bool FootPlanted[2] = {false, false};
    float StepCooldown = 0.f;
    /** How high this hero's ankle sits above the deck when it simply stands, measured once from the
     *  mesh it is wearing. A boot is planted when it comes back near that, which is a number every
     *  hero answers for itself rather than one tuned to the squirrel's short legs. */
    float FootRestHeight = 0.f;
};
