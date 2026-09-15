#include "SSVFXPresentation.h"
#include "SSShip.h"
#include "SSShipPresentation.h"
#include "Components/SceneComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/PackageName.h"
#include "NiagaraComponent.h"
#include "NiagaraEmitter.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraRendererProperties.h"
#include "NiagaraSystem.h"
#include "Serialization/JsonSerializer.h"

namespace
{
float Bounded(float Value, float Low, float High, float Fallback)
{
    return FMath::IsFinite(Value) ? FMath::Clamp(Value, Low, High) : Fallback;
}
void ReleaseEffect(UNiagaraComponent *Component)
{
    if (!IsValid(Component))
        return;
    Component->DeactivateImmediate();
    Component->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
    if (Component->PoolingMethod == ENCPoolMethod::ManualRelease)
        Component->ReleaseToPool();
    else
        Component->DestroyComponent(); // Niagara pooling can be disabled by scalability/config.
}
ESSCombatVFX BoltKind(bool bFromPlayer, bool bHeavy)
{
    return !bFromPlayer ? ESSCombatVFX::EnemyBolt : (bHeavy ? ESSCombatVFX::CannonBolt : ESSCombatVFX::RapidBolt);
}
} // namespace

ASSCombatVFXAnchor::ASSCombatVFXAnchor()
{
    PrimaryActorTick.bCanEverTick = false;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("CosmeticOrigin"));
    SetActorEnableCollision(false);
}

bool USSCombatVFXSubsystem::DoesSupportWorldType(EWorldType::Type WorldType) const
{
    return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}
