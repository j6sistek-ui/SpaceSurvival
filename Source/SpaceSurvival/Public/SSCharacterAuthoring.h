#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SSCharacterAuthoring.generated.h"

class USkeletalMesh;
class USkeleton;
class UAnimSequence;

/** Bounded editor operations unavailable through Unreal's reflected Python factories. */
UCLASS()
class SPACESURVIVAL_API USSCharacterAuthoringLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Creates only the private normalized female skeleton. Never overwrites or saves an asset. */
    UFUNCTION(BlueprintCallable, Category = "Character Authoring")
    static USkeleton *CreateAlienFemaleSkeleton(USkeletalMesh *PrivateMesh);

    /** Measures every baked frame; optionally shifts only a private female clip's root by a constant.
     *  Returns a JSON measurement/invariant receipt. Never saves assets; Python owns backups and hashes. */
    UFUNCTION(BlueprintCallable, Category = "Character Authoring")
    static FString GroundAlienFemaleClip(USkeletalMesh *PrivateMesh, UAnimSequence *PrivateClip, bool Apply = false);
};
