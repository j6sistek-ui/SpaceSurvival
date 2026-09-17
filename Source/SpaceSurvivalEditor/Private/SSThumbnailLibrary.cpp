#include "SSThumbnailLibrary.h"
#include "AssetCompilingManager.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "ImageUtils.h"
#include "Materials/MaterialInterface.h"
#include "Misc/FileHelper.h"
#include "Misc/ObjectThumbnail.h"
#include "ObjectTools.h"
#include "ThumbnailRendering/SceneThumbnailInfo.h"

namespace
{
// A part drawn at low mips is a blur, and a blur is not recognisable. Pin this asset's textures in full before
// drawing; headless runs load hundreds of assets back to back and the streamer never catches up on its own.
void MakeTexturesResident(UStaticMesh *Mesh)
{
    for (const FStaticMaterial &Slot : Mesh->GetStaticMaterials())
    {
        if (!Slot.MaterialInterface)
            continue;
        TArray<UTexture *> Textures;
        Slot.MaterialInterface->GetUsedTextures(Textures, EMaterialQualityLevel::Num, true, ERHIFeatureLevel::Num,
                                                true);
        for (UTexture *Texture : Textures)
            if (auto *Texture2D = Cast<UTexture2D>(Texture))
            {
                Texture2D->SetForceMipLevelsToBeResident(30.f);
                Texture2D->WaitForStreaming();
            }
    }
}

bool Render(UObject *Asset, int32 Size, TArray<FColor> &OutPixels, int32 &OutWidth, int32 &OutHeight)
{
    FObjectThumbnail Thumbnail;
    ThumbnailTools::RenderThumbnail(Asset, Size, Size, ThumbnailTools::EThumbnailTextureFlushMode::AlwaysFlush, nullptr,
                                    &Thumbnail);
    OutWidth = Thumbnail.GetImageWidth();
    OutHeight = Thumbnail.GetImageHeight();
    const TArray<uint8> &Raw = Thumbnail.GetUncompressedImageData();
    if (OutWidth <= 0 || OutHeight <= 0 || Raw.Num() != OutWidth * OutHeight * 4)
        return false;
    OutPixels.SetNumUninitialized(OutWidth * OutHeight);
    FMemory::Memcpy(OutPixels.GetData(), Raw.GetData(), Raw.Num());
    return true;
}

// The thumbnail scene draws its own backdrop, a two-tone checker. Its two colours are whatever dominates the
// border; anything else is the part.
struct FBackdrop
{
    FColor A = FColor::Black, B = FColor::Black;
    static bool Near(const FColor &P, const FColor &Q)
    {
        return FMath::Abs(int32(P.R) - Q.R) <= 6 && FMath::Abs(int32(P.G) - Q.G) <= 6 &&
               FMath::Abs(int32(P.B) - Q.B) <= 6;
    }
    bool Contains(const FColor &P) const
    {
        return Near(P, A) || Near(P, B);
    }
    void Learn(const TArray<FColor> &Pixels, int32 Width, int32 Height)
    {
        TMap<uint32, int32> Counts;
        auto Count = [&](int32 X, int32 Y)
        {
            const FColor &P = Pixels[Y * Width + X];
            ++Counts.FindOrAdd((uint32(P.R >> 2) << 16) | (uint32(P.G >> 2) << 8) | uint32(P.B >> 2));
        };
        for (int32 X = 0; X < Width; ++X)
        {
            Count(X, 0);
            Count(X, Height - 1);
        }
        for (int32 Y = 0; Y < Height; ++Y)
        {
            Count(0, Y);
            Count(Width - 1, Y);
        }
        Counts.ValueSort([](int32 L, int32 R) { return L > R; });
        int32 Index = 0;
        for (const auto &Pair : Counts)
        {
            const FColor Colour(uint8(((Pair.Key >> 16) & 63) << 2), uint8(((Pair.Key >> 8) & 63) << 2),
                                uint8((Pair.Key & 63) << 2));
            (Index == 0 ? A : B) = Colour;
            if (++Index == 2)
                break;
        }
        if (Index == 1)
            B = A;
    }
    int32 Coverage(const TArray<FColor> &Pixels) const
    {
        int32 Covered = 0;
        for (const FColor &P : Pixels)
            Covered += Contains(P) ? 0 : 1;
        return Covered;
    }
};
} // namespace

