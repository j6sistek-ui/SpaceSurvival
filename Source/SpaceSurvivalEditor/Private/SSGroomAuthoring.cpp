#include "SSGroomAuthoring.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "Dom/JsonObject.h"
#include "GroomAsset.h"
#include "HairDescription.h"
#include "Misc/PackageName.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"

namespace
{
constexpr const TCHAR *SilverRoot = TEXT("/Game/SpaceSurvival/Licensed/SilverPonytail_20261014/");

UGroomAsset *SilverSource(UObject *Object)
{
    UGroomAsset *Groom = Cast<UGroomAsset>(Object);
    return Groom && Groom->GetPathName().StartsWith(SilverRoot) ? Groom : nullptr;
}

FString ToJsonText(const TSharedRef<FJsonObject> &Object)
{
    FString Text;
    FJsonSerializer::Serialize(Object, TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Text));
    return Text;
}

TSharedPtr<FJsonValue> Number(double Value)
{
    return MakeShared<FJsonValueNumber>(Value);
}

FString Fail(const FString &Reason)
{
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("success"), false);
    Result->SetStringField(TEXT("error"), Reason);
    return ToJsonText(Result);
}
} // namespace

FString USSGroomAuthoring::ReadSilverStrands(UObject *Source)
{
    UGroomAsset *Groom = SilverSource(Source);
    if (!Groom)
        return Fail(TEXT("Only the private Silver ponytail namespace is supported"));
    const FHairDescription Description = Groom->GetHairDescription();
    const auto Positions = Description.VertexAttributes().GetAttributesRef<FVector3f>(HairAttribute::Vertex::Position);
    const auto Counts = Description.StrandAttributes().GetAttributesRef<int32>(HairAttribute::Strand::VertexCount);
    const auto Guides = Description.StrandAttributes().GetAttributesRef<int32>(HairAttribute::Strand::Guide);
    const auto UVs = Description.StrandAttributes().GetAttributesRef<FVector2f>(HairAttribute::Strand::RootUV);
    if (!Positions.IsValid() || !Counts.IsValid())
        return Fail(TEXT("Source has no editable strand description"));
    TArray<TSharedPtr<FJsonValue>> Curves;
    int32 Offset = 0;
    for (int32 Index = 0; Index < Description.GetNumStrands(); ++Index)
    {
        const FStrandID Strand(Index);
        const int32 Count = Counts[Strand];
        if (Count < 1 || Offset + Count > Description.GetNumVertices())
            return Fail(TEXT("Invalid source vertex span"));
        TSharedRef<FJsonObject> Curve = MakeShared<FJsonObject>();
        Curve->SetNumberField(TEXT("guide"), Guides.IsValid() ? Guides[Strand] : 0);
        const FVector2f UV = UVs.IsValid() ? UVs[Strand] : FVector2f::ZeroVector;
        Curve->SetArrayField(TEXT("uv"), {Number(UV.X), Number(UV.Y)});
        TArray<TSharedPtr<FJsonValue>> Points;
        for (int32 Vertex = 0; Vertex < Count; ++Vertex)
        {
            const FVector3f P = Positions[FVertexID(Offset++)];
            Points.Add(
                MakeShared<FJsonValueArray>(TArray<TSharedPtr<FJsonValue>>{Number(P.X), Number(P.Y), Number(P.Z)}));
        }
        Curve->SetArrayField(TEXT("points"), Points);
        Curves.Add(MakeShared<FJsonValueObject>(Curve));
    }
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("success"), Offset == Description.GetNumVertices());
    Result->SetStringField(TEXT("source"), Groom->GetPathName());
    Result->SetArrayField(TEXT("curves"), Curves);
    return ToJsonText(Result);
}

