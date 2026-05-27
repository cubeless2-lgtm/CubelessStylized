from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


@dataclass
class BlobSettings:
    count: int = 38
    radius_min: float = 0.11
    radius_max: float = 0.24
    vertical_scale_min: float = 0.68
    vertical_scale_max: float = 1.18
    weight_min: float = 0.65
    weight_max: float = 1.0
    inner_softness: float = 0.38


@dataclass
class SecondaryBlobSettings(BlobSettings):
    count: int = 48
    x_scale: float = 1.33
    y_scale: float = 0.91
    z_scale: float = 1.11
    x_offset: float = 0.17
    y_offset: float = 0.23
    z_offset: float = 0.07


@dataclass
class FbmSettings:
    frequencies: list[int] = field(default_factory=lambda: [2, 4, 8, 16])
    first_amplitude: float = 0.58
    amplitude_gain: float = 0.48


@dataclass
class NoiseLayerSettings:
    scale_xy: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    weight: float = 1.0
    bias: float = 0.0
    threshold: float = 0.0


@dataclass
class HeightSettings:
    bottom_fade_start: float = 0.02
    bottom_fade_end: float = 0.18
    top_fade_start: float = 0.78
    top_fade_end: float = 1.0
    cap_start: float = 0.56
    cap_end: float = 1.0
    cap_amount: float = 0.35
    lower_fade_start: float = 0.0
    lower_fade_end: float = 0.95
    lower_amount: float = 0.28


@dataclass
class RampSettings:
    low: float = 0.20
    high: float = 0.74
    gamma: float = 0.82


@dataclass
class OutputSettings:
    tile_size: int = 256
    slices_x: int = 16
    slices_y: int = 8
    preview_width: int = 1536
    preview_height: int = 768


@dataclass
class FormationVolumeSettings:
    notes: dict[str, str] = field(default_factory=lambda: {
        "intent": "Stylized UDS FormationVolume sheet generator.",
        "layout": "4096x2048 by default, 16x8 tiles, 128 slices, 256x256 per slice.",
        "unreal": "Import as Texture2D, set sRGB false, then create VolumeTexture from 256x256 tiles.",
    })
    seed: int = 270527
    output: OutputSettings = field(default_factory=OutputSettings)
    large_blobs: BlobSettings = field(default_factory=BlobSettings)
    secondary_blobs: SecondaryBlobSettings = field(default_factory=SecondaryBlobSettings)
    fbm: FbmSettings = field(default_factory=FbmSettings)
    soft_mass: NoiseLayerSettings = field(default_factory=lambda: NoiseLayerSettings(
        scale_xy=0.82,
        weight=0.42,
        bias=-0.48,
    ))
    breakup: NoiseLayerSettings = field(default_factory=lambda: NoiseLayerSettings(
        scale_xy=1.7,
        offset_x=0.11,
        offset_y=0.39,
        weight=0.18,
        threshold=0.72,
    ))
    erosion: NoiseLayerSettings = field(default_factory=lambda: NoiseLayerSettings(
        scale_xy=4.0,
        offset_x=0.31,
        offset_y=0.13,
        weight=0.44,
        threshold=0.53,
    ))
    height: HeightSettings = field(default_factory=HeightSettings)
    ramp: RampSettings = field(default_factory=RampSettings)
    large_blob_weight: float = 0.72
    secondary_blob_weight: float = 0.28


class NoiseCache:
    def __init__(self) -> None:
        self._grids: dict[tuple[int, int], np.ndarray] = {}

    def grid(self, freq: int, seed: int) -> np.ndarray:
        key = (freq, seed)
        if key not in self._grids:
            rng = np.random.default_rng(seed)
            self._grids[key] = rng.random((freq, freq, freq), dtype=np.float32)
        return self._grids[key]


def smootherstep(t: np.ndarray | float) -> np.ndarray:
    t = np.clip(t, 0.0, 1.0)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def smoothstep(edge0: float, edge1: float, x: np.ndarray | float) -> np.ndarray:
    if edge0 == edge1:
        return np.asarray(x >= edge1, dtype=np.float32)
    return smootherstep((x - edge0) / (edge1 - edge0))


