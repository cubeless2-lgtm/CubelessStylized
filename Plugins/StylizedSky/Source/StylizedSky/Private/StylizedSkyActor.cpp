#include "StylizedSkyActor.h"

#include "Components/DirectionalLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace StylizedSky
{
	static float SmoothStep01(float Edge0, float Edge1, float Value)
	{
		if (FMath::IsNearlyEqual(Edge0, Edge1))
		{
			return Value >= Edge1 ? 1.0f : 0.0f;
		}

		const float T = FMath::Clamp((Value - Edge0) / (Edge1 - Edge0), 0.0f, 1.0f);
		return T * T * (3.0f - 2.0f * T);
	}

	static FLinearColor LerpLookColor(const FLinearColor& NightColor, const FLinearColor& SunsetColor, const FLinearColor& DayColor, const FVector& Weights)
	{
		return NightColor * Weights.X + SunsetColor * Weights.Y + DayColor * Weights.Z;
	}

	static float LerpLookFloat(float NightValue, float SunsetValue, float DayValue, const FVector& Weights)
	{
		return NightValue * Weights.X + SunsetValue * Weights.Y + DayValue * Weights.Z;
	}

	static FStylizedSkyCloudPlaneSettings MakeCloudPlane(
		const FVector& Location,
		const FRotator& Rotation,
		const FVector& Scale,
		int32 SortPriority)
	{
		FStylizedSkyCloudPlaneSettings Settings;
		Settings.RelativeTransform = FTransform(Rotation, Location, Scale);
		Settings.TranslucencySortPriority = SortPriority;
		return Settings;
	}

	static FStylizedSkyCloudPlaneSettings MakeDomeCloudPlane(
		float Radius,
		float AzimuthDegrees,
		float ElevationDegrees,
		float WidthUU,
		float HeightUU,
		int32 SortPriority)
	{
		const float Azimuth = FMath::DegreesToRadians(AzimuthDegrees);
		const float Elevation = FMath::DegreesToRadians(ElevationDegrees);
		const float HorizontalRadius = FMath::Cos(Elevation);

		const FVector Radial = FVector(
			HorizontalRadius * FMath::Cos(Azimuth),
			HorizontalRadius * FMath::Sin(Azimuth),
			FMath::Sin(Elevation)).GetSafeNormal();
		const FVector Location = Radial * Radius;

		FVector TangentRight = FVector::CrossProduct(FVector::UpVector, Radial);
		if (!TangentRight.Normalize())
		{
			TangentRight = FVector::RightVector;
		}

		// The plane mesh is 100uu x 100uu in local X/Y. Keep local Z facing the
		// dome center so the cloud surface is tangent to the sky hemisphere.
		const FRotator Rotation = FRotationMatrix::MakeFromZX(-Radial, TangentRight).Rotator();
		const FVector Scale(FMath::Max(WidthUU, 1.0f) / 100.0f, FMath::Max(HeightUU, 1.0f) / 100.0f, 1.0f);

		return MakeCloudPlane(Location, Rotation, Scale, SortPriority);
	}

	static UMaterialInterface* LoadMaterialInterface(const TCHAR* PrimaryPath, const TCHAR* FallbackPath = nullptr)
	{
		if (UMaterialInterface* Material = Cast<UMaterialInterface>(StaticLoadObject(UMaterialInterface::StaticClass(), nullptr, PrimaryPath)))
		{
			return Material;
		}

		return FallbackPath
			? Cast<UMaterialInterface>(StaticLoadObject(UMaterialInterface::StaticClass(), nullptr, FallbackPath))
			: nullptr;
	}
}

FStylizedSkyLookSettings::FStylizedSkyLookSettings()
	: SkyZenithColor(0.18f, 0.42f, 0.88f, 1.0f)
	, SkyHorizonColor(0.78f, 0.88f, 1.0f, 1.0f)
	, SunColor(1.0f, 0.94f, 0.75f, 1.0f)
	, CloudLightTint(1.0f, 0.97f, 0.88f, 1.0f)
	, CloudShadowTint(0.44f, 0.55f, 0.72f, 1.0f)
	, TimeOfDayTint(1.0f, 1.0f, 1.0f, 1.0f)
	, CloudOpacity(0.74f)
	, CloudIntensity(1.12f)
	, StarsIntensity(0.0f)
	, StarsColor(0.86f, 0.92f, 1.0f, 1.0f)
	, DirectionalLightIntensity(3.5f)
	, DirectionalLightColor(1.0f, 0.94f, 0.82f, 1.0f)
	, DirectionalLightVolumetricScatteringIntensity(0.6f)
	, NightLightIntensity(0.0f)
	, NightLightColor(0.45f, 0.55f, 1.0f, 1.0f)
	, NightLightVolumetricScatteringIntensity(0.35f)
	, MoonColor(0.86f, 0.92f, 1.0f, 1.0f)
	, MoonIntensity(0.0f)
	, MoonAngularSizeDegrees(2.2f)
	, MoonGlowIntensity(0.0f)
	, SkyLightIntensity(1.0f)
	, SkyLightColor(0.62f, 0.75f, 1.0f, 1.0f)
	, SkyAtmosphereSkyLuminanceFactor(1.0f, 1.0f, 1.0f, 1.0f)
	, SkyAtmosphereAerialPerspectiveLuminanceFactor(1.0f, 1.0f, 1.0f, 1.0f)
	, SkyAtmosphereRayleighScattering(0.17f, 0.36f, 1.0f, 1.0f)
	, SkyAtmosphereRayleighScatteringScale(0.35f)
	, SkyAtmosphereMieScattering(1.0f, 0.85f, 0.65f, 1.0f)
	, SkyAtmosphereMieScatteringScale(0.08f)
{
}

FStylizedSkyCloudPlaneSettings::FStylizedSkyCloudPlaneSettings()
	: bEnabled(true)
	, RelativeTransform(FTransform::Identity)
	, MaterialOverride(nullptr)
	, TranslucencySortPriority(20)
{
}

FStylizedSkyMaterialParameterNames::FStylizedSkyMaterialParameterNames()
	: SunDirection(TEXT("SunDirection"))
	, SunElevation(TEXT("SunElevation"))
	, SkyZenithColor(TEXT("SkyZenithColor"))
	, SkyHorizonColor(TEXT("SkyHorizonColor"))
	, SunColor(TEXT("SunColor"))
	, MoonDirection(TEXT("MoonDirection"))
	, MoonColor(TEXT("MoonColor"))
	, MoonIntensity(TEXT("MoonIntensity"))
	, MoonAngularSizeDegrees(TEXT("MoonAngularSizeDegrees"))
	, MoonGlowIntensity(TEXT("MoonGlowIntensity"))
	, StarsIntensity(TEXT("StarsIntensity"))
	, StarsColor(TEXT("StarsColor"))
	, StarsMilkyWayTexture(TEXT("StarsMilkyWayTexture"))
	, StarsMaskMap(TEXT("StarsMaskMap"))
	, StarsTiling(TEXT("StarsTiling"))
	, StarsMaskThreshold(TEXT("StarsMaskThreshold"))
	, StarsMaskPower(TEXT("StarsMaskPower"))
	, PackedCloudAtlas(TEXT("PackedCloudAtlas"))
	, LightWeightsRGB(TEXT("LightWeights_RGB"))
	, CloudLightTint(TEXT("CloudLightTint"))
	, CloudShadowTint(TEXT("CloudShadowTint"))
	, TimeOfDayTint(TEXT("TimeOfDayTint"))
	, CloudOpacity(TEXT("Opacity"))
	, CloudIntensity(TEXT("CloudIntensity"))
{
}

