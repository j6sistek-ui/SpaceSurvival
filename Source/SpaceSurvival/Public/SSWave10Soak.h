#pragma once
#include "CoreMinimal.h"
#include "Async/Future.h"
#include "GameFramework/Actor.h"
#include "SSWave10Soak.generated.h"
class ASSGameMode;
class ACameraActor;
class ASSEnemy;
class UNiagaraComponent;
class FJsonValue;

/** Explicit isolated Development capture. Never used by ordinary gameplay. */
UCLASS(NotBlueprintable, Transient)
class SPACESURVIVAL_API ASSWave10Soak : public AActor
{
    GENERATED_BODY()
public:
    ASSWave10Soak();
    static void TryStart(ASSGameMode *Mode);
    static void NotifyEnemyDefeated(ASSEnemy *Enemy);
    virtual void Tick(float DeltaSeconds) override;

private:
    TWeakObjectPtr<ASSGameMode> Mode;
    FString Root, Token, Failure;
    TSharedFuture<FString> CaptureResult;
    double StartedAt = 0, FlightSeconds = 0, ClimaxSeconds = 0, CompoundSeconds = 0, ApproachSeconds = 0;
    double NextDodge = 8;
    int32 PeakThreats = 0, CapturedFrames = 0;
    bool Started = false, Stopping = false, SawFlightWave = false, SawBreathing = false;
    bool CaptureRequested = false, AllFramesForeground = true;
    bool CaptureVisuals = false;
    bool CaptureSequence = false;
    double NextSequenceSeconds = 6; // Let normal rendering/texture streaming settle before repeated readbacks.
    int32 SequenceIndex = 0;
    bool OffscreenVisuals = false;
    TArray<TSharedPtr<FJsonValue>> VisualRecords;
    TSet<FString> VisualNames;
    void CaptureVisual(const TCHAR *Name, float StageSeconds);
    void CaptureStationReview(const TCHAR *Name, FVector LocalCamera, FVector LocalTarget);
    void CaptureCombatAfterKill();
    TWeakObjectPtr<UNiagaraComponent> CombatExplosion;
    FString CombatEnemy;
    double CombatKilledAt = 0;
    UPROPERTY(Transient)
    TObjectPtr<ACameraActor> StationReviewCamera;
    TWeakObjectPtr<AActor> PreviousReviewViewTarget;
    FName StationReviewShot;
    double ReviewCameraReadyAt = 0;
    double FocusSince = 0;
    bool SawClimax = false, SawApproach = false;
    bool Wave1 = false;
    bool Gallery = false, GalleryRunPreserved = false, GalleryReturned = false;
    int32 GalleryStage = 0;
    double GalleryStageAt = 0, GalleryReadyAt = 0;
    FString GalleryRunBefore, GalleryAccountBefore;
    FTransform GalleryReturnTransform;
    void TickGallery(float DeltaSeconds);
    bool Station5 = false, SawWormhole = false, SawDocking = false, SawExit = false;
    double WormholeSeconds = 0, DockingSeconds = 0, ExitSeconds = 0, StationIdleSeconds = 0;
    /** Last frame's ship rotation during Approach, for rate-damped steering. See Tick. */
    FRotator ApproachLastRotation = FRotator::ZeroRotator;
    bool ApproachHasLastRotation = false;
    /** Next ApproachSeconds at which the approach diagnostic line is written. */
    double NextApproachLog = 0;
    /** Which arrival this run is supposed to show, read off the hero the station actually possessed
     *  rather than assumed. A hero with an exit clip climbs out of the ship; a hero without one is
     *  standing outside it when the docking motion finishes (RPT-20260917-01), and the evidence that
     *  the transition worked is then the pawn itself: on the station's floor, clear of the hull,
     *  collision and walking restored. Both are certifiable; neither certifies the other. */
    bool HeroKnown = false, HeroClimbsOut = false, SawStandingExit = false;
    double DeckSeconds = 0;
    /** How many times the walker's own Tick had to haul the pawn back onto the deck during the station
     *  phase. It should be nought: this fixture never drives the walker, so nothing can walk it off.
     *  Anything above that is an arrival that put the player somewhere it should not have, healed by a
     *  clamp that restores the very state the evidence below is made of - so it is read, and refused,
     *  rather than being allowed to supply the proof. */
    int32 DeckRescues = 0;
    /** Of the deck seconds above, how many the player was also looking through the hero's own camera
     *  for. Counted only outside the possession blend and outside the fixture's own review shots, which
     *  take the view at seven seconds and keep it. */
    double PlayerViewSeconds = 0;
    FString StationHeroId;
    void Stop(const FString &Error);
    void WriteResultAndExit();
};
