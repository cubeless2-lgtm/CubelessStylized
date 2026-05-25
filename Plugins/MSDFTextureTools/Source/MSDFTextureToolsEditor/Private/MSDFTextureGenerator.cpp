#include "MSDFTextureGenerator.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetToolsModule.h"
#include "Editor.h"
#include "Engine/Texture2D.h"
#include "IImageWrapper.h"
#include "IImageWrapperModule.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "ObjectTools.h"
#include "TextureResource.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"

#define LOCTEXT_NAMESPACE "MSDFTextureGenerator"

namespace
{
	FString Quote(const FString& Value)
	{
		return FString::Printf(TEXT("\"%s\""), *Value);
	}

	FString EdgeColoringArgument(EMSDFEdgeColoringMode Mode)
	{
		switch (Mode)
		{
		case EMSDFEdgeColoringMode::Simple:
			return TEXT("simple");
		case EMSDFEdgeColoringMode::Distance:
			return TEXT("distance");
		case EMSDFEdgeColoringMode::InkTrap:
		default:
			return TEXT("inktrap");
		}
	}

	FString MakeTempDirectory(UTexture2D* SourceTexture)
	{
		const FString Root = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("MSDFTextureTools"), SourceTexture->GetName());
		IFileManager::Get().MakeDirectory(*Root, true);
		return Root;
	}

	FString SanitizeLongPackagePath(const FString& InputPath)
	{
		FString Path = InputPath.IsEmpty() ? TEXT("/Game/MSDF") : InputPath;
		if (!Path.StartsWith(TEXT("/Game")))
		{
			Path = TEXT("/Game/MSDF");
		}
		return Path;
	}

	bool PopEdge(TMap<FIntPoint, TArray<FIntPoint>>& Edges, FIntPoint& OutStart, FIntPoint& OutEnd)
	{
		for (TPair<FIntPoint, TArray<FIntPoint>>& Pair : Edges)
		{
			if (!Pair.Value.IsEmpty())
			{
				OutStart = Pair.Key;
				OutEnd = Pair.Value.Pop(EAllowShrinking::No);
				if (Pair.Value.IsEmpty())
				{
					Edges.Remove(Pair.Key);
				}
				return true;
			}
		}
		return false;
	}
}

