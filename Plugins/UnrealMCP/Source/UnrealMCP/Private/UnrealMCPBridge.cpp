#include "UnrealMCPBridge.h"
#include "MCPServerRunnable.h"
#include "Sockets.h"
#include "SocketSubsystem.h"
#include "HAL/RunnableThread.h"
#include "Interfaces/IPv4/IPv4Address.h"
#include "Interfaces/IPv4/IPv4Endpoint.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonWriter.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/DirectionalLight.h"
#include "Engine/PointLight.h"
#include "Engine/SpotLight.h"
#include "Camera/CameraActor.h"
#include "EditorAssetLibrary.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "JsonObjectConverter.h"
#include "GameFramework/Actor.h"
#include "Engine/Selection.h"
#include "Kismet/GameplayStatics.h"
#include "Async/Async.h"
#include "Engine/Texture2D.h"
#include "Containers/Ticker.h"
#include "Framework/Application/SlateApplication.h"
#include "ImageUtils.h"
#include "Interfaces/IPluginManager.h"
#include "Styling/SlateBrush.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SWindow.h"
#include "Widgets/Notifications/SProgressBar.h"
#include "Widgets/Text/STextBlock.h"
// Add Blueprint related includes
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "Factories/BlueprintFactory.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_Event.h"
#include "K2Node_VariableGet.h"
#include "K2Node_VariableSet.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Components/SphereComponent.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
// UE5.5 correct includes
#include "Engine/SimpleConstructionScript.h"
#include "Engine/SCS_Node.h"
#include "UObject/Field.h"
#include "UObject/FieldPath.h"
// Blueprint Graph specific includes
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "K2Node_CallFunction.h"
#include "K2Node_InputAction.h"
#include "K2Node_Self.h"
#include "GameFramework/InputSettings.h"
#include "EditorSubsystem.h"
#include "Subsystems/EditorActorSubsystem.h"
// Include our new command handler classes
#include "Commands/UnrealMCPEditorCommands.h"
#include "Commands/UnrealMCPBlueprintCommands.h"
#include "Commands/UnrealMCPBlueprintNodeCommands.h"
#include "Commands/UnrealMCPProjectCommands.h"
#include "Commands/UnrealMCPCommonUtils.h"
#include "Commands/UnrealMCPUMGCommands.h"

// Default settings
#define MCP_SERVER_HOST "127.0.0.1"
#define MCP_SERVER_PORT 55557

