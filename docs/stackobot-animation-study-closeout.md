# StackOBot Animation Study Closeout

Use this as the readiness gate before accepting a future StackOBot animation
request without a user-provided sample.

## Objective Covered

The study goal was to learn enough of StackOBot's animation systems to create or
modify animation-related parts from intent alone:

- main AnimBP routing and state-machine behavior;
- Post Process AnimBP late bone edits;
- ControlRig late correction and gate forcing;
- Slot/LayeredBoneBlend upper-body route;
- BlendSpace response and sample-only variants;
- Trail and RigidBody animation-physics effects;
- safe boundaries for notifies, curves, sync markers, and Montage internals.

Current status: ready for sample-first implementation requests. Do not mutate
original StackOBot assets unless the user explicitly approves that scope.

## First Page Order

1. Start with `docs/stackobot-animation-quickstart.md`.
2. Compile the request through `docs/stackobot-request-compiler-drills.md`.
3. Pick the route from `docs/stackobot-animation-authoring-templates.md`.
4. Show the matching handoff from
   `docs/stackobot-animation-tivret-handoff-templates.md`.
5. Use command syntax from `docs/stackobot-animation-mcp-command-syntax.md`.
6. Check `docs/stackobot-cpp-api-decision-matrix.md` before any new C++.
7. Check `docs/stackobot-animation-next-work-backlog.md` only if the route is
   blocked or marked candidate.
8. Record the result in `docs/work-log.md`.

## Ready Routes

| Request type | Default route | Verification |
| --- | --- | --- |
| Head, neck, antenna offset after base animation | Post Process ModifyBone sample | Same-instance Post Process PoseWatch |
| Run lean, speed response, or BlendSpace tuning | Sample BlendSpace variant | Runtime pose grid |
| Idle/walk/run/jump/hover behavior | State-machine read and runtime driver cases | Runtime state snapshots and transition metrics |
| Foot IK or interaction reach | ControlRig probe, then forced-driver sample if gates are inactive | ControlRig direct probe plus AnimGraph PoseWatch |
| Upper body over locomotion | Existing `UpperBody` Slot/LayeredBoneBlend route | All-input LayeredBoneBlend PoseWatch |
| Antenna lag or spring follow | Bot Trail Post Process sample | Post Process Trail PoseWatch; prefer SIE/PIE for motion |
| Baddy stalk/body secondary motion | Existing Baddy RigidBody route or sample tuning | RigidBody settings read plus PoseWatch/source comparison |
| Node contribution question | Instrumentation only | Compiled mapping or PoseWatch pre/post |

## Current Evidence Baseline

Latest live validation:

- `docs/stackobot-live-read-drill-2026-06-19.md`
- bridge `127.0.0.1:55557` was restored for a read-only drill;
- Post Process ModifyBone, Bot Trail, Baddy RigidBody, ControlRig,
  LayeredBoneBlend, and state-machine nodes all matched the compiler routes;
- dirty content and map packages after the read drill were `0`;
- the hidden StackOBot editor was closed afterward and the bridge port was no
  longer open.

Stable local sample inventory:

- `docs/stackobot-sample-asset-manifest.md`
- sample root: `/Game/_MCP_Sample/AnimStudy`
- evidence root: `D:/Git/SampleProject/StackOBot/Saved/MCP/AnimStudy`

The StackOBot sample project is not a git repository. Treat its `_MCP_Sample`
assets as local learning artifacts, not versioned deliverables.

## C++ / API Timing

Current timing: no new C++ is needed before the next concrete request.

Keep C++ as a candidate only when the request hits a trigger in
`docs/stackobot-cpp-api-decision-matrix.md`, especially:

- new state or transition authoring that runtime-driver cases cannot express;
- a visible upper-body action source that the existing route cannot provide;
- new Bot RigidBody-style physics where Trail and Baddy references are not
  semantically enough;
- notifies, curves, sync markers, or Montage internals that are protected or
  unsafe through current Python reads;
- repeated PoseWatch failures caused by actor or AnimInstance resolution.

Do not add C++ for ordinary "turn head", "lean more", "antenna lag", "make it
stronger", or "which node changed the pose" requests.

For the non-immediate backlog, use
`docs/stackobot-animation-next-work-backlog.md`.

## Residual Risks

- Existing upper-body proof confirms the Slot/LayeredBoneBlend route, but not a
  visible authored action clip. A concrete action request may need a new sample
  overlay route.
- New state/transition graph authoring is not implemented as a safe sample
  command yet. Runtime-driver proof should come first.
- Notify, curve, sync-marker, and Montage internals remain guarded territory.
  Generic Python Montage probing already asserted in `AnimMontage.h:770`.
- Advanced command availability must be checked against the StackOBot-local
  UnrealMCP plugin copy at
  `D:/Git/SampleProject/StackOBot/Plugins/UnrealMCP`.
- Some proof routes need SIE/PIE for meaningful motion. Static editor-world
  proof is enough only for static Post Process ModifyBone-style deltas.

## Next Request Protocol

For a future request such as "make the bot head look right", "make run lean
wider", "make antenna lag", or "make upper body act while moving":

1. classify the request with the compiler;
2. choose the narrowest sample-only route;
3. show the visible Tivret handoff block before asset work;
4. create or reuse only `_MCP_Sample/AnimStudy` assets;
5. verify with route-specific runtime evidence;
6. report created paths, original mutation status, proof result, artifacts,
   dirty packages, and C++/API decision.

That is enough to proceed without asking the user for a sample first.
