#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "SSGameMode.generated.h"
class ASSShip; class ASSStation; class ASSWalker; class USSSurvivalDirectorComponent; class ASSEncounterBeacon;

enum class ESSPanel { None, Main, Settings, Graphics, Audio, Controls, Progression, Ship, Weapon, Upgrades, Repair, Contracts, Save, Vendor, Reward, Depot, Launch, Results };
struct FSSMenuEntry { FString Label; int32 Action=0; bool Enabled=true; };

UCLASS()
class SPACESURVIVAL_API ASSGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    ASSGameMode();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    ASSShip* GetPlayerShip() const { return Ship; }
    void NotifyEnemyKilled();
    void NotifyEventCompleted(bool bCombat);
    void NotifyPickup(int32 Kind,float Amount);
    void Announce(const FString& Message);
    void Interact();
    void OpenPanel(ESSPanel Panel);
    void ClosePanel();
    void ActivateEntry(int32 Index);
    void StartNewRun();
    void LaunchFromHub();
    void ShowHangar();
    bool IsMenuOpen() const { return Panel!=ESSPanel::None; }
    bool InHangar() const;
    FString PanelTitle, PanelDetail, Announcement;
    TArray<FSSMenuEntry> Entries;
    int32 SelectedEntry=0;
    ESSPanel Panel=ESSPanel::None;
    FVector StationTarget=FVector::ZeroVector;
    float AnnouncementSeconds=0.f, WeaponBuffSeconds=0.f;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USSSurvivalDirectorComponent> Director;
    UPROPERTY() TObjectPtr<ASSEncounterBeacon> ActiveBeacon;
private:
    UPROPERTY() TObjectPtr<ASSShip> Ship;
    UPROPERTY() TObjectPtr<ASSStation> Hub;
    UPROPERTY() TObjectPtr<ASSWalker> Walker;
    UPROPERTY() TObjectPtr<class UAudioComponent> MusicBase;
    UPROPERTY() TObjectPtr<class UAudioComponent> MusicPressure;
    UPROPERTY() TObjectPtr<class UAudioComponent> MusicClimax;
    int32 PreviousPhase=-1, PreviousWave=-1;
    int32 SelectedShip=0,SelectedWeapon=0;
    bool PendingReward=false, RewardCombat=false, DeathPersisted=false;
    float RegionTime=0.f;
    void EnterStation();
    void SpawnFlight(FVector Location,FRotator Rotation);
    void AddEntry(const FString& Label,int32 Action,bool Enabled=true);
};

UCLASS()
class SPACESURVIVAL_API ASSPlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    ASSPlayerController();
    virtual void PlayerTick(float DeltaSeconds) override;
private:
    bool BoostLatch=false,BrakeLatch=false;
};
