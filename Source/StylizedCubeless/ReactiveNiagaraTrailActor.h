#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ReactiveNiagaraTrailActor.generated.h"

class UNiagaraComponent;
class UReactiveSocketComponent;
class USceneComponent;
class UTexture2D;
class UTextureRenderTarget2D;

USTRUCT(BlueprintType)
struct FReactiveSocketTrailPoint
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive")
	FVector WorldLocation = FVector::ZeroVector;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive")
	float Age = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive")
	float StampRadiusUV = 0.04f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive")
	FLinearColor StampColor = FLinearColor::White;
};

UCLASS(Blueprintable, BlueprintType)
class STYLIZEDCUBELESS_API AReactiveNiagaraTrailActor : public AActor
{
	GENERATED_BODY()

public:
	AReactiveNiagaraTrailActor();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive")
	TObjectPtr<USceneComponent> Root = nullptr;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive")
	TObjectPtr<UNiagaraComponent> ReactiveNiagara = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	TObjectPtr<UTextureRenderTarget2D> ReactiveRenderTarget = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	bool bAutoFindSocketsOnParentActor = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	bool bIncludeOwnSockets = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	bool bFollowParentActorAsRenderTargetCenter = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive")
	FVector WorldCenter = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive", meta = (ClampMin = "1.0"))
	float WorldExtent = 2500.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target")
	bool bDrawDirectRenderTargetMask = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target")
	bool bClearRenderTargetOnBeginPlay = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target", meta = (ClampMin = "0.0"))
	float DrawInterval = 0.033f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Trail", meta = (ClampMin = "0.01"))
	float TrailLifetime = 4.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Trail", meta = (ClampMin = "1"))
	int32 MaxTrailPoints = 1024;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target")
	FLinearColor BackgroundColor = FLinearColor::Black;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Reactive|Render Target")
	TObjectPtr<UTexture2D> StampTexture = nullptr;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive|Runtime")
	float TimeSinceLastDraw = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Reactive|Runtime")
	TArray<FReactiveSocketTrailPoint> TrailPoints;

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION(BlueprintCallable, Category = "Reactive")
	void ClearTrail();

	UFUNCTION(BlueprintCallable, Category = "Reactive")
	void RebuildFromSockets(float DeltaSeconds);

protected:
	FVector GetRenderTargetWorldCenter() const;
	bool WorldLocationToUV(const FVector& Location, FVector2D& OutUV) const;
	void CollectReactiveSockets(TArray<UReactiveSocketComponent*>& OutSockets) const;
	void DrawRenderTargetMask();
};
