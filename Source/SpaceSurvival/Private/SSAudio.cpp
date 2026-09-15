#include "SSAudio.h"
#include "SSGameInstance.h"
#include "SSPhase1Data.h"
#include "Components/AudioComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/PackageName.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundConcurrency.h"

namespace
{
float UnitGain(double Value)
{
    return FMath::IsFinite(Value) ? float(FMath::Clamp(Value, 0.0, 1.0)) : 0.f;
}
void ReleaseVoice(UAudioComponent *Component)
{
    if (IsValid(Component))
    {
        Component->Stop();
        Component->DestroyComponent();
    }
}
} // namespace
namespace SSAudio
{
float EffectsGain(const UObject *Context, float Gain)
{
    const auto *Instance = Cast<USSGameInstance>(UGameplayStatics::GetGameInstance(Context));
    return Instance ? UnitGain(Instance->Session.settings.masterVolume) *
                          UnitGain(Instance->Session.settings.effectsVolume) * UnitGain(Gain)
                    : 0.f;
}
float MusicGain(const UObject *Context, float Gain)
{
    const auto *Instance = Cast<USSGameInstance>(UGameplayStatics::GetGameInstance(Context));
    return Instance ? UnitGain(Instance->Session.settings.masterVolume) *
                          UnitGain(Instance->Session.settings.musicVolume) * UnitGain(Gain)
                    : 0.f;
}
USoundBase *PresentationSound(const TCHAR *Name)
{
    const FString Licensed = FString::Printf(TEXT("/Game/SpaceSurvival/Licensed/Audio/%s.%s"), Name, Name);
    if (FPackageName::DoesPackageExist(FPackageName::ObjectPathToPackageName(Licensed)))
        if (auto *Sound = LoadObject<USoundBase>(nullptr, *Licensed))
            return Sound;
    const FString Generated = FString::Printf(TEXT("/Game/SpaceSurvival/Audio/%s.%s"), Name, Name);
    return LoadObject<USoundBase>(nullptr, *Generated);
}
} // namespace SSAudio

bool USSWorldAudioSubsystem::DoesSupportWorldType(EWorldType::Type WorldType) const
{
    return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}
