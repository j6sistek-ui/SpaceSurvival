#pragma once
#include "CoreMinimal.h"

class AActor;
class UStaticMeshComponent;
class UMaterialInterface;

// Optional licensed dressing. The station continues to own all geometry and
// authoritative service/collision locations. Optional idle skeletal components
// animate at 30Hz when rendered; no actor tick or gameplay is added. The alien
// crew adds no tick of its own: PaceAlienCrew is called from the station's existing
// Tick, and moves two of the seven a few steps around their post. The conversation
// groups stay put and face the centre of their own circle, because a group that
// drifts apart stops reading as a conversation.
namespace SSStationPresentation
{
UMaterialInterface *InstancedMaterial(UMaterialInterface *Source);
void BuildDetails(AActor *Owner, TArray<TObjectPtr<UStaticMeshComponent>> &Geometry);
void BuildSupplementalStaff(AActor *Owner);
void BuildAlienCrew(AActor *Owner);
void PaceAlienCrew(AActor *Owner);
} // namespace SSStationPresentation
