# Hover effort causal test (session 48, post-hoc, not part of any verdict)

Test of `results/s2_hover_effort_cause.md` sec. 4. `bench/hover_cause_test.sh`: hover (T1), speed 1, v2 sim config,
seeds 1-3, pid_tuned vs indi_v2 vs indi_v2 with MC_INDI_W_MAX 0 (measured torque unused, model actuator state), the
three controllers of a seed flown side by side, 01:30-01:35 on 2026-11-15. Tables: `python3 bench/hover_cause.py`
and `python3 bench/gt_accel_bands.py <run dirs>`.

## Motor-rate effort (motor_rate_rms_per_s)

| controller | seed 1 | seed 2 | seed 3 | mean | ratio | measured torque in use |
|---|---|---|---|---|---|---|
| pid_tuned | 0.0566 | 0.0462 | 0.0494 | 0.0507 | 1.00 | - |
| indi_v2 | 0.0425 | 0.0593 | 0.0436 | 0.0485 | 0.96 | 0.99, 1.00, 0.97 |
| indi_v2_wmax0 | 0.0552 | 0.0463 | 0.0464 | 0.0493 | 0.97 | 0.00, 0.00, 0.00 |

## Ground-truth roll angular acceleration RMS per band (rad/s^2, mean of seeds 1-3)

| band (Hz) | 0-2 | 2-4 | 4-6 | 6-8 | 8-10 | 10-12 | 12-14 |
|---|---|---|---|---|---|---|---|
| pid_tuned | 1.73 | 10.09 | 0.28 | 0.20 | 0.23 | 0.22 | 0.18 |
| indi_v2 | 1.87 | 5.38 | 2.03 | 1.47 | 1.24 | 0.96 | 0.65 |
| indi_v2_wmax0 | 1.39 | 5.32 | 0.46 | 0.63 | 0.62 | 0.51 | 0.37 |

## Reading
- **Cause 2 confirmed for body motion, not for effort.** Without the measured torque, INDI's true 4-10 Hz roll
  acceleration drops 2-4x (4-6 Hz 2.03 -> 0.46), as predicted, while its effort is unchanged (0.0485 vs 0.0493).
  The coarse eRPM state shakes the vehicle at 4-10 Hz; it is not where the motor-rate effort comes from. It still
  leaves 2-3x PID's 6-12 Hz content, the residual of cause 1 below 30 Hz.
- **The PID reference is not reproducible.** pid_tuned flew at 0.046-0.057 here, against 0.021-0.031 on the clean
  seeds of `results/v3_hover_effort.md`, with a large 2-4 Hz roll oscillation (true acceleration ~10 rad/s^2 in
  that band, about 2x INDI's) on all three seeds. The same 0.064-0.066 level appeared on seen-set seeds 3-4 under host
  overload. Load here was 3 simulations (load average ~6); its cause is not identified. On this batch the INDI/PID
  effort ratio is 0.96, so the 2x of V' criterion 4 holds only against the low-effort PID state. INDI's own hover
  effort (0.043-0.059) is the same in all batches.
- Consequence: the V' criterion-4 figure (2.14x, five seeds) stands as flown, but it compares INDI against a PID
  whose hover effort varies 2x between batches for reasons not yet found. Finding that cause (PID 2-4 Hz mode,
  likely load- or timing-dependent) comes before any claim about INDI's hover effort.
