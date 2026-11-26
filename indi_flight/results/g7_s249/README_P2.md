# G7 re-check S249 (a, d, g, tests) on indi-fw-pr, F-10 head

Branch head: e5b84f62bf62dfbbd4f416aa07c7a9b7cdaaae12 (2 commits on main 7d362c6f38; source feat/indi-flight f96444ba09). Local only, not pushed.

## Commands
- Removed the stale S248 worktree (it held the branch), then `FWBRANCH_WT=/tmp/indi_fwbranch_s249 indi_flight/bench/make_fw_branch.sh --force-recreate` (p2/make_fw_branch.log). Re-added with `git worktree add /tmp/indi_fwbranch_s249 indi-fw-pr`.
- Submodule dirs copied from the repo checkout (not NuttX), .git pointer files removed, mavlink .git pointed at the repo module dir. GIT_SUBMODULES_ARE_EVIL=1.
- Docker: direct `docker run` on px4-indi-sim (run.sh flags, worktree as extra mount), `timeout 3500` inside, outer `timeout 3600`. Scripts fmt.sh, build.sh, tests.sh in p2/ (S248 scripts with s248 -> s249). Repo build/px4_sitl_default untouched.

## (a) PASS
- Script: `pass rule ... []`, `stock-module diff: []`; `git diff --stat main indi-fw-pr -- <6 stock paths>`: 0 lines.
- indi_flight/ or indi_project/ paths on branch: 0. 71 files, +14866/-23 (p2/branch_paths.txt); "not in A/B lists: none".

## (d) PASS
- 46 C/C++ files changed vs main (p2/changed_cpp_files.txt), astyle dry-run per file: `checked=46 reported=0`.

## (g) PASS (px4_sitl_default, host-arch SITL only)
- `make px4_sitl_default` in worktree: `[1924/1924]`, make rc=0, 0 warnings, px4-mc_indi_rate_control and px4-mc_indi_pos_control built (p2/build_tail.txt). Cold build (1924 steps vs 287 in S248).

## Unit tests PASS (p2/tests.log, tests_summary.txt)
px4_sitl_test, 9 targets, all PASSED: IndiAccelControl 61, IndiInjection 10, IndiInjectionStep 8, IndiPosInjection 12, IndiRateFeedforwardGate 6, IndiRateSetpointWatchdog 6, IndiStageMode 15, IndiTorqueStampTracker 6, indi_rate_control_test 75 (same as S248).

## F-10 grep
Pattern over files from `git diff --name-only main` in the worktree: 0 hits (p2/f10_grep.txt empty).

## Unverified
- NuttX/fmu-v6x not built (known flash overflow; std::fmin NuttX finding not re-checked).
