from __future__ import annotations

import json
import math
import traceback

import unreal


LEVEL = "/Game/ThirdPerson/Lvl_ThirdPerson"
STARS_MASK_TEXTURE_PATH = "/Game/Cubeless/Env/Sky/Textures/T_StylizedSky_Stars_Mask_Tile_RGBA"
SKY_MATERIALS = [
    "/StylizedSky/Materials/M_StylizedSky_Dome_MoonRGBMask",
    "/Game/Cubeless/Env/Sky/Materials/M_StylizedSky_Dome_MoonRGBMask",
]
SKY_MIS = [
    "/StylizedSky/Materials/MI_StylizedSky_Dome_MoonRGBMask",
    "/Game/Cubeless/Env/Sky/Materials/MI_StylizedSky_Dome_MoonRGBMask",
]
BP_CLASS_PATH = "/Game/Cubeless/Env/Sky/Blueprints/BP_StylizedSky"


SKY_CODE = r"""
float3 dir = normalize(-ViewDir);
float3 sunDir = normalize(SunDirection.xyz);
float3 moonDir = normalize(MoonDirection.xyz);

float horizonMask = saturate(pow(1.0 - abs(dir.z), 1.28));
float3 sky = lerp(SkyZenithColor.rgb, SkyHorizonColor.rgb, horizonMask);

float sunDot = saturate(dot(dir, sunDir));
float dayMask = smoothstep(-0.05, 0.16, sunDir.z);
float sunDisk = smoothstep(0.9990, 0.9998, sunDot) * dayMask;
float sunGlow = pow(sunDot, 72.0) * dayMask;

float nightMask = saturate((-sunDir.z + 0.05) * 2.6);
float starPower = nightMask * StarsIntensity;
float3 maskRgb = saturate(StarsMask);
float maskRaw = max(maskRgb.r, max(maskRgb.g, maskRgb.b));
float threshold = saturate(StarsMaskThreshold);
float normalizedMask = saturate((maskRaw - threshold) / max(1.0 - threshold, 0.001));
float starMask = pow(normalizedMask, max(StarsMaskPower, 0.1));
float3 starField = StarsColor.rgb * starMask * starPower;
float3 nightGlow = StarsColor.rgb * starMask * horizonMask * starPower * 0.08;

float moonAngle = acos(clamp(dot(dir, moonDir), -1.0, 1.0));
float moonRadius = radians(max(MoonAngularSizeDegrees, 0.05));
float moonDisk = 1.0 - smoothstep(moonRadius * 0.82, moonRadius, moonAngle);
float moonGlow = exp(-moonAngle * 24.0) * MoonGlowIntensity;
float moonPower = nightMask * MoonIntensity;
float3 moon = MoonColor.rgb * (moonDisk * moonPower * 4.2 + moonGlow * moonPower);

return sky + SunColor.rgb * (sunDisk * 16.0 + sunGlow * 0.35) + starField + nightGlow + moon;
"""


STARS_UV_CODE = r"""
float3 dir = normalize(-ViewDir);
float u = atan2(dir.y, dir.x) * 0.15915494309 + 0.5;
float v = asin(clamp(dir.z, -1.0, 1.0)) * 0.31830988618 + 0.5;
return float2(u, v) * max(StarsTiling, 0.1);
"""


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


def custom_input(name: str) -> unreal.CustomInput:
    item = unreal.CustomInput()
    item.set_editor_property("input_name", name)
    return item


def connect(source, target, input_name: str, source_output: str = "") -> None:
    if not unreal.MaterialEditingLibrary.connect_material_expressions(source, source_output, target, input_name):
        raise RuntimeError(f"Failed to connect {source} to {input_name}")


def vector_param(material: unreal.Material, name: str, value: unreal.LinearColor, x: int, y: int):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionVectorParameter,
        x,
        y,
    )
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("default_value", value)
    return node


def scalar_param(material: unreal.Material, name: str, value: float, x: int, y: int):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionScalarParameter,
        x,
        y,
    )
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("default_value", float(value))
    return node


def create_or_load_material(material_path: str) -> unreal.Material:
    folder_path, asset_name = material_path.rsplit("/", 1)
    if unreal.EditorAssetLibrary.does_asset_exist(material_path):
        material = unreal.EditorAssetLibrary.load_asset(material_path)
    else:
        unreal.EditorAssetLibrary.make_directory(folder_path)
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            asset_name,
            folder_path,
            unreal.Material,
            unreal.MaterialFactoryNew(),
        )
    if not material:
        raise RuntimeError(f"Could not load or create material: {material_path}")
    return material


