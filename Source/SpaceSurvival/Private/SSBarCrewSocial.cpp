#include "SSBarCrew.h"
#include "SSGameMode.h"
#include "Animation/AnimSequence.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"

FTransform ASSBarCrew::BarShotGrip() const
{
    FTransform Grip = DrinkGrip;
    if (const UStaticMesh *Mesh = Glass->GetStaticMesh())
    {
        const FVector Center = Grip.TransformPosition(Mesh->GetBounds().Origin);
        Grip.SetScale3D(Grip.GetScale3D() * FMath::Clamp(BarShotScale, .2f, 1.f));
        Grip.AddToTranslation(Center - Grip.TransformPosition(Mesh->GetBounds().Origin));
    }
    return Grip;
}

void ASSBarCrew::ResetBarBreakTimer()
{
    const float Minimum = FMath::Max(1.f, float(BarBreakInterval.X));
    SecondsUntilBarBreak = FMath::FRandRange(Minimum, FMath::Max(Minimum, float(BarBreakInterval.Y)));
}

bool ASSBarCrew::TickBarBreak(float Dt)
{
    auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>();
    if (!bBarBreakActive)
    {
        if (!bAmbientBarBreaks || ServiceState != ESSBarServiceState::Available)
            return false;
        SecondsUntilBarBreak -= Dt;
        if (SecondsUntilBarBreak > 0)
            return false;
        SecondsUntilBarBreak = 5.f;
        if (!GM || !GM->CanAmbientCrewSpeak(this) || !IsValid(Bartender) || !Bartender->bIsBartender ||
            Bartender->ReservedBy.IsValid() || Bartender->IsActionPlaying() || !DrinkAnimation ||
            !Bartender->Actions.IsValidIndex(1) || !Bartender->Actions[1].Clip || BarBanter.IsEmpty() ||
            !PlanPath(Bartender->GetActorTransform().TransformPosition(PickupOffset)))
            return false;
        if (UnusedBanter.IsEmpty())
            for (int32 I = 0; I < BarBanter.Num(); ++I)
                UnusedBanter.Add(I);
        int32 Pick = FMath::RandRange(0, UnusedBanter.Num() - 1);
        if (UnusedBanter.Num() > 1 && UnusedBanter[Pick] == PreviousBanter)
            Pick = (Pick + 1) % UnusedBanter.Num();
        BanterIndex = UnusedBanter[Pick];
        UnusedBanter.RemoveAt(Pick);
        PreviousBanter = BanterIndex;
        BanterStep = 0;
        BanterWait = BarBreakTime = 0;
        bBarBreakActive = true;
        Bartender->ReservedBy = this;
        SetState(ESSBarServiceState::JoiningBartender, TEXT("joining Joy for a quick drink at the bar"));
    }
    BarBreakTime += Dt;
    if (!GM || !IsValid(Bartender) || Bartender->ReservedBy != this || !BarBanter.IsValidIndex(BanterIndex) ||
        BarBreakTime > 100.f)
    {
        ReturnHome(TEXT("Back to the tables."));
        return true;
    }
    if (ServiceState == ESSBarServiceState::JoiningBartender)
    {
        if (MoveAlongPath(Dt) && bBarBreakActive)
        {
            SetActorRotation(FRotator(0, (Bartender->GetActorLocation() - GetActorLocation()).Rotation().Yaw, 0));
            PlayService(IdleAnimation, true);
            SetState(ESSBarServiceState::BarBanter, TEXT("chatting with Joy over a quick drink"));
        }
        return true;
    }
    BanterWait += Dt;
    const auto &Lines = BarBanter[BanterIndex];
    if (BanterWait < 2.f)
        return true;
    if (BanterStep == 0 && GM->TryAmbientCrewLine(this, Lines.Astra))
    {
        BanterStep = 1;
        BanterWait = 0;
    }
    else if (BanterStep == 1 && GM->TryAmbientCrewLine(Bartender, Lines.Joy))
    {
        BanterStep = 2;
        BanterWait = 0;
    }
    else if (BanterStep == 2 && GM->CanAmbientCrewSpeak(this))
    {
        // Start both existing drink motions in the same frame; keep each character's own hand grip.
        if (!Bartender->ASSOutpostAmbientActor::TriggerAction(1))
            return true;
        Bartender->BarAction = 1;
        Glass->AttachToComponent(CharacterMesh, FAttachmentTransformRules::KeepRelativeTransform, DrinkHand);
        Glass->SetRelativeTransform(BarShotGrip());
        Glass->SetVisibility(true);
        PlayService(DrinkAnimation, false, true);
        TalkActivity = TEXT("taking a small drink with Joy at the bar");
        BanterStep = 3;
        BanterWait = 0;
    }
    else if (BanterStep == 3 &&
             BanterWait >= FMath::Max(DrinkAnimation->GetPlayLength(), Bartender->Actions[1].Clip->GetPlayLength()))
    {
        Glass->SetVisibility(false);
        PlayService(IdleAnimation, true);
        if (GM->TryAmbientCrewLine(this, Lines.AfterToast))
        {
            BanterStep = 4;
            BanterWait = 0;
        }
    }
    else if (BanterStep == 4 && GM->CanAmbientCrewSpeak(this))
        ReturnHome(TEXT("Back to the tables."));
    return true;
}
