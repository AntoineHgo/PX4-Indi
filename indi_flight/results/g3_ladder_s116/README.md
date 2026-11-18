# G3 single-factor ladder (S116), probe only, not gate evidence

Scenario stick_zsine_o6 --controller indi --model quad5in --sim v2 --rate-hz 800, base params indi_flight/bench/params/quad5in_indi_g1.params.
Serial runs via fly.sh; progress in progress.txt. Override JSON files: sag07.json, wind5.json, erpmloss.json, weak08.json, sat.json.
Note: the first launch used a non-existent params path (indi_flight/bench/params/quad5in) and all rows failed rc=1 with no flight. Those stubs were removed and the full ladder was rerun.

Override schema check (scenario_overrides.validate against scenarios.SCENARIOS["stick_zsine_o6"]): all five JSON files pass.
- sag07: thrust_sag {scale 0.7}
- wind5: wind {steady 5, peak 7, dir_deg 45} + disturbance gust_x, dist_segment "stick" (the scenario has no "dist" segment)
- erpmloss: erpm_loss {motor 0, start "stick", start_offset_s 5.0, duration_s 2.0} (timed form)
- weak08: motor_fault {segment "stick", motor 1, thrust_scale 0.8}
- sat: motor_fault {segment "stick", motor 1, thrust_scale 0.35}. NOT a distinct saturation type in the schema: the only mechanism is thrust_scale. 0.35 is the S112 saturation scale, on one motor, as the row spec asked (S112 g3_run.py saturation applied all four motors).

| row | NAME | EXTRA | rc | run.json exit_status | hover_thr_used (source) | flew whole scenario | max tilt / tracking | position error | warnings | class |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | nominal | none | 0 | ok | 0.13667, HTE valid=true (not fallback; MPC_THR_HOVER 0.137 not used) | yes | tilt RMS 1.17 deg | 3D RMS 1.81 m, vertical 1.81 m, horiz 0.09 m | preflight GCS/heading warnings (startup), gz frame-id warnings; landing at end normal | OK (vertical RMS unexplained, see below) |
| 1 | mass13 | --model-variant mass=1.3 | 0 | ok | 0.17768, valid=true | yes | tilt RMS 0.84 deg | 3D RMS 1.02 m | none | OK (mass scale applied: 0.566 -> 0.736 kg in run.json) |
| 2 | inert13 | ixx=iyy=izz=1.3 | 0 | ok | 0.13667, valid=true | yes | tilt RMS 0.82 deg | 3D RMS 1.49 m | none | OK (inertia scale NOT checked in run.json) |
| 3 | sag07 | thrust_sag 0.7 | 1 | failed | 0.13668 (run did not reach metrics) | NO: WatchdogTrip height < 0.3 m at sim t=63.03 (value 0.225) | n/a | n/a | watchdog | UNCLEAR (override applied not checked) |
| 4 | wind5 | wind 5/7 @45 deg, gust_x | 0 | ok | 0.13668, valid=true | yes | tilt RMS 1.12 deg | 3D RMS 4.87 m, vertical 1.06 m (horizontal ~4.6 m) | none | CONTROLLER-FINDING candidate (large horizontal error; wind applied not checked) |
| 5 | erpmloss | erpm_loss motor 0, stick+5 s, 2 s | 0 | ok | 0.13668, valid=true | yes | tilt RMS 0.69 deg | 3D RMS 1.79 m | none | OK (applied window not checked) |
| 6 | weak08 | motor 1 thrust 0.8 at stick | 1 | failed | 0.13667 | NO: WatchdogTrip height < 0.3 m at sim t=63.16 (value 0.288) | n/a | n/a | watchdog | UNCLEAR (motor_fault applied record present) |
| 7 | sat | motor 1 thrust 0.35 at stick | 1 | failed | 0.13668 | NO: WatchdogTrip height < 0.3 m at sim t=60.52 (value 0.255) | n/a | n/a | watchdog | UNCLEAR (motor_fault applied record present) |
| 8 | gnssmis | --gps-dly 150 --gnss-delay 0 | 0 | ok | 0.13667, valid=true | yes | tilt RMS 1.21 deg | 3D RMS 1.26 m | none | OK |

