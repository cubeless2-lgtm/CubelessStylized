# StackOBot Animation Request Run Examples

Use these dry-run examples with
`docs/stackobot-animation-request-run-template.md`. They are not execution
results. They show how to fill the record before Tivret touches assets.

## Example 1: Bot Head Yaw

```text
user_request:
Bot head should look 5 degrees to the right after the main animation.

target_character: Bot
target_body_area: head
timing_type: static late additive rotation
runtime_layer: Post Process AnimBP
route: Post Process ModifyBone sample
sample_target:
/Game/_MCP_Sample/AnimStudy/ABP_Bot_PostProcess_Study_HeadYawRight5
first_read_or_authoring_command:
ensure_postprocess_anim_demo_variant
verification_command:
sample_anim_node_pre_post_runtime_pose(mode=pose_watch_capture,
anim_instance_source=post_process, prefer_pie_world=false)
expected_evidence:
runtime_graph_prepost=true, same_instance_prepost=true, head yaw about 5 degrees
handoff_template:
Post Process ModifyBone
cxx_api_status:
not needed
ask_user_first:
false
```

Acceptance focus:

- sample Post Process AnimBP compiles;
- sample SkeletalMesh uses the sample Post Process AnimBP;
- PoseWatch samples the Post Process instance, not only the main AnimInstance;
- original `ABP_Bot`, `SKM_Bot`, and maps remain untouched.

## Example 2: Wider Run Lean

```text
user_request:
Make Bot run lean wider left and right.

target_character: Bot
target_body_area: locomotion body response
timing_type: continuous BlendSpace axis response
runtime_layer: main AnimBP source BlendSpace
route: BlendSpace sample variant
sample_target:
/Game/_MCP_Sample/AnimStudy/BS_Bot_WalkRunLean_LeanWideRequest
first_read_or_authoring_command:
ensure_blendspace_sample_variant
verification_command:
sample_blendspace_runtime_pose_grid
expected_evidence:
valid_pose_count matches the requested grid and input_changed_pose=true
handoff_template:
BlendSpace Sample Variant
cxx_api_status:
not needed
ask_user_first:
false
```

Acceptance focus:

- original `BS_Bot_WalkRunLean` is read-only;
- edited sample coordinates are explicit;
- pose grid compares center, lean-left, and lean-right inputs;
- deltas are treated as controlled evidence, not exact visual approval.

## Example 3: Antenna Lag

```text
user_request:
Make the Bot antenna lag behind movement.

target_character: Bot
target_body_area: antenna_04_l chain, mirrored only if requested
timing_type: secondary motion / follow-through
runtime_layer: Post Process AnimBP physics-style node
route: Bot Trail sample
sample_target:
/Game/_MCP_Sample/AnimStudy/ABP_Bot_Trail_Study
first_read_or_authoring_command:
ensure_anim_graph_trail_demo or reuse existing sample
verification_command:
sample_anim_node_pre_post_runtime_pose(mode=pose_watch_capture,
anim_instance_source=post_process, prefer_pie_world=true)
expected_evidence:
same-instance Trail input/output and target chain delta in SIE/PIE
handoff_template:
Trail Or Secondary Motion
cxx_api_status:
not needed for current Trail sample
ask_user_first:
false
```

Acceptance focus:

- do not reactivate the disconnected original `ABP_Bot` Trail node;
- proof actor uses component-level Post Process override;
- moving physics-style proof prefers SIE/PIE;
- static editor tick alone is not final proof for moving lag behavior.

## Example 4: Upper Body While Moving

```text
user_request:
Play an upper-body action while locomotion continues.

target_character: Bot
target_body_area: upper body
timing_type: overlay action over locomotion
runtime_layer: Slot / LayeredBoneBlend in main AnimBP
route: existing UpperBody Slot and LayeredBlend route proof
sample_target:
none for route proof; future sample overlay only if action source is required
first_read_or_authoring_command:
slot/cached-pose inventory, then all-input PoseWatch
verification_command:
sample_anim_node_pre_post_runtime_pose(mode=pose_watch_capture,
input_pose_mode=all)
expected_evidence:
BasePose from LocomotionPose and BlendPoses[0] from CashedPose_UpperBody in the same AnimInstance
handoff_template:
UpperBody Slot And LayeredBlend
cxx_api_status:
candidate only if a new visible action source or overlay branch is required
ask_user_first:
false for route proof, true before original asset mutation
```

Acceptance focus:

- near-zero pose delta is only route proof when no action source is played;
- do not report visible action proof unless an action source actually runs;
- a new overlay/action source may trigger `ensure_layered_slot_overlay_sample`;
- original `ABP_Bot` graph editing still requires explicit approval.

## Example 5: Notify Or Montage Timing

```text
user_request:
Read the notify timing for this action and align another event to it.

target_character: Bot or Baddy, depending on the named asset
target_body_area: animation source metadata
timing_type: notify / curve / sync marker / Montage metadata
runtime_layer: animation asset metadata, not pose graph
route: protected metadata boundary
sample_target:
none until a guarded native API is approved/implemented
first_read_or_authoring_command:
safe animation asset inventory and AssetRegistry-level scan only
verification_command:
none for protected internals with current tooling
expected_evidence:
clear report of readable fields and blocked protected fields
handoff_template:
Notify, Curve, Sync Marker, Or Montage Internals
cxx_api_status:
candidate guarded native API for concrete metadata requests
ask_user_first:
true before implementing or using new guarded native API
```

Acceptance focus:

- do not broad-probe Montage internals with generic Python;
- do not guess protected notify, curve, or sync-marker data;
- if safe inventory is insufficient, stop and park the guarded API candidate;
- mention the known `AnimMontage.h:770` crash boundary.
