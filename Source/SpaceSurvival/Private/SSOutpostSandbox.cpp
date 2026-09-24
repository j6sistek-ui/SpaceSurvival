#include "SSOutpostSandbox.h"
#include "SSStation.h"
#include "SSPhase1Data.h"
#include "Animation/AnimSequence.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace
{
float Stick(float Value)
{
    return FMath::Abs(Value) <= .16f ? 0.f : FMath::Sign(Value) * (FMath::Abs(Value) - .16f) / .84f;
}
bool CompatibleClip(USkeletalMeshComponent *Mesh, UAnimSequence *Clip)
{
    return Mesh && Clip && Mesh->GetSkeletalMeshAsset() &&
           Mesh->GetSkeletalMeshAsset()->GetSkeleton() == Clip->GetSkeleton();
}
} // namespace

ASSOutpostSandboxGameMode::ASSOutpostSandboxGameMode()
{
    DefaultPawnClass = ASSWalker::StaticClass();
    PlayerControllerClass = ASSOutpostSandboxController::StaticClass();
    HUDClass = ASSOutpostSandboxHUD::StaticClass();
}
void ASSOutpostSandboxGameMode::HandleStartingNewPlayer_Implementation(APlayerController *NewPlayer)
{
    Super::HandleStartingNewPlayer_Implementation(NewPlayer);
    if (auto *Walker = NewPlayer ? Cast<ASSWalker>(NewPlayer->GetPawn()) : nullptr)
        Walker->ApplyHero(PreferredHeroId);
}

