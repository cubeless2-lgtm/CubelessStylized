import unreal

def duplicate_level_to_new_folder(original_level_path, destination_folder, new_level_name):
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    original_level_name = original_level_path.split("/")[-1]
    original_folder_path = original_level_path.rsplit("/", 1)[0]

    # 복사 실행
    new_level_path = f"{destination_folder}/{new_level_name}"
    duplicated_asset = asset_tools.duplicate_asset(
        asset_name=new_level_name,
        package_path=destination_folder,
        original_object=unreal.EditorAssetLibrary.load_asset(original_level_path)
    )

    if not duplicated_asset:
        unreal.log_error(f"레벨 복제 실패: {original_level_path}")
        return

    unreal.log(f"✅ 레벨 복사 성공: {new_level_path}")

    # 리디렉터 정리
    fix_redirectors_in_folder(destination_folder)

    # 복사한 레벨 열기
    if unreal.EditorAssetLibrary.does_asset_exist(new_level_path):  
        unreal.EditorLevelLibrary.load_level(new_level_path)
        unreal.log(f"📂 복사된 레벨 열기 완료: {new_level_path}")
    else:
        unreal.log_error("복사된 레벨 열기 실패!")

def fix_redirectors_in_folder(folder_path):
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    redirectors = asset_registry.get_assets_by_path(folder_path, recursive=True)

    redirector_paths = [r.object_path for r in redirectors if r.asset_class == "Redirector"]
    if redirector_paths:
        unreal.EditorAssetLibrary.fixup_redirectors(folder_path)
        unreal.log("🔧 리디렉터 정리 완료")
    else:
        unreal.log("ℹ️ 리디렉터 없음")

# # ✅ 복사 실행 예제
# original_level = "/Game/EL/Maps/EL_Proto_04/EL_Proto_04"
# destination_folder = "/Game/EL/Maps/EL_World_01"
# new_level_name = "EL_World_01"

# duplicate_level_to_new_folder(original_level, destination_folder, new_level_name)