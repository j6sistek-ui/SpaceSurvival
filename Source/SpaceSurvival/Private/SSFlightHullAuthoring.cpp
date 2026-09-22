#include "SSFlightHull.h"
#include "SSContentTypes.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#if WITH_EDITOR
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
#include "PhysicsEngine/BodySetup.h"
#include "UObject/Package.h"
#endif

FString USSFlightHullAuthoringLibrary::AuthorPhoenixFlightHull(bool bApply, bool bReplaceOwnedAsset)
{
    auto Report = MakeShared<FJsonObject>();
    Report->SetBoolField(TEXT("success"), false);
#if WITH_EDITOR
    const FSSHullDefinition Definition(ESSHullIdentity::StellarPhoenix);
    auto *Mesh = LoadObject<USkeletalMesh>(nullptr, *Definition.MeshPath);
    UPhysicsAsset *Physics = Mesh ? Mesh->GetPhysicsAsset() : nullptr;
    const int32 BodyIndex = Physics ? Physics->FindBodyIndex(TEXT("Body_Bone")) : INDEX_NONE;
    if (BodyIndex == INDEX_NONE || Physics->SkeletalBodySetups.Num() != 1)
        Report->SetStringField(TEXT("error"), TEXT("Expected the supplied single Body_Bone physics asset"));
    else
    {
        const auto &Skeleton = Mesh->GetRefSkeleton();
        const int32 BoneIndex = Skeleton.FindBoneIndex(TEXT("Body_Bone"));
        FTransform BoneTransform = Skeleton.GetRefBonePose()[BoneIndex];
        for (int32 Parent = Skeleton.GetParentIndex(BoneIndex); Parent != INDEX_NONE;
             Parent = Skeleton.GetParentIndex(Parent))
            BoneTransform *= Skeleton.GetRefBonePose()[Parent];
        const FTransform MeshToShip(FRotator(0, Definition.MeshYaw, 0), FVector::ZeroVector,
                                    FVector(Definition.HullScale));
        const FTransform BodyToShip = BoneTransform * MeshToShip;
        const FKAggregateGeom &Source = Physics->SkeletalBodySetups[BodyIndex]->AggGeom;
        FKAggregateGeom Result;
        TArray<TSharedPtr<FJsonValue>> Shapes;
        int32 Excluded = 0;
        bool Supported = Source.GetElementCount() == 13;
        auto ConvexFrom = [](const FKShapeElem *Shape, FKConvexElem &Convex)
        {
            if (Shape->GetShapeType() == EAggCollisionShape::Convex)
                Convex = *static_cast<const FKConvexElem *>(Shape);
            else if (Shape->GetShapeType() == EAggCollisionShape::Box)
                Convex.ConvexFromBoxElem(*static_cast<const FKBoxElem *>(Shape));
            else
                return false;
            Convex.BakeTransformToVerts();
            return true;
        };
        for (int32 Index = 0; Index < Source.GetElementCount(); ++Index)
        {
            FKConvexElem Convex;
            const FKShapeElem *Shape = Source.GetElement(Index);
            if (!ConvexFrom(Shape, Convex))
            {
                Supported = false;
                continue;
            }
            for (FVector &Vertex : Convex.VertexData)
                Vertex = BodyToShip.TransformPosition(Vertex);
            Convex.UpdateElemBox();
            const FBox Bounds = Convex.ElemBox;
            // Verified against both authored poses: these three low envelopes follow the deployed
            // feet, while the fourth follows the open cargo ramp. None follows the folded flight pose.
            const bool Feet = Bounds.Min.Z < 10.f && Bounds.Max.Z < 130.f;
            const bool Ramp =
                Bounds.Min.X < -1250.f && Bounds.Max.X < -900.f && Bounds.Min.Z < 10.f && Bounds.Max.Z < 250.f;
            const bool Include = !Feet && !Ramp;
            auto Row = MakeShared<FJsonObject>();
            Row->SetNumberField(TEXT("source_index"), Index);
            Row->SetNumberField(TEXT("source_type"), int32(Shape->GetShapeType()));
            Row->SetStringField(TEXT("ship_min"), Bounds.Min.ToString());
            Row->SetStringField(TEXT("ship_max"), Bounds.Max.ToString());
            Row->SetBoolField(TEXT("included"), Include);
            Row->SetStringField(TEXT("reason"), Feet   ? TEXT("deployed feet; parked bone geometry owns contact")
                                                : Ramp ? TEXT("open cargo ramp; closed during flight")
                                                       : TEXT("supplied rigid hull"));
            Shapes.Add(MakeShared<FJsonValueObject>(Row));
            if (Include)
            {
                Convex.SetName(FName(*FString::Printf(TEXT("PhoenixBody_%d"), Index)));
                Convex.SetContributeToMass(false);
                Convex.ResetChaosConvexMesh();
                Result.ConvexElems.Add(Convex);
            }
            else
                ++Excluded;
        }
        // The authored engine boxes are a separate asset from the main skeletal physics asset.
        // Expand each only around its own pivot for the bounded visual tilt, preserving the gap.
        for (int32 Side = 0; Side < 2; ++Side)
        {
            const FString Name =
                Side == 0 ? TEXT("SM_Stellar_Phoenix_Engine_Left") : TEXT("SM_Stellar_Phoenix_Engine_Right");
            const FString Path = TEXT("/Game/Stellar_Phoenix/Spaceship/Meshes/") + Name + TEXT(".") + Name;
            auto *Engine = LoadObject<UStaticMesh>(nullptr, *Path);
            const UBodySetup *Setup = Engine ? Engine->GetBodySetup() : nullptr;
            FKConvexElem Original;
            if (!Setup || Setup->AggGeom.GetElementCount() != 1 || !ConvexFrom(Setup->AggGeom.GetElement(0), Original))
            {
                Supported = false;
                continue;
            }
            const FVector Pivot(Side == 0 ? 360.077391 : -360.117086, -523.686815, 344.90032);
            FKConvexElem Envelope;
            for (int32 Yaw = -12; Yaw <= 12; Yaw += 3)
                for (int32 Roll = -12; Roll <= 12; Roll += 3)
                {
                    const FQuat Tilt = FRotator(0.f, float(Yaw), float(Roll)).Quaternion();
                    for (const FVector &Vertex : Original.VertexData)
                        Envelope.VertexData.Add(
                            MeshToShip.TransformPosition(Pivot + Tilt.RotateVector(Vertex - Pivot)));
                }
            Envelope.UpdateElemBox();
            Envelope.SetName(FName(*Name));
            Envelope.SetContributeToMass(false);
            Result.ConvexElems.Add(Envelope);
            auto Row = MakeShared<FJsonObject>();
            Row->SetStringField(TEXT("source_mesh"), Path);
            Row->SetStringField(TEXT("ship_min"), Envelope.ElemBox.Min.ToString());
            Row->SetStringField(TEXT("ship_max"), Envelope.ElemBox.Max.ToString());
            Row->SetNumberField(TEXT("max_pivot_tilt_degrees"), 12);
            Shapes.Add(MakeShared<FJsonValueObject>(Row));
        }
        Report->SetStringField(TEXT("source_physics_asset"), Physics->GetPathName());
        Report->SetArrayField(TEXT("shapes"), Shapes);
        Report->SetNumberField(TEXT("source_shapes"), Source.GetElementCount());
        Report->SetNumberField(TEXT("excluded_deployment_shapes"), Excluded);
        Report->SetNumberField(TEXT("flight_shapes"), Result.ConvexElems.Num());
        Supported = Supported && Excluded == 4 && Result.ConvexElems.Num() == 11;
        const TCHAR *PackagePath = TEXT("/Game/SpaceSurvival/Licensed/PhoenixPresentation/DA_PhoenixFlightHull");
        auto *Existing = LoadObject<USSFlightHullProfile>(
            nullptr, TEXT("/Game/SpaceSurvival/Licensed/PhoenixPresentation/DA_PhoenixFlightHull.DA_PhoenixFlightHull"),
            nullptr, LOAD_NoWarn | LOAD_Quiet);
        if (!Supported)
            Report->SetStringField(TEXT("error"),
                                   TEXT("Source geometry changed; inspect measured rows before authoring"));
        else if (bApply && Existing && !bReplaceOwnedAsset)
            Report->SetStringField(TEXT("error"), TEXT("Existing profile requires verified script ownership"));
        else
        {
            Report->SetBoolField(TEXT("success"), true);
            Report->SetBoolField(TEXT("applied"), bApply);
            if (bApply)
            {
                auto *Profile =
                    Existing ? Existing
                             : NewObject<USSFlightHullProfile>(CreatePackage(PackagePath), TEXT("DA_PhoenixFlightHull"),
                                                               RF_Public | RF_Standalone);
                Profile->Body = NewObject<UBodySetup>(Profile, NAME_None, RF_Public);
                Profile->Body->AggGeom = Result;
                Profile->Body->CollisionTraceFlag = CTF_UseSimpleAsComplex;
                Profile->Body->InvalidatePhysicsData();
                Profile->Body->CreatePhysicsMeshes();
                FString Receipt;
                FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Receipt));
                Profile->SourceReceipt = Receipt;
                Profile->MarkPackageDirty();
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
