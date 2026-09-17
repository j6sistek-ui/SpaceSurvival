#include "SSShipPaint.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace
{
struct FPaintColour
{
    const TCHAR *Name;
    uint8 R, G, B;
};
// Ordinary finishes only: this is a garage, not a galaxy.
const FPaintColour Palette[SS::PaintColours] = {
    {TEXT("Arctic White"), 235, 236, 240}, {TEXT("Slate Grey"), 110, 118, 128},   {TEXT("Graphite Black"), 28, 30, 34},
    {TEXT("Crimson Red"), 176, 28, 38},    {TEXT("Signal Orange"), 232, 112, 20}, {TEXT("Amber Yellow"), 226, 178, 32},
    {TEXT("Forest Green"), 40, 110, 58},   {TEXT("Teal"), 24, 132, 136},          {TEXT("Cobalt Blue"), 32, 74, 168},
    {TEXT("Plum Purple"), 112, 44, 128}};
const TCHAR *Sections[SS::PaintSections] = {TEXT("Body"), TEXT("Wings"), TEXT("Engines"), TEXT("Weapons")};
// A plain material with a colour parameter, for hulls whose own materials expose none.
const TCHAR *FallbackMaterial = TEXT("/Game/SpaceSurvival/Materials/M_Hull.M_Hull");

bool Has(const FString &Name, std::initializer_list<const TCHAR *> Keys)
{
    for (const TCHAR *Key : Keys)
        if (Name.Contains(Key))
            return true;
    return false;
}

// The vector parameter that drives a material's colour, by the names vendors and the project use. Emissive,
// specular and mask parameters are never chosen, so paint cannot turn a running light into a wall of white.
bool ColourParameter(UMaterialInterface *Material, FName &OutName)
{
    if (!Material)
        return false;
    TArray<FMaterialParameterInfo> Infos;
    TArray<FGuid> Ids;
    Material->GetAllVectorParameterInfo(Infos, Ids);
    int32 Best = 0;
    for (const auto &Info : Infos)
    {
        FString Name = Info.Name.ToString().ToLower();
        Name.ReplaceInline(TEXT(" "), TEXT(""));
        Name.ReplaceInline(TEXT("_"), TEXT(""));
        if (Has(Name, {TEXT("emissive"), TEXT("emission"), TEXT("specular"), TEXT("normal"), TEXT("mask"), TEXT("glow"),
                       TEXT("subsurface")}))
            continue;
        int32 Score = 0;
        if (Has(Name, {TEXT("basecolor"), TEXT("albedo")}))
            Score = 4;
        else if (Has(Name, {TEXT("color"), TEXT("colour")}))
            Score = 3;
        else if (Name.Contains(TEXT("tint")))
            Score = 2;
        else if (Name.Contains(TEXT("diffuse")))
            Score = 1;
        if (Score > Best)
        {
            Best = Score;
            OutName = Info.Name;
        }
    }
    return Best > 0;
}
} // namespace

const TCHAR *SSPaint::SectionName(int32 Section)
{
    return Section >= 0 && Section < SS::PaintSections ? Sections[Section] : TEXT("");
}

const TCHAR *SSPaint::ColourName(int32 Colour)
{
    return Colour >= 0 && Colour < SS::PaintColours ? Palette[Colour].Name : TEXT("Factory finish");
}

FLinearColor SSPaint::Colour(int32 Colour)
{
    if (Colour < 0 || Colour >= SS::PaintColours)
        return FLinearColor::White;
    const auto &P = Palette[Colour];
    return FLinearColor::FromSRGBColor(FColor(P.R, P.G, P.B));
}

int32 SSPaint::SectionForMaterial(const FString &MaterialName)
{
    const FString Name = MaterialName.ToLower();
    if (Has(Name, {TEXT("windscreen"), TEXT("glass"), TEXT("window"), TEXT("cockpit"), TEXT("padding"), TEXT("nav"),
                   TEXT("light"), TEXT("emissive"), TEXT("canopy")}))
        return INDEX_NONE;
    if (Name.Contains(TEXT("wing")))
        return Wings;
    if (Has(Name, {TEXT("engine"), TEXT("thrust"), TEXT("exhaust"), TEXT("nozzle"), TEXT("booster")}))
        return Engines;
    if (Has(Name, {TEXT("weapon"), TEXT("gun"), TEXT("laser"), TEXT("cannon"), TEXT("turret")}))
        return Weapons;
    return Body;
}

void SSPaint::Apply(UStaticMeshComponent *Hull, const SS::Account &Account)
{
    if (!Hull || !Hull->GetStaticMesh())
        return;
    const auto &Slots = Hull->GetStaticMesh()->GetStaticMaterials();
    for (int32 Slot = 0; Slot < Slots.Num(); ++Slot)
    {
        UMaterialInterface *Base = Slots[Slot].MaterialInterface;
        if (!Base)
            continue;
        const int32 Section = SectionForMaterial(Base->GetName());
        const int32 Choice = Section == INDEX_NONE ? -1 : Account.paint[Section];
        if (Choice < 0 || Choice >= SS::PaintColours)
        {
            Hull->SetMaterial(Slot, Base);
            continue;
        }
        FName Parameter;
        UMaterialInterface *Source = Base;
        if (!ColourParameter(Source, Parameter))
        {
            Source = LoadObject<UMaterialInterface>(nullptr, FallbackMaterial);
            if (!ColourParameter(Source, Parameter))
            {
                Hull->SetMaterial(Slot, Base);
                continue;
            }
        }
        auto *Instance = UMaterialInstanceDynamic::Create(Source, Hull);
        Instance->SetVectorParameterValue(Parameter, Colour(Choice));
        Hull->SetMaterial(Slot, Instance);
    }
}
