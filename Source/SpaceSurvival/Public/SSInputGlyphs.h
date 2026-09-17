#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "SSInputGlyphs.generated.h"

class UTexture2D;

// A device-specific icon lookup for HUD action prompts (e.g. "Interact" -> a
// glyph texture). Create one instance for keyboard/mouse and one for gamepad,
// assign the owned B23 EasyInputPrompts textures once imported, and reference
// them from ASSGameMode::KeyboardGlyphs / GamepadGlyphs. An action with no
// assigned icon simply falls back to on-screen text, so this is safe to leave
// unpopulated: current HUD behavior is unchanged until an owner fills it in.
UCLASS(BlueprintType)
class SPACESURVIVAL_API USSInputGlyphSet : public UPrimaryDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Glyphs")
    TMap<FName, TSoftObjectPtr<UTexture2D>> Icons;

    // Resolves and caches the icon for an action id. Returns null when no icon
    // is assigned, so callers should fall back to text.
    UTexture2D *Find(FName ActionId) const;

private:
    mutable TMap<FName, TWeakObjectPtr<UTexture2D>> ResolvedCache;
};
