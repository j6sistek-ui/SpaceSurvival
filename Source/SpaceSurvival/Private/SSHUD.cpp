#include "SSHUD.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"

void ASSHUD::Text(const FString& Value,float X,float Y,float Size,FLinearColor Color)
{ DrawText(Value,Color,X,Y,GEngine->GetMediumFont(),Size*Scale,false); }
void ASSHUD::Meter(const FString& Name,double Value,double Maximum,float X,float Y,FLinearColor Color)
{
    DrawRect(FLinearColor(.015f,.025f,.045f,.9f),X,Y,220*Scale,29*Scale);
    DrawRect(Color,X,Y+25*Scale,220*Scale*FMath::Clamp(float(Value/FMath::Max(1.0,Maximum)),0.f,1.f),4*Scale);
    Text(FString::Printf(TEXT("%s  %.0f / %.0f"),*Name,Value,Maximum),X+8*Scale,Y+4*Scale,.75f);
}
int32 ASSHUD::MenuIndexAt(FVector2D Point) const
{ for(int I=0;I<MenuBounds.Num();++I) if(MenuBounds[I].IsInside(Point))return I;return INDEX_NONE; }
void ASSHUD::DrawHUD()
{
    Super::DrawHUD(); MenuBounds.Empty(); if(!Canvas)return;
    auto* GI=GetGameInstance<USSGameInstance>(); auto* GM=GetWorld()->GetAuthGameMode<ASSGameMode>(); if(!GI||!GM)return;
    const auto& S=GI->Session; const auto Stats=S.Stats();
    Scale=FMath::Clamp(float(Canvas->SizeY)/1080.f*float(S.settings.uiScale),.65f,1.6f);
    const float W=Canvas->SizeX,H=Canvas->SizeY,Margin=30*Scale;
    if(S.run.active)
    {
        Text(FString::Printf(TEXT("WAVE %02d"),S.run.wave),Margin,Margin,1.5f);
        Text(FString::Printf(TEXT("%d CREDITS"),S.run.credits),W-250*Scale,Margin,1.f,FLinearColor(1,.78f,.35f));
        Meter(TEXT("HULL"),S.run.hull,Stats.maxHull,Margin,H-150*Scale,FLinearColor(.35f,.9f,.65f));
        Meter(TEXT("SHIELD"),S.run.shield,Stats.maxShield,Margin,H-112*Scale,FLinearColor(.25f,.7f,1));
        Meter(TEXT("BOOST"),S.run.boost,100,Margin,H-74*Scale,FLinearColor(.7f,.4f,1));
        Meter(S.run.brakeOverheated?TEXT("BRAKE OVERHEAT"):TEXT("BRAKE HEAT"),S.run.brakeHeat,100,W-250*Scale,H-112*Scale,FLinearColor(1,.6f,.25f));
        Text(S.run.weapon==SS::Weapon::RapidLaser?TEXT("RAPID LASER"):TEXT("HEAVY CANNON"),W-250*Scale,H-68*Scale,.9f);
        if(S.run.criticalSeconds>0)Text(TEXT("! SUBSYSTEM IMPAIRED / REPAIR AVAILABLE"),Margin,100*Scale,.9f,FLinearColor(1,.7f,.2f));
        if(S.run.contract!=SS::Contract::None)Text(FString::Printf(TEXT("CONTRACT %s  %d / %d"),S.run.contract==SS::Contract::Objective?TEXT("HUNTER"):TEXT("PRESSURE"),S.run.contractProgress,S.run.contractTarget),Margin,140*Scale,.8f);
        if(S.run.pendingReward)Text(TEXT("REWARD SECURED / E or A to choose"),W*.5f-180*Scale,H-90*Scale,.9f,FLinearColor(1,.8f,.4f));
    }
    if(auto* Ship=GM->GetPlayerShip(); Ship && S.IsFlying())
    {
        DrawLine(W*.5f-14*Scale,H*.5f,W*.5f-5*Scale,H*.5f,FLinearColor::White,1.3f);
        DrawLine(W*.5f+5*Scale,H*.5f,W*.5f+14*Scale,H*.5f,FLinearColor::White,1.3f);
        DrawLine(W*.5f,H*.5f-14*Scale,W*.5f,H*.5f-5*Scale,FLinearColor::White,1.3f);
        if(IsValid(Ship->SoftTarget))
        {
            FVector2D Screen; if(PlayerOwner->ProjectWorldLocationToScreen(Ship->SoftTarget->GetActorLocation(),Screen))
                Text(TEXT("[  +  ]"),Screen.X-26*Scale,Screen.Y-12*Scale,.85f,FLinearColor(.5f,1,.9f));
        }
        if(GM->Director->GetActiveThreatCount()>3)
        {
            const float RX=W-115*Scale,RY=180*Scale;
            DrawRect(FLinearColor(.015f,.025f,.04f,.8f),RX-80*Scale,RY-70*Scale,160*Scale,140*Scale);
            Text(TEXT("THREAT RADAR"),RX-60*Scale,RY-65*Scale,.55f);
            Text(TEXT("^"),RX-4*Scale,RY,.7f);
            for(TActorIterator<ASSEnemy> It(GetWorld());It;++It)
            {
                FVector Delta=Ship->GetActorTransform().InverseTransformPosition(It->GetActorLocation());
                Text(TEXT("x"),RX+FMath::Clamp(Delta.Y/150.f,-65.f,65.f)*Scale,RY-FMath::Clamp(Delta.X/180.f,-45.f,45.f)*Scale,.75f,FLinearColor(1,.5f,.3f));
            }
        }
        for(TActorIterator<ASSEncounterBeacon> It(GetWorld());It;++It)
        {
            if(It->IsResolved())continue;
            FVector2D Screen(W*.5f,180*Scale);
            if(!PlayerOwner->ProjectWorldLocationToScreen(It->GetActorLocation(),Screen))
            {
                const FVector Local=Ship->GetActorTransform().InverseTransformPosition(It->GetActorLocation());
                Screen=FVector2D(Local.Y<0?180*Scale:W-360*Scale,H*.5f);
            }
            Screen.X=FMath::Clamp(Screen.X,180*Scale,W-360*Scale); Screen.Y=FMath::Clamp(Screen.Y,180*Scale,H-210*Scale);
            const float Meters=FVector::Dist(Ship->GetActorLocation(),It->GetActorLocation())/100.f;
            Text(FString::Printf(TEXT("<> %s / %.0f m"),*It->GetEncounterLabel(),Meters),Screen.X,Screen.Y,.7f,FLinearColor(1,.8f,.4f));
            if(It->IsPlayerInRange()&&!It->IsAccepted())Text(TEXT("E / A  INTERACT"),Screen.X,Screen.Y+22*Scale,.7f);
        }
        if(S.run.phase==SS::Phase::Approach)
        {
            FVector2D Screen(W*.5f,130*Scale);
            if(!PlayerOwner->ProjectWorldLocationToScreen(GM->StationTarget,Screen))
            {
                const FVector Local=Ship->GetActorTransform().InverseTransformPosition(GM->StationTarget);
                Screen=FVector2D(Local.Y<0?100*Scale:W-300*Scale,H*.5f);
            }
            Screen.X=FMath::Clamp(Screen.X,100*Scale,W-300*Scale);Screen.Y=FMath::Clamp(Screen.Y,130*Scale,H-180*Scale);
            Text(TEXT("[ STATION ]  APPROACH"),Screen.X,Screen.Y,.9f,FLinearColor(.45f,.9f,1));
        }
    }
    if(auto* Walker=Cast<ASSWalker>(UGameplayStatics::GetPlayerPawn(this,0)))
    {
        for(TActorIterator<ASSStation> It(GetWorld());It;++It)
        {
            FString Label;if(It->NearestService(Walker->GetActorLocation(),Label)!=ESSPanel::None)
                Text(TEXT("E / A   ")+Label,W*.5f-200*Scale,H-80*Scale,.9f);
        }
        Text(TEXT("W A S D / left stick: walk   |   Shift / X: run   |   Esc / Menu: shell"),Margin,H-35*Scale,.65f);
    }
    const bool Dialogue=GM->Announcement.StartsWith(TEXT("Acornaut:"))||GM->Announcement.StartsWith(TEXT("Dockmaster:"));
    if(GM->AnnouncementSeconds>0 && (S.settings.subtitles || !Dialogue))
    {
        DrawRect(FLinearColor(.02f,.025f,.05f,.88f),Margin,65*Scale,W-2*Margin,48*Scale);
        Text(GM->Announcement,Margin+12*Scale,77*Scale,.75f);
    }
    if(GM->IsMenuOpen())
    {
        const float PW=FMath::Min(900*Scale,W-80*Scale),X=(W-PW)*.5f,Y=H*.13f;
        DrawRect(FLinearColor(.012f,.02f,.04f,.97f),X,Y,PW,H*.77f);
        DrawRect(FLinearColor(.4f,.8f,.9f),X,Y,5*Scale,H*.77f);
        Text(GM->PanelTitle,X+30*Scale,Y+24*Scale,1.3f,FLinearColor(.8f,.92f,1));
        Text(GM->PanelDetail,X+30*Scale,Y+72*Scale,.7f,FLinearColor(.68f,.75f,.85f));
        const int Lines=1+GM->PanelDetail.CountChar(TCHAR('\n'));
        float RowY=Y+(115+Lines*20)*Scale;
        const float RowH=FMath::Min(40*Scale,(Y+H*.7f-RowY)/FMath::Max(1,GM->Entries.Num()));
        for(int I=0;I<GM->Entries.Num();++I)
        {
            const auto& Entry=GM->Entries[I];
            const bool Selected=I==GM->SelectedEntry;
            DrawRect(Selected?FLinearColor(.075f,.18f,.25f):FLinearColor(.025f,.045f,.07f),X+25*Scale,RowY,PW-50*Scale,RowH-4*Scale);
            Text((Selected?TEXT(">  "):TEXT("   "))+Entry.Label,X+34*Scale,RowY+7*Scale,.76f,Entry.Enabled?FLinearColor(.92f,.95f,1):FLinearColor(.36f,.4f,.47f));
            MenuBounds.Add(FBox2D(FVector2D(X+25*Scale,RowY),FVector2D(X+PW-25*Scale,RowY+RowH-4*Scale))); RowY+=RowH;
        }
    }
}
