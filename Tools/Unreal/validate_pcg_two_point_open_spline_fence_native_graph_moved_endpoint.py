"""Validate native PCG 2-point spline regeneration after moving an endpoint.

This reuses the baseline native 2-point open spline graph fixture and changes
the source local points before scheduling validation. The report proves that
linear spline intent survives endpoint edits and that the actor-property mesh
override still drives SpawnSplineMesh output.
"""

import os

import unreal


SCRIPT_DIR = os.path.dirname(globals().get("__file__", "D:/Git/CubelessStylized/Tools/Unreal/"))
BASE_SCRIPT = os.path.join(SCRIPT_DIR, "validate_pcg_two_point_open_spline_fence_native_graph.py")

MOVED_LOCAL_POINTS = [
    unreal.Vector(-5200.0, -1500.0, 0.0),
    unreal.Vector(4800.0, 2100.0, 0.0),
]

MOVED_REPORT_NAME = "CubelessTwoPointOpenSplineFenceNativeGraph_MovedEndpoint_Report.json"
MOVED_STATE_ATTR = "_cubeless_two_point_open_spline_fence_native_moved_state"


def validate_moved_endpoint_native_graph():
    namespace = {"__name__": "cubeless_two_point_open_spline_fence_native_base"}
    with open(BASE_SCRIPT, "r", encoding="utf-8") as handle:
        code = handle.read()
    exec(compile(code, BASE_SCRIPT, "exec"), namespace)

    namespace["LOCAL_POINTS"] = MOVED_LOCAL_POINTS
    namespace["REPORT_NAME"] = MOVED_REPORT_NAME
    namespace["STATE_ATTR"] = MOVED_STATE_ATTR

    original_write_report = namespace["_write_report"]

    def _write_report_with_variant(report):
        report["point_variant"] = {
            "name": "moved_endpoint",
            "local_points": [
                [point.x, point.y, point.z]
                for point in MOVED_LOCAL_POINTS
            ],
        }
        return original_write_report(report)

    namespace["_write_report"] = _write_report_with_variant
    return namespace["validate_two_point_open_spline_fence_native_graph"]()


if __name__ == "__main__":
    validate_moved_endpoint_native_graph()
