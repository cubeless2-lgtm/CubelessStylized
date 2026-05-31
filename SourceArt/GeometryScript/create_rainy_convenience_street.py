from __future__ import annotations

import math
import random

import unreal


ROOT = "/Game/Cubeless/Generated/RainyConvenienceStreet"
MATERIAL_DIR = f"{ROOT}/Materials"
MESH_PATH = f"{ROOT}/SM_RainyConvenienceStreet_GS"
LEVEL_PATH = f"{ROOT}/LVL_RainyConvenienceStreet_GS"
ACTOR_PREFIX = "GS_RainyStreet_"


MATERIALS = [
    ("M_Asphalt_Wet_Night", (0.015, 0.030, 0.040, 1.0), 0.18, 0.0, 0.65, False, 1.0),
    ("M_Concrete_Cool_Wet", (0.160, 0.210, 0.220, 1.0), 0.38, 0.0, 0.45, False, 1.0),
    ("M_Wall_Main_Teal", (0.045, 0.230, 0.215, 1.0), 0.72, 0.0, 0.32, False, 1.0),
    ("M_Wall_Dark_Blue", (0.035, 0.095, 0.130, 1.0), 0.82, 0.0, 0.28, False, 1.0),
    ("M_Roof_Black_Green", (0.025, 0.045, 0.050, 1.0), 0.62, 0.0, 0.32, False, 1.0),
    ("M_Sign_Lit_White", (1.150, 1.030, 0.720, 1.0), 0.30, 0.0, 0.20, True, 1.0),
    ("M_Sign_Stripe_Green", (0.000, 0.520, 0.380, 1.0), 0.35, 0.0, 0.25, True, 1.0),
    ("M_Sign_Stripe_Orange", (0.720, 0.270, 0.060, 1.0), 0.38, 0.0, 0.25, True, 1.0),
    ("M_Sign_Stripe_Red", (0.650, 0.070, 0.090, 1.0), 0.38, 0.0, 0.25, True, 1.0),
    ("M_Window_Warm", (1.800, 1.150, 0.460, 1.0), 0.20, 0.0, 0.15, True, 1.0),
    ("M_Glass_Dark_Teal", (0.030, 0.150, 0.170, 1.0), 0.10, 0.0, 0.80, False, 0.60),
    ("M_Metal_Ink", (0.015, 0.018, 0.020, 1.0), 0.45, 0.0, 0.50, False, 1.0),
    ("M_Vending_Blue", (0.030, 0.270, 0.560, 1.0), 0.42, 0.0, 0.45, False, 1.0),
    ("M_Plant_Green", (0.030, 0.240, 0.100, 1.0), 0.82, 0.0, 0.20, False, 1.0),
    ("M_Plant_Dark", (0.015, 0.110, 0.065, 1.0), 0.90, 0.0, 0.20, False, 1.0),
    ("M_Pot_Terracotta", (0.410, 0.170, 0.090, 1.0), 0.70, 0.0, 0.25, False, 1.0),
    ("M_Traffic_Red_Glow", (2.300, 0.120, 0.080, 1.0), 0.25, 0.0, 0.15, True, 1.0),
    ("M_Traffic_Amber_Glow", (1.700, 0.620, 0.160, 1.0), 0.25, 0.0, 0.15, True, 1.0),
    ("M_Rail_Painted_Metal", (0.030, 0.260, 0.260, 1.0), 0.50, 0.0, 0.45, False, 1.0),
    ("M_Puddle_Reflection", (0.060, 0.380, 0.390, 1.0), 0.06, 0.0, 0.95, False, 0.78),
    ("M_Background_BlueWall", (0.045, 0.140, 0.190, 1.0), 0.78, 0.0, 0.26, False, 1.0),
    ("M_Sign_Paper", (0.850, 0.760, 0.520, 1.0), 0.55, 0.0, 0.25, True, 1.0),
    ("M_Sign_Ink", (0.005, 0.008, 0.010, 1.0), 0.72, 0.0, 0.20, False, 1.0),
    ("M_AC_OffWhite", (0.640, 0.720, 0.700, 1.0), 0.56, 0.0, 0.35, False, 1.0),
    ("M_Lamp_Warm_Glow", (2.400, 1.450, 0.580, 1.0), 0.20, 0.0, 0.10, True, 1.0),
]


MAT = {name: index for index, (name, *_rest) in enumerate(MATERIALS)}
STALE_ASSETS = [
    f"{MATERIAL_DIR}/M_Rain_Streak",
    "/Game/Cubeless/Generated/_Scratch/SM_GS_TestCube",
]


def ensure_dir(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _constant(material: unreal.Material, value: float, x: int, y: int):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, x, y
    )
    node.set_editor_property("r", float(value))
    return node


