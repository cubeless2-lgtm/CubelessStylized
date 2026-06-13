"""Tune native PCG forest road materials for visual QA.

The native road graph is already functionally validated. This pass keeps the
graph topology and spline mesh counts stable, and only rewrites the three road
materials used by the graph:

- core: very rough low-saturation dirt with procedural color variation
- shoulder: muted earth/green edge kept opaque for stable landscape depth
- duff: green-brown outer blend into the forest floor kept opaque for stable landscape depth
"""

import json
import os
import time

import unreal


REPORT_NAME = "CubelessForestRoadMaterialFinalTuning.json"

MATERIAL_SPECS = {
    "/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_ForestRoad_Core": {
        "label": "core",
        "blend": "opaque",
        "base_a": (0.016, 0.014, 0.011, 1.0),
        "base_b": (0.038, 0.030, 0.020, 1.0),
        "edge_color": (0.035, 0.044, 0.023, 1.0),
        "edge_blend_min": 0.48,
        "edge_blend_max": 0.98,
        "noise_scale": 22.0,
        "noise_levels": 5,
        "roughness": 0.995,
        "specular": 0.003,
        "emissive": None,
    },
    "/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_ForestRoad_Shoulder": {
        "label": "shoulder",
        "blend": "opaque",
        "base_a": (0.018, 0.030, 0.016, 1.0),
        "base_b": (0.035, 0.044, 0.023, 1.0),
        "edge_color": (0.040, 0.080, 0.020, 1.0),
        "edge_blend_min": 0.34,
        "edge_blend_max": 0.94,
        "noise_scale": 34.0,
        "noise_levels": 4,
        "roughness": 0.995,
        "specular": 0.003,
        "emissive": None,
    },
    "/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_ForestRoad_Duff": {
        "label": "duff",
        "blend": "opaque",
        "base_a": (0.015, 0.040, 0.014, 1.0),
        "base_b": (0.026, 0.055, 0.020, 1.0),
        "edge_color": (0.045, 0.100, 0.025, 1.0),
        "edge_blend_min": 0.18,
        "edge_blend_max": 0.88,
        "noise_scale": 38.0,
        "noise_levels": 4,
        "roughness": 0.995,
        "specular": 0.003,
        "emissive": None,
    },
}


def _asset_path_to_object_path(path):
    name = path.rsplit("/", 1)[-1]
    return path + "." + name


def _load_material(path):
    material = unreal.EditorAssetLibrary.load_asset(path)
    if not material:
        material = unreal.load_object(None, _asset_path_to_object_path(path))
    return material


def _expr(material, cls, x, y):
    return unreal.MaterialEditingLibrary.create_material_expression(material, cls, x, y)


def _constant(material, value, x, y):
    node = _expr(material, unreal.MaterialExpressionConstant, x, y)
    node.set_editor_property("r", float(value))
    return node


def _constant3(material, value, x, y):
    node = _expr(material, unreal.MaterialExpressionConstant3Vector, x, y)
    node.set_editor_property("constant", unreal.LinearColor(*value))
    return node


def _connect(src, dst, dst_input, src_output=""):
    return bool(
        unreal.MaterialEditingLibrary.connect_material_expressions(
            src, src_output, dst, dst_input
        )
    )


def _connect_prop(src, prop, src_output=""):
    return bool(unreal.MaterialEditingLibrary.connect_material_property(src, src_output, prop))


def _noise01(material, spec, x, y):
    noise = _expr(material, unreal.MaterialExpressionNoise, x, y)
    for prop, value in (
        ("scale", float(spec["noise_scale"])),
        ("levels", int(spec["noise_levels"])),
        ("quality", 2),
        ("output_min", 0.0),
        ("output_max", 1.0),
    ):
        try:
            noise.set_editor_property(prop, value)
        except Exception:
            pass
    return noise


def _color_variation(material, spec):
    dark = _constant3(material, spec["base_a"], -760, -160)
    light = _constant3(material, spec["base_b"], -760, 20)
    noise = _noise01(material, spec, -760, 200)
    color = _expr(material, unreal.MaterialExpressionLinearInterpolate, -440, -60)
    _connect(dark, color, "A")
    _connect(light, color, "B")
    _connect(noise, color, "Alpha")
    return color


def _edge_distance_alpha(material, spec):
    texcoord = _expr(material, unreal.MaterialExpressionTextureCoordinate, -1180, 440)
    mask_v = _expr(material, unreal.MaterialExpressionComponentMask, -1000, 440)
    mask_v.set_editor_property("r", False)
    mask_v.set_editor_property("g", True)
    mask_v.set_editor_property("b", False)
    mask_v.set_editor_property("a", False)
    _connect(texcoord, mask_v, "")

    minus_half = _constant(material, -0.5, -1000, 580)
    centered = _expr(material, unreal.MaterialExpressionAdd, -800, 500)
    _connect(mask_v, centered, "A")
    _connect(minus_half, centered, "B")

    abs_centered = _expr(material, unreal.MaterialExpressionAbs, -600, 500)
    _connect(centered, abs_centered, "")

    two = _constant(material, 2.0, -600, 640)
    edge_distance = _expr(material, unreal.MaterialExpressionMultiply, -400, 520)
    _connect(abs_centered, edge_distance, "A")
    _connect(two, edge_distance, "B")

    fade_min = _constant(material, spec["edge_blend_min"], -400, 680)
    fade_max = _constant(material, spec["edge_blend_max"], -400, 820)
    smooth = _expr(material, unreal.MaterialExpressionSmoothStep, -180, 580)
    _connect(fade_min, smooth, "Min")
    _connect(fade_max, smooth, "Max")
    _connect(edge_distance, smooth, "Value")
    return smooth


