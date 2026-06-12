from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from pathlib import Path
from typing import Any


DEFAULT_SIGNATURE_INDEX = Path("docs/niagara-learning/niagara_structural_signature_index.json")
DEFAULT_MATERIAL_INDEX = Path("docs/niagara-learning/niagara_material_style_index.json")
DEFAULT_OUTPUT_DIR = Path("Saved/MCP_NiagaraGeneration")
TEMP_ROOT = "/Game/_MCP_Temp/NiagaraGenerated"
PRODUCTION_ROOT = "/Game/Cubeless/FX/Generated"
REVIEW_MAP = "/Script/Engine.World'/Game/SampleTestMap/Niagara_TestMap.Niagara_TestMap'"
UNREAL_MCP_HOST = "127.0.0.1"
UNREAL_MCP_PORT = 55557


ROLE_TERMS = {
    "ground_area": ["area", "field", "ring", "circle", "aoe", "ground", "zone", "장판", "원형", "범위", "바닥", "마법진"],
    "lightning_arc": ["lightning", "electric", "beam", "laser", "spark", "번개", "전기", "전격", "빔", "레이저"],
    "spark_spray": ["spark", "ember", "spray", "fragment", "스파크", "불티", "파편", "흩뿌림", "입자"],
    "smoke_volume": ["smoke", "fog", "mist", "dust", "poison", "연기", "안개", "먼지", "구름", "독안개", "독 안개"],
    "fire_flame": ["fire", "flame", "torch", "burn", "불", "화염", "불꽃", "타오름"],
    "ribbon_trail": ["trail", "ribbon", "slash", "swing", "sword", "animtrail", "궤적", "검궤적", "검 궤적", "베기", "참격"],
    "impact_burst": ["burst", "impact", "explosion", "blast", "hit", "폭발", "충돌", "타격", "히트", "버스트"],
    "weather_loop": ["rain", "snow", "storm", "weather", "비", "눈", "폭풍", "날씨"],
    "reactive_runtime": ["reactive", "interaction", "foliage", "반응", "상호작용", "리액티브", "풀반응"],
}


MATERIAL_TERMS = {
    "additive_glow": ["glow", "light", "emissive", "aura", "빛", "광휘", "발광", "오라"],
    "stylized_lightning": ["lightning", "electric", "번개", "전기", "전격", "빔", "레이저"],
    "soft_smoke": ["smoke", "fog", "mist", "poison", "연기", "안개", "독안개", "독 안개", "먼지"],
    "radial_shockwave": ["shockwave", "ring", "radial", "wave", "충격파", "원형", "장판", "파동"],
    "ribbon_slash": ["trail", "ribbon", "slash", "sword", "검궤적", "검 궤적", "베기", "궤적", "참격"],
    "spark_sprite": ["spark", "ember", "fragment", "스파크", "불티", "파편"],
    "fire_flipbook": ["fire", "flame", "burn", "불", "화염", "불꽃"],
    "water_splash": ["water", "rain", "splash", "물", "비", "물방울"],
}


COLOR_TERMS = {
    "blue": ["blue", "cyan", "푸른", "파란", "청색", "하늘색", "푸른색"],
    "red": ["red", "crimson", "scarlet", "붉은", "빨간", "적색", "핏빛", "붉은색"],
    "purple": ["purple", "violet", "magenta", "보라", "자주", "보라색"],
    "green": ["green", "emerald", "poison", "녹색", "초록", "초록색", "독"],
    "yellow": ["yellow", "gold", "노란", "금색", "황금", "노란색"],
    "orange": ["orange", "amber", "주황", "주황색"],
    "black": ["black", "dark", "shadow", "검은", "어두운", "흑색", "암흑"],
    "white": ["white", "silver", "흰", "하얀", "하얀색", "백색", "실버"],
}


MOTION_TERMS = {
    "radial_expand": ["expand", "outward", "radial", "spread", "퍼짐", "확산", "방사", "원형", "장판"],
    "upward_spark": ["upward", "rise", "위로", "상승", "솟구침"],
    "falling": ["fall", "falling", "drop", "내림", "떨어", "낙하", "비처럼"],
    "follow_or_attached": ["follow", "attached", "trail", "따라", "부착", "궤적", "검궤적", "검 궤적"],
    "swirl_or_vortex": ["swirl", "vortex", "spiral", "소용돌이", "회전", "나선"],
}


ROLE_MATERIAL_HINTS = {
    "ground_area": ["radial_shockwave", "additive_glow"],
    "lightning_arc": ["stylized_lightning", "additive_glow"],
    "spark_spray": ["spark_sprite", "additive_glow"],
    "smoke_volume": ["soft_smoke"],
    "fire_flame": ["fire_flipbook", "additive_glow"],
    "ribbon_trail": ["ribbon_slash", "additive_glow"],
    "impact_burst": ["additive_glow", "spark_sprite", "radial_shockwave"],
    "weather_loop": ["water_splash", "soft_smoke"],
}


