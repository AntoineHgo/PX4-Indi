# G7(g) firmware-only branch `indi-fw-pr`

Command: `bash indi_flight/bench/make_fw_branch.sh [feat/indi-flight] [indi-fw-pr] [--force-recreate]`
Refuses if the branch exists without `--force-recreate`; never pushes; removes its worktree on exit.

## Base
main == merge-base == 7d362c6f3804e6d8f345cc10b71a70ec18dccabc (main has not moved, no conflict possible).
The script reports it if main moves and lists A/B paths changed on main.

## Inventory (71 changed paths outside indi_flight and indi_project; none under .github, .claude, docs, Tools)
| Path | Class | Reason |
|---|---|---|
| src/lib/indi_accel_control/* (4) | A | INDI library + unit test |
| src/lib/indi_rate_control/* (4) | A | INDI library + unit test |
| src/modules/mc_indi_rate_control/* (23) | A | INDI rate module, params, Kconfig, tests |
| src/modules/mc_indi_pos_control/* (16) | A | INDI position module, params, Kconfig, tests |
| msg/ActuatorTorqueMeasured, IndiPosStatus, IndiRateFeedforward, IndiRateStatus (.msg) | A | INDI topics |
| msg/CMakeLists.txt | A (Sim lines in B) | registers msgs; commit 1 omits the two Sim msgs so it stays self-consistent |
| src/lib/CMakeLists.txt | A | add_subdirectory of the two libs |
| src/modules/logger/logged_topics.cpp | A | INDI optional topics |
| ROMFS/.../init.d/rc.mc_apps | A | MC_INDI_EN / MC_INDI_POS_EN start selection |
| ROMFS/.../airframes/4040_gz_quad5in, airframes/CMakeLists.txt | A | airframe |
| boards/px4/sitl/default.px4board | A (scenario-player line in B) | enables INDI modules |
| src/modules/simulation/gz_bridge/* (6 modified) | B | rotor-speed eRPM telemetry |
| src/modules/simulation/sim_scenario_player/* (4) | B | SITL schedule player |
| msg/SimGroundTruth.msg, SimScheduleApplied.msg | B | used by gz_bridge / scenario player |
| ROMFS/.../init.d-posix/rcS | B | starts sim_scenario_player |
Counts: A = 53 paths (+2 shared), B = 16 paths. C = 0 (no agent/tooling files differ from main). D = 0 unclear.

## Flags
- 4040_gz_quad5in sets PX4_SIM_MODEL=quad5in served from `indi_flight/sim/models/quad5in`, which is NOT in the branch (pass rule forbids indi_flight). The airframe will not run in the PR until the model is added under Tools/simulation (not done).
- Bench injectors / Tools/simulation: no changes exist in the diff; nothing to include.
- docs/en: no INDI page exists on feat/indi-flight, so none is included (docs/ko, zh, uk never).

## Stock modules
`git diff --stat main feat/indi-flight -- src/modules/mc_rate_control src/modules/mc_att_control src/modules/mc_pos_control src/modules/control_allocator src/lib/control_allocation src/modules/commander` -> empty (also empty on the branch).

## Pass rules (on indi-fw-pr)
- `git diff --stat main -- indi_flight indi_project` -> empty
- stock-module diff -> empty
- Every path outside indi_*/.claude differs from feat/indi-flight by nothing (branch tree equals source for those paths, except the two commit-1 strips, restored in commit 2).

## Commits (main..indi-fw-pr)
- 5789844545 feat(indi): INDI rate and acceleration control modules (58 files, +12412/-4)
- d9a35024e2 feat(simulation): gz_bridge rotor-speed telemetry for INDI (15 files, +1778/-18)
Total: 71 files changed, 14190 insertions, 22 deletions. Both carry `Assisted-by: Claude`.

## Unverified
Build of the branch (SITL and unit tests) not run, commit 1 alone not built, not pushed, no PR opened. Commit 1 omits sim msgs/scenario player by line stripping (sed), only checked by inspection.
