#include "SSWorldActors.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSDirectorArrivalPresentation,
                                 "SpaceSurvival.Presentation.DirectorArrivalPresentation",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSDirectorArrivalPresentation::RunTest(const FString &)
{
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Isolated arrival world"), World))
        return false;
    GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    ON_SCOPE_EXIT
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
    };
    for (ESSWorldKind Kind : {ESSWorldKind::SmallAsteroid, ESSWorldKind::MediumAsteroid, ESSWorldKind::MassiveAsteroid})
    {
        auto *Rock = World->SpawnActor<ASSWorldBody>(FVector(1000, 0, 0), FRotator::ZeroRotator);
        if (!TestNotNull(TEXT("Spawn actual Director body"), Rock))
            return false;
        Rock->bDirectorAsteroid = true;
        Rock->Configure(Kind, 350.f, 18.f);
        auto *Material = Cast<UMaterialInstanceDynamic>(Rock->Visual->GetMaterial(0));
        if (!TestNotNull(TEXT("Director body has actual private dynamic material"), Material))
            return false;
        float Visibility = 0.f;
        if (!TestTrue(TEXT("Authored arrival parameter is present"),
                      Material->GetScalarParameterValue(FMaterialParameterInfo(TEXT("SpawnVisibility")), Visibility)))
            return false;
        TestEqual(TEXT("Birth begins with readable fifteen percent coverage"), Visibility, .15f);
        TestTrue(TEXT("Private arrival material is masked"), Material->GetBlendMode() == BLEND_Masked);
        TestTrue(TEXT("Native blue-noise mask is enabled"), Material->GetMaterial()->DitherOpacityMask != 0);
        TestEqual(TEXT("Native mask uses the authored endpoint convention"), Material->GetOpacityMaskClipValue(), .5f);
        const FVector Drift(100, 20, -10);
        Rock->SetLinearVelocity(Drift);
        const FVector Origin = Rock->GetActorLocation();
        const FVector Scale = Rock->Visual->GetRelativeScale3D();
        const float Lifetime = Rock->LifetimeSeconds;
        const float Telegraph = Rock->TelegraphSeconds;
        float Elapsed = 0.f;
        for (const float Delta : {.15f, .15f, .20f})
        {
            Rock->Tick(Delta);
            Elapsed += Delta;
            Material->GetScalarParameterValue(FMaterialParameterInfo(TEXT("SpawnVisibility")), Visibility);
            const float ExpectedVisibility = Elapsed < .30f ? .575f : 1.f;
            TestTrue(FString::Printf(TEXT("Arrival coverage at %.3fs: actual %.9f, expected %.9f"), Elapsed, Visibility,
                                     ExpectedVisibility),
                     FMath::IsNearlyEqual(Visibility, ExpectedVisibility, 1.e-6f));
            TestTrue(TEXT("Birth leaves the ordinary drift trajectory unchanged"),
                     Rock->GetActorLocation().Equals(Origin + Drift * Elapsed, .001));
            TestTrue(TEXT("Birth never changes visible scale"), Rock->Visual->GetRelativeScale3D().Equals(Scale));
            TestEqual(TEXT("Birth never changes collision radius"), Rock->Collision->GetUnscaledSphereRadius(), 350.f);
            TestTrue(TEXT("Birth preserves query collision"),
                     Rock->Collision->GetCollisionEnabled() == ECollisionEnabled::QueryOnly);
            TestTrue(TEXT("Birth preserves weapon blocking"),
                     Rock->Collision->GetCollisionResponseToChannel(ECC_Visibility) == ECR_Block);
            TestEqual(TEXT("Birth leaves lifetime unchanged"), Rock->LifetimeSeconds, Lifetime);
            TestEqual(TEXT("Birth leaves reaction timing unchanged"), Rock->TelegraphSeconds, Telegraph);
        }
        Rock->Destroy();
    }
    return true;
}
#endif
