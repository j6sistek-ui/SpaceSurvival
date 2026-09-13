#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSWorldActors.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSPickupFragmentWorld
{
    UWorld *World = nullptr;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    ASSShip *Ship = nullptr;

    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated collection/fragment world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // No GameInstance Init, world BeginPlay, save API or production slots.
        Instance->AccountStorageBlocked = true;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
        if (!Test.TestTrue(TEXT("Install real pickup reward/content GameMode"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        if (!Test.TestNotNull(TEXT("Resolve real GameMode"), Mode))
            return false;
        Mode->Tuning = NewObject<USSPhase1Data>(Mode);
        auto *Controller = World->SpawnActor<APlayerController>();
        Ship = World->SpawnActor<ASSShip>();
        if (!Test.TestNotNull(TEXT("Create actual ship"), Ship) ||
            !Test.TestNotNull(TEXT("Create local controller"), Controller))
            return false;
        Controller->SetAsLocalPlayerController();
        World->AddController(Controller);
        Controller->Possess(Ship);
        Instance->Session.settings.masterVolume = 0.0;
        Instance->Session.account.tutorialFlags = 255;
        return Test.TestTrue(TEXT("Start only an in-memory run"), Instance->Session.StartRun("pickup-fragment"));
    }
    ASSPickup *Pickup(FVector Position)
    {
        auto *Result = World->SpawnActor<ASSPickup>(Position, FRotator::ZeroRotator);
        if (Result)
            Result->ConfigurePickup(0, 37.f);
        return Result;
    }
    TArray<ASSWorldBody *> BreakMedium(FVector Position, FVector Velocity)
    {
        auto *Medium = World->SpawnActor<ASSWorldBody>(Position, FRotator::ZeroRotator);
        if (Medium)
        {
            Medium->Configure(ESSWorldKind::MediumAsteroid, 240.f, 30.f, 4);
            Medium->SetLinearVelocity(Velocity);
            Medium->ReceiveWeaponHit(10000.f);
        }
        TArray<ASSWorldBody *> Fragments;
        for (TActorIterator<ASSWorldBody> It(World); It; ++It)
            if (!It->IsActorBeingDestroyed() && It->GetKind() == ESSWorldKind::SmallAsteroid)
                Fragments.Add(*It);
        return Fragments;
    }
    void ClearBodies()
    {
        for (TActorIterator<ASSWorldBody> It(World); It; ++It)
            It->Destroy();
    }
    ~FSSPickupFragmentWorld()
    {
        if (World)
        {
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
        }
        if (Instance)
            Instance->RemoveFromRoot();
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPickupSweptCollection, "SpaceSurvival.Integration.PickupSweptCollection",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSPickupSweptCollection::RunTest(const FString &Parameters)
{
    FSSPickupFragmentWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    auto &Run = Fixture.Instance->Session.run;
    for (float Step : {1.f / 30.f, 1.f / 60.f, 1.f / 144.f, .1f})
    {
        Fixture.Ship->SetActorLocation(FVector(-1200, 0, 0));
        auto *Pickup = Fixture.Pickup(FVector::ZeroVector);
        if (!TestNotNull(TEXT("Spawn actual crossing pickup"), Pickup))
            return false;
        const int32 Credits = Run.credits;
        const int32 Salvage = Run.salvageCollected;
        Pickup->Tick(0.f);
        // 8000 cm/s is below a boosted upgraded ship; .1 s adds a real hitch crossing.
        double X = -1200.0;
        while (X < 1200.0)
        {
            X = FMath::Min(1200.0, X + 8000.0 * Step);
            Fixture.Ship->SetActorLocation(FVector(X, 0, 0));
            Pickup->Tick(Step);
        }
        TestEqual(TEXT("Crossing grants the configured credit amount exactly once"), Run.credits, Credits + 37);
        TestEqual(TEXT("Crossing counts only one salvage collection"), Run.salvageCollected, Salvage + 1);
        TestTrue(TEXT("Collected actor retires"), Pickup->IsActorBeingDestroyed());
        Pickup->Tick(1.f);
        TestEqual(TEXT("A repeated tick cannot grant another reward"), Run.credits, Credits + 37);
    }

    Fixture.Ship->SetActorLocation(FVector(-400, 240, 0));
    auto *NearMiss = Fixture.Pickup(FVector::ZeroVector);
    if (!TestNotNull(TEXT("Spawn deliberate near-miss pickup"), NearMiss))
        return false;
    const int32 BeforeMiss = Run.credits;
    NearMiss->Tick(0.f);
    Fixture.Ship->SetActorLocation(FVector(400, 240, 0));
    NearMiss->Tick(.1f);
    TestEqual(TEXT("Passing just outside collection envelope does not collect a nearby lane"), Run.credits, BeforeMiss);
    TestTrue(TEXT("Outside current magnet range the pickup never moves toward a crossed lane"),
             NearMiss->GetActorLocation().IsNearlyZero());
    NearMiss->Destroy();

    Fixture.Ship->SetActorLocation(FVector::ZeroVector);
    auto *Moving = Fixture.Pickup(FVector(-400, 0, 0));
    if (!TestNotNull(TEXT("Spawn drifting pickup"), Moving))
        return false;
    Moving->SetLinearVelocity(FVector(8000, 0, 0));
    Moving->Tick(.1f);
    TestEqual(TEXT("First-frame pickup drift also uses a continuous path"), Run.credits, BeforeMiss + 37);

    auto *Magnet = Fixture.Pickup(FVector(350, 0, 0));
    if (!TestNotNull(TEXT("Spawn short-range magnet pickup"), Magnet))
        return false;
    Magnet->Tick(1.f);
    TestTrue(TEXT("A long magnet step stops at the ship instead of overshooting"),
             Magnet->GetActorLocation().IsNearlyZero());
    TestEqual(TEXT("Collection observes the completed magnet movement immediately"), Run.credits, BeforeMiss + 74);

    Fixture.Ship->SetActorLocation(FVector(-400, 0, 0));
    auto *Rebased = Fixture.Pickup(FVector::ZeroVector);
    if (!TestNotNull(TEXT("Spawn origin-shift pickup"), Rebased))
        return false;
    // Rebase the configuration-time history before this pickup's very first tick.
    const FVector Offset(1000000, -2000000, 3000000);
    Fixture.Ship->ApplyWorldOffset(Offset, true);
    Rebased->ApplyWorldOffset(Offset, true);
    Fixture.Ship->SetActorLocation(Offset + FVector(400, 0, 0));
    Rebased->Tick(.1f);
    TestEqual(TEXT("Origin rebasing preserves the same relative crossing"), Run.credits, BeforeMiss + 111);

    Fixture.Ship->SetActorLocation(FVector(-500, 0, 0));
    auto *FirstFrame = Fixture.Pickup(FVector::ZeroVector);
    if (!TestNotNull(TEXT("Spawn pickup before the ship's first crossing"), FirstFrame))
        return false;
    const int32 BeforeFirstFrame = Run.credits;
    Fixture.Ship->SetActorLocation(FVector(500, 0, 0));
    FirstFrame->Tick(.1f);
    TestEqual(TEXT("Configuration seeds a first-frame ship crossing without a preparatory tick"), Run.credits,
              BeforeFirstFrame + 37);

    struct FExpiryCase
    {
        const TCHAR *Label;
        FVector ShipStart;
        FVector ShipEnd;
        FVector PickupStart;
        FVector PickupVelocity;
        float Lifetime;
        bool bCollect;
        FVector ExpectedEnd;
    };
    const FExpiryCase Cases[] = {
        {TEXT("Pickup crosses before expiry"), FVector::ZeroVector, FVector::ZeroVector, FVector(-400, 0, 0),
         FVector(8000, 0, 0), .05f, true, FVector::ZeroVector},
        {TEXT("Ship crosses before expiry"), FVector(-500, 0, 0), FVector(500, 0, 0), FVector::ZeroVector,
         FVector::ZeroVector, .05f, true, FVector::ZeroVector},
        {TEXT("Pickup crosses only after expiry"), FVector::ZeroVector, FVector::ZeroVector, FVector(-800, 0, 0),
         FVector(8000, 0, 0), .05f, false, FVector(-360, 0, 0)},
        {TEXT("Ship crosses only after expiry"), FVector(-800, 0, 0), FVector::ZeroVector, FVector::ZeroVector,
         FVector::ZeroVector, .05f, false, FVector(-40, 0, 0)},
        {TEXT("Magnet would collect only after expiry"), FVector::ZeroVector, FVector::ZeroVector, FVector(270, 0, 0),
         FVector::ZeroVector, .025f, false, FVector(250, 0, 0)},
    };
    for (const FExpiryCase &Case : Cases)
    {
        Fixture.Ship->SetActorLocation(Case.ShipStart);
        auto *Pickup = Fixture.Pickup(Case.PickupStart);
        if (!TestNotNull(Case.Label, Pickup))
            return false;
        Pickup->LifetimeSeconds = Case.Lifetime;
        Pickup->SetLinearVelocity(Case.PickupVelocity);
        const int32 Credits = Run.credits;
        const int32 Salvage = Run.salvageCollected;
        Fixture.Ship->SetActorLocation(Case.ShipEnd);
        Pickup->Tick(.1f);
        TestEqual(FString::Printf(TEXT("%s: only live collection pays"), Case.Label), Run.credits,
                  Credits + (Case.bCollect ? 37 : 0));
        TestEqual(FString::Printf(TEXT("%s: salvage follows live collection"), Case.Label), Run.salvageCollected,
                  Salvage + (Case.bCollect ? 1 : 0));
        TestTrue(FString::Printf(TEXT("%s: drift and magnet stop at the live endpoint"), Case.Label),
                 Pickup->GetActorLocation().Equals(Case.ExpectedEnd, .001));
        TestTrue(FString::Printf(TEXT("%s: final-frame pickup retires"), Case.Label), Pickup->IsActorBeingDestroyed());
        Pickup->Tick(.1f);
        TestEqual(FString::Printf(TEXT("%s: retirement cannot pay again"), Case.Label), Run.credits,
                  Credits + (Case.bCollect ? 37 : 0));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSFragmentReactionAdmission, "SpaceSurvival.Integration.FragmentReactionAdmission",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSFragmentReactionAdmission::RunTest(const FString &Parameters)
{
    FSSPickupFragmentWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    Fixture.Ship->SetActorLocation(FVector::ZeroVector);
    const auto Definition = Fixture.Mode->Tuning->Hazard(ESSWorldKind::MediumAsteroid);
    const FVector FarCentre(10000, 0, 0);
    auto Far = Fixture.BreakMedium(FarCentre, FVector::ZeroVector);
    if (!TestEqual(TEXT("Clear destruction retains all three configured fragments"), Far.Num(), 3))
        return false;
    // Use the actual first admitted direction to reproduce a close breakup inside the ship.
    // Unbegun fixture actors retain the same deterministic initial random stream.
    const FVector FirstDirection = (Far[0]->GetActorLocation() - FarCentre).GetSafeNormal();
    for (auto *Fragment : Far)
    {
        TestTrue(TEXT("Fragment travel speed is unchanged"),
                 FMath::IsNearlyEqual(Fragment->GetVelocity().Size(), double(Definition.FragmentSpeed), .001));
        TestTrue(TEXT("Fragment radius/lifetime and destruction risk remain configured"),
                 FMath::IsNearlyEqual(Fragment->GetBodyRadius(), Definition.FragmentRadius) &&
                     FMath::IsNearlyEqual(Fragment->LifetimeSeconds, Definition.FragmentLifetime) &&
                     Fragment->IsSolidHazard() && Fragment->IsWeaponTarget());
    }
    Fixture.ClearBodies();
    for (FVector ParentVelocity : {FVector::ZeroVector, FirstDirection * 1800.f})
    {
        const FVector Centre = -FirstDirection * 400.f;
        auto Fragments = Fixture.BreakMedium(Centre, ParentVelocity);
        if (!TestTrue(TEXT("Close destruction preserves a bounded nonempty debris burst"),
                      Fragments.Num() > 0 && Fragments.Num() <= 3))
            return false;
        for (auto *Fragment : Fragments)
            TestTrue(TEXT("No admitted fragment initially overlaps the ship"),
                     FVector::Dist(Fragment->GetActorLocation(), Fixture.Ship->GetActorLocation()) >
                         120.f + Fragment->GetBodyRadius());
        const double Hull = Fixture.Instance->Session.run.hull;
        const double Shield = Fixture.Instance->Session.run.shield;
        const double End = Fixture.Mode->Director->MinimumReactionSeconds;
        double Elapsed = 0.0;
        while (Elapsed < End)
        {
            const float Step = float(FMath::Min(1.0 / 144.0, End - Elapsed));
            for (auto *Fragment : Fragments)
                Fragment->Tick(Step);
            Elapsed += Step;
        }
        TestEqual(TEXT("Normal fragment ticks cause no unavoidable damage inside the reaction window"),
                  Fixture.Instance->Session.run.shield, Shield);
        TestEqual(TEXT("Hull is protected by safe admission, not an added damage immunity"),
                  Fixture.Instance->Session.run.hull, Hull);
        // Deliberately steer into admitted debris: its normal collision must still hurt immediately.
        auto *Risk = Fragments[0];
        Fixture.Ship->SetActorLocation(Risk->GetActorLocation());
        Risk->Tick(0.f);
        TestTrue(TEXT("Admitted fragments remain dangerous when the player crosses into them"),
                 Fixture.Instance->Session.run.shield < Shield);
        Fixture.Ship->SetActorLocation(FVector::ZeroVector);
        Fixture.ClearBodies();
    }
    Fixture.Mode->Director->MaximumActiveThreats = 1;
    auto Capped = Fixture.BreakMedium(FarCentre, FVector::ZeroVector);
    TestEqual(TEXT("Fragmentation still obeys the live threat cap"), Capped.Num(), 0);
    return true;
}
#endif
