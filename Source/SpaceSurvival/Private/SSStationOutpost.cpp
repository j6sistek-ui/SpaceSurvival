#include "SSStation.h"
#include "SSLandingPad.h"
#include "SSOutpostSandbox.h"
#include "SSAudio.h"
#include "SSGameMode.h"
#include "Components/AudioComponent.h"
#include "Components/LightComponent.h"
#include "Components/LightComponentBase.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/Level.h"
#include "Engine/LevelStreamingDynamic.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/SkyLight.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Misc/CommandLine.h"
#include "Misc/PackageName.h"
#include "Misc/Parse.h"
#include "Sound/SoundBase.h"

namespace
{
const TCHAR *SSOutpostRuntimeMap = TEXT("/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime");
FString OutpostLabel(const AActor *Actor)
{
    for (const FName Tag : Actor->Tags)
    {
        const FString Value = Tag.ToString();
        if (Value.StartsWith(TEXT("OutpostLabel:")))
            return Value.Mid(13);
    }
    return FString();
}
void SetOutpostLight(ULightComponentBase *Component, float Intensity)
{
    if (auto *Sky = Cast<USkyLightComponent>(Component))
        Sky->SetIntensity(Intensity);
    else if (auto *Light = Cast<ULightComponent>(Component))
        Light->SetIntensity(Intensity);
}
} // namespace

bool ASSStation::IsUsingOutpost() const
{
    return OutpostLevel && OutpostLevel->GetLoadedLevel();
}

