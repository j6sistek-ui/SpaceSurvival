#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformFileManager.h"
#include "HAL/PlatformProcess.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Guid.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "PlatformFeatures.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#if WITH_DEV_AUTOMATION_TESTS && PLATFORM_WINDOWS
#include "Windows/WindowsHWrapper.h"
#endif

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
FString LifecyclePath(FString Path)
{
    Path = FPaths::ConvertRelativePathToFull(Path);
    FPaths::NormalizeDirectoryName(Path);
    FPaths::CollapseRelativeDirectories(Path);
    return Path;
}

struct FSSLifecycleIsolation
{
    FString Root;
    FString Token;
    FString Saved;

    bool Verify(FAutomationTestBase &Test)
    {
        const TCHAR *CommandLine = FCommandLine::Get();
        FGuid Guid;
        if (!Test.TestTrue(TEXT("Lifecycle requires explicit unattended Windows editor opt-in"),
                           PLATFORM_WINDOWS && GIsEditor && FParse::Param(CommandLine, TEXT("SSSaveLifecycle")) &&
                               FParse::Param(CommandLine, TEXT("unattended")) &&
                               FParse::Param(CommandLine, TEXT("NullRHI"))) ||
            !Test.TestTrue(TEXT("Lifecycle root and token are explicit"),
                           FParse::Value(CommandLine, TEXT("SSSaveLifecycleRoot="), Root) &&
                               FParse::Value(CommandLine, TEXT("SSSaveLifecycleToken="), Token) &&
                               FGuid::ParseExact(Token, EGuidFormats::Digits, Guid)))
            return false;
        Root = LifecyclePath(Root);
        const FString ExpectedRoot = LifecyclePath(FPaths::ProjectDir() / TEXT("Artifacts/SaveLifecycle") / Token);
        const FString ExpectedUser = Root / TEXT("User");
        Saved = LifecyclePath(FPaths::ProjectSavedDir());
        FString UserArgument;
        if (!Test.TestTrue(TEXT("Only the GUID harness directory may contain lifecycle saves"),
                           Root.Equals(ExpectedRoot, ESearchCase::IgnoreCase)) ||
            !Test.TestTrue(TEXT("UserDir argument and resolved project paths match isolation exactly"),
                           FParse::Value(CommandLine, TEXT("UserDir="), UserArgument) &&
                               LifecyclePath(UserArgument).Equals(ExpectedUser, ESearchCase::IgnoreCase) &&
                               LifecyclePath(FPaths::ProjectUserDir()).Equals(ExpectedUser, ESearchCase::IgnoreCase) &&
                               Saved.Equals(ExpectedUser / TEXT("Saved"), ESearchCase::IgnoreCase) &&
                               FPaths::ShouldSaveToUserDir()))
            return false;
        // Windows IsSymlink tests FILE_ATTRIBUTE_REPARSE_POINT, including directory junctions.
        auto &Files = FPlatformFileManager::Get().GetPlatformFile();
        for (FString Path = Saved / TEXT("SaveGames"); !Path.IsEmpty();)
        {
            if (!Test.TestTrue(TEXT("Save path ancestors cannot redirect through reparse points"),
                               Files.IsSymlink(*Path) == ESymlinkResult::NonSymlink))
                return false;
            const FString Parent = FPaths::GetPath(Path);
            if (Parent == Path)
                break;
            Path = Parent;
        }
        FString Marker;
        if (!Test.TestTrue(TEXT("Fresh harness marker matches the unique token"),
                           FFileHelper::LoadFileToString(Marker, *(Root / TEXT(".ss-save-lifecycle"))) &&
                               Marker.TrimStartAndEnd() == Token))
            return false;
        // Compare the virtual Windows backend with the engine's exact generic singleton.
        // A configured GDK/cloud/custom backend fails closed before any GameInstance Init.
        auto &Features = IPlatformFeaturesModule::Get();
        if (!Test.TestTrue(TEXT("Active platform storage is the verified local generic backend"),
                           Features.GetSaveGameSystem() == Features.IPlatformFeaturesModule::GetSaveGameSystem()))
            return false;
        Test.AddInfo(TEXT("SAVE_LIFECYCLE_ISOLATION_VERIFIED: ") + Saved / TEXT("SaveGames"));
        return true;
    }

