import traceback

import unreal


AUTHORING_BLUEPRINT_CLASS_PATH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/Blueprints/Authoring/"
    "BP_Cubeless_ED_PCGAuthoringSelector.BP_Cubeless_ED_PCGAuthoringSelector_C"
)
MATRIX_BLUEPRINT_CLASS_PATH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/Blueprints/Authoring/"
    "BP_Cubeless_ED_PCGMatrixSelector.BP_Cubeless_ED_PCGMatrixSelector_C"
)
PROFILE_MATRIX_BLUEPRINT_CLASS_PATH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/Blueprints/Authoring/"
    "BP_Cubeless_ED_PCGProfileMatrixSelector.BP_Cubeless_ED_PCGProfileMatrixSelector_C"
)
STYLE_PROFILE_MATRIX_BLUEPRINT_CLASS_PATH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/Blueprints/Authoring/"
    "BP_Cubeless_ED_PCGStyleProfileMatrixSelector.BP_Cubeless_ED_PCGStyleProfileMatrixSelector_C"
)
TREE_PROFILE_BLUEPRINT_CLASS_PATH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/Blueprints/Authoring/"
    "BP_Cubeless_ED_PCGTreeProfileSelector.BP_Cubeless_ED_PCGTreeProfileSelector_C"
)
MATERIAL_OVERRIDE_BLUEPRINT_CLASS_PATH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/Blueprints/Authoring/"
    "BP_Cubeless_ED_PCGMaterialOverrideSelector.BP_Cubeless_ED_PCGMaterialOverrideSelector_C"
)
ECOSYSTEM_BLUEPRINT_CLASS_PATH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/Blueprints/Authoring/"
    "BP_Cubeless_ED_PCGEcosystemSelector.BP_Cubeless_ED_PCGEcosystemSelector_C"
)
PRODUCTION_CANDIDATE_BLUEPRINT_CLASS_PATH = (
    "/Game/Cubeless/PCG/ProductionCandidates/Blueprints/"
    "BP_Cubeless_PCG_EcosystemCandidate.BP_Cubeless_PCG_EcosystemCandidate_C"
)
MATRIX_GRAPH_FOLDER = "/Game/Cubeless/PCG/ElectricDreamsLearning/DesignerMatrixCombos"
PROFILE_MATRIX_GRAPH_FOLDER = "/Game/Cubeless/PCG/ElectricDreamsLearning/DesignerProfileMatrixCombos"
STYLE_PROFILE_MATRIX_GRAPH_FOLDER = "/Game/Cubeless/PCG/ElectricDreamsLearning/DesignerStyleProfileMatrixCombos"
TREE_PROFILE_GRAPH_FOLDER = "/Game/Cubeless/PCG/ElectricDreamsLearning/TreeProfilePresets"
MATERIAL_OVERRIDE_GRAPH_FOLDER = "/Game/Cubeless/PCG/ElectricDreamsLearning/MaterialOverridePresets"
DYNAMIC_MATERIAL_AXIS_GRAPH_PATH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/DynamicMaterialPrototype/"
    "PCG_Cubeless_ED_DynamicMaterialAxis_ActorPropertySelector_Compat."
    "PCG_Cubeless_ED_DynamicMaterialAxis_ActorPropertySelector_Compat"
)
LANDSCAPE_TRACE_Z = 200000.0
LANDSCAPE_CONFORM_LOCAL_XY_LIMIT = 5000.0
TRUE_MATERIAL_STYLE_GRAPH_FOLDER = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/TrueMaterialApplied/DesignerStyleProfileMatrixCombos"
)
TRUE_MATERIAL_TREE_GRAPH_FOLDER = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/TrueMaterialApplied/TreeProfilePresets"
)

