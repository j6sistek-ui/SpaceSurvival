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
        PrivateDependencyModuleNames.Add("PhysicsCore");
        // Push-to-talk NPC conversations (SSNpcTalk): the engine microphone capture. The AudioCapture plugin
        // supplies the Windows backend and is enabled in the uproject for that reason alone.
        PrivateDependencyModuleNames.Add("AudioCapture");
        if (Target.bBuildEditor)
            PrivateDependencyModuleNames.Add("UnrealEd");
    }
}
