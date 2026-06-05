#pragma once

#include "Modules/ModuleManager.h"

class FOptimizationPreviewToolsModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

private:
	void RegisterStat();
	void UnregisterStat();
};
