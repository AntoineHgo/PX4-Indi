# S87 G2 xy cells (preliminary, pre-freeze, margins UNKEYED for these flights)

Runner: `fly.sh PT AX RATE SEED` / `batch.sh` (serial; base `stage5_s84_accbreak/pt1.params` with MC_INDI_PINJ_AMP 0.08,
MC_INDI_PINJ_TP 20; scenario `hover_xlong` (150 s hold); quad5in, sim v2, speed 4; band 0.2-8 Hz, NP 5, DLY 20).
Re-fly of the S86 xy cells, which had low coherence below 0.5 Hz at AMP 0.04 / TP 10 (T181, keyed by T183).
PT 0 = stage input (velocity/position break), PT 1 = stage output (acceleration break); AX 1 x, 2 y (NED).

## Result
All 16 cells: PM 49.7-64.8 deg (>= 45), GM 18.2-19.3 dB (>= 6), f_c 0.27-0.34 Hz, Ms <= 1.26, min coherence >= 0.93.
DM 0.43-0.67 s against a requirement of a few control periods. pt0 (velocity/position break) PM 49.7-61.8, pt1
(acceleration break) PM 60.9-64.8. Seed spread up to 7 deg at pt0 (s1 54.4 vs s2 61.8 on ax1 r400).

## hole_report (tool after c5b5a897e9)
- 14/16 PASS.
- pt1_ax2_r400_s1 FAIL, real holes: sim 37.5 ms, controller 57.5 ms. Probably host load: the T182 agent ran hole_report
  containers during the first cells. Margins of this cell are not counted. Re-fly before the cell enters G2.
- pt0_ax2_r400_s1 FAIL on the count cross-check only (count-based 9-10 vs gap-based 1-2 at 400 Hz, as in s86
  pt0_ax1_r400_s1, T182 unverified item) and on the 89 Hz outer topic max gap 28.75 ms against a flat 10 ms (spec
  defect queued S88: limit as excess over the nominal period). Max controller-rate gap 7.5 ms.

`table.md` was produced by an inline script (S87 session); the pinj CSVs, margins JSON and holes text are committed.
| cell | PM [deg] | f_c [Hz] | GM [dB] | DM [s] | Ms | coh min | holes |
|---|---|---|---|---|---|---|---|
| pt0_ax1_r400_s1 | 54.4 | 0.33 | 18.3 | 0.458 | 1.21 | 0.93 | PASS |
| pt0_ax1_r400_s2 | 61.8 | 0.31 | 18.3 | 0.554 | 1.22 | 0.97 | PASS |
| pt0_ax1_r800_s1 | 53.0 | 0.34 | 18.7 | 0.427 | 1.24 | 0.97 | PASS |
| pt0_ax1_r800_s2 | 49.7 | 0.31 | 18.8 | 0.451 | 1.26 | 0.97 | PASS |
| pt0_ax2_r400_s1 | 53.1 | 0.31 | 18.3 | 0.471 | 1.21 | 0.97 | FAIL () |
| pt0_ax2_r400_s2 | 52.4 | 0.33 | 18.2 | 0.442 | 1.19 | 0.98 | PASS |
| pt0_ax2_r800_s1 | 52.5 | 0.32 | 18.8 | 0.455 | 1.22 | 0.98 | PASS |
| pt0_ax2_r800_s2 | 55.0 | 0.32 | 18.8 | 0.479 | 1.25 | 0.98 | PASS |
| pt1_ax1_r400_s1 | 62.8 | 0.28 | 18.6 | 0.619 | 1.17 | 0.94 | PASS |
| pt1_ax1_r400_s2 | 63.1 | 0.28 | 18.7 | 0.623 | 1.16 | 0.97 | PASS |
| pt1_ax1_r800_s1 | 60.9 | 0.29 | 19.3 | 0.591 | 1.16 | 0.96 | PASS |
| pt1_ax1_r800_s2 | 61.0 | 0.29 | 19.3 | 0.589 | 1.18 | 0.98 | PASS |
| pt1_ax2_r400_s1 | 64.2 | 0.27 | 18.7 | 0.670 | 1.16 | 0.94 | FAIL (sensor_gyro, sim_ground_truth) |
| pt1_ax2_r400_s2 | 61.1 | 0.30 | 18.8 | 0.572 | 1.16 | 0.96 | PASS |
| pt1_ax2_r800_s1 | 64.8 | 0.29 | 19.3 | 0.622 | 1.16 | 0.97 | PASS |
| pt1_ax2_r800_s2 | 61.5 | 0.29 | 19.3 | 0.584 | 1.16 | 0.95 | PASS |
