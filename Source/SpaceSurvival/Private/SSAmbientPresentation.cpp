#include "SSAmbientPresentation.h"
#include "SSShip.h"
#include "SSShipPresentation.h"
#include "SSSpaceLookData.h"
#include "SSSpaceScenery.h"
#include "Engine/StaticMeshActor.h"
#include "Components/SkyLightComponent.h"
#include "Engine/TextureCube.h"
#include "Engine/DirectionalLight.h"
#include "Components/DirectionalLightComponent.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/StaticMesh.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "Misc/PackageName.h"

namespace
{
constexpr int32 DustCount = 320;
constexpr double DustHalfWidth = 2400.0; // Fine passing grains, distinct from gameplay debris.
TAutoConsoleVariable<int32> DustEnabled(TEXT("ss.LocalDust"), 1,
                                        TEXT("Enable cosmetic local dust grains (0 disables)."));
TAutoConsoleVariable<int32> CloudEnabled(TEXT("ss.AtmosphereClouds"), 1,
                                         TEXT("Enable optional distant atmosphere cloud banks (0 disables)."));
TAutoConsoleVariable<int32> TrailEnabled(TEXT("ss.EngineTrails"), 1,
                                         TEXT("Enable optional Niagara engine ribbon trails (0 disables)."));
// RPT-20260915-08, "thrusters look like cubes". Shape/emission/scale are switchable so a set of candidates could
// be captured and chosen from, instead of one being picked on the implementer's taste. The owner chose the wide
// cone from that sheet, so these defaults are its settings; the variables stay for further review passes.
TAutoConsoleVariable<int32> ThrusterShape(TEXT("ss.ThrusterShape"), 1,
                                          TEXT("Engine core mesh: 0 cube, 1 cone, 2 sphere, 3 cylinder."));
TAutoConsoleVariable<float> ThrusterEmission(TEXT("ss.ThrusterEmission"), 6.f, TEXT("Engine core emissive strength."));
TAutoConsoleVariable<float> ThrusterScale(TEXT("ss.ThrusterScale"), 2.6f, TEXT("Engine core size multiplier."));
// The owner asked to try mixing materials for a distinctive drive, and named the galaxy shaders specifically.
// All of these are already owned. The additive unlit entries are authored for glowing effects; the opaque entries
// are surface materials used against their grain, which is the point of auditioning rather than assuming.
const TCHAR *ThrusterMaterialPaths[] = {
    TEXT("/Game/SpaceSurvival/Materials/M_Emissive.M_Emissive"),                                  //  0 current
    TEXT("/Game/SpaceSurvival/Licensed/Atmosphere/M_DeepSpaceExhaust.M_DeepSpaceExhaust"),        //  1 own exhaust
    TEXT("/Game/NiagaraExamples/Materials/MasterMaterials/M_Mesh_Add.M_Mesh_Add"),                //  2 mesh additive
    TEXT("/Game/NiagaraExamples/Materials/MasterMaterials/M_BrightCore.M_BrightCore"),            //  3 bright core
    TEXT("/Game/NiagaraExamples/Materials/MasterMaterials/M_FresnelGlow.M_FresnelGlow"),          //  4 edge glow
    TEXT("/Game/NiagaraExamples/Materials/MasterMaterials/M_Energy.M_Energy"),                    //  5 energy
    TEXT("/Game/NiagaraExamples/Materials/MasterMaterials/M_Flare.M_Flare"),                      //  6 flare
    TEXT("/Game/Sci_Fi_Weapons_VFX_AIO/Matetials/For_VFX/M_Simple_Beam_Aura.M_Simple_Beam_Aura"), //  7 beam aura
    TEXT("/Game/Sci_Fi_Weapons_VFX_AIO/Matetials/For_VFX/M_Deadly_Beam.M_Deadly_Beam"),           //  8 deadly beam
    TEXT("/Game/Sci_Fi_Weapons_VFX_AIO/Matetials/For_VFX/M_Fire_Rays.M_Fire_Rays"),               //  9 fire rays
    TEXT("/Game/Sci_Fi_Weapons_VFX_AIO/Matetials/For_VFX/M_Smoke_Ribbon.M_Smoke_Ribbon"),         // 10 smoke ribbon
    TEXT("/Game/Sci_Fi_Weapons_VFX_AIO/Matetials/M_Cable_Glow.M_Cable_Glow"),                     // 11 cable glow
    TEXT("/Game/NiagaraExamples/Materials/MI_RocketFlareCore.MI_RocketFlareCore"),                // 12 rocket flare
    TEXT("/Game/SpaceSurvival/Materials/M_Star.M_Star"),                                          // 13 own star
    TEXT("/Game/SpaceNebulaFantasy/Materials/M_Skybox_Nebula.M_Skybox_Nebula"),                   // 14 nebula
    TEXT("/Game/Vefects/Stylized_Galaxy_Shader/Galaxy/Materials/M_VFX_Lush_Galaxy_Shader."
         "M_VFX_Lush_Galaxy_Shader"),                        // 15 galaxy
    TEXT("/Game/CosmicMaterial/Material/M_Master.M_Master"), // 16 cosmic
};
TAutoConsoleVariable<int32> ThrusterMaterial(TEXT("ss.ThrusterMaterial"), 0,
                                             TEXT("Engine core material index into the audition table."));

/** One nested shell of the layered drive: which audition material it wears, its size relative to the single-core
 *  size, and a roll about the exhaust axis. A cone is rotationally symmetric, so roll only turns the material's
 *  mapping, which is the point: it stops two shells sharing a texture from reading as one surface. */
struct FSSThrusterLayer
{
    int32 Material;
    float Scale;
    float Roll;
};
/** The owner's requested mock-up stack, in their stated order. Nested rather than graded, deliberately. */
const FSSThrusterLayer ThrusterLayerStack[] = {
    {1, .90f, 0.f},   // M_DeepSpaceExhaust
    {4, 1.00f, 0.f},  // M_FresnelGlow
    {8, 1.10f, 0.f},  // M_Deadly_Beam
    {3, 1.05f, 90.f}, // M_BrightCore, rolled about the exhaust axis, still firing aft
    {9, 1.30f, 0.f},  // M_Fire_Rays
};
constexpr int32 ThrusterLayerCount = int32(UE_ARRAY_COUNT(ThrusterLayerStack));
TAutoConsoleVariable<int32> ThrusterLayered(TEXT("ss.ThrusterLayered"), 0,
                                            TEXT("Stack the layered drive mock-up instead of one core (0 off)."));
/** In the layered mock-up the long ribbon leaves the wing nozzles entirely and becomes one small plume on the
 *  centreline of the rear booster, which is what the owner asked to see. */
TAutoConsoleVariable<float> ThrusterTrailScale(TEXT("ss.ThrusterTrailScale"), .125f,
                                               TEXT("Ribbon size in the layered mock-up."));
/** Height of that centre plume on the hull. The nozzles sit at Z 10, on the nacelle axis; the big lit ring
 *  in the middle of the hull face is lower, and the owner wants the plume on the ring rather than on the
 *  small lit panel above it. Minus twenty seats the origin on the ring itself; a swept comparison put the
 *  panel at zero and the hull's lower lip near minus fifty. Held as a variable because the right number is
 *  a thing you look at rather than derive. */
TAutoConsoleVariable<float> ThrusterTrailHeight(TEXT("ss.ThrusterTrailHeight"), -20.f,
                                                TEXT("Centre plume height offset, cm, in the layered mock-up."));

/** Lowercased with spaces and underscores dropped, because vendors write "Emissive Gain", "Main Color" and
 *  "Additive_Color" for the same three ideas, and an exact-name list silently matches none of them. */
FString NormalizedParameter(FName Name)
{
    FString Text = Name.ToString().ToLower();
    Text.ReplaceInline(TEXT(" "), TEXT(""));
    Text.ReplaceInline(TEXT("_"), TEXT(""));
    return Text;
}

/** Shape and animation controls that happen to carry a colour or glow word. Driving an exponent or a panner
 *  speed with the drive intensity would distort the material rather than brighten it. */
bool IsShapeControl(const FString &Normalized)
{
    static const TCHAR *Rejects[] = {TEXT("exponent"), TEXT("power"),  TEXT("speed"),  TEXT("shift"),
                                     TEXT("distort"),  TEXT("invert"), TEXT("thresh"), TEXT("density"),
                                     TEXT("opacity"),  TEXT("rough"),  TEXT("metal"),  TEXT("fade"),
                                     TEXT("noise"),    TEXT("tiling"), TEXT("scale"),  TEXT("offset")};
    for (const TCHAR *Reject : Rejects)
        if (Normalized.Contains(Reject))
            return true;
    return false;
}

/** How well a vector parameter serves as the one the drive colour should own. Zero means leave it alone. */
int32 CoreColorPriority(FName Name)
{
    const FString Normalized = NormalizedParameter(Name);
    if (IsShapeControl(Normalized))
        return 0;
    if (Normalized == TEXT("tint"))
        return 100;
    if (Normalized.Contains(TEXT("tint")))
        return 90;
    if (Normalized == TEXT("color") || Normalized == TEXT("colour"))
        return 80;
    if (Normalized.Contains(TEXT("color")) || Normalized.Contains(TEXT("colour")))
        return 70;
    return 0;
}

/** How well a scalar parameter reads as how hot the core is. Zero means leave it alone. */
int32 CoreStrengthPriority(FName Name)
{
    const FString Normalized = NormalizedParameter(Name);
    if (IsShapeControl(Normalized))
        return 0;
    if (Normalized.Contains(TEXT("emissi")))
        return 100;
    if (Normalized.Contains(TEXT("intensity")))
        return 80;
    if (Normalized.Contains(TEXT("bright")))
        return 70;
    if (Normalized.Contains(TEXT("gain")))
        return 60;
    if (Normalized.Contains(TEXT("glow")))
        return 50;
    return 0;
}

/** True for the shapes whose length runs along the mesh's +Z (cone, cylinder), unlike the symmetric cube. */
bool ThrusterCoreIsAxial()
{
    const int32 Shaped = FMath::Clamp(ThrusterShape.GetValueOnGameThread(), 0, 3);
    return Shaped == 1 || Shaped == 3;
}

/** Pitching +90 maps the mesh's +Z onto the ship's -X, so a cone's apex trails aft like a real plume
 *  rather than standing on end. Without this the cone renders point-first out of the nozzle. */
FRotator ThrusterCoreRotation()
{
    return ThrusterCoreIsAxial() ? FRotator(90.f, 0.f, 0.f) : FRotator::ZeroRotator;
}
} // namespace

