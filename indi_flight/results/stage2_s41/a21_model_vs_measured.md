# A-21 closing test 2: INDI model-only roll loop, model vs measured (S41)

Scripts (read-only on firmware and `margins_models.py`): `indi_flight/bench/a21_compare_s41.py` (per-bin comparison and
single-element fits, raw output `a21_tables.txt`), `indi_flight/bench/a21_extra_fits_s41.py` (combined fits,
`a21_extra_fits.txt`). Run through `indi_project/docker/run.sh`. Measured data: `stage2_s41/margins_model_long_s2.txt`
(seed 2) and `stage2_s40/pretest_inj/margins_model_long.txt` (seed 1), 18 bins each (14 and 13 accepted by the S40
checker; the txt files do not say which bins were rejected, so all 18 are used, fit band 2.0-12.7 Hz only).

## 1. Conclusion

1. The inner loop as coded in the firmware equals the model `L_indi(meas=False)` element for element (table 2). The
   as-coded model gives PM 42.7 deg @3.25 Hz, GM 6.1 dB @6.28 Hz; measured PM 24.0-25.3 deg @4.5-4.75 Hz, GM 4.3-6.0 dB
   @7.4-7.7 Hz. The gap is not a firmware/model mismatch in the filters, the actuator model discretisation or the
   injection point.
2. Two things are missing from the model, not from the firmware:
   - the attitude P loop closes around the M3a break point: `rate_sp = -MC_ROLL_P * theta` enters `nu = K (rate_sp - F w)`,
     so the measured quantity is `L = K (F + Patt/s) Pn + ...`, not `K F Pn + ...`. `MC_ROLL_P` = 8 (set-default in
     `4040_gz_quad5in`; module default 4). At 4.5 Hz this is `1 + 8/(j 28) = 1.04 e^{-j 16 deg}`, i.e. about -16 deg of
     phase. ATT alone (no fit): PM 23.5 deg @3.58 Hz, GM 4.6 dB @5.78 Hz. It also explains the phase of -165 deg at 1 Hz
     (the model alone gives -104 deg).
   - a gain about 30 % above the model: fitted g = G1_true / G1_set = 1.30 (G1_set = `MC_INDI_G1_R` = 320, so G1_true
     about 417 rad/s2 per unit torque, UNVERIFIED independently). It moves the crossover from 3.6 to 4.3 Hz, where the
     measured crossover is, and lifts |L| by 2.5-4 dB at 2-5 Hz.
3. After ATT + g, a residual of 1.25 dB-equivalent rms remains (PM 30.5, GM 6.6 dB). One further element closes it, and
   the data cannot tell which: extra pure delay 1.26 ms (= one 800 Hz step, 1.25 ms), or extra lag 1.3 ms, or plant tau
   0.038 s with g = 1.43. All three give rms 0.92-0.97 dB-eq, PM 25.5-28.4 deg, GM 5.2-5.4 dB, inside the measured spread
   (PM 24.0-25.3, GM 4.3-6.0). A delay or lag alone (without ATT and g) does not close: rms 3.2-3.3.
4. The most plausible Gazebo-side cause for the last element is a one-step latency (about 1 sample) between PX4 publishing
   `actuator_motors` and the motor model acting on it, see section 5. Not confirmed.

## 2. Elements: model (`margins_models.L_indi`, model-only) against firmware as coded

Effective values of the flight: `inj_model_long.params` only sets `MC_RATE_CTL_TYPE 1` (boots INDI via `MC_INDI_EN`) and
`MC_INDI_INJ_*`; everything else is module default or airframe. The runner pins `IMU_GYRO_RATEMAX 800`,
`IMU_GYRO_CUTOFF 40`, `IMU_DGYRO_CUTOFF 20` (`run_scenario.py`); `run.json` of `model_long_s2` shows no other applied
parameter and `sim: v1`. Gazebo step 1.25 ms (`worlds/default.sdf`), quad5in IMU 800 Hz.

