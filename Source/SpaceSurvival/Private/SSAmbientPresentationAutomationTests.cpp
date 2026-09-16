#include "SSAmbientPresentation.h"
#include "SSSpaceLookData.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/TextureCube.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/IConsoleManager.h"
#include "MaterialDomain.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/AutomationTest.h"
#include "Misc/PackageName.h"
#include "Misc/ScopeExit.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
/** A stock world and inert viewer: no game session, Director, input or save initialization. */
struct FSSAmbientWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    UGameInstance *Instance = nullptr;
    AActor *Viewer = nullptr;
    ASSAmbientPresentation *Presentation = nullptr;

    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated atmosphere world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<UGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // Do not call Init or InitializeStandalone. The generic instance has no game persistence code.
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        GWorld = World;
        World->GetWorldSettings()->DefaultGameMode = AGameModeBase::StaticClass();
        if (!Test.TestTrue(TEXT("Install stock atmosphere fixture GameMode"), World->SetGameMode(FURL())))
            return false;
        World->InitializeActorsForPlay(FURL());
        Viewer = World->SpawnActor<AActor>();
        Presentation = World->SpawnActor<ASSAmbientPresentation>();
        if (!Test.TestNotNull(TEXT("Spawn inert atmosphere viewer"), Viewer) ||
            !Test.TestNotNull(TEXT("Spawn actual atmosphere actor"), Presentation))
            return false;
        auto *ViewerRoot = NewObject<USceneComponent>(Viewer);
        Viewer->SetRootComponent(ViewerRoot);
        ViewerRoot->RegisterComponent();
        Viewer->SetActorLocation(FVector(12000, -4000, 7000));
        World->BeginPlay();
        return Test.TestTrue(TEXT("Actual atmosphere BeginPlay loaded optional content"),
                             Presentation->HasActorBegunPlay());
    }

    ~FSSAmbientWorld()
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSAmbientPresentationContent, "SpaceSurvival.Presentation.SpaceLookIntegration",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSAmbientPresentationContent::RunTest(const FString &)
{
    IConsoleVariable *CloudSwitch = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.AtmosphereClouds"));
    if (!TestNotNull(TEXT("Cloud scalability control exists"), CloudSwitch))
        return false;
    const int32 PreviousCloudSwitch = CloudSwitch->GetInt();
    const EConsoleVariableFlags Priority = EConsoleVariableFlags(CloudSwitch->GetFlags() & ECVF_SetByMask);
    ON_SCOPE_EXIT
    {
        CloudSwitch->Set(PreviousCloudSwitch, Priority);
    };
    CloudSwitch->Set(1, Priority);
    FSSAmbientWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    const TCHAR *LookPath = TEXT("/Game/SpaceSurvival/Licensed/Atmosphere/DA_DeepSpaceLook");
    const bool HasPrivateLook = FPackageName::DoesPackageExist(LookPath);
    auto *Look = HasPrivateLook ? LoadObject<USSSpaceLookData>(nullptr, LookPath) : nullptr;
    if (HasPrivateLook && !TestNotNull(TEXT("Present private look package loads its declared data class"), Look))
        return false;
    auto *Fog = Fixture.Presentation->FindComponentByClass<UExponentialHeightFogComponent>();
    auto *Sky = Fixture.Presentation->FindComponentByClass<USkyLightComponent>();
    if (!TestNotNull(TEXT("Actual volume grid component exists"), Fog) ||
        !TestNotNull(TEXT("Actual ambient skylight component exists"), Sky))
        return false;
    TArray<UStaticMeshComponent *> Meshes;
    Fixture.Presentation->GetComponents(Meshes);
    TArray<UStaticMeshComponent *> Clouds;
    for (auto *Mesh : Meshes)
        if (Mesh->GetName().StartsWith(TEXT("CloudBank")))
            Clouds.Add(Mesh);
    if (!TestEqual(TEXT("Bounded atmosphere uses two cloud bank components"), Clouds.Num(), 2))
        return false;
    TArray<UPrimitiveComponent *> Primitives;
    Fixture.Presentation->GetComponents(Primitives);
    for (const auto *Primitive : Primitives)
    {
        TestTrue(TEXT("Every cosmetic primitive has no gameplay collision"),
                 Primitive->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
        TestFalse(TEXT("Every cosmetic primitive suppresses overlap events"), Primitive->GetGenerateOverlapEvents());
        TestFalse(TEXT("Every cosmetic primitive is excluded from navigation"), Primitive->CanEverAffectNavigation());
    }
    if (Look)
    {
        TestNotNull(TEXT("Private look declares a cloud material"), Look->CloudMaterial.Get());
        TestNotNull(TEXT("Private look declares an ambient cubemap"), Look->AmbientCubemap.Get());
        TestTrue(TEXT("Ambient component uses the declared cubemap"), Sky->Cubemap == Look->AmbientCubemap.Get());
        TestTrue(TEXT("Ambient component consumes the authored intensity"),
                 FMath::IsNearlyEqual(Sky->Intensity, Look->AmbientIntensity));
        TestTrue(TEXT("Fog grid consumes the authored density and distance"),
                 FMath::IsNearlyEqual(Fog->FogDensity, Look->FogDensity) &&
                     FMath::IsNearlyEqual(Fog->VolumetricFogDistance, Look->FogDistance));
        for (auto *Cloud : Clouds)
        {
            TestNotNull(TEXT("Private cloud has its actual bounds mesh"), Cloud->GetStaticMesh().Get());
            auto *Dynamic = Cast<UMaterialInstanceDynamic>(Cloud->GetMaterial(0));
            if (TestNotNull(TEXT("Cloud owns an instance rather than editing the shared vendor material"), Dynamic))
            {
                TestTrue(TEXT("Cloud instance belongs to its presentation actor"),
                         Dynamic->GetOuter() == Fixture.Presentation);
                const UMaterial *Base = Dynamic->GetMaterial();
                if (TestNotNull(TEXT("Cloud material resolves its actual base"), Base))
                    TestTrue(TEXT("Cloud bounds use a volume-domain material, not opaque surface shading"),
                             Base->MaterialDomain == MD_Volume);
            }
            TestFalse(TEXT("Cloud bounds are excluded from the depth pass"), Cloud->bRenderInDepthPass);
        }
        TestTrue(TEXT("Loaded cloud look enables the volumetric fog grid"), Fog->bEnableVolumetricFog);
    }
    else
    {
        AddInfo(
            TEXT("Private look absent: exercising source-only fallback, without claiming licensed asset coverage."));
        for (const auto *Cloud : Clouds)
        {
            TestNull(TEXT("Missing optional look leaves no cloud mesh"), Cloud->GetStaticMesh().Get());
            TestNull(TEXT("Missing optional look leaves no cloud material"), Cloud->GetMaterial(0));
        }
    }
    const bool CloudsAvailable = Look && Look->CloudMaterial;
    const bool SkyAvailable = Look && Look->AmbientCubemap;
    auto CheckVisibility = [&](bool ExpectClouds, bool ExpectSky)
    {
        TestEqual(TEXT("Fog grid visibility follows the flight/content/scalability gate"), Fog->IsVisible(),
                  ExpectClouds);
        TestEqual(TEXT("Ambient light visibility follows the flight/content gate"), Sky->IsVisible(), ExpectSky);
        for (const auto *Cloud : Clouds)
            TestEqual(TEXT("Cloud bank visibility agrees with its fog grid"), Cloud->IsVisible(), ExpectClouds);
    };
    CheckVisibility(false, false);
    auto *Key = Fixture.World->SpawnActor<ADirectionalLight>();
    auto *Fill = Fixture.World->SpawnActor<ADirectionalLight>();
    if (!TestNotNull(TEXT("Spawn authored scene key"), Key) || !TestNotNull(TEXT("Spawn independent fill"), Fill))
        return false;
    CastChecked<UDirectionalLightComponent>(Key->GetLightComponent())->ForwardShadingPriority = 2;
    CastChecked<UDirectionalLightComponent>(Fill->GetLightComponent())->ForwardShadingPriority = 1;
    Key->GetLightComponent()->SetMobility(EComponentMobility::Movable);
    Fill->GetLightComponent()->SetMobility(EComponentMobility::Movable);
    const FRotator StationRotation(-35, -40, 0), FillRotation(20, 140, 0);
    Key->SetActorRotation(StationRotation);
    Fill->SetActorRotation(FillRotation);
    auto *KeyComponent = CastChecked<UDirectionalLightComponent>(Key->GetLightComponent());
    KeyComponent->SetLightColor(FLinearColor(.4f, .7f, .8f));
    KeyComponent->SetIntensity(7.f);
    const FLinearColor StationColor = KeyComponent->GetLightColor();
    Fixture.Presentation->SetFlightVisible(true);
    TestTrue(TEXT("Flight optionally consumes the authored light direction"),
             Key->GetActorRotation().Equals(Look && Look->bOverrideFlightKeyDirection ? Look->FlightKeyRotation
                                                                                      : StationRotation));
    TestTrue(TEXT("Flight direction leaves other scene lights unchanged"),
             Fill->GetActorRotation().Equals(FillRotation));
    Fixture.Presentation->Tick(0.f);
    CheckVisibility(false, false); // Flight flag alone must not activate an unbound atmosphere.
    Fixture.Presentation->Follow(Fixture.Viewer);
    Fixture.Presentation->Tick(0.f);
    CheckVisibility(CloudsAvailable, SkyAvailable);
    CloudSwitch->Set(0, Priority);
    Fixture.Presentation->Tick(0.f);
    CheckVisibility(false, SkyAvailable); // Disabling expensive clouds must retain ambient hull/rock lighting.
    CloudSwitch->Set(1, Priority);
    Fixture.Presentation->Tick(0.f);
    CheckVisibility(CloudsAvailable, SkyAvailable);
    if (Look && Look->bOverrideFlightKeyDirection)
    {
        KeyComponent->SetLightColor(FLinearColor::Red);
        KeyComponent->SetIntensity(14.f);
    }
    Fixture.Presentation->SetFlightVisible(false);
    TestTrue(TEXT("Station entry restores the scene key direction"), Key->GetActorRotation().Equals(StationRotation));
    TestTrue(TEXT("Station entry restores key color after region presentation"),
             KeyComponent->GetLightColor().Equals(StationColor, .001f));
    TestTrue(TEXT("Station entry restores key intensity after region presentation"),
             FMath::IsNearlyEqual(KeyComponent->Intensity, 7.f));
    CheckVisibility(false, false); // Station entry hides the medium immediately, before the next frame.
    Fixture.Presentation->SetFlightVisible(true);
    Fixture.Presentation->Tick(0.f);
    CheckVisibility(CloudsAvailable, SkyAvailable);
    Fixture.Presentation->Follow(nullptr);
    Fixture.Presentation->Tick(0.f);
    CheckVisibility(false, false);
    AddInfo(TEXT("Component/data integration only; no rendered fog correctness, readability or performance claim."));
    return true;
}
#endif
