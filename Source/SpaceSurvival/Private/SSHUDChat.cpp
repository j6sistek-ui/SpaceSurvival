#include "SSHUD.h"
#include "SSGameMode.h"
#include "CanvasItem.h"
#include "Engine/Canvas.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"

void ASSHUD::DrawChatPanel(const ASSGameMode &Mode)
{
    const float Now = GetWorld()->GetTimeSeconds();
    if (Mode.TalkStatus.IsEmpty() &&
        (Mode.ChatLines.IsEmpty() || (!Mode.IsTalkEngaged() && Now - Mode.ChatLines.Last().ShownAt > 24.f)))
        return;
    BeginRefreshLayout();
    // Same safe 1920x1080 canvas and frame as the radar/menu. The radar legend ends at y=544.
    constexpr float PanelX = 1395.f, PanelY = 560.f, PanelW = 458.f, PanelH = 420.f;
    const FBox2D Bounds = RefreshBounds(PanelX, PanelY, PanelW, PanelH);
    DrawRect(FLinearColor(.008f, .02f, .035f, .90f), Bounds.Min.X, Bounds.Min.Y, Bounds.GetSize().X,
             Bounds.GetSize().Y);
    if (auto *Frame = RefreshTexture(TEXT("Frame")))
    {
        constexpr float Corner = 32.f, SourceCorner = 128.f;
        const float X[] = {PanelX, PanelX + Corner, PanelX + PanelW - Corner, PanelX + PanelW};
        const float Y[] = {PanelY, PanelY + Corner, PanelY + PanelH - Corner, PanelY + PanelH};
        const float U[] = {0, SourceCorner / Frame->GetSizeX(), 1.f - SourceCorner / Frame->GetSizeX(), 1};
        const float V[] = {0, SourceCorner / Frame->GetSizeY(), 1.f - SourceCorner / Frame->GetSizeY(), 1};
        for (int32 Row = 0; Row < 3; ++Row)
            for (int32 Col = 0; Col < 3; ++Col)
            {
                FCanvasTileItem Item(RefreshOrigin + FVector2D(X[Col], Y[Row]) * RefreshScale, Frame->GetResource(),
                                     FVector2D(X[Col + 1] - X[Col], Y[Row + 1] - Y[Row]) * RefreshScale,
                                     FVector2D(U[Col], V[Row]), FVector2D(U[Col + 1], V[Row + 1]), FLinearColor::White);
                Item.BlendMode = SE_BLEND_Translucent;
                Canvas->DrawItem(Item);
            }
    }
    const FLinearColor Cyan = FLinearColor::FromSRGBColor(FColor(154, 227, 240));
    RefreshText(TEXT("CONVERSATION"), PanelX + 24, PanelY + 20, 21, Cyan);
    const float X = Bounds.Min.X + 24.f * RefreshScale;
    const float Width = Bounds.GetSize().X - 48.f * RefreshScale;
    const float Top = Bounds.Min.Y + 62.f * RefreshScale;
    const float Bottom = Bounds.Max.Y - 24.f * RefreshScale;
    const float LineH = MeasureStationText(TEXT("Ag"), .95f).Y + 5.f * Scale;
    struct FRow
    {
        FString Text;
        FLinearColor Color;
    };
    TArray<FRow> Rows, Status;
    auto Wrap = [&](const FString &Value, FLinearColor Color, TArray<FRow> &Into)
    {
        // Character fallback also bounds a single long word; nothing spills outside the side panel.
        TArray<FString> Paragraphs;
        Value.ParseIntoArrayLines(Paragraphs, false);
        for (const FString &Part : Paragraphs)
        {
            FString Pending;
            for (TCHAR Ch : Part)
            {
                if (!Pending.IsEmpty() && MeasureStationText(Pending + Ch, .95f).X > Width)
                {
                    const int32 Space = Pending.Find(TEXT(" "), ESearchCase::CaseSensitive, ESearchDir::FromEnd);
                    if (Space > 0)
                    {
                        Into.Add({Pending.Left(Space), Color});
                        Pending = Pending.Mid(Space + 1);
                    }
                    else
                    {
                        Into.Add({Pending, Color});
                        Pending.Empty();
                    }
                }
                Pending.AppendChar(Ch);
            }
            if (!Pending.IsEmpty())
                Into.Add({Pending, Color});
        }
    };
    for (const auto &Line : Mode.ChatLines)
        Wrap(Line.Speaker + TEXT(": ") + Line.Text, Line.Speaker == TEXT("You") ? FLinearColor(.9f, .94f, 1.f) : Cyan,
             Rows);
    Wrap(Mode.TalkStatus, FLinearColor(1.f, .85f, .5f), Status);
    const int32 Capacity = FMath::Max(1, FMath::FloorToInt((Bottom - Top) / LineH));
    const int32 StatusCount = FMath::Min(Status.Num(), FMath::Max(1, Capacity / 3));
    const int32 Count = FMath::Min(Rows.Num(), Capacity - StatusCount);
    float Y = Bottom - (Count + StatusCount) * LineH;
    for (int32 I = Rows.Num() - Count; I < Rows.Num(); ++I, Y += LineH)
        StationText(Rows[I].Text, X, Y, .95f, Rows[I].Color);
    for (int32 I = 0; I < StatusCount; ++I, Y += LineH)
        StationText(Status[I].Text, X, Y, .95f, Status[I].Color);
}
