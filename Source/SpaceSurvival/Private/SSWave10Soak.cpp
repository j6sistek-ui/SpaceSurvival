#include "SSWave10Soak.h"
#include "SSGameMode.h"
#include "SSGameInstance.h"
#include "SSHUD.h"
#include "SSShip.h"
#include "SSShipVisualRig.h"
#include "SSStation.h"
#include "SSLandingPad.h"
#include "Components/SphereComponent.h"
#include "Engine/World.h"
#include "SSAlienGallery.h"
#include "Camera/PlayerCameraManager.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
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
#if WITH_EDITOR
#include "AssetCompilingManager.h"
#include "ShaderCompiler.h"
#endif

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
    return Station5 || Wave1 || Scenario == TEXT("Wave10") || Scenario == TEXT("Gallery") ||
           Scenario == TEXT("MainMenu");
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
    FString Scenario;
    FParse::Value(FCommandLine::Get(), TEXT("SSSoakScenario="), Scenario);
    if (Scenario == TEXT("MainMenu") && (!FParse::Param(FCommandLine::Get(), TEXT("SSSoakVisuals")) ||
                                         FParse::Param(FCommandLine::Get(), TEXT("SSSoakSequence"))))
        return false;
    if (FParse::Param(FCommandLine::Get(), TEXT("SSStationExteriorReview")) &&
        (!Station5 || !FParse::Param(FCommandLine::Get(), TEXT("SSSoakVisuals"))))
        return false;
    if (FParse::Param(FCommandLine::Get(), TEXT("SSWeaponReadability")) &&
        (!Wave1 || FParse::Param(FCommandLine::Get(), TEXT("SSSoakSequence"))))
        return false;
    FString WalkerRequest;
    const bool HasWalkerRequest = FParse::Value(FCommandLine::Get(), TEXT("SSSoakWalker="), WalkerRequest);
    if ((HasWalkerRequest || FParse::Param(FCommandLine::Get(), TEXT("SSSoakWalker"))) &&
        (!HasWalkerRequest || !Station5 || WalkerRequest != TEXT("AlienFemale") ||
         !FParse::Param(FCommandLine::Get(), TEXT("SSSoakVisuals"))))
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
    Soak->MainMenu = Scenario == TEXT("MainMenu");
    Soak->CaptureVisuals = FParse::Param(FCommandLine::Get(), TEXT("SSSoakVisuals"));
    Soak->WeaponReadability = Soak->Wave1 && FParse::Param(FCommandLine::Get(), TEXT("SSWeaponReadability"));
    Soak->CaptureStationExterior = FParse::Param(FCommandLine::Get(), TEXT("SSStationExteriorReview"));
    Soak->CaptureSequence = Soak->Wave1 && FParse::Param(FCommandLine::Get(), TEXT("SSSoakSequence"));
    Soak->OffscreenVisuals = Soak->CaptureVisuals && FParse::Param(FCommandLine::Get(), TEXT("RenderOffscreen"));
    FParse::Value(FCommandLine::Get(), TEXT("SSSoakWalker="), Soak->RequestedWalkerId);
    if (!Soak->RequestedWalkerId.IsEmpty())
    {
        const auto Bodies = InMode->WardrobeBodies();
        const auto *Requested = Bodies.FindByPredicate(
            [Soak](const FSSHeroDefinition &Hero)
            { return Hero.Id.ToString() == Soak->RequestedWalkerId && Hero.Installed(ESSHeroSlot::Walker); });
        if (!Requested)
        {
            UE_LOG(LogTemp, Error, TEXT("Station capture refused: requested exact walker is not installed: %s"),
                   *Soak->RequestedWalkerId);
            Soak->Destroy();
            return;
        }
        // Only this fresh isolated profile changes. EnterStation still selects and
        // applies the requested body through the actual account/WearHero path.
        GI->Session.account.hero = int32(Requested->Identity);
    }
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
    if (MainMenu && !FParse::Param(FCommandLine::Get(), TEXT("SSUIRefreshReview")))
    {
        const auto *GM = Mode.Get();
        const auto *PC = UGameplayStatics::GetPlayerController(this, 0);
        const auto *HUD = PC ? Cast<ASSHUD>(PC->GetHUD()) : nullptr;
        Row->SetBoolField(TEXT("actualFigmaTitleDrawn"), HUD && HUD->IsDrawingFigmaMainMenu());
        Row->SetNumberField(TEXT("selectedEntry"), GM->SelectedEntry);
        Row->SetNumberField(TEXT("renderedFocusEntry"), HUD->GetFigmaMainMenuFocus());
        Row->SetStringField(TEXT("selectionPath"),
                            TEXT("Labeled synthetic SelectedEntry; no physical input or pointer movement."));
        TArray<TSharedPtr<FJsonValue>> Rows;
        for (int32 Index = 0; Index < GM->Entries.Num(); ++Index)
        {
            const auto &Bounds = HUD->GetMenuBounds()[Index];
            auto Entry = MakeShared<FJsonObject>();
            Entry->SetNumberField(TEXT("index"), Index);
            Entry->SetNumberField(TEXT("action"), GM->Entries[Index].Action);
            Entry->SetBoolField(TEXT("enabled"), GM->Entries[Index].Enabled);
            Entry->SetNumberField(TEXT("minX"), Bounds.Min.X);
            Entry->SetNumberField(TEXT("minY"), Bounds.Min.Y);
            Entry->SetNumberField(TEXT("maxX"), Bounds.Max.X);
            Entry->SetNumberField(TEXT("maxY"), Bounds.Max.Y);
            Entry->SetNumberField(TEXT("centerHitIndex"), HUD->MenuIndexAt(Bounds.GetCenter()));
            Rows.Add(MakeShared<FJsonValueObject>(Entry));
        }
        Row->SetArrayField(TEXT("titleRows"), Rows);
    }
    if (auto *GM = Mode.Get(); GM && !Gallery && !MainMenu)
    {
        if (WeaponReadability)
        {
            const auto *GI = GM->GetGameInstance<USSGameInstance>();
            Row->SetStringField(TEXT("weapon"), GI->Session.run.weapon == SS::Weapon::HeavyCannon ? TEXT("HeavyCannon")
                                                                                                  : TEXT("RapidLaser"));
            Row->SetNumberField(TEXT("confirmedHitFeedbackSeconds"), GM->PlayerHitFlashSeconds);
            Row->SetStringField(TEXT("muzzle"), GM->Ship->MuzzleWorldPosition().ToString());
            Row->SetStringField(TEXT("target"), GetNameSafe(WeaponReviewTarget.Get()));
            Row->SetNumberField(TEXT("uncapturedWarmupShots"), WeaponWarmupShots);
            Row->SetNumberField(TEXT("renderingReadyAtSeconds"), WeaponRenderingReadyAt);
            int32 Projectiles = 0, Pulses = 0;
            for (TActorIterator<ASSProjectile> It(GetWorld()); It; ++It)
                Projectiles += !It->IsActorBeingDestroyed() ? 1 : 0;
            for (TActorIterator<ASSWeaponTracePulse> It(GetWorld()); It; ++It)
                Pulses += !It->IsActorBeingDestroyed() ? 1 : 0;
            Row->SetNumberField(TEXT("liveProjectiles"), Projectiles);
            Row->SetNumberField(TEXT("liveLaserPulses"), Pulses);
        }
        const bool Walking = IsValid(GM->Walker) && UGameplayStatics::GetPlayerPawn(this, 0) == GM->Walker;
        auto *Mesh = Walking ? GM->Walker->GetMesh() : GM->Ship->Pilot.Get();
        if (Walking && !RequestedWalkerId.IsEmpty())
        {
            Row->SetStringField(TEXT("requestedWalker"), RequestedWalkerId);
            Row->SetStringField(TEXT("walkerMesh"), GetPathNameSafe(Mesh->GetSkeletalMeshAsset()));
            Row->SetBoolField(TEXT("walkerMeshVisible"), Mesh->IsVisible());
            Row->SetStringField(TEXT("walkerTransform"), GM->Walker->GetActorTransform().ToHumanReadableString());
            Row->SetStringField(TEXT("walkerMeshBounds"), Mesh->Bounds.BoxExtent.ToString());
            Row->SetNumberField(TEXT("walkerSpeed"), GM->Walker->GetVelocity().Size());
            Row->SetNumberField(TEXT("walkerMotionSeconds"), WalkerMotionSeconds);
            Row->SetBoolField(TEXT("actualWalkerView"),
                              UGameplayStatics::GetPlayerController(this, 0)->GetViewTarget() == GM->Walker);
        }
        // Whose bone names to ask for: the hero actually wearing the measured component.
        const FSSHeroDefinition &Hero = Walking ? GM->Walker->GetHero() : GM->Ship->GetPilotHero();
        Row->SetStringField(TEXT("hero"), Hero.Id.ToString());
        if (auto *Animation = Mesh->GetSingleNodeInstance())
        {
            Row->SetStringField(TEXT("animation"), GetPathNameSafe(Animation->GetCurrentAsset()));
            Row->SetNumberField(TEXT("animationSeconds"), Animation->GetCurrentTime());
        }
        const FSSHullDefinition Hull(ASSShip::SelectedHullIdentity());
        const auto *Rig = GM->Ship->GetVisualRig();
        const auto *VisibleSkeletalHull = GM->Ship->SkeletalHull.Get();
        const bool SkeletalHullVisible =
            VisibleSkeletalHull && VisibleSkeletalHull->IsVisible() && VisibleSkeletalHull->GetSkeletalMeshAsset();
        Row->SetStringField(TEXT("hullIdentity"), Hull.Id.ToString());
        Row->SetStringField(TEXT("hullDefinitionMesh"), Hull.MeshPath);
        Row->SetBoolField(TEXT("blueprintRigActive"), Rig && Rig->HasBlueprintRig());
        Row->SetStringField(TEXT("hull"), SkeletalHullVisible
                                              ? GetPathNameSafe(VisibleSkeletalHull->GetSkeletalMeshAsset())
                                              : GetPathNameSafe(GM->Ship->HullMesh->GetStaticMesh()));
        Row->SetStringField(TEXT("fallbackHull"), GetPathNameSafe(GM->Ship->HullMesh->GetStaticMesh()));
        Row->SetBoolField(TEXT("fallbackHullVisible"), GM->Ship->HullMesh->IsVisible());
        Row->SetStringField(TEXT("cameraTransform"), GM->Ship->Camera->GetComponentTransform().ToHumanReadableString());
        Row->SetNumberField(TEXT("horizontalFov"), GM->Ship->Camera->FieldOfView);
        const auto *PC = UGameplayStatics::GetPlayerController(this, 0);
        if (Walking && !RequestedWalkerId.IsEmpty() && PC && PC->PlayerCameraManager)
        {
            Row->SetStringField(TEXT("cameraTransform"), FTransform(PC->PlayerCameraManager->GetCameraRotation(),
                                                                    PC->PlayerCameraManager->GetCameraLocation())
                                                             .ToHumanReadableString());
            Row->SetNumberField(TEXT("horizontalFov"), PC->PlayerCameraManager->GetFOVAngle());
        }
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
        // A hero that does not have the asked-for bone used to read back as the component itself, which
        // looks like a measurement. The value is still recorded, now beside the name it stands for and
        // an explicit admission when that name resolved to nothing.
        auto RecordBone = [&Row, Mesh, &Hero](const TCHAR *Field, FName Bone)
        {
            FTransform Transform;
            const bool Resolved = FSSHeroDefinition::ResolveBone(Mesh, Bone, Transform);
            Row->SetStringField(Field, Transform.ToHumanReadableString());
            Row->SetStringField(FString(Field) + TEXT("Bone"), Bone.ToString());
            if (!Resolved)
            {
                Row->SetBoolField(FString(Field) + TEXT("Missing"), true);
                UE_LOG(LogTemp, Warning,
                       TEXT("SOAK_BONE_MISSING field=%s hero=%s bone=%s mesh=%s; the component transform was "
                            "recorded because this hero has no such bone."),
                       Field, *Hero.Id.ToString(), *Bone.ToString(), *GetPathNameSafe(Mesh->GetSkeletalMeshAsset()));
            }
        };
        RecordBone(TEXT("leftWrist"), Hero.LeftHandBone);
        RecordBone(TEXT("rightWrist"), Hero.RightHandBone);
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
    if (!Error.IsEmpty())
        UE_LOG(LogTemp, Error, TEXT("ENDGAME_FIXTURE_FIRST_FAILURE galleryStage=%d: %s"), GalleryStage, *Error);
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
        FVector Doorway;
        if (!GM->Hub->ServicePosition(ESSPanel::AlienGallery, Doorway))
        {
            Stop(TEXT("Current station layout has no alien gallery service anchor."));
            return;
        }
        GM->Walker->SetActorLocation(Doorway + GM->Hub->GetActorUpVector() * 110.f);
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
void ASSWave10Soak::TickWeaponReadability()
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    auto *GM = Mode.Get();
    auto *GI = GM ? GM->GetGameInstance<USSGameInstance>() : nullptr;
    if (!GI || !IsValid(GM->Ship) || FlightSeconds > 20.)
    {
        Stop(TEXT("Weapon review did not observe both real shots and confirmed hits within its bounded window."));
        return;
    }
    // Only this explicit isolated review stops the Director/target AI. Damage,
    // cooldown, projectile travel, camera, hull and weapon stats remain the real paths.
    GM->Director->SetActive(false);
    GM->Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 1.f, false, false);
    auto Next = [this]()
    {
        ++WeaponReviewStage;
        WeaponStageAt = FlightSeconds;
    };
    auto SpawnTarget = [&]()
    {
        GM->Director->ResetEncounter();
        GM->PlayerHitFlashSeconds = 0.f;
        const FVector Eye = GM->Ship->Camera->GetComponentLocation();
        const FVector Sight = (GM->Ship->CrosshairWorldPoint() - Eye).GetSafeNormal();
        auto *Target = GetWorld()->SpawnActor<ASSEnemy>(Eye + Sight * 10000.f, (-Sight).Rotation());
        if (!Target)
        {
            Stop(TEXT("Could not create the one isolated weapon review target."));
            return false;
        }
        Target->Configure(ESSWorldKind::Pursuer, 180.f, 0.f, 1);
        Target->SetActorTickEnabled(false);
        WeaponReviewTarget = Target;
        return true;
    };
    switch (WeaponReviewStage)
    {
    case -4:
        // Editor asset/shader preparation can outlive a short shot. Exercise the
        // real paths without a screenshot, then wait for preparation to settle.
        // These warmup hits are explicitly excluded from cold-first-shot evidence.
        GI->Session.run.weapon = SS::Weapon::RapidLaser;
        if (SpawnTarget())
        {
            GM->Ship->Fire();
            if (GM->PlayerHitFlashSeconds <= 0.f)
            {
                Stop(TEXT("Rapid warmup did not deal actual damage to its isolated target."));
                return;
            }
            ++WeaponWarmupShots;
            Next();
        }
        break;
    case -3:
        if (FlightSeconds - WeaponStageAt >= 1. && SpawnTarget())
        {
            GI->Session.run.weapon = SS::Weapon::HeavyCannon;
            GM->Ship->Fire();
            ++WeaponWarmupShots;
            Next();
        }
        break;
    case -2:
        if (GM->PlayerHitFlashSeconds > 0.f)
        {
            GM->Director->ResetEncounter();
            WeaponReviewTarget.Reset();
            Next();
        }
        break;
    case -1:
    {
        int32 PendingAssets = 0, PendingShaders = 0;
#if WITH_EDITOR
        PendingAssets = FAssetCompilingManager::Get().GetNumRemainingAssets();
        PendingShaders = GShaderCompilingManager ? GShaderCompilingManager->GetNumRemainingJobs() : 0;
#endif
        WeaponWarmupPeakAssets = FMath::Max(WeaponWarmupPeakAssets, PendingAssets);
        WeaponWarmupPeakShaders = FMath::Max(WeaponWarmupPeakShaders, PendingShaders);
        if (PendingAssets || PendingShaders)
            WeaponStageAt = FlightSeconds;
        else if (FlightSeconds - WeaponStageAt >= 1.)
        {
            WeaponRenderingReadyAt = FlightSeconds;
            UE_LOG(LogTemp, Display,
                   TEXT("WEAPON_REVIEW_WARMUP_READY shots=%d peakAssets=%d peakShaders=%d seconds=%.3f; "
                        "subsequent captures are warm-render evidence, not cold-first-trigger acceptance."),
                   WeaponWarmupShots, WeaponWarmupPeakAssets, WeaponWarmupPeakShaders, WeaponRenderingReadyAt);
            Next();
        }
        break;
    }
    case 0:
        GM->Director->ResetEncounter();
        Next();
        break;
    case 1:
        if (FlightSeconds >= 5. && !FScreenshotRequest::IsScreenshotRequested())
        {
            GI->Session.run.weapon = SS::Weapon::RapidLaser;
            GM->Ship->Fire();
            CaptureVisual(TEXT("RapidShot"), float(FlightSeconds));
            Next();
        }
        break;
    case 2:
        if (FlightSeconds - WeaponStageAt >= .3 && SpawnTarget())
            Next();
        break;
    case 3:
        GM->Ship->Fire();
        if (GM->PlayerHitFlashSeconds > 0.f && !FScreenshotRequest::IsScreenshotRequested())
        {
            CaptureVisual(TEXT("RapidHit"), float(FlightSeconds));
            Next();
        }
        break;
    case 4:
        if (FlightSeconds - WeaponStageAt >= 1.)
        {
            GM->Director->ResetEncounter();
            WeaponReviewTarget.Reset();
            GI->Session.run.weapon = SS::Weapon::HeavyCannon;
            GM->Ship->Fire();
            Next();
        }
        break;
    case 5:
        if (FlightSeconds - WeaponStageAt >= .08 && !FScreenshotRequest::IsScreenshotRequested())
        {
            bool HasTravellingRound = false;
            for (TActorIterator<ASSProjectile> It(GetWorld()); It; ++It)
                HasTravellingRound |= !It->IsActorBeingDestroyed();
            if (!HasTravellingRound)
            {
                Stop(TEXT("Cannon round retired before the in-flight review frame; no visual claim is possible."));
                return;
            }
            CaptureVisual(TEXT("CannonShot"), float(FlightSeconds));
            Next();
        }
        break;
    case 6:
        if (FlightSeconds - WeaponStageAt >= 1. && SpawnTarget())
        {
            GM->Ship->Fire();
            Next();
        }
        break;
    case 7:
        if (GM->PlayerHitFlashSeconds > 0.f && !FScreenshotRequest::IsScreenshotRequested())
        {
            CaptureVisual(TEXT("CannonHit"), float(FlightSeconds));
            Next();
        }
        break;
    case 8:
        if (FlightSeconds - WeaponStageAt >= 1.)
            Stop(SawFlightWave ? FString() : TEXT("Weapon review did not observe normal flight."));
        break;
    }
