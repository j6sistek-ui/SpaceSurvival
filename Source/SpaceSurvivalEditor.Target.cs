using UnrealBuildTool;
using System.Collections.Generic;
public class SpaceSurvivalEditorTarget : TargetRules
{
    public SpaceSurvivalEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        ExtraModuleNames.Add("SpaceSurvival");
    }
}
