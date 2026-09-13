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
#endif
