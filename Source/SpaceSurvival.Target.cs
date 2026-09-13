using UnrealBuildTool;
using System.Collections.Generic;
public class SpaceSurvivalTarget : TargetRules
{
    public SpaceSurvivalTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        ExtraModuleNames.Add("SpaceSurvival");
    }
}
