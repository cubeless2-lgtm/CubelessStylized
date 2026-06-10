# Niagara Learning Index

CubelessStylized? ?? Niagara ??? ?? ?? ?? ??? ????. ??? ??? ?? ? ? ??? ?? ???? ??? ??? ???, ???, ????, ???? ???? ???.

## ??
- ?? Niagara ??? ?? ?? ????? ????.
- ??/??? ??? `/Game/_MCP_Temp/NiagaraLearning/` ???? ???.
- ? ??? ??? ?? ??? `NiagaraSystem`? ??? ?, ??? `NiagaraEmitter`? ????/??? ???? ????? ???? ????.

## ?? ??
- ?? ??: `2026-06-11T01:41:45`
- ??: `5.7.4-51494982+++UE5+Release-5.7`
- ? Niagara ?? ??: `719`
- ?? ?? ??: `/Game/_MCP_Temp/NiagaraLearning/20260611_014252`
- ?? ?? ??: `10`

## ???? ??
| ?? | ? |
| --- | ---: |
| `NiagaraEmitter` | 41 |
| `NiagaraParameterCollection` | 5 |
| `NiagaraScript` | 39 |
| `NiagaraSystem` | 634 |

## ????? ??
| ?? | ? |
| --- | ---: |
| `uncategorized` | 369 |
| `trail_ribbon_motion` | 107 |
| `burst_impact_projectile` | 79 |
| `weather_rain_snow` | 60 |
| `smoke_fog` | 54 |
| `aura_glow_magic` | 31 |
| `ambient_dust_debris` | 28 |
| `lightning_energy` | 25 |
| `ring_vortex_area` | 13 |
| `reactive_interaction` | 7 |
| `fire_flame` | 5 |

## ?? ??
| ?? | ? |
| --- | ---: |
| `/Game/EL/ART` | 642 |
| `/Game/UltraDynamicSky/Particles` | 58 |
| `/Game/UltraVolumetrics/Core` | 13 |
| `/Game/UltraVolumetrics/Demo` | 4 |
| `/Game/Cubeless/Reactive` | 1 |
| `/Game/LevelPrototyping/Interactable` | 1 |

## ?? ?? Niagara
| ?? | ?? ?? | ?? |
| --- | --- | --- |
| `/Game/EL/ART/BG/FX/Viking_Village/VFXUpdate/Niagara/NS_Torch_01.NS_Torch_01` | `/Game/_MCP_Temp/NiagaraLearning/20260611_014252/Systems/Learn_NS_Torch_01.Learn_NS_Torch_01` | `duplicated` |
| `/Game/UltraDynamicSky/Particles/Rain.Rain` | `/Game/_MCP_Temp/NiagaraLearning/20260611_014252/Systems/Learn_Rain.Learn_Rain` | `duplicated` |
| `/Game/UltraDynamicSky/Particles/Lightning_Strike.Lightning_Strike` | `/Game/_MCP_Temp/NiagaraLearning/20260611_014252/Systems/Learn_Lightning_Strike.Learn_Lightning_Strike` | `duplicated` |
| `/Game/Cubeless/Reactive/NS_Reactive_RTTexturePainter.NS_Reactive_RTTexturePainter` | `/Game/_MCP_Temp/NiagaraLearning/20260611_014252/Systems/Learn_NS_Reactive_RTTexturePainter.Learn_NS_Reactive_RTTexturePainter` | `duplicated` |
| `/Game/UltraVolumetrics/Core/Niagara/NS_Ring.NS_Ring` | `/Game/_MCP_Temp/NiagaraLearning/20260611_014252/Systems/Learn_NS_Ring.Learn_NS_Ring` | `duplicated` |
| `/Game/UltraVolumetrics/Core/Niagara/NS_TrailCharacter.NS_TrailCharacter` | `/Game/_MCP_Temp/NiagaraLearning/20260611_014252/Systems/Learn_NS_TrailCharacter.Learn_NS_TrailCharacter` | `duplicated` |
| `/Game/UltraVolumetrics/Core/Niagara/NS_Burst.NS_Burst` | `/Game/_MCP_Temp/NiagaraLearning/20260611_014252/Systems/Learn_NS_Burst.Learn_NS_Burst` | `duplicated` |
| `/Game/UltraVolumetrics/Core/Niagara/NS_Vortex.NS_Vortex` | `/Game/_MCP_Temp/NiagaraLearning/20260611_014252/Systems/Learn_NS_Vortex.Learn_NS_Vortex` | `duplicated` |
| `/Game/UltraVolumetrics/Demo/FX/NS_LaserBeam.NS_LaserBeam` | `/Game/_MCP_Temp/NiagaraLearning/20260611_014252/Systems/Learn_NS_LaserBeam.Learn_NS_LaserBeam` | `duplicated` |
| `/Game/UltraVolumetrics/Demo/FX/NS_Laserblast.NS_Laserblast` | `/Game/_MCP_Temp/NiagaraLearning/20260611_014252/Systems/Learn_NS_Laserblast.Learn_NS_Laserblast` | `duplicated` |

