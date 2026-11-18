# S100 G2 rate-loop margins, model-only actuator state (2-flight pre-test)

## Recipe
- Base: S99 `g2_rate_batch_s99` params (`params_pitch.params`, `params_yaw.params`), hover_long, indi_m3a, quad5in, `--sim v2`, speed 4, seed 1, ACT_TC 0.05, lead 1, G2_Y 27, bins 1-60 Hz, DLY 20, NP 3.
- Only change: `CA_R_W_MAX 2700` replaced by `CA_R_W_MAX 0`.
- Flights: P400 = pitch (MC_INDI_INJ_AX 2), 400 Hz, seed 1. Y800 = yaw (MC_INDI_INJ_AX 3), 800 Hz, seed 1. Run serially (as the S99 batch did).
- Script: `fly.sh` (per-axis params; the S99 pretest script pointed at non-existent `P1.params`, so it is not reused as-is).

## Model-only selection
- Parameter: `CA_R_W_MAX 0`. `run_scenario.py` (~line 710) renames it to `MC_INDI_W_MAX`, so the sim sets `MC_INDI_W_MAX 0`.
- Why: `MC_INDI_W_MAX` (yaml: "Zero disables the measured torque, INDI then uses its actuator model") is the only switch for the ESC-rpm measured torque path. Old measured recipe `meas800.params` sets `CA_R_W_MAX 2700`; `roll267b.params` has no such line. Zero is explicit and logs as 0.

## Results (margins.txt, gate.md, both PASS)
| Flight | axis / rate | GM dB | PM deg | DM s (control periods) | f_c Hz (first crossing) | bins accepted | gate |
|---|---|---|---|---|---|---|---|
| P400 | pitch 400 Hz | 10.25 | 72.4 | 0.0413 (16.5) | 4.88 | 18 / 18 (1.0-50.1 Hz) | PASS |
| Y800 | yaw 800 Hz | 18.43 | 91.0 | 0.1720 (137.6) | 1.47 | 18 / 18 (1.0-50.1 Hz) | PASS |

Gate thresholds: GM >= 6 dB, PM >= 45 deg, DM >= 2 control periods. Both flights clear all three.
Gate window: 36.0-51.0 s since boot (first airborne + 4 s, 15 s long). Rate RMS 0.0027 / 0.0024 / 0.0004 rad/s (P400) and 0.0028 / 0.0037 / 0.0004 rad/s (Y800). Motor pin 0; torque setpoint achieved 1.

## Model-only check
- `indi_rate_status.measured_torque_in_use` is 0 for every sample in both logs (P400 44360 samples, Y800 88587 samples). Logged `MC_INDI_W_MAX` is 0.0 and `CA_R_W_MAX` is absent in both.
- No `actuator_torque_measured` topic in either log. Model-only path confirmed.

## Warnings
- axis_check.txt: injection found on the intended axis in both flights (P400 pitch, Y800 yaw). The other axes print "no injection on this axis", as expected.
- Yaw crossing at f_c 1.47 Hz is low, so the yaw loop gain margin (18.4 dB) is well clear of the gate. Only the first crossing is reported above.
- Only 2 flights, seed 1 each, no repeats. Not a batch result.
- Rates: esc_status median matches the controller rate in both (400 Hz and 800 Hz); mean esc rate is 385 Hz and 766 Hz, so a few ESC frames are dropped as in S99.

## Files
- `fly.sh`, `params_pitch.params`, `params_yaw.params`, `fly_stdout.log`, `done.txt`.
- Per flight (`P400/`, `Y800/`): `s1/flight.ulg` (raw, untracked), `margins.txt`, `gate.md`, `gate_stdout.txt`, `rates.txt`, `axis_check.txt`, `s1.csv`, `stdout.log`, `post.log`.
