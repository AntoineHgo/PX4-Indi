# G3 pre-test S112 (3 flights)
Base params: bench/params/quad5in_indi_g1.params (the quad5in INDI default; S110 check flight used it). Scenario-override timings per the runner.
Draw selection (scan seeds 1-8 x 20 draws, dry-run build_run): 
- seed1 idx3: o1_lemniscate --sched, wind + tel_loss + weak motor + tel_dropout (a, c-dropout)
- seed3 idx18: stick_zsine_o6, motor_fault = weak motor + saturation, wind (b)
- seed2 idx18: o1_lemniscate, wind + tel_loss + saturation + tel_dropout (c)
Note: g3_run.py never emits --sched-anchor nor a sub-run set_param (grep: no occurrence), so the K111 F-4 set_param latency and --sched-anchor checks have no draw to test: NOT CHECKED unless seen in run.json.
Commands: `bash indi_flight/results/g3_pretest_s112/fly.sh`
Note: host-direct run of g3_run.py fails (FileNotFoundError 'gz', and no sim); all flights are run via indi_project/docker/run.sh (fly.sh).
SET-UP NOTE 2: g3_sample.campaign(seed, n) draws depend on n. A first attempt flown with --n 4 / --n 19 gave different draws (seed1 idx3 had no eRPM loss, no weak motor): discarded to _discarded_n_mismatch/. Re-flown with --n 20 via scratch wrapper g3_one.py (restricts campaign() to one index; runner itself untouched, since g3_run.py has no stop index).

## Draw selection outcome
Flown OK (exit_status ok): seed1 run_003 and seed2 run_018 (both o1_lemniscate --sched). Stick draws seed3/18, seed8/18, seed14/18 (the only stick draws with weak motor AND saturation; all have mass_scale 1.3) did NOT produce a usable flight, see FAULT 2 and FAULT 3 below. A control stick draw (seed3 run_007, weak motor + wind + eRPM loss, mass 1.04) was flown last (section Stick control).
No draw contains --sched-anchor, a sub-run set_param, or a "sag" in seeds 1..8 x 20 (g3_run.py never emits --sched-anchor; --sched only).

## Commands used
```
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
python3 indi_flight/bench/g3_run.py --seed S --n 20 --base-params indi_flight/bench/params/quad5in_indi_g1.params --out-root /tmp/x --dry-run   # scan (via build_run() in a scratch script, seeds 1..59)
# flights, one draw per container (g3_one.py = scratch wrapper restricting g3_sample.campaign() to one index, runner untouched):
indi_project/docker/run.sh -n NAME -t 1500 -- python3 indi_flight/results/g3_pretest_s112/g3_one.py --seed S --n 20 --start K \
    --base-params indi_flight/bench/params/quad5in_indi_g1.params --out-root indi_flight/results/g3_pretest_s112/seedS --timeout-s 1200
 # (S,K) = (1,3) (2,18) [flown OK]; (3,18) (8,18) (14,18) (3,7) [failed, see below]; scripts fly.sh fly2.sh fly3.sh
ulog2csv RUN/flight.ulg -o SCRATCH; python3 chk.py RUN SCRATCH      # chk.py = this directory, the analysis below
python3 indi_flight/bench/pretest_gate.py RUN/flight.ulg RUN/gate.md
```
Base params: indi_flight/bench/params/quad5in_indi_g1.params (the default INDI quad5in file; no earlier G3 check used another: S110 check run params_applied lists it). speed 1.0 (runner default). g3_checks.py does not exist.
Draws are a function of (seed, n): the same --n 20 must be used as in the scan. Failed first attempts with other n are in _discarded_n_mismatch/.

