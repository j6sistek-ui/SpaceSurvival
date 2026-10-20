#include "SSPlayableHeroTools.h"
#if WITH_EDITOR
#include "SSGameMode.h"
#include "SSGameInstance.h"
#include "SSPhase1Data.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "AssetCompilingManager.h"
#include "ClothingAsset.h"
#include "ClothingSystemRuntimeTypes.h"
#include "ChaosCloth/ChaosClothConfig.h"
#include "Components/SkeletalMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "Materials/Material.h"
#include "MaterialShared.h"
#include "Misc/FileHelper.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
#include "Rendering/SkeletalMeshModel.h"
#include "Rendering/SkeletalMeshLODModel.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/UnrealType.h"
#endif

bool USSPlayableHeroTools::BeginGameReview(UWorld *World, FName HeroId, bool ShowWardrobe)
{
#if WITH_EDITOR
    if (!World || !FParse::Param(FCommandLine::Get(), TEXT("SSPlayableHeroReview")) ||
        !FParse::Param(FCommandLine::Get(), TEXT("RenderOffscreen")) ||
        !FPaths::ProjectSavedDir().Replace(TEXT("\\"), TEXT("/")).Contains(TEXT("/.agent/local/StationReview/")))
        return false;
    auto *Mode = World->GetAuthGameMode<ASSGameMode>();
    auto *Instance = World->GetGameInstance<USSGameInstance>();
    if (!Mode || !Instance || !Mode->Tuning)
        return false;
    const auto Hero = Mode->Tuning->SelectHero(ESSHeroSlot::Walker, HeroId);
    if (!HeroId.IsNone() && Hero.Id != HeroId)
        return false;
    // Even the private review account is read-only. This exercises runtime selection in memory.
    Instance->AccountStorageBlocked = true;
    Instance->Session.account.hero = HeroId.IsNone() ? -1 : static_cast<int>(Hero.Identity);
    Mode->ShowHangar();
    Mode->WearHero();
    if (ShowWardrobe) Mode->OpenPanel(ESSPanel::Wardrobe);
    else Mode->ClosePanel();
    return Mode->WornHeroId() == Hero.Id;
#else
    return false;
#endif
}

FString USSPlayableHeroTools::InspectMesh(USkeletalMesh *Mesh)
{
#if WITH_EDITOR
    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetBoolField(TEXT("success"), false);
    if (Mesh && Mesh->GetSkeleton())
    {
        FAssetCompilingManager::Get().FinishAllCompilation();
        const auto *Render = Mesh->GetResourceForRendering();
        if (Render && !Render->LODRenderData.IsEmpty())
        {
            const auto &LOD = Render->LODRenderData[0];
            const auto &Weights = LOD.SkinWeightVertexBuffer;
            int32 BadWeights = 0, InvalidBones = 0, MissingMaterials = 0, MaxInfluences = 0;
            TArray<TSharedPtr<FJsonValue>> Errors;
            for (const auto &Section : LOD.RenderSections)
                for (uint32 V = Section.BaseVertexIndex; V < Section.BaseVertexIndex + Section.NumVertices; ++V)
                {
                    uint32 Sum = 0;
                    int32 Influences = 0;
                    for (uint32 I = 0; I < Weights.GetMaxBoneInfluences(); ++I)
                    {
                        const uint16 Weight = Weights.GetBoneWeight(V, I);
                        Sum += Weight;
                        if (!Weight)
                            continue;
                        ++Influences;
                        const uint32 Bone = Weights.GetBoneIndex(V, I);
                        if (!Section.BoneMap.IsValidIndex(Bone) ||
                            !Mesh->GetRefSkeleton().IsValidIndex(Section.BoneMap[Bone]))
                            ++InvalidBones;
                    }
                    MaxInfluences = FMath::Max(MaxInfluences, Influences);
                    // Imported uint8 weights are expanded to uint16 by the public accessor.
                    BadWeights += FMath::Abs(int32(Sum) - 65535) > 257;
                }
            for (const auto &Slot : Mesh->GetMaterials())
            {
                if (!Slot.MaterialInterface)
                {
                    ++MissingMaterials;
                    continue;
                }
                const auto *Resource = Slot.MaterialInterface->GetMaterial()->GetMaterialResource(GMaxRHIShaderPlatform);
                if (Resource)
                    for (const FString &Error : Resource->GetCompileErrors())
                        Errors.Add(MakeShared<FJsonValueString>(Slot.MaterialInterface->GetPathName() + TEXT(": ") + Error));
            }
            Report->SetNumberField(TEXT("triangles"), LOD.GetTotalFaces());
            Report->SetNumberField(TEXT("vertices"), LOD.GetNumVertices());
            Report->SetNumberField(TEXT("bones"), Mesh->GetRefSkeleton().GetNum());
            Report->SetNumberField(TEXT("bad_weight_sums"), BadWeights);
            Report->SetNumberField(TEXT("invalid_bone_indices"), InvalidBones);
            Report->SetNumberField(TEXT("maximum_influences"), MaxInfluences);
            Report->SetNumberField(TEXT("missing_materials"), MissingMaterials);
            Report->SetArrayField(TEXT("material_compile_errors"), Errors);
            Report->SetBoolField(TEXT("success"), !BadWeights && !InvalidBones && !MissingMaterials && Errors.IsEmpty());
        }
    }
    FString Text;
    FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Text));
    return Text;