def _constant3(material: unreal.Material, color: tuple[float, float, float, float], x: int, y: int):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, x, y
    )
    node.set_editor_property("constant", unreal.LinearColor(*color))
    return node


def create_material(name: str, color, roughness: float, metallic: float, specular: float, emissive: bool, opacity: float):
    ensure_dir(MATERIAL_DIR)
    path = f"{MATERIAL_DIR}/{name}"
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        material = unreal.EditorAssetLibrary.load_asset(path)
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    else:
        material = tools.create_asset(name, MATERIAL_DIR, unreal.Material, unreal.MaterialFactoryNew())

    if not material:
        raise RuntimeError(f"Failed to create material: {path}")

    material.set_editor_property("two_sided", True)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT if opacity < 1.0 else unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property(
        "shading_model",
        unreal.MaterialShadingModel.MSM_UNLIT if emissive else unreal.MaterialShadingModel.MSM_DEFAULT_LIT,
    )

    color_node = _constant3(material, color, -420, -60)
    if emissive:
        unreal.MaterialEditingLibrary.connect_material_property(
            color_node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )
        if opacity >= 1.0:
            base_node = _constant3(material, tuple(min(1.0, c) for c in color), -420, 100)
            unreal.MaterialEditingLibrary.connect_material_property(
                base_node, "", unreal.MaterialProperty.MP_BASE_COLOR
            )
    else:
        unreal.MaterialEditingLibrary.connect_material_property(
            color_node, "", unreal.MaterialProperty.MP_BASE_COLOR
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            _constant(material, roughness, -420, 120), "", unreal.MaterialProperty.MP_ROUGHNESS
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            _constant(material, metallic, -420, 260), "", unreal.MaterialProperty.MP_METALLIC
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            _constant(material, specular, -420, 400), "", unreal.MaterialProperty.MP_SPECULAR
        )

    if opacity < 1.0:
        unreal.MaterialEditingLibrary.connect_material_property(
            _constant(material, opacity, -420, 540), "", unreal.MaterialProperty.MP_OPACITY
        )

    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def make_materials():
    return [create_material(*entry) for entry in MATERIALS]


def delete_stale_assets():
    for path in STALE_ASSETS:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            unreal.EditorAssetLibrary.delete_asset(path)


def transform(location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1)):
    return unreal.Transform(
        unreal.Vector(float(location[0]), float(location[1]), float(location[2])),
        unreal.Rotator(float(rotation[0]), float(rotation[1]), float(rotation[2])),
        unreal.Vector(float(scale[0]), float(scale[1]), float(scale[2])),
    )


def opts(material_name: str):
    primitive_options = unreal.GeometryScriptPrimitiveOptions()
    primitive_options.material_id = MAT[material_name]
    return primitive_options


def box(mesh, material_name, loc, dims, rot=(0, 0, 0)):
    unreal.GeometryScript_Primitives.append_box(
        mesh,
        opts(material_name),
        transform(loc, rot),
        float(dims[0]),
        float(dims[1]),
        float(dims[2]),
        0,
        0,
        0,
        unreal.GeometryScriptPrimitiveOriginMode.CENTER,
    )


def cylinder(mesh, material_name, loc, radius, height, rot=(0, 0, 0), radial_steps=12):
    unreal.GeometryScript_Primitives.append_cylinder(
        mesh,
        opts(material_name),
        transform(loc, rot),
        float(radius),
        float(height),
        int(radial_steps),
        0,
        True,
        unreal.GeometryScriptPrimitiveOriginMode.CENTER,
    )


def sphere(mesh, material_name, loc, radius, steps_phi=6, steps_theta=10):
    unreal.GeometryScript_Primitives.append_sphere_lat_long(
        mesh,
        opts(material_name),
        transform(loc),
        float(radius),
        int(steps_phi),
        int(steps_theta),
        unreal.GeometryScriptPrimitiveOriginMode.CENTER,
    )


def torus(mesh, material_name, loc, major_radius, minor_radius, rot=(0, 0, 0)):
    revolve = unreal.GeometryScriptRevolveOptions()
    unreal.GeometryScript_Primitives.append_torus(
        mesh,
        opts(material_name),
        transform(loc, rot),
        revolve,
        float(major_radius),
        float(minor_radius),
        24,
        6,
        unreal.GeometryScriptPrimitiveOriginMode.CENTER,
    )


def segment_box(mesh, material_name, start, end, thickness):
    sx, sy, sz = start
    ex, ey, ez = end
    dx, dy, dz = ex - sx, ey - sy, ez - sz
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length <= 0.01:
        return
    yaw = math.degrees(math.atan2(dy, dx))
    horiz = math.sqrt(dx * dx + dy * dy)
    pitch = math.degrees(math.atan2(dz, horiz))
    loc = ((sx + ex) * 0.5, (sy + ey) * 0.5, (sz + ez) * 0.5)
    box(mesh, material_name, loc, (length, thickness, thickness), (pitch, yaw, 0))


