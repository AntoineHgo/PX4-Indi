# G3 sampler (S108): `bench/g3_sample.py`, self-test, factor-to-hook map

Spec: GATES.md "G3-G8 FINAL (S94)", section 3 and decisions 1-8. GATES.md unchanged. Hooks are mapped, none built.

Use: `python3 bench/g3_sample.py campaign SEED --n 300 --out DIR` (run_NNN.json + index.json),
`python3 bench/g3_sample.py pretest SEED --out DIR`. Test: `python3 bench/tests/test_g3_sample.py` (pytest is not
installed on this host; the file also runs under `python3 -m pytest -q` where available).

## 1. Choices where the spec is ambiguous

1. **Construction.** Every factor is decoded from a unit-cube coordinate. LHS runs: one point per stratum per
   dimension (independent permutation per dimension). Conditional factors (sag, weak motor, dropout, loss, frozen,
   inverted asymmetry, GNSS matched, mode) are decided by their own LHS dimension against the fraction, so the
   fractions are exact to 1/240, and the value of the factor uses a second dimension.
2. **Counts.** 20 % corners = round(0.2 n) (60 at n=300), split over C1-C6 as evenly as possible (10 each), remaining
   runs LHS (240). Corner runs: unpinned factors are independent uniform draws (not LHS) from the same distributions
   as the LHS runs. Run order: LHS first, then corners C1..C6.
3. **Seeds.** sampler_seed = sha256("g3:master:run:idx") 63 bit; gz_seed = 1 + 30-bit sha256 of ("g3", master, "gz", idx)
   (fits SIM_GZ_SEED 0..2^31-1, never 0 = default streams). Distinct per run (checked at n=300). Output uses
   sort_keys, 6-decimal rounding: byte-identical for the same master seed.
4. **Saturation "10 % of runs (inside the corner set)".** Read as: the saturation draw exists only in the corner set,
   as C3 (10 of 300 runs = 3.3 % of all runs, 17 % of the corners). Alternative reading (30 runs) not used. LHS runs
   never saturate. Saturation scale = 0.27 x drawn mass_scale (spec: 2.0 x hover thrust, "about 0.27" on nominal mass;
   implied nominal T/W 7.4). It replaces the sag in that run (sag off). ORCHESTRATOR: confirm.
5. **Asymmetry.** value = tau_down/tau_up in log-uniform [1,3]; 10 % inverted: 1/value, range [1/3, 1]. Applied as
   model_variant tau_up = 1, tau_down = value, on top of the tau scale (tau_scale applies to both).
6. **Loop delay.** 9 equal steps k = 0..8, total = 1.25 k ms; half to the actuator path, half to the IMU path
   (each 0 .. 5 ms). C1/C6 pin k = 8 (10 ms).
7. **Thrust sag**: ramp 10 s from the start of the hover segment (spec gives no start). Weak motor: static from the
   start of hover, motor index uniform 0-3.
8. **Wind present in every run** (the table draws it uniform, not conditional): steady 0-5 m/s, direction uniform
   0-360 deg, gust peak read as TOTAL wind (steady + gust) uniform 3-9 m/s; gust amplitude added = max(peak - steady, 0),
   effective peak = max(peak, steady). Consequence: the "calm" limits of item 3 never apply in the LHS set (every run
   has wind); the pretest extreme runs other than x_wind are calm. ORCHESTRATOR: confirm that wind is always on.
9. **Event timing** (offsets in seconds after the start of the 20 s hold, nominal hold start 80 s of 100 s): gust at
   offset 0 (spec: "at the start of the hold"); telemetry loss (2 s) and frozen (1 s) start uniform in [1, 5] s, so the
   last 10 s window is free of the fault and the 5 s recovery of item 5 fits. Dropout is whole-flight.
10. **Mode** from its own LHS dimension: u < 0.7 position, < 0.9 stabilized, else acro.
11. **GNSS** latency integer ms uniform 80-250, so "matched" is exact; mismatch offset integer ms uniform
    [-100, 100]; EKF delay = max(0, latency + offset). Corner C4 pin: latency 250, offset -100 -> EKF 150.
12. **Pretest** = 15 extreme runs + 5 sampled (spec: "each injector once at its extreme" counts 17 table rows; to fit 20
    runs the table is grouped into 15 injectors: G1, tau, asym, delay, mass, inertia, sag, weak, saturation,
    telemetry latency+dropout, loss, frozen, vibration, GNSS latency+mismatch, wind+gust). Extreme = the end used by
    the corners (G1 x2, tau x3, asym 3, delay 10 ms, mass/inertia +30 %, sag/weak 0.7, vib x5, GNSS 250/-100,
    wind 5 + gust 9, latency 3 + dropout 0.2). One end only; the other ends are flown by the sampled runs/corners.
    Everything else nominal: no wind, no GNSS latency (EKF delay stock), vibration x1. Mode position.
