#include "SSVFXPresentation.h"
#include "SSWorldActors.h"
#include "Components/SceneComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/AutomationTest.h"
#include "Misc/PackageName.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "UObject/Package.h"
#include "UObject/UObjectIterator.h"
#include "UObject/UnrealType.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
constexpr const TCHAR *CombatDataPath = TEXT("/Game/SpaceSurvival/Licensed/Combat/DA_CombatVisuals");

TArray<UNiagaraComponent *> AttachedEffects(UWorld *World, UNiagaraSystem *System = nullptr)
{
    TArray<UNiagaraComponent *> Result;
    for (TObjectIterator<UNiagaraComponent> It; It; ++It)
        if (IsValid(*It) && It->GetWorld() == World && It->GetAttachParent() && (!System || It->GetAsset() == System))
            Result.Add(*It);
    return Result;
}

struct FSSCombatVFXFixture
{
    UWorld *World = nullptr, *PreviousWorld = nullptr;
    USSCombatVFXSubsystem *FX = nullptr;
    USSCombatVFXData *Data = nullptr;

    bool Initialize(FAutomationTestBase &Test, USSCombatVFXData *Template)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated combat presentation world"), World))
            return false;
        GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
        PreviousWorld = GWorld;
        GWorld = World;
        FX = World->GetSubsystem<USSCombatVFXSubsystem>();
        if (!Test.TestNotNull(TEXT("Actual combat presentation subsystem exists"), FX))
            return false;
        // Install a transient copy in this fixture only. No source DataAsset,
        // production world, GameInstance, slot, package or source file is edited.
        const auto *Property =
            FindFProperty<FObjectPropertyBase>(USSCombatVFXSubsystem::StaticClass(), TEXT("Presentation"));
        if (!Test.TestNotNull(TEXT("Reflected presentation boundary exists"), Property))
            return false;
        if (Template)
        {
            Data = DuplicateObject<USSCombatVFXData>(Template, FX);
            Data->SetFlags(RF_Transient);
            Data->ClearFlags(RF_Public | RF_Standalone);
        }
        Property->SetObjectPropertyValue_InContainer(FX, Data);
        World->InitializeActorsForPlay(FURL());
        World->BeginPlay();
        World->GetWorldSettings()->NotifyBeginPlay();
        return true;
    }

    ASSCombatVFXAnchor *Owner(FVector Position = FVector(1000, 0, 0))
    {
        return World->SpawnActor<ASSCombatVFXAnchor>(Position, FRotator::ZeroRotator);
    }

    ~FSSCombatVFXFixture()
    {
        if (World)
        {
            World->EndPlay(EEndPlayReason::Quit);
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
            GWorld = PreviousWorld;
        }
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSCombatVFXFallback, "SpaceSurvival.Presentation.CombatVFXFallback",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSCombatVFXFallback::RunTest(const FString &)
{
    FSSCombatVFXFixture Fixture;
    if (!Fixture.Initialize(*this, nullptr))
        return false;
    auto *Owner = Fixture.Owner();
    if (!TestNotNull(TEXT("Fallback fixture owner exists"), Owner))
        return false;
    TestFalse(TEXT("Null projectile is safe"), Fixture.FX->AttachProjectile(nullptr, true, false));
    TestFalse(TEXT("Absent private presentation preserves projectile fallback"),
              Fixture.FX->AttachProjectile(Owner, true, false));
    TestFalse(TEXT("Absent private presentation preserves anomaly fallback"), Fixture.FX->AttachAnomaly(Owner));
    Fixture.FX->PlayMuzzle(Owner, Owner->GetActorLocation(), FVector::ForwardVector, true, false);
    Fixture.FX->PlayImpact(Owner->GetActorLocation(), FVector::UpVector, false, false);
    Fixture.FX->PlayEnemyExplosion(Owner->GetActorLocation(), 140.f);
    Fixture.FX->Tick(10.f);
    TestEqual(TEXT("Absent art allocates no cosmetic systems"), AttachedEffects(Fixture.World).Num(), 0);

    auto *Projectile = Fixture.World->SpawnActor<ASSProjectile>(FVector(3000, 0, 0), FRotator::ZeroRotator);
    if (TestNotNull(TEXT("Actual gameplay projectile exists without VFX data"), Projectile))
    {
        Projectile->Launch(FVector::ForwardVector, 55000.f, 0.f, true, Owner, 1000.f);
        TestTrue(TEXT("Native projectile core remains visible without Niagara"), Projectile->Visual->IsVisible());
        TestNotNull(TEXT("Native projectile core keeps a mesh"), Projectile->Visual->GetStaticMesh().Get());
        TestEqual(TEXT("Presentation does not change the player collision radius"), Projectile->GetBodyRadius(), 28.f);
        TestEqual(TEXT("Presentation does not change the six-second projectile lifetime"), Projectile->LifetimeSeconds,
                  6.f);
        TestTrue(TEXT("Existing swept collision authority remains unchanged"),
                 Projectile->Collision->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
        Projectile->Tick(.03f);
        TestTrue(TEXT("Actual tracer remains clipped to its maximum travel"),
                 Projectile->GetActorLocation().Equals(FVector(4000, 0, 0), .001));
        // This speed/range leaves a positive remainder below the engine's
        // minimum vector-clamp distance. It must retire on this same tick.
        TestTrue(TEXT("Actual tracer retires immediately at the engine-precision travel limit"),
                 Projectile->IsActorBeingDestroyed());
    }
    TestFalse(TEXT("Private preparation rejects null systems"),
              USSVFXPresentationLibrary::PreparePrivateSystem(nullptr, true));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSCombatVFXLifecycle, "SpaceSurvival.Presentation.CombatVFXLifecycle",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter |
                                     EAutomationTestFlags::NonNullRHI)
bool FSSCombatVFXLifecycle::RunTest(const FString &)
{
    if (!TestTrue(TEXT("Real Niagara lifecycle validation requires authored private combat content"),
                  FPackageName::DoesPackageExist(CombatDataPath)))
        return false;
    auto *Authored = LoadObject<USSCombatVFXData>(nullptr, CombatDataPath);
    if (!TestNotNull(TEXT("Authored combat data loads"), Authored))
        return false;
    const bool bOriginallyDirty = Authored->GetOutermost()->IsDirty();
    FSSCombatVFXFixture Fixture;
    if (!Fixture.Initialize(*this, Authored))
        return false;
    auto *Rapid = Fixture.Data->Effects.FindByPredicate([](const FSSCombatVFXDefinition &Row)
                                                        { return Row.Kind == ESSCombatVFX::RapidBolt; });
    auto *Enemy = Fixture.Data->Effects.FindByPredicate([](const FSSCombatVFXDefinition &Row)
                                                        { return Row.Kind == ESSCombatVFX::EnemyBolt; });
    if (!TestNotNull(TEXT("Authored rapid bolt definition"), Rapid) ||
        !TestNotNull(TEXT("Authored enemy bolt definition"), Enemy) ||
        !TestNotNull(TEXT("Real rapid Niagara system"), Rapid->System.Get()) ||
        !TestNotNull(TEXT("Real enemy Niagara system"), Enemy->System.Get()))
        return false;
    auto *OwnerA = Fixture.Owner();
    auto *OwnerB = Fixture.Owner(FVector(1500, 0, 0));
    if (!TestNotNull(TEXT("First cosmetic owner"), OwnerA) || !TestNotNull(TEXT("Second cosmetic owner"), OwnerB))
        return false;

    Fixture.Data->MaximumActive = 2;
    Rapid->ActiveLimit = 1;
    Enemy->ActiveLimit = 1;
    TestTrue(TEXT("Actual rapid Niagara allocates through the public hook"),
             Fixture.FX->AttachProjectile(OwnerA, true, false));
    TestFalse(TEXT("Per-kind cap rejects a second rapid bolt"), Fixture.FX->AttachProjectile(OwnerB, true, false));
    TestTrue(TEXT("Another kind can use remaining shared capacity"),
             Fixture.FX->AttachProjectile(OwnerB, false, false));
    TestFalse(TEXT("Global cap rejects another otherwise permitted kind"),
              Fixture.FX->AttachProjectile(OwnerA, true, true));
    auto Components = AttachedEffects(Fixture.World);
    TestEqual(TEXT("Caps bound actual attached Niagara components"), Components.Num(), 2);
    for (auto *Component : Components)
    {
        TestTrue(TEXT("Cosmetic components have no collision"),
                 Component->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
        TestFalse(TEXT("Cosmetic components have no overlap events"), Component->GetGenerateOverlapEvents());
        TestFalse(TEXT("Cosmetic components cast no shadows"), Component->CastShadow);
        TestTrue(TEXT("System uses finite authored bounds"),
                 Component->GetSystemFixedBounds().IsValid &&
                     !Component->GetSystemFixedBounds().GetSize().ContainsNaN());
    }
    Fixture.FX->Tick(9.f);
    TestEqual(TEXT("Hard lifetime releases every actual component, including looping systems"),
              AttachedEffects(Fixture.World).Num(), 0);
    TestTrue(TEXT("Expired effects return their admission capacity"),
             Fixture.FX->AttachProjectile(OwnerA, true, false));
    OwnerA->Destroy();
    Fixture.FX->Tick(0.f);
    TestEqual(TEXT("Owner destruction retires the attached effect immediately at the next subsystem tick"),
              AttachedEffects(Fixture.World).Num(), 0);
    for (int32 Cycle = 0; Cycle < 4; ++Cycle)
    {
        TestTrue(TEXT("Subsequent pool acquisitions remain usable"),
                 Fixture.FX->AttachProjectile(OwnerB, false, false));
        Fixture.FX->Tick(9.f);
        TestEqual(TEXT("Pool release leaves no stale active attachment"), AttachedEffects(Fixture.World).Num(), 0);
    }

    Fixture.FX->PlayEnemyExplosion(FVector(4500, 700, -90), 140.f);
    Components = AttachedEffects(Fixture.World);
    if (TestEqual(TEXT("Actual death hook emits one bounded explosion"), Components.Num(), 1))
    {
        UNiagaraComponent *Explosion = Components[0];
        const FVector Before = Explosion->GetComponentLocation();
        AActor *Anchor = Explosion->GetAttachParent()->GetOwner();
        TestTrue(TEXT("World burst has cosmetic actor ownership"), Anchor->IsA<ASSCombatVFXAnchor>());
        const FVector Shift(-100000, 25000, -500);
        Anchor->ApplyWorldOffset(Shift, true);
        TestTrue(TEXT("Burst placement follows the actual origin-shift actor path exactly once"),
                 Explosion->GetComponentLocation().Equals(Before + Shift, .01));
    }
    Fixture.FX->Tick(9.f);

    // Renderer-enabled negative paths use the same live templates, so an empty
    // template or disabled renderer cannot falsely establish these budget gates.
    Fixture.Data->MaximumActive = 0;
    TestFalse(TEXT("Zero shared budget explicitly disables allocations"),
              Fixture.FX->AttachProjectile(OwnerB, false, false));
    Fixture.Data->MaximumActive = 2;
    Enemy->ActiveLimit = 0;
    TestFalse(TEXT("Zero per-kind budget explicitly disables that kind"),
              Fixture.FX->AttachProjectile(OwnerB, false, false));
    Enemy->ActiveLimit = 1;
    Enemy->System = nullptr;
    TestFalse(TEXT("Null system inside valid data uses fallback safely"),
              Fixture.FX->AttachProjectile(OwnerB, false, false));
    TestEqual(TEXT("Negative paths leave no active allocations"), AttachedEffects(Fixture.World).Num(), 0);
    TestEqual(TEXT("Fixture tuning preserves source data dirty state"), Authored->GetOutermost()->IsDirty(),
              bOriginallyDirty);
    AddInfo(TEXT("Tests component admission, pooling, ownership and origin placement with real Niagara. "
                 "It does not establish particle appearance, GPU cost or player readability."));
    return true;
}
#endif
