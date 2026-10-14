#pragma once
#include "CoreMinimal.h"

namespace SSStationTailFloor
{
/** Smallest upward swing that clears a conservative tail surface. The whole subtree rotates about
 *  its attached root; its local bend, lag and recoil are retained. Points already clear are untouched. */
inline FQuat ClearanceRotation(const TArray<FVector> &Points, const FVector &Root, const FVector &RestDirection,
                               const FPlane &Floor)
{
    if (Points.IsEmpty())
        return FQuat::Identity;
    auto Clears = [&](const FQuat &Rotation)
    {
        for (const FVector &Point : Points)
            if (Floor.PlaneDot(Root + Rotation.RotateVector(Point - Root)) < 0.)
                return false;
        return true;
    };
    if (Clears(FQuat::Identity))
        return FQuat::Identity;
    FVector Direction = FVector::ZeroVector;
    for (const FVector &Point : Points)
        Direction += Point - Root;
    const FVector Normal(Floor.X, Floor.Y, Floor.Z);
    FVector Horizontal = FVector::VectorPlaneProject(Direction, Normal).GetSafeNormal();
    if (Horizontal.IsNearlyZero())
        Horizontal = FVector::VectorPlaneProject(RestDirection, Normal).GetSafeNormal();
    const FVector Axis = FVector::CrossProduct(Horizontal, Normal).GetSafeNormal();
    if (Axis.IsNearlyZero())
        return FQuat::Identity;
    double Lower = 0.;
    // A hanging tail needs less than a quarter-turn to sweep onto the deck. Bound the search so an
    // invalid envelope cannot turn the tail through the character or start a per-frame solver loop.
    for (int32 Step = 1; Step <= 18; ++Step)
    {
        double Upper = FMath::DegreesToRadians(double(Step) * 5.);
        if (Clears(FQuat(Axis, Upper)))
        {
            for (int32 Iteration = 0; Iteration < 12; ++Iteration)
            {
                const double Mid = (Lower + Upper) * .5;
                if (Clears(FQuat(Axis, Mid)))
                    Upper = Mid;
                else
                    Lower = Mid;
            }
            return FQuat(Axis, Upper);
        }
        Lower = Upper;
    }
    return FQuat::Identity;
}
} // namespace SSStationTailFloor
