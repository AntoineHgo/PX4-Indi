# S132 A-45 fix check: AUTO take-off handover with D-HANDOVER (HandoverBlend, tau 0.5 s)

Probe (RC113), not gate evidence. quad5in, `auto_land10`, seeds 1-3, params `params.params` (copy of S131: INDI
defaults + `MC_INDI_POS_EN 1`, `MC_INDI_EN 1`, `MC_RATE_CTL_TYPE 1`). Seeds 1-3: first version of the fix (before the K132 review);
`auto_land10_final` (seed 1): committed firmware 407892e2c4 (adds decay in Hold, clear outside position control;
nominal path unchanged). Raw `flight.ulg` untracked.

    timeout 600 indi_project/docker/run.sh -n s132land -t 500 -- python3 indi_flight/bench/run_scenario.py --scenario auto_land10 --controller indi --model quad5in --seed <s> --speed 4 --sim v2 [--instance <s-1>] --params indi_flight/results/auto_smoke_s132/params.params --out indi_flight/results/auto_smoke_s132/auto_land10[_s<s>]
    python3 indi_flight/bench/auto_smoke_check.py <out> --json <out>/check.json > <out>/check.txt

| seed | vehicle_thrust_setpoint step at rampup->flight (50 ms means) | land vz (MPC_LAND_SPEED 0.70) | contact->disarm |
|---|---|---|---|
| 1 | 0.0067 (0.1 s means: 0.0083) | 0.704 | 2.68 s |
| 2 | 0.0004 | 0.702 | 2.68 s |
| 3 | 0.0008 | 0.700 | 2.68 s |
| 1, final (407892e2c4) | 0.0067 | 0.707 | 2.68 s |
| S131 INDI (before fix) | 0.035 | 0.71 | 2.7 s |
| S131 PID reference | 0.0075 | 0.70 | |

Hover thrust 0.137: worst step 0.0083 = 6 % of hover (proposed G5 limit 10 %). stage_mode 1 in every
`indi_pos_status` sample; its first sample is 0.28-0.3 s after the edge because the logger subscribes to a topic
late after its first advertisement (not a bypass, see design/a45_cause_s131.md S132 section).
