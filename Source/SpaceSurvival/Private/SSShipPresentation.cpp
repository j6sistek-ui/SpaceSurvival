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
    {
        Refresh();
        return;
    }
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
    for (const TCHAR *Track :
         {TEXT("Hull"), TEXT("Shield"), TEXT("Engine"), TEXT("Thrusters"), TEXT("Laser"), TEXT("Cannon")})
        for (int32 Tier = 2; Tier <= 5; ++Tier)
            Names.Add(FString::Printf(TEXT("SM_UpgradeHavolk%s%d"), Track, Tier));
    Names.Add(TEXT("SM_UtilityHavolkVector"));
    Names.Add(TEXT("SM_UtilityHavolkCooling"));
    for (const FString &Name : Names)
    {
        const FString Path =
            FString(Name.Contains(TEXT("Havolk")) ? TEXT("/Game/SpaceSurvival/Licensed/PlayerShipVisualPass/Meshes/")
                                                  : TEXT("/Game/SpaceSurvival/Licensed/ShipVisualPass/Meshes/")) +
            Name;
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

bool USSShipPresentation::TryGetExhaustLocalPosition(int32 SideIndex, FVector &Position) const
{
    if (!Hull || !Hull->GetStaticMesh() || Hull->GetStaticMesh()->GetName() != TEXT("SM_PlayerHavolkStarter"))
        return false;
    // Native-import-verified nacelle axes. Clear the actual displayed rear
    // casing, including larger purchased tiers; the two trail count is fixed.
    float Rear = Hull->GetStaticMesh()->GetBoundingBox().Min.X - 5.f;
    if (Modules.IsValidIndex(2) && Modules[2] && Modules[2]->IsVisible() && Modules[2]->GetStaticMesh())
        Rear = Modules[2]->GetStaticMesh()->GetBoundingBox().Min.X - 5.f;
    Position = FVector(Rear, SideIndex == 0 ? -102.f : 102.f, 10.f);
    return true;
}

bool USSShipPresentation::TryGetMuzzleWorldPosition(FVector &Position) const
{
    if (!Hull || !Hull->GetStaticMesh() || Hull->GetStaticMesh()->GetName() != TEXT("SM_PlayerHavolkStarter") ||
        !Modules.IsValidIndex(4) || !Modules[4] || !Modules[4]->IsVisible() || !Modules[4]->GetStaticMesh())
        return false;
    // Flash at the visible barrel. Authoritative traces/projectiles retain
    // their existing origin and aim calculation in ASSShip::Fire.
    const float Tip = Modules[4]->GetStaticMesh()->GetBoundingBox().Max.X + 2.f;
    Position = Modules[4]->GetComponentTransform().TransformPosition(FVector(Tip, 0.f, -25.f));
    return true;
}

void USSShipPresentation::Refresh()
{
    const auto *GI = GetWorld() ? GetWorld()->GetGameInstance<USSGameInstance>() : nullptr;
    if (!GI || !Hull || Modules.Num() != 6)
        return;
    const auto &Run = GI->Session.run;
    // The separate owner trial stays independent. Each supported hull uses
    // its own measured fittings, with no gameplay or equipment changes.
    const UStaticMesh *Mesh = Hull->GetStaticMesh();
    const bool Havolk = Mesh && Mesh->GetName() == TEXT("SM_PlayerHavolkStarter");
    const bool SupportedHull =
        Run.active && Mesh &&
        (Havolk || Mesh->GetName() == TEXT("SM_AcornShipGripFit") || Mesh->GetName() == TEXT("SM_SwiftCandidateV1"));
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
                if (Havolk)
                    Track = TEXT("Havolk") + Track;
                if (I < 2 && Mesh->GetName() == TEXT("SM_SwiftCandidateV1"))
                    Track += TEXT("Swift");
                Name = FString::Printf(TEXT("SM_Upgrade%s%d"), *Track, Tier);
            }
        }
        else if (SupportedHull)
        {
            if (Run.utility == SS::Utility::VectorThrusters)
                Name = Havolk ? TEXT("SM_UtilityHavolkVector") : TEXT("SM_UtilityVector");
            else if (Run.utility == SS::Utility::OverdriveCooling)
                Name = Havolk ? TEXT("SM_UtilityHavolkCooling") : TEXT("SM_UtilityCooling");
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