bool USSThumbnailLibrary::ExportAssetThumbnail(UObject *Asset, const FString &PngPath, int32 Size)
{
    if (!Asset || Size < 32 || Size > 2048)
        return false;
    auto *Mesh = Cast<UStaticMesh>(Asset);
    if (Mesh)
        MakeTexturesResident(Mesh);
    // A mesh whose shaders or build are still compiling draws as the default grey checker.
    FAssetCompilingManager::Get().FinishAllCompilation();

    // The default orbit sees a thin wall edge-on, and kit walls are one-sided, so half the compass shows nothing at
    // all. For meshes, try a full turn of yaws small and keep the one that shows the most surface; the asset's own
    // thumbnail settings are put back, and the package is never dirtied.
    UThumbnailInfo *Saved = Mesh ? Mesh->ThumbnailInfo.Get() : nullptr;
    USceneThumbnailInfo *View = nullptr;
    if (Mesh)
    {
        View = NewObject<USceneThumbnailInfo>(GetTransientPackage());
        View->OrbitPitch = -22.f;
        View->OrbitZoom = 0.f;
        Mesh->ThumbnailInfo = View;
        float BestYaw = -157.5f;
        int32 BestCoverage = -1;
        for (float Yaw : {-157.5f, -112.5f, -67.5f, -22.5f, 22.5f, 67.5f, 112.5f, 157.5f})
        {
            View->OrbitYaw = Yaw;
            TArray<FColor> Probe;
            int32 W = 0, H = 0;
            if (!Render(Asset, 64, Probe, W, H))
                continue;
            FBackdrop Backdrop;
            Backdrop.Learn(Probe, W, H);
            const int32 Coverage = Backdrop.Coverage(Probe);
            // Prefer the three-quarter defaults unless another angle shows clearly more of the part.
            if (Coverage > BestCoverage * 1.15f)
            {
                BestCoverage = Coverage;
                BestYaw = Yaw;
            }
        }
        View->OrbitYaw = BestYaw;
    }
    // Drawn at twice the size and averaged down: the thumbnail scene is soft at 256, and soft is hard to recognise.
    TArray<FColor> Large;
    int32 LargeWidth = 0, LargeHeight = 0;
    const bool Rendered = Render(Asset, Size * 2, Large, LargeWidth, LargeHeight);
    if (Mesh)
        Mesh->ThumbnailInfo = Saved;
    if (!Rendered || LargeWidth < 2 || LargeHeight < 2)
        return false;
    const int32 Width = LargeWidth / 2, Height = LargeHeight / 2;
    TArray<FColor> Pixels;
    Pixels.SetNumUninitialized(Width * Height);
    for (int32 Y = 0; Y < Height; ++Y)
        for (int32 X = 0; X < Width; ++X)
        {
            int32 R = 0, G = 0, B = 0;
            for (int32 Dy = 0; Dy < 2; ++Dy)
                for (int32 Dx = 0; Dx < 2; ++Dx)
                {
                    const FColor &P = Large[(Y * 2 + Dy) * LargeWidth + X * 2 + Dx];
                    R += P.R;
                    G += P.G;
                    B += P.B;
                }
            Pixels[Y * Width + X] = FColor(uint8(R / 4), uint8(G / 4), uint8(B / 4), 255);
        }

    FBackdrop Backdrop;
    Backdrop.Learn(Pixels, Width, Height);
    if (Backdrop.Coverage(Pixels) == 0)
        return false;
    // One flat backdrop for every part, matching the gallery page, and an exposure lift: the thumbnail scene
    // lights dark metals so dimly that half a space station's parts would be silhouettes.
    const FColor Flat(0x1b, 0x1d, 0x22, 255);
    for (FColor &P : Pixels)
    {
        if (Backdrop.Contains(P))
        {
            P = Flat;
            continue;
        }
        auto Lift = [](uint8 V) { return uint8(FMath::Clamp(FMath::Pow(V / 255.f, 0.62f) * 255.f, 0.f, 255.f)); };
        P = FColor(Lift(P.R), Lift(P.G), Lift(P.B), 255);
    }
    TArray64<uint8> Png;
    FImageUtils::PNGCompressImageArray(Width, Height, TArrayView64<const FColor>(Pixels.GetData(), Pixels.Num()), Png);
    return Png.Num() > 0 && FFileHelper::SaveArrayToFile(Png, *PngPath);
}