ALLOWED_MATERIAL_OPERATIONS = {
    "reuse",
    "duplicate_material_instance",
    "create_from_stylized_master",
    "defer_until_material_analysis",
}


def is_material_instance_candidate(material_path: str) -> bool:
    name = material_path.rsplit("/", 1)[-1]
    lowered = material_path.casefold()
    return "/mi/" in lowered or name.startswith("MI_") or "_MI_" in name


def package_path_from_object_path(object_path: str) -> str:
    path = object_path.strip()
    if "." in path:
        path = path.split(".", 1)[0]
    return path


def asset_name_from_path(path: str) -> str:
    package = package_path_from_object_path(path)
    return package.rsplit("/", 1)[-1]


def object_path_from_package_path(path: str) -> str:
    package = package_path_from_object_path(path)
    name = asset_name_from_path(package)
    return f"{package}.{name}" if package else ""


def send_unreal_mcp_command(command: str, params: dict[str, Any], host: str, port: int, timeout: float = 30.0) -> dict[str, Any]:
    payload = {"type": command, "params": params}
    with socket.create_connection((host, port), timeout=2.0) as sock:
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
            except json.JSONDecodeError:
                continue
    raise RuntimeError(f"Unreal MCP command returned no complete JSON response: {command}")


def inspect_niagara_renderers(system_path: str, mode: str, host: str, port: int) -> dict[str, Any]:
    if mode == "off" or not system_path:
        return {
            "status": "disabled",
            "system_path": system_path,
            "renderers": [],
            "renderer_materials": [],
        }

    try:
        response = send_unreal_mcp_command(
            "inspect_niagara_renderers",
            {"system_path": object_path_from_package_path(system_path)},
            host,
            port,
        )
        if response.get("status") != "success":
            raise RuntimeError(json.dumps(response, ensure_ascii=False))
        result = response.get("result", {})
        return {
            "status": "success",
            "system_path": result.get("system_path", system_path),
            "emitter_count": result.get("emitter_count", 0),
            "renderer_count": result.get("renderer_count", 0),
            "renderers": result.get("renderers", []),
            "renderer_materials": renderer_materials_from_renderers(result.get("renderers", [])),
        }
    except Exception as exc:
        if mode == "required":
            raise
        return {
            "status": "unavailable",
            "system_path": system_path,
            "error": str(exc),
            "renderers": [],
            "renderer_materials": [],
        }


def inspect_niagara_stack(system_path: str, mode: str, host: str, port: int) -> dict[str, Any]:
    if mode == "off" or not system_path:
        return {
            "status": "disabled",
            "system_path": system_path,
            "emitters": [],
            "control_hints": [],
        }

    try:
        response = send_unreal_mcp_command(
            "inspect_niagara_stack",
            {
                "system_path": object_path_from_package_path(system_path),
                "include_pins": False,
                "max_function_calls": 120,
            },
            host,
            port,
            timeout=20.0,
        )
        if response.get("status") != "success":
            raise RuntimeError(json.dumps(response, ensure_ascii=False))
        return compact_stack_analysis(response.get("result", {}), system_path)
    except Exception as exc:
        if mode == "required":
            raise
        return {
            "status": "unavailable",
            "system_path": system_path,
            "error": str(exc),
            "emitters": [],
            "control_hints": [],
        }


def inspect_niagara_module_inputs(system_path: str, mode: str, host: str, port: int) -> dict[str, Any]:
    if mode == "off" or not system_path:
        return {
            "status": "disabled",
            "system_path": system_path,
            "emitters": [],
            "top_candidates": [],
        }

    try:
        response = send_unreal_mcp_command(
            "inspect_niagara_module_inputs",
            {
                "system_path": object_path_from_package_path(system_path),
                "include_linked_sources": True,
                "include_resolved_stack_inputs": True,
                "max_modules": 80,
                "max_candidates_per_module": 16,
                "max_resolved_inputs_per_module": 8,
                "max_top_candidates": 48,
            },
            host,
            port,
            timeout=20.0,
        )
        if response.get("status") != "success":
            raise RuntimeError(json.dumps(response, ensure_ascii=False))
        return compact_module_input_analysis(response.get("result", {}), system_path)
    except Exception as exc:
        if mode == "required":
            raise
        return {
            "status": "unavailable",
            "system_path": system_path,
            "error": str(exc),
            "emitters": [],
            "top_candidates": [],
        }


