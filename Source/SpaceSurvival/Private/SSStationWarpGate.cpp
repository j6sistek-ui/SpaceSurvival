#include "SSStationWarpGate.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "NiagaraComponent.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSShip.h"
#include "SSStation.h"

ASSStationWarpGate::ASSStationWarpGate()
{
    PrimaryActorTick.bCanEverTick = false;
    GateRoot = CreateDefaultSubobject<USceneComponent>(TEXT("GateRoot"));
    SetRootComponent(GateRoot);
    Frame = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Frame"));
    Frame->SetupAttachment(GateRoot);
    Frame->SetCollisionProfileName(UCollisionProfile::BlockAll_ProfileName);
    Frame->SetGenerateOverlapEvents(false);
    ActivationVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("ActivationVolume"));
    ActivationVolume->SetupAttachment(GateRoot);
    ActivationVolume->SetBoxExtent(FVector(100, 100, 120));
    ActivationVolume->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    ActivationVolume->SetCollisionResponseToAllChannels(ECR_Ignore);
    ActivationVolume->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    ActivationVolume->SetGenerateOverlapEvents(true);
    ArrivalPoint = CreateDefaultSubobject<USceneComponent>(TEXT("ArrivalPoint"));
    ArrivalPoint->SetupAttachment(GateRoot);
    PortalVisual = CreateDefaultSubobject<UNiagaraComponent>(TEXT("PortalVisual"));
    DepartureVisual = CreateDefaultSubobject<UNiagaraComponent>(TEXT("DepartureVisual"));
    ArrivalVisual = CreateDefaultSubobject<UNiagaraComponent>(TEXT("ArrivalVisual"));
    for (UNiagaraComponent *EffectComponent : {PortalVisual.Get(), DepartureVisual.Get(), ArrivalVisual.Get()})
    {
        EffectComponent->SetupAttachment(GateRoot);
        EffectComponent->SetAutoActivate(false);
        EffectComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        EffectComponent->PrimaryComponentTick.bTickEvenWhenPaused = false;
    }
}

void ASSStationWarpGate::BeginPlay()
{
    Super::BeginPlay();
    ActivationVolume->OnComponentBeginOverlap.AddDynamic(this, &ASSStationWarpGate::EnteredVolume);
    ActivationVolume->OnComponentEndOverlap.AddDynamic(this, &ASSStationWarpGate::LeftVolume);
    DepartureRestTransform = DepartureVisual->GetRelativeTransform();
    ArrivalRestTransform = ArrivalVisual->GetRelativeTransform();
    PortalVisual->SetAsset(PortalEffect);
    DepartureVisual->SetAsset(DepartureEffect);
    ArrivalVisual->SetAsset(ArrivalEffect);
    if (bEnabled && PortalEffect)
        PortalVisual->Activate(true);
}

bool ASSStationWarpGate::IsTransferPending() const
{
    return PendingWalker.IsValid() || IncomingSource.IsValid();
}

