#include "SSGameMode.h"
#include "SSGameInstance.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSHUD.h"
#include "SSWorldActors.h"
#include "SSPhase1Data.h"
#include "Components/AudioComponent.h"
#include "Components/SceneComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "EngineUtils.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundAttenuation.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "ProfilingDebugging/CsvProfiler.h"

CSV_DEFINE_CATEGORY(SpaceSurvival, true);

namespace
{
const TCHAR *UpgradeNames[] = {TEXT("Hull"), TEXT("Shield"), TEXT("Engine"), TEXT("Thrusters"), TEXT("Weapon")};
FString WeaponName(SS::Weapon W)
{
    return W == SS::Weapon::RapidLaser ? TEXT("Rapid Laser") : TEXT("Heavy Cannon");
}
FString ProgressionMilestone(const SS::Account &Account)
{
    if (!Account.HeavyCannonUnlocked())
        return FString::Printf(TEXT("Next unlock: Heavy Cannon at 150 XP / %lld XP to go"),
                               (long long)(150 - Account.xp));
    if (!Account.AgileShipUnlocked())
        return FString::Printf(TEXT("Next unlock: Acorn Swift at 450 XP / %lld XP to go"),
                               (long long)(450 - Account.xp));
    if (Account.level >= 1000)
        return TEXT("All Phase 1 starting options unlocked. Account level cap reached.");
    const int64 NextXP = 450LL + (Account.level - 2LL) * 600LL;
    return FString::Printf(TEXT("Next account level: %lld XP / %lld XP to go. All Phase 1 starting options unlocked."),
                           (long long)NextXP, (long long)(NextXP - Account.xp));
}
} // namespace
ASSGameMode::ASSGameMode()
{
    PrimaryActorTick.bCanEverTick = true;
    DefaultPawnClass = nullptr;
    PlayerControllerClass = ASSPlayerController::StaticClass();
    HUDClass = ASSHUD::StaticClass();
    Director = CreateDefaultSubobject<USSSurvivalDirectorComponent>(TEXT("SurvivalDirector"));
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("AudioRoot"));
    MusicBase = CreateDefaultSubobject<UAudioComponent>(TEXT("MusicBase"));
    MusicPressure = CreateDefaultSubobject<UAudioComponent>(TEXT("MusicPressure"));
    MusicClimax = CreateDefaultSubobject<UAudioComponent>(TEXT("MusicClimax"));
    MusicBase->SetupAttachment(RootComponent);
    MusicPressure->SetupAttachment(RootComponent);
    MusicClimax->SetupAttachment(RootComponent);
}
void ASSGameMode::BeginPlay()
{
    Super::BeginPlay();
    if (!Tuning)
        Tuning = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
    if (!Tuning)
        Tuning = NewObject<USSPhase1Data>(this);
    if (auto *Data = Tuning.Get())
    {
        auto &T = GetGameInstance<USSGameInstance>()->Session.tuning;
        T.baseHull = Data->BaseHull;
        T.baseShield = Data->BaseShield;
        T.baseSpeed = Data->CruiseSpeed;
        T.baseManeuver = Data->LateralSpeed;
        T.baseResponse = Data->Response;
        T.baseAcceleration = Data->Acceleration;
        T.baseWeaponDamage = Data->BaseWeaponDamage;
        T.waveSecondsMin = Data->WaveSecondsMin;
        T.waveSecondsMax = Data->WaveSecondsMax;
        T.waveSecondsGrowth = Data->WaveSecondsGrowth;
        T.waveCredits = Data->WaveCredits;
        T.upgradeBasePrice = Data->UpgradeBasePrice;
        Director->MinimumReactionSeconds = Data->MinimumReactionSeconds;
        Director->MaximumActiveThreats = Data->MaximumActiveThreats;
        Director->BaseBudgetPerSecond = Data->BaseBudgetPerSecond;
    }
    MusicBase->SetSound(LoadObject<USoundBase>(nullptr, TEXT("/Game/SpaceSurvival/Audio/MusicBase.MusicBase")));
    MusicPressure->SetSound(
        LoadObject<USoundBase>(nullptr, TEXT("/Game/SpaceSurvival/Audio/MusicPressure.MusicPressure")));
    MusicClimax->SetSound(LoadObject<USoundBase>(nullptr, TEXT("/Game/SpaceSurvival/Audio/MusicClimax.MusicClimax")));
    AlarmSound = LoadObject<USoundBase>(nullptr, TEXT("/Game/SpaceSurvival/Audio/Alarm.Alarm"));
    AlarmAttenuation = NewObject<USoundAttenuation>(this);
    AlarmAttenuation->Attenuation.bAttenuate = true;
    AlarmAttenuation->Attenuation.bSpatialize = true;
    AlarmAttenuation->Attenuation.AttenuationShapeExtents = FVector(800.f, 0, 0);
    AlarmAttenuation->Attenuation.FalloffDistance = 2400.f;
    MusicBase->Play();
    MusicPressure->Play();
    MusicClimax->Play();
    for (TActorIterator<AStaticMeshActor> It(GetWorld()); It; ++It)
    {
        if (It->ActorHasTag(TEXT("SpaceBackdrop")))
        {
            SpaceBackdrop = *It;
            SpaceMaterial = It->GetStaticMeshComponent()->CreateAndSetMaterialInstanceDynamic(0);
        }
        if (It->ActorHasTag(TEXT("SpaceStars")))
            SpaceStars = *It;
    }
    ShowHangar();
    OpenPanel(ESSPanel::Main);
}
bool ASSGameMode::InHangar() const
{
    return IsValid(Hub) && Hub->IsHome();
}
void ASSGameMode::Announce(const FString &Message)
{
    Announcement = Message;
    AnnouncementSeconds = 7.f;
}
void ASSGameMode::React(const FString &Message)
{
    if (ReactionCooldown > 0.f)
        return;
    PilotReaction = TEXT("Acornaut: ") + Message;
    PilotReactionSeconds = 4.f;
    ReactionCooldown = 18.f;
}
void ASSGameMode::WarnThreat(const FString &Message, FVector Position, float Duration)
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI || !GI->Session.IsFlying() || !Ship)
        return;
    ThreatWarning = Message;
    ThreatPosition = Position;
    ThreatWarningSeconds = FMath::Clamp(Duration, .25f, 6.f);
    if (AlarmCooldown <= 0.f && AlarmSound)
    {
        // Project the distant threat onto a nearby bearing so urgency stays audible
        // while stereo placement still communicates its direction.
        const FVector Bearing = (Position - Ship->GetActorLocation()).GetSafeNormal();
        const FVector SoundPosition = Ship->GetActorLocation() + Bearing * 650.f;
        UGameplayStatics::PlaySoundAtLocation(
            this, AlarmSound, SoundPosition,
            float(GI->Session.settings.masterVolume * GI->Session.settings.effectsVolume) * .65f, 1.f, 0.f,
            AlarmAttenuation);
        AlarmCooldown = 6.f;
    }
}
void ASSGameMode::UpdateThreatFeedback(float Dt)
{
    AlarmCooldown = FMath::Max(0.f, AlarmCooldown - Dt);
    ReactionCooldown = FMath::Max(0.f, ReactionCooldown - Dt);
    ThreatWarningSeconds = FMath::Max(0.f, ThreatWarningSeconds - Dt);
    PilotReactionSeconds = FMath::Max(0.f, PilotReactionSeconds - Dt);
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI || !Ship || !GI->Session.IsFlying())
        return;
    const auto &S = GI->Session;
    const float HullFraction = float(S.run.hull / FMath::Max(1.0, S.Stats().maxHull));
    if (HullFraction > .4f)
        LowHullAlerted = false;
    if (HullFraction <= .25f && !LowHullAlerted)
    {
        LowHullAlerted = true;
        WarnThreat(TEXT("HULL CRITICAL / FIND CLEAR SPACE"), Ship->GetActorLocation(), 5.f);
        React(TEXT("Hull's hurting. Give me a little room."));
    }
    // Warn for a predicted near collision, not every visible rock or nearby enemy.
    ASSWorldBody *UrgentBody = nullptr;
    float Earliest = 2.5f;
    for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
    {
        if (It->IsActorBeingDestroyed() || !It->IsSolidHazard())
            continue;
        const FVector Offset = It->GetActorLocation() - Ship->GetActorLocation();
        const FVector RelativeVelocity = It->GetVelocity() - Ship->GetVelocity();
        const double SpeedSquared = RelativeVelocity.SizeSquared();
        if (SpeedSquared < 1.0)
            continue;
        const float Time = float(-FVector::DotProduct(Offset, RelativeVelocity) / SpeedSquared);
        if (Time <= 0.f || Time >= Earliest)
            continue;
        const double Clearance = It->GetBodyRadius() + 220.f;
        if ((Offset + RelativeVelocity * Time).SizeSquared() < Clearance * Clearance)
        {
            Earliest = Time;
            UrgentBody = *It;
        }
    }
    if (UrgentBody)
        WarnThreat(TEXT("COLLISION COURSE / EVADE"), UrgentBody->GetActorLocation(), .4f);
}
void ASSGameMode::ApplyWorldOffset(const FVector &InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    ThreatPosition += InOffset;
}
void ASSGameMode::ShowHangar()
{
    ThreatWarningSeconds = PilotReactionSeconds = 0.f;
    Director->SetActive(false);
    Director->ResetEncounter();
    if (Ship)
    {
        Ship->Destroy();
        Ship = nullptr;
    }
    if (Walker)
    {
        Walker->Destroy();
        Walker = nullptr;
    }
    if (Hub)
        Hub->Destroy();
    Hub = GetWorld()->SpawnActor<ASSStation>(FVector::ZeroVector, FRotator::ZeroRotator);
    Hub->BuildHub(true);
    Hub->SetBayShip(SelectedShip);
    Walker = GetWorld()->SpawnActor<ASSWalker>(Hub->WalkSpawn(), FRotator::ZeroRotator);
    UGameplayStatics::GetPlayerController(this, 0)->Possess(Walker);
    PreviousPhase = int32(GetGameInstance<USSGameInstance>()->Session.run.phase);
    PreviousWave = -1;
    ClosePanel();
}
void ASSGameMode::SpawnFlight(FVector Location, FRotator Rotation)
{
    if (Walker)
    {
        Walker->Destroy();
        Walker = nullptr;
    }
    if (Hub)
    {
        Hub->Destroy();
        Hub = nullptr;
    }
    if (Ship)
        Ship->Destroy();
    Ship = GetWorld()->SpawnActor<ASSShip>(Location, Rotation);
    UGameplayStatics::GetPlayerController(this, 0)->Possess(Ship);
    Director->SetActive(true);
    ClosePanel();
}
void ASSGameMode::StartNewRun()
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI)
        return;
    if (GI->Session.run.phase == SS::Phase::Dead && !DeathPersisted)
    {
        OpenPanel(ESSPanel::Results);
        return;
    }
    if (!GI->PersistAccount())
    {
        Announce(GI->LastSaveError);
        return;
    }
    SS::Session Candidate = GI->Session;
    if (!Candidate.StartRun(TCHAR_TO_UTF8(*FGuid::NewGuid().ToString(EGuidFormats::Digits)), SS::Ship(SelectedShip),
                            SS::Weapon(SelectedWeapon)))
    {
        Announce(TEXT("Select an unlocked ship and starting weapon."));
        return;
    }
    if (!GI->InvalidateSuspend())
    {
        Announce(GI->LastSaveError);
        return;
    }
    GI->Session = Candidate;
    DeathPersisted = false;
    LowHullAlerted = false;
    AlarmCooldown = 0.f;
    ReactionCooldown = 12.f;
    PendingReward = false;
    WeaponBuffSeconds = 0;
    Director->ResetEncounter();
    PreviousPhase = -1;
    PreviousWave = -1;
    SpawnFlight(FVector(0, 0, 7000), FRotator::ZeroRotator);
    Announce(TEXT("Acornaut: One more journey. Steer, weave, and keep moving."));
}
void ASSGameMode::LaunchFromHub()
{
    if (InHangar())
    {
        StartNewRun();
        return;
    }
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI)
        return;
    if (!GI->Session.LaunchFromStation())
    {
        Announce(TEXT("Phase 1 flight content ends at Station 2. This live run can be suspended here."));
        return;
    }
    const FVector Location =
        Hub ? Hub->GetActorTransform().TransformPosition(FVector(3500, 0, 1800)) : FVector(0, 0, 7000);
    const FRotator Rotation = Hub ? Hub->GetActorRotation() : FRotator::ZeroRotator;
    SpawnFlight(Location, Rotation);
    Announce(TEXT("Dockmaster: Departure clear. Good hunting, Acornaut."));
}
void ASSGameMode::EnterStation()
{
    Director->SetActive(false);
    Director->ResetEncounter();
    if (Walker)
    {
        Walker->Destroy();
        Walker = nullptr;
    }
    if (Hub && Hub->IsHome())
    {
        Hub->Destroy();
        Hub = nullptr;
    }
    if (!Hub)
    {
        Hub = GetWorld()->SpawnActor<ASSStation>(StationTarget, FRotator::ZeroRotator);
        Hub->BuildHub(false);
    }
    Hub->SetBayShip(int32(GetGameInstance<USSGameInstance>()->Session.run.ship));
    Walker = GetWorld()->SpawnActor<ASSWalker>(Hub->WalkSpawn(), FRotator::ZeroRotator);
    auto *PC = UGameplayStatics::GetPlayerController(this, 0);
    PC->Possess(Walker);
    PC->SetControlRotation(Hub->GetActorRotation());
    if (Ship)
    {
        Ship->FinishDocking();
        Hub->ShowBayShip(false);
        const FVector Exit = Hub->GetActorTransform().TransformPosition(FVector(650, -350, 100));
        Walker->BeginDisembark(Ship->GetActorLocation() + FVector(0, 0, 100), Exit, Hub->GetActorRotation());
        PC->SetViewTarget(Ship);
        PC->SetViewTargetWithBlend(Walker, .9f);
    }
    ClosePanel();
    Announce(TEXT("Dockmaster: Welcome aboard. Your ship is in the service bay."));
    React(TEXT("A solid floor. I missed that."));
}
void ASSGameMode::Tick(float Dt)
{
    Super::Tick(Dt);
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI)
        return;
    auto &S = GI->Session;
    AnnouncementSeconds = FMath::Max(0.f, AnnouncementSeconds - Dt);
    bool Danger = false;
    if (Ship && S.IsFlying())
        for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
            if ((It->IsEnemy() || It->IsSolidHazard() || It->IsEnvironmentalField()) &&
                FVector::DistSquared(It->GetActorLocation(), Ship->GetActorLocation()) <
                    FMath::Square(8000.f + It->GetBodyRadius()))
            {
                Danger = true;
                break;
            }
    S.Tick(Dt, Danger);