def compact_module_input_analysis(result: dict[str, Any], fallback_system_path: str) -> dict[str, Any]:
    top_candidates = []
    resolved_input_examples = []
    control_kinds: list[str] = []
    module_names: list[str] = []
    emitter_names: list[str] = []

    for candidate in result.get("top_candidates", [])[:48]:
        compact_candidate = {
            "emitter_name": candidate.get("emitter_name", ""),
            "module_name": candidate.get("module_name", ""),
            "pin_name": candidate.get("pin_name", ""),
            "control_kind": candidate.get("control_kind", "unknown"),
            "priority": candidate.get("priority", 0),
            "default_value": candidate.get("default_value", ""),
            "default_object": candidate.get("default_object", ""),
            "linked_to_count": candidate.get("linked_to_count", 0),
            "can_author_now": candidate.get("can_author_now", False),
        }
        top_candidates.append(compact_candidate)
        if compact_candidate["control_kind"] not in control_kinds:
            control_kinds.append(compact_candidate["control_kind"])
        if compact_candidate["module_name"] and compact_candidate["module_name"] not in module_names:
            module_names.append(compact_candidate["module_name"])
        if compact_candidate["emitter_name"] and compact_candidate["emitter_name"] not in emitter_names:
            emitter_names.append(compact_candidate["emitter_name"])

    for emitter in result.get("emitters", []):
        for module in emitter.get("modules", []):
            resolved_inputs = module.get("resolved_stack_inputs", [])
            if not resolved_inputs:
                continue
            resolved_input_examples.append(
                {
                    "emitter_name": emitter.get("name", ""),
                    "module_name": module.get("function_name", ""),
                    "resolved_stack_inputs": resolved_inputs[:6],
                }
            )
            if len(resolved_input_examples) >= 16:
                break
        if len(resolved_input_examples) >= 16:
            break

    return {
        "status": "success",
        "system_path": result.get("system_path", fallback_system_path),
        "include_resolved_stack_inputs": result.get("include_resolved_stack_inputs", False),
        "emitter_count": result.get("emitter_count", 0),
        "module_count": result.get("module_count", 0),
        "candidate_count": result.get("candidate_count", 0),
        "top_candidate_count": result.get("top_candidate_count", 0),
        "can_author_module_inputs": result.get("can_author_module_inputs", False),
        "authoring_status": result.get("authoring_status", ""),
        "control_kinds": control_kinds,
        "candidate_modules": module_names,
        "candidate_emitters": emitter_names,
        "top_candidates": top_candidates,
        "resolved_input_examples": resolved_input_examples,
    }


def compact_stack_analysis(result: dict[str, Any], fallback_system_path: str) -> dict[str, Any]:
    emitters = []
    all_hints: list[str] = []
    scratch_pad_sources = []
    for emitter in result.get("emitters", []):
        graph = emitter.get("graph", {})
        hints = list(dict.fromkeys(graph.get("control_hints", [])))
        for hint in hints:
            if hint not in all_hints:
                all_hints.append(hint)

        function_names = [
            function.get("function_name", "")
            for function in graph.get("function_calls", [])[:24]
            if function.get("function_name")
        ]
        scratch_pads = emitter.get("scratch_pad_scripts", [])
        if scratch_pads:
            scratch_pad_sources.append(emitter.get("name", ""))

        emitters.append(
            {
                "name": emitter.get("name", ""),
                "enabled": emitter.get("enabled", False),
                "function_call_count": graph.get("function_call_count", 0),
                "input_node_count": graph.get("input_node_count", 0),
                "output_node_count": graph.get("output_node_count", 0),
                "control_hints": hints,
                "scratch_pad_count": len(scratch_pads),
                "parent_scratch_pad_count": len(emitter.get("parent_scratch_pad_scripts", [])),
                "top_function_names": function_names,
            }
        )

    return {
        "status": "success",
        "system_path": result.get("system_path", fallback_system_path),
        "emitter_count": result.get("emitter_count", 0),
        "system_script_count": result.get("system_script_count", 0),
        "system_scratch_pad_count": result.get("system_scratch_pad_count", 0),
        "total_scratch_pad_count": result.get("total_scratch_pad_count", 0),
        "total_emitter_function_call_count": result.get("total_emitter_function_call_count", 0),
        "control_hints": all_hints,
        "scratch_pad_sources": scratch_pad_sources,
        "emitters": emitters,
    }


def renderer_materials_from_renderers(renderers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}
    for renderer in renderers:
        candidates = []
        primary = renderer.get("primary_material", "")
        if primary:
            candidates.append(primary)
        candidates.extend(renderer.get("used_materials", []))
        for override in renderer.get("override_materials", []):
            explicit = override.get("explicit_material", "")
            if explicit:
                candidates.append(explicit)

        for material_path in candidates:
            if not material_path:
                continue
            object_path = object_path_from_package_path(material_path)
            entry = by_path.setdefault(
                object_path,
                {
                    "material_path": object_path,
                    "source_kind": "renderer_bound",
                    "renderer_classes": [],
                    "renderer_bindings": [],
                },
            )
            renderer_class = renderer.get("renderer_class", "")
            if renderer_class and renderer_class not in entry["renderer_classes"]:
                entry["renderer_classes"].append(renderer_class)
            binding = {
                "emitter_name": renderer.get("emitter_name", ""),
                "emitter_index": renderer.get("emitter_index", -1),
                "renderer_index": renderer.get("renderer_index", -1),
                "renderer_class": renderer_class,
            }
            if binding not in entry["renderer_bindings"]:
                entry["renderer_bindings"].append(binding)

    return sorted(by_path.values(), key=lambda item: item["material_path"])


def repo_root_from(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "StylizedCubeless.uproject").exists():
            return candidate
    return current


