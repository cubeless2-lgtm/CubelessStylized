#include "Modules/ModuleManager.h"

#include "Interfaces/IPluginManager.h"
#include "Misc/Paths.h"
#include "ShaderCore.h"

class FGodotOceanWavesModule : public IModuleInterface
{
public:
	virtual void StartupModule() override
	{
		const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("GodotOceanWaves"));
		if (Plugin.IsValid())
		{
			const FString ShaderDirectory = FPaths::Combine(Plugin->GetBaseDir(), TEXT("Shaders"));
			AddShaderSourceDirectoryMapping(TEXT("/Plugin/GodotOceanWaves"), ShaderDirectory);
		}
	}

	virtual void ShutdownModule() override
	{
	}
};

IMPLEMENT_MODULE(FGodotOceanWavesModule, GodotOceanWaves)