AStylizedSkyActor::AStylizedSkyActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;

	SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
	SetRootComponent(SceneRoot);

	SkyDomeComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SkyDome"));
	SkyDomeComponent->SetupAttachment(SceneRoot);
	SkyDomeComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SkyDomeComponent->SetCastShadow(false);
	SkyDomeComponent->SetGenerateOverlapEvents(false);
	SkyDomeComponent->SetMobility(EComponentMobility::Movable);
	SkyDomeComponent->SetRelativeScale3D(FVector(500.0f));

	CloudRootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("CloudRoot"));
	CloudRootComponent->SetupAttachment(SceneRoot);

	CloudPlane0 = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CloudPlane0"));
	CloudPlane1 = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CloudPlane1"));
	CloudPlane2 = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CloudPlane2"));
	CloudPlane3 = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CloudPlane3"));
	CloudPlane4 = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CloudPlane4"));
	CloudPlane5 = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CloudPlane5"));
	CloudPlane6 = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CloudPlane6"));
	CloudPlane7 = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CloudPlane7"));

	for (UStaticMeshComponent* CloudPlane : GetCloudPlaneComponents())
	{
		CloudPlane->SetupAttachment(CloudRootComponent);
		CloudPlane->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		CloudPlane->SetCastShadow(false);
		CloudPlane->SetGenerateOverlapEvents(false);
		CloudPlane->SetMobility(EComponentMobility::Movable);
		CloudPlane->bReceivesDecals = false;
	}

	static ConstructorHelpers::FObjectFinderOptional<UStaticMesh> SphereMeshRef(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereMeshRef.Succeeded())
	{
		SkyDomeMesh = SphereMeshRef.Get();
		SkyDomeComponent->SetStaticMesh(SkyDomeMesh);
	}

	static ConstructorHelpers::FObjectFinderOptional<UStaticMesh> PlaneMeshRef(TEXT("/Engine/BasicShapes/Plane.Plane"));
	if (PlaneMeshRef.Succeeded())
	{
		CloudPlaneMesh = PlaneMeshRef.Get();
	}

	PackedCloudAtlasTexture = Cast<UTexture2D>(StaticLoadObject(
		UTexture2D::StaticClass(),
		nullptr,
		TEXT("/Game/Cubeless/Env/Sky/Textures/T_CloudPlaneAtlas_LightPacked_UDSLike.T_CloudPlaneAtlas_LightPacked_UDSLike")));

	StarsMilkyWayTexture = Cast<UTexture2D>(StaticLoadObject(
		UTexture2D::StaticClass(),
		nullptr,
		TEXT("/Game/Cubeless/Env/Sky/Textures/T_StylizedSky_Stars_MilkyWay.T_StylizedSky_Stars_MilkyWay")));

	StarsMaskTexture = Cast<UTexture2D>(StaticLoadObject(
		UTexture2D::StaticClass(),
		nullptr,
		TEXT("/Game/Cubeless/Env/Sky/Textures/T_StylizedSky_Stars_Mask_Tile_RGBA.T_StylizedSky_Stars_Mask_Tile_RGBA")));
	StarsTiling = 3.0f;
	StarsMaskThreshold = 0.22f;
	StarsMaskPower = 1.45f;

	SkyDomeMaterial = StylizedSky::LoadMaterialInterface(
		TEXT("/StylizedSky/Materials/MI_StylizedSky_Dome_MoonRGBMask.MI_StylizedSky_Dome_MoonRGBMask"),
		TEXT("/Game/Cubeless/Env/Sky/Materials/MI_StylizedSky_Dome_MoonRGBMask.MI_StylizedSky_Dome_MoonRGBMask"));
	if (!SkyDomeMaterial)
	{
		SkyDomeMaterial = StylizedSky::LoadMaterialInterface(
			TEXT("/StylizedSky/Materials/MI_StylizedSky_Dome_RGBMask.MI_StylizedSky_Dome_RGBMask"),
			TEXT("/Game/Cubeless/Env/Sky/Materials/MI_StylizedSky_Dome_RGBMask.MI_StylizedSky_Dome_RGBMask"));
	}

	DefaultCloudMaterial = StylizedSky::LoadMaterialInterface(
		TEXT("/StylizedSky/Materials/MI_StylizedSky_Cloud_Default.MI_StylizedSky_Cloud_Default"),
		TEXT("/Game/Cubeless/Env/Sky/Materials/MI_StylizedSky_Cloud_Default.MI_StylizedSky_Cloud_Default"));
	if (!DefaultCloudMaterial)
	{
		DefaultCloudMaterial = StylizedSky::LoadMaterialInterface(
			TEXT("/Game/Cubeless/Env/Sky/Materials/MI_CloudPlane_LightPacked_Default.MI_CloudPlane_LightPacked_Default"));
	}

	CloudTileMaterials.SetNum(8);
	for (int32 Index = 0; Index < CloudTileMaterials.Num(); ++Index)
	{
		const FString TilePath = FString::Printf(
			TEXT("/StylizedSky/Materials/MI_StylizedSky_Cloud_Tile_%02d.MI_StylizedSky_Cloud_Tile_%02d"),
			Index,
			Index);
		const FString GameTilePath = FString::Printf(
			TEXT("/Game/Cubeless/Env/Sky/Materials/MI_StylizedSky_Cloud_Tile_%02d.MI_StylizedSky_Cloud_Tile_%02d"),
			Index,
			Index);
		CloudTileMaterials[Index] = StylizedSky::LoadMaterialInterface(*TilePath, *GameTilePath);
		if (!CloudTileMaterials[Index])
		{
			const FString FallbackTilePath = FString::Printf(
				TEXT("/Game/Cubeless/Env/Sky/Materials/MI_CloudPlane_LightPacked_Tile_%02d.MI_CloudPlane_LightPacked_Tile_%02d"),
				Index,
				Index);
			CloudTileMaterials[Index] = StylizedSky::LoadMaterialInterface(*FallbackTilePath);
		}
	}

	ManualSunDirection = FVector(0.35f, -0.25f, 0.9f);
	ManualNightLightDirection = FVector(0.28f, -0.48f, 0.83f);
	bInvertSunActorForward = true;
	bInvertNightLightActorForward = true;
	bUseTimeOfDayPreview = true;
	bDriveSunActorFromTimeOfDay = true;
	bDriveDirectionalLightFromLook = true;
	bDriveNightLightFromLook = true;
	bDriveSkyLightFromLook = true;
	bDriveSkyAtmosphereFromLook = true;
	TimeOfDayHours = 21.0f;
	TimeOfDayMinutes = TimeOfDayHoursToMinutes(TimeOfDayHours);
	bAnimateTimeOfDay = false;
	TimeOfDaySpeedMinutesPerSecond = 10.0f;
	TimeOfDayAzimuthDegrees = 35.0f;
	TimeOfDayMaxSunElevation = 72.0f;
	TimeOfDayMaxNightDepression = 52.0f;
	CurrentTimeOfDayHours = TimeOfDayHours;
	CurrentTimeOfDayMinutes = TimeOfDayMinutes;
	CurrentSunElevationDegrees = 0.0f;
	CurrentLookWeights_NightSunsetDay = FVector::ZeroVector;
	CurrentTimeOfDayPhase = TEXT("Unknown");
	bUpdateEveryTick = true;
	bUpdateInEditor = true;
	bApplyCloudPlaneSettingsOnConstruction = false;

	DayStartElevation = 4.0f;
	DayFullElevation = 14.0f;
	NightFullElevation = -12.0f;
	NightEndElevation = -2.0f;
	SunsetPeakElevation = 0.0f;
	SunsetWidthDegrees = 10.0f;

	DayLook = FStylizedSkyLookSettings();
	DayLook.SkyZenithColor = FLinearColor(0.015f, 0.16f, 0.82f, 1.0f);
	DayLook.SkyHorizonColor = FLinearColor(0.22f, 0.66f, 1.0f, 1.0f);
	DayLook.SunColor = FLinearColor(1.0f, 0.92f, 0.70f, 1.0f);
	DayLook.CloudLightTint = FLinearColor(1.0f, 0.90f, 0.72f, 1.0f);
	DayLook.CloudShadowTint = FLinearColor(0.18f, 0.34f, 0.82f, 1.0f);
	DayLook.TimeOfDayTint = FLinearColor(1.0f, 0.96f, 0.88f, 1.0f);
	DayLook.CloudOpacity = 0.84f;
	DayLook.CloudIntensity = 1.22f;
	DayLook.StarsIntensity = 0.0f;
	DayLook.StarsColor = FLinearColor(0.86f, 0.92f, 1.0f, 1.0f);
	DayLook.DirectionalLightIntensity = 4.0f;
	DayLook.DirectionalLightColor = FLinearColor(1.0f, 0.94f, 0.82f, 1.0f);
	DayLook.DirectionalLightVolumetricScatteringIntensity = 0.55f;
	DayLook.NightLightIntensity = 0.0f;
	DayLook.NightLightColor = FLinearColor(0.45f, 0.55f, 1.0f, 1.0f);
	DayLook.NightLightVolumetricScatteringIntensity = 0.0f;
	DayLook.MoonColor = FLinearColor(0.86f, 0.92f, 1.0f, 1.0f);
	DayLook.MoonIntensity = 0.0f;
	DayLook.MoonAngularSizeDegrees = 2.2f;
	DayLook.MoonGlowIntensity = 0.0f;
	DayLook.SkyLightIntensity = 1.0f;
	DayLook.SkyLightColor = FLinearColor(0.62f, 0.75f, 1.0f, 1.0f);
	DayLook.SkyAtmosphereSkyLuminanceFactor = FLinearColor(1.0f, 1.0f, 1.0f, 1.0f);
	DayLook.SkyAtmosphereAerialPerspectiveLuminanceFactor = FLinearColor(0.90f, 0.98f, 1.0f, 1.0f);
	DayLook.SkyAtmosphereRayleighScattering = FLinearColor(0.18f, 0.38f, 1.0f, 1.0f);
	DayLook.SkyAtmosphereRayleighScatteringScale = 0.32f;
	DayLook.SkyAtmosphereMieScattering = FLinearColor(1.0f, 0.86f, 0.66f, 1.0f);
	DayLook.SkyAtmosphereMieScatteringScale = 0.06f;

	SunsetLook = FStylizedSkyLookSettings();
	SunsetLook.SkyZenithColor = FLinearColor(0.015f, 0.10f, 0.58f, 1.0f);
	SunsetLook.SkyHorizonColor = FLinearColor(1.0f, 0.46f, 0.26f, 1.0f);
	SunsetLook.SunColor = FLinearColor(1.0f, 0.60f, 0.28f, 1.0f);
	SunsetLook.CloudLightTint = FLinearColor(1.0f, 0.68f, 0.46f, 1.0f);
	SunsetLook.CloudShadowTint = FLinearColor(0.20f, 0.22f, 0.68f, 1.0f);
	SunsetLook.TimeOfDayTint = FLinearColor(1.0f, 0.70f, 0.52f, 1.0f);
	SunsetLook.CloudOpacity = 0.86f;
	SunsetLook.CloudIntensity = 1.32f;
	SunsetLook.StarsIntensity = 0.0f;
	SunsetLook.StarsColor = FLinearColor(1.0f, 0.82f, 0.72f, 1.0f);
	SunsetLook.DirectionalLightIntensity = 1.35f;
	SunsetLook.DirectionalLightColor = FLinearColor(1.0f, 0.48f, 0.26f, 1.0f);
	SunsetLook.DirectionalLightVolumetricScatteringIntensity = 0.85f;
	SunsetLook.NightLightIntensity = 0.0f;
	SunsetLook.NightLightColor = FLinearColor(0.65f, 0.50f, 1.0f, 1.0f);
	SunsetLook.NightLightVolumetricScatteringIntensity = 0.0f;
	SunsetLook.MoonColor = FLinearColor(0.80f, 0.84f, 1.0f, 1.0f);
	SunsetLook.MoonIntensity = 0.0f;
	SunsetLook.MoonAngularSizeDegrees = 2.2f;
	SunsetLook.MoonGlowIntensity = 0.0f;
	SunsetLook.SkyLightIntensity = 0.48f;
	SunsetLook.SkyLightColor = FLinearColor(1.0f, 0.48f, 0.38f, 1.0f);
	SunsetLook.SkyAtmosphereSkyLuminanceFactor = FLinearColor(1.0f, 0.45f, 0.34f, 1.0f);
	SunsetLook.SkyAtmosphereAerialPerspectiveLuminanceFactor = FLinearColor(1.0f, 0.55f, 0.42f, 1.0f);
	SunsetLook.SkyAtmosphereRayleighScattering = FLinearColor(0.55f, 0.18f, 0.85f, 1.0f);
	SunsetLook.SkyAtmosphereRayleighScatteringScale = 0.22f;
	SunsetLook.SkyAtmosphereMieScattering = FLinearColor(1.0f, 0.42f, 0.22f, 1.0f);
	SunsetLook.SkyAtmosphereMieScatteringScale = 0.22f;

	NightLook = FStylizedSkyLookSettings();
	NightLook.SkyZenithColor = FLinearColor(0.0005f, 0.004f, 0.035f, 1.0f);
	NightLook.SkyHorizonColor = FLinearColor(0.030f, 0.020f, 0.180f, 1.0f);
	NightLook.SunColor = FLinearColor(0.035f, 0.050f, 0.140f, 1.0f);
	NightLook.CloudLightTint = FLinearColor(0.56f, 0.43f, 0.95f, 1.0f);
	NightLook.CloudShadowTint = FLinearColor(0.010f, 0.025f, 0.130f, 1.0f);
	NightLook.TimeOfDayTint = FLinearColor(0.28f, 0.26f, 0.75f, 1.0f);
	NightLook.CloudOpacity = 1.85f;
	NightLook.CloudIntensity = 0.42f;
	NightLook.StarsIntensity = 0.55f;
	NightLook.StarsColor = FLinearColor(0.82f, 0.90f, 1.0f, 1.0f);
	NightLook.DirectionalLightIntensity = 0.035f;
	NightLook.DirectionalLightColor = FLinearColor(0.22f, 0.28f, 0.62f, 1.0f);
	NightLook.DirectionalLightVolumetricScatteringIntensity = 0.15f;
	NightLook.NightLightIntensity = 0.45f;
	NightLook.NightLightColor = FLinearColor(0.45f, 0.55f, 1.0f, 1.0f);
	NightLook.NightLightVolumetricScatteringIntensity = 0.35f;
	NightLook.MoonColor = FLinearColor(0.86f, 0.92f, 1.0f, 1.0f);
	NightLook.MoonIntensity = 1.2f;
	NightLook.MoonAngularSizeDegrees = 2.2f;
	NightLook.MoonGlowIntensity = 0.12f;
	NightLook.SkyLightIntensity = 0.12f;
	NightLook.SkyLightColor = FLinearColor(0.10f, 0.16f, 0.45f, 1.0f);
	NightLook.SkyAtmosphereSkyLuminanceFactor = FLinearColor(0.025f, 0.045f, 0.18f, 1.0f);
	NightLook.SkyAtmosphereAerialPerspectiveLuminanceFactor = FLinearColor(0.035f, 0.050f, 0.22f, 1.0f);
	NightLook.SkyAtmosphereRayleighScattering = FLinearColor(0.04f, 0.08f, 0.42f, 1.0f);
	NightLook.SkyAtmosphereRayleighScatteringScale = 0.06f;
	NightLook.SkyAtmosphereMieScattering = FLinearColor(0.16f, 0.12f, 0.38f, 1.0f);
	NightLook.SkyAtmosphereMieScatteringScale = 0.03f;

	CloudPlaneSettings = {
		StylizedSky::MakeDomeCloudPlane(18500.0f, -78.0f, 26.0f, 5200.0f, 7800.0f, 20),
		StylizedSky::MakeDomeCloudPlane(19500.0f, -52.0f, 42.0f, 6800.0f, 9800.0f, 21),
		StylizedSky::MakeDomeCloudPlane(17800.0f, -28.0f, 30.0f, 4300.0f, 6200.0f, 22),
		StylizedSky::MakeDomeCloudPlane(20500.0f, -4.0f, 55.0f, 7600.0f, 10800.0f, 23),
		StylizedSky::MakeDomeCloudPlane(18200.0f, 22.0f, 34.0f, 5000.0f, 7200.0f, 24),
		StylizedSky::MakeDomeCloudPlane(19800.0f, 48.0f, 46.0f, 7000.0f, 10000.0f, 25),
		StylizedSky::MakeDomeCloudPlane(18400.0f, 76.0f, 28.0f, 4600.0f, 6500.0f, 26),
		StylizedSky::MakeDomeCloudPlane(20800.0f, 110.0f, 50.0f, 5600.0f, 8000.0f, 27)
	};

	ApplyComponentSettings(true);
}