#if CSV_PROFILER && !CSV_PROFILER_MINIMAL
    // Sample after the domain step; avoid the threat actor scan outside an enabled capture.
    if (FCsvProfiler::IsCapturing() && FCsvProfiler::Get()->IsCategoryEnabled(CSV_CATEGORY_INDEX(SpaceSurvival)))
    {
        CSV_CUSTOM_STAT(SpaceSurvival, Phase, int32(S.run.phase), ECsvCustomStatOp::Set);
        CSV_CUSTOM_STAT(SpaceSurvival, Wave, int32(S.run.wave), ECsvCustomStatOp::Set);
        CSV_CUSTOM_STAT(SpaceSurvival, RunActive, S.run.active ? 1 : 0, ECsvCustomStatOp::Set);
        CSV_CUSTOM_STAT(SpaceSurvival, ActiveThreats, Director->GetActiveThreatCount(), ECsvCustomStatOp::Set);
        CSV_CUSTOM_STAT(SpaceSurvival, Hull, float(S.run.hull), ECsvCustomStatOp::Set);
        CSV_CUSTOM_STAT(SpaceSurvival, ShipSpeedCmPerSec, IsValid(Ship) ? float(Ship->GetVelocity().Size()) : 0.f,
                        ECsvCustomStatOp::Set);
        if (PreviousPhase != int32(S.run.phase))
        {
            CSV_EVENT_NOLOG(SpaceSurvival, TEXT("Phase %d -> %d; Wave %d; RunActive %d"), PreviousPhase,
                            int32(S.run.phase), int32(S.run.wave), S.run.active ? 1 : 0);
        }
    }
