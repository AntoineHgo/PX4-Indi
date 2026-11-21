# S183 outer xy gain sweep (G2 spot cells PM >= 45 and G5.5 <= 0.5 m)

Pairs, both MC_INDI_XY_P 1.2: (A) MC_INDI_XY_VP 2.4, (B) MC_INDI_XY_VP 2.8. Freeze-8 build, one Docker flight at a time, no other flight container present before start.

## Commands
    indi_flight/results/xy_sweep_s183/fly.sh rate 2.4        # pre-test, pair A rate cell first
    nohup bash indi_flight/results/xy_sweep_s183/queue.sh &  # rest, idempotent; queue_status.tsv (rate_2.4 was the pre-test, so not in it)
- fly.sh = g2_spot_probe_s182/fly.sh with output dir vp<VP>/, container names s183sw<VP>*, XY_P 1.2 and XY_VP <arg2> appended to cell params.
- queue.sh G5.5 fly() = freeze8_s181/queue.sh fly() (params g5_freeze_s157/params.params + the two params appended, copy in vp<VP>/g55/<sc>_s1.params).
- Scoring: spot as in fly.sh (m3a_csv + m3a_margins_pretest rate; attitude_break_check + ratesp_csv --margins att; hole_report). G5.5: `g55_check.py <run> --json <run>/g55.json`, metric = rms_h_m (limit 0.5 m; V limit 0.3 m also met).
- Seeds: rate roll800_fwdef_s2, att ax2_r400_s1, G5.5 o1/o3/o7 seed 1.

## Params diff vs freeze-8 (firmware defaults 1.2 / 3.6, not in params files)
    + MC_INDI_XY_P 1.2
    + MC_INDI_XY_VP 2.4 (A) | 2.8 (B)
## ulog confirmation
ulog_params.txt (check_params.py of s182, initial_parameters, no changed_parameters): all 10 flights show XY_P 1.2 and XY_VP 2.4 (A) / 2.8 (B).

## Results (single seed per cell)
| pair XY_P/XY_VP | rate GM dB | PM deg | DM ms | fc Hz | att GM dB | PM deg | DM ms | fc Hz | holes rate / att | G5.5 o1 / o3 / o7 H RMS m |
|---|---|---|---|---|---|---|---|---|---|---|
| freeze-8 1.2/3.6 | 15.9 | 41.3 | 70.6 | 1.63 | 13.6 | 42.2 | 82.1 | - | PASS / PASS | 0.302 / 0.317 / 0.290 |
| probe 0.95/1.8 (s182) | 16.1 | 49.0 | 77.1 | 1.77 | 14.5 | 51.4 | 98.2 | 1.45 | PASS / FAIL | 0.587 / - / - |
| A 1.2/2.4 | 16.4 | 47.2 | 76.1 | 1.72 | 13.8 | 48.1 | 93.2 | 1.43 | PASS / PASS | 0.443 / 0.453 / 0.440 |
| B 1.2/2.8 | 16.0 | 45.5 | 74.7 | 1.69 | 13.9 | 46.4 | 90.5 | 1.42 | FAIL / PASS | 0.375 / 0.399 / 0.387 |
(freeze-8 att fc not re-read; probe o3/o7 not flown. attitude_break_check RESULT PASS for A and B att.)
B rate hole_report FAIL: sim 9 holes 0.0104 % max 12.5 ms excess 11.25 ms, controller 15 holes max 16.25 ms excess 15 ms (limit 10 ms excess); timing jitter, margins still reported. Not re-flown.

## Verdict
Both pairs give PM >= 45 on both cells (A 47.2/48.1, B 45.5/46.4) and all three G5.5 <= 0.5 m (A max 0.453, B max 0.399).
A passes the hole gate on both cells too; B fails the rate-cell hole gate and has only 0.5 / 1.4 deg PM margin. A is the cleaner candidate (PM margin ~2-3 deg, G5.5 margin ~0.05 m); B has more G5.5 margin.
Caveats: single seed per cell, PM seed spread unmeasured (B's margin is inside plausible spread); G5.5 only seed 1 and 3 of 8 scenarios; o7 V RMS 0.13 m (limit 0.3) fine.
