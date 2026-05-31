from __future__ import annotations

import traceback
import unreal


MASK_PATH = "/Game/Cubeless/Env/Sky/Textures/T_StylizedSky_Stars_Mask_Tile_RGBA"
SKY_MATERIALS = [
    "/StylizedSky/Materials/M_StylizedSky_Dome_RGBMask",
    "/Game/Cubeless/Env/Sky/Materials/M_StylizedSky_Dome_RGBMask",
]
SKY_MIS = [
    "/StylizedSky/Materials/MI_StylizedSky_Dome_RGBMask",
    "/Game/Cubeless/Env/Sky/Materials/MI_StylizedSky_Dome_RGBMask",
]

SKY_CODE = r"""
float3 dir = normalize(-ViewDir);
float3 sunDir = normalize(SunDirection.xyz);

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

return sky + SunColor.rgb * (sunDisk * 16.0 + sunGlow * 0.35) + starField + nightGlow;
"""

STARS_UV_CODE = r"""
float3 dir = normalize(-ViewDir);
float u = atan2(dir.y, dir.x) * 0.15915494309 + 0.5;
float v = asin(clamp(dir.z, -1.0, 1.0)) * 0.31830988618 + 0.5;
return float2(u, v) * max(StarsTiling, 0.1);
"""


def custom_input(name: str) -> unreal.CustomInput:
    item = unreal.CustomInput()
    item.set_editor_property("input_name", name)
    return item


def connect(source, target, input_name: str, source_output: str = "") -> None:
    if not unreal.MaterialEditingLibrary.connect_material_expressions(source, source_output, target, input_name):
        raise RuntimeError(f"Failed to connect {source} to {input_name}")


def patch_texture() -> unreal.Texture2D:
    texture = unreal.EditorAssetLibrary.load_asset(MASK_PATH)
    if not texture:
        raise RuntimeError(f"Missing stars mask texture: {MASK_PATH}")

    texture.set_editor_property("srgb", False)
    texture.set_editor_property("address_x", unreal.TextureAddress.TA_WRAP)
    texture.set_editor_property("address_y", unreal.TextureAddress.TA_WRAP)
    try:
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    except Exception as exc:
        unreal.log_warning(f"Could not set TC_MASKS: {exc!r}")
    unreal.EditorAssetLibrary.save_asset(MASK_PATH, only_if_is_dirty=False)
    return texture


def patch_sky_material(material_path: str, mask_texture: unreal.Texture2D) -> bool:
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

    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)

    sky_inputs = [
        "ViewDir",
        "SunDirection",
        "SkyZenithColor",
        "SkyHorizonColor",
        "SunColor",
        "StarsIntensity",
        "StarsColor",
        "StarsMaskThreshold",
        "StarsMaskPower",
        "StarsMask",
    ]

    def scalar_parameter(name: str, value: float, x: int, y: int):
        node = unreal.MaterialEditingLibrary.create_material_expression(
            material,
            unreal.MaterialExpressionScalarParameter,
            x,
            y,
        )
        node.set_editor_property("parameter_name", name)
        node.set_editor_property("default_value", value)
        return node

    def vector_parameter(name: str, value: unreal.LinearColor, x: int, y: int):
        node = unreal.MaterialEditingLibrary.create_material_expression(
            material,
            unreal.MaterialExpressionVectorParameter,
            x,
            y,
        )
        node.set_editor_property("parameter_name", name)
        node.set_editor_property("default_value", value)
        return node

    view_node = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionCameraVectorWS,
        -760,
        -120,
    )
    sun_direction = vector_parameter("SunDirection", unreal.LinearColor(0.35, -0.25, 0.90, 0.0), -760, 20)
    zenith = vector_parameter("SkyZenithColor", unreal.LinearColor(0.18, 0.42, 0.88, 1.0), -760, 160)
    horizon = vector_parameter("SkyHorizonColor", unreal.LinearColor(0.78, 0.88, 1.0, 1.0), -760, 300)
    sun_color = vector_parameter("SunColor", unreal.LinearColor(1.0, 0.94, 0.75, 1.0), -760, 440)
    stars_intensity = scalar_parameter("StarsIntensity", 0.0, -760, 580)
    stars_color = vector_parameter("StarsColor", unreal.LinearColor(0.82, 0.90, 1.0, 1.0), -760, 720)
    stars_tiling = scalar_parameter("StarsTiling", 3.0, -760, 860)
    stars_threshold = scalar_parameter("StarsMaskThreshold", 0.22, -760, 1000)
    stars_power = scalar_parameter("StarsMaskPower", 1.45, -760, 1140)

    stars_uv = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionCustom,
        -520,
        800,
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
        -260,
        820,
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
        -260,
        160,
    )
    sky_node.set_editor_property("description", "Stylized sky dome color")
    sky_node.set_editor_property("code", SKY_CODE)
    sky_node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    sky_node.set_editor_property("inputs", [custom_input(name) for name in sky_inputs])

    for source, input_name in [
        (view_node, "ViewDir"),
        (sun_direction, "SunDirection"),
        (zenith, "SkyZenithColor"),
        (horizon, "SkyHorizonColor"),
        (sun_color, "SunColor"),
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
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
            material_instance,
            "StarsMaskMap",
            mask_texture,
        )
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            material_instance,
            "StarsTiling",
            3.0,
        )
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
            material_instance,
            "StarsColor",
            unreal.LinearColor(0.82, 0.90, 1.0, 1.0),
        )
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            material_instance,
            "StarsMaskThreshold",
            0.22,
        )
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            material_instance,
            "StarsMaskPower",
            1.45,
        )
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            material_instance,
            "StarsIntensity",
            0.55,
        )
        unreal.EditorAssetLibrary.save_asset(material_instance_path, only_if_is_dirty=False)
        changed.append(material_instance_path)
    return changed


