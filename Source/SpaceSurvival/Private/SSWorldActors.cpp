#include "SSWorldActors.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSShip.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace
{
constexpr float ShipRadius = 120.f;

ASSGameMode* GameMode(const UObject* Context)
{
    return Cast<ASSGameMode>(UGameplayStatics::GetGameMode(Context));
}

UStaticMesh* Mesh(const TCHAR* Name, const TCHAR* Fallback = TEXT("/Engine/BasicShapes/Sphere.Sphere"))
{
    const FString Path = FString::Printf(TEXT("/Game/SpaceSurvival/Meshes/%s.%s"), Name, Name);
    if (UStaticMesh* Authored = LoadObject<UStaticMesh>(nullptr, *Path)) return Authored;
    return LoadObject<UStaticMesh>(nullptr, Fallback);
}

FLinearColor BodyColor(ESSWorldKind Kind)
{
    switch (Kind)
    {
    case ESSWorldKind::ElectricalStorm: return FLinearColor(.24f, .55f, 1.f);
    case ESSWorldKind::GravityAnomaly: return FLinearColor(.6f, .18f, 1.f);
    case ESSWorldKind::Pursuer: return FLinearColor(1.f, .16f, .08f);
    case ESSWorldKind::Flanker: return FLinearColor(1.f, .52f, .08f);
    case ESSWorldKind::Wreckage: return FLinearColor(.22f, .36f, .43f);
    case ESSWorldKind::Depot: return FLinearColor(.15f, 1.f, .55f);
    case ESSWorldKind::Event: return FLinearColor(.3f, .85f, 1.f);
    default: return FLinearColor(.35f, .26f, .2f);
    }
}

void Announce(const UObject* Context, const FString& Text)
{
    if (ASSGameMode* Mode = GameMode(Context)) Mode->Announce(Text);
}

bool HasThreatCapacity(const UObject* Context, int32 Additional = 1)
{
    ASSGameMode* Mode = GameMode(Context);
    return !Mode || !Mode->Director || Mode->Director->GetActiveThreatCount() + Additional <= Mode->Director->MaximumActiveThreats;
}
}

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
    Health = Kind == ESSWorldKind::MediumAsteroid ? 90.f : (IsEnemy() ? 55.f : 24.f);
    if (Kind == ESSWorldKind::Wreckage) Health = BodyRadius > 320.f ? 100000.f : 65.f;
    bPersistentAcrossWaves = IsEnvironmentalField();
    Collision->SetSphereRadius(BodyRadius);
    Collision->SetCollisionResponseToChannel(ECC_Visibility, IsEnvironmentalField() ? ECR_Ignore : ECR_Block);
    UpdateVisual();
}

void ASSWorldBody::UpdateVisual()
{
    const TCHAR* Asset = TEXT("SM_AsteroidSmall");
    switch (Kind)
    {
    case ESSWorldKind::MediumAsteroid: Asset = TEXT("SM_AsteroidMedium"); break;
    case ESSWorldKind::MassiveAsteroid: Asset = TEXT("SM_AsteroidMassive"); break;
    case ESSWorldKind::Wreckage: Asset = TEXT("SM_Wreckage"); break;
    case ESSWorldKind::ElectricalStorm: Asset = TEXT("SM_StormRing"); break;
    case ESSWorldKind::GravityAnomaly: Asset = TEXT("SM_GravityRing"); break;
    case ESSWorldKind::Pursuer: Asset = TEXT("SM_Pursuer"); break;
    case ESSWorldKind::Flanker: Asset = TEXT("SM_Flanker"); break;
    case ESSWorldKind::Depot: Asset = TEXT("SM_MobileDepot"); break;
    case ESSWorldKind::Event: Asset = TEXT("SM_EventBeacon"); break;
    case ESSWorldKind::Projectile: Asset = TEXT("SM_Projectile"); break;
    case ESSWorldKind::Pickup: Asset = TEXT("SM_PickupCredit"); break;
    default: break;
    }
    Visual->SetStaticMesh(Mesh(Asset));
    // Match collision to the loaded mesh rather than assuming authoring units.
    // Missing authoring remains an explicit fallback, not presentation verification.
    const float MeshExtent = Visual->GetStaticMesh() ? Visual->GetStaticMesh()->GetBounds().BoxExtent.GetMax() : 50.f;
    Visual->SetRelativeScale3D(FVector(BodyRadius / FMath::Max(1.f, MeshExtent)));
    const TCHAR* MaterialPath = IsEnvironmentalField() || Kind == ESSWorldKind::Event || Kind == ESSWorldKind::Depot || Kind == ESSWorldKind::Projectile || Kind == ESSWorldKind::Pickup
        ? TEXT("/Game/SpaceSurvival/Materials/M_Emissive.M_Emissive")
        : TEXT("/Game/SpaceSurvival/Materials/M_Hazard.M_Hazard");
    UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, MaterialPath);
    if (!Material) Material = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    if (Material)
    {
        DynamicMaterial = UMaterialInstanceDynamic::Create(Material, this);
        DynamicMaterial->SetVectorParameterValue(TEXT("Tint"), BodyColor(Kind));
        DynamicMaterial->SetVectorParameterValue(TEXT("Color"), FLinearColor::White);
        DynamicMaterial->SetScalarParameterValue(TEXT("Emission"), IsEnvironmentalField() ? .25f : 1.f);
        Visual->SetMaterial(0, DynamicMaterial);
    }
    Visual->SetCastShadow(!IsEnvironmentalField());
}

ASSShip* ASSWorldBody::FindShip() const
{
    return Cast<ASSShip>(UGameplayStatics::GetPlayerPawn(this, 0));
}

