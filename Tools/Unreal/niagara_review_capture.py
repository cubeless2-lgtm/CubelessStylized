"""Capture Niagara Preview Lab screenshots or frame sequences inside Unreal Editor.

This script is intended to run from Unreal Python. It never saves the review map
or source Niagara assets. Preview actors are temporary and removed after capture.

Example:
  py C:/Git/CubelessStylized/Tools/Unreal/niagara_review_capture.py \
    --system /Game/EL/ART/FX/Niagara/System/PC/Sword/FX_S_SwordTrail01.FX_S_SwordTrail01 \
    --mode still --view 1

For motion-driven trails, use a frame sequence:
  py C:/Git/CubelessStylized/Tools/Unreal/niagara_review_capture.py \
    --system /Game/EL/ART/FX/Niagara/System/PC/Sword/FX_S_Sword_C_Skill01_Trail01.FX_S_Sword_C_Skill01_Trail01 \
    --mode sequence --motion slash --frames 16 --view 1
"""

from __future__ import annotations

import argparse
import builtins
import json
import math
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import unreal  # type: ignore
except ImportError:  # Allows --help and syntax checks outside Unreal.
    unreal = None  # type: ignore


REVIEW_MAP = "/Game/SampleTestMap/Niagara_TestMap"
REVIEW_MAP_OBJECT = "/Game/SampleTestMap/Niagara_TestMap.Niagara_TestMap"
DEFAULT_OUTPUT_ROOT = "C:/Git/CubelessStylized/Saved/MCP/NiagaraReviews"
PREVIEW_PREFIX = "MCP_NiagaraPreviewLab_"
LEGACY_PREVIEW_PREFIXES = ("MCP_NiagaraReview_",)

# Automation camera presets that match the review bookmark meaning until the
# real editor bookmark API is exposed to MCP/Python.
CAMERA_PRESETS = {
    "1": {
        "name": "near",
        "location": (0.0, -420.0, 180.0),
        "rotation": (-8.0, 90.0, 0.0),
    },
    "2": {
        "name": "mid",
        "location": (0.0, -720.0, 260.0),
        "rotation": (-8.0, 90.0, 0.0),
    },
    "3": {
        "name": "far",
        "location": (0.0, -1150.0, 380.0),
        "rotation": (-8.0, 90.0, 0.0),
    },
}


@dataclass
class CaptureStep:
    frame_index: int
    frame_time: float
    output_file: str


def sanitize_name(value: str) -> str:
    value = value.rsplit("/", 1)[-1].split(".", 1)[0]
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")
    return value or "NiagaraReview"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a non-saving Niagara Preview Lab screenshot or frame-sequence capture in Unreal Editor."
    )
    parser.add_argument("--system", required=True, help="Niagara system object path.")
    parser.add_argument("--map", default=REVIEW_MAP, help="Review map package path.")
    parser.add_argument(
        "--load-map-if-needed",
        action="store_true",
        help=(
            "Load the review map only when no preview work has started. "
            "Normal Niagara Preview Lab work should open the map before running this script."
        ),
    )
    parser.add_argument("--label", default="", help="Output/session label.")
    parser.add_argument(
        "--mode",
        choices=["still", "sequence", "both"],
        default="still",
        help="Capture one still, a frame sequence, or both.",
    )
    parser.add_argument(
        "--view",
        choices=["1", "2", "3"],
        default="1",
        help="Review camera: 1 near, 2 mid, 3 far. Start with 1 unless it is not reviewable.",
    )
    parser.add_argument(
        "--motion",
        choices=["none", "linear-x", "linear-y", "slash"],
        default="none",
        help="Preview actor motion. Use slash or linear motion for ribbon/trail systems.",
    )
    parser.add_argument("--frames", type=int, default=16, help="Frame count for sequence/both.")
    parser.add_argument("--duration", type=float, default=1.0, help="Sequence duration in seconds.")
    parser.add_argument("--width", type=int, default=1280, help="Screenshot width.")
    parser.add_argument("--height", type=int, default=720, help="Screenshot height.")
    parser.add_argument(
        "--step-delay",
        type=float,
        default=0.35,
        help="Editor tick delay between screenshots. HighResShot is asynchronous.",
    )
    parser.add_argument(
        "--output-root",
        default=DEFAULT_OUTPUT_ROOT,
        help="Root folder for output files.",
    )
    parser.add_argument(
        "--keep-preview-actor",
        action="store_true",
        help="Leave the preview actor in the editor after capture. Do not use for normal review.",
    )
    parser.add_argument(
        "--all-views",
        action="store_true",
        help="Capture views 1, 2, and 3. Normal quick review should not use this.",
    )
    return parser.parse_args(argv)


def require_unreal() -> Any:
    if unreal is None:
        raise RuntimeError("This script must run inside Unreal Editor Python for capture.")
    return unreal