def periodic_value_noise_3d(
    x: np.ndarray,
    y: np.ndarray,
    z: float,
    freq: int,
    seed: int,
    cache: NoiseCache,
) -> np.ndarray:
    grid = cache.grid(freq, seed)

    px = x * freq
    py = y * freq
    pz = z * freq

    x0 = np.floor(px).astype(np.int32) % freq
    y0 = np.floor(py).astype(np.int32) % freq
    z0 = int(np.floor(pz)) % freq

    x1 = (x0 + 1) % freq
    y1 = (y0 + 1) % freq
    z1 = (z0 + 1) % freq

    tx = smootherstep(px - np.floor(px))
    ty = smootherstep(py - np.floor(py))
    tz = smootherstep(np.array(pz - np.floor(pz), dtype=np.float32))

    c000 = grid[x0, y0, z0]
    c100 = grid[x1, y0, z0]
    c010 = grid[x0, y1, z0]
    c110 = grid[x1, y1, z0]
    c001 = grid[x0, y0, z1]
    c101 = grid[x1, y0, z1]
    c011 = grid[x0, y1, z1]
    c111 = grid[x1, y1, z1]

    c00 = c000 * (1.0 - tx) + c100 * tx
    c10 = c010 * (1.0 - tx) + c110 * tx
    c01 = c001 * (1.0 - tx) + c101 * tx
    c11 = c011 * (1.0 - tx) + c111 * tx
    c0 = c00 * (1.0 - ty) + c10 * ty
    c1 = c01 * (1.0 - ty) + c11 * ty
    return c0 * (1.0 - tz) + c1 * tz


def fbm(
    x: np.ndarray,
    y: np.ndarray,
    z: float,
    base_seed: int,
    settings: FbmSettings,
    cache: NoiseCache,
) -> np.ndarray:
    result = np.zeros_like(x, dtype=np.float32)
    amplitude = settings.first_amplitude
    total = 0.0

    for octave, freq in enumerate(settings.frequencies):
        n = periodic_value_noise_3d(x, y, z, freq, base_seed + octave * 101, cache)
        result += n * amplitude
        total += amplitude
        amplitude *= settings.amplitude_gain

    return result / max(total, 0.0001)


def torus_delta(a: np.ndarray, b: float) -> np.ndarray:
    d = np.abs(a - b)
    return np.minimum(d, 1.0 - d)


