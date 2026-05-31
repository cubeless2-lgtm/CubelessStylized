from __future__ import annotations

import json
import traceback

import unreal


LEVEL = "/Game/ThirdPerson/Lvl_ThirdPerson"


def color(r: float, g: float, b: float, a: float = 1.0) -> unreal.LinearColor:
    return unreal.LinearColor(float(r), float(g), float(b), float(a))


def set_prop(obj, names, value) -> bool:
    for name in names if isinstance(names, (list, tuple)) else [names]:
        try:
            obj.set_editor_property(name, value)
            return True
        except Exception:
            pass
    return False


def get_prop(obj, names, default=None):
    for name in names if isinstance(names, (list, tuple)) else [names]:
        try:
            return obj.get_editor_property(name)
        except Exception:
            pass
    return default


def all_actors():
    return unreal.EditorLevelLibrary.get_all_level_actors()


def find_actor(label: str):
    for actor in all_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def find_component_owner(component_class_name: str):
    for actor in all_actors():
        for comp in actor.get_components_by_class(unreal.ActorComponent):
            if component_class_name in comp.get_class().get_name():
                return actor
    return None


def component(actor, component_class_name: str):
    if not actor:
        return None
    for comp in actor.get_components_by_class(unreal.ActorComponent):
        if component_class_name in comp.get_class().get_name():
            return comp
    return None


def ensure_sky_atmosphere():
    actor = find_component_owner("SkyAtmosphereComponent") or find_actor("SkyAtmosphere")
    if actor:
        return actor

    sky_atmosphere_class = getattr(unreal, "SkyAtmosphere", None)
    if not sky_atmosphere_class:
        return None

    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        sky_atmosphere_class,
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    actor.set_actor_label("SkyAtmosphere")
    return actor


def apply_look_presets(sky) -> list[str]:
    presets = {
        "DayLook": {
            "directional_light_intensity": 4.0,
            "directional_light_color": color(1.0, 0.94, 0.82),
            "directional_light_volumetric_scattering_intensity": 0.55,
            "sky_light_intensity": 1.0,
            "sky_light_color": color(0.62, 0.75, 1.0),
            "sky_atmosphere_sky_luminance_factor": color(1.0, 1.0, 1.0),
            "sky_atmosphere_aerial_perspective_luminance_factor": color(0.90, 0.98, 1.0),
            "sky_atmosphere_rayleigh_scattering": color(0.18, 0.38, 1.0),
            "sky_atmosphere_rayleigh_scattering_scale": 0.32,
            "sky_atmosphere_mie_scattering": color(1.0, 0.86, 0.66),
            "sky_atmosphere_mie_scattering_scale": 0.06,
        },
        "SunsetLook": {
            "directional_light_intensity": 1.35,
            "directional_light_color": color(1.0, 0.48, 0.26),
            "directional_light_volumetric_scattering_intensity": 0.85,
            "sky_light_intensity": 0.48,
            "sky_light_color": color(1.0, 0.48, 0.38),
            "sky_atmosphere_sky_luminance_factor": color(1.0, 0.45, 0.34),
            "sky_atmosphere_aerial_perspective_luminance_factor": color(1.0, 0.55, 0.42),
            "sky_atmosphere_rayleigh_scattering": color(0.55, 0.18, 0.85),
            "sky_atmosphere_rayleigh_scattering_scale": 0.22,
            "sky_atmosphere_mie_scattering": color(1.0, 0.42, 0.22),
            "sky_atmosphere_mie_scattering_scale": 0.22,
        },
        "NightLook": {
            "directional_light_intensity": 0.035,
            "directional_light_color": color(0.22, 0.28, 0.62),
            "directional_light_volumetric_scattering_intensity": 0.15,
            "sky_light_intensity": 0.12,
            "sky_light_color": color(0.10, 0.16, 0.45),
            "sky_atmosphere_sky_luminance_factor": color(0.025, 0.045, 0.18),
            "sky_atmosphere_aerial_perspective_luminance_factor": color(0.035, 0.050, 0.22),
            "sky_atmosphere_rayleigh_scattering": color(0.04, 0.08, 0.42),
            "sky_atmosphere_rayleigh_scattering_scale": 0.06,
            "sky_atmosphere_mie_scattering": color(0.16, 0.12, 0.38),
            "sky_atmosphere_mie_scattering_scale": 0.03,
        },
    }

    failed = []
    for look_name, values in presets.items():
        look = sky.get_editor_property(look_name)
        for key, value in values.items():
            if not set_prop(look, key, value):
                failed.append(f"{look_name}.{key}")
        sky.set_editor_property(look_name, look)
    return failed


def lc(value):
    if value is None:
        return None
    return [round(float(value.r), 5), round(float(value.g), 5), round(float(value.b), 5), round(float(value.a), 5)]