bool ASSStationWarpGate::Eligible(const ASSWalker *Walker, FString &Reason) const
{
    const UWorld *GateWorld = GetWorld();
    const auto *Destination = PairedGate.Get();
    const auto *Mode = GateWorld ? GateWorld->GetAuthGameMode<ASSGameMode>() : nullptr;
    const auto *Instance = GateWorld ? GateWorld->GetGameInstance<USSGameInstance>() : nullptr;
    const auto *Controller = Walker ? Cast<APlayerController>(Walker->GetController()) : nullptr;
    const auto *Ship = Mode ? Mode->GetPlayerShip() : nullptr;
    if (bEndingPlay || !bEnabled || !IsValid(Destination) || Destination == this || Destination->bEndingPlay ||
        !Destination->bEnabled || Destination->PairedGate != this || Destination->GetWorld() != GateWorld ||
        !IsValid(Station) || Station != Destination->Station || !Mode || Mode->GetStation() != Station || !Instance ||
        !Frame->GetStaticMesh() || !Destination->Frame->GetStaticMesh())
    {
        Reason = TEXT("This transport pair is unavailable.");
        return false;
    }
    if (!IsValid(Walker) || Walker->GetWorld() != GateWorld || !Controller || !Controller->IsLocalController() ||
        Controller->GetPawn() != Walker)
    {
        Reason = TEXT("Transport requires the walking pilot.");
        return false;
    }
    // FinishDocking stops the real parked ship's actor tick; BeginTakeoff enables it again.
    // IsMoored instead describes a depot stop during flight, not either station docking path.
    if (GateWorld->IsPaused() || Mode->IsMenuOpen() || Mode->IsDepartingStation() || !IsValid(Ship) ||
        Ship->GetWorld() != GateWorld || Ship->IsActorTickEnabled() || Ship->IsTakingOff() ||
        Ship->IsInWormholeTransit() || Walker->IsBoarding() || Walker->IsDisembarking() ||
        (!Mode->InHangar() && Instance->Session.run.phase != SS::Phase::Station))
    {
        Reason = TEXT("Transport is unavailable during a departure or menu transition.");
        return false;
    }
    const auto *Movement = Walker->GetCharacterMovement();
    const auto *Capsule = Walker->GetCapsuleComponent();
    FFindFloorResult Floor;
    if (!Movement || !Capsule || !Walker->GetActorEnableCollision() || !Capsule->IsQueryCollisionEnabled() ||
        !Movement->IsMovingOnGround())
    {
        Reason = TEXT("Stand on the pad before using transport.");
        return false;
    }
    Movement->FindFloor(Walker->GetActorLocation(), Floor, false);
    if (!Floor.IsWalkableFloor() || Floor.HitResult.bStartPenetrating)
    {
        Reason = TEXT("Stand on the pad before using transport.");
        return false;
    }
    return true;
}

bool ASSStationWarpGate::ResolveArrival(const ASSWalker *Walker, FVector &Location, FRotator &Facing) const
{
    if (!IsValid(Walker) || !ArrivalPoint || !GetWorld())
        return false;
    const auto *Capsule = Walker->GetCapsuleComponent();
    const auto *Movement = Walker->GetCharacterMovement();
    if (!Capsule || !Movement || !Capsule->IsQueryCollisionEnabled())
        return false;
    float Radius = 0.f, HalfHeight = 0.f;
    Capsule->GetScaledCapsuleSize(Radius, HalfHeight);
    const float FloorGap =
        .5f * (UCharacterMovementComponent::MIN_FLOOR_DIST + UCharacterMovementComponent::MAX_FLOOR_DIST);
    Location = ArrivalPoint->GetComponentLocation() + FVector(0, 0, HalfHeight + FloorGap);
    Facing = FRotator(0, ArrivalPoint->GetComponentRotation().Yaw, 0);
    if (Location.ContainsNaN() || Facing.ContainsNaN() || !FMath::IsFinite(Radius) || !FMath::IsFinite(HalfHeight) ||
        Radius <= 0.f || HalfHeight < Radius)
        return false;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSStationWarpArrival), false, Walker);
    if (GetWorld()->OverlapBlockingTestByProfile(Location, Capsule->GetComponentQuat(),
                                                 Capsule->GetCollisionProfileName(),
                                                 FCollisionShape::MakeCapsule(Radius, HalfHeight), Query))
        return false;
    FFindFloorResult Floor;
    Movement->FindFloor(Location, Floor, false);
    return Floor.IsWalkableFloor() && !Floor.HitResult.bStartPenetrating && Floor.GetDistanceToFloor() >= 0.f &&
           Floor.GetDistanceToFloor() <= UCharacterMovementComponent::MAX_FLOOR_DIST;
}

void ASSStationWarpGate::Refuse(ASSWalker *Walker, const FString &Reason)
{
    LastFailure = Reason;
    UE_LOG(LogTemp, Display, TEXT("SS_STATION_WARP_REFUSED gate=%s reason=%s"), *GetPathName(), *Reason);
    if (IsValid(Walker) && Walker->IsLocallyControlled())
        if (auto *Mode = GetWorld() ? GetWorld()->GetAuthGameMode<ASSGameMode>() : nullptr)
            Mode->Announce(Reason);
}

