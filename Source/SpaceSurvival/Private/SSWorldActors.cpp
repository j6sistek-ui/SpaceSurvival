#include "SSWorldActors.h"
#include "SSAsteroidBurst.h"
#include "SSVFXPresentation.h"
#include "SSWave10Soak.h"
#include "SSAudio.h"
#include "Components/AudioComponent.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSShip.h"
#include "SSPhase1Data.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/StaticMesh.h"
#include "Misc/PackageName.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace
{
// Was a literal 120 while the pawn's own sphere is 105, so hazard contact was judged against a ship 15 cm
// wider than the one every docking sweep used. Read it off the ship instead.
//
// A function and not a constant: a namespace-scope initialiser runs during static initialisation, before
// the engine has built any class default object, so asking the ship how big it is there dereferences null
// and takes the process down before a single test runs. Asked at the call site, it is answered by a CDO
// that exists.
float ShipRadius()
{
    return ASSShip::FlightCollisionRadius();
}

ASSGameMode *GameMode(const UObject *Context)
{
    return Cast<ASSGameMode>(UGameplayStatics::GetGameMode(Context));
}

const USSPhase1Data *Content(const UObject *Context)
{
    if (const ASSGameMode *Mode = GameMode(Context))
        if (Mode->Tuning)
            return Mode->Tuning;
    return GetDefault<USSPhase1Data>();
}

UStaticMesh *Mesh(const TCHAR *Name, const TCHAR *Fallback = TEXT("/Engine/BasicShapes/Sphere.Sphere"))
{
    const FString Path = FString::Printf(TEXT("/Game/SpaceSurvival/Meshes/%s.%s"), Name, Name);
    if (UStaticMesh *Authored = LoadObject<UStaticMesh>(nullptr, *Path))
        return Authored;
    return LoadObject<UStaticMesh>(nullptr, Fallback);
}

FLinearColor BodyColor(ESSWorldKind Kind)
{
    switch (Kind)
    {
    case ESSWorldKind::ElectricalStorm:
        return FLinearColor(.24f, .55f, 1.f);
    case ESSWorldKind::GravityAnomaly:
        return FLinearColor(.6f, .18f, 1.f);
    case ESSWorldKind::Pursuer:
        return FLinearColor(1.f, .16f, .08f);
    case ESSWorldKind::Flanker:
        return FLinearColor(1.f, .52f, .08f);
    case ESSWorldKind::Wreckage:
        return FLinearColor(.22f, .36f, .43f);
    case ESSWorldKind::Depot:
        return FLinearColor(.15f, 1.f, .55f);
    case ESSWorldKind::Event:
        return FLinearColor(.3f, .85f, 1.f);
    default:
        return FLinearColor(.35f, .26f, .2f);
    }
}

void Announce(const UObject *Context, const FString &Text)
{
    if (ASSGameMode *Mode = GameMode(Context))
        Mode->Announce(Text);
}

bool HasThreatCapacity(const UObject *Context, int32 Additional = 1)
{
    ASSGameMode *Mode = GameMode(Context);
    return !Mode || !Mode->Director ||
           Mode->Director->GetActiveThreatCount() + Additional <= Mode->Director->MaximumActiveThreats;
}

// Shared admission rule for point spawns and an event's traversable approach.
// Weather may overlap solids; distinct environmental envelopes remain separated.
bool HasSpatialClearance(const UObject *Context, FVector Start, FVector End, float Radius, bool bField = false)
{
    for (TActorIterator<ASSWorldBody> It(Context->GetWorld()); It; ++It)
    {
        if (It->IsActorBeingDestroyed() || (!It->IsSolidHazard() && !It->IsEnemy() && !It->IsEnvironmentalField()))
            continue;
        if (bField && It->IsEnvironmentalField())
        {
            if (FVector::DistSquared(End, It->GetActorLocation()) <
                FMath::Square(Radius + It->GetBodyRadius() + 1800.f))
                return false;
            continue;
        }
        if (bField || It->IsEnvironmentalField())
            continue;
        if (FMath::PointDistToSegment(It->GetActorLocation(), Start, End) < Radius + It->GetBodyRadius() + 420.f)
            return false;
    }
    return true;
}

bool SelectContent(const UObject *Context, const TArray<ESSWorldKind> &Candidates, int32 Wave, FRandomStream &Random,
                   bool bEnemy, ESSWorldKind &Selected)
{
    float Total = 0.f;
    const auto *Data = Content(Context);
    for (ESSWorldKind Kind : Candidates)
    {
        const int32 MinimumWave = bEnemy ? Data->Enemy(Kind).MinimumWave : Data->Hazard(Kind).MinimumWave;
        if (Wave >= MinimumWave)
            Total += FMath::Max(0.f, bEnemy ? Data->Enemy(Kind).SelectionWeight : Data->Hazard(Kind).SelectionWeight);
    }
    if (Total <= 0.f)
        return false;
    float Draw = Random.FRand() * Total;
    for (ESSWorldKind Kind : Candidates)
    {
        const int32 MinimumWave = bEnemy ? Data->Enemy(Kind).MinimumWave : Data->Hazard(Kind).MinimumWave;
        const float Weight =
            FMath::Max(0.f, bEnemy ? Data->Enemy(Kind).SelectionWeight : Data->Hazard(Kind).SelectionWeight);
        if (Wave < MinimumWave || Weight <= 0.f)
            continue;
        Selected = Kind;
        Draw -= Weight;
        if (Draw <= 0.f)
            return true;
    }
    return true;
}
} // namespace

ASSWorldBody::ASSWorldBody()
{
    PrimaryActorTick.bCanEverTick = true;
    Collision = CreateDefaultSubobject<USphereComponent>(TEXT("ThreatVolume"));
    SetRootComponent(Collision);
    Collision->InitSphereRadius(BodyRadius);
    Collision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Collision->SetCollisionObjectType(ECC_WorldDynamic);
    Collision->SetCollisionResponseToAllChannels(ECR_Ignore);
    Collision->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Collision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Presentation"));
    Visual->SetupAttachment(Collision);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ThreatIndicator = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ThreatIndicator"));
    ThreatIndicator->SetupAttachment(Collision);
    ThreatIndicator->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ThreatIndicator->SetVisibility(false);
}

void ASSWorldBody::BeginPlay()
{
    Super::BeginPlay();
    LocalRandom.Initialize(GetUniqueID() ^ 0x51A7);
    UpdateVisual();
}

void ASSWorldBody::Configure(ESSWorldKind InKind, float InRadius, float InDamage, int32 InWave)
{
    Kind = InKind;
    BodyRadius = FMath::Max(10.f, InRadius);
    CollisionDamage = FMath::Max(0.f, InDamage);
    Wave = FMath::Clamp(InWave, 1, 10);
    Age = 0.f;
    const auto Hazard = Content(this)->Hazard(Kind);
    const auto Enemy = Content(this)->Enemy(Kind);
    Health = FMath::Max(1.f, IsEnemy() ? Enemy.Health : Hazard.Health);
    LifetimeSeconds = IsEnemy() ? Enemy.Lifetime : Hazard.Lifetime;
    TelegraphSeconds = FMath::Max(1.f, FMath::IsFinite(Hazard.TelegraphSeconds) ? Hazard.TelegraphSeconds : 3.5f);
    FieldPulseInterval = FMath::Max(.2, FMath::IsFinite(Hazard.PulseInterval) ? double(Hazard.PulseInterval) : 1.8);
    FieldPulseRemaining = -1.0;
    bFieldHasDischarged = false;
    bWarningIssued = false;
    GravityAcceleration = FMath::Max(0.f, Hazard.GravityBase + Wave * Hazard.GravityPerWave);
    bPersistentAcrossWaves = IsEnvironmentalField();
    Collision->SetSphereRadius(BodyRadius);
    Collision->SetCollisionResponseToChannel(ECC_Visibility, IsEnvironmentalField() ? ECR_Ignore : ECR_Block);
    UpdateVisual();
    // This one photographic family uses local triplanar coordinates, so mesh UV
    // density cannot select its mips. Pin the shared three maps only for the
    // bounded lifetime of newly admitted rocks; never disable streaming globally.
    const bool bPhotographicAsteroid = (Kind == ESSWorldKind::SmallAsteroid || Kind == ESSWorldKind::MediumAsteroid ||
                                        Kind == ESSWorldKind::MassiveAsteroid) &&
                                       Visual->GetMaterial(0) &&
                                       Visual->GetMaterial(0)->GetPathName() ==
                                           TEXT("/Game/SpaceSurvival/Materials/M_RockPhotographic.M_RockPhotographic");
    if (bPhotographicAsteroid)
    {
        const float ResidencySeconds =
            FMath::IsFinite(LifetimeSeconds) ? FMath::Clamp(LifetimeSeconds + 5.f, 5.f, 120.f) : 35.f;
        Visual->PrestreamTextures(ResidencySeconds, false);
    }
    // Runtime-spawned bodies BeginPlay before the Director applies their kind
    // and radius. Attach the electrical presentation only after those values
    // are authoritative, otherwise every storm silently keeps the small-rock
    // default and never receives its owned Nerves beam.
    // The request is refused beyond the presentation cull, and a storm can be admitted beyond it, so
    // Tick asks again until it is granted.
    if (Kind == ESSWorldKind::ElectricalStorm)
        if (auto *FX = GetWorld()->GetSubsystem<USSCombatVFXSubsystem>())
            bFieldPresentationAttached = FX->AttachElectricalField(this, BodyRadius);
    ConfigureAudio();
}

