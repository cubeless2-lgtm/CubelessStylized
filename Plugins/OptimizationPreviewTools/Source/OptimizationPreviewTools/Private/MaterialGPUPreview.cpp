#include "OptimizationPreviewTools.h"

#include "CanvasItem.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/LineBatchComponent.h"
#include "Components/SkinnedMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "CoreGlobals.h"
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
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformProcess.h"
#include "InputCoreTypes.h"
#include "Framework/Application/SlateApplication.h"
#include "Materials/MaterialInterface.h"
#include "Misc/DateTime.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "PhysicsEngine/BodySetup.h"
#include "ProfilingDebugging/TraceAuxiliary.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "RenderingThread.h"
#include "Serialization/ArchiveCountMem.h"
#include "Serialization/MemoryReader.h"
#include "StaticMeshResources.h"
#include "Styling/CoreStyle.h"
#include "TraceServices/AnalysisService.h"
#include "TraceServices/Containers/Timelines.h"
#include "TraceServices/ITraceServicesModule.h"
#include "TraceServices/Model/AnalysisSession.h"
#include "TraceServices/Model/Frames.h"
#include "TraceServices/Model/TimingProfiler.h"
#include "UObject/ObjectKey.h"
#include "UObject/UObjectGlobals.h"
#include "UObject/WeakObjectPtrTemplates.h"
#include "ViewportClient.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
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

#define LOCTEXT_NAMESPACE "OptimizationPreviewTools"