def contains_any(prompt: str, terms: list[str]) -> bool:
    lowered = prompt.casefold()
    return any(term.casefold() in lowered for term in terms)


def detect_tags(prompt: str, table: dict[str, list[str]]) -> list[str]:
    return sorted(tag for tag, terms in table.items() if contains_any(prompt, terms))


def detect_duration(prompt: str) -> float | None:
    patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:sec|secs|second|seconds|s)\b",
        r"(\d+(?:\.\d+)?)\s*초",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def slugify(text: str, fallback: str = "niagara_recipe") -> str:
    romanized_hints = {
        "붉": "red",
        "빨": "red",
        "푸": "blue",
        "파": "blue",
        "번개": "lightning",
        "장판": "field",
        "검": "sword",
        "궤적": "trail",
        "연기": "smoke",
        "안개": "fog",
        "화염": "fire",
        "불": "fire",
        "독": "poison",
    }
    expanded = text
    for needle, replacement in romanized_hints.items():
        expanded = expanded.replace(needle, f" {replacement} ")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", expanded).strip("_")
    return (slug or fallback)[:64]


def prompt_match_keywords(prompt: str, roles: list[str], materials: list[str], motions: list[str]) -> list[str]:
    lowered = prompt.casefold()
    keywords: list[str] = []
    keyword_rules = {
        "sword": ["sword", "blade", "검", "검기", "검궤적", "검 궤적"],
        "trail": ["trail", "ribbon", "animtrail", "궤적", "잔상"],
        "slash": ["slash", "swing", "베기", "참격"],
        "hit": ["hit", "impact", "타격", "히트"],
        "shockwave": ["shockwave", "충격파", "파동"],
        "smoke": ["smoke", "fog", "mist", "연기", "안개"],
        "fire": ["fire", "flame", "burn", "불", "화염", "불꽃"],
        "lightning": ["lightning", "electric", "전기", "번개", "전격"],
        "spark": ["spark", "ember", "스파크", "불티"],
    }
    for keyword, terms in keyword_rules.items():
        if any(term in lowered for term in terms):
            keywords.append(keyword)
    if "ribbon_trail" in roles:
        keywords.extend(["trail", "ribbon"])
    if "ribbon_slash" in materials:
        keywords.append("slash")
    if "follow_or_attached" in motions:
        keywords.append("trail")
    return sorted(set(keywords))


def searchable_text(parts: list[Any]) -> str:
    tokens: list[str] = []
    for part in parts:
        if isinstance(part, list):
            tokens.extend(str(item) for item in part)
        elif part is not None:
            tokens.append(str(part))
    return " ".join(tokens).casefold()


def score_prompt_keywords(asset: dict[str, Any], prompt_keywords: list[str]) -> float:
    if not prompt_keywords:
        return 0.0

    identity_blob = searchable_text(
        [
            asset.get("object_path", ""),
            asset.get("package", ""),
            asset.get("display_name", ""),
            asset.get("search_terms", []),
            asset.get("asset_tokens", []),
        ]
    )
    role_blob = searchable_text(
        [
            asset.get("visual_roles", []),
            asset.get("material_roles", []),
            asset.get("motion_hints", []),
            asset.get("style_profiles", []),
        ]
    )
    material_blob = searchable_text([asset.get("source_materials", []), asset.get("source_meshes", [])])

    score = 0.0
    for keyword in prompt_keywords:
        if keyword in identity_blob:
            score += 12.0
        if keyword in role_blob:
            score += 5.0
        if keyword in material_blob:
            score += 2.0
    if "sword" in prompt_keywords and "trail" in prompt_keywords:
        if "swordtrail" in identity_blob or ("sword" in identity_blob and "trail" in identity_blob):
            score += 18.0
        elif "swordtrail" in material_blob:
            score += 4.0
    return score


def score_signature(asset: dict[str, Any], desired_roles: list[str], motions: list[str], prompt_keywords: list[str]) -> float:
    score = 0.0
    roles = set(asset.get("visual_roles", []))
    motion_hints = set(asset.get("motion_hints", []))
    usable = set(asset.get("usable_as", []))
    materials = asset.get("source_materials", [])
    score += len(roles.intersection(desired_roles)) * 25.0
    score += len(motion_hints.intersection(motions)) * 8.0
    score += score_prompt_keywords(asset, prompt_keywords)
    score += len(materials) * 0.3
    if "primary_template" in usable:
        score += 12.0
    if "support_layer" in usable:
        score += 5.0
    if asset.get("confidence") == "medium":
        score += 4.0
    return round(score, 3)


def choose_sources(
    signatures: list[dict[str, Any]],
    desired_roles: list[str],
    motions: list[str],
    prompt_keywords: list[str],
) -> list[dict[str, Any]]:
    candidates = []
    for asset in signatures:
        score = score_signature(asset, desired_roles, motions, prompt_keywords)
        if score <= 0:
            continue
        item = dict(asset)
        item["recipe_score"] = score
        candidates.append(item)
    candidates.sort(key=lambda item: (-item["recipe_score"], item.get("object_path", "")))
    return candidates


