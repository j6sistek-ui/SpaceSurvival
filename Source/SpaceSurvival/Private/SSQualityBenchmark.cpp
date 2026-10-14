#include "SSWave10Soak.h"
#include "SSGameMode.h"
#include "SSGameInstance.h"
#include "SSShip.h"
#include "SSDistantAsteroids.h"
#include "SSSpaceScenery.h"
#include "SSWorldActors.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SphereComponent.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "Serialization/JsonSerializer.h"
#include "UnrealClient.h"
#if WITH_EDITOR
#include "AssetCompilingManager.h"
#include "ShaderCompiler.h"
#endif

CSV_DEFINE_CATEGORY(SpaceSurvivalBenchmark, true);

namespace
{
constexpr const char *BenchmarkId = "5eade000000000000000000000000010";
FVector LaneAt(double X, double TurnOffset = 0.)
{
    return FVector(X, 7000. * FMath::Sin(X / 100000.) + TurnOffset, 4500. * FMath::Sin(X / 150000.));
}
int32 CVarInt(const TCHAR *Name)
{
    const auto *Value = IConsoleManager::Get().FindConsoleVariable(Name);
    return Value ? Value->GetInt() : MIN_int32;
}
} // namespace

void ASSWave10Soak::BenchmarkContact(UPrimitiveComponent *HitComponent, AActor *OtherActor,
                                     UPrimitiveComponent *OtherComponent, FVector NormalImpulse, const FHitResult &Hit)
{
    if (QualityBenchmark && Started && !Stopping && OtherActor && Mode.IsValid() && OtherActor != Mode->Ship)
        ++BenchmarkContactCount;
}