## Flight 1: seed1 run_003 (o1_lemniscate --sched; wind + tel_loss motor 3 + weak motor 3 (scale 0.8328) + tel_dropout p=0.1495)
exit_status ok, events settle 55.737 / traj 58.737 / hold 76.557 (sim s), flew to the end of the window (ulog to 96.8 s), no disarm/crash flag, watchdog silent.
- vel-None: injector vel_none_ticks 22400 of 22401 updates, first_valid_vel_sim_s None. disturbance.stdout: `TypeError: No message class registered for 'gz.msgs.Pose'` in on_pose (disturbance.py:340) -> the gz pose subscriber never delivers a velocity, wind stays on the legacy (ground-frame) force. FAULT.
- wind force: nonzero, steady plateau |F| = 0.0358 N = 0.00735 * 2.2059^2, direction atan2(fy,fx) = 201.67 deg = drawn dir_deg 201.67 (frame/sign consistent), peak |F| 0.0937 N, ratio to steady 2.619 = (3.5699/2.2059)^2. Wind is applied, but as v_wind*|v_wind| drag on the airframe at rest, NOT air-relative (K110 MAJOR "wind drag not air-relative" is not fixed in practice).
- eRPM loss (esc_status esc_errorcount of motor 3 increments on 100 % of frames; run of 1490 consecutive error frames, frame period 1.25 ms): measured 61.7688 .. 63.7575 s; drawn start = anchor 58.737 + 2.9956 = 61.7326; set_param requested at 61.737 (sim, quantised), parameter_update in ulog 61.7625, first error frame 61.7688: start 36.2 ms late vs drawn (29 frame periods), duration measured 1.990 s vs drawn 2.000 s (-10 ms). Other motors: 11-30 % error frames/0.1 s window (tel_dropout p 0.1495), never a run > 40 frames. Loss exists and is on the right motor; start tolerance of one telemetry period (1.25 ms) NOT met.
- weak motor 3 scale 0.8328: SIM_GZ_EC_MAX4 2700 -> 2464 (= sqrt(scale)). The rotor speed does not drop (rpm/output unchanged 9.558 -> 9.540; ESC rpm 8783 vs 8797-8805 others) because the command u is the (omega/MAX)^2 map and the controller compensates; visible in actuator_motors u: pre [0.1079 0.1079 0.1079 0.108], post (0.5 s .. 17 s after event) [0.1164 0.1166 0.116 0.140]; 0.140/0.1165 = 1.20 = 1/0.8328. OK.
- --sched timing: sim_schedule_applied 895 rows, max |applied timestamp - t_sched| = 0.39 ms, anchor_us 0 (no --sched-anchor in this draw).
- set_param latency (request -> parameter_update in ulog): EC_MAX4 58.737 -> 58.7738 (37 ms); ERPM_LOSS on 61.737 -> 61.7625 (25.5 ms); off 63.740 -> 63.755 (15 ms). sends.csv sim_time_after - before = 11 / 11 / 7 ms; CLI call wall 11-22 ms.
- metrics: bench/metrics.py ran inside run_scenario (metrics_status ok, metrics.json). pretest_gate.py (a hover gate) FAIL rate RMS 0.033/0.082/0.021 (not a G3 criterion, trajectory flight; no judgement). No errors.

## Flight 2: seed2 run_018 (o1_lemniscate --sched; wind 4.26 m/s peak 9 + tel_loss motor 2 + saturation 0.351 on all motors + tel_dropout p=0.105)
exit_status ok, events settle 55.523 / traj 58.523 / hold 76.343, ulog to 98.5 s, no crash.
- vel-None: 22400 of 22401, same Pose TypeError. Wind: dir measured 222.63 deg vs drawn 222.62, steady |F| 0.1335 N = 0.00735 * 4.2623^2, max 0.5954 N, ratio 4.459 = (9/4.2623)^2. Consistent, legacy force.
- eRPM loss: run of 1438 consecutive error frames at 60.565 .. 62.4838; drawn start = 58.523 + 1.9197 = 60.4427; request 60.443, parameter_update 60.465, first error frame 60.565: 122 ms late vs drawn (100 ms after the parameter_update); duration 1.92 s vs 2.00 (-80 ms). End: request 62.453, update 62.4788, last error frame 62.4838 (5 ms after update). Start offset NOT within one telemetry period; the lag after the parameter_update varied (6 ms in flight 1, 100 ms here).
- saturation 0.351 x4 motors (EC_MAX 2700 -> 1600): u mean pre [0.1775 0.1775 0.1774 0.1775], post [0.554 0.554 0.537 0.544] (x3.12 = 1/0.351); peak u 0.71 (< 1, the cap never binds: the fault is a thrust-gain loss, not a clip at this flight level). The 8 set_param calls take effect staggered: parameter_update at 58.5612, 58.5862, 58.6112, 58.6325 for an event at 58.523 (38 .. 110 ms after the event, motors not simultaneous). run.json event_done_us = event_us (58.523) so run.json "applied" time is the request, not the effect.
- --sched: 895 rows, max deviation 0.39 ms, anchor 0. metrics ok; pretest_gate FAIL rate RMS 0.11-0.14 (hover gate, not a criterion).

