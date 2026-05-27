#pragma once

#include "GlobalShader.h"
#include "ShaderParameterStruct.h"

class FGodotOceanWavesPreviewCS : public FGlobalShader
{
	DECLARE_GLOBAL_SHADER(FGodotOceanWavesPreviewCS);
	SHADER_USE_PARAMETER_STRUCT(FGodotOceanWavesPreviewCS, FGlobalShader);

	BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
		SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, OutDisplacement)
		SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, OutNormalFoam)
		SHADER_PARAMETER(FUintVector2, OutputSize)
		SHADER_PARAMETER(float, TimeSeconds)
		SHADER_PARAMETER(float, DeltaTime)
		SHADER_PARAMETER(FVector2f, WorldOrigin)
		SHADER_PARAMETER(FVector2f, TileLength)
		SHADER_PARAMETER(float, DisplacementScale)
		SHADER_PARAMETER(float, NormalScale)
		SHADER_PARAMETER(float, WindSpeed)
		SHADER_PARAMETER(float, WindDirectionRadians)
		SHADER_PARAMETER(float, FetchLengthKm)
		SHADER_PARAMETER(float, Swell)
		SHADER_PARAMETER(float, Spread)
		SHADER_PARAMETER(float, Detail)
		SHADER_PARAMETER(float, Whitecap)
		SHADER_PARAMETER(float, FoamAmount)
		SHADER_PARAMETER(uint32, bResetOutput)
	END_SHADER_PARAMETER_STRUCT()

	static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
	{
		return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
	}
};

class FGodotOceanWavesSpectrumCS : public FGlobalShader
{
	DECLARE_GLOBAL_SHADER(FGodotOceanWavesSpectrumCS);
	SHADER_USE_PARAMETER_STRUCT(FGodotOceanWavesSpectrumCS, FGlobalShader);

	BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
		SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, OutSpectrum)
		SHADER_PARAMETER(FUintVector2, OutputSize)
		SHADER_PARAMETER(FIntPoint, Seed)
		SHADER_PARAMETER(FVector2f, TileLength)
		SHADER_PARAMETER(float, Alpha)
		SHADER_PARAMETER(float, PeakFrequency)
		SHADER_PARAMETER(float, WindSpeed)
		SHADER_PARAMETER(float, WindDirectionRadians)
		SHADER_PARAMETER(float, Depth)
		SHADER_PARAMETER(float, Swell)
		SHADER_PARAMETER(float, Detail)
		SHADER_PARAMETER(float, Spread)
	END_SHADER_PARAMETER_STRUCT()

	static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
	{
		return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
	}
};

class FGodotOceanWavesButterflyCS : public FGlobalShader
{
	DECLARE_GLOBAL_SHADER(FGodotOceanWavesButterflyCS);
	SHADER_USE_PARAMETER_STRUCT(FGodotOceanWavesButterflyCS, FGlobalShader);

	BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
		SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>, OutButterfly)
		SHADER_PARAMETER(uint32, MapSize)
		SHADER_PARAMETER(uint32, NumStages)
	END_SHADER_PARAMETER_STRUCT()

	static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
	{
		return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
	}
};

class FGodotOceanWavesModulateCS : public FGlobalShader
{
	DECLARE_GLOBAL_SHADER(FGodotOceanWavesModulateCS);
	SHADER_USE_PARAMETER_STRUCT(FGodotOceanWavesModulateCS, FGlobalShader);

	BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
		SHADER_PARAMETER_RDG_TEXTURE(Texture2D<float4>, InSpectrum)
		SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>, OutFFTBuffer)
		SHADER_PARAMETER(FUintVector2, OutputSize)
		SHADER_PARAMETER(uint32, MapSize)
		SHADER_PARAMETER(FVector2f, TileLength)
		SHADER_PARAMETER(float, Depth)
		SHADER_PARAMETER(float, TimeSeconds)
	END_SHADER_PARAMETER_STRUCT()

	static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
	{
		return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
	}
};

class FGodotOceanWavesFFTCS : public FGlobalShader
{
	DECLARE_GLOBAL_SHADER(FGodotOceanWavesFFTCS);
	SHADER_USE_PARAMETER_STRUCT(FGodotOceanWavesFFTCS, FGlobalShader);

	BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
		SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>, Butterfly)
		SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>, FFTBuffer)
		SHADER_PARAMETER(uint32, MapSize)
		SHADER_PARAMETER(uint32, NumStages)
	END_SHADER_PARAMETER_STRUCT()

	static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
	{
		return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
	}
};

class FGodotOceanWavesTransposeCS : public FGlobalShader
{
	DECLARE_GLOBAL_SHADER(FGodotOceanWavesTransposeCS);
	SHADER_USE_PARAMETER_STRUCT(FGodotOceanWavesTransposeCS, FGlobalShader);

	BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
		SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>, FFTBuffer)
		SHADER_PARAMETER(uint32, MapSize)
	END_SHADER_PARAMETER_STRUCT()

	static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
	{
		return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
	}
};

class FGodotOceanWavesUnpackCS : public FGlobalShader
{
	DECLARE_GLOBAL_SHADER(FGodotOceanWavesUnpackCS);
	SHADER_USE_PARAMETER_STRUCT(FGodotOceanWavesUnpackCS, FGlobalShader);

	BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
		SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float2>, FFTBufferInput)
		SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, OutDisplacement)
		SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, OutNormalFoam)
		SHADER_PARAMETER(FUintVector2, OutputSize)
		SHADER_PARAMETER(uint32, MapSize)
		SHADER_PARAMETER(float, DisplacementScale)
		SHADER_PARAMETER(float, NormalScale)
		SHADER_PARAMETER(float, Whitecap)
		SHADER_PARAMETER(float, FoamAmount)
		SHADER_PARAMETER(uint32, bResetOutput)
	END_SHADER_PARAMETER_STRUCT()

	static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
	{
		return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
	}
};
