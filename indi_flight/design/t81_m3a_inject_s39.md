# T81 M3a loop-break injection (S39), working notes

Spec: DECISIONS.md D-G2-BREAK, D-G2-INJ. Not committed.

## Plan
- New class `IndiInjection` (src/modules/mc_indi_rate_control/IndiInjection.{hpp,cpp}): grid = margins_est.log_bins
  (per_decade=10, 1 axis), phases = margins_est.multisine Schroeder formula (equal power), max 64 components.
- McIndiRateControl: runIndiRateControl() computes c, d = inject.update(gyro timestamp_sample, armed, landed), u = c + d;
  u goes to indi_rate_status.torque_sp, the published vehicle_torque_setpoint and _prev_torque_setpoint.
- msg IndiRateStatus: + torque_sp_pre_inject, inject, torque_sp (no versioning: append-only fields, topic not versioned).
- Params MC_INDI_INJ_{AX,AMP,TP,FMIN,FMAX,NP} in the module yaml.
- Bench: LOG_TOPICS + indi_rate_status, actuator_torque_measured.
- Unit test IndiInjectionTest.cpp (gtest, same pattern as IndiMeasuredTorqueTest).

## Progress
- [ ] step 1 read (done at note creation)

- step 2 implemented (class IndiInjection, module, msg, yaml, CMake, gtest, LOG_TOPICS +2). Runner already has --params FILE (NAME VALUE lines): no new option.

- step 3: SITL build make px4_sitl_default rc=0 (after 2 fixes: license header terminator, -Werror=float-equal); astyle run on changed C++ in the container.

