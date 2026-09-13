#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSContentTypes.h"
#include "SSAudio.generated.h"

class UAudioComponent;
class USoundAttenuation;
class USoundConcurrency;
class USoundBase;
class USSPhase1Data;

namespace SSAudio
{
float EffectsGain(const UObject *Context, float Gain = 1.f);
float MusicGain(const UObject *Context, float Gain = 1.f);
} // namespace SSAudio

USTRUCT()
struct FSSAudioVoice
{
    GENERATED_BODY()
    UPROPERTY()
    TObjectPtr<UAudioComponent> Component;
    TWeakObjectPtr<AActor> Owner;
    float Gain = 0.f;
    float Intensity = 1.f;
    float Age = 0.f;
    float RetrySeconds = 0.f;
    float Duration = 0.f;
    bool Loop = false;
};

/** World-owned spatial mix for existing threats; no gameplay or save state. */
UCLASS()
class SPACESURVIVAL_API USSWorldAudioSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase &Collection) override;
    virtual void Deinitialize() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual TStatId GetStatId() const override;
    void PreloadContent(const USSPhase1Data *Content);
    UAudioComponent *CreateFieldLoop(AActor *Owner, const FSSAudioCueDefinition &Cue, const TCHAR *DefaultName,
                                     float Intensity);
    UAudioComponent *PlayOneShot(const FSSAudioCueDefinition &Cue, const TCHAR *DefaultName, FVector Position);
    void SetFieldIntensity(UAudioComponent *Component, float Intensity, float Pitch = 1.f);
    USoundBase *ResolveCue(const FSSAudioCueDefinition &Cue, const TCHAR *DefaultName);

protected:
    virtual bool DoesSupportWorldType(EWorldType::Type WorldType) const override;

private:
    friend class FSSAudioFirstState;
    friend class FSSWorldAudioHooks;
    UPROPERTY()
    TObjectPtr<USoundAttenuation> Attenuation;
    UPROPERTY()
    TObjectPtr<USoundConcurrency> ShotConcurrency;
    UPROPERTY()
    TObjectPtr<USoundConcurrency> FieldConcurrency;
    UPROPERTY()
    TArray<TObjectPtr<USoundBase>> WarmSounds;
    UPROPERTY()
    TArray<FSSAudioVoice> Voices;
    UAudioComponent *CreateVoice(AActor *Owner, const FSSAudioCueDefinition &Cue, const TCHAR *DefaultName,
                                 FVector Position, bool Loop, float Intensity);
};
