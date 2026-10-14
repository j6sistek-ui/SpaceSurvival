#include "SSStation.h"
#include "SSLandingPad.h"
#include "SSShip.h"
#include "SSShipVisualRig.h"
#include "SSStationWarpGate.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "PhysicsEngine/BodyInstance.h"
#include "PhysicsEngine/BodySetup.h"

namespace
{
struct FStationWarpPlacement
{
    FTransform FramePose;
    FVector ArrivalFloor = FVector::ZeroVector;
};
} // namespace

void ASSStation::DestroyWarpPair()
{
    ASSStationWarpGate *ShipGate = ShipWarpGate.Get();
    ASSStationWarpGate *WelcomeGate = WelcomeWarpGate.Get();
    ShipWarpGate = WelcomeWarpGate = nullptr;
    for (ASSStationWarpGate *Gate : {ShipGate, WelcomeGate})
        if (IsValid(Gate))
            Gate->Destroy();
}

bool ASSStation::InstallWarpPair(ASSShip *Ship, const ASSWalker *Walker)
{
    DestroyWarpPair();
    UWorld *StationWorld = GetWorld();
    const auto *Mode = StationWorld ? StationWorld->GetAuthGameMode<ASSGameMode>() : nullptr;
    const auto *Capsule = IsValid(Walker) ? Walker->GetCapsuleComponent() : nullptr;
    const auto *Movement = IsValid(Walker) ? Walker->GetCharacterMovement() : nullptr;
    const auto *Rig = IsValid(Ship) ? Ship->GetVisualRig() : nullptr;
    FTransform RampLanding;
    float RampHalfWidth = 0.f;
    // The optional pair is not manufactured for preview actors, legacy/classic hulls or an unlanded rig.
    if (!Mode || Mode->GetStation() != this || Mode->GetPlayerShip() != Ship || !IsUsingOutpost() || !IsValid(Ship) ||
        Ship->GetWorld() != StationWorld || Ship->IsActorTickEnabled() || Ship->IsTakingOff() ||
        Ship->IsInWormholeTransit() || !IsValid(Walker) || Walker->GetWorld() != StationWorld || !Capsule ||
        !Movement || !IsValid(LandingPad) || !LandingPad->GetDeck() || !Rig ||
        !Rig->GetParkedRampLanding(RampLanding, RampHalfWidth))
        return false;
    UStaticMesh *FrameMesh =
        LoadObject<UStaticMesh>(nullptr,
                                TEXT("/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_Door300X250_V1_Part1."
                                     "SM_Door300X250_V1_Part1"),
                                nullptr, LOAD_NoWarn | LOAD_Quiet);
    UNiagaraSystem *Portal = LoadObject<UNiagaraSystem>(
        nullptr, TEXT("/Game/ImportedLibrary/Portal/NS1_Portals/NS_NS1_TeleportPortal.NS_NS1_TeleportPortal"), nullptr,
        LOAD_NoWarn | LOAD_Quiet);
    UNiagaraSystem *Departure = LoadObject<UNiagaraSystem>(
        nullptr, TEXT("/Game/NiagaraExamples/FX_Player/NS_Player_Teleport_Out.NS_Player_Teleport_Out"), nullptr,
        LOAD_NoWarn | LOAD_Quiet);
    UNiagaraSystem *Arrival = LoadObject<UNiagaraSystem>(
        nullptr, TEXT("/Game/NiagaraExamples/FX_Player/NS_Player_Teleport_In.NS_Player_Teleport_In"), nullptr,
        LOAD_NoWarn | LOAD_Quiet);
    if (!FrameMesh || !FrameMesh->GetBodySetup() || !Portal || !Departure || !Arrival)
    {
        UE_LOG(LogTemp, Warning, TEXT("SS_STATION_WARP_PLACEMENT_REFUSED reason=owned frame/effects unavailable"));
        return false;
    }
    const UBodySetup *FrameBody = FrameMesh->GetBodySetup();
    if (FrameBody->AggGeom.GetElementCount() == 0 && FrameBody->CollisionTraceFlag != CTF_UseComplexAsSimple)
    {
        UE_LOG(LogTemp, Warning, TEXT("SS_STATION_WARP_PLACEMENT_REFUSED reason=original frame collision unconfirmed"));
        return false;
    }
    float Radius = 0.f, HalfHeight = 0.f;
    Capsule->GetScaledCapsuleSize(Radius, HalfHeight);
    const FBox FrameBounds = FrameMesh->GetBoundingBox();
    const FBox HullBounds = Rig->GetHullBoundsInSpace(RampLanding);
    const FVector FrameSize = FrameBounds.GetSize(), FrameCenter = FrameBounds.GetCenter();
    const float FloorGap =
        .5f * (UCharacterMovementComponent::MIN_FLOOR_DIST + UCharacterMovementComponent::MAX_FLOOR_DIST);
    if (!FrameBounds.IsValid || !HullBounds.IsValid || FrameSize.ContainsNaN() || !FMath::IsFinite(Radius) ||
        !FMath::IsFinite(HalfHeight) || Radius <= 0.f || HalfHeight < Radius || FrameSize.Y <= 2.f * Radius ||
        FrameSize.Z <= 2.f * HalfHeight + FloorGap || FrameSize.X <= 0.f)
        return false;
    const float Approach = FMath::Max(100.f + Radius + 60.f, float(FrameSize.X) * .5f + Radius + 60.f);
    FCollisionQueryParams GroundQuery(SCENE_QUERY_STAT(SSStationWarpGround), false, Walker);
    const auto GroundAt = [&](const FVector &Hint, FVector &Foot, const UPrimitiveComponent *Required = nullptr)
    {
        FHitResult Hit;
        if (!StationWorld->LineTraceSingleByChannel(Hit, Hint + FVector(0, 0, 200), Hint - FVector(0, 0, 400), ECC_Pawn,
                                                    GroundQuery) ||
            Hit.bStartPenetrating || !Movement->IsWalkable(Hit) || (Required && Hit.GetComponent() != Required))
            return false;
        Foot = Hit.ImpactPoint;
        return Walkable(Foot + FVector(0, 0, HalfHeight + FloorGap), Walker);
    };
    const auto MakePlacement =
        [&](const FVector &Hint, double Yaw, const UPrimitiveComponent *Required, FStationWarpPlacement &Placement)
    {
        FVector Foot;
        if (!GroundAt(Hint, Foot, Required))
            return false;
        Placement.FramePose = FTransform(FRotator(0, Yaw, 0), Foot - FVector(0, 0, FrameBounds.Min.Z));
        // Conservative empty space above the footprint; this is not a replacement collision shape.
        const FVector ClearExtent(FrameSize.X * .5f, FrameSize.Y * .5f, (FrameSize.Z - FloorGap) * .5f);
        const FVector ClearCenter = Placement.FramePose.TransformPosition(FrameCenter + FVector(0, 0, FloorGap * .5f));
        if (StationWorld->OverlapBlockingTestByChannel(ClearCenter, Placement.FramePose.GetRotation(), ECC_Pawn,
                                                       FCollisionShape::MakeBox(ClearExtent), GroundQuery))
            return false;
        for (const double SideY : {FrameBounds.Min.Y, FrameBounds.Max.Y})
        {
            FVector Support;
            const FVector Edge =
                Placement.FramePose.TransformPosition(FVector(FrameCenter.X, SideY, FrameBounds.Min.Z));
            if (!GroundAt(Edge, Support, Required) ||
                FMath::Abs(Support.Z - Foot.Z) > UCharacterMovementComponent::MAX_FLOOR_DIST)
                return false;
        }
        for (const float SideX : {-Approach, Approach})
        {
            FVector ApproachSupport;
            const FVector ApproachFoot =
                Placement.FramePose.TransformPosition(FVector(FrameCenter.X + SideX, FrameCenter.Y, FrameBounds.Min.Z));
            if (!GroundAt(ApproachFoot, ApproachSupport, Required) ||
                FMath::Abs(ApproachSupport.Z - Foot.Z) > UCharacterMovementComponent::MAX_FLOOR_DIST)
                return false;
            if (SideX > 0.f)
                Placement.ArrivalFloor = ApproachSupport;
        }
        return true;
    };
    FStationWarpPlacement WelcomePlacement, ShipPlacement;
    const FVector WelcomeHint = GetActorTransform().TransformPosition(FVector(5112, -912, 0));
    if (!MakePlacement(WelcomeHint, GetActorRotation().Yaw + 135.f, nullptr, WelcomePlacement))
    {
        UE_LOG(LogTemp, Warning, TEXT("SS_STATION_WARP_PLACEMENT_REFUSED reason=welcome footprint/support"));
        return false;
    }
    bool ShipPlaced = false;
    for (const float Side : {-1.f, 1.f})
    {
        const float HullSide = float(Side < 0.f ? -HullBounds.Min.Y : HullBounds.Max.Y);
        const float Offset = FMath::Max(RampHalfWidth + float(FrameSize.X) * .5f + Approach,
                                        HullSide + float(FrameSize.X) * .5f + Approach + Radius + 60.f);
        const FVector Hint = RampLanding.TransformPosition(FVector(0, Side * Offset, 0));
        const FVector Inward = -Side * RampLanding.GetUnitAxis(EAxis::Y);
        if (MakePlacement(Hint, Inward.Rotation().Yaw, LandingPad->GetDeck(), ShipPlacement))
        {
            ShipPlaced = true;
            break;
        }
    }
    if (!ShipPlaced)
    {
        UE_LOG(LogTemp, Warning, TEXT("SS_STATION_WARP_PLACEMENT_REFUSED reason=parked ramp side/support"));
        return false;
    }
    ShipWarpGate = StationWorld->SpawnActorDeferred<ASSStationWarpGate>(
        ASSStationWarpGate::StaticClass(), ShipPlacement.FramePose, this, nullptr,
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    WelcomeWarpGate = StationWorld->SpawnActorDeferred<ASSStationWarpGate>(
        ASSStationWarpGate::StaticClass(), WelcomePlacement.FramePose, this, nullptr,
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if (!ShipWarpGate || !WelcomeWarpGate)
    {
        DestroyWarpPair();
        return false;
    }
    const auto Configure =
        [&](ASSStationWarpGate *Gate, ASSStationWarpGate *Partner, const FStationWarpPlacement &Placement)
    {
        Gate->bEnabled = false;
        Gate->Station = this;
        Gate->PairedGate = Partner;
        Gate->Frame->SetStaticMesh(FrameMesh);
        Gate->PortalEffect = Portal;
        Gate->DepartureEffect = Departure;
        Gate->ArrivalEffect = Arrival;
        Gate->PortalVisual->SetRelativeLocation(FrameCenter);
        Gate->ArrivalPoint->SetRelativeLocation(Placement.FramePose.InverseTransformPosition(Placement.ArrivalFloor));
        Gate->ArrivalPoint->SetRelativeRotation(FRotator::ZeroRotator);
        Gate->ActivationVolume->SetRelativeLocation(
            FVector(FrameCenter.X, FrameCenter.Y, HalfHeight + FloorGap + FrameBounds.Min.Z));
        Gate->ActivationVolume->SetBoxExtent(FVector(100, Radius + 20.f, HalfHeight));
        Gate->ActivationVolume->SetGenerateOverlapEvents(false);
        Gate->DepartureVisual->SetUseAutoManageAttachment(false);
        Gate->ArrivalVisual->SetUseAutoManageAttachment(false);
    };
    Configure(ShipWarpGate, WelcomeWarpGate, ShipPlacement);
    Configure(WelcomeWarpGate, ShipWarpGate, WelcomePlacement);
    ShipWarpGate->FinishSpawning(ShipPlacement.FramePose);
    WelcomeWarpGate->FinishSpawning(WelcomePlacement.FramePose);
    for (ASSStationWarpGate *Gate : {ShipWarpGate.Get(), WelcomeWarpGate.Get()})
    {
        const FBodyInstance *FrameInstance = IsValid(Gate) ? Gate->Frame->GetBodyInstance() : nullptr;
        if (!IsValid(Gate) || !Gate->Frame->IsPhysicsStateCreated() || !Gate->Frame->IsQueryCollisionEnabled() ||
            !FrameInstance || !FrameInstance->IsValidBodyInstance() ||
            !Gate->AttachToComponent(RootComponent, FAttachmentTransformRules::KeepWorldTransform))
        {
            DestroyWarpPair();
            return false;
        }
        const FVector Foot = Gate->ArrivalPoint->GetComponentLocation();
        const FVector CapsuleLocation = Foot + FVector(0, 0, HalfHeight + FloorGap);
        FHitResult Hit;
        const FVector OtherSide = Gate->GetActorTransform().TransformPosition(
            FVector(FrameCenter.X - Approach, FrameCenter.Y, FrameBounds.Min.Z + HalfHeight + FloorGap));
        if (StationWorld->OverlapBlockingTestByProfile(CapsuleLocation, Capsule->GetComponentQuat(),
                                                       Capsule->GetCollisionProfileName(),
                                                       FCollisionShape::MakeCapsule(Radius, HalfHeight), GroundQuery) ||
            StationWorld->SweepSingleByProfile(Hit, CapsuleLocation, OtherSide, Capsule->GetComponentQuat(),
                                               Capsule->GetCollisionProfileName(),
                                               FCollisionShape::MakeCapsule(Radius, HalfHeight), GroundQuery))
        {
            UE_LOG(LogTemp, Warning, TEXT("SS_STATION_WARP_PLACEMENT_REFUSED gate=%s reason=frame passage/capsule"),
                   *Gate->GetPathName());
            DestroyWarpPair();
            return false;
        }
        FFindFloorResult Floor;
        Movement->FindFloor(CapsuleLocation, Floor, false);
        if (!Floor.IsWalkableFloor() || Floor.HitResult.bStartPenetrating || Floor.GetDistanceToFloor() < 0.f ||
            Floor.GetDistanceToFloor() > UCharacterMovementComponent::MAX_FLOOR_DIST)
        {
            DestroyWarpPair();
            return false;
        }
    }
    ShipWarpGate->bEnabled = WelcomeWarpGate->bEnabled = true;
    for (ASSStationWarpGate *Gate : {ShipWarpGate.Get(), WelcomeWarpGate.Get()})
    {
        Gate->ActivationVolume->SetGenerateOverlapEvents(true);
        Gate->PortalVisual->Activate(true);
    }
    UE_LOG(LogTemp, Display, TEXT("SS_STATION_WARP_PAIR_READY station=%s ship=%s welcome=%s"), *GetPathName(),
           *ShipWarpGate->GetActorLocation().ToString(), *WelcomeWarpGate->GetActorLocation().ToString());
    return true;
}
