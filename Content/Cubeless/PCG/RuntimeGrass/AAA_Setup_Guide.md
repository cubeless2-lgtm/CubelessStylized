# PCG AAA — RuntimeGrass 설정 가이드

## 개요
- **에셋 위치**: `/Game/Cubeless/PCG/RuntimeGrass/AAA` (PCGGraph)
- **방식**: GPU Compute Shader (HLSL) → PCG Points → HISM Spawner
- **최적화**: Grid+Jitter 배치 / 경사도 컬링 / LOD Density Falloff / Nanite 지원

---

## 1. 에디터에서 PCG Graph "AAA" 생성

1. **Content Browser** → `/Game/Cubeless/PCG/RuntimeGrass/`
2. 우클릭 → **Procedural Generation** → **PCG Graph**
3. 이름: `AAA`

---

## 2. PCG Graph 노드 구성

```
[Landscape Spline] 또는 [Get Actor Data (ALandscape)]
        ↓
[Surface Sampler]  ← GridSize: 50, Density: 1.0
        ↓
[Custom HLSL Node] ← 아래 HLSL 코드 붙여넣기
        ↓
[Density Filter]   ← Min: 0.1
        ↓
[Transform Points] ← Random Rotation Y / Scale Variation
        ↓
[Static Mesh Spawner] ← 잔디 메시 + LOD 설정
```

### 필수 노드 설정

#### Surface Sampler
| 파라미터 | 값 |
|----------|-----|
| Point Extents | 25 (= GridCellSize/2) |
| Looseness | 0 |
| Apply Mesh Bounds Attribute | Off |

#### Custom HLSL Node (PCG Graph 내부)
```hlsl
// AAA Grass — Custom HLSL Filter
// Input: Point (Position, Normal)
// Output: Density (float)

float3 Normal = InPoint.Normal;
float SlopeAngle = degrees(acos(saturate(dot(Normal, float3(0,0,1)))));

// 경사도 35도 이상 제거
if (SlopeAngle > 35.0)
    return 0.0;

// 물 높이 이하 제거  
if (InPoint.Position.z < WaterHeight)
    return 0.0;

// 거리 기반 밀도 감소 (LOD)
float DistToCam = length(InPoint.Position - CameraPosition);
float LODFactor = 1.0 - saturate((DistToCam - 2000.0) / 8000.0);

// 노이즈 기반 밀도 변화
float2 UV = InPoint.Position.xy * 0.001;
float NoiseVal = frac(sin(dot(UV, float2(127.1, 311.7))) * 43758.5453);

return LODFactor * NoiseVal;
```

#### Density Filter
| 파라미터 | 값 |
|----------|-----|
| Lower Bound | 0.05 |
| Upper Bound | 1.0 |

#### Static Mesh Spawner
| 파라미터 | 값 |
|----------|-----|
| Descriptor 0 — Mesh | 잔디 메시 (SM_Grass_01 등) |
| Descriptor 0 — Weight | 0.7 |
| Descriptor 1 — Mesh | 꽃/잡초 메시 |
| Descriptor 1 — Weight | 0.3 |
| Component Type | Hierarchical Instanced Static Mesh |
| Cast Shadow | Off (잔디) |
| Cull Distance | Min: 100, Max: 3000 |

---

## 3. C++ 커스텀 노드 사용 (고급, GPU 경로)

1. 프로젝트 빌드 후 에디터 재시작
2. PCG Graph에서 우클릭 → `AAAGrassSpawn (HLSL)` 노드 추가
3. Details 패널에서 `UPCGAAAGrassSettings` 파라미터 조정:
   - **Grid Cell Size**: 50 (기본, 낮출수록 조밀)
   - **Jitter Scale**: 0.8
   - **Global Density Scale**: 0.6~1.0
   - **Slope Max Angle**: 35°
   - **LOD Max Distance**: 10000
   - **Use GPU Dispatch**: ✅

---

## 4. PCG Volume Actor 설정

1. 레벨에 **PCG Volume** Actor 배치
2. `PCG Graph` = `AAA`
3. **Generate on Load**: ✅
4. **Is Partitioned**: ✅ (대형 맵용 — Runtime Grid 활성화)
5. Grid Size: 25600 (=256m 파티션)

---

## 5. 최적화 체크리스트

| 항목 | 설정값 | 이유 |
|------|--------|------|
| Nanite | On (SM_Grass에서) | 잔디 드로콜 대폭 감소 |
| WPO Bounds | z: +50 | 바람 애니메이션 컬링 오류 방지 |
| Cast Shadow | Off | 잔디 그림자 비용 절감 |
| Cull Distance Volume | 레벨 전체 커버 | 원거리 인스턴스 제거 |
| PCG Partitioned Grid | 256m | 카메라 주변만 동적 생성 |
| HISM vs FOLIAGE | HISM 권장 | PCG에서는 HISM이 더 안정적 |
| LOD 0 | 고폴리 | 3m 이내 |
| LOD 1 | 빌보드 | 3~30m |
| LOD 2 | 컬 | 30m 이상 |

---

## 6. 파일 구조

```
D:\Git\Cubeless_AI\
├── Shaders\
│   └── PCGGrassDistribution.usf       ← GPU Compute HLSL
├── Source\Cubeless_AI\PCG\
│   ├── PCGGrassSpawnElement.h          ← C++ PCG 커스텀 노드 헤더
│   └── PCGGrassSpawnElement.cpp        ← C++ PCG 커스텀 노드 구현
└── Content\Cubeless\PCG\RuntimeGrass\
    └── AAA.uasset                      ← 에디터에서 생성한 PCG Graph
```