#endif
}
void ASSWave10Soak::TickUIRefresh(float Dt)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    auto *GM = Mode.Get();
    auto *GI = GM ? GM->GetGameInstance<USSGameInstance>() : nullptr;
    auto *PC = UGameplayStatics::GetPlayerController(this, 0);
    auto *HUD = PC ? Cast<ASSHUD>(PC->GetHUD()) : nullptr;
    if (!GI || !HUD || !NoSaveSlots() || FlightSeconds > 60.)
    {
        Stop(TEXT("UI review lost isolated state or exceeded its bounded window."));
        return;
    }
    const FString Run(UTF8_TO_TCHAR(SS::EncodeRun(GI->Session.run).c_str()));
    const FString Account(UTF8_TO_TCHAR(SS::EncodeAccount(GI->Session.account).c_str()));
    if (!Started)
    {
        MainMenuRunBefore = Run;
        MainMenuAccountBefore = Account;
        Started = true;
    }
    MainMenuStatePreserved = Run == MainMenuRunBefore && Account == MainMenuAccountBefore;
    if (!MainMenuStatePreserved)
    {
        Stop(TEXT("UI review changed the actual account or run."));
        return;
    }
    FlightSeconds += Dt;
    ++CapturedFrames;
    const ESSPanel Panels[] = {ESSPanel::Settings, ESSPanel::Graphics, ESSPanel::Audio, ESSPanel::Controls,
                               ESSPanel::Main,     ESSPanel::Wardrobe, ESSPanel::None};
    const TCHAR *Names[] = {TEXT("UIGeneral"), TEXT("UIGraphics"), TEXT("UIAudio"), TEXT("UIControls"),
                            TEXT("UIPause"),   TEXT("UIWardrobe"), TEXT("UIFlight")};
    const int32 Index = MainMenuStage / 2;
    if (Index >= UE_ARRAY_COUNT(Panels))
    {
        HUD->bReviewFlightHUD = false;
        Stop(TEXT(""));
        return;
    }
    if (MainMenuStage % 2 == 0)
    {
        GM->bAtTitleScreen = false;
        GM->bTitleSettingsNavigation = false;
        HUD->bReviewFlightHUD = Panels[Index] == ESSPanel::None;
        if (!HUD->bReviewFlightHUD)
            GM->OpenPanel(Panels[Index]);
        MainMenuStageAt = FlightSeconds;
        ++MainMenuStage;
        return;
    }
    int32 Pending = 0;