#else
    return TEXT("{\"success\":false,\"error\":\"Editor-only inspection.\"}");
#endif
}

FString USSPlayableHeroTools::ConfigureCloth(USkeletalMesh *Mesh, const FString &SourceJson)
{
#if WITH_EDITOR
    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetBoolField(TEXT("success"), false);
    auto Finish = [&Report](const FString &Error = FString())
    {
        if (!Error.IsEmpty()) Report->SetStringField(TEXT("error"), Error);
        FString Text;
        FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Text));
        return Text;
    };
    if (!Mesh || !Mesh->GetPathName().StartsWith(TEXT("/Game/SpaceSurvival/Licensed/PlayableHeroes_20261020/Cloth/")))
        return Finish(TEXT("Only the private cloth hero is supported."));
    if (!Mesh->GetMeshClothingAssets().IsEmpty())
        return Finish(TEXT("Clothing is already configured; inspect it rather than overwriting."));
    FString Json;
    TSharedPtr<FJsonObject> Source;
    if (!FFileHelper::LoadFileToString(Json, *SourceJson) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), Source))
        return Finish(TEXT("Missing physical proxy source."));
    FAssetCompilingManager::Get().FinishAllCompilation();
    const auto &Ref = Mesh->GetRefSkeleton();
    TArray<FTransform> ComponentPose = Ref.GetRefBonePose();
    for (int32 I = 1; I < ComponentPose.Num(); ++I)
        ComponentPose[I] *= ComponentPose[Ref.GetParentIndex(I)];
    const auto Points = Source->GetObjectField(TEXT("bone_points_cm"));
    auto Vector = [](const TSharedPtr<FJsonValue> &V)
    {
        const auto &A = V->AsArray();
        return FVector(A[0]->AsNumber(), A[1]->AsNumber(), A[2]->AsNumber());
    };
    auto From = [&](const TCHAR *Bone) { return Vector(Points->Values[Bone]); };
    auto To = [&](const TCHAR *Bone) { return ComponentPose[Ref.FindBoneIndex(Bone)].GetLocation(); };
    const FVector SL = (From(TEXT("hand_l")) - From(TEXT("hand_r"))).GetSafeNormal();
    const FVector TL = (To(TEXT("hand_l")) - To(TEXT("hand_r"))).GetSafeNormal();
    const FVector SU = FVector::VectorPlaneProject(From(TEXT("head")) - From(TEXT("pelvis")), SL).GetSafeNormal();
    const FVector TU = FVector::VectorPlaneProject(To(TEXT("head")) - To(TEXT("pelvis")), TL).GetSafeNormal();
    const FVector SF = FVector::VectorPlaneProject(FVector::VectorPlaneProject(From(TEXT("ball_l")) - From(TEXT("foot_l")), SL), SU).GetSafeNormal();
    const FVector TF = FVector::VectorPlaneProject(FVector::VectorPlaneProject(To(TEXT("ball_l")) - To(TEXT("foot_l")), TL), TU).GetSafeNormal();
    const double Scale = FVector::Distance(To(TEXT("hand_l")), To(TEXT("hand_r"))) /
                         FVector::Distance(From(TEXT("hand_l")), From(TEXT("hand_r")));
    auto Transform = [&](const FVector &P)
    {
        const FVector D = P - From(TEXT("pelvis"));
        return To(TEXT("pelvis")) + Scale * (TL * FVector::DotProduct(D, SL) + TU * FVector::DotProduct(D, SU) + TF * FVector::DotProduct(D, SF));
    };
    if (FMath::Abs(Scale - 1.) > .01 || SF.IsNearlyZero() || TF.IsNearlyZero())
        return Finish(TEXT("Unexpected source/imported coordinate frame."));
    TArray<TSharedPtr<FJsonValue>> Parts;
    UPhysicsAsset *Collision = Mesh->GetPhysicsAsset()
        ? DuplicateObject<UPhysicsAsset>(Mesh->GetPhysicsAsset(), Mesh, TEXT("ClothBodyCollision")) : nullptr;
    if (!Collision) return Finish(TEXT("The imported body collision asset is required."));
    // Garment-control bones must not become colliders inside the cloth they control.
    Collision->SkeletalBodySetups.RemoveAll([](const auto &Body)
        { return !Body || Body->BoneName.ToString().StartsWith(TEXT("cloth_")); });
    Collision->ConstraintSetup.Empty();
    Collision->UpdateBodySetupIndexMap();
    Collision->UpdateBoundsBodiesArray();
    for (const auto &Value : Source->GetArrayField(TEXT("parts")))
    {
        const auto Part = Value->AsObject();
        const FString Slot = Part->GetStringField(TEXT("material_slot"));
        int32 SectionIndex = INDEX_NONE;
        const auto &Sections = Mesh->GetImportedModel()->LODModels[0].Sections;
        for (int32 I = 0; I < Sections.Num(); ++I)
            if (Mesh->GetMaterials()[Sections[I].MaterialIndex].MaterialSlotName.ToString() == Slot)
                SectionIndex = I;
        if (SectionIndex == INDEX_NONE)
            return Finish(TEXT("Missing separate cloth section: ") + Slot);
        // Use the supplied clean simulation cage directly. Extracting simulation from the dense
        // render cape fails the engine's degenerate-triangle check and is unnecessary here.
        auto *Asset = NewObject<UClothingAssetCommon>(Mesh,
            FName(*(TEXT("CA_") + Part->GetStringField(TEXT("name")))), RF_Transactional);
        auto *GuidProperty = FindFProperty<FStructProperty>(Asset->GetClass(), TEXT("AssetGuid"));
        if (!GuidProperty || GuidProperty->Struct != TBaseStructure<FGuid>::Get())
            return Finish(TEXT("Clothing asset GUID property is unavailable."));
        *GuidProperty->ContainerPtrToValuePtr<FGuid>(Asset) = FGuid::NewGuid();
        Asset->LodData.AddDefaulted();
        Asset->LodMap.Init(INDEX_NONE, Mesh->GetLODNum());
        Asset->ClothConfigs.Add(UChaosClothConfig::StaticClass()->GetFName(), NewObject<UChaosClothConfig>(Asset));
        auto *Shared = NewObject<UChaosClothSharedSimConfig>(Asset);
        Shared->IterationCount = 6;
        Shared->MaxIterationCount = 10;
        Shared->SubdivisionCount = 2;
        Asset->ClothConfigs.Add(UChaosClothSharedSimConfig::StaticClass()->GetFName(), Shared);
        Asset->PhysicsAsset = Collision;
        auto &Lod = Asset->LodData[0];
        auto &Physical = Lod.PhysicalMeshData;
        const auto &Vertices = Part->GetArrayField(TEXT("vertices_cm"));
        const auto &Triangles = Part->GetArrayField(TEXT("triangles"));
        const auto &Distances = Part->GetArrayField(TEXT("max_distance_cm"));
        Physical.Reset(Vertices.Num(), Triangles.Num() * 3);
        Asset->UsedBoneNames.Empty();
        for (const auto &Info : Ref.GetRefBoneInfo()) Asset->UsedBoneNames.Add(Info.Name);
        Asset->RefreshBoneMapping(Mesh);
        const int32 Root = Ref.FindBoneIndex(*Part->GetStringField(TEXT("root_bone")));
        FPointWeightMap Mask(Vertices.Num());
        Mask.Name = TEXT("SourcePinnedMaxDistance");
        Mask.CurrentTarget = uint8(EWeightMapTargetCommon::MaxDistance);
        Mask.bEnabled = true;
        for (int32 V = 0; V < Vertices.Num(); ++V)
        {
            Physical.Vertices[V] = FVector3f(Transform(Vector(Vertices[V])));
            Physical.Normals[V] = FVector3f::ZeroVector;
            Physical.BoneData[V].NumInfluences = 1;
            Physical.BoneData[V].BoneIndices[0] = Root;
            Physical.BoneData[V].BoneWeights[0] = 1.f;
            Mask.Values[V] = Distances[V]->AsNumber() * Scale;
        }
        const bool Flip = FVector::DotProduct(FVector::CrossProduct(SL, SU), SF) * FVector::DotProduct(FVector::CrossProduct(TL, TU), TF) < 0.;
        for (int32 T = 0; T < Triangles.Num(); ++T)
        {
            const auto &Indices = Triangles[T]->AsArray();
            const int32 A = Indices[0]->AsNumber(), B = Indices[Flip ? 2 : 1]->AsNumber(), C = Indices[Flip ? 1 : 2]->AsNumber();
            Physical.Indices[T * 3] = A; Physical.Indices[T * 3 + 1] = B; Physical.Indices[T * 3 + 2] = C;
            const FVector3f N = FVector3f::CrossProduct(Physical.Vertices[B] - Physical.Vertices[A], Physical.Vertices[C] - Physical.Vertices[A]);
            Physical.Normals[A] += N; Physical.Normals[B] += N; Physical.Normals[C] += N;
        }
        for (auto &Normal : Physical.Normals) Normal.Normalize();
        Lod.PointWeightMaps = {Mask};
        Lod.bUseMultipleInfluences = false;
        Lod.SkinningKernelRadius = 30.f;
        if (auto *Config = Asset->GetClothConfig<UChaosClothConfig>())
        {
            Config->CollisionThickness = .6f;
            Config->FrictionCoefficient = .4f;
            Config->DampingCoefficient = .12f;
            Config->bUseCCD = true;
            Config->bUseSelfCollisions = true;
            Config->SelfCollisionThickness = .4f;
            Config->bUseBendingElements = true;
            Config->BendingStiffnessWeighted = {.35f, .35f};
            Config->AnimDriveStiffness = {.05f, .05f};
        }
        Asset->ApplyParameterMasks();
        Physical.FindOrAddWeightMap(EWeightMapTargetCommon::MaxDistance) = Mask;
        Physical.CalculateInverseMasses();
        Physical.CalculateNumInfluences();
        Physical.CalculateTethers(true, true);
        Asset->CalculateReferenceBoneIndex();
        Asset->InvalidateAllCachedData();
        if (Mesh->GetClothingAssetIndex(Asset) == INDEX_NONE) Mesh->AddClothingAsset(Asset);
        if (!Asset->BindToSkeletalMesh(Mesh, 0, SectionIndex, 0))
            return Finish(TEXT("Could not bind cloth proxy: ") + Slot);
        auto &Model = Mesh->GetImportedModel()->LODModels[0];
        auto &Section = Model.Sections[SectionIndex];
        Section.ClothingData.AssetGuid = Asset->GetAssetGuid();
        Section.ClothingData.AssetLodIndex = 0;
        Section.CorrespondClothAssetIndex = Mesh->GetClothingAssetIndex(Asset);
        // The mesh rebuild uses source-section user data, rather than the live section alone.
        auto &User = Model.UserSectionsData.FindOrAdd(Section.OriginalDataSectionIndex);
        User.ClothingData = Section.ClothingData;
        User.CorrespondClothAssetIndex = Section.CorrespondClothAssetIndex;
        TSharedRef<FJsonObject> Entry = MakeShared<FJsonObject>();
        Entry->SetStringField(TEXT("section"), Slot);
        Entry->SetNumberField(TEXT("particles"), Vertices.Num());
        Entry->SetNumberField(TEXT("triangles"), Triangles.Num());
        Entry->SetNumberField(TEXT("fixed_particles"), Physical.NumFixedVerts);
        Parts.Add(MakeShared<FJsonValueObject>(Entry));
    }
    Mesh->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    Mesh->SetHasActiveClothingAssets(Mesh->ComputeActiveClothingAssets());
    Mesh->MarkPackageDirty();
    Report->SetArrayField(TEXT("parts"), Parts);
    TArray<UClothingAssetBase *> Bound;
    Mesh->GetClothingAssetsInUse(Bound);
    Report->SetNumberField(TEXT("bound_assets"), Bound.Num());
    Report->SetBoolField(TEXT("active_clothing"), Mesh->ComputeActiveClothingAssets());
    Report->SetBoolField(TEXT("success"), Bound.Num() == 4 && Parts.Num() == 4);
    return Finish();