## ??? ??? ??
- `fire_flame`: ?, ??, ??, ??, fire, torch, ember -> Torch/ChimneyFlame ?? ???? ???? ember/fire/smoke ?? ????? ?????.
- `smoke_fog`: ??, ??, ??, fog, smoke, mist -> UltraVolumetrics ?? smoke/fog ??? ????? ?? soft alpha/noise ????? ????.
- `weather_rain_snow`: ?, ?, ??, ???, rain, snow, storm -> UltraDynamicSky weather ???? UDW/UDS ???? ???? ?? ????.
- `lightning_energy`: ??, ??, ?, laser, lightning, spark -> Lightning/Beam/Laser ???? ????? ?? ribbon/beam ???? ???? ????.
- `aura_glow_magic`: ??, ??, ??, aura, glow, magic -> Aura/Glow ??? ?????? Ring/Burst ???? ????.
- `trail_ribbon_motion`: ??, ??, ??, trail, ribbon, slash, swing -> Trail/Ribbon/Swing ????? ???? ribbon renderer ??? ????.
- `burst_impact_projectile`: ??, ??, ???, impact, burst, projectile -> Burst/Projectile/Laserblast ??? ????? ?? glow, smoke, debris ???? ?? ??? ??.
- `reactive_interaction`: ????, ???, ??, reactive, interaction, foliage -> Reactive_RTTexturePainter? interactive foliage ???? ???? ?? ????.

## ????? ?? ???
### ambient_dust_debris
- `/Game/EL/ART/FX/Niagara/System/Monster/NPC/FX_S_Clean_Dust01.FX_S_Clean_Dust01` score `18.2`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_J008, /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_K004, /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_Y008
- `/Game/UltraDynamicSky/Particles/Dust.Dust` score `16.5`; material: /Game/UltraDynamicSky/Materials/Weather/Dust_ParticleMat, /Game/UltraDynamicSky/Materials/Weather/Rain_ParticleMat
- `/Game/UltraDynamicSky/Particles/Wind_Debris.Wind_Debris` score `15.35`; material: /Game/UltraDynamicSky/Materials/Weather/Rain_ParticleMat, /Game/UltraDynamicSky/Materials/Weather/Wind_Debris
- `/Game/EL/ART/FX/Niagara/System/Monster/NPC/FX_S_Clean_Dust02.FX_S_Clean_Dust02` score `14.8`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_K004, /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_Y008, /Game/EL/ART/FX/Materials/MI/FX_MI_Spark_Y005
- `/Game/EL/ART/FX/Niagara/System/PC/Hammer/FX_S_HammerDust02B.FX_S_HammerDust02B` score `14.55`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_Y003, /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_Y008, /Game/EL/Art/FX/Materials/MI/FX_MI_Smoke_Y012
- `/Game/EL/ART/FX/Niagara/System/BG/FX_S_dust_01.FX_S_dust_01` score `13.75`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Boke_J001, /Game/EL/ART/FX/Materials/MI/FX_MI_Boke_J002, /Game/EL/ART/FX/Materials/MI/FX_MI_Spark_Y004
- `/Game/EL/ART/FX/Niagara/System/SQ/P0010/FX_S_SEQ_P0010_S01_dust.FX_S_SEQ_P0010_S01_dust` score `13.75`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Boke_J001, /Game/EL/ART/FX/Materials/MI/FX_MI_Boke_J002, /Game/EL/ART/FX/Materials/MI/FX_MI_Spark_Y004
- `/Game/EL/ART/FX/Niagara/System/SQ/IGN/CedarForest_Burst_030/FX_S_SEQ_IGN_CedarForest_Burst_030_Dust.FX_S_SEQ_IGN_CedarForest_Burst_030_Dust` score `13.35`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Stone_Y001, /Game/EL/Art/FX/Materials/MI/FX_MI_Smoke_Y012

