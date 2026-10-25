#include "Misc/AutomationTest.h"
#include "SSAudio.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSOutpostSandbox.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "Components/AudioComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundConcurrency.h"
#include "Misc/PackageName.h"
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
        TestTrue(TEXT("Engine begins silent with zero throttle and explicit activation"),
                 FMath::IsNearlyZero(Ship->EngineAudio->VolumeMultiplier) && !Ship->EngineAudio->bAutoActivate);
        Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 1.f, false, false);
        Ship->Tick(1.f / 60.f);
        TestTrue(TEXT("Powered engine honors the persisted effects mix"),
                 FMath::IsNearlyEqual(Ship->EngineAudio->VolumeMultiplier, float(Master * .6 * .35)));
        Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 0.f, false, false);
        Ship->Tick(1.f / 60.f);
        TestTrue(TEXT("Releasing throttle silences the main engine"),
                 FMath::IsNearlyZero(Ship->EngineAudio->VolumeMultiplier));
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

        // Inject ready PCM into the actual playback path; no voice service or audible output is needed.
        Mode->StopCrewRadio();
        Mode->CrewRadioReady.SampleRate = 48000;
        Mode->CrewRadioReady.Pcm.SetNumZeroed(96000); // One second of mono PCM16.
        Mode->UpdateCrewRadio(.25f);
        TestEqual(TEXT("New crew speech retains its full duration after the start frame"), Mode->CrewRadioLeft, 1.f);
        TestFalse(TEXT("Starting crew speech consumes the ready PCM"), Mode->CrewRadioReady.IsValid());
        Mode->UpdateCrewRadio(.25f);
        TestEqual(TEXT("The next update subtracts elapsed playback time"), Mode->CrewRadioLeft, .75f);
        Mode->UpdateCrewRadio(.5f);
        TestEqual(TEXT("Crew speech remains active before its full duration"), Mode->CrewRadioLeft, .25f);
        Mode->UpdateCrewRadio(.25f);
        TestEqual(TEXT("Crew speech expires after its full playback duration"), Mode->CrewRadioLeft, 0.f);

        Mode->CrewRadioReady.SampleRate = 48000;
        Mode->CrewRadioReady.Pcm.SetNumZeroed(960); // Ten milliseconds, shorter than the start frame.
        Mode->UpdateCrewRadio(1.f / 60.f);
        TestTrue(TEXT("A sub-frame clip cannot expire in the update that starts it"),
                 FMath::IsNearlyEqual(Mode->CrewRadioLeft, .01f));
        TestFalse(TEXT("A sub-frame clip is consumed only once"), Mode->CrewRadioReady.IsValid());
        Mode->UpdateCrewRadio(.005f);
        TestTrue(TEXT("A sub-frame clip retains its remaining playback time"),
                 FMath::IsNearlyEqual(Mode->CrewRadioLeft, .005f));
        Mode->UpdateCrewRadio(.01f);
        TestEqual(TEXT("Elapsed playback clamps the short clip countdown to zero"), Mode->CrewRadioLeft, 0.f);
    }
    AddInfo(TEXT("Component and phase state verified; no rendered audio buffer or listening assertion."));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSRestingCrewInteraction, "SpaceSurvival.NpcTalk.RestingCrew",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSRestingCrewInteraction::RunTest(const FString &Parameters)
{
    FSSAudioWorld Fixture;
    if (!Fixture.Initialize(*this, 0.0))
        return false;
    auto *Mode = Fixture.Mode;
    Mode->Walker = Fixture.World->SpawnActor<ASSWalker>();
    auto *Crew = Fixture.World->SpawnActor<ASSOutpostAmbientActor>();
    if (!TestNotNull(TEXT("Walker exists"), Mode->Walker.Get()) || !TestNotNull(TEXT("Crew exists"), Crew))
        return false;
    Mode->Panel = ESSPanel::None;
    Crew->Actions.SetNum(1);
    Crew->Chatter.Add(TEXT("A line that must not play while asleep."));
    TestTrue(TEXT("Existing crew remain conversation-enabled by default"), Crew->bConversationEnabled);
    TestTrue(TEXT("An available nearby crew member can speak"), Mode->CanAmbientCrewSpeak(Crew));
    Mode->EngagedWith.Name = TEXT("Resting crew");
    Mode->EngagedMesh = Crew->CharacterMesh;
    Mode->EngageAnchor = Mode->Walker->GetActorLocation();
    TestEqual(TEXT("An available partner still offers its authored actions"), Mode->ActionTarget(), Crew);

    Crew->bConversationEnabled = false;
    TestNull(TEXT("A cached partner cannot offer actions after becoming unavailable"), Mode->ActionTarget());
    Mode->CachedHint = Mode->EngagedWith;
    Mode->CachedHintMesh = Crew->CharacterMesh;
    Mode->CachedHintAt = Fixture.World->GetTimeSeconds();
    Mode->WalkerStillSeconds = 3.f;
    TestFalse(TEXT("The cached talk hint disappears immediately"), Mode->TalkHint().IsValid());
    TestFalse(TEXT("Unavailable crew cannot start incidental speech"), Mode->CanAmbientCrewSpeak(Crew));
    TestFalse(TEXT("Unavailable crew reject an ambient line"), Mode->TryAmbientCrewLine(Crew, TEXT("Hello")));
    TestFalse(TEXT("Unavailable crew cannot chatter"), Mode->CrewChatter(Crew));
    const int32 LinesBefore = Mode->ChatLines.Num();
    Mode->SpeakCrewLine(Crew, TEXT("This must not appear."));
    TestEqual(TEXT("Direct scripted speech cannot add a sleeping patron caption"), Mode->ChatLines.Num(), LinesBefore);
    TestFalse(TEXT("No voice request was queued"), Mode->bCrewVoiceWaiting || Mode->CrewRadioReady.IsValid());
    Mode->UpdateTalkEngagement(0.f);
    TestFalse(TEXT("Becoming unavailable ends an existing conversation"), Mode->IsTalkEngaged());
    TestFalse(TEXT("The old partner mesh is released"), Mode->EngagedMesh.IsValid());

    Crew->bConversationEnabled = true;
    TestTrue(TEXT("Availability can be restored without changing the actor"), Mode->CanAmbientCrewSpeak(Crew));
    AddInfo(TEXT("No talk subsystem, helper process, microphone, save or audible output was started."));
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
    FSSAudioCueDefinition RockCue;
    auto *DistantBreak =
        Audio->PlayOneShot(RockCue, TEXT("DebrisBreak"), Ship->GetActorLocation() + FVector(30000, 0, 0));
    if (TestNotNull(TEXT("Breaking a reachable world rock at 300m remains audible"), DistantBreak))
        TestTrue(TEXT("Only rock breakup selects the 600m spatial attenuation"),
                 DistantBreak->AttenuationSettings == Audio->RockBreakAttenuation &&
                     DistantBreak->AttenuationSettings != Audio->Attenuation &&
                     Audio->RockBreakAttenuation->Attenuation.FalloffDistance == 59350.f);
    TestNull(TEXT("Rock breakup outside its separate 600m range allocates no voice"),
             Audio->PlayOneShot(RockCue, TEXT("DebrisBreak"), Ship->GetActorLocation() + FVector(61000, 0, 0)));
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSCombatAudioPalette, "SpaceSurvival.Presentation.CombatAudioPalette",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSCombatAudioPalette::RunTest(const FString &)
{
    const TCHAR *Roles[] = {TEXT("Laser"), TEXT("Cannon"), TEXT("Impact"), TEXT("DebrisBreak")};
    const float Durations[] = {.115f, .46f, .44f, .60f};
    TSet<USoundBase *> Distinct;
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Roles); ++Index)
    {
        const FString Path = FString::Printf(TEXT("/Game/SpaceSurvival/Licensed/Audio/CombatPolish1/%s"), Roles[Index]);
        if (!TestTrue(TEXT("Prepared short combat palette was actually imported"),
                      FPackageName::DoesPackageExist(Path)))
            return false;
        auto *Sound = SSAudio::PresentationSound(Roles[Index]);
        if (!TestNotNull(TEXT("Runtime role resolves to a real sound"), Sound))
            return false;
        TestTrue(TEXT("Runtime selects the new derivative without replacing originals"),
                 Sound->GetPathName().StartsWith(Path));
        TestFalse(TEXT("Combat cue is finite, never looping"), Sound->IsLooping());
        TestTrue(TEXT("Imported cue preserves the measured short release"),
                 FMath::IsNearlyEqual(Sound->GetDuration(), Durations[Index], .01f));
        Distinct.Add(Sound);
    }
    TestEqual(TEXT("Laser, cannon, hull impact and breakup have four distinct source cues"), Distinct.Num(), 4);
    AddInfo(TEXT("Imported role routing and duration only. PCM headroom/band evidence is in the preparation receipt; "
                 "listening and live mix acceptance remain separate."));
    return true;
}
#endif