#else
    return TEXT("{\"success\":false,\"error\":\"Editor-only clothing conversion.\"}");
#endif
}

FString USSPlayableHeroTools::ReadClothSimulation(USkeletalMeshComponent *Component)
{
#if WITH_EDITOR
    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    TArray<TSharedPtr<FJsonValue>> Parts;
    int32 Count = 0;
    bool Finite = true;
    if (Component)
    {
        Report->SetNumberField(TEXT("simulation_instances"), Component->GetClothingSimulationInstances().Num());
        Report->SetBoolField(TEXT("simulation_disabled"), Component->bDisableClothSimulation);
        Report->SetBoolField(TEXT("wait_for_cloth"), Component->bWaitForParallelClothTask);
        Report->SetBoolField(TEXT("mesh_has_clothing"), Component->GetSkeletalMeshAsset() && Component->GetSkeletalMeshAsset()->HasActiveClothingAssets());
    }
    if (Component)
        for (const auto &Pair : Component->GetCurrentClothingData_AnyThread())
        {
            FBox Bounds(ForceInit);
            FVector Sum = FVector::ZeroVector;
            for (const FVector3f &P : Pair.Value.Positions)
            {
                Finite &= !P.ContainsNaN();
                Bounds += FVector(P);
                Sum += FVector(P);
            }
            Count += Pair.Value.Positions.Num();
            Finite &= Bounds.IsValid && Bounds.GetSize().GetMax() < 500.;
            TSharedRef<FJsonObject> Part = MakeShared<FJsonObject>();
            Part->SetNumberField(TEXT("asset"), Pair.Key);
            Part->SetNumberField(TEXT("particles"), Pair.Value.Positions.Num());
            Part->SetNumberField(TEXT("sum_x"), Sum.X);
            Part->SetNumberField(TEXT("sum_y"), Sum.Y);
            Part->SetNumberField(TEXT("sum_z"), Sum.Z);
            Part->SetNumberField(TEXT("height_cm"), Bounds.GetSize().Z);
            Parts.Add(MakeShared<FJsonValueObject>(Part));
        }
    Report->SetArrayField(TEXT("parts"), Parts);
    Report->SetNumberField(TEXT("particles"), Count);
    Report->SetBoolField(TEXT("success"), Finite && Count == 585 && Parts.Num() == 4);
    FString Text;
    FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Text));
    return Text;
