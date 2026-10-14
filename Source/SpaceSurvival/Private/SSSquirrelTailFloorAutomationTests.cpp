#include "Misc/AutomationTest.h"
#include "SSCharacterAuthoring.h"
#include "SSStation.h"
#include "SSStationPoseTransition.h"
#include "SSStationTailFloor.h"
#include "Animation/AnimSequence.h"
#include "Components/SkeletalMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "Misc/PackageName.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#if WITH_EDITOR
#include "Rendering/SkeletalMeshModel.h"
#endif

#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSquirrelTailFloor, "SpaceSurvival.Integration.SquirrelTailFloor",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSSquirrelTailFloor::RunTest(const FString &)
{
    const FString Base = TEXT("/Game/SpaceSurvival/Licensed/HeroReplacement/Final/");
    if (!FPackageName::DoesPackageExist(Base + TEXT("SK_SquirrelHeroReplacement")))
    {
        AddInfo(TEXT("Private replacement squirrel is not installed; exact surface acceptance remains unverified."));
        return true;
    }
    auto *Mesh =
        LoadObject<USkeletalMesh>(nullptr, *(Base + TEXT("SK_SquirrelHeroReplacement.SK_SquirrelHeroReplacement")));
    if (!TestNotNull(TEXT("Load the actual squirrel surface"), Mesh))
        return false;
    TSharedPtr<FJsonObject> Measurement;
    const FString Json = USSCharacterAuthoringLibrary::MeasureReplacementTailEnvelopes(Mesh);
    if (!TestTrue(TEXT("Read native seven-bone surface measurement"),
                  FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), Measurement) &&
                      Measurement.IsValid() && Measurement->GetBoolField(TEXT("success"))))
    {
        AddError(Json);
        return false;
    }
    TMap<FName, FBox> Envelopes;
    for (const auto &Value : Measurement->GetArrayField(TEXT("envelopes")))
    {
        const auto &Entry = Value->AsObject();
        const auto &Min = Entry->GetArrayField(TEXT("min"));
        const auto &Max = Entry->GetArrayField(TEXT("max"));
        Envelopes.Add(FName(Entry->GetStringField(TEXT("bone"))),
                      FBox(FVector(Min[0]->AsNumber(), Min[1]->AsNumber(), Min[2]->AsNumber()),
                           FVector(Max[0]->AsNumber(), Max[1]->AsNumber(), Max[2]->AsNumber())));
    }
    struct FMeasurementWorld
    {
        UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
        FMeasurementWorld()
        {
            if (World)
                GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
        }
        ~FMeasurementWorld()
        {
            if (World)
            {
                World->DestroyWorld(false);
                GEngine->DestroyWorldContext(World);
            }
        }
    } Fixture;
    if (!TestNotNull(TEXT("Create isolated actual-pose world"), Fixture.World))
        return false;
    auto *Owner = Fixture.World->SpawnActor<AActor>();
    auto *Component = NewObject<USkeletalMeshComponent>(Owner);
    Owner->SetRootComponent(Component);
    Owner->AddInstanceComponent(Component);
    Component->SetSkeletalMesh(Mesh);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    Component->RegisterComponent();
    Component->SetAnimInstanceClass(USSStationPoseTransition::StaticClass());
    auto *Transition = Cast<USSStationPoseTransition>(Component->GetAnimInstance());
    if (!TestNotNull(TEXT("Use the real post-blend native pose constraint"), Transition))
        return false;
    const FReferenceSkeleton &Reference = Mesh->GetRefSkeleton();
    const auto &InverseReference = Mesh->GetRefBasesInvMatrix();
    const int32 TailRoot = Reference.FindBoneIndex(TEXT("tail_01"));
    struct FInfluence
    {
        int32 Bone;
        FVector Point;
        double Weight;
    };
    TArray<TArray<FInfluence>> TailVertices;
    for (const auto &Section : Mesh->GetImportedModel()->LODModels[0].Sections)
        for (const FSoftSkinVertex &Vertex : Section.SoftVertices)
        {
            bool IsTail = false;
            TArray<FInfluence> Influences;
            for (int32 Influence = 0; Influence < MAX_TOTAL_INFLUENCES; ++Influence)
                if (Vertex.InfluenceWeights[Influence])
                {
                    const int32 Bone = Section.BoneMap[Vertex.InfluenceBones[Influence]];
                    IsTail |= Bone == TailRoot || Reference.BoneIsChildOf(Bone, TailRoot);
                    Influences.Add({Bone, FVector(InverseReference[Bone].TransformPosition(Vertex.Position)),
                                    double(Vertex.InfluenceWeights[Influence]) / 65535.});
                }
            if (IsTail)
                TailVertices.Add(MoveTemp(Influences));
        }
    auto LowestSurface = [&]()
    {
        double Min = TNumericLimits<double>::Max();
        const auto &Pose = Component->GetComponentSpaceTransforms();
        for (const auto &Vertex : TailVertices)
        {
            FVector Point = FVector::ZeroVector;
            for (const FInfluence &Influence : Vertex)
                Point += Pose[Influence.Bone].TransformPosition(Influence.Point) * Influence.Weight;
            Min = FMath::Min(Min, Point.Z);
        }
        return Min;
    };
    auto Sample = [&](UAnimSequence *Clip, float Seconds, const TOptional<FPlane> &Floor)
    {
        // Each is a distinct pose evaluation, even though this deterministic fixture advances no world time.
        ++GFrameCounter;
        Transition->SetAnimationAsset(Clip, false, 1.f);
        Transition->SetRootMotionMode(ERootMotionMode::NoRootMotionExtraction);
        Transition->SetPosition(Seconds, false);
        Transition->SetExitTime(USSStationPoseTransition::BlendDuration);
        Transition->SetTailFloor(TEXT("tail_01"), Envelopes, Floor);
        Component->TickAnimation(0.f, false);
        Component->RefreshBoneTransforms();
        FPoseSnapshot Snapshot;
        Component->SnapshotPose(Snapshot);
        return Snapshot;
    };
    const double FloorZ = Mesh->GetBounds().GetBox().Min.Z + 1.;
    const FPlane Ground(FVector(0, 0, FloorZ), FVector::UpVector);
    const FPlane Air(FVector(0, 0, FloorZ - 500), FVector::UpVector);
    int32 CorrectedFrames = 0, Samples = 0;
    double BeforeMin = TNumericLimits<double>::Max(), AfterMin = TNumericLimits<double>::Max();
    for (const TCHAR *Name : {TEXT("JumpStart"), TEXT("JumpAir"), TEXT("JumpLand"), TEXT("Walk"), TEXT("Run")})
    {
        const FString Stem = FString(TEXT("A_")) + Name;
        auto *Clip = LoadObject<UAnimSequence>(nullptr, *(Base + Stem + TEXT(".") + Stem));
        if (!TestNotNull(*FString::Printf(TEXT("Load %s source clip"), Name), Clip))
            return false;
        const bool Overlay = FCString::Strcmp(Name, TEXT("Walk")) == 0 || FCString::Strcmp(Name, TEXT("Run")) == 0;
        auto *Land = LoadObject<UAnimSequence>(nullptr, *(Base + TEXT("A_JumpLand.A_JumpLand")));
        const float Duration = Overlay ? Land->GetPlayLength() : Clip->GetPlayLength();
        for (int32 Frame = 0; Frame <= FMath::CeilToInt(Duration * 60); ++Frame)
        {
            const float Seconds = FMath::Min(float(Frame) / 60.f, Duration);
            Transition->SetLandingTail(Overlay ? Land : nullptr, TEXT("tail_01"), Seconds);
            const FPoseSnapshot Original = Sample(Clip, FMath::Fmod(Seconds, Clip->GetPlayLength()), {});
            BeforeMin = FMath::Min(BeforeMin, LowestSurface());
            const FPoseSnapshot Clear = Sample(Clip, FMath::Fmod(Seconds, Clip->GetPlayLength()), Air);
            const FPoseSnapshot Protected = Sample(Clip, FMath::Fmod(Seconds, Clip->GetPlayLength()), Ground);
            if (!Original.bIsValid || !Clear.bIsValid || !Protected.bIsValid ||
                Protected.LocalTransforms.Num() != Reference.GetNum())
            {
                AddError(TEXT("Every measured sample must evaluate a complete actual mesh pose."));
                return false;
            }
            for (int32 Bone = 0; Bone < Reference.GetNum(); ++Bone)
            {
                if (!Original.LocalTransforms[Bone].Equals(Clear.LocalTransforms[Bone], 1.e-4))
                {
                    AddError(FString::Printf(TEXT("A floor far below altered authored airborne drag: clip=%s frame=%d "
                                                  "bone=%s original=%s clear=%s floor=%.4f"),
                                             Name, Frame, *Reference.GetBoneName(Bone).ToString(),
                                             *Original.LocalTransforms[Bone].ToString(),
                                             *Clear.LocalTransforms[Bone].ToString(), FloorZ - 500));
                    return false;
                }
                if (Bone != TailRoot && !Original.LocalTransforms[Bone].Equals(Protected.LocalTransforms[Bone], 1.e-4))
                {
                    AddError(TEXT("The floor constraint changed a body or internal tail joint."));
                    return false;
                }
            }
            if (!Original.LocalTransforms[TailRoot].Equals(Protected.LocalTransforms[TailRoot], 1.e-4))
                ++CorrectedFrames;
            if (!Original.LocalTransforms[TailRoot].GetTranslation().Equals(
                    Protected.LocalTransforms[TailRoot].GetTranslation(), 1.e-4))
            {
                AddError(TEXT("Tail root translation changed; the tail must stay attached."));
                return false;
            }
            const double Lowest = LowestSurface();
            AfterMin = FMath::Min(AfterMin, Lowest);
            if (!FMath::IsFinite(Lowest) || Lowest < FloorZ - .05)
            {
                AddError(
                    FString::Printf(TEXT("Actual deformed tail breaches floor: clip=%s time=%.4f min=%.4f floor=%.4f"),
                                    Name, Seconds, Lowest, FloorZ));
                return false;
            }
            ++Samples;
        }
    }
    AddInfo(FString::Printf(TEXT("TAIL_SURFACE samples=%d vertices=%d corrected=%d before=%.4f after=%.4f floor=%.4f"),
                            Samples, TailVertices.Num(), CorrectedFrames, BeforeMin, AfterMin, FloorZ));
    TestTrue(TEXT("The test reproduces a real authored surface breach and corrects it"),
             BeforeMin < FloorZ - 1. && CorrectedFrames > 0);
    return true;
}
#endif
