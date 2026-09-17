#pragma once

#include "CoreMinimal.h"
#include "SSContentTypes.generated.h"

class USkeletalMesh;
class USkeletalMeshComponent;

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
            MeshName = TEXT("SM_ElectricalFieldCandidateV3");
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
            MeshName = TEXT("SM_GravityFieldCandidateV3");
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
    FName MeshName = TEXT("SM_PursuerCandidateV1");
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
    float VerticalAmplitude = 520.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float LongitudinalAmplitude = 900.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0.05", ClampMax = "2"))
    float LongitudinalRateRatio = .43f;
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
            MeshName = TEXT("SM_FlankerCandidateV1");
            MinimumWave = 4;
            ForwardOffset = 2100.f;
            LateralAmplitude = 2400.f;
            VerticalAmplitude = 1250.f;
            LongitudinalAmplitude = 2300.f;
            LongitudinalRateRatio = .61f;
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

/** The two places a hero is worn. A hero that has no clip for a slot is not a candidate for it:
 *  the temporary trooper walks the deck but has never been seated, so the ship keeps the Acornaut. */
UENUM(BlueprintType)
enum class ESSHeroSlot : uint8
{
    Walker,
    Pilot
};

UENUM(BlueprintType)
enum class ESSHeroIdentity : uint8
{
    /** Licensed stand-in. Wins the walker slot while it is installed; fitted to a height, not to a scale. */
    Trooper,
    /** The hero whose mesh and clips are in this repository. Every measured constant below is its own. */
    Acornaut,
    /** Authored in Blender, not yet imported. Inert: selection skips it until its assets exist. */
    Squirrel
};

/** One hero, described rather than spelled out at the call sites. This carries everything the walking
 *  pawn and the seated pilot used to hold as literals: where the assets are, how the mesh meets the
 *  deck, how fast its walk clip was authored to travel, and the bone names the code asks for by hand.
 *  Selection walks the roster in order and skips a hero whose assets this build does not contain. */
