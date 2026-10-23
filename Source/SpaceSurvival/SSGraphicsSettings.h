#pragma once
#include "CoreMinimal.h"
#include "Domain/SurvivalCore.h"

namespace SSGraphics
{
struct FCapabilities
{
    bool DLSS = false, DLAA = false, FrameGeneration = false, Reflex = false;
    bool RayReconstruction = false, NIS = false, Vibrance = false, FrameGenerationVSync = false;
    TArray<int32> QualityModes, FrameModes;
    FString DLSSReason, FrameReason, ReflexReason, RayReason, NISReason, VibranceReason;
};
struct FTelemetry
{
    float DisplayedFPS = 0, LatencyMs = 0;
    int32 PresentedFrames = 0;
    bool FrameGenerationActive = false;
};
FCapabilities Query();
SS::Settings Resolve(const SS::Settings &Requested, const FCapabilities &Capabilities);
void Apply(const SS::Settings &Requested);
FTelemetry Telemetry();
FString ReconstructionName(int32 Mode);
FString QualityName(int32 Mode);
FString FrameModeName(int32 Mode);
void CopyPreferences(const SS::Settings &From, SS::Settings &To);
} // namespace SSGraphics
