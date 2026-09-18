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

/** What moves a hull. Not a cosmetic distinction: a kinematic hull's position is written directly by a
 *  hand-integrated velocity at a fixed substep, so its trajectory is reproducible frame to frame to a
 *  fraction of a degree. A force-solver hull is pushed by ShipCore and integrated by Chaos, which is a
 *  different and less exactly reproducible thing. Tests that pin reproducibility have to ask which of the
 *  two they are looking at, rather than holding every ship to the numbers the first one happened to make. */
UENUM()
enum class ESSHullDrive : uint8
{
    Kinematic,
    ForceSolver
};

/** Which hull the ship flies. Ordered the way the roster is walked: the first one this build actually
 *  contains wins, so an uninstalled hull is skipped rather than being an error. */
UENUM(BlueprintType)
enum class ESSHullIdentity : uint8
{
    /** Whatever ASSShip::HullAssetPath resolves today - the Havolk starter, the Swift or the Acorn.
     *  A static mesh, roughly 4.8 m long, and the size every gameplay constant was calibrated against. */
    Classic,
    /** The Stellar Phoenix Shuttle. A skeletal mesh with a rear ramp, an interior and a cockpit, and
     *  the hull the owner has chosen. Inert until the pawn can carry a skeletal hull. */
    StellarPhoenix
};

/** One hull, described rather than spelled out. This exists for the same reason FSSHeroDefinition does:
 *  the ship's size, facing and mount points were constants measured from one particular mesh, and a
 *  different hull cannot be dropped into that.
 *
 *  It matters more here than it did for the hero, because of scale. Every gameplay distance in this game
 *  - hazard radii, the collection radius, spawn leads, the station's 1400 cm doorway - was calibrated
 *  against a 4.82 m hull. The Phoenix is 24.8 m, which is 5.2 times longer, and the owner raised that
 *  himself: "the ship is larger than the old one, so scale or something has to adjust to accommodate the
 *  gameplay element being the same." HullScale is where that adjustment lives, in one number, so it can
 *  be dialled rather than chased through six files. */
