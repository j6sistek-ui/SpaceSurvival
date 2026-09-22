#include "SSFlightHull.h"
#include "PhysicsEngine/BodySetup.h"

USSFlightHullComponent::USSFlightHullComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetMobility(EComponentMobility::Movable);
    SetCollisionObjectType(ECC_Pawn);
    SetCollisionResponseToAllChannels(ECR_Ignore);
    SetCollisionResponseToChannel(ECC_WorldStatic, ECR_Block);
    SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    SetGenerateOverlapEvents(false);
    SetNotifyRigidBodyCollision(true);
    SetCanEverAffectNavigation(false);
    BodyInstance.bAutoWeld = true;
    SetEnableGravity(false);
}

bool USSFlightHullComponent::Initialize(USSFlightHullProfile *InProfile)
{
    if (!InProfile || !InProfile->Body || InProfile->Body->AggGeom.ConvexElems.IsEmpty())
        return false;
    Profile = InProfile;
    ShapeBodySetup = Profile->Body;
    return true;
}
UBodySetup *USSFlightHullComponent::GetBodySetup()
{
    return Profile ? Profile->Body.Get() : nullptr;
}
void USSFlightHullComponent::UpdateBodySetup()
{
    ShapeBodySetup = GetBodySetup();
}
FPrimitiveSceneProxy *USSFlightHullComponent::CreateSceneProxy()
{
    return nullptr;
}
FBoxSphereBounds USSFlightHullComponent::CalcBounds(const FTransform &LocalToWorld) const
{
    return Profile && Profile->Body ? FBoxSphereBounds(Profile->Body->AggGeom.CalcAABB(LocalToWorld))
                                    : FBoxSphereBounds(LocalToWorld.GetLocation(), FVector::ZeroVector, 0.f);
}
bool USSFlightHullComponent::IsZeroExtent() const
{
    return !Profile || !Profile->Body || Profile->Body->AggGeom.ConvexElems.IsEmpty();
}
