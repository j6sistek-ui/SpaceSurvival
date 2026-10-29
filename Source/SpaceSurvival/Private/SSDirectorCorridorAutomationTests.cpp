#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSWorldActors.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Components/SphereComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/IConsoleManager.h"
#include "Misc/ScopeExit.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSDirectorWaveCorridor, "SpaceSurvival.Flight.WaveCorridorDirector",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSDirectorWaveCorridor::RunTest(const FString &)
{
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Create isolated corridor admission world"), World))
        return false;
    auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    auto *Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
    Instance->AddToRoot();
    Instance->AccountStorageBlocked = true;
    Instance->Session.settings.masterVolume = 0;
    Instance->Session.settings.cameraShake = false;
    Context.OwningGameInstance = Instance;
    World->SetGameInstance(Instance);
    ON_SCOPE_EXIT
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        Instance->RemoveFromRoot();
    };
    World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
    if (!TestTrue(TEXT("Install actual admission owner"), World->SetGameMode(FURL())))
        return false;
    auto *Mode = World->GetAuthGameMode<ASSGameMode>();
    Mode->Tuning = NewObject<USSPhase1Data>(Mode);
    auto *Controller = World->SpawnActor<APlayerController>();
    auto *Ship = World->SpawnActor<ASSShip>(FVector(1000, 2000, 7000), FRotator(11, 37, 0));
    if (!TestNotNull(TEXT("Controlled ship"), Ship) || !TestNotNull(TEXT("Local controller"), Controller))
        return false;
    Controller->SetAsLocalPlayerController();
    World->AddController(Controller);
    Controller->Possess(Ship);
    Ship->Tuning = Mode->Tuning;
    if (!TestTrue(TEXT("In-memory wave run without saves or production BeginPlay"),
                  Instance->Session.StartRun("corridor-admission")))
        return false;
    // The same route entry used by the real pawn, without starting unrelated mode/menu actors.
    Ship->Tick(0.f);
    if (!TestTrue(TEXT("Wave flight owns a prescribed route"), Ship->IsInWaveCorridor()))
        return false;
    for (int32 Frame = 0; Frame < 90; ++Frame)
        Ship->Tick(1.f / 60.f);
    auto *Director = Mode->Director.Get();
    Director->Configure(6, false);
    const FQuat Frame = Ship->GetFlightRouteFrame();
    const FVector Center = Ship->GetFlightRouteCenter();
    const FVector2D Limits = Ship->GetWaveCorridorHalfExtents();
    FVector InitialLocation;
    Director->Random.Initialize(42);
    if (!TestTrue(TEXT("Ordinary hazard can be admitted ahead of the route"),
                  Director->FindSafeSpawn(300.f, InitialLocation, true)))
        return false;
    // Rolled and displaced ship: the same seed still describes the same world corridor.
    Ship->SetActorLocation(Center + Frame.GetRightVector() * (Limits.X - 200.f) +
                           Frame.GetUpVector() * (Limits.Y - 200.f));
    Ship->SetActorRotation(Frame * FQuat(FVector::ForwardVector, FMath::DegreesToRadians(135.f)));
    FVector RolledLocation;
    Director->Random.Initialize(42);
    if (!TestTrue(TEXT("Edge-of-corridor admission remains available after hull roll"),
                  Director->FindSafeSpawn(300.f, RolledLocation, true)))
        return false;
    TestTrue(TEXT("Hull roll and lateral drift do not rotate or translate ordinary route placements"),
             InitialLocation.Equals(RolledLocation, .1));
    const FVector Local = Frame.UnrotateVector(RolledLocation - Center);
    TestTrue(TEXT("Ordinary hazard is ahead and inside prescribed lateral bounds"),
             Local.X > 9000.f && FMath::Abs(Local.Y) <= Limits.X && FMath::Abs(Local.Z) <= Limits.Y);

    Ship->SetActorLocation(Center);
    FVector Location, Velocity;
    FVector2D Window;
    for (int32 Seed = 0; Seed < 12; ++Seed)
    {
        Director->Random.Initialize(Seed + 101);
        if (!TestTrue(TEXT("Small incoming rock retains admission with bounded escape space"),
                      Director->FindTrajectorySpawn(285.f, 900.f, 80.f, Location, Velocity, Window)))
            return false;
        TestTrue(TEXT("Incoming rock travels along the route regardless of hull roll"),
                 Velocity.GetSafeNormal().Equals(-Frame.GetForwardVector(), .0001));
        const FVector Relative = Location - Ship->GetActorLocation();
        const FVector Closing = Velocity - Ship->GetVelocity();
        const double Time = -FVector::DotProduct(Relative, Closing) / Closing.SizeSquared();
        TestTrue(TEXT("Corridor preserves reaction time"), Time >= Director->MinimumReactionSeconds);
        const FVector FastClosing =
            Velocity - Frame.GetForwardVector() * (Instance->Session.Stats().speed * Ship->Tuning->BoostMultiplier);
        const double FastTime = -FVector::DotProduct(Relative, FastClosing) / FastClosing.SizeSquared();
        const double MissSquared = (Relative + FastClosing * FastTime).SizeSquared();
        const double Contact = 285.f + Ship->Collision->GetScaledSphereRadius();
        const double FirstContact =
            FastTime - FMath::Sqrt(FMath::Max(0., Contact * Contact - MissSquared) / FastClosing.SizeSquared());
        TestTrue(TEXT("Even an immediate boost preserves the first-surface reaction floor"),
                 FirstContact + .001 >= Director->MinimumReactionSeconds);
    }
    auto *DirectShare = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.HazardDirectShare"));
    if (!TestNotNull(TEXT("Resolve direct-shot dial"), DirectShare))
        return false;
    const FString SavedDirectShare = DirectShare->GetString();
    ON_SCOPE_EXIT
    {
        DirectShare->SetWithCurrentPriority(*SavedDirectShare);
    };
    DirectShare->SetWithCurrentPriority(1.f);
    TestFalse(TEXT("Reject an asteroid that covers every reachable escape lane"),
              Director->FindTrajectorySpawn(20000.f, 900.f, 120.f, Location, Velocity, Window));

    // The offer stays reachable even if a data asset asks for an offset outside the corridor.
    for (auto &Encounter : Mode->Tuning->Encounters)
        if (Encounter.Kind == ESSEncounterKind::SalvageCache)
            Encounter.OfferLateralOffset = 100000.f;
    Director->OfferEncounter(ESSEncounterKind::SalvageCache);
    ASSEncounterBeacon *Offer = nullptr;
    for (TActorIterator<ASSEncounterBeacon> It(World); It; ++It)
        Offer = *It;
    if (!TestNotNull(TEXT("Spawn reachable optional offer"), Offer))
        return false;
    const FVector OfferOffset = Frame.UnrotateVector(Offer->GetActorLocation() - Center);
    TestTrue(TEXT("Offer is ahead, bounded and level in the route frame"),
             OfferOffset.X > 0.f && FMath::Abs(OfferOffset.Y) <= Limits.X + .1 && FMath::Abs(OfferOffset.Z) < .1);
    return true;
}
#endif
