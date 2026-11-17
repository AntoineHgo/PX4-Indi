# S59 hover check of stage-3 items 1-4 (65356c4250 + items 2/3 in eafb26b623^, binary at HEAD eafb26b623)

Purpose: first flights with the landed split + t_fb ramp (item 1), frozen-rpm detection (item 4), rate setpoint
timeout (item 3, D-S3-SPTO) and the second-publisher guard (item 2). Check: flies, no false trip of any new flag.

Command (per seed N; binary rebuilt at HEAD first, `make px4_sitl_default` in Docker, rc 0):

    indi_project/docker/run.sh -n s59fly -t 600 -- python3 indi_flight/bench/run_scenario.py --scenario hover \
      --controller indi_meas --model quad5in --sim v2 --rate-hz 800 --seed N --speed 4 --gate \
      --params indi_flight/results/stage3_s59/hover_items23/hover.params --out indi_flight/results/stage3_s59/hover_items23/hover_sN
    python3 indi_flight/bench/pretest_gate.py hover_sN/flight.ulg gate[_sN].md

Params: `hover.params` = S57 `meas800.params` without the injection lines (measured rotor, CA_R_W_MAX 2700, 800 Hz).

## Results

| seed | gate | rate RMS x/y/z [rad/s] | pin | rate_sp_stale | foreign_torque_pub | frozen mask | take-off / touchdown |
|---|---|---|---|---|---|---|---|
| 1 | PASS | 0.0054 / 0.0044 / 0.0012 | 0 | 0 of 65046 | 0 of 65046 | 0 | 32.0 s / 98.3 s |
| 2 | PASS | 0.0060 / 0.0042 / 0.0009 | 0 | 0 of 65181 | 0 of 65181 | 0 | 32.0 s / 98.4 s |

px4.log (both seeds): no "rate setpoint timeout", no "another controller", no "not starting" message.
measured_torque_in_use: 0.864 of all status samples (whole log, ground phases included).

## Not covered here (G5, stage 6)
Triggering paths in SITL: stopping mc_att_control in flight (timeout trips, recovers), `mc_rate_control start` while
INDI runs (foreign flag), `mc_indi_rate_control start` after a stock rate controller (refusal).
