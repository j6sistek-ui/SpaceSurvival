#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/Engine.h"
#include "Engine/Level.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/UnrealType.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
/** Real actors and world ticks; initial flight is fixture setup, not a disk-backed New Run test. */
struct FSSJourneyWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = nullptr;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    APlayerController *Controller = nullptr;

    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create transient journey world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // Never call Init/InitializeStandalone: they read production account/settings.
        // PersistAccount fails before disk writes, including GameMode's death path.
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = 0;
        Instance->Session.account.tutorialFlags = 255;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        PreviousWorld = GWorld;
        GWorld = World;
        World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
        if (!Test.TestTrue(TEXT("Install the real authoritative GameMode"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        auto *Content = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
        if (!Test.TestNotNull(TEXT("Load authored Phase 1 data asset"), Content) ||
            !Test.TestNotNull(TEXT("Resolve real GameMode"), Mode))
            return false;
        Mode->Tuning = DuplicateObject<USSPhase1Data>(Content, Mode);
        Mode->Tuning->WaveSecondsMin = Mode->Tuning->WaveSecondsMax = 12.f;
        Mode->Tuning->WaveSecondsGrowth = 0.f;
        Mode->Tuning->BaseHull = Mode->Tuning->BaseShield = 50000.f;
        for (auto &Encounter : Mode->Tuning->Encounters)
            Encounter.OfferDelay = .5f;
        World->InitializeActorsForPlay(FURL());
        Controller = World->SpawnActor<APlayerController>();
        if (!Test.TestNotNull(TEXT("Create fixture controller without user input"), Controller))
            return false;
        // Match GameMode's local-player creation. A raw remote-style controller in
        // standalone otherwise loops ClientSetViewTarget during an interrupted blend.
        Controller->SetAsLocalPlayerController();
        World->AddController(Controller);
        Controller->SetActorTickEnabled(false);
        World->BeginPlay();
        Controller->SetActorTickEnabled(false);
        auto &Tuning = Instance->Session.tuning;
        Tuning.breathSecondsMin = Tuning.breathSecondsMax = .5;
        Tuning.wormholeSeconds = 3;
        Tuning.climaxSeconds = 12;
        Tuning.dockingSeconds = .5;
        return Test.TestTrue(TEXT("Real BeginPlay creates the home hangar and walker"),
                             Mode->InHangar() && Cast<ASSWalker>(Controller->GetPawn()) != nullptr);
    }

    bool BootstrapFlight(FAutomationTestBase &Test, const char *RunId)
    {
        if (!Test.TestTrue(TEXT("Fixture creates a fresh in-memory run"), Instance->Session.StartRun(RunId)))
            return false;
        // These existing reflected references are set only in the automation fixture.
        // No runtime hooks, bypass flags, production save slots or cheat commands are added.
        for (const TCHAR *Name : {TEXT("Ship"), TEXT("Walker"), TEXT("Hub")})
        {
            auto *Property = FindFProperty<FObjectPropertyBase>(ASSGameMode::StaticClass(), Name);
            if (!Test.TestNotNull(TEXT("Find existing orchestration reference"), Property))
                return false;
            if (auto *Actor = Cast<AActor>(Property->GetObjectPropertyValue_InContainer(Mode)))
                Actor->Destroy();
            Property->SetObjectPropertyValue_InContainer(Mode, nullptr);
        }
        auto *Ship = World->SpawnActor<ASSShip>(FVector(0, 0, 7000), FRotator::ZeroRotator);
        if (!Test.TestNotNull(TEXT("Spawn actual flight pawn with authored assets"), Ship))
            return false;
        FindFProperty<FObjectPropertyBase>(ASSGameMode::StaticClass(), TEXT("Ship"))
            ->SetObjectPropertyValue_InContainer(Mode, Ship);
        Controller->Possess(Ship);
        Mode->Director->ResetEncounter();
        Mode->Director->SetActive(true);
        Mode->ClosePanel();
        return true;
    }

    void Step(float Seconds = .05f)
    {
        if (auto *Ship = Cast<ASSShip>(Controller->GetPawn()))
            Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 0.f, false, false);
        // TickTaskManager deduplicates by the engine frame counter. Each manually
        // driven step is a new synthetic frame; keep the global counter monotonic.
        ++GFrameCounter;
        World->Tick(LEVELTICK_All, Seconds);
    }

    bool Activate(FAutomationTestBase &Test, int32 Action)
    {
        for (int32 Index = 0; Index < Mode->Entries.Num(); ++Index)
            if (Mode->Entries[Index].Action == Action && Mode->Entries[Index].Enabled)
            {
                Mode->ActivateEntry(Index);
                return true;
            }
        Test.AddError(FString::Printf(TEXT("Expected enabled UI action %d was unavailable"), Action));
        return false;
    }

    ASSStation *Station() const
    {
        for (TActorIterator<ASSStation> It(World); It; ++It)
            if (!It->IsHome())
                return *It;
        return nullptr;
    }

    ~FSSJourneyWorld()
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

bool CheckPublishedBackdropCollision(FAutomationTestBase &Test)
{
    // Read the authored map; actual simulation uses a separate backdrop-free world.
    auto *Map = LoadObject<UWorld>(nullptr, TEXT("/Game/SpaceSurvival/Maps/Survival.Survival"));
    if (!Test.TestNotNull(TEXT("Authored gameplay map resolves"), Map) ||
        !Test.TestNotNull(TEXT("Authored map has a persistent level"), Map->PersistentLevel.Get()))
        return false;
    int32 Backdrops = 0;
    for (const auto &Actor : Map->PersistentLevel->Actors)
        if (Actor && (Actor->ActorHasTag(TEXT("SpaceBackdrop")) || Actor->ActorHasTag(TEXT("SpaceStars"))))
        {
            ++Backdrops;
            auto *Mesh = Actor->FindComponentByClass<UStaticMeshComponent>();
            if (!Test.TestNotNull(TEXT("Backdrop mesh resolves"), Mesh))
                return false;
            Test.TestFalse(TEXT("Authored backdrop actor collision is disabled"), Actor->GetActorEnableCollision());
            Test.TestTrue(TEXT("Authored backdrop component has no collision"),
                          Mesh->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
        }
    return Test.TestEqual(TEXT("Both authored backdrop actors were checked"), Backdrops, 2);
}

bool CheckApproach(FAutomationTestBase &Test, FSSJourneyWorld &Fixture)
{
    auto *Hub = Fixture.Station();
    auto *Ship = Fixture.Mode->GetPlayerShip();
    if (!Test.TestNotNull(TEXT("Approach spawns a physical major station"), Hub) ||
        !Test.TestNotNull(TEXT("Approach retains the flight pawn"), Ship))
        return false;
    Test.TestTrue(TEXT("Player retains control before docking assist"), Fixture.Controller->GetPawn() == Ship);
    FCollisionObjectQueryParams StaticObjects(ECC_WorldStatic);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSJourneyDockApproach), false, Ship);
    FHitResult Hit;
    const FVector Forward = Hub->GetActorForwardVector();
    const FVector Dock = Hub->PadDockPosition();
    Test.TestFalse(TEXT("The pad approach is clear before assistance"),
                   Fixture.World->SweepSingleByObjectType(
                       Hit, Dock - Forward * 3000.f, Dock - Forward * 1250.f, FQuat::Identity, StaticObjects,
                       FCollisionShape::MakeSphere(ASSShip::FlightCollisionRadius()), Query));
    Test.TestTrue(TEXT("Walker spawn has a physical station floor beneath it"),
                  Fixture.World->LineTraceSingleByObjectType(
                      Hit, Hub->WalkSpawn(), Hub->WalkSpawn() - FVector(0, 0, 500), StaticObjects, Query) &&
                      Hit.GetActor() == Hub);
    // The pad is where the hero is actually put down now, so it needs the same proof the interior deck
    // has always had: something solid under the spawn, belonging to the station rather than to nothing.
    Test.TestTrue(TEXT("The landing pad has a physical deck beneath where the hero is set down"),
                  Fixture.World->LineTraceSingleByObjectType(
                      Hit, Hub->PadWalkSpawn(), Hub->PadWalkSpawn() - FVector(0, 0, 500), StaticObjects, Query) &&
                      Hit.GetActor() == Hub);
    // Fixture places the player in the assist admission band. Natural manual
    // approach/input precision and high-speed flight feel require separate playtests.
    Ship->SetActorLocation(Dock - Forward * 1000.f);
    Ship->SetActorRotation(Hub->GetActorRotation());
    return true;
}

