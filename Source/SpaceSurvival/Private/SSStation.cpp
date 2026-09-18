#include "SSStation.h"
#include "SSShipPaint.h"
#include "SSGameInstance.h"
#include "SSStationVisualLayout.h"
#include "SSShipPresentation.h"
#include "SSShip.h"
#include "SSPhase1Data.h"
#include "Misc/PackageName.h"
#include "SSStationPoseTransition.h"
#include "SSAudio.h"
#include "SSGameInstance.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SphereComponent.h"
#include "Camera/CameraComponent.h"
#include "HAL/IConsoleManager.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Sound/SoundBase.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"

#include "SSStationRefresh.inl"

ASSStation::ASSStation()
{
    PrimaryActorTick.bCanEverTick = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("HubRoot"));
    // Retain the engine font material on the CDO so its masked, unlit graph is also cooked.
    if (FPackageName::DoesPackageExist(TEXT("/Engine/EngineMaterials/UnlitText")))
    {
        static ConstructorHelpers::FObjectFinderOptional<UMaterialInterface> UnlitText(
            TEXT("/Engine/EngineMaterials/UnlitText.UnlitText"));
        ServiceLabelMaterial = UnlitText.Get();
    }
    VisualLayoutAsset = FSoftObjectPath(
        TEXT("/Game/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout.BP_StationVisualLayout_C"));
    ShellAsset =
        FSoftObjectPath(TEXT("/Game/SpaceSurvival/Meshes/SM_StationShellCandidateV1.SM_StationShellCandidateV1"));
}
UStaticMeshComponent *ASSStation::AddMesh(FVector Position, FVector Scale, const TCHAR *Mesh, const TCHAR *Material,
                                          bool Solid)
{
    auto *C = NewObject<UStaticMeshComponent>(this);
    C->SetupAttachment(RootComponent);
    C->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, Mesh));
    if (Material)
        C->SetMaterial(0, LoadObject<UMaterialInterface>(nullptr, Material));
    C->SetRelativeLocation(Position);
    C->SetRelativeScale3D(Scale);
    C->SetCollisionEnabled(Solid ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
    C->SetCollisionObjectType(ECC_WorldStatic);
    C->SetCollisionResponseToAllChannels(ECR_Block);
    C->RegisterComponent();
    Geometry.Add(C);
    return C;
}
void ASSStation::BuildLandingPad(bool bHome, const TCHAR *Cube, const TCHAR *Hull)
{
    // A slab is a scaled unit cube, so a box spanning [Low, High] on an axis is centred at their midpoint
    // and scaled by their span over 100. Every plate below shares one bottom, so the pad, the walkway and
    // the step read as one poured structure rather than three floating tiles.
    const float Bottom = -280.f;
    auto Slab = [this, Cube, Hull, Bottom](float LowX, float HighX, float HalfY, float Top, const TCHAR *Tag)
    {
        auto *Plate =
            AddMesh(FVector((LowX + HighX) * .5f, 0, (Bottom + Top) * .5f),
                    FVector((HighX - LowX) / 100.f, HalfY * 2.f / 100.f, (Top - Bottom) / 100.f), Cube, Hull, true);
        Plate->ComponentTags.Add(FName(Tag));
        return Plate;
    };
    // The pad itself. 3200 cm square against a 2484 x 1244 cm hull, so the Phoenix fits with room to spare
    // and the 482 cm starter looks like what it is - a small ship on a big pad.
    Slab(PadCenterX - PadHalfExtent, PadCenterX + PadHalfExtent, PadHalfExtent, PadDeckTop, TEXT("StationLandingPad"));
    // The walkway in to the hangar mouth. Kept inside |Y| <= 400 so it passes through the mouth's own
    // |Y| <= 700 opening without touching the jambs.
    Slab(PadCenterX + PadHalfExtent, PadWalkwayInnerX, 400.f, PadDeckTop, TEXT("StationLandingWalkway"));
    // No threshold plate is needed and one would be wrong. The interior DeckCollision spans Z -110..-10 and
    // Bow_Sill's top face is -10, so the walk from pad to deck is already one continuous plane. An earlier
    // pass here added a half-step for a 70 cm lip measured off Keel_Floor - which is the exterior hull box,
    // not the floor the hero stands on.
    // Edge markers, so the pad reads as a pad from the air rather than as a grey square. Deliberately kept
    // under the 45 cm step height: anything taller is a wall the hero would have to climb to reach its ship.
    for (float Side : {-1.f, 1.f})
    {
        auto *Kerb = AddMesh(FVector(PadCenterX, Side * (PadHalfExtent - 60.f), PadDeckTop + 12.f),
                             FVector(PadHalfExtent * 2.f / 100.f, 1.2f, .24f), Cube,
                             TEXT("/Game/SpaceSurvival/Materials/M_Cyan.M_Cyan"), false);
        Kerb->ComponentTags.Add(TEXT("StationLandingKerb"));
    }
    if (bHome)
        return;
    // A pit stop's worth of services where the ship actually is, rather than making the player walk inside
    // for the two things they came to do. The interior hub keeps all nine of its own.
    AddService(FVector(PadCenterX - 700.f, -900.f, PadDeckTop + 80.f), TEXT("DOCK REPAIR"), ESSPanel::Repair);
    AddService(FVector(PadCenterX - 700.f, 900.f, PadDeckTop + 80.f), TEXT("DOCK UPGRADES I - V"), ESSPanel::Upgrades);
}
void ASSStation::AddService(FVector Position, const FString &Label, ESSPanel Panel)
{
    auto *Stand = AddMesh(Position, FVector(1), TEXT("/Game/SpaceSurvival/Meshes/SM_Console.SM_Console"),
                          TEXT("/Game/SpaceSurvival/Materials/M_Hull.M_Hull"), true);
    Stand->SetVisibility(!VisualLayout);
    Stand->SetCastShadow(!VisualLayout);
    auto *Text = NewObject<UTextRenderComponent>(this);
    Text->SetupAttachment(RootComponent);
    Text->SetRelativeLocation(Position + FVector(-55, 0, 190));
    Text->SetRelativeRotation(FRotator(0, 180, 0));
    Text->SetHorizontalAlignment(EHTA_Center);
    Text->SetWorldSize(23);
    Text->SetText(FText::FromString(Label));
    Text->SetTextRenderColor(FColor(130, 230, 245));
    if (ServiceLabelMaterial && ServiceLabelMaterial->GetShadingModels().HasOnlyShadingModel(MSM_Unlit))
        Text->SetTextMaterial(ServiceLabelMaterial);
    Text->SetCastShadow(false);
    Text->ComponentTags.Add(TEXT("StationServiceLabel"));
    Text->RegisterComponent();
    ServiceLabels.Add(Text);
    Services.Add({Position, Label, Panel});
}
bool ASSStation::CanAssistDocking(const ASSShip *Ship) const
{
    if (!IsValid(Ship) || !Ship->Collision)
        return false;
    const FTransform HubTransform = GetActorTransform();
    const float SmallestScale = HubTransform.GetScale3D().GetAbsMin();
    if (SmallestScale <= UE_SMALL_NUMBER)
        return false;
    const float Radius = Ship->Collision->GetScaledSphereRadius() / SmallestScale;
    const FVector Local = HubTransform.InverseTransformPosition(Ship->GetActorLocation());
    // BuildHub's split wall ends at X=-1675 with a 1400 cm opening. Keep the
    // complete flight body above the deck (-10) and below the bay beams (967.5).
    // Admission is on the inbound side of the dock; roof/rear/side dives retain control.
    if (Local.X < -1675.f || Local.X >= 850.f || FMath::Abs(Local.Y) > 700.f - Radius || Local.Z < -10.f + Radius ||
        Local.Z > 967.5f - Radius ||
        FVector::DotProduct(Ship->GetActorForwardVector(), GetActorForwardVector()) <= .45f)
        return false;
    FHitResult Hit;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSDockAdmission), false, Ship);
    const FCollisionResponseParams Responses(Ship->Collision->GetCollisionResponseToChannels());
    // Check the actual flight collision body, including the physical station. Do not
    // admit a path merely because its center line misses a rib or another blocker.
    return !GetWorld()->SweepSingleByChannel(
        Hit, Ship->GetActorLocation(), DockPosition(), Ship->Collision->GetComponentQuat(),
        Ship->Collision->GetCollisionObjectType(), Ship->Collision->GetCollisionShape(), Query, Responses);
}
bool ASSStation::BuildEditableLayout()
{
    if (!bUseEditableLayout || !bUseLicensedPresentation || VisualLayoutAsset.IsNull() ||
        !FPackageName::DoesPackageExist(VisualLayoutAsset.ToSoftObjectPath().GetLongPackageName()))
        return false;
    auto *Class = VisualLayoutAsset.LoadSynchronous();
    if (!Class)
        return false;
    FActorSpawnParameters Params;
    Params.Owner = this;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    VisualLayout = GetWorld()->SpawnActor<ASSStationVisualLayout>(Class, GetActorTransform(), Params);
    if (!VisualLayout)
        return false;
    VisualLayout->AttachToComponent(RootComponent, FAttachmentTransformRules::KeepWorldTransform);
    VisualLayout->EnforcePresentationOnly();
    return true;
}