void ASSWorldBody::UpdateVisual()
{
    const TCHAR *Asset = TEXT("SM_AsteroidSmall");
    switch (Kind)
    {
    case ESSWorldKind::MediumAsteroid:
        Asset = TEXT("SM_AsteroidMedium");
        break;
    case ESSWorldKind::MassiveAsteroid:
        Asset = TEXT("SM_AsteroidMassive");
        break;
    case ESSWorldKind::Wreckage:
        Asset = TEXT("SM_Wreckage");
        break;
    case ESSWorldKind::ElectricalStorm:
        Asset = TEXT("SM_ElectricalFieldCandidateV3");
        break;
    case ESSWorldKind::GravityAnomaly:
        Asset = TEXT("SM_GravityFieldCandidateV3");
        break;
    case ESSWorldKind::Pursuer:
        Asset = TEXT("SM_PursuerCandidateV1");
        break;
    case ESSWorldKind::Flanker:
        Asset = TEXT("SM_FlankerCandidateV1");
        break;
    case ESSWorldKind::Depot:
        Asset = TEXT("SM_MobileDepot");
        break;
    case ESSWorldKind::Event:
        Asset = TEXT("SM_EventBeacon");
        break;
    case ESSWorldKind::Projectile:
        Asset = TEXT("SM_Projectile");
        break;
    case ESSWorldKind::Pickup:
        Asset = TEXT("SM_PickupCredit");
        break;
    default:
        break;
    }
    FString CatalogMesh = Asset;
    if (IsSolidHazard() || IsEnvironmentalField())
        CatalogMesh = Content(this)->Hazard(Kind).MeshName.ToString();
    else if (IsEnemy())
        CatalogMesh = Content(this)->Enemy(Kind).MeshName.ToString();
    UStaticMesh *SelectedMesh = nullptr;
    const bool bRock = Kind == ESSWorldKind::SmallAsteroid || Kind == ESSWorldKind::MediumAsteroid ||
                       Kind == ESSWorldKind::MassiveAsteroid;
    if (bRock)
    {
        const TCHAR *RockNames[] = {TEXT("SM_Asteroid_Barren_1"), TEXT("SM_Asteroid_Barren_2"),
                                    TEXT("SM_Asteroid_Barren_3"), TEXT("SM_AsteroidBarren_4")};
        const FString RockPackage =
            FString::Printf(TEXT("/Game/Asteroid_Library/Static_Meshes/%s"), RockNames[GetUniqueID() % 4]);
        if (FPackageName::DoesPackageExist(RockPackage))
            SelectedMesh = LoadObject<UStaticMesh>(nullptr, *RockPackage);
    }
    if (IsEnemy())
    {
        const TCHAR *Package = Kind == ESSWorldKind::Pursuer
                                   ? TEXT("/Game/SpaceSurvival/Licensed/ShipVisualPass/Meshes/SM_PursuerHavolk")
                                   : TEXT("/Game/SpaceSurvival/Licensed/ShipVisualPass/Meshes/SM_FlankerHavolk");
        if (FPackageName::DoesPackageExist(Package))
            SelectedMesh = LoadObject<UStaticMesh>(nullptr, Package);
    }
    Visual->SetStaticMesh(SelectedMesh ? SelectedMesh : Mesh(*CatalogMesh));
    // Match collision to the loaded mesh rather than assuming authoring units.
    // Missing authoring remains an explicit fallback, not presentation verification.
    const float MeshExtent = Visual->GetStaticMesh() ? Visual->GetStaticMesh()->GetBounds().BoxExtent.GetMax() : 50.f;
    Visual->SetRelativeScale3D(FVector(BodyRadius / FMath::Max(1.f, MeshExtent)));
    Visual->SetRelativeLocation(SelectedMesh ? -Visual->GetRelativeRotation().RotateVector(
                                                   SelectedMesh->GetBounds().Origin * Visual->GetRelativeScale3D())
                                             : FVector::ZeroVector);
    const bool bPreserveAuthoredMaterial = Visual->GetStaticMesh() &&
                                           Visual->GetStaticMesh()->GetPathName().StartsWith(TEXT("/Game/")) &&
                                           (IsSolidHazard() || IsEnemy());
    ThreatIndicator->SetVisibility(IsEnemy());
    UStaticMeshComponent *FeedbackMesh = Visual;
    if (bPreserveAuthoredMaterial)
    {
        // Preserve authored surfaces. A compact muzzle light carries the same
        // committed-shot charge/impact pulse; HUD glyphs identify the archetype.
        // Whole-body luminous rings obscured nearby hazards in compound scenes.
        DynamicMaterial = nullptr;
        if (!IsEnemy())
            return;
        ThreatIndicator->SetStaticMesh(Mesh(TEXT("SM_Projectile")));
        const float IndicatorExtent =
            ThreatIndicator->GetStaticMesh() ? ThreatIndicator->GetStaticMesh()->GetBounds().BoxExtent.GetMax() : 50.f;
        const FBoxSphereBounds Bounds = Visual->GetStaticMesh()->GetBounds();
        const FVector Nose =
            Visual->GetRelativeTransform().TransformPosition(Bounds.Origin + FVector(Bounds.BoxExtent.X, 0, 0));
        ThreatIndicator->SetRelativeLocation(Nose + FVector(BodyRadius * .025f, 0.f, 0.f));
        ThreatIndicator->SetRelativeScale3D(FVector(BodyRadius * .075f / FMath::Max(1.f, IndicatorExtent)));
        ThreatIndicator->SetCastShadow(false);
        FeedbackMesh = ThreatIndicator;
    }
    const TCHAR *MaterialPath = IsEnvironmentalField() || IsEnemy() || Kind == ESSWorldKind::Event ||
                                        Kind == ESSWorldKind::Depot || Kind == ESSWorldKind::Projectile ||
                                        Kind == ESSWorldKind::Pickup
                                    ? TEXT("/Game/SpaceSurvival/Materials/M_Emissive.M_Emissive")
                                    : TEXT("/Game/SpaceSurvival/Materials/M_Hazard.M_Hazard");
    // Field meshes carry distinct electrical/gravity shaders. Read the asset
    // slot, not the component override left by an earlier Configure/BeginPlay.
    // The existing pulse/force clocks continue to own every Emission update.
    UMaterialInterface *Material = nullptr;
    if (IsEnvironmentalField() && Visual->GetStaticMesh() &&
        Visual->GetStaticMesh()->GetPathName().StartsWith(TEXT("/Game/")))
        Material = Visual->GetStaticMesh()->GetMaterial(0);
    if (!Material)
        Material = LoadObject<UMaterialInterface>(nullptr, MaterialPath);
    if (!Material)
        Material =
            LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    if (Material)
    {
        DynamicMaterial = UMaterialInstanceDynamic::Create(Material, this);
        DynamicMaterial->SetVectorParameterValue(TEXT("Tint"), BodyColor(Kind));
        DynamicMaterial->SetVectorParameterValue(TEXT("Color"), FLinearColor::White);
        DynamicMaterial->SetScalarParameterValue(TEXT("Emission"), IsEnvironmentalField() ? .25f : 1.f);
        FeedbackMesh->SetMaterial(0, DynamicMaterial);
    }
    Visual->SetCastShadow(!IsEnvironmentalField());
}

ASSShip *ASSWorldBody::FindShip() const
{
    return Cast<ASSShip>(UGameplayStatics::GetPlayerPawn(this, 0));
}

bool ASSWorldBody::IsEnemy() const
{
    return Kind == ESSWorldKind::Pursuer || Kind == ESSWorldKind::Flanker;
}
bool ASSWorldBody::IsEnvironmentalField() const
{
    return Kind == ESSWorldKind::ElectricalStorm || Kind == ESSWorldKind::GravityAnomaly;
}
bool ASSWorldBody::IsSolidHazard() const
{
    return Kind == ESSWorldKind::SmallAsteroid || Kind == ESSWorldKind::MediumAsteroid ||
           Kind == ESSWorldKind::MassiveAsteroid || Kind == ESSWorldKind::Wreckage;
}
bool ASSWorldBody::IsWeaponTarget() const
{
    if (IsEnemy())
        return true;
    if (!IsSolidHazard())
        return false;
    const auto Definition = Content(this)->Hazard(Kind);
    return Definition.Destructible &&
           (Kind != ESSWorldKind::Wreckage || BodyRadius <= Definition.DestructibleRadiusLimit);
}

FString ASSWorldBody::GetLabel() const
{
    switch (Kind)
    {
    case ESSWorldKind::SmallAsteroid:
        return TEXT("SMALL DEBRIS");
    case ESSWorldKind::MediumAsteroid:
        return TEXT("FRACTURABLE ASTEROID");
    case ESSWorldKind::MassiveAsteroid:
        return TEXT("MASSIVE BODY · EVADE");
    case ESSWorldKind::Wreckage:
        return IsWeaponTarget() ? TEXT("BREAKABLE WRECKAGE") : TEXT("STRUCTURAL WRECKAGE · EVADE");
    case ESSWorldKind::ElectricalStorm:
        return TEXT("ELECTRICAL STORM");
    case ESSWorldKind::GravityAnomaly:
        return TEXT("GRAVITY ANOMALY");
    case ESSWorldKind::Pursuer:
        return TEXT("PURSUER");
    case ESSWorldKind::Flanker:
        return TEXT("FLANKER");
    case ESSWorldKind::Depot:
        return TEXT("MOBILE DEPOT · INTERACT FOR DEALS");
    case ESSWorldKind::Event:
        return TEXT("OPTIONAL SIGNAL · INTERACT TO ACCEPT");
    case ESSWorldKind::Pickup:
        return TEXT("PICKUP");
    default:
        return TEXT("");
    }
}

void ASSWorldBody::ApplyWorldForce(FVector Acceleration, float DeltaSeconds)
{
    if (Kind == ESSWorldKind::MassiveAsteroid || IsEnvironmentalField() || Kind == ESSWorldKind::Event ||
        Kind == ESSWorldKind::Depot)
        return;
    LinearVelocity += Acceleration.GetClampedToMaxSize(1100.f) * DeltaSeconds;
}

void ASSWorldBody::ApplyWorldOffset(const FVector &InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    if (bHasPreviousShipPosition)
        PreviousShipPosition += InOffset;
}

bool ASSWorldBody::AdvanceElectricalPulse(float DeltaSeconds)
{
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds < 0.f)
        return false;
    if (FieldPulseRemaining < 0.0)
    {
        FieldPulseDuration = FMath::Max(1.0, FMath::IsFinite(TelegraphSeconds) ? double(TelegraphSeconds) : 3.5);
        FieldPulseRemaining = FieldPulseDuration;
    }
    FieldPulseRemaining -= double(DeltaSeconds);
    const bool bDischarged = FieldPulseRemaining <= 0.0;
    if (bDischarged)
    {
        // Carry fractional overshoot so cadence does not drift with frame rate.
        // A hitch can display/apply one discharge, never a burst of catch-up damage.
        FieldPulseRemaining = FieldPulseInterval - FMath::Fmod(-FieldPulseRemaining, FieldPulseInterval);
        FieldPulseDuration = FieldPulseInterval;
        bFieldHasDischarged = true;
    }
    if (DynamicMaterial)
    {
        const double Charge = FMath::Clamp(1.0 - FieldPulseRemaining / FieldPulseDuration, 0.0, 1.0);
        double Emission = .35 + 1.75 * Charge;
        const double SinceDischarge = FieldPulseDuration - FieldPulseRemaining;
        if (bDischarged)
            Emission = 2.8;
        else if (bFieldHasDischarged && SinceDischarge < .12)
            Emission = FMath::Max(Emission, 2.8 - 2.45 * SinceDischarge / .12);
        DynamicMaterial->SetScalarParameterValue(TEXT("Emission"), float(Emission));
    }
    return bDischarged;
}

