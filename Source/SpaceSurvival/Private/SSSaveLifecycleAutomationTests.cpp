#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
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
    const FString Prior = Phase == TEXT("Suspend")       ? TEXT("Preflight")
                          : Phase == TEXT("ResumeDeath") ? TEXT("Suspend")
                          : Phase == TEXT("FreshStart")  ? TEXT("ResumeDeath")
                                                         : TEXT("");
    if (!TestFalse(TEXT("Lifecycle phase is recognized"), Prior.IsEmpty()))
        return false;
    auto Previous = Isolation.Read(Prior, *this);
    if (!Previous)
        return false;
    FSSLifecycleInstance Fixture;
    Fixture.Initialize();
    auto *Instance = Fixture.Instance;
    auto &Session = Instance->Session;
    if (!TestFalse(TEXT("Isolated account initializes without a storage error"), Instance->AccountStorageBlocked))
        return false;
    const std::string RunId = "lifecycle-" + std::string(TCHAR_TO_UTF8(*Isolation.Token));
    if (Phase == TEXT("Suspend"))
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
        if (!TestTrue(TEXT("Real SuspendRun persists all three domains"), Instance->SuspendRun()))
            return false;
        TestTrue(TEXT("Written station run is available to resume"), Instance->HasSuspendedRun());
        TestEqual(TEXT("XP remains unawarded while suspended"), Session.account.xp, std::int64_t(0));
    }
    else if (Phase == TEXT("ResumeDeath"))
    {
        TestEqual(TEXT("Fresh Init restores the exact account"),
                  FString(UTF8_TO_TCHAR(SS::EncodeAccount(Session.account).c_str())),
                  Previous->GetStringField(TEXT("accountPayload")));
        TestEqual(TEXT("Fresh Init restores input and settings"),
                  FString(UTF8_TO_TCHAR(SS::EncodeSettings(Session.settings).c_str())),
                  Previous->GetStringField(TEXT("settingsPayload")));
        if (!TestTrue(TEXT("Second process sees the saved station run"), Instance->HasSuspendedRun()) ||
            !TestTrue(TEXT("Real ResumeRun restores and consumes the suspension"), Instance->ResumeRun()))
            return false;
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
        if (!TestTrue(TEXT("Real PersistDeath durably saves progression and invalidation"), Instance->PersistDeath()))
            return false;
        const auto AccountAfterDeath = SS::EncodeAccount(Session.account);
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
