#include "SSStationVisualLayout.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#if WITH_EDITORONLY_DATA
#include "Components/ArrowComponent.h"
#include "Components/BoxComponent.h"
#endif

ASSStationVisualLayout::ASSStationVisualLayout()
{
    PrimaryActorTick.bCanEverTick = false;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("LayoutRoot"));
    SetActorEnableCollision(false);
#if WITH_EDITORONLY_DATA
    auto *Lane = CreateDefaultSubobject<UBoxComponent>(TEXT("Guide_KeepDockingLaneClear"));
    Lane->SetupAttachment(RootComponent);
    Lane->SetRelativeLocation(FVector(-92.5f, 0, 478.75f));
    Lane->SetBoxExtent(FVector(1807.5f, 700, 488.75f));
    Lane->ShapeColor = FColor::Cyan;
    Lane->bIsEditorOnly = true;
    Lane->SetHiddenInGame(true);
    Lane->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Lane->SetGenerateOverlapEvents(false);
    Lane->SetCanEverAffectNavigation(false);
    const FVector Anchors[] = {FVector(200, -1000, 0), FVector(-800, -1000, 0), FVector(-1100, 850, 0),
                               FVector(0, 1000, 0),    FVector(950, -450, 0),   FVector(1000, 1000, 0),
                               FVector(-1400, 0, 0),   FVector(-300, 0, 180),   FVector(850, 0, 220)};
    const TCHAR *Names[] = {
        TEXT("Guide_Upgrades_Loadout"), TEXT("Guide_Repair_ShipBay"), TEXT("Guide_Contracts_Record"),
        TEXT("Guide_Save_Settings"),    TEXT("Guide_Launch"),         TEXT("Guide_Mica"),
        TEXT("Guide_Beacon"),           TEXT("Guide_WalkSpawn"),      TEXT("Guide_DockedShip")};
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Anchors); ++Index)
    {
        auto *Guide = CreateDefaultSubobject<UArrowComponent>(FName(Names[Index]));
        Guide->SetupAttachment(RootComponent);
        Guide->SetRelativeLocation(Anchors[Index]);
        Guide->ArrowColor = FColor::Yellow;
        Guide->ArrowSize = 2;
        Guide->bIsEditorOnly = true;
        Guide->SetHiddenInGame(true);
        Guide->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Guide->SetCanEverAffectNavigation(false);
    }
#endif
}

void ASSStationVisualLayout::OnConstruction(const FTransform &Transform)
{
    Super::OnConstruction(Transform);
    EnforcePresentationOnly();
}

void ASSStationVisualLayout::EnforcePresentationOnly()
{
    SetActorEnableCollision(false);
    TInlineComponentArray<UPrimitiveComponent *> Primitives(this);
    for (auto *Component : Primitives)
    {
        Component->SetCollisionProfileName(TEXT("NoCollision"));
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        if (auto *Staff = Cast<USkeletalMeshComponent>(Component))
        {
            Staff->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
            Staff->bEnableUpdateRateOptimizations = true;
            Staff->SetComponentTickInterval(1.f / 30.f);
        }
    }
}

#if WITH_EDITOR
#include "SSStation.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "Engine/Engine.h"
#include "Engine/SCS_Node.h"
#include "Engine/SimpleConstructionScript.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"