| # | element | model (`INDI_DEF`) | firmware as coded | match |
|---|---|---|---|---|
| 1 | controller rate | fs 800, T = 1/800 | 800 Hz from `sensor_gyro` callback; `dt` from `timestamp_sample` differences (jitter not modelled); filters designed on a low-passed 1/dt | yes (nominal) |
| 2 | gyro filter F | LPF2p Butterworth bilinear, fc 40 | `math::LowPassFilter2p`, `IMU_GYRO_CUTOFF` 40, `VehicleAngularVelocity` | yes |
| 3 | gyro derivative | `a_f = alpha_20 * (F[k]-F[k-1])/T`, alpha first order 20 Hz | `FilterAngularAcceleration`: difference of the (in place LPF2p-filtered) samples times 1/dt, then `AlphaFilter` `IMU_DGYRO_CUTOFF` 20 (tau = 1/(2 pi fc), `AlphaFilter::setCutoffFreq` read) | yes, with two items unread (see section 6) |
| 4 | actuator model | `t_act[k] = a_m t_act[k-1] + (1-a_m) u[k-1]`, `a_m = exp(-T/tau_m)`, tau_m 0.02 | `_t_act += (1 - exp(-dt/_actuator_tc)) (t_alloc - _t_act)`, `t_alloc` = previous published setpoint (minus unallocated torque, 0 in hover), `MC_INDI_ACT_TC` default 0.02, clamp 1 ms..0.2 s | yes (exact discretisation, one-cycle input delay) |
| 5 | model delay | `d_m` = 0 | `MC_INDI_DELAY` default 0, ring buffer, 0 samples | yes |
| 6 | sync filter H on actuator state | `H = alpha_20 * F`, same order | `_lpf` (LPF2p, 40) then `_alpha` (20), same designs as the gyro chain | yes |
| 7 | measurement path / blend | unused (`meas=False`) | `MC_INDI_W_MAX` unset (default 0) so `_meas_in_use` false, `t_f = t_f_model`; ERPM_DLY (1) and ACT_BLD (0) irrelevant | yes |
| 8 | feedback gain K | 20 | `MC_INDI_K_R` default 20 | yes |
| 9 | G1 in the law | 320, `g` = 1 (G1_true = G1_set) | `MC_INDI_G1_R` default 320 | model assumes G1_true = 320, **not verified** |
| 10 | increment form | `u = t_f + (nu - a_f)/G1` | `dt_cmd = (nu - a_f)/G1`, `t_cmd = t_fb + dt_cmd` (bounded by `MC_INDI_DT_MAX`, not active at the injection amplitude 0.005) | yes |
| 11 | rate setpoint | none (`rate_sp = 0`) | `nu = K (rate_sp - rate)`, `rate_sp` from mc_att_control (`MC_ROLL_P` 8) in the flown hover | **mismatch** |
| 12 | injection point | break at M3a, `u = c + d` | `torque_setpoint = pre_inject + inject`, published and stored as `_prev_torque_setpoint` (so the actuator model sees `u`) | yes |
| 13 | extra command latency | `lat` = 0 | none in `McIndiRateControl` (torque setpoint published in the same cycle, control_allocator consumes it by callback) | yes in PX4; downstream of PX4 unknown |
| 14 | plant | first-order lag tau_r 0.033 on rotor speed, exact ZOH, torque = G1 g eta m | SDF `timeConstantUp/Down` 0.033 on all four rotors; thrust ~ w^2, small signal (amplitude 0.005) so same tau; gz filter discretisation and command latency not read | **unverified** |
| 15 | outer loops below 2 Hz | none | position/velocity loops also close in hover_long | mismatch, only matters below ~2 Hz (excluded from the fit) |

## 3. Mismatches (ranked by effect on PM/GM)

1. Element 11: attitude loop inside the break (about -16 deg at 4.5 Hz, crossover pulled down to 3.6 Hz when added
   alone). This is a measurement-definition mismatch: the real rate loop alone is not what the M3a measurement sees.
2. Element 9: |L| 2.5-4 dB higher than the model at 2-5 Hz, fitted g = 1.30 (scan: rms 3.22 at g 1.0, 1.91 at 1.15, 1.25 at
   1.30, 1.79 at 1.45).
3. Element 14: residual of about 1 sample or an equivalent lag (section 4).
4. Element 15: low-frequency bins (1-1.6 Hz) model 4 dB under the measurement even with ATT + g: velocity/position loops.
5. Element 1: nominal against actual `dt`, neglected.

## 4. Fits (fit band 2.0-12.7 Hz, both flights pooled, residual = rms of the complex log error, 1 rad = 8.69 dB = 57.3 deg)

Single added element on the as-coded model, no attitude loop (the question as posed), then with the attitude loop
(Patt = 8):