FMSDFTextureGenerationResult FExternalMSDFGenBackend::Generate(UTexture2D* SourceTexture, const FMSDFTextureGenerationOptions& Options)
{
	FMSDFTextureGenerationResult Result;
	if (!SourceTexture)
	{
		Result.Message = LOCTEXT("NoTexture", "No Texture2D asset was provided.");
		return Result;
	}

	FText Error;
	FMaskData MaskData;
	if (!ExtractMask(SourceTexture, Options, MaskData, Error))
	{
		Result.Message = Error;
		return Result;
	}

	if (!MaskData.bHasAlpha)
	{
		Result.Message = LOCTEXT("NoForeground", "마스크에 전경 픽셀이 없습니다. Threshold를 낮추거나 Invert Alpha를 확인하세요. 알파 채널이 없는 텍스쳐는 루미넌스를 자동으로 사용합니다.");
		return Result;
	}

	FString ModeSuffix;
	switch (Options.GenerationMode)
	{
	case EMSDFGenerationMode::SDF:
		ModeSuffix = TEXT("_SDF");
		break;
	case EMSDFGenerationMode::MSDF:
		ModeSuffix = TEXT("_MSDF");
		break;
	case EMSDFGenerationMode::MTSDF:
	default:
		ModeSuffix = TEXT("_MTSDF");
		break;
	}

	// Compute output dimensions: scale longest side to OutputResolution, preserve aspect ratio.
	// Path coordinates are written in output-pixel space so msdfgen maps them 1:1 without autoframe.
	const int32 Padding = FMath::Max(0, Options.Padding);
	const int32 SrcMax = FMath::Max(MaskData.Width, MaskData.Height);
	const float Scale = (SrcMax > 0) ? (float)FMath::Clamp(Options.OutputResolution, 1, 8192) / SrcMax : 1.0f;
	const int32 ScaledPad = FMath::RoundToInt(Padding * Scale);
	const int32 OutW = FMath::Max(1, FMath::RoundToInt(MaskData.Width * Scale)) + 2 * ScaledPad;
	const int32 OutH = FMath::Max(1, FMath::RoundToInt(MaskData.Height * Scale)) + 2 * ScaledPad;

	const FString TempDir = MakeTempDirectory(SourceTexture);
	Result.DebugDirectory = TempDir;
	const FString SvgPath = FPaths::Combine(TempDir, SourceTexture->GetName() + ModeSuffix + TEXT("_Source.svg"));
	const FString PngPath = FPaths::Combine(TempDir, SourceTexture->GetName() + ModeSuffix + TEXT(".png"));

	if (!WriteSvgFromMask(MaskData, Options, SvgPath, OutW, OutH, Scale, Error))
	{
		Result.Message = Error;
		return Result;
	}

	if (!RunMSDFGen(SvgPath, PngPath, Options, OutW, OutH, Error))
	{
		Result.Message = Error;
		return Result;
	}

	UTexture2D* CreatedTexture = CreateTextureAssetFromPng(PngPath, SourceTexture, Options, Error);
	if (!CreatedTexture)
	{
		Result.Message = Error;
		return Result;
	}

	IFileManager::Get().Delete(*SvgPath);
	IFileManager::Get().Delete(*PngPath);

	FText SuccessMsg;
	switch (Options.GenerationMode)
	{
	case EMSDFGenerationMode::SDF:
		SuccessMsg = LOCTEXT("SDF_Generated", "SDF 텍스쳐가 생성되었습니다.");
		break;
	case EMSDFGenerationMode::MSDF:
		SuccessMsg = LOCTEXT("MSDF_Generated", "MSDF 텍스쳐가 생성되었습니다.");
		break;
	case EMSDFGenerationMode::MTSDF:
	default:
		SuccessMsg = LOCTEXT("MTSDF_Generated", "MTSDF 텍스쳐가 생성되었습니다.");
		break;
	}

	Result.bSucceeded = true;
	Result.Texture = CreatedTexture;
	Result.Message = MaskData.bLooksComplex
		? FText::Format(LOCTEXT("GeneratedWithComplexWarning", "{0}\n\n경고: 소스 이미지가 복잡한 컬러/노이즈 이미지처럼 보입니다. SDF 계열 변환은 깨끗한 알파 실루엣, 아이콘, 로고, UI 마스크에 가장 잘 동작합니다."), SuccessMsg)
		: SuccessMsg;

	if (GEditor)
	{
		TArray<UObject*> ObjectsToSync;
		ObjectsToSync.Add(CreatedTexture);
		GEditor->SyncBrowserToObjects(ObjectsToSync);
	}

	return Result;
}