ASSOutpostTerminal::ASSOutpostTerminal()
{
    PrimaryActorTick.bCanEverTick = false;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("UsePoint"));
    PaintPalette = {FLinearColor(.06f, .32f, .44f), FLinearColor(.55f, .12f, .025f), FLinearColor(.6f, .63f, .65f),
                    FLinearColor(.15f, .035f, .32f), FLinearColor(.025f, .03f, .045f)};
}
bool ASSOutpostTerminal::CanUse(const APawn *User) const
{
    if (!User || !GetWorld() ||
        FVector::DistSquared(User->GetActorLocation(), GetActorLocation()) > FMath::Square(UseDistance))
        return false;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(OutpostUse), false, User);
    Query.AddIgnoredActor(this);
    if (PresentationTarget)
        Query.AddIgnoredActor(PresentationTarget);
    FHitResult Hit;
    const FVector Start = User->GetActorLocation() + FVector(0, 0, 40);
    return !GetWorld()->LineTraceSingleByChannel(Hit, Start, GetActorLocation(), ECC_Visibility, Query) ||
           FVector::DistSquared(Hit.ImpactPoint, GetActorLocation()) < FMath::Square(45.f);
}
FString ASSOutpostTerminal::CyclePaint()
{
    if (!PresentationTarget || PaintPalette.IsEmpty())
        return TEXT("No compatible parked hull is connected to this terminal.");
    const int32 Next = (PreviewIndex + 1) % PaintPalette.Num();
    TArray<UMeshComponent *> Meshes;
    PresentationTarget->GetComponents<UMeshComponent>(Meshes, true);
    int32 Changed = 0;
    for (UMeshComponent *Mesh : Meshes)
    {
        if (!Mesh || !Mesh->ComponentHasTag(PaintComponentTag))
            continue;
        for (int32 Slot : PaintMaterialSlots)
        {
            if (Slot < 0 || Slot >= Mesh->GetNumMaterials())
                continue;
            UMaterialInterface *Material = Mesh->GetMaterial(Slot);
            if (!Material)
                continue;
            TArray<FMaterialParameterInfo> Parameters;
            TArray<FGuid> Ids;
            Material->GetAllVectorParameterInfo(Parameters, Ids);
            if (!Parameters.ContainsByPredicate([this](const FMaterialParameterInfo &P)
                                                { return P.Name == PaintParameter; }))
                continue;
            auto *Dynamic = Cast<UMaterialInstanceDynamic>(Material);
            if (!Dynamic)
                Dynamic = Mesh->CreateDynamicMaterialInstance(Slot, Material);
            if (Dynamic)
            {
                Dynamic->SetVectorParameterValue(PaintParameter, PaintPalette[Next]);
                ++Changed;
            }
        }
    }
    if (!Changed)
        return TEXT("This parked hull has no paint-enabled panels. Factory materials are preserved.");
    PreviewIndex = Next;
    return FString::Printf(
        TEXT("Hull finish %d / %d applied to the parked ship. Sandbox preview; not saved to your account."), Next + 1,
        PaintPalette.Num());
}
FString ASSOutpostTerminal::CycleWardrobe()
{
    auto *Data = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
    auto *Mesh = PresentationTarget ? PresentationTarget->FindComponentByClass<USkeletalMeshComponent>() : nullptr;
    if (!Data || !Mesh)
        return TEXT("Wardrobe projector is not connected.");
    auto Heroes = Data->InstalledHeroes(ESSHeroSlot::Walker);
    Heroes.RemoveAll([](const FSSHeroDefinition &Hero) { return Hero.Identity == ESSHeroIdentity::Acornaut; });
    if (Heroes.IsEmpty())
        return TEXT("No installed crew appearances are available.");
    const int32 Next = (PreviewIndex + 1) % Heroes.Num();
    const auto &Hero = Heroes[Next];
    auto *Asset = LoadObject<USkeletalMesh>(nullptr, *Hero.MeshPath);
    if (!Asset)
        return TEXT("That crew appearance could not be loaded.");
    // Keep the original projector's sole plane, including capsule-centred actor offsets.
    FVector MeshOrigin = Mesh->GetRelativeLocation();
    float SolePlane = MeshOrigin.Z;
    if (const auto *Previous = Mesh->GetSkeletalMeshAsset())
    {
        const auto PreviousBounds = Previous->GetBounds();
        SolePlane += (PreviousBounds.Origin.Z - PreviousBounds.BoxExtent.Z) * Mesh->GetRelativeScale3D().Z;
    }
    if (auto *Ambient = Cast<ASSOutpostAmbientActor>(PresentationTarget))
        Ambient->bAnimationManagedExternally = true;
    Mesh->Stop();
    Mesh->SetSkeletalMesh(Asset);
    Mesh->EmptyOverrideMaterials();
    const auto Bounds = Asset->GetBounds();
    const float Scale = FMath::Clamp(HologramHeight / FMath::Max(1.f, float(Bounds.BoxExtent.Z * 2)), .01f, 10.f);
    Mesh->SetRelativeScale3D(FVector(Scale));
    MeshOrigin.Z = SolePlane - (Bounds.Origin.Z - Bounds.BoxExtent.Z) * Scale;
    Mesh->SetRelativeLocation(MeshOrigin);
    Mesh->SetRelativeRotation(FRotator(0, Hero.MeshYaw, 0));
    if (HologramMaterial)
        for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
            Mesh->SetMaterial(Slot, HologramMaterial);
    Mesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    if (FSSHeroDefinition::AssetInstalled(Hero.IdleClipPath))
        if (auto *Idle = LoadObject<UAnimSequence>(nullptr, *Hero.IdleClipPath); CompatibleClip(Mesh, Idle))
            Mesh->PlayAnimation(Idle, true);
    PreviewIndex = Next;
    return FString::Printf(TEXT("CREW APPEARANCE / %s. Hologram preview only; your equipped character is unchanged."),
                           *Hero.Id.ToString());
}
FString ASSOutpostTerminal::Use(APlayerController *User)
{
    if (!User || !CanUse(User->GetPawn()))
        return TEXT("Move closer to the console and keep the access point in view.");
    switch (Action)
    {
    case ESSOutpostAction::CycleShipPaint:
        return CyclePaint();
    case ESSOutpostAction::CycleWardrobe:
        return CycleWardrobe();
    case ESSOutpostAction::SurvivalBoarding:
    case ESSOutpostAction::FreeFlight:
    {
        const auto *Mode = GetWorld()->GetAuthGameMode<ASSOutpostSandboxGameMode>();
        if (!Mode || Mode->GameplayMap.IsNone())
            return TEXT("The gameplay destination is not configured.");
        // Survival opens the real Start/Continue/Free Flight choice. It never starts a fresh run implicitly.
        UGameplayStatics::OpenLevel(this, Mode->GameplayMap, true,
                                    Action == ESSOutpostAction::FreeFlight ? TEXT("OutpostEntry=FreeFlight")
                                                                           : TEXT("OutpostEntry=LaunchMenu"));
        return TEXT("Loading the current flight game. This design sandbox remains a separate map.");
    }
    default:
        return Description;
    }
}

