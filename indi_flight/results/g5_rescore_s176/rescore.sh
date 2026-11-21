#!/usr/bin/env bash
# S176 re-score of existing G5 evidence with the S175-amended checkers (no flights). Run from the repo root.
R=indi_flight/results; O=$R/g5_rescore_s176; B=indi_flight/bench
d() { indi_project/docker/run.sh -n s176rs -t 600 -e PYTHONDONTWRITEBYTECODE=1 -- "$@"; }
# G5.2 (z band max(2 % d, 0.10 m))
d python3 $B/g52_check.py --out $O/g52 $R/g5_freeze_s157/stick_pos_steps_s{1,2,3}_{altctl,posctl} $R/g5_freeze_s157/stick_pos_steps_s1_posctl_pid > $O/g52_rescore.txt 2>&1
# G5.9a (kill flag reference + commander latency), G5.8 unchanged
d python3 $B/g5_rows_check.py --out $O/g5_rows_freeze $R/g5_freeze_s157/g5_events_s{1,2,3} > $O/g5_rows_freeze.txt 2>&1
d python3 $B/g5_rows_check.py --out $O/g5_rows_s161 $R/g511_fix_s161/g5_events_s{1,2,3} > $O/g5_rows_s161.txt 2>&1
# G5.10 (tilt limit MPC_TILTMAX_AIR + 5 deg)
for s in 1 2 3; do d python3 $B/g510_check.py $R/g5_freeze_s157/sat_sustained_s$s --json $O/g510_sat_sustained_s$s.json > $O/g510_sat_sustained_s$s.txt 2>&1; done
# G5.11 (xy horizontal excursion; yaw tilt excess over the no-event p95)
d python3 $B/g511_check.py --out $O/g511 $R/g511_fix_s161/g5_events_s{1,2,3} > $O/g511_s161.txt 2>&1
d python3 $B/g511_check.py --out $O/g511_freeze $R/g5_freeze_s157/g5_events_s{1,2,3} $R/g5_freeze_s157/g5_events_s1_pid > $O/g511_freeze.txt 2>&1