void USSCombatVFXSubsystem::Initialize(FSubsystemCollectionBase &Collection)
{
    Super::Initialize(Collection);
    // Load once per world, before play. An absent private pack intentionally keeps the native fallback.
    const TCHAR *Path = TEXT("/Game/SpaceSurvival/Licensed/Combat/DA_CombatVisuals");
    if (FPackageName::DoesPackageExist(Path))
        Presentation = LoadObject<USSCombatVFXData>(nullptr, Path);
    if (Presentation)
        for (const auto &Definition : Presentation->Effects)
            if (Definition.System && !Definition.ParticleScaleParameter.IsNone() &&
                Definition.System->GetExposedParameters().IndexOf(FNiagaraVariable(
                    FNiagaraTypeDefinition::GetFloatDef(), Definition.ParticleScaleParameter)) != INDEX_NONE)
                ValidScaleBindings.Add(Definition.Kind);
    Active.Reserve(64);
}
void USSCombatVFXSubsystem::OnWorldBeginPlay(UWorld &InWorld)
{
    Super::OnWorldBeginPlay(InWorld);
    if (Presentation)
        Anchor = InWorld.SpawnActor<ASSCombatVFXAnchor>();
}
void USSCombatVFXSubsystem::Deinitialize()
{
    for (const auto &Instance : Active)
        ReleaseEffect(Instance.Component);
    Active.Empty();
    if (IsValid(Anchor))
        Anchor->Destroy();
    Anchor = nullptr;
    Presentation = nullptr;
    ValidScaleBindings.Empty();
    Super::Deinitialize();
}
TStatId USSCombatVFXSubsystem::GetStatId() const
{
    RETURN_QUICK_DECLARE_CYCLE_STAT(USSCombatVFXSubsystem, STATGROUP_Tickables);
}
void USSCombatVFXSubsystem::Tick(float DeltaSeconds)
{
    const float Elapsed = FMath::IsFinite(DeltaSeconds) ? FMath::Max(0.f, DeltaSeconds) : 0.f;
    for (int32 Index = Active.Num() - 1; Index >= 0; --Index)
    {
        auto &Instance = Active[Index];
        Instance.Age += Elapsed;
        const bool bOwnerGone =
            Instance.bAttached && (!Instance.FollowOwner.IsValid() || Instance.FollowOwner->IsActorBeingDestroyed());
        if (!IsValid(Instance.Component) || bOwnerGone || Instance.Age >= Instance.MaximumSeconds ||
            Instance.Component->IsComplete())
        {
            ReleaseEffect(Instance.Component);
            Active.RemoveAtSwap(Index, 1, EAllowShrinking::No);
        }
    }
}
UNiagaraComponent *USSCombatVFXSubsystem::Spawn(ESSCombatVFX Kind, FVector Position, FRotator Rotation,
                                                AActor *FollowOwner, float Size)
{
    if (!Presentation || !IsValid(Anchor) || Position.ContainsNaN() || Rotation.ContainsNaN() ||
        Active.Num() >= FMath::Clamp(Presentation->MaximumActive, 0, 64))
        return nullptr;
    const FSSCombatVFXDefinition *Definition = Presentation->Effects.FindByPredicate(
        [Kind](const FSSCombatVFXDefinition &Entry) { return Entry.Kind == Kind; });
    if (!Definition || !Definition->System)
        return nullptr;
    int32 Count = 0;
    for (const auto &Instance : Active)
        Count += Instance.Kind == Kind ? 1 : 0;
    if (Count >= FMath::Clamp(Definition->ActiveLimit, 0, 32))
        return nullptr;
    if (const auto *Pawn = UGameplayStatics::GetPlayerPawn(this, 0))
        if (FVector::DistSquared(Pawn->GetActorLocation(), Position) >
            FMath::Square(Bounded(Presentation->MaximumDistance, 1000.f, 60000.f, 22000.f)))
            return nullptr;
    USceneComponent *Parent = IsValid(FollowOwner) ? FollowOwner->GetRootComponent() : Anchor->GetRootComponent();
    if (!Parent)
        return nullptr;
    const float SizeScale = Bounded(Size, .25f, 3.f, 1.f);
    // A system-specific particle-size parameter replaces transform scaling for
    // size variants; applying both would square the requested hull-radius ratio.
    const float TransformScale = ValidScaleBindings.Contains(Kind) ? 1.f : SizeScale;
    const FVector Scale(Bounded(float(Definition->Scale.X), .001f, 10.f, 1.f) * TransformScale,
                        Bounded(float(Definition->Scale.Y), .001f, 10.f, 1.f) * TransformScale,
                        Bounded(float(Definition->Scale.Z), .001f, 10.f, 1.f) * TransformScale);
    const FRotator Offset =
        Definition->RotationOffset.ContainsNaN() ? FRotator::ZeroRotator : Definition->RotationOffset;
    UNiagaraComponent *Component = UNiagaraFunctionLibrary::SpawnSystemAttached(
        Definition->System, Parent, NAME_None, Position, (Rotation.Quaternion() * Offset.Quaternion()).Rotator(), Scale,
        EAttachLocation::KeepWorldPosition, false, ENCPoolMethod::ManualRelease, false, false);
    // Niagara's attached pre-cull uses the parent position, not this world-space
    // burst position. The shared anchor may be far away after continuous flight;
    // admission above uses the actual effect location instead.
    if (!Component)
        return nullptr;
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCastShadow(false);
    Component->SetReceivesDecals(false);
    const float Bounds = Bounded(Definition->BoundsRadius, 100.f, 5000.f, 1500.f);
    Component->SetSystemFixedBounds(FBox(FVector(-Bounds), FVector(Bounds)));
    if (ValidScaleBindings.Contains(Kind))
        Component->SetVariableFloat(Definition->ParticleScaleParameter,
                                    Bounded(Definition->ParticleScale, .01f, 10.f, 1.f) * SizeScale);
    FSSCombatVFXInstance &Instance = Active.AddDefaulted_GetRef();
    Instance.Component = Component;
    Instance.Kind = Kind;
    Instance.MaximumSeconds = Bounded(Definition->MaximumSeconds, .02f, 8.f, .6f);
    Instance.bAttached = IsValid(FollowOwner);
    Instance.FollowOwner = FollowOwner;
    Component->Activate(true);
    return Component;
}
bool USSCombatVFXSubsystem::AttachProjectile(AActor *Projectile, bool bFromPlayer, bool bHeavy)
{
    return IsValid(Projectile) && Spawn(BoltKind(bFromPlayer, bHeavy), Projectile->GetActorLocation(),
                                        Projectile->GetActorRotation(), Projectile) != nullptr;
}
void USSCombatVFXSubsystem::PlayMuzzle(AActor *Source, FVector Position, FVector Direction, bool bFromPlayer,
                                       bool bHeavy)
{
    const ESSCombatVFX Kind =
        !bFromPlayer ? ESSCombatVFX::EnemyMuzzle : (bHeavy ? ESSCombatVFX::CannonMuzzle : ESSCombatVFX::RapidMuzzle);
    if (bFromPlayer)
        if (const auto *Ship = Cast<ASSShip>(Source))
            if (Ship->Presentation)
                Ship->Presentation->TryGetMuzzleWorldPosition(Position);
    Spawn(Kind, Position, Direction.Rotation(), Source);
}
void USSCombatVFXSubsystem::PlayImpact(FVector Position, FVector Normal, bool bFromPlayer, bool bHeavy)
{
    const ESSCombatVFX Kind =
        !bFromPlayer ? ESSCombatVFX::EnemyImpact : (bHeavy ? ESSCombatVFX::CannonImpact : ESSCombatVFX::RapidImpact);
    Spawn(Kind, Position, Normal.Rotation());
}
void USSCombatVFXSubsystem::PlayEnemyExplosion(FVector Position, float BodyRadius)
{
    Spawn(ESSCombatVFX::EnemyExplosion, Position, FRotator::ZeroRotator, nullptr,
          Bounded(BodyRadius / 140.f, .6f, 2.f, 1.f));
}
bool USSCombatVFXSubsystem::AttachAnomaly(AActor *Owner)
{
    return IsValid(Owner) &&
           Spawn(ESSCombatVFX::WormholeMouth, Owner->GetActorLocation(), Owner->GetActorRotation(), Owner) != nullptr;
}

