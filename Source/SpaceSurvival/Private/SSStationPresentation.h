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
/** Names, roles and live activities for the deck crew above, as push-to-talk component tags (docs/NPC_TALK.md). */
void TagTalkers(AActor *Owner);
/** Owner 2026-10-12: the station lags until the crew meshes are optimised, so every character in the authored map
 *  but the pool players, the bartender, the desk crew and the dancers is hidden and stops animating. A switch
 *  (ss.StationCrewTrim 0 shows everyone); labels are an editor-only thing, so a packaged build keeps everyone. */
void TrimCrew(const TArray<TObjectPtr<AActor>> &Actors);
void PaceAlienCrew(AActor *Owner);
} // namespace SSStationPresentation
