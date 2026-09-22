#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "SSContentTypes.h"
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
    AlienGallery,
    Paint,
    Wardrobe
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
    void NotifyPlayerShotHit();
    void NotifyEventCompleted(bool bCombat);
    void NotifyPickup(int32 Kind, float Amount);
    void Announce(const FString &Message);
    bool IsAnnouncementVisible() const;
    void WarnThreat(const FString &Message, FVector Position, float Duration = 4.f);
    void React(const FString &Message);
    void Interact();
    void OpenPanel(ESSPanel Panel);
    /** Approved front-end screen; active-run pause menus retain their existing actions. */
    bool IsTitleMenu() const;
    void ClosePanel();
    void ActivateEntry(int32 Index, bool FromPointer = false);
    void StartNewRun();
    void StartFreeFlight();
    void EndFreeFlight();
    void LaunchFromHub();
    bool IsWalkerInsideShip(const ASSWalker *Candidate) const;
    bool TryBoardShip(ASSWalker *Candidate);
    void ShowHangar();
    bool IsMenuOpen() const
    {
        return Panel != ESSPanel::None;
    }
    bool InHangar() const;
    bool IsInStationZone() const;
    bool IsDepartingStation() const
    {
        return bDepartingStation;
    }
    FVector GetLandingTarget() const;
    float GetDockingRadius() const;
    /** Shared eligibility and feedback for the HUD and the actual use-button transaction. */
    bool DockingStatus(FString &Message) const;
    bool RequestDocking();
    FString PanelTitle, PanelDetail, Announcement;
    FString ThreatWarning, PilotReaction;
    FVector ThreatPosition = FVector::ZeroVector;
    float ThreatWarningSeconds = 0.f, PilotReactionSeconds = 0.f;
    /** Counts down after a player shot connects, so the reticle can flash its hit state. */
    float PlayerHitFlashSeconds = 0.f;
    TArray<FSSMenuEntry> Entries;
    int32 SelectedEntry = 0;
    int32 PaintSection = 0; // The hull section the paint bay is showing.
    ESSPanel Panel = ESSPanel::None;
    FVector StationTarget = FVector::ZeroVector;
    float AnnouncementSeconds = 0.f, WeaponBuffSeconds = 0.f;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USSSurvivalDirectorComponent> Director;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<class USSAlienGallery> AlienGallery;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Content")
    TObjectPtr<class USSPhase1Data> Tuning;
    /** Every hero this build can actually put on the deck, in roster order. What the wardrobe lists. */
    TArray<FSSHeroDefinition> WardrobeBodies() const;
    /** The body the deck should be wearing: the saved choice when it is installed, otherwise whatever
     *  roster order gives. Never returns a hero this build does not carry. */
    FName WornHeroId() const;
    /** Put WornHeroId on the walking pawn, if there is one. Safe to call when there is not. */
    void WearHero();
    UPROPERTY()
    TObjectPtr<ASSEncounterBeacon> ActiveBeacon;

private:
    friend class ASSPlayerController;
    friend class ASSHUD; // DrawPrompt reads the glyph sets; main did not build without this.
    friend class ASSWave10Soak;
    friend class FSSAudioFirstState;
    friend class FSSTitleMenuNavigation;
    bool bAutomatedSoakInput = false;
    bool bTitleSettingsNavigation = false;
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
    bool bDepartingStation = false;
    bool bStartNextBlockOnExit = false;
    bool bAtTitleScreen = true;
    void UpdateMusicMix();
    void UpdateThreatFeedback(float DeltaSeconds);
    void EnterStation();
    void SpawnFlight(FVector Location, FRotator Rotation, bool PreserveHub = false);
    void FollowFlightPresentation();
    void BeginDeparture();
    void AddEntry(const FString &Label, int32 Action, bool Enabled = true);
    void RepaintShips();
};

enum class ESSInputFamily : uint8
{
    KeyboardMouse,
    Gamepad
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
    /** Which device family last produced input, for HUD prompts. Defaults to keyboard/mouse so a
     *  cold boot before any input reads correctly on the common case. */
    ESSInputFamily GetInputFamily() const
    {
        return InputFamily;
    }

    // True when the most recent frame's input came from a gamepad rather than
    // keyboard/mouse. Drives which device's HUD prompt/glyph is shown.
    UPROPERTY(BlueprintReadOnly)
    bool bLastInputWasGamepad = false;

private:
    void UpdateLastInputDevice();
    int32 LastMenuStickDirection = 0;
    float MenuRepeatSeconds = 0.f;
    bool BoostLatch = false, BrakeLatch = false;
    /** A menu Back press must be released before B can become a new boost command. */
    bool SuppressGamepadBoostUntilRelease = false;
    bool SuppressGamepadFireUntilRelease = false;
    float KeyboardThrottle = 0.f;
    /** Only a throttle command changes ownership; look, fire and UI glyph changes cannot restore thrust. */
    bool bAnalogThrottle = false;
    float LastRightTriggerCommand = 0.f;
    TWeakObjectPtr<APawn> LastInputPawn;
    ESSInputFamily InputFamily = ESSInputFamily::KeyboardMouse;
};