### aura_glow_magic
- `/Game/EL/ART/FX/Niagara/System/SQ/P0020/FX_SEQ_BodyAura01.FX_SEQ_BodyAura01` score `28.55`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_AuraHelix_Y062, /Game/EL/ART/FX/Materials/MI/FX_MI_AuraHelix_Y063, /Game/EL/ART/FX/Materials/MI/FX_MI_AuraHelix_Y065
- `/Game/EL/ART/FX/Niagara/System/Monster/High_Guard/FX_S_Guard_MagicShield_Loop01.FX_S_Guard_MagicShield_Loop01` score `25.0`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_AuraCircle_T003, /Game/EL/ART/FX/Materials/MI/FX_MI_AuraCircle_T004, /Game/EL/ART/FX/Materials/MI/FX_MI_MagicShield_T001
- `/Game/EL/ART/FX/Niagara/System/Monster/PalgaBaby/FX_S_PalgaBaby_Buff01.FX_S_PalgaBaby_Buff01` score `22.6`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_AuraDepth_K002, /Game/EL/ART/FX/Materials/MI/FX_MI_AuraDepth_Y002, /Game/EL/ART/FX/Materials/MI/FX_MI_Aura_Y043
- `/Game/EL/ART/FX/Niagara/System/Monster/NPC/FX_S_Magician02.FX_S_Magician02` score `22.5`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_AuraHelix_Y036, /Game/EL/ART/FX/Materials/MI/FX_MI_AuraHelix_Y042, /Game/EL/ART/FX/Materials/MI/FX_MI_Aura_Y031
- `/Game/EL/ART/FX/Niagara/System/Monster/High_Guard/FX_S_Guard_MagicArrow_Hit.FX_S_Guard_MagicArrow_Hit` score `18.85`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_Y009, /Game/EL/ART/FX/Materials/MI/FX_MI_HitRef_J002, /Game/EL/ART/FX/Materials/MI/FX_MI_Shockwave_J007
- `/Game/EL/ART/FX/FX_Test_RD/FX_S_EntangleShot01.FX_S_EntangleShot01` score `18.8`; material: /Game/EL/Art/FX/Materials/MI/FX_MI_AuraCircle_Y002, /Game/EL/Art/FX/Materials/MI/FX_MI_Glow_Y003, /Game/EL/Art/FX/Materials/MI/FX_MI_HitRef_Y001
- `/Game/EL/ART/FX/Niagara/System/Monster/PigTail/FX_S_PigTail_Buff_PowerUp_02.FX_S_PigTail_Buff_PowerUp_02` score `18.65`; material: /Game/EL/ART/FX/Materials/M/FX_MI_Basic01_H013, /Game/EL/ART/FX/Materials/M/FX_MI_Basic01_H014, /Game/EL/ART/FX/Materials/MI/FX_MI_Aura_H006
- `/Game/EL/ART/FX/Niagara/System/SQ/P0020/FX_S_SEQ_Compass02_Glow.FX_S_SEQ_Compass02_Glow` score `18.6`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_Y018, /Game/EL/ART/FX/Materials/MI/FX_MI_Rune_Y015, /Game/EL/ART/FX/Materials/MI/FX_MI_Rune_Y018

