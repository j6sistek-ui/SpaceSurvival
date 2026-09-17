#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SSThumbnailLibrary.generated.h"

// The prefab library's pictures. A proxy rendered in Blender has no textures, and a white wall panel looks like
// every other white wall panel; the engine already draws the real preview the Content Browser shows, for meshes,
// materials and effects alike. This writes that preview to a PNG so the catalogue, the Blender panel and the
// gallery page can all show what a part actually is.
UCLASS()
class USSThumbnailLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Renders the asset's own thumbnail at Size x Size and writes it to PngPath. False when nothing was drawn. */
    UFUNCTION(BlueprintCallable, Category = "SpaceSurvival|Library")
    static bool ExportAssetThumbnail(UObject *Asset, const FString &PngPath, int32 Size = 256);
};