void ASSWave10Soak::TickQualityBenchmark(float Dt)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    auto *GM = Mode.Get();
    auto *GI = GM ? GM->GetGameInstance<USSGameInstance>() : nullptr;
    auto *PC = UGameplayStatics::GetPlayerController(this, 0);
    if (!GI || !PC || !GM->Director || CaptureVisuals || FScreenshotRequest::IsScreenshotRequested())
    {
        Stop(TEXT("Benchmark lost its controller/director or attempted a screenshot."));
        return;
    }
    auto &S = GI->Session;
    if (!Started)
    {
        int32 Width = 0, Height = 0;
        PC->GetViewportSize(Width, Height);
        BenchmarkRequestedCount = CVarInt(TEXT("ss.DistantAsteroidCount"));
        if (Width != 1920 || Height != 1080 || (BenchmarkRequestedCount != 2048 && BenchmarkRequestedCount != 6144) ||
            CVarInt(TEXT("t.IdleWhenNotForeground")) != 0 || CVarInt(TEXT("r.VSync")) != 0 ||
            CVarInt(TEXT("t.MaxFPS")) != 0 || CVarInt(TEXT("r.ScreenPercentage")) != 100)
        {
            Stop(TEXT("Benchmark requires 1920x1080, 2048/6144 instances, 100% screen percentage and uncapped "
                      "offscreen rendering."));
            return;
        }
        // Apply only in this fresh, isolated process. ApplySettings does not persist a save slot.
        S.settings.quality = 2; // Unreal High.
        S.settings.frameLimit = 0;
        GI->ApplySettings();
        for (const TCHAR *Name :
             {TEXT("sg.ViewDistanceQuality"), TEXT("sg.AntiAliasingQuality"), TEXT("sg.ShadowQuality"),
              TEXT("sg.GlobalIlluminationQuality"), TEXT("sg.ReflectionQuality"), TEXT("sg.PostProcessQuality"),
              TEXT("sg.TextureQuality"), TEXT("sg.EffectsQuality"), TEXT("sg.FoliageQuality"),
              TEXT("sg.ShadingQuality")})
            if (CVarInt(Name) != 2)
            {
                Stop(FString(TEXT("Benchmark High scalability did not apply: ")) + Name);
                return;
            }
        if (!S.StartRun(BenchmarkId))
        {
            Stop(TEXT("Benchmark normal starter run could not start."));
            return;
        }
        BenchmarkRunSeed = GetTypeHash(FString(UTF8_TO_TCHAR(BenchmarkId)));
        BenchmarkInitialHull = S.run.hull;
        BenchmarkInitialShield = S.run.shield;
        GM->PreviousPhase = GM->PreviousWave = -1;
        GM->Director->ResetEncounter();
        GM->Director->SetComponentTickEnabled(false);
        // The actual field was first anchored by the hangar's parked ship. Its lane
        // is not centred on world Z=7000. Start this explicit comparison on that
        // stable lane, 500m along it and clear of the hangar, without relocating in flight.
        if (!GM->DistantField)
        {
            Stop(TEXT("Benchmark requires the actual hangar-anchored field before choosing its checked start."));
            return;
        }
        const FTransform FieldTransform = GM->DistantField->GetActorTransform();
        BenchmarkFieldOrigin = FieldTransform.GetLocation();
        BenchmarkStartWorld = FieldTransform.TransformPosition(LaneAt(50000.));
        const FVector InitialTarget = FieldTransform.TransformPosition(LaneAt(70000.));
        const FRotator InitialHeading = (InitialTarget - BenchmarkStartWorld).Rotation();
        GM->SpawnFlight(BenchmarkStartWorld, InitialHeading);
        GM->Director->SetActive(false);
        if (!GM->Ship || !GM->DistantField || !GM->SpaceScenery)
        {
            Stop(TEXT("Benchmark did not spawn its real ship and environment."));
            return;
        }
        FHitResult InitialHit;
        FCollisionQueryParams InitialQuery(SCENE_QUERY_STAT(SSBenchmarkStartClearance), false, GM->Ship);
        ++BenchmarkClearanceProbes;
        if (GM->Ship->SweepFlightHull(InitialHit, BenchmarkStartWorld, InitialTarget, InitialHeading.Quaternion(),
                                      InitialQuery))
        {
            Stop(FString::Printf(TEXT("Benchmark starting hull route is blocked by %s; no collision bypass."),
                                 *GetNameSafe(InitialHit.GetActor())));
            return;
        }
        TArray<UPrimitiveComponent *> Components;
        GM->Ship->GetComponents(Components);
        for (UPrimitiveComponent *Part : Components)
            Part->OnComponentHit.AddDynamic(this, &ASSWave10Soak::BenchmarkContact);
        BenchmarkLastRotation = GM->Ship->GetActorRotation();
        Started = true;
        return;
    }
    auto *Ship = GM->Ship.Get();
    if (!IsValid(Ship) || !GM->DistantField || !GM->SpaceScenery || !S.run.active || !S.IsFlying() ||
        GI->IsFreeFlight() || PC->GetPawn() != Ship || PC->GetViewTarget() != Ship || GM->IsMenuOpen() ||
        BenchmarkContactCount != 0 || S.run.hull < BenchmarkInitialHull - .001 ||
        S.run.shield < BenchmarkInitialShield - .001 || S.run.damageFeedback > 0. ||
        CVarInt(TEXT("ss.DistantAsteroidCount")) != BenchmarkRequestedCount)
    {
        Stop(TEXT("Benchmark lost its ordinary flight context or encountered contact/damage; comparison is invalid."));
        return;
    }
    // The environment-only scenario holds wave progression, not physics time, health or resources.
    S.run.phaseSeconds = 0;
    GM->Director->SetActive(false);
    ++CapturedFrames;
    AllFramesForeground &= FApp::HasFocus();
    FlightSeconds += Dt;
    int32 Pending = 0;
#if WITH_EDITOR
    Pending = FAssetCompilingManager::Get().GetNumRemainingAssets() +
              (GShaderCompilingManager ? GShaderCompilingManager->GetNumRemainingJobs() : 0);
