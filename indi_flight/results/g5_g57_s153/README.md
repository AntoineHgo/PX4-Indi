# S153 G5.7 mode_switch10 seed 1 re-fly with GNSS delay 110 ms (current firmware)
Command: `indi_flight/results/g5_g57_s153/fly.sh` (repo root; `timeout 900`; `run.sh -n s153s1 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario mode_switch10 --stick-mode posctl --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/g5_g57_s153/params.params --gps-dly 110 --gnss-delay 110 --out .../mode_switch10_s1`). Scored with `bench/g57_check.py --validity leaveP mode_switch10_s1` into `g57_summary.txt`.
Firmware: SITL rebuilt in Docker (`make px4_sitl_default`, OK) at HEAD 970402b51f; last src change is 23acbdef67 (mc_indi_pos_control).
Result: **PASS** (10 edges, 4 fast, LOC no, hover 0.137, rc=0).
Worst tilt (limit 5 deg): 3.71 deg at e9 S>H (S143 s2 3.62 at e9; S143 s3 3.55 at e9).
Worst thrust step (limit 20 % hover): 2.6 % at e4 S>P (S143 s2 3.0 %).
Per-edge tilt/thrust (deg / %): e1 0.53/0.9, e2 1.98/0.3, e3 0.49/0.4, e4 2.31/2.6, e5 2.17/0.3, e6 2.42/0.4, e7 0.58/1.1, e8 0.03/0.6, e9 3.71/1.3, e10 1.94/0.4.
