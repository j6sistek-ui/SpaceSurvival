#include "SSBarCrew.h"
#include "SSStationSeat.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Engine/SkeletalMesh.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "SSGameMode.h"

ASSBarTable::ASSBarTable()
{
    Approach = CreateDefaultSubobject<USceneComponent>(TEXT("Approach"));
    RootComponent = Approach;
    Seat = CreateDefaultSubobject<USceneComponent>(TEXT("Seat"));
    Seat->SetupAttachment(Approach);
    DrinkContact = CreateDefaultSubobject<USceneComponent>(TEXT("DrinkContact"));
    DrinkContact->SetupAttachment(Approach);
    ServeFrom = CreateDefaultSubobject<USceneComponent>(TEXT("ServeFrom"));
    ServeFrom->SetupAttachment(Approach);
}

ASSBarCrew::ASSBarCrew()
{
    BarBanter = {{TEXT("Do these count as a staff meeting?"), TEXT("Only if we make one very important decision."),
                  TEXT("Ha! Another meeting tomorrow, then.")},
                 {TEXT("Someone said I light up the room."), TEXT("They were flirting, Astra."),
                  TEXT("Oh! I thought the ceiling panels were failing again.")},
                 {TEXT("To everybody who found their way home."), TEXT("And the ones taking the scenic route."),
                  TEXT("Ha! The cargo lift is not a scenic route.")},
                 {TEXT("I tried practicing my mysterious look."), TEXT("You asked three people if it was working."),
                  TEXT("Well, I needed reliable information!")},
                 {TEXT("You said this drink had a kick. I watched it very carefully."),
                  TEXT("And did it behave itself?"), TEXT("Ha! Perfectly. Not a single foot.")},
                 {TEXT("To the best bartender on this station."), TEXT("You say that every time, Astra."),
                  TEXT("And I have been right every time!")},
                 {TEXT("Why do people say break a leg for good luck?"), TEXT("No idea. Let us try cheers instead."),
                  TEXT("Ha! Much cheaper for the medical bay.")},
                 {TEXT("I saved you the good glass."), TEXT("They are all the same glass."),
                  TEXT("Not anymore. That one has a compliment now.")}};
    Eyes = CreateDefaultSubobject<UPoseableMeshComponent>(TEXT("Eyes"));
    Eyes->SetupAttachment(CharacterMesh, TEXT("head"));
    Eyes->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Corset = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Corset"));
    Shorts = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Shorts"));
    for (auto *Part : {Corset.Get(), Shorts.Get()})
    {
        Part->SetupAttachment(CharacterMesh);
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
    Glass = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Glass"));
    Bottle = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Bottle"));
    ServedGlass = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ServedGlass"));
    ServingTray = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ServingTray"));
    for (auto *Prop : {Glass.Get(), Bottle.Get(), ServedGlass.Get(), ServingTray.Get()})
    {
        Prop->SetupAttachment(CharacterMesh);
        Prop->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Prop->SetVisibility(false);
    }
}

void ASSBarCrew::ConfigureParts()
{
    if (Eyes->GetSkinnedAsset() && CharacterMesh->DoesSocketExist(TEXT("head")))
        Eyes->AttachToComponent(CharacterMesh, FAttachmentTransformRules::KeepRelativeTransform, TEXT("head"));
    for (auto *Part : {Corset.Get(), Shorts.Get()})
        Part->SetLeaderPoseComponent(CharacterMesh, true);
    Glass->AttachToComponent(CharacterMesh, FAttachmentTransformRules::KeepRelativeTransform, GlassHand);
    Glass->SetRelativeTransform(GlassGrip);
    Bottle->AttachToComponent(CharacterMesh, FAttachmentTransformRules::KeepRelativeTransform, BottleHand);
    Bottle->SetRelativeTransform(BottleGrip);
    ServingTray->AttachToComponent(CharacterMesh, FAttachmentTransformRules::KeepRelativeTransform, TrayHand);
    ServingTray->SetRelativeTransform(TrayGrip);
    ServingTray->SetVisibility(false);
    bUsingServingTray = false;
    bUsingTableSetDown = bGlassPickedUp = bGlassReleased = false;
    bUsingCounterPickup = bCounterPickedUp = bCounterPlacedOnTray = false;
}

bool ASSBarCrew::CanUseServingTray() const
{
    const auto *Mesh = CharacterMesh->GetSkeletalMeshAsset();
    return !bIsBartender && ServingTray->GetStaticMesh() && Mesh && CharacterMesh->DoesSocketExist(TrayHand) &&
           TrayCarryAnimation && TrayServeAnimation && Mesh->GetSkeleton() == TrayCarryAnimation->GetSkeleton() &&
           Mesh->GetSkeleton() == TrayServeAnimation->GetSkeleton();
}

void ASSBarCrew::BeginCarryingDrink()
{
    ConfigureParts();
    bUsingServingTray = CanUseServingTray();
    UAnimSequence *CarryClip = bUsingServingTray ? TrayCarryAnimation.Get() : CarryAnimation.Get();
    PlayService(CarryClip ? CarryClip : WalkAnimation.Get(), true);
    if (bUsingServingTray)
    {
        Glass->AttachToComponent(ServingTray, FAttachmentTransformRules::KeepRelativeTransform);
        Glass->SetRelativeTransform(TrayGlassPlacement);
        ServingTray->SetVisibility(true);
    }
    Glass->SetVisibility(true);
}

bool ASSBarCrew::CanSetDownAtTable() const
{
    const auto *Mesh = CharacterMesh->GetSkeletalMeshAsset();
    return bUsingServingTray && DeliveryTable.IsValid() && DeliveryTable->bHasSetDownPose && TraySetDownAnimation &&
           Mesh && Mesh->GetSkeleton() == TraySetDownAnimation->GetSkeleton() &&
           CharacterMesh->DoesSocketExist(DrinkHand) && FMath::IsFinite(TraySetDownWindow.X) &&
           FMath::IsFinite(TraySetDownWindow.Y) && TraySetDownWindow.X > 0 &&
           TraySetDownWindow.Y > TraySetDownWindow.X && TraySetDownWindow.Y < TraySetDownAnimation->GetPlayLength();
}

bool ASSBarCrew::CanUseCounterPickup() const
{
    if (!CanUseServingTray() || !IsValid(Bartender) || !Bartender->bIsBartender || !TrayPickupAnimation ||
        !Bartender->CounterDeliveryAnimation)
        return false;
    const auto *Mesh = CharacterMesh->GetSkeletalMeshAsset();
    const auto *OtherMesh = Bartender->CharacterMesh->GetSkeletalMeshAsset();
    return Mesh && OtherMesh && Mesh->GetSkeleton() == TrayPickupAnimation->GetSkeleton() &&
           OtherMesh->GetSkeleton() == Bartender->CounterDeliveryAnimation->GetSkeleton() &&
           CharacterMesh->DoesSocketExist(DrinkHand) &&
           Bartender->CharacterMesh->DoesSocketExist(Bartender->GlassHand) && FMath::IsFinite(TrayReadySeconds) &&
           FMath::IsFinite(TrayPickupWindow.X) && FMath::IsFinite(TrayPickupWindow.Y) && TrayReadySeconds >= 0 &&
           TrayReadySeconds < TrayPickupWindow.X && TrayPickupWindow.Y > TrayPickupWindow.X &&
           TrayPickupWindow.Y < TrayPickupAnimation->GetPlayLength() &&
           FMath::IsFinite(Bartender->CounterReleaseSeconds) && Bartender->CounterReleaseSeconds > 0 &&
           Bartender->CounterReleaseSeconds < Bartender->CounterDeliveryAnimation->GetPlayLength() &&
           !Bartender->CounterGlassTransform.ContainsNaN();
}

void ASSBarCrew::ReleaseBarReservation()
{
    if (IsValid(Bartender) && Bartender->ReservedBy == this)
    {
        Bartender->ServedGlass->SetVisibility(false);
        Bartender->bUsingCounterDelivery = false;
        Bartender->ReservedBy.Reset();
    }
}

void ASSBarCrew::BeginReturnFromBar()
{
    ReleaseBarReservation();
    BeginCarryingDrink();
    bGlassPickedUp = bGlassReleased = false;
    bUsingTableSetDown = CanSetDownAtTable();
    const FVector GuestPosition = ServiceGuest->GetActorLocation();
    FVector Destination = bUsingTableSetDown
                              ? DeliveryTable->ServeFrom->GetComponentLocation()
                              : GuestPosition + (GetActorLocation() - GuestPosition).GetSafeNormal2D() * 110.f;
    Destination.Z = GetActorLocation().Z;
    if (PlanPath(Destination))
        SetState(ESSBarServiceState::ReturningToGuest, TEXT("carrying the guest's drink back from the bar"));
    else
        ReturnHome(TEXT("I cannot reach your table. Please clear the aisle."));
}

void ASSBarCrew::PlaceServedGlass()
{
    if (!DeliveryTable.IsValid())
        return;
    ServedGlass->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
    ServedGlass->SetWorldTransform(DeliveryTable->DrinkContact->GetComponentTransform());
    ServedGlass->SetWorldScale3D(bUsingServingTray ? TrayGlassPlacement.GetScale3D() : GlassGrip.GetScale3D());
    ServedGlass->SetVisibility(true);
    bGlassReleased = true;
}

void ASSBarCrew::OnConstruction(const FTransform &Transform)
{
    Super::OnConstruction(Transform);
    ConfigureParts();
}

void ASSBarCrew::BeginPlay()
{
    Super::BeginPlay();
    Home = GetActorTransform();
    ResetBarBreakTimer();
    ConfigureParts();
    ServiceClip = IdleAnimation;
    // Evaluate the newly selected service pose before updating hand-attached props.
    if (!bIsBartender)
        CharacterMesh->AddTickPrerequisiteActor(this);
}

void ASSBarCrew::ReleaseTable()
{
    if (Table.IsValid() && Table->Occupant == this)
        Table->Occupant.Reset();
    Table.Reset();
}

void ASSBarCrew::EndPlay(const EEndPlayReason::Type Reason)
{
    ReleaseTable();
    ReleaseBarReservation();
    Super::EndPlay(Reason);
}

void ASSBarCrew::ApplyWorldOffset(const FVector &Offset, bool bWorldShift)
{
    Super::ApplyWorldOffset(Offset, bWorldShift);
    Home.AddToTranslation(Offset);
    GuestOrigin += Offset;
    for (auto &Point : Path)
        Point += Offset;
}

void ASSBarCrew::PlayService(UAnimSequence *Clip, bool bLoop, bool bRestart)
{
    const auto *Mesh = CharacterMesh->GetSkeletalMeshAsset();
    if (!Mesh || !Clip || Mesh->GetSkeleton() != Clip->GetSkeleton())
        return;
    if (ServiceClip == Clip && !bRestart)
        return;
    CharacterMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    CharacterMesh->PlayAnimation(Clip, bLoop);
    ServiceClip = Clip;
}

void ASSBarCrew::SetState(ESSBarServiceState State, const FString &Activity)
{
    ServiceState = State;
    StateTime = 0;
    BlockedTime = 0;
    TalkActivity = Activity;
}

bool ASSBarCrew::IsActionPlaying() const
{
    return bIsBartender ? Super::IsActionPlaying() : ServiceState != ESSBarServiceState::Available;
}

bool ASSBarCrew::TriggerAction(int32 Index)
{
    if (!Actions.IsValidIndex(Index))
        return false;
    if (!bIsBartender)
    {
        const bool bAccepted = RequestService(Index, UGameplayStatics::GetPlayerPawn(this, 0));
        if (!bAccepted && !ServiceNotice.IsEmpty())
            if (auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>())
                GM->SpeakCrewLine(this, ServiceNotice);
        return bAccepted;
    }
    if (ReservedBy.IsValid() || !Super::TriggerAction(Index))
        return false;
    BarAction = Index;
    return true;
}

bool ASSBarCrew::BeginPour(ASSBarCrew *Waitress)
{
    if (!bIsBartender || !IsValid(Waitress) || ReservedBy.IsValid() || Super::IsActionPlaying())
        return false;
    const bool bCounter = Waitress->bUsingCounterPickup && Waitress->CanUseCounterPickup();
    if (!TriggerActionClip(0, bCounter ? CounterDeliveryAnimation.Get() : nullptr))
        return false;
    bUsingCounterDelivery = bCounter;
    bCounterGlassReleased = false;
    ServedGlass->SetVisibility(false);
    if (bCounter)
    {
        ServedGlass->SetStaticMesh(Glass->GetStaticMesh());
        for (int32 I = 0; I < Glass->GetNumMaterials(); ++I)
            ServedGlass->SetMaterial(I, Glass->GetMaterial(I));
    }
    ReservedBy = Waitress;
    BarAction = 0;
    if (auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>())
        GM->SpeakCrewLine(this, TEXT("One for your table, coming right up."));
    return true;
}

ASSBarTable *ASSBarCrew::FindTable(APawn *Guest) const
{
    ASSBarTable *Best = nullptr;
    float Distance = FMath::Square(300.f);
    for (TActorIterator<ASSBarTable> It(GetWorld()); It; ++It)
    {
        if (It->Occupant.IsValid() && It->Occupant != this)
            continue;
        bool HeroInPlace = false;
        for (TActorIterator<ASSStationSeat> Seat(GetWorld()); Seat; ++Seat)
            if (Seat->Occupant.IsValid() &&
                FVector::DistSquared2D(Seat->GetActorLocation(), It->Seat->GetComponentLocation()) <
                    FMath::Square(55.f))
                HeroInPlace = true;
        if (HeroInPlace)
            continue;
        const float Candidate = FVector::DistSquared2D(Guest->GetActorLocation(), It->GetActorLocation());
        if (Candidate < Distance)
        {
            Best = *It;
            Distance = Candidate;
        }
    }
    return Best;
}

bool ASSBarCrew::PlanPath(const FVector &Destination)
{
    // A small authored visibility graph: never teleport through counters or walk across a missing deck.
    TArray<FVector> Nodes = {GetActorLocation(), Destination};
    for (const auto &Point : ServiceWaypoints)
        Nodes.Add(Home.TransformPosition(Point));
    FCollisionQueryParams Query(SCENE_QUERY_STAT(BarServiceRoute), false, this);
    if (ServiceGuest.IsValid() && !bUsingTableSetDown)
        Query.AddIgnoredActor(ServiceGuest.Get());
    const FCollisionShape Shape =
        FCollisionShape::MakeCapsule(Body->GetScaledCapsuleRadius(), Body->GetScaledCapsuleHalfHeight() - 6.f);
    TArray<float> Cost;
    TArray<int32> Previous;
    TArray<bool> Visited;
    Cost.Init(TNumericLimits<float>::Max(), Nodes.Num());
    Previous.Init(INDEX_NONE, Nodes.Num());
    Visited.Init(false, Nodes.Num());
    Cost[0] = 0;
    for (int32 Pass = 0; Pass < Nodes.Num(); ++Pass)
    {
        int32 Current = INDEX_NONE;
        for (int32 I = 0; I < Nodes.Num(); ++I)
            if (!Visited[I] && (Current == INDEX_NONE || Cost[I] < Cost[Current]))
                Current = I;
        if (Current == INDEX_NONE || Cost[Current] == TNumericLimits<float>::Max())
            break;
        if (Current == 1)
            break;
        Visited[Current] = true;
        for (int32 I = 0; I < Nodes.Num(); ++I)
        {
            if (Visited[I] || I == Current)
                continue;
            FHitResult Hit;
            if (GetWorld()->SweepSingleByChannel(Hit, Nodes[Current], Nodes[I], FQuat::Identity, ECC_Pawn, Shape,
                                                 Query))
                continue;
            const float Candidate = Cost[Current] + FVector::Distance(Nodes[Current], Nodes[I]);
            if (Candidate < Cost[I])
            {
                Cost[I] = Candidate;
                Previous[I] = Current;
            }
        }
    }
    Path.Reset();
    PathIndex = 0;
    if (Previous[1] == INDEX_NONE)
        return false;
    for (int32 I = 1; I != 0; I = Previous[I])
        Path.Insert(Nodes[I], 0);
    return true;
}

bool ASSBarCrew::MoveAlongPath(float Dt)
{
    if (!Path.IsValidIndex(PathIndex))
        return true;
    const FVector Delta = Path[PathIndex] - GetActorLocation();
    const bool bContactApproach =
        PathIndex == Path.Num() - 1 && ((bUsingTableSetDown && ServiceState == ESSBarServiceState::ReturningToGuest) ||
                                        (bUsingCounterPickup && ServiceState == ESSBarServiceState::GoingToBar));
    if (Delta.Size2D() < (bContactApproach ? 1.f : 10.f))
        return ++PathIndex >= Path.Num();
    FVector Next = GetActorLocation() + Delta.GetSafeNormal2D() * FMath::Min(Delta.Size2D(), TravelSpeed * Dt);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(BarServiceFloor), false, this);
    FHitResult Floor;
    const bool bGround =
        GetWorld()->LineTraceSingleByObjectType(Floor, Next + FVector(0, 0, 60), Next - FVector(0, 0, 160),
                                                FCollisionObjectQueryParams(ECC_WorldStatic), Query);
    const FVector Before = GetActorLocation();
    if (bGround && Floor.ImpactNormal.Z > .7f)
    {
        Next.Z = Floor.ImpactPoint.Z + Body->GetScaledCapsuleHalfHeight() + 2.f;
        SetActorLocation(Next, true);
    }
    if (FVector::DistSquared(Before, GetActorLocation()) < .01f)
        BlockedTime += Dt;
    else
        BlockedTime = 0;
    SetActorRotation(FMath::RInterpTo(GetActorRotation(), FRotator(0, Delta.Rotation().Yaw, 0), Dt, 5.f));
    UAnimSequence *CarryClip = bUsingServingTray ? TrayCarryAnimation.Get() : CarryAnimation.Get();
    PlayService(Glass->IsVisible() && CarryClip ? CarryClip : WalkAnimation.Get(), true);
    if (BlockedTime > 3.f || StateTime > 60.f)
        ReturnHome(TEXT("The route is blocked. Please give me a little room."));
    return false;
}

