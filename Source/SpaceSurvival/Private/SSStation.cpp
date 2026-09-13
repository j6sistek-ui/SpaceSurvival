#include "SSStation.h"
#include "SSGameInstance.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/CapsuleComponent.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Sound/SoundBase.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"

ASSStation::ASSStation()
{
    PrimaryActorTick.bCanEverTick = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("HubRoot"));
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
void ASSStation::AddService(FVector Position, const FString &Label, ESSPanel Panel)
{
    AddMesh(Position, FVector(1), TEXT("/Game/SpaceSurvival/Meshes/SM_Console.SM_Console"),
            TEXT("/Game/SpaceSurvival/Materials/M_Hull.M_Hull"), true);
    auto *Text = NewObject<UTextRenderComponent>(this);
    Text->SetupAttachment(RootComponent);
    Text->SetRelativeLocation(Position + FVector(-55, 0, 190));
    Text->SetRelativeRotation(FRotator(0, 180, 0));
    Text->SetHorizontalAlignment(EHTA_Center);
    Text->SetWorldSize(23);
    Text->SetText(FText::FromString(Label));
    Text->SetTextRenderColor(FColor(130, 230, 245));
    Text->RegisterComponent();
    Services.Add({Position, Label, Panel});
}
void ASSStation::BuildHub(bool bHome)
{
    Home = bHome;
    const TCHAR *Cube = TEXT("/Engine/BasicShapes/Cube.Cube");
    const TCHAR *Hull = TEXT("/Game/SpaceSurvival/Materials/M_Hull.M_Hull");
    const TCHAR *Cyan = TEXT("/Game/SpaceSurvival/Materials/M_Cyan.M_Cyan");
    const TCHAR *Gold = TEXT("/Game/SpaceSurvival/Materials/M_Gold.M_Gold");
    // Dressing shares four render batches and never alters the physical deck or approach corridor.
    auto MakeBatch = [this, Cube](const TCHAR *Name, const TCHAR *Material)
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
        Batch->RegisterComponent();
        Geometry.Add(Batch);
        return Batch;
    };
    auto Stamp = [](UInstancedStaticMeshComponent *Batch, FVector Position, FVector Scale,
                    FRotator Rotation = FRotator::ZeroRotator)
    { Batch->AddInstance(FTransform(Rotation, Position, Scale)); };
    auto *Plates = MakeBatch(TEXT("DeckPanels"), Hull);
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
    AddMesh(FVector(0, 0, -60), FVector(34, 28, 1), Cube, Hull, true);
    for (int X = 0; X < 6; ++X)
    {
        const float CenterX = -1375.f + X * 550.f;
        for (int Y = 0; Y < 6; ++Y)
            Stamp(Plates, FVector(CenterX, -1125.f + Y * 450.f, -8), FVector(5.35f, 4.35f, .015f));
        for (float Side : {-1.f, 1.f})
        {
            Stamp(Plates, FVector(CenterX, Side * 1378, 205), FVector(5.2f, .12f, 2.8f));
            Stamp(Structure, FVector(CenterX, Side * 1365, 365), FVector(5.35f, .18f, .14f));
            Stamp(Plates, FVector(CenterX, Side * 1120, 960), FVector(5.35f, 4.6f, .12f));
            Stamp(Guides, FVector(CenterX, Side * 1150, 949), FVector(3.6f, .09f, .04f));
        }
    }
    for (float Side : {-1.f, 1.f})
    {
        AddMesh(FVector(0, Side * 1400, 170), FVector(34, .3f, 4.5f), Cube, Hull, true);
        Stamp(Guides, FVector(0, Side * 1340, 8), FVector(32, .12f, .08f));
        for (int I = -2; I <= 2; ++I)
            AddMesh(FVector(I * 600, Side * 1400, 500), FVector(.5f, .5f, 10), Cube, Hull, true);
    }
    // Split the inbound wall around a broad, marked docking corridor.
    AddMesh(FVector(-1700, -1050, 350), FVector(.5f, 7, 8), Cube, Hull, true);
    AddMesh(FVector(-1700, 1050, 350), FVector(.5f, 7, 8), Cube, Hull, true);
    AddMesh(FVector(1700, 0, 100), FVector(.3f, 28, 2), Cube, Hull, true);
    BayShip = AddMesh(FVector(850, 0, 220), FVector(1), TEXT("/Game/SpaceSurvival/Meshes/SM_AcornShip.SM_AcornShip"),
                      nullptr);
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
    if (!Home)
    {
        AddService(FVector(1000, 1000, 0), TEXT("ENGINEER MICA / MODULES"), ESSPanel::Vendor);
        AddService(FVector(-1400, 0, 0), TEXT("BEACON LOG / LOST CREW"), ESSPanel::Reward);
        AddMesh(FVector(1050, 1130, 120), FVector(.5f), TEXT("/Game/SpaceSurvival/Meshes/SM_Crate.SM_Crate"), Hull);
        // Mica's service avatar is a physical, moving vendor at the module bench.
        const TCHAR *Sphere = TEXT("/Engine/BasicShapes/Sphere.Sphere");

        AddMesh(FVector(1110, 1130, 135), FVector(.55f, .5f, .75f), Sphere, Gold);
        VendorHead = AddMesh(FVector(1110, 1130, 200), FVector(.56f, .56f, .45f), Sphere, Hull);
        auto *Visor = AddMesh(FVector(1084, 1130, 204), FVector(.08f, .4f, .12f), Cube, Cyan);
        Visor->AttachToComponent(VendorHead, FAttachmentTransformRules::KeepWorldTransform);
        VendorArm = AddMesh(FVector(1080, 1090, 150), FVector(.16f, .16f, .6f), Cube, Gold);
        BeaconRotor = AddMesh(FVector(-1490, 0, 165), FVector(.55f),
                              TEXT("/Game/SpaceSurvival/Meshes/SM_EventBeacon.SM_EventBeacon"), nullptr);
    }
    // Dock lights, safety strips and repeated structural ribs unify the compact hub.
    for (int I = -3; I <= 3; ++I)
    {
        for (float Side : {-1.f, 1.f})
            Stamp(Guides, FVector(float(I) * 350.f, Side * 650.f, -5), FVector(2.4f, .12f, .04f));
        Stamp(Structure, FVector(float(I) * 450.f, 0, 980), FVector(.18f, 28, .25f));
    }
    AddMesh(FVector(-450, 1120, 65), FVector(.8f), TEXT("/Game/SpaceSurvival/Meshes/SM_Crate.SM_Crate"), nullptr, true);
    AddMesh(FVector(-580, 1120, 50), FVector(.6f), TEXT("/Game/SpaceSurvival/Meshes/SM_Crate.SM_Crate"), nullptr, true);
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
    for (int I = 0; I < 4; ++I)
    {
        auto *Light = NewObject<UPointLightComponent>(this);
        Light->SetupAttachment(RootComponent);
        Light->SetRelativeLocation(FVector((I / 2) * 1800 - 900, (I % 2) * 1600 - 800, 650));
        Light->SetIntensity(120000);
        Light->SetAttenuationRadius(2200);
        Light->SetLightColor(I % 2 ? FLinearColor(.5f, .75f, 1) : FLinearColor(1, .72f, .38f));
        Light->RegisterComponent();
    }
    Ambience = NewObject<UAudioComponent>(this);
    Ambience->SetupAttachment(RootComponent);
    Ambience->SetSound(LoadObject<USoundBase>(nullptr, TEXT("/Game/SpaceSurvival/Audio/Station.Station")));
    Ambience->SetVolumeMultiplier(.25f);
    Ambience->RegisterComponent();
    Ambience->Play();
}
void ASSStation::Tick(float Dt)
{
    Super::Tick(Dt);
    if (ServiceArm)
        ServiceArm->SetRelativeRotation(FRotator(0, 0, FMath::Sin(GetWorld()->GetTimeSeconds() * .7f) * 16.f));
    if (VendorHead)
        VendorHead->SetRelativeRotation(FRotator(0, FMath::Sin(GetWorld()->GetTimeSeconds() * .48f) * 15.f, 0));
    if (VendorArm)
        VendorArm->SetRelativeRotation(FRotator(FMath::Sin(GetWorld()->GetTimeSeconds() * .9f) * 24.f, 0, -18));
    if (BeaconRotor)
        BeaconRotor->AddLocalRotation(FRotator(0, Dt * 24.f, 0));
    if (Ambience)
        if (auto *GI = GetGameInstance<USSGameInstance>())
            Ambience->SetVolumeMultiplier(
                float(GI->Session.settings.masterVolume * GI->Session.settings.effectsVolume) * .25f);
}
void ASSStation::SetBayShip(int32 ShipKind)
{
    if (BayShip)
        BayShip->SetStaticMesh(LoadObject<UStaticMesh>(
            nullptr, ShipKind == 1 ? TEXT("/Game/SpaceSurvival/Meshes/SM_AgileShip.SM_AgileShip")
                                   : TEXT("/Game/SpaceSurvival/Meshes/SM_AcornShip.SM_AcornShip")));
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
ASSWalker::ASSWalker()
{
    PrimaryActorTick.bCanEverTick = true;
    bUseControllerRotationYaw = false;
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0, 540, 0);
    GetCharacterMovement()->MaxWalkSpeed = 320;
    Boom = CreateDefaultSubobject<USpringArmComponent>(TEXT("WalkCameraBoom"));
    Boom->SetupAttachment(RootComponent);
    Boom->TargetArmLength = 350;
    Boom->SocketOffset = FVector(0, 0, 100);
    Boom->bUsePawnControlRotation = true;
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("WalkCamera"));
    Camera->SetupAttachment(Boom);
    // Measured boot sole at the authored walk handoff is -62.90269494 cm, below the ankle bone.
    // Fit it to the deck plates (2.75 cm above collision), including UE's normal walking floor gap.
    const float WalkingFloorGap =
        (UCharacterMovementComponent::MIN_FLOOR_DIST + UCharacterMovementComponent::MAX_FLOOR_DIST) * .5f;
    GetMesh()->SetRelativeLocation(FVector(
        0, 0, 62.90269494f * 1.5f - GetCapsuleComponent()->GetScaledCapsuleHalfHeight() - WalkingFloorGap + 2.75f));
    GetMesh()->SetRelativeRotation(FRotator(0, -90, 0));
    GetMesh()->SetRelativeScale3D(FVector(1.5f));
    GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}