def _road_surface_color(material, spec):
    inner_color = _color_variation(material, spec)
    if not spec.get("edge_color"):
        return inner_color

    edge_color = _constant3(material, spec["edge_color"], -180, 120)
    edge_alpha = _edge_distance_alpha(material, spec)
    color = _expr(material, unreal.MaterialExpressionLinearInterpolate, 80, 40)
    _connect(inner_color, color, "A")
    _connect(edge_color, color, "B")
    _connect(edge_alpha, color, "Alpha")
    return color


def _edge_opacity(material, spec):
    texcoord = _expr(material, unreal.MaterialExpressionTextureCoordinate, -1000, 420)
    mask_v = _expr(material, unreal.MaterialExpressionComponentMask, -820, 420)
    mask_v.set_editor_property("r", False)
    mask_v.set_editor_property("g", True)
    mask_v.set_editor_property("b", False)
    mask_v.set_editor_property("a", False)
    _connect(texcoord, mask_v, "")

    minus_half = _constant(material, -0.5, -820, 560)
    centered = _expr(material, unreal.MaterialExpressionAdd, -620, 480)
    _connect(mask_v, centered, "A")
    _connect(minus_half, centered, "B")

    abs_centered = _expr(material, unreal.MaterialExpressionAbs, -420, 480)
    _connect(centered, abs_centered, "")

    two = _constant(material, 2.0, -420, 620)
    edge_distance = _expr(material, unreal.MaterialExpressionMultiply, -220, 500)
    _connect(abs_centered, edge_distance, "A")
    _connect(two, edge_distance, "B")

    fade_min = _constant(material, spec["fade_min"], -220, 660)
    fade_max = _constant(material, spec["fade_max"], -220, 800)
    smooth = _expr(material, unreal.MaterialExpressionSmoothStep, 0, 560)
    _connect(fade_min, smooth, "Min")
    _connect(fade_max, smooth, "Max")
    _connect(edge_distance, smooth, "Value")

    one_minus = _expr(material, unreal.MaterialExpressionOneMinus, 220, 560)
    _connect(smooth, one_minus, "")

    opacity_scalar = _constant(material, spec["opacity"], 220, 720)
    opacity = _expr(material, unreal.MaterialExpressionMultiply, 460, 600)
    _connect(one_minus, opacity, "A")
    _connect(opacity_scalar, opacity, "B")
    return opacity


def _set_common_material_properties(material, spec):
    material.set_editor_property("two_sided", True)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    if spec["blend"] == "translucent_edge":
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    try:
        material.set_editor_property("use_material_attributes", False)
    except Exception:
        pass


def _build_material(path, spec):
    material = _load_material(path)
    if not material:
        return {"path": path, "label": spec["label"], "applied": False, "reason": "missing"}
    if material.get_class().get_name() != "Material":
        return {
            "path": path,
            "label": spec["label"],
            "applied": False,
            "reason": "not_material",
            "class": material.get_class().get_name(),
        }

    lib = unreal.MaterialEditingLibrary
    lib.delete_all_material_expressions(material)
    _set_common_material_properties(material, spec)

    color = _road_surface_color(material, spec)
    _connect_prop(color, unreal.MaterialProperty.MP_BASE_COLOR)

    roughness = _constant(material, spec["roughness"], -440, 200)
    _connect_prop(roughness, unreal.MaterialProperty.MP_ROUGHNESS)

    specular = _constant(material, spec["specular"], -440, 340)
    _connect_prop(specular, unreal.MaterialProperty.MP_SPECULAR)

    if spec.get("emissive"):
        emissive = _constant3(material, spec["emissive"], -120, 80)
        _connect_prop(emissive, unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    if spec["blend"] == "translucent_edge":
        opacity = _edge_opacity(material, spec)
        _connect_prop(opacity, unreal.MaterialProperty.MP_OPACITY)

    try:
        lib.layout_material_expressions(material)
    except Exception:
        pass
    lib.recompile_material(material)
    save_ok = bool(unreal.EditorAssetLibrary.save_asset(path))

    return {
        "path": path,
        "label": spec["label"],
        "applied": True,
        "blend": spec["blend"],
        "save_ok": save_ok,
        "base_a": spec["base_a"],
        "base_b": spec["base_b"],
        "edge_color": spec.get("edge_color"),
        "edge_blend_min": spec.get("edge_blend_min"),
        "edge_blend_max": spec.get("edge_blend_max"),
        "noise_scale": spec["noise_scale"],
        "opacity": spec.get("opacity"),
    }


def _dirty_packages():
    names = []
    try:
        packages = (
            unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
            + unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
        )
        names = [package.get_name() for package in packages]
    except Exception:
        pass
    return names


def apply_pcg_road_material_final_tuning():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "timestamp": started,
        "materials": [],
        "dirty_before": _dirty_packages(),
    }
    for path, spec in MATERIAL_SPECS.items():
        try:
            report["materials"].append(_build_material(path, spec))
        except Exception as exc:
            report["materials"].append(
                {
                    "path": path,
                    "label": spec["label"],
                    "applied": False,
                    "reason": str(exc),
                }
            )

    report["dirty_after"] = _dirty_packages()
    report["pass"] = all(row.get("applied") and row.get("save_ok") for row in report["materials"])

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_RoadPCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    report["report_path"] = report_path
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(json.dumps(report, ensure_ascii=False))
    return report


if __name__ == "__main__":
    apply_pcg_road_material_final_tuning()