bool ASSWorldBody::IsEnemy() const { return Kind == ESSWorldKind::Pursuer || Kind == ESSWorldKind::Flanker; }
bool ASSWorldBody::IsEnvironmentalField() const { return Kind == ESSWorldKind::ElectricalStorm || Kind == ESSWorldKind::GravityAnomaly; }
bool ASSWorldBody::IsSolidHazard() const
{
    return Kind == ESSWorldKind::SmallAsteroid || Kind == ESSWorldKind::MediumAsteroid || Kind == ESSWorldKind::MassiveAsteroid || Kind == ESSWorldKind::Wreckage;
}
bool ASSWorldBody::IsWeaponTarget() const
{
    return IsEnemy() || Kind == ESSWorldKind::SmallAsteroid || Kind == ESSWorldKind::MediumAsteroid || (Kind == ESSWorldKind::Wreckage && BodyRadius <= 320.f);
}

FString ASSWorldBody::GetLabel() const
{
    switch (Kind)
    {
    case ESSWorldKind::SmallAsteroid: return TEXT("SMALL DEBRIS");
    case ESSWorldKind::MediumAsteroid: return TEXT("FRACTURABLE ASTEROID");
    case ESSWorldKind::MassiveAsteroid: return TEXT("MASSIVE BODY · EVADE");
    case ESSWorldKind::Wreckage: return BodyRadius > 320.f ? TEXT("STRUCTURAL WRECKAGE · EVADE") : TEXT("BREAKABLE WRECKAGE");
    case ESSWorldKind::ElectricalStorm: return TEXT("ELECTRICAL STORM");
    case ESSWorldKind::GravityAnomaly: return TEXT("GRAVITY ANOMALY");
    case ESSWorldKind::Pursuer: return TEXT("PURSUER");
    case ESSWorldKind::Flanker: return TEXT("FLANKER");
    case ESSWorldKind::Depot: return TEXT("MOBILE DEPOT · INTERACT FOR DEALS");
    case ESSWorldKind::Event: return TEXT("OPTIONAL SIGNAL · INTERACT TO ACCEPT");
    case ESSWorldKind::Pickup: return TEXT("PICKUP");
    default: return TEXT("");
    }
}

void ASSWorldBody::ApplyWorldForce(FVector Acceleration, float DeltaSeconds)
{
    if (Kind == ESSWorldKind::MassiveAsteroid || IsEnvironmentalField() || Kind == ESSWorldKind::Event || Kind == ESSWorldKind::Depot) return;
    LinearVelocity += Acceleration.GetClampedToMaxSize(1100.f) * DeltaSeconds;
}

void ASSWorldBody::ApplyWorldOffset(const FVector& InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    if (bHasPreviousShipPosition) PreviousShipPosition += InOffset;
}

void ASSWorldBody::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bDefeated) return;
    const FVector PreviousBodyPosition = GetActorLocation();
    Age += DeltaSeconds;
    ShipContactRemaining = FMath::Max(0.f, ShipContactRemaining - DeltaSeconds);
    AddActorWorldOffset(LinearVelocity * DeltaSeconds, false);
    if (IsSolidHazard()) Visual->AddLocalRotation(FRotator(2.f, 4.f, 1.5f) * DeltaSeconds);
    ASSShip* Ship = FindShip();
    if (Ship)
    {
        const FVector Offset = Ship->GetActorLocation() - GetActorLocation();
        const float Distance = Offset.Size();
        if (IsSolidHazard() || IsEnemy())
        {
            const FVector PreviousRelative = bHasPreviousShipPosition ? PreviousShipPosition - PreviousBodyPosition : Offset;
            const FVector RelativePath = Offset - PreviousRelative;
            const float ClosestTime = RelativePath.IsNearlyZero() ? 1.f : static_cast<float>(FMath::Clamp(-FVector::DotProduct(PreviousRelative, RelativePath) / RelativePath.SizeSquared(), 0.0, 1.0));
            const float SweptDistance = (PreviousRelative + RelativePath * ClosestTime).Size();
            if (SweptDistance < BodyRadius + ShipRadius && ShipContactRemaining <= 0.f)
            {
                Ship->ReceiveDamage(CollisionDamage, SS::DamageType::Kinetic);
                Ship->AddExternalForce(Offset.GetSafeNormal() * FMath::Min(1400.f, CollisionDamage * 20.f));
                ShipContactRemaining = 1.1f;
            }
        }
        else if (IsEnvironmentalField())
        {
            const float WarningDistance = BodyRadius + Ship->GetVelocity().Size() * TelegraphSeconds;
            if (!bWarningIssued && Distance < WarningDistance)
            {
                bWarningIssued = true;
                Announce(this, Kind == ESSWorldKind::ElectricalStorm ? TEXT("ELECTRICAL STORM · Pulsing rings warn before discharge") : TEXT("GRAVITY ANOMALY · Counter the pull; boost across its edge"));
            }
            const bool bReady = Age >= TelegraphSeconds;
            if (DynamicMaterial) DynamicMaterial->SetScalarParameterValue(TEXT("Emission"), bReady ? 1.1f + .3f * FMath::Sin(Age * 4.f) : .25f + Age / FMath::Max(1.f, TelegraphSeconds) * .4f);
            if (Kind == ESSWorldKind::ElectricalStorm)
            {
                FieldPulseRemaining -= DeltaSeconds;
                if (bReady && FieldPulseRemaining <= 0.f)
                {
                    FieldPulseRemaining = 1.8f;
                    if (Distance < BodyRadius) Ship->ReceiveDamage(CollisionDamage, SS::DamageType::Electrical);
                }
            }
            else if (bReady)
            {
                if (Distance < BodyRadius)
                {
                    // Bounded force; no teleport, control lock or singularity at the centre.
                    const float Strength = GravityAcceleration * FMath::Clamp(1.f - Distance / BodyRadius, .15f, 1.f);
                    Ship->AddExternalForce(-Offset.GetSafeNormal() * Strength);
                }
                for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
                {
                    ASSWorldBody* Other = *It;
                    if (Other == this || (!Other->IsSolidHazard() && !Other->IsEnemy())) continue;
                    const FVector ToCentre = GetActorLocation() - Other->GetActorLocation();
                    const float Range = ToCentre.Size();
                    if (Range < BodyRadius) Other->ApplyWorldForce(ToCentre.GetSafeNormal() * GravityAcceleration * .45f * (1.f - Range / BodyRadius), DeltaSeconds);
                }
            }
        }
        // Retain hazards across wave boundaries, retire only beyond the playable vicinity.
        PreviousShipPosition = Ship->GetActorLocation();
        bHasPreviousShipPosition = true;
        if (FVector::DotProduct(GetActorLocation() - Ship->GetActorLocation(), Ship->GetActorForwardVector()) < -16000.f) Destroy();
    }
    if (LifetimeSeconds > 0.f && Age > LifetimeSeconds) Destroy();
}