#else
    return TEXT("{\"success\":false,\"error\":\"Editor-only cloth inspection.\"}");
#endif
}

bool USSPlayableHeroTools::ConfigureCoating(UMaterial *Material, float Amount, float Roughness)
{
#if WITH_EDITOR
    if (!Material || !Material->GetPathName().StartsWith(TEXT("/Game/SpaceSurvival/Licensed/PlayableHeroes_20261020/")))
        return false;
    auto *Data = Material->GetEditorOnlyData();
    Data->ClearCoat.UseConstant = true;
    Data->ClearCoat.Constant = FMath::Clamp(Amount, 0.f, 1.f);
    Data->ClearCoatRoughness.UseConstant = true;
    Data->ClearCoatRoughness.Constant = FMath::Clamp(Roughness, 0.f, 1.f);
    Material->MarkPackageDirty();
    return true;
#else
    return false;
#endif
}

bool USSPlayableHeroTools::PosePreview(USkeletalMeshComponent *Component, UAnimSequence *Clip, float Seconds)
{
#if WITH_EDITOR
    if (!Component || !Clip || !Component->GetSkeletalMeshAsset() ||
        Clip->GetSkeleton() != Component->GetSkeletalMeshAsset()->GetSkeleton())
        return false;
    Component->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    Component->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    Component->PlayAnimation(Clip, false);
    if (!Component->GetSingleNodeInstance())
        return false;
    Component->GetSingleNodeInstance()->SetRootMotionMode(ERootMotionMode::NoRootMotionExtraction);
    Component->SetPosition(FMath::Clamp(Seconds, 0.f, Clip->GetPlayLength()), false);
    Component->TickAnimation(0.f, false);
    Component->RefreshBoneTransforms();
    Component->UpdateBounds();
    Component->MarkRenderDynamicDataDirty();
    return true;
#else
    return false;
#endif
}