void AStylizedSkyActor::BeginDestroy()
{
#if WITH_EDITOR
	ReleaseEditorTicker();
#endif
	Super::BeginDestroy();
}

void AStylizedSkyActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
#if WITH_EDITOR
	EnsureEditorTicker();
#endif
	ApplyComponentSettings(bApplyCloudPlaneSettingsOnConstruction);
	EnsureDynamicMaterials();
	RefreshSky();
}

void AStylizedSkyActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

#if WITH_EDITOR
	if (const UWorld* World = GetWorld(); World && !World->IsGameWorld())
	{
		return;
	}
#endif

	TickSky(DeltaSeconds);
}

void AStylizedSkyActor::TickSky(float DeltaSeconds)
{
	const bool bShouldAdvanceTimeOfDay = bUseTimeOfDayPreview
		&& bAnimateTimeOfDay
		&& !FMath::IsNearlyZero(TimeOfDaySpeedMinutesPerSecond);

	if (bShouldAdvanceTimeOfDay)
	{
		const float DeltaMinutes = FMath::Max(0.0f, DeltaSeconds) * TimeOfDaySpeedMinutesPerSecond;
		TimeOfDayHours = NormalizeTimeOfDayHours(TimeOfDayHours + DeltaMinutes / 60.0f);
		TimeOfDayMinutes = TimeOfDayHoursToMinutes(TimeOfDayHours);
	}

	if (bUpdateEveryTick || bShouldAdvanceTimeOfDay)
	{
		RefreshSky();
	}
}

