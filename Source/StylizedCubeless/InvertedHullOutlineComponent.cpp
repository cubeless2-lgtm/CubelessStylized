#include "InvertedHullOutlineComponent.h"

#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/Character.h"
#include "Materials/MaterialInstanceDynamic.h"

UInvertedHullOutlineComponent::UInvertedHullOutlineComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	bAutoActivate = true;
}

void UInvertedHullOutlineComponent::OnRegister()
{
	Super::OnRegister();
	RefreshOutline();
}

void UInvertedHullOutlineComponent::BeginPlay()
{
	Super::BeginPlay();
	RefreshOutline();
}

void UInvertedHullOutlineComponent::OnUnregister()
{
	DestroyOutlineMeshComponent();
	Super::OnUnregister();
}

#if WITH_EDITOR
void UInvertedHullOutlineComponent::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);
	RefreshOutline();
}
#endif

void UInvertedHullOutlineComponent::RefreshOutline()
{
	USkeletalMeshComponent* SourceMesh = ResolveSourceMeshComponent();
	if (!SourceMesh || !SourceMesh->GetSkeletalMeshAsset())
	{
		DestroyOutlineMeshComponent();
		return;
	}

	if (!OutlineMeshComponent)
	{
		CreateOutlineMeshComponent(SourceMesh);
	}

	ApplySourceMeshSettings(SourceMesh);
	ApplyOutlineMaterial();
	UpdateMaterialParameters();
	SetOutlineEnabled(bOutlineEnabled);
}

void UInvertedHullOutlineComponent::SetOutlineEnabled(bool bNewEnabled)
{
	bOutlineEnabled = bNewEnabled;
	if (OutlineMeshComponent)
	{
		OutlineMeshComponent->SetVisibility(bOutlineEnabled);
		OutlineMeshComponent->SetHiddenInGame(!bOutlineEnabled);
	}
}

void UInvertedHullOutlineComponent::SetOutlineThickness(float NewThickness)
{
	OutlineThickness = FMath::Max(0.0f, NewThickness);
	UpdateMaterialParameters();
}

void UInvertedHullOutlineComponent::SetOutlineColor(FLinearColor NewColor)
{
	OutlineColor = NewColor;
	UpdateMaterialParameters();
}

USkeletalMeshComponent* UInvertedHullOutlineComponent::ResolveSourceMeshComponent() const
{
	if (SourceMeshComponent)
	{
		return SourceMeshComponent;
	}

	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return nullptr;
	}

	if (const ACharacter* CharacterOwner = Cast<ACharacter>(Owner))
	{
		if (USkeletalMeshComponent* CharacterMesh = CharacterOwner->GetMesh())
		{
			return CharacterMesh;
		}
	}

	TArray<USkeletalMeshComponent*> MeshComponents;
	Owner->GetComponents<USkeletalMeshComponent>(MeshComponents);

	if (!SourceMeshComponentName.IsNone())
	{
		for (USkeletalMeshComponent* MeshComponent : MeshComponents)
		{
			if (MeshComponent && MeshComponent->GetFName() == SourceMeshComponentName)
			{
				return MeshComponent;
			}
		}
	}

	for (USkeletalMeshComponent* MeshComponent : MeshComponents)
	{
		if (MeshComponent && MeshComponent != OutlineMeshComponent)
		{
			return MeshComponent;
		}
	}

	return nullptr;
}

void UInvertedHullOutlineComponent::CreateOutlineMeshComponent(USkeletalMeshComponent* SourceMesh)
{
	AActor* Owner = GetOwner();
	if (!Owner || !SourceMesh)
	{
		return;
	}

	OutlineMeshComponent = NewObject<USkeletalMeshComponent>(Owner, TEXT("InvertedHullOutlineMesh"));
	OutlineMeshComponent->CreationMethod = EComponentCreationMethod::Instance;
	OutlineMeshComponent->SetupAttachment(SourceMesh);
	Owner->AddInstanceComponent(OutlineMeshComponent);
	OutlineMeshComponent->RegisterComponent();
}

void UInvertedHullOutlineComponent::ApplySourceMeshSettings(USkeletalMeshComponent* SourceMesh)
{
	if (!OutlineMeshComponent || !SourceMesh)
	{
		return;
	}

	OutlineMeshComponent->AttachToComponent(SourceMesh, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
	OutlineMeshComponent->SetRelativeTransform(FTransform::Identity);
	OutlineMeshComponent->SetSkeletalMesh(OutlineSkeletalMeshOverride ? OutlineSkeletalMeshOverride.Get() : SourceMesh->GetSkeletalMeshAsset(), false);
	OutlineMeshComponent->SetLeaderPoseComponent(SourceMesh, true);
	OutlineMeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	OutlineMeshComponent->SetGenerateOverlapEvents(false);
	OutlineMeshComponent->SetCastShadow(false);
	OutlineMeshComponent->SetReceivesDecals(false);
	OutlineMeshComponent->SetRenderCustomDepth(false);
	OutlineMeshComponent->SetBoundsScale(OutlineBoundsScale);
	OutlineMeshComponent->bUseBoundsFromLeaderPoseComponent = true;
	OutlineMeshComponent->bIgnoreLeaderPoseComponentLOD = false;
	OutlineMeshComponent->SetForcedLOD(SourceMesh->GetForcedLOD());
	OutlineMeshComponent->OverrideMinLOD(SourceMesh->ComputeMinLOD());
	OutlineMeshComponent->SetVisibility(bOutlineEnabled);
	OutlineMeshComponent->SetHiddenInGame(!bOutlineEnabled);
}

void UInvertedHullOutlineComponent::ApplyOutlineMaterial()
{
	if (!OutlineMeshComponent || !OutlineMaterial)
	{
		return;
	}

	const int32 MaterialCount = FMath::Max(OutlineMeshComponent->GetNumMaterials(), 1);
	for (int32 Index = 0; Index < MaterialCount; ++Index)
	{
		UMaterialInstanceDynamic* DynamicMaterial = Cast<UMaterialInstanceDynamic>(OutlineMeshComponent->GetMaterial(Index));
		if (!DynamicMaterial || DynamicMaterial->Parent != OutlineMaterial)
		{
			DynamicMaterial = UMaterialInstanceDynamic::Create(OutlineMaterial, this);
			OutlineMeshComponent->SetMaterial(Index, DynamicMaterial);
		}
	}
}

void UInvertedHullOutlineComponent::UpdateMaterialParameters()
{
	if (!OutlineMeshComponent)
	{
		return;
	}

	const int32 MaterialCount = OutlineMeshComponent->GetNumMaterials();
	for (int32 Index = 0; Index < MaterialCount; ++Index)
	{
		if (UMaterialInstanceDynamic* DynamicMaterial = Cast<UMaterialInstanceDynamic>(OutlineMeshComponent->GetMaterial(Index)))
		{
			DynamicMaterial->SetScalarParameterValue(ThicknessParameterName, OutlineThickness);
			DynamicMaterial->SetVectorParameterValue(ColorParameterName, OutlineColor);
		}
	}
}

void UInvertedHullOutlineComponent::DestroyOutlineMeshComponent()
{
	if (!OutlineMeshComponent)
	{
		return;
	}

	OutlineMeshComponent->DestroyComponent();
	OutlineMeshComponent = nullptr;
}