#if WITH_EDITOR
    Pending = FAssetCompilingManager::Get().GetNumRemainingAssets() +
              (GShaderCompilingManager ? GShaderCompilingManager->GetNumRemainingJobs() : 0);
#endif
    if (Pending)
        MainMenuStageAt = FlightSeconds;
    if (FlightSeconds - MainMenuStageAt < 1. || FScreenshotRequest::IsScreenshotRequested())
        return;
    if (!HUD->bReviewFlightHUD)
    {
        const auto &Bounds = HUD->GetMenuBounds();
        if (Bounds.Num() != GM->Entries.Num())
        {
            Stop(TEXT("UI frame lost native action bounds."));
            return;
        }
        for (int32 I = 0; I < Bounds.Num(); ++I)
            if (!Bounds[I].bIsValid || Bounds[I].Min.X < 0 || Bounds[I].Min.Y < 0 || Bounds[I].Max.X > 1920 ||
                Bounds[I].Max.Y > 1080 || HUD->MenuIndexAt(Bounds[I].GetCenter()) != I)
            {
                Stop(TEXT("UI frame has overlapping, offscreen or mismapped action bounds."));
                return;
            }
    }
    CaptureVisual(Names[Index], float(FlightSeconds));
    ++MainMenuStage;
#endif
}

