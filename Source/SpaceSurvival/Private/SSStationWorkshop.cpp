#include "SSStationVisualLayout.h"

#if WITH_EDITOR
#include "Animation/AnimationAsset.h"
#include "Components/BillboardComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/LightComponent.h"
#include "Components/MeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/RectLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Editor.h"
#include "EditorViewportClient.h"
#include "Engine/DirectionalLight.h"
#include "GameFramework/GameModeBase.h"
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "Engine/Brush.h"
#include "Engine/PointLight.h"
#include "Engine/RectLight.h"
#include "Engine/SCS_Node.h"
#include "Engine/SimpleConstructionScript.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/SkeletalMeshActor.h"
#include "Engine/SpotLight.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "FileHelpers.h"
#include "GameFramework/DefaultPhysicsVolume.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/FileManager.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Materials/MaterialInterface.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "NiagaraActor.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#include "UObject/UnrealType.h"

namespace StationWorkshop
{
const TCHAR *MapPackage = TEXT("/Game/SpaceSurvival/Licensed/StationWorkshop/L_StationWorkshop");
const TCHAR *WorkshopLayoutPackage = TEXT("/Game/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout");
const FName GuideTag(TEXT("StationWorkshopGuide"));

bool EditorReady(FString &Result)
{
    if (!GEditor || GEditor->PlayWorld)
    {
        Result = TEXT("Stop Play/Simulate before editing the Station Workshop.");
        return false;
    }
    return true;
}

bool IsSupportedComponent(const USceneComponent *Component)
{
    const UClass *Class = Component->GetClass();
    return Class == UStaticMeshComponent::StaticClass() || Class == USkeletalMeshComponent::StaticClass() ||
           Class == UPointLightComponent::StaticClass() || Class == USpotLightComponent::StaticClass() ||
           Class == URectLightComponent::StaticClass() || Class == UNiagaraComponent::StaticClass();
}

bool IsSupportedActor(const AActor *Actor)
{
    const UClass *Class = Actor->GetClass();
    return Class == AActor::StaticClass() || Class == AStaticMeshActor::StaticClass() ||
           Class == ASkeletalMeshActor::StaticClass() || Class == APointLight::StaticClass() ||
           Class == ASpotLight::StaticClass() || Class == ARectLight::StaticClass() ||
           Class == ANiagaraActor::StaticClass();
}

struct FPlacement
{
    FString Name;
    USceneComponent *Component = nullptr;
    FTransform Transform;
};

bool Collect(UWorld *World, TArray<FPlacement> &Placements, FString &Result)
{
    if (!World || World->GetOutermost()->GetName() != MapPackage)
    {
        Result = TEXT("Open Station Workshop first. Apply/export only accepts its saved workshop level.");
        return false;
    }
    if (World->GetLevels().Num() != 1)
    {
        Result = TEXT("Streaming sublevels are not supported. Place workshop assets in the persistent level.");
        return false;
    }
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor *Actor = *It;
        // EditorActorSubsystem excludes transient infrastructure such as water/debugger managers.
        // Keep visible/editable transient actors in validation so user placements cannot silently vanish.
        if (Actor->HasAnyFlags(RF_Transient) && (!Actor->IsEditable() || !Actor->IsListedInSceneOutliner()))
            continue;
        if (Actor == World->GetWorldSettings() || Actor == World->GetDefaultBrush() ||
            Actor->IsA<ADefaultPhysicsVolume>() || Actor->IsEditorOnly())
            continue;
        if (!IsSupportedActor(Actor))
        {
            Result =
                FString::Printf(TEXT("Unsupported actor '%s' (%s). Use individual static/skeletal meshes, "
                                     "point/spot/rect lights or Niagara systems; Blueprint behavior is not exported."),
                                *Actor->GetActorLabel(), *Actor->GetClass()->GetName());
            return false;
        }
        int32 Added = 0;
        TInlineComponentArray<USceneComponent *> Components(Actor);
        for (auto *Component : Components)
        {
            if (Component->IsEditorOnly() || Component->GetClass() == USceneComponent::StaticClass() ||
                Component->IsA<UBillboardComponent>())
                continue;
            if (!IsSupportedComponent(Component))
            {
                Result =
                    FString::Printf(TEXT("Unsupported component '%s' on '%s' (%s). Nothing was applied."),
                                    *Component->GetName(), *Actor->GetActorLabel(), *Component->GetClass()->GetName());
                return false;
            }
            const FTransform Transform = Component->GetComponentTransform();
            if (Transform.ContainsNaN() || Transform.GetScale3D().GetAbsMin() <= UE_SMALL_NUMBER)
            {
                Result = FString::Printf(TEXT("'%s' has invalid or zero scale. Use finite, nonzero transforms."),
                                         *Actor->GetActorLabel());
                return false;
            }
            if (const auto *Mesh = Cast<UStaticMeshComponent>(Component); Mesh && !Mesh->GetStaticMesh())
            {
                Result = FString::Printf(TEXT("'%s' has no static mesh assigned."), *Actor->GetActorLabel());
                return false;
            }
            if (const auto *Mesh = Cast<USkeletalMeshComponent>(Component); Mesh && !Mesh->GetSkeletalMeshAsset())
            {
                Result = FString::Printf(TEXT("'%s' has no skeletal mesh assigned."), *Actor->GetActorLabel());
                return false;
            }
            if (const auto *Effect = Cast<UNiagaraComponent>(Component); Effect && !Effect->GetAsset())
            {
                Result = FString::Printf(TEXT("'%s' has no Niagara system assigned."), *Actor->GetActorLabel());
                return false;
            }
            Placements.Add({Actor->GetActorLabel() + TEXT("_") + Component->GetName(), Component, Transform});
            ++Added;
        }
        if (Added == 0)
        {
            Result = FString::Printf(TEXT("'%s' contains no supported visual components."), *Actor->GetActorLabel());
            return false;
        }
    }
    if (Placements.IsEmpty())
    {
        Result = TEXT("The workshop is empty. Refusing to replace the station with an empty layout.");
        return false;
    }
    Placements.Sort([](const FPlacement &A, const FPlacement &B) { return A.Name < B.Name; });
    return true;
}

