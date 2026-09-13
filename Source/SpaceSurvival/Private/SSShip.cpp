#include "SSShip.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSWorldActors.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/AudioComponent.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "EngineUtils.h"
#include "Sound/SoundBase.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"

ASSShip::ASSShip()
{
    PrimaryActorTick.bCanEverTick = true;
    Collision = CreateDefaultSubobject<USphereComponent>(TEXT("FlightCollision"));
    Collision->InitSphereRadius(105.f);
    RootComponent = Collision;
    Collision->SetCollisionObjectType(ECC_Pawn);
    Collision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Collision->SetCollisionResponseToAllChannels(ECR_Ignore);
    Collision->SetCollisionResponseToChannel(ECC_WorldStatic, ECR_Block);
    HullMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("AcornHull"));
    HullMesh->SetupAttachment(RootComponent);
    HullMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Pilot = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("AcornautPilot"));
    Pilot->SetupAttachment(HullMesh);
    Pilot->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Pilot->SetRelativeLocation(FVector(15, 0, 50));
    Pilot->SetRelativeScale3D(FVector(.7f));
    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("ChaseBoom"));
    CameraBoom->SetupAttachment(RootComponent);
    CameraBoom->TargetArmLength = 650.f;
    CameraBoom->SocketOffset = FVector(0, 0, 175);
    CameraBoom->bDoCollisionTest = false;
    CameraBoom->bEnableCameraLag = true;
    CameraBoom->CameraLagSpeed = 9.f;
    CameraBoom->bInheritRoll = false;
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("ChaseCamera"));
    Camera->SetupAttachment(CameraBoom);
    Camera->FieldOfView = 80.f;
    EngineAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("EngineAudio"));
    EngineAudio->SetupAttachment(RootComponent);
}
void ASSShip::BeginPlay()
{
    Super::BeginPlay();
    if (!Tuning)
        Tuning = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
    if (!Tuning)
        Tuning = NewObject<USSPhase1Data>(this);
    auto *GI = GetGameInstance<USSGameInstance>();
    const bool Agile = GI && GI->Session.run.ship == SS::Ship::Agile;
    HullMesh->SetStaticMesh(
        LoadObject<UStaticMesh>(nullptr, Agile ? TEXT("/Game/SpaceSurvival/Meshes/SM_AgileShip.SM_AgileShip")
                                               : TEXT("/Game/SpaceSurvival/Meshes/SM_AcornShip.SM_AcornShip")));
    Pilot->SetSkeletalMesh(
        LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/SpaceSurvival/Character/SK_Acornaut.SK_Acornaut")));
    EngineAudio->SetSound(LoadObject<USoundBase>(nullptr, TEXT("/Game/SpaceSurvival/Audio/Engine.Engine")));
    EngineAudio->Play();
    Velocity = GetActorForwardVector() * Tuning->CruiseSpeed;
}
void ASSShip::SetFlightInput(FVector2D Steering, FVector2D Strafe, float Throttle, bool Boost, bool Brake)
{
    Steer = Steering.GetClampedToMaxSize(1.f);
    StrafeInput = Strafe.GetClampedToMaxSize(1.f);
    ThrottleInput = FMath::Clamp(Throttle, -1.f, 1.f);
    BoostInput = Boost;
    BrakeInput = Brake;
}
void ASSShip::AddExternalForce(FVector Force)
{
    Forces += Force.GetClampedToMaxSize(2500.f);
}
void ASSShip::SetDockingTarget(FVector Target, FRotator Rotation)
{
    DockTarget = Target;
    DockRotation = Rotation;
    Docking = true;
}
void ASSShip::FinishDocking()
{
    SetActorLocation(DockTarget);
    SetActorRotation(DockRotation);
    Pilot->SetVisibility(false);
    EngineAudio->Stop();
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Velocity = Forces = FVector::ZeroVector;
    SetActorTickEnabled(false);
}
void ASSShip::ApplyWorldOffset(const FVector &InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    if (Docking)
        DockTarget += InOffset;
}
void ASSShip::Tick(float Dt)
{
    Super::Tick(Dt);
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI || !Tuning)
        return;
    auto &S = GI->Session;
    FireCooldown = FMath::Max(0.f, FireCooldown - Dt);
    ImpactCooldown = FMath::Max(0.f, ImpactCooldown - Dt);
    if (Docking)
    {
        SetActorLocation(FMath::VInterpTo(GetActorLocation(), DockTarget, Dt, 2.f));
        SetActorRotation(FMath::RInterpTo(GetActorRotation(), DockRotation, Dt, 2.f));
        Velocity = FVector::ZeroVector;
        return;
    }
    if (!S.IsFlying())
    {
        Forces = FVector::ZeroVector;
        return;
    }
    S.TickFlight(Dt, BoostInput, BrakeInput);
    const auto Stats = S.Stats();
    const float BoostFactor = S.run.boosting ? Tuning->BoostMultiplier : 1.f;
    const float BrakeFactor = S.run.braking ? .47f : 1.f;
    const float Speed =
        FMath::Max(Tuning->MinimumSpeed, float(Stats.speed) * (1.f + .3f * ThrottleInput) * BoostFactor * BrakeFactor);
    const float Authority = float(Stats.maneuver) / 1700.f;
    const float Interference = S.run.interferenceSeconds > 0 ? .7f : 1.f;
    // Bounded substeps preserve steering/acceleration and swept movement at low FPS.
    const int32 Steps = FMath::Clamp(FMath::CeilToInt(Dt / (1.f / 120.f)), 1, 32);
    const float Step = Dt / Steps;
    for (int32 I = 0; I < Steps; ++I)
    {
        auto Rotation = GetActorRotation();
        Rotation.Yaw += Steer.X * Tuning->SteeringDegrees * Authority * Interference * Step;
        Rotation.Pitch = FMath::Clamp(
            Rotation.Pitch + Steer.Y * Tuning->SteeringDegrees * Authority * Interference * Step, -85.f, 85.f);
        Rotation.Roll = 0;
        SetActorRotation(Rotation);
        const FVector Desired =
            GetActorForwardVector() * Speed +
            (GetActorRightVector() * StrafeInput.X + GetActorUpVector() * StrafeInput.Y) * float(Stats.maneuver);
        const FVector ResponseDelta = (Desired - Velocity) * (1.f - FMath::Exp(-float(Stats.response) * Step));
        Velocity += ResponseDelta.GetClampedToMaxSize(float(Stats.acceleration) * Step);
        Velocity += Forces.GetClampedToMaxSize(4500.f) * Step;
        FHitResult Hit;
        AddActorWorldOffset(Velocity * Step, true, &Hit);
        if (Hit.bBlockingHit)
        {
            if (ImpactCooldown <= 0)
            {
                ReceiveDamage(15.f * float(S.DamageScale()));
                ImpactCooldown = .8f;
            }
            Velocity = FVector::VectorPlaneProject(Velocity, Hit.Normal) * .65f;
        }
    }
    Forces = FVector::ZeroVector;
    const float Bank = -Steer.X * 28.f - StrafeInput.X * 12.f;
    HullMesh->SetRelativeRotation(
        FMath::RInterpTo(HullMesh->GetRelativeRotation(), FRotator(-StrafeInput.Y * 5.f, 0, Bank), Dt, 6.f));
    CameraBoom->TargetArmLength =
        FMath::FInterpTo(CameraBoom->TargetArmLength, Tuning->ChaseDistance + (S.run.boosting ? 110.f : 0.f), Dt, 3.f);
    Camera->FieldOfView = FMath::FInterpTo(Camera->FieldOfView, S.run.boosting ? 86.f : 80.f, Dt, 3.f);
    if (GI->Session.settings.cameraShake && S.run.damageFeedback > 0)
        Camera->SetRelativeLocation(
            FVector(0, FMath::Sin(GetWorld()->GetTimeSeconds() * 70.f) * 3.f * float(S.run.damageFeedback), 0));
    else
        Camera->SetRelativeLocation(FVector::ZeroVector);
    EngineAudio->SetPitchMultiplier(S.run.boosting ? 1.3f : .9f + .15f * ThrottleInput);
    EngineAudio->SetVolumeMultiplier(float(S.settings.masterVolume * S.settings.effectsVolume) * .35f);
    SoftTarget = nullptr;
    float Best = FMath::Cos(FMath::DegreesToRadians(Tuning->SoftAimDegrees));
    const FVector Aim = AimDirection();
    for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
    {
        if (!It->IsWeaponTarget())
            continue;
        const FVector Delta = It->GetActorLocation() - GetActorLocation();
        if (Delta.SizeSquared() > FMath::Square(Tuning->WeaponRange))
            continue;
        const float Dot = FVector::DotProduct(Aim, Delta.GetSafeNormal());
        if (Dot <= Best)
            continue;
        FHitResult Hit;
        FCollisionQueryParams Params;
        Params.AddIgnoredActor(this);
        GetWorld()->LineTraceSingleByChannel(Hit, GetActorLocation() + Aim * 230.f, It->GetActorLocation(),
                                             ECC_Visibility, Params);
        if (!Hit.bBlockingHit || Hit.GetActor() == *It)
        {
            Best = Dot;
            SoftTarget = *It;
        }
    }
}
FVector ASSShip::AimDirection() const
{
    return Camera ? Camera->GetForwardVector() : GetActorForwardVector();
}
void ASSShip::RequestDodge()
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI || !GI->Session.Dodge())
        return;
    FVector2D Direction = StrafeInput.IsNearlyZero() ? Steer : StrafeInput;
    if (Direction.IsNearlyZero())
        Direction = FVector2D(1, 0);
    Direction.Normalize();
    Velocity += (GetActorRightVector() * Direction.X + GetActorUpVector() * Direction.Y) * Tuning->DodgeImpulse;
    // No collision immunity is granted; every world body still applies damage.
}
void ASSShip::ReceiveDamage(float Amount, SS::DamageType Type)
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI)
        return;
    GI->Session.ApplyDamage(Amount, Type);
    UGameplayStatics::PlaySoundAtLocation(
        this, LoadObject<USoundBase>(nullptr, TEXT("/Game/SpaceSurvival/Audio/Impact.Impact")), GetActorLocation(),
        float(GI->Session.settings.masterVolume * GI->Session.settings.effectsVolume));
}
void ASSShip::Fire()
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI || !GI->Session.IsFlying() || FireCooldown > 0)
        return;
    auto &S = GI->Session;
    const bool Cannon = S.run.weapon == SS::Weapon::HeavyCannon;
    FireCooldown = Cannon ? Tuning->CannonInterval : Tuning->LaserInterval;
    FVector Direction = AimDirection();
    if (IsValid(SoftTarget))
        Direction = FMath::Lerp(Direction, (SoftTarget->GetActorLocation() - GetActorLocation()).GetSafeNormal(), .42f)
                        .GetSafeNormal();
    const FVector Start = GetActorLocation() + GetActorForwardVector() * 240.f;
    const float Damage = float(S.Stats().weaponDamage);
    if (Cannon)
    {
        auto *Shot = GetWorld()->SpawnActor<ASSProjectile>(Start, Direction.Rotation());
        if (Shot)
            Shot->Launch(Direction, 19000.f, Damage, true, this);
    }
    else
    {
        FHitResult Hit;
        FCollisionQueryParams Params;
        Params.AddIgnoredActor(this);
        GetWorld()->LineTraceSingleByChannel(Hit, Start, Start + Direction * Tuning->WeaponRange, ECC_Visibility,
                                             Params);
        if (auto *Body = Cast<ASSWorldBody>(Hit.GetActor()))
            Body->ReceiveWeaponHit(Damage);
        auto *Trace = GetWorld()->SpawnActor<ASSProjectile>(Start, Direction.Rotation());
        if (Trace)
            Trace->Launch(Direction, 55000.f, 0.f, true, this);
    }
    UGameplayStatics::PlaySoundAtLocation(
        this,
        LoadObject<USoundBase>(nullptr, Cannon ? TEXT("/Game/SpaceSurvival/Audio/Cannon.Cannon")
                                               : TEXT("/Game/SpaceSurvival/Audio/Laser.Laser")),
        Start, float(S.settings.masterVolume * S.settings.effectsVolume));
}