ASSOutpostSandboxController::ASSOutpostSandboxController()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bTickEvenWhenPaused = true;
    bShouldPerformFullTickWhenPaused = true;
    bShowMouseCursor = false;
}
void ASSOutpostSandboxController::BeginPlay()
{
    Super::BeginPlay();
    SetInputMode(FInputModeGameOnly());
}
ASSOutpostTerminal *ASSOutpostSandboxController::FocusedTerminal() const
{
    const APawn *Walker = GetPawn();
    if (!Walker || !GetWorld())
        return nullptr;
    ASSOutpostTerminal *Best = nullptr;
    float BestScore = MAX_flt;
    const FVector Forward = GetControlRotation().Vector();
    for (TActorIterator<ASSOutpostTerminal> It(GetWorld()); It; ++It)
    {
        if (!It->CanUse(Walker))
            continue;
        const FVector Delta = It->GetActorLocation() - Walker->GetActorLocation();
        const float Facing = FVector::DotProduct(Forward, Delta.GetSafeNormal());
        if (Facing < -.15f)
            continue;
        const float Score = Delta.Size() * (1.25f - .5f * Facing);
        if (Score < BestScore)
        {
            Best = *It;
            BestScore = Score;
        }
    }
    return Best;
}
void ASSOutpostSandboxController::Interact()
{
    if (bReviewPaused)
        return;
    if (auto *Terminal = FocusedTerminal())
    {
        Notice = Terminal->Use(this);
        NoticeSeconds = 8.f;
    }
}
void ASSOutpostSandboxController::PlayerTick(float Dt)
{
    Super::PlayerTick(Dt);
    if (WasInputKeyJustPressed(EKeys::Escape) || WasInputKeyJustPressed(EKeys::Gamepad_Special_Right))
    {
        bReviewPaused = !bReviewPaused;
        SetPause(bReviewPaused);
    }
    if (bReviewPaused)
        return;
    NoticeSeconds = FMath::Max(0.f, NoticeSeconds - Dt);
    auto *Walker = Cast<ASSWalker>(GetPawn());
    if (!Walker || Dt <= 0.f)
        return;
    if (SafeSpawn.IsNearlyZero())
        SafeSpawn = Walker->GetActorLocation();
    if (Walker->GetActorLocation().Z < SafeSpawn.Z - 1200.f)
    {
        Walker->GetCharacterMovement()->StopMovementImmediately();
        Walker->SetActorLocation(SafeSpawn, false, nullptr, ETeleportType::TeleportPhysics);
        Notice = TEXT("Returned to the arrival deck.");
        NoticeSeconds = 3.f;
    }
    FVector2D Direction(Stick(GetInputAnalogKeyState(EKeys::Gamepad_LeftX)),
                        Stick(GetInputAnalogKeyState(EKeys::Gamepad_LeftY)));
    Direction.X += (IsInputKeyDown(EKeys::D) ? 1.f : 0.f) - (IsInputKeyDown(EKeys::A) ? 1.f : 0.f);
    Direction.Y += (IsInputKeyDown(EKeys::W) ? 1.f : 0.f) - (IsInputKeyDown(EKeys::S) ? 1.f : 0.f);
    Direction = Direction.GetClampedToMaxSize(1.f);
    float MouseX = 0.f, MouseY = 0.f;
    GetInputMouseDelta(MouseX, MouseY);
    FVector2D Look(Stick(GetInputAnalogKeyState(EKeys::Gamepad_RightX)),
                   Stick(GetInputAnalogKeyState(EKeys::Gamepad_RightY)));
    Look.X += MouseX * .16f / (90.f * Dt);
    Look.Y += MouseY * .16f / (70.f * Dt);
    Walker->Move(Direction, Look, IsInputKeyDown(EKeys::LeftShift) || IsInputKeyDown(EKeys::Gamepad_LeftThumbstick),
                 Dt);
    if (WasInputKeyJustPressed(EKeys::SpaceBar) || WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Bottom))
        Walker->Jump();
    if (WasInputKeyJustReleased(EKeys::SpaceBar) || WasInputKeyJustReleased(EKeys::Gamepad_FaceButton_Bottom))
        Walker->StopJumping();
    if (WasInputKeyJustPressed(EKeys::E) || WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Left))
        Interact();
}
void ASSOutpostSandboxHUD::DrawHUD()
{
    Super::DrawHUD();
    const auto *Controller = Cast<ASSOutpostSandboxController>(PlayerOwner);
    if (!Canvas || !Controller || !GEngine)
        return;
    const float Scale = FMath::Clamp(Canvas->ClipY / 1080.f, .75f, 1.5f);
    const float Margin = 32.f * Scale;
    auto Text = [&](const FString &Value, float X, float Y, FLinearColor Colour, float Size)
    { DrawText(Value, Colour, X, Y, GEngine->GetSmallFont(), Size * Scale); };
    Text(TEXT("WAYFARER / ASTEROID OUTPOST"), Margin, Margin, FLinearColor(.55f, .9f, 1.f), 1.3f);
    Text(TEXT("DESIGN SANDBOX"), Margin, Margin + 26.f * Scale, FLinearColor(.6f, .7f, .76f), .85f);
    if (Controller->IsReviewPaused())
    {
        DrawRect(FLinearColor(0.f, .008f, .015f, .72f), 0, 0, Canvas->ClipX, Canvas->ClipY);
        Text(TEXT("PAUSED / Esc or Menu to resume"), Canvas->ClipX * .34f, Canvas->ClipY * .45f, FLinearColor::White,
             1.3f);
        return;
    }
    TArray<FWrappedStringElement> NoticeLines;
    float NoticeHeight = 0.f;
    if (Controller->NoticeSeconds > 0.f)
    {
        FTextSizingParameters Parameters(GEngine->GetSmallFont(), .95f * Scale, .95f * Scale);
        Parameters.DrawXL = FMath::Max(1.f, Canvas->ClipX - 2.f * Margin);
        Canvas->WrapString(Parameters, 0.f, Controller->Notice, NoticeLines);
        for (const auto &Line : NoticeLines)
            NoticeHeight += FMath::Max(float(Line.LineExtent.Y), 14.f * Scale) + 4.f * Scale;
    }
    float NoticeY = Canvas->ClipY - 58.f * Scale - NoticeHeight;
    if (auto *Terminal = Controller->FocusedTerminal())
        Text(TEXT("E / X  ") + Terminal->DisplayName, Margin,
             FMath::Min(Canvas->ClipY - 110.f * Scale, NoticeY - 35.f * Scale), FLinearColor(.5f, .95f, 1.f), 1.3f);
    for (const auto &Line : NoticeLines)
    {
        Text(Line.Value, Margin, NoticeY, FLinearColor::White, .95f);
        NoticeY += FMath::Max(float(Line.LineExtent.Y), 14.f * Scale) + 4.f * Scale;
    }
    Text(TEXT("WASD / LS  MOVE     MOUSE / RS  LOOK     SPACE / A  JUMP     SHIFT / L3  RUN     E / X  USE"), Margin,
         Canvas->ClipY - 35.f * Scale, FLinearColor(.65f, .74f, .8f), .8f);
}

