# Why INDI's hover motor-rate effort is ~2x PID (owner investigation, 2026-11-15)

Complements `results/v3_hover_effort.md` (session 47: ~2x on clean seeds, inherited from v2, not caused by the
blend). Analysis only, no new flight: v2 seen-set hover logs (`results/s2_seen_v2/runs/hover`, seeds 1 and 5, spectra
also seed 6; pid_tuned, pid_default, indi_v2), window = metrics.json window. Scripts in `bench/`:
`hover_effort_split.py`, `accel_gain.py`, `gt_accel_bands.py`, `erpm_torque_resid.py` (run nice, one process).

## 1. Where the excess is

Motor-rate RMS split into motor modes (1/s):

| run | total | roll | pitch | yaw | collective |
|---|---|---|---|---|---|
| pid_tuned s1 | 0.0275 | 0.0206 | 0.0178 | 0.0025 | 0.0040 |
| pid_tuned s5 | 0.0210 | 0.0145 | 0.0131 | 0.0021 | 0.0076 |
| indi_v2 s1 | 0.0441 | 0.0321 | 0.0292 | 0.0029 | 0.0073 |
| indi_v2 s5 | 0.0438 | 0.0320 | 0.0294 | 0.0027 | 0.0051 |

The excess is roll/pitch differential; yaw and collective are equal. Roll torque-setpoint band RMS (seed 1):

| band (Hz) | 0-2 | 2-10 | 10-30 | 30-80 | 80-250 |
|---|---|---|---|---|---|
| pid_tuned | 0.00011 | 0.00022 | 0.00006 | 0.00006 | 0.00004 |
| indi_v2 | 0.00012 | 0.00034 | 0.00021 | 0.00015 | 0.00004 |

Weighting each band by its centre frequency (the metric is a time derivative), ~75 % of INDI's excess comes from
30-80 Hz, ~20 % from 10-30 Hz, a few % from below 10 Hz.

## 2. Cause 1 (dominant): angular-acceleration feedback at gain 1/G1

- 30-80 Hz: estimated angular acceleration (`xyz_derivative`) is the same for both controllers (0.016-0.018 rad/s^2
  band RMS) and ground truth there is ~0 (gt logged at 59 Hz, aliasing makes this indicative): it is gyro + rotor
  vibration noise through the shared derivative filter, identical input for both controllers.
- Regression of band-passed torque setpoint on band-passed acceleration (`accel_gain.py`), torque per rad/s^2:

  | | 10-30 Hz | 30-80 Hz |
  |---|---|---|
  | pid_tuned (s1, s5) | 0.0033-0.0036 | 0.0033-0.0036 |
  | pid_default (s1) | 0.0042 | 0.0043 |
  | indi_v2 (s1, s5) | 0.0059-0.0067 | 0.0065-0.0072 |

  INDI's law fixes this gain at 1/G1 = 0.0057 (plus a small nu contribution); PID's D (0.0024 tuned) is a tuned
  parameter that the tuning kept low. Same noise x ~2x gain = the excess. INDI's increment above 10 Hz is entirely
  `a_f/G1`; `nu` has no content there, the measured torque `t_f` little.
- Structural: no INDI gain reduces it. Only filtering does; `IMU_DGYRO_CUTOFF` is shared with PID, so a fair fix is an
  INDI-only low pass applied synchronously to a_f and to the actuator state (phase-margin cost), a firmware change.

## 3. Cause 2 (secondary, v2-specific): eRPM quantisation in the measured actuator state

- At hover (~7350 rpm) each motor's eRPM telemetry takes only 3-4 distinct values, step 14-29 rpm (14 poles, eRPM/100
  rounding, integer division by pole pairs, D-erpm); the whole measured rpm std (13.5 rpm) is about one step. One step
  on one motor is ~0.4-0.8 % of hover u = omega^2, ~0.002 normalised torque, ~5x the hover torque-setpoint std.
- `erpm_torque_resid.py`: in 0.5-10 Hz the measured torque has 1.5-2x the band RMS of the commanded torque, and the
  residual against a first-order model of the command is as large as the command itself. INDI adds t_f to the
  command with gain 1 (v3's blend keeps the measurement for the high frequencies, so it does not remove this).
- Ground truth (`gt_accel_bands.py`): INDI's true roll angular acceleration is 5-12x PID's in 4-10 Hz, falling to ~2x
  by 25 Hz: real airframe shaking. Body-rate std (1.2x, session 47 note) hides it; so "command noise, not body
  motion" is only true above ~30 Hz. It weighs little in the effort metric (low frequency).
- NOT yet causal: correlation only. Test below.

## 4. Test to fly (not flown: V' validation was flying)

Hover (T1), speed 1, v2 sim config, seeds 1-3, side by side: `indi_v2`, `indi_v2` + `MC_INDI_W_MAX 0` (measured torque
unused, model state; check `indi_rate_status.measured_torque_in_use` = 0), `pid_tuned`. Prediction: effort drops only
slightly (cause 1 dominates) while the 4-10 Hz ground-truth acceleration excess largely disappears (cause 2). If effort
drops to ~PID, cause 2 is larger than estimated here.

## 5. Consequence

V' criterion 4 (hover effort <= 1.5x pid_tuned) fails for every v3 config (~2x) and gain tuning cannot fix cause 1.
Options: an INDI-only synchronous low pass (firmware, screened under O-12), or report the criterion-4 failure as a
structural INDI cost on this sensor noise. Decide before freezing indi_v3.
