#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "MSDFTextureTypes.h"

struct FAssetData;
class FSlateStyleSet;

class FMSDFTextureToolsEditorModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

	void OpenGenerateWindow(const TArray<FAssetData>& SelectedAssets, EMSDFGenerationMode Mode);

private:
	void RegisterMenus();
	void UnregisterMenus();
	void RegisterStyleSet();
	void UnregisterStyleSet();

	TSharedPtr<FSlateStyleSet> StyleSet;
};
