using UnrealBuildTool;

public class SSCryoRuntime : ModuleRules
{
    public SSCryoRuntime(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "InputCore", "Niagara" });
    }
}
