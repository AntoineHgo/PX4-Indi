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
- [x] candidate binary built (S233 part 2) in /tmp/px4_cand_ii/build/px4_sitl_default via /tmp/run_candii.sh (copy of run.sh also mounting main .git ro, needed for git version header); binary contains commit 43547406d3e7. sha256 of bin/px4: d5ca23f5f4ff69f741d353d779eeb508670ed249c048e60e7c1d21ce10ff8d1c

## PART2_PROGRESS
- Flights use run_flight.sh (copy of indi_project/docker/run.sh that also mounts /tmp/px4_cand_ii) with -e PX4_INDI_BUILD=/tmp/px4_cand_ii/build/px4_sitl_default. cand_ii.params == g5_freeze_s157/params.params (diff empty; MAP_* come from the candidate yaml defaults 0.2/0.5, ACT_BLD 1.0).
- chain_pre.sh = first flight (joint) alone; chain.sh = all four. Status in STATUS.txt, output stream_<name>.txt, chain.out, waiter pid in waiter.pid.
- [ ] pretest joint (started 02:19)
- [x] pretest joint flown 02:19-02:20: run_024 ABORTED by flight watchdog (tilt > 60 deg for 0.5 s, sim t=60.13, 113 deg) = LOC; g3_score.sh says INVALID (exit_status failed). Params check valid (MC_INDI_ACT_BLD 1.0, ACT_TC 0.033 as drawn). So joint item 1 FAILS (cand (i) joint passed, baseline LOC). Verdict is MISSED already; remaining 3 flights flown for the record.
- Remaining flights: `bash chain_rest.sh` (d264, d262, d283; started ~02:22; waiter pid in waiter.pid; log chain.out, STATUS.txt; CHAIN_FINISHED line marks end). If cut off: re-run `setsid nohup bash chain_rest.sh > chain.out 2>&1 &` from results dir after `docker ps` shows no px4-indi-g3s233_* container (delete the unfinished <name>/ folder first).
- Score all (after STATUS.txt shows CHAIN_FINISHED): `bash indi_flight/results/g3_cand_ii_s233/score.sh` from the repo root (rm score_args.txt first; joint will be INVALID, key2 on it may error), then write SCORES.md like g3_cand_i_s231/SCORES.md.
- [x] all 4 flights flown 02:19-02:28 (CHAIN_FINISHED), scored with score.sh both keys, SCORES.md written. VERDICT: MISSED (joint and 264 LOC at ~60 s, watchdog abort; 262 pass; 283 item 2 q not worse than baseline). Not yet looked into WHY joint/264 LOC (no root cause analysis done in part 2). .ulg not for git.
