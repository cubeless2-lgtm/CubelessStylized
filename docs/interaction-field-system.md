# 통합 인터랙션 필드 시스템 (Interaction Field System) — 설계 문서

> 상태: **설계 검토 대기 (Design Review)** — 구현 착수 전.
> 작성: 2026-06-14. 갱신 주기: 각 Phase 종료 시.
> 원본 계획/이력: `C:\Users\cubel\.claude\plans\snow-eager-pretzel.md` (에이전트 플랜). 본 문서가 레포 영구본.

---

## 1. 목적 (Context)

풀 눕힘 · 눈/모래 발자국(지속 변형) · 물 파장 · 검 궤적/장풍 같은 "월드 상호작용 흔적·효과"를
**제각각이 아니라 하나의 시스템으로 통합 관리**하고, 결과를 **렌더타겟(RT)** 에 기록해
지면·풀·물·VFX 머티리얼이 **공유 샘플**하게 한다.

"모든 효과를 한 장에 다 찍는다"가 목표가 아니라, **매니저 1개가 RT 세트·좌표계·Niagara·MPC를 총괄**하고
효과는 채널/RT로 분리해 **시스템 차원에서 통합 관리**하는 것이 핵심.

---

## 2. 확정 요구사항

- 타깃 **UE 5.7** (DX12 SM6 주력 + 모바일 Vulkan SM6 → GPU Grid2D/컴퓨트 사용 가능).
- 기록은 가능하면 **Niagara(Grid2D) → RT export**.
- **내 플레이어만 찍히면 안 된다** → NDC 브로드캐스트로 어떤 액터(NPC/투사체/프롭)든 흔적 가능.
- 캡처 영역 **두 모드 선택**: (A) 플레이어 폴로우(영역 스크롤), (B) 볼륨 설치(월드 고정).
- **수직 슬라이스로 차근차근**. MVP 1탄 = **눈/모래 발자국(지속 변형)**.
- 지면 **Landscape + Static/Nanite 메시 둘 다** 지원. 눈 쌓임 = **POM**.
- **RVT / VirtualHeightfieldMesh 배제**(모바일 고려). Landscape 변형은 **머티리얼 WPO + POM 전용**.
- **그라운드 판정은 CharacterMovement 비의존**(독립 트레이스 기반, 모바일 우선).
- **C++ 금지**(불가피 시 사유 보고). BP + Niagara + Material + MPC + NDC + RT 로만, 생성/검증은 UnrealMCP.
- **전달물 = 재사용 가능한 플러그인**(가급적 전부 BP, Content-only).
- **멀티플레이는 "대응 방법(설계 지침)"만** — 직접 구현/테스트는 범위 외. 아키텍처가 MP-ready 함만 보장.
- **문서 따로 기록**, 단계마다 갱신.

---

## 3. 아키텍처 개요

```
[BPC_InteractionSource]  (플레이어/NPC/검/투사체 등 아무 액터에 부착)
    │ 자체 그라운드 판정(무브먼트 비의존, 트레이스) → 접지점 산출
    │ NDC write: Position / Velocity / Radius / Strength / Channel / Shape
    ▼
[NDC_Interactors]  (Niagara Data Channel, handler=Global, visible_to_gpu=true)
    ▼
[NS_InteractionField]  (Grid2D_OceanPatch 복제 기반, GPU 지속 시뮬)
    1) NDC Read → 채널별 브러시 스플랫
    2) 채널 시뮬: 변형(max누적+Rim+슬럼프) / 풀(지수감쇠 복원) / 물(파동 핑퐁) / 트레일 지면투영
    3) Grid2D → RenderTarget export
    ▼
[RT 세트]  RT_IF_Deform(RGBA16F 공유) + RT_IF_Water(RG16F 전용) [+RT_IF_Grass 옵션]
    │ 월드 XY → RT UV 매핑 = MPC가 공급
    ▼
[MF_SampleInteractionField]  공용 머티리얼 함수 (월드pos→UV→RT 샘플 + 노멀 재계산)
    ├─ 지면(Static/Nanite, Landscape) : POM 함몰/Rim + WPO/Nanite 변위 + 노멀   ← MVP
    ├─ 풀/그래스 : WPO bend(방향+강도)
    ├─ 물 메시 : height WPO + 노멀 + foam
    └─ 트레일 : VFX 리본 + 머티리얼 마스크 (+지면 B채널)

[BP_InteractionField (매니저)]  좌표계 총괄
    - 모드 enum FollowPlayer / Volume
    - Center / Extent / Resolution 관리, 매 틱 MPC publish
    - BeginPlay에 트랜션트 RT 생성 후 Niagara User 파라미터 바인딩
    - NiagaraComponent(NS_InteractionField) 소유·구동
```