ASSAmbientPresentation::ASSAmbientPresentation()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickGroup = TG_PostPhysics;
    SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("PresentationRoot")));
    AmbientLight = CreateDefaultSubobject<USkyLightComponent>(TEXT("SpaceAmbientLight"));
    AmbientLight->SetupAttachment(RootComponent);
    AmbientLight->SetMobility(EComponentMobility::Movable);
    AmbientLight->SourceType = SLS_SpecifiedCubemap;
    AmbientLight->SetVisibility(false);
    VolumeFog = CreateDefaultSubobject<UExponentialHeightFogComponent>(TEXT("CloudVolumeGrid"));
    VolumeFog->SetupAttachment(RootComponent);
    // Engine scene registration rejects densities below DELTA / 1000.
    VolumeFog->SetFogDensity(.000001f);
    VolumeFog->SetFogInscatteringColor(FLinearColor::Black);
    VolumeFog->SetDirectionalInscatteringColor(FLinearColor::Black);
    VolumeFog->SetVolumetricFog(true);
    VolumeFog->SetVolumetricFogExtinctionScale(0.f);
    VolumeFog->SetVolumetricFogAlbedo(FColor::Black);
    VolumeFog->SetVolumetricFogEmissive(FLinearColor::Black);
    VolumeFog->SetVolumetricFogDistance(160000.f);
    VolumeFog->SetStartDistance(30000.f);
    VolumeFog->SetVolumetricFogStartDistance(25000.f);
    VolumeFog->SetVolumetricFogNearFadeInDistance(10000.f);
    VolumeFog->SetVisibility(false);
    Dust = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("LocalDust"));
    Dust->SetupAttachment(RootComponent);
    Dust->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Dust->SetGenerateOverlapEvents(false);
    Dust->SetCastShadow(false);
    Dust->SetCanEverAffectNavigation(false);
    Dust->SetVisibility(false);
    for (int32 Index = 0; Index < 2; ++Index)
    {
        auto *Cloud = CreateDefaultSubobject<UStaticMeshComponent>(*FString::Printf(TEXT("CloudBank%d"), Index));
        Cloud->SetupAttachment(RootComponent);
        Cloud->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Cloud->SetGenerateOverlapEvents(false);
        Cloud->SetCastShadow(false);
        // This mesh bounds a participating medium; its faces must not occlude the sky.
        Cloud->SetRenderInDepthPass(false);
        // Main-pass relevance must remain enabled for static volume voxelization.
        Cloud->SetCanEverAffectNavigation(false);
        Cloud->SetVisibility(false);
        CloudBanks.Add(Cloud);
        auto *Trail = CreateDefaultSubobject<UNiagaraComponent>(*FString::Printf(TEXT("EngineTrail%d"), Index));
        Trail->SetupAttachment(RootComponent);
        Trail->SetAutoActivate(false);
        Trail->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Trail->SetCastShadow(false);
        EngineTrails.Add(Trail);
        // Every engine always owns its full stack of shells. Components cannot be created outside the
        // constructor, so the unused ones are simply hidden when the mock-up is off.
        UStaticMeshComponent *Core = nullptr;
        for (int32 Layer = 0; Layer < ThrusterLayerCount; ++Layer)
        {
            auto *Shell =
                CreateDefaultSubobject<UStaticMeshComponent>(*FString::Printf(TEXT("EngineCore%d_%d"), Index, Layer));
            Shell->SetupAttachment(RootComponent);
            Shell->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Shell->SetGenerateOverlapEvents(false);
            Shell->SetCastShadow(false);
            Shell->SetCanEverAffectNavigation(false);
            Shell->SetVisibility(false);
            EngineCores.Add(Shell);
            if (Layer == 0)
                Core = Shell;
        }
        auto *Light = CreateDefaultSubobject<UPointLightComponent>(*FString::Printf(TEXT("EngineGlow%d"), Index));
        Light->SetupAttachment(Core);
        Light->SetIntensityUnits(ELightUnits::Lumens);
        Light->SetAttenuationRadius(700.f);
        Light->SetCastShadows(false);
        Light->SetVisibility(false);
        EngineLights.Add(Light);
    }
    // Six flanking arcs in three pairs. Pairs read as storm cells rather than as isolated sparks.
    for (int32 Index = 0; Index < 6; ++Index)
    {
        auto *Storm = CreateDefaultSubobject<UNiagaraComponent>(*FString::Printf(TEXT("AmbientStorm%d"), Index));
        Storm->SetupAttachment(RootComponent);
        Storm->SetAutoActivate(false);
        Storm->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Storm->SetGenerateOverlapEvents(false);
        Storm->SetCastShadow(false);
        Storm->SetVisibility(false);
        AmbientStorms.Add(Storm);
    }
}

