#include "StylizedCubelessPCGBlueprintLibrary.h"

bool UStylizedCubelessPCGBlueprintLibrary::ApplyPCGGenerationSettings(
	UPCGComponent* PCGComponent,
	EPCGComponentGenerationTrigger GenerationTrigger,
	bool bRegenerateInEditor,
	bool bGenerateOnDropWhenTriggerOnDemand)
{
	if (!PCGComponent)
	{
		return false;
	}

	PCGComponent->GenerationTrigger = GenerationTrigger;
	PCGComponent->bGenerateOnDropWhenTriggerOnDemand =
		GenerationTrigger == EPCGComponentGenerationTrigger::GenerateOnDemand && bGenerateOnDropWhenTriggerOnDemand;
	PCGComponent->SetAutoActivate(true);
	PCGComponent->Activate(true);

#if WITH_EDITORONLY_DATA
	PCGComponent->bRegenerateInEditor = bRegenerateInEditor;
#endif

	return true;
}