bool ASSStation::BuildOutpostHub()
{
    // The runtime station belongs to the real game. Pure actor fixtures and the old authoring Workshop
    // retain their small native station; loading a city merely to inspect one pad is not useful.
    if (!bUseLicensedPresentation || !bUseEditableLayout || !GetWorld()->GetAuthGameMode<ASSGameMode>() ||
        FParse::Param(FCommandLine::Get(), TEXT("SSLegacyStation")))
        return false;
    if (!FPackageName::DoesPackageExist(SSOutpostRuntimeMap))
    {
        UE_LOG(LogTemp, Warning, TEXT("SS_OUTPOST_FALLBACK missing runtime map %s; using legacy station"),
               SSOutpostRuntimeMap);
        return false;
    }
    bool Loaded = false;
    OutpostLevel = ULevelStreamingDynamic::LoadLevelInstance(this, SSOutpostRuntimeMap, GetActorLocation(),
                                                             GetActorRotation(), Loaded);
    if (Loaded && OutpostLevel)
    {
        // BuildHub's callers immediately place the ship/pilot. Finish the authored level and its apartment
        // instance before exposing the station as usable; never let a pilot fall through pending geometry.
        OutpostLevel->SetShouldBeLoaded(true);
        OutpostLevel->SetShouldBeVisible(true);
        GetWorld()->FlushLevelStreaming(EFlushLevelStreamingType::Full);
    }
    ULevel *Level = OutpostLevel ? OutpostLevel->GetLoadedLevel() : nullptr;
    if (!Loaded || !Level)
    {
        UE_LOG(LogTemp, Warning, TEXT("SS_OUTPOST_FALLBACK failed to stream authored station; using legacy station"));
        DestroyOutpostHub();
        return false;
    }
    UStaticMeshComponent *PadDeck = nullptr;
    TArray<TWeakObjectPtr<AActor>> PresentationShips;
    const TArray<TObjectPtr<AActor>> Actors = Level->Actors;
    for (AActor *Actor : Actors)
    {
        if (!IsValid(Actor))
            continue;
        const FString Label = OutpostLabel(Actor);
        if (Label == TEXT("Ground/Player berth"))
            PadDeck = Actor->FindComponentByClass<UStaticMeshComponent>();
        if (Label.StartsWith(TEXT("Berth/Access/")))
        {
            // These stationary ramp/cabin proxies belong to the display hull. The real ASSShip already
            // supplies its own moving boarding surfaces; retaining these would leave invisible floors.
            Actor->Destroy();
            continue;
        }
        if (Label == TEXT("Berth/Phoenix current ship"))
            PresentationShips.Add(Actor);
        if (Actor->ActorHasTag(TEXT("OutpostRole:Sky")))
        {
            Actor->SetActorHiddenInGame(true);
            Actor->SetActorEnableCollision(false);
        }
        if (auto *Terminal = Cast<ASSOutpostTerminal>(Actor))
        {
            OutpostTerminals.Add(Terminal);
            if (Terminal->Action == ESSOutpostAction::CycleShipPaint && Terminal->PresentationTarget)
                PresentationShips.AddUnique(Terminal->PresentationTarget.Get());
            ESSPanel Panel = ESSPanel::None;
            switch (Terminal->Action)
            {
            case ESSOutpostAction::CycleShipPaint:
                Panel = ESSPanel::Paint;
                break;
            case ESSOutpostAction::CycleWardrobe:
                Panel = ESSPanel::Wardrobe;
                break;
            case ESSOutpostAction::SurvivalBoarding:
            case ESSOutpostAction::FreeFlight:
                Panel = ESSPanel::Launch;
                break;
            default:
                if (Terminal->DisplayName.Contains(TEXT("FLIGHT UPGRADES")))
                    Panel = Home ? ESSPanel::Weapon : ESSPanel::Upgrades;
                else if (Terminal->DisplayName.Contains(TEXT("CONTRACT EXCHANGE")))
                    Panel = Home ? ESSPanel::Progression : ESSPanel::Contracts;
                else if (Terminal->DisplayName.Contains(TEXT("SHIP & PARTS")))
                    Panel = Home ? ESSPanel::Ship : ESSPanel::Vendor;
                else if (Terminal->DisplayName.Contains(TEXT("PILOT LEADERBOARD")))
                    Panel = ESSPanel::Progression;
                break;
            }
            if (Panel != ESSPanel::None)
                Services.Add({GetActorTransform().InverseTransformPosition(Terminal->GetActorLocation()),
                              Panel == ESSPanel::Launch ? TEXT("FLIGHT BRIEFING") : Terminal->DisplayName, Panel,
                              Terminal});
        }
        if (const auto *Crew = Cast<ASSOutpostAmbientActor>(Actor);
            Crew && !Crew->bDrone && !Crew->ActorHasTag(TEXT("OutpostRole:Hologram")))
            OutpostCrew.Add(Actor);
        if (Actor->IsA<ADirectionalLight>() || Actor->IsA<ASkyLight>())
            if (auto *Light = Actor->FindComponentByClass<ULightComponentBase>())
                OutpostGlobalLights.Add({Light, Light->Intensity});
        if (auto *Exposure = Cast<APostProcessVolume>(Actor); Exposure && Exposure->bUnbound)
        {
            // The authored station's exposure wins locally, then fades back to the unchanged flight
            // environment. Its own background sphere stays disabled: there is only one universe sky.
            Exposure->Priority = 50.f;
            OutpostExposure.Add(Exposure);
        }
    }
    if (!PadDeck || !PadDeck->IsCollisionEnabled())
    {
        UE_LOG(LogTemp, Warning, TEXT("SS_OUTPOST_FALLBACK tagged physical player pad unavailable"));
        DestroyOutpostHub();
        Services.Reset();
        return false;
    }
    for (const auto &Actor : PresentationShips)
        if (Actor.IsValid())
            Actor->Destroy();
    FActorSpawnParameters Params;
    Params.Owner = this;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    LandingPad = GetWorld()->SpawnActor<ASSLandingPad>(ASSLandingPad::StaticClass(),
                                                       GetActorTransform().TransformPosition(FVector(-4200, 0, 0)),
                                                       GetActorRotation(), Params);
    if (!LandingPad)
    {
        UE_LOG(LogTemp, Warning, TEXT("SS_OUTPOST_FALLBACK native docking adapter unavailable"));
        DestroyOutpostHub();
        Services.Reset();
        return false;
    }
    LandingPad->AttachToComponent(RootComponent, FAttachmentTransformRules::KeepWorldTransform);
    LandingPad->AdoptDeck(PadDeck, 3000.f);
    // Authored equipment may move with a room refinement. Old maps keep their exact service positions.
    const auto ServiceAnchor = [this, &Actors](const TCHAR *Key, const FVector &Fallback)
    {
        const FName Tag(*FString::Printf(TEXT("OutpostServiceAnchor:%s"), Key));
        for (const AActor *Actor : Actors)
            if (IsValid(Actor) && Actor->ActorHasTag(Tag))
                return GetActorTransform().InverseTransformPosition(Actor->GetActorLocation());
        return Fallback;
    };
    // Supplement the existing authored consoles with the Phase1 services the preview never simulated.
    // These are use points and labels at equipment, not replacement stands or invisible building geometry.
    AddService(ServiceAnchor(TEXT("ShipLoadout"), FVector(3685, -3240, 100)),
               Home ? TEXT("SHIP LOADOUT") : TEXT("REPAIR BAY"), Home ? ESSPanel::Ship : ESSPanel::Repair, false);
    AddService(ServiceAnchor(TEXT("Modules"), FVector(4715, -3240, 100)),
               Home ? TEXT("PILOT RECORD") : TEXT("ENGINEERING MODULES"),
               Home ? ESSPanel::Progression : ESSPanel::Vendor, false);
    AddService(ServiceAnchor(TEXT("Systems"), FVector(8120, 600, 100)),
               Home ? TEXT("SYSTEMS") : TEXT("SUSPEND / SAVE & QUIT"), Home ? ESSPanel::Settings : ESSPanel::Save,
               false);
    AddService(FVector(5000, -1100, 100), TEXT("BEACON LOG"), Home ? ESSPanel::History : ESSPanel::Reward, false);
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        if (It->GetLevel() == Level || (!It->IsA<ADirectionalLight>() && !It->IsA<ASkyLight>()))
            continue;
        if (auto *Light = It->FindComponentByClass<ULightComponentBase>())
            WorldGlobalLights.Add({Light, Light->Intensity});
    }
    Ambience = NewObject<UAudioComponent>(this);
    Ambience->SetAutoActivate(false);
    Ambience->SetupAttachment(RootComponent);
    Ambience->SetSound(SSAudio::PresentationSound(TEXT("Station")));
    Ambience->SetVolumeMultiplier(SSAudio::EffectsGain(this, .25f));
    Ambience->RegisterComponent();
    Ambience->Play();
    UpdateOutpostEnvironment();
    UE_LOG(LogTemp, Display, TEXT("SS_OUTPOST_READY map=%s actors=%d services=%d terminals=%d home=%d pad=%s"),
           SSOutpostRuntimeMap, Actors.Num(), Services.Num(), OutpostTerminals.Num(), Home,
           *LandingPad->GetActorLocation().ToString());
    return true;
}

