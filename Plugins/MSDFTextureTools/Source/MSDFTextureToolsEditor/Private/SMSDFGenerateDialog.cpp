#include "SMSDFGenerateDialog.h"

#include "Engine/Texture2D.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "MSDFTextureGenerator.h"
#include "SMSDFPreviewPanel.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SComboBox.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SSpinBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/Layout/SSeparator.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "SMSDFGenerateDialog"

void SMSDFGenerateDialog::Construct(const FArguments& InArgs)
{
	SourceTexture = InArgs._SourceTexture;
	Options.OutputFolder = InArgs._DefaultOutputFolder;
	Options.GenerationMode = InArgs._GenerationMode;

	const bool bIsMultiChannel =
		Options.GenerationMode == EMSDFGenerationMode::MSDF ||
		Options.GenerationMode == EMSDFGenerationMode::MTSDF;

	for (const int32 Resolution : {64, 128, 256, 512, 1024})
	{
		ResolutionItems.Add(MakeShared<FString>(LexToString(Resolution)));
	}
	EdgeColoringItems.Add(MakeShared<FString>(TEXT("Simple")));
	EdgeColoringItems.Add(MakeShared<FString>(TEXT("InkTrap")));
	EdgeColoringItems.Add(MakeShared<FString>(TEXT("Distance")));

	TSharedRef<SVerticalBox> SettingsBox = SNew(SVerticalBox);

	// AddRow: Label | Widget, with a Korean tooltip on the whole row
	auto AddRow = [&SettingsBox](const FText& Label, const TSharedRef<SWidget>& Widget, const FText& Tip)
	{
		SettingsBox->AddSlot()
		.AutoHeight()
		.Padding(0.0f, 4.0f)
		[
			SNew(SHorizontalBox)
			.ToolTipText(Tip)
			+ SHorizontalBox::Slot()
			.FillWidth(0.42f)
			.VAlign(VAlign_Center)
			[
				SNew(STextBlock).Text(Label)
			]
			+ SHorizontalBox::Slot()
			.FillWidth(0.58f)
			[
				Widget
			]
		];
	};

	AddRow(
		LOCTEXT("OutputResolution", "Output Resolution"),
		SNew(SComboBox<TSharedPtr<FString>>)
		.OptionsSource(&ResolutionItems)
		.InitiallySelectedItem(ResolutionItems[2])
		.OnGenerateWidget_Lambda([](TSharedPtr<FString> Item)
		{
			return SNew(STextBlock).Text(FText::FromString(Item.IsValid() ? *Item : FString()));
		})
		.OnSelectionChanged_Lambda([this](TSharedPtr<FString> Item, ESelectInfo::Type)
		{
			if (Item.IsValid())
			{
				Options.OutputResolution = FCString::Atoi(**Item);
			}
		})
		[
			SNew(STextBlock).Text_Lambda([this]() { return FText::AsNumber(Options.OutputResolution); })
		],
		LOCTEXT("OutputResolution_Tip",
			"SDF 텍스쳐의 출력 해상도입니다.\n"
			"긴 축을 기준으로 크기를 맞추고 원본 비율을 유지합니다.")
	);

	AddRow(
		LOCTEXT("Threshold", "Threshold"),
		SNew(SSpinBox<float>)
		.MinValue(0.0f)
		.MaxValue(1.0f)
		.Value(Options.Threshold)
		.OnValueChanged_Lambda([this](float Value) { Options.Threshold = Value; }),
		LOCTEXT("Threshold_Tip",
			"픽셀을 전경으로 분류할 알파 임계값입니다.\n"
			"값이 낮을수록 더 많은 픽셀이 전경으로 처리됩니다.\n"
			"알파 채널이 없는 텍스쳐는 자동으로 루미넌스를 사용합니다.")
	);

	AddRow(
		LOCTEXT("InvertAlpha", "Invert Alpha"),
		SNew(SCheckBox)
		.IsChecked(Options.bInvertAlpha ? ECheckBoxState::Checked : ECheckBoxState::Unchecked)
		.OnCheckStateChanged_Lambda([this](ECheckBoxState State) { Options.bInvertAlpha = State == ECheckBoxState::Checked; }),
		LOCTEXT("InvertAlpha_Tip",
			"알파 채널 값을 반전시킵니다.\n"
			"검은 배경에 흰색 오브젝트가 있는 텍스쳐에 사용하세요.")
	);

	AddRow(
		LOCTEXT("Padding", "Padding"),
		SNew(SSpinBox<int32>)
		.MinValue(0)
		.MaxValue(64)
		.Value(Options.Padding)
		.OnValueChanged_Lambda([this](int32 Value) { Options.Padding = Value; }),
		LOCTEXT("Padding_Tip",
			"SDF 생성 시 이미지 가장자리에 추가할 여백 픽셀 수입니다.\n"
			"경계 부근의 SDF 값이 잘리는 것을 방지합니다.")
	);

	AddRow(
		LOCTEXT("PxRange", "PxRange"),
		SNew(SSpinBox<float>)
		.MinValue(1.0f)
		.MaxValue(64.0f)
		.Value(Options.PxRange)
		.OnValueChanged_Lambda([this](float Value) { Options.PxRange = Value; }),
		LOCTEXT("PxRange_Tip",
			"SDF 그래디언트의 최대 픽셀 거리 범위입니다.\n"
			"값이 클수록 더 넓은 그림자·글로우 효과를 지원하지만,\n"
			"해상도 대비 너무 크면 정밀도가 떨어질 수 있습니다.")
	);

	if (bIsMultiChannel)
	{
		AddRow(
			LOCTEXT("EdgeColoring", "Edge Coloring Mode"),
			SNew(SComboBox<TSharedPtr<FString>>)
			.OptionsSource(&EdgeColoringItems)
			.InitiallySelectedItem(EdgeColoringItems[1])
			.OnGenerateWidget_Lambda([](TSharedPtr<FString> Item)
			{
				return SNew(STextBlock).Text(FText::FromString(Item.IsValid() ? *Item : FString()));
			})
			.OnSelectionChanged_Lambda([this](TSharedPtr<FString> Item, ESelectInfo::Type)
			{
				if (Item.IsValid())
				{
					SetEdgeColoringFromText(*Item);
				}
			})
			[
				SNew(STextBlock).Text_Lambda([this]() { return FText::FromString(GetEdgeColoringText()); })
			],
			LOCTEXT("EdgeColoring_Tip",
				"MSDF/MTSDF 생성 시 엣지에 색상을 배분하는 방식입니다.\n"
				"  Simple   : 단순 각도 기반 배분\n"
				"  InkTrap  : 잉크 트랩 최적화 (권장)\n"
				"  Distance : 거리 기반 배분")
		);
	}

	AddRow(
		LOCTEXT("OutputFolder", "Output Folder"),
		SNew(SEditableTextBox)
		.Text(FText::FromString(Options.OutputFolder))
		.OnTextCommitted_Lambda([this](const FText& Text, ETextCommit::Type) { Options.OutputFolder = Text.ToString(); }),
		LOCTEXT("OutputFolder_Tip",
			"생성된 텍스쳐 에셋이 저장될 콘텐츠 브라우저 경로입니다.\n"
			"/Game/ 로 시작하는 경로를 입력하세요.")
	);

	ChildSlot
	[
		SNew(SBorder)
		.Padding(12.0f)
		[
			SNew(SVerticalBox)

			// Source summary
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 0.0f, 0.0f, 8.0f)
			[
				SNew(STextBlock)
				.Text(this, &SMSDFGenerateDialog::GetSourceSummaryText)
			]

			// Settings
			+ SVerticalBox::Slot()
			.AutoHeight()
			[
				SettingsBox
			]

			// Generate button
			+ SVerticalBox::Slot()
			.AutoHeight()
			.HAlign(HAlign_Right)
			.Padding(0.0f, 8.0f, 0.0f, 0.0f)
			[
				SNew(SButton)
				.Text(LOCTEXT("Generate", "Generate"))
				.OnClicked(this, &SMSDFGenerateDialog::OnGenerateClicked)
			]

			// Status message
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 6.0f)
			[
				SAssignNew(StatusTextBlock, STextBlock)
				.AutoWrapText(true)
			]

			// Separator
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 4.0f)
			[
				SNew(SSeparator)
			]

			// Side-by-side preview: left = raw texture, right = MID material preview
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0.0f, 4.0f, 0.0f, 0.0f)
			[
				SNew(SHorizontalBox)

				// ── Left: raw generated texture ──────────────────────────
				+ SHorizontalBox::Slot()
				.FillWidth(1.0f)
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(0.0f, 0.0f, 0.0f, 4.0f)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("RawTextureLabel", "생성된 텍스쳐"))
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						SNew(SBox)
						.HeightOverride(280.0f)
						[
							SNew(SScaleBox)
							.Stretch(EStretch::ScaleToFit)
							.HAlign(HAlign_Center)
							.VAlign(VAlign_Center)
							[
								SAssignNew(RawTextureImage, SImage)
							]
						]
					]
				]

				// ── Right: MID material preview (zoom/pan) ────────────────
				+ SHorizontalBox::Slot()
				.FillWidth(1.0f)
				.Padding(8.0f, 0.0f, 0.0f, 0.0f)
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot()
					.AutoHeight()
					.Padding(0.0f, 0.0f, 0.0f, 4.0f)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("PreviewLabel", "MID 미리보기  (휠: 확대/축소 · 휠클릭+드래그: 이동)"))
					]
					+ SVerticalBox::Slot()
					.AutoHeight()
					[
						SNew(SBox)
						.HeightOverride(280.0f)
						[
							SAssignNew(PreviewPanel, SMSDFPreviewPanel)
						]
					]
				]
			]
		]
	];
}

