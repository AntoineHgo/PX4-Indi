# O-3/O-4 post-acceptance re-checks of the frozen v1 INDI (session 34; restated against indi_frz in session 38)

Post-acceptance: none of this changes the v1 acceptance result (`acceptance_s15.md`). v1 sim config (stock gz_x500,
FAC 0), H5 = mismatch_combined_att/_rate (plant: motor time constant x2, inertia/mass mismatch), 10 seeds, speed 4.
Runs: `results/s2_recheck_v1/runs/` (script `results/s2_recheck_v1/run.sh`). Variants: indi_tcup (MC_INDI_ACT_TC
12.5 ms = identified tau up), indi_tcdn (25 ms = identified tau down), indi_g2 (frozen + G2_Y 0.16, pending).
Frozen v1 ACT_TC is 11.42 ms.

H5 roll-rate RMS (rad/s), mean +- std over 10 seeds; v1 columns are the v1-era runs (`results/runs/`):

| scenario | PID v1 | INDI frozen v1 | indi_tcup | indi_tcdn | indi_g2 |
|---|---|---|---|---|---|
| mismatch_combined_att | 0.088 +- 0.002 | 0.340 +- 0.039 | 0.210 +- 0.018 | 0.157 +- 0.005 | 0.317 +- 0.035 |
| mismatch_combined_rate | 0.356 +- 0.004 | 0.562 +- 0.006 | 0.515 +- 0.007 | 0.425 +- 0.038 | 0.559 +- 0.006 |

Motor-rate effort vs frozen v1 (summarize_seeds, paired, 10/10 seeds lower, p 0.002): tcup 0.57x / 0.88x,
tcdn 0.33x / 0.63x (att / rate). Attitude RMS within noise of frozen v1 on att; tcdn pitch RMS 1.55x on rate.

Reading (provisional):
- A slower actuator model (25 ms, the identified spin-DOWN constant) reduces the H5 loss but does not remove it:
  INDI stays 1.8x (att) and 1.2x (rate) PID roll-rate RMS. Consistent with review s5 (model slower than plant =
  gain reduction, safe; H5 plant at 2x tau is still slower than a 25 ms model).
- CAUTION: tcup differs from frozen by only 9 % in ACT_TC yet improves roll-rate RMS by 38 % on att. The binary
  changed since the v1 runs (s19 landyaw, s29 dt-jitter, s30 landmodel/faulthold, s31 delay slew), so part of
  every variant's gain may be the binary. Same-binary control `indi_frz` is queued (`run_frz.sh`); the variant
  effects must be re-stated against it before any of this enters the report.
- indi_g2 (frozen ACT_TC 11.42 ms + G2_Y 0.16) is within ~7 % of frozen v1 on H5 (effort 1.78 / 3.61, frozen
  1.92 / 3.63): the G2 term neither causes nor cures the limit cycle. That g2 on the current binary reproduces
  the v1 numbers suggests the binary change is NOT the main cause of tcup's gain, and that H5 is very sensitive
  to ACT_TC near 11-12 ms (near a stability boundary). To be confirmed by indi_frz.
- Batch: 105 runs, 1 failure (step_yaw/indi_g2/seed3: wall timeout in climb, CPU contention at the r1f start).
- Tuning set (hover, steps): not yet analysed.

## Restated against the same-binary control indi_frz (session 38)

`indi_frz` = frozen params on the same binary (build/px4_sitl_default) as the variants, `run_frz.sh`, 0 failures.
Mean over seeds (H5: 10, tuning set: 3); rr = roll-rate RMS [rad/s], att = rotation-angle RMS [deg], eff = motor-rate
RMS [1/s]:

| scenario | frz rr / att / eff | tcup rr / att / eff | tcdn rr / att / eff | g2 rr / att / eff |
|---|---|---|---|---|
| mismatch_combined_att | 0.310±0.039 / 3.01 / 1.75 | 0.209±0.018 / 2.94 / 1.10 | 0.157±0.005 / 2.92 / 0.64 | 0.317±0.035 / 3.90 / 1.78 |
| mismatch_combined_rate | 0.564±0.006 / 19.7 / 3.63 | 0.515±0.007 / 19.2 / 3.18 | 0.425±0.038 / 20.3 / 2.28 | 0.559±0.006 / 19.7 / 3.61 |
| hover | 0.001 / 0.066 / 0.039 | 0.001 / 0.069 / 0.037 | 0.001 / 0.074 / 0.038 | 0.002 / **82.1** / 0.77 |
| step_roll | 0.139 / 2.88 / 0.67 | 0.137 / 2.90 / 0.63 | 0.152 / 2.99 / 0.62 | 0.136 / **21.1** / 0.71 |
| step_pitch | 0.001 / 3.25 / 0.37 | 0.001 / 3.16 / 0.41 | 0.001 / 3.17 / 0.38 | 0.040 / **28.3** / 0.55 |
| step_yaw | 0.001 / 15.3 / 0.65 | 0.001 / 15.1 / 0.64 | 0.001 / 15.2 / 0.60 | n2: 0.001 / **91.7** / 0.85 |
| rate_step_roll | 0.396±0.045 / 19.6 / 2.35 | 0.351 / 19.5 / 2.21 | 0.357 / 19.8 / 2.12 | 0.358 / 20.1 / 2.22 |

Reading:
- The same-binary frozen control reproduces the v1-era H5 numbers (att 0.310 vs 0.340, rate 0.564 vs 0.562): the
  binary changes since v1 are NOT the cause of the variant gains. The provisional reading above stands: a slower
  actuator model (tcdn, 25 ms) reduces the H5 roll-rate loss vs frozen by 49 % (att) and 25 % (rate), tcup (12.5 ms)
  by 33 % / 9 %; neither removes it (PID v1 0.088 / 0.356).
- On the tuning set tcup/tcdn are within a few % of frozen on attitude; tcdn is 9 % slower on step_roll rate RMS.
- **indi_g2 is broken on the tuning set** (rotation RMS 21-92 deg while roll/pitch rate RMS are normal): the
  rotation error is in yaw, i.e. G2_Y 0.16 makes yaw drift or diverge in hover and steps, while on H5 (roll axis
  only, yaw unaffected over the short window) it looked harmless. Not analysed further: G2 stays 0 (D-g2sim) and
  the v2 inner loop uses the measured rotor speed. If G2 is ever revisited, look at the yaw logs of
  `runs/hover/indi_g2/` first (sign convention of the G2 term vs gz reaction torque is the first suspect).
