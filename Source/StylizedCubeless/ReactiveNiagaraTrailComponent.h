#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "ReactiveNiagaraTrailComponent.generated.h"

class UNiagaraComponent;
class UTexture2D;
class UTextureRenderTarget;
class UTextureRenderTarget2D;

USTRUCT(BlueprintType)
struct FReactiveTrailPoint
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive")
	FVector WorldLocation = FVector::ZeroVector;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive")
	float Age = 0.0f;
};

UCLASS(ClassGroup = (Reactive), Blueprintable, BlueprintType, meta = (BlueprintSpawnableComponent))
class STYLIZEDCUBELESS_API UReactiveNiagaraTrailComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UReactiveNiagaraTrailComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	TObjectPtr<UNiagaraComponent> NiagaraComponent = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	TObjectPtr<UTextureRenderTarget> ReactiveRenderTarget = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	FName PlayerUVParameter = TEXT("User.PlayerUV");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	FName CircleLocationParameter = TEXT("Module.CircleLocation");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	FName UserCircleLocationParameter = TEXT("User.CircleLocation");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	FName RenderTargetParameter = TEXT("User.ReactiveRT");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	TArray<FName> CircleLocationParameters;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	TArray<FName> RenderTargetParameters;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	FVector WorldCenter = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive", meta = (ClampMin = "1.0"))
	float WorldExtent = 2500.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	bool bClampUV = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	bool bFollowOwnerAsRenderTargetCenter = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target")
	bool bDrawDirectRenderTargetMask = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target")
	bool bPushRenderTargetToNiagara = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target")
	bool bClearRenderTargetOnBeginPlay = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target", meta = (ClampMin = "0.0"))
	float FadePerSecond = 0.35f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target", meta = (ClampMin = "0.001", ClampMax = "1.0"))
	float StampRadiusUV = 0.035f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target", meta = (ClampMin = "0.0"))
	float DrawInterval = 0.033f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Trail", meta = (ClampMin = "0.01"))
	float TrailLifetime = 4.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Trail", meta = (ClampMin = "0.0"))
	float MinStampDistanceWorld = 12.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Trail", meta = (ClampMin = "1"))
	int32 MaxTrailPoints = 512;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target")
	FLinearColor BackgroundColor = FLinearColor::Black;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target")
	FLinearColor StampColor = FLinearColor::White;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target")
	TObjectPtr<UTexture2D> StampTexture = nullptr;

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UFUNCTION(BlueprintCallable, Category = "Reactive")
	void PushTrailParameters();

private:
	UNiagaraComponent* ResolveNiagaraComponent();
	FVector2D CalculateOwnerUV() const;
	FVector GetRenderTargetWorldCenter() const;
	bool WorldLocationToUV(const FVector& Location, FVector2D& OutUV) const;
	void UpdateTrailPoints(float DeltaTime);
	void DrawDirectRenderTargetMask(float DeltaTime, const FVector2D& UV);
	UTextureRenderTarget2D* GetRenderTarget2D() const;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive|Runtime", meta = (AllowPrivateAccess = "true"))
	float TimeSinceLastDraw = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive|Runtime", meta = (AllowPrivateAccess = "true"))
	TArray<FReactiveTrailPoint> TrailPoints;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive|Runtime", meta = (AllowPrivateAccess = "true"))
	FVector LastStampWorldLocation = FVector(FLT_MAX, FLT_MAX, FLT_MAX);
};