bool FExternalMSDFGenBackend::ExtractMask(UTexture2D* SourceTexture, const FMSDFTextureGenerationOptions& Options, FMaskData& OutMask, FText& OutError)
{
	if (!SourceTexture || !SourceTexture->Source.IsValid())
	{
		OutError = LOCTEXT("InvalidSource", "The selected texture has no valid source pixels. Reimport the texture with source data available, then try again.");
		return false;
	}

	const int32 Width = SourceTexture->Source.GetSizeX();
	const int32 Height = SourceTexture->Source.GetSizeY();
	if (Width <= 0 || Height <= 0)
	{
		OutError = LOCTEXT("InvalidSize", "The selected texture has an invalid source size.");
		return false;
	}

	TArray64<uint8> SourceBytes;
	if (!SourceTexture->Source.GetMipData(SourceBytes, 0))
	{
		OutError = LOCTEXT("CannotReadMip", "Could not read source pixels from the selected Texture2D.");
		return false;
	}

	OutMask.Width = Width;
	OutMask.Height = Height;
	OutMask.Mask.SetNumZeroed(Width * Height);

	const ETextureSourceFormat Format = SourceTexture->Source.GetFormat();
	const uint8 ThresholdByte = static_cast<uint8>(FMath::Clamp(Options.Threshold, 0.0f, 1.0f) * 255.0f);
	TSet<uint32> ForegroundColors;

	for (int32 Y = 0; Y < Height; ++Y)
	{
		for (int32 X = 0; X < Width; ++X)
		{
			const int64 PixelIndex = static_cast<int64>(Y) * Width + X;
			uint8 Alpha = 255;
			uint32 ColorKey = 0;
			bool bPixelHasAlpha = false;

			switch (Format)
			{
			case TSF_BGRA8:
			{
				const int64 Offset = PixelIndex * 4;
				if (SourceBytes.IsValidIndex(Offset + 3))
				{
					const uint8 B = SourceBytes[Offset + 0];
					const uint8 G = SourceBytes[Offset + 1];
					const uint8 R = SourceBytes[Offset + 2];
					Alpha = SourceBytes[Offset + 3];
					ColorKey = (static_cast<uint32>(R) << 16) | (static_cast<uint32>(G) << 8) | B;
					bPixelHasAlpha = true;
				}
				break;
			}
			case TSF_G8:
			{
				if (SourceBytes.IsValidIndex(PixelIndex))
				{
					Alpha = SourceBytes[PixelIndex];
					ColorKey = Alpha;
					bPixelHasAlpha = true;
				}
				break;
			}
			case TSF_G16:
			{
				const int64 Offset = PixelIndex * 2;
				if (SourceBytes.IsValidIndex(Offset + 1))
				{
					Alpha = SourceBytes[Offset + 1];
					ColorKey = Alpha;
					bPixelHasAlpha = true;
				}
				break;
			}
			case TSF_RGBA16:
			{
				const int64 Offset = PixelIndex * 8;
				if (SourceBytes.IsValidIndex(Offset + 7))
				{
					Alpha = SourceBytes[Offset + 7];
					const uint8 R = SourceBytes[Offset + 1];
					const uint8 G = SourceBytes[Offset + 3];
					const uint8 B = SourceBytes[Offset + 5];
					ColorKey = (static_cast<uint32>(R) << 16) | (static_cast<uint32>(G) << 8) | B;
					bPixelHasAlpha = true;
				}
				break;
			}
			default:
				OutError = FText::Format(LOCTEXT("UnsupportedFormat", "Unsupported texture source format: {0}. Use BGRA8, G8, G16, or RGBA16 source textures."), FText::AsNumber(static_cast<int32>(Format)));
				return false;
			}

			if (Options.bInvertAlpha)
			{
				Alpha = 255 - Alpha;
			}

			const bool bForeground = Alpha >= ThresholdByte;
			OutMask.Mask[PixelIndex] = bForeground ? 1 : 0;
			if (bForeground)
			{
				ForegroundColors.Add(ColorKey);
			}
		}
	}

	// bHasAlpha: repurposed as "at least one foreground pixel exists"
	OutMask.bHasAlpha = ForegroundColors.Num() > 0;

	// Luminance fallback: if alpha produced no foreground pixels and format has RGB channels,
	// retry using luminance so that textures without a meaningful alpha channel still convert.
	if (!OutMask.bHasAlpha && (Format == TSF_BGRA8 || Format == TSF_RGBA16))
	{
		ForegroundColors.Reset();
		for (int32 Y = 0; Y < Height; ++Y)
		{
			for (int32 X = 0; X < Width; ++X)
			{
				const int64 PixelIndex = static_cast<int64>(Y) * Width + X;
				uint8 R = 0, G = 0, B = 0;
				if (Format == TSF_BGRA8)
				{
					const int64 Offset = PixelIndex * 4;
					if (SourceBytes.IsValidIndex(Offset + 2))
					{
						B = SourceBytes[Offset + 0];
						G = SourceBytes[Offset + 1];
						R = SourceBytes[Offset + 2];
					}
				}
				else
				{
					const int64 Offset = PixelIndex * 8;
					if (SourceBytes.IsValidIndex(Offset + 5))
					{
						R = SourceBytes[Offset + 1];
						G = SourceBytes[Offset + 3];
						B = SourceBytes[Offset + 5];
					}
				}
				uint8 Lum = static_cast<uint8>(FMath::Clamp((R * 299 + G * 587 + B * 114) / 1000, 0, 255));
				if (Options.bInvertAlpha) Lum = 255 - Lum;
				const bool bFg = Lum >= ThresholdByte;
				OutMask.Mask[PixelIndex] = bFg ? 1 : 0;
				if (bFg)
				{
					OutMask.bHasAlpha = true;
					ForegroundColors.Add(static_cast<uint32>(R) << 16 | static_cast<uint32>(G) << 8 | B);
				}
			}
		}
	}

	OutMask.bLooksComplex = ForegroundColors.Num() > 64 || (Width * Height > 0 && ForegroundColors.Num() > FMath::Max(16, (Width * Height) / 64));
	return true;
}