COMBO_BY_TYPE = {
    1: "PCG_Sparse",
    2: "PCG_Normal",
    3: "PCG_Dense",
}
MATRIX_GRAPH_ASSETS = {
    (1, 1): "PCG_Cubeless_ED_Matrix_GroundSparse_DitchSparse",
    (1, 2): "PCG_Cubeless_ED_Matrix_GroundSparse_DitchNormal",
    (1, 3): "PCG_Cubeless_ED_Matrix_GroundSparse_DitchDense",
    (2, 1): "PCG_Cubeless_ED_Matrix_GroundNormal_DitchSparse",
    (2, 2): "PCG_Cubeless_ED_Matrix_GroundNormal_DitchNormal",
    (2, 3): "PCG_Cubeless_ED_Matrix_GroundNormal_DitchDense",
    (3, 1): "PCG_Cubeless_ED_Matrix_GroundDense_DitchSparse",
    (3, 2): "PCG_Cubeless_ED_Matrix_GroundDense_DitchNormal",
    (3, 3): "PCG_Cubeless_ED_Matrix_GroundDense_DitchDense",
}
PROFILE_MATRIX_GRAPH_ASSETS = {
    (1, 1, 0): "PCG_Cubeless_ED_ProfileMatrix_GroundOnly_GroundSparse",
    (1, 2, 0): "PCG_Cubeless_ED_ProfileMatrix_GroundOnly_GroundNormal",
    (1, 3, 0): "PCG_Cubeless_ED_ProfileMatrix_GroundOnly_GroundDense",
    (2, 0, 1): "PCG_Cubeless_ED_ProfileMatrix_DitchOnly_DitchSparse",
    (2, 0, 2): "PCG_Cubeless_ED_ProfileMatrix_DitchOnly_DitchNormal",
    (2, 0, 3): "PCG_Cubeless_ED_ProfileMatrix_DitchOnly_DitchDense",
    (3, 1, 1): "PCG_Cubeless_ED_ProfileMatrix_Both_GroundSparse_DitchSparse",
    (3, 1, 2): "PCG_Cubeless_ED_ProfileMatrix_Both_GroundSparse_DitchNormal",
    (3, 1, 3): "PCG_Cubeless_ED_ProfileMatrix_Both_GroundSparse_DitchDense",
    (3, 2, 1): "PCG_Cubeless_ED_ProfileMatrix_Both_GroundNormal_DitchSparse",
    (3, 2, 2): "PCG_Cubeless_ED_ProfileMatrix_Both_GroundNormal_DitchNormal",
    (3, 2, 3): "PCG_Cubeless_ED_ProfileMatrix_Both_GroundNormal_DitchDense",
    (3, 3, 1): "PCG_Cubeless_ED_ProfileMatrix_Both_GroundDense_DitchSparse",
    (3, 3, 2): "PCG_Cubeless_ED_ProfileMatrix_Both_GroundDense_DitchNormal",
    (3, 3, 3): "PCG_Cubeless_ED_ProfileMatrix_Both_GroundDense_DitchDense",
}
STYLE_NAMES = {
    1: "ClassicGrass",
    2: "TallGrass",
    3: "MixedGrass",
    4: "GroundFoliage",
    5: "SmallRocks",
}
GROUND_AMOUNT_NAMES = {
    1: "GroundSparse",
    2: "GroundNormal",
    3: "GroundDense",
}
DITCH_AMOUNT_NAMES = {
    1: "DitchSparse",
    2: "DitchNormal",
    3: "DitchDense",
}
TREE_STYLE_NAMES = {
    1: "CompactConifer",
    2: "ColumnConifer",
    3: "MixedConifer",
}
TREE_AMOUNT_NAMES = {
    1: "Solo",
    2: "Sparse",
    3: "LightGrove",
}
MATERIAL_DOMAIN_NAMES = {
    1: "GroundFoliage",
    2: "SmallRocks",
    3: "CompactConifer",
}
MATERIAL_VARIANT_GRAPH_ASSETS = {
    (1, 1): "PCG_Cubeless_ED_MaterialOverride_GroundFoliage_Default",
    (1, 2): "PCG_Cubeless_ED_MaterialOverride_GroundFoliage_CoolLeaf",
    (1, 3): "PCG_Cubeless_ED_MaterialOverride_GroundFoliage_WarmLeaf",
    (2, 1): "PCG_Cubeless_ED_MaterialOverride_SmallRocks_Default",
    (2, 2): "PCG_Cubeless_ED_MaterialOverride_SmallRocks_CoolRock",
    (2, 3): "PCG_Cubeless_ED_MaterialOverride_SmallRocks_DarkRock",
    (3, 1): "PCG_Cubeless_ED_MaterialOverride_CompactConifer_Default",
    (3, 2): "PCG_Cubeless_ED_MaterialOverride_CompactConifer_DarkPine",
    (3, 3): "PCG_Cubeless_ED_MaterialOverride_CompactConifer_SoftPine",
}
TRUE_MATERIAL_VARIANT_NAMES = {
    (1, 2): "CoolLeaf",
    (1, 3): "WarmLeaf",
    (2, 2): "CoolRock",
    (2, 3): "DarkRock",
    (3, 2): "DarkPine",
    (3, 3): "SoftPine",
}
TRUE_MATERIAL_STYLE_DOMAIN_BY_STYLE_TYPE = {
    4: 1,
    5: 2,
}
TRUE_MATERIAL_TREE_DOMAIN_BY_STYLE_TYPE = {
    1: 3,
    2: 3,
    3: 3,
}
ECOSYSTEM_MODES = {
    1: "StyleOnly",
    2: "TreeOnly",
    3: "Combined",
}
TREE_OVERRIDE_TO_AMOUNT = {
    2: 1,
    3: 2,
    4: 3,
}
PRODUCTION_CANDIDATE_PRESETS = {
    1: {
        "label": "MixedMeadowDefault",
        "ecosystem_mode": 3,
        "visual_style_type": 3,
        "profile_mode": 3,
        "ground_amount_type": 2,
        "ditch_amount_type": 1,
        "tree_style_type": 1,
        "tree_amount_type": 1,
        "material_domain_type": 1,
        "material_variant_type": 2,
    },
    2: {
        "label": "DenseGroundFoliage",
        "ecosystem_mode": 3,
        "visual_style_type": 4,
        "profile_mode": 3,
        "ground_amount_type": 3,
        "ditch_amount_type": 2,
        "tree_style_type": 2,
        "tree_amount_type": 2,
        "material_domain_type": 1,
        "material_variant_type": 3,
    },
    3: {
        "label": "RockySparse",
        "ecosystem_mode": 1,
        "visual_style_type": 5,
        "profile_mode": 1,
        "ground_amount_type": 1,
        "ditch_amount_type": 2,
        "tree_style_type": 1,
        "tree_amount_type": 1,
        "material_domain_type": 2,
        "material_variant_type": 3,
    },
    4: {
        "label": "LightConiferEdge",
        "ecosystem_mode": 3,
        "visual_style_type": 1,
        "profile_mode": 3,
        "ground_amount_type": 2,
        "ditch_amount_type": 1,
        "tree_style_type": 3,
        "tree_amount_type": 3,
        "material_domain_type": 3,
        "material_variant_type": 3,
    },
    5: {
        "label": "ClassicGrassFill",
        "ecosystem_mode": 1,
        "visual_style_type": 1,
        "profile_mode": 1,
        "ground_amount_type": 3,
        "ditch_amount_type": 2,
        "tree_style_type": 1,
        "tree_amount_type": 1,
        "material_domain_type": 1,
        "material_variant_type": 1,
    },
}


def _get_actor_subsystem():
    subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    if subsystem_cls:
        return unreal.get_editor_subsystem(subsystem_cls)
    return None


def _get_all_level_actors():
    actor_subsystem = _get_actor_subsystem()
    if actor_subsystem:
        return actor_subsystem.get_all_level_actors()
    return unreal.EditorLevelLibrary.get_all_level_actors()


def _get_selected_level_actors():
    actor_subsystem = _get_actor_subsystem()
    if actor_subsystem:
        return actor_subsystem.get_selected_level_actors()
    return unreal.EditorLevelLibrary.get_selected_level_actors()


def _selector_class(class_path):
    return unreal.load_class(None, class_path)


def _is_actor_of_class(actor, class_path):
    selector_class = _selector_class(class_path)
    if not selector_class:
        return False
    try:
        return bool(actor.get_class().is_child_of(selector_class))
    except Exception:
        return actor.get_class() == selector_class


def _is_authoring_selector_actor(actor):
    return _is_actor_of_class(actor, AUTHORING_BLUEPRINT_CLASS_PATH)


def _is_matrix_selector_actor(actor):
    return _is_actor_of_class(actor, MATRIX_BLUEPRINT_CLASS_PATH)


def _is_profile_matrix_selector_actor(actor):
    return _is_actor_of_class(actor, PROFILE_MATRIX_BLUEPRINT_CLASS_PATH)


def _is_style_profile_matrix_selector_actor(actor):
    return _is_actor_of_class(actor, STYLE_PROFILE_MATRIX_BLUEPRINT_CLASS_PATH)


def _is_tree_profile_selector_actor(actor):
    return _is_actor_of_class(actor, TREE_PROFILE_BLUEPRINT_CLASS_PATH)


def _is_material_override_selector_actor(actor):
    return _is_actor_of_class(actor, MATERIAL_OVERRIDE_BLUEPRINT_CLASS_PATH)


def _is_ecosystem_selector_actor(actor):
    return _is_actor_of_class(actor, ECOSYSTEM_BLUEPRINT_CLASS_PATH)


def _is_production_candidate_actor(actor):
    return _is_actor_of_class(actor, PRODUCTION_CANDIDATE_BLUEPRINT_CLASS_PATH)


def _is_selector_actor(actor):
    return (
        _is_authoring_selector_actor(actor)
        or _is_matrix_selector_actor(actor)
        or _is_profile_matrix_selector_actor(actor)
        or _is_style_profile_matrix_selector_actor(actor)
        or _is_tree_profile_selector_actor(actor)
        or _is_material_override_selector_actor(actor)
        or _is_ecosystem_selector_actor(actor)
        or _is_production_candidate_actor(actor)
    )


