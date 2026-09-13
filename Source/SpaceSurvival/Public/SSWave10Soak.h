#pragma once
#include "CoreMinimal.h"
#include "Async/Future.h"
#include "GameFramework/Actor.h"
#include "SSWave10Soak.generated.h"
class ASSGameMode;
class FJsonValue;

/** Explicit isolated Development capture. Never used by ordinary gameplay. */
UCLASS(NotBlueprintable, Transient)
class SPACESURVIVAL_API ASSWave10Soak : public AActor
{
    GENERATED_BODY()
public:
    ASSWave10Soak();
    static void TryStart(ASSGameMode *Mode);
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
    TArray<TSharedPtr<FJsonValue>> VisualRecords;
    TSet<FString> VisualNames;
    void CaptureVisual(const TCHAR *Name, float StageSeconds);
    double FocusSince = 0;
    bool SawClimax = false, SawApproach = false;
    bool Station5 = false, SawWormhole = false, SawDocking = false, SawExit = false;
    double WormholeSeconds = 0, DockingSeconds = 0, ExitSeconds = 0, StationIdleSeconds = 0;
    void Stop(const FString &Error);
    void WriteResultAndExit();
};