void ASSWalker::BeginPlay()
{
    Super::BeginPlay();
    GetMesh()->SetSkeletalMesh(
        LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/SpaceSurvival/Character/SK_AcornautPilot.SK_AcornautPilot")));
    WalkAnimation = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/SpaceSurvival/Character/A_Walk.A_Walk"));
    StartWalkingAnimation();
}
void ASSWalker::StartWalkingAnimation()
{
    GetMesh()->PlayAnimation(WalkAnimation, true);
    if (auto *Animation = GetMesh()->GetSingleNodeInstance())
    {
        Animation->SetRootMotionMode(ERootMotionMode::NoRootMotionExtraction);
        // A_Disembark ends at this exact authored A_Walk pose.
        Animation->SetPosition(.308333333f, false);
    }
    GetMesh()->GlobalAnimRateScale = 0.f;
    GetMesh()->TickAnimation(0.f, false);
    GetMesh()->RefreshBoneTransforms();
    GetMesh()->SetComponentTickEnabled(true);
}
void ASSWalker::SampleExitPose(float Seconds)
{
    if (auto *Animation = GetMesh()->GetSingleNodeInstance())
        Animation->SetPosition(Seconds, false);
    GetMesh()->TickAnimation(0.f, false);
    GetMesh()->RefreshBoneTransforms();
}
bool ASSWalker::BeginDisembark(const FTransform &PilotWorldTransform, FVector End, FRotator Facing)
{
    auto *ExitAnimation =
        LoadObject<UAnimSequence>(nullptr, TEXT("/Game/SpaceSurvival/Character/A_Disembark.A_Disembark"));
    if (!ExitAnimation || !WalkAnimation || !GetMesh()->GetSkeletalMeshAsset())
        return false;
    // Component local transform * actor transform = the actual seated pilot component transform.
    // This preserves yaw, local mesh offset and the constant 1.5 mesh scale without interpolated shrinking.
    const FTransform StartTransform = GetMesh()->GetRelativeTransform().Inverse() * PilotWorldTransform;
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
    GetMesh()->PlayAnimation(ExitAnimation, false);
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
            StartWalkingAnimation();
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
            if (FMath::Abs(Local.X) > 1750.f || FMath::Abs(Local.Y) > 1450.f || Local.Z < -250.f)
            {
                GetCharacterMovement()->StopMovementImmediately();
                ConsumeMovementInputVector();
                SetActorLocation(Hub->WalkSpawn(), false, nullptr, ETeleportType::TeleportPhysics);
                SetActorRotation(Hub->GetActorRotation());
                GetCharacterMovement()->SetMovementMode(MOVE_Walking);
            }
        }
        GetMesh()->GlobalAnimRateScale = GetVelocity().Size2D() / 180.f;
    }
}
void ASSWalker::Move(FVector2D Direction, FVector2D Look, bool Run, float Dt)
{
    if (Disembarking)
        return;
    AddControllerYawInput(Look.X * 90.f * Dt);
    AddControllerPitchInput(-Look.Y * 70.f * Dt);
    const FRotator Yaw(0, GetControlRotation().Yaw, 0);
    GetCharacterMovement()->MaxWalkSpeed = Run ? 560.f : 320.f;
    AddMovementInput(Yaw.Vector(), Direction.Y);
    AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::Y), Direction.X);
}