**핵심 설계 결정**
- **좌표 분리**: RT↔월드 변환은 전부 `MPC_InteractionField`로 공급 → 모든 머티리얼이 동일 규칙으로 같은 RT 샘플("통합").
- **입력 = NDC**: 인터랙터가 NDC로 브로드캐스트 → 비플레이어 자동 포함. 폴로우/볼륨은 영역 계산에만 영향, 입력 경로는 공통.
- **효과 = 채널/RT 분리**: 지면계(변형/풀/트레일 지면투영)는 `RT_IF_Deform` 채널 패킹, 물은 의미·감쇠가 달라 전용 `RT_IF_Water`. 공중 검궤적은 RT가 아니라 VFX 리본+마스크.

**콘텐츠 경로 (플러그인 마운트)**: `/InteractionField/` → `/Core /Niagara /Materials /Demo`. 임시 검증만 `/Game/_MCP_Temp/`.

---

## 4. 공통 인프라 계약

### 4.1 Channel enum `E_IF_Channel`
| 값 | 의미 |
|----|------|
| 0 Deform | 눈/모래 파임 (MVP) |
| 1 Grass | 풀 눕힘 |
| 2 Water | 입수 임펄스 |
| 3 Trail | 검궤적/장풍 지면투영 |

### 4.2 렌더타겟
- **`RT_IF_Deform`** (공유, **RGBA16F** — 부호 변위/누적 위해 float 필수)
  | 채널 | 내용 | 효과 |
  |------|------|------|
  | R | 변형 깊이 Depth (함몰) | Deform |
  | G | 가장자리 융기 Rim (눈 둑) | Deform |
  | B | Trail 지면 마스크 | Trail |
  | A | 예약 (Age / Impact / 모바일 스칼라 grass) | - |
- **`RT_IF_Water`** (전용, **RG16F**): R=height(부호), G=velocity. 파동 핑퐁용.
- **`RT_IF_Grass`** (옵션, 데스크탑, **RGBA16F**): RG=BendDir, B=강도. (모바일은 스칼라 bend를 `RT_IF_Deform.A`에 패킹.)
- 해상도: 데스크탑 512~1024², 모바일 256². **트랜션트로 BeginPlay 생성**(플랫폼별 스케일). 저장 RT 에셋은 디버그용만.

> ⚠ **채널 예산 (R1)**: 눈(Depth+Rim=2ch) + 풀 방향bend(dir 2ch+강도 1ch) + 트레일(1ch)은 단일 RT 4채널 초과. → 풀 방향은 전용 `RT_IF_Grass`로 분리, 모바일은 스칼라로 축소. Phase 4에서 최종 확정.

### 4.3 `MPC_InteractionField` (Material Parameter Collection)
| 파라미터 | 타입 | 의미 |
|----------|------|------|
| FieldCenter | Vector | 캡처 영역 월드 중심 |
| FieldSize | Vector | xy=가로/세로 크기(cm), z=HeightScale |
| FieldInvSize | Vector | 1/Size 사전계산(머티리얼 division 회피) |
| HeightScale | Scalar | RT 값(0~1) → 월드 변위(cm) |
| FieldFalloff | Scalar | 가장자리 페이드 |
| FieldEnabled | Scalar | 글로벌 토글 0/1 |
| FieldRotation | Scalar | 예약(MVP=0, 회전 미고려) |

