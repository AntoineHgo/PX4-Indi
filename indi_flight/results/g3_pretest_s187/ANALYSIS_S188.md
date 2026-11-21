# G3 pre-test Q22 re-fly, analysis (S188)

Analysis and re-scoring check only, no flights. Draws: `g3_sample.campaign(173, 300)` idx 0-19, Q22 box. All 20 flights ok (g3_outcome ok, rc 0, 1 arm attempt).

## Was a re-score needed? No
SCORE_KEY1/2 come from `g3_score.sh` (via `g3_score_docker.sh`) and `g3_checks_key2.py`, run 20:44-20:45 on 2026-11-21. The scorer files date 18:51/18:55 and are unchanged since commit 5396d88bd2 (D-G3-ZREF, last of the S186 fixes: excursion vs setpoint, item 2 without chatter, pid validity, item 3 on window + setpoint). The rescore_v4/v3 "scripts" are those same two scorers (the dirs are outputs). Flags are the S186 ones: per-run `--t0 --t1 --mode [--wind] [--sag]` from run.json/metrics.json/g3_draw.json (window = last 3 s "hold", hold end - 3 s), key 2 fed the same args plus `--out`. Same hold-end window rule, same derivation. Hence `rescore_s188/` was not created. UNVERIFIED: no bit-identical re-run was done (I did not re-execute the scorer).

## Result
Key 1: 10 pass / 10 FAIL (000, 002, 003, 005, 008, 009, 010, 013, 016, 017). Key 2: same 10 FAIL. Keys agree on overall and on items 1/2/3 for all 20 runs (differences only in the axes listed for run 16: key 1 p,q; key 2 p). Item 1 (LOC): 20/20 pass. Item 3: fails only on 002 and 005. Item 2: fails on all 10. The pre-test is NOT clean: 10 failures to explain, see below.

## Per run (e roll/pitch/yaw; tau up/down scale; delay = total ms loop delay; faults: tl telemetry loss, tf frozen, sag thrust scale, wm weak motor; lat/drop = telemetry latency frames / dropout prob; vib = multiplier; gnss ms; wind steady+gust peak m/s; verdicts = items 1,2,3 then item-2 axes; S186 = overall key1/key2 of same index at the S173 draw)
| run | mode | e r/p/y | tau up/dn | dly | mass; I x/y/z | faults | lat/drop | vib | gnss | wind | key 1 | key 2 | agree | S186 K1/K2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 00 | pos | 1.00/0.88/1.03 | 0.50/0.79 | 7.5 | 1.22; 0.74/0.98/0.80 | wm | 3/0.13 | 1.2 | 152 | 3.4+6.9 | PFP pq | PFP pq | y | P/P |
| 01 | pos | 0.84/0.99/0.89 | 0.50/0.92 | 8.75 | 0.85; 1.17/1.12/0.80 | - | 1/0.00 | 1.5 | 86 | 0.7+7.7 | PPP - | PPP - | y | P/P |
| 02 | pos | 0.84/1.01/1.17 | 0.56/1.31 | 1.25 | 1.11; 1.19/1.02/1.04 | tl,sag 0.94 | 3/0.00 | 3.2 | 226 | 4.7+8.4 | PFF q | PFF q | y | F/F |
| 03 | pos | 0.89/1.19/1.12 | 2.43/2.79 | 1.25 | 0.75; 0.99/1.02/0.84 | tf | 1/0.00 | 1.2 | 168 | 2.2+3.8 | PFP q | PFP q | y | F/F |
| 04 | acro | 0.84/0.82/0.83 | 0.88/1.93 | 10 | 0.94; 1.22/1.09/1.20 | - | 3/0.00 | 2.6 | 170 | 0.0+0.0 | PPP - | PPP - | y | P/P |
| 05 | pos | 0.83/0.99/0.90 | 0.77/1.41 | 0 | 1.19; 0.98/1.22/0.82 | sag 0.83 | 1/0.08 | 4.2 | 186 | 2.1+3.3 | PFF pq | PFF pq | y | F/F |
| 06 | pos | 0.87/0.91/1.16 | 0.59/0.69 | 1.25 | 1.05; 1.05/1.24/1.10 | wm | 0/0.00 | 1.9 | 219 | 0.0+3.9 | PPP - | PPP - | y | P/P |
| 07 | pos | 0.98/1.16/0.93 | 0.60/1.36 | 7.5 | 1.14; 0.84/1.02/1.01 | - | 2/0.02 | 3.4 | 123 | 2.8+4.0 | PPP - | PPP - | y | F/F |
| 08 | pos | 0.86/0.88/0.98 | 0.50/0.58 | 10 | 0.84; 0.75/1.30/0.85 | sag 0.80 | 2/0.00 | 4.7 | 107 | 0.6+6.5 | PFP q | PFP q | y | F/F |
| 09 | pos | 1.07/0.99/0.87 | 1.22/1.69 | 0 | 0.99; 0.95/1.28/0.79 | wm | 2/0.00 | 4.0 | 154 | 0.9+8.0 | PFP p | PFP p | y | F/F |
| 10 | stab | 1.10/1.08/0.95 | 0.81/1.08 | 3.75 | 1.18; 0.77/0.78/0.71 | tl | 2/0.13 | 2.0 | 248 | 0.0+0.0 | PFP pq | PFP pq | y | P/P |
| 11 | pos | 1.06/1.03/0.83 | 0.50/0.99 | 8.75 | 0.82; 1.16/0.76/0.92 | tl,tf,wm | 1/0.00 | 1.8 | 245 | 2.8+8.5 | PPP - | PPP - | y | P/P |
| 12 | pos | 1.16/1.13/0.97 | 0.50/0.54 | 8.75 | 0.99; 1.21/1.01/1.12 | - | 2/0.12 | 1.8 | 176 | 4.9+8.1 | PPP - | PPP - | y | P/P |
| 13 | pos | 1.15/1.00/1.00 | 0.57/1.40 | 5 | 1.11; 1.05/0.97/0.74 | sag,wm 0.91 | 1/0.00 | 3.0 | 119 | 1.1+3.7 | PFP p | PFP p | y | F/F |
| 14 | pos | 0.89/1.02/0.82 | 0.72/1.26 | 5 | 1.12; 0.80/1.22/0.72 | tl,sag 0.90 | 1/0.00 | 3.8 | 120 | 2.6+4.6 | PPP - | PPP - | y | P/P |
| 15 | pos | 1.05/0.93/0.93 | 0.50/0.57 | 5 | 0.92; 0.84/1.18/0.83 | sag 0.94 | 2/0.00 | 2.1 | 190 | 1.1+3.8 | PPP - | PPP - | y | P/P |
| 16 | stab | 0.95/1.09/1.11 | 0.50/0.84 | 5 | 1.16; 1.19/0.97/0.92 | - | 0/0.00 | 1.9 | 203 | 0.0+0.0 | PFP pq | PFP p | y | P/P |
| 17 | pos | 0.93/1.11/1.14 | 0.95/2.28 | 1.25 | 1.30; 0.98/1.23/1.19 | - | 2/0.20 | 3.0 | 201 | 3.0+7.6 | PFP pq | PFP pq | y | F/F |
| 18 | pos | 0.80/0.81/1.10 | 0.53/1.28 | 6.25 | 0.74; 1.17/1.23/0.93 | wm | 2/0.00 | 1.1 | 209 | 3.0+6.3 | PPP - | PPP - | y | P/P |
| 19 | pos | 1.17/1.01/1.12 | 0.50/1.06 | 5 | 0.79; 1.08/1.26/0.92 | - | 1/0.04 | 1.8 | 207 | 1.3+4.1 | PPP - | PPP - | y | P/P |