void ASSWorldBody::ReceiveWeaponHit(float Damage)
{
    if (!IsWeaponTarget() || bDefeated || !FMath::IsFinite(Damage) || Damage <= 0.f) return;
    Health -= Damage;
    if (DynamicMaterial) DynamicMaterial->SetScalarParameterValue(TEXT("Emission"), 1.8f);
    if (Health <= 0.f)
    {
        bDefeated = true;
        OnDefeated();
        Destroy();
    }
}

void ASSWorldBody::OnDefeated()
{
    if (Kind == ESSWorldKind::MediumAsteroid)
    {
        // Fragment count is bounded. Fragments preserve collision and can worsen the line.
        for (int32 Index = 0; Index < 3; ++Index)
        {
            if (!HasThreatCapacity(this)) break;
            const FVector Direction = LocalRandom.VRand();
            if (ASSWorldBody* Fragment = GetWorld()->SpawnActor<ASSWorldBody>(GetActorLocation() + Direction * (BodyRadius + 80.f), FRotator::ZeroRotator))
            {
                Fragment->Configure(ESSWorldKind::SmallAsteroid, 60.f, CollisionDamage * .45f, Wave);
                Fragment->SetLinearVelocity(LinearVelocity + Direction * 210.f);
                Fragment->LifetimeSeconds = 13.f;
            }
        }
    }
    if (Kind == ESSWorldKind::MediumAsteroid || LocalRandom.FRand() < .3f)
    {
        if (ASSPickup* Pickup = GetWorld()->SpawnActor<ASSPickup>(GetActorLocation(), FRotator::ZeroRotator))
        {
            const float Roll = LocalRandom.FRand();
            const int32 PickupKind = Roll < .05f ? 2 : (Roll < .20f ? 1 : (Roll < .26f ? 3 : 0));
            Pickup->ConfigurePickup(PickupKind, PickupKind == 0 ? 25.f : (PickupKind == 3 ? 10.f : 20.f));
            Pickup->SetLinearVelocity(LinearVelocity * .3f);
        }
    }
}

ASSEnemy::ASSEnemy()
{
    Kind = ESSWorldKind::Pursuer;
    LifetimeSeconds = 75.f;
}

void ASSEnemy::SetObjectiveOwner(ASSEncounterBeacon* InOwner) { ObjectiveOwner = InOwner; }