### burst_impact_projectile
- `/Game/EL/ART/FX/Niagara/System/Monster/Aster/FX_S_Aster_CS_FlyElecBreath_Hit.FX_S_Aster_CS_FlyElecBreath_Hit` score `40.15`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Beam_Y004, /Game/EL/ART/FX/Materials/MI/FX_MI_Elec_K001, /Game/EL/ART/FX/Materials/MI/FX_MI_Elec_K002
- `/Game/EL/ART/FX/Niagara/System/Monster/Aster/FX_S_Aster_Burst01_Area01.FX_S_Aster_Burst01_Area01` score `35.85`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Beam_Y004, /Game/EL/ART/FX/Materials/MI/FX_MI_Elec_Y002, /Game/EL/ART/FX/Materials/MI/FX_MI_HitRef_J001
- `/Game/EL/ART/FX/Niagara/System/Monster/Aster/FX_S_Aster_CS_ElecBreath_Shot01.FX_S_Aster_CS_ElecBreath_Shot01` score `32.0`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Beam_Y004, /Game/EL/ART/FX/Materials/MI/FX_MI_Elec_K002, /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_J001
- `/Game/EL/ART/FX/Niagara/System/Monster/Aster/FX_S_Aster_ElecBreath_Shot01.FX_S_Aster_ElecBreath_Shot01` score `29.95`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Beam_Y004, /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_J001, /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J002
- `/Game/EL/ART/FX/Niagara/System/Common/Hit/FX_S_Hit_Sword_Blood01.FX_S_Hit_Sword_Blood01` score `29.25`; material: /Game/EL/ART/FX/Materials/M/FX_M_BloodParticle01, /Game/EL/ART/FX/Materials/MI/FX_MI_DecalBlood_Y002, /Game/EL/ART/FX/Materials/MI/FX_MI_DecalBlood_Y003
- `/Game/EL/ART/FX/Niagara/System/Common/Hit/FX_S_Hit_Sword_Blood01_Big.FX_S_Hit_Sword_Blood01_Big` score `29.25`; material: /Game/EL/ART/FX/Materials/M/FX_M_BloodParticle01, /Game/EL/ART/FX/Materials/MI/FX_MI_DecalBlood_Y002, /Game/EL/ART/FX/Materials/MI/FX_MI_DecalBlood_Y003
- `/Game/EL/ART/FX/Niagara/System/Common/Hit/FX_S_Hit_Blood01.FX_S_Hit_Blood01` score `28.45`; material: /Game/EL/ART/FX/Materials/M/FX_M_BloodParticle01, /Game/EL/ART/FX/Materials/MI/FX_MI_DecalBlood_Y001, /Game/EL/ART/FX/Materials/MI/FX_MI_DecalBlood_Y002
- `/Game/EL/ART/FX/Niagara/System/Monster/Aster/FX_S_Aster_FlyingBreath_Shot01.FX_S_Aster_FlyingBreath_Shot01` score `28.0`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Beam_Y004, /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_J001, /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_J007_Fresnel

### fire_flame
- `/Game/EL/ART/BG/FX/Viking_Village/VFXUpdate/Niagara/NS_Torch_01.NS_Torch_01` score `17.0`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Fire_T001, /Game/EL/ART/FX/Materials/MI/FX_MI_Fire_Y002, /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_J001
- `/Game/EL/ART/FX/Niagara/System/Monster/BoggartBow/FX_S_FireArrow_Projectile02.FX_S_FireArrow_Projectile02` score `14.3`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Fire_J002, /Game/EL/ART/FX/Materials/MI/FX_MI_Ribbon_K002, /Game/EL/Art/FX/Materials/MI/FX_MI_Spark01_Y001
- `/Game/EL/ART/BG/FX/Viking_Village/VFXUpdate/Niagara/NS_Torch_02.NS_Torch_02` score `9.1`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Fire_T002, /Game/EL/ART/FX/Materials/MI/FX_MI_Fire_Y002, /Game/EL/Art/FX/Materials/MI/FX_MI_Glow_Y003
- `/Game/EL/ART/BG/FX/Viking_Village/VFXUpdate/Niagara/NS_ChimneyFlame_01.NS_ChimneyFlame_01` score `8.95`; material: /Game/EL/ART/BG/FX/Viking_Village/VFXUpdate/Materials/MI_ChimneySmoke_MV_01, /Game/EL/ART/BG/FX/Viking_Village/VFXUpdate/Materials/MI_Ember01, /Game/EL/ART/BG/FX/Viking_Village/VFXUpdate/Materials/MI_Fire_MV_01

