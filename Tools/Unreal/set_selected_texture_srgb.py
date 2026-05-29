import unreal


TARGET_SRGB = False


def set_selected_texture_srgb(target_srgb):
    selected_assets = list(unreal.EditorUtilityLibrary.get_selected_assets())
    changed = []
    already_set = []
    skipped = []
    errors = []
    verified = []

    for asset in selected_assets:
        path = asset.get_path_name()
        if not isinstance(asset, unreal.Texture):
            skipped.append(path)
            continue

        prop_name = None
        current_value = None
        for candidate in ("srgb", "sRGB", "SRGB"):
            try:
                current_value = asset.get_editor_property(candidate)
                prop_name = candidate
                break
            except Exception:
                pass

        if prop_name is None:
            errors.append(f"{path}: sRGB property not found")
            continue

        try:
            if current_value != target_srgb:
                asset.modify()
                asset.set_editor_property(prop_name, target_srgb)
                unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
                changed.append(path)
            else:
                unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
                already_set.append(path)

            final_value = asset.get_editor_property(prop_name)
            if final_value == target_srgb:
                verified.append(path)
            else:
                errors.append(f"{path}: final sRGB value is {final_value}")
        except Exception as exc:
            errors.append(f"{path}: {exc}")

    result = {
        "target_srgb": target_srgb,
        "selected_count": len(selected_assets),
        "texture_count": len(changed) + len(already_set),
        "changed_count": len(changed),
        "already_set_count": len(already_set),
        "skipped_count": len(skipped),
        "verified_count": len(verified),
        "error_count": len(errors),
        "changed": changed,
        "already_set": already_set,
        "skipped": skipped,
        "errors": errors,
    }
    unreal.log("SELECTED_TEXTURE_SRGB_RESULT=" + repr(result))
    return result


set_selected_texture_srgb(TARGET_SRGB)
