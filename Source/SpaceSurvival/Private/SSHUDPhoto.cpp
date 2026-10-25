#include "SSHUD.h"
#include "SSPhotoMode.h"
#include "Engine/Canvas.h"

void ASSHUD::DrawPhotoControls(const USSPhotoMode &Photo)
{
    const float Margin = 24.f * Scale;
    const float Width = Canvas->SizeX - Margin * 2.f;
    const float Height = 225.f * Scale;
    const float Y = Canvas->SizeY - Height - Margin;
    const FLinearColor Cyan(.60f, .90f, .96f);
    DrawRect(FLinearColor(.008f, .02f, .035f, .92f), Margin, Y, Width, Height);
    Stroke(FVector2D(Margin, Y), FVector2D(Margin + Width, Y), Cyan, 2.f);
    Text(FString::Printf(TEXT("PHOTO MODE  |  PAUSED     %.1f / 40 m     FOV %.0f"), Photo.DistanceMetres(),
                         Photo.FieldOfView()),
         Margin + 18.f * Scale, Y + 16.f * Scale, .85f, Cyan);
    const FString Move = UsingGamepad()
                             ? TEXT("Left stick: move | Right stick: look | RB / LB: up / down | RT: fast | LT: slow")
                             : TEXT("WASD: move | Mouse: look | E / Q: up / down | Shift: fast | Ctrl: slow");
    const FString Actions =
        UsingGamepad()
            ? TEXT("A: take photo | D-pad Left / Right: zoom | X: reset | Y: hide controls | B / D-pad Up: exit")
            : TEXT("Enter: take photo | Mouse wheel: zoom | Home: reset | H: hide controls | Esc / F8: exit");
    float Top = Y + 58.f * Scale;
    Top += Paragraph(Move, Margin + 18.f * Scale, Top, Width - 36.f * Scale, .62f, FLinearColor::White) + 10.f * Scale;
    Top +=
        Paragraph(Actions, Margin + 18.f * Scale, Top, Width - 36.f * Scale, .62f, FLinearColor::White) + 10.f * Scale;
    Paragraph(
        Photo.Status().IsEmpty()
            ? TEXT("Photos save to Saved/Screenshots/PhotoMode. Walls and the distance limit bound camera movement.")
            : Photo.Status(),
        Margin + 18.f * Scale, Top, Width - 36.f * Scale, .52f, Cyan);
}