#endif
    UpdateThreatFeedback(Dt);
    RegionTime += Dt;
    if (auto *Pawn = UGameplayStatics::GetPlayerPawn(this, 0))
    {
        if (SpaceBackdrop)
            SpaceBackdrop->SetActorLocation(Pawn->GetActorLocation());
        if (SpaceStars)
            SpaceStars->SetActorLocation(Pawn->GetActorLocation());
        if (SpaceMaterial)
        {
            // Long gradual visual drift, independent of wave and station cadence.
            const uint32 RegionSeed = GetTypeHash(FString(UTF8_TO_TCHAR(S.run.id.c_str())));
            const float Blend = .5f + .5f * FMath::Sin(RegionTime * .006f + float(RegionSeed % 1000) * .01f);
            SpaceMaterial->SetVectorParameterValue(
                TEXT("Tint"), FMath::Lerp(FLinearColor(.45f, .65f, 1), FLinearColor(1, .35f, .8f), Blend));
        }
    }
    WeaponBuffSeconds = float(S.run.weaponBuffSeconds);
    PendingReward = S.run.pendingReward;
    RewardCombat = S.run.rewardCombat;
    const float Master = float(S.settings.masterVolume * S.settings.musicVolume);
    MusicBase->SetVolumeMultiplier(Master * (InHangar() ? .35f : .65f));
    MusicPressure->SetVolumeMultiplier(Master * FMath::Clamp(Director->GetPressure() * .65f, 0.f, .65f) *
                                       (S.IsFlying() ? 1.f : 0.f));
    MusicClimax->SetVolumeMultiplier(Master * (S.run.phase == SS::Phase::Climax ? .75f : 0.f));
    if (S.run.phase == SS::Phase::Dead)
    {
        if (PreviousPhase != int32(S.run.phase))
        {
            Director->SetActive(false);
            Director->ResetEncounter();
            DeathPersisted = GI->PersistDeath();
            ShowHangar();
            OpenPanel(ESSPanel::Results);
        }
        PreviousPhase = int32(S.run.phase);
        return;
    }
    if (!S.run.active)
        return;
    if (S.run.wave != PreviousWave || int32(S.run.phase) != PreviousPhase)
    {
        if (S.run.wave != PreviousWave)
        {
            Director->Configure(S.run.wave, S.run.phase == SS::Phase::Climax);
            Announce(FString::Printf(TEXT("WAVE %d  |  Keep surviving"), S.run.wave));
        }
        Director->SetBreathing(S.run.phase == SS::Phase::Breathing);
        if (S.run.phase == SS::Phase::Wormhole)
        {
            Announce(TEXT("WORMHOLE DISTURBANCE  |  Maintain control. The pull is increasing."));
            if (Ship)
            {
                auto *Passage =
                    GetWorld()->SpawnActor<ASSWormholePassage>(Ship->GetActorLocation(), Ship->GetActorRotation());
                if (Passage)
                    Passage->BeginPassage(Ship, float(S.run.phaseDuration));
            }
        }
        if (S.run.phase == SS::Phase::Climax)
        {
            Director->Configure(S.run.wave, true);
            Announce(S.run.wave == 5 ? TEXT("Hostile space. Stay mobile until a station signal resolves.")
                                     : TEXT("COMPOUND FRONT  |  Gravity, asteroids and enemy pressure."));
        }
        if (S.run.phase == SS::Phase::Approach && Ship)
        {
            Director->SetActive(false);
            const FRotator Arrival(0, Ship->GetActorRotation().Yaw, 0);
            const FVector Dock = Ship->GetActorLocation() + Ship->GetActorForwardVector() * 18000.f;
            StationTarget = Dock - Arrival.Vector() * 850.f - FVector(0, 0, 220);
            if (Hub)
                Hub->Destroy();
            Hub = GetWorld()->SpawnActor<ASSStation>(StationTarget, Arrival);
            Hub->BuildHub(false);
            Hub->ShowBayShip(false);
            Announce(TEXT(
                "STATION DETECTED  |  Approach the marked corridor. Final landing assistance engages inside 12 m."));
        }
        if (S.run.phase == SS::Phase::Station)
            EnterStation();
        PreviousPhase = int32(S.run.phase);
        PreviousWave = S.run.wave;
    }
    if (S.run.phase == SS::Phase::Approach && Ship && Hub)
    {
        const FVector ToDock = Hub->DockPosition() - Ship->GetActorLocation();
        if (ToDock.Size() < 1200.f &&
            FVector::DotProduct(Ship->GetActorForwardVector(), ToDock.GetSafeNormal()) > .45f && S.BeginDocking())
        {
            Ship->SetDockingTarget(Hub->DockPosition(), Hub->GetActorRotation());
            Announce(TEXT("Docking assistance engaged. Welcome to port."));
        }
    }
    // Unreal origin rebasing keeps the uninterrupted journey numerically stable.
    if (Ship && Ship->GetActorLocation().Size() > 1000000.f)
    {
        const FIntVector Shift(Ship->GetActorLocation());
        StationTarget -= FVector(Shift);
        GetWorld()->SetNewWorldOrigin(GetWorld()->OriginLocation + Shift);
    }
    if (S.IsFlying() && S.run.wave <= 3 && AnnouncementSeconds <= 0)
    {
        const TCHAR *Prompts[] = {
            TEXT("STEER: mouse / right stick. The ship carries momentum while its hull banks."),
            TEXT("THROTTLE: W S / D-pad up down. A D and R F / left stick weave around hazards."),
            TEXT("BOOST: Shift / right trigger. Release to recharge the meter."),
            TEXT("BRAKE: Space / left trigger. Partial braking builds heat; give it time to cool."),
            TEXT("DODGE: Q / left bumper with a movement direction. Obstacles still hurt during a dodge."),
            TEXT("FIRE: left mouse / right bumper. Aim manually; brackets provide soft targeting assistance."),
            TEXT("PICKUPS: collect shaped rewards. Hull regenerates after damage; shield does not."),
            TEXT("OPTIONAL SIGNALS: approach, then E / A to accept. Passing nearby does not commit you.")};
        const int Limit = S.run.wave == 1 ? 5 : S.run.wave == 2 ? 7 : 8;
        for (int I = 0; I < Limit; ++I)
        {
            if (!(S.account.tutorialFlags & (1u << I)))
            {
                Announce(Prompts[I]);
                break;
            }
        }
    }
}
void ASSGameMode::NotifyEnemyKilled()
{
    if (auto *GI = GetGameInstance<USSGameInstance>())
        GI->Session.RecordKill();
}
void ASSGameMode::NotifyEventCompleted(bool bCombat)
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI || !GI->Session.run.active)
        return;
    React(bCombat ? TEXT("Signal answered. That was worth the trouble.") : TEXT("Good salvage. Let\'s make it count."));
    ++GI->Session.run.eventsCompleted;
    GI->Session.AwardCredits(bCombat ? 100 : 70);
    GI->Session.run.pendingReward = true;
    GI->Session.run.rewardCombat = bCombat;
    PendingReward = true;
    RewardCombat = bCombat;
    Announce(TEXT("Signal resolved. Reward secured. Interact to choose a module or weapon replacement."));
}
void ASSGameMode::NotifyPickup(int32 Kind, float Amount)
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI || !GI->Session.run.active)
        return;
    auto &S = GI->Session;
    const auto Stats = S.Stats();
    switch (Kind)
    {
    case 0:
        S.AwardCredits(FMath::RoundToInt(Amount));
        ++S.run.salvageCollected;
        break;
    case 1:
        S.run.hull = FMath::Min(Stats.maxHull, S.run.hull + Amount);
        break;
    case 2:
        React(TEXT("Shield charge. Just what we needed."));
        S.run.shield = FMath::Min(Stats.maxShield, S.run.shield + Amount);
        break;
    case 3:
        S.run.weaponBuffSeconds = FMath::Max(S.run.weaponBuffSeconds, double(FMath::Clamp(Amount, 0.f, 60.f)));
        break;
    default:
        return;
    }
    if (!(S.account.tutorialFlags & 64u))
    {
        S.account.tutorialFlags |= 64u;
        GI->PersistAccount();
    }
    UGameplayStatics::PlaySound2D(this,
                                  LoadObject<USoundBase>(nullptr, TEXT("/Game/SpaceSurvival/Audio/Pickup.Pickup")),
                                  float(S.settings.masterVolume * S.settings.effectsVolume));
}
void ASSGameMode::Interact()
{
    if (IsMenuOpen())
        return;
    if (Walker && Hub)
    {
        FString Label;
        const auto Service = Hub->NearestService(Walker->GetActorLocation(), Label);
        if (Service != ESSPanel::None)
            OpenPanel(Service);
        return;
    }
    if (Ship)
    {
        if (PendingReward)
        {
            OpenPanel(ESSPanel::Reward);
            return;
        }
        ASSEncounterBeacon *Closest = nullptr;
        float Distance = MAX_flt;
        for (TActorIterator<ASSEncounterBeacon> It(GetWorld()); It; ++It)
            if (It->IsPlayerInRange() && !It->IsResolved())
            {
                const float D = FVector::DistSquared(Ship->GetActorLocation(), It->GetActorLocation());
                if (D < Distance)
                {
                    Distance = D;
                    Closest = *It;
                }
            }
        if (Closest)
        {
            ActiveBeacon = Closest;
            if (Closest->IsDepot())
                OpenPanel(ESSPanel::Depot);
            else if (Closest->TryAccept())
            {
                if (auto *GI = GetGameInstance<USSGameInstance>())
                {
                    GI->Session.account.tutorialFlags |= 128u;
                    GI->PersistAccount();
                }
                Announce(Closest->GetEncounterLabel());
            }
        }
    }
}
void ASSGameMode::AddEntry(const FString &Label, int32 Action, bool Enabled)
{
    Entries.Add({Label, Action, Enabled});
}
void ASSGameMode::ClosePanel()
{
    Panel = ESSPanel::None;
    Entries.Empty();
    SelectedEntry = 0;
    if (auto *PC = UGameplayStatics::GetPlayerController(this, 0))
    {
        PC->bShowMouseCursor = false;
        PC->SetInputMode(FInputModeGameOnly());
    }
    // In-flight depot/reward panels never stop the universe or park the ship.
    UGameplayStatics::SetGamePaused(this, false);
}
void ASSGameMode::OpenPanel(ESSPanel NewPanel)
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI)
        return;
    auto &S = GI->Session;
    Panel = NewPanel;
    Entries.Empty();
    SelectedEntry = 0;
    PanelDetail.Empty();
    if (auto *PC = UGameplayStatics::GetPlayerController(this, 0))
    {
        PC->bShowMouseCursor = true;
        PC->SetInputMode(FInputModeGameAndUI());
    }
    const bool LivePanel = (Panel == ESSPanel::Depot || Panel == ESSPanel::Reward) && S.IsFlying();
    UGameplayStatics::SetGamePaused(this, S.IsFlying() && !LivePanel);
    switch (Panel)
    {
    case ESSPanel::Main:
        PanelTitle = TEXT("SPACE SURVIVAL");
        PanelDetail = TEXT("How far will this journey take you?");
        if (S.run.active)
        {
            AddEntry(TEXT("Return to the journey"), 1);
            if (S.AtSliceBoundary())
                AddEntry(TEXT("Abandon this suspended-capable slice and start a new run (no death XP)"), 51);
        }
        else
        {
            AddEntry(TEXT("Continue suspended run"), 2, GI->HasSuspendedRun());
            AddEntry(TEXT("New run"), 3);
            AddEntry(TEXT("Home hangar"), 4);
        }
        AddEntry(TEXT("Settings"), 5);
        AddEntry(TEXT("Run stats / progression"), 6);
        AddEntry(S.run.active ? TEXT("Quit (unsuspended progress will be lost)") : TEXT("Quit"), 7);
        break;
    case ESSPanel::Results:
        PanelTitle = TEXT("THE JOURNEY ENDS");
        PanelDetail = FString::Printf(TEXT("Wave %d  |  Score %d  |  +%d XP  |  Account level %d\n%s"),
                                      S.account.lastWave, S.account.lastScore, S.account.lastXP, S.account.level,
                                      DeathPersisted ? TEXT("Your next launch starts fresh. Your unlocks remain.")
                                                     : TEXT("Progression save failed. Retry before continuing."));
        if (S.account.xp - S.account.lastXP < 150 && S.account.HeavyCannonUnlocked())
            PanelDetail += TEXT("\nNEW STARTING WEAPON: HEAVY CANNON / select it at the hangar loadout.");
        if (S.account.xp - S.account.lastXP < 450 && S.account.AgileShipUnlocked())
            PanelDetail += TEXT("\nNEW SHIP: ACORN SWIFT / select it at the hangar ship bay.");
        PanelDetail += TEXT("\n") + ProgressionMilestone(S.account);
        AddEntry(TEXT("Launch another run"), 3, DeathPersisted);
        AddEntry(TEXT("Review ship and weapon in hangar"), 4, DeathPersisted);
        if (!DeathPersisted)
            AddEntry(TEXT("Retry progression save"), 8);
        break;
    case ESSPanel::Settings:
        PanelTitle = TEXT("SETTINGS");
        AddEntry(TEXT("Graphics"), 10);
        AddEntry(TEXT("Audio"), 11);
        AddEntry(TEXT("Controls"), 12);
        AddEntry(FString::Printf(TEXT("Subtitles: %s"), S.settings.subtitles ? TEXT("On") : TEXT("Off")), 13);
        AddEntry(FString::Printf(TEXT("UI scale: %.0f%%"), S.settings.uiScale * 100), 14);
        AddEntry(FString::Printf(TEXT("Camera shake: %s"), S.settings.cameraShake ? TEXT("On") : TEXT("Off")), 15);
        break;
    case ESSPanel::Graphics:
        PanelTitle = TEXT("GRAPHICS");
        PanelDetail = TEXT("Simulation and warning readability are preserved at every quality level.");
        AddEntry(FString::Printf(TEXT("Quality: %d / 3"), S.settings.quality), 16);
        AddEntry(FString::Printf(TEXT("Frame limit: %d FPS"), S.settings.frameLimit), 17);
        AddEntry(FString::Printf(TEXT("Motion blur: %s"), S.settings.motionBlur ? TEXT("On") : TEXT("Off")), 18);
        break;
    case ESSPanel::Audio:
        PanelTitle = TEXT("AUDIO");
        AddEntry(FString::Printf(TEXT("Master: %.0f%%"), S.settings.masterVolume * 100), 19);
        AddEntry(FString::Printf(TEXT("Music: %.0f%%"), S.settings.musicVolume * 100), 20);
        AddEntry(FString::Printf(TEXT("Effects: %.0f%%"), S.settings.effectsVolume * 100), 21);
        break;
    case ESSPanel::Controls:
        PanelTitle = TEXT("FLIGHT / WALK CONTROLS");
        PanelDetail = TEXT(
            "Mouse / right stick: steer or look   |   A D, R F / left stick: lateral + vertical\nW S / D-pad up down: "
            "throttle   |   Left click / RB: fire\nShift / RT: boost   |   Space / LT: brake   |   Q / LB: directional "
            "dodge\nE / A: interact   |   Esc / Menu: shell   |   Walk: W A S D / left stick, Shift / X run");
        AddEntry(FString::Printf(TEXT("Mouse sensitivity: %.1f"), S.settings.mouseSensitivity), 22);
        AddEntry(FString::Printf(TEXT("Controller sensitivity: %.1f"), S.settings.controllerSensitivity), 23);
        AddEntry(FString::Printf(TEXT("Invert pitch: %s"), S.settings.invertPitch ? TEXT("On") : TEXT("Off")), 24);
        AddEntry(FString::Printf(TEXT("Boost: %s"), S.settings.toggleBoost ? TEXT("Toggle") : TEXT("Hold")), 25);
        AddEntry(FString::Printf(TEXT("Brake: %s"), S.settings.toggleBrake ? TEXT("Toggle") : TEXT("Hold")), 26);
        AddEntry(TEXT("Replay flight guidance next run"), 27);
        break;
    case ESSPanel::Progression:
        PanelTitle = TEXT("PILOT RECORD");
        PanelDetail = FString::Printf(TEXT("Account level %d  |  %lld XP\nHighest wave %d  |  Best score %d  |  Runs "
                                           "%d\nLast run: wave %d / score %d\nHeavy Cannon: %s  |  Agile ship: %s"),
                                      S.account.level, (long long)S.account.xp, S.account.highestWave,
                                      S.account.bestScore, S.account.runs, S.account.lastWave, S.account.lastScore,
                                      S.account.HeavyCannonUnlocked() ? TEXT("Unlocked") : TEXT("Level 2"),
                                      S.account.AgileShipUnlocked() ? TEXT("Unlocked") : TEXT("Level 3"));
        PanelDetail += TEXT("\n") + ProgressionMilestone(S.account);
        AddEntry(TEXT("Recent journeys"), 28, !S.account.history.empty());
        break;
    case ESSPanel::History:
        PanelTitle = TEXT("RECENT JOURNEYS");
        HistoryPage = FMath::Clamp(HistoryPage, 0, FMath::Max(0, (int32(S.account.history.size()) - 1) / 3));
        PanelDetail = TEXT("Most recent first. Credits show total earned during each journey.\n");
        for (int32 I = HistoryPage * 3; I < FMath::Min(HistoryPage * 3 + 3, int32(S.account.history.size())); ++I)
        {
            const auto &Past = S.account.history[I];
            PanelDetail +=
                FString::Printf(TEXT("\nWave %d · %d score · +%d XP\n%s / %s · %d kills · %d credits\n"), Past.wave,
                                Past.score, Past.xp, Past.ship == SS::Ship::Agile ? TEXT("Swift") : TEXT("Voyager"),
                                *WeaponName(Past.weapon), Past.kills, Past.credits);
        }
        AddEntry(TEXT("Newer journeys"), 60, HistoryPage > 0);
        AddEntry(TEXT("Older journeys"), 61, (HistoryPage + 1) * 3 < int32(S.account.history.size()));
        break;
    case ESSPanel::Ship:
        PanelTitle = TEXT("SHIP BAY");
        PanelDetail = TEXT("The agile chassis turns and accelerates faster, with less starting hull.");
        AddEntry(TEXT("Acorn Voyager / balanced starter"), 30);
        AddEntry(TEXT("Acorn Swift / agility, reduced hull"), 31, S.account.AgileShipUnlocked());
        break;
    case ESSPanel::Weapon:
        PanelTitle = TEXT("STARTING WEAPON");
        PanelDetail = TEXT("One active weapon. Run upgrades are earned after launch.");
        AddEntry(TEXT("Rapid Laser / fast and forgiving"), 32);
        AddEntry(TEXT("Heavy Cannon / slower, high impact"), 33, S.account.HeavyCannonUnlocked());
        break;
    case ESSPanel::Upgrades:
    case ESSPanel::Depot:
        PanelTitle = Panel == ESSPanel::Depot ? TEXT("MOBILE DEPOT / PASSING DEALS") : TEXT("CORE UPGRADES");
        PanelDetail =
            FString::Printf(TEXT("Credits %d  |  Purchased tiers remain yours until the run ends."), S.run.credits);
        for (int I = 0; I < 5; ++I)
        {
            const bool Available =
                Panel != ESSPanel::Depot || (IsValid(ActiveBeacon) && ActiveBeacon->GetOffers().Contains(I));
            if (!Available)
                continue;
            const int Price =
                S.UpgradePrice(SS::Upgrade(I), Panel == ESSPanel::Depot ? ActiveBeacon->GetDiscount() : 1.f);
            AddEntry(FString::Printf(TEXT("%s %d -> %d   |   %d credits"), UpgradeNames[I], S.run.tiers[I],
                                     FMath::Min(5, S.run.tiers[I] + 1), Price),
                     100 + I, S.run.tiers[I] < 5 && S.run.credits >= Price);
        }
        if (Panel == ESSPanel::Depot)
        {
            const int ShieldPrice = S.DepotShieldRepairPrice();
            AddEntry(FString::Printf(TEXT("Shield recharge only / %d credits"), ShieldPrice), 105,
                     S.IsFlying() && IsValid(ActiveBeacon) && ActiveBeacon->IsDepot() &&
                         ActiveBeacon->IsPlayerInRange() && S.run.shield < S.Stats().maxShield &&
                         S.run.credits >= ShieldPrice);
        }
        break;
    case ESSPanel::Repair:
        PanelTitle = TEXT("REPAIR BAY");
        PanelDetail = TEXT("Restore hull and shield, and clear temporary subsystem damage.");
        AddEntry(FString::Printf(TEXT("Full service / %d credits"), S.tuning.repairPrice), 40,
                 S.run.credits >= S.tuning.repairPrice);
        break;
    case ESSPanel::Contracts:
        PanelTitle = TEXT("CONTRACT BOARD");
        PanelDetail = TEXT("One active contract. Reward at the next station; failure forfeits reward only.");
        PanelDetail += TEXT("\nPressure terms: shield capacity -35%; hazard pressure +0.15 until the next station.");
        AddEntry(
            FString::Printf(TEXT("Pressure contract / accept disclosed terms / +%d credits"), S.tuning.contractReward),
            41, S.run.contract == SS::Contract::None && S.run.wave < 10);
        AddEntry(FString::Printf(TEXT("Hunter / destroy %d enemies before next station / +%d credits"),
                                 S.tuning.objectiveTarget, S.tuning.contractReward),
                 42, S.run.contract == SS::Contract::None && S.run.wave < 10);
        break;
    case ESSPanel::Save:
        PanelTitle = TEXT("SUSPEND RUN");
        PanelDetail =
            TEXT("Save and close the application. Continue consumes this suspension. Death ends the run permanently.");
        AddEntry(TEXT("Save & Quit"), 43);
        break;
    case ESSPanel::Vendor:
        PanelTitle = TEXT("ENGINEER MICA");
        PanelDetail = TEXT(
            "Mica: I can fit one utility. Choose the capability you need. Replacing a module removes the old one.");
        AddEntry(TEXT("Vector Thrusters / 150 credits / stronger lateral authority"), 44, S.run.credits >= 150);
        AddEntry(TEXT("Overdrive Cooling / 150 credits / boost efficiency and heat control"), 45, S.run.credits >= 150);
        break;
    case ESSPanel::Reward:
        PanelTitle = PendingReward ? TEXT("SIGNAL REWARD / CHOOSE ONE") : TEXT("LOST CREW BEACON");
        PanelDetail = PendingReward ? TEXT("One deliberate reward. A module replaces the current module; a weapon "
                                           "replaces the active weapon.")
                                    : TEXT("An unfinished beacon repeats a crew's home coordinates. Mica kept the "
                                           "receiver powered. Restore its antenna to recover the cargo tip.");
        if (PendingReward)
        {
            AddEntry(TEXT("Fit Vector Thrusters"), 46);
            AddEntry(TEXT("Fit Overdrive Cooling"), 47);
            if (RewardCombat)
                AddEntry(TEXT("Replace active weapon with Heavy Cannon"), 48);
        }
        else
            AddEntry(TEXT("Restore the beacon / recover 25 credits"), 49, !S.run.stationRewardClaimed);
        break;
    case ESSPanel::Launch:
        PanelTitle = InHangar() ? TEXT("PREPARE FOR LAUNCH") : TEXT("DEPARTURE CONTROL");
        PanelDetail =
            InHangar() ? FString::Printf(TEXT("%s  |  %s"), SelectedShip ? TEXT("Acorn Swift") : TEXT("Acorn Voyager"),
                                         *WeaponName(SS::Weapon(SelectedWeapon)))
            : S.AtSliceBoundary() ? TEXT("You reached the Phase 1 flight boundary. This is a live station stop, not "
                                         "the game's final wave. Save & Quit retains the run.")
                                  : TEXT("Continue with your current ship, credits and upgrades.");
        AddEntry(TEXT("Launch"), 50, InHangar() || !S.AtSliceBoundary());
        break;
    default:
        break;
    }
    AddEntry(TEXT("Back"), 0);
}
void ASSGameMode::ActivateEntry(int32 Index)
{
    if (!Entries.IsValidIndex(Index) || !Entries[Index].Enabled)
        return;
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI)
        return;
    auto &S = GI->Session;
    const int A = Entries[Index].Action;
    const ESSPanel Current = Panel;
    if (A == 0 || A == 1)
    {
        ClosePanel();
        return;
    }
    if (A == 2)
    {
        if (GI->ResumeRun())
        {
            StationTarget = FVector::ZeroVector;
            EnterStation();
            PreviousPhase = int32(S.run.phase);
            PreviousWave = S.run.wave;
        }
        else
            Announce(GI->LastSaveError);
        return;
    }
    if (A == 3)
    {
        StartNewRun();
        return;
    }
    if (A == 4)
    {
        ShowHangar();
        return;
    }
    if (A == 5)
    {
        OpenPanel(ESSPanel::Settings);
        return;
    }
    if (A == 6)
    {
        OpenPanel(ESSPanel::Progression);
        return;
    }
    if (A == 7)
    {
        UKismetSystemLibrary::QuitGame(this, UGameplayStatics::GetPlayerController(this, 0), EQuitPreference::Quit,
                                       false);
        return;
    }
    if (A == 8)
    {
        DeathPersisted = GI->PersistDeath();
        OpenPanel(ESSPanel::Results);
        return;
    }
    if (A == 10)
    {
        OpenPanel(ESSPanel::Graphics);
        return;
    }
    if (A == 11)
    {
        OpenPanel(ESSPanel::Audio);
        return;
    }
    if (A == 12)
    {
        OpenPanel(ESSPanel::Controls);
        return;
    }
    if (A == 28)
    {
        HistoryPage = 0;
        OpenPanel(ESSPanel::History);
        return;
    }
    if (A == 60 || A == 61)
    {
        HistoryPage += A == 60 ? -1 : 1;
        OpenPanel(ESSPanel::History);
        return;
    }
    if (A >= 13 && A <= 27)
    {
        switch (A)
        {
        case 13:
            S.settings.subtitles = !S.settings.subtitles;
            break;
        case 14:
            S.settings.uiScale = S.settings.uiScale >= 1.4 ? .8 : S.settings.uiScale + .1;
            break;
        case 15:
            S.settings.cameraShake = !S.settings.cameraShake;
            break;
        case 16:
            S.settings.quality = (S.settings.quality + 1) % 4;
            break;
        case 17:
            S.settings.frameLimit = S.settings.frameLimit == 60 ? 120 : S.settings.frameLimit == 120 ? 144 : 60;
            break;
        case 18:
            S.settings.motionBlur = !S.settings.motionBlur;
            break;
        case 19:
            S.settings.masterVolume = S.settings.masterVolume >= .99 ? 0 : S.settings.masterVolume + .1;
            break;
        case 20:
            S.settings.musicVolume = S.settings.musicVolume >= .99 ? 0 : S.settings.musicVolume + .1;
            break;
        case 21:
            S.settings.effectsVolume = S.settings.effectsVolume >= .99 ? 0 : S.settings.effectsVolume + .1;
            break;
        case 22:
            S.settings.mouseSensitivity =
                S.settings.mouseSensitivity >= 2.9 ? .3 : FMath::Min(2.9, S.settings.mouseSensitivity + .2);
            break;
        case 23:
            S.settings.controllerSensitivity =
                S.settings.controllerSensitivity >= 2.9 ? .3 : FMath::Min(2.9, S.settings.controllerSensitivity + .2);
            break;
        case 24:
            S.settings.invertPitch = !S.settings.invertPitch;
            break;
        case 25:
            S.settings.toggleBoost = !S.settings.toggleBoost;
            break;
        case 26:
            S.settings.toggleBrake = !S.settings.toggleBrake;
            break;
        case 27:
            S.account.tutorialFlags = 0;
            GI->PersistAccount();
            break;
        }
        if (!GI->PersistSettings())
            Announce(GI->LastSaveError);
        OpenPanel(Current);
        return;
    }
    if (A >= 30 && A <= 33)
    {
        if (A <= 31)
        {
            SelectedShip = A - 30;
            if (Hub)
                Hub->SetBayShip(SelectedShip);
        }
        else
            SelectedWeapon = A - 32;
        Announce(TEXT("Starting loadout selected."));
        ClosePanel();
        return;
    }
    if (A >= 100 && A < 105)
    {
        const int I = A - 100;
        const bool Depot = Current == ESSPanel::Depot;
        if (Depot &&
            (!IsValid(ActiveBeacon) || !ActiveBeacon->IsPlayerInRange() || !ActiveBeacon->GetOffers().Contains(I)))
        {
            Announce(TEXT("Depot is out of range."));
            ClosePanel();
            return;
        }
        const bool Ok = S.Purchase(SS::Upgrade(I), Depot ? ActiveBeacon->GetDiscount() : 1.f);
        Announce(Ok ? TEXT("Upgrade installed.") : TEXT("Upgrade unavailable."));
        OpenPanel(Current);
        return;
    }
    if (A == 105)
    {
        if (Current != ESSPanel::Depot || !S.IsFlying() || !IsValid(ActiveBeacon) || !ActiveBeacon->IsDepot() ||
            !ActiveBeacon->IsPlayerInRange())
        {
            Announce(TEXT("Depot shield service is out of range."));
            ClosePanel();
            return;
        }
        Announce(S.RepairShieldAtDepot() ? TEXT("Shield recharged. Hull and subsystem repairs require a station.")
                                         : TEXT("Shield service unavailable."));
        OpenPanel(Current);
        return;
    }
    if (A == 40)
    {
        Announce(S.Repair() ? TEXT("Service complete. All systems restored.") : TEXT("Service unavailable."));
        OpenPanel(Current);
        return;
    }
    if (A == 41 || A == 42)
    {
        Announce(S.AcceptContract(A == 41 ? SS::Contract::Pressure : SS::Contract::Objective)
                     ? TEXT("Contract accepted. Terms remain active until the next station.")
                     : TEXT("Contract unavailable."));
        OpenPanel(Current);
        return;
    }
    if (A == 43)
    {
        if (GI->SuspendRun())
            UKismetSystemLibrary::QuitGame(this, UGameplayStatics::GetPlayerController(this, 0), EQuitPreference::Quit,
                                           false);
        else
            Announce(GI->LastSaveError);
        return;
    }
    if (A == 44 || A == 45)
    {
        if (S.run.phase == SS::Phase::Station && S.run.credits >= 150 &&
            S.EquipUtility(A == 44 ? SS::Utility::VectorThrusters : SS::Utility::OverdriveCooling))
        {
            S.run.credits -= 150;
            Announce(TEXT("Module fitted."));
        }
        OpenPanel(Current);
        return;
    }
    if (A >= 46 && A <= 48)
    {
        if (!S.run.pendingReward)
            return;
        const bool Success =
            A == 48 ? S.ReplaceWeapon(SS::Weapon::HeavyCannon)
                    : S.EquipUtility(A == 46 ? SS::Utility::VectorThrusters : SS::Utility::OverdriveCooling);
        if (Success)
        {
            S.run.pendingReward = false;
            PendingReward = false;
            Announce(TEXT("Reward fitted. Keep surviving."));
            ClosePanel();
        }
        return;
    }
    if (A == 49)
    {
        if (!S.run.stationRewardClaimed && S.run.phase == SS::Phase::Station)
        {
            S.run.stationRewardClaimed = true;
            S.AwardCredits(25);
            Announce(TEXT("Receiver restored. The crew's signal carries on."));
        }
        OpenPanel(Current);
        return;
    }
    if (A == 50)
    {
        LaunchFromHub();
        return;
    }
    if (A == 51 && S.AtSliceBoundary())
    {
        if (!GI->InvalidateSuspend())
        {
            Announce(GI->LastSaveError);
            return;
        }
        S.run = SS::Run{};
        ShowHangar();
        OpenPanel(ESSPanel::Launch);
        return;
    }
}

