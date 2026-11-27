# 6. Hardware bring-up checklist

## 6.1 Scope and how to read this chapter

Everything in this report was validated in simulation (Gazebo SITL, reference airframe quad5in, 800 Hz world, 1.25 ms step). No real flight log exists. This chapter lists what to measure on a bench before the first flight, so that the assumptions the simulation made are checked on the real vehicle. Each check names the controller assumption it protects.

Path abbreviations: RC = `src/modules/mc_indi_rate_control`, PC = `src/modules/mc_indi_pos_control`, DS = `src/drivers/dshot`, AR = `indi_flight/design/airframe_requirements.md`.
Parameters are cited as `file:line` of their definition in the yaml (the `default:` sits a few lines below the name line). The checks that need a number the sources do not give are marked "(U)" and listed in 6.7.

## 6.2 Parameters and guards referenced

| item | value (source) | role |
|---|---|---|
| `MC_INDI_W_MAX` | default 0 rad/s, 0 disables the measured torque (RC/mc_indi_rate_control_params.yaml:14) | rotor speed at full thrust; u = (omega/omega_max)^2 (RC/IndiMeasuredTorque.cpp:182-185) |
| `MC_INDI_ACT_TC` | 0.05 s, range 0.001-0.2 (yaml:122) | first-order actuator model and rate lead |
| `MC_INDI_ERPM_DLY` | 1 cycle, 0-4 (yaml:157) | delay on the measured torque, to match the filtered acceleration |
| `MC_INDI_ERPM_TO` | 0.02 s (yaml:167) | age above which the measured torque is dropped (RC/McIndiRateControl.cpp:235-237) |
| fixed sample age | 20 ms, hard-coded `SAMPLE_MAX_AGE_US` (RC/IndiMeasuredTorque.hpp:74) | a per-motor sample older than this invalidates the measured torque |
| `MC_INDI_ERPM_FRZ` | 0.5 s, range 0.1-5 (yaml:219) | bit-identical rpm window; frozen only if the command varied by more than 0.02 (`FROZEN_CMD_VARIATION`, IndiMeasuredTorque.hpp:75) |
| plausibility | rpm above 1.5 x omega_max is rejected (`MAX_OMEGA_RATIO`, IndiMeasuredTorque.hpp:76) | catches a wrong pole count or W_MAX |
| error counter | a sample whose `esc_errorcount` changed is dropped (IndiMeasuredTorque.cpp:166-176) | dropped frame |
| `MC_INDI_SP_TO` | 0.5 s, range 0.05-2 (yaml:232) | no rate setpoint: setpoint zeroed, thrust held; not in acro |
| `MC_INDI_INC_MAX` | 1.0, range 0.01-1 (yaml:195) | limit of the torque increment per cycle and axis |
| dt guard | dt clamped to 0.125 ms .. 20 ms (RC/McIndiRateControl.cpp:310-311) | not a parameter |
| `MC_INDI_ID_OK` | 0 (yaml:79) | 0: K_R, K_P, K_Y applied at half their value |
| `MC_INDI_ACT_BLD` | 1.0 s (yaml:180) | blend measured/modelled actuator torque |
| pos module ESC age | 100 ms, hard-coded `kEscMaxAge` (PC/McIndiPosControl.cpp:117, 213) | measured collective thrust freshness |
| `MC_INDI_POS_DLY` | 1 cycle (PC/mc_indi_pos_control_params.yaml:27) | delay on the ESC based thrust |
| pole count | `DSHOT_MOT_POL<n>`, default 14 (src/drivers/dshot/module.yaml:87; code fallback 14, DS/DShot.cpp:1023-1027); esc_rpm = erpm / (pole_count / 2) (DS/DShot.cpp:793, 803) | mechanical rpm used by INDI |
| start | `MC_INDI_EN`, `MC_INDI_POS_EN` select the modules at boot (ROMFS/px4fmu_common/init.d/rc.mc_apps:17-22, 57-62) | no stock fallback |

Behaviour to know before reading the checks:
- The rate module subscribes `esc_status` instance 0 only (RC/McIndiRateControl.hpp:134; PC/McIndiPosControl.hpp:138). A second esc_status instance (for example serial telemetry on another driver) is ignored.
- The rate module judges freshness per motor from `esc.timestamp` (McIndiRateControl.cpp:201). The position module uses the message timestamp (PC/McIndiPosControl.cpp:165), has no frozen detection and no error-count check (grep of the module finds none).
- Missing, stale, offline or frozen telemetry makes the measured path invalid and INDI uses its actuator model (`measured_torque_in_use` false). It does not refuse to arm (6.6).