    TSharedPtr<FJsonObject> Read(const FString &Phase, FAutomationTestBase &Test) const
    {
        FString Text;
        TSharedPtr<FJsonObject> Object;
        if (!FFileHelper::LoadFileToString(Text, *(Root / (Phase + TEXT(".json")))) ||
            !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Object) || !Object.IsValid())
        {
            Test.AddError(TEXT("Missing or invalid prior lifecycle receipt: ") + Phase);
            return nullptr;
        }
        if (Object->GetStringField(TEXT("token")) != Token ||
            Object->GetNumberField(TEXT("processId")) == FPlatformProcess::GetCurrentProcessId() ||
            !Object->GetBoolField(TEXT("success")))
        {
            Test.AddError(TEXT("Prior stage was not successful in a separate process."));
            return nullptr;
        }
        return Object;
    }

    bool Receipt(const FString &Phase, FAutomationTestBase &Test, USSGameInstance *Instance = nullptr) const
    {
        if (Test.HasAnyErrors())
            return false;
        auto Object = MakeShared<FJsonObject>();
        Object->SetStringField(TEXT("phase"), Phase);
        Object->SetStringField(TEXT("token"), Token);
        Object->SetStringField(TEXT("savedDir"), Saved);
        Object->SetNumberField(TEXT("processId"), FPlatformProcess::GetCurrentProcessId());
        Object->SetBoolField(TEXT("success"), true);
        Object->SetBoolField(TEXT("genericBackendVerified"), true);
        Object->SetBoolField(TEXT("gameInstanceInitialized"), Instance != nullptr);
        if (Phase == TEXT("StageCreateDenied") || Phase == TEXT("StageReadDenied"))
        {
            Object->SetBoolField(TEXT("allThreeWritesRejectedAndPreserved"), true);
            Object->SetBoolField(TEXT("nativePermissionProbeVerified"), true);
        }
        if (Phase == TEXT("RecoverInterrupted"))
        {
            Object->SetBoolField(TEXT("abandonedInvalidationIgnored"), true);
            Object->SetBoolField(TEXT("originalCheckpointAvailable"), true);
            Object->SetBoolField(TEXT("onlyRecordedTemporaryRemoved"), true);
        }
        if (Phase == TEXT("ResumeDeath"))
        {
            Object->SetBoolField(TEXT("lockedSuspensionRejectedAndPreserved"), true);
            Object->SetBoolField(TEXT("lockedAccountRejectedAndPreserved"), true);
            Object->SetBoolField(TEXT("replacementRetriesSucceeded"), true);
            Object->SetBoolField(TEXT("failedReplacementStagingCleaned"), true);
        }
        if (Phase == TEXT("SeedCorruptAccount"))
        {
            Object->SetBoolField(TEXT("domainCorruptEnvelopeSeeded"), true);
            Object->SetBoolField(TEXT("exactOriginalFixtureCopyVerified"), true);
            Object->SetBoolField(TEXT("exactCorruptFixtureCopyVerified"), true);
        }
        if (Phase == TEXT("ProtectCorruptAccount"))
        {
            Object->SetBoolField(TEXT("freshInitProtectedAccount"), true);
            Object->SetBoolField(TEXT("resumeBlocked"), true);
            Object->SetBoolField(TEXT("gameModeNewRunBlocked"), true);
            Object->SetBoolField(TEXT("persistAccountBlocked"), true);
            Object->SetBoolField(TEXT("corruptBytesPreservedBeforeRestore"), true);
            Object->SetBoolField(TEXT("exactOriginalFixtureCopyRestored"), true);
            Object->SetBoolField(TEXT("sameInstanceRemainsBlockedAfterFixtureRestore"), true);
        }
        if (Phase == TEXT("RecoverAccount"))
        {
            Object->SetBoolField(TEXT("freshInitRestoredAccount"), true);
            Object->SetBoolField(TEXT("originalCheckpointAvailable"), true);
            Object->SetBoolField(TEXT("validAccountPersistenceRestored"), true);
        }
        if (Instance)
        {
            const auto &Session = Instance->Session;
            Object->SetStringField(TEXT("accountPayload"), UTF8_TO_TCHAR(SS::EncodeAccount(Session.account).c_str()));
            Object->SetStringField(TEXT("runPayload"), UTF8_TO_TCHAR(SS::EncodeRun(Session.run).c_str()));
            Object->SetStringField(TEXT("settingsPayload"),
                                   UTF8_TO_TCHAR(SS::EncodeSettings(Session.settings).c_str()));
            Object->SetNumberField(TEXT("xp"), double(Session.account.xp));
            Object->SetNumberField(TEXT("level"), Session.account.level);
            Object->SetNumberField(TEXT("completedRuns"), Session.account.runs);
            if (Phase == TEXT("PrepareStation5") || Phase == TEXT("PrepareStation10"))
            {
                Object->SetStringField(TEXT("evidenceType"), TEXT("PREPARED_FIXTURE_NOT_GAMEPLAY"));
                Object->SetNumberField(TEXT("preparedWave"), Session.run.wave);
                Object->SetBoolField(TEXT("runActive"), Session.run.active);
                Object->SetBoolField(TEXT("xpAwarded"), Session.run.xpAwarded);
                Object->SetBoolField(TEXT("unconsumedSuspensionVerified"), Instance->HasSuspendedRun());
                Object->SetStringField(TEXT("fixtureDescription"),
                                       TEXT("Assisted station state: 100 kills, Hull II, Vector Thrusters, pending "
                                            "utility reward, weapon buff and explicit lifecycle settings. Objective "
                                            "contract active at Wave 5, completed at Wave 10. No natural travel."));
            }
        }
        FString Text;
        FJsonSerializer::Serialize(Object, TJsonWriterFactory<>::Create(&Text));
        return Test.TestTrue(TEXT("Write isolated lifecycle receipt"),
                             FFileHelper::SaveStringToFile(Text, *(Root / (Phase + TEXT(".json")))));
    }
};

struct FSSLifecycleInstance
{
    USSGameInstance *Instance = nullptr;
    UWorld *World = nullptr;

    void Initialize()
    {
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // Only called after isolation passed. This invokes the real override of Init.
        Instance->InitializeStandalone();
        World = Instance->GetWorld();
    }

    ~FSSLifecycleInstance()
    {
        if (Instance)
            Instance->Shutdown();
        if (World)
        {
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
        }
        if (Instance)
            Instance->RemoveFromRoot();
    }
};

// A real Windows sharing violation exercises the production replacement path. UE OpenRead(false)
// may still permit deletion when file.allowdeleteopenfiles is enabled in editor, so deny both
// write and delete sharing explicitly. Only the already verified GUID profile reaches this helper.
struct FSSLifecycleSaveLock
{
#if PLATFORM_WINDOWS
    HANDLE Handle = INVALID_HANDLE_VALUE;
#endif

