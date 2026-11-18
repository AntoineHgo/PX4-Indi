# S82 outer-loop (acceleration) break injector: notes

## Design (done)
- Break: `McIndiPosControl::runIndiStage`, c = commanded acceleration of the stock position loop (`local_pos_sp.acceleration`),
  which in accel_only mode is the INDI stage input and equals the library's a_c (`indi_accel_control.cpp` "2. commanded
  acceleration": `a_c = a_ref`). u = c + d is passed as `in.a_ref`; the library is untouched.
- States fed by u (all inside `src/lib/indi_accel_control/indi_accel_control.cpp`, derived from a_c/a_ref, so closed through u):
  jerk difference state `updateJerkDifference(a_ref...)` :~239 (-> omega_ff), `t_c = t_f + (a_c - a_f)` :~294, `_thrust_prev = thrust`
  (previous command, model path of the blend `u_model`, `_um_buf`/`_lpf_um`, :~262-275), `_coll_clamped`.
  `local_pos_sp.acceleration` itself is left = c (the stock loop's own output, still logged as c).
  Single clean break, no second one needed.
- Generator: rate module's `IndiInjection` is module-local (own CMake library), so copied to
  `src/modules/mc_indi_pos_control/IndiPosInjection.{hpp,cpp}` (class renamed IndiPosInjection to avoid a duplicate symbol;
  axis = NED x/y/z). Clock = `now` (hrt, sim time in SITL), origin = first cycle with AX set, armed,
  not landed (flag_armed, vehicle_land_detected.landed). Evaluated only inside the can_run branch (d=0 in bypass).
- Params: `MC_INDI_PINJ_AX/AMP/TP/FLO/FHI/NP/DLY` (DLY added: start delay, as MC_INDI_INJ_DLY, otherwise the window starts during takeoff). DEVIATION: spec names FMIN/FMAX would be 17 chars (>16), used FLO/FHI.
- Msg `IndiPosStatus`: `a_c` is now u; new `a_c_pre_inject` (c) and `inject` (d), 3-vectors, one sample per cycle.
pretest launched 2026-11-18T04:29:06+01:00

## Status (end of S82 agent work)
- Build: `ninja bin/px4` in `build/px4_sitl_default` via docker OK (build.log). Unit test `unit-IndiPosInjection` (6 tests incl. BinContent
  DFT check and AX=0 -> exact 0) passes; broken once (freq x1.03): MatchesMarginsEst, Gating, BinContent failed; restored, passes.
- `Tools/astyle/fix_code_style.sh` on the 5 changed C/C++ files: Unchanged (clean).
- Analysis: `bench/pinj_csv.py` (window t,d,x=u,y=c; `--margins` calls `margins_est.frf_periodic/margins`, bins = `log_bins`).
  First attempt with `detect_bins` found 263 spurious bins (non-uniform sampling leakage) -> use the generator's `log_bins`.
- Pre-test flight (hover_long, quad5in, indi, v2, 400 Hz, speed 4, seed 1, wall 48 s): `run/`, params `pretest.params`.
  d non-zero only on z in [42.04, 82.02] s sim (3555 samples, 0 zero samples inside, 0 non-zero on x/y); max |d| 0.397 m/s^2;
  max |u - c - d| = 3e-8. Status rate 88.9 Hz (non-uniform: LS phasor path).
- Result (16 bins 0.2-8 Hz, Tp 10, NP 4, discard 1): coherence ~1.0 on all bins except 0.2 Hz (x: 0.69) and 0.4 Hz (0.89, y 0.98);
  14/16 accepted. One 0 dB crossing at 0.602 Hz, PM 54.4 deg (DM 0.251 s), no -180 deg crossing in band (GM not defined, |L| 0.038
  at 8 Hz, top -28 dB), Ms 1.19. margins.json.
## Unverified / caveats
- Origin = first armed non-landed cycle + 8 s = 42 s sim, which is still partly climb/transition (offboard from ~52 s, hover window
  55 s per metrics.json); periods 1 (discarded) and probably 2 overlap that. With NP 4 discard 2 is impossible. Low-frequency
  bins (0.2-0.4 Hz) are the poorest and the PM crossing (0.6 Hz) is close to them. A repeat with a longer DLY (or NP 5) is advisable.
- AX=0 bit-identical comparison against the previous build (D-G2-BREAK overturn check) was NOT run.
- Only the z axis was flown. x/y not flown. One flight, one seed. No unit test for pinj_csv.py.
- Whether the break "c" should be the stock position loop output (done) vs. a point inside the INDI law: here the library takes
  a_c = a_ref directly in accel_only mode, so u replaces c in all library states; `local_pos_sp.acceleration` stays c.
- Build used `ninja bin/px4` only (not `make px4_sitl_default`: gz plugins untouched).
