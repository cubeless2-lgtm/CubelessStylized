import unreal

# 설정값: True면 Spatially Loaded 켜기, False면 끄기
SPATIALLY_LOADED = True

# 필터에 사용할 접두사 목록
prefixes = ["BPP_", "SM_", "AP_", "Forest_Side_Rock", "Forest_Rock", "BP_RedWoodForest", "S_Huge_Nordic", "GroupActor"]

# Editor Actor Subsystem을 통해 현재 레벨의 모든 액터 가져오기
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
all_actors = actor_subsystem.get_all_level_actors()
all_actors_count = len(all_actors)

# 아웃라이너의 특정 폴더 경로
target_folder = ""  # 아웃라이너에서의 폴더 경로

# for actor in all_actors:
#     # 액터의 이름을 로그에 출력
#     actor_name = actor.get_name()
#     unreal.log(f"액터 이름: {actor_name}")

# 접두사에 따라 필터링
# filtered_actors = [actor for actor in all_actors if actor.get_folder_path() == target_folder and 
#                    any(actor.get_actor_label().startswith(prefix) for prefix in prefixes)]
filtered_actors = [actor for actor in all_actors if any(actor.get_actor_label().startswith(prefix) for prefix in prefixes)]
filtered_actors_count = len(filtered_actors)

# 필터링된 액터를 에디터에서 선택된 상태로 설정
actor_subsystem.set_selected_level_actors(filtered_actors)

modified_count = 0

for actor in filtered_actors:
    if not actor.get_editor_property("is_spatially_loaded"):
        actor.set_editor_property("is_spatially_loaded", SPATIALLY_LOADED)
        modified_count += 1
    # try:
    #     actor.set_editor_property('bIsSpatiallyLoaded', SPATIALLY_LOADED)
    #     modified_count += 1
    # except Exception as e:
    #     # bIsSpatiallyLoaded 프로퍼티가 없는 액터는 무시
    #     continue

unreal.log(f"[Spatial Load 설정] 총 {all_actors_count}개의 액터에 중에 [SM_, BPP_] 이름을 가진 액터는 총 {filtered_actors_count}개 입니다.")
unreal.log(f"[Spatial Load 설정] 총 {modified_count}개의 액터에 대해 'Is Spatially Loaded'를 {SPATIALLY_LOADED}로 설정했습니다.")
