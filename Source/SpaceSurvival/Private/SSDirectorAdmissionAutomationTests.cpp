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
#include "HAL/IConsoleManager.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSWreckageBudgetWorld
{
    UWorld *World = nullptr;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    USSSurvivalDirectorComponent *Director = nullptr;

    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated wreckage budget world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // No GameInstance Init, BeginPlay, save API or production slots.
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = 0;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
        if (!Test.TestTrue(TEXT("Install the actual content/Director owner"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        if (!Test.TestNotNull(TEXT("Resolve actual GameMode"), Mode))
            return false;
        Mode->Tuning = NewObject<USSPhase1Data>(Mode);
        auto *Controller = World->SpawnActor<APlayerController>();
        auto *Ship = World->SpawnActor<ASSShip>();
        if (!Test.TestNotNull(TEXT("Create controlled flight pawn"), Ship) ||
            !Test.TestNotNull(TEXT("Create input-free local controller"), Controller))
            return false;
        Controller->SetAsLocalPlayerController();
        World->AddController(Controller);
        Controller->Possess(Ship);
        if (!Test.TestTrue(TEXT("Start only an in-memory run"), Instance->Session.StartRun("wreckage-budget")))
            return false;
        Instance->Session.run.wave = 6;
        auto &Selection = Mode->Tuning->DirectorContent;
        Selection.EnemyChance = Selection.FieldChance = 0.f;
        Selection.WreckageSelectionStart = 0.f;
        Selection.SpawnIntervalMin = Selection.SpawnIntervalMax = .1f;
        for (auto &Hazard : Mode->Tuning->Hazards)
            if (Hazard.Kind == ESSWorldKind::Wreckage)
            {
                Hazard.SelectionWeight = 1.f;
                Hazard.PressureCost = .5f;
            }
        Director = Mode->Director;
        Director->BaseBudgetPerSecond = 0.f;
        Director->MaximumActiveThreats = 8;
        Director->Configure(6, false); // Existing one-unit initial pressure budget; never reset during a scenario.
        Director->SetActive(true);
        return true;
    }

    void Step(float Seconds = .2f)
    {
        Director->TickComponent(Seconds, LEVELTICK_All, nullptr);
    }

    int32 WreckageCount() const
    {
        int32 Count = 0;
        for (TActorIterator<ASSWorldBody> It(World); It; ++It)
            if (!It->IsActorBeingDestroyed() && It->GetKind() == ESSWorldKind::Wreckage)
                ++Count;
        return Count;
    }

    void RemoveWreckage()
    {
        for (TActorIterator<ASSWorldBody> It(World); It; ++It)
            if (It->GetKind() == ESSWorldKind::Wreckage)
            {
                // Keep deferred destruction out of the next spatial-admission attempt.
                It->SetActorLocation(FVector(-1000000, 0, 0));
                It->Destroy();
            }
    }

    ~FSSWreckageBudgetWorld()
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSWreckageBudgetAdmission, "SpaceSurvival.Integration.WreckageBudgetAdmission",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSWreckageBudgetAdmission::RunTest(const FString &)
{
    for (bool SpatialBlock : {false, true})
    {
        FSSWreckageBudgetWorld F;
        if (!F.Initialize(*this))
            return false;
        ASSWorldBody *Blocker = nullptr;
        const FString Label = SpatialBlock ? TEXT("Spatially blocked passage") : TEXT("Four-slot capacity rejection");
        if (SpatialBlock)
        {
            Blocker = F.World->SpawnActor<ASSWorldBody>(FVector(12000, 0, 0), FRotator::ZeroRotator);
            if (!TestNotNull(TEXT("Create actual hazard covering every candidate spawn"), Blocker))
                return false;
            Blocker->Configure(ESSWorldKind::MassiveAsteroid, 50000.f, 0.f, 6);
        }
        else
            F.Director->MaximumActiveThreats =
                3; // Outer cap permits an attempt; the four-piece reservation cannot fit.
        F.Step(1.f);
        F.Step();
        F.Step();
        TestEqual(Label + TEXT(" creates no wreckage"), F.WreckageCount(), 0);
        if (Blocker)
            Blocker->SetActorLocation(FVector(-1000000, 0, 0));
        F.Director->MaximumActiveThreats = 8;
        // No Configure, private budget access or budget accrual: successful retries
        // must spend the budget preserved through those failed production admissions.
        F.Step();
        TestEqual(Label + TEXT(" retains enough budget for all four pieces after removal"), F.WreckageCount(), 4);
        F.RemoveWreckage();
        F.Step();
        TestEqual(Label + TEXT(" charges the half-unit passage once, not once per chunk"), F.WreckageCount(), 4);
        F.RemoveWreckage();
        F.Step();
        TestEqual(Label + TEXT(" stops spending after the two successful passages exhaust the budget"),
                  F.WreckageCount(), 0);
    }

    FSSWreckageBudgetWorld Partial;
    if (!Partial.Initialize(*this))
        return false;
    for (auto &Hazard : Partial.Mode->Tuning->Hazards)
        if (Hazard.Kind == ESSWorldKind::Wreckage)
        {
            Hazard.PressureCost = 1.f;
            // The first chunk's radius blocks the other three existing candidates.
            // This exercises a real partial passage, rather than fabricating a success flag.
            Hazard.BreakableChunkRadius = 2000.f;
        }
    Partial.Step(1.f);
    TestEqual(TEXT("A partially admitted passage retains its one actual chunk"), Partial.WreckageCount(), 1);
    Partial.RemoveWreckage();
    Partial.Step();
    TestEqual(TEXT("A partial passage still spends its normal one-unit cost"), Partial.WreckageCount(), 0);
    return true;
}

// Every placer derives its lead from the ship's speed; retirement was one fixed radius. Tripling hazard speed
// moved the lead for a 4,300 climax gravity field to 17,775-23,275 at cruise, so the packaged Wave 10 fixture saw
// its required gravity well admitted, charged for and deleted on its first tick, and the compound front never
// formed. Boost did the same to asteroids, enemies, salvage caches and distress attackers. The pawn in this world
// has not begun play and cannot be given a velocity, so the dial and the authored lead stand in for ship speed.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSAdmittedBodiesOutliveAdmission,
                                 "SpaceSurvival.Integration.AdmittedBodiesOutliveAdmission",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSAdmittedBodiesOutliveAdmission::RunTest(const FString &)
{
    IConsoleVariable *Speed = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.HazardSpeed"));
    if (!TestNotNull(TEXT("Resolve the Director's speed dial"), Speed))
        return false;
    const float DefaultRetire = GetDefault<ASSWorldBody>()->RetireDistance;
    const float SavedSpeed = Speed->GetFloat();
    // 450 is the floor FindSafeSpawn puts under the largest authored drift. One step past the quotient lands a
    // body of any radius beyond the default retirement radius while the ship is at rest.
    const float Dial = FMath::CeilToFloat(DefaultRetire / (450.f * 3.5f)) + 1.f;
    Speed->Set(Dial, ECVF_SetByCode);
    if (!FMath::IsNearlyEqual(Speed->GetFloat(), Dial))
    {
        AddError(TEXT("ss.HazardSpeed is pinned by the console or the command line; clear it before this test."));
        return false;
    }
    // Survives the tick after it was placed, and says why: the radius now covers where the body was put.
    auto Outlives = [&](ASSWorldBody *Body, const ASSShip *Ship, const FString &Label)
    {
        const double Distance = FVector::Dist(Body->GetActorLocation(), Ship->GetActorLocation());
        TestTrue(Label + TEXT(" was placed beyond the default retirement radius"), Distance > DefaultRetire);
        Body->Tick(0.f);
        Body->Tick(.1f);
        TestFalse(Label + TEXT(" survives the tick after it was placed"), Body->IsActorBeingDestroyed());
        TestTrue(Label + TEXT(" has a retirement radius that covers where it was placed"),
                 Body->RetireDistance > Distance);
    };
    auto Find = [](UWorld *World, ESSWorldKind Kind)
    {
        for (TActorIterator<ASSWorldBody> It(World); It; ++It)
            if (!It->IsActorBeingDestroyed() && It->GetKind() == Kind)
                return *It;
        return static_cast<ASSWorldBody *>(nullptr);
    };
    bool bResult = true;
    {
        FSSWreckageBudgetWorld F;
        bResult &= F.Initialize(*this);
        if (bResult)
        {
            const ASSShip *Ship = Cast<ASSShip>(F.World->GetFirstPlayerController()->GetPawn());
            F.Director->BaseBudgetPerSecond = 100.f;
            F.Director->Configure(10, true);
            // The compound block admits gravity, then an asteroid, then a pursuer, one per spawn tick.
            ASSWorldBody *Gravity = nullptr, *Asteroid = nullptr, *Pursuer = nullptr;
            for (int32 Attempt = 0; Attempt < 60 && !(Gravity && Asteroid && Pursuer); ++Attempt)
            {
                F.Step(1.f);
                Gravity = Find(F.World, ESSWorldKind::GravityAnomaly);
                Asteroid = Find(F.World, ESSWorldKind::MediumAsteroid);
                Pursuer = Find(F.World, ESSWorldKind::Pursuer);
            }
            bResult &= TestNotNull(TEXT("The Wave 10 climax admits its required gravity field"), Gravity) &&
                       TestNotNull(TEXT("The Wave 10 climax admits its required asteroid"), Asteroid) &&
                       TestNotNull(TEXT("The Wave 10 climax admits its required pursuer"), Pursuer);
            if (bResult)
            {
                Outlives(Gravity, Ship, TEXT("The required gravity field"));
                Outlives(Asteroid, Ship, TEXT("The required asteroid"));
                Outlives(Pursuer, Ship, TEXT("The required pursuer"));
                // Fields are not drawn during a climax. One that is lost has to be asked for again.
                Gravity->SetActorLocation(FVector(-1000000, 0, 0));
                Gravity->Destroy();
                ASSWorldBody *Replacement = nullptr;
                for (int32 Attempt = 0; Attempt < 60 && !Replacement; ++Attempt)
                {
                    F.Step(1.f);
                    Replacement = Find(F.World, ESSWorldKind::GravityAnomaly);
                }
                bResult &= TestNotNull(TEXT("A required gravity field that is lost is admitted again"), Replacement);
            }
        }
    }
    {
        FSSWreckageBudgetWorld F;
        if (F.Initialize(*this))
        {
            const ASSShip *Ship = Cast<ASSShip>(F.World->GetFirstPlayerController()->GetPawn());
            F.Step(1.f);
            int32 Chunks = 0;
            for (TActorIterator<ASSWorldBody> It(F.World); It; ++It)
                if (It->GetKind() == ESSWorldKind::Wreckage)
                    Outlives(*It, Ship, FString::Printf(TEXT("Passage chunk %d"), ++Chunks));
            bResult &= TestEqual(TEXT("The wreckage passage was admitted whole"), Chunks, 4);
        }
        else
            bResult = false;
    }
    for (ESSEncounterKind Kind : {ESSEncounterKind::SalvageCache, ESSEncounterKind::DistressCombat})
    {
        // Accepted during a boost, the course starts past the radius. The authored lead says so here.
        const TCHAR *Name = Kind == ESSEncounterKind::SalvageCache ? TEXT("Salvage") : TEXT("Distress");
        FSSWreckageBudgetWorld F;
        if (!F.Initialize(*this))
        {
            bResult = false;
            continue;
        }
        const ASSShip *Ship = Cast<ASSShip>(F.World->GetFirstPlayerController()->GetPawn());
        for (auto &Entry : F.Mode->Tuning->Encounters)
            Entry.ObjectiveLeadDistance = DefaultRetire + 1000.f;
        auto *Beacon = F.World->SpawnActor<ASSEncounterBeacon>(FVector(1500, 0, 0), FRotator::ZeroRotator);
        if (!TestNotNull(TEXT("Create the accepted signal"), Beacon))
        {
            bResult = false;
            continue;
        }
        Beacon->ConfigureEncounter(Kind, Kind == ESSEncounterKind::SalvageCache ? 2 : 7);
        Beacon->Tick(.1f);
        if (!TestTrue(FString::Printf(TEXT("%s signal is accepted"), Name), Beacon->TryAccept()))
        {
            bResult = false;
            continue;
        }
        int32 Objectives = 0;
        for (TActorIterator<ASSWorldBody> It(F.World); It; ++It)
            if (*It != Beacon)
                Outlives(*It, Ship, FString::Printf(TEXT("%s objective body %d"), Name, ++Objectives));
        bResult &= TestTrue(FString::Printf(TEXT("%s acceptance placed its objectives"), Name),
                            Objectives >= Beacon->GetObjectiveRemaining());
        // The signal the objectives report to must still exist when the ship is at the far end of the course.
        TestTrue(FString::Printf(TEXT("%s signal is kept for the length of its course"), Name),
                 Beacon->RetireDistance > DefaultRetire + DefaultRetire);
    }
    Speed->Set(SavedSpeed, ECVF_SetByCode);
    return bResult;
}
#endif