void ASSBarCrew::ReturnHome(const FString &Reason)
{
    bBarBreakActive = false;
    ResetBarBreakTimer();
    if (ServiceState == ESSBarServiceState::Seated && Table.IsValid())
        SetActorTransform(Table->Approach->GetComponentTransform());
    Body->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    ReleaseTable();
    ReleaseBarReservation();
    ServiceGuest.Reset();
    DeliveryTable.Reset();
    Glass->SetVisibility(false);
    ConfigureParts();
    ServiceNotice = Reason;
    if (ServiceState != ESSBarServiceState::ReturningHome && PlanPath(Home.GetLocation()))
        SetState(ESSBarServiceState::ReturningHome, TEXT("returning to the bar service area"));
    else
    {
        Path.Reset();
        SetState(ESSBarServiceState::Available, TEXT("available to take a drink order"));
        PlayService(IdleAnimation, true);
    }
}

bool ASSBarCrew::RequestService(int32 Index, APawn *Guest)
{
    ServiceNotice.Empty();
    if (bBarBreakActive && IsValid(Guest) &&
        FVector::DistSquared(GetActorLocation(), Guest->GetActorLocation()) < FMath::Square(400.f))
    {
        ReturnHome(TEXT("One moment, I am coming right over."));
        return Index == 3;
    }
    if (bIsBartender || !IsValid(Guest) || Index < 0 || Index > 3 ||
        FVector::DistSquared(GetActorLocation(), Guest->GetActorLocation()) > FMath::Square(400.f))
        return false;
    if (Index == 3)
    {
        if (ServiceGuest.IsValid() && ServiceGuest != Guest)
            return false;
        ReturnHome(TEXT("Of course. Call me when you need me."));
        return true;
    }
    if (ServiceState != ESSBarServiceState::Available)
    {
        ServiceNotice = TEXT("I will be right with you when this order is finished.");
        return false;
    }
    ServiceGuest = Guest;
    GuestOrigin = Guest->GetActorLocation();
    if (Index == 2)
    {
        auto *Nearby = FindTable(Guest);
        if (!Nearby || !SeatedAnimation || !PlanPath(Nearby->Approach->GetComponentLocation()))
        {
            ServiceGuest.Reset();
            ServiceNotice = TEXT("Meet me beside an available table.");
            return false;
        }
        Table = Nearby;
        Nearby->Occupant = this;
        SetState(ESSBarServiceState::JoiningTable, TEXT("joining the guest at their table"));
        return true;
    }
    if (!IsValid(Bartender) || !Bartender->bIsBartender || !CarryAnimation || !ServeAnimation ||
        (Index == 1 && !DrinkAnimation) || !PlanPath(Bartender->GetActorTransform().TransformPosition(PickupOffset)))
    {
        ServiceGuest.Reset();
        ServiceNotice = TEXT("I cannot reach the bar just now.");
        return false;
    }
    DeliveryTable = FindTable(Guest);
    if (!DeliveryTable.IsValid())
    {
        ServiceGuest.Reset();
        ServiceNotice = TEXT("Choose a nearby table, and I will bring your drink over.");
        return false;
    }
    ServedGlass->SetVisibility(false);
    bDrinkTogether = Index == 1;
    bUsingCounterPickup = CanUseCounterPickup();
    bCounterPickedUp = bCounterPlacedOnTray = false;
    SetState(ESSBarServiceState::GoingToBar, TEXT("collecting the guest's drink from Joy"));
    return true;
}

