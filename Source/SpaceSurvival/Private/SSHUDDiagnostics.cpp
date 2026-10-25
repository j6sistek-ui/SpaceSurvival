#include "SSHUD.h"
#include "SSGameInstance.h"
#include "SSGraphicsSettings.h"
#include "SSNpcTalk.h"
#include "DynamicRHI.h"
#include "HAL/PlatformMemory.h"
#include "HAL/PlatformTime.h"
#include "RenderTimer.h"

void ASSHUD::ResetDiagnostics()
{
    DiagnosticStart = DiagnosticLastFrame = DiagnosticGameMs = DiagnosticRenderMs = DiagnosticGpuMs = 0;
    DiagnosticFrames = DiagnosticGpuFrames = 0;
    DiagnosticLines.Reset();
}

void ASSHUD::DrawDiagnostics(const USSGameInstance &Instance)
{
    const double Now = FPlatformTime::Seconds();
    // A hidden HUD or a long editor stall must not leave old numbers displayed as current.
    if (DiagnosticLastFrame > 0 && Now - DiagnosticLastFrame > 2.0)
        ResetDiagnostics();
    DiagnosticLastFrame = Now;
    if (DiagnosticStart == 0)
        DiagnosticStart = Now;
    else
    {
        ++DiagnosticFrames;
        DiagnosticGameMs += FPlatformTime::ToMilliseconds(GGameThreadTime);
        DiagnosticRenderMs += FPlatformTime::ToMilliseconds(GRenderThreadTime);
        const uint32 GpuCycles = GDynamicRHI ? RHIGetGPUFrameCycles() : 0;
        if (GpuCycles > 0)
        {
            DiagnosticGpuMs += FPlatformTime::ToMilliseconds(GpuCycles);
            ++DiagnosticGpuFrames;
        }
    }
    const double Elapsed = Now - DiagnosticStart;
    if (Elapsed >= .75 && DiagnosticFrames > 0)
    {
        DiagnosticLines.Reset();
        DiagnosticLines.Add(FString::Printf(TEXT("Rendered %.0f FPS / %.1f ms frame"), DiagnosticFrames / Elapsed,
                                            Elapsed * 1000 / DiagnosticFrames));
        const FString GameTime = DiagnosticGameMs > 0
                                     ? FString::Printf(TEXT("%.1f ms"), DiagnosticGameMs / DiagnosticFrames)
                                     : TEXT("unavailable");
        const FString RenderTime = DiagnosticRenderMs > 0
                                       ? FString::Printf(TEXT("%.1f ms"), DiagnosticRenderMs / DiagnosticFrames)
                                       : TEXT("unavailable");
        DiagnosticLines.Add(FString::Printf(TEXT("Game %s / Render %s"), *GameTime, *RenderTime));
        DiagnosticLines.Add(DiagnosticGpuFrames > 0
                                ? FString::Printf(TEXT("GPU %.1f ms"), DiagnosticGpuMs / DiagnosticGpuFrames)
                                : TEXT("GPU timing unavailable"));
        const auto Memory = FPlatformMemory::GetStats();
        const auto NVIDIA = SSGraphics::Telemetry();
        DiagnosticLines.Add(NVIDIA.DisplayedFPS > 0 && FMath::IsFinite(NVIDIA.DisplayedFPS)
                                ? FString::Printf(TEXT("Displayed %.0f FPS / FG %s"), NVIDIA.DisplayedFPS,
                                                  NVIDIA.FrameGenerationActive ? TEXT("active") : TEXT("inactive"))
                                : TEXT("Displayed FPS unavailable"));
        DiagnosticLines.Add(NVIDIA.LatencyMs > 0 && FMath::IsFinite(NVIDIA.LatencyMs)
                                ? FString::Printf(TEXT("Game-to-render latency %.1f ms"), NVIDIA.LatencyMs)
                                : TEXT("Game-to-render latency unavailable"));
        DiagnosticLines.Add(FString::Printf(TEXT("Process CPU %.1f%%  /  RAM %.2f GB"),
                                            FPlatformTime::GetCPUTime().CPUTimePct,
                                            double(Memory.UsedPhysical) / (1024 * 1024 * 1024)));
        const int64 VideoBudget = SSNpcTalk::FreeVideoMemoryBytes();
        DiagnosticLines.Add(VideoBudget >= 0 ? FString::Printf(TEXT("VRAM budget headroom %.2f GB"),
                                                               double(VideoBudget) / (1024 * 1024 * 1024))
                                             : TEXT("VRAM budget unavailable"));
        if (const auto *Talk = Instance.GetSubsystem<USSNpcTalkSubsystem>())
        {
            const auto Status = Talk->Diagnostics();
            const TCHAR *Phase = Status.Phase == ESSTalkPhase::Listening      ? TEXT("listening")
                                 : Status.Phase == ESSTalkPhase::Transcribing ? TEXT("transcribing")
                                 : Status.Phase == ESSTalkPhase::Thinking     ? TEXT("thinking")
                                                                              : TEXT("idle");
            DiagnosticLines.Add(FString::Printf(TEXT("Talk: %s / %s"),
                                                !Status.Installed ? TEXT("not installed")
                                                : Status.Enabled  ? TEXT("enabled")
                                                                  : TEXT("disabled"),
                                                Phase));
            DiagnosticLines.Add(FString::Printf(TEXT("LLM %s  /  STT %s"),
                                                Status.LlamaRunning ? TEXT("running") : TEXT("stopped"),
                                                Status.WhisperRunning ? TEXT("running") : TEXT("stopped")));
            if (Status.Phase == ESSTalkPhase::Thinking)
                DiagnosticLines.Add(FString::Printf(TEXT("Reply waiting %.0f s"), Status.RequestSeconds));
            const TCHAR *Voice = !Status.VoiceInstalled ? TEXT("not installed")
                                 : !Status.VoiceEnabled ? TEXT("disabled")
                                 : !Status.VoiceRunning ? TEXT("stopped")
                                 : Status.VoiceReady    ? TEXT("ready")
                                                        : TEXT("warming");
            DiagnosticLines.Add(FString::Printf(TEXT("Voice: %s  /  queued %d"), Voice, Status.VoiceQueue));
            DiagnosticLines.Add(
                FString::Printf(TEXT("Voice restarts %d  /  failures %d"), Status.VoiceRestarts, Status.VoiceFailures));
            DiagnosticLines.Add(Status.TalkError ? TEXT("Talk error: present (see conversation)")
                                                 : TEXT("Talk error: none"));
        }
        else
            DiagnosticLines.Add(TEXT("Local AI status unavailable"));
        DiagnosticStart = Now;
        DiagnosticFrames = DiagnosticGpuFrames = 0;
        DiagnosticGameMs = DiagnosticRenderMs = DiagnosticGpuMs = 0;
    }

    const FLinearColor Cyan = FLinearColor::FromSRGBColor(FColor(154, 227, 240));
    const FLinearColor Muted = FLinearColor::FromSRGBColor(FColor(172, 193, 216));
    const float TextScale = FMath::Clamp(float(Instance.Session.settings.uiScale), .8f, 1.4f);
    const float X = 64, Y = 290, Width = 500 * TextScale;
    const float LineHeight = FMath::Min(30.f * TextScale, 650.f / FMath::Max(1, DiagnosticLines.Num()));
    const FBox2D Bounds = RefreshBounds(X, Y, Width, 80 + FMath::Max(1, DiagnosticLines.Num()) * LineHeight);
    DrawRect(FLinearColor(.012f, .025f, .04f, .92f), Bounds.Min.X, Bounds.Min.Y, Bounds.GetSize().X,
             Bounds.GetSize().Y);
    DrawRect(Cyan, Bounds.Min.X, Bounds.Min.Y, 2 * RefreshScale, Bounds.GetSize().Y);
    RefreshText(TEXT("SYSTEM DIAGNOSTICS"), X + 18, Y + 12, 22, Cyan);
    float RowY = Y + 49;
    if (DiagnosticLines.IsEmpty())
        RefreshText(TEXT("Sampling..."), X + 18, RowY, 21, Muted);
    for (const FString &Line : DiagnosticLines)
    {
        RefreshText(Line, X + 18, RowY, FMath::Min(21.f, LineHeight / (1.3f * TextScale)), Muted);
        RowY += LineHeight;
    }
    RefreshText(TEXT("Graphics settings / Diagnostics"), X + 18, RowY + 7, 16, Muted);
}