def _get_designer_combo_type(actor):
    for prop_name in ("DesignerComboType", "designercombotype"):
        try:
            return int(actor.get_editor_property(prop_name))
        except Exception:
            pass
    raise RuntimeError("Actor has no DesignerComboType property: {}".format(actor.get_actor_label()))


def _get_int_property(actor, prop_names, default_value=2):
    for prop_name in prop_names:
        try:
            return int(actor.get_editor_property(prop_name))
        except Exception:
            pass
    return int(default_value)


def _get_bool_property(actor, prop_names, default_value=False):
    for prop_name in prop_names:
        try:
            return bool(actor.get_editor_property(prop_name))
        except Exception:
            pass
    return bool(default_value)


def _get_matrix_axes(actor):
    ground_type = _get_int_property(actor, ("GroundAmountType", "groundamounttype"), 2)
    ditch_type = _get_int_property(actor, ("DitchAmountType", "ditchamounttype"), 2)
    if (ground_type, ditch_type) not in MATRIX_GRAPH_ASSETS:
        ground_type, ditch_type = 2, 2
    return ground_type, ditch_type


def _normalize_amount_axis(value, default_value=2):
    value = int(value)
    if value in (1, 2, 3):
        return value
    return int(default_value)


def _get_profile_matrix_axes(actor):
    profile_mode = _get_int_property(actor, ("ProfileMode", "profilemode"), 3)
    if profile_mode not in (1, 2, 3):
        profile_mode = 3
    ground_type = _normalize_amount_axis(
        _get_int_property(actor, ("GroundAmountType", "groundamounttype"), 2)
    )
    ditch_type = _normalize_amount_axis(
        _get_int_property(actor, ("DitchAmountType", "ditchamounttype"), 2)
    )
    if profile_mode == 1:
        ditch_type = 0
    elif profile_mode == 2:
        ground_type = 0
    if (profile_mode, ground_type, ditch_type) not in PROFILE_MATRIX_GRAPH_ASSETS:
        profile_mode, ground_type, ditch_type = 3, 2, 2
    return profile_mode, ground_type, ditch_type


def _normalize_style_axis(value, default_value=1):
    value = int(value)
    if value in STYLE_NAMES:
        return value
    return int(default_value)


def _get_style_profile_matrix_axes(actor):
    style_type = _normalize_style_axis(
        _get_int_property(actor, ("VisualStyleType", "visualstyletype"), 1)
    )
    profile_mode = _get_int_property(actor, ("ProfileMode", "profilemode"), 3)
    if profile_mode not in (1, 2, 3):
        profile_mode = 3
    ground_type = _normalize_amount_axis(
        _get_int_property(actor, ("GroundAmountType", "groundamounttype"), 2)
    )
    ditch_type = _normalize_amount_axis(
        _get_int_property(actor, ("DitchAmountType", "ditchamounttype"), 2)
    )
    if profile_mode == 1:
        ditch_type = 0
    elif profile_mode == 2:
        ground_type = 0
    if not _style_profile_matrix_asset_name(style_type, profile_mode, ground_type, ditch_type):
        style_type, profile_mode, ground_type, ditch_type = 1, 3, 2, 2
    return style_type, profile_mode, ground_type, ditch_type


def _get_tree_profile_axes(actor):
    tree_style_type = _get_int_property(actor, ("TreeStyleType", "treestyletype"), 1)
    if tree_style_type not in TREE_STYLE_NAMES:
        tree_style_type = 1
    tree_amount_type = _get_int_property(actor, ("TreeAmountType", "treeamounttype"), 2)
    if tree_amount_type not in TREE_AMOUNT_NAMES:
        tree_amount_type = 2
    return tree_style_type, tree_amount_type


def _get_material_override_axes(actor):
    domain_type = _get_int_property(actor, ("MaterialDomainType", "materialdomaintype"), 1)
    if domain_type not in MATERIAL_DOMAIN_NAMES:
        domain_type = 1
    variant_type = _get_int_property(actor, ("MaterialVariantType", "materialvarianttype"), 1)
    if (domain_type, variant_type) not in MATERIAL_VARIANT_GRAPH_ASSETS:
        variant_type = 1
    return domain_type, variant_type


def _get_generate_material_preview(actor):
    return _get_bool_property(
        actor,
        ("GenerateMaterialPreview", "generatematerialpreview"),
        True,
    )


def _get_ecosystem_axes(actor):
    ecosystem_mode = _get_int_property(actor, ("EcosystemMode", "ecosystemmode"), 3)
    if ecosystem_mode not in ECOSYSTEM_MODES:
        ecosystem_mode = 3
    style_type, profile_mode, ground_type, ditch_type = _get_style_profile_matrix_axes(actor)
    tree_style_type, tree_amount_type = _get_tree_profile_axes(actor)
    material_domain_type, material_variant_type = _get_material_override_axes(actor)
    return (
        ecosystem_mode,
        style_type,
        profile_mode,
        ground_type,
        ditch_type,
        tree_style_type,
        tree_amount_type,
        material_domain_type,
        material_variant_type,
    )


def _normalize_profile_amounts(profile_mode, ground_type, ditch_type):
    if profile_mode == 1:
        return ground_type, 0
    if profile_mode == 2:
        return 0, ditch_type
    return ground_type, ditch_type


def _resolve_production_candidate_axes(
    preset_type,
    density_override=0,
    tree_override=0,
    material_mood=0,
    debug_material_preview=False,
):
    preset_type = int(preset_type)
    if preset_type not in PRODUCTION_CANDIDATE_PRESETS:
        preset_type = 1
    axes = dict(PRODUCTION_CANDIDATE_PRESETS[preset_type])

    density_override = int(density_override)
    if density_override in (1, 2, 3):
        axes["ground_amount_type"] = density_override
        axes["ditch_amount_type"] = density_override

    tree_override = int(tree_override)
    if tree_override == 1:
        axes["ecosystem_mode"] = 1
    elif tree_override in TREE_OVERRIDE_TO_AMOUNT:
        axes["tree_amount_type"] = TREE_OVERRIDE_TO_AMOUNT[tree_override]
        if axes["ecosystem_mode"] == 1:
            axes["ecosystem_mode"] = 3

    material_mood = int(material_mood)
    if material_mood in (1, 2, 3):
        axes["material_variant_type"] = material_mood

    axes["ground_amount_type"], axes["ditch_amount_type"] = _normalize_profile_amounts(
        int(axes["profile_mode"]),
        _normalize_amount_axis(axes["ground_amount_type"]),
        _normalize_amount_axis(axes["ditch_amount_type"]),
    )
    axes["preset_type"] = preset_type
    axes["density_override"] = density_override if density_override in (0, 1, 2, 3) else 0
    axes["tree_override"] = tree_override if tree_override in (0, 1, 2, 3, 4) else 0
    axes["material_mood"] = material_mood if material_mood in (0, 1, 2, 3) else 0
    axes["debug_material_preview"] = bool(debug_material_preview)
    return axes


