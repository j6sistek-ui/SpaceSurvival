#include "SSAlienGallery.h"
#include "SSGameMode.h"
#include "SSGameInstance.h"
#include "SSStation.h"
#include "SSWave10Soak.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/AudioComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Level.h"
#include "Engine/LevelStreamingDynamic.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/HUD.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/PlatformTime.h"
#include "HAL/IConsoleManager.h"
#include "Misc/PackageName.h"

ASSGalleryCamera::ASSGalleryCamera()
{
    auto *View = CreateDefaultSubobject<UCameraComponent>(TEXT("GalleryView"));
    RootComponent = View;
    View->FieldOfView = 80.f;
    SetActorEnableCollision(false);
    PrimaryActorTick.bCanEverTick = false;
}
void ASSGalleryCamera::Drive(APlayerController *PC, float Dt)
{
    if (!PC)
        return;
    auto Down = [PC](FKey Key) { return PC->IsInputKeyDown(Key) ? 1.f : 0.f; };
    float MX = 0, MY = 0;
    PC->GetInputMouseDelta(MX, MY);
    FRotator Facing = GetActorRotation();
    Facing.Yaw += MX * .15f + PC->GetInputAnalogKeyState(EKeys::Gamepad_RightX) * 80.f * Dt;
    Facing.Pitch = FMath::Clamp(
        Facing.Pitch + MY * .15f + PC->GetInputAnalogKeyState(EKeys::Gamepad_RightY) * 80.f * Dt, -89.f, 89.f);
    SetActorRotation(Facing);
    const float Forward = Down(EKeys::W) - Down(EKeys::S) + PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftY);
    const float Side = Down(EKeys::D) - Down(EKeys::A) + PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftX);
    const float Up =
        Down(EKeys::E) - Down(EKeys::Q) + Down(EKeys::Gamepad_RightShoulder) - Down(EKeys::Gamepad_LeftShoulder);
    const FVector Direction =
        (GetActorForwardVector() * Forward + GetActorRightVector() * Side + FVector::UpVector * Up)
            .GetClampedToMaxSize(1.f);
    const bool Fast = Down(EKeys::LeftShift) || PC->GetInputAnalogKeyState(EKeys::Gamepad_RightTriggerAxis) > .3f;
    const bool Slow = Down(EKeys::LeftControl) || PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftTriggerAxis) > .3f;
    AddActorWorldOffset(Direction * TravelSpeed * (Slow ? .15f : Fast ? 5.f : 1.f) * FMath::Min(Dt, .1f), false);
}
USSAlienGallery::USSAlienGallery()
{
    PrimaryComponentTick.bCanEverTick = false;
}
const TCHAR *USSAlienGallery::MapPath(bool Assets)
{
    return Assets ? TEXT("/Game/Megastructure_Scifi_World/Level/L_assets")
                  : TEXT("/Game/Megastructure_Scifi_World/Level/L_Showcase_level");
}
bool USSAlienGallery::Enter(APlayerController *PC, bool Assets)
{
    auto *GI = GetWorld() ? GetWorld()->GetGameInstance<USSGameInstance>() : nullptr;
    auto *Walker = PC ? Cast<ASSWalker>(PC->GetPawn()) : nullptr;
    if (IsActive())
    {
        UE_LOG(LogTemp, Warning, TEXT("ALIEN_GALLERY_ENTER_REJECTED reason=AlreadyActive"));
        return false;
    }
    if (!GI || !Walker)
    {
        UE_LOG(LogTemp, Warning, TEXT("ALIEN_GALLERY_ENTER_REJECTED reason=%s"),
               GI ? TEXT("NoWalkerPawn") : TEXT("NoGameInstance"));
        return false;
    }
    if (Walker->IsDisembarking())
    {
        UE_LOG(LogTemp, Warning, TEXT("ALIEN_GALLERY_ENTER_REJECTED reason=Disembarking"));
        return false;
    }
    if (GI->Session.run.phase != SS::Phase::Hangar && GI->Session.run.phase != SS::Phase::Station)
    {
        UE_LOG(LogTemp, Warning, TEXT("ALIEN_GALLERY_ENTER_REJECTED reason=WrongPhase phase=%d"),
               static_cast<int32>(GI->Session.run.phase));
        return false;
    }
    if (!FPackageName::DoesPackageExist(MapPath(Assets)))
    {
        UE_LOG(LogTemp, Warning, TEXT("ALIEN_GALLERY_ENTER_REJECTED reason=MapMissing map=%s"), MapPath(Assets));
        if (auto *GM = Cast<ASSGameMode>(GetOwner()))
            GM->Announce(TEXT("Alien gallery unavailable: install the owned Megastructure Sci-Fi World maps."));
        return false;
    }
    Controller = PC;
    ReturnPawn = Walker;
    ReturnTransform = Walker->GetActorTransform();
    ReturnRotation = PC->GetControlRotation();
    bAssets = Assets;
    bSwitchAfterUnload = false;
    if (!StartLoad())
        return false;
    if (auto *GM = Cast<ASSGameMode>(GetOwner()))
        GM->ClosePanel();
    SuspendScene();
    return true;
}
bool USSAlienGallery::StartLoad()
{
    bool Success = false;
    Level = ULevelStreamingDynamic::LoadLevelInstance(this, MapPath(bAssets), FVector::ZeroVector,
                                                      FRotator::ZeroRotator, Success);
    if (!Success || !Level)
    {
        UE_LOG(LogTemp, Error, TEXT("ALIEN_GALLERY_LOAD_FAILED map=%s"), MapPath(bAssets));
        return false;
    }
    Level->SetShouldBeVisible(false);
    State = EState::Loading;
    LoadStarted = FPlatformTime::Seconds();
    return true;
}
void USSAlienGallery::SuspendScene()
{
    // Exact state restoration includes lights/fog and component ticks: hidden actors alone do not isolate lighting.
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        AActor *Actor = *It;
        if (Actor == GetOwner() || Actor->IsA<ASSWave10Soak>() || Actor->IsA<AController>() || Actor->IsA<AHUD>() ||
            Actor->IsA<APlayerCameraManager>() || Actor->IsA<AWorldSettings>())
            continue;
        auto *PostProcess = Cast<APostProcessVolume>(Actor);
        Actors.Add({Actor, Actor->IsHidden(), Actor->GetActorEnableCollision(), Actor->IsActorTickEnabled(),
                    PostProcess && PostProcess->bEnabled});
        if (PostProcess)
            PostProcess->bEnabled = false;
        Actor->SetActorHiddenInGame(true);
        Actor->SetActorEnableCollision(false);
        Actor->SetActorTickEnabled(false);
        TInlineComponentArray<UActorComponent *> All;
        Actor->GetComponents(All);
        for (auto *C : All)
        {
            auto *Scene = Cast<USceneComponent>(C);
            auto *Audio = Cast<UAudioComponent>(C);
            Components.Add({C, C->IsComponentTickEnabled(), Scene && Scene->IsVisible(), Audio && Audio->bIsPaused});
            C->SetComponentTickEnabled(false);
            if (Scene)
                Scene->SetVisibility(false, false);
            if (Audio)
                Audio->SetPaused(true);
        }
    }
    // GameMode owns the music and Director, which must not advance during review.
    TInlineComponentArray<UActorComponent *> Owned;
    GetOwner()->GetComponents(Owned);
    for (auto *C : Owned)
    {
        if (C == this)
            continue;
        auto *Audio = Cast<UAudioComponent>(C);
        Components.Add({C, C->IsComponentTickEnabled(), false, Audio && Audio->bIsPaused});
        C->SetComponentTickEnabled(false);
        if (Audio)
            Audio->SetPaused(true);
    }
}
void USSAlienGallery::RestoreScene()
{
    for (const auto &S : Actors)
        if (auto *Actor = S.Actor.Get())
        {
            Actor->SetActorHiddenInGame(S.Hidden);
            Actor->SetActorEnableCollision(S.Collision);
            Actor->SetActorTickEnabled(S.Tick);
            if (auto *PostProcess = Cast<APostProcessVolume>(Actor))
                PostProcess->bEnabled = S.PostProcessEnabled;
        }
    for (const auto &S : Components)
        if (auto *C = S.Component.Get())
        {
            C->SetComponentTickEnabled(S.Tick);
            if (auto *Scene = Cast<USceneComponent>(C); Scene && C->GetOwner() != GetOwner())
                Scene->SetVisibility(S.Visible, false);
            if (auto *Audio = Cast<UAudioComponent>(C))
                Audio->SetPaused(S.AudioPaused);
        }
    Actors.Reset();
    Components.Reset();
    if (auto *PC = Controller.Get(); PC && ReturnPawn.IsValid())
    {
        ReturnPawn->SetActorTransform(ReturnTransform);
        PC->Possess(ReturnPawn.Get());
        PC->SetControlRotation(ReturnRotation);
        PC->SetViewTarget(ReturnPawn.Get());
        PC->bShowMouseCursor = false;
        PC->SetInputMode(FInputModeGameOnly());
    }
    if (Camera)
        Camera->Destroy();
    Camera = nullptr;
    Level = nullptr;
    State = EState::Closed;
}
FTransform USSAlienGallery::FindInitialView() const
{
    // Inspected full-scene overview, outside the architecture rather than inside its origin.
    if (!bAssets)
    {
        const FVector Eye(35000, -20000, 26000);
        return FTransform((FVector(0, 14000, 0) - Eye).Rotation(), Eye);
    }
    if (!Level || !Level->GetLoadedLevel())
        return FTransform(FVector(0, 0, 3000));
    FBox Bounds(ForceInit);
    for (AActor *Actor : Level->GetLoadedLevel()->Actors)
    {
        if (!IsValid(Actor))
            continue;
        // Demo cameras/starts can face empty grid floor. Frame the actual modular
        // inventory regardless of those editor presentation helpers.
        TInlineComponentArray<UStaticMeshComponent *> Meshes;
        Actor->GetComponents(Meshes);
        for (auto *Mesh : Meshes)
            if (Mesh->GetStaticMesh() &&
                Mesh->GetStaticMesh()->GetPathName().StartsWith(TEXT("/Game/Megastructure_Scifi_World/")) &&
                !Mesh->GetStaticMesh()->GetPathName().Contains(TEXT("/Sky_system/")) &&
                !Mesh->GetStaticMesh()->GetPathName().Contains(TEXT("/Meshes/Demo/")))
                Bounds += Mesh->Bounds.GetBox();
    }
    if (!Bounds.IsValid)
        return FTransform(FVector(0, 0, 3000));
    const FVector Center = Bounds.GetCenter();
    const float Radius = FMath::Clamp(float(Bounds.GetExtent().Size()), 1000.f, 500000.f);
    const FVector Eye = Center + FVector(-1.5f, -1.f, .65f) * Radius;
    return FTransform((Center - Eye).Rotation(), Eye);
}
void USSAlienGallery::ResetView()
{
    if (Camera && IsReady())
        Camera->SetActorTransform(InitialView);
}
void USSAlienGallery::SwitchScene()
{
    if (!IsReady())
        return;
    if (!FPackageName::DoesPackageExist(MapPath(!bAssets)))
        return;
    bSwitchAfterUnload = true;
    State = EState::Unloading;
    Level->SetShouldBeVisible(false);
    Level->SetShouldBeLoaded(false);
    Level->SetIsRequestingUnloadAndRemoval(true);
}
void USSAlienGallery::Leave()
{
    if (!IsActive())
        return;
    UE_LOG(LogTemp, Display, TEXT("ALIEN_GALLERY_LEAVE state=%d assets=%d controller=%d camera=%d age=%.3f"),
           int32(State), bAssets, Controller.IsValid(), IsValid(Camera), FPlatformTime::Seconds() - LoadStarted);
    bSwitchAfterUnload = false;
    State = EState::Unloading;
    if (Level)
    {
        Level->SetShouldBeVisible(false);
        Level->SetShouldBeLoaded(false);
        Level->SetIsRequestingUnloadAndRemoval(true);
    }
    else
        RestoreScene();
}
void USSAlienGallery::Update(float Dt)
{
    if (State == EState::Loading)
    {
        if (Level && Level->IsLevelLoaded())
        {
            Level->SetShouldBeVisible(true);
            if (!Level->IsLevelVisible())
            {
                if (FPlatformTime::Seconds() - LoadStarted > 90.)
                    Leave();
                return;
            }
            // The vendor demo stores EV exposure bounds. With this project's non-extended
            // luminance setting those negative bounds produce invalid/all-white exposure.
            // Convert only the streamed instance, preserving the authored source packages.
            const auto *Extended = IConsoleManager::Get().FindConsoleVariable(
                TEXT("r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange"));
            if (Extended && Extended->GetInt() == 0)
                for (AActor *Actor : Level->GetLoadedLevel()->Actors)
                    if (auto *PP = Cast<APostProcessVolume>(Actor); PP && PP->Settings.AutoExposureMinBrightness <= 0.f)
                    {
                        PP->Settings.AutoExposureMinBrightness =
                            FMath::Pow(2.f, PP->Settings.AutoExposureMinBrightness);
                        PP->Settings.AutoExposureMaxBrightness =
                            FMath::Max(PP->Settings.AutoExposureMinBrightness,
                                       FMath::Pow(2.f, PP->Settings.AutoExposureMaxBrightness));
                    }
            InitialView = FindInitialView();
            if (!Camera)
                Camera = GetWorld()->SpawnActor<ASSGalleryCamera>(InitialView.GetLocation(), InitialView.Rotator());
            if (!Camera || !Controller.IsValid())
            {
                UE_LOG(LogTemp, Error, TEXT("ALIEN_GALLERY_VIEW_FAILED camera=%d controller=%d"), IsValid(Camera),
                       Controller.IsValid());
                Leave();
                return;
            }
            Camera->SetActorTransform(InitialView);
            Camera->TravelSpeed = bAssets ? 2000.f : 12000.f;
            Controller->Possess(Camera);
            Controller->SetViewTarget(Camera);
            State = EState::Viewing;
        }
        if (State == EState::Loading && FPlatformTime::Seconds() - LoadStarted > 90.)
        {
            if (auto *GM = Cast<ASSGameMode>(GetOwner()))
                GM->Announce(TEXT("Alien gallery timed out while loading. Returning to the station."));
            Leave();
        }
    }
    if (State == EState::Unloading && (!Level || !Level->IsLevelLoaded()))
    {
        if (bSwitchAfterUnload)
        {
            Level = nullptr;
            bAssets = !bAssets;
            bSwitchAfterUnload = false;
            if (!StartLoad())
                RestoreScene();
        }
        else
            RestoreScene();
    }
}
FString USSAlienGallery::Status() const
{
    if (State == EState::Closed)
        return TEXT("Alien gallery closed / station active");
    if (State == EState::Loading)
        return TEXT("Loading full alien scene... Esc / B cancels");
    if (State == EState::Unloading)
        return TEXT("Leaving scene / restoring station...");
    return bAssets ? TEXT("ALIEN ASSET GALLERY / evaluation only / run frozen")
                   : TEXT("ALIEN WORLD / full vendor showcase / evaluation only / run frozen");
}
void USSAlienGallery::EndPlay(const EEndPlayReason::Type Reason)
{
    if (Level)
        Level->SetIsRequestingUnloadAndRemoval(true);
    if (IsActive())
        RestoreScene();
    Super::EndPlay(Reason);
}