bool Backup(const FString &PackageName, const FString &Directory, FString &Result)
{
    FString Filename;
    if (!FPackageName::DoesPackageExist(PackageName, &Filename))
    {
        Result = TEXT("Cannot back up missing saved package: ") + PackageName;
        return false;
    }
    IFileManager &Files = IFileManager::Get();
    if (!Files.MakeDirectory(*Directory, true))
    {
        Result = TEXT("Cannot create private backup folder: ") + Directory;
        return false;
    }
    const FString Candidates[] = {Filename, FPaths::ChangeExtension(Filename, TEXT("uexp")),
                                  FPaths::ChangeExtension(Filename, TEXT("ubulk"))};
    for (const FString &Source : Candidates)
        if (Files.FileExists(*Source) &&
            Files.Copy(*(Directory / FPaths::GetCleanFilename(Source)), *Source, false, false) != COPY_OK)
        {
            Result = TEXT("Backup failed; station was not changed: ") + Source;
            return false;
        }
    return true;
}

USceneComponent *DuplicateVisual(USceneComponent *Source, UObject *Outer, FName Name, const FTransform &Transform)
{
    // UObject duplication retains serializable component properties, including material slot overrides,
    // animation data, light settings and Niagara user parameters. Do not copy only a mesh/transform subset.
    auto *Copy = DuplicateObject<USceneComponent>(Source, Outer, Name);
    Copy->ClearFlags(RF_Transient | RF_DuplicateTransient | RF_TextExportTransient);
    Copy->SetFlags(RF_Transactional);
    Copy->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
    Copy->SetAbsolute(false, false, false);
    Copy->SetRelativeTransform(Transform);
    Copy->SetHiddenInGame(Source->bHiddenInGame || (Source->GetOwner() && Source->GetOwner()->IsHidden()));
    Copy->SetCanEverAffectNavigation(false);
    return Copy;
}

