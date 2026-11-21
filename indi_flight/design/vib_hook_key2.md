# D-VIB-HOOK second-key review (code against specification), S156

Verdict: ACCEPT WITH FIXES (no BLOCKING finding; one MAJOR trap in the runner).

Checked: DECISIONS.md:864-875, ANOMALIES A-49, uncommitted diff of GZBridge.cpp/.hpp, module.yaml, run_scenario.py,
vib_line_check.py (selftest run: 4/4 OK), and one independent recomputation from hover_typ_s1/flight.ulg.

1. Spec conformance: YES. GZBridge.cpp:683-705 builds one 1P line at the mean |rotor rpm|, accel (cos, sin) in x,y,
   blade-pass sin(NB*phase) at 0.5 on z, gyro (sin, cos, 0.2*bp), all times VIB_ACC/VIB_GYR * (rpm_mean/VIB_RPM)^2.
   Frame: addRotorVibration is called at GZBridge.cpp:737 AFTER the FLU->FRD rotation (:723-733), so x,y,z are FRD
   body (rotor plane, thrust axis). Added before the rotation it would only flip the sign of y,z (a phase flip of a
   circular term), so no amplitude consequence either way. The term goes in before the IMU delay line and only on
   instance 0, as before. Amplitude is per axis at the IMU, as specified.
2. Correctness: no defect found in the phase path.
   - dt: first sample gives 0, gap and non-monotonic stamps give 0 or are clamped to 0.02 s (phase continuous, only
     the tone frequency is wrong during a gap). _vib_timestamp_last is updated before the early return, good.
   - Float wrap: phase is wrapped to [0,2pi); NB is an integer, so sin(NB*phase) is continuous over the wrap; NB*phase
     <= 37.7 rad, float error ~4e-6, negligible. Per-step increment ~1.25 rad, accumulation error random-walk small.
   - Sign: fabsf handles signed rpm. Units: rpm -> rad/s correct; amplitudes m/s^2, rad/s.
   - Thread safety: rpm copied under _node_mutex; _vib_phase is touched only from the instance-0 IMU callback;
     _rotor_rpm_valid is read outside the mutex (bool, benign, unchanged from before).
   - MINOR GZBridge.cpp:689-693: mean is always over 4 entries. Fewer than 4 live rotors (hexa uses the first 4; a
     failed rotor at 0 rpm in a motor_fault scenario) biases the line frequency low; acceptable for quad5in, note it.
   - MINOR GZBridge.cpp:696: no isfinite guard. One NaN rpm makes _vib_phase NaN permanently (wrap of NaN) and the
     IMU output NaN for the rest of the run. Guard rpm_mean with PX4_ISFINITE, cheap.
3. Runner: defaults plausible. 9540 rpm = hover w_h 998 rad/s (ref_airframe_data.md row 9, noise_profiles.md:41-53);
   measured hover mean in the log 9512 rpm confirms. NB 3 matches the 3-blade 5.1 in prop (ref_airframe_data.md:11).
   sim_params are applied after the CLI values (run_scenario.py:1053-1055) so they override.
   - MAJOR run_scenario.py:1042-1048 with scenarios.py:177: _VIB3 sets only SIM_GZ_VIB_ACC/GYR via sim_params. RPM and
     NB are exported only inside `if a.vib_acc > 0 or a.vib_gyr > 0`, so a V5 run without --vib-acc runs quad5in with
     the param defaults 7000 rpm / NB 2: amplitude x1.86 at hover and the blade-pass line at the wrong frequency.
     Fix: set RPM/NB defaults whenever sim v2 (or when sim_params contains SIM_GZ_VIB_ACC/GYR), before the override loop.
   - MINOR noise_profiles.md:~44 still says VIB_ACC is "m/s^2 per rotor"; the typical 10 and harsh 27 were sourced as
     sine amplitude, now interpreted as at the IMU; reword and re-read the S6 source caveat. module.yaml VIB_GYR long
     text is fine.
4. Script: estimator is correct. psd = |X|^2/(fs*sum w^2), doubled for one-sided, integrated over df gives variance
   (Parseval with window power normalisation, so the Hann window gain cancels), A = sqrt(2*P_line). Floor is a median
   of a 15-40 Hz ring per bin, subtracted per bin. Selftest passes (10.005, 1.008, 5.001, noise 0.052) and shows the
   normalisation and aliasing are right.
   - MINOR vib_line_check.py:20-31/45-52: the +-6 Hz band truncates a line broadened by speed wander (rpm std 128 =
     2.1 Hz at 1P). My independent rectangular-window Parseval sum on x, 58-72 s: +-3 Hz 9.74, +-6 Hz 9.79, +-12 Hz
     9.88, +-20 Hz 9.93 (reported 9.70). So the 9.70 vs 9.96-10.0 (chunk std*sqrt2) gap is estimator band loss of
     ~2.5 %, plus (9512/9540)^2 = 0.994 mean-speed scaling, not a hook error. The selftest wander (0.3 rad at 0.2 Hz)
     is a near-pure line and does not exercise this; add a case with ~2 Hz frequency wander, or widen to +-15 Hz.
     BP z 4.80 vs 5.0 expected is the same effect (4.80/5*0.994 = 0.97).

Judgement of the measured result: 1P 9.70 (x,y equal, circular), BP 4.80 at the aliased 323.2 Hz, cross terms 0.001,
chunk estimates 9.96-10.0: consistent with the code. A-49 is closed by the hook; fix the MAJOR before any V5 run.