USTRUCT(BlueprintType)
struct FSSHullDefinition
{
    GENERATED_BODY()
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Identity")
    ESSHullIdentity Identity = ESSHullIdentity::Classic;
    /** Short stable name for logs. Read by people, never parsed. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Identity")
    FName Id = TEXT("Classic");
    /** Empty for Classic, which resolves its mesh through ASSShip::HullAssetPath because which of the
     *  three it gets depends on a command line flag and on what the build contains. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Assets")
    FString MeshPath;
    /** True when the mesh is skeletal. The pawn's hull component is a static mesh today, so this is the
     *  flag that says a hull cannot be flown yet rather than a quiet failure to load. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Assets")
    bool SkeletalHull = false;
    /** Gear down and rear ramp open. On the Phoenix these are one motion: measured, Cargo_Door_Bone
     *  swings 83.7 degrees in the same clip that drops Foot_Bone through 90.3. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Assets")
    FString LandingDeployClipPath;
    /** Gear up and rear ramp shut, which is the clip the launch sequence plays on thrust. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Assets")
    FString LandingStowClipPath;
    /** The measured length of the authored mesh along its own forward axis, in centimetres, before
     *  HullScale. Recorded so the scale arithmetic can be checked rather than believed. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Fit", meta = (ClampMin = "0"))
    float AuthoredLength = 482.5f;
    /** What the hull renders and collides at. One is the authored size. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Fit", meta = (ClampMin = "0.01"))
    float HullScale = 1.f;
    /** Mesh component yaw that turns the authored facing into the pawn's forward. The Phoenix is
     *  authored along +Y, so it needs -90; the current hulls are already along +X. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Fit")
    float MeshYaw = 0.f;
    /** The radius of the sphere that has to fit through the station corridor, before HullScale. This is
     *  the number ASSShip::FlightCollisionRadius has always answered with, and the reason it is here is
     *  that it stops being 105 the moment a different hull is installed. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Fit", meta = (ClampMin = "1"))
    float CollisionRadius = 105.f;
    /** How far the nose reaches past the hull's own origin, and how far the belly sits below it, both in
     *  authored centimetres before HullScale. These exist because "half the length" is not the same thing
     *  as "where the nose is" unless the pivot happens to be centred, and on the Phoenix it is not: measured
     *  in 5.8, the centre sits 141.16 cm aft of the pivot, so the nose reaches 1100.84 while the tail
     *  reaches 1383.16. Three separate passes wrote length/2 into a nose-relative formula before anybody
     *  asked the mesh. Zero means "not measured for this hull" and callers fall back to half the length. */
    float OriginToNose = 0.f;
    float OriginToBelly = 0.f;
    /** What moves this hull. Everything below that differs by DRIVE rather than by SIZE is keyed on this. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flight")
    ESSHullDrive Drive = ESSHullDrive::Kinematic;
    /** How this hull is framed. The chase boom is multiplied by ChaseScale, the eye is lifted by
     *  ChaseHeight, and the camera is pitched by ChasePitch. A 24.84 m ship cannot be framed by a 4.82 m
     *  ship's numbers - the owner's words were that the camera "will have to be dialed in for each ship
     *  individually" while the concept stays fixed - so the concept lives in ASSShip and the numbers live
     *  here. Zero height and zero pitch mean "leave the constructor's framing alone", which is the classic
     *  hull and every build that has ever shipped. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Camera", meta = (ClampMin = "0.01"))
    float ChaseScale = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Camera")
    float ChaseHeight = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Camera")
    float ChasePitch = 0.f;
    /** How far above a landing pad's deck this hull's ORIGIN sits when parked. It is the distance from the
     *  origin to the belly plus whatever the gear needs under it, so it is a property of the hull and not
     *  of the pad. 230 is the classic hull's, whose origin is near its middle. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Fit", meta = (ClampMin = "0"))
    float DockClearanceAboveDeck = 230.f;
    /** Whether USSShipPresentation's six fitted upgrade modules apply to this hull. That component reads
     *  the static mesh's bounding box and gates on the literal name SM_PlayerHavolkStarter, so it fits one
     *  hull and only that one; a skeletal hull carries its own exhausts on its own bones instead. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation")
    bool UsesModulePresentation = true;
    /** How closely this hull's trajectory has to agree with itself across frame rates: centimetres of
     *  position, centimetres per second of velocity, degrees of heading, measured against a 120 Hz run of
     *  the same scripted flight.
     *
     *  These are per hull because the rule is per hull, not because the bar is being lowered. The position
     *  figure was always a share of the ship - the original comment derived 25 cm as "under one eighth of
     *  the collision diameter" - and on that same share the Phoenix is actually TIGHTER than the classic
     *  hull: 108 cm measured on a 2484 cm hull is 4.3 percent of its length, against 25 on 482.5 which is
     *  5.2 percent. Velocity and heading are the ones that genuinely differ, and they differ by DRIVE:
     *  Chaos re-converges on a target speed slightly differently at 30 Hz than at 120, where a fixed
     *  substep integrator does not. Every figure here is measured from a real run, never chosen to make a
     *  test pass; the measurements are in the ShipCoreFrameRateTolerances comment and in KNOWN_ISSUES. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flight", meta = (ClampMin = "0"))
    float FrameRatePositionCm = 25.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flight", meta = (ClampMin = "0"))
    float FrameRateVelocityCmS = 15.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flight", meta = (ClampMin = "0"))
    float FrameRateHeadingDeg = .05f;

    /** The length this hull actually flies at, which is what any gameplay comparison wants. */
    float ScaledLength() const
    {
        return AuthoredLength * HullScale;
    }
    /** The collision radius this hull actually flies at. */
    /** Nose reach in world centimetres. Falls back to half the length for a hull nobody has measured,
     *  which is the old assumption - kept as a fallback rather than as the answer, so an unmeasured hull
     *  behaves as before instead of reading zero and admitting docking from inside the station. */
    float ScaledOriginToNose() const
    {
        return (OriginToNose > 0.f ? OriginToNose : AuthoredLength * .5f) * HullScale;
    }
    float ScaledCollisionRadius() const
    {
        return CollisionRadius * HullScale;
    }
    /** How many times longer this hull is than the one every gameplay distance was calibrated against.
     *  One means no reconciliation is needed; the Phoenix at full size is 5.15. */
    float LengthRatioToClassic() const
    {
        return ScaledLength() / 482.5f;
    }
    /** Whether this build holds the mesh. Classic is always installed: it resolves through
     *  HullAssetPath and the game has always shipped one of those three. Defined in SSContentTypes.cpp
     *  because it borrows the hero slot's package check rather than duplicating it, and that struct is
     *  declared below this one. */
    /** Whether this hull has declared everything its own drive and shape require. The owner's rule: a gate
     *  "has to confirm values exist for that model, not force that model to fit another model's rules". So
     *  a hull that leaves a required value at zero fails loudly here rather than silently inheriting the
     *  number some other ship happened to measure. Returns false and fills Why with the first thing
     *  missing. */
    bool Validate(FString &Why) const
    {
        if (AuthoredLength <= 0.f)
            return Why = TEXT("AuthoredLength is unset; nothing can be derived from a hull of no length"), false;
        if (CollisionRadius <= 0.f)
            return Why = TEXT("CollisionRadius is unset"), false;
        if (FrameRatePositionCm <= 0.f || FrameRateVelocityCmS <= 0.f || FrameRateHeadingDeg <= 0.f)
            return Why = TEXT("frame-rate agreement tolerances are unset; measure them, do not inherit them"), false;
        if (DockClearanceAboveDeck <= 0.f)
            return Why = TEXT("DockClearanceAboveDeck is unset; a hull has to say how high it parks"), false;
        if (ChaseScale <= 0.f)
            return Why = TEXT("ChaseScale is unset; a hull has to say how it is framed"), false;
        // A skeletal hull is the only kind that can carry its own animated gear, and the only kind the
        // module presentation cannot fit. Catching the combination here is cheaper than finding a ship
        // wearing another ship's nacelle casings.
        if (SkeletalHull && UsesModulePresentation)
            return Why = TEXT("a skeletal hull cannot wear the static hull's fitted modules"), false;
        if (Identity != ESSHullIdentity::Classic && OriginToNose <= 0.f)
            return Why = TEXT("OriginToNose is unmeasured; half the length is an assumption, not a nose"), false;
        return true;
    }
    bool Installed() const;