void ASSEnemy::Tick(float DeltaSeconds)
{
    ASSShip* Ship = FindShip();
    if (Ship && !bDefeated)
    {
        SteeringPhase += DeltaSeconds * (.65f + Wave * .055f);
        const FVector Forward = Ship->GetActorForwardVector();
        const FVector Right = Ship->GetActorRightVector();
        const FVector Up = Ship->GetActorUpVector();
        FVector Desired = Ship->GetActorLocation() + Forward * (Kind == ESSWorldKind::Pursuer ? 1700.f : 2100.f);
        if (Kind == ESSWorldKind::Flanker) Desired += Right * FMath::Sin(SteeringPhase) * 1900.f + Up * FMath::Cos(SteeringPhase * .65f) * 850.f;
        else Desired += Right * FMath::Sin(SteeringPhase) * 420.f;
        const float Response = 1.2f + Wave * .1f;
        const FVector Catchup = ((Desired - GetActorLocation()) * Response).GetClampedToMaxSize(2800.f + Wave * 140.f);
        LinearVelocity = FMath::VInterpTo(LinearVelocity, Ship->GetVelocity() + Catchup, DeltaSeconds, 2.5f);
        SetActorRotation((Ship->GetActorLocation() - GetActorLocation()).Rotation());
        ShotCooldown -= DeltaSeconds;
        if (ShotCharge > 0.f)
        {
            ShotCharge -= DeltaSeconds;
            if (DynamicMaterial) DynamicMaterial->SetScalarParameterValue(TEXT("Emission"), 2.8f);
            if (ShotCharge <= 0.f)
            {
                if (ASSProjectile* Shot = GetWorld()->SpawnActor<ASSProjectile>(GetActorLocation() + ShotDirection * (BodyRadius + 30.f), ShotDirection.Rotation()))
                {
                    Shot->Launch(ShotDirection, 5600.f + Wave * 170.f, 8.f + Wave * 1.4f, false, this);
                }
                ShotCooldown = FMath::Max(1.5f, 3.6f - Wave * .13f);
            }
        }
        else if (ShotCooldown <= 0.f && FVector::DistSquared(GetActorLocation(), Ship->GetActorLocation()) < FMath::Square(8000.f))
        {
            // Aim is committed before discharge. A deliberate dodge can invalidate it.
            const FVector Predicted = Ship->GetActorLocation() + Ship->GetVelocity() * .2f;
            const float Error = FMath::Max(35.f, 200.f - Wave * 12.f);
            ShotDirection = (Predicted + LocalRandom.VRand() * Error - GetActorLocation()).GetSafeNormal();
            ShotCharge = .9f;
        }
        else if (DynamicMaterial) DynamicMaterial->SetScalarParameterValue(TEXT("Emission"), 1.f);

        // Enemies share the environment; they neither phase through nor ignore asteroids.
        for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
        {
            ASSWorldBody* Obstacle = *It;
            if (Obstacle == this || !Obstacle->IsSolidHazard()) continue;
            const FVector Separation = GetActorLocation() - Obstacle->GetActorLocation();
            const float CombinedRadius = BodyRadius + Obstacle->GetBodyRadius();
            if (Separation.SizeSquared() < FMath::Square(CombinedRadius + 500.f))
                LinearVelocity += Separation.GetSafeNormal() * 1000.f * DeltaSeconds;
            if (Separation.SizeSquared() < FMath::Square(CombinedRadius))
            {
                Health -= 70.f * DeltaSeconds;
                if (Health <= 0.f)
                {
                    bDefeated = true;
                    if (ObjectiveOwner.IsValid()) ObjectiveOwner->RegisterObjectiveProgress();
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
    if (ASSGameMode* Mode = GameMode(this)) Mode->NotifyEnemyKilled();
    if (ObjectiveOwner.IsValid()) ObjectiveOwner->RegisterObjectiveProgress();
    // Credits from a kill are awarded once by the domain; physical pickups are extra risk income.
    if (LocalRandom.FRand() < .22f)
        if (ASSPickup* Pickup = GetWorld()->SpawnActor<ASSPickup>(GetActorLocation(), FRotator::ZeroRotator)) Pickup->ConfigurePickup(0, 15.f);
}

ASSProjectile::ASSProjectile()
{
    Kind = ESSWorldKind::Projectile;
    BodyRadius = 16.f;
    LifetimeSeconds = 6.f;
}

void ASSProjectile::Launch(FVector Direction, float Speed, float Damage, bool bFromPlayer, AActor* Source)
{
    Configure(ESSWorldKind::Projectile, bFromPlayer ? 28.f : 17.f, Damage);
    bPlayerShot = bFromPlayer;
    SourceActor = Source;
    LinearVelocity = Direction.GetSafeNormal() * Speed;
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    if (DynamicMaterial) DynamicMaterial->SetVectorParameterValue(TEXT("Tint"), bPlayerShot ? FLinearColor(.3f, 1.f, 1.f) : FLinearColor(1.f, .2f, .05f));
}

void ASSProjectile::Tick(float DeltaSeconds)
{
    Age += DeltaSeconds;
    const FVector Start = GetActorLocation();
    const FVector End = Start + LinearVelocity * DeltaSeconds;
    FCollisionObjectQueryParams Objects;
    Objects.AddObjectTypesToQuery(ECC_WorldDynamic);
    Objects.AddObjectTypesToQuery(ECC_WorldStatic);
    Objects.AddObjectTypesToQuery(ECC_Pawn);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SpaceSurvivalProjectile), false, this);
    if (SourceActor.IsValid()) Query.AddIgnoredActor(SourceActor.Get());
    if (bPlayerShot) if (ASSShip* Ship = FindShip()) Query.AddIgnoredActor(Ship);
    TArray<FHitResult> Hits;
    GetWorld()->SweepMultiByObjectType(Hits, Start, End, FQuat::Identity, Objects, FCollisionShape::MakeSphere(BodyRadius), Query);
    Hits.Sort([](const FHitResult& A, const FHitResult& B) { return A.Time < B.Time; });
    for (const FHitResult& Hit : Hits)
    {
        if (ASSWorldBody* Body = Cast<ASSWorldBody>(Hit.GetActor()))
        {
            if (!Body->IsSolidHazard() && !Body->IsEnemy()) continue;
            if (bPlayerShot || Body->IsSolidHazard()) Body->ReceiveWeaponHit(CollisionDamage);
            Destroy();
            return;
        }
        if (ASSShip* Ship = Cast<ASSShip>(Hit.GetActor()))
        {
            if (!bPlayerShot) Ship->ReceiveDamage(CollisionDamage, SS::DamageType::Energy);
            Destroy();
            return;
        }
        if (Hit.bBlockingHit) { Destroy(); return; }
    }
    SetActorLocation(End);
    if (Age > LifetimeSeconds) Destroy();
}

void ASSProjectile::ReceiveWeaponHit(float Damage) { if (Damage > 0.f) Destroy(); }

ASSWormholePassage::ASSWormholePassage()
{
    Kind = ESSWorldKind::Event;
    LifetimeSeconds = 0.f;
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    for (int32 Index = 0; Index < 5; ++Index)
    {
        UStaticMeshComponent* Ring = CreateDefaultSubobject<UStaticMeshComponent>(*FString::Printf(TEXT("PassageRing%d"), Index));
        Ring->SetupAttachment(RootComponent);
        Ring->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        PassageRings.Add(Ring);
    }
}

void ASSWormholePassage::BeginPassage(ASSShip* Ship, float Duration)
{
    if (!Ship) { Destroy(); return; }
    PassageShip = Ship;
    PassageDuration = FMath::Max(1.f, Duration);
    PassageElapsed = 0.f;
    PassageForward = Ship->GetActorForwardVector();
    EntryPoint = Ship->GetActorLocation();
    CourseLength = FMath::Max(10000.f, static_cast<float>(Ship->GetVelocity().Size()) * PassageDuration * 1.08f);
    SetActorLocation(EntryPoint + PassageForward * 2500.f);
    SetActorRotation(PassageForward.Rotation());
    UStaticMesh* RingMesh = Mesh(TEXT("SM_GravityRing"));
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
        UStaticMeshComponent* Ring = PassageRings[Index];
        Ring->SetStaticMesh(RingMesh);
        const float Alpha = float(Index + 1) / float(PassageRings.Num());
        Ring->SetRelativeLocation(FVector(CourseLength * Alpha, 0.f, 0.f));
        Ring->SetRelativeScale3D(FVector(FMath::Lerp(1700.f, 2300.f, Alpha) * UnitScale));
        if (DynamicMaterial) Ring->SetMaterial(0, DynamicMaterial);
        Ring->SetCastShadow(false);
    }
}

void ASSWormholePassage::Tick(float DeltaSeconds)
{
    // Deliberately bypass the environmental-field tick: this sequence never deals
    // damage, spawns a fifth hazard family, teleports, or advances the run state.
    PassageElapsed += DeltaSeconds;
    if (!PassageShip.IsValid()) { Destroy(); return; }
    ASSShip* Ship = PassageShip.Get();
    const float Alpha = FMath::Clamp(PassageElapsed / PassageDuration, 0.f, 1.f);
    const FVector Relative = Ship->GetActorLocation() - EntryPoint;
    const FVector Lateral = Relative - PassageForward * FVector::DotProduct(Relative, PassageForward);
    const FVector Centring = -Lateral.GetClampedToMaxSize(2000.f) * (.12f + .22f * Alpha);
    Ship->AddExternalForce(PassageForward * (600.f + 1600.f * Alpha) + Centring);
    Visual->AddLocalRotation(FRotator(0.f, 0.f, 40.f * DeltaSeconds));
    for (int32 Index = 0; Index < PassageRings.Num(); ++Index)
        PassageRings[Index]->AddLocalRotation(FRotator(0.f, 0.f, (Index % 2 ? -1.f : 1.f) * (35.f + 20.f * Alpha) * DeltaSeconds));
    if (DynamicMaterial) DynamicMaterial->SetScalarParameterValue(TEXT("Emission"), 1.8f + Alpha * 2.f + .3f * FMath::Sin(PassageElapsed * 8.f));
    if (PassageElapsed >= PassageDuration) Destroy();
}

void ASSWormholePassage::ApplyWorldOffset(const FVector& InOffset, bool bWorldShift)
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

void ASSPickup::ConfigurePickup(int32 InKind, float InAmount, ASSEncounterBeacon* Objective)
{
    Configure(ESSWorldKind::Pickup, 60.f, 0.f);
    PickupKind = FMath::Clamp(InKind, 0, 3);
    Amount = FMath::Max(0.f, InAmount);
    ObjectiveOwner = Objective;
    const TCHAR* Assets[] = {TEXT("SM_PickupCredit"), TEXT("SM_PickupRepair"), TEXT("SM_PickupShield"), TEXT("SM_PickupBuff")};
    const TCHAR* Fallbacks[] = {TEXT("/Engine/BasicShapes/Cylinder.Cylinder"), TEXT("/Engine/BasicShapes/Cube.Cube"), TEXT("/Engine/BasicShapes/Sphere.Sphere"), TEXT("/Engine/BasicShapes/Cone.Cone")};
    Visual->SetStaticMesh(Mesh(Assets[PickupKind], Fallbacks[PickupKind]));
    const float MeshExtent = Visual->GetStaticMesh() ? Visual->GetStaticMesh()->GetBounds().BoxExtent.GetMax() : 50.f;
    Visual->SetRelativeScale3D(FVector(BodyRadius / FMath::Max(1.f, MeshExtent)));
    const FLinearColor Colors[] = {FLinearColor(1.f, .75f, .1f), FLinearColor(.2f, 1.f, .4f), FLinearColor(.2f, .6f, 1.f), FLinearColor(1.f, .35f, .9f)};
    if (DynamicMaterial) DynamicMaterial->SetVectorParameterValue(TEXT("Tint"), Colors[PickupKind]);
    Collision->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
}

FString ASSPickup::GetLabel() const
{
    if (ObjectiveOwner.IsValid()) return TEXT("SALVAGE CACHE · COLLECT");
    const TCHAR* Labels[] = {TEXT("CREDITS"), TEXT("HULL REPAIR"), TEXT("SHIELD CHARGE"), TEXT("WEAPON OVERCHARGE")};
    return Labels[FMath::Clamp(PickupKind, 0, 3)];
}

void ASSPickup::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    Visual->AddLocalRotation(FRotator(0.f, 70.f, 20.f) * DeltaSeconds);
    if (ASSShip* Ship = FindShip())
    {
        const FVector ToShip = Ship->GetActorLocation() - GetActorLocation();
        // A short acquisition radius rewards steering toward an item without auto-collecting a lane.
        if (ToShip.SizeSquared() < FMath::Square(450.f)) AddActorWorldOffset(ToShip.GetSafeNormal() * 800.f * DeltaSeconds);
        if (!bCollected && ToShip.SizeSquared() < FMath::Square(ShipRadius + 110.f))
        {
            bCollected = true;
            if (ASSGameMode* Mode = GameMode(this)) Mode->NotifyPickup(PickupKind, Amount);
            if (ObjectiveOwner.IsValid()) ObjectiveOwner->RegisterObjectiveProgress();
            Destroy();
        }
    }
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
    Configure(IsDepot() ? ESSWorldKind::Depot : ESSWorldKind::Event, IsDepot() ? 420.f : 140.f, 0.f, InWave);
    Collision->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
    Offers = {0, 1, 2, 3, 4};
    FRandomStream OfferRandom(GetUniqueID() ^ InWave * 101);
    for (int32 Index = Offers.Num() - 1; Index > 0; --Index) Offers.Swap(Index, OfferRandom.RandRange(0, Index));
    Offers.SetNum(3);
    Discount = OfferRandom.RandRange(0, 1) ? .75f : .85f;
}

