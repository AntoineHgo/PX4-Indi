# S118 stick-pilot pre-test (D-G3-STICK-PILOT), probe not gate evidence

Re-fly of S117 probe draws idx 0 (acro), 21, 49 (stabilized), seed 117, base `quad5in_indi_g1.params`, with the
simulated pilot of `bench/stick_pilot.py` (F118 version: active from the manual-mode switch). Same draws with
`pid_default` as control (`pid_runNNN`). Command: `bash fly.sh` (v1 relaunch logged in progress.txt). The v0 flight
(pilot only in the stick segment) is kept untracked at `results/g3_pilot_s118_v0_run000`.

Note: the INDI runs use the same base params as S117, MC_INDI_POS_EN=0 (INDI rate loop under stock mc_pos_control), as in S117.

## Outcome (S119, ground truth from the ulog; times from the pilot start = manual-mode switch)

| run | ctl | exit | alt mean 0-5/5-15/15-25/25-35 s [m] | alt max [m] | tilt max [deg] | tilt 3 s before LAND |
|---|---|---|---|---|---|---|
| 000 acro | INDI | ok | 4.97 / 6.16 / 5.91 / 4.46 | 8.48 | 50.2 | 0.0 |
| 000 acro | PID | ok | 5.05 / 6.23 / 6.03 / 4.55 | 8.55 | 36.9 | 0.0 |
| 021 stab | INDI | ok | 5.00 / 5.25 / 5.53 / 4.58 | 7.72 | 8.7 | - |
| 021 stab | PID | ok | 5.04 / 5.24 / 5.57 / 4.58 | 7.70 | 7.0 | - |
| 049 stab | INDI | ok | 4.98 / 5.11 / 5.36 / 4.56 | 7.34 | 14.8 | - |
| 049 stab | PID | ok | 4.97 / 5.07 / 5.37 / 4.53 | 7.31 | 17.2 | - |

Stabilized vertical-velocity follow (`bench/stick_check.py`): corr 0.986-0.991, gain vz/demand 2.0-2.2, best lag
120-240 ms, same for INDI and PID: the pilot does not cancel the stick input (K118 MAJOR-2 closed).

Verdict: pass. Altitude held near 5 m and acro levelled for both controllers; INDI and PID within a few cm, so the
scenario now tests the vehicle under a pilot rather than open-loop drift. D-G3-STICK-PILOT decided.

Runner defect found (not a controller effect, outside the scored window): in INDI run_000 the vehicle went from
AUTO_LAND to POSCTL 0.65 s after the LAND command (83.07 -> 83.72 s), then descended on the low throttle stick and
disarmed at about 95 s. Likely the pilot keeps sending sticks after LAND and its acro deflection exceeds the
COM_RC_OVERRIDE threshold. Fix in the runner: centre or stop pilot sticks at the LAND command (open K118 MINOR).

**S121 VOID for INDI:** the "indi" runs here flew the stock rate loop (MC_INDI_EN=0, no boot_params in run.json; base params lacked MC_RATE_CTL_TYPE 1). See JOURNAL S121.