#if WITH_EDITOR
bool AStylizedSkyActor::ShouldTickIfViewportsOnly() const
{
	return bUpdateInEditor || (bUseTimeOfDayPreview && bAnimateTimeOfDay);
}

void AStylizedSkyActor::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);

	const FName ChangedPropertyName = PropertyChangedEvent.Property
		? PropertyChangedEvent.Property->GetFName()
		: NAME_None;

	if (ChangedPropertyName == GET_MEMBER_NAME_CHECKED(AStylizedSkyActor, TimeOfDayMinutes))
	{
		TimeOfDayMinutes = NormalizeTimeOfDayMinutes(TimeOfDayMinutes);
		TimeOfDayHours = TimeOfDayMinutesToHours(TimeOfDayMinutes);
	}
	else
	{
		TimeOfDayHours = NormalizeTimeOfDayHours(TimeOfDayHours);
		TimeOfDayMinutes = TimeOfDayHoursToMinutes(TimeOfDayHours);
	}

	TimeOfDaySpeedMinutesPerSecond = FMath::Clamp(TimeOfDaySpeedMinutesPerSecond, -1440.0f, 1440.0f);
	StarsTiling = FMath::Max(0.1f, StarsTiling);
	StarsMaskThreshold = FMath::Clamp(StarsMaskThreshold, 0.0f, 1.0f);
	StarsMaskPower = FMath::Max(0.1f, StarsMaskPower);
	EnsureEditorTicker();
	RefreshSky();
}

