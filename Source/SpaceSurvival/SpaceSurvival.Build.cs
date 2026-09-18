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
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "InputCore", "UMG", "Slate", "SlateCore", "Json", "JsonUtilities", "Niagara", "ShipCore" });
        PublicIncludePaths.Add(ModuleDirectory);
        if (Target.bBuildEditor)
            PrivateDependencyModuleNames.Add("UnrealEd");
    }
}