void USSWorldAudioSubsystem::Initialize(FSubsystemCollectionBase &Collection)
{
    Super::Initialize(Collection);
    Attenuation = NewObject<USoundAttenuation>(this);
    Attenuation->Attenuation.bAttenuate = true;
    Attenuation->Attenuation.bSpatialize = true;
    Attenuation->Attenuation.AttenuationShapeExtents = FVector(650.f, 0.f, 0.f);
    Attenuation->Attenuation.FalloffDistance = 7500.f;
    ShotConcurrency = NewObject<USoundConcurrency>(this);
    ShotConcurrency->Concurrency.MaxCount = 12;
    ShotConcurrency->Concurrency.bLimitToOwner = false;
    ShotConcurrency->Concurrency.ResolutionRule = EMaxConcurrentResolutionRule::StopFarthestThenOldest;
    ShotConcurrency->Concurrency.VoiceStealReleaseTime = .04f;
    FieldConcurrency = NewObject<USoundConcurrency>(this);
    FieldConcurrency->Concurrency.MaxCount = 4;
    FieldConcurrency->Concurrency.bLimitToOwner = false;
    FieldConcurrency->Concurrency.ResolutionRule = EMaxConcurrentResolutionRule::StopFarthestThenOldest;
    FieldConcurrency->Concurrency.VoiceStealReleaseTime = .08f;
}
void USSWorldAudioSubsystem::Deinitialize()
{
    for (auto &Voice : Voices)
        ReleaseVoice(Voice.Component);
    Voices.Empty();
    WarmSounds.Empty();
    Super::Deinitialize();
}
TStatId USSWorldAudioSubsystem::GetStatId() const
{
    RETURN_QUICK_DECLARE_CYCLE_STAT(USSWorldAudioSubsystem, STATGROUP_Tickables);
}
USoundBase *USSWorldAudioSubsystem::ResolveCue(const FSSAudioCueDefinition &Cue, const TCHAR *DefaultName)
{
    USoundBase *Sound = nullptr;
    if (Cue.UseDefaultSound)
        Sound = SSAudio::PresentationSound(DefaultName);
    else if (!Cue.Sound.IsNull())
        Sound = Cue.Sound.LoadSynchronous();
    // Explicit override + null means silence, never an implicit preset fallback.
    if (Sound)
        WarmSounds.AddUnique(Sound);
    return Sound;
}
void USSWorldAudioSubsystem::PreloadContent(const USSPhase1Data *Content)
{
    if (!Content)
        return;
    for (const auto &Hazard : Content->Hazards)
    {
        if (Hazard.Kind == ESSWorldKind::ElectricalStorm)
        {
            ResolveCue(Hazard.FieldLoopAudio, TEXT("ElectricalCharge"));
            ResolveCue(Hazard.DischargeAudio, TEXT("ElectricalDischarge"));
        }
        else if (Hazard.Kind == ESSWorldKind::GravityAnomaly)
            ResolveCue(Hazard.FieldLoopAudio, TEXT("GravityAmbience"));
        else if (Hazard.Destructible)
            ResolveCue(Hazard.DestructionAudio, TEXT("DebrisBreak"));
    }
    for (const auto &Enemy : Content->Enemies)
    {
        ResolveCue(Enemy.ShotAudio, TEXT("EnemyFire"));
        ResolveCue(Enemy.DestructionAudio, TEXT("EnemyBreak"));
    }
}
UAudioComponent *USSWorldAudioSubsystem::CreateVoice(AActor *Owner, const FSSAudioCueDefinition &Cue,
                                                     const TCHAR *DefaultName, FVector Position, bool Loop,
                                                     float Intensity)
{
    if (!GetWorld() || (Loop && (!IsValid(Owner) || !Owner->GetRootComponent())))
        return nullptr;
    const float Gain = UnitGain(Cue.Gain);
    const float Envelope = UnitGain(Intensity);
    if (!Loop && SSAudio::EffectsGain(this, Gain * Envelope) <= 0.f)
        return nullptr;
    USoundBase *Sound = ResolveCue(Cue, DefaultName);
    if (!Sound || Sound->IsLooping() != Loop)
        return nullptr; // A one-shot override must not become indefinite field ambience.
    if (!Loop)
    {
        if (const auto *Pawn = UGameplayStatics::GetPlayerPawn(this, 0))
            if (FVector::DistSquared(Pawn->GetActorLocation(), Position) > FMath::Square(8150.f))
                return nullptr;
        // Bound component allocation as well as the audio renderer's shared voice count.
        int32 Shots = 0, Oldest = INDEX_NONE;
        for (int32 Index = 0; Index < Voices.Num(); ++Index)
            if (!Voices[Index].Loop)
            {
                ++Shots;
                if (Oldest == INDEX_NONE)
                    Oldest = Index;
            }
        if (Shots >= 12 && Oldest != INDEX_NONE)
        {
            ReleaseVoice(Voices[Oldest].Component);
            Voices.RemoveAt(Oldest, 1, EAllowShrinking::No);
        }
    }
    else
    {
        int32 Loops = 0;
        for (const auto &Voice : Voices)
            Loops += Voice.Loop && IsValid(Voice.Component) ? 1 : 0;
        if (Loops >= 24)
            return nullptr; // The Director itself admits at most 24 threats.
    }
    auto *Component = NewObject<UAudioComponent>(Loop ? static_cast<UObject *>(Owner) : this);
    Component->SetAutoActivate(false);
    Component->bAutoDestroy = false;
    Component->bStopWhenOwnerDestroyed = Loop;
    Component->bIsUISound = false;
    Component->bAllowSpatialization = true;
    Component->AttenuationSettings = Attenuation;
    Component->ConcurrencySet.Add(Loop ? FieldConcurrency : ShotConcurrency);
    Component->SetSound(Sound);
    Component->SetVolumeMultiplier(SSAudio::EffectsGain(this, Gain * Envelope));
    if (Loop)
    {
        Component->SetupAttachment(Owner->GetRootComponent());
        Owner->AddInstanceComponent(Component);
    }
    else
        Component->SetWorldLocation(Position);
    Component->RegisterComponentWithWorld(GetWorld());
    FSSAudioVoice Voice;
    Voice.Component = Component;
    Voice.Owner = Owner;
    Voice.Gain = Gain;
    Voice.Intensity = Envelope;
    Voice.Duration = FMath::IsFinite(Sound->GetDuration()) ? FMath::Clamp(Sound->GetDuration(), .1f, 10.f) : 10.f;
    Voice.Loop = Loop;
    Voices.Add(Voice);
    // No automatic activation: the first audio buffer receives the persisted mix.
    Component->Play();
    return Component;
}
UAudioComponent *USSWorldAudioSubsystem::CreateFieldLoop(AActor *Owner, const FSSAudioCueDefinition &Cue,
                                                         const TCHAR *DefaultName, float Intensity)
{
    return CreateVoice(Owner, Cue, DefaultName, Owner ? Owner->GetActorLocation() : FVector::ZeroVector, true,
                       Intensity);
}
UAudioComponent *USSWorldAudioSubsystem::PlayOneShot(const FSSAudioCueDefinition &Cue, const TCHAR *DefaultName,
                                                     FVector Position)
{
    return CreateVoice(nullptr, Cue, DefaultName, Position, false, 1.f);
}
void USSWorldAudioSubsystem::SetFieldIntensity(UAudioComponent *Component, float Intensity, float Pitch)
{
    if (!IsValid(Component))
        return;
    for (auto &Voice : Voices)
        if (Voice.Component == Component && Voice.Loop)
        {
            Voice.Intensity = UnitGain(Intensity);
            Component->SetVolumeMultiplier(SSAudio::EffectsGain(this, Voice.Gain * Voice.Intensity));
            Component->SetPitchMultiplier(FMath::IsFinite(Pitch) ? FMath::Clamp(Pitch, .5f, 1.5f) : 1.f);
            return;
        }
}
void USSWorldAudioSubsystem::Tick(float DeltaSeconds)
{
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds < 0.f)
        return;
    for (int32 Index = Voices.Num() - 1; Index >= 0; --Index)
    {
        auto &Voice = Voices[Index];
        auto *Component = Voice.Component.Get();
        if (!IsValid(Component) || !Component->IsRegistered() ||
            (Voice.Loop && (!Voice.Owner.IsValid() || Voice.Owner->IsActorBeingDestroyed())))
        {
            ReleaseVoice(Component);
            Voices.RemoveAt(Index, 1, EAllowShrinking::No);
            continue;
        }
        Voice.Age += DeltaSeconds;
        Voice.RetrySeconds += DeltaSeconds;
        Component->SetVolumeMultiplier(SSAudio::EffectsGain(this, Voice.Gain * Voice.Intensity));
        if (!Voice.Loop &&
            ((!Component->IsPlaying() && Voice.Age > .05f) || Voice.Age > FMath::Max(.1f, Voice.Duration) + .25f))
        {
            ReleaseVoice(Component);
            Voices.RemoveAt(Index, 1, EAllowShrinking::No);
        }
        else if (Voice.Loop && !Component->IsPlaying() && Voice.RetrySeconds >= 1.f &&
                 Component->VolumeMultiplier > 0.f)
        {
            // A loop displaced by the shared concurrency group can retry at most once/second.
            Voice.RetrySeconds = 0.f;
            Component->Play();
        }
    }
}
