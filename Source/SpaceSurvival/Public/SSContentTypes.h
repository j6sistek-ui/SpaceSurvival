#pragma once

#include "CoreMinimal.h"
#include "SSContentTypes.generated.h"

/** The two locked contract types expose magnitudes only, never station cadence or extra slots. */
USTRUCT(BlueprintType)
struct FSSContractContentTuning
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Pressure", meta = (ClampMin = "0.1", ClampMax = "0.95"))
    double ShieldMultiplier = 0.65;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Pressure", meta = (ClampMin = "0", ClampMax = "1"))
    double PressureAddition = 0.15;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Pressure", meta = (ClampMin = "1", ClampMax = "100000000"))
    int32 PressureReward = 150;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hunter", meta = (ClampMin = "1", ClampMax = "1000"))
    int32 ObjectiveTarget = 6;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hunter", meta = (ClampMin = "1", ClampMax = "100000000"))
    int32 ObjectiveReward = 150;
};

UENUM(BlueprintType)
enum class ESSWorldKind : uint8
{
    SmallAsteroid,
    MediumAsteroid,
    MassiveAsteroid,
    Wreckage,
    ElectricalStorm,
    GravityAnomaly,
    Pursuer,
    Flanker,
    Projectile,
    Pickup,
    Event,
    Depot
};

UENUM(BlueprintType)
enum class ESSEncounterKind : uint8
{
    SalvageCache,
    DistressCombat,
    MobileDepot
};

UENUM(BlueprintType)
enum class ESSUtilityKind : uint8
{
    None = 0 UMETA(Hidden),
    VectorThrusters = 1,
    OverdriveCooling = 2
};

/** Fixed Phase 1 identities; only existing prices/effect magnitudes are content. */
USTRUCT(BlueprintType)
struct FSSUtilityDefinition
{
    GENERATED_BODY()
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    ESSUtilityKind Kind = ESSUtilityKind::VectorThrusters;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1", ClampMax = "100000000"))
    int32 Price = 150;
    UPROPERTY(EditAnywhere, BlueprintReadOnly,
              meta = (ClampMin = "1", ClampMax = "3", EditCondition = "Kind == ESSUtilityKind::VectorThrusters",
                      EditConditionHides))
    double ManeuverMultiplier = 1.0;
    UPROPERTY(EditAnywhere, BlueprintReadOnly,
              meta = (ClampMin = "1", ClampMax = "3", EditCondition = "Kind == ESSUtilityKind::VectorThrusters",
                      EditConditionHides))
    double ResponseMultiplier = 1.0;
    UPROPERTY(EditAnywhere, BlueprintReadOnly,
              meta = (ClampMin = "1", ClampMax = "3", EditCondition = "Kind == ESSUtilityKind::OverdriveCooling",
                      EditConditionHides))
    double BoostEfficiency = 1.0;
    UPROPERTY(EditAnywhere, BlueprintReadOnly,
              meta = (ClampMin = "1", ClampMax = "3", EditCondition = "Kind == ESSUtilityKind::OverdriveCooling",
                      EditConditionHides))
    double CoolingEfficiency = 1.0;
    FSSUtilityDefinition() : FSSUtilityDefinition(ESSUtilityKind::VectorThrusters) {}
    explicit FSSUtilityDefinition(ESSUtilityKind InKind) : Kind(InKind)
    {
        if (Kind == ESSUtilityKind::VectorThrusters)
        {
            ManeuverMultiplier = 1.30;
            ResponseMultiplier = 1.12;
        }
        else if (Kind == ESSUtilityKind::OverdriveCooling)
        {
            BoostEfficiency = 1.35;
            CoolingEfficiency = 1.45;
        }
    }
};

/** Old serialized rosters inherit role presets; an explicit override may deliberately be silent. */
USTRUCT(BlueprintType)
struct FSSAudioCueDefinition
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio")
    bool UseDefaultSound = true;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio",
              meta = (EditCondition = "!UseDefaultSound", EditConditionHides))
    TSoftObjectPtr<class USoundBase> Sound;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio", meta = (ClampMin = "0", ClampMax = "1"))
    float Gain = .35f;
};

