#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "GameFramework/PlayerController.h"
#include "SSCryoPreview.generated.h"

class ASSCryoChamber;
class UCameraComponent;

/** Asset-only review pawn; production uses the existing SpaceSurvival walker and terminal. */
UCLASS()
class SSCRYORUNTIME_API ASSCryoPreviewPawn : public ACharacter
{
    GENERATED_BODY()
public:
    ASSCryoPreviewPawn();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo")
    TObjectPtr<UCameraComponent> Camera;
};

UCLASS()
class SSCRYORUNTIME_API ASSCryoPreviewController : public APlayerController
{
    GENERATED_BODY()
public:
    virtual void BeginPlay() override;
    virtual void SetupInputComponent() override;
    virtual void PlayerTick(float DeltaSeconds) override;
    UFUNCTION(BlueprintCallable, Category = "Cryo")
    void Interact();
    UFUNCTION(BlueprintPure, Category = "Cryo")
    ASSCryoChamber *FocusedChamber() const;
    FString Notice;
    float NoticeSeconds = 0.f;
};

UCLASS()
class SSCRYORUNTIME_API ASSCryoPreviewHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
};

UCLASS()
class SSCRYORUNTIME_API ASSCryoPreviewGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    ASSCryoPreviewGameMode();
};
