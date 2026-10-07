#include "SSRenderedViewDiagnostic.h"

#if WITH_EDITOR
#include "Containers/Queue.h"
#include "Containers/Ticker.h"
#include "Containers/UnrealString.h"
#include "CoreGlobals.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "FXRenderingUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformTime.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "RenderingThread.h"
#include "SceneView.h"
#include "SceneViewExtension.h"
#include "Slate/SceneViewport.h"
#include "UnrealClient.h"
#include <atomic>

DEFINE_LOG_CATEGORY_STATIC(LogSSRenderedViewDiagnostic, Log, All);

namespace
{
constexpr int32 MaxSamples = 512;
constexpr int32 MaxSteadySamplesPerStage = 20;
constexpr int32 StageCount = 4;
constexpr double MaxSeconds = 90.;

struct FRequestData
{
    int32 Stage = 0;
    uint32 ExpectedOwner = 0;
    uint32 CurrentOwner = 0;
    uint32 RequestedX = 0;
    uint32 RequestedY = 0;
    FIntPoint ViewportSize = FIntPoint::ZeroValue;
    bool bHighRes = false;
    bool bShotRequested = false;
};

struct FRequestSnapshot : ISceneViewFamilyExtentionData
{
    inline static const TCHAR *GSubclassIdentifier = TEXT("SSRenderedViewDiagnostic1");
    virtual const TCHAR *GetSubclassIdentifier() const override
    {
        return GSubclassIdentifier;
    }
    FRequestData Data;
};

struct FSample
{
    uint32 Frame = 0;
    uint64 FrameCounter = 0;
    int32 Stage = 0;
    uint32 ViewOwner = 0;
    FRequestData Request;
    FIntRect Raw;
    FIntRect Output;
    FIntPoint TargetSize = FIntPoint::ZeroValue;
    FVector Origin = FVector::ZeroVector;
    FRotator Rotation = FRotator::ZeroRotator;
    FVector2D Jitter = FVector2D::ZeroVector;
    float Fov = 0.f;
    float SecondaryFraction = 0.f;
    int32 AA = 0;
    int32 PrimaryMethod = 0;
    bool bAA = false;
    bool bTemporalAA = false;
    bool bScreenPercentage = false;
    bool bCameraCut = false;
    bool bState = false;
};

struct FBuffer
{
    TQueue<FSample, EQueueMode::Mpsc> Queue;
    std::atomic<bool> Recording{true};
    std::atomic<int32> SampleCount{0};
    std::atomic<int32> InvalidCount{0};
    std::atomic<int32> SteadyCount[StageCount]{};
    // Only the game thread accesses Stage and ExpectedOwner. Each view family owns its immutable snapshot.
    int32 Stage = 0;
    uint32 ExpectedOwner = 0;
};

class FObserver final : public FWorldSceneViewExtension
{
public:
    FObserver(const FAutoRegister &AutoRegister, UWorld *World,
              const TSharedRef<FBuffer, ESPMode::ThreadSafe> &InBuffer)
        : FWorldSceneViewExtension(AutoRegister, World), Buffer(InBuffer)
    {
    }

    virtual void BeginRenderViewFamily(FSceneViewFamily &Family) override
    {
        check(IsInGameThread());
        if (!Buffer->Recording.load())
            return;
        FRequestData &Snapshot = Family.GetOrCreateExtentionData<FRequestSnapshot>()->Data;
        Snapshot.Stage = Buffer->Stage;
        Snapshot.ExpectedOwner = Buffer->ExpectedOwner;
        Snapshot.bHighRes = GIsHighResScreenshot;
        Snapshot.RequestedX = GScreenshotResolutionX;
        Snapshot.RequestedY = GScreenshotResolutionY;
        Snapshot.bShotRequested = FScreenshotRequest::IsScreenshotRequested();
        if (UWorld *ActualWorld = GetWorld())
        {
            if (APlayerController *Player = UGameplayStatics::GetPlayerController(ActualWorld, 0))
                if (const AActor *Target = Player->GetViewTarget())
                    Snapshot.CurrentOwner = Target->GetUniqueID();
            if (UGameViewportClient *Client = ActualWorld->GetGameViewport())
                if (Client->Viewport)
                    Snapshot.ViewportSize = Client->Viewport->GetSizeXY();
        }
    }

