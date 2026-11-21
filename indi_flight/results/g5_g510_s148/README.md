# G5.10 re-fly after A-48 fix (S148, probe, parallel streams: not gate evidence)

A-48 cause (results/g5_g510_s147/a48_cause.md): the S147 saturation release was 8 sequential per-motor SIM_GZ_EC
MIN/MAX sets spread over about 110 ms, so the motors regained thrust one by one. The asymmetric kick appeared while the
attitude setpoint stayed at about 1 deg. Fix 867e10424a: a uniform all-motor fault is sent as one SIM_GZ_THR_SC set
(sends.csv: `SIM_GZ_THR_SC=0.274` at the SAT start, `=1.0` at REC). The fix has no second key yet.

Command: as in g5_g510_s147/README.md with `--out indi_flight/results/g5_g510_s148/<run>`. The PID run uses no --params.
Check: `python3 indi_flight/bench/g510_check.py <run> --json <run>/g510.json`.

| run | alt loss m (<=2.0) | tilt max deg | back SAT s (<=5) | LOC |
|---|---|---|---|---|
| s1 INDI | 2.71 FAIL | 45.33 | 3.31 | no |
| s2 INDI | 2.74 FAIL | 45.32 | 3.47 | no |
| s3 INDI | 2.67 FAIL | 45.44 | 3.42 | no |
| indi_s2_rep (launched as pid_default, but the params file sets MC_INDI_EN 1, so it flew INDI) | 2.74 | 45.33 | 3.45 | no |
| pid_s2 PID | runner watchdog abort: > 3 m below hold for 1 s at t=60.9 s (SAT part) | - | - | - |

Reading:
- The 65 deg spike at the REC edge is gone. Max tilt is 45.3-45.4 deg = MPC_TILTMAX_AIR, i.e. what the 3 m step commands
  (Q9 a). A-48 is closed as a test artefact.
- Altitude loss in SAT is 2.67-2.74 m, a FAIL against 2.0. It is larger than in S147 (2.15-2.21 m), which also ran at
  thrust scale 0.274, but there the per-motor caps were set one by one. This difference is not explained yet.
  PID loses more than 3 m.
- The AGG part did not saturate (same as S147), so it is INVALID. Q9 (b) is still open.
- The INDI s2 repeat agrees with s2 within 0.004 m.
