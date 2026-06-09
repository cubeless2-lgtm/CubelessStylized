#include "OptimizationPreviewTools.h"

#include "CanvasItem.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Camera/CameraTypes.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/LineBatchComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SkinnedMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Containers/Ticker.h"
#include "CoreGlobals.h"
#include "DynamicRHI.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/EngineTypes.h"
#include "Engine/GameViewportClient.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "GameFramework/ActorPrimitiveColorHandler.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformProcess.h"
#include "InputCoreTypes.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "FoliageType_InstancedStaticMesh.h"
#include "InstancedFoliageActor.h"
#include "LandscapeComponent.h"
#include "LandscapeGrassType.h"
#include "LandscapeProxy.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionLandscapeGrassOutput.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Misc/DateTime.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "PhysicsEngine/BodySetup.h"
#include "ProfilingDebugging/CountersTrace.h"
#include "ProfilingDebugging/TraceAuxiliary.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "RenderingThread.h"
#include "Serialization/ArchiveCountMem.h"
#include "Serialization/MemoryReader.h"
#include "StaticMeshResources.h"
#include "Styling/CoreStyle.h"
#include "Rendering/DrawElements.h"
#include "TraceServices/AnalysisService.h"
#include "TraceServices/Containers/Timelines.h"
#include "TraceServices/ITraceServicesModule.h"
#include "TraceServices/Model/AnalysisSession.h"
#include "TraceServices/Model/Counters.h"
#include "TraceServices/Model/Frames.h"
#include "TraceServices/Model/TimingProfiler.h"
#include "UObject/ObjectKey.h"
#include "UObject/Package.h"
#include "UObject/UObjectGlobals.h"
#include "UObject/WeakObjectPtrTemplates.h"
#include "UnrealClient.h"
#include "ViewportClient.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SViewport.h"
#include "Widgets/Text/STextBlock.h"

#include "CborReader.h"

#if WITH_EDITOR
#include "Editor.h"
#include "Editor/EditorEngine.h"
#include "EditorViewportClient.h"
#endif

DEFINE_LOG_CATEGORY_STATIC(LogOptimizationPreviewTools, Log, All);
TRACE_DECLARE_FLOAT_COUNTER(MaterialGPUUnitGPU, TEXT("MaterialGPU/UnitGPU"));

#define LOCTEXT_NAMESPACE "OptimizationPreviewTools"

namespace OptimizationPreviewTools
{
static const FString StatName = TEXT("Material");
static const FString StatAliasName = TEXT("Mat");
static const FString MaterialModeStatName = TEXT("MatMode");
static const FString ObjectStatName = TEXT("Obj");
static const FString ProfilingStatName = TEXT("Profiling");
static const FName EngineStatName(TEXT("STAT_Material"));
static const FName EngineStatAliasName(TEXT("STAT_Mat"));
static const FName MaterialModeEngineStatName(TEXT("STAT_MatMode"));
static const FName ObjectEngineStatName(TEXT("STAT_Obj"));
static const FName ProfilingEngineStatName(TEXT("STAT_Profiling"));
static const FName EngineStatCategory(TEXT("STATCAT_Engine"));
static const FName ActorColorationHandlerName(TEXT("OptimizationPreviewTools"));
static const FName MaterialReplayCameraTag(TEXT("OptimizationPreviewToolsReplayCamera"));
static const TCHAR* DefaultMaterialGPUTraceChannels = TEXT("gpu,frame,counters");

struct FProfilingCommandButtonSpec
{
	const TCHAR* Label;
	const TCHAR* Command;
};

static const FProfilingCommandButtonSpec GProfilingCommandButtons[] =
{
	{ TEXT("GPU START"), TEXT("stat mat start") },
	{ TEXT("GPU REPLAY"), TEXT("stat mat replay") },
	{ TEXT("COLOR ON"), TEXT("stat matmode") },
	{ TEXT("OBJ SNAP"), TEXT("stat obj") }
};

static constexpr float ProfilingCommandButtonHeight = 41.0f;
static constexpr float ProfilingCommandButtonGap = 7.0f;
static constexpr float ProfilingCommandAreaPadding = 10.0f;

static TAutoConsoleVariable<FString> CVarTraceChannels(
	TEXT("materialgpu.TraceChannels"),
	TEXT(""),
	TEXT("Override Material GPU Preview Insights trace channels. Empty uses OptimizationPreviewTools.ini MaterialGPUPreview.TraceChannels."),
	ECVF_Default);

static TAutoConsoleVariable<int32> CVarTopN(
	TEXT("materialgpu.TopN"),
	10,
	TEXT("Number of Material GPU Preview rows to show."),
	ECVF_Default);

static TAutoConsoleVariable<int32> CVarDebug(
	TEXT("materialgpu.Debug"),
	0,
	TEXT("Show the last Insights material capture using Actor Coloration when r.ForceDebugViewModes=1, otherwise collision-shaped debug overlays."),
	ECVF_Default);

static TAutoConsoleVariable<int32> CVarMaterialDebugMode(
	TEXT("materialgpu.DebugMode"),
	1,
	TEXT("Use Material GPU Preview debug colors. 0 keeps the original scene colors while the stat/replay UI remains visible."),
	ECVF_Default);

static TAutoConsoleVariable<int32> CVarDebugMaterialOverrideFallback(
	TEXT("materialgpu.DebugMaterialOverrideFallback"),
	1,
	TEXT("Temporarily override non-opaque target materials with solid debug materials when Actor Coloration cannot reliably color them. Restored when debug mode is disabled."),
	ECVF_Default);

static TAutoConsoleVariable<int32> CVarDebugAlpha(
	TEXT("materialgpu.DebugAlpha"),
	72,
	TEXT("Alpha used for Insights material debug overlays."),
	ECVF_Default);

static TAutoConsoleVariable<int32> CVarMaxDebugComponents(
	TEXT("materialgpu.MaxDebugComponents"),
	0,
	TEXT("Maximum number of components drawn for the last Insights material capture debug overlay. 0 draws every matched primitive."),
	ECVF_Default);

static TAutoConsoleVariable<int32> CVarMaxDebugShapesPerComponent(
	TEXT("materialgpu.MaxDebugShapesPerComponent"),
	96,
	TEXT("Maximum number of collision shapes or instances drawn per component before falling back to bounds."),
	ECVF_Default);

static TAutoConsoleVariable<float> CVarDebugLineThickness(
	TEXT("materialgpu.DebugLineThickness"),
	2.5f,
	TEXT("Line thickness for wire collision shapes in the Material GPU Preview debug overlay."),
	ECVF_Default);

static TAutoConsoleVariable<float> CVarDebugBoundsPadding(
	TEXT("materialgpu.DebugBoundsPadding"),
	1.015f,
	TEXT("Scale applied to debug collision shapes and fallback bounds to reduce surface fighting."),
	ECVF_Default);

static TAutoConsoleVariable<int32> CVarObjectDebug(
	TEXT("objmem.Debug"),
	0,
	TEXT("Show the last Object Memory Snapshot using Actor Coloration when available, otherwise collision-shaped debug overlays."),
	ECVF_Default);

static TAutoConsoleVariable<int32> CVarObjectTopN(
	TEXT("objmem.TopN"),
	10,
	TEXT("Number of Object Memory Snapshot rows to show."),
	ECVF_Default);

static TAutoConsoleVariable<int32> CVarObjectDebugAlpha(
	TEXT("objmem.DebugAlpha"),
	72,
	TEXT("Alpha used for Object Memory Snapshot debug overlays."),
	ECVF_Default);

static TAutoConsoleVariable<int32> CVarObjectMaxDebugComponents(
	TEXT("objmem.MaxDebugComponents"),
	0,
	TEXT("Maximum number of components drawn for Object Memory Snapshot debug overlay. 0 draws every matched primitive."),
	ECVF_Default);

static const TCHAR* MaterialGPUPreviewConfigName = TEXT("OptimizationPreviewTools");
static const TCHAR* MaterialGPUPreviewConfigSection = TEXT("MaterialGPUPreview");
static const TCHAR* ObjectMemorySnapshotConfigSection = TEXT("ObjectMemorySnapshot");
static constexpr float DefaultDebugGreenMs = 0.5f;
static constexpr float DefaultDebugRedMs = 1.5f;
static constexpr float DefaultDebugPinkMs = 3.0f;
static constexpr float DefaultDebugWhiteMs = 6.0f;
static constexpr float DefaultObjectDebugGreenMaxMB = 5.0f;
static constexpr float DefaultObjectDebugWhiteMB = 10.0f;

struct FMaterialSourceUsage
{
	FString Label;
	int32 InstanceCount = 0;
	int32 ComponentCount = 0;
};

struct FMaterialAccumulator
{
	TWeakObjectPtr<UMaterialInterface> Material;
	FString DisplayName;
	FString PathName;
	EBlendMode BlendMode = BLEND_Opaque;
	float MaxGpuMs = 0.0f;
	float AvgGpuMs = 0.0f;
	int32 TraceDrawEvents = 0;
	int32 ComponentCount = 0;
	int64 Triangles = 0;
	TArray<FMaterialSourceUsage> SourceUsages;
	TArray<TWeakObjectPtr<UPrimitiveComponent>> Components;
};

struct FComponentSourceInfo
{
	FString Label;
	int32 InstanceCount = 0;
};

struct FDebugOverlayEntry
{
	enum class EShapeType : uint8
	{
		Box,
		Sphere,
		Capsule,
		Convex,
		FallbackBounds
	};

	struct FShape
	{
		EShapeType Type = EShapeType::FallbackBounds;
		FVector Origin = FVector::ZeroVector;
		FVector Extent = FVector::ZeroVector;
		FQuat Rotation = FQuat::Identity;
		float Radius = 0.0f;
		float HalfHeight = 0.0f;
		TArray<FVector> Vertices;
		TArray<int32> Indices;

		bool Matches(const FShape& Other) const
		{
			return Type == Other.Type
				&& Origin.Equals(Other.Origin, 1.0)
				&& Extent.Equals(Other.Extent, 1.0)
				&& Rotation.Equals(Other.Rotation, 0.005)
				&& FMath::IsNearlyEqual(Radius, Other.Radius, 1.0f)
				&& FMath::IsNearlyEqual(HalfHeight, Other.HalfHeight, 1.0f)
				&& Vertices.Num() == Other.Vertices.Num()
				&& Indices.Num() == Other.Indices.Num();
		}
	};

	TWeakObjectPtr<UPrimitiveComponent> Component;
	FColor Color = FColor::Transparent;
	FVector Origin = FVector::ZeroVector;
	FVector Extent = FVector::ZeroVector;
	FQuat Rotation = FQuat::Identity;
	float MaxGpuMs = 0.0f;
	int32 Severity = 0;
	uint32 BatchId = ULineBatchComponent::INVALID_ID;
	bool bUsedCollision = false;
	TArray<FShape> Shapes;

	bool Matches(const FDebugOverlayEntry& Other) const
	{
		if (Component.Get() != Other.Component.Get()
			|| Severity != Other.Severity
			|| Color != Other.Color
			|| !Origin.Equals(Other.Origin, 1.0)
			|| !Extent.Equals(Other.Extent, 1.0)
			|| !Rotation.Equals(Other.Rotation, 0.005)
			|| bUsedCollision != Other.bUsedCollision
			|| Shapes.Num() != Other.Shapes.Num())
		{
			return false;
		}

		for (int32 ShapeIndex = 0; ShapeIndex < Shapes.Num(); ++ShapeIndex)
		{
			if (!Shapes[ShapeIndex].Matches(Other.Shapes[ShapeIndex]))
			{
				return false;
			}
		}

		return true;
	}
};

struct FTraceMaterialAggregate
{
	FString MaterialName;
	FString EventName;
	double TotalGpuMs = 0.0;
	double PeakFrameGpuMs = 0.0;
	double AverageFrameGpuMs = 0.0;
	int32 DrawEvents = 0;
	TMap<uint32, double> GpuMsByFrame;
};

struct FMaterialGpuReplayFrameSample
{
	uint32 TraceFrameIndex = 0;
	double TimeSeconds = 0.0;
	double EndTimeSeconds = 0.0;
	float TotalFrameGpuMs = 0.0f;
	bool bHasTotalFrameGpuMs = false;
	TMap<FString, float> MaterialGpuMsByKey;
	TMap<FString, int32> MaterialDrawEventsByKey;
};

struct FFrameGpuInterval
{
	double StartTimeSeconds = 0.0;
	double EndTimeSeconds = 0.0;
};

struct FMaterialReplayCameraSample
{
	double TimeSeconds = 0.0;
	FTransform Transform = FTransform::Identity;
	FMinimalViewInfo ViewInfo;
};

struct FMaterialReplayCharacterSample
{
	double TimeSeconds = 0.0;
	TWeakObjectPtr<ACharacter> Character;
	FTransform Transform = FTransform::Identity;
	FVector Velocity = FVector::ZeroVector;
	FRotator ControlRotation = FRotator::ZeroRotator;
	TEnumAsByte<EMovementMode> MovementMode = MOVE_None;
	uint8 CustomMovementMode = 0;
	TWeakObjectPtr<UAnimMontage> ActiveMontage;
	float MontagePosition = 0.0f;
	float MontagePlayRate = 1.0f;
	bool bHasMovementMode = false;
	bool bHasMontage = false;
	bool bHasControlRotation = false;
};

struct FMaterialReplayAnimationState
{
	TWeakObjectPtr<USkeletalMeshComponent> MeshComponent;
	bool bPauseAnims = false;
	float GlobalAnimRateScale = 1.0f;
};

struct FMaterialDebugMaterialOverrideState
{
	TWeakObjectPtr<UPrimitiveComponent> Component;
	TArray<TWeakObjectPtr<UMaterialInterface>> OriginalMaterials;
	TArray<int32> OverriddenSlots;
	TWeakObjectPtr<UPackage> Package;
	bool bPackageWasDirty = false;
};

struct FMaterialReplayRowsCacheEntry
{
	TArray<FMaterialAccumulator> Rows;
	int32 DebugComponentCount = 0;
};

struct FMaterialReplayUnitGpuSample
{
	double TimeSeconds = 0.0;
	float GpuMs = 0.0f;
	bool bFromStatUnitData = false;
};

struct FObjectMemorySnapshotRow
{
	TWeakObjectPtr<UObject> Object;
	FString DisplayName;
	FString PathName;
	FString ClassName;
	uint64 ObjectBytes = 0;
	uint64 ResourceBytes = 0;
	int32 UserCount = 0;
	TArray<TWeakObjectPtr<UPrimitiveComponent>> Components;

	uint64 GetTotalBytes() const
	{
		return ObjectBytes + ResourceBytes;
	}

	float GetTotalMB() const
	{
		return static_cast<float>(GetTotalBytes()) / (1024.0f * 1024.0f);
	}
};

struct FInputScreenRect
{
	FVector2D Min = FVector2D::ZeroVector;
	FVector2D Max = FVector2D::ZeroVector;
	bool bValid = false;

	void Reset()
	{
		Min = FVector2D::ZeroVector;
		Max = FVector2D::ZeroVector;
		bValid = false;
	}

	void Set(const FVector2D& InMin, const FVector2D& InMax)
	{
		Min = FVector2D(FMath::Min(InMin.X, InMax.X), FMath::Min(InMin.Y, InMax.Y));
		Max = FVector2D(FMath::Max(InMin.X, InMax.X), FMath::Max(InMin.Y, InMax.Y));
		bValid = Max.X > Min.X && Max.Y > Min.Y;
	}

	bool Contains(const FVector2D& Position) const
	{
		return bValid
			&& Position.X >= Min.X
			&& Position.X <= Max.X
			&& Position.Y >= Min.Y
			&& Position.Y <= Max.Y;
	}

	float GetNormalizedX(const FVector2D& Position) const
	{
		return bValid
			? FMath::Clamp(static_cast<float>((Position.X - Min.X) / FMath::Max(Max.X - Min.X, 1.0)), 0.0f, 1.0f)
			: 0.0f;
	}
};

static bool SetInputScreenRectFromWidget(const TSharedPtr<SWidget>& Widget, float InflateX, float InflateY, FInputScreenRect& OutRect)
{
	if (!Widget.IsValid())
	{
		return false;
	}

	const FGeometry& Geometry = Widget->GetCachedGeometry();
	const FVector2D LocalSize = Geometry.GetLocalSize();
	if (LocalSize.X <= 1.0f || LocalSize.Y <= 1.0f)
	{
		return false;
	}

	const FVector2D Min = Geometry.LocalToAbsolute(FVector2D::ZeroVector) - FVector2D(InflateX, InflateY);
	const FVector2D Max = Geometry.LocalToAbsolute(LocalSize) + FVector2D(InflateX, InflateY);
	OutRect.Set(Min, Max);
	return OutRect.bValid;
}

static TArray<FMaterialAccumulator> GCachedRows;
static TArray<FMaterialAccumulator> GCachedRowsAll;
static TArray<FMaterialAccumulator> GCachedDebugRows;
static TArray<FMaterialAccumulator> GMaterialReplayCurrentRows;
static TArray<FMaterialAccumulator> GMaterialReplayCurrentRowsAll;
static TArray<FMaterialAccumulator> GMaterialReplayDebugRows;
static TArray<FMaterialAccumulator> GMaterialReplaySceneRows;
static TArray<FMaterialGpuReplayFrameSample> GMaterialReplaySamples;
static TArray<FMaterialReplayCameraSample> GMaterialReplayCameraSamples;
static TArray<FMaterialReplayCharacterSample> GMaterialReplayCharacterSamples;
static TMap<FObjectKey, FMaterialReplayAnimationState> GMaterialReplayAnimationStates;
static TArray<FMaterialReplayUnitGpuSample> GMaterialReplayUnitGpuSamples;
static TArray<float> GMaterialReplayFrameGpuMs;
static float GMaterialReplayFrameGpuMsMax = 0.0f;
static TArray<int32> GMaterialReplayPeakIndices;
static bool GMaterialReplayPeakIndicesDirty = true;
static TMap<int32, FMaterialReplayRowsCacheEntry> GMaterialReplayRowsCache;
static TArray<int32> GMaterialReplayRowsCacheLru;
static TArray<FObjectMemorySnapshotRow> GCachedObjectRows;
static TArray<FObjectMemorySnapshotRow> GCachedObjectDebugRows;
static TArray<FDebugOverlayEntry> GCachedDebugEntries;
static TMap<FObjectKey, FLinearColor> GActorColorationColors;
static TMap<FObjectKey, FMaterialDebugMaterialOverrideState> GMaterialDebugMaterialOverrides;
static TMap<FString, int32> GMaterialReplaySceneLookup;
static double GCaptureStartTime = -1.0;
static double GCaptureEndTime = -1.0;
static TWeakObjectPtr<UWorld> GCachedDebugWorld;
static TWeakObjectPtr<UWorld> GActorColorationWorld;
static TWeakObjectPtr<UGameViewportClient> GActorColorationGameViewport;
static bool GCaptureActive = false;
static bool GCaptureFrozen = false;
static bool GTraceStartedByCapture = false;
static bool GMaterialCaptureEndGuardActive = false;
static double GMaterialCaptureEndGuardReleaseSeconds = 0.0;
static constexpr double MaterialCaptureEndGuardDebounceSeconds = 0.35;
static bool GActorColorationHandlerRegistered = false;
static bool GActorColorationActive = false;
static bool GMaterialReplayActive = false;
static bool GMaterialReplayPlaying = false;
static bool GMaterialReplayScrubbing = false;
static bool GHasPreviousGameViewMode = false;
static int32 GPreviousGameViewMode = VMI_Lit;
static FString GTraceFilePath;
static bool GHasPreviousShowMaterialDrawEvents = false;
static int32 GPreviousShowMaterialDrawEvents = 0;
static bool GHasPreviousEmitDrawEvents = false;
static bool GPreviousEmitDrawEvents = false;
static FString GLastAnalysisMessage;
static uint64 GLastTraceFrameCount = 0;
static int32 GLastDebugMaterialCount = 0;
static int32 GLastDebugComponentCount = 0;
static int32 GLastObjectSnapshotSourceCount = 0;
static int32 GLastObjectDebugComponentCount = 0;
static double GLastObjectSnapshotTime = -1.0;
static FString GLastObjectSnapshotMessage;
static FString GLastObjectSnapshotFilePath;
static FString GOptimizationPreviewToolsIni;
static bool GOptimizationPreviewToolsIniLoaded = false;
static TArray<IConsoleCommand*> GConsoleAutoCompleteCommands;
static TSharedPtr<SWidget> GProfilingSlateOverlayWidget;
static TSharedPtr<IInputProcessor> GProfilingCommandInputProcessor;
static TArray<TSharedPtr<SWidget>> GProfilingSlateButtonWidgets;
static TWeakObjectPtr<UGameViewportClient> GProfilingSlateOverlayViewport;
static TWeakObjectPtr<UGameViewportClient> GProfilingInputOverrideViewport;
static TSharedPtr<SWidget> GMaterialReplayOverlayWidget;
static TSharedPtr<SWidget> GMaterialReplayPlayButtonWidget;
static TSharedPtr<SWidget> GMaterialReplayPreviousPeakButtonWidget;
static TSharedPtr<SWidget> GMaterialReplayMaxPeakButtonWidget;
static TSharedPtr<SWidget> GMaterialReplayNextPeakButtonWidget;
static TSharedPtr<SSlider> GMaterialReplaySliderWidget;
static TWeakObjectPtr<UGameViewportClient> GMaterialReplayOverlayViewport;
static TWeakObjectPtr<ACameraActor> GMaterialReplayCameraActor;
static TWeakObjectPtr<UCameraComponent> GMaterialReplaySourceCameraComponent;
static TWeakObjectPtr<APlayerController> GMaterialReplayViewPlayerController;
static TWeakObjectPtr<AActor> GMaterialReplayPreviousViewTarget;
static TWeakObjectPtr<APlayerController> GMaterialReplayInputPlayerController;
static TWeakObjectPtr<UWorld> GMaterialReplayCameraCaptureWorld;
static FOverrideInputKeyHandler GPreviousProfilingInputOverride;
static FDelegateHandle GProfilingInputOverrideHandle;
static FTSTicker::FDelegateHandle GMaterialReplayTickerHandle;
static FTSTicker::FDelegateHandle GMaterialReplayCameraCaptureTickerHandle;
static bool GHadPreviousProfilingInputOverride = false;
static bool GMaterialReplayInputLocked = false;
static bool GMaterialReplayPreviousLookInputIgnored = false;
static bool GMaterialReplayPreviousMoveInputIgnored = false;
static double GMaterialReplayCurrentTimeSeconds = 0.0;
static double GMaterialReplayLastTickSeconds = -1.0;
static int32 GMaterialReplayCurrentSampleIndex = INDEX_NONE;
static float GProfilingSlateOverlayLeft = 260.0f;
static float GProfilingSlateOverlayTop = 300.0f;
static float GProfilingSlateOverlayWidth = 760.0f;
static float GProfilingSlateOverlayHeight = 36.0f;
static float GProfilingSlateViewportWidth = 1920.0f;
static float GProfilingSlateViewportHeight = 1080.0f;
static float GProfilingSlateButtonHeight = ProfilingCommandButtonHeight;
static float GProfilingSlateButtonGap = ProfilingCommandButtonGap;
static float GProfilingCommandHitLeft = 260.0f;
static float GProfilingCommandHitTop = 300.0f;
static float GProfilingCommandHitWidth = 760.0f;
static float GProfilingCommandHitHeight = 36.0f;
static float GProfilingCommandHitButtonGap = ProfilingCommandButtonGap;
static bool GProfilingSlateDrawPanel = false;
static bool GLastProfilingSlateDrawPanel = false;
static float GLastProfilingSlateOverlayLeft = -1.0f;
static float GLastProfilingSlateOverlayTop = -1.0f;
static float GLastProfilingSlateOverlayWidth = -1.0f;
static float GLastProfilingSlateOverlayHeight = -1.0f;
static FInputScreenRect GMaterialReplayPlayButtonRect;
static FInputScreenRect GMaterialReplayPreviousPeakButtonRect;
static FInputScreenRect GMaterialReplayMaxPeakButtonRect;
static FInputScreenRect GMaterialReplayNextPeakButtonRect;
static FInputScreenRect GMaterialReplaySliderRect;
static bool GMaterialReplayDraggingSlider = false;
static uint32 GMaterialReplayDraggingPointerIndex = 0;

static double CalculateMergedGpuIntervalDurationMs(TArray<FFrameGpuInterval>& Intervals)
{
	Intervals.RemoveAll([](const FFrameGpuInterval& Interval)
	{
		return !FMath::IsFinite(Interval.StartTimeSeconds)
			|| !FMath::IsFinite(Interval.EndTimeSeconds)
			|| Interval.EndTimeSeconds <= Interval.StartTimeSeconds;
	});

	if (Intervals.Num() == 0)
	{
		return 0.0;
	}

	Intervals.Sort([](const FFrameGpuInterval& A, const FFrameGpuInterval& B)
	{
		if (A.StartTimeSeconds == B.StartTimeSeconds)
		{
			return A.EndTimeSeconds < B.EndTimeSeconds;
		}

		return A.StartTimeSeconds < B.StartTimeSeconds;
	});

	double TotalSeconds = 0.0;
	double CurrentStart = Intervals[0].StartTimeSeconds;
	double CurrentEnd = Intervals[0].EndTimeSeconds;
	for (int32 Index = 1; Index < Intervals.Num(); ++Index)
	{
		const FFrameGpuInterval& Interval = Intervals[Index];
		if (Interval.StartTimeSeconds <= CurrentEnd)
		{
			CurrentEnd = FMath::Max(CurrentEnd, Interval.EndTimeSeconds);
			continue;
		}

		TotalSeconds += CurrentEnd - CurrentStart;
		CurrentStart = Interval.StartTimeSeconds;
		CurrentEnd = Interval.EndTimeSeconds;
	}

	TotalSeconds += CurrentEnd - CurrentStart;
	return TotalSeconds * 1000.0;
}

static float ReadCurrentStatUnitGpuMs(UWorld* World, bool& bOutFromStatUnitData)
{
	bOutFromStatUnitData = false;
	if (World)
	{
		if (UGameViewportClient* GameViewportClient = World->GetGameViewport())
		{
			if (FStatUnitData* StatUnitData = GameViewportClient->GetStatUnitData())
			{
				if (StatUnitData->GPUFrameTime[0] > 0.0f)
				{
					bOutFromStatUnitData = true;
					return StatUnitData->GPUFrameTime[0];
				}

				if (StatUnitData->RawGPUFrameTime[0] > 0.0f)
				{
					bOutFromStatUnitData = true;
					return StatUnitData->RawGPUFrameTime[0];
				}
			}
		}
	}

	return FPlatformTime::ToMilliseconds(RHIGetGPUFrameCycles(0));
}

#if WITH_EDITOR
static FDelegateHandle GEndPIEHandle;
static TMap<FEditorViewportClient*, EViewModeIndex> GPreviousEditorViewModes;
#endif

static FString BuildTraceFilePath()
{
	const FString TraceDir = FPaths::ConvertRelativePathToFull(FPaths::Combine(
		FPaths::ProjectSavedDir(),
		TEXT("Profiling"),
		TEXT("OptimizationPreviewTools"),
		TEXT("MaterialGPUPreview")));
	IFileManager::Get().MakeDirectory(*TraceDir, true);
	return FPaths::Combine(
		TraceDir,
		FString::Printf(TEXT("MaterialGPUPreview_%s.utrace"), *FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S"))));
}

static FString BuildObjectSnapshotFilePath()
{
	const FString SnapshotDir = FPaths::ConvertRelativePathToFull(FPaths::Combine(
		FPaths::ProjectSavedDir(),
		TEXT("Profiling"),
		TEXT("OptimizationPreviewTools"),
		TEXT("ObjectMemorySnapshot")));
	IFileManager::Get().MakeDirectory(*SnapshotDir, true);
	return FPaths::Combine(
		SnapshotDir,
		FString::Printf(TEXT("ObjectMemorySnapshot_%s.csv"), *FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S"))));
}

static void RemoveMaterialReplayOverlay();
static void StopMaterialReplayTicker();
static void StopMaterialReplayCameraCaptureTicker();
static void StartMaterialReplayCameraCapture(UWorld* World);
static void DestroyMaterialReplayCamera();
static void StartMaterialReplay(UWorld* World, FCommonViewportClient* ViewportClient);
static void StopMaterialReplay(UWorld* World, FCommonViewportClient* ViewportClient);
static void RestoreMaterialReplayAnimationStates();
static void RestoreMaterialDebugMaterialOverrides();
static void ClearMaterialReplayDerivedCaches();
static UWorld* FindCurrentPreviewWorld();
static void BuildFoliageComponentsBySourceLabel(UWorld* World, TMap<FString, TArray<UPrimitiveComponent*>>& OutComponentsBySourceLabel);
static int32 FindMaterialReplaySampleIndexForTime(double TimeSeconds);
static float FindNearestMaterialReplayUnitGpuMs(const TArray<FMaterialReplayUnitGpuSample>& Samples, double TimeSeconds);
static float GetMaterialReplayUnitGpuMsForTime(double TimeSeconds);
static void RebuildMaterialReplayFrameGpuMs();
static void ApplyMaterialReplayTime(UWorld* World, FCommonViewportClient* ViewportClient, double TimeSeconds, bool bForceRefresh = false);
static bool IsMaterialCaptureCommandLocked();
static bool IsMaterialCaptureCommand(const FString& Command);
static bool ShouldBlockMaterialCaptureCommand(const FString& Command);
static bool IsProfilingButtonEnabled(int32 ButtonIndex);
static bool TryHandleMaterialReplayPointerDown(const FPointerEvent& PointerEvent);
static bool TryHandleMaterialReplayPointerMove(const FPointerEvent& PointerEvent);
static bool TryHandleMaterialReplayPointerUp(const FPointerEvent& PointerEvent);

static float GetCaptureDurationSeconds()
{
	if (GCaptureStartTime < 0.0)
	{
		return 0.0f;
	}

	const double EndTime = GCaptureActive ? FPlatformTime::Seconds() : GCaptureEndTime;
	return static_cast<float>(FMath::Max(0.0, EndTime - GCaptureStartTime));
}

static void ClearMaterialReplayDerivedCaches()
{
	GMaterialReplayPeakIndices.Reset();
	GMaterialReplayPeakIndicesDirty = true;
	GMaterialReplayRowsCache.Reset();
	GMaterialReplayRowsCacheLru.Reset();
}

static void ClearCaptureState()
{
	GCaptureStartTime = -1.0;
	GCaptureEndTime = -1.0;
	GCaptureActive = false;
	GCaptureFrozen = false;
	GTraceStartedByCapture = false;
	GMaterialCaptureEndGuardActive = false;
	GMaterialCaptureEndGuardReleaseSeconds = 0.0;
	GTraceFilePath.Reset();
	GLastTraceFrameCount = 0;
	GLastDebugMaterialCount = 0;
	GLastDebugComponentCount = 0;
	GCachedRows.Reset();
	GCachedRowsAll.Reset();
	GCachedDebugRows.Reset();
	GMaterialReplayActive = false;
	GMaterialReplayPlaying = false;
	GMaterialReplayScrubbing = false;
	GMaterialReplayCurrentRows.Reset();
	GMaterialReplayCurrentRowsAll.Reset();
	GMaterialReplayDebugRows.Reset();
	GMaterialReplaySceneRows.Reset();
	GMaterialReplaySceneLookup.Reset();
	GMaterialReplaySamples.Reset();
	GMaterialReplayCameraSamples.Reset();
	GMaterialReplayCharacterSamples.Reset();
	GMaterialReplayUnitGpuSamples.Reset();
	GMaterialReplayFrameGpuMs.Reset();
	GMaterialReplayFrameGpuMsMax = 0.0f;
	ClearMaterialReplayDerivedCaches();
	GMaterialReplayCurrentTimeSeconds = 0.0;
	GMaterialReplayLastTickSeconds = -1.0;
	GMaterialReplayCurrentSampleIndex = INDEX_NONE;
	StopMaterialReplayTicker();
	StopMaterialReplayCameraCaptureTicker();
	RemoveMaterialReplayOverlay();
	RestoreMaterialReplayAnimationStates();
	RestoreMaterialDebugMaterialOverrides();
	DestroyMaterialReplayCamera();
}

static void ClearObjectMemorySnapshotState()
{
	GCachedObjectRows.Reset();
	GCachedObjectDebugRows.Reset();
	GLastObjectSnapshotSourceCount = 0;
	GLastObjectDebugComponentCount = 0;
	GLastObjectSnapshotTime = -1.0;
	GLastObjectSnapshotMessage.Reset();
	GLastObjectSnapshotFilePath.Reset();
}

static void SetCaptureConsoleVariable(const TCHAR* Name, int32 Value, bool& bHasPreviousValue, int32& PreviousValue)
{
	IConsoleVariable* Variable = IConsoleManager::Get().FindConsoleVariable(Name);
	if (!Variable)
	{
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Material GPU Preview capture cvar is unavailable: %s"), Name);
		return;
	}

	if (!bHasPreviousValue)
	{
		PreviousValue = Variable->GetInt();
		bHasPreviousValue = true;
	}

	Variable->Set(Value, ECVF_SetByConsole);
}

static void RestoreCaptureConsoleVariable(const TCHAR* Name, bool& bHasPreviousValue, int32 PreviousValue)
{
	if (!bHasPreviousValue)
	{
		return;
	}

	if (IConsoleVariable* Variable = IConsoleManager::Get().FindConsoleVariable(Name))
	{
		Variable->Set(PreviousValue, ECVF_SetByConsole);
	}

	bHasPreviousValue = false;
}

static void ApplyInsightsMaterialCaptureCvars()
{
	if (!GHasPreviousEmitDrawEvents)
	{
		GPreviousEmitDrawEvents = GetEmitDrawEvents();
		GHasPreviousEmitDrawEvents = true;
	}
	SetEmitDrawEvents(true);

	SetCaptureConsoleVariable(TEXT("r.ShowMaterialDrawEvents"), -1, GHasPreviousShowMaterialDrawEvents, GPreviousShowMaterialDrawEvents);
}

static void RestoreInsightsMaterialCaptureCvars()
{
	RestoreCaptureConsoleVariable(TEXT("r.ShowMaterialDrawEvents"), GHasPreviousShowMaterialDrawEvents, GPreviousShowMaterialDrawEvents);

	if (GHasPreviousEmitDrawEvents)
	{
		SetEmitDrawEvents(GPreviousEmitDrawEvents);
		GHasPreviousEmitDrawEvents = false;
	}
}

static FString NormalizeTraceLookupKey(FString Value)
{
	Value.TrimStartAndEndInline();
	Value.TrimQuotesInline();

	if (Value.StartsWith(TEXT("MaterialDrawEvent - ")))
	{
		Value.RightChopInline(20);
		Value.TrimStartInline();
	}
	else if (Value.StartsWith(TEXT("MaterialDrawEvent")))
	{
		Value.RightChopInline(17);
		Value.TrimStartInline();
		if (Value.StartsWith(TEXT("-")))
		{
			Value.RightChopInline(1);
			Value.TrimStartInline();
		}
	}

	if (Value.StartsWith(TEXT("'")) && Value.EndsWith(TEXT("'")))
	{
		Value = Value.Mid(1, Value.Len() - 2);
	}

	return Value.ToLower();
}

static void AddLookupKey(TMap<FString, int32>& Lookup, const FString& Key, int32 Index)
{
	const FString Normalized = NormalizeTraceLookupKey(Key);
	if (!Normalized.IsEmpty())
	{
		Lookup.FindOrAdd(Normalized, Index);
	}
}

static void AddMaterialLookupKeys(TMap<FString, int32>& Lookup, const FMaterialAccumulator& Row, int32 Index)
{
	AddLookupKey(Lookup, Row.DisplayName, Index);
	AddLookupKey(Lookup, Row.PathName, Index);

	if (UMaterialInterface* Material = Row.Material.Get())
	{
		AddLookupKey(Lookup, Material->GetName(), Index);
		AddLookupKey(Lookup, Material->GetPathName(), Index);
		AddLookupKey(Lookup, Material->GetFullName(), Index);

		FString PackageName;
		FString AssetName;
		Material->GetPathName().Split(TEXT("."), &PackageName, &AssetName, ESearchCase::CaseSensitive, ESearchDir::FromEnd);
		AddLookupKey(Lookup, AssetName, Index);
	}

	FString PackageName;
	FString AssetName;
	if (Row.PathName.Split(TEXT("."), &PackageName, &AssetName, ESearchCase::CaseSensitive, ESearchDir::FromEnd))
	{
		AddLookupKey(Lookup, AssetName, Index);
	}
}

static int32 FindSceneMaterialIndex(const TArray<FMaterialAccumulator>& SceneRows, const TMap<FString, int32>& Lookup, const FString& TraceMaterialName)
{
	const FString NormalizedTraceName = NormalizeTraceLookupKey(TraceMaterialName);
	if (NormalizedTraceName.IsEmpty())
	{
		return INDEX_NONE;
	}

	if (const int32* Index = Lookup.Find(NormalizedTraceName))
	{
		return *Index;
	}

	for (int32 Index = 0; Index < SceneRows.Num(); ++Index)
	{
		const FMaterialAccumulator& Row = SceneRows[Index];
		const FString RowPath = NormalizeTraceLookupKey(Row.PathName);
		const FString RowDisplay = NormalizeTraceLookupKey(Row.DisplayName);
		if ((!RowPath.IsEmpty() && (RowPath.EndsWith(NormalizedTraceName) || NormalizedTraceName.EndsWith(RowPath)))
			|| (!RowDisplay.IsEmpty() && (RowDisplay == NormalizedTraceName || NormalizedTraceName.Contains(RowDisplay))))
		{
			return Index;
		}
	}

	return INDEX_NONE;
}

static FString FormatTraceMetadata(const FString& InFormat, TArrayView<const uint8> InMetadata)
{
	if (InFormat.IsEmpty() || InMetadata.Num() == 0)
	{
		return FString();
	}

	FMemoryReaderView MemoryReader(InMetadata);
	FCborReader CborReader(&MemoryReader, ECborEndianness::StandardCompliant);
	FCborContext Context;

	FString Format = InFormat;
	Format.TrimStartInline();
	if (Format.StartsWith(TEXT("- ")))
	{
		Format.RightChopInline(2);
	}

	FString Result;
	const FString Specifiers = TEXT("diuoxXfFeEgGaAcspn");
	auto GetNextFormatSection = [&Format, &Specifiers]()
	{
		bool bIsInFormatSpecifier = false;
		for (int32 Index = 0; Index < Format.Len(); ++Index)
		{
			if (bIsInFormatSpecifier)
			{
				int32 SpecIndex = INDEX_NONE;
				if (Specifiers.FindChar(Format[Index], SpecIndex))
				{
					FString NextFormat = Format.Left(Index + 1);
					Format.MidInline(Index + 1);
					return NextFormat;
				}
			}

			if (Format[Index] == TEXT('%'))
			{
				bIsInFormatSpecifier = !bIsInFormatSpecifier;
			}
		}

		FString Copy = Format;
		Format.Empty();
		return Copy;
	};

	constexpr int32 MaxLength = 1024;
	TCHAR Data[MaxLength];

	auto AppendFormattedValue = [&Result, &Data](const FString& Section, auto Value)
	{
		const int32 Written = FCString::Snprintf(Data, MaxLength, reinterpret_cast<TCHAR const(&)[1]>(**Section), Value);
		if (Written > 0)
		{
			Result.Append(Data);
		}
	};

	while (!Format.IsEmpty())
	{
		if (!CborReader.ReadNext(Context))
		{
			break;
		}

		const FString Section = GetNextFormatSection();
		switch (Context.MajorType())
		{
		case ECborCode::Int:
			AppendFormattedValue(Section, Context.AsInt());
			continue;
		case ECborCode::Uint:
			AppendFormattedValue(Section, Context.AsUInt());
			continue;
		case ECborCode::TextString:
			AppendFormattedValue(Section, *Context.AsString());
			continue;
		case ECborCode::ByteString:
			AppendFormattedValue(Section, Context.AsCString());
			continue;
		default:
			break;
		}

		if (Context.RawCode() == (ECborCode::Prim | ECborCode::Value_4Bytes))
		{
			AppendFormattedValue(Section, Context.AsFloat());
			continue;
		}

		if (Context.RawCode() == (ECborCode::Prim | ECborCode::Value_8Bytes))
		{
			AppendFormattedValue(Section, Context.AsDouble());
			continue;
		}

		if (Context.RawCode() == (ECborCode::Prim | ECborCode::False))
		{
			AppendFormattedValue(Section, false);
			continue;
		}

		if (Context.RawCode() == (ECborCode::Prim | ECborCode::True))
		{
			AppendFormattedValue(Section, true);
			continue;
		}

		Result.Append(TEXT("???"));
		if (Context.IsFiniteContainer())
		{
			CborReader.SkipContainer(ECborCode::Array);
		}
	}

	Result.Append(Format);
	Result.TrimStartAndEndInline();
	return Result;
}

static FString GetTraceTimerName(
	const TraceServices::ITimingProfilerProvider& TimingProfilerProvider,
	const TraceServices::ITimingProfilerTimerReader& TimerReader,
	uint32 TimerIndex,
	FString* OutBaseTimerName = nullptr)
{
	const uint32 OriginalTimerIndex = TimerReader.GetOriginalTimerIdFromMetadata(TimerIndex);
	const TraceServices::FTimingProfilerTimer* Timer = TimerReader.GetTimer(OriginalTimerIndex);
	if (!Timer || !Timer->Name)
	{
		return FString();
	}

	const FString BaseTimerName(Timer->Name);
	if (OutBaseTimerName)
	{
		*OutBaseTimerName = BaseTimerName;
	}

	if (static_cast<int32>(TimerIndex) >= 0 || !Timer->HasValidMetadataSpecId())
	{
		return BaseTimerName;
	}

	const TraceServices::FMetadataSpec* MetadataSpec = TimingProfilerProvider.GetMetadataSpec(Timer->MetadataSpecId);
	if (!MetadataSpec || !MetadataSpec->Format)
	{
		return BaseTimerName;
	}

	const FString MetadataText = FormatTraceMetadata(FString(MetadataSpec->Format), TimerReader.GetMetadata(TimerIndex));
	return MetadataText.IsEmpty() ? BaseTimerName : MetadataText;
}

static FString ExtractMaterialNameFromDrawEvent(FString EventName)
{
	EventName.TrimStartAndEndInline();
	if (EventName.StartsWith(TEXT("MaterialDrawEvent - ")))
	{
		EventName.RightChopInline(20);
		EventName.TrimStartInline();
	}
	else if (EventName.StartsWith(TEXT("MaterialDrawEvent")))
	{
		EventName.RightChopInline(17);
		EventName.TrimStartInline();
		if (EventName.StartsWith(TEXT("-")))
		{
			EventName.RightChopInline(1);
			EventName.TrimStartInline();
		}
	}

	int32 FirstSpace = INDEX_NONE;
	if (EventName.FindChar(TEXT(' '), FirstSpace) && FirstSpace > 0)
	{
		EventName.LeftInline(FirstSpace);
	}

	EventName.TrimStartAndEndInline();
	EventName.TrimQuotesInline();
	return EventName;
}

static void AddTraceDiagnosticSample(TArray<FString>& Samples, TSet<FString>& SeenSamples, const FString& Sample)
{
	constexpr int32 MaxSamples = 24;
	if (Samples.Num() >= MaxSamples || Sample.IsEmpty())
	{
		return;
	}

	if (SeenSamples.Contains(Sample))
	{
		return;
	}

	SeenSamples.Add(Sample);
	Samples.Add(Sample);
}

static FString FindMaterialNameForTraceEvent(
	const TArray<FMaterialAccumulator>& SceneRows,
	const TMap<FString, int32>& SceneLookup,
	const FString& TraceEventName,
	const FString& BaseTimerName)
{
	if (BaseTimerName.Equals(TEXT("MaterialDrawEvent"), ESearchCase::CaseSensitive))
	{
		return ExtractMaterialNameFromDrawEvent(TraceEventName);
	}

	if (BaseTimerName.Equals(TEXT("GpuWork"), ESearchCase::CaseSensitive)
		|| BaseTimerName.Equals(TEXT("GpuWait"), ESearchCase::CaseSensitive))
	{
		return FString();
	}

	const int32 DirectEventIndex = FindSceneMaterialIndex(SceneRows, SceneLookup, TraceEventName);
	if (SceneRows.IsValidIndex(DirectEventIndex))
	{
		return SceneRows[DirectEventIndex].DisplayName;
	}

	const int32 BaseTimerIndex = FindSceneMaterialIndex(SceneRows, SceneLookup, BaseTimerName);
	if (SceneRows.IsValidIndex(BaseTimerIndex))
	{
		return SceneRows[BaseTimerIndex].DisplayName;
	}

	return FString();
}

static FString FindMaterialNameForTraceEventCached(
	const TArray<FMaterialAccumulator>& SceneRows,
	const TMap<FString, int32>& SceneLookup,
	const FString& TraceEventName,
	const FString& BaseTimerName,
	TMap<FString, FString>& ResolvedMaterialNameCache,
	TSet<FString>& UnresolvedMaterialNameCache,
	int32& OutResolveCacheHits,
	int32& OutResolveCacheMisses)
{
	const FString CacheKey = FString::Printf(TEXT("%s\n%s"), *BaseTimerName, *TraceEventName);
	if (const FString* CachedMaterialName = ResolvedMaterialNameCache.Find(CacheKey))
	{
		OutResolveCacheHits++;
		return *CachedMaterialName;
	}

	if (UnresolvedMaterialNameCache.Contains(CacheKey))
	{
		OutResolveCacheHits++;
		return FString();
	}

	OutResolveCacheMisses++;
	const FString MaterialName = FindMaterialNameForTraceEvent(SceneRows, SceneLookup, TraceEventName, BaseTimerName);
	if (MaterialName.IsEmpty())
	{
		UnresolvedMaterialNameCache.Add(CacheKey);
	}
	else
	{
		ResolvedMaterialNameCache.Add(CacheKey, MaterialName);
	}

	return MaterialName;
}

static float GetSeverityMs(const FMaterialAccumulator& Row)
{
	return Row.MaxGpuMs;
}

static const FString& GetOptimizationPreviewToolsIni()
{
	if (!GOptimizationPreviewToolsIniLoaded)
	{
		FConfigCacheIni::LoadGlobalIniFile(GOptimizationPreviewToolsIni, MaterialGPUPreviewConfigName);
		GOptimizationPreviewToolsIniLoaded = true;
	}

	return GOptimizationPreviewToolsIni;
}

static float ReadMaterialGPUPreviewConfigFloat(const TCHAR* Key, float DefaultValue)
{
	float Value = DefaultValue;
	if (GConfig)
	{
		const FString& ConfigFile = GetOptimizationPreviewToolsIni();
		if (!ConfigFile.IsEmpty())
		{
			GConfig->GetFloat(MaterialGPUPreviewConfigSection, Key, Value, ConfigFile);
		}
	}

	return Value;
}

static float ReadMaterialGPUPreviewConfigFloatWithLegacyKey(const TCHAR* Key, const TCHAR* LegacyKey, float DefaultValue)
{
	float Value = DefaultValue;
	if (GConfig)
	{
		const FString& ConfigFile = GetOptimizationPreviewToolsIni();
		if (!ConfigFile.IsEmpty() && !GConfig->GetFloat(MaterialGPUPreviewConfigSection, Key, Value, ConfigFile) && LegacyKey)
		{
			GConfig->GetFloat(MaterialGPUPreviewConfigSection, LegacyKey, Value, ConfigFile);
		}
	}

	return Value;
}

static bool ReadMaterialGPUPreviewConfigBool(const TCHAR* Key, bool bDefaultValue)
{
	bool bValue = bDefaultValue;
	if (GConfig)
	{
		const FString& ConfigFile = GetOptimizationPreviewToolsIni();
		if (!ConfigFile.IsEmpty())
		{
			GConfig->GetBool(MaterialGPUPreviewConfigSection, Key, bValue, ConfigFile);
		}
	}

	return bValue;
}

static FString ReadMaterialGPUPreviewConfigString(const TCHAR* Key, const TCHAR* DefaultValue)
{
	FString Value(DefaultValue);
	if (GConfig)
	{
		const FString& ConfigFile = GetOptimizationPreviewToolsIni();
		if (!ConfigFile.IsEmpty())
		{
			GConfig->GetString(MaterialGPUPreviewConfigSection, Key, Value, ConfigFile);
		}
	}

	Value.TrimStartAndEndInline();
	return Value.IsEmpty() ? FString(DefaultValue) : Value;
}

static float ReadObjectMemorySnapshotConfigFloat(const TCHAR* Key, float DefaultValue)
{
	float Value = DefaultValue;
	if (GConfig)
	{
		const FString& ConfigFile = GetOptimizationPreviewToolsIni();
		if (!ConfigFile.IsEmpty())
		{
			GConfig->GetFloat(ObjectMemorySnapshotConfigSection, Key, Value, ConfigFile);
		}
	}

	return Value;
}

static FString GetMaterialGPUTraceChannels()
{
	FString TraceChannels = CVarTraceChannels.GetValueOnGameThread();
	TraceChannels.TrimStartAndEndInline();
	if (!TraceChannels.IsEmpty())
	{
		return TraceChannels;
	}

	return ReadMaterialGPUPreviewConfigString(TEXT("TraceChannels"), DefaultMaterialGPUTraceChannels);
}

static float GetDebugGreenMs()
{
	return FMath::Max(ReadMaterialGPUPreviewConfigFloatWithLegacyKey(TEXT("DebugGreenMs"), TEXT("DebugGreenMaxMs"), DefaultDebugGreenMs), 0.001f);
}

static float GetDebugRedMs()
{
	return FMath::Max(ReadMaterialGPUPreviewConfigFloat(TEXT("DebugRedMs"), DefaultDebugRedMs), GetDebugGreenMs() + 0.001f);
}

static float GetDebugPinkMs()
{
	return FMath::Max(ReadMaterialGPUPreviewConfigFloat(TEXT("DebugPinkMs"), DefaultDebugPinkMs), GetDebugRedMs() + 0.001f);
}

static float GetDebugWhiteMs()
{
	return FMath::Max(ReadMaterialGPUPreviewConfigFloat(TEXT("DebugWhiteMs"), DefaultDebugWhiteMs), GetDebugPinkMs() + 0.001f);
}

static bool ShouldEmitMaterialGPUUnitGpuCounter()
{
	return ReadMaterialGPUPreviewConfigBool(TEXT("EmitUnitGpuCounter"), true);
}

static float GetObjectDebugGreenMaxMB()
{
	return FMath::Max(ReadObjectMemorySnapshotConfigFloat(TEXT("DebugGreenMaxMB"), DefaultObjectDebugGreenMaxMB), 0.001f);
}

static float GetObjectDebugWhiteMB()
{
	return FMath::Max(ReadObjectMemorySnapshotConfigFloat(TEXT("DebugWhiteMB"), DefaultObjectDebugWhiteMB), GetObjectDebugGreenMaxMB() + 0.001f);
}

static FLinearColor GetTwoPointDebugColorForRange(float Value, float GreenMax, float White)
{
	const FLinearColor LowColor(0.0f, 1.0f, 0.0f, 1.0f);
	const FLinearColor MidColor(1.0f, 0.0f, 0.0f, 1.0f);
	const FLinearColor HighColor(1.0f, 0.0f, 1.0f, 1.0f);

	if (Value >= White)
	{
		return HighColor;
	}

	if (Value < GreenMax)
	{
		return FMath::Lerp(
			LowColor,
			MidColor,
			FMath::Clamp(Value / GreenMax, 0.0f, 1.0f));
	}

	return FMath::Lerp(
		MidColor,
		HighColor,
		FMath::Clamp((Value - GreenMax) / (White - GreenMax), 0.0f, 1.0f));
}

static float GetSmoothDebugRampAlpha(float Value, float Start, float End)
{
	return FMath::SmoothStep(0.0f, 1.0f, FMath::Clamp((Value - Start) / (End - Start), 0.0f, 1.0f));
}

static FLinearColor GetFourPointDebugColorForRange(float Value, float GreenMs, float RedMs, float PinkMs, float WhiteMs)
{
	const FLinearColor GreenColor(0.0f, 1.0f, 0.0f, 1.0f);
	const FLinearColor RedColor(1.0f, 0.0f, 0.0f, 1.0f);
	const FLinearColor PinkColor(1.0f, 0.0f, 1.0f, 1.0f);
	const FLinearColor WhiteColor(1.0f, 1.0f, 1.0f, 1.0f);

	if (Value <= GreenMs)
	{
		return GreenColor;
	}

	if (Value < RedMs)
	{
		return FMath::Lerp(GreenColor, RedColor, GetSmoothDebugRampAlpha(Value, GreenMs, RedMs));
	}

	if (Value < PinkMs)
	{
		return FMath::Lerp(RedColor, PinkColor, GetSmoothDebugRampAlpha(Value, RedMs, PinkMs));
	}

	if (Value < WhiteMs)
	{
		return FMath::Lerp(PinkColor, WhiteColor, GetSmoothDebugRampAlpha(Value, PinkMs, WhiteMs));
	}

	return WhiteColor;
}

static FLinearColor GetMaterialGpuPreviewColor(float MaxGpuMs, float Alpha = 1.0f)
{
	FLinearColor Color = GetFourPointDebugColorForRange(MaxGpuMs, GetDebugGreenMs(), GetDebugRedMs(), GetDebugPinkMs(), GetDebugWhiteMs());
	Color.A = Alpha;
	return Color;
}

static FLinearColor GetObjectMemorySnapshotColor(float TotalMB, float Alpha = 1.0f)
{
	FLinearColor Color = GetTwoPointDebugColorForRange(TotalMB, GetObjectDebugGreenMaxMB(), GetObjectDebugWhiteMB());
	Color.A = Alpha;
	return Color;
}

static bool IsMaterialDebugColorModeEnabled()
{
	return CVarMaterialDebugMode.GetValueOnGameThread() != 0;
}

static FString GetMaterialDebugModeLabel()
{
	if (CVarDebug.GetValueOnGameThread() == 0 && !GMaterialReplayActive)
	{
		return TEXT("Off");
	}

	return IsMaterialDebugColorModeEnabled() ? TEXT("Color") : TEXT("Original");
}

static FString GetObjectDebugModeLabel()
{
	if (CVarObjectDebug.GetValueOnGameThread() == 0)
	{
		return TEXT("Off");
	}

	return IsMaterialDebugColorModeEnabled() ? TEXT("Color") : TEXT("Original");
}

static int32 GetDebugSeverity(float MaxGpuMs)
{
	if (MaxGpuMs >= GetDebugWhiteMs())
	{
		return 4;
	}

	if (MaxGpuMs >= GetDebugPinkMs())
	{
		return 3;
	}

	if (MaxGpuMs >= GetDebugRedMs())
	{
		return 2;
	}

	return 1;
}

static int32 GetObjectDebugSeverity(float TotalMB)
{
	if (TotalMB >= GetObjectDebugWhiteMB())
	{
		return 3;
	}

	if (TotalMB >= GetObjectDebugGreenMaxMB())
	{
		return 2;
	}

	return 1;
}

static FColor GetDebugSeverityColor(float MaxGpuMs, uint8 Alpha)
{
	FLinearColor Color = GetMaterialGpuPreviewColor(MaxGpuMs, static_cast<float>(Alpha) / 255.0f);
	return Color.ToFColor(false);
}

static FColor GetObjectDebugSeverityColor(float TotalMB, uint8 Alpha)
{
	FLinearColor Color = GetObjectMemorySnapshotColor(TotalMB, static_cast<float>(Alpha) / 255.0f);
	return Color.ToFColor(false);
}

static uint32 MakeDebugBatchId(const UPrimitiveComponent* Component)
{
	const uint32 UniqueId = Component ? Component->GetUniqueID() : 0u;
	const uint32 BatchId = 0x4D430000u ^ UniqueId;
	return BatchId != ULineBatchComponent::INVALID_ID ? BatchId : 0x4D430001u;
}

static ULineBatchComponent* GetMaterialCostLineBatcher(UWorld* World)
{
	return World ? World->GetLineBatcher(UWorld::ELineBatcherType::WorldPersistent) : nullptr;
}

static void ClearDebugBatch(UWorld* World, uint32 BatchId)
{
	if (ULineBatchComponent* LineBatcher = GetMaterialCostLineBatcher(World))
	{
		LineBatcher->ClearBatch(BatchId);
	}
}

static void ClearCachedDebugOverlay(UWorld* World)
{
	UWorld* TargetWorld = World ? World : GCachedDebugWorld.Get();
	for (const FDebugOverlayEntry& Entry : GCachedDebugEntries)
	{
		ClearDebugBatch(TargetWorld, Entry.BatchId);
	}

	GCachedDebugEntries.Reset();
	GCachedDebugWorld = nullptr;
}

static bool IsForceDebugViewModesEnabled()
{
	if (IConsoleVariable* Variable = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ForceDebugViewModes")))
	{
		return Variable->GetInt() == 1;
	}

	return false;
}

static bool ShouldUseActorColorationBackend()
{
#if WITH_EDITOR
	return true;
#elif UE_BUILD_SHIPPING || UE_BUILD_TEST
	return false;
#else
	return IsForceDebugViewModesEnabled();
#endif
}

static FLinearColor GetActorColorationPrimitiveColor(const UPrimitiveComponent* Component)
{
	if (!Component)
	{
		return FLinearColor::Black;
	}

	if (const FLinearColor* Color = GActorColorationColors.Find(FObjectKey(Component)))
	{
		return *Color;
	}

	if (GMaterialReplayActive)
	{
		return GetMaterialGpuPreviewColor(0.0f);
	}

	return FLinearColor::Black;
}

static void RegisterActorColorationHandler()
{
#if !(UE_BUILD_SHIPPING || UE_BUILD_TEST)
	if (GActorColorationHandlerRegistered)
	{
		return;
	}

	FActorPrimitiveColorHandler::Get().RegisterPrimitiveColorHandler(
		ActorColorationHandlerName,
		LOCTEXT("OptimizationPreviewToolsActorColoration", "Optimization Preview Tools"),
		[](const UPrimitiveComponent* Component) -> FLinearColor
		{
			return GetActorColorationPrimitiveColor(Component);
		},
		[]() {},
		LOCTEXT("OptimizationPreviewToolsActorColorationTooltip", "Colorize primitives from the active Optimization Preview Tools snapshot. Non-target primitives are black."));
	GActorColorationHandlerRegistered = true;
#endif
}

static void UnregisterActorColorationHandler()
{
#if !(UE_BUILD_SHIPPING || UE_BUILD_TEST)
	if (!GActorColorationHandlerRegistered)
	{
		return;
	}

	FActorPrimitiveColorHandler::Get().UnregisterPrimitiveColorHandler(ActorColorationHandlerName);
	GActorColorationHandlerRegistered = false;
#endif
}

struct FActorColorationTarget
{
	TWeakObjectPtr<UPrimitiveComponent> Component;
	float MaxGpuMs = 0.0f;
	int32 Severity = 0;
	FLinearColor Color = FLinearColor::Black;
};

static bool IsDebugTargetComponent(const UPrimitiveComponent* Component);
static bool CanApplyMaterialDebugOverrideFallbackToComponent(const UPrimitiveComponent* Component);

static UPackage* GetMaterialDebugOverridePackage(UPrimitiveComponent* Component)
{
	return Component ? Component->GetOutermost() : nullptr;
}

static void RestoreMaterialDebugOverridePackageDirtyFlag(const FMaterialDebugMaterialOverrideState& State)
{
	if (UPackage* Package = State.Package.Get())
	{
		Package->SetDirtyFlag(State.bPackageWasDirty);
	}
}

static bool ShouldUseMaterialDebugOverrideFallback(UMaterialInterface* Material)
{
	if (!Material)
	{
		return false;
	}

	return Material->GetBlendMode() != BLEND_Opaque;
}

static bool ApplyMaterialDebugColorParameters(UMaterialInstanceDynamic* Material, const FLinearColor& Color)
{
	if (!Material)
	{
		return false;
	}

	FLinearColor DebugColor = Color;
	DebugColor.A = 1.0f;

	bool bAppliedColorParameter = false;
	auto IsColorLikeParameterName = [](FName ParameterName)
	{
		const FString Name = ParameterName.ToString();
		return Name.Contains(TEXT("Color"), ESearchCase::IgnoreCase)
			|| Name.Contains(TEXT("Tint"), ESearchCase::IgnoreCase)
			|| Name.Contains(TEXT("Albedo"), ESearchCase::IgnoreCase)
			|| Name.Contains(TEXT("Diffuse"), ESearchCase::IgnoreCase)
			|| Name.Contains(TEXT("Emissive"), ESearchCase::IgnoreCase)
			|| Name.Contains(TEXT("Gradient"), ESearchCase::IgnoreCase);
	};

	TArray<FMaterialParameterInfo> VectorParameterInfos;
	TArray<FGuid> VectorParameterIds;
	Material->GetAllVectorParameterInfo(VectorParameterInfos, VectorParameterIds);
	for (const FMaterialParameterInfo& ParameterInfo : VectorParameterInfos)
	{
		if (IsColorLikeParameterName(ParameterInfo.Name))
		{
			Material->SetVectorParameterValueByInfo(ParameterInfo, DebugColor);
			bAppliedColorParameter = true;
		}
	}

	static const FName CommonColorParameterNames[] =
	{
		TEXT("Color"),
		TEXT("BaseColor"),
		TEXT("Base Color"),
		TEXT("Tint"),
		TEXT("TintColor"),
		TEXT("Tint Color"),
		TEXT("Albedo"),
		TEXT("Diffuse"),
		TEXT("Emissive"),
		TEXT("EmissiveColor"),
		TEXT("Emissive Color"),
		TEXT("DebugColor"),
		TEXT("Debug Color")
	};

	for (const FName& ParameterName : CommonColorParameterNames)
	{
		int32 ParameterIndex = INDEX_NONE;
		if (Material->InitializeVectorParameterAndGetIndex(ParameterName, DebugColor, ParameterIndex))
		{
			bAppliedColorParameter = true;
		}
	}

	return bAppliedColorParameter;
}

static UMaterialInterface* GetMaterialDebugOverrideMaterial(const FLinearColor& Color, UMaterialInterface* OriginalMaterial)
{
	if (OriginalMaterial && OriginalMaterial->GetBlendMode() == BLEND_Masked)
	{
		UMaterialInstanceDynamic* MaskedMaterial = UMaterialInstanceDynamic::Create(OriginalMaterial, GetTransientPackage());
		if (MaskedMaterial)
		{
			MaskedMaterial->SetFlags(RF_Transient);
			if (ApplyMaterialDebugColorParameters(MaskedMaterial, Color))
			{
				return MaskedMaterial;
			}
		}
	}

	if (!GEngine || !GEngine->ShadedLevelColorationUnlitMaterial)
	{
		return nullptr;
	}

	UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(
		GEngine->ShadedLevelColorationUnlitMaterial,
		GetTransientPackage());
	if (!Material)
	{
		return nullptr;
	}

	Material->SetFlags(RF_Transient);
	Material->SetVectorParameterValue(TEXT("Color"), Color);
	return Material;
}

static UMaterialInterface* GetOriginalMaterialForDebugOverride(
	UPrimitiveComponent* Component,
	const FMaterialDebugMaterialOverrideState* ExistingState,
	int32 SlotIndex)
{
	if (ExistingState && ExistingState->OriginalMaterials.IsValidIndex(SlotIndex))
	{
		return ExistingState->OriginalMaterials[SlotIndex].Get();
	}

	return Component ? Component->GetMaterial(SlotIndex) : nullptr;
}

static void RestoreMaterialDebugMaterialOverrideState(const FObjectKey& ComponentKey, FMaterialDebugMaterialOverrideState& State)
{
	UPrimitiveComponent* Component = State.Component.Get();
	if (!Component)
	{
		return;
	}

	for (int32 SlotIndex : State.OverriddenSlots)
	{
		if (State.OriginalMaterials.IsValidIndex(SlotIndex))
		{
			Component->SetMaterial(SlotIndex, State.OriginalMaterials[SlotIndex].Get());
		}
	}

	Component->MarkRenderStateDirty();
	RestoreMaterialDebugOverridePackageDirtyFlag(State);
}

static void RestoreMaterialDebugMaterialOverrides()
{
	for (TPair<FObjectKey, FMaterialDebugMaterialOverrideState>& Pair : GMaterialDebugMaterialOverrides)
	{
		RestoreMaterialDebugMaterialOverrideState(Pair.Key, Pair.Value);
	}

	GMaterialDebugMaterialOverrides.Reset();
}

static void ApplyMaterialDebugMaterialOverrides(const TArray<FActorColorationTarget>& Targets)
{
	if (CVarDebugMaterialOverrideFallback.GetValueOnGameThread() == 0)
	{
		RestoreMaterialDebugMaterialOverrides();
		return;
	}

	TSet<FObjectKey> DesiredOverrideComponents;
	for (const FActorColorationTarget& Target : Targets)
	{
		UPrimitiveComponent* Component = Target.Component.Get();
		if (!IsDebugTargetComponent(Component) || !CanApplyMaterialDebugOverrideFallbackToComponent(Component))
		{
			continue;
		}

		const int32 NumMaterials = Component->GetNumMaterials();
		if (NumMaterials <= 0)
		{
			continue;
		}

		const FObjectKey ComponentKey(Component);
		FMaterialDebugMaterialOverrideState* ExistingState = GMaterialDebugMaterialOverrides.Find(ComponentKey);
		TArray<int32> OverrideSlots;
		for (int32 SlotIndex = 0; SlotIndex < NumMaterials; ++SlotIndex)
		{
			UMaterialInterface* OriginalMaterial = GetOriginalMaterialForDebugOverride(Component, ExistingState, SlotIndex);
			if (ShouldUseMaterialDebugOverrideFallback(OriginalMaterial))
			{
				OverrideSlots.Add(SlotIndex);
			}
		}

		if (OverrideSlots.Num() == 0)
		{
			continue;
		}

		TMap<int32, UMaterialInterface*> DebugMaterialsBySlot;
		for (int32 SlotIndex : OverrideSlots)
		{
			UMaterialInterface* OriginalMaterial = GetOriginalMaterialForDebugOverride(Component, ExistingState, SlotIndex);
			if (UMaterialInterface* DebugMaterial = GetMaterialDebugOverrideMaterial(Target.Color, OriginalMaterial))
			{
				DebugMaterialsBySlot.Add(SlotIndex, DebugMaterial);
			}
		}

		if (DebugMaterialsBySlot.Num() == 0)
		{
			continue;
		}

		DesiredOverrideComponents.Add(ComponentKey);
		FMaterialDebugMaterialOverrideState& State = GMaterialDebugMaterialOverrides.FindOrAdd(ComponentKey);
		if (!State.Component.IsValid())
		{
			State.Component = Component;
			State.Package = GetMaterialDebugOverridePackage(Component);
			if (UPackage* Package = State.Package.Get())
			{
				State.bPackageWasDirty = Package->IsDirty();
			}
			State.OriginalMaterials.SetNum(NumMaterials);
			for (int32 SlotIndex = 0; SlotIndex < NumMaterials; ++SlotIndex)
			{
				State.OriginalMaterials[SlotIndex] = Component->GetMaterial(SlotIndex);
			}
		}

		State.OverriddenSlots.Reset();
		for (const TPair<int32, UMaterialInterface*>& Pair : DebugMaterialsBySlot)
		{
			State.OverriddenSlots.Add(Pair.Key);
			Component->SetMaterial(Pair.Key, Pair.Value);
		}
		Component->MarkRenderStateDirty();
		RestoreMaterialDebugOverridePackageDirtyFlag(State);
	}

	TArray<FObjectKey> ComponentsToRestore;
	for (const TPair<FObjectKey, FMaterialDebugMaterialOverrideState>& Pair : GMaterialDebugMaterialOverrides)
	{
		if (!DesiredOverrideComponents.Contains(Pair.Key))
		{
			ComponentsToRestore.Add(Pair.Key);
		}
	}

	for (const FObjectKey& ComponentKey : ComponentsToRestore)
	{
		if (FMaterialDebugMaterialOverrideState* State = GMaterialDebugMaterialOverrides.Find(ComponentKey))
		{
			RestoreMaterialDebugMaterialOverrideState(ComponentKey, *State);
		}
		GMaterialDebugMaterialOverrides.Remove(ComponentKey);
	}
}

static bool IsDebugTargetComponent(const UPrimitiveComponent* Component)
{
	return Component && Component->IsRegistered() && Component->IsVisible();
}

static bool CanApplyMaterialDebugOverrideFallbackToComponent(const UPrimitiveComponent* Component)
{
	return Component && Component->IsA<UStaticMeshComponent>();
}

static int32 GetDebugComponentLimit()
{
	return FMath::Max(CVarMaxDebugComponents.GetValueOnGameThread(), 0);
}

static int32 CountUniqueDebugComponents(const TArray<FMaterialAccumulator>& Rows)
{
	TSet<FObjectKey> Components;
	for (const FMaterialAccumulator& Row : Rows)
	{
		for (const TWeakObjectPtr<UPrimitiveComponent>& WeakComponent : Row.Components)
		{
			if (UPrimitiveComponent* Component = WeakComponent.Get())
			{
				Components.Add(FObjectKey(Component));
			}
		}
	}

	return Components.Num();
}

static const TArray<FMaterialAccumulator>& GetActiveMaterialDebugRows()
{
	return GMaterialReplayActive ? GMaterialReplayDebugRows : GCachedDebugRows;
}

static void AddActorColorationTarget(
	TMap<UPrimitiveComponent*, FActorColorationTarget>& TargetsByComponent,
	UPrimitiveComponent* Component,
	float DebugMs,
	int32 Severity,
	const FLinearColor& Color)
{
	if (!IsDebugTargetComponent(Component))
	{
		return;
	}

	FActorColorationTarget* ExistingTarget = TargetsByComponent.Find(Component);
	if (ExistingTarget && ExistingTarget->MaxGpuMs >= DebugMs)
	{
		return;
	}

	FActorColorationTarget Target;
	Target.Component = Component;
	Target.MaxGpuMs = DebugMs;
	Target.Severity = Severity;
	Target.Color = Color;
	TargetsByComponent.Add(Component, Target);
}

static void RebuildActorColorationColorMap()
{
	GActorColorationColors.Reset();

	const int32 MaxDebugComponents = GetDebugComponentLimit();

	TMap<FString, TArray<UPrimitiveComponent*>> FoliageComponentsBySourceLabel;
	if (UWorld* World = FindCurrentPreviewWorld())
	{
		BuildFoliageComponentsBySourceLabel(World, FoliageComponentsBySourceLabel);
	}

	TMap<UPrimitiveComponent*, FActorColorationTarget> TargetsByComponent;
	for (const FMaterialAccumulator& Row : GetActiveMaterialDebugRows())
	{
		const float DebugMs = GetSeverityMs(Row);
		const int32 Severity = GetDebugSeverity(DebugMs);
		const FLinearColor Color = GetMaterialGpuPreviewColor(DebugMs);

		for (const TWeakObjectPtr<UPrimitiveComponent>& WeakComponent : Row.Components)
		{
			AddActorColorationTarget(TargetsByComponent, WeakComponent.Get(), DebugMs, Severity, Color);
		}

		for (const FMaterialSourceUsage& SourceUsage : Row.SourceUsages)
		{
			if (SourceUsage.Label.IsEmpty())
			{
				continue;
			}

			if (const TArray<UPrimitiveComponent*>* CurrentFoliageComponents = FoliageComponentsBySourceLabel.Find(SourceUsage.Label))
			{
				for (UPrimitiveComponent* Component : *CurrentFoliageComponents)
				{
					AddActorColorationTarget(TargetsByComponent, Component, DebugMs, Severity, Color);
				}
			}
		}
	}

	TArray<FActorColorationTarget> Targets;
	TargetsByComponent.GenerateValueArray(Targets);
	Targets.Sort([](const FActorColorationTarget& A, const FActorColorationTarget& B)
	{
		if (A.Severity != B.Severity)
		{
			return A.Severity > B.Severity;
		}

		if (!FMath::IsNearlyEqual(A.MaxGpuMs, B.MaxGpuMs))
		{
			return A.MaxGpuMs > B.MaxGpuMs;
		}

		const UPrimitiveComponent* AComponent = A.Component.Get();
		const UPrimitiveComponent* BComponent = B.Component.Get();
		return (AComponent ? AComponent->GetUniqueID() : 0u) < (BComponent ? BComponent->GetUniqueID() : 0u);
	});

	if (MaxDebugComponents > 0 && Targets.Num() > MaxDebugComponents)
	{
		Targets.SetNum(MaxDebugComponents);
	}

	for (const FActorColorationTarget& Target : Targets)
	{
		if (UPrimitiveComponent* Component = Target.Component.Get())
		{
			GActorColorationColors.Add(FObjectKey(Component), Target.Color);
		}
	}

	ApplyMaterialDebugMaterialOverrides(Targets);
}

static UGameViewportClient* FindGameViewportClient(FCommonViewportClient* ViewportClient)
{
	if (!GEngine || !ViewportClient)
	{
		return nullptr;
	}

	if (GEngine->GameViewport == ViewportClient)
	{
		return GEngine->GameViewport;
	}

	for (const FWorldContext& WorldContext : GEngine->GetWorldContexts())
	{
		if (WorldContext.GameViewport == ViewportClient)
		{
			return WorldContext.GameViewport;
		}
	}

	return nullptr;
}

#if WITH_EDITOR
static FEditorViewportClient* FindEditorViewportClient(FCommonViewportClient* ViewportClient)
{
	if (!GEditor || !ViewportClient)
	{
		return nullptr;
	}

	for (FEditorViewportClient* EditorViewportClient : GEditor->GetAllViewportClients())
	{
		if (EditorViewportClient == ViewportClient)
		{
			return EditorViewportClient;
		}
	}

	return nullptr;
}
#endif

static FCommonViewportClient* FindViewportClientForViewport(FViewport* Viewport)
{
	if (!Viewport)
	{
		return nullptr;
	}

	if (GEngine)
	{
		if (GEngine->GameViewport && GEngine->GameViewport->Viewport == Viewport)
		{
			return GEngine->GameViewport;
		}

		for (const FWorldContext& WorldContext : GEngine->GetWorldContexts())
		{
			if (WorldContext.GameViewport && WorldContext.GameViewport->Viewport == Viewport)
			{
				return WorldContext.GameViewport;
			}
		}
	}

#if WITH_EDITOR
	if (GEditor)
	{
		for (FEditorViewportClient* EditorViewportClient : GEditor->GetAllViewportClients())
		{
			if (EditorViewportClient && EditorViewportClient->Viewport == Viewport)
			{
				return EditorViewportClient;
			}
		}
	}
#endif

	return nullptr;
}

static UGameViewportClient* ResolveProfilingGameViewport(FCommonViewportClient* ViewportClient)
{
	if (UGameViewportClient* GameViewportClient = FindGameViewportClient(ViewportClient))
	{
		return GameViewportClient;
	}

	if (GEngine)
	{
		if (GEngine->GameViewport)
		{
			return GEngine->GameViewport;
		}

		for (const FWorldContext& WorldContext : GEngine->GetWorldContexts())
		{
			if (WorldContext.GameViewport)
			{
				return WorldContext.GameViewport;
			}
		}
	}

	return nullptr;
}

struct FProfilingViewportLayout
{
	float ViewMinX = 0.0f;
	float ViewMinY = 0.0f;
	float ViewWidth = 1280.0f;
	float ViewHeight = 720.0f;
};

static FProfilingViewportLayout ResolveProfilingViewportLayout(FViewport* Viewport, FCanvas* Canvas, FCommonViewportClient* ViewportClient)
{
	FProfilingViewportLayout Layout;
	const FIntRect CanvasViewRect = Canvas ? Canvas->GetViewRect() : FIntRect(0, 0, 0, 0);
	const FIntPoint RenderTargetSize = (Canvas && Canvas->GetRenderTarget()) ? Canvas->GetRenderTarget()->GetSizeXY() : FIntPoint(1280, 720);
	const FIntPoint RawViewportSize = Viewport ? Viewport->GetSizeXY() : RenderTargetSize;
	const int32 FallbackWidth = RawViewportSize.X > 0 ? RawViewportSize.X : RenderTargetSize.X;
	const int32 FallbackHeight = RawViewportSize.Y > 0 ? RawViewportSize.Y : RenderTargetSize.Y;
	const float DPIScale = Canvas ? FMath::Max(Canvas->GetDPIScale(), 0.01f) : 1.0f;

	Layout.ViewWidth = FMath::Max(320.0f, static_cast<float>(CanvasViewRect.Width() > 0 ? CanvasViewRect.Width() : FallbackWidth) / DPIScale);
	Layout.ViewHeight = FMath::Max(240.0f, static_cast<float>(CanvasViewRect.Height() > 0 ? CanvasViewRect.Height() : FallbackHeight) / DPIScale);
	Layout.ViewMinX = CanvasViewRect.Min.X > 0 ? static_cast<float>(CanvasViewRect.Min.X) / DPIScale : 0.0f;
	Layout.ViewMinY = CanvasViewRect.Min.Y > 0 ? static_cast<float>(CanvasViewRect.Min.Y) / DPIScale : 0.0f;

	if (UGameViewportClient* GameViewportClient = ResolveProfilingGameViewport(ViewportClient))
	{
		if (GameViewportClient->Viewport)
		{
			const FIntPoint GameViewportSize = GameViewportClient->Viewport->GetSizeXY();
			if (GameViewportSize.X > 0 && GameViewportSize.Y > 0)
			{
				Layout.ViewMinX = 0.0f;
				Layout.ViewMinY = 0.0f;
				Layout.ViewWidth = FMath::Max(320.0f, static_cast<float>(GameViewportSize.X) / DPIScale);
				Layout.ViewHeight = FMath::Max(240.0f, static_cast<float>(GameViewportSize.Y) / DPIScale);
			}
		}

		if (TSharedPtr<SViewport> ViewportWidget = GameViewportClient->GetGameViewportWidget())
		{
			const FVector2D SlateViewportSize = ViewportWidget->GetCachedGeometry().GetLocalSize();
			if (SlateViewportSize.X >= 320.0f && SlateViewportSize.Y >= 120.0f)
			{
				Layout.ViewMinX = 0.0f;
				Layout.ViewMinY = 0.0f;
				Layout.ViewWidth = SlateViewportSize.X;
				Layout.ViewHeight = FMath::Max(240.0f, SlateViewportSize.Y);
			}
		}
	}

	return Layout;
}

static float GetCenteredProfilingCommandWidth(float ViewWidth)
{
	constexpr float OuterPadding = 10.0f;
	const float AvailableWidth = FMath::Max(1.0f, ViewWidth - OuterPadding * 2.0f);
	return FMath::Min(FMath::Clamp(AvailableWidth, 384.0f, 912.0f), FMath::Max(1.0f, ViewWidth));
}

static void SetCenteredProfilingCommandLayout(
	const FProfilingViewportLayout& Layout,
	float TopPadding,
	FVector2D& OutButtonPosition,
	FVector2D& OutButtonSize)
{
	constexpr float OuterPadding = 10.0f;
	const float ButtonWidth = GetCenteredProfilingCommandWidth(Layout.ViewWidth);
	const float ButtonX = Layout.ViewMinX + FMath::Max(0.0f, (Layout.ViewWidth - ButtonWidth) * 0.5f);
	const float ButtonY = Layout.ViewMinY + TopPadding;

	GProfilingSlateDrawPanel = false;
	GProfilingSlateButtonHeight = ProfilingCommandButtonHeight;
	GProfilingSlateButtonGap = ProfilingCommandButtonGap;
	GProfilingSlateOverlayLeft = FMath::Max(0.0f, ButtonX);
	GProfilingSlateOverlayTop = FMath::Max(0.0f, ButtonY);
	GProfilingSlateOverlayWidth = ButtonWidth;
	GProfilingSlateOverlayHeight = ProfilingCommandButtonHeight;
	GProfilingSlateViewportWidth = FMath::Max(Layout.ViewMinX + Layout.ViewWidth, ButtonX + ButtonWidth + OuterPadding);
	GProfilingSlateViewportHeight = FMath::Max(Layout.ViewMinY + Layout.ViewHeight, ButtonY + ProfilingCommandButtonHeight + OuterPadding);
	GProfilingCommandHitLeft = ButtonX;
	GProfilingCommandHitTop = ButtonY;
	GProfilingCommandHitWidth = ButtonWidth;
	GProfilingCommandHitHeight = ProfilingCommandButtonHeight;
	GProfilingCommandHitButtonGap = ProfilingCommandButtonGap;

	OutButtonPosition = FVector2D(ButtonX, ButtonY);
	OutButtonSize = FVector2D(ButtonWidth, ProfilingCommandButtonHeight);
}

static void UpdateProfilingCommandHitRectFromSlate()
{
	UGameViewportClient* GameViewportClient = GProfilingSlateOverlayViewport.Get();
	if (!GameViewportClient)
	{
		return;
	}

	TSharedPtr<SViewport> ViewportWidget = GameViewportClient->GetGameViewportWidget();
	if (!ViewportWidget.IsValid())
	{
		return;
	}

	const int32 ButtonCount = UE_ARRAY_COUNT(GProfilingCommandButtons);
	const float SingleButtonWidth = (GProfilingSlateOverlayWidth - ProfilingCommandButtonGap * static_cast<float>(ButtonCount - 1)) / static_cast<float>(ButtonCount);
	if (ButtonCount <= 0 || SingleButtonWidth <= 0.0f)
	{
		return;
	}

	const FGeometry& ViewportGeometry = ViewportWidget->GetCachedGeometry();
	const FVector2D AbsoluteTopLeft = ViewportGeometry.LocalToAbsolute(FVector2D(GProfilingSlateOverlayLeft, GProfilingSlateOverlayTop));
	const FVector2D AbsoluteBottomRight = ViewportGeometry.LocalToAbsolute(FVector2D(GProfilingSlateOverlayLeft + GProfilingSlateOverlayWidth, GProfilingSlateOverlayTop + GProfilingSlateOverlayHeight));
	const FVector2D AbsoluteButtonRight = ViewportGeometry.LocalToAbsolute(FVector2D(GProfilingSlateOverlayLeft + SingleButtonWidth, GProfilingSlateOverlayTop));
	const FVector2D AbsoluteSlotRight = ViewportGeometry.LocalToAbsolute(FVector2D(GProfilingSlateOverlayLeft + SingleButtonWidth + ProfilingCommandButtonGap, GProfilingSlateOverlayTop));
	GProfilingCommandHitLeft = AbsoluteTopLeft.X;
	GProfilingCommandHitTop = AbsoluteTopLeft.Y;
	GProfilingCommandHitWidth = FMath::Max(1.0f, AbsoluteBottomRight.X - AbsoluteTopLeft.X);
	GProfilingCommandHitHeight = FMath::Max(1.0f, AbsoluteBottomRight.Y - AbsoluteTopLeft.Y);
	GProfilingCommandHitButtonGap = FMath::Max(0.0f, AbsoluteSlotRight.X - AbsoluteButtonRight.X);
}

static FString GetProfilingButtonCommand(int32 ButtonIndex)
{
	if (ButtonIndex < 0 || ButtonIndex >= static_cast<int32>(UE_ARRAY_COUNT(GProfilingCommandButtons)))
	{
		return FString();
	}

	const FString DefaultCommand(GProfilingCommandButtons[ButtonIndex].Command);
	if (DefaultCommand.Equals(TEXT("stat mat start"), ESearchCase::IgnoreCase))
	{
		if (!GCaptureActive && IsMaterialCaptureCommandLocked())
		{
			return FString();
		}
		return GCaptureActive ? TEXT("stat mat end") : TEXT("stat mat start");
	}

	if (DefaultCommand.Equals(TEXT("stat obj"), ESearchCase::IgnoreCase))
	{
		return CVarObjectDebug.GetValueOnGameThread() != 0 ? TEXT("stat obj 0") : TEXT("stat obj");
	}

	return DefaultCommand;
}

static bool IsMaterialCaptureCommandLocked()
{
	return GMaterialCaptureEndGuardActive && FPlatformTime::Seconds() < GMaterialCaptureEndGuardReleaseSeconds;
}

static UWorld* FindCurrentPreviewWorld()
{
	if (GEngine && GEngine->GameViewport)
	{
		if (UWorld* World = GEngine->GameViewport->GetWorld())
		{
			return World;
		}
	}

#if WITH_EDITOR
	if (GEditor)
	{
		for (FEditorViewportClient* ViewportClient : GEditor->GetAllViewportClients())
		{
			if (ViewportClient && ViewportClient->GetWorld())
			{
				return ViewportClient->GetWorld();
			}
		}

		if (UWorld* World = GEditor->GetEditorWorldContext().World())
		{
			return World;
		}
	}
#endif

	return GWorld;
}

static bool GetMaterialCaptureCommandVerb(const FString& Command, FString& OutVerb)
{
	FString NormalizedCommand = Command;
	NormalizedCommand.TrimStartAndEndInline();

	const TCHAR* Cmd = *NormalizedCommand;
	if (!FParse::Command(&Cmd, TEXT("stat")))
	{
		return false;
	}
	if (!FParse::Command(&Cmd, *StatName) && !FParse::Command(&Cmd, *StatAliasName))
	{
		return false;
	}

	if (FParse::Command(&Cmd, TEXT("start")))
	{
		OutVerb = TEXT("start");
		return true;
	}
	if (FParse::Command(&Cmd, TEXT("end")))
	{
		OutVerb = TEXT("end");
		return true;
	}
	if (FParse::Command(&Cmd, TEXT("stop")))
	{
		OutVerb = TEXT("stop");
		return true;
	}

	return false;
}

static bool IsMaterialCaptureCommand(const FString& Command)
{
	FString Verb;
	return GetMaterialCaptureCommandVerb(Command, Verb);
}

static bool ShouldBlockMaterialCaptureCommand(const FString& Command)
{
	if (GCaptureActive || !GMaterialCaptureEndGuardActive)
	{
		return false;
	}

	FString Verb;
	if (!GetMaterialCaptureCommandVerb(Command, Verb))
	{
		return false;
	}

	if (FPlatformTime::Seconds() < GMaterialCaptureEndGuardReleaseSeconds)
	{
		return true;
	}

	return !Verb.Equals(TEXT("start"), ESearchCase::IgnoreCase);
}

static bool IsProfilingButtonEnabled(int32 ButtonIndex)
{
	if (ButtonIndex < 0 || ButtonIndex >= static_cast<int32>(UE_ARRAY_COUNT(GProfilingCommandButtons)))
	{
		return false;
	}

	const FString DefaultCommand(GProfilingCommandButtons[ButtonIndex].Command);
	return !DefaultCommand.Equals(TEXT("stat mat start"), ESearchCase::IgnoreCase)
		|| GCaptureActive
		|| !IsMaterialCaptureCommandLocked();
}

static FString GetProfilingButtonLabel(int32 ButtonIndex)
{
	if (ButtonIndex < 0 || ButtonIndex >= static_cast<int32>(UE_ARRAY_COUNT(GProfilingCommandButtons)))
	{
		return FString();
	}

	const FString DefaultCommand(GProfilingCommandButtons[ButtonIndex].Command);
	if (DefaultCommand.Equals(TEXT("stat mat start"), ESearchCase::IgnoreCase))
	{
		if (!GCaptureActive && IsMaterialCaptureCommandLocked())
		{
			return TEXT("GPU WAIT");
		}
		return GCaptureActive ? TEXT("GPU END") : TEXT("GPU START");
	}

	if (DefaultCommand.Equals(TEXT("stat matmode"), ESearchCase::IgnoreCase))
	{
		return IsMaterialDebugColorModeEnabled() ? TEXT("COLOR ON") : TEXT("COLOR OFF");
	}

	if (DefaultCommand.Equals(TEXT("stat mat replay"), ESearchCase::IgnoreCase))
	{
		return GMaterialReplayActive ? TEXT("GPU REPLAY OFF") : TEXT("GPU REPLAY");
	}

	if (DefaultCommand.Equals(TEXT("stat obj"), ESearchCase::IgnoreCase))
	{
		return CVarObjectDebug.GetValueOnGameThread() != 0 ? TEXT("OBJ OFF") : TEXT("OBJ SNAP");
	}

	return GProfilingCommandButtons[ButtonIndex].Label;
}

static bool TryGetProfilingCommandAtRectPosition(
	const FVector2D& Position,
	float RectLeft,
	float RectTop,
	float RectWidth,
	float RectHeight,
	float ButtonGap,
	FString& OutCommand)
{
	const int32 ButtonCount = UE_ARRAY_COUNT(GProfilingCommandButtons);
	if (ButtonCount <= 0
		|| Position.Y < RectTop
		|| Position.Y > RectTop + RectHeight
		|| Position.X < RectLeft
		|| Position.X > RectLeft + RectWidth)
	{
		return false;
	}

	const float LocalX = Position.X - RectLeft;
	const float ButtonWidth = (RectWidth - ButtonGap * static_cast<float>(ButtonCount - 1)) / static_cast<float>(ButtonCount);
	if (ButtonWidth <= 0.0f)
	{
		return false;
	}

	for (int32 ButtonIndex = 0; ButtonIndex < ButtonCount; ++ButtonIndex)
	{
		const float ButtonLeft = static_cast<float>(ButtonIndex) * (ButtonWidth + ButtonGap);
		if (LocalX >= ButtonLeft && LocalX <= ButtonLeft + ButtonWidth)
		{
			OutCommand = GetProfilingButtonCommand(ButtonIndex);
			return true;
		}
	}

	return false;
}

static bool TryGetProfilingCommandAtLocalPosition(const FVector2D& LocalPosition, FString& OutCommand)
{
	if (TryGetProfilingCommandAtRectPosition(
		LocalPosition,
		GProfilingCommandHitLeft,
		GProfilingCommandHitTop,
		GProfilingCommandHitWidth,
		GProfilingCommandHitHeight,
		GProfilingCommandHitButtonGap,
		OutCommand))
	{
		return true;
	}

	if (!GProfilingSlateDrawPanel
		&& TryGetProfilingCommandAtRectPosition(
			LocalPosition,
			GProfilingSlateOverlayLeft,
			GProfilingSlateOverlayTop,
			GProfilingSlateOverlayWidth,
			GProfilingSlateOverlayHeight,
			GProfilingSlateButtonGap,
			OutCommand))
	{
		return true;
	}

	float ScaleCandidates[] =
	{
		FSlateApplication::IsInitialized() ? FMath::Max(FSlateApplication::Get().GetApplicationScale(), 0.01f) : 1.0f,
		1.25f,
		1.5f,
		1.75f,
		2.0f
	};
	for (const float DPIScale : ScaleCandidates)
	{
		if (!FMath::IsNearlyEqual(DPIScale, 1.0f)
			&& TryGetProfilingCommandAtRectPosition(
				LocalPosition * DPIScale,
				GProfilingCommandHitLeft,
				GProfilingCommandHitTop,
				GProfilingCommandHitWidth,
				GProfilingCommandHitHeight,
				GProfilingCommandHitButtonGap,
				OutCommand))
		{
			return true;
		}
	}

	return false;
}

static bool TryGetProfilingCommandAtWidgetPosition(const FVector2D& ScreenPosition, FString& OutCommand)
{
	const int32 ButtonCount = FMath::Min(GProfilingSlateButtonWidgets.Num(), static_cast<int32>(UE_ARRAY_COUNT(GProfilingCommandButtons)));
	for (int32 ButtonIndex = 0; ButtonIndex < ButtonCount; ++ButtonIndex)
	{
		FInputScreenRect ButtonRect;
		if (SetInputScreenRectFromWidget(GProfilingSlateButtonWidgets[ButtonIndex], 2.0f, 4.0f, ButtonRect)
			&& ButtonRect.Contains(ScreenPosition))
		{
			OutCommand = GetProfilingButtonCommand(ButtonIndex);
			return true;
		}
	}

	return false;
}

static bool TryGetProfilingCommandUnderCursor(UGameViewportClient* GameViewportClient, FString& OutCommand)
{
	if (!GameViewportClient || !FSlateApplication::IsInitialized())
	{
		return false;
	}

	const FVector2D CursorPosition = FSlateApplication::Get().GetCursorPos();
	return TryGetProfilingCommandAtWidgetPosition(CursorPosition, OutCommand)
		|| TryGetProfilingCommandAtLocalPosition(CursorPosition, OutCommand);
}

static void KeepProfilingCommandsVisibleAfterButtonCommand(const FString& Command);

static void ExecuteProfilingCommand(const FString& Command)
{
	if (Command.IsEmpty())
	{
		return;
	}
	if (ShouldBlockMaterialCaptureCommand(Command))
	{
		UE_LOG(LogOptimizationPreviewTools, Verbose, TEXT("Material GPU Preview capture command ignored during post-end guard: %s"), *Command);
		return;
	}

	UWorld* World = nullptr;
	if (UGameViewportClient* GameViewportClient = GProfilingSlateOverlayViewport.Get())
	{
		World = GameViewportClient->GetWorld();
	}

	if (!World)
	{
		World = GWorld;
	}

#if WITH_EDITOR
	if (!World && GEditor)
	{
		World = GEditor->GetEditorWorldContext().World();
	}
#endif

	if (GEngine)
	{
		GEngine->Exec(World, *Command);
		KeepProfilingCommandsVisibleAfterButtonCommand(Command);
	}
}

static FReply ExecuteProfilingSlateCommand(const FString Command)
{
	ExecuteProfilingCommand(Command);

	return FReply::Handled();
}

static bool TryExecuteProfilingCommandAtScreenPosition(const FVector2D& ScreenPosition)
{
	if (!GProfilingSlateOverlayWidget.IsValid())
	{
		return false;
	}

	FString Command;
	if (!TryGetProfilingCommandAtWidgetPosition(ScreenPosition, Command)
		&& !TryGetProfilingCommandAtLocalPosition(ScreenPosition, Command))
	{
		return false;
	}

	ExecuteProfilingCommand(Command);
	return true;
}

class FProfilingCommandInputProcessor final : public IInputProcessor
{
public:
	virtual void Tick(const float DeltaTime, FSlateApplication& SlateApp, TSharedRef<ICursor> Cursor) override
	{
	}

	virtual bool HandleMouseMoveEvent(FSlateApplication& SlateApp, const FPointerEvent& MouseEvent) override
	{
		return TryHandleMaterialReplayPointerMove(MouseEvent);
	}

	virtual bool HandleMouseButtonDownEvent(FSlateApplication& SlateApp, const FPointerEvent& MouseEvent) override
	{
		if (!MouseEvent.IsTouchEvent() && MouseEvent.GetEffectingButton() != EKeys::LeftMouseButton)
		{
			return false;
		}

		if (TryExecuteProfilingCommandAtScreenPosition(MouseEvent.GetScreenSpacePosition()))
		{
			return true;
		}

		return TryHandleMaterialReplayPointerDown(MouseEvent);
	}

	virtual bool HandleMouseButtonUpEvent(FSlateApplication& SlateApp, const FPointerEvent& MouseEvent) override
	{
		return TryHandleMaterialReplayPointerUp(MouseEvent);
	}

	virtual const TCHAR* GetDebugName() const override
	{
		return TEXT("OptimizationPreviewToolsProfilingCommands");
	}
};

static void RemoveProfilingInputProcessor()
{
	if (GProfilingCommandInputProcessor.IsValid() && FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().UnregisterInputPreProcessor(GProfilingCommandInputProcessor);
	}

	GProfilingCommandInputProcessor.Reset();
}

static void InstallProfilingInputProcessor()
{
	if (!FSlateApplication::IsInitialized())
	{
		return;
	}

	if (!GProfilingCommandInputProcessor.IsValid())
	{
		GProfilingCommandInputProcessor = MakeShared<FProfilingCommandInputProcessor>();
		FSlateApplication::Get().RegisterInputPreProcessor(GProfilingCommandInputProcessor);
	}
}

static bool HandleProfilingOverrideInputKey(FInputKeyEventArgs& EventArgs)
{
	UGameViewportClient* GameViewportClient = GProfilingInputOverrideViewport.Get();
	if (GProfilingSlateOverlayWidget.IsValid()
		&& GameViewportClient
		&& EventArgs.Event == IE_Pressed
		&& (EventArgs.Key == EKeys::LeftMouseButton || EventArgs.Key.IsTouch()))
	{
		FString Command;
		if (TryGetProfilingCommandUnderCursor(GameViewportClient, Command))
		{
			ExecuteProfilingCommand(Command);
			return true;
		}
	}

	return GHadPreviousProfilingInputOverride && GPreviousProfilingInputOverride.IsBound()
		? GPreviousProfilingInputOverride.Execute(EventArgs)
		: false;
}

static void RemoveProfilingInputOverride()
{
	if (UGameViewportClient* GameViewportClient = GProfilingInputOverrideViewport.Get())
	{
		FOverrideInputKeyHandler& OverrideInputKey = GameViewportClient->OnOverrideInputKey();
		if (!GProfilingInputOverrideHandle.IsValid() || OverrideInputKey.GetHandle() == GProfilingInputOverrideHandle)
		{
			if (GHadPreviousProfilingInputOverride)
			{
				OverrideInputKey = GPreviousProfilingInputOverride;
			}
			else
			{
				OverrideInputKey.Unbind();
			}
		}
	}

	GProfilingInputOverrideViewport = nullptr;
	GPreviousProfilingInputOverride.Unbind();
	GProfilingInputOverrideHandle.Reset();
	GHadPreviousProfilingInputOverride = false;
}

static void InstallProfilingInputOverride(UGameViewportClient* GameViewportClient)
{
	if (!GameViewportClient || GProfilingInputOverrideViewport.Get() == GameViewportClient)
	{
		return;
	}

	RemoveProfilingInputOverride();

	FOverrideInputKeyHandler& OverrideInputKey = GameViewportClient->OnOverrideInputKey();
	GPreviousProfilingInputOverride = OverrideInputKey;
	GHadPreviousProfilingInputOverride = GPreviousProfilingInputOverride.IsBound();
	GProfilingInputOverrideViewport = GameViewportClient;
	OverrideInputKey.BindStatic(&HandleProfilingOverrideInputKey);
	GProfilingInputOverrideHandle = OverrideInputKey.GetHandle();
}

static TSharedRef<SWidget> MakeProfilingSlateButton(int32 ButtonIndex)
{
	TSharedPtr<SBox> ButtonBox;
	TSharedRef<SWidget> ButtonWidget = SAssignNew(ButtonBox, SBox)
		.HeightOverride(TAttribute<FOptionalSize>::CreateLambda([]()
		{
			return FOptionalSize(GProfilingSlateButtonHeight);
		}))
		[
			SNew(SBorder)
			.Padding(1.0f)
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(FLinearColor(0.54f, 0.56f, 0.55f, 0.70f))
			[
				SNew(SBorder)
				.Padding(0.0f)
				.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
				.BorderBackgroundColor(FLinearColor(0.055f, 0.058f, 0.062f, 0.96f))
				[
					SNew(SButton)
					.ButtonStyle(&FCoreStyle::Get().GetWidgetStyle<FButtonStyle>("NoBorder"))
					.ContentPadding(FMargin(12.0f, 0.0f))
					.HAlign(HAlign_Center)
					.VAlign(VAlign_Center)
					.ClickMethod(EButtonClickMethod::MouseDown)
					.TouchMethod(EButtonTouchMethod::Down)
					.IsFocusable(false)
					.IsEnabled(TAttribute<bool>::CreateLambda([ButtonIndex]()
					{
						return IsProfilingButtonEnabled(ButtonIndex);
					}))
					.OnClicked_Lambda([ButtonIndex]()
					{
						return ExecuteProfilingSlateCommand(GetProfilingButtonCommand(ButtonIndex));
					})
					[
						SNew(STextBlock)
						.Text(TAttribute<FText>::CreateLambda([ButtonIndex]()
						{
							return FText::FromString(GetProfilingButtonLabel(ButtonIndex));
						}))
						.ColorAndOpacity(FSlateColor(FLinearColor(0.94f, 0.94f, 0.90f, 1.0f)))
						.Justification(ETextJustify::Center)
					]
				]
			]
		];

	if (GProfilingSlateButtonWidgets.IsValidIndex(ButtonIndex))
	{
		GProfilingSlateButtonWidgets[ButtonIndex] = ButtonBox;
	}

	return ButtonWidget;
}

static TSharedRef<SWidget> MakeProfilingSlateButtonRow()
{
	const int32 ButtonCount = UE_ARRAY_COUNT(GProfilingCommandButtons);
	GProfilingSlateButtonWidgets.SetNum(ButtonCount);
	TSharedRef<SHorizontalBox> ButtonRow = SNew(SHorizontalBox);
	for (int32 ButtonIndex = 0; ButtonIndex < ButtonCount; ++ButtonIndex)
	{
		const bool bHasLeftGap = ButtonIndex > 0;
		ButtonRow->AddSlot()
		.FillWidth(1.0f)
		.Padding(TAttribute<FMargin>::CreateLambda([bHasLeftGap]()
		{
			return FMargin(bHasLeftGap ? GProfilingSlateButtonGap : 0.0f, 0.0f, 0.0f, 0.0f);
		}))
		[
			MakeProfilingSlateButton(ButtonIndex)
		];
	}

	return StaticCastSharedRef<SWidget>(ButtonRow);
}

class SProfilingRecordingIndicator final : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SProfilingRecordingIndicator) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs)
	{
		SetCanTick(false);
	}

	virtual FVector2D ComputeDesiredSize(float LayoutScaleMultiplier) const override
	{
		return FVector2D(384.0f, 102.0f);
	}

	virtual bool ComputeVolatility() const override
	{
		return GCaptureActive;
	}

	virtual int32 OnPaint(
		const FPaintArgs& Args,
		const FGeometry& AllottedGeometry,
		const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements,
		int32 LayerId,
		const FWidgetStyle& InWidgetStyle,
		bool bParentEnabled) const override
	{
		if (!GCaptureActive)
		{
			return LayerId;
		}

		const bool bEnabled = ShouldBeEnabled(bParentEnabled);
		const ESlateDrawEffect DrawEffects = bEnabled ? ESlateDrawEffect::None : ESlateDrawEffect::DisabledEffect;
		const FSlateBrush* WhiteBrush = FCoreStyle::Get().GetBrush("WhiteBrush");
		const FLinearColor Tint = InWidgetStyle.GetColorAndOpacityTint();
		const FVector2D Size = AllottedGeometry.GetLocalSize();
		const double TimeSeconds = FSlateApplication::IsInitialized() ? FSlateApplication::Get().GetCurrentTime() : FPlatformTime::Seconds();
		const float Pulse = 0.5f + 0.5f * FMath::Sin(static_cast<float>(TimeSeconds) * 6.0f);
		const float TextPulse = 0.5f + 0.5f * FMath::Sin(static_cast<float>(TimeSeconds) * 14.0f);
		const float FlickerStep = FMath::Fmod(FMath::FloorToFloat(static_cast<float>(TimeSeconds) * 17.0f) * 0.37f, 1.0f);
		const float TextOpacity = FMath::Clamp(0.58f + TextPulse * 0.30f + (FlickerStep > 0.78f ? 0.12f : -0.08f), 0.42f, 1.0f);
		const float Sweep = FMath::Fmod(static_cast<float>(TimeSeconds) * 1.25f, 1.0f);
		const FVector2D Center(51.0f, Size.Y * 0.5f);
		constexpr float Radius = 33.0f;

		FSlateDrawElement::MakeBox(
			OutDrawElements,
			LayerId,
			AllottedGeometry.ToPaintGeometry(),
			WhiteBrush,
			DrawEffects,
			FLinearColor(0.035f, 0.006f, 0.006f, 0.76f) * Tint);

		for (int32 SegmentIndex = 0; SegmentIndex < 32; ++SegmentIndex)
		{
			const float SegmentAlpha = static_cast<float>(SegmentIndex) / 32.0f;
			const float WrappedAlpha = FMath::Fmod(SegmentAlpha - Sweep + 1.0f, 1.0f);
			const float SegmentOpacity = FMath::Clamp(1.0f - WrappedAlpha * 1.35f, 0.08f, 1.0f);
			const float Angle = SegmentAlpha * UE_TWO_PI;
			const FVector2D Direction(FMath::Cos(Angle), FMath::Sin(Angle));
			const FVector2D Start = Center + Direction * (Radius - 7.5f);
			const FVector2D End = Center + Direction * (Radius + 7.5f);

			TArray<FVector2D> SegmentLine;
			SegmentLine.Add(Start);
			SegmentLine.Add(End);
			FSlateDrawElement::MakeLines(
				OutDrawElements,
				LayerId + 1,
				AllottedGeometry.ToPaintGeometry(),
				SegmentLine,
				DrawEffects,
				FLinearColor(1.0f, 0.02f, 0.02f, SegmentOpacity) * Tint,
				true,
				6.6f);
		}

		const float CoreSize = FMath::Lerp(15.0f, 22.5f, Pulse);
		FSlateDrawElement::MakeBox(
			OutDrawElements,
			LayerId + 2,
			AllottedGeometry.ToPaintGeometry(FVector2D(CoreSize, CoreSize), FSlateLayoutTransform(Center - FVector2D(CoreSize * 0.5f))),
			WhiteBrush,
			DrawEffects,
			FLinearColor(1.0f, 0.0f, 0.0f, FMath::Lerp(0.55f, 0.95f, Pulse)) * Tint);

		FSlateDrawElement::MakeText(
			OutDrawElements,
			LayerId + 3,
			AllottedGeometry.ToPaintGeometry(FVector2D(250.0f, 62.0f), FSlateLayoutTransform(FVector2D(108.0f, 20.0f))),
			FText::FromString(TEXT("REC...")),
			FCoreStyle::GetDefaultFontStyle("Bold", 40),
			DrawEffects,
			FLinearColor(1.0f, 0.03f, 0.03f, TextOpacity) * Tint);

		return LayerId + 4;
	}
};

static TSharedRef<SWidget> BuildProfilingSlateOverlay()
{
	return SNew(SOverlay)
		.Visibility(EVisibility::SelfHitTestInvisible)
		+ SOverlay::Slot()
		.HAlign(HAlign_Left)
		.VAlign(VAlign_Top)
		.Padding(TAttribute<FMargin>::CreateLambda([]()
		{
			return FMargin(GProfilingSlateOverlayLeft, GProfilingSlateOverlayTop, 0.0f, 0.0f);
		}))
		[
			SNew(SBox)
			.Visibility(TAttribute<EVisibility>::CreateLambda([]()
			{
				return GProfilingSlateDrawPanel ? EVisibility::SelfHitTestInvisible : EVisibility::Collapsed;
			}))
			.WidthOverride(TAttribute<FOptionalSize>::CreateLambda([]()
			{
				return FOptionalSize(FMath::Max(240.0f, GProfilingSlateOverlayWidth));
			}))
			.HeightOverride(TAttribute<FOptionalSize>::CreateLambda([]()
			{
				return FOptionalSize(GProfilingSlateOverlayHeight);
			}))
			[
				SNew(SBorder)
				.Padding(0.0f)
				.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
				.BorderBackgroundColor(FLinearColor(0.025f, 0.026f, 0.028f, 0.78f))
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(18.0f, 8.0f, 18.0f, 0.0f))
					[
						SNew(STextBlock)
						.Text(FText::FromString(TEXT("OPTIMIZATION PROFILING")))
						.ColorAndOpacity(FSlateColor(FLinearColor(0.95f, 0.95f, 0.92f, 1.0f)))
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(18.0f, 2.0f, 18.0f, 0.0f))
					[
						SNew(STextBlock)
						.Text(FText::FromString(TEXT("Plugin Commands")))
						.ColorAndOpacity(FSlateColor(FLinearColor(0.62f, 0.72f, 0.82f, 1.0f)))
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(0.0f, 30.0f, 0.0f, 0.0f))
					[
						SNew(SBorder)
						.Padding(0.0f)
						.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
						.BorderBackgroundColor(FLinearColor(0.46f, 0.46f, 0.43f, 0.55f))
						[
							SNew(SBox)
							.HeightOverride(1.0f)
						]
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(18.0f, 10.0f, 18.0f, 0.0f))
					[
						MakeProfilingSlateButtonRow()
					]
					+ SVerticalBox::Slot()
					.FillHeight(1.0f)
					[
						SNew(SSpacer)
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(FMargin(18.0f, 0.0f, 18.0f, 10.0f))
					[
						SNew(STextBlock)
						.Text(FText::FromString(TEXT("Commands: stat mat start/end/replay/0 | stat matmode 0/1 | stat obj/0")))
						.ColorAndOpacity(FSlateColor(FLinearColor(0.50f, 0.58f, 0.64f, 0.95f)))
					]
				]
			]
		]
		+ SOverlay::Slot()
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Top)
		.Padding(TAttribute<FMargin>::CreateLambda([]()
		{
			return FMargin(0.0f, GProfilingSlateOverlayTop, 0.0f, 0.0f);
		}))
		[
			SNew(SBox)
			.Visibility(TAttribute<EVisibility>::CreateLambda([]()
			{
				return GProfilingSlateDrawPanel ? EVisibility::Collapsed : EVisibility::SelfHitTestInvisible;
			}))
			.WidthOverride(TAttribute<FOptionalSize>::CreateLambda([]()
			{
				return FOptionalSize(FMath::Max(240.0f, GProfilingSlateOverlayWidth));
			}))
			.HeightOverride(TAttribute<FOptionalSize>::CreateLambda([]()
			{
				return FOptionalSize(GProfilingSlateOverlayHeight);
			}))
			[
				MakeProfilingSlateButtonRow()
			]
		]
		+ SOverlay::Slot()
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Center)
		[
			SNew(SBox)
			.Visibility(TAttribute<EVisibility>::CreateLambda([]()
			{
				return GCaptureActive ? EVisibility::HitTestInvisible : EVisibility::Collapsed;
			}))
			.WidthOverride(384.0f)
			.HeightOverride(102.0f)
			[
				SNew(SProfilingRecordingIndicator)
			]
		];
}

static void RemoveProfilingSlateOverlay()
{
	RemoveProfilingInputOverride();

	if (GProfilingSlateOverlayWidget.IsValid())
	{
		if (UGameViewportClient* GameViewportClient = GProfilingSlateOverlayViewport.Get())
		{
			GameViewportClient->RemoveViewportWidgetContent(GProfilingSlateOverlayWidget.ToSharedRef());
			UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Optimization Profiling Slate command overlay removed."));
		}
	}

	GProfilingSlateOverlayWidget.Reset();
	GProfilingSlateButtonWidgets.Reset();
	GProfilingSlateOverlayViewport = nullptr;
}

static void RecordProfilingSlateOverlayLayout()
{
	GLastProfilingSlateDrawPanel = GProfilingSlateDrawPanel;
	GLastProfilingSlateOverlayLeft = GProfilingSlateOverlayLeft;
	GLastProfilingSlateOverlayTop = GProfilingSlateOverlayTop;
	GLastProfilingSlateOverlayWidth = GProfilingSlateOverlayWidth;
	GLastProfilingSlateOverlayHeight = GProfilingSlateOverlayHeight;
}

static bool HasProfilingSlateOverlayLayoutChanged()
{
	return GLastProfilingSlateDrawPanel != GProfilingSlateDrawPanel
		|| !FMath::IsNearlyEqual(GLastProfilingSlateOverlayLeft, GProfilingSlateOverlayLeft, 0.5f)
		|| !FMath::IsNearlyEqual(GLastProfilingSlateOverlayTop, GProfilingSlateOverlayTop, 0.5f)
		|| !FMath::IsNearlyEqual(GLastProfilingSlateOverlayWidth, GProfilingSlateOverlayWidth, 0.5f)
		|| !FMath::IsNearlyEqual(GLastProfilingSlateOverlayHeight, GProfilingSlateOverlayHeight, 0.5f);
}

static void RefreshProfilingSlateOverlayIfLayoutChanged()
{
	UGameViewportClient* GameViewportClient = GProfilingSlateOverlayViewport.Get();
	if (!GameViewportClient || !GProfilingSlateOverlayWidget.IsValid() || !HasProfilingSlateOverlayLayoutChanged())
	{
		return;
	}

	GameViewportClient->RemoveViewportWidgetContent(GProfilingSlateOverlayWidget.ToSharedRef());
	GProfilingSlateOverlayWidget = BuildProfilingSlateOverlay();
	GameViewportClient->AddViewportWidgetContent(GProfilingSlateOverlayWidget.ToSharedRef(), 1000);
	RecordProfilingSlateOverlayLayout();
}

static void EnsureProfilingSlateOverlay(FCommonViewportClient* ViewportClient)
{
	UGameViewportClient* GameViewportClient = ResolveProfilingGameViewport(ViewportClient);
	if (!GameViewportClient)
	{
		RemoveProfilingSlateOverlay();
		return;
	}

	if (GProfilingSlateOverlayWidget.IsValid() && GProfilingSlateOverlayViewport.Get() == GameViewportClient)
	{
		InstallProfilingInputProcessor();
		InstallProfilingInputOverride(GameViewportClient);
		return;
	}

	RemoveProfilingSlateOverlay();
	GProfilingSlateOverlayViewport = GameViewportClient;
	GProfilingSlateOverlayWidget = BuildProfilingSlateOverlay();
	GameViewportClient->AddViewportWidgetContent(GProfilingSlateOverlayWidget.ToSharedRef(), 1000);
	RecordProfilingSlateOverlayLayout();
	InstallProfilingInputProcessor();
	InstallProfilingInputOverride(GameViewportClient);
	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Optimization Profiling Slate command overlay added."));
}

static void DisableActorColoration(UWorld* World, FCommonViewportClient* ViewportClient);

static void RefreshActorColorationViewports(FCommonViewportClient* ViewportClient)
{
	if (UGameViewportClient* GameViewportClient = FindGameViewportClient(ViewportClient))
	{
		if (GameViewportClient->Viewport)
		{
			GameViewportClient->Viewport->InvalidateDisplay();
			GameViewportClient->Viewport->Invalidate();
		}
	}

#if WITH_EDITOR
	if (FEditorViewportClient* EditorViewportClient = FindEditorViewportClient(ViewportClient))
	{
		if (EditorViewportClient->Viewport)
		{
			EditorViewportClient->Viewport->InvalidateDisplay();
			EditorViewportClient->Viewport->Invalidate();
		}
	}

	if (GEditor)
	{
		GEditor->RedrawAllViewports();
	}
#endif
}

static void ApplyActorColorationViewModeFromCurrentColors(UWorld* World, FCommonViewportClient* ViewportClient)
{
#if !(UE_BUILD_SHIPPING || UE_BUILD_TEST)
	if (!World || !ShouldUseActorColorationBackend())
	{
		return;
	}

	RegisterActorColorationHandler();
	if (GActorColorationColors.Num() == 0 && !GMaterialReplayActive)
	{
		DisableActorColoration(World, ViewportClient);
		return;
	}

	const bool bChangedHandler = FActorPrimitiveColorHandler::Get().SetActivePrimitiveColorHandler(ActorColorationHandlerName, World);
	if (!bChangedHandler)
	{
		FActorPrimitiveColorHandler::Get().RefreshPrimitiveColorHandler(ActorColorationHandlerName, World);
	}

	if (UGameViewportClient* GameViewportClient = FindGameViewportClient(ViewportClient))
	{
		if (!GHasPreviousGameViewMode)
		{
			GPreviousGameViewMode = GameViewportClient->ViewModeIndex;
			GHasPreviousGameViewMode = true;
			GActorColorationGameViewport = GameViewportClient;
		}
		GameViewportClient->SetViewMode(VMI_VisualizeActorColoration);
	}

#if WITH_EDITOR
	if (FEditorViewportClient* EditorViewportClient = FindEditorViewportClient(ViewportClient))
	{
		if (!GPreviousEditorViewModes.Contains(EditorViewportClient))
		{
			GPreviousEditorViewModes.Add(EditorViewportClient, EditorViewportClient->GetViewMode());
		}
		EditorViewportClient->SetViewMode(VMI_VisualizeActorColoration);
	}
#endif

	GActorColorationActive = true;
	GActorColorationWorld = World;
	ClearCachedDebugOverlay(World);
	RefreshActorColorationViewports(ViewportClient);
#endif
}

static void ApplyActorColorationViewMode(UWorld* World, FCommonViewportClient* ViewportClient)
{
#if !(UE_BUILD_SHIPPING || UE_BUILD_TEST)
	RebuildActorColorationColorMap();
	ApplyActorColorationViewModeFromCurrentColors(World, ViewportClient);
#endif
}

static void DisableActorColoration(UWorld* World, FCommonViewportClient* ViewportClient)
{
#if !(UE_BUILD_SHIPPING || UE_BUILD_TEST)
	RestoreMaterialDebugMaterialOverrides();

	UWorld* TargetWorld = World ? World : GActorColorationWorld.Get();
	if (!TargetWorld)
	{
		TargetWorld = GWorld;
	}

	GActorColorationColors.Reset();

	const bool bOurActorColorationHandlerActive = GActorColorationHandlerRegistered
		&& FActorPrimitiveColorHandler::Get().GetActivePrimitiveColorHandler() == ActorColorationHandlerName;
	if ((GActorColorationActive || bOurActorColorationHandlerActive) && TargetWorld)
	{
		FActorPrimitiveColorHandler::Get().SetActivePrimitiveColorHandler(NAME_None, TargetWorld);
	}

	if ((!ViewportClient || FindGameViewportClient(ViewportClient)) && GHasPreviousGameViewMode)
	{
		UGameViewportClient* GameViewportClient = FindGameViewportClient(ViewportClient);
		if (!GameViewportClient)
		{
			GameViewportClient = GActorColorationGameViewport.Get();
		}
		if (!GameViewportClient && GEngine)
		{
			GameViewportClient = GEngine->GameViewport;
		}
		if (GameViewportClient)
		{
			GameViewportClient->SetViewMode(static_cast<EViewModeIndex>(GPreviousGameViewMode));
		}
		GHasPreviousGameViewMode = false;
		GActorColorationGameViewport = nullptr;
	}

#if WITH_EDITOR
	if (ViewportClient)
	{
		if (FEditorViewportClient* EditorViewportClient = FindEditorViewportClient(ViewportClient))
		{
			if (EViewModeIndex* PreviousViewMode = GPreviousEditorViewModes.Find(EditorViewportClient))
			{
				EditorViewportClient->SetViewMode(*PreviousViewMode);
				GPreviousEditorViewModes.Remove(EditorViewportClient);
			}
		}
	}
	else
	{
		for (const TPair<FEditorViewportClient*, EViewModeIndex>& PreviousViewModePair : GPreviousEditorViewModes)
		{
			if (PreviousViewModePair.Key)
			{
				PreviousViewModePair.Key->SetViewMode(PreviousViewModePair.Value);
			}
		}
		GPreviousEditorViewModes.Reset();
	}
#endif

	GActorColorationActive = false;
	GActorColorationWorld = nullptr;
	RefreshActorColorationViewports(ViewportClient);
#endif
}

static const TCHAR* GetBlendModeShortName(EBlendMode BlendMode)
{
	switch (BlendMode)
	{
	case BLEND_Opaque:
		return TEXT("Opaq");
	case BLEND_Masked:
		return TEXT("Mask");
	case BLEND_Translucent:
		return TEXT("Trans");
	case BLEND_Additive:
		return TEXT("Add");
	case BLEND_Modulate:
		return TEXT("Mod");
	case BLEND_AlphaComposite:
		return TEXT("Alpha");
	case BLEND_AlphaHoldout:
		return TEXT("Hold");
	default:
		return TEXT("Other");
	}
}

static bool IsNamedViewportStatEnabled(FCommonViewportClient* ViewportClient, const FString& InStatName)
{
	return ViewportClient && ViewportClient->IsStatEnabled(InStatName);
}

static FString NormalizeViewportStatName(const FString& InStatName)
{
	FString StatNameToCheck = InStatName;
	StatNameToCheck.TrimStartAndEndInline();
	if (StatNameToCheck.StartsWith(TEXT("STAT_"), ESearchCase::IgnoreCase))
	{
		StatNameToCheck = StatNameToCheck.RightChop(5);
	}

	return StatNameToCheck;
}

static bool IsAuxiliaryViewportStatName(const FString& InStatName)
{
	const FString StatNameToCheck = NormalizeViewportStatName(InStatName);
	return StatNameToCheck.Equals(TEXT("fps"), ESearchCase::IgnoreCase)
		|| StatNameToCheck.Equals(TEXT("unit"), ESearchCase::IgnoreCase)
		|| StatNameToCheck.Equals(TEXT("unitgraph"), ESearchCase::IgnoreCase);
}

static bool IsPluginViewportStatName(const FString& InStatName)
{
	const FString StatNameToCheck = NormalizeViewportStatName(InStatName);
	return StatNameToCheck.Equals(StatName, ESearchCase::IgnoreCase)
		|| StatNameToCheck.Equals(StatAliasName, ESearchCase::IgnoreCase)
		|| StatNameToCheck.Equals(MaterialModeStatName, ESearchCase::IgnoreCase)
		|| StatNameToCheck.Equals(ObjectStatName, ESearchCase::IgnoreCase)
		|| StatNameToCheck.Equals(ProfilingStatName, ESearchCase::IgnoreCase);
}

static bool HasConflictingExternalViewportStat(FCommonViewportClient* ViewportClient)
{
	if (!ViewportClient)
	{
		return false;
	}

	const TArray<FString>* EnabledStats = ViewportClient->GetEnabledStats();
	if (!EnabledStats)
	{
		return false;
	}

	for (const FString& EnabledStat : *EnabledStats)
	{
		if (!EnabledStat.IsEmpty()
			&& !IsAuxiliaryViewportStatName(EnabledStat)
			&& !IsPluginViewportStatName(EnabledStat))
		{
			return true;
		}
	}

	return false;
}

static void RemoveConflictingExternalViewportStats(FCommonViewportClient* ViewportClient)
{
	if (!ViewportClient)
	{
		return;
	}

	const TArray<FString>* EnabledStats = ViewportClient->GetEnabledStats();
	if (!EnabledStats)
	{
		return;
	}

	TArray<FString> NewStats;
	NewStats.Reserve(EnabledStats->Num());
	bool bChanged = false;
	for (const FString& EnabledStat : *EnabledStats)
	{
		if (EnabledStat.IsEmpty()
			|| IsAuxiliaryViewportStatName(EnabledStat)
			|| IsPluginViewportStatName(EnabledStat))
		{
			NewStats.Add(EnabledStat);
		}
		else
		{
			bChanged = true;
		}
	}

	if (bChanged)
	{
		ViewportClient->SetEnabledStats(NewStats);
	}
}

static bool IsViewportStatEnabled(FCommonViewportClient* ViewportClient)
{
	return IsNamedViewportStatEnabled(ViewportClient, StatName) || IsNamedViewportStatEnabled(ViewportClient, StatAliasName);
}

static bool IsObjectViewportStatEnabled(FCommonViewportClient* ViewportClient)
{
	return IsNamedViewportStatEnabled(ViewportClient, ObjectStatName);
}

static bool IsProfilingViewportStatEnabled(FCommonViewportClient* ViewportClient)
{
	return IsNamedViewportStatEnabled(ViewportClient, ProfilingStatName);
}

static void SetNamedViewportStatEnabled(FCommonViewportClient* ViewportClient, const FString& InStatName, bool bEnable)
{
	if (!ViewportClient)
	{
		return;
	}

	const TArray<FString>* EnabledStats = ViewportClient->GetEnabledStats();
	if (!EnabledStats)
	{
		return;
	}

	TArray<FString> NewStats = *EnabledStats;
	const bool bCurrentlyEnabled = NewStats.Contains(InStatName);
	if (bEnable == bCurrentlyEnabled)
	{
		return;
	}

	if (bEnable)
	{
		NewStats.AddUnique(InStatName);
	}
	else
	{
		NewStats.Remove(InStatName);
	}

	ViewportClient->SetEnabledStats(NewStats);
}

static void SetViewportStatEnabled(FCommonViewportClient* ViewportClient, bool bEnable)
{
	if (bEnable)
	{
		RemoveConflictingExternalViewportStats(ViewportClient);
		SetNamedViewportStatEnabled(ViewportClient, ObjectStatName, false);
	}

	SetNamedViewportStatEnabled(ViewportClient, StatAliasName, false);
	SetNamedViewportStatEnabled(ViewportClient, StatName, bEnable);
}

static void SetObjectViewportStatEnabled(FCommonViewportClient* ViewportClient, bool bEnable)
{
	if (bEnable)
	{
		RemoveConflictingExternalViewportStats(ViewportClient);
		SetNamedViewportStatEnabled(ViewportClient, StatName, false);
		SetNamedViewportStatEnabled(ViewportClient, StatAliasName, false);
	}

	SetNamedViewportStatEnabled(ViewportClient, ObjectStatName, bEnable);
}

static void SetProfilingViewportStatEnabled(FCommonViewportClient* ViewportClient, bool bEnable)
{
	if (bEnable)
	{
		RemoveConflictingExternalViewportStats(ViewportClient);
	}

	SetNamedViewportStatEnabled(ViewportClient, ProfilingStatName, bEnable);
	if (bEnable)
	{
		EnsureProfilingSlateOverlay(ViewportClient);
	}
	else
	{
		RemoveProfilingSlateOverlay();
	}
}

static bool DisablePluginViewportStatsForConflictingExternalStat(UWorld* World, FCommonViewportClient* ViewportClient)
{
	if (!HasConflictingExternalViewportStat(ViewportClient))
	{
		return false;
	}

	const bool bHadPluginStat = IsViewportStatEnabled(ViewportClient)
		|| IsObjectViewportStatEnabled(ViewportClient)
		|| IsProfilingViewportStatEnabled(ViewportClient);

	CVarDebug->Set(0);
	CVarObjectDebug->Set(0);
	StopMaterialReplay(World, ViewportClient);
	DisableActorColoration(World, ViewportClient);
	ClearCachedDebugOverlay(World);
	SetViewportStatEnabled(ViewportClient, false);
	SetObjectViewportStatEnabled(ViewportClient, false);
	SetProfilingViewportStatEnabled(ViewportClient, false);

	if (bHadPluginStat)
	{
		UE_LOG(LogOptimizationPreviewTools, Verbose, TEXT("Optimization Preview Tools stats disabled because another viewport stat is active."));
	}

	return true;
}

static bool StopInsightsTraceIfNeeded();

static bool IsProfilingOffCommand(const FString& Command)
{
	FString NormalizedCommand = Command;
	NormalizedCommand.TrimStartAndEndInline();

	const TCHAR* Cmd = *NormalizedCommand;
	if (!FParse::Command(&Cmd, TEXT("stat")))
	{
		return false;
	}
	if (!FParse::Command(&Cmd, *ProfilingStatName))
	{
		return false;
	}

	return FParse::Command(&Cmd, TEXT("0"))
		|| FParse::Command(&Cmd, TEXT("off"))
		|| FParse::Command(&Cmd, TEXT("clear"));
}

static void KeepProfilingCommandsVisibleAfterButtonCommand(const FString& Command)
{
	if (IsProfilingOffCommand(Command))
	{
		return;
	}

	if (UGameViewportClient* ProfilingViewportClient = GProfilingSlateOverlayViewport.Get())
	{
		SetProfilingViewportStatEnabled(ProfilingViewportClient, true);
	}
	else if (UGameViewportClient* EngineGameViewportClient = GEngine ? GEngine->GameViewport : nullptr)
	{
		SetProfilingViewportStatEnabled(EngineGameViewportClient, true);
	}
}

static void DisableAllViewportStats()
{
	if (GEngine)
	{
		if (GEngine->GameViewport)
		{
			SetViewportStatEnabled(GEngine->GameViewport, false);
			SetObjectViewportStatEnabled(GEngine->GameViewport, false);
			SetProfilingViewportStatEnabled(GEngine->GameViewport, false);
		}

		for (const FWorldContext& WorldContext : GEngine->GetWorldContexts())
		{
			if (WorldContext.GameViewport)
			{
				SetViewportStatEnabled(WorldContext.GameViewport, false);
				SetObjectViewportStatEnabled(WorldContext.GameViewport, false);
				SetProfilingViewportStatEnabled(WorldContext.GameViewport, false);
			}
		}
	}

#if WITH_EDITOR
	if (GEditor)
	{
		for (FEditorViewportClient* ViewportClient : GEditor->GetAllViewportClients())
		{
			SetViewportStatEnabled(ViewportClient, false);
			SetObjectViewportStatEnabled(ViewportClient, false);
			SetProfilingViewportStatEnabled(ViewportClient, false);
		}
		GEditor->RedrawAllViewports();
	}
#endif
}

static void RegisterConsoleAutoCompleteCommand(const TCHAR* Command, const TCHAR* Description)
{
	if (IConsoleManager::Get().FindConsoleObject(Command))
	{
		return;
	}

	if (IConsoleCommand* ConsoleCommand = IConsoleManager::Get().RegisterConsoleCommand(Command, Description, ECVF_Default))
	{
		GConsoleAutoCompleteCommands.Add(ConsoleCommand);
	}
}

static void RegisterConsoleAutoComplete()
{
	RegisterConsoleAutoCompleteCommand(TEXT("stat mat"), TEXT("Toggle Material GPU Preview result panel."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat mat start"), TEXT("Start Material GPU Preview Insights trace capture."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat mat end"), TEXT("Stop trace, analyze utrace, and show the result."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat mat stop"), TEXT("Stop trace, analyze utrace, and show the result."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat mat replay"), TEXT("Replay captured per-frame material GPU samples with a timeline slider."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat mat 0"), TEXT("Hide Material GPU Preview panel and debug visualization."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat mat 1"), TEXT("Show last Material GPU Preview Insights result."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat mat clear"), TEXT("Clear Material GPU Preview capture state and overlay."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat matmode"), TEXT("Toggle Material GPU Preview debug colors without hiding the stat or replay UI."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat matmode 0"), TEXT("Use original scene colors for Material GPU Preview."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat matmode 1"), TEXT("Use Material GPU Preview debug colors."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat material"), TEXT("Toggle Material GPU Preview result panel."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat material start"), TEXT("Start Material GPU Preview Insights trace capture."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat material end"), TEXT("Stop trace, analyze utrace, and show the result."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat material replay"), TEXT("Replay captured per-frame material GPU samples with a timeline slider."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat obj"), TEXT("Create and show an Object Memory Snapshot for the current world."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat obj 0"), TEXT("Hide Object Memory Snapshot panel and debug visualization."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat profiling"), TEXT("Show Optimization Preview Tools command buttons under the active Top 10 stat panel."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat profiling 0"), TEXT("Hide Optimization Preview Tools command buttons."));
	RegisterConsoleAutoCompleteCommand(TEXT("materialgpu.DumpLandscapeGrass"), TEXT("Dump Landscape Grass source labels, instance counts, and current debug-row coverage."));
}

static void UnregisterConsoleAutoComplete()
{
	for (IConsoleCommand* ConsoleCommand : GConsoleAutoCompleteCommands)
	{
		if (ConsoleCommand)
		{
			IConsoleManager::Get().UnregisterConsoleObject(ConsoleCommand, false);
		}
	}
	GConsoleAutoCompleteCommands.Reset();
}

#if WITH_EDITOR
static void HandleEndPIE(const bool bIsSimulating)
{
	StopInsightsTraceIfNeeded();
	RestoreInsightsMaterialCaptureCvars();
	GCaptureActive = false;
	GCaptureFrozen = GCachedRows.Num() > 0;
	GCaptureEndTime = FPlatformTime::Seconds();
	GTraceStartedByCapture = false;
	GMaterialReplayActive = false;
	GMaterialReplayPlaying = false;
	GMaterialReplayScrubbing = false;
	GMaterialReplayCurrentRows.Reset();
	GMaterialReplayCurrentRowsAll.Reset();
	GMaterialReplayDebugRows.Reset();
	GMaterialReplayCurrentTimeSeconds = 0.0;
	GMaterialReplayLastTickSeconds = -1.0;
	GMaterialReplayCurrentSampleIndex = INDEX_NONE;
	GMaterialReplayCharacterSamples.Reset();
	GMaterialReplayFrameGpuMs.Reset();
	GMaterialReplayFrameGpuMsMax = 0.0f;
	ClearMaterialReplayDerivedCaches();
	GLastDebugMaterialCount = GCachedDebugRows.Num();
	GLastDebugComponentCount = CountUniqueDebugComponents(GCachedDebugRows);
	StopMaterialReplayTicker();
	StopMaterialReplayCameraCaptureTicker();
	RemoveMaterialReplayOverlay();
	RestoreMaterialReplayAnimationStates();
	DestroyMaterialReplayCamera();
	CVarDebug->Set(0);
	CVarObjectDebug->Set(0);
	DisableActorColoration(nullptr, nullptr);
	ClearCachedDebugOverlay(nullptr);
	DisableAllViewportStats();
	GLastAnalysisMessage = TEXT("PIE ended; stat mat disabled.");
	GLastObjectSnapshotMessage = TEXT("PIE ended; stat obj disabled.");
	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Material GPU Preview disabled on PIE end. Simulating=%s"),
		bIsSimulating ? TEXT("true") : TEXT("false"));
}

static void RegisterEditorDelegates()
{
	if (!GEndPIEHandle.IsValid())
	{
		GEndPIEHandle = FEditorDelegates::EndPIE.AddStatic(&HandleEndPIE);
	}
}

static void UnregisterEditorDelegates()
{
	if (GEndPIEHandle.IsValid())
	{
		FEditorDelegates::EndPIE.Remove(GEndPIEHandle);
		GEndPIEHandle.Reset();
	}
}
#endif

static void UpdateDebugOverlay(UWorld* World);
static void ApplyObjectDebugVisualization(UWorld* World, FCommonViewportClient* ViewportClient);
static bool BuildRowsFromInsightsTrace(UWorld* World);

static void ApplyMaterialDebugVisualization(UWorld* World, FCommonViewportClient* ViewportClient)
{
	if (!World || CVarDebug.GetValueOnGameThread() == 0)
	{
		DisableActorColoration(World, ViewportClient);
		ClearCachedDebugOverlay(World);
		return;
	}

	if (!IsMaterialDebugColorModeEnabled())
	{
		DisableActorColoration(World, ViewportClient);
		ClearCachedDebugOverlay(World);
		RefreshActorColorationViewports(ViewportClient);
		return;
	}

	if (ShouldUseActorColorationBackend())
	{
		ApplyActorColorationViewMode(World, ViewportClient);
	}
	else
	{
		DisableActorColoration(World, ViewportClient);
		UpdateDebugOverlay(World);
	}
}

static bool StartInsightsGpuTrace()
{
	GTraceFilePath = BuildTraceFilePath();
	const FString TraceChannels = GetMaterialGPUTraceChannels();

	FTraceAuxiliary::FOptions Options;
	Options.bTruncateFile = true;
	Options.bExcludeTail = true;
	return FTraceAuxiliary::Start(FTraceAuxiliary::EConnectionType::File, *GTraceFilePath, *TraceChannels, &Options, LogOptimizationPreviewTools);
}

static bool WaitForTraceFileReady(const FString& TraceFilePath)
{
	if (TraceFilePath.IsEmpty())
	{
		return false;
	}

	int64 PreviousFileSize = -1;
	int32 StableSizeSamples = 0;

	for (int32 Attempt = 0; Attempt < 30; ++Attempt)
	{
		const FFileStatData StatData = IFileManager::Get().GetStatData(*TraceFilePath);
		if (StatData.bIsValid && StatData.FileSize > 0)
		{
			if (StatData.FileSize == PreviousFileSize)
			{
				StableSizeSamples++;
				if (StableSizeSamples >= 2)
				{
					return true;
				}
			}
			else
			{
				PreviousFileSize = StatData.FileSize;
				StableSizeSamples = 0;
			}
		}

		FPlatformProcess::Sleep(0.04f);
	}

	return FPaths::FileExists(TraceFilePath);
}

static bool StopInsightsTraceIfNeeded()
{
	if (!GTraceStartedByCapture)
	{
		return false;
	}

	const bool bStopped = FTraceAuxiliary::Stop();
	GTraceStartedByCapture = false;
	return bStopped;
}

static void StartCapture(UWorld* World, FCommonViewportClient* ViewportClient)
{
	if (GCaptureActive)
	{
		UE_LOG(LogOptimizationPreviewTools, Verbose, TEXT("Material GPU Preview capture is already active."));
		return;
	}

	StopMaterialReplay(World, ViewportClient);
	StopInsightsTraceIfNeeded();
	RestoreInsightsMaterialCaptureCvars();
	ClearCaptureState();

	GCachedRows.Reset();
	GCachedRowsAll.Reset();
	GLastAnalysisMessage = TEXT("Recording Insights trace...");
	CVarDebug->Set(0);
	CVarObjectDebug->Set(0);
	DisableActorColoration(World, ViewportClient);
	RemoveConflictingExternalViewportStats(ViewportClient);
	SetViewportStatEnabled(ViewportClient, false);
	SetObjectViewportStatEnabled(ViewportClient, false);
	ClearCachedDebugOverlay(World);

	GCaptureActive = true;
	GCaptureFrozen = false;
	GCaptureStartTime = FPlatformTime::Seconds();
	GCaptureEndTime = -1.0;
	ApplyInsightsMaterialCaptureCvars();
	GTraceStartedByCapture = StartInsightsGpuTrace();

	if (!GTraceStartedByCapture)
	{
		StopMaterialReplayCameraCaptureTicker();
		RestoreInsightsMaterialCaptureCvars();
		GCaptureActive = false;
		GCaptureEndTime = FPlatformTime::Seconds();
		GLastAnalysisMessage = TEXT("Failed to start Insights trace.");
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Material GPU Preview capture failed to start. Trace=%s Channels=%s"),
			*GTraceFilePath,
			*GetMaterialGPUTraceChannels());
		return;
	}

	StartMaterialReplayCameraCapture(World);
	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Material GPU Preview capture started. Trace=%s Channels=%s StartedTrace=%s"),
		*GTraceFilePath,
		*GetMaterialGPUTraceChannels(),
		GTraceStartedByCapture ? TEXT("true") : TEXT("false"));
}

static void EndCapture(UWorld* World, FCommonViewportClient* ViewportClient)
{
	if (!GCaptureActive)
	{
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Material GPU Preview capture is not active."));
		return;
	}

	GCaptureActive = false;
	GCaptureFrozen = true;
	GCaptureEndTime = FPlatformTime::Seconds();
	StopMaterialReplayCameraCaptureTicker();

	FlushRenderingCommands();
	const bool bStoppedTrace = StopInsightsTraceIfNeeded();
	if (bStoppedTrace)
	{
		WaitForTraceFileReady(GTraceFilePath);
	}
	RestoreInsightsMaterialCaptureCvars();
	GCachedRows.Reset();
	GCachedRowsAll.Reset();
	GCachedDebugRows.Reset();
	const bool bBuiltTraceRows = BuildRowsFromInsightsTrace(World);
	if (!bBuiltTraceRows)
	{
		GCachedRows.Reset();
		GCachedRowsAll.Reset();
		GCachedDebugRows.Reset();
		GLastDebugMaterialCount = 0;
		GLastDebugComponentCount = 0;
		CVarDebug->Set(0);
		DisableActorColoration(World, ViewportClient);
		ClearCachedDebugOverlay(World);
		SetViewportStatEnabled(ViewportClient, true);
	}
	else
	{
		if (GMaterialReplaySamples.Num() > 0)
		{
			StartMaterialReplay(World, ViewportClient);
		}
		else
		{
			CVarDebug->Set(1);
			SetViewportStatEnabled(ViewportClient, true);
			ApplyMaterialDebugVisualization(World, ViewportClient);
		}
	}

	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Material GPU Preview capture ended. Duration=%.2fs Rows=%d Source=utrace Trace=%s StoppedTrace=%s Analysis=%s"),
		GetCaptureDurationSeconds(),
		GCachedRows.Num(),
		*GTraceFilePath,
		bStoppedTrace ? TEXT("true") : TEXT("false"),
		*GLastAnalysisMessage);

	GMaterialCaptureEndGuardActive = true;
	GMaterialCaptureEndGuardReleaseSeconds = FPlatformTime::Seconds() + MaterialCaptureEndGuardDebounceSeconds;
}

static void SetDebugViewEnabled(UWorld* World, FCommonViewportClient* ViewportClient, bool bEnable)
{
	if (!bEnable)
	{
		StopMaterialReplay(World, ViewportClient);
		CVarDebug->Set(0);
		DisableActorColoration(World, ViewportClient);
		ClearCachedDebugOverlay(World);
		SetViewportStatEnabled(ViewportClient, false);
		return;
	}

	StopMaterialReplay(World, ViewportClient);
	CVarObjectDebug->Set(0);
	SetObjectViewportStatEnabled(ViewportClient, false);
	ClearCachedDebugOverlay(World);
	SetViewportStatEnabled(ViewportClient, true);
	if (GCachedRows.Num() == 0)
	{
		CVarDebug->Set(0);
		GLastAnalysisMessage = GLastAnalysisMessage.IsEmpty()
			? TEXT("No Insights material capture is available. Run 'stat mat start' and 'stat mat end'.")
			: GLastAnalysisMessage;
		DisableActorColoration(World, ViewportClient);
		ClearCachedDebugOverlay(World);
		return;
	}

	CVarDebug->Set(1);
	ApplyMaterialDebugVisualization(World, ViewportClient);
}

static void SetMaterialDebugColorModeEnabled(UWorld* World, FCommonViewportClient* ViewportClient, bool bEnable)
{
	CVarMaterialDebugMode->Set(bEnable ? 1 : 0, ECVF_SetByConsole);
	ApplyMaterialDebugVisualization(World, ViewportClient);
	ApplyObjectDebugVisualization(World, ViewportClient);
	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Optimization Preview Tools debug color mode %s."),
		bEnable ? TEXT("enabled") : TEXT("disabled"));
}

static bool ToggleMaterialModeStat(UWorld* World, FCommonViewportClient* ViewportClient, const TCHAR* Stream)
{
	FString Args(Stream ? Stream : TEXT(""));
	Args.TrimStartAndEndInline();

	const TCHAR* Cmd = *Args;
	if (FParse::Command(&Cmd, TEXT("0")) || FParse::Command(&Cmd, TEXT("off")))
	{
		SetMaterialDebugColorModeEnabled(World, ViewportClient, false);
		return true;
	}

	if (FParse::Command(&Cmd, TEXT("1")) || FParse::Command(&Cmd, TEXT("on")))
	{
		SetMaterialDebugColorModeEnabled(World, ViewportClient, true);
		return true;
	}

	SetMaterialDebugColorModeEnabled(World, ViewportClient, !IsMaterialDebugColorModeEnabled());
	return true;
}

static bool ToggleStat(UWorld* World, FCommonViewportClient* ViewportClient, const TCHAR* Stream)
{
	FString Args(Stream ? Stream : TEXT(""));
	Args.TrimStartAndEndInline();

	const TCHAR* Cmd = *Args;
	const FString FullCommand = FString::Printf(TEXT("stat %s %s"), *StatName, *Args);
	if (ShouldBlockMaterialCaptureCommand(FullCommand))
	{
		UE_LOG(LogOptimizationPreviewTools, Verbose, TEXT("Material GPU Preview capture command ignored during post-end guard: %s"), *Args);
		return true;
	}

	if (FParse::Command(&Cmd, TEXT("0")))
	{
		SetDebugViewEnabled(World, ViewportClient, false);
		return true;
	}

	if (FParse::Command(&Cmd, TEXT("1")))
	{
		SetDebugViewEnabled(World, ViewportClient, true);
		return true;
	}

	if (FParse::Command(&Cmd, TEXT("start")))
	{
		StartCapture(World, ViewportClient);
		return true;
	}

	if (FParse::Command(&Cmd, TEXT("end")) || FParse::Command(&Cmd, TEXT("stop")))
	{
		EndCapture(World, ViewportClient);
		return true;
	}

	if (FParse::Command(&Cmd, TEXT("replay")))
	{
		if (GMaterialReplayActive)
		{
			SetDebugViewEnabled(World, ViewportClient, false);
		}
		else
		{
			StartMaterialReplay(World, ViewportClient);
		}
		return true;
	}

	if (FParse::Command(&Cmd, TEXT("clear")))
	{
		StopMaterialReplay(World, ViewportClient);
		StopInsightsTraceIfNeeded();
		RestoreInsightsMaterialCaptureCvars();
		ClearCaptureState();
		GCachedRows.Reset();
		GCachedRowsAll.Reset();
		GLastAnalysisMessage.Reset();
		DisableActorColoration(World, ViewportClient);
		ClearCachedDebugOverlay(World);
		CVarDebug->Set(0);
		SetViewportStatEnabled(ViewportClient, false);
		return true;
	}

	if (FParse::Command(&Cmd, TEXT("off")))
	{
		SetDebugViewEnabled(World, ViewportClient, false);
		return true;
	}

	if (FParse::Command(&Cmd, TEXT("on")))
	{
		SetDebugViewEnabled(World, ViewportClient, true);
		return true;
	}

	const bool bEnable = !IsViewportStatEnabled(ViewportClient);
	SetDebugViewEnabled(World, ViewportClient, bEnable);
	return true;
}

static bool ShouldIncludeComponent(const UPrimitiveComponent* Component)
{
	return Component && Component->IsRegistered() && Component->IsVisible();
}

#if WITH_EDITOR
static FName FindLandscapeGrassOutputSlotName(UMaterialInterface* LandscapeMaterial, const ULandscapeGrassType* GrassType)
{
	if (!LandscapeMaterial || !GrassType)
	{
		return NAME_None;
	}

	const UMaterial* BaseMaterial = LandscapeMaterial->GetMaterial();
	if (!BaseMaterial)
	{
		return NAME_None;
	}

	for (const TObjectPtr<UMaterialExpression>& Expression : BaseMaterial->GetExpressions())
	{
		const UMaterialExpressionLandscapeGrassOutput* GrassOutput = Cast<UMaterialExpressionLandscapeGrassOutput>(Expression.Get());
		if (!GrassOutput)
		{
			continue;
		}

		for (const FGrassInput& GrassInput : GrassOutput->GrassTypes)
		{
			if (GrassInput.GrassType.Get() == GrassType)
			{
				return GrassInput.Name;
			}
		}
	}

	return NAME_None;
}
#endif

static FString BuildLandscapeGrassSourceLabel(ULandscapeComponent* LandscapeComponent, ULandscapeGrassType* GrassType, int32 VarietyIndex)
{
	FString SourceName = GrassType ? GrassType->GetName() : FString(TEXT("UnknownGrass"));

#if WITH_EDITOR
	if (LandscapeComponent)
	{
		const FName SlotName = FindLandscapeGrassOutputSlotName(LandscapeComponent->GetLandscapeMaterial(), GrassType);
		if (!SlotName.IsNone())
		{
			SourceName = SlotName.ToString();
		}
	}
#endif

	FString VarietyName;
	if (GrassType && GrassType->GrassVarieties.IsValidIndex(VarietyIndex))
	{
		const FGrassVariety& Variety = GrassType->GrassVarieties[VarietyIndex];
		if (Variety.GrassMesh)
		{
			VarietyName = Variety.GrassMesh->GetName();
		}
	}

	if (!VarietyName.IsEmpty())
	{
		return FString::Printf(TEXT("Grass:%s/%s"), *SourceName, *VarietyName);
	}

	if (VarietyIndex >= 0)
	{
		return FString::Printf(TEXT("Grass:%s#%d"), *SourceName, VarietyIndex);
	}

	return FString::Printf(TEXT("Grass:%s"), *SourceName);
}

static FString BuildInstancedFoliageSourceLabel(UFoliageType* FoliageType)
{
	const UFoliageType_InstancedStaticMesh* InstancedFoliageType = Cast<UFoliageType_InstancedStaticMesh>(FoliageType);
	UStaticMesh* StaticMesh = InstancedFoliageType ? InstancedFoliageType->GetStaticMesh() : nullptr;
	UObject* Source = FoliageType ? FoliageType->GetSource() : nullptr;

	const FString MeshName = StaticMesh ? StaticMesh->GetName() : FString(TEXT("UnknownMesh"));
	const FString SourceName = Source ? Source->GetName() : FString();
	if (!SourceName.IsEmpty() && SourceName != MeshName)
	{
		return FString::Printf(TEXT("Foliage:%s/%s"), *SourceName, *MeshName);
	}

	return FString::Printf(TEXT("Foliage:%s"), *MeshName);
}

static void AddFoliageSourceInfo(
	TMap<FObjectKey, FComponentSourceInfo>& OutSourceInfo,
	UHierarchicalInstancedStaticMeshComponent* Component,
	const FString& SourceLabel,
	int32 FallbackInstanceCount = 0)
{
	if (!Component || SourceLabel.IsEmpty())
	{
		return;
	}

	FComponentSourceInfo& ExistingInfo = OutSourceInfo.FindOrAdd(FObjectKey(Component));
	if (ExistingInfo.Label.IsEmpty())
	{
		ExistingInfo.Label = SourceLabel;
	}
	else if (!ExistingInfo.Label.Contains(SourceLabel))
	{
		ExistingInfo.Label += TEXT(", ");
		ExistingInfo.Label += SourceLabel;
	}

	ExistingInfo.InstanceCount += FMath::Max(Component->GetNumRenderInstances(), FallbackInstanceCount);
}

static void BuildLandscapeGrassSourceInfo(UWorld* World, TMap<FObjectKey, FComponentSourceInfo>& OutSourceInfo)
{
	OutSourceInfo.Reset();
	if (!World)
	{
		return;
	}

	for (TActorIterator<ALandscapeProxy> ProxyIt(World); ProxyIt; ++ProxyIt)
	{
		ALandscapeProxy* Proxy = *ProxyIt;
		if (!Proxy)
		{
			continue;
		}

		for (const FCachedLandscapeFoliage::FGrassComp& GrassComp : Proxy->FoliageCache.CachedGrassComps)
		{
			ULandscapeComponent* LandscapeComponent = GrassComp.Key.BasedOn.Get();
			ULandscapeGrassType* GrassType = GrassComp.Key.GrassType.Get();
			const FString SourceLabel = BuildLandscapeGrassSourceLabel(LandscapeComponent, GrassType, GrassComp.Key.VarietyIndex);

			AddFoliageSourceInfo(OutSourceInfo, GrassComp.Foliage.Get(), SourceLabel);
			AddFoliageSourceInfo(OutSourceInfo, GrassComp.PreviousFoliage.Get(), SourceLabel);
		}
	}
}

static void AppendInstancedFoliageSourceInfo(UWorld* World, TMap<FObjectKey, FComponentSourceInfo>& InOutSourceInfo)
{
	if (!World)
	{
		return;
	}

	for (TActorIterator<AInstancedFoliageActor> ActorIt(World); ActorIt; ++ActorIt)
	{
		AInstancedFoliageActor* FoliageActor = *ActorIt;
		if (!FoliageActor)
		{
			continue;
		}

		for (const TPair<UFoliageType*, TUniqueObj<FFoliageInfo>>& FoliagePair : FoliageActor->GetFoliageInfos())
		{
			UFoliageType* FoliageType = FoliagePair.Key;
			const FFoliageInfo& FoliageInfo = FoliagePair.Value.Get();
			UHierarchicalInstancedStaticMeshComponent* Component = FoliageInfo.GetComponent();
			const FString SourceLabel = BuildInstancedFoliageSourceLabel(FoliageType);
			AddFoliageSourceInfo(InOutSourceInfo, Component, SourceLabel, FoliageInfo.GetPlacedInstanceCount());
		}
	}
}

static void BuildFoliageSourceInfo(UWorld* World, TMap<FObjectKey, FComponentSourceInfo>& OutSourceInfo)
{
	BuildLandscapeGrassSourceInfo(World, OutSourceInfo);
	AppendInstancedFoliageSourceInfo(World, OutSourceInfo);
}

static void BuildFoliageComponentsBySourceLabel(UWorld* World, TMap<FString, TArray<UPrimitiveComponent*>>& OutComponentsBySourceLabel)
{
	OutComponentsBySourceLabel.Reset();
	if (!World)
	{
		return;
	}

	TMap<FObjectKey, FComponentSourceInfo> ComponentSourceInfo;
	BuildFoliageSourceInfo(World, ComponentSourceInfo);
	for (TActorIterator<ALandscapeProxy> ProxyIt(World); ProxyIt; ++ProxyIt)
	{
		ALandscapeProxy* Proxy = *ProxyIt;
		if (!Proxy)
		{
			continue;
		}

		for (const FCachedLandscapeFoliage::FGrassComp& GrassComp : Proxy->FoliageCache.CachedGrassComps)
		{
			UHierarchicalInstancedStaticMeshComponent* Components[] =
			{
				GrassComp.Foliage.Get(),
				GrassComp.PreviousFoliage.Get()
			};

			for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
			{
				if (!Component || !Component->IsVisible())
				{
					continue;
				}

				const FComponentSourceInfo* SourceInfo = ComponentSourceInfo.Find(FObjectKey(Component));
				if (!SourceInfo || SourceInfo->Label.IsEmpty())
				{
					continue;
				}

				OutComponentsBySourceLabel.FindOrAdd(SourceInfo->Label).AddUnique(Component);
			}
		}
	}

	for (TActorIterator<AInstancedFoliageActor> ActorIt(World); ActorIt; ++ActorIt)
	{
		AInstancedFoliageActor* FoliageActor = *ActorIt;
		if (!FoliageActor)
		{
			continue;
		}

		for (const TPair<UFoliageType*, TUniqueObj<FFoliageInfo>>& FoliagePair : FoliageActor->GetFoliageInfos())
		{
			UHierarchicalInstancedStaticMeshComponent* Component = FoliagePair.Value.Get().GetComponent();
			if (!Component || !Component->IsVisible())
			{
				continue;
			}

			const FComponentSourceInfo* SourceInfo = ComponentSourceInfo.Find(FObjectKey(Component));
			if (!SourceInfo || SourceInfo->Label.IsEmpty())
			{
				continue;
			}

			OutComponentsBySourceLabel.FindOrAdd(SourceInfo->Label).AddUnique(Component);
		}
	}
}

static void AddMaterialSourceUsage(FMaterialAccumulator& Accumulator, const FComponentSourceInfo& SourceInfo)
{
	if (SourceInfo.Label.IsEmpty())
	{
		return;
	}

	FMaterialSourceUsage* Usage = Accumulator.SourceUsages.FindByPredicate([&SourceInfo](const FMaterialSourceUsage& ExistingUsage)
	{
		return ExistingUsage.Label == SourceInfo.Label;
	});

	if (!Usage)
	{
		Usage = &Accumulator.SourceUsages.AddDefaulted_GetRef();
		Usage->Label = SourceInfo.Label;
	}

	Usage->InstanceCount += SourceInfo.InstanceCount;
	Usage->ComponentCount++;
}

static void SortMaterialSourceUsages(TArray<FMaterialSourceUsage>& SourceUsages)
{
	SourceUsages.Sort([](const FMaterialSourceUsage& A, const FMaterialSourceUsage& B)
	{
		if (A.InstanceCount != B.InstanceCount)
		{
			return A.InstanceCount > B.InstanceCount;
		}
		if (A.ComponentCount != B.ComponentCount)
		{
			return A.ComponentCount > B.ComponentCount;
		}
		return A.Label < B.Label;
	});
}

static FMaterialAccumulator& FindOrAddAccumulator(TArray<FMaterialAccumulator>& Accumulators, UMaterialInterface* Material)
{
	check(Material);

	for (FMaterialAccumulator& Accumulator : Accumulators)
	{
		if (Accumulator.Material.Get() == Material)
		{
			return Accumulator;
		}
	}

	FMaterialAccumulator& NewAccumulator = Accumulators.AddDefaulted_GetRef();
	NewAccumulator.Material = Material;
	NewAccumulator.DisplayName = Material->GetName();
	NewAccumulator.PathName = Material->GetPathName();
	NewAccumulator.BlendMode = Material->GetBlendMode();

	return NewAccumulator;
}

static void AddUsage(
	TArray<FMaterialAccumulator>& Accumulators,
	UPrimitiveComponent* Component,
	UMaterialInterface* Material,
	int64 Triangles,
	int64 Instances,
	const TMap<FObjectKey, FComponentSourceInfo>& ComponentSourceInfo)
{
	if (!Component || !Material)
	{
		return;
	}

	if (Triangles <= 0 || Instances <= 0)
	{
		return;
	}

	const int64 SafeTriangles = FMath::Max<int64>(Triangles, 1);
	const int64 SafeInstances = Instances;

	FMaterialAccumulator& Accumulator = FindOrAddAccumulator(Accumulators, Material);
	Accumulator.Triangles += SafeTriangles * SafeInstances;

	if (!Accumulator.Components.Contains(Component))
	{
		if (const FComponentSourceInfo* SourceInfo = ComponentSourceInfo.Find(FObjectKey(Component)))
		{
			AddMaterialSourceUsage(Accumulator, *SourceInfo);
		}

		Accumulator.Components.Add(Component);
		Accumulator.ComponentCount++;
	}
}

static void AccumulateStaticMeshComponent(
	TArray<FMaterialAccumulator>& Accumulators,
	UStaticMeshComponent* Component,
	const TMap<FObjectKey, FComponentSourceInfo>& ComponentSourceInfo)
{
	UStaticMesh* StaticMesh = Component ? Component->GetStaticMesh() : nullptr;
	const FStaticMeshRenderData* RenderData = StaticMesh ? StaticMesh->GetRenderData() : nullptr;
	if (!RenderData || RenderData->LODResources.Num() == 0)
	{
		TArray<UMaterialInterface*> Materials;
		Component->GetUsedMaterials(Materials);
		for (UMaterialInterface* Material : Materials)
		{
			AddUsage(Accumulators, Component, Material, 1, 1, ComponentSourceInfo);
		}
		return;
	}

	const int64 InstanceCount = Component->IsA<UInstancedStaticMeshComponent>()
		? static_cast<int64>(CastChecked<UInstancedStaticMeshComponent>(Component)->GetNumRenderInstances())
		: 1;

	const FStaticMeshLODResources& LOD = RenderData->LODResources[0];
	for (const FStaticMeshSection& Section : LOD.Sections)
	{
		UMaterialInterface* Material = Component->GetMaterial(Section.MaterialIndex);
		AddUsage(Accumulators, Component, Material, Section.NumTriangles, InstanceCount, ComponentSourceInfo);
	}
}

static void AccumulateSkinnedMeshComponent(
	TArray<FMaterialAccumulator>& Accumulators,
	USkinnedMeshComponent* Component,
	const TMap<FObjectKey, FComponentSourceInfo>& ComponentSourceInfo)
{
	FSkeletalMeshRenderData* RenderData = Component ? Component->GetSkeletalMeshRenderData() : nullptr;
	if (!RenderData || RenderData->LODRenderData.Num() == 0)
	{
		TArray<UMaterialInterface*> Materials;
		Component->GetUsedMaterials(Materials);
		for (UMaterialInterface* Material : Materials)
		{
			AddUsage(Accumulators, Component, Material, 1, 1, ComponentSourceInfo);
		}
		return;
	}

	const FSkeletalMeshLODRenderData& LOD = RenderData->LODRenderData[0];
	for (const FSkelMeshRenderSection& Section : LOD.RenderSections)
	{
		if (!Section.IsValid())
		{
			continue;
		}

		UMaterialInterface* Material = Component->GetMaterial(Section.MaterialIndex);
		AddUsage(Accumulators, Component, Material, Section.NumTriangles, 1, ComponentSourceInfo);
	}
}

static void AccumulatePrimitiveComponent(
	TArray<FMaterialAccumulator>& Accumulators,
	UPrimitiveComponent* Component,
	const TMap<FObjectKey, FComponentSourceInfo>& ComponentSourceInfo)
{
	if (UStaticMeshComponent* StaticMeshComponent = Cast<UStaticMeshComponent>(Component))
	{
		AccumulateStaticMeshComponent(Accumulators, StaticMeshComponent, ComponentSourceInfo);
		return;
	}

	if (USkinnedMeshComponent* SkinnedMeshComponent = Cast<USkinnedMeshComponent>(Component))
	{
		AccumulateSkinnedMeshComponent(Accumulators, SkinnedMeshComponent, ComponentSourceInfo);
		return;
	}

	TArray<UMaterialInterface*> Materials;
	Component->GetUsedMaterials(Materials);
	for (UMaterialInterface* Material : Materials)
	{
		AddUsage(Accumulators, Component, Material, 1, 1, ComponentSourceInfo);
	}
}

static void AccumulatePrimitiveComponentOnce(
	TArray<FMaterialAccumulator>& Accumulators,
	UPrimitiveComponent* Component,
	const TMap<FObjectKey, FComponentSourceInfo>& ComponentSourceInfo,
	TSet<FObjectKey>& ProcessedComponents)
{
	if (!ShouldIncludeComponent(Component))
	{
		return;
	}

	const FObjectKey ComponentKey(Component);
	if (ProcessedComponents.Contains(ComponentKey))
	{
		return;
	}

	ProcessedComponents.Add(ComponentKey);
	AccumulatePrimitiveComponent(Accumulators, Component, ComponentSourceInfo);
}

static bool IsFoliageTargetComponent(const UPrimitiveComponent* Component)
{
	return Component && Component->IsVisible();
}

static void AccumulateFoliageComponentOnce(
	TArray<FMaterialAccumulator>& Accumulators,
	UPrimitiveComponent* Component,
	const TMap<FObjectKey, FComponentSourceInfo>& ComponentSourceInfo,
	TSet<FObjectKey>& ProcessedComponents)
{
	if (!IsFoliageTargetComponent(Component))
	{
		return;
	}

	const FObjectKey ComponentKey(Component);
	if (ProcessedComponents.Contains(ComponentKey))
	{
		return;
	}

	ProcessedComponents.Add(ComponentKey);
	AccumulatePrimitiveComponent(Accumulators, Component, ComponentSourceInfo);
}

static void AccumulateLandscapeGrassComponents(
	UWorld* World,
	TArray<FMaterialAccumulator>& Accumulators,
	const TMap<FObjectKey, FComponentSourceInfo>& ComponentSourceInfo,
	TSet<FObjectKey>& ProcessedComponents)
{
	if (!World)
	{
		return;
	}

	for (TActorIterator<ALandscapeProxy> ProxyIt(World); ProxyIt; ++ProxyIt)
	{
		ALandscapeProxy* Proxy = *ProxyIt;
		if (!Proxy)
		{
			continue;
		}

		for (const FCachedLandscapeFoliage::FGrassComp& GrassComp : Proxy->FoliageCache.CachedGrassComps)
		{
			AccumulateFoliageComponentOnce(Accumulators, GrassComp.Foliage.Get(), ComponentSourceInfo, ProcessedComponents);
			AccumulateFoliageComponentOnce(Accumulators, GrassComp.PreviousFoliage.Get(), ComponentSourceInfo, ProcessedComponents);
		}
	}
}

static void AccumulateInstancedFoliageComponents(
	UWorld* World,
	TArray<FMaterialAccumulator>& Accumulators,
	const TMap<FObjectKey, FComponentSourceInfo>& ComponentSourceInfo,
	TSet<FObjectKey>& ProcessedComponents)
{
	if (!World)
	{
		return;
	}

	for (TActorIterator<AInstancedFoliageActor> ActorIt(World); ActorIt; ++ActorIt)
	{
		AInstancedFoliageActor* FoliageActor = *ActorIt;
		if (!FoliageActor)
		{
			continue;
		}

		for (const TPair<UFoliageType*, TUniqueObj<FFoliageInfo>>& FoliagePair : FoliageActor->GetFoliageInfos())
		{
			AccumulateFoliageComponentOnce(Accumulators, FoliagePair.Value.Get().GetComponent(), ComponentSourceInfo, ProcessedComponents);
		}
	}
}

static void BuildSceneMaterialAccumulators(UWorld* World, TArray<FMaterialAccumulator>& OutAccumulators)
{
	OutAccumulators.Reset();
	if (!World)
	{
		return;
	}

	TMap<FObjectKey, FComponentSourceInfo> ComponentSourceInfo;
	BuildFoliageSourceInfo(World, ComponentSourceInfo);
	TSet<FObjectKey> ProcessedComponents;

	for (TActorIterator<AActor> ActorIt(World); ActorIt; ++ActorIt)
	{
		AActor* Actor = *ActorIt;
		if (!Actor)
		{
			continue;
		}

		TInlineComponentArray<UPrimitiveComponent*> Components;
		Actor->GetComponents(Components);
		for (UPrimitiveComponent* Component : Components)
		{
			AccumulatePrimitiveComponentOnce(OutAccumulators, Component, ComponentSourceInfo, ProcessedComponents);
		}
	}

	AccumulateLandscapeGrassComponents(World, OutAccumulators, ComponentSourceInfo, ProcessedComponents);
	AccumulateInstancedFoliageComponents(World, OutAccumulators, ComponentSourceInfo, ProcessedComponents);

	for (FMaterialAccumulator& Accumulator : OutAccumulators)
	{
		SortMaterialSourceUsages(Accumulator.SourceUsages);
	}
}

static void SortMaterialAccumulators(TArray<FMaterialAccumulator>& Accumulators)
{
	Accumulators.Sort([](const FMaterialAccumulator& A, const FMaterialAccumulator& B)
	{
		if (A.ComponentCount == B.ComponentCount)
		{
			return A.PathName < B.PathName;
		}
		return A.ComponentCount > B.ComponentCount;
	});
}

static void AddFoliageDumpUsage(TMap<FString, FMaterialSourceUsage>& UsagesByLabel, const FComponentSourceInfo& SourceInfo)
{
	if (SourceInfo.Label.IsEmpty())
	{
		return;
	}

	FMaterialSourceUsage& Usage = UsagesByLabel.FindOrAdd(SourceInfo.Label);
	Usage.Label = SourceInfo.Label;
	Usage.InstanceCount += SourceInfo.InstanceCount;
	Usage.ComponentCount++;
}

static void DumpLandscapeGrassDiagnostics()
{
	UWorld* World = FindCurrentPreviewWorld();
	if (!World)
	{
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("LandscapeGrass dump skipped: no current world."));
		return;
	}

	TMap<FObjectKey, FComponentSourceInfo> ComponentSourceInfo;
	BuildFoliageSourceInfo(World, ComponentSourceInfo);

	TMap<FString, FMaterialSourceUsage> AllUsagesByLabel;
	for (const TPair<FObjectKey, FComponentSourceInfo>& Pair : ComponentSourceInfo)
	{
		AddFoliageDumpUsage(AllUsagesByLabel, Pair.Value);
	}

	TSet<FObjectKey> DebugComponents;
	TSet<FString> DebugSourceLabels;
	TMap<FString, FMaterialSourceUsage> DebugUsagesByLabel;
	for (const FMaterialAccumulator& Row : GetActiveMaterialDebugRows())
	{
		for (const TWeakObjectPtr<UPrimitiveComponent>& WeakComponent : Row.Components)
		{
			UPrimitiveComponent* Component = WeakComponent.Get();
			if (!Component)
			{
				continue;
			}

			const FObjectKey ComponentKey(Component);
			if (DebugComponents.Contains(ComponentKey))
			{
				continue;
			}

			if (const FComponentSourceInfo* SourceInfo = ComponentSourceInfo.Find(ComponentKey))
			{
				AddFoliageDumpUsage(DebugUsagesByLabel, *SourceInfo);
				DebugComponents.Add(ComponentKey);
			}
		}

		for (const FMaterialSourceUsage& RowSourceUsage : Row.SourceUsages)
		{
			if (RowSourceUsage.Label.IsEmpty() || DebugSourceLabels.Contains(RowSourceUsage.Label))
			{
				continue;
			}

			DebugSourceLabels.Add(RowSourceUsage.Label);
			if (const FMaterialSourceUsage* CurrentUsage = AllUsagesByLabel.Find(RowSourceUsage.Label))
			{
				DebugUsagesByLabel.Add(RowSourceUsage.Label, *CurrentUsage);
			}
			else
			{
				DebugUsagesByLabel.Add(RowSourceUsage.Label, RowSourceUsage);
			}
		}
	}

	TArray<FMaterialSourceUsage> AllUsages;
	AllUsagesByLabel.GenerateValueArray(AllUsages);
	AllUsages.Sort([](const FMaterialSourceUsage& A, const FMaterialSourceUsage& B)
	{
		if (A.InstanceCount != B.InstanceCount)
		{
			return A.InstanceCount > B.InstanceCount;
		}
		return A.Label < B.Label;
	});

	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Foliage dump. World=%s Sources=%d Components=%d DebugSources=%d DebugComponents=%d"),
		*World->GetName(),
		AllUsages.Num(),
		ComponentSourceInfo.Num(),
		DebugUsagesByLabel.Num(),
		DebugComponents.Num());

	for (const FMaterialSourceUsage& Usage : AllUsages)
	{
		const FMaterialSourceUsage* DebugUsage = DebugUsagesByLabel.Find(Usage.Label);
		const int32 DebugComponentsForSource = DebugUsage ? DebugUsage->ComponentCount : 0;
		const int32 DebugInstancesForSource = DebugUsage ? DebugUsage->InstanceCount : 0;
		UE_LOG(LogOptimizationPreviewTools, Display, TEXT("  %s | comps=%d instances=%d | debugComps=%d debugInstances=%d"),
			*Usage.Label,
			Usage.ComponentCount,
			Usage.InstanceCount,
			DebugComponentsForSource,
			DebugInstancesForSource);
	}
}

static FAutoConsoleCommand GDumpLandscapeGrassCommand(
	TEXT("materialgpu.DumpLandscapeGrass"),
	TEXT("Dump Landscape Grass and InstancedFoliageActor source labels, instance counts, and current Material GPU debug-row coverage."),
	FConsoleCommandDelegate::CreateStatic(&DumpLandscapeGrassDiagnostics));

static bool BuildRowsFromInsightsTrace(UWorld* World)
{
	if (GTraceFilePath.IsEmpty() || !FPaths::FileExists(GTraceFilePath))
	{
		GLastAnalysisMessage = FString::Printf(TEXT("Trace file is missing: %s"), *GTraceFilePath);
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Material GPU Preview trace analysis skipped; %s"), *GLastAnalysisMessage);
		return false;
	}

	ITraceServicesModule* TraceServicesModule = FModuleManager::LoadModulePtr<ITraceServicesModule>(TEXT("TraceServices"));
	if (!TraceServicesModule)
	{
		GLastAnalysisMessage = TEXT("TraceServices module is unavailable.");
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Material GPU Preview trace analysis skipped; %s"), *GLastAnalysisMessage);
		return false;
	}

	TSharedPtr<TraceServices::IAnalysisService> AnalysisService = TraceServicesModule->GetAnalysisService();
	if (!AnalysisService.IsValid())
	{
		GLastAnalysisMessage = TEXT("Trace analysis service could not be created.");
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Material GPU Preview trace analysis skipped; %s"), *GLastAnalysisMessage);
		return false;
	}

	ClearMaterialReplayDerivedCaches();
	const double AnalyzeStartTime = FPlatformTime::Seconds();
	TSharedPtr<const TraceServices::IAnalysisSession> Session = AnalysisService->Analyze(*GTraceFilePath);
	const double TraceAnalyzeSeconds = FPlatformTime::Seconds() - AnalyzeStartTime;
	if (!Session.IsValid())
	{
		GLastAnalysisMessage = FString::Printf(TEXT("Trace analysis failed: %s"), *GTraceFilePath);
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Material GPU Preview %s"), *GLastAnalysisMessage);
		return false;
	}

	const double SceneBuildStartTime = FPlatformTime::Seconds();
	TArray<FMaterialAccumulator> SceneRows;
	BuildSceneMaterialAccumulators(World, SceneRows);
	SortMaterialAccumulators(SceneRows);

	TMap<FString, int32> SceneLookup;
	for (int32 Index = 0; Index < SceneRows.Num(); ++Index)
	{
		AddMaterialLookupKeys(SceneLookup, SceneRows[Index], Index);
	}
	const double SceneBuildSeconds = FPlatformTime::Seconds() - SceneBuildStartTime;

	TMap<FString, FTraceMaterialAggregate> AggregatesByMaterial;
	TMap<uint32, FMaterialGpuReplayFrameSample> ReplaySamplesByFrame;
	TMap<uint32, TArray<FFrameGpuInterval>> FrameGpuIntervalsByFrame;
	TArray<FMaterialReplayUnitGpuSample> CounterUnitGpuSamples;
	TArray<FString> TraceDiagnosticSamples;
	TSet<FString> SeenTraceDiagnosticSamples;
	TMap<FString, FString> ResolvedMaterialNameCache;
	TSet<FString> UnresolvedMaterialNameCache;
	uint64 FrameCount = 0;
	int32 GpuQueueCount = 0;
	int32 InspectedGpuEventCount = 0;
	int32 MaterialDrawEventCount = 0;
	int32 MatchedTraceEventCount = 0;
	int32 MaterialResolveCacheHits = 0;
	int32 MaterialResolveCacheMisses = 0;
	double GpuEnumerateSeconds = 0.0;
	double CounterEnumerateSeconds = 0.0;

	{
		TraceServices::FAnalysisSessionReadScope SessionReadScope(*Session);

		const TraceServices::ITimingProfilerProvider* TimingProfilerProvider = TraceServices::ReadTimingProfilerProvider(*Session);
		if (!TimingProfilerProvider)
		{
			GLastAnalysisMessage = TEXT("TimingProfilerProvider is unavailable.");
			UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Material GPU Preview trace analysis failed; %s"), *GLastAnalysisMessage);
			return false;
		}

		const TraceServices::IFrameProvider& FrameProvider = TraceServices::ReadFrameProvider(*Session);
		ETraceFrameType FrameType = TraceFrameType_Rendering;
		FrameCount = FrameProvider.GetFrameCount(FrameType);
		if (FrameCount == 0)
		{
			FrameType = TraceFrameType_Game;
			FrameCount = FrameProvider.GetFrameCount(FrameType);
		}
		FrameCount = FMath::Max<uint64>(FrameCount, 1);
		GLastTraceFrameCount = FrameCount;

		auto AddTotalGpuInterval = [&](uint32 FrameIndex, double EventStartTime, double EventEndTime)
		{
			const TraceServices::FFrame* Frame = FrameProvider.GetFrame(FrameType, FrameIndex);
			if (!Frame)
			{
				return;
			}

			const double ClippedStartTime = FMath::Max(EventStartTime, Frame->StartTime);
			const double ClippedEndTime = FMath::Min(EventEndTime, Frame->EndTime);
			if (ClippedEndTime <= ClippedStartTime)
			{
				return;
			}

			FFrameGpuInterval& Interval = FrameGpuIntervalsByFrame.FindOrAdd(FrameIndex).AddDefaulted_GetRef();
			Interval.StartTimeSeconds = ClippedStartTime;
			Interval.EndTimeSeconds = ClippedEndTime;
		};

		const double GpuEnumerateStartTime = FPlatformTime::Seconds();
		TimingProfilerProvider->ReadTimers(
			[&](const TraceServices::ITimingProfilerTimerReader& TimerReader)
			{
				TSet<uint32> VisitedTimelineIndices;

				auto AccumulateTimeline = [&](const TraceServices::ITimingProfilerProvider::Timeline& Timeline)
				{
					Timeline.EnumerateEvents(0.0, Session->GetDurationSeconds(),
						[&](double EventStartTime, double EventEndTime, uint32 EventDepth, const TraceServices::FTimingProfilerEvent& Event)
						{
							if (EventEndTime <= EventStartTime)
							{
								return TraceServices::EEventEnumerate::Continue;
							}

							FString BaseTimerName;
							const FString TraceEventName = GetTraceTimerName(*TimingProfilerProvider, TimerReader, Event.TimerIndex, &BaseTimerName);
							if (BaseTimerName.Equals(TEXT("MaterialDrawEvent"), ESearchCase::CaseSensitive))
							{
								MaterialDrawEventCount++;
							}

							const double DurationMs = (EventEndTime - EventStartTime) * 1000.0;
							const uint32 FrameIndex = FrameProvider.GetFrameNumberForTimestamp(FrameType, EventStartTime);
							const uint32 EndFrameIndex = FrameProvider.GetFrameNumberForTimestamp(FrameType, FMath::Max(EventStartTime, EventEndTime - 0.000000001));
							if (EndFrameIndex >= FrameIndex && EndFrameIndex - FrameIndex <= 512)
							{
								for (uint32 SplitFrameIndex = FrameIndex; SplitFrameIndex <= EndFrameIndex; ++SplitFrameIndex)
								{
									AddTotalGpuInterval(SplitFrameIndex, EventStartTime, EventEndTime);
								}
							}
							else
							{
								AddTotalGpuInterval(FrameIndex, EventStartTime, EventEndTime);
							}

							InspectedGpuEventCount++;
							if (TraceDiagnosticSamples.Num() < 24)
							{
								const FString TrimmedEventName = TraceEventName.Left(180);
								AddTraceDiagnosticSample(
									TraceDiagnosticSamples,
									SeenTraceDiagnosticSamples,
									FString::Printf(TEXT("%s | %s | %.3fms"), *BaseTimerName, *TrimmedEventName, DurationMs));
							}

							const FString MaterialName = FindMaterialNameForTraceEventCached(
								SceneRows,
								SceneLookup,
								TraceEventName,
								BaseTimerName,
								ResolvedMaterialNameCache,
								UnresolvedMaterialNameCache,
								MaterialResolveCacheHits,
								MaterialResolveCacheMisses);
							if (MaterialName.IsEmpty())
							{
								return TraceServices::EEventEnumerate::Continue;
							}

							const FString MaterialKey = NormalizeTraceLookupKey(MaterialName);
							FTraceMaterialAggregate& Aggregate = AggregatesByMaterial.FindOrAdd(MaterialKey);
							if (Aggregate.MaterialName.IsEmpty())
							{
								Aggregate.MaterialName = MaterialName;
							}
							Aggregate.EventName = TraceEventName;
							Aggregate.TotalGpuMs += DurationMs;
							Aggregate.DrawEvents++;
							Aggregate.GpuMsByFrame.FindOrAdd(FrameIndex) += DurationMs;

							FMaterialGpuReplayFrameSample& ReplaySample = ReplaySamplesByFrame.FindOrAdd(FrameIndex);
							ReplaySample.TraceFrameIndex = FrameIndex;
							if (const TraceServices::FFrame* Frame = FrameProvider.GetFrame(FrameType, FrameIndex))
							{
								ReplaySample.TimeSeconds = Frame->StartTime;
								ReplaySample.EndTimeSeconds = Frame->EndTime;
							}
							else
							{
								ReplaySample.TimeSeconds = EventStartTime;
								ReplaySample.EndTimeSeconds = EventEndTime;
							}
							ReplaySample.MaterialGpuMsByKey.FindOrAdd(MaterialKey) += static_cast<float>(DurationMs);
							ReplaySample.MaterialDrawEventsByKey.FindOrAdd(MaterialKey)++;
							MatchedTraceEventCount++;

							return TraceServices::EEventEnumerate::Continue;
						});
				};

				auto AccumulateTimelineIndex = [&](uint32 TimelineIndex)
				{
					if (TimelineIndex == ~0u
						|| TimelineIndex >= TimingProfilerProvider->GetTimelineCount()
						|| VisitedTimelineIndices.Contains(TimelineIndex))
					{
						return;
					}

					VisitedTimelineIndices.Add(TimelineIndex);
					TimingProfilerProvider->ReadTimeline(TimelineIndex, AccumulateTimeline);
				};

				uint32 OldGpuTimelineIndex = 0;
				if (TimingProfilerProvider->GetGpuTimelineIndex(OldGpuTimelineIndex))
				{
					AccumulateTimelineIndex(OldGpuTimelineIndex);
				}

				uint32 OldGpu2TimelineIndex = 0;
				if (TimingProfilerProvider->GetGpu2TimelineIndex(OldGpu2TimelineIndex))
				{
					AccumulateTimelineIndex(OldGpu2TimelineIndex);
				}

				TimingProfilerProvider->EnumerateGpuQueues(
					[&](const TraceServices::FGpuQueueInfo& QueueInfo)
					{
						GpuQueueCount++;
						AccumulateTimelineIndex(QueueInfo.TimelineIndex);
						AccumulateTimelineIndex(QueueInfo.WorkTimelineIndex);
					});
			});
		GpuEnumerateSeconds = FPlatformTime::Seconds() - GpuEnumerateStartTime;

		const double CounterEnumerateStartTime = FPlatformTime::Seconds();
		const TraceServices::ICounterProvider& CounterProvider = TraceServices::ReadCounterProvider(*Session);
		CounterProvider.EnumerateCounters(
			[&](uint32 CounterId, const TraceServices::ICounter& Counter)
			{
				if (!Counter.IsFloatingPoint() || FCString::Stricmp(Counter.GetName(), TEXT("MaterialGPU/UnitGPU")) != 0)
				{
					return;
				}

				Counter.EnumerateFloatValues(0.0, Session->GetDurationSeconds(), true,
					[&](double TimeSeconds, double Value)
					{
						if (!FMath::IsFinite(TimeSeconds) || !FMath::IsFinite(Value) || Value <= 0.0)
						{
							return;
						}

						FMaterialReplayUnitGpuSample& Sample = CounterUnitGpuSamples.AddDefaulted_GetRef();
						Sample.TimeSeconds = TimeSeconds;
						Sample.GpuMs = static_cast<float>(Value);
						Sample.bFromStatUnitData = true;
					});
			});
		CounterEnumerateSeconds = FPlatformTime::Seconds() - CounterEnumerateStartTime;
	}

	if (AggregatesByMaterial.Num() == 0)
	{
		GMaterialReplaySamples.Reset();
		GMaterialReplayCurrentRows.Reset();
		GMaterialReplayCurrentRowsAll.Reset();
		GMaterialReplayDebugRows.Reset();
		GMaterialReplayCharacterSamples.Reset();
		GMaterialReplayFrameGpuMs.Reset();
		GMaterialReplayFrameGpuMsMax = 0.0f;
		ClearMaterialReplayDerivedCaches();
		GMaterialReplayActive = false;
		GMaterialReplayPlaying = false;
		GLastAnalysisMessage = FString::Printf(TEXT("No material GPU scopes found. Trace=%s Queues=%d InspectedEvents=%d MaterialDrawEvents=%d MatchedEvents=%d SceneMaterials=%d"),
			*GTraceFilePath,
			GpuQueueCount,
			InspectedGpuEventCount,
			MaterialDrawEventCount,
			MatchedTraceEventCount,
			SceneRows.Num());
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Material GPU Preview trace analysis found no material GPU scopes. Trace=%s Queues=%d InspectedEvents=%d MaterialDrawEvents=%d MatchedEvents=%d SceneMaterials=%d"),
			*GTraceFilePath,
			GpuQueueCount,
			InspectedGpuEventCount,
			MaterialDrawEventCount,
			MatchedTraceEventCount,
			SceneRows.Num());

		for (int32 SampleIndex = 0; SampleIndex < TraceDiagnosticSamples.Num(); ++SampleIndex)
		{
			UE_LOG(LogOptimizationPreviewTools, Verbose, TEXT("Material GPU Preview GPU event sample %02d: %s"),
				SampleIndex + 1,
				*TraceDiagnosticSamples[SampleIndex]);
		}

		return false;
	}

	const double PostProcessStartTime = FPlatformTime::Seconds();
	for (TPair<uint32, FMaterialGpuReplayFrameSample>& Pair : ReplaySamplesByFrame)
	{
		if (TArray<FFrameGpuInterval>* Intervals = FrameGpuIntervalsByFrame.Find(Pair.Key))
		{
			Pair.Value.TotalFrameGpuMs = static_cast<float>(CalculateMergedGpuIntervalDurationMs(*Intervals));
			Pair.Value.bHasTotalFrameGpuMs = Pair.Value.TotalFrameGpuMs > 0.0f;
		}
	}

	TArray<FTraceMaterialAggregate> TraceAggregates;
	AggregatesByMaterial.GenerateValueArray(TraceAggregates);
	for (FTraceMaterialAggregate& Aggregate : TraceAggregates)
	{
		for (const TPair<uint32, double>& Pair : Aggregate.GpuMsByFrame)
		{
			Aggregate.PeakFrameGpuMs = FMath::Max(Aggregate.PeakFrameGpuMs, Pair.Value);
		}
		Aggregate.AverageFrameGpuMs = Aggregate.TotalGpuMs / static_cast<double>(FrameCount);
	}

	TraceAggregates.Sort([](const FTraceMaterialAggregate& A, const FTraceMaterialAggregate& B)
	{
		if (A.PeakFrameGpuMs == B.PeakFrameGpuMs)
		{
			return A.TotalGpuMs > B.TotalGpuMs;
		}

		return A.PeakFrameGpuMs > B.PeakFrameGpuMs;
	});

	GMaterialReplaySceneRows = SceneRows;
	GMaterialReplaySceneLookup = SceneLookup;
	GMaterialReplaySamples.Reset();
	ReplaySamplesByFrame.GenerateValueArray(GMaterialReplaySamples);
	GMaterialReplaySamples.RemoveAll([](const FMaterialGpuReplayFrameSample& Sample)
	{
		return !FMath::IsFinite(Sample.TimeSeconds);
	});
	GMaterialReplaySamples.Sort([](const FMaterialGpuReplayFrameSample& A, const FMaterialGpuReplayFrameSample& B)
	{
		if (!FMath::IsNearlyEqual(A.TimeSeconds, B.TimeSeconds))
		{
			return A.TimeSeconds < B.TimeSeconds;
		}
		return A.TraceFrameIndex < B.TraceFrameIndex;
	});
	if (CounterUnitGpuSamples.Num() > 0)
	{
		CounterUnitGpuSamples.Sort([](const FMaterialReplayUnitGpuSample& A, const FMaterialReplayUnitGpuSample& B)
		{
			return A.TimeSeconds < B.TimeSeconds;
		});

		for (FMaterialGpuReplayFrameSample& Sample : GMaterialReplaySamples)
		{
			const float CounterGpuMs = FindNearestMaterialReplayUnitGpuMs(CounterUnitGpuSamples, Sample.TimeSeconds);
			if (CounterGpuMs > 0.0f)
			{
				Sample.TotalFrameGpuMs = CounterGpuMs;
				Sample.bHasTotalFrameGpuMs = true;
			}
		}
	}
	if (GMaterialReplaySamples.Num() > 0)
	{
		const double ReplayStartTime = GMaterialReplaySamples[0].TimeSeconds;
		for (int32 SampleIndex = 0; SampleIndex < GMaterialReplaySamples.Num(); ++SampleIndex)
		{
			FMaterialGpuReplayFrameSample& Sample = GMaterialReplaySamples[SampleIndex];
			if (!FMath::IsFinite(Sample.EndTimeSeconds) || Sample.EndTimeSeconds <= Sample.TimeSeconds)
			{
				Sample.EndTimeSeconds = GMaterialReplaySamples.IsValidIndex(SampleIndex + 1)
					? GMaterialReplaySamples[SampleIndex + 1].TimeSeconds
					: Sample.TimeSeconds + (1.0 / 60.0);
			}

			Sample.TimeSeconds = FMath::Max(0.0, Sample.TimeSeconds - ReplayStartTime);
			Sample.EndTimeSeconds = FMath::Max(Sample.TimeSeconds, Sample.EndTimeSeconds - ReplayStartTime);
			if (!FMath::IsFinite(Sample.EndTimeSeconds))
			{
				Sample.EndTimeSeconds = Sample.TimeSeconds + (1.0 / 60.0);
			}
		}
	}
	if (GMaterialReplayUnitGpuSamples.Num() > 0)
	{
		for (FMaterialGpuReplayFrameSample& Sample : GMaterialReplaySamples)
		{
			const float StatUnitGpuMs = GetMaterialReplayUnitGpuMsForTime(Sample.TimeSeconds);
			if (StatUnitGpuMs > 0.0f)
			{
				Sample.TotalFrameGpuMs = StatUnitGpuMs;
				Sample.bHasTotalFrameGpuMs = true;
			}
		}
	}
	RebuildMaterialReplayFrameGpuMs();
	GMaterialReplayCurrentRows.Reset();
	GMaterialReplayCurrentRowsAll.Reset();
	GMaterialReplayDebugRows.Reset();
	GMaterialReplayActive = false;
	GMaterialReplayPlaying = false;
	GMaterialReplayScrubbing = false;
	GMaterialReplayCurrentTimeSeconds = 0.0;
	GMaterialReplayLastTickSeconds = -1.0;
	GMaterialReplayCurrentSampleIndex = INDEX_NONE;

	GCachedRows.Reset();
	GCachedRowsAll.Reset();
	GCachedDebugRows.Reset();
	const int32 TopN = FMath::Clamp(CVarTopN.GetValueOnGameThread(), 1, 50);
	for (int32 Index = 0; Index < TraceAggregates.Num(); ++Index)
	{
		const FTraceMaterialAggregate& Aggregate = TraceAggregates[Index];
		FMaterialAccumulator Row;
		bool bMatchedSceneMaterial = false;

		const int32 SceneIndex = FindSceneMaterialIndex(SceneRows, SceneLookup, Aggregate.MaterialName);
		if (SceneRows.IsValidIndex(SceneIndex))
		{
			Row = SceneRows[SceneIndex];
			bMatchedSceneMaterial = Row.Components.Num() > 0;
		}
		else
		{
			Row.DisplayName = Aggregate.MaterialName;
			Row.PathName = Aggregate.MaterialName;
		}

		Row.MaxGpuMs = static_cast<float>(Aggregate.PeakFrameGpuMs);
		Row.AvgGpuMs = static_cast<float>(Aggregate.AverageFrameGpuMs);
		Row.TraceDrawEvents = Aggregate.DrawEvents;
		if (bMatchedSceneMaterial)
		{
			GCachedRowsAll.Add(Row);
			if (GCachedRows.Num() < TopN)
			{
				GCachedRows.Add(Row);
			}
		}
		if (bMatchedSceneMaterial)
		{
			GCachedDebugRows.Add(MoveTemp(Row));
		}
	}

	GLastDebugMaterialCount = GCachedDebugRows.Num();
	GLastDebugComponentCount = CountUniqueDebugComponents(GCachedDebugRows);
	const double PostProcessSeconds = FPlatformTime::Seconds() - PostProcessStartTime;

	GLastAnalysisMessage = FString::Printf(TEXT("Insights rows=%d/%d debugMaterials=%d debugComps=%d frames=%llu materialEvents=%d trace=%s"),
		GCachedRows.Num(),
		GCachedRowsAll.Num(),
		GLastDebugMaterialCount,
		GLastDebugComponentCount,
		static_cast<unsigned long long>(FrameCount),
		MaterialDrawEventCount,
		*GTraceFilePath);

	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Material GPU Preview trace analysis timings. TraceAnalyze=%.2fs Scene=%.2fs GpuEvents=%.2fs Counters=%.2fs Post=%.2fs ResolveCache=%d/%d Trace=%s"),
		TraceAnalyzeSeconds,
		SceneBuildSeconds,
		GpuEnumerateSeconds,
		CounterEnumerateSeconds,
		PostProcessSeconds,
		MaterialResolveCacheHits,
		MaterialResolveCacheHits + MaterialResolveCacheMisses,
		*GTraceFilePath);

	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Material GPU Preview trace analysis complete. Rows=%d/%d TraceMaterials=%d DebugMaterials=%d DebugComponents=%d InspectedEvents=%d MaterialDrawEvents=%d MatchedEvents=%d Frames=%llu Queues=%d Analyze=%.2fs Trace=%s"),
		GCachedRows.Num(),
		GCachedRowsAll.Num(),
		TraceAggregates.Num(),
		GLastDebugMaterialCount,
		GLastDebugComponentCount,
		InspectedGpuEventCount,
		MaterialDrawEventCount,
		MatchedTraceEventCount,
		static_cast<unsigned long long>(FrameCount),
		GpuQueueCount,
		FPlatformTime::Seconds() - AnalyzeStartTime,
		*GTraceFilePath);

	return GCachedRows.Num() > 0;
}

static bool IsMaterialReplayCameraActor(const AActor* Actor)
{
	return Actor && Actor->ActorHasTag(MaterialReplayCameraTag);
}

static APlayerController* FindMaterialReplayPlayerController(UWorld* World)
{
	if (!World)
	{
		return nullptr;
	}

	if (APlayerController* PlayerController = World->GetFirstPlayerController())
	{
		return PlayerController;
	}

	return nullptr;
}

static UCameraComponent* FindCameraComponentOnActor(AActor* Actor)
{
	if (!Actor || IsMaterialReplayCameraActor(Actor))
	{
		return nullptr;
	}

	TInlineComponentArray<UCameraComponent*> CameraComponents;
	Actor->GetComponents(CameraComponents);
	for (UCameraComponent* CameraComponent : CameraComponents)
	{
		if (CameraComponent && CameraComponent->IsRegistered() && CameraComponent->IsActive())
		{
			return CameraComponent;
		}
	}

	for (UCameraComponent* CameraComponent : CameraComponents)
	{
		if (CameraComponent && CameraComponent->IsRegistered())
		{
			return CameraComponent;
		}
	}

	return nullptr;
}

static UCameraComponent* FindMaterialReplaySourceCamera(UWorld* World, APlayerController* PlayerController)
{
	if (!World || !PlayerController)
	{
		return nullptr;
	}

	if (APawn* Pawn = PlayerController->GetPawn())
	{
		if (UCameraComponent* PawnCamera = FindCameraComponentOnActor(Pawn))
		{
			return PawnCamera;
		}
	}

	if (AActor* ViewTarget = PlayerController->GetViewTarget())
	{
		if (UCameraComponent* ViewTargetCamera = FindCameraComponentOnActor(ViewTarget))
		{
			return ViewTargetCamera;
		}
	}

	return nullptr;
}

static ACharacter* FindMaterialReplayCharacter(UWorld* World, APlayerController* PlayerController)
{
	if (!World || !PlayerController)
	{
		return nullptr;
	}

	return Cast<ACharacter>(PlayerController->GetPawn());
}

static void CopyMaterialReplayCameraSettings(UCameraComponent* SourceCamera, UCameraComponent* TargetCamera)
{
	if (!SourceCamera || !TargetCamera)
	{
		return;
	}

	TargetCamera->SetFieldOfView(SourceCamera->FieldOfView);
	TargetCamera->SetProjectionMode(SourceCamera->ProjectionMode);
	TargetCamera->SetOrthoWidth(SourceCamera->OrthoWidth);
	TargetCamera->SetAspectRatio(SourceCamera->AspectRatio);
	TargetCamera->SetConstraintAspectRatio(SourceCamera->bConstrainAspectRatio);
	TargetCamera->SetAspectRatioAxisConstraint(SourceCamera->AspectRatioAxisConstraint);
	TargetCamera->bOverrideAspectRatioAxisConstraint = SourceCamera->bOverrideAspectRatioAxisConstraint;
	TargetCamera->bUseFieldOfViewForLOD = SourceCamera->bUseFieldOfViewForLOD;
	TargetCamera->PostProcessSettings = SourceCamera->PostProcessSettings;
	TargetCamera->SetPostProcessBlendWeight(SourceCamera->PostProcessBlendWeight);
}

static void ApplyMaterialReplayViewInfo(const FMinimalViewInfo& ViewInfo, UCameraComponent* TargetCamera)
{
	if (!TargetCamera)
	{
		return;
	}

	TargetCamera->SetFieldOfView(ViewInfo.FOV);
	TargetCamera->SetProjectionMode(ViewInfo.ProjectionMode);
	TargetCamera->SetOrthoWidth(ViewInfo.OrthoWidth);
	TargetCamera->SetAspectRatio(ViewInfo.AspectRatio);
	TargetCamera->SetConstraintAspectRatio(ViewInfo.bConstrainAspectRatio);
	TargetCamera->PostProcessSettings = ViewInfo.PostProcessSettings;
	TargetCamera->SetPostProcessBlendWeight(ViewInfo.PostProcessBlendWeight);
}

static bool CaptureMaterialReplayCameraSample(UWorld* World, double TimeSeconds)
{
	APlayerController* PlayerController = FindMaterialReplayPlayerController(World);
	UCameraComponent* SourceCamera = FindMaterialReplaySourceCamera(World, PlayerController);
	if (!World || !PlayerController || !SourceCamera)
	{
		return false;
	}

	FMaterialReplayCameraSample Sample;
	Sample.TimeSeconds = FMath::Max(0.0, TimeSeconds);
	SourceCamera->GetCameraView(0.0f, Sample.ViewInfo);
	Sample.Transform = FTransform(Sample.ViewInfo.Rotation, Sample.ViewInfo.Location);
	GMaterialReplayCameraSamples.Add(MoveTemp(Sample));
	return true;
}

static bool CaptureMaterialReplayCharacterSample(UWorld* World, double TimeSeconds)
{
	APlayerController* PlayerController = FindMaterialReplayPlayerController(World);
	ACharacter* Character = FindMaterialReplayCharacter(World, PlayerController);
	if (!World || !PlayerController || !Character)
	{
		return false;
	}

	FMaterialReplayCharacterSample Sample;
	Sample.TimeSeconds = FMath::Max(0.0, TimeSeconds);
	Sample.Character = Character;
	Sample.Transform = Character->GetActorTransform();
	Sample.Velocity = Character->GetVelocity();
	Sample.ControlRotation = PlayerController->GetControlRotation();
	Sample.bHasControlRotation = true;

	if (UCharacterMovementComponent* CharacterMovement = Character->GetCharacterMovement())
	{
		Sample.Velocity = CharacterMovement->Velocity;
		Sample.MovementMode = CharacterMovement->MovementMode;
		Sample.CustomMovementMode = CharacterMovement->CustomMovementMode;
		Sample.bHasMovementMode = true;
	}

	if (USkeletalMeshComponent* MeshComponent = Character->GetMesh())
	{
		if (UAnimInstance* AnimInstance = MeshComponent->GetAnimInstance())
		{
			if (UAnimMontage* ActiveMontage = AnimInstance->GetCurrentActiveMontage())
			{
				Sample.ActiveMontage = ActiveMontage;
				Sample.MontagePosition = AnimInstance->Montage_GetPosition(ActiveMontage);
				Sample.MontagePlayRate = AnimInstance->Montage_GetPlayRate(ActiveMontage);
				Sample.bHasMontage = true;
			}
		}
	}

	GMaterialReplayCharacterSamples.Add(MoveTemp(Sample));
	return true;
}

static void CaptureMaterialReplayUnitGpuSample(UWorld* World, double TimeSeconds)
{
	bool bFromStatUnitData = false;
	const float GpuMs = ReadCurrentStatUnitGpuMs(World, bFromStatUnitData);
	if (!FMath::IsFinite(GpuMs) || GpuMs <= 0.0f)
	{
		return;
	}

	FMaterialReplayUnitGpuSample Sample;
	Sample.TimeSeconds = FMath::Max(0.0, TimeSeconds);
	Sample.GpuMs = GpuMs;
	Sample.bFromStatUnitData = bFromStatUnitData;
	GMaterialReplayUnitGpuSamples.Add(Sample);

	if (ShouldEmitMaterialGPUUnitGpuCounter())
	{
		TRACE_COUNTER_SET_ALWAYS(MaterialGPUUnitGPU, static_cast<double>(GpuMs));
	}
}

static bool TickMaterialReplayCameraCapture(float DeltaTime)
{
	UWorld* World = GMaterialReplayCameraCaptureWorld.Get();
	if (!GCaptureActive || !World || GCaptureStartTime < 0.0)
	{
		GMaterialReplayCameraCaptureTickerHandle.Reset();
		return false;
	}

	const double CaptureTimeSeconds = FPlatformTime::Seconds() - GCaptureStartTime;
	CaptureMaterialReplayCameraSample(World, CaptureTimeSeconds);
	CaptureMaterialReplayCharacterSample(World, CaptureTimeSeconds);
	CaptureMaterialReplayUnitGpuSample(World, CaptureTimeSeconds);
	return true;
}

static void StopMaterialReplayCameraCaptureTicker()
{
	if (GMaterialReplayCameraCaptureTickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(GMaterialReplayCameraCaptureTickerHandle);
		GMaterialReplayCameraCaptureTickerHandle.Reset();
	}

	if (UWorld* World = GMaterialReplayCameraCaptureWorld.Get())
	{
		const double EndTime = GCaptureEndTime >= 0.0 ? GCaptureEndTime : FPlatformTime::Seconds();
		if (GCaptureStartTime >= 0.0)
		{
			const double CaptureTimeSeconds = EndTime - GCaptureStartTime;
			CaptureMaterialReplayCameraSample(World, CaptureTimeSeconds);
			CaptureMaterialReplayCharacterSample(World, CaptureTimeSeconds);
			CaptureMaterialReplayUnitGpuSample(World, CaptureTimeSeconds);
		}
	}

	GMaterialReplayCameraCaptureWorld = nullptr;
}

static void StartMaterialReplayCameraCapture(UWorld* World)
{
	StopMaterialReplayCameraCaptureTicker();
	GMaterialReplayCameraSamples.Reset();
	GMaterialReplayCharacterSamples.Reset();
	GMaterialReplayUnitGpuSamples.Reset();
	ClearMaterialReplayDerivedCaches();
	GMaterialReplayCameraCaptureWorld = World;
	if (!World || GCaptureStartTime < 0.0)
	{
		return;
	}

	CaptureMaterialReplayCameraSample(World, 0.0);
	CaptureMaterialReplayCharacterSample(World, 0.0);
	CaptureMaterialReplayUnitGpuSample(World, 0.0);
	GMaterialReplayCameraCaptureTickerHandle = FTSTicker::GetCoreTicker().AddTicker(
		FTickerDelegate::CreateStatic(&TickMaterialReplayCameraCapture),
		0.0f);
}

static int32 FindMaterialReplayCameraSampleIndexForTime(double TimeSeconds)
{
	if (GMaterialReplayCameraSamples.Num() == 0)
	{
		return INDEX_NONE;
	}

	const double ClampedTime = FMath::Max(0.0, TimeSeconds);
	int32 BestIndex = 0;
	for (int32 SampleIndex = 0; SampleIndex < GMaterialReplayCameraSamples.Num(); ++SampleIndex)
	{
		if (GMaterialReplayCameraSamples[SampleIndex].TimeSeconds > ClampedTime)
		{
			break;
		}
		BestIndex = SampleIndex;
	}

	return BestIndex;
}

static bool ApplyMaterialReplayCameraSample(ACameraActor* CameraActor, double TimeSeconds)
{
	if (!CameraActor || GMaterialReplayCameraSamples.Num() == 0)
	{
		return false;
	}

	const int32 SampleIndex = FindMaterialReplayCameraSampleIndexForTime(TimeSeconds);
	if (!GMaterialReplayCameraSamples.IsValidIndex(SampleIndex))
	{
		return false;
	}

	const FMaterialReplayCameraSample& Sample = GMaterialReplayCameraSamples[SampleIndex];
	CameraActor->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
	CameraActor->SetActorTransform(Sample.Transform);
	ApplyMaterialReplayViewInfo(Sample.ViewInfo, CameraActor->GetCameraComponent());
	return true;
}

static FMaterialReplayAnimationState& FindOrAddMaterialReplayAnimationState(USkeletalMeshComponent* MeshComponent)
{
	FMaterialReplayAnimationState& State = GMaterialReplayAnimationStates.FindOrAdd(FObjectKey(MeshComponent));
	if (!State.MeshComponent.IsValid())
	{
		State.MeshComponent = MeshComponent;
		State.bPauseAnims = MeshComponent->bPauseAnims;
		State.GlobalAnimRateScale = MeshComponent->GlobalAnimRateScale;
	}
	return State;
}

static void SetMaterialReplayMeshAnimationFrozen(USkeletalMeshComponent* MeshComponent, bool bFreezeAnimation)
{
	if (!MeshComponent)
	{
		return;
	}

	FMaterialReplayAnimationState& State = FindOrAddMaterialReplayAnimationState(MeshComponent);
	if (bFreezeAnimation)
	{
		MeshComponent->GlobalAnimRateScale = 0.0f;
		MeshComponent->bPauseAnims = true;
	}
	else
	{
		MeshComponent->GlobalAnimRateScale = State.GlobalAnimRateScale;
		MeshComponent->bPauseAnims = State.bPauseAnims;
	}
}

static void RestoreMaterialReplayAnimationStates()
{
	for (TPair<FObjectKey, FMaterialReplayAnimationState>& Pair : GMaterialReplayAnimationStates)
	{
		if (USkeletalMeshComponent* MeshComponent = Pair.Value.MeshComponent.Get())
		{
			MeshComponent->bPauseAnims = Pair.Value.bPauseAnims;
			MeshComponent->GlobalAnimRateScale = Pair.Value.GlobalAnimRateScale;
		}
	}

	GMaterialReplayAnimationStates.Reset();
}

static int32 FindMaterialReplayCharacterSampleIndexForTime(double TimeSeconds)
{
	if (GMaterialReplayCharacterSamples.Num() == 0)
	{
		return INDEX_NONE;
	}

	const double ClampedTime = FMath::Max(0.0, TimeSeconds);
	int32 BestIndex = 0;
	for (int32 SampleIndex = 0; SampleIndex < GMaterialReplayCharacterSamples.Num(); ++SampleIndex)
	{
		if (GMaterialReplayCharacterSamples[SampleIndex].TimeSeconds > ClampedTime)
		{
			break;
		}
		BestIndex = SampleIndex;
	}

	return BestIndex;
}

static bool ApplyMaterialReplayCharacterSample(UWorld* World, double TimeSeconds, bool bSeedAnimationFromSample)
{
	if (!World || GMaterialReplayCharacterSamples.Num() == 0)
	{
		return false;
	}

	const int32 SampleIndex = FindMaterialReplayCharacterSampleIndexForTime(TimeSeconds);
	if (!GMaterialReplayCharacterSamples.IsValidIndex(SampleIndex))
	{
		return false;
	}

	const FMaterialReplayCharacterSample& Sample = GMaterialReplayCharacterSamples[SampleIndex];
	APlayerController* PlayerController = FindMaterialReplayPlayerController(World);
	ACharacter* Character = Sample.Character.Get();
	if (!Character || Character->GetWorld() != World)
	{
		Character = FindMaterialReplayCharacter(World, PlayerController);
	}

	if (!Character)
	{
		return false;
	}

	Character->SetActorTransform(Sample.Transform, false, nullptr, ETeleportType::TeleportPhysics);

	if (PlayerController && PlayerController->GetPawn() == Character && Sample.bHasControlRotation)
	{
		PlayerController->SetControlRotation(Sample.ControlRotation);
	}

	if (UCharacterMovementComponent* CharacterMovement = Character->GetCharacterMovement())
	{
		if (Sample.bHasMovementMode)
		{
			CharacterMovement->SetMovementMode(Sample.MovementMode.GetValue(), Sample.CustomMovementMode);
		}
		CharacterMovement->Velocity = Sample.Velocity;
		CharacterMovement->UpdateComponentVelocity();
	}

	if (USkeletalMeshComponent* MeshComponent = Character->GetMesh())
	{
		SetMaterialReplayMeshAnimationFrozen(MeshComponent, false);
		if (bSeedAnimationFromSample)
		{
			if (UAnimInstance* AnimInstance = MeshComponent->GetAnimInstance())
			{
				UAnimMontage* ActiveMontage = Sample.ActiveMontage.Get();
				if (Sample.bHasMontage && ActiveMontage)
				{
					const float ReplayMontagePlayRate = FMath::Max(Sample.MontagePlayRate, 0.001f);
					if (!AnimInstance->Montage_IsPlaying(ActiveMontage))
					{
						AnimInstance->Montage_Play(
							ActiveMontage,
							ReplayMontagePlayRate,
							EMontagePlayReturnType::MontageLength,
							Sample.MontagePosition,
							true);
					}
					AnimInstance->Montage_SetPlayRate(ActiveMontage, ReplayMontagePlayRate);
					AnimInstance->Montage_SetPosition(ActiveMontage, Sample.MontagePosition);
				}
				else if (AnimInstance->GetCurrentActiveMontage())
				{
					AnimInstance->Montage_Stop(0.0f);
				}
			}
		}
	}

	return true;
}

static void LockMaterialReplayPlayerInput(APlayerController* PlayerController)
{
	if (!PlayerController || GMaterialReplayInputLocked)
	{
		return;
	}

	GMaterialReplayPreviousLookInputIgnored = PlayerController->IsLookInputIgnored();
	GMaterialReplayPreviousMoveInputIgnored = PlayerController->IsMoveInputIgnored();
	if (!GMaterialReplayPreviousLookInputIgnored)
	{
		PlayerController->SetIgnoreLookInput(true);
	}
	if (!GMaterialReplayPreviousMoveInputIgnored)
	{
		PlayerController->SetIgnoreMoveInput(true);
	}
	GMaterialReplayInputLocked = true;
	GMaterialReplayInputPlayerController = PlayerController;
}

static void UnlockMaterialReplayPlayerInput()
{
	if (GMaterialReplayInputLocked)
	{
		if (APlayerController* PlayerController = GMaterialReplayInputPlayerController.Get())
		{
			if (!GMaterialReplayPreviousLookInputIgnored)
			{
				PlayerController->SetIgnoreLookInput(false);
			}
			if (!GMaterialReplayPreviousMoveInputIgnored)
			{
				PlayerController->SetIgnoreMoveInput(false);
			}
		}
	}

	GMaterialReplayInputLocked = false;
	GMaterialReplayPreviousLookInputIgnored = false;
	GMaterialReplayPreviousMoveInputIgnored = false;
	GMaterialReplayInputPlayerController = nullptr;
}

static void DestroyMaterialReplayCamera()
{
	UnlockMaterialReplayPlayerInput();

	APlayerController* PlayerController = GMaterialReplayViewPlayerController.Get();
	ACameraActor* CameraActor = GMaterialReplayCameraActor.Get();
	if (CameraActor)
	{
		if (!PlayerController)
		{
			PlayerController = FindMaterialReplayPlayerController(CameraActor->GetWorld());
		}

		if (PlayerController && PlayerController->GetViewTarget() == CameraActor)
		{
			AActor* RestoreTarget = GMaterialReplayPreviousViewTarget.Get();
			if (!RestoreTarget)
			{
				RestoreTarget = PlayerController->GetPawn();
			}

			if (RestoreTarget && RestoreTarget != CameraActor)
			{
				PlayerController->SetViewTarget(RestoreTarget);
			}
		}

		CameraActor->Destroy();
	}

	GMaterialReplayCameraActor = nullptr;
	GMaterialReplaySourceCameraComponent = nullptr;
	GMaterialReplayViewPlayerController = nullptr;
	GMaterialReplayPreviousViewTarget = nullptr;
}

static bool EnsureMaterialReplayCamera(UWorld* World)
{
	if (!World || !GMaterialReplayActive)
	{
		DestroyMaterialReplayCamera();
		return false;
	}

	APlayerController* PlayerController = FindMaterialReplayPlayerController(World);
	UCameraComponent* SourceCamera = FindMaterialReplaySourceCamera(World, PlayerController);
	if (!PlayerController)
	{
		DestroyMaterialReplayCamera();
		return false;
	}

	ACameraActor* CameraActor = GMaterialReplayCameraActor.Get();
	if (!CameraActor || CameraActor->GetWorld() != World || (GMaterialReplayCameraSamples.Num() == 0 && GMaterialReplaySourceCameraComponent.Get() != SourceCamera))
	{
		DestroyMaterialReplayCamera();

		FActorSpawnParameters SpawnParameters;
		SpawnParameters.Name = MakeUniqueObjectName(World, ACameraActor::StaticClass(), TEXT("OptimizationPreviewToolsReplayCamera"));
		SpawnParameters.ObjectFlags |= RF_Transient;
		SpawnParameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		const FTransform FallbackTransform(
			PlayerController->GetControlRotation(),
			PlayerController->GetPawn() ? PlayerController->GetPawn()->GetActorLocation() : FVector::ZeroVector);
		const FTransform SpawnTransform = GMaterialReplayCameraSamples.Num() > 0
			? GMaterialReplayCameraSamples[0].Transform
			: (SourceCamera ? SourceCamera->GetComponentTransform() : FallbackTransform);
		CameraActor = World->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), SpawnTransform, SpawnParameters);
		if (!CameraActor)
		{
			return false;
		}

		CameraActor->Tags.AddUnique(MaterialReplayCameraTag);
		CameraActor->SetActorEnableCollision(false);
		CameraActor->SetActorHiddenInGame(true);
		if (SourceCamera && GMaterialReplayCameraSamples.Num() == 0)
		{
			CameraActor->AttachToComponent(SourceCamera, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
			CameraActor->SetActorRelativeTransform(FTransform::Identity);
		}
		GMaterialReplayCameraActor = CameraActor;
		GMaterialReplaySourceCameraComponent = SourceCamera;
	}

	if (!ApplyMaterialReplayCameraSample(CameraActor, GMaterialReplayCurrentTimeSeconds) && SourceCamera)
	{
		if (UCameraComponent* TargetCamera = CameraActor->GetCameraComponent())
		{
			CopyMaterialReplayCameraSettings(SourceCamera, TargetCamera);
		}

		CameraActor->AttachToComponent(SourceCamera, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
		CameraActor->SetActorRelativeTransform(FTransform::Identity);
	}

	if (GMaterialReplayViewPlayerController.Get() != PlayerController)
	{
		GMaterialReplayViewPlayerController = PlayerController;
		GMaterialReplayPreviousViewTarget = PlayerController->GetViewTarget() != CameraActor
			? PlayerController->GetViewTarget()
			: PlayerController->GetPawn();
	}

	if (PlayerController->GetViewTarget() != CameraActor)
	{
		PlayerController->SetViewTarget(CameraActor);
	}
	LockMaterialReplayPlayerInput(PlayerController);

	return true;
}

static double GetMaterialReplayDurationSeconds()
{
	if (GMaterialReplaySamples.Num() == 0)
	{
		return 0.0;
	}

	const FMaterialGpuReplayFrameSample& LastSample = GMaterialReplaySamples.Last();
	const double LastEndTime = FMath::IsFinite(LastSample.EndTimeSeconds) ? LastSample.EndTimeSeconds : 0.0;
	const double LastStartTime = FMath::IsFinite(LastSample.TimeSeconds) ? LastSample.TimeSeconds : 0.0;
	return FMath::Max(0.001, FMath::Max(LastEndTime, LastStartTime));
}

static float GetMaterialReplayNormalizedValue()
{
	const double Duration = GetMaterialReplayDurationSeconds();
	if (Duration <= 0.0)
	{
		return 0.0f;
	}

	return FMath::Clamp(static_cast<float>(GMaterialReplayCurrentTimeSeconds / Duration), 0.0f, 1.0f);
}

static void RebuildMaterialReplayFrameGpuMs()
{
	GMaterialReplayFrameGpuMs.Reset();
	GMaterialReplayFrameGpuMsMax = 0.0f;
	GMaterialReplayPeakIndices.Reset();
	GMaterialReplayPeakIndicesDirty = true;
	GMaterialReplayFrameGpuMs.Reserve(GMaterialReplaySamples.Num());

	for (const FMaterialGpuReplayFrameSample& Sample : GMaterialReplaySamples)
	{
		float FrameGpuMs = Sample.bHasTotalFrameGpuMs ? FMath::Max(Sample.TotalFrameGpuMs, 0.0f) : 0.0f;
		if (!Sample.bHasTotalFrameGpuMs)
		{
			for (const TPair<FString, float>& Pair : Sample.MaterialGpuMsByKey)
			{
				FrameGpuMs += FMath::Max(Pair.Value, 0.0f);
			}
		}

		GMaterialReplayFrameGpuMs.Add(FrameGpuMs);
		GMaterialReplayFrameGpuMsMax = FMath::Max(GMaterialReplayFrameGpuMsMax, FrameGpuMs);
	}
}

static float GetMaterialReplayCurrentFrameGpuMs()
{
	const int32 SampleIndex = GMaterialReplayCurrentSampleIndex != INDEX_NONE
		? GMaterialReplayCurrentSampleIndex
		: FindMaterialReplaySampleIndexForTime(GMaterialReplayCurrentTimeSeconds);
	return GMaterialReplayFrameGpuMs.IsValidIndex(SampleIndex) ? GMaterialReplayFrameGpuMs[SampleIndex] : 0.0f;
}

enum class EMaterialReplayPeakJumpMode : uint8
{
	Previous,
	Max,
	Next
};

static double GetMaterialReplaySampleTimeForIndex(int32 SampleIndex)
{
	return GMaterialReplaySamples.IsValidIndex(SampleIndex)
		? FMath::Max(0.0, GMaterialReplaySamples[SampleIndex].TimeSeconds)
		: 0.0;
}

static void BuildMaterialReplayGpuPeakIndices(TArray<int32>& OutPeakIndices)
{
	OutPeakIndices.Reset();

	if (GMaterialReplayFrameGpuMs.Num() != GMaterialReplaySamples.Num())
	{
		RebuildMaterialReplayFrameGpuMs();
	}

	if (!GMaterialReplayPeakIndicesDirty)
	{
		OutPeakIndices = GMaterialReplayPeakIndices;
		return;
	}

	GMaterialReplayPeakIndices.Reset();
	if (GMaterialReplayFrameGpuMs.Num() == 0 || GMaterialReplayFrameGpuMsMax <= KINDA_SMALL_NUMBER)
	{
		GMaterialReplayPeakIndicesDirty = false;
		return;
	}

	constexpr float PeakMinRelativeToMax = 0.35f;
	constexpr float PeakGpuMsEpsilon = 0.001f;
	constexpr double PeakMergeSeconds = 0.12;
	const float PeakThreshold = FMath::Max(GMaterialReplayFrameGpuMsMax * PeakMinRelativeToMax, PeakGpuMsEpsilon);

	for (int32 SampleIndex = 0; SampleIndex < GMaterialReplayFrameGpuMs.Num(); ++SampleIndex)
	{
		const float GpuMs = GMaterialReplayFrameGpuMs[SampleIndex];
		if (GpuMs < PeakThreshold)
		{
			continue;
		}

		const float PreviousGpuMs = GMaterialReplayFrameGpuMs.IsValidIndex(SampleIndex - 1)
			? GMaterialReplayFrameGpuMs[SampleIndex - 1]
			: -TNumericLimits<float>::Max();
		const float NextGpuMs = GMaterialReplayFrameGpuMs.IsValidIndex(SampleIndex + 1)
			? GMaterialReplayFrameGpuMs[SampleIndex + 1]
			: -TNumericLimits<float>::Max();
		if (GpuMs <= PreviousGpuMs + PeakGpuMsEpsilon || GpuMs < NextGpuMs - PeakGpuMsEpsilon)
		{
			continue;
		}

		if (GMaterialReplayPeakIndices.Num() > 0)
		{
			const int32 LastPeakIndex = GMaterialReplayPeakIndices.Last();
			const double LastPeakTime = GetMaterialReplaySampleTimeForIndex(LastPeakIndex);
			const double CandidateTime = GetMaterialReplaySampleTimeForIndex(SampleIndex);
			if (CandidateTime - LastPeakTime <= PeakMergeSeconds)
			{
				if (GpuMs > GMaterialReplayFrameGpuMs[LastPeakIndex])
				{
					GMaterialReplayPeakIndices.Last() = SampleIndex;
				}
				continue;
			}
		}

		GMaterialReplayPeakIndices.Add(SampleIndex);
	}

	GMaterialReplayPeakIndicesDirty = false;
	OutPeakIndices = GMaterialReplayPeakIndices;
}

static int32 FindMaterialReplayGpuPeakIndex(EMaterialReplayPeakJumpMode Mode)
{
	TArray<int32> PeakIndices;
	BuildMaterialReplayGpuPeakIndices(PeakIndices);
	if (PeakIndices.Num() == 0)
	{
		return INDEX_NONE;
	}

	if (Mode == EMaterialReplayPeakJumpMode::Max)
	{
		int32 BestPeakIndex = PeakIndices[0];
		for (const int32 PeakIndex : PeakIndices)
		{
			if (GMaterialReplayFrameGpuMs.IsValidIndex(PeakIndex)
				&& GMaterialReplayFrameGpuMs[PeakIndex] > GMaterialReplayFrameGpuMs[BestPeakIndex])
			{
				BestPeakIndex = PeakIndex;
			}
		}
		return BestPeakIndex;
	}

	constexpr double PeakTimeEpsilon = 0.001;
	const double CurrentTime = GMaterialReplayCurrentTimeSeconds;
	int32 BestPeakIndex = INDEX_NONE;
	for (const int32 PeakIndex : PeakIndices)
	{
		const double PeakTime = GetMaterialReplaySampleTimeForIndex(PeakIndex);
		if (Mode == EMaterialReplayPeakJumpMode::Previous)
		{
			if (PeakTime < CurrentTime - PeakTimeEpsilon)
			{
				BestPeakIndex = PeakIndex;
			}
			else
			{
				break;
			}
		}
		else if (PeakTime > CurrentTime + PeakTimeEpsilon)
		{
			BestPeakIndex = PeakIndex;
			break;
		}
	}

	return BestPeakIndex;
}

static FReply JumpMaterialReplayToGpuPeak(EMaterialReplayPeakJumpMode Mode)
{
	const int32 PeakIndex = FindMaterialReplayGpuPeakIndex(Mode);
	if (!GMaterialReplaySamples.IsValidIndex(PeakIndex))
	{
		return FReply::Handled();
	}

	UGameViewportClient* GameViewportClient = GMaterialReplayOverlayViewport.Get();
	UWorld* World = GameViewportClient ? GameViewportClient->GetWorld() : GWorld;
	GMaterialReplayPlaying = false;
	GMaterialReplayScrubbing = false;
	GMaterialReplayLastTickSeconds = -1.0;
	ApplyMaterialReplayTime(World, GameViewportClient, GetMaterialReplaySampleTimeForIndex(PeakIndex), true);
	return FReply::Handled();
}

static float GetMaterialReplayUnitGpuMsForTime(double TimeSeconds)
{
	return FindNearestMaterialReplayUnitGpuMs(GMaterialReplayUnitGpuSamples, TimeSeconds);
}

static float FindNearestMaterialReplayUnitGpuMs(const TArray<FMaterialReplayUnitGpuSample>& Samples, double TimeSeconds)
{
	if (Samples.Num() == 0)
	{
		return 0.0f;
	}

	const double ClampedTime = FMath::Max(0.0, TimeSeconds);
	int32 LowerBoundIndex = 0;
	int32 UpperBoundIndex = Samples.Num();
	while (LowerBoundIndex < UpperBoundIndex)
	{
		const int32 MiddleIndex = LowerBoundIndex + (UpperBoundIndex - LowerBoundIndex) / 2;
		if (Samples[MiddleIndex].TimeSeconds < ClampedTime)
		{
			LowerBoundIndex = MiddleIndex + 1;
		}
		else
		{
			UpperBoundIndex = MiddleIndex;
		}
	}

	int32 BestIndex = FMath::Clamp(LowerBoundIndex, 0, Samples.Num() - 1);
	if (LowerBoundIndex > 0)
	{
		const int32 PreviousIndex = LowerBoundIndex - 1;
		const double CurrentDistance = FMath::Abs(Samples[BestIndex].TimeSeconds - ClampedTime);
		const double PreviousDistance = FMath::Abs(Samples[PreviousIndex].TimeSeconds - ClampedTime);
		if (PreviousDistance <= CurrentDistance)
		{
			BestIndex = PreviousIndex;
		}
	}

	return Samples.IsValidIndex(BestIndex) ? Samples[BestIndex].GpuMs : 0.0f;
}

static int32 FindMaterialReplaySampleIndexForTime(double TimeSeconds)
{
	if (GMaterialReplaySamples.Num() == 0)
	{
		return INDEX_NONE;
	}

	const double ClampedTime = FMath::Clamp(TimeSeconds, 0.0, GetMaterialReplayDurationSeconds());
	int32 BestIndex = 0;
	for (int32 SampleIndex = 0; SampleIndex < GMaterialReplaySamples.Num(); ++SampleIndex)
	{
		const FMaterialGpuReplayFrameSample& Sample = GMaterialReplaySamples[SampleIndex];
		if (ClampedTime >= Sample.TimeSeconds && ClampedTime <= Sample.EndTimeSeconds)
		{
			return SampleIndex;
		}

		if (Sample.TimeSeconds <= ClampedTime)
		{
			BestIndex = SampleIndex;
		}
		else
		{
			break;
		}
	}

	return BestIndex;
}

static void AddMaterialReplayLookupCandidate(TArray<FString>& Candidates, const FString& Value)
{
	const FString Normalized = NormalizeTraceLookupKey(Value);
	if (!Normalized.IsEmpty())
	{
		Candidates.AddUnique(Normalized);
	}
}

static void BuildMaterialReplayLookupCandidates(const FMaterialAccumulator& Row, TArray<FString>& OutCandidates)
{
	OutCandidates.Reset();
	AddMaterialReplayLookupCandidate(OutCandidates, Row.DisplayName);
	AddMaterialReplayLookupCandidate(OutCandidates, Row.PathName);

	if (UMaterialInterface* Material = Row.Material.Get())
	{
		AddMaterialReplayLookupCandidate(OutCandidates, Material->GetName());
		AddMaterialReplayLookupCandidate(OutCandidates, Material->GetPathName());
		AddMaterialReplayLookupCandidate(OutCandidates, Material->GetFullName());
	}

	FString PackageName;
	FString AssetName;
	if (Row.PathName.Split(TEXT("."), &PackageName, &AssetName, ESearchCase::CaseSensitive, ESearchDir::FromEnd))
	{
		AddMaterialReplayLookupCandidate(OutCandidates, AssetName);
	}
}

static void GetMaterialReplaySampleValuesForRow(
	const FMaterialGpuReplayFrameSample& Sample,
	const FMaterialAccumulator& Row,
	float& OutGpuMs,
	int32& OutDrawEvents)
{
	OutGpuMs = 0.0f;
	OutDrawEvents = 0;

	TArray<FString> Candidates;
	BuildMaterialReplayLookupCandidates(Row, Candidates);
	for (const FString& Candidate : Candidates)
	{
		if (const float* GpuMs = Sample.MaterialGpuMsByKey.Find(Candidate))
		{
			OutGpuMs = FMath::Max(OutGpuMs, *GpuMs);
		}

		if (const int32* DrawEvents = Sample.MaterialDrawEventsByKey.Find(Candidate))
		{
			OutDrawEvents = FMath::Max(OutDrawEvents, *DrawEvents);
		}
	}
}

static void TouchMaterialReplayRowsCache(int32 SampleIndex)
{
	GMaterialReplayRowsCacheLru.Remove(SampleIndex);
	GMaterialReplayRowsCacheLru.Add(SampleIndex);
}

static void AddMaterialReplayRowsCacheEntry(int32 SampleIndex, const TArray<FMaterialAccumulator>& Rows, int32 DebugComponentCount)
{
	constexpr int32 MaxReplayRowsCacheEntries = 64;

	FMaterialReplayRowsCacheEntry& Entry = GMaterialReplayRowsCache.FindOrAdd(SampleIndex);
	Entry.Rows = Rows;
	Entry.DebugComponentCount = DebugComponentCount;
	TouchMaterialReplayRowsCache(SampleIndex);

	while (GMaterialReplayRowsCacheLru.Num() > MaxReplayRowsCacheEntries)
	{
		const int32 OldestSampleIndex = GMaterialReplayRowsCacheLru[0];
		GMaterialReplayRowsCacheLru.RemoveAt(0, 1, EAllowShrinking::No);
		GMaterialReplayRowsCache.Remove(OldestSampleIndex);
	}
}

static bool ApplyMaterialReplayRowsCacheEntry(int32 SampleIndex)
{
	const FMaterialReplayRowsCacheEntry* Entry = GMaterialReplayRowsCache.Find(SampleIndex);
	if (!Entry)
	{
		return false;
	}

	GMaterialReplayDebugRows = Entry->Rows;
	GMaterialReplayCurrentRowsAll = Entry->Rows;
	GMaterialReplayCurrentRows = GMaterialReplayCurrentRowsAll;
	const int32 TopN = FMath::Clamp(CVarTopN.GetValueOnGameThread(), 1, 50);
	if (GMaterialReplayCurrentRows.Num() > TopN)
	{
		GMaterialReplayCurrentRows.SetNum(TopN);
	}

	GLastDebugMaterialCount = GMaterialReplayDebugRows.Num();
	GLastDebugComponentCount = Entry->DebugComponentCount;
	TouchMaterialReplayRowsCache(SampleIndex);
	return true;
}

static void BuildMaterialReplayRowsForSample(int32 SampleIndex)
{
	GMaterialReplayCurrentRows.Reset();
	GMaterialReplayCurrentRowsAll.Reset();
	GMaterialReplayDebugRows.Reset();

	if (!GMaterialReplaySamples.IsValidIndex(SampleIndex))
	{
		GLastDebugMaterialCount = 0;
		GLastDebugComponentCount = 0;
		return;
	}

	if (ApplyMaterialReplayRowsCacheEntry(SampleIndex))
	{
		return;
	}

	const FMaterialGpuReplayFrameSample& Sample = GMaterialReplaySamples[SampleIndex];
	TArray<FMaterialAccumulator> Rows;
	for (const FMaterialAccumulator& SceneRow : GMaterialReplaySceneRows)
	{
		if (SceneRow.Components.Num() == 0)
		{
			continue;
		}

		float SampleGpuMs = 0.0f;
		int32 SampleDrawEvents = 0;
		GetMaterialReplaySampleValuesForRow(Sample, SceneRow, SampleGpuMs, SampleDrawEvents);

		FMaterialAccumulator Row = SceneRow;
		Row.MaxGpuMs = SampleGpuMs;
		Row.AvgGpuMs = SampleGpuMs;
		Row.TraceDrawEvents = SampleDrawEvents;
		Rows.Add(MoveTemp(Row));
	}

	Rows.Sort([](const FMaterialAccumulator& A, const FMaterialAccumulator& B)
	{
		if (!FMath::IsNearlyEqual(A.MaxGpuMs, B.MaxGpuMs))
		{
			return A.MaxGpuMs > B.MaxGpuMs;
		}
		if (A.TraceDrawEvents != B.TraceDrawEvents)
		{
			return A.TraceDrawEvents > B.TraceDrawEvents;
		}
		return A.PathName < B.PathName;
	});

	GMaterialReplayDebugRows = Rows;
	GMaterialReplayCurrentRowsAll = Rows;
	GMaterialReplayCurrentRows = GMaterialReplayCurrentRowsAll;
	const int32 TopN = FMath::Clamp(CVarTopN.GetValueOnGameThread(), 1, 50);
	if (GMaterialReplayCurrentRows.Num() > TopN)
	{
		GMaterialReplayCurrentRows.SetNum(TopN);
	}

	GLastDebugMaterialCount = GMaterialReplayDebugRows.Num();
	GLastDebugComponentCount = CountUniqueDebugComponents(GMaterialReplayDebugRows);
	AddMaterialReplayRowsCacheEntry(SampleIndex, GMaterialReplayDebugRows, GLastDebugComponentCount);
}

static void ApplyMaterialReplayTime(UWorld* World, FCommonViewportClient* ViewportClient, double TimeSeconds, bool bForceRefresh)
{
	if (!World || GMaterialReplaySamples.Num() == 0)
	{
		return;
	}

	GMaterialReplayCurrentTimeSeconds = FMath::Clamp(TimeSeconds, 0.0, GetMaterialReplayDurationSeconds());
	const int32 SampleIndex = FindMaterialReplaySampleIndexForTime(GMaterialReplayCurrentTimeSeconds);
	const bool bSampleChanged = SampleIndex != GMaterialReplayCurrentSampleIndex;
	const bool bSeedAnimationFromSample = bForceRefresh || bSampleChanged;
	const bool bNeedsActorColorationRefresh = ShouldUseActorColorationBackend()
		&& IsMaterialDebugColorModeEnabled()
		&& (!GActorColorationActive || GActorColorationColors.Num() == 0);
	if (!bForceRefresh && SampleIndex == GMaterialReplayCurrentSampleIndex && !bNeedsActorColorationRefresh)
	{
		ApplyMaterialReplayCameraSample(GMaterialReplayCameraActor.Get(), GMaterialReplayCurrentTimeSeconds);
		ApplyMaterialReplayCharacterSample(World, GMaterialReplayCurrentTimeSeconds, false);
		return;
	}

	GMaterialReplayCurrentSampleIndex = SampleIndex;
	BuildMaterialReplayRowsForSample(SampleIndex);
	CVarDebug->Set(1);
	SetViewportStatEnabled(ViewportClient, true);
	ApplyMaterialDebugVisualization(World, ViewportClient);

	ApplyMaterialReplayCameraSample(GMaterialReplayCameraActor.Get(), GMaterialReplayCurrentTimeSeconds);
	ApplyMaterialReplayCharacterSample(World, GMaterialReplayCurrentTimeSeconds, bSeedAnimationFromSample);
}

static void RemoveMaterialReplayOverlay()
{
	if (GMaterialReplayOverlayWidget.IsValid())
	{
		if (UGameViewportClient* GameViewportClient = GMaterialReplayOverlayViewport.Get())
		{
			GameViewportClient->RemoveViewportWidgetContent(GMaterialReplayOverlayWidget.ToSharedRef());
		}
	}

	GMaterialReplayOverlayWidget.Reset();
	GMaterialReplayPlayButtonWidget.Reset();
	GMaterialReplayPreviousPeakButtonWidget.Reset();
	GMaterialReplayMaxPeakButtonWidget.Reset();
	GMaterialReplayNextPeakButtonWidget.Reset();
	GMaterialReplaySliderWidget.Reset();
	GMaterialReplayOverlayViewport = nullptr;
	GMaterialReplayPlayButtonRect.Reset();
	GMaterialReplayPreviousPeakButtonRect.Reset();
	GMaterialReplayMaxPeakButtonRect.Reset();
	GMaterialReplayNextPeakButtonRect.Reset();
	GMaterialReplaySliderRect.Reset();
	GMaterialReplayDraggingSlider = false;
	GMaterialReplayScrubbing = false;
}

static void StopMaterialReplayTicker()
{
	if (GMaterialReplayTickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(GMaterialReplayTickerHandle);
		GMaterialReplayTickerHandle.Reset();
	}
}

static FString GetMaterialReplayTimeLabel()
{
	return FString::Printf(
		TEXT("%.2fs / %.2fs"),
		GMaterialReplayCurrentTimeSeconds,
		GetMaterialReplayDurationSeconds());
}

static void SetMaterialReplayScrubNormalized(UWorld* World, FCommonViewportClient* ViewportClient, float NormalizedValue)
{
	GMaterialReplayPlaying = false;
	GMaterialReplayScrubbing = true;
	GMaterialReplayLastTickSeconds = -1.0;
	const double TargetTime = static_cast<double>(FMath::Clamp(NormalizedValue, 0.0f, 1.0f)) * GetMaterialReplayDurationSeconds();
	ApplyMaterialReplayTime(World, ViewportClient, TargetTime, true);
}

static FReply ToggleMaterialReplayPlayback()
{
	if (GMaterialReplaySamples.Num() == 0)
	{
		return FReply::Handled();
	}

	GMaterialReplayScrubbing = false;
	if (GMaterialReplayPlaying)
	{
		GMaterialReplayPlaying = false;
	}
	else
	{
		const double Duration = GetMaterialReplayDurationSeconds();
		if (Duration > 0.0 && GMaterialReplayCurrentTimeSeconds >= Duration - KINDA_SMALL_NUMBER)
		{
			UGameViewportClient* GameViewportClient = GMaterialReplayOverlayViewport.Get();
			UWorld* World = GameViewportClient ? GameViewportClient->GetWorld() : GWorld;
			ApplyMaterialReplayTime(World, GameViewportClient, 0.0, true);
		}
		GMaterialReplayPlaying = true;
	}

	GMaterialReplayLastTickSeconds = -1.0;
	return FReply::Handled();
}

static void SetInputScreenRectFromLocal(
	const FGeometry& Geometry,
	const FVector2D& LocalMin,
	const FVector2D& LocalMax,
	FInputScreenRect& OutRect)
{
	OutRect.Set(Geometry.LocalToAbsolute(LocalMin), Geometry.LocalToAbsolute(LocalMax));
}

static void UpdateMaterialReplayInputRects(UGameViewportClient* GameViewportClient)
{
	GMaterialReplayPlayButtonRect.Reset();
	GMaterialReplayPreviousPeakButtonRect.Reset();
	GMaterialReplayMaxPeakButtonRect.Reset();
	GMaterialReplayNextPeakButtonRect.Reset();
	GMaterialReplaySliderRect.Reset();

	if (!GMaterialReplayActive || !GameViewportClient)
	{
		return;
	}

	const bool bHasPlayButtonRect = SetInputScreenRectFromWidget(GMaterialReplayPlayButtonWidget, 4.0f, 6.0f, GMaterialReplayPlayButtonRect);
	const bool bHasPreviousPeakButtonRect = SetInputScreenRectFromWidget(GMaterialReplayPreviousPeakButtonWidget, 3.0f, 4.0f, GMaterialReplayPreviousPeakButtonRect);
	const bool bHasMaxPeakButtonRect = SetInputScreenRectFromWidget(GMaterialReplayMaxPeakButtonWidget, 3.0f, 4.0f, GMaterialReplayMaxPeakButtonRect);
	const bool bHasNextPeakButtonRect = SetInputScreenRectFromWidget(GMaterialReplayNextPeakButtonWidget, 3.0f, 4.0f, GMaterialReplayNextPeakButtonRect);
	const bool bHasSliderRect = SetInputScreenRectFromWidget(GMaterialReplaySliderWidget, 4.0f, 14.0f, GMaterialReplaySliderRect);
	if (bHasPlayButtonRect && bHasPreviousPeakButtonRect && bHasMaxPeakButtonRect && bHasNextPeakButtonRect && bHasSliderRect)
	{
		return;
	}

	TSharedPtr<SViewport> ViewportWidget = GameViewportClient->GetGameViewportWidget();
	if (!ViewportWidget.IsValid())
	{
		return;
	}

	const FGeometry& ViewportGeometry = ViewportWidget->GetCachedGeometry();
	const FVector2D ViewportSize = ViewportGeometry.GetLocalSize();
	if (ViewportSize.X < 240.0f || ViewportSize.Y < 120.0f)
	{
		return;
	}

	constexpr float OuterPaddingX = 50.0f;
	constexpr float OuterPaddingBottom = 50.0f;
	constexpr float BorderPaddingX = 10.0f;
	constexpr float BorderPaddingY = 7.0f;
	constexpr float GraphHeight = 76.0f;
	constexpr float GraphGap = 7.0f;
	constexpr float ButtonWidth = 76.0f;
	constexpr float ButtonHeight = 30.0f;
	constexpr float PeakButtonGap = 4.0f;
	constexpr float PeakButtonTopGap = 5.0f;
	constexpr float PeakButtonHeight = 24.0f;
	constexpr float PeakPreviousButtonWidth = 30.0f;
	constexpr float PeakMaxButtonWidth = 56.0f;
	constexpr float PeakNextButtonWidth = 30.0f;
	constexpr float TimeSlotLeftPadding = 14.0f;
	constexpr float TimeSlotWidth = 118.0f;
	constexpr float TimeSlotRightPadding = 12.0f;
	constexpr float MinSliderWidth = 48.0f;
	constexpr float SliderHitHeight = 30.0f;

	const float OuterLeft = OuterPaddingX;
	const float OuterRight = FMath::Max(OuterLeft + 1.0f, ViewportSize.X - OuterPaddingX);
	const float OuterTop = FMath::Max(0.0f, ViewportSize.Y - OuterPaddingBottom - GraphHeight - GraphGap - ButtonHeight - PeakButtonTopGap - PeakButtonHeight - BorderPaddingY * 2.0f);
	const float InnerLeft = OuterLeft + BorderPaddingX;
	const float InnerRight = FMath::Max(InnerLeft + 1.0f, OuterRight - BorderPaddingX);
	const float PeakButtonTop = OuterTop + BorderPaddingY + GraphHeight + GraphGap;
	const float ControlTop = PeakButtonTop + PeakButtonHeight + PeakButtonTopGap;

	if (!bHasPlayButtonRect)
	{
		SetInputScreenRectFromLocal(
			ViewportGeometry,
			FVector2D(InnerLeft, ControlTop),
			FVector2D(InnerLeft + ButtonWidth, ControlTop + ButtonHeight),
			GMaterialReplayPlayButtonRect);
	}

	float PeakButtonLeft = InnerLeft;
	if (!bHasPreviousPeakButtonRect)
	{
		SetInputScreenRectFromLocal(
			ViewportGeometry,
			FVector2D(PeakButtonLeft, PeakButtonTop),
			FVector2D(PeakButtonLeft + PeakPreviousButtonWidth, PeakButtonTop + PeakButtonHeight),
			GMaterialReplayPreviousPeakButtonRect);
	}
	PeakButtonLeft += PeakPreviousButtonWidth + PeakButtonGap;
	if (!bHasMaxPeakButtonRect)
	{
		SetInputScreenRectFromLocal(
			ViewportGeometry,
			FVector2D(PeakButtonLeft, PeakButtonTop),
			FVector2D(PeakButtonLeft + PeakMaxButtonWidth, PeakButtonTop + PeakButtonHeight),
			GMaterialReplayMaxPeakButtonRect);
	}
	PeakButtonLeft += PeakMaxButtonWidth + PeakButtonGap;
	if (!bHasNextPeakButtonRect)
	{
		SetInputScreenRectFromLocal(
			ViewportGeometry,
			FVector2D(PeakButtonLeft, PeakButtonTop),
			FVector2D(PeakButtonLeft + PeakNextButtonWidth, PeakButtonTop + PeakButtonHeight),
			GMaterialReplayNextPeakButtonRect);
	}

	const float PreferredSliderLeft = InnerLeft + ButtonWidth + TimeSlotLeftPadding + TimeSlotWidth + TimeSlotRightPadding;
	const float SliderLeft = FMath::Min(FMath::Max(PreferredSliderLeft, InnerLeft + ButtonWidth + 12.0f), InnerRight - MinSliderWidth);
	if (!bHasSliderRect)
	{
		SetInputScreenRectFromLocal(
			ViewportGeometry,
			FVector2D(SliderLeft, ControlTop + (ButtonHeight - SliderHitHeight) * 0.5f),
			FVector2D(InnerRight, ControlTop + (ButtonHeight + SliderHitHeight) * 0.5f),
			GMaterialReplaySliderRect);
	}
}

static bool TryHandleMaterialReplayPointerDown(const FPointerEvent& PointerEvent)
{
	if (!GMaterialReplayActive || !GMaterialReplayOverlayWidget.IsValid())
	{
		return false;
	}

	UpdateMaterialReplayInputRects(GMaterialReplayOverlayViewport.Get());
	const FVector2D ScreenPosition = PointerEvent.GetScreenSpacePosition();
	if (GMaterialReplayPlayButtonRect.Contains(ScreenPosition))
	{
		GMaterialReplayDraggingSlider = false;
		GMaterialReplayScrubbing = false;
		ToggleMaterialReplayPlayback();
		return true;
	}

	if (GMaterialReplayPreviousPeakButtonRect.Contains(ScreenPosition))
	{
		GMaterialReplayDraggingSlider = false;
		JumpMaterialReplayToGpuPeak(EMaterialReplayPeakJumpMode::Previous);
		return true;
	}

	if (GMaterialReplayMaxPeakButtonRect.Contains(ScreenPosition))
	{
		GMaterialReplayDraggingSlider = false;
		JumpMaterialReplayToGpuPeak(EMaterialReplayPeakJumpMode::Max);
		return true;
	}

	if (GMaterialReplayNextPeakButtonRect.Contains(ScreenPosition))
	{
		GMaterialReplayDraggingSlider = false;
		JumpMaterialReplayToGpuPeak(EMaterialReplayPeakJumpMode::Next);
		return true;
	}

	if (GMaterialReplaySliderRect.Contains(ScreenPosition))
	{
		UGameViewportClient* GameViewportClient = GMaterialReplayOverlayViewport.Get();
		UWorld* World = GameViewportClient ? GameViewportClient->GetWorld() : GWorld;
		GMaterialReplayDraggingSlider = true;
		GMaterialReplayDraggingPointerIndex = PointerEvent.GetPointerIndex();
		SetMaterialReplayScrubNormalized(World, GameViewportClient, GMaterialReplaySliderRect.GetNormalizedX(ScreenPosition));
		return true;
	}

	return false;
}

static bool TryHandleMaterialReplayPointerMove(const FPointerEvent& PointerEvent)
{
	if (!GMaterialReplayDraggingSlider)
	{
		return false;
	}

	if (!GMaterialReplayActive || !GMaterialReplayOverlayWidget.IsValid())
	{
		GMaterialReplayDraggingSlider = false;
		GMaterialReplayScrubbing = false;
		return false;
	}

	if (PointerEvent.GetPointerIndex() != GMaterialReplayDraggingPointerIndex)
	{
		return true;
	}

	UpdateMaterialReplayInputRects(GMaterialReplayOverlayViewport.Get());
	if (!GMaterialReplaySliderRect.bValid)
	{
		return true;
	}

	UGameViewportClient* GameViewportClient = GMaterialReplayOverlayViewport.Get();
	UWorld* World = GameViewportClient ? GameViewportClient->GetWorld() : GWorld;
	SetMaterialReplayScrubNormalized(World, GameViewportClient, GMaterialReplaySliderRect.GetNormalizedX(PointerEvent.GetScreenSpacePosition()));
	return true;
}

static bool TryHandleMaterialReplayPointerUp(const FPointerEvent& PointerEvent)
{
	if (!GMaterialReplayDraggingSlider)
	{
		return false;
	}

	if (PointerEvent.GetPointerIndex() != GMaterialReplayDraggingPointerIndex)
	{
		return true;
	}

	GMaterialReplayDraggingSlider = false;
	GMaterialReplayScrubbing = false;
	GMaterialReplayLastTickSeconds = -1.0;
	return true;
}

static TSharedRef<SWidget> MakeMaterialReplayButton(
	const TAttribute<FText>& Label,
	TFunction<FReply()> OnClicked,
	TSharedPtr<SWidget>* OutHitWidget = nullptr,
	float WidthOverride = 76.0f,
	float HeightOverride = 30.0f,
	const TAttribute<FText>& ToolTip = TAttribute<FText>())
{
	TSharedPtr<SBox> ButtonBox;
	TSharedRef<SWidget> ButtonWidget = SAssignNew(ButtonBox, SBox)
		.WidthOverride(WidthOverride)
		.HeightOverride(HeightOverride)
		[
			SNew(SBorder)
			.Padding(1.0f)
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(FLinearColor(0.55f, 0.56f, 0.54f, 0.65f))
			[
				SNew(SButton)
				.ButtonStyle(&FCoreStyle::Get().GetWidgetStyle<FButtonStyle>("NoBorder"))
				.ContentPadding(FMargin(8.0f, 0.0f))
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				.ClickMethod(EButtonClickMethod::MouseDown)
				.TouchMethod(EButtonTouchMethod::Down)
				.IsFocusable(false)
				.ToolTipText(ToolTip)
				.OnClicked_Lambda([OnClicked]()
				{
					return OnClicked();
				})
				[
					SNew(STextBlock)
					.Text(Label)
					.ColorAndOpacity(FSlateColor(FLinearColor(0.94f, 0.94f, 0.90f, 1.0f)))
					.Justification(ETextJustify::Center)
				]
			]
		];

	if (OutHitWidget)
	{
		*OutHitWidget = ButtonBox;
	}

	return ButtonWidget;
}

static TSharedRef<SWidget> MakeMaterialReplayPeakButtonRow()
{
	return SNew(SHorizontalBox)
		+ SHorizontalBox::Slot()
		.AutoWidth()
		[
			MakeMaterialReplayButton(
				TAttribute<FText>::CreateLambda([]()
				{
					return FText::FromString(TEXT("<<"));
				}),
				[]()
				{
					return JumpMaterialReplayToGpuPeak(EMaterialReplayPeakJumpMode::Previous);
				},
				&GMaterialReplayPreviousPeakButtonWidget,
				30.0f,
				24.0f,
				TAttribute<FText>::CreateLambda([]()
				{
					return FText::FromString(TEXT("Previous GPU spike peak"));
				}))
		]
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.Padding(FMargin(4.0f, 0.0f, 0.0f, 0.0f))
		[
			MakeMaterialReplayButton(
				TAttribute<FText>::CreateLambda([]()
				{
					return FText::FromString(TEXT("Maxms"));
				}),
				[]()
				{
					return JumpMaterialReplayToGpuPeak(EMaterialReplayPeakJumpMode::Max);
				},
				&GMaterialReplayMaxPeakButtonWidget,
				56.0f,
				24.0f,
				TAttribute<FText>::CreateLambda([]()
				{
					return FText::FromString(TEXT("Jump to highest GPU spike peak"));
				}))
		]
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.Padding(FMargin(4.0f, 0.0f, 0.0f, 0.0f))
		[
			MakeMaterialReplayButton(
				TAttribute<FText>::CreateLambda([]()
				{
					return FText::FromString(TEXT(">>"));
				}),
				[]()
				{
					return JumpMaterialReplayToGpuPeak(EMaterialReplayPeakJumpMode::Next);
				},
				&GMaterialReplayNextPeakButtonWidget,
				30.0f,
				24.0f,
				TAttribute<FText>::CreateLambda([]()
				{
					return FText::FromString(TEXT("Next GPU spike peak"));
				}))
		]
		+ SHorizontalBox::Slot()
		.FillWidth(1.0f)
		[
			SNew(SSpacer)
		];
}

class SMaterialReplayGpuGraph final : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SMaterialReplayGpuGraph) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs)
	{
		SetCanTick(false);
	}

	virtual FVector2D ComputeDesiredSize(float LayoutScaleMultiplier) const override
	{
		return FVector2D(240.0f, 76.0f);
	}

	virtual int32 OnPaint(
		const FPaintArgs& Args,
		const FGeometry& AllottedGeometry,
		const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements,
		int32 LayerId,
		const FWidgetStyle& InWidgetStyle,
		bool bParentEnabled) const override
	{
		const bool bEnabled = ShouldBeEnabled(bParentEnabled);
		const ESlateDrawEffect DrawEffects = bEnabled ? ESlateDrawEffect::None : ESlateDrawEffect::DisabledEffect;
		const FVector2D Size = AllottedGeometry.GetLocalSize();
		const FSlateBrush* WhiteBrush = FCoreStyle::Get().GetBrush("WhiteBrush");

		FSlateDrawElement::MakeBox(
			OutDrawElements,
			LayerId,
			AllottedGeometry.ToPaintGeometry(),
			WhiteBrush,
			DrawEffects,
			FLinearColor(0.018f, 0.020f, 0.023f, 0.88f) * InWidgetStyle.GetColorAndOpacityTint());

		if (Size.X < 8.0f || Size.Y < 8.0f)
		{
			return LayerId + 1;
		}

		constexpr float PaddingLeft = 8.0f;
		constexpr float PaddingRight = 8.0f;
		constexpr float PaddingTop = 8.0f;
		constexpr float PaddingBottom = 16.0f;
		const FVector2D PlotMin(PaddingLeft, PaddingTop);
		const FVector2D PlotMax(FMath::Max(PaddingLeft + 1.0f, Size.X - PaddingRight), FMath::Max(PaddingTop + 1.0f, Size.Y - PaddingBottom));
		const FVector2D PlotSize = PlotMax - PlotMin;
		const FLinearColor Tint = InWidgetStyle.GetColorAndOpacityTint();
		constexpr float LowGraphMaxMs = 8.0f;
		constexpr float MidGraphMaxMs = 17.0f;
		constexpr float DefaultGraphMaxMs = 33.0f;
		constexpr float FrameBudgetGuideMs = 16.0f;
		const float PeakGpuMs = FMath::Max(0.0f, GMaterialReplayFrameGpuMsMax);
		float GraphMaxMs = LowGraphMaxMs;
		if (PeakGpuMs > DefaultGraphMaxMs)
		{
			GraphMaxMs = PeakGpuMs;
		}
		else if (PeakGpuMs > MidGraphMaxMs)
		{
			GraphMaxMs = DefaultGraphMaxMs;
		}
		else if (PeakGpuMs > LowGraphMaxMs)
		{
			GraphMaxMs = MidGraphMaxMs;
		}

		for (int32 GridIndex = 0; GridIndex < 3; ++GridIndex)
		{
			const float Alpha = static_cast<float>(GridIndex) / 2.0f;
			const float Y = FMath::Lerp(PlotMin.Y, PlotMax.Y, Alpha);
			TArray<FVector2D> GridLine;
			GridLine.Add(FVector2D(PlotMin.X, Y));
			GridLine.Add(FVector2D(PlotMax.X, Y));
			FSlateDrawElement::MakeLines(
				OutDrawElements,
				LayerId + 1,
				AllottedGeometry.ToPaintGeometry(),
				GridLine,
				DrawEffects,
				FLinearColor(0.20f, 0.23f, 0.25f, 0.50f) * Tint,
				true,
				1.0f);
		}

		auto DrawMsGuide = [&](float GuideMs)
		{
			if (GraphMaxMs <= KINDA_SMALL_NUMBER || GuideMs > GraphMaxMs)
			{
				return;
			}

			const bool bFrameBudgetGuide = FMath::IsNearlyEqual(GuideMs, FrameBudgetGuideMs);
			const float GuideAlpha = FMath::Clamp(GuideMs / GraphMaxMs, 0.0f, 1.0f);
			const float GuideY = FMath::Lerp(PlotMax.Y, PlotMin.Y, GuideAlpha);
			const FLinearColor GuideColor = bFrameBudgetGuide
				? FLinearColor(1.0f, 0.58f, 0.12f, 0.86f)
				: FLinearColor(0.38f, 0.44f, 0.47f, 0.58f);

			if (bFrameBudgetGuide)
			{
				constexpr float DashLength = 7.0f;
				constexpr float DashGap = 5.0f;
				for (float DashX = PlotMin.X; DashX < PlotMax.X; DashX += DashLength + DashGap)
				{
					TArray<FVector2D> DashLine;
					DashLine.Add(FVector2D(DashX, GuideY));
					DashLine.Add(FVector2D(FMath::Min(DashX + DashLength, PlotMax.X), GuideY));
					FSlateDrawElement::MakeLines(
						OutDrawElements,
						LayerId + 2,
						AllottedGeometry.ToPaintGeometry(),
						DashLine,
						DrawEffects,
						GuideColor * Tint,
						true,
						1.0f);
				}
			}
			else
			{
				TArray<FVector2D> GuideLine;
				GuideLine.Add(FVector2D(PlotMin.X, GuideY));
				GuideLine.Add(FVector2D(PlotMax.X, GuideY));
				FSlateDrawElement::MakeLines(
					OutDrawElements,
					LayerId + 2,
					AllottedGeometry.ToPaintGeometry(),
					GuideLine,
					DrawEffects,
					GuideColor * Tint,
					true,
					1.0f);
			}

			const FString GuideLabel = FString::Printf(TEXT("%.0fms"), GuideMs);
			FSlateDrawElement::MakeText(
				OutDrawElements,
				LayerId + 3,
				AllottedGeometry.ToPaintGeometry(FVector2D(34.0f, 12.0f), FSlateLayoutTransform(FVector2D(PaddingLeft + 2.0f, FMath::Clamp(GuideY - 12.0f, PaddingTop, PlotMax.Y - 12.0f)))),
				FText::FromString(GuideLabel),
				FCoreStyle::GetDefaultFontStyle("Regular", 8),
				DrawEffects,
				(bFrameBudgetGuide ? FLinearColor(1.0f, 0.68f, 0.18f, 0.94f) : FLinearColor(0.68f, 0.75f, 0.78f, 0.90f)) * Tint);
		};

		constexpr float GuideLabelsMs[] = { 8.0f, 16.0f, 33.0f };
		for (const float GuideMs : GuideLabelsMs)
		{
			DrawMsGuide(GuideMs);
		}

		const FString ScaleLabel = FString::Printf(TEXT("%.0fms"), GraphMaxMs);
		FSlateDrawElement::MakeText(
			OutDrawElements,
			LayerId + 3,
			AllottedGeometry.ToPaintGeometry(FVector2D(48.0f, 12.0f), FSlateLayoutTransform(FVector2D(FMath::Max(PaddingLeft, Size.X - PaddingRight - 48.0f), PaddingTop))),
			FText::FromString(ScaleLabel),
			FCoreStyle::GetDefaultFontStyle("Regular", 8),
			DrawEffects,
			FLinearColor(0.66f, 0.72f, 0.76f, 0.92f) * Tint);

		if (GMaterialReplayFrameGpuMs.Num() == 0 || GMaterialReplayFrameGpuMsMax <= KINDA_SMALL_NUMBER)
		{
			FSlateDrawElement::MakeText(
				OutDrawElements,
				LayerId + 2,
				AllottedGeometry.ToPaintGeometry(FVector2D(180.0f, 16.0f), FSlateLayoutTransform(FVector2D(PaddingLeft, PaddingTop + 6.0f))),
				FText::FromString(TEXT("No GPU frame data")),
				FCoreStyle::GetDefaultFontStyle("Regular", 9),
				DrawEffects,
				FLinearColor(0.58f, 0.64f, 0.68f, 0.86f) * Tint);
		}
		else
		{
			TArray<FVector2D> Points;
			const int32 SampleCount = GMaterialReplayFrameGpuMs.Num();
			const int32 PointCount = SampleCount == 1 ? 2 : FMath::Clamp(FMath::FloorToInt(PlotSize.X), 2, SampleCount);
			Points.Reserve(PointCount);

			for (int32 PointIndex = 0; PointIndex < PointCount; ++PointIndex)
			{
				const float StartAlpha = static_cast<float>(PointIndex) / static_cast<float>(PointCount);
				const float EndAlpha = static_cast<float>(PointIndex + 1) / static_cast<float>(PointCount);
				const int32 StartSample = FMath::Clamp(FMath::FloorToInt(StartAlpha * static_cast<float>(SampleCount)), 0, SampleCount - 1);
				const int32 EndSample = SampleCount == 1 ? 1 : FMath::Clamp(FMath::CeilToInt(EndAlpha * static_cast<float>(SampleCount)), StartSample + 1, SampleCount);

				float BucketGpuMs = 0.0f;
				for (int32 SampleIndex = StartSample; SampleIndex < EndSample; ++SampleIndex)
				{
					BucketGpuMs = FMath::Max(BucketGpuMs, GMaterialReplayFrameGpuMs[SampleIndex]);
				}

				const float ValueAlpha = FMath::Clamp(BucketGpuMs / GraphMaxMs, 0.0f, 1.0f);
				const float X = FMath::Lerp(PlotMin.X, PlotMax.X, PointCount > 1 ? static_cast<float>(PointIndex) / static_cast<float>(PointCount - 1) : 0.0f);
				const float Y = FMath::Lerp(PlotMax.Y, PlotMin.Y, ValueAlpha);
				Points.Add(FVector2D(X, Y));
			}

			FSlateDrawElement::MakeLines(
				OutDrawElements,
				LayerId + 2,
				AllottedGeometry.ToPaintGeometry(),
				Points,
				DrawEffects,
				FLinearColor(0.12f, 0.82f, 0.92f, 0.94f) * Tint,
				true,
				1.6f);

			const FString MaxLabel = FString::Printf(TEXT("peak %.2fms"), GMaterialReplayFrameGpuMsMax);
			FSlateDrawElement::MakeText(
				OutDrawElements,
				LayerId + 3,
				AllottedGeometry.ToPaintGeometry(FVector2D(86.0f, 12.0f), FSlateLayoutTransform(FVector2D(PaddingLeft, Size.Y - 14.0f))),
				FText::FromString(MaxLabel),
				FCoreStyle::GetDefaultFontStyle("Regular", 8),
				DrawEffects,
				FLinearColor(0.58f, 0.66f, 0.70f, 0.90f) * Tint);
		}

		const float CursorX = FMath::Lerp(PlotMin.X, PlotMax.X, GetMaterialReplayNormalizedValue());
		TArray<FVector2D> CursorLine;
		CursorLine.Add(FVector2D(CursorX, PlotMin.Y));
		CursorLine.Add(FVector2D(CursorX, PlotMax.Y));
		FSlateDrawElement::MakeLines(
			OutDrawElements,
			LayerId + 4,
			AllottedGeometry.ToPaintGeometry(),
			CursorLine,
			DrawEffects,
			FLinearColor(1.0f, 0.86f, 0.24f, 0.95f) * Tint,
			true,
			1.2f);

		const FString CurrentLabel = FString::Printf(TEXT("%.2fms"), GetMaterialReplayCurrentFrameGpuMs());
		const float LabelX = FMath::Clamp(CursorX + 5.0f, PaddingLeft, FMath::Max(PaddingLeft, Size.X - 48.0f));
		FSlateDrawElement::MakeText(
			OutDrawElements,
			LayerId + 5,
			AllottedGeometry.ToPaintGeometry(FVector2D(48.0f, 14.0f), FSlateLayoutTransform(FVector2D(LabelX, PaddingTop))),
			FText::FromString(CurrentLabel),
			FCoreStyle::GetDefaultFontStyle("Regular", 9),
			DrawEffects,
			FLinearColor(1.0f, 0.88f, 0.34f, 0.98f) * Tint);

		return LayerId + 6;
	}
};

static TSharedRef<SWidget> BuildMaterialReplayOverlay()
{
	return SNew(SOverlay)
		.Visibility(EVisibility::SelfHitTestInvisible)
		+ SOverlay::Slot()
		.HAlign(HAlign_Fill)
		.VAlign(VAlign_Bottom)
		.Padding(FMargin(50.0f, 0.0f, 50.0f, 50.0f))
		[
			SNew(SBorder)
			.Padding(FMargin(10.0f, 7.0f))
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(FLinearColor(0.025f, 0.026f, 0.028f, 0.82f))
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(0.0f, 0.0f, 0.0f, 7.0f))
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.AutoWidth()
					[
						SNew(SBox)
						.WidthOverride(76.0f)
					]
					+ SHorizontalBox::Slot()
					.AutoWidth()
					.Padding(FMargin(14.0f, 0.0f, 12.0f, 0.0f))
					[
						SNew(SBox)
						.WidthOverride(118.0f)
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					[
						SNew(SBox)
						.HeightOverride(76.0f)
						.Visibility(EVisibility::HitTestInvisible)
						[
							SNew(SMaterialReplayGpuGraph)
						]
					]
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				[
					MakeMaterialReplayPeakButtonRow()
				]
				+ SVerticalBox::Slot()
				.AutoHeight()
				.Padding(FMargin(0.0f, 5.0f, 0.0f, 0.0f))
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.AutoWidth()
					[
						MakeMaterialReplayButton(TAttribute<FText>::CreateLambda([]()
						{
							return FText::FromString(GMaterialReplayPlaying ? TEXT("STOP") : TEXT("PLAY"));
						}), []()
						{
							return ToggleMaterialReplayPlayback();
						}, &GMaterialReplayPlayButtonWidget)
					]
					+ SHorizontalBox::Slot()
					.AutoWidth()
					.Padding(FMargin(14.0f, 0.0f, 12.0f, 0.0f))
					.VAlign(VAlign_Center)
					[
						SNew(SBox)
						.WidthOverride(118.0f)
						[
							SNew(STextBlock)
							.Text(TAttribute<FText>::CreateLambda([]()
							{
								return FText::FromString(GetMaterialReplayTimeLabel());
							}))
							.ColorAndOpacity(FSlateColor(FLinearColor(0.70f, 0.78f, 0.84f, 1.0f)))
						]
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					.VAlign(VAlign_Center)
					[
						SAssignNew(GMaterialReplaySliderWidget, SSlider)
						.Value(TAttribute<float>::CreateLambda([]()
						{
							return GetMaterialReplayNormalizedValue();
						}))
						.StepSize(0.0f)
						.MouseUsesStep(false)
						.IsFocusable(false)
						.SliderBarColor(FLinearColor(0.14f, 0.76f, 0.86f, 0.78f))
						.SliderHandleColor(FLinearColor(0.92f, 0.96f, 0.98f, 1.0f))
						.OnMouseCaptureBegin_Lambda([]()
						{
							GMaterialReplayDraggingSlider = false;
							GMaterialReplayPlaying = false;
							GMaterialReplayScrubbing = true;
							GMaterialReplayLastTickSeconds = -1.0;
						})
						.OnMouseCaptureEnd_Lambda([]()
						{
							GMaterialReplayDraggingSlider = false;
							GMaterialReplayScrubbing = false;
							GMaterialReplayLastTickSeconds = -1.0;
						})
						.OnValueChanged_Lambda([](float NewValue)
						{
							UGameViewportClient* GameViewportClient = GMaterialReplayOverlayViewport.Get();
							UWorld* World = GameViewportClient ? GameViewportClient->GetWorld() : GWorld;
							FCommonViewportClient* ViewportClient = GameViewportClient;
							SetMaterialReplayScrubNormalized(World, ViewportClient, NewValue);
						})
					]
				]
			]
		];
}

static void EnsureMaterialReplayOverlay(FCommonViewportClient* ViewportClient)
{
	UGameViewportClient* GameViewportClient = ResolveProfilingGameViewport(ViewportClient);
	if (!GameViewportClient || !GMaterialReplayActive)
	{
		RemoveMaterialReplayOverlay();
		return;
	}

	if (GMaterialReplayOverlayWidget.IsValid() && GMaterialReplayOverlayViewport.Get() == GameViewportClient)
	{
		UpdateMaterialReplayInputRects(GameViewportClient);
		return;
	}

	RemoveMaterialReplayOverlay();
	GMaterialReplayOverlayViewport = GameViewportClient;
	GMaterialReplayOverlayWidget = BuildMaterialReplayOverlay();
	GameViewportClient->AddViewportWidgetContent(GMaterialReplayOverlayWidget.ToSharedRef(), 1100);
	UpdateMaterialReplayInputRects(GameViewportClient);
}

static bool TickMaterialReplay(float DeltaTime)
{
	if (!GMaterialReplayActive)
	{
		DestroyMaterialReplayCamera();
		GMaterialReplayTickerHandle.Reset();
		return false;
	}

	UGameViewportClient* GameViewportClient = GMaterialReplayOverlayViewport.Get();
	UWorld* World = GameViewportClient ? GameViewportClient->GetWorld() : GWorld;
	FCommonViewportClient* ViewportClient = GameViewportClient;
	if (!World)
	{
		return true;
	}

	UpdateMaterialReplayInputRects(GameViewportClient);
	EnsureMaterialReplayCamera(World);
	if (!GMaterialReplayPlaying || GMaterialReplayScrubbing)
	{
		GMaterialReplayLastTickSeconds = -1.0;
		ApplyMaterialReplayTime(World, ViewportClient, GMaterialReplayCurrentTimeSeconds);
		return true;
	}

	const double Now = FPlatformTime::Seconds();
	const double DeltaSeconds = GMaterialReplayLastTickSeconds > 0.0
		? FMath::Max(0.0, Now - GMaterialReplayLastTickSeconds)
		: static_cast<double>(DeltaTime);
	GMaterialReplayLastTickSeconds = Now;

	const double Duration = GetMaterialReplayDurationSeconds();
	double NextTime = GMaterialReplayCurrentTimeSeconds + DeltaSeconds;
	if (NextTime >= Duration)
	{
		NextTime = Duration;
		GMaterialReplayPlaying = false;
	}

	ApplyMaterialReplayTime(World, ViewportClient, NextTime);
	return true;
}

static void EnsureMaterialReplayTicker()
{
	if (!GMaterialReplayTickerHandle.IsValid())
	{
		GMaterialReplayTickerHandle = FTSTicker::GetCoreTicker().AddTicker(
			FTickerDelegate::CreateStatic(&TickMaterialReplay),
			0.0f);
	}
}

static void StartMaterialReplay(UWorld* World, FCommonViewportClient* ViewportClient)
{
	if (!World || GMaterialReplaySamples.Num() == 0)
	{
		GLastAnalysisMessage = TEXT("No per-frame material replay samples. Run 'stat mat start' and 'stat mat end' first.");
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Material GPU Preview replay skipped. World=%s Samples=%d"),
			*GetNameSafe(World),
			GMaterialReplaySamples.Num());
		return;
	}

	CVarObjectDebug->Set(0);
	SetObjectViewportStatEnabled(ViewportClient, false);
	if (GMaterialReplayFrameGpuMs.Num() != GMaterialReplaySamples.Num())
	{
		RebuildMaterialReplayFrameGpuMs();
	}
	GMaterialReplayActive = true;
	GMaterialReplayPlaying = false;
	GMaterialReplayScrubbing = false;
	GMaterialReplayCurrentTimeSeconds = 0.0;
	GMaterialReplayLastTickSeconds = -1.0;
	GMaterialReplayCurrentSampleIndex = INDEX_NONE;
	RemoveConflictingExternalViewportStats(ViewportClient);
	ApplyMaterialReplayTime(World, ViewportClient, 0.0, true);
	EnsureMaterialReplayCamera(World);
	EnsureMaterialReplayOverlay(ViewportClient);
	EnsureMaterialReplayTicker();
	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Material GPU Preview replay ready. Samples=%d CharacterSamples=%d Duration=%.2fs"),
		GMaterialReplaySamples.Num(),
		GMaterialReplayCharacterSamples.Num(),
		GetMaterialReplayDurationSeconds());
}

static void StopMaterialReplay(UWorld* World, FCommonViewportClient* ViewportClient)
{
	const bool bWasActive = GMaterialReplayActive;
	GMaterialReplayActive = false;
	GMaterialReplayPlaying = false;
	GMaterialReplayScrubbing = false;
	GMaterialReplayCurrentRows.Reset();
	GMaterialReplayCurrentRowsAll.Reset();
	GMaterialReplayDebugRows.Reset();
	GMaterialReplayCurrentTimeSeconds = 0.0;
	GMaterialReplayLastTickSeconds = -1.0;
	GMaterialReplayCurrentSampleIndex = INDEX_NONE;
	StopMaterialReplayTicker();
	RemoveMaterialReplayOverlay();
	RestoreMaterialReplayAnimationStates();
	DestroyMaterialReplayCamera();

	if (bWasActive)
	{
		ClearCachedDebugOverlay(World);
		RefreshActorColorationViewports(ViewportClient);
	}
}

static FString CompactPath(const FString& Path, int32 MaxLen)
{
	if (Path.Len() <= MaxLen)
	{
		return Path;
	}

	return FString::Printf(TEXT("...%s"), *Path.Right(MaxLen - 3));
}

static FString GetMaterialTableName(const FMaterialAccumulator& Row, int32 MaxLen)
{
	FString Name = Row.DisplayName;
	if (Name.IsEmpty())
	{
		Name = Row.PathName;
	}

	FString PackageName;
	FString AssetName;
	if (Name.Split(TEXT("."), &PackageName, &AssetName, ESearchCase::CaseSensitive, ESearchDir::FromEnd) && !AssetName.IsEmpty())
	{
		Name = AssetName;
	}
	else if (Name.Split(TEXT("/"), &PackageName, &AssetName, ESearchCase::CaseSensitive, ESearchDir::FromEnd) && !AssetName.IsEmpty())
	{
		Name = AssetName;
	}

	if (Row.SourceUsages.Num() > 0)
	{
		const FMaterialSourceUsage& SourceUsage = Row.SourceUsages[0];
		FString SourceLabel = SourceUsage.Label;
		if (SourceUsage.InstanceCount > 0)
		{
			SourceLabel += FString::Printf(TEXT(" x%d"), SourceUsage.InstanceCount);
		}
		if (Row.SourceUsages.Num() > 1)
		{
			SourceLabel += FString::Printf(TEXT(" +%d"), Row.SourceUsages.Num() - 1);
		}
		Name += FString::Printf(TEXT(" [%s]"), *SourceLabel);
	}

	return CompactPath(Name, MaxLen);
}

static void DrawStatTile(FCanvas* Canvas, const FVector2D& Position, const FVector2D& Size, const FLinearColor& Color)
{
	FCanvasTileItem TileItem(Position, Size, Color);
	TileItem.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(TileItem);
}

static void DrawStatLine(FCanvas* Canvas, const FVector2D& Start, const FVector2D& End, const FLinearColor& Color)
{
	FCanvasLineItem LineItem(Start, End);
	LineItem.SetColor(Color);
	LineItem.LineThickness = 1.0f;
	Canvas->DrawItem(LineItem);
}

static void DrawStatOutline(FCanvas* Canvas, const FVector2D& Position, const FVector2D& Size, const FLinearColor& Color)
{
	DrawStatLine(Canvas, Position, FVector2D(Position.X + Size.X, Position.Y), Color);
	DrawStatLine(Canvas, FVector2D(Position.X + Size.X, Position.Y), Position + Size, Color);
	DrawStatLine(Canvas, Position + Size, FVector2D(Position.X, Position.Y + Size.Y), Color);
	DrawStatLine(Canvas, FVector2D(Position.X, Position.Y + Size.Y), Position, Color);
}

static float GetProfilingCommandButtonsHeight()
{
	return ProfilingCommandButtonHeight;
}

static float GetProfilingCommandBarHeight()
{
	return ProfilingCommandAreaPadding + GetProfilingCommandButtonsHeight() + 22.0f;
}

static float GetProfilingCommandBarTotalHeight()
{
	return GetProfilingCommandBarHeight();
}

static float GetStatPanelWidth(float ViewWidth, float AvailableWidth)
{
	return FMath::Min(FMath::Clamp(ViewWidth * 0.76f, 640.0f, 1080.0f), AvailableWidth);
}

static float GetStatPanelX(float ViewMinX, float ViewWidth, float PanelWidth)
{
	return ViewMinX + FMath::Max(16.0f, (ViewWidth - PanelWidth) * 0.5f);
}

static float DrawProfilingCommandBar(FCanvas* Canvas, UFont* Font, float PanelX, float ToolbarY, float PanelWidth)
{
	if (!Canvas || !Font)
	{
		return 0.0f;
	}

	GProfilingSlateDrawPanel = false;

	const float BarHeight = GetProfilingCommandBarHeight();
	const float ButtonsHeight = GetProfilingCommandButtonsHeight();
	const float PaddingX = 18.0f;
	const float ButtonY = ToolbarY + ProfilingCommandAreaPadding;
	const FProfilingViewportLayout ViewLayout = ResolveProfilingViewportLayout(nullptr, Canvas, nullptr);
	const float ButtonWidth = GetCenteredProfilingCommandWidth(ViewLayout.ViewWidth);
	const float CenteredButtonX = ViewLayout.ViewMinX + FMath::Max(0.0f, (ViewLayout.ViewWidth - ButtonWidth) * 0.5f);
	GProfilingSlateDrawPanel = false;
	GProfilingSlateButtonHeight = ProfilingCommandButtonHeight;
	GProfilingSlateButtonGap = ProfilingCommandButtonGap;
	GProfilingSlateOverlayLeft = FMath::Max(0.0f, CenteredButtonX);
	GProfilingSlateOverlayTop = FMath::Max(0.0f, ButtonY);
	GProfilingSlateOverlayWidth = ButtonWidth;
	GProfilingSlateOverlayHeight = ButtonsHeight;
	GProfilingSlateViewportWidth = FMath::Max(ViewLayout.ViewMinX + ViewLayout.ViewWidth, CenteredButtonX + ButtonWidth + PaddingX);
	GProfilingSlateViewportHeight = FMath::Max(ViewLayout.ViewMinY + ViewLayout.ViewHeight, ButtonY + ButtonsHeight + PaddingX);
	GProfilingCommandHitLeft = CenteredButtonX;
	GProfilingCommandHitTop = ButtonY;
	GProfilingCommandHitWidth = ButtonWidth;
	GProfilingCommandHitHeight = ButtonsHeight;
	GProfilingCommandHitButtonGap = ProfilingCommandButtonGap;
	RefreshProfilingSlateOverlayIfLayoutChanged();

	DrawStatTile(Canvas, FVector2D(PanelX, ToolbarY), FVector2D(PanelWidth, BarHeight), FLinearColor(0.035f, 0.037f, 0.04f, 0.86f));
	DrawStatLine(Canvas, FVector2D(PanelX, ToolbarY), FVector2D(PanelX + PanelWidth, ToolbarY), FLinearColor(0.46f, 0.46f, 0.43f, 0.55f));

	const int32 ButtonCount = UE_ARRAY_COUNT(GProfilingCommandButtons);
	const float SingleButtonWidth = (ButtonWidth - ProfilingCommandButtonGap * static_cast<float>(ButtonCount - 1)) / static_cast<float>(ButtonCount);
	for (int32 ButtonIndex = 0; ButtonIndex < ButtonCount; ++ButtonIndex)
	{
		const float ButtonX = CenteredButtonX + static_cast<float>(ButtonIndex) * (SingleButtonWidth + ProfilingCommandButtonGap);
		const FVector2D ButtonPosition(ButtonX, ButtonY);
		const FVector2D ButtonSize(SingleButtonWidth, ButtonsHeight);
		DrawStatTile(Canvas, ButtonPosition, ButtonSize, FLinearColor(0.54f, 0.56f, 0.55f, 0.70f));
		DrawStatTile(Canvas, ButtonPosition + FVector2D(1.0f, 1.0f), ButtonSize - FVector2D(2.0f, 2.0f), FLinearColor(0.055f, 0.058f, 0.062f, 0.96f));

		const FString Label = GetProfilingButtonLabel(ButtonIndex);
		const float TextWidth = static_cast<float>(Label.Len()) * 7.0f;
		const float TextHeight = 14.0f;
		FCanvasTextItem ButtonTextItem(
			FVector2D(ButtonX + FMath::Max(0.0f, (SingleButtonWidth - TextWidth) * 0.5f), ButtonY + FMath::Max(0.0f, (ButtonsHeight - TextHeight) * 0.5f)),
			FText::FromString(Label),
			Font,
			FLinearColor(0.94f, 0.94f, 0.90f, 1.0f));
		ButtonTextItem.EnableShadow(FLinearColor::Black);
		Canvas->DrawItem(ButtonTextItem);
	}

	const float CommandY = ButtonY + ButtonsHeight + 6.0f;
	FCanvasTextItem CommandTextItem(FVector2D(CenteredButtonX, CommandY), FText::FromString(TEXT("Commands: stat mat start/end/replay/0 | stat matmode 0/1 | stat obj/0")), Font, FLinearColor(0.50f, 0.58f, 0.64f, 0.95f));
	CommandTextItem.EnableShadow(FLinearColor::Black);
	Canvas->DrawItem(CommandTextItem);

	return GetProfilingCommandBarTotalHeight();
}

static int32 GetMaxDebugShapesPerComponent()
{
	return FMath::Clamp(CVarMaxDebugShapesPerComponent.GetValueOnGameThread(), 0, 4096);
}

static float GetDebugLineThickness()
{
	return FMath::Clamp(CVarDebugLineThickness.GetValueOnGameThread(), 0.0f, 16.0f);
}

static int32 GetSimpleCollisionShapeCount(const FKAggregateGeom& AggGeom)
{
	return AggGeom.BoxElems.Num()
		+ AggGeom.SphereElems.Num()
		+ AggGeom.SphylElems.Num()
		+ AggGeom.ConvexElems.Num();
}

static bool BuildDebugWorldTransforms(UPrimitiveComponent* Component, TArray<FTransform>& OutTransforms)
{
	OutTransforms.Reset();
	if (!Component)
	{
		return false;
	}

	if (const UInstancedStaticMeshComponent* InstancedComponent = Cast<UInstancedStaticMeshComponent>(Component))
	{
		const int32 InstanceCount = InstancedComponent->GetInstanceCount();
		const int32 MaxDebugShapes = GetMaxDebugShapesPerComponent();
		if (InstanceCount <= 0 || InstanceCount > MaxDebugShapes)
		{
			return false;
		}

		OutTransforms.Reserve(InstanceCount);
		for (int32 InstanceIndex = 0; InstanceIndex < InstanceCount; ++InstanceIndex)
		{
			FTransform InstanceTransform;
			if (InstancedComponent->GetInstanceTransform(InstanceIndex, InstanceTransform, true))
			{
				OutTransforms.Add(InstanceTransform);
			}
		}

		return OutTransforms.Num() > 0;
	}

	OutTransforms.Add(Component->GetComponentTransform());
	return true;
}

static void AddFallbackBoundsShape(const UPrimitiveComponent* Component, FDebugOverlayEntry& Entry, float BoundsPadding)
{
	constexpr float MinDebugExtent = 2.0f;

	Entry.Origin = Component ? Component->Bounds.Origin : FVector::ZeroVector;
	Entry.Extent = Component ? Component->Bounds.BoxExtent * BoundsPadding : FVector(MinDebugExtent);
	Entry.Extent.X = FMath::Max(Entry.Extent.X, MinDebugExtent);
	Entry.Extent.Y = FMath::Max(Entry.Extent.Y, MinDebugExtent);
	Entry.Extent.Z = FMath::Max(Entry.Extent.Z, MinDebugExtent);
	Entry.Rotation = Component ? Component->GetComponentQuat() : FQuat::Identity;
	Entry.bUsedCollision = false;
	Entry.Shapes.Reset();

	FDebugOverlayEntry::FShape Shape;
	Shape.Type = FDebugOverlayEntry::EShapeType::FallbackBounds;
	Shape.Origin = Entry.Origin;
	Shape.Extent = Entry.Extent;
	Shape.Rotation = Entry.Rotation;
	Entry.Shapes.Add(MoveTemp(Shape));
}

static FTransform BuildScaledCollisionParentTransform(const FTransform& WorldTransform)
{
	FTransform ParentTransform = WorldTransform;
	ParentTransform.RemoveScaling();
	return ParentTransform;
}

static bool AreConvexIndicesValid(const TArray<int32>& Indices, int32 VertexCount)
{
	if (VertexCount <= 0 || Indices.Num() < 3 || (Indices.Num() % 3) != 0)
	{
		return false;
	}

	for (int32 Index : Indices)
	{
		if (Index < 0 || Index >= VertexCount)
		{
			return false;
		}
	}

	return true;
}

static bool AddCollisionShapesForTransform(
	const FKAggregateGeom& AggGeom,
	const FTransform& WorldTransform,
	float ShapePadding,
	TArray<FDebugOverlayEntry::FShape>& OutShapes)
{
	const FVector Scale3D = WorldTransform.GetScale3D();
	const FTransform ParentTransform = BuildScaledCollisionParentTransform(WorldTransform);
	const int32 InitialShapeCount = OutShapes.Num();

	for (const FKBoxElem& BoxElem : AggGeom.BoxElems)
	{
		const FKBoxElem ScaledBox = BoxElem.GetFinalScaled(Scale3D, FTransform::Identity);
		FTransform ShapeTransform = ScaledBox.GetTransform();
		ShapeTransform *= ParentTransform;

		FDebugOverlayEntry::FShape Shape;
		Shape.Type = FDebugOverlayEntry::EShapeType::Box;
		Shape.Origin = ShapeTransform.GetLocation();
		Shape.Rotation = ShapeTransform.GetRotation();
		Shape.Extent = FVector(
			FMath::Max(ScaledBox.X * 0.5f * ShapePadding, 1.0f),
			FMath::Max(ScaledBox.Y * 0.5f * ShapePadding, 1.0f),
			FMath::Max(ScaledBox.Z * 0.5f * ShapePadding, 1.0f));
		OutShapes.Add(MoveTemp(Shape));
	}

	for (const FKSphereElem& SphereElem : AggGeom.SphereElems)
	{
		FTransform ShapeTransform = SphereElem.GetTransform();
		ShapeTransform.ScaleTranslation(Scale3D);
		ShapeTransform *= ParentTransform;

		FDebugOverlayEntry::FShape Shape;
		Shape.Type = FDebugOverlayEntry::EShapeType::Sphere;
		Shape.Origin = ShapeTransform.GetLocation();
		Shape.Rotation = ShapeTransform.GetRotation();
		Shape.Radius = FMath::Max(SphereElem.Radius * Scale3D.GetAbsMin() * ShapePadding, 1.0f);
		OutShapes.Add(MoveTemp(Shape));
	}

	for (const FKSphylElem& SphylElem : AggGeom.SphylElems)
	{
		const FKSphylElem ScaledSphyl = SphylElem.GetFinalScaled(Scale3D, FTransform::Identity);
		FTransform ShapeTransform = ScaledSphyl.GetTransform();
		ShapeTransform *= ParentTransform;

		FDebugOverlayEntry::FShape Shape;
		Shape.Type = FDebugOverlayEntry::EShapeType::Capsule;
		Shape.Origin = ShapeTransform.GetLocation();
		Shape.Rotation = ShapeTransform.GetRotation();
		Shape.Radius = FMath::Max(ScaledSphyl.Radius * ShapePadding, 1.0f);
		Shape.HalfHeight = FMath::Max((ScaledSphyl.Length * 0.5f + ScaledSphyl.Radius) * ShapePadding, Shape.Radius);
		OutShapes.Add(MoveTemp(Shape));
	}

	for (const FKConvexElem& ConvexElem : AggGeom.ConvexElems)
	{
		TArray<int32> Indices = ConvexElem.IndexData;
		if (Indices.Num() == 0)
		{
			Indices = ConvexElem.GetChaosConvexIndices();
		}

		if (!AreConvexIndicesValid(Indices, ConvexElem.VertexData.Num()))
		{
			continue;
		}

		const FTransform ShapeTransform = ConvexElem.GetTransform() * WorldTransform;
		FDebugOverlayEntry::FShape Shape;
		Shape.Type = FDebugOverlayEntry::EShapeType::Convex;
		Shape.Origin = ShapeTransform.GetLocation();
		Shape.Rotation = ShapeTransform.GetRotation();
		Shape.Vertices.Reserve(ConvexElem.VertexData.Num());
		const FVector LocalCenter = ConvexElem.ElemBox.IsValid ? ConvexElem.ElemBox.GetCenter() : FVector::ZeroVector;
		for (const FVector& Vertex : ConvexElem.VertexData)
		{
			const FVector PaddedVertex = LocalCenter + (Vertex - LocalCenter) * ShapePadding;
			Shape.Vertices.Add(ShapeTransform.TransformPosition(PaddedVertex));
		}
		Shape.Indices = MoveTemp(Indices);
		OutShapes.Add(MoveTemp(Shape));
	}

	return OutShapes.Num() > InitialShapeCount;
}

static bool AddCollisionOverlayShapes(UPrimitiveComponent* Component, FDebugOverlayEntry& Entry, float ShapePadding)
{
	if (!Component)
	{
		return false;
	}

	UBodySetup* BodySetup = Component->GetBodySetup();
	if (!BodySetup)
	{
		return false;
	}

	const FKAggregateGeom& AggGeom = BodySetup->AggGeom;
	const int32 CollisionShapeCount = GetSimpleCollisionShapeCount(AggGeom);
	if (CollisionShapeCount <= 0)
	{
		return false;
	}

	TArray<FTransform> WorldTransforms;
	if (!BuildDebugWorldTransforms(Component, WorldTransforms))
	{
		return false;
	}

	const int32 MaxDebugShapes = GetMaxDebugShapesPerComponent();
	if (MaxDebugShapes <= 0 || CollisionShapeCount * WorldTransforms.Num() > MaxDebugShapes)
	{
		return false;
	}

	Entry.Shapes.Reset();
	Entry.Shapes.Reserve(CollisionShapeCount * WorldTransforms.Num());
	for (const FTransform& WorldTransform : WorldTransforms)
	{
		AddCollisionShapesForTransform(AggGeom, WorldTransform, ShapePadding, Entry.Shapes);
	}

	Entry.bUsedCollision = Entry.Shapes.Num() > 0;
	return Entry.bUsedCollision;
}

static TArray<FDebugOverlayEntry> BuildDebugOverlayEntries()
{
	TArray<FDebugOverlayEntry> Entries;
	const int32 MaxDebugComponents = GetDebugComponentLimit();

	const uint8 Alpha = static_cast<uint8>(FMath::Clamp(CVarDebugAlpha.GetValueOnGameThread(), 8, 220));
	const float ShapePadding = FMath::Clamp(CVarDebugBoundsPadding.GetValueOnGameThread(), 1.0f, 4.0f);
	TMap<UPrimitiveComponent*, FDebugOverlayEntry> EntriesByComponent;

	for (const FMaterialAccumulator& Row : GetActiveMaterialDebugRows())
	{
		const float DebugMs = GetSeverityMs(Row);
		const int32 Severity = GetDebugSeverity(DebugMs);
		const FColor Color = GetDebugSeverityColor(DebugMs, Alpha);
		for (const TWeakObjectPtr<UPrimitiveComponent>& WeakComponent : Row.Components)
		{
			UPrimitiveComponent* Component = WeakComponent.Get();
			if (!Component)
			{
				continue;
			}

			FDebugOverlayEntry Entry;
			Entry.Component = Component;
			Entry.Color = Color;
			Entry.MaxGpuMs = DebugMs;
			Entry.Severity = Severity;
			Entry.BatchId = MakeDebugBatchId(Component);
			Entry.Origin = Component->Bounds.Origin;
			Entry.Extent = Component->Bounds.BoxExtent * ShapePadding;
			Entry.Rotation = Component->GetComponentQuat();
			if (!AddCollisionOverlayShapes(Component, Entry, ShapePadding))
			{
				AddFallbackBoundsShape(Component, Entry, ShapePadding);
			}

			FDebugOverlayEntry* ExistingEntry = EntriesByComponent.Find(Component);
			if (!ExistingEntry || Entry.Severity > ExistingEntry->Severity || Entry.MaxGpuMs > ExistingEntry->MaxGpuMs)
			{
				EntriesByComponent.Add(Component, Entry);
			}
		}
	}

	EntriesByComponent.GenerateValueArray(Entries);
	Entries.Sort([](const FDebugOverlayEntry& A, const FDebugOverlayEntry& B)
	{
		if (A.Severity != B.Severity)
		{
			return A.Severity > B.Severity;
		}

		if (A.MaxGpuMs != B.MaxGpuMs)
		{
			return A.MaxGpuMs > B.MaxGpuMs;
		}

		const UPrimitiveComponent* AComponent = A.Component.Get();
		const UPrimitiveComponent* BComponent = B.Component.Get();
		return (AComponent ? AComponent->GetUniqueID() : 0u) < (BComponent ? BComponent->GetUniqueID() : 0u);
	});

	if (MaxDebugComponents > 0 && Entries.Num() > MaxDebugComponents)
	{
		Entries.SetNum(MaxDebugComponents);
	}

	return Entries;
}

static const FDebugOverlayEntry* FindDebugEntryByBatchId(const TArray<FDebugOverlayEntry>& Entries, uint32 BatchId)
{
	for (const FDebugOverlayEntry& Entry : Entries)
	{
		if (Entry.BatchId == BatchId)
		{
			return &Entry;
		}
	}

	return nullptr;
}

static void DrawDebugOverlayEntry(UWorld* World, const FDebugOverlayEntry& Entry)
{
	if (ULineBatchComponent* LineBatcher = GetMaterialCostLineBatcher(World))
	{
		const FLinearColor LineColor(Entry.Color);
		const float LineThickness = GetDebugLineThickness();
		for (const FDebugOverlayEntry::FShape& Shape : Entry.Shapes)
		{
			switch (Shape.Type)
			{
			case FDebugOverlayEntry::EShapeType::Box:
			case FDebugOverlayEntry::EShapeType::FallbackBounds:
			{
				const FBox Box = FBox::BuildAABB(FVector::ZeroVector, Shape.Extent);
				const FTransform Transform(Shape.Rotation, Shape.Origin, FVector::OneVector);
				LineBatcher->DrawSolidBox(Box, Transform, Entry.Color, 0, -1.0f, Entry.BatchId);
				break;
			}
			case FDebugOverlayEntry::EShapeType::Sphere:
				LineBatcher->DrawSphere(Shape.Origin, Shape.Radius, 24, LineColor, -1.0f, 0, LineThickness, Entry.BatchId);
				break;
			case FDebugOverlayEntry::EShapeType::Capsule:
				LineBatcher->DrawCapsule(Shape.Origin, Shape.HalfHeight, Shape.Radius, Shape.Rotation, LineColor, -1.0f, 0, LineThickness, Entry.BatchId);
				break;
			case FDebugOverlayEntry::EShapeType::Convex:
				if (Shape.Vertices.Num() > 0 && Shape.Indices.Num() >= 3)
				{
					LineBatcher->DrawMesh(Shape.Vertices, Shape.Indices, Entry.Color, 0, -1.0f, Entry.BatchId);
				}
				break;
			default:
				break;
			}
		}
	}
}

static void UpdateDebugOverlay(UWorld* World)
{
	if (!World || CVarDebug.GetValueOnGameThread() == 0 || GActorColorationActive || !IsMaterialDebugColorModeEnabled())
	{
		ClearCachedDebugOverlay(World);
		return;
	}

	if (GCachedDebugWorld.Get() != World)
	{
		ClearCachedDebugOverlay(GCachedDebugWorld.Get());
		GCachedDebugWorld = World;
	}

	TArray<FDebugOverlayEntry> NewEntries = BuildDebugOverlayEntries();

	for (const FDebugOverlayEntry& OldEntry : GCachedDebugEntries)
	{
		const FDebugOverlayEntry* NewEntry = FindDebugEntryByBatchId(NewEntries, OldEntry.BatchId);
		if (!NewEntry || !OldEntry.Matches(*NewEntry))
		{
			ClearDebugBatch(World, OldEntry.BatchId);
		}
	}

	for (const FDebugOverlayEntry& NewEntry : NewEntries)
	{
		const FDebugOverlayEntry* OldEntry = FindDebugEntryByBatchId(GCachedDebugEntries, NewEntry.BatchId);
		if (!OldEntry || !OldEntry->Matches(NewEntry))
		{
			DrawDebugOverlayEntry(World, NewEntry);
		}
	}

	GCachedDebugEntries = MoveTemp(NewEntries);
	GCachedDebugWorld = World;
}

static uint64 ToUInt64(SIZE_T Value)
{
	return static_cast<uint64>(Value);
}

static void AddObjectMemoryUsage(
	TArray<FObjectMemorySnapshotRow>& Rows,
	TMap<FObjectKey, int32>& RowLookup,
	UObject* Object,
	UPrimitiveComponent* UserComponent)
{
	if (!Object || Object->IsTemplate())
	{
		return;
	}

	const FObjectKey ObjectKey(Object);
	int32* ExistingIndex = RowLookup.Find(ObjectKey);
	if (!ExistingIndex)
	{
		FObjectMemorySnapshotRow& Row = Rows.AddDefaulted_GetRef();
		Row.Object = Object;
		Row.DisplayName = Object->GetName();
		Row.PathName = Object->GetPathName();
		Row.ClassName = Object->GetClass() ? Object->GetClass()->GetName() : TEXT("Object");

		FArchiveCountMem Count(Object);
		Row.ObjectBytes = ToUInt64(Count.GetMax());

		FResourceSizeEx ResourceSize(EResourceSizeMode::Exclusive);
		Object->GetResourceSizeEx(ResourceSize);
		Row.ResourceBytes = ToUInt64(ResourceSize.GetTotalMemoryBytes());

		const int32 NewRowIndex = Rows.Num() - 1;
		RowLookup.Add(ObjectKey, NewRowIndex);
		ExistingIndex = RowLookup.Find(ObjectKey);
	}

	if (!Rows.IsValidIndex(*ExistingIndex))
	{
		return;
	}

	FObjectMemorySnapshotRow& Row = Rows[*ExistingIndex];
	if (UserComponent && !Row.Components.Contains(UserComponent))
	{
		Row.Components.Add(UserComponent);
		Row.UserCount = Row.Components.Num();
	}
}

static void AddMaterialAndTexturesForObjectSnapshot(
	TArray<FObjectMemorySnapshotRow>& Rows,
	TMap<FObjectKey, int32>& RowLookup,
	UMaterialInterface* Material,
	UPrimitiveComponent* UserComponent)
{
	if (!Material)
	{
		return;
	}

	AddObjectMemoryUsage(Rows, RowLookup, Material, UserComponent);

	TArray<UTexture*> Textures;
	Material->GetUsedTextures(Textures);
	for (UTexture* Texture : Textures)
	{
		AddObjectMemoryUsage(Rows, RowLookup, Texture, UserComponent);
	}
}

static void AddPrimitiveComponentObjectMemory(
	TArray<FObjectMemorySnapshotRow>& Rows,
	TMap<FObjectKey, int32>& RowLookup,
	UPrimitiveComponent* Component)
{
	if (!ShouldIncludeComponent(Component))
	{
		return;
	}

	AddObjectMemoryUsage(Rows, RowLookup, Component, Component);

	if (UStaticMeshComponent* StaticMeshComponent = Cast<UStaticMeshComponent>(Component))
	{
		AddObjectMemoryUsage(Rows, RowLookup, StaticMeshComponent->GetStaticMesh(), Component);
	}

	if (USkinnedMeshComponent* SkinnedMeshComponent = Cast<USkinnedMeshComponent>(Component))
	{
		AddObjectMemoryUsage(Rows, RowLookup, SkinnedMeshComponent->GetSkinnedAsset(), Component);
	}

	TArray<UMaterialInterface*> Materials;
	Component->GetUsedMaterials(Materials);
	for (UMaterialInterface* Material : Materials)
	{
		AddMaterialAndTexturesForObjectSnapshot(Rows, RowLookup, Material, Component);
	}
}

static FString CsvEscape(const FString& Value)
{
	FString EscapedValue = Value;
	EscapedValue.ReplaceInline(TEXT("\""), TEXT("\"\""));
	return FString::Printf(TEXT("\"%s\""), *EscapedValue);
}

static bool SaveObjectMemorySnapshotRows(const TArray<FObjectMemorySnapshotRow>& Rows)
{
	if (Rows.Num() == 0)
	{
		GLastObjectSnapshotFilePath.Reset();
		return false;
	}

	TArray<FString> Lines;
	Lines.Reserve(Rows.Num() + 1);
	Lines.Add(TEXT("Rank,TotalMB,ObjectKB,ResourceKB,Users,Class,ObjectPath"));

	for (int32 RowIndex = 0; RowIndex < Rows.Num(); ++RowIndex)
	{
		const FObjectMemorySnapshotRow& Row = Rows[RowIndex];
		const FString ClassCsv = CsvEscape(Row.ClassName);
		const FString PathCsv = CsvEscape(Row.PathName);
		Lines.Add(FString::Printf(
			TEXT("%d,%.3f,%llu,%llu,%d,%s,%s"),
			RowIndex + 1,
			Row.GetTotalMB(),
			static_cast<unsigned long long>(Row.ObjectBytes / 1024u),
			static_cast<unsigned long long>(Row.ResourceBytes / 1024u),
			Row.UserCount,
			*ClassCsv,
			*PathCsv));
	}

	GLastObjectSnapshotFilePath = BuildObjectSnapshotFilePath();
	return FFileHelper::SaveStringToFile(FString::Join(Lines, TEXT("\n")), *GLastObjectSnapshotFilePath);
}

static void SortObjectMemoryRows(TArray<FObjectMemorySnapshotRow>& Rows)
{
	Rows.Sort([](const FObjectMemorySnapshotRow& A, const FObjectMemorySnapshotRow& B)
	{
		const uint64 ATotalBytes = A.GetTotalBytes();
		const uint64 BTotalBytes = B.GetTotalBytes();
		if (ATotalBytes != BTotalBytes)
		{
			return ATotalBytes > BTotalBytes;
		}

		if (A.UserCount != B.UserCount)
		{
			return A.UserCount > B.UserCount;
		}

		return A.PathName < B.PathName;
	});
}

static int32 CountUniqueObjectDebugComponents(const TArray<FObjectMemorySnapshotRow>& Rows)
{
	TSet<FObjectKey> Components;
	for (const FObjectMemorySnapshotRow& Row : Rows)
	{
		for (const TWeakObjectPtr<UPrimitiveComponent>& WeakComponent : Row.Components)
		{
			if (UPrimitiveComponent* Component = WeakComponent.Get())
			{
				Components.Add(FObjectKey(Component));
			}
		}
	}

	return Components.Num();
}

static bool BuildObjectMemorySnapshot(UWorld* World)
{
	if (!World)
	{
		GLastObjectSnapshotMessage = TEXT("Object Memory Snapshot skipped: world is unavailable.");
		return false;
	}

	const double SnapshotStartTime = FPlatformTime::Seconds();

	FlushAsyncLoading();
	CollectGarbage(GARBAGE_COLLECTION_KEEPFLAGS, true);
	FlushRenderingCommands();

	TArray<FObjectMemorySnapshotRow> Rows;
	TMap<FObjectKey, int32> RowLookup;
	int32 SourceComponentCount = 0;

	for (TActorIterator<AActor> ActorIt(World); ActorIt; ++ActorIt)
	{
		AActor* Actor = *ActorIt;
		if (!Actor)
		{
			continue;
		}

		TInlineComponentArray<UPrimitiveComponent*> Components;
		Actor->GetComponents(Components);
		for (UPrimitiveComponent* Component : Components)
		{
			if (ShouldIncludeComponent(Component))
			{
				SourceComponentCount++;
				AddPrimitiveComponentObjectMemory(Rows, RowLookup, Component);
			}
		}
	}

	Rows.RemoveAll([](const FObjectMemorySnapshotRow& Row)
	{
		return Row.GetTotalBytes() == 0 || Row.Components.Num() == 0;
	});
	SortObjectMemoryRows(Rows);

	GCachedObjectRows.Reset();
	GCachedObjectDebugRows = Rows;
	const bool bSavedRawSnapshot = SaveObjectMemorySnapshotRows(Rows);
	const int32 TopN = FMath::Clamp(CVarObjectTopN.GetValueOnGameThread(), 1, 64);
	for (int32 RowIndex = 0; RowIndex < Rows.Num() && GCachedObjectRows.Num() < TopN; ++RowIndex)
	{
		GCachedObjectRows.Add(Rows[RowIndex]);
	}

	GLastObjectSnapshotSourceCount = SourceComponentCount;
	GLastObjectDebugComponentCount = CountUniqueObjectDebugComponents(GCachedObjectDebugRows);
	GLastObjectSnapshotTime = FPlatformTime::Seconds();
	GLastObjectSnapshotMessage = FString::Printf(
		TEXT("Snapshot rows=%d debugObjects=%d debugComps=%d sources=%d time=%.2fs raw=%s"),
		GCachedObjectRows.Num(),
		GCachedObjectDebugRows.Num(),
		GLastObjectDebugComponentCount,
		GLastObjectSnapshotSourceCount,
		FPlatformTime::Seconds() - SnapshotStartTime,
		bSavedRawSnapshot ? *GLastObjectSnapshotFilePath : TEXT("not saved"));

	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Object Memory Snapshot complete. Rows=%d DebugObjects=%d DebugComponents=%d SourceComponents=%d Analyze=%.2fs Raw=%s"),
		GCachedObjectRows.Num(),
		GCachedObjectDebugRows.Num(),
		GLastObjectDebugComponentCount,
		GLastObjectSnapshotSourceCount,
		FPlatformTime::Seconds() - SnapshotStartTime,
		bSavedRawSnapshot ? *GLastObjectSnapshotFilePath : TEXT("not saved"));

	return GCachedObjectRows.Num() > 0;
}

struct FObjectActorColorationTarget
{
	TWeakObjectPtr<UPrimitiveComponent> Component;
	float TotalMB = 0.0f;
	int32 Severity = 0;
	FLinearColor Color = FLinearColor::Black;
};

static int32 GetObjectDebugComponentLimit()
{
	return FMath::Max(CVarObjectMaxDebugComponents.GetValueOnGameThread(), 0);
}

static void RebuildObjectActorColorationColorMap()
{
	GActorColorationColors.Reset();

	const int32 MaxDebugComponents = GetObjectDebugComponentLimit();
	TMap<UPrimitiveComponent*, FObjectActorColorationTarget> TargetsByComponent;
	for (const FObjectMemorySnapshotRow& Row : GCachedObjectDebugRows)
	{
		const float TotalMB = Row.GetTotalMB();
		const int32 Severity = GetObjectDebugSeverity(TotalMB);
		const FLinearColor Color = GetObjectMemorySnapshotColor(TotalMB);

		for (const TWeakObjectPtr<UPrimitiveComponent>& WeakComponent : Row.Components)
		{
			UPrimitiveComponent* Component = WeakComponent.Get();
			if (!IsDebugTargetComponent(Component))
			{
				continue;
			}

			FObjectActorColorationTarget* ExistingTarget = TargetsByComponent.Find(Component);
			if (ExistingTarget && ExistingTarget->TotalMB >= TotalMB)
			{
				continue;
			}

			FObjectActorColorationTarget Target;
			Target.Component = Component;
			Target.TotalMB = TotalMB;
			Target.Severity = Severity;
			Target.Color = Color;
			TargetsByComponent.Add(Component, Target);
		}
	}

	TArray<FObjectActorColorationTarget> Targets;
	TargetsByComponent.GenerateValueArray(Targets);
	Targets.Sort([](const FObjectActorColorationTarget& A, const FObjectActorColorationTarget& B)
	{
		if (A.Severity != B.Severity)
		{
			return A.Severity > B.Severity;
		}

		if (!FMath::IsNearlyEqual(A.TotalMB, B.TotalMB))
		{
			return A.TotalMB > B.TotalMB;
		}

		const UPrimitiveComponent* AComponent = A.Component.Get();
		const UPrimitiveComponent* BComponent = B.Component.Get();
		return (AComponent ? AComponent->GetUniqueID() : 0u) < (BComponent ? BComponent->GetUniqueID() : 0u);
	});

	if (MaxDebugComponents > 0 && Targets.Num() > MaxDebugComponents)
	{
		Targets.SetNum(MaxDebugComponents);
	}

	for (const FObjectActorColorationTarget& Target : Targets)
	{
		if (UPrimitiveComponent* Component = Target.Component.Get())
		{
			GActorColorationColors.Add(FObjectKey(Component), Target.Color);
		}
	}
}

static TArray<FDebugOverlayEntry> BuildObjectDebugOverlayEntries()
{
	TArray<FDebugOverlayEntry> Entries;
	const int32 MaxDebugComponents = GetObjectDebugComponentLimit();
	const uint8 Alpha = static_cast<uint8>(FMath::Clamp(CVarObjectDebugAlpha.GetValueOnGameThread(), 8, 220));
	const float ShapePadding = FMath::Clamp(CVarDebugBoundsPadding.GetValueOnGameThread(), 1.0f, 4.0f);
	TMap<UPrimitiveComponent*, FDebugOverlayEntry> EntriesByComponent;

	for (const FObjectMemorySnapshotRow& Row : GCachedObjectDebugRows)
	{
		const float TotalMB = Row.GetTotalMB();
		const int32 Severity = GetObjectDebugSeverity(TotalMB);
		const FColor Color = GetObjectDebugSeverityColor(TotalMB, Alpha);

		for (const TWeakObjectPtr<UPrimitiveComponent>& WeakComponent : Row.Components)
		{
			UPrimitiveComponent* Component = WeakComponent.Get();
			if (!Component)
			{
				continue;
			}

			FDebugOverlayEntry Entry;
			Entry.Component = Component;
			Entry.Color = Color;
			Entry.MaxGpuMs = TotalMB;
			Entry.Severity = Severity;
			Entry.BatchId = MakeDebugBatchId(Component);
			Entry.Origin = Component->Bounds.Origin;
			Entry.Extent = Component->Bounds.BoxExtent * ShapePadding;
			Entry.Rotation = Component->GetComponentQuat();
			if (!AddCollisionOverlayShapes(Component, Entry, ShapePadding))
			{
				AddFallbackBoundsShape(Component, Entry, ShapePadding);
			}

			FDebugOverlayEntry* ExistingEntry = EntriesByComponent.Find(Component);
			if (!ExistingEntry || Entry.Severity > ExistingEntry->Severity || Entry.MaxGpuMs > ExistingEntry->MaxGpuMs)
			{
				EntriesByComponent.Add(Component, Entry);
			}
		}
	}

	EntriesByComponent.GenerateValueArray(Entries);
	Entries.Sort([](const FDebugOverlayEntry& A, const FDebugOverlayEntry& B)
	{
		if (A.Severity != B.Severity)
		{
			return A.Severity > B.Severity;
		}

		if (A.MaxGpuMs != B.MaxGpuMs)
		{
			return A.MaxGpuMs > B.MaxGpuMs;
		}

		const UPrimitiveComponent* AComponent = A.Component.Get();
		const UPrimitiveComponent* BComponent = B.Component.Get();
		return (AComponent ? AComponent->GetUniqueID() : 0u) < (BComponent ? BComponent->GetUniqueID() : 0u);
	});

	if (MaxDebugComponents > 0 && Entries.Num() > MaxDebugComponents)
	{
		Entries.SetNum(MaxDebugComponents);
	}

	return Entries;
}

static void UpdateObjectDebugOverlay(UWorld* World)
{
	if (!World || CVarObjectDebug.GetValueOnGameThread() == 0 || GActorColorationActive || !IsMaterialDebugColorModeEnabled())
	{
		ClearCachedDebugOverlay(World);
		return;
	}

	if (GCachedDebugWorld.Get() != World)
	{
		ClearCachedDebugOverlay(GCachedDebugWorld.Get());
		GCachedDebugWorld = World;
	}

	TArray<FDebugOverlayEntry> NewEntries = BuildObjectDebugOverlayEntries();

	for (const FDebugOverlayEntry& OldEntry : GCachedDebugEntries)
	{
		const FDebugOverlayEntry* NewEntry = FindDebugEntryByBatchId(NewEntries, OldEntry.BatchId);
		if (!NewEntry || !OldEntry.Matches(*NewEntry))
		{
			ClearDebugBatch(World, OldEntry.BatchId);
		}
	}

	for (const FDebugOverlayEntry& NewEntry : NewEntries)
	{
		const FDebugOverlayEntry* OldEntry = FindDebugEntryByBatchId(GCachedDebugEntries, NewEntry.BatchId);
		if (!OldEntry || !OldEntry->Matches(NewEntry))
		{
			DrawDebugOverlayEntry(World, NewEntry);
		}
	}

	GCachedDebugEntries = MoveTemp(NewEntries);
	GCachedDebugWorld = World;
}

static void ApplyObjectDebugVisualization(UWorld* World, FCommonViewportClient* ViewportClient)
{
	if (!World || CVarObjectDebug.GetValueOnGameThread() == 0)
	{
		if (CVarDebug.GetValueOnGameThread() == 0 && !GMaterialReplayActive)
		{
			ClearCachedDebugOverlay(World);
		}
		return;
	}

	if (!IsMaterialDebugColorModeEnabled())
	{
		DisableActorColoration(World, ViewportClient);
		ClearCachedDebugOverlay(World);
		RefreshActorColorationViewports(ViewportClient);
		return;
	}

	if (ShouldUseActorColorationBackend())
	{
		RebuildObjectActorColorationColorMap();
		ApplyActorColorationViewModeFromCurrentColors(World, ViewportClient);
	}
	else
	{
		DisableActorColoration(World, ViewportClient);
		UpdateObjectDebugOverlay(World);
	}
}

static FString GetObjectMemoryTableName(const FObjectMemorySnapshotRow& Row, int32 MaxLen)
{
	FString Name = Row.PathName.IsEmpty() ? Row.DisplayName : Row.PathName;
	FString PackageName;
	FString AssetName;
	if (Name.Split(TEXT("."), &PackageName, &AssetName, ESearchCase::CaseSensitive, ESearchDir::FromEnd) && !AssetName.IsEmpty())
	{
		Name = AssetName;
	}
	else if (Name.Split(TEXT("/"), &PackageName, &AssetName, ESearchCase::CaseSensitive, ESearchDir::FromEnd) && !AssetName.IsEmpty())
	{
		Name = AssetName;
	}

	return CompactPath(Name, MaxLen);
}

static void DisableObjectMemorySnapshot(UWorld* World, FCommonViewportClient* ViewportClient)
{
	CVarObjectDebug->Set(0);
	DisableActorColoration(World, ViewportClient);
	ClearCachedDebugOverlay(World);
	SetObjectViewportStatEnabled(ViewportClient, false);
}

static void ShowObjectMemorySnapshot(UWorld* World, FCommonViewportClient* ViewportClient)
{
	StopMaterialReplay(World, ViewportClient);
	StopInsightsTraceIfNeeded();
	RestoreInsightsMaterialCaptureCvars();
	CVarDebug->Set(0);
	SetViewportStatEnabled(ViewportClient, false);
	DisableActorColoration(World, ViewportClient);
	ClearCachedDebugOverlay(World);

	SetObjectViewportStatEnabled(ViewportClient, true);
	const bool bBuiltRows = BuildObjectMemorySnapshot(World);
	if (!bBuiltRows)
	{
		CVarObjectDebug->Set(0);
		ClearCachedDebugOverlay(World);
		return;
	}

	CVarObjectDebug->Set(1);
	ApplyObjectDebugVisualization(World, ViewportClient);
}

static bool ToggleObjectStat(UWorld* World, FCommonViewportClient* ViewportClient, const TCHAR* Stream)
{
	FString Args(Stream ? Stream : TEXT(""));
	Args.TrimStartAndEndInline();

	const TCHAR* Cmd = *Args;
	if (FParse::Command(&Cmd, TEXT("0")) || FParse::Command(&Cmd, TEXT("off")) || FParse::Command(&Cmd, TEXT("clear")))
	{
		DisableObjectMemorySnapshot(World, ViewportClient);
		return true;
	}

	if (!Args.IsEmpty())
	{
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Unknown stat obj argument '%s'. Use 'stat obj' to snapshot or 'stat obj 0' to hide."), *Args);
		return true;
	}

	ShowObjectMemorySnapshot(World, ViewportClient);
	return true;
}

static bool ToggleProfilingStat(UWorld* World, FCommonViewportClient* ViewportClient, const TCHAR* Stream)
{
	FString Args(Stream ? Stream : TEXT(""));
	Args.TrimStartAndEndInline();

	const TCHAR* Cmd = *Args;
	if (FParse::Command(&Cmd, TEXT("0")) || FParse::Command(&Cmd, TEXT("off")) || FParse::Command(&Cmd, TEXT("clear")))
	{
		SetProfilingViewportStatEnabled(ViewportClient, false);
		return true;
	}

	if (!Args.IsEmpty())
	{
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Unknown stat profiling argument '%s'. Use 'stat profiling' or 'stat profiling 0'."), *Args);
		return true;
	}

	SetProfilingViewportStatEnabled(ViewportClient, true);
	return true;
}

static int32 RenderProfilingStat(UWorld* World, FViewport* Viewport, FCanvas* Canvas, int32 X, int32 Y, const FVector* ViewLocation, const FRotator* ViewRotation)
{
	if (!Canvas || !GEngine)
	{
		return Y;
	}

	FCommonViewportClient* RenderingViewportClient = FindViewportClientForViewport(Viewport);
	if (DisablePluginViewportStatsForConflictingExternalStat(World, RenderingViewportClient))
	{
		return Y;
	}

	if (!IsProfilingViewportStatEnabled(RenderingViewportClient))
	{
		return Y;
	}

	constexpr float OuterPadding = 10.0f;
	const FProfilingViewportLayout ViewLayout = ResolveProfilingViewportLayout(Viewport, Canvas, RenderingViewportClient);
	FVector2D ButtonPosition = FVector2D::ZeroVector;
	FVector2D ButtonSize = FVector2D::ZeroVector;
	SetCenteredProfilingCommandLayout(ViewLayout, OuterPadding, ButtonPosition, ButtonSize);
	EnsureProfilingSlateOverlay(RenderingViewportClient);
	RefreshProfilingSlateOverlayIfLayoutChanged();
	UpdateProfilingCommandHitRectFromSlate();

	return FMath::Max(Y, static_cast<int32>(ButtonPosition.Y + ButtonSize.Y + 4.0f));
}

static int32 RenderObjectStat(UWorld* World, FViewport* Viewport, FCanvas* Canvas, int32 X, int32 Y, const FVector* ViewLocation, const FRotator* ViewRotation)
{
	if (!World || !Canvas || !GEngine)
	{
		return Y;
	}

	if (CVarObjectDebug.GetValueOnGameThread() == 0)
	{
		ClearCachedDebugOverlay(World);
	}

	UFont* Font = GEngine->GetSmallFont();
	if (!Font)
	{
		return Y;
	}

	const FIntRect CanvasViewRect = Canvas->GetViewRect();
	const FIntPoint FallbackViewSize = Canvas->GetRenderTarget() ? Canvas->GetRenderTarget()->GetSizeXY() : FIntPoint(1280, 720);
	FCommonViewportClient* RenderingViewportClient = FindViewportClientForViewport(Viewport);
	if (DisablePluginViewportStatsForConflictingExternalStat(World, RenderingViewportClient))
	{
		return Y;
	}

	const float DPIScale = FMath::Max(Canvas->GetDPIScale(), 0.01f);
	const float ViewWidth = FMath::Max(320.0f, static_cast<float>(CanvasViewRect.Width() > 0 ? CanvasViewRect.Width() : FallbackViewSize.X) / DPIScale);
	const float ViewHeight = FMath::Max(240.0f, static_cast<float>(CanvasViewRect.Height() > 0 ? CanvasViewRect.Height() : FallbackViewSize.Y) / DPIScale);
	const float ViewMinX = CanvasViewRect.Min.X > 0 ? static_cast<float>(CanvasViewRect.Min.X) / DPIScale : 0.0f;
	const float ViewMinY = CanvasViewRect.Min.Y > 0 ? static_cast<float>(CanvasViewRect.Min.Y) / DPIScale : 0.0f;
	const float AvailableWidth = FMath::Max(320.0f, ViewWidth - 32.0f);
	const float PanelWidth = GetStatPanelWidth(ViewWidth, AvailableWidth);
	const float PanelX = GetStatPanelX(ViewMinX, ViewWidth, PanelWidth);
	const float PanelY = ViewMinY + FMath::Clamp(ViewHeight * 0.055f, 32.0f, 64.0f);
	const float PaddingX = 18.0f;
	const float TitleHeight = 20.0f;
	const float StatusHeight = 17.0f;
	const float HeaderHeight = 19.0f;
	const float RowHeight = 16.0f;
	const float BottomPadding = 10.0f;
	const int32 VisibleRows = GCachedObjectRows.Num() > 0 ? GCachedObjectRows.Num() : 1;
	const float PanelHeight = PaddingX + TitleHeight + StatusHeight + HeaderHeight + static_cast<float>(VisibleRows) * RowHeight + BottomPadding;
	const float TableX = PanelX + PaddingX;
	const float TableY = PanelY + PaddingX + TitleHeight + StatusHeight;

	DrawStatTile(Canvas, FVector2D(PanelX, PanelY), FVector2D(PanelWidth, PanelHeight), FLinearColor(0.025f, 0.026f, 0.028f, 0.78f));
	DrawStatTile(Canvas, FVector2D(PanelX, TableY), FVector2D(PanelWidth, HeaderHeight), FLinearColor(0.18f, 0.18f, 0.18f, 0.86f));

	const float ObjectX = TableX;
	const float TotalX = PanelX + PanelWidth - 428.0f;
	const float ObjectKBX = PanelX + PanelWidth - 338.0f;
	const float ResourceKBX = PanelX + PanelWidth - 252.0f;
	const float UsersX = PanelX + PanelWidth - 160.0f;
	const float ClassX = PanelX + PanelWidth - 98.0f;
	const int32 ObjectNameChars = FMath::Clamp(static_cast<int32>((TotalX - ObjectX - 18.0f) / 7.0f), 24, 74);

	FCanvasTextItem TextItem(FVector2D::ZeroVector, FText::GetEmpty(), Font, FLinearColor::White);
	TextItem.EnableShadow(FLinearColor::Black);

	const FString TitleText = TEXT("OBJECT MEMORY SNAPSHOT");
	const FString StatusText = FString::Printf(TEXT("MemReport snapshot | Objects %d | Sources %d | Targets %d | Debug %s"),
		GCachedObjectDebugRows.Num(),
		GLastObjectSnapshotSourceCount,
		GLastObjectDebugComponentCount,
		*GetObjectDebugModeLabel());

	TextItem.SetColor(FLinearColor(0.95f, 0.95f, 0.92f, 1.0f));
	TextItem.Text = FText::FromString(TitleText);
	Canvas->DrawItem(TextItem, FVector2D(PanelX + PaddingX, PanelY + 8.0f));

	TextItem.SetColor(FLinearColor(0.62f, 0.72f, 0.82f, 1.0f));
	TextItem.Text = FText::FromString(StatusText);
	Canvas->DrawItem(TextItem, FVector2D(PanelX + PaddingX, PanelY + 27.0f));

	TextItem.SetColor(FLinearColor(1.0f, 0.63f, 0.18f, 1.0f));
	TextItem.Text = FText::FromString(TEXT("Object"));
	Canvas->DrawItem(TextItem, FVector2D(ObjectX, TableY + 2.0f));
	TextItem.Text = FText::FromString(TEXT("TotalMB"));
	Canvas->DrawItem(TextItem, FVector2D(TotalX, TableY + 2.0f));
	TextItem.Text = FText::FromString(TEXT("ObjKB"));
	Canvas->DrawItem(TextItem, FVector2D(ObjectKBX, TableY + 2.0f));
	TextItem.Text = FText::FromString(TEXT("ResKB"));
	Canvas->DrawItem(TextItem, FVector2D(ResourceKBX, TableY + 2.0f));
	TextItem.Text = FText::FromString(TEXT("Users"));
	Canvas->DrawItem(TextItem, FVector2D(UsersX, TableY + 2.0f));
	TextItem.Text = FText::FromString(TEXT("Class"));
	Canvas->DrawItem(TextItem, FVector2D(ClassX, TableY + 2.0f));

	float RowY = TableY + HeaderHeight;
	if (GCachedObjectRows.Num() == 0)
	{
		DrawStatTile(Canvas, FVector2D(PanelX, RowY), FVector2D(PanelWidth, RowHeight), FLinearColor(0.10f, 0.10f, 0.10f, 0.62f));
		TextItem.SetColor(FLinearColor::Yellow);
		TextItem.Text = FText::FromString(TEXT("No object memory snapshot. Use 'stat obj'."));
		Canvas->DrawItem(TextItem, FVector2D(ObjectX, RowY + 1.0f));
		RowY += RowHeight;
		return static_cast<int32>(PanelY + PanelHeight + 4.0f);
	}

	for (int32 RowIndex = 0; RowIndex < GCachedObjectRows.Num(); ++RowIndex)
	{
		const FObjectMemorySnapshotRow& Row = GCachedObjectRows[RowIndex];
		const float TotalMB = Row.GetTotalMB();
		const FLinearColor RowColor = GetObjectMemorySnapshotColor(TotalMB);
		const FLinearColor BandColor = (RowIndex % 2) == 0
			? FLinearColor(0.11f, 0.11f, 0.11f, 0.66f)
			: FLinearColor(0.18f, 0.18f, 0.18f, 0.66f);

		DrawStatTile(Canvas, FVector2D(PanelX, RowY), FVector2D(PanelWidth, RowHeight), BandColor);
		TextItem.SetColor(RowColor);
		TextItem.Text = FText::FromString(GetObjectMemoryTableName(Row, ObjectNameChars));
		Canvas->DrawItem(TextItem, FVector2D(ObjectX, RowY + 1.0f));

		TextItem.Text = FText::FromString(FString::Printf(TEXT("%7.2f"), TotalMB));
		Canvas->DrawItem(TextItem, FVector2D(TotalX, RowY + 1.0f));
		TextItem.Text = FText::FromString(FString::Printf(TEXT("%6llu"), static_cast<unsigned long long>(Row.ObjectBytes / 1024u)));
		Canvas->DrawItem(TextItem, FVector2D(ObjectKBX, RowY + 1.0f));
		TextItem.Text = FText::FromString(FString::Printf(TEXT("%6llu"), static_cast<unsigned long long>(Row.ResourceBytes / 1024u)));
		Canvas->DrawItem(TextItem, FVector2D(ResourceKBX, RowY + 1.0f));
		TextItem.Text = FText::FromString(FString::Printf(TEXT("%5d"), Row.UserCount));
		Canvas->DrawItem(TextItem, FVector2D(UsersX, RowY + 1.0f));
		TextItem.Text = FText::FromString(CompactPath(Row.ClassName, 14));
		Canvas->DrawItem(TextItem, FVector2D(ClassX, RowY + 1.0f));

		RowY += RowHeight;
	}

	return static_cast<int32>(PanelY + PanelHeight + 4.0f);
}

static int32 RenderStat(UWorld* World, FViewport* Viewport, FCanvas* Canvas, int32 X, int32 Y, const FVector* ViewLocation, const FRotator* ViewRotation)
{
	if (!World || !Canvas || !GEngine)
	{
		return Y;
	}

	if (CVarDebug.GetValueOnGameThread() == 0 && !GMaterialReplayActive)
	{
		ClearCachedDebugOverlay(World);
	}

	UFont* Font = GEngine->GetSmallFont();
	if (!Font)
	{
		return Y;
	}

	const FIntRect CanvasViewRect = Canvas->GetViewRect();
	const FIntPoint FallbackViewSize = Canvas->GetRenderTarget() ? Canvas->GetRenderTarget()->GetSizeXY() : FIntPoint(1280, 720);
	FCommonViewportClient* RenderingViewportClient = FindViewportClientForViewport(Viewport);
	if (DisablePluginViewportStatsForConflictingExternalStat(World, RenderingViewportClient))
	{
		return Y;
	}

	if (GMaterialReplayActive)
	{
		ApplyMaterialReplayTime(World, RenderingViewportClient, GMaterialReplayCurrentTimeSeconds);
		EnsureMaterialReplayOverlay(RenderingViewportClient);
	}
	else
	{
		RemoveMaterialReplayOverlay();
	}
	const float DPIScale = FMath::Max(Canvas->GetDPIScale(), 0.01f);
	const float ViewWidth = FMath::Max(320.0f, static_cast<float>(CanvasViewRect.Width() > 0 ? CanvasViewRect.Width() : FallbackViewSize.X) / DPIScale);
	const float ViewHeight = FMath::Max(240.0f, static_cast<float>(CanvasViewRect.Height() > 0 ? CanvasViewRect.Height() : FallbackViewSize.Y) / DPIScale);
	const float ViewMinX = CanvasViewRect.Min.X > 0 ? static_cast<float>(CanvasViewRect.Min.X) / DPIScale : 0.0f;
	const float ViewMinY = CanvasViewRect.Min.Y > 0 ? static_cast<float>(CanvasViewRect.Min.Y) / DPIScale : 0.0f;
	const float AvailableWidth = FMath::Max(320.0f, ViewWidth - 32.0f);
	const float PanelWidth = GetStatPanelWidth(ViewWidth, AvailableWidth);
	const float PanelX = GetStatPanelX(ViewMinX, ViewWidth, PanelWidth);
	const float PanelY = ViewMinY + FMath::Clamp(ViewHeight * 0.055f, 32.0f, 64.0f);
	const float PaddingX = 18.0f;
	const float TitleHeight = 20.0f;
	const float StatusHeight = 17.0f;
	const float HeaderHeight = 19.0f;
	const float RowHeight = 16.0f;
	const float BottomPadding = 10.0f;
	const TArray<FMaterialAccumulator>& DisplayRows = GMaterialReplayActive ? GMaterialReplayCurrentRows : GCachedRows;
	const TArray<FMaterialAccumulator>& AllRows = GMaterialReplayActive ? GMaterialReplayCurrentRowsAll : GCachedRowsAll;
	const bool bHasMaterialRows = DisplayRows.Num() > 0;
	const int32 VisibleRows = bHasMaterialRows ? DisplayRows.Num() + 1 : 1;
	const float PanelHeight = PaddingX + TitleHeight + StatusHeight + HeaderHeight + static_cast<float>(VisibleRows) * RowHeight + BottomPadding;
	const float TableX = PanelX + PaddingX;
	const float TableY = PanelY + PaddingX + TitleHeight + StatusHeight;
	const float TableWidth = PanelWidth - PaddingX * 2.0f;

	DrawStatTile(Canvas, FVector2D(PanelX, PanelY), FVector2D(PanelWidth, PanelHeight), FLinearColor(0.025f, 0.026f, 0.028f, 0.78f));
	DrawStatTile(Canvas, FVector2D(PanelX, TableY), FVector2D(PanelWidth, HeaderHeight), FLinearColor(0.18f, 0.18f, 0.18f, 0.86f));

	const float MaterialX = TableX;
	const float AvgX = PanelX + PanelWidth - 366.0f;
	const float DrawEventsX = PanelX + PanelWidth - 288.0f;
	const float CompsX = PanelX + PanelWidth - 214.0f;
	const float BlendX = PanelX + PanelWidth - 146.0f;
	const float TrisX = PanelX + PanelWidth - 82.0f;
	const int32 MaterialNameChars = FMath::Clamp(static_cast<int32>((AvgX - MaterialX - 18.0f) / 7.0f), 24, 84);

	FCanvasTextItem TextItem(FVector2D::ZeroVector, FText::GetEmpty(), Font, FLinearColor::White);
	TextItem.EnableShadow(FLinearColor::Black);

	const TCHAR* CaptureState = GCaptureActive ? TEXT("Recording") : (GCaptureFrozen ? TEXT("Captured") : TEXT("Idle"));
	const FString ReplayState = GMaterialReplayActive
		? FString::Printf(TEXT("Replay %s %.2fs/%.2fs"),
			GMaterialReplayPlaying ? TEXT("Playing") : TEXT("Paused"),
			GMaterialReplayCurrentTimeSeconds,
			GetMaterialReplayDurationSeconds())
		: FString::Printf(TEXT("Replay %s"), GMaterialReplaySamples.Num() > 0 ? TEXT("Ready") : TEXT("Off"));
	const FString TitleText = TEXT("MATERIAL GPU PREVIEW");
	const FString StatusText = FString::Printf(TEXT("Insights %s %.1fs | Frames %llu | Materials %d/%d | DebugComps %d | Debug %s | %s"),
		CaptureState,
		GetCaptureDurationSeconds(),
		static_cast<unsigned long long>(GLastTraceFrameCount),
		DisplayRows.Num(),
		AllRows.Num(),
		GLastDebugComponentCount,
		*GetMaterialDebugModeLabel(),
		*ReplayState);

	TextItem.SetColor(FLinearColor(0.95f, 0.95f, 0.92f, 1.0f));
	TextItem.Text = FText::FromString(TitleText);
	Canvas->DrawItem(TextItem, FVector2D(PanelX + PaddingX, PanelY + 8.0f));

	TextItem.SetColor(FLinearColor(0.62f, 0.72f, 0.82f, 1.0f));
	TextItem.Text = FText::FromString(StatusText);
	Canvas->DrawItem(TextItem, FVector2D(PanelX + PaddingX, PanelY + 27.0f));

	TextItem.SetColor(FLinearColor(1.0f, 0.63f, 0.18f, 1.0f));
	TextItem.Text = FText::FromString(TEXT("Material"));
	Canvas->DrawItem(TextItem, FVector2D(MaterialX, TableY + 2.0f));
	TextItem.Text = FText::FromString(TEXT("GPU(ms)"));
	Canvas->DrawItem(TextItem, FVector2D(AvgX, TableY + 2.0f));
	TextItem.Text = FText::FromString(TEXT("DrawEv/F"));
	Canvas->DrawItem(TextItem, FVector2D(DrawEventsX, TableY + 2.0f));
	TextItem.Text = FText::FromString(TEXT("Comps"));
	Canvas->DrawItem(TextItem, FVector2D(CompsX, TableY + 2.0f));
	TextItem.Text = FText::FromString(TEXT("Blend"));
	Canvas->DrawItem(TextItem, FVector2D(BlendX, TableY + 2.0f));
	TextItem.Text = FText::FromString(TEXT("Tris"));
	Canvas->DrawItem(TextItem, FVector2D(TrisX, TableY + 2.0f));

	float RowY = TableY + HeaderHeight;
	if (!bHasMaterialRows)
	{
		DrawStatTile(Canvas, FVector2D(PanelX, RowY), FVector2D(PanelWidth, RowHeight), FLinearColor(0.10f, 0.10f, 0.10f, 0.62f));
		TextItem.SetColor(FLinearColor::Yellow);
		TextItem.Text = FText::FromString(GMaterialReplayActive
			? TEXT("No material GPU sample at this replay time.")
			: TEXT("No Insights material data. Use 'stat mat start', then 'stat mat end'."));
		Canvas->DrawItem(TextItem, FVector2D(MaterialX, RowY + 1.0f));
		RowY += RowHeight;
		return static_cast<int32>(PanelY + PanelHeight + 4.0f);
	}

	const float TotalGpuMs = GMaterialReplayActive ? GetMaterialReplayCurrentFrameGpuMs() : GMaterialReplayFrameGpuMsMax;
	DrawStatTile(Canvas, FVector2D(PanelX, RowY), FVector2D(PanelWidth, RowHeight), FLinearColor(0.08f, 0.12f, 0.14f, 0.78f));
	TextItem.SetColor(GetMaterialGpuPreviewColor(TotalGpuMs));
	TextItem.Text = FText::FromString(TEXT("TOTAL"));
	Canvas->DrawItem(TextItem, FVector2D(MaterialX, RowY + 1.0f));
	TextItem.Text = FText::FromString(FString::Printf(TEXT("%7.2f"), TotalGpuMs));
	Canvas->DrawItem(TextItem, FVector2D(AvgX, RowY + 1.0f));
	TextItem.SetColor(FLinearColor(0.52f, 0.60f, 0.64f, 0.92f));
	TextItem.Text = FText::FromString(TEXT("-"));
	Canvas->DrawItem(TextItem, FVector2D(DrawEventsX, RowY + 1.0f));
	Canvas->DrawItem(TextItem, FVector2D(CompsX, RowY + 1.0f));
	Canvas->DrawItem(TextItem, FVector2D(BlendX, RowY + 1.0f));
	Canvas->DrawItem(TextItem, FVector2D(TrisX, RowY + 1.0f));
	RowY += RowHeight;

	for (int32 RowIndex = 0; RowIndex < DisplayRows.Num(); ++RowIndex)
	{
		const FMaterialAccumulator& Row = DisplayRows[RowIndex];
		const float DisplayMs = GetSeverityMs(Row);
		const double DrawEventsPerFrame = GMaterialReplayActive
			? static_cast<double>(Row.TraceDrawEvents)
			: static_cast<double>(Row.TraceDrawEvents) / static_cast<double>(FMath::Max<uint64>(GLastTraceFrameCount, 1));
		const FLinearColor RowColor = GetMaterialGpuPreviewColor(DisplayMs);
		const FLinearColor BandColor = ((RowIndex + 1) % 2) == 0
			? FLinearColor(0.11f, 0.11f, 0.11f, 0.66f)
			: FLinearColor(0.18f, 0.18f, 0.18f, 0.66f);

		DrawStatTile(Canvas, FVector2D(PanelX, RowY), FVector2D(PanelWidth, RowHeight), BandColor);
		TextItem.SetColor(RowColor);
		TextItem.Text = FText::FromString(GetMaterialTableName(Row, MaterialNameChars));
		Canvas->DrawItem(TextItem, FVector2D(MaterialX, RowY + 1.0f));

		TextItem.Text = FText::FromString(FString::Printf(TEXT("%7.2f"), Row.MaxGpuMs));
		Canvas->DrawItem(TextItem, FVector2D(AvgX, RowY + 1.0f));
		TextItem.Text = FText::FromString(FString::Printf(TEXT("%7.2f"), DrawEventsPerFrame));
		Canvas->DrawItem(TextItem, FVector2D(DrawEventsX, RowY + 1.0f));
		TextItem.Text = FText::FromString(FString::Printf(TEXT("%5d"), Row.ComponentCount));
		Canvas->DrawItem(TextItem, FVector2D(CompsX, RowY + 1.0f));
		TextItem.Text = FText::FromString(GetBlendModeShortName(Row.BlendMode));
		Canvas->DrawItem(TextItem, FVector2D(BlendX, RowY + 1.0f));
		TextItem.Text = FText::FromString(FString::Printf(TEXT("%6lld"), Row.Triangles));
		Canvas->DrawItem(TextItem, FVector2D(TrisX, RowY + 1.0f));

		RowY += RowHeight;
	}

	return static_cast<int32>(PanelY + PanelHeight + 4.0f);
}
}

void FOptimizationPreviewToolsModule::StartupModule()
{
	RegisterStat();
	OptimizationPreviewTools::InstallProfilingInputProcessor();
	OptimizationPreviewTools::RegisterActorColorationHandler();
	OptimizationPreviewTools::RegisterConsoleAutoComplete();
#if WITH_EDITOR
	OptimizationPreviewTools::RegisterEditorDelegates();
#endif
}

void FOptimizationPreviewToolsModule::ShutdownModule()
{
#if WITH_EDITOR
	OptimizationPreviewTools::UnregisterEditorDelegates();
#endif
	OptimizationPreviewTools::UnregisterConsoleAutoComplete();
	UnregisterStat();
	OptimizationPreviewTools::RemoveProfilingInputProcessor();
	OptimizationPreviewTools::UnregisterActorColorationHandler();
}

void FOptimizationPreviewToolsModule::RegisterStat()
{
	if (!GEngine)
	{
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("GEngine is not available; Optimization Preview Tools stats were not registered."));
		return;
	}

	GEngine->AddEngineStat(
		OptimizationPreviewTools::EngineStatName,
		OptimizationPreviewTools::EngineStatCategory,
		LOCTEXT("MaterialGPUPreviewDescription", "Display Insights material GPU costs with Actor Coloration or fallback debug overlays."),
		UEngine::FEngineStatRender::CreateStatic(&OptimizationPreviewTools::RenderStat),
		UEngine::FEngineStatToggle::CreateStatic(&OptimizationPreviewTools::ToggleStat),
		false);

	GEngine->AddEngineStat(
		OptimizationPreviewTools::EngineStatAliasName,
		OptimizationPreviewTools::EngineStatCategory,
		LOCTEXT("MaterialGPUPreviewAliasDescription", "Alias for stat material. Use stat mat start/end for Material GPU Preview captures."),
		UEngine::FEngineStatRender(),
		UEngine::FEngineStatToggle::CreateStatic(&OptimizationPreviewTools::ToggleStat),
		false);

	GEngine->AddEngineStat(
		OptimizationPreviewTools::MaterialModeEngineStatName,
		OptimizationPreviewTools::EngineStatCategory,
		LOCTEXT("MaterialGPUPreviewModeDescription", "Toggle Material GPU Preview debug colors without hiding the stat or replay UI."),
		UEngine::FEngineStatRender(),
		UEngine::FEngineStatToggle::CreateStatic(&OptimizationPreviewTools::ToggleMaterialModeStat),
		false);

	GEngine->AddEngineStat(
		OptimizationPreviewTools::ObjectEngineStatName,
		OptimizationPreviewTools::EngineStatCategory,
		LOCTEXT("ObjectMemorySnapshotDescription", "Create and display a memreport-style Object Memory Snapshot for the current world."),
		UEngine::FEngineStatRender::CreateStatic(&OptimizationPreviewTools::RenderObjectStat),
		UEngine::FEngineStatToggle::CreateStatic(&OptimizationPreviewTools::ToggleObjectStat),
		false);

	GEngine->AddEngineStat(
		OptimizationPreviewTools::ProfilingEngineStatName,
		OptimizationPreviewTools::EngineStatCategory,
		LOCTEXT("OptimizationProfilingDescription", "Show Optimization Preview Tools command buttons under the active profiling stat panel."),
		UEngine::FEngineStatRender::CreateStatic(&OptimizationPreviewTools::RenderProfilingStat),
		UEngine::FEngineStatToggle::CreateStatic(&OptimizationPreviewTools::ToggleProfilingStat),
		false);
}

void FOptimizationPreviewToolsModule::UnregisterStat()
{
	OptimizationPreviewTools::RemoveProfilingSlateOverlay();
	OptimizationPreviewTools::StopInsightsTraceIfNeeded();
	OptimizationPreviewTools::RestoreInsightsMaterialCaptureCvars();
	OptimizationPreviewTools::DisableActorColoration(nullptr, nullptr);
	OptimizationPreviewTools::ClearCaptureState();
	OptimizationPreviewTools::ClearObjectMemorySnapshotState();
	OptimizationPreviewTools::ClearCachedDebugOverlay(nullptr);

	if (GEngine)
	{
		GEngine->RemoveEngineStat(OptimizationPreviewTools::EngineStatName);
		GEngine->RemoveEngineStat(OptimizationPreviewTools::EngineStatAliasName);
		GEngine->RemoveEngineStat(OptimizationPreviewTools::MaterialModeEngineStatName);
		GEngine->RemoveEngineStat(OptimizationPreviewTools::ObjectEngineStatName);
		GEngine->RemoveEngineStat(OptimizationPreviewTools::ProfilingEngineStatName);
	}
}

IMPLEMENT_MODULE(FOptimizationPreviewToolsModule, OptimizationPreviewTools)

#undef LOCTEXT_NAMESPACE
