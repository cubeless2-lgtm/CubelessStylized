#include "GodotOceanWavesComponent.h"

#include "Engine/TextureRenderTarget2D.h"
#include "GodotOceanWavesShaders.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Components/MeshComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "RHICommandList.h"
#include "TextureResource.h"

UGodotOceanWavesComponent::UGodotOceanWavesComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
#if WITH_EDITOR
	bTickInEditor = true;
#endif
	EnsureDefaultCascade();
}

void UGodotOceanWavesComponent::OnRegister()
{
	Super::OnRegister();
	EnsureDefaultCascade();
	RebuildOutputs();
	ApplyToTargetMesh();
	if (bGeneratePreviewMaps)
	{
		ForceUpdate(1.0f / 30.0f);
	}
}

void UGodotOceanWavesComponent::BeginPlay()
{
	Super::BeginPlay();
	EnsureDefaultCascade();
	RebuildOutputs();
	ApplyToTargetMesh();
	if (bGeneratePreviewMaps)
	{
		ForceUpdate(1.0f / 30.0f);
	}
}

void UGodotOceanWavesComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	UpdateFollowTarget();

	if (!bGeneratePreviewMaps)
	{
		return;
	}

	TimeSeconds += DeltaTime;
	if (UpdatesPerSecond <= 0.0f)
	{
		ForceUpdate(DeltaTime);
		return;
	}

	UpdateAccumulator += DeltaTime;
	const float Interval = 1.0f / FMath::Max(UpdatesPerSecond, 0.001f);
	if (UpdateAccumulator >= Interval)
	{
		const float ConsumedDelta = UpdateAccumulator;
		UpdateAccumulator = 0.0f;
		ForceUpdate(ConsumedDelta);
	}
}

#if WITH_EDITOR
void UGodotOceanWavesComponent::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);
	MapSize = FMath::Clamp(FMath::RoundUpToPowerOfTwo(FMath::Max(MapSize, 16)), 16, 1024);
	EnsureDefaultCascade();
	RebuildOutputs();
	ApplyToTargetMesh();
}

#endif

void UGodotOceanWavesComponent::EnsureDefaultCascade()
{
	if (Cascades.IsEmpty() || bUseRecommendedPreviewPreset)
	{
		Cascades.Reset();

		FGodotOceanWaveCascadeParameters LargeWaves;
		LargeWaves.TileLength = FVector2D(5000.0, 5000.0);
		LargeWaves.SpectrumSeed = FIntPoint(17, 91);
		LargeWaves.DisplacementScale = 0.62f;
		LargeWaves.NormalScale = 0.58f;
		LargeWaves.WindSpeed = 18.0f;
		LargeWaves.FetchLengthKm = 550.0f;
		LargeWaves.Swell = 1.0f;
		LargeWaves.Spread = 0.12f;
		LargeWaves.Detail = 0.35f;
		LargeWaves.Whitecap = 0.68f;
		LargeWaves.FoamAmount = 1.10f;
		Cascades.Add(LargeWaves);

		FGodotOceanWaveCascadeParameters MediumWaves = LargeWaves;
		MediumWaves.TileLength = FVector2D(1250.0, 1250.0);
		MediumWaves.SpectrumSeed = FIntPoint(131, 47);
		MediumWaves.DisplacementScale = 0.16f;
		MediumWaves.NormalScale = 0.52f;
		MediumWaves.WindDirectionDegrees += 8.0f;
		MediumWaves.Swell = 0.42f;
		MediumWaves.Spread = 0.28f;
		MediumWaves.Detail = 0.50f;
		MediumWaves.Whitecap = 0.63f;
		MediumWaves.FoamAmount = 1.35f;
		Cascades.Add(MediumWaves);

		FGodotOceanWaveCascadeParameters SmallWaves = LargeWaves;
		SmallWaves.TileLength = FVector2D(320.0, 320.0);
		SmallWaves.SpectrumSeed = FIntPoint(7, 211);
		SmallWaves.DisplacementScale = 0.022f;
		SmallWaves.NormalScale = 0.34f;
		SmallWaves.WindDirectionDegrees -= 14.0f;
		SmallWaves.Swell = 0.10f;
		SmallWaves.Spread = 0.42f;
		SmallWaves.Detail = 0.70f;
		SmallWaves.Whitecap = 0.58f;
		SmallWaves.FoamAmount = 1.75f;
		Cascades.Add(SmallWaves);
	}
}