void ASSStation::DestroyVisualLayout()
{
    auto *Layout = VisualLayout.Get();
    VisualLayout = nullptr;
    if (IsValid(Layout))
        Layout->Destroy();
}

void ASSStation::Destroyed()
{
    // EndPlay is not routed for an uninitialized actor destroyed in an authoring/preview world.
    DestroyVisualLayout();
    Super::Destroyed();
}

void ASSStation::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    DestroyVisualLayout();
    Super::EndPlay(EndPlayReason);
}

void ASSStation::BuildHub(bool bHome)
{
    Home = bHome;
    const TCHAR *Cube = TEXT("/Engine/BasicShapes/Cube.Cube");
    const TCHAR *Hull = TEXT("/Game/SpaceSurvival/Materials/M_Hull.M_Hull");
    const TCHAR *Cyan = TEXT("/Game/SpaceSurvival/Materials/M_Cyan.M_Cyan");
    const TCHAR *Gold = TEXT("/Game/SpaceSurvival/Materials/M_Gold.M_Gold");
    const bool EditableLayout = BuildEditableLayout();
    const bool LicensedShell = EditableLayout || (bUseLicensedPresentation && BuildLicensedShell());
    UStaticMesh *ShellMesh = LicensedShell || ShellAsset.IsNull() ? nullptr : ShellAsset.LoadSynchronous();
    if (ShellMesh)
    {
        auto *Shell = NewObject<UStaticMeshComponent>(this, TEXT("StationShell"));
        Shell->SetupAttachment(RootComponent);
        Shell->SetStaticMesh(ShellMesh);
        Shell->SetCollisionProfileName(TEXT("NoCollision"));
        Shell->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Shell->SetGenerateOverlapEvents(false);
        Shell->SetCanEverAffectNavigation(false);
        Shell->RegisterComponent();
        Geometry.Add(Shell);
    }
    // The pit stop body: the hangar is a notch in it, authored in station-local centimetres by
    // Scripts/AuthorStationPitStop.py, so it sits at the origin with no rotation. It carries no collision of its
    // own; the solid parts are the boxes generated from the same receipt, so the visual and the collision cannot
    // disagree, and the mouth is the admission gap exactly. It is placed natively in every path, because it is
    // structure rather than dressing and is never harvested into the editable layout.
    const TCHAR *PitStopPath = TEXT("/Game/SpaceSurvival/Licensed/StationPitStop/SM_StationPitStop");
    const bool PitStop = FPackageName::DoesPackageExist(PitStopPath);
    if (PitStop)
    {
        auto *Body = AddMesh(FVector::ZeroVector, FVector(1), PitStopPath, nullptr, false);
        Body->SetCastShadow(false);
        Body->SetCanEverAffectNavigation(false);
#include "SSStationPitStopBoxes.inl"
        for (const auto &Box : SSStationPitStopBoxes)
        {
            auto *Solid = AddMesh(Box.Center, Box.Extent * (2.f / 100.f), Cube, Hull, true);
            Solid->SetVisibility(false);
            Solid->SetCastShadow(false);
            Solid->SetCanEverAffectNavigation(false);
            Solid->ComponentTags.Add(TEXT("StationPitStopSolid"));
        }
    }
    // The previous licensed exterior, kept as the fallback when the pit stop asset is absent.
    const TCHAR *ExteriorPath = TEXT("/Game/SpaceSurvival/Licensed/StationExterior/SM_StationExterior");
    if (!PitStop && FPackageName::DoesPackageExist(ExteriorPath))
    {
        if (!EditableLayout)
        {
            auto *Exterior = AddMesh(FVector(7000, 0, 3500), FVector(1), ExteriorPath, nullptr, false);
            Exterior->SetRelativeRotation(FRotator(0, 90, 0));
            Exterior->SetCastShadow(false);
            Exterior->SetCanEverAffectNavigation(false);
        }
        // The exterior is reachable during manual approach. A conservative solid
        // envelope prevents flying through it without narrowing the existing bay.
        auto *ExteriorCollision = AddMesh(FVector(7000, 0, 3500), FVector(71.42f, 100.f, 76.62f), Cube, Hull, true);
        ExteriorCollision->SetVisibility(false);
        ExteriorCollision->SetCastShadow(false);
    }
    auto AddBoundary = [this, Cube, Hull, ShellMesh, LicensedShell](FVector Position, FVector Scale)
    {
        auto *Boundary = AddMesh(Position, Scale, Cube, Hull, true);
        if (ShellMesh || LicensedShell)
        {
            Boundary->SetVisibility(false);
            Boundary->SetCastShadow(false);
        }
    };
    // Remaining dressing shares five batches; the original collision and approach corridor stay exact.
    auto MakeBatch = [this, Cube](const TCHAR *Name, const TCHAR *Material, bool ForceMips = false)
    {
        auto *Batch = NewObject<UInstancedStaticMeshComponent>(this, FName(Name));
        Batch->SetupAttachment(RootComponent);
        Batch->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, Cube));
        Batch->SetMaterial(0, LoadObject<UMaterialInterface>(nullptr, Material));
        Batch->SetCollisionProfileName(TEXT("NoCollision"));
        Batch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Batch->SetGenerateOverlapEvents(false);
        Batch->SetCanEverAffectNavigation(false);
        Batch->SetCastShadow(false);
        Batch->bForceMipStreaming = ForceMips;
        Batch->RegisterComponent();
        Geometry.Add(Batch);
        return Batch;
    };
    auto Stamp = [EditableLayout](UInstancedStaticMeshComponent *Batch, FVector Position, FVector Scale,
                                  FRotator Rotation = FRotator::ZeroRotator)
    {
        if (!EditableLayout)
            Batch->AddInstance(FTransform(Rotation, Position, Scale));
    };
    auto *Plates = MakeBatch(TEXT("DeckPanels"), Hull);
    auto *FloorPlates =
        MakeBatch(TEXT("TexturedDeckPanels"), TEXT("/Game/SpaceSurvival/Materials/M_StationDeck.M_StationDeck"), true);
    FloorPlates->SetVisibility(!LicensedShell);
    auto *Structure = MakeBatch(TEXT("ServiceStructure"), Hull);
    auto *Paint = MakeBatch(TEXT("BayPaint"), Gold);
    auto *Guides = MakeBatch(TEXT("DeckGuides"), Cyan);
    if (auto *Material = Plates->CreateDynamicMaterialInstance(0))
    {
        Material->SetVectorParameterValue(TEXT("Color"), FLinearColor(.13f, .17f, .21f));
        Material->SetScalarParameterValue(TEXT("Roughness"), .65f);
    }
    if (auto *Material = Paint->CreateDynamicMaterialInstance(0))
    {
        Material->SetVectorParameterValue(TEXT("Color"), FLinearColor(.63f, .36f, .1f));
        Material->SetScalarParameterValue(TEXT("Metallic"), .15f);
        Material->SetScalarParameterValue(TEXT("Roughness"), .75f);
    }
    auto *DeckCollision = AddMesh(FVector(0, 0, -60), FVector(34, 28, 1), Cube, Hull, true);
    DeckCollision->SetVisibility(!EditableLayout);
    DeckCollision->SetCastShadow(!EditableLayout);
    for (int X = 0; X < 6; ++X)
    {
        const float CenterX = -1375.f + X * 550.f;
        for (int Y = 0; Y < 6; ++Y)
            Stamp(FloorPlates, FVector(CenterX, -1125.f + Y * 450.f, -8), FVector(5.35f, 4.35f, .015f));
        if (!ShellMesh && !LicensedShell)
        {
            for (float Side : {-1.f, 1.f})
            {
                Stamp(Plates, FVector(CenterX, Side * 1378, 205), FVector(5.2f, .12f, 2.8f));
                Stamp(Structure, FVector(CenterX, Side * 1365, 365), FVector(5.35f, .18f, .14f));
                Stamp(Plates, FVector(CenterX, Side * 1120, 960), FVector(5.35f, 4.6f, .12f));
                Stamp(Guides, FVector(CenterX, Side * 1150, 949), FVector(3.6f, .09f, .04f));
            }
        }
    }
    for (float Side : {-1.f, 1.f})
    {
        AddBoundary(FVector(0, Side * 1400, 170), FVector(34, .3f, 4.5f));
        if (!ShellMesh && !LicensedShell)
            Stamp(Guides, FVector(0, Side * 1340, 8), FVector(32, .12f, .08f));
        for (int I = -2; I <= 2; ++I)
            AddBoundary(FVector(I * 600, Side * 1400, 500), FVector(.5f, .5f, 10));
    }
    // Split the inbound wall around a broad, marked docking corridor.
    AddBoundary(FVector(-1700, -1050, 350), FVector(.5f, 7, 8));
    AddBoundary(FVector(-1700, 1050, 350), FVector(.5f, 7, 8));
    AddBoundary(FVector(1700, 0, 100), FVector(.3f, 28, 2));
    BayShip = AddMesh(FVector(850, 0, 220), FVector(1), ASSShip::HullAssetPath(SS::Ship::Starter), nullptr);
    auto *Modules = NewObject<USSShipPresentation>(this);
    Modules->RegisterComponent();
    Modules->SetHull(BayShip);
    RefreshPaint();
    ServiceArm = AddMesh(FVector(850, 280, 150), FVector(1),
                         TEXT("/Game/SpaceSurvival/Meshes/SM_ServiceArm.SM_ServiceArm"), Hull);
    // The ship's measured underside is at deck Z153.5; its cradle stays inside its footprint.
    Stamp(Structure, FVector(850, 0, 5), FVector(4.1f, 1.9f, .3f));
    for (float X : {720.f, 970.f})
        for (float Y : {-55.f, 55.f})
            Stamp(Structure, FVector(X, Y, 75), FVector(.22f, .22f, 1.1f));
    Stamp(Structure, FVector(850, 0, 138), FVector(3.7f, 1.35f, .16f));
    for (float X : {740.f, 960.f})
        Stamp(Paint, FVector(X, 0, 149), FVector(.28f, 1.3f, .08f));
    Stamp(Structure, FVector(850, 280, 70), FVector(.82f, .82f, 1.6f));
    Stamp(Paint, FVector(850, 280, 2), FVector(1.05f, 1.05f, .24f));
    for (float Side : {-1.f, 1.f})
    {
        Stamp(Paint, FVector(850, Side * 390, -4), FVector(7.7f, .09f, .015f));
        Stamp(Paint, FVector(Side < 0 ? 460 : 1240, 0, -4), FVector(.09f, 7.9f, .015f));
        for (int I = 0; I < 4; ++I)
            Stamp(Paint, FVector(1320 + I * 48, Side * 390, -4), FVector(.2f, .9f, .015f), FRotator(0, 35, 0));
    }
    AddService(FVector(200, -1000, 0), Home ? TEXT("LOADOUT / WEAPON") : TEXT("CORE UPGRADES I - V"),
               Home ? ESSPanel::Weapon : ESSPanel::Upgrades);
    AddService(FVector(-800, -1000, 0), Home ? TEXT("SHIP BAY") : TEXT("REPAIR BAY"),
               Home ? ESSPanel::Ship : ESSPanel::Repair);
    AddService(FVector(-1100, 850, 0), Home ? TEXT("PILOT RECORD") : TEXT("CONTRACT BOARD"),
               Home ? ESSPanel::Progression : ESSPanel::Contracts);
    AddService(FVector(0, 1000, 0), Home ? TEXT("SYSTEMS") : TEXT("SUSPEND / SAVE & QUIT"),
               Home ? ESSPanel::Settings : ESSPanel::Save);
    AddService(FVector(950, -450, 0), TEXT("LAUNCH CONTROL"), ESSPanel::Launch);
    // The paint bay: a lift stand on the starboard wall; the editable layout dresses it with a platform and arch.
    AddService(FVector(-1400, -1000, 0), TEXT("PAINT BAY"), ESSPanel::Paint);
    // A separate review doorway: available in home hangar and both stations, never a run destination.
    BuildLandingPad(Home, Cube, Hull);
    AddService(FVector(450, 1000, 0), TEXT("ALIEN WORLD"), ESSPanel::AlienGallery);
    ServiceLabels.Last()->SetRelativeLocation(FVector(450, 1160, 265));
    ServiceLabels.Last()->SetWorldSize(20);
    for (float Side : {-1.f, 1.f})
        AddMesh(FVector(450 + Side * 120, 1180, 155), FVector(.16f, .30f, 3.1f), Cube, Cyan, false);
    AddMesh(FVector(450, 1180, 315), FVector(2.56f, .30f, .18f), Cube, Cyan, false);
    if (!Home)
    {
        AddService(FVector(1000, 1000, 0), TEXT("ENGINEER MICA / MODULES"), ESSPanel::Vendor);
        AddService(FVector(-1400, 0, 0), TEXT("BEACON LOG / LOST CREW"), ESSPanel::Reward);
        if (!EditableLayout)
            AddMesh(FVector(1050, 1130, 120), FVector(.5f), TEXT("/Game/SpaceSurvival/Meshes/SM_Crate.SM_Crate"), Hull);
        // Preserve the vendor interaction, using the optional idle robot when available.
        if (!EditableLayout &&
            GetComponentsByTag(USkeletalMeshComponent::StaticClass(), TEXT("StationRobotMica")).IsEmpty())
        {
            const TCHAR *Sphere = TEXT("/Engine/BasicShapes/Sphere.Sphere");
            AddMesh(FVector(1110, 1130, 135), FVector(.55f, .5f, .75f), Sphere, Gold);
            VendorHead = AddMesh(FVector(1110, 1130, 200), FVector(.56f, .56f, .45f), Sphere, Hull);
            auto *Visor = AddMesh(FVector(1084, 1130, 204), FVector(.08f, .4f, .12f), Cube, Cyan);
            Visor->AttachToComponent(VendorHead, FAttachmentTransformRules::KeepWorldTransform);
            VendorArm = AddMesh(FVector(1080, 1090, 150), FVector(.16f, .16f, .6f), Cube, Gold);
        }
        BeaconRotor = AddMesh(FVector(-1490, 0, 165), FVector(.55f),
                              TEXT("/Game/SpaceSurvival/Meshes/SM_EventBeacon.SM_EventBeacon"), nullptr);
    }
    // Optional owned characters remain presentation-only and appear whenever their private assets are installed.
    SSStationPresentation::BuildSupplementalStaff(this);
    // Dock lights, safety strips and repeated structural ribs unify the compact hub.
    for (int I = -3; I <= 3; ++I)
    {
        for (float Side : {-1.f, 1.f})
            Stamp(Guides, FVector(float(I) * 350.f, Side * 650.f, -5), FVector(2.4f, .12f, .04f));
        if (!ShellMesh && !LicensedShell)
            Stamp(Structure, FVector(float(I) * 450.f, 0, 980), FVector(.18f, 28, .25f));
    }
    auto *CrateCollision = AddMesh(FVector(-450, 1120, 65), FVector(.8f),
                                   TEXT("/Game/SpaceSurvival/Meshes/SM_Crate.SM_Crate"), nullptr, true);
    CrateCollision->SetVisibility(!EditableLayout);
    CrateCollision->SetCastShadow(!EditableLayout);
    CrateCollision = AddMesh(FVector(-580, 1120, 50), FVector(.6f),
                             TEXT("/Game/SpaceSurvival/Meshes/SM_Crate.SM_Crate"), nullptr, true);
    CrateCollision->SetVisibility(!EditableLayout);
    CrateCollision->SetCastShadow(!EditableLayout);
    // Pallets and the module bench support the existing props without moving their collision.
    Stamp(Structure, FVector(-450, 1120, 27.5f), FVector(.7f, .6f, .75f));
    Stamp(Structure, FVector(-580, 1120, 20), FVector(.52f, .48f, .6f));
    if (!Home)
    {
        Stamp(Structure, FVector(1050, 1130, 114), FVector(1.15f, .65f, .12f));
        for (float X : {1005.f, 1095.f})
            Stamp(Structure, FVector(X, 1130, 49), FVector(.12f, .5f, 1.18f));
        // One replaced panel and a hand-painted reminder give the maintenance corner a history.
        Stamp(Structure, FVector(-450, 1361, 235), FVector(4.5f, .16f, 1.55f));
        Stamp(Paint, FVector(-450, 1351, 305), FVector(4.2f, .02f, .04f));
        auto *Plaque = NewObject<UTextRenderComponent>(this);
        Plaque->SetupAttachment(RootComponent);
        Plaque->SetRelativeLocation(FVector(-450, 1349, 235));
        Plaque->SetRelativeRotation(FRotator(0, -90, 0));
        Plaque->SetHorizontalAlignment(EHTA_Center);
        Plaque->SetWorldSize(20);
        Plaque->SetText(FText::FromString(TEXT("KEEP THE BEACON LIT")));
        Plaque->SetTextRenderColor(FColor(222, 174, 95));
        Plaque->SetCastShadow(false);
        Plaque->RegisterComponent();
    }
    for (int I = 0; I < (EditableLayout ? 0 : 4); ++I)
    {
        auto *Light = NewObject<UPointLightComponent>(this);
        Light->SetupAttachment(RootComponent);
        Light->SetRelativeLocation(FVector((I / 2) * 1800 - 900, (I % 2) * 1600 - 800, 650));
        Light->SetIntensity(120000);
        Light->SetAttenuationRadius(2200);
        Light->SetLightColor(I % 2 ? FLinearColor(.5f, .75f, 1) : FLinearColor(1, .72f, .38f));
        Light->RegisterComponent();
    }
    if (Ambience)
    {
        Ambience->Stop();
        Ambience->DestroyComponent();
    }
    Ambience = NewObject<UAudioComponent>(this);
    Ambience->SetAutoActivate(false);
    Ambience->SetupAttachment(RootComponent);
    Ambience->SetSound(SSAudio::PresentationSound(TEXT("Station")));
    Ambience->SetVolumeMultiplier(SSAudio::EffectsGain(this, .25f));
    Ambience->RegisterComponent();
    Ambience->Play();
}
void ASSStation::Tick(float Dt)
{
    Super::Tick(Dt);
    if (auto *Controller = GetWorld()->GetFirstPlayerController())
    {
        FVector ViewLocation;
        FRotator ViewRotation;
        Controller->GetPlayerViewPoint(ViewLocation, ViewRotation);
        for (UTextRenderComponent *Label : ServiceLabels)
        {
            const FVector ToCamera = (ViewLocation - Label->GetComponentLocation()).GetSafeNormal2D();
            if (!ToCamera.IsNearlyZero())
                Label->SetWorldRotation(FRotator(0, ToCamera.Rotation().Yaw, 0));
        }
    }
    if (ServiceArm)
        ServiceArm->SetRelativeRotation(FRotator(0, 0, FMath::Sin(GetWorld()->GetTimeSeconds() * .7f) * 16.f));
    if (VendorHead)
        VendorHead->SetRelativeRotation(FRotator(0, FMath::Sin(GetWorld()->GetTimeSeconds() * .48f) * 15.f, 0));
    if (VendorArm)
        VendorArm->SetRelativeRotation(FRotator(FMath::Sin(GetWorld()->GetTimeSeconds() * .9f) * 24.f, 0, -18));
    if (BeaconRotor)
        BeaconRotor->AddLocalRotation(FRotator(0, Dt * 24.f, 0));
    if (Ambience)
        Ambience->SetVolumeMultiplier(SSAudio::EffectsGain(this, .25f));
}
void ASSStation::SetBayShip(int32 ShipKind)
{
    if (BayShip)
        BayShip->SetStaticMesh(LoadObject<UStaticMesh>(
            nullptr, ASSShip::HullAssetPath(ShipKind == 1 ? SS::Ship::Agile : SS::Ship::Starter)));
    RefreshPaint();
}
void ASSStation::RefreshPaint()
{
    if (const auto *GI = GetGameInstance<USSGameInstance>())
        SSPaint::Apply(BayShip, GI->Session.account);
}
void ASSStation::ShowBayShip(bool Visible)
{
    if (BayShip)
        BayShip->SetVisibility(Visible);
}
ESSPanel ASSStation::NearestService(FVector Position, FString &Label) const
{
    float Nearest = 280.f;
    ESSPanel Result = ESSPanel::None;
    for (const auto &Service : Services)
    {
        const float Distance = FVector::Dist2D(Position, GetActorTransform().TransformPosition(Service.Location));
        if (Distance < Nearest)
        {
            Nearest = Distance;
            Result = Service.Panel;
            Label = Service.Label;
        }
    }
    return Result;
}
namespace
{
// The walker's readability rig, and the owner's dials for it.
//
// Why it exists: the station's lighting is authored and liked, and it is also exactly why the hero
// disappears into it. Every lamp in the recipe hangs at Z 260 to 570 over a head at about Z 135, so the
// deck takes them at near-normal incidence and returns a specular streak as well, while the hero's
// vertical, camera-facing surfaces take the same lamps at a graze of roughly 0.2. The floor is lit; the
// hero is skimmed. Brightening the station would only widen that gap, so the answer belongs on the pawn.
//
// The strength is split in two: these dials are the look, and the hero's own ReadabilityLightScale is
// how much of it that hero's albedo needs. Turning a dial moves every hero together; the data field is
// what keeps a black suit and a pale one from wanting the same lamp.
//
// The lumens look small beside the station's own lamps and the ship's 1500 lm fill. They are, and the
// reason is distance and exposure: these sit about 2.5 m from the hero in a bay whose exposure is set
// for a deck that renders at 0.074 relative luminance. The first attempt at this asked for the same
// order of magnitude as the station's lamps, 16250 lm on the key, and rendered the squirrel's black
// suit at mean luma 230 of 255 with 70% of it clipped white. So the whole rig belongs in the low
// hundreds, and these two were then measured into place over two more captures: they land the
// squirrel's body at about three quarters of the deck's luminance, up from an eighth.
//
// These two are also the lamps' built intensities, so the class defaults and the dials cannot drift
// apart: a light that is registered but never ticked, in the editor or in some future path that skips
// BeginPlay, burns exactly what the dial says it burns.
constexpr float KeyLumens = 95.f;
constexpr float RimLumens = 160.f;
TAutoConsoleVariable<float> HeroLightKey(TEXT("ss.HeroLightKey"), KeyLumens,
                                         TEXT("Lumens in the walker's camera-side key light, before the hero's own "
                                              "scale. Models the body and lights what the camera sees."));
TAutoConsoleVariable<float> HeroLightRim(TEXT("ss.HeroLightRim"), RimLumens,
                                         TEXT("Lumens in the walker's far-side rim light, before the hero's own "
                                              "scale. This is the one that separates the silhouette."));
TAutoConsoleVariable<float> HeroLightScale(TEXT("ss.HeroLightScale"), 1.f,
                                           TEXT("Master multiplier on the walker's readability rig. 0 switches it "
                                                "off outright, for comparison against the station alone. The useful "
                                                "range ends near 1.4: at 1 the squirrel's body sits at about three "
                                                "quarters of the deck's luminance, and past 1.4 the character is "
                                                "brighter than the floor it is standing on, which reads as a torch."));
} // namespace