def _get_production_candidate_axes(actor):
    return _resolve_production_candidate_axes(
        _get_int_property(actor, ("PresetType", "presettype"), 1),
        _get_int_property(actor, ("DensityOverride", "densityoverride"), 0),
        _get_int_property(actor, ("TreeOverride", "treeoverride"), 0),
        _get_int_property(actor, ("MaterialMood", "materialmood"), 0),
        _get_bool_property(actor, ("DebugMaterialPreview", "debugmaterialpreview"), False),
    )


def _matrix_graph_path(ground_type, ditch_type):
    asset_name = MATRIX_GRAPH_ASSETS[(ground_type, ditch_type)]
    return "{}/{}.{}".format(MATRIX_GRAPH_FOLDER, asset_name, asset_name)


def _profile_matrix_graph_path(profile_mode, ground_type, ditch_type):
    asset_name = PROFILE_MATRIX_GRAPH_ASSETS[(profile_mode, ground_type, ditch_type)]
    return "{}/{}.{}".format(PROFILE_MATRIX_GRAPH_FOLDER, asset_name, asset_name)


def _style_profile_matrix_asset_name(style_type, profile_mode, ground_type, ditch_type):
    style_name = STYLE_NAMES.get(style_type)
    if not style_name:
        return None
    if profile_mode == 1 and ground_type in GROUND_AMOUNT_NAMES and ditch_type == 0:
        return "PCG_Cubeless_ED_StyleProfileMatrix_{}_GroundOnly_{}".format(
            style_name,
            GROUND_AMOUNT_NAMES[ground_type],
        )
    if profile_mode == 2 and ground_type == 0 and ditch_type in DITCH_AMOUNT_NAMES:
        return "PCG_Cubeless_ED_StyleProfileMatrix_{}_DitchOnly_{}".format(
            style_name,
            DITCH_AMOUNT_NAMES[ditch_type],
        )
    if profile_mode == 3 and ground_type in GROUND_AMOUNT_NAMES and ditch_type in DITCH_AMOUNT_NAMES:
        return "PCG_Cubeless_ED_StyleProfileMatrix_{}_Both_{}_{}".format(
            style_name,
            GROUND_AMOUNT_NAMES[ground_type],
            DITCH_AMOUNT_NAMES[ditch_type],
        )
    return None


def _style_profile_matrix_graph_path(style_type, profile_mode, ground_type, ditch_type):
    asset_name = _style_profile_matrix_asset_name(style_type, profile_mode, ground_type, ditch_type)
    if not asset_name:
        raise RuntimeError(
            "Invalid style profile matrix axes: style={} profile={} ground={} ditch={}".format(
                style_type,
                profile_mode,
                ground_type,
                ditch_type,
            )
        )
    return "{}/{}.{}".format(STYLE_PROFILE_MATRIX_GRAPH_FOLDER, asset_name, asset_name)


def _tree_profile_asset_name(tree_style_type, tree_amount_type):
    style_name = TREE_STYLE_NAMES.get(tree_style_type)
    amount_name = TREE_AMOUNT_NAMES.get(tree_amount_type)
    if not style_name or not amount_name:
        return None
    return "PCG_Cubeless_ED_TreeProfile_{}_{}".format(style_name, amount_name)


def _tree_profile_graph_path(tree_style_type, tree_amount_type):
    asset_name = _tree_profile_asset_name(tree_style_type, tree_amount_type)
    if not asset_name:
        raise RuntimeError(
            "Invalid tree profile axes: style={} amount={}".format(
                tree_style_type,
                tree_amount_type,
            )
        )
    return "{}/{}.{}".format(TREE_PROFILE_GRAPH_FOLDER, asset_name, asset_name)


def _material_override_graph_path(domain_type, variant_type):
    asset_name = MATERIAL_VARIANT_GRAPH_ASSETS.get((domain_type, variant_type))
    if not asset_name:
        raise RuntimeError(
            "Invalid material override axes: domain={} variant={}".format(
                domain_type,
                variant_type,
            )
        )
    return "{}/{}.{}".format(MATERIAL_OVERRIDE_GRAPH_FOLDER, asset_name, asset_name)


def _dynamic_material_axis_graph_path(domain_type, variant_type):
    if (domain_type, variant_type) in TRUE_MATERIAL_VARIANT_NAMES:
        return DYNAMIC_MATERIAL_AXIS_GRAPH_PATH
    return None


def _load_material_override_graph(domain_type, variant_type):
    dynamic_graph_path = _dynamic_material_axis_graph_path(domain_type, variant_type)
    if dynamic_graph_path:
        dynamic_graph = unreal.EditorAssetLibrary.load_asset(dynamic_graph_path)
        if dynamic_graph:
            return dynamic_graph_path, dynamic_graph, "dynamic_actor_property"

    graph_path = _material_override_graph_path(domain_type, variant_type)
    graph = unreal.EditorAssetLibrary.load_asset(graph_path)
    if not graph:
        raise RuntimeError("Missing material override graph: {}".format(graph_path))
    return graph_path, graph, "preset_graph"


def _true_material_variant_name(domain_type, variant_type):
    return TRUE_MATERIAL_VARIANT_NAMES.get((domain_type, variant_type))


def _true_material_style_profile_matrix_asset_name(
    style_type,
    profile_mode,
    ground_type,
    ditch_type,
    material_domain_type,
    material_variant_type,
):
    expected_domain_type = TRUE_MATERIAL_STYLE_DOMAIN_BY_STYLE_TYPE.get(style_type)
    if expected_domain_type != material_domain_type:
        return None
    variant_name = _true_material_variant_name(material_domain_type, material_variant_type)
    if not variant_name:
        return None
    base_asset_name = _style_profile_matrix_asset_name(style_type, profile_mode, ground_type, ditch_type)
    if not base_asset_name:
        return None
    base_suffix = base_asset_name.replace("PCG_Cubeless_ED_", "", 1)
    return "PCG_Cubeless_ED_TrueMaterial_{}_{}".format(variant_name, base_suffix)


def _true_material_style_profile_matrix_graph_path(
    style_type,
    profile_mode,
    ground_type,
    ditch_type,
    material_domain_type,
    material_variant_type,
):
    asset_name = _true_material_style_profile_matrix_asset_name(
        style_type,
        profile_mode,
        ground_type,
        ditch_type,
        material_domain_type,
        material_variant_type,
    )
    if not asset_name:
        return _style_profile_matrix_graph_path(style_type, profile_mode, ground_type, ditch_type)
    return "{}/{}.{}".format(TRUE_MATERIAL_STYLE_GRAPH_FOLDER, asset_name, asset_name)


def _true_material_tree_profile_asset_name(tree_style_type, tree_amount_type, material_domain_type, material_variant_type):
    expected_domain_type = TRUE_MATERIAL_TREE_DOMAIN_BY_STYLE_TYPE.get(tree_style_type)
    if expected_domain_type != material_domain_type:
        return None
    variant_name = _true_material_variant_name(material_domain_type, material_variant_type)
    if not variant_name:
        return None
    base_asset_name = _tree_profile_asset_name(tree_style_type, tree_amount_type)
    if not base_asset_name:
        return None
    base_suffix = base_asset_name.replace("PCG_Cubeless_ED_", "", 1)
    return "PCG_Cubeless_ED_TrueMaterial_{}_{}".format(variant_name, base_suffix)


