#include "SSCryoChamber.h"
#include "Components/CapsuleComponent.h"
#include "Components/MeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraComponent.h"
#include "TimerManager.h"

namespace
{
const FName FreezeParameter(TEXT("FreezeAmount"));
}

ASSCryoChamber::ASSCryoChamber()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("ChamberRoot"));
    BodyCollision = CreateDefaultSubobject<UCapsuleComponent>(TEXT("BodyCollision"));
    BodyCollision->SetupAttachment(RootComponent);
    BodyCollision->InitCapsuleSize(80.f, 160.f);
    BodyCollision->SetRelativeLocation(FVector(0.f, 0.f, 160.f));
    BodyCollision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    BodyCollision->SetCollisionObjectType(ECC_WorldStatic);
    BodyCollision->SetCollisionResponseToAllChannels(ECR_Ignore);
    BodyCollision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
    BodyCollision->SetGenerateOverlapEvents(false);
    BodyCollision->SetCanEverAffectNavigation(false);
    LeftNozzle = CreateDefaultSubobject<UNiagaraComponent>(TEXT("LeftNozzle"));
    RightNozzle = CreateDefaultSubobject<UNiagaraComponent>(TEXT("RightNozzle"));
    for (auto *Nozzle : {LeftNozzle.Get(), RightNozzle.Get()})
    {
        Nozzle->SetupAttachment(RootComponent);
        Nozzle->SetAutoActivate(false);
    }
}

void ASSCryoChamber::BeginPlay()
{
    Super::BeginPlay();
    for (auto *Nozzle : {LeftNozzle.Get(), RightNozzle.Get()})
    {
        Nozzle->SetAsset(JetSystem);
        Nozzle->DeactivateImmediate();
    }
    bConfigured = JetSystem && BindPanes();
}

bool ASSCryoChamber::BindPanes()
{
    if (FrostSurfaces.IsEmpty())
        return false;
    TSet<UMeshComponent *> Seen;
    for (AActor *Surface : FrostSurfaces)
    {
        if (!IsValid(Surface))
        {
            RestoreMaterials();
            return false;
        }
        int32 Bound = 0;
        TArray<UMeshComponent *> Meshes;
        Surface->GetComponents<UMeshComponent>(Meshes);
        for (auto *Mesh : Meshes)
        {
            if (Seen.Contains(Mesh))
                continue;
            Seen.Add(Mesh);
            for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
            {
                auto *Original = Mesh->GetMaterial(Slot);
                float Normal = 0.f;
                if (!Original || !Original->GetScalarParameterValue(FMaterialParameterInfo(FreezeParameter), Normal))
                    continue;
                auto *Dynamic = Mesh->CreateDynamicMaterialInstance(Slot, Original);
                if (!Dynamic)
                    continue;
                auto &Pane = Panes.AddDefaulted_GetRef();
                Pane.Mesh = Mesh;
                Pane.Slot = Slot;
                Pane.Original = Original;
                Pane.Dynamic = Dynamic;
                Pane.NormalAmount = Normal;
                ++Bound;
            }
        }
        if (Bound == 0)
        {
            RestoreMaterials();
            return false;
        }
    }
    return !Panes.IsEmpty();
}

FVector ASSCryoChamber::GetUseLocation() const
{
    return GetActorTransform().TransformPosition(UsePoint);
}

bool ASSCryoChamber::CanUse(const APawn *User) const
{
    if (!IsValid(User) || User->GetWorld() != GetWorld() || !GetWorld() ||
        FVector::DistSquared(User->GetActorLocation(), GetUseLocation()) > FMath::Square(UseDistance))
        return false;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(CryoUse), false, User);
    Query.AddIgnoredActor(this);
    for (const AActor *Surface : FrostSurfaces)
        if (IsValid(Surface))
            Query.AddIgnoredActor(Surface);
    FHitResult Hit;
    return !GetWorld()->LineTraceSingleByChannel(Hit, User->GetPawnViewLocation(), GetUseLocation(), ECC_Visibility,
                                                 Query);
}