bool ASSEncounterBeacon::IsPlayerInRange() const
{
    const ASSShip* Ship = FindShip();
    return Ship && FVector::DistSquared(Ship->GetActorLocation(), GetActorLocation()) <= FMath::Square(InteractionRadius);
}

FString ASSEncounterBeacon::GetEncounterLabel() const
{
    if (IsDepot()) return FString::Printf(TEXT("MOBILE DEPOT · %d%% OFF · THREE SYSTEM DEALS"), FMath::RoundToInt((1.f - Discount) * 100.f));
    const TCHAR* Name = EncounterKind == ESSEncounterKind::SalvageCache ? TEXT("SALVAGE CACHE") : TEXT("DISTRESS / COMBAT");
    if (bResolved) return FString::Printf(TEXT("%s · RESOLVED"), Name);
    if (bAccepted) return FString::Printf(TEXT("%s · %d OBJECTIVES REMAIN"), Name, ObjectiveRemaining);
    return FString::Printf(TEXT("%s · OPTIONAL · INTERACT TO ACCEPT"), Name);
}

bool ASSEncounterBeacon::TryAccept()
{
    if (bResolved || !IsPlayerInRange()) return false;
    if (IsDepot()) return true; // The UI presents offers; Session owns any actual purchase.
    if (bAccepted) return false;
    if (USSGameInstance* Instance = GetGameInstance<USSGameInstance>())
    {
        if (Instance->Session.run.pendingReward)
        { Announce(this,TEXT("Claim your secured reward before accepting another signal.")); return false; }
    }
    for (TActorIterator<ASSEncounterBeacon> It(GetWorld()); It; ++It)
        if (*It != this && It->IsAccepted() && !It->IsResolved())
        { Announce(this,TEXT("Resolve the active optional signal first.")); return false; }
    ASSShip* Ship = FindShip();
    if (!Ship) return false;
    if (!HasThreatCapacity(this, EncounterKind == ESSEncounterKind::SalvageCache ? 6 : 2))
    {
        Announce(this, TEXT("SIGNAL ON HOLD · Clear nearby threats before accepting"));
        return false;
    }
    bAccepted = true;
    ObjectiveRemaining = EncounterKind == ESSEncounterKind::SalvageCache ? 3 : 2;
    ObjectiveSeconds = EncounterKind == ESSEncounterKind::SalvageCache ? 26.f : 38.f;
    if (USSGameInstance* Instance = GetGameInstance<USSGameInstance>())
    {
        if (EncounterKind == ESSEncounterKind::SalvageCache) Instance->Session.run.salvageEventAccepted = true;
        else Instance->Session.run.distressEventAccepted = true;
    }
    const FVector Forward = Ship->GetActorForwardVector();
    const FVector Right = Ship->GetActorRightVector();
    const FVector Up = Ship->GetActorUpVector();
    const FVector Origin = Ship->GetActorLocation();
    const float Lead = FMath::Max(8000.f, static_cast<float>(Ship->GetVelocity().Size()) * 3.5f);
    if (EncounterKind == ESSEncounterKind::SalvageCache)
    {
        Announce(this, TEXT("SALVAGE ACCEPTED · Collect three marked caches through the wreckage"));
        for (int32 Index = 0; Index < 3; ++Index)
        {
            const FVector Centre = Origin + Forward * (Lead + Index * 3600.f) + Right * (Index == 1 ? -650.f : 650.f);
            if (ASSPickup* Cache = GetWorld()->SpawnActor<ASSPickup>(Centre, FRotator::ZeroRotator))
            {
                Cache->ConfigurePickup(0, 30.f, this);
                Cache->LifetimeSeconds = 35.f;
            }
            for (int32 Side = -1; Side <= 1; Side += 2)
                if (ASSWorldBody* Debris = GetWorld()->SpawnActor<ASSWorldBody>(Centre + Right * Side * 1100.f + Up * 100.f, FRotator::ZeroRotator))
                    Debris->Configure(ESSWorldKind::Wreckage, 300.f, 24.f + Wave * 2.f, Wave);
        }
    }
    else
    {
        Announce(this, TEXT("DISTRESS ACCEPTED · Defeat both attackers; reward choice follows success"));
        for (int32 Index = 0; Index < 2; ++Index)
            if (ASSEnemy* Enemy = GetWorld()->SpawnActor<ASSEnemy>(Origin + Forward * Lead + Right * (Index == 0 ? -1100.f : 1100.f), FRotator::ZeroRotator))
            {
                Enemy->Configure(Index == 0 ? ESSWorldKind::Pursuer : ESSWorldKind::Flanker, 150.f, 25.f, Wave);
                Enemy->SetObjectiveOwner(this);
                Enemy->SetLinearVelocity(Ship->GetVelocity());
            }
    }
    return true;
}

