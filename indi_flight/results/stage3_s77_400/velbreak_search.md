# Velocity/acceleration loop-break injection: search (read-only)

Question: does an injection at the outer-loop (velocity/accel/collective) break exist for mc_indi_pos_control, usable for PM in SITL?

## (1) What exists, by break

- Rate break (M3a, INDI): exists. `src/modules/mc_indi_rate_control/McIndiRateControl.cpp:111-112` (setParameters), `:231-242` (c, d, u = c + d; d added on axis `_injection.axis()`). Design: `indi_flight/DECISIONS.md:191-203` (D-G2-BREAK), `:204-215` (D-G2-INJ, Schroeder multisine in-module, bench-only, off by default).
- Rate break, gyro M1 / actuator M2: not injected in code (method only, `bench/margins_est.py`). Not verified in full.
- Attitude, velocity, position, accel break: NO injector. `grep -i inj` on `src/modules/mc_indi_pos_control/` returns 0 hits (C++, Kconfig, params yaml). `src/lib/indi_accel_control/` has no injection/break code (only NaN-test cases and gain docs, `indi_accel_control.hpp:119`).
- Offline only: `indi_flight/bench/m3a_csv.py` (extracts the rate M3a window) and `m3a_margins_pretest.py` (rate). Both read `inject[axis]` from `indi_rate_status`, so they cannot see an outer-loop break.
- Outer-loop break is only a design item: `DECISIONS.md:429` and `:448` (D-GAP, S71 amendment item 3) cite "G2 velocity-break PM < 45 deg" as an overturn test. `DECISIONS.md:343` and `:350` say the outer-loop break should be an additive input (feed-forward). Not implemented.

## (2) Velocity/accel break: enable parameters and flags

- Parameters: none exist for an outer-loop injection. `MC_INDI_INJ_AX/AMP/TP/FMIN/FMAX/NP/DLY` (`src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml:220+`) only drive the rate module (AX: 1 roll, 2 pitch, 3 yaw).
- Runner flag: `indi_flight/bench/run_scenario.py:682-684` maps overlay `MC_INDI_POS_EN=1` to `PX4_PARAM_MC_INDI_POS_EN` and `boot_params`. This enables the outer module only, with no injection. `scenarios.py` has no INJ or POS_EN keys.
- Past result dirs with MC_INDI_POS_EN=1 (no velocity injection in them): `indi_flight/results/stage5_s73/gap_bld1.0.params`, `indi_flight/results/stage5_s73/gap_bld0.3.params`, `indi_flight/results/stage5_s73/loss08_bld0.3/run/run.json`, `indi_flight/results/stage5_s73/loss08_bld1.0/run/px4.log`, `indi_flight/results/stage3_s77_400/bld1.0.params` (the last one is the current stage, not yet analysed for PM).
- Past result dirs with MC_INDI_INJ_AX (rate break only): `indi_flight/results/stage2_s39/pretest_m3a`, `indi_flight/results/stage2_s40/pretest_inj`. No result uses an outer-loop break. Grep by `MC_INDI_INJ_AX` only matched rate-axis injections; I did not open them to confirm the axis.

## (3) Missing to measure a velocity-break PM with MC_INDI_POS_EN 1

1. An injector in `McIndiPosControl.cpp` (or `indi_accel_control`) that adds d to the commanded acceleration or collective before it is published and stored as the previous setpoint (same structure as D-G2-BREAK). Pos module publish points: `McIndiPosControl.cpp:210` (status), `:808` (setpoints). The `vehicle_acceleration`/`vehicle_thrust_setpoint` subscriptions are at `:91-100`.
2. Matching `MC_INDI_POS_INJ_*` parameters, Kconfig/params yaml entries, and logging of c, d, u in the pos status message (the only logged topic is `indi_pos_status`, `run_scenario.py:81`).
3. A runner scenario/flag (no INJ key in `scenarios.py`) and an analysis script that reads the new fields (`m3a_csv.py` reads rate fields only).
4. A bit-identical check at d = 0 (D-G2-BREAK overturn condition), not run.

## Not verified

- Full read of `McIndiRateControl.cpp:329/331` (the decision cites these lines; the current file has the inject block at 231-242, so the lines have moved).
- Contents of the `stage2_s39`/`stage2_s40` injection flights and their axis.
- `indi_accel_control` beyond grep (no injection-related hits found).
- Whether `indi_flight/design/slice2_plan_s69.md` or `stage3_items_note.md` plan an outer injector (grep matched them for MC_INDI_POS_EN but I did not read them).