bool FExternalMSDFGenBackend::WriteSvgFromMask(const FMaskData& MaskData, const FMSDFTextureGenerationOptions& Options, const FString& SvgPath, int32 OutW, int32 OutH, float Scale, FText& OutError)
{
	TMap<FIntPoint, TArray<FIntPoint>> Edges;
	auto IsForeground = [&MaskData](int32 X, int32 Y)
	{
		return X >= 0 && X < MaskData.Width && Y >= 0 && Y < MaskData.Height && MaskData.Mask[Y * MaskData.Width + X] != 0;
	};
	auto AddEdge = [&Edges](const FIntPoint& A, const FIntPoint& B)
	{
		Edges.FindOrAdd(A).Add(B);
	};

	for (int32 Y = 0; Y < MaskData.Height; ++Y)
	{
		for (int32 X = 0; X < MaskData.Width; ++X)
		{
			if (!IsForeground(X, Y))
			{
				continue;
			}

			if (!IsForeground(X, Y - 1))
			{
				AddEdge(FIntPoint(X, Y), FIntPoint(X + 1, Y));
			}
			if (!IsForeground(X + 1, Y))
			{
				AddEdge(FIntPoint(X + 1, Y), FIntPoint(X + 1, Y + 1));
			}
			if (!IsForeground(X, Y + 1))
			{
				AddEdge(FIntPoint(X + 1, Y + 1), FIntPoint(X, Y + 1));
			}
			if (!IsForeground(X - 1, Y))
			{
				AddEdge(FIntPoint(X, Y + 1), FIntPoint(X, Y));
			}
		}
	}

	if (Edges.IsEmpty())
	{
		OutError = LOCTEXT("EmptyMask", "The threshold produced an empty mask. Lower the threshold or disable Invert Alpha.");
		return false;
	}

	// Collect all contours as vertex lists before building SVG paths
	TArray<TArray<FIntPoint>> Contours;
	{
		FIntPoint Start;
		FIntPoint Current;
		while (PopEdge(Edges, Start, Current))
		{
			TArray<FIntPoint> Contour;
			Contour.Add(Start);
			if (Current != Start)
			{
				Contour.Add(Current);
			}

			const FIntPoint LoopStart = Start;
			int32 Guard = 0;
			while (Current != LoopStart && Guard++ < MaskData.Width * MaskData.Height * 8)
			{
				TArray<FIntPoint>* Nexts = Edges.Find(Current);
				if (!Nexts || Nexts->IsEmpty())
				{
					break;
				}
				const FIntPoint Next = Nexts->Pop(EAllowShrinking::No);
				if (Nexts->IsEmpty())
				{
					Edges.Remove(Current);
				}
				Current = Next;
				if (Current != LoopStart)
				{
					Contour.Add(Current);
				}
			}

			if (Contour.Num() >= 3)
			{
				Contours.Add(MoveTemp(Contour));
			}
		}
	}

	// Simplify contours: remove collinear interior vertices so that a long run of
	// horizontal/vertical pixel-boundary edges becomes a single line segment.
	// Before: O(perimeter-in-pixels) vertices  →  After: O(corners) vertices.
	// This gives msdfgen clean rectilinear segments with clear 90° corners, which
	// is required for proper R/G/B edge-color assignment in MSDF/MTSDF output.
	for (TArray<FIntPoint>& Contour : Contours)
	{
		TArray<FIntPoint> Simplified;
		Simplified.Reserve(Contour.Num());
		const int32 N = Contour.Num();
		for (int32 i = 0; i < N; ++i)
		{
			const FIntPoint DirIn  = Contour[i]              - Contour[(i + N - 1) % N];
			const FIntPoint DirOut = Contour[(i + 1) % N]   - Contour[i];
			if (DirIn != DirOut)
			{
				Simplified.Add(Contour[i]);
			}
		}
		if (Simplified.Num() >= 3)
		{
			Contour = MoveTemp(Simplified);
		}
	}

	// All coordinates are written in output-pixel space (scaled + padding offset) so that
	// msdfgen renders them 1:1 without -autoframe, preserving the source texture's layout.
	const float ScaledPad = FMath::Max(0, Options.Padding) * Scale;
	FString PathData;
	for (const TArray<FIntPoint>& Contour : Contours)
	{
		const int32 N = Contour.Num();

		PathData += FString::Printf(TEXT("M%.3f %.3f "),
			Contour[0].X * Scale + ScaledPad,
			Contour[0].Y * Scale + ScaledPad);

		for (int32 i = 1; i < N; ++i)
		{
			PathData += FString::Printf(TEXT("L%.3f %.3f "),
				Contour[i].X * Scale + ScaledPad,
				Contour[i].Y * Scale + ScaledPad);
		}

		PathData += TEXT("Z ");
	}

	const FString Svg = FString::Printf(
		TEXT("<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 %d %d\"><path fill=\"black\" d=\"%s\"/></svg>"),
		OutW, OutH, *PathData);

	if (!FFileHelper::SaveStringToFile(Svg, *SvgPath))
	{
		OutError = FText::Format(LOCTEXT("SaveSvgFailed", "Could not write temporary SVG file: {0}"), FText::FromString(SvgPath));
		return false;
	}

	return true;
}