namespace
{
const TCHAR *LayoutPackage = TEXT("/Game/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout");

struct FStationAuthorWorld
{
    UWorld *World = nullptr;
    FStationAuthorWorld()
    {
        const auto Initialization = UWorld::InitializationValues()
                                        .AllowAudioPlayback(false)
                                        .RequiresHitProxies(false)
                                        .CreatePhysicsScene(true)
                                        .CreateNavigation(false)
                                        .CreateAISystem(false)
                                        .ShouldSimulatePhysics(false);
        World = UWorld::CreateWorld(EWorldType::EditorPreview, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num,
                                    &Initialization);
        if (World)
            GEngine->CreateNewWorldContext(EWorldType::EditorPreview).SetCurrentWorld(World);
    }
    ~FStationAuthorWorld()
    {
        if (World)
        {
            GEngine->DestroyWorldContext(World);
            World->DestroyWorld(false);
        }
    }
};

FVector JsonVector(const TSharedPtr<FJsonObject> &Object, const TCHAR *Key, FVector Default)
{
    const TArray<TSharedPtr<FJsonValue>> *Values = nullptr;
    if (Object->TryGetArrayField(Key, Values) && Values->Num() == 3)
        return FVector((*Values)[0]->AsNumber(), (*Values)[1]->AsNumber(), (*Values)[2]->AsNumber());
    return Default;
}

FTransform JsonTransform(const TSharedPtr<FJsonObject> &Object)
{
    const FVector Rotation = JsonVector(Object, TEXT("rotation"), FVector::ZeroVector);
    return FTransform(FRotator(Rotation.X, Rotation.Y, Rotation.Z),
                      JsonVector(Object, TEXT("location"), FVector::ZeroVector),
                      JsonVector(Object, TEXT("scale"), FVector::OneVector));
}
} // namespace
#endif

