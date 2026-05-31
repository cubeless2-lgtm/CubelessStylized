from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal


PRESET_FILE = "cloud_plane_art_direction_presets.json"
MATERIAL_ROOT = "/Game/Cubeless/Env/Sky/Materials"
MATERIAL_PREFIX = "MI_CloudPlane_LightPacked"


def _script_dir() -> Path:
    try:
        return Path(__file__).resolve().parent
    except NameError:
        return Path.cwd()


def _linear_color(values: list[float]) -> unreal.LinearColor:
    rgba = list(values) + [1.0] * max(0, 4 - len(values))
    return unreal.LinearColor(float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3]))


def _load_presets() -> dict:
    preset_path = _script_dir() / PRESET_FILE
    with preset_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _preset_name(config: dict) -> str:
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    if args:
        return args[-1]
    return str(config.get("default_preset", "day_soft"))


def _target_material_paths() -> list[str]:
    paths = [f"{MATERIAL_ROOT}/{MATERIAL_PREFIX}_Default"]
    paths.extend(f"{MATERIAL_ROOT}/{MATERIAL_PREFIX}_Tile_{index:02d}" for index in range(8))
    return paths


def apply_preset(name: str) -> None:
    config = _load_presets()
    presets = config.get("presets", {})
    if name not in presets:
        available = ", ".join(sorted(presets.keys()))
        raise RuntimeError(f"Unknown preset '{name}'. Available presets: {available}")

    preset = presets[name]
    vector_params = [
        "LightWeights_RGB",
        "CloudLightTint",
        "CloudShadowTint",
        "TimeOfDayTint",
        "AmbientColor",
    ]
    scalar_params = [
        "Opacity",
        "CloudDensity",
        "CloudIntensity",
        "SunLightingIntensity",
        "ShadingClouds_Offset",
        "ShadingClouds_GradientWidth",
        "RimLightAmount",
        "AmbientInfluence",
        "AlphaFeather",
        "MPCSunVectorInfluence",
        "MPCCloudDensityInfluence",
        "MPCCloudCoverageInfluence",
        "MPCShadowCancelInfluence",
    ]
    changed = []

    for material_path in _target_material_paths():
        if not material_path.startswith(MATERIAL_ROOT + "/" + MATERIAL_PREFIX):
            raise RuntimeError(f"Refusing to edit non-Cubeless cloud material: {material_path}")

        material = unreal.EditorAssetLibrary.load_asset(material_path)
        if not material:
            unreal.log_warning(f"Missing material instance: {material_path}")
            continue

        for param_name in vector_params:
            if param_name in preset:
                unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                    material,
                    param_name,
                    _linear_color(preset[param_name]),
                )

        for param_name in scalar_params:
            if param_name in preset:
                unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                    material,
                    param_name,
                    float(preset[param_name]),
                )

        unreal.EditorAssetLibrary.save_asset(material_path, only_if_is_dirty=False)
        changed.append(material_path)

    unreal.log(f"Applied cloud plane art-direction preset '{name}' to {len(changed)} material instances.")
    for material_path in changed:
        unreal.log(f"  {material_path}")


if __name__ == "__main__":
    apply_preset(_preset_name(_load_presets()))
