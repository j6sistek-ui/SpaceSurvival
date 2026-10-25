#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SSBarEyeAuthoring.generated.h"

class USkeletalMesh;
class USkeleton;

/** Private eye-rig initialization unavailable through the reflected SkeletonFactory. */
UCLASS()
class SPACESURVIVAL_API USSBarEyeAuthoring : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category = "Character Authoring")
    static USkeleton *CreateAstraEyeSkeleton(USkeletalMesh *PrivateMesh);
};