void ASSWave10Soak::TickMainMenu(float Dt)
{
    if (FParse::Param(FCommandLine::Get(), TEXT("SSUIRefreshReview")))
    {
        TickUIRefresh(Dt);
        return;
    }
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    auto *GM = Mode.Get();
    auto *GI = GM ? GM->GetGameInstance<USSGameInstance>() : nullptr;
    auto *PC = UGameplayStatics::GetPlayerController(this, 0);
    const auto *HUD = PC ? Cast<ASSHUD>(PC->GetHUD()) : nullptr;
    if (!GI || !GM->IsTitleMenu() || GI->Session.run.active || GI->IsFreeFlight() || !NoSaveSlots() ||
        FlightSeconds > 45.)
    {
        Stop(TEXT("Title review lost the inactive startup menu, save isolation or bounded render window."));
        return;
    }
    const FString Run(UTF8_TO_TCHAR(SS::EncodeRun(GI->Session.run).c_str()));
    const FString Account(UTF8_TO_TCHAR(SS::EncodeAccount(GI->Session.account).c_str()));
    if (!Started)
    {
        MainMenuRunBefore = Run;
        MainMenuAccountBefore = Account;
        Started = true;
    }
    MainMenuStatePreserved = Run == MainMenuRunBefore && Account == MainMenuAccountBefore;
    if (!MainMenuStatePreserved)
    {
        Stop(TEXT("Title review changed account or survival state."));
        return;
    }
    ++CapturedFrames;
    FlightSeconds += Dt;
    AllFramesForeground &= FApp::HasFocus();
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Scenario, 5, ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Stage, 10, ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, SimulationDeltaMs, Dt * 1000.f, ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, TitleSelection, GM->SelectedEntry, ECsvCustomStatOp::Set);
    if (!HUD || !HUD->IsDrawingFigmaMainMenu())
    {
        MainMenuStageAt = FlightSeconds;
        return; // Missing imports must time out, never certify the fallback panel as approved art.
    }
    const int32 Actions[] = {2, 4, 5, 7};
    if (GM->Entries.Num() != 4 || HUD->GetMenuBounds().Num() != 4 || GM->Entries[0].Enabled)
    {
        Stop(TEXT("Fresh title review needs four authored bounds and disabled Continue."));
        return;
    }
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Actions); ++Index)
        if (GM->Entries[Index].Action != Actions[Index] ||
            HUD->MenuIndexAt(HUD->GetMenuBounds()[Index].GetCenter()) != Index)
        {
            Stop(TEXT("Rendered title bounds do not map to the four real menu actions."));
            return;
        }
    auto Next = [this]()
    {
        ++MainMenuStage;
        MainMenuStageAt = FlightSeconds;
    };
    if (MainMenuStage == 0)
    {
        int32 Pending = 0;
#if WITH_EDITOR
        Pending = FAssetCompilingManager::Get().GetNumRemainingAssets() +
                  (GShaderCompilingManager ? GShaderCompilingManager->GetNumRemainingJobs() : 0);
#endif
        if (Pending)
            MainMenuStageAt = FlightSeconds;
        else if (FlightSeconds - MainMenuStageAt >= 1.)
        {
            GM->SelectedEntry = INDEX_NONE;
            Next();
        }
        return;
    }
    if (FlightSeconds - MainMenuStageAt < .25 || FScreenshotRequest::IsScreenshotRequested())
        return;
    if (MainMenuStage == 2 || MainMenuStage == 4)
    {
        GM->SelectedEntry = MainMenuStage / 2; // New Game, then Settings; no action is activated.
        Next();
        return;
    }
    if (MainMenuStage == 1 || MainMenuStage == 3 || MainMenuStage == 5)
    {
        const int32 Expected = MainMenuStage == 1 ? INDEX_NONE : MainMenuStage / 2;
        if (HUD->GetFigmaMainMenuFocus() != Expected)
        {
            Stop(TEXT("Title pointer/focus state disagrees with the requested normal or focused frame."));
            return;
        }
        const TCHAR *Name = MainMenuStage == 1   ? TEXT("MainMenuNormal")
                            : MainMenuStage == 3 ? TEXT("MainMenuNewGame")
                                                 : TEXT("MainMenuSettings");
        CaptureVisual(Name, float(FlightSeconds));
        Next();
        return;
    }
    if (MainMenuStage == 6)
        Stop(TEXT(""));