/** One of the six existing presentations of the four Phase 1 hazard families. */
USTRUCT(BlueprintType)
struct FSSHazardDefinition
{
    GENERATED_BODY()
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    ESSWorldKind Kind = ESSWorldKind::SmallAsteroid;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FName MeshName = TEXT("SM_AsteroidSmall");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1", ClampMax = "10"))
    int32 MinimumWave = 1;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float SelectionWeight = .48f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.1"))
    float PressureCost = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "10"))
    float Radius = 95.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "10"))
    float ClimaxRadius = 95.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1"))
    float Health = 24.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    bool Destructible = true;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float DamageBase = 14.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float DamagePerWave = 3.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float DriftSpeedMin = 40.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float DriftSpeedMax = 350.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1"))
    float Lifetime = 65.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1"))
    float TelegraphSeconds = 3.5f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.2"))
    float PulseInterval = 1.8f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float GravityBase = 400.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float GravityPerWave = 45.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "1"))
    float FieldVelocityFraction = .3f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "1"))
    float ClimaxVelocityFraction = .65f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "1"))
    float DropChance = .3f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "3"))
    int32 FragmentCount = 0;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "10"))
    float FragmentRadius = 60.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float FragmentSpeed = 210.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "1"))
    float FragmentDamageFraction = .45f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1"))
    float FragmentLifetime = 13.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "10"))
    float BreakableChunkRadius = 290.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "10"))
    float DestructibleRadiusLimit = 320.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "600"))
    float PassageHalfSpacing = 1150.f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio")
    FSSAudioCueDefinition FieldLoopAudio;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio")
    FSSAudioCueDefinition DischargeAudio;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio")
    FSSAudioCueDefinition DestructionAudio;

    FSSHazardDefinition() = default;
    explicit FSSHazardDefinition(ESSWorldKind InKind) : Kind(InKind)
    {
        switch (Kind)
        {
        case ESSWorldKind::MediumAsteroid:
            MeshName = TEXT("SM_AsteroidMedium");
            Radius = 240.f;
            ClimaxRadius = Radius;
            Health = 90.f;
            SelectionWeight = .37f;
            DropChance = 1.f;
            FragmentCount = 3;
            break;
        case ESSWorldKind::MassiveAsteroid:
            MeshName = TEXT("SM_AsteroidMassive");
            Radius = 650.f;
            ClimaxRadius = Radius;
            Destructible = false;
            DamageBase = 28.f;
            DamagePerWave = 6.f;
            SelectionWeight = .15f;
            break;
        case ESSWorldKind::Wreckage:
            MeshName = TEXT("SM_Wreckage");
            Radius = 450.f;
            ClimaxRadius = Radius;
            Health = 65.f;
            MinimumWave = 2;
            PressureCost = 4.f;
            DamageBase = 20.f;
            DriftSpeedMin = 80.f;
            DriftSpeedMax = 80.f;
            SelectionWeight = .15f;
            break;
        case ESSWorldKind::ElectricalStorm:
            MeshName = TEXT("SM_StormRing");
            Radius = 3400.f;
            ClimaxRadius = Radius;
            MinimumWave = 4;
            Destructible = false;
            DamageBase = 6.f;
            DamagePerWave = .7f;
            PressureCost = 5.f;
            SelectionWeight = .55f;
            break;
        case ESSWorldKind::GravityAnomaly:
            MeshName = TEXT("SM_GravityRing");
            Radius = 3400.f;
            ClimaxRadius = 4300.f;
            MinimumWave = 6;
            Destructible = false;
            PressureCost = 5.f;
            SelectionWeight = .45f;
            break;
        default:
            break;
        }
    }
};

USTRUCT(BlueprintType)
struct FSSEnemyDefinition
{
    GENERATED_BODY()
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    ESSWorldKind Kind = ESSWorldKind::Pursuer;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FName MeshName = TEXT("SM_Pursuer");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1", ClampMax = "10"))
    int32 MinimumWave = 3;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float SelectionWeight = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.1"))
    float PressureCost = 3.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "10"))
    float Radius = 150.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1"))
    float Health = 55.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float CollisionDamageBase = 16.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float CollisionDamagePerWave = 2.5f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1"))
    float Lifetime = 75.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float ForwardOffset = 1700.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float LateralAmplitude = 420.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float VerticalAmplitude = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float OrbitRate = .65f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float OrbitRatePerWave = .055f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float Response = 1.2f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float ResponsePerWave = .1f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float CatchupSpeed = 2800.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float CatchupPerWave = 140.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.1"))
    float VelocityResponse = 2.5f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.3"))
    float ShotTelegraph = .9f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.2"))
    float InitialShotDelay = 2.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.2"))
    float ShotInterval = 3.6f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float ShotIntervalReductionPerWave = .13f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.2"))
    float MinimumShotInterval = 1.5f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float ProjectileSpeed = 5600.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float ProjectileSpeedPerWave = 170.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float ShotDamage = 8.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float ShotDamagePerWave = 1.4f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float AimLeadSeconds = .2f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float AimError = 200.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float AimErrorReductionPerWave = 12.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float MinimumAimError = 35.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float WeaponRange = 8000.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float AvoidanceDistance = 500.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float AvoidanceAcceleration = 1000.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float HazardDamagePerSecond = 70.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "1"))
    float CreditDropChance = .22f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float CreditDropAmount = 15.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio")
    FSSAudioCueDefinition ShotAudio;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio")
    FSSAudioCueDefinition DestructionAudio;
    FSSEnemyDefinition() = default;
    explicit FSSEnemyDefinition(ESSWorldKind InKind) : Kind(InKind)
    {
        if (Kind == ESSWorldKind::Flanker)
        {
            MeshName = TEXT("SM_Flanker");
            MinimumWave = 4;
            ForwardOffset = 2100.f;
            LateralAmplitude = 1900.f;
            VerticalAmplitude = 850.f;
        }
    }
};

