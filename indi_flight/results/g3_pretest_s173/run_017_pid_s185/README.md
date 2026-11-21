# G3 run 17 with the PID stack (S185)

Reference for run_017 of g3_pretest_s173: same draw (seed 173, idx 17, sampler seed 368048566, gz seed 445533786),
controller `pid_default`, no MC_RATE_CTL_TYPE, no MC_INDI_* from the base file. Driver: `fly_pid_run017.py` (uses
g3_run.build_run with CONTROLLER set to pid_default; run in docker via `indi_project/docker/run.sh -n pid173_17 -t 1000`).
Command: `python3 indi_flight/bench/run_scenario.py --scenario o1_lemniscate --controller pid_default --model quad5in --sim v2
--rate-hz 800 --seed 368048566 --sim-seed 445533786 --out <dir> --params <dir>/g3_params.txt --sched --model-variant ... --erpm-drop 0.19865
--vib-acc 13.012077 --vib-gyr 0.150604 --imu-noise-scale 4.0 --gps-dly 201 --gnss-delay 190 --scenario-overrides <dir>/g3_scenario_overrides.json`
Scoring: `g3_checks.py flight.ulg --t0 62.291 --t1 65.291 --wind --mode position` (window from score.sh rule).

Draw: tel_frozen NOT drawn in run 17 (on false), so no tel_frozen hook applied. tel_loss, thrust_sag, saturation, weak_motor off.
Wind steady 3.01 m/s + gust_x peak 7.60 m/s from traj onset, dir 81 deg. eRPM drop 19.9 %. Not applied to PID: g1_ctrl_mult (INDI gains only).
run.json exit ok, wall 99.4 s. g3_done.json says `void` because run_validity only knows controller names indi/pid and the runner
was called with pid_default; manual run_validity with controller `pid`: valid, MC_INDI_EN 0, no INDI rate samples (validity_pid.json).

| | PID (this run) | INDI run 17 (score_s174 / run_017/g3_checks.json) |
|---|---|---|
| scored window tilt max | 38.6 deg | 128.6 deg |
| whole-flight max tilt (ulog attitude) | 38.5 deg at ulog 52.71 s (traj +8.1 s) | 128.5 deg at ulog 77.86 s (about 8.5 s after land cmd at 69.45 s, after hold) |
| tilt > 60 deg longest | 0 s | 1.11 s (limit 0.2 s) |
| loss of control (item 1) | no (excursion 4.95 m, limit 5.0) | yes (excursion 5.90 m) |
| oscillation flag (item 2) | yes: p and q sustained, r not | yes: p, q, r sustained |
| hRMS / alt mean | 0.091 m / -0.039 m (pass) | 0.481 m / -0.218 m (fail) |
| factors active at worst moment | steady wind 3.0 m/s (since traj onset), eRPM drop 19.9 %, vib, GNSS delay; gust not yet (ulog ~56.6-57.6 s) | eRPM drop 19.9 %, vib, GNSS delay, model variants; wind segment ends with traj (UNVERIFIED) |

Notes: the PID run is one reference flight with the same draw, not the same trajectory: the controller changes the closed loop.
The PID run also sets MC_INDI_ID_OK 1 through the run_scenario default on o11 builds (MC_INDI_EN stays 0, the INDI module does not start).
Whole-flight tilt is max of arccos(1-2(qx^2+qy^2)) from vehicle_attitude, from traj onset to hold end (ulog clock = px4 clock - start_timestamp).
Scipy for g3_checks came from an earlier session scratch install (PYTHONPATH), not from the repo.