월드→UV: `uv = (WorldPos.xy - FieldCenter.xy) * FieldInvSize.xy + 0.5`. (V-flip 방향은 디버그 RT로 검증.)

### 4.4 `NDC_Interactors` (Niagara Data Channel)
페이로드: `Position`(WS) · `Velocity`(WS) · `Radius`(cm) · `Strength` · `Channel`(E_IF_Channel) · `Shape`(0 Sphere/1 Capsule/2 Cone). handler=Global, visible_to_gpu=true.

### 4.5 필드 정책 (확정)
**글로벌 MPC 1세트 + 활성 필드 1개**(R7). 기본 `FieldWorldSize` = **30~40m**(넓게·저밀도, R5). 동시 다중 볼륨 불필요(여러 개 있어도 가장 가까운/우선 1개만 활성).

---

## 5. 단계별 구현 로드맵

각 단계는 독립 검증 가능. 각 Phase 종료 시 본 문서 §10 진행 로그 갱신.

### Phase P — 준비/실현가능성 선검증 (구현 전 필수)
MCP 실측으로 폴백을 못박는다.
1. `Grid2D_OceanPatch` 전체 구조 덤프(SimStage 개수/iteration 소스/Grid2D 해상도 바인딩/RT export).
2. OceanPatch `/Game/_MCP_Temp/` 복제 1회 시험.
3. **NDC Read 최소 모듈 1건 에디터 수동 제작** (유일한 100% 수동 지점, 복제 소스로 박제).
4. 임시 BP에서 `NiagaraDataChannelWriter.write_position` 콜노드 핀 스모크.
5. 라플라시안/감쇠/diffusion 식을 Material Custom 노드로 뺄지 vs Niagara 복제로 끝낼지 결정.
6. 플러그인 자기완결 vs WaterAdvanced 의존 결정(§9 (a)/(b)).
→ 결과를 §10 "실현가능성 확정" 표로 기록.

### Phase 0 — 문서화 + 플러그인 스캐폴드
본 문서 + `docs/work-log.md` 착수 기록 + `InteractionField` 플러그인 스캐폴드(.uplugin Content-only) + `/InteractionField/` 폴더.

### Phase 1 — 좌표계 골격 (RT 매핑 검증)
`MPC_InteractionField` · `RT_IF_Deform` · `BP_InteractionField`(두 모드, MPC publish) · `MF_SampleInteractionField` 초안 → 디버그 점 1개로 **월드↔UV 정합** 두 모드 검증.

### Phase 2 — Niagara 시뮬 + NDC 주입 ★크리티컬 패스★
`NDC_Interactors` · `BPC_InteractionSource`(자체 그라운드 판정) · `NS_InteractionField`(OceanPatch 복제) · NDC Read 모듈 삽입 · Grid2D→RT export. **비플레이어 흔적도 RT에 찍히는지** 검증.
- 폴백: 복제·NDC Read 막히면 SceneCapture+머티리얼 누적 RT, 또는 `NS_Reactive_RTTexturePainter` 패턴.

### Phase 3 — 눈/모래 발자국 + POM ★MVP★  (세부 §6.A)
### Phase 4 — 풀 눕힘  (세부 §6.B)
### Phase 5 — 물 파장  (세부 §6.C)
### Phase 6 — 검 궤적/장풍  (세부 §6.D)
### Phase 7 — 폴로우 스크롤 영속성 + 최적화 + 모바일 + 플러그인 마감
- 폴로우 toroidal grid(Center 셀 스냅, 진입 가장자리만 클리어). Grid2D wrap 미지원 시 가장자리 decay.
- RT 해상도/포맷/빈도/LOD/토글, 모바일 Vulkan SM6 프로파일.
- 플러그인 자기완결성·의존성·셋업 가이드 마감.
- (MP 구현 안 함) §7 지침과 충돌 없는지 점검만.

---

## 6. 효과별 세부 구현

