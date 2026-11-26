# G3 pre-test S230 scores (event hover), key 1 and key 2

Scored 2026-11-26 on host python (/tmp/g3venv), same flags as g3_score.sh/g3_chain.sh (--run-json, --mode position, --wind, --sag per draw, --skip-nav-change). No key code changed. Raw outputs: raw_key1_<run>.txt/.json, raw_key2_<run>.txt, key2_<run>/run_NNN.json.

## Event timeline (run.json g3_timeline, PX4 clock)

| run | settle start s | t0 - settle | gust - t0 (spec 12) | main - t0 (spec 23) | fault_on | wind_on |
|---|---|---|---|---|---|---|
| indi_d0 | 55.651 | 3.000 | 12.000 | 23.002 | True | True |
| pid_d0 | 55.648 | 3.000 | 12.000 | 23.010 | True | True |
| indi_d262 | 55.698 | 3.000 | 12.000 | 23.010 | True | True |
| indi_d283 | 55.695 | 3.000 | 12.000 | 23.028 | False | True |

## Scores

| run | item | key 1 value | key 2 value | threshold | key 1 | key 2 | agree |
|---|---|---|---|---|---|---|---|
| indi_d0 | 1 | tilt 42.861 deg, drop 0.021 m, exc 0.661 m | tilt 42.861, drop 0.030, exc 0.661 | tilt>60 deg, ground contact, NaN, drop | PASS | PASS | yes |
| indi_d0 | 2 | rms@maxratio p/q/r 2.485/1.961/1.347 dps; sust none | max rms p/q/r 3.036/5.095/1.749 dps; sust none | no sustained rate/position oscillation; G4 chatter separate | PASS | PASS | yes |
| indi_d0 | 3 | rms 0.039 m, alt -0.022 m | rms 0.039 m, alt -0.022 m | rms<=0.3 m, |alt|<=0.2 m | PASS | PASS | yes |
| indi_d0 | 4 | horiz 0.418, vert 0.076 m | horiz 0.418, vert 0.076 m | horiz<=0.5, vert<=0.3 m | PASS | PASS | yes |
| indi_d0 | 5 | ev0: back 0.000 s, err 0.159 m; ev1: back 0.000 s, err 0.067 m | fault@t0: back 0.000 s, err 0.159 m, att 5.585 deg; gust: back 0.000 s, err 0.067 m, att 2.022 deg | back<=5 s, quiet err<=0.3 m, att<=3 deg | PASS | PASS | yes |
| indi_d0 | 6 | n/a (not rate mode) | n/a (not rate mode) | rate mode only | PASS | PASS | yes |
| indi_d0 | overall |  |  |  | PASS | PASS | yes |
| indi_d0 | g4 chatter | sustained False | sustained False |  | PASS | PASS | yes |
| pid_d0 | 1 | tilt 38.377 deg, drop 0.025 m, exc 1.345 m | tilt 38.377, drop -0.000, exc 1.345 | tilt>60 deg, ground contact, NaN, drop | PASS | PASS | yes |
| pid_d0 | 2 | rms@maxratio p/q/r 1.662/1.710/0.085 dps; sust none | max rms p/q/r 2.758/2.189/0.185 dps; sust none | no sustained rate/position oscillation; G4 chatter separate | PASS | PASS | yes |
| pid_d0 | 3 | rms 0.038 m, alt -0.011 m | rms 0.038 m, alt -0.011 m | rms<=0.3 m, |alt|<=0.2 m | PASS | PASS | yes |
| pid_d0 | 4 | horiz 0.768, vert 0.051 m | horiz 0.768, vert 0.051 m | horiz<=0.5, vert<=0.3 m | FAIL | FAIL | yes |
| pid_d0 | 5 | ev0: back 0.001 s, err 0.077 m; ev1: back 0.001 s, err 0.095 m | fault@t0: back 0.001 s, err 0.077 m, att 1.724 deg; gust: back 0.001 s, err 0.095 m, att 1.079 deg | back<=5 s, quiet err<=0.3 m, att<=3 deg | PASS | PASS | yes |
| pid_d0 | 6 | n/a (not rate mode) | n/a (not rate mode) | rate mode only | PASS | PASS | yes |
| pid_d0 | overall |  |  |  | FAIL | FAIL | yes |
| pid_d0 | g4 chatter | sustained False | sustained False |  | PASS | PASS | yes |
| indi_d262 | 1 | tilt 45.984 deg, drop 0.037 m, exc 1.826 m | tilt 45.984, drop 0.097, exc 1.826 | tilt>60 deg, ground contact, NaN, drop | PASS | PASS | yes |
| indi_d262 | 2 | rms@maxratio p/q/r 2.478/1.932/2.060 dps; sust none | max rms p/q/r 2.488/5.310/2.088 dps; sust none | no sustained rate/position oscillation; G4 chatter separate | PASS | PASS | yes |
| indi_d262 | 3 | rms 0.040 m, alt -0.070 m | rms 0.040 m, alt -0.070 m | rms<=0.3 m, |alt|<=0.2 m | PASS | PASS | yes |
| indi_d262 | 4 | horiz 0.988, vert 0.067 m | horiz 0.988, vert 0.067 m | horiz<=0.5, vert<=0.3 m | FAIL | FAIL | yes |
| indi_d262 | 5 | ev0: back 0.001 s, err 1.305 m; ev1: back 0.001 s, err 0.279 m | fault@t0: back 0.001 s, err 1.305 m, att 11.963 deg; gust: back 0.001 s, err 0.279 m, att 8.784 deg | back<=5 s, quiet err<=0.3 m, att<=3 deg | FAIL | FAIL | yes |
| indi_d262 | 6 | n/a (not rate mode) | n/a (not rate mode) | rate mode only | PASS | PASS | yes |
| indi_d262 | overall |  |  |  | FAIL | FAIL | yes |
| indi_d262 | g4 chatter | sustained True | sustained True |  | FAIL | FAIL | yes |
| indi_d283 | 1 | tilt 43.555 deg, drop 0.002 m, exc 0.770 m | tilt 43.555, drop 0.029, exc 0.770 | tilt>60 deg, ground contact, NaN, drop | PASS | PASS | yes |
| indi_d283 | 2 | rms@maxratio p/q/r 2.144/5.954/1.830 dps; sust ['q'] | max rms p/q/r 2.861/7.774/2.909 dps; sust ['q'] | no sustained rate/position oscillation; G4 chatter separate | FAIL | FAIL | yes |
| indi_d283 | 3 | rms 0.030 m, alt 0.032 m | rms 0.030 m, alt 0.032 m | rms<=0.3 m, |alt|<=0.2 m | PASS | PASS | yes |
| indi_d283 | 4 | horiz 0.485, vert 0.095 m | horiz 0.485, vert 0.095 m | horiz<=0.5, vert<=0.3 m | PASS | PASS | yes |
| indi_d283 | 5 | ev0: back 0.000 s, err 0.074 m | gust: back 0.000 s, err 0.074 m, att 1.719 deg; tel_loss: back 0.000 s, err 0.067 m, att 1.719 deg; tel_frozen: back 0.001 s, err 0.067 m, att 1.719 deg | back<=5 s, quiet err<=0.3 m, att<=3 deg | PASS | PASS | yes |
| indi_d283 | 6 | n/a (not rate mode) | n/a (not rate mode) | rate mode only | PASS | PASS | yes |
| indi_d283 | overall |  |  |  | FAIL | FAIL | yes |
| indi_d283 | g4 chatter | sustained False | sustained False |  | PASS | PASS | yes |

