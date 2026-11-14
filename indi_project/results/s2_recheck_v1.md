# O-3/O-4 post-acceptance re-checks of the frozen v1 INDI (session 34, PRELIMINARY)

Post-acceptance: none of this changes the v1 acceptance result (`acceptance_s15.md`). v1 sim config (stock gz_x500,
FAC 0), H5 = mismatch_combined_att/_rate (plant: motor time constant x2, inertia/mass mismatch), 10 seeds, speed 4.
Runs: `results/s2_recheck_v1/runs/` (script `results/s2_recheck_v1/run.sh`). Variants: indi_tcup (MC_INDI_ACT_TC
12.5 ms = identified tau up), indi_tcdn (25 ms = identified tau down), indi_g2 (frozen + G2_Y 0.16, pending).
Frozen v1 ACT_TC is 11.42 ms.

H5 roll-rate RMS (rad/s), mean +- std over 10 seeds; v1 columns are the v1-era runs (`results/runs/`):

| scenario | PID v1 | INDI frozen v1 | indi_tcup | indi_tcdn |
|---|---|---|---|---|
| mismatch_combined_att | 0.088 +- 0.002 | 0.340 +- 0.039 | 0.210 +- 0.018 | 0.157 +- 0.005 |
| mismatch_combined_rate | 0.356 +- 0.004 | 0.562 +- 0.006 | 0.515 +- 0.007 | 0.425 +- 0.038 |

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
- Tuning set (hover, steps) and indi_g2: not yet analysed.
