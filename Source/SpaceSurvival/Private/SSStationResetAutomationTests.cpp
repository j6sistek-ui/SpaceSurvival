#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSLandingPad.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSShipPaint.h"
#include "SSShipVisualRig.h"
#include "SSStation.h"
#include "SSStationVisualLayout.h"
#include "SSWorldActors.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/MeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "Physics/Experimental/PhysScene_Chaos.h"
#include "UObject/UnrealType.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSFunctionalStationWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    APlayerController *Controller = nullptr;
    ASSStation *Hub = nullptr;
    ASSWalker *Walker = nullptr;

    bool Initialize(FAutomationTestBase &Test, bool Home)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated functional-station world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // No Init/InitializeStandalone or production BeginPlay. UI actions may update this account
        // in memory, but even an accidental PersistAccount request cannot touch personal saves.
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = 0;
        Instance->Session.account.tutorialFlags = 255;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        GWorld = World;
        World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
        if (!Test.TestTrue(TEXT("Install native station service mode"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        auto *Content = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
        if (!Test.TestNotNull(TEXT("Resolve native service mode"), Mode) ||
            !Test.TestNotNull(TEXT("Resolve installed hero roster"), Content))
            return false;
        Mode->Tuning = DuplicateObject<USSPhase1Data>(Content, Mode);
        Mode->SetActorTickEnabled(false);
        Mode->Director->SetComponentTickEnabled(false);
        World->InitializeActorsForPlay(FURL());
        World->SetBegunPlay(true);
        if (World->GetPhysicsScene())
            World->GetPhysicsScene()->OnWorldBeginPlay();
        Controller = World->SpawnActor<APlayerController>();
        if (!Test.TestNotNull(TEXT("Create service controller"), Controller))
            return false;
        Controller->SetPlayer(NewObject<ULocalPlayer>(GEngine, NAME_None, RF_Transient));
        Controller->bEnableMouseOverEvents = false;
        Controller->bEnableTouchOverEvents = false;
        Controller->bForceFeedbackEnabled = false;
        Controller->SetDisableHaptics(true);
        Controller->SetActorTickEnabled(false);
        World->AddController(Controller);
        auto *HubProperty = FindFProperty<FObjectPropertyBase>(ASSGameMode::StaticClass(), TEXT("Hub"));
        auto *WalkerProperty = FindFProperty<FObjectPropertyBase>(ASSGameMode::StaticClass(), TEXT("Walker"));
        if (!Test.TestNotNull(TEXT("Resolve native hub ownership"), HubProperty) ||
            !Test.TestNotNull(TEXT("Resolve native walker ownership"), WalkerProperty))
            return false;
        if (Home)
        {
            // Exercise the real home construction/possession entry point, without boot-time save work.
            Mode->ShowHangar();
            Hub = Cast<ASSStation>(HubProperty->GetObjectPropertyValue_InContainer(Mode));
            Walker = Cast<ASSWalker>(Controller->GetPawn());
        }
        else
        {
            if (!Test.TestTrue(TEXT("Start transient mid-run station context"),
                               Instance->Session.StartRun("functional-station-fixture")))
                return false;
            Instance->Session.run.phase = SS::Phase::Station;
            const FTransform Transform(FRotator(0, 73, 0), FVector(16000, -8000, 5000));
            Hub = World->SpawnActor<ASSStation>(ASSStation::StaticClass(), Transform);
            if (!Test.TestNotNull(TEXT("Create transformed mid-run hub"), Hub))
                return false;
            Hub->BuildHub(false);
            Walker = World->SpawnActor<ASSWalker>(Hub->WalkSpawn(), Hub->GetActorRotation());
            HubProperty->SetObjectPropertyValue_InContainer(Mode, Hub);
            WalkerProperty->SetObjectPropertyValue_InContainer(Mode, Walker);
            Controller->Possess(Walker);
            Mode->WearHero();
        }
        return Test.TestNotNull(TEXT("Actual station exists"), Hub) &&
               Test.TestNotNull(TEXT("Actual walker is possessed"), Walker) &&
               Test.TestTrue(TEXT("Installed reset layout is active; native fallback cannot satisfy this test"),
                             Hub->IsUsingFunctionalLayout()) &&
               Test.TestEqual(TEXT("Station retains the requested home/service context"), Hub->IsHome(), Home);
    }

    UPrimitiveComponent *Solid(const TCHAR *Name) const
    {
        TInlineComponentArray<UPrimitiveComponent *> Bodies(Hub);
        for (auto *Body : Bodies)
            if (Body->GetFName() == FName(Name) && (Body->ComponentHasTag(TEXT("StationFunctionalSolid")) ||
                                                    Body->ComponentHasTag(TEXT("StationFunctionalStaffSolid"))))
                return Body;
        return nullptr;
    }

    bool Sweep(FAutomationTestBase &Test, const TCHAR *Name, FVector LocalStart, FVector LocalEnd)
    {
        auto *Expected = Solid(Name);
        if (!Test.TestNotNull(FString::Printf(TEXT("%s has a native blocking body"), Name), Expected))
            return false;
        const auto *Capsule = Walker->GetCapsuleComponent();
        const FCollisionShape Shape =
            FCollisionShape::MakeCapsule(Capsule->GetScaledCapsuleRadius(), Capsule->GetScaledCapsuleHalfHeight());
        FCollisionQueryParams Query(SCENE_QUERY_STAT(SSFunctionalStationSweep), false, Walker);
        FHitResult Hit;
        const FTransform Transform = Hub->GetActorTransform();
        const bool Blocked = World->SweepSingleByChannel(Hit, Transform.TransformPosition(LocalStart),
                                                         Transform.TransformPosition(LocalEnd), Hub->GetActorQuat(),
                                                         ECC_Pawn, Shape, Query);
        return Test.TestTrue(FString::Printf(TEXT("Actual walking capsule is blocked by %s"), Name),
                             Blocked && !Hit.bStartPenetrating && Hit.GetActor() == Hub &&
                                 Hit.GetComponent() == Expected);
    }

    ~FSSFunctionalStationWorld()
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
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSStationResetCollision, "SpaceSurvival.Integration.StationResetCollision",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSStationResetCollision::RunTest(const FString &)
{
    for (bool Home : {true, false})
    {
        FSSFunctionalStationWorld F;
        if (!F.Initialize(*this, Home))
            return false;
        const float FeetClear = F.Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 20.f;
        F.Sweep(*this, TEXT("Solid_Collision_Floor_Main"), FVector(0, 0, FeetClear + 200),
                FVector(0, 0, FeetClear - 100));
        F.Sweep(*this, TEXT("Solid_Collision_Wall_North"), FVector(500, 1350, FeetClear),
                FVector(500, 1700, FeetClear));
        F.Sweep(*this, TEXT("Solid_Collision_Column_NE"), FVector(1400, 1350, FeetClear),
                FVector(1800, 1350, FeetClear));
        F.Sweep(*this, TEXT("Solid_Collision_Console_Wardrobe"), FVector(-1100, 1100, FeetClear),
                FVector(-1450, 1100, FeetClear));
        TestTrue(TEXT("Visible main-deck floor remains inside rescue walkable space"),
                 F.Hub->Walkable(F.Hub->GetActorTransform().TransformPosition(FVector(0, 0, FeetClear))));
        const FTransform HubTransform = F.Hub->GetActorTransform();
        auto *Pad = F.Hub->GetLandingPad();
        if (!TestNotNull(TEXT("The functional station owns an actual pad"), Pad))
            return false;
        TestFalse(TEXT("Square corners outside the circular deck cannot satisfy pad support"),
                  Pad->Covers(HubTransform.TransformPosition(FVector(ASSStation::PadCenterX + 1500, 1500, 100))));
        for (float Side : {-350.f, 350.f})
        {
            const FVector Junction(ASSStation::PadCenterX + ASSStation::PadHalfExtent - 25, Side, 0);
            FHitResult Floor;
            FCollisionQueryParams Query(SCENE_QUERY_STAT(SSFunctionalBridgeSupport), false, F.Walker);
            const bool Supported = F.World->LineTraceSingleByChannel(
                Floor, HubTransform.TransformPosition(Junction + FVector(0, 0, 100)),
                HubTransform.TransformPosition(Junction - FVector(0, 0, 100)), ECC_Pawn, Query);
            TestTrue(TEXT("Both sides of the round-pad/bridge junction have a physical floor"),
                     Supported && FVector::DotProduct(Floor.ImpactNormal, F.Hub->GetActorUpVector()) > .99f &&
                         (Floor.GetActor() == F.Hub || Floor.GetActor() == Pad));
        }
        if (Home)
        {
            auto *Ship = F.Mode->GetPlayerShip();
            if (!TestNotNull(TEXT("Home uses the actual ship parked outside"), Ship))
                return false;
            TestTrue(TEXT("Home ship faces outward through the cavity mouth"),
                     FVector::DotProduct(Ship->GetActorForwardVector(), F.Hub->GetActorForwardVector()) < -.99f);
            TestTrue(TEXT("The home player ship is parked at the actual pad docking point"),
                     !Ship->IsActorTickEnabled() && Ship->GetVelocity().IsNearlyZero() &&
                         Ship->GetActorLocation().Equals(F.Hub->PadDockPosition(), .1f));
        }
        TestFalse(TEXT("Collision fixture never entered production mode BeginPlay"), F.Mode->HasActorBegunPlay());
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSStationResetStaff, "SpaceSurvival.Integration.StationResetStaff",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSStationResetStaff::RunTest(const FString &)
{
    for (bool Home : {true, false})
    {
        FSSFunctionalStationWorld F;
        if (!F.Initialize(*this, Home))
            return false;
        int32 VisibleStaff = 0;
        TInlineComponentArray<USkeletalMeshComponent *> Meshes(F.Hub->GetVisualLayout());
        for (auto *Mesh : Meshes)
            if (Mesh->ComponentHasTag(TEXT("StationFunctionalStaff")) && Mesh->GetSkeletalMeshAsset() &&
                Mesh->IsVisible())
                ++VisibleStaff;
        TestEqual(TEXT("The authored layout contains the two intended visible staff"), VisibleStaff, 2);
        int32 PhysicalStaff = 0;
        TInlineComponentArray<UCapsuleComponent *> Bodies(F.Hub);
        for (auto *Body : Bodies)
        {
            if (!Body->ComponentHasTag(TEXT("StationFunctionalStaffSolid")))
                continue;
            ++PhysicalStaff;
            const FVector Center = F.Hub->GetActorTransform().InverseTransformPosition(Body->GetComponentLocation());
            F.Sweep(*this, *Body->GetName(), Center - FVector(180, 0, 0), Center);
            const FVector Foot =
                Body->GetComponentLocation() - F.Hub->GetActorUpVector() * Body->GetScaledCapsuleHalfHeight();
            FCollisionQueryParams Query(SCENE_QUERY_STAT(SSFunctionalStaffSupport), false, F.Walker);
            Query.AddIgnoredComponent(Body);
            FHitResult Floor;
            const bool Supported =
                F.World->LineTraceSingleByChannel(Floor, Foot + F.Hub->GetActorUpVector() * 20.f,
                                                  Foot - F.Hub->GetActorUpVector() * 20.f, ECC_Pawn, Query);
            TestTrue(TEXT("Each staff body stands on the real deck rather than floating or clipping"),
                     Supported && Floor.GetActor() == F.Hub && Floor.GetComponent() &&
                         Floor.GetComponent()->ComponentHasTag(TEXT("StationFunctionalFloor")) &&
                         FVector::Dist(Foot, Floor.ImpactPoint) < 1.f);
        }
        TestEqual(TEXT("Both visible staff have their own native blocking capsule"), PhysicalStaff, 2);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSStationResetWardrobe, "SpaceSurvival.Integration.StationResetWardrobe",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSStationResetWardrobe::RunTest(const FString &)
{
    for (bool Home : {true, false})
    {
        FSSFunctionalStationWorld F;
        if (!F.Initialize(*this, Home))
            return false;
        FVector Service;
        if (!TestTrue(TEXT("Home and mid-run hubs expose the wardrobe service"),
                      F.Hub->ServicePosition(ESSPanel::Wardrobe, Service)))
            return false;
        F.Walker->SetActorLocation(Service + F.Hub->GetActorUpVector() * 100.f);
        F.Mode->Interact();
        if (!TestTrue(TEXT("The nearby physical console opens the actual wardrobe panel"),
                      F.Mode->Panel == ESSPanel::Wardrobe))
            return false;
        const TArray<FSSHeroDefinition> Bodies = F.Mode->WardrobeBodies();
        if (!TestTrue(TEXT("Installed wardrobe offers at least two usable body choices"), Bodies.Num() >= 2))
            return false;
        int32 Changed = 0;
        for (int32 Index = 0; Index < Bodies.Num() && Index < 8; ++Index)
        {
            const int32 Entry = F.Mode->Entries.IndexOfByPredicate([Index](const FSSMenuEntry &Item)
                                                                   { return Item.Action == 140 + Index; });
            if (!TestTrue(TEXT("Each installed body has a real wardrobe action"), Entry != INDEX_NONE))
                return false;
            if (F.Mode->Entries[Entry].Enabled)
            {
                F.Mode->ActivateEntry(Entry);
                ++Changed;
                TestEqual(TEXT("Selecting a body updates the isolated account choice"),
                          F.Instance->Session.account.hero, static_cast<int>(Bodies[Index].Identity));
            }
            TestEqual(TEXT("Wardrobe action changes the actual walking hero"), F.Walker->GetHero().Id,
                      Bodies[Index].Id);
            TestEqual(TEXT("The visible mesh matches the selected installed body"),
                      GetPathNameSafe(F.Walker->GetMesh()->GetSkeletalMeshAsset()), Bodies[Index].MeshPath);
        }
        TestTrue(TEXT("The wardrobe performs an actual body change"), Changed > 0);
        TestTrue(TEXT("No wardrobe action can write personal account storage"), F.Instance->AccountStorageBlocked);
        TestFalse(TEXT("Wardrobe fixture never entered production mode BeginPlay"), F.Mode->HasActorBegunPlay());
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSStationPhoenixPaintCapability,
                                 "SpaceSurvival.Integration.StationPhoenixPaintCapability",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSStationPhoenixPaintCapability::RunTest(const FString &)
{
    FSSFunctionalStationWorld F;
    if (!F.Initialize(*this, true))
        return false;
    auto *Ship = F.Mode->GetPlayerShip();
    if (!TestTrue(TEXT("Paint fixture uses the actual supplied Phoenix rig"),
                  Ship && Ship->GetVisualRig() && Ship->GetVisualRig()->HasBlueprintRig() &&
                      Ship->GetVisualRig()->GetHull()))
        return false;
    TMap<UMeshComponent *, TArray<UMaterialInterface *>> AuthoredMaterials;
    TInlineComponentArray<UMeshComponent *> Meshes(Ship->GetVisualRig()->GetHull()->GetOwner());
    for (auto *Mesh : Meshes)
        AuthoredMaterials.Add(Mesh, Mesh->GetMaterials());
    F.Instance->Session.account.paint = {{3, 4, 5, 6}};
    const auto SavedPaint = F.Instance->Session.account.paint;
    FVector Service;
    if (!TestTrue(TEXT("Physical paint console exists"), F.Hub->ServicePosition(ESSPanel::Paint, Service)))
        return false;
    F.Walker->SetActorLocation(Service + F.Hub->GetActorUpVector() * 100.f);
    F.Mode->Interact();
    if (!TestTrue(TEXT("Physical console opens the actual paint service"), F.Mode->Panel == ESSPanel::Paint))
        return false;
    for (int32 Section = 0; Section < SS::PaintSections; ++Section)
    {
        TestFalse(TEXT("The supplied Phoenix does not advertise unsupported paint sections"),
                  SSPaint::SupportsSection(Ship, Section));
        for (const auto &Entry : F.Mode->Entries)
            if (Entry.Action >= 121 && Entry.Action <= 131)
                TestFalse(TEXT("Unsupported finish controls are disabled"), Entry.Enabled);
        TestTrue(TEXT("The service explains that the factory finish remains"),
                 F.Mode->PanelDetail.Contains(TEXT("factory finish")));
        for (int32 Action : {121, 131})
        {
            const int32 Index = F.Mode->Entries.IndexOfByPredicate([Action](const FSSMenuEntry &Entry)
                                                                   { return Entry.Action == Action; });
            if (!TestTrue(TEXT("The finish action remains visible"), Index != INDEX_NONE))
                return false;
            // Simulate an enabled entry retained from a previous hull. Activation must check capability again.
            F.Mode->Entries[Index].Enabled = true;
            F.Mode->ActivateEntry(Index);
            TestTrue(TEXT("A stale colour or factory action preserves all saved classic paint choices"),
                     F.Instance->Session.account.paint == SavedPaint);
        }
        const int32 Next =
            F.Mode->Entries.IndexOfByPredicate([](const FSSMenuEntry &Entry) { return Entry.Action == 120; });
        if (!TestTrue(TEXT("All sections can still be inspected"), Next != INDEX_NONE))
            return false;
        F.Mode->ActivateEntry(Next);
    }
    Ship->RefreshPaint();
    for (const auto &Pair : AuthoredMaterials)
        TestTrue(TEXT("Paint service preserves every supplied hull, engine, glass and light material"),
                 Pair.Key->GetMaterials() == Pair.Value);
    TestTrue(TEXT("Paint fixture cannot write personal account files"), F.Instance->AccountStorageBlocked);
    return true;
}
#endif
