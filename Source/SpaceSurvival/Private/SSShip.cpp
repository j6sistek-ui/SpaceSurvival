#include "SSShip.h"
#include "SSAudio.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSWorldActors.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "EngineUtils.h"
#include "Sound/SoundBase.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "Animation/AnimSequence.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/PackageName.h"

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
    // The player is always close to this single shared hero texture.
    Pilot->bForceMipStreaming = true;
    Pilot->SetRelativeLocation(FVector(-15, 0, 72));
    Pilot->SetRelativeRotation(FRotator(0, -90, 0));
    Pilot->SetRelativeScale3D(FVector(1.5f));
    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("ChaseBoom"));
    CameraBoom->SetupAttachment(RootComponent);
    CameraBoom->TargetArmLength = 900.f;
    CameraBoom->SocketOffset = FVector(0, 0, 125);
    CameraBoom->bDoCollisionTest = false;
    CameraBoom->bEnableCameraLag = true;
    CameraBoom->CameraLagSpeed = 9.f;
    CameraBoom->CameraLagMaxDistance = 35.f;
    CameraBoom->bUseCameraLagSubstepping = true;
    CameraBoom->CameraLagMaxTimeStep = 1.f / 120.f;
    CameraBoom->bInheritRoll = false;
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("ChaseCamera"));
    Camera->SetupAttachment(CameraBoom);
    Camera->FieldOfView = 80.f;
    // Frame the entire banked hull below the sightline. The previous upward view
    // clipped the rear hull even without lag at a 16:9 viewport.
    Camera->SetRelativeRotation(FRotator(-4, 0, 0));
    // A restrained chase-side fill keeps the player silhouette readable in deep shadow.
    auto *ReadabilityLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("ShipReadabilityFill"));
    ReadabilityLight->SetupAttachment(RootComponent);
    ReadabilityLight->SetRelativeLocation(FVector(-350, -180, 220));
    ReadabilityLight->SetIntensityUnits(ELightUnits::Lumens);
    ReadabilityLight->SetIntensity(1500.f);
    ReadabilityLight->SetAttenuationRadius(900.f);
    ReadabilityLight->SetLightColor(FLinearColor(.7f, .82f, 1.f));
    ReadabilityLight->SetCastShadows(false);
    EngineAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("EngineAudio"));
    EngineAudio->SetAutoActivate(false);
    EngineAudio->SetupAttachment(RootComponent);
}
const TCHAR *ASSShip::HullAssetPath(SS::Ship Kind)
{
    if (Kind == SS::Ship::Starter && FParse::Param(FCommandLine::Get(), TEXT("SSShipRefresh")) &&
        FPackageName::DoesPackageExist(TEXT("/Game/SpaceSurvival/ShipRefresh/SM_LudoStarter")))
        return TEXT("/Game/SpaceSurvival/ShipRefresh/SM_LudoStarter.SM_LudoStarter");
    return Kind == SS::Ship::Agile ? TEXT("/Game/SpaceSurvival/Meshes/SM_SwiftCandidateV1.SM_SwiftCandidateV1")
                                   : TEXT("/Game/SpaceSurvival/Meshes/SM_AcornShipGripFit.SM_AcornShipGripFit");
}
void ASSShip::UpdateEngineMix()
{
    const auto *GI = GetGameInstance<USSGameInstance>();
    EngineAudio->SetVolumeMultiplier(SSAudio::EffectsGain(this, .35f));
    EngineAudio->SetPitchMultiplier(GI && GI->Session.run.boosting ? 1.3f : .9f + .15f * ThrottleInput);
}
void ASSShip::BeginPlay()
{
    Super::BeginPlay();
    if (!Tuning)
        Tuning = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
    if (!Tuning)
        Tuning = NewObject<USSPhase1Data>(this);
    auto *GI = GetGameInstance<USSGameInstance>();
    HullMesh->SetStaticMesh(
        LoadObject<UStaticMesh>(nullptr, HullAssetPath(GI ? GI->Session.run.ship : SS::Ship::Starter)));
    Pilot->SetSkeletalMesh(
        LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/SpaceSurvival/Character/SK_AcornautTailV2.SK_AcornautTailV2")));
    Pilot->SetVisibility(!HullMesh->GetStaticMesh() || !HullMesh->GetStaticMesh()->GetPathName().StartsWith(
                                                           TEXT("/Game/SpaceSurvival/ShipRefresh/")));
    Pilot->PlayAnimation(
        LoadObject<UAnimSequence>(nullptr, TEXT("/Game/SpaceSurvival/Character/A_PilotGripFit.A_PilotGripFit")), true);
    EngineAudio->SetSound(LoadObject<USoundBase>(nullptr, TEXT("/Game/SpaceSurvival/Audio/Engine.Engine")));
    UpdateEngineMix();
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
bool ASSShip::BeginMooring()
{
    const auto *GI = GetGameInstance<USSGameInstance>();
    if (Docking || !GI || !GI->Session.IsFlying())
        return false;
    Moored = true;
    Velocity = Forces = FVector::ZeroVector;
    SoftTarget = nullptr;
    SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 0.f, false, false);
    return true;
}
void ASSShip::EndMooring()
{
    if (!Moored)
        return;
    Moored = false;
    Forces = FVector::ZeroVector;
    const auto *GI = GetGameInstance<USSGameInstance>();
    if (GI && GI->Session.IsFlying())
        Velocity = GetActorForwardVector() * float(GI->Session.Stats().speed);
}
float ASSShip::SoftAssistWeight(float Alignment, float ConeDegrees, float MaximumStrength)
{
    if (!FMath::IsFinite(Alignment) || !FMath::IsFinite(ConeDegrees) || ConeDegrees <= 0.f ||
        !FMath::IsFinite(MaximumStrength))
        return 0.f;
    const float Edge = FMath::Cos(FMath::DegreesToRadians(FMath::Clamp(ConeDegrees, .01f, 45.f)));
    const float Position = FMath::Clamp((Alignment - Edge) / FMath::Max(1.f - Edge, SMALL_NUMBER), 0.f, 1.f);
    return FMath::Clamp(MaximumStrength, 0.f, .4f) * Position;
}
void ASSShip::FinishDocking()
{
    SetActorLocation(DockTarget);
    SetActorRotation(DockRotation);
    Pilot->SetVisibility(false);
    if (auto *ReadabilityLight = FindComponentByClass<UPointLightComponent>())
        ReadabilityLight->SetVisibility(false);
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
    UpdateEngineMix();
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI || !Tuning)
        return;
    auto &S = GI->Session;
    FireCooldown = FMath::Max(0.f, FireCooldown - Dt);
    ImpactCooldown = FMath::Max(0.f, ImpactCooldown - Dt);
    if (Moored)
    {
        // Existing hazards and damage remain active; GameMode freezes wave progress.
        Velocity = Forces = FVector::ZeroVector;
        SoftTarget = nullptr;
        S.TickFlight(Dt, false, false);
        return;
    }
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
        FMath::FInterpTo(CameraBoom->TargetArmLength,
                         FMath::Max(900.f, Tuning->ChaseDistance) + (S.run.boosting ? 110.f : 0.f), Dt, 3.f);
    Camera->FieldOfView = FMath::FInterpTo(Camera->FieldOfView, S.run.boosting ? 86.f : 80.f, Dt, 3.f);
    if (GI->Session.settings.cameraShake && S.run.damageFeedback > 0)
        Camera->SetRelativeLocation(
            FVector(0, FMath::Sin(GetWorld()->GetTimeSeconds() * 70.f) * 3.f * float(S.run.damageFeedback), 0));
    else
        Camera->SetRelativeLocation(FVector::ZeroVector);
    UpdateEngineMix();
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
        const FVector SightOrigin = Camera ? Camera->GetComponentLocation() : GetActorLocation();
        const float Dot = FVector::DotProduct(Aim, (It->GetActorLocation() - SightOrigin).GetSafeNormal());
        if (Dot <= Best)
            continue;
        FHitResult Hit;
        FCollisionQueryParams Params;
        Params.AddIgnoredActor(this);
        GetWorld()->LineTraceSingleByChannel(Hit, GetActorLocation() + GetActorForwardVector() * 240.f,
                                             It->GetActorLocation(), ECC_Visibility, Params);
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
    if (Moored || !GI || !GI->Session.Dodge())
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
void ASSShip::ReceiveImpact(float Amount, FVector AwayFromContact)
{
    ReceiveDamage(Amount, SS::DamageType::Kinetic);
    const auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI || !GI->Session.IsFlying() || !FMath::IsFinite(Amount) || Amount <= 0.f || AwayFromContact.ContainsNaN())
        return;
    // A contact changes velocity once, in cm/s. Gravity remains an acceleration
    // integrated over time; treating a single impact that way weakened it at high FPS.
    Velocity += AwayFromContact.GetSafeNormal() * FMath::Min(1400.f, Amount * 20.f);
}
void ASSShip::Fire()
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (Moored || !GI || !GI->Session.IsFlying() || FireCooldown > 0)
        return;
    auto &S = GI->Session;
    const bool Cannon = S.run.weapon == SS::Weapon::HeavyCannon;
    FireCooldown = Cannon ? Tuning->CannonInterval : Tuning->LaserInterval;
    const FVector Start = GetActorLocation() + GetActorForwardVector() * 240.f;
    const FVector Sight = AimDirection();
    const FVector SightOrigin = Camera ? Camera->GetComponentLocation() : Start;
    FVector AimPoint = SightOrigin + Sight * Tuning->WeaponRange;
    FCollisionQueryParams SightQuery(SCENE_QUERY_STAT(SSManualAim), false, this);
    FHitResult SightHit;
    // Resolve the visible reticle point, then converge from the real muzzle.
    // Camera obstructions behind the muzzle must never reverse a shot.
    if (GetWorld()->LineTraceSingleByChannel(SightHit, SightOrigin, AimPoint, ECC_Visibility, SightQuery) &&
        FVector::DotProduct(SightHit.ImpactPoint - Start, Sight) > 1.f)
        AimPoint = SightHit.ImpactPoint;
    FVector Direction = (AimPoint - Start).GetSafeNormal();
    if (IsValid(SoftTarget) && !SoftTarget->IsActorBeingDestroyed())
    {
        const FVector TargetDelta = SoftTarget->GetActorLocation() - SightOrigin;
        const float Alignment = FVector::DotProduct(Sight, TargetDelta.GetSafeNormal());
        const float Weight = SoftAssistWeight(Alignment, Tuning->SoftAimDegrees, MaximumSoftAssist);
        // Recheck the current sightline at trigger time; a previous frame's target must not pull a turn.
        if (FVector::DistSquared(SoftTarget->GetActorLocation(), GetActorLocation()) <=
            FMath::Square(Tuning->WeaponRange))
            Direction = FMath::Lerp(Direction, (SoftTarget->GetActorLocation() - Start).GetSafeNormal(), Weight)
                            .GetSafeNormal();
    }
    // The existing muzzle trace/projectile sweep still handles nearby cover;
    // selecting a visible aim point never permits shooting through an obstacle.
    const float Damage = float(S.Stats().weaponDamage);
    if (Cannon)
    {
        auto *Shot = GetWorld()->SpawnActor<ASSProjectile>(Start, Direction.Rotation());
        if (Shot)
            Shot->Launch(Direction, 19000.f, Damage, true, this, Tuning->WeaponRange);
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
            Trace->Launch(Direction, 55000.f, 0.f, true, this, Tuning->WeaponRange);
    }
    UGameplayStatics::PlaySoundAtLocation(
        this,
        LoadObject<USoundBase>(nullptr, Cannon ? TEXT("/Game/SpaceSurvival/Audio/Cannon.Cannon")
                                               : TEXT("/Game/SpaceSurvival/Audio/Laser.Laser")),
        Start, float(S.settings.masterVolume * S.settings.effectsVolume));
}
