# G7 re-check S248 (a, d, g) on indi-fw-pr

Branch head: 4ebf90ad2f9110c32548cd50b4b8938329fefdab (2 commits on main 7d362c6f38; source feat/indi-flight 0b1c6a26d1). Local only, not pushed.

## Commands
- `FWBRANCH_WT=/tmp/indi_fwbranch_s248 indi_flight/bench/make_fw_branch.sh --force-recreate` (log: make_fw_branch.log). The script removes its worktree on exit, so I re-added it with `git worktree add /tmp/indi_fwbranch_s248 indi-fw-pr`.
- Submodule dirs in the worktree were empty; copied from the repo checkout (not NuttX), .git pointer files removed, mavlink .git pointed at the repo module dir (needed for px_update_git_header). Build used GIT_SUBMODULES_ARE_EVIL=1.
- Docker: direct `docker run` on px4-indi-sim (same flags as run.sh) with the worktree as an extra mount, because run.sh mounts only the repo. Repo build/px4_sitl_default untouched.

## (a) PASS
- Script: `pass rule git diff --stat main -- indi_flight indi_project: []`, `stock-module diff: []`.
- `git diff --stat main indi-fw-pr -- <6 stock paths>`: 0 lines.
- Paths under indi_flight/ or indi_project/ on branch: 0. 71 files, +14588/-23 (branch_paths.txt); all in the script A/B lists ("not in A/B lists: none").

## (d) PASS
- 46 C/C++ files changed vs main under src/msg (changed_cpp_files.txt), astyle `fix_code_style.sh --dry-run --formatted` per file (S195 method, fmt.sh), in the worktree: `checked=46 reported=0`.

## (g) PASS (px4_sitl_default, host-arch SITL only)
- `make px4_sitl_default` in worktree, build dir /tmp/indi_fwbranch_s248/build/px4_sitl_default: `[287/287] ... make rc=0`, 0 warnings, bin/px4 plus px4-mc_indi_rate_control and px4-mc_indi_pos_control produced (build_tail.txt; full log /tmp/indi_fwbranch_s248/s248_build.log).
- Unverified: NuttX/fmu-v6x not built (known 23.5 kB flash overflow, and the S195 std::fmin NuttX finding was not re-checked).

## Unit tests PASS (tests.log)
Config px4_sitl_test, 9 gtest targets, all PASSED: IndiAccelControl 61, IndiInjection 10, IndiInjectionStep 8, IndiPosInjection 12, IndiRateFeedforwardGate 6, IndiRateSetpointWatchdog 6, IndiStageMode 15, IndiTorqueStampTracker 6, indi_rate_control_test 75.
