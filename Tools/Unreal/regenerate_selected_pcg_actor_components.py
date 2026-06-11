import json
import os
import pathlib

import unreal


REPORT_PATH = "Saved/MCP_PCG/regenerate_selected_pcg_actor_components_report.json"
DEFAULT_SKIP_COMPONENT_NAMES = {"PCG_MaterialPreview"}
WATCHED_ACTOR_PROPERTIES = [
    "UseTreeMeshOverride",
    "TreeMeshOverride",
    "UseGrassMeshOverride",
    "GrassMeshOverride",
    "UseRockMeshOverride",
    "RockMeshOverride",
]


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return bool(default)
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_csv(name):
    value = os.environ.get(name, "")
    return [part.strip() for part in value.split(",") if part.strip()]


def actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def object_path(obj):
    if not obj:
        return None
    try:
        return obj.get_path_name()
    except Exception:
        return str(obj)


def get_actor_subsystem():
    subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    if not subsystem_cls:
        return None
    return unreal.get_editor_subsystem(subsystem_cls)


def get_all_level_actors():
    subsystem = get_actor_subsystem()
    if subsystem:
        return list(subsystem.get_all_level_actors())
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def get_selected_level_actors():
    subsystem = get_actor_subsystem()
    if subsystem:
        return list(subsystem.get_selected_level_actors())
    return []


def select_target_actors():
    label_filter = os.environ.get("CUBELESS_PCG_ACTOR_FILTER", "").strip()
    if label_filter:
        return [actor for actor in get_all_level_actors() if label_filter in actor_label(actor)]
    return get_selected_level_actors()


def component_graph_path(component):
    try:
        graph = component.get_editor_property("graph")
        if graph:
            return object_path(graph)
    except Exception:
        pass
    try:
        graph_instance = component.get_editor_property("graph_instance")
        if graph_instance:
            graph = graph_instance.get_editor_property("graph")
            if graph:
                return object_path(graph)
    except Exception:
        pass
    return None


def component_state(component):
    state = {
        "component": component.get_name(),
        "graph": component_graph_path(component),
    }
    for prop in ["generation_trigger", "regenerate_in_editor", "dirty_generated", "generated"]:
        try:
            state[prop] = str(component.get_editor_property(prop))
        except Exception:
            pass
    return state


def summarize_ism_rows(actor):
    rows = []
    for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        try:
            mesh = component.get_editor_property("static_mesh")
        except Exception:
            mesh = None
        try:
            count = int(component.get_instance_count())
        except Exception:
            count = -1
        rows.append(
            {
                "component": component.get_name(),
                "mesh": object_path(mesh),
                "count": count,
            }
        )
    rows.sort(key=lambda row: (str(row["mesh"]), row["component"]))
    return rows


def summarize_actor_properties(actor):
    properties = {}
    for prop in WATCHED_ACTOR_PROPERTIES:
        try:
            value = actor.get_editor_property(prop)
            properties[prop] = object_path(value) if hasattr(value, "get_path_name") else value
        except Exception as exc:
            properties[prop] = f"ERR: {exc}"
    return properties


def should_process_component(component):
    include_names = set(env_csv("CUBELESS_PCG_COMPONENTS"))
    if include_names:
        return component.get_name() in include_names
    skip_names = set(DEFAULT_SKIP_COMPONENT_NAMES)
    skip_names.update(env_csv("CUBELESS_PCG_SKIP_COMPONENTS"))
    return component.get_name() not in skip_names


def hard_remove_pcg_ism_outputs(actor):
    """Optional recovery for orphaned PCG-generated ISM components after graph swaps."""
    removed = []
    for component in list(actor.get_components_by_class(unreal.InstancedStaticMeshComponent)):
        name = component.get_name()
        if not name.startswith("ISM_"):
            continue
        entry = {"component": name}
        try:
            unreal.ActorComponent.destroy_component(component)
            entry["removed"] = True
        except Exception as exc:
            entry["removed"] = False
            entry["error"] = str(exc)
        removed.append(entry)
    return removed


def regenerate_component(component):
    result = component_state(component)
    try:
        component.activate(True)
    except Exception as exc:
        result["activate_error"] = str(exc)
    try:
        component.cleanup(True)
        component.generate(True)
        try:
            component.generate_local(True)
        except Exception as local_exc:
            result["generate_local_error"] = str(local_exc)
        component.generate(True)
        result["regenerated"] = True
    except Exception as exc:
        result["regenerated"] = False
        result["error"] = str(exc)
    result["after"] = component_state(component)
    return result


def write_report(report):
    report_path = pathlib.Path(unreal.Paths.project_dir()) / REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(report_path)


def main():
    print("MCP_CUBELESS_REGENERATE_SELECTED_PCG_ACTOR_COMPONENTS_BEGIN")
    actors = select_target_actors()
    if not actors:
        raise RuntimeError(
            "No target actors. Select PCG actors or set CUBELESS_PCG_ACTOR_FILTER."
        )

    hard_remove = env_bool("CUBELESS_PCG_HARD_REMOVE_ISM_OUTPUTS", False)
    actor_reports = []
    for actor in actors:
        entry = {
            "actor": actor_label(actor),
            "class": object_path(actor.get_class()),
            "actor_properties": summarize_actor_properties(actor),
            "hard_remove_ism_outputs": hard_remove,
            "ism_before": summarize_ism_rows(actor),
            "components": [],
        }
        if hard_remove:
            entry["hard_removed_ism_outputs"] = hard_remove_pcg_ism_outputs(actor)
        for component in actor.get_components_by_class(unreal.PCGComponent):
            if not should_process_component(component):
                continue
            entry["components"].append(regenerate_component(component))
        entry["ism_after"] = summarize_ism_rows(actor)
        actor_reports.append(entry)

    report = {
        "actor_filter": os.environ.get("CUBELESS_PCG_ACTOR_FILTER", "").strip(),
        "component_filter": env_csv("CUBELESS_PCG_COMPONENTS"),
        "skip_components": sorted(DEFAULT_SKIP_COMPONENT_NAMES.union(env_csv("CUBELESS_PCG_SKIP_COMPONENTS"))),
        "notes": [
            "PCG Actor Property values are read at generation time.",
            "Use this after editing Blueprint mesh override properties on Generate On Demand PCG actors.",
            "Static Mesh Spawner mesh choices should remain Blueprint-variable overridable by project rule.",
        ],
        "actors": actor_reports,
    }
    report_path = write_report(report)
    print(json.dumps({"report_path": report_path, "actor_count": len(actor_reports)}, indent=2, ensure_ascii=False))
    print("MCP_CUBELESS_REGENERATE_SELECTED_PCG_ACTOR_COMPONENTS_END")


if __name__ == "__main__":
    main()
