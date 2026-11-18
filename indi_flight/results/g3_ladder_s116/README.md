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
