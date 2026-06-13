# Bake SDF alpha into cloud card atlas (4x2 cells, 2048x2048).
# RGB preserved (directional light pack), A replaced by signed-distance soft alpha.
# Run: uv run --with pillow,numpy,scipy python bake_cloudcard_sdf_atlas.py
import numpy as np
from PIL import Image
from scipy import ndimage

# Note: the *_Preview_* PNG has fully-opaque alpha (beauty preview). The packed
# atlas with real alpha/density is the *_RGBA_* file.
SRC = r"C:\Git\CubelessStylized\Content\Cubeless\Env\Sky\Textures\CloudPlaneAtlas_LightPacked_UDSLike_RGBA_2048.png"
DST = r"C:\Git\CubelessStylized\SourceArt\Sky\CloudPlaneAtlas_SDF_2048.png"

COLS, ROWS = 4, 2
SOFT_PX = 48.0  # +/- soft width in pixels around the 0.5 iso line

img = Image.open(SRC).convert("RGBA")
arr = np.array(img)
H, W = arr.shape[:2]
cw, ch = W // COLS, H // ROWS
print(f"atlas {W}x{H}, cell {cw}x{ch}")

out = arr.copy()
for r in range(ROWS):
    for c in range(COLS):
        y0, x0 = r * ch, c * cw
        a = arr[y0:y0+ch, x0:x0+cw, 3].astype(np.float32) / 255.0
        inside = a >= 0.5
        if inside.any() and (~inside).any():
            d_out = ndimage.distance_transform_edt(~inside)  # dist to inside, >0 outside
            d_in = ndimage.distance_transform_edt(inside)    # dist to outside, >0 inside
            sd = d_in - d_out  # signed: + inside, - outside
        else:
            sd = np.where(inside, SOFT_PX, -SOFT_PX).astype(np.float32)
        sdf = np.clip(0.5 + sd / (2.0 * SOFT_PX), 0.0, 1.0)
        out[y0:y0+ch, x0:x0+cw, 3] = np.round(sdf * 255.0).astype(np.uint8)

Image.fromarray(out, "RGBA").save(DST)
print("saved", DST)

# Verification: histogram of cell 0 alpha — should be a smooth gradient, not binary
cell0 = out[0:ch, 0:cw, 3]
hist, _ = np.histogram(cell0, bins=16, range=(0, 256))
total = cell0.size
print("cell0 alpha 16-bin histogram (fractions):")
for i, hv in enumerate(hist):
    print(f"  [{i*16:3d}-{i*16+15:3d}] {hv/total:.4f}")
mid = hist[1:15].sum() / total
print(f"mid-range (16..239) fraction: {mid:.4f}  (binary alpha would be ~0)")
uniq = len(np.unique(cell0))
print(f"unique alpha values in cell0: {uniq}")