    virtual void PostRenderView_RenderThread(FRDGBuilder &, FSceneView &View) override
    {
        if (!Buffer->Recording.load() || !View.Family || !View.bIsGameView || !View.bIsViewInfo ||
            View.bIsSceneCapture || View.bIsReflectionCapture || View.bIsPlanarReflection || View.PlayerIndex != 0)
            return;
        const FRequestSnapshot *Snapshot = View.Family->GetExtentionData<FRequestSnapshot>();
        if (!Snapshot)
            return;
        const FRequestData &Request = Snapshot->Data;
        // At most 60 steady samples across control, ordinary and after stages; high-res/request draws retain tiles.
        if (!Request.bHighRes && !Request.bShotRequested)
        {
            if (Request.Stage == 2 || View.Family->FrameCounter % 4 != 0 ||
                Buffer->SteadyCount[Request.Stage].fetch_add(1) >= MaxSteadySamplesPerStage)
                return;
        }
        const FIntRect Raw = UE::FXRenderingUtils::GetRawViewRectUnsafe(View);
        if (Raw.Width() <= 0 || Raw.Height() <= 0 || View.UnscaledViewRect.Width() <= 0 ||
            View.UnscaledViewRect.Height() <= 0 || !FMath::IsFinite(View.Family->SecondaryViewFraction) ||
            View.Family->SecondaryViewFraction <= 0.f)
        {
            Buffer->InvalidCount.fetch_add(1);
            return;
        }
        const int32 Index = Buffer->SampleCount.fetch_add(1);
        if (Index >= MaxSamples)
        {
            Buffer->Recording.store(false);
            return;
        }
        FSample Sample;
        Sample.Frame = View.Family->FrameNumber;
        Sample.FrameCounter = View.Family->FrameCounter;
        Sample.Stage = Request.Stage;
        Sample.ViewOwner = View.ViewActor.ActorUniqueId;
        Sample.Request = Request;
        Sample.Raw = Raw;
        Sample.Output = View.UnscaledViewRect;
        Sample.TargetSize = View.Family->RenderTarget ? View.Family->RenderTarget->GetSizeXY() : FIntPoint::ZeroValue;
        Sample.Origin = View.ViewMatrices.GetViewOrigin();
        Sample.Rotation = View.ViewRotation;
        Sample.Jitter = View.ViewMatrices.GetTemporalAAJitter();
        Sample.Fov = View.FOV;
        Sample.SecondaryFraction = View.Family->SecondaryViewFraction;
        Sample.AA = static_cast<int32>(View.AntiAliasingMethod);
        Sample.PrimaryMethod = static_cast<int32>(View.PrimaryScreenPercentageMethod);
        Sample.bAA = View.Family->EngineShowFlags.AntiAliasing;
        Sample.bTemporalAA = View.Family->EngineShowFlags.TemporalAA;
        Sample.bScreenPercentage = View.Family->EngineShowFlags.ScreenPercentage;
        Sample.bCameraCut = View.bCameraCut;
        Sample.bState = View.State != nullptr;
        Buffer->Queue.Enqueue(MoveTemp(Sample));
    }

private:
    TSharedRef<FBuffer, ESPMode::ThreadSafe> Buffer;
};

struct FSession
{
    TWeakObjectPtr<UWorld> World;
    TSharedRef<FBuffer, ESPMode::ThreadSafe> Buffer = MakeShared<FBuffer, ESPMode::ThreadSafe>();
    TSharedPtr<FObserver, ESPMode::ThreadSafe> Observer;
    FTSTicker::FDelegateHandle Ticker;
    FDelegateHandle Cleanup;
    double Started = 0.;
    int32 Logged = 0;
    TWeakObjectPtr<UGameViewportClient> SizedClient;
    FSceneViewport *SizedViewport = nullptr;
    FIntPoint OriginalSize = FIntPoint::ZeroValue;
    bool bOriginalFixed = false;
    bool bSizeChanged = false;
};

TUniquePtr<FSession> Session;
TUniquePtr<FAutoConsoleCommandWithWorldAndArgs> BeginCommand;
TUniquePtr<FAutoConsoleCommandWithWorldAndArgs> StageCommand;
TUniquePtr<FAutoConsoleCommandWithWorldAndArgs> EndCommand;
TUniquePtr<FAutoConsoleCommandWithWorldAndArgs> SizeCommand;
TUniquePtr<FAutoConsoleCommandWithWorldAndArgs> RestoreSizeCommand;

bool RestoreViewportSize()
{
    check(IsInGameThread());
    if (!Session || !Session->bSizeChanged)
        return true;
    UWorld *OwningWorld = Session->World.Get();
    UGameViewportClient *Client = Session->SizedClient.Get();
    if (!OwningWorld || OwningWorld->WorldType != EWorldType::PIE || !Client ||
        OwningWorld->GetGameViewport() != Client || Client->GetGameViewport() != Session->SizedViewport ||
        Client->Viewport != Session->SizedViewport)
    {
        UE_LOG(LogSSRenderedViewDiagnostic, Error,
               TEXT("SSVIEWSIZE2 restore rejected: exact owning PIE client/viewport no longer live"));
        return false;
    }
    FSceneViewport *ActualViewport = Client->GetGameViewport();
    if (Session->bOriginalFixed)
        ActualViewport->SetFixedViewportSize(Session->OriginalSize.X, Session->OriginalSize.Y);
    else
    {
        // Installed implementation is unavailable; verify this public API's native unfix behavior below.
        ActualViewport->SetFixedViewportSize(0, 0);
        ActualViewport->SetViewportSize(Session->OriginalSize.X, Session->OriginalSize.Y);
    }
    const FIntPoint ActualSize = ActualViewport->GetSizeXY();
    const bool bActualFixed = ActualViewport->HasFixedSize();
    const bool bRestored = ActualSize == Session->OriginalSize && bActualFixed == Session->bOriginalFixed;
    UE_LOG(LogSSRenderedViewDiagnostic, Log,
           TEXT("SSVIEWSIZE2 restore original=%d,%d original_fixed=%d actual=%d,%d actual_fixed=%d verified=%d"),
           Session->OriginalSize.X, Session->OriginalSize.Y, Session->bOriginalFixed, ActualSize.X, ActualSize.Y,
           bActualFixed, bRestored);
    if (bRestored)
        Session->bSizeChanged = false;
    else
        UE_LOG(LogSSRenderedViewDiagnostic, Error,
               TEXT("SSVIEWSIZE2 native original size/fixed-state restoration failed"));
    return bRestored;
}

void ResizeOwnedViewport(const TArray<FString> &Args, UWorld *World)
{
    check(IsInGameThread());
    if (!Args.IsEmpty() || !SizeCommand || !Session || Session->World.Get() != World || !World ||
        World->WorldType != EWorldType::PIE || Session->bSizeChanged)
    {
        UE_LOG(LogSSRenderedViewDiagnostic, Error,
               TEXT("SSVIEWSIZE2 resize rejected: require inactive resize in exact owning PIE session and no args"));
        return;
    }
    UGameViewportClient *Client = World->GetGameViewport();
    FSceneViewport *ActualViewport = Client ? Client->GetGameViewport() : nullptr;
    if (!ActualViewport || Client->Viewport != ActualViewport || ActualViewport->GetSizeXY().GetMin() <= 0)
    {
        UE_LOG(LogSSRenderedViewDiagnostic, Error, TEXT("SSVIEWSIZE2 resize rejected: no exact typed game viewport"));
        return;
    }
    Session->SizedClient = Client;
    Session->SizedViewport = ActualViewport;
    Session->OriginalSize = ActualViewport->GetSizeXY();
    Session->bOriginalFixed = ActualViewport->HasFixedSize();
    Session->bSizeChanged = true;
    ActualViewport->SetFixedViewportSize(1600, 900);
    const FIntPoint ActualSize = ActualViewport->GetSizeXY();
    UE_LOG(LogSSRenderedViewDiagnostic, Log,
           TEXT("SSVIEWSIZE2 request original=%d,%d original_fixed=%d requested=1600,900 actual=%d,%d actual_fixed=%d"),
           Session->OriginalSize.X, Session->OriginalSize.Y, Session->bOriginalFixed, ActualSize.X, ActualSize.Y,
           ActualViewport->HasFixedSize());
}

void RestoreOwnedViewport(const TArray<FString> &Args, UWorld *World)
{
    if (Args.IsEmpty() && Session && Session->World.Get() == World)
        RestoreViewportSize();
    else
        UE_LOG(LogSSRenderedViewDiagnostic, Error, TEXT("SSVIEWSIZE2 restore rejected: require exact owning session"));
}

void Drain()
{
    check(IsInGameThread());
    if (!Session)
        return;
    FSample Sample;
    while (Session->Buffer->Queue.Dequeue(Sample))
    {
        ++Session->Logged;
        UE_LOG(LogSSRenderedViewDiagnostic, Log,
               TEXT("SSVIEW1 frame=%u counter=%llu stage=%d owner=%u expected_owner=%u current_owner=%u highres=%d "
                    "shot=%d requested=%u,%u "
                    "viewport=%d,%d target=%d,%d raw=%d,%d,%d,%d output=%d,%d,%d,%d fraction=%.6f,%.6f secondary=%.6f "
                    "aa=%d aa_flag=%d temporal_flag=%d screen_flag=%d primary=%d cut=%d state=%d jitter=%.9f,%.9f "
                    "origin=%.3f,%.3f,%.3f rotation=%.3f,%.3f,%.3f fov=%.3f"),
               Sample.Frame, static_cast<unsigned long long>(Sample.FrameCounter), Sample.Stage, Sample.ViewOwner,
               Sample.Request.ExpectedOwner, Sample.Request.CurrentOwner, Sample.Request.bHighRes,
               Sample.Request.bShotRequested, Sample.Request.RequestedX, Sample.Request.RequestedY,
               Sample.Request.ViewportSize.X, Sample.Request.ViewportSize.Y, Sample.TargetSize.X, Sample.TargetSize.Y,
               Sample.Raw.Min.X, Sample.Raw.Min.Y, Sample.Raw.Max.X, Sample.Raw.Max.Y, Sample.Output.Min.X,
               Sample.Output.Min.Y, Sample.Output.Max.X, Sample.Output.Max.Y,
               double(Sample.Raw.Width()) / Sample.Output.Width(), double(Sample.Raw.Height()) / Sample.Output.Height(),
               double(Sample.SecondaryFraction), Sample.AA, Sample.bAA, Sample.bTemporalAA, Sample.bScreenPercentage,
               Sample.PrimaryMethod, Sample.bCameraCut, Sample.bState, Sample.Jitter.X, Sample.Jitter.Y,
               Sample.Origin.X, Sample.Origin.Y, Sample.Origin.Z, Sample.Rotation.Pitch, Sample.Rotation.Yaw,
               Sample.Rotation.Roll, double(Sample.Fov));
    }
}

void Stop(const TCHAR *Reason, bool bFromTicker = false)
{
    check(IsInGameThread());
    if (!Session)
        return;
    Session->Buffer->Recording.store(false);
    RestoreViewportSize();
    Session->Observer.Reset();
    // Frame references can outlive the extension owner; drain before releasing its session/queue.
    FlushRenderingCommands();
    Drain();
    // RemoveTicker may wait for a running delegate. This callback removes itself by returning false.
    if (!bFromTicker)
        FTSTicker::RemoveTicker(Session->Ticker);
    FWorldDelegates::OnWorldCleanup.Remove(Session->Cleanup);
    UE_LOG(LogSSRenderedViewDiagnostic, Log, TEXT("SSVIEW1 end reason=%s logged=%d invalid=%d limit=%d"), Reason,
           Session->Logged, Session->Buffer->InvalidCount.load(), MaxSamples);
    Session.Reset();
}

void Begin(const TArray<FString> &Args, UWorld *World)
{
    check(IsInGameThread());
    if (!Args.IsEmpty() || Session || !World || World->WorldType != EWorldType::PIE)
    {
        UE_LOG(LogSSRenderedViewDiagnostic, Error,
               TEXT("SSVIEW1 begin rejected: require one inactive actual PIE session and no args"));
        return;
    }
    APlayerController *Player = UGameplayStatics::GetPlayerController(World, 0);
    AActor *Target = Player ? Player->GetViewTarget() : nullptr;
    if (!Target || !World->GetGameViewport() || !World->GetGameViewport()->Viewport)
    {
        UE_LOG(LogSSRenderedViewDiagnostic, Error,
               TEXT("SSVIEW1 begin rejected: no actual player camera/game viewport"));
        return;
    }
    Session = MakeUnique<FSession>();
    Session->World = World;
    Session->Buffer->ExpectedOwner = Target->GetUniqueID();
    Session->Started = FPlatformTime::Seconds();
    Session->Observer = FSceneViewExtensions::NewExtension<FObserver>(World, Session->Buffer);
    Session->Cleanup = FWorldDelegates::OnWorldCleanup.AddLambda(
        [](UWorld *CleaningWorld, bool, bool)
        {
            if (Session && Session->World.Get() == CleaningWorld)
                Stop(TEXT("world_cleanup"));
        });
    Session->Ticker = FTSTicker::GetCoreTicker().AddTicker(
        FTickerDelegate::CreateLambda(
            [](float)
            {
                if (!Session)
                    return false;
                Drain();
                if (!Session->World.IsValid() || FPlatformTime::Seconds() - Session->Started >= MaxSeconds ||
                    !Session->Buffer->Recording.load())
                {
                    Stop(TEXT("bounded_auto_stop"), true);
                    return false;
                }
                return true;
            }),
        .1f);
    UE_LOG(LogSSRenderedViewDiagnostic, Log, TEXT("SSVIEW1 begin world=%s expected_owner=%u max_seconds=%.0f limit=%d"),
           *World->GetPathName(), Session->Buffer->ExpectedOwner, MaxSeconds, MaxSamples);
}

void Stage(const TArray<FString> &Args, UWorld *World)
{
    check(IsInGameThread());
    int32 Value = -1;
    if (!Session || Session->World.Get() != World || Args.Num() != 1 || !LexTryParseString(Value, *Args[0]) ||
        Value < 0 || Value >= StageCount)
    {
        UE_LOG(LogSSRenderedViewDiagnostic, Error,
               TEXT("SSVIEW1 stage rejected: require owning PIE world and integer0..3"));
        return;
    }
    Session->Buffer->Stage = Value;
    UE_LOG(LogSSRenderedViewDiagnostic, Log, TEXT("SSVIEW1 stage=%d"), Value);
}

void End(const TArray<FString> &Args, UWorld *World)
{
    if (Args.IsEmpty() && Session && Session->World.Get() == World)
        Stop(TEXT("explicit_end"));
}
} // namespace