void AStylizedSkyActor::EnsureEditorTicker()
{
	if (!HasAnyFlags(RF_ClassDefaultObject) && !EditorTickerHandle.IsValid())
	{
		EditorTickerHandle = FTSTicker::GetCoreTicker().AddTicker(
			FTickerDelegate::CreateUObject(this, &AStylizedSkyActor::HandleEditorTick),
			0.0f);
	}
}

void AStylizedSkyActor::ReleaseEditorTicker()
{
	if (EditorTickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(EditorTickerHandle);
		EditorTickerHandle.Reset();
	}
}

bool AStylizedSkyActor::HandleEditorTick(float DeltaSeconds)
{
	if (HasAnyFlags(RF_BeginDestroyed | RF_FinishDestroyed))
	{
		return false;
	}

	const UWorld* World = GetWorld();
	if (!World || World->IsGameWorld())
	{
		return true;
	}

	if (bUpdateInEditor || (bUseTimeOfDayPreview && bAnimateTimeOfDay))
	{
		TickSky(DeltaSeconds);
	}

	return true;
}
#endif

void AStylizedSkyActor::RefreshSky()
{
	EnsureDynamicMaterials();

	const FVector SunDirection = GetResolvedSunDirection();
	const FVector MoonDirection = GetResolvedNightLightDirection();
	if (bUseTimeOfDayPreview && bDriveSunActorFromTimeOfDay)
	{
		ApplyTimeOfDayToSunActor(SunDirection);
	}

	const float SunElevation = FMath::RadiansToDegrees(FMath::Asin(FMath::Clamp(SunDirection.Z, -1.0f, 1.0f)));
	const FStylizedSkyLookSettings Look = BlendLookSettings(SunElevation);
	const FVector LookWeights = ComputeLookWeights(SunElevation);
	const FVector LightWeights = ComputePackedLightWeights(SunDirection, SunElevation);

	CurrentTimeOfDayHours = NormalizeTimeOfDayHours(TimeOfDayHours);
	CurrentTimeOfDayMinutes = TimeOfDayHoursToMinutes(CurrentTimeOfDayHours);
	CurrentSunElevationDegrees = SunElevation;
	CurrentLookWeights_NightSunsetDay = LookWeights;
	CurrentTimeOfDayPhase = ComputeTimeOfDayPhase(LookWeights);

	ApplyLookToEnvironment(Look);
	ApplyLookToMaterial(SkyDomeMID, Look, SunDirection, MoonDirection, SunElevation, LightWeights);

	for (UMaterialInstanceDynamic* CloudMID : CloudMIDs)
	{
		ApplyLookToMaterial(CloudMID, Look, SunDirection, MoonDirection, SunElevation, LightWeights);
	}
}

FVector AStylizedSkyActor::GetResolvedSunDirection() const
{
	if (bUseTimeOfDayPreview)
	{
		return ComputeTimeOfDaySunDirection();
	}

	FVector Direction = ManualSunDirection;

	if (SunActor)
	{
		if (const UDirectionalLightComponent* DirectionalLight = SunActor->FindComponentByClass<UDirectionalLightComponent>())
		{
			Direction = DirectionalLight->GetForwardVector();
		}
		else
		{
			Direction = SunActor->GetActorForwardVector();
		}

		if (bInvertSunActorForward)
		{
			Direction *= -1.0f;
		}
	}

	if (!Direction.Normalize())
	{
		Direction = FVector(0.35f, -0.25f, 0.9f);
		Direction.Normalize();
	}

	return Direction;
}

FVector AStylizedSkyActor::GetResolvedNightLightDirection() const
{
	FVector Direction = ManualNightLightDirection;

	if (NightLightActor)
	{
		if (const UDirectionalLightComponent* DirectionalLight = NightLightActor->FindComponentByClass<UDirectionalLightComponent>())
		{
			Direction = DirectionalLight->GetForwardVector();
		}
		else
		{
			Direction = NightLightActor->GetActorForwardVector();
		}

		if (bInvertNightLightActorForward)
		{
			Direction *= -1.0f;
		}
	}

	if (!Direction.Normalize())
	{
		Direction = FVector(0.28f, -0.48f, 0.83f);
		Direction.Normalize();
	}

	return Direction;
}

float AStylizedSkyActor::GetSunElevationDegrees() const
{
	const FVector SunDirection = GetResolvedSunDirection();
	return FMath::RadiansToDegrees(FMath::Asin(FMath::Clamp(SunDirection.Z, -1.0f, 1.0f)));
}

void AStylizedSkyActor::SetTimeOfDayHours(float NewTimeOfDayHours)
{
	TimeOfDayHours = NormalizeTimeOfDayHours(NewTimeOfDayHours);
	TimeOfDayMinutes = TimeOfDayHoursToMinutes(TimeOfDayHours);
	RefreshSky();
}

void AStylizedSkyActor::SetTimeOfDayMinutes(int32 NewTimeOfDayMinutes)
{
	TimeOfDayMinutes = NormalizeTimeOfDayMinutes(NewTimeOfDayMinutes);
	TimeOfDayHours = TimeOfDayMinutesToHours(TimeOfDayMinutes);
	RefreshSky();
}

FVector AStylizedSkyActor::ComputeTimeOfDaySunDirection() const
{
	const float NormalizedHours = NormalizeTimeOfDayHours(TimeOfDayHours);
	const float DayPhase = (NormalizedHours - 6.0f) / 24.0f * 2.0f * UE_PI;
	const float SolarHeight = FMath::Sin(DayPhase);
	const float ElevationDegrees = SolarHeight >= 0.0f
		? SolarHeight * TimeOfDayMaxSunElevation
		: SolarHeight * TimeOfDayMaxNightDepression;

	const float AzimuthDegrees = TimeOfDayAzimuthDegrees + NormalizedHours / 24.0f * 360.0f;
	const float ElevationRadians = FMath::DegreesToRadians(ElevationDegrees);
	const float AzimuthRadians = FMath::DegreesToRadians(AzimuthDegrees);
	const float Horizontal = FMath::Cos(ElevationRadians);

	return FVector(
		Horizontal * FMath::Cos(AzimuthRadians),
		Horizontal * FMath::Sin(AzimuthRadians),
		FMath::Sin(ElevationRadians)).GetSafeNormal();
}

void AStylizedSkyActor::ApplyCloudPlaneSettingsToComponents()
{
	ApplyComponentSettings(true);
	EnsureDynamicMaterials();
	RefreshSky();
}