FString USSGroomAuthoring::CreateSilverStrands(UObject *Source, const FString &DescriptionJson,
                                               const FString &CandidateName, bool Apply)
{
    UGroomAsset *Groom = SilverSource(Source);
    if (!Groom || CandidateName.IsEmpty() || CandidateName.Len() > 64)
        return Fail(TEXT("Invalid source or candidate name"));
    for (TCHAR C : CandidateName)
        if (!FChar::IsAlnum(C) && C != TEXT('_'))
            return Fail(TEXT("Candidate name must be alphanumeric or underscore"));
    TSharedPtr<FJsonObject> Json;
    if (DescriptionJson.Len() > 100000000 ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(DescriptionJson), Json) || !Json.IsValid())
        return Fail(TEXT("Invalid description JSON"));
    const TArray<TSharedPtr<FJsonValue>> *Curves = nullptr;
    if (!Json->TryGetArrayField(TEXT("curves"), Curves) || Curves->Num() < 2 || Curves->Num() > 100000)
        return Fail(TEXT("Expected bounded curve array"));
    FHairDescription Description;
    int32 RenderCounts[2] = {0, 0};
    int32 GuideCounts[2] = {0, 0};
    for (const TSharedPtr<FJsonValue> &Value : *Curves)
    {
        const TSharedPtr<FJsonObject> *Curve = nullptr;
        if (!Value->TryGetObject(Curve))
            return Fail(TEXT("Invalid curve"));
        int32 Group = -1, Guide = -1;
        const TArray<TSharedPtr<FJsonValue>> *Points = nullptr;
        const TArray<TSharedPtr<FJsonValue>> *UV = nullptr;
        if (!(*Curve)->TryGetNumberField(TEXT("group"), Group) || Group < 0 || Group > 1 ||
            !(*Curve)->TryGetNumberField(TEXT("guide"), Guide) || Guide < 0 || Guide > 1 ||
            !(*Curve)->TryGetArrayField(TEXT("points"), Points) || Points->Num() < 2 || Points->Num() > 1024 ||
            !(*Curve)->TryGetArrayField(TEXT("uv"), UV) || UV->Num() != 2)
            return Fail(TEXT("Invalid group, guide, points or UV"));
        const FStrandID Strand = Description.AddStrand();
        SetHairStrandAttribute(Description, Strand, HairAttribute::Strand::VertexCount, Points->Num());
        SetHairStrandAttribute(Description, Strand, HairAttribute::Strand::GroupID, Group);
        SetHairStrandAttribute(Description, Strand, HairAttribute::Strand::Guide, Guide);
        SetHairStrandAttribute(Description, Strand, HairAttribute::Strand::RootUV,
                               FVector2f((*UV)[0]->AsNumber(), (*UV)[1]->AsNumber()));
        SetHairStrandAttribute(Description, Strand, HairAttribute::Strand::Width, 0.02f);
        for (const TSharedPtr<FJsonValue> &Point : *Points)
        {
            const TArray<TSharedPtr<FJsonValue>> *XYZ = nullptr;
            if (!Point->TryGetArray(XYZ) || XYZ->Num() != 3 || Description.GetNumVertices() > 2000000)
                return Fail(TEXT("Invalid or oversized point array"));
            double X, Y, Z;
            if (!(*XYZ)[0]->TryGetNumber(X) || !(*XYZ)[1]->TryGetNumber(Y) || !(*XYZ)[2]->TryGetNumber(Z) ||
                !FMath::IsFinite(X) || !FMath::IsFinite(Y) || !FMath::IsFinite(Z) || FMath::Abs(X) > 250 ||
                FMath::Abs(Y) > 250 || FMath::Abs(Z) > 250)
                return Fail(TEXT("Nonfinite or out-of-bounds point"));
            const FVertexID Vertex = Description.AddVertex();
            SetHairVertexAttribute(Description, Vertex, HairAttribute::Vertex::Position, FVector3f(X, Y, Z));
        }
        (Guide ? GuideCounts : RenderCounts)[Group]++;
    }
    if (RenderCounts[0] < 10 || RenderCounts[1] < 10 || GuideCounts[0] < 1 || GuideCounts[1] < 1)
        return Fail(TEXT("Both groups need render strands and guides"));
    const FString PackageName = FString(SilverRoot) + TEXT("Separated/") + CandidateName;
    if (FindPackage(nullptr, *PackageName) || FPackageName::DoesPackageExist(PackageName))
        return Fail(TEXT("Candidate already exists; refusing overwrite"));
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("success"), true);
    Result->SetBoolField(TEXT("applied"), Apply);
    Result->SetStringField(TEXT("path"), PackageName);
    Result->SetArrayField(TEXT("render_counts"), {Number(RenderCounts[0]), Number(RenderCounts[1])});
    Result->SetArrayField(TEXT("guide_counts"), {Number(GuideCounts[0]), Number(GuideCounts[1])});
    if (Apply)
    {
        UPackage *Package = CreatePackage(*PackageName);
        UGroomAsset *Candidate = DuplicateObject<UGroomAsset>(Groom, Package, *CandidateName);
        Candidate->SetFlags(RF_Public | RF_Standalone);
        Candidate->SetNumGroup(2);
        Candidate->CommitHairDescription(MoveTemp(Description), EHairDescriptionType::Source);
        Candidate->ValidateSimulationCache();
        if (!Candidate->CacheDerivedDatas())
            return Fail(TEXT("Candidate derived-data build failed; not saved"));
        Candidate->PostEditChange();
        Candidate->MarkPackageDirty();
        FAssetRegistryModule::AssetCreated(Candidate);
    }
    return ToJsonText(Result);
}
