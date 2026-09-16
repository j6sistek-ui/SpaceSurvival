#include "SSWave10Soak.h"
#include "SSGameMode.h"
#include "SSGameInstance.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSAlienGallery.h"
#include "Camera/PlayerCameraManager.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "UnrealClient.h"
#include "Kismet/GameplayStatics.h"
#include "SSWorldActors.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "UObject/UObjectIterator.h"
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
bool ReadScenario(bool &Station5, bool &Wave1)
{
    FString Scenario;
    Wave1 = false;
    if (!FParse::Value(FCommandLine::Get(), TEXT("SSSoakScenario="), Scenario))
    {
        Station5 = false;
        return true;
    }
    Station5 = Scenario == TEXT("Station5");
    Wave1 = Scenario == TEXT("Wave1");
    return Station5 || Wave1 || Scenario == TEXT("Wave10") || Scenario == TEXT("Gallery");
}
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
    bool Station5, Wave1;
    if (!ReadScenario(Station5, Wave1) || (Wave1 && !FParse::Param(FCommandLine::Get(), TEXT("SSSoakVisuals"))))
        return false;
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
    ReadScenario(Soak->Station5, Soak->Wave1);
    FString Scenario;
    FParse::Value(FCommandLine::Get(), TEXT("SSSoakScenario="), Scenario);
    Soak->Gallery = Scenario == TEXT("Gallery");
    Soak->CaptureVisuals = FParse::Param(FCommandLine::Get(), TEXT("SSSoakVisuals"));
    Soak->CaptureSequence = Soak->Wave1 && FParse::Param(FCommandLine::Get(), TEXT("SSSoakSequence"));
    Soak->OffscreenVisuals = Soak->CaptureVisuals && FParse::Param(FCommandLine::Get(), TEXT("RenderOffscreen"));
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
           TEXT("RENDERED_FIXTURE_NOT_NATURAL_GAMEPLAY: token=%s process=%u wave1NormalStats=%d; scripted input."),
           *Token, FPlatformProcess::GetCurrentProcessId(), Soak->Wave1);
#endif
}
void ASSWave10Soak::CaptureVisual(const TCHAR *Name, float StageSeconds)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    if (!CaptureVisuals || VisualNames.Contains(Name) || FScreenshotRequest::IsScreenshotRequested())
        return;
    const FString Path = Root / (FString(Name) + TEXT(".png"));
    if (FPlatformFileManager::Get().GetPlatformFile().IsSymlink(*Path) != ESymlinkResult::NonSymlink ||
        IFileManager::Get().FileExists(*Path))
    {
        Stop(TEXT("Visual fixture refuses an existing or redirected screenshot path."));
        return;
    }
    auto Row = MakeShared<FJsonObject>();
    Row->SetStringField(TEXT("name"), Name);
    Row->SetNumberField(TEXT("requestStageSeconds"), StageSeconds);
    Row->SetNumberField(TEXT("requestFrame"), double(GFrameCounter));
    if (FCString::Strcmp(Name, TEXT("CombatImpact")) == 0 && CombatExplosion.IsValid())
    {
        Row->SetStringField(TEXT("combatSourceEnemy"), CombatEnemy);
        Row->SetStringField(TEXT("combatSystem"), GetPathNameSafe(CombatExplosion->GetAsset()));
        Row->SetStringField(TEXT("combatEffectPosition"), CombatExplosion->GetComponentLocation().ToString());
        Row->SetNumberField(TEXT("combatSecondsSinceKill"), GetWorld()->GetTimeSeconds() - CombatKilledAt);
        Row->SetBoolField(TEXT("normalWeaponKill"), true);
    }
    if (auto *GM = Mode.Get(); GM && !Gallery)
    {
        auto *Mesh = IsValid(GM->Walker) && UGameplayStatics::GetPlayerPawn(this, 0) == GM->Walker
                         ? GM->Walker->GetMesh()
                         : GM->Ship->Pilot.Get();
        if (auto *Animation = Mesh->GetSingleNodeInstance())
        {
            Row->SetStringField(TEXT("animation"), GetPathNameSafe(Animation->GetCurrentAsset()));
            Row->SetNumberField(TEXT("animationSeconds"), Animation->GetCurrentTime());
        }
        Row->SetStringField(TEXT("hull"), GetPathNameSafe(GM->Ship->HullMesh->GetStaticMesh()));
        Row->SetStringField(TEXT("cameraTransform"), GM->Ship->Camera->GetComponentTransform().ToHumanReadableString());
        Row->SetNumberField(TEXT("horizontalFov"), GM->Ship->Camera->FieldOfView);
        const auto *PC = UGameplayStatics::GetPlayerController(this, 0);
        const bool ReviewView = IsValid(StationReviewCamera) && PC && PC->GetViewTarget() == StationReviewCamera;
        Row->SetBoolField(TEXT("scriptedStationReviewCamera"), ReviewView);
        if (ReviewView)
        {
            Row->SetStringField(TEXT("cameraTransform"),
                                StationReviewCamera->GetActorTransform().ToHumanReadableString());
            Row->SetNumberField(TEXT("horizontalFov"), StationReviewCamera->GetCameraComponent()->FieldOfView);
            Row->SetStringField(
                TEXT("reviewCameraLimit"),
                TEXT("Scripted visual inspection viewpoint; the actual walking pawn remains possessed."));
        }
        Row->SetBoolField(TEXT("pilotVisible"), GM->Ship->Pilot->IsVisible());
        Row->SetStringField(TEXT("pilotTransform"), Mesh->GetComponentTransform().ToHumanReadableString());
        Row->SetStringField(TEXT("leftWrist"), Mesh->GetSocketTransform(TEXT("L_Wrist")).ToHumanReadableString());
        Row->SetStringField(TEXT("rightWrist"), Mesh->GetSocketTransform(TEXT("R_Wrist")).ToHumanReadableString());
    }
    if (Gallery)
    {
        if (auto *PC = UGameplayStatics::GetPlayerController(this, 0); PC && PC->PlayerCameraManager)
        {
            Row->SetStringField(TEXT("cameraLocation"), PC->PlayerCameraManager->GetCameraLocation().ToString());
            Row->SetStringField(TEXT("cameraRotation"), PC->PlayerCameraManager->GetCameraRotation().ToString());
            Row->SetNumberField(TEXT("horizontalFov"), PC->PlayerCameraManager->GetFOVAngle());
        }
        Row->SetStringField(TEXT("galleryStatus"), Mode->AlienGallery->Status());
    }
    VisualNames.Add(Name);
    VisualRecords.Add(MakeShared<FJsonValueObject>(Row));
    // Viewport + HUD. Only the two explicitly labeled station review frames use
    // a fixture camera. Fulfilled at frame end; this is the request timestamp.
    FScreenshotRequest::RequestScreenshot(Path, true, false, false, FIntRect(), true);
    UE_LOG(LogTemp, Display, TEXT("SOAK_VISUAL_REQUEST %s stageSeconds=%.6f frame=%llu"), Name, StageSeconds,
           GFrameCounter);
