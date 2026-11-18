# I118 simulated stick pilot (D-G3-STICK-PILOT)

Module `bench/stick_pilot.py` (pure), wired in `bench/run_scenario.py` behind `--stick-pilot` (default off), `g3_run.py` passes it
for stick modes stabilized / acro. Tests `bench/tests/test_stick_pilot.py` (run as `python3 bench/tests/test_stick_pilot.py`, no pytest on host).

## Usage
`run_scenario.py ... --stick-mode acro --stick-pilot` (error without `--stick-mode`). sticks.csv gets columns
`pilot_thr,pilot_roll_stick,pilot_pitch_stick` (neutral rows outside the stick segment: empty). meta.json `stick.pilot` holds the gains and limits.

## Altitude loop derivation
Vertical accel ~ (g / thr_hover) * d_thr (thrust linear in throttle, small tilt), so z'' = K u, K = g / thr0 (about 19.6 at thr0 0.5).
Control u = kp e + ki int(e) - kd (vz - vz_ref). Closed loop: s^3 + K kd s^2 + K kp s + K ki. Place poles at (s + a)(s^2 + 2 zeta wn s + wn^2),
wn = 2 pi 0.25 = 1.57 rad/s, zeta 0.8, a = 0.4 wn: kd = (2 zeta wn + a)/K, kp = (wn^2 + 2 zeta wn a)/K, ki = a wn^2 / K.
At thr0 0.5: kp 0.206 per m, ki 0.079 per m s, kd 0.160 per m/s (thrust units). Integral state clamped to +-0.1, total correction to +-0.15 thrust.
Self-test: 5 % thrust error, error < 0.05 m after 15 s, excursion < 1.5 m.

## Reference altitude (choice)
The zsine throttle is thr = thr_hover + 0.5 * 0.15 * vz_up_demand / 3 : it IS meant to move the vehicle. z_ref = z at segment start + integral of the
profile's vz_up_demand, and the damping term acts on (vz - vz_demand). The pilot then tracks the intended climb rather than cancelling it.
The thrust-to-vz response of the open-loop profile is an acceleration, not a velocity, so the realized motion differs from the integral of
the demand; the pilot closes that gap at 0.25 Hz (it will attenuate profile content below its bandwidth; zsine_o6 period not checked against that: UNVERIFIED impact on test severity).

## Acro levelling
roll/pitch rate command = -k_level * angle, k_level 1.5 /s (0.24 Hz). Acro stick map from the firmware: roll rate = superexpo(y) * MC_ACRO_R_MAX,
pitch rate = superexpo(-x) * MC_ACRO_P_MAX; the runner sets neither MC_ACRO_* nor expo, so PX4 defaults are used (100 deg/s, expo 0,
supexpo 0 -> linear): y = p/R_MAX, x = -q/P_MAX. If the G3 base params change MC_ACRO_R_MAX/P_MAX/EXPO, Pilot(r_max, p_max) must follow (not wired: UNVERIFIED that G3 params leave them at default).
Bandwidth check: altitude 0.25 Hz and levelling 0.24 Hz vs attitude closed loop of several Hz (assumed >= 5 Hz, not measured here): ratio < 1/5, OK;
the rate loop beneath is tens of Hz. In acro tilt also reduces vertical thrust (cos tilt) which the altitude loop sees as disturbance, no tilt compensation.

## Measurement
Latest estimator values received by the runner, ATTITUDE (roll, pitch) and LOCAL_POSITION_NED (z, vz), as a human pilot would see the vehicle;
sim time `sim.t`. z_up = -z, vz_up = -vz. The pilot is updated at the stick stream rate (50 Hz sim grid).

## Deviations
1. "throttle correction in stick_profile units": stick_profile throttle is a stick value whose thrust map is mode dependent, so the correction is
   collective thrust (0..1) added to the profile thrust (stick_to_thrust of the sample), then converted back with thrust_to_stick. Total clamped by the stick range via stick_to_raw.
2. `update` takes an extra optional `vz_ref_mps` (default 0) for the damping reference.
3. Added `roll`/`pitch` fields to the runner state (from ATTITUDE).

## Tests and mutations
Tests: altitude recovery (both modes), step reference, acro tilt decay from 32/-20 deg, acro sign/scale, stabilized has no attitude term, inactive in altctl/posctl, limit + anti-windup, gains positive.
Mutations tried, each made at least one test fail: active in all modes; damping sign flipped; integral disabled; integral clamp removed; roll sign flipped; pitch sign flipped; attitude term in stabilized.

## UNVERIFIED
- Sign conventions against PX4 in flight (pitch x sign from source reading of mc rate control: q = superexpo(-x)*P_MAX; roll y positive = right roll rate; z in LOCAL_POSITION_NED down). Nothing was flown.
- Plant in the test is synthetic; real INDI/PID response, 5 % figure, attitude bandwidth.
- `--stick-pilot` added to g3_run commands: G3 stick runs from before S118 are not reproduced with the pilot (flag only for stabilized/acro); tests/test_g3_run.py rerun passed (see summary).

## F118 fixes
- Pilot is active from the first stick sample sent after the manual mode is observed (neutral rows included), one Pilot instance for the whole stick-mode period, no reset at segment boundaries. Reference altitude = altitude at activation + integral of vz_up_demand (0 on neutral rows), kept in `Pilot.track()`. Acro levelling applies on neutral rows too. Runner wiring: `make_pilot_sp` in `bench/run_scenario.py` returns (neutral callback, stick callback factory); every applied correction is in sticks.csv.
- MAJOR-1 clamps scale with thr0: integral clamp +-1.0*thr0; total commanded thrust (profile thrust + correction) clamped to MANTHR_MIN..THR_MAX; no separate +-0.15 clamp. Anti-windup: integration held while the output saturates in the direction of the error.
- meta.json stick.pilot now has bandwidth_hz, damping, i_lim, thr_min, thr_max with the gains.
- Tests added: combined thr0=0.12 / thrust x0.7 / mass x1.3 step, state persistence neutral->stick, reference follows vz_up_demand.
