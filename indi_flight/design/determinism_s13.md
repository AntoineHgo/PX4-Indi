# Determinism s13: arm/offboard timing spread and metric re-score

Scope: same-seed SITL hovers `indi_flight/results/det_s12/r1..r3` (gate G1). Analysis only, no simulation run.
Scratch: `/tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/52d81939-c2c5-4141-b338-03f1bc8a732b/scratchpad/det13/`
(`rescore.py`, `check_gyro.py`, `gyro_abs.py`, `summary.json`, `table.md`, `r1..r3/run.json` and `r1..r3/metrics.json`).

All times are sim seconds (ULog time base). Spread = (max - min) / |mean| over the three runs.

## 1. ULog vs run.json arm and offboard instants

| run | run.json t_arm | ULog ARMED (first vehicle_status sample with arming_state 2) | run.json minus ULog arm | run.json t_offboard | ULog OFFBOARD (first nav_state 14) | run.json minus ULog offboard | first actuator_motors max(control[0..3]) > 0.01 | first sample > idle + 0.02 |
|---|---|---|---|---|---|---|---|---|
| r1 | 30.280 | 30.016 | 0.264 | 52.280 | 52.024 | 0.256 | 31.244 | 31.460 |
| r2 | 30.612 | 30.016 | 0.596 | 52.612 | 52.024 | 0.588 | 31.240 | 31.456 |
| r3 | 30.596 | 30.012 | 0.584 | 52.596 | 52.032 | 0.564 | 31.244 | 31.460 |

Spreads: run.json arm 0.332 s (r1..r3 range 0.332 s), run.json offboard 0.332 s; ULog offboard 8 ms; ULog arm 4 ms; motor first above idle 4 ms.

- ULog OFFBOARD is a real transition: the previous vehicle_status sample (52.012, 52.012, 52.020) still has nav_state != 14.
- ULog ARMED is NOT a transition in the log: the log starts at arm. The first vehicle_status sample (30.016, 30.016, 30.012) already has arming_state 2, so the 4 ms arm spread is only the logger start, an upper bound on the PX4 arm instant.
- Motor idle level at arm is about 0.0011 (max of control[0..3]); spin-up starts about 1.2 s after arm.
- The run.json lag over the ULog instants is 0.26 to 0.60 s and is nearly the same for arm and offboard within a run (differs by 8 to 20 ms). This is consistent with both being read from the same 1 Hz HEARTBEAT stream (phase), but the runner code was only grepped, not read (see flags).

**Answer:** PX4's offboard instant is identical across runs to 8 ms (one vehicle_status sample pair is 12 ms apart). The 0.33 s spread is a runner observation artefact, not PX4 timing.

## 2. Metric re-score with window aligned to the ULog OFFBOARD instant

