#include "SSLandingPad.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"

ASSLandingPad::ASSLandingPad()
{
    PrimaryActorTick.bCanEverTick = false;
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);
}
UStaticMeshComponent *ASSLandingPad::AddMesh(FVector Position, FVector Scale, const TCHAR *Mesh, const TCHAR *Material,
                                             bool Solid, const TCHAR *Tag)
{
    // The same shape as ASSStation::AddMesh, on purpose: a pad is built the way the station is built, so
    // the collision, the object type and the block-everything response are identical and a hero walking
    // from one onto the other never crosses a seam.
    auto *C = NewObject<UStaticMeshComponent>(this);
    C->SetupAttachment(Root);
    C->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, Mesh));
    if (Material)
        C->SetMaterial(0, LoadObject<UMaterialInterface>(nullptr, Material));
    C->SetRelativeLocation(Position);
    C->SetRelativeScale3D(Scale);
    C->SetCollisionEnabled(Solid ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
    C->SetCollisionObjectType(ECC_WorldStatic);
    C->SetCollisionResponseToAllChannels(ECR_Block);
    C->SetCanEverAffectNavigation(false);
    C->ComponentTags.Add(FName(Tag));
    C->RegisterComponent();
    return C;
}
void ASSLandingPad::Build()
{
    if (IsBuilt())
        return;
    const TCHAR *Cube = TEXT("/Engine/BasicShapes/Cube.Cube");
    const TCHAR *Hull = TEXT("/Game/SpaceSurvival/Materials/M_Hull.M_Hull");
    const TCHAR *Cyan = TEXT("/Game/SpaceSurvival/Materials/M_Cyan.M_Cyan");
    // The deck. A scaled unit cube hanging below the origin, so its top face is exactly the actor's
    // location and "put the ship on the pad" needs no arithmetic about slab centres. Solid, and tagged the
    // way the station tags its own structure, so a test that asks "is there a floor under this point"
    // gets the same kind of answer here as it does inside.
    Deck = AddMesh(FVector(0, 0, -DeckThickness * .5f),
                   FVector(HalfExtent * 2.f / 100.f, HalfExtent * 2.f / 100.f, DeckThickness / 100.f),
                   bCircularDeck ? TEXT("/Engine/BasicShapes/Cylinder.Cylinder") : Cube, Hull, true,
                   TEXT("StationLandingPad"));
    Deck->SetCastShadow(true);
    // The colony perimeter is a genuine walking guardrail. The bridge is the intended exit; a short
    // step-over kerb would let CharacterMovement walk straight off the circular deck into rescue.
    if (bCircularDeck)
    {
        for (int32 Index = 0; Index < 24; ++Index)
        {
            const float Angle = Index * 15.f;
            if (FMath::Abs(FRotator::NormalizeAxis(Angle)) <= 20.f)
                continue; // A clear opening wider than the eight metre bridge, facing pad-local +X.
            const float Radians = FMath::DegreesToRadians(Angle);
            const FVector Center(FMath::Cos(Radians) * (HalfExtent - 50.f), FMath::Sin(Radians) * (HalfExtent - 50.f),
                                 55.f);
            auto *Rail = AddMesh(Center, FVector(3.3f, .45f, 1.10f), Cube, Hull, true, TEXT("StationLandingKerb"));
            Rail->CanCharacterStepUpOn = ECB_No;
            Rail->SetRelativeRotation(FRotator(0, Angle + 90.f, 0));
            Dressing.Add(Rail);
            auto *Strip = AddMesh(Center + FVector(0, 0, 55.5f), FVector(3.2f, .10f, .01f), Cube, Cyan, false,
                                  TEXT("StationLandingRimLight"));
            Strip->SetRelativeRotation(FRotator(0, Angle + 90.f, 0));
            Dressing.Add(Strip);
        }
        // The first circular segment starts at30 degrees, well outside the bridge's +/-400cm floor.
        // Join its exact inner endpoint to the authored bridge guard at y+/-445, overlapping that
        // guard's pad-local x1610 start by50cm. Without these returns a walker can leave diagonally
        // through a263cm opening between the round perimeter and the straight bridge barriers.
        const float JoinAngle = FMath::DegreesToRadians(30.f), HalfRailLength = 165.f;
        const FVector ArcEnd(FMath::Cos(JoinAngle) * (HalfExtent - 50.f) + FMath::Sin(JoinAngle) * HalfRailLength,
                             FMath::Sin(JoinAngle) * (HalfExtent - 50.f) - FMath::Cos(JoinAngle) * HalfRailLength,
                             55.f);
        for (float Side : {-1.f, 1.f})
        {
            const FVector From(ArcEnd.X, Side * ArcEnd.Y, 55.f), To(HalfExtent + 60.f, Side * 445.f, 55.f);
            const FVector Center = (From + To) * .5f;
            const float Length = FVector::Distance(From, To);
            const FRotator Heading = (To - From).Rotation();
            auto *Return =
                AddMesh(Center, FVector(Length / 100.f, .45f, 1.10f), Cube, Hull, true, TEXT("StationLandingKerb"));
            Return->CanCharacterStepUpOn = ECB_No;
            Return->SetRelativeRotation(Heading);
            Dressing.Add(Return);
            auto *Strip = AddMesh(Center + FVector(0, 0, 55.5f), FVector((Length - 10.f) / 100.f, .10f, .01f), Cube,
                                  Cyan, false, TEXT("StationLandingRimLight"));
            Strip->SetRelativeRotation(Heading);
            Dressing.Add(Strip);
        }
    }
    else
        for (float Side : {-1.f, 1.f})
            Dressing.Add(AddMesh(FVector(0, Side * (HalfExtent - 60.f), 12.f),
                                 FVector(HalfExtent * 2.f / 100.f, 1.2f, .24f), Cube, Cyan, false,
                                 TEXT("StationLandingKerb")));
    // Where to put it down. A lit disc on the deck at the dock point, so a pilot can see where the ship
    // will end up before committing. The engine's own cylinder and the cyan the kerbs already use - no
    // new asset. Flattened rather than a plane so it reads from a low approach angle as well as from above.
    Indicator = AddMesh(FVector(0, 0, 3.f), FVector(18.f, 18.f, .04f), TEXT("/Engine/BasicShapes/Cylinder.Cylinder"),
                        Cyan, false, TEXT("StationPadIndicator"));
    for (UStaticMeshComponent *Plate : Dressing)
        Plate->SetCastShadow(false);
    Indicator->SetCastShadow(false);
}
bool ASSLandingPad::ConfigureWalkExit(const FBox &HullBounds, float CapsuleRadius, float CapsuleHalfHeight,
                                      const AActor *ParkedShip)
{
    ParkedHullBounds = HullBounds;
    if (!HullBounds.IsValid || !GetWorld() || !Deck)
        return false;
    const float Scale = GetActorScale3D().GetAbsMin();
    if (Scale <= UE_SMALL_NUMBER)
        return false;
    const float LocalRadius = CapsuleRadius / Scale;
    const float Edge = HalfExtent - LocalRadius - 60.f;
    const float X = FMath::Clamp(400.f, -Edge, Edge);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSPadExit), false, ParkedShip);
    const FCollisionObjectQueryParams StaticObjects(ECC_WorldStatic);
    // Neither the legacy +400 centreline spawn nor -350 side offset clears the Phoenix. Derive both
    // routes from the rendered hull, then require actual deck support and capsule clearance.
    for (const float Y : {float(HullBounds.Min.Y) - LocalRadius - 60.f, float(HullBounds.Max.Y) + LocalRadius + 60.f})
    {
        if (FMath::Abs(Y) > Edge)
            continue;
        const FVector Above = GetActorTransform().TransformPosition(FVector(X, Y, 300.f));
        FHitResult Floor;
        if (!GetWorld()->LineTraceSingleByObjectType(Floor, Above, Above - GetActorUpVector() * 600.f, StaticObjects,
                                                     Query) ||
            Floor.GetActor() != this || FVector::DotProduct(Floor.ImpactNormal, FVector::UpVector) < .7f)
            continue;
        const FVector Candidate = Floor.ImpactPoint + FVector::UpVector * (CapsuleHalfHeight + 2.5f);
        if (!Covers(Candidate, -LocalRadius - 60.f))
            continue;
        if (GetWorld()->OverlapBlockingTestByChannel(Candidate, FQuat::Identity, ECC_Pawn,
                                                     FCollisionShape::MakeCapsule(CapsuleRadius, CapsuleHalfHeight),
                                                     Query))
            continue;
        WalkSpawnOffset = ExitOffset = GetActorTransform().InverseTransformPosition(Candidate);
        return true;
    }
    return false;
}

bool ASSLandingPad::IsOutsideParkedHull(const FVector &World, float CapsuleRadius) const
{
    if (!ParkedHullBounds.IsValid)
        return false;
    const FVector Local = GetActorTransform().InverseTransformPosition(World);
    const float Radius = CapsuleRadius / FMath::Max(UE_SMALL_NUMBER, GetActorScale3D().GetAbsMin());
    return Local.X + Radius < ParkedHullBounds.Min.X || Local.X - Radius > ParkedHullBounds.Max.X ||
           Local.Y + Radius < ParkedHullBounds.Min.Y || Local.Y - Radius > ParkedHullBounds.Max.Y;
}

void ASSLandingPad::ShowIndicator(bool Visible)
{
    if (Indicator)
        Indicator->SetVisibility(Visible);
}
bool ASSLandingPad::IsIndicatorVisible() const
{
    return Indicator && Indicator->IsVisible();
}