namespace OptimizationPreviewTools
{
static const FString StatName = TEXT("Material");
static const FString StatAliasName = TEXT("Mat");
static const FString ObjectStatName = TEXT("Obj");
static const FString ProfilingStatName = TEXT("Profiling");
static const FName EngineStatName(TEXT("STAT_Material"));
static const FName EngineStatAliasName(TEXT("STAT_Mat"));
static const FName ObjectEngineStatName(TEXT("STAT_Obj"));
static const FName ProfilingEngineStatName(TEXT("STAT_Profiling"));
static const FName EngineStatCategory(TEXT("STATCAT_Engine"));
static const FName ActorColorationHandlerName(TEXT("OptimizationPreviewTools"));
static const TCHAR* TraceChannels = TEXT("gpu,frame,stats,log,rendercommands,cpu");

struct FProfilingCommandButtonSpec
{
	const TCHAR* Label;
	const TCHAR* Command;
};

static const FProfilingCommandButtonSpec GProfilingCommandButtons[] =
{
	{ TEXT("MAT START"), TEXT("stat mat start") },
	{ TEXT("MAT END"), TEXT("stat mat end") },
	{ TEXT("MAT OFF"), TEXT("stat mat 0") },
	{ TEXT("OBJ SNAP"), TEXT("stat obj") },
	{ TEXT("OBJ OFF"), TEXT("stat obj 0") }
};

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
static constexpr float DefaultDebugGreenMaxMs = 0.5f;
static constexpr float DefaultDebugWhiteMs = 2.0f;
static constexpr float DefaultObjectDebugGreenMaxMB = 5.0f;
static constexpr float DefaultObjectDebugWhiteMB = 10.0f;

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
	TArray<TWeakObjectPtr<UPrimitiveComponent>> Components;
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

static TArray<FMaterialAccumulator> GCachedRows;
static TArray<FMaterialAccumulator> GCachedDebugRows;
static TArray<FObjectMemorySnapshotRow> GCachedObjectRows;
static TArray<FObjectMemorySnapshotRow> GCachedObjectDebugRows;
static TArray<FDebugOverlayEntry> GCachedDebugEntries;
static TMap<FObjectKey, FLinearColor> GActorColorationColors;
static double GCaptureStartTime = -1.0;
static double GCaptureEndTime = -1.0;
static TWeakObjectPtr<UWorld> GCachedDebugWorld;
static TWeakObjectPtr<UWorld> GActorColorationWorld;
static TWeakObjectPtr<UGameViewportClient> GActorColorationGameViewport;
static bool GCaptureActive = false;
static bool GCaptureFrozen = false;
static bool GTraceStartedByCapture = false;
static bool GActorColorationHandlerRegistered = false;
static bool GActorColorationActive = false;
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
static TWeakObjectPtr<UGameViewportClient> GProfilingSlateOverlayViewport;
static TWeakObjectPtr<UGameViewportClient> GProfilingInputOverrideViewport;
static FOverrideInputKeyHandler GPreviousProfilingInputOverride;
static FDelegateHandle GProfilingInputOverrideHandle;
static bool GHadPreviousProfilingInputOverride = false;
static float GProfilingSlateOverlayLeft = 260.0f;
static float GProfilingSlateOverlayTop = 300.0f;
static float GProfilingSlateOverlayWidth = 760.0f;
static float GProfilingSlateOverlayHeight = 36.0f;
static float GProfilingSlateViewportWidth = 1920.0f;
static float GProfilingSlateViewportHeight = 1080.0f;

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

static float GetCaptureDurationSeconds()
{
	if (GCaptureStartTime < 0.0)
	{
		return 0.0f;
	}

	const double EndTime = GCaptureActive ? FPlatformTime::Seconds() : GCaptureEndTime;
	return static_cast<float>(FMath::Max(0.0, EndTime - GCaptureStartTime));
}

static void ClearCaptureState()
{
	GCaptureStartTime = -1.0;
	GCaptureEndTime = -1.0;
	GCaptureActive = false;
	GCaptureFrozen = false;
	GTraceStartedByCapture = false;
	GTraceFilePath.Reset();
	GLastTraceFrameCount = 0;
	GLastDebugMaterialCount = 0;
	GLastDebugComponentCount = 0;
	GCachedRows.Reset();
	GCachedDebugRows.Reset();
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

static float GetDebugGreenMaxMs()
{
	return FMath::Max(ReadMaterialGPUPreviewConfigFloat(TEXT("DebugGreenMaxMs"), DefaultDebugGreenMaxMs), 0.001f);
}

static float GetDebugWhiteMs()
{
	return FMath::Max(ReadMaterialGPUPreviewConfigFloat(TEXT("DebugWhiteMs"), DefaultDebugWhiteMs), GetDebugGreenMaxMs() + 0.001f);
}

static float GetObjectDebugGreenMaxMB()
{
	return FMath::Max(ReadObjectMemorySnapshotConfigFloat(TEXT("DebugGreenMaxMB"), DefaultObjectDebugGreenMaxMB), 0.001f);
}

static float GetObjectDebugWhiteMB()
{
	return FMath::Max(ReadObjectMemorySnapshotConfigFloat(TEXT("DebugWhiteMB"), DefaultObjectDebugWhiteMB), GetObjectDebugGreenMaxMB() + 0.001f);
}

static FLinearColor SampleColorRange(const TArray<FLinearColor>& Colors, int32 StartIndex, int32 EndIndex, float Alpha)
{
	if (Colors.Num() == 0)
	{
		return FLinearColor::White;
	}

	StartIndex = FMath::Clamp(StartIndex, 0, Colors.Num() - 1);
	EndIndex = FMath::Clamp(EndIndex, 0, Colors.Num() - 1);
	if (StartIndex == EndIndex)
	{
		return Colors[StartIndex];
	}

	const float RangePosition = FMath::Clamp(Alpha, 0.0f, 1.0f) * static_cast<float>(EndIndex - StartIndex);
	const int32 LowerIndex = StartIndex + FMath::FloorToInt(RangePosition);
	const int32 UpperIndex = FMath::Min(LowerIndex + 1, EndIndex);
	const float Blend = RangePosition - FMath::FloorToFloat(RangePosition);
	return FMath::Lerp(Colors[LowerIndex], Colors[UpperIndex], Blend);
}

static FLinearColor GetFallbackComplexityColorForRange(float Value, float GreenMax, float White)
{
	if (Value >= White)
	{
		return FLinearColor(1.0f, 0.9f, 0.9f, 1.0f);
	}

	if (Value < GreenMax)
	{
		return FMath::Lerp(
			FLinearColor(0.0f, 1.0f, 0.127f, 1.0f),
			FLinearColor(0.046f, 0.52f, 0.0f, 1.0f),
			FMath::Clamp(Value / GreenMax, 0.0f, 1.0f));
	}

	return FMath::Lerp(
		FLinearColor(0.52f, 0.046f, 0.0f, 1.0f),
		FLinearColor(1.0f, 0.9f, 0.9f, 1.0f),
		FMath::Clamp((Value - GreenMax) / (White - GreenMax), 0.0f, 1.0f));
}

static FLinearColor GetComplexityPreviewColorForRange(float Value, float GreenMax, float White, float Alpha = 1.0f)
{
	FLinearColor Color = GetFallbackComplexityColorForRange(Value, GreenMax, White);
	if (GEngine && GEngine->ShaderComplexityColors.Num() > 0)
	{
		const TArray<FLinearColor>& Colors = GEngine->ShaderComplexityColors;
		if (Value >= White)
		{
			Color = Colors.Last();
		}
		else if (Value < GreenMax)
		{
			const int32 GreenEndIndex = FMath::Min(2, Colors.Num() - 1);
			Color = SampleColorRange(Colors, 0, GreenEndIndex, Value / GreenMax);
		}
		else
		{
			const int32 RedStartIndex = FMath::Min(4, Colors.Num() - 1);
			Color = SampleColorRange(Colors, RedStartIndex, Colors.Num() - 1, (Value - GreenMax) / (White - GreenMax));
		}
	}

	Color.A = Alpha;
	return Color;
}

static FLinearColor GetFallbackComplexityColor(float MaxGpuMs)
{
	return GetFallbackComplexityColorForRange(MaxGpuMs, GetDebugGreenMaxMs(), GetDebugWhiteMs());
}

static FLinearColor GetMaterialGpuPreviewColor(float MaxGpuMs, float Alpha = 1.0f)
{
	return GetComplexityPreviewColorForRange(MaxGpuMs, GetDebugGreenMaxMs(), GetDebugWhiteMs(), Alpha);
}

static FLinearColor GetObjectMemorySnapshotColor(float TotalMB, float Alpha = 1.0f)
{
	return GetComplexityPreviewColorForRange(TotalMB, GetObjectDebugGreenMaxMB(), GetObjectDebugWhiteMB(), Alpha);
}

static int32 GetDebugSeverity(float MaxGpuMs)
{
	if (MaxGpuMs >= GetDebugWhiteMs())
	{
		return 3;
	}

	if (MaxGpuMs >= GetDebugGreenMaxMs())
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

static bool IsDebugTargetComponent(const UPrimitiveComponent* Component)
{
	return Component && Component->IsRegistered() && Component->IsVisible();
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

static void RebuildActorColorationColorMap()
{
	GActorColorationColors.Reset();

	const int32 MaxDebugComponents = GetDebugComponentLimit();

	TMap<UPrimitiveComponent*, FActorColorationTarget> TargetsByComponent;
	for (const FMaterialAccumulator& Row : GCachedDebugRows)
	{
		const float DebugMs = GetSeverityMs(Row);
		const int32 Severity = GetDebugSeverity(DebugMs);
		const FLinearColor Color = GetMaterialGpuPreviewColor(DebugMs);

		for (const TWeakObjectPtr<UPrimitiveComponent>& WeakComponent : Row.Components)
		{
			UPrimitiveComponent* Component = WeakComponent.Get();
			if (!IsDebugTargetComponent(Component))
			{
				continue;
			}

			FActorColorationTarget* ExistingTarget = TargetsByComponent.Find(Component);
			if (ExistingTarget && ExistingTarget->MaxGpuMs >= DebugMs)
			{
				continue;
			}

			FActorColorationTarget Target;
			Target.Component = Component;
			Target.MaxGpuMs = DebugMs;
			Target.Severity = Severity;
			Target.Color = Color;
			TargetsByComponent.Add(Component, Target);
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

static bool TryGetProfilingCommandAtLocalPosition(const FVector2D& LocalPosition, FString& OutCommand)
{
	constexpr float ButtonGap = 8.0f;
	const int32 ButtonCount = UE_ARRAY_COUNT(GProfilingCommandButtons);
	if (ButtonCount <= 0
		|| LocalPosition.Y < GProfilingSlateOverlayTop
		|| LocalPosition.Y > GProfilingSlateOverlayTop + GProfilingSlateOverlayHeight
		|| LocalPosition.X < GProfilingSlateOverlayLeft
		|| LocalPosition.X > GProfilingSlateOverlayLeft + GProfilingSlateOverlayWidth)
	{
		return false;
	}

	const float LocalX = LocalPosition.X - GProfilingSlateOverlayLeft;
	const float SlotWidth = GProfilingSlateOverlayWidth / static_cast<float>(ButtonCount);
	const int32 ButtonIndex = FMath::Clamp(FMath::FloorToInt(LocalX / SlotWidth), 0, ButtonCount - 1);
	const float SlotLocalX = LocalX - SlotWidth * static_cast<float>(ButtonIndex);
	if (ButtonIndex < ButtonCount - 1 && SlotLocalX > SlotWidth - ButtonGap)
	{
		return false;
	}

	OutCommand = GProfilingCommandButtons[ButtonIndex].Command;
	return true;
}

static bool TryGetProfilingCommandUnderCursor(UGameViewportClient* GameViewportClient, FString& OutCommand)
{
	if (!GameViewportClient || !FSlateApplication::IsInitialized())
	{
		return false;
	}

	TSharedPtr<SViewport> ViewportWidget = GameViewportClient->GetGameViewportWidget();
	if (!ViewportWidget.IsValid())
	{
		return false;
	}

	const FVector2D CursorPosition = FSlateApplication::Get().GetCursorPos();
	const FVector2D LocalPosition = ViewportWidget->GetCachedGeometry().AbsoluteToLocal(CursorPosition);
	return TryGetProfilingCommandAtLocalPosition(LocalPosition, OutCommand);
}

static void ExecuteProfilingCommand(const FString& Command)
{
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
	}
}

static FReply ExecuteProfilingSlateCommand(const FString Command)
{
	ExecuteProfilingCommand(Command);

	return FReply::Handled();
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

static TSharedRef<SButton> MakeProfilingSlateButton(const TCHAR* Label, const TCHAR* Command)
{
	return SNew(SButton)
		.ButtonColorAndOpacity(FLinearColor(0.075f, 0.078f, 0.082f, 0.96f))
		.ContentPadding(FMargin(12.0f, 6.0f))
		.ClickMethod(EButtonClickMethod::MouseDown)
		.TouchMethod(EButtonTouchMethod::Down)
		.IsFocusable(false)
		.OnClicked_Lambda([CommandString = FString(Command)]()
		{
			return ExecuteProfilingSlateCommand(CommandString);
		})
		[
			SNew(STextBlock)
			.Text(FText::FromString(Label))
			.ColorAndOpacity(FSlateColor(FLinearColor(0.92f, 0.93f, 0.90f, 1.0f)))
			.Justification(ETextJustify::Center)
		];
}

static TSharedRef<SWidget> BuildProfilingSlateOverlay()
{
	return SNew(SBox)
		.Visibility(EVisibility::SelfHitTestInvisible)
		.WidthOverride(TAttribute<FOptionalSize>::CreateLambda([]()
		{
			return FOptionalSize(GProfilingSlateViewportWidth);
		}))
		.HeightOverride(TAttribute<FOptionalSize>::CreateLambda([]()
		{
			return FOptionalSize(GProfilingSlateViewportHeight);
		}))
		[
			SNew(SOverlay)
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
				.WidthOverride(TAttribute<FOptionalSize>::CreateLambda([]()
				{
					return FOptionalSize(FMath::Max(360.0f, GProfilingSlateOverlayWidth));
				}))
				.HeightOverride(TAttribute<FOptionalSize>::CreateLambda([]()
				{
					return FOptionalSize(GProfilingSlateOverlayHeight);
				}))
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					.Padding(0.0f, 0.0f, 8.0f, 0.0f)
					[
						MakeProfilingSlateButton(GProfilingCommandButtons[0].Label, GProfilingCommandButtons[0].Command)
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					.Padding(0.0f, 0.0f, 8.0f, 0.0f)
					[
						MakeProfilingSlateButton(GProfilingCommandButtons[1].Label, GProfilingCommandButtons[1].Command)
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					.Padding(0.0f, 0.0f, 8.0f, 0.0f)
					[
						MakeProfilingSlateButton(GProfilingCommandButtons[2].Label, GProfilingCommandButtons[2].Command)
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					.Padding(0.0f, 0.0f, 8.0f, 0.0f)
					[
						MakeProfilingSlateButton(GProfilingCommandButtons[3].Label, GProfilingCommandButtons[3].Command)
					]
					+ SHorizontalBox::Slot()
					.FillWidth(1.0f)
					[
						MakeProfilingSlateButton(GProfilingCommandButtons[4].Label, GProfilingCommandButtons[4].Command)
					]
				]
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
	GProfilingSlateOverlayViewport = nullptr;
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
		InstallProfilingInputOverride(GameViewportClient);
		return;
	}

	RemoveProfilingSlateOverlay();
	GProfilingSlateOverlayViewport = GameViewportClient;
	GProfilingSlateOverlayWidget = BuildProfilingSlateOverlay();
	GameViewportClient->AddViewportWidgetContent(GProfilingSlateOverlayWidget.ToSharedRef(), 1000);
	InstallProfilingInputOverride(GameViewportClient);
	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Optimization Profiling Slate command overlay added."));
}

static void DisableActorColoration(UWorld* World, FCommonViewportClient* ViewportClient);

static void ApplyActorColorationViewModeFromCurrentColors(UWorld* World, FCommonViewportClient* ViewportClient)
{
#if !(UE_BUILD_SHIPPING || UE_BUILD_TEST)
	if (!World || !ShouldUseActorColorationBackend())
	{
		return;
	}

	RegisterActorColorationHandler();
	if (GActorColorationColors.Num() == 0)
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
	RegisterConsoleAutoCompleteCommand(TEXT("stat mat 0"), TEXT("Hide Material GPU Preview panel and debug visualization."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat mat 1"), TEXT("Show last Material GPU Preview Insights result."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat mat clear"), TEXT("Clear Material GPU Preview capture state and overlay."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat material"), TEXT("Toggle Material GPU Preview result panel."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat material start"), TEXT("Start Material GPU Preview Insights trace capture."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat material end"), TEXT("Stop trace, analyze utrace, and show the result."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat obj"), TEXT("Create and show an Object Memory Snapshot for the current world."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat obj 0"), TEXT("Hide Object Memory Snapshot panel and debug visualization."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat profiling"), TEXT("Show Optimization Preview Tools command buttons under the active Top 10 stat panel."));
	RegisterConsoleAutoCompleteCommand(TEXT("stat profiling 0"), TEXT("Hide Optimization Preview Tools command buttons."));
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
static bool BuildRowsFromInsightsTrace(UWorld* World);

static bool StartInsightsGpuTrace()
{
	GTraceFilePath = BuildTraceFilePath();

	FTraceAuxiliary::FOptions Options;
	Options.bTruncateFile = true;
	Options.bExcludeTail = true;
	return FTraceAuxiliary::Start(FTraceAuxiliary::EConnectionType::File, *GTraceFilePath, TraceChannels, &Options, LogOptimizationPreviewTools);
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

	StopInsightsTraceIfNeeded();
	RestoreInsightsMaterialCaptureCvars();
	ClearCaptureState();

	GCachedRows.Reset();
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
		RestoreInsightsMaterialCaptureCvars();
		GCaptureActive = false;
		GCaptureEndTime = FPlatformTime::Seconds();
		GLastAnalysisMessage = TEXT("Failed to start Insights trace.");
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Material GPU Preview capture failed to start. Trace=%s Channels=%s"),
			*GTraceFilePath,
			TraceChannels);
		return;
	}

	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Material GPU Preview capture started. Trace=%s Channels=%s StartedTrace=%s"),
		*GTraceFilePath,
		TraceChannels,
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

	FlushRenderingCommands();
	const bool bStoppedTrace = StopInsightsTraceIfNeeded();
	if (bStoppedTrace)
	{
		WaitForTraceFileReady(GTraceFilePath);
	}
	RestoreInsightsMaterialCaptureCvars();
	GCachedRows.Reset();
	GCachedDebugRows.Reset();
	const bool bBuiltTraceRows = BuildRowsFromInsightsTrace(World);
	if (!bBuiltTraceRows)
	{
		GCachedRows.Reset();
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
		CVarDebug->Set(1);
		SetViewportStatEnabled(ViewportClient, true);
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

	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Material GPU Preview capture ended. Duration=%.2fs Rows=%d Source=utrace Trace=%s StoppedTrace=%s Analysis=%s"),
		GetCaptureDurationSeconds(),
		GCachedRows.Num(),
		*GTraceFilePath,
		bStoppedTrace ? TEXT("true") : TEXT("false"),
		*GLastAnalysisMessage);
}

static void SetDebugViewEnabled(UWorld* World, FCommonViewportClient* ViewportClient, bool bEnable)
{
	if (!bEnable)
	{
		CVarDebug->Set(0);
		DisableActorColoration(World, ViewportClient);
		ClearCachedDebugOverlay(World);
		SetViewportStatEnabled(ViewportClient, false);
		return;
	}

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

static bool ToggleStat(UWorld* World, FCommonViewportClient* ViewportClient, const TCHAR* Stream)
{
	FString Args(Stream ? Stream : TEXT(""));
	Args.TrimStartAndEndInline();

	const TCHAR* Cmd = *Args;
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

	if (FParse::Command(&Cmd, TEXT("clear")))
	{
		StopInsightsTraceIfNeeded();
		RestoreInsightsMaterialCaptureCvars();
		ClearCaptureState();
		GCachedRows.Reset();
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

static void AddUsage(TArray<FMaterialAccumulator>& Accumulators, UPrimitiveComponent* Component, UMaterialInterface* Material, int64 Triangles, int64 Instances)
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
		Accumulator.Components.Add(Component);
		Accumulator.ComponentCount++;
	}
}

static void AccumulateStaticMeshComponent(TArray<FMaterialAccumulator>& Accumulators, UStaticMeshComponent* Component)
{
	UStaticMesh* StaticMesh = Component ? Component->GetStaticMesh() : nullptr;
	const FStaticMeshRenderData* RenderData = StaticMesh ? StaticMesh->GetRenderData() : nullptr;
	if (!RenderData || RenderData->LODResources.Num() == 0)
	{
		TArray<UMaterialInterface*> Materials;
		Component->GetUsedMaterials(Materials);
		for (UMaterialInterface* Material : Materials)
		{
			AddUsage(Accumulators, Component, Material, 1, 1);
		}
		return;
	}

	const int64 InstanceCount = Component->IsA<UInstancedStaticMeshComponent>()
		? static_cast<int64>(CastChecked<UInstancedStaticMeshComponent>(Component)->GetInstanceCount())
		: 1;

	const FStaticMeshLODResources& LOD = RenderData->LODResources[0];
	for (const FStaticMeshSection& Section : LOD.Sections)
	{
		UMaterialInterface* Material = Component->GetMaterial(Section.MaterialIndex);
		AddUsage(Accumulators, Component, Material, Section.NumTriangles, InstanceCount);
	}
}

static void AccumulateSkinnedMeshComponent(TArray<FMaterialAccumulator>& Accumulators, USkinnedMeshComponent* Component)
{
	FSkeletalMeshRenderData* RenderData = Component ? Component->GetSkeletalMeshRenderData() : nullptr;
	if (!RenderData || RenderData->LODRenderData.Num() == 0)
	{
		TArray<UMaterialInterface*> Materials;
		Component->GetUsedMaterials(Materials);
		for (UMaterialInterface* Material : Materials)
		{
			AddUsage(Accumulators, Component, Material, 1, 1);
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
		AddUsage(Accumulators, Component, Material, Section.NumTriangles, 1);
	}
}

static void AccumulatePrimitiveComponent(TArray<FMaterialAccumulator>& Accumulators, UPrimitiveComponent* Component)
{
	if (UStaticMeshComponent* StaticMeshComponent = Cast<UStaticMeshComponent>(Component))
	{
		AccumulateStaticMeshComponent(Accumulators, StaticMeshComponent);
		return;
	}

	if (USkinnedMeshComponent* SkinnedMeshComponent = Cast<USkinnedMeshComponent>(Component))
	{
		AccumulateSkinnedMeshComponent(Accumulators, SkinnedMeshComponent);
		return;
	}

	TArray<UMaterialInterface*> Materials;
	Component->GetUsedMaterials(Materials);
	for (UMaterialInterface* Material : Materials)
	{
		AddUsage(Accumulators, Component, Material, 1, 1);
	}
}

static void BuildSceneMaterialAccumulators(UWorld* World, TArray<FMaterialAccumulator>& OutAccumulators)
{
	OutAccumulators.Reset();
	if (!World)
	{
		return;
	}

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
				AccumulatePrimitiveComponent(OutAccumulators, Component);
			}
		}
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

	const double AnalyzeStartTime = FPlatformTime::Seconds();
	TSharedPtr<const TraceServices::IAnalysisSession> Session = AnalysisService->Analyze(*GTraceFilePath);
	if (!Session.IsValid())
	{
		GLastAnalysisMessage = FString::Printf(TEXT("Trace analysis failed: %s"), *GTraceFilePath);
		UE_LOG(LogOptimizationPreviewTools, Warning, TEXT("Material GPU Preview %s"), *GLastAnalysisMessage);
		return false;
	}

	TArray<FMaterialAccumulator> SceneRows;
	BuildSceneMaterialAccumulators(World, SceneRows);
	SortMaterialAccumulators(SceneRows);

	TMap<FString, int32> SceneLookup;
	for (int32 Index = 0; Index < SceneRows.Num(); ++Index)
	{
		AddMaterialLookupKeys(SceneLookup, SceneRows[Index], Index);
	}

	TMap<FString, FTraceMaterialAggregate> AggregatesByMaterial;
	TArray<FString> TraceDiagnosticSamples;
	TSet<FString> SeenTraceDiagnosticSamples;
	uint64 FrameCount = 0;
	int32 GpuQueueCount = 0;
	int32 InspectedGpuEventCount = 0;
	int32 MaterialDrawEventCount = 0;
	int32 MatchedTraceEventCount = 0;

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
							InspectedGpuEventCount++;
							if (TraceDiagnosticSamples.Num() < 24)
							{
								const FString TrimmedEventName = TraceEventName.Left(180);
								AddTraceDiagnosticSample(
									TraceDiagnosticSamples,
									SeenTraceDiagnosticSamples,
									FString::Printf(TEXT("%s | %s | %.3fms"), *BaseTimerName, *TrimmedEventName, DurationMs));
							}

							const FString MaterialName = FindMaterialNameForTraceEvent(SceneRows, SceneLookup, TraceEventName, BaseTimerName);
							if (MaterialName.IsEmpty())
							{
								return TraceServices::EEventEnumerate::Continue;
							}

							const uint32 FrameIndex = FrameProvider.GetFrameNumberForTimestamp(FrameType, EventStartTime);
							FTraceMaterialAggregate& Aggregate = AggregatesByMaterial.FindOrAdd(NormalizeTraceLookupKey(MaterialName));
							if (Aggregate.MaterialName.IsEmpty())
							{
								Aggregate.MaterialName = MaterialName;
							}
							Aggregate.EventName = TraceEventName;
							Aggregate.TotalGpuMs += DurationMs;
							Aggregate.DrawEvents++;
							Aggregate.GpuMsByFrame.FindOrAdd(FrameIndex) += DurationMs;
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
	}

	if (AggregatesByMaterial.Num() == 0)
	{
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

	GCachedRows.Reset();
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
		if (bMatchedSceneMaterial && GCachedRows.Num() < TopN)
		{
			GCachedRows.Add(Row);
		}
		if (bMatchedSceneMaterial)
		{
			GCachedDebugRows.Add(MoveTemp(Row));
		}
	}

	GLastDebugMaterialCount = GCachedDebugRows.Num();
	GLastDebugComponentCount = CountUniqueDebugComponents(GCachedDebugRows);

	GLastAnalysisMessage = FString::Printf(TEXT("Insights rows=%d debugMaterials=%d debugComps=%d frames=%llu materialEvents=%d trace=%s"),
		GCachedRows.Num(),
		GLastDebugMaterialCount,
		GLastDebugComponentCount,
		static_cast<unsigned long long>(FrameCount),
		MaterialDrawEventCount,
		*GTraceFilePath);

	UE_LOG(LogOptimizationPreviewTools, Display, TEXT("Material GPU Preview trace analysis complete. Rows=%d TraceMaterials=%d DebugMaterials=%d DebugComponents=%d InspectedEvents=%d MaterialDrawEvents=%d MatchedEvents=%d Frames=%llu Queues=%d Analyze=%.2fs Trace=%s"),
		GCachedRows.Num(),
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

static float GetProfilingCommandButtonHeight()
{
	return 40.0f;
}

static float GetProfilingCommandBarHeight()
{
	return 50.0f;
}

static float GetProfilingCommandBarTotalHeight()
{
	return GetProfilingCommandBarHeight() + 14.0f;
}

static float GetStatPanelWidth(float ViewWidth, float AvailableWidth)
{
	return FMath::Min(FMath::Clamp(ViewWidth * 0.76f, 640.0f, 1080.0f), AvailableWidth);
}

static float GetStatPanelX(float ViewMinX, float ViewWidth, float PanelWidth)
{
	return ViewMinX + FMath::Max(16.0f, (ViewWidth - PanelWidth) * 0.5f);
}

static float DrawProfilingCommandBar(FCanvas* Canvas, UFont* Font, float PanelX, float ToolbarY, float PanelWidth, float SlateButtonY)
{
	if (!Canvas || !Font)
	{
		return 0.0f;
	}

	const float BarHeight = GetProfilingCommandBarHeight();
	const float ButtonHeight = GetProfilingCommandButtonHeight();
	const float PaddingX = 18.0f;
	const float InnerX = PanelX + PaddingX;
	const FIntRect CanvasViewRect = Canvas->GetViewRect();
	const FIntPoint FallbackViewSize = Canvas->GetRenderTarget() ? Canvas->GetRenderTarget()->GetSizeXY() : FIntPoint(1280, 720);
	const float DPIScale = FMath::Max(Canvas->GetDPIScale(), 0.01f);
	const float ViewWidth = FMath::Max(320.0f, static_cast<float>(CanvasViewRect.Width() > 0 ? CanvasViewRect.Width() : FallbackViewSize.X) / DPIScale);
	const float ViewHeight = FMath::Max(240.0f, static_cast<float>(CanvasViewRect.Height() > 0 ? CanvasViewRect.Height() : FallbackViewSize.Y) / DPIScale);
	const float ViewMinX = CanvasViewRect.Min.X > 0 ? static_cast<float>(CanvasViewRect.Min.X) / DPIScale : 0.0f;
	const float ViewMinY = CanvasViewRect.Min.Y > 0 ? static_cast<float>(CanvasViewRect.Min.Y) / DPIScale : 0.0f;
	const float SlateScale = DPIScale;
	const float SlateButtonVisualWidthCompensation = 16.0f;
	GProfilingSlateOverlayLeft = FMath::Max(0.0f, PanelX * SlateScale);
	GProfilingSlateOverlayTop = FMath::Max(0.0f, (SlateButtonY - ViewMinY) * SlateScale);
	GProfilingSlateOverlayWidth = FMath::Max(360.0f, (PanelWidth * SlateScale) + SlateButtonVisualWidthCompensation);
	GProfilingSlateOverlayHeight = ButtonHeight;
	GProfilingSlateViewportWidth = ViewWidth * SlateScale;
	GProfilingSlateViewportHeight = ViewHeight * SlateScale;

	DrawStatTile(Canvas, FVector2D(PanelX, ToolbarY), FVector2D(PanelWidth, BarHeight), FLinearColor(0.035f, 0.037f, 0.04f, 0.86f));
	DrawStatLine(Canvas, FVector2D(PanelX, ToolbarY), FVector2D(PanelX + PanelWidth, ToolbarY), FLinearColor(0.46f, 0.46f, 0.43f, 0.55f));

	const float CommandY = ToolbarY + BarHeight + 2.0f;
	FCanvasTextItem CommandTextItem(FVector2D(InnerX, CommandY), FText::FromString(TEXT("Commands: stat mat start/end/0 | stat obj/0")), Font, FLinearColor(0.50f, 0.58f, 0.64f, 0.95f));
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

	for (const FMaterialAccumulator& Row : GCachedDebugRows)
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
	if (!World || CVarDebug.GetValueOnGameThread() == 0 || GActorColorationActive)
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
	if (!World || CVarObjectDebug.GetValueOnGameThread() == 0 || GActorColorationActive)
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

	if (!IsProfilingViewportStatEnabled(RenderingViewportClient)
		|| IsViewportStatEnabled(RenderingViewportClient)
		|| IsObjectViewportStatEnabled(RenderingViewportClient))
	{
		return Y;
	}
	EnsureProfilingSlateOverlay(RenderingViewportClient);

	UFont* Font = GEngine->GetSmallFont();
	if (!Font)
	{
		return Y;
	}

	const FIntRect CanvasViewRect = Canvas->GetViewRect();
	const FIntPoint FallbackViewSize = Canvas->GetRenderTarget() ? Canvas->GetRenderTarget()->GetSizeXY() : FIntPoint(1280, 720);
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
	const float CommandGap = 8.0f;
	const float BottomPadding = 10.0f;
	const float ToolbarY = PanelY + PaddingX + TitleHeight + StatusHeight + CommandGap;
	const float ProfilingButtonY = FMath::Max(ViewMinY + 6.0f, PanelY - GetProfilingCommandButtonHeight() - 8.0f);
	const float PanelHeight = PaddingX + TitleHeight + StatusHeight + CommandGap + GetProfilingCommandBarTotalHeight() + BottomPadding;

	DrawStatTile(Canvas, FVector2D(PanelX, PanelY), FVector2D(PanelWidth, PanelHeight), FLinearColor(0.025f, 0.026f, 0.028f, 0.78f));

	FCanvasTextItem TextItem(FVector2D::ZeroVector, FText::GetEmpty(), Font, FLinearColor::White);
	TextItem.EnableShadow(FLinearColor::Black);
	TextItem.SetColor(FLinearColor(0.95f, 0.95f, 0.92f, 1.0f));
	TextItem.Text = FText::FromString(TEXT("OPTIMIZATION PROFILING"));
	Canvas->DrawItem(TextItem, FVector2D(PanelX + PaddingX, PanelY + 8.0f));

	TextItem.SetColor(FLinearColor(0.62f, 0.72f, 0.82f, 1.0f));
	TextItem.Text = FText::FromString(TEXT("Plugin Commands"));
	Canvas->DrawItem(TextItem, FVector2D(PanelX + PaddingX, PanelY + 27.0f));

	DrawProfilingCommandBar(Canvas, Font, PanelX, ToolbarY, PanelWidth, ProfilingButtonY);

	return static_cast<int32>(PanelY + PanelHeight + 4.0f);
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

	const bool bDrawProfilingCommands = IsProfilingViewportStatEnabled(RenderingViewportClient);
	if (bDrawProfilingCommands)
	{
		EnsureProfilingSlateOverlay(RenderingViewportClient);
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
	const float ProfilingCommandGap = bDrawProfilingCommands ? 8.0f : 0.0f;
	const float ProfilingCommandHeight = bDrawProfilingCommands ? GetProfilingCommandBarTotalHeight() : 0.0f;
	const float ProfilingButtonY = FMath::Max(ViewMinY + 6.0f, PanelY - GetProfilingCommandButtonHeight() - 8.0f);
	const int32 VisibleRows = GCachedObjectRows.Num() > 0 ? GCachedObjectRows.Num() : 1;
	const float PanelHeight = PaddingX + TitleHeight + StatusHeight + HeaderHeight + static_cast<float>(VisibleRows) * RowHeight + ProfilingCommandGap + ProfilingCommandHeight + BottomPadding;
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
		CVarObjectDebug.GetValueOnGameThread() != 0 ? TEXT("On") : TEXT("Off"));

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
		if (bDrawProfilingCommands)
		{
			DrawProfilingCommandBar(Canvas, Font, PanelX, RowY + ProfilingCommandGap, PanelWidth, ProfilingButtonY);
		}
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

	if (bDrawProfilingCommands)
	{
		DrawProfilingCommandBar(Canvas, Font, PanelX, RowY + ProfilingCommandGap, PanelWidth, ProfilingButtonY);
	}

	return static_cast<int32>(PanelY + PanelHeight + 4.0f);
}

static int32 RenderStat(UWorld* World, FViewport* Viewport, FCanvas* Canvas, int32 X, int32 Y, const FVector* ViewLocation, const FRotator* ViewRotation)
{
	if (!World || !Canvas || !GEngine)
	{
		return Y;
	}

	if (CVarDebug.GetValueOnGameThread() == 0)
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

	const bool bDrawProfilingCommands = IsProfilingViewportStatEnabled(RenderingViewportClient);
	if (bDrawProfilingCommands)
	{
		EnsureProfilingSlateOverlay(RenderingViewportClient);
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
	const float ProfilingCommandGap = bDrawProfilingCommands ? 8.0f : 0.0f;
	const float ProfilingCommandHeight = bDrawProfilingCommands ? GetProfilingCommandBarTotalHeight() : 0.0f;
	const float ProfilingButtonY = FMath::Max(ViewMinY + 6.0f, PanelY - GetProfilingCommandButtonHeight() - 8.0f);
	const int32 VisibleRows = GCachedRows.Num() > 0 ? GCachedRows.Num() : 1;
	const float PanelHeight = PaddingX + TitleHeight + StatusHeight + HeaderHeight + static_cast<float>(VisibleRows) * RowHeight + ProfilingCommandGap + ProfilingCommandHeight + BottomPadding;
	const float TableX = PanelX + PaddingX;
	const float TableY = PanelY + PaddingX + TitleHeight + StatusHeight;
	const float TableWidth = PanelWidth - PaddingX * 2.0f;

	DrawStatTile(Canvas, FVector2D(PanelX, PanelY), FVector2D(PanelWidth, PanelHeight), FLinearColor(0.025f, 0.026f, 0.028f, 0.78f));
	DrawStatTile(Canvas, FVector2D(PanelX, TableY), FVector2D(PanelWidth, HeaderHeight), FLinearColor(0.18f, 0.18f, 0.18f, 0.86f));

	const float MaterialX = TableX;
	const float MaxX = PanelX + PanelWidth - 438.0f;
	const float AvgX = PanelX + PanelWidth - 366.0f;
	const float DrawEventsX = PanelX + PanelWidth - 288.0f;
	const float CompsX = PanelX + PanelWidth - 214.0f;
	const float BlendX = PanelX + PanelWidth - 146.0f;
	const float TrisX = PanelX + PanelWidth - 82.0f;
	const int32 MaterialNameChars = FMath::Clamp(static_cast<int32>((MaxX - MaterialX - 18.0f) / 7.0f), 24, 74);

	FCanvasTextItem TextItem(FVector2D::ZeroVector, FText::GetEmpty(), Font, FLinearColor::White);
	TextItem.EnableShadow(FLinearColor::Black);

	const TCHAR* CaptureState = GCaptureActive ? TEXT("Recording") : (GCaptureFrozen ? TEXT("Captured") : TEXT("Idle"));
	const FString TitleText = TEXT("MATERIAL GPU PREVIEW");
	const FString StatusText = FString::Printf(TEXT("Insights %s %.1fs | Frames %llu | Targets %d | Debug %s"),
		CaptureState,
		GetCaptureDurationSeconds(),
		static_cast<unsigned long long>(GLastTraceFrameCount),
		GLastDebugComponentCount,
		CVarDebug.GetValueOnGameThread() != 0 ? TEXT("On") : TEXT("Off"));

	TextItem.SetColor(FLinearColor(0.95f, 0.95f, 0.92f, 1.0f));
	TextItem.Text = FText::FromString(TitleText);
	Canvas->DrawItem(TextItem, FVector2D(PanelX + PaddingX, PanelY + 8.0f));

	TextItem.SetColor(FLinearColor(0.62f, 0.72f, 0.82f, 1.0f));
	TextItem.Text = FText::FromString(StatusText);
	Canvas->DrawItem(TextItem, FVector2D(PanelX + PaddingX, PanelY + 27.0f));

	TextItem.SetColor(FLinearColor(1.0f, 0.63f, 0.18f, 1.0f));
	TextItem.Text = FText::FromString(TEXT("Material"));
	Canvas->DrawItem(TextItem, FVector2D(MaterialX, TableY + 2.0f));
	TextItem.Text = FText::FromString(TEXT("MaxMS"));
	Canvas->DrawItem(TextItem, FVector2D(MaxX, TableY + 2.0f));
	TextItem.Text = FText::FromString(TEXT("AvgMS"));
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
	if (GCachedRows.Num() == 0)
	{
		DrawStatTile(Canvas, FVector2D(PanelX, RowY), FVector2D(PanelWidth, RowHeight), FLinearColor(0.10f, 0.10f, 0.10f, 0.62f));
		TextItem.SetColor(FLinearColor::Yellow);
		TextItem.Text = FText::FromString(TEXT("No Insights material data. Use 'stat mat start', then 'stat mat end'."));
		Canvas->DrawItem(TextItem, FVector2D(MaterialX, RowY + 1.0f));
		RowY += RowHeight;
		if (bDrawProfilingCommands)
		{
			DrawProfilingCommandBar(Canvas, Font, PanelX, RowY + ProfilingCommandGap, PanelWidth, ProfilingButtonY);
		}
		return static_cast<int32>(PanelY + PanelHeight + 4.0f);
	}

	for (int32 RowIndex = 0; RowIndex < GCachedRows.Num(); ++RowIndex)
	{
		const FMaterialAccumulator& Row = GCachedRows[RowIndex];
		const float DisplayMs = GetSeverityMs(Row);
		const double DrawEventsPerFrame = static_cast<double>(Row.TraceDrawEvents) / static_cast<double>(FMath::Max<uint64>(GLastTraceFrameCount, 1));
		const FLinearColor RowColor = GetMaterialGpuPreviewColor(DisplayMs);
		const FLinearColor BandColor = (RowIndex % 2) == 0
			? FLinearColor(0.11f, 0.11f, 0.11f, 0.66f)
			: FLinearColor(0.18f, 0.18f, 0.18f, 0.66f);

		DrawStatTile(Canvas, FVector2D(PanelX, RowY), FVector2D(PanelWidth, RowHeight), BandColor);
		TextItem.SetColor(RowColor);
		TextItem.Text = FText::FromString(GetMaterialTableName(Row, MaterialNameChars));
		Canvas->DrawItem(TextItem, FVector2D(MaterialX, RowY + 1.0f));

		TextItem.Text = FText::FromString(FString::Printf(TEXT("%5.2f"), Row.MaxGpuMs));
		Canvas->DrawItem(TextItem, FVector2D(MaxX, RowY + 1.0f));
		TextItem.Text = FText::FromString(FString::Printf(TEXT("%5.2f"), Row.AvgGpuMs));
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

	if (bDrawProfilingCommands)
	{
		DrawProfilingCommandBar(Canvas, Font, PanelX, RowY + ProfilingCommandGap, PanelWidth, ProfilingButtonY);
	}

	return static_cast<int32>(PanelY + PanelHeight + 4.0f);
}
}

void FOptimizationPreviewToolsModule::StartupModule()
{
	RegisterStat();
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
		GEngine->RemoveEngineStat(OptimizationPreviewTools::ObjectEngineStatName);
		GEngine->RemoveEngineStat(OptimizationPreviewTools::ProfilingEngineStatName);
	}
}

IMPLEMENT_MODULE(FOptimizationPreviewToolsModule, OptimizationPreviewTools)

#undef LOCTEXT_NAMESPACE