void ASSAmbientPresentation::BeginPlay()
{
    Super::BeginPlay();
    const TCHAR *LookPath = TEXT("/Game/SpaceSurvival/Licensed/Atmosphere/DA_DeepSpaceLook");
    SpaceLook = FPackageName::DoesPackageExist(LookPath) ? LoadObject<USSSpaceLookData>(nullptr, LookPath) : nullptr;
    UMaterialInterface *Material = SpaceLook ? SpaceLook->CloudMaterial.Get() : nullptr;
    if (SpaceLook)
    {
        VolumeFog->SetFogDensity(SpaceLook->FogDensity);
        VolumeFog->SetFogHeightFalloff(0.f);
        // The flight backdrop is opaque geometry, not sky: AuthorContent spawns a 50 km sphere and
        // GenerateGeometry places the starfield at 40 km, and the sky material is authored is_sky=False
        // because is_sky=True rendered black. That is not a mystery worth solving here. A sky material
        // is routed out of the base pass into EMeshPass::SkyPass, which BasePassRendering.cpp:1512 runs
        // only when EngineShowFlags.Atmosphere is set, so the sky becomes conditional on a view flag the
        // offscreen capture path need not share. Bounding the fog instead removes the need for the flag:
        // the engine documents FogCutoffDistance as "Scene elements past this distance will not have fog
        // applied. This is useful for excluding skyboxes". At 20 km nothing exists between the playable
        // field and the cutoff, so the seam is invisible, while the starfield and backdrop keep true black.
        VolumeFog->SetFogCutoffDistance(2000000.f);
        // Second guard, so the furthest landmark inside the cutoff still keeps a fifth of its own value.
        VolumeFog->SetFogMaxOpacity(.8f);
        VolumeFog->SetVolumetricFogExtinctionScale(1.f);
        VolumeFog->SetVolumetricFogAlbedo(FColor::White);
        VolumeFog->SetVolumetricFogDistance(SpaceLook->FogDistance);
        AmbientLight->SetCubemap(SpaceLook->AmbientCubemap);
        AmbientLight->SetIntensity(SpaceLook->AmbientIntensity);
    }
    // The owned A23 Nerves beams, vendor misspelling included. Same system the ElectricalStorm hazard
    // uses, so distant weather and the dangerous version read as one phenomenon at different range.
    const TCHAR *StormPath = TEXT("/Game/NERVES/FX/NS_ElectircBeams_Blue.NS_ElectircBeams_Blue");
    if (auto *StormSystem = FPackageName::DoesPackageExist(TEXT("/Game/NERVES/FX/NS_ElectircBeams_Blue"))
                                ? LoadObject<UNiagaraSystem>(nullptr, StormPath, nullptr, LOAD_NoWarn | LOAD_Quiet)
                                : nullptr)
    {
        for (const auto &Storm : AmbientStorms)
            Storm->SetAsset(StormSystem);
        AmbientStormsAvailable = true;
    }
    auto *Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto *HullMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/SpaceSurvival/Materials/M_Hull.M_Hull"),
                                                        nullptr, LOAD_NoWarn | LOAD_Quiet);
    const bool Layered = ThrusterLayered.GetValueOnGameThread() != 0;
    const int32 Chosen =
        FMath::Clamp(ThrusterMaterial.GetValueOnGameThread(), 0, int32(UE_ARRAY_COUNT(ThrusterMaterialPaths)) - 1);
    // One material per shell. Off the mock-up every shell but the first is hidden, so they all take the single
    // chosen material and only the first is ever seen.
    TArray<UMaterialInterface *, TInlineAllocator<8>> LayerMaterials;
    for (int32 Layer = 0; Layer < ThrusterLayerCount; ++Layer)
    {
        const int32 MaterialIndex = FMath::Clamp(Layered ? ThrusterLayerStack[Layer].Material : Chosen, 0,
                                                 int32(UE_ARRAY_COUNT(ThrusterMaterialPaths)) - 1);
        auto *Loaded = LoadObject<UMaterialInterface>(nullptr, ThrusterMaterialPaths[MaterialIndex], nullptr,
                                                      LOAD_NoWarn | LOAD_Quiet);
        if (!Loaded)
        {
            // A borrowed material that fails to load must not silently leave the nozzles unlit.
            UE_LOG(LogTemp, Warning, TEXT("Thruster material %d (%s) did not load; using the project emissive."),
                   MaterialIndex, ThrusterMaterialPaths[MaterialIndex]);
            Loaded =
                LoadObject<UMaterialInterface>(nullptr, ThrusterMaterialPaths[0], nullptr, LOAD_NoWarn | LOAD_Quiet);
        }
        LayerMaterials.Add(Loaded);
    }
    auto *CoreMaterial = LayerMaterials[0];
    if (Cube && HullMaterial)
    {
        Dust->SetStaticMesh(Cube);
        DustMaterial = UMaterialInstanceDynamic::Create(HullMaterial, this);
        DustMaterial->SetVectorParameterValue(TEXT("Color"), FLinearColor(.30f, .36f, .42f));
        DustMaterial->SetVectorParameterValue(TEXT("Tint"), FLinearColor::White);
        DustMaterial->SetScalarParameterValue(TEXT("Metallic"), 0.f);
        DustMaterial->SetScalarParameterValue(TEXT("Roughness"), .9f);
        DustMaterial->SetScalarParameterValue(TEXT("Emission"), .15f);
        Dust->SetMaterial(0, DustMaterial);
        DustPositions.Reserve(DustCount);
        DustTransforms.Reserve(DustCount);
        DustSizes.Reserve(DustCount);
        FRandomStream Random(419731);
        for (int32 Index = 0; Index < DustCount; ++Index)
        {
            DustPositions.Add(FVector(Random.FRandRange(-DustHalfWidth, DustHalfWidth),
                                      Random.FRandRange(-DustHalfWidth, DustHalfWidth),
                                      Random.FRandRange(-DustHalfWidth, DustHalfWidth)));
            DustSizes.Add(Random.FRandRange(.25f, .85f));
            DustTransforms.Add(FTransform(FRotator(Random.FRandRange(0.f, 180.f), Random.FRandRange(0.f, 180.f), 0.f),
                                          FVector::ZeroVector, FVector::ZeroVector));
        }
        Dust->AddInstances(DustTransforms, false, false, false);
    }
    const TCHAR *ShapePaths[] = {TEXT("/Engine/BasicShapes/Cube.Cube"), TEXT("/Engine/BasicShapes/Cone.Cone"),
                                 TEXT("/Engine/BasicShapes/Sphere.Sphere"),
                                 TEXT("/Engine/BasicShapes/Cylinder.Cylinder")};
    const int32 ShapeIndex = FMath::Clamp(ThrusterShape.GetValueOnGameThread(), 0, 3);
    auto *CoreShape = LoadObject<UStaticMesh>(nullptr, ShapePaths[ShapeIndex]);
    if (!CoreShape)
        CoreShape = Cube;
    if (CoreShape && CoreMaterial)
        for (const auto &Core : EngineCores)
        {
            Core->SetStaticMesh(CoreShape);
            auto *LayerMaterial = LayerMaterials[EngineCoreMaterials.Num() % ThrusterLayerCount];
            auto *Dynamic = UMaterialInstanceDynamic::Create(LayerMaterial ? LayerMaterial : CoreMaterial, this);
            Dynamic->SetVectorParameterValue(TEXT("Color"), FLinearColor::White);
            Dynamic->SetScalarParameterValue(TEXT("Emission"), ThrusterEmission.GetValueOnGameThread());
            Core->SetMaterial(0, Dynamic);
            EngineCoreMaterials.Add(Dynamic);
        }
    // Ask each shell's material what it actually exposes, once. Setting a parameter a material does not declare
    // fails silently, so a borrowed material would otherwise sit at its authored colour and ignore the drive
    // entirely, which reads as a bug rather than as a deliberate look. Exactly one parameter of each kind is
    // claimed per shell: M_Emissive multiplies its Tint by its Color, so driving both would square the colour.
    CoreColorParameter.SetNum(ThrusterLayerCount);
    CoreStrengthParameter.SetNum(ThrusterLayerCount);
    for (int32 Layer = 0; Layer < ThrusterLayerCount; ++Layer)
    {
        auto *LayerMaterial = LayerMaterials[Layer];
        if (!LayerMaterial)
            continue;
        TArray<FMaterialParameterInfo> Parameters;
        TArray<FGuid> Ids;
        int32 BestColor = 0, BestStrength = 0;
        LayerMaterial->GetAllVectorParameterInfo(Parameters, Ids);
        for (const FMaterialParameterInfo &Parameter : Parameters)
        {
            const int32 Priority = CoreColorPriority(Parameter.Name);
            if (Priority > BestColor)
            {
                BestColor = Priority;
                CoreColorParameter[Layer] = Parameter.Name;
            }
        }
        Parameters.Reset();
        Ids.Reset();
        LayerMaterial->GetAllScalarParameterInfo(Parameters, Ids);
        for (const FMaterialParameterInfo &Parameter : Parameters)
        {
            const int32 Priority = CoreStrengthPriority(Parameter.Name);
            if (Priority > BestStrength)
            {
                BestStrength = Priority;
                CoreStrengthParameter[Layer] = Parameter.Name;
            }
        }
        // Logged by name so a capture run shows exactly what was driven, rather than leaving a silent no-op to
        // be mistaken for an authored look.
        UE_LOG(LogTemp, Log, TEXT("Thruster shell %d (%s) drives colour '%s' and strength '%s'."), Layer,
               *LayerMaterial->GetName(), *CoreColorParameter[Layer].ToString(),
               *CoreStrengthParameter[Layer].ToString());
        if (!Layered)
            break; // Only the first shell is ever visible off the mock-up.
    }
    CloudAvailable = Material && Cube;
    if (CloudAvailable)
    {
        for (int32 Index = 0; Index < CloudBanks.Num(); ++Index)
        {
            auto *Cloud = CloudBanks[Index].Get();
            Cloud->SetStaticMesh(Cube);
            // Engine cube is 100cm across; banks remain inside the 1.6km fog grid.
            Cloud->SetWorldScale3D(SpaceLook->CloudScale);
            auto *Dynamic = UMaterialInstanceDynamic::Create(Material, this);
            // Keep the authored volume parameters, including its soft boundary and lighting.
            Cloud->SetMaterial(0, Dynamic);
            CloudMaterials.Add(Dynamic);
        }
    }
    const TCHAR *TrailPath = TEXT("/Game/SpaceSurvival/Licensed/Atmosphere/NS_DeepSpaceExhaust");
    auto *System = FPackageName::DoesPackageExist(TrailPath) ? LoadObject<UNiagaraSystem>(nullptr, TrailPath) : nullptr;
    if (!System)
        System = LoadObject<UNiagaraSystem>(
            nullptr, TEXT("/Game/NiagaraExamples/FX_Weapons/Trails/NS_SimpleRibbonTrail.NS_SimpleRibbonTrail"), nullptr,
            LOAD_NoWarn | LOAD_Quiet);
    TrailsAvailable = System != nullptr;
    for (const auto &Trail : EngineTrails)
    {
        Trail->SetAsset(System);
        // Instance-only bounds: never mutate the shared vendor system.
        Trail->SetSystemFixedBounds(FBox(FVector(-6000, -400, -400), FVector(400, 400, 400)));
    }
}