void ASSWorldBody::ConfigureAudio()
{
    if (FieldAudio)
    {
        FieldAudio->Stop();
        FieldAudio->DestroyComponent();
        FieldAudio = nullptr;
    }
    if (!IsEnvironmentalField())
        return;
    if (auto *Audio = GetWorld()->GetSubsystem<USSWorldAudioSubsystem>())
        FieldAudio = Audio->CreateFieldLoop(
            this, Content(this)->Hazard(Kind).FieldLoopAudio,
            Kind == ESSWorldKind::ElectricalStorm ? TEXT("ElectricalCharge") : TEXT("GravityAmbience"), .08f);
}
void ASSWorldBody::UpdateFieldAudio(bool bDischarged)
{
    if (!IsEnvironmentalField())
        return;
    auto *Audio = GetWorld()->GetSubsystem<USSWorldAudioSubsystem>();
    if (!Audio)
        return;
    const float Charge = Kind == ESSWorldKind::ElectricalStorm
                             ? float(FMath::Clamp(1.0 - FieldPulseRemaining / FieldPulseDuration, 0.0, 1.0))
                             : FMath::Clamp(Age / FMath::Max(1.f, TelegraphSeconds), 0.f, 1.f);
    Audio->SetFieldIntensity(FieldAudio, .08f + .92f * Charge,
                             Kind == ESSWorldKind::ElectricalStorm ? .75f + .5f * Charge : 1.f);
    if (bDischarged)
        Audio->PlayOneShot(Content(this)->Hazard(Kind).DischargeAudio, TEXT("ElectricalDischarge"), GetActorLocation());
}
void ASSWorldBody::PlayDestructionAudio()
{
    if (auto *Audio = GetWorld()->GetSubsystem<USSWorldAudioSubsystem>())
    {
        if (IsEnemy())
            Audio->PlayOneShot(Content(this)->Enemy(Kind).DestructionAudio, TEXT("EnemyBreak"), GetActorLocation());
        else if (IsSolidHazard())
            Audio->PlayOneShot(Content(this)->Hazard(Kind).DestructionAudio, TEXT("DebrisBreak"), GetActorLocation());
    }
}
void ASSWorldBody::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bDefeated)
        return;
    const FVector PreviousBodyPosition = GetActorLocation();
    Age += DeltaSeconds;
    ShipContactRemaining = FMath::Max(0.f, ShipContactRemaining - DeltaSeconds);
    AddActorWorldOffset(LinearVelocity * DeltaSeconds, false);
    if (IsSolidHazard())
    {
        Visual->AddLocalRotation(FRotator(2.f, 4.f, 1.5f) * DeltaSeconds);
        const UStaticMesh *VisualMesh = Visual->GetStaticMesh();
        if (VisualMesh && VisualMesh->GetPathName().StartsWith(TEXT("/Game/Asteroid_Library/")))
        {
            // Rotate about the visual bounds centre, not the vendor's off-centre
            // authoring pivot. Keep that centre on the unchanged collision sphere.
            Visual->SetRelativeLocation(-Visual->GetRelativeRotation().RotateVector(VisualMesh->GetBounds().Origin *
                                                                                    Visual->GetRelativeScale3D()));
        }
    }
    const bool bElectricalDischarge = Kind == ESSWorldKind::ElectricalStorm && AdvanceElectricalPulse(DeltaSeconds);
    if (bElectricalDischarge)
        if (auto *FX = GetWorld()->GetSubsystem<USSCombatVFXSubsystem>())
            FX->PlayElectricalDischarge(GetActorLocation(), BodyRadius);
    UpdateFieldAudio(bElectricalDischarge);
    if (Kind == ESSWorldKind::ElectricalStorm && !bFieldPresentationAttached)
        if (auto *FX = GetWorld()->GetSubsystem<USSCombatVFXSubsystem>())
            bFieldPresentationAttached = FX->AttachElectricalField(this, BodyRadius);
    ASSShip *Ship = FindShip();
    if (Ship)
    {
        const FVector Offset = Ship->GetActorLocation() - GetActorLocation();
        const float Distance = Offset.Size();
        if (IsSolidHazard() || IsEnemy())
        {
            const FVector PreviousRelative =
                bHasPreviousShipPosition ? PreviousShipPosition - PreviousBodyPosition : Offset;
            const FVector RelativePath = Offset - PreviousRelative;
            const float ClosestTime =
                RelativePath.IsNearlyZero()
                    ? 1.f
                    : static_cast<float>(FMath::Clamp(
                          -FVector::DotProduct(PreviousRelative, RelativePath) / RelativePath.SizeSquared(), 0.0, 1.0));
            const float SweptDistance = (PreviousRelative + RelativePath * ClosestTime).Size();
            if (SweptDistance < BodyRadius + ShipRadius() && ShipContactRemaining <= 0.f)
            {
                FVector ContactNormal = (PreviousRelative + RelativePath * ClosestTime).GetSafeNormal();
                if (ContactNormal.IsNearlyZero())
                    ContactNormal = PreviousRelative.GetSafeNormal();
                Ship->ReceiveImpact(CollisionDamage, ContactNormal);
                ShipContactRemaining = 1.1f;
            }
        }
        else if (IsEnvironmentalField())
        {
            const float WarningDistance = BodyRadius + Ship->GetVelocity().Size() * TelegraphSeconds;
            if (!bWarningIssued && Distance < WarningDistance)
            {
                bWarningIssued = true;
                Announce(this, Kind == ESSWorldKind::ElectricalStorm
                                   ? TEXT("ELECTRICAL STORM · Field charges before discharge")
                                   : TEXT("GRAVITY ANOMALY · Counter the pull; boost across its edge"));
                if (auto *Mode = GameMode(this))
                {
                    Mode->WarnThreat(Kind == ESSWorldKind::ElectricalStorm ? TEXT("ELECTRICAL FIELD / WATCH THE PULSE")
                                                                           : TEXT("GRAVITY FIELD / COUNTER THE PULL"),
                                     GetActorLocation(), 4.f);
                    Mode->React(Kind == ESSWorldKind::ElectricalStorm ? TEXT("Static on the hull. Keep us clear.")
                                                                      : TEXT("That pull is getting personal."));
                }
            }
            if (Kind == ESSWorldKind::ElectricalStorm)
            {
                if (bElectricalDischarge && Distance < BodyRadius)
                    Ship->ReceiveDamage(CollisionDamage, SS::DamageType::Electrical);
            }
            else
            {
                const bool bReady = Age >= TelegraphSeconds;
                if (DynamicMaterial)
                    DynamicMaterial->SetScalarParameterValue(
                        TEXT("Emission"), bReady ? 1.1f + .3f * FMath::Sin(Age * 4.f)
                                                 : .25f + Age / FMath::Max(1.f, TelegraphSeconds) * .4f);
                if (bReady)
                {
                    if (Distance < BodyRadius)
                    {
                        // Bounded force; no teleport, control lock or singularity at the centre.
                        const float Strength =
                            GravityAcceleration * FMath::Clamp(1.f - Distance / BodyRadius, .15f, 1.f);
                        Ship->AddExternalForce(-Offset.GetSafeNormal() * Strength);
                    }
                    for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
                    {
                        ASSWorldBody *Other = *It;
                        if (Other == this || (!Other->IsSolidHazard() && !Other->IsEnemy()))
                            continue;
                        const FVector ToCentre = GetActorLocation() - Other->GetActorLocation();
                        const float Range = ToCentre.Size();
                        if (Range < BodyRadius)
                            Other->ApplyWorldForce(ToCentre.GetSafeNormal() * GravityAcceleration * .45f *
                                                       (1.f - Range / BodyRadius),
                                                   DeltaSeconds);
                    }
                }
            }
        }
        // Retain hazards across wave boundaries, retire only beyond the playable vicinity.
        PreviousShipPosition = Ship->GetActorLocation();
        bHasPreviousShipPosition = true;
        // Retire on distance, not on facing. This used to be a dot product against the ship's CURRENT
        // forward vector, so a body was kept or destroyed according to where the player happened to be
        // looking: turning around retired everything that had been more than 16,000 ahead, in the frame the
        // turn completed. That contradicts the intended model, in which the danger around the player is one
        // intensity rather than one direction. The radius is larger than the old threshold so that nothing
        // now disappears sooner than it used to, in any direction.
        if (!bAdmitted)
        {
            bAdmitted = true;
            KeepAdmittedAt(Ship->GetActorLocation());
        }
        if (FVector::DistSquared(GetActorLocation(), Ship->GetActorLocation()) > FMath::Square(RetireDistance))
            Destroy();
    }
    if (LifetimeSeconds > 0.f && Age > LifetimeSeconds)
        Destroy();
}

void ASSWorldBody::KeepAdmittedAt(const FVector &ShipLocation)
{
    // The slack covers a field admitted ahead of a ship that then brakes: the field keeps a share of the
    // speed the ship had, and for a few seconds it is the one pulling away.
    RetireDistance = FMath::Max(RetireDistance, FVector::Dist(GetActorLocation(), ShipLocation) + 4000.f);
}

void ASSWorldBody::ReceiveWeaponHit(float Damage)
{
    if (!IsWeaponTarget() || bDefeated || !FMath::IsFinite(Damage) || Damage <= 0.f)
        return;
    Health -= Damage;
    if (DynamicMaterial)
        DynamicMaterial->SetScalarParameterValue(TEXT("Emission"), 1.8f);
    if (Health <= 0.f)
    {
        bDefeated = true;
        OnDefeated();
        Destroy();
    }
}

void ASSWorldBody::OnDefeated()
{
    PlayDestructionAudio();
    if (Kind == ESSWorldKind::SmallAsteroid || Kind == ESSWorldKind::MediumAsteroid)
        ASSAsteroidBurst::SpawnBurst(GetWorld(), GetActorLocation(), LinearVelocity, BodyRadius);
    const auto Definition = Content(this)->Hazard(Kind);
    if (Kind == ESSWorldKind::MediumAsteroid)
    {
        // Keep fragments dangerous, but admit no new body inside the player's reaction path.
        const ASSShip *Ship = FindShip();
        const ASSGameMode *Mode = GameMode(this);
        const float Reaction =
            Mode && Mode->Director ? Mode->Director->MinimumReactionSeconds : Content(this)->MinimumReactionSeconds;
        const float ReactionSeconds = FMath::IsFinite(Reaction) ? FMath::Max(0.f, Reaction) : 3.5f;
        const float Clearance = ShipRadius() + FMath::Max(10.f, Definition.FragmentRadius);
        for (int32 Index = 0; Index < FMath::Clamp(Definition.FragmentCount, 0, 3); ++Index)
        {
            if (!HasThreatCapacity(this))
                break;
            for (int32 Attempt = 0; Attempt < 16; ++Attempt)
            {
                const FVector Direction = LocalRandom.VRand();
                const FVector Position = GetActorLocation() + Direction * (BodyRadius + 80.f);
                const FVector Velocity = LinearVelocity + Direction * Definition.FragmentSpeed;
                if (Ship)
                {
                    const FVector RelativeStart = Position - Ship->GetActorLocation();
                    const FVector RelativeEnd = RelativeStart + (Velocity - Ship->GetVelocity()) * ReactionSeconds;
                    if (FMath::PointDistToSegment(FVector::ZeroVector, RelativeStart, RelativeEnd) <= Clearance)
                        continue;
                }
                if (ASSWorldBody *Fragment = GetWorld()->SpawnActor<ASSWorldBody>(Position, FRotator::ZeroRotator))
                {
                    Fragment->Configure(ESSWorldKind::SmallAsteroid, Definition.FragmentRadius,
                                        CollisionDamage * Definition.FragmentDamageFraction, Wave);
                    Fragment->SetLinearVelocity(Velocity);
                    Fragment->LifetimeSeconds = Definition.FragmentLifetime;
                }
                break;
            }
        }
    }
    if (LocalRandom.FRand() < FMath::Clamp(Definition.DropChance, 0.f, 1.f))
    {
        if (ASSPickup *Pickup = GetWorld()->SpawnActor<ASSPickup>(GetActorLocation(), FRotator::ZeroRotator))
        {
            float TotalWeight = 0.f;
            for (int32 Index = 0; Index < 4; ++Index)
                TotalWeight += FMath::Max(0.f, Content(this)->Pickup(Index).DropWeight);
            float Roll = LocalRandom.FRand() * TotalWeight;
            int32 PickupKind = 0;
            for (int32 Index = 0; Index < 4; ++Index)
            {
                Roll -= FMath::Max(0.f, Content(this)->Pickup(Index).DropWeight);
                if (Roll <= 0.f)
                {
                    PickupKind = Index;
                    break;
                }
            }
            Pickup->ConfigurePickup(PickupKind, Content(this)->Pickup(PickupKind).Amount);
            Pickup->SetLinearVelocity(LinearVelocity * .3f);
        }
    }
}

ASSEnemy::ASSEnemy()
{
    Kind = ESSWorldKind::Pursuer;
    LifetimeSeconds = 75.f;
}

void ASSEnemy::SetObjectiveOwner(ASSEncounterBeacon *InOwner)
{
    ObjectiveOwner = InOwner;
}