namespace
{
class FIetaMCPStatusWindow
{
public:
    static void ShowWithParams(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
    {
        PendingParamsSummary = BuildParamsSummary(Params);
        bUsePendingParamsOnNextShow = true;
        Show(CommandType);
    }

    static void Show(const FString& CommandType)
    {
        if (!FSlateApplication::IsInitialized())
        {
            return;
        }

        if (bUsePendingParamsOnNextShow)
        {
            bUsePendingParamsOnNextShow = false;
        }
        else
        {
            PendingParamsSummary.Reset();
        }

        ++CloseRequestGeneration;

        if (StatusWindow.IsValid())
        {
            const TSharedPtr<SWindow> ExistingWindow = StatusWindow.Pin();
            LastShowTime = FPlatformTime::Seconds();
            SetProcessingStatus(CommandType);
            ExistingWindow->BringToFront();
            FlushSlateWindowNow(ExistingWindow.ToSharedRef());
            return;
        }

        const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("UnrealMCP"));
        const FString ImagePath = Plugin.IsValid()
            ? FPaths::Combine(Plugin->GetBaseDir(), TEXT("Resources"), TEXT("Ieta.png"))
            : FString();

        if (!AvatarTexture && FPaths::FileExists(ImagePath))
        {
            AvatarTexture = FImageUtils::ImportFileAsTexture2D(ImagePath);
            if (AvatarTexture)
            {
                AvatarTexture->AddToRoot();
                AvatarTexture->SRGB = true;
            }
        }

        if (AvatarTexture)
        {
            AvatarBrush = MakeShared<FSlateBrush>();
            AvatarBrush->SetResourceObject(AvatarTexture);
            AvatarBrush->ImageSize = FVector2D(96.0f, 96.0f);
            AvatarBrush->DrawAs = ESlateBrushDrawType::Image;
        }
        else
        {
            AvatarBrush.Reset();
        }

        const FText TitleText = FText::FromString(TEXT("이에타가 처리 중"));
        const FText BodyText = FText::FromString(FString::Printf(
            TEXT("흥, 잠깐 기다려.\n")
            TEXT("이에타가 MCP 작업을 지켜보고 있어.\n")
            TEXT("명령: %s\n")
            TEXT("끝나면 티브렛이 알아서 정리해둘 거야."),
            *CommandType));

        TSharedRef<SWindow> Window = SNew(SWindow)
            .Title(TitleText)
            .ClientSize(FVector2D(620.0f, 240.0f))
            .SizingRule(ESizingRule::FixedSize)
            .SupportsMaximize(false)
            .SupportsMinimize(false)
            .HasCloseButton(true)
            .IsTopmostWindow(true)
            [
                SNew(SBorder)
                .Padding(18.0f)
                .BorderBackgroundColor(FLinearColor(0.035f, 0.035f, 0.042f, 0.96f))
                [
                    SNew(SHorizontalBox)

                    + SHorizontalBox::Slot()
                    .AutoWidth()
                    .VAlign(VAlign_Center)
                    [
                        SNew(SBox)
                        .WidthOverride(112.0f)
                        .HeightOverride(112.0f)
                        [
                            SNew(SImage)
                            .Image(AvatarBrush.IsValid() ? AvatarBrush.Get() : FCoreStyle::Get().GetDefaultBrush())
                        ]
                    ]

                    + SHorizontalBox::Slot()
                    .FillWidth(1.0f)
                    .Padding(18.0f, 0.0f, 0.0f, 0.0f)
                    .VAlign(VAlign_Center)
                    [
                        SNew(SVerticalBox)

                        + SVerticalBox::Slot()
                        .AutoHeight()
                        [
                            SNew(STextBlock)
                            .Text(TitleText)
                            .ColorAndOpacity(FLinearColor(1.0f, 0.86f, 0.48f, 1.0f))
                            .Font(FCoreStyle::GetDefaultFontStyle("Bold", 18))
                        ]

                        + SVerticalBox::Slot()
                        .AutoHeight()
                        .Padding(0.0f, 10.0f, 0.0f, 0.0f)
                        [
                            SAssignNew(BodyTextBlock, STextBlock)
                            .Text(BodyText)
                            .AutoWrapText(true)
                            .ColorAndOpacity(FLinearColor(0.93f, 0.93f, 0.96f, 1.0f))
                            .Font(FCoreStyle::GetDefaultFontStyle("Regular", 12))
                        ]

                        + SVerticalBox::Slot()
                        .AutoHeight()
                        .Padding(0.0f, 14.0f, 0.0f, 0.0f)
                        [
                            SAssignNew(ProgressBar, SProgressBar)
                            .Percent(0.05f)
                        ]
                    ]
                ]
            ];

        StatusWindow = Window;
        LastShowTime = FPlatformTime::Seconds();
        FSlateApplication::Get().AddWindow(Window);
        SetProcessingStatus(CommandType);
        FlushSlateWindowNow(Window);
    }