void ASSAmbientPresentation::Follow(AActor *Actor)
{
    if (Followed.Get() == Actor)
        return;
    if (Followed.IsValid())
        RemoveTickPrerequisiteActor(Followed.Get());
    Followed = Actor;
    DustInitialized = false;
    CloudPositionInitialized = false;
    CloudTravel = FVector::ZeroVector;
    if (Actor)
        AddTickPrerequisiteActor(Actor);
    auto *Ship = Cast<ASSShip>(Actor);
    for (int32 Index = 0; Index < EngineTrails.Num(); ++Index)
    {
        auto *Trail = EngineTrails[Index].Get();
        Trail->DeactivateImmediate();
        Trail->AttachToComponent(Ship && Ship->HullMesh ? Ship->HullMesh.Get() : GetRootComponent(),
                                 FAttachmentTransformRules::KeepRelativeTransform);
        float Rear = -235.f;
        float Side = 80.f;
        if (Ship && Ship->HullMesh && Ship->HullMesh->GetStaticMesh())
        {
            const FBox Bounds = Ship->HullMesh->GetStaticMesh()->GetBoundingBox();
            Rear = Bounds.Min.X + 10.f;
            Side = Bounds.GetExtent().Y * .55f;
        }
        FVector ExhaustPosition(Rear, Index == 0 ? -Side : Side, 10.f);
        if (Ship && Ship->Presentation)
            Ship->Presentation->TryGetExhaustLocalPosition(Index, ExhaustPosition);
        Trail->SetRelativeLocation(ExhaustPosition);
        Trail->SetRelativeRotation(FRotator::ZeroRotator);
        for (int32 Layer = 0; Layer < ThrusterLayerCount; ++Layer)
        {
            const int32 Shell = Index * ThrusterLayerCount + Layer;
            if (!EngineCores.IsValidIndex(Shell))
                continue;
            EngineCores[Shell]->AttachToComponent(Ship && Ship->HullMesh ? Ship->HullMesh.Get() : GetRootComponent(),
                                                  FAttachmentTransformRules::KeepRelativeTransform);
            EngineCores[Shell]->SetRelativeLocation(ExhaustPosition + FVector(-18.f, 0.f, 0.f));
            // Roll turns the shell about the exhaust axis without changing where it fires.
            FRotator Orientation = ThrusterCoreRotation();
            Orientation.Roll += ThrusterLayerStack[Layer].Roll;
            EngineCores[Shell]->SetRelativeRotation(Orientation);
        }
    }
    RestartTrails = true;
}