def add_window(mesh, loc, dims, frame=True):
    box(mesh, "M_Window_Warm", loc, dims)
    if frame:
        x, y, z = loc
        dx, dy, dz = dims
        box(mesh, "M_Metal_Ink", (x - 3, y, z + dz * 0.5 + 2), (8, dy + 12, 8))
        box(mesh, "M_Metal_Ink", (x - 3, y, z - dz * 0.5 - 2), (8, dy + 12, 8))
        box(mesh, "M_Metal_Ink", (x - 3, y - dy * 0.5 - 2, z), (8, 8, dz + 12))
        box(mesh, "M_Metal_Ink", (x - 3, y + dy * 0.5 + 2, z), (8, 8, dz + 12))


def add_front_facade(mesh):
    # Convenience store mass and overhanging lit sign.
    box(mesh, "M_Wall_Main_Teal", (120, -310, 160), (420, 760, 320))
    box(mesh, "M_Roof_Black_Green", (-105, -310, 332), (42, 820, 24))
    box(mesh, "M_Sign_Lit_White", (-116, -310, 278), (34, 800, 82))

    stripe_z = [294, 278, 262]
    stripe_mats = ["M_Sign_Stripe_Orange", "M_Sign_Stripe_Green", "M_Sign_Stripe_Red"]
    for z, mat in zip(stripe_z, stripe_mats):
        for y in [-530, -310, -90]:
            box(mesh, mat, (-138, y, z), (10, 190, 10))

    # Simple 7-like mark from primitive bars.
    box(mesh, "M_Sign_Stripe_Orange", (-142, 65, 295), (11, 68, 16), (0, 0, 0))
    box(mesh, "M_Sign_Stripe_Red", (-143, 40, 278), (11, 16, 44), (0, 0, -28))
    box(mesh, "M_Sign_Stripe_Green", (-142, 102, 264), (11, 54, 14))

    # Storefront glazing, sliding door and mullions.
    box(mesh, "M_Glass_Dark_Teal", (-122, -345, 115), (18, 600, 190))
    for y in [-610, -470, -310, -150, -30]:
        box(mesh, "M_Metal_Ink", (-138, y, 116), (14, 8, 198))
    box(mesh, "M_Metal_Ink", (-139, -345, 210), (14, 620, 8))
    box(mesh, "M_Metal_Ink", (-139, -345, 35), (14, 620, 10))
    add_window(mesh, (-145, -420, 126), (9, 115, 155), False)
    add_window(mesh, (-145, -265, 126), (9, 115, 155), False)

    # Product silhouettes inside the bright shop.
    for i, y in enumerate([-575, -520, -470, -190, -130, -75]):
        box(mesh, "M_Sign_Stripe_Green" if i % 2 else "M_Sign_Stripe_Red", (-154, y, 70), (8, 32, 36))
        box(mesh, "M_Sign_Stripe_Orange", (-154, y + 20, 112), (8, 24, 42))

    # Vending machine and trash bins.
    box(mesh, "M_Vending_Blue", (-102, 110, 115), (72, 105, 210))
    box(mesh, "M_Sign_Lit_White", (-142, 110, 168), (8, 78, 86))
    for row in range(4):
        for col in range(4):
            mat = ["M_Sign_Stripe_Green", "M_Sign_Stripe_Orange", "M_Sign_Stripe_Red", "M_Window_Warm"][(row + col) % 4]
            box(mesh, mat, (-148, 76 + col * 20, 190 - row * 18), (6, 9, 8))
    box(mesh, "M_Wall_Dark_Blue", (-118, 110, 44), (12, 64, 18))
    box(mesh, "M_Pot_Terracotta", (-130, -680, 42), (60, 44, 55))
    box(mesh, "M_Pot_Terracotta", (-130, -610, 35), (48, 42, 45))
    box(mesh, "M_Plant_Green", (-142, -675, 82), (60, 52, 34))
    box(mesh, "M_Plant_Dark", (-142, -610, 70), (46, 42, 28))


