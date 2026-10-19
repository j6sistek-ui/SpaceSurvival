#include "SSHUD.h"
#include "SSOutpostSandbox.h"
#include "Engine/Canvas.h"

void ASSHUD::DrawInteractionOptions(const ASSOutpostAmbientActor &Crew)
{
    const float W = FMath::Min(680.f * Scale, float(Canvas->SizeX) - 48.f * Scale);
    const float X = (Canvas->SizeX - W) * .5f;
    const float H = 240.f * Scale, Y = Canvas->SizeY - H - 155.f * Scale;
    const FLinearColor Cyan(.45f, .9f, 1.f);
    DrawRect(FLinearColor(.008f, .02f, .035f, .95f), X, Y, W, H);
    Stroke(FVector2D(X, Y), FVector2D(X + W, Y), Cyan, 2.f);
    StationText(TEXT("HOLD LB + PRESS A D-PAD DIRECTION"), X + 18.f * Scale, Y + 14.f * Scale, .82f, Cyan);
    static const TCHAR *Directions[] = {TEXT("UP"), TEXT("RIGHT"), TEXT("DOWN"), TEXT("LEFT")};
    static const FKey Keys[] = {EKeys::Gamepad_DPad_Up, EKeys::Gamepad_DPad_Right, EKeys::Gamepad_DPad_Down,
                                EKeys::Gamepad_DPad_Left};
    for (int32 I = 0; I < FMath::Min(4, Crew.Actions.Num()); ++I)
    {
        const float RowY = Y + (55.f + I * 43.f) * Scale;
        Glyph(Keys[I], Keys[I], X + 18.f * Scale, RowY, .68f, Cyan);
        StationText(Directions[I], X + 68.f * Scale, RowY, .78f, Cyan);
        StationText(Crew.Actions[I].Name, X + 160.f * Scale, RowY, .85f, FLinearColor::White);
    }
}
