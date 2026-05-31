# Hunyuan3D Clean Input Set

Use these images as the preferred image-to-3D inputs for the rainy hillside alley prop set.

The parent `RainyAlleyProps` folder contains richer art-direction references. This `CleanInput` folder is intentionally simpler: light background, reduced base planes, fewer environmental details, and larger isolated silhouettes.

## Preferred Generation Order

| Order | File | Notes |
| --- | --- | --- |
| 01 | `hunyuan_input_01_corner_convenience_store.png` | Main anchor building. Good first shape test. |
| 02 | `hunyuan_input_02_stair_alley_module.png` | Environment module. Keep railings if shape output is stable. |
| 03 | `hunyuan_input_03_hillside_residential_mass.png` | Background building cluster. Expect cleanup around balconies and antennas. |
| 04 | `hunyuan_input_04_facade_window_balcony_ac.png` | Reusable wall kit piece. Good for repeat placement. |
| 05 | `hunyuan_input_05_blue_vending_machine.png` | Simple box prop. Good high-confidence test. |
| 06 | `hunyuan_input_06_vertical_shop_sign.png` | Thin bracket may need cleanup or manual replacement. |
| 07 | `hunyuan_input_07_utility_pole_simplified.png` | Generate pole body; rebuild long wires manually in Unreal if needed. |
| 08 | `hunyuan_input_08_traffic_signal.png` | Good isolated prop. Red lens is the intended active light. |
| 09 | `hunyuan_input_09_potted_plants_cluster.png` | Treat as a stylized mass; individual leaves may not survive cleanly. |
| 10 | `hunyuan_input_10_wet_road_crosswalk_tile.png` | Flat ground tile. Useful for material/mesh reference. |

## Input Rules

- Prefer this folder over the richer concept images when running Hunyuan3D shape generation.
- Run shape first, inspect geometry, then run 1K texture/PBR only for accepted meshes.
- Keep one prop per run.
- Do not feed the contact sheet into Hunyuan3D.
- If thin details fail, rebuild them in Unreal with splines, simple meshes, or cards.

## Files

- `contact_sheet_hunyuan_clean_inputs.png` is for human review only.
- Individual `hunyuan_input_*.png` files are the actual input candidates.