### 6.A 눈/모래 발자국 (지속 변형) + POM
**시뮬 (Grid2D)**: 셀당 `Depth`/`Rim`/(`Age`). 브러시 `Strength*smoothstep(1,0,dist/Radius)`.
- 함몰 = `Depth = max(Depth_prev, brush)` (감산식은 무한 심화라 기각).
- 눈: Rim 강(`Rim=max(Rim, ring*RimStrength)`)·가파른 벽·영구(Refill=0).
- 모래: Rim 약·이웃 diffusion 슬럼프(`Depth=lerp(Depth,neighborAvg,SandSlump*dt)`)·느린 Refill.
- 지속 Grid2D는 **매 프레임 클리어 금지**.

**머티리얼**: `M_SilhouettePOM_Custom_dither_shadow_final_fade` **fork → `M_SnowDeformPOM`** (월드UV, SkyAtmosphere 태양 추적, 그레이징 페이드, 셀프섀도우, PDO 보유. → `docs/silhouette-pom-research.md`).
- `H_final = saturate(H_base − Depth*CarveDepthScale + Rim*RimHeightScale)`.
- **FeatureLevelSwitch 분기(R4)**: 데스크탑=POM 루프 내 합성 / **모바일=POM 패스 통째 우회 → RT 노멀+얕은 WPO만**.
- 노멀: MF 출력 우선, Rim 프레넬 하이라이트, 함몰 AO(`1-Depth*AOStrength`).
- 신규 파라미터: CarveDepthScale / RimHeightScale / UseDeformRT.

**지면 두 경로**:
- Static/Nanite: 데스크탑=Nanite displacement(눈두께·실루엣)+POM(디테일)[5.7 동적 RT displacement 검증], 모바일=얕은 WPO+노멀.
- Landscape: **머티리얼 WPO(Depth)+POM 전용**. **RVT/VHM 배제 확정**(모바일).
- 공통 `MF_SampleInteractionField` + MPC 재사용.

### 6.B 풀 눕힘 (감쇠 복원)
- `bend = max(bend*exp(-RestoreRate*dt), stamp)`. 방향 `BendDir`(vec2 Velocity EMA; 모바일 폴백 스칼라).
- RT(R1): 데스크탑=전용 `RT_IF_Grass`(RG=BendDir, B=강도), 모바일=스칼라 bend를 `RT_IF_Deform.A`.
- 머티리얼: 버텍스 높이마스크 `pow(h,k)` × bend강도 × BendDir 로 수평 WPO. stateless(현재 RT만).
- 기존 `MF_EL_Foliage_Interaction_PP2_4Pivots` 핀 구조 검증 후 래핑 검토.

### 6.C 물 파장
- 파동방정식 explicit: `acc=(이웃합-4h)*c²; vel=(vel+acc*dt)*Damping; h+=vel*dt`. **CFL `c²dt²≤0.5`** clamp/substep. 경계 absorb 기본.
- 핑퐁: OceanPatch의 `GetPreviousFloatValue` 패턴 재활용(검증) 또는 Grid2D 2장 스왑.
- 전용 `RT_IF_Water`(RG16F). 입수 임펄스 NDC Channel=Water.
- 표현 **독립 물 메시 1순위**(모바일 안전): height WPO/노멀(ddx,ddy 또는 인접텍셀)/foam(|height|·|vel| 임계).
- UE Water 플러그인 연동 2순위: WaterBody 머티리얼 외부 RT 가산 가능성 검증, WaterExtras Local Waves 충돌 검증, Buoyancy는 RT 못 읽음(시각/물리 분리). **검증 전 WaterBody 머티리얼 수정 금지.**

### 6.D 검 궤적 / 장풍 (공중 트랜션트)
- 공중 3D 궤적은 top-down RT에 높이 소실 → **RT 아님**. 트레일 = Niagara Ribbon/Sprite + 머티리얼 마스크(`UltraVolumetrics/NS_Swing` 복제 기반).
- 지면 닿는 부분만 `RT_IF_Deform.B`. 검=소켓 부착+애님 노티파이 게이트, 투사체=상시. Channel=Trail.
- 소비처: 머티리얼 마스크+VFX 우선, 데칼 보조, (옵션) 지면 Grass cross-splat.

---

## 7. 멀티플레이 대응 방법 (설계 지침 — 직접 구현 안 함)

