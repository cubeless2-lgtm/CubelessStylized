#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "PlayerStatsComponentBase.generated.h"

UCLASS(Blueprintable, ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class STYLIZEDCUBELESS_API UPlayerStatsComponentBase : public UActorComponent
{
	GENERATED_BODY()

public:
	virtual void OnRegister() override;
	virtual void BeginPlay() override;

private:
	void InitializeCharacterReference();
};