def _true_material_tree_profile_graph_path(tree_style_type, tree_amount_type, material_domain_type, material_variant_type):
    asset_name = _true_material_tree_profile_asset_name(
        tree_style_type,
        tree_amount_type,
        material_domain_type,
        material_variant_type,
    )
    if not asset_name:
        return _tree_profile_graph_path(tree_style_type, tree_amount_type)
    return "{}/{}.{}".format(TRUE_MATERIAL_TREE_GRAPH_FOLDER, asset_name, asset_name)


def _component_key(component):
    name = component.get_name()
    for key in COMBO_BY_TYPE.values():
        if name.startswith(key):
            return key
    return name


def _point_count_for_component(component):
    total_points = 0
    try:
        collection = component.get_generated_graph_output()
        for item in collection.get_editor_property("tagged_data"):
            data = item.get_editor_property("data").get_editor_property("data")
            if data and hasattr(data, "get_num_points"):
                total_points += int(data.get_num_points())
    except Exception:
        return 0
    return total_points


def _summarize_counts(actor):
    counts = {}
    for component in actor.get_components_by_class(unreal.PCGComponent):
        counts[_component_key(component)] = _point_count_for_component(component)
    return counts


def _schedule_component_regenerate(component, graph, force=True):
    state = {"elapsed": 0.0, "handle": None}

    def _on_tick(delta_seconds):
        state["elapsed"] += float(delta_seconds)
        if state["elapsed"] < 0.05:
            return
        try:
            unreal.unregister_slate_post_tick_callback(state["handle"])
        except Exception:
            pass
        try:
            component.set_graph(graph)
            component.cleanup(True)
            component.activate(True)
            component.generate(bool(force))
            component.generate(bool(force))
        except Exception:
            unreal.log_error("Cubeless ED PCG deferred regenerate failed\n{}".format(traceback.format_exc()))

    state["handle"] = unreal.register_slate_post_tick_callback(_on_tick)
    return True


def apply_authoring_selector(actor, force=True):
    combo_type = _get_designer_combo_type(actor)
    selected_key = COMBO_BY_TYPE.get(combo_type, COMBO_BY_TYPE[2])
    components = actor.get_components_by_class(unreal.PCGComponent)
    if len(components) < 3:
        raise RuntimeError("Selector actor expected 3 PCG components: {}".format(actor.get_actor_label()))

    for component in components:
        component.cleanup(True)
        component.deactivate()

    for component in components:
        if _component_key(component) == selected_key:
            component.activate(True)
            component.generate(bool(force))
            component.generate(bool(force))

    return {
        "selector_type": "combo",
        "actor": actor.get_actor_label(),
        "designer_combo_type": combo_type,
        "selected_component": selected_key,
        "component_point_counts": _summarize_counts(actor),
    }


def apply_matrix_selector(actor, force=True):
    ground_type, ditch_type = _get_matrix_axes(actor)
    graph_path = _matrix_graph_path(ground_type, ditch_type)
    graph = unreal.EditorAssetLibrary.load_asset(graph_path)
    if not graph:
        raise RuntimeError("Missing matrix graph: {}".format(graph_path))

    components = actor.get_components_by_class(unreal.PCGComponent)
    if not components:
        raise RuntimeError("Matrix selector actor has no PCG component: {}".format(actor.get_actor_label()))

    component = components[0]
    component.set_graph(graph)
    component.cleanup(True)
    component.activate(True)
    component.generate(bool(force))
    component.generate(bool(force))
    return {
        "selector_type": "matrix",
        "actor": actor.get_actor_label(),
        "ground_amount_type": ground_type,
        "ditch_amount_type": ditch_type,
        "graph": graph_path,
        "component_point_counts": _summarize_counts(actor),
    }


def apply_profile_matrix_selector(actor, force=True):
    profile_mode, ground_type, ditch_type = _get_profile_matrix_axes(actor)
    graph_path = _profile_matrix_graph_path(profile_mode, ground_type, ditch_type)
    graph = unreal.EditorAssetLibrary.load_asset(graph_path)
    if not graph:
        raise RuntimeError("Missing profile matrix graph: {}".format(graph_path))

    components = actor.get_components_by_class(unreal.PCGComponent)
    if not components:
        raise RuntimeError(
            "Profile matrix selector actor has no PCG component: {}".format(actor.get_actor_label())
        )

    component = components[0]
    component.cleanup(True)
    component.set_graph(graph)
    component.activate(True)
    component.generate(bool(force))
    component.generate(bool(force))
    return {
        "selector_type": "profile_matrix",
        "actor": actor.get_actor_label(),
        "profile_mode": profile_mode,
        "ground_amount_type": ground_type,
        "ditch_amount_type": ditch_type,
        "graph": graph_path,
        "component_point_counts": _summarize_counts(actor),
    }


def apply_style_profile_matrix_selector(actor, force=True):
    style_type, profile_mode, ground_type, ditch_type = _get_style_profile_matrix_axes(actor)
    graph_path = _style_profile_matrix_graph_path(style_type, profile_mode, ground_type, ditch_type)
    graph = unreal.EditorAssetLibrary.load_asset(graph_path)
    if not graph:
        raise RuntimeError("Missing style profile matrix graph: {}".format(graph_path))

    components = actor.get_components_by_class(unreal.PCGComponent)
    if not components:
        raise RuntimeError(
            "Style profile matrix selector actor has no PCG component: {}".format(actor.get_actor_label())
        )

    component = components[0]
    component.cleanup(True)
    component.set_graph(graph)
    component.activate(True)
    component.generate(bool(force))
    component.generate(bool(force))
    return {
        "selector_type": "style_profile_matrix",
        "actor": actor.get_actor_label(),
        "visual_style_type": style_type,
        "profile_mode": profile_mode,
        "ground_amount_type": ground_type,
        "ditch_amount_type": ditch_type,
        "graph": graph_path,
        "component_point_counts": _summarize_counts(actor),
    }


def apply_tree_profile_selector(actor, force=True):
    tree_style_type, tree_amount_type = _get_tree_profile_axes(actor)
    graph_path = _tree_profile_graph_path(tree_style_type, tree_amount_type)
    graph = unreal.EditorAssetLibrary.load_asset(graph_path)
    if not graph:
        raise RuntimeError("Missing tree profile graph: {}".format(graph_path))

    components = actor.get_components_by_class(unreal.PCGComponent)
    if not components:
        raise RuntimeError(
            "Tree profile selector actor has no PCG component: {}".format(actor.get_actor_label())
        )

    component = components[0]
    component.cleanup(True)
    component.set_graph(graph)
    component.activate(True)
    component.generate(bool(force))
    component.generate(bool(force))
    return {
        "selector_type": "tree_profile",
        "actor": actor.get_actor_label(),
        "tree_style_type": tree_style_type,
        "tree_amount_type": tree_amount_type,
        "graph": graph_path,
        "component_point_counts": _summarize_counts(actor),
    }


