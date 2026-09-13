#pragma once
#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "SSHUD.generated.h"
UCLASS()
class SPACESURVIVAL_API ASSHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
    int32 MenuIndexAt(FVector2D Point) const;

private:
    TArray<FBox2D> MenuBounds;
    float Scale = 1.f;
    void Text(const FString &Value, float X, float Y, float Size = 1.f, FLinearColor Color = FLinearColor::White);
    float Paragraph(const FString &Value, float X, float Y, float Width, float Size, FLinearColor Color,
                    bool Render = true);
    void Stroke(FVector2D A, FVector2D B, FLinearColor Color, float Width = 1.f);
    void ThreatGlyph(FVector2D Centre, bool Flanker, bool Charging, float Size, FLinearColor Color);
    void DrawCombatCues(class ASSShip *Ship, bool ShowRadar);
    void Meter(const FString &Name, double Value, double Maximum, float X, float Y, FLinearColor Color);
};
