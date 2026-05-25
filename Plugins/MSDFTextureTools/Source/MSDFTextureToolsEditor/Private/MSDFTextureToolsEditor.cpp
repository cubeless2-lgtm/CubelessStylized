#include "MSDFTextureToolsEditor.h"

#include "Brushes/SlateImageBrush.h"
#include "ContentBrowserMenuContexts.h"
#include "Editor.h"
#include "Framework/Application/SlateApplication.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/MessageDialog.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "SMSDFGenerateDialog.h"
#include "Styling/SlateStyle.h"
#include "Styling/SlateStyleRegistry.h"
#include "ToolMenu.h"
#include "ToolMenuSection.h"
#include "ToolMenus.h"
#include "Engine/Texture2D.h"

#define LOCTEXT_NAMESPACE "FMSDFTextureToolsEditorModule"

void FMSDFTextureToolsEditorModule::StartupModule()
{
	RegisterStyleSet();

	if (UToolMenus::IsToolMenuUIEnabled())
	{
		UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FMSDFTextureToolsEditorModule::RegisterMenus));
	}
}

void FMSDFTextureToolsEditorModule::ShutdownModule()
{
	UnregisterMenus();
	UnregisterStyleSet();
}

void FMSDFTextureToolsEditorModule::RegisterStyleSet()
{
	StyleSet = MakeShared<FSlateStyleSet>(TEXT("MSDFTextureToolsStyle"));

	const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("MSDFTextureTools"));
	const FString ResourcesDir = Plugin.IsValid()
		? FPaths::Combine(Plugin->GetBaseDir(), TEXT("Resources"))
		: FPaths::Combine(FPaths::ProjectPluginsDir(), TEXT("MSDFTextureTools"), TEXT("Resources"));

	StyleSet->Set(
		TEXT("MSDFTextureTools.MenuIcon"),
		new FSlateImageBrush(FPaths::Combine(ResourcesDir, TEXT("Icon128.png")), FVector2D(16.0f, 16.0f))
	);

	FSlateStyleRegistry::RegisterSlateStyle(*StyleSet);
}

void FMSDFTextureToolsEditorModule::UnregisterStyleSet()
{
	if (StyleSet.IsValid())
	{
		FSlateStyleRegistry::UnRegisterSlateStyle(*StyleSet);
		StyleSet.Reset();
	}
}