void ASSBarCrew::Tick(float Dt)
{
    if (bIsBartender)
    {
        Super::Tick(Dt);
        const float Position = CharacterMesh->GetPosition();
        const FVector2D Window = BarAction == 0 ? PourPropWindow : CheersPropWindow;
        const bool bVisible = Super::IsActionPlaying() && Position >= Window.X && Position <= Window.Y;
        Glass->AttachToComponent(CharacterMesh, FAttachmentTransformRules::KeepRelativeTransform,
                                 BarAction == 1 ? DrinkHand : GlassHand);
        const bool bStaffToast = BarAction == 1 && ReservedBy.IsValid() && ReservedBy->bBarBreakActive;
        Glass->SetRelativeTransform(bStaffToast ? BarShotGrip() : (BarAction == 1 ? DrinkGrip : GlassGrip));
        Bottle->SetVisibility(bVisible && BarAction == 0);
        if (bUsingCounterDelivery && ReservedBy.IsValid() && !bCounterGlassReleased && Super::IsActionPlaying() &&
            Position >= CounterReleaseSeconds)
        {
            ServedGlass->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
            ServedGlass->SetWorldTransform(CounterGlassTransform * GetActorTransform());
            ServedGlass->SetWorldScale3D(GlassGrip.GetScale3D());
            ServedGlass->SetVisibility(true);
            bCounterGlassReleased = true;
        }
        Glass->SetVisibility(bVisible && (BarAction == 0 || BarAction == 1) &&
                             !(bUsingCounterDelivery && bCounterGlassReleased));
        return;
    }
    AActor::Tick(Dt);
    if (Dt <= 0)
        return;
    StateTime += Dt;
    if (TickBarBreak(Dt))
        return;
    if (ServiceState != ESSBarServiceState::Available && ServiceState != ESSBarServiceState::ReturningHome &&
        (!ServiceGuest.IsValid() ||
         FVector::DistSquared2D(ServiceGuest->GetActorLocation(), GuestOrigin) > FMath::Square(GuestDepartureDistance)))
    {
        ReturnHome(TEXT("The guest has left the table."));
        return;
    }
    switch (ServiceState)
    {
    case ESSBarServiceState::GoingToBar:
        if (!IsValid(Bartender))
            ReturnHome(TEXT("The bartender is unavailable."));
        else if (MoveAlongPath(Dt))
        {
            SetActorRotation(FRotator(0, (Bartender->GetActorLocation() - GetActorLocation()).Rotation().Yaw, 0));
            PlayService(IdleAnimation, true);
            SetState(ESSBarServiceState::WaitingForBar, TEXT("asking Joy to prepare the guest's drink"));
            if (auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>())
                GM->SpeakCrewLine(this, TEXT("Joy, a drink for my table, please."));
        }
        break;
    case ESSBarServiceState::WaitingForBar:
        if (!IsValid(Bartender) || StateTime > 40.f)
            ReturnHome(TEXT("The bar is busy. Please try again shortly."));
        else if (Bartender->ReservedBy == this && !Bartender->IsActionPlaying())
        {
            if (bUsingCounterPickup && CanUseCounterPickup() && Bartender->ServedGlass->IsVisible())
            {
                bUsingServingTray = true;
                PlayService(TrayPickupAnimation, false, true);
                SetState(ESSBarServiceState::CollectingDrink, TEXT("collecting the drink from the counter"));
            }
            else
                BeginReturnFromBar();
        }
        else if (StateTime >= 2.5f && !Bartender->ReservedBy.IsValid())
            Bartender->BeginPour(this);
        break;
    case ESSBarServiceState::CollectingDrink:
        if (!IsValid(Bartender) || Bartender->ReservedBy != this || !CanUseCounterPickup())
        {
            ReturnHome(TEXT("The bar pickup is no longer available."));
            break;
        }
        {
            const float Position = CharacterMesh->GetPosition();
            ServingTray->SetVisibility(Position >= TrayReadySeconds);
            if (!bCounterPickedUp && Position >= TrayPickupWindow.X)
            {
                Glass->AttachToComponent(CharacterMesh, FAttachmentTransformRules::KeepRelativeTransform, DrinkHand);
                Glass->SetRelativeTransform(DrinkGrip);
                Glass->SetVisibility(true);
                Bartender->ServedGlass->SetVisibility(false);
                bCounterPickedUp = true;
            }
            if (!bCounterPlacedOnTray && Position >= TrayPickupWindow.Y)
            {
                Glass->AttachToComponent(ServingTray, FAttachmentTransformRules::KeepRelativeTransform);
                Glass->SetRelativeTransform(TrayGlassPlacement);
                bCounterPlacedOnTray = true;
            }
            if (StateTime >= TrayPickupAnimation->GetPlayLength())
                BeginReturnFromBar();
        }
        break;
    case ESSBarServiceState::ReturningToGuest:
        if (bUsingTableSetDown && !DeliveryTable.IsValid())
        {
            ReturnHome(TEXT("The table is no longer available."));
            break;
        }
        if (MoveAlongPath(Dt))
        {
            SetActorRotation(FRotator(0,
                                      bUsingTableSetDown
                                          ? DeliveryTable->ServeFrom->GetComponentRotation().Yaw
                                          : (ServiceGuest->GetActorLocation() - GetActorLocation()).Rotation().Yaw,
                                      0));
            PlayService(bUsingTableSetDown  ? TraySetDownAnimation.Get()
                        : bUsingServingTray ? TrayServeAnimation.Get()
                                            : ServeAnimation.Get(),
                        false, true);
            SetState(ESSBarServiceState::Serving, bUsingTableSetDown ? TEXT("setting the drink on the table")
                                                                     : TEXT("offering the guest their drink"));
            if (auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>())
                GM->SpeakCrewLine(this, TEXT("Here you are. Enjoy."));
        }
        break;
    case ESSBarServiceState::Serving:
        if (!DeliveryTable.IsValid())
        {
            ReturnHome(TEXT("The table is no longer available."));
            break;
        }
        if (!ServiceClip.IsValid())
        {
            ReturnHome(TEXT("The serving animation is unavailable."));
            break;
        }
        if (bUsingTableSetDown)
        {
            const float PoseTime = CharacterMesh->GetPosition();
            if (!bGlassPickedUp && PoseTime >= TraySetDownWindow.X)
            {
                Glass->AttachToComponent(CharacterMesh, FAttachmentTransformRules::KeepRelativeTransform, DrinkHand);
                Glass->SetRelativeTransform(DrinkGrip);
                bGlassPickedUp = true;
            }
            if (!bGlassReleased && PoseTime >= TraySetDownWindow.Y)
            {
                PlaceServedGlass();
                Glass->SetVisibility(false);
            }
        }
        if (StateTime >= ServiceClip->GetPlayLength())
        {
            if (!bGlassReleased)
                PlaceServedGlass();
            if (bDrinkTogether)
            {
                ServingTray->SetVisibility(false);
                bUsingServingTray = false;
                Glass->AttachToComponent(CharacterMesh, FAttachmentTransformRules::KeepRelativeTransform, DrinkHand);
                Glass->SetRelativeTransform(DrinkGrip);
                Glass->SetVisibility(true);
                PlayService(DrinkAnimation, false, true);
                SetState(ESSBarServiceState::Drinking, TEXT("sharing a drink with the guest"));
            }
            else
                ReturnHome(TEXT("Your drink has been served."));
        }
        break;
    case ESSBarServiceState::Drinking:
        if (StateTime >= DrinkAnimation->GetPlayLength())
            ReturnHome(TEXT("Cheers. That was lovely."));
        break;
    case ESSBarServiceState::JoiningTable:
        if (!Table.IsValid())
            ReturnHome(TEXT("That table is no longer available."));
        else if (MoveAlongPath(Dt))
        {
            Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            SetActorTransform(Table->Seat->GetComponentTransform());
            PlayService(SeatedAnimation, true);
            SetState(ESSBarServiceState::Seated, TEXT("sitting with the guest; staying until dismissed or they leave"));
        }
        break;
    case ESSBarServiceState::ReturningHome:
        if (MoveAlongPath(Dt))
        {
            SetActorRotation(Home.Rotator());
            SetState(ESSBarServiceState::Available, TEXT("available to take a drink order"));
            PlayService(IdleAnimation, true);
        }
        break;
    case ESSBarServiceState::Available:
    case ESSBarServiceState::Seated:
        ChatterTime -= Dt;
        if (ChatterTime <= 0)
        {
            auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>();
            const bool bSpoke = GM && GM->CrewChatter(this);
            ChatterTime = bSpoke ? FMath::Max(5.f, ChatterInterval) : 5.f;
        }
        break;
    }
}