13. **Placeholders**: `g4_typical_noise.profile = null` in every run (profile does not exist); `--imu-noise-scale` null.
    Vibration x1 point (1.0 m/s^2, 0.05 rad/s) recorded as provisional (decision 1).
14. G1 error is recorded as a multiplier on the nominal controller G1 (`MC_INDI_G1_R/P/Y` = nominal x error). The
    sampler does not know the identified nominal (G6), so the hook stores the factor, not an absolute value.

## 2. Factor -> hook table (today's bench; status: EXISTS / PARTIAL / MISSING)

| factor | status | how it is applied today, and the gap |
|---|---|---|
| G1 error (3 axes) | EXISTS (param) | PX4 params `MC_INDI_G1_R/P/Y` (rad/s^2 per normalised torque, default R 320; `--params FILE` "NAME VALUE" lines, or `set_param`). Set controller = nominal x error. Needs the nominal values for quad5in from the identified set (G6). |
| motor tau (up and down) | MISSING for quad5in | `model_variant tau` / `tau_up` / `tau_down` exist (`bench/model_variant.py`) but `run_scenario.py:203` aborts: "model variants are x500-only until the stage-1b port". Port `build_variant` to `sim/models/quad5in*` (SDF motor timeConstantUp/Down). |
| tau_down/tau_up asymmetry (incl. inverted) | MISSING for quad5in | Same key (`tau_down`, `tau_up`); x500-only. Inverted needs `tau_up` > 1 with tau_down = 1 or the equivalent ratio, which the keys allow. |
| loop delay 0-10 ms (act / IMU) | PARTIAL | `--dly-act` / `--dly-imu` = `SIM_GZ_DLY_ACT` / `SIM_GZ_DLY_IMU`, integer ms 0..10. The spec's 1.25 ms steps are not integer ms: the sampler's 2.5/5.0 ms halves are fine, odd steps (0.625, 1.875, ...) must be rounded or the params made float; the hook quantises to the mixer/IMU period anyway. The spec marks it MISSING; the hook was built in the simulator work. |
| mass +-30 % | MISSING for quad5in | `model_variant mass` (base_link only, rotor links unchanged) x500-only. "Hover command scales with it": the controller must learn hover thrust itself, nothing to set. |
| inertia diag +-30 % | MISSING for quad5in | `model_variant ixx/iyy/izz`, x500-only. |
| uniform sag 1.0-0.7, ramp 10 s | PARTIAL | `SIM_GZ_THR_SC` (0..1, rotor speed x sqrt(scale)), driven by scenario key `thrust_sag` (0.5 s staircase over the whole segment sum). Needs a ramp duration/start parameter (now: ramp over all segments). |
| weak motor 1.0-0.7 | PARTIAL | scenario key `motor_fault` (motor, thrust_scale) scales `SIM_GZ_EC_MAX{n}` from a named segment start; no per-run (JSON-driven) scenario entry, and "from hover start" needs a segment name. |
| saturation corner | PARTIAL | `SIM_GZ_THR_SC` down to 0.27-0.35 is within the param's 0..1 range, same ramp gap as sag. Unverified that the sim stays stable (no saturation test with 0.27). |
| telemetry latency 0-3 frames | EXISTS | `SIM_GZ_ERPM_LAT` (frames, 0..8), `sim_params` in scenario or `--params`; needs `SIM_GZ_ESC_FB=2` (`--sim v2`). |
| telemetry dropout 0-20 % | EXISTS | `--erpm-drop` = `SIM_GZ_ERPM_DRP` (0..1), seeded by `--sim-seed` = `SIM_GZ_SEED`. |
| telemetry total loss, 2 s, one motor | PARTIAL | `SIM_GZ_ERPM_LOSS` bitmask (bit i = motor i), toggled by scenario key `erpm_loss` between named segments only. Needs a timed (seconds after hold start) toggle. |
| telemetry frozen, 1 s | MISSING | no simulator hook for a silent bit-identical rpm freeze (ERPM_LOSS holds the value but with failing frames, a different signal for the INDI detector `MC_INDI_ERPM_FRZ`). Needs a `SIM_GZ_ERPM_FRZ`-style mask or an agreed substitute. |
| vibration x1-x5 | EXISTS | `--vib-acc` (m/s^2) / `--vib-gyr` (rad/s) = `SIM_GZ_VIB_ACC` / `SIM_GZ_VIB_GYR` (gyr max 5.0), `SIM_GZ_VIB_RPM` reference rpm; needs `SIM_GZ_ESC_FB>=1`. |
| GNSS latency 80-250 ms | EXISTS | `--gps-dly` = `SIM_GZ_GPS_DLY` (ms, 0..250, delivery delay, no sample time stamped). |
| EKF GNSS delay (matched / mismatched) | EXISTS | `--gnss-delay` = `SENS_GNSS0_DELAY` (ms). Matched = `--gps-dly` value. Stock 110 ms when unset. |
| wind steady 0-5 m/s + gust peak 3-9 m/s, any direction | PARTIAL | `bench/disturbance.py` profiles `gust_x` (+x only, base wind and 6 m/s gust as module constants), `gust_diag` (fixed 4 m/s at 45 deg + 8 m/s at 120 deg). Needs a parametrised profile (steady, gust amplitude, direction, start offset) taking the sampler's `hooks.disturbance`. Also sized from airframe CdA of quad5in = UNVERIFIED assumption (`disturbance.py:33`). |
| mode mix | EXISTS (partial for acro) | `--stick-mode` (stabilized/acro etc.) and scenario `mode`; acro with zero sticks as a G3 flight is not checked. |
| gz seed | EXISTS | `--sim-seed` = `SIM_GZ_SEED` (only affects eRPM dropout and extra IMU noise streams). |
| G4 typical noise profile | MISSING (placeholder) | `g4_typical_noise.profile = null`; `--imu-noise-scale` = `SIM_GZ_IMU_NSC` (1..10) is the likely carrier. |