void ASSStation::UpdateOutpostEnvironment()
{
    if (!IsUsingOutpost())
        return;
    float Weight = 1.f;
    if (const auto *Controller = GetWorld()->GetFirstPlayerController(); Controller && Controller->GetPawn())
    {
        const FVector Centre = GetActorTransform().TransformPosition(FVector(4000, 0, 300));
        const float Distance = FVector::Dist(Controller->GetPawn()->GetActorLocation(), Centre);
        Weight = 1.f - FMath::SmoothStep(17000.f, 25000.f, Distance);
    }
    if (FMath::Abs(Weight - OutpostEnvironmentWeight) < .002f)
        return;
    OutpostEnvironmentWeight = Weight;
    for (const auto &Entry : OutpostGlobalLights)
        if (auto *Light = Entry.Component.Get())
            SetOutpostLight(Light, Entry.Intensity * Weight);
    for (const auto &Entry : WorldGlobalLights)
        if (auto *Light = Entry.Component.Get())
            SetOutpostLight(Light, Entry.Intensity * (1.f - Weight));
    for (const auto &Entry : OutpostExposure)
        if (auto *Exposure = Entry.Get())
            Exposure->BlendWeight = Weight;
}

void ASSStation::DestroyOutpostHub()
{
    auto *Stream = OutpostLevel.Get();
    OutpostLevel = nullptr;
    for (const auto &Entry : WorldGlobalLights)
        if (auto *Light = Entry.Component.Get())
            SetOutpostLight(Light, Entry.Intensity);
    WorldGlobalLights.Reset();
    OutpostGlobalLights.Reset();
    OutpostExposure.Reset();
    OutpostTerminals.Reset();
    OutpostCrew.Reset();
    OutpostEnvironmentWeight = -1.f;
    if (!Stream)
        return;
    // Stop collision and scene effects immediately; unloading itself is owned by level streaming. The
    // next station's blocking load also completes this removal, avoiding overlapping station copies.
    if (ULevel *Level = Stream->GetLoadedLevel())
        for (AActor *Actor : Level->Actors)
            if (IsValid(Actor))
            {
                Actor->SetActorHiddenInGame(true);
                Actor->SetActorEnableCollision(false);
                Actor->SetActorTickEnabled(false);
                if (auto *Light = Actor->FindComponentByClass<ULightComponentBase>())
                    SetOutpostLight(Light, 0.f);
                if (auto *Exposure = Cast<APostProcessVolume>(Actor))
                    Exposure->BlendWeight = 0.f;
            }
    Stream->SetShouldBeVisible(false);
    Stream->SetShouldBeLoaded(false);
    Stream->SetIsRequestingUnloadAndRemoval(true);
}