def apply_material_override_selector(actor, force=True):
    domain_type, variant_type = _get_material_override_axes(actor)
    graph_path, graph, graph_mode = _load_material_override_graph(domain_type, variant_type)

    components = actor.get_components_by_class(unreal.PCGComponent)
    if not components:
        raise RuntimeError(
            "Material override selector actor has no PCG component: {}".format(actor.get_actor_label())
        )

    component = components[0]
    component.set_graph(graph)
    component.cleanup(True)
    component.activate(True)
    component.generate(bool(force))
    component.generate(bool(force))
    counts = _summarize_counts(actor)
    deferred_regeneration = False
    if graph_mode == "dynamic_actor_property" and counts.get(_component_key(component), 0) == 0:
        deferred_regeneration = _schedule_component_regenerate(component, graph, force)
    return {
        "selector_type": "material_override",
        "actor": actor.get_actor_label(),
        "material_domain_type": domain_type,
        "material_variant_type": variant_type,
        "graph": graph_path,
        "graph_mode": graph_mode,
        "component_point_counts": counts,
        "deferred_regeneration": deferred_regeneration,
    }


def _find_named_pcg_component(actor, expected_name):
    for component in actor.get_components_by_class(unreal.PCGComponent):
        if component.get_name().startswith(expected_name):
            return component
    return None


def _prepare_component(component, graph, force):
    component.set_graph(graph)
    component.cleanup(True)
    component.activate(True)
    component.generate(bool(force))
    component.generate(bool(force))


def _get_editor_world():
    subsystem_cls = getattr(unreal, "UnrealEditorSubsystem", None)
    if subsystem_cls:
        try:
            subsystem = unreal.get_editor_subsystem(subsystem_cls)
            world = subsystem.get_editor_world() if subsystem else None
            if world:
                return world
        except Exception:
            pass
    try:
        return unreal.EditorLevelLibrary.get_editor_world()
    except Exception:
        return None


def _is_landscape_actor(actor):
    if not actor:
        return False
    try:
        class_name = actor.get_class().get_name()
    except Exception:
        return False
    return class_name == "Landscape" or "LandscapeStreamingProxy" in class_name


def _trace_landscape_at_xy(x, y):
    world = _get_editor_world()
    if not world:
        return None
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world,
            unreal.Vector(float(x), float(y), LANDSCAPE_TRACE_Z),
            unreal.Vector(float(x), float(y), -LANDSCAPE_TRACE_Z),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False,
            [],
            unreal.DrawDebugTrace.NONE,
            True,
        )
        data = hit.to_tuple()
        if not data or not data[0] or len(data) <= 9 or not _is_landscape_actor(data[9]):
            return None
        return data[4]
    except Exception:
        return None


def _get_instance_transform(component, index):
    transform = component.get_instance_transform(index, True)
    if isinstance(transform, tuple):
        return transform[0] if transform else None
    return transform


def _get_world_instance_location(actor, location):
    actor_location = actor.get_actor_location()
    world_xy_delta = max(abs(location.x - actor_location.x), abs(location.y - actor_location.y))
    local_xy_delta = max(abs(location.x), abs(location.y))
    if world_xy_delta <= LANDSCAPE_CONFORM_LOCAL_XY_LIMIT:
        return location
    if local_xy_delta > LANDSCAPE_CONFORM_LOCAL_XY_LIMIT:
        return location
    return unreal.Vector(
        actor_location.x + location.x,
        actor_location.y + location.y,
        actor_location.z + location.z,
    )


def _conform_generated_ism_to_landscape(actor, vertical_offset_cache=None):
    actor_location = actor.get_actor_location()
    adjusted = 0
    missed = 0
    components = actor.get_components_by_class(unreal.InstancedStaticMeshComponent)
    for component in components:
        try:
            count = int(component.get_instance_count())
        except Exception:
            continue
        for index in range(count):
            transform = _get_instance_transform(component, index)
            if not transform:
                missed += 1
                continue
            world_location = _get_world_instance_location(actor, transform.translation)
            landscape_location = _trace_landscape_at_xy(world_location.x, world_location.y)
            if not landscape_location:
                missed += 1
                continue
            cache_key = (component.get_name(), index)
            if vertical_offset_cache is not None and cache_key in vertical_offset_cache:
                vertical_offset = vertical_offset_cache[cache_key]
            else:
                vertical_offset = world_location.z - actor_location.z
                if vertical_offset_cache is not None:
                    vertical_offset_cache[cache_key] = vertical_offset
            world_location.z = landscape_location.z + vertical_offset
            transform.translation = world_location
            try:
                component.update_instance_transform(index, transform, True, True, True)
                adjusted += 1
            except Exception:
                missed += 1
    return {
        "landscape_conform_adjusted_instances": adjusted,
        "landscape_conform_missed_instances": missed,
    }


def _schedule_landscape_conform(actor, vertical_offset_cache=None):
    if vertical_offset_cache is None:
        vertical_offset_cache = {}
    state = {
        "elapsed": 0.0,
        "handle": None,
        "last_attempt": 0.0,
        "successful_passes": 0,
    }

    def _on_tick(delta_seconds):
        state["elapsed"] += float(delta_seconds)
        if state["elapsed"] < 0.15:
            return
        if (state["elapsed"] - state["last_attempt"]) < 0.25:
            return
        state["last_attempt"] = state["elapsed"]
        try:
            result = _conform_generated_ism_to_landscape(actor, vertical_offset_cache)
            touched = int(result.get("landscape_conform_adjusted_instances", 0)) + int(
                result.get("landscape_conform_missed_instances", 0)
            )
            if touched > 0:
                state["successful_passes"] += 1
            if state["successful_passes"] >= 3 or state["elapsed"] >= 5.0:
                try:
                    unreal.unregister_slate_post_tick_callback(state["handle"])
                except Exception:
                    pass
        except Exception:
            try:
                unreal.unregister_slate_post_tick_callback(state["handle"])
            except Exception:
                pass
            unreal.log_error("Cubeless production candidate landscape conform failed\n{}".format(traceback.format_exc()))

    state["handle"] = unreal.register_slate_post_tick_callback(_on_tick)
    return True


def _set_actor_property_if_available(actor, prop_name, value):
    try:
        actor.set_editor_property(prop_name, value)
        return True
    except Exception:
        return False