void ASSAmbientPresentation::SetFlightVisible(bool Visible)
{
    if (FlightVisible == Visible)
        return;
    FlightVisible = Visible;
    if (SpaceLook && SpaceLook->bOverrideFlightKeyDirection && !SpaceLook->FlightKeyRotation.ContainsNaN())
    {
        if (Visible)
        {
            for (TActorIterator<ADirectionalLight> It(GetWorld()); It; ++It)
                if (auto *Light = Cast<UDirectionalLightComponent>(It->GetLightComponent());
                    Light && Light->ForwardShadingPriority == 2)
                {
                    FlightKey = *It;
                    PreviousKeyRotation = It->GetActorRotation();
                    PreviousKeyColor = Light->GetLightColor();
                    PreviousKeyIntensity = Light->Intensity;
                    It->SetActorRotation(SpaceLook->FlightKeyRotation);
                    break;
                }
        }
        else if (FlightKey.IsValid())
        {
            FlightKey->SetActorRotation(PreviousKeyRotation);
            if (auto *Light = Cast<UDirectionalLightComponent>(FlightKey->GetLightComponent()))
            {
                Light->SetLightColor(PreviousKeyColor);
                Light->SetIntensity(PreviousKeyIntensity);
            }
            FlightKey.Reset();
        }
    }
    if (!Visible)
    {
        Dust->SetVisibility(false);
        VolumeFog->SetVisibility(false);
        AmbientLight->SetVisibility(false);
        for (const auto &Cloud : CloudBanks)
            Cloud->SetVisibility(false);
        for (const auto &Trail : EngineTrails)
            Trail->DeactivateImmediate();
        for (const auto &Core : EngineCores)
            Core->SetVisibility(false);
        for (const auto &Light : EngineLights)
            Light->SetVisibility(false);
    }
    else
        RestartTrails = true;
}

