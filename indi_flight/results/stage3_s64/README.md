# S64: G4 pre-look, setpoint-lead derivative (r_dot_f) noise and motor effort

Same build and command as `../g2_step_s64/README.md` (HEAD 360c9ae453), seed 1. A/B: `indi.params` (MC_INDI_LEAD 1,
default) vs `indi_lead0.params` (MC_INDI_LEAD 0: removes both the feedback lead and the setpoint lead; no parameter
isolates the setpoint lead). Script: `python3 bench/rdot_effort_s64.py results/stage3_s64/effort.md results/stage3_s64/{hover,rate_step_roll}_lead{1,0}/run`
(self-test `--selftest`; single key, pre-look only, not a gate metric). HF = deviation from a 0.25 s boxcar mean.

| flight | r_dot RMS r/p rad/s^2 | lead term HF RMS (r) | torque_sp HF RMS (r) | motor cmd HF RMS | rpm HF RMS |
|---|---|---|---|---|---|
| hover lead 1 | 0.036 / 0.032 | 1.3e-5 | 5.3e-5 | 2.7e-4 | 7.8 |
| hover lead 0 | (0.067 / 0.057, unused) | 0 | 7.1e-5 | 2.7e-4 | 8.0 |
| rate pulses lead 1 | 8.4 / 0.15 | 4.5e-3 | 6.1e-3 | 4.5e-3 | 66 |
| rate pulses lead 0 | (8.4, unused) | 0 | 2.4e-3 | 1.9e-3 | 45 |

Reading: in hover the setpoint-lead term carries no measurable noise into the motors (motor HF RMS 2.7e-4 of full
scale either way, rpm ripple 7.8 vs 8.0). In the rate pulses (acro-like, clean steps) the lead adds HF motor content
(4.5e-3 vs 1.9e-3 of full scale, 0.45 % peak-free RMS): this is the step feed-forward itself, not noise, since the
SITL rate setpoint has no stick noise. Open for G4: a real RC stick is quantised and sampled at 50-250 Hz; its
derivative reaches r_dot through a 10 ms low pass. The G4 acro case must include a stick-noise/quantisation model
(build item, see `design/gates_g3_g8_draft_s64.md`) before r_dot_f in acro is closed.