def patch_texture() -> unreal.Texture2D:
    texture = unreal.EditorAssetLibrary.load_asset(STARS_MASK_TEXTURE_PATH)
    if not texture:
        raise RuntimeError(f"Missing stars mask texture: {STARS_MASK_TEXTURE_PATH}")

    texture.set_editor_property("srgb", False)
    texture.set_editor_property("address_x", unreal.TextureAddress.TA_WRAP)
    texture.set_editor_property("address_y", unreal.TextureAddress.TA_WRAP)
    try:
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    except Exception as exc:
        unreal.log_warning(f"Could not set TC_MASKS: {exc!r}")
    unreal.EditorAssetLibrary.save_asset(STARS_MASK_TEXTURE_PATH, only_if_is_dirty=False)
    return texture


def patch_sky_material(material_path: str, mask_texture: unreal.Texture2D) -> bool:
    material = create_or_load_material(material_path)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)
    try:
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    except Exception:
        pass

    view_node = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionCameraVectorWS,
        -860,
        -120,
    )
    sun_direction = vector_param(material, "SunDirection", color(0.35, -0.25, 0.90, 0.0), -860, 20)
    moon_direction = vector_param(material, "MoonDirection", color(0.28, -0.48, 0.83, 0.0), -860, 160)
    zenith = vector_param(material, "SkyZenithColor", color(0.18, 0.42, 0.88), -860, 300)
    horizon = vector_param(material, "SkyHorizonColor", color(0.78, 0.88, 1.0), -860, 440)
    sun_color = vector_param(material, "SunColor", color(1.0, 0.94, 0.75), -860, 580)
    moon_color = vector_param(material, "MoonColor", color(0.86, 0.92, 1.0), -860, 720)
    moon_intensity = scalar_param(material, "MoonIntensity", 0.0, -860, 860)
    moon_size = scalar_param(material, "MoonAngularSizeDegrees", 2.2, -860, 1000)
    moon_glow = scalar_param(material, "MoonGlowIntensity", 0.12, -860, 1140)
    stars_intensity = scalar_param(material, "StarsIntensity", 0.0, -860, 1280)
    stars_color = vector_param(material, "StarsColor", color(0.82, 0.90, 1.0), -860, 1420)
    stars_tiling = scalar_param(material, "StarsTiling", 3.0, -860, 1560)
    stars_threshold = scalar_param(material, "StarsMaskThreshold", 0.22, -860, 1700)
    stars_power = scalar_param(material, "StarsMaskPower", 1.45, -860, 1840)

    stars_uv = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionCustom,
        -560,
        1500,
    )
    stars_uv.set_editor_property("description", "Spherical star UV")
    stars_uv.set_editor_property("code", STARS_UV_CODE)
    stars_uv.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT2)
    stars_uv.set_editor_property("inputs", [custom_input("ViewDir"), custom_input("StarsTiling")])
    connect(view_node, stars_uv, "ViewDir")
    connect(stars_tiling, stars_uv, "StarsTiling")

    stars_mask = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionTextureSampleParameter2D,
        -280,
        1520,
    )
    stars_mask.set_editor_property("parameter_name", "StarsMaskMap")
    stars_mask.set_editor_property("texture", mask_texture)
    try:
        stars_mask.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    except Exception as exc:
        unreal.log_warning(f"Could not set StarsMaskMap sampler type: {exc!r}")
    connect(stars_uv, stars_mask, "UVs")

    sky_node = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionCustom,
        -280,
        240,
    )
    sky_node.set_editor_property("description", "Stylized sky dome color with moon")
    sky_node.set_editor_property("code", SKY_CODE)
    sky_node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    sky_inputs = [
        "ViewDir",
        "SunDirection",
        "MoonDirection",
        "SkyZenithColor",
        "SkyHorizonColor",
        "SunColor",
        "MoonColor",
        "MoonIntensity",
        "MoonAngularSizeDegrees",
        "MoonGlowIntensity",
        "StarsIntensity",
        "StarsColor",
        "StarsMaskThreshold",
        "StarsMaskPower",
        "StarsMask",
    ]
    sky_node.set_editor_property("inputs", [custom_input(name) for name in sky_inputs])

    for source, input_name in [
        (view_node, "ViewDir"),
        (sun_direction, "SunDirection"),
        (moon_direction, "MoonDirection"),
        (zenith, "SkyZenithColor"),
        (horizon, "SkyHorizonColor"),
        (sun_color, "SunColor"),
        (moon_color, "MoonColor"),
        (moon_intensity, "MoonIntensity"),
        (moon_size, "MoonAngularSizeDegrees"),
        (moon_glow, "MoonGlowIntensity"),
        (stars_intensity, "StarsIntensity"),
        (stars_color, "StarsColor"),
        (stars_threshold, "StarsMaskThreshold"),
        (stars_power, "StarsMaskPower"),
        (stars_mask, "StarsMask"),
    ]:
        connect(source, sky_node, input_name)

    unreal.MaterialEditingLibrary.connect_material_property(
        sky_node,
        "",
        unreal.MaterialProperty.MP_EMISSIVE_COLOR,
    )
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(material_path, only_if_is_dirty=False)
    return True