S186 (old draws, e up to 2, tau up to 3, asym to 3) failed (both keys) on 002, 003, 005, 007, 008, 009, 013, 017; the other 12 passed (000, 010, 016 passed there and FAIL now; 003, 007, 013, 017, 009 changed cause or recovered item 3).

## Classification of the 10 failures (all item 2, p/q rate oscillation; 002 and 005 also item 3)
Detector lines (f Hz, start s after airborne start; traj/wind/faults start about 22.9 s after airborne start, hold 40.7 s, land about 48 s; key 2 skips the first 7 windows and still fails every one of these runs, so the early lines are not a take-off transient artefact):
- A. Early, pre-trajectory (no wind or injected fault yet, only plant/noise factors): 000 (p,q 3.25/2.75 Hz from 1-4 s, 15 dps; again 2.5 Hz at 39 s), 005 (4.5 Hz from 3 s, 19 windows, 12 dps), 010 stabilized (5.5 Hz from 3 s, 12 windows, 7 dps), 016 stabilized (7.25 Hz from 2 s, 11 windows, 6 dps; q 6.75 Hz 5.3 dps), 017 (2.5-3.0 Hz from 0-5 s, 17 windows, 16 dps). Frequencies 2.5-7.3 Hz are rate-loop band, well above the attitude crossover (1.2-1.3 Hz).
- B. Started at trajectory start or at a fault: 002 (q 2.0 Hz from 24 s, faults tel_loss at +4.9 s, sag 0.94, wind 4.7+8.4), 003 (q 2.0 Hz from 27 s, tel_frozen at +1.5 s, slowest motors tau 2.4/2.8), 008 (q 10.75 Hz from 24 s, 14 windows, sag 0.80, tau 0.50/0.58, delay 10 ms, Iyy 1.30), 009 (p 2.75 Hz at 24 s, 5 windows, 8 dps, weak motor 0.99), 013 (p 2.75 Hz at 33 s, 3 windows, 7.7 dps, sag 0.91 + weak motor 0.94). All are short (3-18 windows) except 008.
- Item 3 (002: 0.53 m, 005: 0.45 m horizontal rms, limit 0.3): both runs with thrust sag (0.94, 0.83) and wind, together with a sustained p/q line during the trajectory (002 q 2 Hz, 005 p,q 4.5 Hz); 008, 013 have sag and pass item 3, so sag alone does not do it.
Common factors: no single corner. Failing and passing runs overlap on tau_up 0.5 (fail 000, 008, 016; pass 001, 011, 012, 015, 019), on e (all within 0.8-1.2, failing e spans the box), on dropout (fail 000/005/010/017; pass 012, 019, 007) and on faults (8 of 10 failing have one; pass: 006, 011, 014, 015, 018). Weak commonality: telemetry latency 2-3 frames in 6 of 10 failing (000, 002, 008, 009, 010, 017) vs 5 of 10 passing (weak), mass/inertia nothing visible. Fast-motor corner (tau_up 0.50-0.57) with a delay: 000, 008, 013, 016 fail. Nothing singles out a factor at n=20.
Model prediction: results/g3_box_s187/margins_tables.md gives attitude PM 45-75 deg and rate PM 53-86 deg for all 20 draws, i.e. the linear model predicts all 20 stable. The lowest attitude PM are run 3 pitch (45/49) and run 17 pitch (57/64), both fail (q 2.0 Hz and p,q 3 Hz, plausible partial hit); the others fail at PM 67-78 (000 72, 005 67, 008 74, 010 68, 016 71), so the model does not predict them. The fast-motor corner table (e 0.8, tau 0.5, 10 ms: rate GM 4.2 dB at 7.6 Hz) matches the frequency of 016 (7.25 Hz) and 008 (10.75 Hz) qualitatively but its margins are positive. The linear model misses these (not modelled: dropout, vibration/noise, GNSS delay, 3 s hold, nonlinearities). The S186 osc-margin result (att PM<15 predicts OSC) does not apply: no draw has PM<15 in the Q22 box, yet 10 fail.