void UGodotOceanWavesComponent::CreateRenderTarget(TObjectPtr<UTextureRenderTarget2D>& RenderTarget, const TCHAR* Name)
{
	if (RenderTarget && RenderTarget->SizeX == MapSize && RenderTarget->SizeY == MapSize && RenderTarget->RenderTargetFormat == RTF_RGBA16f)
	{
		return;
	}

	RenderTarget = NewObject<UTextureRenderTarget2D>(this, Name, RF_Transient);
	RenderTarget->RenderTargetFormat = RTF_RGBA16f;
	RenderTarget->ClearColor = FLinearColor::Black;
	RenderTarget->bAutoGenerateMips = false;
	RenderTarget->bCanCreateUAV = true;
	RenderTarget->AddressX = TA_Wrap;
	RenderTarget->AddressY = TA_Wrap;
	RenderTarget->Filter = TF_Bilinear;
	RenderTarget->InitAutoFormat(MapSize, MapSize);
	RenderTarget->UpdateResourceImmediate(true);
}

void UGodotOceanWavesComponent::RebuildOutputs()
{
	MapSize = FMath::Clamp(FMath::RoundUpToPowerOfTwo(FMath::Max(MapSize, 16)), 16, 1024);
	CreateRenderTarget(DisplacementRenderTarget, TEXT("GOW_DisplacementRT"));
	CreateRenderTarget(NormalFoamRenderTarget, TEXT("GOW_NormalFoamRT"));
	ApplyToTargetMesh();
}

void UGodotOceanWavesComponent::ForceUpdate(float DeltaTime)
{
	EnsureDefaultCascade();
	RebuildOutputs();
	if (SimulationMode == EGodotOceanWavesSimulationMode::FFTExperimental)
	{
		DispatchFFTCompute(DeltaTime);
	}
	else
	{
		DispatchPreviewCompute(DeltaTime);
	}
}

void UGodotOceanWavesComponent::ApplyToMaterialInstance(UMaterialInstanceDynamic* MaterialInstance, FName InDisplacementParameterName, FName InNormalFoamParameterName) const
{
	if (!MaterialInstance)
	{
		return;
	}

	MaterialInstance->SetTextureParameterValue(InDisplacementParameterName, DisplacementRenderTarget);
	MaterialInstance->SetTextureParameterValue(InNormalFoamParameterName, NormalFoamRenderTarget);
}

void UGodotOceanWavesComponent::ApplyToTargetMesh()
{
	if (!bAutoApplyToMesh)
	{
		return;
	}

	UMeshComponent* MeshComponent = ResolveTargetMesh();
	if (!MeshComponent || TargetMaterialIndex < 0 || TargetMaterialIndex >= MeshComponent->GetNumMaterials())
	{
		return;
	}

	if (bDisableTargetMeshCollision)
	{
		MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		MeshComponent->SetGenerateOverlapEvents(false);
	}

	if (!AppliedMaterialInstance)
	{
		AppliedMaterialInstance = MeshComponent->CreateAndSetMaterialInstanceDynamic(TargetMaterialIndex);
	}
	else if (MeshComponent->GetMaterial(TargetMaterialIndex) != AppliedMaterialInstance)
	{
		MeshComponent->SetMaterial(TargetMaterialIndex, AppliedMaterialInstance);
	}

	ApplyToMaterialInstance(AppliedMaterialInstance, DisplacementParameterName, NormalFoamParameterName);
}

UMeshComponent* UGodotOceanWavesComponent::ResolveTargetMesh() const
{
	if (TargetMeshComponent)
	{
		return TargetMeshComponent;
	}

	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return nullptr;
	}

	TArray<UMeshComponent*> MeshComponents;
	Owner->GetComponents<UMeshComponent>(MeshComponents);
	return MeshComponents.IsEmpty() ? nullptr : MeshComponents[0];
}