ASSOutpostDoor::ASSOutpostDoor()
{
    PrimaryActorTick.bCanEverTick = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("DoorFrame"));
    LeftLeaf = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("LeftLeaf"));
    RightLeaf = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RightLeaf"));
    LeftBlocker = CreateDefaultSubobject<UBoxComponent>(TEXT("LeftBlocker"));
    RightBlocker = CreateDefaultSubobject<UBoxComponent>(TEXT("RightBlocker"));
    LeftLeaf->SetupAttachment(RootComponent);
    RightLeaf->SetupAttachment(RootComponent);
    LeftBlocker->SetupAttachment(RootComponent);
    RightBlocker->SetupAttachment(RootComponent);
    for (UStaticMeshComponent *Leaf : {LeftLeaf.Get(), RightLeaf.Get()})
    {
        Leaf->SetMobility(EComponentMobility::Movable);
        Leaf->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
    for (UBoxComponent *Blocker : {LeftBlocker.Get(), RightBlocker.Get()})
    {
        Blocker->SetMobility(EComponentMobility::Movable);
        Blocker->SetCollisionProfileName(TEXT("BlockAllDynamic"));
        Blocker->SetCanEverAffectNavigation(false);
    }
    PositionLeaves();
}
void ASSOutpostDoor::PositionLeaves()
{
    const float Ease = FMath::SmoothStep(0.f, 1.f, OpenFraction);
    const FVector Left = LeftClosed + LeftTravel * Ease, Right = RightClosed + RightTravel * Ease;
    LeftLeaf->SetRelativeLocation(Left);
    RightLeaf->SetRelativeLocation(Right);
    LeftBlocker->SetRelativeLocation(Left);
    RightBlocker->SetRelativeLocation(Right);
    LeftBlocker->SetBoxExtent(LeafHalfExtent.GetAbs());
    RightBlocker->SetBoxExtent(LeafHalfExtent.GetAbs());
}
void ASSOutpostDoor::OnConstruction(const FTransform &Transform)
{
    Super::OnConstruction(Transform);
    PositionLeaves();
}
void ASSOutpostDoor::BeginPlay()
{
    Super::BeginPlay();
    OpenFraction = 0.f;
    PositionLeaves();
}
void ASSOutpostDoor::RequestOpen()
{
    HoldRemaining = FMath::Max(.5f, HoldOpenSeconds);
}
bool ASSOutpostDoor::IsDoorwayOccupied() const
{
    if (!GetWorld())
        return false;
    FCollisionObjectQueryParams Objects;
    Objects.AddObjectTypesToQuery(ECC_Pawn);
    Objects.AddObjectTypesToQuery(ECC_PhysicsBody);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(OutpostDoorSafety), false, this);
    // Include the complete swept pockets as well as the opening: a crate beside an open leaf must
    // inhibit closing too. The proxy covers every point either leaf would cross on its return.
    FBox Swept(-SafetyHalfExtent.GetAbs() + FVector(0, 0, SafetyHalfExtent.Z),
               SafetyHalfExtent.GetAbs() + FVector(0, 0, SafetyHalfExtent.Z));
    for (const FVector &Position : {LeftClosed, RightClosed, LeftClosed + LeftTravel, RightClosed + RightTravel})
    {
        Swept += Position - LeafHalfExtent.GetAbs();
        Swept += Position + LeafHalfExtent.GetAbs();
    }
    return GetWorld()->OverlapAnyTestByObjectType(
        GetActorTransform().TransformPosition(Swept.GetCenter()), GetActorQuat(), Objects,
        FCollisionShape::MakeBox(Swept.GetExtent() * GetActorScale3D().GetAbs()), Query);
}
void ASSOutpostDoor::Tick(float Dt)
{
    Super::Tick(Dt);
    if (Dt <= 0.f)
        return;
    FCollisionObjectQueryParams Objects;
    Objects.AddObjectTypesToQuery(ECC_Pawn);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(OutpostDoorSensor), false, this);
    if (GetWorld()->OverlapAnyTestByObjectType(GetActorLocation() + FVector(0, 0, 100), FQuat::Identity, Objects,
                                               FCollisionShape::MakeSphere(FMath::Max(200.f, SensorRadius)), Query) ||
        IsDoorwayOccupied())
        RequestOpen();
    else
        HoldRemaining = FMath::Max(0.f, HoldRemaining - Dt);
    const float Target = HoldRemaining > 0.f ? 1.f : 0.f;
    OpenFraction = FMath::FInterpConstantTo(OpenFraction, Target, Dt, 1.f / FMath::Max(.2f, SlideSeconds));
    PositionLeaves();
}