    bool Open(const FString &Path)
    {
#if PLATFORM_WINDOWS
        if (FPlatformFileManager::Get().GetPlatformFile().IsSymlink(*Path) != ESymlinkResult::NonSymlink)
            return false;
        FString Native = IFileManager::Get().ConvertToAbsolutePathForExternalAppForRead(*Path);
        Native.ReplaceInline(TEXT("/"), TEXT("\\"));
        Handle =
            CreateFileW(*Native, GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
        return Handle != INVALID_HANDLE_VALUE;
#else
        return false;
#endif
    }

    ~FSSLifecycleSaveLock()
    {
#if PLATFORM_WINDOWS
        if (Handle != INVALID_HANDLE_VALUE)
            CloseHandle(Handle);
#endif
    }
};

bool CheckNoStagingFiles(FAutomationTestBase &Test, const FSSLifecycleIsolation &Isolation)
{
    TArray<FString> Files;
    IFileManager::Get().FindFiles(Files, *(Isolation.Saved / TEXT("SaveGames/*.tmp")), true, false);
    return Test.TestTrue(TEXT("Failed replacement cleans its isolated temporary file"), Files.IsEmpty());
}

bool CheckConsumed(FAutomationTestBase &Test, USSGameInstance *Instance)
{
    auto *Record = Cast<USSStoredData>(UGameplayStatics::LoadGameFromSlot(TEXT("SS_Suspend_v1"), 0));
    return Test.TestNotNull(TEXT("Consumed suspension still has a durable record"), Record) &&
           Test.TestTrue(TEXT("Suspension was durably invalidated and its payload cleared"),
                         !Record->Valid && Record->Payload.IsEmpty()) &&
           Test.TestFalse(TEXT("Consumed suspension is unavailable"), Instance->HasSuspendedRun());
}
} // namespace