USCS_Node *AddVisualNode(UBlueprint *Blueprint, const FPlacement &Placement, int32 Index)
{
    auto *Copy = DuplicateVisual(Placement.Component, GetTransientPackage(),
                                 MakeUniqueObjectName(GetTransientPackage(), Placement.Component->GetClass(),
                                                      *FString::Printf(TEXT("Workshop_%04d"), Index)),
                                 Placement.Transform);
    Copy->SetFlags(RF_ArchetypeObject | RF_Public);
    Copy->CreationMethod = EComponentCreationMethod::SimpleConstructionScript;
    Copy->SetMobility(EComponentMobility::Movable);
    Copy->ComponentTags.AddUnique(TEXT("StationAuthoredVisual"));
    Copy->ComponentTags.AddUnique(FName(*Placement.Name));
    // The station still owns gameplay collision. This workshop is explicitly a visual composition tool.
    if (auto *Primitive = Cast<UPrimitiveComponent>(Copy))
    {
        Primitive->SetCollisionProfileName(TEXT("NoCollision"));
        Primitive->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Primitive->SetGenerateOverlapEvents(false);
    }
    auto *Node = Blueprint->SimpleConstructionScript->CreateNodeAndRenameComponent(Copy);
    Blueprint->SimpleConstructionScript->AddNode(Node);
    Node->SetParent(GetDefault<ASSStationVisualLayout>()->GetRootComponent());
    return Node;
}

TArray<TSharedPtr<FJsonValue>> VectorJson(const FVector &Value)
{
    return {MakeShared<FJsonValueNumber>(Value.X), MakeShared<FJsonValueNumber>(Value.Y),
            MakeShared<FJsonValueNumber>(Value.Z)};
}