def apply_ecosystem_selector(actor, force=True):
    (
        ecosystem_mode,
        style_type,
        profile_mode,
        ground_type,
        ditch_type,
        tree_style_type,
        tree_amount_type,
        material_domain_type,
        material_variant_type,
    ) = _get_ecosystem_axes(actor)
    generate_material_preview = _get_generate_material_preview(actor)
    style_graph_path = _true_material_style_profile_matrix_graph_path(
        style_type,
        profile_mode,
        ground_type,
        ditch_type,
        material_domain_type,
        material_variant_type,
    )
    tree_graph_path = _true_material_tree_profile_graph_path(
        tree_style_type,
        tree_amount_type,
        material_domain_type,
        material_variant_type,
    )
    style_graph = unreal.EditorAssetLibrary.load_asset(style_graph_path)
    tree_graph = unreal.EditorAssetLibrary.load_asset(tree_graph_path)
    material_graph_path, material_graph, material_graph_mode = _load_material_override_graph(
        material_domain_type,
        material_variant_type,
    )
    if not style_graph:
        raise RuntimeError("Missing ecosystem style graph: {}".format(style_graph_path))
    if not tree_graph:
        raise RuntimeError("Missing ecosystem tree graph: {}".format(tree_graph_path))

    style_component = _find_named_pcg_component(actor, "PCG_StyleProfileMatrix")
    tree_component = _find_named_pcg_component(actor, "PCG_TreeProfile")
    material_component = _find_named_pcg_component(actor, "PCG_MaterialOverride")
    if not style_component or not tree_component or not material_component:
        raise RuntimeError(
            "Ecosystem selector actor expected PCG_StyleProfileMatrix, PCG_TreeProfile, and PCG_MaterialOverride: {}".format(
                actor.get_actor_label()
            )
        )

    for component in (style_component, tree_component, material_component):
        component.cleanup(True)
        component.deactivate()

    if ecosystem_mode in (1, 3):
        _prepare_component(style_component, style_graph, force)
    else:
        style_component.set_graph(style_graph)

    if ecosystem_mode in (2, 3):
        _prepare_component(tree_component, tree_graph, force)
    else:
        tree_component.set_graph(tree_graph)

    if generate_material_preview:
        _prepare_component(material_component, material_graph, force)
    else:
        material_component.set_graph(material_graph)

    counts = _summarize_counts(actor)
    deferred_material_regeneration = False
    if (
        generate_material_preview
        and material_graph_mode == "dynamic_actor_property"
        and counts.get(_component_key(material_component), 0) == 0
    ):
        deferred_material_regeneration = _schedule_component_regenerate(material_component, material_graph, force)
        counts = _summarize_counts(actor)

    return {
        "selector_type": "ecosystem",
        "actor": actor.get_actor_label(),
        "ecosystem_mode": ecosystem_mode,
        "visual_style_type": style_type,
        "profile_mode": profile_mode,
        "ground_amount_type": ground_type,
        "ditch_amount_type": ditch_type,
        "tree_style_type": tree_style_type,
        "tree_amount_type": tree_amount_type,
        "material_domain_type": material_domain_type,
        "material_variant_type": material_variant_type,
        "generate_material_preview": generate_material_preview,
        "style_graph": style_graph_path,
        "tree_graph": tree_graph_path,
        "material_graph": material_graph_path,
        "material_graph_mode": material_graph_mode,
        "component_point_counts": counts,
        "deferred_material_regeneration": deferred_material_regeneration,
    }


def apply_production_candidate_selector(actor, force=True):
    axes = _get_production_candidate_axes(actor)
    ecosystem_mode = int(axes["ecosystem_mode"])
    style_type = int(axes["visual_style_type"])
    profile_mode = int(axes["profile_mode"])
    ground_type = int(axes["ground_amount_type"])
    ditch_type = int(axes["ditch_amount_type"])
    tree_style_type = int(axes["tree_style_type"])
    tree_amount_type = int(axes["tree_amount_type"])
    material_domain_type = int(axes["material_domain_type"])
    material_variant_type = int(axes["material_variant_type"])
    debug_material_preview = bool(axes["debug_material_preview"])

    # The dynamic material preview graph reads these actor properties.
    _set_actor_property_if_available(actor, "MaterialDomainType", material_domain_type)
    _set_actor_property_if_available(actor, "MaterialVariantType", material_variant_type)

    style_graph_path = _true_material_style_profile_matrix_graph_path(
        style_type,
        profile_mode,
        ground_type,
        ditch_type,
        material_domain_type,
        material_variant_type,
    )
    tree_graph_path = _true_material_tree_profile_graph_path(
        tree_style_type,
        tree_amount_type,
        material_domain_type,
        material_variant_type,
    )
    style_graph = unreal.EditorAssetLibrary.load_asset(style_graph_path)
    tree_graph = unreal.EditorAssetLibrary.load_asset(tree_graph_path)
    material_graph_path, material_graph, material_graph_mode = _load_material_override_graph(
        material_domain_type,
        material_variant_type,
    )
    if not style_graph:
        raise RuntimeError("Missing production candidate style graph: {}".format(style_graph_path))
    if not tree_graph:
        raise RuntimeError("Missing production candidate tree graph: {}".format(tree_graph_path))

    style_component = _find_named_pcg_component(actor, "PCG_Style")
    tree_component = _find_named_pcg_component(actor, "PCG_Tree")
    material_component = _find_named_pcg_component(actor, "PCG_MaterialPreview")
    if not style_component or not tree_component or not material_component:
        raise RuntimeError(
            "Production candidate actor expected PCG_Style, PCG_Tree, and PCG_MaterialPreview: {}".format(
                actor.get_actor_label()
            )
        )

    for component in (style_component, tree_component, material_component):
        component.cleanup(True)
        component.deactivate()

    if ecosystem_mode in (1, 3):
        _prepare_component(style_component, style_graph, force)
    else:
        style_component.set_graph(style_graph)

    if ecosystem_mode in (2, 3):
        _prepare_component(tree_component, tree_graph, force)
    else:
        tree_component.set_graph(tree_graph)

    if debug_material_preview:
        _prepare_component(material_component, material_graph, force)
    else:
        material_component.set_graph(material_graph)

    counts = _summarize_counts(actor)
    deferred_material_regeneration = False
    if (
        debug_material_preview
        and material_graph_mode == "dynamic_actor_property"
        and counts.get(_component_key(material_component), 0) == 0
    ):
        deferred_material_regeneration = _schedule_component_regenerate(material_component, material_graph, force)
        counts = _summarize_counts(actor)
    landscape_conform_cache = {}
    landscape_conform = _conform_generated_ism_to_landscape(actor, landscape_conform_cache)
    landscape_conform["landscape_conform_scheduled"] = _schedule_landscape_conform(actor, landscape_conform_cache)

    return {
        "selector_type": "production_candidate",
        "actor": actor.get_actor_label(),
        "preset_type": axes["preset_type"],
        "preset_label": axes["label"],
        "density_override": axes["density_override"],
        "tree_override": axes["tree_override"],
        "material_mood": axes["material_mood"],
        "ecosystem_mode": ecosystem_mode,
        "visual_style_type": style_type,
        "profile_mode": profile_mode,
        "ground_amount_type": ground_type,
        "ditch_amount_type": ditch_type,
        "tree_style_type": tree_style_type,
        "tree_amount_type": tree_amount_type,
        "material_domain_type": material_domain_type,
        "material_variant_type": material_variant_type,
        "debug_material_preview": debug_material_preview,
        "style_graph": style_graph_path,
        "tree_graph": tree_graph_path,
        "material_graph": material_graph_path,
        "material_graph_mode": material_graph_mode,
        "component_point_counts": counts,
        "deferred_material_regeneration": deferred_material_regeneration,
        "landscape_conform": landscape_conform,
    }