bool ASSStationWarpGate::AttachBurstToWalker(UNiagaraComponent *Visual, ASSWalker *Walker)
{
    USkeletalMeshComponent *BurstMesh = IsValid(Walker) ? Walker->GetMesh() : nullptr;
    if (!IsValid(Visual) || !IsValid(BurstMesh) || !BurstMesh->GetSkeletalMeshAsset() ||
        BurstMesh->GetOwner() != Walker || BurstMesh->GetWorld() != GetWorld() || !BurstMesh->IsRegistered() ||
        !Visual->AttachToComponent(BurstMesh, FAttachmentTransformRules::KeepWorldTransform))
    {
        UE_LOG(LogTemp, Warning, TEXT("SS_STATION_WARP_BURST_SKIPPED gate=%s reason=no live pilot mesh attachment"),
               *GetPathName());
        return false;
    }
    // The owned bursts use Default skeletal-source lookup, with no named user mesh parameter.
    // Keep the foot-space effect transform; the actual mesh parent supplies its animated skin.
    Walker->OnEndPlay.AddUniqueDynamic(this, &ASSStationWarpGate::BurstWalkerEndedPlay);
    return true;
}

void ASSStationWarpGate::RestoreBurst(UNiagaraComponent *Visual, const FTransform &RestTransform)
{
    if (!IsValid(Visual))
        return;
    USceneComponent *BurstParent = Visual->GetAttachParent();
    AActor *BurstSourceActor = BurstParent ? BurstParent->GetOwner() : nullptr;
    Visual->DeactivateImmediate();
    if (IsValid(Visual))
    {
        Visual->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
        if (IsValid(GateRoot) && Visual->AttachToComponent(GateRoot, FAttachmentTransformRules::KeepWorldTransform))
            Visual->SetRelativeTransform(RestTransform);
    }
    const auto StillSamples = [BurstSourceActor](const UNiagaraComponent *OtherVisual)
    {
        const USceneComponent *OtherParent = IsValid(OtherVisual) ? OtherVisual->GetAttachParent() : nullptr;
        return OtherParent && OtherParent->GetOwner() == BurstSourceActor;
    };
    if (IsValid(BurstSourceActor) && BurstSourceActor != this && !StillSamples(DepartureVisual) &&
        !StillSamples(ArrivalVisual))
        BurstSourceActor->OnEndPlay.RemoveDynamic(this, &ASSStationWarpGate::BurstWalkerEndedPlay);
}

void ASSStationWarpGate::BurstWalkerEndedPlay(AActor *Actor, EEndPlayReason::Type EndPlayReason)
{
    if (IsValid(DepartureVisual) && DepartureVisual->GetAttachParent() &&
        DepartureVisual->GetAttachParent()->GetOwner() == Actor)
        CancelTransfer(TEXT("Transport interrupted."));
    if (IsValid(ArrivalVisual) && ArrivalVisual->GetAttachParent() &&
        ArrivalVisual->GetAttachParent()->GetOwner() == Actor)
        StopArrivalVisual();
}