def add_upper_buildings(mesh):
    # Upper apartments stacked above the store.
    box(mesh, "M_Wall_Main_Teal", (150, -310, 520), (470, 780, 360))
    box(mesh, "M_Roof_Black_Green", (150, -310, 708), (500, 820, 30))
    box(mesh, "M_Wall_Dark_Blue", (250, -520, 875), (360, 315, 300))
    box(mesh, "M_Wall_Dark_Blue", (300, -150, 885), (320, 360, 320))
    box(mesh, "M_Roof_Black_Green", (250, -520, 1040), (390, 345, 24))
    box(mesh, "M_Roof_Black_Green", (300, -150, 1050), (350, 390, 24))

    # Balconies and windows.
    add_window(mesh, (-92, -455, 518), (10, 175, 120))
    add_window(mesh, (-92, -105, 520), (10, 200, 130))
    add_window(mesh, (70, 78, 518), (10, 150, 125))
    add_window(mesh, (85, -600, 850), (10, 105, 86))
    add_window(mesh, (120, -210, 865), (10, 120, 100))
    add_window(mesh, (255, 62, 875), (10, 100, 110))

    for y in [-455, -105]:
        box(mesh, "M_Metal_Ink", (-128, y, 438), (18, 210, 12))
        for rail_y in [y - 92, y - 46, y, y + 46, y + 92]:
            box(mesh, "M_Metal_Ink", (-130, rail_y, 470), (12, 8, 80))

    # AC units.
    for y, z in [(-208, 410), (-28, 410), (-550, 690), (130, 650)]:
        box(mesh, "M_AC_OffWhite", (-142, y, z), (64, 78, 52))
        cylinder(mesh, "M_Metal_Ink", (-176, y, z), 18, 7, (0, 90, 0), 16)

    # Small roof planters.
    for y in [-560, -480, -210, -130, 10]:
        box(mesh, "M_Pot_Terracotta", (45, y, 738), (45, 35, 32))
        sphere(mesh, "M_Plant_Green", (45, y, 770), 30, 5, 8)


def add_stairs_and_right_side(mesh):
    # Stairway climbing to the right/back of the composition.
    step_count = 26
    for i in range(step_count):
        x = -125 + i * 47
        z = 18 + i * 15
        box(mesh, "M_Concrete_Cool_Wet", (x, 530, z), (50, 540, 16))
        if i % 4 == 0:
            box(mesh, "M_Puddle_Reflection", (x - 3, 530, z + 9), (30, 500, 3))

    segment_box(mesh, "M_Rail_Painted_Metal", (-170, 250, 60), (1110, 250, 472), 18)
    segment_box(mesh, "M_Rail_Painted_Metal", (-170, 810, 70), (1110, 810, 482), 18)
    for i in range(0, step_count, 3):
        x = -150 + i * 47
        z = 50 + i * 15
        box(mesh, "M_Rail_Painted_Metal", (x, 250, z), (16, 16, 120))
        box(mesh, "M_Rail_Painted_Metal", (x, 810, z + 10), (16, 16, 130))

    # Retaining walls and foliage mass along the stairs.
    segment_box(mesh, "M_Wall_Dark_Blue", (-170, 210, 20), (1110, 210, 410), 72)
    segment_box(mesh, "M_Wall_Dark_Blue", (-140, 860, 25), (1010, 860, 380), 58)
    for i in range(16):
        x = -40 + i * 62
        y = 150 + (i % 3) * 35
        z = 70 + i * 16
        sphere(mesh, "M_Plant_Dark" if i % 2 else "M_Plant_Green", (x, y, z), 52, 5, 8)

    # Right side buildings, signs and windows.
    box(mesh, "M_Background_BlueWall", (275, 1030, 300), (430, 280, 600))
    box(mesh, "M_Wall_Dark_Blue", (690, 980, 515), (390, 310, 720))
    box(mesh, "M_Roof_Black_Green", (690, 980, 885), (420, 340, 28))
    add_window(mesh, (75, 878, 355), (12, 120, 200))
    add_window(mesh, (500, 820, 440), (12, 120, 180))
    add_window(mesh, (470, 1132, 705), (12, 100, 150))
    add_window(mesh, (835, 830, 610), (12, 95, 130))

    box(mesh, "M_Sign_Paper", (248, 270, 450), (26, 82, 310))
    for z in [540, 490, 440, 390]:
        box(mesh, "M_Sign_Ink", (228, 270, z), (10, 48, 9), (0, 0, 18))
        box(mesh, "M_Sign_Ink", (227, 285, z - 18), (10, 8, 42))

    box(mesh, "M_Sign_Paper", (390, 682, 520), (24, 90, 360))
    for z in [635, 585, 530, 475, 420]:
        box(mesh, "M_Sign_Ink", (370, 682, z), (10, 50, 8), (0, 0, -15))
        box(mesh, "M_Sign_Ink", (369, 665, z - 20), (10, 8, 36))


