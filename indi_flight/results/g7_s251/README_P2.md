# G7 re-check S251 (a, d, g, tests) on indi-fw-pr, F-10 head

Branch head: ee7d4542d75 (ee7d4542d7; 2 commits on main 7d362c6f38; source feat/indi-flight 3e6f2ede78). Local only, not pushed.
Contains 042e38a1dd, 1ac5d58c89, 731fc34528, b89a18b4aa, 3ab7c72046 (all in main..feat/indi-flight). `git diff --stat indi-fw-pr feat/indi-flight` over the 4 INDI src/lib and src/modules dirs: empty (identical). New files on branch: IndiEscThrust.hpp, IndiEscThrustTest.cpp, IndiRateSetpointSource.hpp, IndiRateSetpointSourceTest.cpp, IndiMeasuredTorque.{cpp,hpp}, IndiMeasuredTorqueTest.cpp (7 paths).

## Commands
- No S249 worktree existed (git worktree list: none); `FWBRANCH_WT=/tmp/indi_fwbranch_s251 indi_flight/bench/make_fw_branch.sh --force-recreate` (p2/make_fw_branch.log; deleted old branch e5b84f62bf). Re-added with `git worktree add /tmp/indi_fwbranch_s251 indi-fw-pr`.
- Submodule dirs copied from the repo checkout (not NuttX), .git pointer files removed, mavlink .git rewritten to the repo module dir. GIT_SUBMODULES_ARE_EVIL=1.
- Docker: p2/dock.sh (px4-indi-sim, worktree rw, results dir rw, repo .git ro and repo src/modules/mavlink/mavlink ro, both needed because worktree gitdir and the mavlink core.worktree point into the repo), `timeout 3500` inside, outer `timeout 3600`. Scripts fmt.sh, build.sh, tests.sh in p2/ (S249 scripts with s249 -> s251), tests_func.sh added (S249 tests.sh pattern only matched unit-* targets, so functional-IndiMeasuredTorque needed its own run). Repo build/px4_sitl_default untouched.
- Build detours (not branch problems): first two configure runs failed with "gitdir ... is not a directory" (repo .git not mounted), then link error px4_mavlink_lib_version_binary (stale build_git_version.h generated before the mavlink git fix; header deleted, regenerated). Final build is a continuation of those partial builds, so the final log shows 287 steps.

## (a) PASS
- Script: `pass rule ... []`, `stock-module diff: []`; `git diff --stat main indi-fw-pr -- <6 stock paths>`: 0 lines.
- indi_flight/ or indi_project/ paths on branch: 0. 75 files, +15587/-23 (p2/branch_paths.txt); "not in A/B lists: none".

## (d) PASS
- 50 C/C++ files changed vs main (p2/changed_cpp_files.txt), astyle dry-run per file: `checked=50 reported=0` (p2/fmt.log).

## (g) PASS (px4_sitl_default, host-arch SITL only)
- `make px4_sitl_default` in worktree: `[287/287]`, make rc=0, 0 warnings in log, bin/px4 linked, px4-mc_indi_rate_control and mc_indi_pos_control built (p2/build_tail.txt).

## Unit tests PASS (px4_sitl_test, 12 targets, all PASSED, rc=0; logs /tmp/indi_fwbranch_s251/s251_tests.log, s251_tests_func.log, copies p2/tests_docker.log)
IndiAccelControl 63, IndiEscThrust 10, IndiInjection 10, IndiInjectionStep 8, IndiPosInjection 12, IndiRateFeedforwardGate 6, IndiRateSetpointSource 3, IndiRateSetpointWatchdog 6, IndiStageMode 15, IndiTorqueStampTracker 6, indi_rate_control_test 77, functional-IndiMeasuredTorque 23. Total 239.
(S249: IndiAccelControl 61 and indi_rate_control_test 75, so +2 each from the new tests.)

## F-10 grep
Added lines of `git diff -U0 main HEAD` (all 75 files), pattern `\b(D-[A-Z0-9-]+|A-?[0-9]{1,3}|S[0-9]{2,3}|K[0-9]{2,3}|Q[0-9]{1,2}|RC[0-9]{2,3}|G[1-8]\([a-z]\))\b|indi_flight|indi_project|\bgate\b`: 0 hits (p2/f10_grep.txt empty). Wider S248 extra patterns (owner, freeze, .md/.py) not re-run.

## Unverified
- NuttX/fmu-v6x not built (known flash overflow; std::fmin NuttX finding not re-checked).
- Build was incremental after failed configure/link attempts, not one cold run.