ASSWalker::ASSWalker()
{
    PrimaryActorTick.bCanEverTick = true;
    bUseControllerRotationYaw = false;
    GetCharacterMovement()->bOrientRotationToMovement = false;
    GetCharacterMovement()->RotationRate = FRotator(0, 540, 0);
    GetCharacterMovement()->MaxWalkSpeed = 320;
    Boom = CreateDefaultSubobject<USpringArmComponent>(TEXT("WalkCameraBoom"));
    Boom->SetupAttachment(RootComponent);
    Boom->TargetArmLength = 350;
    Boom->SocketOffset = FVector(0, 0, 100);
    Boom->bUsePawnControlRotation = true;
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("WalkCamera"));
    Camera->SetupAttachment(Boom);
    // A readability rig, not a torch. Two unshadowed point lights ride the pawn, and both are confined
    // with the hero's mesh to one lighting channel that nothing else in the world is on, so the deck,
    // the hull and the ship never take them. That confinement is what lets them be strong enough to
    // open a suit as dark as the squirrel's while the station's own lighting is left untouched.
    //
    // What the channel actually covers, because it is not everything: the deferred direct pass honours
    // it, and so does Lumen, which is what this project renders with - its surface cache carries both a
    // per-light and a per-primitive-group channel mask. Volumetric fog does not honour it at all; local
    // lights are injected on scattering intensity alone, which is why both lamps set that to zero below
    // rather than relying on the channel. With those two closed, what is left is Lumen's indirect
    // bounce off the hero itself, and that is small but not nil: on the owner's own frame the deck
    // immediately left and right of the character moved by 0.6 and 0.4 of one code value out of 255,
    // where two renders of the same build differ by 0.1 to 0.2 in the same places. So the bound on the
    // floor is measured, not structural, and winding ss.HeroLightScale far past 1 winds it up too.
    //
    // Offsets are in the rig's frame, which is yawed to the camera every tick: -X is toward the camera,
    // +X away, +Y to the camera's right, Z from the capsule centre (88 cm above the deck plates). They
    // are absolute centimetres and the same for every hero, which is deliberate: the capsule is the
    // same for every hero too, and the heroes this roster holds stand between about 135 and 180 cm, so
    // the key lands from just over the head to just under the top of it across that range. A rig scaled
    // to each hero's own height would hold the angles exactly but would have to move the lamps, and
    // moving them changes their distance and so their strength. Validated on the squirrel.
    LightRig = CreateDefaultSubobject<USceneComponent>(TEXT("HeroLightRig"));
    LightRig->SetupAttachment(RootComponent);
    KeyLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("HeroKeyLight"));
    KeyLight->SetupAttachment(LightRig);
    // 190 back toward the camera, 170 to its left, 85 up: 40 degrees off the view axis and 16 above the
    // torso. That is a portrait key rather than a lamp on the lens, so it models the body instead of
    // flattening it, and it is near enough the view for the suit to answer. The suits are roughness
    // 0.47 dielectrics, which have a broad specular lobe: a light this close to the camera axis puts a
    // sheen where the camera can see it, and specular does not care how black the base colour is.
    KeyLight->SetRelativeLocation(FVector(-190, -170, 85));
    KeyLight->SetIntensityUnits(ELightUnits::Lumens);
    // Both, and in this order. The units alone would leave the engine's 5000 on the dial and reinterpret
    // it as 5000 lumens, twenty-one times what the hero ever gets, on any path that does not reach
    // UpdateReadabilityLighting - the editor viewport among them.
    KeyLight->SetIntensity(KeyLumens);
    // Volumetric fog ignores lighting channels, so the channel alone would not keep this lamp out of the
    // bay's air. Zero scattering is what actually keeps it out.
    KeyLight->SetVolumetricScatteringIntensity(0.f);
    // Warm, near the amber the overhead pools already lay on the deck, so the hero reads as lit by this
    // bay rather than by something that followed it in.
    KeyLight->SetLightColor(FLinearColor(1.f, .86f, .7f));
    // Reaches the soles at 308 cm. The radius is a cost bound, not a look: the inverse square has taken
    // this light to nothing well inside it, so where it stops is not a place anyone can see.
    KeyLight->SetAttenuationRadius(460.f);
    KeyLight->SetCastShadows(false);
    // The owner's words: "the overhead can reflect, but he isn't a lantern". A readability lamp is a
    // courtesy to the player, and it should leave no evidence in the world. The channel keeps its direct
    // light off the deck, but indirect does not ask the channel: without these two the lamp bounces off
    // the hero into the room and is gathered again by the polished deck, so the hero reads as a light
    // source lying on a mirror. Off both paths, his reflection is still there and is lit by the bay, as
    // the overhead pools are. The cost is that the reflection is darker than the hero, which is the
    // honest consequence of lighting him for the camera and not for the room.
    KeyLight->SetAffectGlobalIllumination(false);
    KeyLight->SetAffectReflection(false);
    KeyLight->LightingChannels.bChannel0 = false;
    KeyLight->LightingChannels.bChannel1 = true;
    RimLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("HeroRimLight"));
    RimLight->SetupAttachment(LightRig);
    // The far side, 210 past the hero, 200 to the camera's right and 170 up: 136 degrees round from the
    // view axis at about 25 of elevation. At a silhouette edge the view is grazing, and Fresnel takes
    // even a near-black dielectric to almost total reflection there, so this is the lamp that costs
    // nothing in albedo. It is the one that answers the actual complaint: the measured squirrel had no
    // rim at all, and what looked like one was the deck showing through the antialiased edge.
    RimLight->SetRelativeLocation(FVector(210, 200, 170));
    RimLight->SetIntensityUnits(ELightUnits::Lumens);
    RimLight->SetIntensity(RimLumens);
    RimLight->SetVolumetricScatteringIntensity(0.f);
    // Cool, near the walkway fills' own (.8, .88, 1), so the edge belongs to the light behind the hero.
    RimLight->SetLightColor(FLinearColor(.78f, .87f, 1.f));
    RimLight->SetAttenuationRadius(540.f);
    RimLight->SetCastShadows(false);
    // Same reasoning as the key, and it matters more here: a rim lamp sits behind the hero pointing back
    // at the camera, which is the worst place to be gathered from by a floor.
    RimLight->SetAffectGlobalIllumination(false);
    RimLight->SetAffectReflection(false);
    RimLight->LightingChannels.bChannel0 = false;
    RimLight->LightingChannels.bChannel1 = true;
    // The hero keeps the station's channel and adds the rig's. This is the only primitive that does.
    GetMesh()->LightingChannels.bChannel1 = true;
    // Built with the fallback hero, because a constructor cannot ask what content is installed.
    // BeginPlay applies whichever hero this build actually has, over these same three calls.
    GetMesh()->SetRelativeLocation(FVector(0, 0, MeshLift(Hero.ScaledSoleOffset(nullptr))));
    GetMesh()->SetRelativeRotation(FRotator(0, Hero.MeshYaw, 0));
    GetMesh()->SetRelativeScale3D(FVector(Hero.RenderedScale(nullptr)));
    GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    GetMesh()->bForceMipStreaming = true;
}
double ASSWalker::MeshLift(double ScaledSoleOffset) const
{
    // Stand the hero's own measured sole on the deck plates, including UE's normal walking floor gap.
    const float WalkingFloorGap =
        (UCharacterMovementComponent::MIN_FLOOR_DIST + UCharacterMovementComponent::MAX_FLOOR_DIST) * .5f;
    return ScaledSoleOffset - GetCapsuleComponent()->GetScaledCapsuleHalfHeight() - WalkingFloorGap + DeckClearance;
}
void ASSWalker::BeginPlay()
{
    Super::BeginPlay();
    if (!Tuning)
        Tuning = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
    if (!Tuning)
        Tuning = NewObject<USSPhase1Data>(this);
    Hero = Tuning->SelectHero(ESSHeroSlot::Walker);
    USkeletalMesh *HeroMesh = LoadObject<USkeletalMesh>(nullptr, *Hero.MeshPath);
    WalkAnimation = LoadObject<UAnimSequence>(nullptr, *Hero.WalkClipPath);
    const FSSHeroDefinition Shipped = Tuning->FallbackHero();
    // A clip can only play on the skeleton it was authored against. An installed hero whose assets
    // fail to load, or whose walk belongs to another skeleton, gives the slot back to the shipped hero.
    if (Hero.Identity != Shipped.Identity &&
        (!HeroMesh || !WalkAnimation || HeroMesh->GetSkeleton() != WalkAnimation->GetSkeleton()))
    {
        Hero = Shipped;
        HeroMesh = LoadObject<USkeletalMesh>(nullptr, *Hero.MeshPath);
        WalkAnimation = LoadObject<UAnimSequence>(nullptr, *Hero.WalkClipPath);
    }
    // Only a hero who also flies the ship inherits the seated component transform and its live pose.
    SharesPilotRig = Tuning->SelectHero(ESSHeroSlot::Pilot).Identity == Hero.Identity;
    GetMesh()->SetSkeletalMesh(HeroMesh);
    GetMesh()->SetRelativeLocation(FVector(0.f, 0.f, MeshLift(Hero.ScaledSoleOffset(HeroMesh))));
    GetMesh()->SetRelativeRotation(FRotator(0, Hero.MeshYaw, 0));
    GetMesh()->SetRelativeScale3D(FVector(Hero.RenderedScale(HeroMesh)));
    // What this hero stands in, if it has anything to stand in. A clip can only play on the skeleton
    // it was authored against, exactly as above, and here a mismatch is not a reason to give the slot
    // away - it is a reason for this hero to stand the way heroes stood before any of these existed.
    IdleAnimation = nullptr;
    FidgetAnimations.Reset();
    // Rung zero is the walk, always, installed or not - every other rung is measured against it and
    // UpdateHeroAnimation reads GaitAnimations[0] where it used to read WalkAnimation.
    GaitAnimations.Reset();
    GaitSpeeds.Reset();
    GaitAnimations.Add(WalkAnimation);
    GaitSpeeds.Add(FMath::Max(1.f, Hero.WalkSpeed));
    if (const USkeleton *Skeleton = HeroMesh ? HeroMesh->GetSkeleton() : nullptr)
    {
        auto LoadClip = [Skeleton](const FString &Path) -> UAnimSequence *
        {
            // Asked about before it is loaded, because a hero declaring an idle this build does not
            // carry is the ordinary shape of a build without the licensed pack, and LoadObject would
            // put a warning in the log for every one of them.
            auto *Clip = FSSHeroDefinition::AssetInstalled(Path) ? LoadObject<UAnimSequence>(nullptr, *Path) : nullptr;
            return Clip && Clip->GetSkeleton() == Skeleton ? Clip : nullptr;
        };
        IdleAnimation = LoadClip(Hero.IdleClipPath);
        // Only alongside an idle: a fidget is a clip you cut away from and come back to, so one with
        // nowhere to come back to would be a hero left holding a pose once its fidget second passed.
        if (IdleAnimation)
            for (const FString &Path : Hero.IdleFidgetClipPaths)
                if (auto *Fidget = LoadClip(Path))
                    FidgetAnimations.Add(Fidget);
        // The ladder, built once and ascending. A hero with neither fast clip installed ends with a
        // single rung and ChooseGait can only ever return it, which is the behaviour every hero had.
        auto AddGait = [this, &LoadClip](const FString &Path, float Speed)
        {
            if (auto *Clip = LoadClip(Path))
                if (Speed > GaitSpeeds.Last())
                {
                    GaitAnimations.Add(Clip);
                    GaitSpeeds.Add(Speed);
                }
        };
        AddGait(Hero.JogClipPath, Hero.JogSpeed);
        AddGait(Hero.RunClipPath, Hero.RunSpeed);
    }
    // The rig's strength is this hero's, and BeginPlay is the first moment that is known.
    UpdateReadabilityLighting();
    // Where this hero's ankle rests when it is simply standing. Footsteps compare against it rather
    // than against a fixed height, because the heroes this roster holds stand between 135 and 180 cm
    // and an ankle that is planted on one of them is mid-stride on another.
    FTransform RestFoot;
    if (FSSHeroDefinition::ResolveBone(GetMesh(), Hero.LeftFootBone, RestFoot))
        FootRestHeight =
            FMath::Max(0.f, float(RestFoot.GetLocation().Z -
                                  (GetActorLocation().Z - GetCapsuleComponent()->GetScaledCapsuleHalfHeight())));
    StartStandingAnimation(false);
}
void ASSWalker::UpdateReadabilityLighting()
{
    if (!LightRig || !KeyLight || !RimLight)
        return;
    // Aimed at the camera, not at the world. The player orbits the boom, and a hero lit from a fixed
    // world direction is a cut-out again the moment they turn; the complaint was about one such angle.
    // Yaw only: the look clamps to 55 degrees down, and a rig that inherited pitch would swing the key
    // under the character's chin at the bottom of that.
    //
    // Read from the same place the boom reads it, not from the camera component. This runs in the
    // pawn's tick group, TG_PrePhysics, and the boom writes the camera's transform in TG_PostPhysics,
    // so the component's rotation this frame is still last frame's and the rig would trail the view
    // through a fast turn. GetViewRotation is the control rotation while possessed and the actor's
    // while not, which is the same fallback the boom takes, so the unpossessed case is unchanged.
    LightRig->SetWorldRotation(FRotator(0, GetViewRotation().Yaw, 0));
    const float Scale = FMath::Max(0.f, HeroLightScale.GetValueOnGameThread()) * Hero.ReadabilityLightScale;
    const float Key = FMath::Max(0.f, HeroLightKey.GetValueOnGameThread()) * Scale;
    const float Rim = FMath::Max(0.f, HeroLightRim.GetValueOnGameThread()) * Scale;
    // Only on a change: setting an intensity dirties the render state, and this runs every frame so the
    // owner can turn a dial mid-session and watch it move.
    if (!FMath::IsNearlyEqual(KeyLight->Intensity, Key))
        KeyLight->SetIntensity(Key);
    if (!FMath::IsNearlyEqual(RimLight->Intensity, Rim))
        RimLight->SetIntensity(Rim);
    // Zero is off rather than black: a light with no intensity still costs a pass over its own bounds.
    if (KeyLight->IsVisible() != (Key > 0.f))
        KeyLight->SetVisibility(Key > 0.f);
    if (RimLight->IsVisible() != (Rim > 0.f))
        RimLight->SetVisibility(Rim > 0.f);
}
void ASSWalker::PlayClip(UAnimSequence *Clip, float Seconds, bool Loop, float RateScale, bool CarryPose)
{
    // Starting a clip is a hard cut: PlayAnimation resets the single-node instance's clock, so this
    // is how a clip is started rather than resumed, and calling it on the clip already playing would
    // restart the stride every frame. Every caller is a transition; nothing calls this to keep going.
    //
    // CarryPose is what stops that cut being seen. Measured across all 46 bones, the jump from the
    // idle's first pose into the walk at WalkHandoffSeconds moves R_Calf 7.73 cm, which is 11.6 cm at
    // this hero's scale, and the jump the other way - out of an arbitrary walk phase back to the idle
    // - has a median worst bone of 16.8 cm and reaches 22.2, so 33.2 cm on the deck. Those are the
    // two most frequent transitions in the game, one per start and one per stop. USSStationPoseTransition
    // already exists for exactly this: it holds the outgoing pose and blends off it over BlendDuration,
    // and it was built for this same pawn and this same mesh. Reusing it costs one snapshot per cut.
    //
    // A hero with no idle never passes true, and then this function is the line it always was.
    FPoseSnapshot Outgoing;
    if (CarryPose && GetMesh()->GetSkeletalMeshAsset() && GetMesh()->GetAnimInstance())
        GetMesh()->SnapshotPose(Outgoing);
    CutSeconds = -1.f;
    if (Outgoing.bIsValid)
    {
        // Not PlayAnimation: that would switch the component back to a plain single-node instance and
        // throw away the very object holding the pose being blended from.
        GetMesh()->SetAnimInstanceClass(USSStationPoseTransition::StaticClass());
        if (auto *Transition = Cast<USSStationPoseTransition>(GetMesh()->GetAnimInstance()))
        {
            Transition->SetAnimationAsset(Clip, Loop, 1.f);
            Transition->SetRootMotionMode(ERootMotionMode::NoRootMotionExtraction);
            Transition->SetPosition(Seconds, false);
            Transition->SetPlaying(true);
            // A refused pose is not a failure worth a branch upstream. It means this cut is as hard
            // as every cut used to be, which is the thing being improved rather than depended on.
            if (Transition->SetSourcePose(Outgoing))
                CutSeconds = 0.f;
        }
    }
    else
    {
        GetMesh()->PlayAnimation(Clip, Loop);
        if (auto *Animation = GetMesh()->GetSingleNodeInstance())
        {
            Animation->SetRootMotionMode(ERootMotionMode::NoRootMotionExtraction);
            Animation->SetPosition(Seconds, false);
        }
    }
    GetMesh()->GlobalAnimRateScale = RateScale;
    GetMesh()->TickAnimation(0.f, false);
    GetMesh()->RefreshBoneTransforms();
    GetMesh()->SetComponentTickEnabled(true);
}
int32 ASSWalker::ChooseGait(float Speed) const
{
    // Boundaries are geometric means, not midpoints, because what has to stay near 1 is a RATIO: the
    // rate a gait plays at is Speed divided by that gait's own authored speed. Splitting at the
    // geometric mean makes the worst rate on either side of a boundary the same distance from 1.
    // For this hero - 180, 205.5, 384.3 against pawn speeds of 320 and 560 - it puts the boundaries
    // at 192 and 281, so cruising sits in the run at 0.83x and sprinting in the run at 1.46x, where
    // one clip for everything had the walk at 1.78x and 3.11x. The jog holds the ramp between them.
    int32 Chosen = Gait;
    // Up while the speed is clear of the boundary above, down while it is clear of the one below.
    while (Chosen + 1 < GaitSpeeds.Num() &&
           Speed > FMath::Sqrt(GaitSpeeds[Chosen] * GaitSpeeds[Chosen + 1]) * (1.f + GaitHysteresis))
        ++Chosen;
    while (Chosen > 0 && Speed < FMath::Sqrt(GaitSpeeds[Chosen - 1] * GaitSpeeds[Chosen]) / (1.f + GaitHysteresis))
        --Chosen;
    return Chosen;
}
void ASSWalker::StartStandingAnimation(bool CarryPose)
{
    Moving = false;
    StandingSeconds = 0.f;
    FidgetSecondsLeft = 0.f;
    Gait = 0;
    // A hero with an idle stands in it, at its own authored rate. A hero without one stands where
    // every hero used to: the walk clip, frozen on the single frame the disembark clip ends at, with
    // the stride stopped dead. Those two lines are the whole difference, and the second of them is
    // the old body of this function unchanged - same clip, same second, same zero, no pose carried.
    if (IdleAnimation)
        PlayClip(IdleAnimation, 0.f, true, 1.f, CarryPose);
    else
        PlayClip(WalkAnimation, Hero.WalkHandoffSeconds, true, 0.f, false);
}
void ASSWalker::UpdateHeroAnimation(float Dt)
{
    // THE GAIT MAPPING.
    //
    // One rule: play the gait whose own authored travel is nearest the pawn's speed, at a rate of
    // pawnSpeed / thatGait'sSpeed. The rate is what makes the planted foot cancel the ground exactly,
    // so every band has no skate by construction; choosing the nearest gait is what keeps that rate
    // near 1 instead of stretching one clip over the whole range. With a single gait installed the
    // rule collapses to what the game always did - the walk at Speed/WalkSpeed - and that is the case
    // the two heroes without fast clips take.
    //
    // For the squirrel the ladder is the walk at 180, the jog at 205.5 and the run at 384.3, against
    // a pawn that walks at 320 and runs at 560 (Move). Its cruising speed lands in the run at 0.83x
    // and its sprint in the run at 1.46x, where one clip for everything ran the walk at 1.78x and
    // 3.11x. That is not a quirk of the clips: 320 cm/s on a hero 134.7 cm tall is 2.4 body heights a
    // second, which on a person is a run, so the pawn's "walk" was never a walk.
    //
    // What this cannot do is blend two gaits, because a single-node pawn plays one clip - so each
    // band change is a cut, taken through the same pose carry as every other cut here, and the
    // hysteresis in ChooseGait is what stops a pawn sitting on a boundary cutting every frame.
    const float Speed = GetVelocity().Size2D();
    if (!IdleAnimation)
    {
        // Unchanged, and deliberately still one line: for a hero with no idle this is the whole of
        // its animation, standing and walking alike, exactly as it was before any of this existed.
        GetMesh()->GlobalAnimRateScale = Speed / FMath::Max(1.f, Hero.WalkSpeed);
        return;
    }
    // One sane step, used by everything below it. A frame that reports no time, or reports a NaN,
    // must not be able to run a blend out, bring a fidget forward, or push one away for ever.
    const float Step = FMath::IsFinite(Dt) && Dt > 0.f ? Dt : 0.f;
    if (CutSeconds >= 0.f)
    {
        CutSeconds += Step;
        // The same call the disembark uses, and the same curve: seconds in, smoothstepped alpha out.
        // It clears its own held pose when it arrives, so this only has to stop asking.
        if (auto *Transition = Cast<USSStationPoseTransition>(GetMesh()->GetAnimInstance()))
            Transition->SetExitTime(CutSeconds);
        if (CutSeconds >= USSStationPoseTransition::BlendDuration)
            CutSeconds = -1.f;
    }
    // Held input, not just measured speed. GetVelocity on a walking pawn is what it managed to move,
    // so a hero pressed into a bulkhead reports nearly zero and would drop into the idle - and then,
    // after IdleFidgetSeconds of the player still holding forward, stand there and fidget at the wall.
    // The deck is a bounded room, so that is not a corner case. Requiring the intent to be gone too
    // leaves a pressed hero where it always was - a blocked pawn reports no speed, so the ladder
    // below picks its slowest rung and plays the walk at rate ~0, which is exactly what pressing into
    // a bulkhead looked like before any of this. Releasing the stick still reaches the idle the same
    // frame, so the guard buys that case without costing a frame anywhere else.
    //
    // Both halves are asked because they are true at different moments: the pending input vector is
    // this frame's, set before this tick and consumed after it, and the acceleration is what the
    // movement component made of the last one.
    const auto *Movement = GetCharacterMovement();
    const bool Pushing = !GetPendingMovementInputVector().IsNearlyZero() ||
                         (Movement && !Movement->GetCurrentAcceleration().IsNearlyZero());
    if (Moving ? Speed < Hero.WalkSpeed * MoveExitFraction && !Pushing : Speed > Hero.WalkSpeed * MoveEnterFraction)
    {
        Moving = !Moving;
        // Into the gait at the walk's handoff second rather than at its start, because that second is
        // a planted contact - heel strike is at 0.158 and toe-off at 0.467 - while the clip's own
        // frame zero is mid-swing. Leaving a stand on a foot already on the ground is a step; leaving
        // it on a foot in the air is a stumble. It is also the one pose this hero has always stood
        // in, so the cut out of the idle lands exactly where the game used to start every walk from.
        if (Moving)
        {
            Gait = ChooseGait(Speed);
            PlayClip(GaitAnimations[Gait], Hero.WalkHandoffSeconds, true, Speed / GaitSpeeds[Gait], true);
        }
        else
            StartStandingAnimation();
    }
    if (Moving)
    {
        const int32 Wanted = ChooseGait(Speed);
        if (Wanted != Gait)
        {
            Gait = Wanted;
            // Frame zero, not the walk's handoff second: that second is a contact pose of the WALK,
            // and the other two clips are different lengths with their contacts elsewhere. The pose
            // carry is what covers the seam, so the entry phase no longer has to.
            PlayClip(GaitAnimations[Gait], 0.f, true, Speed / GaitSpeeds[Gait], true);
        }
        GetMesh()->GlobalAnimRateScale = Speed / GaitSpeeds[Gait];
        return;
    }
    if (FidgetSecondsLeft > 0.f)
    {
        FidgetSecondsLeft -= Step;
        // A fidget's last pose is its first pose is the idle's first pose, all three within 0.01 cm
        // and 0.05 degrees, so being a frame early or late on the way back cannot show.
        if (FidgetSecondsLeft <= 0.f)
        {
            FidgetSecondsLeft = 0.f;
            StandingSeconds = 0.f;
            PlayClip(IdleAnimation, 0.f, true, 1.f, true);
        }
    }
    else
    {
        StandingSeconds += Step;
        if (Hero.IdleFidgetSeconds > 0.f && FidgetAnimations.Num() > 0 && StandingSeconds >= Hero.IdleFidgetSeconds)
        {
            // In turn rather than at random: two fidgets alternating is what a person standing about
            // looks like, and a random pick can repeat itself twice running, which does not.
            UAnimSequence *Fidget = FidgetAnimations[NextFidget % FidgetAnimations.Num()];
            NextFidget = (NextFidget + 1) % FidgetAnimations.Num();
            FidgetSecondsLeft = Fidget->GetPlayLength();
            StandingSeconds = 0.f;
            PlayClip(Fidget, 0.f, false, 1.f, true);
        }
    }
    // An idle keeps its own clock. The pawn is not moving, so there is no ground speed for it to
    // follow, and the zero this used to be is what made standing a still frame in the first place.
    GetMesh()->GlobalAnimRateScale = 1.f;
}
void ASSWalker::SampleExitPose(float Seconds)
{
    if (auto *Transition = Cast<USSStationPoseTransition>(GetMesh()->GetAnimInstance()))
        Transition->SetExitTime(Seconds);
    if (auto *Animation = GetMesh()->GetSingleNodeInstance())
        Animation->SetPosition(Seconds, false);
    GetMesh()->TickAnimation(0.f, false);
    GetMesh()->RefreshBoneTransforms();
}
bool ASSWalker::BeginDisembark(const FTransform &PilotWorldTransform, FVector End, FRotator Facing,
                               const FPoseSnapshot *SourcePose)
{
    auto *ExitAnimation =
        Hero.DisembarkClipPath.IsEmpty() ? nullptr : LoadObject<UAnimSequence>(nullptr, *Hero.DisembarkClipPath);
    if (!ExitAnimation || !WalkAnimation || !GetMesh()->GetSkeletalMeshAsset())
        return false;
    // Component local transform * actor transform = the actual seated pilot component transform.
    // This preserves yaw, local mesh offset and the hero's own mesh scale without interpolated shrinking.
    // A hero who never flies the ship has no seat of its own and starts from the ship position instead.
    const FTransform StartTransform = SharesPilotRig
                                          ? GetMesh()->GetRelativeTransform().Inverse() * PilotWorldTransform
                                          : FTransform(Facing, PilotWorldTransform.GetLocation(), FVector::OneVector);
    ExitStart = StartTransform.GetLocation();
    ExitStartRotation = StartTransform.GetRotation();
    ExitEndRotation = Facing.Quaternion();
    ExitEnd = End;
    FHitResult Floor;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSDisembarkFloor), false, this);
    if (GetWorld()->LineTraceSingleByObjectType(Floor, End + FVector(0, 0, 300), End - FVector(0, 0, 600),
                                                FCollisionObjectQueryParams(ECC_WorldStatic), Query) &&
        Floor.ImpactNormal.Z > .5f)
    {
        // Begin the planted stage at the height MOVE_Walking will retain, avoiding a completion snap.
        const float WalkingFloorGap =
            (UCharacterMovementComponent::MIN_FLOOR_DIST + UCharacterMovementComponent::MAX_FLOOR_DIST) * .5f;
        ExitEnd.Z = Floor.ImpactPoint.Z + GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + WalkingFloorGap;
    }
    ExitElapsed = 0.0;
    Disembarking = true;
    GetCharacterMovement()->StopMovementImmediately();
    GetCharacterMovement()->DisableMovement();
    ConsumeMovementInputVector();
    GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SetActorTransform(StartTransform, false, nullptr, ETeleportType::TeleportPhysics);
    // Losing the seated pose is not fatal: the exit still plays, from the clip's own first pose rather
    // than from the pose the pilot was actually holding. It is a visible seam either way, so one place
    // decides it and one line says it out loud. The reasons the transition works out are only half of
    // them; the half that fires on every transition today is that the hero walking the deck was never
    // the hero in the seat, and that used to be the one case that passed in silence.
    ESSPoseRefusal Refusal = ESSPoseRefusal::Accepted;
    if (!SharesPilotRig)
        Refusal = ESSPoseRefusal::NotSharedRig;
    else if (!SourcePose || !SourcePose->bIsValid)
        Refusal = ESSPoseRefusal::NoSnapshot;
    else
    {
        GetMesh()->SetAnimInstanceClass(USSStationPoseTransition::StaticClass());
        if (auto *Transition = Cast<USSStationPoseTransition>(GetMesh()->GetAnimInstance()))
        {
            Transition->SetAnimationAsset(ExitAnimation, false, 1.f);
            Transition->SetSourcePose(*SourcePose, &Refusal);
        }
        else
            Refusal = ESSPoseRefusal::NoTransitionInstance;
    }
    if (Refusal != ESSPoseRefusal::Accepted)
    {
        // A pose the transition itself refused leaves that instance already holding the exit clip.
        // The reasons decided above never reached it, so those still have to start the clip.
        if (Refusal == ESSPoseRefusal::NotSharedRig || Refusal == ESSPoseRefusal::NoSnapshot ||
            Refusal == ESSPoseRefusal::NoTransitionInstance)
            GetMesh()->PlayAnimation(ExitAnimation, false);
        const FString PilotId = Tuning ? Tuning->SelectHero(ESSHeroSlot::Pilot).Id.ToString() : FString(TEXT("none"));
        const FString SnapshotMesh = SourcePose ? SourcePose->SkeletalMeshName.ToString() : FString(TEXT("none"));
        const FString Line = FString::Printf(
            TEXT("SSDisembark: the walking hero '%s' could not carry a seated pose into its exit because %s. "
                 "The exit starts from the clip instead. pilotHero=%s walkerMesh=%s walkerBones=%d "
                 "snapshotMesh=%s snapshotBones=%d"),
            *Hero.Id.ToString(), USSStationPoseTransition::RefusalReason(Refusal), *PilotId,
            *GetNameSafe(GetMesh()->GetSkeletalMeshAsset()),
            GetMesh()->GetSkeletalMeshAsset()->GetRefSkeleton().GetNum(), *SnapshotMesh,
            SourcePose ? SourcePose->LocalTransforms.Num() : 0);
        // Two of these are the expected shape of a call, not a fault. A stand-in that only walks the deck
        // has no seat of its own, and the exit is deliberately started without a pose where there never
        // was one. Those explain the seam at Log, which keeps it in the log file without training anyone
        // to ignore warnings on a build that is behaving exactly as designed. A pose that was handed over
        // and still could not be carried is a rig that should have matched and did not: that is a warning.
        if (Refusal == ESSPoseRefusal::NotSharedRig || Refusal == ESSPoseRefusal::NoSnapshot)
        {
            UE_LOG(LogTemp, Log, TEXT("%s"), *Line);
        }
        else
        {
            UE_LOG(LogTemp, Warning, TEXT("%s"), *Line);
        }
    }
    if (auto *Animation = GetMesh()->GetSingleNodeInstance())
    {
        Animation->SetRootMotionMode(ERootMotionMode::NoRootMotionExtraction);
        Animation->SetPlaying(false);
    }
    // Only this actor clock advances the clip; component ticks cannot advance it a second time.
    GetMesh()->SetComponentTickEnabled(false);
    GetMesh()->GlobalAnimRateScale = 0.f;
    SampleExitPose(0.f);
    return true;
}
void ASSWalker::ApplyWorldOffset(const FVector &InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    ExitStart += InOffset;
    ExitEnd += InOffset;
}
void ASSWalker::Tick(float Dt)
{
    Super::Tick(Dt);
    // Before the early returns below: the exit is the other shot the owner looks at, and a dial that
    // only took effect while standing still would be a dial that lies.
    UpdateReadabilityLighting();
    if (Disembarking)
    {
        if (!FMath::IsFinite(Dt) || Dt <= 0.f)
            return;
        ExitElapsed = FMath::Min(ExitElapsed + double(Dt), double(DisembarkDuration));
        // Brace/rise happens in the authored pose. Travel starts after the rise and ends at deck contact.
        const float Travel = FMath::Clamp(float((ExitElapsed - .82) / (1.6 - .82)), 0.f, 1.f);
        const float Ease = Travel * Travel * (3.f - 2.f * Travel);
        const FVector Position = FMath::Lerp(ExitStart, ExitEnd, Ease) +
                                 FVector(0, 0, Travel > 0.f && Travel < 1.f ? FMath::Sin(Travel * PI) * 125.f : 0.f);
        SetActorLocationAndRotation(Position, FQuat::Slerp(ExitStartRotation, ExitEndRotation, Ease), false, nullptr,
                                    ETeleportType::TeleportPhysics);
        SampleExitPose(float(ExitElapsed));
        // From 1.6 through 2.4 the actor is fixed, preserving the clip's planted ankles.
        if (ExitElapsed >= double(DisembarkDuration))
        {
            Disembarking = false;
            GetCharacterMovement()->StopMovementImmediately();
            ConsumeMovementInputVector();
            GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
            GetCharacterMovement()->SetMovementMode(MOVE_Walking);
            // The exit clip is authored to end on the walk's handoff pose, so for the two heroes that
            // climb out this hands back to the exact frame it always did - they have no idle, so the
            // pose carry is not reached and this is the same call it always was. A hero with both an
            // exit clip and an idle would land on a pose the idle does not start from; none is that
            // shape today, and when one is, the carry below covers it.
            StartStandingAnimation();
        }
    }
    else
    {
        if (!RecoveryHub.IsValid())
        {
            float Nearest = MAX_flt;
            for (TActorIterator<ASSStation> It(GetWorld()); It; ++It)
            {
                const float Distance = FVector::DistSquared(GetActorLocation(), It->GetActorLocation());
                if (Distance < Nearest)
                {
                    Nearest = Distance;
                    RecoveryHub = *It;
                }
            }
        }
        if (const ASSStation *Hub = RecoveryHub.Get())
        {
            const FVector Local = Hub->GetActorTransform().InverseTransformPosition(GetActorLocation());
            // The ship's inbound corridor stays open. A walker who leaves the
            // finite deck is returned to its safe spawn without ending the run.
            // The deck is no longer only the interior: it now includes the exterior landing pad and the
            // walkway between them, which is what makes "land outside and walk in" possible at all. Before
            // this the envelope stopped at X -1750 and the hangar mouth is at -1800, so the hero was fenced
            // in fifty centimetres short of its own doorway.
            if (!ASSStation::WalkableLocal(Local))
            {
                // Counted, because this restores the very state an arrival is asked to prove and would
                // otherwise let a broken arrival pose as a good one that simply started off the deck.
                ++OffDeckRescues;
                GetCharacterMovement()->StopMovementImmediately();
                ConsumeMovementInputVector();
                SetActorLocation(Hub->WalkSpawn(), false, nullptr, ETeleportType::TeleportPhysics);
                SetActorRotation(Hub->GetActorRotation());
                GetCharacterMovement()->SetMovementMode(MOVE_Walking);
            }
        }
        // Which clip this hero should be in, and how fast it should run.
        UpdateHeroAnimation(Dt);
        UpdateFootsteps(Dt);
    }
}
void ASSWalker::UpdateFootsteps(float Dt)
{
    // Fired from the feet themselves, not from notifies hung on the clips. This hero's gaits come
    // from two different places - the walk authored for this game, the rest retargeted from mocap -
    // and re-importing any of them would drop a notify, silently. A boot coming down is the same
    // event in every clip, and it is the event the sound belongs to.
    StepCooldown = FMath::Max(0.f, StepCooldown - Dt);
    auto *Movement = GetCharacterMovement();
    const bool OnFoot = Moving && !Disembarking && Movement && Movement->IsMovingOnGround();
    const FName Feet[2] = {Hero.LeftFootBone, Hero.RightFootBone};
    const float Deck = GetActorLocation().Z - GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
    for (int32 Side = 0; Side < 2; ++Side)
    {
        FTransform Foot;
        if (!OnFoot || FootRestHeight <= 0.f || !FSSHeroDefinition::ResolveBone(GetMesh(), Feet[Side], Foot))
        {
            // Standing, mid-exit, or a hero whose feet this build cannot name: nothing is planted,
            // so the next real step still sounds instead of being swallowed as "already down".
            FootPlanted[Side] = false;
            continue;
        }
        const bool Planted = Foot.GetLocation().Z - Deck <= FootRestHeight * 1.35f;
        if (Planted && !FootPlanted[Side] && StepCooldown <= 0.f)
        {
            if (auto *Audio = GetWorld()->GetSubsystem<USSWorldAudioSubsystem>())
                if (auto *Voice = Audio->PlayOneShot(FSSAudioCueDefinition(), TEXT("Footstep"), Foot.GetLocation()))
                {
                    // No two boots land alike, and a hero moving faster lands harder.
                    Voice->SetPitchMultiplier(FMath::FRandRange(.92f, 1.09f));
                    Voice->SetVolumeMultiplier(SSAudio::EffectsGain(
                        this, FMath::GetMappedRangeValueClamped(FVector2D(60.f, 480.f), FVector2D(.45f, 1.f),
                                                                float(GetVelocity().Size2D()))));
                }
            // A walk lands about twice a second and a sprint about four times; this bar is under
            // both, so it never silences a real step - it only stops a clip that jitters at the
            // contact threshold from turning two frames into a burst.
            StepCooldown = .12f;
        }
        FootPlanted[Side] = Planted;
    }
}
void ASSWalker::Move(FVector2D Direction, FVector2D Look, bool Run, float Dt)
{
    if (Disembarking)
        return;
    if (!Controller || !FMath::IsFinite(Dt) || Dt <= 0.f || Look.ContainsNaN())
        return;
    // Input is polled after Super::PlayerTick has already consumed RotationInput.
    // Apply this frame's station view directly before TickActor clears that buffer.
    FRotator View = Controller->GetControlRotation();
    View.Yaw = FRotator::NormalizeAxis(View.Yaw + Look.X * 90.f * Dt);
    View.Pitch = FMath::Clamp(FRotator::NormalizeAxis(View.Pitch) - Look.Y * 70.f * Dt, -55.f, 35.f);
    View.Roll = 0.f;
    Controller->SetControlRotation(View);
    const FRotator Yaw(0, View.Yaw, 0);
    // Forward, back and strafe share this facing: the chase view stays behind the body.
    SetActorRotation(Yaw);
    GetCharacterMovement()->MaxWalkSpeed = Run ? 560.f : 320.f;
    AddMovementInput(Yaw.Vector(), Direction.Y);
    AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::Y), Direction.X);
}