ASSOutpostAmbientActor::ASSOutpostAmbientActor()
{
    PrimaryActorTick.bCanEverTick = true;
    Body = CreateDefaultSubobject<UCapsuleComponent>(TEXT("Body"));
    RootComponent = Body;
    Body->InitCapsuleSize(28.f, 85.f);
    Body->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Body->SetCollisionObjectType(ECC_Pawn);
    Body->SetCollisionResponseToAllChannels(ECR_Block);
    Body->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
    Body->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
    CharacterMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("CharacterMesh"));
    CharacterMesh->SetupAttachment(Body);
    CharacterMesh->SetRelativeLocation(FVector(0, 0, -85));
    CharacterMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    DroneMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DroneMesh"));
    DroneMesh->SetupAttachment(Body);
    DroneMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}
void ASSOutpostAmbientActor::PlayClip(UAnimSequence *Clip, bool bLoop)
{
    if (Clip == ActiveAnimation || !CompatibleClip(CharacterMesh, Clip))
        return;
    CharacterMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    CharacterMesh->PlayAnimation(Clip, bLoop);
    ActiveAnimation = Clip;
}
void ASSOutpostAmbientActor::BeginPlay()
{
    Super::BeginPlay();
    RouteOrigin = GetActorTransform();
    Elapsed = PhaseOffset;
    WaitRemaining = FMath::Fmod(FMath::Abs(PhaseOffset), 3.f);
    NextGesture = 6.f + FMath::Fmod(FMath::Abs(PhaseOffset), 5.f);
    if (bDrone)
    {
        Body->SetCapsuleSize(25, 25);
        Body->SetCollisionObjectType(ECC_WorldDynamic);
        Body->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
    }
    else if (!bAnimationManagedExternally)
    {
        PlayClip(IdleAnimation, true);
        if (ActiveAnimation && ActiveAnimation->GetPlayLength() > .01f)
            CharacterMesh->SetPosition(FMath::Fmod(FMath::Abs(PhaseOffset), ActiveAnimation->GetPlayLength()), false);
    }
}
void ASSOutpostAmbientActor::Tick(float Dt)
{
    Super::Tick(Dt);
    if (Dt <= 0.f)
        return;
    if (bAnimationManagedExternally)
        return;
    Elapsed += Dt;
    WaitRemaining = FMath::Max(0.f, WaitRemaining - Dt);
    bool Moving = false;
    if (RoutePoints.Num() > 1 && WaitRemaining <= 0.f)
    {
        FVector Target = RouteOrigin.TransformPosition(RoutePoints[RouteIndex]);
        const FVector Delta = Target - GetActorLocation();
        if (Delta.SizeSquared() < FMath::Square(12.f))
        {
            RouteIndex = (RouteIndex + 1) % RoutePoints.Num();
            WaitRemaining = FMath::Max(0.f, PauseAtWaypoint);
        }
        else
        {
            const FVector Step = Delta.GetClampedToMaxSize(FMath::Max(0.f, TravelSpeed) * Dt);
            FVector Next = GetActorLocation() + Step;
            if (!bDrone)
            {
                FCollisionQueryParams Query(SCENE_QUERY_STAT(OutpostCrewFloor), false, this);
                FHitResult Ground;
                // Only upward-facing static deck supports crew; another crew capsule is never ground.
                if (GetWorld()->LineTraceSingleByObjectType(Ground, Next + FVector(0, 0, 70), Next - FVector(0, 0, 260),
                                                            FCollisionObjectQueryParams(ECC_WorldStatic), Query) &&
                    Ground.ImpactNormal.Z > .7f)
                    Next.Z = Ground.ImpactPoint.Z + Body->GetScaledCapsuleHalfHeight() + 2.f;
                else
                    Next = GetActorLocation();
            }
            FHitResult Hit;
            const FVector Before = GetActorLocation();
            SetActorLocation(Next, true, &Hit);
            Moving = FVector::DistSquared(Before, GetActorLocation()) > .01f;
            if (Moving)
            {
                const FRotator Facing(0, Delta.Rotation().Yaw, 0);
                SetActorRotation(FMath::RInterpTo(GetActorRotation(), Facing, Dt, 4.f));
                BlockedSeconds = 0.f;
            }
            else
            {
                BlockedSeconds += Dt;
                if (BlockedSeconds > 2.f)
                {
                    RouteIndex = (RouteIndex + 1) % RoutePoints.Num();
                    BlockedSeconds = 0.f;
                    WaitRemaining = 1.f;
                }
            }
        }
    }
    if (bDrone)
    {
        DroneMesh->SetRelativeLocation(FVector(0, 0, FMath::Sin(Elapsed * 1.8f) * BobAmplitude));
        DroneMesh->SetRelativeRotation(FRotator(FMath::Sin(Elapsed) * 3.f, 0, FMath::Sin(Elapsed * .8f) * 4.f));
        return;
    }
    if (Moving)
    {
        GestureRemaining = 0.f;
        PlayClip(WalkAnimation, true);
        return;
    }
    GestureRemaining = FMath::Max(0.f, GestureRemaining - Dt);
    NextGesture -= Dt;
    if (GestureRemaining <= 0.f && NextGesture <= 0.f && !GestureAnimations.IsEmpty())
    {
        auto *Gesture = GestureAnimations[GestureIndex++ % GestureAnimations.Num()].Get();
        if (CompatibleClip(CharacterMesh, Gesture))
        {
            PlayClip(Gesture, false);
            GestureRemaining = Gesture->GetPlayLength();
        }
        NextGesture = 9.f + FMath::Fmod(FMath::Abs(PhaseOffset), 6.f);
    }
    if (GestureRemaining <= 0.f)
        PlayClip(IdleAnimation, true);
}
