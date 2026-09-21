#include "SSCharacterAuthoring.h"
#if WITH_EDITOR
#include "Animation/AnimData/IAnimationDataController.h"
#include "Animation/AnimData/IAnimationDataModel.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/Skeleton.h"
#include "AssetCompilingManager.h"
#include "Components/SkeletalMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "Misc/PackageName.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/Package.h"
#endif

USkeleton *USSCharacterAuthoringLibrary::CreateAlienFemaleSkeleton(USkeletalMesh *PrivateMesh)
{
#if WITH_EDITOR
    const TCHAR *MeshPath = TEXT("/Game/SpaceSurvival/Licensed/AlienFemalePresentation/"
                                 "SK_AlienFemalePresentation.SK_AlienFemalePresentation");
    const TCHAR *PackagePath =
        TEXT("/Game/SpaceSurvival/Licensed/AlienFemalePresentation/SKEL_AlienFemalePresentation");
    const FString ObjectPath = FString(PackagePath) + TEXT(".SKEL_AlienFemalePresentation");
    if (!PrivateMesh || PrivateMesh->GetPathName() != MeshPath || FPackageName::DoesPackageExist(PackagePath) ||
        FindObject<USkeleton>(nullptr, *ObjectPath))
        return nullptr;
    const FReferenceSkeleton &Reference = PrivateMesh->GetRefSkeleton();
    if (Reference.GetNum() != 61 || Reference.GetBoneName(0) != TEXT("root") ||
        !Reference.GetRefBonePose()[0].Equals(FTransform::Identity, .001))
        return nullptr;
    for (const FTransform &Bone : Reference.GetRefBonePose())
        if (!Bone.GetScale3D().Equals(FVector::OneVector, .001) || Bone.ContainsNaN())
            return nullptr;
    // Match SkeletonFactory's supported native initialization without its modal error branches.
    // Python owns source hashes, output ownership, backups and saving this exact package.
    USkeleton *Skeleton = NewObject<USkeleton>(CreatePackage(PackagePath), TEXT("SKEL_AlienFemalePresentation"),
                                               RF_Public | RF_Standalone | RF_Transactional);
    if (!Skeleton->MergeAllBonesToBoneTree(PrivateMesh, false))
    {
        Skeleton->ClearFlags(RF_Public | RF_Standalone);
        return nullptr;
    }
    PrivateMesh->SetSkeleton(Skeleton);
    Skeleton->SetPreviewMesh(PrivateMesh);
    PrivateMesh->MarkPackageDirty();
    Skeleton->MarkPackageDirty();
    return Skeleton;
#else
    return nullptr;
#endif
}

