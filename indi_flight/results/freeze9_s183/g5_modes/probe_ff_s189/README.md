# probe_ff_s189: revert aa4fd2654a (offboard-only body-rate FF in McIndiPosControl.cpp)
git apply -R applied cleanly. Built via run.sh 'make px4_sitl_default' (build.log; McIndiPosControl.cpp.o recompiled, 15/15).
Flights: mode_switch10, exact freeze-9 command/params, posctl, seeds 3 and 1. Scored with g57_check.py --validity leaveP.

## Result: PASS on both seeds (limit 5 deg)
Edge tilt_err deg: probe s3 / probe s1 / f9 s3 / f6 s3
 2>1   0.36 / 0.25 / 0.30 / 0.47
 1>2   2.45 / 2.94 / 10.66 / 2.40
 2>15  0.49 / 0.44 / 0.57 / 0.53
 15>2  2.38 / 2.93 / 6.20 / 3.30
 2>4   2.86 / 2.58 / 6.05 / 2.44
 4>2   3.75 / 3.81 / 4.26 / 2.64
 2>1   0.35 / 0.31 / 0.29 / 0.48
 1>15  0.04 / 0.02 / 0.05 / 0.04
 15>4  2.97 / 2.48 / 5.51 / 4.15
 4>2   3.39 / 2.95 / 5.63 / 2.76
Hold-edge errors (2>4, 15>4, 4>2) drop to freeze-6 level: aa4fd2654a is the cause (caveat: single run per seed, no f9 s1 comparison here).

## Restore
git checkout of McIndiPosControl.cpp done; git status --short src/ empty; SITL rebuilt at freeze-9 (rebuild_f9.log).
