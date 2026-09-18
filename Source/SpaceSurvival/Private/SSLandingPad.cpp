#include "SSLandingPad.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
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
                   FVector(HalfExtent * 2.f / 100.f, HalfExtent * 2.f / 100.f, DeckThickness / 100.f), Cube, Hull, true,
                   TEXT("StationLandingPad"));
    Deck->SetCastShadow(true);
    // Edge markers, so the pad reads as a pad from the air rather than as a grey square. Kept under the
    // 45 cm step height: anything taller is a wall the hero would have to climb to reach its own ship.
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
void ASSLandingPad::ShowIndicator(bool Visible)
{
    if (Indicator)
        Indicator->SetVisibility(Visible);
}
bool ASSLandingPad::IsIndicatorVisible() const
{
    return Indicator && Indicator->IsVisible();
}