bool ASSStation::OutpostWalkable(const FVector &World, const AActor *IgnoreActor) const
{
    const FVector Local = GetActorTransform().InverseTransformPosition(World);
    if (Local.Z < -650.f || FMath::Abs(Local.X - 4000.f) > 18000.f || FMath::Abs(Local.Y) > 14000.f)
        return false;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSOutpostWalkGround), false, this);
    Query.AddIgnoredActor(IgnoreActor);
    if (const auto *Controller = GetWorld()->GetFirstPlayerController())
        Query.AddIgnoredActor(Controller->GetPawn());
    FHitResult Floor;
    // Ask what blocks a walking pawn, not every WorldStatic decoration. The narrow sweep also admits
    // support beneath the capsule's edge at apartment thresholds where a centre ray can miss the floor.
    // The reach admits the jump arc but still requires actual collision under the pawn.
    return GetWorld()->SweepSingleByChannel(Floor, World + FVector(0, 0, 20), World - FVector(0, 0, 1400),
                                            FQuat::Identity, ECC_Pawn, FCollisionShape::MakeSphere(28.f), Query) &&
           !Floor.bStartPenetrating && Floor.ImpactNormal.Z > .55f;
}

ASSOutpostTerminal *ASSStation::OutpostTerminalAt(const APawn *User) const
{
    if (!User)
        return nullptr;
    ASSOutpostTerminal *Nearest = nullptr;
    float Distance = MAX_flt;
    for (const auto &Entry : OutpostTerminals)
        if (auto *Terminal = Entry.Get(); Terminal && Terminal->CanUse(User))
        {
            const float Candidate = FVector::DistSquared(User->GetActorLocation(), Terminal->GetActorLocation());
            if (Candidate < Distance)
            {
                Distance = Candidate;
                Nearest = Terminal;
            }
        }
    return Nearest;
}

ESSPanel ASSStation::OutpostPanel(const ASSOutpostTerminal *Terminal) const
{
    for (const auto &Service : Services)
        if (Service.Terminal.Get() == Terminal && Terminal)
            return Service.Panel;
    return ESSPanel::None;
}