    static void UpdateStatus(const FString& StatusText, const FString& CommandType, TOptional<float> Progress = TOptional<float>())
    {
        if (!FSlateApplication::IsInitialized())
        {
            return;
        }

        if (!StatusWindow.IsValid())
        {
            Show(CommandType.IsEmpty() ? TEXT("ieta_status") : CommandType);
        }

        const FString EffectiveCommand = CommandType.IsEmpty() ? TEXT("작업 상태") : CommandType;
        const bool bPlanning = IsIetaPlanningCommand(EffectiveCommand);
        const FText UpdatedBodyText = bPlanning
            ? FText::FromString(FString::Printf(
                TEXT("흠, 생각은 이 정도면 됐어.\n")
                TEXT("%s\n")
                TEXT("명령: %s\n")
                TEXT("정리해서 넘기면 되겠지."),
                *StatusText,
                *EffectiveCommand))
            : FText::FromString(FString::Printf(
                TEXT("흥, 티브렛이 하는 일은 설명해줄게.\n")
                TEXT("%s\n")
                TEXT("명령: %s\n")
                TEXT("끝날 때까지 얌전히 기다려."),
                *StatusText,
                *EffectiveCommand));

        if (BodyTextBlock.IsValid())
        {
            BodyTextBlock->SetText(UpdatedBodyText);
        }

        if (ProgressBar.IsValid())
        {
            ProgressBar->SetVisibility(EVisibility::Visible);
            if (Progress.IsSet())
            {
                ProgressBar->SetPercent(FMath::Clamp(Progress.GetValue(), 0.0f, 1.0f));
            }
        }

        LastShowTime = FPlatformTime::Seconds();
        if (StatusWindow.IsValid())
        {
            const TSharedPtr<SWindow> Window = StatusWindow.Pin();
            Window->BringToFront();
            FlushSlateWindowNow(Window.ToSharedRef());
        }
    }

    static void CompleteCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& ResponseJson)
    {
        FString ResponseStatus;
        if (ResponseJson.IsValid())
        {
            ResponseJson->TryGetStringField(TEXT("status"), ResponseStatus);
        }

        FString DetailText;
        if (ResponseJson.IsValid())
        {
            ResponseJson->TryGetStringField(TEXT("error"), DetailText);
            if (DetailText.IsEmpty())
            {
                ResponseJson->TryGetStringField(TEXT("message"), DetailText);
            }
        }

        const bool bSucceeded = ResponseStatus == TEXT("success");
        if (IsIetaPlanningCommand(CommandType))
        {
            const FString IetaPlanningCompletionText = bSucceeded
                ? TEXT("계획은 끝났어. 이제 필요한 걸 넘기면 돼.")
                : FString::Printf(TEXT("흠, 생각하다가 막혔어.%s%s"),
                    DetailText.IsEmpty() ? TEXT("") : TEXT("\n"),
                    *DetailText);

            UpdateStatus(IetaPlanningCompletionText, CommandType, TOptional<float>(1.0f));
            Hide();
            return;
        }

        const FString CompletionText = bSucceeded
            ? TEXT("MCP 작업 완료: 성공")
            : FString::Printf(TEXT("MCP 작업 완료: 실패%s%s"),
                DetailText.IsEmpty() ? TEXT("") : TEXT("\n"),
                *DetailText);

        (void)CompletionText;

        const FString IetaCompletionText = bSucceeded
            ? TEXT("끝났어. 티브렛이 처리해뒀어.")
            : FString::Printf(TEXT("흠, 티브렛이 여기서 막혔어.%s%s"),
                DetailText.IsEmpty() ? TEXT("") : TEXT("\n"),
                *DetailText);

        UpdateStatus(IetaCompletionText, CommandType, TOptional<float>(1.0f));
        Hide();
    }