#endif
}
void ASSWave10Soak::NotifyEnemyDefeated(ASSEnemy *Enemy)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    if (!IsValid(Enemy) || !FParse::Param(FCommandLine::Get(), TEXT("SSSoakVisuals")))
        return;
    for (TActorIterator<ASSWave10Soak> It(Enemy->GetWorld()); It; ++It)
    {
        auto *Soak = *It;
        if (!Soak->Station5 || !Soak->CaptureVisuals || !Soak->Started || Soak->Stopping ||
            Soak->VisualNames.Contains(TEXT("CombatImpact")) || Soak->CombatExplosion.IsValid())
            continue;
        // Observe the real weapon-death path. A rejected/missing cosmetic must
        // not become successful visual evidence merely because a kill occurred.
        for (TObjectIterator<UNiagaraComponent> Effect; Effect; ++Effect)
            if (Effect->GetWorld() == Enemy->GetWorld() && Effect->IsActive() && !Effect->IsComplete() &&
                Effect->GetAsset() &&
                Effect->GetAsset()->GetPathName() ==
                    TEXT("/Game/SpaceSurvival/Licensed/Combat/NS_EnemyExplosion.NS_EnemyExplosion") &&
                Effect->GetComponentLocation().Equals(Enemy->GetActorLocation(), 1.f))
            {
                Soak->CombatExplosion = *Effect;
                Soak->CombatEnemy = Enemy->GetName();
                Soak->CombatKilledAt = Enemy->GetWorld()->GetTimeSeconds();
                return;
            }
    }