void ASSEnemy::Tick(float DeltaSeconds)
{
    ASSShip *Ship = FindShip();
    if (Ship && !bDefeated)
    {
        const auto Definition = Content(this)->Enemy(Kind);
        if (Age == 0.f)
            ShotCooldown = Definition.InitialShotDelay;
        SteeringPhase += DeltaSeconds * (Definition.OrbitRate + Wave * Definition.OrbitRatePerWave);
        const FVector Forward = Ship->GetActorForwardVector();
        const FVector Right = Ship->GetActorRightVector();
        const FVector Up = Ship->GetActorUpVector();
        FVector Desired = Ship->GetActorLocation() + Forward * Definition.ForwardOffset;
        Desired +=
            Right * FMath::Sin(SteeringPhase) * Definition.LateralAmplitude +
            Up * FMath::Cos(SteeringPhase * .65f) * Definition.VerticalAmplitude +
            Forward * FMath::Sin(SteeringPhase * Definition.LongitudinalRateRatio) * Definition.LongitudinalAmplitude;
        const float Response = Definition.Response + Wave * Definition.ResponsePerWave;
        const FVector Catchup = ((Desired - GetActorLocation()) * Response)
                                    .GetClampedToMaxSize(Definition.CatchupSpeed + Wave * Definition.CatchupPerWave);
        LinearVelocity =
            FMath::VInterpTo(LinearVelocity, Ship->GetVelocity() + Catchup, DeltaSeconds, Definition.VelocityResponse);
        FRotator Facing = (Ship->GetActorLocation() - GetActorLocation()).Rotation();
        const FVector RelativeVelocity = LinearVelocity - Ship->GetVelocity();
        Facing.Roll = FMath::Clamp(-FVector::DotProduct(Right, RelativeVelocity) * .018f, -34.f, 34.f);
        SetActorRotation(FMath::RInterpTo(GetActorRotation(), Facing, DeltaSeconds, 4.5f));
        ShotCooldown -= DeltaSeconds;
        if (ShotCharge > 0.f)
        {
            ShotCharge -= DeltaSeconds;
            if (DynamicMaterial)
                DynamicMaterial->SetScalarParameterValue(TEXT("Emission"), 2.8f);
            if (ShotCharge <= 0.f)
            {
                if (ASSProjectile *Shot = GetWorld()->SpawnActor<ASSProjectile>(
                        GetActorLocation() + ShotDirection * (BodyRadius + 30.f), ShotDirection.Rotation()))
                {
                    Shot->Launch(ShotDirection, Definition.ProjectileSpeed + Wave * Definition.ProjectileSpeedPerWave,
                                 Definition.ShotDamage + Wave * Definition.ShotDamagePerWave, false, this);
                    if (auto *Audio = GetWorld()->GetSubsystem<USSWorldAudioSubsystem>())
                        Audio->PlayOneShot(Definition.ShotAudio, TEXT("EnemyFire"), GetActorLocation());
                }
                ShotCooldown = FMath::Max(Definition.MinimumShotInterval,
                                          Definition.ShotInterval - Wave * Definition.ShotIntervalReductionPerWave);
            }
        }
        else if (ShotCooldown <= 0.f && FVector::DistSquared(GetActorLocation(), Ship->GetActorLocation()) <
                                            FMath::Square(Definition.WeaponRange))
        {
            // Aim is committed before discharge. A deliberate dodge can invalidate it.
            const FVector Predicted = Ship->GetActorLocation() + Ship->GetVelocity() * Definition.AimLeadSeconds;
            const float Error = FMath::Max(Definition.MinimumAimError,
                                           Definition.AimError - Wave * Definition.AimErrorReductionPerWave);
            ShotDirection = (Predicted + LocalRandom.VRand() * Error - GetActorLocation()).GetSafeNormal();
            ShotCharge = FMath::Max(.3f, Definition.ShotTelegraph);
        }
        else if (DynamicMaterial)
            DynamicMaterial->SetScalarParameterValue(TEXT("Emission"), 1.f);

        // Enemies share the environment; they neither phase through nor ignore asteroids.
        for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
        {
            ASSWorldBody *Obstacle = *It;
            if (Obstacle == this || !Obstacle->IsSolidHazard())
                continue;
            const FVector Separation = GetActorLocation() - Obstacle->GetActorLocation();
            const float CombinedRadius = BodyRadius + Obstacle->GetBodyRadius();
            if (Separation.SizeSquared() < FMath::Square(CombinedRadius + Definition.AvoidanceDistance))
                LinearVelocity += Separation.GetSafeNormal() * Definition.AvoidanceAcceleration * DeltaSeconds;
            if (Separation.SizeSquared() < FMath::Square(CombinedRadius))
            {
                Health -= Definition.HazardDamagePerSecond * DeltaSeconds;
                if (Health <= 0.f)
                {
                    bDefeated = true;
                    PlayDestructionAudio();
                    if (auto *FX = GetWorld()->GetSubsystem<USSCombatVFXSubsystem>())
                        FX->PlayEnemyExplosion(GetActorLocation(), BodyRadius);
                    if (ObjectiveOwner.IsValid())
                        ObjectiveOwner->RegisterObjectiveProgress();
                    Destroy();
                    return;
                }
            }
        }
    }
    Super::Tick(DeltaSeconds);
}

void ASSEnemy::OnDefeated()
{
    PlayDestructionAudio();
    if (auto *FX = GetWorld()->GetSubsystem<USSCombatVFXSubsystem>())
        FX->PlayEnemyExplosion(GetActorLocation(), BodyRadius);
    ASSWave10Soak::NotifyEnemyDefeated(this);
    if (ASSGameMode *Mode = GameMode(this))
        Mode->NotifyEnemyKilled();
    if (ObjectiveOwner.IsValid())
        ObjectiveOwner->RegisterObjectiveProgress();
    // Credits from a kill are awarded once by the domain; physical pickups are extra risk income.
    const auto Definition = Content(this)->Enemy(Kind);
    if (LocalRandom.FRand() < Definition.CreditDropChance)
        if (ASSPickup *Pickup = GetWorld()->SpawnActor<ASSPickup>(GetActorLocation(), FRotator::ZeroRotator))
            Pickup->ConfigurePickup(0, Definition.CreditDropAmount);
}

ASSProjectile::ASSProjectile()
{
    Kind = ESSWorldKind::Projectile;
    BodyRadius = 16.f;
    LifetimeSeconds = 6.f;
    ShotLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("ShotLight"));
    ShotLight->SetupAttachment(Visual);
    ShotLight->SetIntensityUnits(ELightUnits::Lumens);
    ShotLight->SetCastShadows(false);
    ShotLight->SetAttenuationRadius(650.f);
    ShotLight->SetVisibility(false);
}

void ASSProjectile::Launch(FVector Direction, float Speed, float Damage, bool bFromPlayer, AActor *Source,
                           float MaximumTravel)
{
    Configure(ESSWorldKind::Projectile, bFromPlayer ? 28.f : 17.f, Damage);
    LifetimeSeconds = 6.f;
    bPlayerShot = bFromPlayer;
    TravelRemaining = FMath::IsFinite(MaximumTravel) ? MaximumTravel : 0.f;
    SourceActor = Source;
    LinearVelocity = Direction.GetSafeNormal() * Speed;
    const bool Heavy = bFromPlayer && Damage > 0.f;
    if (auto *FX = GetWorld()->GetSubsystem<USSCombatVFXSubsystem>())
    {
        FX->AttachProjectile(this, bFromPlayer, Heavy);
        FX->PlayMuzzle(Source, GetActorLocation(), Direction, bFromPlayer, Heavy);
    }
    // A distinct native core and compact light remain readable if scalability culls Niagara.
    const FVector CoreShape = !bFromPlayer ? FVector(2.8f, .46f, .46f)
                              : Heavy      ? FVector(2.2f, .72f, .72f)
                                           : FVector(5.4f, .38f, .38f);
    Visual->SetRelativeScale3D(Visual->GetRelativeScale3D() * CoreShape);
    const FLinearColor LightColor = !bFromPlayer ? FLinearColor(1.f, .04f, .01f)
                                    : Heavy      ? FLinearColor(1.f, .34f, .025f)
                                                 : FLinearColor(.04f, .8f, 1.f);
    ShotLight->SetLightColor(LightColor);
    ShotLight->SetIntensity(!bFromPlayer ? 3800.f : Heavy ? 8200.f : 5600.f);
    ShotLight->SetAttenuationRadius(Heavy ? 900.f : 650.f);
    ShotLight->SetVisibility(true);
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    TrackedShip = FindShip();
    bHasPreviousShipPosition = TrackedShip.IsValid();
    if (TrackedShip.IsValid())
    {
        PreviousShipPosition = TrackedShip->GetActorLocation();
        // Sample the ship after its movement, so both swept paths share one frame.
        AddTickPrerequisiteActor(TrackedShip.Get());
    }
    if (DynamicMaterial)
        DynamicMaterial->SetVectorParameterValue(TEXT("Tint"), bPlayerShot ? FLinearColor(.3f, 1.f, 1.f)
                                                                           : FLinearColor(1.f, .2f, .05f));
}

void ASSProjectile::Tick(float DeltaSeconds)
{
    if (IsActorBeingDestroyed())
        return;
    // Both paths stop at the same live-time boundary, including range expiry.
    const float FrameSeconds = FMath::Max(0.f, DeltaSeconds);
    float FlightSeconds = FMath::Min(FrameSeconds, FMath::Max(0.f, LifetimeSeconds - Age));
    if (TravelRemaining >= 0.f && LinearVelocity.SizeSquared() > UE_SMALL_NUMBER)
        FlightSeconds = FMath::Min(FlightSeconds, TravelRemaining / float(LinearVelocity.Size()));
    Age += FrameSeconds;
    const FVector Start = GetActorLocation();
    FVector Travel = LinearVelocity * FlightSeconds;
    if (TravelRemaining >= 0.f)
    {
        Travel = Travel.GetClampedToMaxSize(TravelRemaining);
        TravelRemaining = FMath::Max(0.f, TravelRemaining - float(Travel.Size()));
        // FVector clamps smaller distances to zero. Retire the same residual
        // instead of leaving a stationary projectile until its lifetime ends.
        if (TravelRemaining < UE_KINDA_SMALL_NUMBER)
            TravelRemaining = 0.f;
    }
    const FVector End = Start + Travel;
    ASSShip *Ship = FindShip();
    if (Ship != TrackedShip.Get())
    {
        if (TrackedShip.IsValid())
            RemoveTickPrerequisiteActor(TrackedShip.Get());
        TrackedShip = Ship;
        bHasPreviousShipPosition = Ship != nullptr;
        if (Ship)
        {
            PreviousShipPosition = Ship->GetActorLocation();
            AddTickPrerequisiteActor(Ship);
        }
    }
    double ShipHitTime = 2.0;
    if (Ship)
    {
        const FVector ShipStart = bHasPreviousShipPosition ? PreviousShipPosition : Ship->GetActorLocation();
        const float LiveFraction = FrameSeconds > 0.f ? FlightSeconds / FrameSeconds : 0.f;
        const FVector ShipTravel = (Ship->GetActorLocation() - ShipStart) * LiveFraction;
        if (!bPlayerShot && Ship != SourceActor.Get())
        {
            // Solve first contact between simultaneous paths. A sweep against the
            // ship's final position alone can reward a dodge with a false hit.
            const FVector RelativeStart = Start - ShipStart;
            const FVector RelativeTravel = Travel - ShipTravel;
            const double Radius = BodyRadius + Ship->Collision->GetScaledSphereRadius();
            const double C = RelativeStart.SizeSquared() - Radius * Radius;
            const double A = RelativeTravel.SizeSquared();
            const double B = FVector::DotProduct(RelativeStart, RelativeTravel);
            const double Discriminant = B * B - A * C;
            if (C <= 0.0)
                ShipHitTime = 0.0;
            else if (A > UE_SMALL_NUMBER && B < 0.0 && Discriminant >= 0.0)
            {
                const double Contact = (-B - FMath::Sqrt(Discriminant)) / A;
                if (Contact >= 0.0 && Contact <= 1.0)
                    ShipHitTime = Contact;
            }
        }
        PreviousShipPosition = Ship->GetActorLocation();
        bHasPreviousShipPosition = true;
    }
    FCollisionObjectQueryParams Objects;
    Objects.AddObjectTypesToQuery(ECC_WorldDynamic);
    Objects.AddObjectTypesToQuery(ECC_WorldStatic);
    Objects.AddObjectTypesToQuery(ECC_Pawn);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SpaceSurvivalProjectile), false, this);
    if (SourceActor.IsValid())
        Query.AddIgnoredActor(SourceActor.Get());
    if (Ship)
        Query.AddIgnoredActor(Ship);
    TArray<FHitResult> Hits;
    GetWorld()->SweepMultiByObjectType(Hits, Start, End, FQuat::Identity, Objects,
                                       FCollisionShape::MakeSphere(BodyRadius), Query);
    Hits.Sort([](const FHitResult &A, const FHitResult &B) { return A.Time < B.Time; });
    const FHitResult *WorldHit = nullptr;
    for (const FHitResult &Hit : Hits)
    {
        if (const ASSWorldBody *Body = Cast<ASSWorldBody>(Hit.GetActor()))
        {
            if (!Body->IsSolidHazard() && !Body->IsEnemy())
                continue;
        }
        else if (!Hit.bBlockingHit)
            continue;
        WorldHit = &Hit;
        break;
    }
    // Cover wins a simultaneous contact. Later cover cannot erase an earlier hit.
    if (ShipHitTime <= 1.0 && (!WorldHit || ShipHitTime < WorldHit->Time))
    {
        Ship->ReceiveDamage(CollisionDamage, SS::DamageType::Energy);
        if (auto *FX = GetWorld()->GetSubsystem<USSCombatVFXSubsystem>(); FX && CollisionDamage > 0.f)
            FX->PlayImpact(Start + Travel * ShipHitTime, -LinearVelocity.GetSafeNormal(), bPlayerShot, false);
        Destroy();
        return;
    }
    if (WorldHit)
    {
        if (auto *FX = GetWorld()->GetSubsystem<USSCombatVFXSubsystem>(); FX && CollisionDamage > 0.f)
            FX->PlayImpact(WorldHit->ImpactPoint, WorldHit->ImpactNormal, bPlayerShot, bPlayerShot);
        ASSWorldBody *Body = Cast<ASSWorldBody>(WorldHit->GetActor());
        if (Body)
            if (bPlayerShot || Body->IsSolidHazard())
                Body->ReceiveWeaponHit(CollisionDamage);
        if (bPlayerShot && CollisionDamage > 0.f && Body && Body->IsWeaponTarget())
            if (auto *Mode = GetWorld()->GetAuthGameMode<ASSGameMode>())
                Mode->NotifyPlayerShotHit();
        Destroy();
        return;
    }
    SetActorLocation(End);
    if (Age >= LifetimeSeconds || TravelRemaining == 0.f)
        Destroy();
}

