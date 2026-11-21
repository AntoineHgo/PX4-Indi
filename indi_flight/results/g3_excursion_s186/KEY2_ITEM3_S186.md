# KEY2 item 3 (steady state) re-implemented from the written spec (S186)

## Spec read
GATES.md G3 "Pass per run" item 3 and the shared definition "Steady-state window: last 10 s of a hold >= 20 s after the last transient, truth":
horizontal RMS <= 0.15 m calm, <= 0.30 m with wind or gust; altitude |mean| <= 0.10 m calm, <= 0.20 m with sag or weak motor;
roll/pitch |mean| <= 1.0 deg in attitude mode; yaw excluded. score.sh supplies window (--t0/--t1, seconds since ulog start_timestamp,
the pre-test stand-in is the final 3 s hold segment), --mode, --wind (position runs with wind or gust), --sag (sag, weak motor or saturation).

## Ambiguities (chosen from the spec text, not from key 1)
1. Hold point not defined in the spec. Chosen: the commanded hold, i.e. logged trajectory_setpoint x, y (and z for altitude), linearly
   interpolated onto each truth sample in the window (same interpolation rule as key-2 item-1 excursion, GATES item 1 uses "reference").
   Old key 2 used the truth median of the first second of the hold: wrong for the lemniscate runs (the vehicle is still moving there).
2. Altitude reference: altitude error = mean(truth height) - mean(-setpoint z). Truth height is referenced to the initial truth z
   (median of first 800 samples), setpoint z to the estimator origin: any origin offset between them (observed 5 mm) enters directly.
   Spec silent; this is the only residual disagreement with key 1 (see run_007).
3. Attitude mode: no position setpoint exists. Horizontal and altitude are NOT gated (reported about the window truth mean / 0);
   only roll/pitch is gated. Strict reading (horizontal and altitude gated in all modes) cannot be evaluated without a reference.
   Roll/pitch is gated only in attitude mode (spec wording); in position mode it is reported.
4. Wind and sag limits treated as independent (horizontal limit from --wind, altitude limit from --sag); old key 2 tied both to wind.
5. Wind flag semantic ("wind or gust") taken from the command line as given.

## Change (bench/g3_checks_key2.py)
New `steady_state()` and `interp_sp()`; `analyse()`/`load_run()` take window, mode, wind, sag; CLI accepts `--t0 --t1 --mode --wind --sag`
(window on the ulog start_timestamp clock). Without --t0/--t1 the window is the last 10 s of the run.json hold. Items 1, 2, chatter untouched.

## Test
`--self-test`: all 11 old cases and 6 new item-3 cases pass (known hold point (3,-2, 10 m) + offset (0.3,0.4,0.15) gives RMS 0.5000 and
altitude error 0.1500; limits depend on wind/sag independently; offset outside the window and 5 m pre-window displacement ignored).
bench/tests/test_g3_excursion_key2.py functions called directly: pass. scipy not needed by key 2.

## Result (results/g3_excursion_s186/rescore_v3/key2/, args from key1/args.txt)
rescore_v3/key2_invalid_args_dropped/ is a first run where the shell did not word-split the args (kept, invalid, ignore).

| run | mode | key1 hRMS / alt (m) | key2 hRMS / alt (m) | key1 / key2 verdict | agree | abs diff hRMS, alt |
|---|---|---|---|---|---|---|
| run_000 | position | 0.200 / -0.061 | 0.200 / -0.056 | P / P | yes | 0.0000 0.0050 |
| run_001 | position | 0.278 / -0.011 | 0.278 / -0.006 | P / P | yes | 0.0000 0.0050 |
| run_002 | position | 0.692 / -0.104 | 0.692 / -0.099 | F / F | yes | 0.0000 0.0050 |
| run_003 | position | 0.450 / -0.273 | 0.450 / -0.268 | F / F | yes | 0.0000 0.0050 |
| run_004 | attitude | 0.002 / -0.000 | 0.002 / +0.000 (ungated) | P / P | yes | 0.0000 0.0000 |
| run_005 | position | 0.603 / -0.086 | 0.603 / -0.081 | F / F | yes | 0.0000 0.0050 |
| run_006 | position | 0.207 / -0.049 | 0.207 / -0.044 | P / P | yes | 0.0000 0.0050 |
| run_007 | position | 0.232 / -0.102 | 0.232 / -0.097 | F / P | NO | 0.0000 0.0050 |
| run_008 | position | 0.082 / -0.040 | 0.082 / -0.035 | P / P | yes | 0.0000 0.0050 |
| run_009 | position | 0.344 / +0.003 | 0.344 / +0.008 | F / F | yes | 0.0000 0.0050 |
| run_010 | attitude | 0.001 / +0.000 | 0.001 / +0.000 (ungated) | P / P | yes | 0.0000 0.0000 |
| run_011 | position | 0.138 / +0.111 | 0.138 / +0.116 | P / P | yes | 0.0000 0.0050 |
| run_012 | position | 0.102 / +0.022 | 0.102 / +0.027 | P / P | yes | 0.0000 0.0050 |
| run_013 | position | 0.150 / -0.103 | 0.150 / -0.098 | P / P | yes | 0.0000 0.0050 |
| run_014 | position | 0.192 / -0.025 | 0.192 / -0.020 | P / P | yes | 0.0000 0.0050 |
| run_015 | position | 0.222 / -0.062 | 0.222 / -0.057 | P / P | yes | 0.0000 0.0050 |
| run_016 | attitude | 0.008 / +0.000 | 0.008 / +0.000 (ungated) | P / P | yes | 0.0000 0.0000 |
| run_017 | position | 0.481 / -0.218 | 0.481 / -0.213 | F / F | yes | 0.0000 0.0050 |
| run_017_pid_s185 | position | 0.091 / -0.039 | 0.091 / -0.034 | P / P | yes | 0.0000 0.0050 |
| run_018 | position | 0.135 / +0.015 | 0.135 / +0.020 | P / P | yes | 0.0000 0.0050 |
| run_019 | position | 0.239 / -0.010 | 0.239 / -0.005 | P / P | yes | 0.0000 0.0050 |

Item 3 verdict agreement: 20 of 21. Largest differences: horizontal RMS 0.00005 m, altitude mean 0.0050 m (constant on every position run),
roll/pitch mean 0.012 deg. The single disagreement, run_007: altitude mean key1 -0.102 (F, limit 0.10) vs key2 -0.097 (P), pure origin offset of ambiguity 2.
Roll/pitch columns omitted from the table; they agree within 0.012 deg (key 1 roll/pitch is gated only in attitude mode in both keys).
