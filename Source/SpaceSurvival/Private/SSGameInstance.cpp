#include "SSGameInstance.h"
#include "SSLocalSave.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/GameUserSettings.h"
#include "HAL/IConsoleManager.h"

namespace
{
const FString AccountSlot = TEXT("SS_Account_v1"), SettingsSlot = TEXT("SS_Settings_v1"),
              RunSlot = TEXT("SS_Suspend_v1");
bool WasAwarded(const SS::Account &Account, const std::string &RunId)
{
    if (Account.lastAwardedRunId == RunId)
        return true;
    for (const auto &Entry : Account.history)
        if (Entry.id == RunId)
            return true;
    return false;
}
} // namespace

void USSGameInstance::Init()
{
    Super::Init();
    std::string Payload, Error;
    if (UGameplayStatics::DoesSaveGameExist(AccountSlot, 0) &&
        (!ReadDomain(AccountSlot, Payload) || !SS::DecodeAccount(Payload, Session.account, Error)))
    {
        AccountStorageBlocked = true;
        LastSaveError = TEXT("Account data could not be read. Original save is protected; restore a backup before "
                             "starting another run.");
    }
    if (ReadDomain(SettingsSlot, Payload))
        SS::DecodeSettings(Payload, Session.settings, Error);
    ApplySettings();
}
void USSGameInstance::OnStart()
{
    Super::OnStart();
    // Init runs before GameEngine is initialized, when UE skips scalability.
    // Reapply after startup so the first frame uses our loaded/default quality.
    ApplySettings();
}
bool USSGameInstance::ReadDomain(const FString &Slot, std::string &Payload) const
{
    if (!UGameplayStatics::DoesSaveGameExist(Slot, 0))
        return false;
    const auto *Record = Cast<USSStoredData>(UGameplayStatics::LoadGameFromSlot(Slot, 0));
    if (!Record || Record->Version != 1 || !Record->Valid)
        return false;
    Payload = TCHAR_TO_UTF8(*Record->Payload);
    return true;
}
bool USSGameInstance::WriteDomain(const FString &Slot, const std::string &Payload, bool Valid)
{
    if (Slot != SettingsSlot && RejectFreeFlightSave())
        return false;
    auto *Record = Cast<USSStoredData>(UGameplayStatics::CreateSaveGameObject(USSStoredData::StaticClass()));
    Record->Valid = Valid;
    Record->Payload = UTF8_TO_TCHAR(Payload.c_str());
    TArray<uint8> Bytes;
    if (!UGameplayStatics::SaveGameToMemory(Record, Bytes))
    {
        LastSaveError = TEXT("Save serialization failed. The previous save was not replaced.");
        return false;
    }
    const auto *Verify = Cast<USSStoredData>(UGameplayStatics::LoadGameFromMemory(Bytes));
    if (!Verify || Verify->Version != Record->Version || Verify->Valid != Valid || Verify->Payload != Record->Payload)
    {
        LastSaveError = TEXT("Save serialization verification failed. The previous save was not replaced.");
        return false;
    }
    return SSLocalSave::Write(Slot, Bytes, LastSaveError);
}
bool USSGameInstance::PersistAccount()
{
    if (RejectFreeFlightSave())
        return false;
    if (AccountStorageBlocked)
    {
        LastSaveError = TEXT("Unreadable account save is protected from overwrite. Restore a backup to continue.");
        return false;
    }
    return WriteDomain(AccountSlot, SS::EncodeAccount(Session.account));
}
bool USSGameInstance::PersistSettings()
{
    ApplySettings();
    return WriteDomain(SettingsSlot, SS::EncodeSettings(Session.settings));
}
bool USSGameInstance::HasSuspendedRun() const
{
    if (AccountStorageBlocked)
        return false;
    std::string Payload, Error;
    SS::Run Candidate;
    return ReadDomain(RunSlot, Payload) && SS::DecodeRun(Payload, Candidate, Error) && Candidate.active &&
           Candidate.phase == SS::Phase::Station &&
           !WasAwarded(IsFreeFlight() ? SurvivalBeforeFreeFlight->account : Session.account, Candidate.id);
}
bool USSGameInstance::SuspendRun()
{
    if (RejectFreeFlightSave())
        return false;
    if (!Session.run.active || Session.run.phase != SS::Phase::Station)
        return false;
    return PersistAccount() && PersistSettings() && WriteDomain(RunSlot, SS::EncodeRun(Session.run));
}
bool USSGameInstance::InvalidateSuspend()
{
    if (RejectFreeFlightSave())
        return false;
    return WriteDomain(RunSlot, "", false);
}
bool USSGameInstance::ResumeRun()
{
    if (RejectFreeFlightSave())
        return false;
    if (AccountStorageBlocked)
        return false;
    std::string Payload, Error;
    SS::Run Candidate;
    if (!ReadDomain(RunSlot, Payload) || !SS::DecodeRun(Payload, Candidate, Error) || !Candidate.active ||
        Candidate.phase != SS::Phase::Station || WasAwarded(Session.account, Candidate.id))
    {
        LastSaveError = TEXT("No valid suspended run is available.");
        return false;
    }
    // Consume durably BEFORE exposing restored gameplay. Fail closed on disk errors.
    if (!InvalidateSuspend())
        return false;
    Session.run = Candidate;
    return true;
}
bool USSGameInstance::PersistDeath()
{
    if (RejectFreeFlightSave())
        return false;
    // Account's lastAwardedRunId also excludes a stale suspended record if a crash
    // occurs between these two writes. Retrying writes cannot award XP twice.
    return PersistAccount() && InvalidateSuspend();
}
bool USSGameInstance::DiscardSliceRun()
{
    if (RejectFreeFlightSave())
        return false;
    if (!Session.AtSliceBoundary())
    {
        LastSaveError = TEXT("Only a live run at Station 2 can be discarded here.");
        return false;
    }
    // BeginWave already records the highest wave in memory. Preserve that account
    // before consuming the checkpoint or clearing the live run; this awards no XP.
    if (!PersistAccount() || !InvalidateSuspend())
        return false;
    Session.run = SS::Run{};
    return true;
}
bool USSGameInstance::RejectFreeFlightSave()
{
    if (!IsFreeFlight())
        return false;
    LastSaveError = TEXT("Free Flight is practice only. Survival progress, XP and checkpoints are protected. "
                         "Return home before loading or saving a survival run.");
    return true;
}