## 6.3 Bench checks

Props off unless the row says otherwise. Log at full rate (`esc_status`, `actuator_motors`, `actuator_torque_measured`, `indi_rate_status`, `sensor_gyro`, `vehicle_angular_velocity`).

**B1. Both modules run.**
Measure: `mc_indi_rate_control status`, `mc_indi_pos_control status` (prints "running" only, DOCS_DRAFT_S201.md item 8) and the module list in `top`.
Criterion: both listed. Reason: no stock controller starts in their place (rc.mc_apps:17-22, 57-62; R3 in AR).
If it fails: the rate module refuses to start when another publisher of `vehicle_torque_setpoint` is younger than 500 ms (DOCS_DRAFT_S201.md item 5); find the other publisher, fix `MC_INDI_EN`, reboot.

**B2. Rotor geometry and direction vs `CA_*`.**
Measure: with props off, spin each motor briefly at low command from the actuator test and compare motor number, position and spin direction with `CA_ROTOR<n>_*`. Then with props off and a rate step injected on the bench (`MC_INDI_INJ_*`, only to see that signs agree), check that the sign of the logged `actuator_torque_measured.torque` follows the commanded `vehicle_torque_setpoint` per axis.
Criterion: signs agree on all three axes. Reason: the measured torque is built with the control allocation matrix (airframe requirement R2); a wrong direction turns the feedback positive.
If it fails: correct `CA_*` before anything else.

**B3. Telemetry rate, per motor.**
Measure: from the log, the interval of new `esc_status.esc[i].timestamp` per motor and `esc_status.counter` rate, at idle and at about hover command (props off, short run, restrained).
Criterion (U): the sources give no required rate. The controller needs a sample younger than `MC_INDI_ERPM_TO` (0.02 s) and than 20 ms, so a motor updating slower than about 50 Hz cannot satisfy the rate module's freshness rule continuously. The simulation telemetry frame is 1.25 ms, 0-3 frames latency was the G3 envelope (GATES.md, G3 factor table).
If it fails: the rate path will sit on the actuator model; set `MC_INDI_W_MAX` 0 and treat the vehicle as running the modelled path, or raise the telemetry rate.

**B3a. rpm published while disarmed.**
Measure: with the vehicle disarmed and props off, log `esc_status` and read the update rate of every motor.
Criterion: every motor at about 50 Hz or more while disarmed (the arming check needs a sample younger than 20 ms). Unverified on hardware.
If it fails: arming is refused with the INDI rpm telemetry event; fix the ESC driver or telemetry configuration. Also check that arming is refused with one motor's telemetry unplugged.

**B4. Telemetry latency and spread.**
Measure: step the command of one motor (props off, small step above idle) and read the delay between the `actuator_motors` change and the first `esc_status.esc_rpm` change, per motor; repeat 10 times. Use `ident_actc.py` (below) on a hover log for the combined delay it reports.
Criterion: latency small and the same on all motors, and covered by `MC_INDI_ERPM_DLY` (1 cycle by default, yaml:157) plus the G3 envelope of 0-3 frames. The G2 delay margin was set as at least 2 control periods plus the telemetry latency (GATES.md G2 pass rule), but the latency value itself is not recorded (report/g2_margins.md:9-10): the numeric limit is (U).
If it fails: a latency beyond the tested envelope is outside the validation; set `MC_INDI_ERPM_DLY` to the measured number of cycles (range 0-4) only if the lag is a whole number of cycles, and report the value.

**B5. Pole count and omega_max.**
Measure: run the motor at a known throttle with an optical or hand tachometer on a bare shaft (props off), compare `esc_rpm` with the tachometer. Then set `MC_INDI_W_MAX` (rad/s) to the rotor speed at full thrust, props on, measured at the highest command that is not saturated.
Criterion: `esc_rpm` within a few percent of the tachometer (U: tolerance not in the sources) for the `DSHOT_MOT_POL<n>` set; W_MAX such that u = (omega/W_MAX)^2 lies in 0..1 at full thrust. Reason: a wrong pole count halves or doubles omega and the measured torque scales with its square; the 1.5 x omega_max plausibility check (IndiMeasuredTorque.hpp:76) would reject an over-reading rather than correct it.
If it fails: fix `DSHOT_MOT_POL<n>` first (code fallback is 14, DShot.cpp:1026), then W_MAX.