## Item 5 per event

| run | event | t (PX4 s) | recovery time s | max error m | att | key1/key2 | notes |
|---|---|---|---|---|---|---|---|
| indi_d0 | fault@t0 | 58.651 | K1 0.000 / K2 0.000 | K1 0.159 / K2 0.159 | K2 5.585 deg | PASS/PASS | gated True, re_exc False |
| indi_d0 | gust | 70.651 | K1 0.000 / K2 0.000 | K1 0.067 / K2 0.067 | K2 2.022 deg | PASS/PASS | gated True, re_exc False |
| pid_d0 | fault@t0 | 58.648 | K1 0.001 / K2 0.001 | K1 0.077 / K2 0.077 | K2 1.724 deg | PASS/PASS | gated True, re_exc False |
| pid_d0 | gust | 70.648 | K1 0.001 / K2 0.001 | K1 0.095 / K2 0.095 | K2 1.079 deg | PASS/PASS | gated True, re_exc False |
| indi_d262 | fault@t0 | 58.698 | K1 0.001 / K2 0.001 | K1 1.305 / K2 1.305 | K2 11.963 deg | FAIL/FAIL | gated True, re_exc True |
| indi_d262 | gust | 70.698 | K1 0.001 / K2 0.001 | K1 0.279 / K2 0.279 | K2 8.784 deg | PASS/PASS | gated True, re_exc False |
| indi_d283 | gust | 70.695 | K1 0.000 / K2 0.000 | K1 0.074 / K2 0.074 | K2 1.719 deg | PASS/PASS | gated True, re_exc False |

Item 1 and 2 thresholds are as coded in the keys (not restated numerically here); item 1 values differ only in drop (K1 uses a different height reference), both pass. Item 2 values are not comparable in definition (K1 rms at the max-ratio window, K2 max rms), the pass/fail and sustained axis agree. Item 5 recovery time is about 0 s in every event (error is already under the limit when the quiet window starts), so the gate is decided by max error.

## Plain facts

1. All four run.json carry g3_timeline; t0 = settle start + 3.000 s, gust = t0 + 12.000 s, main start = t0 + 23.002 to 23.028 s, as specified. Fault is on in indi_d0, pid_d0, indi_d262 and off in indi_d283 (draw 283 has no fault; only gust, plus tel_loss and tel_frozen that key 2 also lists).
2. Both keys agree on every item and overall for all four runs: indi_d0 PASS, pid_d0 FAIL (item 4 horiz 0.768 m vs 0.5), indi_d262 FAIL (items 4 and 5 fault@t0, G4 chatter sustained), indi_d283 FAIL (item 2 sustained q oscillation).
3. PID reference (pid_d0) item 5: PASS on both keys, fault@t0 max error 0.077 m, gust 0.095 m, recovery about 0.001 s.
4. indi_d262 fault@t0: max error 1.305 m and attitude 11.96 deg, re-excursion flagged; gust max error 0.279 m (limit 0.3), attitude 8.78 deg (listed att limit 3 deg, yet gust event scored PASS on both keys; not investigated which quantity gates).
5. indi_d0 INDI item 5: fault@t0 0.159 m (att 5.58 deg), gust 0.067 m; item 4 0.418 m and item 3 0.039 m rms pass.