void UGodotOceanWavesComponent::UpdateFollowTarget()
{
	if (!bFollowViewTarget)
	{
		return;
	}

	UWorld* World = GetWorld();
	AActor* Owner = GetOwner();
	if (!World || !Owner || !World->IsGameWorld())
	{
		return;
	}

	AActor* TargetActor = FollowTargetActor;
	if (!TargetActor)
	{
		if (APlayerController* PlayerController = World->GetFirstPlayerController())
		{
			TargetActor = PlayerController->GetViewTarget();
			if (!TargetActor)
			{
				TargetActor = PlayerController->GetPawn();
			}
		}
	}

	if (!TargetActor)
	{
		return;
	}

	const FVector TargetLocation = TargetActor->GetActorLocation();
	FVector NewLocation = Owner->GetActorLocation();
	NewLocation.X = TargetLocation.X;
	NewLocation.Y = TargetLocation.Y;
	NewLocation.Z = OceanHeight;

	if (FollowSnapSize > KINDA_SMALL_NUMBER)
	{
		NewLocation.X = FMath::GridSnap(NewLocation.X, FollowSnapSize);
		NewLocation.Y = FMath::GridSnap(NewLocation.Y, FollowSnapSize);
	}

	Owner->SetActorLocation(NewLocation);
}