SMSDFGenerateDialog::~SMSDFGenerateDialog()
{
	if (IsValid(PreviewMID))
	{
		PreviewMID->RemoveFromRoot();
		PreviewMID = nullptr;
	}
}

FReply SMSDFGenerateDialog::OnGenerateClicked()
{
	if (!SourceTexture.IsValid())
	{
		if (StatusTextBlock.IsValid())
		{
			StatusTextBlock->SetText(LOCTEXT("NoSourceTexture", "소스 텍스쳐가 선택되지 않았습니다."));
		}
		return FReply::Handled();
	}

	FExternalMSDFGenBackend Backend;
	FMSDFTextureGenerationResult Result = Backend.Generate(SourceTexture.Get(), Options);

	if (StatusTextBlock.IsValid())
	{
		StatusTextBlock->SetText(Result.Message);
	}

	if (Result.bSucceeded && IsValid(Result.Texture))
	{
		UpdatePreview(Result.Texture, Options);
	}

	return FReply::Handled();
}

void SMSDFGenerateDialog::UpdatePreview(UTexture2D* GeneratedTexture, const FMSDFTextureGenerationOptions& InOptions)
{
	if (!IsValid(GeneratedTexture))
	{
		return;
	}

	const FVector2D NaturalSize(
		static_cast<float>(FMath::Max(1, GeneratedTexture->GetSizeX())),
		static_cast<float>(FMath::Max(1, GeneratedTexture->GetSizeY()))
	);

	// ── Left panel: raw texture ───────────────────────────────────────────
	RawTextureBrush = FSlateBrush();
	RawTextureBrush.DrawAs = ESlateBrushDrawType::Image;
	RawTextureBrush.ImageSize = NaturalSize;
	RawTextureBrush.Tiling = ESlateBrushTileType::NoTile;
	RawTextureBrush.ImageType = ESlateBrushImageType::FullColor;
	RawTextureBrush.SetResourceObject(GeneratedTexture);

	if (RawTextureImage.IsValid())
	{
		RawTextureImage->SetImage(&RawTextureBrush);
	}

	// ── Right panel: MID material preview ────────────────────────────────
	if (!IsValid(PreviewMID))
	{
		UMaterial* BaseMaterial = LoadObject<UMaterial>(nullptr,
			TEXT("/MSDFTextureTools/Material/Mat_PreViewSDF.Mat_PreViewSDF"));
		if (!IsValid(BaseMaterial))
		{
			if (StatusTextBlock.IsValid())
			{
				StatusTextBlock->SetText(FText::Format(
					LOCTEXT("PreviewMatMissing", "{0}\n(미리보기 메터리얼을 찾을 수 없습니다: /MSDFTextureTools/Material/Mat_PreViewSDF)"),
					StatusTextBlock->GetText()));
			}
			return;
		}
		PreviewMID = UMaterialInstanceDynamic::Create(BaseMaterial, GetTransientPackage());
		PreviewMID->AddToRoot();
	}

	PreviewMID->SetTextureParameterValue(TEXT("Tex"), GeneratedTexture);
	PreviewMID->SetScalarParameterValue(TEXT("pxRange"), InOptions.PxRange);
	PreviewMID->SetScalarParameterValue(TEXT("TexelSize"), 1.0f / NaturalSize.X);

	PreviewBrush = FSlateBrush();
	PreviewBrush.DrawAs = ESlateBrushDrawType::Image;
	PreviewBrush.ImageSize = NaturalSize;
	PreviewBrush.Tiling = ESlateBrushTileType::NoTile;
	PreviewBrush.ImageType = ESlateBrushImageType::FullColor;
	PreviewBrush.SetResourceObject(PreviewMID);

	if (PreviewPanel.IsValid())
	{
		PreviewPanel->SetContent(&PreviewBrush, NaturalSize);
	}
}