def add_left_side_and_background(mesh):
    # Smaller houses to the left and distant uphill houses.
    box(mesh, "M_Background_BlueWall", (80, -980, 210), (470, 330, 420))
    box(mesh, "M_Roof_Black_Green", (50, -980, 450), (520, 365, 40), (0, 0, 0))
    add_window(mesh, (-160, -1090, 250), (12, 130, 120))
    add_window(mesh, (-160, -870, 300), (12, 110, 110))

    box(mesh, "M_Wall_Dark_Blue", (610, -820, 445), (420, 300, 610))
    box(mesh, "M_Background_BlueWall", (880, -435, 600), (390, 280, 520))
    box(mesh, "M_Roof_Black_Green", (610, -820, 760), (450, 330, 30))
    box(mesh, "M_Roof_Black_Green", (880, -435, 875), (410, 310, 30))
    add_window(mesh, (400, -930, 535), (10, 96, 90))
    add_window(mesh, (690, -712, 650), (10, 100, 95))
    add_window(mesh, (1010, -350, 760), (10, 86, 80))

    # Far stair landing and tiny houses at the horizon.
    for i in range(7):
        box(mesh, "M_Concrete_Cool_Wet", (930 + i * 56, 520, 450 + i * 18), (55, 430, 14))
    for j, y in enumerate([290, 460, 670]):
        box(mesh, "M_Background_BlueWall", (1230, y, 680 + j * 80), (190, 160, 180))
        add_window(mesh, (1130, y - 30, 715 + j * 80), (8, 55, 45), False)


def add_street_props(mesh):
    # Road, curbs, foreground reflections.
    box(mesh, "M_Asphalt_Wet_Night", (-360, 0, -10), (520, 2200, 20))
    box(mesh, "M_Concrete_Cool_Wet", (-90, -845, 6), (80, 340, 32))
    box(mesh, "M_Concrete_Cool_Wet", (-90, 915, 6), (80, 360, 32))
    box(mesh, "M_Puddle_Reflection", (-530, -220, 2), (140, 530, 4), (0, 0, 8))
    box(mesh, "M_Puddle_Reflection", (-390, 460, 3), (120, 420, 4), (0, 0, -12))
    box(mesh, "M_Puddle_Reflection", (-260, -645, 3), (85, 260, 4), (0, 0, -4))

    # Bicycle silhouette.
    torus(mesh, "M_Metal_Ink", (-210, -715, 58), 38, 5, (90, 0, 0))
    torus(mesh, "M_Metal_Ink", (-210, -575, 58), 38, 5, (90, 0, 0))
    segment_box(mesh, "M_Metal_Ink", (-210, -715, 58), (-210, -640, 118), 8)
    segment_box(mesh, "M_Metal_Ink", (-210, -575, 58), (-210, -640, 118), 8)
    segment_box(mesh, "M_Metal_Ink", (-210, -690, 108), (-210, -585, 112), 7)
    segment_box(mesh, "M_Metal_Ink", (-210, -640, 118), (-210, -640, 165), 7)
    box(mesh, "M_Pot_Terracotta", (-210, -640, 168), (38, 24, 10))
    segment_box(mesh, "M_Metal_Ink", (-210, -585, 112), (-210, -540, 145), 6)

    # Street planters.
    for y in [-780, -735, 850, 915, 980]:
        box(mesh, "M_Pot_Terracotta", (-120, y, 40), (48, 48, 58))
        sphere(mesh, "M_Plant_Green", (-120, y, 84), 38, 5, 9)

    # Traffic signal.
    box(mesh, "M_Metal_Ink", (85, 835, 430), (28, 28, 860))
    segment_box(mesh, "M_Metal_Ink", (85, 835, 790), (85, 450, 765), 22)
    box(mesh, "M_Metal_Ink", (83, 415, 760), (55, 225, 70))
    for y, mat in [(355, "M_Traffic_Red_Glow"), (415, "M_Traffic_Red_Glow"), (475, "M_Metal_Ink")]:
        cylinder(mesh, mat, (52, y, 760), 26, 12, (0, 90, 0), 24)

    # Utility poles and wires.
    pole_positions = [(-260, -1050, 360), (40, -650, 720), (85, 835, 760), (760, 730, 850), (980, -230, 920)]
    for x, y, h in pole_positions:
        box(mesh, "M_Metal_Ink", (x, y, h * 0.5), (24, 24, h))
        box(mesh, "M_Metal_Ink", (x, y, h - 70), (20, 300, 18))
    wire_pairs = [
        ((-260, -1120, 760), (1120, -180, 980)),
        ((-260, -1040, 700), (1120, -90, 900)),
        ((-260, -960, 635), (1120, 10, 820)),
        ((70, -650, 830), (760, 735, 920)),
        ((70, -600, 760), (760, 790, 850)),
        ((85, 835, 860), (1030, 210, 970)),
        ((85, 895, 810), (1030, 300, 900)),
    ]
    for start, end in wire_pairs:
        segment_box(mesh, "M_Metal_Ink", start, end, 8)

    # Warm street lamps.
    for loc in [(180, 710, 410), (520, 870, 520), (930, 560, 650), (-120, -910, 350)]:
        x, y, z = loc
        box(mesh, "M_Metal_Ink", (x, y, z - 95), (16, 16, 190))
        sphere(mesh, "M_Lamp_Warm_Glow", (x, y, z), 32, 6, 10)