void FMSDFTextureToolsEditorModule::RegisterMenus()
{
	FToolMenuOwnerScoped OwnerScoped(this);
	UToolMenu* Menu = UToolMenus::Get()->ExtendMenu(TEXT("ContentBrowser.AssetContextMenu.Texture2D"));
	if (!Menu)
	{
		return;
	}

	FToolMenuSection& Section = Menu->FindOrAddSection(TEXT("GetAssetActions"));
	Section.AddDynamicEntry(TEXT("MSDFTextureTools.Generate"), FNewToolMenuSectionDelegate::CreateLambda(
		[](FToolMenuSection& InSection)
		{
			const UContentBrowserAssetContextMenuContext* Context = InSection.FindContext<UContentBrowserAssetContextMenuContext>();
			if (!Context || Context->SelectedAssets.IsEmpty())
			{
				return;
			}

			TArray<FAssetData> TextureAssets;
			for (const FAssetData& AssetData : Context->SelectedAssets)
			{
				if (AssetData.AssetClassPath == UTexture2D::StaticClass()->GetClassPathName())
				{
					TextureAssets.Add(AssetData);
				}
			}

			if (TextureAssets.IsEmpty())
			{
				return;
			}

			InSection.AddSubMenu(
				TEXT("MSDFTextureTools.SubMenu"),
				LOCTEXT("MSDFSubMenu_Label", "MSDF 텍스쳐 변환"),
				LOCTEXT("MSDFSubMenu_Tooltip", "선택된 Texture2D 알파 마스크로부터 SDF/MSDF/MTSDF 텍스쳐를 생성합니다."),
				FNewToolMenuDelegate::CreateLambda([TextureAssets](UToolMenu* SubMenu)
				{
					FToolMenuSection& SubSection = SubMenu->FindOrAddSection(TEXT("GenerateTypes"));

					SubSection.AddMenuEntry(
						TEXT("GenerateSDF"),
						LOCTEXT("GenerateSDF_Label", "SDF 텍스쳐 변환"),
						LOCTEXT("GenerateSDF_Tooltip", "단일 채널 SDF 텍스쳐를 생성합니다. (A=SDF)"),
						FSlateIcon(),
						FUIAction(FExecuteAction::CreateLambda([TextureAssets]()
						{
							FMSDFTextureToolsEditorModule& Module = FModuleManager::LoadModuleChecked<FMSDFTextureToolsEditorModule>(TEXT("MSDFTextureToolsEditor"));
							Module.OpenGenerateWindow(TextureAssets, EMSDFGenerationMode::SDF);
						}))
					);

					SubSection.AddMenuEntry(
						TEXT("GenerateMSDF"),
						LOCTEXT("GenerateMSDF_Label", "MSDF 텍스쳐 변환"),
						LOCTEXT("GenerateMSDF_Tooltip", "멀티채널 SDF 텍스쳐를 생성합니다. (RGB=MSDF)"),
						FSlateIcon(),
						FUIAction(FExecuteAction::CreateLambda([TextureAssets]()
						{
							FMSDFTextureToolsEditorModule& Module = FModuleManager::LoadModuleChecked<FMSDFTextureToolsEditorModule>(TEXT("MSDFTextureToolsEditor"));
							Module.OpenGenerateWindow(TextureAssets, EMSDFGenerationMode::MSDF);
						}))
					);

					SubSection.AddMenuEntry(
						TEXT("GenerateMTSDF"),
						LOCTEXT("GenerateMTSDF_Label", "MTSDF 텍스쳐 변환"),
						LOCTEXT("GenerateMTSDF_Tooltip", "멀티채널 True SDF 텍스쳐를 생성합니다. (RGB=MSDF, A=True SDF)"),
						FSlateIcon(),
						FUIAction(FExecuteAction::CreateLambda([TextureAssets]()
						{
							FMSDFTextureToolsEditorModule& Module = FModuleManager::LoadModuleChecked<FMSDFTextureToolsEditorModule>(TEXT("MSDFTextureToolsEditor"));
							Module.OpenGenerateWindow(TextureAssets, EMSDFGenerationMode::MTSDF);
						}))
					);
				}),
				false,
				FSlateIcon(TEXT("MSDFTextureToolsStyle"), TEXT("MSDFTextureTools.MenuIcon"))
			);
		}));
}

void FMSDFTextureToolsEditorModule::UnregisterMenus()
{
	if (UToolMenus::IsToolMenuUIEnabled())
	{
		UToolMenus::UnRegisterStartupCallback(this);
		UToolMenus::UnregisterOwner(this);
	}
}

void FMSDFTextureToolsEditorModule::OpenGenerateWindow(const TArray<FAssetData>& SelectedAssets, EMSDFGenerationMode Mode)
{
	if (SelectedAssets.IsEmpty())
	{
		return;
	}

	UTexture2D* SourceTexture = Cast<UTexture2D>(SelectedAssets[0].GetAsset());
	if (!SourceTexture)
	{
		FMessageDialog::Open(EAppMsgType::Ok, LOCTEXT("InvalidSelection", "텍스쳐 변환을 시작하려면 Texture2D 에셋을 선택하세요."));
		return;
	}

	FText WindowTitle;
	switch (Mode)
	{
	case EMSDFGenerationMode::SDF:
		WindowTitle = LOCTEXT("WindowTitle_SDF", "SDF 텍스쳐 변환");
		break;
	case EMSDFGenerationMode::MSDF:
		WindowTitle = LOCTEXT("WindowTitle_MSDF", "MSDF 텍스쳐 변환");
		break;
	case EMSDFGenerationMode::MTSDF:
	default:
		WindowTitle = LOCTEXT("WindowTitle_MTSDF", "MTSDF 텍스쳐 변환");
		break;
	}

	const FString DefaultOutputFolder = FPackageName::GetLongPackagePath(SourceTexture->GetOutermost()->GetName());

	TSharedRef<SWindow> Window = SNew(SWindow)
		.Title(WindowTitle)
		.ClientSize(FVector2D(720.0f, 860.0f))
		.SupportsMaximize(false)
		.SupportsMinimize(false);

	Window->SetContent(
		SNew(SMSDFGenerateDialog)
		.SourceTexture(SourceTexture)
		.DefaultOutputFolder(DefaultOutputFolder)
		.GenerationMode(Mode)
	);

	FSlateApplication::Get().AddWindow(Window);
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FMSDFTextureToolsEditorModule, MSDFTextureToolsEditor)
