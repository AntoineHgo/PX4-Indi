# INDI v0: filter synchronisation, in-loop G1, and the yaw noise path (session 7)

Data: `indi_v0` (defaults G1 R/P/Y 320/210/30, K 20/20/10, ACT_TC 0.02 s),
gz_x500, seed 1, speed 1; runs `results/runs/{hover,step_roll,step_pitch,step_yaw}/indi_v0/seed1`.
Tool: `bench/check_sync.py` (span 10 samples = 40 ms; per-run output in `sync.json`).
One seed: diagnostic, not a benchmark result.

## 1. Synchronisation

On each excited axis the lag of best fit between filtered acceleration
increments and filtered modelled torque increments is 0 or +1 controller cycle
(4 ms). The `H` filter on the actuator model is in step with the gyro
derivative chain, as designed (architecture sec. 5). No change needed.

## 2. In-loop effectiveness

| axis | scenario | G1 fit | R^2 | v0 default |
|---|---|---|---|---|
| roll | step_roll | 237 | 0.94 | 320 |
| pitch | step_pitch | 245 | 0.95 | 210 |
| yaw | step_yaw | 7.2-7.6 (span 1-50) | 0.52-0.87 | 30 |

Roll and pitch now agree within 3 %, as they should on the symmetric x500.
This explains the "known problem" of the session-5 open-loop identification
(321 vs 211): that fit used PID logs and a re-simulated actuator/filter
model with a free time constant; the in-loop fit uses the controller's own
filtered torque. Unexcited axes (R^2 < 0.3) are ignored. With single-sample
increments the fit is noise-dominated and biased low (roll 183, R^2 0.68).

Yaw: a two-regressor fit with a rotor-inertia term (G2 * d t_f/dt) gives
G1 7.16, G2 0.05, R^2 unchanged (0.53): the G2 term is not identifiable from
this run. The x4 overestimate of G1_Y in v0 means the yaw increments were 4x
smaller than designed.

## 3. Control effort: the yaw noise path (surprise, explained)

| scenario | motor-rate RMS (1/s) INDI v0 | PID default | motor saturation frac INDI / PID |
|---|---|---|---|
| hover | 0.300 | 0.037 | 0 / 0 |
| step_roll | 0.425 | 0.528 | 0 / 0 |
| step_pitch | 0.504 | 0.532 | 0 / 0 |
| step_yaw | 2.90 | 0.569 | 0.138 / 0.044 |

Hover, torque setpoint over 20 s: roll/pitch torque std 0.0002 for both
controllers; yaw torque std 0.0015 (INDI) vs 0.0002 (PID), spectral peak
35 Hz, sample-to-sample std 0.0012. The yaw increment std (0.0018) equals
std(a_f,yaw)/G1_Y = 0.048/30: the filtered yaw acceleration noise passes
straight to the yaw torque with gain 1/G1_Y. PID has no yaw D term and
applies `MC_YAW_TQ_CUTOFF` to its yaw output; INDI cannot apply that output
filter without breaking synchronisation (architecture sec. 3).

Consequence: with the identified G1_Y = 7.4 the yaw noise gain becomes 4x
larger. Because yaw effectiveness is small (drag torque), yaw is INDI's
noise-amplification weak point; the step_yaw saturation (14 % of the time,
9 % of samples torque not achieved) follows from the same path.

Remedy chosen: D-yawfilt in `DECISIONS.md`.

Step tracking with v0 (for the record, one seed): pitch attitude RMS 3.32 deg
vs 3.35 (PID); yaw attitude RMS 11.9 vs 13.9 deg, overshoot 0.1 % vs 24 %,
settle 0.75 s vs 2.4 s, at 5x the motor-rate effort.