Counts (19 rows): EXISTS 8 (G1 error, tel. latency, dropout, vibration, GNSS latency, EKF delay, mode, gz seed; mode acro-with-zero-sticks unchecked);
PARTIAL 5 (delay, sag, weak motor, saturation, loss) + wind = 6; MISSING 6 (tau, asymmetry, mass, inertia on quad5in,
frozen telemetry, G4 noise profile).
By gap: model-variant port to quad5in (4 factors), timed/ramped scenario hooks (sag, weak, saturation, loss),
parametrised wind profile, frozen-telemetry injector, G4 profile.

## 3. Self-test result

`python3 bench/tests/test_g3_sample.py`: 9 tests, 0 failures (byte determinism incl. different seed differs, counts and
distinct seeds incl. other n, ranges, LHS stratification (all 240 strata hit once for 11 continuous marginals, discrete
levels balanced within 2), conditional fractions at n=300 within 0.02 (exact by construction), corner pins exact for all 60
corner runs, matched GNSS => EKF delay == latency, pretest set, JSON keys). Documented widenings in the range test: inverted
asymmetry [1/3,1], saturation (only C3, scale 0.27 x mass).

Break-check (changes restored afterwards, original file re-run: 9/9 pass):
- Replace the log-uniform draw by a linear one: `test_lhs_stratification` FAILS (the strata of the log-uniform factors are
  no longer hit once each); range test still passes, as expected (a linear draw stays inside the range).
- Set sag fraction 0.40 -> 0.50 and matched EKF delay = latency + 1: `test_conditional_fractions_n300` and
  `test_matched_gnss_delay_equals_latency` FAIL.
No pytest on this host; the plain-python runner was used.

## 4. UNVERIFIED

- Choices 4 (saturation share), 8 (wind in every run), 9 (event timing), 12 (pretest grouping, one end per extreme) are
  my readings of the spec, not owner statements.
- The hook status table is from reading flags/params/yaml and `run_scenario.py`, not from flying any of them. In particular
  that `SIM_GZ_DLY_*` / `SIM_GZ_GPS_DLY` do what their descriptions say (G1.5 checks) and that `SIM_GZ_THR_SC` ~0.27 is stable.
- Delay hooks take integer ms; the sampler records floats (act_ms 0..5 in 0.625 steps) and the JSON `hooks` block copies
  them unrounded.
- The hooks block is descriptive; no runner consumes it yet (`gate_g3.sh` does not exist).
- Nominal controller G1 for the identified set (G6) is unknown here; `x_nominal` multipliers only.
- The 1.0 m/s^2 / 0.05 rad/s vibration x1 point is provisional (decision 1).