ASSPlayerController::ASSPlayerController()
{
    PrimaryActorTick.bTickEvenWhenPaused = true;
    bShouldPerformFullTickWhenPaused = true;
}
void ASSPlayerController::PlayerTick(float Dt)
{
    Super::PlayerTick(Dt);
    auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>();
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GM || !GI)
        return;
    if (LastInputPawn.Get() != GetPawn())
    {
        LastInputPawn = GetPawn();
        BoostLatch = BrakeLatch = false;
    }
    const auto Pressed = [this](FKey K) { return WasInputKeyJustPressed(K); };
    const auto Down = [this](FKey K) { return IsInputKeyDown(K); };
    if (Pressed(EKeys::Escape) || Pressed(EKeys::Gamepad_Special_Right))
    {
        if (GM->IsMenuOpen())
            GM->ClosePanel();
        else
            GM->OpenPanel(ESSPanel::Main);
    }
    const bool MenuInput = GM->IsMenuOpen();
    const bool LiveFlightMenu =
        MenuInput && GI->Session.IsFlying() && (GM->Panel == ESSPanel::Depot || GM->Panel == ESSPanel::Reward);
    if (MenuInput)
    {
        if (Pressed(EKeys::Up) || Pressed(EKeys::Gamepad_DPad_Up))
            GM->SelectedEntry = FMath::Max(0, GM->SelectedEntry - 1);
        if (Pressed(EKeys::Down) || Pressed(EKeys::Gamepad_DPad_Down))
            GM->SelectedEntry = FMath::Min(GM->Entries.Num() - 1, GM->SelectedEntry + 1);
        if (Pressed(EKeys::Enter) || Pressed(EKeys::Gamepad_FaceButton_Bottom))
            GM->ActivateEntry(GM->SelectedEntry);
        if (Pressed(EKeys::Gamepad_FaceButton_Right))
            GM->ClosePanel();
        if (Pressed(EKeys::LeftMouseButton))
            if (auto *HUD = Cast<ASSHUD>(GetHUD()))
            {
                float X, Y;
                if (GetMousePosition(X, Y))
                    GM->ActivateEntry(HUD->MenuIndexAt(FVector2D(X, Y)));
            }
        if (!LiveFlightMenu || !GI->Session.IsFlying())
        {
            if (auto *ShipPawn = Cast<ASSShip>(GetPawn()))
                ShipPawn->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 0, false, false);
            return;
        }
        // Live offers retain flight control. Menu clicks, confirm and navigation
        // stay consumed for this frame even when selecting a reward closes it.
    }
    float MouseX = 0, MouseY = 0;
    GetInputMouseDelta(MouseX, MouseY);
    const float MouseDegrees = GM->Tuning ? GM->Tuning->MouseSensitivity : .143f;
    const float SteeringDegrees = GM->Tuning ? GM->Tuning->SteeringDegrees : 65.f;
    const float StickScale =
        (GM->Tuning ? GM->Tuning->ControllerSensitivity : 1.f) * float(GI->Session.settings.controllerSensitivity);
    const float MouseScale = float(GI->Session.settings.mouseSensitivity) * MouseDegrees /
                             (FMath::Max(1.f, SteeringDegrees) * FMath::Max(.001f, Dt));
    FVector2D Look(MouseX * MouseScale + GetInputAnalogKeyState(EKeys::Gamepad_RightX) * StickScale,
                   -MouseY * MouseScale + GetInputAnalogKeyState(EKeys::Gamepad_RightY) * StickScale);
    if (GI->Session.settings.invertPitch)
        Look.Y = -Look.Y;
    if (auto *ShipPawn = Cast<ASSShip>(GetPawn()))
    {
        const bool Boost = Down(EKeys::LeftShift) || GetInputAnalogKeyState(EKeys::Gamepad_RightTriggerAxis) > .3f;
        const bool Brake = Down(EKeys::SpaceBar) || GetInputAnalogKeyState(EKeys::Gamepad_LeftTriggerAxis) > .3f;
        if (Pressed(EKeys::LeftShift) || Pressed(EKeys::Gamepad_RightTrigger))
            BoostLatch = !BoostLatch;
        if (Pressed(EKeys::SpaceBar) || Pressed(EKeys::Gamepad_LeftTrigger))
            BrakeLatch = !BrakeLatch;
        FVector2D Strafe(float(Down(EKeys::D)) - float(Down(EKeys::A)) + GetInputAnalogKeyState(EKeys::Gamepad_LeftX),
                         float(Down(EKeys::R)) - float(Down(EKeys::F)) + GetInputAnalogKeyState(EKeys::Gamepad_LeftY));
        const float Throttle = float(Down(EKeys::W) || (!MenuInput && Down(EKeys::Gamepad_DPad_Up))) -
                               float(Down(EKeys::S) || (!MenuInput && Down(EKeys::Gamepad_DPad_Down)));
        const bool FireHeld = (!MenuInput && Down(EKeys::LeftMouseButton)) || Down(EKeys::Gamepad_RightShoulder);
        const uint32 Before = GI->Session.account.tutorialFlags;
        if (!Look.IsNearlyZero())
            GI->Session.account.tutorialFlags |= 1u;
        if (FMath::Abs(Throttle) > .1f)
            GI->Session.account.tutorialFlags |= 2u;
        if (Boost)
            GI->Session.account.tutorialFlags |= 4u;
        if (Brake)
            GI->Session.account.tutorialFlags |= 8u;
        if (Pressed(EKeys::Q) || Pressed(EKeys::Gamepad_LeftShoulder))
            GI->Session.account.tutorialFlags |= 16u;
        if (FireHeld)
            GI->Session.account.tutorialFlags |= 32u;
        if (Before != GI->Session.account.tutorialFlags)
            GI->PersistAccount();
        ShipPawn->SetFlightInput(Look, Strafe, Throttle, GI->Session.settings.toggleBoost ? BoostLatch : Boost,
                                 GI->Session.settings.toggleBrake ? BrakeLatch : Brake);
        if (Pressed(EKeys::Q) || Pressed(EKeys::Gamepad_LeftShoulder))
            ShipPawn->RequestDodge();
        if (FireHeld)
            ShipPawn->Fire();
    }
    else if (auto *WalkPawn = Cast<ASSWalker>(GetPawn()))
        WalkPawn->Move(
            FVector2D(float(Down(EKeys::D)) - float(Down(EKeys::A)) + GetInputAnalogKeyState(EKeys::Gamepad_LeftX),
                      float(Down(EKeys::W)) - float(Down(EKeys::S)) + GetInputAnalogKeyState(EKeys::Gamepad_LeftY)),
            Look, Down(EKeys::LeftShift) || Down(EKeys::Gamepad_FaceButton_Left), Dt);
    if (!MenuInput && (Pressed(EKeys::E) || Pressed(EKeys::Gamepad_FaceButton_Bottom)))
        GM->Interact();
}
