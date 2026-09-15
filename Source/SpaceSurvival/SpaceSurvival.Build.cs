using UnrealBuildTool;
public class SpaceSurvival : ModuleRules
{
    public SpaceSurvival(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        CppStandard = CppStandardVersion.Cpp20;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "InputCore", "UMG", "Slate", "SlateCore", "Json", "JsonUtilities", "Niagara" });
        PublicIncludePaths.Add(ModuleDirectory);
        if (Target.bBuildEditor)
            PrivateDependencyModuleNames.Add("UnrealEd");
    }
}