void AStylizedSkyActor::ApplyComponentSettings(bool bApplyTransforms)
{
	if (SkyDomeMesh)
	{
		SkyDomeComponent->SetStaticMesh(SkyDomeMesh);
	}

	if (SkyDomeMaterial)
	{
		SkyDomeComponent->SetMaterial(0, SkyDomeMaterial);
	}

	const TArray<UStaticMeshComponent*> CloudComponents = GetCloudPlaneComponents();
	for (int32 Index = 0; Index < CloudComponents.Num(); ++Index)
	{
		UStaticMeshComponent* CloudComponent = CloudComponents[Index];
		if (!CloudComponent)
		{
			continue;
		}

		const FStylizedSkyCloudPlaneSettings Settings = CloudPlaneSettings.IsValidIndex(Index)
			? CloudPlaneSettings[Index]
			: FStylizedSkyCloudPlaneSettings();

		CloudComponent->SetVisibility(Settings.bEnabled);
		CloudComponent->SetHiddenInGame(!Settings.bEnabled);
		CloudComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		CloudComponent->SetCastShadow(false);
		CloudComponent->SetGenerateOverlapEvents(false);
		CloudComponent->bReceivesDecals = false;
		CloudComponent->SetTranslucentSortPriority(Settings.TranslucencySortPriority);

		if (bApplyTransforms)
		{
			CloudComponent->SetRelativeTransform(Settings.RelativeTransform);
		}

		if (CloudPlaneMesh)
		{
			CloudComponent->SetStaticMesh(CloudPlaneMesh);
		}

		UMaterialInterface* SourceMaterial = Settings.MaterialOverride;
		if (!SourceMaterial && CloudTileMaterials.IsValidIndex(Index))
		{
			SourceMaterial = CloudTileMaterials[Index];
		}
		if (!SourceMaterial)
		{
			SourceMaterial = DefaultCloudMaterial;
		}
		if (SourceMaterial)
		{
			CloudComponent->SetMaterial(0, SourceMaterial);
		}
	}
}

void AStylizedSkyActor::EnsureDynamicMaterials()
{
	if (SkyDomeComponent && SkyDomeMaterial)
	{
		if (!SkyDomeMID || SkyDomeComponent->GetMaterial(0) != SkyDomeMID)
		{
			SkyDomeMID = SkyDomeComponent->CreateDynamicMaterialInstance(0, SkyDomeMaterial);
		}
	}

	const TArray<UStaticMeshComponent*> CloudComponents = GetCloudPlaneComponents();
	CloudMIDs.SetNum(CloudComponents.Num());

	for (int32 Index = 0; Index < CloudComponents.Num(); ++Index)
	{
		UStaticMeshComponent* CloudComponent = CloudComponents[Index];
		if (!CloudComponent)
		{
			CloudMIDs[Index] = nullptr;
			continue;
		}

		UMaterialInterface* SourceMaterial = nullptr;
		if (CloudPlaneSettings.IsValidIndex(Index))
		{
			SourceMaterial = CloudPlaneSettings[Index].MaterialOverride;
		}
		if (!SourceMaterial && CloudTileMaterials.IsValidIndex(Index))
		{
			SourceMaterial = CloudTileMaterials[Index];
		}
		if (!SourceMaterial)
		{
			SourceMaterial = DefaultCloudMaterial;
		}

		if (SourceMaterial && (!CloudMIDs[Index] || CloudComponent->GetMaterial(0) != CloudMIDs[Index]))
		{
			CloudMIDs[Index] = CloudComponent->CreateDynamicMaterialInstance(0, SourceMaterial);
		}
	}
}

void AStylizedSkyActor::ApplyTimeOfDayToSunActor(const FVector& SunDirection)
{
	if (!SunActor)
	{
		return;
	}

	FVector ForwardDirection = bInvertSunActorForward ? -SunDirection : SunDirection;
	if (!ForwardDirection.Normalize())
	{
		return;
	}

	const FRotator TargetRotation = FRotationMatrix::MakeFromX(ForwardDirection).Rotator();
	if (!SunActor->GetActorRotation().Equals(TargetRotation, 0.01f))
	{
		SunActor->SetActorRotation(TargetRotation);
	}
}

void AStylizedSkyActor::ApplyLookToEnvironment(const FStylizedSkyLookSettings& Look) const
{
	if (bDriveDirectionalLightFromLook && SunActor)
	{
		if (UDirectionalLightComponent* DirectionalLight = SunActor->FindComponentByClass<UDirectionalLightComponent>())
		{
#if WITH_EDITOR
			DirectionalLight->Modify();
#endif
			DirectionalLight->SetIntensity(FMath::Max(0.0f, Look.DirectionalLightIntensity));
			DirectionalLight->SetLightColor(Look.DirectionalLightColor, false);
			DirectionalLight->SetVolumetricScatteringIntensity(FMath::Max(0.0f, Look.DirectionalLightVolumetricScatteringIntensity));
		}
	}

	if (bDriveNightLightFromLook && NightLightActor)
	{
		if (UDirectionalLightComponent* NightLight = NightLightActor->FindComponentByClass<UDirectionalLightComponent>())
		{
#if WITH_EDITOR
			NightLight->Modify();
#endif
			NightLight->SetIntensity(FMath::Max(0.0f, Look.NightLightIntensity));
			NightLight->SetLightColor(Look.NightLightColor, false);
			NightLight->SetVolumetricScatteringIntensity(FMath::Max(0.0f, Look.NightLightVolumetricScatteringIntensity));
		}
	}

	if (bDriveSkyLightFromLook && SkyLightActor)
	{
		if (USkyLightComponent* SkyLight = SkyLightActor->FindComponentByClass<USkyLightComponent>())
		{
#if WITH_EDITOR
			SkyLight->Modify();
#endif
			SkyLight->SetIntensity(FMath::Max(0.0f, Look.SkyLightIntensity));
			SkyLight->SetLightColor(Look.SkyLightColor);
		}
	}

	if (bDriveSkyAtmosphereFromLook && SkyAtmosphereActor)
	{
		if (USkyAtmosphereComponent* SkyAtmosphere = SkyAtmosphereActor->FindComponentByClass<USkyAtmosphereComponent>())
		{
#if WITH_EDITOR
			SkyAtmosphere->Modify();
#endif
			SkyAtmosphere->SetSkyLuminanceFactor(Look.SkyAtmosphereSkyLuminanceFactor);
			SkyAtmosphere->SetSkyAndAerialPerspectiveLuminanceFactor(Look.SkyAtmosphereAerialPerspectiveLuminanceFactor);
			SkyAtmosphere->SetRayleighScattering(Look.SkyAtmosphereRayleighScattering);
			SkyAtmosphere->SetRayleighScatteringScale(FMath::Max(0.0f, Look.SkyAtmosphereRayleighScatteringScale));
			SkyAtmosphere->SetMieScattering(Look.SkyAtmosphereMieScattering);
			SkyAtmosphere->SetMieScatteringScale(FMath::Max(0.0f, Look.SkyAtmosphereMieScatteringScale));
		}
	}
}