#endif
}
void ASSWave10Soak::CaptureCombatAfterKill()
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    if (!Station5 || !CombatExplosion.IsValid() || VisualNames.Contains(TEXT("CombatImpact")))
        return;
    const double SinceKill = GetWorld()->GetTimeSeconds() - CombatKilledAt;
    if (!CombatExplosion->IsActive() || CombatExplosion->IsComplete() || SinceKill > .65)
    {
        CombatExplosion.Reset();
        return;
    }
    if (SinceKill < .15 || FScreenshotRequest::IsScreenshotRequested())
        return;
    auto *PC = UGameplayStatics::GetPlayerController(this, 0);
    int32 Width = 0, Height = 0;
    FVector2D Pixel;
    if (PC)
        PC->GetViewportSize(Width, Height);
    if (!PC || !PC->ProjectWorldLocationToScreen(CombatExplosion->GetComponentLocation(), Pixel) ||
        Pixel.X < Width * .1 || Pixel.X > Width * .9 || Pixel.Y < Height * .15 || Pixel.Y > Height * .85)
    {
        CombatExplosion.Reset(); // Wait for the next visible, real weapon kill.
        return;
    }
    CaptureVisual(TEXT("CombatImpact"), float(FlightSeconds));
#endif
}
void ASSWave10Soak::CaptureStationReview(const TCHAR *Name, FVector LocalCamera, FVector LocalTarget)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    if (!CaptureVisuals || !Station5 || !VisualNames.Contains(TEXT("StationIdle")) || VisualNames.Contains(Name) ||
        FScreenshotRequest::IsScreenshotRequested())
        return;
    auto *GM = Mode.Get();
    auto *PC = UGameplayStatics::GetPlayerController(this, 0);
    if (!GM || !IsValid(GM->Hub) || !PC || !IsValid(GM->Walker) || PC->GetPawn() != GM->Walker ||
        GM->Walker->IsDisembarking())
    {
        Stop(TEXT("Station review camera requires the existing hub and possessed walking pawn after exit."));
        return;
    }
    if (StationReviewShot != FName(Name))
    {
        if (!IsValid(StationReviewCamera))
        {
            PreviousReviewViewTarget = PC->GetViewTarget();
            FActorSpawnParameters Parameters;
            Parameters.Owner = this;
            Parameters.ObjectFlags |= RF_Transient;
            StationReviewCamera = GetWorld()->SpawnActor<ACameraActor>(Parameters);
            if (!StationReviewCamera)
            {
                Stop(TEXT("Could not create the transient station review camera."));
                return;
            }
            StationReviewCamera->SetActorEnableCollision(false);
            StationReviewCamera->SetActorTickEnabled(false);
            StationReviewCamera->GetCameraComponent()->SetFieldOfView(70.f);
        }
        const FTransform HubTransform = GM->Hub->GetActorTransform();
        const FVector Position = HubTransform.TransformPosition(LocalCamera);
        const FVector Target = HubTransform.TransformPosition(LocalTarget);
        StationReviewCamera->SetActorLocationAndRotation(Position, (Target - Position).Rotation());
        PC->SetViewTarget(StationReviewCamera);
        StationReviewShot = FName(Name);
        // Let the normal camera update and temporal rendering settle before the
        // screenshot request; never move or possess a different gameplay pawn.
        ReviewCameraReadyAt = StationIdleSeconds + .5;
        return;
    }
    if (StationIdleSeconds >= ReviewCameraReadyAt)
        CaptureVisual(Name, float(StationIdleSeconds));
#endif
}
void ASSWave10Soak::Stop(const FString &Error)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    if (Stopping)
        return;
    Failure = Error;
    Stopping = true;
    if (IsValid(StationReviewCamera))
    {
        if (auto *PC = UGameplayStatics::GetPlayerController(this, 0);
            PC && PC->GetViewTarget() == StationReviewCamera && PreviousReviewViewTarget.IsValid())
            PC->SetViewTarget(PreviousReviewViewTarget.Get());
        StationReviewCamera->Destroy();
        StationReviewCamera = nullptr;
    }
    CaptureResult = FCsvProfiler::Get()->EndCapture();
