#include "ReactiveNiagaraTrailComponent.h"

#include "Engine/Canvas.h"
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "NiagaraComponent.h"

UReactiveNiagaraTrailComponent::UReactiveNiagaraTrailComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;

	CircleLocationParameters = {
		TEXT("User.PlayerUV"),
		TEXT("User.CircleLocation"),
		TEXT("Module.CircleLocation"),
		TEXT("RenderCircleToGrid.CircleLocation"),
		TEXT("Constants.PaintGrid.RenderCircleToGrid.CircleLocation")
	};

	RenderTargetParameters = {
		TEXT("User.ReactiveRT"),
		TEXT("User.Render Target 2D"),
		TEXT("Emitter.Render Target 2D"),
		TEXT("Module.Render Target 2D"),
		TEXT("PaintGrid.Render Target 2D")
	};
}

void UReactiveNiagaraTrailComponent::BeginPlay()
{
	Super::BeginPlay();

	if (!StampTexture)
	{
		StampTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Engine/EngineResources/WhiteSquareTexture.WhiteSquareTexture"));
	}

	if (bClearRenderTargetOnBeginPlay)
	{
		if (UTextureRenderTarget2D* RenderTarget2D = GetRenderTarget2D())
		{
			UKismetRenderingLibrary::ClearRenderTarget2D(this, RenderTarget2D, BackgroundColor);
		}
	}

	PushTrailParameters();
}

void UReactiveNiagaraTrailComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	UpdateTrailPoints(DeltaTime);
	PushTrailParameters();

	if (bDrawDirectRenderTargetMask)
	{
		TimeSinceLastDraw += FMath::Max(DeltaTime, 0.0f);
		if (DrawInterval <= 0.0f || TimeSinceLastDraw >= DrawInterval)
		{
			const float DrawDeltaTime = TimeSinceLastDraw;
			TimeSinceLastDraw = 0.0f;
			DrawDirectRenderTargetMask(DrawDeltaTime, CalculateOwnerUV());
		}
	}
}

void UReactiveNiagaraTrailComponent::PushTrailParameters()
{
	UNiagaraComponent* Niagara = ResolveNiagaraComponent();
	if (!Niagara || WorldExtent <= 0.0f)
	{
		return;
	}

	const FVector2D UV = CalculateOwnerUV();

	Niagara->SetVariableVec2(PlayerUVParameter, UV);
	Niagara->SetVariableVec2(CircleLocationParameter, UV);
	Niagara->SetVariableVec2(UserCircleLocationParameter, UV);
	for (const FName& ParameterName : CircleLocationParameters)
	{
		if (!ParameterName.IsNone())
		{
			Niagara->SetVariableVec2(ParameterName, UV);
		}
	}

	if (bPushRenderTargetToNiagara && ReactiveRenderTarget)
	{
		Niagara->SetVariableTextureRenderTarget(RenderTargetParameter, ReactiveRenderTarget);
		for (const FName& ParameterName : RenderTargetParameters)
		{
			if (!ParameterName.IsNone())
			{
				Niagara->SetVariableTextureRenderTarget(ParameterName, ReactiveRenderTarget);
			}
		}
	}
}

UNiagaraComponent* UReactiveNiagaraTrailComponent::ResolveNiagaraComponent()
{
	if (NiagaraComponent)
	{
		return NiagaraComponent;
	}

	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return nullptr;
	}

	TArray<UNiagaraComponent*> Components;
	Owner->GetComponents<UNiagaraComponent>(Components);
	for (UNiagaraComponent* Component : Components)
	{
		if (Component && Component->GetName().Contains(TEXT("ReactiveNiagara")))
		{
			NiagaraComponent = Component;
			return Component;
		}
	}

	if (Components.Num() > 0)
	{
		NiagaraComponent = Components[0];
		return Components[0];
	}

	return nullptr;
}

FVector2D UReactiveNiagaraTrailComponent::CalculateOwnerUV() const
{
	FVector2D UV(0.5f, 0.5f);
	if (!WorldLocationToUV(GetOwner() ? GetOwner()->GetActorLocation() : GetRenderTargetWorldCenter(), UV))
	{
		return FVector2D(0.5f, 0.5f);
	}

	return UV;
}

FVector UReactiveNiagaraTrailComponent::GetRenderTargetWorldCenter() const
{
	if (bFollowOwnerAsRenderTargetCenter)
	{
		if (const AActor* Owner = GetOwner())
		{
			return Owner->GetActorLocation();
		}
	}

	return WorldCenter;
}