    static void Hide()
    {
        if (!FSlateApplication::IsInitialized())
        {
            StatusWindow.Reset();
            AvatarBrush.Reset();
            BodyTextBlock.Reset();
            ProgressBar.Reset();
            return;
        }

        if (StatusWindow.IsValid())
        {
            const double RemainingSeconds = CompletionVisibleSeconds - (FPlatformTime::Seconds() - LastShowTime);
            if (RemainingSeconds > 0.0)
            {
                const TWeakPtr<SWindow> WindowToClose = StatusWindow;
                const uint64 RequestedGeneration = CloseRequestGeneration;
                FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([WindowToClose, RequestedGeneration](float)
                {
                    if (CloseRequestGeneration != RequestedGeneration)
                    {
                        return false;
                    }

                    if (WindowToClose.IsValid())
                    {
                        WindowToClose.Pin()->RequestDestroyWindow();
                    }
                    const TSharedPtr<SWindow> CurrentWindow = StatusWindow.Pin();
                    const TSharedPtr<SWindow> ExpectedWindow = WindowToClose.Pin();
                    if ((CurrentWindow.IsValid() && ExpectedWindow.IsValid() && CurrentWindow.Get() == ExpectedWindow.Get()) ||
                        (!CurrentWindow.IsValid() && !ExpectedWindow.IsValid()))
                    {
                        StatusWindow.Reset();
                        AvatarBrush.Reset();
                        BodyTextBlock.Reset();
                        ProgressBar.Reset();
                    }
                    return false;
                }), static_cast<float>(RemainingSeconds));
                return;
            }
        }

        if (StatusWindow.IsValid())
        {
            StatusWindow.Pin()->RequestDestroyWindow();
        }

        StatusWindow.Reset();
        AvatarBrush.Reset();
        BodyTextBlock.Reset();
        ProgressBar.Reset();
    }

