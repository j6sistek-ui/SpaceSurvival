#include "SSStationVisualLayout.h"
#include "Animation/SkeletalMeshActor.h"
#include "AssetRegistry/AssetData.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Components/MeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "ContentBrowserModule.h"
#include "ContentBrowserDataSubsystem.h"
#include "IContentBrowserDataModule.h"
#include "Editor.h"
#include "Engine/Level.h"
#include "Engine/Selection.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "Framework/Application/SlateApplication.h"
#include "Framework/Docking/TabManager.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "IContentBrowserSingleton.h"
#include "ImageUtils.h"
#include "LevelEditorViewport.h"
#include "Materials/MaterialInterface.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "NiagaraActor.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "ScopedTransaction.h"
#include "Styling/AppStyle.h"
#include "ToolMenus.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SComboBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "SpaceSurvivalWorkshop"
DEFINE_LOG_CATEGORY_STATIC(LogStationWorkshop, Log, All);

namespace StationWorkshop
{
const FName TabId(TEXT("SpaceSurvival.StationWorkshop"));
const FString MapPackage(TEXT("/Game/SpaceSurvival/Licensed/StationWorkshop/L_StationWorkshop"));
const TCHAR *MaterialNames[] = {TEXT("Steel"),          TEXT("Dark steel"), TEXT("Painted white"), TEXT("Copper"),
                                TEXT("Caution yellow"), TEXT("Rubber"),     TEXT("Glass"),         TEXT("Cyan light"),
                                TEXT("Amber light"),    TEXT("Red light")};

UWorld *GetEditableWorld()
{
    if (!GEditor || GEditor->PlayWorld)
        return nullptr;
    UWorld *World = GEditor->GetEditorWorldContext().World();
    return World && World->WorldType == EWorldType::Editor && World->GetOutermost()->GetName() == MapPackage ? World
                                                                                                             : nullptr;
}
} // namespace StationWorkshop

class FSpaceSurvivalEditorModule : public IModuleInterface
{
public:
    virtual void StartupModule() override
    {
        if (IsRunningCommandlet() || !FSlateApplication::IsInitialized())
            return;
        bRegistered = true;
        for (const TCHAR *Name : StationWorkshop::MaterialNames)
            MaterialOptions.Add(MakeShared<FString>(Name));
        SelectedMaterial = MaterialOptions[0];
        Status =
            LOCTEXT("Ready", "Open the workshop to edit your saved station. Changes stay local until Save + Apply.");
        FGlobalTabmanager::Get()
            ->RegisterNomadTabSpawner(StationWorkshop::TabId,
                                      FOnSpawnTab::CreateRaw(this, &FSpaceSurvivalEditorModule::SpawnWorkshopTab))
            .SetDisplayName(LOCTEXT("TabTitle", "Station Workshop"))
            .SetMenuType(ETabSpawnerMenuType::Hidden);
        UToolMenus::RegisterStartupCallback(
            FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FSpaceSurvivalEditorModule::RegisterMenus));
        OpenCommand = IConsoleManager::Get().RegisterConsoleCommand(
            TEXT("SS.Workshop.Open"), TEXT("Open the Station Workshop editor tab."),
            FConsoleCommandDelegate::CreateRaw(this, &FSpaceSurvivalEditorModule::ShowWorkshop), ECVF_Default);
        CaptureCommand = IConsoleManager::Get().RegisterConsoleCommand(
            TEXT("SS.Workshop.Capture"), TEXT("Capture the open workshop tab to a new absolute .png path."),
            FConsoleCommandWithArgsDelegate::CreateRaw(this, &FSpaceSurvivalEditorModule::CaptureWorkshop),
            ECVF_Default);
    }

    virtual void ShutdownModule() override
    {
        if (!bRegistered)
            return;
        UToolMenus::UnRegisterStartupCallback(this);
        UToolMenus::UnregisterOwner(this);
        IConsoleManager::Get().UnregisterConsoleObject(OpenCommand);
        IConsoleManager::Get().UnregisterConsoleObject(CaptureCommand);
        if (TSharedPtr<SDockTab> Tab = WorkshopTab.Pin())
            Tab->RequestCloseTab();
        FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(StationWorkshop::TabId);
    }