TSharedRef<FJsonObject> Describe(const FPlacement &Placement, int32 Index)
{
    auto Entry = MakeShared<FJsonObject>();
    const USceneComponent *Component = Placement.Component;
    Entry->SetStringField(TEXT("id"), Component->GetOwner()->GetActorGuid().ToString(EGuidFormats::Digits) + TEXT("/") +
                                          Component->GetName());
    Entry->SetStringField(TEXT("name"), Placement.Name);
    Entry->SetStringField(TEXT("component_class"), Component->GetClass()->GetPathName());
    Entry->SetArrayField(TEXT("location_cm"), VectorJson(Placement.Transform.GetLocation()));
    Entry->SetArrayField(TEXT("scale"), VectorJson(Placement.Transform.GetScale3D()));
    const FQuat Rotation = Placement.Transform.GetRotation();
    Entry->SetArrayField(TEXT("rotation_xyzw"),
                         {MakeShared<FJsonValueNumber>(Rotation.X), MakeShared<FJsonValueNumber>(Rotation.Y),
                          MakeShared<FJsonValueNumber>(Rotation.Z), MakeShared<FJsonValueNumber>(Rotation.W)});
    Entry->SetBoolField(TEXT("visible"), Component->IsVisible());
    Entry->SetBoolField(TEXT("hidden_in_game"), Component->bHiddenInGame || Component->GetOwner()->IsHidden());
    if (const auto *Mesh = Cast<UStaticMeshComponent>(Component))
        Entry->SetStringField(TEXT("asset"), Mesh->GetStaticMesh()->GetPathName());
    if (const auto *Mesh = Cast<USkeletalMeshComponent>(Component))
    {
        Entry->SetStringField(TEXT("asset"), Mesh->GetSkeletalMeshAsset()->GetPathName());
        Entry->SetNumberField(TEXT("animation_mode"), Mesh->GetAnimationMode());
        Entry->SetStringField(TEXT("animation"), GetPathNameSafe(Mesh->AnimationData.AnimToPlay));
    }
    if (const auto *Effect = Cast<UNiagaraComponent>(Component))
        Entry->SetStringField(TEXT("asset"), GetPathNameSafe(Effect->GetAsset()));
    if (const auto *Mesh = Cast<UMeshComponent>(Component))
    {
        TArray<TSharedPtr<FJsonValue>> Materials;
        for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
            Materials.Add(MakeShared<FJsonValueString>(GetPathNameSafe(Mesh->GetMaterial(Slot))));
        Entry->SetArrayField(TEXT("materials"), Materials);
    }
    // UE property text retains tunable settings not covered by the normalized fields above.
    // It contains references/settings, not textures or mesh payloads; the saved map remains authoritative.
    auto Properties = MakeShared<FJsonObject>();
    for (TFieldIterator<FProperty> It(Component->GetClass()); It; ++It)
        if ((It->HasAnyPropertyFlags(CPF_Edit) || It->GetFName() == TEXT("OverrideParameters") ||
             It->GetFName() == TEXT("AnimationData")) &&
            !It->HasAnyPropertyFlags(CPF_Transient | CPF_InstancedReference) &&
            It->GetFName() != TEXT("AttachParent") && It->GetFName() != TEXT("AttachChildren"))
        {
            FString Value;
            It->ExportTextItem_Direct(Value, It->ContainerPtrToValuePtr<void>(Component), nullptr,
                                      const_cast<USceneComponent *>(Component), PPF_None);
            Properties->SetStringField(It->GetName(), Value);
        }
    Entry->SetObjectField(TEXT("editable_properties_ue"), Properties);
    return Entry;
}
} // namespace StationWorkshop
#endif