    FSSHullDefinition() = default;
    explicit FSSHullDefinition(ESSHullIdentity InIdentity) : Identity(InIdentity)
    {
        if (Identity == ESSHullIdentity::StellarPhoenix)
        {
            Id = TEXT("StellarPhoenix");
            MeshPath = TEXT("/Game/Stellar_Phoenix/Spaceship/Meshes/Stellar_Phoenix.Stellar_Phoenix");
            SkeletalHull = true;
            LandingDeployClipPath = TEXT("/Game/Stellar_Phoenix/Spaceship/Animation/Landing_On.Landing_On");
            LandingStowClipPath = TEXT("/Game/Stellar_Phoenix/Spaceship/Animation/Landing_Off.Landing_Off");
            // Measured in 5.8 by loading it: bounds 1243.9 x 2484.0 x 704.8, standing on Z = 0. The long
            // axis is Y, not X - the airbrake mesh spans X and the left engine sits at X +589.85 - which
            // is also why MeshYaw is -90 rather than 0.
            AuthoredLength = 2484.f;
            MeshYaw = -90.f;
            // Half the widest horizontal extent, 1243.9 / 2. A sphere is a poor fit for a hull this shape
            // and that is a known problem rather than an oversight: most of a 24.8 x 12.4 m ship would sit
            // outside a sphere sized to its width, or inside one sized to its length. Recorded here so the
            // number is at least derived from the mesh instead of inherited from a different ship.
            CollisionRadius = 621.95f;
            // Measured from the loaded mesh, not inferred: half-extents 621.94 x 1242.0 x 352.4 with the box
            // centre offset (-1.98, -141.16, 352.65) from the pivot. So the nose is at +1100.84 along the
            // authored forward, and the belly sits 0.25 cm under the origin - the hull stands on its own pivot,
            // which is why parking it at the classic hull's 220 cm leaves it hanging above the pad.
            OriginToNose = 1100.84f;
            OriginToBelly = 0.25f;
            Drive = ESSHullDrive::ForceSolver;
            // Found by flying it and looking, not derived: the full 5.15 length ratio put the camera inside an
            // asteroid, the square root filled the middle of the screen, and 4.5 with the eye high and the tilt
            // shallow is where the hull reads AND the crosshair still covers a target.
            ChaseScale = 4.5f;
            ChaseHeight = 3000.f;
            ChasePitch = -16.f;
            // Its own exhausts ride its own nozzle bones; the fitted-module presentation is measured against a
            // different mesh entirely and would hang casings in mid air.
            UsesModulePresentation = false;
            // PROVISIONAL, and the one number here that is not measured. OriginToBelly is 0.25 - this hull
            // stands on its own pivot - so the belly wants to sit at the deck plus whatever the landing gear
            // holds it up by, and that extension has never been measured. Parking at the classic hull's 230
            // leaves it hanging; this is a deliberate under-correction until the gear is measured rather than
            // a guess dressed as a figure.
            DockClearanceAboveDeck = 230.f;
            // Measured at 30, 60 and 144 Hz against a 120 Hz reference of the same scripted flight. Worst
            // observed: 108.0 cm, 71.9 cm/s, 0.574 degrees of yaw - all three at 30 Hz, all three shrinking
            // as the rate rises (60 Hz: 33.9, 23.2, 0.178; 144 Hz: 23.6, 28.9, 0.104). Declared at roughly
            // 1.5x the worst: wide enough not to flap, narrow enough that a real regression still trips it.
            //
            // Worth seeing what these say. On POSITION the Phoenix is proportionally TIGHTER than the hull
            // it replaces - 108 cm on a 2484 cm ship is 4.3 percent of its length, against the classic
            // hull's 25 on 482.5, which is 5.2 percent. The looser figure is not a worse ship; it is a
            // bigger one measured by the same rule. Velocity and heading are where the drive differs.
            FrameRatePositionCm = 165.f;
            FrameRateVelocityCmS = 110.f;
            FrameRateHeadingDeg = .9f;
            // Deliberately 1: the owner said not to change a value unless it is certainly wrong, and the
            // authored size is not wrong - it is what makes a walkable interior possible for a 1.35 m
            // hero. The reconciliation the owner asked for belongs in the gameplay distances or in this
            // one number once it has been flown, not in a guess made before anything has flown.
            HullScale = 1.f;
        }
    }
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
    /** What this hero stands in. Empty means it has none, and then standing is exactly what it has
     *  always been: the walk clip frozen at WalkHandoffSeconds with the stride stopped dead. That is
     *  the pose the player sees more than any other, and it is one frame of a walk, which is the
     *  weakest thing about a hero that has nothing else. Two of the three heroes here still have no
     *  idle and are unchanged by every line that reads this. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Assets")
    FString IdleClipPath;
    /** Played once each, in turn, when the hero has stood still for IdleFidgetSeconds, then back to
     *  the idle. Ignored entirely when IdleClipPath is empty: a clip with nothing to return to is not
     *  a fidget. These are not decoration - see IdleFidgetSeconds for what they are actually for. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Assets")
    TArray<FString> IdleFidgetClipPaths;
    /** The faster gaits, above the walk. Empty means this hero has one gait and the walk covers every
     *  speed it ever reaches, which is how all three heroes behaved until the squirrel got these and
     *  is still exactly how the other two behave. Each is paired with the speed it was authored to
     *  travel at - see JogSpeed - and a clip without a credible measured speed does not belong here,
     *  because the speed is what the rate is divided by. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Assets")
    FString JogClipPath;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Assets")
    FString RunClipPath;
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
    /** What JogClipPath and RunClipPath were authored to travel at, in the same units as WalkSpeed:
     *  ground cm/s at the rendered scale, at rate 1. Measured off the clip the same way the walk's
     *  180 was - the planted foot's own travel while it is on the deck - because that measurement is
     *  the whole point of carrying the number. The rate a gait plays at is pawnSpeed/thisSpeed, so a
     *  wrong value here is a foot that skates by exactly the error. Ignored when the path is empty. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Motion", meta = (ClampMin = "1"))
    float JogSpeed = 180.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Motion", meta = (ClampMin = "1"))
    float RunSpeed = 180.f;
    /** Seconds of standing still before a fidget is cut in. Zero means never, which is every hero
     *  that has no idle and any hero whose idle should simply loop.
     *
     *  This is not polish. The retargeted stand clips carry no tail motion at all - the body they
     *  were captured on has no tail - so in the idle alone the squirrel's tail is a motionless
     *  vertical slab, and the camera the player actually uses is the one behind it. The fidgets fix
     *  that without anybody authoring a tail: their pelvis rotation alone swings the rigid tail tip
     *  through a 48 cm arc (Tail_05 X from -23.35 to +24.71 cm, measured), which is what reads as a
     *  bushy squirrel tail. So the fidget timer is what makes the idle worth standing in. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Motion", meta = (ClampMin = "0"))
    float IdleFidgetSeconds = 0.f;
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

    /** Whether this build actually holds the package behind an object path. An empty path is not a
     *  missing file, it is a hero saying it has none of that thing, and both answer false. Anything
     *  optional has to ask this before loading: LoadObject logs a warning for a path that is not
     *  there, and a hero declaring an idle the licensed pack would have carried is the ordinary state
     *  of a build without that pack, not a fault worth a line in the log. */
    static bool AssetInstalled(const FString &ObjectPath);
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
            // Licensed/ rather than Character/ is WRONG for most of what is under it, and is a known
            // open decision rather than a considered choice. An earlier version of this comment claimed
            // the hero "is derived from a purchased model"; that was an assumption, and the owner has
            // since stated plainly that the model is their own - generated in Tripo, whose bridge output
            // still sits in the ignored Content/TripoModels. Only the five retargeted clips below are
            // licence-restricted, and those verifiably are: each one still carries MoCap Online's own
            // master path and source MD5 inside the asset. So the mesh, skeleton, physics asset,
            // material, textures, walk and pilot clip are first-party work sitting in an ignored tree
            // named for somebody else's content, with no history and no backup, and the five clips
            // beside them are the only things that actually have to stay out of git.
            //
            // Splitting them is blocked on one question only: this repository is public, so tracking
            // the art publishes it, and whether that is allowed depends on the owner's Tripo plan.
            // Until that is answered nothing moves, because git history cannot be taken back.
            // Selection skips this entry until the files exist on disk.
            MeshPath = TEXT("/Game/SpaceSurvival/Licensed/Hero/SK_SquirrelHero.SK_SquirrelHero");
            WalkClipPath = TEXT("/Game/SpaceSurvival/Licensed/Hero/A_SquirrelWalk.A_SquirrelWalk");
            PilotClipPath = TEXT("/Game/SpaceSurvival/Licensed/Hero/A_SquirrelPilot.A_SquirrelPilot");
            // No exit clip, deliberately: the ship has no door, so nobody climbs out of it yet
            // (RPT-20260917-01). A hero with no exit clip is simply standing outside when the
            // docking motion finishes.
            DisembarkClipPath = FString();
            // Retargeted from MoCap Online's MCO_Mocap_Basics onto this hero's own skeleton, through
            // the IK retargeter Scripts/AuthorHeroMocapRetarget.py rebuilds from scratch.
            //
            // GROUNDING, measured with a real footprint - eight markers per foot laid on the sole
            // plane of the reference pose - and not with the toe bone, which sits 2.2 cm above the
            // sole and would flatter every one of these. Figures are cm at this hero's unscaled
            // 89.8 cm size; multiply by MeshScale for the deck. The owner's own A_SquirrelWalk
            // measures -0.46/+14.02 by the same method and is the standard the rest are held to.
            //   idle      +0.16 / +0.60, i.e. its lowest sole point is ABOVE the deck all the way
            //             through - the only clip here of which that is true
            //   fidget A  -0.03 / +0.85     fidget B  -0.16 / +3.54
            //   jog       -1.30 / +30.62    run       -1.66 / +32.27
            // Against DeckClearance 2.75 the deepest of them, the run, is 2.49 cm at MeshScale 1.5,
            // so no sole reaches the collision floor under the plates.
            //
            // SKATE, and what is honestly wrong with the fidgets. The measure is contact-patch path:
            // per frame, the smallest horizontal movement among the sole markers that are touching,
            // summed, so a pivot or a roll scores zero and only a sliding flat foot scores. It is
            // reported instead of net displacement, which is ~0 for any clip that returns to its own
            // start pose and would call every one of these perfect.
            //   idle      0.76 / 0.71 cm over 6.1 s, and the toe never leaves a 0.17 cm circle. Still.
            //   fidget A  7.73 / 10.84 cm, toe wandering 2.71 cm from its spot - 4.07 cm on the deck.
            //   fidget B  7.73 / 7.84 cm; its left foot also takes a real 3.46 cm step, which is in
            //             the capture (the mannequin's own foot travels 54.4 cm there) and not
            //             invented by the retarget.
            // Fidget A's wander is invented: the source's feet move 1.41 cm, which at this body's
            // 0.3935 height ratio should be 0.55. That is the known cost of these two clips and it is
            // written here rather than smoothed over. It survives because 4 cm of drift across five
            // seconds is slower than the eye tracks and because of what the fidget is FOR - see
            // IdleFidgetSeconds. What did not survive is the claim that nothing here skates.
            //
            // One clearance to trip over if this mesh is ever re-exported: in the idle the glove
            // passes the lower torso with 0.22 cm to spare at frame 2, which is 3.3 mm on the deck.
            // Nothing intersects in any clip here, and the arms are as tucked as this suit allows,
            // but a LOD swap, a fur pass or a re-export of SquirrelSuit has 2.2 mm to play with -
            // and it is the idle, the pose held longest, that would show it first.
            IdleClipPath = TEXT("/Game/SpaceSurvival/Licensed/Hero/A_SquirrelIdle.A_SquirrelIdle");
            IdleFidgetClipPaths = {TEXT("/Game/SpaceSurvival/Licensed/Hero/A_SquirrelFidgetA.A_SquirrelFidgetA"),
                                   TEXT("/Game/SpaceSurvival/Licensed/Hero/A_SquirrelFidgetB.A_SquirrelFidgetB")};
            // The two fast gaits, and the speeds they were measured to travel at. Both are grounded
            // above; both keep the same zero-skate property the walk has, because the rate they play
            // at is the pawn's speed divided by the number beside them.
            JogClipPath = TEXT("/Game/SpaceSurvival/Licensed/Hero/A_SquirrelJog.A_SquirrelJog");
            RunClipPath = TEXT("/Game/SpaceSurvival/Licensed/Hero/A_SquirrelRun.A_SquirrelRun");
            JogSpeed = 205.5f;
            RunSpeed = 384.3f;
            // Three of the eight retargeted clips are not listed anywhere and are not even beside
            // this hero: AuthorHeroMocapRetarget.py writes A_SquirrelRunStop, A_SquirrelCrouchIdle
            // and A_SquirrelWalkMocapCompare into Licensed/MocapSource, which DefaultGame.ini names
            // under DirectoriesToNeverCook. The stop clip ends on a pose nothing returns from and its
            // sole reaches -2.20; the crouch folds a character that is mostly helmet and backpack
            // into a pile; the MoCap walk exists only to be looked at beside the owner's, which stays.
            //
            // Two full idle loops. The length matters and is not a taste: measured across all 46
            // bones, the fidgets' first pose is the idle's first pose to 0.004 cm and 0.009 degrees,
            // and the idle's own loop seam is 0.005 cm and 0.012 degrees, so a cut on a boundary lands
            // on matching poses and costs nothing even before the blend below smooths it. Any
            // multiple of 6.133333 s lands there; one loop fidgets too often to read as idle.
            IdleFidgetSeconds = 12.266666f;
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
            // its L_Foot is the ankle it sounds like.
            //
            // WalkSpeed stays at the inherited 180 and that is now a measurement rather than a
            // placeholder. Its planted foot travels 119.3 cm/s unscaled, which is 178.9 at this
            // hero's 1.5 scale; the author measured the same thing in Blender at 120.23 cm/s and
            // wrote the target down as "speed/180 at mesh scale 1.5 -> 1.2 m/s unscaled". Three
            // independent measurements inside 0.8% of each other. An earlier reading of 80.8 cm/s
            // claimed the walk skates at 180; it does not, and acting on that figure would have
            // recalibrated the one constant this clip was authored against.
            //
            // JogSpeed and RunSpeed are read off their clips the same way, on the same run.
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
