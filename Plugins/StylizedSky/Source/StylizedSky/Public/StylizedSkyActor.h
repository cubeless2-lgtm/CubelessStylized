#pragma once

#include "CoreMinimal.h"
#if WITH_EDITOR
#include "Containers/Ticker.h"
#endif
#include "GameFramework/Actor.h"
#include "StylizedSkyActor.generated.h"

class UMaterialInstanceDynamic;
class UMaterialInterface;
class UStaticMesh;
class UStaticMeshComponent;
class USceneComponent;
class UTexture2D;
struct FPropertyChangedEvent;

USTRUCT(BlueprintType)
struct FStylizedSkyLookSettings
{
	GENERATED_BODY()

	FStylizedSkyLookSettings();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky")
	FLinearColor SkyZenithColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky")
	FLinearColor SkyHorizonColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky")
	FLinearColor SunColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky")
	FLinearColor CloudLightTint;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky")
	FLinearColor CloudShadowTint;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky")
	FLinearColor TimeOfDayTint;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky", meta = (ClampMin = "0.0"))
	float CloudOpacity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky", meta = (ClampMin = "0.0"))
	float CloudIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky", meta = (ClampMin = "0.0"))
	float StarsIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky")
	FLinearColor StarsColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Lighting", meta = (ClampMin = "0.0"))
	float DirectionalLightIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Lighting")
	FLinearColor DirectionalLightColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Lighting", meta = (ClampMin = "0.0"))
	float DirectionalLightVolumetricScatteringIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Night Light", meta = (ClampMin = "0.0"))
	float NightLightIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Night Light")
	FLinearColor NightLightColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Night Light", meta = (ClampMin = "0.0"))
	float NightLightVolumetricScatteringIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Moon")
	FLinearColor MoonColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Moon", meta = (ClampMin = "0.0"))
	float MoonIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Moon", meta = (ClampMin = "0.05", UIMin = "0.1", UIMax = "8.0"))
	float MoonAngularSizeDegrees;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Moon", meta = (ClampMin = "0.0", UIMin = "0.0", UIMax = "2.0"))
	float MoonGlowIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Lighting", meta = (ClampMin = "0.0"))
	float SkyLightIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Lighting")
	FLinearColor SkyLightColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Atmosphere")
	FLinearColor SkyAtmosphereSkyLuminanceFactor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Atmosphere")
	FLinearColor SkyAtmosphereAerialPerspectiveLuminanceFactor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Atmosphere")
	FLinearColor SkyAtmosphereRayleighScattering;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Atmosphere", meta = (ClampMin = "0.0"))
	float SkyAtmosphereRayleighScatteringScale;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Atmosphere")
	FLinearColor SkyAtmosphereMieScattering;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Atmosphere", meta = (ClampMin = "0.0"))
	float SkyAtmosphereMieScatteringScale;
};

USTRUCT(BlueprintType)
struct FStylizedSkyCloudPlaneSettings
{
	GENERATED_BODY()

	FStylizedSkyCloudPlaneSettings();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky")
	bool bEnabled;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky")
	FTransform RelativeTransform;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky")
	TObjectPtr<UMaterialInterface> MaterialOverride;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky", meta = (ClampMin = "0"))
	int32 TranslucencySortPriority;
};

USTRUCT(BlueprintType)
struct FStylizedSkyMaterialParameterNames
{
	GENERATED_BODY()

	FStylizedSkyMaterialParameterNames();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sky")
	FName SunDirection;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sky")
	FName SunElevation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sky")
	FName SkyZenithColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sky")
	FName SkyHorizonColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sky")
	FName SunColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Moon")
	FName MoonDirection;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Moon")
	FName MoonColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Moon")
	FName MoonIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Moon")
	FName MoonAngularSizeDegrees;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Moon")
	FName MoonGlowIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sky")
	FName StarsIntensity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sky")
	FName StarsColor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sky")
	FName StarsMilkyWayTexture;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sky")
	FName StarsMaskMap;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sky")
	FName StarsTiling;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sky")
	FName StarsMaskThreshold;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sky")
	FName StarsMaskPower;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Clouds")
	FName PackedCloudAtlas;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Clouds")
	FName LightWeightsRGB;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Clouds")
	FName CloudLightTint;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Clouds")
	FName CloudShadowTint;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Clouds")
	FName TimeOfDayTint;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Clouds")
	FName CloudOpacity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Clouds")
	FName CloudIntensity;
};

UCLASS(Blueprintable, ClassGroup = (Rendering))
class STYLIZEDSKY_API AStylizedSkyActor : public AActor
{
	GENERATED_BODY()

public:
	AStylizedSkyActor();