void ASSEncounterBeacon::RegisterObjectiveProgress()
{
    if (!bAccepted || bResolved || IsDepot()) return;
    ObjectiveRemaining = FMath::Max(0, ObjectiveRemaining - 1);
    if (ObjectiveRemaining == 0)
    {
        bResolved = true;
        if (ASSGameMode* Mode = GameMode(this)) Mode->NotifyEventCompleted(EncounterKind == ESSEncounterKind::DistressCombat);
    }
}

void ASSEncounterBeacon::FailObjective()
{
    if (bResolved || IsDepot()) return;
    bResolved = true;
    Announce(this, TEXT("OPTIONAL SIGNAL LOST · No reward; no credit penalty"));
}

void ASSEncounterBeacon::Tick(float DeltaSeconds)
{
    // Track alongside the ship once reached, allowing a deliberate moving interaction.
    // No pause, invulnerability, free repairs or full station service is granted.
    if (ASSShip* Ship = FindShip())
    {
        if (bAccepted || IsPlayerInRange()) LinearVelocity = Ship->GetVelocity();
        if (!bAnnounced)
        {
            bAnnounced = true;
            Announce(this, GetEncounterLabel());
        }
    }
    Super::Tick(DeltaSeconds);
    Visual->AddLocalRotation(FRotator(0.f, 15.f, 0.f) * DeltaSeconds);
    if (bAccepted && !bResolved && !IsDepot())
    {
        ObjectiveSeconds -= DeltaSeconds;
        if (ObjectiveSeconds <= 0.f) FailObjective();
    }
}

USSSurvivalDirectorComponent::USSSurvivalDirectorComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    bAutoActivate = false;
    Random.Initialize(0x53A9);
}

ASSShip* USSSurvivalDirectorComponent::FindShip() const { return Cast<ASSShip>(UGameplayStatics::GetPlayerPawn(this, 0)); }

