from __future__ import annotations

import unreal


PLUGIN_MATERIAL_FOLDER = "/StylizedSky/Materials"
PROJECT_MATERIAL_FOLDER = "/Game/Cubeless/Env/Sky/Materials"
TEXTURE_PATH = "/Game/Cubeless/Env/Sky/Textures/T_CloudPlaneAtlas_LightPacked_UDSLike"
STARS_MASK_TEXTURE_PATH = "/Game/Cubeless/Env/Sky/Textures/T_StylizedSky_Stars_Mask_Tile_RGBA"


def _material_folder() -> str:
    # The plugin mount exists after the editor restarts with StylizedSky enabled.
    if unreal.EditorAssetLibrary.does_directory_exist("/StylizedSky"):
        return PLUGIN_MATERIAL_FOLDER
    return PROJECT_MATERIAL_FOLDER


MATERIAL_FOLDER = _material_folder()


def _load(path: str):
    return unreal.EditorAssetLibrary.load_asset(path)


def _create_or_reset_material(name: str) -> unreal.Material:
    path = f"{MATERIAL_FOLDER}/{name}"
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        material = _load(path)
    else:
        unreal.EditorAssetLibrary.make_directory(MATERIAL_FOLDER)
        material = tools.create_asset(name, MATERIAL_FOLDER, unreal.Material, unreal.MaterialFactoryNew())

    if not material:
        raise RuntimeError(f"Failed to create material: {path}")
    return material


def _create_or_reset_mi(name: str, parent: unreal.MaterialInterface) -> unreal.MaterialInstanceConstant:
    path = f"{MATERIAL_FOLDER}/{name}"
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mi = _load(path)
    else:
        mi = tools.create_asset(name, MATERIAL_FOLDER, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())

    if not mi:
        raise RuntimeError(f"Failed to create material instance: {path}")

    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent)
    return mi


def _vector_param(material: unreal.Material, name: str, value: tuple[float, float, float, float], x: int, y: int):
    node = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionVectorParameter, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("default_value", unreal.LinearColor(*value))
    return node


def _scalar_param(material: unreal.Material, name: str, value: float, x: int, y: int):
    node = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionScalarParameter, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("default_value", float(value))
    return node


def _texture_param(material: unreal.Material, name: str, texture: unreal.Texture2D, x: int, y: int):
    node = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    node.set_editor_property("parameter_name", name)
    if texture:
        node.set_editor_property("texture", texture)
    if name in {"PackedCloudAtlas", "StarsMaskMap"}:
        node.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    return node


def _custom(material: unreal.Material, description: str, code: str, output_type, inputs: list[str], x: int, y: int):
    node = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionCustom, x, y)
    node.set_editor_property("description", description)
    node.set_editor_property("code", code)
    node.set_editor_property("output_type", output_type)
    custom_inputs = []
    for input_name in inputs:
        custom_input = unreal.CustomInput()
        custom_input.set_editor_property("input_name", input_name)
        custom_inputs.append(custom_input)
    node.set_editor_property("inputs", custom_inputs)
    return node


def _connect(source, source_output: str, target, target_input: str) -> None:
    if not unreal.MaterialEditingLibrary.connect_material_expressions(source, source_output, target, target_input):
        raise RuntimeError(f"Failed material expression connection: {source} -> {target_input}")


