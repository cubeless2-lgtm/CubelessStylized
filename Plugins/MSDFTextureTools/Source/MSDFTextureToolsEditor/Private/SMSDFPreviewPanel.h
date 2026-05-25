#pragma once

#include "CoreMinimal.h"
#include "Styling/SlateBrush.h"
#include "Widgets/SLeafWidget.h"

// Interactive preview panel: scroll-wheel zoom, middle-mouse-drag pan.
// Pan is clamped so the viewport cannot go outside the image boundary.
class SMSDFPreviewPanel : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SMSDFPreviewPanel) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	// Call after each generation. Resets zoom/pan to fit-in-panel.
	void SetContent(const FSlateBrush* InBrush, const FVector2D& InNaturalSize);
	void ResetView();

	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry,
		const FSlateRect& MyCullingRect, FSlateWindowElementList& OutDrawElements,
		int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

	virtual FVector2D ComputeDesiredSize(float LayoutScaleMultiplier) const override;
	virtual FReply OnMouseWheel(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual FReply OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual FReply OnMouseButtonUp(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual FReply OnMouseMove(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual FCursorReply OnCursorQuery(const FGeometry& MyGeometry, const FPointerEvent& CursorEvent) const override;
	virtual bool SupportsKeyboardFocus() const override { return false; }

private:
	void ClampPanOffset(const FVector2D& ViewSize);

	const FSlateBrush* Brush = nullptr;
	FVector2D NaturalSize = FVector2D(256.0f, 256.0f);
	float ZoomScale = 1.0f;
	FVector2D PanOffset = FVector2D::ZeroVector;
	bool bIsPanning = false;
	FVector2D LastLocalMousePos = FVector2D::ZeroVector;
};
