#pragma once
#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "GameFramework/SaveGame.h"
#include "Domain/SurvivalCore.h"
#include "SSGameInstance.generated.h"

UCLASS()
class SPACESURVIVAL_API USSStoredData : public USaveGame
{
    GENERATED_BODY()
public:
    UPROPERTY(SaveGame)
    int32 Version = 1;
    UPROPERTY(SaveGame)
    bool Valid = false;
    UPROPERTY(SaveGame)
    FString Payload;
};

UCLASS()
class SPACESURVIVAL_API USSGameInstance : public UGameInstance
{
    GENERATED_BODY()
public:
    SS::Session Session;
    FString LastSaveError;
    bool AccountStorageBlocked = false;
    virtual void Init() override;
    virtual void OnStart() override;
    bool HasSuspendedRun() const;
    bool SuspendRun();
    bool ResumeRun();
    bool PersistAccount();
    bool PersistSettings();
    bool PersistDeath();
    bool DiscardSliceRun();
    bool InvalidateSuspend();
    /** Practice starts only from home, with no live survival run to lose on quit. */
    bool BeginFreeFlight(SS::Ship Ship, SS::Weapon Weapon);
    bool EndFreeFlight();
    bool IsFreeFlight() const
    {
        return SurvivalBeforeFreeFlight.IsSet();
    }
    void ApplySettings();

private:
    TOptional<SS::Session> SurvivalBeforeFreeFlight;
    bool RejectFreeFlightSave();
    bool WriteDomain(const FString &Slot, const std::string &Payload, bool Valid = true);
    bool ReadDomain(const FString &Slot, std::string &Payload) const;
};