**B6. Frozen-value behaviour of the DShot driver.**
Measure: with the vehicle armed, props off, command varying by more than 0.02 on one motor; disconnect that ESC's telemetry (or stop its replies) and watch whether `esc_status.esc[i].esc_rpm` keeps the last value, goes to 0, or the motor leaves `esc_online_flags`; then watch `actuator_torque_measured.motor_frozen_mask`, `.motor_valid_mask`, `.valid` and `indi_rate_status.measured_torque_in_use`.
Criterion: within `MC_INDI_ERPM_FRZ` (0.5 s) plus the window of the first change, the motor must leave the valid mask (frozen bit set, or offline), and `measured_torque_in_use` goes false. A driver that keeps repeating a value while the command is constant is not a failure (the detector needs a command variation above 0.02, IndiMeasuredTorque.cpp:129-139). Reason: the controller assumes a missing measurement is flagged, otherwise it feeds a stale rotor speed into the torque. The simulator frozen hook tripped at 0.075 s with a 0.5 s window (ANOMALIES.md A-57, cause unverified), so the real trip time may differ.
If it fails: do not fly the measured path; set `MC_INDI_W_MAX` 0.

**B7. Dropped frames.**
Measure: `esc_status.esc[i].esc_errorcount` over a minute at hover command. Criterion: counter changes are isolated; each change drops one sample (IndiMeasuredTorque.cpp:166-176), and a run of drops longer than 20 ms invalidates the measured torque for the cycle. Persistent invalidity: see B3. The G3 envelope drew dropout 0-20 % of frames and a 2 s loss on one motor (GATES.md G3 factor table).

**B8. Loop timing.**
Measure: `top` for the CPU load; `perf` for `mc_indi_rate_control: cycle` (RC/McIndiRateControl.cpp:52) and the pos module counter; log `sensor_gyro` and `vehicle_angular_velocity` and check the interval of `timestamp_sample` for gaps (the G2 validity rule used no gap above 3 periods, GATES.md:120-121).
Criterion: rate module runs once per gyro update at the configured rate (G2 tested 800 and 400 Hz, 267 Hz reported only, GATES.md G2), no missed cycle, no `dt` beyond the 20 ms clamp (McIndiRateControl.cpp:310-311). A minimum rate and load limit are not in the sources (U). Reason: the margins were computed for 400-800 Hz; the clamp hides a long gap.
If it fails: lower the load, or leave the vehicle on the tested rates; do not fly at a rate that was not margin-tested.

**B9. Setpoint timeout and INC_MAX.**
Measure: stop the `vehicle_rates_setpoint` publisher in a mode other than acro, armed, props off; watch `indi_rate_status.rate_sp_stale` and the zeroed rate setpoint after `MC_INDI_SP_TO` (0.5 s). Criterion: stale flag set at about the timeout, thrust held. These two guards (SP_TO, INC_MAX) are not evidenced by a flown test (6.6), so a bench confirmation is the only evidence.

**B10. GNSS latency (R4 in AR).**
Measure the receiver latency and set `SENS_GNSS0_DELAY` within 50 ms of it. Reason: G3 drew mismatches of +-50 ms and the outer loop was less tolerant than PID beyond about +60 ms (AR, R4).

**B11. Props on, restrained.**
Repeat B6-B7 and B8 with props on at hover command, vehicle restrained, to catch vibration, electrical noise and telemetry quality at real rotor speed.

## 6.4 First hover sequence (tethered or low risk)

1. B1-B11 passed and logged; `MC_INDI_ID_OK` 0 (gains at half, the only configuration validated before identification, DECISIONS.md D-G7-DEFAULTS), `MC_INDI_W_MAX` 0 or set from B5.
2. Tethered or net, low height, a pilot with a switch at hand. There is no PID fallback in flight (docs/en/config_mc/indi_control.md "Limitations"); the safe action is to land or kill.
3. Take off in a stabilised or altitude mode, hover about 1 m for 20-30 s, no excitation. Check in the log: `indi_rate_status.fault` false, `measured_torque_in_use` true, `motor_valid_mask` full, no `rate_sp_stale`.
4. Small manual attitude inputs, then the position mode only if the GNSS delay check passed.
5. Land and review the log before any excitation.

## 6.5 Identification steps run by the user