## Step 4: pre-test (hover, INDI, quad5in, speed 4, seed 1, v1 sim, MC_INDI_W_MAX unset)
Run: `indi_project/docker/run.sh -n s39fly -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller indi_m3a --model quad5in --seed 1 --speed 4 --params indi_flight/results/stage2_s39/pretest_m3a/inj.params --out indi_flight/results/stage2_s39/pretest_m3a/hover` (rc 0, flew to completion).
Params (file inj.params; the runner's existing --params FILE was used, no new option): MC_RATE_CTL_TYPE 1 (mapped to MC_INDI_EN=1), INJ_AX 1, AMP 0.02, TP 10, NP 2, FMIN 1, FMAX 60 (18 components, bins 10..501 of 1/Tp). Raw output of the checks: indi_flight/results/stage2_s39/pretest_m3a/checks.txt, checks2.txt.

| check | result |
|---|---|
| (a) rates | indi_rate_status 63805 samples, 799.9 Hz in the window (15998 samples in 19.9975 s); vehicle_torque_setpoint 800.0 Hz. No dropout in indi_rate_status by count. vehicle_torque_setpoint sample time has 15 gaps of 2.5 ms in the whole run (2 inside the window, t=36.81, 47.926 s), and so does vehicle_angular_velocity at the same times (sensor_gyro has 8 other gaps): cycles skipped upstream of the module, not a logger loss of indi_rate_status. Status vs vts count differ by one over the run (63805 vs 63804). |
| (b) max abs(torque_sp - (pre + inject)) | 0 over all 63805 samples (float add is the same operation). |
| (c) status.torque_sp vs vehicle_torque_setpoint.xyz | index-aligned (offset 0): exact (0 error) for the first 59157 samples, which include the whole injection window; they diverge only after sample 59157 (late in the flight, after the injection ended, the one-sample count difference shifts the alignment; not diagnosed). A time-matched comparison (last status before the vts publish timestamp) gave 0.30: that matching is ambiguous when two statuses share an hrt timestamp, so it was not used. |
| (d) injection window | d nonzero from sim 32.0187 s to 52.0162 s = 19.9975 s (NP*Tp = 20 s); only axis 1 nonzero; landed and maybe_landed both false at every nonzero sample. CAVEAT: the origin is the first non-landed armed cycle, i.e. liftoff/takeoff (land detector reports not landed at arming + thrust): the first ~4 s of the 20 s are on the ground (height ~0 until t=34) and the climb (to 4.7 m by t=41), only ~11 s are in hover. The land detector stays non-landed through the window. |
| (e) fault | 0 of 15998 samples in the window, 0 in the whole run. measured_torque_in_use 0 (no measured torque, see below). |
| (f) airborne / roll | stayed airborne (height 4.99..5.00 m at the end of the window). Peak abs roll in the window 14.50 deg (t 42-44 s, hover at 4.7-4.9 m), rms 3.6 deg; 7.3 to 10.5 deg during t 32-40 (takeoff, climb); 6.5 to 8.9 deg for t 44-52. max abs u_roll 0.28 to 0.56 per 2 s block. |

Finding 1: actuator_torque_measured is NOT in the ulog. The module only publishes it when the measured-torque model is enabled (MC_INDI_W_MAX > 0, McIndiRateControl.cpp updateMeasuredTorque early return) and the topic needs ESC rpm (sim v2). LOG_TOPICS now lists it (interval 0) but G2 runs must set CA_R_W_MAX/MC_INDI_W_MAX and --sim v2 to get it. The pre-test was flown without it, so the M3a path with measured torque in use is NOT exercised.
Finding 2: amplitude. 18 components at 0.02 each give u_roll up to ~0.4 and a 14.5 deg roll excursion: far from the "small signal" regime; for the real G2 run AMP is probably to be lowered (e.g. 0.005 to 0.01) and the start moved after the hover is established (the origin rule starts at takeoff).
Finding 3: the CSV for margins_est (roll: t = vts timestamp_sample - t0, d = status.inject[0], x = status.torque_sp[0] = u, y = status.torque_sp_pre_inject[0] = c; max abs(x - y - d) 3e-8) has a non-uniform time base (2 skipped cycles, "max_dev_samples" 2), and NP = 2 with the default --discard 1 leaves one period: margins_est refuses ("need >= 2 usable periods after discard"). It was run with --discard 0.

### margins_est.py output (python3 indi_flight/bench/margins_est.py m3a_roll.csv --Tp 10 --discard 0), head; full file margins_est_out.txt. Pre-test, NOT a result (window contains takeoff/climb: not stationary; 2 periods only; non-uniform time base):
```
{
 "fs": 800.000000000017,
 "time_base": {
  "max_dev_samples": 2.0000000003421263,
  "uniform": false
 },
 "margins": {
  "pm_deg": -146.078605755247,
  "dm_s": -0.03459064552259803,
  "gm_db": -16.127320010160506,
  "crossings": [
   {
    "w_c": 23.320296406303886,
    "f_c": 3.7115404474314264,
    "pm_deg": -46.218448785558735,
    "dm_s": -0.03459064552259803,
    "slope_down": true
   },
   {
    "w_c": 24.520678139901623,
    "f_c": 3.9025871339307248,
    "pm_deg": 1.0253924328699782,
```

## Files changed (nothing committed)
 M indi_flight/bench/run_scenario.py
 M msg/IndiRateStatus.msg
 M src/modules/mc_indi_rate_control/CMakeLists.txt
 M src/modules/mc_indi_rate_control/McIndiRateControl.cpp
 M src/modules/mc_indi_rate_control/McIndiRateControl.hpp
 M src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml
?? indi_flight/design/t81_m3a_inject_s39.md
?? src/modules/mc_indi_rate_control/IndiInjection.cpp
?? src/modules/mc_indi_rate_control/IndiInjection.hpp
?? src/modules/mc_indi_rate_control/IndiInjectionTest.cpp
```
 indi_flight/bench/run_scenario.py                  |  1 +
 msg/IndiRateStatus.msg                             |  5 ++
 src/modules/mc_indi_rate_control/CMakeLists.txt    |  9 +++
 .../mc_indi_rate_control/McIndiRateControl.cpp     | 28 +++++++++-
 .../mc_indi_rate_control/McIndiRateControl.hpp     | 15 ++++-
 .../mc_indi_rate_control_params.yaml               | 65 ++++++++++++++++++++++
 6 files changed, 117 insertions(+), 6 deletions(-)
```
Zero-diff modules check: git diff --stat for mc_rate_control mc_att_control mc_pos_control control_allocator src/lib/control_allocation commander = 0 lines.

## Step 1-3 summary
- msg: IndiRateStatus.msg + torque_sp_pre_inject, inject, torque_sp (appended; not versioned: messages.instructions says no versioning unless strictly needed; ulog readers keep working).
- Params (yaml, bench/system-identification wording): MC_INDI_INJ_AX (enum 0..3), _AMP 0.02, _TP 20, _FMIN 0.5, _FMAX 60, _NP 3. Max 64 components (highest bins dropped beyond 64, ~6.4 decades). Window is half-open [0, NP*Tp) (same samples as margins_est.multisine, n = fs*Tp*NP). Origin resets when disarmed or when any waveform parameter changes; d computed in double, cast to float. With AX = 0 update() is not evaluated, d is a zero vector, u = c + 0 exactly.
- Module: runIndiRateControl() now takes gyro timestamp_sample and armed; u feeds status, vehicle_torque_setpoint and _prev_torque_setpoint (the latter two via the existing non-finite guard in Run(), unchanged).
- Build: `make px4_sitl_default` in Docker rc=0 (after fixing a license-header terminator and -Werror=float-equal). Tools/astyle/fix_code_style.sh run on the changed C++ in the container.
- Unit test IndiInjectionTest.cpp (gtest functional: off = exact zero, 3 values + t=0 from margins_est.py, bin counts 18 and 21, gating, 64 limit) written and registered in CMakeLists, but NOT RUN: `ninja functional-IndiInjection` in build/px4_sitl_test fails at link with undefined reference to uorb_start (px4_init.cpp:69) while the sibling functional-IndiMeasuredTorque links; the difference was not found (tried adding VehicleActuatorEffectiveness to LINKLIBS). The bin counts and values were independently confirmed by the flight: 18-component grid and exact window length. A bit-level check against margins_est.py of the in-flight d is not done.

## M3b store points (READ-ONLY, not yet written: see section below)
```
src/modules/mc_indi_pos_control/McIndiPosControl.hpp:208:	float _last_thrust{0.f};
src/modules/mc_indi_pos_control/McIndiPosControl.hpp:210:	matrix::Vector3f _last_rates{};
src/modules/mc_indi_pos_control/McIndiPosControl.cpp:52:	_last_thrust = _param_mpc_thr_hover.get();
src/modules/mc_indi_pos_control/McIndiPosControl.cpp:221:			_last_rates.zero();
src/modules/mc_indi_pos_control/McIndiPosControl.cpp:222:			_last_thrust = _param_mpc_thr_hover.get();
src/modules/mc_indi_pos_control/McIndiPosControl.cpp:394:		publishRates(_last_rates, _last_thrust);
src/modules/mc_indi_pos_control/McIndiPosControl.cpp:416:		publishRates(rates, _last_thrust);
src/modules/mc_indi_pos_control/McIndiPosControl.cpp:428:	status.thrust = _last_thrust;
src/modules/mc_indi_pos_control/McIndiPosControl.cpp:475:			_last_rates.zero();
src/modules/mc_indi_pos_control/McIndiPosControl.cpp:476:			_last_thrust = _param_mpc_thr_min.get();
src/modules/mc_indi_pos_control/McIndiPosControl.cpp:477:			publishRates(_last_rates, _last_thrust);
src/modules/mc_indi_pos_control/McIndiPosControl.cpp:578:	_last_rates = rates;
src/modules/mc_indi_pos_control/McIndiPosControl.cpp:579:	_last_thrust = out.thrust;
src/lib/indi_accel_control/indi_accel_control.cpp:78:	_lpf_f.set_cutoff_frequency(sample_freq_hz, cutoff_hz);
src/lib/indi_accel_control/indi_accel_control.cpp:79:	_lpf_u.set_cutoff_frequency(sample_freq_hz, cutoff_hz);
src/lib/indi_accel_control/indi_accel_control.cpp:80:	_lpf_j.set_cutoff_frequency(sample_freq_hz, cutoff_hz);
src/lib/indi_accel_control/indi_accel_control.cpp:83:void IndiAccelControl::setThrustModel(float g_t, float k_cmd)
src/lib/indi_accel_control/indi_accel_control.cpp:89:	if (PX4_ISFINITE(k_cmd) && (k_cmd > FLT_EPSILON)) {
src/lib/indi_accel_control/indi_accel_control.cpp:90:		_k_cmd = k_cmd;
src/lib/indi_accel_control/indi_accel_control.cpp:107:	_thrust_prev = u / _k_cmd;
src/lib/indi_accel_control/indi_accel_control.cpp:110:	_a_ref_prev.zero();
src/lib/indi_accel_control/indi_accel_control.cpp:115:		_t_a_ref_prev[i] = 0.f;
src/lib/indi_accel_control/indi_accel_control.cpp:116:		_a_ref_prev_valid[i] = false;
src/lib/indi_accel_control/indi_accel_control.cpp:127:			_a_ref_prev_valid[i] = false;
src/lib/indi_accel_control/indi_accel_control.cpp:132:		if (!_a_ref_prev_valid[i]) {
src/lib/indi_accel_control/indi_accel_control.cpp:133:			_a_ref_prev(i) = a_ref(i);
src/lib/indi_accel_control/indi_accel_control.cpp:134:			_t_a_ref_prev[i] = _time;
src/lib/indi_accel_control/indi_accel_control.cpp:135:			_a_ref_prev_valid[i] = true;
src/lib/indi_accel_control/indi_accel_control.cpp:140:		if (fabsf(a_ref(i) - _a_ref_prev(i)) > 0.f) {
src/lib/indi_accel_control/indi_accel_control.cpp:141:			const float dt_change = math::max(_time - _t_a_ref_prev[i], kMinDt);
src/lib/indi_accel_control/indi_accel_control.cpp:142:			_j_diff(i) = math::constrain((a_ref(i) - _a_ref_prev(i)) / dt_change, -kMaxJerk, kMaxJerk);
src/lib/indi_accel_control/indi_accel_control.cpp:143:			_a_ref_prev(i) = a_ref(i);
src/lib/indi_accel_control/indi_accel_control.cpp:144:			_t_a_ref_prev[i] = _time;
src/lib/indi_accel_control/indi_accel_control.cpp:265:	const float u_in = in.mean_u_valid ? in.mean_u : _thrust_prev * _k_cmd;
src/lib/indi_accel_control/indi_accel_control.cpp:270:	const Vector3f t_f = z_b * (-_g_t * u_f);
src/lib/indi_accel_control/indi_accel_control.cpp:273:	Vector3f t_c = t_f + (a_c - a_f);
src/lib/indi_accel_control/indi_accel_control.cpp:276:	const float c_min = _g_t * _k_cmd * _thr_min;
src/lib/indi_accel_control/indi_accel_control.cpp:277:	const float c_max = _g_t * _k_cmd * _thr_max;
src/lib/indi_accel_control/indi_accel_control.cpp:279:	if (!PX4_ISFINITE(t_c(0)) || !PX4_ISFINITE(t_c(1)) || !PX4_ISFINITE(t_c(2))) {
src/lib/indi_accel_control/indi_accel_control.cpp:283:	if (t_c(2) > -kMinUpThrust) {
src/lib/indi_accel_control/indi_accel_control.cpp:284:		t_c(2) = -math::max(c_min, kMinUpThrust);
src/lib/indi_accel_control/indi_accel_control.cpp:287:	// tilt: angle between t_c and -e3 (up in NED), scale the horizontal part keeping t_c,z
src/lib/indi_accel_control/indi_accel_control.cpp:288:	const float h_max = -t_c(2) * tanf(_tilt_max);
src/lib/indi_accel_control/indi_accel_control.cpp:289:	const float h = Vector2f(t_c(0), t_c(1)).norm();
src/lib/indi_accel_control/indi_accel_control.cpp:293:		t_c(0) *= s;
src/lib/indi_accel_control/indi_accel_control.cpp:294:		t_c(1) *= s;
src/lib/indi_accel_control/indi_accel_control.cpp:297:	float c = t_c.norm();
src/lib/indi_accel_control/indi_accel_control.cpp:301:		const float z_abs = -t_c(2);
src/lib/indi_accel_control/indi_accel_control.cpp:305:			const float h_now = Vector2f(t_c(0), t_c(1)).norm();
src/lib/indi_accel_control/indi_accel_control.cpp:307:			t_c(0) *= s;
src/lib/indi_accel_control/indi_accel_control.cpp:308:			t_c(1) *= s;
src/lib/indi_accel_control/indi_accel_control.cpp:311:			t_c = Vector3f(0.f, 0.f, -c_max);
src/lib/indi_accel_control/indi_accel_control.cpp:314:		c = t_c.norm();
```
(raw grep; interpretation by the reader of this file: the accel-loop command is published by publishRates(rates, thrust) at McIndiPosControl.cpp:371-381 as vehicle_rates_setpoint, called at :394, :416, :477 (hold/fallback paths with _last_rates/_last_thrust) and :583 (normal path, out.thrust); store points are the lines above that assign _last_* or the library's previous-command member. Not verified by reading the code beyond grep: UNVERIFIED.)

## UNVERIFIED
- gtest not run (link failure); in-flight d not compared bit-exactly with margins_est.multisine (only window length and component count).
- measured-torque path (actuator_torque_measured, W_MAX) not exercised; no PID/bit-identical AX=0 flight done (D-G2-BREAK overturn test).
- (c) divergence after sample 59157 not diagnosed; 2.5 ms input gaps (skipped cycles) not diagnosed (probably pre-existing, same in vehicle_angular_velocity).
- M3b store points: raw grep only.

### M3b store points, summary (partial, from grep only)
- t_c (accel-loop command) is computed at src/lib/indi_accel_control/indi_accel_control.cpp:273 (t_c = t_f + (a_c - a_f), t_f at :270 from u_f = filtered thrust/mean_u, u_in at :265 = in.mean_u (ESC measured) if valid else _thrust_prev * _k_cmd). _thrust_prev lines: 107:	_thrust_prev = u / _k_cmd;;265:	const float u_in = in.mean_u_valid ? in.mean_u : _thrust_prev * _k_cmd;;345:	_thrust_prev = thrust;;
- Module side: published via publishRates(rates, thrust) McIndiPosControl.cpp:371-381 (vehicle_rates_setpoint); stored for the next cycle in _last_rates/_last_thrust at McIndiPosControl.cpp:578-579 (normal path), reset at :221-222 and :475-476, hold/fallback publish :394, :416, :477 (hpp:208, :210).
- The _thrust_prev assignment (the store feeding t_f when no ESC measurement) still has to be read in the library; not confirmed here.

## Orchestrator follow-up (S39)
- Diff read by me: u = c + d reaches the publish and `_prev_torque_setpoint` (stored from the published, guarded
  values, `McIndiRateControl.cpp` ~353). AX = 0: d not computed, u == c.
- Generator check against `margins_est.log_bins`/`multisine` on the pre-test log (indi_rate_status.inject[0], time from
  vehicle_torque_setpoint.timestamp_sample joined on publish timestamp): 15849/15998 samples within 1e-5, max error
  0.026 on the other 149, which sit at the 0/2500 us publish-timestamp steps (join artefact, A-13 sim holes). 18
  components. Not a two-key result yet: S40 repeats it on `timestamp_sample` (now logged).
- Added by me: `indi_rate_status.timestamp_sample` (gyro sample time, so the analysis needs no join) and
  `MC_INDI_INJ_DLY` (start delay after the first airborne cycle, default 5 s), so the excitation starts in hover.
  SITL build OK, astyle clean.
- Unit test: `IndiInjectionTest` registered as `px4_add_unit_gtest` (pure code, no uORB; functional gtest failed to link
  on `uorb_start`). NOT RUN: `build/px4_sitl_o11` is a default config, `make tests` needs `build/px4_sitl_test`
  (first attempt errored "not a directory"). S40: build the test config and run the Indi* tests.
- Measured rotor-speed path not exercised: needs `CA_R_W_MAX` in the params file (mapped to MC_INDI_W_MAX,
  `run_scenario.py:652`) and `--sim v2`. The G2 matrix flies both model-only and measured configurations.
- Amplitude: AMP 0.02 x 18 components gave |d| peak 0.23 and 14.5 deg roll: too large. S41 pre-test AMP 0.005.
