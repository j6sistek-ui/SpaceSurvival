#include "SSWeaponDamage.h"
#include "SSDistantAsteroids.h"
#include "SSSpaceScenery.h"
#include "SSWorldActors.h"

bool SSWeaponDamage::Apply(const FHitResult &Hit, float Damage)
{
    if (!FMath::IsFinite(Damage) || Damage <= 0.f)
        return false;
    if (auto *Body = Cast<ASSWorldBody>(Hit.GetActor()))
    {
        const bool Target = Body->IsWeaponTarget() && !Body->IsActorBeingDestroyed();
        Body->ReceiveWeaponHit(Damage);
        return Target;
    }
    bool Destroyed = false;
    if (auto *Field = Cast<ASSDistantAsteroids>(Hit.GetActor()))
        return Field->ApplyWeaponHit(Hit, Damage, Destroyed);
    if (auto *Scenery = Cast<ASSSpaceScenery>(Hit.GetActor()))
        return Scenery->ApplyWeaponHit(Hit, Damage, Destroyed);
    return false;
}