#endif
    const bool Measured = BenchmarkWarmupSeconds >= 15.;
    if (!Measured)
    {
        BenchmarkQuietSeconds = Pending == 0 ? BenchmarkQuietSeconds + Dt : 0.;
        if (BenchmarkQuietSeconds >= 15.)
            BenchmarkWarmupSeconds = FlightSeconds;
    }
    else
        BenchmarkMeasuredSeconds += Dt;
    const int32 Stage = !Measured ? 0 : BenchmarkMeasuredSeconds < 20. ? 1 : BenchmarkMeasuredSeconds < 40. ? 2 : 3;
    const double TurnOffset = Stage == 2 ? 800. * FMath::Sin((BenchmarkMeasuredSeconds - 20.) * PI / 10.) : 0.;
    const FTransform FieldTransform = GM->DistantField->GetActorTransform();
    const FVector Local = FieldTransform.InverseTransformPosition(Ship->GetActorLocation());
    const FVector Target = FieldTransform.TransformPosition(LaneAt(Local.X + 20000., TurnOffset));
    const double LaneError = (Local - LaneAt(Local.X)).Size();
    if (LaneError > 4500.)
    {
        Stop(TEXT("Benchmark steering left the checked field lane; comparison is invalid."));
        return;
    }
    if (FlightSeconds >= BenchmarkNextProbeAt)
    {
        CSV_SCOPED_TIMING_STAT(SpaceSurvivalBenchmark, ClearanceProbe);
        BenchmarkNextProbeAt = FlightSeconds + 1.;
        ++BenchmarkClearanceProbes;
        FHitResult Hit;
        FCollisionQueryParams Query(SCENE_QUERY_STAT(SSBenchmarkLaneClearance), false, Ship);
        if (Ship->SweepFlightHull(Hit, Ship->GetActorLocation(), Target,
                                  (Target - Ship->GetActorLocation()).ToOrientationQuat(), Query))
        {
            Stop(
                FString::Printf(TEXT("Benchmark real swept hull found blocked upcoming lane: %s; no collision bypass."),
                                *GetNameSafe(Hit.GetActor())));
            return;
        }
    }
    const FRotator Current = Ship->GetActorRotation();
    const FRotator Desired = (Target - Ship->GetActorLocation()).Rotation();
    const float Step = FMath::Max(Dt, 1.f / 240.f);
    const float YawRate = FMath::FindDeltaAngleDegrees(BenchmarkLastRotation.Yaw, Current.Yaw) / Step;
    const float PitchRate = FMath::FindDeltaAngleDegrees(BenchmarkLastRotation.Pitch, Current.Pitch) / Step;
    BenchmarkLastRotation = Current;
    const FVector2D Steering(
        FMath::Clamp(FMath::FindDeltaAngleDegrees(Current.Yaw, Desired.Yaw) / 40.f - YawRate * .015f, -.4f, .4f),
        FMath::Clamp(FMath::FindDeltaAngleDegrees(Current.Pitch, Desired.Pitch) / 40.f - PitchRate * .015f, -.4f, .4f));
    Ship->SetFlightInput(Steering, FVector2D::ZeroVector, Measured ? 1.f : 0.f, Stage == 3,
                         !Measured && Ship->GetVelocity().Size() > 25.f);
    const FIntVector Cell = GM->DistantField->GetResidentCenter();