IMPLEMENT_COMPLEX_AUTOMATION_TEST(FSSSaveLifecycle, "SpaceSurvival.SaveLifecycle",
                                  EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
void FSSSaveLifecycle::GetTests(TArray<FString> &Names, TArray<FString> &Commands) const
{
    // Ordinary "RunTests SpaceSurvival" does not list or execute these disk transactions.
    // Scripts/TestSaveLifecycle.ps1 opts in and starts exactly one stage per fresh process.
    FString Phase;
    if (FParse::Param(FCommandLine::Get(), TEXT("SSSaveLifecycle")) &&
        FParse::Value(FCommandLine::Get(), TEXT("SSSaveLifecyclePhase="), Phase))
    {
        Names.Add(Phase);
        Commands.Add(Phase);
    }
}

bool FSSSaveLifecycle::RunTest(const FString &Phase)
{
    FSSLifecycleIsolation Isolation;
    if (!Isolation.Verify(*this))
        return false;
    if (Phase == TEXT("Preflight"))
    {
        for (const TCHAR *Slot : {TEXT("SS_Account_v1"), TEXT("SS_Settings_v1"), TEXT("SS_Suspend_v1")})
            TestFalse(TEXT("Fresh isolated slot must not exist"), UGameplayStatics::DoesSaveGameExist(Slot, 0));
        return Isolation.Receipt(Phase, *this);
    }
    const bool FaultMode = FParse::Param(FCommandLine::Get(), TEXT("SSSaveFaults"));
    const bool FaultPhase = Phase == TEXT("StageCreateDenied") || Phase == TEXT("StageReadDenied") ||
                            Phase == TEXT("InterruptConsume") || Phase == TEXT("RecoverInterrupted");
    if (FaultPhase && !TestTrue(TEXT("Storage faults require the explicit fault-mode opt-in"), FaultMode))
        return false;
    const bool CorruptMode = FParse::Param(FCommandLine::Get(), TEXT("SSCorruptAccount"));
    const bool CorruptPhase = Phase == TEXT("SeedCorruptAccount") || Phase == TEXT("ProtectCorruptAccount") ||
                              Phase == TEXT("RecoverAccount");
    if (CorruptPhase &&
        !TestTrue(TEXT("Domain corruption requires its separate explicit opt-in"), CorruptMode && !FaultMode))
        return false;
    const int32 PreparedWave = Phase == TEXT("PrepareStation5") ? 5 : Phase == TEXT("PrepareStation10") ? 10 : 0;
    if (PreparedWave != 0)
    {
        int32 RequestedWave = 0;
        if (!TestTrue(TEXT("Station preparation requires a matching explicit opt-in"),
                      FParse::Value(FCommandLine::Get(), TEXT("SSPreparePackagedStation="), RequestedWave) &&
                          RequestedWave == PreparedWave))
            return false;
    }
    const FString Prior = (Phase == TEXT("Suspend") || Phase == TEXT("SeedCorruptAccount") || PreparedWave != 0)
                              ? TEXT("Preflight")
                          : Phase == TEXT("ProtectCorruptAccount")     ? TEXT("SeedCorruptAccount")
                          : Phase == TEXT("RecoverAccount")            ? TEXT("ProtectCorruptAccount")
                          : Phase == TEXT("RecoverInterrupted")        ? TEXT("InterruptConsume")
                          : FaultPhase || Phase == TEXT("ResumeDeath") ? TEXT("Suspend")
                          : Phase == TEXT("FreshStart")                ? TEXT("ResumeDeath")
                                                                       : TEXT("");
    if (!TestFalse(TEXT("Lifecycle phase is recognized"), Prior.IsEmpty()))
        return false;
    auto Previous = Isolation.Read(Prior, *this);
    if (!Previous)
        return false;
    // These exact test-owned files are the only corruption/restoration targets. Reject a redirected
    // leaf as well as the ancestors verified above, before Init can read any account bytes.
    const FString AccountPath = Isolation.Saved / TEXT("SaveGames/SS_Account_v1.sav");
    const FString OriginalCopy = Isolation.Root / TEXT("CorruptAccount.original");
    const FString CorruptCopy = Isolation.Root / TEXT("CorruptAccount.corrupt");
    if (CorruptPhase)
    {
        auto &Files = FPlatformFileManager::Get().GetPlatformFile();
        for (const FString &Path :
             {AccountPath, OriginalCopy, CorruptCopy, Isolation.Saved / TEXT("SaveGames/SS_Settings_v1.sav"),
              Isolation.Saved / TEXT("SaveGames/SS_Suspend_v1.sav")})
            if (!TestTrue(TEXT("Corruption fixture leaves cannot redirect outside the GUID profile"),
                          Files.IsSymlink(*Path) == ESymlinkResult::NonSymlink))
                return false;
    }
    FSSLifecycleInstance Fixture;
    Fixture.Initialize();
    auto *Instance = Fixture.Instance;
    auto &Session = Instance->Session;
    if (Phase == TEXT("ProtectCorruptAccount"))
    {
        TArray<uint8> Original, Corrupt, Actual;
        if (!TestTrue(TEXT("Read the exact valid and corrupt test-owned byte copies"),
                      FFileHelper::LoadFileToArray(Original, *OriginalCopy) &&
                          FFileHelper::LoadFileToArray(Corrupt, *CorruptCopy) && Original != Corrupt &&
                          FFileHelper::LoadFileToArray(Actual, *AccountPath) && Actual == Corrupt))
            return false;
        const auto *OriginalRecord = Cast<USSStoredData>(UGameplayStatics::LoadGameFromMemory(Original));
        SS::Account Decoded;
        std::string Error;
        if (!TestTrue(TEXT("Restoration copy is the exact valid account from the seed process"),
                      OriginalRecord && OriginalRecord->Version == 1 && OriginalRecord->Valid &&
                          OriginalRecord->Payload == Previous->GetStringField(TEXT("accountPayload")) &&
                          SS::DecodeAccount(TCHAR_TO_UTF8(*OriginalRecord->Payload), Decoded, Error)))
            return false;
        TestTrue(TEXT("Real fresh Init protects the domain-corrupt account with an explicit error"),
                 Instance->AccountStorageBlocked &&
                     Instance->LastSaveError.Contains(TEXT("Account data could not be read")) &&
                     Instance->LastSaveError.Contains(TEXT("protected")));
        const auto RunBefore = SS::EncodeRun(Session.run);
        const auto AccountBefore = SS::EncodeAccount(Session.account);
        TestFalse(TEXT("Protected account hides the existing checkpoint"), Instance->HasSuspendedRun());
        TestFalse(TEXT("Protected account refuses ResumeRun"), Instance->ResumeRun());
        TestFalse(TEXT("Protected account refuses direct account persistence"), Instance->PersistAccount());
        TestTrue(TEXT("Account persistence reports overwrite protection"),
                 Instance->LastSaveError.Contains(TEXT("protected from overwrite")));
        // InitializeStandalone already owns a transient, initialized game world. Do not begin play,
        // construct a station or create a player: the real New Run path must stop at PersistAccount.
        if (!TestNotNull(TEXT("Protected GameInstance owns an isolated world"), Fixture.World) ||
            !TestFalse(TEXT("Corruption guard fixture has not entered gameplay"), Fixture.World->HasBegunPlay()))
            return false;
        auto *Mode = Fixture.World->SpawnActor<ASSGameMode>();
        if (!TestNotNull(TEXT("Spawn the real GameMode for its New Run admission guard"), Mode) ||
            !TestTrue(TEXT("GameMode is bound to the protected isolated instance"),
                      Mode->GetGameInstance<USSGameInstance>() == Instance))
            return false;
        Mode->StartNewRun();
        TestTrue(TEXT("New Run reports the protected account and does not launch a ship"),
                 Mode->Announcement == Instance->LastSaveError &&
                     Mode->Announcement.Contains(TEXT("protected from overwrite")) && !Mode->GetPlayerShip());
        TestTrue(TEXT("Rejected resume, persistence and New Run leave account and run state unchanged"),
                 !Session.run.active && SS::EncodeRun(Session.run) == RunBefore &&
                     SS::EncodeAccount(Session.account) == AccountBefore && Session.account.xp == 0 &&
                     Session.account.runs == 0 && Session.account.history.empty());
        TestTrue(TEXT("Every original corrupt byte survives Init and all rejected actions"),
                 FFileHelper::LoadFileToArray(Actual, *AccountPath) && Actual == Corrupt);
        CheckNoStagingFiles(*this, Isolation);
        if (HasAnyErrors())
            return false;
        // Manual fixture restoration only, after protection is proven. This is not a product backup
        // or recovery feature; the next fresh process must reload the original account normally.
        TestTrue(TEXT("Restore only the verified original fixture bytes and read-compare them"),
                 FFileHelper::SaveArrayToFile(Original, *AccountPath) &&
                     FFileHelper::LoadFileToArray(Actual, *AccountPath) && Actual == Original);
        TestTrue(TEXT("The existing instance stays blocked until a fresh Init"), Instance->AccountStorageBlocked);
        return Isolation.Receipt(Phase, *this, Instance);
    }
    if (!TestFalse(TEXT("Isolated account initializes without a storage error"), Instance->AccountStorageBlocked))
        return false;
    const std::string RunId = "lifecycle-" + std::string(TCHAR_TO_UTF8(*Isolation.Token));
    if (FaultPhase)
    {
        TestEqual(TEXT("Fault process loads the original account exactly"),
                  FString(UTF8_TO_TCHAR(SS::EncodeAccount(Session.account).c_str())),
                  Previous->GetStringField(TEXT("accountPayload")));
        TestEqual(TEXT("Fault process loads the original settings exactly"),
                  FString(UTF8_TO_TCHAR(SS::EncodeSettings(Session.settings).c_str())),
                  Previous->GetStringField(TEXT("settingsPayload")));
        if (!TestTrue(TEXT("Fault process sees the preserved live checkpoint"), Instance->HasSuspendedRun()) ||
            !TestFalse(TEXT("Init alone never exposes the saved run"), Session.run.active))
            return false;
        auto &Files = FPlatformFileManager::Get().GetPlatformFile();
        if (Phase == TEXT("RecoverInterrupted"))
        {
            const FString Name = Previous->GetStringField(TEXT("stagingName"));
            const FString Prefix = TEXT("SS_Suspend_v1.sav.");
            FGuid StagingGuid;
            if (!TestTrue(TEXT("Recovery names only the recorded unique sibling staging file"),
                          Name == FPaths::GetCleanFilename(Name) && Name.StartsWith(Prefix) &&
                              Name.EndsWith(TEXT(".tmp")) &&
                              FGuid::ParseExact(Name.Mid(Prefix.Len(), Name.Len() - Prefix.Len() - 4),
                                                EGuidFormats::Digits, StagingGuid)))
                return false;
            const FString Staging = Isolation.Saved / TEXT("SaveGames") / Name;
            TArray<uint8> Bytes, Expected;
            if (!TestTrue(
                    TEXT("Abandoned staging is a real file inside the verified profile"),
                    Files.IsSymlink(*Staging) == ESymlinkResult::NonSymlink &&
                        FFileHelper::LoadFileToArray(Bytes, *Staging) &&
                        FFileHelper::LoadFileToArray(Expected, *(Isolation.Root / TEXT("InterruptConsume.expected"))) &&
                        Bytes == Expected))
                return false;
            const auto *Record = Cast<USSStoredData>(UGameplayStatics::LoadGameFromMemory(Bytes));
            TestTrue(TEXT("Abandoned file contains the completed but uncommitted invalidation"),
                     Record && Record->Version == 1 && !Record->Valid && Record->Payload.IsEmpty());
            const auto *Live = Cast<USSStoredData>(UGameplayStatics::LoadGameFromSlot(TEXT("SS_Suspend_v1"), 0));
            TestTrue(TEXT("Fresh Init ignores the orphan and preserves the exact original valid run"),
                     Live && Live->Valid && Live->Payload == Previous->GetStringField(TEXT("runPayload")) &&
                         Instance->HasSuspendedRun() && !Session.run.active);
            if (HasAnyErrors())
                return false;
            TestTrue(TEXT("Remove only this harness's recorded abandoned staging file"), Files.DeleteFile(*Staging));
            CheckNoStagingFiles(*this, Isolation);
        }
        else if (Phase == TEXT("InterruptConsume"))
        {
            // The parent owns the destination oplock until this process is confirmed terminated.
            // A completed stage must match these bytes before the parent accepts a replacement barrier.
            auto *Invalid = Cast<USSStoredData>(UGameplayStatics::CreateSaveGameObject(USSStoredData::StaticClass()));
            Invalid->Valid = false;
            Invalid->Payload.Empty();
            TArray<uint8> Expected;
            if (!TestTrue(TEXT("Serialize the expected real suspension invalidation"),
                          UGameplayStatics::SaveGameToMemory(Invalid, Expected) &&
                              FFileHelper::SaveArrayToFile(Expected,
                                                           *(Isolation.Root / TEXT("InterruptConsume.expected")))) ||
                !Isolation.Receipt(TEXT("InterruptConsumeReady"), *this, Instance))
                return false;
            AddInfo(TEXT("SAVE_FAULT_REPLACEMENT_READY: invoking the real ResumeRun; parent holds the oplock."));
            Instance->ResumeRun();
            AddError(TEXT(
                "Interrupted ResumeRun returned before the parent terminated this process; no interruption pass."));
            return false;
        }
        else
        {
            const bool ReadDenied = Phase == TEXT("StageReadDenied");
            const FString Probe = Isolation.Saved / TEXT("SaveGames/StagingProbe.tmp");
            const uint8 ProbeBytes[] = {0x53, 0x53, 0x01, 0x7f};
            {
                TUniquePtr<IFileHandle> Handle(Files.OpenWrite(*Probe));
                if (ReadDenied)
                {
                    if (!TestTrue(TEXT("Real staging probe can create, write and flush under the read-denial ACL"),
                                  Handle && Handle->Write(ProbeBytes, UE_ARRAY_COUNT(ProbeBytes)) &&
                                      Handle->Flush(true)))
                        return false;
                    Handle.Reset();
                    TUniquePtr<IFileHandle> Reader(Files.OpenRead(*Probe));
                    TestFalse(TEXT("The new staging probe is actually denied read access"), Reader.IsValid());
                    Reader.Reset();
                    TestTrue(TEXT("Read-denied probe still permits cleanup"), Files.DeleteFile(*Probe));
                }
                else
                    TestFalse(TEXT("The GUID directory actually denies staging-file creation"), Handle.IsValid());
            }
            const std::string OriginalAccount = SS::EncodeAccount(Session.account);
            const std::string OriginalSettings = SS::EncodeSettings(Session.settings);
            const std::string OriginalRun = SS::EncodeRun(Session.run);
            for (const TCHAR *Slot : {TEXT("SS_Suspend_v1"), TEXT("SS_Account_v1"), TEXT("SS_Settings_v1")})
            {
                const FString Path = Isolation.Saved / TEXT("SaveGames") / (FString(Slot) + TEXT(".sav"));
                TArray<uint8> Before, After;
                if (!TestTrue(TEXT("Read the original slot before the staging fault"),
                              FFileHelper::LoadFileToArray(Before, *Path)))
                    return false;
                if (ReadDenied)
                    AddExpectedMessagePlain(TEXT("Failed to read file '") + Path + TEXT("."), ELogVerbosity::Warning,
                                            EAutomationExpectedMessageFlags::Contains, 1);
                bool Saved = false;
                if (FString(Slot) == TEXT("SS_Suspend_v1"))
                    Saved = Instance->ResumeRun();
                else if (FString(Slot) == TEXT("SS_Account_v1"))
                {
                    Session.account.tutorialFlags ^= 1u;
                    Saved = Instance->PersistAccount();
                    Session.account.tutorialFlags ^= 1u;
                }
                else
                {
                    const double BeforeSensitivity = Session.settings.mouseSensitivity;
                    Session.settings.mouseSensitivity = 2.1;
                    Saved = Instance->PersistSettings();
                    Session.settings.mouseSensitivity = BeforeSensitivity;
                }
                TestFalse(TEXT("Real GI persistence rejects the staging fault"), Saved);
                TestTrue(TEXT("Staging failure is reported before destination replacement"),
                         Instance->LastSaveError.Contains(TEXT("Save staging or verification failed")));
                TestTrue(TEXT("Every byte of the prior live slot survives the staging failure"),
                         FFileHelper::LoadFileToArray(After, *Path) && After == Before);
                CheckNoStagingFiles(*this, Isolation);
            }
            TestTrue(TEXT("Failed staging does not expose a run, consume its checkpoint, or change account XP"),
                     SS::EncodeRun(Session.run) == OriginalRun &&
                         SS::EncodeAccount(Session.account) == OriginalAccount &&
                         SS::EncodeSettings(Session.settings) == OriginalSettings && !Session.run.active &&
                         Session.account.xp == 0 && Session.account.runs == 0 && Instance->HasSuspendedRun());
        }
        return Isolation.Receipt(Phase, *this, Instance);
    }
    if (FaultMode && Phase == TEXT("ResumeDeath") && !Isolation.Read(TEXT("RecoverInterrupted"), *this))
        return false;
    if (Phase == TEXT("Suspend") || Phase == TEXT("SeedCorruptAccount") || PreparedWave != 0)
    {
        TestEqual(TEXT("First process begins with fresh account XP"), Session.account.xp, std::int64_t(0));
        TestFalse(TEXT("Fresh account has no suspension"), Instance->HasSuspendedRun());
        if (!TestTrue(TEXT("Create lifecycle run"), Session.StartRun(RunId)))
            return false;
        // Station state is a deterministic fixture; integrated travel is tested by Journey automation.
        for (int32 Index = 0; Index < 100; ++Index)
            Session.RecordKill();
        Session.run.wave = Session.run.wavesCompleted = 5;
        Session.run.phase = SS::Phase::Station;
        Session.run.phaseSeconds = Session.run.phaseDuration = 0;
        Session.account.highestWave = 5;
        Session.run.pendingReward = true;
        Session.run.weaponBuffSeconds = 8.5;
        TestTrue(TEXT("Station upgrade enters the suspended payload"), Session.Purchase(SS::Upgrade::Hull));
        TestTrue(TEXT("Station utility enters the suspended payload"),
                 Session.EquipUtility(SS::Utility::VectorThrusters));
        TestTrue(TEXT("Station contract enters the suspended payload"),
                 Session.AcceptContract(SS::Contract::Objective));
        Session.settings.masterVolume = 0;
        Session.settings.mouseSensitivity = 1.7;
        Session.settings.controllerSensitivity = 1.2;
        Session.settings.uiScale = 1.15;
        if (PreparedWave == 10)
        {
            // Explicit fixture positioning/progress, not a traversal or contract gameplay result.
            // Use docking completion to settle the existing contract exactly as Station 2 does.
            Session.run.wave = Session.run.wavesCompleted = 10;
            Session.run.phase = SS::Phase::Docking;
            Session.run.contractProgress = Session.run.contractTarget;
            if (!TestTrue(TEXT("Prepared Station 2 settles the fixture objective contract"), Session.CompleteDocking()))
                return false;
            Session.account.highestWave = 10;
            TestTrue(TEXT("Station 2 has no unreachable active contract"),
                     Session.run.contract == SS::Contract::None && Session.run.contractsCompleted == 1);
        }
        if (PreparedWave != 0)
        {
            SS::Run Decoded;
            std::string Error;
            const auto Payload = SS::EncodeRun(Session.run);
            if (!TestTrue(TEXT("Prepared station is accepted by the strict production run codec"),
                          SS::DecodeRun(Payload, Decoded, Error) && SS::EncodeRun(Decoded) == Payload) ||
                !TestTrue(TEXT("Prepared fixture is the requested live station without awarded XP"),
                          Session.run.active && Session.run.phase == SS::Phase::Station &&
                              Session.run.wave == PreparedWave && Session.run.wavesCompleted == PreparedWave &&
                              !Session.run.xpAwarded && Session.account.xp == 0 && Session.account.runs == 0 &&
                              Session.account.history.empty()))
                return false;
            AddInfo(FString::Printf(TEXT("PREPARED_FIXTURE_NOT_GAMEPLAY: Wave %d; no resume or death is executed."),
                                    PreparedWave));
        }
        if (!TestTrue(TEXT("Real SuspendRun persists all three domains"), Instance->SuspendRun()))
            return false;
        TestTrue(TEXT("Written station run is available to resume"), Instance->HasSuspendedRun());
        TestEqual(TEXT("XP remains unawarded while suspended"), Session.account.xp, std::int64_t(0));
        if (PreparedWave != 0)
        {
            const auto *Record = Cast<USSStoredData>(UGameplayStatics::LoadGameFromSlot(TEXT("SS_Suspend_v1"), 0));
            TestTrue(TEXT("Preparation leaves the exact valid suspension unconsumed for packaged Continue"),
                     Record && Record->Version == 1 && Record->Valid &&
                         Record->Payload == UTF8_TO_TCHAR(SS::EncodeRun(Session.run).c_str()));
        }
        if (Phase == TEXT("SeedCorruptAccount"))
        {
            auto &Files = FPlatformFileManager::Get().GetPlatformFile();
            TArray<uint8> Original, Copied, Corrupt;
            if (!TestFalse(TEXT("Original fixture copy must not already exist"), Files.FileExists(*OriginalCopy)) ||
                !TestFalse(TEXT("Corrupt fixture copy must not already exist"), Files.FileExists(*CorruptCopy)) ||
                !TestTrue(TEXT("Retain and verify the exact account bytes written by real SuspendRun"),
                          FFileHelper::LoadFileToArray(Original, *AccountPath) &&
                              FFileHelper::SaveArrayToFile(Original, *OriginalCopy) &&
                              FFileHelper::LoadFileToArray(Copied, *OriginalCopy) && Copied == Original))
                return false;
            auto *Record = Cast<USSStoredData>(UGameplayStatics::CreateSaveGameObject(USSStoredData::StaticClass()));
            Record->Valid = true;
            Record->Payload = TEXT("SS_ACCOUNT_INVALID_DOMAIN_FIXTURE");
            SS::Account Decoded;
            std::string Error;
            if (!TestFalse(TEXT("Fixture payload is rejected by the production account domain codec"),
                           SS::DecodeAccount(TCHAR_TO_UTF8(*Record->Payload), Decoded, Error)) ||
                !TestTrue(TEXT("Seed domain corruption through a real valid Unreal save envelope"),
                          Record->Version == 1 && UGameplayStatics::SaveGameToSlot(Record, TEXT("SS_Account_v1"), 0)))
                return false;
            const auto *Readback = Cast<USSStoredData>(UGameplayStatics::LoadGameFromSlot(TEXT("SS_Account_v1"), 0));
            TestTrue(TEXT("Unreal envelope still loads while its domain payload remains invalid"),
                     Readback && Readback->Version == 1 && Readback->Valid && Readback->Payload == Record->Payload);
            TestTrue(TEXT("Retain exact corrupt bytes for cross-process preservation checks"),
                     FFileHelper::LoadFileToArray(Corrupt, *AccountPath) && Corrupt != Original &&
                         FFileHelper::SaveArrayToFile(Corrupt, *CorruptCopy) &&
                         FFileHelper::LoadFileToArray(Copied, *CorruptCopy) && Copied == Corrupt);
            AddInfo(TEXT(
                "DOMAIN_CORRUPTION_FIXTURE_ONLY: valid Unreal envelope; invalid account text; no binary corruption."));
        }
    }
    else if (Phase == TEXT("RecoverAccount"))
    {
        const auto Seed = Isolation.Read(TEXT("SeedCorruptAccount"), *this);
        if (!Seed)
            return false;
        TArray<uint8> Original, Actual;
        TestTrue(TEXT("Fresh Init sees exactly the manually restored fixture bytes"),
                 FFileHelper::LoadFileToArray(Original, *OriginalCopy) &&
                     FFileHelper::LoadFileToArray(Actual, *AccountPath) && Actual == Original);
        TestEqual(TEXT("Fresh Init restores every original account field"),
                  FString(UTF8_TO_TCHAR(SS::EncodeAccount(Session.account).c_str())),
                  Seed->GetStringField(TEXT("accountPayload")));
        TestEqual(TEXT("Settings survive account corruption and fixture restoration unchanged"),
                  FString(UTF8_TO_TCHAR(SS::EncodeSettings(Session.settings).c_str())),
                  Seed->GetStringField(TEXT("settingsPayload")));
        const auto *Run = Cast<USSStoredData>(UGameplayStatics::LoadGameFromSlot(TEXT("SS_Suspend_v1"), 0));
        TestTrue(TEXT("Fresh restored account can see the exact original unconsumed station checkpoint"),
                 Run && Run->Version == 1 && Run->Valid && Run->Payload == Seed->GetStringField(TEXT("runPayload")) &&
                     Instance->HasSuspendedRun() && !Session.run.active);
        TestTrue(TEXT("Valid account persistence works again after the fresh Init"), Instance->PersistAccount());
        TestTrue(TEXT("Protection validation awards no XP and completes no runs"),
                 Session.account.xp == 0 && Session.account.runs == 0 && Session.account.history.empty());
        CheckNoStagingFiles(*this, Isolation);
    }
    else if (Phase == TEXT("ResumeDeath"))
    {
        TestEqual(TEXT("Fresh Init restores the exact account"),
                  FString(UTF8_TO_TCHAR(SS::EncodeAccount(Session.account).c_str())),
                  Previous->GetStringField(TEXT("accountPayload")));
        TestEqual(TEXT("Fresh Init restores input and settings"),
                  FString(UTF8_TO_TCHAR(SS::EncodeSettings(Session.settings).c_str())),
                  Previous->GetStringField(TEXT("settingsPayload")));
        if (!TestTrue(TEXT("Second process sees the saved station run"), Instance->HasSuspendedRun()))
            return false;
        const FString SuspendPath = Isolation.Saved / TEXT("SaveGames/SS_Suspend_v1.sav");
        TArray<uint8> SuspendBefore;
        if (!TestTrue(TEXT("Read isolated suspension before its failed replacement"),
                      FFileHelper::LoadFileToArray(SuspendBefore, *SuspendPath)))
            return false;
        const auto RunBeforeResume = SS::EncodeRun(Session.run);
        {
            FSSLifecycleSaveLock Lock;
            if (!TestTrue(TEXT("Acquire actual Windows suspension lock without write/delete sharing"),
                          Lock.Open(SuspendPath)) ||
                !TestFalse(TEXT("Resume rejects a real suspension replacement failure"), Instance->ResumeRun()))
                return false;
            TestTrue(TEXT("Resume failure reports the replacement error"),
                     Instance->LastSaveError.Contains(TEXT("Save replacement failed")));
            TestTrue(TEXT("Failed resume never exposes or mutates the candidate run"),
                     !Session.run.active && SS::EncodeRun(Session.run) == RunBeforeResume);
            TArray<uint8> SuspendAfter;
            TestTrue(TEXT("Failed resume preserves every byte of the previous checkpoint"),
                     FFileHelper::LoadFileToArray(SuspendAfter, *SuspendPath) && SuspendAfter == SuspendBefore);
            TestTrue(TEXT("Unconsumed checkpoint remains available after rejected replacement"),
                     Instance->HasSuspendedRun());
            if (!CheckNoStagingFiles(*this, Isolation))
                return false;
        }
        if (!TestTrue(TEXT("Resume retry after releasing the lock restores and consumes the suspension"),
                      Instance->ResumeRun()))
            return false;
        TestTrue(TEXT("Successful resume retry clears the storage error"), Instance->LastSaveError.IsEmpty());
        TestEqual(TEXT("Every suspended run field survived process restart"),
                  FString(UTF8_TO_TCHAR(SS::EncodeRun(Session.run).c_str())),
                  Previous->GetStringField(TEXT("runPayload")));
        if (!CheckConsumed(*this, Instance))
            return false;
        TestFalse(TEXT("A second resume cannot reuse the checkpoint"), Instance->ResumeRun());
        TestTrue(TEXT("Resume rejection leaves the restored run active"),
                 Session.run.active && Session.run.id == RunId);
        if (!TestTrue(TEXT("Resumed station run can launch"), Session.LaunchFromStation()))
            return false;
        Session.ApplyDamage(100000.0);
        TestTrue(TEXT("Lethal damage ends the resumed run"),
                 !Session.run.active && Session.run.phase == SS::Phase::Dead);
        TestEqual(TEXT("Five completed waves and 100 kills award XP once"), Session.account.xp, std::int64_t(475));
        TestTrue(TEXT("Death unlocks both starting sidegrades"),
                 Session.account.HeavyCannonUnlocked() && Session.account.AgileShipUnlocked());
        const auto AccountAfterDeath = SS::EncodeAccount(Session.account);
        TArray<uint8> AccountBefore;
        if (!TestTrue(TEXT("Read isolated account before its failed replacement"),
                      FFileHelper::LoadFileToArray(AccountBefore, *AccountPath)))
            return false;
        {
            FSSLifecycleSaveLock Lock;
            if (!TestTrue(TEXT("Acquire actual Windows account lock without write/delete sharing"),
                          Lock.Open(AccountPath)) ||
                !TestFalse(TEXT("Death persistence rejects a real account replacement failure"),
                           Instance->PersistDeath()))
                return false;
            TestTrue(TEXT("Death save failure reports the replacement error"),
                     Instance->LastSaveError.Contains(TEXT("Save replacement failed")));
            TArray<uint8> AccountAfter;
            TestTrue(TEXT("Failed death save preserves every byte of the previous account"),
                     FFileHelper::LoadFileToArray(AccountAfter, *AccountPath) && AccountAfter == AccountBefore);
            TestTrue(TEXT("Failed save retains the awarded in-memory account for a retry"),
                     SS::EncodeAccount(Session.account) == AccountAfterDeath && Session.account.runs == 1);
            if (!CheckConsumed(*this, Instance) || !CheckNoStagingFiles(*this, Isolation))
                return false;
        }
        if (!TestTrue(TEXT("Death save retry after releasing the lock persists progression and invalidation"),
                      Instance->PersistDeath()))
            return false;
        TestTrue(TEXT("Successful death save retry clears the storage error"), Instance->LastSaveError.IsEmpty());
        Session.EndRun();
        TestTrue(TEXT("PersistDeath retry succeeds"), Instance->PersistDeath());
        TestTrue(TEXT("Death and persistence retry cannot duplicate account XP/history"),
                 SS::EncodeAccount(Session.account) == AccountAfterDeath && Session.account.runs == 1 &&
                     Session.account.history.size() == 1);
        if (!CheckConsumed(*this, Instance))
            return false;
    }
    else
    {
        TestEqual(TEXT("Third-process Init restores the exact post-death account"),
                  FString(UTF8_TO_TCHAR(SS::EncodeAccount(Session.account).c_str())),
                  Previous->GetStringField(TEXT("accountPayload")));
        TestEqual(TEXT("Account XP survived the second process exit exactly once"), Session.account.xp,
                  std::int64_t(475));
        if (!CheckConsumed(*this, Instance))
            return false;
        TestFalse(TEXT("Fresh process cannot resume the dead run"), Instance->ResumeRun());
        TestFalse(TEXT("Rejected checkpoint does not expose an active run"), Session.run.active);
        TestTrue(TEXT("Both unlocks survive fresh Init"),
                 Session.account.HeavyCannonUnlocked() && Session.account.AgileShipUnlocked());
        if (!TestTrue(TEXT("New run accepts the durably unlocked ship and weapon"),
                      Session.StartRun(RunId + "-next", SS::Ship::Agile, SS::Weapon::HeavyCannon)))
            return false;
        TestTrue(TEXT("New run begins in flight with the selected sidegrades"),
                 Session.IsFlying() && Session.run.wave == 1 && Session.run.ship == SS::Ship::Agile &&
                     Session.run.weapon == SS::Weapon::HeavyCannon);
        TestTrue(TEXT("Run-specific upgrades, utility, credits and contract reset"),
                 Session.run.tiers == std::array<int, 5>{{1, 1, 1, 1, 1}} && Session.run.utility == SS::Utility::None &&
                     Session.run.contract == SS::Contract::None && Session.run.credits == 0 &&
                     !Session.run.pendingReward && Session.run.weaponBuffSeconds == 0);
    }
    return Isolation.Receipt(Phase, *this, Instance);
}
#endif