The firmware flies its own excitation (D-IDENT, DECISIONS.md:626-640): the user sets the `MC_INDI_INJ_*` and `MC_INDI_PINJ_*` parameters (defaults off; INJ_AMP 0.02 normalised torque, RC yaml:272) and flies the hover plus multisine manoeuvre in the ID_OK 0 configuration. Offline, the repository bench tools fit the parameters: `indi_flight/bench/ident_actc.py` (ACT_TC, per-motor output-error fit of (rpm/rpm_max)^2 against the command, design/actc_ident_s208.md) and `ident_iv.py`, `ident_fit.py`, `ident_fit_yaw.py` (G1, G2_Y; D-IDENT). Steps:
1. Fly the manoeuvre, log `actuator_motors`, `esc_status` and the rate topics at full rate.
2. Run `ident_actc.py` on the log. Accept the result only if the fit-quality flags pass (D-ACTC-IDENT): a failed check is a failed identification, not a value.
3. Set `MC_INDI_ACT_TC` to tau_sym (D-ACTC-RULE, accepted by D-OWNER-Q28). Do not round up: the old "when unsure, round up" in the yaml text (yaml:126-128) was overturned by D-OWNER-Q27; the yaml text is out of date (U, fix pending).
4. Enter the G1_* and G2_Y values from the fit. Set `MC_INDI_ID_OK` 1 by hand (nothing sets it; D-DEFAULTS-FW, DECISIONS.md:668-675). The docs page states the tooling is not yet described.

SITL validated the estimators only (D-IDENT); identification on a real log is untested.

## 6.6 Limits of this validation

- Simulation only, no real flight log. Telemetry in the simulator is a model with 0-3 frames of 1.25 ms; the real driver, ESC firmware and rate are not covered.
- G3 robustness is NOT PASSED (GATES.md:808-823). Corner C3 (thrust scale 0.351, motor 3 at 0.709, mass 1.3): the INDI rate controller lost control (tilt above 60 deg) while PID recovered (tilt max 40 deg); it does not depend on ACT_TC (0.033 or 0.0177 both fail). Expect no recovery on a saturated vehicle with a weak motor. Q31 is open.
- The simulator eRPM-loss hook is late by 36-122 ms (STATE.md Notes), so frozen and loss timings were not measured exactly (A-57).
- The logger misses the first ~0.2 s of `indi_pos_status` (late subscription): a missing sample is not bypass (STATE.md Notes). Same care on the real logger.
- Requirement R1 (refuse to arm without rpm telemetry on every motor) is enforced by an arming check in the rate module (04_limits.md 4.4). It is flown in SITL only; on hardware it depends on the ESC driver publishing rpm while disarmed (B3a). In flight the check always allows.
- `MC_INDI_ERPM_TO`/`ERPM_FRZ`, `MC_INDI_SP_TO` and `MC_INDI_INC_MAX` are not backed by a flown test of their own (no test found for them; only the A-57 trip probe touched the frozen detector).
- The position module has no frozen-rpm detection and uses a 100 ms ESC age against 20 ms in the rate module (6.2): a frozen telemetry is flagged for the rate path only.
- ESC telemetry instance 0 only (6.2).
- G6 un-identified item flies ID_OK 0, ACT_TC 0.05 (D-G6-ITEM7-SET). Production boards do not build the modules (only the sitl board enables them, DOCS_DRAFT_S201.md item 4).

## 6.7 Unverified

- Required telemetry rate (B3), acceptable telemetry latency in ms (B4; G2 value "not found", g2_margins.md:9-10) and the minimum loop rate and CPU load (B8). [open: needs flight/hardware]
- Tolerance of `esc_rpm` against a tachometer (B5), and the real trip time of the frozen detector (A-57 open). [open: needs tachometer test]
- Whether the real DShot driver repeats a stale `esc_rpm`, zeroes it or clears `esc_online_flags` on telemetry loss: read the driver only for pole count and publish path; the loss behaviour is the thing B6 measures. [open: needs hardware (B6)]
- Behaviour of a second `esc_status` instance on a real board. [open: needs real board]
- Whether the guard parameters `ERPM_TO`, `ERPM_FRZ`, `SP_TO`, `INC_MAX` are tuned for real hardware. [open: needs hardware flight]
- Whether `MC_INDI_ACT_TC` yaml text (yaml:126-128) is to be updated; `ident_actc.py` use on a hardware log (written for sim logs). [open: waits G7 parameter pass (yaml:126-128 unchanged at S217); `ident_actc.py` on hardware needs a flight]
- Default values quoted here were read from the yaml; the `default:` line numbers were not individually cited. [open: line numbers] (Closed S217: `DSHOT_MOT_POL` default 14 is also the parameter default, `src/drivers/dshot/module.yaml:87`.)