def make_blob_field(
    x: np.ndarray,
    y: np.ndarray,
    z: float,
    seed: int,
    settings: BlobSettings,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    centers = rng.random((settings.count, 3), dtype=np.float32)
    radii = rng.uniform(settings.radius_min, settings.radius_max, size=settings.count).astype(np.float32)
    vertical_scale = rng.uniform(
        settings.vertical_scale_min,
        settings.vertical_scale_max,
        size=settings.count,
    ).astype(np.float32)
    weight = rng.uniform(settings.weight_min, settings.weight_max, size=settings.count).astype(np.float32)

    field = np.zeros_like(x, dtype=np.float32)
    for idx in range(settings.count):
        dx = torus_delta(x, float(centers[idx, 0]))
        dy = torus_delta(y, float(centers[idx, 1]))
        dz = min(abs(z - float(centers[idx, 2])), 1.0 - abs(z - float(centers[idx, 2])))
        dist = np.sqrt(dx * dx + dy * dy + (dz / vertical_scale[idx]) ** 2)
        blob = 1.0 - smoothstep(radii[idx] * settings.inner_softness, radii[idx], dist)
        field = np.maximum(field, blob * weight[idx])

    return field


def layer_coords(
    x: np.ndarray,
    y: np.ndarray,
    layer: NoiseLayerSettings,
) -> tuple[np.ndarray, np.ndarray]:
    lx = (x * layer.scale_xy + layer.offset_x) % 1.0
    ly = (y * layer.scale_xy + layer.offset_y) % 1.0
    return lx, ly


def make_slice(
    x: np.ndarray,
    y: np.ndarray,
    z: float,
    settings: FormationVolumeSettings,
    cache: NoiseCache,
) -> np.ndarray:
    large_blobs = make_blob_field(x, y, z, settings.seed + 10, settings.large_blobs)
    sec = settings.secondary_blobs
    secondary_blobs = make_blob_field(
        (x * sec.x_scale + sec.x_offset) % 1.0,
        (y * sec.y_scale + sec.y_offset) % 1.0,
        (z * sec.z_scale + sec.z_offset) % 1.0,
        settings.seed + 45,
        sec,
    )

    soft_x, soft_y = layer_coords(x, y, settings.soft_mass)
    erosion_x, erosion_y = layer_coords(x, y, settings.erosion)
    breakup_x, breakup_y = layer_coords(x, y, settings.breakup)

    soft_mass = fbm(soft_x, soft_y, z, settings.seed + 100, settings.fbm, cache)
    breakup = fbm(breakup_x, breakup_y, z, settings.seed + 220, settings.fbm, cache)
    erosion = fbm(erosion_x, erosion_y, z, settings.seed + 350, settings.fbm, cache)

    height = settings.height
    height_base = smoothstep(height.bottom_fade_start, height.bottom_fade_end, z)
    height_base *= 1.0 - smoothstep(height.top_fade_start, height.top_fade_end, z)
    cumulus_cap = 1.0 - smoothstep(height.cap_start, height.cap_end, z) * height.cap_amount
    lower_weight = 1.0 - smoothstep(height.lower_fade_start, height.lower_fade_end, z) * height.lower_amount

    density = (
        large_blobs * settings.large_blob_weight
        + secondary_blobs * settings.secondary_blob_weight
        + (soft_mass + settings.soft_mass.bias) * settings.soft_mass.weight
        - np.maximum(erosion - settings.erosion.threshold, 0.0) * settings.erosion.weight
        - np.maximum(breakup - settings.breakup.threshold, 0.0) * settings.breakup.weight
    )
    density *= height_base * cumulus_cap * lower_weight

    ramp = settings.ramp
    density = smoothstep(ramp.low, ramp.high, density)
    density = np.power(np.clip(density, 0.0, 1.0), ramp.gamma)
    return density.astype(np.float32)


def generate(
    output: Path,
    preview: Path,
    settings: FormationVolumeSettings,
) -> dict[str, Any]:
    out = settings.output
    depth = out.slices_x * out.slices_y
    sheet_w = out.tile_size * out.slices_x
    sheet_h = out.tile_size * out.slices_y
    coords = np.linspace(0.0, 1.0, out.tile_size, endpoint=False, dtype=np.float32)
    x, y = np.meshgrid(coords, coords, indexing="xy")
    sheet = np.zeros((sheet_h, sheet_w), dtype=np.uint8)
    cache = NoiseCache()

    for slice_index in range(depth):
        z = slice_index / depth
        tile = make_slice(x, y, z, settings, cache)
        tile_u8 = np.round(tile * 255.0).astype(np.uint8)

        tile_x = slice_index % out.slices_x
        tile_y = slice_index // out.slices_x
        x0 = tile_x * out.tile_size
        y0 = tile_y * out.tile_size
        sheet[y0 : y0 + out.tile_size, x0 : x0 + out.tile_size] = tile_u8

    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(sheet, mode="L").save(output)

    preview_img = Image.fromarray(sheet, mode="L")
    preview_img.thumbnail((out.preview_width, out.preview_height), Image.Resampling.LANCZOS)
    preview.parent.mkdir(parents=True, exist_ok=True)
    preview_img.save(preview)

    return {
        "output": str(output),
        "preview": str(preview),
        "sheet_size": [sheet_w, sheet_h],
        "tile_size": out.tile_size,
        "slices": depth,
        "layout": [out.slices_x, out.slices_y],
        "min": int(sheet.min()),
        "max": int(sheet.max()),
        "mean": float(sheet.mean()),
        "nonzero_percent": float((sheet > 0).mean() * 100.0),
    }


def update_dataclass(target: Any, values: dict[str, Any]) -> Any:
    valid = {f.name for f in fields(target)}
    for key, value in values.items():
        if key == "notes":
            continue
        if key not in valid:
            raise KeyError(f"Unknown setting: {key}")
        current = getattr(target, key)
        if hasattr(current, "__dataclass_fields__"):
            update_dataclass(current, value)
        else:
            setattr(target, key, value)
    return target


def load_settings(path: Path | None) -> FormationVolumeSettings:
    settings = FormationVolumeSettings()
    if path is None:
        return settings
    data = json.loads(path.read_text(encoding="utf-8"))
    return update_dataclass(settings, data)


def save_settings_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(FormationVolumeSettings()), indent=2),
        encoding="utf-8",
    )


