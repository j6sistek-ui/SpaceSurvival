#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SSGroomAuthoring.generated.h"

/** Editor-only bridge for fitting the private Silver ponytail's strand groups. */
UCLASS()
class USSGroomAuthoring : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /** Reads positions, guide flags and root UVs without changing the source groom. */
    UFUNCTION(BlueprintCallable, Category = "Character Authoring")
    static FString ReadSilverStrands(UObject *Source);

    /** Validates a fitted two-group description; Apply creates an unsaved private candidate only.
     * Group 0 is fixed scalp hair; group 1 is the dynamic tail. Never overwrites assets. */
    UFUNCTION(BlueprintCallable, Category = "Character Authoring")
    static FString CreateSilverStrands(UObject *Source, const FString &DescriptionJson, const FString &CandidateName,
                                       bool Apply = false);
};