### lightning_energy
- `/Game/EL/ART/FX/Niagara/System/Monster/High_Guard/FX_S_Guard_Lightning_CC_02.FX_S_Guard_Lightning_CC_02` score `21.95`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_Y009, /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J003, /Game/EL/ART/FX/Materials/MI/FX_MI_Ribbon_Y012
- `/Game/EL/ART/FX/Niagara/System/Common/Doodad/FX_S_ElectricPotion01.FX_S_ElectricPotion01` score `21.55`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Beam_Y008, /Game/EL/ART/FX/Materials/MI/FX_MI_Elec_Y001, /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_Dof_J001
- `/Game/EL/ART/FX/Niagara/System/SQ/QM0020/FX_S_QM0020_Spark01.FX_S_QM0020_Spark01` score `18.75`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_AuraDepth_K002, /Game/EL/ART/FX/Materials/MI/FX_MI_AuraHelix_Y018, /Game/EL/ART/FX/Materials/MI/FX_MI_Spark_Y002
- `/Game/UltraDynamicSky/Particles/Lightning_Strike.Lightning_Strike` score `18.0`; material: /Game/UltraDynamicSky/Materials/Weather/LightningBolt_ParticleMat, /Game/UltraDynamicSky/Materials/Weather/LightningFlare_ParticleMat, /Game/UltraDynamicSky/Materials/Weather/Lightning_Light_Rays_Card
- `/Game/EL/ART/FX/Niagara/System/Monster/PalgaGoric/FX_S_PalgaGoric_Spark01.FX_S_PalgaGoric_Spark01` score `16.3`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_Y013, /Game/EL/ART/FX/Materials/MI/FX_MI_Spark_Y002, /Game/EL/Art/FX/Materials/MI/FX_MI_Glow_Y003
- `/Game/UltraDynamicSky/Particles/Obscured_Lightning.Obscured_Lightning` score `16.1`; material: /Game/UltraDynamicSky/Materials/Weather/LightningFlare_ParticleMat_Obscured, /Game/UltraDynamicSky/Materials/Weather/Lightning_Glow, /Game/UltraDynamicSky/Materials/Weather/Lightning_Rainfall_Particle
- `/Game/EL/ART/FX/Niagara/System/SQ/Aster/FX_Aster_S_Smoke_ShockWave.FX_Aster_S_Smoke_ShockWave` score `14.95`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J003, /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_J004, /Game/EL/Art/FX/Materials/MI/FX_MI_Smoke_Y012
- `/Game/EL/ART/FX/Niagara/System/SQ/QM0020/FX_S_QM0020_Spark02.FX_S_QM0020_Spark02` score `14.4`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_AuraDepth_K002, /Game/EL/ART/FX/Materials/MI/FX_MI_Spark_Y002, /Game/EL/Art/FX/Materials/MI/FX_MI_Spark01_Y001

### reactive_interaction
- `/Game/UltraDynamicSky/Particles/WeatherOcclusionVolumeSystem.WeatherOcclusionVolumeSystem` score `37.15`; material: indexed material ??
- `/Game/UltraDynamicSky/Particles/DLWE_Interaction_System.DLWE_Interaction_System` score `17.1`; material: /Game/UltraDynamicSky/Materials/Weather/Snow_Trail_Particle
- `/Game/UltraDynamicSky/Particles/Puddle_FluidGrid.Puddle_FluidGrid` score `13.0`; material: /Game/UltraDynamicSky/Materials/Weather/Puddle_Water, /Game/UltraDynamicSky/Materials/Weather/Puddle_Wet_Decal
- `/Game/Cubeless/Reactive/NS_Reactive_RTTexturePainter.NS_Reactive_RTTexturePainter` score `9.2`; material: indexed material ??
- `/Game/UltraDynamicSky/Particles/DF_Occlusion_Test.DF_Occlusion_Test` score `8.5`; material: indexed material ??
- `/Game/UltraDynamicSky/Particles/Clear_WeatherOcclusionVolume.Clear_WeatherOcclusionVolume` score `7.75`; material: indexed material ??

