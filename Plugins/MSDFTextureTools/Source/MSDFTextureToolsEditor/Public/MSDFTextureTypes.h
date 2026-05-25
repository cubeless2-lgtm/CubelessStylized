#pragma once

#include "CoreMinimal.h"

class UTexture2D;

enum class EMSDFEdgeColoringMode : uint8
{
	Simple,
	InkTrap,
	Distance
};

enum class EMSDFGenerationMode : uint8
{
	SDF,
	MSDF,
	MTSDF
};

struct FMSDFTextureGenerationOptions
{
	int32 OutputResolution = 256;
	float Threshold = 0.5f;
	bool bInvertAlpha = false;
	int32 Padding = 2;
	float PxRange = 4.0f;
	EMSDFEdgeColoringMode EdgeColoringMode = EMSDFEdgeColoringMode::InkTrap;
	EMSDFGenerationMode GenerationMode = EMSDFGenerationMode::MTSDF;
	FString OutputFolder;
};

struct FMSDFTextureGenerationResult
{
	bool bSucceeded = false;
	FText Message;
	UTexture2D* Texture = nullptr;
	FString DebugDirectory;
};
