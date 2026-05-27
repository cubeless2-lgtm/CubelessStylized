#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GodotOceanWavesTypes.h"
#include "GodotOceanWavesComponent.generated.h"

class UMaterialInstanceDynamic;
class UMeshComponent;
class UTextureRenderTarget2D;
class AActor;

UCLASS(ClassGroup = (Rendering), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class GODOTOCEANWAVES_API UGodotOceanWavesComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UGodotOceanWavesComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ocean", meta = (ClampMin = "16", UIMin = "128", UIMax = "1024"))
	int32 MapSize = 512;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ocean")
	EGodotOceanWavesSimulationMode SimulationMode = EGodotOceanWavesSimulationMode::Preview;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ocean", meta = (ClampMin = "0.0", UIMin = "0.0", UIMax = "60.0"))
	float UpdatesPerSecond = 30.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ocean")
	TArray<FGodotOceanWaveCascadeParameters> Cascades;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ocean", meta = (ToolTip = "When enabled, the component maintains a stable three-cascade preview setup tuned for readable ocean swells. Disable this before hand-authoring custom cascades."))
	bool bUseRecommendedPreviewPreset = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ocean", meta = (ClampMin = "1", ClampMax = "4", UIMin = "1", UIMax = "4"))
	int32 MaxActiveCascades = 3;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Preview")
	bool bGeneratePreviewMaps = true;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "Output")
	TObjectPtr<UTextureRenderTarget2D> DisplacementRenderTarget = nullptr;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "Output")
	TObjectPtr<UTextureRenderTarget2D> NormalFoamRenderTarget = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Material")
	bool bAutoApplyToMesh = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Collision")
	bool bDisableTargetMeshCollision = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Material")
	TObjectPtr<UMeshComponent> TargetMeshComponent = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Material", meta = (ClampMin = "0"))
	int32 TargetMaterialIndex = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Material")
	FName DisplacementParameterName = TEXT("GOW_Displacement");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Material")
	FName NormalFoamParameterName = TEXT("GOW_NormalFoam");

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "Material")
	TObjectPtr<UMaterialInstanceDynamic> AppliedMaterialInstance = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Follow")
	bool bFollowViewTarget = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Follow", meta = (EditCondition = "bFollowViewTarget"))
	TObjectPtr<AActor> FollowTargetActor = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Follow", meta = (EditCondition = "bFollowViewTarget"))
	float OceanHeight = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Follow", meta = (EditCondition = "bFollowViewTarget", ClampMin = "0.0", UIMin = "0.0"))
	float FollowSnapSize = 0.0f;

	UFUNCTION(BlueprintCallable, Category = "Godot Ocean Waves")
	void RebuildOutputs();

	UFUNCTION(BlueprintCallable, Category = "Godot Ocean Waves")
	void ForceUpdate(float DeltaTime);

	UFUNCTION(BlueprintCallable, Category = "Godot Ocean Waves")
	void ApplyToMaterialInstance(UMaterialInstanceDynamic* MaterialInstance, FName InDisplacementParameterName = TEXT("GOW_Displacement"), FName InNormalFoamParameterName = TEXT("GOW_NormalFoam")) const;

protected:
	virtual void BeginPlay() override;
	virtual void OnRegister() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

#if WITH_EDITOR
	virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
#endif

private:
	float TimeSeconds = 0.0f;
	float UpdateAccumulator = 0.0f;

	void EnsureDefaultCascade();
	void CreateRenderTarget(TObjectPtr<UTextureRenderTarget2D>& RenderTarget, const TCHAR* Name);
	void DispatchPreviewCompute(float DeltaTime);
	void DispatchFFTCompute(float DeltaTime);
	void ApplyToTargetMesh();
	void UpdateFollowTarget();
	UMeshComponent* ResolveTargetMesh() const;
};
