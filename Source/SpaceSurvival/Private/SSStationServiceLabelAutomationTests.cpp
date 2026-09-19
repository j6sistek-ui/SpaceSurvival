#include "Misc/AutomationTest.h"
#include "SSStation.h"
#include "Camera/CameraActor.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/TextRenderComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Materials/MaterialInterface.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSStationServiceLabelView, "SpaceSurvival.Integration.StationServiceLabelView",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSStationServiceLabelView::RunTest(const FString &)
{
    auto *World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Create isolated service-label world"), World))
        return false;
    GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    auto *Hub = World->SpawnActor<ASSStation>(FVector(16000, -8000, 5000), FRotator(0, 75, 0));
    Hub->BuildHub(false);
    auto *Controller = World->SpawnActor<APlayerController>();
    Controller->SetAsLocalPlayerController();
    World->AddController(Controller);
    Controller->SpawnPlayerCameraManager();
    auto *FrontCamera = World->SpawnActor<ACameraActor>();
    auto *RearCamera = World->SpawnActor<ACameraActor>();
    FrontCamera->SetActorLocation(Hub->GetActorTransform().TransformPosition(FVector(-1400, -500, 350)));
    RearCamera->SetActorLocation(Hub->GetActorTransform().TransformPosition(FVector(1700, 500, 650)));

    TInlineComponentArray<UTextRenderComponent *> Texts(Hub);
    TArray<FTransform> InitialTransforms;
    TArray<FString> InitialText;
    int32 ServiceCount = 0;
    for (auto *Text : Texts)
    {
        InitialTransforms.Add(Text->GetComponentTransform());
        InitialText.Add(Text->Text.ToString());
        ServiceCount += Text->ComponentHasTag(TEXT("StationServiceLabel")) ? 1 : 0;
    }
    // Nine inside, plus the two on the exterior landing pad - a pit stop's worth of services where the
    // ship actually parks, so arriving does not mean walking inside before anything can be done.
    // Twelve since the crew wardrobe joined them. The count is pinned rather than just "more than
    // zero" because a service whose label silently stops facing the player is invisible in exactly
    // the way this test exists to catch.
    TestEqual(TEXT("All twelve live service labels participate in view-facing presentation"), ServiceCount, 12);
    for (auto *Camera : {FrontCamera, RearCamera})
    {
        Controller->SetViewTarget(Camera);
        Controller->PlayerCameraManager->UpdateCamera(.016f);
        Hub->Tick(.016f);
        for (int32 Index = 0; Index < Texts.Num(); ++Index)
        {
            auto *Text = Texts[Index];
            TestEqual(TEXT("View changes preserve label wording"), Text->Text.ToString(), InitialText[Index]);
            if (Text->ComponentHasTag(TEXT("StationServiceLabel")))
            {
                auto *Material = Text->GetMaterial(0);
                TestTrue(TEXT("Service labels use an unlit material so shadowed stations keep readable text"),
                         Material && Material->GetShadingModels().HasOnlyShadingModel(MSM_Unlit));
                // UE text quads face local +X; a camera on that side sees the readable front face.
                const FVector TowardView =
                    (Camera->GetActorLocation() - Text->GetComponentLocation()).GetSafeNormal2D();
                TestTrue(TEXT("Opposite active view targets both see the readable front of each service label"),
                         FVector::DotProduct(Text->GetForwardVector(), TowardView) > .999);
                TestTrue(TEXT("Labels remain upright and anchored without casting shadows"),
                         Text->GetUpVector().Equals(FVector::UpVector, .0001) && !Text->CastShadow &&
                             Text->GetComponentLocation().Equals(InitialTransforms[Index].GetLocation(), .0001));
                const FVector Anchor =
                    Hub->GetActorTransform().TransformPosition(Text->GetRelativeLocation() - FVector(-55, 0, 190));
                FString ServiceLabel;
                TestTrue(TEXT("Facing a different camera preserves each service interaction and its label"),
                         Hub->NearestService(Anchor, ServiceLabel) != ESSPanel::None &&
                             ServiceLabel == InitialText[Index]);
            }
            else
                TestTrue(TEXT("Authored wall plaque remains fixed"),
                         Text->GetComponentTransform().Equals(InitialTransforms[Index], .0001));
        }
    }
    Hub->Destroy();
    GEngine->DestroyWorldContext(World);
    World->DestroyWorld(false);
    return true;
}
#endif
