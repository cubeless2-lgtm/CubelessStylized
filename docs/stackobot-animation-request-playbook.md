# StackOBot Animation Request Playbook

Use this playbook when the user asks for a specific animation part to be created,
changed, tested, or explained. It turns the learned StackOBot grammar into an
execution protocol.

Related docs:

- `docs/stackobot-animbp-authoring-patterns.md`
- `docs/stackobot-animation-execution-map.md`
- `docs/stackobot-animation-study.md`

## Default Rule

Start sample-only unless the user explicitly approves original asset mutation.

Default target paths:

- Sample content root: `/Game/_MCP_Sample/AnimStudy`
- Evidence root: `D:/Git/SampleProject/StackOBot/Saved/MCP/AnimStudy`
- Reference project: `D:/Git/SampleProject/StackOBot`

Do not edit original StackOBot assets for a first pass. Use original assets as
reference inputs and duplicate or create safe sample variants.

## Intake

For every request, extract these fields before doing asset work:

| Field | Meaning | Example |
| --- | --- | --- |
| Target character | Which skeleton/mesh/AnimBP owns the behavior | Bot, Baddy |
| Body area | Bone chain or system affected | head, antenna, foot IK, upper body |
| Timing type | Static offset, state change, continuous axis, overlay, physics response | head yaw, run lean, jump transition |
| Runtime layer | Main AnimBP, ControlRig, Post Process AnimBP, physics node | Post Process ModifyBone |
| Authoring target | Sample-only, original asset, or project implementation | `/Game/_MCP_Sample/AnimStudy` |
| Verification depth | Compile/load only, runtime smoke, same-instance PoseWatch | PoseWatch pre/post |
| Approval state | Whether original assets or non-exception C++ are approved | sample-only by default |

If the request is vague, choose the narrowest reversible sample-only path and record
the assumption. Ask only when the choice could mutate original assets, require
non-exception C++, or materially change the intended visual result.

## Classification Matrix

| Request wording | Route | First sample action | Proof |
| --- | --- | --- | --- |
| "make the head turn/look/tilt after animation" | Post Process AnimBP | `ensure_postprocess_anim_demo_variant` | no-SIE or SIE PoseWatch on ModifyBone |
| "make antenna wobble/follow/lag" | Post Process AnimBP physics | `ensure_anim_graph_trail_demo` or ModifyBone sample | PoseWatch on Trail/ModifyBone |
| "make idle/walk/run/jump/hover transition" | Main AnimBP state machine | inspect first; sample graph only if tooling exists | `inspect_anim_state_machine_transitions`, runtime state response |
| "change speed/lean response" | BlendSpace | inspect source sample map; sample grid | `sample_blendspace_runtime_pose_grid` |
| "upper body action over movement" | Slot/layered blend | inspect slot/cached pose/branch filters | all-input PoseWatch on LayeredBoneBlend |
| "foot placement/IK interaction" | ControlRig | forced-driver sample if gameplay gate is inactive | direct ControlRig probe plus AnimGraph PoseWatch |
| "physics jiggle/secondary body motion" | RigidBody/Trail | use Baddy RigidBody or Bot Trail sample | compiled mapping plus PoseWatch |
| "which node caused this?" | Instrumentation | no asset edit; target node resolver first | `sample_anim_node_pre_post_runtime_pose` |

## Execution Protocol

1. Classify the request with the matrix above.
2. State the target route in a `티브렛에게 전달할 지시` block before asset work.
3. Confirm the target is sample-only unless the user approved original asset edits.
4. Run static topology or existing evidence first.
5. Create or modify the sample using the narrowest existing MCP command.
6. Compile/save sample assets only when the route is an authoring command.
7. Verify runtime behavior with the cheapest reliable proof:
   - Post Process static ModifyBone: editor-world no-SIE PoseWatch is acceptable.
   - Physics, state machine, BlendSpace, gameplay-driven gates: prefer SIE/PIE.
   - Multi-input blend: use all-input PoseWatch.
8. Write artifacts under `Saved/MCP/AnimStudy`.
9. Check dirty packages and never save dirty original maps just to clean up a proof actor.
10. Update Cubeless docs/work-log, then commit only relevant docs or tooling files.

## Known Safe Routes

