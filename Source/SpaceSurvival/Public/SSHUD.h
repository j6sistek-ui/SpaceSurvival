#pragma once
#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "SSHUD.generated.h"
struct FSlateFontInfo;
class UTexture2D;
UCLASS()
class SPACESURVIVAL_API ASSHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
    int32 MenuIndexAt(FVector2D Point) const;
    const TArray<FBox2D> &GetMenuBounds() const
    {
        return MenuBounds;
    }
    bool IsDrawingFigmaMainMenu() const
    {
        return bTitleWasOpen;
    }
    int32 GetFigmaMainMenuFocus() const
    {
        return bTitleWasOpen ? RenderedTitleFocus : INDEX_NONE;
    }

private:
    friend class ASSWave10Soak;
    bool bReviewFlightHUD = false;
    UPROPERTY()
    TMap<FName, TObjectPtr<UTexture2D>> RefreshTextures;
    UPROPERTY()
    TObjectPtr<class UFont> RefreshFont;
    float RefreshScale = 1.f;
    FVector2D RefreshOrigin = FVector2D::ZeroVector;
    void BeginRefreshLayout();
    UTexture2D *RefreshTexture(FName Name);
    FBox2D RefreshBounds(float X, float Y, float Width, float Height) const;
    void RefreshImage(FName Name, float X, float Y, float Width, float Height, FLinearColor Tint = FLinearColor::White);
    float RefreshText(const FString &Value, float X, float Y, float Pixels, FLinearColor Color, float Width = 0.f);
    bool DrawRefreshMenu(const class ASSGameMode &Mode);
    void DrawRefreshVitals(const class ASSGameMode &Mode, bool Walking);
    TArray<FBox2D> MenuBounds;
    float Scale = 1.f;
    FString FeedbackRun;
    int32 ObservedKills = 0, RecentKills = 0;
    float KillNoticeUntil = 0.f;
    UPROPERTY()
    TObjectPtr<UObject> KeyboardMouseIcons;
    UPROPERTY()
    TObjectPtr<UObject> GamepadIcons;
    UPROPERTY()
    TArray<TObjectPtr<UTexture2D>> CrosshairTextures;
    UPROPERTY()
    TArray<TObjectPtr<UTexture2D>> TitleTextures;
    bool bTitleAssetsRequested = false, bTitleWasOpen = false, bTitleNavigationFocus = false;
    int32 LastTitleSelection = INDEX_NONE;
    int32 RenderedTitleFocus = INDEX_NONE;
    FVector2D LastTitlePointer = FVector2D::ZeroVector;
    /** Exact Figma artwork, with the same native entry indices used by pointer/controller input. */
    bool DrawFigmaMainMenu(const class ASSGameMode &Mode);
    FSlateFontInfo HudFont(float Size) const;
    FVector2D MeasureText(const FString &Value, float Size) const;
    void Text(const FString &Value, float X, float Y, float Size = 1.f, FLinearColor Color = FLinearColor::White);
    float Paragraph(const FString &Value, float X, float Y, float Width, float Size, FLinearColor Color,
                    bool Render = true);
    void Stroke(FVector2D A, FVector2D B, FLinearColor Color, float Width = 1.f);
    // Draws a device-appropriate action prompt: the assigned glyph icon if the
    // active GameMode has one for ActionId on the current input device,
    // otherwise KeyboardLabel/GamepadLabel as text. Returns the X position
    // immediately after what was drawn, for placing a following label.
    float DrawPrompt(FName ActionId, const FString &KeyboardLabel, const FString &GamepadLabel, float X, float Y,
                     float Size, FLinearColor Color);
    void ThreatGlyph(FVector2D Centre, bool Flanker, bool Charging, float Size, FLinearColor Color);
    void DrawCombatCues(class ASSShip *Ship, bool ShowRadar);
    /** Aim reticle. Four owned states share one on-screen ring size, so only the tick marks move. */
    void DrawCrosshair(class ASSShip *Ship, float CentreX, float CentreY);
    void Meter(const FString &Name, double Value, double Maximum, float X, float Y, FLinearColor Color);
    /** True while the owning controller's last input came from a gamepad, so a prompt can pick the
     *  matching half of the EasyInputPrompts icon set instead of naming both devices at once. */
    bool UsingGamepad() const;
    UTexture2D *GlyphTexture(const FKey &Key, bool Gamepad);
    /** Draws one device-icon prompt: the keyboard/mouse key on that device, the gamepad key on this
     *  one. Falls back to the key's own display name if the icon pack has not resolved (or is not
     *  present in this build), so a prompt never goes silently blank. */
    float Glyph(const FKey &KeyboardKey, const FKey &GamepadKey, float X, float Y, float Size,
                FLinearColor Color = FLinearColor::White);
};
