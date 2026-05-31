# Rainy Alley Hunyuan3D Prop References

Private-use concept references for splitting the rainy hillside alley concept into individual 3D-generation-friendly background props.

## Files

| Order | File | Intended model |
| --- | --- | --- |
| 01 | `prop_01_corner_convenience_store.png` | Corner convenience store building |
| 02 | `prop_02_stair_alley_module.png` | Steep stair alley module |
| 03 | `prop_03_hillside_residential_mass.png` | Background stacked residential mass |
| 04 | `prop_04_facade_window_balcony_ac.png` | Reusable facade/window/balcony/AC wall module |
| 05 | `prop_05_blue_vending_machine.png` | Blue drink vending machine |
| 06 | `prop_06_vertical_shop_sign.png` | Vertical hanging shop sign |
| 07 | `prop_07_utility_pole_wires.png` | Utility pole with cable reference |
| 08 | `prop_08_traffic_signal.png` | Horizontal traffic signal |
| 09 | `prop_09_potted_plants_cluster.png` | Potted plant cluster |
| 10 | `prop_10_wet_road_crosswalk_tile.png` | Wet road and crosswalk ground tile |
| Ref | `reference_original_concept_board.png` | Original composition/reference board |

## Hunyuan3D Notes

- Generate each prop as a separate model. Avoid using the full reference board as a direct image-to-3D input.
- Prefer shape generation first, then run texture/PBR separately at 1K.
- For RTX 5070 Ti 16GB, close GPU-heavy apps before texture generation and keep the texture run isolated.
- Thin elements such as wires, railings, plant leaves, and cables may need manual cleanup or separate Unreal spline/card meshes.
- Current references are for private/internal use. If the assets become public or commercial, clean up readable signs, brand-like shapes, and copied visual marks before release.