### ring_vortex_area
- `/Game/EL/ART/FX/Niagara/System/Monster/Aster/FX_S_Aster_Burst01_Area01.FX_S_Aster_Burst01_Area01` score `35.85`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Beam_Y004, /Game/EL/ART/FX/Materials/MI/FX_MI_Elec_Y002, /Game/EL/ART/FX/Materials/MI/FX_MI_HitRef_J001
- `/Game/EL/ART/FX/Niagara/System/Monster/ShadeWing/FX_S_ShadeWing_Skill01_Area02.FX_S_ShadeWing_Skill01_Area02` score `33.45`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_AuraHelix_K024, /Game/EL/ART/FX/Materials/MI/FX_MI_AuraHelix_K027, /Game/EL/ART/FX/Materials/MI/FX_MI_AuraHelix_K028
- `/Game/UltraDynamicSky/Particles/Radial_Storm.Radial_Storm` score `20.95`; material: /Game/UltraDynamicSky/Materials/Weather/LightningFlare_ParticleMat_Obscured, /Game/UltraDynamicSky/Materials/Weather/Lightning_Glow, /Game/UltraDynamicSky/Materials/Weather/Lightning_Rainfall_Particle
- `/Game/EL/ART/FX/Niagara/System/Monster/Aster/FX_S_Aster_ATK_Skill01_During_01.FX_S_Aster_ATK_Skill01_During_01` score `17.0`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J002, /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J003, /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_J004
- `/Game/EL/ART/FX/Niagara/System/Monster/Aster/FX_S_Aster_ATK_Skill01_During_02.FX_S_Aster_ATK_Skill01_During_02` score `17.0`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J002, /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J003, /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_J004
- `/Game/UltraVolumetrics/Core/Niagara/NS_Ring.NS_Ring` score `16.25`; material: /Game/UltraVolumetrics/Core/Material/Instances/MI_ObjectIntSprite
- `/Game/EL/ART/FX/Niagara/System/Monster/ShadeWing/FX_S_ShadeWing_Skill01_Area01.FX_S_ShadeWing_Skill01_Area01` score `14.7`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_AuraHelix_Y009, /Game/EL/ART/FX/Materials/MI/FX_M_RadialBlur01_Y001, /Game/EL/Art/FX/Materials/MI/FX_MI_Spark01_Y001
- `/Game/UltraVolumetrics/Core/Niagara/NS_Vortex.NS_Vortex` score `11.7`; material: /Game/UltraVolumetrics/Core/Material/Instances/MI_ObjectIntSprite

### smoke_fog
- `/Game/EL/ART/FX/Niagara/System/SQ/P0010/FX_S_SEQ_P0010_SmokeTrail01.FX_S_SEQ_P0010_SmokeTrail01` score `21.75`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_AuraDepth_Y003, /Game/EL/ART/FX/Materials/MI/FX_MI_Simple_particle_J004, /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_J002
- `/Game/EL/ART/FX/Niagara/System/SQ/P0016/FX_S_SEQ_P0016_Smoke02.FX_S_SEQ_P0016_Smoke02` score `18.05`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_J002, /Game/EL/ART/FX/Materials/MI/FX_MI_Stone_Y001, /Game/EL/ART/FX/Materials/MI/FX_MI_Wood_Y001
- `/Game/EL/ART/FX/Niagara/System/SQ/P0016/FX_S_SEQ_P0016_Smoke03.FX_S_SEQ_P0016_Smoke03` score `18.05`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_J002, /Game/EL/ART/FX/Materials/MI/FX_MI_Stone_Y001, /Game/EL/ART/FX/Materials/MI/FX_MI_Wood_Y001
- `/Game/EL/ART/FX/Niagara/System/SQ/Aster/FX_Aster_S_Smoke.FX_Aster_S_Smoke` score `17.0`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J002, /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J003, /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_J004
- `/Game/UltraVolumetrics/Core/Niagara/NS_Jump.NS_Jump` score `16.5`; material: /Game/UltraVolumetrics/Core/Material/Instances/MI_ObjectIntSprite
- `/Game/UltraVolumetrics/Core/Niagara/NS_Ring.NS_Ring` score `16.25`; material: /Game/UltraVolumetrics/Core/Material/Instances/MI_ObjectIntSprite
- `/Game/UltraVolumetrics/Core/Niagara/NS_TrailObjects.NS_TrailObjects` score `15.95`; material: /Game/UltraVolumetrics/Core/Material/Instances/MI_ObjectIntSprite
- `/Game/EL/ART/FX/Niagara/System/SQ/Aster/FX_Aster_S_Smoke_ShockWave.FX_Aster_S_Smoke_ShockWave` score `14.95`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J003, /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_J004, /Game/EL/Art/FX/Materials/MI/FX_MI_Smoke_Y012

