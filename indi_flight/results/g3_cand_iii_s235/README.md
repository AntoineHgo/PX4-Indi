# G3 step (c) candidate (iii), bounded rate integrator (S235)

Design: ../../design/cand_iii_design.md. Worktree: /tmp/px4_cand_iii (base 94b4270a687, uncommitted changes in msg/IndiRateStatus.msg, src/lib/indi_rate_control/*, src/modules/mc_indi_rate_control/*). Diff saved as cand_iii.diff.

## Checks (2026-11-26)
- [x] `git -C /tmp/px4_cand_iii diff` == cand_iii.diff except one extra hunk in the live diff: submodule src/modules/mavlink/mavlink shows "-dirty" (untracked .gd_mav/, not a source change).
- [x] binary build/px4_sitl_default/bin/px4 (05:33:54) is newer than every changed source (latest 05:31:38). sha256 60d6a954a24eaf91b366988b60ad689ca60e1d1101edba270887c40777755937
- [x] unit tests: ctest unit-indi_rate_control_test 1/1 passed; gtest binary 79 tests from 9 suites, 79 passed, 0 failed (unit_test.log). Run via /tmp/run_candiii.sh (run.sh copy with REPO_DIR=/tmp/px4_cand_iii and main .git mounted ro) with -e GIT_SUBMODULES_ARE_EVIL=1, `make tests TESTFILTER=indi`, build dir px4_sitl_test. A first attempt with run_flight.sh failed on the submodule check (wiped the empty px4_sitl_test dir, px4_sitl_default untouched; binary mtime/sha unchanged).
- [x] no stray containers before launch.

## Flights
- Launched 2026-11-26 05:37:56 (chain.sh via setsid nohup, pid 1768338, output chain.out, status STATUS.txt). Order joint, d264, d262, d283.
- 05:40: STATUS.txt shows "START joint", container px4-indi-g3s235_joint running.
- [ ] flights finished (CHAIN_FINISHED in STATUS.txt), [ ] scored (score.sh), [ ] SCORES.md
