#pragma once
#include "CoreMinimal.h"
#include "Domain/SurvivalCore.h"

class UStaticMeshComponent;

// Private to the module: nothing outside it paints a hull.
// The paint bay: ten flat finishes over four hull sections, kept on the account. A section is found from the
// material a slot carries, so every supported hull paints without per-mesh tables; glass, lights and cockpit
// interiors never take paint.
namespace SSPaint
{
enum ESection : int32
{
    Body = 0,
    Wings = 1,
    Engines = 2,
    Weapons = 3
};
const TCHAR *SectionName(int32 Section);
const TCHAR *ColourName(int32 Colour);
FLinearColor Colour(int32 Colour);
// The section a material belongs to from its name, or INDEX_NONE for surfaces that are never painted.
int32 SectionForMaterial(const FString &MaterialName);
// Repaints a hull from the account. A painted section gets a dynamic instance of the mesh's own material with its
// colour parameter set; everything else returns to the mesh's default material, so repainting is idempotent.
void Apply(UStaticMeshComponent *Hull, const SS::Account &Account);
} // namespace SSPaint