USTRUCT(BlueprintType)
struct FSSHeroDefinition
{
    GENERATED_BODY()
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Identity")
    ESSHeroIdentity Identity = ESSHeroIdentity::Acornaut;
    /** Short stable name for logs and telemetry. Read by people, never parsed. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Identity")
    FName Id = TEXT("Acornaut");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Assets")
    FString MeshPath = TEXT("/Game/SpaceSurvival/Character/SK_AcornautTailV2.SK_AcornautTailV2");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Assets")
    FString WalkClipPath = TEXT("/Game/SpaceSurvival/Character/A_WalkLegRepair.A_WalkLegRepair");
    /** Empty when this hero has never been seated; the pilot slot then falls to the next hero that has. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Assets")
    FString PilotClipPath = TEXT("/Game/SpaceSurvival/Character/A_PilotGripFit.A_PilotGripFit");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Assets")
    FString DisembarkClipPath = TEXT("/Game/SpaceSurvival/Character/A_DisembarkLegRepair.A_DisembarkLegRepair");
    /** Centimetres from the mesh origin down to the sole at WalkHandoffSeconds, before scale.
     *  Measured, not guessed: the Acornaut's boot sole sits 62.90269494 cm below its mesh origin. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Fit")
    float SoleOffset = 62.90269494f;
    /** The rendered scale, used when FitHeight is zero. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Fit", meta = (ClampMin = "0.01"))
    float MeshScale = 1.5f;
    /** Non-zero replaces MeshScale and SoleOffset with what the imported bounds give: the scale that
     *  makes this mesh this many centimetres tall, and the sole those scaled bounds actually reach. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Fit", meta = (ClampMin = "0"))
    float FitHeight = 0.f;
    /** Mesh component yaw that turns the authored facing into the pawn's forward. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Fit")
    float MeshYaw = -90.f;
    /** Where the seated hero sits inside the hull. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Fit")
    FVector PilotMountOffset = FVector(-15, 0, 72);
    /** Multiplier on the walking pawn's readability rig for this hero. It belongs to the hero because
     *  albedo does: the lamp that models a pale suit leaves a black one the cut-out the owner
     *  complained about, and the lamp that opens a black one blows a pale one out.
     *
     *  Every hero's value is measured, not chosen, and the rule is the same for all three: one
     *  inverse-albedo step from the squirrel, the only hero that has actually been rendered with the
     *  rig, so that each suit takes the same amount of added light. scale = 2.5 x 0.046 / thisHerosReturn.
     *  That is what stops a rig sized for a black suit from arriving on a pale one at the same strength.
     *
     *  What goes in as "this hero's return" is the mean linear albedo of its base colour map over its
     *  used texels, with atlas padding dropped - except where the suit gives back more than its base
     *  colour says it should, which the trooper's glossy plates do, and then it is read off a render of
     *  that hero standing on the deck instead. Both numbers, and which one was used, are in each
     *  hero's own branch below.
     *
     *  This default is the Acornaut's own measured value, in the same way every other default in this
     *  struct spells out the Acornaut; the constructor's branches carry the other two. Its atlas,
     *  model-rigged.glb, averages 0.235 linear albedo over its used texels, five times the squirrel's,
     *  so it asks for a fifth of the squirrel's lamp. Unlike the squirrel's, this number has never been
     *  confirmed in a render: no capture of this hero on the deck exists, and its source also carries a
     *  0.4 base colour factor that would argue for more light if the import honours it. It is
     *  deliberately left at the low end of that uncertainty, because a hero that is under-lit is the
     *  hero nobody has complained about and a hero that is over-lit is a torch. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation", meta = (ClampMin = "0"))
    float ReadabilityLightScale = .5f;
    /** The pose the walk clip and the disembark clip share. The walk clip is frozen here so the
     *  standing hero and the hero that has just stepped off the ship are in the same pose. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Motion", meta = (ClampMin = "0"))
    float WalkHandoffSeconds = .308333333f;
    /** Ground speed in cm/s at which the walk clip plays at its authored rate, at the rendered scale.
     *  The Acornaut's 1.2 m/s stride at 1.5 scale is 180. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Motion", meta = (ClampMin = "1"))
    float WalkSpeed = 180.f;
    /** The names the code reaches for by hand. A hero that does not have one leaves it None, and
     *  ResolveBone reports the gap instead of quietly handing back the component transform.
     *
     *  These are spellings, not meanings, and the meanings do not line up across heroes. This hero's
     *  LeftFootBone is a toe and its ankle is L_Ankle; the trooper's foot_l is the ankle and its toe is
     *  ball_l; the squirrel's L_Foot is the ankle again. Anything that needs a particular joint rather
     *  than "the bone this hero calls its foot" has to say so, and cannot assume these agree. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bones")
    FName RootBone = TEXT("Pelvis");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bones")
    FName PelvisBone = TEXT("Pelvis");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bones")
    FName LeftFootBone = TEXT("L_Foot");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bones")
    FName RightFootBone = TEXT("R_Foot");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bones")
    FName LeftHandBone = TEXT("L_Wrist");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bones")
    FName RightHandBone = TEXT("R_Wrist");

    /** True when this build actually contains the mesh and the clip this slot plays. */
    bool Installed(ESSHeroSlot Slot) const;
    /** The scale this hero renders at once its mesh is loaded; FitHeight needs the imported bounds. */
    float RenderedScale(const USkeletalMesh *Mesh) const;
    /** Centimetres from the mesh origin down to the sole, already scaled. Double, because a fitted
     *  hero's bounds are, and the caller's arithmetic has always been carried at their width. */
    double ScaledSoleOffset(const USkeletalMesh *Mesh) const;
    /** GetSocketTransform answers an unknown name with the component transform and no complaint, so a
     *  hero missing a bone measures the wrong thing in silence. This returns false instead, still
     *  filling Out with that same component transform so a caller that records anyway is unchanged. */
    static bool ResolveBone(const USkeletalMeshComponent *Mesh, FName Bone, FTransform &Out);
    /** The hero the pawns are built with. A constructor cannot ask what content is installed and a
     *  class default must not depend on it, so both pawns start here and BeginPlay decides. It is
     *  also where selection lands when no hero in the roster is installed. */
    static FSSHeroDefinition Fallback()
    {
        return FSSHeroDefinition(ESSHeroIdentity::Acornaut);
    }