bool CheckStation(FAutomationTestBase &Test, FSSJourneyWorld &Fixture)
{
    auto *Hub = Fixture.Station();
    auto *Ship = Fixture.Mode->GetPlayerShip();
    auto *Walker = Cast<ASSWalker>(Fixture.Controller->GetPawn());
    if (!Test.TestNotNull(TEXT("Station retains the hub"), Hub) ||
        !Test.TestNotNull(TEXT("Station possesses Acornaut walker"), Walker) ||
        !Test.TestNotNull(TEXT("Station retains the docked ship"), Ship))
        return false;
    Test.TestTrue(TEXT("Ship finishes parked on the exterior landing pad"),
                  Ship->GetActorLocation().Equals(Hub->PadDockPosition(), 1.0));
    Test.TestFalse(TEXT("Docked ship stops its flight tick"), Ship->IsActorTickEnabled());
    Test.TestTrue(TEXT("Docked ship collision is disabled"),
                  Ship->Collision->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
    Test.TestFalse(TEXT("Station stops the Director"), Fixture.Mode->Director->IsActive());
    int32 WorldBodies = 0;
    for (TActorIterator<ASSWorldBody> It(Fixture.World); It; ++It)
        ++WorldBodies;
    Test.TestEqual(TEXT("Station transition tears down hazards, enemies, projectiles and event actors"), WorldBodies,
                   0);
    // How a hero gets from the seat onto the deck depends on the hero, and both routes are correct. One
    // with an exit clip climbs out and the station holds the player off until it finishes. One without -
    // the ship has no door, so the exit animation was cancelled and the gap logged as RPT-20260917-01 -
    // is standing outside the ship the moment the docking motion ends. What is not allowed is either one
    // wearing the other's behaviour: a transition that started with no clip to play, or a clip that
    // arrived and was never used.
    const bool ClimbsOut = !Walker->GetHero().DisembarkClipPath.IsEmpty();
    Test.AddInfo(FString::Printf(TEXT("JOURNEY_STATION_HERO id=%s climbsOut=%d exiting=%d"),
                                 *Walker->GetHero().Id.ToString(), ClimbsOut ? 1 : 0,
                                 Walker->IsDisembarking() ? 1 : 0));
    Test.TestEqual(TEXT("The station starts an authored exit exactly when this hero has one to start"),
                   Walker->IsDisembarking(), ClimbsOut);
    const int32 ArrivalWave = Fixture.Instance->Session.run.wave;
    const FVector Console = Hub->GetActorTransform().TransformPosition(FVector(200, -800, 100));
    const FVector Exit = Hub->GetActorTransform().TransformPosition(FVector(650, -350, 100));

    // Services stay shut while a transition is running and the shell cannot skip it. That gate reads one
    // thing - whether the GameMode's walker is mid-exit - and with a hero that has no exit clip there is
    // nothing running for it to refuse, so the check would quietly become vacuous on exactly the builds
    // whose hero does not climb out. A transition is therefore built rather than the check dropped: a
    // second walker, on a roster narrowed to heroes that do climb out, stands in as the GameMode's walker
    // for as long as the three calls take. The arriving walker keeps possession throughout and is put
    // back before anything else runs.
    auto *WalkerProperty = FindFProperty<FObjectPropertyBase>(ASSGameMode::StaticClass(), TEXT("Walker"));
    if (!Test.TestNotNull(TEXT("Find the existing walker reference"), WalkerProperty))
        return false;
    ASSWalker *StandIn = nullptr;
    if (!ClimbsOut)
    {
        auto *Climbing = NewObject<USSPhase1Data>(Fixture.Mode);
        for (auto &Entry : Climbing->Heroes)
            if (Entry.DisembarkClipPath.IsEmpty())
            {
                Entry.MeshPath = TEXT("/Game/SpaceSurvival/Character/SK_NoSuchHero.SK_NoSuchHero");
                Entry.WalkClipPath = TEXT("/Game/SpaceSurvival/Character/A_NoSuchWalk.A_NoSuchWalk");
                Entry.PilotClipPath = TEXT("/Game/SpaceSurvival/Character/A_NoSuchPilot.A_NoSuchPilot");
            }
        // Deferred, because the roster has to be on the pawn before its BeginPlay reads one.
        const FTransform Spawn(Hub->GetActorRotation(), Hub->WalkSpawn());
        StandIn = Fixture.World->SpawnActorDeferred<ASSWalker>(ASSWalker::StaticClass(), Spawn);
        if (!Test.TestNotNull(TEXT("Create a stand-in walker that does climb out"), StandIn))
            return false;
        StandIn->Tuning = Climbing;
        StandIn->FinishSpawning(Spawn);
        Test.AddInfo(FString::Printf(TEXT("JOURNEY_GATE_STANDIN id=%s clip=%s"), *StandIn->GetHero().Id.ToString(),
                                     *StandIn->GetHero().DisembarkClipPath));
        if (!Test.TestTrue(
                TEXT("The stand-in begins the exit this build's arriving hero has none of"),
                StandIn->BeginDisembark(Ship->Pilot->GetComponentTransform(), Exit, Hub->GetActorRotation())))
        {
            StandIn->Destroy();
            return false;
        }
        WalkerProperty->SetObjectPropertyValue_InContainer(Fixture.Mode, StandIn);
    }
    {
        ASSWalker *Gated = StandIn ? StandIn : Walker;
        Gated->SetActorLocation(Console);
        if (!Test.TestTrue(TEXT("The gate is put in front of a walker that really is mid-exit"),
                           Gated->IsDisembarking()))
            return false;
        Fixture.Mode->Interact();
        Test.TestTrue(TEXT("Early console interaction cannot interrupt the authored exit"),
                      !Fixture.Mode->IsMenuOpen());
        Fixture.Mode->OpenPanel(ESSPanel::Main);
        Test.TestTrue(TEXT("Shell cannot pause or skip the authored exit"), !Fixture.Mode->IsMenuOpen());
        Fixture.Mode->LaunchFromHub();
        Test.TestEqual(TEXT("Early departure leaves the station wave unchanged"), Fixture.Instance->Session.run.wave,
                       ArrivalWave);
        Test.TestTrue(TEXT("Early departure does not leave the station either"),
                      Fixture.Instance->Session.run.phase == SS::Phase::Station);
    }
    if (StandIn)
    {
        WalkerProperty->SetObjectPropertyValue_InContainer(Fixture.Mode, Walker);
        StandIn->Destroy();
        // Nothing the stand-in did touched the arriving hero, which has been standing on the deck in
        // control since docking finished. That is the whole of this hero's exit.
        Test.TestTrue(TEXT("A hero with no exit clip is outside the ship and in control from the first frame"),
                      !Walker->IsDisembarking() && Fixture.Controller->GetPawn() == Walker &&
                          Walker->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics);
        // In plan, because the pawn settles onto the deck vertically: it is where the station puts a
        // walker, not dragged to the seat and not left at the authored exit target.
        Test.TestTrue(TEXT("It stands where the station puts a walker down on the pad, clear of its own ship"),
                      FVector2D(Hub->GetActorTransform().InverseTransformPosition(Walker->GetActorLocation()))
                              .Equals(FVector2D(ASSStation::PadCenterX + 400.f, 0), 1.f) &&
                          FVector::Dist2D(Walker->GetActorLocation(), Hub->PadDockPosition()) > 300.);
    }
    for (int32 Index = 0; Index < 60 && Walker->IsDisembarking(); ++Index)
        Fixture.Step();
    Test.TestTrue(TEXT("However the hero reached the deck, it has possession, collision and walking"),
                  !Walker->IsDisembarking() && Fixture.Controller->GetPawn() == Walker &&
                      Walker->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics);
    Test.TestTrue(TEXT("Arrival leaves the walker above the station floor"),
                  Hub->GetActorTransform().InverseTransformPosition(Walker->GetActorLocation()).Z > 0.f);
    Walker->SetActorLocation(Console);
    Fixture.Mode->Interact();
    Test.TestTrue(TEXT("Physical upgrade console opens the upgrade panel"), Fixture.Mode->Panel == ESSPanel::Upgrades);
    int32 UpgradeTracks = 0;
    for (const FSSMenuEntry &Entry : Fixture.Mode->Entries)
        if (Entry.Action >= 100 && Entry.Action < 105)
            ++UpgradeTracks;
    Test.TestEqual(TEXT("Each major station exposes all five core tracks"), UpgradeTracks, 5);
    Fixture.Mode->ClosePanel();
    return true;
}
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSAcceleratedJourney, "SpaceSurvival.Integration.AcceleratedTenWaveJourney",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSAcceleratedJourney::RunTest(const FString &Parameters)
{
    AddInfo(TEXT("Accelerated actor integration: 12-second waves/climaxes, shortened transitions, enlarged durability, "
                 "fixture flight bootstrap, forced objective acquisition/defeat and assist-band positioning. "
                 "This does not validate natural balance, fairness, flight feel, controller input, performance, "
                 "or disk-backed New Run/death/restart transactions."));
    if (!CheckPublishedBackdropCollision(*this))
        return false;
    FSSJourneyWorld Fixture;
    if (!Fixture.Initialize(*this) || !Fixture.BootstrapFlight(*this, "qa-accelerated-journey"))
        return false;
    auto &Session = Fixture.Instance->Session;
    TArray<int32> Waves;
    TSet<ASSEncounterBeacon *> SeenDepots;
    TSet<ASSEncounterBeacon *> HandledSignals;
    int32 Stations = 0, ApproachWave = 0, DockingTransitions = 0;
    SS::Phase PreviousPhase = SS::Phase::Hangar;
    bool WormholeActorSeen = false, HostileClimaxSeen = false, CompoundActorsSeen = false, ThreatsSeen = false;
    for (int32 Frame = 0; Frame < 6000 && Stations < 2; ++Frame)
    {
        Fixture.Step();
        if (!TestTrue(TEXT("Controlled-survival fixture remains alive"), Session.run.active))
            return false;
        if (Waves.IsEmpty() || Waves.Last() != Session.run.wave)
        {
            TestEqual(TEXT("GameMode advances waves without skipping"), Session.run.wave, Waves.Num() + 1);
            Waves.Add(Session.run.wave);
            AddInfo(FString::Printf(TEXT("JOURNEY_WAVE %d"), Session.run.wave));
        }
        if (Session.run.phase == SS::Phase::Docking && PreviousPhase != SS::Phase::Docking)
            ++DockingTransitions;
        PreviousPhase = Session.run.phase;
        bool Gravity = false, Asteroid = false, Enemy = false;
        for (TActorIterator<ASSWorldBody> It(Fixture.World); It; ++It)
        {
            ThreatsSeen |= It->IsSolidHazard() || It->IsEnemy();
            Gravity |= It->GetKind() == ESSWorldKind::GravityAnomaly;
            Asteroid |= It->GetKind() == ESSWorldKind::SmallAsteroid || It->GetKind() == ESSWorldKind::MediumAsteroid ||
                        It->GetKind() == ESSWorldKind::MassiveAsteroid;
            Enemy |= It->IsEnemy();
            WormholeActorSeen |= Session.run.phase == SS::Phase::Wormhole && Cast<ASSWormholePassage>(*It) != nullptr;
        }
        HostileClimaxSeen |= Session.run.wave == 5 && Session.run.phase == SS::Phase::Climax && Enemy;
        CompoundActorsSeen |=
            Session.run.wave == 10 && Session.run.phase == SS::Phase::Climax && Gravity && Asteroid && Enemy;
        TArray<ASSEncounterBeacon *> Beacons;
        for (TActorIterator<ASSEncounterBeacon> It(Fixture.World); It; ++It)
            Beacons.Add(*It);
        for (ASSEncounterBeacon *Beacon : Beacons)
        {
            if (Beacon->IsDepot())
                SeenDepots.Add(Beacon);
            if (HandledSignals.Contains(Beacon) || Beacon->IsResolved() || !Session.IsFlying())
                continue;
            HandledSignals.Add(Beacon);
            auto *Ship = Fixture.Mode->GetPlayerShip();
            const FVector BeforeServiceLocation = Ship->GetActorLocation();
            if (Beacon->IsDepot())
            {
                // The accelerated fixture can offer a depot alongside live threats.
                // Explicitly stage the service above their bounds, exercising real
                // acceptance rather than weakening the production safety check.
                double ClearHeight = BeforeServiceLocation.Z;
                for (TActorIterator<ASSWorldBody> It(Fixture.World); It; ++It)
                    ClearHeight = FMath::Max(ClearHeight, It->GetActorLocation().Z + It->GetBodyRadius());
                Ship->SetActorLocation(
                    FVector(BeforeServiceLocation.X, BeforeServiceLocation.Y, ClearHeight + 10000.0));
            }
            Beacon->SetActorLocation(Ship->GetActorLocation() + Ship->GetActorRightVector() * 200.f);
            Fixture.Mode->ClosePanel();
            TSet<ASSEnemy *> ExistingEnemies;
            for (TActorIterator<ASSEnemy> It(Fixture.World); It; ++It)
                ExistingEnemies.Add(*It);
            Fixture.Mode->Interact();
            if (Beacon->IsDepot())
            {
                if (!TestTrue(TEXT("Magnetic depot opens through GameMode interaction"),
                              Fixture.Mode->Panel == ESSPanel::Depot))
                    return false;
                if (!TestEqual(TEXT("Depot offers a three-track subset"), Beacon->GetOffers().Num(), 3))
                    return false;
                const int32 Track = Beacon->GetOffers()[0];
                const int32 BeforeTier = Session.run.tiers[Track], BeforeCredits = Session.run.credits;
                const int32 Price = Session.UpgradePrice(SS::Upgrade(Track), Beacon->GetDiscount());
                if (!Fixture.Activate(*this, 100 + Track))
                    return false;
                TestEqual(TEXT("Real depot purchase installs its offered tier"), Session.run.tiers[Track],
                          BeforeTier + 1);
                TestEqual(TEXT("Real depot purchase charges its discounted price"), Session.run.credits,
                          BeforeCredits - Price);

                // Explicit fixture damage exposes the paid service. No natural
                // damage, controller operation or physical range traversal is claimed.
                Session.run.shield = FMath::Max(0.0, Session.Stats().maxShield - 250.0);
                Fixture.Mode->OpenPanel(ESSPanel::Depot);
                const SS::Run BeforeShieldService = Session.run;
                if (!Fixture.Activate(*this, 105))
                    return false;
                SS::Run ExpectedShieldService = BeforeShieldService;
                ExpectedShieldService.credits -= 21;
                ExpectedShieldService.shield = Session.Stats().maxShield;
                TestEqual(TEXT("Live depot shield service charges the current 21-credit price"), Session.run.credits,
                          BeforeShieldService.credits - 21);
                TestTrue(TEXT("Depot service changes only shield and paid credits"),
                         SS::EncodeRun(Session.run) == SS::EncodeRun(ExpectedShieldService));

                // Keep the enabled offer stale while its physical owner leaves
                // range. The activation handler must revalidate before mutation.
                Session.run.shield = FMath::Max(0.0, Session.Stats().maxShield - 250.0);
                Fixture.Mode->OpenPanel(ESSPanel::Depot);
                const SS::Run BeforeOutOfRangeService = Session.run;
                const FVector DepotLocation = Beacon->GetActorLocation();
                Beacon->SetActorLocation(Ship->GetActorLocation() +
                                         Ship->GetActorRightVector() * (Beacon->GetInteractionRadius() + 1000.f));
                TestFalse(TEXT("Fixture moved the depot beyond its interaction range"), Beacon->IsPlayerInRange());
                if (!Fixture.Activate(*this, 105))
                    return false;
                TestTrue(TEXT("Out-of-range shield activation leaves the entire run unchanged"),
                         SS::EncodeRun(Session.run) == SS::EncodeRun(BeforeOutOfRangeService));
                TestTrue(TEXT("Out-of-range depot offer closes"), Fixture.Mode->Panel == ESSPanel::None);
                Beacon->SetActorLocation(DepotLocation);
                Fixture.Mode->ClosePanel();
                TestFalse(TEXT("Closing services releases magnetic hold"), Ship->IsMoored());
                // No actor Tick separates release and this attempted reacquisition.
                Fixture.Mode->Interact();
                TestTrue(TEXT("Released depot cannot reset its timer before the next beacon tick"),
                         !Ship->IsMoored() && Fixture.Mode->Panel == ESSPanel::None);
                Ship->SetActorLocation(BeforeServiceLocation);
                continue;
            }
            if (!TestTrue(TEXT("Explicit GameMode interaction accepts the optional event"), Beacon->IsAccepted()))
                return false;
            TArray<ASSPickup *> Caches;
            for (TActorIterator<ASSPickup> It(Fixture.World); It; ++It)
                if (It->GetLabel().StartsWith(TEXT("SALVAGE CACHE")))
                    Caches.Add(*It);
            for (ASSPickup *Cache : Caches)
            {
                Cache->SetActorLocation(Ship->GetActorLocation());
                Cache->Tick(0.f);
            }
            TArray<ASSEnemy *> Attackers;
            for (TActorIterator<ASSEnemy> It(Fixture.World); It; ++It)
                if (!ExistingEnemies.Contains(*It))
                    Attackers.Add(*It);
            for (ASSEnemy *Attacker : Attackers)
                Attacker->ReceiveWeaponHit(100000.f);
            if (!TestTrue(TEXT("Real objective callbacks secure an event reward"),
                          Beacon->IsResolved() && Session.run.pendingReward))
                return false;
            Fixture.Step();
            Fixture.Mode->Interact();
            if (!TestTrue(TEXT("Secured reward opens the deliberate choice panel"),
                          Fixture.Mode->Panel == ESSPanel::Reward) ||
                !Fixture.Activate(*this, Session.run.rewardCombat ? 48 : 46))
                return false;
            TestFalse(TEXT("Choosing a reward consumes the pending choice"), Session.run.pendingReward);
        }
        if (Session.run.phase == SS::Phase::Approach && ApproachWave != Session.run.wave)
        {
            ApproachWave = Session.run.wave;
            if (!CheckApproach(*this, Fixture))
                return false;
        }
        if (Session.run.phase == SS::Phase::Station)
        {
            ++Stations;
            AddInfo(FString::Printf(TEXT("JOURNEY_STATION %d"), Stations));
            TestEqual(TEXT("Major stations arrive on the fifth-wave cadence"), Session.run.wave, Stations * 5);
            if (!CheckStation(*this, Fixture))
                return false;
            if (Stations == 1)
            {
                ASSShip *DockedShip = Fixture.Mode->GetPlayerShip();
                Fixture.Mode->LaunchFromHub();
                TestEqual(TEXT("Real station departure advances to Wave 6"), Session.run.wave, 6);
                TestTrue(TEXT("Departure possesses a fresh flying pawn"),
                         Fixture.Controller->GetPawn() == Fixture.Mode->GetPlayerShip() &&
                             Fixture.Mode->GetPlayerShip() != DockedShip);
                TestTrue(TEXT("Departure reactivates the Director"), Fixture.Mode->Director->IsActive());
                TestTrue(TEXT("Station departure preserves the deliberate event module"),
                         Session.run.utility == SS::Utility::VectorThrusters);
            }
        }
    }
    TestEqual(TEXT("Integrated journey reaches every Phase 1 wave"), Waves.Num(), 10);
    TestEqual(TEXT("Both real station transitions complete"), Stations, 2);
    TestEqual(TEXT("Both approaches enter assisted docking"), DockingTransitions, 2);
    TestTrue(TEXT("Director spawned actual traversal threats"), ThreatsSeen);
    TestTrue(TEXT("Wave 5 spawns its real wormhole passage"), WormholeActorSeen);
    TestTrue(TEXT("Wave 5 hostile climax contains enemy actors"), HostileClimaxSeen);
    TestTrue(TEXT("Wave 10 concurrently contains gravity, asteroid and enemy actors"), CompoundActorsSeen);
    TestEqual(TEXT("Exactly one depot actor was offered across both blocks"), SeenDepots.Num(), 1);
    TestEqual(TEXT("Both optional events complete through real actors"), Session.run.eventsCompleted, 2);
    TestTrue(TEXT("Combat reward replaces the active weapon"), Session.run.weapon == SS::Weapon::HeavyCannon);
    const auto BoundaryRun = SS::EncodeRun(Session.run);
    const auto BoundaryAccount = SS::EncodeAccount(Session.account);
    Fixture.Mode->OpenPanel(ESSPanel::Launch);
    TestTrue(TEXT("Station 2 shows the live run summary without declaring a victory"),
             Fixture.Mode->PanelTitle.Contains(TEXT("STATION 2")) &&
                 Fixture.Mode->PanelDetail.Contains(TEXT("Live run: 10 waves")));
    TestTrue(TEXT("Boundary offers guarded suspension and disclosed abandonment directly"),
             Fixture.Mode->Entries.ContainsByPredicate([](const FSSMenuEntry &Entry)
                                                       { return Entry.Action == 43 && Entry.Enabled; }) &&
                 Fixture.Mode->Entries.ContainsByPredicate(
                     [](const FSSMenuEntry &Entry)
                     { return Entry.Action == 51 && Entry.Enabled && Entry.Label.Contains(TEXT("no XP")); }));
    TestFalse(TEXT("Boundary has no enabled next-wave launch"),
              Fixture.Mode->Entries.ContainsByPredicate([](const FSSMenuEntry &Entry)
                                                        { return Entry.Action == 50 && Entry.Enabled; }));
    if (!Fixture.Activate(*this, 0))
        return false;
    TestTrue(TEXT("Returning to station services closes only the summary"),
             Fixture.Mode->Panel == ESSPanel::None && SS::EncodeRun(Session.run) == BoundaryRun &&
                 SS::EncodeAccount(Session.account) == BoundaryAccount);
    Fixture.Mode->LaunchFromHub();
    TestTrue(TEXT("Station 2 remains the documented live slice boundary"), Session.AtSliceBoundary());
    TestTrue(TEXT("Blocked departure preserves run and account"),
             SS::EncodeRun(Session.run) == BoundaryRun && SS::EncodeAccount(Session.account) == BoundaryAccount);

    // Exercise the actual vendor adapter after the complete journey, keeping free event choices above intact.
    Session.AwardCredits(300);
    Fixture.Mode->OpenPanel(ESSPanel::Vendor);
    TestTrue(TEXT("The event-fitted utility is visibly disabled at the vendor"),
             Fixture.Mode->Entries.ContainsByPredicate(
                 [](const FSSMenuEntry &Entry)
                 { return Entry.Action == 44 && !Entry.Enabled && Entry.Label.Contains(TEXT("already fitted")); }));
    const int BeforeModule = Session.run.credits;
    if (!Fixture.Activate(*this, 45))
        return false;
    TestTrue(TEXT("Vendor replacement fits the other utility for exactly 150 credits"),
             Session.run.utility == SS::Utility::OverdriveCooling && Session.run.credits == BeforeModule - 150);
    const auto FittedRun = SS::EncodeRun(Session.run);
    const int32 FittedIndex =
        Fixture.Mode->Entries.IndexOfByPredicate([](const FSSMenuEntry &Entry) { return Entry.Action == 45; });
    if (!TestTrue(TEXT("The newly fitted offer remains present, labelled and disabled"),
                  FittedIndex != INDEX_NONE && !Fixture.Mode->Entries[FittedIndex].Enabled &&
                      Fixture.Mode->Entries[FittedIndex].Label.Contains(TEXT("already fitted"))))
        return false;
    Fixture.Mode->ActivateEntry(FittedIndex);
    TestTrue(TEXT("Selecting the disabled fitted module cannot charge twice"), SS::EncodeRun(Session.run) == FittedRun);
    Fixture.Mode->ClosePanel();
    TestTrue(TEXT("Persistence remains blocked for the entire fixture"), Fixture.Instance->AccountStorageBlocked);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSJourneyDeathAndFreshRun, "SpaceSurvival.Integration.JourneyDeathAndFreshRun",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSJourneyDeathAndFreshRun::RunTest(const FString &Parameters)
{
    AddInfo(TEXT("Actor death/XP/hangar and in-memory next-run reset. Persistence is intentionally blocked; "
                 "the normal restart button must remain blocked. Next flight uses explicit fixture bootstrap."));
    FSSJourneyWorld Fixture;
    if (!Fixture.Initialize(*this) || !Fixture.BootstrapFlight(*this, "qa-journey-death"))
        return false;
    auto &Session = Fixture.Instance->Session;
    for (int32 Frame = 0; Frame < 400 && Session.run.wave < 2; ++Frame)
        Fixture.Step();
    if (!TestEqual(TEXT("Real orchestration earns Wave 1 progression before death"), Session.run.wave, 2))
        return false;
    Session.run.tiers[0] = 3;
    Session.EquipUtility(SS::Utility::OverdriveCooling);
    Fixture.Mode->GetPlayerShip()->ReceiveDamage(1000000.f);
    Fixture.Step();
    TestTrue(TEXT("Actual ship damage ends the run"), Session.run.phase == SS::Phase::Dead && !Session.run.active);
    TestTrue(TEXT("Death awards account XP from completed survival"), Session.account.xp > 0);
    TestEqual(TEXT("Death records one account run"), Session.account.runs, 1);
    TestTrue(TEXT("GameMode returns the player to the home hangar"),
             Fixture.Mode->InHangar() && Cast<ASSWalker>(Fixture.Controller->GetPawn()) != nullptr);
    TestTrue(TEXT("GameMode displays the real results panel"), Fixture.Mode->Panel == ESSPanel::Results);
    Fixture.Mode->StartNewRun();
    TestTrue(TEXT("Failed persistence prevents the normal new-run path"), Session.run.phase == SS::Phase::Dead);
    const int64 AccountXP = Session.account.xp;
    if (!Fixture.BootstrapFlight(*this, "qa-journey-fresh"))
        return false;
    Fixture.Step();
    TestEqual(TEXT("Fixture next flight begins at Wave 1"), Session.run.wave, 1);
    TestEqual(TEXT("Fresh flight resets hull upgrades"), Session.run.tiers[0], 1);
    TestEqual(TEXT("Fresh flight resets run currency"), Session.run.credits, 0);
    TestTrue(TEXT("Fresh flight clears the previous utility"), Session.run.utility == SS::Utility::None);
    TestTrue(TEXT("Fresh flight preserves earned account progression"), Session.account.xp == AccountXP);
    TestTrue(TEXT("Fresh flight possesses a real ship and runs the Director"),
             Cast<ASSShip>(Fixture.Controller->GetPawn()) != nullptr && Fixture.Mode->Director->IsActive());
    return true;
}
#endif
