using UnrealBuildTool;
using System.Collections.Generic;

public class StylizedCubelessTarget : TargetRules
{
	public StylizedCubelessTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("StylizedCubeless");
	}
}