    FSSHeroDefinition() = default;
    explicit FSSHeroDefinition(ESSHeroIdentity InIdentity) : Identity(InIdentity)
    {
        if (Identity == ESSHeroIdentity::Trooper)
        {
            Id = TEXT("Trooper");
            MeshPath = TEXT("/Game/SciFITrooper_Man_03/SkeletalMesh/SK_SciFITrooper_Man_03.SK_SciFITrooper_Man_03");
            WalkClipPath = TEXT("/Game/SciFITrooper_Man_03/DemoContent/Anims/ThirdPersonWalk.ThirdPersonWalk");
            // Never seated: the ship keeps the Acornaut pilot while this stand-in walks the deck.
            PilotClipPath = FString();
            DisembarkClipPath =
                TEXT("/Game/SciFITrooper_Man_03/DemoContent/Anims/ThirdPersonJump_End.ThirdPersonJump_End");
            // Licensed body of unknown proportions: fitted to 180 cm from its own bounds, sole included.
            SoleOffset = 0.f;
            FitHeight = 180.f;
            // Measured twice, because this hero is the one the two methods disagree about. Its base
            // colour maps average 0.123 linear albedo over their used texels with the emissive ones
            // dropped, 2.7 times the squirrel's, which would ask for 0.94. But its armour is glossy
            // metal, and in the one capture of it standing on the deck its non-emissive plates return
            // 0.62 of the deck beside them against the squirrel's 0.12 - five times, not 2.7, because
            // specular carries what albedo does not. The render is what readability is about, so the
            // render wins: 2.5 / 5.07 = 0.49. Its gold is emissive and answers no lamp at all, so the
            // brightness it reads with today is not brightness this rig can add to.
            ReadabilityLightScale = .5f;
            // Its rig is the Unreal mannequin set, read out of SK_SciFITrooper_Man_03's reference
            // skeleton: lowercase, side-suffixed, and sharing not one spelling with the Acornaut's
            // except the pelvis. Naming them is what lets this hero be measured at all; the hand
            // bones in particular are what the soak used to record as the component while calling
            // them wrists. Its ankle is foot_l, as the mannequin means it, and its toe is ball_l.
            RootBone = TEXT("root");
            PelvisBone = TEXT("pelvis");
            LeftFootBone = TEXT("foot_l");
            RightFootBone = TEXT("foot_r");
            LeftHandBone = TEXT("hand_l");
            RightHandBone = TEXT("hand_r");
        }
        else if (Identity == ESSHeroIdentity::Squirrel)
        {
            Id = TEXT("Squirrel");
            // Licensed/ rather than Character/: this hero is derived from a purchased model, and
            // Content/SpaceSurvival/Licensed is the ignored tree every other licensed pack lives in,
            // where Content/SpaceSurvival/Character is tracked. Selection skips this entry until the
            // files exist on disk.
            MeshPath = TEXT("/Game/SpaceSurvival/Licensed/Hero/SK_SquirrelHero.SK_SquirrelHero");
            WalkClipPath = TEXT("/Game/SpaceSurvival/Licensed/Hero/A_SquirrelWalk.A_SquirrelWalk");
            PilotClipPath = TEXT("/Game/SpaceSurvival/Licensed/Hero/A_SquirrelPilot.A_SquirrelPilot");
            // No exit clip, deliberately: the ship has no door, so nobody climbs out of it yet
            // (RPT-20260917-01). A hero with no exit clip is simply standing outside when the
            // docking motion finishes.
            DisembarkClipPath = FString();
            // Measured on the imported base: it stands on Z = 0, so its sole is its origin.
            SoleOffset = 0.f;
            // And that is exactly why this hero cannot inherit the mount above it. The Acornaut's
            // FVector(-15, 0, 72) was measured for a body whose origin sits 62.90269494 cm above its
            // boots; this body's origin IS its boots, so the same number left it floating 44.067 cm
            // over the seat - a third of its own height, which is the float the owner reported.
            //
            // Measured against the cockpit geometry itself rather than adjusted by eye:
            // .agent/local/HeroSquirrel/Stage6_Clips/SeatFit.json, taken in SwiftCandidate.blend
            // (/Game/SpaceSurvival/Meshes/SM_SwiftCandidateV1) and confirmed identical in the Acorn
            // grip-fit cockpit, whose 24 seat, footwell, coaming and windscreen parts have
            // byte-identical world bounds and whose ship origin is the same (0, 0, 0). At this mount
            // the hips sit on the cushion and the boots hang into the footwell.
            //
            // Only the Swift ever shows it: ASSShip hides the pilot under the closed hulls, which in
            // this build are SM_PlayerHavolkStarter (the installed licensed starter) and anything
            // under ShipRefresh/, and FinishDocking() hides it outright. The Agile kind's
            // SM_SwiftCandidateV1 is the open cockpit this is for.
            PilotMountOffset = FVector(-12.5, 0, 27.933);
            // The darkest hero in the game, measured rather than guessed: the base colour map in
            // SquirrelHero_Base.glb averages 0.046 linear albedo over its used texels, about half of
            // fresh asphalt, with 73% of them under 0.05. At the rig's baseline it is still a
            // silhouette. 2.5 is deliberately short of the ~5x its albedo deficit alone would ask for,
            // because the suit is meant to read as dark worn leather and not to be repainted grey.
            //
            // This is the only one of the three scales that has been confirmed in a render, which is
            // why it is the anchor the other two are derived from rather than the other way round. At
            // 2.5 the suit sits at 0.75 of the deck beside it, up from 0.12, and nothing clips.
            ReadabilityLightScale = 2.5f;
            // 46 bones, root named Root, no fingers and no wrists; its hands are L_Hand and R_Hand,
            // its L_Foot is the ankle it sounds like. The stride is still the Acornaut's: the walk
            // clip has not been measured for travel yet, so 180 cm/s stands until it is.
            RootBone = TEXT("Root");
            LeftHandBone = TEXT("L_Hand");
            RightHandBone = TEXT("R_Hand");
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