void ASSAmbientPresentation::UpdateAreaStyle(float DeltaSeconds)
{
    if (!SpaceLook || SpaceLook->AreaRecipes.IsEmpty())
        return;
    if (!RegionScenery.IsValid())
        for (TActorIterator<ASSSpaceScenery> It(GetWorld()); It; ++It)
        {
            RegionScenery = *It;
            break;
        }
    if (!RegionScenery.IsValid())
        return;
    const auto Blend = RegionScenery->GetCurrentAreaBlend();
    if (!SpaceLook->AreaRecipes.IsValidIndex(Blend.First) || !SpaceLook->AreaRecipes.IsValidIndex(Blend.Second))
        return;
    const auto &A = SpaceLook->AreaRecipes[Blend.First];
    const auto &B = SpaceLook->AreaRecipes[Blend.Second];
    const float Smooth = AreaStyleInitialized ? 1.f - FMath::Exp(-FMath::Max(0.f, DeltaSeconds) * .3f) : 1.f;
    CurrentHazeColor = FMath::Lerp(CurrentHazeColor, FMath::Lerp(A.HazeColor, B.HazeColor, Blend.Alpha), Smooth);
    CurrentKeyColor = FMath::Lerp(CurrentKeyColor, FMath::Lerp(A.KeyColor, B.KeyColor, Blend.Alpha), Smooth);
    CurrentHazeDensity =
        FMath::Lerp(CurrentHazeDensity, FMath::Lerp(A.HazeDensity, B.HazeDensity, Blend.Alpha), Smooth);
    CurrentFogDensity = FMath::Lerp(CurrentFogDensity, FMath::Lerp(A.FogDensity, B.FogDensity, Blend.Alpha), Smooth);
    CurrentFogBrightness =
        FMath::Lerp(CurrentFogBrightness, FMath::Lerp(A.FogBrightness, B.FogBrightness, Blend.Alpha), Smooth);
    CurrentAmbientStormScale = FMath::Lerp(CurrentAmbientStormScale,
                                           FMath::Lerp(A.AmbientStormScale, B.AmbientStormScale, Blend.Alpha), Smooth);
    CurrentKeyIntensity =
        FMath::Lerp(CurrentKeyIntensity, FMath::Lerp(A.KeyIntensity, B.KeyIntensity, Blend.Alpha), Smooth);
    CurrentAmbientIntensity =
        FMath::Lerp(CurrentAmbientIntensity, FMath::Lerp(A.AmbientIntensity, B.AmbientIntensity, Blend.Alpha), Smooth);
    AreaStyleInitialized = true;
    // A restrained distance tint connects separated silhouettes without washing
    // the nearby ship. The bounded volume banks provide the denser local patches.
    // A luminous belt and an eerie murk are the same fog at different inscattering. Per zone, so one
    // region can silhouette dark rock against bright haze while another lights rock against dark murk.
    VolumeFog->SetFogInscatteringColor(CurrentHazeColor * CurrentFogBrightness);
    // Fog is a property of the region, not of the game. Crossing a boundary fades one zone's fog out
    // and the next one's in on the same smoothing as haze and key light, so an open region reads as
    // genuinely open rather than as the same space with the fog switched off.
    VolumeFog->SetFogDensity(FMath::Max(.000001f, CurrentFogDensity));
    for (const auto &Material : CloudMaterials)
    {
        Material->SetVectorParameterValue(TEXT("Color"), CurrentHazeColor);
        Material->SetScalarParameterValue(TEXT("Density"), CurrentHazeDensity);
    }
    AmbientLight->SetIntensity(CurrentAmbientIntensity);
    if (FlightKey.IsValid())
        if (auto *Light = Cast<UDirectionalLightComponent>(FlightKey->GetLightComponent()))
        {
            Light->SetLightColor(CurrentKeyColor);
            Light->SetIntensity(CurrentKeyIntensity);
        }
    if (!RegionSkyMaterial)
        for (TActorIterator<AStaticMeshActor> It(GetWorld()); It; ++It)
            if (It->ActorHasTag(TEXT("SpaceBackdrop")))
                RegionSkyMaterial = Cast<UMaterialInstanceDynamic>(It->GetStaticMeshComponent()->GetMaterial(0));
    if (RegionSkyMaterial)
        RegionSkyMaterial->SetVectorParameterValue(TEXT("AreaTint"), CurrentHazeColor * 3.f);
}

