"""Execute safe first-pass Niagara generation recipe steps.

This script is designed for Unreal Editor Python, but it can run outside Unreal
with --dry-run for CI/smoke checks and socket post-processing. It only performs
operations that are safe for the current API level:

- read a JSON recipe produced by niagara_generation_recipe_builder.py
- duplicate the selected primary Niagara system into /Game/_MCP_Temp/NiagaraGenerated
- optionally duplicate candidate Material Instances into the same temp folder
- write an execution report under Saved/MCP_NiagaraGeneration
- optionally bind duplicated renderer materials through UnrealMCP C++
- optionally set matching exposed User parameters through UnrealMCP C++
- optionally set or create safe RapidIteration module input overrides through UnrealMCP C++ batch APIs

It intentionally does not edit source assets, merge emitters, create Scratch Pad
graphs, or create arbitrary graph pins/dynamic inputs.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    import unreal  # type: ignore
except ImportError:
    unreal = None  # type: ignore


TEMP_ROOT = "/Game/_MCP_Temp/NiagaraGenerated"
DEFAULT_REPORT_DIR = Path("Saved/MCP_NiagaraGeneration")
PREVIEW_PLAYER_COMMAND = "open_niagara_preview_player"
UNREAL_MCP_HOST = "127.0.0.1"
UNREAL_MCP_PORT = 55557
COLOR_VALUES = {
    "red": (1.0, 0.08, 0.035, 1.0),
    "blue": (0.08, 0.35, 1.0, 1.0),
    "green": (0.08, 0.9, 0.28, 1.0),
    "purple": (0.72, 0.2, 1.0, 1.0),
    "yellow": (1.0, 0.85, 0.08, 1.0),
    "orange": (1.0, 0.38, 0.08, 1.0),
    "black": (0.02, 0.018, 0.025, 1.0),
    "white": (1.0, 1.0, 1.0, 1.0),
}
COLOR_TEXT_TERMS = {
    "blue": ("blue", "cyan", "파란", "푸른", "청색", "하늘색"),
    "red": ("red", "crimson", "scarlet", "빨간", "붉은", "적색", "빨갛"),
    "purple": ("purple", "violet", "magenta", "보라", "자주"),
    "green": ("green", "emerald", "poison", "녹색", "초록"),
    "yellow": ("yellow", "gold", "노란", "금색", "황금"),
    "orange": ("orange", "amber", "주황"),
    "black": ("black", "dark", "shadow", "검은", "검정", "어두"),
    "white": ("white", "silver", "흰", "하얀", "백색", "은색"),
}
COLOR_PARAMETER_HINTS = (
    "color",
    "colour",
    "tint",
    "emission",
    "emissive",
    "linecolor",
    "base",
)
DURATION_PARAMETER_HINTS = (
    "duration",
    "lifetime",
    "life",
    "time",
    "age",
)
MODULE_DURATION_HINTS = (
    "loopduration",
    "lifetime",
    "lifetime min",
    "lifetime max",
    "life",
    "duration",
)
SIZE_UP_TERMS = ("big", "large", "larger", "wide", "wider", "huge", "크게", "큰", "넓게", "거대")
SIZE_DOWN_TERMS = ("small", "smaller", "tiny", "narrow", "작게", "작은", "좁게")
SPAWN_UP_TERMS = ("dense", "more", "many", "lots", "burst", "많이", "많은", "빽빽", "밀도")
SPAWN_DOWN_TERMS = ("sparse", "less", "few", "적게", "성기게")
FAST_TERMS = ("fast", "faster", "quick", "rapid", "빠르게", "빠른", "급격")
SLOW_TERMS = ("slow", "slower", "느리게", "느린")
FADE_TERMS = ("transparent", "faint", "soft", "fade", "투명", "흐리", "연하게")
OPAQUE_TERMS = ("opaque", "strong", "solid", "진하게", "선명", "강하게")
DOUBLE_TERMS = ("double", "twice", "2x", "x2", "two times", "두 배", "두배", "2배")
HALF_TERMS = ("half", "0.5x", "x0.5", "절반", "반으로", "반만")
VERY_TERMS = ("very", "much", "super", "아주", "매우", "많이", "강하게")
SLIGHT_TERMS = ("slight", "slightly", "little", "조금", "약간", "살짝")
MAIN_LAYER_TERMS = ("main", "primary", "core", "center", "메인", "주", "중심", "핵심")
LINE_LAYER_TERMS = ("line", "line only", "line layer", "line emitter", "beam line", "라인", "선만", "선형")
SUPPORT_LAYER_TERMS = ("support", "sub", "secondary", "ref", "afterimage", "after image", "ghost", "보조", "서브", "잔상")
ONLY_TERMS = ("only", "just", "만", "만 ")
COLOR_USER_PARAMETER_TYPES = (
    "color",
    "linearcolor",
    "vec3",
    "vector3",
    "vec4",
    "vector4",
)
FLOAT_USER_PARAMETER_TYPES = (
    "float",
    "double",
)


def repo_root_from(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "StylizedCubeless.uproject").exists():
            return candidate
    return current


def require_unreal() -> Any:
    if unreal is None:
        raise RuntimeError("This recipe executor must run inside Unreal Editor unless --dry-run is used.")
    return unreal


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_stdout_utf8() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def package_path_from_object_path(object_path: str) -> str:
    path = object_path.strip()
    if "." in path:
        path = path.split(".", 1)[0]
    return path


def asset_name_from_path(path: str) -> str:
    package = package_path_from_object_path(path)
    return package.rsplit("/", 1)[-1]


def slug_from_target(target_system: str) -> str:
    package = package_path_from_object_path(target_system)
    parent = package.rsplit("/", 1)[0]
    slug = parent.rsplit("/", 1)[-1]
    return sanitize_asset_name(slug or asset_name_from_path(package))


def sanitize_asset_name(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    return clean or "GeneratedNiagara"


def ensure_temp_path(path: str) -> None:
    package = package_path_from_object_path(path)
    if not package.startswith(TEMP_ROOT + "/"):
        raise ValueError(f"Refusing to write outside {TEMP_ROOT}: {path}")


def ensure_unreal_directory(directory: str) -> None:
    ue = require_unreal()
    ensure_temp_path(directory + "/_Guard")
    if not ue.EditorAssetLibrary.does_directory_exist(directory):
        ue.EditorAssetLibrary.make_directory(directory)


def delete_asset_if_needed(asset_path: str, overwrite: bool) -> bool:
    ue = require_unreal()
    if not ue.EditorAssetLibrary.does_asset_exist(asset_path):
        return False
    if not overwrite:
        raise RuntimeError(f"Target asset already exists. Pass --overwrite to replace it: {asset_path}")
    return bool(ue.EditorAssetLibrary.delete_asset(asset_path))


def duplicate_asset(source_path: str, target_path: str, overwrite: bool, save_assets: bool) -> dict[str, Any]:
    ue = require_unreal()
    ensure_temp_path(target_path)
    source_package = package_path_from_object_path(source_path)
    target_package = package_path_from_object_path(target_path)
    target_dir = target_package.rsplit("/", 1)[0]
    ensure_unreal_directory(target_dir)

    if not ue.EditorAssetLibrary.does_asset_exist(source_package):
        raise RuntimeError(f"Source asset does not exist: {source_path}")

    deleted_existing = delete_asset_if_needed(target_package, overwrite)
    duplicated_asset = ue.EditorAssetLibrary.duplicate_asset(source_package, target_package)
    if duplicated_asset is None:
        raise RuntimeError(f"Failed to duplicate {source_path} to {target_package}")

    saved = False
    if save_assets:
        saved = bool(ue.EditorAssetLibrary.save_loaded_asset(duplicated_asset, False))

    object_path = duplicated_asset.get_path_name()
    return {
        "source": source_path,
        "target": object_path,
        "target_package": target_package,
        "deleted_existing": deleted_existing,
        "saved": saved,
        "class": duplicated_asset.get_class().get_path_name() if duplicated_asset.get_class() else "",
    }


def color_from_recipe(recipe: dict[str, Any]) -> tuple[str, tuple[float, float, float, float]] | None:
    colors = recipe.get("parsed_intent", {}).get("colors", [])
    if not colors:
        return None
    color_name = colors[0]
    value = COLOR_VALUES.get(color_name)
    if value is None:
        return None
    return color_name, value


def color_from_text(text: str) -> tuple[str, tuple[float, float, float, float]] | None:
    for color_name, terms in COLOR_TEXT_TERMS.items():
        if contains_any_text(text, terms):
            value = COLOR_VALUES.get(color_name)
            if value is not None:
                return color_name, value
    return None


def duration_from_text(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:seconds?|secs?|s|초)", text, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def is_color_parameter(parameter_name: str) -> bool:
    lowered = parameter_name.casefold().replace("_", "")
    return any(hint in lowered for hint in COLOR_PARAMETER_HINTS)


def is_duration_parameter(parameter_name: str) -> bool:
    lowered = parameter_name.casefold().replace("_", "")
    return any(hint in lowered for hint in DURATION_PARAMETER_HINTS)


def normalized_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def contains_any_text(value: str, terms: tuple[str, ...]) -> bool:
    lowered = value.casefold()
    return any(term.casefold() in lowered for term in terms)


def detect_layer_targets(prompt: str) -> list[str]:
    targets: list[str] = []
    if contains_any_text(prompt, LINE_LAYER_TERMS):
        targets.append("line")
    if contains_any_text(prompt, SUPPORT_LAYER_TERMS):
        targets.append("support")
    if contains_any_text(prompt, MAIN_LAYER_TERMS):
        targets.append("main")
    return targets


def emitter_layer_tags(emitter_name: str) -> set[str]:
    lowered = normalized_name(emitter_name)
    tags: set[str] = set()
    if "line" in lowered or "beam" in lowered:
        tags.add("line")
    if "ref" in lowered or "sub" in lowered or "support" in lowered or "afterimage" in lowered:
        tags.add("support")
    if "trail" in lowered or "sword" in lowered:
        tags.add("trail")
    if "spark" in lowered:
        tags.add("spark")
    if "smoke" in lowered:
        tags.add("smoke")
    if "line" not in tags and "support" not in tags:
        tags.add("main")
    return tags


def row_matches_layer_targets(row: dict[str, Any], module_intent: dict[str, Any]) -> bool:
    targets = module_intent.get("target_layers", [])
    if not targets:
        return True
    tags = emitter_layer_tags(str(row.get("emitter_name", "")))
    return bool(tags.intersection(set(targets)))


def is_module_color_input(input_name: str) -> bool:
    lowered = normalized_name(input_name)
    return any(hint in lowered for hint in ("color", "colour", "tint", "emissive", "scalergb", "scalergba"))


def is_module_duration_input(input_name: str) -> bool:
    lowered = normalized_name(input_name)
    return any(normalized_name(hint) in lowered for hint in MODULE_DURATION_HINTS)


def is_module_size_input(input_name: str) -> bool:
    lowered = normalized_name(input_name)
    if any(hint in lowered for hint in ("curve", "color", "alpha", "spawn", "probability")):
        return False
    return any(hint in lowered for hint in ("scalefactor", "meshscale", "spritesize", "uniformspritesize", "radius", "width", "size"))


def is_module_spawn_input(input_name: str) -> bool:
    lowered = normalized_name(input_name)
    return any(hint in lowered for hint in ("spawncount", "spawnrate", "spawnprobability"))


def is_module_velocity_input(input_name: str) -> bool:
    lowered = normalized_name(input_name)
    return "velocity" in lowered or "speed" in lowered


def is_module_opacity_input(input_name: str) -> bool:
    lowered = normalized_name(input_name)
    return any(hint in lowered for hint in ("alpha", "opacity"))


def normalized_type_name(type_name: str) -> str:
    return type_name.casefold().replace(" ", "").replace("_", "")


def is_color_user_parameter(parameter: dict[str, Any]) -> bool:
    if not is_color_parameter(str(parameter.get("name", ""))):
        return False
    type_name = normalized_type_name(str(parameter.get("type", "")))
    return any(candidate in type_name for candidate in COLOR_USER_PARAMETER_TYPES)


def is_float_user_parameter(parameter: dict[str, Any]) -> bool:
    type_name = normalized_type_name(str(parameter.get("type", "")))
    return any(candidate == type_name or candidate in type_name for candidate in FLOAT_USER_PARAMETER_TYPES)


def target_value_for_user_parameter(
    parameter: dict[str, Any],
    material_color: tuple[str, tuple[float, float, float, float]] | None,
    duration: float | None,
) -> tuple[str, Any] | None:
    if not parameter.get("settable_by_mcp", False):
        return None

    if material_color is not None and is_color_user_parameter(parameter):
        rgba = list(material_color[1])
        type_name = normalized_type_name(str(parameter.get("type", "")))
        if "vec3" in type_name or "vector3" in type_name:
            return "parsed_color", rgba[:3]
        return "parsed_color", rgba

    if duration is not None and is_duration_parameter(str(parameter.get("name", ""))) and is_float_user_parameter(parameter):
        return "parsed_duration", float(duration)

    return None


def value_from_rapid_iteration(resolved_input: dict[str, Any]) -> Any:
    rapid_parameter = resolved_input.get("rapid_iteration_parameter", {})
    if not rapid_parameter.get("has_value", False):
        return None
    return rapid_parameter.get("value")


def module_input_has_rapid_iteration_value(resolved_input: dict[str, Any]) -> bool:
    rapid_parameter = resolved_input.get("rapid_iteration_parameter", {})
    return bool(rapid_parameter.get("has_value", False))


def module_input_type_kind(type_name: str) -> str:
    normalized = normalized_type_name(type_name)
    if "curve" in normalized or "커브" in normalized:
        return "unsupported"
    if any(token in normalized for token in ("linearcolor", "color", "colour", "선형컬러")):
        return "color"
    if any(token in normalized for token in ("vector4", "vec4", "float4")):
        return "vec4"
    if any(token in normalized for token in ("vector3", "vec3", "position", "float3", "vector")):
        return "vec3"
    if any(token in normalized for token in ("vector2", "vec2", "float2")):
        return "vec2"
    if any(token in normalized for token in ("int32", "integer", "int")):
        return "int"
    if any(token in normalized for token in ("float", "double", "플로트")):
        return "float"
    if any(token in normalized for token in ("bool", "boolean", "부울")):
        return "bool"
    return "unknown"


def can_create_missing_module_input_override(row: dict[str, Any]) -> bool:
    module_name = str(row.get("module_name", ""))
    supported_modules = {
        "EmitterState",
        "ParticleState",
        "ScaleColor",
        "SolveForcesAndVelocity",
    }
    if module_name not in supported_modules:
        return False
    return module_input_type_kind(str(row.get("input_type", ""))) not in {"unknown", "unsupported", "bool"}


def seed_vector_value(kind: str, scalar: float) -> Any:
    if kind == "vec2":
        return [scalar, scalar]
    if kind == "vec3":
        return [scalar, scalar, scalar]
    if kind == "vec4":
        return [scalar, scalar, scalar, scalar]
    if kind == "float":
        return scalar
    if kind == "int":
        return max(1, int(round(scalar)))
    return None


def seed_value_for_missing_module_input(row: dict[str, Any], module_intent: dict[str, Any]) -> tuple[str, Any] | None:
    if not can_create_missing_module_input_override(row):
        return None

    input_name = str(row.get("input_name", ""))
    kind = module_input_type_kind(str(row.get("input_type", "")))

    material_color = module_intent.get("color")
    if material_color is not None and is_module_color_input(input_name):
        rgba = list(material_color[1])
        if kind == "color" or kind == "vec4":
            return "parsed_color_created_override", rgba
        if kind == "vec3":
            return "parsed_color_created_override", rgba[:3]

    duration = module_intent.get("duration")
    if duration is not None and is_module_duration_input(input_name) and kind in {"float", "int"}:
        value = float(duration)
        return "parsed_duration_created_override", max(1, int(round(value))) if kind == "int" else value

    size_multiplier = module_intent.get("size_multiplier")
    if size_multiplier is not None and is_module_size_input(input_name):
        value = seed_vector_value(kind, float(size_multiplier))
        if value is not None:
            return "parsed_size_multiplier_created_override", value

    spawn_multiplier = module_intent.get("spawn_multiplier")
    if spawn_multiplier is not None and is_module_spawn_input(input_name):
        if "spawnprobability" in normalized_name(input_name):
            value = seed_vector_value(kind, max(0.0, min(1.0, float(spawn_multiplier))))
        else:
            value = seed_vector_value(kind, float(spawn_multiplier))
        if value is not None:
            return "parsed_spawn_multiplier_created_override", value

    velocity_multiplier = module_intent.get("velocity_multiplier")
    if velocity_multiplier is not None and is_module_velocity_input(input_name):
        value = seed_vector_value(kind, float(velocity_multiplier))
        if value is not None:
            return "parsed_velocity_multiplier_created_override", value

    opacity_multiplier = module_intent.get("opacity_multiplier")
    if opacity_multiplier is not None and is_module_opacity_input(input_name):
        value = seed_vector_value(kind, max(0.0, min(1.0, float(opacity_multiplier))))
        if value is not None:
            return "parsed_opacity_multiplier_created_override", value

    return None


def scaled_value(current_value: Any, multiplier: float) -> Any:
    if isinstance(current_value, bool):
        return None
    if isinstance(current_value, (int, float)):
        return current_value * multiplier
    if isinstance(current_value, list) and current_value:
        result = []
        for item in current_value:
            if not isinstance(item, (int, float)) or isinstance(item, bool):
                return None
            result.append(item * multiplier)
        return result
    return None


def clamp01_value(current_value: Any, multiplier: float) -> Any:
    scaled = scaled_value(current_value, multiplier)
    if isinstance(scaled, (int, float)):
        return max(0.0, min(1.0, float(scaled)))
    if isinstance(scaled, list):
        return [max(0.0, min(1.0, float(item))) for item in scaled]
    return None


def values_nearly_equal(left: Any, right: Any) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)) < 0.0001
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        return all(values_nearly_equal(a, b) for a, b in zip(left, right))
    return left == right


def intent_value(source: str, current_value: Any, new_value: Any) -> tuple[str, Any] | None:
    if new_value is None or values_nearly_equal(current_value, new_value):
        return None
    return source, new_value


def prompt_multiplier(
    prompt: str,
    up_terms: tuple[str, ...],
    down_terms: tuple[str, ...],
    default_up: float,
    default_down: float,
) -> float | None:
    wants_up = contains_any_text(prompt, up_terms)
    wants_down = contains_any_text(prompt, down_terms)
    if not wants_up and not wants_down:
        return None

    if wants_up:
        if contains_any_text(prompt, DOUBLE_TERMS):
            return 2.0
        if contains_any_text(prompt, VERY_TERMS):
            return max(default_up, 1.8)
        if contains_any_text(prompt, SLIGHT_TERMS):
            return 1.2
        return default_up

    if contains_any_text(prompt, HALF_TERMS):
        return 0.5
    if contains_any_text(prompt, VERY_TERMS):
        return min(default_down, 0.45)
    if contains_any_text(prompt, SLIGHT_TERMS):
        return 0.85
    return default_down


def split_prompt_clauses(prompt: str) -> list[str]:
    normalized = re.sub(r"\s+(?:and|then|그리고|그다음|다음은)\s+", ",", prompt, flags=re.IGNORECASE)
    parts = re.split(r"[,;/\n]+", normalized)
    return [part.strip() for part in parts if part.strip()]


def has_actionable_module_intent(intent: dict[str, Any]) -> bool:
    return any(
        intent.get(key) is not None and intent.get(key) not in ("", [])
        for key in (
            "color",
            "duration",
            "size_multiplier",
            "spawn_multiplier",
            "velocity_multiplier",
            "opacity_multiplier",
        )
    )


def module_intent_from_text(text: str, fallback_color: tuple[str, tuple[float, float, float, float]] | None, fallback_duration: float | None) -> dict[str, Any]:
    intent: dict[str, Any] = {
        "color": color_from_text(text),
        "duration": duration_from_text(text),
        "size_multiplier": prompt_multiplier(text, SIZE_UP_TERMS, SIZE_DOWN_TERMS, 1.5, 0.65),
        "spawn_multiplier": prompt_multiplier(text, SPAWN_UP_TERMS, SPAWN_DOWN_TERMS, 1.75, 0.55),
        "velocity_multiplier": prompt_multiplier(text, FAST_TERMS, SLOW_TERMS, 1.5, 0.65),
        "opacity_multiplier": prompt_multiplier(text, OPAQUE_TERMS, FADE_TERMS, 1.35, 0.55),
        "target_layers": detect_layer_targets(text),
        "source_text": text,
    }
    if intent["color"] is None and fallback_color is not None and contains_any_text(text, ("color", "색", "색상")):
        intent["color"] = fallback_color
    if intent["duration"] is None and fallback_duration is not None and contains_any_text(text, DURATION_PARAMETER_HINTS):
        intent["duration"] = fallback_duration
    return intent


def module_bindings_from_prompt(prompt: str, fallback_color: tuple[str, tuple[float, float, float, float]] | None, fallback_duration: float | None) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for clause in split_prompt_clauses(prompt):
        intent = module_intent_from_text(clause, fallback_color, fallback_duration)
        if intent.get("target_layers") and has_actionable_module_intent(intent):
            bindings.append(intent)
    return bindings


def binding_for_row(row: dict[str, Any], module_intent: dict[str, Any]) -> dict[str, Any] | None:
    bindings = module_intent.get("bindings", [])
    if not bindings:
        return module_intent if row_matches_layer_targets(row, module_intent) else None

    tags = emitter_layer_tags(str(row.get("emitter_name", "")))
    for binding in bindings:
        target_layers = set(binding.get("target_layers", []))
        if tags.intersection(target_layers):
            return binding
    return None


def module_intent_from_recipe(recipe: dict[str, Any]) -> dict[str, Any]:
    prompt = str(recipe.get("request", ""))
    fallback_color = color_from_recipe(recipe)
    fallback_duration = recipe.get("parsed_intent", {}).get("duration_seconds")
    intent: dict[str, Any] = {
        "color": fallback_color,
        "duration": fallback_duration,
        "size_multiplier": None,
        "spawn_multiplier": None,
        "velocity_multiplier": None,
        "opacity_multiplier": None,
        "target_layers": detect_layer_targets(prompt),
        "bindings": module_bindings_from_prompt(prompt, fallback_color, fallback_duration),
    }
    intent["size_multiplier"] = prompt_multiplier(prompt, SIZE_UP_TERMS, SIZE_DOWN_TERMS, 1.5, 0.65)
    intent["spawn_multiplier"] = prompt_multiplier(prompt, SPAWN_UP_TERMS, SPAWN_DOWN_TERMS, 1.75, 0.55)
    intent["velocity_multiplier"] = prompt_multiplier(prompt, FAST_TERMS, SLOW_TERMS, 1.5, 0.65)
    intent["opacity_multiplier"] = prompt_multiplier(prompt, OPAQUE_TERMS, FADE_TERMS, 1.35, 0.55)
    return intent


def target_value_for_module_input(
    row: dict[str, Any],
    module_intent: dict[str, Any],
) -> tuple[str, Any, str] | None:
    resolved_input = row["resolved_input"]
    variable = resolved_input.get("variable", {})
    input_name = str(variable.get("name", ""))
    current_value = value_from_rapid_iteration(resolved_input)
    if current_value is None:
        seeded_value = seed_value_for_missing_module_input(row, module_intent)
        if seeded_value is None:
            return None
        source, value = seeded_value
        return source, value, "create_override"

    material_color = module_intent.get("color")
    if material_color is not None and is_module_color_input(input_name):
        rgba = list(material_color[1])
        if isinstance(current_value, list) and len(current_value) == 3:
            result = intent_value("parsed_color", current_value, rgba[:3])
            return (*result, "set_existing") if result else None
        if isinstance(current_value, list) and len(current_value) == 4:
            result = intent_value("parsed_color", current_value, rgba)
            return (*result, "set_existing") if result else None
        result = intent_value("parsed_color", current_value, rgba)
        return (*result, "set_existing") if result else None

    duration = module_intent.get("duration")
    if duration is not None and is_module_duration_input(input_name):
        if isinstance(current_value, (int, float)) and not isinstance(current_value, bool):
            result = intent_value("parsed_duration", current_value, float(duration))
            return (*result, "set_existing") if result else None

    size_multiplier = module_intent.get("size_multiplier")
    if size_multiplier is not None and is_module_size_input(input_name):
        value = scaled_value(current_value, float(size_multiplier))
        if value is not None:
            result = intent_value("parsed_size_multiplier", current_value, value)
            return (*result, "set_existing") if result else None

    spawn_multiplier = module_intent.get("spawn_multiplier")
    if spawn_multiplier is not None and is_module_spawn_input(input_name):
        if "spawnprobability" in normalized_name(input_name):
            value = clamp01_value(current_value, float(spawn_multiplier))
        else:
            value = scaled_value(current_value, float(spawn_multiplier))
        if isinstance(current_value, int) and not isinstance(current_value, bool) and "spawnprobability" not in normalized_name(input_name):
            value = max(1, int(round(float(value))))
        if value is not None:
            result = intent_value("parsed_spawn_multiplier", current_value, value)
            return (*result, "set_existing") if result else None

    velocity_multiplier = module_intent.get("velocity_multiplier")
    if velocity_multiplier is not None and is_module_velocity_input(input_name):
        value = scaled_value(current_value, float(velocity_multiplier))
        if value is not None:
            result = intent_value("parsed_velocity_multiplier", current_value, value)
            return (*result, "set_existing") if result else None

    opacity_multiplier = module_intent.get("opacity_multiplier")
    if opacity_multiplier is not None and is_module_opacity_input(input_name):
        value = clamp01_value(current_value, float(opacity_multiplier))
        if value is not None:
            result = intent_value("parsed_opacity_multiplier", current_value, value)
            return (*result, "set_existing") if result else None

    return None


def iter_resolved_module_inputs(module_input_result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for emitter in module_input_result.get("emitters", []):
        emitter_name = str(emitter.get("name", ""))
        emitter_index = int(emitter.get("emitter_index", -1))
        for module in emitter.get("modules", []):
            module_name = str(module.get("function_name", ""))
            module_index = int(module.get("node_index", -1))
            module_guid = str(module.get("node_guid", ""))
            for resolved_input in module.get("resolved_stack_inputs", []):
                variable = resolved_input.get("variable", {})
                rows.append(
                    {
                        "emitter_name": emitter_name,
                        "emitter_index": emitter_index,
                        "module_name": module_name,
                        "module_index": module_index,
                        "module_node_guid": module_guid,
                        "input_name": str(variable.get("name", "")),
                        "input_type": str(variable.get("type", "")),
                        "resolved_input": resolved_input,
                    }
                )
    return rows


def summarize_module_input_applications(applications: list[dict[str, Any]]) -> dict[str, Any]:
    by_intent: dict[str, int] = {}
    by_input: dict[str, int] = {}
    by_operation: dict[str, int] = {}
    created_missing_override = 0
    overwritten_existing = 0
    edited_existing = 0
    failed = 0
    for application in applications:
        if not application.get("success", False):
            failed += 1
        intent_source = str(application.get("intent_source", "unknown"))
        input_name = str(application.get("input_name", "unknown"))
        operation = str(application.get("operation", "unknown"))
        by_intent[intent_source] = by_intent.get(intent_source, 0) + 1
        by_input[input_name] = by_input.get(input_name, 0) + 1
        by_operation[operation] = by_operation.get(operation, 0) + 1
        if application.get("created_missing_override", False):
            created_missing_override += 1
        if application.get("overwrote_existing", False):
            overwritten_existing += 1
        if application.get("had_rapid_iteration_value", False):
            edited_existing += 1
    return {
        "total": len(applications),
        "failed": failed,
        "succeeded": len(applications) - failed,
        "created_missing_override": created_missing_override,
        "overwritten_existing": overwritten_existing,
        "edited_existing": edited_existing,
        "by_operation": by_operation,
        "by_intent": by_intent,
        "by_input": by_input,
    }


def summarize_module_input_batch_response(batch_response: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(batch_response, dict):
        return {}
    result = batch_response.get("result", {})
    if not isinstance(result, dict):
        return {}
    return {
        "success": bool(result.get("success", False)),
        "requested_count": int(result.get("requested_count", 0) or 0),
        "processed_count": int(result.get("processed_count", 0) or 0),
        "applied_count": int(result.get("applied_count", 0) or 0),
        "failed_count": int(result.get("failed_count", 0) or 0),
        "continue_on_error": bool(result.get("continue_on_error", False)),
        "saved": bool(result.get("saved", False)),
        "write_scope": result.get("write_scope", ""),
    }


def apply_color_to_material_instance(material_object_path: str, color: tuple[str, tuple[float, float, float, float]], save_assets: bool) -> dict[str, Any]:
    ue = require_unreal()
    color_name, rgba = color
    material = ue.EditorAssetLibrary.load_asset(material_object_path)
    if material is None:
        return {
            "material": material_object_path,
            "color": color_name,
            "success": False,
            "reason": "material_load_failed",
            "applied_parameters": [],
        }

    class_name = material.get_class().get_name() if material.get_class() else ""
    if class_name != "MaterialInstanceConstant":
        return {
            "material": material_object_path,
            "color": color_name,
            "success": False,
            "reason": f"unsupported_material_class:{class_name}",
            "applied_parameters": [],
        }

    vector_parameters = ue.MaterialEditingLibrary.get_vector_parameter_names(material)
    target_parameters = [param for param in vector_parameters if is_color_parameter(str(param))]
    linear_color = ue.LinearColor(float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3]))
    applied = []
    for parameter in target_parameters:
        ue.MaterialEditingLibrary.set_material_instance_vector_parameter_value(material, parameter, linear_color)
        applied.append(str(parameter))

    if applied:
        ue.MaterialEditingLibrary.update_material_instance(material)
        if save_assets:
            ue.EditorAssetLibrary.save_loaded_asset(material, False)

    return {
        "material": material_object_path,
        "color": color_name,
        "success": bool(applied),
        "reason": "" if applied else "no_safe_vector_color_parameter_found",
        "applied_parameters": applied,
    }


def material_target_path(recipe_slug: str, source_material: str) -> str:
    source_name = sanitize_asset_name(asset_name_from_path(source_material))
    prefix = "MI_" if not source_name.startswith("MI_") else ""
    return f"{TEMP_ROOT}/{recipe_slug}/Materials/{prefix}{recipe_slug}_{source_name}"


def object_path_from_package_path(package_path: str) -> str:
    package = package_path_from_object_path(package_path)
    name = asset_name_from_path(package)
    return f"{package}.{name}"


def send_unreal_mcp_command(command: str, params: dict[str, Any], host: str, port: int, timeout: float = 60.0) -> dict[str, Any]:
    payload = {"type": command, "params": params}
    with socket.create_connection((host, port), timeout=10.0) as sock:
        sock.settimeout(timeout)
        sock.sendall(json.dumps(payload).encode("utf-8"))
        chunks: list[bytes] = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            try:
                return json.loads(b"".join(chunks).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
    raise RuntimeError(f"Unreal MCP command returned no complete JSON response: {command}")


def send_unreal_mcp_command_with_retry(
    command: str,
    params: dict[str, Any],
    host: str,
    port: int,
    timeout: float = 60.0,
    attempts: int = 2,
    retry_delay_seconds: float = 1.0,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(max(1, attempts)):
        try:
            return send_unreal_mcp_command(command, params, host, port, timeout)
        except (TimeoutError, socket.timeout, OSError, RuntimeError) as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                break
            time.sleep(retry_delay_seconds)
    raise RuntimeError(f"Unreal MCP command failed after {attempts} attempts: {command}: {last_error}")


def inspect_dirty_packages_via_socket(host: str, port: int) -> dict[str, Any]:
    code = r'''
import json
import unreal

utils = unreal.EditorLoadingAndSavingUtils
dirty_content = [package.get_name() for package in utils.get_dirty_content_packages()]
dirty_maps = [package.get_name() for package in utils.get_dirty_map_packages()]
result = {
    "success": True,
    "dirty_content_count": len(dirty_content),
    "dirty_map_count": len(dirty_maps),
    "dirty_content_packages": dirty_content,
    "dirty_map_packages": dirty_maps,
}
print("MCP_DIRTY_PACKAGES_JSON:" + json.dumps(result, ensure_ascii=False))
'''
    try:
        response = send_unreal_mcp_command(
            "execute_python",
            {"code": code, "mode": "ExecuteFile", "defer_to_ticker": True},
            host,
            port,
            timeout=125.0,
        )
        if response.get("status") != "success":
            raise RuntimeError(f"execute_python failed: {response}")
        result = unwrap_unreal_mcp_result(response)
        for entry in result.get("logs", []):
            output = str(entry.get("output", ""))
            marker = "MCP_DIRTY_PACKAGES_JSON:"
            if marker in output:
                payload = output.split(marker, 1)[1].strip()
                parsed = json.loads(payload)
                parsed["status"] = "pass" if parsed.get("dirty_content_count", 0) == 0 and parsed.get("dirty_map_count", 0) == 0 else "fail"
                return parsed
        raise RuntimeError("execute_python completed but no dirty package JSON marker was found")
    except Exception as exc:
        return {
            "success": False,
            "status": "unavailable",
            "error": str(exc),
            "dirty_content_count": None,
            "dirty_map_count": None,
            "dirty_content_packages": [],
            "dirty_map_packages": [],
        }


def material_binding_lookup(recipe: dict[str, Any], recipe_slug: str) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for material in recipe.get("material_plan", []):
        if material.get("operation") != "duplicate_material_instance":
            continue
        source_material = material.get("source_material", "")
        if not source_material:
            continue
        lookup[object_path_from_package_path(source_material)] = object_path_from_package_path(
            material_target_path(recipe_slug, source_material)
        )
    return lookup


def bind_renderer_materials_via_socket(
    recipe: dict[str, Any],
    recipe_path: Path,
    host: str,
    port: int,
    save_assets: bool,
) -> dict[str, Any]:
    generation_plan = recipe.get("generation_plan", {})
    target_system = generation_plan.get("target_system", "")
    ensure_temp_path(target_system)
    recipe_slug = slug_from_target(target_system)
    lookup = material_binding_lookup(recipe, recipe_slug)

    inspect_response = send_unreal_mcp_command(
        "inspect_niagara_renderers",
        {"system_path": object_path_from_package_path(target_system)},
        host,
        port,
    )
    if inspect_response.get("status") != "success":
        raise RuntimeError(f"Failed to inspect Niagara renderers: {inspect_response}")

    renderers = inspect_response.get("result", {}).get("renderers", [])
    bindings = []
    skipped = []
    for renderer in renderers:
        source_candidates = []
        primary_material = renderer.get("primary_material", "")
        if primary_material:
            source_candidates.append(primary_material)
        source_candidates.extend(renderer.get("used_materials", []))

        target_material = ""
        source_material = ""
        for candidate in source_candidates:
            if candidate in lookup:
                source_material = candidate
                target_material = lookup[candidate]
                break

        if not target_material:
            skipped.append(
                {
                    "emitter_index": renderer.get("emitter_index"),
                    "renderer_index": renderer.get("renderer_index"),
                    "renderer_class": renderer.get("renderer_class", ""),
                    "reason": "no_duplicated_material_match",
                    "source_candidates": source_candidates,
                }
            )
            continue

        set_response = send_unreal_mcp_command(
            "set_niagara_renderer_material",
            {
                "system_path": object_path_from_package_path(target_system),
                "material_path": target_material,
                "emitter_index": int(renderer.get("emitter_index", -1)),
                "renderer_index": int(renderer.get("renderer_index", -1)),
                "save": save_assets,
            },
            host,
            port,
        )
        bindings.append(
            {
                "success": set_response.get("status") == "success",
                "source_material": source_material,
                "target_material": target_material,
                "response": set_response,
            }
        )

    return {
        "success": all(binding.get("success") for binding in bindings),
        "mode": "socket_bind_renderer_materials",
        "recipe_path": str(recipe_path),
        "request": recipe.get("request", ""),
        "target_system": object_path_from_package_path(target_system),
        "binding_count": len(bindings),
        "bindings": bindings,
        "skipped_renderers": skipped,
        "material_lookup_count": len(lookup),
        "source_policy": recipe.get("write_scope", {}).get("source_policy", ""),
    }


def apply_user_parameters_via_socket(
    recipe: dict[str, Any],
    recipe_path: Path,
    host: str,
    port: int,
    save_assets: bool,
) -> dict[str, Any]:
    generation_plan = recipe.get("generation_plan", {})
    target_system = generation_plan.get("target_system", "")
    ensure_temp_path(target_system)
    target_object_path = object_path_from_package_path(target_system)
    module_intent = module_intent_from_recipe(recipe)
    material_color = module_intent.get("color")
    duration = module_intent.get("duration")

    inspect_response = send_unreal_mcp_command(
        "inspect_niagara_user_parameters",
        {"system_path": target_object_path},
        host,
        port,
    )
    if inspect_response.get("status") != "success":
        raise RuntimeError(f"Failed to inspect Niagara user parameters: {inspect_response}")

    parameters = inspect_response.get("result", {}).get("parameters", [])
    applications = []
    skipped = []
    used_parameters: set[str] = set()
    for parameter in parameters:
        name = str(parameter.get("name", ""))
        target_value = target_value_for_user_parameter(parameter, material_color, duration)
        if target_value is None:
            skipped.append(
                {
                    "parameter_name": name,
                    "type": parameter.get("type", ""),
                    "reason": "no_safe_prompt_intent_match_or_unsupported_type",
                }
            )
            continue

        source, value = target_value
        if name in used_parameters:
            skipped.append(
                {
                    "parameter_name": name,
                    "type": parameter.get("type", ""),
                    "reason": "already_set",
                }
            )
            continue
        used_parameters.add(name)

        set_response = send_unreal_mcp_command(
            "set_niagara_user_parameter",
            {
                "system_path": target_object_path,
                "parameter_name": name,
                "value": value,
                "save": save_assets,
            },
            host,
            port,
        )
        applications.append(
            {
                "success": set_response.get("status") == "success",
                "parameter_name": name,
                "type": parameter.get("type", ""),
                "intent_source": source,
                "value": value,
                "response": set_response,
            }
        )

    return {
        "success": all(item.get("success") for item in applications),
        "mode": "socket_apply_user_parameters",
        "recipe_path": str(recipe_path),
        "request": recipe.get("request", ""),
        "target_system": target_object_path,
        "parameter_count": inspect_response.get("result", {}).get("parameter_count", len(parameters)),
        "settable_count": inspect_response.get("result", {}).get("settable_count", 0),
        "application_count": len(applications),
        "application_summary": summarize_module_input_applications(applications),
        "applications": applications,
        "skipped_parameters": skipped,
        "unapplied_user_parameter_intent": {
            "color": material_color[0] if material_color else "",
            "duration_seconds": duration,
            "reason": "" if applications else "No existing exposed User.* parameter matched safe name/type hints.",
        },
        "source_policy": recipe.get("write_scope", {}).get("source_policy", ""),
    }


def apply_module_inputs_via_socket(
    recipe: dict[str, Any],
    recipe_path: Path,
    host: str,
    port: int,
    save_assets: bool,
) -> dict[str, Any]:
    generation_plan = recipe.get("generation_plan", {})
    target_system = generation_plan.get("target_system", "")
    ensure_temp_path(target_system)
    target_object_path = object_path_from_package_path(target_system)
    module_intent = module_intent_from_recipe(recipe)
    material_color = module_intent.get("color")
    duration = module_intent.get("duration")

    inspect_response = send_unreal_mcp_command(
        "inspect_niagara_module_inputs",
        {
            "system_path": target_object_path,
            "include_resolved_stack_inputs": True,
            "max_modules": 120,
            "max_candidates_per_module": 8,
            "max_resolved_inputs_per_module": 16,
            "max_top_candidates": 32,
        },
        host,
        port,
        timeout=180.0,
    )
    if inspect_response.get("status") != "success":
        raise RuntimeError(f"Failed to inspect Niagara module inputs: {inspect_response}")

    planned_applications = []
    batch_edits = []
    skipped = []
    used_targets: set[str] = set()
    for row in iter_resolved_module_inputs(inspect_response.get("result", {})):
        row_intent = binding_for_row(row, module_intent)
        if row_intent is None:
            skipped.append(
                {
                    "emitter_name": row["emitter_name"],
                    "module_name": row["module_name"],
                    "input_name": row["input_name"],
                    "input_type": row["input_type"],
                    "reason": "outside_requested_layer_target_or_binding",
                    "emitter_layer_tags": sorted(emitter_layer_tags(row["emitter_name"])),
                    "requested_layer_targets": module_intent.get("target_layers", []),
                    "bindings": [
                        {
                            "target_layers": binding.get("target_layers", []),
                            "source_text": binding.get("source_text", ""),
                        }
                        for binding in module_intent.get("bindings", [])
                    ],
                }
            )
            continue

        target_value = target_value_for_module_input(row, row_intent)
        target_key = "|".join(
            [
                row["emitter_name"],
                row["module_node_guid"],
                row["input_name"],
            ]
        )
        if target_value is None:
            skipped.append(
                {
                    "emitter_name": row["emitter_name"],
                    "module_name": row["module_name"],
                    "input_name": row["input_name"],
                    "input_type": row["input_type"],
                    "reason": "no_safe_prompt_intent_match_or_unsupported_missing_override_type",
                    "value_source": row.get("resolved_input", {}).get("value_source", ""),
                }
            )
            continue
        if target_key in used_targets:
            skipped.append(
                {
                    "emitter_name": row["emitter_name"],
                    "module_name": row["module_name"],
                    "input_name": row["input_name"],
                    "input_type": row["input_type"],
                    "reason": "already_set",
                }
            )
            continue
        used_targets.add(target_key)

        source, value, operation = target_value
        batch_edits.append(
            {
                "operation": operation,
                "emitter_name": row["emitter_name"],
                "module_node_guid": row["module_node_guid"],
                "input_name": row["input_name"],
                "value": value,
            }
        )
        planned_applications.append(
            {
                "success": False,
                "emitter_name": row["emitter_name"],
                "module_name": row["module_name"],
                "module_node_guid": row["module_node_guid"],
                "input_name": row["input_name"],
                "input_type": row["input_type"],
                "operation": operation,
                "created_missing_override": operation == "create_override",
                "previous_value_source": row.get("resolved_input", {}).get("value_source", ""),
                "had_rapid_iteration_value": module_input_has_rapid_iteration_value(row.get("resolved_input", {})),
                "intent_source": source,
                "intent_source_text": row_intent.get("source_text", ""),
                "intent_target_layers": row_intent.get("target_layers", []),
                "value": value,
            }
        )

    batch_response: dict[str, Any] | None = None
    applications = planned_applications
    if batch_edits:
        batch_response = send_unreal_mcp_command(
            "set_niagara_module_inputs_batch",
            {
                "system_path": target_object_path,
                "edits": batch_edits,
                "operation": "set_existing",
                "continue_on_error": True,
                "save": save_assets,
            },
            host,
            port,
            timeout=max(60.0, 20.0 * len(batch_edits)),
        )

        batch_result = batch_response.get("result", {}) if isinstance(batch_response, dict) else {}
        result_by_index = {
            int(item.get("edit_index", -1)): item
            for item in batch_result.get("results", [])
            if isinstance(item, dict)
        }
        for index, application in enumerate(applications):
            item_result = result_by_index.get(index, {})
            item_success = bool(item_result.get("success", False))
            application["success"] = item_success
            application["response"] = item_result
            application["created_missing_override"] = bool(item_result.get("created", False))
            application["overwrote_existing"] = bool(item_result.get("overwrote_existing", False))
            if "new_value" in item_result:
                application["applied_value"] = item_result.get("new_value")

    success = all(item.get("success") for item in applications)
    return {
        "success": success,
        "mode": "socket_apply_module_inputs",
        "transport": "set_niagara_module_inputs_batch",
        "recipe_path": str(recipe_path),
        "request": recipe.get("request", ""),
        "target_system": target_object_path,
        "inspected_emitter_count": inspect_response.get("result", {}).get("emitter_count", 0),
        "inspected_module_count": inspect_response.get("result", {}).get("module_count", 0),
        "application_count": len(applications),
        "application_summary": summarize_module_input_applications(applications),
        "applications": applications,
        "batch_edit_count": len(batch_edits),
        "batch_summary": summarize_module_input_batch_response(batch_response),
        "batch_response": batch_response,
        "skipped_module_inputs": skipped[:200],
        "module_intent": {
            "target_layers": module_intent.get("target_layers", []),
            "bindings": [
                {
                    "target_layers": binding.get("target_layers", []),
                    "source_text": binding.get("source_text", ""),
                    "color": binding.get("color", [""])[0] if binding.get("color") else "",
                    "duration_seconds": binding.get("duration"),
                    "size_multiplier": binding.get("size_multiplier"),
                    "spawn_multiplier": binding.get("spawn_multiplier"),
                    "velocity_multiplier": binding.get("velocity_multiplier"),
                    "opacity_multiplier": binding.get("opacity_multiplier"),
                }
                for binding in module_intent.get("bindings", [])
            ],
            "size_multiplier": module_intent.get("size_multiplier"),
            "spawn_multiplier": module_intent.get("spawn_multiplier"),
            "velocity_multiplier": module_intent.get("velocity_multiplier"),
            "opacity_multiplier": module_intent.get("opacity_multiplier"),
            "duration_seconds": duration,
            "color": material_color[0] if material_color else "",
        },
        "unapplied_module_input_intent": {
            "color": material_color[0] if material_color else "",
            "duration_seconds": duration,
            "reason": "" if applications else "No RapidIteration module input matched safe name/type hints or supported missing-override types.",
        },
        "source_policy": recipe.get("write_scope", {}).get("source_policy", ""),
    }


def insert_scratch_pad_modules_via_socket(
    recipe: dict[str, Any],
    recipe_path: Path,
    host: str,
    port: int,
    save_assets: bool,
) -> dict[str, Any]:
    generation_plan = recipe.get("generation_plan", {})
    target_system = generation_plan.get("target_system", "")
    ensure_temp_path(target_system)
    target_object_path = object_path_from_package_path(target_system)
    planned_insertions = generation_plan.get("scratch_pad_stack_insertions", [])

    applications = []
    for index, insertion in enumerate(planned_insertions):
        params = {
            "target_system_path": target_object_path,
            "scratch_pad_owner_kind": insertion.get("scratch_pad_owner_kind", "system"),
            "scratch_pad_name": insertion.get("scratch_pad_name", ""),
            "target_usage": insertion.get("target_usage", "ParticleUpdateScript"),
            "target_index": insertion.get("target_index", -1),
            "suggested_name": insertion.get("suggested_name", ""),
            "skip_if_duplicate": True,
            "save": save_assets,
            "request_compile": True,
        }
        for optional_key in (
            "scratch_pad_script_index",
            "scratch_pad_emitter_index",
            "scratch_pad_emitter_name",
            "target_emitter_index",
            "target_emitter_name",
        ):
            if optional_key in insertion and insertion.get(optional_key) not in (None, ""):
                params[optional_key] = insertion.get(optional_key)

        response = send_unreal_mcp_command(
            "add_scratch_pad_module_to_stack",
            params,
            host,
            port,
            timeout=60.0,
        )
        result = response.get("result", {}) if isinstance(response, dict) else {}
        applications.append(
            {
                "success": response.get("status") == "success" and bool(result.get("success", False)),
                "status": "skipped_duplicate" if result.get("skipped_duplicate", False) else ("inserted" if response.get("status") == "success" and bool(result.get("success", False)) else "failed"),
                "skipped_duplicate": bool(result.get("skipped_duplicate", False)),
                "skip_reason": result.get("skip_reason", ""),
                "edit_index": index,
                "scratch_pad_name": insertion.get("scratch_pad_name", ""),
                "target_usage": insertion.get("target_usage", ""),
                "target_emitter_name": insertion.get("target_emitter_name", ""),
                "target_emitter_index": insertion.get("target_emitter_index", -1),
                "new_module_node_guid": result.get("new_module_node_guid", "") or result.get("existing_module_node_guid", ""),
                "new_module_function_name": result.get("new_module_function_name", "") or result.get("existing_module_function_name", ""),
                "graph_node_count_before": result.get("graph_node_count_before"),
                "graph_node_count_after": result.get("graph_node_count_after"),
                "response": response,
            }
        )

    compile_validation = validate_compile_status_via_socket(
        recipe,
        recipe_path,
        host,
        port,
        timeout_seconds=20.0,
        poll_interval_seconds=0.2,
    ) if applications else {}
    inserted_count = len([item for item in applications if item.get("status") == "inserted"])
    skipped_duplicate_count = len([item for item in applications if item.get("status") == "skipped_duplicate"])
    failed_count = len([item for item in applications if item.get("status") == "failed"])

    return {
        "success": all(item.get("success") for item in applications) and (not compile_validation or bool(compile_validation.get("success", False))),
        "mode": "socket_insert_scratch_pad_modules",
        "transport": "add_scratch_pad_module_to_stack",
        "recipe_path": str(recipe_path),
        "request": recipe.get("request", ""),
        "target_system": target_object_path,
        "planned_count": len(planned_insertions),
        "application_count": len(applications),
        "inserted_count": inserted_count,
        "skipped_duplicate_count": skipped_duplicate_count,
        "failed_count": failed_count,
        "applications": applications,
        "compile_validation": compile_validation,
        "fatal_reasons": compile_validation.get("fatal_reasons", []) if compile_validation else [],
        "source_policy": recipe.get("write_scope", {}).get("source_policy", ""),
    }


def validate_compile_status_via_socket(
    recipe: dict[str, Any],
    recipe_path: Path,
    host: str,
    port: int,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> dict[str, Any]:
    generation_plan = recipe.get("generation_plan", {})
    target_system = generation_plan.get("target_system", "")
    ensure_temp_path(target_system)
    target_object_path = object_path_from_package_path(target_system)

    response = send_unreal_mcp_command(
        "inspect_niagara_compile_status",
        {
            "system_path": target_object_path,
            "request_compile": True,
            "force": False,
            "wait_for_completion": True,
            "timeout_seconds": timeout_seconds,
            "poll_interval_seconds": poll_interval_seconds,
        },
        host,
        port,
        timeout=max(30.0, float(timeout_seconds) + 15.0),
    )
    if response.get("status") != "success":
        raise RuntimeError(f"Failed to inspect Niagara compile status: {response}")

    result = response.get("result", {})
    fatal_reasons = []
    if result.get("wait_timed_out", False):
        fatal_reasons.append("compile_wait_timed_out")
    if result.get("outstanding_compilation_requests_after", False):
        fatal_reasons.append("outstanding_compilation_requests_after_wait")
    if int(result.get("error_count", 0)) > 0:
        fatal_reasons.append("compile_errors_present")
    if int(result.get("dirty_count", 0)) > 0:
        fatal_reasons.append("dirty_scripts_present")
    if int(result.get("missing_count", 0)) > 0:
        fatal_reasons.append("missing_scripts_present")

    notable_scripts = []
    for script in result.get("scripts", []):
        compile_status = script.get("compile_status", "")
        if script.get("has_error") or script.get("has_warning") or compile_status in {"NCS_Dirty", "NCS_Unknown", "missing"}:
            notable_scripts.append(
                {
                    "owner_kind": script.get("owner_kind", ""),
                    "owner_name": script.get("owner_name", ""),
                    "script_name": script.get("script_name", ""),
                    "usage": script.get("usage", ""),
                    "compile_status": compile_status,
                    "has_error": script.get("has_error", False),
                    "has_warning": script.get("has_warning", False),
                }
            )

    return {
        "success": not fatal_reasons,
        "mode": "socket_validate_compile_status",
        "recipe_path": str(recipe_path),
        "request": recipe.get("request", ""),
        "target_system": target_object_path,
        "fatal_reasons": fatal_reasons,
        "compile_summary": {
            "script_count": result.get("script_count", 0),
            "error_count": result.get("error_count", 0),
            "warning_count": result.get("warning_count", 0),
            "dirty_count": result.get("dirty_count", 0),
            "unknown_count": result.get("unknown_count", 0),
            "missing_count": result.get("missing_count", 0),
            "compile_requested": result.get("compile_requested", False),
            "wait_for_completion": result.get("wait_for_completion", False),
            "wait_timed_out": result.get("wait_timed_out", False),
            "wait_elapsed_seconds": result.get("wait_elapsed_seconds", 0.0),
            "wait_iterations": result.get("wait_iterations", 0),
            "outstanding_compilation_requests_before": result.get("outstanding_compilation_requests_before", False),
            "outstanding_compilation_requests_after_request": result.get("outstanding_compilation_requests_after_request", False),
            "outstanding_compilation_requests_after": result.get("outstanding_compilation_requests_after", False),
        },
        "notable_scripts": notable_scripts[:50],
        "source_policy": recipe.get("write_scope", {}).get("source_policy", ""),
    }


def unwrap_unreal_mcp_result(response: dict[str, Any]) -> dict[str, Any]:
    if isinstance(response.get("result"), dict):
        return response["result"]
    return response


def preview_capture_output_path(recipe: dict[str, Any], recipe_path: Path) -> Path:
    generation_plan = recipe.get("generation_plan", {})
    target_system = generation_plan.get("target_system", "")
    slug = slug_from_target(target_system) if target_system else sanitize_asset_name(recipe_path.stem)
    root = repo_root_from(recipe_path.parent)
    return root / "Saved" / "MCP" / "NiagaraReviews" / slug / f"{slug}_niagara_previewer.png"


def capture_preview_player_window(output_path: Path, title_pattern: str = "Niagara Preview Player") -> dict[str, Any]:
    root = repo_root_from(output_path.parent)
    script_path = root / "Tools" / "Unreal" / "capture-unreal-editor-window.ps1"
    if not script_path.exists():
        raise RuntimeError(f"Preview Player capture script is missing: {script_path}")

    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            "-OutputPath",
            str(output_path),
            "-TitlePattern",
            title_pattern,
        ],
        text=True,
        capture_output=True,
        timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Preview Player window capture failed: "
            + (completed.stderr.strip() or completed.stdout.strip() or f"exit={completed.returncode}")
        )

    stdout = completed.stdout.strip()
    try:
        result = json.loads(stdout.splitlines()[-1])
    except Exception as exc:
        raise RuntimeError(f"Preview Player capture did not return JSON: {stdout}") from exc

    if not output_path.exists():
        raise RuntimeError(f"Preview Player capture did not write PNG: {output_path}")
    return result


def analyze_preview_player_screenshot(image_path: Path) -> dict[str, Any]:
    image_path_text = str(image_path)
    command = f"$ImagePath = @'\n{image_path_text}\n'@\n" + r"""