USTRUCT(BlueprintType)
struct FSSPickupDefinition
{
    GENERATED_BODY()
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    int32 Kind = 0;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float DropWeight = .74f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float Amount = 25.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "10"))
    float Radius = 60.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float AttractionRadius = 450.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float AttractionSpeed = 800.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float CollectionPadding = 110.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1"))
    float Lifetime = 30.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FName MeshName = TEXT("SM_PickupCredit");
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FLinearColor Tint = FLinearColor(1.f, .75f, .1f);
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FString Label = TEXT("CREDITS");
    FSSPickupDefinition() = default;
    explicit FSSPickupDefinition(int32 InKind) : Kind(InKind)
    {
        if (Kind == 1)
        {
            DropWeight = .15f;
            Amount = 20.f;
            MeshName = TEXT("SM_PickupRepair");
            Tint = FLinearColor(.2f, 1.f, .4f);
            Label = TEXT("HULL REPAIR");
        }
        if (Kind == 2)
        {
            DropWeight = .05f;
            Amount = 20.f;
            MeshName = TEXT("SM_PickupShield");
            Tint = FLinearColor(.2f, .6f, 1.f);
            Label = TEXT("SHIELD CHARGE");
        }
        if (Kind == 3)
        {
            DropWeight = .06f;
            Amount = 12.f;
            MeshName = TEXT("SM_PickupBuff");
            Tint = FLinearColor(1.f, .35f, .9f);
            Label = TEXT("WEAPON OVERCHARGE");
        }
    }
};

USTRUCT(BlueprintType)
struct FSSEncounterDefinition
{
    GENERATED_BODY()
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    ESSEncounterKind Kind = ESSEncounterKind::SalvageCache;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1", ClampMax = "10"))
    int32 OfferedWave = 2;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0"))
    float OfferDelay = 7.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1"))
    float Lifetime = 80.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "100"))
    float InteractionRadius = 2100.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "10"))
    float BeaconRadius = 140.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "3"))
    float ObjectiveDuration = 26.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1", ClampMax = "3"))
    int32 ObjectiveCount = 3;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float OfferLeadDistance = 6500.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float OfferLeadSeconds = 3.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float OfferLateralOffset = 1100.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float ObjectiveLeadDistance = 8000.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float ObjectiveLeadSeconds = 3.5f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float CacheSpacing = 3600.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float CacheLateralOffset = 650.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float CacheCredits = 30.f;
    // -1 identifies legacy serialized rows with no completion amount; authoring fills by Kind.
    UPROPERTY(EditAnywhere, BlueprintReadOnly,
              meta = (ClampMin = "0", ClampMax = "100000000", EditCondition = "Kind != ESSEncounterKind::MobileDepot",
                      EditConditionHides))
    int32 CompletionCredits = -1;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float DebrisRadius = 300.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float DebrisHalfSpacing = 1100.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float DebrisDamageBase = 24.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float DebrisDamagePerWave = 2.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float EnemyCollisionDamage = 25.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.1", ClampMax = "1"))
    float DepotPriceFractionA = .75f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.1", ClampMax = "1"))
    float DepotPriceFractionB = .85f;
    FSSEncounterDefinition() = default;
    explicit FSSEncounterDefinition(ESSEncounterKind InKind) : Kind(InKind)
    {
        CompletionCredits = 70;
        if (Kind == ESSEncounterKind::DistressCombat)
        {
            OfferedWave = 7;
            OfferDelay = 10.f;
            ObjectiveDuration = 38.f;
            ObjectiveCount = 2;
            CompletionCredits = 100;
        }
        if (Kind == ESSEncounterKind::MobileDepot)
        {
            OfferedWave = 3;
            OfferDelay = 0.f;
            BeaconRadius = 420.f;
            CompletionCredits = 0;
        }
    }
};

USTRUCT(BlueprintType)
struct FSSDirectorContentTuning
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float EnemyChance = .20f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float ClimaxEnemyChance = .42f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float FieldChance = .11f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float WreckageSelectionStart = .69f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float SpawnIntervalMin = .65f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float SpawnIntervalMax = 1.2f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float BudgetCapacity = 10.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float BudgetBaseMultiplier = .65f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float BudgetGrowthPerWave = .13f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float PressureBase = .18f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float PressurePerWave = .065f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float ClimaxPressureBonus = .18f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    int32 EarlyEnemyCap = 2;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    int32 LateEnemyCap = 4;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    int32 ClimaxEnemyCap = 5;
};