def apply_cli_overrides(settings: FormationVolumeSettings, args: argparse.Namespace) -> None:
    scalar_overrides = {
        "seed": ("seed",),
        "tile_size": ("output", "tile_size"),
        "slices_x": ("output", "slices_x"),
        "slices_y": ("output", "slices_y"),
        "large_blob_count": ("large_blobs", "count"),
        "large_radius_min": ("large_blobs", "radius_min"),
        "large_radius_max": ("large_blobs", "radius_max"),
        "secondary_blob_count": ("secondary_blobs", "count"),
        "soft_weight": ("soft_mass", "weight"),
        "erosion_weight": ("erosion", "weight"),
        "erosion_threshold": ("erosion", "threshold"),
        "breakup_weight": ("breakup", "weight"),
        "breakup_threshold": ("breakup", "threshold"),
        "ramp_low": ("ramp", "low"),
        "ramp_high": ("ramp", "high"),
        "ramp_gamma": ("ramp", "gamma"),
        "top_fade_start": ("height", "top_fade_start"),
        "bottom_fade_end": ("height", "bottom_fade_end"),
    }
    for arg_name, path in scalar_overrides.items():
        value = getattr(args, arg_name)
        if value is None:
            continue
        target = settings
        for part in path[:-1]:
            target = getattr(target, part)
        setattr(target, path[-1], value)

    if args.frequencies:
        settings.fbm.frequencies = [int(v.strip()) for v in args.frequencies.split(",") if v.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a stylized 2D slice sheet for an Unreal VolumeTexture.",
    )
    parser.add_argument("--config", type=Path, help="JSON settings file to load.")
    parser.add_argument("--write-config", type=Path, help="Write a default JSON settings file and exit.")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("FormationVolumeSheet_Stylized.png"))
    parser.add_argument("--preview", type=Path, default=Path(__file__).with_name("FormationVolumeSheet_Stylized_preview.png"))
    parser.add_argument("--stats", type=Path, help="Optional JSON file for generation stats.")

    parser.add_argument("--seed", type=int)
    parser.add_argument("--tile-size", type=int)
    parser.add_argument("--slices-x", type=int)
    parser.add_argument("--slices-y", type=int)
    parser.add_argument("--frequencies", help="Comma-separated fBM frequencies, for example 2,4,8,16.")

    parser.add_argument("--large-blob-count", type=int)
    parser.add_argument("--large-radius-min", type=float)
    parser.add_argument("--large-radius-max", type=float)
    parser.add_argument("--secondary-blob-count", type=int)

    parser.add_argument("--soft-weight", type=float)
    parser.add_argument("--erosion-weight", type=float)
    parser.add_argument("--erosion-threshold", type=float)
    parser.add_argument("--breakup-weight", type=float)
    parser.add_argument("--breakup-threshold", type=float)

    parser.add_argument("--ramp-low", type=float)
    parser.add_argument("--ramp-high", type=float)
    parser.add_argument("--ramp-gamma", type=float)
    parser.add_argument("--top-fade-start", type=float)
    parser.add_argument("--bottom-fade-end", type=float)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.write_config:
        save_settings_template(args.write_config)
        print(f"Wrote config template: {args.write_config}")
        return

    settings = load_settings(args.config)
    apply_cli_overrides(settings, args)
    stats = generate(args.output, args.preview, settings)

    if args.stats:
        args.stats.parent.mkdir(parents=True, exist_ok=True)
        args.stats.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