void ASSAmbientPresentation::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const bool Active = FlightVisible && Followed.IsValid();
    if (Active)
        UpdateAreaStyle(DeltaSeconds);
    const bool CloudsVisible = Active && CloudAvailable && CloudEnabled.GetValueOnGameThread() != 0;
    const FVector Center = Followed.IsValid() ? Followed->GetActorLocation() : FVector::ZeroVector;
    if (!CloudPositionInitialized)
    {
        LastCloudCenter = Center;
        CloudPositionInitialized = true;
    }
    const FVector CloudStep = Center - LastCloudCenter;
    // Banks remain world-stationary over ordinary travel. Bound the accumulated
    // offset so long runs cannot leave the local fog grid; never rotate with aim.
    if (CloudStep.SizeSquared() < FMath::Square(6000.0))
        CloudTravel = (CloudTravel - CloudStep).GetClampedToMaxSize(35000.0);
    else
        CloudTravel = FVector::ZeroVector;
    LastCloudCenter = Center;
    VolumeFog->SetVisibility(CloudsVisible);
    AmbientLight->SetVisibility(Active && SpaceLook && SpaceLook->AmbientCubemap);
    if (CloudsVisible)
        VolumeFog->SetWorldLocation(Center + FVector(0, 0, -10000000));
    const auto *Ship = Cast<ASSShip>(Followed.Get());
    UpdateDust(Center, Ship ? Ship->GetVelocity() : FVector::ZeroVector,
               Active && DustEnabled.GetValueOnGameThread() != 0);
    for (int32 Index = 0; Index < CloudBanks.Num(); ++Index)
    {
        CloudBanks[Index]->SetVisibility(CloudsVisible);
        if (CloudsVisible)
            CloudBanks[Index]->SetWorldLocation(Center + CloudTravel +
                                                (Index == 0 ? SpaceLook->CloudOffsetA : SpaceLook->CloudOffsetB));
    }
    // Three storm cells, 3 to 5 km out, offset laterally and vertically and never along the forward axis
    // where the Director admits real hazards. They are region weather seen at distance, not something to
    // dodge, so nothing here carries collision, damage or a telegraph.
    const bool StormsVisible =
        Active && AmbientStormsAvailable && CurrentAmbientStormScale > .01f && CloudEnabled.GetValueOnGameThread() != 0;
    // Distance here means AHEAD, not sideways. A large lateral offset at short range leaves the frustum,
    // which is exactly what a first attempt at "farther" got wrong. These sit 6 to 11 km down-range with a
    // lateral offset of roughly 15 to 20 degrees, so they read as weather on the horizon near the frame edge.
    // Two earlier attempts put these out of view: straight to the side leaves the frustum, and 6 to 11 km
    // down-range is past Niagara's own significance culling. These sit 1.8 to 2.8 km ahead with a lateral
    // offset of 0.7 to 1.1 km, well clear of the hazard corridor the Director admits inside, while staying
    // inside the view and inside the range at which the system still renders.
    static const FVector StormOffsets[] = {
        FVector(182000, 74000, 41000),   FVector(226000, 98000, 22000),    // cell one, ahead and right
        FVector(198000, -82000, -36000), FVector(254000, -108000, -21000), // cell two, ahead and left
        FVector(272000, 61000, -58000),  FVector(286000, 39000, -44000)    // cell three, further and low
    };
    for (int32 Index = 0; Index < AmbientStorms.Num(); ++Index)
    {
        auto *Storm = AmbientStorms[Index].Get();
        if (!Storm)
            continue;
        if (StormsVisible != Storm->IsVisible())
        {
            Storm->SetVisibility(StormsVisible);
            StormsVisible ? Storm->Activate(true) : Storm->Deactivate();
        }
        if (StormsVisible)
        {
            Storm->SetWorldLocation(Center + CloudTravel + StormOffsets[Index % 6]);
            Storm->SetWorldScale3D(FVector(CurrentAmbientStormScale));
            // A beam system's bounds are authored for close use; without this it culls before leaving frame.
            Storm->SetBoundsScale(24.f);
        }
    }
    const bool TrailsVisible =
        Active && Ship && !Ship->IsMoored() && TrailsAvailable && TrailEnabled.GetValueOnGameThread() != 0;
    float DrivePower = 0.f, Damage = 0.f;
    bool Boosting = false, Braking = false;
    if (Ship)
        Ship->GetDrivePresentation(DrivePower, Boosting, Braking, Damage);
    const float Pulse = .85f + .15f * FMath::Sin(GetWorld()->GetTimeSeconds() * (Damage > .1f ? 28.f : 9.f));
    const FLinearColor DriveColor = Damage > .1f && Pulse < .92f ? FLinearColor(1.f, .02f, .01f)
                                    : Braking                    ? FLinearColor(1.f, .18f, .02f)
                                    : Boosting                   ? FLinearColor(.18f, .62f, 1.2f)
                                                                 : FLinearColor(.03f, .22f, .82f);
    const float VisualPower = (Boosting ? 1.75f : Braking ? .55f : DrivePower) * Pulse;
    const bool LayeredNow = ThrusterLayered.GetValueOnGameThread() != 0;
    // Collected here and applied in the core pass below, which is where the mesh length is known.
    TArray<TOptional<FVector>, TInlineAllocator<4>> ExhaustPositions;
    ExhaustPositions.SetNum(EngineTrails.Num());
    for (int32 Index = 0; Index < ExhaustPositions.Num(); ++Index)
    {
        FVector ExhaustPosition;
        if (Ship && Ship->Presentation && Ship->Presentation->TryGetExhaustLocalPosition(Index, ExhaustPosition))
            ExhaustPositions[Index] = ExhaustPosition;
    }
    // The booster centre, known only once every nozzle has been read.
    TOptional<FVector> BoosterCentre;
    if (ExhaustPositions.Num() >= 2 && ExhaustPositions[0].IsSet() && ExhaustPositions[1].IsSet())
    {
        FVector Centre = (ExhaustPositions[0].GetValue() + ExhaustPositions[1].GetValue()) * .5f;
        Centre.Y = 0.f; // the booster sits on the hull's centreline whatever the nozzles do
        Centre.Z += ThrusterTrailHeight.GetValueOnGameThread();
        BoosterCentre = Centre;
    }
    for (int32 Index = 0; Index < EngineTrails.Num(); ++Index)
    {
        const auto &Trail = EngineTrails[Index];
        if (ExhaustPositions.IsValidIndex(Index) && ExhaustPositions[Index].IsSet())
            Trail->SetRelativeLocation(ExhaustPositions[Index].GetValue());
        // In the mock-up the long ribbon leaves the wing nozzles entirely: one small plume sits on the
        // centreline between them, on the rear booster, and the second ribbon is simply not shown.
        const bool ThisTrailVisible = TrailsVisible && (!LayeredNow || Index == 0);
        if (LayeredNow && Index == 0 && BoosterCentre.IsSet())
            Trail->SetRelativeLocation(BoosterCentre.GetValue());
        if (ThisTrailVisible)
        {
            if (RestartTrails || !Trail->IsActive())
                Trail->Activate(true);
            const float Grow = FMath::Clamp(.65f + VisualPower * .55f, .55f, 1.8f);
            Trail->SetRelativeScale3D(
                FVector(Grow * (LayeredNow ? FMath::Max(.01f, ThrusterTrailScale.GetValueOnGameThread()) : 1.f)));
        }
        else if (Trail->IsActive())
            Trail->DeactivateImmediate();
        Trail->SetVisibility(ThisTrailVisible);
    }
    const bool CoreVisible = Active && Ship && !Ship->IsMoored() && !EngineCoreMaterials.IsEmpty();
    for (int32 Index = 0; Index < EngineCores.Num(); ++Index)
    {
        const int32 Engine = Index / ThrusterLayerCount;
        const int32 Layer = Index % ThrusterLayerCount;
        auto *Core = EngineCores[Index].Get();
        // Off the mock-up only the first shell of each engine exists as far as the viewer is concerned.
        const bool ShellVisible = CoreVisible && (LayeredNow || Layer == 0);
        Core->SetVisibility(ShellVisible);
        if (ShellVisible)
        {
            const float Length = FMath::Clamp(18.f + VisualPower * 42.f, 14.f, 95.f);
            const float Width = FMath::Clamp(7.f + VisualPower * 4.f, 6.f, 18.f);
            // Engine cube is 100cm; extend rearward along the ship's +X/-X axis.
            const float ShapeScale = FMath::Max(.05f, ThrusterScale.GetValueOnGameThread());
            // A cone or cylinder is rotated so its length runs aft, so its axes swap relative to a cube.
            const bool Axial = ThrusterCoreIsAxial();
            const FVector CoreSize = Axial ? FVector(Width, Width, Length) : FVector(Length, Width, Width);
            // A shell's size is stated relative to the single-core size, so 90 per cent means ten per cent less.
            const float LayerScale = LayeredNow ? ThrusterLayerStack[Layer].Scale : 1.f;
            Core->SetRelativeScale3D(CoreSize * ShapeScale * LayerScale / 100.f);
            // Every basic shape straddles its own origin, so an axial mesh would bury its wide end in the
            // hull. Shift it aft by half its length to seat the flare at the nozzle lip.
            if (ExhaustPositions.IsValidIndex(Engine) && ExhaustPositions[Engine].IsSet())
                Core->SetRelativeLocation(
                    ExhaustPositions[Engine].GetValue() +
                    FVector(-18.f - (Axial ? Length * ShapeScale * LayerScale * .5f : 0.f), 0.f, 0.f));
            if (EngineCoreMaterials.IsValidIndex(Index) && CoreColorParameter.IsValidIndex(Layer))
            {
                const float Strength = (.45f + VisualPower * 1.15f) * ThrusterEmission.GetValueOnGameThread() / 3.f;
                if (!CoreColorParameter[Layer].IsNone())
                    EngineCoreMaterials[Index]->SetVectorParameterValue(CoreColorParameter[Layer], DriveColor);
                if (!CoreStrengthParameter[Layer].IsNone())
                    EngineCoreMaterials[Index]->SetScalarParameterValue(CoreStrengthParameter[Layer], Strength);
            }
            // One light per engine, carried by its first shell, not one per shell.
            if (Layer == 0 && EngineLights.IsValidIndex(Engine))
            {
                EngineLights[Engine]->SetLightColor(DriveColor.GetClamped());
                EngineLights[Engine]->SetIntensity(35.f + VisualPower * 180.f);
                EngineLights[Engine]->SetAttenuationRadius(170.f + VisualPower * 90.f);
            }
        }
        if (Layer == 0 && EngineLights.IsValidIndex(Engine))
            EngineLights[Engine]->SetVisibility(CoreVisible);
    }
    RestartTrails = false;
}

