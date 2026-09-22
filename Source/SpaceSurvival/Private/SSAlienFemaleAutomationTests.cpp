#include "Misc/AutomationTest.h"
#include "SSPhase1Data.h"
#include "SSStation.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionTextureSampleParameter.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSFemaleWorld
{
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    FSSFemaleWorld()
    {
        if (World)
            GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    }
    ~FSSFemaleWorld()
    {
        if (World)
        {
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
        }
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSAlienFemaleVisibility, "SpaceSurvival.Integration.AlienFemaleVisibility",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSAlienFemaleVisibility::RunTest(const FString &)
{
    FSSFemaleWorld F;
    if (!TestNotNull(TEXT("Create isolated female visibility world"), F.World))
        return false;
    auto *Walker = F.World->SpawnActor<ASSWalker>();
    if (!TestNotNull(TEXT("Use the actual wardrobe walking pawn"), Walker))
        return false;
    Walker->DispatchBeginPlay();
    Walker->ApplyHero(TEXT("AlienFemale"));
    const FSSHeroDefinition Hero = Walker->GetHero();
    const FString PrivateMeshPath = TEXT("/Game/SpaceSurvival/Licensed/AlienFemalePresentation/"
                                         "SK_AlienFemalePresentation.SK_AlienFemalePresentation");
    TestEqual(TEXT("Wardrobe resolves the private normalized female mesh"), Hero.MeshPath, PrivateMeshPath);
    auto *Authored = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
    if (TestNotNull(TEXT("Inspect the actual serialized gameplay data asset"), Authored))
        TestEqual(TEXT("Serialized hero arrays resolve the repaired presentation too"),
                  Authored->SelectHero(ESSHeroSlot::Walker, TEXT("AlienFemale")).MeshPath, PrivateMeshPath);
    FSSHeroDefinition Legacy(ESSHeroIdentity::AlienFemale);
    Legacy.FitHeight = 183.f;
    TestEqual(TEXT("Resolving the known legacy import preserves authored fit"), Legacy.ResolvedPresentation().FitHeight,
              183.f);
    // NOTCOOKED-BEGIN: deliberately absent custom assignment, never loaded by this regression.
    Legacy.WalkClipPath = TEXT("/Game/Custom/Walk.Walk");
    // NOTCOOKED-END
    TestEqual(TEXT("Custom animation assignments are never replaced by the legacy repair"),
              Legacy.ResolvedPresentation().MeshPath, Legacy.MeshPath);
    auto *Component = Walker->GetMesh();
    auto *Mesh = Component->GetSkeletalMeshAsset();
    if (!TestEqual(TEXT("Selected female remains the intended hero, without substituting another body"), Hero.Id,
                   FName(TEXT("AlienFemale"))) ||
        !TestNotNull(TEXT("The actual selected female mesh loads"), Mesh))
        return false;
    TestTrue(TEXT("The selected walking body is not hidden from the owning player"),
             Component->IsVisible() && !Component->bHiddenInGame && !Component->bOwnerNoSee && !Walker->IsHidden());
    const auto *Render = Mesh->GetResourceForRendering();
    const auto *Weights = Component->GetSkinWeightBuffer(0);
    if (!TestTrue(TEXT("Female LOD zero carries geometry and readable skin weights"),
                  Render && !Render->LODRenderData.IsEmpty() && Weights &&
                      Render->LODRenderData[0].StaticVertexBuffers.PositionVertexBuffer.GetAllowCPUAccess() &&
                      Weights->GetNeedsCPUAccess()))
        return false;
    const auto &LOD = Render->LODRenderData[0];
    int32 VisibleTriangles = 0;
    for (const auto &Section : LOD.RenderSections)
    {
        const bool Shown = !Section.bDisabled && Component->IsMaterialSectionShown(Section.MaterialIndex, 0);
        if (Shown)
            VisibleTriangles += Section.NumTriangles;
        auto *Material = Component->GetMaterial(Section.MaterialIndex);
        AddInfo(FString::Printf(TEXT("FEMALE_SECTION mesh=%s triangles=%u shown=%d material=%s"), *Mesh->GetPathName(),
                                Section.NumTriangles, Shown ? 1 : 0, *GetPathNameSafe(Material)));
        TestNotNull(TEXT("Female visible section resolves an authored material, not a missing import"), Material);
        if (Material)
            TestTrue(TEXT("Female body is an opaque or masked surface"),
                     Material->GetMaterial() && Material->GetMaterial()->MaterialDomain == MD_Surface &&
                         (Material->GetBlendMode() == BLEND_Opaque || Material->GetBlendMode() == BLEND_Masked));
    }
    TestTrue(TEXT("Female contains visible render triangles"), VisibleTriangles > 1000);
    if (auto *Material = Component->GetMaterial(0);
        Material && TestNotNull(TEXT("Female material has a real parent"), Material->GetMaterial()))
    {
        TestEqual(TEXT("The mesh uses the corrected material while the legacy material is preserved"),
                  Material->GetPathName(),
                  FString(TEXT("/Game/SpaceSurvival/Licensed/AlienFemalePresentation/"
                               "MI_AlienFemaleCorrected.MI_AlienFemaleCorrected")));
        struct FRole
        {
            const TCHAR *Parameter;
            const TCHAR *ObjectPath;
            TextureCompressionSettings Compression;
            bool SRGB;
            EMaterialSamplerType Sampler;
            const TCHAR *OriginalMask;
        };
        // Import metadata and exported pixels established that the two source names are swapped.
        const FRole Roles[] = {
            {TEXT("BaseColorTex"), TEXT("/Game/TripoModels/AlienFemale/T_AlienFemale_Normal.T_AlienFemale_Normal"),
             TC_Default, true, SAMPLERTYPE_Color, nullptr},
            {TEXT("NormalTex"), TEXT("/Game/TripoModels/AlienFemale/T_AlienFemale_BaseColor.T_AlienFemale_BaseColor"),
             TC_Normalmap, false, SAMPLERTYPE_Normal, nullptr},
            {TEXT("MetallicTex"),
             TEXT("/Game/SpaceSurvival/Licensed/AlienFemalePresentation/"
                  "T_AlienFemaleMetallicLinear.T_AlienFemaleMetallicLinear"),
             TC_Grayscale, false, SAMPLERTYPE_LinearGrayscale,
             TEXT("/Game/TripoModels/AlienFemale/T_AlienFemale_Metallic.T_AlienFemale_Metallic")},
            {TEXT("RoughnessTex"),
             TEXT("/Game/SpaceSurvival/Licensed/AlienFemalePresentation/"
                  "T_AlienFemaleRoughnessLinear.T_AlienFemaleRoughnessLinear"),
             TC_Grayscale, false, SAMPLERTYPE_LinearGrayscale,
             TEXT("/Game/TripoModels/AlienFemale/T_AlienFemale_Roughness.T_AlienFemale_Roughness")}};
        TestEqual(TEXT("Female keeps the supplied PBR master"), Material->GetMaterial()->GetPathName(),
                  FString(TEXT("/Game/TripoModels/Materials/M_Tripo_PBR_Master.M_Tripo_PBR_Master")));
        for (const FRole &Role : Roles)
        {
            UTexture *Texture = nullptr;
            const FString Label(Role.Parameter);
            TestTrue(Label + TEXT(" resolves its actual material parameter"),
                     Material->GetTextureParameterValue(FMaterialParameterInfo(Role.Parameter), Texture));
            auto *Image = Cast<UTexture2D>(Texture);
            if (!TestNotNull(Label + TEXT(" is a real texture"), Image))
                continue;
            TestEqual(Label + TEXT(" has the measured source role"), Image->GetPathName(), FString(Role.ObjectPath));
            TestEqual(Label + TEXT(" compression matches its sampler"), int32(Image->CompressionSettings),
                      int32(Role.Compression));
            TestEqual(Label + TEXT(" uses the correct colour space"), bool(Image->SRGB), Role.SRGB);
#if WITH_EDITOR
            bool FoundSampler = false;
            for (UMaterialExpression *Expression : Material->GetMaterial()->GetExpressions())
                if (const auto *Sample = Cast<UMaterialExpressionTextureSampleParameter>(Expression);
                    Sample && Sample->ParameterName == Role.Parameter)
                {
                    FoundSampler = true;
                    TestEqual(Label + TEXT(" master has the expected sampler role"), int32(Sample->SamplerType),
                              int32(Role.Sampler));
                }
            TestTrue(Label + TEXT(" exists in the supplied master graph"), FoundSampler);
            if (Role.OriginalMask)
            {
                auto *Original = LoadObject<UTexture2D>(nullptr, Role.OriginalMask);
                if (!TestNotNull(Label + TEXT(" original mask remains installed"), Original))
                    continue;
                TArray64<uint8> OriginalPixels, PrivatePixels;
                TestTrue(Label + TEXT(" private mask preserves every original source pixel"),
                         Original->Source.GetMipData(OriginalPixels, 0) && Image->Source.GetMipData(PrivatePixels, 0) &&
                             !OriginalPixels.IsEmpty() && OriginalPixels == PrivatePixels &&
                             Original->Source.GetSizeX() == Image->Source.GetSizeX() &&
                             Original->Source.GetSizeY() == Image->Source.GetSizeY());
            }
#endif
        }
    }
    auto Measure = [this, Walker, Component, &LOD, Weights](const FString &Pose, bool Log = true)
    {
        Component->TickAnimation(0.f, false);
        Component->RefreshBoneTransforms();
        Component->UpdateBounds();
        TArray<FMatrix44f> RefToLocal;
        TArray<FVector3f> Vertices;
        Component->GetCurrentRefToLocalMatrices(RefToLocal, 0);
        USkinnedMeshComponent::ComputeSkinnedPositions(Component, Vertices, RefToLocal, LOD, *Weights);
        FBox Bounds(ForceInit);
        for (const auto &Vertex : Vertices)
            Bounds += Component->GetComponentTransform().TransformPosition(FVector(Vertex));
        const double Deck = Walker->GetActorLocation().Z - Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
        const FVector Extent = Bounds.GetSize();
        if (Log)
            AddInfo(FString::Printf(TEXT("FEMALE_POSE pose=%s vertices=%d min=%s max=%s size=%s deck=%.4f"), *Pose,
                                    Vertices.Num(), *Bounds.Min.ToString(), *Bounds.Max.ToString(), *Extent.ToString(),
                                    Deck));
        TestTrue(*FString::Printf(TEXT("%s keeps a human-scale visible body above the deck"), *Pose),
                 Bounds.IsValid && Extent.Z > 100.f && Extent.Z < 240.f && Extent.X > 15.f && Extent.Y > 15.f &&
                     Bounds.Max.Z > Deck + 100.f && Bounds.Min.Z > Deck - 25.f && Bounds.Min.Z < Deck + 60.f);
        TestTrue(*FString::Printf(TEXT("%s remains beside its actual walking capsule"), *Pose),
                 FVector::Dist2D(Bounds.GetCenter(), Walker->GetActorLocation()) < 100.f);
        return Bounds;
    };
    Component->SetForceRefPose(true);
    const FBox Reference = Measure(TEXT("reference"));
    Component->SetForceRefPose(false);
    for (const FString &Path : {Hero.IdleClipPath, Hero.WalkClipPath, Hero.RunClipPath})
    {
        auto *Clip = LoadObject<UAnimSequence>(nullptr, *Path);
        if (!TestNotNull(TEXT("Selected female locomotion clip loads"), Clip))
            continue;
        Component->PlayAnimation(Clip, true);
        for (float Fraction : {0.f, .25f, .5f, .75f})
        {
            Component->SetPosition(Clip->GetPlayLength() * Fraction, false);
            Measure(FString::Printf(TEXT("%s@%.2f"), *Clip->GetName(), Fraction));
        }
        // Test the actual animated vertices at every stored sample. A fitted reference pose
        // alone previously passed while every idle/walk pose hovered several centimetres high.
        // Running may be airborne; each complete cycle must still have a planted support pose.
        const int32 Keys = Clip->GetNumberOfSampledKeys();
        if (!TestTrue(TEXT("Grounding regression evaluates a complete bounded animation cycle"),
                      Keys >= 2 && Keys <= 4000))
            continue;
        double Lowest = TNumericLimits<double>::Max(), Highest = -TNumericLimits<double>::Max();
        for (int32 Frame = 0; Frame < Keys; ++Frame)
        {
            Component->SetPosition(Clip->GetPlayLength() * Frame / float(Keys - 1), false);
            const FBox Pose = Measure(FString::Printf(TEXT("%s frame%d"), *Clip->GetName(), Frame), false);
            Lowest = FMath::Min(Lowest, Pose.Min.Z);
            Highest = FMath::Max(Highest, Pose.Min.Z);
        }
        TestTrue(*FString::Printf(TEXT("%s has a genuine planted pose at its reference sole height"), *Clip->GetName()),
                 FMath::Abs(Lowest - Reference.Min.Z) < .15);
        if (Path == Hero.IdleClipPath)
            TestTrue(TEXT("The entire standing cycle stays near the supported floor"), Highest - Reference.Min.Z < 2.);
        AddInfo(FString::Printf(TEXT("FEMALE_GROUNDING clip=%s samples=%d reference=%.4f lowest=%.4f highest=%.4f"),
                                *Clip->GetName(), Keys, Reference.Min.Z, Lowest, Highest));
    }
    return true;
}
#endif