> MP는 "대응 가능한 방법"만 문서로 남긴다. RPC/복제 노드는 이번에 만들지 않되, 시스템이 이 지침과 충돌하지 않게(MP-ready) 설계한다.

**핵심 원칙**: RT/Grid2D는 GPU 로컬 렌더 산출물 → 복제 불가. **시각 결과(RT)가 아니라 흔적의 "원인(인터랙터 이벤트)"을 복제**하고 각 클라가 로컬 NDC→Grid2D→RT로 재생.

| 종류 | 복제 방식 | 근거 |
|------|-----------|------|
| 발자국·풀 눕힘(이동기반) | **복제 안 함**. 각 클라가 영역 내 모든 복제된 폰 순회 → 로컬 NDC write | CharacterMovement가 폰 위치 이미 복제 → RPC 0 |
| 검 궤적·장풍(이벤트성) | 공격/스폰 복제 이벤트에 묶어 Multicast(또는 GAS Gameplay Cue) → 클라 로컬 splat | 이벤트당 1회 Unreliable |
| 물 파장 | 입수 임펄스 이벤트만 Multicast, 전파 시뮬 클라 로컬 | 시각효과(미세 차이 허용) |

- **서버 타입**: 데디 서버 = GPU/RT/Niagara 비활성(`IsDedicatedServer`), 이벤트 권위 중계만. 리슨 서버 = 호스트 로컬 시뮬.
- **결정론**: 픽셀 일치 보장 못 함. 게임플레이상 동일성 필요 시(잠입 단서 등)엔 RT는 표현 전용, 판정용 권위 데이터를 별도 복제 레이어로 분리.
- **두 모드**: 폴로우=클라별 자연 분리, 볼륨=월드 고정(Net Relevancy로 영역 내 폰 복제 확인).
- **검증 필요**: UE5.7 NDC 자체 네트워크 복제 지원 여부 / visible_to_game·gpu 의 네트워크 무관성 / 데디서버 Relevancy. → 확정 전 "NDC 비복제 + 이벤트 복제" 보수 모델 디폴트.

---

## 8. 그라운드 판정 (CharacterMovement 비의존)

흔적 접지 위치를 캡슐 floor(1점)에 기대지 않고 독립 계산. 이유: 발별 위치/경사 노멀 필요, NPC/투사체/프롭도 흔적 가능, 경사·계단 정확도.

`BPC_InteractionSource`가 산출: 접지 월드 XY(Position), 접지 노멀, 접지 여부(planted), 침투 깊이(Strength 가중).

| 방식 | 내용 | 비용 | 용도 |
|------|------|------|------|
| M1 풋본+다운 트레이스 (권장) | 발 본/캡슐 바닥에서 -Z LineTrace/SphereTrace → Hit Location/Normal | 발 2개×스로틀 | 스켈레탈 |
| M2 풋플랜트 노티파이 게이트 (모바일 최적) | FootDown 노티파이 시점에만 트레이스 1회 | 최소 | 정확·저비용 |
| M3 액터 원점 단일 트레이스 | 액터 위치 -Z 1회 | 최저 | 투사체/프롭/NPC |
| M4 비동기 트레이스 | 위들을 AsyncLineTrace | 게임스레드 0 | 모바일 다수 |

- **트레이스 채널(플러그인 이식성)**: 커스텀 채널 `InteractionGround`는 소비 프로젝트 Config라 콘텐츠 플러그인에 못 담음 → **기본은 기존 채널(Visibility/WorldStatic)+오브젝트타입/태그 필터**로 단독 동작. 커스텀 채널은 소비 프로젝트 선택 최적화.
- 출력: Hit이면 Position=HitLocation, Normal=HitNormal, planted=true, Strength*=침투량. Miss(공중)면 publish 스킵.
- **모바일 비용 통제**: 영역 밖 액터 트레이스 안 함, 발당 매프레임 금지(M2 1순위→M1 N프레임+Async), SphereTrace 반경 최소.
- **MP 정합**: 각 클라가 로컬 트레이스(복제 안 함) → §7 "이동기반 로컬 재생"과 일치.
- 검증 필요: 사용 스켈레톤 발 소켓/본 이름, 모바일 AsyncTrace 다수 비용.

