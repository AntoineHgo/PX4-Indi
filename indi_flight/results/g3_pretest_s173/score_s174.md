# G3 pre-test S173 scoring (S174), 20 runs, master seed 173
Script: `score.sh` (writes run_NNN/g3_checks.json + g3_checks.txt). Needs scipy: host python lacks it, I ran with a scratchpad install via PYTHONPATH.
Window DEVIATION: stand-in scenarios (g3_run.py:26 UNVERIFIED comment) have no 20 s hold; the last segment "hold" is 3 s. Window = those 3 s
(metrics window.end_s minus ulog start_timestamp; the px4-clock window lands after touchdown). Flags: --wind on all lemniscate runs (gust_x), --sag if sag/weak motor.

## Verdicts
Columns: V1 = g3_checks pass incl. chatter clause; V2 = without chatter (LOC incl. the 5 m excursion rule); V3 = V2 also without the 5 m excursion
rule (see finding A). Limits: LOC tilt 0.2 s, exc 5.0 m, hRMS 0.30 (wind), alt 0.10 calm / 0.20 sag or weak.
| run | scen | mode | V1 | V2 | V3 | failing criterion value/limit | factors not applied |
|---|---|---|---|---|---|---|---|
| 00 | lemn | posit | F | F | P | exc 5.43/5.0 | - |
| 01 | lemn | posit | F | F | P | exc 5.62/5.0 | - |
| 02 | lemn | posit | F | F | F | exc 6.80/5.0, hRMS 0.692/0.3 | - |
| 03 | lemn | posit | F | F | F | exc 5.70/5.0, osc pqr (q 52/51 win), hRMS 0.450/0.3, alt 0.273/0.1 | tel_frozen |
| 04 | zsine | acro | F | P | P | - | - |
| 05 | lemn | posit | F | F | F | exc 6.57/5.0, hRMS 0.603/0.3 | - |
| 06 | lemn | posit | F | F | P | exc 5.43/5.0 | - |
| 07 | lemn | posit | F | F | F | exc 5.43/5.0, osc pqr (q 32/51 win), alt 0.102/0.1 | - |
| 08 | lemn | posit | F | F | F | exc 5.02/5.0, osc q (q 14/51 win) | - |
| 09 | lemn | posit | F | F | F | exc 5.94/5.0, hRMS 0.344/0.3 | - |
| 10 | zsine | stabi | F | P | P | - | - |
| 11 | lemn | posit | F | F | P | exc 5.22/5.0 | tel_frozen |
| 12 | lemn | posit | F | F | P | exc 5.15/5.0 | - |
| 13 | lemn | posit | F | F | F | exc 5.14/5.0, osc pqr (q 18/51 win) | - |
| 14 | lemn | posit | F | F | P | exc 5.40/5.0 | - |
| 15 | lemn | posit | F | F | P | exc 5.48/5.0 | - |
| 16 | zsine | stabi | F | P | P | - | - |
| 17 | lemn | posit | F | F | F | exc 5.90/5.0, tilt>60 1.1s/0.2s (max 129), osc pqr (q 60/51 win), hRMS 0.481/0.3, alt 0.218/0.1 | - |
| 18 | lemn | posit | F | P | P | - | - |
| 19 | lemn | posit | F | F | P | exc 5.48/5.0 | - |

Totals: V1 0/20 PASS; V2 4/20 (04, 10, 16, 18); V3 12/20 (fails 02, 03, 05, 07, 08, 09, 13, 17). All 20 g3_done validity true, no problems.
Not applied (g3_done.json not_applied): g4_typical_noise (hook missing) in ALL 20; tel_frozen in 03 and 11 (hook missing). Everything else applied.
run_validity.py is a library (no CLI): its result is the g3_done.json `validity` block (params + indi_status rate), not a plant-factor check.

## Findings
A. Excursion LOC clause is a scenario artifact: o1_lemniscate has ax=5.0 m, the setpoint itself reaches exactly 5.00 m from the hold-point reference
(measured on trajectory_setpoint, runs 0-19 except 17), so truth reaches 4.9-6.8 m and the 5 m rule trips on 16/17 lemniscate runs. Test defect
(class a, stand-in scenario), not controller. Run 17 setpoint excursion 18.55 m: it flipped (tilt 129 deg), a real LOC.
B. Chatter clause: sustained on all 4 motors in all 20 runs (known Q14), including the 3 stick runs.
C. Real candidates (V3 fails): oscillation p,q,r in 03 (G1 pitch/yaw 1.89, tau 2.79), 07 (G1 pitch 1.75, asym 2.27, delay 3.75 ms), 13 (G1 1.66/1.11/1.46, sag 0.91,
weak 0.94), 17 (tau 2.28, asym 2.41, mass 1.30, drop 0.20); q only in 08 (tau 0.58, delay 5 ms, G1 pitch 0.53, vib 4.7). Pattern: high controller G1 and/or slow tau with
asymmetry, i.e. high loop gain over actuator lag. Steady-state: 02 hRMS 0.69 (G1 roll 0.49, pitch/yaw ok, wind 4.7/8.4, loss on, GNSS 226/131), 05 hRMS 0.60
(sag 0.83, vib 4.2, GNSS 186/102 mismatched), 09 hRMS 0.34 (peak 8.0, vib 4.0), 03/07/17 alt -0.27/-0.102/-0.22 (calm limit 0.10, no sag drawn; 07 marginal).
Candidate explanations only; no draw-restore re-fly done (gate failure rule not executed).
D. Scenario mix. Code: g3_sample.py:58 `MODE_MIX = (("position", 0.70), ("stabilized", 0.20), ("acro", 0.10))`; decode() lines 240-245 take the cumulative sum
(`acc += p; if u["mode"] < acc - 1e-12: mode = name`); g3_run.py:81-86 maps position -> o1_lemniscate, else stick_zsine_o6. g3_draw.json mode field: 17 position,
2 stabilized (10, 16), 1 acro (04), consistent with the scenario in each run.json: no mapping collapse. 3/20 stick vs expected 6: P(<=3 of 20 at p=0.3) = 0.107,
LHS over 240 points is not stratified on the first 20 rows. Not a defect on this evidence. Side effect: campaign corners C2, C3, C4, C6 pin thrust/wind dims and force
position (g3_sample.py:101,358-361), so the campaign stick share is about 0.3 x 260/300 = 26 %, below 30 %. Stick runs also draw no sag, weak motor, saturation or wind (:246-259).

## UNVERIFIED
- Windows are a 3 s post-event hold, not the gate's last 10 s of a 20 s hold; item 3 values are indicative only. Items 4 (tracking RMS), 5 (recovery), 6 (rate RMS acro) not computed by g3_checks.
- acro run 04 is checked with --mode attitude (roll/pitch mean); the gate defines no acro attitude check.
- g1_ctrl_mult shows 0.42-0.49 in runs 04, 18, 02: I assume it is err x plant inertia compensation (range of g1_err 0.5-2 not re-derived); not checked in g3_sample.py.
- Time-base offset (ulog start_timestamp) is my correction; g3_checks.py docs say seconds since start_timestamp, metrics.json window is px4 clock.
- Whether "applied" in g3_done means physically effective in gz was not checked beyond the not_applied list.