bool USSGameInstance::BeginFreeFlight(SS::Ship Ship, SS::Weapon Weapon)
{
    if (IsFreeFlight())
    {
        LastSaveError = TEXT("Free Flight is already active.");
        return false;
    }
    if (Session.run.active)
    {
        LastSaveError = TEXT("Free Flight is available from home. Continue or safely finish the current survival "
                             "run first; its progress has not been changed.");
        return false;
    }
    if (AccountStorageBlocked)
    {
        LastSaveError = TEXT("Unreadable account save is protected. Restore a backup before selecting a ship.");
        return false;
    }
    SS::Session Practice = Session;
    const FString Id = TEXT("practice-") + FGuid::NewGuid().ToString(EGuidFormats::Digits);
    if (!Practice.StartRun(TCHAR_TO_UTF8(*Id), Ship, Weapon))
    {
        LastSaveError = TEXT("This ship or weapon is not available for Free Flight.");
        return false;
    }
    SurvivalBeforeFreeFlight = Session;
    Session = MoveTemp(Practice);
    LastSaveError.Empty();
    return true;
}

bool USSGameInstance::EndFreeFlight()
{
    if (!IsFreeFlight())
    {
        LastSaveError = TEXT("Free Flight is not active.");
        return false;
    }
    const SS::Settings Settings = Session.settings;
    Session = MoveTemp(SurvivalBeforeFreeFlight.GetValue());
    SurvivalBeforeFreeFlight.Reset();
    Session.settings = Settings;
    LastSaveError.Empty();
    return true;
}

void USSGameInstance::ApplySettings()
{
    if (auto *Settings = UGameUserSettings::GetGameUserSettings())
    {
        Settings->SetOverallScalabilityLevel(Session.settings.quality);
        Settings->SetFrameRateLimit(Session.settings.frameLimit);
        // Graphics changes must not override the startup window/resolution request.
        Settings->ApplyNonResolutionSettings();
    }
    if (auto *CVar = IConsoleManager::Get().FindConsoleVariable(TEXT("r.MotionBlurQuality")))
        CVar->Set(Session.settings.motionBlur ? 3 : 0, ECVF_SetByGameSetting);
}