ASSCryoChamber *ASSCryoChamber::FindFocused(const APawn *User, const FVector &ViewDirection)
{
    if (!IsValid(User) || !User->GetWorld())
        return nullptr;
    ASSCryoChamber *Best = nullptr;
    float BestScore = MAX_flt;
    for (TActorIterator<ASSCryoChamber> It(User->GetWorld()); It; ++It)
    {
        if (!It->CanUse(User))
            continue;
        const FVector Delta = It->GetUseLocation() - User->GetPawnViewLocation();
        const float Facing = FVector::DotProduct(ViewDirection.GetSafeNormal(), Delta.GetSafeNormal());
        if (Facing < .25f)
            continue;
        const float Score = Delta.Size() * (1.25f - .5f * Facing);
        if (Score < BestScore)
        {
            BestScore = Score;
            Best = *It;
        }
    }
    return Best;
}

FString ASSCryoChamber::Interact(APawn *User)
{
    if (!CanUse(User))
        return TEXT("Move closer and keep the chamber access point in view.");
    if (bCooling)
        return TEXT("Cooling cycle already running.");
    if (!bConfigured)
        return TEXT("The chamber frost or nozzle effect is not configured.");
    // Recheck references at action time; no partial cycle if a pane has disappeared.
    for (const auto &Pane : Panes)
        if (!IsValid(Pane.Mesh) || !IsValid(Pane.Dynamic) || Pane.Mesh->GetMaterial(Pane.Slot) != Pane.Dynamic)
            return TEXT("The chamber glazing changed. Reload its presentation before use.");
    bCooling = true;
    CycleStartedAt = GetWorld()->GetTimeSeconds();
    CycleElapsed = 0.f;
    SetFreeze(0.f);
    LeftNozzle->Activate(true);
    RightNozzle->Activate(true);
    SetActorTickEnabled(true);
    GetWorldTimerManager().SetTimer(FinishTimer, this, &ASSCryoChamber::FinishCycle, CycleDuration, false);
    return TEXT("Hypercooling / four-second cycle.");
}

void ASSCryoChamber::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bCooling)
        return;
    CycleElapsed = FMath::Clamp(float(GetWorld()->GetTimeSeconds() - CycleStartedAt), 0.f, CycleDuration);
    // Let the downward jets read through clear glass before the frost closes the view.
    const float Rise = FMath::Clamp((CycleElapsed - .65f) / .6f, 0.f, 1.f);
    const float Fall = FMath::Clamp((CycleDuration - CycleElapsed) / .6f, 0.f, 1.f);
    SetFreeze(FMath::Min(Rise, Fall));
    if (CycleElapsed >= CycleDuration)
        FinishCycle();
}

void ASSCryoChamber::SetFreeze(float Amount)
{
    FreezeAmount = FMath::Clamp(Amount, 0.f, 1.f);
    for (const auto &Pane : Panes)
        if (IsValid(Pane.Dynamic))
            Pane.Dynamic->SetScalarParameterValue(FreezeParameter, FMath::Lerp(Pane.NormalAmount, 1.f, FreezeAmount));
}

void ASSCryoChamber::FinishCycle()
{
    GetWorldTimerManager().ClearTimer(FinishTimer);
    SetFreeze(0.f);
    LeftNozzle->DeactivateImmediate();
    RightNozzle->DeactivateImmediate();
    bCooling = false;
    CycleElapsed = 0.f;
    SetActorTickEnabled(false);
}

void ASSCryoChamber::RestoreMaterials()
{
    for (const auto &Pane : Panes)
        if (IsValid(Pane.Mesh) && Pane.Mesh->GetMaterial(Pane.Slot) == Pane.Dynamic)
            Pane.Mesh->SetMaterial(Pane.Slot, Pane.Original);
    Panes.Reset();
}

void ASSCryoChamber::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    FinishCycle();
    RestoreMaterials();
    Super::EndPlay(EndPlayReason);
}