	virtual void BeginDestroy() override;
	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void Tick(float DeltaSeconds) override;

#if WITH_EDITOR
	virtual bool ShouldTickIfViewportsOnly() const override;
	virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
#endif

	UFUNCTION(BlueprintCallable, Category = "StylizedSky")
	void RefreshSky();

	UFUNCTION(BlueprintCallable, Category = "StylizedSky")
	FVector GetResolvedSunDirection() const;

	UFUNCTION(BlueprintCallable, Category = "StylizedSky")
	FVector GetResolvedNightLightDirection() const;

	UFUNCTION(BlueprintCallable, Category = "StylizedSky")
	float GetSunElevationDegrees() const;

	UFUNCTION(BlueprintCallable, Category = "StylizedSky|Time Of Day")
	void SetTimeOfDayHours(float NewTimeOfDayHours);

	UFUNCTION(BlueprintCallable, Category = "StylizedSky|Time Of Day")
	void SetTimeOfDayMinutes(int32 NewTimeOfDayMinutes);

	UFUNCTION(BlueprintCallable, Category = "StylizedSky|Time Of Day")
	FVector ComputeTimeOfDaySunDirection() const;

	UFUNCTION(BlueprintCallable, Category = "StylizedSky|Clouds")
	void ApplyCloudPlaneSettingsToComponents();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "StylizedSky|Components")
	TObjectPtr<USceneComponent> SceneRoot;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "StylizedSky|Components")
	TObjectPtr<UStaticMeshComponent> SkyDomeComponent;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "StylizedSky|Components")
	TObjectPtr<USceneComponent> CloudRootComponent;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "StylizedSky|Components")
	TObjectPtr<UStaticMeshComponent> CloudPlane0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "StylizedSky|Components")
	TObjectPtr<UStaticMeshComponent> CloudPlane1;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "StylizedSky|Components")
	TObjectPtr<UStaticMeshComponent> CloudPlane2;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "StylizedSky|Components")
	TObjectPtr<UStaticMeshComponent> CloudPlane3;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "StylizedSky|Components")
	TObjectPtr<UStaticMeshComponent> CloudPlane4;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "StylizedSky|Components")
	TObjectPtr<UStaticMeshComponent> CloudPlane5;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "StylizedSky|Components")
	TObjectPtr<UStaticMeshComponent> CloudPlane6;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "StylizedSky|Components")
	TObjectPtr<UStaticMeshComponent> CloudPlane7;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sun")
	TObjectPtr<AActor> SunActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Night Light")
	TObjectPtr<AActor> NightLightActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Lighting")
	TObjectPtr<AActor> SkyLightActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Atmosphere")
	TObjectPtr<AActor> SkyAtmosphereActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sun")
	FVector ManualSunDirection;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Night Light")
	FVector ManualNightLightDirection;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Sun")
	bool bInvertSunActorForward;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Night Light")
	bool bInvertNightLightActorForward;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Time Of Day")
	bool bUseTimeOfDayPreview;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Time Of Day", meta = (EditCondition = "bUseTimeOfDayPreview"))
	bool bDriveSunActorFromTimeOfDay;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Lighting", meta = (EditCondition = "bUseTimeOfDayPreview"))
	bool bDriveDirectionalLightFromLook;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Night Light", meta = (EditCondition = "bUseTimeOfDayPreview"))
	bool bDriveNightLightFromLook;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Lighting", meta = (EditCondition = "bUseTimeOfDayPreview"))
	bool bDriveSkyLightFromLook;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Atmosphere", meta = (EditCondition = "bUseTimeOfDayPreview"))
	bool bDriveSkyAtmosphereFromLook;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Time Of Day", meta = (ClampMin = "0.0", ClampMax = "24.0", UIMin = "0.0", UIMax = "24.0", EditCondition = "bUseTimeOfDayPreview"))
	float TimeOfDayHours;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Time Of Day", meta = (ClampMin = "0", ClampMax = "1439", UIMin = "0", UIMax = "1439", EditCondition = "bUseTimeOfDayPreview", DisplayName = "Time Of Day Minutes (0-1439)"))
	int32 TimeOfDayMinutes;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Time Of Day", meta = (EditCondition = "bUseTimeOfDayPreview"))
	bool bAnimateTimeOfDay;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Time Of Day", meta = (ClampMin = "-1440.0", ClampMax = "1440.0", UIMin = "-240.0", UIMax = "240.0", EditCondition = "bUseTimeOfDayPreview"))
	float TimeOfDaySpeedMinutesPerSecond;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Time Of Day", meta = (ClampMin = "-360.0", ClampMax = "360.0", UIMin = "-180.0", UIMax = "180.0", EditCondition = "bUseTimeOfDayPreview"))
	float TimeOfDayAzimuthDegrees;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Time Of Day", meta = (ClampMin = "1.0", ClampMax = "90.0", UIMin = "35.0", UIMax = "85.0", EditCondition = "bUseTimeOfDayPreview"))
	float TimeOfDayMaxSunElevation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Time Of Day", meta = (ClampMin = "1.0", ClampMax = "90.0", UIMin = "20.0", UIMax = "75.0", EditCondition = "bUseTimeOfDayPreview"))
	float TimeOfDayMaxNightDepression;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "StylizedSky|Time Of Day")
	float CurrentTimeOfDayHours;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "StylizedSky|Time Of Day")
	int32 CurrentTimeOfDayMinutes;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "StylizedSky|Time Of Day")
	float CurrentSunElevationDegrees;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "StylizedSky|Time Of Day")
	FVector CurrentLookWeights_NightSunsetDay;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "StylizedSky|Time Of Day")
	FName CurrentTimeOfDayPhase;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Update")
	bool bUpdateEveryTick;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Update")
	bool bUpdateInEditor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Assets")
	TObjectPtr<UStaticMesh> SkyDomeMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Assets")
	TObjectPtr<UMaterialInterface> SkyDomeMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Assets")
	TObjectPtr<UStaticMesh> CloudPlaneMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Assets")
	TObjectPtr<UMaterialInterface> DefaultCloudMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Assets")
	TObjectPtr<UTexture2D> PackedCloudAtlasTexture;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Stars")
	TObjectPtr<UTexture2D> StarsMilkyWayTexture;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Stars")
	TObjectPtr<UTexture2D> StarsMaskTexture;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Stars", meta = (ClampMin = "0.1", UIMin = "0.25", UIMax = "8.0"))
	float StarsTiling;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Stars", meta = (ClampMin = "0.0", ClampMax = "1.0", UIMin = "0.0", UIMax = "1.0"))
	float StarsMaskThreshold;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Stars", meta = (ClampMin = "0.1", UIMin = "0.25", UIMax = "4.0"))
	float StarsMaskPower;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Assets")
	TArray<TObjectPtr<UMaterialInterface>> CloudTileMaterials;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Clouds")
	TArray<FStylizedSkyCloudPlaneSettings> CloudPlaneSettings;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Clouds")
	bool bApplyCloudPlaneSettingsOnConstruction;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Look")
	FStylizedSkyLookSettings DayLook;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Look")
	FStylizedSkyLookSettings SunsetLook;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Look")
	FStylizedSkyLookSettings NightLook;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Look", meta = (ClampMin = "-90.0", ClampMax = "90.0"))
	float DayStartElevation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Look", meta = (ClampMin = "-90.0", ClampMax = "90.0"))
	float DayFullElevation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Look", meta = (ClampMin = "-90.0", ClampMax = "90.0"))
	float NightFullElevation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Look", meta = (ClampMin = "-90.0", ClampMax = "90.0"))
	float NightEndElevation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Look", meta = (ClampMin = "-90.0", ClampMax = "90.0"))
	float SunsetPeakElevation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Look", meta = (ClampMin = "1.0"))
	float SunsetWidthDegrees;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StylizedSky|Parameters")
	FStylizedSkyMaterialParameterNames ParameterNames;