#define BENCHMARK_STAT(Name, Value) CSV_CUSTOM_STAT(SpaceSurvivalBenchmark, Name, Value, ECsvCustomStatOp::Set)
    BENCHMARK_STAT(Measured, Measured ? 1 : 0);
    BENCHMARK_STAT(Stage, Stage);
    BENCHMARK_STAT(ElapsedSeconds, FlightSeconds);
    BENCHMARK_STAT(SimulationDeltaMs, Dt * 1000.f);
    BENCHMARK_STAT(SpeedCmPerSecond, Ship->GetVelocity().Size());
    BENCHMARK_STAT(DistantInstances, GM->DistantField->GetRockCount());
    BENCHMARK_STAT(DistantCells, GM->DistantField->GetResidentCellCount());
    BENCHMARK_STAT(DistantCellX, Cell.X);
    BENCHMARK_STAT(DistantCellY, Cell.Y);
    BENCHMARK_STAT(DistantCellZ, Cell.Z);
    BENCHMARK_STAT(RegionCells, GM->SpaceScenery->GetResidentCellCount());
    BENCHMARK_STAT(RegionClutter, GM->SpaceScenery->GetResidentClutterCount());
    BENCHMARK_STAT(RegionLandmarks, GM->SpaceScenery->GetResidentLandmarkCount());
    BENCHMARK_STAT(RegionArea, GM->SpaceScenery->GetCurrentAreaIndex());
    BENCHMARK_STAT(Hull, S.run.hull);
    BENCHMARK_STAT(Shield, S.run.shield);
    BENCHMARK_STAT(Boost, S.run.boost);
    BENCHMARK_STAT(Boosting, S.run.boosting ? 1 : 0);
    BENCHMARK_STAT(LaneErrorCm, LaneError);
    BENCHMARK_STAT(PositionX, Ship->GetActorLocation().X);
    BENCHMARK_STAT(PositionY, Ship->GetActorLocation().Y);
    BENCHMARK_STAT(PositionZ, Ship->GetActorLocation().Z);
    BENCHMARK_STAT(OriginX, GetWorld()->OriginLocation.X);
    BENCHMARK_STAT(OriginY, GetWorld()->OriginLocation.Y);
    BENCHMARK_STAT(OriginZ, GetWorld()->OriginLocation.Z);
#undef BENCHMARK_STAT
    if (BenchmarkMeasuredSeconds >= 60.)
        Stop(TEXT(""));
#endif
}

void ASSWave10Soak::AddQualityBenchmarkResult(const TSharedRef<FJsonObject> &Result) const
{
    Result->SetBoolField(TEXT("qualityBenchmark"), true);
    Result->SetNumberField(TEXT("benchmarkWarmupSeconds"), BenchmarkWarmupSeconds);
    Result->SetNumberField(TEXT("benchmarkMeasuredSeconds"), BenchmarkMeasuredSeconds);
    Result->SetNumberField(TEXT("benchmarkContactCount"), BenchmarkContactCount);
    Result->SetNumberField(TEXT("benchmarkClearanceProbes"), BenchmarkClearanceProbes);
    Result->SetNumberField(TEXT("benchmarkRunSeed"), BenchmarkRunSeed);
    Result->SetNumberField(TEXT("benchmarkDistantAsteroidCount"), BenchmarkRequestedCount);
    Result->SetNumberField(TEXT("benchmarkInitialHull"), BenchmarkInitialHull);
    Result->SetNumberField(TEXT("benchmarkInitialShield"), BenchmarkInitialShield);
    Result->SetStringField(TEXT("benchmarkStartWorldCm"), BenchmarkStartWorld.ToString());
    Result->SetStringField(TEXT("benchmarkInitialFieldOriginCm"), BenchmarkFieldOrigin.ToString());
    Result->SetNumberField(TEXT("benchmarkStartFieldLocalXcm"), 50000.);
    Result->SetBoolField(TEXT("benchmarkDirectorDisabled"), true);
    Result->SetBoolField(TEXT("benchmarkNormalStats"), true);
    Result->SetBoolField(TEXT("benchmarkScriptedPhysicsInput"), true);
    Result->SetBoolField(TEXT("benchmarkPhaseAgeHeld"), true);
    Result->SetBoolField(TEXT("benchmarkHealthAssistance"), false);
    Result->SetStringField(TEXT("benchmarkResolutionQuality"), TEXT("1920x1080 High, 100% screen percentage"));
    Result->SetStringField(
        TEXT("benchmarkRoute"),
        TEXT("Initial spawn on the actual field-local curve at X=500m, real swept hull checked before timing; "
             "200m lookahead, +/-8m smooth turn during seconds20-40; "
             "boost held seconds40-60 without refills."));
}