## Stick draws (b) and the third check: FAULTS
- FAULT 2 (sampler): seed3 run_018 never flew. gz.log `A link named base_link has invalid inertia`, px4 `Preflight Fail: No valid data from Accel/Gyro`, RunError timeout waiting for 'Ready for takeoff'. Drawn inertia scales (0.865, 1.003, 1.153) x nominal (1.022, 1.122, 1.944)e-3 give ixx+iyy = 2.010e-3 < izz = 2.241e-3: violates the triangle inequality. Per-axis independent inertia scaling breaks it in 7/20, 5/20, 7/20 draws (seeds 3, 2, 1, n=20) and 97/300, 90/300, 94/300 (n=300): ~1/3 of a 300-run campaign would fail at start-up (g3_sample or g3_run must draw a physically valid inertia, e.g. check the triangle inequality or scale ixx,iyy,izz with correlation).
- FAULT 3 (stick scenario, undetermined cause): stick draws seed8/18 and seed14/18 (both mass 1.3, valid inertia, no gz error) tripped the runner watchdog (height < 0.3 m) at sim 53.76 / 53.79 s, i.e. BEFORE the settle/stick segment (55.5 s), before any hook; seed14: altitude 4.97 m at 52 s -> 3.67 m at 53 s, u falls 0.173 -> 0.11. Both are mass 1.3 + stick_zsine_o6. Control seed3 run_007 (stick, mass 1.04, weak motor 0 scale 0.742, wind 1.9 m/s, eRPM loss motor 1) reached the stick segment (58.551) but the height was already 4.31 m (from 5.0 at 52 s, vz -0.22) before the stick start and fell below 0.3 m at 62.09 s (watchdog), 0.67 s after the eRPM loss began (61.423; drawn 58.551+2.8689 = 61.4199, request 3 ms late). Not a hook problem for sure, not excluded either; the hooks that did apply: weak motor 0 raised u0 to 0.18 vs 0.13 (x1.38 vs 1/0.742 = 1.35); injector 2862/2862 vel-None ticks. metrics.py crashes on these aborted runs (TypeError NoneType * float at metrics.py:531, window None); the driver prints METRICS FAILED but returns 1 (no g3_done marker).
- No flight tests weak motor AND saturation together in a flown stick run: NOT verified (the combined multiply `motor_fault` list is only seen in the run_018 draw files and run.json of seed2, which had saturation only).

## Verdicts
| check | verdict |
|---|---|
| wind force applied, nonzero, direction/sign vs drawn | OK (flights 1, 2: dir within 0.01 deg, |F| = 0.00735 w^2, peak ratio = (peak/steady)^2) |
| wind drag air-relative / vel-None ticks small | FAULT: 22400/22401 (100 %) ticks without velocity, gz Pose callback TypeError `No message class registered for 'gz.msgs.Pose'`; same in the stick run (2862/2862) |
| eRPM loss window (position mode) | FAULT (tolerance): right motor, duration -10 / -80 ms, start 36 / 122 ms late (> one 1.25 ms frame); cause is set_param latency + sim-side read; run.json on_us (the request) is not the effective time |
| weak motor scale visible | OK (u ratio 1.20 = 1/0.8328; flight 1) |
| saturation visible | OK as a gain loss (u x3.12); no clipping reached; 4 motors staggered 38-110 ms |
| weak motor + saturation together | NOT CHECKED (no flown draw: every such draw is the stress slot idx 18; seed3/8/14 failed, see FAULT 2/3) |
| --sched timing | OK (max 0.39 ms, 895 rows x 2 flights) |
| --sched-anchor | NOT CHECKED (g3_run.py never emits it; anchor_us = 0 in both flights) |
| sub-run set_param latency (K111 F-4) | measured on the fault/eRPM-loss set_params only: request -> parameter_update 15-26 ms (single param), 38-110 ms (8-param fault set); no sub-run set_param in these draws beyond those |
| metric scripts | metrics.py OK on flown runs, crashes on aborted runs (above); pretest_gate runs; g3_checks.py absent |
| each flight flew to the end | flights 1, 2 yes; stick draws seed3/18 (no start-up), seed8/18, seed14/18, seed3/7 no (watchdog) |
| stick mode run with the hooks | FAULT/NOT CHECKED (3 of 3 stick flights did not complete) |
