#pragma once

#include "CoreMinimal.h"
#include "MSDFTextureTypes.h"

class UTexture2D;

class IMSDFTextureBackend
{
public:
	virtual ~IMSDFTextureBackend() = default;
	virtual FMSDFTextureGenerationResult Generate(UTexture2D* SourceTexture, const FMSDFTextureGenerationOptions& Options) = 0;
};

class FExternalMSDFGenBackend final : public IMSDFTextureBackend
{
public:
	virtual FMSDFTextureGenerationResult Generate(UTexture2D* SourceTexture, const FMSDFTextureGenerationOptions& Options) override;

private:
	struct FMaskData
	{
		int32 Width = 0;
		int32 Height = 0;
		bool bHasAlpha = false;
		bool bLooksComplex = false;
		TArray<uint8> Mask;
	};

	static bool ExtractMask(UTexture2D* SourceTexture, const FMSDFTextureGenerationOptions& Options, FMaskData& OutMask, FText& OutError);
	static bool WriteSvgFromMask(const FMaskData& MaskData, const FMSDFTextureGenerationOptions& Options, const FString& SvgPath, int32 OutW, int32 OutH, float Scale, FText& OutError);
	static bool RunMSDFGen(const FString& SvgPath, const FString& PngPath, const FMSDFTextureGenerationOptions& Options, int32 OutW, int32 OutH, FText& OutError);
	static UTexture2D* CreateTextureAssetFromPng(const FString& PngPath, UTexture2D* SourceTexture, const FMSDFTextureGenerationOptions& Options, FText& OutError);
	static FString GetMSDFGenExecutablePath();
};
