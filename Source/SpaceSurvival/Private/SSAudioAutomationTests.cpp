#include "Misc/AutomationTest.h"
#include "SSAudio.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "Components/AudioComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundConcurrency.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSAudioWorld
{
    UWorld *World = nullptr, *PreviousWorld = nullptr;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    APlayerController *Controller = nullptr;
    USSWorldAudioSubsystem *Audio = nullptr;

    bool Initialize(FAutomationTestBase &Test, double Master)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated audio component world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // No GI Init, disk-backed settings load, save API or production slot access.
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = Master;
        Instance->Session.settings.effectsVolume = .6;
        Instance->Session.settings.musicVolume = .4;
        Instance->Session.account.tutorialFlags = 255;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        PreviousWorld = GWorld;
        GWorld = World;
        World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
        if (!Test.TestTrue(TEXT("Install actual audio GameMode"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        if (!Test.TestNotNull(TEXT("Resolve actual audio GameMode"), Mode))
            return false;
        Mode->Tuning = NewObject<USSPhase1Data>(Mode);
        Audio = World->GetSubsystem<USSWorldAudioSubsystem>();
        if (!Test.TestNotNull(TEXT("Resolve actual world audio subsystem"), Audio))
            return false;
        World->InitializeActorsForPlay(FURL());
        Controller = World->SpawnActor<APlayerController>();
        if (!Test.TestNotNull(TEXT("Create isolated local audio controller"), Controller))
            return false;
        Controller->SetAsLocalPlayerController();
        World->AddController(Controller);
        Controller->SetActorTickEnabled(false);
        return true;
    }
    ASSShip *SpawnShip()
    {
        auto *Ship = World->SpawnActor<ASSShip>(FVector(100000, 0, 0), FRotator::ZeroRotator);
        if (Ship)
        {
            Ship->Tuning = Mode->Tuning;
            Controller->Possess(Ship);
        }
        return Ship;
    }
    ~FSSAudioWorld()
    {
        if (World)
        {
            World->EndPlay(EEndPlayReason::Quit);
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
            GWorld = PreviousWorld;
        }
        if (Instance)
            Instance->RemoveFromRoot();
    }
};
UAudioComponent *FindSoundComponent(AActor *Actor, const TCHAR *Name)
{
    TArray<UAudioComponent *> Components;
    Actor->GetComponents(Components);
    for (auto *Component : Components)
        if (Component->GetSound() && Component->GetSound()->GetName() == Name)
            return Component;
    return nullptr;
}
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSAudioFirstState, "SpaceSurvival.Integration.AudioFirstPlayMix",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSAudioFirstState::RunTest(const FString &Parameters)
{
    for (double Master : {0.0, .5})
    {
        FSSAudioWorld Fixture;
        if (!Fixture.Initialize(*this, Master))
            return false;
        auto &S = Fixture.Instance->Session;
        auto *Mode = Fixture.Mode;
        // Verify phase treatment before the home hub exists, then actual BeginPlay components.
        TestNull(TEXT("Initial music phase does not depend on an already-created hangar"), Mode->Hub.Get());
        Mode->UpdateMusicMix();
        TestTrue(TEXT("Unmuted initial Hangar uses decompression level before any Play"),
                 FMath::IsNearlyEqual(Mode->MusicBase->VolumeMultiplier, float(Master * .4 * .35)));
        TestEqual(TEXT("Initial pressure stem starts silent"), Mode->MusicPressure->VolumeMultiplier, 0.f);
        TestEqual(TEXT("Initial climax stem starts silent"), Mode->MusicClimax->VolumeMultiplier, 0.f);
        Fixture.World->BeginPlay();
        TestTrue(TEXT("Actual BeginPlay retains the persisted first-play base mix"),
                 FMath::IsNearlyEqual(Mode->MusicBase->VolumeMultiplier, float(Master * .4 * .35)));
        TestTrue(TEXT("Music activation cannot precede explicit gain assignment"),
                 !Mode->MusicBase->bAutoActivate && !Mode->MusicPressure->bAutoActivate &&
                     !Mode->MusicClimax->bAutoActivate);
        auto *StationAudio = Mode->Hub ? FindSoundComponent(Mode->Hub, TEXT("Station")) : nullptr;
        if (!TestNotNull(TEXT("Real home hangar creates station ambience"), StationAudio))
            return false;
        TestTrue(TEXT("Station begins at the persisted effects mix"),
                 FMath::IsNearlyEqual(StationAudio->VolumeMultiplier, float(Master * .6 * .25)) &&
                     !StationAudio->bAutoActivate);
        if (!TestTrue(TEXT("Start in-memory phase fixture only"), S.StartRun("audio-phases")))
            return false;
        auto *Ship = Fixture.SpawnShip();
        if (!TestNotNull(TEXT("Actual ship BeginPlay creates engine audio"), Ship))
            return false;
        TestTrue(TEXT("Engine begins at persisted effects mix with explicit activation"),
                 FMath::IsNearlyEqual(Ship->EngineAudio->VolumeMultiplier, float(Master * .6 * .35)) &&
                     !Ship->EngineAudio->bAutoActivate);
        S.settings.masterVolume = .5;
        Mode->Director->Configure(8, false);
        Mode->Director->SetActive(true);
        Mode->Director->TickComponent(.01f, LEVELTICK_All, nullptr);
        Mode->UpdateMusicMix();
        TestTrue(TEXT("Real Director pressure enters the pressure stem"),
                 Mode->Director->GetPressure() > 0.f && Mode->MusicPressure->VolumeMultiplier > 0.f);
        S.run.phase = SS::Phase::Breathing;
        Mode->UpdateMusicMix();
        TestEqual(TEXT("Breathing strips the pressure stem even before Director tick"),
                  Mode->MusicPressure->VolumeMultiplier, 0.f);
        S.run.phase = SS::Phase::Climax;
        Mode->UpdateMusicMix();
        TestTrue(TEXT("Climax adds only its authored scaled stem"),
                 FMath::IsNearlyEqual(Mode->MusicClimax->VolumeMultiplier, .5f * .4f * .75f));
        S.run.phase = SS::Phase::Station;
        Mode->UpdateMusicMix();
        TestTrue(TEXT("Station music decompresses and removes threat layers"),
                 FMath::IsNearlyEqual(Mode->MusicBase->VolumeMultiplier, .5f * .4f * .35f) &&
                     Mode->MusicPressure->VolumeMultiplier == 0.f && Mode->MusicClimax->VolumeMultiplier == 0.f);
        S.settings.masterVolume = 0;
        Mode->UpdateMusicMix();
        Ship->Tick(0.f); // Mix still updates when the flight simulation is inactive.
        Mode->Hub->Tick(0.f);
        TestTrue(TEXT("Live mute reaches music, inactive ship engine and station ambience"),
                 Mode->MusicBase->VolumeMultiplier == 0.f && Mode->MusicPressure->VolumeMultiplier == 0.f &&
                     Mode->MusicClimax->VolumeMultiplier == 0.f && Ship->EngineAudio->VolumeMultiplier == 0.f &&
                     StationAudio->VolumeMultiplier == 0.f);
    }
    AddInfo(TEXT("Component and phase state verified; no rendered audio buffer or listening assertion."));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSWorldAudioHooks, "SpaceSurvival.Integration.SpatialThreatAudio",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSWorldAudioHooks::RunTest(const FString &Parameters)
{
    FSSAudioWorld Fixture;
    if (!Fixture.Initialize(*this, .5))
        return false;
    Fixture.World->BeginPlay();
    auto &S = Fixture.Instance->Session;
    S.tuning.baseHull = S.tuning.baseShield = 50000;
    if (!TestTrue(TEXT("Start only an in-memory actor/audio fixture"), S.StartRun("audio-hooks")))
        return false;
    auto *Ship = Fixture.SpawnShip();
    if (!TestNotNull(TEXT("Spawn actual audio listener pawn"), Ship))
        return false;
    auto *Audio = Fixture.Audio;
    TestTrue(TEXT("Shared attenuation is spatial and bounded"),
             Audio->Attenuation->Attenuation.bAttenuate && Audio->Attenuation->Attenuation.bSpatialize &&
                 Audio->Attenuation->Attenuation.AttenuationShapeExtents.X == 650.f &&
                 Audio->Attenuation->Attenuation.FalloffDistance == 7500.f);
    TestTrue(TEXT("Shared native voice limits retain separate twelve-shot and four-field budgets"),
             Audio->ShotConcurrency->Concurrency.MaxCount == 12 && Audio->FieldConcurrency->Concurrency.MaxCount == 4 &&
                 !Audio->ShotConcurrency->Concurrency.bLimitToOwner &&
                 Audio->ShotConcurrency->Concurrency.ResolutionRule ==
                     EMaxConcurrentResolutionRule::StopFarthestThenOldest);
    const auto CountSound = [Audio](const TCHAR *Name)
    {
        int32 Count = 0;
        for (const auto &Voice : Audio->Voices)
            if (IsValid(Voice.Component) && Voice.Component->GetSound() &&
                Voice.Component->GetSound()->GetName() == Name)
                ++Count;
        return Count;
    };
    auto *Data = Fixture.Mode->Tuning.Get();
    auto *Storm =
        Fixture.World->SpawnActor<ASSWorldBody>(Ship->GetActorLocation() + FVector(100, 0, 0), FRotator::ZeroRotator);
    if (!TestNotNull(TEXT("Create actual electrical actor"), Storm))
        return false;
    Storm->Configure(ESSWorldKind::ElectricalStorm, 500.f, 7.f, 4);
    auto *Charge = FindSoundComponent(Storm, TEXT("ElectricalCharge"));
    if (!TestNotNull(TEXT("Old/default hazard rows resolve their electrical loop preset"), Charge))
        return false;
    TestTrue(TEXT("Field begins quietly at the persisted effects mix"),
             FMath::IsNearlyEqual(Charge->VolumeMultiplier, .5f * .6f * .35f * .08f) && !Charge->bAutoActivate &&
                 Charge->ConcurrencySet.Contains(Audio->FieldConcurrency));
    const double Shield = S.run.shield;
    Storm->Tick(3.49f);
    TestEqual(TEXT("Charge cannot emit a premature discharge cue"), CountSound(TEXT("ElectricalDischarge")), 0);
    const float RisingGain = Charge->VolumeMultiplier;
    Storm->Tick(.02f);
    TestTrue(TEXT("Real electrical damage and spatial discharge cue occur on the same boundary"),
             S.run.shield == Shield - 7 && CountSound(TEXT("ElectricalDischarge")) == 1);
    TestTrue(TEXT("Audio charge falls after its authoritative pulse resets"), Charge->VolumeMultiplier < RisingGain);
    auto *Gravity =
        Fixture.World->SpawnActor<ASSWorldBody>(Ship->GetActorLocation() + FVector(0, 2500, 0), FRotator::ZeroRotator);
    if (!TestNotNull(TEXT("Create actual gravity actor"), Gravity))
        return false;
    Gravity->Configure(ESSWorldKind::GravityAnomaly, 500, 0, 4);
    TestNotNull(TEXT("Gravity uses its distinct field loop"), FindSoundComponent(Gravity, TEXT("GravityAmbience")));

    for (auto &Enemy : Data->Enemies)
    {
        Enemy.InitialShotDelay = .01f;
        Enemy.ShotTelegraph = .3f;
    }
    auto *Enemy =
        Fixture.World->SpawnActor<ASSEnemy>(Ship->GetActorLocation() + FVector(2000, 0, 0), FRotator::ZeroRotator);
    if (!TestNotNull(TEXT("Spawn real enemy for discharge/destruction hooks"), Enemy))
        return false;
    Enemy->Configure(ESSWorldKind::Pursuer, 100, 0, 1);
    Enemy->Tick(.02f);
    TestEqual(TEXT("Enemy charge does not play a projectile discharge early"), CountSound(TEXT("EnemyFire")), 0);
    Enemy->Tick(.31f);
    TestEqual(TEXT("Actual projectile creation triggers one spatial fire cue"), CountSound(TEXT("EnemyFire")), 1);
    Enemy->ReceiveWeaponHit(100000);
    TestEqual(TEXT("Actual defeated enemy triggers its destruction cue"), CountSound(TEXT("EnemyBreak")), 1);
    Enemy->ReceiveWeaponHit(100000);
    TestEqual(TEXT("Repeated damage cannot duplicate enemy destruction"), CountSound(TEXT("EnemyBreak")), 1);
    auto *Rock =
        Fixture.World->SpawnActor<ASSWorldBody>(Ship->GetActorLocation() + FVector(0, -2000, 0), FRotator::ZeroRotator);
    if (!TestNotNull(TEXT("Spawn actual destructible asteroid"), Rock))
        return false;
    Rock->Configure(ESSWorldKind::SmallAsteroid, 100, 0, 1);
    Rock->ReceiveWeaponHit(100000);
    TestEqual(TEXT("Actual asteroid break triggers a distinct cue"), CountSound(TEXT("DebrisBreak")), 1);

    FSSAudioCueDefinition Override;
    Override.UseDefaultSound = false;
    TestNull(TEXT("Explicit null is silent instead of falling back"), Audio->ResolveCue(Override, TEXT("EnemyFire")));
    auto *StationSound = LoadObject<USoundBase>(nullptr, TEXT("/Game/SpaceSurvival/Audio/Station.Station"));
    auto *CannonSound = LoadObject<USoundBase>(nullptr, TEXT("/Game/SpaceSurvival/Audio/Cannon.Cannon"));
    if (!TestNotNull(TEXT("Custom loop fixture asset exists"), StationSound) ||
        !TestNotNull(TEXT("Custom one-shot fixture asset exists"), CannonSound))
        return false;
    Override.Sound = StationSound;
    TestNull(TEXT("Looping sound cannot become an indefinite one-shot"),
             Audio->PlayOneShot(Override, TEXT("EnemyFire"), Ship->GetActorLocation()));
    Override.Sound = CannonSound;
    TestNull(TEXT("Non-loop sound cannot become repeating field chatter"),
             Audio->CreateFieldLoop(Gravity, Override, TEXT("GravityAmbience"), 1.f));
    for (auto &Hazard : Data->Hazards)
        if (Hazard.Kind == ESSWorldKind::GravityAnomaly)
        {
            Hazard.FieldLoopAudio.UseDefaultSound = false;
            Hazard.FieldLoopAudio.Sound = StationSound;
            Hazard.FieldLoopAudio.Gain = .8f;
        }
    Gravity->Configure(ESSWorldKind::GravityAnomaly, 500, 0, 4);
    auto *CustomField = FindSoundComponent(Gravity, TEXT("Station"));
    if (!TestNotNull(TEXT("Actual Data Asset override reaches actor field component"), CustomField))
        return false;
    TestTrue(TEXT("Authored field gain reaches the first-play mix"),
             FMath::IsNearlyEqual(CustomField->VolumeMultiplier, .5f * .6f * .8f * .08f));
    Override.Gain = std::numeric_limits<float>::quiet_NaN();
    TestNull(TEXT("Nonfinite cue gain cannot create an audible voice"),
             Audio->PlayOneShot(Override, TEXT("EnemyFire"), Ship->GetActorLocation()));
    Override.Gain = 2.f;
    auto *Bounded = Audio->PlayOneShot(Override, TEXT("EnemyFire"), Ship->GetActorLocation());
    if (!TestNotNull(TEXT("Out-of-range finite gain remains usable and bounded"), Bounded))
        return false;
    TestTrue(TEXT("Malformed gain clamps to the persisted effects limit"),
             FMath::IsNearlyEqual(Bounded->VolumeMultiplier, .5f * .6f));
    TestNull(TEXT("Inaudible distant shots allocate no component"),
             Audio->PlayOneShot(Override, TEXT("EnemyFire"), Ship->GetActorLocation() + FVector(9000, 0, 0)));
    for (int32 Index = 0; Index < 40; ++Index)
        Audio->PlayOneShot(Override, TEXT("EnemyFire"), Ship->GetActorLocation());
    int32 Shots = 0;
    for (const auto &Voice : Audio->Voices)
        Shots += !Voice.Loop ? 1 : 0;
    TestEqual(TEXT("Actual one-shot component allocation remains bounded during a burst"), Shots, 12);
    S.settings.masterVolume = 0;
    Audio->Tick(.01f);
    TestTrue(TEXT("Live mute reaches existing actual field overrides"), CustomField->VolumeMultiplier == 0.f);
    TestNull(TEXT("Muted one-shot skips allocation"),
             Audio->PlayOneShot(Override, TEXT("EnemyFire"), Ship->GetActorLocation()));
    Storm->Destroy();
    Gravity->Destroy();
    Audio->Tick(11.f);
    TestEqual(TEXT("Destroyed field owners and bounded one-shots leave no retained voices"), Audio->Voices.Num(), 0);
    AddInfo(TEXT("Real actor hooks/component bounds verified; NullRHI does not prove renderer voice count, spatial "
                 "perception or listening quality."));
    return true;
}
#endif
