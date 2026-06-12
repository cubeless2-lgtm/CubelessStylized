"""Validate closed-spline grass StaticMeshSpawner actor-property override.

This runs the closed-area fixture with UseGrassMeshOverride enabled and checks
that generated ISM components use the source actor GrassMeshOverride value
instead of the weighted default mesh.
"""

import pathlib

import unreal


BASE_SCRIPT = (
    pathlib.Path(unreal.Paths.project_dir())
    / "Tools"
    / "Unreal"
    / "validate_pcg_closed_spline_grass_area.py"
)


def main():
    if not BASE_SCRIPT.exists():
        raise RuntimeError("Missing closed-spline grass validation script: {}".format(BASE_SCRIPT))
    namespace = {
        "__name__": "__main__",
        "__file__": str(BASE_SCRIPT),
        "CUBELESS_CLOSED_GRASS_USE_MESH_OVERRIDE": True,
        "CUBELESS_CLOSED_GRASS_REPORT_NAME": (
            "CubelessClosedSplineGrassMeshActorPropertyOverride_Report.json"
        ),
    }
    with BASE_SCRIPT.open("r", encoding="utf-8") as handle:
        exec(compile(handle.read(), str(BASE_SCRIPT), "exec"), namespace)
    print("pcg_closed_grass_mesh_actor_property_override_scheduled=True")
    print(
        "pcg_closed_grass_mesh_actor_property_override_note="
        "run deferred_verify after Unreal has ticked long enough for PCG generation"
    )


if __name__ == "__main__":
    main()