def create_sky_dome_material() -> unreal.Material:
    stars_mask_texture = _load(STARS_MASK_TEXTURE_PATH)
    material = _create_or_reset_material("M_StylizedSky_Dome_RGBMask")
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)

    view_dir = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionCameraVectorWS, -760, -120)
    sun_dir = _vector_param(material, "SunDirection", (0.35, -0.25, 0.90, 0.0), -760, 20)
    zenith = _vector_param(material, "SkyZenithColor", (0.18, 0.42, 0.88, 1.0), -760, 160)
    horizon = _vector_param(material, "SkyHorizonColor", (0.78, 0.88, 1.0, 1.0), -760, 300)
    sun_color = _vector_param(material, "SunColor", (1.0, 0.94, 0.75, 1.0), -760, 440)
    stars = _scalar_param(material, "StarsIntensity", 0.0, -760, 580)
    stars_color = _vector_param(material, "StarsColor", (0.82, 0.90, 1.0, 1.0), -760, 720)
    stars_tiling = _scalar_param(material, "StarsTiling", 3.0, -760, 860)
    stars_threshold = _scalar_param(material, "StarsMaskThreshold", 0.22, -760, 1000)
    stars_power = _scalar_param(material, "StarsMaskPower", 1.45, -760, 1140)
    stars_uv_code = r"""
float3 dir = normalize(-ViewDir);
float u = atan2(dir.y, dir.x) * 0.15915494309 + 0.5;
float v = asin(clamp(dir.z, -1.0, 1.0)) * 0.31830988618 + 0.5;
return float2(u, v) * max(StarsTiling, 0.1);
"""
    stars_uv = _custom(
        material,
        "Spherical star UV",
        stars_uv_code,
        unreal.CustomMaterialOutputType.CMOT_FLOAT2,
        ["ViewDir", "StarsTiling"],
        -520,
        720,
    )
    stars_mask = _texture_param(material, "StarsMaskMap", stars_mask_texture, -260, 720)
    _connect(view_dir, "", stars_uv, "ViewDir")
    _connect(stars_tiling, "", stars_uv, "StarsTiling")
    _connect(stars_uv, "", stars_mask, "UVs")

    sky_code = r"""
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
    custom = _custom(
        material,
        "Stylized sky dome color",
        sky_code,
        unreal.CustomMaterialOutputType.CMOT_FLOAT3,
        ["ViewDir", "SunDirection", "SkyZenithColor", "SkyHorizonColor", "SunColor", "StarsIntensity", "StarsColor", "StarsMaskThreshold", "StarsMaskPower", "StarsMask"],
        -260,
        160,
    )

    for source, input_name in [
        (view_dir, "ViewDir"),
        (sun_dir, "SunDirection"),
        (zenith, "SkyZenithColor"),
        (horizon, "SkyHorizonColor"),
        (sun_color, "SunColor"),
        (stars, "StarsIntensity"),
        (stars_color, "StarsColor"),
        (stars_threshold, "StarsMaskThreshold"),
        (stars_power, "StarsMaskPower"),
        (stars_mask, "StarsMask"),
    ]:
        _connect(source, "", custom, input_name)

    unreal.MaterialEditingLibrary.connect_material_property(custom, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.EditorAssetLibrary.save_asset(f"{MATERIAL_FOLDER}/M_StylizedSky_Dome_RGBMask", only_if_is_dirty=False)
    return material


def create_cloud_materials() -> unreal.Material:
    texture = _load(TEXTURE_PATH)
    material = _create_or_reset_material("M_StylizedSky_Cloud_LightPacked_Custom")
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)

    uv = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, -1120, -80)
    uv_rect = _vector_param(material, "UVRect_OffsetXY_ScaleZW", (0.0, 0.0, 0.25, 0.5), -1120, 80)
    packed = _texture_param(material, "PackedCloudAtlas", texture, -520, -80)
    light_weights = _vector_param(material, "LightWeights_RGB", (0.42, 0.33, 0.25, 0.0), -520, 120)
    light_tint = _vector_param(material, "CloudLightTint", (1.0, 0.97, 0.88, 1.0), -520, 260)
    shadow_tint = _vector_param(material, "CloudShadowTint", (0.44, 0.55, 0.72, 1.0), -520, 400)
    time_tint = _vector_param(material, "TimeOfDayTint", (1.0, 1.0, 1.0, 1.0), -520, 540)
    opacity = _scalar_param(material, "Opacity", 0.74, -520, 680)
    intensity = _scalar_param(material, "CloudIntensity", 1.12, -520, 820)

    # Unreal custom node vector inputs are compiled as float3 in this material path.
    # Keep the historical UVRect param layout as X/Y offset and Z scale-x, then
    # use the fixed 4x2 atlas scale-y here.
    uv_code = "return UV * float2(UVRect.z, 0.5) + UVRect.xy;"
    uv_custom = _custom(
        material,
        "Atlas UV rect",
        uv_code,
        unreal.CustomMaterialOutputType.CMOT_FLOAT2,
        ["UV", "UVRect"],
        -840,
        -20,
    )
    _connect(uv, "", uv_custom, "UV")
    _connect(uv_rect, "", uv_custom, "UVRect")
    _connect(uv_custom, "", packed, "UVs")

    cloud_color_code = r"""
float3 weights = saturate(LightWeights_RGB.rgb);
float weightSum = max(dot(weights, float3(1.0, 1.0, 1.0)), 0.0001);
weights /= weightSum;

float response = saturate(dot(PackedRGBA.rgb, weights));
float rim = saturate(max(PackedRGBA.r, PackedRGBA.g) - PackedRGBA.b * 0.35);
float3 tint = lerp(CloudShadowTint.rgb, CloudLightTint.rgb, response);
tint += CloudLightTint.rgb * rim * 0.18;

