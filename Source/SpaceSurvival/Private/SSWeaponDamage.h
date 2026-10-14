#pragma once
#include "CoreMinimal.h"

namespace SSWeaponDamage
{
/** Damage only the actual traced actor/instance. Returns true for an accepted hit. */
bool Apply(const FHitResult &Hit, float Damage);
} // namespace SSWeaponDamage