bool UReactiveNiagaraTrailComponent::WorldLocationToUV(const FVector& Location, FVector2D& OutUV) const
{
	if (WorldExtent <= 0.0f)
	{
		return false;
	}

	const FVector Center = GetRenderTargetWorldCenter();
	OutUV = FVector2D(
		((Location.X - Center.X) / (WorldExtent * 2.0f)) + 0.5f,
		((Location.Y - Center.Y) / (WorldExtent * 2.0f)) + 0.5f);

	if (bClampUV)
	{
		OutUV.X = FMath::Clamp(OutUV.X, 0.0, 1.0);
		OutUV.Y = FMath::Clamp(OutUV.Y, 0.0, 1.0);
	}

	return OutUV.X >= 0.0f && OutUV.X <= 1.0f && OutUV.Y >= 0.0f && OutUV.Y <= 1.0f;
}

void UReactiveNiagaraTrailComponent::UpdateTrailPoints(float DeltaTime)
{
	const AActor* Owner = GetOwner();
	if (!Owner || TrailLifetime <= 0.0f)
	{
		TrailPoints.Reset();
		return;
	}

	for (int32 Index = TrailPoints.Num() - 1; Index >= 0; --Index)
	{
		TrailPoints[Index].Age += FMath::Max(DeltaTime, 0.0f);
		if (TrailPoints[Index].Age > TrailLifetime)
		{
			TrailPoints.RemoveAtSwap(Index, 1, EAllowShrinking::No);
		}
	}

	const FVector Location = Owner->GetActorLocation();
	const bool bShouldAddFirstPoint = TrailPoints.Num() == 0 || LastStampWorldLocation.X == FLT_MAX;
	const bool bMovedEnough = bShouldAddFirstPoint || FVector::DistSquared2D(Location, LastStampWorldLocation) >= FMath::Square(MinStampDistanceWorld);
	if (bMovedEnough)
	{
		FReactiveTrailPoint Point;
		Point.WorldLocation = Location;
		Point.Age = 0.0f;
		TrailPoints.Add(Point);
		LastStampWorldLocation = Location;
	}

	while (TrailPoints.Num() > MaxTrailPoints)
	{
		TrailPoints.RemoveAt(0, 1, EAllowShrinking::No);
	}
}

void UReactiveNiagaraTrailComponent::DrawDirectRenderTargetMask(float DeltaTime, const FVector2D& UV)
{
	const UWorld* World = GetWorld();
	if (!World || !World->IsGameWorld())
	{
		return;
	}

	UTextureRenderTarget2D* RenderTarget2D = GetRenderTarget2D();
	if (!RenderTarget2D || !StampTexture)
	{
		return;
	}

	UCanvas* Canvas = nullptr;
	FVector2D CanvasSize = FVector2D::ZeroVector;
	FDrawToRenderTargetContext Context;
	UKismetRenderingLibrary::BeginDrawCanvasToRenderTarget(this, RenderTarget2D, Canvas, CanvasSize, Context);
	if (!Canvas)
	{
		UKismetRenderingLibrary::EndDrawCanvasToRenderTarget(this, Context);
		return;
	}

	Canvas->K2_DrawTexture(StampTexture, FVector2D::ZeroVector, CanvasSize, FVector2D::ZeroVector, FVector2D::UnitVector, BackgroundColor, BLEND_Opaque);

	const float RadiusPixels = StampRadiusUV * FMath::Min(CanvasSize.X, CanvasSize.Y);
	for (const FReactiveTrailPoint& Point : TrailPoints)
	{
		FVector2D PointUV;
		if (!WorldLocationToUV(Point.WorldLocation, PointUV))
		{
			continue;
		}

		FLinearColor PointColor = StampColor;
		PointColor.A *= FMath::Clamp(1.0f - (Point.Age / FMath::Max(TrailLifetime, KINDA_SMALL_NUMBER)), 0.0f, 1.0f);
		const FVector2D StampCenter(PointUV.X * CanvasSize.X, PointUV.Y * CanvasSize.Y);
		Canvas->K2_DrawPolygon(StampTexture, StampCenter, FVector2D(RadiusPixels, RadiusPixels), 48, PointColor);
	}

	UKismetRenderingLibrary::EndDrawCanvasToRenderTarget(this, Context);
}

UTextureRenderTarget2D* UReactiveNiagaraTrailComponent::GetRenderTarget2D() const
{
	return Cast<UTextureRenderTarget2D>(ReactiveRenderTarget.Get());
}