bool ASSStationWarpGate::TryActivate(ASSWalker *Walker)
{
    ReleaseLatchIfOutside();
    if (IsTransferPending() || LatchedWalker.IsValid() ||
        (IsValid(PairedGate) && (PairedGate->IsTransferPending() || PairedGate->LatchedWalker.IsValid())))
        return false;
    FString Reason;
    if (!Eligible(Walker, Reason))
    {
        Refuse(Walker, Reason);
        return false;
    }
    // Overlapping, separately authored pairs must not reserve the same pilot twice.
    for (TActorIterator<ASSStationWarpGate> Gate(GetWorld()); Gate; ++Gate)
    {
        ASSStationWarpGate *OtherGate = *Gate;
        if (!IsValid(OtherGate) || OtherGate == this || OtherGate == PairedGate)
            continue;
        OtherGate->ReleaseLatchIfOutside();
        if (OtherGate->PendingWalker.Get() == Walker || OtherGate->LatchedWalker.Get() == Walker)
        {
            Refuse(Walker, TEXT("Leave the previous transport pad before using another."));
            return false;
        }
    }
    FVector DestinationLocation;
    FRotator DestinationFacing;
    if (!ActivationVolume->IsOverlappingComponent(Walker->GetCapsuleComponent()) || !FMath::IsFinite(DepartureDelay) ||
        DepartureDelay < .1f || DepartureDelay > 5.f ||
        !PairedGate->ResolveArrival(Walker, DestinationLocation, DestinationFacing))
    {
        Refuse(Walker, TEXT("The transport destination is blocked or unsupported."));
        return false;
    }
    StopArrivalVisual();
    RestoreBurst(DepartureVisual, DepartureRestTransform);
    PendingWalker = LatchedWalker = Walker;
    PendingDestination = LatchPartner = PairedGate.Get();
    PairedGate->IncomingSource = this;
    PairedGate->LatchedWalker = Walker;
    PairedGate->LatchPartner = this;
    LastFailure.Empty();
    if (DepartureEffect)
    {
        DepartureVisual->SetWorldLocation(Walker->GetActorLocation() -
                                          FVector(0, 0, Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()));
        if (AttachBurstToWalker(DepartureVisual, Walker))
        {
            DepartureVisual->SetAsset(DepartureEffect);
            DepartureVisual->ReinitializeSystem();
            DepartureVisual->Activate(true);
        }
    }
    // Game-time timers and ordinary Niagara component ticks freeze with world pause.
    GetWorldTimerManager().SetTimer(DepartureTimer, this, &ASSStationWarpGate::CompleteTransfer, DepartureDelay, false);
    return true;
}

void ASSStationWarpGate::CompleteTransfer()
{
    ASSWalker *Walker = PendingWalker.Get();
    ASSStationWarpGate *Destination = PendingDestination.Get();
    FString Reason;
    if (!IsValid(Destination) || Destination != PairedGate || !Eligible(Walker, Reason) ||
        !ActivationVolume->IsOverlappingComponent(Walker->GetCapsuleComponent()))
    {
        CancelTransfer(Reason.IsEmpty() ? TEXT("Transport interrupted.") : Reason);
        return;
    }
    FVector Location;
    FRotator Facing;
    if (!Destination->ResolveArrival(Walker, Location, Facing))
    {
        CancelTransfer(TEXT("The transport destination is blocked or unsupported."));
        return;
    }
    auto *Controller = Cast<APlayerController>(Walker->GetController());
    const FRotator PreviousView = Controller->GetControlRotation();
    const TWeakObjectPtr<APlayerController> TransferController = Controller;
    const FString DestinationName = Destination->GetPathName();
    const FString WalkerName = Walker->GetPathName();
    // Kill and detach the departure skin BEFORE the pawn moves, including local-space particles.
    RestoreBurst(DepartureVisual, DepartureRestTransform);
    Controller = TransferController.Get();
    if (bEndingPlay || !IsValid(Walker) || !IsValid(Destination) || Destination->bEndingPlay || !IsValid(Controller) ||
        Controller->GetPawn() != Walker)
    {
        CancelTransfer(TEXT("Transport interrupted."));
        return;
    }
    bCompletingTransfer = true;
    const bool bMoved = Walker->TeleportTo(Location, Facing, false, true);
    // Teleport updates overlaps synchronously; an overlap callback can tear down either endpoint or possession.
    Controller = TransferController.Get();
    if (bMoved && !bEndingPlay && IsValid(Walker) && IsValid(Controller) && Controller->GetPawn() == Walker)
    {
        Walker->GetCharacterMovement()->StopMovementImmediately();
        Walker->ConsumeMovementInputVector();
        Controller->SetControlRotation(FRotator(PreviousView.Pitch, Facing.Yaw, PreviousView.Roll));
        if (IsValid(Destination) && !Destination->bEndingPlay && Destination->ArrivalEffect)
        {
            Destination->StopArrivalVisual();
            Destination->ArrivalVisual->SetWorldLocation(Destination->ArrivalPoint->GetComponentLocation());
            if (Destination->AttachBurstToWalker(Destination->ArrivalVisual, Walker))
            {
                Destination->ArrivalVisual->SetAsset(Destination->ArrivalEffect);
                Destination->ArrivalVisual->ReinitializeSystem();
                Destination->ArrivalVisual->Activate(true);
                const float DisplaySeconds = FMath::IsFinite(Destination->ArrivalDisplaySeconds)
                                                 ? FMath::Clamp(Destination->ArrivalDisplaySeconds, .1f, 10.f)
                                                 : 2.f;
                Destination->GetWorldTimerManager().SetTimer(Destination->ArrivalTimer, Destination,
                                                             &ASSStationWarpGate::StopArrivalVisual, DisplaySeconds,
                                                             false);
            }
        }
        UE_LOG(LogTemp, Display, TEXT("SS_STATION_WARP_ARRIVED source=%s destination=%s walker=%s"), *GetPathName(),
               *DestinationName, *WalkerName);
    }
    bCompletingTransfer = false;
    CancelTransfer(bMoved ? FString() : TEXT("Transport could not move the pilot."));
}