### Post Process ModifyBone

Best current route for a static late bone correction:

1. Create sample variant with `ensure_postprocess_anim_demo_variant`.
2. Confirm target SkeletalMesh points to the generated Post Process AnimBlueprint.
3. Spawn an editor-world transient actor without SIE if the proof is static.
4. Set main `ABP_Bot_C` and explicit component-level Post Process override.
5. Run:

```text
sample_anim_node_pre_post_runtime_pose(
  mode=pose_watch_capture,
  anim_instance_source=post_process,
  prefer_pie_world=false,
  require_pie_world=false
)
```

Evidence: `HeadYawAuthoringPattern` uses this route. It proved `head` yaw `8.0 deg`,
antenna leaf movement about `11.74 cm`, `runtime_graph_prepost=true`, and
`same_instance_prepost=true` without starting SIE.

### ControlRig

Best current route when gameplay gates do not fire naturally:

1. Inspect topology with `inspect_anim_graph_protected_topology`.
2. Use `controlrig_direct_gate_probe` to identify required curve/input gates.
3. Create or reuse the forced-driver sample through `ensure_controlrig_forced_driver_animbp`.
4. Verify with `sample_anim_node_pre_post_runtime_pose(mode=pose_watch_capture)`.

Evidence: `_MCP_Sample` `ABP_Bot_ControlRig_ForcedDriver_Study` proved same-instance
ControlRig pre/post with output link `42` and input `Source` link `45`.

### BlendSpace

Best current route for axis-driven animation:

1. Inspect the source pose map and authored sample coordinates.
2. Use `sample_blendspace_runtime_pose_grid`.
3. Interpret deltas as controlled tooling evidence, not exact match to older async SIE artifacts.

### Physics

Best current route for secondary motion:

1. Prefer existing Baddy RigidBody or Bot Trail samples.
2. Use compiled mapping to prove the live node maps to the selected editor node.
3. Use PoseWatch capture for exact same-instance input/output proof.

## Approval Gates

Proceed without asking again:

- Reading StackOBot/Cubeless/UnrealMCP code and docs.
- Creating or updating Cubeless documentation.
- Creating or modifying C++ inside the UnrealMCP plugin when justified by MCP tooling.
- Creating or modifying disposable sample assets under `/Game/_MCP_Sample/AnimStudy`.

Ask or require explicit approval:

- Modifying original StackOBot assets outside `_MCP_Sample`.
- Modifying Cubeless project gameplay/runtime C++ outside approved plugin exceptions.
- Saving original maps that became dirty during transient proof actor cleanup.
- Using billed/API routes, credentials, or non-local services.
- Promoting sample assets into production content.

## C++/API Escalation

Keep C++ as a candidate only when an existing MCP command cannot safely create,
wire, inspect, or verify the requested graph.

Escalate to UnrealMCP C++ when:

- Python wrappers cannot access required AnimGraph internals.
- Generic `execute_python` would need unsafe map switching, SIE setup, or protected pin edits.
- The requested proof needs reusable same-instance runtime instrumentation.
- A repeated manual setup pattern can be made safer as a native command.

Do not escalate when:

- Existing commands already cover the request.
- A sample-only asset can be created and verified with current commands.
- The only missing work is documentation or artifact summarization.

## Failure Handling

If a validation route fails, classify the failure before changing the plan:

| Failure | Interpretation | Next action |
| --- | --- | --- |
| Compile error | Sample graph invalid | Fix sample graph or command parameters |
| Dirty map after spawn/delete | Reversible proof actor dirtied map | Do not save; close editor externally |
| Python wrapper method missing | Wrapper exposure gap | Let C++ command handle tick/read path |
| SIE setup crash | Unsafe setup route | Avoid repeating; use no-SIE proof or native setup |
| No pose delta | Could be real behavior or inactive gate | Check topology, curves, runtime state, and input gates |
| No matching actor/AnimInstance | Runtime target setup issue | Recreate transient target or use a native command |

## Delivery Shape

When finishing a requested animation part, report:

- Asset paths created or modified.
- Whether originals were untouched.
- The exact authoring route.
- Compile/save result.
- Runtime proof result and key deltas.
- Artifact paths.
- Dirty package result.
- Residual risk or blocked route, if any.

