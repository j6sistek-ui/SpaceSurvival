#pragma once
#include "CoreMinimal.h"

namespace SSLocalSave
{
// The Phase 1 Windows generic backend uses the existing three Unreal .sav slots.
bool Write(const FString &Slot, const TArray<uint8> &Data, FString &Error);
} // namespace SSLocalSave
