# Rainy Alley Generated 3D Outputs - 512 PBR

Generated with the local Hunyuan3D-2.1 install at `D:/Git/Hunyuan3D-2.1`.

## Decision

The project uses 512 texture maps for this pass. A native 1K texture attempt with `--resolution 1024 --render-size 1024 --texture-size 1024` consumed nearly all 16GB VRAM and did not finish within the run window, so 512 is the stable target for now.

## Generated Assets

| Asset | Shape GLB | Textured OBJ | Texture maps |
| --- | --- | --- | --- |
| Corner convenience store | `shape_glb/01_corner_convenience_store.glb` | `textured_obj/01_corner_convenience_store/textured_mesh.obj` | albedo, metallic, roughness at 512x512 |
| Stair alley module | `shape_glb/02_stair_alley_module.glb` | `textured_obj/02_stair_alley_module/textured_mesh.obj` | albedo, metallic, roughness at 512x512 |
| Hillside residential mass | `shape_glb/03_hillside_residential_mass.glb` | `textured_obj/03_hillside_residential_mass/textured_mesh.obj` | albedo, metallic, roughness at 512x512 |
| Facade window balcony AC | `shape_glb/04_facade_window_balcony_ac.glb` | `textured_obj/04_facade_window_balcony_ac/textured_mesh.obj` | albedo, metallic, roughness at 512x512 |
| Blue vending machine | `shape_glb/05_blue_vending_machine.glb` | `textured_obj/05_blue_vending_machine/textured_mesh.obj` | albedo, metallic, roughness at 512x512 |
| Vertical shop sign | `shape_glb/06_vertical_shop_sign.glb` | `textured_obj/06_vertical_shop_sign/textured_mesh.obj` | albedo, metallic, roughness at 512x512 |
| Utility pole simplified | `shape_glb/07_utility_pole_simplified.glb` | `textured_obj/07_utility_pole_simplified/textured_mesh.obj` | albedo, metallic, roughness at 512x512 |
| Traffic signal | `shape_glb/08_traffic_signal.glb` | `textured_obj/08_traffic_signal/textured_mesh.obj` | albedo, metallic, roughness at 512x512 |
| Potted plants cluster | `shape_glb/09_potted_plants_cluster.glb` | `textured_obj/09_potted_plants_cluster/textured_mesh.obj` | albedo, metallic, roughness at 512x512 |
| Wet road crosswalk tile | `shape_glb/10_wet_road_crosswalk_tile.glb` | `textured_obj/10_wet_road_crosswalk_tile/textured_mesh.obj` | albedo, metallic, roughness at 512x512 |

## Validation

Validated on 2026-05-31 with the Hunyuan3D Python environment.

| Asset | GLB size | Vertices | Faces |
| --- | ---: | ---: | ---: |
| 01 corner convenience store | 21.03 MB | 612469 | 1225374 |
| 02 stair alley module | 15.64 MB | 455299 | 911382 |
| 03 hillside residential mass | 8.54 MB | 248356 | 497946 |
| 04 facade window balcony AC | 4.83 MB | 140572 | 281246 |
| 05 blue vending machine | 9.51 MB | 277103 | 554260 |
| 06 vertical shop sign | 3.31 MB | 96306 | 192632 |
| 07 utility pole simplified | 1.73 MB | 50187 | 100526 |
| 08 traffic signal | 5.10 MB | 148487 | 296994 |
| 09 potted plants cluster | 13.23 MB | 384237 | 771772 |
| 10 wet road crosswalk tile | 5.25 MB | 152768 | 305532 |

All ten GLBs load with valid geometry. All ten textured OBJ folders contain `.obj`, `.mtl`, albedo, metallic, and roughness maps, and all texture maps are 512x512.

## Preview

`contact_sheet_generated3d_512_albedo.png` shows the generated 512 albedo maps for quick review.

## Notes

- The GLB files are raw shape-generation outputs.
- The OBJ folders contain remeshed textured outputs with `.mtl`, albedo JPG, metallic JPG, and roughness JPG.
- Inspect geometry before importing as final Unreal assets. Generated meshes are dense and may need decimation or cleanup.
- Thin details such as signal brackets, balcony rails, wires, plants, and signs may need manual rebuilds in Unreal.