return tint * TimeOfDayTint.rgb * CloudIntensity;
"""
    color_custom = _custom(
        material,
        "UDS-like packed cloud lighting",
        cloud_color_code,
        unreal.CustomMaterialOutputType.CMOT_FLOAT3,
        ["PackedRGBA", "LightWeights_RGB", "CloudLightTint", "CloudShadowTint", "TimeOfDayTint", "CloudIntensity"],
        -80,
        230,
    )

    for source, input_name in [
        (packed, "PackedRGBA"),
        (light_weights, "LightWeights_RGB"),
        (light_tint, "CloudLightTint"),
        (shadow_tint, "CloudShadowTint"),
        (time_tint, "TimeOfDayTint"),
        (intensity, "CloudIntensity"),
    ]:
        _connect(source, "", color_custom, input_name)

    opacity_code = r"""
float alpha = saturate(PackedAlpha);
float feather = smoothstep(0.01, 0.18, alpha) * 0.65;
float bodyOcclusion = smoothstep(0.08, 0.30, alpha);
return saturate(max(feather, bodyOcclusion) * Opacity);
"""
    opacity_custom = _custom(
        material,
        "Cloud atlas alpha",
        opacity_code,
        unreal.CustomMaterialOutputType.CMOT_FLOAT1,
        ["PackedAlpha", "Opacity"],
        -80,
        680,
    )
    _connect(packed, "A", opacity_custom, "PackedAlpha")
    _connect(opacity, "", opacity_custom, "Opacity")

    unreal.MaterialEditingLibrary.connect_material_property(color_custom, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(opacity_custom, "", unreal.MaterialProperty.MP_OPACITY)
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.EditorAssetLibrary.save_asset(f"{MATERIAL_FOLDER}/M_StylizedSky_Cloud_LightPacked_Custom", only_if_is_dirty=False)

    default_mi = _create_or_reset_mi("MI_StylizedSky_Cloud_Default", material)
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(default_mi, "PackedCloudAtlas", texture)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(default_mi, "UVRect_OffsetXY_ScaleZW", unreal.LinearColor(0.0, 0.0, 0.25, 0.5))
    unreal.EditorAssetLibrary.save_asset(f"{MATERIAL_FOLDER}/MI_StylizedSky_Cloud_Default", only_if_is_dirty=False)

    for index in range(8):
        x = (index % 4) * 0.25
        y = (index // 4) * 0.5
        tile_mi = _create_or_reset_mi(f"MI_StylizedSky_Cloud_Tile_{index:02d}", material)
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(tile_mi, "PackedCloudAtlas", texture)
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(tile_mi, "UVRect_OffsetXY_ScaleZW", unreal.LinearColor(x, y, 0.25, 0.5))
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(tile_mi, "LightWeights_RGB", unreal.LinearColor(0.42, 0.33, 0.25, 0.0))
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(tile_mi, "CloudLightTint", unreal.LinearColor(1.0, 0.97, 0.88, 1.0))
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(tile_mi, "CloudShadowTint", unreal.LinearColor(0.44, 0.55, 0.72, 1.0))
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(tile_mi, "TimeOfDayTint", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(tile_mi, "Opacity", 0.74)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(tile_mi, "CloudIntensity", 1.12)
        unreal.EditorAssetLibrary.save_asset(f"{MATERIAL_FOLDER}/MI_StylizedSky_Cloud_Tile_{index:02d}", only_if_is_dirty=False)

    return material


def create_material_instances(sky_material: unreal.Material) -> None:
    stars_mask_texture = _load(STARS_MASK_TEXTURE_PATH)
    sky_mi = _create_or_reset_mi("MI_StylizedSky_Dome_RGBMask", sky_material)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(sky_mi, "SunDirection", unreal.LinearColor(0.35, -0.25, 0.90, 0.0))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(sky_mi, "SkyZenithColor", unreal.LinearColor(0.18, 0.42, 0.88, 1.0))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(sky_mi, "SkyHorizonColor", unreal.LinearColor(0.78, 0.88, 1.0, 1.0))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(sky_mi, "SunColor", unreal.LinearColor(1.0, 0.94, 0.75, 1.0))
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(sky_mi, "StarsIntensity", 0.0)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(sky_mi, "StarsColor", unreal.LinearColor(0.82, 0.90, 1.0, 1.0))
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(sky_mi, "StarsTiling", 3.0)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(sky_mi, "StarsMaskThreshold", 0.22)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(sky_mi, "StarsMaskPower", 1.45)
    if stars_mask_texture:
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(sky_mi, "StarsMaskMap", stars_mask_texture)
    unreal.EditorAssetLibrary.save_asset(f"{MATERIAL_FOLDER}/MI_StylizedSky_Dome_RGBMask", only_if_is_dirty=False)


def main() -> None:
    sky_material = create_sky_dome_material()
    create_cloud_materials()
    create_material_instances(sky_material)
    unreal.log("Created StylizedSky custom-node dome and cloud materials.")


if __name__ == "__main__":
    main()