void ASSProjectile::ReceiveWeaponHit(float Damage)
{
    if (Damage > 0.f)
        Destroy();
}

ASSWormholePassage::ASSWormholePassage()
{
    Kind = ESSWorldKind::Event;
    LifetimeSeconds = 0.f;
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    for (int32 Index = 0; Index < 5; ++Index)
    {
        UStaticMeshComponent *Ring =
            CreateDefaultSubobject<UStaticMeshComponent>(*FString::Printf(TEXT("PassageRing%d"), Index));
        Ring->SetupAttachment(RootComponent);
        Ring->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        PassageRings.Add(Ring);
    }
}

void ASSWormholePassage::BeginPassage(ASSShip *Ship, float Duration)
{
    if (!Ship)
    {
        Destroy();
        return;
    }
    PassageShip = Ship;
    PassageDuration = FMath::Max(1.f, Duration);
    PassageElapsed = 0.f;
    PassageForward = Ship->GetActorForwardVector();
    EntryPoint = Ship->GetActorLocation();
    CourseLength = FMath::Max(10000.f, static_cast<float>(Ship->GetVelocity().Size()) * PassageDuration * 1.08f);
    SetActorLocation(EntryPoint + PassageForward * 2500.f);
    SetActorRotation(PassageForward.Rotation());
    if (auto *FX = GetWorld()->GetSubsystem<USSCombatVFXSubsystem>())
        FX->AttachAnomaly(this);
    UStaticMesh *RingMesh = Mesh(TEXT("SM_GravityRing"));
    Visual->SetStaticMesh(RingMesh);
    const float MeshExtent = RingMesh ? RingMesh->GetBounds().BoxExtent.GetMax() : 50.f;
    const float UnitScale = 1.f / FMath::Max(1.f, MeshExtent);
    Visual->SetRelativeScale3D(FVector(1800.f * UnitScale));
    if (DynamicMaterial)
    {
        DynamicMaterial->SetVectorParameterValue(TEXT("Tint"), FLinearColor(.15f, .55f, 1.f));
        DynamicMaterial->SetScalarParameterValue(TEXT("Emission"), 2.5f);
    }
    for (int32 Index = 0; Index < PassageRings.Num(); ++Index)
    {
        UStaticMeshComponent *Ring = PassageRings[Index];
        Ring->SetStaticMesh(RingMesh);
        const float Alpha = float(Index + 1) / float(PassageRings.Num());
        Ring->SetRelativeLocation(FVector(CourseLength * Alpha, 0.f, 0.f));
        Ring->SetRelativeScale3D(FVector(FMath::Lerp(1700.f, 2300.f, Alpha) * UnitScale));
        if (DynamicMaterial)
            Ring->SetMaterial(0, DynamicMaterial);
        Ring->SetCastShadow(false);
    }
}

void ASSWormholePassage::Tick(float DeltaSeconds)
{
    // Deliberately bypass the environmental-field tick: this sequence never deals
    // damage, spawns a fifth hazard family, teleports, or advances the run state.
    PassageElapsed += DeltaSeconds;
    if (!PassageShip.IsValid())
    {
        Destroy();
        return;
    }
    ASSShip *Ship = PassageShip.Get();
    const float Alpha = FMath::Clamp(PassageElapsed / PassageDuration, 0.f, 1.f);
    const FVector Relative = Ship->GetActorLocation() - EntryPoint;
    const FVector Lateral = Relative - PassageForward * FVector::DotProduct(Relative, PassageForward);
    const FVector Centring = -Lateral.GetClampedToMaxSize(2000.f) * (.12f + .22f * Alpha);
    // A bounded exit turbulence envelope gives the transition a physical release,
    // without reversing input or adding immunity. Forward control remains available.
    const float ExitTime = PassageElapsed - PassageDuration;
    if (ExitTime < 0.f)
    {
        // The entrance is behind the camera soon after transit begins. Keep
        // the one bounded Niagara mouth ahead while the native course stays
        // anchored to its original world positions. Forces use EntryPoint.
        SetActorLocation(Ship->GetActorLocation() + PassageForward * 3500.f);
        const FVector CourseStart = GetActorTransform().InverseTransformPosition(EntryPoint + PassageForward * 2500.f);
        Visual->SetRelativeLocation(CourseStart);
        for (int32 Index = 0; Index < PassageRings.Num(); ++Index)
            PassageRings[Index]->SetRelativeLocation(
                CourseStart + FVector(CourseLength * float(Index + 1) / float(PassageRings.Num()), 0.f, 0.f));
    }
    const float ExitEnvelope =
        ExitTime >= 0.f ? FMath::Max(0.f, 1.f - ExitTime / 2.f) : FMath::Clamp((Alpha - .75f) * 4.f, 0.f, 1.f);
    const FVector Turbulence = Ship->GetActorRightVector() * FMath::Sin(PassageElapsed * 7.f) * 650.f +
                               Ship->GetActorUpVector() * FMath::Cos(PassageElapsed * 5.f) * 420.f;
    Ship->AddExternalForce(
        (ExitTime < 0.f ? PassageForward * (600.f + 1600.f * Alpha) + Centring : FVector::ZeroVector) +
        Turbulence * ExitEnvelope);
    if (ExitTime >= 0.f)
    {
        Visual->SetVisibility(false);
        for (UStaticMeshComponent *Ring : PassageRings)
            Ring->SetVisibility(false);
    }
    Visual->AddLocalRotation(FRotator(0.f, 0.f, 40.f * DeltaSeconds));
    for (int32 Index = 0; Index < PassageRings.Num(); ++Index)
        PassageRings[Index]->AddLocalRotation(
            FRotator(0.f, 0.f, (Index % 2 ? -1.f : 1.f) * (35.f + 20.f * Alpha) * DeltaSeconds));
    if (DynamicMaterial)
        DynamicMaterial->SetScalarParameterValue(TEXT("Emission"),
                                                 1.8f + Alpha * 2.f + .3f * FMath::Sin(PassageElapsed * 8.f));
    if (PassageElapsed >= PassageDuration + 2.f)
        Destroy();
}

void ASSWormholePassage::ApplyWorldOffset(const FVector &InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    EntryPoint += InOffset;
}

ASSPickup::ASSPickup()
{
    Kind = ESSWorldKind::Pickup;
    BodyRadius = 60.f;
    LifetimeSeconds = 30.f;
}

void ASSPickup::ConfigurePickup(int32 InKind, float InAmount, ASSEncounterBeacon *Objective)
{
    PickupKind = FMath::Clamp(InKind, 0, 3);
    const auto Definition = Content(this)->Pickup(PickupKind);
    Configure(ESSWorldKind::Pickup, Definition.Radius, 0.f);
    LifetimeSeconds = Definition.Lifetime;
    Amount = FMath::Max(0.f, InAmount);
    ObjectiveOwner = Objective;
    // A ship can cross the pickup between configuration and its first tick.
    ASSShip *Ship = FindShip();
    bHasPreviousShipPosition = Ship != nullptr;
    if (Ship)
        PreviousShipPosition = Ship->GetActorLocation();
    const TCHAR *Fallbacks[] = {TEXT("/Engine/BasicShapes/Cylinder.Cylinder"), TEXT("/Engine/BasicShapes/Cube.Cube"),
                                TEXT("/Engine/BasicShapes/Sphere.Sphere"), TEXT("/Engine/BasicShapes/Cone.Cone")};
    Visual->SetStaticMesh(Mesh(*Definition.MeshName.ToString(), Fallbacks[PickupKind]));
    const float MeshExtent = Visual->GetStaticMesh() ? Visual->GetStaticMesh()->GetBounds().BoxExtent.GetMax() : 50.f;
    Visual->SetRelativeScale3D(FVector(BodyRadius / FMath::Max(1.f, MeshExtent)));
    if (DynamicMaterial)
        DynamicMaterial->SetVectorParameterValue(TEXT("Tint"), Definition.Tint);
    Collision->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
}

FString ASSPickup::GetLabel() const
{
    if (ObjectiveOwner.IsValid())
        return TEXT("SALVAGE CACHE · COLLECT");
    return Content(this)->Pickup(PickupKind).Label;
}