Method: window start = ULog offboard + 3.256 s (r1's offset: 55.280 - 52.024), duration 30.000 s, all else unchanged. `metrics.py` run on the original `flight.ulg` with the shifted run.json copies. Sanity check: r1 after equals r1 before exactly (its window is unchanged).

| run | before window [s] | after window [s] | ULog offboard [s] | run.json t_offboard [s] |
|---|---|---|---|---|
| r1 | 55.280 .. 85.280 | 55.280 .. 85.280 | 52.024 | 52.280 |
| r2 | 55.612 .. 85.620 | 55.280 .. 85.280 | 52.024 | 52.612 |
| r3 | 55.596 .. 85.596 | 55.288 .. 85.288 | 52.032 | 52.596 |

| metric | before r1 | before r2 | before r3 | before spread | after r1 | after r2 | after r3 | after spread | change (pp) |
|---|---|---|---|---|---|---|---|---|---|
| position.max_dev_horizontal_m | 0.0318328 | 0.0341944 | 0.0407051 | 24.94 % | 0.0318328 | 0.0341944 | 0.0407051 | 24.94 % | 0.00 |
| position.max_dev_vertical_m | 0.0240173 | 0.0204773 | 0.0202332 | 17.54 % | 0.0240173 | 0.0204773 | 0.0202332 | 17.54 % | 0.00 |
| position.rms_3d_m | 0.0195441 | 0.0186482 | 0.0187519 | 4.72 % | 0.0195441 | 0.0186136 | 0.0188306 | 4.90 % | +0.18 |
| attitude_tracking.roll_rms_deg | 0.0305004 | 0.0319577 | 0.0342302 | 11.57 % | 0.0305004 | 0.0321690 | 0.0341493 | 11.31 % | -0.26 |
| attitude_tracking.rotation_angle_rms_deg | 0.0334648 | 0.0356249 | 0.0398903 | 17.69 % | 0.0334648 | 0.0357233 | 0.0394012 | 16.40 % | -1.29 |
| attitude_tracking.yaw_rms_deg | 0.0127175 | 0.0158334 | 0.0135075 | 22.23 % | 0.0127175 | 0.0157722 | 0.0132097 | 21.98 % | -0.25 |
| rate_tracking.roll_rms_rad_s | 0.00102147 | 0.000997246 | 0.00106588 | 6.68 % | 0.00102147 | 0.00100258 | 0.00105705 | 5.30 % | -1.38 |
| effort.motor_rate_rms_per_s | 0.00738473 | 0.00744447 | 0.00724445 | 2.72 % | 0.00738473 | 0.00743902 | 0.00722619 | 2.90 % | +0.18 |

Alignment explains at most 1.4 pp of spread. For the 10 to 25 % metrics: max_dev_horizontal 0 pp, max_dev_vertical 0 pp, yaw 0.25 pp (1 % of its spread), rotation angle 1.3 pp (7 %).

## 3. Gyro samples in the first 2 s after arm, r1 vs r2

ULog arm instant is the same in both runs (30.016 s), so absolute timestamps are compared.

| topic | samples in [arm, arm+2 s] r1 / r2 | common timestamps | identical rows | max abs diff | first differing sample after arm |
|---|---|---|---|---|---|
| sensor_gyro (logged at about 1 Hz, unusable for this) | 2 / 2 | 0 | 0 | 1.8e-3 rad/s | sample times differ by 8 ms |
| sensor_combined gyro_rad (about 250 Hz) | 495 / 492 | 492 | 0 | 2.93e-3 rad/s | +28 ms (first common sample) |
| vehicle_angular_velocity xyz (about 250 Hz) | 495 / 492 | 492 | 0 | 2.17e-3 rad/s | +28 ms |
| actuator_motors max(control[0..3]) | 495 / 492 | 492 | 0 | 9.3e-4 | +28 ms (idle level 0.00106 vs 0.00110) |

The 4 ms IMU grid coincides in absolute sim time (all 492 r2 stamps appear in r1). r1 has 3 extra samples in the window (two at arm+20 and +24 ms), so its first sample relative to arm differs; that is logger start, not a sim clock offset.

Not bit-identical: the IMU and motor outputs already differ at the first common sample after arm.

## Commands run

- `python3 indi_flight/bench/metrics.py --help` (usage: `metrics.py ulog [--run-json] [--out]`)
- `python3 -c "import pyulog"` (available on host)
- `python3 <scratch>/rescore.py`: pyulog extraction of vehicle_status, actuator_motors, sensor_gyro; writes shifted run.json copies; runs `python3 indi_flight/bench/metrics.py indi_flight/results/det_s12/rN/flight.ulg --run-json <scratch>/rN/run.json --out <scratch>/rN/metrics.json` for N = 1..3
- `python3 <scratch>/check_gyro.py`: vehicle_status around arm, topic rates, relative-grid comparison
- `python3 <scratch>/gyro_abs.py`: absolute-timestamp comparison of sensor_combined, vehicle_angular_velocity, actuator_motors in [30.016, 32.016] s

Nothing under indi_project/ or results/det_s12/ was modified. No simulation was run.

## Conclusion

1. The 0.33 s arm/offboard spread in run.json is a runner artefact: the observed times lag the true PX4 transitions by 0.26 to 0.60 s and differ per run. PX4's offboard transition is at 52.024, 52.024 and 52.032 s (8 ms).
2. Window misalignment explains essentially none of the 10 to 25 % metric spread. Max deviation metrics are unchanged; the largest change is rate_tracking.roll (6.7 to 5.3 %). Steady-hover metrics are insensitive to a 0.3 s shift.
3. The remaining metric spread is real non-determinism in PX4/SITL: IMU and motor outputs already differ at the first common sample after arm (max 2.9e-3 rad/s), so divergence starts before arm, where the log has no data.
4. Gate G1 needs the pre-arm divergence traced (log from boot, or compare the seed-driven noise streams), not runner timing fixes.
5. Caveat: three runs only, so the spread statistics are weak.

## Unverified / flags

- The heartbeat-phase explanation of the runner lag is a hypothesis; `indi_flight/bench/run_scenario.py` was only grepped (lines 308, 573-574, 609-610), not read in full.
- ULog ARMED is not observed (log starts at arm); the arm instant is only bounded by 30.012 to 30.016 s.
- `sensor_gyro` is logged at about 1 Hz here (2 samples per 2 s), so the bit-identical test used sensor_combined and vehicle_angular_velocity instead.
- The "above idle" thresholds (0.01 and idle + 0.02) are my choices.
- The re-score shifted only the run.json window; t_offboard_us and t_arm_us were not changed (metrics.py for hover does not read them).
- Origin of the pre-arm divergence (seed, wall clock, or initial state) was not determined.