def patch_level_instance(mask_texture: unreal.Texture2D) -> str:
    sky = None
    sun = None
    skylight = None
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if label == "StylizedSky_Main":
            sky = actor
        elif label == "DirectionalLight":
            sun = actor
        elif label == "SkyLight":
            skylight = actor

    if not sky:
        return "Level:StylizedSky_Main missing"

    sky.modify()
    for prop in ("StarsMaskTexture", "stars_mask_texture"):
        try:
            sky.set_editor_property(prop, mask_texture)
        except Exception:
            pass
    for prop in ("StarsTiling", "stars_tiling"):
        try:
            sky.set_editor_property(prop, 3.0)
        except Exception:
            pass
    for prop, value in (("StarsMaskThreshold", 0.22), ("stars_mask_threshold", 0.22), ("StarsMaskPower", 1.45), ("stars_mask_power", 1.45)):
        try:
            sky.set_editor_property(prop, value)
        except Exception:
            pass
    for prop, value in (
        ("bUpdateEveryTick", True),
        ("b_update_every_tick", True),
        ("bUpdateInEditor", True),
        ("b_update_in_editor", True),
        ("bUseTimeOfDayPreview", True),
        ("b_use_time_of_day_preview", True),
        ("bDriveSunActorFromTimeOfDay", True),
        ("b_drive_sun_actor_from_time_of_day", True),
    ):
        try:
            sky.set_editor_property(prop, value)
        except Exception:
            pass

    night = sky.get_editor_property("NightLook")
    night.set_editor_property("stars_intensity", 0.55)
    try:
        night.set_editor_property("stars_color", unreal.LinearColor(0.82, 0.90, 1.0, 1.0))
    except Exception:
        pass
    night.set_editor_property("cloud_opacity", 1.85)
    sky.set_editor_property("NightLook", night)
    sky.set_editor_property("bApplyCloudPlaneSettingsOnConstruction", False)
    project_mi = unreal.EditorAssetLibrary.load_asset("/Game/Cubeless/Env/Sky/Materials/MI_StylizedSky_Dome_RGBMask")
    plugin_mi = unreal.EditorAssetLibrary.load_asset("/StylizedSky/Materials/MI_StylizedSky_Dome_RGBMask")
    sky_material = project_mi or plugin_mi
    if sky_material:
        for prop in ("SkyDomeMaterial", "sky_dome_material"):
            try:
                sky.set_editor_property(prop, sky_material)
            except Exception:
                pass

    if sun:
        sun.modify()
        rotation = unreal.Rotator()
        rotation.set_editor_property("pitch", 18.0)
        rotation.set_editor_property("yaw", 35.0)
        rotation.set_editor_property("roll", 0.0)
        sun.set_actor_rotation(rotation, False)
        light = sun.get_component_by_class(unreal.DirectionalLightComponent)
        if light:
            light.set_editor_property("intensity", 0.08)

    if skylight:
        sky_light_component = skylight.get_component_by_class(unreal.SkyLightComponent)
        if sky_light_component:
            skylight.modify()
            sky_light_component.set_editor_property("intensity", 0.12)

    sky.refresh_sky()
    unreal.EditorLevelLibrary.save_current_level()
    return f"Level:StylizedSky_Main stars mask applied, elevation={sky.get_sun_elevation_degrees()}"


def main() -> None:
    try:
        mask_texture = patch_texture()
        changed = [MASK_PATH]
        for material_path in SKY_MATERIALS:
            if patch_sky_material(material_path, mask_texture):
                changed.append(material_path)
        changed.extend(patch_material_instances(mask_texture))
        changed.append(patch_level_instance(mask_texture))
        unreal.log("Stars mask-map material update complete: " + ", ".join(changed))
    except Exception as exc:
        unreal.log_error(f"STARS_MASK_MAP_UPDATE_ERROR: {exc!r}")
        unreal.log_error(traceback.format_exc())
        raise


main()