void ASSStationWarpGate::CancelTransfer(const FString &Reason)
{
    GetWorldTimerManager().ClearTimer(DepartureTimer);
    RestoreBurst(DepartureVisual, DepartureRestTransform);
    ASSWalker *Walker = PendingWalker.Get();
    if (auto *Destination = PendingDestination.Get(); Destination && Destination->IncomingSource == this)
        Destination->IncomingSource.Reset();
    PendingWalker.Reset();
    PendingDestination.Reset();
    if (!Reason.IsEmpty())
        Refuse(Walker, Reason);
    ReleaseLatchIfOutside();
}

void ASSStationWarpGate::ReleaseLatchIfOutside()
{
    if (IsTransferPending() || bCompletingTransfer)
        return;
    ASSWalker *Walker = LatchedWalker.Get();
    ASSStationWarpGate *Partner = LatchPartner.Get();
    if (Walker && (ActivationVolume->IsOverlappingActor(Walker) ||
                   (Partner && Partner->ActivationVolume->IsOverlappingActor(Walker))))
        return;
    if (Partner && Partner->LatchedWalker == LatchedWalker && !Partner->IsTransferPending())
    {
        Partner->LatchedWalker.Reset();
        Partner->LatchPartner.Reset();
    }
    LatchedWalker.Reset();
    LatchPartner.Reset();
}

void ASSStationWarpGate::EnteredVolume(UPrimitiveComponent *Component, AActor *OtherActor,
                                       UPrimitiveComponent *OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
                                       const FHitResult &SweepResult)
{
    if (auto *Walker = Cast<ASSWalker>(OtherActor);
        Walker && OtherComponent == Walker->GetCapsuleComponent() && Walker != LatchedWalker.Get())
        TryActivate(Walker);
}

void ASSStationWarpGate::LeftVolume(UPrimitiveComponent *Component, AActor *OtherActor,
                                    UPrimitiveComponent *OtherComponent, int32 OtherBodyIndex)
{
    if (auto *Walker = Cast<ASSWalker>(OtherActor); Walker && OtherComponent == Walker->GetCapsuleComponent())
    {
        if (Walker == PendingWalker.Get() && !bCompletingTransfer)
            CancelTransfer();
        ReleaseLatchIfOutside();
    }
}

void ASSStationWarpGate::StopArrivalVisual()
{
    GetWorldTimerManager().ClearTimer(ArrivalTimer);
    RestoreBurst(ArrivalVisual, ArrivalRestTransform);
}

void ASSStationWarpGate::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    bEndingPlay = true;
    if (auto *Source = IncomingSource.Get())
        Source->CancelTransfer(TEXT("Transport interrupted."));
    CancelTransfer();
    GetWorldTimerManager().ClearTimer(ArrivalTimer);
    StopArrivalVisual();
    PortalVisual->DeactivateImmediate();
    if (auto *Partner = LatchPartner.Get(); Partner && Partner->LatchPartner == this)
    {
        Partner->LatchedWalker.Reset();
        Partner->LatchPartner.Reset();
    }
    LatchedWalker.Reset();
    LatchPartner.Reset();
    ActivationVolume->OnComponentBeginOverlap.RemoveDynamic(this, &ASSStationWarpGate::EnteredVolume);
    ActivationVolume->OnComponentEndOverlap.RemoveDynamic(this, &ASSStationWarpGate::LeftVolume);
    Super::EndPlay(EndPlayReason);
}
