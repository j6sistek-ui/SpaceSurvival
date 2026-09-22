#include "SSFlightHull.h"
#include "SSContentTypes.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#if WITH_EDITOR
#include "Engine/SkeletalMesh.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
#include "UObject/Package.h"
#endif

FString USSFlightHullAuthoringLibrary::AuthorPhoenixParkedPhysics(bool bApply, bool bReplaceOwnedAsset)
{
    auto Report = MakeShared<FJsonObject>();
    Report->SetBoolField(TEXT("success"), false);
#if WITH_EDITOR
    const FSSHullDefinition Definition(ESSHullIdentity::StellarPhoenix);
    auto *Mesh = LoadObject<USkeletalMesh>(nullptr, *Definition.MeshPath);
    UPhysicsAsset *Source = Mesh ? Mesh->GetPhysicsAsset() : nullptr;
    const int32 BodyIndex = Source ? Source->FindBodyIndex(TEXT("Body_Bone")) : INDEX_NONE;
    if (BodyIndex == INDEX_NONE || Source->SkeletalBodySetups.Num() != 1)
        Report->SetStringField(TEXT("error"), TEXT("Expected the supplied single Body_Bone physics asset"));
    else
    {
        const FKAggregateGeom &Original = Source->SkeletalBodySetups[BodyIndex]->AggGeom;
        FKAggregateGeom Filtered = Original;
        const auto &Skeleton = Mesh->GetRefSkeleton();
        const int32 BoneIndex = Skeleton.FindBoneIndex(TEXT("Body_Bone"));
        FTransform BoneToMesh = Skeleton.GetRefBonePose()[BoneIndex];
        for (int32 Parent = Skeleton.GetParentIndex(BoneIndex); Parent != INDEX_NONE;
             Parent = Skeleton.GetParentIndex(Parent))
            BoneToMesh *= Skeleton.GetRefBonePose()[Parent];
        const FTransform MeshToShip(FRotator(0.f, Definition.MeshYaw, 0.f), FVector::ZeroVector,
                                    FVector(Definition.HullScale));
        const FTransform BodyToShip = BoneToMesh * MeshToShip;
        TArray<int32> Removed;
        TArray<TSharedPtr<FJsonValue>> Rows;
        // The inspected source is thirteen boxes. Preserve their exact local geometry instead of
        // refitting the body, ramp or mounts. Only the measured coarse deployed-foot boxes go away.
        bool Supported = Original.GetElementCount() == 13 && Original.BoxElems.Num() == 13;
        for (int32 Index = 0; Index < Original.BoxElems.Num(); ++Index)
        {
            FKConvexElem Measurement;
            Measurement.ConvexFromBoxElem(Original.BoxElems[Index]);
            Measurement.BakeTransformToVerts();
            for (FVector &Vertex : Measurement.VertexData)
                Vertex = BodyToShip.TransformPosition(Vertex);
            Measurement.UpdateElemBox();
            const FBox Bounds = Measurement.ElemBox;
            const bool CoarseFoot = Bounds.Min.Z < 10.f && Bounds.Max.Z < 130.f;
            if (CoarseFoot)
                Removed.Add(Index);
            auto Row = MakeShared<FJsonObject>();
            Row->SetNumberField(TEXT("source_index"), Index);
            Row->SetStringField(TEXT("ship_min"), Bounds.Min.ToString());
            Row->SetStringField(TEXT("ship_max"), Bounds.Max.ToString());
            Row->SetBoolField(TEXT("included"), !CoarseFoot);
            Row->SetStringField(TEXT("reason"), CoarseFoot
                                                    ? TEXT("coarse foot envelope replaced by animated mesh parts")
                                                    : TEXT("supplied hull, mounts or open cargo ramp preserved"));
            Rows.Add(MakeShared<FJsonValueObject>(Row));
        }
        Supported = Supported && Removed == TArray<int32>({0, 10, 11});
        for (int32 Index = Removed.Num() - 1; Index >= 0; --Index)
            Filtered.BoxElems.RemoveAt(Removed[Index]);
        Report->SetStringField(TEXT("source_physics_asset"), Source->GetPathName());
        Report->SetArrayField(TEXT("shapes"), Rows);
        Report->SetNumberField(TEXT("source_shapes"), Original.GetElementCount());
        Report->SetNumberField(TEXT("removed_foot_envelopes"), Removed.Num());
        Report->SetNumberField(TEXT("parked_shapes"), Filtered.GetElementCount());
        const TCHAR *PackagePath = TEXT("/Game/SpaceSurvival/Licensed/PhoenixPresentation/PA_PhoenixParked");
        auto *Existing = LoadObject<UPhysicsAsset>(
            nullptr, TEXT("/Game/SpaceSurvival/Licensed/PhoenixPresentation/PA_PhoenixParked.PA_PhoenixParked"),
            nullptr, LOAD_NoWarn | LOAD_Quiet);
        if (!Supported)
            Report->SetStringField(TEXT("error"),
                                   TEXT("Source geometry changed; inspect measured rows before authoring"));
        else if (bApply && Existing && !bReplaceOwnedAsset)
            Report->SetStringField(TEXT("error"), TEXT("Existing parked asset requires verified script ownership"));
        else if (Existing &&
                 (Existing->SkeletalBodySetups.Num() != 1 || Existing->FindBodyIndex(TEXT("Body_Bone")) != BodyIndex))
            Report->SetStringField(TEXT("error"), TEXT("Owned parked asset structure changed"));
        else
        {
            Report->SetBoolField(TEXT("success"), true);
            Report->SetBoolField(TEXT("applied"), bApply);
            if (bApply)
            {
                UPhysicsAsset *Target = Existing ? Existing
                                                 : DuplicateObject<UPhysicsAsset>(Source, CreatePackage(PackagePath),
                                                                                  TEXT("PA_PhoenixParked"));
                Target->SetFlags(RF_Public | RF_Standalone);
                USkeletalBodySetup *Body = Target->SkeletalBodySetups[BodyIndex];
                Body->AggGeom = Filtered;
                Body->InvalidatePhysicsData();
                Body->CreatePhysicsMeshes();
                Target->MarkPackageDirty();
            }
        }
    }
#else
    Report->SetStringField(TEXT("error"), TEXT("Editor-only authoring"));
#endif
    FString Json;
    FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Json));
    return Json;
}
