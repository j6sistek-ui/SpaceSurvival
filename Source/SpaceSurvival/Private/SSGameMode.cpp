#include "SSGameMode.h"
#include "SSGameInstance.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSHUD.h"
#include "SSWorldActors.h"
#include "SSPhase1Data.h"
#include "Components/AudioComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "EngineUtils.h"
#include "Sound/SoundBase.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace
{
const TCHAR* UpgradeNames[]={TEXT("Hull"),TEXT("Shield"),TEXT("Engine"),TEXT("Thrusters"),TEXT("Weapon")};
FString WeaponName(SS::Weapon W) { return W==SS::Weapon::RapidLaser?TEXT("Rapid Laser"):TEXT("Heavy Cannon"); }
}
ASSGameMode::ASSGameMode()
{
    PrimaryActorTick.bCanEverTick=true;
    DefaultPawnClass=nullptr; PlayerControllerClass=ASSPlayerController::StaticClass(); HUDClass=ASSHUD::StaticClass();
    Director=CreateDefaultSubobject<USSSurvivalDirectorComponent>(TEXT("SurvivalDirector"));
    MusicBase=CreateDefaultSubobject<UAudioComponent>(TEXT("MusicBase"));
    MusicPressure=CreateDefaultSubobject<UAudioComponent>(TEXT("MusicPressure"));
    MusicClimax=CreateDefaultSubobject<UAudioComponent>(TEXT("MusicClimax"));
}
void ASSGameMode::BeginPlay()
{
    Super::BeginPlay();
    if(auto* Data=LoadObject<USSPhase1Data>(nullptr,TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1")))
    {
        auto& T=GetGameInstance<USSGameInstance>()->Session.tuning;
        T.baseHull=Data->BaseHull; T.baseShield=Data->BaseShield; T.baseSpeed=Data->CruiseSpeed;
        T.baseManeuver=Data->LateralSpeed; T.baseResponse=Data->Response; T.baseAcceleration=Data->Acceleration;
        T.baseWeaponDamage=Data->BaseWeaponDamage; T.waveSecondsMin=Data->WaveSecondsMin;
        T.waveSecondsMax=Data->WaveSecondsMax; T.waveSecondsGrowth=Data->WaveSecondsGrowth;
        T.waveCredits=Data->WaveCredits; T.upgradeBasePrice=Data->UpgradeBasePrice;
        Director->MinimumReactionSeconds=Data->MinimumReactionSeconds; Director->MaximumActiveThreats=Data->MaximumActiveThreats;
        Director->BaseBudgetPerSecond=Data->BaseBudgetPerSecond;
    }
    MusicBase->SetSound(LoadObject<USoundBase>(nullptr,TEXT("/Game/SpaceSurvival/Audio/MusicBase.MusicBase")));
    MusicPressure->SetSound(LoadObject<USoundBase>(nullptr,TEXT("/Game/SpaceSurvival/Audio/MusicPressure.MusicPressure")));
    MusicClimax->SetSound(LoadObject<USoundBase>(nullptr,TEXT("/Game/SpaceSurvival/Audio/MusicClimax.MusicClimax")));
    MusicBase->Play(); MusicPressure->Play(); MusicClimax->Play();
    for(TActorIterator<AStaticMeshActor> It(GetWorld());It;++It)
    {
        if(It->ActorHasTag(TEXT("SpaceBackdrop"))) {SpaceBackdrop=*It;SpaceMaterial=It->GetStaticMeshComponent()->CreateAndSetMaterialInstanceDynamic(0);}
        if(It->ActorHasTag(TEXT("SpaceStars"))) SpaceStars=*It;
    }
    ShowHangar(); OpenPanel(ESSPanel::Main);
}
bool ASSGameMode::InHangar() const { return IsValid(Hub) && Hub->IsHome(); }
void ASSGameMode::Announce(const FString& Message)
{
    Announcement=Message; AnnouncementSeconds=7.f;
}
void ASSGameMode::ShowHangar()
{
    Director->SetActive(false); Director->ResetEncounter();
    if (Ship) { Ship->Destroy(); Ship=nullptr; }
    if (Walker) { Walker->Destroy(); Walker=nullptr; }
    if (Hub) Hub->Destroy();
    Hub=GetWorld()->SpawnActor<ASSStation>(FVector::ZeroVector,FRotator::ZeroRotator); Hub->BuildHub(true);
    Walker=GetWorld()->SpawnActor<ASSWalker>(Hub->WalkSpawn(),FRotator::ZeroRotator);
    UGameplayStatics::GetPlayerController(this,0)->Possess(Walker);
    PreviousPhase=int32(GetGameInstance<USSGameInstance>()->Session.run.phase); PreviousWave=-1;
    ClosePanel();
}
void ASSGameMode::SpawnFlight(FVector Location,FRotator Rotation)
{
    if (Walker) { Walker->Destroy(); Walker=nullptr; }
    if (Hub) { Hub->Destroy(); Hub=nullptr; }
    if (Ship) Ship->Destroy();
    Ship=GetWorld()->SpawnActor<ASSShip>(Location,Rotation);
    UGameplayStatics::GetPlayerController(this,0)->Possess(Ship);
    Director->SetActive(true); ClosePanel();
}
void ASSGameMode::StartNewRun()
{
    auto* GI=GetGameInstance<USSGameInstance>(); if (!GI) return;
    if(GI->Session.run.phase==SS::Phase::Dead && !DeathPersisted) {OpenPanel(ESSPanel::Results);return;}
    if(!GI->PersistAccount()) {Announce(GI->LastSaveError);return;}
    SS::Session Candidate=GI->Session;
    if (!Candidate.StartRun(TCHAR_TO_UTF8(*FGuid::NewGuid().ToString(EGuidFormats::Digits)),SS::Ship(SelectedShip),SS::Weapon(SelectedWeapon)))
    { Announce(TEXT("Select an unlocked ship and starting weapon.")); return; }
    if (!GI->InvalidateSuspend()) { Announce(GI->LastSaveError); return; }
    GI->Session=Candidate;
    DeathPersisted=false; PendingReward=false; WeaponBuffSeconds=0;
    Director->ResetEncounter(); PreviousPhase=-1; PreviousWave=-1;
    SpawnFlight(FVector(0,0,7000),FRotator::ZeroRotator);
    Announce(TEXT("Acornaut: One more journey. Steer, weave, and keep moving."));
}
void ASSGameMode::LaunchFromHub()
{
    if (InHangar()) { StartNewRun(); return; }
    auto* GI=GetGameInstance<USSGameInstance>(); if (!GI) return;
    if (!GI->Session.LaunchFromStation())
    { Announce(TEXT("Phase 1 flight content ends at Station 2. This live run can be suspended here.")); return; }
    const FVector Location=Hub?Hub->GetActorTransform().TransformPosition(FVector(3500,0,1800)):FVector(0,0,7000);
    const FRotator Rotation=Hub?Hub->GetActorRotation():FRotator::ZeroRotator;
    SpawnFlight(Location,Rotation); Announce(TEXT("Dockmaster: Departure clear. Good hunting, Acornaut."));
}
void ASSGameMode::EnterStation()
{
    Director->SetActive(false); Director->ResetEncounter();
    if (Ship) { Ship->Destroy(); Ship=nullptr; }
    if (Walker) { Walker->Destroy(); Walker=nullptr; }
    if (Hub && Hub->IsHome()) { Hub->Destroy(); Hub=nullptr; }
    if (!Hub) {Hub=GetWorld()->SpawnActor<ASSStation>(StationTarget,FRotator::ZeroRotator); Hub->BuildHub(false);}
    Walker=GetWorld()->SpawnActor<ASSWalker>(Hub->WalkSpawn(),FRotator::ZeroRotator);
    UGameplayStatics::GetPlayerController(this,0)->Possess(Walker);
    ClosePanel(); Announce(TEXT("Dockmaster: Welcome aboard. Your ship is in the service bay."));
}
void ASSGameMode::Tick(float Dt)
{
    Super::Tick(Dt);
    auto* GI=GetGameInstance<USSGameInstance>(); if (!GI) return;
    auto& S=GI->Session;
    AnnouncementSeconds=FMath::Max(0.f,AnnouncementSeconds-Dt);
    bool Danger=false;
    if(Ship && S.IsFlying())
        for(TActorIterator<ASSWorldBody> It(GetWorld());It;++It)
            if((It->IsEnemy()||It->IsSolidHazard()||It->IsEnvironmentalField()) && FVector::DistSquared(It->GetActorLocation(),Ship->GetActorLocation())<FMath::Square(8000.f+It->GetBodyRadius()))
            {Danger=true;break;}
    S.Tick(Dt,Danger);
    RegionTime+=Dt;
    if(auto* Pawn=UGameplayStatics::GetPlayerPawn(this,0))
    {
        if(SpaceBackdrop) SpaceBackdrop->SetActorLocation(Pawn->GetActorLocation());
        if(SpaceStars) SpaceStars->SetActorLocation(Pawn->GetActorLocation());
        if(SpaceMaterial)
        {
            // Long gradual visual drift, independent of wave and station cadence.
            const uint32 RegionSeed=GetTypeHash(FString(UTF8_TO_TCHAR(S.run.id.c_str())));
            const float Blend=.5f+.5f*FMath::Sin(RegionTime*.006f+float(RegionSeed%1000)*.01f);
            SpaceMaterial->SetVectorParameterValue(TEXT("Tint"),FMath::Lerp(FLinearColor(.45f,.65f,1),FLinearColor(1,.35f,.8f),Blend));
        }
    }
    WeaponBuffSeconds=float(S.run.weaponBuffSeconds);
    PendingReward=S.run.pendingReward; RewardCombat=S.run.rewardCombat;
    const float Master=float(S.settings.masterVolume*S.settings.musicVolume);
    MusicBase->SetVolumeMultiplier(Master*(InHangar()?.35f:.65f));
    MusicPressure->SetVolumeMultiplier(Master*FMath::Clamp(Director->GetPressure()*.65f,0.f,.65f)*(S.IsFlying()?1.f:0.f));
    MusicClimax->SetVolumeMultiplier(Master*(S.run.phase==SS::Phase::Climax?.75f:0.f));
    if (S.run.phase==SS::Phase::Dead)
    {
        if (PreviousPhase!=int32(S.run.phase))
        {
            Director->SetActive(false); Director->ResetEncounter();
            DeathPersisted=GI->PersistDeath();
            ShowHangar(); OpenPanel(ESSPanel::Results);
        }
        PreviousPhase=int32(S.run.phase); return;
    }
    if (!S.run.active) return;
    if (S.run.wave!=PreviousWave || int32(S.run.phase)!=PreviousPhase)
    {
        if (S.run.wave!=PreviousWave)
        {
            Director->Configure(S.run.wave,S.run.phase==SS::Phase::Climax);
            Announce(FString::Printf(TEXT("WAVE %d  |  Keep surviving"),S.run.wave));
        }
        Director->SetBreathing(S.run.phase==SS::Phase::Breathing);
        if (S.run.phase==SS::Phase::Wormhole)
        {
            Announce(TEXT("WORMHOLE DISTURBANCE  |  Maintain control. The pull is increasing."));
            if(Ship)
            {
                auto* Passage=GetWorld()->SpawnActor<ASSWormholePassage>(Ship->GetActorLocation(),Ship->GetActorRotation());
                if(Passage) Passage->BeginPassage(Ship,float(S.run.phaseDuration));
            }
        }
        if (S.run.phase==SS::Phase::Climax)
        {
            Director->Configure(S.run.wave,true);
            Announce(S.run.wave==5?TEXT("Hostile space. Stay mobile until a station signal resolves."):TEXT("COMPOUND FRONT  |  Gravity, asteroids and enemy pressure."));
        }
        if (S.run.phase==SS::Phase::Approach && Ship)
        {
            Director->SetActive(false);
            const FRotator Arrival(0,Ship->GetActorRotation().Yaw,0);
            const FVector Dock=Ship->GetActorLocation()+Ship->GetActorForwardVector()*18000.f;
            StationTarget=Dock-Arrival.Vector()*850.f-FVector(0,0,220);
            if (Hub) Hub->Destroy();
            Hub=GetWorld()->SpawnActor<ASSStation>(StationTarget,Arrival); Hub->BuildHub(false);
            Announce(TEXT("STATION DETECTED  |  Approach the marked corridor. Final landing assistance engages inside 12 m."));
        }
        if (S.run.phase==SS::Phase::Station) EnterStation();
        PreviousPhase=int32(S.run.phase); PreviousWave=S.run.wave;
    }
    if (S.run.phase==SS::Phase::Approach && Ship && Hub)
    {
        const FVector ToDock=Hub->DockPosition()-Ship->GetActorLocation();
        if (ToDock.Size()<1200.f && FVector::DotProduct(Ship->GetActorForwardVector(),ToDock.GetSafeNormal())>.45f && S.BeginDocking())
        {
            Ship->SetDockingTarget(Hub->DockPosition(),Hub->GetActorRotation());
            Announce(TEXT("Docking assistance engaged. Welcome to port."));
        }
    }
    // Unreal origin rebasing keeps the uninterrupted journey numerically stable.
    if (Ship && Ship->GetActorLocation().Size()>1000000.f)
    {
        const FIntVector Shift(Ship->GetActorLocation());
        StationTarget-=FVector(Shift);
        GetWorld()->SetNewWorldOrigin(GetWorld()->OriginLocation+Shift);
    }
    if (S.IsFlying() && S.run.wave<=3 && AnnouncementSeconds<=0)
    {
        const TCHAR* Prompts[]={
            TEXT("STEER: mouse / right stick. The ship carries momentum while its hull banks."),
            TEXT("THROTTLE: W S / D-pad up down. A D and R F / left stick weave around hazards."),
            TEXT("BOOST: Shift / right trigger. Release to recharge the meter."),
            TEXT("BRAKE: Space / left trigger. Partial braking builds heat; give it time to cool."),
            TEXT("DODGE: Q / left bumper with a movement direction. Obstacles still hurt during a dodge."),
            TEXT("FIRE: left mouse / right bumper. Aim manually; brackets provide soft targeting assistance."),
            TEXT("PICKUPS: collect shaped rewards. Hull regenerates after damage; shield does not."),
            TEXT("OPTIONAL SIGNALS: approach, then E / A to accept. Passing nearby does not commit you.")};
        const int Limit=S.run.wave==1?5:S.run.wave==2?7:8;
        for(int I=0;I<Limit;++I)
        {
            if(!(S.account.tutorialFlags&(1u<<I))) {Announce(Prompts[I]);break;}
        }
    }
}
void ASSGameMode::NotifyEnemyKilled()
{
    if (auto* GI=GetGameInstance<USSGameInstance>()) GI->Session.RecordKill();
}
void ASSGameMode::NotifyEventCompleted(bool bCombat)
{
    auto* GI=GetGameInstance<USSGameInstance>(); if (!GI || !GI->Session.run.active) return;
    ++GI->Session.run.eventsCompleted; GI->Session.AwardCredits(bCombat?100:70);
    GI->Session.run.pendingReward=true; GI->Session.run.rewardCombat=bCombat;
    PendingReward=true; RewardCombat=bCombat;
    Announce(TEXT("Signal resolved. Reward secured. Interact to choose a module or weapon replacement."));
}
void ASSGameMode::NotifyPickup(int32 Kind,float Amount)
{
    auto* GI=GetGameInstance<USSGameInstance>(); if (!GI || !GI->Session.run.active) return;
    auto& S=GI->Session; const auto Stats=S.Stats();
    switch (Kind)
    {
        case 0:S.AwardCredits(FMath::RoundToInt(Amount)); ++S.run.salvageCollected; break;
        case 1:S.run.hull=FMath::Min(Stats.maxHull,S.run.hull+Amount); break;
        case 2:S.run.shield=FMath::Min(Stats.maxShield,S.run.shield+Amount); break;
        case 3:S.run.weaponBuffSeconds=FMath::Max(S.run.weaponBuffSeconds,12.0); break;
        default:return;
    }
    if(!(S.account.tutorialFlags&64u)) {S.account.tutorialFlags|=64u;GI->PersistAccount();}
    UGameplayStatics::PlaySound2D(this,LoadObject<USoundBase>(nullptr,TEXT("/Game/SpaceSurvival/Audio/Pickup.Pickup")),float(S.settings.masterVolume*S.settings.effectsVolume));
}
void ASSGameMode::Interact()
{
    if (IsMenuOpen()) return;
    if (Walker && Hub)
    {
        FString Label; const auto Service=Hub->NearestService(Walker->GetActorLocation(),Label);
        if (Service!=ESSPanel::None) OpenPanel(Service);
        return;
    }
    if (Ship)
    {
        if (PendingReward) { OpenPanel(ESSPanel::Reward); return; }
        ASSEncounterBeacon* Closest=nullptr; float Distance=MAX_flt;
        for (TActorIterator<ASSEncounterBeacon> It(GetWorld());It;++It)
            if (It->IsPlayerInRange() && !It->IsResolved())
            { const float D=FVector::DistSquared(Ship->GetActorLocation(),It->GetActorLocation()); if (D<Distance) {Distance=D;Closest=*It;} }
        if (Closest)
        {
            ActiveBeacon=Closest;
            if (Closest->IsDepot()) OpenPanel(ESSPanel::Depot);
            else if(Closest->TryAccept())
            {
                if(auto* GI=GetGameInstance<USSGameInstance>()) {GI->Session.account.tutorialFlags|=128u;GI->PersistAccount();}
                Announce(Closest->GetEncounterLabel());
            }
        }
    }
}
void ASSGameMode::AddEntry(const FString& Label,int32 Action,bool Enabled) { Entries.Add({Label,Action,Enabled}); }
void ASSGameMode::ClosePanel()
{
    Panel=ESSPanel::None; Entries.Empty(); SelectedEntry=0;
    if (auto* PC=UGameplayStatics::GetPlayerController(this,0))
    { PC->bShowMouseCursor=false; PC->SetInputMode(FInputModeGameOnly()); }
    // In-flight depot/reward panels never stop the universe or park the ship.
    UGameplayStatics::SetGamePaused(this,false);
}
void ASSGameMode::OpenPanel(ESSPanel NewPanel)
{
    auto* GI=GetGameInstance<USSGameInstance>(); if (!GI) return;
    auto& S=GI->Session; Panel=NewPanel; Entries.Empty(); SelectedEntry=0; PanelDetail.Empty();
    if (auto* PC=UGameplayStatics::GetPlayerController(this,0))
    { PC->bShowMouseCursor=true; PC->SetInputMode(FInputModeGameAndUI()); }
    const bool LivePanel=(Panel==ESSPanel::Depot || Panel==ESSPanel::Reward) && S.IsFlying();
    UGameplayStatics::SetGamePaused(this,S.IsFlying() && !LivePanel);
    switch(Panel)
    {
    case ESSPanel::Main:
        PanelTitle=TEXT("SPACE SURVIVAL"); PanelDetail=TEXT("How far will this journey take you?");
        if (S.run.active)
        {
            AddEntry(TEXT("Return to the journey"),1);
            if(S.AtSliceBoundary()) AddEntry(TEXT("Abandon this suspended-capable slice and start a new run (no death XP)"),51);
        }
        else { AddEntry(TEXT("Continue suspended run"),2,GI->HasSuspendedRun()); AddEntry(TEXT("New run"),3); AddEntry(TEXT("Home hangar"),4); }
        AddEntry(TEXT("Settings"),5); AddEntry(TEXT("Run stats / progression"),6);
        AddEntry(S.run.active?TEXT("Quit (unsuspended progress will be lost)"):TEXT("Quit"),7); break;
    case ESSPanel::Results:
        PanelTitle=TEXT("THE JOURNEY ENDS");
        PanelDetail=FString::Printf(TEXT("Wave %d  |  Score %d  |  +%d XP  |  Account level %d\n%s"),S.account.lastWave,S.account.lastScore,S.account.lastXP,S.account.level,
            DeathPersisted?TEXT("Your next launch starts fresh. Your unlocks remain."):TEXT("Progression save failed. Retry before continuing."));
        AddEntry(TEXT("Launch another run"),3,DeathPersisted); AddEntry(TEXT("Review ship and weapon in hangar"),4,DeathPersisted);
        if (!DeathPersisted) AddEntry(TEXT("Retry progression save"),8); break;
    case ESSPanel::Settings:
        PanelTitle=TEXT("SETTINGS"); AddEntry(TEXT("Graphics"),10); AddEntry(TEXT("Audio"),11); AddEntry(TEXT("Controls"),12);
        AddEntry(FString::Printf(TEXT("Subtitles: %s"),S.settings.subtitles?TEXT("On"):TEXT("Off")),13);
        AddEntry(FString::Printf(TEXT("UI scale: %.0f%%"),S.settings.uiScale*100),14);
        AddEntry(FString::Printf(TEXT("Camera shake: %s"),S.settings.cameraShake?TEXT("On"):TEXT("Off")),15); break;
    case ESSPanel::Graphics:
        PanelTitle=TEXT("GRAPHICS"); PanelDetail=TEXT("Simulation and warning readability are preserved at every quality level.");
        AddEntry(FString::Printf(TEXT("Quality: %d / 3"),S.settings.quality),16);
        AddEntry(FString::Printf(TEXT("Frame limit: %d FPS"),S.settings.frameLimit),17);
        AddEntry(FString::Printf(TEXT("Motion blur: %s"),S.settings.motionBlur?TEXT("On"):TEXT("Off")),18); break;
    case ESSPanel::Audio:
        PanelTitle=TEXT("AUDIO");
        AddEntry(FString::Printf(TEXT("Master: %.0f%%"),S.settings.masterVolume*100),19);
        AddEntry(FString::Printf(TEXT("Music: %.0f%%"),S.settings.musicVolume*100),20);
        AddEntry(FString::Printf(TEXT("Effects: %.0f%%"),S.settings.effectsVolume*100),21); break;
    case ESSPanel::Controls:
        PanelTitle=TEXT("FLIGHT / WALK CONTROLS");
        PanelDetail=TEXT("Mouse / right stick: steer or look   |   A D, R F / left stick: lateral + vertical\nW S / D-pad up down: throttle   |   Left click / RB: fire\nShift / RT: boost   |   Space / LT: brake   |   Q / LB: directional dodge\nE / A: interact   |   Esc / Menu: shell   |   Walk: W A S D / left stick, Shift / X run");
        AddEntry(FString::Printf(TEXT("Mouse sensitivity: %.1f"),S.settings.mouseSensitivity),22);
        AddEntry(FString::Printf(TEXT("Controller sensitivity: %.1f"),S.settings.controllerSensitivity),23);
        AddEntry(FString::Printf(TEXT("Invert pitch: %s"),S.settings.invertPitch?TEXT("On"):TEXT("Off")),24);
        AddEntry(FString::Printf(TEXT("Boost: %s"),S.settings.toggleBoost?TEXT("Toggle"):TEXT("Hold")),25);
        AddEntry(FString::Printf(TEXT("Brake: %s"),S.settings.toggleBrake?TEXT("Toggle"):TEXT("Hold")),26);
        AddEntry(TEXT("Replay flight guidance next run"),27); break;
    case ESSPanel::Progression:
        PanelTitle=TEXT("PILOT RECORD");
        PanelDetail=FString::Printf(TEXT("Account level %d  |  %lld XP\nHighest wave %d  |  Best score %d  |  Runs %d\nLast run: wave %d / score %d\nHeavy Cannon: %s  |  Agile ship: %s"),S.account.level,(long long)S.account.xp,S.account.highestWave,S.account.bestScore,S.account.runs,S.account.lastWave,S.account.lastScore,
            S.account.HeavyCannonUnlocked()?TEXT("Unlocked"):TEXT("Level 2"),S.account.AgileShipUnlocked()?TEXT("Unlocked"):TEXT("Level 3")); break;
    case ESSPanel::Ship:
        PanelTitle=TEXT("SHIP BAY"); PanelDetail=TEXT("The agile chassis turns and accelerates faster, with less starting hull.");
        AddEntry(TEXT("Acorn Voyager / balanced starter"),30); AddEntry(TEXT("Acorn Swift / agility, reduced hull"),31,S.account.AgileShipUnlocked()); break;
    case ESSPanel::Weapon:
        PanelTitle=TEXT("STARTING WEAPON"); PanelDetail=TEXT("One active weapon. Run upgrades are earned after launch.");
        AddEntry(TEXT("Rapid Laser / fast and forgiving"),32); AddEntry(TEXT("Heavy Cannon / slower, high impact"),33,S.account.HeavyCannonUnlocked()); break;
    case ESSPanel::Upgrades:
    case ESSPanel::Depot:
        PanelTitle=Panel==ESSPanel::Depot?TEXT("MOBILE DEPOT / PASSING DEALS"):TEXT("CORE UPGRADES");
        PanelDetail=FString::Printf(TEXT("Credits %d  |  Purchased tiers remain yours until the run ends."),S.run.credits);
        for(int I=0;I<5;++I)
        {
            const bool Available=Panel!=ESSPanel::Depot || (IsValid(ActiveBeacon) && ActiveBeacon->GetOffers().Contains(I));
            if(!Available) continue;
            const int Price=S.UpgradePrice(SS::Upgrade(I),Panel==ESSPanel::Depot?ActiveBeacon->GetDiscount():1.f);
            AddEntry(FString::Printf(TEXT("%s %d -> %d   |   %d credits"),UpgradeNames[I],S.run.tiers[I],FMath::Min(5,S.run.tiers[I]+1),Price),100+I,S.run.tiers[I]<5 && S.run.credits>=Price);
        } break;
    case ESSPanel::Repair:
        PanelTitle=TEXT("REPAIR BAY"); PanelDetail=TEXT("Restore hull and shield, and clear temporary subsystem damage.");
        AddEntry(FString::Printf(TEXT("Full service / %d credits"),S.tuning.repairPrice),40,S.run.credits>=S.tuning.repairPrice); break;
    case ESSPanel::Contracts:
        PanelTitle=TEXT("CONTRACT BOARD"); PanelDetail=TEXT("One active contract. Reward at the next station; failure forfeits reward only.");
        AddEntry(TEXT("Pressure contract / reduced shield capacity until next station / +150 credits"),41,S.run.contract==SS::Contract::None && S.run.wave<10);
        AddEntry(TEXT("Hunter contract / destroy 6 enemies before next station / +150 credits"),42,S.run.contract==SS::Contract::None && S.run.wave<10); break;
    case ESSPanel::Save:
        PanelTitle=TEXT("SUSPEND RUN"); PanelDetail=TEXT("Save and close the application. Continue consumes this suspension. Death ends the run permanently.");
        AddEntry(TEXT("Save & Quit"),43); break;
    case ESSPanel::Vendor:
        PanelTitle=TEXT("ENGINEER MICA"); PanelDetail=TEXT("Mica: I can fit one utility. Choose the capability you need. Replacing a module removes the old one.");
        AddEntry(TEXT("Vector Thrusters / 150 credits / stronger lateral authority"),44,S.run.credits>=150);
        AddEntry(TEXT("Overdrive Cooling / 150 credits / boost efficiency and heat control"),45,S.run.credits>=150); break;
    case ESSPanel::Reward:
        PanelTitle=PendingReward?TEXT("SIGNAL REWARD / CHOOSE ONE"):TEXT("LOST CREW BEACON");
        PanelDetail=PendingReward?TEXT("One deliberate reward. A module replaces the current module; a weapon replaces the active weapon."):
            TEXT("An unfinished beacon repeats a crew's home coordinates. Mica kept the receiver powered. Restore its antenna to recover the cargo tip.");
        if(PendingReward) { AddEntry(TEXT("Fit Vector Thrusters"),46); AddEntry(TEXT("Fit Overdrive Cooling"),47); if(RewardCombat) AddEntry(TEXT("Replace active weapon with Heavy Cannon"),48); }
        else AddEntry(TEXT("Restore the beacon / recover 25 credits"),49,!S.run.stationRewardClaimed); break;
    case ESSPanel::Launch:
        PanelTitle=InHangar()?TEXT("PREPARE FOR LAUNCH"):TEXT("DEPARTURE CONTROL");
        PanelDetail=InHangar()?FString::Printf(TEXT("%s  |  %s"),SelectedShip?TEXT("Acorn Swift"):TEXT("Acorn Voyager"),*WeaponName(SS::Weapon(SelectedWeapon))):
            S.AtSliceBoundary()?TEXT("You reached the Phase 1 flight boundary. This is a live station stop, not the game's final wave. Save & Quit retains the run."):TEXT("Continue with your current ship, credits and upgrades.");
        AddEntry(TEXT("Launch"),50,InHangar() || !S.AtSliceBoundary()); break;
    default:break;
    }
    AddEntry(TEXT("Back"),0);
}
void ASSGameMode::ActivateEntry(int32 Index)
{
    if(!Entries.IsValidIndex(Index) || !Entries[Index].Enabled) return;
    auto* GI=GetGameInstance<USSGameInstance>(); if(!GI) return;
    auto& S=GI->Session; const int A=Entries[Index].Action; const ESSPanel Current=Panel;
    if(A==0 || A==1) {ClosePanel();return;}
    if(A==2)
    {
        if(GI->ResumeRun()) {StationTarget=FVector::ZeroVector; EnterStation(); PreviousPhase=int32(S.run.phase);PreviousWave=S.run.wave;}
        else Announce(GI->LastSaveError); return;
    }
    if(A==3) {StartNewRun();return;}
    if(A==4) {ShowHangar();return;}
    if(A==5) {OpenPanel(ESSPanel::Settings);return;}
    if(A==6) {OpenPanel(ESSPanel::Progression);return;}
    if(A==7) {UKismetSystemLibrary::QuitGame(this,UGameplayStatics::GetPlayerController(this,0),EQuitPreference::Quit,false);return;}
    if(A==8) {DeathPersisted=GI->PersistDeath();OpenPanel(ESSPanel::Results);return;}
    if(A==10) {OpenPanel(ESSPanel::Graphics);return;} if(A==11) {OpenPanel(ESSPanel::Audio);return;} if(A==12) {OpenPanel(ESSPanel::Controls);return;}
    if(A>=13 && A<=27)
    {
        switch(A)
        {
        case 13:S.settings.subtitles=!S.settings.subtitles;break;
        case 14:S.settings.uiScale=S.settings.uiScale>=1.4?.8:S.settings.uiScale+.1;break;
        case 15:S.settings.cameraShake=!S.settings.cameraShake;break;
        case 16:S.settings.quality=(S.settings.quality+1)%4;break;
        case 17:S.settings.frameLimit=S.settings.frameLimit==60?120:S.settings.frameLimit==120?144:60;break;
        case 18:S.settings.motionBlur=!S.settings.motionBlur;break;
        case 19:S.settings.masterVolume=S.settings.masterVolume>=.99?0:S.settings.masterVolume+.1;break;
        case 20:S.settings.musicVolume=S.settings.musicVolume>=.99?0:S.settings.musicVolume+.1;break;
        case 21:S.settings.effectsVolume=S.settings.effectsVolume>=.99?0:S.settings.effectsVolume+.1;break;
        case 22:S.settings.mouseSensitivity=S.settings.mouseSensitivity>=2.9?.3:S.settings.mouseSensitivity+.2;break;
        case 23:S.settings.controllerSensitivity=S.settings.controllerSensitivity>=2.9?.3:S.settings.controllerSensitivity+.2;break;
        case 24:S.settings.invertPitch=!S.settings.invertPitch;break;
        case 25:S.settings.toggleBoost=!S.settings.toggleBoost;break;
        case 26:S.settings.toggleBrake=!S.settings.toggleBrake;break;
        case 27:S.account.tutorialFlags=0;GI->PersistAccount();break;
        }
        if(!GI->PersistSettings()) Announce(GI->LastSaveError);
        OpenPanel(Current);return;
    }
    if(A>=30 && A<=33) {if(A<=31)SelectedShip=A-30;else SelectedWeapon=A-32;Announce(TEXT("Starting loadout selected."));ClosePanel();return;}
    if(A>=100 && A<105)
    {
        const int I=A-100;
        const bool Depot=Current==ESSPanel::Depot;
        if(Depot && (!IsValid(ActiveBeacon) || !ActiveBeacon->IsPlayerInRange() || !ActiveBeacon->GetOffers().Contains(I))) {Announce(TEXT("Depot is out of range."));ClosePanel();return;}
        const bool Ok=S.Purchase(SS::Upgrade(I),Depot?ActiveBeacon->GetDiscount():1.f);
        Announce(Ok?TEXT("Upgrade installed."):TEXT("Upgrade unavailable."));OpenPanel(Current);return;
    }
    if(A==40) {Announce(S.Repair()?TEXT("Service complete. All systems restored."):TEXT("Service unavailable."));OpenPanel(Current);return;}
    if(A==41 || A==42) {Announce(S.AcceptContract(A==41?SS::Contract::Pressure:SS::Contract::Objective)?TEXT("Contract accepted. Terms remain active until the next station."):TEXT("Contract unavailable."));OpenPanel(Current);return;}
    if(A==43) {if(GI->SuspendRun()) UKismetSystemLibrary::QuitGame(this,UGameplayStatics::GetPlayerController(this,0),EQuitPreference::Quit,false);else Announce(GI->LastSaveError);return;}
    if(A==44 || A==45) {if(S.run.phase==SS::Phase::Station && S.run.credits>=150 && S.EquipUtility(A==44?SS::Utility::VectorThrusters:SS::Utility::OverdriveCooling)) {S.run.credits-=150;Announce(TEXT("Module fitted."));}OpenPanel(Current);return;}
    if(A>=46 && A<=48)
    {
        if(!S.run.pendingReward) return;
        const bool Success=A==48?S.ReplaceWeapon(SS::Weapon::HeavyCannon):S.EquipUtility(A==46?SS::Utility::VectorThrusters:SS::Utility::OverdriveCooling);
        if(Success) {S.run.pendingReward=false;PendingReward=false;Announce(TEXT("Reward fitted. Keep surviving."));ClosePanel();} return;
    }
    if(A==49) {if(!S.run.stationRewardClaimed && S.run.phase==SS::Phase::Station) {S.run.stationRewardClaimed=true;S.AwardCredits(25);Announce(TEXT("Receiver restored. The crew's signal carries on."));}OpenPanel(Current);return;}
    if(A==50) {LaunchFromHub();return;}
    if(A==51 && S.AtSliceBoundary())
    {
        if(!GI->InvalidateSuspend()) {Announce(GI->LastSaveError);return;}
        S.run=SS::Run{}; ShowHangar(); OpenPanel(ESSPanel::Launch); return;
    }
}

ASSPlayerController::ASSPlayerController()
{
    PrimaryActorTick.bTickEvenWhenPaused=true;
    bShouldPerformFullTickWhenPaused=true;
}
void ASSPlayerController::PlayerTick(float Dt)
{
    Super::PlayerTick(Dt);
    auto* GM=GetWorld()->GetAuthGameMode<ASSGameMode>(); auto* GI=GetGameInstance<USSGameInstance>(); if(!GM || !GI)return;
    const auto Pressed=[this](FKey K){return WasInputKeyJustPressed(K);};
    const auto Down=[this](FKey K){return IsInputKeyDown(K);};
    if(Pressed(EKeys::Escape)||Pressed(EKeys::Gamepad_Special_Right)) {if(GM->IsMenuOpen())GM->ClosePanel();else GM->OpenPanel(ESSPanel::Main);}
    if(GM->IsMenuOpen())
    {
        if(Pressed(EKeys::Up)||Pressed(EKeys::Gamepad_DPad_Up)) GM->SelectedEntry=FMath::Max(0,GM->SelectedEntry-1);
        if(Pressed(EKeys::Down)||Pressed(EKeys::Gamepad_DPad_Down)) GM->SelectedEntry=FMath::Min(GM->Entries.Num()-1,GM->SelectedEntry+1);
        if(Pressed(EKeys::Enter)||Pressed(EKeys::Gamepad_FaceButton_Bottom))GM->ActivateEntry(GM->SelectedEntry);
        if(Pressed(EKeys::Gamepad_FaceButton_Right))GM->ClosePanel();
        if(Pressed(EKeys::LeftMouseButton)) if(auto* HUD=Cast<ASSHUD>(GetHUD())) {float X,Y;if(GetMousePosition(X,Y))GM->ActivateEntry(HUD->MenuIndexAt(FVector2D(X,Y)));}
        if(auto* ShipPawn=Cast<ASSShip>(GetPawn()))ShipPawn->SetFlightInput(FVector2D::ZeroVector,FVector2D::ZeroVector,0,false,false);
        return;
    }
    float MouseX=0,MouseY=0;GetInputMouseDelta(MouseX,MouseY);
    const float MouseScale=float(GI->Session.settings.mouseSensitivity)*.0022f/FMath::Max(.001f,Dt);
    FVector2D Look(MouseX*MouseScale+GetInputAnalogKeyState(EKeys::Gamepad_RightX)*GI->Session.settings.controllerSensitivity,
        -MouseY*MouseScale+GetInputAnalogKeyState(EKeys::Gamepad_RightY)*GI->Session.settings.controllerSensitivity);
    if(GI->Session.settings.invertPitch)Look.Y=-Look.Y;
    if(auto* ShipPawn=Cast<ASSShip>(GetPawn()))
    {
        const bool Boost=Down(EKeys::LeftShift)||GetInputAnalogKeyState(EKeys::Gamepad_RightTriggerAxis)>.3f;
        const bool Brake=Down(EKeys::SpaceBar)||GetInputAnalogKeyState(EKeys::Gamepad_LeftTriggerAxis)>.3f;
        if(Pressed(EKeys::LeftShift)||Pressed(EKeys::Gamepad_RightTrigger))BoostLatch=!BoostLatch;
        if(Pressed(EKeys::SpaceBar)||Pressed(EKeys::Gamepad_LeftTrigger))BrakeLatch=!BrakeLatch;
        FVector2D Strafe(float(Down(EKeys::D))-float(Down(EKeys::A))+GetInputAnalogKeyState(EKeys::Gamepad_LeftX),
            float(Down(EKeys::R))-float(Down(EKeys::F))+GetInputAnalogKeyState(EKeys::Gamepad_LeftY));
        const float Throttle=float(Down(EKeys::W)||Down(EKeys::Gamepad_DPad_Up))-float(Down(EKeys::S)||Down(EKeys::Gamepad_DPad_Down));
        const uint32 Before=GI->Session.account.tutorialFlags;
        if(!Look.IsNearlyZero()) GI->Session.account.tutorialFlags|=1u;
        if(FMath::Abs(Throttle)>.1f) GI->Session.account.tutorialFlags|=2u;
        if(Boost) GI->Session.account.tutorialFlags|=4u;
        if(Brake) GI->Session.account.tutorialFlags|=8u;
        if(Pressed(EKeys::Q)||Pressed(EKeys::Gamepad_LeftShoulder)) GI->Session.account.tutorialFlags|=16u;
        if(Down(EKeys::LeftMouseButton)||Down(EKeys::Gamepad_RightShoulder)) GI->Session.account.tutorialFlags|=32u;
        if(Before!=GI->Session.account.tutorialFlags)GI->PersistAccount();
        ShipPawn->SetFlightInput(Look,Strafe,Throttle,GI->Session.settings.toggleBoost?BoostLatch:Boost,GI->Session.settings.toggleBrake?BrakeLatch:Brake);
        if(Pressed(EKeys::Q)||Pressed(EKeys::Gamepad_LeftShoulder))ShipPawn->RequestDodge();
        if(Down(EKeys::LeftMouseButton)||Down(EKeys::Gamepad_RightShoulder))ShipPawn->Fire();
    }
    else if(auto* WalkPawn=Cast<ASSWalker>(GetPawn()))
        WalkPawn->Move(FVector2D(float(Down(EKeys::D))-float(Down(EKeys::A))+GetInputAnalogKeyState(EKeys::Gamepad_LeftX),
            float(Down(EKeys::W))-float(Down(EKeys::S))+GetInputAnalogKeyState(EKeys::Gamepad_LeftY)),Look,Down(EKeys::LeftShift)||Down(EKeys::Gamepad_FaceButton_Left),Dt);
    if(Pressed(EKeys::E)||Pressed(EKeys::Gamepad_FaceButton_Bottom))GM->Interact();
}
