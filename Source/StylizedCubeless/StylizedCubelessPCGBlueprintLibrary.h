#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "PCGComponent.h"
#include "StylizedCubelessPCGBlueprintLibrary.generated.h"

UCLASS()
class STYLIZEDCUBELESS_API UStylizedCubelessPCGBlueprintLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "PCG|Cubeless")
	static bool ApplyPCGGenerationSettings(
		UPCGComponent* PCGComponent,
		EPCGComponentGenerationTrigger GenerationTrigger,
		bool bRegenerateInEditor,
		bool bGenerateOnDropWhenTriggerOnDemand);
};