void ASSPickup::Tick(float DeltaSeconds)
{
    if (bCollected || IsActorBeingDestroyed())
        return;
    const float FrameSeconds = FMath::Max(0.f, DeltaSeconds);
    const float RemainingSeconds = LifetimeSeconds > 0.f ? FMath::Max(0.f, LifetimeSeconds - Age) : FrameSeconds;
    const float LiveSeconds = FMath::Min(FrameSeconds, RemainingSeconds);
    const bool bExpires = LifetimeSeconds > 0.f && FrameSeconds >= RemainingSeconds;
    if (bExpires && RemainingSeconds <= 0.f)
    {
        Destroy();
        return;
    }
    ASSShip *Ship = FindShip();
    // Preserve both moving endpoints, including only the live fraction of an expiry frame.
    const FVector ShipStart =
        Ship ? (bHasPreviousShipPosition ? PreviousShipPosition : Ship->GetActorLocation()) : FVector::ZeroVector;
    const FVector ShipEnd =
        Ship ? FMath::Lerp(ShipStart, Ship->GetActorLocation(), FrameSeconds > 0.f ? LiveSeconds / FrameSeconds : 1.f)
             : FVector::ZeroVector;
    const FVector PreviousRelative = ShipStart - GetActorLocation();
    Super::Tick(LiveSeconds);
    if (IsActorBeingDestroyed())
        return;
    Visual->AddLocalRotation(FRotator(0.f, 70.f, 20.f) * LiveSeconds);
    if (Ship)
    {
        const FVector ToShip = ShipEnd - GetActorLocation();
        const auto Definition = Content(this)->Pickup(PickupKind);
        const float CollectionRadius = ShipRadius() + Definition.CollectionPadding;
        const bool bCrossedCollection =
            FMath::PointDistToSegment(FVector::ZeroVector, PreviousRelative, ToShip) < CollectionRadius;
        // Magnetism remains local and cannot overshoot or continue after expiry.
        if (ToShip.SizeSquared() < FMath::Square(Definition.AttractionRadius))
        {
            const double Travel = FMath::Clamp(double(Definition.AttractionSpeed) * LiveSeconds, 0.0, ToShip.Size());
            AddActorWorldOffset(ToShip.GetSafeNormal() * Travel);
        }
        if (bCrossedCollection || FVector::DistSquared(ShipEnd, GetActorLocation()) < FMath::Square(CollectionRadius))
        {
            bCollected = true;
            if (ASSGameMode *Mode = GameMode(this))
                Mode->NotifyPickup(PickupKind, Amount);
            if (ObjectiveOwner.IsValid())
                ObjectiveOwner->RegisterObjectiveProgress();
            Destroy();
            return;
        }
    }
    if (bExpires)
        Destroy();
}

ASSEncounterBeacon::ASSEncounterBeacon()
{
    Kind = ESSWorldKind::Event;
    BodyRadius = 140.f;
    LifetimeSeconds = 80.f;
}

void ASSEncounterBeacon::ConfigureEncounter(ESSEncounterKind InKind, int32 InWave)
{
    EncounterKind = InKind;
    const auto Definition = Content(this)->Encounter(InKind);
    Configure(IsDepot() ? ESSWorldKind::Depot : ESSWorldKind::Event, Definition.BeaconRadius, 0.f, InWave);
    InteractionRadius = FMath::Max(100.f, Definition.InteractionRadius);
    LifetimeSeconds = FMath::Max(1.f, Definition.Lifetime);
    Collision->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
    Offers = {0, 1, 2, 3, 4};
    FRandomStream OfferRandom(GetUniqueID() ^ InWave * 101);
    for (int32 Index = Offers.Num() - 1; Index > 0; --Index)
        Offers.Swap(Index, OfferRandom.RandRange(0, Index));
    Offers.SetNum(3);
    Discount = FMath::Clamp(
        OfferRandom.RandRange(0, 1) ? Definition.DepotPriceFractionA : Definition.DepotPriceFractionB, .1f, 1.f);
}

bool ASSEncounterBeacon::IsPlayerInRange() const
{
    const ASSShip *Ship = FindShip();
    return Ship &&
           FVector::DistSquared(Ship->GetActorLocation(), GetActorLocation()) <= FMath::Square(InteractionRadius);
}

FString ASSEncounterBeacon::GetEncounterLabel() const
{
    if (IsDepot())
        return FString::Printf(TEXT("DEPOT · OPTIONAL 20s MAGNETIC MOORING · %d%% OFF"),
                               FMath::RoundToInt((1.f - Discount) * 100.f));
    const TCHAR *Name =
        EncounterKind == ESSEncounterKind::SalvageCache ? TEXT("SALVAGE CACHE") : TEXT("DISTRESS / COMBAT");
    if (bResolved)
        return FString::Printf(TEXT("%s · RESOLVED"), Name);
    if (bAccepted)
        return FString::Printf(TEXT("%s · %d OBJECTIVES REMAIN"), Name, ObjectiveRemaining);
    return FString::Printf(TEXT("%s · OPTIONAL · INTERACT TO ACCEPT"), Name);
}

bool ASSEncounterBeacon::TryAccept()
{
    if (bResolved || bAccepted || !IsPlayerInRange())
        return false;
    if (IsDepot())
    {
        ASSShip *Ship = FindShip();
        if (!Ship || Ship->IsMoored())
            return false;
        bool bFieldClear = true;
        for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
            if (It->IsEnvironmentalField() && !It->IsActorBeingDestroyed() &&
                FVector::DistSquared(It->GetActorLocation(), Ship->GetActorLocation()) <
                    FMath::Square(It->GetBodyRadius() + 1500.f))
                bFieldClear = false;
        if (!bFieldClear || !HasSpatialClearance(this, Ship->GetActorLocation(), Ship->GetActorLocation(), 1500.f))
        {
            Announce(this, TEXT("MOORING UNSAFE / Clear nearby hazards before engaging the lock"));
            return false;
        }
        if (!Ship->BeginMooring())
            return false;
        bAccepted = true;
        ObjectiveSeconds = 20.f;
        LifetimeSeconds = FMath::Max(LifetimeSeconds, Age + 25.f);
        Announce(this, TEXT("MAGNETIC LOCK / Stay aboard. Select services, then release to depart."));
        return true;
    }
    if (bAccepted)
        return false;
    if (USSGameInstance *Instance = GetGameInstance<USSGameInstance>())
    {
        if (Instance->Session.run.pendingReward)
        {
            Announce(this, TEXT("Claim your secured reward before accepting another signal."));
            return false;
        }
    }
    for (TActorIterator<ASSEncounterBeacon> It(GetWorld()); It; ++It)
        if (*It != this && It->IsAccepted() && !It->IsResolved())
        {
            Announce(this, TEXT("Resolve the active optional signal first."));
            return false;
        }
    ASSShip *Ship = FindShip();
    if (!Ship)
        return false;
    const auto Definition = Content(this)->Encounter(EncounterKind);
    const int32 ObjectiveCount = FMath::Clamp(Definition.ObjectiveCount, 1, 3);
    if (!HasThreatCapacity(this, EncounterKind == ESSEncounterKind::SalvageCache ? ObjectiveCount * 2 : ObjectiveCount))
    {
        Announce(this, TEXT("SIGNAL ON HOLD · Clear nearby threats before accepting"));
        return false;
    }
    const FVector Forward = Ship->GetActorForwardVector();
    const FVector Right = Ship->GetActorRightVector();
    const FVector Up = Ship->GetActorUpVector();
    const FVector ShipOrigin = Ship->GetActorLocation();
    const float Lead =
        FMath::Max(Definition.ObjectiveLeadDistance,
                   static_cast<float>(Ship->GetVelocity().Size()) *
                       FMath::Max(Content(this)->MinimumReactionSeconds, Definition.ObjectiveLeadSeconds));
    const FVector2D RouteOffsets[] = {FVector2D(0, 0),     FVector2D(1400, 0),    FVector2D(-1400, 0),
                                      FVector2D(2800, 0),  FVector2D(-2800, 0),   FVector2D(0, 1200),
                                      FVector2D(0, -1200), FVector2D(1400, 1200), FVector2D(-1400, -1200)};
    FVector Origin = ShipOrigin;
    bool bRouteClear = false;
    for (const FVector2D Offset : RouteOffsets)
    {
        const FVector CandidateOrigin = ShipOrigin + Right * Offset.X + Up * Offset.Y;
        FVector PreviousCache = ShipOrigin;
        bool bClear = true;
        for (int32 Index = 0; Index < ObjectiveCount && bClear; ++Index)
        {
            if (EncounterKind == ESSEncounterKind::SalvageCache)
            {
                const FVector Centre =
                    CandidateOrigin + Forward * (Lead + Index * Definition.CacheSpacing) +
                    Right * (Index % 2 ? -Definition.CacheLateralOffset : Definition.CacheLateralOffset);
                bClear = HasSpatialClearance(this, PreviousCache, Centre, ShipRadius());
                for (int32 Side : {-1, 1})
                {
                    const FVector DebrisPosition = Centre + Right * Side * Definition.DebrisHalfSpacing + Up * 100.f;
                    bClear =
                        bClear && HasSpatialClearance(this, DebrisPosition, DebrisPosition, Definition.DebrisRadius);
                }
                PreviousCache = Centre;
            }
            else
            {
                const ESSWorldKind EnemyKind = Index % 2 ? ESSWorldKind::Flanker : ESSWorldKind::Pursuer;
                const FVector Position =
                    CandidateOrigin + Forward * Lead +
                    Right * (Index - .5f * (ObjectiveCount - 1)) * 2.f * Definition.DebrisHalfSpacing;
                bClear = HasSpatialClearance(this, Position, Position, Content(this)->Enemy(EnemyKind).Radius);
            }
        }
        if (bClear)
        {
            Origin = CandidateOrigin;
            bRouteClear = true;
            break;
        }
    }
    if (!bRouteClear)
    {
        Announce(this, TEXT("SIGNAL ON HOLD / Objective route obstructed; move into clear space and retry"));
        return false;
    }
    bAccepted = true;
    ObjectiveRemaining = ObjectiveCount;
    ObjectiveSeconds = FMath::Max(3.f, Definition.ObjectiveDuration);
    // Offer age must not shorten the objective window granted on acceptance.
    LifetimeSeconds = FMath::Max(LifetimeSeconds, Age + ObjectiveSeconds + 5.f);
    // Nor may distance. The objectives report to this signal, and the last of them is a course length away
    // from it: accepted during a boost, the third cache sits past the radius at which the signal would retire,
    // taking the objective's progress with it.
    RetireDistance += Lead + (ObjectiveCount - 1) * FMath::Max(0.f, Definition.CacheSpacing) + 4000.f;
    if (USSGameInstance *Instance = GetGameInstance<USSGameInstance>())
    {
        if (EncounterKind == ESSEncounterKind::SalvageCache)
            Instance->Session.run.salvageEventAccepted = true;
        else
            Instance->Session.run.distressEventAccepted = true;
    }
    if (EncounterKind == ESSEncounterKind::SalvageCache)
    {
        Announce(this, FString::Printf(TEXT("SALVAGE ACCEPTED · Collect %d marked caches through the wreckage"),
                                       ObjectiveCount));
        for (int32 Index = 0; Index < ObjectiveCount; ++Index)
        {
            const FVector Centre = Origin + Forward * (Lead + Index * Definition.CacheSpacing) +
                                   Right * (Index % 2 ? -Definition.CacheLateralOffset : Definition.CacheLateralOffset);
            if (ASSPickup *Cache = GetWorld()->SpawnActor<ASSPickup>(Centre, FRotator::ZeroRotator))
            {
                Cache->ConfigurePickup(0, Definition.CacheCredits, this);
                Cache->LifetimeSeconds = FMath::Max(35.f, Definition.ObjectiveDuration + 5.f);
            }
            for (int32 Side = -1; Side <= 1; Side += 2)
                if (ASSWorldBody *Debris = GetWorld()->SpawnActor<ASSWorldBody>(
                        Centre + Right * Side * Definition.DebrisHalfSpacing + Up * 100.f, FRotator::ZeroRotator))
                    Debris->Configure(ESSWorldKind::Wreckage, Definition.DebrisRadius,
                                      Definition.DebrisDamageBase + Wave * Definition.DebrisDamagePerWave, Wave);
        }
    }
    else
    {
        Announce(this, FString::Printf(TEXT("DISTRESS ACCEPTED · Defeat %d attackers; reward choice follows success"),
                                       ObjectiveCount));
        for (int32 Index = 0; Index < ObjectiveCount; ++Index)
            if (ASSEnemy *Enemy = GetWorld()->SpawnActor<ASSEnemy>(Origin + Forward * Lead +
                                                                       Right * (Index - .5f * (ObjectiveCount - 1)) *
                                                                           2.f * Definition.DebrisHalfSpacing,
                                                                   FRotator::ZeroRotator))
            {
                const ESSWorldKind EnemyKind = Index % 2 ? ESSWorldKind::Flanker : ESSWorldKind::Pursuer;
                const auto EnemyDefinition = Content(this)->Enemy(EnemyKind);
                Enemy->Configure(EnemyKind, EnemyDefinition.Radius, Definition.EnemyCollisionDamage, Wave);
                Enemy->SetObjectiveOwner(this);
                Enemy->SetLinearVelocity(Ship->GetVelocity());
            }
    }
    return true;
}

