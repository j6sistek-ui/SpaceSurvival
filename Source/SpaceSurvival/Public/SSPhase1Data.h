#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "SSPhase1Data.generated.h"

/** Runtime tuning entry point. Asset content is authored by Scripts/AuthorContent.py. */
UCLASS(BlueprintType)
class SPACESURVIVAL_API USSPhase1Data : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Flight") float CruiseSpeed = 2400.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Flight") float MinimumSpeed = 1000.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Flight") float BoostMultiplier = 1.85f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Flight") float LateralSpeed = 1700.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Flight") float SteeringDegrees = 65.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Flight") float Response = 4.2f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Flight") float Acceleration = 3200.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Flight") float DodgeImpulse = 2500.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Camera") float ChaseDistance = 650.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Camera") float MouseSensitivity = 0.14f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Camera") float ControllerSensitivity = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Combat") float BaseWeaponDamage = 12.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Survival") float BaseHull = 100.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Survival") float BaseShield = 60.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Director") float WaveSecondsMin = 36.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Director") float WaveSecondsMax = 48.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Director") float WaveSecondsGrowth = 3.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Director") float MinimumReactionSeconds = 3.5f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Director") int32 MaximumActiveThreats = 24;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Director") float BaseBudgetPerSecond = 1.5f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Economy") int32 WaveCredits = 75;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Economy") int32 UpgradeBasePrice = 130;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Combat") float LaserInterval = 0.12f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Combat") float CannonInterval = 0.85f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Combat") float WeaponRange = 14000.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Combat") float SoftAimDegrees = 5.f;
};