def patch_material_instances(mask_texture: unreal.Texture2D) -> list[str]:
    changed = []
    for material_instance_path, parent_material_path in zip(SKY_MIS, SKY_MATERIALS):
        parent_material = unreal.EditorAssetLibrary.load_asset(parent_material_path)
        if not parent_material:
            continue
        if not unreal.EditorAssetLibrary.does_asset_exist(material_instance_path):
            folder_path, asset_name = material_instance_path.rsplit("/", 1)
            unreal.EditorAssetLibrary.make_directory(folder_path)
            material_instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                asset_name,
                folder_path,
                unreal.MaterialInstanceConstant,
                unreal.MaterialInstanceConstantFactoryNew(),
            )
        else:
            material_instance = unreal.EditorAssetLibrary.load_asset(material_instance_path)
        if not material_instance:
            continue
        unreal.MaterialEditingLibrary.set_material_instance_parent(material_instance, parent_material)
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(material_instance, "MoonDirection", color(0.28, -0.48, 0.83, 0.0))
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(material_instance, "MoonColor", color(0.86, 0.92, 1.0))
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(material_instance, "MoonIntensity", 0.0)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(material_instance, "MoonAngularSizeDegrees", 2.2)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(material_instance, "MoonGlowIntensity", 0.12)
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(material_instance, "StarsMaskMap", mask_texture)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(material_instance, "StarsTiling", 3.0)
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(material_instance, "StarsColor", color(0.82, 0.90, 1.0))
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(material_instance, "StarsMaskThreshold", 0.22)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(material_instance, "StarsMaskPower", 1.45)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(material_instance, "StarsIntensity", 0.55)
        unreal.EditorAssetLibrary.save_asset(material_instance_path, only_if_is_dirty=False)
        changed.append(material_instance_path)
    return changed


def set_look_values(sky) -> list[str]:
    failed = []
    values = {
        "DayLook": {
            "night_light_intensity": 0.0,
            "night_light_color": color(0.45, 0.55, 1.0),
            "night_light_volumetric_scattering_intensity": 0.0,
            "moon_color": color(0.86, 0.92, 1.0),
            "moon_intensity": 0.0,
            "moon_angular_size_degrees": 2.2,
            "moon_glow_intensity": 0.0,
        },
        "SunsetLook": {
            "night_light_intensity": 0.0,
            "night_light_color": color(0.65, 0.50, 1.0),
            "night_light_volumetric_scattering_intensity": 0.0,
            "moon_color": color(0.80, 0.84, 1.0),
            "moon_intensity": 0.0,
            "moon_angular_size_degrees": 2.2,
            "moon_glow_intensity": 0.0,
        },
        "NightLook": {
            "night_light_intensity": 0.45,
            "night_light_color": color(0.45, 0.55, 1.0),
            "night_light_volumetric_scattering_intensity": 0.35,
            "moon_color": color(0.86, 0.92, 1.0),
            "moon_intensity": 1.2,
            "moon_angular_size_degrees": 2.2,
            "moon_glow_intensity": 0.12,
        },
    }
    for look_name, look_values in values.items():
        try:
            look = sky.get_editor_property(look_name)
        except Exception:
            failed.append(look_name)
            continue
        for key, value in look_values.items():
            if not set_prop(look, key, value):
                failed.append(f"{look_name}.{key}")
        set_prop(sky, [look_name, look_name[0].lower() + look_name[1:]], look)
    return failed