| hypothesis | fitted | rms (dB-eq) | PM deg @Hz | GM dB @Hz |
|---|---|---|---|---|
| as coded | - | 3.72 | 42.7 @3.25 | 6.1 @6.28 |
| (a) extra pure delay | Td = 3.45 ms | 3.19 | 35.7 @3.48 | 4.2 @5.98 |
| (b) extra first-order lag | tx = 2.9 ms | 3.27 | 36.9 @3.43 | 4.5 @6.00 |
| (c) plant tau_r | 0.0320 s (= SDF 0.033) | 3.71 | 44.1 @3.23 | 6.5 @6.44 |
| (d) gain g | 1.235 | 2.77 | 44.4 @3.92 | 7.5 @7.83 |
| ATT only (Patt 8, nothing fitted) | - | 3.22 | 23.5 @3.58 | 4.6 @5.78 |
| ATT + (a) delay | Td = 1.94 ms | 3.02 | 20.7 @3.70 | 3.7 @5.62 |
| ATT + (b) lag | tx = 1.6 ms | 3.06 | 21.2 @3.68 | 3.8 @5.64 |
| ATT + (c) tau_r | 0.0281 s | 2.87 | 29.6 @3.48 | 6.7 @6.69 |
| ATT + (d) g | g = 1.302 | 1.25 | 30.5 @4.27 | 6.6 @7.77 |
| ATT + g, lat = 1 sample (integer) | g = 1.306 | 0.97 | 28.0 @4.39 | 5.4 @7.48 |
| ATT + g, lat = 2 samples | g = 1.307 | 1.18 | 25.3 @4.51 | 4.4 @7.21 |
| ATT + g + (a) delay | g = 1.306, Td = 1.26 ms | 0.97 | 27.9 @4.39 | 5.4 @7.48 |
| ATT + g + (b) lag | g = 1.309, tx = 1.3 ms | 0.96 | 27.9 @4.40 | 5.4 @7.48 |
| ATT + g + (c) tau_r | g = 1.435, tau_r = 0.0382 s | 0.92 | 25.5 @4.59 | 5.2 @7.36 |
| ATT (Patt free) + g | Patt 8.60, g 1.306 | 1.24 | 29.5 @4.29 | 6.5 @7.75 |
| ATT (Patt free) + g + Td | Patt 7.58, g 1.304, Td 1.33 ms | 0.96 | 28.4 @4.38 | 5.4 @7.48 |
| g + Td, no ATT | g 1.235, Td 2.76 ms | 2.24 | 37.5 @4.16 | 5.1 @7.27 |
| ATT + g + Td with the model tau_m set to 0.033 | g 1.292, Td 6.8 ms | 1.76 | 28.4 @4.04 | 5.8 @7.84 |

Measured: seed 2 PM 24.0 @4.75 Hz, GM 6.0 dB @7.66 Hz; seed 1 PM 25.3 @4.47 Hz, GM 4.3 dB @7.44 Hz.
Fitting Patt freely returns 7.3-8.6, consistent with the airframe value 8 (no free ATT delay: Tatt fitted 0).
Per-bin residual of the best closing candidate (ATT 8 + g + Td, in band): seed 2 max 1.7 dB / 14 deg, seed 1 max 1.1 dB /
4 deg. The three closing options differ by less than 0.1 dB-eq rms: the 2-12.7 Hz data cannot separate a 1.3 ms delay,
a 1.3 ms lag and a 5 ms tau change (all within PM 25-28 deg). Bins above 12.7 Hz are noisy (|L| below -10 dB) and are
not used; they are listed in the tables below.

## 5. Which hypothesis is physically plausible in Gazebo, and what would confirm it

- Pure delay of one sample (1.25 ms, matches Td = 1.26-1.33 ms): plausible. The world step is 1.25 ms and PX4 runs at the
  same 800 Hz; a command published by the control cycle reaches the gz motor plugin through gz transport and is applied
  at the next physics step at the earliest, and the IMU sample returned in the cycle is from the previous step. This is a
  structural one-step latency, not a tuning artefact. The gz-side discretisation of the motor model and the gz_bridge
  publication path were NOT read (no gz source in the repo, budget).
- Extra 1.3 ms lag: indistinguishable at these frequencies from the delay; no physical reason beyond the same one-step
  latency.
