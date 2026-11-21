# CAUSE_S189 (G3 pretest oscillation cause)

## Findings so far (run_016, stabilized; scripts bench/osc_env_s189.py, bench/osc_loop_s189.py)
- Factor table: already in ANALYSIS_S188.md (no single separating factor); not repeated.
- Oscillation in run_016 is NOT a take-off transient: ulog clock 0-37 s clean (<0.02 dps), then from t~37.5 to 51.5 s a constant-amplitude 6.5-7 Hz line (INDI p 5.5 dps rms, q 4.8 dps; PID ref same draw: 1.5 dps p,q at same 7 Hz, same window), then stops abruptly at 51.6. Scorer "start 2 s" is relative to its own window clock.
- Rate setpoint carries the line at the same amplitude as the rate (INDI spR 7.3 dps vs p 5.5 dps, phase sp leads gyro 113 deg at 7 Hz); motor cmd range at 40-44 s: 0.149-0.165 (no saturation); truth gyro matches measured gyro (real motion, not sensor artefact).

## Result (S189, logs only; no probe flown, tool budget used on diagnosis)
Scripts: bench/osc_env_s189.py (per-2s band rms), bench/osc_loop_s189.py (amp/phase per signal), bench/osc_qd_s189.py (q_d/att and rate_sp/gyro ratios per run).

### Which loop (run_016, 40-50 s ulog clock, 7.0 Hz, stabilized, zero stick roll/pitch in sticks.csv)
- Rate loop is NOT the oscillator: it tracks. rate_sp/gyro amplitude 1.3, phase sp leads gyro 113 deg (consistent with 20 rad/s rate bandwidth + ~33 ms actuator lag). Measured torque vs commanded torque: gain 0.71, -62 deg, as the actuator model (tau 0.033) predicts; u from eRPM is healthy, no motor saturation (cmd 0.149-0.165 around hover 0.158, allocator not saturated), no telemetry freeze.
- The ATTITUDE SETPOINT q_d itself oscillates at 7 Hz with zero stick input: q_d 0.0277 rad vs attitude 0.0026 rad (10x), rate_sp = 5.3 x (q_d - att) exactly as the att P gain. So the line is a loop that closes through whatever produces q_d: in stabilized mode that is mc_indi_pos_control (INDI thrust-vector/acceleration loop): indi_pos_status t_c[0] rms 0.24, a_f rms 0.19 m/s2 at 7 Hz while g*tilt would be only 0.023 m/s2 (a_f/tilt = 56 (roll) and -112 (pitch) /s2 instead of 9.81). The measured/filtered acceleration a_f fed into t_c = t_f + m(a_c - a_f) is 8x larger than the tilt can explain and in phase with the pitch/roll motion.
- Linear, constant-amplitude (5.5 dps p, 4.8 dps q, 13 s, starts 37.5 s, stops abruptly at 51.6 s when the stabilized segment ends/sticks go to land), no clipping: an underdamped/marginal linear mode, not a saturation/eRPM limit cycle.
- Same draw, PID ref: line at same 7 Hz, same window, but q_d 0.0061 rad, p 1.5 dps (3.7x lower); PID q_d/att 4.5-7.6 too. So the sim plant has a coupling that makes the stock stabilized thrust-to-attitude path wobble as well; INDI's acceleration feedback amplifies it by ~4x.
- a_f/tilt, lever arm check: a_f ~ g*tilt + h*alpha with h ~0.03-0.04 m fits (complex ratio incl. filter lag). The gz model has the IMU at the link origin = CoM (sim/models/quad5in_base/model.sdf: no offset), rotors 4 cm below CoM. So the origin of the large a_f is UNVERIFIED (candidates: sim IMU/CoM offset, rotor thrust line below CoM, vibration x1.9 pickup, filter path in indi_pos).

### Run 10 and others
- run_010 (stabilized): same signature, 5.2 Hz, q_d/att 7.2, rate_sp/p 1.45, q_d 2.0 deg vs att 0.28 deg; PID ref 5.2 Hz too (q_d/att 4.5, p 2.6 dps vs INDI 9.2).
- run_000 (2.5 Hz, p 21 dps, att 1.4 deg, q_d/att 1.6, rate_sp/p 1.0) and run_017 (2.5 Hz, att 1.2 deg, q_d/att 1.3, rate_sp/p 0.97): DIFFERENT signature, position-mode low-frequency line where attitude moves a lot and rate tracks sp: outer/attitude loop band (position loop, xy P 1.2 / VP 2.4), plant corner (delay/dropout/latency), not the 7 Hz stabilized mode. run_005 4.2 Hz in between (q_d/att 4.5, rate_sp/p 1.3). Passing runs 001/019 also show 2.5-3 Hz at 4-6 dps (below the 5 dps rms detector level), i.e. the 2.5 Hz line is a marginal mode present in the whole set, the detector threshold decides.

### Likely cause / where it points
1. For the stabilized failures (010, 016) the oscillating loop is the outer INDI acceleration (thrust-vector) loop in mc_indi_pos_control, running in stabilized mode, closed through the measured acceleration a_f at 5-7 Hz, attitude+rate loops follow correctly. The linear margin model (g3_box_margins / g3_osc_margins) models rate and attitude loops only; it does not contain the a_f -> t_c -> q_d path with its filter (MC_INDI_POS_LPF 10 Hz, POS_DLY) and the observed excess acceleration gain (56-112 vs 9.81 /s2). That is the modelling gap; D-FREEZE-8's F2/F4 and XY_P do not touch stabilized mode, so freeze-8 is not the prime suspect (PID line pre-exists).
2. For the position-mode failures (000, 017, 005 partly) the line is 2.5-4.5 Hz with large attitude motion: attitude/position-loop band; the plant corner (tau_up 0.5, delay, dropout 13-20 %) with D-XY-PICK gains is the candidate. Not tested.
### Unverified / next
- Probe NOT flown. Param-only candidates: MC_INDI_POS_LPF 10 -> 5 (or POS_TB, POS_EN) on run_016's draw; expected: 7 Hz line drops if the a_f path is the cause.
- Check what a_f is (sensor_accel vs vehicle_acceleration, frame, lever-arm) and fit a_f gain vs frequency from the ulog (system-ID of tilt -> a_f) to put the path in the model.
- Factor table: not repeated, see ANALYSIS_S188.md (no separating factor at n=20).
