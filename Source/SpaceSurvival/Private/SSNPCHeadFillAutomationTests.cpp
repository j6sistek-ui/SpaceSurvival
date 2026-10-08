#include "Misc/AutomationTest.h"
#include "SSNPCHeadFillComponent.h"
#include "SSOutpostSandbox.h"
#include "Animation/SkeletalMeshActor.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"

#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR
namespace
{
struct FSSNPCFillTestWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;

    bool Initialize(FAutomationTestBase &Test)
    {
        UWorld::InitializationValues Values;
        Values.CreatePhysicsScene(true)
            .ShouldSimulatePhysics(false)
            .AllowAudioPlayback(false)
            .RequiresHitProxies(false)
            .CreateNavigation(false)
            .CreateAISystem(false);
        World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
        if (!Test.TestNotNull(TEXT("Create isolated NPC fill world"), World))
            return false;
        GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
        GWorld = World;
        World->InitializeActorsForPlay(FURL());
        World->SetBegunPlay(true);
        return true;
    }
    ~FSSNPCFillTestWorld()
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSNPCHeadFillLifecycle, "SpaceSurvival.Presentation.NPCHeadFillLifecycle",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSNPCHeadFillLifecycle::RunTest(const FString &)
{
    // A missing licensed receiver is a failure, not a passing source-only skip.
    auto *Nyxar = LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/Nyxar/Meshes/SKM_Nyxar.SKM_Nyxar"));
    if (!TestNotNull(TEXT("Actual station Nyxar receiver loads"), Nyxar))
        return false;
    bool bOpaqueMaterial = false;
    for (const auto &Slot : Nyxar->GetMaterials())
        if (const auto *Material = Slot.MaterialInterface.Get())
            bOpaqueMaterial |= Material->GetBlendMode() == BLEND_Opaque || Material->GetBlendMode() == BLEND_Masked;
    if (!TestTrue(TEXT("Actual receiver has an opaque or masked material"), bOpaqueMaterial))
        return false;

    FSSNPCFillTestWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    auto *Plain = Fixture.World->SpawnActor<ASkeletalMeshActor>();
    auto *Ambient = Fixture.World->SpawnActor<ASSOutpostAmbientActor>(FVector(300, 0, 0), FRotator::ZeroRotator);
    if (!TestNotNull(TEXT("Create plain sequence-compatible skeletal actor"), Plain) ||
        !TestNotNull(TEXT("Create Ambient actor with its original light"), Ambient))
        return false;
    auto *PlainMesh = Plain->GetSkeletalMeshComponent();
    PlainMesh->SetSkeletalMeshAsset(Nyxar);
    PlainMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    PlainMesh->SetLightingChannels(true, true, false);
    Ambient->CharacterMesh->SetSkeletalMeshAsset(Nyxar);
    Ambient->CharacterMesh->SetLightingChannels(false, true, true);
    if (!TestTrue(TEXT("Actual head socket exists on both receivers"),
                  PlainMesh->DoesSocketExist(TEXT("head")) && Ambient->CharacterMesh->DoesSocketExist(TEXT("head"))))
        return false;
    const FLightingChannels PlainBefore = PlainMesh->LightingChannels;
    const FLightingChannels AmbientBefore = Ambient->CharacterMesh->LightingChannels;
    auto CheckChannels =
        [this](const TCHAR *Label, const USkeletalMeshComponent *Mesh, const FLightingChannels &Expected)
    {
        TestTrue(Label, Mesh->LightingChannels.bChannel0 == Expected.bChannel0 &&
                            Mesh->LightingChannels.bChannel1 == Expected.bChannel1 &&
                            Mesh->LightingChannels.bChannel2 == Expected.bChannel2);
    };

    auto *Configuration = USSNPCHeadFillComponent::EnrollNPCMesh(PlainMesh);
    if (!TestNotNull(TEXT("Explicitly enroll the actual plain NPC mesh"), Configuration) ||
        !TestNotNull(TEXT("Enrollment creates its owned light"), Configuration->HeadFillLight.Get()))
        return false;
    auto *OwnedLight = Configuration->HeadFillLight.Get();
    TestTrue(TEXT("Repeated enrollment returns the same configuration and light"),
             USSNPCHeadFillComponent::EnrollNPCMesh(PlainMesh) == Configuration &&
                 Configuration->HeadFillLight == OwnedLight &&
                 TInlineComponentArray<USSNPCHeadFillComponent *>(Plain).Num() == 1 &&
                 TInlineComponentArray<UPointLightComponent *>(Plain).Num() == 1);
    Configuration->RefreshReadabilityLighting();
    Configuration->ReregisterComponent();
    TestTrue(TEXT("Plain receiver stays lit after refresh and native reregistration"),
             OwnedLight->IsVisible() && PlainMesh->LightingChannels.bChannel2 &&
                 PlainMesh->LightingChannels.bChannel0 == PlainBefore.bChannel0 &&
                 PlainMesh->LightingChannels.bChannel1 == PlainBefore.bChannel1);
    Configuration->DisableAndRestoreReceiver();
    TestFalse(TEXT("Disabling hides the owned light"), OwnedLight->IsVisible());
    CheckChannels(TEXT("Disabling restores every original plain receiver channel"), PlainMesh, PlainBefore);
    Configuration->RefreshReadabilityLighting();
    const TWeakObjectPtr<UPointLightComponent> OwnedLightLifetime(OwnedLight);
    Configuration->DestroyComponent();
    TestFalse(TEXT("Removing enrollment destroys only its owned light"), OwnedLightLifetime.IsValid());
    CheckChannels(TEXT("Owned-light teardown restores plain receiver channels"), PlainMesh, PlainBefore);

    auto *BorrowedLight = Ambient->HeadFillLight.Get();
    if (!TestNotNull(TEXT("Ambient retains its original light subobject"), BorrowedLight) ||
        !TestNotNull(TEXT("Ambient has the shared configurator"), Ambient->HeadFillConfiguration.Get()))
        return false;
    Ambient->RefreshReadabilityLighting();
    TestTrue(TEXT("Ambient refresh borrows its original light"),
             Ambient->HeadFillConfiguration->HeadFillLight == BorrowedLight && BorrowedLight->IsVisible());
    // Regression: OnUnregister turned this off, while an Ambient-skipping OnRegister never reactivated it.
    Ambient->HeadFillConfiguration->ReregisterComponent();
    TestTrue(TEXT("Ambient native reregistration reactivates its authoritative head fill"),
             BorrowedLight->IsVisible() && Ambient->CharacterMesh->LightingChannels.bChannel2);
    const TWeakObjectPtr<UPointLightComponent> BorrowedLightLifetime(BorrowedLight);
    Ambient->HeadFillConfiguration->DestroyComponent();
    TestTrue(TEXT("Configurator teardown preserves the Ambient-owned light"),
             BorrowedLightLifetime.IsValid() && BorrowedLight->IsRegistered() && !BorrowedLight->IsVisible() &&
                 Ambient->HeadFillLight == BorrowedLight);
    CheckChannels(TEXT("Borrowed-light teardown preserves preexisting channel2 and channels0/1"),
                  Ambient->CharacterMesh, AmbientBefore);
    return true;
}
#endif
