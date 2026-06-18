# StackOBot Animation Quickstart

Use this as the first page for future StackOBot animation requests.

## Start Here

1. Confirm the primary bridge is reachable:
   `127.0.0.1:55557`.
2. Compile the user's natural-language request with
   `docs/stackobot-request-compiler-drills.md`.
3. Show the filled `티브렛에게 전달할 지시` block from
   `docs/stackobot-animation-tivret-handoff-templates.md`.
4. Keep the first pass sample-only under `/Game/_MCP_Sample/AnimStudy`.
5. Run the narrowest read or authoring command from
   `docs/stackobot-animation-mcp-command-syntax.md`.
6. Verify with the route-specific gate from
   `docs/stackobot-animation-authoring-templates.md`.
7. Record results in `docs/work-log.md` and commit only relevant docs/tooling.

## Route Shortcuts

| User asks for | Route | First proof |
| --- | --- | --- |
| Head, neck, antenna offset after animation | Post Process ModifyBone | Sample Post Process AnimBP, then Post Process PoseWatch |
| Run speed or lean response | BlendSpace sample variant | Sample BlendSpace, then pose grid |
| Idle/walk/run/jump/hover behavior | State machine/runtime driver | State-machine inspect, then runtime cases |
| Foot IK or interaction reach | ControlRig late correction | Direct gate probe, then forced-driver sample if needed |
| Upper body while moving | Existing UpperBody Slot/LayeredBlend | Inventory, then all-input LayeredBlend PoseWatch |
| Antenna lag or spring follow | Bot Trail sample | Trail sample, then SIE Post Process PoseWatch |
| Baddy jiggle/stalk/tail physics | RigidBody | RigidBody settings read, then sample tuning if needed |
| Notify, curve, sync marker, Montage internals | Protected metadata | Safe inventory only; guarded native API if concrete request needs internals |

## Do Not Do First

- Do not edit original StackOBot assets for the first pass.
- Do not save dirty original maps to clean up transient proof actors.
- Do not broad-probe Montage internals with generic Python reflection.
- Do not reactivate the disconnected original Bot Trail node directly.
- Do not add C++ unless the current command surface cannot express a concrete
  request.

## Main References

- Closeout/readiness: `docs/stackobot-animation-study-closeout.md`
- Next-work backlog: `docs/stackobot-animation-next-work-backlog.md`
- Request compiler: `docs/stackobot-request-compiler-drills.md`
- Request playbook: `docs/stackobot-animation-request-playbook.md`
- Handoff templates: `docs/stackobot-animation-tivret-handoff-templates.md`
- Authoring templates: `docs/stackobot-animation-authoring-templates.md`
- Physics grammar: `docs/stackobot-physics-request-grammar.md`
- Command syntax: `docs/stackobot-animation-mcp-command-syntax.md`
- C++ API decision matrix: `docs/stackobot-cpp-api-decision-matrix.md`
- Execution map: `docs/stackobot-animation-execution-map.md`
- Sample manifest: `docs/stackobot-sample-asset-manifest.md`
- Latest live read drill: `docs/stackobot-live-read-drill-2026-06-19.md`
