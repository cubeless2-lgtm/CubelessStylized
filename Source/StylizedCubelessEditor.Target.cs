using UnrealBuildTool;
using System.Collections.Generic;

public class StylizedCubelessEditorTarget : TargetRules
{
	public StylizedCubelessEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("StylizedCubeless");
	}
}
