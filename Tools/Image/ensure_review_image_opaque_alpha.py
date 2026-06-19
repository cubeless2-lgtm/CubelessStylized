#!/usr/bin/env python3
"""Make user-facing review images fully opaque before display.

This hook is for screenshots and validation images shown to the user or used
for visual QA. It must not be used on source textures or masks where alpha is
intentional data.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_PYTHON_ROOT = PROJECT_ROOT / "Plugins" / "CustomTools" / "Content" / "Python" / "ArtScripts"

try:
    from PIL import Image  # type: ignore
except ModuleNotFoundError:
    if PLUGIN_PYTHON_ROOT.exists():
        sys.path.insert(0, str(PLUGIN_PYTHON_ROOT))
    from PIL import Image  # type: ignore


def _json_ready_extrema(extrema: tuple[int, int] | None) -> list[int] | None:
    if extrema is None:
        return None
    return [int(extrema[0]), int(extrema[1])]


def _resolve_output_path(input_path: Path, output_path: Path | None, in_place: bool) -> Path:
    if output_path:
        return output_path
    if in_place:
        return input_path
    suffix = input_path.suffix if input_path.suffix.lower() == ".png" else ".png"
    return input_path.with_name(f"{input_path.stem}_review_opaque{suffix}")


def ensure_review_image_opaque_alpha(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    in_place: bool = False,
) -> dict[str, Any]:
    source = Path(input_path).resolve()
    if not source.exists():
        return {
            "success": False,
            "input_path": str(source),
            "error": "input image does not exist",
            "opaque_for_review": False,
        }

    target = _resolve_output_path(
        source,
        Path(output_path).resolve() if output_path else None,
        in_place,
    )
    target.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as image:
        image.load()
        before_mode = image.mode
        before_bands = list(image.getbands())
        before_size = image.size
        rgba = image.convert("RGBA")
        before_alpha_extrema = rgba.getchannel("A").getextrema()

        if before_alpha_extrema != (255, 255) or target != source:
            rgba.putalpha(255)
            rgba.save(target, format="PNG")
            wrote_file = True
        else:
            wrote_file = False

    if target == source and not wrote_file:
        after_path = source
    elif target != source and not wrote_file:
        shutil.copy2(source, target)
        after_path = target
    else:
        after_path = target

    with Image.open(after_path) as image:
        image.load()
        after_mode = image.mode
        after_bands = list(image.getbands())
        after_rgba = image.convert("RGBA")
        after_alpha_extrema = after_rgba.getchannel("A").getextrema()

    return {
        "success": True,
        "input_path": str(source),
        "output_path": str(after_path),
        "changed": bool(wrote_file),
        "mode_before": before_mode,
        "bands_before": before_bands,
        "size": [int(before_size[0]), int(before_size[1])],
        "alpha_extrema_before": _json_ready_extrema(before_alpha_extrema),
        "mode_after": after_mode,
        "bands_after": after_bands,
        "alpha_extrema_after": _json_ready_extrema(after_alpha_extrema),
        "opaque_for_review": after_alpha_extrema == (255, 255),
        "policy": "review/display images must have alpha 255; source textures with intentional alpha are out of scope",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set every pixel alpha to 255 for a user-facing review image.",
    )
    parser.add_argument("input_path", help="Input image path.")
    parser.add_argument("--output", help="Output image path. Defaults to *_review_opaque.png.")
    parser.add_argument("--in-place", action="store_true", help="Rewrite the input image.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = ensure_review_image_opaque_alpha(
        args.input_path,
        args.output,
        in_place=args.in_place,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("opaque_for_review") else 1


if __name__ == "__main__":
    raise SystemExit(main())