void UGodotOceanWavesComponent::DispatchFFTCompute(float DeltaTime)
{
	if (!DisplacementRenderTarget || !NormalFoamRenderTarget || Cascades.IsEmpty())
	{
		return;
	}

	FTextureRenderTargetResource* DisplacementResource = DisplacementRenderTarget->GameThread_GetRenderTargetResource();
	FTextureRenderTargetResource* NormalFoamResource = NormalFoamRenderTarget->GameThread_GetRenderTargetResource();
	if (!DisplacementResource || !NormalFoamResource)
	{
		return;
	}

	const int32 OutputSize = MapSize;
	const uint32 NumStages = static_cast<uint32>(FMath::FloorLog2(OutputSize));
	const float CapturedTime = TimeSeconds;
	const int32 ActiveCascadeCount = FMath::Clamp(FMath::Min(Cascades.Num(), MaxActiveCascades), 1, 4);
	TArray<FGodotOceanWaveCascadeParameters> ActiveCascades;
	ActiveCascades.Reserve(ActiveCascadeCount);
	for (int32 CascadeIndex = 0; CascadeIndex < ActiveCascadeCount; ++CascadeIndex)
	{
		ActiveCascades.Add(Cascades[CascadeIndex]);
	}

	ENQUEUE_RENDER_COMMAND(DispatchGodotOceanWavesFFT)(
		[DisplacementResource, NormalFoamResource, ActiveCascades, OutputSize, NumStages, CapturedTime](FRHICommandListImmediate& RHICmdList)
		{
			FRDGBuilder GraphBuilder(RHICmdList);

			const uint32 ButterflyElementCount = NumStages * static_cast<uint32>(OutputSize);
			FRDGBufferRef ButterflyBuffer = GraphBuilder.CreateBuffer(
				FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector4f), ButterflyElementCount),
				TEXT("GOW.Butterfly"));

			FRDGTextureRef DisplacementTexture = GraphBuilder.RegisterExternalTexture(::CreateRenderTarget(DisplacementResource->GetRenderTargetTexture(), TEXT("GOW.Displacement")));
			FRDGTextureRef NormalFoamTexture = GraphBuilder.RegisterExternalTexture(::CreateRenderTarget(NormalFoamResource->GetRenderTargetTexture(), TEXT("GOW.NormalFoam")));

			{
				FGodotOceanWavesButterflyCS::FParameters* Parameters = GraphBuilder.AllocParameters<FGodotOceanWavesButterflyCS::FParameters>();
				Parameters->OutButterfly = GraphBuilder.CreateUAV(ButterflyBuffer);
				Parameters->MapSize = static_cast<uint32>(OutputSize);
				Parameters->NumStages = NumStages;

				TShaderMapRef<FGodotOceanWavesButterflyCS> ComputeShader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
				FComputeShaderUtils::AddPass(
					GraphBuilder,
					RDG_EVENT_NAME("GodotOceanWaves.Butterfly"),
					ComputeShader,
					Parameters,
					FIntVector(FMath::DivideAndRoundUp(OutputSize / 2, 64), NumStages, 1));
			}

			FRDGBufferSRVRef ButterflySRV = GraphBuilder.CreateSRV(ButterflyBuffer);
			const FRDGTextureDesc SpectrumDesc = FRDGTextureDesc::Create2D(
				FIntPoint(OutputSize, OutputSize),
				PF_A32B32G32R32F,
				FClearValueBinding::Black,
				TexCreate_ShaderResource | TexCreate_UAV);
			const uint32 FFTElementCount = static_cast<uint32>(OutputSize) * static_cast<uint32>(OutputSize) * 4u * 2u;
			constexpr float Gravity = 9.81f;
			constexpr float Depth = 20.0f;

			for (int32 CascadeIndex = 0; CascadeIndex < ActiveCascades.Num(); ++CascadeIndex)
			{
				const FGodotOceanWaveCascadeParameters Cascade = ActiveCascades[CascadeIndex];
				const float WindSpeed = FMath::Max(Cascade.WindSpeed, 0.0001f);
				const float FetchMeters = FMath::Max(Cascade.FetchLengthKm * 1000.0f, 0.0001f);
				const float Alpha = 0.076f * FMath::Pow((WindSpeed * WindSpeed) / (FetchMeters * Gravity), 0.22f);
				const float PeakFrequency = 22.0f * FMath::Pow((Gravity * Gravity) / (WindSpeed * FetchMeters), 1.0f / 3.0f);

				FRDGTextureRef SpectrumTexture = GraphBuilder.CreateTexture(SpectrumDesc, TEXT("GOW.Spectrum"));
				FRDGBufferRef FFTBuffer = GraphBuilder.CreateBuffer(
					FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector2f), FFTElementCount),
					TEXT("GOW.FFTBuffer"));
				FRDGBufferUAVRef FFTBufferUAV = GraphBuilder.CreateUAV(FFTBuffer);

				{
					FGodotOceanWavesSpectrumCS::FParameters* Parameters = GraphBuilder.AllocParameters<FGodotOceanWavesSpectrumCS::FParameters>();
					Parameters->OutSpectrum = GraphBuilder.CreateUAV(SpectrumTexture);
					Parameters->OutputSize = FUintVector2(OutputSize, OutputSize);
					Parameters->Seed = Cascade.SpectrumSeed;
					Parameters->TileLength = FVector2f(Cascade.TileLength);
					Parameters->Alpha = Alpha;
					Parameters->PeakFrequency = PeakFrequency;
					Parameters->WindSpeed = Cascade.WindSpeed;
					Parameters->WindDirectionRadians = FMath::DegreesToRadians(Cascade.WindDirectionDegrees);
					Parameters->Depth = Depth;
					Parameters->Swell = Cascade.Swell;
					Parameters->Detail = Cascade.Detail;
					Parameters->Spread = Cascade.Spread;

					TShaderMapRef<FGodotOceanWavesSpectrumCS> ComputeShader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
					FComputeShaderUtils::AddPass(
						GraphBuilder,
						RDG_EVENT_NAME("GodotOceanWaves.Spectrum"),
						ComputeShader,
						Parameters,
						FIntVector(FMath::DivideAndRoundUp(OutputSize, 16), FMath::DivideAndRoundUp(OutputSize, 16), 1));
				}

				{
					FGodotOceanWavesModulateCS::FParameters* Parameters = GraphBuilder.AllocParameters<FGodotOceanWavesModulateCS::FParameters>();
					Parameters->InSpectrum = SpectrumTexture;
					Parameters->OutFFTBuffer = FFTBufferUAV;
					Parameters->OutputSize = FUintVector2(OutputSize, OutputSize);
					Parameters->MapSize = static_cast<uint32>(OutputSize);
					Parameters->TileLength = FVector2f(Cascade.TileLength);
					Parameters->Depth = Depth;
					Parameters->TimeSeconds = CapturedTime;

					TShaderMapRef<FGodotOceanWavesModulateCS> ComputeShader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
					FComputeShaderUtils::AddPass(
						GraphBuilder,
						RDG_EVENT_NAME("GodotOceanWaves.Modulate"),
						ComputeShader,
						Parameters,
						FIntVector(FMath::DivideAndRoundUp(OutputSize, 16), FMath::DivideAndRoundUp(OutputSize, 16), 1));
				}

				auto AddFFTPass = [&GraphBuilder, OutputSize, NumStages, ButterflySRV, FFTBufferUAV]()
				{
					FGodotOceanWavesFFTCS::FParameters* Parameters = GraphBuilder.AllocParameters<FGodotOceanWavesFFTCS::FParameters>();
					Parameters->Butterfly = ButterflySRV;
					Parameters->FFTBuffer = FFTBufferUAV;
					Parameters->MapSize = static_cast<uint32>(OutputSize);
					Parameters->NumStages = NumStages;

					TShaderMapRef<FGodotOceanWavesFFTCS> ComputeShader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
					FComputeShaderUtils::AddPass(
						GraphBuilder,
						RDG_EVENT_NAME("GodotOceanWaves.FFT"),
						ComputeShader,
						Parameters,
						FIntVector(1, OutputSize, 4));
				};

				AddFFTPass();

				{
					FGodotOceanWavesTransposeCS::FParameters* Parameters = GraphBuilder.AllocParameters<FGodotOceanWavesTransposeCS::FParameters>();
					Parameters->FFTBuffer = FFTBufferUAV;
					Parameters->MapSize = static_cast<uint32>(OutputSize);

					TShaderMapRef<FGodotOceanWavesTransposeCS> ComputeShader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
					FComputeShaderUtils::AddPass(
						GraphBuilder,
						RDG_EVENT_NAME("GodotOceanWaves.Transpose"),
						ComputeShader,
						Parameters,
						FIntVector(FMath::DivideAndRoundUp(OutputSize, 32), FMath::DivideAndRoundUp(OutputSize, 32), 4));
				}

				AddFFTPass();

				{
					FGodotOceanWavesUnpackCS::FParameters* Parameters = GraphBuilder.AllocParameters<FGodotOceanWavesUnpackCS::FParameters>();
					Parameters->FFTBufferInput = GraphBuilder.CreateSRV(FFTBuffer);
					Parameters->OutDisplacement = GraphBuilder.CreateUAV(DisplacementTexture);
					Parameters->OutNormalFoam = GraphBuilder.CreateUAV(NormalFoamTexture);
					Parameters->OutputSize = FUintVector2(OutputSize, OutputSize);
					Parameters->MapSize = static_cast<uint32>(OutputSize);
					Parameters->DisplacementScale = Cascade.DisplacementScale * 100.0f;
					Parameters->NormalScale = Cascade.NormalScale;
					Parameters->Whitecap = Cascade.Whitecap;
					Parameters->FoamAmount = Cascade.FoamAmount;
					Parameters->bResetOutput = CascadeIndex == 0 ? 1u : 0u;

					TShaderMapRef<FGodotOceanWavesUnpackCS> ComputeShader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
					FComputeShaderUtils::AddPass(
						GraphBuilder,
						RDG_EVENT_NAME("GodotOceanWaves.Unpack"),
						ComputeShader,
						Parameters,
						FIntVector(FMath::DivideAndRoundUp(OutputSize, 16), FMath::DivideAndRoundUp(OutputSize, 16), 1));
				}
			}

			GraphBuilder.Execute();
		});
}