#endif
}
void ASSWave10Soak::TickWalkerMotion(float Dt)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    auto *GM = Mode.Get();
    auto *PC = UGameplayStatics::GetPlayerController(this, 0);
    auto *Walker = GM ? GM->Walker.Get() : nullptr;
    auto *Movement = Walker ? Walker->GetCharacterMovement() : nullptr;
    if (!Walker || !PC || !GM->Hub || PC->GetPawn() != Walker || Walker->IsDisembarking() ||
        Walker->GetHero().Id.ToString() != RequestedWalkerId || !Movement || !Movement->IsMovingOnGround() ||
        !Movement->CurrentFloor.bBlockingHit || !GM->Hub->Walkable(Walker->GetActorLocation()) ||
        Walker->OffDeckRecoveries() != 0 || WalkerMotionSeconds > 8.)
    {
        Stop(TEXT("Requested walker motion lost the exact body, walking possession or supported deck."));
        return;
    }
    WalkerMotionSeconds += Dt;
    WalkerMotionStageSeconds += Dt;
    // Stage9 is deliberately outside the stationary-arrival CSV stages. Those
    // counters are frozen only after their original acceptance gate has passed.
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, Stage, 9, ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, SimulationDeltaMs, Dt * 1000.f, ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(SpaceSurvivalSoak, ApplicationForeground, FApp::HasFocus() ? 1 : 0, ECsvCustomStatOp::Set);
    if (WalkerMotionStage == 0)
    {
        PC->SetViewTarget(Walker);
        if (StationReviewCamera)
        {
            StationReviewCamera->Destroy();
            StationReviewCamera = nullptr;
        }
        WalkerMotionStart = Walker->GetActorLocation();
        const auto *Capsule = Walker->GetCapsuleComponent();
        const FCollisionShape Shape =
            FCollisionShape::MakeCapsule(Capsule->GetScaledCapsuleRadius(), Capsule->GetScaledCapsuleHalfHeight());
        FCollisionQueryParams Query(SCENE_QUERY_STAT(SSWalkerReviewCorridor), false, Walker);
        for (int32 Index = 0; Index < 8 && WalkerMotionDirection.IsNearlyZero(); ++Index)
        {
            const FVector Direction = FRotator(0, GM->Hub->GetActorRotation().Yaw + Index * 45.f, 0).Vector();
            FHitResult Hit;
            bool Clear =
                !GetWorld()->SweepSingleByChannel(Hit, WalkerMotionStart, WalkerMotionStart + Direction * 240.f,
                                                  FQuat::Identity, ECC_Pawn, Shape, Query) &&
                !GetWorld()->SweepSingleByChannel(Hit, WalkerMotionStart, WalkerMotionStart - Direction * 80.f,
                                                  FQuat::Identity, ECC_Pawn, Shape, Query);
            for (float Along = -80.f; Clear && Along <= 240.f; Along += 40.f)
            {
                const FVector Sample = WalkerMotionStart + Direction * Along;
                Clear = GM->Hub->Walkable(Sample) &&
                        GM->Hub->GetLandingPad()->IsOutsideParkedHull(Sample, Capsule->GetScaledCapsuleRadius()) &&
                        GetWorld()->LineTraceSingleByChannel(Hit, Sample + FVector(0, 0, 150),
                                                             Sample - FVector(0, 0, 250), ECC_Visibility, Query) &&
                        (Hit.GetActor() == GM->Hub || Hit.GetActor() == GM->Hub->GetLandingPad());
            }
            if (Clear)
                WalkerMotionDirection = Direction;
        }
        if (WalkerMotionDirection.IsNearlyZero())
        {
            Stop(TEXT("No physically clear, supported short walking corridor exists beside the actual spawn."));
            return;
        }
        PC->SetControlRotation(FRotator(-12.f, WalkerMotionDirection.Rotation().Yaw, 0));
        WalkerMotionStage = 1;
        WalkerMotionStageSeconds = 0;
        return;
    }
    if (PC->GetViewTarget() != Walker)
    {
        Stop(TEXT("Requested walker motion is not using the actual player walking camera."));
        return;
    }
    const float Along = FVector::DotProduct(Walker->GetActorLocation() - WalkerMotionStart, WalkerMotionDirection);
    WalkerMaximumTravel = FMath::Max(WalkerMaximumTravel, Along);
    if (WalkerMotionStage == 1 && WalkerMotionStageSeconds >= .35)
        WalkerMotionStage = 2;
    if (WalkerMotionStage == 2)
    {
        Walker->Move(FVector2D(0, 1), FVector2D::ZeroVector, false, Dt);
        if (Along >= 45.f && Walker->GetVelocity().Size() > 40.f)
            CaptureVisual(TEXT("WalkerOut"), float(WalkerMotionSeconds));
        if (Along >= 150.f)
        {
            WalkerTurnStartYaw = Walker->GetActorRotation().Yaw;
            WalkerMotionStage = 3;
        }
    }
    else if (WalkerMotionStage == 3)
    {
        Walker->Move(FVector2D(0, -1), FVector2D::ZeroVector, false, Dt);
        if (FMath::Abs(FMath::FindDeltaAngleDegrees(WalkerTurnStartYaw, Walker->GetActorRotation().Yaw)) >= 25.f &&
            Walker->GetVelocity().Size() > 40.f)
            CaptureVisual(TEXT("WalkerTurn"), float(WalkerMotionSeconds));
        if (Along <= 70.f && VisualNames.Contains(TEXT("WalkerTurn")) && Walker->GetVelocity().Size() > 40.f)
            CaptureVisual(TEXT("WalkerReturn"), float(WalkerMotionSeconds));
        if (Along <= 15.f)
        {
            Walker->ConsumeMovementInputVector();
            Walker->Move(FVector2D::ZeroVector, FVector2D::ZeroVector, false, Dt);
            WalkerMotionStage = 4;
            WalkerMotionStageSeconds = 0;
        }
    }
    else if (WalkerMotionStage == 4 && WalkerMotionStageSeconds >= .5)
    {
        WalkerMotionComplete = WalkerMaximumTravel >= 100.f && VisualNames.Contains(TEXT("WalkerOut")) &&
                               VisualNames.Contains(TEXT("WalkerTurn")) && VisualNames.Contains(TEXT("WalkerReturn"));
        Stop(WalkerMotionComplete ? FString() : TEXT("Requested walker did not complete all real movement frames."));
    }
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
    if (MainMenu)
    {
        TickMainMenu(Dt);
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
    if (WalkerMotionActive)
    {
        TickWalkerMotion(Dt);
        return;
    }
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
        if (WeaponReadability)
        {
            TickWeaponReadability();
            return;
        }
        const bool Turning = FlightSeconds >= 7 && FlightSeconds < 14;
        GM->Ship->SetFlightInput(Turning ? FVector2D(.16, .035) : FVector2D::ZeroVector, FVector2D::ZeroVector, 1.f,
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
        if (CaptureStationExterior && (!IsValid(GM->Hub) || !GM->Hub->IsUsingFunctionalLayout()))
        {
            Stop(TEXT("Exterior colony review requires the installed functional station reset."));
            return;
        }
        if (!IsValid(GM->Walker) || UGameplayStatics::GetPlayerPawn(this, 0) != GM->Walker)
        {
            Stop(TEXT("Station fixture did not possess the actual exit/walking pawn."));
            return;
        }
        if (!HeroKnown)
        {
            HeroKnown = true;
            HeroClimbsOut = !GM->Walker->GetHero().DisembarkClipPath.IsEmpty();
            StationHeroId = GM->Walker->GetHero().Id.ToString();
            if (!RequestedWalkerId.IsEmpty() && StationHeroId != RequestedWalkerId)
            {
                Stop(TEXT("Station selected a different body from the exact requested walker."));
                return;
            }
            UE_LOG(LogTemp, Display, TEXT("ENDGAME_FIXTURE_STATION_HERO id=%s climbsOut=%d"), *StationHeroId,
                   HeroClimbsOut ? 1 : 0);
        }
        if (Exiting)
        {
            SawExit = true;
            ExitSeconds += Dt;
        }
        else
        {
            StationIdleSeconds += Dt;
            // A hero that does not climb out has no exit footage to certify, so the pawn is the evidence
            // instead, and it is all of the evidence a working transition leaves behind: the player's own
            // walker, with the collision and the walking the exit path takes away and hands back, resting
            // its full weight on the station's own collision floor, inside the deck the station itself
            // keeps a walker on, clear of the hull the ship has just parked in, turned the way the station
            // faces, and actually on screen. A transition that had gone wrong fails at least one of these
            // - a pawn still stripped mid-exit, one falling or parked in the air at seat height, one left
            // inside the ship, one left at world north while the camera looks down the hub, one the player
            // is not even looking through.
            const auto *Movement = GM->Walker->GetCharacterMovement();
            const auto *PC = UGameplayStatics::GetPlayerController(this, 0);
            const FVector Local =
                IsValid(GM->Hub) ? GM->Hub->GetActorTransform().InverseTransformPosition(GM->Walker->GetActorLocation())
                                 : FVector::ZeroVector;
            // The body stands the way the station does. The hub carries whatever heading the ship flew in
            // on, and the walker neither orients to movement nor follows the controller, so this is the
            // clause that separates an arrival which placed the body from one that left it at identity.
            const bool Facing =
                IsValid(GM->Hub) && FMath::Abs(FMath::FindDeltaAngleDegrees(GM->Walker->GetActorRotation().Yaw,
                                                                            GM->Hub->GetActorRotation().Yaw)) <= 1.;
            const bool OnDeck =
                IsValid(GM->Hub) && Movement && Movement->MovementMode == MOVE_Walking &&
                Movement->CurrentFloor.bBlockingHit &&
                (Movement->CurrentFloor.HitResult.GetActor() == GM->Hub ||
                 Movement->CurrentFloor.HitResult.GetActor() == GM->Hub->GetLandingPad()) &&
                GM->Walker->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics &&
                // Ask the station where the hero is allowed to stand rather than repeating its envelope
                // here. This used to carry its own copy of |X| <= 1750 / |Y| <= 1450, which stopped being
                // the deck the moment arrival moved out to the exterior landing pad - and a fixture with a
                // stale copy of a boundary reports a correct arrival as a failure.
                GM->Hub->Walkable(GM->Walker->GetActorLocation()) && Local.Z > 0. &&
                GM->Hub->GetLandingPad()->IsOutsideParkedHull(
                    GM->Walker->GetActorLocation(), GM->Walker->GetCapsuleComponent()->GetScaledCapsuleRadius()) &&
                Facing;
            if (OnDeck)
            {
                SawStandingExit = true;
                DeckSeconds += Dt;
            }
            // That the player is looking through the hero's own camera is separate evidence and needs a
            // separate window, because every clause above reads the pawn: without this the whole arrival
            // could be filmed from the ship's chase camera twelve metres away and each of them would
            // still be true. It cannot be asked of the whole idle, though - the possession blend owns the
            // first fraction of a second, and from seven seconds in the fixture borrows the view for its
            // own labelled review shots and does not give it back until the run stops. So it is counted
            // over what is left, which is the stretch this fixture is actually filming the player's view.
            if (OnDeck && !IsValid(StationReviewCamera) && PC && PC->GetViewTarget() == GM->Walker)
                PlayerViewSeconds += Dt;
        }
        // Read every station frame, on both routes: being hauled back onto the deck is a failed arrival
        // whether or not the hero had a clip, and this fixture never walks the pawn anywhere, so the
        // clamp has nothing legitimate to rescue it from.
        DeckRescues = FMath::Max(DeckRescues, GM->Walker->OffDeckRecoveries());
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
                CaptureStationReview(
                    TEXT("StationServices"),
                    GM->Hub->IsUsingFunctionalLayout() ? FVector(550, 650, 210) : FVector(600, 500, 220),
                    GM->Hub->IsUsingFunctionalLayout() ? FVector(1050, 1250, 125) : FVector(1110, 1130, 160));
            if (StationIdleSeconds >= 12 && VisualNames.Contains(TEXT("StationServices")))
                CaptureStationReview(TEXT("StationOverview"),
                                     GM->Hub->IsUsingFunctionalLayout() ? FVector(-1600, -350, 390)
                                                                        : FVector(1300, -1150, 650),
                                     GM->Hub->IsUsingFunctionalLayout() ? FVector(400, 0, 120) : FVector(-600, 0, 300));
            if (CaptureStationExterior && StationIdleSeconds >= 17 && VisualNames.Contains(TEXT("StationOverview")))
                CaptureStationReview(TEXT("StationColonyOverview"), FVector(-17000, -6000, 9000),
                                     FVector(-1600, 0, 2400));
            if (CaptureStationExterior && StationIdleSeconds >= 22 &&
                VisualNames.Contains(TEXT("StationColonyOverview")))
                CaptureStationReview(TEXT("StationPadMouth"), FVector(-2000, 2200, 1000), FVector(-5200, -400, 300));
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
    // Applied after normal simulation for the next engine frame. Never relocate the ship or bypass
    // docking eligibility: the fixture presses the ordinary interaction once the pilot prompt is ready.
    if (S.run.phase != SS::Phase::Approach)
        ApproachHasLastRotation = false;
    if (Station5 && S.run.phase == SS::Phase::Approach && IsValid(GM->Hub))
    {
        // Aim above the deck: the measured parked pivot is only2.5cm above it, so flying toward that
        // point would put the hull into the rim before the ordinary docking assist can take over.
        const FVector ApproachTarget =
            GM->Hub->PadDockPosition() + GM->Hub->GetActorUpVector() * FMath::Min(1600.f, GM->GetDockingRadius() * .7f);
        const float DistanceToApproach = FVector::Distance(GM->Ship->GetActorLocation(), ApproachTarget);
        const FRotator Desired = (ApproachTarget - GM->Ship->GetActorLocation()).Rotation();
        const FRotator Current = GM->Ship->GetActorRotation();
        // Steer like a pilot, not like a thermostat. This used to be pure proportional - clamp(error/30) -
        // which converges on the kinematic hull because heading there follows the input directly. On a
        // body with inertia that is proportional control on a double integrator and it overshoots, so the
        // command is now error minus a share of the rate the ship is already turning at. The rate comes
        // from this fixture's own frame-to-frame rotation, in the same FRotator terms as the error, so the
        // damping sign cannot disagree with the error sign whatever the physics frame's convention is.
        //
        // For the record: the run that motivated this - the Phoenix at full cruise weaving across a 30 km
        // box with 45 km vertical swings - was not mostly this controller's fault. Its own SOAK_APPROACH
        // lines later showed both commands saturated for a hundred seconds with neither error closing,
        // which is a command going to the wrong axis: DriveShipCore was feeding the pitch stick to the
        // gyro's roll axis and the yaw stick to its pitch axis. Damping is still right for this body. It
        // just was not the bug.
        const float Step = FMath::Max(Dt, 1.f / 240.f);
        const float YawRate =
            ApproachHasLastRotation ? FMath::FindDeltaAngleDegrees(ApproachLastRotation.Yaw, Current.Yaw) / Step : 0.f;
        const float PitchRate = ApproachHasLastRotation
                                    ? FMath::FindDeltaAngleDegrees(ApproachLastRotation.Pitch, Current.Pitch) / Step
                                    : 0.f;
        ApproachLastRotation = Current;
        ApproachHasLastRotation = true;
        const float Kp = 1.f / 40.f, Kd = .015f;
        const FVector2D Steering(
            FMath::Clamp(FMath::FindDeltaAngleDegrees(Current.Yaw, Desired.Yaw) * Kp - YawRate * Kd, -.75f, .75f),
            FMath::Clamp(FMath::FindDeltaAngleDegrees(Current.Pitch, Desired.Pitch) * Kp - PitchRate * Kd, -.75f,
                         .75f));
        // Absolute throttle and brake feedback keep the scripted pilot moving
        // toward its waypoint without reintroducing the removed idle-thrust floor.
        const float WantedSpeed = DistanceToApproach < 300.f
                                      ? 0.f
                                      : FMath::Min(float(S.Stats().speed), FMath::Max(250.f, DistanceToApproach * .5f));
        const float ActualSpeed = GM->Ship->GetVelocity().Size();
        const float Throttle = FMath::Clamp(WantedSpeed / FMath::Max(1.f, float(S.Stats().speed)), 0.f, 1.f);
        GM->Ship->SetFlightInput(Steering, FVector2D::ZeroVector, Throttle, false, ActualSpeed > WantedSpeed + 50.f);
        FString DockingMessage;
        if (!RequestedDocking && GM->DockingStatus(DockingMessage))
        {
            GM->Interact();
            RequestedDocking = S.run.phase == SS::Phase::Docking;
            UE_LOG(LogTemp, Display, TEXT("SOAK_DOCK_REQUEST path=GameModeInteract accepted=%d"),
                   RequestedDocking ? 1 : 0);
        }
        // Diagnostic, once a second: where the ship is relative to the pad, whether its body is simulating,
        // how fast it is really going, the heading error and the command, whether admission's clearance
        // would pass, and - if the clearance sweep is blocked - by what. Fixture-only; nothing here touches
        // the ship. It exists because two Phoenix runs failed two different ways and the CSV only carries
        // the camera, so the ship's own state was being inferred rather than read.
        if (ApproachSeconds >= NextApproachLog)
        {
            NextApproachLog = ApproachSeconds + 1.0;
            const FVector Local = GM->Hub->GetActorTransform().InverseTransformPosition(GM->Ship->GetActorLocation());
            const FVector Dock = GM->Hub->PadDockPosition();
            const bool Sim = GM->Ship->Collision && GM->Ship->Collision->IsSimulatingPhysics();
            const FVector PhysV = Sim ? GM->Ship->Collision->GetPhysicsLinearVelocity() : FVector::ZeroVector;
            FHitResult Block;
            FCollisionQueryParams Q(SCENE_QUERY_STAT(SSSoakApproachProbe), false, GM->Ship);
            const bool Blocked =
                GM->Ship->SweepFlightHull(Block, GM->Ship->GetActorLocation(),
                                          Dock + GM->Hub->GetActorUpVector() * 700.f, GM->Ship->GetActorQuat(), Q);
            UE_LOG(LogTemp, Display,
                   TEXT("SOAK_APPROACH t=%.0f local=(%.0f,%.0f,%.0f) toDock=%.0f radius=%.0f speed=%.0f physV=%.0f "
                        "sim=%d yawErr=%.1f pitchErr=%.1f steer=(%.2f,%.2f) assist=%d "
                        "compoundHoverProbeBlocked=%d by=%s/%s toApproach=%.0f status=%s"),
                   ApproachSeconds, Local.X, Local.Y, Local.Z, FVector::Dist(GM->Ship->GetActorLocation(), Dock),
                   GM->GetDockingRadius(), GM->Ship->GetVelocity().Size(), PhysV.Size(), Sim ? 1 : 0,
                   FMath::FindDeltaAngleDegrees(Current.Yaw, Desired.Yaw),
                   FMath::FindDeltaAngleDegrees(Current.Pitch, Desired.Pitch), Steering.X, Steering.Y,
                   GM->Hub->CanAssistDocking(GM->Ship) ? 1 : 0, Blocked ? 1 : 0,
                   Blocked && Block.GetActor() ? *Block.GetActor()->GetName() : TEXT("-"),
                   Blocked && Block.GetComponent() ? *Block.GetComponent()->GetName() : TEXT("-"), DistanceToApproach,
                   *DockingMessage);
        }
    }
    else if (!Station5 || (S.run.phase != SS::Phase::Docking && S.run.phase != SS::Phase::Station))
    {
        const double Cycle = FMath::Fmod(FlightSeconds, 12.0);
        GM->Ship->SetFlightInput(
            FVector2D::ZeroVector,
            FVector2D(.12 * FMath::Sin(FlightSeconds * .35), .08 * FMath::Cos(FlightSeconds * .35)), 1.f, Cycle < 2.0,
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
    else if (Station5 && StationIdleSeconds >= (CaptureStationExterior ? 25 : 15))
    {
        // Getting off the ship is certified two ways, and the hero decides which one this run owes. One
        // with an exit clip owes the climb-out itself: 2.3 s of a running transition, which is what the
        // Exit0..6 frames are shots of. One with none owes the same arrival without the animation - the
        // docking motion really ran, and it really ended with the player standing on the deck in control
        // for as long as the climb-out would have taken. Neither may be paid with the other's evidence:
        // a hero with no clip that somehow started a transition is a fault, not a pass, and a hero with a
        // clip cannot certify by standing still. Docking itself is demanded in both, so a run that
        // skipped the arrival and spawned a walker on the deck certifies nothing.
        const bool Arrived = RequestedDocking && SawDocking && DockingSeconds >= 2.9;
        const bool ClimbedOut = HeroClimbsOut && SawExit && ExitSeconds >= 2.3;
        // The standing arrival is owed for the whole window, not a slice of it. The climb-out branch
        // above cannot be paid by a self-correction because its 2.3 s has to come out of a 2.4 s stage;
        // a bare 2.3 s of deck out of fifteen could be, since the walker's own Tick hauls a pawn that
        // is off the deck back to the spawn and sets it walking again, which rebuilds every clause of
        // the evidence. So the deck has to hold for all of the window bar a settle budget, and the
        // rescue counter has to be nought - together those refuse an arrival that was ever wrong, as
        // well as one that was wrong and got quietly fixed.
        const bool StoodOutside = !HeroClimbsOut && !SawExit && SawStandingExit && DeckSeconds >= 2.3 &&
                                  DeckSeconds >= StationIdleSeconds - 1.5 && PlayerViewSeconds >= 2.3;
        const bool Covered = SawFlightWave && SawBreathing && SawWormhole && WormholeSeconds >= 7.9 && SawClimax &&
                             ClimaxSeconds >= 39.5 && SawApproach && ApproachSeconds > 0 && Arrived && HeroKnown &&
                             DeckRescues == 0 && (ClimbedOut || StoodOutside);
        if (Covered && !RequestedWalkerId.IsEmpty())
        {
            WalkerMotionActive = true;
            return;
        }
        Stop(Covered ? FString()
                     : FString::Printf(
                           TEXT("Required complete Wave 5, wormhole, docking or arrival coverage was not observed: "
                                "hero=%s climbsOut=%d wave5=%d breathing=%d wormhole=%d/%.2f climax=%d/%.2f "
                                "approach=%d/%.2f docking=%d/%.2f exit=%d/%.2f standingOnDeck=%d/%.2f of %.2f "
                                "playerView=%.2f deckRescues=%d"),
                           StationHeroId.IsEmpty() ? TEXT("none") : *StationHeroId, HeroClimbsOut ? 1 : 0,
                           SawFlightWave ? 1 : 0, SawBreathing ? 1 : 0, SawWormhole ? 1 : 0, WormholeSeconds,
                           SawClimax ? 1 : 0, ClimaxSeconds, SawApproach ? 1 : 0, ApproachSeconds, SawDocking ? 1 : 0,
                           DockingSeconds, SawExit ? 1 : 0, ExitSeconds, SawStandingExit ? 1 : 0, DeckSeconds,
                           StationIdleSeconds, PlayerViewSeconds, DeckRescues));
    }
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
    if (CaptureVisuals && Failure.IsEmpty())
    {
        TArray<FString> Expected;
        if (MainMenu && FParse::Param(FCommandLine::Get(), TEXT("SSUIRefreshReview")))
            Expected = {TEXT("UIGeneral"), TEXT("UIGraphics"), TEXT("UIAudio"), TEXT("UIControls"),
                        TEXT("UIPause"),   TEXT("UIWardrobe"), TEXT("UIFlight")};
        else if (MainMenu)
            Expected = {TEXT("MainMenuNormal"), TEXT("MainMenuNewGame"), TEXT("MainMenuSettings")};
        else if (Gallery)
            Expected = {TEXT("GalleryDoorway"), TEXT("GalleryShowcase"), TEXT("GalleryAssets"), TEXT("GalleryReturn")};
        else if (Station5)
        {
            Expected = {TEXT("Flight"), TEXT("Climax"), TEXT("Wormhole"), TEXT("Approach"), TEXT("Docking")};
            // The seven exit frames are shots of a climb-out, so they are owed only by a run that had one.
            // A hero with no exit clip never enters that stage, and demanding its frames would be asking
            // for pictures of an animation the owner cancelled; the station frames below are its arrival.
            if (HeroClimbsOut)
                for (int32 Index = 0; Index < 7; ++Index)
                    Expected.Add(FString::Printf(TEXT("Exit%d"), Index));
            Expected.Append(
                {TEXT("StationIdle"), TEXT("StationServices"), TEXT("StationOverview"), TEXT("CombatImpact")});
            if (CaptureStationExterior)
                Expected.Append({TEXT("StationColonyOverview"), TEXT("StationPadMouth")});
            if (!RequestedWalkerId.IsEmpty())
                Expected.Append({TEXT("WalkerOut"), TEXT("WalkerTurn"), TEXT("WalkerReturn")});
        }
        else if (WeaponReadability)
            Expected = {TEXT("RapidShot"), TEXT("RapidHit"), TEXT("CannonShot"), TEXT("CannonHit")};
        else if (Wave1)
            Expected = {TEXT("Cruise"), TEXT("Turn"), TEXT("Boost"), TEXT("Brake")};
        else
            Expected = {TEXT("Flight"), TEXT("Climax"), TEXT("Compound"), TEXT("Approach")};
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
    if (Failure.IsEmpty() && Gallery && (!GalleryRunPreserved || !GalleryReturned))
        Failure = TEXT("Gallery return/session checks failed.");
    if (Failure.IsEmpty() && MainMenu && !MainMenuStatePreserved)
        Failure = TEXT("Title menu account/session preservation failed.");
    const FString Csv = CaptureResult.Get();
    const bool Success =
        Failure.IsEmpty() && SlotsUntouched && !Csv.IsEmpty() && (AllFramesForeground || OffscreenVisuals);
    auto Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("evidenceType"), FParse::Param(FCommandLine::Get(), TEXT("SSUIRefreshReview"))
                                                     ? TEXT("UI_REFRESH_RENDERED_REVIEW")
                                                 : MainMenu          ? TEXT("TITLE_MENU_RENDERED_REVIEW")
                                                 : Gallery           ? TEXT("ALIEN_GALLERY_SCRIPTED_VISUAL_REVIEW")
                                                 : WeaponReadability ? TEXT("WEAPON_READABILITY_SCRIPTED_NORMAL_STATS")
                                                 : Wave1             ? TEXT("WAVE1_VISUAL_ONLY_SCRIPTED_NORMAL_STATS")
                                                 : Station5 ? TEXT("RENDERED_TRANSITION_FIXTURE_NOT_NATURAL_GAMEPLAY")
                                                            : TEXT("RENDERED_ENDGAME_FIXTURE_NOT_NATURAL_GAMEPLAY"));
    Result->SetBoolField(TEXT("success"), Success);
    Result->SetBoolField(TEXT("visualCaptureEnabled"), CaptureVisuals);
    Result->SetBoolField(TEXT("stationExteriorReview"), CaptureStationExterior);
    Result->SetBoolField(TEXT("weaponReadabilityReview"), WeaponReadability);
    Result->SetBoolField(TEXT("mainMenuReview"), MainMenu);
    Result->SetBoolField(TEXT("uiRefreshReview"), FParse::Param(FCommandLine::Get(), TEXT("SSUIRefreshReview")));
    Result->SetBoolField(TEXT("mainMenuStatePreserved"), MainMenuStatePreserved);
    if (WeaponReadability)
    {
        Result->SetNumberField(TEXT("weaponUncapturedWarmupShots"), WeaponWarmupShots);
        Result->SetNumberField(TEXT("weaponRenderingReadyAtSeconds"), WeaponRenderingReadyAt);
        Result->SetNumberField(TEXT("weaponWarmupPeakPendingAssets"), WeaponWarmupPeakAssets);
        Result->SetNumberField(TEXT("weaponWarmupPeakPendingShaders"), WeaponWarmupPeakShaders);
        Result->SetStringField(TEXT("weaponWarmupLimit"),
                               TEXT("Two uncaptured real shots/hits prepare rendering before the four review frames. "
                                    "No cold first-trigger or packaged readiness acceptance is inferred."));
    }
    Result->SetArrayField(TEXT("visualRequests"), VisualRecords);
    Result->SetStringField(
        TEXT("visualCaptureLimit"),
        TEXT("Viewport screenshots are fulfilled after each recorded request. Station review shots use labeled "
             "fixture cameras without changing possession, runtime lighting or exposure settings. Image readback "
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
    Result->SetStringField(TEXT("scenario"), MainMenu   ? TEXT("MainMenu")
                                             : Gallery  ? TEXT("Gallery")
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
    Result->SetBoolField(TEXT("requestedDocking"), RequestedDocking);
    Result->SetStringField(TEXT("dockInputPath"), TEXT("Scripted GameMode.Interact; not physical controller input"));
    Result->SetBoolField(TEXT("sawAuthoredExit"), SawExit);
    Result->SetStringField(TEXT("stationHero"), StationHeroId);
    Result->SetStringField(TEXT("requestedWalker"), RequestedWalkerId);
    Result->SetBoolField(TEXT("walkerMotionComplete"), WalkerMotionComplete);
    Result->SetNumberField(TEXT("walkerMotionSeconds"), WalkerMotionSeconds);
    Result->SetNumberField(TEXT("walkerMaximumTravelCm"), WalkerMaximumTravel);
    if (!RequestedWalkerId.IsEmpty())
        Result->SetStringField(
            TEXT("walkerMotionLimit"),
            TEXT("Exact requested walker in player camera. Scripted short out/turn/return on a physically probed "
                 "corridor; no pawn teleport or camera actor. Appended after the original stationary gate. "
                 "Motion is CSV Stage9 and is excluded from stationary arrival counters; no natural input claim."));
    Result->SetBoolField(TEXT("heroClimbsOut"), HeroClimbsOut);
    Result->SetBoolField(TEXT("sawStandingExit"), SawStandingExit);
    Result->SetNumberField(TEXT("standingOnDeckSeconds"), DeckSeconds);
    Result->SetNumberField(TEXT("offDeckRescues"), DeckRescues);
    Result->SetNumberField(TEXT("playerViewOnDeckSeconds"), PlayerViewSeconds);
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
    if (MainMenu)
        Result->SetStringField(TEXT("fixture"),
                               TEXT("Fresh inactive startup title, exact imported Figma textures required. "
                                    "Synthetic no-selection/NewGame/Settings focus; real rendered button centers "
                                    "must hit their existing actions. No StartRun, activation, OS pointer movement, "
                                    "save API, physical input or performance acceptance."));
    else if (Gallery)
        Result->SetStringField(
            TEXT("fixture"), TEXT("Fresh isolated home hangar; scripted walker placement at real service, ordinary "
                                  "interaction, full vendor showcase, asset layout, return. Exact run/account and "
                                  "return transform checked. No save APIs, natural input or performance acceptance."));
    else if (WeaponReadability)
        Result->SetStringField(
            TEXT("fixture"),
            TEXT("Normal fresh Wave1 starter stats, TierI, no utility or durability override. Scripted straight "
                 "powered flight through the normal chase camera; both weapons selected in fixture memory and "
                 "fired through Ship.Fire. One normal-health Pursuer target at a time; target AI and Director "
                 "paused for this isolated shot review. Hit frames require actual damage feedback. No unlock, "
                 "physical input, natural combat/balance, audio or performance acceptance."));
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
                 "Wave5, 8s wormhole,40s climax, ordinary bounded steering to port, actual docking and15s "
                 "stationary hub. Arrival is certified against the hero that was possessed: a hero with an exit "
                 "clip owes 2.3s of authored climb-out and its Exit0..6 frames; a hero with none (RPT-20260917-01) "
                 "owes 2.3s standing on the station's own collision floor, on the deck, clear of the docked hull, "
                 "with collision and walking restored, and films no exit. No forced docking/teleport, menu "
                 "purchases, physical input, natural progression/balance or representative FPS acceptance."));
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
