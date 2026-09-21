#pragma once
#include "CoreMinimal.h"

// Measured from the licensed Phoenix LOD0 imported vertices by PhoenixGearGeometry on 2026-09-21.
// Every listed vertex is rigidly weighted to this exact mesh bone. Units are bone-local (the
// authored skeleton carries a scale of 100); attaching in bone space preserves all gear animation.
// Individual part bounds leave the gaps between the three legs open. Never replace with a hull box.
// The geometry test recomputes these bounds against the real asset, so source changes cannot drift.
struct FSSPhoenixGearBounds
{
    const TCHAR *Bone;
    FVector Min, Max;
    int32 Vertices;
};

inline const FSSPhoenixGearBounds SSPhoenixGearBounds[] = {
    {TEXT("Chasis_Front_A_Mesh"), FVector(-0.228, -1.029, -0.252), FVector(0.228, 0.252, 0.252), 36},
    {TEXT("Chasis_Front_B_Mesh"), FVector(-0.635, -0.290, -1.683), FVector(0.000, 1.598, 0.290), 440},
    {TEXT("Chasis_Front_D_Mesh"), FVector(-0.673, -0.096, -0.186), FVector(0.000, 0.410, 0.424), 128},
    {TEXT("Chasis_Front_E_Mesh"), FVector(-0.604, -0.510, -1.059), FVector(0.000, 0.178, 0.132), 228},
    {TEXT("Chasis_Front_Leg_Mesh"), FVector(-0.461, -1.543, -0.741), FVector(0.461, 0.483, 0.174), 414},
    {TEXT("Chasis_Front_C_Mesh"), FVector(-0.130, -1.165, -0.039), FVector(0.130, 0.071, 1.734), 110},
    {TEXT("Chasis_Back_A_Left_Mesh"), FVector(-0.263, -0.874, -0.327), FVector(0.263, 0.758, 0.306), 26},
    {TEXT("Chasis_Back_B_Left_Mesh"), FVector(-0.375, -2.451, -1.639), FVector(0.375, 0.419, 0.409), 572},
    {TEXT("Chasis_Back_E_Left_Mesh"), FVector(-0.196, -0.424, -0.222), FVector(0.196, -0.001, 0.559), 68},
    {TEXT("Chasis_Back_C_Left_Mesh"), FVector(-0.356, -0.106, -0.039), FVector(0.356, 0.088, 1.158), 144},
    {TEXT("Chasis_Back_F_Left_Mesh"), FVector(-0.302, -0.360, -1.044), FVector(0.302, 0.149, 0.129), 218},
    {TEXT("Chasis_Back_Leg_Left_Mesh"), FVector(-0.642, -0.658, -0.845), FVector(0.659, 2.477, 0.340), 567},
    {TEXT("Chasis_Back_G_Left_Mesh"), FVector(-0.289, -0.143, -0.152), FVector(0.166, 0.119, 0.962), 74},
    {TEXT("Chasis_Back_G_Left_2_Mesh"), FVector(-0.159, -0.172, -1.032), FVector(0.159, 0.167, 0.092), 62},
    {TEXT("Chasis_Back_A_Right_Mesh"), FVector(-0.263, -0.874, -0.327), FVector(0.263, 0.758, 0.306), 26},
    {TEXT("Chasis_Back_C_Right_Mesh_2"), FVector(-0.375, -2.451, -1.639), FVector(0.375, 0.419, 0.409), 572},
    {TEXT("Chasis_Back_E_Right_Mesh"), FVector(-0.196, -0.424, -0.222), FVector(0.196, -0.001, 0.559), 68},
    {TEXT("Chasis_Back_C_Right_2_Mesh"), FVector(-0.356, -0.106, -0.039), FVector(0.356, 0.088, 1.158), 144},
    {TEXT("Chasis_Back_F_Right_Mesh"), FVector(-0.302, -0.360, -1.044), FVector(0.302, 0.149, 0.129), 218},
    {TEXT("Chasis_Back_Leg_Right_Mesh"), FVector(-0.659, -0.658, -0.845), FVector(0.642, 2.477, 0.340), 567},
    {TEXT("Chasis_Back_G_Right_Mesh"), FVector(-0.166, -0.143, -0.152), FVector(0.289, 0.119, 0.962), 74},
    {TEXT("Chasis_Back_G_Right_2_Mesh"), FVector(-0.159, -0.172, -1.032), FVector(0.159, 0.167, 0.092), 62},
    {TEXT("Chasis_Back_C_Left_2_Mesh"), FVector(-0.373, -0.120, -0.783), FVector(0.373, 0.112, 0.001), 56},
    {TEXT("Chasis_Back_C_2_Mesh"), FVector(-0.373, -0.120, -0.783), FVector(0.373, 0.112, 0.001), 56},
};
