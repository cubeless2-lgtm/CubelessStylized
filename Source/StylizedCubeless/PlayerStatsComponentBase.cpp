#include "PlayerStatsComponentBase.h"

#include "Kismet/GameplayStatics.h"
#include "UObject/UnrealType.h"

void UPlayerStatsComponentBase::OnRegister()
{
	Super::OnRegister();
	InitializeCharacterReference();
}

void UPlayerStatsComponentBase::BeginPlay()
{
	InitializeCharacterReference();
	Super::BeginPlay();
}

void UPlayerStatsComponentBase::InitializeCharacterReference()
{
	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	static const FName CharacterPropertyName(TEXT("BP Third Person Character"));
	FObjectPropertyBase* CharacterProperty = FindFProperty<FObjectPropertyBase>(GetClass(), CharacterPropertyName);
	if (!CharacterProperty)
	{
		for (TFieldIterator<FObjectPropertyBase> It(GetClass()); It; ++It)
		{
			FObjectPropertyBase* Candidate = *It;
			if (Candidate->GetName() == CharacterPropertyName.ToString() ||
				Candidate->GetAuthoredName() == CharacterPropertyName.ToString())
			{
				CharacterProperty = Candidate;
				break;
			}
		}
	}

	if (!CharacterProperty || CharacterProperty->GetObjectPropertyValue_InContainer(this))
	{
		return;
	}

	if (Owner->IsA(CharacterProperty->PropertyClass))
	{
		CharacterProperty->SetObjectPropertyValue_InContainer(this, Owner);
		return;
	}

	APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
	if (PlayerPawn && PlayerPawn->IsA(CharacterProperty->PropertyClass))
	{
		CharacterProperty->SetObjectPropertyValue_InContainer(this, PlayerPawn);
	}
}