UBlueprint *USSStationLayoutAuthoringLibrary::CreateStationVisualLayout(const FString &RecipeJson, bool bResetExisting)
{
#if WITH_EDITOR
    UBlueprint *Blueprint =
        FPackageName::DoesPackageExist(LayoutPackage) ? LoadObject<UBlueprint>(nullptr, LayoutPackage) : nullptr;
    if (Blueprint && !bResetExisting)
        return Blueprint;
    if (Blueprint && Blueprint->ParentClass != ASSStationVisualLayout::StaticClass())
    {
        UE_LOG(LogTemp, Error, TEXT("Station layout has an unexpected parent; preserving it."));
        return nullptr;
    }
    TSharedPtr<FJsonObject> Recipe;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(RecipeJson.IsEmpty() ? TEXT("{}") : RecipeJson),
                                      Recipe) ||
        !Recipe)
    {
        UE_LOG(LogTemp, Error, TEXT("Invalid station layout recipe JSON."));
        return nullptr;
    }
    FStationAuthorWorld Fixture;
    if (!Fixture.World)
    {
        UE_LOG(LogTemp, Error, TEXT("Station layout: no authoring world."));
        return nullptr;
    }
    auto *Donor = Fixture.World->SpawnActor<ASSStation>();
    Donor->bUseEditableLayout = false;
    Donor->BuildHub(false);
    if (!Blueprint)
        Blueprint = FKismetEditorUtilities::CreateBlueprint(
            ASSStationVisualLayout::StaticClass(), CreatePackage(LayoutPackage), TEXT("BP_StationVisualLayout"),
            BPTYPE_Normal, UBlueprint::StaticClass(), UBlueprintGeneratedClass::StaticClass(),
            TEXT("StationLayoutAuthoring"));
    if (!Blueprint || !Blueprint->SimpleConstructionScript)
    {
        UE_LOG(LogTemp, Error, TEXT("Station layout: no Blueprint or construction script."));
        return nullptr;
    }
    auto *SCS = Blueprint->SimpleConstructionScript.Get();
    const TArray<USCS_Node *> OldNodes = SCS->GetAllNodes();
    for (auto *Node : OldNodes)
        SCS->RemoveNode(Node);
    TSet<FName> Names;
    TArray<FString> Exclusions;
    const TArray<TSharedPtr<FJsonValue>> *Values = nullptr;
    if (Recipe->TryGetArrayField(TEXT("exclude_harvested"), Values))
        for (const auto &Value : *Values)
            Exclusions.Add(Value->AsString());
    auto Excluded = [&Exclusions](const FString &Name)
    {
        for (const auto &Pattern : Exclusions)
            if (Name.MatchesWildcard(Pattern))
                return true;
        return false;
    };
    auto AddNode = [SCS, &Names](UClass *Class, const FString &Name, const FTransform &Transform)
    {
        const FName NodeName(*Name);
        if (Names.Contains(NodeName) || Transform.ContainsNaN() ||
            Transform.GetScale3D().GetAbsMin() <= UE_SMALL_NUMBER)
        {
            UE_LOG(LogTemp, Error, TEXT("Station layout: component '%s' rejected (%s)."), *Name,
                   Names.Contains(NodeName)  ? TEXT("duplicate name")
                   : Transform.ContainsNaN() ? TEXT("NaN transform")
                                             : TEXT("zero scale"));
            return static_cast<USceneComponent *>(nullptr);
        }
        Names.Add(NodeName);
        auto *Node = SCS->CreateNode(Class, NodeName);
        SCS->AddNode(Node);
        Node->SetParent(GetDefault<ASSStationVisualLayout>()->GetRootComponent());
        auto *Component = CastChecked<USceneComponent>(Node->ComponentTemplate);
        Component->SetRelativeTransform(Transform);
        Component->SetMobility(EComponentMobility::Movable);
        Component->ComponentTags.Add(TEXT("StationAuthoredVisual"));
        if (auto *Primitive = Cast<UPrimitiveComponent>(Component))
        {
            Primitive->SetCollisionProfileName(TEXT("NoCollision"));
            Primitive->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Primitive->SetGenerateOverlapEvents(false);
            Primitive->SetCanEverAffectNavigation(false);
        }
        return Component;
    };
    auto AddStatic = [&AddNode](const FString &Name, UStaticMesh *Mesh, const FTransform &Transform,
                                const TArray<UMaterialInterface *> &Materials, bool Shadows, const TArray<FName> &Tags)
    {
        auto *Target = Cast<UStaticMeshComponent>(AddNode(UStaticMeshComponent::StaticClass(), Name, Transform));
        if (!Target || !Mesh)
        {
            if (!Mesh)
                UE_LOG(LogTemp, Error, TEXT("Station layout: '%s' has no mesh."), *Name);
            return false;
        }
        Target->SetStaticMesh(Mesh);
        Target->SetCastShadow(Shadows);
        for (int32 Slot = 0; Slot < Materials.Num(); ++Slot)
        {
            if (!Materials[Slot])
            {
                UE_LOG(LogTemp, Error, TEXT("Station layout: '%s' material slot %d is empty."), *Name, Slot);
                return false;
            }
            Target->SetMaterial(Slot, Materials[Slot]);
        }
        Target->ComponentTags.Append(Tags);
        return true;
    };
    TInlineComponentArray<UStaticMeshComponent *> MeshComponents(Donor);
    for (auto *Source : MeshComponents)
    {
        const bool Shell = Source->GetName().StartsWith(TEXT("LicensedStation_"));
        const bool Detail = Source->ComponentHasTag(TEXT("StationVisualDetail"));
        const bool Exterior =
            Source->GetStaticMesh() && Source->GetStaticMesh()->GetName() == TEXT("SM_StationExterior");
        if (!Shell && !Detail && !Exterior)
            continue;
        TArray<UMaterialInterface *> Materials;
        for (int32 Slot = 0; Slot < Source->GetNumMaterials(); ++Slot)
            Materials.Add(Source->GetMaterial(Slot));
        auto *Instanced = Cast<UInstancedStaticMeshComponent>(Source);
        const int32 Count = Instanced ? Instanced->GetInstanceCount() : 1;
        for (int32 Index = 0; Index < Count; ++Index)
        {
            const FString Name = FString::Printf(
                TEXT("%s_%03d"), *(Shell ? TEXT("Shell_") + Source->GetStaticMesh()->GetName() : Source->GetName()),
                Index);
            if (Excluded(Name))
                continue;
            FTransform Transform = Source->GetComponentTransform();
            if (Instanced)
                Instanced->GetInstanceTransform(Index, Transform, true);
            if (!AddStatic(Name, Source->GetStaticMesh(), Transform.GetRelativeTransform(Donor->GetActorTransform()),
                           Materials, Source->CastShadow, Source->ComponentTags))
                return nullptr;
        }
    }
    TInlineComponentArray<USkeletalMeshComponent *> StaffComponents(Donor);
    for (auto *Source : StaffComponents)
    {
        if (!Source->ComponentHasTag(TEXT("StationRobotStaff")) || Excluded(Source->GetName()))
            continue;
        auto *Target = Cast<USkeletalMeshComponent>(
            AddNode(USkeletalMeshComponent::StaticClass(), Source->GetName(), Source->GetRelativeTransform()));
        if (!Target)
            return nullptr;
        Target->SetSkeletalMeshAsset(Source->GetSkeletalMeshAsset());
        for (int32 Slot = 0; Slot < Source->GetNumMaterials(); ++Slot)
            Target->SetMaterial(Slot, Source->GetMaterial(Slot));
        Target->ComponentTags.Append(Source->ComponentTags);
        Target->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
        Target->bEnableUpdateRateOptimizations = true;
        Target->bComponentUseFixedSkelBounds = true;
        Target->SetComponentTickInterval(1.f / 30.f);
        if (auto *Animation = Source->GetSingleNodeInstance())
            Target->OverrideAnimationData(Animation->GetCurrentAsset(), true, true, Source->GetPosition(),
                                          Source->GetPlayRate());
    }
    TInlineComponentArray<UPointLightComponent *> Lights(Donor);
    for (int32 Index = 0; Index < Lights.Num(); ++Index)
    {
        const FString Name = FString::Printf(TEXT("BayLight_%d"), Index);
        if (Excluded(Name))
            continue;
        auto *Source = Lights[Index];
        auto *Target = Cast<UPointLightComponent>(
            AddNode(UPointLightComponent::StaticClass(), Name, Source->GetRelativeTransform()));
        Target->SetIntensity(Source->Intensity);
        Target->SetAttenuationRadius(Source->AttenuationRadius);
        Target->SetLightColor(Source->GetLightColor());
        Target->SetCastShadows(Source->CastShadows);
    }
    if (Recipe->TryGetArrayField(TEXT("static_meshes"), Values))
        for (const auto &Value : *Values)
        {
            const auto Object = Value->AsObject();
            if (!Object)
                return nullptr;
            auto *Mesh = LoadObject<UStaticMesh>(nullptr, *Object->GetStringField(TEXT("asset")));
            if (!Mesh)
            {
                UE_LOG(LogTemp, Error, TEXT("Station layout: recipe asset '%s' did not load."),
                       *Object->GetStringField(TEXT("asset")));
                return nullptr;
            }
            TArray<UMaterialInterface *> Materials;
            for (int32 Slot = 0; Slot < Mesh->GetStaticMaterials().Num(); ++Slot)
                Materials.Add(Mesh->GetMaterial(Slot));
            const TArray<TSharedPtr<FJsonValue>> *Overrides = nullptr;
            if (Object->TryGetArrayField(TEXT("materials"), Overrides))
                for (int32 Slot = 0; Slot < Overrides->Num(); ++Slot)
                {
                    if (!Materials.IsValidIndex(Slot))
                    {
                        UE_LOG(LogTemp, Error, TEXT("Station layout: '%s' overrides material slot %d, which it lacks."),
                               *Object->GetStringField(TEXT("name")), Slot);
                        return nullptr;
                    }
                    Materials[Slot] = LoadObject<UMaterialInterface>(nullptr, *(*Overrides)[Slot]->AsString());
                }
            bool Shadows = true;
            Object->TryGetBoolField(TEXT("cast_shadows"), Shadows);
            if (!AddStatic(Object->GetStringField(TEXT("name")), Mesh, JsonTransform(Object), Materials, Shadows,
                           {FName(TEXT("StationVisualDetail"))}))
                return nullptr;
        }
    if (Recipe->TryGetArrayField(TEXT("point_lights"), Values))
        for (const auto &Value : *Values)
        {
            const auto Object = Value->AsObject();
            if (!Object)
                return nullptr;
            auto *Target = Cast<UPointLightComponent>(AddNode(
                UPointLightComponent::StaticClass(), Object->GetStringField(TEXT("name")), JsonTransform(Object)));
            if (!Target)
                return nullptr;
            const FVector Color = JsonVector(Object, TEXT("color"), FVector::OneVector);
            Target->SetLightColor(FLinearColor(Color.X, Color.Y, Color.Z));
            Target->SetIntensity(Object->GetNumberField(TEXT("intensity")));
            Target->SetAttenuationRadius(Object->GetNumberField(TEXT("attenuation_radius")));
            bool Shadows = false;
            Object->TryGetBoolField(TEXT("cast_shadows"), Shadows);
            Target->SetCastShadows(Shadows);
        }
    Blueprint->MarkPackageDirty();
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
    if (Blueprint->Status == BS_Error || !Blueprint->GeneratedClass)
    {
        UE_LOG(LogTemp, Error, TEXT("Station layout: Blueprint failed to compile (%d components)."), Names.Num());
        return nullptr;
    }
    UE_LOG(LogTemp, Display,
           TEXT("Station editable layout authored with %d individual components; save through author script."),
           Names.Num());
    return Blueprint;
