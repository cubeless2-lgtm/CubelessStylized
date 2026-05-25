// Copyright 2023 GiM s.r.o. All Rights Reserved.

using UnrealBuildTool;

public class GFur : ModuleRules
{
	public GFur(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		DefaultBuildSettings = BuildSettingsVersion.V6;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;

		PublicIncludePaths.Add(ModuleDirectory + "/Public");

        PrivateIncludePaths.Add(ModuleDirectory + "/Private");
        PrivateIncludePaths.Add(EngineDirectory + "/Shaders/Shared");

        PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core", "CoreUObject", "Engine", "InputCore", "RHI", "RenderCore"
			}
			);

		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"CoreUObject",
				"Engine",
				"Slate",
				"SlateCore",
				"Projects"
			}
			);
	}
}