namespace SSRenderedViewDiagnostic
{
void Initialize()
{
    const bool bFullSize = FParse::Param(FCommandLine::Get(), TEXT("SSRenderedViewViewport2"));
    if ((!FParse::Param(FCommandLine::Get(), TEXT("SSRenderedViewDiagnostic1")) && !bFullSize) ||
        !FParse::Param(FCommandLine::Get(), TEXT("renderoffscreen")))
        return;
    BeginCommand = MakeUnique<FAutoConsoleCommandWithWorldAndArgs>(
        TEXT("SS.RenderedView.Begin"), TEXT("Opt-in isolated PIE renderer observation; no settings writes."),
        FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(Begin));
    StageCommand = MakeUnique<FAutoConsoleCommandWithWorldAndArgs>(
        TEXT("SS.RenderedView.Stage"), TEXT("Numeric observation phase:0control,1ordinary,2highres,3after."),
        FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(Stage));
    EndCommand = MakeUnique<FAutoConsoleCommandWithWorldAndArgs>(
        TEXT("SS.RenderedView.End"), TEXT("Drain and release isolated renderer observation."),
        FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(End));
    if (bFullSize)
    {
        SizeCommand = MakeUnique<FAutoConsoleCommandWithWorldAndArgs>(
            TEXT("SS.RenderedView.Size"), TEXT("Opt-in owning PIE viewport only: temporary fixed1600x900."),
            FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(ResizeOwnedViewport));
        RestoreSizeCommand = MakeUnique<FAutoConsoleCommandWithWorldAndArgs>(
            TEXT("SS.RenderedView.RestoreSize"),
            TEXT("Restore and verify the temporary viewport's original size/fixed state."),
            FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(RestoreOwnedViewport));
    }
}

void Shutdown()
{
    Stop(TEXT("module_shutdown"));
    RestoreSizeCommand.Reset();
    SizeCommand.Reset();
    EndCommand.Reset();
    StageCommand.Reset();
    BeginCommand.Reset();
}
} // namespace SSRenderedViewDiagnostic
#endif