private:
    bool bRegistered = false;
    TArray<TSharedPtr<FString>> MaterialOptions;
    TSharedPtr<FString> SelectedMaterial;
    TWeakPtr<SDockTab> WorkshopTab;
    FText Status;
    IConsoleObject *OpenCommand = nullptr;
    IConsoleObject *CaptureCommand = nullptr;

    void SetStatus(const FString &Message)
    {
        Status = FText::FromString(Message);
        UE_LOG(LogStationWorkshop, Display, TEXT("%s"), *Message);
    }

    void RegisterMenus()
    {
        FToolMenuOwnerScoped Owner(this);
        UToolMenu *Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Tools");
        Menu->FindOrAddSection("SpaceSurvival", LOCTEXT("MenuSection", "SpaceSurvival"))
            .AddMenuEntry("StationWorkshop", LOCTEXT("MenuLabel", "Station Workshop"),
                          LOCTEXT("MenuHint", "Arrange station assets and apply the saved layout to the game."),
                          FSlateIcon(FAppStyle::GetAppStyleSetName(), "Icons.Layout"),
                          FUIAction(FExecuteAction::CreateRaw(this, &FSpaceSurvivalEditorModule::ShowWorkshop)));
    }

    void ShowWorkshop()
    {
        FGlobalTabmanager::Get()->TryInvokeTab(StationWorkshop::TabId);
    }

    TSharedRef<SDockTab> SpawnWorkshopTab(const FSpawnTabArgs &Args)
    {
        FAssetPickerConfig Picker;
        Picker.Filter.PackagePaths = {FName("/Game"), FName("/Engine/BasicShapes")};
        Picker.Filter.ClassPaths = {UStaticMesh::StaticClass()->GetClassPathName(),
                                    USkeletalMesh::StaticClass()->GetClassPathName(),
                                    UNiagaraSystem::StaticClass()->GetClassPathName()};
        Picker.Filter.bRecursivePaths = true;
        Picker.Filter.bRecursiveClasses = true;
        TArray<FAssetData> AvailableAssets;
        FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry")
            .Get()
            .GetAssets(Picker.Filter, AvailableAssets);
        UWorld *EditorWorld = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
        UE_LOG(LogStationWorkshop, Display,
               TEXT("Workshop catalog: %d matching assets, world=%s type=%d PIE=%d enabled=%d"), AvailableAssets.Num(),
               EditorWorld ? *EditorWorld->GetOutermost()->GetName() : TEXT("none"),
               EditorWorld ? static_cast<int32>(EditorWorld->WorldType) : -1, GEditor && GEditor->PlayWorld ? 1 : 0,
               StationWorkshop::GetEditableWorld() ? 1 : 0);
        // UE5.8 SAssetPicker treats source paths as Content Browser virtual paths, not package paths.
        UContentBrowserDataSubsystem *BrowserData = IContentBrowserDataModule::Get().GetSubsystem();
        for (FName &Path : Picker.Filter.PackagePaths)
            Path = BrowserData->ConvertInternalPathToVirtual(Path);
        Picker.InitialAssetViewType = EAssetViewType::Tile;
        Picker.SelectionMode = ESelectionMode::Single;
        Picker.bAllowNullSelection = false;
        Picker.bAllowDragging = true;
        Picker.bAllowRename = false;
        // Folder mode suppresses recursive enumeration in SAssetPicker even with bRecursivePaths set.
        // This is deliberately a flat, searchable catalog of every imported placeable asset.
        Picker.bCanShowFolders = false;
        Picker.AssetShowWarningText = LOCTEXT(
            "NoAssets",
            "No matching assets. Clear the search or filters; downloaded Fab packs must be added to this project.");
        Picker.bForceShowEngineContent = true;
        Picker.bCanShowRealTimeThumbnails = false;
        Picker.bAddFilterUI = true;
        Picker.bShowPathInColumnView = true;
        Picker.SaveSettingsName = TEXT("SpaceSurvivalStationWorkshop");
        Picker.OnAssetDoubleClicked = FOnAssetDoubleClicked::CreateRaw(this, &FSpaceSurvivalEditorModule::PlaceAsset);
        const TSharedRef<SWidget> AssetPicker =
            FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser").Get().CreateAssetPicker(Picker);

        FSlateFontInfo HeadingFont = FAppStyle::GetFontStyle("NormalText");
        HeadingFont.Size = 18;
        TSharedRef<SDockTab> Tab = SNew(SDockTab).TabRole(ETabRole::NomadTab)[SNew(SBorder).Padding(
            14)[SNew(SVerticalBox) +
                SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 6)
                    [SNew(STextBlock).Text(LOCTEXT("Heading", "SPACE SURVIVAL / STATION WORKSHOP")).Font(HeadingFont)] +
                SVerticalBox::Slot().AutoHeight().Padding(
                    0, 0, 0,
                    10)[SNew(STextBlock)
                            .AutoWrapText(true)
                            .Text(LOCTEXT("Intro", "Build in the level viewport. Drag an asset into the scene, or "
                                                   "double-click to place it in front of the camera."))] +
                SVerticalBox::Slot().AutoHeight().Padding(
                    0, 0, 0,
                    8)[SNew(SHorizontalBox) +
                       SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 6, 0)
                           [SNew(SButton)
                                .Text(LOCTEXT("Open", "Open Workshop"))
                                .OnClicked_Raw(this, &FSpaceSurvivalEditorModule::OpenWorkshop)] +
                       SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 6, 0)
                           [SNew(SButton)
                                .Text(LOCTEXT("SaveApply", "Save + Apply"))
                                .ToolTipText(LOCTEXT("ApplyHint", "Save this workshop and update the station layout "
                                                                  "used on the next Play session."))
                                .OnClicked_Raw(this, &FSpaceSurvivalEditorModule::ApplyWorkshop)] +
                       SHorizontalBox::Slot()
                           .AutoWidth()[SNew(SButton)
                                            .Text(LOCTEXT("Export", "Export Layout"))
                                            .ToolTipText(LOCTEXT("ExportHint", "Export asset references and placements "
                                                                               "to a private local JSON file."))
                                            .OnClicked_Raw(this, &FSpaceSurvivalEditorModule::ExportWorkshop)]] +
                SVerticalBox::Slot().AutoHeight().Padding(
                    0, 0, 0,
                    10)[SNew(STextBlock)
                            .AutoWrapText(true)
                            .Text(LOCTEXT("Controls", "Select in viewport or Outliner. W move / E rotate / R scale / "
                                                      "Delete remove / Ctrl+W duplicate / Ctrl+Z undo. Use viewport "
                                                      "snapping. F frames the selection."))] +
                SVerticalBox::Slot().AutoHeight().Padding(
                    0, 0, 0, 6)[SNew(STextBlock).Text(LOCTEXT("Materials", "10 MATERIAL PRESETS"))] +
                SVerticalBox::Slot().AutoHeight().Padding(
                    0, 0, 0,
                    10)[SNew(SHorizontalBox) +
                        SHorizontalBox::Slot().FillWidth(1).Padding(0, 0, 6, 0)
                            [SNew(SComboBox<TSharedPtr<FString>>)
                                 .OptionsSource(&MaterialOptions)
                                 .InitiallySelectedItem(SelectedMaterial)
                                 .OnGenerateWidget_Lambda([](TSharedPtr<FString> Option)
                                                          { return SNew(STextBlock).Text(FText::FromString(*Option)); })
                                 .OnSelectionChanged_Lambda(
                                     [this](TSharedPtr<FString> Option, ESelectInfo::Type)
                                     { SelectedMaterial = Option; })[SNew(STextBlock)
                                                                         .Text_Lambda(
                                                                             [this]()
                                                                             {
                                                                                 return FText::FromString(
                                                                                     SelectedMaterial.IsValid()
                                                                                         ? *SelectedMaterial
                                                                                         : FString());
                                                                             })]] +
                        SHorizontalBox::Slot().AutoWidth()
                            [SNew(SButton)
                                 .Text(LOCTEXT("ApplyMaterial", "Apply to selection"))
                                 .ToolTipText(LOCTEXT("MaterialHint", "Replace every material slot on selected meshes. "
                                                                      "Ctrl+Z restores the original materials."))
                                 .OnClicked_Raw(this, &FSpaceSurvivalEditorModule::ApplyMaterial)]] +
                SVerticalBox::Slot().AutoHeight().Padding(
                    0, 0, 0, 6)[SNew(STextBlock).Text(LOCTEXT("Assets", "IMPORTED ASSETS + BASIC SHAPES"))] +
                SVerticalBox::Slot().FillHeight(
                    1)[SNew(SBox).MinDesiredWidth(420).MinDesiredHeight(320).IsEnabled_Lambda(
                    []() { return StationWorkshop::GetEditableWorld() != nullptr; })[AssetPicker]] +
                SVerticalBox::Slot().AutoHeight().Padding(
                    0, 10, 0, 0)[SNew(STextBlock)
                                     .AutoWrapText(true)
                                     .ColorAndOpacity(FLinearColor(0.55f, 0.87f, 0.93f))
                                     .Text_Lambda([this]() { return Status; })] +
                SVerticalBox::Slot().AutoHeight().Padding(
                    0, 8, 0,
                    0)[SNew(STextBlock)
                           .AutoWrapText(true)
                           .Text(LOCTEXT("Boundary", "Visual layout only. Service markers and collision remain "
                                                     "game-controlled. Downloaded Fab assets must first be added to "
                                                     "this project. Save + Apply does not upload or publish."))]]];
        Tab->SetContent(SNew(SBox).MinDesiredWidth(440).MinDesiredHeight(650)[Tab->GetContent()]);
        WorkshopTab = Tab;
        return Tab;
    }

    FReply OpenWorkshop()
    {
        FString Message;
        USSStationLayoutAuthoringLibrary::OpenStationWorkshop(Message);
        SetStatus(Message);
        return FReply::Handled();
    }

    FReply ApplyWorkshop()
    {
        FString Message;
        USSStationLayoutAuthoringLibrary::ApplyStationWorkshop(Message);
        SetStatus(Message);
        return FReply::Handled();
    }

    FReply ExportWorkshop()
    {
        const FString Path = FPaths::ConvertRelativePathToFull(FPaths::Combine(
            FPaths::ProjectDir(), TEXT(".agent/local/StationWorkshop/Exports"),
            FString::Printf(TEXT("StationLayout-%s-%s.json"), *FDateTime::UtcNow().ToString(TEXT("%Y%m%dT%H%M%SZ")),
                            *FGuid::NewGuid().ToString(EGuidFormats::Digits).Left(8))));
        FString Message;
        USSStationLayoutAuthoringLibrary::ExportStationWorkshop(Path, Message);
        SetStatus(Message);
        return FReply::Handled();
    }

    void PlaceAsset(const FAssetData &Asset)
    {
        UWorld *World = StationWorkshop::GetEditableWorld();
        if (!World)
        {
            SetStatus(TEXT("Open the Station Workshop and stop Play before placing assets."));
            return;
        }
        UObject *Object = Asset.GetAsset(); // Only load the asset the owner actually places.
        UClass *ActorClass = Cast<UStaticMesh>(Object)      ? AStaticMeshActor::StaticClass()
                             : Cast<USkeletalMesh>(Object)  ? ASkeletalMeshActor::StaticClass()
                             : Cast<UNiagaraSystem>(Object) ? ANiagaraActor::StaticClass()
                                                            : nullptr;
        if (!ActorClass)
        {
            SetStatus(TEXT("This asset could not be loaded as a static mesh, skeletal mesh or Niagara system."));
            return;
        }
        FVector Location(0, 0, 100);
        if (GCurrentLevelEditingViewportClient && GCurrentLevelEditingViewportClient->GetWorld() == World)
            Location = GCurrentLevelEditingViewportClient->GetViewLocation() +
                       GCurrentLevelEditingViewportClient->GetViewRotation().Vector() * 600;
        const FScopedTransaction Transaction(LOCTEXT("PlaceTransaction", "Place station asset"));
        World->Modify();
        World->GetCurrentLevel()->Modify();
        AActor *Actor = GEditor->AddActor(World->GetCurrentLevel(), ActorClass, FTransform(Location));
        if (!Actor)
        {
            SetStatus(TEXT("Unreal could not create the selected asset actor."));
            return;
        }
        Actor->Modify();
        if (AStaticMeshActor *MeshActor = Cast<AStaticMeshActor>(Actor))
            MeshActor->GetStaticMeshComponent()->SetStaticMesh(CastChecked<UStaticMesh>(Object));
        else if (ASkeletalMeshActor *SkeletalActor = Cast<ASkeletalMeshActor>(Actor))
            SkeletalActor->GetSkeletalMeshComponent()->SetSkeletalMeshAsset(CastChecked<USkeletalMesh>(Object));
        else if (ANiagaraActor *EffectActor = Cast<ANiagaraActor>(Actor))
            EffectActor->GetNiagaraComponent()->SetAsset(CastChecked<UNiagaraSystem>(Object));
        Actor->SetActorLabel(Asset.AssetName.ToString());
        Actor->SetFolderPath(FName(TEXT("Owner additions")));
        Actor->MarkPackageDirty();
        GEditor->SelectNone(false, true);
        GEditor->SelectActor(Actor, true, true);
        GEditor->RedrawLevelEditingViewports();
        SetStatus(FString::Printf(TEXT("Placed %s. W / E / R adjusts placement; Save + Apply keeps it in the station."),
                                  *Asset.AssetName.ToString()));
    }

    FReply ApplyMaterial()
    {
        UWorld *World = StationWorkshop::GetEditableWorld();
        if (!World || !SelectedMaterial.IsValid())
        {
            SetStatus(TEXT("Open the Station Workshop and stop Play before applying materials."));
            return FReply::Handled();
        }
        TArray<UMeshComponent *> Meshes;
        for (FSelectionIterator It(*GEditor->GetSelectedActors()); It; ++It)
        {
            AActor *Actor = Cast<AActor>(*It);
            if (!Actor || Actor->GetWorld() != World || Actor->IsEditorOnly() ||
                Actor->ActorHasTag(TEXT("StationWorkshopGuide")))
                continue;
            TInlineComponentArray<UMeshComponent *> Components;
            Actor->GetComponents(Components);
            for (UMeshComponent *Mesh : Components)
                if (Mesh && Mesh->GetNumMaterials() > 0)
                    Meshes.Add(Mesh);
        }
        if (Meshes.IsEmpty())
        {
            SetStatus(TEXT("Select one or more mesh actors in the workshop viewport or Outliner first."));
            return FReply::Handled();
        }
        const int32 PresetIndex = MaterialOptions.IndexOfByKey(SelectedMaterial) + 1;
        const FString AssetPath = FString::Printf(
            TEXT("/Game/SpaceSurvival/Licensed/StationWorkshop/Materials/MI_Workshop_%02d.MI_Workshop_%02d"),
            PresetIndex, PresetIndex);
        UMaterialInterface *Material = TSoftObjectPtr<UMaterialInterface>(FSoftObjectPath(AssetPath)).LoadSynchronous();
        if (!Material)
        {
            SetStatus(FString::Printf(TEXT("Preset %s is missing from the project; no materials were changed."),
                                      **SelectedMaterial));
            return FReply::Handled();
        }
        const FScopedTransaction Transaction(LOCTEXT("MaterialTransaction", "Apply station material preset"));
        World->GetCurrentLevel()->Modify();
        for (UMeshComponent *Mesh : Meshes)
        {
            Mesh->GetOwner()->Modify();
            Mesh->Modify();
            for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
                Mesh->SetMaterial(Slot, Material);
            Mesh->MarkPackageDirty();
            Mesh->MarkRenderStateDirty();
        }
        World->MarkPackageDirty();
        GEditor->RedrawLevelEditingViewports();
        SetStatus(
            FString::Printf(TEXT("Applied %s to %d mesh component(s), all slots. Ctrl+Z restores original materials."),
                            **SelectedMaterial, Meshes.Num()));
        return FReply::Handled();
    }

    void CaptureWorkshop(const TArray<FString> &Args)
    {
        const TSharedPtr<SDockTab> Tab = WorkshopTab.Pin();
        if (!Tab || Args.Num() != 1 || FPaths::IsRelative(Args[0]) ||
            !FPaths::GetExtension(Args[0]).Equals(TEXT("png"), ESearchCase::IgnoreCase) ||
            IFileManager::Get().FileExists(*Args[0]))
        {
            UE_LOG(LogStationWorkshop, Warning,
                   TEXT("Capture requires an open tab and a new absolute .png path; existing files are preserved."));
            return;
        }
        TArray<FColor> Pixels;
        FIntVector Size;
        if (!FSlateApplication::Get().TakeScreenshot(Tab->GetContent(), Pixels, Size) || Size.X <= 0 || Size.Y <= 0)
        {
            UE_LOG(LogStationWorkshop, Warning, TEXT("Workshop tab screenshot was unavailable."));
            return;
        }
        TArray64<uint8> Compressed;
        FImageUtils::PNGCompressImageArray(Size.X, Size.Y, TArrayView64<const FColor>(Pixels), Compressed);
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Args[0]), true);
        const bool bSaved = FFileHelper::SaveArrayToFile(Compressed, *Args[0]);
        UE_LOG(LogStationWorkshop, Display, TEXT("Workshop capture %s: %s"), bSaved ? TEXT("saved") : TEXT("failed"),
               *Args[0]);
    }
};

IMPLEMENT_MODULE(FSpaceSurvivalEditorModule, SpaceSurvivalEditor)
#undef LOCTEXT_NAMESPACE
