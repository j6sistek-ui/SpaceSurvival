using UnrealBuildTool;
public class SpaceSurvival : ModuleRules
{
    public SpaceSurvival(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        CppStandard = CppStandardVersion.Cpp20;
        // ShipCore is the flight model. The plugin was enabled in the uproject long before anything used
        // it, which meant it compiled but nothing could include its headers - the game module simply did
        // not link against it. This line is what makes it reachable from C++.
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "InputCore", "UMG", "Slate", "SlateCore", "Json", "JsonUtilities", "Niagara", "ShipCore", "HTTP", "AudioCaptureCore" });
        PublicIncludePaths.Add(ModuleDirectory);
        PrivateDependencyModuleNames.AddRange(new[] { "PhysicsCore", "RenderCore", "RHI", "SSCryoRuntime" });
        // Push-to-talk NPC conversations (SSNpcTalk): the engine microphone capture. The AudioCapture plugin
        // supplies the Windows backend and is enabled in the uproject for that reason alone.
        PrivateDependencyModuleNames.Add("AudioCapture");
        // Vendor files stay private. Clones without the SDK retain native rendering and disabled controls.
        bool Nvidia = Target.Platform == UnrealTargetPlatform.Win64;
        foreach (string Plugin in new[] { "DLSS", "NIS", "StreamlineCore", "StreamlineDLSSG", "StreamlineReflex", "StreamlineDeepDVC" })
            Nvidia &= System.IO.Directory.Exists(System.IO.Path.Combine(EngineDirectory, "Plugins/Marketplace", Plugin)) ||
                      System.IO.Directory.Exists(System.IO.Path.Combine(ModuleDirectory, "../../Plugins", Plugin));
        PublicDefinitions.Add("SS_WITH_NVIDIA=" + (Nvidia ? "1" : "0"));
        if (Nvidia)
            PrivateDependencyModuleNames.AddRange(new[] { "DLSSBlueprint", "NISBlueprint", "StreamlineBlueprint",
                "StreamlineDLSSGBlueprint", "StreamlineReflexBlueprint", "StreamlineDeepDVCBlueprint" });
        if (Target.bBuildEditor)
        {
            PrivateDependencyModuleNames.Add("UnrealEd");
            // Opt-in editor renderer observations use only public Renderer APIs.
            PrivateDependencyModuleNames.Add("Renderer");
            PrivateDependencyModuleNames.AddRange(new[] { "ClothingSystemRuntimeCommon", "ClothingSystemRuntimeInterface", "ChaosCloth", "Chaos", "ChaosCore" });
        }
    }
}
