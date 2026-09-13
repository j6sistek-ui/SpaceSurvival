#pragma once
#include "CoreMinimal.h"
#include "Async/Future.h"
#include "GameFramework/Actor.h"
#include "SSWave10Soak.generated.h"
class ASSGameMode;

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
    bool Started = false, Stopping = false, SawWave9 = false, SawBreathing = false;
    bool CaptureRequested = false, AllFramesForeground = true;
    double FocusSince = 0;
    bool SawClimax = false, SawApproach = false;
    void Stop(const FString &Error);
    void WriteResultAndExit();
};
