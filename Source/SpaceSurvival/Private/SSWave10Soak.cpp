#include "SSWave10Soak.h"
#include "SSGameMode.h"
#include "SSGameInstance.h"
#include "SSShip.h"
#include "SSWorldActors.h"
#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/PlatformFileManager.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "HAL/PlatformMisc.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Guid.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "PlatformFeatures.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "Serialization/JsonSerializer.h"

CSV_DEFINE_CATEGORY(SpaceSurvivalSoak, true);

namespace
{
bool IsIsolatedSoak(FString &Root, FString &Token)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    auto Normalize = [](FString Path)
    {
        Path = FPaths::ConvertRelativePathToFull(Path);
        FPaths::NormalizeDirectoryName(Path);
        FPaths::CollapseRelativeDirectories(Path);
        return Path;
    };
    const FString User = Normalize(FPaths::ProjectUserDir());
    const FString Saved = Normalize(FPaths::ProjectSavedDir());
    Root = FPaths::GetPath(User);
    Token = FPaths::GetCleanFilename(Root);
    FGuid Guid;
    FString Argument, Marker, RootArgument;
    auto &Features = IPlatformFeaturesModule::Get();
    if (!PLATFORM_WINDOWS || !FParse::Param(FCommandLine::Get(), TEXT("SSWave10Soak")) ||
        FParse::Param(FCommandLine::Get(), TEXT("NullRHI")) || !FApp::CanEverRender() ||
        !FPaths::ShouldSaveToUserDir() || !FGuid::ParseExact(Token, EGuidFormats::Digits, Guid) ||
        !User.Equals(Root / TEXT("User"), ESearchCase::IgnoreCase) ||
        !Saved.Equals(User / TEXT("Saved"), ESearchCase::IgnoreCase) ||
        !FPaths::GetCleanFilename(FPaths::GetPath(Root)).Equals(TEXT("EndgameSoak"), ESearchCase::IgnoreCase) ||
        !FPaths::GetCleanFilename(FPaths::GetPath(FPaths::GetPath(Root)))
             .Equals(TEXT("Artifacts"), ESearchCase::IgnoreCase) ||
        !FParse::Value(FCommandLine::Get(), TEXT("UserDir="), Argument) ||
        !Normalize(Argument).Equals(User, ESearchCase::IgnoreCase) ||
        !FParse::Value(FCommandLine::Get(), TEXT("SSWave10SoakRoot="), RootArgument) ||
        !Normalize(RootArgument).Equals(Root, ESearchCase::IgnoreCase) ||
        Features.GetSaveGameSystem() != Features.IPlatformFeaturesModule::GetSaveGameSystem())
        return false;
    auto &Files = FPlatformFileManager::Get().GetPlatformFile();
    for (FString Path = Saved / TEXT("SaveGames"); !Path.IsEmpty();)
    {
        if (Files.IsSymlink(*Path) != ESymlinkResult::NonSymlink)
            return false;
        const FString Parent = FPaths::GetPath(Path);
        if (Parent == Path)
            break;
        Path = Parent;
    }
    const FString MarkerPath = Root / TEXT(".ss-endgame-soak");
    if (Files.IsSymlink(*MarkerPath) != ESymlinkResult::NonSymlink ||
        !FFileHelper::LoadFileToString(Marker, *MarkerPath) || Marker.TrimStartAndEnd() != Token)
        return false;
    for (const FString Leaf : {Root / TEXT("Endgame.csv"), Root / TEXT("fixture.json")})
        if (Files.IsSymlink(*Leaf) != ESymlinkResult::NonSymlink)
            return false;
    return true;
#else
    return false;
#endif
}
bool NoSaveSlots()
{
    TArray<FString> Files;
    IFileManager::Get().FindFiles(Files, *(FPaths::ProjectSavedDir() / TEXT("SaveGames/*")), true, false);
    return Files.IsEmpty();
}
} // namespace