---

## 9. 플러그인 패키징 (전달물 형태)

전달물 = 재사용 가능한 **`InteractionField` Content-only(Blueprint) 플러그인** (C++ 불필요 확인됨 → 빌드 의존 없이 활성만으로 추가).

**플러그인에 들어갈 것(자기완결 코어)**: MPC_InteractionField, NDC_Interactors, E_IF_Channel/E_IF_CaptureMode, BP_InteractionField(매니저), BPC_InteractionSource, NS_InteractionField, **MF_SampleInteractionField(소비처가 참조하는 핵심 API)**, 디버그 RT/머티리얼, /Demo 예제.

**자기완결성 제약(중요)**: 플러그인 콘텐츠는 프로젝트 `/Game` 콘텐츠를 참조 불가(참조 방향: 프로젝트→플러그인만).
- **POM 눈 머티리얼은 "소비처"** → 기존 `/Game/AI_Generated/...M_SilhouettePOM...`를 플러그인이 fork 불가. **해결**: 플러그인은 MF + (선택)간단 예제 머티리얼만, **실제 POM fork는 소비 프로젝트에 두고 플러그인 MF 참조**. MVP POM 작업은 `/Game`에서.
- **NS_InteractionField OceanPatch 복제(WaterAdvanced 의존)** → (a) `.uplugin`에 Water/WaterAdvanced 의존 선언(간단·무거움) vs (b) 플러그인 내 자기완결 재구성(재사용성↑·작업량↑). **Phase P에서 결정.**

**소비 프로젝트 셋업 가이드**: ①플러그인 활성 ②(선택)트레이스 채널 정의/기본 채널 ③캐릭터·액터에 BPC_InteractionSource 부착 ④레벨에 BP_InteractionField 배치(볼륨) 또는 폴로우 타깃 지정 ⑤지면 머티리얼에 MF_SampleInteractionField 연결 ⑥플랫폼별 RT 해상도 스케일 확인.

---

## 10. 실측 사실 / 제약 (UE 5.7.4, 추측 아님)

**가능**: Grid2DCollection/Reader/RenderTarget2D DI 존재(SetRenderTargetValue 실측). NDC Asset/Writer/Reader/Library(write_to_niagara_data_channel BP 노출), 핸들러 Global/Islands/GameplayBurst. BP 콜노드로 NDC Writer 체인·Niagara User 파라미터·MPC setter 전부 커버. 모듈 입력값/ RT export 바인딩 자동화 가능.

**막힘(크리티컬)**: 스크래치패드 MCP 인스펙션 전용(Custom HLSL 본문 R/W 불가). Niagara SimulationStage 신규 생성 API 미노출. 시뮬 내 NDC Read DI Python 미노출. 애님 노티파이 트리거 배선 전용 툴 없음.

**게임체인저**: `/WaterAdvanced/Niagara/Systems/Grid2D_OceanPatch`가 Grid2D+SimStage+파동/핑퐁+RT export를 다 보유 → **복제 시드**. NDC Read 모듈만 1회 수동 제작 후 복제.
**결론: C++ 불필요.** 수동 1회성 지점 = ①NDC Read 모듈 ②(필요시)HLSL 식 ③노티파이 배선.

---

## 11. 리스크 (자체 비판 검토)

🔴치명 / 🟠중 / 🟡경.