void ASSEncounterBeacon::RegisterObjectiveProgress()
{
    if (!bAccepted || bResolved || IsDepot())
        return;
    ObjectiveRemaining = FMath::Max(0, ObjectiveRemaining - 1);
    if (ObjectiveRemaining == 0)
    {
        bResolved = true;
        if (ASSGameMode *Mode = GameMode(this))
            Mode->NotifyEventCompleted(EncounterKind == ESSEncounterKind::DistressCombat);
    }
}

void ASSEncounterBeacon::FailObjective()
{
    if (bResolved || IsDepot())
        return;
    bResolved = true;
    Announce(this, TEXT("OPTIONAL SIGNAL LOST · No reward; no credit penalty"));
}

void ASSEncounterBeacon::Tick(float DeltaSeconds)
{
    // A signal marks a place in the world; proximity never makes it follow the player.
    LinearVelocity = FVector::ZeroVector;
    if (!bAnnounced)
    {
        bAnnounced = true;
        Announce(this, GetEncounterLabel());
    }
    if (IsDepot() && bAccepted && !bResolved)
    {
        ObjectiveSeconds -= DeltaSeconds;
        ASSShip *Ship = FindShip();
        if (!Ship || !Ship->IsMoored() || ObjectiveSeconds <= 0.f)
        {
            bResolved = true;
            if (ASSGameMode *Mode = GameMode(this))
                if (Mode->ActiveBeacon == this && Mode->Panel == ESSPanel::Depot)
                    Mode->ClosePanel();
            if (Ship && Ship->IsMoored())
                Ship->EndMooring();
            Announce(this, TEXT("MAGNETIC LOCK RELEASED / Departure clear"));
        }
    }
    Super::Tick(DeltaSeconds);
    Visual->AddLocalRotation(FRotator(0.f, 15.f, 0.f) * DeltaSeconds);
    if (bAccepted && !bResolved && !IsDepot())
    {
        ObjectiveSeconds -= DeltaSeconds;
        if (ObjectiveSeconds <= 0.f)
            FailObjective();
    }
}

USSSurvivalDirectorComponent::USSSurvivalDirectorComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    bAutoActivate = false;
    Random.Initialize(0x53A9);
}

ASSShip *USSSurvivalDirectorComponent::FindShip() const
{
    return Cast<ASSShip>(UGameplayStatics::GetPlayerPawn(this, 0));
}

void USSSurvivalDirectorComponent::Configure(int32 InWave, bool bInClimax)
{
    Wave = FMath::Clamp(InWave, 1, 10);
    bClimax = bInClimax;
    bBreathing = false;
    WaveAge = 0.f;
    AvailableBudget = 1.f;
    SpawnCooldown = .75f;
    bCompoundGravitySpawned = bCompoundAsteroidSpawned = bCompoundEnemySpawned = false;
    CompoundGravity.Reset();
    SafeLane = FVector2D(Random.RandRange(-1, 1) * 950.f, Random.RandRange(-1, 1) * 750.f);
    if (USSGameInstance *Instance = Cast<USSGameInstance>(GetWorld()->GetGameInstance()))
    {
        bDepotOffered = Instance->Session.run.depotSeen;
        bSalvageOffered = Instance->Session.run.salvageEventSeen;
        bDistressOffered = Instance->Session.run.distressEventSeen;
        Random.Initialize(static_cast<int32>(Instance->Session.run.rng ^ (Wave * 7919)));
    }
}

void USSSurvivalDirectorComponent::SetBreathing(bool bValue)
{
    bBreathing = bValue;
    AvailableBudget = FMath::Min(AvailableBudget, 1.f);
    if (bValue && Wave == Content(this)->Encounter(ESSEncounterKind::MobileDepot).OfferedWave && !bDepotOffered)
        OfferEncounter(ESSEncounterKind::MobileDepot);
}

int32 USSSurvivalDirectorComponent::GetActiveThreatCount() const
{
    int32 Count = 0;
    for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
        if (!It->IsActorBeingDestroyed() && (It->IsSolidHazard() || It->IsEnemy() || It->IsEnvironmentalField()))
            ++Count;
    return Count;
}

void USSSurvivalDirectorComponent::CleanTrackedActors()
{
    Spawned.RemoveAll([](const TWeakObjectPtr<ASSWorldBody> &Body) { return !Body.IsValid(); });
}

namespace
{
// The owner's direction for the Director: it governs how many bodies it throws, how fast, and how
// closely aligned to the flight path. Authored drift is 40 to 350 cm/s against a 2400 cm/s cruise, so
// a hazard supplied at most about a eighth of the closing speed and was in practice a stationary rock
// the player drove into. These are the dials for that.
TAutoConsoleVariable<float> HazardSpeed(TEXT("ss.HazardSpeed"), 3.f,
                                        TEXT("Multiplier on authored hazard drift speed."));
TAutoConsoleVariable<float> HazardAim(TEXT("ss.HazardAim"), .55f,
                                      TEXT("0 fires along the ship's heading at spawn, 1 leads the ship."));
TAutoConsoleVariable<int32> HazardCount(TEXT("ss.HazardCount"), 40, TEXT("Active hazard and enemy cap."));

/** How fast a hazard may travel, after the dial. Shared so the spawn distance and the velocity cannot
 *  disagree: reaction time is computed from closing speed, and a faster hazard that spawned at the old
 *  distance would arrive inside the reaction budget, which is unfair rather than hard. */
float HazardSpeedScale()
{
    return FMath::Max(0.f, HazardSpeed.GetValueOnGameThread());
}
} // namespace

bool USSSurvivalDirectorComponent::FindSafeSpawn(float Radius, FVector &Location, bool bField) const
{
    ASSShip *Ship = FindShip();
    if (!Ship)
        return false;
    const FVector Forward = Ship->GetActorForwardVector();
    const FVector Right = Ship->GetActorRightVector();
    const FVector Up = Ship->GetActorUpVector();
    // Use closing speed, including a maximum approach drift, rather than distance alone.
    float MaximumDrift = 450.f;
    for (const auto &Hazard : Content(this)->Hazards)
        MaximumDrift = FMath::Max(MaximumDrift, Hazard.DriftSpeedMax);
    MaximumDrift *= HazardSpeedScale();
    const float ClosingSpeed = Ship->GetVelocity().Size() + MaximumDrift;
    const float Lead = FMath::Max(9000.f, ClosingSpeed * MinimumReactionSeconds + Radius + PlayerClearanceRadius);
    for (int32 Attempt = 0; Attempt < 16; ++Attempt)
    {
        const FVector2D Offset(Random.FRandRange(-2600.f, 2600.f), Random.FRandRange(-1700.f, 1700.f));
        if (!bField && FVector2D::Distance(Offset, SafeLane) < Radius + PlayerClearanceRadius + 320.f)
            continue;
        const FVector Candidate = Ship->GetActorLocation() + Forward * (Lead + Random.FRandRange(0.f, 5500.f)) +
                                  Right * Offset.X + Up * Offset.Y;
        if (HasSpatialClearance(this, Candidate, Candidate, Radius, bField))
        {
            Location = Candidate;
            return true;
        }
    }
    return false;
}

ASSWorldBody *USSSurvivalDirectorComponent::SpawnHazard(ESSWorldKind Kind, float Radius)
{
    if (GetActiveThreatCount() >= FMath::Max(1, HazardCount.GetValueOnGameThread()))
        return nullptr;
    const auto Definition = Content(this)->Hazard(Kind);
    Radius = Radius > 0.f ? Radius : Definition.Radius;
    FVector Location;
    const bool bField = Kind == ESSWorldKind::ElectricalStorm || Kind == ESSWorldKind::GravityAnomaly;
    if (!FindSafeSpawn(Radius, Location, bField))
        return nullptr;
    ASSWorldBody *Body = GetWorld()->SpawnActor<ASSWorldBody>(Location, FRotator::ZeroRotator);
    if (!Body)
        return nullptr;
    const float Damage = Definition.DamageBase + Wave * Definition.DamagePerWave;
    Body->Configure(Kind, Radius, Damage, Wave);
    Body->TelegraphSeconds = FMath::Max(MinimumReactionSeconds, Definition.TelegraphSeconds);
    if (ASSShip *Ship = FindShip())
    {
        if (bField)
        {
            // A share of cruise, not of whatever the ship was doing when the field was admitted. Boost is
            // 1.85 of cruise and the climax share is .65, so a field admitted during a boost travelled at 1.2
            // of cruise, could never be reached once the boost ran out, and retired unseen a few seconds later.
            FVector Carried = Ship->GetVelocity();
            if (const USSGameInstance *Instance = Cast<USSGameInstance>(GetWorld()->GetGameInstance()))
                Carried = Carried.GetClampedToMaxSize(FMath::Max(1.f, float(Instance->Session.Stats().speed)));
            Body->SetLinearVelocity(Carried *
                                    (bClimax ? Definition.ClimaxVelocityFraction : Definition.FieldVelocityFraction));
        }
        else
        {
            const float Speed = Random.FRandRange(Definition.DriftSpeedMin,
                                                  FMath::Max(Definition.DriftSpeedMin, Definition.DriftSpeedMax)) *
                                HazardSpeedScale();
            // Firing along the heading the ship happened to hold at spawn means any turn sends the hazard
            // sailing past, which is what made them read as scenery drifting by. Leading the ship instead
            // makes a hazard something to dodge. Partial by default: a field where everything intercepts
            // is not harder, it is unavoidable, and the owner asked for danger rather than for a tax.
            FVector Direction = -Ship->GetActorForwardVector();
            const float Aim = FMath::Clamp(HazardAim.GetValueOnGameThread(), 0.f, 1.f);
            const FVector ToShip = Ship->GetActorLocation() - Location;
            if (Aim > 0.f && Speed > 1.f && !ToShip.IsNearlyZero())
            {
                const float Closing = FMath::Max(1.f, Speed + Ship->GetVelocity().Size());
                const FVector Lead = Ship->GetActorLocation() + Ship->GetVelocity() * (ToShip.Size() / Closing);
                const FVector Intercept = (Lead - Location).GetSafeNormal();
                if (!Intercept.IsNearlyZero())
                    Direction = FMath::Lerp(Direction, Intercept, Aim).GetSafeNormal();
            }
            Body->SetLinearVelocity(Direction * Speed);
        }
    }
    Spawned.Add(Body);
    return Body;
}

