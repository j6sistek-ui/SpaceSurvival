#include "SSLocalSave.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformFileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Guid.h"
#include "Misc/Paths.h"
#include "PlatformFeatures.h"
#if PLATFORM_WINDOWS
#include "Windows/WindowsHWrapper.h"
#endif

namespace SSLocalSave
{
#if PLATFORM_WINDOWS
namespace
{
FString NativePath(const FString &Path)
{
    FString Full = IFileManager::Get().ConvertToAbsolutePathForExternalAppForWrite(*Path);
    FPaths::CollapseRelativeDirectories(Full);
    Full.ReplaceInline(TEXT("/"), TEXT("\\"));
    if (Full.StartsWith(TEXT("\\\\?\\")))
        return Full;
    return Full.StartsWith(TEXT("\\\\")) ? TEXT("\\\\?\\UNC\\") + Full.Mid(2) : TEXT("\\\\?\\") + Full;
}
} // namespace
#endif

bool Write(const FString &Slot, const TArray<uint8> &Data, FString &Error)
{
#if PLATFORM_WINDOWS
    auto &Features = IPlatformFeaturesModule::Get();
    if (!IsInGameThread() || Features.GetSaveGameSystem() != Features.IPlatformFeaturesModule::GetSaveGameSystem())
    {
        Error = TEXT("The configured save backend is unsupported. Local Windows storage is required.");
        return false;
    }
    if ((Slot != TEXT("SS_Account_v1") && Slot != TEXT("SS_Settings_v1") && Slot != TEXT("SS_Suspend_v1")) ||
        Data.IsEmpty())
    {
        Error = TEXT("Invalid local save request.");
        return false;
    }
    auto &Files = FPlatformFileManager::Get().GetPlatformFile();
    const FString Directory = FPaths::ProjectSavedDir() / TEXT("SaveGames");
    if (!Files.CreateDirectoryTree(*Directory))
    {
        Error = TEXT("Save folder is unavailable. Check disk space and folder access, then retry.");
        return false;
    }
    const FString Destination = Directory / (Slot + TEXT(".sav"));
    const FString Staging = Destination + TEXT(".") + FGuid::NewGuid().ToString(EGuidFormats::Digits) + TEXT(".tmp");
    // Never truncate the live slot. A failed/abandoned temporary file is not a loadable save.
    if (Files.FileExists(*Staging) || Files.DirectoryExists(*Staging))
    {
        Error = TEXT("Could not reserve a temporary save file. Retry the action.");
        return false;
    }
    TUniquePtr<IFileHandle> Handle(Files.OpenWrite(*Staging));
    const bool Written = Handle && Handle->Write(Data.GetData(), Data.Num()) && Handle->Flush(true);
    Handle.Reset();
    TArray<uint8> Verified;
    const bool Ready = Written && FFileHelper::LoadFileToArray(Verified, *Staging) && Verified == Data;
    if (!Ready)
    {
        Files.DeleteFile(*Staging);
        Error = TEXT("Save staging or verification failed. Previous save was not replaced; retry after checking "
                     "disk space and folder access.");
        return false;
    }
    // IFileManager::Move deletes its destination first. Use one same-volume replacement instead;
    // omitting COPY_ALLOWED forbids a copy/delete fallback. Bytes were flushed and verified above.
    const bool Committed = !!MoveFileExW(*NativePath(Staging), *NativePath(Destination),
                                         MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH);
    if (!Committed)
    {
        const uint32 Code = GetLastError();
        Files.DeleteFile(*Staging);
        Error = FString::Printf(TEXT("Save replacement failed (Windows %u). Close any app holding the save file "
                                     "and retry. The action has not been confirmed."),
                                Code);
        return false;
    }
    // A post-commit read can fail transiently after a suspension has already been consumed.
    // The verified staging bytes and successful replacement are the commit acknowledgement.
    Error.Empty();
    return true;
#else
    Error = TEXT("Local save replacement is implemented for Windows only.");
    return false;
#endif
}
} // namespace SSLocalSave