### trail_ribbon_motion
- `/Game/EL/ART/FX/Niagara/System/Common/Hit/FX_S_Hit_Sword_Blood01.FX_S_Hit_Sword_Blood01` score `29.25`; material: /Game/EL/ART/FX/Materials/M/FX_M_BloodParticle01, /Game/EL/ART/FX/Materials/MI/FX_MI_DecalBlood_Y002, /Game/EL/ART/FX/Materials/MI/FX_MI_DecalBlood_Y003
- `/Game/EL/ART/FX/Niagara/System/Common/Hit/FX_S_Hit_Sword_Blood01_Big.FX_S_Hit_Sword_Blood01_Big` score `29.25`; material: /Game/EL/ART/FX/Materials/M/FX_M_BloodParticle01, /Game/EL/ART/FX/Materials/MI/FX_MI_DecalBlood_Y002, /Game/EL/ART/FX/Materials/MI/FX_MI_DecalBlood_Y003
- `/Game/EL/ART/FX/Niagara/System/SQ/P0010/FX_S_SEQ_P0010_SmokeTrail01.FX_S_SEQ_P0010_SmokeTrail01` score `21.75`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_AuraDepth_Y003, /Game/EL/ART/FX/Materials/MI/FX_MI_Simple_particle_J004, /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_J002
- `/Game/EL/ART/FX/Niagara/System/PC/Sword/FX_S_Sword_C_Skill01_Shot02.FX_S_Sword_C_Skill01_Shot02` score `20.65`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Crack_Y002, /Game/EL/ART/FX/Materials/MI/FX_MI_SmokeMesh_Y001, /Game/EL/ART/FX/Materials/MI/FX_MI_Smoke_Y001
- `/Game/EL/ART/FX/Niagara/System/Monster/Arlea/FX_S_Arlea_Skill02_AnimTrail01.FX_S_Arlea_Skill02_AnimTrail01` score `19.5`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Ribbon_K016, /Game/EL/ART/FX/Materials/MI/FX_MI_Ribbon_K023, /Game/EL/ART/FX/Materials/MI/FX_MI_Ribbon_K024
- `/Game/EL/ART/FX/Niagara/System/PC/Sword/FX_S_KickTrail01.FX_S_KickTrail01` score `19.35`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_KickTrail_Y001, /Game/EL/ART/FX/Materials/MI/FX_MI_KickTrail_Y002, /Game/EL/ART/FX/Materials/MI/FX_M_SwordTrail_Y001
- `/Game/EL/ART/FX/Niagara/System/PC/Sword/FX_S_SwordTrail06.FX_S_SwordTrail06` score `19.35`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_SwordTrail_Y011, /Game/EL/ART/FX/Materials/MI/FX_MI_SwordTrail_Y012, /Game/EL/ART/FX/Materials/MI/FX_M_SwordTrail_Y001
- `/Game/EL/ART/FX/Niagara/System/PC/Sword/FX_S_SwordTrail07.FX_S_SwordTrail07` score `19.35`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_SwordTrail_Y011, /Game/EL/ART/FX/Materials/MI/FX_MI_SwordTrail_Y012, /Game/EL/ART/FX/Materials/MI/FX_M_SwordTrail_Y001

### uncategorized
- `/Game/EL/ART/FX/Niagara/System/SQ/P0020/FX_S_SEQ_Compass02.FX_S_SEQ_Compass02` score `42.6`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_AuraHelix_Y061, /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_Y007, /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_Y018
- `/Game/EL/ART/FX/Niagara/System/Monster/LowEist_Guard/FX_S_LowEist_Guard_Teleport02.FX_S_LowEist_Guard_Teleport02` score `41.95`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Aura_Y027, /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_J011, /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_K014
- `/Game/EL/ART/FX/Niagara/System/Common/Doodad/FX_S_AetherCore01.FX_S_AetherCore01` score `40.7`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_AuraSphere_Y005, /Game/EL/ART/FX/Materials/MI/FX_MI_AuraSphere_Y006, /Game/EL/ART/FX/Materials/MI/FX_MI_AuraSphere_Y008
- `/Game/EL/ART/FX/Niagara/System/Monster/Tark/FX_S_Tark_Shocwave01.FX_S_Tark_Shocwave01` score `39.1`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Crack_Y011, /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_J009, /Game/EL/ART/FX/Materials/MI/FX_MI_HitRef_J001
- `/Game/EL/ART/FX/Niagara/System/Monster/Tark/FX_S_Tark_AtkJump01_02.FX_S_Tark_AtkJump01_02` score `35.2`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Crack_Y010, /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_J009, /Game/EL/ART/FX/Materials/MI/FX_MI_HitRef_J001
- `/Game/EL/ART/FX/Niagara/System/Monster/Tark/FX_S_TarkDie01.FX_S_TarkDie01` score `33.65`; material: /Game/EL/ART/FX/Materials/M/FX_M_BloodParticle01, /Game/EL/ART/FX/Materials/MI/FX_MI_BloodRibbon_Y0001, /Game/EL/ART/FX/Materials/MI/FX_MI_DecalBlood_Y001
- `/Game/EL/ART/FX/Niagara/System/Monster/ForestmushroomBubblekeeper/FX_S_ForestmushroomBubblekeeper_Spawn01.FX_S_ForestmushroomBubblekeeper_Spawn01` score `33.6`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_AuraHelix_Y003, /Game/EL/ART/FX/Materials/MI/FX_MI_AuraHelix_Y005, /Game/EL/ART/FX/Materials/MI/FX_MI_GBufferColor01_Y001
- `/Game/EL/ART/FX/Niagara/System/Monster/Mouse/FX_S_Mouse_Spawn01.FX_S_Mouse_Spawn01` score `33.35`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_GBufferColor01_Y001, /Game/EL/ART/FX/Materials/MI/FX_MI_HitRef_Y003, /Game/EL/ART/FX/Materials/MI/FX_MI_Ribbon_K004

