#include "SSInputGlyphs.h"
#include "Engine/Texture2D.h"

UTexture2D *USSInputGlyphSet::Find(FName ActionId) const
{
    if (const TWeakObjectPtr<UTexture2D> *Cached = ResolvedCache.Find(ActionId))
        if (UTexture2D *Texture = Cached->Get())
            return Texture;
    if (const TSoftObjectPtr<UTexture2D> *Soft = Icons.Find(ActionId))
    {
        UTexture2D *Texture = Soft->LoadSynchronous();
        ResolvedCache.Add(ActionId, Texture);
        return Texture;
    }
    return nullptr;
}
