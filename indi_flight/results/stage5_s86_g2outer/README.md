# S86 G2 outer-loop cells (preliminary, pre-freeze, UNKEYED)

Runner: `fly.sh PT AX RATE SEED` (from repo root, run with bash; base params `stage5_s84_accbreak/pt1.params`,
hover_long, quad5in, sim v2, speed 4, AMP 0.04, TP 10, NP 5, DLY 20, band 0.2-8 Hz). Per cell: `<cell>.params`,
`<cell>_margins.json` (pinj_csv --margins), `<cell>_holes.txt` (hole_report after the T179 fixes, 98e977a9f0).

## Findings
1. **G2 cells must fly one at a time.** The 3-flight parallel pre-test (pt0_ax1_r400_s1, pt1_ax1_r400_s1,
   pt1_ax3_r800_s1 moved to `pretest_parallel/`) failed hole_report: sim holes 0.10-0.21 % (max 12.5-15 ms) and
   controller holes up to 21 ms. Single flights (S83 tb10, S84 pt1/hf, S86 serial) have sim max <= 6.25 ms.
2. **xy "no crossover" is a reading error, not a loop fault** (T181, `t181_xy_diagnosis.md`, UNKEYED): `top_db` is
   |L| at the last accepted bin, not the maximum (margins_est.py:254). Raw FRF from the CSV: |L| 1.26 / 0.74 / 0.27 at
   0.2 / 0.4 / 1 Hz, crossover about 0.35 Hz, PM about 55 deg; the bins below 0.5 Hz fail the coherence gate. Stock
   MPC_XY gains predict 0.60 / 0.29 / 0.14 at 0.5 / 1 / 2 Hz (measured 0.69 / 0.27 / 0.16). Fix: re-fly xy with
   AMP 0.08 and TP 20 (serial), rename/clarify `top_db`.
3. **hole_report count cross-check fails healthy 800 Hz runs** (T179 finding-1 fix): count-based vs gap-based missing
   differ by 1 (gyro, torque setpoint) and 3 (actuator_motors) on pt1/pt0 ax3 r800 s1, all other criteria PASS
   (missing 0.043 %, max 5 ms). A disagreement of 1 is flagged although the spec says > 1: check the comparison and
   the tolerance at 1.25 ms periods before any G2 cell counts. Tool defect, not a flight defect.

## z cells (serial)
| cell | PM [deg] | f_c [Hz] | DM [s] | Ms | holes |
|---|---|---|---|---|---|
| pt1_ax3_r400_s1 (accel break) | 63.7 | 0.68 | 0.262 | 1.18 | PASS |
| pt1_ax3_r800_s1 (accel break) | 63.0 | 0.70 | 0.251 | 1.20 | FAIL (count check, finding 3) |
| pt0_ax3_r800_s1 (vel/pos break) | 62.8 | 0.68 | 0.255 | 1.17 | FAIL (count check, finding 3) |
| pt1_ax3_r400_s2 | 63.0 | 0.65 | 0.269 | 1.20 | PASS |
| pt1_ax3_r800_s2 | 58.3 | 0.68 | 0.239 | 1.17 | FAIL (count check) |
| pt0_ax3_r800_s2 | 66.1 | 0.69 | 0.266 | 1.17 | FAIL (count check) |
| pt0_ax3_r400_s2 | 64.5 | 0.62 | 0.291 | 1.17 | PASS |

All 400 Hz cells PASS hole_report, all 800 Hz cells FAIL only on the count cross-check (finding 3). z PM range 58.3-66.1 deg, all >= 45; pt0_ax3_r400_s1 = S83 tb10 (57.3, re-scored S85). Preliminary: cells count only after the count-check fix and a second key of the margins.