ASSWave10Soak::ASSWave10Soak()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickGroup = TG_PostUpdateWork;
}
void ASSWave10Soak::TryStart(ASSGameMode *InMode)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    if (!FParse::Param(FCommandLine::Get(), TEXT("SSWave10Soak")))
        return;
    FString Root, Token;
    auto *GI = InMode ? InMode->GetGameInstance<USSGameInstance>() : nullptr;
    if (!GI || !IsIsolatedSoak(Root, Token) || GI->Session.run.active || !NoSaveSlots() ||
        FCsvProfiler::IsCapturing() || FCsvProfiler::Get()->IsWritingFile() ||
        IFileManager::Get().FileExists(*(Root / TEXT("Endgame.csv"))) ||
        IFileManager::Get().FileExists(*(Root / TEXT("fixture.json"))))
    {
        UE_LOG(LogTemp, Error,
               TEXT("SSWave10Soak refused: isolated fresh profile, renderer and idle CSV are required."));
        return;
    }
    auto *Soak = InMode->GetWorld()->SpawnActor<ASSWave10Soak>();
    if (!Soak)
        return;
    Soak->Mode = InMode;
    Soak->Root = Root;
    Soak->Token = Token;
    Soak->StartedAt = FPlatformTime::Seconds();
    InMode->bAutomatedSoakInput = true;
    // Prevent incidental account writes. No save APIs are called by the fixture.
    GI->AccountStorageBlocked = true;
    FCsvProfiler::Get()->EnableCategoryByString(TEXT("SpaceSurvival"));
    FCsvProfiler::Get()->EnableCategoryByString(TEXT("SpaceSurvivalSoak"));
    UE_LOG(LogTemp, Display,
           TEXT("ENDGAME_FIXTURE_WAITING_FOR_FOREGROUND: activate this owned game window; capture starts after two "
                "focused seconds."));
    UE_LOG(LogTemp, Display,
           TEXT("RENDERED_ENDGAME_FIXTURE_NOT_NATURAL_GAMEPLAY: token=%s process=%u; normal time; base durability "
                "50000; Tier V; scripted input."),
           *Token, FPlatformProcess::GetCurrentProcessId());
#endif
}
void ASSWave10Soak::Stop(const FString &Error)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    if (Stopping)
        return;
    Failure = Error;
    Stopping = true;
    CaptureResult = FCsvProfiler::Get()->EndCapture();