protected:
	void TickSky(float DeltaSeconds);
	void ApplyComponentSettings(bool bApplyTransforms);
	void EnsureDynamicMaterials();
	void ApplyTimeOfDayToSunActor(const FVector& SunDirection);
	void ApplyLookToEnvironment(const FStylizedSkyLookSettings& Look) const;
	void ApplyLookToMaterial(UMaterialInstanceDynamic* Material, const FStylizedSkyLookSettings& Look, const FVector& SunDirection, const FVector& MoonDirection, float SunElevation, const FVector& LightWeights) const;
	FStylizedSkyLookSettings BlendLookSettings(float SunElevation) const;
	FVector ComputeLookWeights(float SunElevation) const;
	FVector ComputePackedLightWeights(const FVector& SunDirection, float SunElevation) const;
	float NormalizeTimeOfDayHours(float Hours) const;
	int32 NormalizeTimeOfDayMinutes(int32 Minutes) const;
	int32 TimeOfDayHoursToMinutes(float Hours) const;
	float TimeOfDayMinutesToHours(int32 Minutes) const;
	FName ComputeTimeOfDayPhase(const FVector& LookWeights) const;
	TArray<UStaticMeshComponent*> GetCloudPlaneComponents() const;

#if WITH_EDITOR
	void EnsureEditorTicker();
	void ReleaseEditorTicker();
	bool HandleEditorTick(float DeltaSeconds);

	FTSTicker::FDelegateHandle EditorTickerHandle;
#endif

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> SkyDomeMID;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UMaterialInstanceDynamic>> CloudMIDs;
};