bool USSStationLayoutAuthoringLibrary::OpenStationWorkshop(FString &Result)
{
#if WITH_EDITOR
    using namespace StationWorkshop;
    if (!EditorReady(Result))
        return false;
    UWorld *Current = GEditor->GetEditorWorldContext().World();
    if (Current && Current->GetOutermost()->GetName() == MapPackage)
    {
        Result = TEXT("Station Workshop is already open; current edits were preserved.");
        return true;
    }
    // Cancellation aborts the switch. Do not silently discard another open level or dirty assets.
    if (!FEditorFileUtils::SaveDirtyPackages(true, true, true, false, false, false))
    {
        Result = TEXT("Opening the workshop was cancelled while saving current work.");
        return false;
    }
    FString Filename;
    if (FPackageName::DoesPackageExist(MapPackage, &Filename))
    {
        const bool Loaded = UEditorLoadingAndSavingUtils::LoadMap(Filename) != nullptr;
        Result =
            Loaded ? TEXT("Opened your saved Station Workshop unchanged.") : TEXT("Could not load saved workshop.");
        return Loaded;
    }
    auto *Layout = LoadObject<UBlueprint>(nullptr, WorkshopLayoutPackage);
    if (!Layout || !Layout->GeneratedClass || Layout->Status == BS_Error)
    {
        Result = TEXT("The saved BP_StationVisualLayout must exist and compile before creating a workshop.");
        return false;
    }
    UWorld *World = GEditor->NewMap(false);
    if (!World)
    {
        Result = TEXT("Could not create the empty workshop editor level.");
        return false;
    }
    World->GetWorldSettings()->DefaultGameMode = AGameModeBase::StaticClass();
    FActorSpawnParameters Spawn;
    Spawn.ObjectFlags = RF_Transactional;
    auto *Source = World->SpawnActor<ASSStationVisualLayout>(Layout->GeneratedClass, FTransform::Identity, Spawn);
    if (!Source)
    {
        Result = TEXT("Could not instantiate the existing station layout.");
        return false;
    }
    int32 Count = 0;
    TInlineComponentArray<USceneComponent *> Components(Source);
    for (auto *Component : Components)
    {
        if (Component->IsEditorOnly() || Component == Source->GetRootComponent())
            continue;
        if (!IsSupportedComponent(Component))
        {
            Result = TEXT("Existing layout includes unsupported component: ") + Component->GetName();
            World->DestroyActor(Source);
            return false;
        }
        auto *Actor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity, Spawn);
        auto *Copy = DuplicateVisual(Component, Actor, TEXT("Visual"), Component->GetComponentTransform());
        Copy->CreationMethod = EComponentCreationMethod::Instance;
        Actor->SetRootComponent(Copy);
        Actor->AddInstanceComponent(Copy);
        Copy->RegisterComponent();
        Actor->SetActorLabel(Component->GetName());
        Actor->SetFolderPath(TEXT("Station Layout"));
        ++Count;
    }
    World->DestroyActor(Source);
    auto *Guides =
        World->SpawnActor<ASSStationVisualLayout>(ASSStationVisualLayout::StaticClass(), FTransform::Identity, Spawn);
    Guides->bIsEditorOnlyActor = true;
    Guides->Tags.Add(GuideTag);
    Guides->SetActorLabel(TEXT("GUIDES - fixed service anchors and docking lane"));
    Guides->SetFolderPath(TEXT("Workshop Guides"));
    auto *PreviewLight = World->SpawnActor<ADirectionalLight>(ADirectionalLight::StaticClass(),
                                                              FTransform(FRotator(-35, -25, 0)), Spawn);
    PreviewLight->bIsEditorOnlyActor = true;
    PreviewLight->Tags.Add(GuideTag);
    PreviewLight->SetActorLabel(TEXT("GUIDE - workshop preview light (not exported)"));
    PreviewLight->SetFolderPath(TEXT("Workshop Guides"));
    PreviewLight->GetLightComponent()->SetIntensity(1.5f);
    PreviewLight->GetLightComponent()->SetCastShadows(false);
    for (FEditorViewportClient *Viewport : GEditor->GetAllViewportClients())
        if (Viewport && Viewport->IsLevelEditorClient() && Viewport->GetWorld() == World)
        {
            Viewport->SetViewLocation(FVector(-1300, -600, 550));
            Viewport->SetViewRotation(FRotator(-12, 18, 0));
            Viewport->Invalidate();
        }
    World->MarkPackageDirty();
    if (!UEditorLoadingAndSavingUtils::SaveMap(World, MapPackage))
    {
        Result = TEXT("Workshop was created but could not be saved. Preserve this open level with Save As.");
        return false;
    }
    Result = FString::Printf(TEXT("Created Station Workshop with %d individually editable visuals. "
                                  "Save edits, then Apply to Station. Guides do not enter the game."),
                             Count);
    return true;
#else
    Result = TEXT("Station Workshop is available only in Unreal Editor.");
    return false;
#endif
}

