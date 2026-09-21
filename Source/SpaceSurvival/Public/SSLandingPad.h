#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSLandingPad.generated.h"
class UStaticMeshComponent;

/** A place a ship can be put down. Placeable on its own, anywhere, with no station behind it.
 *
 *  The owner's requirement, in their words: "a landing pad anywhere in the game, ever, future features
 *  anything, all docks and launches the same exact way" and "make sure this is a prefab type concept or
 *  feature so if we add landing pads anywhere else, they all work exactly the same". Before this the pad
 *  was three static constexpr numbers on ASSStation and a lambda that assembled cubes in station-local
 *  space - which meant exactly one pad could exist, at one station, and the docking sequence had nowhere
 *  to be written against except that station.
 *
 *  The actor's origin IS the landing spot: the centre of the deck's top surface. That is the one point a
 *  ship, a hero and a sequence all care about, so it is the pivot rather than something derived from a
 *  slab centre and a thickness. The slab hangs below it. Everything a caller asks for - where to park,
 *  where to set the hero down, whether a point is on the pad - is answered relative to that origin and
 *  this actor's own rotation, so a pad rotated seventy-five degrees at the far end of the map answers the
 *  same questions the same way. */
UCLASS()
class SPACESURVIVAL_API ASSLandingPad : public AActor
{
    GENERATED_BODY()
public:
    ASSLandingPad();
    /** Half the width of the square deck. 1600 holds the 2484 x 1244 cm Phoenix with room either side. */
    UPROPERTY(EditAnywhere, Category = "Landing Pad")
    float HalfExtent = 1600.f;
    /** Reset colony pad: a circular physical slab with full-height walking guards and an open bridge. */
    UPROPERTY(EditAnywhere, Category = "Landing Pad")
    bool bCircularDeck = false;
    /** How far the slab hangs below the deck surface. */
    UPROPERTY(EditAnywhere, Category = "Landing Pad")
    float DeckThickness = 270.f;
    /** Minimum capture radius; a long hull may require a wider approach envelope. */
    UPROPERTY(EditAnywhere, Category = "Landing Pad", meta = (ClampMin = "1200"))
    float ApproachRadius = 1200.f;
    /** Survival resumes only when a departing ship clears this boundary. */
    UPROPERTY(EditAnywhere, Category = "Landing Pad", meta = (ClampMin = "5000"))
    float StationZoneRadius = 18000.f;
    /** Builds the deck, its kerbs and the landing indicator from meshes and materials the project already
     *  ships. Called by whoever placed the pad, once; a second call is a no-op. Explicit rather than
     *  BeginPlay because the automation worlds that spawn stations never run BeginPlay, and a pad that only
     *  exists once play starts is a pad the tests cannot see. */
    void Build();
    bool IsBuilt() const
    {
        return Deck != nullptr;
    }
    const UStaticMeshComponent *GetDeck() const
    {
        return Deck;
    }
    /** The centre of the deck's top surface, in world space. The origin, by construction. */
    FVector DeckPoint() const
    {
        return GetActorLocation();
    }
    /** Where a ship's origin parks. The clearance is the ship's to declare, because it is the distance from
     *  that ship's origin to its belly plus whatever its gear needs; 230 is the classic hull's, kept as the
     *  default so callers that do not yet know their hull behave as they always did. */
    FVector DockPoint(float ClearanceAboveDeck = 230.f) const
    {
        return GetActorTransform().TransformPosition(FVector(0, 0, ClearanceAboveDeck));
    }
    FVector HoverPoint(float ClearanceAboveDeck = 230.f) const
    {
        return DockPoint(ClearanceAboveDeck) + GetActorUpVector() * 700.f;
    }
    /** Where the hero appears. ConfigureWalkExit replaces the unoccupied-pad default with a measured,
     *  floor-supported position beside the actual parked hull. */
    FVector WalkSpawn() const
    {
        return GetActorTransform().TransformPosition(WalkSpawnOffset);
    }
    /** Where a disembarking hero is set down, beside the parked ship rather than inside it. */
    FVector ExitPoint() const
    {
        return GetActorTransform().TransformPosition(ExitOffset);
    }
    /** Bounds are measured in this pad's frame after the ship reaches its parked transform. */
    bool ConfigureWalkExit(const FBox &HullBounds, float CapsuleRadius, float CapsuleHalfHeight,
                           const AActor *ParkedShip);
    bool IsOutsideParkedHull(const FVector &World, float CapsuleRadius) const;
    /** Whether a world position counts as being on this pad, for the purpose of NOT rescuing a walker who
     *  is standing there. Generous by the margin, so the kerbs and the first step off the edge are still
     *  "on the pad"; a hero who actually falls drops through the floor of the band and is caught by the
     *  usual rescue. */
    bool Covers(const FVector &World, float Margin = 100.f) const
    {
        const FVector Local = GetActorTransform().InverseTransformPosition(World);
        const bool Inside =
            bCircularDeck ? Local.SizeSquared2D() <= FMath::Square(HalfExtent + Margin)
                          : FMath::Abs(Local.X) <= HalfExtent + Margin && FMath::Abs(Local.Y) <= HalfExtent + Margin;
        return Inside && Local.Z >= -240.f;
    }
    /** The lit disc at the dock point. On while the pad is waiting for a ship, off once one is down. */
    void ShowIndicator(bool Visible);
    bool IsIndicatorVisible() const;

private:
    FVector WalkSpawnOffset = FVector(400.f, 0, 190.f);
    FVector ExitOffset = FVector(200.f, -350.f, 110.f);
    FBox ParkedHullBounds = FBox(ForceInit);
    UPROPERTY()
    TObjectPtr<USceneComponent> Root;
    UPROPERTY()
    TObjectPtr<UStaticMeshComponent> Deck;
    UPROPERTY()
    TObjectPtr<UStaticMeshComponent> Indicator;
    UPROPERTY()
    TArray<TObjectPtr<UStaticMeshComponent>> Dressing;
    UStaticMeshComponent *AddMesh(FVector Position, FVector Scale, const TCHAR *Mesh, const TCHAR *Material, bool Solid,
                                  const TCHAR *Tag);
};