FString USSCharacterAuthoringLibrary::GroundAlienFemaleClip(USkeletalMesh *PrivateMesh, UAnimSequence *PrivateClip,
                                                            bool Apply)
{
#if WITH_EDITOR
    const FString Base = TEXT("/Game/SpaceSurvival/Licensed/AlienFemalePresentation/");
    const TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetBoolField(TEXT("success"), false);
    auto Finish = [&Report](const FString &Error = FString())
    {
        if (!Error.IsEmpty())
            Report->SetStringField(TEXT("error"), Error);
        FString Json;
        FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Json));
        return Json;
    };
    bool AllowedClip = false;
    for (const TCHAR *Name : {TEXT("A_AlienFemaleIdle"), TEXT("A_AlienFemaleWalk"), TEXT("A_AlienFemaleRun")})
        AllowedClip |= PrivateClip && PrivateClip->GetPathName() == Base + Name + TEXT(".") + Name;
    if (!GEngine || !PrivateMesh || !AllowedClip ||
        PrivateMesh->GetPathName() != Base + TEXT("SK_AlienFemalePresentation.SK_AlienFemalePresentation") ||
        !PrivateMesh->GetSkeleton() ||
        PrivateMesh->GetSkeleton()->GetPathName() !=
            Base + TEXT("SKEL_AlienFemalePresentation.SKEL_AlienFemalePresentation") ||
        PrivateClip->GetSkeleton() != PrivateMesh->GetSkeleton())
        return Finish(TEXT("Only the exact private female mesh, skeleton and three baked clips are accepted."));
    UObject *Assets[] = {PrivateMesh, PrivateClip};
    FAssetCompilingManager::Get().FinishCompilationForObjects(Assets);
    auto *Model = PrivateClip->GetDataModel();
    Report->SetBoolField(TEXT("force_root_lock"), PrivateClip->bForceRootLock);
    Report->SetBoolField(TEXT("root_motion_enabled"), PrivateClip->bEnableRootMotion);
    Report->SetBoolField(TEXT("additive"), PrivateClip->IsValidAdditive());
    if (!Model || PrivateClip->bForceRootLock || PrivateClip->bEnableRootMotion || PrivateClip->IsValidAdditive())
        return Finish(TEXT("Expected an in-place, non-additive clip with root locking and root motion disabled."));
    const int32 Keys = Model->GetNumberOfKeys();
    const FFrameRate Rate = Model->GetFrameRate();
    const double Duration = PrivateClip->GetPlayLength();
    if (Keys < 2 || Keys > 4000 || Rate.Numerator <= 0 || Rate.Denominator <= 0 || Duration > 120.)
        return Finish(TEXT("Unexpected bounded clip timing."));
    TArray<FName> Names;
    Model->GetBoneTrackNames(Names);
    if (!Names.Contains(TEXT("root")) || PrivateMesh->GetRefSkeleton().GetNum() != 61 ||
        PrivateMesh->GetRefSkeleton().GetBoneName(0) != TEXT("root"))
        return Finish(TEXT("The measured mesh and clip must share their root bone."));
    TArray<FFrameNumber> Frames;
    for (int32 Index = 0; Index < Keys; ++Index)
        Frames.Add(FFrameNumber(Index));
    TMap<FName, TArray<FTransform>> Tracks;
    for (FName Name : Names)
    {
        Model->GetBoneTrackTransforms(Name, Frames, Tracks.Add(Name));
        if (Tracks[Name].Num() != Keys)
            return Finish(TEXT("Could not read every authored key."));
        for (const FTransform &Pose : Tracks[Name])
            if (Pose.ContainsNaN())
                return Finish(TEXT("The source clip contains a nonfinite transform."));
    }
    // This isolated world contains only a transient measuring component. It does not load a map,
    // possess a pawn, initialize a game instance, or touch the caller's editor world.
    struct FMeasurementWorld
    {
        UWorld *World = UWorld::CreateWorld(EWorldType::EditorPreview, false);
        FMeasurementWorld()
        {
            if (World)
                GEngine->CreateNewWorldContext(EWorldType::EditorPreview).SetCurrentWorld(World);
        }
        ~FMeasurementWorld()
        {
            if (World)
            {
                World->DestroyWorld(false);
                GEngine->DestroyWorldContext(World);
            }
        }
    } Measurement;
    if (!Measurement.World)
        return Finish(TEXT("Could not create an isolated measurement world."));
    auto *Owner = Measurement.World->SpawnActor<AActor>();
    if (!Owner)
        return Finish(TEXT("Could not create the transient measurement actor."));
    auto *Component = NewObject<USkeletalMeshComponent>(Owner);
    Owner->SetRootComponent(Component);
    Owner->AddInstanceComponent(Component);
    Component->SetSkeletalMesh(PrivateMesh);
    Component->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    Component->RegisterComponent();
    Component->PlayAnimation(PrivateClip, false);
    if (!Component->GetSingleNodeInstance())
        return Finish(TEXT("The measuring component could not evaluate the actual clip."));
    Component->GetSingleNodeInstance()->SetRootMotionMode(ERootMotionMode::NoRootMotionExtraction);
    const auto *Render = PrivateMesh->GetResourceForRendering();
    const auto *Weights = Component->GetSkinWeightBuffer(0);
    if (!Render || Render->LODRenderData.IsEmpty() || !Weights || !Weights->GetNeedsCPUAccess() ||
        !Render->LODRenderData[0].StaticVertexBuffers.PositionVertexBuffer.GetAllowCPUAccess())
        return Finish(TEXT("CPU-readable mesh and skin weights are required to measure actual soles."));
    const auto &LOD = Render->LODRenderData[0];
    auto BoundsAt = [&]()
    {
        Component->TickAnimation(0.f, false);
        Component->RefreshBoneTransforms();
        TArray<FMatrix44f> Matrices;
        TArray<FVector3f> Vertices;
        Component->GetCurrentRefToLocalMatrices(Matrices, 0);
        USkinnedMeshComponent::ComputeSkinnedPositions(Component, Vertices, Matrices, LOD, *Weights);
        FBox Bounds(ForceInit);
        for (const FVector3f &Vertex : Vertices)
            Bounds += FVector(Vertex);
        return Bounds;
    };
    Component->SetForceRefPose(true);
    const FBox Reference = BoundsAt();
    Component->SetForceRefPose(false);
    auto Sample = [&]()
    {
        TArray<FBox> Bounds;
        for (int32 Frame = 0; Frame < Keys; ++Frame)
        {
            Component->SetPosition(float(Rate.AsSeconds(FFrameTime(Frame))), false);
            Bounds.Add(BoundsAt());
        }
        return Bounds;
    };
    const TArray<FBox> Before = Sample();
    double Lowest = TNumericLimits<double>::Max();
    for (const FBox &Bounds : Before)
    {
        if (!Bounds.IsValid || Bounds.GetSize().Z < 40. || Bounds.GetSize().Z > 200.)
            return Finish(TEXT("An evaluated pose is not a finite body at the preserved imported scale."));
        Lowest = FMath::Min(Lowest, Bounds.Min.Z);
    }
    const double Offset = Reference.Min.Z - Lowest;
    if (!Reference.IsValid || !FMath::IsFinite(Offset) || FMath::Abs(Offset) > 15.)
        return Finish(TEXT("Measured offset exceeds the bounded sole-height correction."));
    Report->SetStringField(TEXT("clip"), PrivateClip->GetPathName());
    Report->SetNumberField(TEXT("keys"), Keys);
    Report->SetNumberField(TEXT("frame_rate_numerator"), Rate.Numerator);
    Report->SetNumberField(TEXT("frame_rate_denominator"), Rate.Denominator);
    Report->SetNumberField(TEXT("duration"), Duration);
    Report->SetNumberField(TEXT("reference_sole_z_cm"), Reference.Min.Z);
    Report->SetNumberField(TEXT("root_offset_z_cm"), Offset);
    Report->SetBoolField(TEXT("applied"), Apply);
    auto AddSamples = [&Report](const TCHAR *Field, const TArray<FBox> &Bounds)
    {
        TArray<TSharedPtr<FJsonValue>> Values;
        for (const FBox &Pose : Bounds)
            Values.Add(MakeShared<FJsonValueNumber>(Pose.Min.Z));
        Report->SetArrayField(Field, Values);
    };
    AddSamples(TEXT("sole_z_before_cm"), Before);
    if (Apply)
    {
        TArray<FVector> Positions, Scales;
        TArray<FQuat> Rotations;
        for (const FTransform &Pose : Tracks[TEXT("root")])
        {
            Positions.Add(Pose.GetTranslation() + FVector(0, 0, Offset));
            Rotations.Add(Pose.GetRotation());
            Scales.Add(Pose.GetScale3D());
        }
        auto &Controller = PrivateClip->GetController();
        Controller.OpenBracket(FText::FromString(TEXT("Align private female clip's measured sole")), false);
        const bool Written = Controller.SetBoneTrackKeys(TEXT("root"), Positions, Rotations, Scales, false);
        Controller.CloseBracket(false);
        if (!Written)
            return Finish(TEXT("Root-key write failed; do not save this derivative."));
        // SetBoneTrackKeys can report true even if its nested curve write fails. Read every
        // track back, including untouched ones, before trusting it or serializing the asset.
        for (FName Name : Names)
        {
            TArray<FTransform> Actual;
            Model->GetBoneTrackTransforms(Name, Frames, Actual);
            if (Actual.Num() != Keys)
                return Finish(TEXT("Authored key count changed after the correction."));
            for (int32 Frame = 0; Frame < Keys; ++Frame)
            {
                FTransform Expected = Tracks[Name][Frame];
                if (Name == TEXT("root"))
                    Expected.AddToTranslation(FVector(0, 0, Offset));
                if (!Actual[Frame].Equals(Expected, .001))
                    return Finish(TEXT("A rotation, scale, non-root key or root delta changed unexpectedly."));
            }
        }
        if (Model->GetNumberOfKeys() != Keys || Model->GetFrameRate() != Rate ||
            !FMath::IsNearlyEqual(double(PrivateClip->GetPlayLength()), Duration, .00001))
            return Finish(TEXT("Clip timing changed unexpectedly."));
        FAssetCompilingManager::Get().FinishCompilationForObjects(Assets);
        Component->InitAnim(true);
        Component->PlayAnimation(PrivateClip, false);
        Component->GetSingleNodeInstance()->SetRootMotionMode(ERootMotionMode::NoRootMotionExtraction);
        const TArray<FBox> After = Sample();
        double MaxError = 0.;
        for (int32 Frame = 0; Frame < Keys; ++Frame)
        {
            MaxError = FMath::Max(MaxError, (After[Frame].Min - Before[Frame].Min - FVector(0, 0, Offset)).Size());
            MaxError = FMath::Max(MaxError, (After[Frame].Max - Before[Frame].Max - FVector(0, 0, Offset)).Size());
        }
        Report->SetNumberField(TEXT("max_pose_translation_error_cm"), MaxError);
        AddSamples(TEXT("sole_z_after_cm"), After);
        // Recompression can move evaluated bounds by a fraction of a millimeter
        // even when the raw non-root keys remain identical (checked above).
        if (!FMath::IsFinite(MaxError) || MaxError > .05)
            return Finish(TEXT("Evaluated poses did not translate uniformly by the measured root offset."));
        PrivateClip->MarkPackageDirty();
    }
    Report->SetBoolField(TEXT("success"), true);
    Report->SetBoolField(TEXT("pose_and_timing_invariants_preserved"), true);
    return Finish();
#else
    return TEXT("{\"success\":false,\"error\":\"Editor-only authoring operation.\"}");
#endif
}
