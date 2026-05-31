from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "SourceArt" / "Sky" / "CloudPlaneAtlas_LightPacked_UDSLike_RGBA_2048.png"
OUT_PACKED = ROOT / "SourceArt" / "Sky" / "CloudPlaneAtlas_LightPacked_UDSLike_RGBA_2048.png"
OUT_PREVIEW = ROOT / "SourceArt" / "Sky" / "CloudPlaneAtlas_LightPacked_UDSLike_Preview_2048.png"
CONTENT_PACKED = ROOT / "Content" / "Cubeless" / "Env" / "Sky" / "Textures" / "CloudPlaneAtlas_LightPacked_UDSLike_RGBA_2048.png"
CONTENT_PREVIEW = ROOT / "Content" / "Cubeless" / "Env" / "Sky" / "Textures" / "CloudPlaneAtlas_LightPacked_UDSLike_Preview_2048.png"


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    t = clamp01((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def channel_to_list(img: Image.Image) -> list[int]:
    return list(img.convert("L").getdata())


def make_preview(packed: Image.Image) -> Image.Image:
    r, g, b, a = packed.split()
    rp = channel_to_list(r)
    gp = channel_to_list(g)
    bp = channel_to_list(b)
    ap = channel_to_list(a)

    width, height = packed.size
    bg = (232, 242, 250)
    light = (255, 230, 185)
    shadow = (42, 74, 188)
    rim = (255, 246, 226)
    out = []

    # Preview uses a sunset/day mix to expose the stronger packed shading.
    for rv, gv, bv, av in zip(rp, gp, bp, ap):
        alpha = av / 255.0
        response = clamp01((rv * 0.25 + gv * 0.15 + bv * 0.60) / 255.0)
        rim_amount = clamp01((max(rv, gv) - bv * 0.35) / 255.0)
        cloud = [
            shadow[i] * (1.0 - response) + light[i] * response + rim[i] * rim_amount * 0.22
            for i in range(3)
        ]
        out.append(
            tuple(
                int(round(bg[i] * (1.0 - alpha) + min(255.0, cloud[i]) * alpha))
                for i in range(3)
            )
            + (255,)
        )

    preview = Image.new("RGBA", (width, height))
    preview.putdata(out)
    return preview


def main() -> None:
    src = Image.open(SRC).convert("RGBA")
    width, height = src.size
    base_r, base_g, base_b, alpha = src.split()

    alpha_blur = alpha.filter(ImageFilter.GaussianBlur(2.0))
    alpha_core = alpha.filter(ImageFilter.GaussianBlur(15.0))
    alpha_broad = alpha.filter(ImageFilter.GaussianBlur(36.0))
    alpha_edge = ImageChops.difference(alpha, alpha_blur).filter(ImageFilter.GaussianBlur(1.0))

    ap = channel_to_list(alpha)
    softp = channel_to_list(alpha_blur)
    corep = channel_to_list(alpha_core)
    broadp = channel_to_list(alpha_broad)
    edgep = channel_to_list(alpha_edge)
    base_luma = [
        int(round((rv * 0.30 + gv * 0.46 + bv * 0.24)))
        for rv, gv, bv in zip(channel_to_list(base_r), channel_to_list(base_g), channel_to_list(base_b))
    ]

    tile_cols = 4
    tile_rows = 2
    tile_w = width // tile_cols
    tile_h = height // tile_rows

    boxes: list[tuple[int, int, int, int]] = []
    for row in range(tile_rows):
        for col in range(tile_cols):
            x0 = col * tile_w
            y0 = row * tile_h
            x1 = x0 + tile_w
            y1 = y0 + tile_h
            min_x, min_y, max_x, max_y = x1, y1, x0, y0
            found = False
            for y in range(y0, y1):
                idx = y * width + x0
                for x in range(x0, x1):
                    if ap[idx + (x - x0)] > 10:
                        found = True
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                        max_x = max(max_x, x)
                        max_y = max(max_y, y)
            if not found:
                boxes.append((x0, y0, x1 - 1, y1 - 1))
            else:
                boxes.append((min_x, min_y, max_x, max_y))

    packed = []
    new_alpha = []
    for y in range(height):
        for x in range(width):
            i = y * width + x
            a = ap[i] / 255.0
            if a <= 0.002:
                packed.append((0, 0, 0, 0))
                new_alpha.append(0)
                continue

            tile_index = min(tile_rows - 1, y // tile_h) * tile_cols + min(tile_cols - 1, x // tile_w)
            bx0, by0, bx1, by1 = boxes[tile_index]
            bw = max(1, bx1 - bx0)
            bh = max(1, by1 - by0)
            tx = clamp01((x - bx0) / bw)
            ty = clamp01((y - by0) / bh)

            density = softp[i] / 255.0
            core = corep[i] / 255.0
            broad = broadp[i] / 255.0
            edge = edgep[i] / 255.0
            luma = base_luma[i] / 255.0

            top_light = 1.0 - smoothstep(0.24, 1.0, ty)
            underside = smoothstep(0.50, 1.0, ty)
            cavity = clamp01(core * 1.25 + broad * 0.55 - edge * 0.20)
            paint_detail = clamp01((luma - 0.45) * 1.65 + edge * 0.55)

            shadow_cut = clamp01(0.08 + underside * 0.40 + cavity * 0.18)
            local_detail = (paint_detail - 0.30) * 0.26

            right_key = clamp01(0.10 + top_light * 0.78 + tx * 0.24 + edge * 0.28 + local_detail - shadow_cut * 0.34)
            left_key = clamp01(0.10 + top_light * 0.78 + (1.0 - tx) * 0.24 + edge * 0.28 + local_detail - shadow_cut * 0.34)
            overhead = clamp01(0.12 + top_light * 0.88 + edge * 0.30 + local_detail - shadow_cut * 0.42)

            # Keep deeper interior and bottom regions meaningfully dark so the
            # material lerp reaches the blue-violet shadow tint.
            interior_shadow = clamp01(underside * density * 0.28 + cavity * density * 0.12)
            right_key = clamp01(right_key - interior_shadow)
            left_key = clamp01(left_key - interior_shadow)
            overhead = clamp01(overhead - interior_shadow * 1.15)

            r = int(round(255 * right_key))
            g = int(round(255 * left_key))
            b = int(round(255 * overhead))
            aa = int(round(255 * clamp01(a ** 0.86)))
            packed.append((r, g, b, aa))
            new_alpha.append(aa)

    out = Image.new("RGBA", (width, height))
    out.putdata(packed)
    out.save(OUT_PACKED)
    CONTENT_PACKED.parent.mkdir(parents=True, exist_ok=True)
    out.save(CONTENT_PACKED)

    preview = make_preview(out)
    preview.save(OUT_PREVIEW)
    preview.save(CONTENT_PREVIEW)

    mask_values = [(r, g, b) for r, g, b, a in packed if a > 12]
    if mask_values:
        mins = [min(v[i] for v in mask_values) for i in range(3)]
        maxs = [max(v[i] for v in mask_values) for i in range(3)]
        means = [sum(v[i] for v in mask_values) / len(mask_values) for i in range(3)]
        print(f"packed RGB min={mins} max={maxs} mean={[round(m, 2) for m in means]}")
    alpha_nonzero = [v for v in new_alpha if v > 0]
    if alpha_nonzero:
        print(f"alpha min={min(alpha_nonzero)} max={max(alpha_nonzero)} mean={round(sum(alpha_nonzero) / len(alpha_nonzero), 2)}")
    print(f"wrote {OUT_PACKED}")
    print(f"wrote {OUT_PREVIEW}")


if __name__ == "__main__":
    main()