#else
    return nullptr;
#endif
}

FString USSStationLayoutAuthoringLibrary::DescribeStationVisualLayout(UBlueprint *Blueprint)
{
#if WITH_EDITOR
    if (!Blueprint || !Blueprint->SimpleConstructionScript)
        return TEXT("{}");
    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("path"), Blueprint->GetPathName());
    Report->SetStringField(TEXT("parent"),
                           Blueprint->ParentClass ? Blueprint->ParentClass->GetPathName() : TEXT("None"));
    Report->SetBoolField(TEXT("compiled"), Blueprint->Status != BS_Error && Blueprint->GeneratedClass != nullptr);
    TArray<TSharedPtr<FJsonValue>> Components;
    for (auto *Node : Blueprint->SimpleConstructionScript->GetAllNodes())
    {
        auto *Component = Cast<USceneComponent>(Node->ComponentTemplate);
        if (!Component)
            continue;
        TSharedRef<FJsonObject> Entry = MakeShared<FJsonObject>();
        Entry->SetStringField(TEXT("name"), Node->GetVariableName().ToString());
        Entry->SetStringField(TEXT("class"), Component->GetClass()->GetName());
        Entry->SetStringField(TEXT("transform"), Component->GetRelativeTransform().ToString());
        if (auto *Primitive = Cast<UPrimitiveComponent>(Component))
        {
            Entry->SetBoolField(TEXT("collision_disabled"),
                                Primitive->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
            Entry->SetBoolField(TEXT("overlap_disabled"), !Primitive->GetGenerateOverlapEvents());
            Entry->SetBoolField(TEXT("navigation_disabled"), !Primitive->CanEverAffectNavigation());
        }
        if (auto *Mesh = Cast<UStaticMeshComponent>(Component))
            Entry->SetStringField(TEXT("mesh"), GetPathNameSafe(Mesh->GetStaticMesh()));
        if (auto *Mesh = Cast<USkeletalMeshComponent>(Component))
            Entry->SetStringField(TEXT("mesh"), GetPathNameSafe(Mesh->GetSkeletalMeshAsset()));
        Components.Add(MakeShared<FJsonValueObject>(Entry));
    }
    Report->SetArrayField(TEXT("components"), Components);
    FString Result;
    FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Result));
    return Result;
#else
    return TEXT("{}");
#endif
}
