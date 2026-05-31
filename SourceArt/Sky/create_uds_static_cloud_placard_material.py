from __future__ import annotations

import unreal


MATERIAL_FOLDER = "/Game/Cubeless/Env/Sky/Materials"
TEXTURE_PATH = "/Game/Cubeless/Env/Sky/Textures/T_CloudPlaneAtlas_LightPacked_UDSLike"
UDS_VOLUMETRIC_CLOUDS_MPC_PATH = "/Game/UltraDynamicSky/Materials/Material_Functions/UDS_VolumetricClouds_MPC"
UDS_WEATHER_MPC_PATH = "/Game/UltraDynamicSky/Materials/Weather/UltraDynamicWeather_Parameters"

MASTER_NAME = "M_CloudPlane_LightPacked_Master"
DEFAULT_MI_NAME = "MI_CloudPlane_LightPacked_Default"
TILE_MI_PREFIX = "MI_CloudPlane_LightPacked_Tile"


# Values sampled from the placed Ultra_Dynamic_Sky actor's sky MID in
# /Game/ThirdPerson/Lvl_ThirdPerson while using UDS static sky/static clouds.
UDS_STATIC_LIGHTING_MASK = (0.586461, 0.340078, 0.073461, 1.0)
UDS_STATIC_COLOR_TINT = (0.701009, 0.702989, 0.760417, 1.0)
UDS_STATIC_SHADOW_TINT = (0.869251, 0.840228, 0.815230, 0.0)
UDS_AMBIENT_COLOR = (0.140302, 0.253465, 0.471929, 0.0)

UDS_CLOUD_DENSITY = 1.596
UDS_CLOUD_OPACITY = 0.82
UDS_SUN_LIGHTING_INTENSITY = 3.0
UDS_SHADING_OFFSET = 0.10
UDS_SHADING_GRADIENT_WIDTH = 0.75
MPC_SUN_VECTOR_INFLUENCE = 1.0
MPC_CLOUD_DENSITY_INFLUENCE = 0.35
MPC_CLOUD_COVERAGE_INFLUENCE = 0.40
MPC_SHADOW_CANCEL_INFLUENCE = 0.0


def _load(path: str):
    return unreal.load_asset(path)


def _create_or_load_material(name: str) -> unreal.Material:
    path = f"{MATERIAL_FOLDER}/{name}"
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = _load(path)
    if not material:
        unreal.EditorAssetLibrary.make_directory(MATERIAL_FOLDER)
        material = tools.create_asset(name, MATERIAL_FOLDER, unreal.Material, unreal.MaterialFactoryNew())
    if not material:
        raise RuntimeError(f"Failed to create material: {path}")
    return material


def _create_or_load_mi(name: str, parent: unreal.MaterialInterface) -> unreal.MaterialInstanceConstant:
    path = f"{MATERIAL_FOLDER}/{name}"
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi = _load(path)
    if not mi:
        unreal.EditorAssetLibrary.make_directory(MATERIAL_FOLDER)
        mi = tools.create_asset(name, MATERIAL_FOLDER, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    if not mi:
        raise RuntimeError(f"Failed to create material instance: {path}")
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent)
    return mi


def _scalar_param(material: unreal.Material, name: str, value: float, x: int, y: int, group: str = "UDS Static Cloud Match"):
    node = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionScalarParameter, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("default_value", float(value))
    node.set_editor_property("group", group)
    return node


def _vector_param(material: unreal.Material, name: str, value: tuple[float, float, float, float], x: int, y: int, group: str = "UDS Static Cloud Match"):
    node = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionVectorParameter, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("default_value", unreal.LinearColor(*value))
    node.set_editor_property("group", group)
    return node


def _texture_param(material: unreal.Material, name: str, texture: unreal.Texture2D, x: int, y: int):
    node = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("group", "Texture")
    node.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    if texture:
        node.set_editor_property("texture", texture)
    return node