private:
    static bool IsIetaPlanningCommand(const FString& CommandType)
    {
        return CommandType.IsEmpty() ||
            CommandType == TEXT("ieta_status") ||
            CommandType == TEXT("codex_start") ||
            CommandType == TEXT("이에타");
    }

    static FString GetFriendlyCommandText(const FString& CommandType)
    {
        if (CommandType == TEXT("codex_connection"))
        {
            return TEXT("Codex가 Unreal MCP에 연결됐어.");
        }
        if (CommandType == TEXT("ieta_status"))
        {
            return TEXT("Unreal MCP 연결 상태를 확인하는 중이야.");
        }
        if (CommandType == TEXT("execute_python"))
        {
            return TEXT("에디터 Python 스크립트를 실행하는 중이야.");
        }
        if (CommandType == TEXT("get_actors_in_level"))
        {
            return TEXT("현재 레벨의 액터 목록을 확인하는 중이야.");
        }
        if (CommandType == TEXT("find_actors_by_name"))
        {
            return TEXT("이름으로 액터를 찾는 중이야.");
        }
        if (CommandType == TEXT("spawn_actor") || CommandType == TEXT("create_actor") || CommandType == TEXT("spawn_blueprint_actor"))
        {
            return TEXT("레벨에 액터를 배치하는 중이야.");
        }
        if (CommandType == TEXT("delete_actor"))
        {
            return TEXT("레벨의 액터를 정리하는 중이야.");
        }
        if (CommandType == TEXT("set_actor_transform") || CommandType == TEXT("set_actor_property"))
        {
            return TEXT("액터 설정을 바꾸는 중이야.");
        }
        if (CommandType.Contains(TEXT("blueprint")))
        {
            return TEXT("블루프린트 작업을 처리하는 중이야.");
        }
        if (CommandType.Contains(TEXT("widget")) || CommandType.Contains(TEXT("umg")))
        {
            return TEXT("위젯 작업을 처리하는 중이야.");
        }
        return TEXT("MCP 작업 요청을 처리하는 중이야.");
    }

    static FString BuildParamsSummary(const TSharedPtr<FJsonObject>& Params)
    {
        if (!Params.IsValid() || Params->Values.Num() == 0)
        {
            return FString();
        }

        FString ParamsString;
        TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ParamsString);
        FJsonSerializer::Serialize(Params.ToSharedRef(), Writer);
        ParamsString.ReplaceInline(TEXT("\r"), TEXT(""));
        ParamsString.ReplaceInline(TEXT("\n"), TEXT(" "));

        constexpr int32 MaxParamsLength = 220;
        if (ParamsString.Len() > MaxParamsLength)
        {
            ParamsString = ParamsString.Left(MaxParamsLength - 3) + TEXT("...");
        }

        return ParamsString;
    }

    static FText BuildProcessingBodyText(const FString& CommandType)
    {
        const FString EffectiveCommand = CommandType.IsEmpty() ? TEXT("codex_start") : CommandType;
        const FString DetailText = PendingParamsSummary.IsEmpty() ? TEXT("추가 입력은 없어.") : PendingParamsSummary;
        if (IsIetaPlanningCommand(EffectiveCommand))
        {
            return FText::FromString(TEXT("흠, 잠깐 생각 좀 할게.\n계획을 정리하고 있어.\n보채지 말고 조용히 기다려."));
        }
        if (FPlatformTime::Seconds() >= 0.0)
        {
            return FText::FromString(FString::Printf(
                TEXT("흥, 티브렛이 일을 시작했어.\n")
                TEXT("%s\n")
                TEXT("명령: %s\n")
                TEXT("내용: %s\n")
                TEXT("귀찮지만 진행은 내가 보고 있을게."),
                *GetFriendlyCommandText(EffectiveCommand),
                *EffectiveCommand,
                *DetailText));
        }

        return FText::FromString(FString::Printf(
            TEXT("흥, Codex가 Unreal MCP 작업을 시작했어.\n")
            TEXT("이에타가 진행 중인 명령을 지켜보고 있어.\n")
            TEXT("명령: %s\n")
            TEXT("결과가 표시되면 창은 알아서 닫힐 거야."),
            *EffectiveCommand));
    }

    static void SetProcessingStatus(const FString& CommandType)
    {
        if (BodyTextBlock.IsValid())
        {
            BodyTextBlock->SetText(BuildProcessingBodyText(CommandType));
        }

        if (ProgressBar.IsValid())
        {
            ProgressBar->SetVisibility(EVisibility::Visible);
            ProgressBar->SetPercent(IsIetaPlanningCommand(CommandType) ? 0.15f : 0.05f);
        }
    }

    static void FlushSlateWindowNow(const TSharedRef<SWindow>& Window)
    {
        FSlateApplication& SlateApplication = FSlateApplication::Get();
        SlateApplication.PumpMessages();
        SlateApplication.ForceRedrawWindow(Window);
    }

    static constexpr double CompletionVisibleSeconds = 5.0;
    static double LastShowTime;
    static TWeakPtr<SWindow> StatusWindow;
    static TSharedPtr<STextBlock> BodyTextBlock;
    static TSharedPtr<SProgressBar> ProgressBar;
    static TSharedPtr<FSlateBrush> AvatarBrush;
    static UTexture2D* AvatarTexture;
    static FString PendingParamsSummary;
    static bool bUsePendingParamsOnNextShow;
    static uint64 CloseRequestGeneration;
};

double FIetaMCPStatusWindow::LastShowTime = 0.0;
TWeakPtr<SWindow> FIetaMCPStatusWindow::StatusWindow;
TSharedPtr<STextBlock> FIetaMCPStatusWindow::BodyTextBlock;
TSharedPtr<SProgressBar> FIetaMCPStatusWindow::ProgressBar;
TSharedPtr<FSlateBrush> FIetaMCPStatusWindow::AvatarBrush;
UTexture2D* FIetaMCPStatusWindow::AvatarTexture = nullptr;
FString FIetaMCPStatusWindow::PendingParamsSummary;
bool FIetaMCPStatusWindow::bUsePendingParamsOnNextShow = false;
uint64 FIetaMCPStatusWindow::CloseRequestGeneration = 0;

}