Key findings:
- Rows 3, 6, 7 all abort on the height watchdog at t=60.5-63.2 s, 2-5 s into the stick segment (stick starts at ~58.5 s). The three faults hit different parts of the plant (thrust ramp, one motor at 0.8, one motor at 0.35). Common cause is unverified: it may be the thrust margin on the zsine stick, or the hook timing. Not diagnosed.
- Row 4 (wind) flew but the horizontal error is about 4.6 m against a 5 m/s steady wind.

Unverified / open:
- Nominal vertical RMS 1.81 m (max 3.6 m) is large for a hover while horizontal is 0.09 m. I did not check whether metrics.py uses the moving zsine setpoint as reference. Needs a look before trusting any vertical metric.
- No run.json applied-record check was done for sag07, wind5, erpmloss, inert13 (the applied field was not found by my key search; only motor_fault was seen).
- mass13 and inert13 share HTE valid=true; only the mass change was checked in run.json.
- Nothing committed. Nothing written inside indi_project/.

## b: control flights (S116)

Run by fly_b.sh (serial, progress_b.txt). Container names g3b_*. Stick rows: stick_zsine_o6, --stick-mode stabilized, base params quad5in_indi_g1.params (the PID row uses the same file, as in g3_stick_s114 Commands). Lemniscate rows: o1_lemniscate --controller indi --sched (as in g3_pretest_s112), no --stick-mode. Model quad5in, sim v2, rate 800, same seeds as fly.sh.

Override files: sag07.json used unchanged. For o1_lemniscate the segments are settle / traj / hold (no "stick"), so weak08 and sat were adapted to segment "traj" (weak08_lem.json, sat_lem.json) and wind5 to dist_segment "traj" (wind5_lem.json). Only the segment fields changed. Adapted files were written without running the validator first. The runs accepted them.

| row | rc | run.json exit_status | abort (sim t, height) | applied record (run.json) | vertical RMS / max (m) | horizontal RMS / max (m) | class |
|---|---|---|---|---|---|---|---|
| b1 pid_sag07 | 1 | failed | WatchdogTrip height < 0.3 m, t=63.10 s, value 0.283 m | thrust_sag scale 0.7, t0 55.531 s | no metrics (aborted) | no metrics | WATCHDOG |
| b2 pid_weak08 | 1 | failed | WatchdogTrip height < 0.3 m, t=63.30 s, value 0.292 m | motor_fault motor 1, thrust 0.8, event 58.555 s, applied MAX 2415 of 2700 (omega ratio 0.894) | no metrics | no metrics | WATCHDOG |
| b3 lem_sag07 | 0 | ok | none | thrust_sag 0.7, t0 55.545 s | 0.053 / 0.098 | 2.816 / 4.837 | FLIES |
| b4 lem_weak08 | 0 | ok | none | motor_fault motor 1, 0.8, traj event 58.581 s, applied 2415 of 2700 | 0.029 / 0.077 | 2.803 / 4.805 | FLIES |
| b5 lem_sat | 0 | ok | none | motor_fault motor 1, 0.35, traj event 58.582 s, applied 1597 of 2700 (omega ratio 0.592) | 0.183 / 0.600 | 2.806 / 4.765 | FLIES |
| b6 lem_wind5 | 0 | ok | none | wind steady 5, peak 7, dir 45 deg; gust_x onset 58.503 s; injector 22401 updates, 0 missing velocity ticks | 0.034 / 0.087 | 2.741 / 4.842 | FLIES |

Metrics are metrics.json position.rms_vertical_m, position.max_dev_vertical_m, position.rms_horizontal_m and position.max_dev_horizontal_m. Truth-trajectory horizontal RMS for the lemniscate rows is 1.15 to 1.37 m (trajectory.truth), so the 2.8 m position figure is not a clean tracking number. No lemniscate nominal run was flown, so the faults are not compared against a baseline.

Aborted rows, from flight.ulg via pyulog (altitude = -local_position z, thrust = -vehicle_thrust_setpoint xyz[2]; ULG time assumed on the run.json event time base):