## Scorer / set-up artefact suspects
- No window misplacement: key 1 hold window and key 2 window both lie in the final 3 s hold (run.json hold dur 3.0 s, window on ulog clock); all 20 g3_outcome ok, signals present, skipped_windows 0 (key 1). Key 1 and key 2 clocks differ by about 13.9 s (key 1 window 62.0, key 2 75.8 for run 0), same as in S186 rescore_v3/v4; UNVERIFIED that key 2 maps the args to the same instant (verdicts and rms agree to 1e-4, so it does).
- Item 2 is whole flight incl. take-off and descent, so faults outside the 3 s window are in scope by definition.
- Borderline amplitudes vs RMS_DEG_S = 5.0 dps: 016 (p 6.0, q 5.3 dps, min 3 windows), 010 (6.8), 013 (7.7), 009 (8.3). Detection threshold sensitive: 016 and 013 would flip with a modest threshold change. Not an artefact but weak evidence.
- Hold is 3 s instead of the spec 20 s (stand-in deviation): the position limit-cycle test is not evaluated (hold < 10 s in key 2). Item 3 after a lemniscate is a tracking error, partly transient (002, 005).
- Run 003 and 017: oscillation A/B at the same time as S186; plausible genuine.
No run shows a missing signal or fault outside the window. No evidence for a scorer artefact beyond the borderline amplitudes.

## PID reference candidates (same draw, same seed; not flown)
Decide INDI-specific vs plant-specific. Priority 1 (cleanest, no wind or fault pollution): 010, 016 (stabilized), 000, 005, 017 (early line before any fault). Priority 2: 002, 003, 008, 009, 013. Passing runs need no reference. (The S185 PID ref of run 17 used the old draw, tau 2.28/2.41, so it does not cover the new draw 17.)
How S185 flew it: `g3_run.py` has no `--controller` option (module constant `CONTROLLER = "indi"`). The driver is results/g3_pretest_s173/run_017_pid_s185/fly_pid_run017.py: sets `g3_run.CONTROLLER = "pid_default"`, rebuilds the draw with `g3_run.build_run(d, BASE, out)` (BASE = `<argv1>/pid_base.params`, a base param file without MC_INDI_*/MC_RATE_CTL_TYPE; not found in the repo, UNVERIFIED how it was made, presumably results/g5_freeze_s157/params.params minus those keys), then runs `indi_project/docker/run.sh -n pid173_17 -t 1000 -- python3 indi_flight/bench/run_scenario.py --scenario ... --controller pid_default ...` and `g3_run.finalize`. For the new batch copy it, set `idx`, `campaign(173, 300)`, `out = indi_flight/results/g3_pretest_s187/run_0NN_pid_s188`, container `pid187_NN`, drop the S173 draw assert, and run `python3 fly_pid.py <dir with pid_base.params>` per index; score with `g3_score.sh`-style args (`--t0 --t1 --mode --wind --sag` from the INDI run's args in SCORE_KEY1.txt) and `g3_checks.py` / `g3_checks_key2.py`. Serial only, never during another batch.
