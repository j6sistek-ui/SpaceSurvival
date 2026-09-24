#include "SSShip.h"
#include "SSAudio.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShipPresentation.h"
#include "SSShipVisualRig.h"
#include "SSVFXPresentation.h"
#include "SSWorldActors.h"
#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

FVector ASSShip::MuzzleWorldPosition() const
{
    FVector Position;
    if (VisualRig && VisualRig->GetMuzzleWorldPosition(Position))
        return Position;
    if (Presentation && Presentation->TryGetMuzzleWorldPosition(Position))
        return Position;
    const FSSHullDefinition Hull(SelectedHullIdentity());
    // A missing optional weapon mount must still fire clear of the measured hull. The previous
    // universal +240 cm point was inside the Phoenix, hiding its muzzle and initial tracer travel.
    return GetActorLocation() + GetActorForwardVector() * (Hull.ScaledOriginToNose() + 30.f) +
           GetActorUpVector() * Hull.CrosshairMountZ;
}

FVector ASSShip::CrosshairWorldPoint() const
{
    const FSSHullDefinition Hull(SelectedHullIdentity());
    if (Hull.CrosshairReach <= 0.f)
        return Camera ? Camera->GetComponentLocation() + Camera->GetForwardVector() * 20000.f
                      : GetActorLocation() + GetActorForwardVector() * 20000.f;
    return GetActorLocation() + GetActorUpVector() * Hull.CrosshairMountZ +
           GetActorForwardVector() * Hull.CrosshairReach;
}
FVector ASSShip::AimDirection() const
{
    const FVector Muzzle = MuzzleWorldPosition();
    const FVector Eye = Camera ? Camera->GetComponentLocation() : Muzzle;
    // CrosshairWorldPoint is projected by the HUD. Its screen ray starts at the camera, including
    // the Phoenix's off-centre reticle. A muzzle ray through the distant anchor misses nearby
    // objects visibly under that reticle because the elevated chase camera has substantial parallax.
    const FVector Sight = (CrosshairWorldPoint() - Eye).GetSafeNormal();
    const float Range = Tuning ? FMath::Max(1.f, Tuning->WeaponRange) : 20000.f;
    const FVector EyeToMuzzle = Muzzle - Eye;
    const double Along = FVector::DotProduct(EyeToMuzzle, Sight);
    const double AcrossSquared = FMath::Max(0., EyeToMuzzle.SizeSquared() - Along * Along);
    FVector AimPoint =
        Eye + Sight * (FMath::Max(0., Along) + FMath::Sqrt(FMath::Max(0., double(Range) * Range - AcrossSquared)));
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSManualAim), false, this);
    FHitResult Hit;
    if (GetWorld() && GetWorld()->LineTraceSingleByChannel(Hit, Eye, AimPoint, ECC_Visibility, Query) &&
        FVector::DotProduct(Hit.ImpactPoint - Muzzle, GetActorForwardVector()) > 1.f)
        AimPoint = Hit.ImpactPoint;
    return (AimPoint - Muzzle).GetSafeNormal();
}

void ASSShip::Fire()
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (Moored || Docking || TakingOff || !GI || !GI->Session.IsFlying() || FireCooldown > 0)
        return;
    auto &S = GI->Session;
    const bool Cannon = S.run.weapon == SS::Weapon::HeavyCannon;
    FireCooldown = Cannon ? Tuning->CannonInterval : Tuning->LaserInterval;
    // Long enough to stay lit between rapid-laser shots, short enough that one cannon shot does
    // not hold the reticle open for most of a second.
    FireVisualSeconds = .16f;
    if (VisualRig)
        VisualRig->PlayFiring();
    const FVector Start = MuzzleWorldPosition();
    const FVector SightOrigin = Camera ? Camera->GetComponentLocation() : Start;
    const FVector Sight = (CrosshairWorldPoint() - SightOrigin).GetSafeNormal();
    FVector Direction = AimDirection();
    if (IsValid(SoftTarget) && !SoftTarget->IsActorBeingDestroyed())
    {
        const FVector TargetDelta = SoftTarget->GetActorLocation() - SightOrigin;
        const float Alignment = FVector::DotProduct(Sight, TargetDelta.GetSafeNormal());
        const float Weight = SoftAssistWeight(Alignment, Tuning->SoftAimDegrees, MaximumSoftAssist);
        FHitResult Cover;
        FCollisionQueryParams Query(SCENE_QUERY_STAT(SSAssistCover), false, this);
        const bool Obstructed =
            GetWorld()->LineTraceSingleByChannel(Cover, Start, SoftTarget->GetActorLocation(), ECC_Visibility, Query) &&
            Cover.GetActor() != SoftTarget;
        // Recheck range and cover at trigger time; a previous frame's target cannot pull a shot
        // through cover or turn the ship. Assistance remains a bounded correction to manual aim.
        if (!Obstructed &&
            FVector::DistSquared(SoftTarget->GetActorLocation(), Start) <= FMath::Square(Tuning->WeaponRange))
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
        if (Hit.bBlockingHit)
            if (auto *FX = GetWorld()->GetSubsystem<USSCombatVFXSubsystem>())
                FX->PlayImpact(Hit.ImpactPoint, Hit.ImpactNormal, true, false);
        if (auto *Body = Cast<ASSWorldBody>(Hit.GetActor()))
        {
            const bool Damageable = Body->IsWeaponTarget();
            Body->ReceiveWeaponHit(Damage);
            if (Damageable)
                if (auto *Mode = GetWorld()->GetAuthGameMode<ASSGameMode>())
                    Mode->NotifyPlayerShotHit();
        }
        auto *Trace = GetWorld()->SpawnActor<ASSProjectile>(Start, Direction.Rotation());
        if (Trace)
            Trace->Launch(Direction, 55000.f, 0.f, true, this, Hit.bBlockingHit ? Hit.Distance : Tuning->WeaponRange);
    }
    UGameplayStatics::PlaySoundAtLocation(this, SSAudio::PresentationSound(Cannon ? TEXT("Cannon") : TEXT("Laser")),
                                          Start, float(S.settings.masterVolume * S.settings.effectsVolume));
}