bool FExternalMSDFGenBackend::RunMSDFGen(const FString& SvgPath, const FString& PngPath, const FMSDFTextureGenerationOptions& Options, int32 OutW, int32 OutH, FText& OutError)
{
	const FString ExePath = GetMSDFGenExecutablePath();
	if (!FPaths::FileExists(ExePath))
	{
		OutError = FText::Format(
			LOCTEXT("MissingMSDFGen", "msdfgen executable was not found at:\n{0}\n\nBuild or download msdfgen and place msdfgen.exe in the plugin ThirdParty/msdfgen/Win64 folder. The mtsdf mode requires msdfgen 1.10 or later."),
			FText::FromString(ExePath));
		return false;
	}

	const float PxRange = FMath::Max(Options.PxRange, 0.01f);

	FString Args;
	switch (Options.GenerationMode)
	{
	case EMSDFGenerationMode::SDF:
		Args = FString::Printf(
			TEXT("sdf -svg %s -o %s -size %d %d -pxrange %.3f"),
			*Quote(SvgPath), *Quote(PngPath), OutW, OutH, PxRange);
		break;
	case EMSDFGenerationMode::MSDF:
		Args = FString::Printf(
			TEXT("msdf -svg %s -o %s -size %d %d -pxrange %.3f -coloringstrategy %s"),
			*Quote(SvgPath), *Quote(PngPath), OutW, OutH, PxRange,
			*EdgeColoringArgument(Options.EdgeColoringMode));
		break;
	case EMSDFGenerationMode::MTSDF:
	default:
		Args = FString::Printf(
			TEXT("mtsdf -svg %s -o %s -size %d %d -pxrange %.3f -coloringstrategy %s"),
			*Quote(SvgPath), *Quote(PngPath), OutW, OutH, PxRange,
			*EdgeColoringArgument(Options.EdgeColoringMode));
		break;
	}

	int32 ReturnCode = 0;
	FString StdOut;
	FString StdErr;
	if (!FPlatformProcess::ExecProcess(*ExePath, *Args, &ReturnCode, &StdOut, &StdErr) || ReturnCode != 0)
	{
		OutError = FText::Format(
			LOCTEXT("MSDFGenFailed", "msdfgen failed with exit code {0}.\n\nOutput:\n{1}\n\nErrors:\n{2}"),
			FText::AsNumber(ReturnCode),
			FText::FromString(StdOut),
			FText::FromString(StdErr));
		return false;
	}

	if (!FPaths::FileExists(PngPath))
	{
		OutError = LOCTEXT("MSDFPngMissing", "msdfgen completed, but did not create an output PNG.");
		return false;
	}

	return true;
}

