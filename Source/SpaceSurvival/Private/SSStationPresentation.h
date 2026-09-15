#pragma once
#include "CoreMinimal.h"

class AActor;
class UStaticMeshComponent;
class UMaterialInterface;

// Optional licensed dressing. The station continues to own all geometry and
// authoritative service/collision locations. At most two optional idle skeletal
// components animate at 30Hz when rendered; no actor tick or gameplay is added.
namespace SSStationPresentation
{
UMaterialInterface *InstancedMaterial(UMaterialInterface *Source);
void BuildDetails(AActor *Owner, TArray<TObjectPtr<UStaticMeshComponent>> &Geometry);
void BuildSupplementalStaff(AActor *Owner);
} // namespace SSStationPresentation
