#include "SSStation.h"
#include "SSGameInstance.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Animation/AnimSequence.h"
#include "Sound/SoundBase.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Materials/MaterialInterface.h"

ASSStation::ASSStation()
{
    PrimaryActorTick.bCanEverTick=true;
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("HubRoot"));
}
UStaticMeshComponent* ASSStation::AddMesh(FVector Position,FVector Scale,const TCHAR* Mesh,const TCHAR* Material,bool Solid)
{
    auto* C=NewObject<UStaticMeshComponent>(this); C->SetupAttachment(RootComponent);
    C->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,Mesh)); C->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,Material));
    C->SetRelativeLocation(Position); C->SetRelativeScale3D(Scale);
    C->SetCollisionEnabled(Solid?ECollisionEnabled::QueryAndPhysics:ECollisionEnabled::NoCollision);
    C->SetCollisionObjectType(ECC_WorldStatic); C->SetCollisionResponseToAllChannels(ECR_Block);
    C->RegisterComponent(); Geometry.Add(C); return C;
}
void ASSStation::AddService(FVector Position,const FString& Label,ESSPanel Panel)
{
    AddMesh(Position,FVector(1),TEXT("/Game/SpaceSurvival/Meshes/SM_Console.SM_Console"),TEXT("/Game/SpaceSurvival/Materials/M_Hull.M_Hull"),true);
    auto* Text=NewObject<UTextRenderComponent>(this); Text->SetupAttachment(RootComponent);
    Text->SetRelativeLocation(Position+FVector(-55,0,190)); Text->SetRelativeRotation(FRotator(0,180,0));
    Text->SetHorizontalAlignment(EHTA_Center); Text->SetWorldSize(23); Text->SetText(FText::FromString(Label));
    Text->SetTextRenderColor(FColor(130,230,245)); Text->RegisterComponent();
    Services.Add({Position,Label,Panel});
}
void ASSStation::BuildHub(bool bHome)
{
    Home=bHome;
    const TCHAR* Cube=TEXT("/Engine/BasicShapes/Cube.Cube");
    const TCHAR* Hull=TEXT("/Game/SpaceSurvival/Materials/M_Hull.M_Hull");
    const TCHAR* Cyan=TEXT("/Game/SpaceSurvival/Materials/M_Cyan.M_Cyan");
    AddMesh(FVector(0,0,-60),FVector(34,28,1),Cube,Hull,true);
    for (float Side : {-1.f,1.f})
    {
        AddMesh(FVector(0,Side*1400,170),FVector(34,.3f,4.5f),Cube,Hull,true);
        AddMesh(FVector(0,Side*1340,8),FVector(32,.12f,.08f),Cube,Cyan);
        for (int I=-2;I<=2;++I) AddMesh(FVector(I*600,Side*1400,500),FVector(.5f,.5f,10),Cube,Hull,true);
    }
    // Split the inbound wall around a broad, marked docking corridor.
    AddMesh(FVector(-1700,-1050,350),FVector(.5f,7,8),Cube,Hull,true);
    AddMesh(FVector(-1700,1050,350),FVector(.5f,7,8),Cube,Hull,true);
    AddMesh(FVector(1700,0,100),FVector(.3f,28,2),Cube,Hull,true);
    AddMesh(FVector(850,0,180),FVector(1),TEXT("/Game/SpaceSurvival/Meshes/SM_AcornShip.SM_AcornShip"),Hull);
    ServiceArm=AddMesh(FVector(850,280,150),FVector(1),TEXT("/Game/SpaceSurvival/Meshes/SM_ServiceArm.SM_ServiceArm"),Hull);
    AddService(FVector(200,-1000,0),Home?TEXT("LOADOUT / WEAPON"):TEXT("CORE UPGRADES I - V"),Home?ESSPanel::Weapon:ESSPanel::Upgrades);
    AddService(FVector(-800,-1000,0),Home?TEXT("SHIP BAY"):TEXT("REPAIR BAY"),Home?ESSPanel::Ship:ESSPanel::Repair);
    AddService(FVector(-1100,850,0),Home?TEXT("PILOT RECORD"):TEXT("CONTRACT BOARD"),Home?ESSPanel::Progression:ESSPanel::Contracts);
    AddService(FVector(0,1000,0),Home?TEXT("SYSTEMS"):TEXT("SUSPEND / SAVE & QUIT"),Home?ESSPanel::Settings:ESSPanel::Save);
    AddService(FVector(950,-450,0),TEXT("LAUNCH CONTROL"),ESSPanel::Launch);
    if (!Home)
    {
        AddService(FVector(1000,1000,0),TEXT("ENGINEER MICA / MODULES"),ESSPanel::Vendor);
        AddService(FVector(-1400,0,0),TEXT("BEACON LOG / LOST CREW"),ESSPanel::Reward);
        AddMesh(FVector(1050,1130,120),FVector(.5f),TEXT("/Game/SpaceSurvival/Meshes/SM_Crate.SM_Crate"),Hull);
    }
    for (int I=0;I<4;++I)
    {
        auto* Light=NewObject<UPointLightComponent>(this); Light->SetupAttachment(RootComponent);
        Light->SetRelativeLocation(FVector((I/2)*1800-900,(I%2)*1600-800,650));
        Light->SetIntensity(120000); Light->SetAttenuationRadius(2200); Light->SetLightColor(I%2?FLinearColor(.5f,.75f,1):FLinearColor(1,.72f,.38f));
        Light->RegisterComponent();
    }
    Ambience=NewObject<UAudioComponent>(this); Ambience->SetupAttachment(RootComponent);
    Ambience->SetSound(LoadObject<USoundBase>(nullptr,TEXT("/Game/SpaceSurvival/Audio/Station.Station"))); Ambience->SetVolumeMultiplier(.25f);
    Ambience->RegisterComponent(); Ambience->Play();
}
void ASSStation::Tick(float Dt)
{
    Super::Tick(Dt);
    if (ServiceArm) ServiceArm->SetRelativeRotation(FRotator(0,0,FMath::Sin(GetWorld()->GetTimeSeconds()*.7f)*16.f));
    if(Ambience) if(auto* GI=GetGameInstance<USSGameInstance>()) Ambience->SetVolumeMultiplier(float(GI->Session.settings.masterVolume*GI->Session.settings.effectsVolume)*.25f);
}
ESSPanel ASSStation::NearestService(FVector Position,FString& Label) const
{
    float Nearest=280.f; ESSPanel Result=ESSPanel::None;
    for (const auto& Service:Services)
    {
        const float Distance=FVector::Dist2D(Position,GetActorTransform().TransformPosition(Service.Location));
        if (Distance<Nearest) { Nearest=Distance; Result=Service.Panel; Label=Service.Label; }
    }
    return Result;
}
ASSWalker::ASSWalker()
{
    PrimaryActorTick.bCanEverTick=true;
    bUseControllerRotationYaw=false;
    GetCharacterMovement()->bOrientRotationToMovement=true;
    GetCharacterMovement()->RotationRate=FRotator(0,540,0); GetCharacterMovement()->MaxWalkSpeed=320;
    Boom=CreateDefaultSubobject<USpringArmComponent>(TEXT("WalkCameraBoom")); Boom->SetupAttachment(RootComponent);
    Boom->TargetArmLength=350; Boom->SocketOffset=FVector(0,0,100); Boom->bUsePawnControlRotation=true;
    Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("WalkCamera")); Camera->SetupAttachment(Boom);
    GetMesh()->SetRelativeLocation(FVector(0,0,-88)); GetMesh()->SetRelativeRotation(FRotator(0,-90,0));
}
void ASSWalker::BeginPlay()
{
    Super::BeginPlay();
    GetMesh()->SetSkeletalMesh(LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/SpaceSurvival/Character/SK_Acornaut.SK_Acornaut")));
    GetMesh()->PlayAnimation(LoadObject<UAnimSequence>(nullptr,TEXT("/Game/SpaceSurvival/Character/A_Walk.A_Walk")),true);
}
void ASSWalker::Tick(float Dt) { Super::Tick(Dt); GetMesh()->GlobalAnimRateScale=GetVelocity().Size2D()/180.f; }
void ASSWalker::Move(FVector2D Direction,FVector2D Look,bool Run,float Dt)
{
    AddControllerYawInput(Look.X*90.f*Dt); AddControllerPitchInput(-Look.Y*70.f*Dt);
    const FRotator Yaw(0,GetControlRotation().Yaw,0);
    GetCharacterMovement()->MaxWalkSpeed=Run?560.f:320.f;
    AddMovementInput(Yaw.Vector(),Direction.Y); AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::Y),Direction.X);
}