void UGodotOceanWavesComponent::DispatchPreviewCompute(float DeltaTime)
{
	if (!DisplacementRenderTarget || !NormalFoamRenderTarget || Cascades.IsEmpty())
	{
		return;
	}

	FTextureRenderTargetResource* DisplacementResource = DisplacementRenderTarget->GameThread_GetRenderTargetResource();
	FTextureRenderTargetResource* NormalFoamResource = NormalFoamRenderTarget->GameThread_GetRenderTargetResource();
	if (!DisplacementResource || !NormalFoamResource)
	{
		return;
	}

	const int32 OutputSize = MapSize;
	const float CapturedTime = TimeSeconds;
	const FVector OwnerLocation = GetOwner() ? GetOwner()->GetActorLocation() : FVector::ZeroVector;
	const FVector2f CapturedWorldOrigin(static_cast<float>(OwnerLocation.X), static_cast<float>(OwnerLocation.Y));
	const int32 ActiveCascadeCount = FMath::Clamp(FMath::Min(Cascades.Num(), MaxActiveCascades), 1, 4);
	TArray<FGodotOceanWaveCascadeParameters> ActiveCascades;
	ActiveCascades.Reserve(ActiveCascadeCount);
	for (int32 CascadeIndex = 0; CascadeIndex < ActiveCascadeCount; ++CascadeIndex)
	{
		ActiveCascades.Add(Cascades[CascadeIndex]);
	}

	ENQUEUE_RENDER_COMMAND(DispatchGodotOceanWavesPreview)(
		[DisplacementResource, NormalFoamResource, ActiveCascades, OutputSize, CapturedTime, DeltaTime, CapturedWorldOrigin](FRHICommandListImmediate& RHICmdList)
		{
			FRDGBuilder GraphBuilder(RHICmdList);

			FRDGTextureRef DisplacementTexture = GraphBuilder.RegisterExternalTexture(::CreateRenderTarget(DisplacementResource->GetRenderTargetTexture(), TEXT("GOW.Displacement")));
			FRDGTextureRef NormalFoamTexture = GraphBuilder.RegisterExternalTexture(::CreateRenderTarget(NormalFoamResource->GetRenderTargetTexture(), TEXT("GOW.NormalFoam")));

			for (int32 CascadeIndex = 0; CascadeIndex < ActiveCascades.Num(); ++CascadeIndex)
			{
				const FGodotOceanWaveCascadeParameters Cascade = ActiveCascades[CascadeIndex];
				FGodotOceanWavesPreviewCS::FParameters* Parameters = GraphBuilder.AllocParameters<FGodotOceanWavesPreviewCS::FParameters>();
				Parameters->OutDisplacement = GraphBuilder.CreateUAV(DisplacementTexture);
				Parameters->OutNormalFoam = GraphBuilder.CreateUAV(NormalFoamTexture);
				Parameters->OutputSize = FUintVector2(OutputSize, OutputSize);
				Parameters->TimeSeconds = CapturedTime;
				Parameters->DeltaTime = DeltaTime;
				Parameters->WorldOrigin = CapturedWorldOrigin;
				Parameters->TileLength = FVector2f(Cascade.TileLength);
				Parameters->DisplacementScale = Cascade.DisplacementScale;
				Parameters->NormalScale = Cascade.NormalScale;
				Parameters->WindSpeed = Cascade.WindSpeed;
				Parameters->WindDirectionRadians = FMath::DegreesToRadians(Cascade.WindDirectionDegrees);
				Parameters->FetchLengthKm = Cascade.FetchLengthKm;
				Parameters->Swell = Cascade.Swell;
				Parameters->Spread = Cascade.Spread;
				Parameters->Detail = Cascade.Detail;
				Parameters->Whitecap = Cascade.Whitecap;
				Parameters->FoamAmount = Cascade.FoamAmount;
				Parameters->bResetOutput = CascadeIndex == 0 ? 1u : 0u;

				TShaderMapRef<FGodotOceanWavesPreviewCS> ComputeShader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
				FComputeShaderUtils::AddPass(
					GraphBuilder,
					RDG_EVENT_NAME("GodotOceanWaves.Preview"),
					ComputeShader,
					Parameters,
					FIntVector(FMath::DivideAndRoundUp(OutputSize, 8), FMath::DivideAndRoundUp(OutputSize, 8), 1));
			}

			GraphBuilder.Execute();
		});
}
