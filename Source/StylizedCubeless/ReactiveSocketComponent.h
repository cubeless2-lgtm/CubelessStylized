#pragma once

#include "Components/SceneComponent.h"
#include "CoreMinimal.h"
#include "ReactiveSocketComponent.generated.h"

UCLASS(ClassGroup = (Reactive), Blueprintable, BlueprintType, meta = (BlueprintSpawnableComponent))
class STYLIZEDCUBELESS_API UReactiveSocketComponent : public USceneComponent
{
	GENERATED_BODY()

public:
	UReactiveSocketComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	bool bReactiveEnabled = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	TObjectPtr<USceneComponent> SourceComponent = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	FName SourceSocketName = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive", meta = (ClampMin = "0.001", ClampMax = "1.0"))
	float StampRadiusUV = 0.04f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	FLinearColor StampColor = FLinearColor::White;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive", meta = (ClampMin = "0.0"))
	float MinStampDistanceWorld = 12.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive|Runtime")
	FVector LastStampedWorldLocation = FVector(FLT_MAX, FLT_MAX, FLT_MAX);

	UFUNCTION(BlueprintCallable, Category = "Reactive")
	FVector GetReactiveWorldLocation() const;

	UFUNCTION(BlueprintCallable, Category = "Reactive")
	bool ShouldStampAtLocation(const FVector& WorldLocation) const;

	UFUNCTION(BlueprintCallable, Category = "Reactive")
	void MarkStamped(const FVector& WorldLocation);
};
