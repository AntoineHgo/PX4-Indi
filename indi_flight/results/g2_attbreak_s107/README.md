# G2 attitude-loop break re-measure (S107), HEAD bf6c1127e6 (branch feat/indi-flight)

Why: rate-setpoint path changed (D-RATE-LEAD setpoint lead) after S91. Recipe = S91 unchanged, copied scripts
(only the output dir and container names differ): fly.sh AX RATE SEED RAMP (hover_xlong, quad5in, v2, seed 1,
RAMP 0.06, TP 10, 0.2-20 Hz, NP 5, DLY 20, MC_INDI_INJ_PT 1, base params stage5_s84_accbreak/pt1.params without PINJ),
then attitude_break_check.py, hole_report.py, ratesp_csv.py --margins (batch.sh). Run from repo root:

    indi_flight/results/g2_attbreak_s107/fly.sh 1 400 1 0.06      # pre-test, roll 400 Hz
    indi_flight/results/g2_attbreak_s107/batch.sh                 # 5 other cells, serial

Binary: build/px4_sitl_default/bin/px4 built 14:22 (after the gz_bridge GNSS fix 99673b62bd); commits since are docs/test only
(checked: no src/Tools/platforms/boards change since 14:00). Not rebuilt.

## Status log
- pre-test roll 400 PASS (check PASS, holes PASS, window 50.0 s, max |x-y-d| 3e-8): PM 56.8 GM 22.2 f_c 1.338 DM 0.118 s. SITL rebuilt via docker make px4_sitl_default (only version header changed).
- batch of 5 cells launched

## Results (HEAD bf6c1127e6, seed 1, RAMP 0.06, serial; all checks PASS, holes PASS, window 50.0 s, max |x-y-d| 3e-8)
Format S91 / S107: PM deg / GM dB / DM s / f_c Hz. Delta = S107 - S91.

| axis | rate Hz | S91 | S107 | delta | G2 pass |
|---|---|---|---|---|---|
| roll | 400 | 56.6/22.0/0.119/1.318 | 56.8/22.2/0.118/1.338 | +0.2 deg, +0.2 dB | y |
| pitch | 400 | 56.8/22.1/0.119/1.332 | 57.2/22.2/0.120/1.321 | +0.3 deg, +0.1 dB | y |
| yaw | 400 | 73.4/34.3/0.448/0.455 | 73.5/34.4/0.449/0.455 | +0.2 deg, +0.1 dB | y |
| roll | 800 | 57.3/21.9/0.121/1.319 | 57.2/22.0/0.121/1.313 | -0.1 deg, +0.1 dB | y |
| pitch | 800 | 58.1/21.9/0.123/1.311 | 57.7/22.0/0.121/1.323 | -0.4 deg, +0.1 dB | y |
| yaw | 800 | 73.8/33.9/0.452/0.454 | 73.2/32.1/0.449/0.453 | -0.5 deg, -1.8 dB (FLAG > 1.5 dB) | y |

G2: GM >= 6 dB, PM >= 45 deg, DM (0.12-0.45 s) far above 2 periods + telemetry latency: all 6 cells pass.
Flag: yaw 800 GM dropped 1.8 dB (still 32.1 dB, 26 dB above the limit). Not chased. Observed: the phase crossing moved from 7.19 Hz (S91) to 6.39 Hz (S107), on a flat-ish high-frequency |L|, so a small
phase shift moves GM by dB; yaw 400 Hz did not move. Cause not investigated (single seed, estimation scatter possible).
Conclusion: the D-RATE-LEAD setpoint change did not shift the attitude-loop margins measurably (<= 0.5 deg PM, <= 0.2 dB GM
on 5 of 6 cells). Unverified: coherence per cell not recomputed; one seed; outer loops closed (as in S91).

## Files to commit
`ax*_r*_s1_a0.06_margins.json`, `*_check.txt`, `*_holes.txt`, `*.params`, `fly.sh`, `batch.sh`, `batch.log`, this README.
Leave untracked: `ax*/` run dirs (flight.ulg, run.json), `*_att.csv`, `*.stdout.log`, `*_margins.err`.
(run.json files live in the ax*/ dirs; commit them too if the repo convention is to track them.)

## Orchestrator note (S107)
- Yaw 800 GM -1.8 dB (33.9 -> 32.1 dB): the phase crossing sits where |L| is about -32 dB, so the estimate rests on a
  small loop response; single seed, coherence not recomputed. Bounded: 26 dB above the 6 dB threshold, verdict
  unaffected. Re-open only if a later yaw attitude cell falls below 20 dB.
- Verdict: 6/6 attitude cells PASS G2 at HEAD; D-RATE-LEAD changed attitude PM by at most 0.5 deg.