FString USSPlayableHeroTools::MeasureMotion(USkeletalMesh *Mesh, UAnimSequence *Clip, int32 Samples)
{
#if WITH_EDITOR
    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetBoolField(TEXT("success"), false);
    auto Finish = [&Report](const FString &Error = FString())
    {
        if (!Error.IsEmpty())
            Report->SetStringField(TEXT("error"), Error);
        FString Text;
        FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Text));
        return Text;
    };
    if (!Mesh || !Clip || Mesh->GetSkeleton() != Clip->GetSkeleton() || Clip->GetPlayLength() <= 0.f)
        return Finish(TEXT("Missing asset or skeleton mismatch."));
    FAssetCompilingManager::Get().FinishAllCompilation();
    UWorld *World = UWorld::CreateWorld(EWorldType::EditorPreview, false);
    if (!World)
        return Finish(TEXT("Could not create transient measuring world."));
    GEngine->CreateNewWorldContext(EWorldType::EditorPreview).SetCurrentWorld(World);
    AActor *Owner = World->SpawnActor<AActor>();
    auto *Component = NewObject<USkeletalMeshComponent>(Owner);
    Owner->SetRootComponent(Component);
    Owner->AddInstanceComponent(Component);
    Component->SetSkeletalMesh(Mesh);
    Component->RegisterComponent();
    auto Cleanup = [&]()
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
    };
    const auto *Render = Mesh->GetResourceForRendering();
    const auto *Weights = Component->GetSkinWeightBuffer(0);
    if (!Render || Render->LODRenderData.IsEmpty() || !Weights)
    {
        Cleanup();
        return Finish(TEXT("Missing LOD0 render skin buffers."));
    }
    const auto &LOD = Render->LODRenderData[0];
    TArray<TSharedPtr<FJsonValue>> Frames;
    bool Finite = true;
    Samples = FMath::Clamp(Samples, 2, 241);
    for (int32 Frame = 0; Frame < Samples; ++Frame)
    {
        const float Time = Clip->GetPlayLength() * Frame / float(Samples - 1);
        if (!PosePreview(Component, Clip, Time))
        {
            Cleanup();
            return Finish(TEXT("Animation evaluation failed."));
        }
        TArray<FMatrix44f> Matrices;
        TArray<FVector3f> Vertices;
        Component->GetCurrentRefToLocalMatrices(Matrices, 0);
        USkinnedMeshComponent::ComputeSkinnedPositions(Component, Vertices, Matrices, LOD, *Weights);
        FBox Bounds(ForceInit);
        for (const FVector3f &V : Vertices)
        {
            Finite &= !V.ContainsNaN();
            Bounds += FVector(V);
        }
        Finite &= Bounds.IsValid && Bounds.GetSize().GetMax() < 1000.;
        TSharedRef<FJsonObject> Entry = MakeShared<FJsonObject>();
        Entry->SetNumberField(TEXT("seconds"), Time);
        Entry->SetNumberField(TEXT("sole_z_cm"), Bounds.Min.Z);
        Entry->SetNumberField(TEXT("top_z_cm"), Bounds.Max.Z);
        Entry->SetNumberField(TEXT("height_cm"), Bounds.GetSize().Z);
        Frames.Add(MakeShared<FJsonValueObject>(Entry));
    }
    Report->SetStringField(TEXT("mesh"), Mesh->GetPathName());
    Report->SetStringField(TEXT("clip"), Clip->GetPathName());
    Report->SetNumberField(TEXT("triangles"), LOD.GetTotalFaces());
    Report->SetNumberField(TEXT("render_vertices"), LOD.GetNumVertices());
    Report->SetArrayField(TEXT("frames"), Frames);
    Report->SetBoolField(TEXT("success"), Finite);
    Cleanup();
    return Finish(Finite ? FString() : TEXT("Nonfinite or exploding skin bounds."));
#else
    return TEXT("{\"success\":false,\"error\":\"Editor-only measurement.\"}");
#endif
}