void AStylizedSkyActor::ApplyLookToMaterial(
	UMaterialInstanceDynamic* Material,
	const FStylizedSkyLookSettings& Look,
	const FVector& SunDirection,
	const FVector& MoonDirection,
	float SunElevation,
	const FVector& LightWeights) const
{
	if (!Material)
	{
		return;
	}

	Material->SetVectorParameterValue(ParameterNames.SunDirection, FLinearColor(SunDirection.X, SunDirection.Y, SunDirection.Z, 0.0f));
	Material->SetScalarParameterValue(ParameterNames.SunElevation, SunElevation);
	Material->SetVectorParameterValue(ParameterNames.SkyZenithColor, Look.SkyZenithColor);
	Material->SetVectorParameterValue(ParameterNames.SkyHorizonColor, Look.SkyHorizonColor);
	Material->SetVectorParameterValue(ParameterNames.SunColor, Look.SunColor);
	Material->SetVectorParameterValue(ParameterNames.MoonDirection, FLinearColor(MoonDirection.X, MoonDirection.Y, MoonDirection.Z, 0.0f));
	Material->SetVectorParameterValue(ParameterNames.MoonColor, Look.MoonColor);
	Material->SetScalarParameterValue(ParameterNames.MoonIntensity, Look.MoonIntensity);
	Material->SetScalarParameterValue(ParameterNames.MoonAngularSizeDegrees, Look.MoonAngularSizeDegrees);
	Material->SetScalarParameterValue(ParameterNames.MoonGlowIntensity, Look.MoonGlowIntensity);
	Material->SetScalarParameterValue(ParameterNames.StarsIntensity, Look.StarsIntensity);
	Material->SetVectorParameterValue(ParameterNames.StarsColor, Look.StarsColor);
	Material->SetScalarParameterValue(ParameterNames.StarsTiling, StarsTiling);
	Material->SetScalarParameterValue(ParameterNames.StarsMaskThreshold, StarsMaskThreshold);
	Material->SetScalarParameterValue(ParameterNames.StarsMaskPower, StarsMaskPower);
	if (StarsMaskTexture)
	{
		Material->SetTextureParameterValue(ParameterNames.StarsMaskMap, StarsMaskTexture);
	}
	if (StarsMilkyWayTexture)
	{
		Material->SetTextureParameterValue(ParameterNames.StarsMilkyWayTexture, StarsMilkyWayTexture);
	}

	if (PackedCloudAtlasTexture)
	{
		Material->SetTextureParameterValue(ParameterNames.PackedCloudAtlas, PackedCloudAtlasTexture);
	}

	Material->SetVectorParameterValue(ParameterNames.LightWeightsRGB, FLinearColor(LightWeights.X, LightWeights.Y, LightWeights.Z, 0.0f));
	Material->SetVectorParameterValue(ParameterNames.CloudLightTint, Look.CloudLightTint);
	Material->SetVectorParameterValue(ParameterNames.CloudShadowTint, Look.CloudShadowTint);
	Material->SetVectorParameterValue(ParameterNames.TimeOfDayTint, Look.TimeOfDayTint);
	Material->SetScalarParameterValue(ParameterNames.CloudOpacity, Look.CloudOpacity);
	Material->SetScalarParameterValue(ParameterNames.CloudIntensity, Look.CloudIntensity);
}

FStylizedSkyLookSettings AStylizedSkyActor::BlendLookSettings(float SunElevation) const
{
	const FVector Weights = ComputeLookWeights(SunElevation);

	FStylizedSkyLookSettings Result;
	Result.SkyZenithColor = StylizedSky::LerpLookColor(NightLook.SkyZenithColor, SunsetLook.SkyZenithColor, DayLook.SkyZenithColor, Weights);
	Result.SkyHorizonColor = StylizedSky::LerpLookColor(NightLook.SkyHorizonColor, SunsetLook.SkyHorizonColor, DayLook.SkyHorizonColor, Weights);
	Result.SunColor = StylizedSky::LerpLookColor(NightLook.SunColor, SunsetLook.SunColor, DayLook.SunColor, Weights);
	Result.CloudLightTint = StylizedSky::LerpLookColor(NightLook.CloudLightTint, SunsetLook.CloudLightTint, DayLook.CloudLightTint, Weights);
	Result.CloudShadowTint = StylizedSky::LerpLookColor(NightLook.CloudShadowTint, SunsetLook.CloudShadowTint, DayLook.CloudShadowTint, Weights);
	Result.TimeOfDayTint = StylizedSky::LerpLookColor(NightLook.TimeOfDayTint, SunsetLook.TimeOfDayTint, DayLook.TimeOfDayTint, Weights);
	Result.CloudOpacity = StylizedSky::LerpLookFloat(NightLook.CloudOpacity, SunsetLook.CloudOpacity, DayLook.CloudOpacity, Weights);
	Result.CloudIntensity = StylizedSky::LerpLookFloat(NightLook.CloudIntensity, SunsetLook.CloudIntensity, DayLook.CloudIntensity, Weights);
	Result.StarsIntensity = StylizedSky::LerpLookFloat(NightLook.StarsIntensity, SunsetLook.StarsIntensity, DayLook.StarsIntensity, Weights);
	Result.StarsColor = StylizedSky::LerpLookColor(NightLook.StarsColor, SunsetLook.StarsColor, DayLook.StarsColor, Weights);
	Result.DirectionalLightIntensity = StylizedSky::LerpLookFloat(NightLook.DirectionalLightIntensity, SunsetLook.DirectionalLightIntensity, DayLook.DirectionalLightIntensity, Weights);
	Result.DirectionalLightColor = StylizedSky::LerpLookColor(NightLook.DirectionalLightColor, SunsetLook.DirectionalLightColor, DayLook.DirectionalLightColor, Weights);
	Result.DirectionalLightVolumetricScatteringIntensity = StylizedSky::LerpLookFloat(NightLook.DirectionalLightVolumetricScatteringIntensity, SunsetLook.DirectionalLightVolumetricScatteringIntensity, DayLook.DirectionalLightVolumetricScatteringIntensity, Weights);
	Result.NightLightIntensity = StylizedSky::LerpLookFloat(NightLook.NightLightIntensity, SunsetLook.NightLightIntensity, DayLook.NightLightIntensity, Weights);
	Result.NightLightColor = StylizedSky::LerpLookColor(NightLook.NightLightColor, SunsetLook.NightLightColor, DayLook.NightLightColor, Weights);
	Result.NightLightVolumetricScatteringIntensity = StylizedSky::LerpLookFloat(NightLook.NightLightVolumetricScatteringIntensity, SunsetLook.NightLightVolumetricScatteringIntensity, DayLook.NightLightVolumetricScatteringIntensity, Weights);
	Result.MoonColor = StylizedSky::LerpLookColor(NightLook.MoonColor, SunsetLook.MoonColor, DayLook.MoonColor, Weights);
	Result.MoonIntensity = StylizedSky::LerpLookFloat(NightLook.MoonIntensity, SunsetLook.MoonIntensity, DayLook.MoonIntensity, Weights);
	Result.MoonAngularSizeDegrees = StylizedSky::LerpLookFloat(NightLook.MoonAngularSizeDegrees, SunsetLook.MoonAngularSizeDegrees, DayLook.MoonAngularSizeDegrees, Weights);
	Result.MoonGlowIntensity = StylizedSky::LerpLookFloat(NightLook.MoonGlowIntensity, SunsetLook.MoonGlowIntensity, DayLook.MoonGlowIntensity, Weights);
	Result.SkyLightIntensity = StylizedSky::LerpLookFloat(NightLook.SkyLightIntensity, SunsetLook.SkyLightIntensity, DayLook.SkyLightIntensity, Weights);
	Result.SkyLightColor = StylizedSky::LerpLookColor(NightLook.SkyLightColor, SunsetLook.SkyLightColor, DayLook.SkyLightColor, Weights);
	Result.SkyAtmosphereSkyLuminanceFactor = StylizedSky::LerpLookColor(NightLook.SkyAtmosphereSkyLuminanceFactor, SunsetLook.SkyAtmosphereSkyLuminanceFactor, DayLook.SkyAtmosphereSkyLuminanceFactor, Weights);
	Result.SkyAtmosphereAerialPerspectiveLuminanceFactor = StylizedSky::LerpLookColor(NightLook.SkyAtmosphereAerialPerspectiveLuminanceFactor, SunsetLook.SkyAtmosphereAerialPerspectiveLuminanceFactor, DayLook.SkyAtmosphereAerialPerspectiveLuminanceFactor, Weights);
	Result.SkyAtmosphereRayleighScattering = StylizedSky::LerpLookColor(NightLook.SkyAtmosphereRayleighScattering, SunsetLook.SkyAtmosphereRayleighScattering, DayLook.SkyAtmosphereRayleighScattering, Weights);
	Result.SkyAtmosphereRayleighScatteringScale = StylizedSky::LerpLookFloat(NightLook.SkyAtmosphereRayleighScatteringScale, SunsetLook.SkyAtmosphereRayleighScatteringScale, DayLook.SkyAtmosphereRayleighScatteringScale, Weights);
	Result.SkyAtmosphereMieScattering = StylizedSky::LerpLookColor(NightLook.SkyAtmosphereMieScattering, SunsetLook.SkyAtmosphereMieScattering, DayLook.SkyAtmosphereMieScattering, Weights);
	Result.SkyAtmosphereMieScatteringScale = StylizedSky::LerpLookFloat(NightLook.SkyAtmosphereMieScatteringScale, SunsetLook.SkyAtmosphereMieScatteringScale, DayLook.SkyAtmosphereMieScatteringScale, Weights);
	return Result;
}