def add_extra_detail_pass(mesh):
    # Storefront trim, shelves, posters, and door hardware.
    box(mesh, "M_Metal_Ink", (-146, -310, 324), (18, 825, 12))
    box(mesh, "M_Metal_Ink", (-146, -310, 235), (18, 825, 10))
    box(mesh, "M_Metal_Ink", (-146, -708, 278), (18, 10, 86))
    box(mesh, "M_Metal_Ink", (-146, 88, 278), (18, 10, 86))
    for z in [82, 124, 166]:
        box(mesh, "M_AC_OffWhite", (-151, -470, z), (7, 245, 7))
        box(mesh, "M_AC_OffWhite", (-151, -155, z), (7, 245, 7))
    poster_data = [
        (-151, -590, 145, "M_Sign_Stripe_Red"),
        (-151, -550, 112, "M_Sign_Stripe_Orange"),
        (-151, -500, 148, "M_Sign_Stripe_Green"),
        (-151, -205, 145, "M_Sign_Stripe_Orange"),
        (-151, -165, 112, "M_Sign_Stripe_Red"),
        (-151, -105, 148, "M_Sign_Stripe_Green"),
    ]
    for x, y, z, mat in poster_data:
        box(mesh, mat, (x, y, z), (6, 28, 40))
        box(mesh, "M_Sign_Paper", (x - 1, y, z + 27), (5, 30, 9))
    box(mesh, "M_Metal_Ink", (-154, -312, 112), (10, 8, 145))
    box(mesh, "M_Lamp_Warm_Glow", (-160, -334, 112), (8, 10, 26))
    box(mesh, "M_Lamp_Warm_Glow", (-160, -290, 112), (8, 10, 26))
    box(mesh, "M_Wall_Dark_Blue", (-164, -310, 28), (8, 115, 8))

    # Exterior conduits, gutters, AC pipes, and utility boxes.
    for y in [-720, 95]:
        box(mesh, "M_Metal_Ink", (-108, y, 510), (18, 16, 360))
        box(mesh, "M_Metal_Ink", (-111, y, 330), (22, 28, 20))
    pipe_pairs = [
        ((-176, -208, 410), (-176, -208, 350)),
        ((-176, -28, 410), (-176, -28, 350)),
        ((-176, -550, 690), (-176, -550, 620)),
        ((-176, 130, 650), (-176, 130, 590)),
    ]
    for start, end in pipe_pairs:
        segment_box(mesh, "M_AC_OffWhite", start, end, 7)
    for y in [-625, -585, -545, -505]:
        box(mesh, "M_Metal_Ink", (-173, y, 690), (8, 5, 40))
    box(mesh, "M_AC_OffWhite", (-150, 210, 420), (44, 62, 86))
    box(mesh, "M_Metal_Ink", (-178, 210, 420), (8, 50, 60))

    # Balcony rails and rooftop antennas.
    for y in [-455, -105]:
        for z in [492, 515]:
            box(mesh, "M_Metal_Ink", (-136, y, z), (10, 220, 7))
    antenna_base = [(170, -620, 1060), (360, -95, 1070), (740, -805, 790)]
    for x, y, z in antenna_base:
        box(mesh, "M_Metal_Ink", (x, y, z + 55), (9, 9, 110))
        segment_box(mesh, "M_Metal_Ink", (x, y - 70, z + 95), (x, y + 70, z + 95), 6)
        segment_box(mesh, "M_Metal_Ink", (x - 55, y, z + 130), (x + 55, y, z + 130), 5)

    # Stair tread highlights, landing clutter, and side wall block joints.
    for i in range(26):
        x = -125 + i * 47
        z = 28 + i * 15
        box(mesh, "M_Sign_Paper", (x - 20, 530, z), (5, 500, 4))
        if i % 5 == 2:
            box(mesh, "M_Metal_Ink", (x, 225, z + 45), (24, 18, 18))
            box(mesh, "M_Metal_Ink", (x, 838, z + 50), (24, 18, 18))
    for i in range(10):
        x = -95 + i * 105
        z = 45 + i * 33
        box(mesh, "M_Metal_Ink", (x, 177, z), (5, 78, 8))
        box(mesh, "M_Metal_Ink", (x, 890, z + 4), (5, 58, 7))
    box(mesh, "M_Pot_Terracotta", (1020, 845, 430), (58, 55, 54))
    sphere(mesh, "M_Plant_Green", (1020, 845, 482), 45, 5, 8)
    box(mesh, "M_Vending_Blue", (910, 875, 438), (52, 46, 72))
    box(mesh, "M_Sign_Lit_White", (885, 875, 465), (6, 32, 24))

    # Road markings, manholes, bollards, drains, and curb cuts.
    for y in [-760, -580, 520, 700]:
        box(mesh, "M_Sign_Paper", (-430, y, 5), (7, 120, 3), (0, 0, -7))
    for y in [-900, -840, -780, 760, 820, 880]:
        cylinder(mesh, "M_Rail_Painted_Metal", (-205, y, 38), 12, 72, (0, 0, 0), 12)
        box(mesh, "M_Lamp_Warm_Glow", (-205, y, 78), (25, 25, 8))
    cylinder(mesh, "M_Metal_Ink", (-470, 150, 2), 48, 6, (0, 0, 0), 24)
    cylinder(mesh, "M_Rail_Painted_Metal", (-471, 150, 6), 34, 4, (0, 0, 0), 24)
    for offset in [-30, 0, 30]:
        box(mesh, "M_Metal_Ink", (-505 + offset, 150, 10), (4, 64, 4), (0, 0, 0))
    for y in [-1030, 1030]:
        for x in [-320, -220, -120, -20]:
            box(mesh, "M_Metal_Ink", (x, y, 18), (55, 8, 10))

    # Extra signs and small facade strokes to push the alley density.
    sign_specs = [
        ((15, -760, 265), (22, 68, 240)),
        ((315, -665, 585), (20, 74, 260)),
        ((755, -610, 645), (18, 70, 220)),
        ((615, 1160, 505), (18, 72, 250)),
    ]
    for loc, dims in sign_specs:
        box(mesh, "M_Sign_Paper", loc, dims)
        x, y, z = loc
        for k in range(4):
            box(mesh, "M_Sign_Ink", (x - dims[0] * 0.5 - 4, y, z + 70 - k * 42), (8, 42, 7), (0, 0, 14 - k * 9))
            box(mesh, "M_Sign_Ink", (x - dims[0] * 0.5 - 5, y + 17, z + 52 - k * 42), (8, 7, 32))

    # More background window variety.
    for x, y, z in [
        (470, -840, 430), (520, -760, 520), (810, -510, 545),
        (930, -430, 690), (1045, 325, 720), (1200, 580, 760),
        (420, 1085, 555), (720, 1128, 735),
    ]:
        add_window(mesh, (x, y, z), (8, 58, 50), False)

    # Randomized roof and alley clutter without using rain streaks.
    random.seed(241)
    for _ in range(28):
        x = random.uniform(-60, 820)
        y = random.choice([-700, -620, -520, -210, -120, 80, 260, 920])
        z = random.uniform(715, 1040)
        box(mesh, "M_Wall_Dark_Blue", (x, y, z), (random.uniform(18, 52), random.uniform(14, 42), random.uniform(12, 34)))