void USSSurvivalDirectorComponent::Configure(int32 InWave, bool bInClimax)
{
    Wave = FMath::Clamp(InWave, 1, 10);
    bClimax = bInClimax;
    bBreathing = false;
    WaveAge = 0.f;
    AvailableBudget = 1.f;
    SpawnCooldown = .75f;
    bCompoundGravitySpawned = false;
    SafeLane = FVector2D(Random.RandRange(-1, 1) * 950.f, Random.RandRange(-1, 1) * 750.f);
    if (USSGameInstance* Instance = Cast<USSGameInstance>(GetWorld()->GetGameInstance()))
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
    if (bValue && Wave == 3 && !bDepotOffered) OfferEncounter(ESSEncounterKind::MobileDepot);
}

int32 USSSurvivalDirectorComponent::GetActiveThreatCount() const
{
    int32 Count = 0;
    for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
        if (!It->IsActorBeingDestroyed() && (It->IsSolidHazard() || It->IsEnemy() || It->IsEnvironmentalField())) ++Count;
    return Count;
}

void USSSurvivalDirectorComponent::CleanTrackedActors()
{
    Spawned.RemoveAll([](const TWeakObjectPtr<ASSWorldBody>& Body) { return !Body.IsValid(); });
}

bool USSSurvivalDirectorComponent::FindSafeSpawn(float Radius, FVector& Location, bool bField) const
{
    ASSShip* Ship = FindShip();
    if (!Ship) return false;
    const FVector Forward = Ship->GetActorForwardVector();
    const FVector Right = Ship->GetActorRightVector();
    const FVector Up = Ship->GetActorUpVector();
    // Use closing speed, including a maximum approach drift, rather than distance alone.
    const float ClosingSpeed = Ship->GetVelocity().Size() + 450.f;
    const float Lead = FMath::Max(9000.f, ClosingSpeed * MinimumReactionSeconds + Radius + PlayerClearanceRadius);
    for (int32 Attempt = 0; Attempt < 16; ++Attempt)
    {
        const FVector2D Offset(Random.FRandRange(-2600.f, 2600.f), Random.FRandRange(-1700.f, 1700.f));
        if (!bField && FVector2D::Distance(Offset, SafeLane) < Radius + PlayerClearanceRadius + 320.f) continue;
        const FVector Candidate = Ship->GetActorLocation() + Forward * (Lead + Random.FRandRange(0.f, 5500.f)) + Right * Offset.X + Up * Offset.Y;
        bool bClear = true;
        for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
        {
            if (It->IsActorBeingDestroyed() || (!It->IsSolidHazard() && !It->IsEnemy() && !It->IsEnvironmentalField())) continue;
            if (bField && It->IsEnvironmentalField())
            {
                if (FVector::DistSquared(Candidate, It->GetActorLocation()) < FMath::Square(Radius + It->GetBodyRadius() + 1800.f)) { bClear = false; break; }
                continue;
            }
            // Fields may overlap physical hazards by design. Distinct fields must
            // have separated envelopes; a distant old field cannot starve a climax.
            if (bField || It->IsEnvironmentalField()) continue;
            if (FVector::DistSquared(Candidate, It->GetActorLocation()) < FMath::Square(Radius + It->GetBodyRadius() + 420.f)) { bClear = false; break; }
        }
        if (bClear) { Location = Candidate; return true; }
    }
    return false;
}

ASSWorldBody* USSSurvivalDirectorComponent::SpawnHazard(ESSWorldKind Kind, float Radius)
{
    if (GetActiveThreatCount() >= MaximumActiveThreats) return nullptr;
    FVector Location;
    const bool bField = Kind == ESSWorldKind::ElectricalStorm || Kind == ESSWorldKind::GravityAnomaly;
    if (!FindSafeSpawn(Radius, Location, bField)) return nullptr;
    ASSWorldBody* Body = GetWorld()->SpawnActor<ASSWorldBody>(Location, FRotator::ZeroRotator);
    if (!Body) return nullptr;
    float Damage = Kind == ESSWorldKind::ElectricalStorm ? 6.f + Wave * .7f : 14.f + Wave * 3.f;
    if (Kind == ESSWorldKind::MassiveAsteroid) Damage *= 2.f;
    Body->Configure(Kind, Radius, Damage, Wave);
    Body->TelegraphSeconds = MinimumReactionSeconds;
    if (ASSShip* Ship = FindShip())
    {
        Body->SetLinearVelocity(bField ? Ship->GetVelocity() * (bClimax ? .65f : .3f) : -Ship->GetActorForwardVector() * Random.FRandRange(40.f, 350.f));
        Body->GravityAcceleration = 400.f + Wave * 45.f;
    }
    Spawned.Add(Body);
    return Body;
}

void USSSurvivalDirectorComponent::SpawnEnemy(ESSWorldKind Kind, ASSEncounterBeacon* Objective)
{
    if (GetActiveThreatCount() >= MaximumActiveThreats) return;
    int32 EnemyCount = 0;
    for (TActorIterator<ASSEnemy> It(GetWorld()); It; ++It) ++EnemyCount;
    if (EnemyCount >= (bClimax ? 5 : (Wave < 6 ? 2 : 4))) return;
    FVector Location;
    if (!FindSafeSpawn(150.f, Location)) return;
    if (ASSEnemy* Enemy = GetWorld()->SpawnActor<ASSEnemy>(Location, FRotator::ZeroRotator))
    {
        Enemy->Configure(Kind, 150.f, 16.f + Wave * 2.5f, Wave);
        Enemy->SetObjectiveOwner(Objective);
        if (ASSShip* Ship = FindShip()) Enemy->SetLinearVelocity(Ship->GetVelocity());
        Spawned.Add(Enemy);
    }
}