UUnrealMCPBridge::UUnrealMCPBridge()
{
    EditorCommands = MakeShared<FUnrealMCPEditorCommands>();
    BlueprintCommands = MakeShared<FUnrealMCPBlueprintCommands>();
    BlueprintNodeCommands = MakeShared<FUnrealMCPBlueprintNodeCommands>();
    ProjectCommands = MakeShared<FUnrealMCPProjectCommands>();
    UMGCommands = MakeShared<FUnrealMCPUMGCommands>();
}

UUnrealMCPBridge::~UUnrealMCPBridge()
{
    EditorCommands.Reset();
    BlueprintCommands.Reset();
    BlueprintNodeCommands.Reset();
    ProjectCommands.Reset();
    UMGCommands.Reset();
}

// Initialize subsystem
void UUnrealMCPBridge::Initialize(FSubsystemCollectionBase& Collection)
{
    UE_LOG(LogTemp, Display, TEXT("UnrealMCPBridge: Initializing"));
    
    bIsRunning = false;
    ListenerSocket = nullptr;
    ConnectionSocket = nullptr;
    ServerRunnable = nullptr;
    ServerThread = nullptr;
    Port = MCP_SERVER_PORT;
    FIPv4Address::Parse(MCP_SERVER_HOST, ServerAddress);

    // Start the server automatically
    StartServer();
}

// Clean up resources when subsystem is destroyed
void UUnrealMCPBridge::Deinitialize()
{
    UE_LOG(LogTemp, Display, TEXT("UnrealMCPBridge: Shutting down"));
    StopServer();
}

// Start the MCP server
void UUnrealMCPBridge::StartServer()
{
    if (bIsRunning)
    {
        UE_LOG(LogTemp, Warning, TEXT("UnrealMCPBridge: Server is already running"));
        return;
    }

    // Create socket subsystem
    ISocketSubsystem* SocketSubsystem = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
    if (!SocketSubsystem)
    {
        UE_LOG(LogTemp, Error, TEXT("UnrealMCPBridge: Failed to get socket subsystem"));
        return;
    }

    // Create listener socket
    TSharedPtr<FSocket> NewListenerSocket = MakeShareable(SocketSubsystem->CreateSocket(NAME_Stream, TEXT("UnrealMCPListener"), false));
    if (!NewListenerSocket.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("UnrealMCPBridge: Failed to create listener socket"));
        return;
    }

    // Allow address reuse for quick restarts
    NewListenerSocket->SetReuseAddr(true);
    NewListenerSocket->SetNonBlocking(true);

    // Bind to address
    FIPv4Endpoint Endpoint(ServerAddress, Port);
    if (!NewListenerSocket->Bind(*Endpoint.ToInternetAddr()))
    {
        UE_LOG(LogTemp, Error, TEXT("UnrealMCPBridge: Failed to bind listener socket to %s:%d"), *ServerAddress.ToString(), Port);
        return;
    }

    // Start listening
    if (!NewListenerSocket->Listen(5))
    {
        UE_LOG(LogTemp, Error, TEXT("UnrealMCPBridge: Failed to start listening"));
        return;
    }

    ListenerSocket = NewListenerSocket;
    bIsRunning = true;
    UE_LOG(LogTemp, Display, TEXT("UnrealMCPBridge: Server started on %s:%d"), *ServerAddress.ToString(), Port);

    // Start server thread
    ServerRunnable = new FMCPServerRunnable(this, ListenerSocket);
    ServerThread = FRunnableThread::Create(
        ServerRunnable,
        TEXT("UnrealMCPServerThread"),
        0, TPri_Normal
    );

    if (!ServerThread)
    {
        UE_LOG(LogTemp, Error, TEXT("UnrealMCPBridge: Failed to create server thread"));
        delete ServerRunnable;
        ServerRunnable = nullptr;
        StopServer();
        return;
    }
}

