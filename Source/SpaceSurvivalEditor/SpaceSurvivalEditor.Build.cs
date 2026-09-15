using UnrealBuildTool;

public class SpaceSurvivalEditor : ModuleRules
{
    public SpaceSurvivalEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        CppStandard = CppStandardVersion.Cpp20;
        PrivateDependencyModuleNames.AddRange(new[]
        {
            "Core", "CoreUObject", "Engine", "SpaceSurvival", "UnrealEd", "Slate", "SlateCore",
            "InputCore", "ContentBrowser", "ContentBrowserData", "AssetRegistry", "ToolMenus", "Niagara"
        });
    }
}
