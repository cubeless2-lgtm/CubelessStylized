#pragma once

#include "CoreMinimal.h"
#include "GodotOceanWavesTypes.generated.h"

UENUM(BlueprintType)
enum class EGodotOceanWavesSimulationMode : uint8
{
	Preview UMETA(DisplayName = "Preview Waves"),
	FFTExperimental UMETA(DisplayName = "FFT Experimental")
};

USTRUCT(BlueprintType)
struct FGodotOceanWaveCascadeParameters
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cascade", meta = (ClampMin = "1.0"))
	FVector2D TileLength = FVector2D(5000.0, 5000.0);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cascade")
	FIntPoint SpectrumSeed = FIntPoint(0, 0);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cascade", meta = (ClampMin = "0.0", UIMin = "0.0", UIMax = "4.0"))
	float DisplacementScale = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cascade", meta = (ClampMin = "0.0", UIMin = "0.0", UIMax = "4.0"))
	float NormalScale = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spectrum", meta = (ClampMin = "0.0001"))
	float WindSpeed = 20.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spectrum")
	float WindDirectionDegrees = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spectrum", meta = (ClampMin = "0.0001"))
	float FetchLengthKm = 550.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spectrum", meta = (ClampMin = "0.0", UIMin = "0.0", UIMax = "2.0"))
	float Swell = 0.8f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spectrum", meta = (ClampMin = "0.0", UIMin = "0.0", UIMax = "1.0"))
	float Spread = 0.2f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spectrum", meta = (ClampMin = "0.0", UIMin = "0.0", UIMax = "1.0"))
	float Detail = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Foam", meta = (ClampMin = "0.0", UIMin = "0.0", UIMax = "2.0"))
	float Whitecap = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Foam", meta = (ClampMin = "0.0", UIMin = "0.0", UIMax = "10.0"))
	float FoamAmount = 5.0f;
};
