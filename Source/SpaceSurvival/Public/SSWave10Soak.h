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
    bool Station5 = false, SawWormhole = false, SawDocking = false, SawExit = false;
    double WormholeSeconds = 0, DockingSeconds = 0, ExitSeconds = 0, StationIdleSeconds = 0;
    void Stop(const FString &Error);
    void WriteResultAndExit();
};