def _collection_param(material: unreal.Material, collection: unreal.MaterialParameterCollection, name: str, x: int, y: int):
    node = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionCollectionParameter, x, y)
    node.set_editor_property("collection", collection)
    node.set_editor_property("parameter_name", name)
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


def _set_common_mi_params(mi: unreal.MaterialInstanceConstant, uv_rect: tuple[float, float, float, float]) -> None:
    texture = _load(TEXTURE_PATH)
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, "PackedCloudAtlas", texture)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "UVRect_OffsetXY_ScaleZW", unreal.LinearColor(*uv_rect))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "LightWeights_RGB", unreal.LinearColor(*UDS_STATIC_LIGHTING_MASK))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "CloudShadowTint", unreal.LinearColor(*UDS_STATIC_COLOR_TINT))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "CloudLightTint", unreal.LinearColor(*UDS_STATIC_SHADOW_TINT))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "TimeOfDayTint", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "AmbientColor", unreal.LinearColor(*UDS_AMBIENT_COLOR))
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "Opacity", UDS_CLOUD_OPACITY)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "CloudDensity", UDS_CLOUD_DENSITY)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "CloudIntensity", 1.15)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "SunLightingIntensity", UDS_SUN_LIGHTING_INTENSITY)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "ShadingClouds_Offset", UDS_SHADING_OFFSET)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "ShadingClouds_GradientWidth", UDS_SHADING_GRADIENT_WIDTH)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "RimLightAmount", 0.16)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "AmbientInfluence", 0.10)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "AlphaFeather", 0.18)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "MPCSunVectorInfluence", MPC_SUN_VECTOR_INFLUENCE)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "MPCCloudDensityInfluence", MPC_CLOUD_DENSITY_INFLUENCE)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "MPCCloudCoverageInfluence", MPC_CLOUD_COVERAGE_INFLUENCE)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "MPCShadowCancelInfluence", MPC_SHADOW_CANCEL_INFLUENCE)


