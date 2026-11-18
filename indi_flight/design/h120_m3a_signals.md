# H120: M3a injection signals, logging and gaps (read-only survey)

Source note: indi_flight/design/t81_m3a_inject_s39.md (T81 M3a, S39).

## 1. Enable, shape, axes, loop position
- Params (src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml:220-310):
  MC_INDI_INJ_AX (enum, 0 = off, pretest used 1, i.e. roll; note finding (d) "only axis 1 nonzero"),
  MC_INDI_INJ_AMP (per-component amplitude, normalised torque), MC_INDI_INJ_TP (period, s),
  MC_INDI_INJ_FMIN (default 0.5), MC_INDI_INJ_FMAX, MC_INDI_INJ_NP (periods, int32),
  MC_INDI_INJ_PT (1 = rate-setpoint break using MC_INDI_INJ_RAMP instead of AMP; default point is torque).
- Shape: Schroeder-phase multisine, equal power, integer bins k/Tp about 10 per decade, max 64 components
  (IndiInjection.cpp:65-101, phases at :84-101). Pretest: 18 components, bins 10..501 of 1/Tp.
- Window: starts at the first armed, non-landed cycle (IndiInjection.cpp:107-131), lasts NP*Tp, then stops.
- Loop: McIndiRateControl.cpp:113-120 (set params, restart on PT change), :249 runIndiInjectionStep,
  :252-254 c = torque_sp_pre_inject, d = inject, u = torque_sp = c + d (u also fed back to the actuator model).

## 2. Topics and fields
- Injection as applied: indi_rate_status.inject (d), torque_sp_pre_inject (c), torque_sp (u)
  (msg/IndiRateStatus.msg:17-19). Rate-break variant: rates_sp_inject, rates_sp_applied (:23-24).
- Actuator state: no measured omega-based u in indi_rate_status. torque_filtered is the modelled torque (:7).
  actuator_torque_measured (ESC-rpm based torque) exists only when MC_INDI_W_MAX > 0 (McIndiRateControl.hpp:109).
  esc_status (esc_rpm) and actuator_motors (control[]) are the raw inputs.
- du: torque_increment (msg :8) is commanded, not measured.
- Gyro: sensor_gyro (800 Hz class, logged_topics.cpp:252, 381); vehicle_angular_velocity (100 Hz in the A-12 note).
- Saturation: no saturation field found. IndiRateStatus has `fault` (inputs rejected, output zeroed) and
  `rate_sp_stale`, neither is saturation. control_allocator_status is in LOG_TOPICS but not checked.
- Bench logger: indi_flight/bench/run_scenario.py:80-94 (LOG_TOPICS, includes indi_rate_status and
  actuator_torque_measured), written with interval 0 = every publish (run_scenario.py:290).
  Measured rate of indi_rate_status: 799.9 Hz (note step 4a). actuator_torque_measured: not in the pretest ulog.
- ident_iv.py:245-246 expects `inject` at 100 Hz and `actuator_torque_measured` at 100 Hz.

## 3. Run command and result
- Command (note line 23): `indi_project/docker/run.sh -n s39fly -t 420 -- python3 indi_flight/bench/run_scenario.py
  --scenario hover --controller indi_m3a --model quad5in --seed 1 --speed 4 --params
  indi_flight/results/stage2_s39/pretest_m3a/inj.params --out indi_flight/results/stage2_s39/pretest_m3a/hover`
- Result dir: indi_flight/results/stage2_s39/pretest_m3a/hover (flight.ulg 90 MB, metrics.json, sends.csv, px4.log);
  checks.txt, checks2.txt, m3a_roll.csv, margins_est_out.txt in indi_flight/results/stage2_s39/pretest_m3a/. Log exists.

## 4. Gaps against the estimator needs
- Rate: actuator state (esc_status, actuator_motors) and any u/du source at 100 Hz in the logger, below the 400 Hz target.
- actuator_torque_measured absent from the pretest ulog; needs MC_INDI_W_MAX > 0 and --sim v2 (note finding 1).
- No omega-based u=(omega/omega_max)^2 per motor and no saturation flag in indi_rate_status.
- Timing: vehicle_torque_setpoint has 2.5 ms gaps; index alignment with indi_rate_status diverged after
  sample 59157 (note 4c). Use timestamp_sample, not index.
- Design: injection starts at takeoff (first ~4 s on the ground); AMP 0.02 gave 14.5 deg roll; NP=2 with
  --discard 1 leaves one period, so margins_est refuses.

## Orchestrator check (S120)
run_scenario.py:79-90 LOG_TOPICS logs esc_status, actuator_torque_measured, indi_rate_status and sensor_gyro at every
update (interval 0). So "esc_status 100 Hz" above is either the publication rate in the s39 log or a misreading of
logged_topics.cpp defaults: UNVERIFIED. First check next session (pyulog on a recent quad5in INDI log with
MC_INDI_W_MAX > 0): publication rate of esc_status and actuator_torque_measured. If the simulated eRPM is published at
100 Hz, the INDI measured path itself runs on 100 Hz data: open an anomaly before any ident flight.