def moon_direction_to_light_rotation(direction: unreal.Vector) -> unreal.Rotator:
    length = math.sqrt(direction.x * direction.x + direction.y * direction.y + direction.z * direction.z)
    if length <= 0.0001:
        direction = unreal.Vector(0.28, -0.48, 0.83)
        length = math.sqrt(direction.x * direction.x + direction.y * direction.y + direction.z * direction.z)
    moon_x = direction.x / length
    moon_y = direction.y / length
    moon_z = direction.z / length

    forward_x = -moon_x
    forward_y = -moon_y
    forward_z = -moon_z
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, forward_z))))
    yaw = math.degrees(math.atan2(forward_y, forward_x))
    rotation = unreal.Rotator()
    rotation.set_editor_property("pitch", pitch)
    rotation.set_editor_property("yaw", yaw)
    rotation.set_editor_property("roll", 0.0)
    return rotation


def get_inverted_actor_forward(actor) -> unreal.Vector:
    forward = actor.get_actor_forward_vector()
    return unreal.Vector(-forward.x, -forward.y, -forward.z)


def ensure_night_light():
    actor = find_actor("StylizedSky_NightLight")
    created = False
    desired_moon_direction = unreal.Vector(0.28, -0.48, 0.83)
    if not actor:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.DirectionalLight,
            unreal.Vector(0.0, 0.0, 0.0),
            moon_direction_to_light_rotation(desired_moon_direction),
        )
        actor.set_actor_label("StylizedSky_NightLight")
        created = True

    actor.modify()
    current_moon_direction = get_inverted_actor_forward(actor)
    if created or current_moon_direction.z < 0.05:
        actor.set_actor_rotation(moon_direction_to_light_rotation(desired_moon_direction), False)

    light = component(actor, "DirectionalLightComponent")
    if light:
        try:
            light.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        except Exception:
            pass
        light.set_editor_property("intensity", 0.0)
        try:
            light.set_editor_property("light_color", color(0.45, 0.55, 1.0))
        except Exception:
            pass
        try:
            light.set_editor_property("volumetric_scattering_intensity", 0.35)
        except Exception:
            pass
    return actor, created


def set_common_sky_props(sky, sky_material, night_light) -> list[str]:
    failed = []
    for prop, value in [
        ("SkyDomeMaterial", sky_material),
        ("NightLightActor", night_light),
        ("ManualNightLightDirection", unreal.Vector(0.28, -0.48, 0.83)),
        ("bInvertNightLightActorForward", True),
        ("bDriveNightLightFromLook", True),
        ("bUseTimeOfDayPreview", True),
        ("bUpdateInEditor", True),
        ("bUpdateEveryTick", True),
        ("bAnimateTimeOfDay", True),
        ("TimeOfDaySpeedMinutesPerSecond", 48.0),
        ("bApplyCloudPlaneSettingsOnConstruction", False),
    ]:
        if not set_prop(sky, [prop, prop[0].lower() + prop[1:]], value):
            failed.append(prop)
    set_prop(sky, ["StarsTiling", "stars_tiling"], 3.0)
    set_prop(sky, ["StarsMaskThreshold", "stars_mask_threshold"], 0.22)
    set_prop(sky, ["StarsMaskPower", "stars_mask_power"], 1.45)
    set_prop(sky, ["StarsMaskTexture", "stars_mask_texture"], unreal.EditorAssetLibrary.load_asset(STARS_MASK_TEXTURE_PATH))
    failed.extend(set_look_values(sky))
    return failed


def patch_blueprint_defaults(sky_material) -> list[str]:
    bp_class = unreal.EditorAssetLibrary.load_blueprint_class(BP_CLASS_PATH)
    if not bp_class:
        return [f"Missing {BP_CLASS_PATH}"]
    try:
        cdo = unreal.get_default_object(bp_class)
    except Exception:
        cdo = bp_class.get_default_object()
    failed = set_common_sky_props(cdo, sky_material, None)
    set_prop(cdo, ["bAnimateTimeOfDay", "b_animate_time_of_day"], True)
    unreal.EditorAssetLibrary.save_asset("/Game/Cubeless/Env/Sky/Blueprints/BP_StylizedSky", only_if_is_dirty=False)
    return failed


def read_scalar(material, name: str):
    if not material:
        return None
    for method_name in ["get_scalar_parameter_value"]:
        try:
            method = getattr(material, method_name)
            value = method(name)
            if isinstance(value, tuple):
                return value[-1]
            return value
        except Exception:
            pass
    return None


def vec_to_list(vec) -> list[float]:
    return [round(float(vec.x), 5), round(float(vec.y), 5), round(float(vec.z), 5)]


