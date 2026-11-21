# freeze-7 gate re-fly queue (S177, D-FREEZE-7)

One serial, idempotent, detached queue: `queue.sh`. Status per flight: `queue_status.tsv` (name, start, end, rc). Log: `queue.log`
(ends with `QUEUE_END`). Raw logs untracked. Firmware: `make px4_sitl_default` in Docker at HEAD (08011e92d0 for src/), `build.log`, BUILD_RC 0.

## Contents (48 flights)
- G5.5: 8 scenarios (offb_vel_step, o1_lemniscate, o2_circle_z, o3_lemniscate_gust, o4_lemniscate_payload, o5_zsine_com_shift,
  o6_zsine_mass, o7_lemniscate_tau2) x seeds 1-3 = 24, out `g55/<scenario>_s<seed>`.
- G4: 18 = (quiet, typ, harsh) x (hover = hover_long, cruise = traj_lemniscate) x seeds 1-3, via `bench/gate_g4.sh fly` single-run mode
  (same command as the s169 set), out `g4/<hover|cruise>_<profile>_s<seed>`. Score later: `bench/gate_g4.sh score results/freeze7_s177/g4` in Docker.
- G5.3/G5.4: auto_tour, auto_land10 x seeds 1-3 = 6 (the scenarios of g5_freeze_s157), out `g5/<scenario>_s<seed>`.

## Commands copied
- Runner (G5.5 and G5.3/G5.4): `g5_freeze_s157/fly.sh` arguments: `run.sh -t 900 -- python3 indi_flight/bench/run_scenario.py --controller indi
  --model quad5in --seed S --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0
  --params g5_freeze_s157/params.params --scenario SC --out ...`, wrapped in `timeout 1000`. Only --out, seed, scenario change.
- Params: freeze params.params has MC_INDI_POS_EN 1 and no MC_INDI_XY_* / MPC_XY_* entry, so firmware defaults 1.9/3.6 apply
  (run.json boot_params of flight 1: MC_INDI_EN 1, MC_INDI_POS_EN 1).
- G4: `timeout 1000 sh indi_flight/bench/gate_g4.sh fly <out> <profile> <flight> <seed>`.
- Done test: `<outdir>/flight.ulg` exists (a failed flight leaves no ulg unless it got far enough; rc is in the tsv).

## Resume
`cd <repo root> && setsid nohup bash indi_flight/results/freeze7_s177/queue.sh >> indi_flight/results/freeze7_s177/queue.log 2>&1 &`
(stop the queue first with `pkill -f freeze7_s177/queue.sh; docker ps -q --filter name=s177 | xargs -r docker stop`).

## Timing
Flight 1 (offb_vel_step s1) 35 s wall; G5.5 flights 38-41 s each (8 flights measured, all rc 0). G4 hover (60 s hold) and
auto_tour/auto_land10 are expected longer (about 45-70 s; auto_* unmeasured). Expected total about 40-50 min from 12:57 (end about 13:45).