def create_material() -> unreal.Material:
    texture = _load(TEXTURE_PATH)
    if not texture:
        raise RuntimeError(f"Missing packed cloud atlas: {TEXTURE_PATH}")
    clouds_mpc = _load(UDS_VOLUMETRIC_CLOUDS_MPC_PATH)
    weather_mpc = _load(UDS_WEATHER_MPC_PATH)
    if not clouds_mpc:
        raise RuntimeError(f"Missing UDS cloud MPC: {UDS_VOLUMETRIC_CLOUDS_MPC_PATH}")
    if not weather_mpc:
        raise RuntimeError(f"Missing UDS weather MPC: {UDS_WEATHER_MPC_PATH}")

    material = _create_or_load_material(MASTER_NAME)
    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)

    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)

    uv = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, -1200, -160)
    uv_rect = _vector_param(material, "UVRect_OffsetXY_ScaleZW", (0.0, 0.0, 0.25, 0.5), -1200, 0, "Atlas")
    packed = _texture_param(material, "PackedCloudAtlas", texture, -760, -160)

    light_weights = _vector_param(material, "LightWeights_RGB", UDS_STATIC_LIGHTING_MASK, -760, 80)
    cloud_light = _vector_param(material, "CloudLightTint", UDS_STATIC_SHADOW_TINT, -760, 220)
    cloud_shadow = _vector_param(material, "CloudShadowTint", UDS_STATIC_COLOR_TINT, -760, 360)
    time_tint = _vector_param(material, "TimeOfDayTint", (1.0, 1.0, 1.0, 1.0), -760, 500)
    ambient = _vector_param(material, "AmbientColor", UDS_AMBIENT_COLOR, -760, 640)

    opacity = _scalar_param(material, "Opacity", UDS_CLOUD_OPACITY, -760, 820)
    density = _scalar_param(material, "CloudDensity", UDS_CLOUD_DENSITY, -760, 960)
    intensity = _scalar_param(material, "CloudIntensity", 1.15, -760, 1100)
    sun_intensity = _scalar_param(material, "SunLightingIntensity", UDS_SUN_LIGHTING_INTENSITY, -760, 1240)
    shade_offset = _scalar_param(material, "ShadingClouds_Offset", UDS_SHADING_OFFSET, -760, 1380)
    shade_width = _scalar_param(material, "ShadingClouds_GradientWidth", UDS_SHADING_GRADIENT_WIDTH, -760, 1520)
    rim_amount = _scalar_param(material, "RimLightAmount", 0.16, -760, 1660)
    ambient_influence = _scalar_param(material, "AmbientInfluence", 0.10, -760, 1800)
    alpha_feather = _scalar_param(material, "AlphaFeather", 0.18, -760, 1940)
    mpc_sun_influence = _scalar_param(material, "MPCSunVectorInfluence", MPC_SUN_VECTOR_INFLUENCE, -760, 2080, "UDS MPC")
    mpc_density_influence = _scalar_param(material, "MPCCloudDensityInfluence", MPC_CLOUD_DENSITY_INFLUENCE, -760, 2220, "UDS MPC")
    mpc_coverage_influence = _scalar_param(material, "MPCCloudCoverageInfluence", MPC_CLOUD_COVERAGE_INFLUENCE, -760, 2360, "UDS MPC")
    mpc_shadow_cancel_influence = _scalar_param(material, "MPCShadowCancelInfluence", MPC_SHADOW_CANCEL_INFLUENCE, -760, 2500, "UDS MPC")

    mpc_sun_vector = _collection_param(material, weather_mpc, "Sun Vector", -440, -420)
    mpc_cloud_coverage = _collection_param(material, weather_mpc, "Cloud Coverage", -440, -280)
    mpc_cloud_shadow_light_vector = _collection_param(material, clouds_mpc, "Cloud Shadows Light Vector", -440, -140)
    mpc_cloud_density = _collection_param(material, clouds_mpc, "Cloud Density", -440, 0)
    mpc_cloud_coverage_target_opacity = _collection_param(material, clouds_mpc, "Cloud Coverage Target Opacity", -440, 140)
    mpc_cloud_shadows_cancel = _collection_param(material, clouds_mpc, "Cloud Shadows Cancel", -440, 280)

    uv_code = r"""
return UV * float2(UVRect.z, 0.5) + UVRect.xy;
"""
    uv_custom = _custom(
        material,
        "4x2 atlas tile UV",
        uv_code,
        unreal.CustomMaterialOutputType.CMOT_FLOAT2,
        ["UV", "UVRect"],
        -980,
        -100,
    )
    _connect(uv, "", uv_custom, "UV")
    _connect(uv_rect, "", uv_custom, "UVRect")
    _connect(uv_custom, "", packed, "UVs")

    color_code = r"""
float3 weights = max(LightWeights_RGB.rgb, float3(0.0, 0.0, 0.0));
weights /= max(weights.x + weights.y + weights.z, 0.0001);

float3 sunVector = MPCSunVector.xyz;
float sunVectorLen = length(sunVector);
float3 shadowVector = MPCCloudShadowLightVector.xyz;
float shadowVectorLen = length(shadowVector);
float3 udsVector = normalize(lerp(shadowVector, sunVector, step(0.001, sunVectorLen)));
float validVector = max(step(0.001, sunVectorLen), step(0.001, shadowVectorLen));
float3 vectorWeights = float3(
    saturate(0.45 + udsVector.x * 0.40),
    saturate(0.45 - udsVector.x * 0.40),
    saturate(0.20 + abs(udsVector.z) * 0.55)
);
vectorWeights /= max(vectorWeights.x + vectorWeights.y + vectorWeights.z, 0.0001);
weights = lerp(weights, vectorWeights, saturate(MPCSunVectorInfluence) * validVector);

float responseRaw = saturate(dot(PackedRGBA.rgb, weights));
float shadeWidth = max(ShadingClouds_GradientWidth, 0.001);
float shade = smoothstep(ShadingClouds_Offset, ShadingClouds_Offset + shadeWidth, responseRaw);
float shadowCancel = saturate(MPCCloudShadowsCancel) * saturate(MPCShadowCancelInfluence);
shade = lerp(shade, max(shade, 0.72), shadowCancel);

// The current UDS static-sky setup stores the warm lit color in
// "Static Clouds Shadow Tint" and the cooler body color in
// "Static Clouds Color Tint", so the material instance maps them to
// CloudLightTint and CloudShadowTint respectively.
float3 tint = lerp(CloudShadowTint.rgb, CloudLightTint.rgb, shade);

float rim = saturate(max(PackedRGBA.r, PackedRGBA.g) - PackedRGBA.b * 0.35);
float sunScale = saturate(SunLightingIntensity / 3.0);
float coverage = saturate(max(MPCCloudCoverage, MPCCloudCoverageTargetOpacity));
float coverageScale = lerp(1.0, max(coverage, 0.25), saturate(MPCCloudCoverageInfluence));
float3 rimLight = CloudLightTint.rgb * rim * RimLightAmount * sunScale;
float3 ambientLift = AmbientColor.rgb * AmbientInfluence * (1.0 - shade) * (0.35 + PackedAlpha);

return max(tint + rimLight + ambientLift, float3(0.0, 0.0, 0.0)) * TimeOfDayTint.rgb * CloudIntensity * coverageScale;
"""
    color_custom = _custom(
        material,
        "UDS static sky cloud color",
        color_code,
        unreal.CustomMaterialOutputType.CMOT_FLOAT3,
        [
            "PackedRGBA",
            "PackedAlpha",
            "LightWeights_RGB",
            "MPCSunVector",
            "MPCCloudShadowLightVector",
            "MPCCloudCoverage",
            "MPCCloudCoverageTargetOpacity",
            "MPCCloudShadowsCancel",
            "CloudLightTint",
            "CloudShadowTint",
            "TimeOfDayTint",
            "AmbientColor",
            "CloudIntensity",
            "SunLightingIntensity",
            "ShadingClouds_Offset",
            "ShadingClouds_GradientWidth",
            "RimLightAmount",
            "AmbientInfluence",
            "MPCSunVectorInfluence",
            "MPCCloudCoverageInfluence",
            "MPCShadowCancelInfluence",
        ],
        -260,
        420,
    )

    for source, input_name in [
        (packed, "PackedRGBA"),
        (light_weights, "LightWeights_RGB"),
        (mpc_sun_vector, "MPCSunVector"),
        (mpc_cloud_shadow_light_vector, "MPCCloudShadowLightVector"),
        (mpc_cloud_coverage, "MPCCloudCoverage"),
        (mpc_cloud_coverage_target_opacity, "MPCCloudCoverageTargetOpacity"),
        (mpc_cloud_shadows_cancel, "MPCCloudShadowsCancel"),
        (cloud_light, "CloudLightTint"),
        (cloud_shadow, "CloudShadowTint"),
        (time_tint, "TimeOfDayTint"),
        (ambient, "AmbientColor"),
        (intensity, "CloudIntensity"),
        (sun_intensity, "SunLightingIntensity"),
        (shade_offset, "ShadingClouds_Offset"),
        (shade_width, "ShadingClouds_GradientWidth"),
        (rim_amount, "RimLightAmount"),
        (ambient_influence, "AmbientInfluence"),
        (mpc_sun_influence, "MPCSunVectorInfluence"),
        (mpc_coverage_influence, "MPCCloudCoverageInfluence"),
        (mpc_shadow_cancel_influence, "MPCShadowCancelInfluence"),
    ]:
        _connect(source, "", color_custom, input_name)
    _connect(packed, "A", color_custom, "PackedAlpha")

    opacity_code = r"""
float alpha = saturate(PackedAlpha);
float mpcDensity = max(MPCCloudDensity, 0.0);
float mpcDensityScale = max(mpcDensity / max(CloudDensity, 0.001), 0.15);
float densityScale = lerp(1.0, mpcDensityScale, saturate(MPCCloudDensityInfluence) * step(0.001, mpcDensity));
float coverage = saturate(max(MPCCloudCoverage, MPCCloudCoverageTargetOpacity));
float coverageScale = lerp(1.0, max(coverage, 0.25), saturate(MPCCloudCoverageInfluence));
float dense = saturate(alpha * max(CloudDensity, 0.0) * densityScale);
float feather = smoothstep(0.01, max(AlphaFeather, 0.011), alpha) * 0.58;
float body = smoothstep(0.08, 0.34, dense);
return saturate(max(feather, body) * Opacity * coverageScale);
"""
    opacity_custom = _custom(
        material,
        "UDS static cloud alpha",
        opacity_code,
        unreal.CustomMaterialOutputType.CMOT_FLOAT1,
        [
            "PackedAlpha",
            "Opacity",
            "CloudDensity",
            "AlphaFeather",
            "MPCCloudDensity",
            "MPCCloudDensityInfluence",
            "MPCCloudCoverage",
            "MPCCloudCoverageTargetOpacity",
            "MPCCloudCoverageInfluence",
        ],
        -260,
        1040,
    )
    _connect(packed, "A", opacity_custom, "PackedAlpha")
    _connect(opacity, "", opacity_custom, "Opacity")
    _connect(density, "", opacity_custom, "CloudDensity")
    _connect(alpha_feather, "", opacity_custom, "AlphaFeather")
    _connect(mpc_cloud_density, "", opacity_custom, "MPCCloudDensity")
    _connect(mpc_density_influence, "", opacity_custom, "MPCCloudDensityInfluence")
    _connect(mpc_cloud_coverage, "", opacity_custom, "MPCCloudCoverage")
    _connect(mpc_cloud_coverage_target_opacity, "", opacity_custom, "MPCCloudCoverageTargetOpacity")
    _connect(mpc_coverage_influence, "", opacity_custom, "MPCCloudCoverageInfluence")

    unreal.MaterialEditingLibrary.connect_material_property(color_custom, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(opacity_custom, "", unreal.MaterialProperty.MP_OPACITY)
    unreal.MaterialEditingLibrary.set_material_usage(material, unreal.MaterialUsage.MATUSAGE_STATIC_MESH)
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def create_instances(material: unreal.Material) -> list[str]:
    saved_paths = []
    default_mi = _create_or_load_mi(DEFAULT_MI_NAME, material)
    _set_common_mi_params(default_mi, (0.0, 0.0, 0.25, 0.5))
    unreal.EditorAssetLibrary.save_loaded_asset(default_mi, only_if_is_dirty=False)
    saved_paths.append(f"{MATERIAL_FOLDER}/{DEFAULT_MI_NAME}")

    for index in range(8):
        x = (index % 4) * 0.25
        y = (index // 4) * 0.5
        name = f"{TILE_MI_PREFIX}_{index:02d}"
        tile_mi = _create_or_load_mi(name, material)
        _set_common_mi_params(tile_mi, (x, y, 0.25, 0.5))
        unreal.EditorAssetLibrary.save_loaded_asset(tile_mi, only_if_is_dirty=False)
        saved_paths.append(f"{MATERIAL_FOLDER}/{name}")

    return saved_paths


def main() -> None:
    material = create_material()
    saved_paths = create_instances(material)
    unreal.log("Created UDS static-sky cloud placard material and instances:")
    unreal.log(f"  {MATERIAL_FOLDER}/{MASTER_NAME}")
    for path in saved_paths:
        unreal.log(f"  {path}")


if __name__ == "__main__":
    main()
