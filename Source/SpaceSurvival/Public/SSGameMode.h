#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "SSGameMode.generated.h"
class ASSShip;
class ASSDistantAsteroids;
class ASSAmbientPresentation;
class ASSStation;
class ASSWalker;
class USSSurvivalDirectorComponent;
class ASSEncounterBeacon;
class USSInputGlyphSet;

enum class ESSPanel
{
    None,
    Main,
    Settings,
    Graphics,
    Audio,
    Controls,
    Progression,
    History,
    Ship,
    Weapon,
    Upgrades,
    Repair,
    Contracts,
    Save,
    Vendor,
    Reward,
    Depot,
    Launch,
    Results,
    Acknowledgements,
    AlienGallery
};
struct FSSMenuEntry
{
    FString Label;
    int32 Action = 0;
    bool Enabled = true;
};

UCLASS()
class SPACESURVIVAL_API ASSGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    ASSGameMode();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void ApplyWorldOffset(const FVector &InOffset, bool bWorldShift) override;
    ASSShip *GetPlayerShip() const
    {
        return Ship;
    }
    void NotifyEnemyKilled();
    void NotifyEventCompleted(bool bCombat);
    void NotifyPickup(int32 Kind, float Amount);
    void Announce(const FString &Message);
    bool IsAnnouncementVisible() const;
    void WarnThreat(const FString &Message, FVector Position, float Duration = 4.f);
    void React(const FString &Message);
    void Interact();
    void OpenPanel(ESSPanel Panel);
    void ClosePanel();
    void ActivateEntry(int32 Index);
    void StartNewRun();
    void LaunchFromHub();
    void ShowHangar();
    bool IsMenuOpen() const
    {
        return Panel != ESSPanel::None;
    }
    bool InHangar() const;
    FString PanelTitle, PanelDetail, Announcement;
    FString ThreatWarning, PilotReaction;
    FVector ThreatPosition = FVector::ZeroVector;
    float ThreatWarningSeconds = 0.f, PilotReactionSeconds = 0.f;
    TArray<FSSMenuEntry> Entries;
    int32 SelectedEntry = 0;
    ESSPanel Panel = ESSPanel::None;
    FVector StationTarget = FVector::ZeroVector;
    float AnnouncementSeconds = 0.f, WeaponBuffSeconds = 0.f;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USSSurvivalDirectorComponent> Director;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<class USSAlienGallery> AlienGallery;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Content")
    TObjectPtr<class USSPhase1Data> Tuning;
    UPROPERTY()
    TObjectPtr<ASSEncounterBeacon> ActiveBeacon;

private:
    friend class ASSPlayerController;
    friend class ASSWave10Soak;
    friend class FSSAudioFirstState;
    bool bAutomatedSoakInput = false;
    UPROPERTY()
    TObjectPtr<ASSShip> Ship;
    UPROPERTY()
    TObjectPtr<ASSDistantAsteroids> DistantField;
    UPROPERTY()
    TObjectPtr<ASSAmbientPresentation> AmbientPresentation;
    UPROPERTY()
    TObjectPtr<class ASSSpaceScenery> SpaceScenery;
    UPROPERTY()
    TObjectPtr<class USSSpaceLookData> SpaceLook;
    int32 ActiveSkyIndex = -1;
    UPROPERTY()
    TObjectPtr<ASSStation> Hub;
    UPROPERTY()
    TObjectPtr<ASSWalker> Walker;
    UPROPERTY()
    TObjectPtr<class UAudioComponent> MusicBase;
    UPROPERTY()
    TObjectPtr<class UAudioComponent> MusicPressure;
    UPROPERTY()
    TObjectPtr<class UAudioComponent> MusicClimax;
    UPROPERTY()
    TObjectPtr<class UMaterialInstanceDynamic> SpaceMaterial;
    UPROPERTY()
    TObjectPtr<AActor> SpaceBackdrop;
    UPROPERTY()
    TObjectPtr<AActor> SpaceStars;
    UPROPERTY()
    TObjectPtr<class USoundBase> AlarmSound;
    UPROPERTY()
    TObjectPtr<class USoundAttenuation> AlarmAttenuation;
    // Device-aware HUD prompts: assign one set per device once the owned B23
    // glyph textures are imported. Unassigned actions fall back to text.
    UPROPERTY(EditDefaultsOnly, Category = "Input Glyphs")
    TObjectPtr<USSInputGlyphSet> KeyboardGlyphs;
    UPROPERTY(EditDefaultsOnly, Category = "Input Glyphs")
    TObjectPtr<USSInputGlyphSet> GamepadGlyphs;
    int32 PreviousPhase = -1, PreviousWave = -1;
    int32 SelectedShip = 0, SelectedWeapon = 0;
    int32 HistoryPage = 0;
    bool PendingReward = false, RewardCombat = false, DeathPersisted = false;
    float RegionTime = 0.f;
    float ArrivalColorBlend = 0.f;
    bool bWormholeArrived = false;
    float AlarmCooldown = 0.f, ReactionCooldown = 0.f;
    bool LowHullAlerted = false;
    void UpdateMusicMix();
    void UpdateThreatFeedback(float DeltaSeconds);
    void EnterStation();
    void SpawnFlight(FVector Location, FRotator Rotation);
    void AddEntry(const FString &Label, int32 Action, bool Enabled = true);
};

UCLASS()
class SPACESURVIVAL_API ASSPlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    ASSPlayerController();
    virtual void PlayerTick(float DeltaSeconds) override;
    UFUNCTION(Exec)
    void SSReviewExit();
    UFUNCTION(Exec)
    void SSReviewAlienGallery(bool Assets = false);
    UFUNCTION(Exec)
    void SSReviewGalleryReturn();
    UFUNCTION(Exec)
    void SSReviewGallerySwitch();

    // True when the most recent frame's input came from a gamepad rather than
    // keyboard/mouse. Drives which device's HUD prompt/glyph is shown.
    UPROPERTY(BlueprintReadOnly)
    bool bLastInputWasGamepad = false;

private:
    void UpdateLastInputDevice();
    bool BoostLatch = false, BrakeLatch = false;
    TWeakObjectPtr<APawn> LastInputPawn;
};