def score_material(material: dict[str, Any], desired_material_roles: list[str], source_styles: list[str]) -> float:
    roles = set(material.get("material_roles", []))
    styles = set(material.get("style_profiles", []))
    score = len(roles.intersection(desired_material_roles)) * 20.0
    score += len(styles.intersection(source_styles)) * 4.0
    score += min(material.get("used_by_count", 0), 20) * 0.2
    if material.get("recommended_operation") == "duplicate_material_instance":
        score += 4.0
    if material.get("confidence") == "medium":
        score += 2.0
    return round(score, 3)


def choose_materials(materials: list[dict[str, Any]], desired_material_roles: list[str], source_styles: list[str]) -> list[dict[str, Any]]:
    candidates = []
    for material in materials:
        score = score_material(material, desired_material_roles, source_styles)
        if score <= 0:
            continue
        item = dict(material)
        item["recipe_score"] = score
        candidates.append(item)
    candidates.sort(key=lambda item: (-item["recipe_score"], item.get("material_path", "")))
    return candidates


def infer_material_roles(roles: list[str], detected_material_roles: list[str]) -> list[str]:
    inferred = list(detected_material_roles)
    for role in roles:
        for material_role in ROLE_MATERIAL_HINTS.get(role, []):
            if material_role not in inferred:
                inferred.append(material_role)
    return inferred or ["additive_glow"]


def build_layers(sources: list[dict[str, Any]], desired_roles: list[str]) -> list[dict[str, Any]]:
    layers = []
    if not sources:
        return [
            {
                "role": "missing_primary",
                "operation": "defer_until_api_available",
                "source": "",
                "notes": ["No structural signature source matched the request."],
            }
        ]

    primary = next((item for item in sources if "primary_template" in item.get("usable_as", [])), sources[0])
    layers.append(
        {
            "role": "primary_template",
            "operation": "duplicate_system",
            "source": primary["object_path"],
            "notes": [
                f"Matched roles: {', '.join([role for role in primary.get('visual_roles', []) if role in desired_roles]) or 'inferred closest source'}",
                f"Confidence: {primary.get('confidence', 'unknown')}",
            ],
        }
    )

    seen = {primary["object_path"]}
    for source in sources:
        if source["object_path"] in seen:
            continue
        if len(layers) >= 5:
            break
        operation = "duplicate_emitter" if "support_layer" in source.get("usable_as", []) else "reuse_source_as_reference"
        layers.append(
            {
                "role": "support_layer",
                "operation": operation,
                "source": source["object_path"],
                "notes": [
                    f"Visual roles: {', '.join(source.get('visual_roles', []))}",
                    "Actual emitter merge waits for a Niagara edit API; use as a reference until then.",
                ],
            }
        )
        seen.add(source["object_path"])
    return layers


def normalize_material_operation(operation: str) -> str:
    if operation in ALLOWED_MATERIAL_OPERATIONS:
        return operation
    if operation in {"reuse_or_create_instance", "inspect_before_use"}:
        return "duplicate_material_instance"
    return "defer_until_material_analysis"


def color_parameter_overrides(colors: list[str]) -> dict[str, Any]:
    if not colors:
        return {}
    return {
        "User.Gen_ColorName": colors[0],
        "note": "Use this as a generator-owned color intent until material parameter names are inspected.",
    }