#endif
}
void ASSWave10Soak::Tick(float Dt)
{
    Super::Tick(Dt);
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    if (Stopping)
    {
        if (CaptureResult.IsValid() && CaptureResult.IsReady())
            WriteResultAndExit();
        return;
    }
    const double Now = FPlatformTime::Seconds();
    if (!CaptureRequested)
    {
        if (Now - StartedAt > 60)
        {
            UE_LOG(LogTemp, Error, TEXT("Endgame fixture did not obtain foreground focus within 60 seconds."));
            SetActorTickEnabled(false);
            FPlatformMisc::RequestExit(false);
            return;
        }
        if (!FApp::HasFocus())
        {
            FocusSince = 0;
            return;
        }
        if (FocusSince == 0)
            FocusSince = Now;
        if (Now - FocusSince < 2)
            return;
        CaptureRequested = true;
        StartedAt = Now;
        FCsvProfiler::Get()->BeginCapture(-1, Root, TEXT("Endgame.csv"));
    }
    auto *GM = Mode.Get();
    auto *GI = GM ? GM->GetGameInstance<USSGameInstance>() : nullptr;
    if (!GI || FPlatformTime::Seconds() - StartedAt > 180 ||
        !FMath::IsNearlyEqual(GetWorld()->GetWorldSettings()->GetEffectiveTimeDilation(), 1.f) ||
        FApp::UseFixedTimeStep() || (GEngine && GEngine->bUseFixedFrameRate))
    {
        Stop(TEXT("Missing world, timeout, fixed timestep or time dilation invalidates this rendered fixture."));
        return;
    }
    if (!FCsvProfiler::IsCapturing())
        return;
    auto &S = GI->Session;
    if (!Started)
    {
        // Seed only test memory; retain normal durations, caps, pressure, damage and spawn rules.
        S.tuning.baseHull = S.tuning.baseShield = 50000;
        if (!S.StartRun("5eade000000000000000000000000010"))
        {
            Stop(TEXT("Fixture run initialization failed."));
            return;
        }
        S.run.tiers = {{5, 5, 5, 5, 5}};
        S.run.utility = SS::Utility::OverdriveCooling;
        S.run.wave = 8;
        S.run.wavesCompleted = 7;
        S.run.depotSeen = S.run.salvageEventSeen = S.run.distressEventSeen = true;
        S.FinishWave(); // Real Wave 8 breathing enters normal Wave 9 through Session::Tick.
        S.run.hull = S.Stats().maxHull;
        S.run.shield = S.Stats().maxShield;
        GM->PreviousPhase = GM->PreviousWave = -1;
        GM->Director->ResetEncounter();
        GM->SpawnFlight(FVector(0, 0, 7000), FRotator::ZeroRotator);
        GM->Announce(TEXT("AUTOMATED ENDGAME CAPTURE / SEEDED BUILD / NOT NATURAL GAMEPLAY"));
        Started = true;
    }
    if (!S.run.active || !IsValid(GM->Ship) || S.run.wave > 10 || !FMath::IsNearlyEqual(S.tuning.climaxSeconds, 40.0))
    {
        Stop(TEXT("Fixture died, lost its ship or left the normal ten-wave/duration boundary."));
        return;
    }
    const bool Foreground = FApp::HasFocus();
    AllFramesForeground &= Foreground;
    ++CapturedFrames;
    FlightSeconds += Dt;
    int32 Kinds[12] = {};
    int32 Threats = 0;
    for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
        if (!It->IsActorBeingDestroyed())
        {
            const int32 Index = int32(It->GetKind());
            if (Index >= 0 && Index < 12)
                ++Kinds[Index];
            Threats += It->IsSolidHazard() || It->IsEnemy() || It->IsEnvironmentalField();
        }
    PeakThreats = FMath::Max(PeakThreats, Threats);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Fixture, 1, ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, ApplicationForeground, Foreground ? 1 : 0, ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, SimulationDeltaMs, Dt * 1000.f, ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Gravity, Kinds[5], ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Asteroids, Kinds[0] + Kinds[1] + Kinds[2], ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Wreckage, Kinds[3], ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Electrical, Kinds[4], ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Pursuers, Kinds[6], ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Flankers, Kinds[7], ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Projectiles, Kinds[8], ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Pickups, Kinds[9], ECsvCustomStatOp::Set);
    SawWave9 |= S.run.wave == 9 && S.run.phase == SS::Phase::Flight;
    SawBreathing |= S.run.wave == 9 && S.run.phase == SS::Phase::Breathing;
    if (S.run.wave == 10 && S.run.phase == SS::Phase::Climax)
    {
        SawClimax = true;
        ClimaxSeconds += Dt;
        if (Kinds[5] > 0 && Kinds[0] + Kinds[1] + Kinds[2] > 0 && Kinds[6] + Kinds[7] > 0)
            CompoundSeconds += Dt;
    }
    if (S.run.wave == 10 && S.run.phase == SS::Phase::Approach)
    {
        SawApproach = true;
        ApproachSeconds += Dt;
    }
    // Applied after normal world simulation for the next engine frame. No tick loops or time scaling.
    const double Cycle = FMath::Fmod(FlightSeconds, 12.0);
    GM->Ship->SetFlightInput(FVector2D::ZeroVector,
                             FVector2D(.12 * FMath::Sin(FlightSeconds * .35), .08 * FMath::Cos(FlightSeconds * .35)),
                             0.f, Cycle < 2.0, Cycle >= 6.0 && Cycle < 8.0);
    if (FlightSeconds >= NextDodge)
    {
        GM->Ship->RequestDodge();
        NextDodge += 8.0;
    }
    if (FMath::Fmod(FlightSeconds, 6.0) < 2.0)
        GM->Ship->Fire();
    if (Threats > GM->Director->MaximumActiveThreats)
        Stop(TEXT("Director active threat cap exceeded during rendered fixture."));
    else if (ApproachSeconds >= 5)
        Stop(SawWave9 && SawBreathing && SawClimax && ClimaxSeconds >= 39.5 && CompoundSeconds >= 3.5
                 ? FString()
                 : TEXT("Required complete endgame interval or concurrent compound coverage was not observed."));