void ASSAmbientPresentation::ApplyWorldOffset(const FVector &InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    if (DustInitialized)
    {
        LastDustCenter += InOffset;
        for (auto &Position : DustPositions)
            Position += InOffset;
    }
    if (CloudPositionInitialized)
        LastCloudCenter += InOffset;
    // Clear world-space ribbon history across rebasing to avoid a screen-wide streak.
    for (const auto &Trail : EngineTrails)
        Trail->DeactivateImmediate();
    RestartTrails = true;
}

void ASSAmbientPresentation::UpdateDust(const FVector &Center, const FVector &Velocity, bool Visible)
{
    Dust->SetVisibility(Visible && DustMaterial != nullptr);
    if (!Visible || !DustMaterial || DustPositions.IsEmpty())
        return;
    // Positions remain world-stationary while the ship flies past. Only recycle
    // across the faded outer shell; never rotate the field with the camera.
    const FVector Travel = Center - LastDustCenter;
    const bool Teleported = DustInitialized && Travel.SizeSquared() > FMath::Square(6000.0);
    if (!DustInitialized || Teleported)
    {
        for (auto &Position : DustPositions)
            Position += DustInitialized ? Travel : Center - LastDustCenter;
        DustInitialized = true;
    }
    LastDustCenter = Center;
    const float SpeedFraction = FMath::Clamp(float(Velocity.Size() / 4200.0), 0.f, 1.5f);
    const FQuat TravelRotation = Velocity.IsNearlyZero() ? FQuat::Identity : Velocity.ToOrientationQuat();
    for (int32 Index = 0; Index < DustPositions.Num(); ++Index)
    {
        FVector Offset = DustPositions[Index] - Center;
        for (int32 Axis = 0; Axis < 3; ++Axis)
        {
            if (Offset[Axis] < -DustHalfWidth || Offset[Axis] > DustHalfWidth)
                Offset[Axis] -= FMath::FloorToDouble((Offset[Axis] + DustHalfWidth) / (2.0 * DustHalfWidth)) *
                                (2.0 * DustHalfWidth);
        }
        DustPositions[Index] = Center + Offset;
        const double EdgeDistance = DustHalfWidth - Offset.GetAbsMax();
        const float Edge = FMath::Clamp(float(EdgeDistance / 700.0), 0.f, 1.f);
        const float Bubble = FMath::Clamp(float((Offset.Size() - 200.0) / 300.0), 0.f, 1.f);
        const float Fade = Edge * Edge * (3.f - 2.f * Edge) * Bubble * Bubble * (3.f - 2.f * Bubble);
        DustTransforms[Index].SetLocation(DustPositions[Index]);
        DustTransforms[Index].SetRotation(TravelRotation);
        const float Width = DustSizes[Index] * Fade / 100.f;
        DustTransforms[Index].SetScale3D(FVector(Width * (1.f + SpeedFraction * 3.f), Width, Width));
    }
    // One component submission/render-state update for all grains.
    Dust->BatchUpdateInstancesTransforms(0, DustTransforms, true, true, Teleported);
}
