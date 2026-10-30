#include "SSOutpostSandbox.h"
#include "SSCryoChamber.h"
#include "SSNPCHeadFillComponent.h"
#include "SSStation.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "Animation/AnimSequence.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
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
const USSPhase1Data *Phase1Data()
{
    return LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
}
/** What the wardrobe cycles through: every installed walker body except the Acornaut. */
TArray<FSSHeroDefinition> WardrobeHeroes(const USSPhase1Data &Data)
{
    auto Heroes = Data.InstalledHeroes(ESSHeroSlot::Walker);
    Heroes.RemoveAll([](const FSSHeroDefinition &Hero) { return Hero.Identity == ESSHeroIdentity::Acornaut; });
    return Heroes;
}
} // namespace

ASSOutpostSandboxGameMode::ASSOutpostSandboxGameMode()
{
    DefaultPawnClass = ASSWalker::StaticClass();
    PlayerControllerClass = ASSOutpostSandboxController::StaticClass();
    HUDClass = ASSOutpostSandboxHUD::StaticClass();
}
void ASSOutpostSandboxGameMode::BeginPlay()
{
    Super::BeginPlay();
    // The current station is editable directly, but Play must use the full game world.
    // A streamed station uses SSGameMode; the original sandbox keeps its preview rules.
    if (UGameplayStatics::GetCurrentLevelName(this, true) == TEXT("L_WayfarerRuntime"))
        UGameplayStatics::OpenLevel(this, GameplayMap);
}
void ASSOutpostSandboxGameMode::HandleStartingNewPlayer_Implementation(APlayerController *NewPlayer)
{
    Super::HandleStartingNewPlayer_Implementation(NewPlayer);
    // A walker that has not begun play has no hero tuning yet, and its own BeginPlay would put the roster
    // default back on; StartPlay dresses those. This covers a player arriving after the world began play.
    auto *Walker = NewPlayer ? Cast<ASSWalker>(NewPlayer->GetPawn()) : nullptr;
    if (Walker && Walker->HasActorBegunPlay())
        Walker->ApplyHero(StartingHeroId());
}
void ASSOutpostSandboxGameMode::StartPlay()
{
    Super::StartPlay(); // every actor's BeginPlay has run
    for (FConstPlayerControllerIterator It = GetWorld()->GetPlayerControllerIterator(); It; ++It)
        if (auto *Walker = It->IsValid() ? Cast<ASSWalker>(It->Get()->GetPawn()) : nullptr)
            Walker->ApplyHero(StartingHeroId());
}
FName ASSOutpostSandboxGameMode::StartingHeroId() const
{
    // A character worn at the wardrobe outranks the map's default, resolved as ASSGameMode::WornHeroId does.
    // A saved body this build does not carry falls back to the map's default, not to roster order.
    const auto *GI = GetGameInstance<USSGameInstance>();
    const auto *Data = Phase1Data();
    if (GI && Data && GI->Session.account.hero >= 0 &&
        GI->Session.account.hero != static_cast<int32>(ESSHeroIdentity::Acornaut))
    {
        const FSSHeroDefinition Chosen = Data->Hero(static_cast<ESSHeroIdentity>(GI->Session.account.hero));
        if (Data->SelectHero(ESSHeroSlot::Walker, Chosen.Id).Id == Chosen.Id)
            return Chosen.Id;
    }
    return PreferredHeroId;
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
    const auto *Data = Phase1Data();
    auto *Mesh = PresentationTarget ? PresentationTarget->FindComponentByClass<USkeletalMeshComponent>() : nullptr;
    if (!Data || !Mesh)
        return TEXT("Wardrobe projector is not connected.");
    const auto Heroes = WardrobeHeroes(*Data);
    if (Heroes.IsEmpty())
        return TEXT("No installed crew appearances are available.");
    const int32 Next = (PreviewIndex + 1) % Heroes.Num();
    const auto &Hero = Heroes[Next];
    if (!PreviewWardrobe(Hero))
        return TEXT("That crew appearance could not be loaded.");
    PreviewIndex = Next;
    return FString::Printf(TEXT("CREW APPEARANCE / %s. Hologram preview only; your equipped character is unchanged."),
                           *Hero.Id.ToString());
}
bool ASSOutpostTerminal::PreviewWardrobe(const FSSHeroDefinition &Hero)
{
    auto *Original =
        IsValid(PresentationTarget) ? PresentationTarget->FindComponentByClass<USkeletalMeshComponent>() : nullptr;
    if (!IsValid(Original) || !GetWorld() || IsActorBeingDestroyed() || !FMath::IsFinite(HologramHeight) ||
        HologramHeight <= 0.f || !FMath::IsFinite(Hero.MeshYaw) || !FSSHeroDefinition::AssetInstalled(Hero.MeshPath))
        return false;
    auto *Asset = LoadObject<USkeletalMesh>(nullptr, *Hero.MeshPath);
    if (!Asset)
        return false;

    const FTransform OriginalWorld = Original->GetComponentTransform();
    double SolePlane = OriginalWorld.GetLocation().Z;
    if (const auto *OriginalAsset = Original->GetSkeletalMeshAsset())
    {
        const auto OriginalBounds = OriginalAsset->GetBounds().TransformBy(OriginalWorld);
        SolePlane = OriginalBounds.Origin.Z - OriginalBounds.BoxExtent.Z;
    }

    USceneComponent *Parent = Original->GetAttachParent();
    FName Socket = Original->GetAttachSocketName();
    FTransform Relative = Original->GetRelativeTransform();
    if (Parent)
    {
        FRotator Rotation = Relative.Rotator();
        Rotation.Yaw = Hero.MeshYaw;
        Relative.SetRotation(Rotation.Quaternion());
    }
    else
    {
        // A root mesh is itself a stable attachment; retain its authored world facing.
        Parent = Original;
        Socket = NAME_None;
        Relative = FTransform::Identity;
    }
    const FTransform ParentWorld = Parent->GetSocketTransform(Socket);
    if (OriginalWorld.ContainsNaN() || ParentWorld.ContainsNaN() ||
        ParentWorld.GetScale3D().GetAbsMin() <= UE_SMALL_NUMBER)
        return false;
    Relative.SetScale3D(FVector::OneVector);
    const auto AssetBounds = Asset->GetBounds();
    const auto UnitBounds = AssetBounds.TransformBy(Relative * ParentWorld);
    const double UnitHeight = UnitBounds.BoxExtent.Z * 2.;
    if (!FMath::IsFinite(UnitHeight) || UnitHeight <= UE_SMALL_NUMBER || !FMath::IsFinite(SolePlane))
        return false;
    // Fit in world centimetres, including parent/socket scale, without changing the original mesh.
    Relative.SetScale3D(FVector(HologramHeight / UnitHeight));
    FTransform PreviewWorld = Relative * ParentWorld;
    const auto FittedBounds = AssetBounds.TransformBy(PreviewWorld);
    PreviewWorld.AddToTranslation(FVector(0, 0, SolePlane - (FittedBounds.Origin.Z - FittedBounds.BoxExtent.Z)));
    Relative = PreviewWorld.GetRelativeTransform(ParentWorld);
    if (Relative.ContainsNaN())
        return false;

    auto *Candidate = NewObject<USkeletalMeshComponent>(this, NAME_None, RF_Transient);
    Candidate->SetupAttachment(Parent, Socket);
    Candidate->SetRelativeTransform(Relative);
    Candidate->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Candidate->SetGenerateOverlapEvents(false);
    Candidate->SetCanEverAffectNavigation(false);
    Candidate->SetSimulatePhysics(false);
    Candidate->bDisableClothSimulation = true;
    Candidate->bSuppressNotifyEventDispatch = true;
    Candidate->SetDisablePostProcessBlueprint(true);
    Candidate->SetCastShadow(false);
    Candidate->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    Candidate->SetSkeletalMesh(Asset);
    if (HologramMaterial)
        for (int32 Slot = 0; Slot < Candidate->GetNumMaterials(); ++Slot)
            Candidate->SetMaterial(Slot, HologramMaterial);
    Candidate->RegisterComponent();
    if (!Candidate->IsRegistered())
    {
        Candidate->DestroyComponent();
        return false;
    }
    if (Asset->GetSkeleton() && FSSHeroDefinition::AssetInstalled(Hero.IdleClipPath))
        if (auto *Idle = LoadObject<UAnimSequence>(nullptr, *Hero.IdleClipPath); CompatibleClip(Candidate, Idle))
            Candidate->PlayAnimation(Idle, true);
    Candidate->UpdateBounds();

    // Commit only after the candidate exists. No Stop/Play or material writes touch the placed mesh.
    EndWardrobePreview();
    WardrobeOriginalMesh = Original;
    bWardrobeOriginalVisible = Original->GetVisibleFlag();
    WardrobePreviewMesh = Candidate;
    Original->SetVisibility(false);
    return true;
}
void ASSOutpostTerminal::EndWardrobePreview()
{
    if (IsValid(WardrobePreviewMesh))
        WardrobePreviewMesh->DestroyComponent();
    WardrobePreviewMesh = nullptr;
    if (auto *Original = WardrobeOriginalMesh.Get())
        Original->SetVisibility(bWardrobeOriginalVisible);
    WardrobeOriginalMesh.Reset();
}
FVector ASSOutpostTerminal::WardrobePreviewCenter() const
{
    if (IsValid(WardrobePreviewMesh))
        return WardrobePreviewMesh->Bounds.Origin;
    return IsValid(PresentationTarget) ? PresentationTarget->GetActorLocation() : GetActorLocation();
}
bool ASSOutpostTerminal::HasWardrobePreview() const
{
    return PreviewIndex >= 0 && IsValid(WardrobePreviewMesh);
}
FString ASSOutpostTerminal::WearPreviewedHero(APlayerController *User)
{
    if (!User || !CanUse(User->GetPawn()))
        return TEXT("Move closer to the console and keep the access point in view.");
    if (Action != ESSOutpostAction::CycleWardrobe || !HasWardrobePreview())
        return TEXT("Preview a character first, then wear it.");
    const auto *Data = Phase1Data();
    const auto Heroes = Data ? WardrobeHeroes(*Data) : TArray<FSSHeroDefinition>();
    auto *Walker = Cast<ASSWalker>(User->GetPawn());
    if (!Heroes.IsValidIndex(PreviewIndex) || !Walker)
        return TEXT("That crew appearance cannot be worn here.");
    // Mirrors the station wardrobe's wear action (ASSGameMode, Wardrobe panel): equip, then save the identity.
    const auto &Hero = Heroes[PreviewIndex];
    Walker->ApplyHero(Hero.Id);
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI)
        return FString::Printf(TEXT("Now wearing %s for this visit. No account is loaded to save it."),
                               *Hero.Id.ToString());
    GI->Session.account.hero = static_cast<int32>(Hero.Identity);
    if (!GI->PersistAccount())
        return GI->LastSaveError;
    return FString::Printf(TEXT("Now wearing %s. Saved as your character."), *Hero.Id.ToString());
}
void ASSOutpostTerminal::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    EndWardrobePreview();
    Super::EndPlay(EndPlayReason);
}
FString ASSOutpostTerminal::Use(APlayerController *User)
{
    if (!User || !CanUse(User->GetPawn()))
        return TEXT("Move closer to the console and keep the access point in view.");
    if (Action == ESSOutpostAction::CryoChill)
    {
        if (auto *Chamber = Cast<ASSCryoChamber>(PresentationTarget))
            return Chamber->Interact(User->GetPawn());
        return TEXT("No cryogenic chamber is connected to this console.");
    }
    if (Action == ESSOutpostAction::PayCover)
    {
        // Talking never admits; only the cover menu's demo payment opens the rope.
        const auto *Gate = Cast<ASSClubCoverGate>(PresentationTarget);
        if (!Gate)
            return TEXT("No rope connected to this bouncer.");
        if (Gate->IsAdmitted())
            return TEXT("You're on the list. Head on up.");
        return FString::Printf(TEXT("Cover first: %d CR to get past the rope."), Gate->DisplayedCover);
    }
    if (auto *Game = GetWorld()->GetAuthGameMode<ASSGameMode>();
        Game && Game->GetStation() && Game->GetStation()->IsUsingOutpost())
    {
        // Real game services use the existing account/run transactions. Sandbox previews stay local.
        const ESSPanel Panel = Game->GetStation()->OutpostPanel(this);
        if (Panel == ESSPanel::Launch)
        {
            Game->OpenPanel(ESSPanel::Launch);
            return FString();
        }
        if (Panel != ESSPanel::None)
        {
            Game->OpenPanel(Panel);
            return FString();
        }
        return Description;
    }
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
        if (Terminal->Action == ESSOutpostAction::PayCover)
            if (auto *Gate = Cast<ASSClubCoverGate>(Terminal->PresentationTarget); Gate && !Gate->IsAdmitted())
            {
                CoverMenuGate = Gate;
                CoverMenuTerminal = Terminal;
                NoticeSeconds = 0.f; // an older notice must not sit frozen under the menu
                return;
            }
        Notice = Terminal->Use(this);
        NoticeSeconds = 8.f;
    }
}
void ASSOutpostSandboxController::CloseCoverMenu()
{
    CoverMenuGate.Reset();
    CoverMenuTerminal.Reset();
}
void ASSOutpostSandboxController::PlayerTick(float Dt)
{
    Super::PlayerTick(Dt);
    // The cover menu owns this frame's input: no pause toggle, walking, jumping or interacting underneath it.
    if (auto *Gate = CoverMenu())
    {
        const auto *Terminal = CoverMenuTerminal.Get();
        if (!Terminal || !Terminal->CanUse(GetPawn()) || Gate->IsAdmitted())
            CloseCoverMenu();
        else if (WasInputKeyJustPressed(EKeys::Escape) || WasInputKeyJustPressed(EKeys::Gamepad_Special_Right) ||
                 WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Right))
        {
            CloseCoverMenu();
            Notice = TEXT("Maybe next time.");
            NoticeSeconds = 4.f;
        }
        else if (WasInputKeyJustPressed(EKeys::E) || WasInputKeyJustPressed(EKeys::Enter) ||
                 WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Bottom) ||
                 WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Left))
        {
            Notice = Gate->AdmitWithDemoPayment();
            NoticeSeconds = 8.f;
            CloseCoverMenu();
        }
        return;
    }
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
    if (WasInputKeyJustPressed(EKeys::F) || WasInputKeyJustPressed(EKeys::Gamepad_FaceButton_Top))
        if (auto *Terminal = FocusedTerminal();
            Terminal && Terminal->Action == ESSOutpostAction::CycleWardrobe && Terminal->HasWardrobePreview())
        {
            Notice = Terminal->WearPreviewedHero(this);
            NoticeSeconds = 8.f;
        }
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
    Text(TEXT("Wayfarer / Design preview"), Margin, Margin, FLinearColor(.6f, .7f, .76f), .95f);
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
    if (const auto *Gate = Controller->CoverMenu())
    {
        // Canvas modal (the game has no UMG). The payment is a demo and the menu says so.
        struct FModalLine
        {
            FString Value;
            FLinearColor Colour;
            float Size, Gap, Width = 0.f, Height = 0.f;
        };
        TArray<FModalLine> Lines = {
            {Gate->VenueName + TEXT("  /  COVER CHARGE"), FLinearColor(1.f, .45f, .8f), 1.3f, 18.f},
            {FString::Printf(TEXT("%d CR"), Gate->DisplayedCover), FLinearColor::White, 2.4f, 22.f},
            {TEXT("[E / A]  Pay cover"), FLinearColor(.75f, .95f, 1.f), 1.15f, 10.f},
            {TEXT("[Esc / B]  Not tonight"), FLinearColor(.7f, .74f, .8f), 1.15f, 22.f},
            {TEXT("Demo payment - no credits are deducted."), FLinearColor(.55f, .58f, .64f), .85f, 0.f}};
        float Width = 0.f, Height = 0.f;
        for (auto &Line : Lines)
        {
            GetTextSize(Line.Value, Line.Width, Line.Height, GEngine->GetSmallFont(), Line.Size * Scale);
            Width = FMath::Max(Width, Line.Width);
            Height += Line.Height + Line.Gap * Scale;
        }
        const float Pad = 30.f * Scale, BoxW = Width + 2.f * Pad, BoxH = Height + 2.f * Pad;
        const float BoxX = (Canvas->ClipX - BoxW) * .5f, BoxY = (Canvas->ClipY - BoxH) * .5f;
        DrawRect(FLinearColor(0.f, .008f, .015f, .5f), 0, 0, Canvas->ClipX, Canvas->ClipY);
        DrawRect(FLinearColor(.025f, .01f, .035f, .95f), BoxX, BoxY, BoxW, BoxH);
        DrawRect(FLinearColor(1.f, .16f, .63f), BoxX, BoxY, BoxW, 4.f * Scale);
        float LineY = BoxY + Pad;
        for (const auto &Line : Lines)
        {
            Text(Line.Value, (Canvas->ClipX - Line.Width) * .5f, LineY, Line.Colour, Line.Size);
            LineY += Line.Height + Line.Gap * Scale;
        }
    }
    else if (auto *Terminal = Controller->FocusedTerminal())
    {
        // The preview's Information action is not a working purchase. Keep its
        // access/identity intact while describing what this action really does.
        FString Action = TEXT("Read station information");
        switch (Terminal->Action)
        {
        case ESSOutpostAction::CryoChill:
            Action = TEXT("Hypercool chamber for 4 seconds");
            break;
        case ESSOutpostAction::CycleShipPaint:
            Action = TEXT("Preview next ship color");
            break;
        case ESSOutpostAction::CycleWardrobe:
            Action = TEXT("Preview next character");
            break;
        case ESSOutpostAction::SurvivalBoarding:
            Action = TEXT("Open flight game");
            break;
        case ESSOutpostAction::FreeFlight:
            Action = TEXT("Open free flight");
            break;
        case ESSOutpostAction::PayCover:
            Action = TEXT("Talk to the bouncer");
            break;
        default:
            if (Terminal->DisplayName.Contains(TEXT("FLIGHT UPGRADES")))
                Action = TEXT("Read upgrade overview");
            else if (Terminal->DisplayName.Contains(TEXT("CONTRACT EXCHANGE")))
                Action = TEXT("Read contract overview");
            else if (Terminal->DisplayName.Contains(TEXT("SHIP & PARTS")))
                Action = TEXT("Read ship information");
            else if (Terminal->DisplayName.Contains(TEXT("PILOT LEADERBOARD")))
                Action = TEXT("Read pilot information");
            else if (Terminal->DisplayName.Contains(TEXT("TRADE NETWORK")))
                Action = TEXT("Read trade information");
            break;
        }
        TArray<FString> Prompts = {TEXT("E / X   ") + Action};
        if (Terminal->Action == ESSOutpostAction::CycleWardrobe && Terminal->HasWardrobePreview())
            Prompts.Add(TEXT("F / Y   Wear this character"));
        float Width = 0.f, Height = 0.f, LineHeight = 0.f;
        for (const FString &Prompt : Prompts)
        {
            float LineWidth = 0.f;
            GetTextSize(Prompt, LineWidth, LineHeight, GEngine->GetSmallFont(), 1.3f * Scale);
            Width = FMath::Max(Width, LineWidth);
            Height += LineHeight;
        }
        const float Spacing = 6.f * Scale;
        Height += Spacing * (Prompts.Num() - 1);
        const float X = FMath::Max(Margin, (Canvas->ClipX - Width) * .5f);
        const float Y =
            FMath::Min(Canvas->ClipY - 74.f * Scale - (Height - LineHeight), NoticeY - Height - 22.f * Scale);
        DrawRect(FLinearColor(.01f, .022f, .032f, .9f), X - 12.f * Scale, Y - 10.f * Scale, Width + 24.f * Scale,
                 Height + 20.f * Scale);
        for (int32 Index = 0; Index < Prompts.Num(); ++Index)
            Text(Prompts[Index], X, Y + Index * (LineHeight + Spacing), FLinearColor(.75f, .95f, 1.f), 1.3f);
    }
    for (const auto &Line : NoticeLines)
    {
        Text(Line.Value, Margin, NoticeY, FLinearColor::White, .95f);
        NoticeY += FMath::Max(float(Line.LineExtent.Y), 14.f * Scale) + 4.f * Scale;
    }
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

