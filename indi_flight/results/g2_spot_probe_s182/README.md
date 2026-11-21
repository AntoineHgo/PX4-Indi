# G2 spot cells, probe H1 (S182): outer xy gains back to freeze-6 values

Hypothesis (design/g2_spot_cause_s182.md): phase loss comes from MC_INDI_XY_P / MC_INDI_XY_VP 1.2 / 3.6 (freeze-8) vs 0.95 / 1.8 (freeze-6 equivalent).
Probes on the unchanged freeze-8 build (d2f3845292), same seed, scenario, plant args as freeze8_s181/g2s.

## Commands
    nohup bash -c 'indi_flight/results/g2_spot_probe_s182/fly.sh rate; indi_flight/results/g2_spot_probe_s182/fly.sh att'
fly.sh is freeze8_s181/g2s_fly.sh with: output dir, container names (s182probe*), and the two params appended.
Flights ran one at a time, no other flight container present before start. Scoring via the same commands as the fly script
(m3a_csv + m3a_margins_pretest for rate; attitude_break_check + ratesp_csv --margins for att; hole_report).

## Params diff (vs freeze-8 cell params; the .params files are in this dir)
    + MC_INDI_XY_P 0.95
    + MC_INDI_XY_VP 1.8
(both cells; nothing else changed)

## ulog confirmation (ulog_params.txt, check_params.py, initial_parameters, no changed_parameters)
- P1 rate: MC_INDI_XY_P 0.95, MC_INDI_XY_VP 1.8 (float 0.949999988 / 1.79999995)
- P2 att:  MC_INDI_XY_P 0.95, MC_INDI_XY_VP 1.8
- freeze-8 att ulg for contrast: 1.2 / 3.6

## Results
| cell | GM dB | PM deg | DM ms | crossover Hz | holes OVERALL | vs freeze-8 | vs freeze-6 |
|---|---|---|---|---|---|---|---|
| P1 rate roll800_fwdef_s2 | 16.1 | 49.0 | 77.1 | 1.77 | PASS | 41.3/15.9/70.6 -> +7.7 deg PM, +0.2 dB, +6.5 ms | 54.3: still 5.3 deg short |
| P2 att ax2_r400_s1 | 14.5 | 51.4 | 98.2 | 1.45 | FAIL (sim 16 holes 0.034 %, max 17.5 ms, excess 15 ms; controller 5 holes) | 42.2/13.6/82.1 -> +9.2 deg PM, +0.9 dB, +16 ms | 53.4: 2.0 deg short |

Phase at 1 Hz (rate cell): probe -155.0 deg, freeze-8 -167.2, freeze-6 -153 (probe recovers 12 of 14 deg). |L| at 1 Hz 8.2 dB (freeze-8 6.8).
attitude_break_check on P2: RESULT PASS.

## Verdict
H1 restores the margin partly to mostly: both cells clear PM >= 45; attitude is close to freeze-6 (51.4 vs 53.4), rate is partial (49.0 vs 54.3).
Some of the rate-cell loss is therefore from something else (candidate: the F4 setpoint lead 0.01 -> 0.03, only inner-loop change).

## Caveats
- Single seed each, no repeat; the seed-to-seed PM spread is not measured here.
- P2 hole_report FAILs the gate (freeze-8 att run PASSed); the margin numbers are reported but the att probe does not meet the hole gate. Not re-flown.