- Plant tau 0.038 s (with g = 1.43): needs 5 ms more than the SDF value and a larger gain; less plausible because the
  SDF states 0.033 on both directions, but the rotor-speed to torque relation (w^2, rotor inertia, drag) is not a pure
  first-order lag and cannot be excluded.
- Gain g = 1.30: a G1_true about 30 % above the module default 320. Plausible because G1_R = 320 is a generic default and
  no one has identified G1 for quad5in (`ref_airframe_model.md` open item 2: "G1 needs the rate-loop signals at
  controller rate"). It was not computed from the allocator normalisation (the normalisation code was not located).

Confirmation, without new flights where possible:
1. Attitude loop: recompute L from the existing `flight.ulg` with `c' = c - K rate_sp / G1` (rate_sp from
   `vehicle_rates_setpoint`, c from `indi_rate_status.torque_sp_pre_inject`) - the rate-loop-only L must then follow the
   model PM within the fitted g/delay. Or fly the injection with the attitude loop opened (acro mode, constant rate
   setpoint).
2. G1: regress `xyz_derivative` (or the filtered gyro difference) on `torque_sp` at 800 Hz in the same logs, in a band
   2-10 Hz where `u` dominates; expect 417 +- 10 %. Or compute from kT, Ixx = 1.40e-3 and the allocator row
   normalisation.
3. Delay/lag/tau: a motor step test in SITL with `--sim v2` (`SIM_GZ_ESC_FB 2`, rotor joint speed published): step the
   `actuator_motors` command and compare the joint speed response against the command: a 1.25 ms offset between the
   `actuator_motors` timestamp and the first joint speed change, and a 33 ms time constant, confirm (a) and rule out
   (c). Alternatively the same injection at `IMU_GYRO_RATEMAX` 400: a one-step delay moves to 2.5 ms (about 4 deg at 4.5 Hz
   instead of 2); a physical 1.3 ms lag would not change.

## 6. Unverified

- G1_true (g = 1.30 is a fit, degenerate with tau_r: g 1.43 / tau_r 0.038 fits equally).
- `FilterAngularAcceleration` caller order (that `data` is already the LPF2p output when differenced) and the exact
  `AlphaFilter::update` form (alpha = dt/(dt + tau) assumed, as in `alpha_coef`); `margins_models.py` itself flags this
  as read from memory.
- gz motor model discretisation, command publication latency, IMU publication timing.
- Which of the 18 bins the checker accepted (all are used; the in-band fit is insensitive to the rejected ones but the
  bins at 15.8-50 Hz are visibly noisy and are excluded).
- Attitude-loop model: pure `Patt/s` with no extra delay or the attitude estimator dynamics, Patt 8 from the airframe
  file (not read back from the flight log; the fit with Patt free returns 7.3-8.6).
- Fit band excludes below 2 Hz where position/velocity loops also contribute.

## 7. Tables (script output, `a21_tables.txt`)

As-coded parameters (MM.INDI_DEF): {"tau_r": 0.033, "tau_m": 0.02, "d_m": 0, "n": 1, "K": 20.0, "G1": 320.0, "gyro_fc": 40.0, "dgyro_fc": 20.0, "lat": 0, "g": 1.0, "eta": 1.0}

## Fit summary (fit band 2.0-12.7 Hz, both flights, 18 bins)

| hypothesis | fitted | rms resid (dB-equiv) | PM deg @Hz | GM dB @Hz |
|---|---|---|---|---|
| A0 as coded (no outer loop) | - | 3.72 | 42.7 @3.25 | 6.1 @6.28 |
| ATT only: Patt = 8 (airframe), no fit | - | 3.22 | 23.5 @3.58 | 4.6 @5.78 |
| (a) extra pure delay Td | Td=0.003454 | 3.19 | 35.7 @3.48 | 4.2 @5.98 |
| (b) extra first-order lag tx | tx=0.002919 | 3.27 | 36.9 @3.43 | 4.5 @6.00 |
| (c) plant tau_r | tau_r=0.03197 | 3.71 | 44.1 @3.23 | 6.5 @6.44 |
| (d) gain g = G1_true/G1_set | g=1.235 | 2.77 | 44.4 @3.92 | 7.5 @7.83 |
| ATT + (a) delay Td, Patt=8 | Td=0.001943 | 3.02 | 20.7 @3.70 | 3.7 @5.62 |
| ATT + (b) lag tx, Patt=8 | tx=0.001608 | 3.06 | 21.2 @3.68 | 3.8 @5.64 |
| ATT + (c) tau_r, Patt=8 | tau_r=0.02805 | 2.87 | 29.6 @3.48 | 6.7 @6.69 |
| ATT + (d) g, Patt=8 | g=1.302 | 1.25 | 30.5 @4.27 | 6.6 @7.77 |
| ATT with Patt free | Patt=7.289 | 3.21 | 25.0 @3.54 | 4.8 @5.83 |
| ATT Patt=8 + g + Td | g=1.306, Td=0.001264 | 0.97 | 27.9 @4.39 | 5.4 @7.48 |

Measured: s41_seed2 PM 24.0 @4.75 Hz, GM 6.0 dB @7.66 Hz; s40_seed1 PM 25.3 @4.47 Hz, GM 4.3 dB @7.44 Hz

## Per-bin s41_seed2: measured vs model (|L| dB / arg deg; err = model - measured)

| f Hz | meas dB | meas deg | A0 as coded (n dB | deg | ATT only: Patt dB | deg | ATT with Patt  dB | deg | (a) extra pure dB | deg | (b) extra firs dB | deg | (c) plant tau_ dB | deg | ATT + (a) dela dB | deg | ATT Patt=8 + g dB | deg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.0 | 18.4 | -168.5 | 10.1 | -104 | 14.3 | -154 | 13.8 | -152 | 10.2 | -105 | 10.1 | -105 | 10.1 | -104 | 14.3 | -155 | 16.3 | -153 |  (outside fit band)
| 1.3 | 11.3 | -165.3 | 7.8 | -109 | 10.8 | -150 | 10.4 | -148 | 7.9 | -110 | 7.9 | -110 | 7.8 | -108 | 10.8 | -151 | 12.7 | -148 |  (outside fit band)
| 1.6 | 9.2 | -151.6 | 6.1 | -113 | 8.3 | -148 | 8.0 | -146 | 6.2 | -115 | 6.2 | -115 | 6.1 | -112 | 8.3 | -149 | 10.1 | -145 |  (outside fit band)
| 2.0 | 7.8 | -145.6 | 4.2 | -119 | 5.8 | -147 | 5.6 | -145 | 4.4 | -121 | 4.3 | -121 | 4.1 | -118 | 5.8 | -148 | 7.6 | -142 |
| 2.5 | 7.0 | -127.8 | 2.3 | -126 | 3.4 | -149 | 3.3 | -147 | 2.6 | -129 | 2.5 | -129 | 2.2 | -125 | 3.6 | -150 | 5.3 | -142 |
| 3.2 | 2.4 | -137.0 | 0.1 | -137 | 1.1 | -153 | 0.9 | -152 | 0.6 | -140 | 0.6 | -140 | 0.1 | -135 | 1.3 | -155 | 2.9 | -144 |
| 4.0 | 1.5 | -150.4 | -1.8 | -148 | -1.1 | -161 | -1.1 | -160 | -1.1 | -152 | -1.2 | -152 | -1.9 | -147 | -0.7 | -162 | 0.9 | -149 |
| 5.0 | -0.6 | -157.8 | -3.9 | -163 | -3.2 | -171 | -3.3 | -171 | -2.8 | -167 | -3.0 | -166 | -4.0 | -161 | -2.6 | -173 | -1.2 | -157 |
| 6.3 | -3.4 | -170.8 | -6.2 | 180 | -5.5 | 174 | -5.6 | 175 | -4.6 | 176 | -4.9 | 176 | -6.3 | -178 | -4.7 | 172 | -3.6 | -169 |
| 7.9 | -6.4 | 177.7 | -8.5 | 160 | -8.0 | 157 | -8.0 | 157 | -6.5 | 157 | -6.8 | 157 | -8.7 | 162 | -6.8 | 155 | -6.0 | 176 |
| 10.0 | -9.3 | 151.9 | -11.2 | 137 | -10.7 | 136 | -10.8 | 136 | -8.5 | 136 | -8.9 | 135 | -11.4 | 140 | -9.2 | 136 | -8.8 | 158 |
| 12.6 | -12.7 | 137.5 | -14.0 | 114 | -13.6 | 113 | -13.7 | 113 | -10.6 | 115 | -11.1 | 113 | -14.3 | 116 | -11.6 | 115 | -11.8 | 139 |
| 15.8 | -11.7 | 155.2 | -17.0 | 89 | -16.7 | 89 | -16.7 | 89 | -12.8 | 93 | -13.4 | 91 | -17.3 | 92 | -14.2 | 93 | -14.8 | 118 |  (outside fit band)
| 20.0 | -15.4 | 143.6 | -20.3 | 62 | -20.1 | 63 | -20.1 | 63 | -15.2 | 70 | -15.9 | 66 | -20.6 | 65 | -17.0 | 69 | -18.0 | 94 |  (outside fit band)
| 25.1 | -16.0 | 102.5 | -23.8 | 36 | -23.7 | 37 | -23.7 | 37 | -17.8 | 45 | -18.7 | 40 | -24.2 | 38 | -19.9 | 45 | -21.2 | 69 |  (outside fit band)
| 31.6 | -22.0 | -23.9 | -27.9 | 8 | -27.9 | 9 | -27.9 | 9 | -20.9 | 18 | -22.1 | 12 | -28.3 | 10 | -23.4 | 19 | -24.9 | 42 |  (outside fit band)
| 39.8 | -20.6 | -146.4 | -32.9 | -20 | -32.9 | -20 | -32.9 | -20 | -24.8 | -11 | -26.4 | -18 | -33.2 | -18 | -27.5 | -8 | -29.1 | 13 |  (outside fit band)
| 50.1 | -23.5 | -0.2 | -38.7 | -46 | -38.8 | -46 | -38.7 | -46 | -29.6 | -41 | -31.8 | -48 | -39.0 | -44 | -32.5 | -35 | -34.1 | -16 |  (outside fit band)

residual A0 as coded (no outer loop)        in-band rms 3.73 dB-eq (max |dB| 4.7, max |deg| 27)
residual ATT only: Patt = 8 (airframe), no fit in-band rms 3.32 dB-eq (max |dB| 3.6, max |deg| 24)
residual ATT with Patt free                 in-band rms 3.31 dB-eq (max |dB| 3.7, max |deg| 24)
residual (a) extra pure delay Td            in-band rms 3.32 dB-eq (max |dB| 4.4, max |deg| 24)
residual (b) extra first-order lag tx       in-band rms 3.39 dB-eq (max |dB| 4.5, max |deg| 25)
residual (c) plant tau_r                    in-band rms 3.70 dB-eq (max |dB| 4.8, max |deg| 28)
residual ATT + (a) delay Td, Patt=8         in-band rms 3.20 dB-eq (max |dB| 3.4, max |deg| 23)
residual ATT Patt=8 + g + Td                in-band rms 1.17 dB-eq (max |dB| 1.7, max |deg| 14)

## Per-bin s40_seed1: measured vs model (|L| dB / arg deg; err = model - measured)

| f Hz | meas dB | meas deg | A0 as coded (n dB | deg | ATT only: Patt dB | deg | ATT with Patt  dB | deg | (a) extra pure dB | deg | (b) extra firs dB | deg | (c) plant tau_ dB | deg | ATT + (a) dela dB | deg | ATT Patt=8 + g dB | deg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.0 | 16.9 | -163.7 | 10.1 | -104 | 14.3 | -154 | 13.8 | -152 | 10.2 | -105 | 10.1 | -105 | 10.1 | -104 | 14.3 | -155 | 16.3 | -153 |  (outside fit band)
| 1.3 | 12.4 | -163.5 | 7.8 | -109 | 10.8 | -150 | 10.4 | -148 | 7.9 | -110 | 7.9 | -110 | 7.8 | -108 | 10.8 | -151 | 12.7 | -148 |  (outside fit band)
| 1.6 | 10.6 | -163.0 | 6.1 | -113 | 8.3 | -148 | 8.0 | -146 | 6.2 | -115 | 6.2 | -115 | 6.1 | -112 | 8.3 | -149 | 10.1 | -145 |  (outside fit band)
| 2.0 | 6.9 | -143.5 | 4.2 | -119 | 5.8 | -147 | 5.6 | -145 | 4.4 | -121 | 4.3 | -121 | 4.1 | -118 | 5.8 | -148 | 7.6 | -142 |
| 2.5 | 6.0 | -138.0 | 2.3 | -126 | 3.4 | -149 | 3.3 | -147 | 2.6 | -129 | 2.5 | -129 | 2.2 | -125 | 3.6 | -150 | 5.3 | -142 |
| 3.2 | 2.9 | -142.4 | 0.1 | -137 | 1.1 | -153 | 0.9 | -152 | 0.6 | -140 | 0.6 | -140 | 0.1 | -135 | 1.3 | -155 | 2.9 | -144 |
| 4.0 | 1.2 | -151.0 | -1.8 | -148 | -1.1 | -161 | -1.1 | -160 | -1.1 | -152 | -1.2 | -152 | -1.9 | -147 | -0.7 | -162 | 0.9 | -149 |
| 5.0 | -1.2 | -158.6 | -3.9 | -163 | -3.2 | -171 | -3.3 | -171 | -2.8 | -167 | -3.0 | -166 | -4.0 | -161 | -2.6 | -173 | -1.2 | -157 |
| 6.3 | -2.8 | -170.0 | -6.2 | 180 | -5.5 | 174 | -5.6 | 175 | -4.6 | 176 | -4.9 | 176 | -6.3 | -178 | -4.7 | 172 | -3.6 | -169 |
| 7.9 | -4.9 | 175.6 | -8.5 | 160 | -8.0 | 157 | -8.0 | 157 | -6.5 | 157 | -6.8 | 157 | -8.7 | 162 | -6.8 | 155 | -6.0 | 176 |
| 10.0 | -8.6 | 154.4 | -11.2 | 137 | -10.7 | 136 | -10.8 | 136 | -8.5 | 136 | -8.9 | 135 | -11.4 | 140 | -9.2 | 136 | -8.8 | 158 |
| 12.6 | -12.3 | 134.9 | -14.0 | 114 | -13.6 | 113 | -13.7 | 113 | -10.6 | 115 | -11.1 | 113 | -14.3 | 116 | -11.6 | 115 | -11.8 | 139 |
| 15.8 | -10.0 | 128.3 | -17.0 | 89 | -16.7 | 89 | -16.7 | 89 | -12.8 | 93 | -13.4 | 91 | -17.3 | 92 | -14.2 | 93 | -14.8 | 118 |  (outside fit band)
| 20.0 | -23.3 | 173.7 | -20.3 | 62 | -20.1 | 63 | -20.1 | 63 | -15.2 | 70 | -15.9 | 66 | -20.6 | 65 | -17.0 | 69 | -18.0 | 94 |  (outside fit band)
| 25.1 | -16.4 | 113.7 | -23.8 | 36 | -23.7 | 37 | -23.7 | 37 | -17.8 | 45 | -18.7 | 40 | -24.2 | 38 | -19.9 | 45 | -21.2 | 69 |  (outside fit band)
| 31.6 | -20.0 | -5.4 | -27.9 | 8 | -27.9 | 9 | -27.9 | 9 | -20.9 | 18 | -22.1 | 12 | -28.3 | 10 | -23.4 | 19 | -24.9 | 42 |  (outside fit band)
| 39.8 | -21.9 | -142.6 | -32.9 | -20 | -32.9 | -20 | -32.9 | -20 | -24.8 | -11 | -26.4 | -18 | -33.2 | -18 | -27.5 | -8 | -29.1 | 13 |  (outside fit band)
| 50.1 | -24.8 | -46.4 | -38.7 | -46 | -38.8 | -46 | -38.7 | -46 | -29.6 | -41 | -31.8 | -48 | -39.0 | -44 | -32.5 | -35 | -34.1 | -16 |  (outside fit band)

residual A0 as coded (no outer loop)        in-band rms 3.71 dB-eq (max |dB| 3.7, max |deg| 25)
residual ATT only: Patt = 8 (airframe), no fit in-band rms 3.12 dB-eq (max |dB| 3.1, max |deg| 22)
residual ATT with Patt free                 in-band rms 3.12 dB-eq (max |dB| 3.1, max |deg| 22)
residual (a) extra pure delay Td            in-band rms 3.05 dB-eq (max |dB| 3.4, max |deg| 22)
residual (b) extra first-order lag tx       in-band rms 3.16 dB-eq (max |dB| 3.5, max |deg| 23)
residual (c) plant tau_r                    in-band rms 3.71 dB-eq (max |dB| 3.8, max |deg| 25)
residual ATT + (a) delay Td, Patt=8         in-band rms 2.84 dB-eq (max |dB| 2.4, max |deg| 20)
residual ATT Patt=8 + g + Td                in-band rms 0.71 dB-eq (max |dB| 1.1, max |deg| 4)