| row | fault start (s) | altitude before (t0-1..t0) | altitude t0+2..t0+3 | altitude 60-61 / 62-63 | thrust before (t0-3..t0) | thrust after (t0..t0+3) | thrust 62-63.1 | thrust 63-63.5 |
|---|---|---|---|---|---|---|---|---|
| b1 pid_sag07 | 55.531 | 5.01 m | 4.91 m | 4.99 / 2.44 m | 0.1367 | 0.137 | 0.141 | 0.169 |
| b2 pid_weak08 | 58.555 | 5.05 m | 5.68 m | 5.40 / 2.92 m | 0.1367 | 0.139 | 0.139 | 0.172 |

Reading: in stabilized stick mode the collective setpoint stays near the hover stick value (about 0.137 to 0.141) through the fault and through the altitude drop from about 5 m to about 2.4 to 2.9 m at 62 to 63 s. It rises only in the last 0.5 s before the trip. Nothing in the setpoint closes an altitude loop, so the watchdog trip follows the open-loop collective and the fault, not an INDI error.

Classification: b1 and b2 are WATCHDOG (scenario property, same window as the INDI ladder rows). b3 to b6 FLY. None are SETUP-FAULT.

Answers:
- Does PID trip the same watchdog on sag07 and weak08 stick: yes. height < 0.3 m at 63.10 s (sag07) and 63.30 s (weak08). The INDI ladder rows tripped at 63.03 s and 63.16 s.
- Does INDI hold altitude on o1_lemniscate with these faults: yes. Vertical RMS 0.03 to 0.18 m across sag07, weak08, sat and wind5. No watchdog trip on any lemniscate row.

Open: the stick-row vertical RMS anomaly from the ladder section is still unresolved. The lemniscate rows report small vertical RMS, so that anomaly is not confirmed by these runs. Nothing committed. Nothing written inside indi_project/.

## c: nominal lemniscate baseline (S116, A-41)

Run by fly_c.sh (serial, progress_c.txt, containers g3c_*). Same command as the lem_* rows of fly_b.sh (o1_lemniscate, --sched, quad5in, sim v2, rate 800, same seeds, params quad5in_indi_g1.params) but without --scenario-overrides, so no faults.

| row | rc | run.json exit_status | vertical RMS / max (m) | horizontal RMS / max (m) |
|---|---|---|---|---|
| c1 lem_nominal_indi (--controller indi) | 0 | ok | 0.030 / 0.086 | 2.805 / 4.827 |
| c2 lem_nominal_pid (--controller pid_default) | 0 | ok | 0.032 / 0.087 | 2.800 / 4.820 |

Metrics from metrics.json position.rms_vertical_m, max_dev_vertical_m, rms_horizontal_m, max_dev_horizontal_m (metrics.json exit_status field is null, so the status is from run.json).

Comparison with section b lem_* rows (faulted, horizontal RMS 2.741 to 2.816 m, vertical RMS 0.029 to 0.183 m): the nominal horizontal RMS is in the same band, so the ~2.8 m horizontal figure is not caused by the faults. Nominal INDI and nominal PID both give about 2.80 m horizontal RMS, which matches the fault rows.

Reference: metrics.py defines analytic_reference (hold_pos plus traj_pva at ULog times) and truth_local_position (sim ground truth). The grep did not confirm which one the o1 horizontal metric uses. This is unverified.

Earlier comparable numbers (pid_default traj_lemniscate, not o1 --sched, so not the same scenario): det_g16/traj_lemniscate/r1..r5 horizontal RMS 2.221 to 2.235 m (vertical 0.018 to 0.028 m); t55_pretest_s26/traj_lemniscate_r1 horizontal RMS 2.227 m (vertical 0.022 m).

Nothing committed. Nothing written inside indi_project/.

**S121 VOID for INDI:** the "indi" runs here flew the stock rate loop (MC_INDI_EN=0, no boot_params in run.json; base params lacked MC_RATE_CTL_TYPE 1). See JOURNAL S121.
