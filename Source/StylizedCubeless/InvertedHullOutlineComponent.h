#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "InvertedHullOutlineComponent.generated.h"

class UMaterialInterface;
class UMaterialInstanceDynamic;
class USkeletalMesh;
class USkeletalMeshComponent;

UCLASS(ClassGroup = (Rendering), Blueprintable, BlueprintType, meta = (BlueprintSpawnableComponent))
class STYLIZEDCUBELESS_API UInvertedHullOutlineComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UInvertedHullOutlineComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outline")
	bool bOutlineEnabled = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outline", meta = (ClampMin = "0.0", UIMin = "0.0", UIMax = "10.0"))
	float OutlineThickness = 2.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outline")
	FLinearColor OutlineColor = FLinearColor::Black;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outline")
	TObjectPtr<UMaterialInterface> OutlineMaterial = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outline")
	FName ThicknessParameterName = TEXT("OutlineThickness");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outline")
	FName ColorParameterName = TEXT("OutlineColor");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outline")
	TObjectPtr<USkeletalMeshComponent> SourceMeshComponent = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outline")
	FName SourceMeshComponentName = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outline")
	TObjectPtr<USkeletalMesh> OutlineSkeletalMeshOverride = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Outline", meta = (ClampMin = "1.0", UIMin = "1.0", UIMax = "2.0"))
	float OutlineBoundsScale = 1.15f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Outline")
	TObjectPtr<USkeletalMeshComponent> OutlineMeshComponent = nullptr;

	UFUNCTION(BlueprintCallable, Category = "Outline")
	void RefreshOutline();

	UFUNCTION(BlueprintCallable, Category = "Outline")
	void SetOutlineEnabled(bool bNewEnabled);

	UFUNCTION(BlueprintCallable, Category = "Outline")
	void SetOutlineThickness(float NewThickness);

	UFUNCTION(BlueprintCallable, Category = "Outline")
	void SetOutlineColor(FLinearColor NewColor);

protected:
	virtual void OnRegister() override;
	virtual void BeginPlay() override;
	virtual void OnUnregister() override;
#if WITH_EDITOR
	virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
#endif

private:
	USkeletalMeshComponent* ResolveSourceMeshComponent() const;
	void CreateOutlineMeshComponent(USkeletalMeshComponent* SourceMesh);
	void ApplySourceMeshSettings(USkeletalMeshComponent* SourceMesh);
	void ApplyOutlineMaterial();
	void UpdateMaterialParameters();
	void DestroyOutlineMeshComponent();
};
