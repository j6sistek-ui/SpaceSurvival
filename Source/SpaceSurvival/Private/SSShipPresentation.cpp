#include "SSShipPresentation.h"
#include "SSGameInstance.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Misc/PackageName.h"

USSShipPresentation::USSShipPresentation()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = .15f;
}

void USSShipPresentation::SetHull(UStaticMeshComponent *InHull)
{
    if (Hull == InHull && Modules.Num() == 6)
        return;
    for (auto &Module : Modules)
        if (Module)
            Module->DestroyComponent();
    Modules.Reset();
    SelectedAssets.Init(FString(), 6);
    Hull = InHull;
    if (!Hull)
        return;
    LoadModuleAssets();
    for (int32 I = 0; I < 6; ++I)
    {
        auto *Module = NewObject<UStaticMeshComponent>(GetOwner());
        Module->SetMobility(EComponentMobility::Movable);
        Module->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Module->SetGenerateOverlapEvents(false);
        Module->SetCanEverAffectNavigation(false);
        Module->SetupAttachment(Hull);
        GetOwner()->AddInstanceComponent(Module);
        Module->RegisterComponent();
        Modules.Add(Module);
    }
    Refresh();
}

void USSShipPresentation::LoadModuleAssets()
{
    if (AssetsLoaded)
        return;
    AssetsLoaded = true;
    TArray<FString> Names;
    for (const TCHAR *Track : {TEXT("Hull"), TEXT("Shield"), TEXT("HullSwift"), TEXT("ShieldSwift"), TEXT("Engine"),
                               TEXT("Thrusters"), TEXT("Laser"), TEXT("Cannon")})
        for (int32 Tier = 2; Tier <= 5; ++Tier)
            Names.Add(FString::Printf(TEXT("SM_Upgrade%s%d"), Track, Tier));
    Names.Add(TEXT("SM_UtilityVector"));
    Names.Add(TEXT("SM_UtilityCooling"));
    for (const FString &Name : Names)
    {
        const FString Path = TEXT("/Game/SpaceSurvival/Licensed/ShipVisualPass/Meshes/") + Name;
        if (FPackageName::DoesPackageExist(Path))
            ModuleAssets.Add(Name, LoadObject<UStaticMesh>(nullptr, *(Path + TEXT(".") + Name)));
    }
}

void USSShipPresentation::TickComponent(float DeltaTime, ELevelTick TickType,
                                        FActorComponentTickFunction *ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    Refresh();
}

void USSShipPresentation::Refresh()
{
    const auto *GI = GetWorld() ? GetWorld()->GetGameInstance<USSGameInstance>() : nullptr;
    if (!GI || !Hull || Modules.Num() != 6)
        return;
    const auto &Run = GI->Session.run;
    // Keep the separate closed-canopy owner trial untouched. These attachments
    // are fitted to the two original open-cockpit player hulls only.
    const UStaticMesh *Mesh = Hull->GetStaticMesh();
    const bool SupportedHull =
        Run.active && Mesh &&
        (Mesh->GetName() == TEXT("SM_AcornShipGripFit") || Mesh->GetName() == TEXT("SM_SwiftCandidateV1"));
    const TCHAR *Tracks[] = {TEXT("Hull"), TEXT("Shield"), TEXT("Engine"), TEXT("Thrusters"), TEXT("Laser")};
    for (int32 I = 0; I < 6; ++I)
    {
        FString Name;
        if (SupportedHull && I < 5)
        {
            const int32 Tier = FMath::Clamp(Run.tiers[I], 1, 5);
            if (Tier > 1)
            {
                FString Track = I == 4 && Run.weapon == SS::Weapon::HeavyCannon ? TEXT("Cannon") : Tracks[I];
                if (I < 2 && Mesh->GetName() == TEXT("SM_SwiftCandidateV1"))
                    Track += TEXT("Swift");
                Name = FString::Printf(TEXT("SM_Upgrade%s%d"), *Track, Tier);
            }
        }
        else if (SupportedHull)
        {
            if (Run.utility == SS::Utility::VectorThrusters)
                Name = TEXT("SM_UtilityVector");
            else if (Run.utility == SS::Utility::OverdriveCooling)
                Name = TEXT("SM_UtilityCooling");
        }
        if (SelectedAssets[I] != Name)
        {
            // An unlicensed source checkout keeps the existing hull. Missing
            // optional art never changes the purchased tier or module effects.
            const auto *Asset = ModuleAssets.Find(Name);
            Modules[I]->SetStaticMesh(Asset ? Asset->Get() : nullptr);
            SelectedAssets[I] = Name;
        }
        Modules[I]->SetVisibility(Hull->IsVisible() && Modules[I]->GetStaticMesh() != nullptr);
    }
}