#endif
}
void ASSWave10Soak::TickGallery(float Dt)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    auto *GM = Mode.Get();
    auto *PC = UGameplayStatics::GetPlayerController(this, 0);
    auto *GI = GM ? GM->GetGameInstance<USSGameInstance>() : nullptr;
    if (!GI || !PC || !GM->Walker || !GM->Hub || !CaptureVisuals)
    {
        Stop(TEXT("Gallery fixture requires the fresh home hangar and visual capture."));
        return;
    }
    ++CapturedFrames;
    AllFramesForeground &= FApp::HasFocus();
    const double Now = FPlatformTime::Seconds();
    auto Next = [&]()
    {
        ++GalleryStage;
        GalleryStageAt = Now;
        GalleryReadyAt = 0;
    };
    auto Payload = [&]() { return FString(UTF8_TO_TCHAR(SS::EncodeRun(GI->Session.run).c_str())); };
    auto Account = [&]() { return FString(UTF8_TO_TCHAR(SS::EncodeAccount(GI->Session.account).c_str())); };
    if (GalleryStage == 0)
    {
        GM->ClosePanel();
        GM->Walker->SetActorLocation(GM->Hub->GetActorTransform().TransformPosition(FVector(450, 900, 100)));
        PC->SetControlRotation(FRotator(-10, 90, 0));
        Started = true;
        Next();
    }
    else if (GalleryStage == 1 && Now - GalleryStageAt > 4)
    {
        CaptureVisual(TEXT("GalleryDoorway"), float(Now - StartedAt));
        Next();
    }
    else if (GalleryStage == 2 && Now - GalleryStageAt > 1)
    {
        GalleryReturnTransform = GM->Walker->GetActorTransform();
        GalleryRunBefore = Payload();
        GalleryAccountBefore = Account();
        GM->Interact();
        if (!GM->AlienGallery->IsActive())
        {
            Stop(TEXT("Station doorway did not enter installed alien gallery."));
            return;
        }
        Next();
    }
    else if (GalleryStage == 3 || GalleryStage == 5)
    {
        if (!GM->AlienGallery->IsActive())
        {
            Stop(TEXT("Gallery exited before requested scene was ready."));
            return;
        }
        if (Payload() != GalleryRunBefore || Account() != GalleryAccountBefore)
        {
            Stop(TEXT("Gallery changed run/account state."));
            return;
        }
        if (!GM->AlienGallery->IsReady())
            return;
        if (GalleryReadyAt == 0)
            GalleryReadyAt = Now;
        if (Now - GalleryReadyAt < 10)
            return;
        if (GalleryStage == 5 && !GM->AlienGallery->Status().Contains(TEXT("ASSET GALLERY")))
        {
            Stop(TEXT("Asset gallery did not switch maps."));
            return;
        }
        CaptureVisual(GalleryStage == 3 ? TEXT("GalleryShowcase") : TEXT("GalleryAssets"), float(Now - StartedAt));
        Next();
    }
    else if (GalleryStage == 4 && Now - GalleryStageAt > 1)
    {
        GM->AlienGallery->SwitchScene();
        Next();
    }
    else if (GalleryStage == 6 && Now - GalleryStageAt > 1)
    {
        GM->AlienGallery->Leave();
        Next();
    }
    else if (GalleryStage == 7 && !GM->AlienGallery->IsActive())
    {
        GalleryReturned =
            PC->GetPawn() == GM->Walker && GM->Walker->GetActorTransform().Equals(GalleryReturnTransform, .1);
        GalleryRunPreserved = Payload() == GalleryRunBefore && Account() == GalleryAccountBefore;
        if (!GalleryReturned || !GalleryRunPreserved)
        {
            Stop(TEXT("Gallery return did not preserve pawn/transform/session."));
            return;
        }
        Next();
    }
    else if (GalleryStage == 8 && Now - GalleryStageAt > 3)
    {
        CaptureVisual(TEXT("GalleryReturn"), float(Now - StartedAt));
        Next();
    }
    else if (GalleryStage == 9 && Now - GalleryStageAt > 2)
        Stop(TEXT(""));
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
        if (!OffscreenVisuals && !FApp::HasFocus())
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
    if (!GI ||
        FPlatformTime::Seconds() - StartedAt > (Gallery    ? 240
                                                : Wave1    ? 90
                                                : Station5 ? 240
                                                           : 180) ||
        !FMath::IsNearlyEqual(GetWorld()->GetWorldSettings()->GetEffectiveTimeDilation(), 1.f) ||
        FApp::UseFixedTimeStep() || (GEngine && GEngine->bUseFixedFrameRate))
    {
        Stop(TEXT("Missing world, timeout, fixed timestep or time dilation invalidates this rendered fixture."));
        return;
    }
    if (!FCsvProfiler::IsCapturing())
        return;
    if (Gallery)
    {
        TickGallery(Dt);
        return;
    }
    auto &S = GI->Session;
    if (!Started)
    {
        // Seed only test memory; retain normal durations, caps, pressure, damage and spawn rules.
        if (!Wave1)
            S.tuning.baseHull = S.tuning.baseShield = 50000;
        if (!S.StartRun("5eade000000000000000000000000010"))
        {
            Stop(TEXT("Fixture run initialization failed."));
            return;
        }
        if (!Wave1)
        {
            S.run.tiers = {{5, 5, 5, 5, 5}};
            S.run.utility = SS::Utility::OverdriveCooling;
            S.run.wave = Station5 ? 4 : 8;
            S.run.wavesCompleted = S.run.wave - 1;
            S.run.depotSeen = S.run.salvageEventSeen = S.run.distressEventSeen = true;
            S.FinishWave(); // Real breathing enters the next normal wave through Session::Tick.
        }
        S.run.hull = S.Stats().maxHull;
        S.run.shield = S.Stats().maxShield;
        GM->PreviousPhase = GM->PreviousWave = -1;
        GM->Director->ResetEncounter();
        GM->SpawnFlight(FVector(0, 0, 7000), FRotator::ZeroRotator);
        GM->Announce(Wave1      ? TEXT("WAVE 1 VISUAL FIXTURE / NORMAL STARTER STATS / SCRIPTED INPUT")
                     : Station5 ? TEXT("AUTOMATED STATION 1 CAPTURE / SEEDED BUILD / NOT NATURAL GAMEPLAY")
                                : TEXT("AUTOMATED ENDGAME CAPTURE / SEEDED BUILD / NOT NATURAL GAMEPLAY"));
        Started = true;
        return; // GM phase counters were sampled before this one-time seed; mark only subsequent frames.
    }
    if (!S.run.active || !IsValid(GM->Ship) ||
        S.run.wave > (Wave1      ? 1
                      : Station5 ? 5
                                 : 10) ||
        !FMath::IsNearlyEqual(S.tuning.climaxSeconds, 40.0) ||
        (Station5 &&
         (!FMath::IsNearlyEqual(S.tuning.wormholeSeconds, 8.0) || !FMath::IsNearlyEqual(S.tuning.dockingSeconds, 3.0))))
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
    const bool Exiting =
        Station5 && S.run.phase == SS::Phase::Station && IsValid(GM->Walker) && GM->Walker->IsDisembarking();
    const int32 Stage = S.run.phase == SS::Phase::Station ? (Exiting ? 7 : 8) : int32(S.run.phase);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Scenario, Wave1 ? 3 : Station5 ? 2 : 1, ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Stage, Stage, ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Phase, int32(S.run.phase), ECsvCustomStatOp::Set);
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
    if (Wave1)
    {
        SawFlightWave |= S.run.wave == 1 && S.run.phase == SS::Phase::Flight;
        const bool Turning = FlightSeconds >= 7 && FlightSeconds < 14;
        GM->Ship->SetFlightInput(Turning ? FVector2D(.16, .035) : FVector2D::ZeroVector, FVector2D::ZeroVector, 0.f,
                                 FlightSeconds >= 14 && FlightSeconds < 21, FlightSeconds >= 21 && FlightSeconds < 28);
        const float Times[] = {5.f, 12.f, 19.f, 25.f};
        const TCHAR *Names[] = {TEXT("Cruise"), TEXT("Turn"), TEXT("Boost"), TEXT("Brake")};
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(Times); ++Index)
            if (FlightSeconds >= Times[Index])
                CaptureVisual(Names[Index], float(FlightSeconds));
        if (CaptureSequence && FlightSeconds >= NextSequenceSeconds && !FScreenshotRequest::IsScreenshotRequested())
        {
            const FString Name = FString::Printf(TEXT("Sequence_%03d"), SequenceIndex++);
            CaptureVisual(*Name, float(FlightSeconds));
            // Actual request timestamps remain in the receipt; no fixed timestep or interpolation.
            NextSequenceSeconds = FlightSeconds + .25;
        }
        if (Threats > GM->Director->MaximumActiveThreats)
            Stop(TEXT("Director active threat cap exceeded during Wave 1 visual fixture."));
        else if (FlightSeconds >= 29)
            Stop(SawFlightWave ? FString() : TEXT("Normal Wave 1 flight was not observed."));
        return;
    }
    SawFlightWave |= S.run.wave == (Station5 ? 5 : 9) && S.run.phase == SS::Phase::Flight;
    SawBreathing |= S.run.wave == (Station5 ? 4 : 9) && S.run.phase == SS::Phase::Breathing;
    if (S.run.wave == (Station5 ? 5 : 10) && S.run.phase == SS::Phase::Climax)
    {
        SawClimax = true;
        ClimaxSeconds += Dt;
        if (Kinds[5] > 0 && Kinds[0] + Kinds[1] + Kinds[2] > 0 && Kinds[6] + Kinds[7] > 0)
            CompoundSeconds += Dt;
    }
    if (S.run.wave == (Station5 ? 5 : 10) && S.run.phase == SS::Phase::Approach)
    {
        SawApproach = true;
        ApproachSeconds += Dt;
    }
    if (Station5 && S.run.phase == SS::Phase::Wormhole)
    {
        SawWormhole = true;
        WormholeSeconds += Dt;
    }
    if (Station5 && S.run.phase == SS::Phase::Docking)
    {
        SawDocking = true;
        DockingSeconds += Dt;
    }
    if (Station5 && S.run.phase == SS::Phase::Station)
    {
        if (!IsValid(GM->Walker) || UGameplayStatics::GetPlayerPawn(this, 0) != GM->Walker)
        {
            Stop(TEXT("Station fixture did not possess the actual exit/walking pawn."));
            return;
        }
        if (Exiting)
        {
            SawExit = true;
            ExitSeconds += Dt;
        }
        else
            StationIdleSeconds += Dt;
    }
    if (CaptureVisuals)
    {
        CaptureCombatAfterKill();
        if (S.run.phase == SS::Phase::Flight && FlightSeconds >= 15)
            CaptureVisual(TEXT("Flight"), FlightSeconds);
        if (S.run.phase == SS::Phase::Climax && ClimaxSeconds >= 5)
            CaptureVisual(TEXT("Climax"), ClimaxSeconds);
        if (!Station5 && CompoundSeconds >= 4 && S.run.phase == SS::Phase::Climax && Kinds[5] > 0 &&
            Kinds[0] + Kinds[1] + Kinds[2] > 0 && Kinds[6] + Kinds[7] > 0)
            CaptureVisual(TEXT("Compound"), ClimaxSeconds);
        if (S.run.phase == SS::Phase::Approach && ApproachSeconds >= 1)
            CaptureVisual(TEXT("Approach"), ApproachSeconds);
        if (Station5)
        {
            if (S.run.phase == SS::Phase::Wormhole && WormholeSeconds >= 2)
                CaptureVisual(TEXT("Wormhole"), WormholeSeconds);
            if (S.run.phase == SS::Phase::Docking && DockingSeconds >= 1)
                CaptureVisual(TEXT("Docking"), DockingSeconds);
            if (Exiting)
            {
                const float Times[] = {0.f, .1f, .27f, .82f, 1.2f, 1.65f, 2.35f};
                for (int32 Index = 0; Index < UE_ARRAY_COUNT(Times); ++Index)
                    if (ExitSeconds >= Times[Index])
                        CaptureVisual(*FString::Printf(TEXT("Exit%d"), Index), ExitSeconds);
            }
            if (StationIdleSeconds >= 2)
                CaptureVisual(TEXT("StationIdle"), StationIdleSeconds);
            if (StationIdleSeconds >= 7)
                CaptureStationReview(TEXT("StationServices"), FVector(600, 500, 220), FVector(1110, 1130, 160));
            if (StationIdleSeconds >= 12 && VisualNames.Contains(TEXT("StationServices")))
                CaptureStationReview(TEXT("StationOverview"), FVector(1300, -1150, 650), FVector(-600, 0, 300));
        }
        const TCHAR *TextureStage = Station5 ? TEXT("StationIdle") : TEXT("Compound");
        if (VisualNames.Contains(TextureStage) && !VisualNames.Contains(TEXT("TexturesLogged")))
        {
            VisualNames.Add(TEXT("TexturesLogged"));
            UE_LOG(LogTemp, Display, TEXT("SOAK_VISUAL_TEXTURE_RESIDENCY_BEGIN"));
            GEngine->Exec(GetWorld(), TEXT("ListTextures"));
            UE_LOG(LogTemp, Display, TEXT("SOAK_VISUAL_TEXTURE_RESIDENCY_END"));
        }
    }
    // Applied after normal simulation for the next engine frame; never relocate the ship or force docking.
    if (Station5 && S.run.phase == SS::Phase::Approach && IsValid(GM->Hub))
    {
        const FRotator Desired = (GM->Hub->DockPosition() - GM->Ship->GetActorLocation()).Rotation();
        const FRotator Current = GM->Ship->GetActorRotation();
        const FVector2D Steering(
            FMath::Clamp(FMath::FindDeltaAngleDegrees(Current.Yaw, Desired.Yaw) / 30.f, -.75f, .75f),
            FMath::Clamp(FMath::FindDeltaAngleDegrees(Current.Pitch, Desired.Pitch) / 30.f, -.75f, .75f));
        GM->Ship->SetFlightInput(Steering, FVector2D::ZeroVector, -1.f, false, false);
    }
    else if (!Station5 || (S.run.phase != SS::Phase::Docking && S.run.phase != SS::Phase::Station))
    {
        const double Cycle = FMath::Fmod(FlightSeconds, 12.0);
        GM->Ship->SetFlightInput(
            FVector2D::ZeroVector,
            FVector2D(.12 * FMath::Sin(FlightSeconds * .35), .08 * FMath::Cos(FlightSeconds * .35)), 0.f, Cycle < 2.0,
            Cycle >= 6.0 && Cycle < 8.0);
        if (FlightSeconds >= NextDodge)
        {
            GM->Ship->RequestDodge();
            NextDodge += 8.0;
        }
        if (FMath::Fmod(FlightSeconds, 6.0) < 2.0)
            GM->Ship->Fire();
    }
    if (Threats > GM->Director->MaximumActiveThreats)
        Stop(TEXT("Director active threat cap exceeded during rendered fixture."));
    else if (Station5 && StationIdleSeconds >= 15)
        Stop(SawFlightWave && SawBreathing && SawWormhole && WormholeSeconds >= 7.9 && SawClimax &&
                     ClimaxSeconds >= 39.5 && SawApproach && ApproachSeconds > 0 && SawDocking &&
                     DockingSeconds >= 2.9 && SawExit && ExitSeconds >= 2.3
                 ? FString()
                 : TEXT("Required complete Wave 5, wormhole, docking or authored exit coverage was not observed."));
    else if (!Station5 && ApproachSeconds >= 5)
        Stop(SawFlightWave && SawBreathing && SawClimax && ClimaxSeconds >= 39.5 && CompoundSeconds >= 3.5
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
    if (CaptureVisuals)
    {
        const TArray<FString> Expected =
            Gallery    ? TArray<FString>{TEXT("GalleryDoorway"), TEXT("GalleryShowcase"), TEXT("GalleryAssets"),
                                         TEXT("GalleryReturn")}
            : Station5 ? TArray<FString>{TEXT("Flight"),      TEXT("Climax"),          TEXT("Wormhole"),
                                         TEXT("Approach"),    TEXT("Docking"),         TEXT("Exit0"),
                                         TEXT("Exit1"),       TEXT("Exit2"),           TEXT("Exit3"),
                                         TEXT("Exit4"),       TEXT("Exit5"),           TEXT("Exit6"),
                                         TEXT("StationIdle"), TEXT("StationServices"), TEXT("StationOverview"),
                                         TEXT("CombatImpact")}
            : Wave1    ? TArray<FString>{TEXT("Cruise"), TEXT("Turn"), TEXT("Boost"), TEXT("Brake")}
                       : TArray<FString>{TEXT("Flight"), TEXT("Climax"), TEXT("Compound"), TEXT("Approach")};
        if (VisualRecords.Num() != Expected.Num() + SequenceIndex || (CaptureSequence && SequenceIndex < 40))
            Failure = TEXT("Visual fixture did not request every required scene stage.");
        for (const FString &Name : Expected)
            if (!VisualNames.Contains(Name))
                Failure = TEXT("Visual fixture is missing required scene stage: ") + Name;
        for (const auto &Row : VisualRecords)
            if (IFileManager::Get().FileSize(
                    *(Root / (Row->AsObject()->GetStringField(TEXT("name")) + TEXT(".png")))) <= 0)
                Failure = TEXT("Visual fixture screenshot was not written.");
    }
    const bool SlotsUntouched = NoSaveSlots();
    if (Gallery && (!GalleryRunPreserved || !GalleryReturned))
        Failure = TEXT("Gallery return/session checks failed.");
    const FString Csv = CaptureResult.Get();
    const bool Success =
        Failure.IsEmpty() && SlotsUntouched && !Csv.IsEmpty() && (AllFramesForeground || OffscreenVisuals);
    auto Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("evidenceType"), Gallery    ? TEXT("ALIEN_GALLERY_SCRIPTED_VISUAL_REVIEW")
                                                 : Wave1    ? TEXT("WAVE1_VISUAL_ONLY_SCRIPTED_NORMAL_STATS")
                                                 : Station5 ? TEXT("RENDERED_TRANSITION_FIXTURE_NOT_NATURAL_GAMEPLAY")
                                                            : TEXT("RENDERED_ENDGAME_FIXTURE_NOT_NATURAL_GAMEPLAY"));
    Result->SetBoolField(TEXT("success"), Success);
    Result->SetBoolField(TEXT("visualCaptureEnabled"), CaptureVisuals);
    Result->SetArrayField(TEXT("visualRequests"), VisualRecords);
    Result->SetStringField(
        TEXT("visualCaptureLimit"),
        TEXT("Viewport screenshots are fulfilled after each recorded request. StationServices and "
             "StationOverview use labeled fixture cameras without changing possession. Image readback "
             "and ListTextures perturb timings; visual captures are not performance evidence."));
    Result->SetStringField(TEXT("failure"), Failure);
    Result->SetStringField(TEXT("token"), Token);
    Result->SetNumberField(TEXT("processId"), FPlatformProcess::GetCurrentProcessId());
    Result->SetStringField(TEXT("savedDir"), FPaths::ProjectSavedDir());
    Result->SetStringField(TEXT("csv"), Csv);
    Result->SetBoolField(TEXT("noSaveSlotsWritten"), SlotsUntouched);
    Result->SetBoolField(TEXT("allFixtureFramesForeground"), AllFramesForeground);
    Result->SetBoolField(TEXT("offscreenVisualOnly"), OffscreenVisuals);
    Result->SetBoolField(TEXT("suitableForPerformanceFinding"), !Wave1 && !CaptureVisuals && AllFramesForeground);
    Result->SetStringField(TEXT("scenario"), Gallery    ? TEXT("Gallery")
                                             : Wave1    ? TEXT("Wave1")
                                             : Station5 ? TEXT("Station5")
                                                        : TEXT("Wave10"));
    Result->SetBoolField(TEXT("galleryReturned"), GalleryReturned);
    Result->SetBoolField(TEXT("galleryRunPreserved"), GalleryRunPreserved);
    Result->SetBoolField(TEXT("sawWave1"), Wave1 && SawFlightWave);
    Result->SetBoolField(TEXT("sawWave9"), !Wave1 && !Station5 && SawFlightWave);
    Result->SetBoolField(TEXT("sawWave5"), Station5 && SawFlightWave);
    Result->SetBoolField(TEXT("sawWormhole"), SawWormhole);
    Result->SetBoolField(TEXT("sawDocking"), SawDocking);
    Result->SetBoolField(TEXT("sawAuthoredExit"), SawExit);
    Result->SetNumberField(TEXT("wormholeSimulationSeconds"), WormholeSeconds);
    Result->SetNumberField(TEXT("dockingSimulationSeconds"), DockingSeconds);
    Result->SetNumberField(TEXT("exitSimulationSeconds"), ExitSeconds);
    Result->SetNumberField(TEXT("stationIdleSimulationSeconds"), StationIdleSeconds);
    Result->SetBoolField(TEXT("sawBreathing"), SawBreathing);
    Result->SetBoolField(TEXT("sawClimax"), SawClimax);
    Result->SetBoolField(TEXT("sawApproach"), SawApproach);
    Result->SetNumberField(TEXT("fixtureFrames"), CapturedFrames);
    Result->SetNumberField(TEXT("climaxSimulationSeconds"), ClimaxSeconds);
    Result->SetNumberField(TEXT("compoundActorPresenceSeconds"), CompoundSeconds);
    Result->SetNumberField(TEXT("approachSimulationSeconds"), ApproachSeconds);
    Result->SetNumberField(TEXT("peakThreats"), PeakThreats);
    Result->SetNumberField(TEXT("wallSeconds"), FPlatformTime::Seconds() - StartedAt);
    if (Gallery)
        Result->SetStringField(
            TEXT("fixture"), TEXT("Fresh isolated home hangar; scripted walker placement at real service, ordinary "
                                  "interaction, full vendor showcase, asset layout, return. Exact run/account and "
                                  "return transform checked. No save APIs, natural input or performance acceptance."));
    else if (Wave1)
        Result->SetStringField(
            TEXT("fixture"),
            TEXT("Normal fresh Wave1 starter stats, TierI, no utility, real damage and Director. "
                 "29 seconds scripted cruise/turn/boost/brake; no fire, forced survival or duration override. "
                 "Screenshot-only evidence, not physical input, natural balance or performance acceptance. "
                 "SSShipRefresh optionally selects candidate hull; each screenshot records actual asset and pilot "
                 "visibility."));
    else if (Station5)
        Result->SetStringField(
            TEXT("fixture"),
            TEXT("Seeded end of Wave4; starter/RapidLaser, Tier V, OverdriveCooling, base durability50000. Normal "
                 "Wave5, 8s wormhole,40s climax, ordinary bounded steering to port, actual docking and2.4s exit,15s "
                 "stationary hub. No forced docking/teleport, menu purchases, physical input, natural "
                 "progression/balance or representative FPS acceptance."));
    else
        Result->SetStringField(
            TEXT("fixture"),
            TEXT(
                "Fixed seed 5eade000000000000000000000000010; starter/RapidLaser; five Tier V paths; OverdriveCooling; "
                "base hull/shield 50000; seeded end of Wave8; no contract/events. Normal wave timings, 40s climax, "
                "caps, budgets, spatial admission and damage. Scripted shallow strafe, boost/brake cycles, dodge/8s "
                "and "
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