### weather_rain_snow
- `/Game/UltraDynamicSky/Particles/WeatherOcclusionVolumeSystem.WeatherOcclusionVolumeSystem` score `37.15`; material: indexed material ??
- `/Game/EL/ART/FX/Niagara/System/Monster/Aster/FX_Aster_S_Storm_01.FX_Aster_S_Storm_01` score `22.4`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Glow_J014_depth, /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J002, /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J003
- `/Game/EL/ART/FX/Niagara/System/Monster/Aster/FX_Aster_S_Storm_01_Temp.FX_Aster_S_Storm_01_Temp` score `21.9`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Fog_J001, /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J002, /Game/EL/ART/FX/Materials/MI/FX_MI_Lightning_J003
- `/Game/UltraDynamicSky/Particles/Rain.Rain` score `21.8`; material: /Game/UltraDynamicSky/Materials/Weather/Rain_ParticleMat, /Game/UltraDynamicSky/Materials/Weather/Rain_Ripple_Decal, /Game/UltraDynamicSky/Materials/Weather/Rain_Spot_Decal
- `/Game/UltraDynamicSky/Particles/Radial_Storm.Radial_Storm` score `20.95`; material: /Game/UltraDynamicSky/Materials/Weather/LightningFlare_ParticleMat_Obscured, /Game/UltraDynamicSky/Materials/Weather/Lightning_Glow, /Game/UltraDynamicSky/Materials/Weather/Lightning_Rainfall_Particle
- `/Game/EL/ART/FX/Niagara/System/SQ/P0040/FX_S_SEQ_P0040_Water01.FX_S_SEQ_P0040_Water01` score `19.85`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_HitRef_Y005, /Game/EL/ART/FX/Materials/MI/FX_MI_Water_J002, /Game/EL/ART/FX/Materials/MI/FX_MI_Water_K005
- `/Game/EL/ART/FX/Niagara/System/SQ/CedarForest_Burst_Step100/FX_S_SQ_WaterSplash05.FX_S_SQ_WaterSplash05` score `18.95`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Water_K003, /Game/EL/ART/FX/Materials/MI/FX_MI_Water_K005, /Game/EL/ART/FX/Materials/MI/FX_MI_Water_K009
- `/Game/EL/ART/FX/Niagara/System/Common/FX_S_FootStep_Water02.FX_S_FootStep_Water02` score `18.3`; material: /Game/EL/ART/FX/Materials/MI/FX_MI_Water_K003, /Game/EL/ART/FX/Materials/MI/FX_MI_Water_K005, /Game/EL/ART/FX/Materials/MI/FX_MI_Water_K006

## ?? ??
- `niagara_asset_index.json`: ?? 719? Niagara ?? ??? ??? ???
- `niagara_generation_index.json`: ??? ????? ???/???/???? ??? ???? ???
- `dependency-chunks/*.json`: ??? ?? ?? ??
- `niagara_temp_copy_report.json`: ?? ?? ??
