using UnrealBuildTool;

public class OptimizationPreviewTools : ModuleRules
{
	public OptimizationPreviewTools(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Cbor",
			"Core",
			"CoreUObject",
			"Engine",
			"Foliage",
			"InputCore",
			"Landscape",
			"Niagara",
			"RHI",
			"RenderCore",
			"TraceAnalysis",
			"TraceServices"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"Slate",
			"SlateCore"
		});

		if (Target.bBuildEditor)
		{
			PrivateDependencyModuleNames.Add("UnrealEd");
		}
	}
}
