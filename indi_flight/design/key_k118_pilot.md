# Second-key review K118: simulated stick pilot (code to spec). Verdict before reading i118_stick_pilot.md

Counts: BLOCKING 0, MAJOR 2, MINOR 4.

1. Signs: OK. PX4 acro (src/modules/mc_indi_rate_control/McIndiRateControl.cpp:349-353): p_sp = superexpo(roll=y)*R_MAX, q_sp = superexpo(-pitch=-x)*P_MAX.
   Pilot: roll_stick = -k*roll/R_MAX (roll right -> y<0 -> p<0, reduces tilt); pitch_stick = +k*pitch/P_MAX (nose up -> x>0 -> q<0, reduces tilt)
   (stick_pilot.py:~68-70). z_up=-pos[2], vz_up=-vz (run_scenario.py make_pilot_sp); e = z_ref - z_up, thr = kp*e + ... raises thrust when below. ATTITUDE roll/pitch = FRD standard.
2. Acro scaling: OK. MC_ACRO_R_MAX = P_MAX = 100 deg/s, EXPO = SUPEXPO = 0 (mc_acro_params.yaml), not overridden in params/quad5in_indi_g1.params or STICK_PARAMS
   (run_scenario.py:95); stick_pilot.py:19-20 matches. MINOR-1: constants are hard-coded, not read from the SITL param; add an assert/meta of the effective MC_ACRO_* if someone later overrides them.
   Acro thrust = (throttle+1)/2 (linear, MulticopterRateControl.cpp:~170), stabilized uses hover curve: stick_profile.thrust_to_stick handles both. OK.
3. Gains: derivation correct (K=g/thr0, s^3+K kd s^2+K kp s+K ki, wn=2pi*0.25, zeta 0.8, extra pole 0.4 wn); tilt (1/cos) ignored, fine at 0.25 Hz.
   MAJOR-1 (stick_pilot.py Pilot.__init__ i_lim=0.1, thr_lim=0.15): steady-state need = thr0*(m_scale/thrust_scale - 1). With thr0~0.4-0.5: mass x1.3 = 0.12-0.15, thrust 0.7 = 0.17-0.21,
   both = 0.34-0.43. Integral clamp 0.1 / total 0.15 cannot hold hover for thrust 0.7 or for the combined corner (not even mass 1.3 for thr0>0.33). Static mass is absorbed only
   if thr0 = HTE measured after the hover and converged (run_scenario.py:933, verify); thrust sag / weak motor / saturation steps arrive after thr0 is fixed and stay open-loop-ish (vehicle sinks).
   Fix: i_lim ~0.5*thr0, thr_lim ~0.6*thr0 (or documented "factors beyond X remain uncovered"), and record clamp-hit time in sticks.csv.
   MAJOR-2 (design/consistency, make_pilot_sp): the profile thrust is feed-forward proportional to vz_up_demand (thrust = thr_hover + GAIN/2*demand: an ACCELERATION command), while z_ref is the integral of vz_up_demand
   (a velocity). Vehicle acceleration from the stick is not the reference trajectory's, so the pilot will partly cancel the stick input (error between ff-driven motion and z_ref); the kd term uses vz_ref=demand likewise.
   Matches the written spec, but the "pilot does not cancel the test input" goal is only partly met; quantify on one run (altitude vs z_ref, pilot_thr vs profile thrust).
4. Timing: Pilot is created per stick segment (fresh integ, t_prev=None, z_ref = altitude at segment start): good. First call dt=0, dt clamped [0,0.2]. update() is called inside the sp callback at the stick rate with sim.t: good.
   MINOR-2: sim.roll/pitch/pos/vz are the latest received messages (up to one message period stale; no timestamp check); sim.pos None before first LOCAL_POSITION_NED would raise TypeError (hover precedes, so unlikely).
   MINOR-3: z_ref integration uses sim.t deltas with no clamp (a long gap integrates the whole gap); pilot dt clamps at 0.2 but z_ref does not.
5. Logging: sticks.csv gets pilot_thr, pilot_roll_stick, pilot_pitch_stick (neutral rows padded with empties); gains in meta["stick"]["pilot"] (params()). bw_hz/zeta/pole_ratio not recorded (only kp,ki,kd): MINOR-4.
   Flag off: tuple rows, header, send path unchanged (sim.roll/pitch only added attributes) -> command stream identical. In pilot mode acro x/y are overwritten (profile x,y are 0 in these scenarios; if not, the profile is dropped silently).
6. Tests: they check closed-loop altitude with 5 % thrust error, step reference, acro tilt decay, a sign test, limits. They would fail on a sign error in the levelling/altitude terms in stick_pilot.py. They would NOT fail on:
   missing/incorrect reference following in make_pilot_sp (no integration test, no vz_ref test, first-call/segment-reset untested), a wrong stick->thrust map (plant bypasses it), the thrust 0.7 / mass 1.3 draws (only 1.05 tested:
   MAJOR-1 would be exposed by thr_err=1/0.7). Also the synthetic plant is built with the same convention as the pilot (q=-x*P_MAX), so it checks internal consistency; the PX4 sign was verified above independently.