FText SMSDFGenerateDialog::GetSourceSummaryText() const
{
	if (!SourceTexture.IsValid())
	{
		return LOCTEXT("NoSource", "No Texture2D selected.");
	}

	return FText::Format(
		LOCTEXT("SourceSummary", "Source: {0} ({1} x {2})"),
		FText::FromString(SourceTexture->GetName()),
		FText::AsNumber(SourceTexture->Source.GetSizeX()),
		FText::AsNumber(SourceTexture->Source.GetSizeY()));
}

FString SMSDFGenerateDialog::GetEdgeColoringText() const
{
	switch (Options.EdgeColoringMode)
	{
	case EMSDFEdgeColoringMode::Simple:   return TEXT("Simple");
	case EMSDFEdgeColoringMode::Distance: return TEXT("Distance");
	case EMSDFEdgeColoringMode::InkTrap:
	default:                              return TEXT("InkTrap");
	}
}

void SMSDFGenerateDialog::SetEdgeColoringFromText(const FString& Value)
{
	if (Value == TEXT("Simple"))
	{
		Options.EdgeColoringMode = EMSDFEdgeColoringMode::Simple;
	}
	else if (Value == TEXT("Distance"))
	{
		Options.EdgeColoringMode = EMSDFEdgeColoringMode::Distance;
	}
	else
	{
		Options.EdgeColoringMode = EMSDFEdgeColoringMode::InkTrap;
	}
}

#undef LOCTEXT_NAMESPACE
