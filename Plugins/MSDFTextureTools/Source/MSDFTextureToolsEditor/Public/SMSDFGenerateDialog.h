#pragma once

#include "CoreMinimal.h"
#include "MSDFTextureTypes.h"
#include "Styling/SlateBrush.h"
#include "Widgets/SCompoundWidget.h"

class UTexture2D;
class UMaterialInstanceDynamic;
class SMSDFPreviewPanel;

class SMSDFGenerateDialog : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SMSDFGenerateDialog) {}
		SLATE_ARGUMENT(TWeakObjectPtr<UTexture2D>, SourceTexture)
		SLATE_ARGUMENT(FString, DefaultOutputFolder)
		SLATE_ARGUMENT(EMSDFGenerationMode, GenerationMode)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual ~SMSDFGenerateDialog() override;

private:
	FReply OnGenerateClicked();
	FText GetSourceSummaryText() const;
	FString GetEdgeColoringText() const;
	void SetEdgeColoringFromText(const FString& Value);
	void UpdatePreview(UTexture2D* GeneratedTexture, const FMSDFTextureGenerationOptions& InOptions);

	TWeakObjectPtr<UTexture2D> SourceTexture;
	FMSDFTextureGenerationOptions Options;
	TArray<TSharedPtr<FString>> ResolutionItems;
	TArray<TSharedPtr<FString>> EdgeColoringItems;

	// Left panel: raw generated texture
	FSlateBrush RawTextureBrush;
	TSharedPtr<SImage> RawTextureImage;

	// Right panel: MID material preview (zoom/pan)
	UMaterialInstanceDynamic* PreviewMID = nullptr;
	FSlateBrush PreviewBrush;
	TSharedPtr<SMSDFPreviewPanel> PreviewPanel;

	TSharedPtr<STextBlock> StatusTextBlock;
};