FString USSVFXPresentationLibrary::DescribeSystem(UNiagaraSystem *System)
{
    const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetBoolField(TEXT("loaded"), IsValid(System));
    if (IsValid(System))
    {
        Root->SetStringField(TEXT("path"), System->GetPathName());
        TArray<TSharedPtr<FJsonValue>> Parameters;
        TArray<FNiagaraVariable> Variables;
        const auto &Store = System->GetExposedParameters();
        Store.GetParameters(Variables);
        for (const auto &Variable : Variables)
        {
            const auto Row = MakeShared<FJsonObject>();
            Row->SetStringField(TEXT("name"), Variable.GetName().ToString());
            Row->SetStringField(TEXT("type"), Variable.GetType().GetName());
            if (Variable.GetType() == FNiagaraTypeDefinition::GetFloatDef())
                Row->SetNumberField(TEXT("default"), Store.GetParameterValue<float>(Variable));
            else if (Variable.GetType() == FNiagaraTypeDefinition::GetIntDef())
                Row->SetNumberField(TEXT("default"), Store.GetParameterValue<int32>(Variable));
            else if (Variable.GetType() == FNiagaraTypeDefinition::GetBoolDef())
                Row->SetBoolField(TEXT("default"), Store.GetParameterValue<FNiagaraBool>(Variable).GetValue());
            else if (Variable.GetType() == FNiagaraTypeDefinition::GetColorDef())
                Row->SetStringField(TEXT("default"), Store.GetParameterValue<FLinearColor>(Variable).ToString());
            else if (Variable.GetType() == FNiagaraTypeDefinition::GetVec3Def())
                Row->SetStringField(TEXT("default"), Store.GetParameterValue<FVector3f>(Variable).ToString());
            Parameters.Add(MakeShared<FJsonValueObject>(Row));
        }
        Root->SetArrayField(TEXT("parameters"), Parameters);
        TArray<TSharedPtr<FJsonValue>> Emitters;
        for (const auto &Handle : System->GetEmitterHandles())
        {
            const auto Row = MakeShared<FJsonObject>();
            Row->SetStringField(TEXT("name"), Handle.GetName().ToString());
            Row->SetBoolField(TEXT("enabled"), Handle.GetIsEnabled());
            if (const auto *Data = Handle.GetInstance().GetEmitterData())
            {
                Row->SetBoolField(TEXT("local_space"), Data->bLocalSpace);
                Row->SetStringField(TEXT("simulation"),
                                    Data->SimTarget == ENiagaraSimTarget::CPUSim ? TEXT("CPU") : TEXT("GPU"));
                TArray<TSharedPtr<FJsonValue>> Renderers;
                for (const auto *Renderer : Data->GetRenderers())
                    if (Renderer)
                    {
                        const auto RendererRow = MakeShared<FJsonObject>();
                        RendererRow->SetStringField(TEXT("class"), Renderer->GetClass()->GetName());
                        RendererRow->SetBoolField(TEXT("enabled"), Renderer->GetIsEnabled());
                        Renderers.Add(MakeShared<FJsonValueObject>(RendererRow));
                    }
                Row->SetArrayField(TEXT("renderers"), Renderers);
            }
            Emitters.Add(MakeShared<FJsonValueObject>(Row));
        }
        Root->SetArrayField(TEXT("emitters"), Emitters);
    }
    FString Result;
    FJsonSerializer::Serialize(Root, TJsonWriterFactory<>::Create(&Result));
    return Result;
}
bool USSVFXPresentationLibrary::PreparePrivateSystem(UNiagaraSystem *System, bool bLocalSpace)
{
#if WITH_EDITOR
    if (!IsValid(System) || !System->GetPathName().StartsWith(TEXT("/Game/SpaceSurvival/Licensed/Combat/")))
        return false;
    for (const auto &Handle : System->GetEmitterHandles())
    {
        const auto Emitter = Handle.GetInstance();
        const auto *Data = Emitter.GetEmitterData();
        if (!Data || !Emitter.Emitter || Emitter.Emitter->GetOutermost() != System->GetOutermost())
            return false; // Never edit a shared external emitter or original vendor asset.
        for (const auto *Renderer : Data->GetRenderers())
            if (Renderer && Renderer->GetOutermost() != System->GetOutermost())
                return false;
    }
    System->Modify();
    for (const auto &Handle : System->GetEmitterHandles())
    {
        const auto Emitter = Handle.GetInstance();
        auto *Data = Emitter.GetEmitterData();
        Emitter.Emitter->Modify();
        Data->bLocalSpace = bLocalSpace;
        for (auto *Renderer : Data->GetRenderers())
            if (Renderer && Renderer->GetClass()->GetName().Contains(TEXT("LightRenderer")))
                Renderer->SetIsEnabled(false);
    }
    System->RequestCompile(true);
    System->WaitForCompilationComplete(false, false);
    return true;
#else
    return false;
#endif
}