// Stop the MCP server
void UUnrealMCPBridge::StopServer()
{
    if (!bIsRunning)
    {
        return;
    }

    bIsRunning = false;

    // Clean up thread
    if (ServerThread)
    {
        if (ServerRunnable)
        {
            ServerRunnable->Stop();
        }
        ServerThread->WaitForCompletion();
        delete ServerThread;
        ServerThread = nullptr;
    }

    delete ServerRunnable;
    ServerRunnable = nullptr;

    // Close sockets
    if (ConnectionSocket.IsValid())
    {
        ConnectionSocket->Close();
        ConnectionSocket.Reset();
    }

    if (ListenerSocket.IsValid())
    {
        ListenerSocket->Close();
        ListenerSocket.Reset();
    }

    UE_LOG(LogTemp, Display, TEXT("UnrealMCPBridge: Server stopped"));
}

// Execute a command received from a client
FString UUnrealMCPBridge::ExecuteCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
    UE_LOG(LogTemp, Display, TEXT("UnrealMCPBridge: Executing command: %s"), *CommandType);
    
    // Create a promise to wait for the result
    TSharedRef<TPromise<FString>, ESPMode::ThreadSafe> Promise = MakeShared<TPromise<FString>, ESPMode::ThreadSafe>();
    TFuture<FString> Future = Promise->GetFuture();
    
    auto RunCommand = [this, CommandType, Params, Promise]()
    {
        TSharedPtr<FJsonObject> ResponseJson = MakeShareable(new FJsonObject);
        
        try
        {
            TSharedPtr<FJsonObject> ResultJson;
            
            if (CommandType == TEXT("ping"))
            {
                ResultJson = MakeShareable(new FJsonObject);
                ResultJson->SetStringField(TEXT("message"), TEXT("pong"));
            }
            else if (CommandType == TEXT("ieta_status"))
            {
                FString StatusText;
                FString StatusCommand;
                double ProgressValue = -1.0;
                if (Params.IsValid())
                {
                    Params->TryGetStringField(TEXT("text"), StatusText);
                    Params->TryGetStringField(TEXT("command"), StatusCommand);
                    Params->TryGetNumberField(TEXT("progress"), ProgressValue);
                }

                if (StatusText.IsEmpty())
                {
                    StatusText = TEXT("이에타가 작업 상태를 확인하는 중이야.");
                }

                ResultJson = MakeShareable(new FJsonObject);
                ResultJson->SetBoolField(TEXT("success"), true);
                ResultJson->SetStringField(TEXT("text"), StatusText);
                ResultJson->SetStringField(TEXT("command"), StatusCommand);
                if (ProgressValue >= 0.0)
                {
                    ResultJson->SetNumberField(TEXT("progress"), ProgressValue);
                }
            }
            // Editor Commands (including actor manipulation)
            else if (CommandType == TEXT("get_actors_in_level") || 
                     CommandType == TEXT("find_actors_by_name") ||
                     CommandType == TEXT("spawn_actor") ||
                     CommandType == TEXT("create_actor") ||
                     CommandType == TEXT("delete_actor") || 
                     CommandType == TEXT("set_actor_transform") ||
                     CommandType == TEXT("get_actor_properties") ||
                     CommandType == TEXT("set_actor_property") ||
                     CommandType == TEXT("spawn_blueprint_actor") ||
                     CommandType == TEXT("focus_viewport") || 
                     CommandType == TEXT("take_screenshot"))
            {
                ResultJson = EditorCommands->HandleCommand(CommandType, Params);
            }
            // Blueprint Commands
            else if (CommandType == TEXT("create_blueprint") || 
                     CommandType == TEXT("add_component_to_blueprint") || 
                     CommandType == TEXT("set_component_property") || 
                     CommandType == TEXT("set_physics_properties") || 
                     CommandType == TEXT("compile_blueprint") || 
                     CommandType == TEXT("set_blueprint_property") || 
                     CommandType == TEXT("set_static_mesh_properties") ||
                     CommandType == TEXT("set_pawn_properties"))
            {
                ResultJson = BlueprintCommands->HandleCommand(CommandType, Params);
            }
            // Blueprint Node Commands
            else if (CommandType == TEXT("connect_blueprint_nodes") || 
                     CommandType == TEXT("add_blueprint_get_self_component_reference") ||
                     CommandType == TEXT("add_blueprint_self_reference") ||
                     CommandType == TEXT("find_blueprint_nodes") ||
                     CommandType == TEXT("add_blueprint_event_node") ||
                     CommandType == TEXT("add_blueprint_input_action_node") ||
                     CommandType == TEXT("add_blueprint_function_node") ||
                     CommandType == TEXT("add_blueprint_get_component_node") ||
                     CommandType == TEXT("add_blueprint_variable"))
            {
                ResultJson = BlueprintNodeCommands->HandleCommand(CommandType, Params);
            }
            // Project Commands
            else if (CommandType == TEXT("create_input_mapping") ||
                     CommandType == TEXT("execute_python"))
            {
                ResultJson = ProjectCommands->HandleCommand(CommandType, Params);
            }
            // UMG Commands
            else if (CommandType == TEXT("create_umg_widget_blueprint") ||
                     CommandType == TEXT("add_text_block_to_widget") ||
                     CommandType == TEXT("add_button_to_widget") ||
                     CommandType == TEXT("bind_widget_event") ||
                     CommandType == TEXT("set_text_block_binding") ||
                     CommandType == TEXT("add_widget_to_viewport"))
            {
                ResultJson = UMGCommands->HandleCommand(CommandType, Params);
            }
            else
            {
                ResponseJson->SetStringField(TEXT("status"), TEXT("error"));
                ResponseJson->SetStringField(TEXT("error"), FString::Printf(TEXT("Unknown command: %s"), *CommandType));
                
                FIetaMCPStatusWindow::CompleteCommand(CommandType, ResponseJson);

                FString ResultString;
                TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ResultString);
                FJsonSerializer::Serialize(ResponseJson.ToSharedRef(), Writer);
                Promise->SetValue(ResultString);
                return;
            }
            
            // Check if the result contains an error
            bool bSuccess = true;
            FString ErrorMessage;
            
            if (ResultJson->HasField(TEXT("success")))
            {
                bSuccess = ResultJson->GetBoolField(TEXT("success"));
                if (!bSuccess && ResultJson->HasField(TEXT("error")))
                {
                    ErrorMessage = ResultJson->GetStringField(TEXT("error"));
                }
            }
            
            if (bSuccess)
            {
                // Set success status and include the result
                ResponseJson->SetStringField(TEXT("status"), TEXT("success"));
                ResponseJson->SetObjectField(TEXT("result"), ResultJson);
            }
            else
            {
                // Set error status and include the error message
                ResponseJson->SetStringField(TEXT("status"), TEXT("error"));
                ResponseJson->SetStringField(TEXT("error"), ErrorMessage);
            }
        }
        catch (const std::exception& e)
        {
            ResponseJson->SetStringField(TEXT("status"), TEXT("error"));
            ResponseJson->SetStringField(TEXT("error"), UTF8_TO_TCHAR(e.what()));
        }
        
        FIetaMCPStatusWindow::CompleteCommand(CommandType, ResponseJson);

        FString ResultString;
        TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ResultString);
        FJsonSerializer::Serialize(ResponseJson.ToSharedRef(), Writer);
        Promise->SetValue(ResultString);
    };

    // Queue execution on Game Thread. Show the assistant window first, then run
    // the command on the next tick so the editor has a chance to paint the UI.
    // Python import workflows can enter UE's Interchange pipeline, which must
    // not run inside a TaskGraph task because it may wait on TaskGraph work
    // internally.
    AsyncTask(ENamedThreads::GameThread, [CommandType, Params, RunCommand]()
    {
        FIetaMCPStatusWindow::ShowWithParams(CommandType, Params);
        FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([RunCommand](float)
        {
            RunCommand();
            return false;
        }));
    });
    
    return Future.Get();
}