def sample_sky(sky, night_light, minute: int) -> dict:
    set_prop(sky, ["bAnimateTimeOfDay", "b_animate_time_of_day"], False)
    try:
        sky.set_time_of_day_minutes(minute)
    except Exception:
        set_prop(sky, ["TimeOfDayMinutes", "time_of_day_minutes"], minute)
        set_prop(sky, ["TimeOfDayHours", "time_of_day_hours"], minute / 60.0)
    sky.refresh_sky()

    night_comp = component(night_light, "DirectionalLightComponent")
    sky_dome_component = component(sky, "StaticMeshComponent")
    sky_material = sky_dome_component.get_material(0) if sky_dome_component else None
    moon_intensity = read_scalar(sky_material, "MoonIntensity")
    try:
        moon_direction = sky.get_resolved_night_light_direction()
    except Exception:
        moon_direction = unreal.Vector(0.0, 0.0, 0.0)

    return {
        "minute": minute,
        "phase": str(get_prop(sky, ["CurrentTimeOfDayPhase", "current_time_of_day_phase"], "")),
        "sun_elevation": round(float(get_prop(sky, ["CurrentSunElevationDegrees", "current_sun_elevation_degrees"], 0.0)), 5),
        "night_light_intensity": round(float(get_prop(night_comp, "intensity", -1.0)), 5) if night_comp else None,
        "moon_intensity_param": round(float(moon_intensity), 5) if moon_intensity is not None else None,
        "moon_direction": vec_to_list(moon_direction),
    }


def patch_level_instance(mask_texture: unreal.Texture2D) -> dict:
    if not find_actor("StylizedSky_Main"):
        unreal.EditorLevelLibrary.load_level(LEVEL)

    sky = find_actor("StylizedSky_Main")
    if not sky:
        raise RuntimeError("StylizedSky_Main not found")

    night_light, created_night_light = ensure_night_light()
    project_mi = unreal.EditorAssetLibrary.load_asset("/Game/Cubeless/Env/Sky/Materials/MI_StylizedSky_Dome_MoonRGBMask")
    plugin_mi = unreal.EditorAssetLibrary.load_asset("/StylizedSky/Materials/MI_StylizedSky_Dome_MoonRGBMask")
    sky_material = plugin_mi or project_mi
    if not sky_material:
        raise RuntimeError("Moon sky material instance was not created")

    sky.modify()
    failed_level_sets = set_common_sky_props(sky, sky_material, night_light)
    failed_bp_sets = patch_blueprint_defaults(sky_material)

    samples = [sample_sky(sky, night_light, minute) for minute in [720, 1260]]
    try:
        sky.set_time_of_day_minutes(1260)
    except Exception:
        set_prop(sky, ["TimeOfDayMinutes", "time_of_day_minutes"], 1260)
        set_prop(sky, ["TimeOfDayHours", "time_of_day_hours"], 21.0)
    set_prop(sky, ["bAnimateTimeOfDay", "b_animate_time_of_day"], True)
    set_prop(sky, ["TimeOfDaySpeedMinutesPerSecond", "time_of_day_speed_minutes_per_second"], 48.0)
    sky.refresh_sky()

    unreal.EditorLevelLibrary.save_current_level()
    return {
        "sky": sky.get_actor_label(),
        "night_light": night_light.get_actor_label() if night_light else None,
        "created_night_light": created_night_light,
        "sky_material": sky_material.get_path_name(),
        "failed_level_sets": failed_level_sets,
        "failed_bp_sets": failed_bp_sets,
        "samples": samples,
        "restored_minute": int(get_prop(sky, ["TimeOfDayMinutes", "time_of_day_minutes"], -1)),
        "restored_speed_minutes_per_second": float(get_prop(sky, ["TimeOfDaySpeedMinutesPerSecond", "time_of_day_speed_minutes_per_second"], -1.0)),
        "restored_animate": bool(get_prop(sky, ["bAnimateTimeOfDay", "b_animate_time_of_day"], False)),
    }


def main() -> None:
    try:
        mask_texture = patch_texture()
        changed = [STARS_MASK_TEXTURE_PATH]
        for material_path in SKY_MATERIALS:
            if patch_sky_material(material_path, mask_texture):
                changed.append(material_path)
        changed.extend(patch_material_instances(mask_texture))
        level_result = patch_level_instance(mask_texture)
        result = {"changed": changed, "level": level_result}
        unreal.log("STYLIZED_SKY_NIGHT_LIGHT_MOON_OK=" + json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        unreal.log_error("STYLIZED_SKY_NIGHT_LIGHT_MOON_ERROR: " + repr(exc))
        unreal.log_error(traceback.format_exc())
        raise


main()