def build_mesh():
    mesh = unreal.DynamicMesh()
    add_street_props(mesh)
    add_front_facade(mesh)
    add_upper_buildings(mesh)
    add_stairs_and_right_side(mesh)
    add_left_side_and_background(mesh)
    add_extra_detail_pass(mesh)

    normal_options = unreal.GeometryScriptCalculateNormalsOptions()
    normal_options.angle_weighted = True
    normal_options.area_weighted = True
    unreal.GeometryScript_Normals.recompute_normals(mesh, normal_options)
    return mesh


def create_static_mesh(mesh, materials):
    if unreal.EditorAssetLibrary.does_asset_exist(MESH_PATH):
        unreal.EditorAssetLibrary.delete_asset(MESH_PATH)

    asset_options = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    asset_options.enable_collision = True
    asset_options.enable_recompute_normals = True
    asset_options.enable_recompute_tangents = True
    asset_options.enable_nanite = False
    static_mesh, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        mesh, MESH_PATH, asset_options
    )

    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS or not static_mesh:
        raise RuntimeError(f"Static mesh creation failed: {outcome}")

    for index, material in enumerate(materials):
        static_mesh.set_material(index, material)

    unreal.EditorAssetLibrary.save_loaded_asset(static_mesh, only_if_is_dirty=False)
    return static_mesh


def clear_generated_actors():
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actor_subsystem.get_all_level_actors()
    to_delete = []
    for actor in actors:
        try:
            if actor.get_actor_label().startswith(ACTOR_PREFIX):
                to_delete.append(actor)
        except Exception:
            pass
    if to_delete:
        actor_subsystem.destroy_actors(to_delete)


