# G3 step (c) candidate (ii), per-motor map correction (S233)

Design: ../../design/cand_ii_design.md. Worktree: /tmp/px4_cand_ii (local branch cand-ii, commit 43547406d3e; ~/px4_cand_ii was dropped because guard.sh only lets docker mount the repo, ~/.ccache and /tmp; /tmp is lost on reboot, re-create with `git worktree add /tmp/px4_cand_ii cand-ii` + submodules), base c0b733e677 + GZBridge
fix f110361a33 (git apply of that commit's GZBridge.hpp diff) = gate binary 903eae63 sources (D-BINARY-GZFIX: the 33
code files changed c0b733e677..f110361a33 are the 32 FREEZE-10 restores + GZBridge). Submodules initialised from the
main repo's .git/modules (local, same pinned commits).

## Candidate parameter values (fixed before flight; defaults in the candidate yaml, so base params need no edit)
- MC_INDI_MAP_TC = 0.2 (s), MC_INDI_MAP_LIM = 0.5, MC_INDI_ACT_BLD = 1.0 (unchanged, FREEZE-10)

## PART1_PROGRESS
- [x] design note written (design/cand_ii_design.md)
- [x] code done: cand-ii 43547406d3e = c0b733e677 + GZBridge fix + candidate (motor_map_correction.{hpp,cpp}, module wiring, yaml MC_INDI_MAP_TC/LIM, IndiMeasuredTorque::motorThrust)
- [x] unit tests pass in px4-indi-sim (make tests TESTFILTER=MotorMapCorrection: 7 tests; TESTFILTER=IndiMeasuredTorque incl. new MotorThrustOnlyFromFreshUnfrozenSamples); break-checks running (/tmp/px4_cand_ii/breakcheck.txt)