def build_material_plan(
    materials: list[dict[str, Any]],
    colors: list[str],
    renderer_materials: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    plan = []
    seen: set[str] = set()

    for material in (renderer_materials or [])[:32]:
        source_material = object_path_from_package_path(material["material_path"])
        operation = "duplicate_material_instance" if is_material_instance_candidate(source_material) else "reuse"
        plan.append(
            {
                "role": "renderer_bound:" + ",".join(material.get("renderer_classes", [])),
                "operation": operation,
                "source_material": source_material,
                "target_material": "",
                "source_kind": "renderer_bound",
                "renderer_bindings": material.get("renderer_bindings", []),
                "parameter_overrides": color_parameter_overrides(colors),
            }
        )
        seen.add(source_material.casefold())

    for material in materials[:8]:
        source_material = material["material_path"]
        source_object_path = object_path_from_package_path(source_material)
        if source_object_path.casefold() in seen:
            continue
        operation = normalize_material_operation(material.get("recommended_operation", "reuse"))
        if is_material_instance_candidate(source_material):
            operation = "duplicate_material_instance"
        plan.append(
            {
                "role": ",".join(material.get("material_roles", [])),
                "operation": operation,
                "source_material": source_object_path,
                "target_material": "",
                "source_kind": "style_variant",
                "renderer_bindings": [],
                "parameter_overrides": color_parameter_overrides(colors),
            }
        )
        seen.add(source_object_path.casefold())
    if not plan:
        plan.append(
            {
                "role": "missing_material_style",
                "operation": "defer_until_material_analysis",
                "source_material": "",
                "target_material": "",
                "source_kind": "missing",
                "renderer_bindings": [],
                "parameter_overrides": {},
            }
        )
    return plan


def build_user_parameters(colors: list[str], duration: float | None) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if colors:
        params["User.Gen_ColorName"] = colors[0]
    if duration is not None:
        params["User.Gen_Duration"] = duration
    params["User.Gen_ReviewMap"] = REVIEW_MAP
    return params


def build_generation_plan(
    layers: list[dict[str, Any]],
    material_plan: list[dict[str, Any]],
    slug: str,
    colors: list[str],
    duration: float | None,
    module_input_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    can_execute_now = []
    blocked_by_api = []

    for layer in layers:
        operation = layer.get("operation")
        if operation == "duplicate_system":
            can_execute_now.append(
                {
                    "step": "duplicate_primary_system_to_temp",
                    "source": layer.get("source", ""),
                    "target": f"{TEMP_ROOT}/{slug}/NS_{slug}",
                }
            )
        elif operation in {"duplicate_emitter", "add_primitive"}:
            blocked_by_api.append(
                {
                    "step": operation,
                    "source": layer.get("source", ""),
                    "missing_api": "Niagara emitter stack/module authoring API",
                }
            )
        elif operation == "defer_until_api_available":
            blocked_by_api.append(
                {
                    "step": "select_or_create_primary_template",
                    "source": layer.get("source", ""),
                    "missing_api": "Inspector-backed primitive/template selection",
                }
            )

    if any(item.get("operation") == "duplicate_material_instance" for item in material_plan):
        can_execute_now.append(
            {
                "step": "duplicate_candidate_material_instances",
                "source": "material_plan",
                "target": f"{TEMP_ROOT}/{slug}/Materials",
            }
        )
        can_execute_now.append(
            {
                "step": "bind_duplicated_materials_to_matching_renderers",
                "source": "material_plan",
                "target": f"{TEMP_ROOT}/{slug}/NS_{slug}",
                "requires_mcp_command": "set_niagara_renderer_material",
                "execution_mode": "external_socket_after_unreal_python_duplication",
            }
        )

    if build_user_parameters(colors, duration):
        can_execute_now.append(
            {
                "step": "apply_matching_user_parameter_overrides",
                "source": "user_parameters",
                "target": f"{TEMP_ROOT}/{slug}/NS_{slug}",
                "requires_mcp_command": "set_niagara_user_parameter",
                "execution_mode": "external_socket_after_unreal_python_duplication",
                "rule": "Only set existing exposed User.* parameters on generated temp systems when type and name hints match the request intent.",
            }
        )

    module_inputs_available = bool(
        module_input_analysis
        and module_input_analysis.get("status") == "success"
        and module_input_analysis.get("include_resolved_stack_inputs", False)
        and module_input_analysis.get("resolved_input_examples", [])
    )
    if module_inputs_available and (colors or duration is not None):
        can_execute_now.append(
            {
                "step": "apply_matching_module_input_overrides",
                "source": "module_input_analysis",
                "target": f"{TEMP_ROOT}/{slug}/NS_{slug}",
                "requires_mcp_command": "set_niagara_module_input_value",
                "execution_mode": "external_socket_after_unreal_python_duplication",
                "rule": "Only set existing RapidIteration module inputs on generated temp systems when name/type hints match the request intent.",
            }
        )

    return {
        "target_system": f"{TEMP_ROOT}/{slug}/NS_{slug}",
        "can_execute_now": can_execute_now,
        "blocked_by_api": blocked_by_api,
        "preview_after_generation": {
            "tool": "Niagara Preview Player",
            "fallback_tool": "Niagara Preview Lab",
            "rule": "Open the generated temp system in Preview Player first; use Preview Lab screenshots for review gates.",
        },
        "promotion_gate": "Only after Ieta visual/material/BP-user-parameter review passes, duplicate or move to /Game/Cubeless/FX/Generated.",
    }


def build_risk_notes(
    sources: list[dict[str, Any]],
    renderer_analysis: dict[str, Any] | None = None,
    stack_analysis: dict[str, Any] | None = None,
    module_input_analysis: dict[str, Any] | None = None,
) -> list[str]:
    risk_notes = [
        "Recipe is no-C++ and inference-based.",
        "Original source assets are read-only.",
        "Emitter add/remove and Scratch Pad reuse require future Niagara edit APIs.",
        "User parameter overrides are limited to existing exposed User.* parameters on generated temp systems.",
    ]
    if renderer_analysis:
        status = renderer_analysis.get("status", "unknown")
        if status == "success":
            risk_notes.append(
                f"Renderer inspect succeeded: {renderer_analysis.get('renderer_count', 0)} renderers and {len(renderer_analysis.get('renderer_materials', []))} unique renderer materials."
            )
        elif status == "unavailable":
            risk_notes.append(f"Renderer inspect unavailable; material plan fell back to style index. Reason: {renderer_analysis.get('error', '')}")
    if stack_analysis:
        status = stack_analysis.get("status", "unknown")
        if status == "success":
            risk_notes.append(
                f"Stack inspect succeeded: {stack_analysis.get('emitter_count', 0)} emitters, {stack_analysis.get('total_emitter_function_call_count', 0)} function calls, {stack_analysis.get('total_scratch_pad_count', 0)} scratch pads."
            )
        elif status == "unavailable":
            risk_notes.append(f"Stack inspect unavailable; module/Scratch Pad hints are missing. Reason: {stack_analysis.get('error', '')}")
    if module_input_analysis:
        status = module_input_analysis.get("status", "unknown")
        if status == "success":
            risk_notes.append(
                f"Module input inspect succeeded: {module_input_analysis.get('candidate_count', 0)} candidates. Authoring enabled: {module_input_analysis.get('can_author_module_inputs', False)}."
            )
        elif status == "unavailable":
            risk_notes.append(f"Module input inspect unavailable; exact module-input candidates are missing. Reason: {module_input_analysis.get('error', '')}")
    for source in sources[:5]:
        if source.get("bp_linkage_hints"):
            risk_notes.append(f"BP linkage hint on {source['object_path']}: {', '.join(source['bp_linkage_hints'])}")
        if source.get("scratch_pad_hints"):
            risk_notes.append(f"Scratch Pad not deeply inspected on {source['object_path']}.")
    return risk_notes


def build_recipe(
    prompt: str,
    signatures: dict[str, Any],
    material_index: dict[str, Any],
    output_name: str | None,
    renderer_inspect_mode: str = "auto",
    stack_inspect_mode: str = "auto",
    module_input_inspect_mode: str = "auto",
    unreal_mcp_host: str = UNREAL_MCP_HOST,
    unreal_mcp_port: int = UNREAL_MCP_PORT,
) -> dict[str, Any]:
    desired_roles = detect_tags(prompt, ROLE_TERMS) or ["unknown_visual_role"]
    detected_material_roles = detect_tags(prompt, MATERIAL_TERMS)
    material_roles = infer_material_roles(desired_roles, detected_material_roles)
    colors = detect_tags(prompt, COLOR_TERMS)
    motions = detect_tags(prompt, MOTION_TERMS)
    duration = detect_duration(prompt)
    prompt_keywords = prompt_match_keywords(prompt, desired_roles, material_roles, motions)
    sources = choose_sources(signatures.get("assets", []), desired_roles, motions, prompt_keywords)
    source_styles = sorted({style for source in sources[:5] for style in source.get("style_profiles", [])})
    materials = choose_materials(material_index.get("materials", []), material_roles, source_styles)
    slug = output_name or slugify(prompt)
    layers = build_layers(sources, desired_roles)
    primary_source = layers[0].get("source", "") if layers else ""
    renderer_analysis = inspect_niagara_renderers(
        primary_source,
        renderer_inspect_mode,
        unreal_mcp_host,
        unreal_mcp_port,
    )
    stack_analysis = inspect_niagara_stack(
        primary_source,
        stack_inspect_mode,
        unreal_mcp_host,
        unreal_mcp_port,
    )
    module_input_analysis = inspect_niagara_module_inputs(
        primary_source,
        module_input_inspect_mode,
        unreal_mcp_host,
        unreal_mcp_port,
    )
    material_plan = build_material_plan(materials, colors, renderer_analysis.get("renderer_materials", []))

    return {
        "schema_version": 1,
        "request": prompt,
        "parsed_intent": {
            "visual_roles": desired_roles,
            "material_roles": material_roles,
            "colors": colors,
            "motions": motions,
            "duration_seconds": duration,
            "source_match_keywords": prompt_keywords,
        },
        "write_scope": {
            "temporary_root": f"{TEMP_ROOT}/{slug}",
            "production_root": PRODUCTION_ROOT,
            "source_policy": "Original Niagara, Material, Blueprint, Texture, and Mesh assets are read-only references.",
        },
        "reference_analysis": {
            "primary_sources": [source["object_path"] for source in sources[:3]],
            "support_sources": [source["object_path"] for source in sources[3:10]],
            "material_sources": [material["material_path"] for material in materials[:10]],
            "renderer_material_sources": [
                material["material_path"]
                for material in renderer_analysis.get("renderer_materials", [])
            ],
            "stack_control_hints": stack_analysis.get("control_hints", []),
            "module_input_control_candidates": module_input_analysis.get("top_candidates", []),
            "module_input_control_kinds": module_input_analysis.get("control_kinds", []),
            "bp_linkage_sources": [
                source["object_path"]
                for source in sources[:10]
                if source.get("bp_linkage_hints")
            ],
            "scratch_pad_sources": [
                source["object_path"]
                for source in sources[:10]
                if source.get("scratch_pad_hints")
            ] + stack_analysis.get("scratch_pad_sources", []),
            "risk_notes": build_risk_notes(sources, renderer_analysis, stack_analysis, module_input_analysis),
        },
        "renderer_analysis": renderer_analysis,
        "stack_analysis": stack_analysis,
        "module_input_analysis": module_input_analysis,
        "layers": layers,
        "material_plan": material_plan,
        "user_parameters": build_user_parameters(colors, duration),
        "generation_plan": build_generation_plan(layers, material_plan, slug, colors, duration, module_input_analysis),
        "validation": {
            "required_checks": [
                "load_generated_asset",
                "compile_or_collect_compile_status",
                "verify_no_source_asset_dirty",
                "verify_niagara_preview_lab_map_without_same_session_reload",
                "spawn_preview_actor_in_niagara_preview_lab",
                "capture_one_quick_preview_from_first_reviewable_bookmark",
                "capture_frame_sequence_for_timing_sensitive_effects",
            ],
            "review_map": REVIEW_MAP,
            "preview_system": "Niagara Preview Player first, Niagara Preview Lab for gated screenshots",
            "camera_bookmarks": {
                "1": "near",
                "2": "mid",
                "3": "far",
            },
            "quick_preview_fallback": ["1", "2", "3"],
            "quick_preview_rule": "Capture one screenshot by default. Start at bookmark 1. If the effect is too large, clipped, invisible, or not reviewable, use bookmark 2. If bookmark 2 still fails, use bookmark 3 and record the selected bookmark. Capture all three only for explicit distance comparison.",
            "video_review_rule": "For timing-sensitive Niagara such as sword trails or slash ribbons, capture a PNG frame sequence first. Convert to video only after the frame sequence is verified.",
            "map_reload_safety_rule": "Niagara Preview Lab must not reload the review map from the same Unreal Python session after preview actors or world references exist. Reuse the loaded map, delete preview actors by prefix, and restart Unreal if a full reset is needed.",
            "preview_frames_seconds": [0.5, 1.0, duration if duration else 2.0],
            "review_gate": "Ieta reviews request match, stylized readability, BP/User parameter safety, material fit, selected bookmark screenshot, and timing frame sequence when needed before production promotion.",
        },
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_prompt_text(text: str) -> str:
    return text.lstrip("\ufeff").strip()


def configure_stdout_utf8() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a first-pass generative Niagara recipe from structural and material indices.")
    parser.add_argument("prompt", nargs="?", default=None)
    parser.add_argument("--prompt-file", type=Path, default=None)
    parser.add_argument("--signature-index", type=Path, default=None)
    parser.add_argument("--material-index", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--output-name", default=None)
    parser.add_argument("--renderer-inspect-mode", choices=["auto", "off", "required"], default="auto")
    parser.add_argument("--stack-inspect-mode", choices=["auto", "off", "required"], default="auto")
    parser.add_argument("--module-input-inspect-mode", choices=["auto", "off", "required"], default="auto")
    parser.add_argument("--unreal-mcp-host", default=UNREAL_MCP_HOST)
    parser.add_argument("--unreal-mcp-port", type=int, default=UNREAL_MCP_PORT)
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def main() -> int:
    configure_stdout_utf8()
    args = parse_args()
    if args.prompt_file:
        prompt = normalize_prompt_text(args.prompt_file.read_text(encoding="utf-8-sig"))
    elif args.prompt:
        prompt = normalize_prompt_text(args.prompt)
    else:
        raise SystemExit("Provide a prompt argument or --prompt-file.")

    root = repo_root_from(Path.cwd())
    signature_path = args.signature_index or root / DEFAULT_SIGNATURE_INDEX
    material_path = args.material_index or root / DEFAULT_MATERIAL_INDEX
    output_dir = args.output_dir or root / DEFAULT_OUTPUT_DIR
    recipe = build_recipe(
        prompt,
        load_json(signature_path),
        load_json(material_path),
        args.output_name,
        renderer_inspect_mode=args.renderer_inspect_mode,
        stack_inspect_mode=args.stack_inspect_mode,
        module_input_inspect_mode=args.module_input_inspect_mode,
        unreal_mcp_host=args.unreal_mcp_host,
        unreal_mcp_port=args.unreal_mcp_port,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    slug = args.output_name or slugify(prompt)
    output_path = output_dir / f"{slug}_generation_recipe.json"
    output_path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.print_json:
        print(json.dumps(recipe, ensure_ascii=False, indent=2))
    else:
        print(f"Recipe: {output_path}")
        print(f"Primary: {recipe['layers'][0]['source'] if recipe['layers'] else 'NONE'}")
        print(f"Roles: {', '.join(recipe['parsed_intent']['visual_roles'])}")
        print(f"Materials: {', '.join(recipe['parsed_intent']['material_roles'])}")
        print(f"Can execute now: {len(recipe['generation_plan']['can_execute_now'])}")
        print(f"Blocked by API: {len(recipe['generation_plan']['blocked_by_api'])}")
        print(f"Renderer inspect: {recipe.get('renderer_analysis', {}).get('status', 'missing')}")
        print(f"Stack inspect: {recipe.get('stack_analysis', {}).get('status', 'missing')}")
        print(f"Module input inspect: {recipe.get('module_input_analysis', {}).get('status', 'missing')}")
        print(f"Preview system: {recipe['validation']['preview_system']}")
        print(f"Review map: {recipe['validation']['review_map']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