UTexture2D* FExternalMSDFGenBackend::CreateTextureAssetFromPng(const FString& PngPath, UTexture2D* SourceTexture, const FMSDFTextureGenerationOptions& Options, FText& OutError)
{
	TArray<uint8> CompressedPng;
	if (!FFileHelper::LoadFileToArray(CompressedPng, *PngPath))
	{
		OutError = FText::Format(LOCTEXT("LoadPngFailed", "Could not read generated PNG: {0}"), FText::FromString(PngPath));
		return nullptr;
	}

	IImageWrapperModule& ImageWrapperModule = FModuleManager::LoadModuleChecked<IImageWrapperModule>(TEXT("ImageWrapper"));
	const TSharedPtr<IImageWrapper> PngWrapper = ImageWrapperModule.CreateImageWrapper(EImageFormat::PNG);
	if (!PngWrapper.IsValid() || !PngWrapper->SetCompressed(CompressedPng.GetData(), CompressedPng.Num()))
	{
		OutError = LOCTEXT("DecodePngFailed", "Could not decode the generated MSDF PNG.");
		return nullptr;
	}

	TArray64<uint8> RawRGBA;
	if (!PngWrapper->GetRaw(ERGBFormat::RGBA, 8, RawRGBA))
	{
		OutError = LOCTEXT("DecodeRawFailed", "Could not decode PNG pixels as 8-bit RGBA.");
		return nullptr;
	}

	const int32 Width = PngWrapper->GetWidth();
	const int32 Height = PngWrapper->GetHeight();
	TArray<uint8> RawBGRA;
	RawBGRA.SetNumUninitialized(Width * Height * 4);
	for (int32 Index = 0; Index < Width * Height; ++Index)
	{
		RawBGRA[Index * 4 + 0] = RawRGBA[Index * 4 + 2];
		RawBGRA[Index * 4 + 1] = RawRGBA[Index * 4 + 1];
		RawBGRA[Index * 4 + 2] = RawRGBA[Index * 4 + 0];
		RawBGRA[Index * 4 + 3] = RawRGBA[Index * 4 + 3];
	}

	FString AssetSuffix;
	switch (Options.GenerationMode)
	{
	case EMSDFGenerationMode::SDF:
		AssetSuffix = TEXT("_SDF");
		break;
	case EMSDFGenerationMode::MSDF:
		AssetSuffix = TEXT("_MSDF");
		break;
	case EMSDFGenerationMode::MTSDF:
	default:
		AssetSuffix = TEXT("_MTSDF");
		break;
	}

	const FString OutputFolder = SanitizeLongPackagePath(Options.OutputFolder);
	const FString BaseAssetName = SourceTexture->GetName() + AssetSuffix;
	FString PackageName;
	FString AssetName;
	FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools"));
	AssetToolsModule.Get().CreateUniqueAssetName(OutputFolder / BaseAssetName, TEXT(""), PackageName, AssetName);

	UPackage* Package = CreatePackage(*PackageName);
	UTexture2D* Texture = NewObject<UTexture2D>(Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
	Texture->Source.Init(Width, Height, 1, 1, TSF_BGRA8, RawBGRA.GetData());
	Texture->SRGB = false;
	Texture->CompressionSettings = TC_VectorDisplacementmap;
	Texture->MipGenSettings = TMGS_NoMipmaps;
	Texture->LODGroup = TEXTUREGROUP_UI;
	Texture->NeverStream = true;
	Texture->UpdateResource();
	Texture->PostEditChange();
	Texture->MarkPackageDirty();

	FAssetRegistryModule::AssetCreated(Texture);

	const FString PackageFilename = FPackageName::LongPackageNameToFilename(PackageName, FPackageName::GetAssetPackageExtension());
	FSavePackageArgs SaveArgs;
	SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
	SaveArgs.SaveFlags = SAVE_NoError;
	if (!UPackage::SavePackage(Package, Texture, *PackageFilename, SaveArgs))
	{
		OutError = FText::Format(LOCTEXT("SaveAssetFailed", "MSDF texture was created but could not be saved: {0}"), FText::FromString(PackageName));
		return nullptr;
	}

	return Texture;
}

FString FExternalMSDFGenBackend::GetMSDFGenExecutablePath()
{
	const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("MSDFTextureTools"));
	const FString BaseDir = Plugin.IsValid() ? Plugin->GetBaseDir() : FPaths::ProjectPluginsDir() / TEXT("MSDFTextureTools");
#if PLATFORM_WINDOWS
	return FPaths::Combine(BaseDir, TEXT("ThirdParty/msdfgen/Win64/msdfgen.exe"));
#else
	return FPaths::Combine(BaseDir, TEXT("ThirdParty/msdfgen/msdfgen"));
#endif
}

#undef LOCTEXT_NAMESPACE