ASSClubCoverGate::ASSClubCoverGate()
{
    PrimaryActorTick.bCanEverTick = false;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("RopeLine"));
    Gate = CreateDefaultSubobject<UBoxComponent>(TEXT("Gate"));
    Gate->SetupAttachment(RootComponent);
    Gate->SetMobility(EComponentMobility::Movable);
    Gate->SetCollisionProfileName(TEXT("BlockAllDynamic"));
    Gate->SetCanEverAffectNavigation(false);
    Gate->InitBoxExtent(GateHalfExtent.GetAbs());
}
void ASSClubCoverGate::OnConstruction(const FTransform &Transform)
{
    Super::OnConstruction(Transform);
    Gate->SetBoxExtent(GateHalfExtent.GetAbs());
}
FString ASSClubCoverGate::AdmitWithDemoPayment()
{
    // Never touches credits or the account save: admission lasts for this play session only.
    Gate->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    for (AActor *Rope : RopeActors)
        if (IsValid(Rope))
        {
            Rope->SetActorHiddenInGame(true);
            Rope->SetActorEnableCollision(false);
#if WITH_EDITOR
            Rope->SetIsTemporarilyHiddenInEditor(true);
#endif
        }
    bAdmitted = true;
    return FString::Printf(TEXT("%s / Cover paid: %d CR. Demo payment - no credits were charged. Head on up."),
                           *VenueName, DisplayedCover);
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
    HeadFillLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("NPCHeadFill"));
    HeadFillLight->SetupAttachment(CharacterMesh);
    HeadFillLight->SetMobility(EComponentMobility::Movable);
    HeadFillLight->SetIntensityUnits(ELightUnits::Lumens);
    HeadFillLight->SetIntensity(HeadFillLumens);
    HeadFillLight->SetUseInverseSquaredFalloff(true);
    HeadFillLight->SetAttenuationRadius(HeadFillRadius);
    HeadFillLight->SetSourceRadius(HeadFillSourceRadius);
    HeadFillLight->SetLightColor(FLinearColor(1.f, .95f, .9f));
    HeadFillLight->SetLightingChannels(false, false, true);
    HeadFillLight->SetSpecularScale(0.f);
    HeadFillLight->SetIndirectLightingIntensity(0.f);
    HeadFillLight->SetVolumetricScatteringIntensity(0.f);
    HeadFillLight->SetAffectReflection(false);
    HeadFillLight->SetAffectGlobalIllumination(false);
    HeadFillLight->SetCastShadows(false);
    HeadFillLight->SetVisibility(false);
    HeadFillConfiguration = CreateDefaultSubobject<USSNPCHeadFillComponent>(TEXT("NPCHeadFillConfiguration"));
    HeadFillConfiguration->ReceiverMesh = CharacterMesh;
    HeadFillConfiguration->HeadFillLight = HeadFillLight;
}
void ASSOutpostAmbientActor::OnConstruction(const FTransform &Transform)
{
    Super::OnConstruction(Transform);
    RefreshReadabilityLighting();
}
void ASSOutpostAmbientActor::RefreshReadabilityLighting()
{
    if (!HeadFillLight || !CharacterMesh || !HeadFillConfiguration)
        return;
    if (bHeadFillOwnsChannel)
    {
        CharacterMesh->SetLightingChannels(CharacterMesh->LightingChannels.bChannel0,
                                           CharacterMesh->LightingChannels.bChannel1, bHeadFillPreviousChannel2);
        bHeadFillOwnsChannel = false;
    }
    HeadFillConfiguration->ReceiverMesh = CharacterMesh;
    HeadFillConfiguration->HeadFillLight = HeadFillLight;
    HeadFillConfiguration->OffsetFrame = nullptr;
    HeadFillConfiguration->bEnableHeadFill =
        bEnableHeadFill && !bDrone && !bAnimationManagedExternally && !ActorHasTag(TEXT("OutpostRole:Hologram"));
    HeadFillConfiguration->HeadFillSocket = HeadFillSocket;
    HeadFillConfiguration->HeadFillOffset = HeadFillOffset;
    HeadFillConfiguration->HeadFillLumens = HeadFillLumens;
    HeadFillConfiguration->HeadFillRadius = HeadFillRadius;
    HeadFillConfiguration->HeadFillSourceRadius = HeadFillSourceRadius;
    HeadFillConfiguration->RefreshReadabilityLighting();
}
void ASSOutpostAmbientActor::PlayClip(UAnimSequence *Clip, bool bLoop)
{
    if (Clip == ActiveAnimation || !CompatibleClip(CharacterMesh, Clip))
        return;
    CharacterMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    CharacterMesh->PlayAnimation(Clip, bLoop);
    ActiveAnimation = Clip;
}
bool ASSOutpostAmbientActor::TriggerAction(int32 Index)
{
    return TriggerActionClip(Index, nullptr);
}
bool ASSOutpostAmbientActor::TriggerActionClip(int32 Index, UAnimSequence *ClipOverride)
{
    if (!Actions.IsValidIndex(Index) || bDrone || bAnimationManagedExternally)
        return false;
    const FSSNpcAction &Action = Actions[Index];
    UAnimSequence *Clip = ClipOverride ? ClipOverride : Action.Clip.Get();
    if (!CompatibleClip(CharacterMesh, Clip))
        return false;
    ActiveAnimation = nullptr; // a second "cheers" is a second cheers, even mid-clip
    PlayClip(Clip, Action.bLoop);
    ActionRemaining = GestureRemaining = Action.bLoop ? FMath::Max(1.f, Action.LoopSeconds) : Clip->GetPlayLength();
    NextGesture = FMath::Max(0.f, GestureInterval) + FMath::Fmod(FMath::Abs(PhaseOffset), 6.f);
    return true;
}
FString ASSOutpostAmbientActor::TakeChatterLine()
{
    if (Chatter.IsEmpty())
        return FString();
    if (ChatterIndex == 0)
        ChatterIndex = FMath::RandRange(0, Chatter.Num() - 1); // not the same opener every visit
    return Chatter[ChatterIndex++ % Chatter.Num()];
}
int32 ASSOutpostAmbientActor::MatchAction(const FString &SpokenText) const
{
    const FString Text = SpokenText.ToLower();
    for (int32 I = 0; I < Actions.Num(); ++I)
        for (const FString &Word : Actions[I].Keywords)
            if (!Word.IsEmpty() && Text.Contains(Word.ToLower()))
                return I;
    return -1;
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
    RefreshReadabilityLighting();
}
void ASSOutpostAmbientActor::ApplyWorldOffset(const FVector &InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    RouteOrigin.AddToTranslation(InOffset);
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
    ActionRemaining = FMath::Max(0.f, ActionRemaining - Dt);
    NextGesture -= Dt;
    if (GestureRemaining <= 0.f && NextGesture <= 0.f && !GestureAnimations.IsEmpty())
    {
        auto *Gesture = GestureAnimations[GestureIndex++ % GestureAnimations.Num()].Get();
        if (CompatibleClip(CharacterMesh, Gesture))
        {
            PlayClip(Gesture, false);
            GestureRemaining = Gesture->GetPlayLength();
        }
        NextGesture = FMath::Max(0.f, GestureInterval) + FMath::Fmod(FMath::Abs(PhaseOffset), 6.f);
    }
    if (GestureRemaining <= 0.f)
        PlayClip(IdleAnimation, true);
    // Unprompted talk: the game mode decides whether anyone is in earshot and the channel is free.
    if (!Chatter.IsEmpty())
    {
        NextChatter -= Dt;
        if (NextChatter <= 0.f)
        {
            auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>();
            const bool Spoken = GM && GM->CrewChatter(this);
            NextChatter = Spoken ? FMath::Max(5.f, ChatterInterval) * FMath::FRandRange(1.f, 1.5f) : 4.f;
        }
    }
}