ASSEnemy *USSSurvivalDirectorComponent::SpawnEnemy(ESSWorldKind Kind, ASSEncounterBeacon *Objective)
{
    if (GetActiveThreatCount() >= FMath::Max(1, HazardCount.GetValueOnGameThread()))
        return nullptr;
    int32 EnemyCount = 0;
    for (TActorIterator<ASSEnemy> It(GetWorld()); It; ++It)
        ++EnemyCount;
    const auto &DirectorData = Content(this)->DirectorContent;
    const auto Definition = Content(this)->Enemy(Kind);
    if (EnemyCount >=
        (bClimax ? DirectorData.ClimaxEnemyCap : (Wave < 6 ? DirectorData.EarlyEnemyCap : DirectorData.LateEnemyCap)))
        return nullptr;
    FVector Location;
    if (!FindSafeSpawn(Definition.Radius, Location))
        return nullptr;
    if (ASSEnemy *Enemy = GetWorld()->SpawnActor<ASSEnemy>(Location, FRotator::ZeroRotator))
    {
        Enemy->Configure(Kind, Definition.Radius,
                         Definition.CollisionDamageBase + Wave * Definition.CollisionDamagePerWave, Wave);
        Enemy->SetObjectiveOwner(Objective);
        if (ASSShip *Ship = FindShip())
            Enemy->SetLinearVelocity(Ship->GetVelocity());
        Spawned.Add(Enemy);
        return Enemy;
    }
    return nullptr;
}

bool USSSurvivalDirectorComponent::SpawnWreckagePassage()
{
    if (GetActiveThreatCount() + 4 > MaximumActiveThreats)
        return false;
    ASSShip *Ship = FindShip();
    if (!Ship)
        return false;
    const auto Definition = Content(this)->Hazard(ESSWorldKind::Wreckage);
    FVector Centre;
    if (!FindSafeSpawn(350.f, Centre))
        return false;
    // Authored four-piece frame: an unobstructed 1,400 cm aperture with varied orientation.
    const FVector Axes[] = {Ship->GetActorRightVector(), -Ship->GetActorRightVector(), Ship->GetActorUpVector(),
                            -Ship->GetActorUpVector()};
    bool SpawnedAny = false;
    for (int32 Index = 0; Index < 4; ++Index)
    {
        const FVector Position = Centre + Axes[Index] * Definition.PassageHalfSpacing;
        bool bClear = true;
        for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
            if (It->IsSolidHazard() &&
                FVector::DistSquared(Position, It->GetActorLocation()) < FMath::Square(It->GetBodyRadius() + 600.f))
            {
                bClear = false;
                break;
            }
        if (!bClear)
            continue;
        if (ASSWorldBody *Chunk = GetWorld()->SpawnActor<ASSWorldBody>(Position, Ship->GetActorRotation()))
        {
            Chunk->Configure(ESSWorldKind::Wreckage, Index == 0 ? Definition.BreakableChunkRadius : Definition.Radius,
                             Definition.DamageBase + Wave * Definition.DamagePerWave, Wave);
            Chunk->SetLinearVelocity(-Ship->GetActorForwardVector() * Definition.DriftSpeedMin);
            Spawned.Add(Chunk);
            SpawnedAny = true;
        }
    }
    return SpawnedAny;
}

void USSSurvivalDirectorComponent::OfferEncounter(ESSEncounterKind Kind)
{
    ASSShip *Ship = FindShip();
    if (!Ship)
        return;
    const auto Definition = Content(this)->Encounter(Kind);
    const float Lead = FMath::Max(Definition.OfferLeadDistance,
                                  static_cast<float>(Ship->GetVelocity().Size()) * Definition.OfferLeadSeconds);
    const FVector Location = Ship->GetActorLocation() + Ship->GetActorForwardVector() * Lead +
                             Ship->GetActorRightVector() * Definition.OfferLateralOffset;
    if (ASSEncounterBeacon *Beacon = GetWorld()->SpawnActor<ASSEncounterBeacon>(Location, Ship->GetActorRotation()))
    {
        Beacon->ConfigureEncounter(Kind, Wave);
        Spawned.Add(Beacon);
        if (Kind == ESSEncounterKind::MobileDepot)
            bDepotOffered = true;
        if (Kind == ESSEncounterKind::SalvageCache)
            bSalvageOffered = true;
        if (Kind == ESSEncounterKind::DistressCombat)
            bDistressOffered = true;
        if (USSGameInstance *Instance = Cast<USSGameInstance>(GetWorld()->GetGameInstance()))
        {
            Instance->Session.run.depotSeen = bDepotOffered;
            Instance->Session.run.salvageEventSeen = bSalvageOffered;
            Instance->Session.run.distressEventSeen = bDistressOffered;
        }
    }
}

void USSSurvivalDirectorComponent::TickComponent(float DeltaSeconds, ELevelTick TickType,
                                                 FActorComponentTickFunction *ThisTickFunction)
{
    Super::TickComponent(DeltaSeconds, TickType, ThisTickFunction);
    if (!IsActive() || !FindShip())
        return;
    CleanTrackedActors();
    if (FindShip()->IsMoored())
        return; // No new admission or banked pressure during the bounded service stop.
    WaveAge += DeltaSeconds;
    float Modifier = 1.f;
    if (USSGameInstance *Instance = Cast<USSGameInstance>(GetWorld()->GetGameInstance()))
        Modifier = static_cast<float>(Instance->Session.PressureMultiplier());
    const auto *Data = Content(this);
    const auto &DirectorData = Data->DirectorContent;
    const auto Salvage = Data->Encounter(ESSEncounterKind::SalvageCache);
    const auto Distress = Data->Encounter(ESSEncounterKind::DistressCombat);
    const auto Depot = Data->Encounter(ESSEncounterKind::MobileDepot);
    const auto Wreckage = Data->Hazard(ESSWorldKind::Wreckage);
    const auto Storm = Data->Hazard(ESSWorldKind::ElectricalStorm);
    const auto Gravity = Data->Hazard(ESSWorldKind::GravityAnomaly);
    Pressure = bBreathing ? .08f
                          : FMath::Clamp((DirectorData.PressureBase + Wave * DirectorData.PressurePerWave +
                                          (bClimax ? DirectorData.ClimaxPressureBonus : 0.f)) *
                                             Modifier,
                                         .1f, 1.f);
    if (!bSalvageOffered && Wave == Salvage.OfferedWave && WaveAge > Salvage.OfferDelay)
        OfferEncounter(ESSEncounterKind::SalvageCache);
    if (!bDistressOffered && Wave == Distress.OfferedWave && WaveAge > Distress.OfferDelay)
        OfferEncounter(ESSEncounterKind::DistressCombat);
    if (bBreathing)
    {
        if (Wave == Depot.OfferedWave && !bDepotOffered)
            OfferEncounter(ESSEncounterKind::MobileDepot);
        return;
    }
    AvailableBudget = FMath::Min(
        DirectorData.BudgetCapacity,
        AvailableBudget + DeltaSeconds * BaseBudgetPerSecond *
                              (DirectorData.BudgetBaseMultiplier + Wave * DirectorData.BudgetGrowthPerWave) * Modifier);
    SpawnCooldown -= DeltaSeconds;
    if (SpawnCooldown > 0.f || GetActiveThreatCount() >= MaximumActiveThreats)
        return;
    SpawnCooldown = Random.FRandRange(FMath::Max(.1f, DirectorData.SpawnIntervalMin),
                                      FMath::Max(DirectorData.SpawnIntervalMin, DirectorData.SpawnIntervalMax));

    // A turn of a few seconds carries the ship out of the required field's reach and retires it. Every other
    // kind is simply admitted again ahead of the new heading; fields are not drawn during a climax, so this one
    // has to be asked for again or the front is asteroids and enemies for the rest of it.
    if (bClimax && Wave == 10 && bCompoundGravitySpawned && !CompoundGravity.IsValid())
        bCompoundGravitySpawned = false;
    if (bClimax && Wave == 10 && (!bCompoundGravitySpawned || !bCompoundAsteroidSpawned || !bCompoundEnemySpawned))
    {
        // Establish each required component before random composition resumes.
        // Existing capacity, telegraph, safe-lane and budget rules still apply;
        // a blocked admission retries without consuming its cost.
        const ESSWorldKind Required = !bCompoundGravitySpawned    ? ESSWorldKind::GravityAnomaly
                                      : !bCompoundAsteroidSpawned ? ESSWorldKind::MediumAsteroid
                                                                  : ESSWorldKind::Pursuer;
        const bool bEnemy = Required == ESSWorldKind::Pursuer;
        const float Cost =
            FMath::Max(.1f, bEnemy ? Data->Enemy(Required).PressureCost : Data->Hazard(Required).PressureCost);
        if (AvailableBudget >= Cost)
        {
            ASSWorldBody *SpawnedRequired =
                bEnemy ? SpawnEnemy(Required)
                       : SpawnHazard(Required, Required == ESSWorldKind::GravityAnomaly ? Gravity.ClimaxRadius : -1.f);
            if (SpawnedRequired)
            {
                AvailableBudget -= Cost;
                if (Required == ESSWorldKind::GravityAnomaly)
                {
                    bCompoundGravitySpawned = true;
                    CompoundGravity = SpawnedRequired;
                }
                else if (Required == ESSWorldKind::MediumAsteroid)
                    bCompoundAsteroidSpawned = true;
                else
                    bCompoundEnemySpawned = true;
            }
        }
        return;
    }
    const float Roll = Random.FRand();
    if ((bClimax && Wave == 5) || (Wave >= FMath::Min(Data->Enemy(ESSWorldKind::Pursuer).MinimumWave,
                                                      Data->Enemy(ESSWorldKind::Flanker).MinimumWave) &&
                                   Roll < (bClimax ? DirectorData.ClimaxEnemyChance : DirectorData.EnemyChance)))
    {
        ESSWorldKind Selected = ESSWorldKind::Pursuer;
        if (SelectContent(this, {ESSWorldKind::Pursuer, ESSWorldKind::Flanker}, Wave, Random, true, Selected))
        {
            const float Cost = FMath::Max(.1f, Data->Enemy(Selected).PressureCost);
            if (AvailableBudget >= Cost && SpawnEnemy(Selected))
                AvailableBudget -= Cost;
        }
    }
    else if (Wave >= FMath::Min(Storm.MinimumWave, Gravity.MinimumWave) && !bClimax &&
             Roll > 1.f - DirectorData.FieldChance &&
             AvailableBudget >= FMath::Min(Storm.PressureCost, Gravity.PressureCost))
    {
        ESSWorldKind Selected = ESSWorldKind::ElectricalStorm;
        if (SelectContent(this, {ESSWorldKind::ElectricalStorm, ESSWorldKind::GravityAnomaly}, Wave, Random, false,
                          Selected))
        {
            const float Cost = FMath::Max(.1f, Data->Hazard(Selected).PressureCost);
            if (AvailableBudget >= Cost && SpawnHazard(Selected, -1.f))
                AvailableBudget -= Cost;
        }
    }
    else if (Wave >= Wreckage.MinimumWave && Roll > DirectorData.WreckageSelectionStart &&
             Roll < DirectorData.WreckageSelectionStart + Wreckage.SelectionWeight &&
             AvailableBudget >= Wreckage.PressureCost)
    {
        if (SpawnWreckagePassage())
            AvailableBudget -= FMath::Max(.1f, Wreckage.PressureCost);
    }
    else if (AvailableBudget >= 1.f)
    {
        ESSWorldKind Selected = ESSWorldKind::SmallAsteroid;
        if (SelectContent(this,
                          {ESSWorldKind::MassiveAsteroid, ESSWorldKind::MediumAsteroid, ESSWorldKind::SmallAsteroid},
                          Wave, Random, false, Selected))
        {
            const float Cost = FMath::Max(.1f, Data->Hazard(Selected).PressureCost);
            if (AvailableBudget >= Cost && SpawnHazard(Selected, -1.f))
                AvailableBudget -= Cost;
        }
    }
}

void USSSurvivalDirectorComponent::ResetEncounter()
{
    SetActive(false);
    // Called only for station/death transitions. Ordinary Configure never clears the universe.
    for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
        It->Destroy();
    Spawned.Empty();
    AvailableBudget = 0.f;
    Pressure = 0.f;
    WaveAge = 0.f;
}
