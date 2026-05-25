#include "ReactiveSocketComponent.h"

UReactiveSocketComponent::UReactiveSocketComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

FVector UReactiveSocketComponent::GetReactiveWorldLocation() const
{
	if (SourceComponent && !SourceSocketName.IsNone() && SourceComponent->DoesSocketExist(SourceSocketName))
	{
		return SourceComponent->GetSocketLocation(SourceSocketName);
	}

	if (!SourceSocketName.IsNone())
	{
		if (const AActor* Owner = GetOwner())
		{
			TArray<USceneComponent*> SceneComponents;
			Owner->GetComponents<USceneComponent>(SceneComponents);
			for (const USceneComponent* SceneComponent : SceneComponents)
			{
				if (SceneComponent && SceneComponent->DoesSocketExist(SourceSocketName))
				{
					return SceneComponent->GetSocketLocation(SourceSocketName);
				}
			}
		}
	}

	return GetComponentLocation();
}

bool UReactiveSocketComponent::ShouldStampAtLocation(const FVector& WorldLocation) const
{
	if (!bReactiveEnabled)
	{
		return false;
	}

	if (LastStampedWorldLocation.X == FLT_MAX)
	{
		return true;
	}

	return FVector::DistSquared2D(WorldLocation, LastStampedWorldLocation) >= FMath::Square(MinStampDistanceWorld);
}

void UReactiveSocketComponent::MarkStamped(const FVector& WorldLocation)
{
	LastStampedWorldLocation = WorldLocation;
}