- **R1 🔴** RT 채널 예산 초과 → 풀 전용 `RT_IF_Grass` 분리/모바일 스칼라. (해소)
- **R2 🔴** Grid2D 스플랫 레이스 컨디션(같은 셀 동시 write의 max 누적) → gather 또는 파티클→RT max 블렌드 렌더. Phase 2에서 확정.
- **R3 🔴** 폴로우 영속성이 필수 모드인데 가장 어렵고 후순위 → Phase 2~3에서 조기 프로토타입으로 가능성 판정. 불가 시 가장자리 decay 윈도우로 스펙 다운.
- **R4 ✅결정** 모바일 POM 제외(노멀+얕은 WPO), POM·Nanite displacement 데스크탑 전용.
- **R5 ✅결정** 넓게·저밀도 30~40m 단일 필드. 발자국 거칠어짐 → 브러시 반경 넉넉히/데스크탑 1024²/머티리얼 디테일 보강.
- **R6 🟠** 런타임 트랜션트 RT(플랫폼별 크기), 저장 에셋 RT는 디버그용만.
- **R7 ✅결정** 단일 활성 필드(글로벌 MPC 1세트).
- **R8 🟠** 틱 순서(NDC write→center publish→sim read) TickGroup 정렬.
- **R9 🟡** WPO 콜리전 비반영+테셀 비용 → MVP 얕은 변형.
- **R10 🟡** 풋플랜트 노티파이 작업량 → M1 트레이스 폴백 상시 구비.
- **R11 🟡** 모래 diffusion 전체 번짐 → 모래만+낮은 rate.
- **R12 🟡** 성능 예산 미정량 → Phase 2 직후 모바일 ms 측정.
- **R13 🟡** 데칼 폴백 인지(발자국 단독 성능 위기 시).

---

## 12. 검증 필요 항목 (구현 중 MCP 실측)

1. NDC Read 모듈/DI 실제 이름·구성 (크리티컬, Phase P).
2. Grid2D→RT export 정확 경로(OceanPatch 재활용).
3. `_MCP_Temp` 복제 동작.
4. BP write_position 콜노드 핀 생성.
5. UV V-flip/grid index 방향.
6. Grid2D Previous-frame read(물 핑퐁).
7. Grid2D diffusion(모래 슬럼프) 안정성.
8. POM 루프 내 RT SampleGrad 모바일 컴파일.
9. 5.7 Nanite 동적 RT displacement(막히면 POM/WPO만).
10. (배제됨) RVT/VHM 미사용. Landscape WPO 변위 모바일 비용/타일 LOD 불연속만 점검.
11. UE Water 머티리얼 외부 RT 가산 + WaterExtras 충돌.
12. 기존 Foliage MF 핀 구조.
13. 폴로우 Grid2D wrap/scroll.
14. UE5.7 NDC 네트워크 복제 특성(MP).
15. 그라운드 판정: 트레이스 채널·발 소켓·모바일 Async 다수 비용.

---

## 13. 기존 자산 활용 결정

- **POM 마스터 fork**: `M_SilhouettePOM_Custom_dither_shadow_final_fade` (사용자 "POM 사용" 명시).
- **Niagara 시드 복제**: `Grid2D_OceanPatch` (SimStage 생성 API 미노출 때문에 사실상 필수).
- **참고만**: `NS_Reactive_RTTexturePainter`, `BP_ReactiveWater*`, `MF_EL_Foliage_Interaction_PP2_*`, `UltraVolumetrics/NS_Swing`. 중복 RT 페인터 공존 시 구자산 deprecate.
- 디폴트: 신규 단일화 + POM fork + OceanPatch 시드 복제.

---

## 14. 진행 로그 (Phase 종료 시 갱신)

| 날짜 | Phase | 결과 / 블로커 |
|------|-------|----------------|
| 2026-06-14 | (설계) | 설계 문서 작성, 검토 대기. 구현 미착수. |

---

## 15. 전체 검증 (E2E)

1. 데모 레벨: Nanite 평면(눈)+Landscape(눈/모래), 캐릭터+더미 NPC.
2. 볼륨 모드(1차): 이동 → 발자국 함몰+Rim, **플레이어·NPC 모두**.
3. 폴로우 전환 → 동작+영역 추종(Phase 7).
4. 각 Phase: Niagara/머티리얼 compile 0, RT PNG export 육안, 전후 캡처, `analyze_*`/`inspect_*` 확인.
5. 모바일 Vulkan SM6 프리뷰 비용/크래시.
6. (MP 구현 안 함) §7 지침과 모순 없는지 설계 검토만.
7. 플러그인 자기완결성: 소비 프로젝트에서 플러그인만 활성+가이드대로 동작 확인.
8. 각 Phase 종료 시 본 문서 §14 갱신.