def make_vector(values: tuple[float, float, float]) -> Any:
    ue = require_unreal()
    return ue.Vector(float(values[0]), float(values[1]), float(values[2]))


def make_rotator(values: tuple[float, float, float]) -> Any:
    ue = require_unreal()
    rot = ue.Rotator()
    rot.pitch = float(values[0])
    rot.yaw = float(values[1])
    rot.roll = float(values[2])
    return rot


def apply_motion(actor: Any, motion: str, t: float) -> None:
    ue = require_unreal()
    t = max(0.0, min(1.0, t))
    if motion == "linear-x":
        location = ue.Vector(-160.0 + 320.0 * t, 0.0, 120.0)
        rotation = ue.Rotator(0.0, 0.0, 0.0)
    elif motion == "linear-y":
        location = ue.Vector(0.0, -160.0 + 320.0 * t, 120.0)
        rotation = ue.Rotator(0.0, 0.0, 0.0)
    elif motion == "slash":
        angle = math.radians(-65.0 + 130.0 * t)
        radius = 180.0
        location = ue.Vector(math.sin(angle) * radius, math.cos(angle) * radius * 0.35, 120.0 + math.cos(angle) * 80.0)
        rotation = ue.Rotator(0.0, 0.0, -65.0 + 130.0 * t)
    else:
        location = ue.Vector(0.0, 0.0, 120.0)
        rotation = ue.Rotator(0.0, 0.0, 0.0)
    actor.set_actor_location(location, False, False)
    actor.set_actor_rotation(rotation, False)


