#include "ReactiveNiagaraTrailActor.h"

#include "Engine/Canvas.h"
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "NiagaraComponent.h"
#include "ReactiveSocketComponent.h"

AReactiveNiagaraTrailActor::AReactiveNiagaraTrailActor()
{
	PrimaryActorTick.bCanEverTick = true;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	ReactiveNiagara = CreateDefaultSubobject<UNiagaraComponent>(TEXT("ReactiveNiagara"));
	ReactiveNiagara->SetupAttachment(Root);
	ReactiveNiagara->SetAutoActivate(false);
}

void AReactiveNiagaraTrailActor::BeginPlay()
{
	Super::BeginPlay();

	if (!ReactiveRenderTarget)
	{
		ReactiveRenderTarget = LoadObject<UTextureRenderTarget2D>(nullptr, TEXT("/Game/Cuneless/Reactive/RT_Reactive_PlayerPosition.RT_Reactive_PlayerPosition"));
	}

	if (!StampTexture)
	{
		StampTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Engine/EngineResources/WhiteSquareTexture.WhiteSquareTexture"));
	}

	if (bClearRenderTargetOnBeginPlay && ReactiveRenderTarget)
	{
		UKismetRenderingLibrary::ClearRenderTarget2D(this, ReactiveRenderTarget, BackgroundColor);
	}
}

void AReactiveNiagaraTrailActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	RebuildFromSockets(DeltaSeconds);

	if (bDrawDirectRenderTargetMask)
	{
		TimeSinceLastDraw += FMath::Max(DeltaSeconds, 0.0f);
		if (DrawInterval <= 0.0f || TimeSinceLastDraw >= DrawInterval)
		{
			TimeSinceLastDraw = 0.0f;
			DrawRenderTargetMask();
		}
	}
}

void AReactiveNiagaraTrailActor::ClearTrail()
{
	TrailPoints.Reset();
	TimeSinceLastDraw = 0.0f;

	TArray<UReactiveSocketComponent*> Sockets;
	CollectReactiveSockets(Sockets);
	for (UReactiveSocketComponent* Socket : Sockets)
	{
		if (Socket)
		{
			Socket->LastStampedWorldLocation = FVector(FLT_MAX, FLT_MAX, FLT_MAX);
		}
	}

	if (ReactiveRenderTarget)
	{
		UKismetRenderingLibrary::ClearRenderTarget2D(this, ReactiveRenderTarget, BackgroundColor);
	}
}

void AReactiveNiagaraTrailActor::RebuildFromSockets(float DeltaSeconds)
{
	if (TrailLifetime <= 0.0f)
	{
		ClearTrail();
		return;
	}

	for (int32 Index = TrailPoints.Num() - 1; Index >= 0; --Index)
	{
		TrailPoints[Index].Age += FMath::Max(DeltaSeconds, 0.0f);
		if (TrailPoints[Index].Age > TrailLifetime)
		{
			TrailPoints.RemoveAtSwap(Index, 1, EAllowShrinking::No);
		}
	}

	TArray<UReactiveSocketComponent*> Sockets;
	CollectReactiveSockets(Sockets);
	for (UReactiveSocketComponent* Socket : Sockets)
	{
		if (!Socket || !Socket->bReactiveEnabled)
		{
			continue;
		}

		const FVector Location = Socket->GetReactiveWorldLocation();
		if (!Socket->ShouldStampAtLocation(Location))
		{
			continue;
		}

		FReactiveSocketTrailPoint Point;
		Point.WorldLocation = Location;
		Point.Age = 0.0f;
		Point.StampRadiusUV = Socket->StampRadiusUV;
		Point.StampColor = Socket->StampColor;
		TrailPoints.Add(Point);
		Socket->MarkStamped(Location);
	}

	while (TrailPoints.Num() > MaxTrailPoints)
	{
		TrailPoints.RemoveAt(0, 1, EAllowShrinking::No);
	}
}

FVector AReactiveNiagaraTrailActor::GetRenderTargetWorldCenter() const
{
	if (bFollowParentActorAsRenderTargetCenter)
	{
		if (const AActor* Parent = GetParentActor())
		{
			return Parent->GetActorLocation();
		}

		if (const AActor* OwnerActor = GetOwner())
		{
			return OwnerActor->GetActorLocation();
		}
	}

	return WorldCenter;
}

bool AReactiveNiagaraTrailActor::WorldLocationToUV(const FVector& Location, FVector2D& OutUV) const
{
	if (WorldExtent <= 0.0f)
	{
		return false;
	}

	const FVector Center = GetRenderTargetWorldCenter();
	OutUV = FVector2D(
		((Location.X - Center.X) / (WorldExtent * 2.0f)) + 0.5f,
		((Location.Y - Center.Y) / (WorldExtent * 2.0f)) + 0.5f);

	return OutUV.X >= 0.0f && OutUV.X <= 1.0f && OutUV.Y >= 0.0f && OutUV.Y <= 1.0f;
}

void AReactiveNiagaraTrailActor::CollectReactiveSockets(TArray<UReactiveSocketComponent*>& OutSockets) const
{
	OutSockets.Reset();

	if (bAutoFindSocketsOnParentActor)
	{
		if (AActor* Parent = GetParentActor())
		{
			Parent->GetComponents<UReactiveSocketComponent>(OutSockets);
		}
		else if (AActor* OwnerActor = GetOwner())
		{
			OwnerActor->GetComponents<UReactiveSocketComponent>(OutSockets);
		}
	}

	if (bIncludeOwnSockets)
	{
		TArray<UReactiveSocketComponent*> OwnSockets;
		GetComponents<UReactiveSocketComponent>(OwnSockets);
		OutSockets.Append(OwnSockets);
	}
}

void AReactiveNiagaraTrailActor::DrawRenderTargetMask()
{
	const UWorld* World = GetWorld();
	if (!World || !World->IsGameWorld() || !ReactiveRenderTarget || !StampTexture)
	{
		return;
	}

	UCanvas* Canvas = nullptr;
	FVector2D CanvasSize = FVector2D::ZeroVector;
	FDrawToRenderTargetContext Context;
	UKismetRenderingLibrary::BeginDrawCanvasToRenderTarget(this, ReactiveRenderTarget, Canvas, CanvasSize, Context);
	if (!Canvas)
	{
		UKismetRenderingLibrary::EndDrawCanvasToRenderTarget(this, Context);
		return;
	}

	Canvas->K2_DrawTexture(StampTexture, FVector2D::ZeroVector, CanvasSize, FVector2D::ZeroVector, FVector2D::UnitVector, BackgroundColor, BLEND_Opaque);

	for (const FReactiveSocketTrailPoint& Point : TrailPoints)
	{
		FVector2D UV;
		if (!WorldLocationToUV(Point.WorldLocation, UV))
		{
			continue;
		}

		FLinearColor PointColor = Point.StampColor;
		PointColor.A *= FMath::Clamp(1.0f - (Point.Age / FMath::Max(TrailLifetime, KINDA_SMALL_NUMBER)), 0.0f, 1.0f);
		const float RadiusPixels = Point.StampRadiusUV * FMath::Min(CanvasSize.X, CanvasSize.Y);
		const FVector2D StampCenter(UV.X * CanvasSize.X, UV.Y * CanvasSize.Y);
		Canvas->K2_DrawPolygon(StampTexture, StampCenter, FVector2D(RadiusPixels, RadiusPixels), 48, PointColor);
	}

	UKismetRenderingLibrary::EndDrawCanvasToRenderTarget(this, Context);
}