def set_light(actor, intensity, color, radius=None):
    comp = actor.get_component_by_class(unreal.LightComponent)
    if not comp:
        return
    comp.set_editor_property("intensity", float(intensity))
    comp.set_editor_property("light_color", unreal.Color(int(color[0]), int(color[1]), int(color[2]), int(color[3])))
    if radius is not None and hasattr(comp, "attenuation_radius"):
        comp.set_editor_property("attenuation_radius", float(radius))


def spawn_lighting_and_camera():
    def spawn(cls, label, loc, rot=(0, 0, 0)):
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            cls, unreal.Vector(*loc), unreal.Rotator(*rot)
        )
        actor.set_actor_label(ACTOR_PREFIX + label)
        return actor

    directional = spawn(unreal.DirectionalLight, "Moon_Directional", (-900, -600, 900), (-48, 38, 0))
    set_light(directional, 0.22, (80, 155, 210, 255))

    sky = spawn(unreal.SkyLight, "Blue_Skylight", (0, 0, 500))
    comp = sky.get_component_by_class(unreal.SkyLightComponent)
    if comp:
        comp.set_editor_property("intensity", 0.35)
        comp.set_editor_property("light_color", unreal.Color(42, 95, 130, 255))

    fog = spawn(unreal.ExponentialHeightFog, "Rain_Fog", (0, 0, 0))
    fog_comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    if fog_comp:
        fog_comp.set_editor_property("fog_density", 0.025)
        fog_comp.set_editor_property("fog_height_falloff", 0.18)
        fog_comp.set_fog_inscattering_color(unreal.LinearColor(0.05, 0.22, 0.28, 1.0))

    for label, loc, intensity, radius, color in [
        ("Store_Rect_Left", (-250, -470, 180), 850, 500, (255, 214, 135, 255)),
        ("Store_Rect_Right", (-250, -125, 180), 760, 480, (255, 226, 150, 255)),
        ("Vending_Glow", (-225, 110, 185), 380, 260, (80, 220, 255, 255)),
        ("Traffic_Red", (15, 390, 760), 620, 300, (255, 48, 40, 255)),
        ("Stair_Lamp_A", (180, 710, 420), 520, 380, (255, 205, 115, 255)),
        ("Stair_Lamp_B", (520, 870, 540), 430, 360, (255, 205, 115, 255)),
        ("Distant_Lamp", (930, 560, 675), 320, 320, (255, 198, 120, 255)),
    ]:
        light = spawn(unreal.PointLight, label, loc)
        set_light(light, intensity, color, radius)

    camera_loc = unreal.Vector(-1750, -1450, 610)
    target = unreal.Vector(340, 150, 420)
    camera_rot = unreal.MathLibrary.find_look_at_rotation(camera_loc, target)
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, camera_loc, camera_rot)
    camera.set_actor_label(ACTOR_PREFIX + "Camera_Composition")
    cam_comp = camera.get_component_by_class(unreal.CameraComponent)
    if cam_comp:
        cam_comp.set_editor_property("field_of_view", 72.0)
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera_loc, camera_rot)


def create_or_open_level():
    current_world = unreal.EditorLevelLibrary.get_editor_world()
    if current_world and current_world.get_path_name().startswith(f"{LEVEL_PATH}."):
        return
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        if not unreal.EditorLevelLibrary.load_level(LEVEL_PATH):
            raise RuntimeError(f"Failed to load level: {LEVEL_PATH}")
    else:
        if not unreal.EditorLevelLibrary.new_level(LEVEL_PATH):
            raise RuntimeError(f"Failed to create level: {LEVEL_PATH}")


def place_scene(static_mesh):
    create_or_open_level()
    clear_generated_actors()
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
    )
    actor.set_actor_label(ACTOR_PREFIX + "Geometry_Diorama")
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_static_mesh(static_mesh)
    comp.set_editor_property("cast_shadow", True)
    spawn_lighting_and_camera()
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, LEVEL_PATH):
        raise RuntimeError(f"Failed to save map: {LEVEL_PATH}")
    return actor


def main():
    ensure_dir(ROOT)
    create_or_open_level()
    clear_generated_actors()
    delete_stale_assets()
    materials = make_materials()
    mesh = build_mesh()
    info = unreal.GeometryScript_MeshQueries.get_mesh_info_string(mesh)
    static_mesh = create_static_mesh(mesh, materials)
    actor = place_scene(static_mesh)
    unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True)
    unreal.log(f"Rainy convenience street generated at {LEVEL_PATH}")
    unreal.log(f"Static mesh: {static_mesh.get_path_name()}")
    unreal.log(f"Placed actor: {actor.get_actor_label()}")
    unreal.log(f"Mesh info: {info}")
    return {
        "level": LEVEL_PATH,
        "mesh": MESH_PATH,
        "actor": actor.get_actor_label(),
        "material_count": len(materials),
        "mesh_info": info,
    }


RESULT = main()
print("RESULT", RESULT)
