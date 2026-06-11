"""Rebuild true-material PCG graphs with actor-property mesh override routes."""

import json
import pathlib

import unreal


REPORT_NAME = "pcg_true_material_actor_property_override_rebuild_report.json"


def _builder_script_path():
    project_dir = pathlib.Path(unreal.Paths.project_dir()).resolve()
    return (
        project_dir.parent
        / "unreal-mcp-cubeless"
        / "Docs"
        / "Analysis"
        / "ElectricDreams"
        / "build_cubeless_ed_true_material_applied_presets.py"
    )


def _load_builder_namespace():
    script_path = _builder_script_path()
    namespace = {"__name__": "_cubeless_true_material_actor_property_rebuild", "__file__": str(script_path)}
    with open(script_path, "r", encoding="utf-8") as handle:
        code = compile(handle.read(), str(script_path), "exec")
    exec(code, namespace)
    return namespace


def _write_report(report):
    out_dir = pathlib.Path(unreal.Paths.project_saved_dir()) / "MCP_PCG"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / REPORT_NAME
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(out_path)


def rebuild_pcg_true_material_actor_property_overrides():
    builder = _load_builder_namespace()
    report = {
        "builder_script": str(_builder_script_path()),
        "style_amount_graphs": [],
        "style_matrix_graphs": [],
        "tree_graphs": [],
    }

    builder["MATERIAL_CONFIG"]["ensure_material_variants"]()

    for style in builder["STYLE_CONFIG"]["STYLE_SPECS"]:
        if style["style_type"] not in builder["STYLE_DOMAIN_BY_STYLE_TYPE"]:
            continue
        for variant_type in (2, 3):
            for amount in builder["STYLE_CONFIG"]["GROUND_AMOUNT_SPECS"]:
                graph = builder["build_true_style_amount_graph"]("Ground", amount, style, variant_type)
                report["style_amount_graphs"].append(graph.get_path_name())
            for amount in builder["STYLE_CONFIG"]["DITCH_AMOUNT_SPECS"]:
                graph = builder["build_true_style_amount_graph"]("Ditch", amount, style, variant_type)
                report["style_amount_graphs"].append(graph.get_path_name())

    for spec in builder["TRUE_STYLE_MATRIX_SPECS"]:
        graph = builder["build_true_style_matrix_graph"](spec["style_matrix_spec"], spec["variant_type"])
        report["style_matrix_graphs"].append(graph.get_path_name())

    for spec in builder["TRUE_TREE_SPECS"]:
        graph = builder["build_true_tree_graph"](spec["tree_spec"], spec["variant_type"])
        report["tree_graphs"].append(graph.get_path_name())

    report["style_amount_graph_count"] = len(report["style_amount_graphs"])
    report["style_matrix_graph_count"] = len(report["style_matrix_graphs"])
    report["tree_graph_count"] = len(report["tree_graphs"])
    report["total_graph_count"] = (
        report["style_amount_graph_count"]
        + report["style_matrix_graph_count"]
        + report["tree_graph_count"]
    )
    report_path = _write_report(report)
    print(json.dumps({"report_path": report_path, "total_graph_count": report["total_graph_count"]}, indent=2))
    return report


if __name__ == "__main__":
    print("MCP_CUBELESS_PCG_TRUE_MATERIAL_ACTOR_PROPERTY_OVERRIDE_REBUILD_BEGIN")
    rebuild_pcg_true_material_actor_property_overrides()
    print("MCP_CUBELESS_PCG_TRUE_MATERIAL_ACTOR_PROPERTY_OVERRIDE_REBUILD_END")