class NiagaraReviewCaptureSession:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.ue = require_unreal()
        self.label = sanitize_name(args.label or args.system)
        self.output_dir = Path(args.output_root) / self.label
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.actor = None
        self.component = None
        self.steps: list[CaptureStep] = []
        self.step_index = -1
        self.elapsed = 0.0
        self.callback_handle = None
        self.result: dict[str, Any] = {
            "system": args.system,
            "review_map": args.map,
            "view": args.view,
            "preview_system": "Niagara Preview Lab",
            "view_policy": "Niagara Preview Lab captures view 1 first. Re-run with view 2 or 3 only if the effect is too large, clipped, or not reviewable.",
            "mode": args.mode,
            "motion": args.motion,
            "output_dir": str(self.output_dir).replace("\\", "/"),
            "captures": [],
            "errors": [],
        }

    def start(self) -> None:
        self.load_map()
        self.cleanup_existing()
        self.spawn_actor()
        self.build_steps()
        self.log("started")
        self.callback_handle = self.ue.register_slate_post_tick_callback(self.tick)

    def load_map(self) -> None:
        world = self.ue.EditorLevelLibrary.get_editor_world()
        current_path = world.get_path_name() if world else ""
        if current_path and self.args.map in current_path:
            self.result["loaded_world"] = current_path
            self.result["map_load_policy"] = "reused_already_loaded_review_map"
            return
        if not self.args.load_map_if_needed:
            raise RuntimeError(
                f"Review map is not currently loaded. Open {REVIEW_MAP_OBJECT} before running Niagara review capture. "
                "This script does not reload maps by default because same-session review-map reloads can crash Unreal "
                "with World Memory Leaks when Python references still exist."
            )
        if not world or self.args.map not in current_path:
            self.ue.EditorLoadingAndSavingUtils.load_map(self.args.map)
        world = self.ue.EditorLevelLibrary.get_editor_world()
        self.result["loaded_world"] = world.get_path_name() if world else None
        self.result["map_load_policy"] = "loaded_before_preview_work"

    def cleanup_existing(self) -> None:
        actors = [
            actor
            for actor in self.ue.EditorLevelLibrary.get_all_level_actors()
                if actor.get_actor_label().startswith(PREVIEW_PREFIX)
                or any(actor.get_actor_label().startswith(Prefix) for Prefix in LEGACY_PREVIEW_PREFIXES)
        ]
        if actors:
            self.ue.EditorLevelLibrary.destroy_actors(actors)
        self.result["cleanup_count"] = len(actors)

    def spawn_actor(self) -> None:
        system = self.ue.load_asset(self.args.system)
        if not system:
            raise RuntimeError(f"Niagara system not found: {self.args.system}")
        self.actor = self.ue.EditorLevelLibrary.spawn_actor_from_class(
            self.ue.NiagaraActor,
            self.ue.Vector(0.0, 0.0, 120.0),
            self.ue.Rotator(0.0, 0.0, 0.0),
            transient=True,
        )
        self.actor.set_actor_label(f"{PREVIEW_PREFIX}{self.label}", mark_dirty=False)
        try:
            self.actor.set_folder_path("MCP/NiagaraReview")
        except Exception:
            pass
        self.component = self.actor.get_component_by_class(self.ue.NiagaraComponent)
        if self.component:
            self.component.set_asset(system)
            self.component.set_auto_activate(True)
            self.component.activate(True)
        self.ue.EditorLevelLibrary.set_selected_level_actors([self.actor])
        self.result["actor_label"] = self.actor.get_actor_label()

    def build_steps(self) -> None:
        views = ["1", "2", "3"] if self.args.all_views else [self.args.view]
        still_needed = self.args.mode in {"still", "both"}
        sequence_needed = self.args.mode in {"sequence", "both"}
        for view_id in views:
            if still_needed:
                filename = self.output_dir / f"{self.label}_view{view_id}_{CAMERA_PRESETS[view_id]['name']}_still.png"
                self.steps.append(CaptureStep(-1, 0.5, str(filename).replace("\\", "/")))
            if sequence_needed:
                frame_count = max(1, self.args.frames)
                for index in range(frame_count):
                    t = index / max(1, frame_count - 1)
                    filename = self.output_dir / "frames" / f"{self.label}_view{view_id}_{index:04d}.png"
                    filename.parent.mkdir(parents=True, exist_ok=True)
                    self.steps.append(CaptureStep(index, t, str(filename).replace("\\", "/")))
        self.result["planned_capture_count"] = len(self.steps)

    def tick(self, delta_seconds: float) -> None:
        self.elapsed += float(delta_seconds)
        if self.step_index >= 0 and self.elapsed < self.args.step_delay:
            return
        self.elapsed = 0.0
        self.step_index += 1
        try:
            if self.step_index >= len(self.steps):
                self.finish()
                return
            self.capture_step(self.steps[self.step_index])
        except Exception as exc:
            self.result["errors"].append(str(exc))
            self.finish()

    def capture_step(self, step: CaptureStep) -> None:
        view_id = self.args.view
        if self.args.all_views:
            name = Path(step.output_file).name
            match = re.search(r"_view([123])_", name)
            if match:
                view_id = match.group(1)
        camera = CAMERA_PRESETS[view_id]
        self.ue.EditorLevelLibrary.set_level_viewport_camera_info(
            make_vector(camera["location"]),
            make_rotator(camera["rotation"]),
        )
        if self.actor:
            apply_motion(self.actor, self.args.motion, step.frame_time)
        if self.component:
            self.component.activate(True)
            try:
                self.component.advance_simulation_by_time(max(0.03, self.args.duration / max(1, self.args.frames)), 30.0)
            except Exception:
                pass
        world = self.ue.EditorLevelLibrary.get_editor_world()
        command = f'HighResShot {self.args.width}x{self.args.height} filename="{step.output_file}"'
        self.ue.SystemLibrary.execute_console_command(world, command)
        self.result["captures"].append(
            {
                "frame_index": step.frame_index,
                "frame_time": round(step.frame_time, 4),
                "view": view_id,
                "view_name": camera["name"],
                "file": step.output_file,
            }
        )

    def finish(self) -> None:
        try:
            if self.callback_handle is not None:
                self.ue.unregister_slate_post_tick_callback(self.callback_handle)
        except Exception:
            pass
        if self.actor and not self.args.keep_preview_actor:
            try:
                self.ue.EditorLevelLibrary.destroy_actor(self.actor)
                self.result["preview_actor_removed"] = True
            except Exception as exc:
                self.result["errors"].append(f"cleanup_failed: {exc}")
        self.collect_dirty_packages()
        self.log("finished")
        try:
            if getattr(builtins, "_mcp_niagara_review_capture_session", None) is self:
                delattr(builtins, "_mcp_niagara_review_capture_session")
        except Exception:
            pass

    def collect_dirty_packages(self) -> None:
        dirty = []
        try:
            for package in self.ue.EditorLoadingAndSavingUtils.get_dirty_content_packages():
                dirty.append(package.get_name())
            for package in self.ue.EditorLoadingAndSavingUtils.get_dirty_map_packages():
                dirty.append(package.get_name())
        except Exception as exc:
            self.result["errors"].append(f"dirty_check_failed: {exc}")
        self.result["dirty_packages"] = sorted(set(dirty))

    def log(self, state: str) -> None:
        payload = dict(self.result)
        payload["state"] = state
        self.ue.log("MCP_NIAGARA_REVIEW_CAPTURE=" + json.dumps(payload, ensure_ascii=False))


def run(argv: list[str]) -> None:
    args = parse_args(argv)
    if unreal is None:
        print("This script must run inside Unreal Editor Python. Use --help outside Unreal only.")
        return
    session = NiagaraReviewCaptureSession(args)
    globals()["_mcp_niagara_review_capture_session"] = session
    builtins._mcp_niagara_review_capture_session = session
    session.start()


if __name__ == "__main__":
    run(sys.argv[1:])