def apply_selector(actor, force=True):
    if _is_production_candidate_actor(actor):
        return apply_production_candidate_selector(actor, force=force)
    if _is_ecosystem_selector_actor(actor):
        return apply_ecosystem_selector(actor, force=force)
    if _is_material_override_selector_actor(actor):
        return apply_material_override_selector(actor, force=force)
    if _is_tree_profile_selector_actor(actor):
        return apply_tree_profile_selector(actor, force=force)
    if _is_style_profile_matrix_selector_actor(actor):
        return apply_style_profile_matrix_selector(actor, force=force)
    if _is_profile_matrix_selector_actor(actor):
        return apply_profile_matrix_selector(actor, force=force)
    if _is_matrix_selector_actor(actor):
        return apply_matrix_selector(actor, force=force)
    return apply_authoring_selector(actor, force=force)


def _show_message(title, message):
    try:
        unreal.EditorDialog.show_message(title, message, unreal.AppMsgType.OK)
    except Exception:
        unreal.log("{}: {}".format(title, message))


def _show_delayed_result(actors, selected_only):
    if not hasattr(unreal, "register_slate_post_tick_callback"):
        return

    state = {
        "elapsed": 0.0,
        "handle": None,
    }

    def _on_tick(delta_seconds):
        state["elapsed"] += float(delta_seconds)
        if state["elapsed"] < 0.25:
            return
        try:
            unreal.unregister_slate_post_tick_callback(state["handle"])
        except Exception:
            pass

        lines = []
        for actor in actors:
            try:
                if _is_production_candidate_actor(actor):
                    axes = _get_production_candidate_axes(actor)
                    lines.append(
                        "{} -> Candidate {} {} / Density Override {} / Tree Override {} / Material Mood {} / Debug Preview {} {}".format(
                            actor.get_actor_label(),
                            axes["preset_type"],
                            axes["label"],
                            axes["density_override"],
                            axes["tree_override"],
                            axes["material_mood"],
                            axes["debug_material_preview"],
                            _summarize_counts(actor),
                        )
                    )
                elif _is_ecosystem_selector_actor(actor):
                    (
                        ecosystem_mode,
                        style_type,
                        profile_mode,
                        ground_type,
                        ditch_type,
                        tree_style_type,
                        tree_amount_type,
                        material_domain_type,
                        material_variant_type,
                    ) = _get_ecosystem_axes(actor)
                    generate_material_preview = _get_generate_material_preview(actor)
                    lines.append(
                        "{} -> Ecosystem {} / Style {} / Profile {} / Ground {} / Ditch {} / Tree Style {} / Tree Amount {} / Material Domain {} / Material Variant {} / Material Preview {} {}".format(
                            actor.get_actor_label(),
                            ecosystem_mode,
                            style_type,
                            profile_mode,
                            ground_type,
                            ditch_type,
                            tree_style_type,
                            tree_amount_type,
                            material_domain_type,
                            material_variant_type,
                            generate_material_preview,
                            _summarize_counts(actor),
                        )
                    )
                elif _is_tree_profile_selector_actor(actor):
                    tree_style_type, tree_amount_type = _get_tree_profile_axes(actor)
                    lines.append(
                        "{} -> Tree Style {} / Tree Amount {} {}".format(
                            actor.get_actor_label(),
                            tree_style_type,
                            tree_amount_type,
                            _summarize_counts(actor),
                        )
                    )
                elif _is_material_override_selector_actor(actor):
                    domain_type, variant_type = _get_material_override_axes(actor)
                    lines.append(
                        "{} -> Material Domain {} / Variant {} {}".format(
                            actor.get_actor_label(),
                            domain_type,
                            variant_type,
                            _summarize_counts(actor),
                        )
                    )
                elif _is_style_profile_matrix_selector_actor(actor):
                    style_type, profile_mode, ground_type, ditch_type = _get_style_profile_matrix_axes(actor)
                    lines.append(
                        "{} -> Style {} / Profile {} / Ground {} / Ditch {} {}".format(
                            actor.get_actor_label(),
                            style_type,
                            profile_mode,
                            ground_type,
                            ditch_type,
                            _summarize_counts(actor),
                        )
                    )
                elif _is_profile_matrix_selector_actor(actor):
                    profile_mode, ground_type, ditch_type = _get_profile_matrix_axes(actor)
                    lines.append(
                        "{} -> Profile {} / Ground {} / Ditch {} {}".format(
                            actor.get_actor_label(),
                            profile_mode,
                            ground_type,
                            ditch_type,
                            _summarize_counts(actor),
                        )
                    )
                elif _is_matrix_selector_actor(actor):
                    ground_type, ditch_type = _get_matrix_axes(actor)
                    lines.append(
                        "{} -> Ground {} / Ditch {} {}".format(
                            actor.get_actor_label(),
                            ground_type,
                            ditch_type,
                            _summarize_counts(actor),
                        )
                    )
                else:
                    combo_type = _get_designer_combo_type(actor)
                    selected_key = COMBO_BY_TYPE.get(combo_type, COMBO_BY_TYPE[2])
                    lines.append(
                        "{} -> {} {}".format(
                            actor.get_actor_label(),
                            selected_key,
                            _summarize_counts(actor),
                        )
                    )
            except Exception:
                lines.append("{} -> failed to read generated output".format(actor.get_actor_label()))

        scope = "selected selectors" if selected_only else "all selectors"
        _show_message("Cubeless ED PCG Selector", "Applied {}:\n{}".format(scope, "\n".join(lines)))

    state["handle"] = unreal.register_slate_post_tick_callback(_on_tick)


def apply_authoring_selectors_from_menu(show_dialog=True):
    try:
        selected = [actor for actor in _get_selected_level_actors() if _is_selector_actor(actor)]
        actors = selected or [actor for actor in _get_all_level_actors() if _is_selector_actor(actor)]
        if not actors:
            message = "No Cubeless ED PCG selector actors found in the current level."
            if show_dialog:
                _show_message("Cubeless ED PCG Selector", message)
            else:
                unreal.log_warning("Cubeless ED PCG Selector: {}".format(message))
            return

        results = [apply_selector(actor, force=True) for actor in actors]
        for result in results:
            unreal.log("Cubeless ED PCG Selector applied: {}".format(result))

        if show_dialog:
            _show_delayed_result(actors, bool(selected))
    except Exception:
        unreal.log_error("Cubeless ED PCG Selector failed\n{}".format(traceback.format_exc()))
        if show_dialog:
            _show_message("Cubeless ED PCG Selector", "Apply failed. Check the Output Log.")