bool USSStationLayoutAuthoringLibrary::ApplyStationWorkshop(FString &Result)
{
#if WITH_EDITOR
    using namespace StationWorkshop;
    if (!EditorReady(Result))
        return false;
    UWorld *World = GEditor->GetEditorWorldContext().World();
    TArray<FPlacement> Placements;
    if (!Collect(World, Placements, Result))
    {
        UE_LOG(LogTemp, Display, TEXT("Station Workshop validation: %s"), *Result);
        return false;
    }
    auto *Layout = LoadObject<UBlueprint>(nullptr, WorkshopLayoutPackage);
    if (!Layout || !Layout->SimpleConstructionScript || Layout->ParentClass != ASSStationVisualLayout::StaticClass())
    {
        Result = TEXT("The station visual Blueprint is missing or has an unexpected parent. Nothing was applied.");
        return false;
    }
    if (Layout->GetOutermost()->IsDirty() &&
        !UEditorLoadingAndSavingUtils::SavePackagesWithDialog({Layout->GetOutermost()}, true))
    {
        Result = TEXT("Save existing Blueprint edits before applying the workshop.");
        return false;
    }
    const FString BackupDirectory = FPaths::ProjectDir() / TEXT(".agent/local/StationWorkshop/Backups") /
                                    (FDateTime::UtcNow().ToString(TEXT("%Y%m%dT%H%M%S")) + TEXT("-") +
                                     FGuid::NewGuid().ToString(EGuidFormats::Digits));
    if (!Backup(WorkshopLayoutPackage, BackupDirectory, Result) || !Backup(MapPackage, BackupDirectory, Result))
        return false;
    if (!UEditorLoadingAndSavingUtils::SaveMap(World, MapPackage))
    {
        Result = TEXT("Could not save workshop edits. Runtime station was not changed.");
        return false;
    }
    // Compile a disposable candidate first; a bad imported property cannot replace the current Blueprint.
    auto *Candidate = FKismetEditorUtilities::CreateBlueprint(
        ASSStationVisualLayout::StaticClass(), GetTransientPackage(),
        MakeUniqueObjectName(GetTransientPackage(), UBlueprint::StaticClass(), TEXT("StationWorkshopCandidate")),
        BPTYPE_Normal, UBlueprint::StaticClass(), UBlueprintGeneratedClass::StaticClass(), TEXT("StationWorkshop"));
    if (!Candidate)
    {
        Result = TEXT("Could not create validation Blueprint. Runtime station was not changed.");
        return false;
    }
    for (int32 Index = 0; Index < Placements.Num(); ++Index)
        AddVisualNode(Candidate, Placements[Index], Index);
    FKismetEditorUtilities::CompileBlueprint(Candidate);
    if (Candidate->Status == BS_Error || !Candidate->GeneratedClass)
    {
        Result = TEXT("Workshop validation compile failed. Runtime station was not changed.");
        return false;
    }
    const FScopedTransaction Transaction(NSLOCTEXT("StationWorkshop", "Apply", "Apply Station Workshop"));
    Layout->Modify();
    auto *SCS = Layout->SimpleConstructionScript.Get();
    SCS->Modify();
    const TArray<USCS_Node *> OldRoots = SCS->GetRootNodes();
    const TArray<USCS_Node *> OldNodes = SCS->GetAllNodes();
    struct FNodeLinks
    {
        TArray<USCS_Node *> Children;
        FName Parent;
        FName OwnerClass;
        bool Native = false;
    };
    TMap<USCS_Node *, FNodeLinks> OldLinks;
    for (auto *Node : OldNodes)
    {
        FNodeLinks Links;
        for (auto *Child : Node->GetChildNodes())
            Links.Children.Add(Child);
        Links.Parent = Node->ParentComponentOrVariableName;
        Links.OwnerClass = Node->ParentComponentOwnerClassName;
        Links.Native = Node->bIsParentComponentNative;
        OldLinks.Add(Node, Links);
    }
    for (auto *Node : OldNodes)
        for (auto *Child : OldLinks[Node].Children)
            Node->RemoveChildNode(Child);
    for (auto *Root : OldRoots)
        SCS->RemoveNode(Root, false);
    TArray<USCS_Node *> NewNodes;
    for (int32 Index = 0; Index < Placements.Num(); ++Index)
        NewNodes.Add(AddVisualNode(Layout, Placements[Index], Index));
    FKismetEditorUtilities::CompileBlueprint(Layout);
    Layout->MarkPackageDirty();
    if (Layout->Status == BS_Error || !Layout->GeneratedClass ||
        !UEditorLoadingAndSavingUtils::SavePackages({Layout->GetOutermost()}, false))
    {
        for (auto *Node : NewNodes)
            SCS->RemoveNode(Node);
        for (auto *Root : OldRoots)
            SCS->AddNode(Root);
        for (auto *Node : OldNodes)
        {
            const auto &Links = OldLinks[Node];
            for (auto *Child : Links.Children)
                Node->AddChildNode(Child);
            Node->ParentComponentOrVariableName = Links.Parent;
            Node->ParentComponentOwnerClassName = Links.OwnerClass;
            Node->bIsParentComponentNative = Links.Native;
        }
        FKismetEditorUtilities::CompileBlueprint(Layout);
        Layout->MarkPackageDirty();
        Result = TEXT("Apply failed; previous component tree restored in memory. Saved backups: ") + BackupDirectory;
        return false;
    }
    Result = FString::Printf(TEXT("Applied %d visuals to the station and saved the workshop. Backup: %s. "
                                  "Collision/services remain native; those reported bugs are unchanged."),
                             Placements.Num(), *BackupDirectory);
    return true;
#else
    Result = TEXT("Station Workshop is available only in Unreal Editor.");
    return false;
#endif
}