FVector AStylizedSkyActor::ComputeLookWeights(float SunElevation) const
{
	const float DayWeightRaw = StylizedSky::SmoothStep01(DayStartElevation, DayFullElevation, SunElevation);
	const float NightWeightRaw = 1.0f - StylizedSky::SmoothStep01(NightFullElevation, NightEndElevation, SunElevation);

	const float SunsetDistance = FMath::Abs(SunElevation - SunsetPeakElevation);
	float SunsetWeightRaw = FMath::Clamp(1.0f - SunsetDistance / FMath::Max(SunsetWidthDegrees, 1.0f), 0.0f, 1.0f);
	SunsetWeightRaw *= SunsetWeightRaw;
	SunsetWeightRaw *= (1.0f - DayWeightRaw * 0.55f);
	SunsetWeightRaw *= (1.0f - NightWeightRaw * 0.45f);

	const float Total = FMath::Max(KINDA_SMALL_NUMBER, NightWeightRaw + SunsetWeightRaw + DayWeightRaw);
	return FVector(NightWeightRaw / Total, SunsetWeightRaw / Total, DayWeightRaw / Total);
}

FVector AStylizedSkyActor::ComputePackedLightWeights(const FVector& SunDirection, float SunElevation) const
{
	FVector LocalSun = GetActorTransform().InverseTransformVectorNoScale(SunDirection);
	if (!LocalSun.Normalize())
	{
		LocalSun = FVector::UpVector;
	}
	const float HorizonAmount = FMath::Clamp(1.0f - FMath::Abs(LocalSun.Z), 0.0f, 1.0f);
	const float AboveHorizon = StylizedSky::SmoothStep01(-8.0f, 18.0f, SunElevation);

	float RightKey = FMath::Max(0.0f, LocalSun.Y) * HorizonAmount * AboveHorizon;
	float LeftKey = FMath::Max(0.0f, -LocalSun.Y) * HorizonAmount * AboveHorizon;
	float OverheadFill = (0.18f + FMath::Max(0.0f, LocalSun.Z) * 0.82f) * FMath::Max(AboveHorizon, 0.15f);

	RightKey = FMath::Max(RightKey, 0.035f * AboveHorizon);
	LeftKey = FMath::Max(LeftKey, 0.035f * AboveHorizon);
	OverheadFill = FMath::Max(OverheadFill, 0.10f);

	const float Total = FMath::Max(KINDA_SMALL_NUMBER, RightKey + LeftKey + OverheadFill);
	return FVector(RightKey / Total, LeftKey / Total, OverheadFill / Total);
}

float AStylizedSkyActor::NormalizeTimeOfDayHours(float Hours) const
{
	float Result = FMath::Fmod(Hours, 24.0f);
	if (Result < 0.0f)
	{
		Result += 24.0f;
	}

	return FMath::Clamp(Result, 0.0f, 24.0f);
}

int32 AStylizedSkyActor::NormalizeTimeOfDayMinutes(int32 Minutes) const
{
	int32 Result = Minutes % 1440;
	if (Result < 0)
	{
		Result += 1440;
	}

	return FMath::Clamp(Result, 0, 1439);
}

int32 AStylizedSkyActor::TimeOfDayHoursToMinutes(float Hours) const
{
	const float NormalizedHours = NormalizeTimeOfDayHours(Hours);
	const int32 Minutes = FMath::RoundToInt(NormalizedHours * 60.0f);
	return NormalizeTimeOfDayMinutes(Minutes);
}

float AStylizedSkyActor::TimeOfDayMinutesToHours(int32 Minutes) const
{
	return static_cast<float>(NormalizeTimeOfDayMinutes(Minutes)) / 60.0f;
}

FName AStylizedSkyActor::ComputeTimeOfDayPhase(const FVector& LookWeights) const
{
	if (LookWeights.Z >= 0.65f)
	{
		return TEXT("Day");
	}
	if (LookWeights.Y >= 0.35f)
	{
		return TEXT("Sunset");
	}
	if (LookWeights.X >= 0.65f)
	{
		return TEXT("Night");
	}

	return TEXT("Blend");
}

TArray<UStaticMeshComponent*> AStylizedSkyActor::GetCloudPlaneComponents() const
{
	return {
		CloudPlane0,
		CloudPlane1,
		CloudPlane2,
		CloudPlane3,
		CloudPlane4,
		CloudPlane5,
		CloudPlane6,
		CloudPlane7
	};
}