void USSSurvivalDirectorComponent::SpawnWreckagePassage()
{
    if (GetActiveThreatCount() + 4 > MaximumActiveThreats) return;
    ASSShip* Ship = FindShip();
    if (!Ship) return;
    FVector Centre;
    if (!FindSafeSpawn(350.f, Centre)) return;
    // Authored four-piece frame: an unobstructed 1,400 cm aperture with varied orientation.
    const FVector Axes[] = {Ship->GetActorRightVector(), -Ship->GetActorRightVector(), Ship->GetActorUpVector(), -Ship->GetActorUpVector()};
    for (int32 Index = 0; Index < 4; ++Index)
    {
        const FVector Position = Centre + Axes[Index] * 1150.f;
        bool bClear = true;
        for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
            if (It->IsSolidHazard() && FVector::DistSquared(Position, It->GetActorLocation()) < FMath::Square(It->GetBodyRadius() + 600.f)) { bClear = false; break; }
        if (!bClear) continue;
        if (ASSWorldBody* Chunk = GetWorld()->SpawnActor<ASSWorldBody>(Position, Ship->GetActorRotation()))
        {
            Chunk->Configure(ESSWorldKind::Wreckage, Index == 0 ? 290.f : 450.f, 20.f + Wave * 3.f, Wave);
            Chunk->SetLinearVelocity(-Ship->GetActorForwardVector() * 80.f);
            Spawned.Add(Chunk);
        }
    }
}

void USSSurvivalDirectorComponent::OfferEncounter(ESSEncounterKind Kind)
{
    ASSShip* Ship = FindShip();
    if (!Ship) return;
    const float Lead = FMath::Max(6500.f, static_cast<float>(Ship->GetVelocity().Size()) * 3.f);
    const FVector Location = Ship->GetActorLocation() + Ship->GetActorForwardVector() * Lead + Ship->GetActorRightVector() * 1100.f;
    if (ASSEncounterBeacon* Beacon = GetWorld()->SpawnActor<ASSEncounterBeacon>(Location, Ship->GetActorRotation()))
    {
        Beacon->ConfigureEncounter(Kind, Wave);
        Spawned.Add(Beacon);
        if (Kind == ESSEncounterKind::MobileDepot) bDepotOffered = true;
        if (Kind == ESSEncounterKind::SalvageCache) bSalvageOffered = true;
        if (Kind == ESSEncounterKind::DistressCombat) bDistressOffered = true;
        if (USSGameInstance* Instance = Cast<USSGameInstance>(GetWorld()->GetGameInstance()))
        {
            Instance->Session.run.depotSeen = bDepotOffered;
            Instance->Session.run.salvageEventSeen = bSalvageOffered;
            Instance->Session.run.distressEventSeen = bDistressOffered;
        }
    }
}

void USSSurvivalDirectorComponent::TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaSeconds, TickType, ThisTickFunction);
    if (!IsActive() || !FindShip()) return;
    CleanTrackedActors();
    WaveAge += DeltaSeconds;
    float Modifier = 1.f;
    if (USSGameInstance* Instance = Cast<USSGameInstance>(GetWorld()->GetGameInstance())) Modifier = static_cast<float>(Instance->Session.PressureMultiplier());
    Pressure = bBreathing ? .08f : FMath::Clamp((.18f + Wave * .065f + (bClimax ? .18f : 0.f)) * Modifier, .1f, 1.f);
    if (!bSalvageOffered && Wave == 2 && WaveAge > 7.f) OfferEncounter(ESSEncounterKind::SalvageCache);
    if (!bDistressOffered && Wave == 7 && WaveAge > 10.f) OfferEncounter(ESSEncounterKind::DistressCombat);
    if (bBreathing)
    {
        if (Wave == 3 && !bDepotOffered) OfferEncounter(ESSEncounterKind::MobileDepot);
        return;
    }
    AvailableBudget = FMath::Min(10.f, AvailableBudget + DeltaSeconds * BaseBudgetPerSecond * (.65f + Wave * .13f) * Modifier);
    SpawnCooldown -= DeltaSeconds;
    if (SpawnCooldown > 0.f || GetActiveThreatCount() >= MaximumActiveThreats) return;
    SpawnCooldown = Random.FRandRange(.65f, 1.2f);

    if (bClimax && Wave == 10 && !bCompoundGravitySpawned)
    {
        if (SpawnHazard(ESSWorldKind::GravityAnomaly, 4300.f)) bCompoundGravitySpawned = true;
        return;
    }
    const float Roll = Random.FRand();
    if ((bClimax && Wave == 5) || (Wave >= 3 && Roll < (bClimax ? .42f : .20f)))
    {
        if (AvailableBudget >= 3.f) { SpawnEnemy(Wave >= 4 && Random.FRand() < .5f ? ESSWorldKind::Flanker : ESSWorldKind::Pursuer); AvailableBudget -= 3.f; }
    }
    else if (Wave >= 4 && !bClimax && Roll > .89f && AvailableBudget >= 5.f)
    {
        if (SpawnHazard(Wave >= 6 && Random.FRand() < .45f ? ESSWorldKind::GravityAnomaly : ESSWorldKind::ElectricalStorm, 3400.f)) AvailableBudget -= 5.f;
    }
    else if (Wave >= 2 && Roll > .69f && Roll < .84f && AvailableBudget >= 4.f)
    {
        SpawnWreckagePassage();
        AvailableBudget -= 4.f;
    }
    else if (AvailableBudget >= 1.f)
    {
        const float SizeRoll = Random.FRand();
        const ESSWorldKind Hazard = SizeRoll < .15f ? ESSWorldKind::MassiveAsteroid : (SizeRoll < .52f ? ESSWorldKind::MediumAsteroid : ESSWorldKind::SmallAsteroid);
        if (SpawnHazard(Hazard, Hazard == ESSWorldKind::MassiveAsteroid ? 650.f : (Hazard == ESSWorldKind::MediumAsteroid ? 240.f : 95.f))) AvailableBudget -= 1.f;
    }
}

void USSSurvivalDirectorComponent::ResetEncounter()
{
    SetActive(false);
    // Called only for station/death transitions. Ordinary Configure never clears the universe.
    for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It) It->Destroy();
    Spawned.Empty();
    AvailableBudget = 0.f;
    Pressure = 0.f;
    WaveAge = 0.f;
}