bool USSStationLayoutAuthoringLibrary::ExportStationWorkshop(const FString &FilePath, FString &Result)
{
#if WITH_EDITOR
    using namespace StationWorkshop;
    if (!EditorReady(Result))
        return false;
    UWorld *World = GEditor->GetEditorWorldContext().World();
    TArray<FPlacement> Placements;
    if (!Collect(World, Placements, Result))
    {
        UE_LOG(LogTemp, Display, TEXT("Station Workshop validation: %s"), *Result);
        return false;
    }
    FString Destination = FilePath;
    if (Destination.IsEmpty())
        Destination = FPaths::ProjectDir() / TEXT(".agent/local/StationWorkshop/StationWorkshop.layout.json");
    Destination = FPaths::ConvertRelativePathToFull(Destination);
    if (!Destination.EndsWith(TEXT(".json")))
    {
        Result = TEXT("Choose a .json filename for the placement export.");
        return false;
    }
    auto Root = MakeShared<FJsonObject>();
    Root->SetStringField(TEXT("schema"), TEXT("spacesurvival.station-workshop.v1"));
    Root->SetStringField(TEXT("source_map"), MapPackage);
    Root->SetStringField(TEXT("target_blueprint"), WorkshopLayoutPackage);
    Root->SetStringField(TEXT("exported_utc"), FDateTime::UtcNow().ToIso8601());
    Root->SetStringField(TEXT("coordinate_system"),
                         TEXT("Unreal left-handed Z-up; world origin equals station layout origin; centimetres"));
    Root->SetStringField(TEXT("hierarchy_policy"),
                         TEXT("Flattened component world transforms; saved map retains editing hierarchy"));
    Root->SetBoolField(TEXT("includes_unsaved_editor_changes"), World->GetOutermost()->IsDirty());
    Root->SetStringField(TEXT("collision_policy"), TEXT("presentation_only_native_station_collision_unchanged"));
    TArray<TSharedPtr<FJsonValue>> Entries;
    for (int32 Index = 0; Index < Placements.Num(); ++Index)
        Entries.Add(MakeShared<FJsonValueObject>(Describe(Placements[Index], Index)));
    Root->SetArrayField(TEXT("placements"), Entries);
    FString Json;
    FJsonSerializer::Serialize(Root, TJsonWriterFactory<>::Create(&Json));
    if (!IFileManager::Get().MakeDirectory(*FPaths::GetPath(Destination), true) ||
        !FFileHelper::SaveStringToFile(Json, *Destination, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
    {
        Result = TEXT("Could not write layout export: ") + Destination;
        return false;
    }
    Result = TEXT("Exported layout references/settings to ") + Destination +
             TEXT(". Model/texture files remain in the private project Content folders.");
    return true;
#else
    Result = TEXT("Station Workshop is available only in Unreal Editor.");
    return false;
#endif
}