#endif
}
void ASSWave10Soak::WriteResultAndExit()
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    FString CheckedRoot, CheckedToken;
    if (!IsIsolatedSoak(CheckedRoot, CheckedToken) || CheckedRoot != Root || CheckedToken != Token)
    {
        UE_LOG(LogTemp, Error, TEXT("Endgame fixture isolation no longer matches; result write refused."));
        FPlatformMisc::RequestExit(false);
        SetActorTickEnabled(false);
        return;
    }
    const bool SlotsUntouched = NoSaveSlots();
    const FString Csv = CaptureResult.Get();
    const bool Success = Failure.IsEmpty() && SlotsUntouched && !Csv.IsEmpty() && AllFramesForeground;
    auto Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("evidenceType"), TEXT("RENDERED_ENDGAME_FIXTURE_NOT_NATURAL_GAMEPLAY"));
    Result->SetBoolField(TEXT("success"), Success);
    Result->SetStringField(TEXT("failure"), Failure);
    Result->SetStringField(TEXT("token"), Token);
    Result->SetNumberField(TEXT("processId"), FPlatformProcess::GetCurrentProcessId());
    Result->SetStringField(TEXT("savedDir"), FPaths::ProjectSavedDir());
    Result->SetStringField(TEXT("csv"), Csv);
    Result->SetBoolField(TEXT("noSaveSlotsWritten"), SlotsUntouched);
    Result->SetBoolField(TEXT("allFixtureFramesForeground"), AllFramesForeground);
    Result->SetBoolField(TEXT("sawWave9"), SawWave9);
    Result->SetBoolField(TEXT("sawBreathing"), SawBreathing);
    Result->SetBoolField(TEXT("sawClimax"), SawClimax);
    Result->SetBoolField(TEXT("sawApproach"), SawApproach);
    Result->SetNumberField(TEXT("fixtureFrames"), CapturedFrames);
    Result->SetNumberField(TEXT("climaxSimulationSeconds"), ClimaxSeconds);
    Result->SetNumberField(TEXT("compoundActorPresenceSeconds"), CompoundSeconds);
    Result->SetNumberField(TEXT("approachSimulationSeconds"), ApproachSeconds);
    Result->SetNumberField(TEXT("peakThreats"), PeakThreats);
    Result->SetNumberField(TEXT("wallSeconds"), FPlatformTime::Seconds() - StartedAt);
    Result->SetStringField(
        TEXT("fixture"),
        TEXT("Fixed seed 5eade000000000000000000000000010; starter/RapidLaser; five Tier V paths; OverdriveCooling; "
             "base hull/shield 50000; seeded end of Wave8; no contract/events. Normal wave timings, 40s climax, "
             "caps, budgets, spatial admission and damage. Scripted shallow strafe, boost/brake cycles, dodge/8s and "
             "fire2s/6s. Kind presence includes telegraphs/offscreen actors. No station docking or natural "
             "balance/input/feel acceptance."));
    FString Json;
    FJsonSerializer::Serialize(Result, TJsonWriterFactory<>::Create(&Json));
    const FString ResultPath = Root / TEXT("fixture.json");
    auto &Files = FPlatformFileManager::Get().GetPlatformFile();
    if (Files.IsSymlink(*ResultPath) == ESymlinkResult::NonSymlink)
        FFileHelper::SaveStringToFile(Json, *ResultPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
    UE_LOG(LogTemp, Display, TEXT("ENDGAME_FIXTURE_FINISHED success=%d climax=%.3f compound=%.3f approach=%.3f; %s"),
           Success, ClimaxSeconds, CompoundSeconds, ApproachSeconds, *Failure);
    SetActorTickEnabled(false);
    FPlatformMisc::RequestExit(false);
#endif
}
