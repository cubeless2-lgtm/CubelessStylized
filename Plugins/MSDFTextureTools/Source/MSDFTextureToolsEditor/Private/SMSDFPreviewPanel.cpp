#include "SMSDFPreviewPanel.h"

#include "Brushes/SlateColorBrush.h"
#include "Rendering/DrawElements.h"

void SMSDFPreviewPanel::Construct(const FArguments& InArgs)
{
	SetCanTick(false);
}

void SMSDFPreviewPanel::SetContent(const FSlateBrush* InBrush, const FVector2D& InNaturalSize)
{
	Brush = InBrush;
	NaturalSize = InNaturalSize.IsNearlyZero() ? FVector2D(256.0f, 256.0f) : InNaturalSize;

	// Initial zoom: fit the longer side to 256px without upscaling
	const float MaxDim = FMath::Max(NaturalSize.X, NaturalSize.Y);
	ZoomScale = MaxDim > 0.0f ? FMath::Min(1.0f, 256.0f / MaxDim) : 1.0f;
	PanOffset = FVector2D::ZeroVector;

	Invalidate(EInvalidateWidgetReason::Paint);
}

void SMSDFPreviewPanel::ResetView()
{
	const float MaxDim = FMath::Max(NaturalSize.X, NaturalSize.Y);
	ZoomScale = MaxDim > 0.0f ? FMath::Min(1.0f, 256.0f / MaxDim) : 1.0f;
	PanOffset = FVector2D::ZeroVector;
	Invalidate(EInvalidateWidgetReason::Paint);
}

FVector2D SMSDFPreviewPanel::ComputeDesiredSize(float) const
{
	return FVector2D(256.0f, 256.0f);
}

int32 SMSDFPreviewPanel::OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry,
	const FSlateRect& MyCullingRect, FSlateWindowElementList& OutDrawElements,
	int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	// Dark background
	static const FSlateColorBrush BackgroundBrush(FLinearColor(0.02f, 0.02f, 0.02f, 1.0f));
	FSlateDrawElement::MakeBox(
		OutDrawElements,
		LayerId++,
		AllottedGeometry.ToPaintGeometry(),
		&BackgroundBrush
	);

	if (!Brush || !Brush->GetResourceObject())
	{
		return LayerId;
	}

	const FVector2D ViewSize = AllottedGeometry.GetLocalSize();
	const FVector2D ImageSize = NaturalSize * ZoomScale;
	const FVector2D ImagePos = (ViewSize - ImageSize) * 0.5f + PanOffset;

	// Clip so the image never renders outside the panel bounds
	OutDrawElements.PushClip(FSlateClippingZone(AllottedGeometry));

	FSlateDrawElement::MakeBox(
		OutDrawElements,
		LayerId,
		AllottedGeometry.ToPaintGeometry(ImageSize, FSlateLayoutTransform(ImagePos)),
		Brush,
		ESlateDrawEffect::None,
		FLinearColor::White
	);

	OutDrawElements.PopClip();

	return LayerId;
}

FReply SMSDFPreviewPanel::OnMouseWheel(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	// Wheel down (negative delta) = zoom in / Wheel up (positive delta) = zoom out
	const float Factor = MouseEvent.GetWheelDelta() < 0.0f ? 1.15f : (1.0f / 1.15f);
	ZoomScale = FMath::Clamp(ZoomScale * Factor, 0.05f, 32.0f);
	ClampPanOffset(MyGeometry.GetLocalSize());
	Invalidate(EInvalidateWidgetReason::Paint);
	return FReply::Handled();
}

FReply SMSDFPreviewPanel::OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	if (MouseEvent.GetEffectingButton() == EKeys::MiddleMouseButton)
	{
		bIsPanning = true;
		LastLocalMousePos = MyGeometry.AbsoluteToLocal(MouseEvent.GetScreenSpacePosition());
		return FReply::Handled().CaptureMouse(AsShared());
	}
	return FReply::Unhandled();
}

FReply SMSDFPreviewPanel::OnMouseButtonUp(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	if (MouseEvent.GetEffectingButton() == EKeys::MiddleMouseButton && bIsPanning)
	{
		bIsPanning = false;
		return FReply::Handled().ReleaseMouseCapture();
	}
	return FReply::Unhandled();
}

FReply SMSDFPreviewPanel::OnMouseMove(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	if (bIsPanning)
	{
		const FVector2D CurrentLocalPos = MyGeometry.AbsoluteToLocal(MouseEvent.GetScreenSpacePosition());
		PanOffset += CurrentLocalPos - LastLocalMousePos;
		LastLocalMousePos = CurrentLocalPos;
		ClampPanOffset(MyGeometry.GetLocalSize());
		Invalidate(EInvalidateWidgetReason::Paint);
		return FReply::Handled();
	}
	return FReply::Unhandled();
}

FCursorReply SMSDFPreviewPanel::OnCursorQuery(const FGeometry& MyGeometry, const FPointerEvent& CursorEvent) const
{
	return FCursorReply::Cursor(bIsPanning ? EMouseCursor::GrabHandClosed : EMouseCursor::Default);
}

void SMSDFPreviewPanel::ClampPanOffset(const FVector2D& ViewSize)
{
	const FVector2D ImageSize = NaturalSize * ZoomScale;

	// Max pan = half of the overflow in each axis; zero when image is smaller than view
	const float MaxX = FMath::Max(0.0f, (ImageSize.X - ViewSize.X) * 0.5f);
	PanOffset.X = FMath::Clamp(PanOffset.X, -MaxX, MaxX);

	const float MaxY = FMath::Max(0.0f, (ImageSize.Y - ViewSize.Y) * 0.5f);
	PanOffset.Y = FMath::Clamp(PanOffset.Y, -MaxY, MaxY);
}