Add-Type -AssemblyName System.Drawing
$bitmap = [System.Drawing.Bitmap]::new($ImagePath)
try {
    $left = [Math]::Floor($bitmap.Width * 0.01)
    $top = [Math]::Floor($bitmap.Height * 0.17)
    $right = [Math]::Floor($bitmap.Width * 0.63)
    $bottom = [Math]::Floor($bitmap.Height * 0.94)
    $stepX = [Math]::Max(1, [Math]::Floor(($right - $left) / 48))
    $stepY = [Math]::Max(1, [Math]::Floor(($bottom - $top) / 36))
    $sampleCount = 0
    $nonBlackCount = 0
    $brightCount = 0
    $lumaTotal = 0
    $lumaMax = 0
    for ($y = $top; $y -lt $bottom; $y += $stepY) {
        for ($x = $left; $x -lt $right; $x += $stepX) {
            $pixel = $bitmap.GetPixel($x, $y)
            $sum = [int]$pixel.R + [int]$pixel.G + [int]$pixel.B
            $luma = $sum / 3.0
            $sampleCount++
            $lumaTotal += $luma
            if ($luma -gt $lumaMax) { $lumaMax = $luma }
            if ($sum -gt 18) { $nonBlackCount++ }
            if ($sum -gt 180) { $brightCount++ }
        }
    }
    [pscustomobject]@{
        width = $bitmap.Width
        height = $bitmap.Height
        viewport_rect_ratio = "0.01,0.17,0.63,0.94"
        sample_count = $sampleCount
        viewport_non_black_ratio = if ($sampleCount -gt 0) { [Math]::Round($nonBlackCount / $sampleCount, 4) } else { 0.0 }
        viewport_bright_ratio = if ($sampleCount -gt 0) { [Math]::Round($brightCount / $sampleCount, 4) } else { 0.0 }
        viewport_average_luma = if ($sampleCount -gt 0) { [Math]::Round($lumaTotal / $sampleCount, 2) } else { 0.0 }
        viewport_max_luma = [Math]::Round($lumaMax, 2)
    } | ConvertTo-Json -Compress
} finally {
    $bitmap.Dispose()
}
"""
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        text=True,
        capture_output=True,
        timeout=20,
    )
    if completed.returncode != 0:
        return {"success": False, "error": completed.stderr.strip() or completed.stdout.strip()}
    try:
        result = json.loads(completed.stdout.strip().splitlines()[-1])
    except Exception as exc:
        return {"success": False, "error": f"Could not parse screenshot analysis JSON: {exc}"}
    result["success"] = True
    result.update(classify_preview_player_visual_read(result))
    if result.get("visual_warnings"):
        result["warning"] = "; ".join(result["visual_warnings"])
    return result


def classify_preview_player_visual_read(analysis: dict[str, Any]) -> dict[str, Any]:
    if not analysis.get("success", False):
        return {
            "visual_pass": False,
            "visual_read_status": "analysis_failed",
            "visual_confidence": "none",
            "visual_warnings": [],
            "visual_failure_reasons": ["screenshot_analysis_failed"],
            "visual_summary": "Screenshot analysis failed.",
        }

    sample_count = int(analysis.get("sample_count", 0) or 0)
    non_black_ratio = float(analysis.get("viewport_non_black_ratio", 0.0) or 0.0)
    bright_ratio = float(analysis.get("viewport_bright_ratio", 0.0) or 0.0)
    average_luma = float(analysis.get("viewport_average_luma", 0.0) or 0.0)
    max_luma = float(analysis.get("viewport_max_luma", 0.0) or 0.0)
    warnings: list[str] = []
    failures: list[str] = []

    if sample_count < 100:
        failures.append("too_few_viewport_samples")
    if non_black_ratio < 0.05:
        failures.append("viewport_appears_empty_or_black")
    if max_luma < 90.0 and bright_ratio < 0.002:
        failures.append("viewport_too_dark_for_visual_read")
    elif max_luma < 120.0:
        warnings.append("viewport_has_no_strong_highlight")
    if average_luma < 35.0:
        warnings.append("viewport_average_luma_is_low")
    if bright_ratio < 0.005:
        warnings.append("viewport_bright_pixel_ratio_is_low")

    if failures:
        status = "fail"
        confidence = "low"
        visual_pass = False
    elif max_luma >= 150.0 and bright_ratio >= 0.005:
        status = "pass" if not warnings else "pass_with_warnings"
        confidence = "high" if bright_ratio >= 0.05 else "medium"
        visual_pass = True
    elif max_luma >= 120.0 and bright_ratio >= 0.002:
        status = "pass_with_warnings"
        confidence = "low"
        visual_pass = True
        warnings.append("visual_signal_is_thin_or_brief")
    else:
        status = "weak"
        confidence = "low"
        visual_pass = False
        warnings.append("visual_signal_is_weak")

    summary = (
        f"{status}: avg_luma={average_luma:.2f}, max_luma={max_luma:.2f}, "
        f"bright_ratio={bright_ratio:.4f}, non_black_ratio={non_black_ratio:.4f}"
    )
    return {
        "visual_pass": visual_pass,
        "visual_read_status": status,
        "visual_confidence": confidence,
        "visual_warnings": sorted(set(warnings)),
        "visual_failure_reasons": sorted(set(failures)),
        "visual_summary": summary,
    }


def preview_screenshot_score(analysis: dict[str, Any]) -> float:
    if not analysis.get("success", False):
        return -1.0
    return (
        float(analysis.get("viewport_average_luma", 0.0))
        + float(analysis.get("viewport_max_luma", 0.0)) * 0.4
        + float(analysis.get("viewport_bright_ratio", 0.0)) * 120.0
    )


def capture_preview_player_candidates(
    output_path: Path,
    capture_count: int,
    capture_interval_seconds: float,
) -> dict[str, Any]:
    safe_count = max(1, min(int(capture_count), 12))
    safe_interval = max(0.0, float(capture_interval_seconds))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    candidates = []
    for index in range(safe_count):
        if index > 0 and safe_interval > 0:
            time.sleep(safe_interval)
        candidate_path = output_path.with_name(f"{output_path.stem}_candidate_{index + 1:02d}{output_path.suffix}")
        capture_result = capture_preview_player_window(candidate_path)
        analysis = analyze_preview_player_screenshot(candidate_path)
        candidates.append(
            {
                "candidate_index": index + 1,
                "path": str(candidate_path),
                "score": round(preview_screenshot_score(analysis), 4),
                "capture_result": capture_result,
                "screenshot_analysis": analysis,
            }
        )

    successful_candidates = [candidate for candidate in candidates if candidate.get("screenshot_analysis", {}).get("success", False)]
    if not successful_candidates:
        raise RuntimeError("Preview Player capture produced no analyzable screenshot candidates")

    best = max(successful_candidates, key=lambda candidate: candidate.get("score", -1.0))
    shutil.copyfile(best["path"], output_path)
    final_analysis = analyze_preview_player_screenshot(output_path)
    final_capture_result = dict(best.get("capture_result", {}))
    final_capture_result["path"] = str(output_path)

    return {
        "path": str(output_path),
        "selected_candidate_index": best.get("candidate_index"),
        "selected_candidate_path": best.get("path", ""),
        "selected_score": best.get("score", -1.0),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "capture_result": final_capture_result,
        "screenshot_analysis": final_analysis,
    }


def validate_preview_player_via_socket(
    recipe: dict[str, Any],
    recipe_path: Path,
    host: str,
    port: int,
    capture_screenshot: bool,
    preview_settle_seconds: float,
    preview_capture_count: int,
    preview_capture_interval: float,
    refresh_state: bool,
    require_visual_pass: bool,
) -> dict[str, Any]:
    generation_plan = recipe.get("generation_plan", {})
    target_system = generation_plan.get("target_system", "")
    ensure_temp_path(target_system)
    target_object_path = object_path_from_package_path(target_system)

    open_error = ""
    open_recovered_from_state = False
    try:
        open_response = send_unreal_mcp_command(
            "open_niagara_preview_player",
            {"system_path": target_object_path},
            host,
            port,
            timeout=90.0,
        )
        if open_response.get("status") != "success":
            raise RuntimeError(f"Failed to open Niagara Preview Player: {open_response}")
        open_result = unwrap_unreal_mcp_result(open_response)
    except Exception as exc:
        open_error = str(exc)
        state_response = send_unreal_mcp_command_with_retry(
            "get_niagara_preview_player_state",
            {},
            host,
            port,
            timeout=15.0,
            attempts=2,
            retry_delay_seconds=1.0,
        )
        if state_response.get("status") != "success":
            raise RuntimeError(f"Failed to recover Niagara Preview Player state after open error: {open_error}; {state_response}") from exc
        open_result = unwrap_unreal_mcp_result(state_response)
        if open_result.get("last_object_path", "") != target_object_path:
            raise RuntimeError(
                "Niagara Preview Player open timed out and recovered state did not match target: "
                f"target={target_object_path}, state={open_result.get('last_object_path', '')}, error={open_error}"
            ) from exc
        open_result["preview_loaded"] = True
        open_recovered_from_state = True

    if preview_settle_seconds > 0:
        time.sleep(preview_settle_seconds)

    state_result = open_result
    state_source = "get_niagara_preview_player_state_after_open_error" if open_recovered_from_state else "open_niagara_preview_player"
    state_error = ""
    if refresh_state:
        try:
            state_response = send_unreal_mcp_command_with_retry(
                "get_niagara_preview_player_state",
                {},
                host,
                port,
                timeout=15.0,
                attempts=1,
                retry_delay_seconds=2.0,
            )
            if state_response.get("status") != "success":
                raise RuntimeError(f"Failed to inspect Niagara Preview Player state: {state_response}")
            state_result = unwrap_unreal_mcp_result(state_response)
            state_source = "get_niagara_preview_player_state"
        except Exception as exc:
            state_error = str(exc)
            state_result = open_result

    capture_result: dict[str, Any] = {}
    screenshot_analysis: dict[str, Any] = {}
    screenshot_candidates: list[dict[str, Any]] = []
    selected_candidate_index = 0
    screenshot_path = ""
    capture_error = ""
    if capture_screenshot:
        output_path = preview_capture_output_path(recipe, recipe_path)
        try:
            capture_selection = capture_preview_player_candidates(
                output_path,
                preview_capture_count,
                preview_capture_interval,
            )
            capture_result = capture_selection.get("capture_result", {})
            screenshot_analysis = capture_selection.get("screenshot_analysis", {})
            screenshot_candidates = capture_selection.get("candidates", [])
            selected_candidate_index = int(capture_selection.get("selected_candidate_index", 0))
            screenshot_path = capture_selection.get("path", str(output_path))
        except Exception as exc:
            capture_error = str(exc)

    fatal_reasons = []
    if not open_result.get("preview_loaded", False):
        fatal_reasons.append("preview_player_load_failed")
    if not state_result.get("last_preview_renderable", False):
        fatal_reasons.append("preview_not_renderable")
    if capture_screenshot and capture_error:
        fatal_reasons.append("preview_player_screenshot_failed")
    if capture_screenshot and require_visual_pass and not capture_error and not screenshot_analysis.get("visual_pass", False):
        fatal_reasons.append("preview_visual_read_failed")

    return {
        "success": not fatal_reasons,
        "mode": "socket_validate_preview_player",
        "recipe_path": str(recipe_path),
        "request": recipe.get("request", ""),
        "target_system": target_object_path,
        "fatal_reasons": fatal_reasons,
        "preview_loaded": open_result.get("preview_loaded", False),
        "open_error": open_error,
        "open_recovered_from_state": open_recovered_from_state,
        "window_open": state_result.get("window_open", False),
        "last_preview_renderable": state_result.get("last_preview_renderable", False),
        "playback_state": state_result.get("playback_state", ""),
        "looping": state_result.get("looping", False),
        "analysis_summary": str(state_result.get("analysis_summary", ""))[:4096],
        "state_source": state_source,
        "state_error": state_error,
        "screenshot_path": screenshot_path,
        "selected_screenshot_candidate_index": selected_candidate_index,
        "require_visual_pass": require_visual_pass,
        "screenshot_visual_pass": screenshot_analysis.get("visual_pass", False),
        "screenshot_visual_read_status": screenshot_analysis.get("visual_read_status", ""),
        "screenshot_visual_confidence": screenshot_analysis.get("visual_confidence", ""),
        "screenshot_visual_warnings": screenshot_analysis.get("visual_warnings", []),
        "screenshot_visual_failure_reasons": screenshot_analysis.get("visual_failure_reasons", []),
        "screenshot_visual_summary": screenshot_analysis.get("visual_summary", ""),
        "capture_result": capture_result,
        "screenshot_analysis": screenshot_analysis,
        "screenshot_candidates": screenshot_candidates,
        "capture_error": capture_error,
        "source_policy": recipe.get("write_scope", {}).get("source_policy", ""),
    }


def run_socket_postprocess(
    recipe: dict[str, Any],
    recipe_path: Path,
    host: str,
    port: int,
    save_assets: bool,
    compile_wait_timeout: float,
    compile_poll_interval: float,
    preview_capture: bool,
    preview_settle_seconds: float,
    preview_capture_count: int,
    preview_capture_interval: float,
    preview_refresh_state: bool,
    preview_require_visual_pass: bool,
) -> dict[str, Any]:
    generation_plan = recipe.get("generation_plan", {})
    target_system = generation_plan.get("target_system", "")
    ensure_temp_path(target_system)

    step_reports: list[dict[str, Any]] = []
    step_errors: list[dict[str, Any]] = []
    available_steps = {
        step.get("step", "")
        for step in generation_plan.get("can_execute_now", [])
    }

    def run_step(step_name: str, runner) -> None:
        if step_name not in available_steps:
            step_reports.append(
                {
                    "mode": step_name,
                    "success": True,
                    "skipped": True,
                    "reason": "step_not_present_in_generation_plan",
                }
            )
            return
        try:
            step_reports.append(runner())
        except Exception as exc:
            step_errors.append({"step": step_name, "error": str(exc)})

    run_step(
        "bind_duplicated_materials_to_matching_renderers",
        lambda: bind_renderer_materials_via_socket(recipe, recipe_path, host, port, save_assets),
    )
    run_step(
        "apply_matching_user_parameter_overrides",
        lambda: apply_user_parameters_via_socket(recipe, recipe_path, host, port, save_assets),
    )
    run_step(
        "apply_matching_module_input_overrides",
        lambda: apply_module_inputs_via_socket(recipe, recipe_path, host, port, save_assets),
    )
    run_step(
        "insert_planned_scratch_pad_modules",
        lambda: insert_scratch_pad_modules_via_socket(recipe, recipe_path, host, port, save_assets),
    )
    try:
        step_reports.append(
            validate_compile_status_via_socket(
                recipe,
                recipe_path,
                host,
                port,
                compile_wait_timeout,
                compile_poll_interval,
            )
        )
    except Exception as exc:
        step_errors.append({"step": "validate_compile_status", "error": str(exc)})
    try:
        step_reports.append(
            validate_preview_player_via_socket(
                recipe,
                recipe_path,
                host,
                port,
                preview_capture,
                preview_settle_seconds,
                preview_capture_count,
                preview_capture_interval,
                preview_refresh_state,
                preview_require_visual_pass,
            )
        )
    except Exception as exc:
        step_errors.append({"step": "validate_preview_player", "error": str(exc)})

    return {
        "success": not step_errors and all(report.get("success", False) for report in step_reports),
        "mode": "socket_postprocess",
        "recipe_path": str(recipe_path),
        "request": recipe.get("request", ""),
        "target_system": object_path_from_package_path(target_system),
        "step_reports": step_reports,
        "step_errors": step_errors,
        "blocked_by_api": generation_plan.get("blocked_by_api", []),
        "source_policy": recipe.get("write_scope", {}).get("source_policy", ""),
    }


def report_step(report: dict[str, Any], mode: str) -> dict[str, Any]:
    if report.get("mode") == mode:
        return report
    for step in report.get("step_reports", []):
        if step.get("mode") == mode:
            return step
    return {}


def review_status_from_bool(value: Any) -> str:
    if value is True:
        return "pass"
    if value is False:
        return "fail"
    return "not_run"


def build_review_summary(report: dict[str, Any], report_path: Path) -> dict[str, Any]:
    compile_report = report_step(report, "socket_validate_compile_status")
    preview_report = report_step(report, "socket_validate_preview_player")
    renderer_report = report_step(report, "socket_bind_renderer_materials")
    user_report = report_step(report, "socket_apply_user_parameters")
    module_report = report_step(report, "socket_apply_module_inputs")
    scratch_pad_report = report_step(report, "socket_insert_scratch_pad_modules")

    compile_summary = compile_report.get("compile_summary", {})
    module_application_summary = module_report.get("application_summary", {})
    module_batch_summary = module_report.get("batch_summary", {})
    visual_pass = preview_report.get("screenshot_visual_pass") if preview_report else None
    visual_warnings = preview_report.get("screenshot_visual_warnings", []) if preview_report else []
    visual_failures = preview_report.get("screenshot_visual_failure_reasons", []) if preview_report else []
    blocked_by_api = report.get("blocked_by_api", [])
    step_errors = report.get("step_errors", [])
    dirty_check = report.get("dirty_package_check", {})
    dirty_status = dirty_check.get("status", "not_recorded")
    dirty_content_count = dirty_check.get("dirty_content_count")
    dirty_map_count = dirty_check.get("dirty_map_count")
    fatal_reasons = []
    for gate_report in (compile_report, preview_report):
        fatal_reasons.extend(gate_report.get("fatal_reasons", []))

    warnings = []
    if visual_warnings:
        warnings.extend(f"visual:{item}" for item in visual_warnings)
    if int(compile_summary.get("warning_count", 0) or 0) > 0:
        warnings.append("compile_warnings_present")
    if preview_report and not preview_report.get("screenshot_path"):
        warnings.append("missing_preview_screenshot")
    if report.get("mode") in {"socket_postprocess", "socket_validate_preview_player"} and not preview_report:
        warnings.append("preview_gate_not_found")
    if dirty_status == "unavailable":
        warnings.append("dirty_package_check_unavailable")
    dirty_failed = dirty_status == "fail"

    if not report.get("success", False) or step_errors or fatal_reasons or dirty_failed:
        overall_status = "fail"
        recommended_next_action = "Fix fatal validation reasons, step errors, or dirty packages, then rerun generated-temp postprocess validation."
    elif blocked_by_api:
        overall_status = "blocked"
        recommended_next_action = "Resolve remaining blocked API items before attempting deeper Niagara authoring."
    elif visual_pass is False:
        overall_status = "needs_visual_review"
        recommended_next_action = "Manually review the Preview Player screenshot before promoting or rerun with more capture candidates."
    elif warnings:
        overall_status = "pass_with_warnings"
        recommended_next_action = "Review warnings and screenshot, then decide whether the generated temp system is acceptable."
    else:
        overall_status = "pass"
        recommended_next_action = "Automated generated-temp review passed; manually inspect the screenshot before promoting beyond _MCP_Temp."

    return {
        "summary_version": 2,
        "overall_status": overall_status,
        "success": overall_status == "pass",
        "recommended_next_action": recommended_next_action,
        "request": report.get("request", ""),
        "mode": report.get("mode", ""),
        "target_system": report.get("target_system", ""),
        "source_policy": report.get("source_policy", ""),
        "artifacts": {
            "execution_report_path": str(report_path),
            "screenshot_path": preview_report.get("screenshot_path", ""),
            "selected_screenshot_candidate_index": preview_report.get("selected_screenshot_candidate_index", 0),
            "screenshot_candidate_count": len(preview_report.get("screenshot_candidates", [])) if preview_report else 0,
        },
        "writes": {
            "renderer_binding_count": int(renderer_report.get("binding_count", 0) or 0),
            "user_parameter_application_count": int(user_report.get("application_count", 0) or 0),
            "module_input_application_count": int(module_report.get("application_count", 0) or 0),
            "scratch_pad_stack_insert_count": int(scratch_pad_report.get("application_count", 0) or 0),
            "module_inputs": {
                "transport": module_report.get("transport", ""),
                "application_count": int(module_report.get("application_count", 0) or 0),
                "batch_edit_count": int(module_report.get("batch_edit_count", 0) or 0),
                "succeeded": int(module_application_summary.get("succeeded", 0) or 0),
                "failed": int(module_application_summary.get("failed", 0) or 0),
                "created_missing_override": int(module_application_summary.get("created_missing_override", 0) or 0),
                "overwritten_existing": int(module_application_summary.get("overwritten_existing", 0) or 0),
                "edited_existing": int(module_application_summary.get("edited_existing", 0) or 0),
                "by_operation": module_application_summary.get("by_operation", {}),
                "by_intent": module_application_summary.get("by_intent", {}),
                "batch": module_batch_summary,
            },
            "scratch_pads": {
                "transport": scratch_pad_report.get("transport", ""),
                "planned_count": int(scratch_pad_report.get("planned_count", 0) or 0),
                "application_count": int(scratch_pad_report.get("application_count", 0) or 0),
                "inserted": int(scratch_pad_report.get("inserted_count", 0) or 0),
                "skipped_duplicate": int(scratch_pad_report.get("skipped_duplicate_count", 0) or 0),
                "failed": int(scratch_pad_report.get("failed_count", 0) or 0),
                "compile_fatal_reasons": scratch_pad_report.get("fatal_reasons", []),
                "applications": [
                    {
                        "status": item.get("status", ""),
                        "scratch_pad_name": item.get("scratch_pad_name", ""),
                        "target_usage": item.get("target_usage", ""),
                        "target_emitter_name": item.get("target_emitter_name", ""),
                        "new_module_node_guid": item.get("new_module_node_guid", ""),
                        "new_module_function_name": item.get("new_module_function_name", ""),
                    }
                    for item in scratch_pad_report.get("applications", [])
                ],
            },
        },
        "gates": {
            "compile": {
                "status": review_status_from_bool(compile_report.get("success") if compile_report else None),
                "fatal_reasons": compile_report.get("fatal_reasons", []),
                "script_count": int(compile_summary.get("script_count", 0) or 0),
                "error_count": int(compile_summary.get("error_count", 0) or 0),
                "warning_count": int(compile_summary.get("warning_count", 0) or 0),
                "dirty_count": int(compile_summary.get("dirty_count", 0) or 0),
                "missing_count": int(compile_summary.get("missing_count", 0) or 0),
                "wait_timed_out": bool(compile_summary.get("wait_timed_out", False)),
                "outstanding_compilation_requests_after": bool(compile_summary.get("outstanding_compilation_requests_after", False)),
            },
            "preview": {
                "status": review_status_from_bool(preview_report.get("success") if preview_report else None),
                "fatal_reasons": preview_report.get("fatal_reasons", []),
                "preview_loaded": bool(preview_report.get("preview_loaded", False)),
                "last_preview_renderable": bool(preview_report.get("last_preview_renderable", False)),
                "playback_state": preview_report.get("playback_state", ""),
                "state_source": preview_report.get("state_source", ""),
                "open_recovered_from_state": bool(preview_report.get("open_recovered_from_state", False)),
            },
            "visual": {
                "status": review_status_from_bool(visual_pass),
                "require_visual_pass": bool(preview_report.get("require_visual_pass", False)) if preview_report else False,
                "read_status": preview_report.get("screenshot_visual_read_status", ""),
                "confidence": preview_report.get("screenshot_visual_confidence", ""),
                "warnings": visual_warnings,
                "failure_reasons": visual_failures,
                "summary": preview_report.get("screenshot_visual_summary", ""),
            },
            "dirty_packages": {
                "status": dirty_status,
                "dirty_content_count": dirty_content_count,
                "dirty_map_count": dirty_map_count,
                "dirty_content_packages": dirty_check.get("dirty_content_packages", []),
                "dirty_map_packages": dirty_check.get("dirty_map_packages", []),
                "error": dirty_check.get("error", ""),
            },
        },
        "issues": {
            "step_errors": step_errors,
            "fatal_reasons": fatal_reasons,
            "warnings": warnings,
            "blocked_by_api_count": len(blocked_by_api),
            "blocked_by_api": blocked_by_api,
        },
    }


def build_dry_run_report(recipe: dict[str, Any], recipe_path: Path) -> dict[str, Any]:
    generation_plan = recipe.get("generation_plan", {})
    material_color = color_from_recipe(recipe)
    return {
        "success": True,
        "mode": "dry_run",
        "recipe_path": str(recipe_path),
        "request": recipe.get("request", ""),
        "target_system": generation_plan.get("target_system", ""),
        "would_execute": generation_plan.get("can_execute_now", []),
        "would_apply_material_color": material_color[0] if material_color else "",
        "blocked_by_api": generation_plan.get("blocked_by_api", []),
        "source_policy": recipe.get("write_scope", {}).get("source_policy", ""),
    }


def execute_recipe(recipe: dict[str, Any], recipe_path: Path, overwrite: bool, save_assets: bool) -> dict[str, Any]:
    generation_plan = recipe.get("generation_plan", {})
    target_system = generation_plan.get("target_system", "")
    ensure_temp_path(target_system)
    recipe_slug = slug_from_target(target_system)

    duplicated_assets: list[dict[str, Any]] = []
    material_parameter_applications: list[dict[str, Any]] = []
    skipped_steps: list[dict[str, Any]] = []
    material_color = color_from_recipe(recipe)

    for step in generation_plan.get("can_execute_now", []):
        step_name = step.get("step", "")
        if step_name == "duplicate_primary_system_to_temp":
            duplicated_assets.append(
                duplicate_asset(
                    source_path=step.get("source", ""),
                    target_path=target_system,
                    overwrite=overwrite,
                    save_assets=save_assets,
                )
            )
        elif step_name == "duplicate_candidate_material_instances":
            for material in recipe.get("material_plan", []):
                if material.get("operation") != "duplicate_material_instance":
                    continue
                source_material = material.get("source_material", "")
                if not source_material:
                    continue
                duplicated_material = duplicate_asset(
                    source_path=source_material,
                    target_path=material_target_path(recipe_slug, source_material),
                    overwrite=overwrite,
                    save_assets=save_assets,
                )
                duplicated_assets.append(duplicated_material)
                if material_color is not None:
                    material_parameter_applications.append(
                        apply_color_to_material_instance(
                            duplicated_material["target"],
                            material_color,
                            save_assets=save_assets,
                        )
                    )
        elif step_name == "bind_duplicated_materials_to_matching_renderers":
            skipped_steps.append(
                {
                    "step": step_name,
                    "reason": "Run this after duplication from an external process with --socket-bind-only to avoid re-entering the UnrealMCP socket from an in-editor Python command.",
                    "source": step.get("source", ""),
                    "target": step.get("target", ""),
                }
            )
        else:
            skipped_steps.append(
                {
                    "step": step_name,
                    "reason": "Executor does not implement this safe step yet.",
                    "source": step.get("source", ""),
                    "target": step.get("target", ""),
                }
            )

    preview_object_path = ""
    if duplicated_assets:
        preview_object_path = duplicated_assets[0].get("target", "")

    return {
        "success": True,
        "mode": "execute",
        "recipe_path": str(recipe_path),
        "request": recipe.get("request", ""),
        "target_system": target_system,
        "duplicated_assets": duplicated_assets,
        "material_parameter_applications": material_parameter_applications,
        "skipped_steps": skipped_steps,
        "blocked_by_api": generation_plan.get("blocked_by_api", []),
        "preview": {
            "recommended_tool": "Niagara Preview Player",
            "command": PREVIEW_PLAYER_COMMAND,
            "system_path": preview_object_path,
            "fallback": "Niagara Preview Lab screenshot after Preview Player visual check.",
        },
        "source_policy": recipe.get("write_scope", {}).get("source_policy", ""),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute safe temp Niagara generation recipe steps.")
    parser.add_argument("--recipe", required=True, type=Path, help="Recipe JSON from niagara_generation_recipe_builder.py.")
    parser.add_argument("--report", type=Path, default=None, help="Output execution report JSON.")
    parser.add_argument("--dry-run", action="store_true", help="Inspect recipe without Unreal or asset writes.")
    parser.add_argument("--socket-postprocess-only", action="store_true", help="Run all safe UnrealMCP socket post-processing steps on an already duplicated generated temp Niagara system.")
    parser.add_argument("--socket-bind-only", action="store_true", help="Bind duplicated temp materials to matching Niagara renderers through the UnrealMCP socket. Run outside the in-editor Python command after duplication.")
    parser.add_argument("--socket-apply-user-parameters-only", action="store_true", help="Apply prompt intent to existing exposed User.* parameters on a generated temp Niagara system through the UnrealMCP socket.")
    parser.add_argument("--socket-apply-module-inputs-only", action="store_true", help="Apply prompt intent to existing RapidIteration module inputs on a generated temp Niagara system through the UnrealMCP socket.")
    parser.add_argument("--socket-insert-scratch-pads-only", action="store_true", help="Insert planned target-local Scratch Pad modules into a generated temp Niagara system through the UnrealMCP socket.")
    parser.add_argument("--socket-validate-compile-only", action="store_true", help="Request and wait for Niagara compile validation on a generated temp Niagara system through the UnrealMCP socket.")
    parser.add_argument("--socket-validate-preview-only", action="store_true", help="Open the generated temp Niagara system in the Preview Player and capture the Preview Player window.")
    parser.add_argument("--compile-wait-timeout", type=float, default=20.0, help="Seconds to wait for Niagara compile validation in socket modes.")
    parser.add_argument("--compile-poll-interval", type=float, default=0.1, help="Seconds between Niagara compile validation polls.")
    parser.add_argument("--no-preview-capture", action="store_true", help="Skip Preview Player OS-window screenshot capture while still validating Preview Player state.")
    parser.add_argument("--preview-settle-seconds", type=float, default=1.0, help="Seconds to wait after loading the system in the Preview Player before state/capture.")
    parser.add_argument("--preview-capture-count", type=int, default=3, help="Number of Preview Player screenshot candidates to capture before selecting the best frame.")
    parser.add_argument("--preview-capture-interval", type=float, default=0.75, help="Seconds between Preview Player screenshot candidates.")
    parser.add_argument("--preview-refresh-state", action="store_true", help="After opening the Preview Player, also call get_niagara_preview_player_state. Disabled by default because open_niagara_preview_player already returns the loaded state.")
    parser.add_argument("--preview-require-visual-pass", action="store_true", help="Fail the Preview Player validation gate when the selected screenshot visual-read classification does not pass.")
    parser.add_argument("--unreal-mcp-host", default=UNREAL_MCP_HOST, help="UnrealMCP bridge host for --socket-bind-only.")
    parser.add_argument("--unreal-mcp-port", type=int, default=UNREAL_MCP_PORT, help="UnrealMCP bridge port for --socket-bind-only.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing temp generated assets.")
    parser.add_argument("--no-save", action="store_true", help="Do not save duplicated temp assets.")
    parser.add_argument("--no-dirty-package-check", action="store_true", help="Skip the post-run Unreal dirty package check in socket modes.")
    parser.add_argument("--no-review-summary", action="store_true", help="Do not write the compact review summary JSON next to the execution report.")
    parser.add_argument("--print-json", action="store_true", help="Print report JSON to stdout.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    configure_stdout_utf8()
    args = parse_args(argv)
    cwd_root = repo_root_from(Path.cwd())
    recipe_path = args.recipe if args.recipe.is_absolute() else cwd_root / args.recipe
    root = repo_root_from(recipe_path.parent)
    recipe = load_json(recipe_path)

    if args.socket_postprocess_only:
        report = run_socket_postprocess(
            recipe=recipe,
            recipe_path=recipe_path,
            host=args.unreal_mcp_host,
            port=args.unreal_mcp_port,
            save_assets=not args.no_save,
            compile_wait_timeout=args.compile_wait_timeout,
            compile_poll_interval=args.compile_poll_interval,
            preview_capture=not args.no_preview_capture,
            preview_settle_seconds=args.preview_settle_seconds,
            preview_capture_count=args.preview_capture_count,
            preview_capture_interval=args.preview_capture_interval,
            preview_refresh_state=args.preview_refresh_state,
            preview_require_visual_pass=args.preview_require_visual_pass,
        )
    elif args.socket_bind_only:
        report = bind_renderer_materials_via_socket(
            recipe=recipe,
            recipe_path=recipe_path,
            host=args.unreal_mcp_host,
            port=args.unreal_mcp_port,
            save_assets=not args.no_save,
        )
    elif args.socket_apply_user_parameters_only:
        report = apply_user_parameters_via_socket(
            recipe=recipe,
            recipe_path=recipe_path,
            host=args.unreal_mcp_host,
            port=args.unreal_mcp_port,
            save_assets=not args.no_save,
        )
    elif args.socket_apply_module_inputs_only:
        report = apply_module_inputs_via_socket(
            recipe=recipe,
            recipe_path=recipe_path,
            host=args.unreal_mcp_host,
            port=args.unreal_mcp_port,
            save_assets=not args.no_save,
        )
    elif args.socket_insert_scratch_pads_only:
        report = insert_scratch_pad_modules_via_socket(
            recipe=recipe,
            recipe_path=recipe_path,
            host=args.unreal_mcp_host,
            port=args.unreal_mcp_port,
            save_assets=not args.no_save,
        )
    elif args.socket_validate_compile_only:
        report = validate_compile_status_via_socket(
            recipe=recipe,
            recipe_path=recipe_path,
            host=args.unreal_mcp_host,
            port=args.unreal_mcp_port,
            timeout_seconds=args.compile_wait_timeout,
            poll_interval_seconds=args.compile_poll_interval,
        )
    elif args.socket_validate_preview_only:
        report = validate_preview_player_via_socket(
            recipe=recipe,
            recipe_path=recipe_path,
            host=args.unreal_mcp_host,
            port=args.unreal_mcp_port,
            capture_screenshot=not args.no_preview_capture,
            preview_settle_seconds=args.preview_settle_seconds,
            preview_capture_count=args.preview_capture_count,
            preview_capture_interval=args.preview_capture_interval,
            refresh_state=args.preview_refresh_state,
            require_visual_pass=args.preview_require_visual_pass,
        )
    elif args.dry_run:
        report = build_dry_run_report(recipe, recipe_path)
    else:
        report = execute_recipe(
            recipe=recipe,
            recipe_path=recipe_path,
            overwrite=args.overwrite,
            save_assets=not args.no_save,
        )

    if (
        not args.no_dirty_package_check
        and str(report.get("mode", "")).startswith("socket")
        and "dirty_package_check" not in report
    ):
        report["dirty_package_check"] = inspect_dirty_packages_via_socket(
            args.unreal_mcp_host,
            args.unreal_mcp_port,
        )
        if report["dirty_package_check"].get("status") == "fail":
            report["success"] = False

    if args.report:
        report_path = args.report if args.report.is_absolute() else root / args.report
    else:
        target_system = report.get("target_system", "NiagaraExecution")
        slug = slug_from_target(target_system) if target_system else "NiagaraExecution"
        report_path = root / DEFAULT_REPORT_DIR / f"{slug}_execution_report.json"
    write_json(report_path, report)
    summary_path = None
    if not args.no_review_summary:
        summary_path = report_path.with_name(f"{report_path.stem}_review_summary.json")
        write_json(summary_path, build_review_summary(report, report_path))

    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Report: {report_path}")
        if summary_path:
            print(f"Review summary: {summary_path}")
        print(f"Mode: {report['mode']}")
        print(f"Target: {report.get('target_system', '')}")
        print(f"Blocked by API: {len(report.get('blocked_by_api', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