def sample(sky, sun, skylight, atmosphere, minute: int):
    try:
        sky.set_time_of_day_minutes(minute)
    except Exception:
        sky.set_editor_property("TimeOfDayMinutes", minute)
        sky.set_editor_property("TimeOfDayHours", minute / 60.0)

    sky.refresh_sky()
    directional_light = component(sun, "DirectionalLightComponent")
    sky_light = component(skylight, "SkyLightComponent")
    sky_atmosphere = component(atmosphere, "SkyAtmosphereComponent")

    return {
        "minute": minute,
        "hour": round(float(sky.get_editor_property("TimeOfDayHours")), 4),
        "phase": str(sky.get_editor_property("CurrentTimeOfDayPhase")),
        "sun_elevation": round(float(sky.get_editor_property("CurrentSunElevationDegrees")), 5),
        "directional_intensity": round(float(get_prop(directional_light, "intensity", -1.0)), 5) if directional_light else None,
        "directional_color": lc(get_prop(directional_light, "light_color")) if directional_light else None,
        "directional_volumetric": round(float(get_prop(directional_light, "volumetric_scattering_intensity", -1.0)), 5) if directional_light else None,
        "skylight_intensity": round(float(get_prop(sky_light, "intensity", -1.0)), 5) if sky_light else None,
        "skylight_color": lc(get_prop(sky_light, "light_color")) if sky_light else None,
        "atmos_sky_luminance": lc(get_prop(sky_atmosphere, "sky_luminance_factor")) if sky_atmosphere else None,
        "atmos_aerial_luminance": lc(get_prop(sky_atmosphere, "sky_and_aerial_perspective_luminance_factor")) if sky_atmosphere else None,
        "atmos_rayleigh": lc(get_prop(sky_atmosphere, "rayleigh_scattering")) if sky_atmosphere else None,
        "atmos_rayleigh_scale": round(float(get_prop(sky_atmosphere, "rayleigh_scattering_scale", -1.0)), 5) if sky_atmosphere else None,
        "atmos_mie": lc(get_prop(sky_atmosphere, "mie_scattering")) if sky_atmosphere else None,
        "atmos_mie_scale": round(float(get_prop(sky_atmosphere, "mie_scattering_scale", -1.0)), 5) if sky_atmosphere else None,
    }


def main() -> None:
    try:
        if not find_actor("StylizedSky_Main"):
            unreal.EditorLevelLibrary.load_level(LEVEL)

        sky = find_actor("StylizedSky_Main")
        if not sky:
            raise RuntimeError("StylizedSky_Main not found")

        sun = find_actor("DirectionalLight") or find_component_owner("DirectionalLightComponent")
        skylight = find_actor("SkyLight") or find_component_owner("SkyLightComponent")
        atmosphere = ensure_sky_atmosphere()

        sky.modify()
        set_prop(sky, ["SunActor", "sun_actor"], sun)
        set_prop(sky, ["SkyLightActor", "sky_light_actor"], skylight)
        set_prop(sky, ["SkyAtmosphereActor", "sky_atmosphere_actor"], atmosphere)

        for prop in [
            "bDriveDirectionalLightFromLook",
            "bDriveSkyLightFromLook",
            "bDriveSkyAtmosphereFromLook",
            "bUpdateInEditor",
            "bUpdateEveryTick",
            "bUseTimeOfDayPreview",
            "bDriveSunActorFromTimeOfDay",
        ]:
            set_prop(sky, [prop, prop[0].lower() + prop[1:]], True)

        failed_sets = apply_look_presets(sky)
        samples = [sample(sky, sun, skylight, atmosphere, minute) for minute in [360, 720, 1080, 1260]]

        try:
            sky.set_time_of_day_minutes(1260)
        except Exception:
            sky.set_editor_property("TimeOfDayMinutes", 1260)
            sky.set_editor_property("TimeOfDayHours", 21.0)

        sky.set_editor_property("bAnimateTimeOfDay", False)
        sky.refresh_sky()
        unreal.EditorLevelLibrary.save_current_level()

        result = {
            "sky": sky.get_actor_label(),
            "sun": sun.get_actor_label() if sun else None,
            "skylight": skylight.get_actor_label() if skylight else None,
            "atmosphere": atmosphere.get_actor_label() if atmosphere else None,
            "failed_sets": failed_sets,
            "samples": samples,
            "restored_minute": int(sky.get_editor_property("TimeOfDayMinutes")),
            "restored_phase": str(sky.get_editor_property("CurrentTimeOfDayPhase")),
        }
        unreal.log("STYLIZED_SKY_LIGHT_ATMOS_APPLY_OK=" + json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        unreal.log_error("STYLIZED_SKY_LIGHT_ATMOS_APPLY_ERROR: " + repr(exc))
        unreal.log_error(traceback.format_exc())
        raise


main()
